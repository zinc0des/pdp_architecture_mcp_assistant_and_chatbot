"""
AI-Enabling Code Analysis Tools

Provides flexible analysis frameworks that enable AI reasoning rather than
constraining it with rigid prescriptive patterns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.tools.code_review.prescriptive_comments import (
    _get_pr_details_with_context,
)
from pdp_dev_mcp.tools.common.azure_devops_common import AzureDevOpsPRContext


class AnalysisDepth(Enum):
    """Analysis depth levels for context gathering."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ComplexityLevel(Enum):
    """Code change complexity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AnalysisGuidelines:
    """
    Guidelines for AI analysis that enable flexible reasoning.

    Provides framework and direction without constraining AI's analytical capabilities.
    """

    objective: str
    domain_focus: str
    approach: str
    technology_focus: str
    technology_patterns: str
    focus_areas: List[str]
    depth: str


@dataclass
class DomainContext:
    """
    Payment domain context for specialized analysis.

    Enables AI to apply domain-specific expertise during code review.
    """

    compliance_requirements: List[str]
    performance_patterns: List[str]
    business_logic: List[str]
    security_patterns: List[str]
    technology_patterns: List[str] = field(default_factory=list)
    complexity_level: str = "medium"


@dataclass
class QualityCategories:
    """
    Hybrid classification system with standard and novel category support.

    Provides structure while preserving AI's ability to identify new patterns.
    """

    standard_categories: List[str]
    allow_novel_categories: bool
    novel_category_guidance: str
    category_descriptions: Dict[str, str] = field(default_factory=dict)


@dataclass
class CodeAnalysisContext:
    """
    Comprehensive context for AI-enabled code analysis.

    Contains all information needed for flexible, intelligent code review
    without constraining AI reasoning to predefined patterns.
    """

    pr_id: int
    files: List[str]
    analysis_guidelines: AnalysisGuidelines
    domain_context: DomainContext
    quality_categories: QualityCategories
    output_guidance: str
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD


@mcp.tool()
def get_code_analysis_context(
    pr_id: Optional[int] = None,
    org: Optional[str] = None,
    project: Optional[str] = None,
    repository: Optional[str] = None,
    pr_context: Optional[AzureDevOpsPRContext] = None,
    pr_url: Optional[str] = None,
    depth: str = "standard",
) -> CodeAnalysisContext:
    """
    Retrieve comprehensive analysis context for AI-enabled code review.

    Provides analytical framework and domain context that enables AI to perform
    flexible, intelligent code analysis without rigid constraints.

    Automatically fetches changed files from the PR via Azure DevOps API.

    Context-first approach: Accepts either:
    1. Pre-established PR context dataclass (AzureDevOpsPRContext) - preferred
    2. PR URL for automatic context establishment
    3. Individual components (pr_id, org, project, repository) - legacy support

    Args:
        pr_id: Pull request identifier (optional if pr_context or pr_url provided)
        org: Azure DevOps organization (optional if pr_context or pr_url provided)
        project: Azure DevOps project (optional if pr_context or pr_url provided)
        repository: Repository name (optional if pr_context or pr_url provided)
        pr_context: Pre-established AzureDevOpsPRContext (recommended)
        pr_url: Azure DevOps PR URL (alternative to pr_context)
        depth: Analysis depth level (minimal/standard/comprehensive)

    Returns:
        CodeAnalysisContext with guidelines, domain context, quality frameworks, and
        list of changed files fetched from the PR

    Raises:
        ValueError: If neither pr_context, pr_url, nor complete individual parameters are provided
        Exception: If PR file fetching fails (with graceful fallback to empty list)

    Examples:
        # Method 1: Using pre-established context (recommended)
        context = azure_devops_establish_pr_context(pr_url="https://...")
        analysis = get_code_analysis_context(pr_context=context)

        # Method 2: Using PR URL directly
        analysis = get_code_analysis_context(
            pr_url="https://dev.azure.com/org/project/_git/repo/pullrequest/123"
        )

        # Method 3: Using individual parameters (legacy)
        analysis = get_code_analysis_context(
            pr_id=123, org="org", project="project", repository="repo"
        )
    """
    # Context-first: Use provided context, URL, or individual parameters
    if pr_context:
        pr_id = pr_context.pr_id
        org = pr_context.organization
        project = pr_context.project
        repository = pr_context.repository
    elif pr_url:
        # Parse URL and extract components
        from pdp_dev_mcp.tools.common.enhanced_repository_discovery import (
            parse_azure_devops_pr_url,
        )

        parsed_org, parsed_project, parsed_repo, parsed_pr_id = (
            parse_azure_devops_pr_url(pr_url)
        )
        if not all([parsed_org, parsed_project, parsed_repo, parsed_pr_id]):
            raise ValueError(
                f"Unable to parse all required components from PR URL: {pr_url}"
            )

        pr_id = int(parsed_pr_id)
        org = parsed_org
        project = parsed_project
        repository = parsed_repo
    elif not all([pr_id, org, project, repository]):
        raise ValueError(
            "Must provide either: (1) pr_context, (2) pr_url, or (3) all of pr_id, org, project, and repository"
        )

    # At this point, all required parameters are guaranteed to be non-None due to validation above
    assert pr_id is not None
    assert org is not None
    assert project is not None
    assert repository is not None

    # Fetch PR changed files from Azure DevOps API
    from pdp_dev_mcp.tools.code_review.ai_comment_posting import _get_pr_diff_files

    try:
        diff_files = _get_pr_diff_files(org, project, repository, pr_id)
        files = list(diff_files.keys()) if diff_files else []
    except Exception:
        # Graceful fallback if file fetching fails
        files = []

    # Get PR metadata for enhanced context
    pr_title = f"PR {pr_id}"
    pr_description_snippet = ""
    try:
        # Use modern context architecture for PR details retrieval
        pr_url_str = f"https://dev.azure.com/{org}/{project}/_git/{repository}/pullrequest/{pr_id}"
        context = AzureDevOpsPRContext.from_pr_url(pr_url_str)
        pr_details = _get_pr_details_with_context(context)
        if pr_details:
            pr_title = pr_details.title or pr_title
            pr_description_snippet = (
                f" - {pr_details.description[:100]}..."
                if pr_details.description
                else ""
            )
    except Exception:
        # Graceful fallback if PR metadata retrieval fails
        pass

    # Get payment domain context for specialized analysis
    domain_info = _get_domain_context()

    # Detect technology stack for context-specific guidance
    tech_stack = _detect_technology_stack(files)
    tech_context = _get_tech_specific_context(tech_stack)

    # Determine if this is a simple change
    is_simple = _is_simple_change(files)

    # Build analysis guidelines with PR context
    guidelines = AnalysisGuidelines(
        objective=f"Analyze code changes for quality, performance, security, maintainability, and business logic compliance using flexible AI reasoning. Context: {pr_title}{pr_description_snippet}",
        domain_focus="Payment processing with emphasis on PCI compliance, provider patterns, and financial transaction integrity",
        approach="Apply comprehensive software engineering knowledge with flexible reasoning rather than rigid rule matching",
        technology_focus=", ".join([k for k, v in tech_stack.items() if v]),
        technology_patterns=", ".join(tech_context.get("patterns", [])),
        focus_areas=_get_focus_areas(depth, is_simple),
        depth=depth,
    )

    # Build domain context
    domain_context = DomainContext(
        compliance_requirements=domain_info.get("compliance_requirements", []),
        performance_patterns=domain_info.get("performance_patterns", []),
        business_logic=domain_info.get("business_logic", []),
        security_patterns=domain_info.get("security_patterns", []),
        technology_patterns=tech_context.get("patterns", []),
        complexity_level="low" if is_simple else "medium",
    )

    # Build quality categories with hybrid approach
    quality_categories = QualityCategories(
        standard_categories=[
            "performance",
            "security",
            "maintainability",
            "domain-specific",
            "architecture",
        ],
        allow_novel_categories=True,
        novel_category_guidance="AI can propose new categories when standard classifications don't capture the specific nature of code quality issues found",
        category_descriptions={
            "performance": "Efficiency, scalability, resource usage, and optimization opportunities",
            "security": "Vulnerability assessment, PCI compliance, data protection, and access control",
            "maintainability": "Code clarity, documentation, testing, and long-term sustainability",
            "domain-specific": "Payment processing logic, provider patterns, and business rule compliance",
            "architecture": "Design patterns, coupling, separation of concerns, and structural quality",
        },
    )

    # Build output guidance
    output_guidance = """
    Organize your analysis findings to enable structured communication:
    1. Classify each finding using standard or novel categories with rationale
    2. Assess business impact and technical severity in payment processing context
    3. Provide specific, actionable recommendations with examples where helpful
    4. Structure findings for Azure DevOps comment threading and developer workflow
    5. Highlight any domain-specific concerns (PCI compliance, provider patterns, etc.)
    """

    return CodeAnalysisContext(
        pr_id=pr_id,
        files=files,
        analysis_guidelines=guidelines,
        domain_context=domain_context,
        quality_categories=quality_categories,
        output_guidance=output_guidance.strip(),
        analysis_depth=AnalysisDepth(depth),
    )


def _get_domain_context() -> Dict[str, List[str]]:
    """Get payment domain context for specialized analysis."""
    return {
        "compliance_requirements": [
            "PCI DSS Level 1 compliance",
            "Card scheme rules and regulations",
            "Data retention policies",
            "Audit trail requirements",
        ],
        "performance_patterns": [
            "Spark DataFrame optimization and caching",
            "Large dataset processing efficiency",
            "Payment volume scaling patterns",
            "Real-time transaction processing",
        ],
        "business_logic": [
            "Chargeback and refund processing rules",
            "Provider-specific integration patterns",
            "Payment state machine integrity",
            "Financial reconciliation accuracy",
        ],
        "security_patterns": [
            "Credential and certificate management",
            "Input validation and sanitization",
            "Authentication and authorization flows",
            "Secure API communication patterns",
            "Data encryption and key management",
            "Vulnerability assessment and remediation",
        ],
    }


def _detect_technology_stack(files: List[str]) -> Dict[str, bool]:
    """Detect technology stack from file patterns."""
    tech_stack = {
        "data_processing": False,  # Spark/Databricks/PySpark
        "web_services": False,  # APIs/Endpoints
        "database": False,  # SQL/Database operations
        "frontend": False,  # UI/Frontend components
        "infrastructure": False,  # IaC/Bicep/ARM templates
    }

    for file_path in files:
        path_lower = file_path.lower()

        # Data processing: Spark, Databricks, PySpark patterns
        if any(pattern in path_lower for pattern in ["spark", "databricks", "pyspark"]):
            tech_stack["data_processing"] = True

        # Web services: API, endpoints, web services
        if any(
            pattern in path_lower
            for pattern in ["api", "endpoint", "service", "controller"]
        ):
            tech_stack["web_services"] = True

        # Database: SQL, database operations
        if any(
            pattern in path_lower
            for pattern in ["sql", "database", "query", "migration"]
        ):
            tech_stack["database"] = True

        # Frontend: UI, frontend, web components
        if any(
            pattern in path_lower for pattern in ["frontend", "ui", "component", "view"]
        ):
            tech_stack["frontend"] = True

        # Infrastructure as Code: Bicep, ARM, Terraform, deployment
        if any(
            pattern in path_lower
            for pattern in ["bicep", "arm", "terraform", "deployment", "infrastructure"]
        ) or any(
            ext in path_lower for ext in [".bicep", ".json", ".tf", ".yaml", ".yml"]
        ):
            tech_stack["infrastructure"] = True

    return tech_stack


def _get_tech_specific_context(tech_stack: Dict[str, bool]) -> Dict[str, List[str]]:
    """Get technology-specific analysis context."""
    patterns = []

    if tech_stack.get("data_processing"):
        patterns.extend(
            [
                "DataFrame caching best practices",
                "Avoid multiple actions without cache",
                "Partition optimization for large datasets",
                "Broadcast join optimization",
                "Memory management for large transformations",
            ]
        )

    if tech_stack.get("web_services"):
        patterns.extend(
            [
                "Input validation and sanitization",
                "Rate limiting implementation",
                "Error handling and logging",
                "Authentication and authorization",
                "API versioning and compatibility",
            ]
        )

    if tech_stack.get("database"):
        patterns.extend(
            [
                "Query optimization and indexing",
                "Transaction management",
                "Connection pooling",
                "SQL injection prevention",
            ]
        )

    if tech_stack.get("frontend"):
        patterns.extend(
            [
                "Component lifecycle management",
                "State management patterns",
                "Performance optimization techniques",
                "Accessibility best practices",
            ]
        )

    if tech_stack.get("infrastructure"):
        patterns.extend(
            [
                "Resource security configurations",
                "Cost optimization strategies",
                "Infrastructure compliance validation",
                "Deployment automation patterns",
                "Resource dependency management",
            ]
        )

    return {"patterns": patterns}


def _is_simple_change(files: List[str]) -> bool:
    """Determine if this represents a simple code change."""
    # Simple heuristic: single file or utility changes
    if len(files) <= 1:
        return True

    # Check for utility/helper file patterns
    simple_patterns = ["util", "helper", "constant", "config"]
    for file_path in files:
        if any(pattern in file_path.lower() for pattern in simple_patterns):
            return True

    return False


def _get_focus_areas(depth: str, is_simple: bool) -> List[str]:
    """Get analysis focus areas based on depth and complexity."""
    base_areas = ["code quality", "business logic", "security"]

    if depth == "minimal" or is_simple:
        return base_areas

    if depth == "comprehensive":
        return base_areas + [
            "performance optimization",
            "architectural patterns",
            "maintainability",
            "testing coverage",
            "documentation quality",
            "compliance validation",
        ]

    # Standard depth
    return base_areas + ["performance", "maintainability"]
