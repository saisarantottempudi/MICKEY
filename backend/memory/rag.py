from memory.chroma_store import query


def retrieve_context(user_input: str) -> str:
    parts = []

    # Search Brain wiki knowledge
    wiki_hits = query("brain_wiki", user_input, n_results=3)
    if wiki_hits:
        wiki_texts = [h["text"][:300] for h in wiki_hits if h["distance"] < 1.5]
        if wiki_texts:
            parts.append("Relevant knowledge from your wiki:\n" + "\n---\n".join(wiki_texts))

    # Search past conversations
    conv_hits = query("conversations", user_input, n_results=2)
    if conv_hits:
        conv_texts = [h["text"][:200] for h in conv_hits if h["distance"] < 1.2]
        if conv_texts:
            parts.append("From past conversations:\n" + "\n---\n".join(conv_texts))

    # Search past mistakes (high priority)
    mistake_hits = query("mistakes", user_input, n_results=2)
    if mistake_hits:
        mistake_texts = [h["text"] for h in mistake_hits if h["distance"] < 1.3]
        if mistake_texts:
            parts.append(
                "IMPORTANT — Previous corrections (do NOT repeat these mistakes):\n"
                + "\n---\n".join(mistake_texts)
            )

    return "\n\n".join(parts) if parts else ""
