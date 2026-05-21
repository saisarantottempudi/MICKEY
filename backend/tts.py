import subprocess
import tempfile
import shutil


def speak(text: str) -> str:
    if shutil.which("piper"):
        return _piper_speak(text)
    return _macos_speak(text)


def _piper_speak(text: str) -> str:
    output_path = tempfile.mktemp(suffix=".wav")
    subprocess.run(
        ["piper", "--model", "en_US-lessac-medium", "--output_file", output_path],
        input=text, text=True, timeout=30
    )
    return output_path


def _macos_speak(text: str) -> str:
    output_path = tempfile.mktemp(suffix=".aiff")
    subprocess.run(
        ["say", "-v", "Samantha", "-o", output_path, text],
        timeout=30
    )
    return output_path
