"""
Azure DevOps Pull Request Lifecycle Management Tools

This module provides tools for creating and managing the lifecycle of pull requests
in Azure DevOps.

Functions:
    - azure_devops_create_pull_request: Create a new PR with comprehensive options
"""

import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from pdp_dev_mcp.mcp_instance import mcp

from .azure_devops_common import create_analysis_folder
from .azure_devops_repository import azure_devops_repository_discovery_enhanced
from .repository_context import get_repository_context


@mcp.tool()
def azure_devops_create_pull_request(
    source_branch: str,
    target_branch: str = "main",
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_draft: bool = False,
    reviewers: Optional[List[str]] = None,
    work_items: Optional[List[str]] = None,
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new pull request in Azure DevOps with comprehensive options.

    Enables AI agents to automate PR creation as part of development workflows,
    supporting both draft and ready-for-review PRs with proper metadata.

    Args:
        source_branch: Branch to merge from (e.g., 'feature/my-feature')
        target_branch: Branch to merge into (default: 'main')
        title: PR title (auto-generated from commits if not provided)
        description: PR description (can include markdown formatting)
        is_draft: Create as draft PR (default: False)
        reviewers: List of reviewer usernames/emails
        work_items: List of Azure DevOps work item IDs to link
        working_directory: Optional repository directory

    Returns:
        PR creation results with URL, ID, and metadata
    """
    # Get repository context
    try:
        if working_directory:
            repo_info = azure_devops_repository_discovery_enhanced(working_directory)
        else:
            context = get_repository_context()
            if context and isinstance(context, dict) and context.get("success"):
                # Use stored repository info from context
                repo_info = {
                    "success": True,
                    "organization": context.get("organization"),
                    "project": context.get("project"),
                    "repository": context.get("repository"),
                }
            else:
                return {
                    "success": False,
                    "error": "No repository context set and working_directory not provided",
                    "suggestion": "Use set_repository_context() first or provide working_directory parameter",
                }

        if not repo_info["success"]:
            return repo_info

        organization = repo_info["organization"]
        project = repo_info["project"]
        repository = repo_info["repository"]

    except Exception as e:
        return {
            "success": False,
            "step": "repository_context",
            "error": f"Repository context error: {str(e)}",
            "suggestion": "Verify repository context and try again",
        }

    # Create analysis folder for operation logs
    analysis_folder = create_analysis_folder()

    # Initialize command for error handling
    cmd = []

    try:
        # Build the Azure CLI command
        cmd = [
            "az",
            "repos",
            "pr",
            "create",
            "--source-branch",
            source_branch,
            "--target-branch",
            target_branch,
            "--org",
            f"https://dev.azure.com/{organization}",
            "--project",
            project,
            "--repository",
            repository,
        ]

        # Add optional parameters
        if title:
            cmd.extend(["--title", title])

        if description:
            cmd.extend(["--description", description])

        if is_draft:
            cmd.append("--draft")

        if reviewers:
            cmd.extend(["--reviewers"] + reviewers)

        if work_items:
            cmd.extend(["--work-items"] + work_items)

        # Execute PR creation
        print(f"Creating PR: {source_branch} -> {target_branch}")
        if is_draft:
            print("Creating as DRAFT PR")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the result (Azure CLI returns JSON)
        try:
            pr_data = json.loads(result.stdout)
            pr_id = pr_data.get("pullRequestId")
            pr_url = pr_data.get("_links", {}).get("web", {}).get("href")

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            pr_id = "unknown"
            pr_url = f"https://dev.azure.com/{organization}/{project}/_git/{repository}/pullrequests"

        # Save operation results
        operation_data = {
            "operation": "create_pull_request",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "is_draft": is_draft,
            "pr_id": pr_id,
            "pr_url": pr_url,
            "organization": organization,
            "project": project,
            "repository": repository,
            "reviewers": reviewers,
            "work_items": work_items,
            "timestamp": datetime.now().isoformat(),
            "command_executed": " ".join(cmd),
            "raw_output": result.stdout,
        }

        results_file = os.path.join(
            analysis_folder, f"pr_create_{source_branch.replace('/', '_')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(operation_data, f, indent=2)

        return {
            "success": True,
            "pr_id": pr_id,
            "pr_url": pr_url,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title or "Auto-generated from commits",
            "is_draft": is_draft,
            "reviewers": reviewers or [],
            "work_items": work_items or [],
            "results_file": results_file,
            "message": f"Pull request created successfully: {source_branch} -> {target_branch}",
            "next_steps": [
                f"Review PR at: {pr_url}",
                "Add reviewers if not specified",
                "Link work items if needed",
                "Convert from draft if applicable",
            ],
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "step": "pr_creation",
            "error": f"Azure CLI error: {e.stderr}",
            "command": " ".join(cmd),
            "suggestion": "Check branch exists, Azure CLI authentication, and repository permissions",
        }
    except Exception as e:
        return {
            "success": False,
            "step": "pr_creation",
            "error": str(e),
            "command": " ".join(cmd),
            "suggestion": "Check Azure CLI installation and authentication",
        }
