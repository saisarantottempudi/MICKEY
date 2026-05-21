import subprocess
import os

WHISPER_CMD = "whisper-cli"


def transcribe(audio_path: str, model: str = "base") -> str:
    model_path = _find_model(model)
    if not model_path:
        return f"[Whisper model '{model}' not found]"

    result = subprocess.run(
        [WHISPER_CMD, "-m", model_path, "-f", audio_path, "--no-timestamps"],
        capture_output=True, text=True, timeout=30
    )
    text = result.stdout.strip()
    if not text and result.stderr:
        return f"[Whisper error: {result.stderr.strip()[:200]}]"
    return text


def _find_model(model: str) -> str:
    search_paths = [
        f"/opt/homebrew/share/whisper-cpp/models/ggml-{model}.bin",
        f"/usr/local/share/whisper-cpp/models/ggml-{model}.bin",
        os.path.expanduser(f"~/MICKEY/models/whisper/ggml-{model}.bin"),
    ]
    for path in search_paths:
        if os.path.exists(path):
            return path
    return ""
