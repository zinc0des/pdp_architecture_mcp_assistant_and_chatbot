# AI Comment Posting - Usage Guidance

## Overview

The AI comment posting tool provides intelligent code review assistance that adapts its behavior based on the social context of the PR. This ensures professional and appropriate interactions.

## Behavior for Different Scenarios

### 🔄 Posting to Others' PRs

When providing AI assistance on someone else's PR:

**✅ All comments are posted to the PR:**
- ✨ Praise comments: "Excellent implementation! Great use of design patterns."
- 🔧 Constructive feedback: "Consider adding error handling for edge cases."
- ⚠️ Critical issues: "Security vulnerability: credentials should not be hardcoded."

**Result format:**
```python
result = post_ai_generated_comments(...)
# result.posted_comments = [all comments]
# result.local_praise_comments = []  # Empty
```

### 🏠 Posting to Your Own PR

When using AI assistance on your own PR to avoid awkward self-congratulation:

**📝 Posted to PR (visible to reviewers):**
- 🔧 Constructive feedback: "Consider adding error handling for edge cases."
- ⚠️ Critical issues: "Security vulnerability: credentials should not be hardcoded."
- 💡 Suggestions: "Performance could be improved with caching."

**📱 Shown locally only (private feedback):**
- ✨ Praise comments: "Excellent implementation! Great use of design patterns."
- 🏆 Positive feedback: "Outstanding test coverage! Well-structured code."
- 👏 Recognition: "Perfect adherence to team coding standards."

**Result format:**
```python
result = post_ai_generated_comments(...)
# result.posted_comments = [constructive feedback only]
# result.local_praise_comments = [praise comments for your reference]
```

## Usage Examples

### Basic Usage

```python
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_generated_comments,
    create_ai_comment,
)

# Create AI-generated comments
comments = [
    create_ai_comment(
        "praise_001",
        "Excellent Test Coverage",
        "🏆 Outstanding BDD tests! Comprehensive scenario coverage."
    ),
    create_ai_comment(
        "feedback_001", 
        "Error Handling",
        "Consider adding try-catch blocks for API calls."
    ),
]

# Post comments with intelligent filtering
result = post_ai_generated_comments(
    org="myorg",
    project="myproject", 
    repository="myrepo",
    pr_id=12345,
    comments=comments,
)

# Handle results based on context
print(f"Posted {result.successful_posts} comments to PR")

if result.local_praise_comments:
    print(f"\\n✨ Positive feedback for your reference:")
    for praise in result.local_praise_comments:
        print(f"  • {praise['title']}: {praise['content']}")
```

### Disabling Self-Praise Filtering

```python
# Force all comments to be posted (including praise on own PR)
result = post_ai_generated_comments(
    org="myorg",
    project="myproject",
    repository="myrepo", 
    pr_id=12345,
    comments=comments,
    filter_self_praise=False,  # Disable filtering
)
```

### Handling Results in AI Tools

```python
def display_ai_feedback(result: CommentPostingResult):
    """Display AI feedback appropriately based on context."""
    
    # Show comments posted to PR
    if result.posted_comments:
        print("🔄 Comments posted to PR for team review:")
        for comment in result.posted_comments:
            print(f"  • {comment['title']}")
    
    # Show local praise separately  
    if result.local_praise_comments:
        print("\\n✨ Positive feedback for your work:")
        for praise in result.local_praise_comments:
            print(f"  🏆 {praise['title']}")
            print(f"     {praise['content']}")
    
    # Show any failures
    if result.failures:
        print("\\n⚠️ Some comments could not be posted:")
        for failure in result.failures:
            print(f"  • {failure['comment_id']}: {failure['error']}")

# Usage
result = post_ai_generated_comments(...)
display_ai_feedback(result)
```

## Best Practices

### For AI Tool Developers

1. **Always check `local_praise_comments`** - Don't let valuable positive feedback disappear
2. **Display context appropriately** - Make it clear what was posted vs. shown locally
3. **Preserve user choice** - Allow users to disable filtering if desired
4. **Handle failures gracefully** - Show users what couldn't be posted and why

### For Users

1. **Review local praise** - Use positive feedback to understand what you did well
2. **Focus on posted feedback** - Address constructive comments visible to the team
3. **Consider context** - Filtering helps maintain professional appearance on PRs

## Implementation Details

The tool automatically:

- 🔍 **Detects praise** using pattern matching (words like "excellent", "outstanding", emojis like 🏆)
- 👤 **Identifies PR authorship** by comparing current user with PR creator
- 🎯 **Routes appropriately** based on social context
- 📊 **Provides clear results** showing what was posted vs. displayed locally

This ensures AI assistance enhances rather than disrupts professional code review workflows.