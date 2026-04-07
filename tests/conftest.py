"""
Shared test fixtures for DQ tools testing.
"""

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
print(sys.path)


@pytest.fixture
def sample_test_file() -> Generator[str, None, None]:
    """Create a sample test file for testing."""
    content = '''"""
Data Quality Test: Transaction Completeness
Tests completeness of transaction data.
"""

import pytest
from pyspark.sql import SparkSession

@pytest.mark.testclassification(
    test_type="Integration",
    subject_area="PaymentTransactions",
    severity="SEV3",
    is_active="True",
    frequency="Daily",
    test_id="03578780-19e5-4ed7-b3e3-94059772c486",
    alert_name="PDP Alert | SEV3 | Completeness | Missing Field | PMT | Transaction data is incomplete",
    description="Test that transaction data is complete"
)
def test_payment_pipelines_can_validate_transaction_data_completeness_for_fraud_prevention():
    """
    As a payment processing pipeline
    When I receive transaction data for validation
    Then I can verify completeness to prevent fraud and ensure data integrity
    """
    # Basic test implementation with debugging
    sample_data = [{"id": 1}, {"id": 2}]
    print(f"Found {len(sample_data)} records")
    assert True

class TestTransactionData:
    """Test transaction data quality."""

    def test_data_validators_can_verify_required_fields_for_downstream_processing(self):
        """
        As a data validation system
        When I process transaction data
        Then I can verify required fields exist for reliable downstream processing
        """
        pass
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def empty_test_file() -> Generator[str, None, None]:
    """Create an empty test file for testing edge cases."""
    content = '''"""
Empty test file with no test functions.
"""
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_metadata_test_file() -> Generator[str, None, None]:
    """Create a test file with invalid metadata for testing."""
    content = '''"""
Test file with invalid metadata.
"""

import pytest

@pytest.mark.testclassification(
    test_type="InvalidType",
    subject_area="InvalidSubject",
    severity="SEV3",
    test_id="7c6729e5-29c2-4cc2-be33-479abc6ad8da",
    alert_name="Invalid alert name format",
    description="Test with invalid metadata"
)
def test_test_runners_can_handle_invalid_metadata_for_robust_execution():
    """
    As a test execution framework
    When I encounter tests with invalid classification metadata
    Then I can handle them gracefully to maintain robust test suite execution
    """
    assert True
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# Azure DevOps Integration Test Fixtures


@pytest.fixture(scope="session")
def cleanup_integration_test_comments():
    """
    Pytest fixture to clean up integration test comments before tests run.

    This fixture runs once per test session and cleans up test comments
    from the configured PR to prevent accumulation of test artifacts.

    Usage:
        @pytest.mark.integration
        class TestSomething:
            def test_something(self, cleanup_integration_test_comments):
                # Test will run with clean PR comments
                pass
    """
    from .integration.cleanup_test_comments import cleanup_integration_test_comments

    # Configuration for the test PR
    # These should match the PR used in integration tests
    TEST_CONFIG = {
        "org": "microsoft",
        "project": "Universal Store",
        "repository": "Commerce.PaymentsDataPlatform",
        "pr_id": 13844374,  # Main test PR ID used across integration tests
    }

    print("\n🧹 Setting up integration test environment...")
    print(f"Cleaning up test comments from PR {TEST_CONFIG['pr_id']}...")

    # Clean up test comments before tests run
    cleanup_result = cleanup_integration_test_comments(
        org=TEST_CONFIG["org"],
        project=TEST_CONFIG["project"],
        repository=TEST_CONFIG["repository"],
        pr_id=TEST_CONFIG["pr_id"],
        dry_run=False,  # Set to True for debugging
    )

    print(f"Cleanup result: {cleanup_result['message']}")

    # Return the cleanup result for tests that might want to check it
    yield cleanup_result

    # Optional: Clean up again after all tests complete
    print("\n🧹 Post-test cleanup...")
    final_cleanup = cleanup_integration_test_comments(
        org=TEST_CONFIG["org"],
        project=TEST_CONFIG["project"],
        repository=TEST_CONFIG["repository"],
        pr_id=TEST_CONFIG["pr_id"],
        dry_run=False,
    )
    print(f"Final cleanup result: {final_cleanup['message']}")


@pytest.fixture
def test_pr_config():
    """
    Provide standard test PR configuration for integration tests.

    This ensures all integration tests use the same PR and makes it easy
    to change the test PR in one place if needed.
    """
    return {
        "org": "microsoft",
        "project": "Universal Store",
        "repository": "Commerce.PaymentsDataPlatform",
        "pr_id": 13844374,
    }
