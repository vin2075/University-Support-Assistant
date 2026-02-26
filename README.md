# 🎓 University RAG Assistant

A **production-grade Retrieval-Augmented Generation (RAG)** chat assistant built with:
- **OpenRouter** — LLM gateway (free tier) for grounded response generation
- **sentence-transformers** (`all-MiniLM-L6-v2`) — Local embeddings, no API key needed
- **FastAPI** (Python) — Async REST backend
- **React + Vite + Tailwind CSS** — Modern reactive frontend
- **NumPy** — Cosine similarity vector math

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER (Browser)                             │
│                    React Chat Interface                             │
│          sessionId stored in localStorage                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  POST /api/chat
                               │  { sessionId, message }
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Embed Query   sentence-transformers (LOCAL, no API)      │  │
│  │     "How to reset?"  →  [0.12, -0.43, 0.87, ...]  (384-dim) │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────▼────────────────────────────────┐  │
│  │  2. Cosine Similarity Search    vector_store.json            │  │
│  │     Query Vector vs all chunk vectors (NumPy)                │  │
│  │     → sorted by score → top 3 above threshold 0.30          │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────▼────────────────────────────────┐  │
│  │  3. Build Augmented Prompt                                   │  │
│  │     SYSTEM: "Answer using ONLY the context below..."         │  │
│  │     CONTEXT: [Source 1 — IT Policy]\n...\n[Source 2]\n...   │  │
│  │     HISTORY: last 5 conversation pairs                       │  │
│  │     QUESTION: "How do I reset my password?"                  │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────▼────────────────────────────────┐  │
│  │  4. LLM Generation       OpenRouter (free model)             │  │
│  │     temp=0.2  max_tokens=1024                                │  │
│  │     → grounded, factual answer                               │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
│                                │                                    │
└────────────────────────────────┼────────────────────────────────────┘
                                 │  { reply, tokensUsed,
                                 │    retrievedChunks, scores }
                                 ▼
                           React renders response
                    Sidebar shows similarity scores + token count
```

---

## ✅ What I Achieved

### Core RAG Pipeline
- Built a **fully functional RAG system** from scratch with real embedding-based retrieval (not keyword matching)
- Created a **10-document university knowledge base** covering policies on attendance, grading, housing, IT, financial aid, library, parking, health, registration, and academic integrity
- Implemented **document chunking with 50-word overlap** so context is never lost at chunk boundaries
- Generated **384-dimensional embedding vectors** locally using `sentence-transformers`
- Built **cosine similarity search** using NumPy to retrieve the top-3 most relevant chunks per query
- Applied a **similarity threshold (0.30)** so irrelevant chunks are filtered out before reaching the LLM
- Constructed a **grounded system prompt** that forces the LLM to answer only from retrieved context

### Backend (FastAPI)
- Built a complete REST API with `/api/chat`, `/api/health`, `/api/session/new`, `/api/session/{id}` endpoints
- Implemented **in-memory session management** to maintain last 5 conversation pairs per user
- Added **strict CORS policy** — only allows `http://localhost:5173` (the React dev server)
- Added structured error handling for rate limits, timeouts, invalid keys, and empty responses

### Frontend (React + Vite)
- Built a full chat UI with message bubbles, timestamps, and markdown rendering
- Added **animated typing indicator** (3-dot bounce) while waiting for LLM response
- Implemented **auto-scroll** to latest message
- Added **session persistence** via `localStorage` so the session survives page refreshes
- Built a sidebar showing **similarity scores as progress bars**, token usage, and suggested questions
- Suggested questions are **clickable and send directly** to the chat

### Integration
- Connected frontend to backend via **Vite proxy** — no CORS issues during development
- Only **one external API** is used at runtime (OpenRouter) — embeddings run fully locally

---

## 🚧 Problems I Faced & How I Solved Them

### Problem 1 — Mixed API Versions in Code
**What happened:** The project went through multiple iterations. Early versions used Anthropic's Claude API + Voyage AI for embeddings. When switching to OpenRouter, some files were updated while others were not. This caused errors like:
```
OSError: VOYAGE_API_KEY is not set. Check your .env file.
```
even after creating a `.env` with `OPENROUTER_API_KEY`.

**Root cause:** There were two different `server.py` files floating around — one still importing `voyageai` and `anthropic`, and a newer one using `openai` (pointing at OpenRouter) + `sentence_transformers`. The wrong one was being run.

**Solution:** Completely replaced `server.py` with the clean OpenRouter + sentence-transformers version. Removed all references to `voyageai` and `anthropic` packages. Updated `requirements.txt` accordingly.

---

### Problem 2 — `.env` File Not Being Loaded
**What happened:** Even after creating `.env` with the correct `OPENROUTER_API_KEY`, the server kept throwing:
```
OSError: OPENROUTER_API_KEY is not set.
```

**Root cause:** The `.env` file was named `.env.example` or placed in the wrong directory. FastAPI loads the `.env` using `load_dotenv(BASE_DIR / ".env")` where `BASE_DIR` is the `backend/` folder. The file must be at `backend/.env` exactly.

**Solution:** Created the file correctly at `E:\rag-assistant\backend\.env` using:
```powershell
New-Item -Name ".env" -ItemType File
notepad .env
```

---

### Problem 3 — Frontend Could Not Reach Backend (ECONNREFUSED)
**What happened:** The React frontend showed this error in the Vite terminal:
```
Error: connect ECONNREFUSED ::1:8000
```
Messages sent from the UI never reached the backend.

**Root cause:** `vite.config.js` had `target: "http://localhost:8000"`. On Windows with Node.js 18+, `localhost` resolves to IPv6 (`::1`) by default. But `uvicorn` binds to IPv4 (`127.0.0.1`). So the proxy was connecting to the wrong address.

**Solution:** Changed the proxy target to the explicit IPv4 address:
```js
// BROKEN
target: "http://localhost:8000"

// FIXED
target: "http://127.0.0.1:8000"
```

---

### Problem 4 — OpenRouter 404: Model Not Found
**What happened:** After fixing the connection issue, the chat returned:
```
⚠️ Error: OpenRouter error: Error code: 404 -
{'error': {'message': 'No endpoints found for mistralai/mistral-7b-instruct:free.'}}
```

**Root cause:** Free model availability on OpenRouter changes frequently. The model name `mistralai/mistral-7b-instruct:free` that was referenced in earlier instructions was no longer available as a free endpoint by the time the project was running.

**What I tried:**
- `mistralai/mistral-7b-instruct:free` → 404
- `deepseek/deepseek-chat-v3-0324:free` → 404
- Multiple other model names → 404

**Solution:** Used `openrouter/free` — OpenRouter's own automatic free model router that picks whatever free model is currently available. This never 404s regardless of which individual models come and go. Set in `.env`:
```
OPENROUTER_MODEL=openrouter/free
```

---

### Problem 5 — Suggested Questions Were Dead Buttons
**What happened:** Clicking any suggested question in the sidebar did nothing. The text did not appear in the chat or get sent to the backend.

**Root cause:** The `Sidebar.jsx` component rendered the question buttons but had no `onClick` handler:
```jsx
// Dead button — no action
<button key={q} className="...">
  {q}
</button>
```
Also, `App.jsx` never passed the `handleSend` function down to `Sidebar` as a prop.

**Solution:**
1. Added `onSend` prop to `Sidebar`
2. Wired each button's `onClick` to call `onSend(q)`
3. Passed `onSend={handleSend}` from `App.jsx` to `<Sidebar />`

```jsx
// Fixed — clicking sends the question
<button key={q} onClick={() => onSend(q)} className="...">
  {q}
</button>
```

---

### Problem 6 — API Key Accidentally Exposed
**What happened:** While debugging, the actual `OPENROUTER_API_KEY` value was pasted in a chat message, making it publicly visible.

**Solution:** Immediately went to https://openrouter.ai/keys, deleted the compromised key, and generated a new one. Lesson learned: never paste real API keys anywhere — use placeholders like `sk-or-v1-xxxx` in documentation.

---

## 🏁 How I Concluded

After working through all the above problems, the final working stack is:

| Component | Original Plan | Final Solution | Reason for Change |
|-----------|--------------|----------------|-------------------|
| LLM | Anthropic Claude API | OpenRouter (free tier) | Cost — OpenRouter provides free LLM access |
| Embeddings | Voyage AI (cloud API) | sentence-transformers (local) | Eliminated a second API key requirement |
| Frontend proxy | `localhost:8000` | `127.0.0.1:8000` | IPv6 vs IPv4 resolution on Windows |
| Free model | `mistral-7b-instruct:free` | `openrouter/free` | Specific free models kept going offline |

The key insight was that **sentence-transformers running locally** was a better choice than a cloud embedding API for this use case. It removes one API dependency, works offline after the initial model download, and is fast enough for development use.

The final application successfully demonstrates all core RAG concepts:
- Real embedding-based retrieval (not keyword search)
- Cosine similarity with threshold filtering
- Context-injected grounded prompting
- Conversation history management
- Full-stack integration with React frontend

---

## 🔄 RAG Workflow Explanation

**RAG (Retrieval-Augmented Generation)** prevents hallucinations by grounding the LLM in real facts:

| Step | What Happens |
|------|-------------|
| 1. **Offline Ingestion** | Documents → chunked → embedded locally → saved to `vector_store.json` |
| 2. **Query Embedding** | User question → embedding vector (same local model as documents) |
| 3. **Similarity Search** | Cosine similarity of query vs. every chunk vector |
| 4. **Context Injection** | Top-3 relevant chunks injected into the LLM prompt |
| 5. **Grounded Response** | LLM reads ONLY the injected context to answer |

**Without RAG:** LLM guesses from training data → may hallucinate
**With RAG:** LLM reads your specific documents → factually grounded

---

## 📐 Embedding Strategy

- **Model:** `all-MiniLM-L6-v2` — runs locally, ~90 MB download, 384-dimensional vectors
- **Chunk Size:** ~300 words with 50-word overlap
- **Similarity Threshold:** 0.30 (tuned lower than cloud models since MiniLM scores run in a different range)
- **Storage:** `vector_store.json` stores both the text and its vector — no re-embedding needed at query time

### Chunking with Overlap

```
Original: "... [word 1 ... word 300] [word 251 ... word 550] ..."
                 └── Chunk 1 ──┘      └── Chunk 2 ──┘
                           └──overlap (50w)──┘
```

---

## 📏 Similarity Search Explanation

We use **cosine similarity** — the angle between two vectors in high-dimensional space:

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```

- `1.0` = identical meaning
- `0.0` = completely unrelated
- Threshold `0.30` = chunks below this score are discarded

```python
# From utils/vector_math.py
def cosine_similarity(vec_a, vec_b):
    a, b = np.array(vec_a), np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

---

## 💬 Prompt Design Reasoning

```
SYSTEM: "Answer ONLY using the context provided. Say 'I don't know' if insufficient."
          ↑ Hard grounding rule → prevents hallucination

RETRIEVED CONTEXT:
[Source 1 — IT Policy]: "... password reset steps ..."
[Source 2 — Registration]: "..."
          ↑ Real factual data injected at runtime

CONVERSATION HISTORY: (last 5 turns)
User: "What is the late fee?"
Assistant: "The late fee is $150..."
          ↑ Maintains conversational continuity

USER QUESTION: "Is there a grace period?"
          ↑ Actual user input

ANSWER:
```

**Temperature = 0.2** — Low randomness ensures consistent, factual answers.

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenRouter API key: https://openrouter.ai/keys (free signup)

---

### Step 1: Clone & Configure

```bash
git clone <your-repo-url>
cd rag-assistant
```

Create `backend/.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openrouter/free
```

---

### Step 2: Install Python dependencies

```bash
cd backend
pip install openai sentence-transformers fastapi uvicorn python-dotenv numpy pydantic
```

---

### Step 3: Generate the Vector Store (run once)

```bash
python scripts/ingest.py
```

Expected output:
```
📦  Loading embedding model 'all-MiniLM-L6-v2' ...
✅  Model ready.
📂  Loading documents... Found 10 document(s).
✂️   Chunking documents... Generated 13 chunk(s).
🔢  Generating embeddings locally...
✅  Vector store saved! 13 chunks, 384 dimensions.
```

---

### Step 4: Start the Backend

```bash
uvicorn server:app --reload --port 8000
```

Verify at: http://127.0.0.1:8000/api/health

---

### Step 5: Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: **http://localhost:5173**

---

## 📁 Project Structure

```
rag-assistant/
├── backend/
│   ├── data/
│   │   ├── docs.json              # 10 university policy documents
│   │   └── vector_store.json      # Chunks + embeddings (auto-generated)
│   ├── scripts/
│   │   └── ingest.py              # Chunking + local embedding pipeline
│   ├── utils/
│   │   └── vector_math.py         # Cosine similarity + top-k retrieval
│   ├── server.py                  # FastAPI entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx      # Scrollable message list
│   │   │   ├── Message.jsx         # Individual message bubble
│   │   │   ├── InputBar.jsx        # Text input + send button
│   │   │   ├── TypingIndicator.jsx # Animated dots
│   │   │   └── Sidebar.jsx         # Session info + suggestions
│   │   ├── App.jsx                 # Root component + session logic
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

---

## 🔌 API Reference

### `GET /api/health`
```json
{
  "status": "ok",
  "chunksLoaded": 13,
  "llmModel": "openrouter/free",
  "embeddingModel": "all-MiniLM-L6-v2",
  "externalAPIs": ["openrouter.ai"]
}
```

### `POST /api/chat`
**Request:**
```json
{ "sessionId": "abc123", "message": "How do I reset my password?" }
```
**Response:**
```json
{
  "reply": "Students can reset their university portal password at account.university.edu...",
  "tokensUsed": 312,
  "retrievedChunks": 1,
  "scores": [0.842],
  "sessionId": "abc123"
}
```

---

## 🛡️ Error Handling

| Scenario | Status | Response |
|----------|--------|----------|
| Empty message | 422 | Validation error |
| Message > 2000 chars | 422 | Validation error |
| OpenRouter rate limit | 429 | Retry message |
| OpenRouter timeout | 504 | Timeout message |
| Model not found (404) | 502 | API error detail |
| No relevant chunks | 200 | Safe fallback text |

---

## 📊 Knowledge Base Topics

1. Academic Integrity Policy
2. Attendance and Absence Policy
3. Tuition Payment and Financial Aid
4. Password Reset and IT Account Access
5. Library Resources and Borrowing Policy
6. Campus Housing and Dormitory Rules
7. Grading Scale and GPA Calculation
8. Student Health and Counseling Services
9. Course Registration and Drop/Add Policy
10. Campus Parking and Transportation