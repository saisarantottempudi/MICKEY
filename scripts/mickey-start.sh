#!/bin/bash
# MICKEY startup script — used by launchd and manual start
# Starts backend (Flask) and frontend (Vite dev) together

MICKEY_DIR="/Users/mickey/MICKEY"
LOG_DIR="$MICKEY_DIR/data/logs"
mkdir -p "$LOG_DIR"

echo "🤖 Starting MICKEY..."

# Start backend
cd "$MICKEY_DIR/backend"
source venv/bin/activate
python3 main.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
for i in {1..30}; do
    if curl -s http://localhost:5050/api/health > /dev/null 2>&1; then
        echo "   Backend ready"
        break
    fi
    sleep 1
done

# Start frontend
cd "$MICKEY_DIR/frontend"
npx vite --host > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo "   Backend:  http://localhost:5050"
echo "   Frontend: http://localhost:5173"
echo "🤖 MICKEY is online."

# Save PIDs for stop script
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"

# Wait for both
wait
