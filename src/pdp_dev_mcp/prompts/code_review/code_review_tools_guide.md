# Code Review Tools Guide - AI-Assisted Payment Platform Reviews

## Overview

The Payments Data Platform (PDP) provides 10 specialized MCP tools for AI-assisted code reviews. These tools follow an **AI-enabling architecture** that provides intelligent context and signals rather than prescriptive rules, allowing AI agents to reason naturally while being informed by payment domain expertise.

## Tool Architecture Philosophy

**AI-Enabling vs. Prescriptive Approach:**
- ✅ **AI-Enabling**: Provides intelligent context, data, and insights to enhance AI reasoning
- ❌ **Prescriptive**: Tells AI exactly what to say or enforces rigid rules
- 🎯 **Goal**: Enhance AI intelligence without constraining natural reasoning patterns

## Tool Categories

### 📊 AI-Enabling Tools (Context & Quality Assessment)

These tools provide comprehensive context and quality signals to inform AI analysis.

#### 1. `get_code_analysis_context`

**Purpose**: Provide comprehensive context for AI-assisted code reviews

**When to use**:
- Starting a code review process
- Need testing guidelines, domain context, and quality frameworks
- Want to ground review in project-specific standards

**Automatic PR File Fetching**:
- 🚀 **Always** fetches changed files from the PR via Azure DevOps API
- Returns populated file list in `CodeAnalysisContext.files`
- Enables seamless code review workflows - no manual file listing needed
- Single entry point for PR analysis with complete context

**Parameters**:
- `pr_id` (int): Pull request identifier
- `org` (str): Azure DevOps organization (REQUIRED)
- `project` (str): Azure DevOps project name (REQUIRED)
- `repository` (str): Repository name (REQUIRED)
- `depth` (str): Analysis depth - "minimal", "standard", or "comprehensive" (default: "standard")

**Returns**: `CodeAnalysisContext` with guidelines, domain context, quality frameworks, and **automatically fetched file list**

**Example use case**:
```
# Seamless workflow - automatically fetches changed files from PR:
context = get_code_analysis_context(
    pr_id=12345, 
    org="msazure",
    project="One",
    repository="Commerce.PaymentsDataPlatform",
    depth="comprehensive"
)
# context.files now contains the list of changed files from the PR
```

---

#### 1.5. `get_pr_file_changes_with_context`

**Purpose**: Retrieve detailed file change metadata from a pull request

**When to use**:
- Need metadata about changed files (paths, change types)
- Prerequisite step before fetching actual file contents
- Want to filter or prioritize files based on change type

**Workflow position**: Step 2 in complete code review workflow:
1. Establish PR context with `azure_devops_establish_pr_context`
2. Get file changes metadata (this tool) ← YOU ARE HERE
3. Fetch actual file contents with `get_file_contents_with_context`

**Parameters**:
- `context` (AzureDevOpsPRContext): PR context from `azure_devops_establish_pr_context`

**Returns**: `FileChangesResult` with:
- `files`: List of `FileChange` objects (path, change_type)
- `file_count`: Number of changed files
- `context`: Original PR context

**Example use case**:
```python
# Step 1: Establish PR context
context = azure_devops_establish_pr_context(
    pr_url_or_id="https://dev.azure.com/org/project/_git/repo/pullrequest/123"
)

# Step 2: Get file changes metadata
changes = get_pr_file_changes_with_context(context)
print(f"Found {changes.file_count} changed files")
for file in changes.files:
    print(f"{file.change_type}: {file.item.path}")
```

---

#### 1.6. `get_file_contents_with_context`

**Purpose**: Fetch actual source code contents from pull request files

**When to use**:
- Need to analyze actual code (not just file paths)
- Performing deep code review with specific insights
- Completing the full code review workflow

**Critical capability**: This is **the missing piece** that enables AI agents to read actual code for review, not just see file names.

**Workflow position**: Step 3 in complete code review workflow:
1. Establish PR context with `azure_devops_establish_pr_context`
2. Get file changes metadata with `get_pr_file_changes_with_context`
3. Fetch actual file contents (this tool) ← YOU ARE HERE

**Parameters**:
- `file_changes` (FileChangesResult): Output from `get_pr_file_changes_with_context`
- `context` (AzureDevOpsPRContext): PR context from step 1
- `context_depth` (str): Context level - "minimal", "standard", or "comprehensive" (default: "standard")

**Context depth options**:
- `"minimal"`: Just file contents
- `"standard"`: Contents + basic metadata
- `"comprehensive"`: Contents + metadata + domain context

**Returns**: `FileContentsResult` with:
- `files`: List of `FileContent` objects (path, content, metadata)
- `file_count`: Number of files fetched
- `context`: Original PR context

**Example use case**:
```python
# Complete 3-step workflow for code review:

# Step 1: Establish PR context
context = azure_devops_establish_pr_context(
    pr_url_or_id="https://dev.azure.com/org/project/_git/repo/pullrequest/123"
)

# Step 2: Get file changes metadata
changes = get_pr_file_changes_with_context(context)

# Step 3: Fetch actual file contents (THE MISSING PIECE!)
contents = await get_file_contents_with_context(changes, context, context_depth="comprehensive")

# Now analyze actual code:
for file in contents.files:
    if file.content:
        # Perform deep code analysis on actual source code
        analyze_code_quality(file.content)
        check_payment_patterns(file.content)
        validate_security(file.content)
```

---

#### 2. `get_payments_change_context`

**Purpose**: Extract payment domain context relevant to changed files

**When to use**:
- Reviewing changes to payment processing code
- Need to understand impact on Bronze/Silver/Gold data layers
- Want to identify affected payment systems and dependencies

**Based on domain audit**:
- Databricks notebooks (852 Python files with payment logic)
- PowerBI semantic models (payment analytics patterns)
- Synapse SQL scripts (star schema definitions)
- Payment processing across Bronze/Silver/Gold layers

**Parameters**:
- `changed_files` (List[str]): List of changed file paths
- `context_type` (str): "patterns", "compliance", "architecture", "history"
- `working_directory` (Optional[str]): Repository directory

**Returns**: `PaymentsDomainContextResult` with domain-specific insights

**Example use case**:
```
For changes to Bronze layer notebooks, understand payment flow impact:
context = get_payments_change_context(
    changed_files=["notebooks/bronze/payment_ingestion.py"],
    context_type="patterns"
)
```

---

#### 3. `get_code_quality_signals`

**Purpose**: Detect and analyze code quality signals for AI-driven assessment

**When to use**:
- Performing technical quality analysis
- Detecting security patterns, performance issues, anti-patterns
- Want quantitative metrics and qualitative insights

**Combines**:
- Static analysis (complexity, maintainability, technical debt)
- Security pattern detection
- Performance issue identification
- Domain-specific risks (payment security, data handling)

**Parameters**:
- `file_paths` (List[str]): Files to analyze
- `include_patterns` (Optional[List[str]]): Focus areas (e.g., ["security", "performance"])
- `severity_threshold` (SeverityLevel): Minimum severity ("info", "low", "medium", "high", "critical")
- `enable_domain_detection` (bool): Apply payment domain-specific detection

**Returns**: `CodeQualityReport` with structured quality signals

**Example use case**:
```
Analyze security and performance signals in payment processing code:
signals = await get_code_quality_signals(
    file_paths=["src/payment_processor.py"],
    include_patterns=["security", "performance"],
    severity_threshold="medium"
)
```

---

### 💬 Comment Posting Tools (Feedback Delivery)

These tools deliver AI-generated feedback to Azure DevOps pull requests.

#### 4. `post_ai_comments_by_pr_url` ⭐ **RECOMMENDED**

**Purpose**: Post AI-generated comments using PR URL (enhanced UX version)

**When to use**:
- You have a PR URL
- Want automatic parsing of org/project/repository/PR ID
- Cross-organization support needed

**Advantages over `post_ai_generated_comments`**:
- No manual URL parsing required
- Automatic org/project/repository extraction
- Handles both dev.azure.com and .visualstudio.com formats

**Parameters**:
- `pr_url` (str): Full Azure DevOps PR URL
- `comments` (List[CodeReviewComment]): AI-generated comments
- `dry_run` (bool): Validate without posting (default: False)
- `batch_size` (int): Comments per batch for rate limiting (default: 5)
- `filter_self_praise` (bool): Show praise locally for own PRs (default: True)

**Returns**: `CommentPostingResult` with posting status and local praise comments

**Self-praise filtering**: Automatically detects when posting to own PR and shows praise comments locally instead of publicly (avoids awkward self-congratulation).

**Example use case**:
```
Post review comments to a PR using just the URL:
result = post_ai_comments_by_pr_url(
    pr_url="https://dev.azure.com/microsoft/One/_git/Repo/pullrequest/123",
    comments=[...],
    dry_run=False
)
```

---

#### 5. `post_ai_generated_comments`

**Purpose**: Post comments with explicit org/project/repository/PR ID parameters

**When to use**:
- You already have parsed URL components
- Need explicit control over all parameters
- Working with components from other tools

**Parameters**:
- `org` (str): Azure DevOps organization (e.g., 'microsoft', 'msazure')
- `project` (str): Project name (e.g., 'One', 'PaymentsDataPlatform')
- `repository` (str): Repository name
- `pr_id` (int): Pull request ID (numeric)
- `comments` (List[CodeReviewComment]): AI-generated comments
- `dry_run`, `batch_size`, `filter_self_praise`: Same as above

**Example use case**:
```
Post comments when you already have parsed components:
result = post_ai_generated_comments(
    org="microsoft", project="One", repository="Repo", pr_id=123,
    comments=[...]
)
```

---

### 🔍 Payment Domain Tools (Deep Domain Analysis)

These tools provide payment-specific deep analysis for specialized reviews.

#### 6. `get_payments_domain_context`

**Purpose**: Analyze files for payment domain knowledge and requirements

**When to use**:
- Need domain knowledge analysis
- Want patterns, compliance, architecture, or historical analysis
- Reviewing payment-specific code changes

**Parameters**:
- `file_paths` (List[str]): Files to analyze
- `context_type` (str): "patterns", "compliance", "architecture", "history"

**Returns**: `DomainKnowledgeAnalysisResult` with structured analysis

**Example use case**:
```
Analyze payment patterns in changed files:
analysis = await get_payments_domain_context(
    file_paths=["src/payment_flow.py"],
    context_type="patterns"
)
```

---

#### 7. `analyze_payment_code_compliance`

**Purpose**: Analyze payment code for PCI DSS compliance requirements

**When to use**:
- Reviewing payment card data handling
- Need PCI DSS compliance validation
- Identifying sensitive data storage/transmission risks

**Detects**:
- Sensitive data handling violations
- Storage security risks
- Transmission security issues
- PCI DSS requirement violations

**Parameters**:
- `file_paths` (List[str]): Files to analyze for compliance

**Returns**: `List[ComplianceRequirement]` with violations and remediation guidance

**Example use case**:
```
Check PCI DSS compliance in payment processing code:
violations = await analyze_payment_code_compliance(
    file_paths=["src/card_processor.py"]
)
```

---

#### 8. `analyze_payment_provider_patterns`

**Purpose**: Analyze payment provider integration patterns

**When to use**:
- Reviewing provider integration code
- Need to identify provider-specific patterns or anti-patterns
- Want recommendations for integration improvements

**Identifies**:
- Provider-specific integration patterns
- Anti-patterns and code smells
- Best practices for provider APIs
- Improvement recommendations

**Parameters**:
- `file_paths` (List[str]): Files to analyze for provider patterns

**Returns**: `List[DomainPattern]` with detected patterns and recommendations

**Example use case**:
```
Analyze PayPal integration patterns:
patterns = await analyze_payment_provider_patterns(
    file_paths=["src/integrations/paypal.py"]
)
```

---

#### 9. `analyze_payment_architecture_constraints`

**Purpose**: Analyze architectural constraints for payment data flow

**When to use**:
- Reviewing data pipeline changes
- Need Bronze/Silver/Gold layer validation
- Want data immutability constraint checking

**Validates**:
- Bronze/Silver/Gold layer constraints
- Data immutability requirements
- Architectural pattern compliance
- Data flow correctness

**Parameters**:
- `file_paths` (List[str]): Files to analyze for architectural constraints

**Returns**: `List[ArchitecturalConstraint]` with constraint violations and validation rules

**Example use case**:
```
Validate Bronze layer data immutability:
constraints = await analyze_payment_architecture_constraints(
    file_paths=["notebooks/bronze/payment_events.py"]
)
```

---

#### 10. `analyze_payment_historical_issues`

**Purpose**: Analyze historical payment processing issues and lessons learned

**When to use**:
- Want to learn from past incidents
- Need to prevent known failure patterns
- Reviewing code similar to past issues

**Extracts**:
- Historical incidents and root causes
- Best practices from postmortems
- Prevention measures
- Lessons learned documentation

**Parameters**:
- `file_paths` (List[str]): Files to analyze for historical context

**Returns**: `List[HistoricalIssue]` with incidents and prevention measures

**Example use case**:
```
Check if changes might repeat historical payment retry issues:
issues = await analyze_payment_historical_issues(
    file_paths=["src/payment_retry.py"]
)
```

---

## Recommended Workflow

### Standard AI-Assisted Code Review Process:

1. **Gather Context with Automatic File Fetching** (Start Here):
   ```
   # Automatically fetches PR changed files - no manual file listing needed!
   context = get_code_analysis_context(
       pr_id=12345,
       org="msazure",
       project="One",
       repository="Commerce.PaymentsDataPlatform",
       depth="standard"
   )
   # context.files now contains the list of changed files from the PR
   ```

2. **Extract Domain Context** (If payment-related):
   ```
   # Use the auto-fetched files from step 1
   domain_context = get_payments_change_context(
       changed_files=context.files,
       context_type="patterns"
   )
   ```

3. **Analyze Quality Signals**:
   ```
   # Use the auto-fetched files from step 1
   signals = await get_code_quality_signals(
       file_paths=context.files,
       include_patterns=["security", "performance"]
   )
   ```

4. **Deep Domain Analysis** (If needed):
   ```
   # Use specialized payment tools with auto-fetched files:
   compliance = await analyze_payment_code_compliance(file_paths=context.files)
   patterns = await analyze_payment_provider_patterns(file_paths=context.files)
   constraints = await analyze_payment_architecture_constraints(file_paths=context.files)
   issues = await analyze_payment_historical_issues(file_paths=context.files)
   ```

5. **Generate and Post Comments**:
   ```
   # Based on your analysis, create CodeReviewComment objects
   comments = [...]
   
   # Post using PR URL (recommended)
   result = post_ai_comments_by_pr_url(
       pr_url="https://dev.azure.com/msazure/One/_git/Repo/pullrequest/12345",
       comments=comments,
       dry_run=False  # Set to True for validation only
   )
   ```

---

## Complete Workflow Example

Here's a complete end-to-end example demonstrating the auto-fetch workflow:

```python
# Step 1: Parse PR URL (if provided by developer)
from pdp_dev_mcp.tools.common.enhanced_repository_discovery import parse_azure_devops_pr_url

pr_url = "https://dev.azure.com/msazure/One/_git/Commerce.PaymentsDataPlatform/pullrequest/13665362"
org, project, repository, pr_id = parse_azure_devops_pr_url(pr_url)

# Step 2: Auto-fetch files and get analysis context
context = get_code_analysis_context(
    pr_id=int(pr_id),
    org=org,
    project=project,
    repository=repository,
    depth="comprehensive"
)

# Step 3: Files are automatically available - no manual listing needed!
print(f"Analyzing {len(context.files)} files: {context.files}")

# Step 4: Perform domain-specific analysis
domain_context = get_payments_change_context(
    changed_files=context.files,
    context_type="patterns"
)

# Step 5: Analyze code quality
signals = await get_code_quality_signals(
    file_paths=context.files,
    include_patterns=["security", "performance"]
)

# Step 6: Generate and post comments based on analysis
comments = [
    # Your AI-generated comments here
]

result = post_ai_comments_by_pr_url(
    pr_url=pr_url,
    comments=comments,
    dry_run=True  # Validate first
)
```

---

## Best Practices

⚠️ **Cross-Repository Review Warning**:
When reviewing PRs in other repositories:
- DO NOT reference documentation from your current workspace
- DO NOT assume patterns/docs exist in the target repository
- DO provide inline examples or point to publicly accessible references
- DO verify any documentation references exist in the target repo

### ✅ DO:
- **Start with `get_code_analysis_context`** - it's the single entry point that fetches files automatically
- **Use the auto-fetched `context.files`** throughout your workflow
- Provide all required parameters: `pr_id`, `org`, `project`, `repository`
- Use `post_ai_comments_by_pr_url` for easier comment posting
- Enable `dry_run=True` first to validate comments before posting
- Use domain tools for payment-specific deep analysis
- Let AI reason naturally - tools provide context, not prescriptions
- Leverage the complete workflow: parse PR URL → fetch context with files → analyze → comment

### ❌ DON'T:
- Don't skip `get_code_analysis_context` - it's required to get the file list
- Don't try to fetch files manually - the tool does it automatically
- Don't post without dry-run validation first
- Don't use prescriptive rigid rules - tools enable, not constrain
- Don't ignore domain tools for payment code reviews
- Don't forget self-praise filtering - it's automatic but important
- Don't omit required parameters (`org`, `project`, `repository`) - they're mandatory

---

## Comment Structure

### CodeReviewComment Dataclass:

```python
@dataclass
class CodeReviewComment:
    comment_id: str                    # Unique identifier
    comment_type: CommentType          # GENERAL, LINE, FILE, SECURITY, etc.
    severity: CommentSeverity          # INFO, SUGGESTION, WARNING, ERROR, CRITICAL
    title: str                         # Brief summary
    content: str                       # Detailed feedback
    file_path: Optional[str]           # For line/file comments
    line_number: Optional[int]         # For line-specific comments
    suggested_code: Optional[str]      # Code suggestion if applicable
    tags: List[str]                    # Categorization tags
    reasoning: Optional[str]           # AI reasoning for transparency
    business_impact: Optional[str]     # Business context
    metadata: dict                     # Additional context
```

### Enum Types:

**CommentType**: GENERAL, LINE, FILE, SUGGESTION, SECURITY, PERFORMANCE, DOMAIN

**CommentSeverity**: INFO, SUGGESTION, WARNING, ERROR, CRITICAL

---

## Self-Documentation Features

All tools include **runtime validation** and **enhanced error messages**:

1. **Runtime Enum Validation**: Invalid enum values caught immediately with clear guidance
2. **Enhanced Error Messages**: AGENT_GUIDANCE sections for common failures (401, 404, 403, 400)
3. **Dry-Run Validation**: Comprehensive validation without side effects

See BDD tests in `tests/tools/common/mcp_tool_documentation_test.py` for full specification.

---

## Tool Testing & Coverage

- **AI-Enabling Tools**: 89-98% test coverage
- **Comment Posting Tools**: 89% coverage with comprehensive error handling
- **Domain Tools**: Full BDD test coverage
- **Total**: 226+ tests across all code review tools

All tools follow BDD testing patterns documented in `.github/instructions/`.

---

## Additional Resources

- **Architecture Documentation**: `docs/AI_ENABLING_CODE_REVIEW_ARCHITECTURE.md`
- **Usage Guidance**: `docs/ai_comment_guidance.md`
- **BDD Test Specs**: `tests/tools/code_review/*_test.py`
- **Integration Examples**: `tests/integration/*_test.py`

---

## Summary

Use these 10 tools to perform intelligent, context-aware code reviews:
- **3 AI-enabling tools** provide context and quality signals
- **2 comment posting tools** deliver feedback (prefer `post_ai_comments_by_pr_url`)
- **5 domain tools** enable payment-specific deep analysis

The tools follow AI-enabling principles: they inform your reasoning without constraining it, enabling natural, intelligent code reviews enhanced by payment platform expertise.
