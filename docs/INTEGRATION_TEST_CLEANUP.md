# Integration Test Comment Cleanup

This document describes the test comment cleanup system for `pdp-dev-mcp` integration tests.

## Problem

Integration tests for Azure DevOps comment posting write test comments to actual PRs. Over time, this accumulates many test comments in the PR, making it cluttered and harder to review real feedback.

## Solution

A comprehensive test comment cleanup system that:

1. **Automatically cleans up test comments before integration tests run**
2. **Provides manual cleanup scripts for on-demand cleaning**
3. **Uses pattern matching to identify test comments safely**
4. **Supports dry-run mode for safe testing**

## Components

### 1. Test Comment Cleanup Module

**File**: `tests/integration/test_comment_cleanup.py`

Core functionality for identifying and removing test comments:

- `TestCommentCleanupConfig`: Configuration class for cleanup operations
- `TestCommentCleaner`: Main class that handles comment identification and removal
- `cleanup_integration_test_comments()`: Convenience function for simple cleanup

**Test Comment Identification Patterns**:
- `🧪 **INTEGRATION TEST**` - Main integration test marker
- `🔬 **MCP Tool Test**` - MCP tool specific tests
- `*Test ID:` - Test ID markers
- `integration-test` - Tag-based identification
- `mcp-test` - MCP test tags
- `*This is an automated test comment` - Explicit automation markers

### 2. Pytest Fixtures

**File**: `tests/conftest.py`

Pytest fixtures for automatic cleanup:

- `cleanup_integration_test_comments`: Session-scoped fixture that runs cleanup before and after test sessions
- `test_pr_config`: Provides centralized PR configuration for all integration tests

**Usage in tests**:
```python
@pytest.mark.integration
class TestSomething:
    def test_something(self, cleanup_integration_test_comments, test_pr_config):
        # Test runs with clean PR comments
        # Uses standardized PR config
        pass
```

### 3. Manual Cleanup Script

**File**: `.copilot/scripts/cleanup_test_comments.py`

Standalone script for manual cleanup operations:

```bash
# Clean up test comments from default PR
python .copilot/scripts/cleanup_test_comments.py

# Clean up from specific PR
python .copilot/scripts/cleanup_test_comments.py --pr-id 13845550

# Dry run to see what would be cleaned
python .copilot/scripts/cleanup_test_comments.py --pr-id 13844374 --dry-run

# Clean up with additional patterns
python .copilot/scripts/cleanup_test_comments.py --additional-patterns "custom-test" "debug-comment"
```

## Configuration

### Default Test PR Configuration

The system uses a centralized configuration for the test PR:

```python
TEST_CONFIG = {
    "org": "microsoft",
    "project": "Universal Store", 
    "repository": "Commerce.PaymentsDataPlatform",
    "pr_id": 13844374,  # Main test PR ID
}
```

This configuration is used by:
- Pytest fixtures in `conftest.py`
- Integration tests that use `test_pr_config` fixture
- Default values in the manual cleanup script

### Changing the Test PR

To change the test PR used across all integration tests:

1. Update `TEST_CONFIG` in `tests/conftest.py`
2. Update the default `--pr-id` in `.copilot/scripts/cleanup_test_comments.py`
3. Update any hardcoded PR IDs in individual test files

## Integration Test Updates

Updated integration tests to use the new cleanup system:

### Before
```python
def test_something(self):
    tester = TestAIAgentsCanPostCommentsToAzureDevOps(
        org="microsoft",
        project="Universal Store", 
        repository="Commerce.PaymentsDataPlatform",
        pr_id=13844374,
    )
```

### After
```python
def test_something(self, cleanup_integration_test_comments, test_pr_config):
    tester = TestAIAgentsCanPostCommentsToAzureDevOps(
        org=test_pr_config["org"],
        project=test_pr_config["project"],
        repository=test_pr_config["repository"],
        pr_id=test_pr_config["pr_id"],
    )
```

## Benefits

1. **Clean Test Environment**: Each test run starts with a clean PR, removing stale test comments
2. **Centralized Configuration**: Easy to change test PR across all tests
3. **Safety**: Pattern-based identification ensures only test comments are removed
4. **Flexibility**: Supports both automatic and manual cleanup
5. **Debugging**: Dry-run mode allows safe testing of cleanup logic
6. **Extensibility**: Easy to add new test comment patterns

## Usage Examples

### Running Integration Tests
```bash
# Tests will automatically clean up comments before running
pytest tests/integration/ -m integration
```

### Manual Cleanup
```bash
# Quick cleanup of current test PR  
python .copilot/scripts/cleanup_test_comments.py

# Cleanup specific PR with dry run
python .copilot/scripts/cleanup_test_comments.py --pr-id 13845550 --dry-run

# See what test comments exist
python .copilot/scripts/cleanup_test_comments.py --dry-run
```

### Adding New Test Comment Patterns

To identify new types of test comments, add patterns to the default list in `TestCommentCleanupConfig`:

```python
test_comment_patterns: List[str] = [
    "🧪 **INTEGRATION TEST**",
    "🔬 **MCP Tool Test**", 
    "*Test ID:",
    "integration-test",
    "mcp-test",
    "*This is an automated test comment",
    "YOUR_NEW_PATTERN",  # Add here
]
```

## Safety Features

- **Pattern-based identification**: Only removes comments matching test patterns
- **Dry-run support**: Test cleanup logic without actually removing comments
- **Detailed logging**: Shows exactly what comments are being processed
- **Error handling**: Graceful handling of network issues and API errors
- **Result reporting**: Comprehensive results showing success/failure counts

## Troubleshooting

### Authentication Issues
Ensure Azure CLI is logged in and has access to the Azure DevOps organization:
```bash
az login
az devops configure --defaults organization=https://dev.azure.com/microsoft
```

### Permission Issues
Verify the account has permission to:
- Read PR comments
- Update/resolve PR comment threads
- Access the specific repository and project

### Pattern Matching Issues
Use dry-run mode to verify patterns are working correctly:
```bash
python .copilot/scripts/cleanup_test_comments.py --dry-run
```

This will show which comments would be identified as test comments without actually removing them.