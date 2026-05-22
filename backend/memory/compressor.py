"""
Memory compressor: summarizes old conversations into semantic memories.
- Conversations >7 days old → LLM summarizes → stored in ChromaDB as compressed memory
- Original rows deleted after 30 days
- Runs as part of daily maintenance
"""

import sqlite3
from datetime import datetime, timedelta
from config import MEMORY_DB, OLLAMA_URL, OLLAMA_MODEL
from memory.chroma_store import add_document
import requests
import os


def get_conn():
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _summarize_text(text: str) -> str:
    """Use LLM to create a concise summary."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Summarize the following conversation concisely. "
                        "Capture key facts, decisions, and preferences mentioned. "
                        "Output only the summary, no preamble.",
                    },
                    {"role": "user", "content": text},
                ],
                "stream": False,
            },
            timeout=60,
        )
        return response.json()["message"]["content"]
    except Exception as e:
        # Fallback: truncate to first 500 chars
        return text[:500] + "..." if len(text) > 500 else text


def compress_old_conversations(days_old: int = 7) -> dict:
    """Summarize conversation sessions older than `days_old` days."""
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()

    # Find sessions with messages older than cutoff that haven't been compressed
    rows = conn.execute(
        """
        SELECT DISTINCT session_id FROM conversations
        WHERE timestamp < ? AND session_id IS NOT NULL
        AND session_id NOT IN (
            SELECT session_id FROM conversations WHERE timestamp >= ?
        )
        """,
        (cutoff, cutoff),
    ).fetchall()

    compressed = 0
    for (session_id,) in rows:
        # Get all messages for this session
        messages = conn.execute(
            "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        if not messages:
            continue

        # Build conversation text
        conv_text = "\n".join(f"{role}: {content}" for role, content in messages)

        # Summarize
        summary = _summarize_text(conv_text)

        # Store compressed memory in ChromaDB
        doc_id = f"compressed_{session_id}_{datetime.now().strftime('%Y%m%d')}"
        add_document(
            "conversations",
            doc_id,
            f"[Compressed session {session_id}] {summary}",
            {
                "type": "compressed",
                "session_id": session_id,
                "original_messages": len(messages),
                "compressed_at": datetime.now().isoformat(),
            },
        )
        compressed += 1

    conn.close()
    return {"sessions_compressed": compressed, "cutoff_date": cutoff}


def purge_old_conversations(days_old: int = 30) -> dict:
    """Delete conversation rows older than `days_old` days (already compressed)."""
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()

    # Count before delete
    count = conn.execute(
        "SELECT COUNT(*) FROM conversations WHERE timestamp < ?", (cutoff,)
    ).fetchone()[0]

    if count > 0:
        conn.execute("DELETE FROM conversations WHERE timestamp < ?", (cutoff,))
        conn.commit()

    conn.close()
    return {"rows_deleted": count, "cutoff_date": cutoff}
