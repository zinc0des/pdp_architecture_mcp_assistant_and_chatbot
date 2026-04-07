"""
Integration tests for PDP Development MCP Tools.

This package contains domain-specific integration tests that verify real-world
API interactions and cross-tool workflows that unit tests with mocks cannot validate.

Test Organization:
- data_quality_integration_test.py: AI agent workflows combining DQ tools
- azure_devops_integration_test.py: Azure DevOps API integration and workflow tools

Running Integration Tests:
- All integration tests: pytest tests/integration/ -m integration
- Specific domain: pytest tests/integration/azure_devops_integration_test.py -m integration
- Skip integration tests: pytest -m "not integration"

Requirements:
- Integration tests require live API access and authentication
- Tests are marked with @pytest.mark.integration
- Slow tests additionally marked with @pytest.mark.slow
"""
