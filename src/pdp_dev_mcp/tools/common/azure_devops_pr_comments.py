"""
Azure DevOps Pull Request Comment Management Tools

This module provides tools for analyzing and managing PR comments in Azure DevOps.
Designed for AI agents and developers to analyze feedback, track comment threads,
and programmatically resolve discussions.

Functions:
    - azure_devops_establish_pr_context: Establish PR context from URL or ID
    - azure_devops_pr_comment_analysis: Analyze all comments on a PR
    - azure_devops_post_pr_comment: Post new comment thread to a PR
    - azure_devops_reply_to_pr_comment: Reply to existing comment thread
    - azure_devops_resolve_pr_comments: Resolve comment threads programmatically
"""

import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from pdp_dev_mcp.mcp_instance import mcp

from .azure_devops_common import AzureDevOpsPRContext, get_project_identifier
from .repository_context import get_repository_context


@mcp.tool()
def azure_devops_establish_pr_context(
    pr_url_or_id: str,
    working_directory: Optional[str] = None,
) -> AzureDevOpsPRContext:
    """
    Establish PR context from URL or ID for subsequent operations.

    Context-first design: Creates a reusable context dataclass that encapsulates
    organization, project, repository, and PR ID. This eliminates repeated URL parsing
    and enables efficient multi-PR workflows.

    Supports both URL and PR ID inputs:
    - URL: Full Azure DevOps PR URL (auto-discovers repository)
    - PR ID: Numeric ID (requires working_directory or active repository context)

    Args:
        pr_url_or_id: Azure DevOps PR URL or numeric PR ID
        working_directory: Repository directory (only needed for PR ID input)

    Returns:
        AzureDevOpsPRContext dataclass with organization, project, repository, pr_id

    Raises:
        ValueError: If PR URL is invalid or repository context cannot be determined
    """
    if not pr_url_or_id:
        raise ValueError(
            "No PR URL or ID provided. Please provide either a PR URL or numeric PR ID."
        )
    
    # Check if input is a URL or a PR ID
    if pr_url_or_id.startswith("http"):
        # Parse PR URL
        url_parts = pr_url_or_id.split("/")

        try:
            # Extract org from either dev.azure.com or visualstudio.com URLs
            if "dev.azure.com" in pr_url_or_id:
                org_index = url_parts.index("dev.azure.com") + 1
                org = url_parts[org_index]
                project_index = org_index + 1
            elif ".visualstudio.com" in pr_url_or_id:
                # Extract org from subdomain
                visualstudio_parts = [part for part in url_parts if ".visualstudio.com" in part]
                org = visualstudio_parts[0].split(".")[0]
                # For visualstudio.com, project comes after the domain
                project_index = url_parts.index(visualstudio_parts[0]) + 1
            else:
                raise ValueError(
                    f"Unsupported Azure DevOps URL format: {pr_url_or_id}. "
                    "Expected dev.azure.com or visualstudio.com URL."
                )

            project = url_parts[project_index]
            repository = url_parts[url_parts.index("_git") + 1]
            pr_id = url_parts[url_parts.index("pullrequest") + 1].split("?")[0]
        except (IndexError, ValueError) as e:
            if isinstance(e, IndexError) or "_git" not in pr_url_or_id or "pullrequest" not in pr_url_or_id:
                raise ValueError(
                    f"Incomplete Azure DevOps PR URL: {pr_url_or_id}. "
                    "Expected format: https://dev.azure.com/org/project/_git/repo/pullrequest/123"
                )
            raise

        return AzureDevOpsPRContext(
            pr_url=pr_url_or_id,
            organization=org,
            project=project,
            repository=repository,
            pr_id=int(pr_id),
            source="url",
        )
    else:
        # Input is a PR ID - need repository context
        try:
            pr_id = int(pr_url_or_id)
        except ValueError:
            raise ValueError(
                f"Invalid PR identifier '{pr_url_or_id}'. "
                "Expected a PR URL or numeric PR ID."
            )

        # Get repository context from cache or working directory
        repo_context = get_repository_context(working_directory)

        if not repo_context or not repo_context.get("success"):
            raise ValueError(
                "Cannot establish PR context from PR ID without repository context. "
                "Either provide a PR URL or ensure repository context is set "
                "(use azure_devops_repository_discovery or set_repository_context first)."
            )

        # Construct PR URL from repository context
        org = repo_context["organization"]
        project = repo_context["project"]
        repo = repo_context["repository"]
        pr_url = f"https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{pr_id}"

        return AzureDevOpsPRContext(
            pr_url=pr_url,
            organization=org,
            project=project,
            repository=repo,
            pr_id=pr_id,
            source="local_context",
        )


@mcp.tool()
def azure_devops_pr_comment_analysis(
    pr_context: Optional[AzureDevOpsPRContext] = None,
    pr_url_or_id: Optional[str] = None,
    save_to_file: bool = True,
    save_directory: Optional[str] = None,
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze all comments on an Azure DevOps pull request.

    Context-first approach: Accepts either:
    1. Pre-established PR context dataclass (AzureDevOpsPRContext) - preferred
    2. PR URL or ID for automatic context establishment

    Enables AI agents to analyze PR feedback from any Azure DevOps repository
    without repeated URL parsing or repository context discovery.

    Args:
        pr_context: Pre-established AzureDevOpsPRContext (recommended)
        pr_url_or_id: Azure DevOps PR URL or PR ID (if no pr_context provided)
        save_to_file: Whether to save full JSON response to file for detailed analysis
        save_directory: Custom directory to save analysis files. Defaults to .copilot/analysis/
        working_directory: Repository directory (only needed if pr_url_or_id is a PR ID)

    Returns detailed comment analysis including active/fixed thread counts, comment authors, and content summaries.
    """
    # Context-first: Use provided context or establish new one
    if pr_context:
        context = pr_context
    else:
        # Establish context from URL or ID
        try:
            context = azure_devops_establish_pr_context(pr_url_or_id, working_directory)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }

    # Extract values from dataclass
    org = context.organization
    project = context.project
    repository = context.repository
    pr_id = context.pr_id

    # Rest of analysis uses established context...
    try:
        # Get repository GUID using REST API (needed for comment threads)
        repos_result = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "GET",
                "--uri",
                f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository}?api-version=6.0",
                "--resource",
                "499b84ac-1321-427f-aa17-267ca6975798",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if repos_result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to get repository information",
                "stderr": repos_result.stderr,
            }

        repo_data = json.loads(repos_result.stdout)
        repo_guid = repo_data.get("id", "")

        # Get project GUID
        project_result = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "GET",
                "--uri",
                f"https://dev.azure.com/{org}/_apis/projects/{project}?api-version=6.0",
                "--resource",
                "499b84ac-1321-427f-aa17-267ca6975798",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if project_result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to get project information",
                "stderr": project_result.stderr,
            }

        project_data = json.loads(project_result.stdout)
        project_guid = project_data.get("id", "")

        if not repo_guid or not project_guid:
            return {
                "success": False,
                "error": "Could not extract repository and project GUIDs from Azure CLI response",
            }

        # Get PR comments using REST API
        comments_result = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "GET",
                "--uri",
                f"https://dev.azure.com/{org}/{project_guid}/_apis/git/repositories/{repo_guid}/pullRequests/{pr_id}/threads?api-version=6.0",
                "--resource",
                "499b84ac-1321-427f-aa17-267ca6975798",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if comments_result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to retrieve PR comments",
                "stderr": comments_result.stderr,
            }

        # Save to file if requested
        file_saved = None
        analysis_folder = None
        if save_to_file:
            # Use custom directory or default to .copilot/analysis/ following team patterns
            if save_directory:
                analysis_folder = save_directory
            else:
                today = datetime.now().strftime("%Y%m%d")
                analysis_folder = f".copilot/analysis/azure-devops-workflow-{today}"

            os.makedirs(analysis_folder, exist_ok=True)
            output_file = os.path.join(
                analysis_folder, f"pr-{pr_id}-comments-analysis.json"
            )

            with open(output_file, "w") as f:
                json.dump(json.loads(comments_result.stdout), f, indent=2)
            file_saved = output_file

        # Parse the JSON response
        comments_data = json.loads(comments_result.stdout)
        threads = comments_data.get("value", [])

        # Analyze threads
        active_threads = [t for t in threads if t.get("status") == "active"]
        fixed_threads = [t for t in threads if t.get("status") == "fixed"]
        total_threads = len(threads)

        # Analyze comment authors and content for better visibility
        comment_authors = {}
        all_comments = []
        active_comments = []

        for thread in threads:
            # Extract thread context (file path and line numbers) if available
            thread_context = thread.get("threadContext", {})
            file_path = thread_context.get("filePath") if thread_context else None
            
            # Safely extract line numbers with None checks
            right_file_start = thread_context.get("rightFileStart") if thread_context else None
            right_file_end = thread_context.get("rightFileEnd") if thread_context else None
            left_file_start = thread_context.get("leftFileStart") if thread_context else None
            left_file_end = thread_context.get("leftFileEnd") if thread_context else None
            
            line_start = None
            line_end = None
            if right_file_start:
                line_start = right_file_start.get("line")
            if line_start is None and left_file_start:
                line_start = left_file_start.get("line")
            
            if right_file_end:
                line_end = right_file_end.get("line")
            if line_end is None and left_file_end:
                line_end = left_file_end.get("line")
            
            if thread.get("comments"):
                for comment in thread["comments"]:
                    author_name = comment.get("author", {}).get(
                        "displayName", "Unknown"
                    )

                    # Count comments by author
                    comment_authors[author_name] = (
                        comment_authors.get(author_name, 0) + 1
                    )

                    # Collect all comments for analysis
                    comment_info = {
                        "thread_id": thread.get("id"),
                        "thread_status": thread.get("status", "unknown"),
                        "author": author_name,
                        "content_preview": comment.get("content", "")[:200] + "..."
                        if len(comment.get("content", "")) > 200
                        else comment.get("content", ""),
                        "full_content": comment.get("content", ""),
                        "created_date": comment.get("publishedDate"),
                        "is_deleted": comment.get("isDeleted", False),
                        "file_path": file_path,
                        "line_start": line_start,
                        "line_end": line_end,
                    }
                    all_comments.append(comment_info)

                    # Track active comments separately
                    if thread.get("status") == "active":
                        active_comments.append(comment_info)

        # Create sample comments by author for immediate visibility
        author_samples = {}
        for author in comment_authors.keys():
            author_comments = [
                c for c in all_comments if c["author"] == author and not c["is_deleted"]
            ]
            if author_comments:
                # Get the most recent non-deleted comment from this author
                author_samples[author] = {
                    "count": comment_authors[author],
                    "latest_comment": author_comments[-1]["content_preview"],
                    "latest_status": author_comments[-1]["thread_status"],
                }

        analysis_result = {
            "success": True,
            "pr_id": pr_id,
            "repository_context": {
                "organization": org,
                "project": project,
                "repository": repository,
            },
            "comment_summary": {
                "total_threads": total_threads,
                "active_threads": len(active_threads),
                "fixed_threads": len(fixed_threads),
                "active_percentage": round(
                    (len(active_threads) / total_threads * 100)
                    if total_threads > 0
                    else 0,
                    1,
                ),
            },
            "comment_authors": comment_authors,
            "author_samples": author_samples,
            "active_comments": active_comments,
            "resolution_ready": len(active_threads) == 0,
            "file_output": {
                "saved": save_to_file,
                "path": file_saved if save_to_file else None,
                "directory_used": analysis_folder if save_to_file else None,
                "save_directory_source": "custom"
                if save_directory
                else "default (.copilot/)",
            },
            "context_based": True,
        }

        return analysis_result

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out - might need authentication or PR doesn't exist",
        }
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def azure_devops_resolve_pr_comments(
    pr_context: AzureDevOpsPRContext,
    thread_ids: List[str],
    status: str = "fixed",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Programmatically resolve Azure DevOps PR comment threads after implementing feedback.
    Supports batch resolution and dry-run mode for validation.

    Enables AI agents to help developers complete the feedback cycle by resolving implemented suggestions
    from all sources including automated tools and human reviewers.

    Args:
        pr_context: Established PR context from azure_devops_establish_pr_context()
        thread_ids: List of comment thread IDs to resolve
        status: Resolution status ('fixed', 'wontFix', 'byDesign', 'closed')
        dry_run: If True, show what would be resolved without making changes

    Returns detailed results of resolution operations.
    """
    valid_statuses = ["fixed", "wontFix", "byDesign", "closed"]
    if status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status '{status}'. Must be one of: {valid_statuses}",
        }

    # Extract values from context dataclass
    org = pr_context.organization
    project = pr_context.project
    repo = pr_context.repository
    pr_id = pr_context.pr_id

    # Construct org URL from context
    org_url = f"https://dev.azure.com/{org}"

    try:
        # Get project GUID to avoid URL encoding issues with project names containing spaces
        # Do NOT use az devops configure as it interferes with multi-project workflows
        try:
            project_id_result = subprocess.run(
                [
                    "az",
                    "devops",
                    "project",
                    "show",
                    "--project",
                    project,
                    "--org",
                    org_url,
                    "--query",
                    "id",
                    "-o",
                    "tsv",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if project_id_result.returncode == 0 and project_id_result.stdout.strip():
                project_identifier = project_id_result.stdout.strip()
            else:
                # Fallback to project name if GUID lookup fails
                project_identifier = project

        except subprocess.TimeoutExpired:
            # Fallback to project name if GUID lookup times out
            project_identifier = project
        except Exception:
            # Fallback for any other exceptions
            project_identifier = project

        # Get repository GUIDs using explicit parameters
        repo_result = subprocess.run(
            [
                "az",
                "repos",
                "show",
                "--repository",
                repo,
                "--project",
                project_identifier,
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if repo_result.returncode != 0:
            return {"success": False, "error": "Failed to get repository information"}

        repo_data = json.loads(repo_result.stdout)
        repo_guid = repo_data.get("id", "")
        project_guid = repo_data.get("project", {}).get("id", "")

        resolution_results = []

        if dry_run:
            for thread_id in thread_ids:
                resolution_results.append(
                    {
                        "thread_id": thread_id,
                        "status": "DRY_RUN",
                        "message": f"Would resolve thread {thread_id} with status '{status}'",
                    }
                )

            return {
                "success": True,
                "dry_run": True,
                "pr_id": pr_id,
                "requested_status": status,
                "threads_to_resolve": len(thread_ids),
                "results": resolution_results,
                "next_steps": "Set dry_run=False to execute the resolution",
            }

        # Resolve each thread
        for thread_id in thread_ids:
            try:
                resolve_result = subprocess.run(
                    [
                        "az",
                        "rest",
                        "--method",
                        "PATCH",
                        "--uri",
                        f"https://dev.azure.com/{org}/{project_guid}/_apis/git/repositories/{repo_guid}/pullRequests/{pr_id}/threads/{thread_id}?api-version=6.0",
                        "--resource",
                        "499b84ac-1321-427f-aa17-267ca6975798",
                        "--body",
                        json.dumps({"status": status}),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if resolve_result.returncode == 0:
                    resolution_results.append(
                        {
                            "thread_id": thread_id,
                            "status": "SUCCESS",
                            "message": f"Thread {thread_id} resolved with status '{status}'",
                        }
                    )
                else:
                    resolution_results.append(
                        {
                            "thread_id": thread_id,
                            "status": "FAILED",
                            "message": f"Failed to resolve thread {thread_id}",
                            "error": resolve_result.stderr,
                        }
                    )

            except Exception as e:
                resolution_results.append(
                    {
                        "thread_id": thread_id,
                        "status": "ERROR",
                        "message": f"Error resolving thread {thread_id}: {str(e)}",
                    }
                )

        successful_resolutions = [
            r for r in resolution_results if r["status"] == "SUCCESS"
        ]
        failed_resolutions = [r for r in resolution_results if r["status"] != "SUCCESS"]

        return {
            "success": len(failed_resolutions) == 0,
            "pr_id": pr_id,
            "resolution_status": status,
            "total_threads": len(thread_ids),
            "successful_resolutions": len(successful_resolutions),
            "failed_resolutions": len(failed_resolutions),
            "results": resolution_results,
            "summary": f"Resolved {len(successful_resolutions)}/{len(thread_ids)} threads with status '{status}'",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


@mcp.tool()
def azure_devops_post_pr_comment(
    pr_context: AzureDevOpsPRContext,
    comment_text: str,
    thread_status: str = "active",
) -> Dict[str, Any]:
    """
    Post a new comment thread to an Azure DevOps pull request.
    
    Enables AI agents and developers to programmatically add comments to PRs for:
    - Providing feedback on code changes
    - Posting analysis results
    - Documenting decisions or suggestions
    - Automated code review comments
    
    Args:
        pr_context: Established PR context from azure_devops_establish_pr_context()
        comment_text: The text content of the comment (supports markdown)
        thread_status: Thread status ('active', 'fixed', 'closed', 'byDesign', 'wontFix')
    
    Returns:
        Dict with success status, thread_id, comment_id, and thread details
    """
    valid_statuses = ["active", "fixed", "closed", "byDesign", "wontFix", "pending", "unknown"]
    if thread_status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid thread status '{thread_status}'. Must be one of: {valid_statuses}",
        }
    
    # Extract values from context dataclass
    org = pr_context.organization
    project = pr_context.project
    repo = pr_context.repository
    pr_id = pr_context.pr_id
    
    # Construct org URL from context
    org_url = f"https://dev.azure.com/{org}"
    
    try:
        # Get project GUID
        project_identifier = get_project_identifier(org_url, project)
        
        # Get repository GUID
        repo_result = subprocess.run(
            [
                "az",
                "repos",
                "show",
                "--repository",
                repo,
                "--project",
                project_identifier,
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if repo_result.returncode != 0:
            return {"success": False, "error": "Failed to get repository information"}
        
        repo_data = json.loads(repo_result.stdout)
        repo_guid = repo_data.get("id", "")
        project_guid = repo_data.get("project", {}).get("id", "")
        
        # Construct comment body
        comment_body = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": comment_text,
                    "commentType": 1
                }
            ],
            "status": thread_status
        }
        
        # Post comment using az rest
        post_result = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "POST",
                "--uri",
                f"https://dev.azure.com/{org}/{project_guid}/_apis/git/repositories/{repo_guid}/pullRequests/{pr_id}/threads?api-version=7.0",
                "--resource",
                "499b84ac-1321-427f-aa17-267ca6975798",
                "--body",
                json.dumps(comment_body),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if post_result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to post comment",
                "details": post_result.stderr,
            }
        
        # Parse response
        response_data = json.loads(post_result.stdout)
        thread_id = response_data.get("id")
        comments = response_data.get("comments", [])
        comment_id = comments[0].get("id") if comments else None
        
        return {
            "success": True,
            "thread_id": thread_id,
            "comment_id": comment_id,
            "thread_status": response_data.get("status", thread_status),
            "pr_id": pr_id,
            "comment_text": comment_text,
            "message": f"Comment posted successfully to PR {pr_id}",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


@mcp.tool()
def azure_devops_reply_to_pr_comment(
    pr_context: AzureDevOpsPRContext,
    thread_id: int,
    comment_text: str,
    parent_comment_id: int = 1,
) -> Dict[str, Any]:
    """
    Reply to an existing comment thread in an Azure DevOps pull request.
    
    Enables AI agents and developers to programmatically respond to feedback:
    - Answering questions from reviewers
    - Clarifying implementation decisions
    - Providing status updates
    - Continuing conversations in existing threads
    
    Args:
        pr_context: Established PR context from azure_devops_establish_pr_context()
        thread_id: ID of the thread to reply to
        comment_text: The text content of the reply (supports markdown)
        parent_comment_id: ID of the comment being replied to (default: 1, the first comment)
    
    Returns:
        Dict with success status, comment_id, thread_id, and reply details
    """
    # Extract values from context dataclass
    org = pr_context.organization
    project = pr_context.project
    repo = pr_context.repository
    pr_id = pr_context.pr_id
    
    # Construct org URL from context
    org_url = f"https://dev.azure.com/{org}"
    
    try:
        # Get project GUID
        project_identifier = get_project_identifier(org_url, project)
        
        # Get repository GUID
        repo_result = subprocess.run(
            [
                "az",
                "repos",
                "show",
                "--repository",
                repo,
                "--project",
                project_identifier,
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if repo_result.returncode != 0:
            return {"success": False, "error": "Failed to get repository information"}
        
        repo_data = json.loads(repo_result.stdout)
        repo_guid = repo_data.get("id", "")
        project_guid = repo_data.get("project", {}).get("id", "")
        
        # Construct reply body
        reply_body = {
            "content": comment_text,
            "parentCommentId": parent_comment_id,
            "commentType": 1
        }
        
        # Post reply using az rest
        post_result = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "POST",
                "--uri",
                f"https://dev.azure.com/{org}/{project_guid}/_apis/git/repositories/{repo_guid}/pullRequests/{pr_id}/threads/{thread_id}/comments?api-version=7.0",
                "--resource",
                "499b84ac-1321-427f-aa17-267ca6975798",
                "--body",
                json.dumps(reply_body),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if post_result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to post reply",
                "details": post_result.stderr,
            }
        
        # Parse response
        response_data = json.loads(post_result.stdout)
        comment_id = response_data.get("id")
        
        return {
            "success": True,
            "comment_id": comment_id,
            "thread_id": thread_id,
            "parent_comment_id": parent_comment_id,
            "pr_id": pr_id,
            "comment_text": comment_text,
            "message": f"Reply posted successfully to thread {thread_id} in PR {pr_id}",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }
