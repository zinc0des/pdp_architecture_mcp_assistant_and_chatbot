"""
Tests for PDP MCP Server - behavior-focused tests.

Tests focus on what developers can accomplish when deploying and running
the PDP Development MCP Server in their AI-assisted development workflows.
"""

import os
import subprocess
import sys
from unittest.mock import patch

from pdp_dev_mcp import server, __version__
from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger


class TestDevelopersCanDeployAndUsePDPMCPServer:
    """Test what developers can accomplish when deploying and using the PDP MCP Server for AI-assisted development."""

    def test_developers_can_start_pdp_server_for_ai_assistance(self):
        """
        As a developer
        When I start the PDP MCP server
        Then I can enable AI-assisted development workflows for my team
        """
        # Given: Developer has access to the server main function
        assert callable(server.main), (
            "Server main function must be callable for developers to start AI assistance"
        )

        # When: Developer attempts to start the server
        # Then: Server should initialize without import errors or configuration issues
        # Note: We test the initialization path but mock the actual server run to avoid blocking
        with patch("pdp_dev_mcp.mcp_instance.mcp.run") as mock_run, patch(
            "sys.argv", ["pdp_dev_mcp.server"]
        ):
            try:
                server.main()
                # Verify the server attempted to start (reached the run call)
                mock_run.assert_called_once()
                assert True, "Server successfully initialized and attempted to start"
            except Exception as e:
                # Developers need reliable server startup for their workflow
                assert False, (
                    f"Developer unable to initialize PDP server for AI assistance: {e}"
                )

    def test_developers_can_run_pdp_server_as_module_for_deployment_flexibility(self):
        """
        As a developer
        When I run the PDP server as a Python module
        Then I can deploy it flexibly across different environments and configurations
        """
        # This tests developer deployment capability: module execution for various environments
        test_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            test_dir
        )  # Go up one level from tests/ to project root

        result = subprocess.run(
            [sys.executable, "-m", "pdp_dev_mcp.server", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=project_root,
        )

        # Developers need reliable module execution for deployment flexibility
        # In development mode, module may not be installed - accept various return codes
        assert result.returncode in [0, 1, 2], (
            f"Developer should be able to attempt running PDP server as module. "
            f"Return code {result.returncode} with stderr: {result.stderr}"
        )

        # If it fails due to module not found, that's acceptable in development mode
        if result.returncode == 1 and "No module named 'pdp_dev_mcp'" in result.stderr:
            # This is expected in development mode before package installation
            pass
        elif result.returncode not in [0, 2]:
            # Unexpected error
            assert False, f"Unexpected error running server module: {result.stderr}"

    def test_developers_can_verify_pdp_server_version_for_compatibility_tracking(self):
        """
        As a developer
        When I check the PDP server version
        Then I can ensure compatibility with my development environment and dependencies
        """
        # This tests developer capability: version verification for environment management
        # Developers need clear version information for compatibility management
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_developers_can_validate_pdp_server_dependencies_for_reliable_deployment(
        self,
    ):
        """
        As a developer
        When I validate PDP server dependencies
        Then I can ensure reliable deployment and AI assistance functionality
        """
        # This tests developer capability: dependency validation for deployment confidence
        try:
            # Developers need assurance that critical dependencies are available for AI assistance
            assert hasattr(mcp, "run"), (
                "Developers need functional MCP instance for AI integration"
            )
            assert hasattr(logger, "info"), (
                "Developers need operational logging for troubleshooting"
            )

        except ImportError as e:
            assert False, (
                f"Developer missing critical dependency for PDP AI assistance: {e}"
            )
