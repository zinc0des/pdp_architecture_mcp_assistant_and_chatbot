#!/usr/bin/env python3
"""
Enhanced Repository Discovery for Multi-Repo Workspaces

This module provides intelligent repository discovery that works gracefully
with both single-repo and multi-repo VS Code workspaces.

Key Features:
- Context-aware repository detection
- Graceful handling of ambiguous scenarios
- No configuration required for basic usage
- Smart fallbacks and user guidance
"""

import os
import subprocess
import re
from typing import Dict, List, Optional, Any


def find_git_repositories(search_root: str) -> List[Dict[str, str]]:
    """
    Find all git repositories starting from search_root.

    Args:
        search_root: Directory to start searching from

    Returns:
        List of repository info dictionaries
    """
    repositories = []

    # Check if search_root itself is a git repo
    if os.path.exists(os.path.join(search_root, ".git")):
        repo_info = get_repository_info(search_root)
        if repo_info:
            repositories.append(repo_info)
        return repositories

    # Search subdirectories for git repositories
    try:
        for item in os.listdir(search_root):
            item_path = os.path.join(search_root, item)
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, ".git")
            ):
                repo_info = get_repository_info(item_path)
                if repo_info:
                    repositories.append(repo_info)
    except (OSError, PermissionError):
        # Handle cases where we can't read the directory
        pass

    return repositories


def get_repository_info(repo_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract repository information from a git repository.

    Args:
        repo_path: Path to the git repository

    Returns:
        Repository info dictionary or None if invalid
    """
    try:
        # Get remote origin URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_path,
        )

        if result.returncode != 0:
            return None

        remote_url = result.stdout.strip()

        # Parse Azure DevOps information
        org, project, repository = parse_azure_devops_url(remote_url)

        if not all([org, project, repository]):
            return None

        # Build API URLs based on the repository type
        if ".visualstudio.com" in remote_url:
            # Legacy Visual Studio URLs use different base paths
            api_base = (
                f"https://{org}.visualstudio.com/DefaultCollection/{project}/_apis"
            )
            modern_api_urls = {
                "rest_api_base": api_base,
                "repos_api": f"{api_base}/git/repositories/{repository}",
                "pull_requests_api": f"{api_base}/git/repositories/{repository}/pullrequests",
                "work_items_api": f"https://{org}.visualstudio.com/DefaultCollection/_apis/wit/workitems",
            }
        else:
            # Modern dev.azure.com URLs
            modern_api_urls = {
                "rest_api_base": f"https://dev.azure.com/{org}/{project}/_apis",
                "repos_api": f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository}",
                "pull_requests_api": f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository}/pullrequests",
                "work_items_api": f"https://dev.azure.com/{org}/_apis/wit/workitems",
            }

        # Determine repository type
        repo_type = "azure_devops"
        if "msazure" in org.lower():
            repo_type = "azure_devops_msazure"
        elif "microsoft" in org.lower():
            repo_type = "azure_devops_microsoft"

        # Workspace context - handle permission errors gracefully
        try:
            is_multi_repo_workspace = len(os.listdir(os.path.dirname(repo_path))) > 1
        except (OSError, PermissionError):
            # If we can't list parent directory, assume single-repo workspace
            is_multi_repo_workspace = False

        workspace_context = {
            "is_multi_repo_workspace": is_multi_repo_workspace,
            "workspace_root": os.path.dirname(repo_path),
            "repository_relative_path": os.path.basename(repo_path),
        }

        # Construct the correct org_url based on the original URL format
        if ".visualstudio.com" in remote_url:
            org_url = f"https://{org}.visualstudio.com"
        else:
            org_url = f"https://dev.azure.com/{org}"

        return {
            "path": repo_path,
            "name": repository,
            "organization": org,
            "project": project,
            "remote_url": remote_url,
            "org_url": org_url,
            "modern_api_urls": modern_api_urls,
            "repo_type": repo_type,
            "workspace_context": workspace_context,
        }

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return None


def parse_azure_devops_url(remote_url: str) -> tuple[str, str, str]:
    """
    Parse Azure DevOps URL to extract organization, project, and repository.

    Args:
        remote_url: Git remote URL

    Returns:
        Tuple of (organization, project, repository)
    """
    org, project, repository, _ = parse_azure_devops_pr_url(remote_url)
    return org, project, repository


def parse_azure_devops_pr_url(pr_url: str) -> tuple[str, str, str, str]:
    """
    Parse Azure DevOps PR URL to extract organization, project, repository, and PR ID.

    Supports both PR URLs and regular git repository URLs.

    Args:
        pr_url: Azure DevOps PR URL or git remote URL

    Returns:
        Tuple of (organization, project, repository, pr_id)
        pr_id will be empty string if not a PR URL
    """
    org = project = repository = pr_id = ""

    if "dev.azure.com" in pr_url:
        # New Azure DevOps URL format
        org_match = re.search(r"dev\.azure\.com/([^/]*)", pr_url)
        project_match = re.search(r"dev\.azure\.com/[^/]*/([^/]*)", pr_url)

        org = org_match.group(1) if org_match else ""
        project = project_match.group(1).replace("%20", " ") if project_match else ""

        # Check if this is a PR URL
        pr_match = re.search(r"/_git/([^/]*?)/pullrequest/(\d+)", pr_url)
        if pr_match:
            repository = pr_match.group(1)
            pr_id = pr_match.group(2)
        else:
            # Regular git repository URL
            repo_match = re.search(r"/_git/([^/]*?)(?:\.git)?$", pr_url)
            repository = repo_match.group(1) if repo_match else ""

        # Handle SSH remote formats (git@ssh.dev.azure.com:v3/<org>/<project>/<repo>)
        if not repository and "ssh.dev.azure.com" in pr_url:
            ssh_match = re.search(
                r"ssh\.dev\.azure\.com:v3/([^/]*)/([^/]*)/([^/]*)", pr_url
            )
            if ssh_match:
                org = ssh_match.group(1)
                project = ssh_match.group(2).replace("%20", " ")
                repository = ssh_match.group(3).replace(".git", "")

    elif ".visualstudio.com" in pr_url:
        # Azure DevOps visualstudio.com URL format (both legacy and modern)
        org_match = re.search(r"([^/]*?)\.visualstudio\.com", pr_url)
        org = org_match.group(1) if org_match else ""

        # Check for legacy format with DefaultCollection
        project_match = re.search(r"DefaultCollection/([^/]*)", pr_url)
        if project_match:
            # Legacy format: https://org.visualstudio.com/DefaultCollection/project/_git/repo
            project = project_match.group(1).replace("%20", " ")
        else:
            # Modern format: https://org.visualstudio.com/project/_git/repo
            # Extract project from URL after domain and before /_git/
            modern_match = re.search(r"\.visualstudio\.com/([^/]*?)/_git", pr_url)
            project = modern_match.group(1).replace("%20", " ") if modern_match else ""

        # Check if this is a PR URL
        pr_match = re.search(r"/_git/([^/]*?)/pullrequest/(\d+)", pr_url)
        if pr_match:
            repository = pr_match.group(1)
            pr_id = pr_match.group(2)
        else:
            # Regular git repository URL
            repo_match = re.search(r"/_git/([^/]*?)(?:\.git)?$", pr_url)
            repository = repo_match.group(1) if repo_match else ""

    return org, project, repository, pr_id


def infer_target_repository(
    repositories: List[Dict[str, str]], working_directory: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Intelligently infer which repository the user is targeting.

    Args:
        repositories: List of available repositories
        working_directory: Optional hint about working directory

    Returns:
        Best guess repository or None if ambiguous
    """
    if not repositories:
        return None

    if len(repositories) == 1:
        return repositories[0]

    # If working_directory is provided, prefer repos that match or contain it
    if working_directory:
        for repo in repositories:
            if working_directory.startswith(repo["path"]):
                return repo

    # Look for indicators of recent activity
    current_dir = os.getcwd()
    for repo in repositories:
        if current_dir.startswith(repo["path"]):
            return repo

    # If we can't determine, return None to indicate ambiguity
    return None


def enhanced_repository_discovery(
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enhanced repository discovery that handles both single and multi-repo workspaces.

    Args:
        working_directory: Optional path to search from

    Returns:
        Discovery result with success status and repository information
    """
    try:
        # Determine search starting point
        search_root = working_directory or os.getcwd()

        # Strategy 1: Check if we're already in a git repository
        current_repo = None
        check_dir = search_root
        while check_dir != os.path.dirname(check_dir):  # Walk up to filesystem root
            if os.path.exists(os.path.join(check_dir, ".git")):
                current_repo = get_repository_info(check_dir)
                if current_repo:
                    return {
                        "success": True,
                        "strategy": "current_directory",
                        "repository_path": current_repo["path"],
                        **current_repo,
                    }
                break
            check_dir = os.path.dirname(check_dir)

        # Strategy 2: Multi-repo workspace discovery
        repositories = find_git_repositories(search_root)

        if not repositories:
            return {
                "success": False,
                "error": "No git repositories found",
                "search_root": search_root,
                "suggestion": "Ensure you're in or near a git repository directory",
            }

        # Strategy 3: Intelligent repository selection
        target_repo = infer_target_repository(repositories, working_directory)

        if target_repo:
            return {
                "success": True,
                "strategy": "intelligent_inference",
                "repository_path": target_repo["path"],
                "available_repositories": len(repositories),
                **target_repo,
            }

        # Strategy 4: Ambiguous case - provide guidance
        return {
            "success": False,
            "error": "Multiple repositories found - please specify target",
            "available_repositories": [
                {
                    "name": repo["name"],
                    "path": repo["path"],
                    "organization": repo["organization"],
                    "project": repo["project"],
                }
                for repo in repositories
            ],
            "suggestion": "Either run from within a specific repository or use the working_directory parameter",
            "example_usage": f"working_directory='{repositories[0]['path']}'",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Repository discovery failed: {str(e)}",
            "search_root": working_directory or os.getcwd(),
        }


def azure_devops_repository_discovery_enhanced(
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enhanced Azure DevOps repository discovery with modern features.

    This version provides comprehensive repository context, multi-repo workspace support,
    modern API URLs, and intelligent error handling for improved collaboration.
    """
    result = enhanced_repository_discovery(working_directory)

    if result["success"]:
        # Return the full enhanced format with all modern features
        return {
            "success": True,
            "organization": result["organization"],
            "project": result["project"],
            "repository": result["name"],
            "org_url": result["org_url"],
            "remote_url": result["remote_url"],
            "cli_config_command": f'az devops configure --defaults organization={result["org_url"]} project="{result["project"]}"',
            # Enhanced fields for modern tooling
            "modern_api_urls": result["modern_api_urls"],
            "repo_type": result["repo_type"],
            "workspace_context": result["workspace_context"],
            "detection_strategy": result.get("strategy", "unknown"),
        }
    else:
        # Enhanced error reporting with comprehensive context
        return {
            "success": False,
            "error": result["error"],
            "available_repositories": result.get("available_repositories", []),
            "suggestion": result.get("suggestion", ""),
            "example_usage": result.get("example_usage", ""),
            "workspace_context": result.get("workspace_context", {}),
        }
