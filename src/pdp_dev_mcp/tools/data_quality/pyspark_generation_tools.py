"""
PySpark Test Generation Tools

Focused on generating PySpark test files with proper debugging patterns,
statistical analysis capabilities, and PDP standards compliance.
"""

import uuid
from typing import Any

from pdp_dev_mcp.mcp_instance import mcp

# Test Generation Constants
SUBJECT_AREA_MAPPING = {
    "PaymentTransactions": "PMT",
    "BIN": "BIN",
    "CostOfPayments": "COP",
    "Fraud": "FRAUD",
    "AccountUpdater": "AU",
    "NetworkTokenization": "NT",
}

DIRECTORY_MAPPING = {
    "PaymentTransactions": "src/databricks/workspace/notebooks/PaymentTransactions/Test",
    "PMT": "src/databricks/workspace/notebooks/PaymentTransactions/Test",
    "BIN": "src/databricks/workspace/notebooks/BIN/Test",
    "CostOfPayments": "src/databricks/workspace/notebooks/CostOfPayments/Test",
    "COP": "src/databricks/workspace/notebooks/CostOfPayments/Test",
    "Fraud": "src/databricks/workspace/notebooks/Fraud/Test",
    "FRAUD": "src/databricks/workspace/notebooks/Fraud/Test",
    "AccountUpdater": "src/databricks/workspace/notebooks/AccountUpdater/Test",
    "AU": "src/databricks/workspace/notebooks/AccountUpdater/Test",
    "NetworkTokenization": "src/databricks/workspace/notebooks/NetworkTokenization/Test",
    "NT": "src/databricks/workspace/notebooks/NetworkTokenization/Test",
}


def _generate_test_classification(
    test_type: str,
    subject_area: str,
    data_quality_category: str,
    table_name: str,
    field_name: str | None,
    is_canary: bool = False,
) -> dict[str, Any]:
    """Generate proper test classification metadata."""
    test_id = str(uuid.uuid4())
    subject_abbrev = SUBJECT_AREA_MAPPING.get(subject_area, subject_area)

    # Generate proper alert name based on test type
    if test_type == "Functional":
        issue_type = "Regression"
    elif test_type == "Diff":
        issue_type = "Data Mismatch"
    else:  # Integration (default)
        issue_type = (
            "Empty Field"
            if data_quality_category == "Completeness"
            else "Invalid Field"
        )

    if field_name:
        description = f"{table_name}.{field_name} has {issue_type.lower()}"
    else:
        description = f"{table_name} has {data_quality_category.lower()} issues"

    alert_name = f"PDP Alert | SEV3 | {data_quality_category} | {issue_type} | {subject_abbrev} | {description}"

    return {
        "test_type": test_type,
        "subject_area": subject_area,
        "severity": "SEV3",
        "is_active": "True",
        "frequency": "Daily",
        "test_id": test_id,
        "alert_name": alert_name,
        "description": description,
        "is_canary": "True" if is_canary else "False",
    }


def _generate_completeness_template(
    classification: dict[str, str], table_name: str, field_name: str | None
) -> str:
    """Generate a completeness test template with rich debugging."""
    field_or_target = field_name or "target_field"
    clean_table = table_name.replace(".", "_")

    return f"""@pytest.mark.testclassification(
    test_type="{classification["test_type"]}",
    subject_area="{classification["subject_area"]}",
    severity="{classification["severity"]}",
    is_active="{classification["is_active"]}",
    frequency="{classification["frequency"]}",
    test_id="{classification["test_id"]}",
    alert_name="{classification["alert_name"]}",
    description="{classification["description"]}"
)
def test_{clean_table}_{field_or_target}_completeness_validation({clean_table}_data):
    \"\"\"
    Validate completeness for {table_name}{"." + field_name if field_name else ""}.

    Business Rule: {field_name or "Required fields"} should not be null/empty for valid transactions.
    \"\"\"

    # Apply business filters
    df_filtered = {clean_table}_data.filter(
        # Add appropriate business logic filters here
        col("Date") >= date_sub(current_date(), 90)  # Last 90 days
    )

    # Check for null/empty values
    failure_df = df_filtered.filter(
        col("{field_or_target}").isNull() |
        (col("{field_or_target}") == "")
    )

    failure_count = failure_df.count()

    if failure_count > 0:
        # DEBUGGING: Display sample failures before assertion
        print("=" * 80)
        print(f"🚨 DEBUGGING: Found {{failure_count}} records with null/empty {field_name or "values"}")
        print("=" * 80)

        print("DEBUGGING: Displaying sample records with null/empty values...")
        failure_df.select([
            "{field_or_target}",
            "TransactionId",
            "Date",
            "ProviderName"
        ]).limit(20).display()

        # Display summary statistics
        print("DEBUGGING: Failure distribution by provider:")
        failure_df.groupBy("ProviderName").count().orderBy(desc("count")).display()

    assert failure_count == 0, f"Found {{failure_count}} records with null/empty {field_name or "values"} in {table_name}"
"""


def _generate_accuracy_template(
    classification: dict[str, str], table_name: str, field_name: str | None
) -> str:
    """Generate an accuracy test template with validation logic."""
    field_or_target = field_name or "target_field"
    clean_table = table_name.replace(".", "_")

    return f"""@pytest.mark.testclassification(
    test_type="{classification["test_type"]}",
    subject_area="{classification["subject_area"]}",
    severity="{classification["severity"]}",
    is_active="{classification["is_active"]}",
    frequency="{classification["frequency"]}",
    test_id="{classification["test_id"]}",
    alert_name="{classification["alert_name"]}",
    description="{classification["description"]}"
)
def test_{clean_table}_{field_or_target}_accuracy_validation({clean_table}_data):
    \"\"\"
    Validate accuracy for {table_name}{"." + field_name if field_name else ""}.

    Business Rule: {field_name or "Target field"} should contain valid, accurate data according to business rules.
    \"\"\"

    # Apply business filters
    df_filtered = {clean_table}_data.filter(
        col("Date") >= date_sub(current_date(), 90)  # Last 90 days
    )

    # Implement accuracy validation (customize based on field type)
    failure_df = df_filtered.filter(
        # Add specific accuracy validation logic here
        # Examples: invalid formats, out-of-range values, mapping failures
        col("{field_or_target}").isNotNull()  # Replace with actual validation
    )

    failure_count = failure_df.count()

    if failure_count > 0:
        # DEBUGGING: Display sample failures with statistical analysis
        print("=" * 80)
        print(f"🚨 DEBUGGING: Found {{failure_count}} accuracy issues in {field_name or "data"}")
        print("=" * 80)

        print("DEBUGGING: Displaying sample problematic records...")
        failure_df.select([
            "{field_or_target}",
            "TransactionId",
            "Date",
            "ProviderName"
        ]).limit(20).display()

        # Statistical analysis for debugging
        print("DEBUGGING: Statistical breakdown of issues:")
        failure_df.groupBy("{field_or_target}").count().orderBy(desc("count")).limit(10).display()

    assert failure_count == 0, f"Found {{failure_count}} accuracy issues in {table_name}.{field_name or "data"}"
"""


def _get_target_directory(subject_area: str, test_type: str) -> str:
    """Get the correct target directory for test file placement."""
    base_dir = DIRECTORY_MAPPING.get(subject_area)
    if not base_dir:
        subject_abbrev = SUBJECT_AREA_MAPPING.get(subject_area, subject_area)
        base_dir = DIRECTORY_MAPPING.get(
            subject_abbrev, DIRECTORY_MAPPING["PaymentTransactions"]
        )

    return f"{base_dir}/{test_type}"


def _generate_filename(
    data_quality_category: str,
    table_name: str,
    subject_area: str,
    field_name: str | None,
) -> str:
    """Generate filename following PDP patterns."""
    clean_table = table_name.replace(".", "_").lower()
    subject_abbrev = SUBJECT_AREA_MAPPING.get(subject_area, subject_area).lower()

    if field_name:
        specific_check = f"{clean_table}_{field_name.lower()}"
    else:
        specific_check = f"{clean_table}_{data_quality_category.lower()}"

    return f"test_{data_quality_category.lower()}_{specific_check}_{subject_abbrev}.py"


@mcp.tool(
    description="Generate PySpark data quality test suggestions with proper PDP standards compliance, directory placement, and debugging patterns."
)
def generate_test_suggestions(
    test_type: str,
    subject_area: str,
    data_quality_category: str,
    table_name: str,
    field_name: str | None = None,
    is_canary: bool = False,
    is_pre_commit: bool = False,
    is_post_commit: bool = False,
) -> dict[str, Any]:
    """Generate PySpark test suggestions based on PDP standards."""

    # Validate inputs
    valid_test_types = ["Integration", "Functional", "Diff"]
    if test_type not in valid_test_types:
        raise ValueError(
            f"Invalid test_type '{test_type}'. Valid values: {', '.join(valid_test_types)}"
        )

    # Generate classification
    classification = _generate_test_classification(
        test_type,
        subject_area,
        data_quality_category,
        table_name,
        field_name,
        is_canary,
    )

    # Add secondary characteristics
    classification["is_pre_commit"] = "True" if is_pre_commit else "False"
    classification["is_post_commit"] = "True" if is_post_commit else "False"

    # Generate appropriate test template based on category
    if data_quality_category == "Completeness":
        test_template = _generate_completeness_template(
            classification, table_name, field_name
        )
    elif data_quality_category == "Accuracy":
        test_template = _generate_accuracy_template(
            classification, table_name, field_name
        )
    else:
        # Use accuracy template as base for other categories
        test_template = _generate_accuracy_template(
            classification, table_name, field_name
        )

    # Get directory and filename
    target_directory = _get_target_directory(subject_area, test_type)
    filename = _generate_filename(
        data_quality_category, table_name, subject_area, field_name
    )

    return {
        "test_classification": classification,
        "test_template": test_template,
        "target_directory": target_directory,
        "filename": filename,
        "full_path": f"{target_directory}/{filename}",
        "implementation_guidance": [
            "Tests include comprehensive debugging patterns",
            "Statistical analysis built into failure investigation",
            "Proper business rule documentation required",
            "Directory placement follows PDP structure",
        ],
        "debugging_features": [
            "Sample failure records displayed via .display()",
            "Statistical breakdown of issues",
            "Provider-level failure distribution",
            "Rich console output for investigation",
        ],
    }


@mcp.tool(
    description="Get guidance on PySpark test structure, debugging patterns, and best practices."
)
def get_pyspark_test_guidance() -> list[str]:
    """Return guidance on PySpark test best practices."""
    return [
        "# PySpark Test Generation Best Practices",
        "",
        "## Test Template Features:",
        "- Comprehensive debugging with .display() for Databricks",
        "- Statistical analysis for pattern identification",
        "- Business rule documentation",
        "- Proper assertion messages with context",
        "",
        "## Directory Structure:",
        "- Integration tests: {SubjectArea}/Test/Integration/",
        "- Functional tests: {SubjectArea}/Test/Functional/",
        "- Diff tests: {SubjectArea}/Test/Diff/",
        "",
        "## Debugging Capabilities:",
        "- Sample failure records with context columns",
        "- Failure distribution analysis by provider",
        "- Statistical breakdowns for pattern identification",
        "- Rich console output for investigation",
        "",
        "## When to Use PySpark Tests:",
        "- Complex validation logic needed",
        "- Statistical analysis required",
        "- Detailed debugging and investigation",
        "- Custom business rule implementation",
    ]
