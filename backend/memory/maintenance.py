"""
Maintenance routines for MICKEY.
- Clean temp audio files
- Vacuum SQLite
- Compress old conversations
- Purge stale data
- Run backups
- Report storage metrics
"""

import os
import glob
import tempfile
from datetime import datetime
from config import DATA_DIR, MEMORY_DB, CHROMA_DIR, LOGS_DIR
from memory.compressor import compress_old_conversations, purge_old_conversations
from memory.backup import backup_sqlite, backup_chroma, get_backup_stats
import sqlite3


def clean_temp_audio() -> dict:
    """Delete temp WAV files created by voice pipeline."""
    temp_dir = tempfile.gettempdir()
    wav_files = glob.glob(os.path.join(temp_dir, "tmp*.wav"))
    deleted = 0
    freed = 0
    for f in wav_files:
        try:
            size = os.path.getsize(f)
            os.remove(f)
            deleted += 1
            freed += size
        except OSError:
            pass
    return {"deleted": deleted, "freed_bytes": freed}


def vacuum_sqlite() -> dict:
    """Vacuum and analyze SQLite database."""
    if not os.path.exists(MEMORY_DB):
        return {"status": "skip", "reason": "No database"}

    size_before = os.path.getsize(MEMORY_DB)
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("PRAGMA optimize")
    conn.execute("VACUUM")
    conn.execute("ANALYZE")
    conn.close()
    size_after = os.path.getsize(MEMORY_DB)

    return {
        "size_before": size_before,
        "size_after": size_after,
        "saved_bytes": size_before - size_after,
    }


def clean_old_logs(days: int = 30) -> dict:
    """Compress or delete log files older than N days."""
    if not os.path.exists(LOGS_DIR):
        return {"status": "skip"}

    import gzip

    cleaned = 0
    for f in os.listdir(LOGS_DIR):
        path = os.path.join(LOGS_DIR, f)
        if not os.path.isfile(path) or f.endswith(".gz") or f.endswith(".pid"):
            continue
        # Don't compress active logs
        if f in ("backend.log", "frontend.log", "launchd-stdout.log", "launchd-stderr.log"):
            continue
        age_days = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).days
        if age_days > days:
            # Compress old log
            with open(path, "rb") as fin:
                with gzip.open(path + ".gz", "wb") as fout:
                    fout.write(fin.read())
            os.remove(path)
            cleaned += 1

    return {"compressed": cleaned}


def get_storage_metrics() -> dict:
    """Get current storage usage for all MICKEY data."""

    def dir_size(path):
        total = 0
        if os.path.exists(path):
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total += os.path.getsize(fp)
        return total

    sqlite_size = os.path.getsize(MEMORY_DB) if os.path.exists(MEMORY_DB) else 0
    chroma_size = dir_size(CHROMA_DIR)
    logs_size = dir_size(LOGS_DIR)
    backup_stats = get_backup_stats()
    total = sqlite_size + chroma_size + logs_size + backup_stats["total_size_bytes"]

    return {
        "sqlite_bytes": sqlite_size,
        "chroma_bytes": chroma_size,
        "logs_bytes": logs_size,
        "backups_bytes": backup_stats["total_size_bytes"],
        "backups_count": backup_stats["count"],
        "total_bytes": total,
        "total_mb": round(total / (1024 * 1024), 2),
    }


def run_daily_maintenance() -> dict:
    """Run all daily maintenance tasks. Called by cron/launchd at 3 AM."""
    results = {}

    # 1. Clean temp audio
    results["audio_cleanup"] = clean_temp_audio()

    # 2. Compress old conversations (>7 days)
    results["compression"] = compress_old_conversations(days_old=7)

    # 3. Purge very old conversations (>30 days, already compressed)
    results["purge"] = purge_old_conversations(days_old=30)

    # 4. Vacuum SQLite
    results["vacuum"] = vacuum_sqlite()

    # 5. Clean old logs
    results["logs"] = clean_old_logs(days=30)

    # 6. Backup SQLite
    results["backup_sqlite"] = backup_sqlite()

    # 7. Storage metrics
    results["storage"] = get_storage_metrics()

    results["timestamp"] = datetime.now().isoformat()
    return results


def run_weekly_maintenance() -> dict:
    """Run weekly tasks (includes daily + ChromaDB backup). Sundays."""
    results = run_daily_maintenance()

    # Additional: backup ChromaDB
    results["backup_chroma"] = backup_chroma()

    return results
