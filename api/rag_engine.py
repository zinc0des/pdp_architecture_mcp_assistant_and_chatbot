"""
RAG Engine — Azure AI Foundry LLM Client

Generates responses to architecture questions using Azure AI Foundry (gpt-4.1-mini)
with retrieved context from the PDP knowledge base.
"""

import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

SYSTEM_PROMPT = """You are the **PDP Architecture Assistant** — a friendly, knowledgeable expert
on every aspect of the Payments Data Platform (PDP): architecture, data flows, infrastructure,
engineering patterns, and operational practices.

**Answering principles:**
1. Ground every claim in the provided context. If the context does not cover the question, say so
   honestly rather than speculating.
2. Write in a warm, professional, conversational tone — as if you were a senior engineer
   explaining something to a colleague over coffee. Avoid robotic bullet-only answers.

**Response structure (follow for every answer):**
- **## Overview** — Start with a short, accessible paragraph (2-3 sentences) that directly
  answers the question at a high level. This should make sense even if the reader stops here.
- **## How It Works** — Explain the mechanics in 2-4 concise paragraphs. Refer to specific
  layers (e.g., "Layer 3 – Processing"), domains, table names, and Azure resources when relevant.
  Use sub-headings if the explanation naturally breaks into parts.
- **## Architecture Flow** — For questions about data flow, pipelines, or topology, include a
  compact ```mermaid``` flowchart that traces the path from source to consumer. Skip this section
  if the question is purely conceptual or config-related.
- **## Key Takeaways** — Close with 3-5 bullet points that capture the most important facts.
  Each bullet should be a complete, self-contained sentence.

**Formatting rules:**
- Keep paragraphs to 2-4 sentences. Prefer prose over long bullet lists.
- Use inline code for table names (`gold.fact_transactions`), column names, and resource names.
- Cite the layer, domain, or knowledge-base topic you drew from when possible.
- Do NOT repeat the question back or pad with filler phrases like "Great question!"."""


class RAGEngine:
    """Azure AI Foundry RAG engine for PDP architecture questions."""

    def __init__(self):
        project_dir = Path(__file__).resolve().parent.parent
        load_dotenv(project_dir / ".env", override=False)
        load_dotenv(project_dir / ".env.local", override=False)

        self.project_endpoint = (
            os.getenv("AZURE_AI_PROJECT_ENDPOINT")
            or os.getenv("PDP_RAG_PROJECT_ENDPOINT")
            or ""
        ).strip()
        self.model_name = (
            os.getenv("PDP_RAG_MODEL")
            or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            or os.getenv("AZURE_OPENAI_DEPLOYMENT")
            or "gpt-4.1-mini"
        )
        self.endpoint = (
            os.getenv("AZURE_AI_ENDPOINT")
            or os.getenv("AZURE_OPENAI_ENDPOINT")
            or os.getenv("PDP_RAG_ENDPOINT")
            or ""
        ).strip()
        # For Azure AI Inference SDK, prefer the project endpoint as-is
        # (the SDK handles routing internally). Only fall back to the
        # normalised /models URL when no explicit endpoint is given.
        if not self.endpoint and self.project_endpoint:
            self.endpoint = self.project_endpoint
        self.api_key = (
            os.getenv("AZURE_AI_API_KEY")
            or os.getenv("AZURE_OPENAI_API_KEY")
            or os.getenv("AZURE_INFERENCE_CREDENTIAL")
            or os.getenv("PDP_RAG_API_KEY")
            or ""
        ).strip()
        self._client = None
        self._client_kind = None

    def _normalize_foundry_endpoint(self, endpoint: str) -> str:
        """Convert a Foundry project endpoint to the model inference endpoint when needed."""
        endpoint = (endpoint or "").strip().rstrip("/")
        if not endpoint:
            return ""
        if "/api/projects/" in endpoint:
            return endpoint.split("/api/projects/")[0] + "/models"
        if endpoint.endswith("/api/models"):
            return endpoint[:-4]
        if endpoint.endswith("/models"):
            return endpoint
        if ".services.ai.azure.com" in endpoint:
            return endpoint + "/models"
        return endpoint

    @property
    def is_ready(self) -> bool:
        """Whether the app has enough configuration to attempt a live model call."""
        return bool(self.endpoint or self.project_endpoint)

    def _build_fallback_response(self, question: str, context: str, reason: str | None = None) -> str:
        """Return a well-structured retrieval-only answer when the live model is unavailable."""
        context = context.strip()
        lines: list[str] = []

        # --- Status note ---
        if reason:
            # Simplify verbose Azure error messages for the user
            short_reason = reason
            if "PermissionDenied" in reason or "lacks the required data action" in reason:
                short_reason = (
                    "Your Azure identity needs the **Cognitive Services OpenAI User** role "
                    "on the Foundry resource. Ask your admin to assign it, or add an API key "
                    "to `.env` as `AZURE_AI_API_KEY=<key>`."
                )
            elif "Unauthorized" in reason:
                short_reason = (
                    "Authentication failed. Run `az login` to refresh your credentials, "
                    "or add an API key to `.env` as `AZURE_AI_API_KEY=<key>`."
                )
            lines.extend([
                "> **Note:** This answer is assembled directly from the PDP knowledge base "
                "because the live Azure AI model is temporarily unavailable.",
                f">",
                f"> {short_reason}",
                "",
            ])
        else:
            lines.extend([
                "> **Note:** Running in retrieval-only mode (Azure AI endpoint not configured). "
                "Responses are drawn directly from the PDP knowledge base.",
                "",
            ])

        # --- Overview ---
        lines.append("## Overview")
        lines.append("")
        if context:
            # Use the first meaningful paragraph as the overview
            first_para = self._extract_first_paragraph(context)
            lines.append(first_para)
        else:
            lines.append(
                "I wasn't able to find matching content in the local PDP architecture knowledge "
                "base for that question. Try rephrasing, or ask about a specific topic like "
                "data flow, a domain (PMT, BIN, COP), or an infrastructure component."
            )
        lines.append("")

        # --- Architecture Flow (when relevant) ---
        lowered = question.lower()
        if any(kw in lowered for kw in ("flow", "lineage", "architecture", "diagram", "topology", "pipeline", "how does", "how is")):
            if "billing" in lowered:
                lines.extend([
                    "## Architecture Flow",
                    "",
                    "Here's the BillingService data flow through PDP:",
                    "",
                    "```mermaid",
                    "flowchart LR",
                    "    A[Modern Billing Journal] -->|EventHub| B[Bronze]",
                    "    C[MCF] -->|EventHub| B",
                    "    D[Legacy CTP] -->|SStream| B",
                    "    B -->|Normalize & Classify| E[PDP Billing EventHub]",
                    "    E -->|Streaming Merge| F[Gold.Billing]",
                    "    F -->|CDF| G[Gold.PaymentsBilling]",
                    "```",
                    "",
                    "The **PDP Billing EventHub** acts as a Silver-equivalent normalization bus —",
                    "all three billing sources are normalized to a common schema before publishing",
                    "to this internal EventHub, replacing a traditional Silver Delta table with an",
                    "event-driven pattern.",
                    "",
                ])
            else:
                lines.extend([
                    "## Architecture Flow",
                    "",
                    "The high-level PDP data path follows the medallion pattern:",
                    "",
                    "```mermaid",
                    "flowchart LR",
                    "    A[Source Systems] -->|EventHub / API| B[Bronze]",
                    "    B -->|Cleanse & Conform| C[Silver]",
                    "    C -->|Business Logic & Star Schema| D[Gold]",
                    "    D -->|Serve| E[Power BI / Kusto / Apps]",
                    "```",
                    "",
                ])

        # --- How It Works (remaining context, deduplicated) ---
        if context:
            lines.append("## How It Works")
            lines.append("")
            # Remove the already-shown first paragraph and trim to a readable length
            remaining = self._clean_context_for_display(context).rstrip()
            first_para = self._extract_first_paragraph(context)
            if remaining.startswith(first_para) or remaining.startswith(f"**{first_para}"):
                remaining = remaining[len(first_para):].lstrip("\n -")
            # Trim to ~1800 chars and break at the last complete paragraph/section
            if len(remaining) > 1800:
                cut = remaining[:1800]
                last_break = cut.rfind("\n\n")
                if last_break > 600:
                    cut = cut[:last_break]
                remaining = cut.rstrip()
            if remaining:
                lines.append(remaining)
            lines.append("")

        # --- Key Takeaways ---
        lines.append("## Key Takeaways")
        lines.append("")
        lines.append("- The PDP knowledge base successfully matched relevant content for your question.")
        if reason:
            lines.append(
                "- Live model-backed responses will resume once the Azure AI endpoint and "
                "permissions are available — the architecture and content will be richer then."
            )
        else:
            lines.append(
                "- Configure the Azure AI endpoint in `.env` to enable richer, model-backed answers."
            )
        lines.append(
            "- For deeper exploration, try asking about specific layers, domains, or pipeline stages."
        )

        return "\n".join(lines)

    @staticmethod
    def _extract_first_paragraph(text: str) -> str:
        """Pull the first non-empty, non-heading paragraph (up to ~500 chars) from context text."""
        for block in text.split("\n\n"):
            stripped = block.strip()
            if (
                len(stripped) > 30
                and not stripped.startswith("#")
                and not stripped.startswith("```")
                and not stripped.startswith("|")
                and not stripped.startswith("---")
            ):
                return stripped[:500]
        return text[:300].rstrip()

    @staticmethod
    def _clean_context_for_display(text: str) -> str:
        """Clean raw knowledge-base context for human-readable display.

        Strips top-level headings (# and ##) that would clash with the
        response structure, and removes divider lines.
        """
        lines = text.splitlines()
        cleaned: list[str] = []
        for line in lines:
            # Convert top-level headings to bold labels
            if line.startswith("## "):
                cleaned.append(f"**{line.lstrip('# ').strip()}**")
            elif line.startswith("# "):
                cleaned.append(f"**{line.lstrip('# ').strip()}**")
            elif line.strip() == "---":
                cleaned.append("")  # replace HR with blank line
            else:
                cleaned.append(line)
        return "\n".join(cleaned)

    def _get_client(self):
        """Lazy-init the Azure OpenAI client.

        Uses the ``openai`` SDK for all Foundry endpoints so that we control
        the token audience correctly (``https://cognitiveservices.azure.com``).
        """
        if self._client is not None:
            return self._client

        if not self.endpoint:
            return None

        # Resolve the base host (strip project/model sub-paths).
        base = self.endpoint.rstrip("/")
        if "/api/projects/" in base:
            base = base.split("/api/projects/")[0]
        if base.endswith("/models"):
            base = base[: -len("/models")]

        from openai import AsyncAzureOpenAI

        if self.api_key:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=base,
                api_key=self.api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            )
        else:
            from azure.identity import AzureCliCredential, get_bearer_token_provider

            token_provider = get_bearer_token_provider(
                AzureCliCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=base,
                azure_ad_token_provider=token_provider,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            )

        self._client_kind = "azure-openai"
        return self._client

        self._client_kind = "azure-openai"
        return self._client

    async def generate(
        self,
        question: str,
        context: str,
        history: Optional[list[dict]] = None,
    ) -> str:
        """Generate a response using the LLM with retrieved context."""
        client = self._get_client()
        if client is None:
            return self._build_fallback_response(question, context)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        user_message = f"""Context from PDP Knowledge Base:
---
{context}
---

Question: {question}"""

        messages.append({"role": "user", "content": user_message})

        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as exc:
            return self._build_fallback_response(question, context, str(exc))
