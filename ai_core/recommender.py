"""Lightweight recommender using gensim similarities or keyword overlap."""
import logging
import os

logger = logging.getLogger(__name__)

try:
    import gensim
    from gensim import corpora, models, similarities
except Exception:
    gensim = None

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


def recommend_similar(text: str, corpus_texts=None, topn=3):
    """Return a list of similar texts from corpus_texts.

    If gensim is unavailable, use naive substring matching.
    """
    corpus_texts = corpus_texts or []
    if gensim is None or not corpus_texts:
        # Naive fallback: return corpus_texts that contain any keyword
        keywords = set(text.lower().split())
        scored = []
        for t in corpus_texts:
            score = len(keywords & set(t.lower().split()))
            if score:
                scored.append((score, t))
        scored.sort(reverse=True)
        return [t for _, t in scored[:topn]]

    # Build gensim index
    try:
        tokenized = [[w for w in doc.lower().split()] for doc in corpus_texts]
        dictionary = corpora.Dictionary(tokenized)
        corpus = [dictionary.doc2bow(text) for text in tokenized]
        tfidf = models.TfidfModel(corpus)
        index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=len(dictionary))
        vec = dictionary.doc2bow(text.lower().split())
        sims = index[tfidf[vec]]
        sims_idx = sorted(list(enumerate(sims)), key=lambda x: -x[1])[:topn]
        return [corpus_texts[i] for i, _ in sims_idx]
    except Exception as e:
        logger.warning("recommend_similar failed: %s", e)
        return []
