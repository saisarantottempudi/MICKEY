#!/usr/bin/env python3
"""
MICKEY Menu Bar App.

Sits in the macOS menu bar with a Mickey-style icon.
Provides quick access to all MICKEY features:
- Status indicator (green dot = online)
- Open HUD in browser
- Start/stop wake word listener
- Quick chat (text input)
- Trigger briefing
- Pomodoro controls
- System info
- Quit
"""

import rumps
import subprocess
import requests
import os
import signal
import webbrowser
import threading

BACKEND_URL = "http://localhost:5050"
FRONTEND_URL = "http://localhost:5173"
ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "mickey_menubarTemplate.png")

# Track wake word listener process
_wake_proc = None


class MickeyMenuBar(rumps.App):
    def __init__(self):
        super().__init__(
            "MICKEY",
            icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
            template=True,  # Auto light/dark mode
        )

        # Menu items
        self.status_item = rumps.MenuItem("● MICKEY: Checking...", callback=None)
        self.status_item.set_callback(None)

        self.menu = [
            self.status_item,
            None,  # separator
            rumps.MenuItem("🖥 Open HUD", callback=self.open_hud),
            rumps.MenuItem("🎙 Start Listening", callback=self.toggle_wake),
            None,
            rumps.MenuItem("💬 Quick Chat...", callback=self.quick_chat),
            rumps.MenuItem("📋 Morning Briefing", callback=self.briefing),
            self._build_pomodoro_menu(),
            rumps.MenuItem("📝 Quick Note...", callback=self.quick_note),
            None,
            rumps.MenuItem("ℹ️ System Info", callback=self.system_info),
            rumps.MenuItem("🔄 Reindex Wiki", callback=self.reindex),
            rumps.MenuItem("💾 Backup Now", callback=self.backup),
            None,
            rumps.MenuItem("⚙️ Copy Auth Token", callback=self.copy_token),
        ]

        # Start health check timer (note: _build_pomodoro_menu called above)
        self._health_timer = rumps.Timer(self.check_health, 30)
        self._health_timer.start()
        # Initial check
        threading.Thread(target=self._initial_check, daemon=True).start()

    def _initial_check(self):
        self.check_health(None)

    def _build_pomodoro_menu(self):
        """Build Pomodoro submenu."""
        pomo = rumps.MenuItem("🍅 Pomodoro")
        pomo["Start"] = rumps.MenuItem("Start", callback=self.pomo_start)
        pomo["Status"] = rumps.MenuItem("Status", callback=self.pomo_status)
        pomo["Stop"] = rumps.MenuItem("Stop", callback=self.pomo_stop)
        return pomo

    def check_health(self, _):
        try:
            r = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                model = data.get("last_model_used", "hermes3:8b")
                self.status_item.title = f"● MICKEY: Online ({model})"
                self.title = "🤖"  # or keep icon
            else:
                self.status_item.title = "○ MICKEY: Error"
        except Exception:
            self.status_item.title = "○ MICKEY: Offline"

    def open_hud(self, _):
        webbrowser.open(FRONTEND_URL)

    def toggle_wake(self, sender):
        global _wake_proc
        if _wake_proc and _wake_proc.poll() is None:
            # Stop wake word listener
            _wake_proc.terminate()
            _wake_proc = None
            sender.title = "🎙 Start Listening"
            rumps.notification("MICKEY", "", "Wake word listener stopped.")
        else:
            # Start wake word listener
            backend_dir = os.path.join(os.path.dirname(__file__))
            venv_python = os.path.join(backend_dir, "venv", "bin", "python3")
            wake_script = os.path.join(backend_dir, "wake_word.py")
            _wake_proc = subprocess.Popen(
                [venv_python, wake_script],
                cwd=backend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            sender.title = "🎙 Stop Listening"
            rumps.notification("MICKEY", "", "Wake word listener active. Say 'Hey Mickey'!")

    def quick_chat(self, _):
        window = rumps.Window(
            message="Ask MICKEY anything:",
            title="MICKEY",
            default_text="",
            ok="Send",
            cancel="Cancel",
            dimensions=(320, 60),
        )
        response = window.run()
        if response.clicked and response.text.strip():
            self._send_chat(response.text.strip())

    def _send_chat(self, message):
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={"message": message},
                timeout=60,
            )
            data = r.json()
            reply = data.get("spoken", data.get("result", "No response"))
            # Show as notification
            rumps.notification("MICKEY", message[:50], reply[:200])
            # Also speak it
            threading.Thread(
                target=self._speak, args=(reply,), daemon=True
            ).start()
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def _speak(self, text):
        subprocess.run(["say", "-v", "Samantha", text], timeout=30)

    def briefing(self, _):
        try:
            r = requests.get(f"{BACKEND_URL}/api/proactive/briefing", timeout=30)
            text = r.json().get("briefing", "No briefing available.")
            rumps.notification("MICKEY — Morning Briefing", "", text[:200])
            threading.Thread(target=self._speak, args=(text,), daemon=True).start()
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def pomo_start(self, _):
        self._plugin_cmd("pomodoro_start")

    def pomo_status(self, _):
        self._plugin_cmd("pomodoro_status")

    def pomo_stop(self, _):
        self._plugin_cmd("pomodoro_stop")

    def _plugin_cmd(self, command):
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/plugins/run",
                json={"command": command, "params": {}},
                timeout=10,
            )
            result = r.json().get("result", "Done")
            rumps.notification("MICKEY", command, result[:200])
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def quick_note(self, _):
        window = rumps.Window(
            message="Save a quick note:",
            title="MICKEY — Quick Note",
            default_text="",
            ok="Save",
            cancel="Cancel",
            dimensions=(320, 80),
        )
        response = window.run()
        if response.clicked and response.text.strip():
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/plugins/run",
                    json={"command": "note_add", "params": {"content": response.text.strip()}},
                    timeout=10,
                )
                result = r.json().get("result", "Saved")
                rumps.notification("MICKEY", "Note", result[:200])
            except Exception as e:
                rumps.notification("MICKEY", "Error", str(e)[:100])

    def system_info(self, _):
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={"message": "system info"},
                timeout=30,
            )
            data = r.json()
            result = data.get("spoken", data.get("result", "No info"))
            rumps.notification("MICKEY — System Info", "", result[:200])
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def reindex(self, _):
        try:
            r = requests.post(f"{BACKEND_URL}/api/memory/reindex", timeout=60)
            data = r.json()
            msg = f"Indexed {data.get('files_processed', '?')} files, {data.get('chunks_indexed', '?')} chunks"
            rumps.notification("MICKEY", "Wiki Reindexed", msg)
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def backup(self, _):
        try:
            r = requests.post(f"{BACKEND_URL}/api/backup", timeout=120)
            rumps.notification("MICKEY", "Backup Complete", "SQLite + ChromaDB backed up.")
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])

    def copy_token(self, _):
        try:
            r = requests.get(f"{BACKEND_URL}/api/token", timeout=5)
            token = r.json().get("token", "")
            if token:
                subprocess.run(["pbcopy"], input=token.encode(), check=True)
                rumps.notification("MICKEY", "Token Copied", "Auth token copied to clipboard.")
            else:
                rumps.notification("MICKEY", "Error", "Could not retrieve token.")
        except Exception as e:
            rumps.notification("MICKEY", "Error", str(e)[:100])


if __name__ == "__main__":
    MickeyMenuBar().run()
