"""Session management module for multi-session support."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .short_term_memory import ShortTermMemory


@dataclass
class Session:
    """Represents a single conversation session."""

    session_id: str
    name: str
    created_at: str
    last_active: str


class SessionManager:
    """Manages multiple conversation sessions."""

    def __init__(self, storage_dir: Path) -> None:
        """Initialize session manager.

        Args:
            storage_dir: Directory for session storage.
        """
        self._storage_dir = storage_dir
        self.sessions: dict[str, Session] = {}
        self._current_session_id: Optional[str] = None
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Load all sessions from storage."""
        sessions_file = self._storage_dir / "sessions.json"
        if sessions_file.exists():
            with open(sessions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in data.get("sessions", []):
                self.sessions[s["session_id"]] = Session(**s)

    def _save_sessions(self) -> None:
        """Save all sessions to storage."""
        sessions_file = self._storage_dir / "sessions.json"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "name": s.name,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                }
                for s in self.sessions.values()
            ]
        }
        with open(sessions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_session(self, name: Optional[str] = None) -> Session:
        """Create a new session.

        Args:
            name: Optional name for the session.

        Returns:
            The created Session object.
        """
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        session = Session(
            session_id=session_id,
            name=name or session_id,
            created_at=now,
            last_active=now,
        )
        self.sessions[session_id] = session
        self._current_session_id = session_id
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: ID of session to delete.

        Returns:
            True if deleted, False if not found.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            session_dir = self._storage_dir / session_id
            if session_dir.exists():
                for f in session_dir.iterdir():
                    f.unlink()
                session_dir.rmdir()
            self._save_sessions()
            if self._current_session_id == session_id:
                self._current_session_id = None
            return True
        return False

    def switch_session(self, identifier: str) -> bool:
        """Switch to a different session by ID or name.

        Args:
            identifier: Session ID or name to switch to.

        Returns:
            True if switched, False if not found.
        """
        # Try session_id first
        if identifier in self.sessions:
            self._current_session_id = identifier
            session = self.sessions[identifier]
            session.last_active = datetime.now().isoformat()
            self._save_sessions()
            return True

        # Try session name
        for session_id, session in self.sessions.items():
            if session.name == identifier:
                self._current_session_id = session_id
                session.last_active = datetime.now().isoformat()
                self._save_sessions()
                return True

        return False

    @property
    def current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._current_session_id

    def list_sessions(self) -> list[Session]:
        """List all sessions sorted by last_active."""
        return sorted(self.sessions.values(), key=lambda s: s.last_active, reverse=True)

    def get_memory_path(self, session_id: str) -> Path:
        """Get path to session's memory file."""
        return self._storage_dir / session_id / "memory.json"

    def load_memory(self, session_id: str) -> Optional[ShortTermMemory]:
        """Load short-term memory for a session."""
        memory_path = self.get_memory_path(session_id)
        if memory_path.exists():
            return ShortTermMemory.load(memory_path)
        return None

    def save_memory(self, memory: ShortTermMemory) -> None:
        """Save short-term memory for a session."""
        memory_path = self.get_memory_path(memory.session_id)
        memory.save(memory_path)