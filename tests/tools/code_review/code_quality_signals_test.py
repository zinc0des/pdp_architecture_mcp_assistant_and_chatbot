"""
Tests for code quality signal detection.

Tests focus on AI's ability to detect, classify, and reason about quality signals
across different categories and severity levels.
"""

import tempfile
import os

import pytest

from pdp_dev_mcp.tools.code_review.code_quality_signals import (
    get_code_quality_signals,
    SeverityLevel,
    SignalSource,
    CodeQualityReport,
)


class TestAIAgentsCanDetectCodeQualitySignals:
    """Test AI agents' ability to detect and classify code quality signals."""

    @pytest.mark.asyncio
    async def test_ai_agents_can_detect_static_analysis_signals_in_python_code(
        self,
    ) -> None:
        """
        As an AI agent performing code quality analysis
        When I analyze Python code with various quality issues
        Then I detect static analysis signals with appropriate severity levels
        """
        # Given: Python code with static analysis issues
        python_code = (
            '''
def very_long_function_that_does_too_many_things():
    """This function is way too long and should be broken up."""
    # TODO: Refactor this mess
    result = ""
    for i in range(100):
        for j in range(50):
            for k in range(25):  # Deeply nested loops
                if i > 10 and j > 20 and k > 5 and i < 90 and j < 45:  # Complex conditional
                    result += f"Processing {i}, {j}, {k}"  # String concatenation in loop
                    # More processing...
                    x = 1
                    y = 2
                    z = 3
                    # ... many more lines to make function long
'''
            + "\n    pass" * 50
        )  # Make function very long

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            temp_file = f.name

        try:
            # When: AI agent analyzes the code for quality signals
            result = await get_code_quality_signals([temp_file])

            # Then: Multiple quality signals are detected
            assert isinstance(result, CodeQualityReport)
            assert result.total_signals > 0
            assert len(result.quality_signals) > 0

            # And: Signals have appropriate sources and categories
            signal_sources = {signal.source for signal in result.quality_signals}
            assert SignalSource.STATIC_ANALYSIS in signal_sources
            assert SignalSource.PERFORMANCE_PATTERNS in signal_sources

            # And: Severity levels are appropriately assigned
            has_medium_severity = any(
                s.severity == SeverityLevel.MEDIUM for s in result.quality_signals
            )
            assert has_medium_severity

            # And: Specific issues are detected
            signal_titles = {signal.title for signal in result.quality_signals}
            assert any("Long Function" in title for title in signal_titles)
            assert any("Technical Debt" in title for title in signal_titles)
            assert any("Nested Loops" in title for title in signal_titles)

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_detect_security_vulnerabilities_with_critical_severity(
        self,
    ) -> None:
        """
        As an AI agent focused on security analysis
        When I analyze code with security vulnerabilities
        Then I detect critical security signals with appropriate business impact
        """
        # Given: Code with security vulnerabilities
        vulnerable_code = """
# Configuration with hardcoded credentials
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"

def process_payment(card_number, amount):
    # Hardcoded test data - NEVER DO THIS
    test_card = "4111-1111-1111-1111"
    cvv = 123
    expiry = "12/25"
    
    # SQL injection vulnerability
    query = f"SELECT * FROM payments WHERE card = '{card_number}'"
    execute(query)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(vulnerable_code)
            temp_file = f.name

        try:
            # When: AI agent analyzes for security vulnerabilities
            result = await get_code_quality_signals([temp_file])

            # Then: Critical security vulnerabilities are detected
            security_signals = [
                s
                for s in result.quality_signals
                if s.category == "security_vulnerabilities"
            ]
            assert len(security_signals) > 0

            # And: Some signals have critical severity
            critical_signals = [
                s for s in security_signals if s.severity == SeverityLevel.CRITICAL
            ]
            assert len(critical_signals) > 0

            # And: Business impact is provided for critical issues
            for signal in critical_signals:
                assert signal.business_impact is not None
                assert "CRITICAL" in signal.business_impact.upper()

            # And: Specific security issues are identified
            signal_descriptions = {s.description for s in security_signals}
            assert any("credential" in desc.lower() for desc in signal_descriptions)

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_detect_payment_domain_specific_violations(
        self,
    ) -> None:
        """
        As an AI agent specializing in payment processing
        When I analyze payment-related code with domain violations
        Then I detect PCI compliance and payment-specific issues
        """
        # Given: Payment code with PCI compliance violations
        payment_code = """
def process_credit_card_payment(card_data):
    # PCI VIOLATION: Never store full card numbers
    card_number = "4111-1111-1111-1111"
    cvv = 123
    expiry_date = "12/25"
    
    # Missing error handling for payment operations
    charge_result = process_payment(card_number, amount=100.00)
    
    return charge_result

def handle_chargeback(transaction_id):
    # Payment operation without error handling
    refund_amount = calculate_refund(transaction_id)
    process_refund(refund_amount)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(payment_code)
            temp_file = f.name

        try:
            # When: AI agent analyzes with domain detection enabled
            result = await get_code_quality_signals(
                [temp_file], enable_domain_detection=True
            )

            # Then: Domain-specific violations are detected
            domain_signals = [
                s
                for s in result.quality_signals
                if s.source == SignalSource.DOMAIN_PATTERNS
            ]
            assert len(domain_signals) > 0

            # And: PCI compliance violations are flagged as critical
            pci_violations = [
                s
                for s in domain_signals
                if "pci" in s.title.lower() and s.severity == SeverityLevel.CRITICAL
            ]
            assert len(pci_violations) > 0

            # And: Domain context is provided
            assert result.domain_context["payment_domain_detected"] is True
            assert result.domain_context["pci_compliance_issues"] > 0

            # And: Payment-specific recommendations are generated
            assert len(result.domain_context["domain_specific_recommendations"]) > 0

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_filter_signals_by_severity_threshold(self) -> None:
        """
        As an AI agent with configurable analysis depth
        When I set a severity threshold for quality analysis
        Then I receive only signals meeting or exceeding that threshold
        """
        # Given: Code with mixed severity issues
        mixed_code = """
def example_function():
    password = "hardcoded_password"  # HIGH severity
    x = 42  # Magic number - LOW severity
    very_long_line_that_exceeds_the_recommended_character_limit_and_should_be_broken_up_for_better_readability = True  # INFO severity
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(mixed_code)
            temp_file = f.name

        try:
            # When: AI agent analyzes with HIGH severity threshold
            result_high = await get_code_quality_signals(
                [temp_file], severity_threshold=SeverityLevel.HIGH
            )

            # Then: Only high and critical severity signals are included
            for signal in result_high.quality_signals:
                assert signal.severity.value in ["high", "critical"]

            # When: AI agent analyzes with LOW severity threshold
            result_low = await get_code_quality_signals(
                [temp_file], severity_threshold=SeverityLevel.LOW
            )

            # Then: More signals are included (low, medium, high, critical)
            assert len(result_low.quality_signals) >= len(result_high.quality_signals)

            low_and_above = [
                s
                for s in result_low.quality_signals
                if s.severity.value in ["low", "medium", "high", "critical"]
            ]
            assert len(low_and_above) == len(result_low.quality_signals)

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_focus_analysis_with_include_patterns(self) -> None:
        """
        As an AI agent with targeted analysis needs
        When I specify include patterns for specific quality concerns
        Then I receive signals filtered to those areas of focus
        """
        # Given: Code with various types of issues
        diverse_code = """
def security_issue():
    api_key = "hardcoded_key"  # Security issue
    
def performance_issue():
    result = ""
    for i in range(1000):
        result += f"item {i}"  # Performance issue
        
def documentation_issue():
    # Missing docstring - documentation issue
    return 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(diverse_code)
            temp_file = f.name

        try:
            # When: AI agent focuses only on security patterns
            security_result = await get_code_quality_signals(
                [temp_file], include_patterns=["security"]
            )

            # Then: Only security-related signals are returned
            for signal in security_result.quality_signals:
                assert "security" in signal.category.lower()

            # When: AI agent focuses on performance patterns
            performance_result = await get_code_quality_signals(
                [temp_file], include_patterns=["performance"]
            )

            # Then: Only performance-related signals are returned
            for signal in performance_result.quality_signals:
                assert "performance" in signal.category.lower()

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_receive_comprehensive_quality_report_with_metrics(
        self,
    ) -> None:
        """
        As an AI agent performing comprehensive quality analysis
        When I analyze code for quality signals
        Then I receive a detailed report with metrics and recommendations
        """
        # Given: Code with various quality issues
        code_sample = """
def problematic_function():
    # TODO: Fix this later
    password = "secret123"  # Security issue
    result = ""
    for i in range(100):
        result += str(i)  # Performance issue
    return result

class UndocumentedClass:
    def method_without_docs(self):
        return 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_sample)
            temp_file = f.name

        try:
            # When: AI agent requests comprehensive quality analysis
            result = await get_code_quality_signals([temp_file])

            # Then: Comprehensive metrics are provided
            assert isinstance(result.signals_by_severity, dict)
            assert isinstance(result.signals_by_category, dict)
            assert isinstance(result.overall_quality_score, (int, float))
            assert 0 <= result.overall_quality_score <= 100

            # And: Signal categories are properly structured
            assert hasattr(result.signal_categories, "standard_categories")
            assert hasattr(result.signal_categories, "detected_novel_categories")
            assert hasattr(result.signal_categories, "allow_novel_categories")

            # And: AI-enabling recommendations are provided
            assert isinstance(result.recommendations, list)
            assert len(result.recommendations) > 0

            # And: Each signal contains actionable information
            for signal in result.quality_signals:
                assert signal.signal_id is not None
                assert signal.source is not None
                assert signal.category is not None
                assert signal.severity is not None
                assert signal.title is not None
                assert signal.file_path == temp_file

        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_detect_missing_test_coverage(self) -> None:
        """
        As an AI agent evaluating test coverage
        When I analyze production code without corresponding tests
        Then I detect testing gaps and recommend test creation
        """
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: Production code without tests
            production_file = os.path.join(temp_dir, "payment_processor.py")
            with open(production_file, "w") as f:
                f.write('''
def process_payment(amount, card_number):
    """Process a payment transaction."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {"status": "success", "transaction_id": "12345"}
''')

            # When: AI agent analyzes for testing patterns
            result = await get_code_quality_signals([production_file])

            # Then: Missing test coverage is detected
            testing_signals = [
                s
                for s in result.quality_signals
                if s.source == SignalSource.TESTING_PATTERNS
            ]
            assert len(testing_signals) > 0

            # And: Specific recommendation is provided
            test_signal = testing_signals[0]
            assert "test" in test_signal.title.lower()
            assert test_signal.severity == SeverityLevel.MEDIUM
            assert "business_impact" in test_signal.__dict__

    @pytest.mark.asyncio
    async def test_ai_agents_handle_file_access_errors_gracefully(self) -> None:
        """
        As an AI agent with robust error handling
        When I encounter files that cannot be read
        Then I handle errors gracefully and continue analysis
        """
        # Given: Non-existent file and valid file
        non_existent_file = "/path/that/does/not/exist.py"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def valid_function(): pass")
            valid_file = f.name

        try:
            # When: AI agent analyzes mixed file list
            result = await get_code_quality_signals([non_existent_file, valid_file])

            # Then: Analysis completes without errors
            assert isinstance(result, CodeQualityReport)
            assert result.total_signals >= 0

            # And: Valid files are still processed
            assert valid_file in result.file_paths

        finally:
            os.unlink(valid_file)

    @pytest.mark.asyncio
    async def test_ai_agents_can_assess_overall_code_quality_score(self) -> None:
        """
        As an AI agent providing quality assessment
        When I analyze code with varying quality levels
        Then I calculate meaningful quality scores based on signal severity
        """
        # Given: High quality code (minimal issues)
        high_quality_code = '''
def well_designed_function(amount: float) -> dict:
    """
    Process a payment with proper error handling.
    
    Args:
        amount: Payment amount in dollars
        
    Returns:
        dict: Payment result with status and transaction ID
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    try:
        result = {"status": "success", "amount": amount}
        return result
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        raise
'''

        # Given: Poor quality code (many issues)
        poor_quality_code = """
def bad_function():
    password = "hardcoded_password"
    api_key = "secret_key_123"
    result = ""
    for i in range(1000):
        for j in range(500):
            for k in range(100):
                result += f"processing {i} {j} {k}"
    return result
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1:
            f1.write(high_quality_code)
            high_quality_file = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f2:
            f2.write(poor_quality_code)
            poor_quality_file = f2.name

        try:
            # When: AI agent analyzes both code samples
            high_quality_result = await get_code_quality_signals([high_quality_file])
            poor_quality_result = await get_code_quality_signals([poor_quality_file])

            # Then: Quality scores reflect the difference in code quality
            assert high_quality_result.overall_quality_score is not None
            assert poor_quality_result.overall_quality_score is not None
            assert (
                high_quality_result.overall_quality_score
                > poor_quality_result.overall_quality_score
            )

            # And: Quality scores are in valid range
            assert 0 <= high_quality_result.overall_quality_score <= 100
            assert 0 <= poor_quality_result.overall_quality_score <= 100

        finally:
            os.unlink(high_quality_file)
            os.unlink(poor_quality_file)

    @pytest.mark.asyncio
    async def test_ai_agents_receive_hybrid_classification_system(self) -> None:
        """
        As an AI agent capable of flexible reasoning
        When I analyze code quality signals
        Then I receive both standard and novel category classifications
        """
        # Given: Code that might generate novel category patterns
        specialized_code = """
def custom_payment_flow():
    # This could generate novel categories beyond standard ones
    pass
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(specialized_code)
            temp_file = f.name

        try:
            # When: AI agent analyzes code for quality signals
            result = await get_code_quality_signals([temp_file])

            # Then: Hybrid classification system is provided
            categories = result.signal_categories
            assert hasattr(categories, "standard_categories")
            assert hasattr(categories, "detected_novel_categories")
            assert hasattr(categories, "allow_novel_categories")
            assert categories.allow_novel_categories is True

            # And: Standard categories are well-defined
            standard_categories = categories.standard_categories
            expected_categories = [
                "code_smells",
                "security_vulnerabilities",
                "performance_issues",
                "maintainability_concerns",
                "testing_gaps",
                "documentation_issues",
                "domain_violations",
            ]
            for expected in expected_categories:
                assert expected in standard_categories

            # And: Category descriptions are provided for AI understanding
            assert isinstance(categories.category_descriptions, dict)
            assert len(categories.category_descriptions) > 0

        finally:
            os.unlink(temp_file)
