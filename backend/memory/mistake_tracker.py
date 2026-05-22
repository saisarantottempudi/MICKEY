import sqlite3
import os
from datetime import datetime
from config import MEMORY_DB
from memory.chroma_store import add_document

_conn = None

CORRECTION_TRIGGERS = [
    "that's wrong", "thats wrong", "no,", "wrong", "incorrect",
    "that's not right", "actually,", "i meant", "correct that",
    "correct:", "fix that", "not what i asked",
]


def get_conn():
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
        _conn = sqlite3.connect(MEMORY_DB, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _init_tables(_conn)
    return _conn


def _init_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_query TEXT NOT NULL,
            wrong_response TEXT NOT NULL,
            correction TEXT NOT NULL,
            countermeasure TEXT,
            category TEXT DEFAULT 'general',
            resolved BOOLEAN DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_mistakes_category ON mistakes(category);
    """)
    conn.commit()


def is_correction(user_input: str) -> bool:
    lower = user_input.lower().strip()
    return any(trigger in lower for trigger in CORRECTION_TRIGGERS)


def log_mistake(
    user_query: str,
    wrong_response: str,
    correction: str,
    countermeasure: str = None,
    category: str = "general",
):
    conn = get_conn()
    conn.execute(
        """INSERT INTO mistakes
        (timestamp, user_query, wrong_response, correction, countermeasure, category)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(), user_query, wrong_response, correction, countermeasure, category),
    )
    conn.commit()

    # Also embed into ChromaDB for RAG retrieval
    doc_id = f"mistake_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    doc_text = (
        f"MISTAKE: When asked '{user_query}', I wrongly said '{wrong_response}'. "
        f"CORRECTION: {correction}. "
        f"COUNTERMEASURE: {countermeasure or 'Remember this correction for future.'}"
    )
    add_document("mistakes", doc_id, doc_text, {"category": category, "timestamp": datetime.now().isoformat()})


def get_recent_mistakes(limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, user_query, wrong_response, correction, countermeasure, category FROM mistakes ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {
            "timestamp": r[0], "user_query": r[1], "wrong_response": r[2],
            "correction": r[3], "countermeasure": r[4], "category": r[5],
        }
        for r in rows
    ]


def get_mistake_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) FROM mistakes").fetchone()[0]
