"""
Code Quality Signal Detection

Detects and classifies quality signals from static analysis, testing, and code patterns
to enable AI-driven quality assessment and recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import re
import os
import asyncio

from pdp_dev_mcp.mcp_instance import mcp


class SeverityLevel(Enum):
    """Quality signal severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalSource(Enum):
    """Source of quality signals."""

    STATIC_ANALYSIS = "static_analysis"
    CODE_PATTERNS = "code_patterns"
    TESTING_PATTERNS = "testing_patterns"
    SECURITY_PATTERNS = "security_patterns"
    PERFORMANCE_PATTERNS = "performance_patterns"
    DOMAIN_PATTERNS = "domain_patterns"


@dataclass
class QualitySignal:
    """
    Individual quality signal detected in code.

    Represents specific findings that AI can reason about for quality assessment.
    """

    signal_id: str
    source: SignalSource
    category: str
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    business_impact: Optional[str] = None
    technical_debt_score: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualitySignalCategories:
    """
    Categories for organizing quality signals with hybrid classification.

    Enables both standard and novel categorization based on discovered patterns.
    """

    standard_categories: List[str] = field(
        default_factory=lambda: [
            "code_smells",
            "security_vulnerabilities",
            "performance_issues",
            "maintainability_concerns",
            "testing_gaps",
            "documentation_issues",
            "domain_violations",
        ]
    )
    detected_novel_categories: List[str] = field(default_factory=list)
    category_descriptions: Dict[str, str] = field(default_factory=dict)
    allow_novel_categories: bool = True


@dataclass
class CodeQualityReport:
    """
    Comprehensive code quality signals report for AI analysis.

    Provides structured quality intelligence that enables AI reasoning
    about code quality, priorities, and recommendations.
    """

    file_paths: List[str]
    total_signals: int
    signals_by_severity: Dict[str, int]
    signals_by_category: Dict[str, int]
    quality_signals: List[QualitySignal]
    signal_categories: QualitySignalCategories
    overall_quality_score: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    domain_context: Dict[str, Any] = field(default_factory=dict)


@mcp.tool()
async def get_code_quality_signals(
    file_paths: List[str],
    include_patterns: Optional[List[str]] = None,
    severity_threshold: SeverityLevel = SeverityLevel.INFO,
    enable_domain_detection: bool = True,
) -> CodeQualityReport:
    """
    Detect and analyze code quality signals for AI-driven assessment.

    Combines static analysis, pattern detection, and domain-specific rules
    to provide comprehensive quality intelligence that enables AI reasoning.

    Args:
        file_paths: List of file paths to analyze
        include_patterns: Optional patterns to focus analysis (e.g., ["security", "performance"])
        severity_threshold: Minimum severity level to include
        enable_domain_detection: Whether to apply payment domain-specific detection

    Returns:
        CodeQualityReport with structured quality signals for AI analysis
    """
    all_signals = []

    # Collect signals from different sources concurrently
    async def analyze_single_file(file_path: str) -> List[QualitySignal]:
        """Analyze a single file and return all quality signals."""
        if not os.path.exists(file_path):
            return []

        file_signals = []

        # Run all analysis types for this file (keeping internal functions sync for now)
        file_signals.extend(_detect_static_analysis_signals(file_path))
        file_signals.extend(_detect_code_pattern_signals(file_path))
        file_signals.extend(_detect_security_pattern_signals(file_path))
        file_signals.extend(_detect_performance_pattern_signals(file_path))
        file_signals.extend(_detect_testing_pattern_signals(file_path))

        # Domain-specific analysis (payment processing)
        if enable_domain_detection:
            file_signals.extend(_detect_domain_pattern_signals(file_path))

        return file_signals

    # Process all files concurrently - this is where we get the major performance gain
    tasks = [analyze_single_file(file_path) for file_path in file_paths]
    file_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect all signals from concurrent results
    for result in file_results:
        if isinstance(result, list):
            all_signals.extend(result)
        # Skip exceptions and continue with other files

    # Filter by severity threshold
    filtered_signals = [
        signal
        for signal in all_signals
        if _severity_meets_threshold(signal.severity, severity_threshold)
    ]

    # Filter by include patterns if specified
    if include_patterns:
        filtered_signals = [
            signal
            for signal in filtered_signals
            if any(
                pattern.lower() in signal.category.lower()
                for pattern in include_patterns
            )
        ]

    # Build signal categories with hybrid classification
    signal_categories = _build_signal_categories(filtered_signals)

    # Calculate metrics
    signals_by_severity = _calculate_severity_distribution(filtered_signals)
    signals_by_category = _calculate_category_distribution(filtered_signals)

    # Generate AI-enabling recommendations
    recommendations = _generate_quality_recommendations(filtered_signals)

    # Calculate overall quality score
    quality_score = _calculate_quality_score(filtered_signals)

    # Build domain context
    domain_context = _build_domain_context(filtered_signals, file_paths)

    return CodeQualityReport(
        file_paths=file_paths,
        total_signals=len(filtered_signals),
        signals_by_severity=signals_by_severity,
        signals_by_category=signals_by_category,
        quality_signals=filtered_signals,
        signal_categories=signal_categories,
        overall_quality_score=quality_score,
        recommendations=recommendations,
        domain_context=domain_context,
    )


def _detect_static_analysis_signals(file_path: str) -> List[QualitySignal]:
    """Detect quality signals from static analysis patterns."""
    signals = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except (IOError, UnicodeDecodeError):
        return signals

    # Python-specific patterns
    if file_path.endswith(".py"):
        signals.extend(_detect_python_static_patterns(file_path, content, lines))

    # General patterns for all files
    signals.extend(_detect_general_static_patterns(file_path, content, lines))

    return signals


def _detect_python_static_patterns(
    file_path: str, content: str, lines: List[str]
) -> List[QualitySignal]:
    """Detect Python-specific static analysis patterns."""
    signals = []

    # Long function detection
    current_function = None
    function_start = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Function definition
        if stripped.startswith("def ") and ":" in stripped:
            if current_function and (i - function_start) > 50:
                signals.append(
                    QualitySignal(
                        signal_id=f"long_function_{function_start}",
                        source=SignalSource.STATIC_ANALYSIS,
                        category="maintainability_concerns",
                        severity=SeverityLevel.MEDIUM,
                        title="Long Function Detected",
                        description=f"Function '{current_function}' is {i - function_start} lines long",
                        file_path=file_path,
                        line_number=function_start,
                        recommendation="Consider breaking this function into smaller, more focused functions",
                        business_impact="Reduces code maintainability and increases debugging complexity",
                    )
                )

            current_function = stripped.split("(")[0].replace("def ", "")
            function_start = i

    # Check the last function if it exists
    if current_function and (len(lines) - function_start + 1) > 50:
        signals.append(
            QualitySignal(
                signal_id=f"long_function_{function_start}",
                source=SignalSource.STATIC_ANALYSIS,
                category="maintainability_concerns",
                severity=SeverityLevel.MEDIUM,
                title="Long Function Detected",
                description=f"Function '{current_function}' is {len(lines) - function_start + 1} lines long",
                file_path=file_path,
                line_number=function_start,
                recommendation="Consider breaking this function into smaller, more focused functions",
                business_impact="Reduces code maintainability and increases debugging complexity",
            )
        )

    # Complex conditionals
    for i, line in enumerate(lines, 1):
        if "if " in line and (" and " in line or " or " in line):
            condition_complexity = line.count(" and ") + line.count(" or ") + 1
            if condition_complexity > 3:
                signals.append(
                    QualitySignal(
                        signal_id=f"complex_conditional_{i}",
                        source=SignalSource.STATIC_ANALYSIS,
                        category="maintainability_concerns",
                        severity=SeverityLevel.LOW,
                        title="Complex Conditional Logic",
                        description=f"Conditional has {condition_complexity} logical operators",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation="Consider extracting complex conditions into well-named boolean variables or functions",
                    )
                )

    # TODO/FIXME comments
    for i, line in enumerate(lines, 1):
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            signals.append(
                QualitySignal(
                    signal_id=f"technical_debt_{i}",
                    source=SignalSource.STATIC_ANALYSIS,
                    category="technical_debt",
                    severity=SeverityLevel.LOW,
                    title="Technical Debt Marker",
                    description="Code contains technical debt markers",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line.strip(),
                    technical_debt_score=1,
                )
            )

    return signals


def _detect_general_static_patterns(
    file_path: str, content: str, lines: List[str]
) -> List[QualitySignal]:
    """Detect general static analysis patterns applicable to all file types."""
    signals = []

    # Large file detection
    if len(lines) > 500:
        signals.append(
            QualitySignal(
                signal_id="large_file",
                source=SignalSource.STATIC_ANALYSIS,
                category="maintainability_concerns",
                severity=SeverityLevel.MEDIUM,
                title="Large File Detected",
                description=f"File has {len(lines)} lines",
                file_path=file_path,
                recommendation="Consider breaking large files into smaller, more focused modules",
                business_impact="Large files are harder to maintain and understand",
            )
        )

    # Long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            signals.append(
                QualitySignal(
                    signal_id=f"long_line_{i}",
                    source=SignalSource.STATIC_ANALYSIS,
                    category="code_style",
                    severity=SeverityLevel.INFO,
                    title="Long Line",
                    description=f"Line exceeds 120 characters ({len(line)} chars)",
                    file_path=file_path,
                    line_number=i,
                    recommendation="Break long lines for better readability",
                )
            )

    return signals


def _detect_code_pattern_signals(file_path: str) -> List[QualitySignal]:
    """Detect quality signals from code patterns and structures."""
    signals = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except (IOError, UnicodeDecodeError):
        return signals

    if file_path.endswith(".py"):
        # Missing docstrings
        if "def " in content or "class " in content:
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if (
                    stripped.startswith("def ") or stripped.startswith("class ")
                ) and ":" in stripped:
                    # Check if next non-empty line is a docstring
                    next_line_idx = i
                    while (
                        next_line_idx < len(lines) and not lines[next_line_idx].strip()
                    ):
                        next_line_idx += 1

                    if (
                        next_line_idx >= len(lines)
                        or not lines[next_line_idx].strip().startswith('"""')
                        and not lines[next_line_idx].strip().startswith("'''")
                    ):
                        element_type = (
                            "function" if stripped.startswith("def ") else "class"
                        )
                        element_name = (
                            stripped.split("(")[0]
                            .split(":")[0]
                            .replace("def ", "")
                            .replace("class ", "")
                        )

                        signals.append(
                            QualitySignal(
                                signal_id=f"missing_docstring_{i}",
                                source=SignalSource.CODE_PATTERNS,
                                category="documentation_issues",
                                severity=SeverityLevel.LOW,
                                title=f"Missing {element_type.title()} Docstring",
                                description=f"{element_type.title()} '{element_name}' lacks documentation",
                                file_path=file_path,
                                line_number=i,
                                recommendation=f"Add docstring to document {element_type} purpose, parameters, and return value",
                            )
                        )

        # Magic numbers
        for i, line in enumerate(lines, 1):
            # Look for numeric literals that aren't 0, 1, or -1
            numbers = re.findall(r"\b\d{2,}\b", line)
            for number in numbers:
                if int(number) not in [0, 1, 100]:  # Common acceptable magic numbers
                    signals.append(
                        QualitySignal(
                            signal_id=f"magic_number_{i}_{number}",
                            source=SignalSource.CODE_PATTERNS,
                            category="maintainability_concerns",
                            severity=SeverityLevel.LOW,
                            title="Magic Number Detected",
                            description=f"Numeric literal '{number}' should be a named constant",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            recommendation="Replace magic numbers with named constants for better maintainability",
                        )
                    )

    return signals


def _detect_security_pattern_signals(file_path: str) -> List[QualitySignal]:
    """Detect security-related quality signals."""
    signals = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except (IOError, UnicodeDecodeError):
        return signals

    # Hardcoded credentials patterns
    credential_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded Token"),
        (r'DATABASE_PASSWORD\s*=\s*["\'][^"\']+["\']', "Hardcoded Database Password"),
        (r'API_KEY\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
    ]

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        for pattern, title in credential_patterns:
            if re.search(pattern, line_lower, re.IGNORECASE):
                signals.append(
                    QualitySignal(
                        signal_id=f"hardcoded_credential_{i}",
                        source=SignalSource.SECURITY_PATTERNS,
                        category="security_vulnerabilities",
                        severity=SeverityLevel.CRITICAL,
                        title=title,
                        description="Hardcoded credentials detected in source code",
                        file_path=file_path,
                        line_number=i,
                        recommendation="Use environment variables or secure credential management systems",
                        business_impact="CRITICAL: Exposes sensitive credentials in source code, violates PCI compliance",
                    )
                )

    # SQL injection patterns (basic detection)
    if file_path.endswith(".py"):
        for i, line in enumerate(lines, 1):
            if (
                ("execute(" in line or "query(" in line)
                and ('"' in line or "'" in line)
                and "%" in line
            ):
                signals.append(
                    QualitySignal(
                        signal_id=f"potential_sql_injection_{i}",
                        source=SignalSource.SECURITY_PATTERNS,
                        category="security_vulnerabilities",
                        severity=SeverityLevel.HIGH,
                        title="Potential SQL Injection Risk",
                        description="String formatting in SQL query may be vulnerable",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation="Use parameterized queries or ORM methods to prevent SQL injection",
                        business_impact="HIGH: SQL injection vulnerabilities can compromise data integrity",
                    )
                )

    return signals


def _detect_performance_pattern_signals(file_path: str) -> List[QualitySignal]:
    """Detect performance-related quality signals."""
    signals = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except (IOError, UnicodeDecodeError):
        return signals

    if file_path.endswith(".py"):
        # Nested loops detection
        loop_depth = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            if stripped.startswith("for ") or stripped.startswith("while "):
                loop_depth += 1
                if loop_depth > 2:
                    signals.append(
                        QualitySignal(
                            signal_id=f"nested_loops_{i}",
                            source=SignalSource.PERFORMANCE_PATTERNS,
                            category="performance_issues",
                            severity=SeverityLevel.MEDIUM,
                            title="Deeply Nested Loops",
                            description=f"Loop nesting depth of {loop_depth} detected",
                            file_path=file_path,
                            line_number=i,
                            recommendation="Consider algorithmic improvements or breaking into separate functions",
                            business_impact="May impact performance with large datasets",
                        )
                    )
            elif not stripped or indent <= loop_depth * 4:
                loop_depth = max(0, loop_depth - 1)

        # Inefficient string concatenation
        for i, line in enumerate(lines, 1):
            if "+=" in line and ("str(" in line or '"' in line or "'" in line):
                signals.append(
                    QualitySignal(
                        signal_id=f"string_concatenation_{i}",
                        source=SignalSource.PERFORMANCE_PATTERNS,
                        category="performance_issues",
                        severity=SeverityLevel.LOW,
                        title="Inefficient String Concatenation",
                        description="String concatenation in loop may be inefficient",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip(),
                        recommendation="Use join() for multiple string concatenations or f-strings for formatting",
                    )
                )

    return signals


def _detect_testing_pattern_signals(file_path: str) -> List[QualitySignal]:
    """Detect testing-related quality signals."""
    signals = []

    # Check if this is a test file
    is_test_file = (
        "test_" in os.path.basename(file_path)
        or file_path.endswith("_test.py")
        or "/test" in file_path.lower()
    )

    if not is_test_file:
        # Check if corresponding test file exists
        base_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)

        if file_path.endswith(".py"):
            # Look for test files
            test_patterns = [
                f"test_{base_name}",
                base_name.replace(".py", "_test.py"),
                f"tests/test_{base_name}",
                f"test/test_{base_name}",
            ]

            test_exists = False
            for pattern in test_patterns:
                test_path = os.path.join(dir_name, pattern)
                if os.path.exists(test_path):
                    test_exists = True
                    break

            if not test_exists:
                signals.append(
                    QualitySignal(
                        signal_id="missing_tests",
                        source=SignalSource.TESTING_PATTERNS,
                        category="testing_gaps",
                        severity=SeverityLevel.MEDIUM,
                        title="Missing Test Coverage",
                        description="No corresponding test file found",
                        file_path=file_path,
                        recommendation="Create comprehensive test coverage for this module",
                        business_impact="Lack of tests increases risk of regression bugs in production",
                    )
                )

    return signals


def _detect_domain_pattern_signals(file_path: str) -> List[QualitySignal]:
    """Detect payment domain-specific quality signals."""
    signals = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except (IOError, UnicodeDecodeError):
        return signals

    # Payment-specific patterns
    payment_keywords = [
        "payment",
        "transaction",
        "chargeback",
        "refund",
        "authorization",
        "settlement",
    ]

    if any(keyword in content.lower() for keyword in payment_keywords):
        # PCI compliance patterns
        pci_sensitive_patterns = [
            (
                r"\b\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4}\b",
                "Credit Card Number Pattern",
            ),
            (r"\bcvv\s*[:=]\s*\d{3,4}\b", "CVV Code Pattern"),
            (r"\bexpir[ye]\s*[:=]\s*\d{2}[/\-]\d{2,4}\b", "Expiration Date Pattern"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, title in pci_sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    signals.append(
                        QualitySignal(
                            signal_id=f"pci_violation_{i}",
                            source=SignalSource.DOMAIN_PATTERNS,
                            category="domain_violations",
                            severity=SeverityLevel.CRITICAL,
                            title=f"PCI Compliance Violation: {title}",
                            description="Sensitive payment data detected in source code",
                            file_path=file_path,
                            line_number=i,
                            recommendation="Remove sensitive payment data from source code immediately",
                            business_impact="CRITICAL: PCI compliance violation can result in fines and loss of payment processing privileges",
                        )
                    )

        # Missing error handling for payment operations
        for i, line in enumerate(lines, 1):
            if any(
                keyword in line.lower()
                for keyword in ["process_payment", "charge_card", "refund"]
            ):
                # Check if there's error handling nearby
                has_error_handling = False
                for j in range(max(0, i - 5), min(len(lines), i + 10)):
                    if any(
                        error_pattern in lines[j].lower()
                        for error_pattern in ["try:", "except", "catch", "error"]
                    ):
                        has_error_handling = True
                        break

                if not has_error_handling:
                    signals.append(
                        QualitySignal(
                            signal_id=f"missing_payment_error_handling_{i}",
                            source=SignalSource.DOMAIN_PATTERNS,
                            category="domain_violations",
                            severity=SeverityLevel.HIGH,
                            title="Missing Payment Error Handling",
                            description="Payment operation lacks proper error handling",
                            file_path=file_path,
                            line_number=i,
                            recommendation="Add comprehensive error handling for payment operations",
                            business_impact="Payment failures without proper error handling can lead to inconsistent financial state",
                        )
                    )

    return signals


def _severity_meets_threshold(
    signal_severity: SeverityLevel, threshold: SeverityLevel
) -> bool:
    """Check if signal severity meets the threshold."""
    severity_order = {
        SeverityLevel.INFO: 0,
        SeverityLevel.LOW: 1,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.HIGH: 3,
        SeverityLevel.CRITICAL: 4,
    }
    return severity_order[signal_severity] >= severity_order[threshold]


def _build_signal_categories(signals: List[QualitySignal]) -> QualitySignalCategories:
    """Build signal categories with hybrid classification."""
    detected_categories = set()
    standard_categories = [
        "code_smells",
        "security_vulnerabilities",
        "performance_issues",
        "maintainability_concerns",
        "testing_gaps",
        "documentation_issues",
        "domain_violations",
        "technical_debt",
        "code_style",
    ]

    for signal in signals:
        detected_categories.add(signal.category)

    novel_categories = [
        cat for cat in detected_categories if cat not in standard_categories
    ]

    category_descriptions = {
        "code_smells": "Code that works but indicates deeper problems in design or implementation",
        "security_vulnerabilities": "Security risks including hardcoded credentials, injection risks, and data exposure",
        "performance_issues": "Patterns that may negatively impact system performance or scalability",
        "maintainability_concerns": "Issues that make code harder to understand, modify, or maintain",
        "testing_gaps": "Missing or inadequate test coverage for critical functionality",
        "documentation_issues": "Missing or inadequate documentation for code components",
        "domain_violations": "Violations of payment domain-specific rules, compliance, or business logic",
        "technical_debt": "Accumulated shortcuts or temporary solutions that need future attention",
        "code_style": "Code formatting and style consistency issues",
    }

    return QualitySignalCategories(
        standard_categories=standard_categories,
        detected_novel_categories=novel_categories,
        category_descriptions=category_descriptions,
        allow_novel_categories=True,
    )


def _calculate_severity_distribution(signals: List[QualitySignal]) -> Dict[str, int]:
    """Calculate distribution of signals by severity."""
    distribution = {level.value: 0 for level in SeverityLevel}
    for signal in signals:
        distribution[signal.severity.value] += 1
    return distribution


def _calculate_category_distribution(signals: List[QualitySignal]) -> Dict[str, int]:
    """Calculate distribution of signals by category."""
    distribution = {}
    for signal in signals:
        distribution[signal.category] = distribution.get(signal.category, 0) + 1
    return distribution


def _generate_quality_recommendations(signals: List[QualitySignal]) -> List[str]:
    """Generate AI-enabling quality recommendations based on detected signals."""
    recommendations = []

    # Group by category for strategic recommendations
    by_category = {}
    for signal in signals:
        if signal.category not in by_category:
            by_category[signal.category] = []
        by_category[signal.category].append(signal)

    # Security-first recommendations
    if "security_vulnerabilities" in by_category:
        critical_security = [
            s
            for s in by_category["security_vulnerabilities"]
            if s.severity == SeverityLevel.CRITICAL
        ]
        if critical_security:
            recommendations.append(
                "IMMEDIATE ACTION REQUIRED: Critical security vulnerabilities detected. Address hardcoded credentials and PCI compliance violations before deployment."
            )

    # Domain-specific recommendations
    if "domain_violations" in by_category:
        recommendations.append(
            "Payment domain violations detected. Review PCI compliance requirements and ensure proper error handling for financial operations."
        )

    # Technical debt recommendations
    if "technical_debt" in by_category:
        debt_count = len(by_category["technical_debt"])
        recommendations.append(
            f"Technical debt identified in {debt_count} locations. Consider scheduling cleanup sprint to address TODO/FIXME items."
        )

    # Performance recommendations
    if "performance_issues" in by_category:
        recommendations.append(
            "Performance patterns detected that may impact scalability. Review algorithmic complexity and string handling optimizations."
        )

    # Testing recommendations
    if "testing_gaps" in by_category:
        recommendations.append(
            "Test coverage gaps identified. Prioritize test creation for payment processing logic and security-critical components."
        )

    return recommendations


def _calculate_quality_score(signals: List[QualitySignal]) -> float:
    """Calculate overall quality score based on signal severity and distribution."""
    if not signals:
        return 100.0

    # Weight by severity
    severity_weights = {
        SeverityLevel.INFO: 0.1,
        SeverityLevel.LOW: 0.5,
        SeverityLevel.MEDIUM: 2.0,
        SeverityLevel.HIGH: 5.0,
        SeverityLevel.CRITICAL: 10.0,
    }

    total_weight = sum(severity_weights[signal.severity] for signal in signals)

    # Base score of 100, subtract based on weighted issues
    quality_score = max(0.0, 100.0 - (total_weight * 2))

    return round(quality_score, 1)


def _build_domain_context(
    signals: List[QualitySignal], file_paths: List[str]
) -> Dict[str, Any]:
    """Build domain-specific context for payment processing analysis."""
    domain_signals = [s for s in signals if s.source == SignalSource.DOMAIN_PATTERNS]
    security_signals = [s for s in signals if s.category == "security_vulnerabilities"]

    # Check if payment domain is detected by file paths or content
    payment_detected = (
        any("payment" in path.lower() for path in file_paths)
        or len(domain_signals) > 0  # If domain signals found, payment content detected
    )

    return {
        "payment_domain_detected": payment_detected,
        "pci_compliance_issues": len(
            [s for s in domain_signals if "pci" in s.title.lower()]
        ),
        "security_critical_count": len(
            [s for s in security_signals if s.severity == SeverityLevel.CRITICAL]
        ),
        "domain_specific_recommendations": [
            s.recommendation for s in domain_signals if s.recommendation
        ],
    }
