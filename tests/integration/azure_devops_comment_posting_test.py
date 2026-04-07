"""
Azure DevOps Comment Posting Integration Tests

These tests exercise the actual Azure CLI commands against real Azure DevOps
to ensure our comment posting system works correctly in production.

Tests will:
1. Post test comments to PR 13844374
2. Verify the comments were posted successfully
3. Clean up test comments afterwards
"""

import json
import subprocess
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pytest

from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    CodeReviewComment,
    CommentType,
    CommentSeverity,
    post_ai_generated_comments,
)


@dataclass
class CommentTestConfig:
    """Test comment configuration"""

    comment_id: str
    title: str
    content: str
    severity: CommentSeverity = CommentSeverity.INFO
    comment_type: CommentType = CommentType.GENERAL
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    tags: Optional[List[str]] = None

    def to_code_review_comment(self) -> CodeReviewComment:
        """Convert to CodeReviewComment for testing"""
        return CodeReviewComment(
            comment_id=self.comment_id,
            comment_type=self.comment_type,
            severity=self.severity,
            title=self.title,
            content=self.content,
            file_path=self.file_path,
            line_number=self.line_number,
            tags=self.tags or [],
            reasoning="Integration test comment",
        )


@pytest.mark.integration
class TestAIAgentsCanPostCommentsToAzureDevOps:
    """Test that AI agents can post comments to Azure DevOps for code review assistance."""

    def __init__(self, org: str, project: str, repository: str, pr_id: int):
        self.org = org
        self.project = project
        self.repository = repository
        self.pr_id = pr_id
        self.test_comments: List[str] = []  # Track comment IDs for cleanup

    def test_ai_agents_can_verify_azure_cli_connection_for_reliable_operations(
        self,
    ) -> bool:
        """As an AI agent helping developers with Azure DevOps integration,
        When I test the Azure CLI connectivity,
        Then I should verify successful authentication and connection,
        So I can ensure reliable Azure DevOps operations for code review assistance."""
        try:
            result = subprocess.run(
                ["az", "account", "show"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_existing_comments(self) -> List[Dict[str, Any]]:
        """Get all existing comments on the PR"""
        try:
            result = subprocess.run(
                [
                    "az",
                    "rest",
                    "--method",
                    "GET",
                    "--uri",
                    f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repository}/pullRequests/{self.pr_id}/threads?api-version=6.0",
                    "--resource",
                    "499b84ac-1321-427f-aa17-267ca6975798",
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
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

    def post_test_comment(
        self, test_comment: CommentTestConfig
    ) -> tuple[bool, Optional[str], Optional[int]]:
        """Post a single test comment and return success, error, thread_id"""
        comment_data = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": f"🧪 **INTEGRATION TEST** - {test_comment.title}\n\n{test_comment.content}\n\n*Test ID: {test_comment.comment_id}*",
                    "commentType": 1,
                }
            ],
            "status": 1,
        }

        # Add file positioning for line comments
        if test_comment.file_path and test_comment.line_number:
            comment_data["threadContext"] = {
                "filePath": test_comment.file_path,
                "rightFileStart": {"line": test_comment.line_number, "offset": 1},
                "rightFileEnd": {"line": test_comment.line_number, "offset": 1},
            }

        try:
            result = subprocess.run(
                [
                    "az",
                    "rest",
                    "--method",
                    "POST",
                    "--uri",
                    f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repository}/pullRequests/{self.pr_id}/threads?api-version=6.0",
                    "--resource",
                    "499b84ac-1321-427f-aa17-267ca6975798",
                    "--body",
                    json.dumps(comment_data),
                    "--headers",
                    "Content-Type=application/json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                response = json.loads(result.stdout)
                thread_id = response.get("id")
                self.test_comments.append(str(thread_id))
                return True, None, thread_id
            else:
                return False, result.stderr, None

        except Exception as e:
            return False, str(e), None

    def resolve_comment_thread(self, thread_id: int) -> bool:
        """Resolve a comment thread"""
        try:
            # First, get the thread to understand its structure
            get_result = subprocess.run(
                [
                    "az",
                    "rest",
                    "--method",
                    "GET",
                    "--uri",
                    f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repository}/pullRequests/{self.pr_id}/threads/{thread_id}?api-version=6.0",
                    "--resource",
                    "499b84ac-1321-427f-aa17-267ca6975798",
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if get_result.returncode != 0:
                return False

            # Update thread status to resolved (4)
            update_data = {"status": 4}

            result = subprocess.run(
                [
                    "az",
                    "rest",
                    "--method",
                    "PATCH",
                    "--uri",
                    f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repository}/pullRequests/{self.pr_id}/threads/{thread_id}?api-version=6.0",
                    "--resource",
                    "499b84ac-1321-427f-aa17-267ca6975798",
                    "--body",
                    json.dumps(update_data),
                    "--headers",
                    "Content-Type=application/json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except Exception:
            return False

    def cleanup_test_comments(self) -> Dict[str, bool]:
        """Clean up all test comments by resolving them"""
        results = {}
        for thread_id in self.test_comments:
            success = self.resolve_comment_thread(int(thread_id))
            results[thread_id] = success
        return results

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test suite"""
        results = {
            "azure_cli_connected": False,
            "initial_comment_count": 0,
            "test_comments": [],
            "cleanup_results": {},
            "overall_success": False,
        }

        # Test 1: Azure CLI connection
        results["azure_cli_connected"] = (
            self.test_ai_agents_can_verify_azure_cli_connection_for_reliable_operations()
        )
        if not results["azure_cli_connected"]:
            return results

        # Test 2: Get baseline comment count
        initial_comments = self.get_existing_comments()
        results["initial_comment_count"] = len(initial_comments)

        # Test 3: Post various types of test comments
        test_cases = [
            CommentTestConfig(
                comment_id="integration_test_general",
                title="General Comment Test",
                content="Testing general PR comment posting via Azure REST API",
                tags=["integration-test", "general"],
            ),
            CommentTestConfig(
                comment_id="integration_test_performance",
                title="Performance Comment Test",
                content="Testing performance-related comment with suggestions:\n\n```python\n# Example optimization\nresult = await asyncio.gather(*tasks)\n```",
                severity=CommentSeverity.SUGGESTION,
                comment_type=CommentType.PERFORMANCE,
                tags=["integration-test", "performance"],
            ),
            CommentTestConfig(
                comment_id="integration_test_line_comment",
                title="Line-Specific Comment Test",
                content="Testing line-specific comment positioning on actual code",
                comment_type=CommentType.LINE_COMMENT,
                file_path="src/pdp-dev-mcp/src/pdp_dev_mcp/tools/code_review/code_quality_signals.py",
                line_number=1,
                tags=["integration-test", "line-comment"],
            ),
        ]

        # Post test comments
        for test_case in test_cases:
            success, error, thread_id = self.post_test_comment(test_case)
            results["test_comments"].append(
                {
                    "test_id": test_case.comment_id,
                    "success": success,
                    "error": error,
                    "thread_id": thread_id,
                }
            )

        # Wait a moment for comments to be available
        time.sleep(2)

        # Test 4: Verify comments were posted
        final_comments = self.get_existing_comments()
        posted_count = len([r for r in results["test_comments"] if r["success"]])
        expected_total = results["initial_comment_count"] + posted_count

        # Test 5: Clean up test comments
        results["cleanup_results"] = self.cleanup_test_comments()

        # Overall success assessment
        results["overall_success"] = (
            results["azure_cli_connected"]
            and posted_count > 0
            and len(final_comments) >= expected_total
        )

        return results

    def test_ai_agents_can_post_comments_for_comprehensive_code_review_integration(
        self,
        cleanup_integration_test_comments,
        test_pr_config,
    ):
        """As an AI agent helping developers with Azure DevOps code review,
        When I post AI-generated comments to a pull request,
        Then I should successfully create and manage test comments,
        So I can provide comprehensive code review assistance through Azure DevOps integration."""

        # Use the centralized test PR config
        tester = TestAIAgentsCanPostCommentsToAzureDevOps(
            org=test_pr_config["org"],
            project=test_pr_config["project"],
            repository=test_pr_config["repository"],
            pr_id=test_pr_config["pr_id"],
        )

        print("🧪 Starting Azure DevOps Comment Posting Integration Tests...")

        # Run comprehensive test
        results = tester.run_comprehensive_test()

        # Print detailed results
        print("\n📊 Integration Test Results:")
        print(f"  Azure CLI Connected: {results['azure_cli_connected']}")
        print(f"  Initial Comment Count: {results['initial_comment_count']}")
        print(
            f"  Test Comments Posted: {len([r for r in results['test_comments'] if r['success']])}/{len(results['test_comments'])}"
        )

        for test_result in results["test_comments"]:
            status = "✅" if test_result["success"] else "❌"
            print(
                f"    {status} {test_result['test_id']}: Thread {test_result.get('thread_id', 'N/A')}"
            )
            if test_result["error"]:
                print(f"      Error: {test_result['error'][:100]}...")

        print(
            f"  Cleanup Results: {len([r for r in results['cleanup_results'].values() if r])}/{len(results['cleanup_results'])} resolved"
        )
        print(f"  Overall Success: {results['overall_success']}")

        # Assertions for pytest
        assert results["azure_cli_connected"], "Azure CLI should be connected"
        assert len([r for r in results["test_comments"] if r["success"]]) > 0, (
            "At least one test comment should post successfully"
        )

        return results

    def test_ai_agents_can_use_mcp_tools_for_structured_comment_posting(
        self, cleanup_integration_test_comments, test_pr_config
    ):
        """As an AI agent helping developers with MCP-based code review,
        When I use MCP tools to post structured comments to Azure DevOps,
        Then I should successfully create formatted comments with proper metadata,
        So I can provide developers with structured feedback through the MCP framework."""

        print("\n🔧 Testing MCP Tool Comment Posting...")

        # Create test comments using our MCP tool
        test_comments = [
            CodeReviewComment(
                comment_id="mcp_tool_test_001",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="MCP Tool Integration Test",
                content="🔬 **MCP Tool Test**\n\nThis comment is posted via the MCP tool to verify the integration works correctly.\n\n**Test Objectives:**\n- Verify MCP tool can post comments\n- Test comment formatting and display\n- Validate Azure DevOps integration\n\n*This is an automated test comment that will be resolved.*",
                tags=["mcp-test", "integration"],
                reasoning="Testing MCP tool comment posting functionality",
            ),
            CodeReviewComment(
                comment_id="mcp_tool_test_002",
                comment_type=CommentType.SUGGESTION,
                severity=CommentSeverity.SUGGESTION,
                title="MCP Suggestion Test",
                content="💡 **Code Improvement Suggestion**\n\nTesting suggestion-type comments with code examples:\n\n```python\n# Example async optimization\nasync def process_files(files):\n    tasks = [process_file(f) for f in files]\n    return await asyncio.gather(*tasks)\n```\n\n**Benefits:**\n- Concurrent processing\n- Better performance\n- Cleaner code structure",
                tags=["mcp-test", "suggestion"],
                reasoning="Testing MCP tool suggestion-type comments",
            ),
        ]

        # Post comments using the MCP tool
        result = post_ai_generated_comments(
            org=test_pr_config["org"],
            project=test_pr_config["project"],
            repository=test_pr_config["repository"],
            pr_id=test_pr_config["pr_id"],
            comments=test_comments,
            dry_run=False,  # Actually post the comments
            batch_size=2,
        )

        print("📊 MCP Tool Test Results:")
        print(f"  Total Comments: {result.total_comments}")
        print(f"  Successful Posts: {result.successful_posts}")
        print(f"  Failed Posts: {result.failed_posts}")

        if result.failures:
            print("  Failures:")
            for failure in result.failures:
                print(f"    - {failure['comment_id']}: {failure['error'][:100]}...")

        # Clean up - resolve the test comments
        if result.successful_posts > 0:
            print("\n🧹 Cleaning up test comments...")
            tester = TestAIAgentsCanPostCommentsToAzureDevOps(
                org=test_pr_config["org"],
                project=test_pr_config["project"],
                repository=test_pr_config["repository"],
                pr_id=test_pr_config["pr_id"],
            )

            # Give a moment for comments to be available
            time.sleep(3)

            # Get recent comments and resolve test comments
            comments = tester.get_existing_comments()
            for comment in comments[
                -result.successful_posts :
            ]:  # Get the most recent comments
                thread_id = comment.get("id")
                if thread_id:
                    resolved = tester.resolve_comment_thread(thread_id)
                    print(f"  Resolved thread {thread_id}: {resolved}")

        # Assertions
        assert result.total_comments == len(test_comments), (
            "Should process all test comments"
        )
        assert result.successful_posts > 0, (
            "At least one comment should post successfully"
        )

        return result
