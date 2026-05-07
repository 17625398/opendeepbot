"""
Session Manager
===============

会话管理器 — 会话检查点保存/加载和持久化
Manages session checkpoints, save/load, and persistence for conversation state.

Provides checkpoint-based session persistence with configurable storage backends.
提供基于检查点的会话持久化，支持可配置的存储后端。
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SessionCheckpoint:
    """A single checkpoint in a session's history.
    会话历史中的单个检查点。
    """

    checkpoint_id: str
    timestamp: float
    turn_index: int
    user_message: str
    assistant_response: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionRecord:
    """Persistent record for a single conversation session.
    单个会话的持久化记录。
    """

    session_id: str
    created_at: float
    updated_at: float
    title: str = ""
    checkpoints: list[SessionCheckpoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class SessionManager:
    """
    Save, load, and manage conversation sessions with checkpoint-based persistence.

    使用基于检查点的持久化保存、加载和管理会话。

    Sessions are stored as JSON files in a configurable directory.
    会话以 JSON 文件形式存储在可配置的目录中。
    """

    DEFAULT_SESSIONS_DIR = str(Path.home() / ".deepseek" / "sessions")

    def __init__(self, sessions_dir: str | None = None) -> None:
        self._sessions_dir = sessions_dir or self.DEFAULT_SESSIONS_DIR
        self._sessions: dict[str, SessionRecord] = {}
        self._loaded = False

    # ── Directory management ──

    def _ensure_dir(self) -> None:
        """Ensure the sessions directory exists."""
        os.makedirs(self._sessions_dir, exist_ok=True)

    def _session_path(self, session_id: str) -> str:
        return os.path.join(self._sessions_dir, f"{session_id}.json")

    # ── Core operations ──

    async def save_checkpoint(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        turn_index: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Save a conversation checkpoint.

        保存对话检查点。

        Args:
            session_id: Session identifier.
            user_message: The user's message at this turn.
            assistant_response: The assistant's response.
            turn_index: Optional turn index; auto-incremented if not provided.
            metadata: Optional metadata for this checkpoint.

        Returns:
            The checkpoint_id string.
        """
        self._ensure_dir()
        record = self._get_or_create(session_id)

        if turn_index is None:
            turn_index = record.turn_count

        checkpoint = SessionCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            timestamp=time.time(),
            turn_index=turn_index,
            user_message=user_message,
            assistant_response=assistant_response,
            metadata=metadata or {},
        )

        record.checkpoints.append(checkpoint)
        record.turn_count = max(record.turn_count, turn_index + 1)
        record.updated_at = time.time()

        # Update token/cost if provided
        if metadata:
            record.total_tokens += metadata.get("tokens", 0)
            record.total_cost += metadata.get("cost", 0.0)

        self._sessions[session_id] = record
        self._persist_session(session_id)
        logger.info("Saved checkpoint %s for session %s", checkpoint.checkpoint_id[:8], session_id)
        return checkpoint.checkpoint_id

    def load_session(self, session_id: str) -> SessionRecord | None:
        """Load a session from disk."""
        path = self._session_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            record = self._deserialize_record(data)
            self._sessions[session_id] = record
            return record
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load session %s: %s", session_id, exc)
            return None

    def list_sessions(
        self, limit: int = 50, offset: int = 0
    ) -> list[SessionRecord]:
        """List sessions sorted by most recently updated."""
        self._discover_sessions()
        records = sorted(
            self._sessions.values(),
            key=lambda r: r.updated_at,
            reverse=True,
        )
        return records[offset : offset + limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        path = self._session_path(session_id)
        self._sessions.pop(session_id, None)
        try:
            os.remove(path)
            logger.info("Deleted session %s", session_id)
            return True
        except OSError:
            return False

    def get_history(
        self,
        session_id: str,
        max_turns: int | None = None,
    ) -> list[dict[str, str]]:
        """
        Get conversation history in OpenAI message format.

        以 OpenAI 消息格式获取对话历史。

        Returns a list of {"role": "user"/"assistant", "content": ...} dicts.
        """
        record = self.load_session(session_id)
        if record is None:
            return []

        checkpoints = record.checkpoints
        if max_turns is not None:
            checkpoints = checkpoints[-max_turns:]

        history: list[dict[str, str]] = []
        for c in checkpoints:
            history.append({"role": "user", "content": c.user_message})
            history.append({"role": "assistant", "content": c.assistant_response})
        return history

    def update_metadata(
        self,
        session_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """Update session-level metadata."""
        record = self._get_or_create(session_id)
        record.metadata.update(metadata)
        record.updated_at = time.time()
        self._persist_session(session_id)

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Get a session record, loading from disk if needed."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self.load_session(session_id)

    # ── Internal methods ──

    def _get_or_create(self, session_id: str) -> SessionRecord:
        """Get existing record or create a new one."""
        existing = self.get_session(session_id)
        if existing is not None:
            return existing

        record = SessionRecord(
            session_id=session_id,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._sessions[session_id] = record
        return record

    def _persist_session(self, session_id: str) -> None:
        """Write a single session to disk."""
        record = self._sessions.get(session_id)
        if record is None:
            return
        try:
            self._ensure_dir()
            data = self._serialize_record(record)
            Path(self._session_path(session_id)).write_text(
                json.dumps(data, indent=2, ensure_ascii=False)
            )
        except OSError as exc:
            logger.warning("Failed to persist session %s: %s", session_id, exc)

    def _discover_sessions(self) -> None:
        """Scan the sessions directory for all session files."""
        if self._loaded:
            return
        self._ensure_dir()
        path = Path(self._sessions_dir)
        for f in sorted(path.glob("*.json"), key=os.path.getmtime, reverse=True):
            session_id = f.stem
            if session_id not in self._sessions:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    self._sessions[session_id] = self._deserialize_record(data)
                except (OSError, json.JSONDecodeError):
                    pass
        self._loaded = True

    @staticmethod
    def _serialize_record(record: SessionRecord) -> dict[str, Any]:
        """Serialize a SessionRecord to a JSON-compatible dict."""
        return asdict(record)

    @staticmethod
    def _deserialize_record(data: dict[str, Any]) -> SessionRecord:
        """Deserialize a dict back to a SessionRecord."""
        checkpoints_data = data.pop("checkpoints", [])
        record = SessionRecord(**data)
        record.checkpoints = [
            SessionCheckpoint(**cp) for cp in checkpoints_data
        ]
        return record


# Global singleton
_global_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
