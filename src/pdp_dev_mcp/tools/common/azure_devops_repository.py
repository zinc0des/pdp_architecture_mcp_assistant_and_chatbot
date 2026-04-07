"""
Azure DevOps Repository Discovery and Context Management Tools.

Provides tools for discovering repository information and managing
repository context in multi-repo workspaces.
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger
from .azure_devops_common import get_project_identifier
from .repository_context import RepositoryContext, get_repository_context
from .enhanced_repository_discovery import azure_devops_repository_discovery_enhanced


@mcp.tool()
def azure_devops_repository_discovery(
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Automatically discover Azure DevOps organization, project, and repository information
    from the current git repository. Works with both dev.azure.com and visualstudio.com URLs.

    Enhanced with multi-repo workspace support and intelligent repository inference.
    Works gracefully with both single-repo and multi-repo VS Code workspaces.

    Enables AI agents to help developers understand their repository context for Azure DevOps operations.

    Args:
        working_directory: Optional path to the git repository. If not provided, intelligently
                           discovers repositories starting from current directory and workspace root.

    Returns repository context needed for other Azure DevOps operations.
    """
    try:
        result = azure_devops_repository_discovery_enhanced(working_directory)

        # Add tool metadata for development and troubleshooting
        if isinstance(result, dict):
            result["_tool_version"] = "0.2.1"
            result["_execution_timestamp"] = datetime.now().isoformat()

        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Enhanced discovery error: {str(e)}",
            "_tool_version": "0.2.1",
            "_execution_timestamp": datetime.now().isoformat(),
        }


@mcp.tool()
def azure_devops_workflow_setup(
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete Azure DevOps workflow setup: discover repository, configure CLI, and list current PRs.
    Uses repository context management for consistent multi-repo workspace support.
    This is typically the first step in any Azure DevOps AI workflow.

    Enables AI agents to help developers quickly set up their environment for Azure DevOps AI-assisted development.

    Args:
        working_directory: Optional explicit repository directory (overrides global context)

    Returns comprehensive setup status and available PRs for further workflow operations.
    """
    try:
        # Step 1: Repository Context
        repo_info = get_repository_context(working_directory)
        if not repo_info["success"]:
            return {
                "success": False,
                "step": "repository_context",
                "error": repo_info["error"],
                "suggestion": "Use set_repository_context() to establish repository context first",
            }

        org = repo_info["organization"]
        project = repo_info["project"]
        repo = repo_info["repository"]
        org_url = repo_info["org_url"]

        # Step 2: Get project GUID to avoid URL encoding issues
        # Do NOT use az devops configure as it interferes with multi-project workflows
        project_identifier = get_project_identifier(project, org_url)
        logger.debug(f"Using project identifier: {project_identifier}")

        # Step 3: List current PRs using explicit parameters (no global defaults)
        logger.debug(
            f"Listing PRs with project: {project_identifier}, org: {org_url}, repo: {repo}"
        )
        # List active PRs using explicit parameters
        pr_result = subprocess.run(
            [
                "az",
                "repos",
                "pr",
                "list",
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
            timeout=60,
        )

        if pr_result.returncode != 0:
            return {
                "success": False,
                "step": "pr_listing",
                "error": f"Failed to list PRs: {pr_result.stderr}",
                "repository_info": repo_info,
            }

        # Parse PR list
        prs = json.loads(pr_result.stdout)

        # Get current branch for context
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        current_branch = (
            branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        )

        # Find PRs for current branch
        current_branch_prs = [
            pr for pr in prs if pr.get("sourceRefName", "").endswith(current_branch)
        ]

        # Format PR summaries
        pr_summaries = []
        for pr in prs[:10]:  # Limit to first 10 PRs
            pr_summaries.append(
                {
                    "id": pr.get("pullRequestId"),
                    "title": pr.get("title", "")[:80],
                    "status": pr.get("status"),
                    "created_by": pr.get("createdBy", {}).get("displayName", "Unknown"),
                    "source_branch": pr.get("sourceRefName", "").split("/")[-1],
                    "is_draft": pr.get("isDraft", False),
                }
            )

        return {
            "success": True,
            "setup_complete": True,
            "repository_context": {
                "organization": org,
                "project": project,
                "repository": repo,
                "org_url": repo_info["org_url"],
                "current_branch": current_branch,
            },
            "cli_configured": True,
            "pr_overview": {
                "total_prs": len(prs),
                "current_branch_prs": len(current_branch_prs),
                "recent_prs": pr_summaries,
            },
            "current_branch_pr_ids": [
                pr.get("pullRequestId") for pr in current_branch_prs
            ],
            "workflow_ready": True,
            "next_steps": [
                "Use azure_devops_pr_comment_analysis(pr_id) to analyze specific PR comments",
                "Use azure_devops_resolve_pr_comments(pr_id, thread_ids) to resolve AI feedback",
                "Review PR summaries above to identify target PR for AI workflow",
            ],
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "step": "json_parsing",
            "error": f"JSON parsing error: {str(e)}",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "step": "command_timeout",
            "error": "Command timed out - check authentication and network connectivity",
        }
    except Exception as e:
        return {
            "success": False,
            "step": "unexpected_error",
            "error": f"Unexpected error: {str(e)}",
        }


@mcp.tool()
def set_repository_context(working_directory: str) -> Dict[str, Any]:
    """
    Set the active repository context for Azure DevOps operations.

    This tool establishes the repository context for all subsequent Azure DevOps tools
    in this session, providing consistent repository information and avoiding repeated
    discovery operations.

    Args:
        working_directory: Absolute path to the repository directory to set as context

    Returns:
        Repository context information with success status and cached details
    """
    result = RepositoryContext.set_working_directory(working_directory)

    if result["success"]:
        return {
            "success": True,
            "message": "Repository context set successfully",
            "working_directory": working_directory,
            "repository": result["repository_info"].get("repository"),
            "organization": result["repository_info"].get("organization"),
            "project": result["repository_info"].get("project"),
            "context_timestamp": result.get("context_timestamp"),
            "discovery_method": result["repository_info"].get("discovery_method"),
            "note": "All Azure DevOps tools will now use this repository context by default",
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Failed to set repository context"),
            "working_directory": working_directory,
            "suggestion": "Ensure the path exists and contains a valid repository",
        }


@mcp.tool()
def get_repository_context_status() -> Dict[str, Any]:
    """
    Get the current repository context status and debugging information.

    This tool provides visibility into the current repository context state,
    including cached information and timestamps for debugging multi-repo operations.

    Returns:
        Repository context status with cache information and metadata
    """
    status = RepositoryContext.get_context_status()

    if status["context_set"]:
        current_info = get_repository_context()
        return {
            "success": True,
            "context_set": True,
            "current_working_directory": status["current_working_directory"],
            "repository": current_info.get("repository"),
            "organization": current_info.get("organization"),
            "project": current_info.get("project"),
            "cache_timestamp": status["cache_timestamp"],
            "cache_available": status["cache_available"],
            "context_source": current_info.get("_context_source"),
            "note": "Repository context is active - tools will use cached information",
        }
    else:
        return {
            "success": True,
            "context_set": False,
            "message": "No repository context set",
            "cache_available": status["cache_available"],
            "note": "Tools will attempt intelligent discovery or require explicit working_directory parameters",
        }


@mcp.tool()
def clear_repository_context() -> Dict[str, Any]:
    """
    Clear the current repository context and cache.

    This tool resets the repository context, forcing subsequent tools to perform
    fresh discovery or require explicit working_directory parameters.

    Returns:
        Status of the clear operation with previous context information
    """
    result = RepositoryContext.clear_context()

    return {
        "success": True,
        "message": "Repository context cleared successfully",
        "previous_directory": result.get("previous_directory"),
        "previous_cache_available": result.get("previous_cache_available"),
        "cleared_at": result.get("cleared_at"),
        "note": "Tools will now require explicit working_directory parameters or attempt intelligent discovery",
    }
