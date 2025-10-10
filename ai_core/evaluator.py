"""Local evaluator for quiz answers using TF-IDF cosine similarity."""
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - optional dependency
    TfidfVectorizer = None
    cosine_similarity = None


def grade_answer(reference: str, user_input: str) -> float:
    """Return a similarity score between 0 and 1 (rounded to 2 decimals).

    Falls back to a simple token overlap if sklearn isn't available.
    """
    if TfidfVectorizer is None:
        # Naive fallback: token overlap ratio
        ref_tokens = set(reference.lower().split())
        usr_tokens = set(user_input.lower().split())
        if not ref_tokens:
            return 0.0
        overlap = len(ref_tokens & usr_tokens) / len(ref_tokens)
        return round(overlap, 2)
    try:
        vect = TfidfVectorizer().fit([reference, user_input])
        tfidf = vect.transform([reference, user_input])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(score), 2)
    except Exception as e:
        logger.warning("grade_answer failed: %s", e)
        return 0.0
