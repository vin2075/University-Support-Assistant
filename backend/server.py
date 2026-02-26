"""
server.py — Production-Grade RAG Chat Backend (OpenRouter Edition)
------------------------------------------------------------------
- Embeddings: local sentence-transformers (no API key)
- LLM:        OpenRouter only
- CORS:       only allows http://localhost:5173
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

# ── Path & env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR))
from utils.vector_math import top_k_similar

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="University RAG Assistant", version="1.0.0")

# ── CORS — only permit the React dev server ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── OpenRouter client (the ONLY external API used) ────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY is not set. Add it to backend/.env")

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# ── Local embeddings — zero API calls ────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
print(f"📦  Loading embedding model '{EMBEDDING_MODEL_NAME}' ...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
print("✅  Embedding model ready.")

# ── Vector store ──────────────────────────────────────────────────────────────
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store.json"
vector_store: list = []


def load_vector_store():
    global vector_store
    if not VECTOR_STORE_PATH.exists():
        raise FileNotFoundError(
            f"Vector store not found at {VECTOR_STORE_PATH}. "
            "Run: python scripts/ingest.py"
        )
    with open(VECTOR_STORE_PATH, "r", encoding="utf-8") as f:
        vector_store = json.load(f)
    print(f"✅  Loaded {len(vector_store)} chunks from vector store.")


load_vector_store()

sessions: dict[str, list] = {}
MAX_HISTORY_PAIRS = 5

LLM_MODEL            = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
SIMILARITY_THRESHOLD = 0.30
TOP_K                = 3

SYSTEM_PROMPT = """You are a knowledgeable and friendly University Support Assistant.

IMPORTANT RULES:
1. Answer ONLY using the information provided in the RETRIEVED CONTEXT section below.
2. If the context does not contain enough information to answer the question, say:
   "I'm sorry, I don't have enough information about that in my knowledge base. Please contact the university directly."
3. Do not fabricate, infer, or guess any facts not present in the context.
4. Be concise, clear, and professional.
5. When relevant, mention which policy or document your answer comes from.
"""

FALLBACK_TEXT = (
    "I'm sorry, I don't have enough information about that in my knowledge base. "
    "Please contact the university directly."
)


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
            raise ValueError("Message exceeds 2000 character limit.")
        return v

    @field_validator("sessionId")
    @classmethod
    def validate_session(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("sessionId cannot be empty.")
        return v.strip()


class ChatResponse(BaseModel):
    reply: str
    tokensUsed: int
    retrievedChunks: int
    scores: list[float]
    sessionId: str


def embed_query(text: str) -> list[float]:
    try:
        return embedding_model.encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


def retrieve_chunks(query_vector: list[float]) -> list[dict]:
    return top_k_similar(query_vector, vector_store, k=TOP_K, threshold=SIMILARITY_THRESHOLD)


def build_messages(retrieved: list[dict], history: list[dict], question: str) -> list[dict]:
    context = "\n\n".join(
        f"[Source {i+1} — {c['title']}]\n{c['content']}"
        for i, c in enumerate(retrieved)
    ) if retrieved else "No relevant documents were found for this query."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-(MAX_HISTORY_PAIRS * 2):])
    messages.append({
        "role": "user",
        "content": f"RETRIEVED CONTEXT:\n{context}\n\nUSER QUESTION: {question}\n\nANSWER:"
    })
    return messages


def call_openrouter(messages: list[dict]) -> tuple[str, int]:
    try:
        response = openrouter_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
            extra_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "University RAG Assistant",
            },
        )
        reply  = (response.choices[0].message.content or "").strip()
        tokens = response.usage.total_tokens if response.usage else 0
        return reply or FALLBACK_TEXT, tokens

    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenRouter rate limit reached. Try again shortly.")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="OpenRouter request timed out.")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter error: {e}")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "chunksLoaded": len(vector_store),
        "llmModel": LLM_MODEL,
        "embeddingModel": EMBEDDING_MODEL_NAME,
        "externalAPIs": ["openrouter.ai"],
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.sessionId not in sessions:
        sessions[req.sessionId] = []
    history = sessions[req.sessionId]

    query_vector      = embed_query(req.message)
    retrieved         = retrieve_chunks(query_vector)
    messages          = build_messages(retrieved, history[-(MAX_HISTORY_PAIRS*2):], req.message)
    reply, tokens     = call_openrouter(messages)

    history.append({"role": "user",      "content": req.message})
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