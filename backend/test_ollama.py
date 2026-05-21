import requests
from config import OLLAMA_URL, OLLAMA_MODEL

response = requests.post(f"{OLLAMA_URL}/api/generate", json={
    "model": OLLAMA_MODEL,
    "prompt": "You are MICKEY, a personal AI assistant. Say hello and introduce yourself in 2 sentences.",
    "stream": False
})

if response.status_code == 200:
    print(response.json()["response"])
else:
    print(f"Error: {response.status_code} — {response.text}")
