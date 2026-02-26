import json
import os
import sys
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_store.json")

CHUNK_SIZE_WORDS = 300
OVERLAP_WORDS = 50
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

def chunk_text(text, chunk_size=CHUNK_SIZE_WORDS, overlap=OVERLAP_WORDS):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += chunk_size - overlap
    return chunks

def main():
    print(f"📦  Loading embedding model '{EMBEDDING_MODEL_NAME}' (downloads ~90MB on first run)...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("✅  Model ready.")

    print(f"\n📂  Loading documents...")
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    print(f"    Found {len(docs)} document(s).")

    print("\n✂️   Chunking documents...")
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["content"])
        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{doc['id']}_chunk{idx}",
                "doc_id": doc["id"],
                "title": doc["title"],
                "content": chunk,
                "chunk_index": idx,
                "embedding": None
            })
    print(f"    Generated {len(all_chunks)} chunk(s).")

    print(f"\n🔢  Generating embeddings locally (no API key needed)...")
    texts = [f"{c['title']}: {c['content']}" for c in all_chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    for chunk, emb in zip(all_chunks, embeddings):
        chunk["embedding"] = emb.tolist()

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VECTOR_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\n✅  Vector store saved! {len(all_chunks)} chunks, {len(all_chunks[0]['embedding'])} dimensions.")
    print("🚀  Now run: uvicorn server:app --reload --port 8000")

if __name__ == "__main__":
    main()