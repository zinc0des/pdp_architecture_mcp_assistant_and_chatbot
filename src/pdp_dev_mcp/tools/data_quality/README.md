# Data Quality Tools

Comprehensive data quality development tools for the Payments Data Platform, providing AI agents with expert data quality capabilities for generating PySpark tests and JSON DQ Framework rules through intelligent prompts and guided workflows.

## ✨ What can you do with the Data Quality Tools?

### 🧪 Generate Data Quality Tests
- "Create a PySpark test to validate transaction completeness for the PaymentTransactions table"
- "Generate JSON DQ Framework rules for monitoring null values in critical payment fields"
- "Help me choose between PySpark tests and JSON rules for complex statistical validation"
- "Create a test template for detecting anomalies in payment volumes with proper debugging patterns"

### 📊 Analyze Existing Tests
- "Analyze my test file for PDP compliance standards and suggest improvements"
- "Review multiple test files and provide a compliance scorecard"
- "Check if my tests follow proper debugging and alerting patterns"

### 🎯 Get Architecture Guidance
- "Should I use PySpark tests or JSON DQ Framework rules for this validation scenario?"
- "What's the best directory structure for my data quality tests?"
- "Help me understand the dual-path data quality architecture"

## Vision & Objectives

### Primary Goal
Provide a unified, dual-path approach to data quality management that supports both detailed investigation and operational monitoring, ensuring data reliability across all PDP systems.

### Key Principles
- **Dual-Path Architecture**: Support both PySpark test templates (detailed analysis) and JSON DQ Framework rules (operational monitoring)
- **Standards Compliance**: Ensure all generated tests follow established PDP data quality standards and best practices
- **Guided Generation**: Provide intelligent suggestions based on table schemas, business context, and existing patterns
- **Comprehensive Analysis**: Enable deep analysis of existing test files for compliance and effectiveness
- **Architectural Guidance**: Help users choose the optimal approach based on their specific data quality needs

## Architecture Overview

### 🔬 PySpark Tests - Advanced Validation Path
**Purpose**: Complex validation logic, statistical analysis, debugging, and production validation that exceeds JSON framework capabilities

### 📊 JSON DQ Framework Rules - Standard Monitoring Path
**Purpose**: Continuous monitoring, dashboard integration, and automated alerting for standard validation patterns

> 💡 **Need help choosing?** Use the `dual_path_dq_guidance` prompt for personalized recommendations based on your validation complexity and requirements.

## Available Tools

### 🧪 Test Generation & Suggestions
- **`generate_test_suggestions`** - Generate PySpark test templates with proper debugging patterns
- **`generate_json_rule_suggestions`** - Generate JSON DQ Framework rules for operational monitoring
- **`generate_advanced_json_rule`** - Generate fully customized JSON DQ Framework rules with complete control

### 📋 Test Analysis & Compliance
- **`analyze_test_file`** - Analyze individual test files for standards compliance with detailed scoring
- **`analyze_multiple_files`** - Batch analyze multiple test files for comprehensive review and comparison

### 🎯 Architecture & Guidance
- **`get_dual_path_architecture_guidance`** - Provide guidance on choosing the optimal approach with examples
- **`get_directory_guidance`** - Help with proper file placement and directory structure
- **`get_debugging_guidance`** - Provide debugging best practices for DQ tests
- **`get_standards_checklist`** - Ensure compliance with PDP data quality standards
- **`compare_dq_approaches`** - Detailed comparison of PySpark vs JSON approaches
- **`get_dq_approach_examples`** - Real-world scenarios for when to use each approach

## MCP Prompts

### 🧪 Test Suggestion Generator
**Prompt**: `test_suggestion_generator`
**Purpose**: Expert guidance for creating compliant data quality tests and monitoring rules

### 📊 Data Quality Analyst
**Prompt**: `data_quality_analyst`
**Purpose**: Expert analysis of test files for compliance and effectiveness

### 🎯 Dual-Path Architecture Guidance
**Prompt**: `dual_path_dq_guidance`
**Purpose**: Comprehensive guidance for choosing between PySpark tests and JSON DQ Framework rules

## Deployment Guidance

### PySpark Test Deployment
```
Target: src/databricks/workspace/notebooks/{SubjectArea}/Test/{TestType}/
File: test_{category}_{specific_check}_{subject_area}.py
Execution: Via Pytest-Runner.py automation in Databricks (production-ready)
```

### JSON Rule Deployment
```
Target: src/databricks/workspace/notebooks/DQFramework/RuleConfig/MetricCollector/{SubjectArea}/
File: {layer}.json (integrated with existing files)
Execution: Via DQ Framework MetricCollector
```

## JSON DQ Framework Integration

The system automatically selects appropriate rule types based on data quality categories and field context. Common rule types include `count`, `null_check`, `duplicate_check`, `sum`, `custom_query`, `table_history`, and `custom_notebook`.

> 🛠️ **Implementation**: The tools handle intelligent rule selection automatically - just describe your validation needs and get the appropriate rule type with proper thresholds.

## Best Practices

- **Start with Data Exploration**: When available, use Kusto tools to understand data patterns before creating tests
- **Choose the Right Path**: Use the dual-path guidance to choose between PySpark tests and JSON rules
- **Follow Standards**: Ensure all tests meet PDP compliance requirements with 100% test coverage
- **Proper Directory Structure**: Place files in correct directories following established patterns
- **Include Debugging Information**: Add comprehensive debugging patterns for troubleshooting
- **Validate Before Production**: Use analysis tools to verify compliance before deployment

### Strategic Implementation Approach
1. **Start with prompts** - Get personalized guidance based on your validation complexity
2. **Standard Monitoring** - Use JSON rules for common patterns (counts, nulls, basic thresholds)
3. **Advanced Validation** - Use PySpark tests for complex validation or statistical analysis
4. **Automated Execution** - Both approaches support production automation

---

*Data Quality tools for the PDP Development MCP Server*
