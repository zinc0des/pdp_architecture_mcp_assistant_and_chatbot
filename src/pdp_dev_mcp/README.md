# PDP Development MCP Server

A comprehensive Model Context Protocol (MCP) server for Payments Data Platform development. This server provides AI agents with specialized tools and guidance across multiple domains of platform development.

## 🏗️ Architecture Overview

The PDP Development MCP Server is organized into domain-specific modules, each containing specialized tools and prompts for different aspects of platform development:

### 📂 Domain Structure

```
src/pdp_dev_mcp/
├── tools/
│   ├── data_quality/          # Data quality analysis, testing, and monitoring
│   └── [future domains]/      # Infrastructure, analytics, operations, etc.
├── prompts/
│   ├── data_quality/          # DQ-specific workflow prompts
│   └── [future domains]/      # Domain-specific guidance prompts
└── common/                    # Shared utilities and patterns
```

## 🎯 Available Domains

### � Data Quality
**Location**: `tools/data_quality/` and `prompts/data_quality/`  
**Purpose**: Comprehensive data quality development tools including PySpark test generation, JSON DQ Framework rules, compliance analysis, and architectural guidance.

**Key Capabilities**:
- Dual-path data quality architecture (PySpark tests + JSON rules)
- Standards compliance checking and analysis
- Test generation with debugging patterns
- Architecture guidance for choosing optimal approaches

[**See detailed documentation →**](tools/data_quality/README.md)

### 🚀 Future Potential Domains
The server is designed to expand into additional platform development areas:

- **Infrastructure & Deployment**: Bicep templates, EV2 configurations, Azure resources
- **Data Platform**: Kusto queries, Databricks notebooks, Synapse pipelines  
- **Analytics & BI**: Power BI models, Analysis Services, reporting
- **Platform Operations**: Monitoring, alerts, performance optimization

## 🛠️ Getting Started

### Prerequisites
1. VS Code (Stable or Insiders)
2. GitHub Copilot extensions
3. Python 3.10+
4. `uv` package manager

### Installation

```bash
# Basic installation
uv add pdp-dev-mcp

# With integration features
uv add "pdp-dev-mcp[integration]"

# Development setup
uv add "pdp-dev-mcp[dev]"
```

### VS Code Configuration

Add to your `settings.json`:

```json
{
    "mcp": {
        "servers": {
            "pdp-dev-mcp": {
                "command": "uv",
                "args": [
                    "run",
                    "--with",
                    "pdp-dev-mcp",
                    "-m",
                    "pdp_dev_mcp.server"
                ]
            }
        }
    }
}
```

### Quick Start

1. Start the PDP Development MCP server
2. Open GitHub Copilot in VS Code (Agent mode)
3. Select the PDP Development MCP Server
4. Choose Claude Sonnet 4 model
5. Use domain-specific prompts with `/mcp.` prefix

## 🎨 Usage Patterns

### Domain-Specific Prompts
Each domain provides specialized prompts accessible via the `/mcp.` prefix:

**Data Quality Examples**:
- `/mcp.pdp-development-mcp.test_suggestion_generator` - Generate data quality tests
- `/mcp.pdp-development-mcp.data_quality_analyst` - Analyze existing tests
- `/mcp.pdp-development-mcp.dual_path_dq_guidance` - Get architectural guidance

### Tool Integration
Tools can be called directly by AI agents or used in combination for complex workflows:

```
AI Agent → Domain Tools → Platform Integration → Results
```

## 🔧 Development

### Adding New Domains

1. Create domain directory structure:
   ```
   tools/[domain_name]/
   prompts/[domain_name]/
   ```

2. Implement domain-specific tools with `@mcp.tool` decorators
3. Create domain-specific prompts with `@mcp.prompt` decorators  
4. Update imports in main `__init__.py`
5. Add domain documentation

### Testing

```bash
# Run all tests
uv run task test

# Run with coverage
uv run task coverage

# Run domain-specific tests
uv run pytest tests/[domain_name]/
```

## 📋 Best Practices

- **Domain Separation**: Keep domain-specific logic isolated
- **Shared Utilities**: Use `common/` for cross-domain functionality
- **Documentation**: Maintain domain-specific README files
- **Standards**: Follow established MCP patterns and conventions
- **Testing**: Maintain comprehensive test coverage per domain

## 🛡️ Security

Credentials are handled securely through the official [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/identity/Azure.Identity/README.md) when using integration features.

## 👥 Contributing

This project welcomes contributions and suggestions. Please see the main repository's contribution guidelines.

---

*Comprehensive development assistance for the Payments Data Platform - August 2025*
