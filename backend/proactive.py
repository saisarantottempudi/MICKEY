"""
Proactive suggestions system.
Generates contextual notifications based on time, calendar, and patterns.

Runs as a background thread — checks every 15 minutes.
Emits events via SocketIO when something worth saying is found.
"""

import threading
import time
from datetime import datetime, timedelta
from config import OLLAMA_URL, OLLAMA_MODEL
from system_commands.calendar_cmd import get_today_events
from system_commands.system_info import get_info
import requests


class ProactiveScheduler:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self._running = False
        self._thread = None
        self._last_briefing = None
        self._last_reminder = None
        self._check_interval = 900  # 15 minutes

    def start(self):
        """Start background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._check()
            except Exception as e:
                print(f"Proactive check error: {e}")
            time.sleep(self._check_interval)

    def _check(self):
        now = datetime.now()
        hour = now.hour

        # Morning briefing (7-9 AM, once per day)
        if 7 <= hour <= 9 and self._should_brief("morning"):
            briefing = self.generate_morning_briefing()
            self._emit("proactive_message", {
                "type": "morning_briefing",
                "message": briefing,
                "timestamp": now.isoformat(),
            })
            self._last_briefing = now.date()

        # Meeting reminder (check upcoming events)
        if self._should_remind():
            reminder = self._check_upcoming_events()
            if reminder:
                self._emit("proactive_message", {
                    "type": "meeting_reminder",
                    "message": reminder,
                    "timestamp": now.isoformat(),
                })
                self._last_reminder = now

        # Evening review (8-10 PM, once per day)
        if 20 <= hour <= 22 and self._should_brief("evening"):
            review = self.generate_evening_review()
            self._emit("proactive_message", {
                "type": "evening_review",
                "message": review,
                "timestamp": now.isoformat(),
            })

        # Low battery warning
        try:
            info = get_info()
            if "battery" in info.lower():
                # Parse battery percentage
                for part in info.split("\n"):
                    if "battery" in part.lower() and "%" in part:
                        pct = int("".join(c for c in part.split("%")[0].split()[-1] if c.isdigit()))
                        if pct < 15:
                            self._emit("proactive_message", {
                                "type": "battery_warning",
                                "message": f"Battery at {pct}%. Might want to plug in.",
                                "timestamp": now.isoformat(),
                            })
        except Exception:
            pass

    def _should_brief(self, kind: str) -> bool:
        today = datetime.now().date()
        if kind == "morning":
            return self._last_briefing != today
        return True  # evening: simple daily check

    def _should_remind(self) -> bool:
        if self._last_reminder is None:
            return True
        return (datetime.now() - self._last_reminder).seconds > 1800  # 30 min cooldown

    def _check_upcoming_events(self) -> str | None:
        """Check if any calendar events are starting in the next 15 minutes."""
        try:
            events = get_today_events()
            if not events or events == "No events today.":
                return None
            # Simple heuristic: check if any event mentions a time close to now
            now = datetime.now()
            # Parse events for times — this is best-effort
            for line in events.split("\n"):
                # Look for HH:MM patterns
                import re
                times = re.findall(r"(\d{1,2}):(\d{2})", line)
                for h, m in times:
                    event_time = now.replace(hour=int(h), minute=int(m), second=0)
                    diff = (event_time - now).total_seconds()
                    if 0 < diff <= 900:  # Within 15 minutes
                        return f"Heads up — you have something coming up in {int(diff/60)} minutes: {line.strip()}"
            return None
        except Exception:
            return None

    def generate_morning_briefing(self) -> str:
        """Generate a morning briefing using LLM."""
        try:
            events = get_today_events()
            sys_info = get_info()
            day = datetime.now().strftime("%A, %B %d")

            prompt = (
                f"Today is {day}. Generate a brief, friendly morning briefing for Mickey.\n"
                f"Calendar: {events}\n"
                f"System: {sys_info}\n"
                "Keep it under 3 sentences. Be like Jarvis — concise, helpful, slightly witty."
            )

            response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=30,
            )
            return response.json()["message"]["content"]
        except Exception as e:
            return f"Good morning. Systems online. {str(e)[:50] if str(e) else 'Ready when you are.'}"

    def generate_evening_review(self) -> str:
        """Generate an evening review."""
        try:
            from memory.conversation_log import get_message_count

            msg_count = get_message_count()
            prompt = (
                f"Generate a brief evening sign-off for Mickey. "
                f"We had {msg_count} messages today. "
                "Remind him to rest. One sentence, Jarvis-style."
            )

            response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=30,
            )
            return response.json()["message"]["content"]
        except Exception:
            return "Systems nominal. Get some rest — tomorrow's another day."

    def _emit(self, event: str, data: dict):
        """Emit via SocketIO if available."""
        if self.socketio:
            self.socketio.emit(event, data)
        print(f"[Proactive] {data.get('type')}: {data.get('message', '')[:80]}")

    # Manual triggers
    def trigger_briefing(self) -> str:
        return self.generate_morning_briefing()

    def trigger_review(self) -> str:
        return self.generate_evening_review()
