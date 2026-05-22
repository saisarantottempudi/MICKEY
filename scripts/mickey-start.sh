#!/bin/bash
# MICKEY startup script — used by launchd and manual start
# Starts backend (Flask), frontend (Vite dev), and wake word listener

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

# Start wake word listener
cd "$MICKEY_DIR/backend"
source venv/bin/activate
python3 wake_word.py > "$LOG_DIR/wake_word.log" 2>&1 &
WAKE_PID=$!
echo "   Wake word PID: $WAKE_PID"

echo "   Backend:    http://localhost:5050"
echo "   Frontend:   http://localhost:5173"
echo "   Wake words: 'Hey Mickey', 'Daddy's Home', 'Good Morning Mickey'"
echo "🤖 MICKEY is online and listening."

# Save PIDs for stop script
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
echo "$WAKE_PID" > "$LOG_DIR/wake_word.pid"

# Wait for all
wait
