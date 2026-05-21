import subprocess


def open_app(name: str) -> str:
    subprocess.run(["osascript", "-e", f'tell application "{name}" to activate'])
    return f"Opened {name}"


def close_app(name: str) -> str:
    subprocess.run(["osascript", "-e", f'tell application "{name}" to quit'])
    return f"Closed {name}"
