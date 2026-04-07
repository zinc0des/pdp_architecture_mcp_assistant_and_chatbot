"""
Phase 4 Prescriptive Code Review - Stub Implementation

This module provides AI-assisted line-level code comments with anti-pattern detection,
performance optimization suggestions, and security vulnerability identification.

This is a stub implementation to support BDD test development.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
import subprocess
import json
import os
import re

# Import MCP instance for tool registration
from pdp_dev_mcp.mcp_instance import mcp

# Import new context-based architecture
from pdp_dev_mcp.tools.common.azure_devops_common import AzureDevOpsPRContext
from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
    azure_devops_establish_pr_context,
)


# Migrated dataclasses from legacy pr_code_context.py
@dataclass
class PRDetails:
    """Information about a pull request."""

    pull_request_id: int
    title: str
    description: Optional[str] = None
    source_ref_name: Optional[str] = None
    target_ref_name: Optional[str] = None
    status: Optional[str] = None  # "active", "completed", "abandoned"
    author: Optional[str] = None
    created_date: Optional[str] = None
    last_merge_source_commit: Optional[str] = (
        None  # The latest commit in the source branch
    )
    last_merge_commit: Optional[str] = None  # The merge commit (for completed PRs)


def _get_pr_details_with_context(
    context: AzureDevOpsPRContext,
) -> Optional[PRDetails]:
    """
    Internal helper: Get PR details from Azure DevOps API using Azure CLI.

    This is an enhanced implementation using the
    modern AzureDevOpsPRContext architecture for type-safe and reliable context management.

    Args:
        context: Established Azure DevOps PR context containing validated org, project, repo, pr_id

    Returns:
        PRDetails object if successful, None if failed.
    """
    try:
        # Build the org URL in the format expected by Azure CLI
        org_url = f"https://dev.azure.com/{context.organization}"

        # Use Azure CLI to get PR details with proper parameters
        result = subprocess.run(
            [
                "az",
                "repos",
                "pr",
                "show",
                "--id",
                str(context.pr_id),
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return None

        pr_data = json.loads(result.stdout)

        # Extract commit ID from lastMergeSourceCommit if available (latest commit in source branch)
        last_merge_source_commit = None
        if "lastMergeSourceCommit" in pr_data and pr_data["lastMergeSourceCommit"]:
            commit_data = pr_data["lastMergeSourceCommit"]
            if isinstance(commit_data, dict):
                last_merge_source_commit = commit_data.get("commitId")
            elif isinstance(commit_data, str):
                last_merge_source_commit = commit_data

        # Extract merge commit ID (for completed PRs where source branch may be deleted)
        last_merge_commit = None
        if "lastMergeCommit" in pr_data and pr_data["lastMergeCommit"]:
            commit_data = pr_data["lastMergeCommit"]
            if isinstance(commit_data, dict):
                last_merge_commit = commit_data.get("commitId")
            elif isinstance(commit_data, str):
                last_merge_commit = commit_data

        # Convert Azure DevOps field names to our dataclass field names
        return PRDetails(
            pull_request_id=pr_data.get("pullRequestId", context.pr_id),
            title=pr_data.get("title", ""),
            description=pr_data.get("description"),
            source_ref_name=pr_data.get("sourceRefName"),
            target_ref_name=pr_data.get("targetRefName"),
            status=pr_data.get("status"),
            author=pr_data.get("createdBy", {}).get("displayName")
            if pr_data.get("createdBy")
            else None,
            created_date=pr_data.get("creationDate"),
            last_merge_source_commit=last_merge_source_commit,
            last_merge_commit=last_merge_commit,
        )

    except json.JSONDecodeError:
        return None


@dataclass
class DependencyInfo:
    """Information about a code dependency."""

    file_path: str
    symbol: str
    dependency_type: str  # "cross_repository_reference", "import", etc.
    repository: Optional[str] = None  # Repository name for cross-repo dependencies
    project: Optional[str] = None  # Project name for cross-repo dependencies
    context: Optional[str] = None  # Additional context about the dependency


@dataclass
class PRCodeContextResult:
    """Result of PR code context analysis."""

    success: bool
    pr_details: Optional[PRDetails] = None
    file_contents: Optional[Dict[str, str]] = None
    change_summary: Optional[str] = None
    work_items: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[DependencyInfo]] = None
    test_coverage: Optional["TestCoverageInfo"] = None
    test_suggestions: Optional[List["TestSuggestion"]] = None
    error: Optional[str] = None


# Enhanced modern dataclasses
@dataclass
class FileChangeItem:
    """Represents a single file item in a change entry."""

    path: str


@dataclass
class FileChange:
    """Represents a single file change in a PR."""

    item: FileChangeItem
    change_type: str  # "add", "delete", "edit", "rename"


@dataclass
class FileChangesResult:
    """Result of getting PR file changes from Azure DevOps API."""

    success: bool
    changes: Optional[List[FileChange]] = None
    error: Optional[str] = None


@dataclass
class FileContent:
    """Represents the content of a single file from Azure DevOps."""

    path: str
    content: str
    encoding: str = "utf-8"
    size_bytes: int = 0
    is_binary: bool = False
    error: Optional[str] = None


@dataclass
class FileContentsResult:
    """Result of retrieving file contents from Azure DevOps API."""

    success: bool
    files: List[FileContent] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    error_files: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def get_content_by_path(self, path: str) -> Optional[str]:
        """Get content for a specific file path."""
        for file in self.files:
            if file.path == path:
                return file.content
        return None

    def has_file(self, path: str) -> bool:
        """Check if a file path exists in the results."""
        return any(file.path == path for file in self.files)

    def get_successful_files(self) -> List[FileContent]:
        """Get only files that were successfully retrieved (no errors)."""
        return [file for file in self.files if file.error is None]


@dataclass
class TestCoverageInfo:
    """Information about a test file's coverage of a source file."""

    test_file: str
    source_file: str
    coverage_status: str = "exists"  # exists, missing, outdated


@dataclass
class MissingCoverageItem:
    """Information about missing test coverage for a function."""

    file_path: str
    function_name: str
    reason: str
    suggested_test_type: Optional[str] = None


@dataclass
class TestUpdateItem:
    """Information about a test that may need updating."""

    test_file: str
    reason: str
    hardcoded_value: Optional[str] = None


@dataclass
class TestSuggestion:
    """Suggestion for improving test coverage."""

    type: str  # business_logic_test, validation_test, integration_test, etc.
    function: str
    file: str
    description: str
    priority: str = "medium"  # low, medium, high


@dataclass
class TestCoverageResult:
    """Comprehensive test coverage analysis result."""

    existing_tests: List[TestCoverageInfo] = field(default_factory=list)
    missing_coverage: List[MissingCoverageItem] = field(default_factory=list)
    tests_needing_updates: List[TestUpdateItem] = field(default_factory=list)
    suggestions: List[TestSuggestion] = field(default_factory=list)
    total_files_analyzed: int = 0
    coverage_percentage: float = 0.0

    def get_high_priority_suggestions(self) -> List[TestSuggestion]:
        """Get suggestions marked as high priority."""
        return [s for s in self.suggestions if s.priority == "high"]

    def get_uncovered_functions(self) -> List[str]:
        """Get list of function names without test coverage."""
        return [item.function_name for item in self.missing_coverage]


@dataclass
class ChangeSummary:
    """Structured change summary with payment domain intelligence."""

    pr_title: str
    pr_description: Optional[str]
    domain_areas: List[str] = field(default_factory=list)
    critical_patterns: List[str] = field(default_factory=list)
    file_count: int = 0
    risk_level: str = "low"  # low, medium, high

    def to_summary_string(self) -> str:
        """Convert to human-readable summary string."""
        summary_parts = []

        summary_parts.append(f"PR: {self.pr_title}")
        if self.pr_description:
            summary_parts.append(f"Description: {self.pr_description}")

        if self.domain_areas:
            summary_parts.append(f"Domain areas: {', '.join(self.domain_areas)}")

        if self.critical_patterns:
            summary_parts.append(f"Critical areas: {', '.join(self.critical_patterns)}")

        summary_parts.append(f"Files: {self.file_count}")
        summary_parts.append(f"Risk: {self.risk_level}")

        return " | ".join(summary_parts)


async def analyze_test_coverage_with_context(
    pr_details: PRDetails,
    file_changes: FileChangesResult,
    file_contents: FileContentsResult,
    context_depth: str = "comprehensive",
) -> TestCoverageResult:
    """
    Analyze test coverage for changed files with payment domain expertise.

    Enhanced implementation of test coverage analysis,
    using modern dataclasses and enhanced payment testing patterns.

    Args:
        pr_details: PR metadata information
        file_changes: Structured file changes from Azure DevOps
        file_contents: File contents with metadata
        context_depth: Analysis depth (basic, comprehensive)

    Returns:
        TestCoverageResult: Comprehensive test coverage analysis
    """
    result = TestCoverageResult()

    if not file_changes.changes:
        return result

    # Track analysis metrics
    analyzed_files = 0
    covered_files = 0

    for change in file_changes.changes:
        file_path = change.item.path
        change_type = change.change_type

        # Skip test files and non-code files
        if (
            not file_path
            or "test" in file_path.lower()
            or not file_path.endswith((".py", ".cs", ".js", ".ts"))
        ):
            continue

        analyzed_files += 1

        # Generate test file pattern suggestions based on payment domain conventions
        test_patterns = _generate_test_patterns(file_path)

        # Look for existing test files
        existing_tests = []
        for pattern in test_patterns:
            if file_contents.has_file(pattern):
                existing_tests.append(
                    TestCoverageInfo(
                        test_file=pattern,
                        source_file=file_path,
                        coverage_status="exists",
                    )
                )
                covered_files += 1

        result.existing_tests.extend(existing_tests)

        # Analyze missing coverage for new files or files without tests
        if change_type == "add" or not existing_tests:
            await _analyze_missing_coverage(
                file_path=file_path,
                file_contents=file_contents,
                result=result,
                context_depth=context_depth,
            )

        # Check if existing tests need updates
        if existing_tests and context_depth == "comprehensive":
            await _analyze_test_freshness(
                existing_tests=existing_tests,
                source_file=file_path,
                file_contents=file_contents,
                result=result,
            )

    # Calculate coverage metrics
    result.total_files_analyzed = analyzed_files
    result.coverage_percentage = (
        (covered_files / analyzed_files * 100) if analyzed_files > 0 else 0.0
    )

    return result


def _generate_test_patterns(file_path: str) -> List[str]:
    """
    Generate test file patterns based on payment domain conventions.

    Args:
        file_path: Source file path

    Returns:
        List of potential test file paths
    """
    patterns = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # Standard Python patterns
    patterns.extend(
        [
            file_path.replace(".py", "_test.py"),
            file_path.replace("/src/", "/tests/").replace(".py", "_test.py"),
            f"tests/{file_path.lstrip('/').replace('.py', '_test.py')}",
            f"tests/test_{base_name}.py",
        ]
    )

    # Payment domain specific patterns
    if "payment" in file_path.lower():
        patterns.extend(
            [
                f"tests/payments/test_{base_name}.py",
                f"tests/integration/payments/test_{base_name}_integration.py",
            ]
        )

    if "provider" in file_path.lower():
        patterns.extend(
            [
                f"tests/providers/test_{base_name}.py",
                f"tests/integration/providers/test_{base_name}_integration.py",
            ]
        )

    if "fraud" in file_path.lower():
        patterns.extend(
            [
                f"tests/fraud/test_{base_name}.py",
                f"tests/security/test_{base_name}_security.py",
            ]
        )

    # .NET patterns for function apps
    if file_path.endswith(".cs"):
        patterns.extend(
            [
                file_path.replace(".cs", "Tests.cs"),
                file_path.replace("/src/", "/tests/").replace(".cs", "Tests.cs"),
                f"tests/{base_name}Tests.cs",
            ]
        )

    return list(set(patterns))  # Remove duplicates


async def _analyze_missing_coverage(
    file_path: str,
    file_contents: FileContentsResult,
    result: TestCoverageResult,
    context_depth: str,
) -> None:
    """
    Analyze missing test coverage for a file.

    Args:
        file_path: Source file path
        file_contents: File contents repository
        result: Result object to populate
        context_depth: Analysis depth
    """
    if not file_contents.has_file(file_path):
        return

    content = file_contents.get_content_by_path(file_path)
    if not content:
        return

    # Extract functions/methods based on file type
    if file_path.endswith(".py"):
        functions = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", content)
        classes = re.findall(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]", content)
    elif file_path.endswith(".cs"):
        functions = re.findall(
            r"public\s+(?:async\s+)?(?:static\s+)?[\w<>]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            content,
        )
        classes = re.findall(r"public\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
    else:
        functions = []
        classes = []

    # Analyze each function for missing coverage
    for func in functions:
        missing_item = MissingCoverageItem(
            file_path=file_path,
            function_name=func,
            reason=f"Function '{func}' lacks test coverage",
        )

        # Determine suggested test type based on payment domain patterns
        test_type, priority = _classify_function_test_needs(func, content, file_path)
        missing_item.suggested_test_type = test_type

        result.missing_coverage.append(missing_item)

        # Generate detailed suggestions for comprehensive analysis
        if context_depth == "comprehensive":
            suggestion = TestSuggestion(
                type=test_type,
                function=func,
                file=file_path,
                description=_generate_test_description(func, test_type, file_path),
                priority=priority,
            )
            result.suggestions.append(suggestion)

    # Analyze classes for structural testing needs
    for cls in classes:
        if _is_critical_payment_class(cls, content):
            suggestion = TestSuggestion(
                type="integration_test",
                function=cls,
                file=file_path,
                description=f"Create integration tests for critical payment class '{cls}'",
                priority="high",
            )
            result.suggestions.append(suggestion)


def _classify_function_test_needs(
    func_name: str, content: str, file_path: str
) -> tuple[str, str]:
    """
    Classify the testing needs for a function based on payment domain expertise.

    Args:
        func_name: Function name
        content: File content
        file_path: File path

    Returns:
        Tuple of (test_type, priority)
    """
    func_lower = func_name.lower()
    content_lower = content.lower()

    # Critical payment functions - high priority
    if any(
        keyword in func_lower
        for keyword in ["authorize", "capture", "refund", "void", "chargeback"]
    ):
        return "payment_flow_test", "high"

    if any(keyword in func_lower for keyword in ["validate", "verify", "check"]):
        if "pci" in content_lower or "card" in content_lower:
            return "security_validation_test", "high"
        return "validation_test", "medium"

    if any(keyword in func_lower for keyword in ["calculate", "compute", "process"]):
        if "fee" in content_lower or "cost" in content_lower or "rate" in content_lower:
            return "financial_calculation_test", "high"
        return "business_logic_test", "medium"

    if any(keyword in func_lower for keyword in ["fraud", "risk", "score"]):
        return "fraud_detection_test", "high"

    if any(keyword in func_lower for keyword in ["encrypt", "decrypt", "hash", "sign"]):
        return "security_test", "high"

    # API and integration functions
    if any(
        keyword in func_lower
        for keyword in ["send", "receive", "call", "invoke", "request"]
    ):
        return "integration_test", "medium"

    # Provider-specific functions
    if "provider" in file_path.lower() or any(
        provider in content_lower
        for provider in ["visa", "mastercard", "amex", "paypal", "stripe"]
    ):
        return "provider_integration_test", "high"

    # Default case
    return "unit_test", "low"


def _generate_test_description(func_name: str, test_type: str, file_path: str) -> str:
    """
    Generate detailed test description based on function and test type.

    Args:
        func_name: Function name
        test_type: Type of test needed
        file_path: File path

    Returns:
        Detailed test description
    """
    descriptions = {
        "payment_flow_test": f"Test {func_name} with various payment scenarios including success, failure, timeout, and edge cases. Verify proper state transitions and error handling.",
        "security_validation_test": f"Test {func_name} with valid/invalid security parameters, boundary conditions, and PCI compliance requirements.",
        "financial_calculation_test": f"Test {func_name} with various amounts, currencies, and rate scenarios. Verify precision, rounding, and edge cases.",
        "fraud_detection_test": f"Test {func_name} with known fraud patterns, legitimate transactions, and edge cases. Verify accuracy and performance.",
        "security_test": f"Test {func_name} with various security scenarios including malformed inputs, injection attempts, and cryptographic edge cases.",
        "integration_test": f"Test {func_name} end-to-end integration including network scenarios, timeouts, and error responses.",
        "provider_integration_test": f"Test {func_name} with provider-specific scenarios, API variations, and failure modes.",
        "validation_test": f"Test {func_name} with valid/invalid inputs, boundary conditions, and error scenarios.",
        "business_logic_test": f"Test {func_name} with various business scenarios including edge cases and error conditions.",
        "unit_test": f"Test {func_name} with comprehensive input scenarios and verify expected outputs.",
    }

    return descriptions.get(
        test_type,
        f"Create comprehensive tests for {func_name} covering various scenarios and edge cases.",
    )


def _is_critical_payment_class(class_name: str, content: str) -> bool:
    """
    Determine if a class is critical for payment processing.

    Args:
        class_name: Class name
        content: File content

    Returns:
        True if class is critical for payments
    """
    class_lower = class_name.lower()

    # Critical payment class patterns
    critical_patterns = [
        "payment",
        "transaction",
        "authorization",
        "capture",
        "refund",
        "chargeback",
        "provider",
        "gateway",
        "processor",
        "fraud",
        "risk",
        "security",
        "vault",
        "token",
        "card",
    ]

    return any(pattern in class_lower for pattern in critical_patterns)


async def _analyze_test_freshness(
    existing_tests: List[TestCoverageInfo],
    source_file: str,
    file_contents: FileContentsResult,
    result: TestCoverageResult,
) -> None:
    """
    Analyze if existing tests need updates based on source changes.

    Args:
        existing_tests: List of existing test files
        source_file: Source file being tested
        file_contents: File contents repository
        result: Result object to populate
    """
    source_content = file_contents.get_content_by_path(source_file)
    if not source_content:
        return

    for test_info in existing_tests:
        test_content = file_contents.get_content_by_path(test_info.test_file)
        if not test_content:
            continue

        # Look for hardcoded values that might need updating
        hardcoded_numbers = re.findall(r"\b\d{4,}\b", test_content)

        for number in hardcoded_numbers[:3]:  # Check first few numbers
            if number not in source_content:
                update_item = TestUpdateItem(
                    test_file=test_info.test_file,
                    reason=f"Test contains hardcoded value '{number}' that may need updating",
                    hardcoded_value=number,
                )
                result.tests_needing_updates.append(update_item)
                break

        # Check for outdated payment domain patterns
        if _has_outdated_payment_patterns(test_content, source_content):
            update_item = TestUpdateItem(
                test_file=test_info.test_file,
                reason="Test may use outdated payment patterns or API versions",
            )
            result.tests_needing_updates.append(update_item)


def _has_outdated_payment_patterns(test_content: str, source_content: str) -> bool:
    """
    Check if test content has outdated payment patterns.

    Args:
        test_content: Test file content
        source_content: Source file content

    Returns:
        True if outdated patterns detected
    """
    # Common outdated patterns in payment testing
    outdated_patterns = [
        r"mock\.patch\s*\(\s*['\"]urllib['\"]",  # Old HTTP mocking
        r"assert_called_with\s*\(\s*['\"]http://",  # HTTP instead of HTTPS
        r"\.json\(\)\.get\(",  # Old JSON parsing pattern
        r"time\.sleep\(",  # Synchronous waits in async code
    ]

    return any(re.search(pattern, test_content) for pattern in outdated_patterns)


def generate_change_summary_with_context(
    pr_details: PRDetails,
    file_changes: FileChangesResult,
    file_contents: FileContentsResult,
) -> ChangeSummary:
    """
    Generate intelligent change summary with payment domain expertise.

    Enhanced implementation of change summary generation,
    but using modern dataclasses and enhanced payment domain intelligence.

    Args:
        pr_details: PR metadata from Azure DevOps
        file_changes: Structured file changes result
        file_contents: Structured file contents result

    Returns:
        ChangeSummary with payment domain intelligence and risk assessment
    """
    # Extract file paths from structured data
    changed_files = []
    if file_changes.changes:
        changed_files = [change.item.path for change in file_changes.changes]

    # Identify domain areas with enhanced patterns
    domain_areas = []

    # Data processing patterns
    if any(
        "databricks" in path.lower() or "spark" in path.lower()
        for path in changed_files
    ):
        domain_areas.append("data processing")

    # Payment provider patterns (enhanced)
    payment_providers = ["adyen", "paypal", "stripe", "visa", "mastercard", "amex"]
    if any(
        provider in path.lower()
        for path in changed_files
        for provider in payment_providers
    ):
        domain_areas.append("payment provider integration")

    # Payment processing patterns
    payment_keywords = ["payment", "transaction", "settlement", "refund", "chargeback"]
    if any(
        keyword in path.lower()
        for path in changed_files
        for keyword in payment_keywords
    ):
        domain_areas.append("payment processing")

    # Testing patterns
    if any("test" in path.lower() for path in changed_files):
        domain_areas.append("testing")

    # Documentation patterns
    if any(path.endswith(".md") or "readme" in path.lower() for path in changed_files):
        domain_areas.append("documentation")

    # Configuration patterns
    if any(
        path.endswith((".json", ".yaml", ".yml", ".toml")) for path in changed_files
    ):
        domain_areas.append("configuration")

    # Look for critical patterns in file contents with enhanced detection
    critical_patterns = []
    financial_risk_patterns = {
        "chargeback": ["chargeback", "dispute", "liability_shift"],
        "financial_liability": ["liability", "financial_risk", "loss"],
        "provider_mapping": ["provider_mapping", "response_code", "status_mapping"],
        "fraud_detection": ["fraud", "risk_score", "suspicious"],
        "pci_compliance": ["pci", "card_data", "sensitive_data"],
        "settlement": ["settlement", "payout", "reconciliation"],
    }

    for file_content in file_contents.get_successful_files():
        content_lower = file_content.content.lower()
        for pattern_category, keywords in financial_risk_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                critical_patterns.append(pattern_category)

    # Remove duplicates and sort
    critical_patterns = sorted(set(critical_patterns))

    # Assess risk level based on critical patterns and domain areas
    risk_level = "low"
    high_risk_patterns = [
        "chargeback",
        "financial_liability",
        "pci_compliance",
        "fraud_detection",
    ]
    medium_risk_patterns = ["provider_mapping", "settlement", "payment_processing"]

    if any(pattern in critical_patterns for pattern in high_risk_patterns):
        risk_level = "high"
    elif any(pattern in critical_patterns for pattern in medium_risk_patterns):
        risk_level = "medium"
    elif "payment provider integration" in domain_areas:
        risk_level = "medium"

    return ChangeSummary(
        pr_title=pr_details.title,
        pr_description=pr_details.description,
        domain_areas=domain_areas,
        critical_patterns=critical_patterns,
        file_count=len(changed_files),
        risk_level=risk_level,
    )


@mcp.tool()
def get_pr_file_changes_with_context(
    context: AzureDevOpsPRContext,
) -> FileChangesResult:
    """
    Get the list of files changed in a pull request using Azure DevOps REST API.

    This tool retrieves comprehensive metadata about all files changed in a PR,
    including change types (add/edit/delete), file paths, and change statistics.
    Use this as a prerequisite before fetching actual file contents.

    Args:
        context: Established Azure DevOps PR context containing org, project, repo, pr_id.
                 Create context using azure_devops_establish_pr_context() first.

    Returns:
        FileChangesResult with:
        - success: Boolean indicating operation success
        - changes: List of FileChange objects with metadata
        - error: Error message if operation failed

    Example:
        # First establish PR context
        context = azure_devops_establish_pr_context(
            pr_url_or_id="https://dev.azure.com/org/project/_git/repo/pullrequest/123"
        )

        # Then get file changes
        changes = get_pr_file_changes_with_context(context)

        if changes.success:
            print(f"Found {len(changes.changes)} changed files")
            for change in changes.changes:
                print(f"{change.change_type}: {change.item.path}")
    """
    # Validate context before proceeding
    if not context or not isinstance(context, AzureDevOpsPRContext):
        return FileChangesResult(
            success=False,
            error=(
                "❌ Invalid PR context provided\n\n"
                "This tool requires a valid AzureDevOpsPRContext object.\n\n"
                "Expected workflow:\n"
                "1. Call azure_devops_establish_pr_context() first:\n"
                "   context = azure_devops_establish_pr_context(\n"
                "       pr_url_or_id='https://dev.azure.com/org/project/_git/repo/pullrequest/123'\n"
                "   )\n\n"
                "2. Pass the returned context to this tool:\n"
                "   changes = get_pr_file_changes_with_context(context)\n\n"
                f"Received type: {type(context).__name__}"
            ),
        )

    # Validate required fields
    missing_fields = []
    if not context.organization:
        missing_fields.append("organization")
    if not context.project:
        missing_fields.append("project")
    if not context.repository:
        missing_fields.append("repository")
    if not context.pr_id:
        missing_fields.append("pr_id")

    if missing_fields:
        return FileChangesResult(
            success=False,
            error=(
                f"❌ Invalid PR context: Missing required fields: {', '.join(missing_fields)}\n\n"
                "The PR context is incomplete. This usually means:\n"
                "1. The PR URL parsing failed\n"
                "2. The context was manually constructed incorrectly\n\n"
                "Solution: Use azure_devops_establish_pr_context() to create valid context:\n"
                "   context = azure_devops_establish_pr_context(\n"
                "       pr_url_or_id='https://dev.azure.com/org/project/_git/repo/pullrequest/123'\n"
                "   )\n\n"
                f"Current context values:\n"
                f"  organization: {context.organization or 'MISSING'}\n"
                f"  project: {context.project or 'MISSING'}\n"
                f"  repository: {context.repository or 'MISSING'}\n"
                f"  pr_id: {context.pr_id or 'MISSING'}"
            ),
        )

    try:
        # Use context values instead of parameters
        org_url = f"https://dev.azure.com/{context.organization}"
        project = context.project
        repository = context.repository
        pr_id = context.pr_id

        # Extract organization name from URL for route parameters
        org_name = context.organization

        # First, get the list of iterations for this PR using az devops invoke
        iterations_result = subprocess.run(
            [
                "az",
                "devops",
                "invoke",
                "--area",
                "git",
                "--resource",
                "pullRequestIterations",
                "--route-parameters",
                f"organization={org_name}",
                f"project={project}",
                f"repositoryId={repository}",
                f"pullRequestId={pr_id}",
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if iterations_result.returncode != 0:
            return FileChangesResult(
                success=False,
                error=f"Failed to get PR iterations: {iterations_result.stderr.strip()}\n\n"
                "This usually means:\n"
                "1. Invalid PR ID or PR doesn't exist\n"
                "2. Insufficient Azure DevOps permissions\n"
                "3. Azure CLI not authenticated\n"
                "4. Incorrect organization/project/repository parameters\n\n"
                f"Attempted PR: {pr_id} in {org_url}/{project}/{repository}",
            )

        try:
            iterations_data = json.loads(iterations_result.stdout)
        except json.JSONDecodeError:
            return FileChangesResult(
                success=False,
                error=f"Invalid JSON response from iterations API: {iterations_result.stdout[:200]}...",
            )

        # Extract iterations from response
        if isinstance(iterations_data, dict) and "value" in iterations_data:
            iterations = iterations_data["value"]
        elif isinstance(iterations_data, list):
            iterations = iterations_data
        else:
            return FileChangesResult(
                success=False,
                error="Unexpected iterations response format from API.",
            )

        if not iterations:
            return FileChangesResult(
                success=False,
                error="No iterations found for this PR. This may indicate an empty or invalid PR.",
            )

        # Get the latest iteration (highest ID)
        latest_iteration = max(iterations, key=lambda x: x.get("id", 0))
        iteration_id = latest_iteration.get("id")

        if iteration_id is None:
            return FileChangesResult(
                success=False,
                error="Could not determine latest iteration ID from API response.",
            )

        # Now get the file changes for the latest iteration using az devops invoke
        changes_result = subprocess.run(
            [
                "az",
                "devops",
                "invoke",
                "--area",
                "git",
                "--resource",
                "pullRequestIterationChanges",
                "--route-parameters",
                f"organization={org_name}",
                f"project={project}",
                f"repositoryId={repository}",
                f"pullRequestId={pr_id}",
                f"iterationId={iteration_id}",
                "--org",
                org_url,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if changes_result.returncode != 0:
            return FileChangesResult(
                success=False,
                error=f"Failed to get PR file changes: {changes_result.stderr.strip()}\n\n"
                f"Iteration ID: {iteration_id}\n"
                f"This may indicate API permissions issues or invalid iteration.",
            )

        try:
            changes_data = json.loads(changes_result.stdout)
        except json.JSONDecodeError:
            return FileChangesResult(
                success=False,
                error=f"Invalid JSON response from changes API: {changes_result.stdout[:200]}...",
            )

        # Extract file changes from Azure DevOps API response
        changes = []
        if isinstance(changes_data, dict) and "changeEntries" in changes_data:
            api_changes = changes_data["changeEntries"]
        else:
            return FileChangesResult(
                success=False,
                error="Unexpected changes response format from API.",
            )

        for change in api_changes:
            if isinstance(change, dict) and "item" in change:
                item = change["item"]
                path = item.get("path", "")
                change_type = change.get("changeType", "edit")

                # Normalize change type to match expected format
                if change_type in ["add", "delete", "edit", "rename"]:
                    normalized_type = change_type
                else:
                    normalized_type = "edit"  # Default fallback

                changes.append(
                    FileChange(
                        item=FileChangeItem(path=path), change_type=normalized_type
                    )
                )

        # Success! Now provide guidance for the next step in the workflow
        success_message = None
        if changes:
            success_message = (
                f"✅ Successfully retrieved {len(changes)} file changes from PR #{context.pr_id}.\n\n"
                f"📋 Next step in workflow: Call get_file_contents_with_context() to fetch actual file contents:\n"
                f"   - Pass this FileChangesResult as the file_changes parameter\n"
                f"   - Pass the same AzureDevOpsPRContext as the context parameter\n"
                f"   - Optionally set context_depth ('minimal', 'standard', or 'comprehensive')\n\n"
                f"Example:\n"
                f"   contents = await get_file_contents_with_context(\n"
                f"       file_changes=file_changes_result,\n"
                f"       context=pr_context,\n"
                f"       context_depth='standard'\n"
                f"   )"
            )

        return FileChangesResult(
            success=True,
            changes=changes,
            error=success_message,  # Using error field for workflow guidance (doesn't indicate failure)
        )

    except Exception as e:
        return FileChangesResult(
            success=False, error=f"Failed to retrieve file changes: {str(e)}"
        )


@mcp.tool()
async def get_file_contents_with_context(
    file_changes: FileChangesResult,
    context: AzureDevOpsPRContext,
    context_depth: str = "standard",
) -> FileContentsResult:
    """
    Retrieve actual file contents from a pull request for code review analysis.

    This tool fetches the actual source code contents of files changed in a PR,
    enabling AI agents to read and analyze the code being reviewed. This is the
    missing piece that allows agents to perform actual code analysis rather than
    just seeing file names.

    Enhanced features:
    - Fetches actual file contents via Azure DevOps REST API
    - Type-safe input/output with dataclasses
    - Performance optimizations for different context depths
    - Graceful fallback from API to local files
    - Comprehensive error tracking

    Args:
        file_changes: Result from get_pr_file_changes_with_context containing file metadata
        context: Established Azure DevOps PR context (from azure_devops_establish_pr_context)
        context_depth: Analysis depth controlling which files to fetch:
            - "minimal": Skip .json, .xml, .yaml, .lock, .log files
            - "standard": Skip .lock, .log, .tmp, .pyc, .bin files
            - "comprehensive": Fetch all files

    Returns:
        FileContentsResult with:
        - success: Boolean indicating operation success
        - files: List of FileContent objects with actual code
        - skipped_files: Files skipped based on context_depth
        - error_files: Files that couldn't be retrieved
        - error: Overall error message if operation failed

    Example:
        # Step 1: Establish PR context
        context = azure_devops_establish_pr_context(
            pr_url_or_id="https://dev.azure.com/org/project/_git/repo/pullrequest/123"
        )

        # Step 2: Get file changes metadata
        changes = get_pr_file_changes_with_context(context)

        # Step 3: Fetch actual file contents for analysis
        contents = await get_file_contents_with_context(
            file_changes=changes,
            context=context,
            context_depth="standard"
        )

        if contents.success:
            for file in contents.files:
                print(f"Analyzing {file.path} ({file.size_bytes} bytes)")
                print(file.content[:100])  # First 100 chars of actual code
    """
    # Validate inputs with helpful error messages
    if not context or not isinstance(context, AzureDevOpsPRContext):
        return FileContentsResult(
            success=False,
            error=(
                "❌ Invalid PR context provided\n\n"
                "This tool requires a valid AzureDevOpsPRContext object.\n\n"
                "Complete workflow:\n"
                "1. context = azure_devops_establish_pr_context(pr_url='...')\n"
                "2. changes = get_pr_file_changes_with_context(context)\n"
                "3. contents = get_file_contents_with_context(changes, context)  ← YOU ARE HERE\n\n"
                f"Received context type: {type(context).__name__}"
            ),
        )

    if not file_changes or not isinstance(file_changes, FileChangesResult):
        return FileContentsResult(
            success=False,
            error=(
                "❌ Invalid file changes provided\n\n"
                "This tool requires a FileChangesResult from get_pr_file_changes_with_context().\n\n"
                "Complete workflow:\n"
                "1. context = azure_devops_establish_pr_context(pr_url='...')\n"
                "2. changes = get_pr_file_changes_with_context(context)  ← CALL THIS FIRST\n"
                "3. contents = get_file_contents_with_context(changes, context)\n\n"
                f"Received file_changes type: {type(file_changes).__name__}"
            ),
        )

    if not file_changes.success or not file_changes.changes:
        return FileContentsResult(
            success=False,
            error=(
                "❌ File changes result indicates failure or no files found\n\n"
                f"File changes success: {file_changes.success}\n"
                f"Number of changes: {len(file_changes.changes) if file_changes.changes else 0}\n"
                f"Error from previous step: {file_changes.error or 'None'}\n\n"
                "This usually means:\n"
                "1. The PR has no file changes (empty PR)\n"
                "2. The previous tool (get_pr_file_changes_with_context) failed\n"
                "3. You're working with an invalid or merged PR\n\n"
                "Solution: Check the file_changes object for errors before calling this tool."
            ),
        )

    result = FileContentsResult(success=True)
    org_url = f"https://dev.azure.com/{context.organization}"
    org_name = context.organization

    # CRITICAL: For new files (change_type="add"), we need to fetch from the source branch
    # Get PR details to know the source branch/commit
    pr_details = None
    source_branch = None
    source_commit = None
    pr_is_completed = False

    try:
        pr_details = _get_pr_details_with_context(context)
        if pr_details:
            # Check if PR is completed (merged and potentially source branch deleted)
            pr_is_completed = (
                pr_details.status and pr_details.status.lower() == "completed"
            )

            if pr_is_completed:
                # For completed PRs, use the merge commit (changes are in target branch)
                # Source branch may be deleted, so we can't fetch from it
                if pr_details.last_merge_commit:
                    source_commit = pr_details.last_merge_commit
                elif pr_details.last_merge_source_commit:
                    # Fallback to last source commit if merge commit not available
                    source_commit = pr_details.last_merge_source_commit
            else:
                # For active PRs, prefer source branch (changes not yet merged)
                if pr_details.source_ref_name:
                    # sourceRefName format: "refs/heads/feature-branch" -> extract "feature-branch"
                    source_branch = pr_details.source_ref_name.replace(
                        "refs/heads/", ""
                    )

                # Also get the source commit as a fallback
                if pr_details.last_merge_source_commit:
                    source_commit = pr_details.last_merge_source_commit
    except Exception:
        # If we can't get PR details, continue without source branch info
        # This will cause new files to fail, but that's better than crashing
        pass

    for change in file_changes.changes:
        file_path = change.item.path
        if not file_path:
            continue

        # Performance optimization: Skip certain file types for standard depth
        if context_depth == "standard" and any(
            file_path.endswith(ext) for ext in [".lock", ".log", ".tmp", ".pyc", ".bin"]
        ):
            result.skipped_files.append(file_path)
            continue

        # Additional performance optimization for minimal depth
        if context_depth == "minimal" and any(
            file_path.endswith(ext)
            for ext in [".json", ".xml", ".yaml", ".yml", ".lock", ".log", ".tmp"]
        ):
            result.skipped_files.append(file_path)
            continue

        try:
            # Primary: Use Azure DevOps API for cross-repository access
            # CRITICAL: Must include includeContent=true to get actual file content
            # Without this, API only returns metadata (objectId, url) but no content field
            #
            # CRITICAL: For new files (change_type="add"), must fetch from source branch
            # New files don't exist in target branch yet, so we need to specify the version

            # Build query parameters - start with includeContent=true
            query_params = "includeContent=true"

            # CRITICAL: For both new AND edited files, fetch the correct version with PR changes
            # - "add" files: Don't exist in target branch yet (before merge)
            # - "edit" files: Need the NEW version with changes, not the old target branch version
            # - "delete" files: Fetch from target branch (the version before deletion)
            #
            # Strategy depends on PR status:
            # - Active PR: Fetch from source branch (changes not yet merged)
            # - Completed PR: Fetch from merge commit (source branch may be deleted)
            if change.change_type in ("add", "edit"):
                # Prefer commit ID (more reliable, especially for completed PRs)
                if source_commit:
                    # versionDescriptor format for commit: versionType=commit&version=commitId
                    query_params += f"&versionDescriptor.versionType=commit&versionDescriptor.version={source_commit}"
                elif source_branch:
                    # versionDescriptor format for branch: versionType=branch&version=branch-name
                    # Only works for active PRs where source branch still exists
                    query_params += f"&versionDescriptor.versionType=branch&versionDescriptor.version={source_branch}"
                # If neither is available, proceed without versionDescriptor
                # This may fail for "add" files but will work for "edit" files in some cases

            # Build complete command
            cmd = [
                "az",
                "devops",
                "invoke",
                "--area",
                "git",
                "--resource",
                "items",
                "--route-parameters",
                f"organization={org_name}",
                f"project={context.project}",
                f"repositoryId={context.repository}",
                f"path={file_path}",
                "--query-parameters",
                query_params,
                "--org",
                org_url,
                "--api-version",
                "6.0",
                "--output",
                "json",
            ]

            api_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if api_result.returncode == 0:
                try:
                    file_data = json.loads(api_result.stdout)
                    # Azure DevOps Items API with includeContent=true returns:
                    # { "objectId": "...", "gitObjectType": "blob", "content": "base64_encoded_content", ... }
                    # The content field contains the actual file content
                    if isinstance(file_data, dict) and "content" in file_data:
                        content = file_data["content"]
                    elif isinstance(file_data, str):
                        content = file_data
                    else:
                        # No content field - this shouldn't happen with includeContent=true
                        # Track as error instead of silently returning metadata
                        result.error_files.append(file_path)
                        continue

                    result.files.append(
                        FileContent(
                            path=file_path,
                            content=content,
                            size_bytes=len(content.encode("utf-8")),
                            is_binary=False,
                        )
                    )
                    continue
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    content = api_result.stdout
                    result.files.append(
                        FileContent(
                            path=file_path,
                            content=content,
                            size_bytes=len(content.encode("utf-8")),
                            is_binary=False,
                        )
                    )
                    continue

            # Fallback: Try local file access for development scenarios
            try:
                local_path = file_path.lstrip("/")
                # Assume we're in the repository root for local fallback
                with open(local_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    result.files.append(
                        FileContent(
                            path=file_path,
                            content=content,
                            size_bytes=len(content.encode("utf-8")),
                            is_binary=False,
                        )
                    )
            except (FileNotFoundError, UnicodeDecodeError, PermissionError):
                # File couldn't be read - track but don't fail the whole operation
                result.error_files.append(file_path)

        except Exception:
            # Individual file errors shouldn't fail the whole operation
            result.error_files.append(file_path)

    # Add workflow guidance message to the result
    success_summary = []
    if result.files:
        success_summary.append(
            f"✅ Successfully retrieved contents for {len(result.files)} files from PR #{context.pr_id}"
        )
    if result.skipped_files:
        success_summary.append(
            f"⏩ Skipped {len(result.skipped_files)} files based on context_depth='{context_depth}'"
        )
    if result.error_files:
        success_summary.append(
            f"⚠️  Failed to retrieve {len(result.error_files)} files (see error_files list)"
        )

    if success_summary:
        result.error = (
            "\n".join(success_summary) + "\n\n"
            "📋 Next steps in workflow:\n"
            "1. Use get_code_analysis_context() to get analysis guidelines and domain context\n"
            "2. Use get_code_quality_signals() to analyze code quality for the retrieved files\n"
            "3. Generate review comments based on the analysis\n"
            "4. Use post_ai_comments_by_pr_url() to post comments (or dry_run=True to preview)\n\n"
            "Example:\n"
            "   analysis_context = get_code_analysis_context(pr_context=pr_context)\n"
            "   quality_signals = get_code_quality_signals(file_paths=[f.path for f in contents.files])\n"
            "   # Generate comments based on analysis_context and quality_signals\n"
            "   post_result = post_ai_comments_by_pr_url(\n"
            "       pr_url=pr_context.pr_url,\n"
            "       comments=generated_comments,\n"
            "       dry_run=True\n"
            "   )"
        )

    return result


async def _get_pr_file_contents_for_analysis(
    pr_id: int, working_directory: Optional[str] = None
) -> PRCodeContextResult:
    """
    Enhanced bridge function using adapted legacy capabilities.

    This provides the same interface as the old get_pr_code_context function
    but uses the new azure_devops_establish_pr_context approach combined with
    adapted legacy functions for comprehensive analysis.

    Enhanced capabilities:
    - Sophisticated Azure DevOps API integration for file changes
    - Proper error handling with detailed troubleshooting guidance
    - Real file change data (not just stubs)
    - Foundation for adding more legacy analysis functions
    """
    try:
        # Establish PR context using new architecture
        context = azure_devops_establish_pr_context(
            pr_url_or_id=str(pr_id), working_directory=working_directory
        )

        # Use adapted legacy function for sophisticated file change analysis
        file_changes = get_pr_file_changes_with_context(context)
        if not file_changes.success:
            return PRCodeContextResult(
                success=False,
                error=file_changes.error or "Failed to get PR file changes",
                file_contents={},
            )

        # Enhanced: We now have actual file change data and can get real file contents
        file_contents_result = await get_file_contents_with_context(
            file_changes, context, context_depth="standard"
        )

        # Convert the file contents result to dictionary format for existing interface compatibility
        file_contents = {}
        if file_contents_result.success:
            for file_content in file_contents_result.files:
                if (
                    file_content.error is None
                ):  # Only include successfully retrieved files
                    file_contents[file_content.path] = file_content.content

        # Generate enhanced change summary using our modern implementation
        if file_contents_result.success and file_changes.changes:
            # Create PR details for change summary analysis
            pr_details = PRDetails(
                pull_request_id=context.pr_id,
                title=f"Enhanced Analysis PR #{context.pr_id}",
                description="Enhanced PR analysis using adapted legacy functions for comprehensive file change analysis.",
                source_ref_name=f"feature/enhanced-branch-{context.pr_id}",
                target_ref_name="main",
                status="Active",
                author="enhanced-analysis@microsoft.com",
                created_date="2024-01-01T00:00:00Z",
            )

            change_summary = generate_change_summary_with_context(
                pr_details=pr_details,
                file_changes=file_changes,
                file_contents=file_contents_result,
            )

            # Create comprehensive analysis summary
            summary_info = [
                "# Enhanced analysis with modern implementation functions",
                "",
                "## Change Summary",
                f"**PR Title**: {change_summary.pr_title}",
                f"**Risk Level**: {change_summary.risk_level.upper()}",
                f"**Files Changed**: {change_summary.file_count}",
                f"**Domain Areas**: {', '.join(change_summary.domain_areas)}",
                "",
                "### Description",
                change_summary.pr_description or "No description provided",
                "",
            ]

            # Add critical patterns if any
            if change_summary.critical_patterns:
                summary_info.extend(
                    [
                        "### Critical Patterns Detected",
                    ]
                )
                for pattern in change_summary.critical_patterns:
                    summary_info.append(f"- {pattern}")
                summary_info.append("")

            # Add formatted summary
            summary_info.extend(
                [
                    "### Summary String",
                    change_summary.to_summary_string(),
                    "",
                ]
            )

            # Add technical details
            summary_info.extend(
                [
                    "",
                    "## Technical Details",
                    f"- **Found**: {len(file_changes.changes)} file changes",
                    f"- **Retrieved**: {len(file_contents)} file contents",
                    f"- **Skipped**: {len(file_contents_result.skipped_files)} files for performance",
                    f"- **Failed**: {len(file_contents_result.error_files)} files",
                    f"- **Context**: {context.organization}/{context.project}/{context.repository}",
                ]
            )

            file_contents["_analysis_summary.md"] = "\n".join(summary_info)
        else:
            # Fallback for cases with no changes
            summary_info = [
                "# Enhanced analysis with modern implementation functions",
                f"# Found {len(file_changes.changes) if file_changes.changes else 0} file changes",
                f"# Retrieved {len(file_contents)} file contents",
                f"# Context: {context.organization}/{context.project}/{context.repository}",
            ]
            file_contents["_analysis_summary.md"] = "\n".join(summary_info)

        # Create proper PR details using context information
        pr_details = PRDetails(
            pull_request_id=context.pr_id,
            title=f"Enhanced Analysis PR #{context.pr_id}",
            description="Enhanced PR analysis using adapted legacy functions for comprehensive file change analysis.",
            source_ref_name=f"feature/enhanced-branch-{context.pr_id}",
            target_ref_name="main",
            status="Active",
            author="enhanced-analysis@microsoft.com",
            created_date="2024-01-01T00:00:00Z",
        )

        return PRCodeContextResult(
            success=True, file_contents=file_contents, pr_details=pr_details, error=None
        )

    except Exception as e:
        return PRCodeContextResult(
            success=False,
            error=f"Failed to establish PR context: {str(e)}",
            file_contents=None,
        )
