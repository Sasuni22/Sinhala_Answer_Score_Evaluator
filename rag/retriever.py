"""
RAG Pipeline: Offline retrieval using ChromaDB + sentence-transformers
"""

import os
import logging
import warnings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["ALLOW_RESET"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from pathlib import Path

KB_DIR     = Path(__file__).parent.parent / "data" / "knowledge_base"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_client     = None
_collection = None
_ef         = None


def _get_client():
    global _client
    if _client is None:
        # Import here, not at module level — avoids SessionInfo error
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def _get_ef():
    global _ef
    if _ef is None:
        # Import here, not at module level
        from chromadb.utils import embedding_functions
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
    return _ef


def build_vector_store(force_rebuild: bool = False):
    global _collection

    if _collection is not None and not force_rebuild:
        return _collection

    try:
        client = _get_client()
        ef     = _get_ef()
        collection_name = "anuradhapura_kb"

        existing = [c.name for c in client.list_collections()]

        if force_rebuild and collection_name in existing:
            client.delete_collection(collection_name)
            existing = []

        if collection_name in existing:
            _collection = client.get_collection(
                name=collection_name,
                embedding_function=ef,
            )
            return _collection

        _collection = client.create_collection(
            name=collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

        docs, metadatas, ids = [], [], []
        chunk_id = 0

        for txt_file in sorted(KB_DIR.glob("*.txt")):
            content    = txt_file.read_text(encoding="utf-8")
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
            for para in paragraphs:
                docs.append(para)
                metadatas.append({"source": txt_file.name, "file": txt_file.stem})
                ids.append(f"chunk_{chunk_id}")
                chunk_id += 1

        if docs:
            batch_size = 50
            for i in range(0, len(docs), batch_size):
                _collection.add(
                    documents=docs[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                    ids=ids[i : i + batch_size],
                )

        return _collection

    except Exception as e:
        # Return None gracefully — pipeline will skip RAG
        print(f"[RAG] Vector store unavailable: {e}")
        return None


def retrieve_context(query: str, n_results: int = 3) -> list[dict]:
    try:
        collection = build_vector_store()
        if collection is None:
            return []

        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        if results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                retrieved.append({
                    "text":      doc,
                    "source":    meta.get("source", "unknown"),
                    "relevance": round(1 - dist, 3),
                })
        return retrieved

    except Exception as e:
        print(f"[RAG] Retrieval failed: {e}")
        return []


def format_context_for_prompt(contexts: list[dict]) -> str:
    if not contexts:
        return ""
    parts = []
    for i, ctx in enumerate(contexts, 1):
        parts.append(f"[Context {i} - {ctx['source']}]\n{ctx['text']}")
    return "\n\n".join(parts)