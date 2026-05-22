import json
import requests
from config import OLLAMA_URL, OLLAMA_MODEL, SYSTEM_PROMPT
from memory.conversation_log import log_message, start_session
from memory.context_builder import build_messages
from memory.chroma_store import add_document
from datetime import datetime


class Brain:
    def __init__(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._msg_counter = 0
        start_session()

    def think(self, user_input: str) -> str:
        # Log user message
        log_message("user", user_input)

        # Build RAG-augmented messages
        messages = build_messages(user_input, self.history[1:])

        response = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        })
        reply = response.json()["message"]["content"]

        # Update local history (without RAG context — keep it clean)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        # Log assistant message
        log_message("assistant", reply)

        # Embed conversation into ChromaDB periodically (every 5 exchanges)
        self._msg_counter += 1
        if self._msg_counter % 5 == 0:
            self._embed_recent()

        return reply

    def think_stream(self, user_input: str):
        log_message("user", user_input)
        messages = build_messages(user_input, self.history[1:])

        response = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": True
        }, stream=True)
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk["message"]["content"]
                full_response += token
                yield token

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": full_response})
        log_message("assistant", full_response)

        self._msg_counter += 1
        if self._msg_counter % 5 == 0:
            self._embed_recent()

    def _embed_recent(self):
        """Embed recent conversation pairs into ChromaDB for future RAG retrieval."""
        recent = self.history[-10:]  # Last 5 exchanges
        if len(recent) < 2:
            return
        text = "\n".join(f"{m['role']}: {m['content']}" for m in recent if m['role'] != 'system')
        doc_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._msg_counter}"
        add_document("conversations", doc_id, text, {"timestamp": datetime.now().isoformat()})

    def clear_history(self):
        self.history = [self.history[0]]
        self._msg_counter = 0
