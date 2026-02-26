"""
download_model.py
-----------------
Run during build to pre-download the sentence-transformers model.
This prevents startup timeout on Render — the model is cached before
the server ever tries to start.
"""
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
print(f"📦  Downloading model '{MODEL_NAME}' ...")
model = SentenceTransformer(MODEL_NAME)
print(f"✅  Model downloaded and cached. Dimensions: {model.get_sentence_embedding_dimension()}")