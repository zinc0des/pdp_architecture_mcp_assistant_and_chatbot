"""
Azure DevOps Pull Request Review Status Tools

This module provides tools for getting PR review status, analyzing approvals and rejections,
detecting vote invalidation, and sending review reminders.

Functions:
    - azure_devops_get_pr_review_status: Get comprehensive review status including vote invalidation
    - azure_devops_send_pr_review_reminders: Analyze PRs to identify pending reviewers
"""

import json
import os
import subprocess
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pdp_dev_mcp.mcp_instance import mcp

from .azure_devops_common import create_analysis_folder, parse_azure_devops_date, get_project_identifier
from .repository_context import get_repository_context


@dataclass
class ReviewerInfo:
    """Information about a PR reviewer"""

    display_name: str
    unique_name: str  # email
    vote: int  # 0=no vote, 10=approved, -10=rejected, 5=approved with suggestions
    is_required: bool
    is_container: bool  # True for team reviewers


@dataclass
class PendingPR:
    """PR that needs review reminders"""

    pr_id: int
    title: str
    author: str
    creation_date: datetime
    repository: str
    organization: str
    project: str
    web_url: str
    pending_reviewers: List[ReviewerInfo]
    days_open: int
    merge_status: str  # 'succeeded', 'conflicts', 'queued', 'rejectedByPolicy', 'failure'
    has_conflicts: bool
    needs_approvals_count: int = 0  # How many more approvals are needed
    valid_approvals_count: int = 0  # How many valid approvals exist


def _determine_vote_status(
    reviewer: Dict[str, Any],
    stale_voter_ids: Optional[set] = None
) -> Dict[str, Any]:
    """
    Determine the status of a reviewer's vote using Azure DevOps branch policy data.
    
    Args:
        reviewer: Reviewer data from Azure DevOps API
        stale_voter_ids: Set of reviewer IDs marked as stale by Azure DevOps branch policies
        
    Returns:
        Dict with vote status details including:
        - name: Reviewer display name
        - email: Reviewer unique name/email
        - vote: Vote value (-10, -5, 0, 5, 10)
        - vote_text: Human-readable vote description
        - vote_invalidated: Whether their vote was invalidated by commit
        - invalidated_by_commit: Whether commit came after their vote
    """
    vote = reviewer.get("vote", 0)
    display_name = reviewer.get("displayName", "Unknown")
    unique_name = reviewer.get("uniqueName", "")
    reviewer_id = reviewer.get("id", "")
    is_container = reviewer.get("isContainer", False)  # True for teams/groups
    
    # Map vote values to text
    vote_text_map = {
        10: "Approved",
        5: "Approved with suggestions",
        0: "No vote",
        -5: "Waiting for author",
        -10: "Rejected"
    }
    vote_text = vote_text_map.get(vote, f"Unknown vote: {vote}")
    
    # Use Azure DevOps branch policy staleness determination
    # This is authoritative and handles all branch policy rules correctly
    vote_invalidated = False
    invalidated_by_commit = False
    
    if vote in [10, 5] and stale_voter_ids and reviewer_id in stale_voter_ids:
        vote_invalidated = True
        invalidated_by_commit = True
    
    return {
        "name": display_name,
        "email": unique_name,
        "vote": vote,
        "vote_text": vote_text,
        "vote_invalidated": vote_invalidated,
        "invalidated_by_commit": invalidated_by_commit,
        "is_container": is_container,
    }


@mcp.tool()
def azure_devops_get_pr_review_status(
    pr_id: int,
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get comprehensive review status for a pull request, including vote invalidation analysis.
    
    This tool provides detailed PR review status information that goes beyond simple "pending reviewers":
    - Identifies which approvals have been invalidated by subsequent commits
    - Shows all vote types (approve, reject, waiting for author, approved with suggestions)
    - Calculates how many more approvals are needed since the last commit
    - Provides clear, actionable summaries for developers and DevOps teams
    
    Key features:
    - **Vote Invalidation Detection**: Branch policies typically require approvals "since last commit",
      so this tool identifies which approvals were given before the latest commit and are now invalid.
    - **Comprehensive Vote Status**: Shows approved, rejected, waiting for author, and pending reviewers.
    - **Actionable Summaries**: Provides clear text summaries like "Needs 2 approvals (3 invalidated by recent commits)".
    - **Error Resilience**: Gracefully handles missing timestamps, API failures, and malformed data.
    
    Use cases:
    - Understanding why a PR shows as needing review despite having approvals
    - Creating status updates for Teams messages
    - Identifying blocking rejections or waiting-for-author votes
    - Determining which specific reviewers need to re-approve after code changes
    
    Args:
        pr_id: Pull request ID number
        working_directory: Optional repository directory (uses repository context if not provided)
        
    Returns:
        Comprehensive PR review status including:
        - success: Whether the operation succeeded
        - pr_id: The PR ID that was analyzed
        - title: PR title
        - author: PR author name
        - url: Web URL to the PR
        - days_open: How many days the PR has been open
        - last_commit_date: When the most recent commit was made
        - approval_status: Detailed approval status with:
          - is_approved: Whether PR has enough valid approvals
          - needs_approvals_count: How many more approvals needed
          - has_rejection: Whether any reviewer rejected
          - valid_approvers: Reviewers with valid approval votes since last commit
          - invalidated_approvers: Reviewers whose approvals were invalidated by commits
          - rejecting_reviewers: Reviewers who rejected the PR
          - waiting_reviewers: Reviewers waiting for author
          - pending_reviewers: Reviewers who haven't voted yet
        - summary: Human-readable status summary
        - error: Error message if operation failed
        
    Example:
        >>> result = azure_devops_get_pr_review_status(pr_id=14446184)
        >>> print(result["summary"])
        "Needs 2 approvals (2 previous approvals invalidated by recent commit)"
    """
    # Get repository context
    repo_info = get_repository_context(working_directory)
    if not repo_info["success"]:
        error_msg = repo_info.get("error", "Unknown repository context error")
        suggestion = repo_info.get(
            "suggestion", "Use set_repository_context() first or provide working_directory"
        )
        
        return {
            "success": False,
            "error": f"Repository context failed: {error_msg}",
            "suggestion": suggestion,
        }
    
    project = repo_info["project"]
    repo = repo_info["repository"]
    org_url = repo_info["org_url"]
    
    try:
        # Get PR details with reviewers and commits
        pr_cmd = [
            "az",
            "repos",
            "pr",
            "show",
            "--id",
            str(pr_id),
            "--org",
            org_url,
            "--output",
            "json",
        ]
        
        pr_result = subprocess.run(
            pr_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30,
        )
        
        if pr_result.returncode != 0:
            error_msg = pr_result.stderr or "Unknown error"
            
            # Provide specific error messages for common cases
            if "not found" in error_msg.lower() or "TF401180" in error_msg:
                return {
                    "success": False,
                    "error": f"PR #{pr_id} not found or access denied. Verify the PR ID and your permissions.",
                }
            elif "permission" in error_msg.lower() or "TF401019" in error_msg:
                return {
                    "success": False,
                    "error": f"Permission denied accessing PR #{pr_id}. You may not have access to this repository.",
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to retrieve PR #{pr_id}: {error_msg}",
                }
        
        # Parse PR details
        try:
            pr_details = json.loads(pr_result.stdout)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse API response for PR #{pr_id}. JSON error: {str(e)}",
            }
        
        # Validate required fields
        if "pullRequestId" not in pr_details:
            return {
                "success": False,
                "error": "API response missing required field 'pullRequestId'. Response may be incomplete.",
            }
        
        # Extract PR metadata
        title = pr_details.get("title", "Unknown Title")
        created_by = pr_details.get("createdBy", {})
        author = created_by.get("displayName", "Unknown Author")
        creation_date = parse_azure_devops_date(pr_details.get("creationDate", ""))
        repository = pr_details.get("repository", {})
        reviewers = pr_details.get("reviewers", [])
        
        # Calculate days open
        days_open = 0
        if creation_date:
            days_open = (datetime.now() - creation_date).days
        
        # Get latest commit date - use REST API as Azure CLI doesn't return commit timestamps
        latest_commit_date = None
        commit_fetch_error = None
        
        try:
            # Extract project and repo names
            repo_name = repository.get("name", "")
            project_name = repository.get("project", {}).get("name", "")
            
            if project_name and repo_name:
                # URL encode the project name (e.g., "Universal Store" -> "Universal%20Store")
                project_encoded = urllib.parse.quote(project_name)
                
                # Build REST API URL for commits
                base_url = org_url.rstrip('/')
                commits_url = f"{base_url}/{project_encoded}/_apis/git/repositories/{repo_name}/pullRequests/{pr_id}/commits?api-version=7.0"
                
                # Use az rest to call the REST API (handles authentication automatically)
                commits_result = subprocess.run(
                    [
                        "az",
                        "rest",
                        "--method",
                        "GET",
                        "--uri",
                        commits_url,
                        "--resource",
                        "499b84ac-1321-427f-aa17-267ca6975798",
                        "--output",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30,
                )
                
                if commits_result.returncode == 0:
                    try:
                        commits_response = json.loads(commits_result.stdout)
                        commits = commits_response.get("value", [])
                        
                        if commits and len(commits) > 0:
                            # Get the most recent commit (first in the list)
                            latest_commit = commits[0]
                            
                            # Try committer date first, then author date
                            commit_date_str = None
                            if "committer" in latest_commit:
                                commit_date_str = latest_commit["committer"].get("date")
                            elif "author" in latest_commit:
                                commit_date_str = latest_commit["author"].get("date")
                            
                            if commit_date_str:
                                latest_commit_date = parse_azure_devops_date(commit_date_str)
                            else:
                                commit_fetch_error = "No commit date found in commit data"
                        else:
                            commit_fetch_error = f"No commits in response (got {len(commits)} commits)"
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        # If we can't parse commits, continue without them (graceful degradation)
                        commit_fetch_error = f"JSON parse error: {str(e)}"
                else:
                    commit_fetch_error = f"API call failed with code {commits_result.returncode}: {commits_result.stderr[:100]}"
            else:
                commit_fetch_error = f"Missing data - project:{project_name}, repo:{repo_name}"
        except subprocess.TimeoutExpired:
            # Continue without commit data if timeout
            commit_fetch_error = "Timeout getting commits"
        except Exception as e:
            # Continue without commit data for any other errors
            commit_fetch_error = f"Exception: {type(e).__name__}: {str(e)}"
        
        # Get stale approval information from PR properties
        # Azure DevOps tracks vote staleness in the OneReviewPolicyPilot property
        stale_voter_ids = set()
        try:
            # Reuse project and repo names from commits fetch
            repo_name = repository.get("name", "")
            project_name = repository.get("project", {}).get("name", "")
            
            if project_name and repo_name:
                # URL encode the project name
                project_encoded = urllib.parse.quote(project_name)
                
                # Build REST API URL for properties
                base_url = org_url.rstrip('/')
                properties_url = f"{base_url}/{project_encoded}/_apis/git/repositories/{repo_name}/pullRequests/{pr_id}/properties?api-version=7.0"
                
                # Use az rest to call the REST API
                properties_result = subprocess.run(
                    [
                        "az",
                        "rest",
                        "--method",
                        "GET",
                        "--uri",
                        properties_url,
                        "--resource",
                        "499b84ac-1321-427f-aa17-267ca6975798",
                        "--output",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30,
                )
                
                if properties_result.returncode == 0:
                    properties_data = json.loads(properties_result.stdout)
                    one_review_policy = properties_data.get("value", {}).get("OneReviewPolicyPilot", {})
                    policy_value = one_review_policy.get("$value", "")
                    
                    if policy_value:
                        # Parse the nested JSON string
                        policy_data = json.loads(policy_value)
                        owner_paths = policy_data.get("OwnerPaths", [])
                        
                        for owner_path in owner_paths:
                            owner_votes = owner_path.get("OwnerVotes", [])
                            for vote in owner_votes:
                                # Check if this vote is marked as stale by Azure DevOps
                                if vote.get("ApprovalState") == "Stale":
                                    voter_id = vote.get("Id")
                                    if voter_id:
                                        stale_voter_ids.add(voter_id)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, Exception):
            # If we can't get stale approval data, continue without it
            pass
        
        # Build web URL
        web_url = pr_details.get("url", "")
        if not web_url:
            # Construct from context if not in response
            web_url = f"{org_url}{project}/_git/{repo}/pullrequest/{pr_id}"
        # Clean up DefaultCollection artifacts
        web_url = web_url.replace("/DefaultCollection/", "/")
        
        # Analyze reviewers
        valid_approvers = []
        invalidated_approvers = []
        rejecting_reviewers = []
        waiting_reviewers = []
        pending_reviewers = []
        
        for reviewer in reviewers:
            vote_status = _determine_vote_status(reviewer, stale_voter_ids)
            vote = vote_status["vote"]
            
            if vote == 10 or vote == 5:  # Approved or approved with suggestions
                if vote_status["vote_invalidated"]:
                    invalidated_approvers.append(vote_status)
                else:
                    valid_approvers.append(vote_status)
            elif vote == -10:  # Rejected
                rejecting_reviewers.append(vote_status)
            elif vote == -5:  # Waiting for author
                waiting_reviewers.append(vote_status)
            elif vote == 0:  # No vote
                pending_reviewers.append(vote_status)
        
        # Calculate approval requirements
        # Standard policy: need 2 approvals since last commit
        # Teams/distribution lists don't count - only individual approvals
        required_approvals = 2
        individual_approvals = [a for a in valid_approvers if not a.get("is_container", False)]
        current_valid_approvals = len(individual_approvals)
        needs_approvals_count = max(0, required_approvals - current_valid_approvals)
        
        # Determine if PR is approved
        is_approved = needs_approvals_count == 0 and len(rejecting_reviewers) == 0
        
        # Determine blocking status
        has_rejection = len(rejecting_reviewers) > 0
        
        # Build summary
        summary_parts = []
        
        if has_rejection:
            rejector_names = ", ".join([r["name"] for r in rejecting_reviewers])
            summary_parts.append(f"BLOCKED: Rejected by {rejector_names}")
        
        if is_approved:
            summary_parts.append(f"Ready to merge (approved by {current_valid_approvals} reviewers)")
        else:
            approval_text = f"Needs {needs_approvals_count} approval(s)"
            if len(invalidated_approvers) > 0:
                invalidated_text = f"{len(invalidated_approvers)} previous approval(s) invalidated"
                approval_text += f" ({invalidated_text})"
            summary_parts.append(approval_text)
        
        if len(waiting_reviewers) > 0:
            waiter_names = ", ".join([r["name"] for r in waiting_reviewers])
            summary_parts.append(f"Waiting for author (from: {waiter_names})")
        
        summary = ". ".join(summary_parts) if summary_parts else "No review activity"
        
        return {
            "success": True,
            "pr_id": pr_id,
            "title": title,
            "author": author,
            "url": web_url,
            "days_open": days_open,
            "last_commit_date": latest_commit_date.isoformat() if latest_commit_date else None,
            "approval_status": {
                "is_approved": is_approved,
                "needs_approvals_count": needs_approvals_count,
                "has_rejection": has_rejection,
                "valid_approvers": valid_approvers,
                "invalidated_approvers": invalidated_approvers,
                "rejecting_reviewers": rejecting_reviewers,
                "waiting_reviewers": waiting_reviewers,
                "pending_reviewers": pending_reviewers,
            },
            "summary": summary,
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Timeout while retrieving PR #{pr_id}. Check network connectivity and Azure CLI authentication.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error analyzing PR #{pr_id}: {str(e)}",
        }


@mcp.tool()
def azure_devops_send_pr_review_reminders(
    max_days_old: int = 30,
    current_user_only: bool = True,
    working_directory: Optional[str] = None,
    save_analysis: bool = True,
) -> Dict[str, Any]:
    """
    Analyze pull requests to identify pending reviewers and PRs needing attention.

    This tool discovers pull requests that need review attention by identifying pending
    reviewers who haven't voted yet. By default, it focuses on PRs created by the current
    user, following the principle that PR creators are responsible for chasing reviewers
    to ensure timely completion.

    Integrates with existing Azure DevOps workflow tools and follows team collaboration patterns.

    Enables AI agents to help developers maintain review velocity by providing actionable
    insights about which PRs need attention and who to follow up with manually.

    Args:
        max_days_old: Only analyze PRs created within this many days (default: 30)
        current_user_only: If True, only analyze PRs created by the current user (default: True)
        working_directory: Optional repository directory (uses repository context if not provided)
        save_analysis: Save detailed analysis to .copilot folder (default: True)

    Returns:
        Analysis results including PRs found, pending reviewers per PR, and actionable summary
    """

    # Get repository context
    repo_info = get_repository_context(working_directory)
    if not repo_info["success"]:
        error_msg = repo_info.get("error", "Unknown repository context error")
        suggestion = repo_info.get(
            "suggestion", "Use mcp_pdp-dev-mcp_set_repository_context() first"
        )

        return {
            "success": False,
            "error": f"Repository context failed: {error_msg}",
            "suggestion": suggestion,
        }

    org = repo_info["organization"]
    project = repo_info["project"]
    repo = repo_info["repository"]

    try:
        # Get project GUID to avoid URL encoding issues with project names containing spaces
        # Do NOT use az devops configure as it interferes with multi-project workflows
        project_identifier = get_project_identifier(project, repo_info["org_url"])

        # Build the PR list command with explicit parameters
        pr_cmd = [
            "az",
            "repos",
            "pr",
            "list",
            "--repository",
            repo,
            "--project",
            project_identifier,
            "--org",
            repo_info["org_url"],
            "--status",
            "active",
            "--output",
            "json",
        ]

        # Add creator filter if only current user's PRs are wanted
        if current_user_only:
            # Get current user info
            user_result = subprocess.run(
                ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
            )

            if user_result.returncode == 0:
                current_user = user_result.stdout.strip()
                pr_cmd.extend(["--creator", current_user])
            else:
                return {
                    "success": False,
                    "error": f"Failed to get current user info: {user_result.stderr}",
                }

        # Get open PRs (filtered by creator if specified)
        pr_result = subprocess.run(
            pr_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60,
        )

        if pr_result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to retrieve PRs: {pr_result.stderr}",
            }

        prs = json.loads(pr_result.stdout)

        # Filter PRs by age and get detailed reviewer information
        cutoff_date = datetime.now() - timedelta(days=max_days_old)
        pending_prs = []
        reminder_summary = {
            "total_prs": len(prs),
            "prs_needing_reminders": 0,
            "total_pending_reviewers": 0,
            "prs_with_work_items": 0,
            "prs_without_work_items": 0,
            "prs_with_conflicts": 0,
        }

        for pr in prs:
            # Skip draft PRs - they're not ready for review yet
            if pr.get("isDraft", False):
                continue
            
            # Parse creation date (Azure DevOps format: 2024-01-15T10:30:00.000Z)
            created_date_str = pr.get("creationDate", "")
            try:
                # Remove microseconds and timezone info for consistent parsing
                created_date_clean = created_date_str.split(".")[0] + "Z"
                created_date = datetime.fromisoformat(
                    created_date_clean.replace("Z", "+00:00")
                )
                created_date = created_date.replace(tzinfo=None)  # Make timezone-naive
            except (ValueError, IndexError, TypeError):
                # Skip PRs with unparseable dates
                continue

            if created_date < cutoff_date:
                continue  # Skip old PRs

            # Get detailed PR info including reviewers
            pr_detail_result = subprocess.run(
                [
                    "az",
                    "repos",
                    "pr",
                    "show",
                    "--id",
                    str(pr["pullRequestId"]),
                    "--org",
                    repo_info["org_url"],
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
            )

            if pr_detail_result.returncode != 0:
                continue  # Skip PRs we can't get details for

            pr_detail = json.loads(pr_detail_result.stdout)

            # Extract pending reviewers (those who haven't voted)
            pending_reviewers = []
            for reviewer in pr_detail.get("reviewers", []):
                if reviewer.get("vote", 0) == 0:  # No vote yet
                    pending_reviewers.append(
                        ReviewerInfo(
                            display_name=reviewer.get("displayName", ""),
                            unique_name=reviewer.get("uniqueName", ""),
                            vote=reviewer.get("vote", 0),
                            is_required=reviewer.get("isRequired", True),
                            is_container=reviewer.get("isContainer", False),
                        )
                    )

            # Calculate needs_approvals_count using same logic as review status tool
            # This catches PRs that need approvals even if everyone already voted
            reviewers = pr_detail.get("reviewers", [])
            commits = pr_detail.get("commits", [])
            
            # Get latest commit timestamp
            latest_commit_date = None
            if commits:
                try:
                    commit_date_str = commits[0].get("committer", {}).get("date", "")
                    if commit_date_str:
                        commit_date_clean = commit_date_str.split(".")[0] + "Z"
                        latest_commit_date = datetime.fromisoformat(commit_date_clean.replace("Z", "+00:00"))
                        latest_commit_date = latest_commit_date.replace(tzinfo=None)
                except (ValueError, IndexError, TypeError):
                    pass
            
            # Count valid individual approvals (vote=10, after last commit, not a team)
            valid_approvals = 0
            for reviewer in reviewers:
                if reviewer.get("vote", 0) == 10 and not reviewer.get("isContainer", False):
                    # Check if vote is after last commit
                    voted_for = reviewer.get("votedFor", [])
                    if voted_for and latest_commit_date:
                        try:
                            vote_date_str = voted_for[0].get("date", "")
                            vote_date_clean = vote_date_str.split(".")[0] + "Z"
                            vote_date = datetime.fromisoformat(vote_date_clean.replace("Z", "+00:00"))
                            vote_date = vote_date.replace(tzinfo=None)
                            if vote_date > latest_commit_date:
                                valid_approvals += 1
                        except (ValueError, IndexError, TypeError, KeyError):
                            pass
                    elif not voted_for or not latest_commit_date:
                        # No commit timestamp or vote timestamp, count the approval
                        valid_approvals += 1
            
            required_approvals = 2
            needs_approvals_count = max(0, required_approvals - valid_approvals)
            
            # Check for active comment threads that need author attention
            # Active threads can come from reviewers or non-reviewers
            # Best practice: address all comments before prompting for more reviews
            threads = pr_detail.get("threads", [])
            has_active_comments = any(
                thread.get("status") == "active" for thread in threads
            )

            # Include PR if it has pending reviewers OR needs more approvals
            # BUT skip if there are active comment threads (author must respond first)
            # This catches:
            # 1. Fresh PRs with only teams (no individuals joined yet)
            # 2. PRs where everyone voted but approvals were invalidated by commits
            # 3. Excludes PRs with active comments (ball is in author's court)
            if (pending_reviewers or needs_approvals_count > 0) and not has_active_comments:
                days_open = (datetime.now() - created_date).days
                
                # Extract merge status
                merge_status = pr_detail.get("mergeStatus", "unknown")
                has_conflicts = merge_status == "conflicts"

                pending_pr = PendingPR(
                    pr_id=pr["pullRequestId"],
                    title=pr.get("title", ""),
                    author=pr.get("createdBy", {}).get("displayName", ""),
                    creation_date=created_date,
                    repository=repo,
                    organization=org,
                    project=project,
                    web_url=pr.get("_links", {}).get("web", {}).get("href", ""),
                    pending_reviewers=pending_reviewers,
                    days_open=days_open,
                    merge_status=merge_status,
                    has_conflicts=has_conflicts,
                    needs_approvals_count=needs_approvals_count,  # Add approval info
                    valid_approvals_count=valid_approvals,  # Add valid approvals count
                )

                pending_prs.append(pending_pr)
                reminder_summary["prs_needing_reminders"] += 1
                reminder_summary["total_pending_reviewers"] += len(pending_reviewers)
                
                # Track merge conflicts
                if has_conflicts:
                    reminder_summary["prs_with_conflicts"] += 1

        # Correlate PRs with work items (only for same-org scenarios)
        work_item_map = {}  # pr_url -> work_item_id
        same_org = any(domain in repo_info["org_url"] for domain in ["msazure.visualstudio.com", "dev.azure.com"])

        if same_org and pending_prs:
            try:
                # Query work items that might reference PRs
                # Look in recent work items to avoid scanning entire backlog
                wi_query = f"""
                SELECT [System.Id], [System.Title], [System.Description]
                FROM workitems
                WHERE [System.TeamProject] = '{project}'
                AND [System.State] <> 'Removed'
                AND [System.ChangedDate] >= @Today - 90
                ORDER BY [System.ChangedDate] DESC
                """

                wi_result = subprocess.run(
                    [
                        "az",
                        "boards",
                        "query",
                        "--wiql",
                        wi_query,
                        "--org",
                        repo_info["org_url"],
                        "--output",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30,
                )

                if wi_result.returncode == 0:
                    work_items = json.loads(wi_result.stdout)

                    # For each work item, check if description contains PR URLs
                    for wi in work_items:
                        wi_id = wi["id"]

                        # Get full work item details including description
                        wi_detail_result = subprocess.run(
                            [
                                "az",
                                "boards",
                                "work-item",
                                "show",
                                "--id",
                                str(wi_id),
                                "--org",
                                repo_info["org_url"],
                                "--output",
                                "json",
                            ],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='replace',
                            timeout=10,
                        )

                        if wi_detail_result.returncode == 0:
                            wi_data = json.loads(wi_detail_result.stdout)
                            description = wi_data.get("fields", {}).get(
                                "System.Description", ""
                            )

                            # Check each pending PR URL against this work item
                            for pending_pr in pending_prs:
                                pr_id_str = str(pending_pr.pr_id)
                                # Match PR ID in description using word boundaries to avoid false positives
                                if (
                                    f" {pr_id_str} " in f" {description} "
                                    or pending_pr.web_url in description
                                ):
                                    work_item_map[pending_pr.web_url] = wi_id
                                    break

            except subprocess.TimeoutExpired:
                # Work item correlation is optional - don't fail if timeout
                pass
            except Exception:
                # Work item correlation is optional - don't fail on errors
                pass

        # Build actionable summary for each PR
        pr_summaries = []
        prs_with_work_items = 0
        prs_without_work_items = 0

        for pr in pending_prs:
            pending_reviewer_list = [
                {
                    "name": r.display_name,
                    "email": r.unique_name,
                    "is_required": r.is_required,
                }
                for r in pr.pending_reviewers
                if not r.is_container  # Skip team reviewers
            ]

            # Check if this PR has a work item
            work_item_id = work_item_map.get(pr.web_url)
            if work_item_id:
                prs_with_work_items += 1
            else:
                prs_without_work_items += 1

            pr_summaries.append(
                {
                    "pr_id": pr.pr_id,
                    "title": pr.title,
                    "author": pr.author,
                    "days_open": pr.days_open,
                    "web_url": pr.web_url,
                    "pending_reviewers": pending_reviewer_list,
                    "pending_reviewer_count": len(pending_reviewer_list),
                    "needs_approvals_count": pr.needs_approvals_count,
                    "valid_approvals_count": pr.valid_approvals_count,
                    "work_item_id": work_item_id,
                    "has_work_item": work_item_id is not None,
                    "merge_status": pr.merge_status,
                    "has_conflicts": pr.has_conflicts,
                }
            )

        # Update summary with work item tracking stats
        reminder_summary["prs_with_work_items"] = prs_with_work_items
        reminder_summary["prs_without_work_items"] = prs_without_work_items

        # Save analysis if requested
        analysis_file = None
        if save_analysis:
            analysis_folder = create_analysis_folder()
            analysis_data = {
                "operation": "pr_review_reminders",
                "timestamp": datetime.now().isoformat(),
                "repository_context": {
                    "organization": org,
                    "project": project,
                    "repository": repo,
                },
                "parameters": {
                    "max_days_old": max_days_old,
                    "current_user_only": current_user_only,
                },
                "summary": reminder_summary,
                "pending_prs": [
                    {
                        "pr_id": pr.pr_id,
                        "title": pr.title,
                        "author": pr.author,
                        "days_open": pr.days_open,
                        "web_url": pr.web_url,
                        "pending_reviewers": [
                            {
                                "display_name": r.display_name,
                                "unique_name": r.unique_name,
                                "is_required": r.is_required,
                                "is_container": r.is_container,
                            }
                            for r in pr.pending_reviewers
                        ],
                    }
                    for pr in pending_prs
                ],
                "pr_summaries": pr_summaries,
            }

            analysis_file = os.path.join(
                analysis_folder,
                f"pr_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, indent=2, default=str)

        return {
            "success": True,
            "current_user_only": current_user_only,
            "repository_context": {
                "organization": org,
                "project": project,
                "repository": repo,
            },
            "summary": reminder_summary,
            "pending_prs": pr_summaries,
            "analysis_file": analysis_file,
            "next_steps": (
                [
                    f"⚠️  {reminder_summary['prs_with_conflicts']} PRs blocked by merge conflicts - resolve conflicts first",
                ]
                if reminder_summary["prs_with_conflicts"] > 0
                else []
            )
            + [
                "Review pending_prs list to see who needs follow-up",
                "Manually message reviewers via Teams or email",
                "Check analysis_file for full details",
                "Focus on PRs with required reviewers first",
            ]
            + (
                [
                    f"Create work items for {prs_without_work_items} PRs without tracking",
                    "Link work items by including PR URLs in descriptions",
                ]
                if prs_without_work_items > 0
                else []
            ),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out - check Azure CLI authentication and network connectivity",
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parsing error: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }
