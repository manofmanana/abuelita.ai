"""Optional topic enhancer helpers.

This module provides small, safe utilities to expand a topic into related
keywords or paraphrase sentences. It prefers lightweight, optional
dependencies and falls back to simple heuristics when they are not present so
we don't require heavy models during install or tests.

Functions:
 - expand_topic(topic) -> List[str]: return a short list of related keywords
 - paraphrase(text) -> List[str]: return a list of paraphrases (may return [] or [text])

The implementation tries to use NLTK WordNet if available. If not, it uses
basic heuristics (pluralization and simple morphological variants).
"""
from typing import List
import logging
import re

logger = logging.getLogger(__name__)

try:
    import nltk
    from nltk.corpus import wordnet as wn
    _NLTK_AVAILABLE = True
except Exception:
    wn = None
    _NLTK_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, util
    _ST_AVAILABLE = True
    # Defer model instantiation until used to avoid startup cost
    _st_model = None
except Exception:
    _ST_AVAILABLE = False
    _st_model = None


def expand_topic(topic: str, max_results: int = 5) -> List[str]:
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
                for l in s.lemmas():
                    name = l.name().replace('_', ' ')
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
                        for l in h.lemmas():
                            name = l.name().replace('_', ' ')
                            if name.lower() != t.lower() and name not in results:
                                results.append(name)
                            if len(results) >= max_results:
                                break
                        if len(results) >= max_results:
                            break
                    if len(results) >= max_results:
                        break
        except Exception as e:
            logger.debug('WordNet expand failed: %s', e)

    # Heuristic fallbacks: add plural/singular forms and a few templated relatives
    if not results:
        try:
            if t.endswith('s'):
                base = t.rstrip('s') or t
                results.append(base)
            else:
                results.append(t + 's')
            # Add some templated relatives
            results.append('common ' + t)
            results.append('simple ' + t)
        except Exception:
            pass

    # Trim to max_results and return
    return results[:max_results]


def paraphrase(text: str, max_results: int = 3) -> List[str]:
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
                    for l in s.lemmas():
                        lemma = l.name().replace('_', ' ')
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
            logger.debug('WordNet paraphrase failed: %s', e)

    # Fallback: small, safe variants by expanding contractions or trimming punctuation
    try:
        if "I'm" in text:
            out.append(text.replace("I'm", "I am"))
        if text.endswith('.'):
            out.append(text[:-1])
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


def make_cloze(text: str, topic: str = None, max_results: int = 2) -> List[str]:
    """Generate simple cloze (fill-in-the-blank) variants for a sentence.

    If `topic` appears in the text, blank the topic; otherwise blank a long
    content word. Returns plain English cloze strings with a '____' placeholder.
    """
    if not text:
        return []
    out = []
    try:
        if topic and topic.strip().lower() in text.lower():
            # replace occurrences of the topic (case-insensitive) with blanks
            pat = re.compile(re.escape(topic), re.IGNORECASE)
            cl = pat.sub('____', text)
            out.append(cl)
        else:
            words = re.findall(r"\w+", text)
            # pick the longest significant word
            candidates = [w for w in words if len(w) > 3]
            if candidates:
                longest = max(candidates, key=len)
                pat = re.compile(re.escape(longest), re.IGNORECASE)
                cl = pat.sub('____', text, count=1)
                out.append(cl)
        # if still need variants, also add a punctuation-trimmed variant
        if len(out) < max_results and text.endswith('.'):
            out.append(text[:-1].replace('.', '') + ' ____')
    except Exception as e:
        logger.debug('make_cloze failed: %s', e)
    return out[:max_results]


def make_exercise(text: str, topic: str = None):
    """Return a single exercise dict for a sentence.

    The exercise blanks a single random content word and returns a dict with
    keys: 'cloze' (display string with '____') and 'answer' (the missing word).
    """
    if not text:
        return None
    try:
        words = re.findall(r"\w+", text)
        # Prefer longer content words (>3 chars) for meaningful exercises
        candidates = [w for w in words if len(w) > 3]
        if not candidates:
            candidates = words
        if not candidates:
            return None
        # pick a random candidate deterministically-ish (use first for tests)
        answer = candidates[0]
        # if topic appears and is a candidate prefer it
        if topic and topic.strip().lower() in text.lower():
            # find first matching word equal to topic
            for w in candidates:
                if w.lower() == topic.strip().lower():
                    answer = w
                    break
        pat = re.compile(re.escape(answer), re.IGNORECASE)
        cloze = pat.sub('____', text, count=1)
        return {"cloze": cloze, "answer": answer}
    except Exception as e:
        logger.debug('make_exercise failed: %s', e)
        return None


def phoneticize(text: str, lang: str = 'es') -> str:
    """Return a rough phonetic/reading guide for a sentence.

    This is intentionally lightweight: for Spanish we apply simple letter-to
    sound rules to help English speakers approximate pronunciation. For
    English we apply a naive approximation by marking some digraphs. This is
    a helper for learning and not a replacement for a proper phonetic
    transcription.
    """
    if not text:
        return ''
    s = text
    try:
        if lang and lang.startswith('es'):
            # lowercase and apply simple Spanish pronunciation rules
            s = s.lower()
            s = s.replace('ll', 'y')
            s = s.replace('ch', 'ch')
            s = s.replace('qu', 'k')
            s = s.replace('gue', 'ge').replace('gui', 'gi')
            s = s.replace('güe', 'gwe').replace('güi', 'gwi')
            s = s.replace('j', 'h')
            s = s.replace('h', '')
            s = s.replace('ñ', 'ny')
            s = s.replace('c', 'k')
            # c before e/i should sound like 's' for Latin American
            s = re.sub(r'k(?=[ei])', 's', s)
            s = s.replace('z', 's')
            s = s.replace('v', 'b')
            # simple vowel emphasis spacing
            s = re.sub(r'([aeiou])', r'\1 ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        else:
            # naive english hint: separate common digraphs and add spacing
            s = s.lower()
            s = s.replace('th', 'th')
            s = s.replace('ough', 'off')
            s = s.replace('ph', 'f')
            s = s.replace('sh', 'sh')
            s = s.replace('ch', 'ch')
            s = re.sub(r'([aeiou])', r'\1 ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s
    except Exception:
        return text


def difficulty_of(text: str) -> str:
    """Simple heuristic to bucket text difficulty into easy/medium/hard.

    Based on word count and average token length; intentionally conservative.
    """
    if not text:
        return 'easy'
    words = re.findall(r"\w+", text)
    wc = len(words)
    avg_len = sum(len(w) for w in words) / wc if wc else 0
    if wc <= 4 and avg_len <= 5:
        return 'easy'
    if wc <= 8 and avg_len <= 6:
        return 'medium'
    return 'hard'
