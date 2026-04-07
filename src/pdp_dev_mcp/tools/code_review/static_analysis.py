"""
Domain knowledge analysis tool for AI-assisted code review.

Provides analysis of payment processing code against domain requirements,
compliance standards, and architectural constraints.
"""

import aiofiles
import asyncio
import os
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from pdp_dev_mcp.mcp_instance import mcp


@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement identified in code."""

    standard: str  # e.g., "PCI DSS", "PCI-3DS", "GDPR"
    requirement_id: str  # e.g., "3.4", "4.1"
    description: str
    severity: str  # "critical", "high", "medium", "low"
    affected_files: List[str]
    code_patterns: List[str]
    remediation_guidance: str


@dataclass
class DomainPattern:
    """Represents a payment processing pattern identified in code."""

    pattern_type: str  # e.g., "provider_integration", "error_handling", "retry_logic"
    pattern_name: str
    description: str
    files_found: List[str]
    confidence_score: float
    best_practice_alignment: str  # "good", "needs_improvement", "problematic"
    recommendations: List[str]


@dataclass
@dataclass
class ArchitecturalConstraint:
    """Represents an architectural constraint relevant to code changes."""

    constraint_type: str  # e.g., "data_flow", "security", "scalability"
    description: str
    affected_systems: List[str]
    risk_level: str  # "high", "medium", "low"
    validation_rules: List[str]
    violation_indicators: List[str]


@dataclass
class HistoricalIssue:
    """Represents a historical issue relevant to current code changes."""

    issue_type: str  # e.g., "payment_failure", "data_breach", "performance"
    description: str
    affected_components: List[str]
    root_cause: str
    resolution: str
    prevention_measures: List[str]
    relevance_score: float


@dataclass
class DomainKnowledgeAnalysisResult:
    """Complete domain knowledge analysis result."""

    success: bool
    domain_patterns: List[DomainPattern]
    compliance_requirements: List[ComplianceRequirement]
    architectural_constraints: List[ArchitecturalConstraint]
    historical_issues: List[HistoricalIssue]
    analysis_summary: str
    recommendations: List[str]
    risk_assessment: Dict[str, Any]


def _analyze_pci_compliance(
    file_paths: List[str], file_contents: Dict[str, str]
) -> List[ComplianceRequirement]:
    """Analyze files for PCI DSS compliance requirements."""
    requirements = []

    # PCI DSS patterns to look for
    sensitive_data_patterns = [
        r"card_number|cardnumber|pan|primary_account_number",
        r"cvv|cvc|security_code|card_verification",
        r"expiry|expiration.*date|exp_date",
        r"cardholder.*name|card_holder",
    ]

    storage_risk_patterns = [
        r"\.store\(|\.save\(|INSERT\s+INTO|UPDATE\s+.*SET",
        r"database|db|redis|cache|session",
        r"log|print|console\.log|echo",
    ]

    for file_path in file_paths:
        if file_path not in file_contents:
            continue

        content = file_contents[file_path].lower()

        # Check for sensitive data handling
        for pattern in sensitive_data_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Any handling of sensitive data triggers PCI compliance requirements
                requirements.append(
                    ComplianceRequirement(
                        standard="PCI DSS",
                        requirement_id="3.4",
                        description="Protect stored cardholder data - sensitive authentication data must not be stored",
                        severity="critical",
                        affected_files=[file_path],
                        code_patterns=[pattern],
                        remediation_guidance="Ensure cardholder data is properly encrypted and access is restricted",
                    )
                )

                # Check if this sensitive data is being stored or logged (additional violation)
                for storage_pattern in storage_risk_patterns:
                    if re.search(storage_pattern, content, re.IGNORECASE):
                        requirements.append(
                            ComplianceRequirement(
                                standard="PCI DSS",
                                requirement_id="3.1",
                                description="Never store sensitive authentication data after authorization",
                                severity="critical",
                                affected_files=[file_path],
                                code_patterns=[pattern, storage_pattern],
                                remediation_guidance="Remove storage of sensitive authentication data or implement proper encryption",
                            )
                        )
                        break

        # Check for unencrypted transmission patterns
        transmission_patterns = [
            r"http://|ftp://|smtp://",  # Unencrypted protocols
            r"email|mail|sms|chat",  # Insecure communication channels
        ]

        for pattern in transmission_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                requirements.append(
                    ComplianceRequirement(
                        standard="PCI DSS",
                        requirement_id="4.1",
                        description="Encrypt transmission of cardholder data across open, public networks",
                        severity="high",
                        affected_files=[file_path],
                        code_patterns=[pattern],
                        remediation_guidance="Use strong cryptography (TLS 1.2+) for all cardholder data transmission",
                    )
                )

    return requirements


def _analyze_provider_integration_patterns(
    file_paths: List[str], file_contents: Dict[str, str]
) -> List[DomainPattern]:
    """Analyze files for payment provider integration patterns."""
    patterns = []

    provider_indicators = {
        "adyen": r"adyen",
        "stripe": r"stripe",
        "paypal": r"paypal",
        "square": r"square",
    }

    integration_patterns = {
        "api_call": r"requests\.|http\.|fetch\(|axios\.",
        "response_handling": r"response\.|status_code|json\(\)",
        "error_handling": r"try:|except:|catch\(|error|exception",
        "retry_logic": r"retry|attempt|backoff|sleep",
        "webhook": r"webhook|callback|notification",
    }

    for file_path in file_paths:
        # First, try to detect provider from filename
        detected_provider = None
        for provider, pattern in provider_indicators.items():
            if re.search(pattern, file_path, re.IGNORECASE):
                detected_provider = provider
                break

        # If we have content, analyze it for patterns
        found_patterns = []
        if file_path in file_contents and file_contents[file_path]:
            content = file_contents[file_path]

            # Also check content for provider indicators
            if not detected_provider:
                for provider, pattern in provider_indicators.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        detected_provider = provider
                        break

            # Analyze integration patterns in content
            for pattern_name, pattern_regex in integration_patterns.items():
                if re.search(pattern_regex, content, re.IGNORECASE):
                    found_patterns.append(pattern_name)

        # If we detected a provider (from filename or content), create patterns
        if detected_provider:
            confidence = (
                len(found_patterns) / len(integration_patterns)
                if found_patterns
                else 0.3
            )  # Base confidence from filename

            # Add the main integration pattern
            patterns.append(
                DomainPattern(
                    pattern_type="provider_integration",
                    pattern_name=f"{detected_provider}_integration",
                    description=f"Integration with {detected_provider.title()} payment provider - ensure proper response code standardization",
                    files_found=[file_path],
                    confidence_score=confidence,
                    best_practice_alignment="needs_improvement"
                    if confidence < 0.6
                    else "good",
                    recommendations=[
                        "Implement response code standardization patterns",
                        "Ensure proper error handling for all API calls",
                        "Implement retry logic with exponential backoff",
                        "Validate all response data before processing",
                        "Log integration events for monitoring",
                    ],
                )
            )

            # Also add anti-patterns to watch for
            patterns.append(
                DomainPattern(
                    pattern_type="anti-pattern",
                    pattern_name="provider_integration_antipatterns",
                    description="Common anti-patterns to avoid in payment provider integrations",
                    files_found=[file_path],
                    confidence_score=1.0,  # High confidence in anti-pattern guidance
                    best_practice_alignment="problematic",
                    recommendations=[
                        "Never store provider API keys in code or logs",
                        "Don't process payments synchronously without timeout handling",
                        "Avoid tight coupling between provider-specific logic and business logic",
                        "Don't ignore error responses from payment providers",
                        "Avoid hardcoding provider-specific response codes throughout the application",
                    ],
                )
            )

    return patterns


def _analyze_data_flow_architecture(
    files_content: Dict[str, str],
) -> List[ArchitecturalConstraint]:
    """Analyze architectural constraints for data flow layers."""
    constraints = []

    # Look for bronze/silver/gold architecture documentation
    for file_path, content in files_content.items():
        if "architecture" in file_path.lower() and (
            "bronze" in content.lower()
            or "silver" in content.lower()
            or "gold" in content.lower()
        ):
            # Extract layer-specific constraints
            if "never modify bronze layer" in content.lower():
                constraints.append(
                    ArchitecturalConstraint(
                        constraint_type="data_immutability",
                        description="Bronze layer data must never be modified after initial load",
                        affected_systems=["bronze_layer", "data_pipeline"],
                        risk_level="high",
                        validation_rules=[
                            "Check for direct bronze table modifications"
                        ],
                        violation_indicators=[
                            "UPDATE statements on bronze tables",
                            "Direct data modifications",
                        ],
                    )
                )

            if "silver layer must be reprocessable" in content.lower():
                constraints.append(
                    ArchitecturalConstraint(
                        constraint_type="reprocessability",
                        description="Silver layer transformations must be reprocessable from bronze",
                        affected_systems=["silver_layer", "data_pipeline"],
                        risk_level="high",
                        validation_rules=[
                            "Verify transformations are deterministic",
                            "Check bronze dependency preservation",
                        ],
                        violation_indicators=[
                            "Non-deterministic operations",
                            "Lost bronze references",
                        ],
                    )
                )

            if "gold layer calculations must be deterministic" in content.lower():
                constraints.append(
                    ArchitecturalConstraint(
                        constraint_type="deterministic_calculations",
                        description="Gold layer calculations must be deterministic and auditable",
                        affected_systems=["gold_layer", "analytics"],
                        risk_level="high",
                        validation_rules=[
                            "Verify calculation reproducibility",
                            "Check audit trail preservation",
                        ],
                        violation_indicators=[
                            "Random functions",
                            "Non-reproducible aggregations",
                        ],
                    )
                )

    # Analyze code for layer pattern compliance
    for file_path, content in files_content.items():
        if "/bronze/" in file_path and "transformation" in content.lower():
            constraints.append(
                ArchitecturalConstraint(
                    constraint_type="bronze_transformation_limit",
                    description="Bronze layer should only perform minimal transformations (data type conversions)",
                    affected_systems=["bronze_layer"],
                    risk_level="medium",
                    validation_rules=["Check transformation complexity"],
                    violation_indicators=["Complex business logic in bronze layer"],
                )
            )

        if "/silver/" in file_path and "standardize" in content.lower():
            if "bronze_source_id" in content or "source_record_id" in content:
                # Good pattern detected - preserving source reference
                pass
            else:
                constraints.append(
                    ArchitecturalConstraint(
                        constraint_type="source_traceability",
                        description="Silver layer transformations should preserve bronze source references",
                        affected_systems=["silver_layer"],
                        risk_level="medium",
                        validation_rules=["Check for bronze reference preservation"],
                        violation_indicators=[
                            "Missing source_record_id",
                            "Lost bronze traceability",
                        ],
                    )
                )

    return constraints


def _analyze_historical_issues(
    files_content: Dict[str, str], context_files: Optional[List[str]] = None
) -> List[HistoricalIssue]:
    """Analyze historical issues relevant to current code changes."""
    issues = []

    # Look for incident documentation and historical issue reports
    for file_path, content in files_content.items():
        if (
            "incident" in file_path.lower()
            or "issue" in file_path.lower()
            or "postmortem" in file_path.lower()
            or "provider" in file_path.lower()
            or "integration" in file_path.lower()
        ):
            # Parse incident reports for historical context
            lines = content.split("\n")
            current_issue = None

            for line in lines:
                line = line.strip()
                # Look for best practices sections first
                if "Best Practices" in line:
                    # Store current issue before starting best practices section
                    if current_issue:
                        issues.append(current_issue)
                        current_issue = None

                    # Create a solution-type issue for best practices
                    current_issue = HistoricalIssue(
                        issue_type="best practice solution",
                        description="Best practices learned from historical incidents",
                        affected_components=["payment_processing", "retry_logic"],
                        root_cause="Lessons learned from multiple incidents",
                        resolution="Implementation of best practices",
                        prevention_measures=[],
                        relevance_score=0.9,
                    )

                # Look for incident headers or provider-specific issue headers
                elif line.startswith("## Incident") or line.startswith("## Issue:"):
                    if current_issue:
                        issues.append(current_issue)

                    # Extract incident ID and description
                    if line.startswith("## Incident"):
                        incident_info = line.replace("## Incident", "").strip()
                    else:  # ## Issue: format
                        incident_info = line.replace("## Issue:", "").strip()

                    issue_type = "payment_failure"  # Default type
                    if "retry" in incident_info.lower():
                        issue_type = "retry_logic"
                    elif "outage" in incident_info.lower():
                        issue_type = "service_outage"
                    elif (
                        "security" in incident_info.lower()
                        or "breach" in incident_info.lower()
                    ):
                        issue_type = "security_incident"
                    elif (
                        "paypal" in incident_info.lower()
                        or "paypal" in file_path.lower()
                    ):
                        issue_type = "provider_specific"
                    elif (
                        "timezone" in incident_info.lower()
                        or "timestamp" in incident_info.lower()
                    ):
                        issue_type = "data_handling"

                    current_issue = HistoricalIssue(
                        issue_type=issue_type,
                        description=incident_info,
                        affected_components=[],
                        root_cause="",
                        resolution="",
                        prevention_measures=[],
                        relevance_score=0.8,  # Default relevance score
                    )

                elif current_issue:
                    # Parse incident details - handle both incident and provider doc formats
                    if line.startswith("**Issue**:") or line.startswith("**Problem**:"):
                        problem = (
                            line.replace("**Issue**:", "")
                            .replace("**Problem**:", "")
                            .strip()
                        )
                        # Append problem details to existing description rather than replacing it
                        if current_issue.description:
                            current_issue.description = (
                                f"{current_issue.description}: {problem}"
                            )
                        else:
                            current_issue.description = problem
                    elif line.startswith("**Root Cause**:"):
                        current_issue.root_cause = line.replace(
                            "**Root Cause**:", ""
                        ).strip()
                    elif line.startswith("**Solution**:") or line.startswith(
                        "**Workaround**:"
                    ):
                        solution = (
                            line.replace("**Solution**:", "")
                            .replace("**Workaround**:", "")
                            .strip()
                        )
                        current_issue.resolution = solution
                    elif line.startswith("**Impact**:"):
                        # Extract affected components from impact description
                        impact = line.replace("**Impact**:", "").strip()
                        if "payment" in impact.lower():
                            current_issue.affected_components.append(
                                "payment_processing"
                            )
                        if "provider" in impact.lower():
                            current_issue.affected_components.append("payment_provider")
                        if "retry" in impact.lower():
                            current_issue.affected_components.append("retry_logic")

                elif (
                    line.startswith("- ")
                    and current_issue
                    and current_issue.issue_type == "best practice solution"
                ):
                    # Extract prevention measures from best practices
                    measure = line.replace("- ", "").strip()
                    current_issue.prevention_measures.append(measure)

            # Don't forget the last issue
            if current_issue:
                issues.append(current_issue)

    return issues


@mcp.tool()
async def get_payments_domain_context(
    file_paths: List[str], context_type: str = "patterns"
) -> DomainKnowledgeAnalysisResult:
    """
    Analyze files for payment domain knowledge and requirements.

    This is the direct function that the BDD tests expect - it provides the analysis
    logic that MCP tools can leverage for AI-assisted code review.

    Args:
        file_paths: List of file paths to analyze
        context_type: Type of analysis ("patterns", "compliance", "architecture", "history")

    Returns:
        DomainKnowledgeAnalysisResult with structured analysis results
    """
    try:
        # Read file contents concurrently (will be mocked in tests)
        async def read_file_async(file_path: str) -> tuple[str, str]:
            """Read a file asynchronously and return (path, content)."""
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    return file_path, content
            except Exception:
                # Skip files that can't be read
                return file_path, ""

        # Read all files concurrently
        file_read_tasks = [read_file_async(fp) for fp in file_paths]
        file_results = await asyncio.gather(*file_read_tasks, return_exceptions=True)

        file_contents = {}
        for result in file_results:
            if isinstance(result, tuple) and result[1]:  # Valid result with content
                file_contents[result[0]] = result[1]

        # For architecture analysis, also try to read relevant architecture documentation
        if context_type in ["architecture", "all"]:
            architecture_docs = [
                "/docs/architecture/Data_Flow_Architecture.md",
                "/docs/architecture/architecture.md",
                "/README.md",
            ]
            # Read architecture docs concurrently
            arch_tasks = []
            for doc_path in architecture_docs:
                if os.path.exists(doc_path):
                    arch_tasks.append(read_file_async(doc_path))

            if arch_tasks:
                arch_results = await asyncio.gather(*arch_tasks, return_exceptions=True)
                for result in arch_results:
                    if isinstance(result, tuple) and result[1]:
                        file_contents[result[0]] = result[1]

        # For historical analysis, also try to read incident documentation and provider notes
        if context_type in ["history", "all"]:
            incident_docs = [
                "/docs/incidents/Payment_Retry_Issues_2024.md",
                "/docs/incidents/incidents.md",
                "/docs/postmortems/postmortems.md",
                "/docs/providers/PayPal_Integration_Notes.md",
                "/docs/providers/Stripe_Integration_Notes.md",
                "/docs/providers/Adyen_Integration_Notes.md",
            ]
            # Read incident docs concurrently
            incident_tasks = []
            for doc_path in incident_docs:
                if os.path.exists(doc_path):
                    incident_tasks.append(read_file_async(doc_path))

            if incident_tasks:
                incident_results = await asyncio.gather(
                    *incident_tasks, return_exceptions=True
                )
                for result in incident_results:
                    if isinstance(result, tuple) and result[1]:
                        file_contents[result[0]] = result[1]

        # Perform analysis based on context type
        domain_patterns = []
        compliance_requirements = []
        architectural_constraints = []
        historical_issues = []

        if context_type in ["patterns", "all"]:
            domain_patterns = _analyze_provider_integration_patterns(
                file_paths, file_contents
            )

        if context_type in ["compliance", "all"]:
            compliance_requirements = _analyze_pci_compliance(file_paths, file_contents)

        if context_type in ["architecture", "all"]:
            architectural_constraints = _analyze_data_flow_architecture(file_contents)

        if context_type in ["history", "all"]:
            historical_issues = _analyze_historical_issues(file_contents)

        # Generate analysis summary
        analysis_summary = (
            f"Analyzed {len(file_paths)} files for {context_type} context. "
        )
        analysis_summary += f"Found {len(domain_patterns)} domain patterns, {len(compliance_requirements)} compliance requirements, "
        analysis_summary += f"{len(architectural_constraints)} architectural constraints, and {len(historical_issues)} historical issues."

        # Generate recommendations
        recommendations = []
        for pattern in domain_patterns:
            recommendations.extend(pattern.recommendations)
        for requirement in compliance_requirements:
            recommendations.append(requirement.remediation_guidance)

        # Generate risk assessment
        risk_assessment = {
            "critical_issues": len(
                [r for r in compliance_requirements if r.severity == "critical"]
            ),
            "high_risk_constraints": len(
                [c for c in architectural_constraints if c.risk_level == "high"]
            ),
            "pattern_confidence_avg": sum(p.confidence_score for p in domain_patterns)
            / len(domain_patterns)
            if domain_patterns
            else 0.0,
            "historical_relevance_avg": sum(
                h.relevance_score for h in historical_issues
            )
            / len(historical_issues)
            if historical_issues
            else 0.0,
        }

        return DomainKnowledgeAnalysisResult(
            success=True,
            domain_patterns=domain_patterns,
            compliance_requirements=compliance_requirements,
            architectural_constraints=architectural_constraints,
            historical_issues=historical_issues,
            analysis_summary=analysis_summary,
            recommendations=list(set(recommendations)),  # Remove duplicates
            risk_assessment=risk_assessment,
        )

    except Exception as e:
        return DomainKnowledgeAnalysisResult(
            success=False,
            domain_patterns=[],
            compliance_requirements=[],
            architectural_constraints=[],
            historical_issues=[],
            analysis_summary=f"Analysis failed: {str(e)}",
            recommendations=[],
            risk_assessment={"error": str(e)},
        )


# MCP Tools that leverage the private analysis functions above


@mcp.tool()
async def analyze_payment_code_compliance(
    file_paths: List[str],
) -> List[ComplianceRequirement]:
    """
    Analyze payment processing code for PCI DSS compliance requirements.

    This tool identifies potential compliance violations in payment code,
    including sensitive data handling, storage risks, and transmission security.

    Args:
        file_paths: List of file paths to analyze for compliance

    Returns:
        List of ComplianceRequirement dataclasses with identified violations
        and remediation guidance
    """

    # Read file contents concurrently
    async def read_file_async(file_path: str) -> tuple[str, str]:
        """Read a file asynchronously and return (path, content)."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return file_path, content
        except Exception:
            # Skip files that can't be read
            return file_path, ""

    # Read all files concurrently
    file_read_tasks = [read_file_async(fp) for fp in file_paths]
    file_results = await asyncio.gather(*file_read_tasks, return_exceptions=True)

    file_contents = {}
    for result in file_results:
        if isinstance(result, tuple) and result[1]:  # Valid result with content
            file_contents[result[0]] = result[1]

    return _analyze_pci_compliance(file_paths, file_contents)


@mcp.tool()
async def analyze_payment_provider_patterns(
    file_paths: List[str],
) -> List[DomainPattern]:
    """
    Analyze payment provider integration patterns in code.

    This tool identifies provider-specific integration patterns,
    anti-patterns, and provides recommendations for improvement.

    Args:
        file_paths: List of file paths to analyze for provider patterns

    Returns:
        List of DomainPattern dataclasses with detected patterns
        and improvement recommendations
    """

    # Read file contents concurrently
    async def read_file_async(file_path: str) -> tuple[str, str]:
        """Read a file asynchronously and return (path, content)."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return file_path, content
        except Exception:
            # Skip files that can't be read
            return file_path, ""

    # Read all files concurrently
    file_read_tasks = [read_file_async(fp) for fp in file_paths]
    file_results = await asyncio.gather(*file_read_tasks, return_exceptions=True)

    file_contents = {}
    for result in file_results:
        if isinstance(result, tuple) and result[1]:  # Valid result with content
            file_contents[result[0]] = result[1]

    return _analyze_provider_integration_patterns(file_paths, file_contents)


@mcp.tool()
async def analyze_payment_architecture_constraints(
    file_paths: List[str],
) -> List[ArchitecturalConstraint]:
    """
    Analyze architectural constraints for payment data flow.

    This tool validates Bronze/Silver/Gold layer constraints,
    data immutability requirements, and architectural patterns.

    Args:
        file_paths: List of file paths to analyze for architectural constraints

    Returns:
        List of ArchitecturalConstraint dataclasses with constraint violations
        and validation rules
    """

    # Read file contents concurrently
    async def read_file_async(file_path: str) -> tuple[str, str]:
        """Read a file asynchronously and return (path, content)."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return file_path, content
        except Exception:
            # Skip files that can't be read
            return file_path, ""

    # Read all files concurrently
    file_read_tasks = [read_file_async(fp) for fp in file_paths]

    # Also try to read relevant architecture documentation concurrently
    architecture_docs = [
        "/docs/architecture/Data_Flow_Architecture.md",
        "/docs/architecture/architecture.md",
        "/README.md",
    ]
    for doc_path in architecture_docs:
        if os.path.exists(doc_path):
            file_read_tasks.append(read_file_async(doc_path))

    file_results = await asyncio.gather(*file_read_tasks, return_exceptions=True)

    file_contents = {}
    for result in file_results:
        if isinstance(result, tuple) and result[1]:  # Valid result with content
            file_contents[result[0]] = result[1]

    return _analyze_data_flow_architecture(file_contents)


@mcp.tool()
async def analyze_payment_historical_issues(
    file_paths: List[str],
) -> List[HistoricalIssue]:
    """
    Analyze historical payment processing issues and lessons learned.

    This tool extracts relevant historical incidents, best practices,
    and prevention measures from documentation and incident reports.

    Args:
        file_paths: List of file paths to analyze for historical context

    Returns:
        List of HistoricalIssue dataclasses with historical incidents
        and prevention measures
    """

    # Read file contents concurrently
    async def read_file_async(file_path: str) -> tuple[str, str]:
        """Read a file asynchronously and return (path, content)."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return file_path, content
        except Exception:
            # Skip files that can't be read
            return file_path, ""

    # Read all files concurrently
    file_read_tasks = [read_file_async(fp) for fp in file_paths]

    # Also try to read incident documentation and provider notes concurrently
    incident_docs = [
        "/docs/incidents/Payment_Retry_Issues_2024.md",
        "/docs/incidents/incidents.md",
        "/docs/postmortems/postmortems.md",
        "/docs/providers/PayPal_Integration_Notes.md",
        "/docs/providers/Stripe_Integration_Notes.md",
        "/docs/providers/Adyen_Integration_Notes.md",
    ]
    for doc_path in incident_docs:
        if os.path.exists(doc_path):
            file_read_tasks.append(read_file_async(doc_path))

    file_results = await asyncio.gather(*file_read_tasks, return_exceptions=True)

    file_contents = {}
    for result in file_results:
        if isinstance(result, tuple) and result[1]:  # Valid result with content
            file_contents[result[0]] = result[1]

    return _analyze_historical_issues(file_contents)
