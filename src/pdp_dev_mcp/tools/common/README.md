# Repository Context Management System

## Overview

The Repository Context Management System provides session-level repository context for Azure DevOps MCP tools, enabling consistent operations across multi-repo workspaces with performance optimization through caching.

## Architecture

### Core Components

- **`RepositoryContext` Class**: Thread-safe singleton managing global repository state
- **Context Management Tools**: MCP tools for setting, checking, and clearing repository context
- **Enhanced Tool Integration**: Updated Azure DevOps tools support both global context and explicit overrides

### Key Features

- **Global Session Context**: Set repository context once, use across all subsequent tool calls
- **Thread-Safe Operations**: Concurrent tool usage with proper locking mechanisms
- **Intelligent Caching**: Cached repository information for performance optimization
- **Explicit Override Support**: Override global context for multi-repo operations
- **Debugging Visibility**: Tools to inspect current context state and cache status

## Usage Patterns

### 1. Global Context Pattern (Recommended for focused work)

```python
# Set repository context at session start
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT")

# All tools automatically use the cached context
setup = azure_devops_workflow_setup()  # Uses PMT repository
analysis = azure_devops_pr_comment_analysis(pr_id=13483931)  # Uses PMT repository
resolution = azure_devops_resolve_pr_comments(13483931, ["thread_1", "thread_2"])
```

### 2. Explicit Override Pattern (Recommended for multi-repo)

```python
# Work with different repositories explicitly without setting global context
pmt_setup = azure_devops_workflow_setup(
    working_directory="/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT"
)
bin_setup = azure_devops_workflow_setup(
    working_directory="/Users/user/src/Microsoft/CFS-Payments-DataPlatform-BIN"
)
```

### 3. Context Switching Pattern

```python
# Start with PMT repository
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-PMT")
pmt_analysis = azure_devops_pr_comment_analysis(pr_id=13483931)

# Switch to BIN repository
set_repository_context("/Users/user/src/Microsoft/CFS-Payments-DataPlatform-BIN")
bin_analysis = azure_devops_pr_comment_analysis(pr_id=13500000)
```

## Tool Reference

### Context Management Tools

#### `set_repository_context(working_directory: str)`
Set the active repository context for subsequent operations.

**Parameters:**
- `working_directory`: Absolute path to repository directory

**Returns:**
- Success status with repository information and cache timestamp
- Error details if repository discovery fails

#### `get_repository_context_status()`
Get current repository context status and debugging information.

**Returns:**
- Context status including active repository, cache timestamp, and metadata
- Cache availability and context source information

#### `clear_repository_context()`
Clear the current repository context and cache.

**Returns:**
- Status of clear operation with previous context information
- Timestamp of when context was cleared

### Enhanced Azure DevOps Tools

All Azure DevOps tools now support the `working_directory` parameter for explicit overrides:

- `azure_devops_workflow_setup(working_directory=None)`
- `azure_devops_pr_comment_analysis(pr_id, save_to_file=True, working_directory=None)`
- `azure_devops_repository_discovery(working_directory=None)`

## Implementation Details

### RepositoryContext Class

```python
class RepositoryContext:
    """Global repository context manager for MCP tools."""
    
    _current_working_directory: Optional[str] = None
    _cached_repo_info: Optional[Dict[str, Any]] = None
    _cache_timestamp: Optional[str] = None
    _lock = Lock()
```

### Thread Safety

- Global state protected by `threading.Lock`
- Atomic operations for context switching
- Safe concurrent access across multiple tool calls

### Caching Strategy

- Repository information cached after successful discovery
- Cache invalidated when context changes
- Fresh discovery for explicit overrides
- Intelligent fallback to discovery when no context set

### Error Handling

- Graceful fallback to intelligent discovery if no context set
- Clear error messages with actionable suggestions
- Validation of working directory paths and repository structure

## Benefits

### Performance
- **Eliminated Repeated Discovery**: Repository discovery only happens once per context
- **Cached Repository Information**: Instant access to organization, project, repository details
- **Reduced Azure CLI Calls**: Minimize expensive subprocess operations

### Developer Experience
- **Consistent Context**: All tools work with same repository throughout session
- **Clear Error Messages**: Actionable feedback when repository context issues occur
- **Debugging Visibility**: Tools to inspect and understand current context state

### Multi-Repo Support
- **Workspace Flexibility**: Easy switching between repositories in complex workspaces
- **Explicit Override Capability**: Work with multiple repositories in single session
- **Context Isolation**: Clean separation between different repository operations

## Migration Guide

### From v0.2.1 to v0.2.2

**Before (v0.2.1):**
```python
# Tools required working_directory parameter or used current directory
setup = azure_devops_workflow_setup()  # Used current directory
analysis = azure_devops_pr_comment_analysis(pr_id=123)  # Used current directory
```

**After (v0.2.2):**
```python
# Option 1: Set global context (recommended for focused work)
set_repository_context("/path/to/repository")
setup = azure_devops_workflow_setup()  # Uses cached context
analysis = azure_devops_pr_comment_analysis(pr_id=123)  # Uses cached context

# Option 2: Use explicit overrides (recommended for multi-repo)
setup = azure_devops_workflow_setup(working_directory="/path/to/repository")
analysis = azure_devops_pr_comment_analysis(pr_id=123, working_directory="/path/to/repository")
```

### Backward Compatibility

- All existing tool calls continue to work without changes
- Intelligent discovery still works when no context is set
- Explicit `working_directory` parameters always take precedence
- No breaking changes to existing workflows

## Troubleshooting

### Common Issues

**Issue**: Tools report "No repository context set" error
**Solution**: Use `set_repository_context()` to establish context before calling tools

**Issue**: Tools use wrong repository in multi-repo workspace  
**Solution**: Use explicit `working_directory` parameters or switch context with `set_repository_context()`

**Issue**: Cached context becomes stale after repository changes
**Solution**: Use `clear_repository_context()` to force fresh discovery

### Debugging Commands

```python
# Check current context status
status = get_repository_context_status()
print(f"Context set: {status['context_set']}")
print(f"Current repository: {status.get('repository', 'None')}")
print(f"Cache timestamp: {status.get('cache_timestamp', 'None')}")

# Clear context if issues persist
clear_repository_context()
```

## Version History

- **v0.2.2**: Repository context management system introduced
- **v0.2.1**: Enhanced repository discovery with modern Azure DevOps support
- **v0.2.0**: Basic Azure DevOps workflow tools implementation