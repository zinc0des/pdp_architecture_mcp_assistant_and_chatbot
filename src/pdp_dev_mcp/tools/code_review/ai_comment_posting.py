"""
AI-Generated Comment Posting

Simple posting mechanism for AI-crafted contextual feedback to Azure DevOps pull requests.
Enables AI to deliver intelligent code review comments with proper threading and formatting.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import subprocess
import logging
import json
import re

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.tools.common.enhanced_repository_discovery import (
    parse_azure_devops_pr_url,
)

logger = logging.getLogger(__name__)


class CommentType(Enum):
    """Types of code review comments."""

    GENERAL = "general"  # General PR-level comment
    LINE_COMMENT = "line"  # Specific line comment
    FILE_COMMENT = "file"  # File-level comment
    SUGGESTION = "suggestion"  # Code suggestion with diff
    SECURITY = "security"  # Security-focused comment
    PERFORMANCE = "performance"  # Performance-focused comment
    DOMAIN = "domain"  # Payment domain-specific comment


class CommentSeverity(Enum):
    """Severity levels for code review comments."""

    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeReviewComment:
    """
    Individual code review comment with contextual information.

    Designed to enable AI-generated comments with proper formatting,
    threading, and Azure DevOps integration.

    RUNTIME VALIDATION: This class validates enum types at initialization
    to catch common AI agent errors where string values are provided instead
    of proper enum instances.
    """

    comment_id: str
    comment_type: CommentType
    severity: CommentSeverity
    title: str
    content: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_code: Optional[str] = None
    reasoning: Optional[str] = None
    business_impact: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_thread_id: Optional[int] = None  # For threaded replies

    def __post_init__(self):
        """
        Validate enum fields at runtime.

        Python dataclasses don't enforce type checking at runtime, so this
        method explicitly validates that enum fields contain proper enum instances
        rather than string values.

        This helps AI agents catch errors early with clear guidance about valid values.
        """
        # Validate comment_type
        if not isinstance(self.comment_type, CommentType):
            valid_types = [e.value for e in CommentType]
            raise ValueError(
                f"VALIDATION_ERROR: comment_type must be a CommentType enum instance, "
                f"not {type(self.comment_type).__name__} '{self.comment_type}'. "
                f"Valid values: {', '.join(valid_types)}. "
                f"AGENT_GUIDANCE: Use CommentType.GENERAL, CommentType.SECURITY, etc. "
                f"Import CommentType from pdp_dev_mcp.tools.code_review.ai_comment_posting. "
                f"Example: comment_type=CommentType.SECURITY (not 'security')"
            )

        # Validate severity
        if not isinstance(self.severity, CommentSeverity):
            valid_severities = [e.value for e in CommentSeverity]
            raise ValueError(
                f"VALIDATION_ERROR: severity must be a CommentSeverity enum instance, "
                f"not {type(self.severity).__name__} '{self.severity}'. "
                f"Valid values: {', '.join(valid_severities)}. "
                f"AGENT_GUIDANCE: Use CommentSeverity.WARNING, CommentSeverity.ERROR, etc. "
                f"Import CommentSeverity from pdp_dev_mcp.tools.code_review.ai_comment_posting. "
                f"Example: severity=CommentSeverity.WARNING (not 'warning')"
            )


@dataclass
class CommentPostingResult:
    """
    Result of posting comments to Azure DevOps pull request.

    Provides feedback on successful posts, failures, and any issues
    encountered during the posting process.
    """

    total_comments: int
    successful_posts: int
    failed_posts: int
    posted_comments: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[Dict[str, str]] = field(default_factory=list)
    pr_url: Optional[str] = None
    dry_run: bool = False
    local_praise_comments: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Praise shown locally only


def _get_organization_url_info(org: str) -> Tuple[str, str]:
    """
    Determine the correct URL format for an Azure DevOps organization.

    Args:
        org: Organization name (e.g., 'msazure', 'microsoft', 'contoso')

    Returns:
        Tuple of (base_url, pr_url_format)
        - base_url: API base URL for REST calls
        - pr_url_format: URL format for pull request links

    Note: This implements cross-organization support by detecting the correct
    URL format based on organization patterns. However, some organizations
    (like msazure) may use both formats depending on how repositories were
    migrated. When in doubt, this defaults to modern dev.azure.com format
    as it's more widely supported.

    Real-world examples:
    - microsoft: https://microsoft.visualstudio.com/Universal%20Store/_git/...
    - msazure legacy: https://msazure.visualstudio.com/One/_git/...
    - msazure modern: https://dev.azure.com/msazure/One/_git/...
    """
    # Organizations that predominantly use legacy .visualstudio.com format
    # Note: Some of these orgs may have both formats - this is the primary/legacy format
    legacy_primary_orgs = {"microsoft", "microsoft-internal"}

    if org.lower() in legacy_primary_orgs:
        # Legacy Visual Studio URLs
        base_url = f"https://{org}.visualstudio.com/DefaultCollection"
        pr_url_format = f"https://{org}.visualstudio.com"
    else:
        # Modern dev.azure.com URLs (default for most orgs including msazure)
        # This works for both pure modern orgs and mixed orgs like msazure
        base_url = f"https://dev.azure.com/{org}"
        pr_url_format = f"https://dev.azure.com/{org}"

    return base_url, pr_url_format


def _build_api_url(org: str, project: str, repository: str, endpoint: str) -> str:
    """
    Build the correct API URL for Azure DevOps REST calls.

    Args:
        org: Organization name
        project: Project name
        repository: Repository name
        endpoint: API endpoint path (e.g., 'pullRequests', 'iterations')

    Returns:
        Complete API URL with correct base format
    """
    base_url, _ = _get_organization_url_info(org)

    if "visualstudio.com" in base_url:
        # Legacy format: https://org.visualstudio.com/DefaultCollection/project/_apis/git/repositories/repo/endpoint
        return f"{base_url}/{project}/_apis/git/repositories/{repository}/{endpoint}"
    else:
        # Modern format: https://dev.azure.com/org/project/_apis/git/repositories/repo/endpoint
        return f"{base_url}/{project}/_apis/git/repositories/{repository}/{endpoint}"


def _build_pr_url(org: str, project: str, repository: str, pr_id: int) -> str:
    """
    Build the correct pull request URL for Azure DevOps.

    Args:
        org: Organization name
        project: Project name
        repository: Repository name
        pr_id: Pull request ID

    Returns:
        Complete PR URL with correct format
    """
    _, pr_url_format = _get_organization_url_info(org)

    if "visualstudio.com" in pr_url_format:
        # Legacy format: https://org.visualstudio.com/project/_git/repo/pullrequest/id
        return f"{pr_url_format}/{project}/_git/{repository}/pullrequest/{pr_id}"
    else:
        # Modern format: https://dev.azure.com/org/project/_git/repo/pullrequest/id
        return f"{pr_url_format}/{project}/_git/{repository}/pullrequest/{pr_id}"


def _get_pr_diff_files(
    org: str, project: str, repository: str, pr_id: int
) -> Dict[str, Any]:
    """
    Get the list of files changed in the PR to validate comment positioning.

    Returns a dictionary with file paths as keys and their change info as values.
    This prevents the "file no longer exists" error by ensuring we only comment
    on files that are actually part of the PR diff.

    Falls back to git diff if Azure DevOps API is not accessible.
    """
    try:
        # First try Azure DevOps API
        iterations_url = _build_api_url(
            org, project, repository, f"pullRequests/{pr_id}/iterations?api-version=6.0"
        )
        cmd_parts = [
            "az",
            "rest",
            "--method",
            "GET",
            "--uri",
            iterations_url,
            "--resource",
            "https://app.vssps.visualstudio.com",
        ]

        result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)

        if result.returncode == 0 and "<!DOCTYPE html" not in result.stdout:
            iterations_data = json.loads(result.stdout)
            if iterations_data.get("value"):
                latest_iteration = iterations_data["value"][-1]
                iteration_id = latest_iteration.get("id", 1)

                # Get the files changed in the latest iteration
                changes_url = _build_api_url(
                    org,
                    project,
                    repository,
                    f"pullRequests/{pr_id}/iterations/{iteration_id}/changes?api-version=6.0",
                )
                changes_cmd = [
                    "az",
                    "rest",
                    "--method",
                    "GET",
                    "--uri",
                    changes_url,
                    "--resource",
                    "https://app.vssps.visualstudio.com",
                ]

                changes_result = subprocess.run(
                    changes_cmd, capture_output=True, text=True, timeout=30
                )

                if (
                    changes_result.returncode == 0
                    and "<!DOCTYPE html" not in changes_result.stdout
                ):
                    changes_data = json.loads(changes_result.stdout)
                    files_in_diff = {}

                    for change in changes_data.get("changeEntries", []):
                        if change.get("item", {}).get("path"):
                            file_path = change["item"]["path"].lstrip("/")
                            files_in_diff[file_path] = {
                                "changeType": change.get("changeType", "unknown"),
                                "path": file_path,
                            }

                    logger.info(
                        f"Found {len(files_in_diff)} files in PR {pr_id} diff via Azure DevOps API"
                    )
                    return files_in_diff

        # Fallback removed: git diff approach is inappropriate for cross-repo scenarios
        # The Azure DevOps API should be the primary and only method for getting PR files
        logger.warning(
            "Azure DevOps API not accessible - cannot retrieve PR files for cross-repo scenarios"
        )
        logger.info(
            "Note: git diff fallback removed to enable cross-repository code reviews"
        )
        return {}

    except Exception as e:
        logger.error(f"Error getting PR diff files: {e}")
        return {}


def _validate_comment_against_diff(
    comment: CodeReviewComment, diff_files: Dict[str, Any]
) -> bool:
    """
    Validate that a comment can be positioned on a file that exists in the PR diff.

    Returns True if the comment can be safely posted, False otherwise.
    """
    if comment.comment_type != CommentType.LINE_COMMENT or not comment.file_path:
        # General comments don't need file validation
        return True

    # Normalize the file path (remove leading slash)
    file_path = comment.file_path.lstrip("/")

    if file_path not in diff_files:
        logger.warning(
            f"Comment {comment.comment_id} targets file '{file_path}' which is not in PR diff. "
            f"This will cause 'file no longer exists' error. Available files: {list(diff_files.keys())}"
        )
        return False

    return True


def _is_praise_comment(comment: CodeReviewComment) -> bool:
    """
    Detect if a comment is primarily praise/positive feedback.

    Returns True if the comment appears to be praise that would look
    awkward coming from the PR author themselves.
    """
    praise_patterns = [
        r"excellent|exceptional|outstanding|great|fantastic|awesome|brilliant",
        r"well\s+done|good\s+job|nice\s+work|impressive|superb",
        r"perfect|flawless|exemplary|beautiful|elegant",
        r"congratulat|praise|commend|applaud",
        r"love\s+(this|it)|amazing|wonderful|marvelous",
        r"🏆|👏|🎉|✨|🌟",  # Praise emojis
        r"highlights?:|strengths?:|excellence",
        r"best\s+practices?|template.*other.*teams?",
        r"educational\s+value|serves.*as.*example",
    ]

    # Combine title and content for analysis
    text_to_analyze = f"{comment.title} {comment.content}".lower()

    # Check for praise patterns
    for pattern in praise_patterns:
        if re.search(pattern, text_to_analyze, re.IGNORECASE):
            return True

    # Additional heuristics: comments that are mostly positive adjectives
    positive_words = re.findall(
        r"\b(excellent|great|good|perfect|awesome|fantastic|amazing|wonderful|brilliant|superb|outstanding|exceptional|impressive|beautiful|elegant|clean|clear|comprehensive|thorough)\b",
        text_to_analyze,
    )

    # If comment has multiple positive words and is relatively short, likely praise
    word_count = len(text_to_analyze.split())
    if len(positive_words) >= 2 and word_count < 100:
        return True

    return False


def _get_pr_author(
    org: str, project: str, repository: str, pr_id: int
) -> Optional[str]:
    """
    Get the author/creator of the pull request.

    Returns the display name of the PR author, or None if unable to retrieve.
    """
    try:
        pr_url = _build_api_url(
            org, project, repository, f"pullRequests/{pr_id}?api-version=6.0"
        )
        cmd_parts = [
            "az",
            "rest",
            "--method",
            "GET",
            "--uri",
            pr_url,
            "--resource",
            "https://app.vssps.visualstudio.com",
        ]

        result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)

        if result.returncode == 0 and "<!DOCTYPE html" not in result.stdout:
            pr_data = json.loads(result.stdout)
            return pr_data.get("createdBy", {}).get("displayName")

    except Exception as e:
        logger.warning(f"Failed to get PR author: {e}")

    return None


def _filter_self_praise_comments(
    comments: List[CodeReviewComment],
    pr_author: Optional[str],
    current_user: Optional[str] = None,
) -> tuple[List[CodeReviewComment], List[CodeReviewComment]]:
    """
    Filter praise comments when they would appear to come from the PR author.

    Returns a tuple of (comments_to_post, praise_comments_for_local_display).

    When posting to your own PR:
    - Critical/constructive feedback → Post to PR (visible to everyone)
    - Positive feedback → Return for local display only (not posted to PR)

    This prevents awkward self-congratulation while preserving valuable positive feedback.
    """
    # Try to get current user if not provided
    if not current_user:
        try:
            result = subprocess.run(
                ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                current_user = result.stdout.strip()
        except Exception:
            pass

    # If we can't determine EITHER the PR author OR the current user, be conservative
    if not pr_author or not current_user:
        logger.info(
            f"Cannot determine {'PR author' if not pr_author else 'current user'}, filtering all praise comments to avoid self-praise"
        )
        comments_to_post = []
        local_praise = []

        for comment in comments:
            if _is_praise_comment(comment):
                local_praise.append(comment)
            else:
                comments_to_post.append(comment)

        return comments_to_post, local_praise

    # Check if current user is the PR author (allowing for some name variations)
    is_same_author = (
        current_user.lower() in pr_author.lower()
        or pr_author.lower() in current_user.lower()
        or current_user.lower() == pr_author.lower()
    )

    if is_same_author:
        comments_to_post = []
        local_praise = []

        for comment in comments:
            if _is_praise_comment(comment):
                local_praise.append(comment)
                logger.info(f"Moved praise comment to local display: {comment.title}")
            else:
                comments_to_post.append(comment)

        if local_praise:
            logger.info(
                f"Moved {len(local_praise)} praise comments to local display to avoid self-congratulation"
            )

        return comments_to_post, local_praise

    # Different author - post all comments normally
    return comments, []


@mcp.tool()
def post_ai_generated_comments(
    org: str,
    project: str,
    repository: str,
    pr_id: int,
    comments: List[CodeReviewComment],
    dry_run: bool = False,
    batch_size: int = 5,
    filter_self_praise: bool = True,
) -> CommentPostingResult:
    """
    Post AI-generated code review comments to Azure DevOps pull request.

    This tool enables AI agents to deliver contextual code review feedback with proper
    formatting and threading. Designed for cross-organization Azure DevOps support.

    AGENT_USAGE_NOTES:
    - For better UX, consider using post_ai_comments_by_pr_url() which accepts PR URLs directly
    - This function requires manual parameter extraction but works when you have individual components
    - Handles self-praise filtering automatically to avoid awkward self-congratulation on own PRs
    - Supports both dev.azure.com and .visualstudio.com URL formats via dynamic API construction

    Args:
        org: Azure DevOps organization name (e.g., 'microsoft', 'msazure')
        project: Azure DevOps project name (e.g., 'PaymentsDataPlatform', 'One')
        repository: Repository name (e.g., 'Commerce.PaymentsDataPlatform')
        pr_id: Pull request ID (numeric)
        comments: List of AI-generated code review comments
        dry_run: If True, validate and format but don't actually post
        batch_size: Number of comments to post in each batch (rate limiting)
        filter_self_praise: If True, show praise locally when posting to own PR

    Returns:
        CommentPostingResult with posting status, failures, and local praise comments
    """
    if not comments:
        return CommentPostingResult(
            total_comments=0, successful_posts=0, failed_posts=0, dry_run=dry_run
        )

    # Get PR author to filter self-praise comments (if enabled)
    local_praise_comments = []
    if filter_self_praise:
        pr_author = _get_pr_author(org, project, repository, pr_id)

        # Separate comments into those to post and those to show locally
        # Pass None for current_user to force the function to determine it itself
        # This ensures conservative filtering when user identification fails
        comments, local_praise_comments = _filter_self_praise_comments(
            comments, pr_author, current_user=None
        )
        filtered_count = len(local_praise_comments)

        if filtered_count > 0:
            logger.info(
                f"Moved {filtered_count} praise comments to local display from PR {pr_id}"
            )
    else:
        logger.info("Self-praise filtering disabled")

    # Update result with actual comment count after filtering
    result = CommentPostingResult(
        total_comments=len(comments),
        successful_posts=0,
        failed_posts=0,
        dry_run=dry_run,
        local_praise_comments=[
            {
                "comment_id": comment.comment_id,
                "title": comment.title,
                "content": comment.content,
                "formatted_content": _format_comment_for_azure_devops(comment),
                "type": comment.comment_type.value,
                "severity": comment.severity.value,
                "reasoning": comment.reasoning,
                "business_impact": comment.business_impact,
                "tags": comment.tags,
            }
            for comment in local_praise_comments
        ],
    )

    # Build PR URL for reference using correct format
    result.pr_url = _build_pr_url(org, project, repository, pr_id)

    if dry_run:
        logger.info(f"DRY RUN: Would post {len(comments)} comments to PR {pr_id}")
        validation_passed = True

        for comment in comments:
            try:
                # Validate comment structure
                formatted_comment = _format_comment_for_azure_devops(comment)

                # Additional validation checks for AI agents
                validation_issues = []

                # Check required fields are non-empty
                if not comment.comment_id:
                    validation_issues.append("comment_id cannot be empty")
                if not comment.title:
                    validation_issues.append("title cannot be empty")
                if not comment.content:
                    validation_issues.append("content cannot be empty")

                # Validate file_path and line_number consistency
                if comment.line_number is not None and not comment.file_path:
                    validation_issues.append(
                        "line_number specified but file_path is missing - "
                        "both are required for line-level comments"
                    )

                if comment.file_path and comment.line_number is not None:
                    if comment.line_number < 1:
                        validation_issues.append(
                            f"line_number must be >= 1, got {comment.line_number}"
                        )

                if validation_issues:
                    validation_passed = False
                    result.failures.append(
                        {
                            "comment_id": comment.comment_id,
                            "error": "Validation failed: "
                            + "; ".join(validation_issues),
                            "severity": comment.severity.value,
                        }
                    )
                    result.failed_posts += 1
                else:
                    result.posted_comments.append(
                        {
                            "comment_id": comment.comment_id,
                            "formatted_content": formatted_comment,
                            "file_path": comment.file_path,
                            "line_number": comment.line_number,
                            "type": comment.comment_type.value,
                            "severity": comment.severity.value,
                            "validation": "PASSED",
                        }
                    )
                    result.successful_posts += 1
            except Exception as e:
                # Catch validation errors (e.g., from __post_init__)
                validation_passed = False
                result.failures.append(
                    {
                        "comment_id": getattr(comment, "comment_id", "unknown"),
                        "error": f"Validation exception: {type(e).__name__}: {e}",
                        "severity": getattr(
                            comment, "severity", CommentSeverity.ERROR
                        ).value
                        if hasattr(comment, "severity")
                        else "error",
                    }
                )
                result.failed_posts += 1

        if validation_passed:
            logger.info(
                f"DRY RUN VALIDATION: All {len(comments)} comments passed validation"
            )
        else:
            logger.warning(
                f"DRY RUN VALIDATION: {result.failed_posts} of {len(comments)} comments failed validation"
            )

        return result

    # Post comments in batches to avoid rate limiting
    for i in range(0, len(comments), batch_size):
        batch = comments[i : i + batch_size]

        for comment in batch:
            try:
                success, error_msg = _post_single_comment(
                    org, project, repository, pr_id, comment
                )

                if success:
                    result.successful_posts += 1
                    result.posted_comments.append(
                        {
                            "comment_id": comment.comment_id,
                            "title": comment.title,
                            "file_path": comment.file_path,
                            "line_number": comment.line_number,
                            "type": comment.comment_type.value,
                            "severity": comment.severity.value,
                            "posted": True,
                        }
                    )
                    logger.info(f"Successfully posted comment {comment.comment_id}")
                else:
                    result.failed_posts += 1
                    result.failures.append(
                        {
                            "comment_id": comment.comment_id,
                            "error": error_msg or "Failed to post comment",
                            "title": comment.title,
                            "agent_guidance": "Check Azure CLI authentication with 'az account show'. Verify organization/project/repository permissions. Ensure PR exists and is accessible.",
                        }
                    )
                    logger.warning(
                        f"AGENT_WARNING: Failed to post comment {comment.comment_id}: {error_msg}. "
                        f"Check Azure DevOps connectivity and permissions."
                    )

            except Exception as e:
                result.failed_posts += 1
                error_guidance = _get_error_guidance_for_agents(e)
                result.failures.append(
                    {
                        "comment_id": comment.comment_id,
                        "error": str(e),
                        "title": comment.title,
                        "agent_guidance": error_guidance,
                    }
                )
                logger.error(
                    f"AGENT_ERROR: Error posting comment {comment.comment_id}: {e}. "
                    f"GUIDANCE: {error_guidance}"
                )

    logger.info(
        f"Comment posting complete: {result.successful_posts}/{result.total_comments} successful"
    )
    return result


@mcp.tool()
def post_ai_comments_by_pr_url(
    pr_url: str,
    comments: List[CodeReviewComment],
    dry_run: bool = False,
    batch_size: int = 5,
    filter_self_praise: bool = True,
) -> CommentPostingResult:
    """
    Post AI-generated code review comments to Azure DevOps pull request using PR URL.

    Enhanced version that accepts a PR URL instead of separate org/project/repository/pr_id
    parameters. Automatically parses the URL to extract all needed information and determines
    the correct Azure DevOps URL format (dev.azure.com vs .visualstudio.com).

    This tool is designed for AI agents to post contextual code review comments. The PR URL
    approach eliminates the need for agents to manually extract URL components and automatically
    handles cross-organization URL format detection.

    Args:
        pr_url: Full Azure DevOps PR URL (e.g., https://dev.azure.com/org/project/_git/repo/pullrequest/123)
        comments: List of AI-generated code review comments
        dry_run: If True, validate and format but don't actually post
        batch_size: Number of comments to post in each batch (rate limiting)
        filter_self_praise: If True, show praise locally when posting to own PR

    Returns:
        CommentPostingResult with posting status, failures, and local praise comments

    Raises:
        ValueError: If the PR URL cannot be parsed or is not a valid Azure DevOps PR URL
    """
    # Parse the PR URL to extract organization, project, repository, and PR ID
    org, project, repository, pr_id_str = parse_azure_devops_pr_url(pr_url)

    # Validate that we got all required components
    if not all([org, project, repository, pr_id_str]):
        # Provide detailed guidance for AI agents
        parsed_components = f"org='{org}', project='{project}', repository='{repository}', pr_id='{pr_id_str}'"
        raise ValueError(
            f"TOOL_USAGE_ERROR: Unable to parse Azure DevOps PR URL. "
            f"URL provided: {pr_url}. "
            f"Parsed components: {parsed_components}. "
            f"AGENT_GUIDANCE: Ensure the URL is a complete Azure DevOps PR URL. "
            f"Supported formats: "
            f"1. https://dev.azure.com/[org]/[project]/_git/[repo]/pullrequest/[id] "
            f"2. https://[org].visualstudio.com/DefaultCollection/[project]/_git/[repo]/pullrequest/[id]. "
            f"If the user provided only a PR ID, prompt them for the complete PR URL. "
            f"If the URL appears correct, check for special characters or encoding issues."
        )

    try:
        pr_id = int(pr_id_str)
    except ValueError:
        raise ValueError(
            f"TOOL_USAGE_ERROR: Invalid PR ID extracted from URL. "
            f"URL: {pr_url}, Extracted PR ID: '{pr_id_str}'. "
            f"AGENT_GUIDANCE: The PR ID must be numeric. Check that the URL follows the correct format "
            f"with '/pullrequest/' followed by a number. If the URL is malformed, ask the user "
            f"for a correctly formatted Azure DevOps PR URL."
        )

    # Log the parsed components for AI agent transparency
    logger.info(
        f"Parsed PR URL - Org: {org}, Project: {project}, Repo: {repository}, PR: {pr_id}"
    )

    # Call the original function with the parsed parameters
    return post_ai_generated_comments(
        org=org,
        project=project,
        repository=repository,
        pr_id=pr_id,
        comments=comments,
        dry_run=dry_run,
        batch_size=batch_size,
        filter_self_praise=filter_self_praise,
    )


def _format_comment_for_azure_devops(comment: CodeReviewComment) -> str:
    """Format a code review comment for Azure DevOps display."""

    # Build severity indicator
    severity_indicators = {
        CommentSeverity.INFO: "ℹ️",
        CommentSeverity.SUGGESTION: "💡",
        CommentSeverity.WARNING: "⚠️",
        CommentSeverity.ERROR: "❌",
        CommentSeverity.CRITICAL: "🚨",
    }

    severity_icon = severity_indicators.get(comment.severity, "📝")

    # Build comment header
    header = f"{severity_icon} **{comment.title}**"

    # Add type-specific formatting with severity indicators
    if comment.comment_type == CommentType.SECURITY:
        header = f"🔒 **SECURITY**: {severity_icon} {comment.title}"
    elif comment.comment_type == CommentType.PERFORMANCE:
        header = f"⚡ **PERFORMANCE**: {severity_icon} {comment.title}"
    elif comment.comment_type == CommentType.DOMAIN:
        header = f"💳 **PAYMENT DOMAIN**: {severity_icon} {comment.title}"

    # Build main content
    content_parts = [header, "", comment.content]

    # Add suggested code if present
    if comment.suggested_code:
        content_parts.extend(
            ["", "**💡 Suggested Code:**", "```python", comment.suggested_code, "```"]
        )

    # Add reasoning if present
    if comment.reasoning:
        content_parts.extend(["", "**🤔 Reasoning:**", comment.reasoning])

    # Add business impact if present
    if comment.business_impact:
        content_parts.extend(["", "**📈 Business Impact:**", comment.business_impact])

    # Add tags
    if comment.tags:
        tag_str = " ".join(f"`{tag}`" for tag in comment.tags)
        content_parts.extend(["", f"**🏷️ Tags:** {tag_str}"])

    return "\n".join(content_parts)


def _post_single_comment(
    org: str, project: str, repository: str, pr_id: int, comment: CodeReviewComment
) -> tuple[bool, Optional[str]]:
    """
    Post a single comment to Azure DevOps pull request.

    IMPLEMENTATION: Uses official Microsoft documentation-based ThreadContext structure
    with proper LeftFileStart/End and RightFileStart/End properties per the documented
    CommentThreadContext API specification from Microsoft.TeamFoundation.SourceControl.WebApi.
    """

    try:
        _format_comment_for_azure_devops(comment)

        # Build Azure CLI REST API command
        # Create proper JSON structure based on official Microsoft REST API docs
        comment_data = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": comment.content,
                    "commentType": 1,  # text comment type
                }
            ],
            "status": 1,  # active status
        }

        # ENHANCED DOCUMENTATION-BASED: Line positioning with REAL iteration context
        if comment.file_path and comment.line_number:
            # Get actual iteration data for proper positioning context
            _get_pr_diff_files(org, project, repository, pr_id)

            # Based on Microsoft.TeamFoundation.SourceControl.WebApi.CommentThreadContext
            # AND GitPullRequestCommentThreadContext with IterationContext
            # Based on official Microsoft REST API documentation example
            comment_data["threadContext"] = {
                "filePath": f"/{comment.file_path}",  # Leading slash as in Microsoft example
                "leftFileStart": None,  # null for new files according to example
                "leftFileEnd": None,  # null for new files according to example
                "rightFileStart": {
                    "line": comment.line_number,
                    "offset": 1,  # Must be >= 1, starts at 1 according to docs
                },
                "rightFileEnd": {
                    "line": comment.line_number,
                    "offset": 1,  # Must be >= 1, starts at 1 according to docs
                },
            }

            # Add PullRequestThreadContext with IterationContext
            # Try to get real iteration data, fallback to basic values
            try:
                # Get latest iteration data from Azure DevOps
                iteration_url = _build_api_url(
                    org,
                    project,
                    repository,
                    f"pullRequests/{pr_id}/iterations?api-version=6.0",
                )
                iteration_cmd = [
                    "az",
                    "rest",
                    "--method",
                    "GET",
                    "--uri",
                    iteration_url,
                    "--resource",
                    "https://app.vssps.visualstudio.com",
                ]
                iter_result = subprocess.run(
                    iteration_cmd, capture_output=True, text=True, timeout=30
                )

                if (
                    iter_result.returncode == 0
                    and "<!DOCTYPE html" not in iter_result.stdout
                ):
                    iterations_data = json.loads(iter_result.stdout)
                    if iterations_data.get("value"):
                        latest_iteration = iterations_data["value"][-1]
                        iteration_id = latest_iteration.get("id", 1)

                        comment_data["pullRequestThreadContext"] = {
                            "changeTrackingId": 1,  # Required for iteration support
                            "iterationContext": {
                                "firstComparingIteration": 1,  # Base iteration
                                "secondComparingIteration": iteration_id,  # Current iteration
                            },
                        }
                    else:
                        # Fallback if no iteration data
                        comment_data["pullRequestThreadContext"] = {
                            "changeTrackingId": 1,  # Required for iteration support
                            "iterationContext": {
                                "firstComparingIteration": 1,
                                "secondComparingIteration": 1,
                            },
                        }
                else:
                    # Fallback if API call fails
                    comment_data["pullRequestThreadContext"] = {
                        "changeTrackingId": 1,  # Required for iteration support
                        "iterationContext": {
                            "firstComparingIteration": 1,
                            "secondComparingIteration": 1,
                        },
                    }
            except Exception as e:
                logger.warning(f"Could not get iteration context: {e}")
                # Fallback to basic iteration context
                comment_data["pullRequestThreadContext"] = {
                    "changeTrackingId": 1,  # Required for iteration support
                    "iterationContext": {
                        "firstComparingIteration": 1,
                        "secondComparingIteration": 1,
                    },
                }

            # 🔍 DEBUG: Print the threadContext we're sending
            print("\n🔍 DEBUG - ThreadContext being sent:")
            print(f"File path: {comment_data['threadContext']['filePath']}")
            print(
                f"Line number: {comment_data['threadContext']['rightFileStart']['line']}"
            )
            print(
                f"Full threadContext: {json.dumps(comment_data.get('threadContext'), indent=2)}"
            )
            if "pullRequestThreadContext" in comment_data:
                print(
                    f"PullRequestThreadContext: {json.dumps(comment_data.get('pullRequestThreadContext'), indent=2)}"
                )
            print("🔍 END DEBUG\n")

        comment_json = json.dumps(comment_data)

        # Determine endpoint based on whether this is a threaded reply
        if comment.parent_thread_id:
            # Post a reply to an existing thread
            uri = _build_api_url(
                org,
                project,
                repository,
                f"pullRequests/{pr_id}/threads/{comment.parent_thread_id}/comments?api-version=6.0",
            )
            # For replies, we only need the comment content, not the full thread structure
            reply_data = {
                "content": comment.content,
                "commentType": 1,  # text comment type
                "parentCommentId": 0,  # 0 for new comments in the thread
            }
            comment_json = json.dumps(reply_data)
        else:
            # Create a new thread
            uri = _build_api_url(
                org,
                project,
                repository,
                f"pullRequests/{pr_id}/threads?api-version=6.0",
            )

        cmd_parts = [
            "az",
            "rest",
            "--method",
            "POST",
            "--uri",
            uri,
            "--resource",
            "https://app.vssps.visualstudio.com",  # Updated resource
            "--body",
            comment_json,
            "--headers",
            "Content-Type=application/json",
        ]

        # Execute Azure CLI REST command
        result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return True, None
        else:
            # Enhanced error message with context for AI agents
            error_msg = result.stderr or "Azure CLI command failed"

            # Parse common error patterns and provide guidance
            guidance = ""
            if "401" in error_msg or "Unauthorized" in error_msg:
                guidance = (
                    "AGENT_GUIDANCE: Authentication failed. Common causes: "
                    "1. Azure CLI not authenticated (run 'az login'). "
                    "2. Token expired (re-authenticate with 'az login'). "
                    "3. Insufficient permissions for this repository. "
                    "4. Wrong organization or project specified. "
                    f"Organization: {org}, Project: {project}, Repository: {repository}"
                )
            elif "404" in error_msg or "Not Found" in error_msg:
                guidance = (
                    "AGENT_GUIDANCE: Resource not found. Common causes: "
                    f"1. PR {pr_id} does not exist in repository '{repository}'. "
                    "2. Repository name is incorrect (check spelling and case). "
                    "3. Organization or project name is incorrect. "
                    f"4. User does not have access to view this PR. "
                    f"Verify: org={org}, project={project}, repo={repository}, pr_id={pr_id}"
                )
            elif "403" in error_msg or "Forbidden" in error_msg:
                guidance = (
                    "AGENT_GUIDANCE: Access forbidden. Common causes: "
                    "1. User lacks permission to post comments to this PR. "
                    "2. Repository requires specific access levels. "
                    "3. PR is locked or completed. "
                    f"Check user permissions in repository: {repository}"
                )
            elif "400" in error_msg or "Bad Request" in error_msg:
                guidance = (
                    "AGENT_GUIDANCE: Invalid request. Common causes: "
                    "1. Malformed comment JSON structure. "
                    "2. Invalid file path or line number. "
                    "3. Thread context references non-existent file. "
                    f"Comment: {comment.comment_id}, File: {comment.file_path}, Line: {comment.line_number}"
                )
            elif "timeout" in error_msg.lower():
                guidance = (
                    "AGENT_GUIDANCE: Request timeout. Common causes: "
                    "1. Network connectivity issues. "
                    "2. Azure DevOps service temporarily unavailable. "
                    "3. Large payload or slow connection. "
                    "Recommend: Retry after brief delay, check network connectivity."
                )
            else:
                guidance = (
                    "AGENT_GUIDANCE: Unexpected error. "
                    f"Review error details above. PR: {pr_id}, Comment: {comment.comment_id}. "
                    "If error persists, check Azure DevOps service status."
                )

            enhanced_error = f"{error_msg}\n\n{guidance}"
            logger.error(f"Azure CLI error: {enhanced_error}")
            return False, enhanced_error

    except subprocess.TimeoutExpired:
        error_msg = (
            "TIMEOUT_ERROR: Azure CLI command timed out after 30 seconds. "
            "AGENT_GUIDANCE: This indicates network issues or Azure DevOps service delays. "
            "Recommend: 1) Check network connectivity, 2) Verify Azure DevOps service status, "
            "3) Retry with exponential backoff. "
            f"Context: org={org}, project={project}, repository={repository}, pr_id={pr_id}"
        )
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = (
            f"UNEXPECTED_ERROR: {type(e).__name__}: {e}. "
            "AGENT_GUIDANCE: This is an unexpected error in the comment posting logic. "
            f"Comment ID: {comment.comment_id}, PR: {pr_id}. "
            "Check that comment structure is valid and all required fields are present. "
            f"Comment type: {comment.comment_type}, Severity: {comment.severity}"
        )
        logger.error(error_msg)
        return False, error_msg


def create_ai_comment(
    comment_id: str,
    title: str,
    content: str,
    comment_type: CommentType = CommentType.GENERAL,
    severity: CommentSeverity = CommentSeverity.INFO,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    suggested_code: Optional[str] = None,
    reasoning: Optional[str] = None,
    business_impact: Optional[str] = None,
    tags: Optional[List[str]] = None,
    parent_thread_id: Optional[int] = None,
) -> CodeReviewComment:
    """
    Helper function to create AI-generated code review comments.

    Provides convenient comment creation with sensible defaults
    for AI-generated code review feedback.

    IMPLEMENTATION: file_path and line_number now use documented Azure DevOps API
    structure for proper line positioning with official ThreadContext format.
    """
    return CodeReviewComment(
        comment_id=comment_id,
        comment_type=comment_type,
        severity=severity,
        title=title,
        content=content,
        file_path=file_path,  # Used for line positioning with documented API
        line_number=line_number,  # Used for line positioning with documented API
        suggested_code=suggested_code,
        reasoning=reasoning,
        business_impact=business_impact,
        tags=tags or [],
        metadata={},
        parent_thread_id=parent_thread_id,
    )


def create_security_comment(
    comment_id: str,
    title: str,
    content: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    severity: CommentSeverity = CommentSeverity.ERROR,
    business_impact: Optional[str] = None,
) -> CodeReviewComment:
    """Create a security-focused code review comment."""
    return create_ai_comment(
        comment_id=comment_id,
        title=title,
        content=content,
        comment_type=CommentType.SECURITY,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        business_impact=business_impact,
        tags=["security", "compliance"],
    )


def create_performance_comment(
    comment_id: str,
    title: str,
    content: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    suggested_code: Optional[str] = None,
    reasoning: Optional[str] = None,
) -> CodeReviewComment:
    """Create a performance-focused code review comment."""
    return create_ai_comment(
        comment_id=comment_id,
        title=title,
        content=content,
        comment_type=CommentType.PERFORMANCE,
        severity=CommentSeverity.WARNING,
        file_path=file_path,
        line_number=line_number,
        suggested_code=suggested_code,
        reasoning=reasoning,
        tags=["performance", "optimization"],
    )


def create_domain_comment(
    comment_id: str,
    title: str,
    content: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    severity: CommentSeverity = CommentSeverity.WARNING,
    business_impact: Optional[str] = None,
) -> CodeReviewComment:
    """Create a payment domain-specific code review comment."""
    return create_ai_comment(
        comment_id=comment_id,
        title=title,
        content=content,
        comment_type=CommentType.DOMAIN,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        business_impact=business_impact,
        tags=["payment-domain", "business-logic"],
    )


def _get_error_guidance_for_agents(error: Exception) -> str:
    """
    Provide AI agent-specific guidance based on the type of error encountered.

    This function helps AI agents understand how to troubleshoot and resolve
    common issues when posting comments to Azure DevOps.
    """
    error_str = str(error).lower()

    # Order matters - more specific patterns first
    if "azure cli" in error_str or (
        "az" in error_str and ("not found" in error_str or "command" in error_str)
    ):
        return (
            "AZURE_CLI_ERROR: Azure CLI tool issue. "
            "Ensure Azure CLI is installed and updated: 'az --version'. "
            "Try 'az login' to refresh authentication."
        )

    elif (
        "authentication" in error_str
        or "unauthorized" in error_str
        or "401" in error_str
    ):
        return (
            "AUTHENTICATION_ERROR: Azure CLI authentication failed. "
            "Run 'az login' to authenticate, then 'az account show' to verify. "
            "Ensure the account has access to the Azure DevOps organization."
        )

    elif "forbidden" in error_str or "403" in error_str:
        return (
            "PERMISSION_ERROR: Insufficient permissions for the Azure DevOps resource. "
            "Verify the authenticated user has 'Contribute to pull requests' permission. "
            "Check organization/project/repository access levels."
        )

    elif (
        "not found" in error_str
        or "404" in error_str
        or "does not exist" in error_str
        or "doesn't exist" in error_str
        or "repository not" in error_str
        or "project not" in error_str
    ) and "azure cli" not in error_str:
        return (
            "RESOURCE_NOT_FOUND: The PR, organization, project, or repository doesn't exist or isn't accessible. "
            "Verify the org/project/repository names are correct and the PR ID exists. "
            "Check if the PR was deleted or moved to a different project."
        )

    elif "rate limit" in error_str or "429" in error_str:
        return (
            "RATE_LIMIT_ERROR: Azure DevOps API rate limit exceeded. "
            "Reduce batch_size parameter or add delays between requests. "
            "Wait before retrying the operation."
        )

    elif "json" in error_str and "decode" in error_str:
        return (
            "API_RESPONSE_ERROR: Azure DevOps API returned malformed JSON. "
            "This often indicates an authentication redirect or service outage. "
            "Check 'az account show' and verify Azure DevOps service status."
        )

    elif "timeout" in error_str or "connectionerror" in error_str:
        return (
            "CONNECTIVITY_ERROR: Network timeout or connection failed. "
            "Check internet connectivity to Azure DevOps. "
            "Retry the operation - temporary network issues may resolve automatically."
        )

    else:
        return (
            "GENERAL_ERROR: Unexpected error occurred. "
            "Check Azure CLI authentication ('az account show'), "
            "verify organization/project/repository parameters, "
            "and ensure PR exists and is accessible. "
            "Consider using dry_run=True to test without posting."
        )
