"""
Chunk Retriever — TF-IDF based knowledge base retrieval

Loads markdown files from the PDP architecture knowledge base,
chunks them into sections, and provides keyword-based retrieval
with TF-IDF scoring and synonym expansion.
"""

import re
import math
from collections import Counter
from pathlib import Path
from typing import Optional


# Synonym expansion for common PDP terms
SYNONYMS = {
    "eventhub": ["event hub", "event hubs", "eh"],
    "event hub": ["eventhub", "event hubs", "eh"],
    "databricks": ["spark", "dbr", "notebook"],
    "spark": ["databricks", "pyspark"],
    "bronze": ["raw", "landing", "ingestion layer"],
    "silver": ["cleaned", "curated", "transform"],
    "gold": ["business", "consumer-facing", "star schema", "aggregate"],
    "pmt": ["payment transactions", "paymenttransactions", "fact_transactions"],
    "pj": ["payments journal", "payment journal", "pmt", "fact_transactions"],
    "payments journal": ["pj", "pmt", "payment transactions", "fact_transactions"],
    "cop": ["cost of payments", "fees", "interchange"],
    "dq": ["data quality", "testing", "test framework"],
    "nt": ["network tokenization", "token", "dpan"],
    "au": ["account updater", "card-on-file"],
    "bin": ["bank identification", "issuing bank"],
    "ev2": ["express v2", "deployment"],
    "bicep": ["iac", "infrastructure as code", "arm"],
    "kusto": ["adx", "azure data explorer", "kql"],
    "synapse": ["pipeline", "orchestration"],
    "streaming": ["structured streaming", "real-time", "continuous"],
    "delta": ["delta lake", "delta table", "acid"],
}


class ChunkRetriever:
    """TF-IDF based chunk retriever for the PDP knowledge base."""

    def __init__(self, knowledge_base_dir: str):
        self.kb_dir = Path(knowledge_base_dir)
        self.documents: list[dict] = []
        self.chunks: list[dict] = []
        self._idf: dict[str, float] = {}
        self._load_knowledge_base()
        self._build_index()

    def _load_knowledge_base(self):
        """Load all markdown files from the knowledge base directory."""
        if not self.kb_dir.is_dir():
            return

        for md_file in sorted(self.kb_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            self.documents.append({
                "filename": md_file.name,
                "content": text,
                "title": self._extract_title(text),
            })

            # Chunk by heading sections
            sections = self._chunk_by_headings(text, md_file.name)
            self.chunks.extend(sections)

    def _extract_title(self, text: str) -> str:
        """Extract the first heading as title."""
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def _chunk_by_headings(self, text: str, source: str) -> list[dict]:
        """Split markdown into chunks by headings."""
        chunks = []
        current_heading = ""
        current_content: list[str] = []

        for line in text.splitlines():
            if line.startswith("## ") or line.startswith("### "):
                # Save previous chunk
                if current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 30:
                        chunks.append({
                            "source": source,
                            "heading": current_heading,
                            "content": content,
                        })
                current_heading = line.lstrip("#").strip()
                current_content = [line]
            else:
                current_content.append(line)

        # Save last chunk
        if current_content:
            content = "\n".join(current_content).strip()
            if len(content) > 30:
                chunks.append({
                    "source": source,
                    "heading": current_heading,
                    "content": content,
                })

        return chunks

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase words."""
        return re.findall(r"[a-z0-9_]+", text.lower())

    def _build_index(self):
        """Build TF-IDF index for all chunks."""
        if not self.chunks:
            return

        # Document frequency
        df: Counter = Counter()
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["content"]))
            for token in tokens:
                df[token] += 1

        n = len(self.chunks)
        self._idf = {
            token: math.log((n + 1) / (count + 1)) + 1
            for token, count in df.items()
        }

    def _score_chunk(self, chunk: dict, query_tokens: list[str]) -> float:
        """Score a chunk against query tokens using TF-IDF."""
        chunk_tokens = self._tokenize(chunk["content"])
        if not chunk_tokens:
            return 0.0

        tf = Counter(chunk_tokens)
        total = len(chunk_tokens)

        score = 0.0
        for token in query_tokens:
            if token in tf:
                tf_score = tf[token] / total
                idf_score = self._idf.get(token, 1.0)
                score += tf_score * idf_score

        # Boost for heading matches
        heading_lower = chunk.get("heading", "").lower()
        for token in query_tokens:
            if token in heading_lower:
                score *= 1.5

        return score

    def _expand_query(self, query: str) -> list[str]:
        """Expand query with synonyms."""
        tokens = self._tokenize(query)
        expanded = list(tokens)

        for token in tokens:
            if token in SYNONYMS:
                for syn in SYNONYMS[token]:
                    expanded.extend(self._tokenize(syn))

        return list(set(expanded))

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Retrieve the most relevant chunks for a query."""
        if not self.chunks:
            return []

        query_tokens = self._expand_query(query)

        scored = []
        for chunk in self.chunks:
            score = self._score_chunk(chunk, query_tokens)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "source": chunk["source"],
                "heading": chunk["heading"],
                "content": chunk["content"],
                "score": round(score, 4),
            })

        return results
