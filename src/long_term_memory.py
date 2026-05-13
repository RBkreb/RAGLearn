"""Long-term memory module for cross-session storage (JSON-based)."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.messages import SystemMessage


@dataclass
class MemoryEntry:
    """A single entry in long-term memory."""

    timestamp: str
    content: str
    tags: list[str] = field(default_factory=list)
    session_id: Optional[str] = None


@dataclass
class SessionMemory:
    """Long-term memory structure for a session."""

    session_id: str
    summaries: list[MemoryEntry] = field(default_factory=list)
    key_info: list[MemoryEntry] = field(default_factory=list)
    preferences: list[MemoryEntry] = field(default_factory=list)

    def add_summary(self, content: str, tags: Optional[list[str]] = None) -> None:
        """Add a session summary."""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            content=content,
            tags=tags or [],
            session_id=self.session_id,
        )
        self.summaries.append(entry)

    def add_key_info(self, content: str, tags: Optional[list[str]] = None) -> None:
        """Add key information."""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            content=content,
            tags=tags or [],
            session_id=self.session_id,
        )
        self.key_info.append(entry)

    def search(self, query: str) -> list[str]:
        """Search memory entries by keyword/tag.

        Args:
            query: Search query.

        Returns:
            List of matching content strings.
        """
        results = []
        query_lower = query.lower()
        for entry_list in [self.summaries, self.key_info, self.preferences]:
            for entry in entry_list:
                if (query_lower in entry.content.lower() or
                    any(query_lower in tag.lower() for tag in entry.tags)):
                    results.append(entry.content)
        return results

    def to_system_message(self) -> SystemMessage:
        """Convert to system message for context injection."""
        parts = []
        if self.summaries:
            parts.append("会话摘要:")
            for s in self.summaries[-3:]:
                parts.append(f"- {s.content}")
        if self.key_info:
            parts.append("\n关键信息:")
            for k in self.key_info[-5:]:
                parts.append(f"- {k.content}")
        return SystemMessage(content="\n".join(parts) if parts else "无长期记忆")


class LongTermMemory:
    """Manages cross-session memory storage."""

    def __init__(self, storage_dir: Path) -> None:
        """Initialize long-term memory.

        Args:
            storage_dir: Directory for JSON storage.
        """
        self._storage_dir = storage_dir
        self._sessions: dict[str, SessionMemory] = {}
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _load_index(self) -> None:
        """Load all session memories from storage."""
        index_file = self._storage_dir / "index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
            for session_id in index.get("sessions", []):
                self._load_session(session_id)

    def _load_session(self, session_id: str) -> None:
        """Load a single session's memory."""
        session_file = self._storage_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = SessionMemory(session_id=session_id)
            for entry_data in data.get("summaries", []):
                session.summaries.append(MemoryEntry(**entry_data))
            for entry_data in data.get("key_info", []):
                session.key_info.append(MemoryEntry(**entry_data))
            for entry_data in data.get("preferences", []):
                session.preferences.append(MemoryEntry(**entry_data))
            self._sessions[session_id] = session

    def _save_session(self, session_id: str) -> None:
        """Save a session's memory to disk."""
        if session_id not in self._sessions:
            return
        session = self._sessions[session_id]
        session_file = self._storage_dir / f"{session_id}.json"
        data = {
            "summaries": [
                {"timestamp": e.timestamp, "content": e.content,
                 "tags": e.tags, "session_id": e.session_id}
                for e in session.summaries
            ],
            "key_info": [
                {"timestamp": e.timestamp, "content": e.content,
                 "tags": e.tags, "session_id": e.session_id}
                for e in session.key_info
            ],
            "preferences": [
                {"timestamp": e.timestamp, "content": e.content,
                 "tags": e.tags, "session_id": e.session_id}
                for e in session.preferences
            ],
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._save_index()

    def _save_index(self) -> None:
        """Save session index."""
        index_file = self._storage_dir / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump({"sessions": list(self._sessions.keys())}, f)

    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get memory for a session."""
        return self._sessions.get(session_id)

    def create_session(self, session_id: str) -> SessionMemory:
        """Create or get a session's memory."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id)
            self._save_index()
        return self._sessions[session_id]

    def add_summary(self, session_id: str, content: str, tags: Optional[list[str]] = None) -> None:
        """Add a summary to a session's memory."""
        session = self.create_session(session_id)
        session.add_summary(content, tags)
        self._save_session(session_id)

    def add_key_info(self, session_id: str, content: str, tags: Optional[list[str]] = None) -> None:
        """Add key information to a session's memory."""
        session = self.create_session(session_id)
        session.add_key_info(content, tags)
        self._save_session(session_id)

    def search_session(self, session_id: str, query: str) -> list[str]:
        """Search within a session's memory."""
        session = self._sessions.get(session_id)
        if session:
            return session.search(query)
        return []

    def get_context(self, session_id: str) -> SystemMessage:
        """Get long-term memory as system message."""
        session = self._sessions.get(session_id)
        if session:
            return session.to_system_message()
        return SystemMessage(content="无长期记忆")