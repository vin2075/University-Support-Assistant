"""
server.py — Production-Grade RAG Chat Backend (Render Optimized)
------------------------------------------------------------------
- Embeddings: local sentence-transformers (lazy loaded)
- LLM:        OpenRouter only
- Safe for small cloud instances
"""

import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, APITimeoutError, RateLimitError, APIError
from pydantic import BaseModel, field_validator
from sentence_transformers import SentenceTransformer

# ── Paths & env ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
sys.path.insert(0, str(BASE_DIR))

from utils.vector_math import top_k_similar

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="University RAG Assistant", version="1.1.0")

FRONTEND_URL = os.getenv("FRONTEND_URL", "")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Globals (lazy loaded) ────────────────────────────────────────────────────
embedding_model = None
vector_store = None
sessions: dict[str, list] = {}

# ── Environment ──────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY is not set.")

LLM_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store.json"

SIMILARITY_THRESHOLD = 0.30
TOP_K = 3
MAX_HISTORY_PAIRS = 5

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a knowledgeable and friendly University Support Assistant.

IMPORTANT RULES:
1. Answer ONLY using the RETRIEVED CONTEXT.
2. If insufficient info, respond with:
   "I'm sorry, I don't have enough information about that in my knowledge base. Please contact the university directly."
3. Do not fabricate information.
4. Be concise and professional.
"""

FALLBACK_TEXT = (
    "I'm sorry, I don't have enough information about that in my knowledge base. "
    "Please contact the university directly."
)

# ── Lazy Loaders ─────────────────────────────────────────────────────────────
def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        print("📦 Loading embedding model...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("✅ Embedding model ready.")
    return embedding_model


def get_vector_store():
    global vector_store
    if vector_store is None:
        print("📂 Loading vector store...")
        if not VECTOR_STORE_PATH.exists():
            raise FileNotFoundError(
                f"Vector store not found at {VECTOR_STORE_PATH}. Run ingest first."
            )
        with open(VECTOR_STORE_PATH, "r", encoding="utf-8") as f:
            vector_store = json.load(f)
        print(f"✅ Loaded {len(vector_store)} chunks.")
    return vector_store


# ── Schemas ──────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    sessionId: str
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty.")
        if len(v) > 2000:
            raise ValueError("Message too long.")
        return v


class ChatResponse(BaseModel):
    reply: str
    tokensUsed: int
    retrievedChunks: int
    scores: list[float]
    sessionId: str


# ── Core Logic ───────────────────────────────────────────────────────────────
def embed_query(text: str) -> list[float]:
    try:
        model = get_embedding_model()
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


def retrieve_chunks(query_vector: list[float]) -> list[dict]:
    store = get_vector_store()
    return top_k_similar(query_vector, store, k=TOP_K, threshold=SIMILARITY_THRESHOLD)


def build_messages(retrieved, history, question):
    context = "\n\n".join(
        f"[Source {i+1} — {c['title']}]\n{c['content']}"
        for i, c in enumerate(retrieved)
    ) if retrieved else "No relevant documents found."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-(MAX_HISTORY_PAIRS * 2):])
    messages.append({
        "role": "user",
        "content": f"RETRIEVED CONTEXT:\n{context}\n\nUSER QUESTION: {question}\n\nANSWER:"
    })
    return messages


def call_openrouter(messages):
    try:
        response = openrouter_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
        )
        reply = (response.choices[0].message.content or "").strip()
        tokens = response.usage.total_tokens if response.usage else 0
        return reply or FALLBACK_TEXT, tokens

    except RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit reached.")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out.")
    except APIError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "University RAG Assistant running"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llmModel": LLM_MODEL,
        "embeddingModel": EMBEDDING_MODEL_NAME,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.sessionId not in sessions:
        sessions[req.sessionId] = []

    history = sessions[req.sessionId]

    query_vector = embed_query(req.message)
    retrieved = retrieve_chunks(query_vector)
    messages = build_messages(retrieved, history, req.message)
    reply, tokens = call_openrouter(messages)

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    sessions[req.sessionId] = history[-(MAX_HISTORY_PAIRS * 2):]

    return ChatResponse(
        reply=reply,
        tokensUsed=tokens,
        retrievedChunks=len(retrieved),
        scores=[float(c["score"]) for c in retrieved],
        sessionId=req.sessionId,
    )


@app.post("/api/session/new")
def new_session():
    sid = str(uuid.uuid4())
    sessions[sid] = []
    return {"sessionId": sid}


@app.delete("/api/session/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": True, "sessionId": session_id}