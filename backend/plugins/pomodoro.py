"""
Pomodoro Timer Plugin.
Commands: pomodoro_start, pomodoro_stop, pomodoro_status
"""

import threading
import time
from datetime import datetime
from plugins import MickeyPlugin


class PomodoroPlugin(MickeyPlugin):
    name = "pomodoro"
    description = "Pomodoro focus timer (25min work / 5min break)"
    version = "0.1"

    def on_load(self):
        self._timer = None
        self._running = False
        self._mode = "idle"  # idle, work, break
        self._started_at = None
        self._sessions_completed = 0
        self._work_duration = 25 * 60  # 25 minutes
        self._break_duration = 5 * 60   # 5 minutes
        self._remaining = 0

    def get_commands(self) -> list[dict]:
        return [
            {"name": "pomodoro_start", "description": "Start a Pomodoro work session", "params": {}},
            {"name": "pomodoro_stop", "description": "Stop the current Pomodoro", "params": {}},
            {"name": "pomodoro_status", "description": "Get Pomodoro timer status", "params": {}},
        ]

    def handle_command(self, command: str, params: dict) -> str:
        if command == "pomodoro_start":
            return self._start()
        elif command == "pomodoro_stop":
            return self._stop()
        elif command == "pomodoro_status":
            return self._status()
        return "Unknown pomodoro command"

    def _start(self) -> str:
        if self._running:
            return f"Pomodoro already running. {self._status()}"

        self._running = True
        self._mode = "work"
        self._started_at = datetime.now()
        self._remaining = self._work_duration

        self._timer = threading.Thread(target=self._countdown, daemon=True)
        self._timer.start()

        return "🍅 Pomodoro started! 25 minutes of focus. You got this."

    def _stop(self) -> str:
        if not self._running:
            return "No Pomodoro running."
        self._running = False
        self._mode = "idle"
        return f"Pomodoro stopped. Sessions completed today: {self._sessions_completed}."

    def _status(self) -> str:
        if not self._running:
            return f"No active Pomodoro. Sessions completed: {self._sessions_completed}."
        mins = self._remaining // 60
        secs = self._remaining % 60
        return f"🍅 {self._mode.upper()}: {mins}:{secs:02d} remaining. Sessions: {self._sessions_completed}."

    def _countdown(self):
        while self._running and self._remaining > 0:
            time.sleep(1)
            self._remaining -= 1

        if self._running:
            if self._mode == "work":
                self._sessions_completed += 1
                self._mode = "break"
                self._remaining = self._break_duration
                print(f"[Pomodoro] Work session done! Take a {self._break_duration // 60}min break.")
                self._countdown()  # Auto-start break
            elif self._mode == "break":
                self._mode = "idle"
                self._running = False
                print("[Pomodoro] Break over! Ready for another session?")
