#!/usr/bin/env python3
"""
MICKEY Wake Word Listener.

Continuously monitors microphone for wake phrases:
  - "hey mickey"
  - "daddy's home"
  - "wake up mickey"
  - "yo mickey"

Flow:
  1. Listen for voice activity (volume above threshold)
  2. Record short clip (2-3 seconds)
  3. Run Whisper STT on it
  4. Check transcript for wake phrases
  5. If matched → play greeting via TTS, then enter conversation mode
  6. After conversation ends (silence timeout), return to listening

Runs as a standalone daemon. Auto-started by launchd on boot.
"""

import sounddevice as sd
import numpy as np
import wave
import tempfile
import subprocess
import time
import os
import sys
import signal
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from stt import transcribe
from tts import speak
from audio.player import play_audio

# ── Configuration ──
SAMPLE_RATE = 16000
WAKE_CLIP_DURATION = 3.0       # seconds to record for wake word check
VOICE_THRESHOLD = 0.015        # minimum volume to trigger recording
COOLDOWN_SECONDS = 5           # ignore mic for N seconds after interaction
BACKEND_URL = "http://localhost:5050"

WAKE_PHRASES = [
    "hey mickey",
    "daddy's home",
    "daddys home",
    "daddy is home",
    "wake up mickey",
    "yo mickey",
    "good morning mickey",
    "mickey",
]

# Greetings mapped to wake phrases
GREETINGS = {
    "daddy's home": [
        "Welcome back, sir. All systems are online and at your service.",
        "The prodigal father returns. What can I do for you?",
        "Good to have you back. MICKEY is ready.",
    ],
    "daddys home": [
        "Welcome back, sir. All systems are online and at your service.",
        "The prodigal father returns. What can I do for you?",
    ],
    "daddy is home": [
        "Welcome back. MICKEY is fully operational.",
    ],
    "hey mickey": [
        "At your service. What do you need?",
        "I'm here. What's up?",
        "Online and listening.",
    ],
    "good morning mickey": [
        "Good morning! Let me get your briefing ready.",
    ],
    "wake up mickey": [
        "I'm awake. Systems nominal. Ready when you are.",
    ],
    "yo mickey": [
        "Yo. What's the play?",
    ],
    "mickey": [
        "Yes?",
        "I'm listening.",
    ],
}

_running = True


def signal_handler(sig, frame):
    global _running
    print("\n🛑 Wake word listener shutting down...")
    _running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_greeting(wake_phrase: str) -> str:
    """Pick a greeting for the detected wake phrase."""
    import random

    for phrase, greetings in GREETINGS.items():
        if phrase in wake_phrase:
            return random.choice(greetings)
    return "At your service."


def record_clip(duration: float = WAKE_CLIP_DURATION) -> str:
    """Record a short audio clip and save as WAV."""
    frames = int(SAMPLE_RATE * duration)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()

    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return path


def record_until_silence(silence_threshold=0.01, silence_duration=2.0) -> str:
    """Record until silence detected (for conversation mode)."""
    chunks = []
    silent_chunks = 0
    chunk_size = int(SAMPLE_RATE * 0.1)
    max_silent = int(silence_duration / 0.1)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while True:
            data, _ = stream.read(chunk_size)
            chunks.append(data.copy())
            volume = np.abs(data).mean()
            if volume < silence_threshold:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if silent_chunks >= max_silent and len(chunks) > max_silent:
                break
            # Max 30 seconds
            if len(chunks) * 0.1 > 30:
                break

    audio = np.concatenate(chunks)
    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return path


def check_wake_word(transcript: str) -> str | None:
    """Check if transcript contains a wake phrase. Returns matched phrase or None."""
    lower = transcript.lower().strip()
    # Remove common Whisper artifacts
    lower = lower.replace("[blank_audio]", "").replace("(silence)", "").strip()
    if not lower:
        return None

    for phrase in WAKE_PHRASES:
        if phrase in lower:
            return phrase
    return None


def speak_and_play(text: str):
    """TTS + play audio."""
    audio_path = speak(text)
    play_audio(audio_path)
    try:
        os.remove(audio_path)
    except OSError:
        pass


def send_to_backend(text: str) -> str:
    """Send message to MICKEY backend and get response."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={"message": text},
            timeout=60,
        )
        data = response.json()
        return data.get("spoken", data.get("result", "I didn't catch that."))
    except Exception as e:
        return f"Backend connection error: {str(e)[:50]}"


def conversation_mode():
    """Enter conversation mode after wake word detected.
    Listen → transcribe → send to backend → speak response → repeat.
    Exit after 2 consecutive silence timeouts.
    """
    consecutive_silence = 0

    while _running and consecutive_silence < 2:
        print("  🎙  Listening for your command...")
        audio_path = record_until_silence()
        transcript = transcribe(audio_path)

        # Clean up audio file
        try:
            os.remove(audio_path)
        except OSError:
            pass

        # Skip empty/noise transcripts
        clean = transcript.strip().lower()
        clean = clean.replace("[blank_audio]", "").replace("(silence)", "").strip()
        if not clean or len(clean) < 3:
            consecutive_silence += 1
            continue

        consecutive_silence = 0
        print(f"  📝 You: {transcript}")

        # Check for exit phrases
        if any(x in clean for x in ["goodbye", "bye mickey", "that's all", "go to sleep", "never mind"]):
            speak_and_play("Going back to standby. Call me when you need me.")
            break

        # Send to backend
        response = send_to_backend(transcript)
        print(f"  🤖 MICKEY: {response[:80]}")
        speak_and_play(response)

    print("  💤 Returning to wake word listening...")


def is_voice_active() -> bool:
    """Quick check if there's voice activity on the mic."""
    try:
        audio = sd.rec(int(SAMPLE_RATE * 0.3), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        volume = np.abs(audio).mean()
        return volume > VOICE_THRESHOLD
    except Exception:
        return False


def main():
    print("=" * 50)
    print("  🤖 MICKEY Wake Word Listener")
    print("=" * 50)
    print(f"  Wake phrases: {', '.join(WAKE_PHRASES[:4])}...")
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Mic threshold: {VOICE_THRESHOLD}")
    print("  Listening... (Ctrl+C to stop)")
    print("=" * 50)

    # Wait for backend to be available
    for attempt in range(30):
        try:
            r = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
            if r.status_code == 200:
                print("  ✓ Backend is online")
                break
        except Exception:
            pass
        if attempt < 29:
            time.sleep(2)
    else:
        print("  ⚠ Backend not responding — will retry on wake")

    while _running:
        try:
            # Phase 1: Wait for voice activity
            if not is_voice_active():
                time.sleep(0.1)  # Small sleep to avoid CPU spin
                continue

            # Phase 2: Voice detected — record a short clip
            audio_path = record_clip(WAKE_CLIP_DURATION)
            transcript = transcribe(audio_path)

            # Clean up
            try:
                os.remove(audio_path)
            except OSError:
                pass

            # Phase 3: Check for wake word
            wake_phrase = check_wake_word(transcript)
            if wake_phrase:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n  🔔 [{timestamp}] Wake word detected: \"{wake_phrase}\"")

                # Greet
                greeting = get_greeting(wake_phrase)
                print(f"  🤖 {greeting}")
                speak_and_play(greeting)

                # If it was "good morning", also trigger briefing
                if "good morning" in wake_phrase:
                    try:
                        r = requests.get(f"{BACKEND_URL}/api/proactive/briefing", timeout=30)
                        briefing = r.json().get("briefing", "")
                        if briefing:
                            print(f"  📋 {briefing[:80]}")
                            speak_and_play(briefing)
                    except Exception:
                        pass

                # Enter conversation mode
                conversation_mode()

                # Cooldown
                time.sleep(COOLDOWN_SECONDS)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  ⚠ Error: {e}")
            time.sleep(1)

    print("🛑 Wake word listener stopped.")


if __name__ == "__main__":
    main()
