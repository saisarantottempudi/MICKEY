"""
Backup system for MICKEY data.
- SQLite backup using online backup API
- Rolling backups (keep N most recent)
- ChromaDB backup via directory copy
"""

import os
import shutil
import sqlite3
from datetime import datetime
from config import MEMORY_DB, DATA_DIR, CHROMA_DIR

BACKUP_DIR = os.path.join(DATA_DIR, "backups")
MAX_BACKUPS = 7


def _ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def backup_sqlite() -> dict:
    """Create a hot backup of the SQLite database."""
    _ensure_backup_dir()

    if not os.path.exists(MEMORY_DB):
        return {"status": "skip", "reason": "No database found"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"mickey_{timestamp}.db")

    # Use SQLite online backup API (safe even while DB is in use)
    src = sqlite3.connect(MEMORY_DB)
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()

    size = os.path.getsize(backup_path)

    # Rotate old backups
    _rotate_backups("mickey_", ".db")

    return {
        "status": "ok",
        "path": backup_path,
        "size_bytes": size,
        "timestamp": timestamp,
    }


def backup_chroma() -> dict:
    """Create a compressed backup of ChromaDB directory."""
    _ensure_backup_dir()

    if not os.path.exists(CHROMA_DIR):
        return {"status": "skip", "reason": "No ChromaDB found"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"chroma_{timestamp}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    # Copy directory then compress
    shutil.copytree(CHROMA_DIR, backup_path)
    archive_path = shutil.make_archive(backup_path, "gztar", BACKUP_DIR, backup_name)

    # Remove uncompressed copy
    shutil.rmtree(backup_path)

    size = os.path.getsize(archive_path)

    # Rotate old backups
    _rotate_backups("chroma_", ".tar.gz")

    return {
        "status": "ok",
        "path": archive_path,
        "size_bytes": size,
        "timestamp": timestamp,
    }


def _rotate_backups(prefix: str, suffix: str):
    """Keep only MAX_BACKUPS most recent files matching prefix+suffix."""
    files = sorted(
        [
            f
            for f in os.listdir(BACKUP_DIR)
            if f.startswith(prefix) and f.endswith(suffix)
        ],
        reverse=True,
    )
    for old_file in files[MAX_BACKUPS:]:
        os.remove(os.path.join(BACKUP_DIR, old_file))


def list_backups() -> list[dict]:
    """List all backups with metadata."""
    _ensure_backup_dir()
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(path):
            backups.append(
                {
                    "filename": f,
                    "size_bytes": os.path.getsize(path),
                    "created": datetime.fromtimestamp(
                        os.path.getctime(path)
                    ).isoformat(),
                }
            )
    return backups


def get_backup_stats() -> dict:
    """Get backup directory stats."""
    _ensure_backup_dir()
    total_size = sum(
        os.path.getsize(os.path.join(BACKUP_DIR, f))
        for f in os.listdir(BACKUP_DIR)
        if os.path.isfile(os.path.join(BACKUP_DIR, f))
    )
    count = len(
        [f for f in os.listdir(BACKUP_DIR) if os.path.isfile(os.path.join(BACKUP_DIR, f))]
    )
    return {"count": count, "total_size_bytes": total_size}
