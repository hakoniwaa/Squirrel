"""
Claude Code log parser.

Parses session logs from ~/.claude/projects/<project-hash>/*.jsonl
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqrl.parsers.base import (
    BaseParser,
    Episode,
    EpisodeStats,
    Event,
    EventKind,
    Frustration,
    Role,
    TestStatus,
)

# Frustration detection patterns (rule-based)
FRUSTRATION_PATTERNS = {
    Frustration.SEVERE: [
        r"\b(fuck|shit|damn|wtf|ffs)\b",
        r"!!{2,}",  # Multiple exclamation marks
    ],
    Frustration.MODERATE: [
        r"\b(finally|ugh|argh|sigh)\b",
        r"\b(why (won't|doesn't|isn't|can't))",
        r"\b(still (not|doesn't|won't))",
    ],
    Frustration.MILD: [
        r"\b(hmm|hm+)\b",
        r"\?{2,}",  # Multiple question marks
    ],
}

# Error detection patterns in tool results
ERROR_PATTERNS = [
    r"error:",
    r"exception:",
    r"traceback",
    r"failed",
    r"errno",
    r"permission denied",
    r"not found",
    r"syntax error",
]

# Max length for raw snippets (truncate longer content)
MAX_SNIPPET_LENGTH = 200


def detect_frustration(text: str) -> Frustration:
    """Detect user frustration level from message text."""
    text_lower = text.lower()
    for level in [Frustration.SEVERE, Frustration.MODERATE, Frustration.MILD]:
        for pattern in FRUSTRATION_PATTERNS[level]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return level
    return Frustration.NONE


def is_error_result(text: str) -> bool:
    """Check if tool result indicates an error."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in ERROR_PATTERNS)


def truncate(text: str, max_len: int = MAX_SNIPPET_LENGTH) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def summarize_content(content: list[dict]) -> tuple[str, Optional[str], Optional[str]]:
    """
    Extract summary, tool_name, and file from message content.

    Returns: (summary, tool_name, file_path)
    """
    summary_parts = []
    tool_name = None
    file_path = None

    for block in content:
        block_type = block.get("type", "")

        if block_type == "text":
            text = block.get("text", "")
            # Truncate long text for summary
            summary_parts.append(truncate(text, 100))

        elif block_type == "tool_use":
            tool_name = block.get("name")
            tool_input = block.get("input", {})
            # Extract file path if present
            if "file_path" in tool_input:
                file_path = tool_input["file_path"]
            elif "path" in tool_input:
                file_path = tool_input["path"]
            summary_parts.append(f"[{tool_name}]")

        elif block_type == "tool_result":
            result_content = block.get("content", "")
            if isinstance(result_content, str):
                summary_parts.append(truncate(result_content, 50))

    return " ".join(summary_parts) or "(empty)", tool_name, file_path


class ClaudeCodeParser(BaseParser):
    """Parser for Claude Code session logs."""

    def __init__(self, claude_dir: Optional[Path] = None):
        self.claude_dir = claude_dir or Path.home() / ".claude"

    def _get_project_hash(self, project_path: Path) -> str:
        """Convert project path to Claude Code's hash format."""
        # Claude Code uses path with / replaced by -, prefixed with -
        return "-" + str(project_path).replace("/", "-").lstrip("-")

    def get_sessions(self, project_path: Optional[Path] = None) -> list[Path]:
        """Find all session files for a project."""
        projects_dir = self.claude_dir / "projects"
        if not projects_dir.exists():
            return []

        if project_path:
            # Look for specific project
            project_hash = self._get_project_hash(project_path)
            project_dir = projects_dir / project_hash
            if not project_dir.exists():
                return []
            dirs = [project_dir]
        else:
            # All projects
            dirs = [d for d in projects_dir.iterdir() if d.is_dir()]

        sessions = []
        for d in dirs:
            # Get JSONL files, exclude agent-* files (sub-conversations)
            for f in d.glob("*.jsonl"):
                if not f.name.startswith("agent-"):
                    sessions.append(f)

        return sorted(sessions, key=lambda p: p.stat().st_mtime)

    def parse_session(self, session_path: Path) -> list[Episode]:
        """Parse a session file into episodes."""
        events: list[Event] = []
        max_frustration = Frustration.NONE
        error_count = 0
        session_id = session_path.stem
        project_id = session_path.parent.name

        with open(session_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type")
                if entry_type not in ("user", "assistant", "system"):
                    continue

                # Parse timestamp
                ts_str = entry.get("timestamp")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except ValueError:
                    continue

                # Get message content
                message = entry.get("message", {})
                content = message.get("content", [])
                if not content:
                    continue

                # Normalize content to list of dicts
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                elif not isinstance(content, list):
                    continue

                # Determine role
                role_str = message.get("role", entry_type)
                role = Role(role_str) if role_str in Role._value2member_map_ else Role.ASSISTANT

                # Determine event kind
                has_tool_use = any(b.get("type") == "tool_use" for b in content)
                has_tool_result = any(b.get("type") == "tool_result" for b in content)

                if has_tool_use:
                    kind = EventKind.TOOL_CALL
                elif has_tool_result:
                    kind = EventKind.TOOL_RESULT
                else:
                    kind = EventKind.MESSAGE

                # Extract summary
                summary, tool_name, file_path = summarize_content(content)

                # Check for errors in tool results
                is_error = False
                if kind == EventKind.TOOL_RESULT:
                    for block in content:
                        if block.get("type") == "tool_result":
                            result_text = str(block.get("content", ""))
                            if is_error_result(result_text):
                                is_error = True
                                error_count += 1
                                break

                # Detect frustration in user messages
                if role == Role.USER and kind == EventKind.MESSAGE:
                    for block in content:
                        if block.get("type") == "text":
                            frustration = detect_frustration(block.get("text", ""))
                            if frustration.value > max_frustration.value:
                                max_frustration = frustration

                # Create event
                event = Event(
                    ts=ts,
                    role=role,
                    kind=kind,
                    summary=truncate(summary),
                    tool_name=tool_name,
                    file=file_path,
                    is_error=is_error,
                )
                events.append(event)

        if not events:
            return []

        # Create single episode from session
        # TODO: Split into multiple episodes based on task boundaries
        episode = Episode(
            session_id=session_id,
            project_id=project_id,
            start_ts=events[0].ts,
            end_ts=events[-1].ts,
            events=events,
            stats=EpisodeStats(
                error_count=error_count,
                retry_loops=0,  # TODO: detect retry loops
                user_frustration=max_frustration,
            ),
        )

        return [episode]
