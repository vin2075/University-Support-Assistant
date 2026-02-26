import numpy as np


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """
    Computes the cosine similarity between two vectors.
    Returns a float between -1 and 1, where 1 = identical direction.
    """
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Guard against division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def top_k_similar(query_vector: list, documents: list, k: int = 3, threshold: float = 0.4) -> list:
    """
    Given a query embedding and a list of document dicts (each with an 'embedding' key),
    returns the top-k documents sorted by cosine similarity, filtered by threshold.

    Args:
        query_vector: The embedding of the user query.
        documents: List of dicts, each containing at least {"embedding": [...], ...}.
        k: Number of top results to return.
        threshold: Minimum similarity score to consider a document relevant.

    Returns:
        List of document dicts with an additional 'score' key, sorted descending.
    """
    scored = []
    for doc in documents:
        score = cosine_similarity(query_vector, doc["embedding"])
        if score >= threshold:
            scored.append({**doc, "score": round(score, 6)})

    # Sort by score descending and return top k
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
