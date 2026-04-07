"""
Tests for payments domain knowledge retrieval tool.

Tests focus on what AI agents can accomplish when helping developers
understand payment processing domain requirements and compliance context.
"""

import pytest
from unittest.mock import patch, mock_open

# Import the actual implementation
from pdp_dev_mcp.tools.code_review.static_analysis import get_payments_domain_context


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
                "AI agents need access to compliance requirements context to provide informed guidance. "
                f"Expected compliance requirements for AI reasoning, got: {compliance_requirements}"
            )

            # Then: AI agent has access to comprehensive compliance context including PCI DSS
            pci_requirements = [
                req for req in compliance_requirements if "PCI" in req.standard
            ]
            assert len(pci_requirements) > 0, (
                "AI agents need PCI DSS context to provide compliance-aware guidance for card processing changes. "
                f"Expected PCI requirements in context, got: {pci_requirements}"
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

            # Then: AI agent has access to proven integration patterns
            assert result.success is True, (
                "AI agents need comprehensive provider integration pattern context for guidance"
            )

            domain_patterns = result.domain_patterns
            assert len(domain_patterns) > 0, (
                "AI agents need access to domain patterns to provide contextual guidance. "
                f"Expected domain patterns for AI reasoning, got: {domain_patterns}"
            )

            # Then: AI agent has access to comprehensive provider integration context
            pattern_descriptions = [pattern.description for pattern in domain_patterns]
            assert len(pattern_descriptions) > 0, (
                "AI agents need rich pattern context to provide nuanced provider integration guidance. "
                f"Expected pattern descriptions for AI context, got: {pattern_descriptions}"
            )

            # Then: AI agent has access to both positive patterns and anti-patterns for balanced guidance
            pattern_types = [
                pattern.pattern_type.lower() for pattern in domain_patterns
            ]
            assert len(pattern_types) > 0, (
                "AI agents need diverse pattern context to provide comprehensive guidance on what works and what doesn't"
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

            # Then: AI agent has access to bronze-silver-gold architectural context
            assert result.success is True, (
                "AI agents need comprehensive data flow architectural context for guidance"
            )

            architectural_constraints = result.architectural_constraints
            assert len(architectural_constraints) > 0, (
                "AI agents need access to data flow architectural constraints for AI reasoning. "
                f"Expected architectural constraints, got: {architectural_constraints}"
            )

            # Then: AI agent has layer-specific responsibility context
            constraint_descriptions = [
                constraint.description for constraint in architectural_constraints
            ]
            assert any(
                "silver layer" in desc.lower() for desc in constraint_descriptions
            ), (
                "AI agents need specific silver layer transformation context for informed guidance. "
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

            # Then: AI agent has access to historical incident context
            assert result.success is True, (
                "AI agents need comprehensive historical incident context for informed guidance"
            )

            historical_issues = result.historical_issues
            assert len(historical_issues) > 0, (
                "AI agents need access to relevant historical payment processing context for AI reasoning. "
                f"Expected historical issues, got: {historical_issues}"
            )

            # Then: AI agent has specific retry-related incident context
            issue_descriptions = [issue.description for issue in historical_issues]
            assert any("retry" in desc.lower() for desc in issue_descriptions), (
                "AI agents need retry-related historical incident context for retry logic implementations. "
                f"Expected retry incidents in: {issue_descriptions}"
            )

            # Then: AI agent has access to actionable lessons learned
            assert any(
                "solution" in issue.issue_type.lower()
                or "best practice" in issue.issue_type.lower()
                for issue in historical_issues
            ), (
                "AI agents need actionable solutions and best practices context from historical incidents"
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

            # Then: AI agent has access to provider-specific historical context
            assert result.success is True, (
                "AI agents need comprehensive provider-specific historical context for informed guidance"
            )

            historical_issues = result.historical_issues
            provider_specific_issues = [
                issue
                for issue in historical_issues
                if "paypal" in issue.description.lower()
            ]
            assert len(provider_specific_issues) > 0, (
                "AI agents need PayPal-specific historical issue context for PayPal integration reasoning. "
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
