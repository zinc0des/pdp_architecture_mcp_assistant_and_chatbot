# PDP Development MCP Server

A specialized Model Context Protocol (MCP) server for Payments Data Platform development, with comprehensive data quality tools and Azure DevOps workflow automation.

### ✨ What can you do with the PDP Development MCP Server?
Here are some development workflow prompts you can try:

### 🧪 Data Quality Development
- "Generate a PySpark test to validate transaction completeness for the PaymentTransactions table"
- "Create JSON DQ Framework rules for monitoring null values in critical payment fields"
- "Help me choose between PySpark tests and JSON rules for complex statistical validation"
- "Analyze my test file for PDP compliance standards and suggest improvements"

### 🚀 Azure DevOps Workflow Automation
- "Set up my Azure DevOps environment and show me current PRs"
- "Analyze PR comments for my current branch and identify what needs to be resolved"
- "Help me understand the feedback patterns in PR 12345"
- "Resolve all addressed comment threads in my PR"

### 📋 Architecture & Standards Guidance
- "Should I use PySpark tests or JSON DQ Framework rules for this validation scenario?"
- "What's the best directory structure for my data quality tests?"
- "Help me understand the dual-path data quality architecture"

## Getting Started

### Prerequisites
1. Install either the stable or Insiders release of VS Code:
   * [💫 Stable release](https://code.visualstudio.com/download)
   * [🔮 Insiders release](https://code.visualstudio.com/insiders)
2. Complete GitHub EMU enrollment at [aka.ms/github/copilot](https://aka.ms/github/copilot).
3. Install the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) and [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extensions
4. Install and authenticate with Azure CLI:
   * [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
   * Run `az login` to authenticate with your Azure account
5. Make sure you have [Python 3.10+](https://www.python.org/downloads/) installed properly and added to your PATH.

### 🔧 Install

#### ⚠️ One Click Install Issue

**Root Cause:** VS Code security filters block install URLs containing `#subdirectory=` parameters for security reasons.

**Current Status:** The `uvx` command works perfectly, but the 1-click install button is blocked by VS Code's URL filtering. Please use the manual installation method below.

#### ✅ Recommended Installation

#### Manual Installation

Follow the MCP install [guide](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server), use one of the following configs:

**Option 1: Direct HTTPS Installation (Recommended)**

Add this to your VS Code MCP configuration (`mcp.json`):
```json
{    
    "servers": {
        "pdp-dev-mcp": {
            "command": "uvx",
            "args": ["--from", "git+https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform#subdirectory=src/pdp-dev-mcp", "pdp-dev-mcp"],
            "type": "stdio"
        }
    }
}
```

**Note:** This will download and run the latest version each time. No manual updates needed!

**Option 2: Clone and Install Locally (Faster startup)**
```bash
# Clone the repository
git clone https://msazure.visualstudio.com/One/_git/Commerce.PaymentsDataPlatform
cd Commerce.PaymentsDataPlatform/src/pdp-dev-mcp

# Install the tool globally
uv tool install .
```

Then use this simple VS Code MCP configuration:
```json
{    
    "servers": {
        "pdp-dev-mcp": {
            "config": {
                "command": "pdp-dev-mcp",
                "type": "stdio"
            }
        }
    }
}
```

**To update to latest version:**
```bash
cd Commerce.PaymentsDataPlatform/src/pdp-dev-mcp
git pull
uv tool install . --force
```

**Option 3: Local Development Installation**
If you have the repository cloned locally:
```json
{    
    "servers": {
        "pdp-dev-mcp": {
            "config": {
                "command": "python",
                "args": [
                    "/absolute/path/to/Commerce.PaymentsDataPlatform/src/pdp-dev-mcp/src/pdp_dev_mcp/server.py"
                ],
                "env": {
                    "PYTHONPATH": "/absoulute/path/to/Commerce.PaymentsDataPlatform/src/pdp-dev-mcp/src"
                },
                "type": "stdio"
            }
        }
    }
}
```

**Important:** Replace `/absolute/path/to/` with your actual repository path (e.g., `/Users/yourname/src/Microsoft/Commerce.PaymentsDataPlatform`)

**Troubleshooting**

- **Server not appearing in VS Code?** Restart VS Code after modifying mcp.json
- **Authentication issues?** Ensure you're authenticated with Azure DevOps (git credential approve)
- **Python errors?** Make sure you have Python 3.10+ installed

### 🚀 Usage

1. After installation, the PDP Development MCP server will be available for use with your GitHub Copilot agent in VS Code.
2. For best experience:
    - Open the PDP repository: [Commerce.PaymentsDataPlatform](https://msazure.visualstudio.com/DefaultCollection/One/_git/Commerce.PaymentsDataPlatform)
    - Open GitHub Copilot in VS Code and choose the Claude Sonnet 4 model
    - Use domain-specific prompts with `/mcp.` prefix for specialized workflows

## Quick Start (Legacy Installation)

```bash
# Install with uv (alternative to one-click)
uv add pdp-dev-mcp

# Or with integration features
uv add "pdp-dev-mcp[integration]"
```

## 🔗 Relationship to PDP MCP

The **PDP Development MCP** complements the existing [**PDP MCP**](https://msazure.visualstudio.com/One/_git/CFS-Payments-DataPlatform-MCP) server:

- **PDP MCP** (Production): Data analysis, querying, and investigation tools (Kusto, semantic models, documentation)
- **PDP Development MCP** (This package): Development workflow automation tools (data quality testing, Azure DevOps workflows)

Use both servers together for complete PDP development workflows - analyze data with PDP MCP, then build quality tests and manage development processes with PDP Development MCP.

## 🛡️ Security Note

Your credentials are always handled securely through the official [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/identity/Azure.Identity/README.md)

## Documentation

See [src/pdp_dev_mcp/README.md](src/pdp_dev_mcp/README.md) for complete documentation, installation instructions, and usage examples.

## Development

```bash
# Clone and setup
cd src/pdp-dev-mcp

# Install all dependencies for development
uv sync --dev
```

### Available Tasks

This project uses `taskipy` for Gradle-style task management. List all available tasks:

```bash
# Show all available tasks
uv run task -l
# OR
uv run task --list
```

### Common Development Tasks

```bash
# Testing
uv run task test              # Run unit tests only (CI/CD safe)
uv run task test-unit         # Run unit tests only (explicit)  
uv run task test-integration  # Run integration tests (requires Azure auth)
uv run task test-all          # Run unit + integration tests
uv run task test-verbose      # Run unit tests with verbose output
uv run task test-no-cov       # Run unit tests without coverage (faster)

# Code Quality
uv run task lint              # Check code quality with ruff
uv run task format            # Auto-format code with ruff
uv run task format-check      # Check if code needs formatting
uv run task fix               # Auto-fix linting issues where possible

# Coverage Reports
uv run task coverage-report   # Show coverage report from existing data
uv run task coverage-html     # Generate HTML coverage report

# Composite Tasks
uv run task check             # Run lint + test + coverage (full check)
```

### Integration Test Comment Cleanup

The system includes automatic cleanup of test comments to prevent PR clutter:

- **Automatic cleanup**: Test comments are automatically cleaned before integration tests run
- **Safe patterns**: Only removes comments matching test patterns (🧪, 🔬, integration-test, etc.)

### Direct Commands (alternative to tasks)

```bash
# Run tests directly
uv run pytest

# Run with coverage (configured in pyproject.toml)
uv run pytest --cov=pdp_dev_mcp --cov-report=html
```
<img width="1568" height="692" alt="image" src="https://github.com/user-attachments/assets/88e23e42-4817-47b3-9d66-f59d02a2d7fa" />
