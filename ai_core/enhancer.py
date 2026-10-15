"""Optional topic enhancer helpers.

This module provides small, safe utilities to expand a topic into related
keywords or paraphrase sentences. It prefers lightweight, optional
dependencies and falls back to simple heuristics when they are not present so
we don't require heavy models during install or tests.

Functions:
 - expand_topic(topic) -> List[str]: return a short list of related keywords
 - paraphrase(text) -> List[str]: return a list of paraphrases (may return [] or [text])
 - phoneticize(text, lang) -> str: rough pronunciation guide
 - difficulty_of(text) -> str: 'easy' / 'medium' / 'hard'

The implementation tries to use NLTK WordNet if available. If not, it uses
basic heuristics (pluralization and simple morphological variants).
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

try:
    from nltk.corpus import wordnet as wn

    _NLTK_AVAILABLE = True
except Exception:
    wn = None
    _NLTK_AVAILABLE = False


def expand_topic(topic: str, max_results: int = 5) -> list[str]:
    """Return a small list of related keywords for the given topic.

    This function is intentionally conservative: it never raises and always
    returns a short list (possibly empty) so callers can use it without
    crashing.
    """
    if not topic:
        return []
    t = topic.strip()
    results = []

    # Try WordNet synonyms when available (best-effort)
    if _NLTK_AVAILABLE:
        try:
            synsets = wn.synsets(t)
            for s in synsets:
                for lemma_obj in s.lemmas():
                    name = lemma_obj.name().replace("_", " ")
                    if name.lower() != t.lower() and name not in results:
                        results.append(name)
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break
            # also include hypernyms / hyponyms (one level)
            if len(results) < max_results:
                for s in synsets:
                    for h in s.hyponyms()[:3]:
                        for lemma_obj in h.lemmas():
                            name = lemma_obj.name().replace("_", " ")
                            if name.lower() != t.lower() and name not in results:
                                results.append(name)
                            if len(results) >= max_results:
                                break
                        if len(results) >= max_results:
                            break
                    if len(results) >= max_results:
                        break
        except Exception as e:
            logger.debug("WordNet expand failed: %s", e)

    # Without WordNet there is no reliable source of related words; returning
    # nothing beats inventing phrases like "common lego".
    return results[:max_results]


def paraphrase(text: str, max_results: int = 3) -> list[str]:
    """Return a list of paraphrases for the given text.

    Currently this is a no-op fallback that returns an empty list. If you
    install heavier dependencies (e.g., HuggingFace transformers), you can
    implement paraphrasing here and return variants.
    """
    out = []

    # Prefer lightweight word substitution via WordNet when available.
    if _NLTK_AVAILABLE:
        try:
            # Find candidate content words (simple heuristic: alphanumeric words
            # longer than 3 chars). We'll attempt to substitute the first few
            # candidate words with a WordNet synonym to produce paraphrases.
            words = re.findall(r"\w+", text)
            candidates = [w for w in words if len(w) > 3]
            seen = set()
            for w in candidates:
                syns = wn.synsets(w)
                for s in syns:
                    for lemma_obj in s.lemmas():
                        lemma = lemma_obj.name().replace("_", " ")
                        if lemma.lower() != w.lower() and lemma not in seen:
                            # build a simple substitution (first occurrence)
                            pattern = re.compile(re.escape(w), re.IGNORECASE)
                            parap = pattern.sub(lemma, text, count=1)
                            if parap and parap.strip() and parap != text:
                                out.append(parap)
                                seen.add(lemma)
                                if len(out) >= max_results:
                                    break
                    if len(out) >= max_results:
                        break
                if len(out) >= max_results:
                    break
            return out
        except Exception as e:
            logger.debug("WordNet paraphrase failed: %s", e)

    # Fallback: small, safe variants by expanding contractions or trimming punctuation
    try:
        if "I'm" in text:
            out.append(text.replace("I'm", "I am"))
        if "Let's" in text:
            out.append(text.replace("Let's", "Let us"))
    except Exception:
        pass

    # Deduplicate and trim to requested count
    final = []
    for p in out:
        if p not in final:
            final.append(p)
        if len(final) >= max_results:
            break
    return final


def phoneticize(text: str, lang: str = "es") -> str:
    """Return a rough phonetic/reading guide for a sentence.

    This is intentionally lightweight: for Spanish we apply simple letter-to
    sound rules to help English speakers approximate pronunciation. For
    English we apply a naive approximation by marking some digraphs. This is
    a helper for learning and not a replacement for a proper phonetic
    transcription.
    """
    if not text:
        return ""
    s = text
    try:
        if lang and lang.startswith("es"):
            s = s.lower()
            # Rules that depend on diacritics must run before they are stripped.
            s = s.replace("ñ", "ny")
            s = s.replace("güe", "gwe").replace("güi", "gwi")
            s = unicodedata.normalize("NFD", s)
            s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
            # Protect "ch" so dropping the silent h doesn't break it.
            s = s.replace("ch", "\0")
            s = s.replace("h", "")
            s = s.replace("ll", "y")
            s = s.replace("qu", "k")
            # Spanish j, and g before e/i, sound like an English h. The u in
            # gue/gui only keeps the g hard, so drop it afterwards.
            s = re.sub(r"g(?=[ei])", "h", s)
            s = s.replace("gue", "ge").replace("gui", "gi")
            s = s.replace("j", "h")
            # c before e/i -> s, otherwise k
            s = re.sub(r"c(?=[ei])", "s", s)
            s = s.replace("c", "k")
            s = s.replace("z", "s")
            s = s.replace("v", "b")
            s = s.replace("\0", "ch")
            # remove punctuation and digits
            s = re.sub(r"[^a-z\s]", " ", s)
            # insert simple spacing between phonetic chunks (vowels and consonants)
            s = re.sub(r"([aeiou])", r"\1 ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s
        else:
            # naive english hint: normalize accents, separate common digraphs
            s = unicodedata.normalize("NFD", s)
            s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
            s = s.lower()
            s = s.replace("ough", "off")
            s = s.replace("ph", "f")
            s = s.replace("sh", "sh")
            s = s.replace("ch", "ch")
            s = re.sub(r"[^a-z\s]", " ", s)
            s = re.sub(r"([aeiou])", r"\1 ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s
    except Exception:
        return text


def difficulty_of(text: str) -> str:
    """Simple heuristic to bucket text difficulty into easy/medium/hard.

    Based on word count and average token length; intentionally conservative.
    """
    if not text:
        return "easy"
    words = re.findall(r"\w+", text)
    wc = len(words)
    avg_len = sum(len(w) for w in words) / wc if wc else 0
    if wc <= 4 and avg_len <= 5:
        return "easy"
    if wc <= 8 and avg_len <= 6:
        return "medium"
    return "hard"
