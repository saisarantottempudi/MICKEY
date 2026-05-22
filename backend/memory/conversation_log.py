import sqlite3
import os
import uuid
from datetime import datetime
from config import MEMORY_DB

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
        _conn = sqlite3.connect(MEMORY_DB, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _init_tables(_conn)
    return _conn


def _init_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            session_id TEXT,
            intent TEXT,
            tokens_used INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp);
        CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            message_count INTEGER DEFAULT 0
        );
    """)
    conn.commit()


# Session management
_current_session = None


def start_session() -> str:
    global _current_session
    _current_session = str(uuid.uuid4())[:8]
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (id, started_at) VALUES (?, ?)",
        (_current_session, datetime.now().isoformat()),
    )
    conn.commit()
    return _current_session


def get_session() -> str:
    global _current_session
    if _current_session is None:
        _current_session = start_session()
    return _current_session


def log_message(role: str, content: str, intent: str = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO conversations (timestamp, role, content, session_id, intent) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), role, content, get_session(), intent),
    )
    conn.execute(
        "UPDATE sessions SET message_count = message_count + 1 WHERE id = ?",
        (get_session(),),
    )
    conn.commit()


def get_recent_messages(limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, role, content, intent FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {"timestamp": r[0], "role": r[1], "content": r[2], "intent": r[3]}
        for r in reversed(rows)
    ]


def get_session_messages(session_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, role, content FROM conversations WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    return [{"timestamp": r[0], "role": r[1], "content": r[2]} for r in rows]


def get_message_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]


def get_session_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
