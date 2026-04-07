"""
Research Notes Service

Core logic for capturing, updating, tagging, and listing research notes
stored in the research vault (.research-vault/).

The vault is an external directory that holds structured markdown files
with YAML frontmatter for provenance tracking. Each note has:
- Version history with revision logs
- Auto-suggested and manually-applied tags
- Status lifecycle: draft → reviewed → promoted → archived
- KB integration tracking for Scavenger agent consumption

This service is consumed by the MCP tool functions in research_notes_tools.py.
"""

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pdp_dev_mcp.common import logger

# Vault location: sibling to workspace roots, outside any repo
_WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
VAULT_DIR = _WORKSPACE_ROOT / ".research-vault"
INDEX_PATH = VAULT_DIR / "index.json"


def _ensure_vault():
    """Create vault directory if it doesn't exist."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)


def _read_index() -> dict:
    """Read the vault index or return empty dict."""
    if INDEX_PATH.is_file():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {}


def _write_index(index: dict):
    """Write the vault index."""
    _ensure_vault()
    INDEX_PATH.write_text(json.dumps(index, indent=2, default=str), encoding="utf-8")


def _content_hash(text: str) -> str:
    """Generate a short hash of content for dedup."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _slugify(text: str) -> str:
    """Convert a topic to a filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-")[:60]


def _now_iso() -> str:
    """ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    """Today's date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _build_filename(topic: str) -> str:
    """Build the filename for a new note: YYYY-MM-DD_slug.md"""
    return f"{_today()}_{_slugify(topic)}.md"


def _find_existing_note(topic: str) -> Optional[Path]:
    """Find an existing note by topic name (case-insensitive slug match)."""
    slug = _slugify(topic)
    if not VAULT_DIR.is_dir():
        return None
    for p in VAULT_DIR.glob("*.md"):
        if slug in p.stem.lower():
            return p
    return None


def _build_frontmatter(
    title: str,
    tags: list[str],
    project: str,
    version: int,
    revisions: list[dict],
    status: str = "draft",
    kb_reviewed: bool = False,
    kb_topic: str = "",
    kb_promoted_date: str = "",
) -> str:
    """Build YAML frontmatter block."""
    lines = ["---"]
    lines.append(f"title: \"{title}\"")
    lines.append(f"created: \"{_now_iso()}\"")
    lines.append(f"updated: \"{_now_iso()}\"")
    lines.append(f"version: {version}")
    lines.append(f"status: \"{status}\"")
    if project:
        lines.append(f"project: \"{project}\"")
    if tags:
        lines.append(f"tags: [{', '.join(repr(t) for t in tags)}]")
    else:
        lines.append("tags: []")
    lines.append(f"kb_reviewed: {str(kb_reviewed).lower()}")
    if kb_topic:
        lines.append(f"kb_topic: \"{kb_topic}\"")
    if kb_promoted_date:
        lines.append(f"kb_promoted_date: \"{kb_promoted_date}\"")
    if revisions:
        lines.append("revisions:")
        for rev in revisions:
            lines.append(f"  - timestamp: \"{rev.get('timestamp', '')}\"")
            lines.append(f"    action: \"{rev.get('action', '')}\"")
            lines.append(f"    summary: \"{rev.get('summary', '')}\"")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns (metadata_dict, body_content).
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()

    metadata: dict = {}
    current_key = ""
    current_list: list = []
    in_list = False

    for line in fm_text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if line_stripped.startswith("- ") and in_list:
            # List item under revisions or similar
            item_text = line_stripped[2:].strip()
            if ":" in item_text:
                k, v = item_text.split(":", 1)
                if current_list:
                    current_list[-1][k.strip()] = v.strip().strip('"')
                else:
                    current_list.append({k.strip(): v.strip().strip('"')})
            continue

        if ":" in line_stripped and not line_stripped.startswith("-"):
            if in_list and current_key:
                metadata[current_key] = current_list
                in_list = False
                current_list = []

            k, v = line_stripped.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"')

            if v == "":
                in_list = True
                current_key = k
                current_list = [{}]
                continue

            if v.startswith("[") and v.endswith("]"):
                items = [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip()]
                metadata[k] = items
            elif v.lower() in ("true", "false"):
                metadata[k] = v.lower() == "true"
            elif v.isdigit():
                metadata[k] = int(v)
            else:
                metadata[k] = v

    if in_list and current_key:
        metadata[current_key] = current_list

    return metadata, body


def _rebuild_tag_index(index: dict):
    """Rebuild tag index from all notes."""
    tag_index: dict[str, list[str]] = {}
    for filename, meta in index.items():
        for tag in meta.get("tags", []):
            tag_index.setdefault(tag, []).append(filename)
    index["_tag_index"] = tag_index


def capture_notes(
    topic: str,
    content: str,
    tags: Optional[str] = None,
    project: str = "",
    mode: str = "auto",
    review_notes: str = "",
) -> dict:
    """Capture or update a research note.

    Modes: auto, create, update, review
    """
    _ensure_vault()
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    suggested = _suggest_tags(content)
    all_tags = sorted(set(tag_list + suggested))

    existing = _find_existing_note(topic) if mode != "create" else None

    if mode == "review" and existing:
        return _review_note(existing, review_notes, all_tags)

    if existing and mode in ("auto", "update"):
        return _update_note(existing, content, all_tags, project)

    return _create_note(topic, content, all_tags, project)


def _create_note(topic: str, content: str, tags: list[str], project: str) -> dict:
    """Create a new research note."""
    filename = _build_filename(topic)
    filepath = VAULT_DIR / filename
    revision = {
        "timestamp": _now_iso(),
        "action": "created",
        "summary": f"Initial capture: {topic}",
    }
    frontmatter = _build_frontmatter(
        title=topic, tags=tags, project=project,
        version=1, revisions=[revision],
    )
    body = f"\n# {topic}\n\n## Key Findings\n\n{content}\n\n## Open Questions\n\n_None yet._\n\n## Raw Notes\n\n_Captured from conversation._\n"
    filepath.write_text(frontmatter + "\n" + body, encoding="utf-8")

    # Update index
    index = _read_index()
    index[filename] = {
        "topic": topic,
        "version": 1,
        "status": "draft",
        "tags": tags,
        "project": project,
        "created": _now_iso(),
        "updated": _now_iso(),
        "content_hash": _content_hash(content),
    }
    _rebuild_tag_index(index)
    _write_index(index)

    logger.info("Created research note: %s", filename)
    return {
        "action": "created",
        "filename": filename,
        "version": 1,
        "tags": tags,
        "suggested_tags": [t for t in tags if t not in ([] if not tags else tags)],
    }


def _update_note(filepath: Path, content: str, tags: list[str], project: str) -> dict:
    """Update an existing research note with new content."""
    text = filepath.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    version = metadata.get("version", 1) + 1
    old_tags = metadata.get("tags", [])
    tags_added = [t for t in tags if t not in old_tags]
    tags_removed = [t for t in old_tags if t not in tags]
    all_tags = sorted(set(old_tags + tags))

    revisions = metadata.get("revisions", [])
    revisions.append({
        "timestamp": _now_iso(),
        "action": "updated",
        "summary": f"Content update v{version}",
    })

    frontmatter = _build_frontmatter(
        title=metadata.get("title", filepath.stem),
        tags=all_tags,
        project=project or metadata.get("project", ""),
        version=version,
        revisions=revisions,
        status=metadata.get("status", "draft"),
        kb_reviewed=metadata.get("kb_reviewed", False),
    )

    # Append update section
    update_section = f"\n\n## Update (v{version}) — {_today()}\n\n{content}\n"
    new_text = frontmatter + "\n" + body + update_section
    filepath.write_text(new_text, encoding="utf-8")

    # Update index
    index = _read_index()
    index[filepath.name] = {
        "topic": metadata.get("title", filepath.stem),
        "version": version,
        "status": metadata.get("status", "draft"),
        "tags": all_tags,
        "project": project or metadata.get("project", ""),
        "created": metadata.get("created", ""),
        "updated": _now_iso(),
        "content_hash": _content_hash(content),
    }
    _rebuild_tag_index(index)
    _write_index(index)

    logger.info("Updated research note: %s to v%d", filepath.name, version)
    return {
        "action": "updated",
        "filename": filepath.name,
        "version": version,
        "tags": all_tags,
        "tags_added": tags_added,
        "tags_removed": tags_removed,
    }


def _review_note(filepath: Path, review_notes: str, tags: list[str]) -> dict:
    """Mark an existing note as reviewed."""
    text = filepath.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    version = metadata.get("version", 1) + 1
    revisions = metadata.get("revisions", [])
    revisions.append({
        "timestamp": _now_iso(),
        "action": "reviewed",
        "summary": review_notes or "Reviewed",
    })

    frontmatter = _build_frontmatter(
        title=metadata.get("title", filepath.stem),
        tags=sorted(set(metadata.get("tags", []) + tags)),
        project=metadata.get("project", ""),
        version=version,
        revisions=revisions,
        status="reviewed",
        kb_reviewed=True,
    )

    new_text = frontmatter + "\n" + body
    filepath.write_text(new_text, encoding="utf-8")

    index = _read_index()
    if filepath.name in index:
        index[filepath.name]["version"] = version
        index[filepath.name]["status"] = "reviewed"
        index[filepath.name]["updated"] = _now_iso()
        _rebuild_tag_index(index)
        _write_index(index)

    logger.info("Reviewed research note: %s", filepath.name)
    return {"action": "reviewed", "filename": filepath.name, "version": version}


def tag_notes(
    topic: str,
    add_tags: str = "",
    remove_tags: str = "",
    set_status: str = "",
) -> dict:
    """Add/remove tags or change status on a research note."""
    existing = _find_existing_note(topic)
    if not existing:
        return {"error": f"No note found for topic '{topic}'"}

    text = existing.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    old_tags = metadata.get("tags", [])
    add_list = [t.strip() for t in add_tags.split(",") if t.strip()]
    remove_list = [t.strip() for t in remove_tags.split(",") if t.strip()]

    new_tags = sorted(set(old_tags + add_list) - set(remove_list))
    new_status = set_status if set_status else metadata.get("status", "draft")

    version = metadata.get("version", 1) + 1
    revisions = metadata.get("revisions", [])
    summary_parts = []
    if add_list:
        summary_parts.append(f"Added tags: {', '.join(add_list)}")
    if remove_list:
        summary_parts.append(f"Removed tags: {', '.join(remove_list)}")
    if set_status:
        summary_parts.append(f"Status → {set_status}")
    revisions.append({
        "timestamp": _now_iso(),
        "action": "tagged",
        "summary": "; ".join(summary_parts) or "Tag update",
    })

    frontmatter = _build_frontmatter(
        title=metadata.get("title", existing.stem),
        tags=new_tags,
        project=metadata.get("project", ""),
        version=version,
        revisions=revisions,
        status=new_status,
        kb_reviewed=metadata.get("kb_reviewed", False),
    )

    existing.write_text(frontmatter + "\n" + body, encoding="utf-8")

    index = _read_index()
    if existing.name in index:
        index[existing.name]["tags"] = new_tags
        index[existing.name]["status"] = new_status
        index[existing.name]["version"] = version
        index[existing.name]["updated"] = _now_iso()
        _rebuild_tag_index(index)
        _write_index(index)

    return {
        "action": "tagged",
        "filename": existing.name,
        "tags_added": add_list,
        "tags_removed": remove_list,
        "current_tags": new_tags,
        "status": new_status,
    }


def list_notes(
    tag: str = "",
    project: str = "",
    since: str = "",
    unreviewed_only: bool = False,
    status: str = "",
) -> list[dict]:
    """List research notes with optional filters."""
    index = _read_index()
    results = []

    for filename, meta in index.items():
        if filename.startswith("_"):
            continue
        if tag and tag not in meta.get("tags", []):
            continue
        if project and project.lower() not in meta.get("project", "").lower():
            continue
        if status and meta.get("status", "") != status:
            continue
        if unreviewed_only and meta.get("status", "") != "draft":
            continue
        if since:
            updated = meta.get("updated", "")
            if updated and updated[:10] < since:
                continue

        results.append({
            "filename": filename,
            "topic": meta.get("topic", ""),
            "version": meta.get("version", 1),
            "status": meta.get("status", "draft"),
            "tags": meta.get("tags", []),
            "project": meta.get("project", ""),
            "updated": meta.get("updated", ""),
        })

    results.sort(key=lambda r: r.get("updated", ""), reverse=True)
    return results


def get_note_content(topic: str) -> dict:
    """Get full content and metadata of a research note."""
    existing = _find_existing_note(topic)
    if not existing:
        return {"error": f"No note found for topic '{topic}'"}

    text = existing.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    return {
        "filename": existing.name,
        "metadata": metadata,
        "content": body,
    }


def _suggest_tags(content: str) -> list[str]:
    """Auto-suggest tags based on content analysis."""
    content_lower = content.lower()
    tag_keywords = {
        "cop": ["cost of payment", "fee", "interchange", "billed fee", "cop"],
        "fraud": ["fraud", "pims", "risk", "chargeback"],
        "pmt": ["payment transaction", "fact_transactions", "approval rate"],
        "nt": ["network token", "token lifecycle", "dpan"],
        "au": ["account updater", "card-on-file"],
        "bin": ["bin", "bank identification"],
        "databricks": ["databricks", "spark", "notebook", "cluster", "dbr"],
        "synapse": ["synapse", "pipeline", "linked service"],
        "eventhub": ["eventhub", "event hub", "consumer group"],
        "delta": ["delta lake", "delta table", "merge", "upsert"],
        "streaming": ["streaming", "structured streaming", "checkpoint"],
        "dq": ["data quality", "dq framework", "test", "assertion"],
        "grafana": ["grafana", "alert", "dashboard"],
        "deployment": ["deployment", "bicep", "ev2", "cicd"],
        "schema": ["schema", "column", "table", "star schema"],
    }

    suggested = []
    for tag, keywords in tag_keywords.items():
        if any(kw in content_lower for kw in keywords):
            suggested.append(tag)
    return suggested


def _extract_questions(content: str) -> list[str]:
    """Extract questions from content for Open Questions section."""
    questions = []
    for line in content.splitlines():
        line = line.strip()
        if line.endswith("?") and len(line) > 10:
            questions.append(line)
    return questions[:5]
