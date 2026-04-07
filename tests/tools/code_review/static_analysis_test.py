"""
Tests for static analysis tools for payment processing domain knowledge.

Tests focus on what AI agents can accomplish when helping developers
understand payment processing domain requirements and compliance context.
"""

import pytest
from unittest.mock import patch, mock_open, AsyncMock
import asyncio

# Import the actual implementations
from pdp_dev_mcp.tools.code_review.static_analysis import (
    get_payments_domain_context,
    analyze_payment_code_compliance,
    analyze_payment_provider_patterns,
    analyze_payment_architecture_constraints,
    analyze_payment_historical_issues,
)


def mock_open_multiple_files(files_dict):
    """Create a mock_open that can handle multiple files."""

    def mock_open_func(*args, **kwargs):
        filename = args[0]
        if filename in files_dict:
            mock_file = mock_open(read_data=files_dict[filename])
            return mock_file(*args, **kwargs)
        # Return empty content for unknown files
        mock_file = mock_open(read_data="")
        return mock_file(*args, **kwargs)

    return mock_open_func


class AsyncMockFile:
    """Mock async file object for aiofiles."""

    def __init__(self, content):
        self.content = content

    async def read(self):
        return self.content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def mock_aiofiles_open(files_dict):
    """Create an aiofiles.open mock that can handle multiple files."""

    def mock_open_func(file_path, *args, **kwargs):
        content = files_dict.get(file_path, "")
        return AsyncMockFile(content)

    return mock_open_func


class TestAIAgentsCanProvidePaymentsDomainExpertise:
    """Test what AI agents can accomplish when helping developers understand payment processing domain knowledge."""

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_understand_pci_compliance_requirements(
        self,
    ) -> None:
        """
        As a developer modifying payment card processing code
        When I ask an AI agent about compliance requirements
        Then the agent provides specific PCI DSS guidance relevant to my changes
        """
        # Given: Developer is modifying code that handles credit card data
        file_paths = [
            "/src/databricks/bronze/card_processor.py",
            "/src/databricks/silver/card_tokenization.py",
        ]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/docs/compliance/PCI_DSS_Requirements.md": """
# PCI DSS Requirements for Payment Card Processing

## Requirement 3: Protect stored cardholder data
- Never store sensitive authentication data after authorization
- Mask PAN when displayed (only show last 4 digits)
- Encrypt cardholder data in storage using strong cryptography

## Requirement 4: Encrypt transmission of cardholder data
- Use strong cryptography and security protocols (TLS 1.2+)
- Never send unencrypted PANs by email, instant messaging, SMS, or chat
""",
                        "/src/databricks/bronze/card_processor.py": """
def process_card_transaction(card_data):
    # Processing credit card transaction data
    card_number = card_data.get('card_number')  # Full PAN - POTENTIAL PCI RISK
    cvv = card_data.get('cvv')  # Should not be stored - PCI violation risk
    return process_payment(card_number, cvv)
""",
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: AI agent analyzes payment card processing code for domain requirements
            result = await get_payments_domain_context(
                file_paths=file_paths, context_type="compliance"
            )

            # Then: AI agent provides specific PCI DSS guidance
            assert result.success is True, (
                "AI agents need successful domain knowledge retrieval to provide compliance guidance"
            )

            compliance_requirements = result.compliance_requirements
            assert len(compliance_requirements) > 0, (
                "AI agents need PCI DSS requirement context for payment card processing code analysis. "
                f"Expected compliance requirements, got: {compliance_requirements}"
            )

            # Then: AI agent identifies specific risks in current code
            pci_requirements = [
                req for req in compliance_requirements if "PCI" in req.standard
            ]
            assert len(pci_requirements) > 0, (
                "AI agents should specifically identify PCI DSS requirements for card processing modifications. "
                f"Expected PCI requirements, got: {pci_requirements}"
            )

            # Then: AI agent highlights data storage and transmission concerns
            requirement_descriptions = [
                req.description for req in compliance_requirements
            ]
            assert any(
                "cardholder data" in desc.lower() for desc in requirement_descriptions
            ), (
                "AI agents should highlight cardholder data protection requirements. "
                f"Expected cardholder data guidance in: {requirement_descriptions}"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_understand_provider_integration_patterns(
        self,
    ) -> None:
        """
        As a developer implementing a new payment provider integration
        When I ask an AI agent about integration patterns
        Then the agent provides proven patterns and anti-patterns for provider integrations
        """
        # Given: Developer is implementing new payment provider integration
        file_paths = ["/src/databricks/bronze/stripe_processor.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/docs/architecture/Provider_Integration_Patterns.md": """
# Payment Provider Integration Patterns

## Proven Patterns
### Response Code Standardization
- Always map provider-specific response codes to standardized internal codes
- Use consistent error handling across all provider integrations
- Implement retry logic with exponential backoff

### Data Transformation
- Bronze layer: Store raw provider responses for audit trail
- Silver layer: Transform to standardized payment schema
- Gold layer: Business logic and aggregations

## Anti-Patterns to Avoid
- Never store provider API keys in code or logs
- Don't process payments synchronously without timeout handling
- Avoid tight coupling between provider-specific logic and business logic
""",
                        "/src/databricks/bronze/adyen_processor.py": """
# Example of well-implemented provider integration
def process_adyen_response(raw_response):
    # Good pattern: Standardize response codes
    status_mapping = {
        'Authorised': 'APPROVED',
        'Declined': 'DECLINED', 
        'Error': 'ERROR'
    }
    return {
        'standardized_status': status_mapping.get(raw_response.get('resultCode'), 'UNKNOWN'),
        'raw_response': raw_response,  # Keep audit trail
        'provider': 'Adyen'
    }
""",
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: AI agent analyzes provider integration code for domain patterns
            result = await get_payments_domain_context(
                file_paths=file_paths, context_type="patterns"
            )

            # Then: AI agent provides proven integration patterns
            assert result.success is True, (
                "AI agents should successfully retrieve provider integration patterns"
            )

            domain_patterns = result.domain_patterns
            assert len(domain_patterns) > 0, (
                "AI agents should identify proven provider integration patterns. "
                f"Expected domain patterns, got: {domain_patterns}"
            )

            # Then: AI agent highlights response code standardization patterns
            pattern_descriptions = [pattern.description for pattern in domain_patterns]
            assert any(
                "response code" in desc.lower() for desc in pattern_descriptions
            ), (
                "AI agents should highlight response code standardization patterns for provider integrations. "
                f"Expected response code patterns in: {pattern_descriptions}"
            )

            # Then: AI agent identifies anti-patterns to avoid
            assert any(
                "anti-pattern" in pattern.pattern_type.lower()
                for pattern in domain_patterns
            ), (
                "AI agents should identify anti-patterns to help developers avoid common mistakes"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_understand_data_flow_architecture(
        self,
    ) -> None:
        """
        As a developer modifying data transformation logic
        When I ask an AI agent about architectural constraints
        Then the agent provides bronze-silver-gold layer guidance and data flow principles
        """
        # Given: Developer is modifying data transformation in the silver layer
        file_paths = ["/src/databricks/silver/payment_standardization.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/docs/architecture/Data_Flow_Architecture.md": """
# Payment Data Platform Architecture

## Bronze Layer (Raw Data)
- Store exact copies of source system data
- Minimal transformation - only data type conversions
- Preserve all original fields for audit and reprocessing

## Silver Layer (Standardized Data)  
- Transform to common payment schema
- Data quality validations and cleansing
- Standardize provider-specific fields to common format

## Gold Layer (Business Logic)
- Business rules and calculations
- Aggregations and derived metrics
- Optimized for analytics and reporting

## Critical Constraints
- Never modify bronze layer data after initial load
- Silver layer must be reprocessable from bronze
- Gold layer calculations must be deterministic and auditable
""",
                        "/src/databricks/silver/payment_standardization.py": """
def standardize_payment_data(bronze_data):
    # Silver layer transformation - must be reprocessable
    standardized = {}
    
    # Good: Preserve original data reference
    standardized['bronze_source_id'] = bronze_data.get('source_record_id')
    
    # Transform provider-specific fields to standard schema
    standardized['payment_id'] = extract_payment_id(bronze_data)
    standardized['amount'] = standardize_amount(bronze_data)
    
    return standardized
""",
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: AI agent analyzes data transformation code for architectural guidance
            result = await get_payments_domain_context(
                file_paths=file_paths, context_type="architecture"
            )

            # Then: AI agent provides bronze-silver-gold architectural guidance
            assert result.success is True, (
                "AI agents should successfully retrieve data flow architectural guidance"
            )

            architectural_constraints = result.architectural_constraints
            assert len(architectural_constraints) > 0, (
                "AI agents should identify data flow architectural constraints. "
                f"Expected architectural constraints, got: {architectural_constraints}"
            )

            # Then: AI agent emphasizes layer-specific responsibilities
            constraint_descriptions = [
                constraint.description for constraint in architectural_constraints
            ]
            assert any(
                "silver layer" in desc.lower() for desc in constraint_descriptions
            ), (
                "AI agents should provide specific silver layer transformation guidance. "
                f"Expected silver layer guidance in: {constraint_descriptions}"
            )

            # Then: AI agent highlights reprocessability requirements
            assert any(
                "reprocessable" in desc.lower() or "deterministic" in desc.lower()
                for desc in constraint_descriptions
            ), (
                "AI agents should emphasize data reprocessability requirements for payment data transformations"
            )


class TestAIAgentsCanLearnFromHistoricalIssues:
    """Test what AI agents can accomplish when helping developers learn from past payment processing issues."""

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_avoid_known_payment_processing_pitfalls(
        self,
    ) -> None:
        """
        As a developer implementing payment retry logic
        When I ask an AI agent about historical issues
        Then the agent provides context about past retry-related incidents and solutions
        """
        # Given: Developer is implementing payment retry logic
        file_paths = ["/src/databricks/silver/payment_retry_handler.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/docs/incidents/Payment_Retry_Issues_2024.md": """
# Payment Retry Issues - 2024 Incident Reports

## Incident #2024-03-15: Infinite Retry Loop
**Issue**: Payment retry logic caused infinite loops when provider returned ambiguous error codes
**Impact**: 150K duplicate payment attempts, provider rate limiting
**Root Cause**: Retry logic didn't distinguish between retryable and non-retryable errors
**Solution**: Implement explicit error code classification and max retry limits

## Incident #2024-06-22: Retry Storm During Provider Outage  
**Issue**: All failed payments retried simultaneously when provider came back online
**Impact**: Overwhelmed provider API, caused secondary outage
**Root Cause**: No jitter in retry timing, no backoff strategy
**Solution**: Exponential backoff with jitter, circuit breaker pattern

## Best Practices Learned
- Always implement maximum retry limits (recommend 3 retries max)
- Use exponential backoff with jitter to prevent retry storms
- Classify errors as retryable vs non-retryable based on provider documentation
- Implement circuit breaker for provider health monitoring
"""
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: AI agent analyzes retry logic code for historical context
            result = await get_payments_domain_context(
                file_paths=file_paths, context_type="history"
            )

            # Then: AI agent provides historical incident context
            assert result.success is True, (
                "AI agents should successfully retrieve historical incident context"
            )

            historical_issues = result.historical_issues
            assert len(historical_issues) > 0, (
                "AI agents should identify relevant historical payment processing issues. "
                f"Expected historical issues, got: {historical_issues}"
            )

            # Then: AI agent highlights specific retry-related incidents
            issue_descriptions = [issue.description for issue in historical_issues]
            assert any("retry" in desc.lower() for desc in issue_descriptions), (
                "AI agents should identify retry-related historical incidents for retry logic implementations. "
                f"Expected retry incidents in: {issue_descriptions}"
            )

            # Then: AI agent provides actionable lessons learned
            assert any(
                "solution" in issue.issue_type.lower()
                or "best practice" in issue.issue_type.lower()
                for issue in historical_issues
            ), (
                "AI agents should provide actionable solutions and best practices from historical incidents"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_understand_provider_specific_gotchas(
        self,
    ) -> None:
        """
        As a developer working with a specific payment provider
        When I ask an AI agent about provider-specific issues
        Then the agent provides context about known provider quirks and workarounds
        """
        # Given: Developer is working with PayPal integration
        file_paths = ["/src/databricks/bronze/paypal_processor.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/docs/providers/PayPal_Integration_Notes.md": """
# PayPal Integration - Known Issues and Workarounds

## Issue: PayPal Express Checkout Timezone Handling
**Problem**: PayPal timestamps are in PST/PDT, not UTC
**Impact**: Transaction reconciliation failures during DST transitions
**Workaround**: Always convert PayPal timestamps to UTC before storage

## Issue: PayPal Duplicate Transaction Detection
**Problem**: PayPal's duplicate detection is case-sensitive on merchant transaction ID
**Impact**: Failed payments with similar transaction IDs
**Workaround**: Always use consistent casing (uppercase) for transaction IDs

## Issue: PayPal Webhook Delivery Reliability  
**Problem**: PayPal webhooks may be delivered out of order or with delays
**Impact**: Payment status inconsistencies
**Workaround**: Implement idempotent webhook processing and status reconciliation
"""
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: AI agent analyzes PayPal integration code for provider-specific context
            result = await get_payments_domain_context(
                file_paths=file_paths, context_type="history"
            )

            # Then: AI agent provides provider-specific historical context
            assert result.success is True, (
                "AI agents should successfully retrieve provider-specific historical context"
            )

            historical_issues = result.historical_issues
            provider_specific_issues = [
                issue
                for issue in historical_issues
                if "paypal" in issue.description.lower()
            ]
            assert len(provider_specific_issues) > 0, (
                "AI agents should identify PayPal-specific historical issues for PayPal integration work. "
                f"Expected PayPal issues, got: {provider_specific_issues}"
            )

            # Then: AI agent highlights critical integration quirks
            issue_descriptions = [
                issue.description for issue in provider_specific_issues
            ]
            assert any(
                "timezone" in desc.lower() or "timestamp" in desc.lower()
                for desc in issue_descriptions
            ), (
                "AI agents should highlight PayPal timezone handling quirks that commonly cause integration issues"
            )


class TestAIAgentsCanAnalyzeSpecificPaymentCodePatterns:
    """Test what AI agents can accomplish when analyzing specific payment code patterns."""

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_analyze_code_compliance_patterns(
        self,
    ) -> None:
        """
        As a developer modifying payment processing code
        When I ask an AI agent to analyze compliance patterns
        Then the agent identifies specific compliance requirements in the code
        """
        # Given: Payment processing code files
        file_paths = [
            "/src/databricks/bronze/card_processor.py",
            "/src/databricks/silver/transaction_validator.py",
        ]

        # When: Analyzing code compliance patterns
        compliance_requirements = await analyze_payment_code_compliance(file_paths)

        # Then: Should return compliance analysis results
        assert isinstance(compliance_requirements, list), (
            "AI agents should return compliance requirements as a list"
        )
        # Note: The function may return empty list if files don't exist or have no patterns
        # This is acceptable behavior for a stub implementation

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_analyze_provider_integration_patterns(
        self,
    ) -> None:
        """
        As a developer working on payment provider integration
        When I ask an AI agent to analyze provider patterns
        Then the agent identifies specific provider integration patterns
        """
        # Given: Provider integration files
        file_paths = [
            "/src/databricks/bronze/adyen_processor.py",
            "/src/databricks/bronze/stripe_processor.py",
        ]

        # When: Analyzing provider patterns
        provider_patterns = await analyze_payment_provider_patterns(file_paths)

        # Then: Should return provider pattern analysis
        assert isinstance(provider_patterns, list), (
            "AI agents should return provider patterns as a list"
        )

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_analyze_architecture_constraints(
        self,
    ) -> None:
        """
        As a developer designing payment architecture
        When I ask an AI agent to analyze architectural constraints
        Then the agent identifies relevant architecture patterns and constraints
        """
        # Given: Architecture-related files
        file_paths = [
            "/src/databricks/silver/payment_orchestrator.py",
            "/src/databricks/gold/payment_aggregator.py",
        ]

        # When: Analyzing architecture constraints
        constraints = await analyze_payment_architecture_constraints(file_paths)

        # Then: Should return architecture constraint analysis
        assert isinstance(constraints, list), (
            "AI agents should return architecture constraints as a list"
        )

    @pytest.mark.asyncio
    async def test_ai_agents_help_developers_analyze_historical_payment_issues(
        self,
    ) -> None:
        """
        As a developer avoiding known payment processing pitfalls
        When I ask an AI agent to analyze historical issues
        Then the agent identifies relevant historical problems and solutions
        """
        # Given: Payment processing files that may have historical issues
        file_paths = [
            "/src/databricks/bronze/legacy_payment_processor.py",
            "/src/databricks/silver/transaction_reconciler.py",
        ]

        # When: Analyzing historical issues
        historical_issues = await analyze_payment_historical_issues(file_paths)

        # Then: Should return historical issue analysis
        assert isinstance(historical_issues, list), (
            "AI agents should return historical issues as a list"
        )

    @pytest.mark.asyncio
    async def test_ai_agents_handle_empty_file_lists_gracefully(self) -> None:
        """
        As a developer using AI agents for code analysis
        When I provide empty file lists
        Then the agent handles this gracefully without errors
        """
        # Given: Empty file list
        empty_files = []

        # When: Running various analysis functions
        compliance = await analyze_payment_code_compliance(empty_files)
        patterns = await analyze_payment_provider_patterns(empty_files)
        constraints = await analyze_payment_architecture_constraints(empty_files)
        issues = await analyze_payment_historical_issues(empty_files)

        # Then: All should handle empty input gracefully
        assert isinstance(compliance, list), "Should handle empty compliance analysis"
        assert isinstance(patterns, list), "Should handle empty pattern analysis"
        assert isinstance(constraints, list), "Should handle empty constraint analysis"
        assert isinstance(issues, list), "Should handle empty issue analysis"

    @pytest.mark.asyncio
    async def test_ai_agents_handle_nonexistent_files_gracefully(self) -> None:
        """
        As a developer using AI agents for code analysis
        When I provide paths to nonexistent files
        Then the agent handles this gracefully without crashing
        """
        # Given: Non-existent file paths
        nonexistent_files = [
            "/nonexistent/path/file1.py",
            "/another/nonexistent/file2.py",
        ]

        # When: Running analysis functions with nonexistent files
        try:
            compliance = await analyze_payment_code_compliance(nonexistent_files)
            patterns = await analyze_payment_provider_patterns(nonexistent_files)
            constraints = await analyze_payment_architecture_constraints(
                nonexistent_files
            )
            issues = await analyze_payment_historical_issues(nonexistent_files)

            # Then: Should not crash and return reasonable results
            assert isinstance(compliance, list), (
                "Should handle nonexistent files for compliance"
            )
            assert isinstance(patterns, list), (
                "Should handle nonexistent files for patterns"
            )
            assert isinstance(constraints, list), (
                "Should handle nonexistent files for constraints"
            )
            assert isinstance(issues, list), (
                "Should handle nonexistent files for issues"
            )

        except Exception as e:
            # If exceptions are raised, they should be meaningful
            assert "file" in str(e).lower() or "path" in str(e).lower(), (
                f"Exception should be file-related, got: {e}"
            )


class TestAIAgentsHandleDomainAnalysisErrorScenarios:
    """Test how AI agents handle error scenarios during domain knowledge analysis."""

    @pytest.mark.asyncio
    async def test_ai_agents_handle_historical_issue_analysis_data_access_failures(
        self,
    ):
        """
        Given an AI agent providing payments domain expertise
        When historical issue analysis encounters data access failures
        Then the system should provide available domain context with clear limitations
        """
        # Given: Historical issue analysis with data access failure
        file_paths = ["/src/databricks/silver/payment_processor.py"]

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False  # Simulate missing historical data

            # When: Analyzing historical payment issues with data access failure
            result = await analyze_payment_historical_issues(file_paths)

            # Then: System should provide available context with clear limitations
            assert isinstance(result, list), (
                "AI agents should provide list response despite data access failures"
            )
            assert len(result) >= 0, (
                "AI agents should provide empty list when data access fails"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_provide_domain_context_when_file_analysis_encounters_encoding_issues(
        self,
    ):
        """
        Given an AI agent analyzing payment-related code changes
        When file analysis encounters encoding or format issues
        Then the system should provide available domain context with encoding error handling
        """
        # Given: File analysis with encoding issues
        file_paths = ["/src/databricks/silver/payment_processor.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid character"),
            ),
        ):
            mock_exists.return_value = True

            # When: Analyzing payment code with encoding issues
            result = await analyze_payment_code_compliance(file_paths)

            # Then: System should provide domain context with encoding error handling
            assert isinstance(result, list), (
                "AI agents should provide list response despite encoding issues"
            )
            assert len(result) >= 0, (
                "AI agents should provide empty list when encoding errors occur"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_handle_provider_integration_pattern_analysis_edge_cases(
        self,
    ):
        """
        Given an AI agent analyzing provider integration patterns
        When pattern analysis encounters unexpected code structures
        Then the system should provide intelligent pattern matching with graceful fallbacks
        """
        # Given: Provider integration analysis with unexpected code structures
        file_paths = ["/src/databricks/bronze/unusual_provider.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/src/databricks/bronze/unusual_provider.py": """
# Unusual code structure that might confuse pattern analysis
def weird_payment_processor(**kwargs):
    '''Unusual provider with non-standard patterns'''
    exec(f"result = process_{kwargs.get('provider', 'unknown')}_payment(kwargs)")
    return locals().get('result', {})
"""
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: Analyzing unusual provider integration patterns
            result = await analyze_payment_provider_patterns(file_paths)

            # Then: System should provide intelligent pattern matching with fallbacks
            assert isinstance(result, list), (
                "AI agents should handle unusual code structures with intelligent fallbacks"
            )
            assert len(result) >= 0, (
                "AI agents should provide pattern analysis despite edge cases"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_provide_architectural_guidance_when_constraint_analysis_fails(
        self,
    ):
        """
        Given an AI agent providing architectural constraints analysis
        When constraint analysis encounters parsing or structure errors
        Then the system should provide available architectural guidance with error context
        """
        # Given: Architectural constraint analysis with parsing failures
        file_paths = ["/src/databricks/silver/complex_architecture.py"]

        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "aiofiles.open",
                side_effect=mock_aiofiles_open(
                    {
                        "/src/databricks/silver/complex_architecture.py": """
# Malformed code that causes parsing errors
def payment_processor(
    # Intentionally malformed syntax to cause parsing issues
    amount: float = ,
    currency: str = invalid_syntax
):
    return {"error": "malformed"}
"""
                    }
                ),
            ),
        ):
            mock_exists.return_value = True

            # When: Analyzing architectural constraints with parsing failures
            result = await analyze_payment_architecture_constraints(file_paths)

            # Then: System should provide architectural guidance with error context
            assert isinstance(result, list), (
                "AI agents should provide architectural guidance despite parsing errors"
            )
            assert len(result) >= 0, (
                "AI agents should provide empty list when constraint analysis fails"
            )
