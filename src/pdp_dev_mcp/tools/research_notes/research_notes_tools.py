"""
Research Notes MCP Tools

MCP-decorated tools for capturing, tagging, and listing research notes
stored in the research vault (.research-vault/).

These are standalone tools invoked from Copilot's tools dropdown during
independent research sessions. They are NOT part of the chatbot UI —
they're fire-and-forget actions that build your personal knowledge vault.

The Knowledge Scavenger agent (future) will scan the vault for notes
worth promoting into the PDP Architecture knowledge base.
"""

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger
from . import research_notes_service
from .research_notes_service import (
    capture_notes,
    tag_notes,
    list_notes,
    get_note_content,
    VAULT_DIR,
)


@mcp.tool()
def capture_research_notes(
    topic: str,
    content: str,
    tags: str = "",
    project: str = "",
    mode: str = "auto",
    review_notes: str = "",
) -> str:
    """Capture or update research notes in the personal research vault.

    Saves structured markdown with YAML frontmatter to .research-vault/ outside all repos.
    Notes include version tracking, auto-suggested tags, revision history, and KB integration status.

    Modes:
      auto   — If a note with matching topic exists, update it. Otherwise create new.
      create — Always create a new note (even if topic exists).
      update — Append to existing note. Creates new if not found.
      review — Mark existing note as reviewed, add review notes. No content change.

    Every invocation:
      - Increments version number
      - Logs revision with timestamp, action, and summary
      - Auto-suggests tags based on content analysis (COP, fraud, databricks, etc.)
      - Records tags_added / tags_removed in revision history
      - Updates the vault index.json

    Example usage:
      capture_research_notes(
          topic="COP Fee Reconciliation",
          content="Found that interchange fees from Adyen have a 2-day lag...",
          tags="cop, adyen",
          project="CFS-Payments-DataPlatform-COP"
      )
    """
    result = capture_notes(
        topic=topic,
        content=content,
        tags=tags,
        project=project,
        mode=mode,
        review_notes=review_notes,
    )
    if "error" in result:
        return f"Error: {result['error']}"

    action = result.get("action", "unknown")
    filename = result.get("filename", "")
    version = result.get("version", 1)
    tags_list = result.get("tags", [])

    return (
        f"Research note {action}: {filename} (v{version})\n"
        f"Tags: {', '.join(tags_list)}\n"
        f"Vault: {VAULT_DIR}"
    )


@mcp.tool()
def tag_research_notes(
    topic: str,
    add_tags: str = "",
    remove_tags: str = "",
    set_status: str = "",
) -> str:
    """Add or remove tags on a research note, or change its status.

    Every tag change is logged as a revision with full provenance tracking.

    Statuses: draft, reviewed, promoted, archived
      - draft: Initial state after capture
      - reviewed: You've validated the content
      - promoted: Scavenger has integrated into KB
      - archived: No longer active (Scavenger skips these)

    Example usage:
      tag_research_notes(
          topic="COP Fee Reconciliation",
          add_tags="validated, production-verified",
          remove_tags="unverified",
          set_status="reviewed"
      )
    """
    result = tag_notes(
        topic=topic,
        add_tags=add_tags,
        remove_tags=remove_tags,
        set_status=set_status,
    )
    if "error" in result:
        return f"Error: {result['error']}"

    return (
        f"Note updated: {result.get('filename', '')}\n"
        f"Current tags: {', '.join(result.get('current_tags', []))}\n"
        f"Status: {result.get('status', 'draft')}"
    )


@mcp.tool()
def list_research_notes(
    tag: str = "",
    project: str = "",
    since: str = "",
    unreviewed_only: bool = False,
    status: str = "",
) -> str:
    """List research notes from the vault with optional filters.

    Filters:
      - tag: Show only notes with this tag (e.g. "cop", "fraud", "databricks")
      - project: Filter by PDP project name
      - since: Date filter (YYYY-MM-DD) — notes modified on or after this date
      - unreviewed_only: Only notes not yet integrated into the KB
      - status: Filter by status (draft / reviewed / promoted / archived)

    Returns a table of notes with topic, version, status, tags, and last modified date.

    Example: list_research_notes(tag="cop", status="draft")
    """
    results = list_notes(
        tag=tag,
        project=project,
        since=since,
        unreviewed_only=unreviewed_only,
        status=status,
    )
    if not results:
        return "No research notes found matching the given filters."

    lines = ["| Topic | Version | Status | Tags | Updated |",
             "|-------|---------|--------|------|---------|"]
    for note in results:
        tags_str = ", ".join(note.get("tags", [])[:5])
        lines.append(
            f"| {note.get('topic', '')} | v{note.get('version', 1)} "
            f"| {note.get('status', 'draft')} | {tags_str} "
            f"| {note.get('updated', '')[:10]} |"
        )
    return "\n".join(lines)


@mcp.tool()
def get_research_note(topic: str) -> str:
    """Get the full content and metadata of a specific research note.

    Returns the complete note including YAML frontmatter, revision history,
    all sections (Key Findings, Updates, Open Questions, Raw Notes), and
    current tags/status.

    Use this to review a note's content before updating or promoting it.
    """
    result = get_note_content(topic)
    if "error" in result:
        return f"Error: {result['error']}"

    metadata = result.get("metadata", {})
    content = result.get("content", "")
    filename = result.get("filename", "")

    header_lines = [
        f"**File:** {filename}",
        f"**Status:** {metadata.get('status', 'draft')}",
        f"**Version:** {metadata.get('version', 1)}",
        f"**Tags:** {', '.join(metadata.get('tags', []))}",
        f"**Project:** {metadata.get('project', 'N/A')}",
        f"**Created:** {metadata.get('created', 'N/A')}",
        f"**Updated:** {metadata.get('updated', 'N/A')}",
        "",
        "---",
        "",
    ]
    return "\n".join(header_lines) + content
