# PDP Knowledge Vault

This directory stores learnings harvested from Copilot conversations about PDP.

## Structure

```
knowledge-vault/
├── README.md           # This file
├── learnings/          # Timestamped learning entries
├── categories/         # Consolidated by topic (future)
└── pending-review/     # Awaiting verification (future)
```

## Learning Format

Each learning is a markdown file with YAML frontmatter:

```yaml
---
id: "2026-03-08_001_bronze-layer.md"
timestamp: "2026-03-08T15:30:00+00:00"
session_id: "20260308_153000"
category: "architecture"
confidence: 0.80
matched_keywords: ['bronze', 'delta lake', 'ingestion']
related_topics: ['bronze layer', 'delta lake']
tags: ['architecture', 'bronze', 'delta lake']
integrated: false
captured_date: "2026-03-08"
updated_date: "2026-03-08"
---
```

## Categories

- architecture, data-flow, domains, infrastructure, pipelines
- patterns, operations, monitoring, data-quality, security, tooling

## Workflow

1. User says "thanks pdp" → triggers `harvest_pdp_learnings`
2. Tool extracts learnings from assistant messages
3. Saves to `learnings/` with metadata
4. Cross-references to `.research-vault/` for unified search
5. Verified learnings can be promoted to knowledge base
