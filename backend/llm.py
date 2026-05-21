import json
import requests
from config import OLLAMA_URL, OLLAMA_MODEL, SYSTEM_PROMPT


class Brain:
    def __init__(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def think(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        response = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": self.history,
            "stream": False
        })
        reply = response.json()["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def think_stream(self, user_input: str):
        self.history.append({"role": "user", "content": user_input})
        response = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": self.history,
            "stream": True
        }, stream=True)
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk["message"]["content"]
                full_response += token
                yield token
        self.history.append({"role": "assistant", "content": full_response})

    def clear_history(self):
        self.history = [self.history[0]]
