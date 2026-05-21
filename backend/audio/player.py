import subprocess


def play_audio(path: str):
    subprocess.run(["afplay", path])
