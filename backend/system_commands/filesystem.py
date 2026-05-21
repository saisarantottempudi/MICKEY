import os


def read_file(path: str) -> str:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"File not found: {path}"
    with open(path, "r") as f:
        content = f.read(5000)
    return content


def list_directory(path: str = "~") -> str:
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return f"Not a directory: {path}"
    entries = sorted(os.listdir(path))
    return "\n".join(entries[:50])
