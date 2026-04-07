"""
Knowledge Discovery Tools

Scans PDP repositories for architecture changes, new patterns, and knowledge to harvest.
Used by knowledge_discovery_agent for automated KB enrichment.

GUARDRAILS ENFORCED:
- SYNC-ONLY: git fetch + git pull origin main to sync accepted changes (no push/commit/reset)
- NO SECRETS: Filters out files that may contain secrets before reporting
- SAFE OPS: No destructive commands, subprocess with strict timeouts
"""

import asyncio
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger

# ---------------------------------------------------------------------------
# PDP Repository Paths
# ---------------------------------------------------------------------------
PDP_REPOS: list[str] = [
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\Commerce.PaymentsDataPlatform",
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\CFS-PaymentsJournal\CFS-Payments-DataPlatform-PaymentsJournal",
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\CFS-Payments-DataPlatform-COP",
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\CFS-Payments-DataPlatform-BIN",
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\CFS-Payments-DataPlatform-BillingService",
    r"C:\Users\v-sataroy\Commerce.PaymentsDataPlatform\CFS-Payments-DataPlatform-PaymentInstrument",
]

# ---------------------------------------------------------------------------
# Security Guardrails
# ---------------------------------------------------------------------------
SECRET_FILE_PATTERNS = [
    r"\.env$", r"\.env\.", r"secrets?\.", r"credentials?\.",
    r"\.key$", r"\.pem$", r"\.pfx$", r"\.p12$",
    r"connection[-_]?string", r"appsettings\..*\.json$",
]

SECRET_CONTENT_PATTERNS = [
    r"password\s*=", r"secret\s*=", r"api[-_]?key\s*=",
    r"connection[-_]?string\s*=", r"token\s*=",
    r"-----BEGIN", r"DefaultEndpointsProtocol=",
]


def _is_secret_file(file_path: str) -> bool:
    """Check if a file path matches known secret file patterns."""
    return any(re.search(p, file_path, re.IGNORECASE) for p in SECRET_FILE_PATTERNS)


def _redact_secrets(content: str) -> str:
    """Redact potential secret values from content."""
    for pattern in SECRET_CONTENT_PATTERNS:
        content = re.sub(pattern + r"[^\n]*", "[REDACTED]", content, flags=re.IGNORECASE)
    return content


def _validate_git_command(cmd: list[str]) -> bool:
    """Validate a git command is safe (read-only or sync-only).

    Allowed: fetch, pull, log, diff, show, status, branch, rev-parse, ls-files
    Blocked: push, commit, reset, clean, checkout (destructive), rebase, merge, stash drop
    """
    if not cmd or cmd[0] != "git":
        return False

    blocked = {
        "push", "commit", "reset", "clean", "rebase",
        "merge", "cherry-pick", "revert", "stash",
        "gc", "prune", "remote remove", "branch -D",
        "branch -d", "tag -d",
    }
    subcmd = " ".join(cmd[1:3]).lower()
    for b in blocked:
        if subcmd.startswith(b):
            logger.warning("Blocked git command: %s", " ".join(cmd))
            return False
    return True


def _safe_subprocess(
    cmd: list[str],
    cwd: str,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run a subprocess with safety guardrails."""
    if cmd[0] == "git" and not _validate_git_command(cmd):
        raise PermissionError(f"Blocked command: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _categorize_file(file_path: str) -> str:
    """Categorize a file by its path into PDP architectural areas."""
    path_lower = file_path.lower()
    if "test" in path_lower:
        return "testing"
    if "gold" in path_lower:
        return "gold-layer"
    if "silver" in path_lower:
        return "silver-layer"
    if "bronze" in path_lower:
        return "bronze-layer"
    if "deployment" in path_lower or "bicep" in path_lower or "ev2" in path_lower:
        return "infrastructure"
    if "pipeline" in path_lower or "synapse" in path_lower:
        return "orchestration"
    if "notebook" in path_lower or "databricks" in path_lower:
        return "processing"
    if "alert" in path_lower or "monitor" in path_lower:
        return "monitoring"
    if "docs" in path_lower:
        return "documentation"
    return "other"


def _sync_repo(repo_path: str) -> dict:
    """Sync a repo by fetching and pulling latest main."""
    repo_name = Path(repo_path).name
    result = {"repo": repo_name, "synced": False, "error": ""}

    if not Path(repo_path).is_dir():
        result["error"] = "Directory not found"
        return result

    try:
        # Fetch
        fetch = _safe_subprocess(["git", "fetch", "origin"], cwd=repo_path, timeout=60)
        if fetch.returncode != 0:
            result["error"] = f"Fetch failed: {fetch.stderr.strip()}"
            return result

        # Check current branch
        branch = _safe_subprocess(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
        )
        current = branch.stdout.strip()

        if current == "main":
            pull = _safe_subprocess(
                ["git", "pull", "origin", "main"],
                cwd=repo_path,
                timeout=60,
            )
            if pull.returncode != 0:
                result["error"] = f"Pull failed: {pull.stderr.strip()}"
                return result
            result["synced"] = True
            result["output"] = pull.stdout.strip()[:200]
        else:
            result["synced"] = False
            result["error"] = f"Not on main (on {current}), skipping pull"

    except subprocess.TimeoutExpired:
        result["error"] = "Timeout during sync"
    except PermissionError as e:
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def ping() -> str:
    """Health check for the knowledge discovery tools.

    Returns a simple confirmation that the discovery tools are operational.
    """
    return "Knowledge Discovery Tools operational. Ready to scan PDP repos."


@mcp.tool()
def scan_repos_for_knowledge(
    days_back: int = 7,
    repo_filter: Optional[str] = None,
    pattern_filter: Optional[str] = None,
    skip_sync: bool = False,
) -> dict:
    """Scan PDP repositories for recent changes worth harvesting into the knowledge base.

    Performs git log analysis across all PDP repos to find:
    - New or modified architecture files
    - Schema changes
    - Pipeline updates
    - Infrastructure changes
    - New patterns or conventions

    Args:
        days_back: Number of days to look back (default 7)
        repo_filter: Optional repo name substring to filter (e.g., 'BillingService')
        pattern_filter: Optional file pattern to focus on (e.g., '*.py', 'Gold/*')
        skip_sync: If True, skip git fetch/pull before scanning
    """
    repos = PDP_REPOS
    if repo_filter:
        repos = [r for r in repos if repo_filter.lower() in r.lower()]

    if not repos:
        return {"error": f"No repos matched filter '{repo_filter}'"}

    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    all_changes: list[dict] = []
    sync_results: list[dict] = []

    for repo_path in repos:
        repo_name = Path(repo_path).name

        # Sync if requested
        if not skip_sync:
            sync = _sync_repo(repo_path)
            sync_results.append(sync)

        # Get recent commits
        try:
            cmd = [
                "git", "log", f"--since={since}",
                "--pretty=format:%H|%an|%ai|%s",
                "--name-only",
            ]
            if pattern_filter:
                cmd.extend(["--", pattern_filter])

            result = _safe_subprocess(cmd, cwd=repo_path, timeout=30)
            if result.returncode != 0:
                continue

            # Parse git log output
            current_commit = None
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "|" in line and line.count("|") >= 3:
                    parts = line.split("|", 3)
                    current_commit = {
                        "repo": repo_name,
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2][:10],
                        "message": parts[3],
                        "files": [],
                    }
                elif current_commit and line:
                    if _is_secret_file(line):
                        continue
                    category = _categorize_file(line)
                    current_commit["files"].append({
                        "path": line,
                        "category": category,
                    })

            # Only include commits with relevant files
            if current_commit and current_commit.get("files"):
                all_changes.append(current_commit)

        except Exception as e:
            logger.warning("Error scanning %s: %s", repo_name, e)

    # Summarize by category
    category_counts: dict[str, int] = {}
    for change in all_changes:
        for f in change.get("files", []):
            cat = f["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "scan_period": f"Last {days_back} days (since {since})",
        "repos_scanned": len(repos),
        "total_changes": len(all_changes),
        "category_breakdown": dict(sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )),
        "sync_results": sync_results,
        "changes": all_changes[:50],  # Cap at 50 to avoid huge responses
    }


@mcp.tool()
def get_file_diff_summary(
    repo_name: str,
    repo_path: str,
    file_path: str,
    days_back: int = 7,
) -> dict:
    """Get a diff summary for a specific file in a PDP repo.

    Shows recent changes to a file with context, useful for understanding
    what changed and whether it's knowledge-base-worthy.

    Args:
        repo_name: Display name of the repo
        repo_path: Full path to the repo
        file_path: Path to the file relative to repo root
        days_back: Number of days to look back (default 7)
    """
    if _is_secret_file(file_path):
        return {"error": "Cannot display diff for potential secret file"}

    if not Path(repo_path).is_dir():
        return {"error": f"Repo not found: {repo_path}"}

    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        # Get commits touching this file
        log_result = _safe_subprocess(
            ["git", "log", f"--since={since}", "--pretty=format:%H|%ai|%s",
             "--", file_path],
            cwd=repo_path,
        )
        if log_result.returncode != 0:
            return {"error": f"Git log failed: {log_result.stderr.strip()}"}

        commits = []
        for line in log_result.stdout.strip().splitlines():
            if "|" in line:
                parts = line.split("|", 2)
                commits.append({
                    "hash": parts[0][:8],
                    "date": parts[1][:10] if len(parts) > 1 else "",
                    "message": parts[2] if len(parts) > 2 else "",
                })

        if not commits:
            return {"message": f"No changes to {file_path} in the last {days_back} days"}

        # Get latest diff
        diff_result = _safe_subprocess(
            ["git", "diff", f"HEAD~{min(len(commits), 5)}", "HEAD", "--", file_path],
            cwd=repo_path,
            timeout=15,
        )
        diff_text = diff_result.stdout[:3000] if diff_result.returncode == 0 else ""
        diff_text = _redact_secrets(diff_text)

        return {
            "repo": repo_name,
            "file": file_path,
            "category": _categorize_file(file_path),
            "commits": commits[:10],
            "diff_preview": diff_text,
        }

    except Exception as e:
        return {"error": f"Failed to get diff: {e}"}
