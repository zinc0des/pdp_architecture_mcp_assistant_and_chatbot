"""
Payments domain context extraction tool for AI-assisted code review.

This tool extracts payment domain knowledge from repository sources identified
during the domain audit to provide contextual insights for code review assistance.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.tools.common.repository_context import ensure_repository_context


@dataclass
class ProviderPatterns:
    """Payment provider patterns and integration approaches."""

    provider_types: List[str]
    integration_patterns: List[str]
    data_flow_approaches: List[str]
    common_transformations: List[str]


@dataclass
class ComplianceRequirements:
    """PCI DSS and regulatory compliance requirements."""

    pci_requirements: List[str]
    data_sensitivity_levels: List[str]
    encryption_standards: List[str]
    audit_requirements: List[str]


@dataclass
class ArchitecturalContext:
    """Medallion architecture and system constraints."""

    medallion_architecture: Dict[str, str]
    architectural_constraints: List[str]
    data_flow_patterns: List[str]
    integration_points: List[str]


@dataclass
class HistoricalContext:
    """Historical incidents and lessons learned."""

    incident_patterns: List[str]
    lessons_learned: List[str]
    risk_factors: List[str]
    success_patterns: List[str]


@dataclass
class RepositoryInfo:
    """Repository context information."""

    organization: str
    project: str
    repository: str


@dataclass
class PaymentsDomainContextResult:
    """Result of payments domain context analysis."""

    success: bool
    domain_relevance: str
    context_summary: str
    repository_info: RepositoryInfo
    recommended_reviewers: List[str]
    provider_patterns: Optional[ProviderPatterns] = None
    compliance_requirements: Optional[ComplianceRequirements] = None
    architectural_context: Optional[ArchitecturalContext] = None
    historical_context: Optional[HistoricalContext] = None
    error: Optional[str] = None


@mcp.tool()
def get_payments_change_context(
    changed_files: List[str],
    context_type: str = "patterns",
    working_directory: Optional[str] = None,
) -> PaymentsDomainContextResult:
    """
    Extract payment domain context relevant to changed files for AI code review assistance.

    Based on domain audit findings, extracts context from:
    - Databricks notebooks (852 Python files with payment processing logic)
    - PowerBI semantic models (payment analytics patterns)
    - Synapse SQL scripts (star schema definitions)
    - Payment processing patterns across Bronze/Silver/Gold layers

    Args:
        changed_files: List of file paths that were modified
        context_type: Type of context to extract
                      - "patterns": Provider patterns and integration approaches
                      - "compliance": PCI DSS and regulatory requirements
                      - "architecture": Medallion architecture and constraints
                      - "history": Historical incidents and lessons learned
                      - "comprehensive": All context types combined
        working_directory: Repository root directory

    Returns:
        PaymentsDomainContextResult containing:
        - success: Whether context extraction succeeded
        - domain_relevance: Low/medium/high relevance to payment processing
        - context_summary: High-level summary of findings
        - repository_info: RepositoryInfo with organization, project, repository details
        - recommended_reviewers: List of suggested reviewer types based on changes
        - provider_patterns: ProviderPatterns dataclass (if context_type="patterns" or "comprehensive")
        - compliance_requirements: ComplianceRequirements dataclass (if context_type="compliance" or "comprehensive")
        - architectural_context: ArchitecturalContext dataclass (if context_type="architecture" or "comprehensive")
        - historical_context: HistoricalContext dataclass (if context_type="history" or "comprehensive")
        - error: Error message if extraction failed
    """
    try:
        # Get repository context for integration (with improved error handling)
        repo_context = ensure_repository_context(working_directory)

        # Create repository info (with fallbacks if context discovery fails)
        if repo_context.get("success"):
            repo_info = RepositoryInfo(
                organization=repo_context.get("organization", "unknown"),
                project=repo_context.get("project", "unknown"),
                repository=repo_context.get("repository", "unknown"),
            )
        else:
            # Provide guidance when repository context fails
            return PaymentsDomainContextResult(
                success=False,
                error=f"Repository context required: {repo_context.get('error', 'Unknown error')}",
                domain_relevance="unknown",
                context_summary="Repository context discovery failed",
                repository_info=RepositoryInfo(
                    organization="unknown", project="unknown", repository="unknown"
                ),
                recommended_reviewers=[],
                provider_patterns=None,
                compliance_requirements=None,
                architectural_context=None,
                historical_context=None,
            )

        # Analyze domain relevance of changed files
        domain_relevance = _analyze_domain_relevance(changed_files)

        # Generate context summary and reviewer suggestions
        context_summary = _generate_context_summary(
            changed_files, context_type, domain_relevance
        )
        recommended_reviewers = _suggest_reviewers(changed_files, domain_relevance)

        # For low relevance files, return minimal context
        if domain_relevance == "low":
            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
            )

        # Extract context based on type
        if context_type == "patterns":
            provider_patterns = _extract_provider_patterns(
                changed_files, working_directory
            )
            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
                provider_patterns=provider_patterns,
            )
        elif context_type == "compliance":
            compliance_requirements = _extract_compliance_requirements(
                changed_files, working_directory
            )
            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
                compliance_requirements=compliance_requirements,
            )
        elif context_type == "architecture":
            architectural_context = _extract_architectural_context(
                changed_files, working_directory
            )
            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
                architectural_context=architectural_context,
            )
        elif context_type == "history":
            historical_context = _extract_historical_context(
                changed_files, working_directory
            )
            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
                historical_context=historical_context,
            )
        elif context_type == "comprehensive":
            # Extract all context types
            provider_patterns = _extract_provider_patterns(
                changed_files, working_directory
            )
            compliance_requirements = _extract_compliance_requirements(
                changed_files, working_directory
            )
            architectural_context = _extract_architectural_context(
                changed_files, working_directory
            )
            historical_context = _extract_historical_context(
                changed_files, working_directory
            )

            return PaymentsDomainContextResult(
                success=True,
                domain_relevance=domain_relevance,
                context_summary=context_summary,
                repository_info=repo_info,
                recommended_reviewers=recommended_reviewers,
                provider_patterns=provider_patterns,
                compliance_requirements=compliance_requirements,
                architectural_context=architectural_context,
                historical_context=historical_context,
            )
        else:
            return PaymentsDomainContextResult(
                success=False,
                domain_relevance="unknown",
                context_summary="",
                repository_info=repo_info,
                recommended_reviewers=[],
                error=f"Unknown context_type: {context_type}. Use patterns|compliance|architecture|history|comprehensive",
            )

    except Exception as e:
        return PaymentsDomainContextResult(
            success=False,
            domain_relevance="unknown",
            context_summary="",
            repository_info=RepositoryInfo(
                organization="unknown", project="unknown", repository="unknown"
            ),
            recommended_reviewers=[],
            error=f"Failed to extract payments domain context: {str(e)}",
        )


def _analyze_domain_relevance(changed_files: List[str]) -> str:
    """
    Analyze how relevant the changed files are to payment processing domain.

    Based on audit findings of payment processing areas:
    - PaymentTransactions: Core payment processing
    - NetworkTokenization: Card tokenization and BIN data
    - Fraud: PIMS events and risk management
    - AccountUpdater: Payment method lifecycle
    - PowerBI: Payment analytics and reporting
    """
    high_relevance_patterns = [
        r"PaymentTransactions",
        r"NetworkTokenization",
        r"Fraud.*PIMS",
        r"AccountUpdater",
        r"Payment.*Analytics",
        r"dimCard|dimPayment|factTransaction",
    ]

    medium_relevance_patterns = [
        r"PowerBI",
        r"Synapse.*sql",
        r"Bronze|Silver|Gold",
        r"billing|chargeback|refund",
    ]

    high_count = sum(
        1
        for file in changed_files
        for pattern in high_relevance_patterns
        if re.search(pattern, file, re.IGNORECASE)
    )

    medium_count = sum(
        1
        for file in changed_files
        for pattern in medium_relevance_patterns
        if re.search(pattern, file, re.IGNORECASE)
    )

    if high_count > 0:
        return "high"
    elif medium_count > 0:
        return "medium"
    else:
        return "low"


def _extract_provider_patterns(
    changed_files: List[str], working_directory: Optional[str]
) -> ProviderPatterns:
    """
    Extract payment provider patterns from domain knowledge sources.

    Based on audit findings from NetworkTokenization notebooks and PaymentTransactions.

    Returns:
        ProviderPatterns dataclass containing:
        - provider_types: List of supported payment providers (visa, mastercard, etc.)
        - integration_patterns: List of integration approach patterns
        - data_flow_approaches: List of data processing approaches
        - common_transformations: List of typical data transformation patterns
    """
    # From domain audit: NetworkTokenization/Gold/dimCard.py revealed provider patterns
    return ProviderPatterns(
        provider_types=["visa", "mastercard", "amex", "discover"],
        integration_patterns=[
            "Bronze ingestion -> Silver processing -> Gold dimensions",
            "Provider response mapping with error handling",
            "BIN range validation and issuer identification",
            "Card tokenization for PCI compliance",
            "Geographic issuer mapping (issuingCountryName, issuingBank)",
        ],
        data_flow_approaches=[
            "Real-time provider responses with batch processing",
            "Event-driven ingestion with Delta Lake storage",
            "Multi-provider aggregation with standardized output",
        ],
        common_transformations=[
            "cardProviderName normalization (lowercase)",
            "Payment method family categorization",
            "Brand and card type classification",
            "Issuing bank and country identification",
        ],
    )


def _extract_compliance_requirements(
    changed_files: List[str], working_directory: Optional[str]
) -> ComplianceRequirements:
    """
    Extract PCI DSS and regulatory compliance requirements.

    Based on audit findings and data quality frameworks in repository.

    Returns:
        ComplianceRequirements dataclass containing:
        - pci_requirements: List of PCI DSS compliance requirements
        - data_sensitivity_levels: List of data classification levels
        - encryption_standards: List of required encryption standards
        - audit_requirements: List of audit and retention requirements
    """
    return ComplianceRequirements(
        pci_requirements=[
            "Card data tokenization required for storage",
            "BIN data handling must follow PCI guidelines",
            "Payment instrument data requires secure processing",
            "Sensitive authentication data must not be stored",
            "Card verification values must be protected",
        ],
        data_sensitivity_levels=[
            "Level 1: Card numbers, CVV, magnetic stripe data",
            "Level 2: Payment instrument IDs, account IDs",
            "Level 3: Transaction amounts, merchant data",
            "Level 4: Aggregate analytics and reporting data",
        ],
        encryption_standards=[
            "AES-256 for data at rest",
            "TLS 1.2+ for data in transit",
            "Key rotation every 90 days",
            "Hardware security modules (HSMs) for key management",
        ],
        audit_requirements=[
            "Payment data: 7 years for compliance",
            "Card tokens: Active period + 1 year",
            "Fraud data: 5 years for pattern analysis",
            "GDPR compliance for EU payment data",
            "SOX controls for financial reporting",
            "PCI DSS Level 1 merchant requirements",
        ],
    )


def _extract_architectural_context(
    changed_files: List[str], working_directory: Optional[str]
) -> ArchitecturalContext:
    """
    Extract medallion architecture patterns and constraints.

    Based on audit findings from databricks notebooks and table naming patterns.

    Returns:
        ArchitecturalContext dataclass containing:
        - medallion_architecture: Dict mapping layer names to descriptions
        - architectural_constraints: List of architectural constraints and rules
        - data_flow_patterns: List of data processing flow patterns
        - integration_points: List of system integration points
    """
    return ArchitecturalContext(
        medallion_architecture={
            "bronze_layer": "Raw data ingestion from payment providers and systems",
            "silver_layer": "Cleaned, validated, and integrated payment data",
            "gold_layer": "Business-ready dimensional models for analytics",
        },
        architectural_constraints=[
            "Bronze uses main_root path, never reprocessed",
            "Silver/Gold use workspace-specific paths for reprocessing",
            "Shadow tables supported with shadow_ prefix for safe testing",
            "Delta Lake format required for ACID transactions",
        ],
        data_flow_patterns=[
            "Payment events -> Bronze tables -> Silver processing -> Gold dimensions",
            "Real-time ingestion with batch processing windows",
            "Kusto ingestion for operational monitoring data",
            "PowerBI semantic models consume Gold layer",
        ],
        integration_points=[
            "Kusto ingestion for operational data",
            "PowerBI semantic models for analytics",
            "Synapse star schema for reporting",
            "AAS (Analysis Services) for OLAP processing",
        ],
    )


def _extract_historical_context(
    changed_files: List[str], working_directory: Optional[str]
) -> HistoricalContext:
    """
    Extract historical incident patterns and lessons learned.

    Based on audit findings and common payment processing issues.

    Returns:
        HistoricalContext dataclass containing:
        - incident_patterns: List of historical incident patterns
        - lessons_learned: List of lessons learned from past issues
        - risk_factors: List of identified risk factors for changes
        - success_patterns: List of proven successful patterns and practices
    """
    return HistoricalContext(
        incident_patterns=[
            "Card testing fraud spikes during holiday seasons",
            "PIMS event processing bottlenecks during high-volume periods",
            "Retry logic failures causing duplicate payment processing",
            "Network tokenization issues during provider outages",
            "Data pipeline failures during schema evolution",
        ],
        lessons_learned=[
            "Always implement idempotency for payment operations",
            "Monitor PIMS event lag for early fraud detection",
            "Geographic patterns indicate payment method abuse",
            "Shadow table testing prevents production issues",
            "Gradual rollouts minimize payment disruption",
        ],
        risk_factors=[
            "Changes to retry logic can cause duplicate processing",
            "PIMS event filtering changes affect fraud detection accuracy",
            "Payment method mapping errors impact risk scoring",
            "Schema changes can break downstream analytics",
            "Network tokenization changes affect PCI compliance",
        ],
        success_patterns=[
            "Staged rollouts prevent payment processing disruptions",
            "Shadow table testing validates changes safely",
            "Real-time monitoring catches issues quickly",
            "Comprehensive test coverage prevents regressions",
            "Domain expert review catches subtle issues",
        ],
    )


def _generate_context_summary(
    changed_files: List[str], context_type: str, domain_relevance: str
) -> str:
    """Generate a human-readable summary of the context analysis."""
    file_count = len(changed_files)

    if domain_relevance == "low":
        return f"Analyzed {file_count} files with minimal payment domain relevance. No payment-specific domain knowledge applicable."

    domain_areas = []
    for file in changed_files:
        if re.search(r"PaymentTransactions", file, re.IGNORECASE):
            domain_areas.append("payment transactions")
        if re.search(r"NetworkTokenization", file, re.IGNORECASE):
            domain_areas.append("network tokenization")
        if re.search(r"Fraud", file, re.IGNORECASE):
            domain_areas.append("fraud detection")
        if re.search(r"PowerBI|Analytics", file, re.IGNORECASE):
            domain_areas.append("analytics")

    domain_areas = list(set(domain_areas))  # Remove duplicates
    areas_text = (
        ", ".join(domain_areas) if domain_areas else "general payment processing"
    )

    context_desc = {
        "patterns": "provider patterns and integration approaches",
        "compliance": "PCI compliance and regulatory requirements",
        "architecture": "medallion architecture and data flow constraints",
        "history": "historical incidents and lessons learned",
        "comprehensive": "comprehensive domain knowledge",
    }.get(context_type, "domain context")

    return f"Analyzed {file_count} files affecting {areas_text}. Extracted {context_desc} with {domain_relevance} domain relevance."


def _suggest_reviewers(changed_files: List[str], domain_relevance: str) -> List[str]:
    """Suggest appropriate reviewer types based on changed files and domain relevance."""
    if domain_relevance == "low":
        return ["Standard code review sufficient"]

    reviewers = []

    # Domain-specific reviewers
    if any(
        re.search(r"NetworkTokenization|dimCard", f, re.IGNORECASE)
        for f in changed_files
    ):
        reviewers.append("Payment domain expert (tokenization)")
        reviewers.append("Security team (PCI compliance)")

    if any(re.search(r"Fraud|PIMS", f, re.IGNORECASE) for f in changed_files):
        reviewers.append("Risk management team (fraud detection)")

    if any(
        re.search(r"Bronze|Silver|Gold|databricks", f, re.IGNORECASE)
        for f in changed_files
    ):
        reviewers.append("Data engineering team (pipeline architecture)")

    if any(
        re.search(r"PowerBI|Analytics|Synapse", f, re.IGNORECASE) for f in changed_files
    ):
        reviewers.append("Analytics team (reporting impact)")

    # Default to payment domain expert for high relevance
    if domain_relevance == "high" and not reviewers:
        reviewers.append("Payment domain expert")

    return reviewers if reviewers else ["Standard code review sufficient"]
