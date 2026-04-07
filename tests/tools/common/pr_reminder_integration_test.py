#!/usr/bin/env python3
"""Integration tests for PR reminder functionality using real repository data."""

import pytest

from pdp_dev_mcp.tools.common.azure_devops_pr_review import (
    azure_devops_send_pr_review_reminders,
)


class TestPRReminderIntegration:
    """
    Integration tests for PR reminder functionality.
    These tests use real repository data and verify actual behavior.
    """

    def test_ai_agents_help_developers_identify_their_prs_using_current_user_filter(
        self,
    ) -> None:
        """
        As a developer
        When I ask an AI agent to analyze my PRs that need review reminders
        Then the agent provides successful analysis scoped to my PRs only
        """
        # When: Developer runs reminder tool for their PRs only
        result = azure_devops_send_pr_review_reminders(
            max_days_old=7,
            current_user_only=True,
        )

        # Then: Developer gets successful PR analysis
        assert result["success"] is True, (
            "Developers need successful PR analysis to understand their review status"
        )

        # Then: Developer sees their PRs are properly scoped to their own work
        assert result["current_user_only"] is True, (
            "Developers should see confirmation that reminders are scoped to their own PRs"
        )

        # Then: Developer gets valid summary structure
        assert "summary" in result, "Developer should see summary of PR analysis"
        summary = result["summary"]

        assert "total_prs" in summary, "Summary should include total PR count"
        assert "prs_needing_reminders" in summary, (
            "Summary should include reminder count"
        )
        assert isinstance(summary["total_prs"], int), "Total PRs should be an integer"
        assert isinstance(summary["prs_needing_reminders"], int), (
            "Reminder count should be an integer"
        )

        # Then: Developer sees data structures for PR details
        assert "pending_prs" in result, "Developer should see pending PRs structure"
        assert isinstance(result["pending_prs"], list), "Pending PRs should be a list"

        # Then: Developer gets analysis file location for detailed review
        assert "analysis_file" in result, "Developer should see analysis file path"

    def test_ai_agents_help_developers_prepare_reminder_messages_in_dry_run_mode(
        self,
    ) -> None:
        """
        As a developer
        When I ask an AI agent to analyze PRs needing review
        Then the agent provides analysis for manual copying to Teams
        
        Note: This test was updated after dry_run was removed. The tool now
        always provides analysis output for manual Teams posting.
        """
        # When: Developer analyzes PRs
        result = azure_devops_send_pr_review_reminders(
            current_user_only=True,
        )

        # Then: Developer gets successful analysis
        assert result["success"] is True, (
            "Developers need successful analysis to understand reminder content"
        )

        # Then: Developer gets analysis summary
        assert "summary" in result, "Developer should see analysis summary"
        assert "prs_needing_reminders" in result["summary"], (
            "Summary should include PR count needing reminders"
        )
        assert isinstance(result["summary"]["prs_needing_reminders"], int), (
            "PR count should be an integer"
        )

        # Then: Developer sees PR details for manual posting
        assert "pending_prs" in result, "Developer should see pending PRs for manual review"
        assert isinstance(result["pending_prs"], list), "Pending PRs should be a list"

    def test_ai_agents_help_developers_understand_when_no_prs_need_reminders(
        self,
    ) -> None:
        """
        As a developer
        When I ask an AI agent about PRs needing reminders but have none
        Then the agent provides a successful response with clear status information
        """
        # When: Developer analyzes PRs (may find no PRs needing reminders)
        result = azure_devops_send_pr_review_reminders(
            current_user_only=True,
        )

        # Then: Developer gets successful response regardless of PR count
        assert result["success"] is True, (
            "Developers need successful response even when no PRs need reminders"
        )

        # Then: Developer gets clear status about their PR situation
        assert "summary" in result, "Developer should see summary of their PR status"
        assert "next_steps" in result, "Developer should see guidance for next steps"
        assert isinstance(result["next_steps"], list), (
            "Next steps should be a list of actions"
        )



    def test_ai_agents_help_developers_filter_prs_by_age_for_focused_reminders(
        self,
    ) -> None:
        """
        As a developer
        When I ask an AI agent to focus reminders on older PRs
        Then the agent filters by age to avoid reminder spam
        
        Note: This tool now provides PR analysis for manual Teams posting,
        since automatic Teams posting was removed due to auth constraints.
        """
        # When: Developer filters for older PRs only
        result = azure_devops_send_pr_review_reminders(
            max_days_old=3,  # Only PRs older than 3 days
            current_user_only=True,
        )

        # Then: Developer gets successful filtering response
        assert result["success"] is True, (
            "Developers need successful filtering to focus their reminder efforts"
        )

        # Then: Developer sees age filtering was applied
        assert "summary" in result, "Developer should see filtering summary"

        # Then: Developer gets actionable next steps
        assert "next_steps" in result, (
            "Developer should see guidance for follow-up actions"
        )
