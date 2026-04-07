# Azure DevOps AI-Assisted Development Workflow

This guide documents the proven AI-assisted development workflow for AI agents using the MCP server. This workflow dramatically improves code quality and development efficiency through AI-human collaboration.

**Note**: This guide uses dedicated MCP tools that implement the Azure DevOps workflow patterns as first-class functions, providing one-click execution of complex multi-step processes.

## 🚀 Quick Reference - MCP Tools

**Repository Context Management:**
- `set_repository_context(working_directory)` - Set global repository context for multi-repo workspaces
- `get_repository_context_status()` - Check current repository context and cache status
- `clear_repository_context()` - Clear global context and force fresh discovery

**Core Workflow Tools:**
- `azure_devops_workflow_setup(working_directory=None)` - Complete setup: discover repo, establish parameters, list PRs
- `azure_devops_pr_comment_analysis(pr_id, working_directory=None)` - Analyze all PR feedback with detailed summaries
- `azure_devops_resolve_pr_comments(pr_id, thread_ids)` - Resolve comment threads after implementation
- `azure_devops_repository_discovery(working_directory=None)` - Auto-discover repository context from git

**Multi-Repo Workspace Usage Pattern:**
```python
# 1. Set repository context for consistent operations
set_repository_context("/path/to/your/repository")

# 1. Setup everything (uses cached context)
setup = azure_devops_workflow_setup()

# 2. Analyze PR comments (uses cached context)
analysis = azure_devops_pr_comment_analysis(pr_id=13577785)

# 3. After implementing fixes, resolve comments
thread_ids = [comment["thread_id"] for comment in analysis["active_comments"]]
resolution = azure_devops_resolve_pr_comments(13577785, thread_ids, status="fixed")
```

**Single-Repo or Explicit Override Usage:**
```python
# 1. Setup with explicit directory (overrides any global context)
setup = azure_devops_workflow_setup(working_directory="/path/to/specific/repo")

# 2. Analyze PR comments with explicit directory
analysis = azure_devops_pr_comment_analysis(pr_id=13577785, working_directory="/path/to/specific/repo")

# 3. Resolution works with cached information from previous calls
thread_ids = [comment["thread_id"] for comment in analysis["active_comments"]]
resolution = azure_devops_resolve_pr_comments(13577785, thread_ids, status="fixed")
```

## 🚀 The Complete Workflow

### Phase 1: Initial Development
- **Use MCP Tools**: Leverage AI assistance for rapid code generation and exploration. Utilize tools like `kusto_execute_query` for data validation and schema tools to ensure data integrity.
- **Data-Driven Approach**: Implement a data-driven development strategy by integrating data validation early in the process.
- **Follow Standards**: Establish a proper directory structure and adhere to naming conventions to maintain consistency.
- **Write Tests**: Develop comprehensive test coverage from the start to catch potential issues early.

### Phase 2: Pull Request Creation
- **Create PR Early**: Initiate pull requests early in the development process to incorporate AI feedback and improve code iteratively.
- **Clear Documentation**: Craft descriptive PR titles and detailed descriptions to facilitate understanding and review.
- **Link Work Items**: Connect PRs to relevant Azure DevOps work items to maintain traceability and context.
- **Enable Automation**: Set up CI/CD pipelines and automated policy checks to streamline the integration process.

### Phase 3: AI Review (The Magic ✨)
- **Automatic Trigger**: AI systems automatically review PRs shortly after creation, providing timely feedback.
- **Typical Output**: Expect 2-4 targeted, actionable suggestions per PR, focusing on areas such as logic gaps and unused parameters.
- **Focus Areas**: AI identifies validation opportunities and best practices, offering improvement-focused insights.
- **Quality**: AI comments are designed to be insightful and drive meaningful improvements.

### Phase 4: AI Feedback Analysis & Implementation
- **Retrieve Feedback**: Use `azure_devops_pr_comment_analysis(pr_id)` to gather all PR comments with detailed analysis.
- **Prioritize Critical Issues**: Address functional improvements first, such as unused function parameters or missing input validation.
- **Example Critical Issues**:
  - Unused function parameters in scoring logic
  - Missing input validation
  - Logic gaps in business rules
  - Opportunities for enhanced functionality

### Phase 5: Iterative Enhancement
- **Implement Fixes**: Make targeted commits to address AI suggestions, focusing on enhancing functionality.
- **Document Changes**: Use clear commit messages that reference AI feedback to maintain a record of changes.
- **Test Enhancements**: Ensure that all improvements are thoroughly tested and validated.
- **Update PR**: Keep the PR description updated with any changes made to reflect the current state of the code.
- **Resolve Comments**: Use `azure_devops_resolve_pr_comments(pr_id, thread_ids)` to programmatically resolve comment threads after addressing them.

### Phase 5.5: Comment Resolution (New!)
- **Programmatic Resolution**: Use `azure_devops_resolve_pr_comments(pr_id, thread_ids, status="fixed")` to resolve comments after implementation
- **Status Options**: Set thread status to `"fixed"`, `"wontFix"`, `"byDesign"`, or `"closed"`
- **Batch Operations**: Resolve multiple AI suggestions efficiently with the `thread_ids` list parameter
- **Dry-Run Support**: Use `dry_run=True` to validate resolution plans before execution
- **Documentation Trail**: Maintain clear record of which AI suggestions were addressed and how

### Phase 6: Human Review & Deployment
- **Clean Code Review**: Present human reviewers with AI-enhanced code, reducing the number of review cycles needed.
- **Higher Quality**: Benefit from fewer review cycles due to the pre-review improvements made by AI.
- **Team Learning**: Share AI improvement patterns with the team to foster collective learning.
- **Production Ready**: Achieve a production-ready state through effective AI-human collaboration.

## 🏢 Multi-Repo Workspace Management

### Repository Context Management (v0.2.2+)

The MCP tools now support **repository context management** for consistent operations across multi-repo workspaces. This eliminates the need for repeated repository discovery and ensures all tools work with the correct repository context.

#### Key Benefits:
- **Performance**: Cached repository information avoids repeated discovery operations
- **Consistency**: All tools use the same repository context throughout a session
- **Multi-Repo Support**: Easy switching between repositories in complex workspaces
- **Thread Safety**: Safe concurrent operations with proper locking

#### Usage Patterns:

**Pattern 1: Set Global Context (Recommended for focused work)**
```python
# Set repository context once at the beginning of your session
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT")

# All subsequent tools use the cached context automatically
setup = azure_devops_workflow_setup()  # Uses PMT repository
analysis = azure_devops_pr_comment_analysis(pr_id=13483931)  # Uses PMT repository
```

**Pattern 2: Explicit Override (Recommended for multi-repo operations)**
```python
# Work with different repositories explicitly
pmt_setup = azure_devops_workflow_setup(
    working_directory="/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT"
)
bin_setup = azure_devops_workflow_setup(
    working_directory="/Users/user/src/Microsoft/CFS-Payments-DataPlatform-BIN"
)
```

**Pattern 3: Context Switching**
```python
# Work with PMT repository
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT")
pmt_analysis = azure_devops_pr_comment_analysis(pr_id=13483931)

# Switch to BIN repository
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-BIN")
bin_analysis = azure_devops_pr_comment_analysis(pr_id=13500000)

# Check current context
status = get_repository_context_status()
```

#### Context Management Tools:

- **`set_repository_context(working_directory)`**: Set global repository context
- **`get_repository_context_status()`**: Check current context and cache status  
- **`clear_repository_context()`**: Clear context and force fresh discovery

#### Debugging and Visibility:

```python
# Check what repository context is currently active
status = get_repository_context_status()
print(f"Active repository: {status['repository']}")
print(f"Context timestamp: {status['cache_timestamp']}")

# Clear context if needed
clear_repository_context()
```

## 📊 Real-World Example: DQ Tools Enhancement (PR #13577785)

### MerlinBot's Actual Feedback (3 Medium Severity Issues):

#### 1. **Pattern Matching Enhancement** (Reliability: Correctness)
```python
# Original Issue: Simple substring matching without word boundaries
json_matches = sum(1 for pattern in json_patterns if pattern in use_case_lower)

# MerlinBot's Suggestion: Use regex with word boundaries  
json_matches = sum(1 for pattern in json_patterns if re.search(rf'\b{pattern}\b', use_case_lower))
```

#### 2. **Documentation Quality** (Readability: Documentation Quality)
- **Issue**: Phase headers lacked detailed, actionable content
- **Enhancement**: Added comprehensive step-by-step guidance for each workflow phase
- **Result**: Developers now get specific, practical instructions instead of high-level bullet points

#### 3. **JSON Parsing Robustness** (Reliability: Data Handling)  
```bash
# Original: Fragile grep/sed parsing
REPO_ID=$(echo "$REPO_INFO" | grep '"id":' | head -1 | sed 's/.*"id": "\([^"]*\)".*/\1/')

# Enhanced: Robust Python JSON parser fallback
REPO_ID=$(echo "$REPO_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
```

### Implementation Results:
- **All Tests Passing**: 75/75 with 100% coverage maintained
- **Enhanced Functionality**: More accurate pattern matching, better documentation, robust parsing
- **Comments Resolved**: All 3 AI threads resolved programmatically via `azure_devops_resolve_pr_comments()` tool
- **Production Ready**: Enterprise-grade reliability improvements implemented

## 🔧 Essential Azure DevOps MCP Tools

### 🔍 Repository Discovery and Setup
```
azure_devops_repository_discovery()
```
**Purpose**: Automatically discover Azure DevOps organization, project, and repository information from the current git repository. Handles both dev.azure.com and legacy visualstudio.com URLs.

**Returns**: Repository context including organization, project, repository names, and setup status.

```
azure_devops_workflow_setup()
```
**Purpose**: Complete end-to-end workflow setup - discovers repository, establishes parameters, and lists current PRs. This is typically the first step in any Azure DevOps AI workflow.

**Returns**: Comprehensive setup status, repository context, and available PRs for further workflow operations.

### 📋 Basic PR Operations
```
# Basic Azure CLI operations (still useful for direct CLI work)
az repos pr list --output table
az repos pr show --id <PR_ID>
az repos pr update --id <PR_ID> --description "Updated description"

# MCP authentication tools
azure_auth-get_auth_state
azure_auth-get_current_tenant
az account show  # Alternative CLI check
```

### 🎯 Get All PR Comments and Reviews (Including AI Feedback)

```
azure_devops_pr_comment_analysis(pr_id, save_to_file=True)
```
**Purpose**: Analyze all comments on an Azure DevOps pull request. Automatically discovers repository context and retrieves PR comments with robust parsing.

**Parameters**:
- `pr_id`: The pull request ID to analyze
- `save_to_file`: Whether to save full JSON response to file for detailed analysis

**Returns**: 
- Detailed comment analysis including active/fixed thread counts
- Content summaries of all comments
- Thread IDs for resolution operations
- Repository context information

**Example Output**:
```json
{
  "success": true,
  "pr_id": 13577785,
  "comment_summary": {
    "total_threads": 5,
    "active_threads": 3,
    "fixed_threads": 2,
    "active_percentage": 60.0
  },
  "active_comments": [
    {
      "thread_id": "123456",
      "author": "AI Assistant",
      "content_preview": "Consider using word boundaries in regex...",
      "created_date": "2025-08-21T10:30:00Z"
    }
  ],
  "resolution_ready": false
}
```

### 🎯 Resolve AI Comments

```
azure_devops_resolve_pr_comments(pr_id, thread_ids, status="fixed", dry_run=False)
```
**Purpose**: Programmatically resolve Azure DevOps PR comment threads after implementing feedback. Supports batch resolution and dry-run mode for validation.

**Parameters**:
- `pr_id`: The pull request ID
- `thread_ids`: List of comment thread IDs to resolve (from `azure_devops_pr_comment_analysis`)
- `status`: Resolution status - `"fixed"`, `"wontFix"`, `"byDesign"`, or `"closed"`
- `dry_run`: If True, show what would be resolved without making changes

**Example Usage**:
```python
# First, analyze comments to get thread IDs
result = azure_devops_pr_comment_analysis(13577785)
thread_ids = [comment["thread_id"] for comment in result["active_comments"]]

# Dry-run to validate the resolution plan
plan = azure_devops_resolve_pr_comments(13577785, thread_ids, dry_run=True)

# Execute the resolution
resolution = azure_devops_resolve_pr_comments(13577785, thread_ids, status="fixed")
```

**Example Output**:
```json
{
  "success": true,
  "pr_id": 13577785,
  "resolution_status": "fixed",
  "total_threads": 3,
  "successful_resolutions": 3,
  "failed_resolutions": 0,
  "summary": "Resolved 3/3 threads with status 'fixed'"
}
```

### 🚀 Quick Setup

```
azure_devops_workflow_setup()
```
**Purpose**: Complete Azure DevOps workflow setup in one command. Discovers repository, establishes parameters, and lists current PRs.

**Example Output**:
```json
{
  "success": true,
  "setup_complete": true,
  "repository_context": {
    "organization": "microsoft",
    "project": "Universal Store",
    "repository": "Commerce.PaymentsDataPlatform",
    "org_url": "https://dev.azure.com/microsoft",
    "current_branch": "feature-branch"
  },
  "workflow_ready": true,
  "pr_overview": {
    "total_prs": 5,
    "current_branch_prs": 1,
    "recent_prs": [
      {
        "id": 13577785,
        "title": "DQ Tools Enhancement",
        "status": "Active",
        "created_by": "Developer",
        "source_branch": "feature-branch"
      }
    ]
  },
  "workflow_ready": true,
  "next_steps": [
    "Use azure_devops_pr_comment_analysis(pr_id) to analyze specific PR comments",
    "Use azure_devops_resolve_pr_comments(pr_id, thread_ids) to resolve AI feedback"
  ]
}
```

### 🤖 Azure DevOps Workflow MCP Tools

**Core Azure DevOps Workflow Tools:**
```
azure_devops_repository_discovery()    # Auto-discover repository context
azure_devops_workflow_setup()          # Complete workflow setup
azure_devops_pr_comment_analysis()     # Analyze all PR feedback
azure_devops_resolve_pr_comments()     # Resolve comment threads
```

**Additional Azure MCP Tools:**
```
# Authentication and account management
azure_auth-get_auth_state              # Check current authentication status
azure_auth-get_current_tenant          # Get current tenant information
azure_auth-get_selected_subscriptions  # List selected subscriptions
azure_auth-open_subscription_picker    # Open subscription picker UI

# Resource discovery and management
azure_resources-query_azure_resource_graph  # Query resources using Azure Resource Graph
```

### 🚨 Troubleshooting

**If Azure DevOps workflow MCP tools are not available:**
1. **Session State Issue**: If tools like `azure_devops_workflow_setup()` or `azure_devops_pr_comment_analysis()` are not accessible, this is typically a session initialization issue
   - **Solution**: Open a new Copilot chat session to reinitialize MCP server connections
   - **Cause**: MCP servers may not load if the session started before the server was ready
   - **Note**: This is a known MCP/VS Code integration behavior, not a code or configuration bug

**If MCP tools fail during execution:**
1. **Check Authentication**:
   - MCP tool: `azure_auth-get_auth_state`
   - Azure CLI: `az account show`
2. **Verify Repository Context**: Use `azure_devops_repository_discovery()` to validate repository detection
3. **Check Repository Access**: `az repos list`
4. **Tool-Specific Issues**: All Azure DevOps workflow tools provide detailed error messages and context

**Common Issues**:
- ✅ **Tools Not Available**: Open a new Copilot session to reload MCP servers
- ✅ **Repository Not Recognized**: Ensure you're in a git repository with Azure DevOps remote
- ✅ **Authentication Expired**: Use `az login` to refresh authentication
- ✅ **Project Access**: Verify you have access to the Azure DevOps project
- ✅ **Tool Timeouts**: Network connectivity issues may cause subprocess timeouts

## 💡 Best Practices for AI Review Success

### Code Structure for AI Review:
1. **Clear Parameter Usage**: Every function parameter should serve a purpose
2. **Logical Flow**: Structure code for easy AI pattern recognition
3. **Comprehensive Docs**: Include clear docstrings and comments
4. **Testable Design**: Write code that's easy to validate and enhance

### Team Collaboration:
1. **Share AI Patterns**: Document successful AI suggestions for team learning
2. **Focus on Function**: Prioritize AI suggestions that enhance functionality
3. **Document Learnings**: Capture workflow insights in team documentation
4. **Iterative Mindset**: Embrace the AI feedback loop as part of development

### Quality Maintenance:
1. **Let It Cook**: After addressing AI feedback, allow time for human review
2. **Test Thoroughly**: Validate all AI-suggested enhancements
3. **Maintain Standards**: Keep existing quality standards while embracing AI improvements
4. **Continuous Learning**: Each cycle improves both code and developer skills

## 🎯 Expected Outcomes

### Development Efficiency:
- **Faster Initial Development**: MCP tools accelerate code generation
- **Higher Quality First Drafts**: AI catches issues early in the process
- **Reduced Review Cycles**: Human reviewers see cleaner, pre-improved code
- **Enhanced Functionality**: AI suggestions often improve beyond original scope

### Code Quality Improvements:
- **Logic Gap Detection**: AI catches unused parameters and incomplete implementations
- **Best Practice Enforcement**: Consistent application of coding standards
- **Enhanced Test Coverage**: AI suggestions often improve testing approaches
- **Documentation Quality**: Better comments and clearer code structure

### Team Benefits:
- **Knowledge Sharing**: AI suggestions become learning opportunities for the entire team
- **Consistency**: Standardized approach to code quality and review
- **Efficiency**: Less time spent on basic issues, more on architecture and innovation
- **Quality Culture**: AI-human collaboration raises overall development standards

## 🚀 Getting Started

1. **Set Up Azure DevOps Access**: Ensure `az` command is authenticated with your credentials
2. **Create Your First AI-Enhanced PR**: Start with any feature or fix
3. **Wait for MerlinBot**: Usually provides feedback within 5-10 minutes
4. **Address AI Feedback**: Focus on critical/functional improvements first
5. **Document the Experience**: Share learnings with your team
6. **Iterate and Improve**: Each cycle teaches you more about effective AI collaboration

## 🔄 **Alternative Workflow: Human Review First**

**Real-World Example from PR #13577785**: Sometimes human reviewers provide feedback before AI systems, creating a different but equally effective workflow:

### **Modified Phase Sequence:**
1. **📤 Create PR**: Submit comprehensive technical work for review
2. **👥 Human Review**: Team lead (Noam) provides architectural guidance 
3. **🔧 Address Human Feedback**: Implement structural/naming changes requested
4. **🤖 AI Enhancement**: Continue with MerlinBot integration as available
5. **✅ Resolution**: Programmatically resolve all comment threads

### **Key Learnings:**
- **✅ Flexibility**: Workflow adapts to review timing and team availability
- **✅ Comprehensive Resolution**: Address all feedback sources (human + AI) systematically  
- **✅ Proactive Implementation**: Major refactoring can address feedback before it's formally requested
- **✅ Documentation Value**: Update workflow guides based on real experience

### **Technical Implementation:**
Use the Azure DevOps workflow MCP tools for streamlined implementation:

1. **Complete Setup**: `azure_devops_workflow_setup()` - discovers repository, establishes parameters, lists PRs
2. **Analyze Feedback**: `azure_devops_pr_comment_analysis(pr_id)` - get all comments with detailed analysis
3. **Resolve Comments**: `azure_devops_resolve_pr_comments(pr_id, thread_ids)` - programmatically resolve threads

**Benefits of MCP Tools**:
- ✅ **One-Click Operations**: Complex multi-step processes become single function calls
- ✅ **Universal Compatibility**: Works across Windows/Linux/macOS without platform-specific code
- ✅ **Error Handling**: Comprehensive error messages and fallback strategies
- ✅ **Robust Parsing**: Handles JSON with control characters and various Azure DevOps URL formats

## 🏆 Success Metrics

This workflow has proven effective for:
- ✅ **100% Test Coverage** maintained through AI-enhanced development (75/75 tests passing)
- ✅ **AI Feedback Resolution** with functional enhancements beyond bug fixes (using `azure_devops_resolve_pr_comments()`)
- ✅ **Reduced Human Review Cycles** due to clean, AI-improved code
- ✅ **Enhanced Functionality** beyond original requirements through AI suggestions
- ✅ **Team Adoption** of AI-assisted development patterns
- ✅ **Programmatic Comment Resolution** via MCP tools
- ✅ **Real-World Validation** demonstrated in PR #13577785 with DQ tools migration

### 📈 **Measurable Outcomes from PR #13577785**
- **Code Quality**: Medium severity issues addressed (pattern matching, documentation, robustness)
- **Test Coverage**: 435 statements with 0 missing coverage across all modules
- **AI Integration**: Successfully resolved 3 AI suggestions using `azure_devops_resolve_pr_comments()`
- **Enhanced Features**: Word boundary pattern matching, comprehensive workflow documentation, robust JSON parsing
- **Enterprise Ready**: Production-grade reliability improvements implemented

---

**Remember**: This isn't just about fixing bugs - it's about leveraging AI to enhance functionality and create better software through human-AI collaboration! 🎉
