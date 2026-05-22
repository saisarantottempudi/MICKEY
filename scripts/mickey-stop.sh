#!/bin/bash
# Stop MICKEY services

LOG_DIR="/Users/mickey/MICKEY/data/logs"

echo "🛑 Stopping MICKEY..."

# Kill by PID files
for svc in backend frontend; do
    PID_FILE="$LOG_DIR/$svc.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "   Stopped $svc (PID $PID)"
        fi
        rm -f "$PID_FILE"
    fi
done

# Also kill by port as fallback
kill $(lsof -ti:5050) 2>/dev/null
kill $(lsof -ti:5173) 2>/dev/null

echo "🛑 MICKEY stopped."
