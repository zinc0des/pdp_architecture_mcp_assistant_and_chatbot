"""
Test cleanup utilities for Azure DevOps integration tests.

Provides mechanisms to clean up test comments before running integration tests
to prevent accumulation of test artifacts in PRs.
"""

import json
import subprocess
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Constants
AZURE_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass
class TestCommentCleanupConfig:
    """Configuration for test comment cleanup"""

    org: str
    project: str
    repository: str
    pr_id: int

    # Patterns to identify test comments
    test_comment_patterns: Optional[List[str]] = None
    dry_run: bool = False

    def __post_init__(self):
        """Initialize default test comment patterns if none provided.

        Sets up comprehensive patterns to identify integration test comments
        including emoji markers, test IDs, and content-based patterns.
        """
        if self.test_comment_patterns is None:
            self.test_comment_patterns = [
                "🧪 **INTEGRATION TEST**",
                "🔬 **MCP Tool Test**",
                "🧪 **TEST:",  # Catches "🧪 **TEST: Official Azure DevOps REST API Structure"
                "*Test ID:",
                "integration-test",
                "mcp-test",
                "*This is an automated test comment",
                "Testing suggestion-type comments",  # Catches "Testing suggestion-type comments with code examples"
                "comment in batch test",  # Catches both "First comment in batch test" and "Second comment in batch test"
                # Integration test patterns
                "Testing general PR comment",  # Catches "Testing general PR comment posting via Azure REST API"
                "Testing performance-related",  # Catches "Testing performance-related comment with suggestions"
                "Testing line-specific",  # Catches "Testing line-specific comment positioning on actual code"
                "integration_test_",  # Catches comment IDs like "integration_test_general", "integration_test_performance"
            ]


class TestCommentCleaner:
    """Utility class to clean up test comments from Azure DevOps PRs"""

    def __init__(self, config: TestCommentCleanupConfig):
        """Initialize the comment cleaner with configuration.

        Args:
            config: Configuration object containing Azure DevOps details
                    and cleanup parameters.
        """
        self.config = config

    def get_all_comments(self) -> List[Dict[str, Any]]:
        """Get all comments on the PR"""
        try:
            uri = (
                f"https://dev.azure.com/{self.config.org}/{self.config.project}"
                f"/_apis/git/repositories/{self.config.repository}"
                f"/pullRequests/{self.config.pr_id}/threads?api-version=6.0"
            )
            result = subprocess.run(
                [
                    "az",
                    "rest",
                    "--method",
                    "GET",
                    "--uri",
                    uri,
                    "--resource",
                    AZURE_RESOURCE_ID,
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )

            if result.returncode == 0:
                response = json.loads(result.stdout)
                return response.get("value", [])
            else:
                print(f"Error getting comments: {result.stderr}")
                return []

        except Exception as e:
            print(f"Exception getting comments: {e}")
            return []

    def is_test_comment(self, comment_thread: Dict[str, Any]) -> bool:
        """Check if a comment thread contains test content"""
        if not comment_thread.get("comments"):
            return False

        # Check all comments in the thread
        for comment in comment_thread["comments"]:
            content = comment.get("content")
            if not content:  # Skip None or empty content
                continue
            content = content.lower()

            # Ensure test_comment_patterns is a list
            patterns = self.config.test_comment_patterns or []
            # Check for test patterns
            for pattern in patterns:
                if pattern.lower() in content:
                    return True

        return False

    def _build_get_comments_command(self, thread_id: int) -> List[str]:
        """Build the Azure CLI command for getting thread comments."""
        uri = (
            f"https://dev.azure.com/{self.config.org}/{self.config.project}"
            f"/_apis/git/repositories/{self.config.repository}"
            f"/pullRequests/{self.config.pr_id}/threads/{thread_id}/comments"
            f"?api-version=7.1"
        )
        return [
            "az",
            "rest",
            "--method",
            "GET",
            "--uri",
            uri,
            "--resource",
            AZURE_RESOURCE_ID,
        ]

    def _build_delete_comment_command(
        self, thread_id: int, comment_id: int
    ) -> List[str]:
        """Build the Azure CLI command for deleting a comment."""
        uri = (
            f"https://dev.azure.com/{self.config.org}/{self.config.project}"
            f"/_apis/git/repositories/{self.config.repository}"
            f"/pullRequests/{self.config.pr_id}/threads/{thread_id}/comments/{comment_id}"
            f"?api-version=7.1"
        )
        return [
            "az",
            "rest",
            "--method",
            "DELETE",
            "--uri",
            uri,
            "--resource",
            AZURE_RESOURCE_ID,
        ]

    def _execute_command_with_timeout(
        self, cmd: List[str]
    ) -> subprocess.CompletedProcess:
        """Execute command with standard timeout and capture settings."""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

    def delete_comment_thread(self, thread_id: int) -> bool:
        """Delete all comments in a thread, effectively deleting the thread"""
        if self.config.dry_run:
            print(f"[DRY RUN] Would delete all comments in thread {thread_id}")
            return True

        try:
            # First get all comments in the thread
            get_cmd = self._build_get_comments_command(thread_id)
            get_result = self._execute_command_with_timeout(get_cmd)

            if get_result.returncode != 0:
                print(f"Failed to get comments for thread {thread_id}")
                return False

            thread_data = json.loads(get_result.stdout)
            comments = thread_data.get("value", [])

            if not comments:
                print(f"No comments found in thread {thread_id}")
                return True

            # Delete each comment in the thread
            deleted_count = 0
            for comment in comments:
                comment_id = comment.get("id")
                if not comment_id:
                    continue

                delete_cmd = self._build_delete_comment_command(thread_id, comment_id)
                delete_result = self._execute_command_with_timeout(delete_cmd)

                if delete_result.returncode == 0:
                    deleted_count += 1
                else:
                    print(
                        f"Failed to delete comment {comment_id} from thread {thread_id}"
                    )

            print(
                f"Deleted {deleted_count}/{len(comments)} comments from thread {thread_id}"
            )
            return deleted_count > 0

        except Exception as e:
            print(f"Error deleting thread {thread_id}: {e}")
            return False

    def _create_cleanup_results(
        self,
        success: bool,
        message: str,
        total_comments: int,
        test_comments_found: int,
        resolved_threads: List[int],
        failed_threads: List[int],
    ) -> Dict[str, Any]:
        """Build the cleanup results summary."""
        return {
            "success": success,
            "message": message,
            "total_comments": total_comments,
            "test_comments_found": test_comments_found,
            "resolved_count": len(resolved_threads),
            "failed_count": len(failed_threads),
            "resolved_threads": resolved_threads,
            "failed_threads": failed_threads,
        }

    def cleanup_test_comments(self) -> Dict[str, Any]:
        """Clean up all test comments from the PR"""
        print(f"🧹 Cleaning up test comments from PR {self.config.pr_id}...")

        # Get all comments
        all_comments = self.get_all_comments()
        if not all_comments:
            return self._create_cleanup_results(
                success=True,
                message="No comments found or unable to retrieve comments",
                total_comments=0,
                test_comments_found=0,
                resolved_threads=[],
                failed_threads=[],
            )

        # Find test comments
        test_comment_threads = []
        for comment_thread in all_comments:
            if self.is_test_comment(comment_thread):
                test_comment_threads.append(comment_thread)

        print(
            f"Found {len(test_comment_threads)} test comment threads out of {len(all_comments)} total"
        )

        if not test_comment_threads:
            return self._create_cleanup_results(
                success=True,
                message="No test comments found to clean up",
                total_comments=len(all_comments),
                test_comments_found=0,
                resolved_threads=[],
                failed_threads=[],
            )

        # Resolve test comments
        deleted_threads = []
        failed_threads = []

        for thread in test_comment_threads:
            thread_id = thread.get("id")
            if thread_id:
                success = self.delete_comment_thread(int(thread_id))
                if success:
                    deleted_threads.append(thread_id)
                    print(f"✅ Deleted test thread {thread_id}")
                else:
                    failed_threads.append(thread_id)
                    print(f"❌ Failed to delete test thread {thread_id}")

                # Small delay to avoid rate limiting
                time.sleep(0.5)

        cleanup_success = len(failed_threads) == 0
        message = f"Cleanup completed: {len(deleted_threads)} deleted, {len(failed_threads)} failed"

        result = self._create_cleanup_results(
            success=cleanup_success,
            message=message,
            total_comments=len(all_comments),
            test_comments_found=len(test_comment_threads),
            resolved_threads=deleted_threads,
            failed_threads=failed_threads,
        )

        if cleanup_success:
            print(f"🎉 Successfully cleaned up {len(deleted_threads)} test comments")
        else:
            print(f"⚠️ Cleanup completed with {len(failed_threads)} failures")

        return result


def cleanup_integration_test_comments(
    org: str,
    project: str,
    repository: str,
    pr_id: int,
    dry_run: bool = False,
    additional_patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to clean up integration test comments.

    Args:
        org: Azure DevOps organization
        project: Azure DevOps project
        repository: Repository name
        pr_id: Pull request ID
        dry_run: If True, only report what would be cleaned up
        additional_patterns: Additional patterns to identify test comments

    Returns:
        Dictionary with cleanup results
    """
    patterns = [
        "🧪 **INTEGRATION TEST**",
        "🔬 **MCP Tool Test**",
        "*Test ID:",
        "integration-test",
        "mcp-test",
        "*This is an automated test comment",
    ]

    if additional_patterns:
        patterns.extend(additional_patterns)

    config = TestCommentCleanupConfig(
        org=org,
        project=project,
        repository=repository,
        pr_id=pr_id,
        test_comment_patterns=patterns,
        dry_run=dry_run,
    )

    cleaner = TestCommentCleaner(config)
    return cleaner.cleanup_test_comments()
