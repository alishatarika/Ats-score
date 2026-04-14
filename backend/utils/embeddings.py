import threading
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as _sk_cosine

_LOCK   = threading.Lock()
_MODEL: SentenceTransformer | None = None
_MODEL_NAME = "all-MiniLM-L6-v2"



def get_model() -> SentenceTransformer:
    """Return the shared SentenceTransformer instance (lazy-loaded, thread-safe)."""
    global _MODEL
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


# ── Core embedding helpers ────────────────────────────────────────────────────

def embed(texts: List[str]) -> np.ndarray:
    """
    Embed a list of strings.
    Returns L2-normalized vectors of shape (N, D).
    Empty / whitespace strings are replaced with a neutral placeholder.
    """
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)

    safe = [t.strip() if t.strip() else "[empty]" for t in texts]
    vecs = get_model().encode(
        safe,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=64,
    )
    return vecs


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D normalized vectors."""
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def max_cosine_sim(query_vec: np.ndarray, corpus_vecs: np.ndarray) -> float:
    """Maximum cosine similarity of a single query against all corpus vectors."""
    if corpus_vecs.shape[0] == 0:
        return 0.0
    sims = _sk_cosine(query_vec.reshape(1, -1), corpus_vecs)[0]
    return float(sims.max())


def pairwise_sim_matrix(vecs_a: np.ndarray, vecs_b: np.ndarray) -> np.ndarray:
    """
    Full cosine similarity matrix of shape (len_a, len_b).
    Handles empty inputs gracefully.
    """
    if vecs_a.shape[0] == 0 or vecs_b.shape[0] == 0:
        return np.zeros((vecs_a.shape[0], vecs_b.shape[0]), dtype=np.float32)
    return _sk_cosine(vecs_a, vecs_b)


def text_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two raw text strings.
    Returns float in [0, 1].
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vecs = embed([text_a, text_b])
    return max(cosine_sim(vecs[0], vecs[1]), 0.0)


def mean_pool_similarity(texts: List[str], reference: str) -> float:
    """
    Mean-pool all `texts` embeddings and compute similarity against `reference`.
    Useful for comparing a section (multiple sentences) to the JD.
    """
    if not texts or not reference.strip():
        return 0.0
    all_texts  = texts + [reference]
    vecs       = embed(all_texts)
    section_vec = vecs[:-1].mean(axis=0)
    section_vec /= np.linalg.norm(section_vec) + 1e-8
    ref_vec     = vecs[-1]
    return max(cosine_sim(section_vec, ref_vec), 0.0)