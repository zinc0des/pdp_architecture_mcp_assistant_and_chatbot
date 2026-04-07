"""
Data Quality Analysis Tools

Provides analysis of test files for PDP standards compliance.
Focuses purely on analyzing existing test code.
"""

import os
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from pdp_dev_mcp.mcp_instance import mcp


@dataclass
class AnalysisIssue:
    """Represents an issue found in a test file."""

    issue_type: str
    severity: str
    description: str
    file_path: str
    line_number: int | None = None
    example_code: str | None = None
    suggested_fix: str | None = None


@dataclass
class FileAnalysisResult:
    """Complete analysis of a test file."""

    file_path: str
    total_tests: int
    issues: list[AnalysisIssue]
    good_patterns: list[str]
    compliance_score: float


# DQ Standards for Analysis
ALERT_NAME_PATTERN = r"^PDP Alert \| SEV\d+(\.\d+)? \| .+ \| .+ \| .+"

VALID_DQ_CATEGORIES = [
    "Accuracy",
    "Availability",
    "Completeness",
    "Consistency",
    "Performance",
    "Reliability",
    "Timeliness",
]

VALID_SUBJECT_AREAS = [
    "AU",
    "AccountUpdater",
    "AuthN",
    "Authentication",
    "BIN",
    "COP",
    "CostOfPayments",
    "Fraud",
    "NT",
    "NetworkToken",
    "PMT",
    "PaymentTransactions",
]

VALID_TEST_TYPES = ["Diff", "Functional", "Integration"]
VALID_SEVERITIES = ["SEV1", "SEV1.5", "SEV2", "SEV2.5", "SEV3", "SEV3.5", "SEV4"]
REQUIRED_CLASSIFICATION_FIELDS = ["alert_name", "subject_area", "test_type", "test_id"]
DEBUGGING_PATTERNS = [".display()", "display(", "print(", "logger.", "logging."]


def _analyze_file_content(file_path: str) -> FileAnalysisResult:
    """Core analysis logic for a single file."""
    if not os.path.exists(file_path):
        return FileAnalysisResult(
            file_path=file_path,
            total_tests=0,
            issues=[
                AnalysisIssue(
                    "file_not_found",
                    "critical",
                    f"File not found: {file_path}",
                    file_path,
                )
            ],
            good_patterns=[],
            compliance_score=0.0,
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return FileAnalysisResult(
            file_path=file_path,
            total_tests=0,
            issues=[
                AnalysisIssue(
                    "read_error", "critical", f"Cannot read file: {str(e)}", file_path
                )
            ],
            good_patterns=[],
            compliance_score=0.0,
        )

    issues = []
    good_patterns = []

    # Count test functions
    test_functions = re.findall(r"def test_\w+\(", content)
    total_tests = len(test_functions)

    if total_tests == 0:
        return FileAnalysisResult(
            file_path=file_path,
            total_tests=0,
            issues=[
                AnalysisIssue(
                    "no_tests_found",
                    "critical",
                    "No test functions found in file - should contain test_* functions",
                    file_path,
                )
            ],
            good_patterns=[],
            compliance_score=0.0,  # No tests = lowest score
        )

    # Scoring system: Each major area can contribute points
    total_possible_points = 100
    earned_points = 0

    # 1. Alert Naming (20 points)
    alert_names = re.findall(r'alert_name\s*=\s*["\']([^"\']+)["\']', content)
    if alert_names:
        valid_alerts = 0
        for alert_name in alert_names:
            if re.match(ALERT_NAME_PATTERN, alert_name):
                good_patterns.append(f"Proper alert naming: {alert_name[:50]}...")
                valid_alerts += 1
            else:
                issues.append(
                    AnalysisIssue(
                        "invalid_alert_name",
                        "medium",
                        f"Alert name doesn't follow PDP pattern: {alert_name[:50]}...",
                        file_path,
                    )
                )
        if valid_alerts > 0:
            earned_points += 20

    # 2. Required Classification Fields (30 points)
    missing_fields = []
    for field in REQUIRED_CLASSIFICATION_FIELDS:
        field_pattern = rf'{field}\s*=\s*["\'][^"\']*["\']'
        if not re.search(field_pattern, content):
            missing_fields.append(field)

    # Award points based on completeness
    field_completeness = (
        len(REQUIRED_CLASSIFICATION_FIELDS) - len(missing_fields)
    ) / len(REQUIRED_CLASSIFICATION_FIELDS)
    earned_points += int(30 * field_completeness)

    if len(missing_fields) == 0:
        good_patterns.append("All required classification fields present")
    else:
        for field in missing_fields:
            issues.append(
                AnalysisIssue(
                    "missing_classification",
                    "medium",
                    f"Missing required classification field: {field}",
                    file_path,
                )
            )

    # 3. Subject Area Validity (15 points)
    subject_areas = re.findall(r'subject_area\s*=\s*["\']([^"\']+)["\']', content)
    if subject_areas:
        valid_subject_areas = 0
        for subject_area in subject_areas:
            if subject_area in VALID_SUBJECT_AREAS:
                valid_subject_areas += 1
                good_patterns.append(f"Valid subject area: {subject_area}")
            else:
                issues.append(
                    AnalysisIssue(
                        "invalid_subject_area",
                        "medium",
                        f"Invalid subject area: {subject_area}. Valid options: {', '.join(VALID_SUBJECT_AREAS)}",
                        file_path,
                    )
                )

        # Award points proportionally based on valid vs total subject areas
        subject_area_score = int(15 * (valid_subject_areas / len(subject_areas)))
        earned_points += subject_area_score

    # 4. Metadata Completeness (20 points)
    has_test_id = bool(re.search(r'test_id\s*=\s*["\']([^"\']+)["\']', content))
    has_severity = bool(re.search(r'severity\s*=\s*["\']SEV\d+(\.\d+)?["\']', content))
    has_test_type = bool(re.search(r'test_type\s*=\s*["\'][^"\']+["\']', content))

    metadata_score = 0
    if has_test_id:
        metadata_score += 7

        # Validate UUID format for test_id
        test_id_matches = re.findall(r'test_id\s*=\s*["\']([^"\']+)["\']', content)
        for test_id in test_id_matches:
            try:
                uuid.UUID(test_id)
                good_patterns.append(f"Valid UUID format for test_id: {test_id[:8]}...")
            except ValueError:
                issues.append(
                    AnalysisIssue(
                        "invalid_test_id_format",
                        "medium",
                        f"test_id is not a valid UUID format: {test_id}",
                        file_path,
                    )
                )
                # Reduce metadata score for invalid UUID
                metadata_score -= 2

    if has_severity:
        metadata_score += 7
    if has_test_type:
        metadata_score += 6

    earned_points += metadata_score

    if has_test_id and has_severity and has_test_type:
        good_patterns.append("Complete metadata classification")

    # 5. Debugging Patterns (15 points)
    has_debugging = any(pattern in content for pattern in DEBUGGING_PATTERNS)
    if has_debugging:
        good_patterns.append("Contains debugging patterns for investigation")
        earned_points += 15
    else:
        issues.append(
            AnalysisIssue(
                "missing_debugging",
                "low",
                "No debugging patterns found (display, print, etc.)",
                file_path,
            )
        )

    # Calculate compliance score (0-1)
    compliance_score = earned_points / total_possible_points

    return FileAnalysisResult(
        file_path=file_path,
        total_tests=total_tests,
        issues=issues,
        good_patterns=good_patterns,
        compliance_score=compliance_score,
    )


@mcp.tool(
    description="Analyze a single test file for data quality standards compliance. Returns compliance score, issues found, and good patterns identified."
)
def analyze_test_file(file_path: str) -> dict[str, Any]:
    """Analyze a single test file for standards compliance."""
    result = _analyze_file_content(file_path)

    # Convert to dict for JSON serialization
    return {
        "file_path": result.file_path,
        "total_tests": result.total_tests,
        "issues": [asdict(issue) for issue in result.issues],
        "good_patterns": result.good_patterns,
        "compliance_score": result.compliance_score,
    }


@mcp.tool(
    description="Analyze multiple test files for data quality standards compliance. Provides batch analysis with individual and summary results."
)
def analyze_multiple_files(file_paths: list[str]) -> dict[str, Any]:
    """Analyze multiple test files in batch."""
    results: dict[str, dict[str, Any]] = {}
    total_files = len(file_paths)
    total_issues = 0
    total_compliance = 0.0

    for file_path in file_paths:
        result = _analyze_file_content(file_path)
        results[file_path] = {
            "total_tests": result.total_tests,
            "issues": [asdict(issue) for issue in result.issues],
            "good_patterns": result.good_patterns,
            "compliance_score": result.compliance_score,
        }
        total_issues += len(result.issues)
        total_compliance += result.compliance_score

    return {
        "individual_results": results,
        "summary": {
            "total_files_analyzed": total_files,
            "total_issues_found": total_issues,
            "average_compliance": total_compliance / total_files
            if total_files > 0
            else 0.0,
            "files_with_issues": sum(
                1 for r in results.values() if len(r["issues"]) > 0
            ),
        },
    }


@mcp.tool(
    description="Get data quality analysis standards and validation criteria used by the analyzer."
)
def get_analysis_standards() -> dict[str, Any]:
    """Return the standards used for analysis."""
    return {
        "valid_dq_categories": VALID_DQ_CATEGORIES,
        "valid_subject_areas": VALID_SUBJECT_AREAS,
        "valid_test_types": VALID_TEST_TYPES,
        "valid_severities": VALID_SEVERITIES,
        "required_fields": REQUIRED_CLASSIFICATION_FIELDS,
        "debugging_patterns": DEBUGGING_PATTERNS,
        "alert_name_pattern": ALERT_NAME_PATTERN,
        "analysis_info": {
            "total_validation_categories": len(VALID_DQ_CATEGORIES),
            "total_subject_areas": len(VALID_SUBJECT_AREAS),
            "required_classification_fields": len(REQUIRED_CLASSIFICATION_FIELDS),
        },
    }
