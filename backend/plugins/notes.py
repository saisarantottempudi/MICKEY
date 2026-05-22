"""
Quick Notes Plugin.
Commands: note_add, note_list, note_search
Stores notes in SQLite for quick capture during conversations.
"""

import sqlite3
import os
from datetime import datetime
from config import MEMORY_DB
from plugins import MickeyPlugin


class NotesPlugin(MickeyPlugin):
    name = "notes"
    description = "Quick note capture and retrieval"
    version = "0.1"

    def on_load(self):
        self._init_db()

    def _get_conn(self):
        os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
        conn = sqlite3.connect(MEMORY_DB, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quick_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_ts ON quick_notes(timestamp)")
        conn.commit()
        conn.close()

    def get_commands(self) -> list[dict]:
        return [
            {"name": "note_add", "description": "Add a quick note", "params": {"content": "string", "tags": "string (optional, comma-separated)"}},
            {"name": "note_list", "description": "List recent notes", "params": {"limit": "int (default 10)"}},
            {"name": "note_search", "description": "Search notes by keyword", "params": {"query": "string"}},
        ]

    def handle_command(self, command: str, params: dict) -> str:
        if command == "note_add":
            return self._add(params.get("content", ""), params.get("tags", ""))
        elif command == "note_list":
            return self._list(params.get("limit", 10))
        elif command == "note_search":
            return self._search(params.get("query", ""))
        return "Unknown notes command"

    def _add(self, content: str, tags: str = "") -> str:
        if not content:
            return "No note content provided."
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO quick_notes (timestamp, content, tags) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), content, tags),
        )
        conn.commit()
        conn.close()
        return f"📝 Note saved: \"{content[:50]}{'...' if len(content) > 50 else ''}\""

    def _list(self, limit: int = 10) -> str:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT timestamp, content, tags FROM quick_notes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        if not rows:
            return "No notes yet."
        lines = []
        for ts, content, tags in rows:
            date = ts[:10]
            tag_str = f" [{tags}]" if tags else ""
            lines.append(f"• {date}{tag_str}: {content[:80]}")
        return "\n".join(lines)

    def _search(self, query: str) -> str:
        if not query:
            return "No search query."
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT timestamp, content, tags FROM quick_notes WHERE content LIKE ? OR tags LIKE ? ORDER BY id DESC LIMIT 10",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        conn.close()
        if not rows:
            return f"No notes matching '{query}'."
        lines = [f"Found {len(rows)} note(s):"]
        for ts, content, tags in rows:
            lines.append(f"• {ts[:10]}: {content[:80]}")
        return "\n".join(lines)
