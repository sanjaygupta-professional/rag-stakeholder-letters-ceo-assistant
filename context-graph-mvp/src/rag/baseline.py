"""Deliberately simple ChromaDB baseline RAG — the control group.

No graph context, no market data, no cross-company linking.
Just raw letter text → vector search → synthesis.
"""

import logging
import os

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

COLLECTION_NAME = "shareholder_letters"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def build_collection(processed_letters_dir: str = "data/processed/letters",
                     persist_dir: str = "data/chromadb") -> chromadb.Collection:
    """Build (or load) a ChromaDB collection from processed letter text files.

    Uses sentence-transformers/all-MiniLM-L6-v2 for embeddings (local, no API key).
    """
    os.makedirs(persist_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Check if already populated
    if collection.count() > 0:
        logger.info("Collection already has %d chunks, skipping build", collection.count())
        return collection

    # Load and chunk each letter
    from src.data_collection.letter_registry import LETTERS
    total_chunks = 0

    for letter in LETTERS:
        base = os.path.splitext(letter["output_filename"])[0]
        if letter["company"] == "Infosys":
            txt_name = f"{base.replace('_ar', '')}_ceo.txt"
        else:
            txt_name = f"{base}.txt"
        txt_path = os.path.join(processed_letters_dir, txt_name)

        if not os.path.exists(txt_path):
            logger.warning("Text file not found: %s", txt_path)
            continue

        with open(txt_path, encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        if not chunks:
            continue

        ids = [f"{base}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"company": letter["company"], "year": letter["year"],
             "author": letter["author"], "geography": letter["geography"]}
            for _ in chunks
        ]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        logger.info("%s: %d chunks", txt_name, len(chunks))

    logger.info("Total chunks in collection: %d", total_chunks)
    return collection


def query_baseline(collection: chromadb.Collection, query: str,
                   n_results: int = 5) -> list[dict]:
    """Simple semantic similarity search — no graph context."""
    results = collection.query(query_texts=[query], n_results=n_results)

    output = []
    for i in range(len(results["documents"][0])):
        output.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return output


def get_collection(persist_dir: str = "data/chromadb") -> chromadb.Collection:
    """Load an existing ChromaDB collection."""
    client = chromadb.PersistentClient(path=persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
