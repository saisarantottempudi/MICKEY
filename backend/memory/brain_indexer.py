import os
import re
import hashlib
from memory.chroma_store import add_documents, collection_count

BRAIN_WIKI_DIR = "/Users/mickey/Brain/wiki"


def chunk_markdown(text: str, max_chunk: int = 500) -> list[str]:
    sections = re.split(r'\n##\s+', text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section.split()) <= max_chunk:
            chunks.append(section)
        else:
            words = section.split()
            for i in range(0, len(words), max_chunk):
                chunk = " ".join(words[i:i + max_chunk])
                if len(chunk.split()) > 20:
                    chunks.append(chunk)
    return chunks


def index_brain_wiki() -> dict:
    if not os.path.isdir(BRAIN_WIKI_DIR):
        return {"status": "error", "message": f"Brain wiki not found at {BRAIN_WIKI_DIR}"}

    all_ids = []
    all_texts = []
    all_metas = []
    files_processed = 0

    for root, _, files in os.walk(BRAIN_WIKI_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, BRAIN_WIKI_DIR)

            with open(fpath, "r", errors="ignore") as f:
                content = f.read()

            chunks = chunk_markdown(content)
            for i, chunk in enumerate(chunks):
                doc_id = hashlib.md5(f"{rel_path}:{i}".encode()).hexdigest()
                all_ids.append(doc_id)
                all_texts.append(chunk)
                all_metas.append({"source": rel_path, "chunk": i})

            files_processed += 1

    if all_texts:
        # Batch in groups of 100 (ChromaDB limit)
        for start in range(0, len(all_texts), 100):
            end = min(start + 100, len(all_texts))
            add_documents("brain_wiki", all_ids[start:end], all_texts[start:end], all_metas[start:end])

    return {
        "status": "ok",
        "files_processed": files_processed,
        "chunks_indexed": len(all_texts),
        "total_in_collection": collection_count("brain_wiki"),
    }


if __name__ == "__main__":
    result = index_brain_wiki()
    print(f"Indexed {result['files_processed']} files, {result['chunks_indexed']} chunks")
