from config import SYSTEM_PROMPT
from memory.rag import retrieve_context


def build_messages(user_input: str, conversation_history: list) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Retrieve RAG context
    rag_context = retrieve_context(user_input)
    if rag_context:
        messages.append({
            "role": "system",
            "content": f"Context from memory (use this to inform your response):\n{rag_context}",
        })

    # Add recent conversation history (last 20 messages to stay in token budget)
    recent = conversation_history[-20:]
    messages.extend(recent)

    messages.append({"role": "user", "content": user_input})
    return messages
