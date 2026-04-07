"""
Shared utilities and types for Azure DevOps tools.

Contains common helpers, dataclasses, and utility functions used across
Azure DevOps tool modules.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AzureDevOpsPRContext:
    """URL-based context for Azure DevOps PR operations.

    Established once from a PR URL, then reused across all PR-related tools
    to avoid repeated URL parsing and provide consistent context.
    """

    pr_url: str
    organization: str
    project: str
    repository: str
    pr_id: int
    source: str  # "url" or "local_context"

    @classmethod
    def from_pr_url(cls, pr_url: str) -> "AzureDevOpsPRContext":
        """Create context from Azure DevOps PR URL."""
        from .enhanced_repository_discovery import parse_azure_devops_pr_url
        
        try:
            org, project, repo, pr_id_str = parse_azure_devops_pr_url(pr_url)
            if not all([org, project, repo, pr_id_str]):
                raise ValueError(f"Unable to parse Azure DevOps PR URL: {pr_url}")

            pr_id = int(pr_id_str)
            return cls(
                pr_url=pr_url,
                organization=org,
                project=project,
                repository=repo,
                pr_id=pr_id,
                source="url",
            )
        except Exception as e:
            raise ValueError(f"Failed to parse PR URL {pr_url}: {str(e)}")

    @classmethod
    def from_local_context(
        cls, pr_id: int, working_directory: Optional[str] = None
    ) -> "AzureDevOpsPRContext":
        """Create context from local repository context."""
        from .repository_context import get_repository_context
        
        repo_info = get_repository_context(working_directory)
        if not repo_info["success"]:
            error_msg = repo_info.get("error", "Unknown repository context error")
            raise ValueError(f"Repository context failed: {error_msg}")

        # Build URL from context
        org = repo_info["organization"]
        project = repo_info["project"]
        repo = repo_info["repository"]
        pr_url = (
            f"https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{pr_id}"
        )

        return cls(
            pr_url=pr_url,
            organization=org,
            project=project,
            repository=repo,
            pr_id=pr_id,
            source="local_context",
        )


def create_analysis_folder() -> str:
    """
    Create the proper .copilot folder structure following team guidelines.
    Returns the path to the thread-specific folder.
    """
    today = datetime.now().strftime("%Y%m%d")
    folder_path = f".copilot/analysis/azure-devops-workflow-{today}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def parse_azure_devops_date(date_str: str) -> Optional[datetime]:
    """
    Parse Azure DevOps date string into datetime object.
    
    Handles various formats returned by Azure DevOps API:
    - ISO format with timezone
    - ISO format with milliseconds
    - ISO format without timezone
    
    Args:
        date_str: Date string from Azure DevOps API
        
    Returns:
        datetime object in local time, or None if parsing fails
    """
    if not date_str:
        return None
        
    try:
        # Handle both with and without microseconds
        if "." in date_str:
            date_clean = date_str.split(".")[0] + "Z"
        else:
            date_clean = date_str
            
        # Parse and convert to local timezone for consistent comparison
        parsed_date = datetime.fromisoformat(date_clean.replace("Z", "+00:00"))
        return parsed_date.astimezone().replace(tzinfo=None)
    except (ValueError, IndexError, TypeError):
        return None


def get_project_identifier(project: str, org_url: str, timeout: int = 10) -> str:
    """
    Get project GUID for Azure CLI operations, with fallback to project name.
    
    Azure DevOps project names with spaces need special handling. This helper
    attempts to resolve the project GUID but gracefully falls back to the 
    project name if the lookup fails.
    
    Args:
        project: Project name (may contain spaces)
        org_url: Azure DevOps organization URL
        timeout: Timeout in seconds for the lookup operation
        
    Returns:
        Project GUID if lookup succeeds, otherwise the original project name
    """
    import subprocess
    
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
            timeout=timeout,
        )

        if project_id_result.returncode == 0 and project_id_result.stdout.strip():
            return project_id_result.stdout.strip()
        else:
            # Fallback to project name if GUID lookup fails
            return project
    except subprocess.TimeoutExpired:
        # Fallback to project name if GUID lookup times out
        return project
    except Exception:
        # Fallback for any other exceptions
        return project


def discover_repository_context(working_directory: Optional[str] = None) -> Dict[str, Any]:
    """Helper function to discover repository context (wrapper for backwards compatibility)."""
    from .repository_context import get_repository_context
    return get_repository_context(working_directory)
