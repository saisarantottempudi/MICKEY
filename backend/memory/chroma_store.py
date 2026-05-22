import chromadb
from config import CHROMA_DIR

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def get_or_create_collection(name: str):
    return get_client().get_or_create_collection(name=name)


def add_document(collection_name: str, doc_id: str, text: str, metadata: dict = None):
    collection = get_or_create_collection(collection_name)
    collection.upsert(documents=[text], ids=[doc_id], metadatas=[metadata or {}])


def add_documents(collection_name: str, doc_ids: list, texts: list, metadatas: list = None):
    collection = get_or_create_collection(collection_name)
    collection.upsert(
        documents=texts,
        ids=doc_ids,
        metadatas=metadatas or [{} for _ in texts],
    )


def query(collection_name: str, query_text: str, n_results: int = 3) -> list[dict]:
    collection = get_or_create_collection(collection_name)
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query_text], n_results=min(n_results, collection.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    return [{"text": d, "metadata": m, "distance": dist} for d, m, dist in zip(docs, metas, dists)]


def delete_document(collection_name: str, doc_id: str):
    collection = get_or_create_collection(collection_name)
    collection.delete(ids=[doc_id])


def collection_count(collection_name: str) -> int:
    return get_or_create_collection(collection_name).count()
