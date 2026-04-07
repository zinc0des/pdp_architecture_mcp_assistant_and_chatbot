# Dual-Path Data Quality Architecture Guidance

Choose the optimal approach based on your validation complexity and requirements:

## 📊 JSON DQ Framework Rules - When to Use:
- **Standard Validation Patterns**: Common checks like counts, nulls, duplicates, basic thresholds
- **Dashboard Integration**: Metrics that feed directly into operational dashboards and reports
- **Simple Alerting**: Automated notifications for straightforward threshold breaches
- **Operational Efficiency**: Low-maintenance, standardized monitoring with minimal overhead
- **SLA Monitoring**: Service level agreement compliance and basic trend tracking

## 🔬 PySpark Tests - When to Use:
- **Complex Validation Logic**: Multi-table joins, complex aggregations, custom business rules
- **Statistical Analysis**: Advanced metrics, distributions, correlations, variance analysis
- **When JSON Framework is Insufficient**: Avoid complex custom queries/notebooks in JSON framework
- **Production Validation**: Complex validation that runs via automated Pytest-Runner
- **Debugging & Investigation**: Deep-dive analysis with rich output and detailed context
- **Data Profiling**: Comprehensive data exploration and pattern discovery

## 🎯 Decision Matrix:

### Choose JSON DQ Framework When:
- Standard validation patterns cover your needs (counts, nulls, basic comparisons)
- You need lightweight, low-maintenance monitoring
- Dashboard integration is the primary goal
- Simple threshold-based alerting is sufficient
- Typically when a metric is called for

### Choose PySpark Tests When:
- JSON framework would require complex custom queries or notebooks (team preference: avoid)
- You need sophisticated validation logic beyond basic patterns
- Statistical analysis or data profiling is required
- Complex business rules span multiple tables or require custom logic
- You're investigating issues and need detailed debugging output

## 🚀 AI-Assisted Development Best Practices

### Proven Development Workflow for DQ Implementation:
For complete details on the Azure DevOps + MerlinBot AI-assisted development workflow, see: `./azure_devops_ai_workflow_guide.md`

### DQ-Specific Workflow Applications:
1. **Initial Data Quality Development** (with MCP AI assistance for code generation)
2. **Create Pull Request** (collaborative approach with team)
3. **MerlinBot AI Review** (automated review provides 2-4 targeted suggestions)
4. **Iterate Based on AI Feedback** (address logic gaps, unused parameters, etc.)
5. **Human Review** (clean, enhanced code ready for team approval)
6. **Production Deployment** (both JSON rules and PySpark tests support automation)

### Azure DevOps Integration for DQ Teams:
- Use `az repos pr show --id <PR_ID>` to check PR status and retrieve MerlinBot feedback
- Expect AI comments focusing on **critical improvements** like unused parameters or logic enhancements
- **Address functional gaps first** (e.g., parameters not used in scoring logic) over cosmetic issues
- Document AI-suggested improvements in commit messages for team visibility

### Team Workflow Enhancement:
- **Let PRs "cook"** after addressing AI feedback - allows clean human review process
- Use MerlinBot suggestions to **enhance functionality** (e.g., intelligent pattern matching)
- Maintain high code quality through AI-human collaboration cycle
- Share successful AI integration patterns with team for broader adoption

## 🚀 Implementation Best Practices:

### For JSON DQ Framework Rules:
1. Stick to standard rule types (count, null_check, duplicate_check, sum, table_history)
2. Use consistent naming conventions for dashboard integration
3. Set appropriate execution schedules based on business needs
4. Design for scalability and maintainability in production environments

### For PySpark Tests:
1. Use when JSON framework limitations would force complex custom queries
2. Include comprehensive error handling and debugging information
3. Follow established directory structure and naming conventions
4. Design for automated execution via Pytest-Runner.py
5. Provide clear pass/fail criteria and actionable insights

## 📋 Getting Started Checklist:
1. **Explore the data first** - Use Kusto tools to understand patterns, distributions, and edge cases
2. **Assess validation complexity** - Can standard JSON rule types handle it elegantly?
3. **Check for existing resources** - For PySpark tests, look for existing Pytest fixtures; for JSON rules, review existing rule patterns
4. **Consider maintenance** - Will you need ongoing debugging and analysis capabilities?
5. **Plan for automation** - Both approaches support production deployment
6. **Choose the right tool** - JSON for standard patterns, PySpark for complex validation
7. **Validate assumptions** - Query actual data to calibrate thresholds and test edge cases
8. **Test thoroughly** - Validate in development before production deployment
9. **Leverage AI feedback** - Create PR early to get MerlinBot suggestions for enhancement

## 💡 Pre-Development Best Practices:
- **Data Exploration**: Use `kusto_execute_query` to understand data patterns before writing tests
- **Schema Validation**: Use `kusto_get_table_schema` to ensure tests align with actual table structure
- **Fixture Reuse**: For PySpark tests, check for existing Pytest fixtures; for JSON rules, review existing rule patterns
- **Threshold Calibration**: Query historical data to set realistic and meaningful thresholds
- **AI Review Planning**: Structure code for effective AI review (clear parameter usage, logical flow)

## 🔄 Hybrid Approach:
Use both approaches strategically:
- **JSON DQ Framework** for standard monitoring patterns
- **PySpark Tests** for complex validation that exceeds JSON framework capabilities

This provides comprehensive coverage while following team preferences and leveraging each approach's strengths through modern AI-assisted development workflows.
