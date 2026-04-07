"""
BDD-style tests for get_payments_change_context tool based on domain knowledge audit.

Tests validate understanding of payment domain patterns, compliance requirements,
and architectural context extraction from repository sources.
"""

import pytest
from unittest.mock import Mock, patch

from pdp_dev_mcp.tools.code_review.change_context import (
    get_payments_change_context,
)


class TestPaymentsDomainContextBDD:
    """BDD tests for payments domain context extraction based on audit findings."""

    def setup_method(self):
        """Setup mock for repository context before each test."""
        self.repo_context_patcher = patch(
            "pdp_dev_mcp.tools.code_review.change_context.ensure_repository_context"
        )
        self.mock_ensure_context = self.repo_context_patcher.start()
        self.mock_ensure_context.return_value = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
        }

    def teardown_method(self):
        """Clean up patches after each test."""
        self.repo_context_patcher.stop()

    @pytest.fixture
    def mock_repository_context(self):
        """Mock repository context for testing."""
        context = Mock()
        context.working_directory = "/test/repo"
        context.organization = "test-org"
        context.project = "test-project"
        context.repository = "test-repo"
        return context

    @pytest.fixture
    def sample_payment_files(self):
        """Sample changed files representing different payment processing areas."""
        return [
            "src/databricks/workspace/notebooks/PaymentTransactions/Silver/ProcessPayments.py",
            "src/databricks/workspace/notebooks/NetworkTokenization/Gold/dimCard.py",
            "src/databricks/workspace/notebooks/Fraud/Silver/Silver_Load_PIMS_Events.py",
            "src/PowerBI/Payment Analytics Dataset.SemanticModel/model.bim",
        ]

    # Scenario 1: Provider Pattern Analysis
    def test_ai_agents_help_data_engineers_understand_provider_integration_patterns(
        self, mock_repository_context, sample_payment_files
    ):
        """
        As a data engineer
        When I ask an AI agent to review payment provider integration files
        Then the agent provides provider-specific patterns to ensure proper implementation
        """
        # Given: Payment provider integration files that need review
        changed_files = [
            "src/databricks/workspace/notebooks/NetworkTokenization/Gold/dimCard.py",
            "src/databricks/workspace/notebooks/PaymentTransactions/PaymentTransactions_TableNames.py",
        ]

        # When: Data engineer requests provider patterns context
        result = get_payments_change_context(
            changed_files, context_type="patterns", working_directory="/test/repo"
        )

        # Then: Receives provider patterns for integration validation
        assert result.success is True, (
            f"Context extraction should succeed for provider files: {changed_files}"
        )
        assert result.provider_patterns is not None, (
            "Provider patterns should be populated for payment provider files"
        )
        assert "visa" in result.provider_patterns.provider_types, (
            f"Expected 'visa' in provider types: {result.provider_patterns.provider_types}"
        )
        assert (
            "Bronze ingestion -> Silver processing -> Gold dimensions"
            in result.provider_patterns.integration_patterns
        ), (
            f"Expected standard integration pattern in: {result.provider_patterns.integration_patterns}"
        )

    # Scenario 2: Compliance Requirements Analysis
    def test_ai_agents_help_security_reviewers_identify_pci_requirements_for_sensitive_data(
        self, mock_repository_context, sample_payment_files
    ):
        """
        As a security reviewer
        When I ask an AI agent to analyze files handling sensitive payment data
        Then the agent identifies PCI DSS requirements to ensure compliance
        """
        # Arrange
        changed_files = [
            "src/databricks/workspace/notebooks/NetworkTokenization/Gold/dimCard.py",
            "src/databricks/workspace/notebooks/Fraud/Silver/Silver_Load_PIMS_Events.py",
        ]

        # Act
        result = get_payments_change_context(
            changed_files, context_type="compliance", working_directory="/test/repo"
        )

        # Assert - security reviewer can identify compliance requirements
        assert result.success is True, (
            "Expected successful compliance analysis for security review"
        )
        assert result.compliance_requirements is not None, (
            "Expected compliance requirements to be identified for sensitive payment data files"
        )

        expected_tokenization_req = "Card data tokenization required for storage"
        assert (
            expected_tokenization_req in result.compliance_requirements.pci_requirements
        ), (
            f"Expected tokenization requirement '{expected_tokenization_req}' in PCI requirements, "
            f"but found: {result.compliance_requirements.pci_requirements}"
        )

        expected_sensitivity_level = "Level 2: Payment instrument IDs, account IDs"
        assert (
            expected_sensitivity_level
            in result.compliance_requirements.data_sensitivity_levels
        ), (
            f"Expected sensitivity level '{expected_sensitivity_level}' for payment data, "
            f"but found: {result.compliance_requirements.data_sensitivity_levels}"
        )

    # Scenario 3: Architectural Context Analysis
    def test_ai_agents_help_solution_architects_understand_medallion_patterns_for_pipeline_changes(
        self, mock_repository_context, sample_payment_files
    ):
        """
        As a solution architect
        When I ask an AI agent to analyze data pipeline architecture changes
        Then the agent explains medallion patterns and design constraints
        """
        # Arrange
        changed_files = [
            "src/databricks/workspace/notebooks/PaymentTransactions/Bronze/Load_PaymentEvents.py",
            "src/databricks/workspace/notebooks/PaymentTransactions/Silver/ProcessPayments.py",
            "src/databricks/workspace/notebooks/PaymentTransactions/Gold/PublishToCorp.py",
        ]

        # Act
        result = get_payments_change_context(
            changed_files,
            context_type="architecture",
            working_directory="/test/repo",
        )

        # Assert - solution architect can understand architectural patterns
        assert result.success is True, (
            "Expected successful architectural analysis for solution architect"
        )
        assert result.architectural_context is not None, (
            "Expected architectural context to be provided for data pipeline changes"
        )

        medallion_arch = result.architectural_context.medallion_architecture
        assert "bronze_layer" in medallion_arch, (
            f"Expected 'bronze_layer' in medallion architecture explanation, but found: {medallion_arch}"
        )

        constraints = result.architectural_context.architectural_constraints
        assert isinstance(constraints, list), (
            f"Expected architectural constraints as list, but got: {type(constraints)}"
        )
        assert len(constraints) > 0, (
            f"Expected architectural constraints to be identified, but found empty list: {constraints}"
        )

    # Scenario 4: Historical Context Analysis
    def test_ai_agents_help_fraud_analysts_access_incident_patterns_for_risk_management(
        self, mock_repository_context, sample_payment_files
    ):
        """
        As a fraud analyst
        When I ask an AI agent to analyze fraud detection or risk management changes
        Then the agent provides historical incident patterns and lessons learned
        """
        # Arrange
        changed_files = [
            "src/databricks/workspace/notebooks/Fraud/Silver/Silver_Load_PIMS_Events.py",
            "src/databricks/workspace/notebooks/Fraud/Gold/Gold-Dim-PIMSEvents-Payment.py",
        ]

        # Act
        result = get_payments_change_context(
            changed_files, context_type="history", working_directory="/test/repo"
        )

        # Assert - fraud analyst can access historical context
        assert result.success is True, (
            "Expected successful historical analysis for fraud analyst"
        )
        assert result.historical_context is not None, (
            "Expected historical context to be provided for fraud detection changes"
        )

        incident_patterns = result.historical_context.incident_patterns
        assert isinstance(incident_patterns, list), (
            f"Expected incident patterns as list, but got: {type(incident_patterns)}"
        )

        lessons_learned = result.historical_context.lessons_learned
        assert isinstance(lessons_learned, list), (
            f"Expected lessons learned as list, but got: {type(lessons_learned)}"
        )

        assert len(incident_patterns) > 0, (
            f"Expected historical incident patterns to be identified, but found empty list: {incident_patterns}"
        )
        assert len(lessons_learned) > 0, (
            f"Expected lessons learned to be provided, but found empty list: {lessons_learned}"
        )

    # Scenario 5: Mixed Context Analysis
    def test_ai_agents_help_technical_leads_get_comprehensive_context_for_complex_payment_changes(
        self, mock_repository_context, sample_payment_files
    ):
        """
        As a technical lead
        When I ask an AI agent to analyze complex changes across payment processing areas
        Then the agent provides comprehensive domain context for informed decisions
        """
        # Arrange
        changed_files = sample_payment_files

        # Act
        result = get_payments_change_context(
            changed_files,
            context_type="comprehensive",
            working_directory="/test/repo",
        )

        # Assert - technical lead gets comprehensive context
        assert result.success is True, (
            "Expected successful comprehensive analysis for technical lead"
        )
        assert result.context_summary is not None, (
            "Expected context summary to be provided for comprehensive analysis"
        )

        # Comprehensive context should have all context types populated
        assert result.provider_patterns is not None, (
            "Expected provider patterns for comprehensive payment context"
        )
        assert result.compliance_requirements is not None, (
            "Expected compliance requirements for comprehensive payment context"
        )
        assert result.architectural_context is not None, (
            "Expected architectural context for comprehensive payment context"
        )
        assert result.historical_context is not None, (
            "Expected historical context for comprehensive payment context"
        )

        # Check that we have meaningful data for technical decisions
        provider_types = result.provider_patterns.provider_types
        assert len(provider_types) > 0, (
            f"Expected provider types to be identified, but found empty list: {provider_types}"
        )

        pci_requirements = result.compliance_requirements.pci_requirements
        assert len(pci_requirements) > 0, (
            f"Expected PCI requirements to be identified, but found empty list: {pci_requirements}"
        )

    # Scenario 6: Error Handling
    def test_ai_agents_help_code_reviewers_get_minimal_context_for_non_payment_files(
        self, mock_repository_context
    ):
        """
        As a code reviewer
        When I ask an AI agent to analyze files unrelated to payment processing
        Then the agent provides minimal context indicating no payment-specific concerns
        """
        # Arrange
        changed_files = [
            "README.md",
            "src/utilities/logging.py",
            "tests/unit/test_utils.py",
        ]

        # Act
        result = get_payments_change_context(
            changed_files, context_type="patterns", working_directory="/test/repo"
        )

        # Assert - code reviewer gets minimal context for non-payment files
        assert result.success is True, (
            "Expected successful analysis even for non-payment files"
        )
        assert result.domain_relevance == "low", (
            f"Expected low domain relevance for non-payment files, but got: {result.domain_relevance}"
        )
        assert result.provider_patterns is None, (
            f"Expected no provider patterns for non-payment files, but got: {result.provider_patterns}"
        )

        expected_summary_message = "No payment-specific domain knowledge"
        assert expected_summary_message in result.context_summary, (
            f"Expected context summary to indicate no payment knowledge with '{expected_summary_message}', "
            f"but got: {result.context_summary}"
        )

    # Scenario 7: Repository Context Integration
    def test_ai_agents_help_developers_use_repository_context_for_consistent_domain_analysis(
        self, mock_repository_context
    ):
        """
        As a developer
        When I ask an AI agent for payment domain context with repository information
        Then the agent provides analysis that integrates with existing repository discovery
        """
        # Arrange
        changed_files = [
            "src/databricks/workspace/notebooks/PaymentTransactions/Silver/ProcessPayments.py"
        ]

        # Act
        result = get_payments_change_context(
            changed_files, context_type="patterns", working_directory="/test/repo"
        )

        # Assert - developer gets integrated repository context
        assert result.success is True, (
            "Expected successful domain analysis with repository integration"
        )
        assert result.repository_info is not None, (
            "Expected repository information to be included in domain context"
        )

        # Repository discovery provides structured information for consistent analysis
        repo_info = result.repository_info
        assert hasattr(repo_info, "organization"), (
            f"Expected repository info to have organization attribute, but found: {dir(repo_info)}"
        )
        assert hasattr(repo_info, "project"), (
            f"Expected repository info to have project attribute, but found: {dir(repo_info)}"
        )
        assert hasattr(repo_info, "repository"), (
            f"Expected repository info to have repository attribute, but found: {dir(repo_info)}"
        )
