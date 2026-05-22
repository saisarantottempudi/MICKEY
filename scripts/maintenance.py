#!/usr/bin/env python3
"""
MICKEY maintenance runner.
Usage:
  python3 scripts/maintenance.py daily
  python3 scripts/maintenance.py weekly
  python3 scripts/maintenance.py backup
  python3 scripts/maintenance.py metrics

Called by launchd or manually.
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from memory.maintenance import (
    run_daily_maintenance,
    run_weekly_maintenance,
    get_storage_metrics,
)
from memory.backup import backup_sqlite, backup_chroma, list_backups


def main():
    if len(sys.argv) < 2:
        print("Usage: maintenance.py [daily|weekly|backup|metrics|backups]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "daily":
        result = run_daily_maintenance()
        print(json.dumps(result, indent=2))

    elif cmd == "weekly":
        result = run_weekly_maintenance()
        print(json.dumps(result, indent=2))

    elif cmd == "backup":
        print("Backing up SQLite...")
        r1 = backup_sqlite()
        print(json.dumps(r1, indent=2))
        print("\nBacking up ChromaDB...")
        r2 = backup_chroma()
        print(json.dumps(r2, indent=2))

    elif cmd == "metrics":
        result = get_storage_metrics()
        print(json.dumps(result, indent=2))

    elif cmd == "backups":
        result = list_backups()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
