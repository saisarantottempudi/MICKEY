# MICKEY — Local AI Assistant

<div align="center">

![MICKEY](assets/mickey_menubar@2x.png)

**A Jarvis/Friday-inspired personal AI assistant that runs completely locally on Apple Silicon.**

No data ever leaves your hardware. Voice-first interaction with a dark HUD-style web UI.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

</div>

---

## What It Does

MICKEY is a fully local, privacy-first AI assistant. Talk to it, give it commands, and it learns from every interaction — all without sending a single byte to the cloud.

- **Voice interaction** — Push-to-talk or wake word ("Hey Mickey", "Daddy's Home")
- **System control** — Open/close apps, read files, check calendar, get system info
- **Jarvis HUD** — Dark, glowing UI with Three.js arc reactor and voice waveform
- **Memory** — Remembers conversations, learns from mistakes, indexes your knowledge base
- **Cross-device** — Access from iPhone, iPad, or any device via Tailscale VPN
- **Smart routing** — Simple queries use fast 3B model, complex ones use 8B
- **Plugins** — Extensible: Pomodoro timer, quick notes, and easy to add more
- **Menu bar app** — Mickey Mouse icon in macOS status bar for quick access

## Architecture

```
┌─────────────────────────────────────┐
│          THIN CLIENTS               │
│   iPhone / iPad / MacBook Air       │
│   (Browser or iOS Shortcut)         │
└──────────────┬──────────────────────┘
               │ Tailscale VPN (encrypted)
┌──────────────▼──────────────────────┐
│    MacBook Pro M-series (Server)    │
│                                     │
│  nginx (HTTPS) ── React HUD        │
│       │                             │
│  Flask + SocketIO (:5050)           │
│    │      │      │      │           │
│   STT    LLM    TTS   SysCmds      │
│  Whisper Ollama  say  AppleScript   │
│    │      │                         │
│  ChromaDB + SQLite + RAG            │
│    │                                │
│  Wake Word ── Menu Bar App          │
└─────────────────────────────────────┘
```

## Tech Stack

| Layer | Tool | Role |
|-------|------|------|
| LLM | Ollama (Hermes 3 8B + Llama 3.2 3B) | Brain (multi-model routing) |
| Speech-to-text | Whisper.cpp (Metal accelerated) | Ears |
| Text-to-speech | macOS `say` | Voice |
| Backend | Python + Flask + Flask-SocketIO | Nervous system |
| Frontend | React + Vite + Three.js + Framer Motion | Jarvis HUD |
| Vector DB | ChromaDB | Long-term memory |
| Database | SQLite (WAL mode) | Conversation logs, mistakes, notes |
| Encryption | Fernet (cryptography) | Sensitive data protection |
| Remote access | Tailscale | Cross-device VPN |
| Reverse proxy | nginx | HTTPS termination |
| System control | AppleScript + Python subprocess | Hands |
| Menu bar | rumps (PyObjC) | Quick access |
| Camera | OpenCV (Haar + LBPH) | Face detection/recognition |

## Quick Start

### Prerequisites

- macOS on Apple Silicon (M1/M2/M3/M4/M5)
- [Ollama](https://ollama.com) installed
- [Homebrew](https://brew.sh)
- Node.js 18+
- Python 3.12+

### Install

```bash
# Clone
git clone https://github.com/saisarantottempudi/MICKEY.git
cd MICKEY

# Pull LLM models
ollama pull hermes3:8b
ollama pull llama3.2

# Install Whisper
brew install whisper-cpp

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Run

```bash
# Option 1: All-in-one script (backend + frontend + wake word + menu bar)
bash scripts/mickey-start.sh

# Option 2: Manual (two terminals)
# Terminal 1:
cd backend && source venv/bin/activate && python3 main.py

# Terminal 2:
cd frontend && npm run dev
```

Then open **http://localhost:5173** for the HUD.

### Auto-Start on Boot

```bash
cp config/com.mickey.assistant.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mickey.assistant.plist
```

### Cross-Device Setup

```bash
# Install Tailscale on all devices, then:
bash scripts/setup-phase4.sh
```

## Features

### Wake Word Detection
Always-on mic listening. Say any of these to activate:
- **"Hey Mickey"** — "At your service. What do you need?"
- **"Daddy's Home"** — "Welcome back, sir. All systems are online."
- **"Good Morning Mickey"** — Greeting + automatic morning briefing
- **"Yo Mickey"** — "Yo. What's the play?"

### RAG Memory System
MICKEY remembers everything:
- **Brain wiki** — Indexes your markdown knowledge base (ChromaDB)
- **Conversations** — Periodically embedded for semantic search
- **Mistakes** — Tracks corrections, avoids repeating errors

### Plugin System
Drop a `.py` file in `backend/plugins/` with a class extending `MickeyPlugin`:

```python
from plugins import MickeyPlugin

class WeatherPlugin(MickeyPlugin):
    name = "weather"
    description = "Get weather forecasts"

    def on_load(self):
        pass

    def get_commands(self):
        return [{"name": "weather", "description": "Get weather", "params": {}}]

    def handle_command(self, command, params):
        return "Sunny, 22°C"
```

Built-in plugins: **Pomodoro Timer**, **Quick Notes**

### Multi-Model Routing
- Simple queries (greetings, yes/no, basic math) → **Llama 3.2 3B** (fast)
- Complex queries (explanations, code, system commands) → **Hermes 3 8B** (smart)

### Menu Bar App
Mickey Mouse icon in your status bar with:
- Quick Chat popup
- Morning Briefing
- Pomodoro controls
- Quick Notes
- Backup/Reindex
- Start/stop wake word listener

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send text message |
| `/api/voice` | POST | Send audio, get audio response |
| `/api/health` | GET | System status + storage metrics |
| `/api/memory/search` | GET | Semantic search across all memory |
| `/api/memory/reindex` | POST | Re-index Brain wiki |
| `/api/memory/mistakes` | GET | List tracked mistakes |
| `/api/correct` | POST | Log a correction |
| `/api/maintenance` | POST | Run maintenance tasks |
| `/api/storage` | GET | Storage metrics |
| `/api/backup` | POST | Create backup |
| `/api/backups` | GET | List backups |
| `/api/camera/check` | GET | Face detection |
| `/api/camera/register` | POST | Register face |
| `/api/plugins` | GET | List plugins |
| `/api/plugins/run` | POST | Run plugin command |
| `/api/proactive/briefing` | GET | Morning briefing |
| `/api/proactive/review` | GET | Evening review |
| `/api/routing` | POST | Check model routing |
| `/api/token` | GET | Get auth token (localhost only) |

## Project Structure

```
MICKEY/
├── backend/
│   ├── main.py              # Flask entry point
│   ├── llm.py               # Brain class (Ollama interface)
│   ├── stt.py               # Whisper speech-to-text
│   ├── tts.py               # macOS text-to-speech
│   ├── intent_router.py     # Route LLM output to commands
│   ├── model_router.py      # Multi-model query routing
│   ├── auth.py              # Token authentication
│   ├── wake_word.py         # Wake word listener daemon
│   ├── menubar.py           # macOS menu bar app
│   ├── proactive.py         # Proactive suggestions scheduler
│   ├── config.py            # All settings centralized
│   ├── camera/
│   │   └── detector.py      # Face detection + recognition
│   ├── memory/
│   │   ├── chroma_store.py  # ChromaDB wrapper
│   │   ├── conversation_log.py  # SQLite logger
│   │   ├── mistake_tracker.py   # Self-correction system
│   │   ├── rag.py           # RAG retrieval pipeline
│   │   ├── brain_indexer.py # Wiki indexer
│   │   ├── context_builder.py   # Prompt assembly
│   │   ├── compressor.py    # Memory compression
│   │   ├── backup.py        # Backup system
│   │   ├── encryption.py    # Fernet encryption
│   │   └── maintenance.py   # Cleanup + optimization
│   ├── plugins/
│   │   ├── __init__.py      # Plugin base class + registry
│   │   ├── pomodoro.py      # Pomodoro timer
│   │   └── notes.py         # Quick notes
│   ├── system_commands/
│   │   ├── apps.py          # Open/close apps
│   │   ├── calendar_cmd.py  # Calendar events
│   │   ├── filesystem.py    # Read files, list dirs
│   │   └── system_info.py   # Battery, disk, wifi
│   └── audio/
│       ├── recorder.py      # Mic capture
│       └── player.py        # Audio playback
├── frontend/
│   └── src/
│       ├── App.jsx          # Main layout
│       ├── components/
│       │   ├── ArcReactor.jsx    # Three.js arc reactor
│       │   ├── VoiceWaveform.jsx # Audio visualizer
│       │   ├── ChatPanel.jsx     # Message history
│       │   ├── ResponsePanel.jsx # Streaming response
│       │   ├── StatusBar.jsx     # System status
│       │   ├── InputBar.jsx      # Text + voice input
│       │   ├── TokenGate.jsx     # Remote auth
│       │   └── HUDFrame.jsx      # Decorative borders
│       ├── hooks/
│       │   ├── useSocket.js      # WebSocket streaming
│       │   └── useAudio.js       # Mic/playback
│       └── styles/global.css     # HUD theme
├── config/                   # nginx, launchd plists
├── scripts/                  # Start/stop, setup, maintenance
├── assets/                   # Menu bar icons
└── data/                     # ChromaDB, SQLite, backups, logs
```

## Maintenance

```bash
# Manual maintenance
python3 scripts/maintenance.py daily    # Compress, vacuum, backup, cleanup
python3 scripts/maintenance.py weekly   # Daily + ChromaDB backup
python3 scripts/maintenance.py metrics  # Storage usage
python3 scripts/maintenance.py backup   # Just backups

# Automatic (launchd)
# Daily at 3:00 AM, Weekly Sundays at 3:30 AM
cp config/com.mickey.maintenance.daily.plist ~/Library/LaunchAgents/
cp config/com.mickey.maintenance.weekly.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mickey.maintenance.daily.plist
launchctl load ~/Library/LaunchAgents/com.mickey.maintenance.weekly.plist
```

## Privacy

MICKEY is designed with privacy as a hard requirement:
- **All processing is local** — LLM, STT, TTS, vector search, everything
- **No cloud dependencies** — works fully offline (after initial model download)
- **No telemetry** — zero data sent anywhere
- **Encrypted storage** — Fernet encryption for sensitive fields
- **Token auth** — remote access requires explicit token
- **HTTPS** — Tailscale provides encrypted tunnels with auto-certs

## License

MIT

## Author

**Sai Saran Tottempudi** — [GitHub](https://github.com/saisarantottempudi)
