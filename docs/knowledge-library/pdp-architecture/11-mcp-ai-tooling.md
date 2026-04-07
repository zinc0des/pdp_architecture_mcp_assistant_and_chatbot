# PDP MCP and AI Tooling

## MCP Server Architecture

PDP has two MCP (Model Context Protocol) servers that provide AI-accessible tools:

### 1. PDP Data MCP Server (`CFS-Payments-DataPlatform-MCP`)
- **Framework**: FastMCP (MCP SDK)
- **Transport**: stdio (invoked by VS Code Copilot)
- **Purpose**: Live data queries against PDP data sources
- **Pattern**: Tool-based — Copilot calls tools, gets data back
- **State**: Stateless

#### Tool Categories
- **Kusto tools**: Execute KQL queries against PDP Kusto clusters
- **SQL DW tools**: Query Databricks SQL warehouse
- **Semantic Model tools**: Execute DAX against Power BI semantic models
- **Azure DevOps tools**: PR management, work item queries

### 2. PDP Dev MCP Server (`pdp-dev-mcp`)
- **Framework**: FastMCP + FastAPI (for RAG chatbot)
- **Transport**: stdio (MCP) + HTTP (API)
- **Purpose**: Architecture knowledge, code review, DQ guidance
- **Pattern**: Knowledge-base retrieval + RAG
- **State**: Stateless (MCP) / Stateful sessions (API)

#### Tool Categories
- **Architecture tools**: Knowledge base retrieval (12 topics)
- **Grafana tools**: Alert diagnosis and resolution guidance
- **Knowledge Harvester**: Learning extraction from Copilot sessions
- **Research Notes**: Personal research vault management
- **Data Quality tools**: Test analysis, compliance checking
- **Code Review tools**: PR analysis, prescriptive comments
- **Azure DevOps tools**: Repository discovery, PR lifecycle

## RAG Chatbot (Architecture Assistant API)

### Architecture
```
Browser UI → FastAPI Server → Chunk Retriever → Knowledge Base
                ↓
         Azure AI Foundry (gpt-4.1-mini) → Response with citations
```

### Components
- **main.py**: FastAPI server with REST endpoints
- **rag_engine.py**: Azure AI Foundry client for LLM calls
- **chunk_retriever.py**: TF-IDF based chunk retrieval with synonym expansion
- **ui/**: Static HTML/CSS/JS for browser interface

### Endpoint
- `http://127.0.0.1:8002`
- Chat endpoint: `POST /chat`
- Health: `GET /health`

## Agent Modes (VS Code Copilot)

### pdp_architecture_assistant
- Answers PDP architecture questions
- Uses architecture KB tools, grafana tools, knowledge harvester
- Cites specific layers, domains, topics

### payment_analyst
- Payments data analysis with report generation
- Uses Kusto, semantic model, SQL DW tools
- Generates Mermaid diagrams and markdown reports

### dq_test_assistant
- Data quality investigation and troubleshooting
- Uses DQ analysis tools, App Insights queries
- Root cause analysis with remediation steps

### incident_impact_analyst
- Payment incident analysis
- Impact assessment across providers, regions, methods
- ICM integration
