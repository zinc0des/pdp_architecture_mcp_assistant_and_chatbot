"""
Repository context management for Azure DevOps MCP tools.

Provides session-level repository context with caching and explicit override capabilities.
Solves the problem of repeated repository discovery and inconsistent context across tools.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

from .enhanced_repository_discovery import azure_devops_repository_discovery_enhanced


def ensure_repository_context(
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ensure repository context is available, with intelligent fallbacks.

    This function provides a robust way for tools to get repository context
    without requiring strict tool execution order from AI agents.

    Args:
        working_directory: Optional explicit directory path

    Returns:
        Repository context dict with success status and helpful error messages

    Usage:
        ```python
        repo_context = ensure_repository_context(working_directory)
        if not repo_context["success"]:
            return {"error": repo_context["error"], "suggestion": repo_context.get("suggestion")}

        org = repo_context["organization"]
        project = repo_context["project"]
        repository = repo_context["repository"]
        ```
    """
    # First, try to get existing cached context
    if working_directory is None:
        cached_info = RepositoryContext.get_repository_info()
        if cached_info["success"]:
            return cached_info

    # If no cached context or explicit override, do fresh discovery
    repo_info = RepositoryContext.get_repository_info(working_directory)

    if repo_info["success"]:
        return repo_info

    # Enhanced error messages for AI agents
    error_context = {
        "success": False,
        "error": repo_info.get("error", "Repository context not available"),
        "suggestion": "Use mcp_pdp-dev-mcp_set_repository_context() MCP tool to set the repository path first",
        "ai_guidance": {
            "required_mcp_tool": "mcp_pdp-dev-mcp_set_repository_context",
            "example": "mcp_pdp-dev-mcp_set_repository_context(working_directory='/path/to/repository')",
            "common_paths": [
                "/Users/[username]/src/Microsoft/Commerce.PaymentsDataPlatform",
                "Current working directory if already in repository",
            ],
        },
        "troubleshooting": {
            "step_1": "Call mcp_pdp-dev-mcp_set_repository_context() MCP tool first",
            "step_2": "Ensure you're specifying a valid git repository path",
            "step_3": "Verify the directory contains a .git folder",
            "step_4": "Confirm repository is connected to Azure DevOps",
        },
    }

    # Add discovery details if available
    if "discovery_error" in repo_info:
        error_context["discovery_details"] = repo_info["discovery_error"]

    return error_context


class RepositoryContext:
    """
    Global repository context manager for MCP tools.

    Provides session-level repository context with:
    - Cached repository information for performance
    - Explicit context switching for multi-repo workspaces
    - Thread-safe operations for concurrent tool usage
    - Clear state management and debugging capabilities
    """

    _current_working_directory: Optional[str] = None
    _cached_repo_info: Optional[Dict[str, Any]] = None
    _cache_timestamp: Optional[str] = None
    _lock = Lock()

    @classmethod
    def set_working_directory(cls, working_directory: str) -> Dict[str, Any]:
        """
        Set the active repository context for subsequent tool operations.

        Args:
            working_directory: Absolute path to the repository directory

        Returns:
            Repository information dict with success status
        """
        with cls._lock:
            if not os.path.isabs(working_directory):
                return {
                    "success": False,
                    "error": f"Working directory must be absolute path, got: {working_directory}",
                }

            if not os.path.exists(working_directory):
                return {
                    "success": False,
                    "error": f"Working directory does not exist: {working_directory}",
                }

            # Clear cache when switching context
            cls._current_working_directory = working_directory
            cls._cached_repo_info = None
            cls._cache_timestamp = None

            # Immediately validate the new context
            repo_info = cls._discover_repository_info(working_directory)

            if repo_info["success"]:
                cls._cached_repo_info = repo_info
                cls._cache_timestamp = datetime.now().isoformat()

                return {
                    "success": True,
                    "message": f"Repository context set to: {working_directory}",
                    "repository_info": repo_info,
                    "context_timestamp": cls._cache_timestamp,
                }
            else:
                # Reset context on failure
                cls._current_working_directory = None
                return {
                    "success": False,
                    "error": f"Failed to discover repository information: {repo_info.get('error', 'Unknown error')}",
                    "attempted_directory": working_directory,
                }

    @classmethod
    def get_repository_info(
        cls, working_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get repository information using cached context or explicit override.

        Args:
            working_directory: Optional explicit directory to override global context

        Returns:
            Repository information dict with success status
        """
        with cls._lock:
            target_directory = working_directory or cls._current_working_directory

            # If no context set and no override provided, try intelligent discovery
            if target_directory is None:
                repo_info = cls._discover_repository_info(None)
                if repo_info["success"]:
                    return cls._add_context_metadata(repo_info, "intelligent_discovery")
                else:
                    return {
                        "success": False,
                        "error": "No repository context set and intelligent discovery failed. Use set_repository_context() first.",
                        "suggestion": "Call set_repository_context() with your repository path",
                        "discovery_error": repo_info.get("error", "Unknown error"),
                    }

            # Use cached info if available and no override provided
            if (
                working_directory is None
                and cls._cached_repo_info is not None
                and cls._cached_repo_info["success"]
            ):
                return cls._add_context_metadata(cls._cached_repo_info, "cached")

            # Discover fresh info for explicit override or cache miss
            repo_info = cls._discover_repository_info(target_directory)

            # Update cache if using global context (not override)
            if working_directory is None and repo_info["success"]:
                cls._cached_repo_info = repo_info
                cls._cache_timestamp = datetime.now().isoformat()

            return cls._add_context_metadata(repo_info, "fresh_discovery")

    @classmethod
    def get_context_status(cls) -> Dict[str, Any]:
        """
        Get current repository context status for debugging and visibility.

        Returns:
            Context status information including cached data and timestamps
        """
        with cls._lock:
            return {
                "context_set": cls._current_working_directory is not None,
                "current_working_directory": cls._current_working_directory,
                "cache_available": cls._cached_repo_info is not None,
                "cache_timestamp": cls._cache_timestamp,
                "cached_repository": (
                    cls._cached_repo_info.get("repository")
                    if cls._cached_repo_info
                    else None
                ),
                "cached_organization": (
                    cls._cached_repo_info.get("organization")
                    if cls._cached_repo_info
                    else None
                ),
            }

    @classmethod
    def clear_context(cls) -> Dict[str, Any]:
        """
        Clear the current repository context and cache.

        Returns:
            Status of the clear operation
        """
        with cls._lock:
            previous_directory = cls._current_working_directory
            previous_cache_available = cls._cached_repo_info is not None

            cls._current_working_directory = None
            cls._cached_repo_info = None
            cls._cache_timestamp = None

            return {
                "success": True,
                "message": "Repository context cleared",
                "previous_directory": previous_directory,
                "previous_cache_available": previous_cache_available,
                "cleared_at": datetime.now().isoformat(),
            }

    @classmethod
    def _discover_repository_info(
        cls, working_directory: Optional[str]
    ) -> Dict[str, Any]:
        """
        Internal method to discover repository information using enhanced discovery.

        Args:
            working_directory: Directory to discover repository info for

        Returns:
            Repository information from enhanced discovery
        """
        try:
            return azure_devops_repository_discovery_enhanced(working_directory)
        except Exception as e:
            return {
                "success": False,
                "error": f"Repository discovery exception: {str(e)}",
                "working_directory": working_directory,
            }

    @classmethod
    def _add_context_metadata(
        cls, repo_info: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """
        Add context management metadata to repository information.

        Args:
            repo_info: Original repository information
            source: How the information was obtained (cached, fresh_discovery, etc.)

        Returns:
            Repository information with added context metadata
        """
        if isinstance(repo_info, dict):
            repo_info["_context_source"] = source
            repo_info["_context_timestamp"] = datetime.now().isoformat()
            if cls._current_working_directory:
                repo_info["_context_working_directory"] = cls._current_working_directory

        return repo_info


def get_repository_context(working_directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get repository context.

    This is the primary interface that MCP tools should use for repository information.

    Args:
        working_directory: Optional explicit directory to override global context

    Returns:
        Repository information dict with success status
    """
    return RepositoryContext.get_repository_info(working_directory)


def set_repository_context(working_directory: str) -> Dict[str, Any]:
    """
    Convenience function to set repository context.

    This should be called by AI agents before using other repository-dependent tools.

    Args:
        working_directory: Absolute path to the repository directory

    Returns:
        Repository context setup result with success status
    """
    return RepositoryContext.set_working_directory(working_directory)


def get_context_status() -> Dict[str, Any]:
    """
    Convenience function to check current repository context status.

    Useful for debugging and understanding whether repository context is properly set.

    Returns:
        Context status information including cached data and timestamps
    """
    return RepositoryContext.get_context_status()


def clear_repository_context() -> Dict[str, Any]:
    """
    Convenience function to clear repository context.

    Useful for switching between different repositories or resetting state.

    Returns:
        Clear operation status
    """
    return RepositoryContext.clear_context()
