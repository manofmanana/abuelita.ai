"""Bilingual (EN/ES) micro-lesson generator.

``generate_lesson(topic, as_struct=True)`` returns a dict the Learn page
renders (and the AJAX endpoint returns as JSON):

* ``phrases`` / ``examples``: lists of ``{en, es, difficulty, phonetic_en,
  phonetic_es[, paraphrases_en]}``
* ``levels``: the phrases grouped easy -> medium -> hard, with labels
* ``quiz``: two questions with prompts, choices and answers in both languages
* ``labels``: UI strings in both languages

``generate_lesson(topic)`` (``as_struct=False``) returns the same lesson as
plain text. Everything works offline with deterministic fallbacks; only the
translations need the network.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

from .enhancer import difficulty_of, expand_topic, paraphrase, phoneticize
from .translator import TranslationError, translate, translate_to_spanish

try:
    import inflect
except Exception:  # pragma: no cover - optional dependency
    inflect = None

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency
    spacy = None

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data"
MAX_TOPIC_CHARS = 80
SENSITIVE_TOPICS = {"sex", "porn", "rape"}
# Common mass nouns: "I like music", not "I like musics".
UNCOUNTABLE = {
    "advice", "art", "bread", "coffee", "family", "food", "fun", "furniture", "health", "help",
    "homework", "information", "love", "luggage", "meat", "milk", "money", "music", "news", "rice",
    "salt", "sugar", "tea", "traffic", "travel", "water", "weather", "work",
}  # fmt: skip
DIFFICULTIES = ("easy", "medium", "hard")

LABELS = {
    "topicLabel_en": "Topic",
    "topicLabel_es": "Tema",
    "tipText_en": "Tip: Click any phrase or example to view English and Spanish side-by-side.",
    "tipText_es": "Haz clic en cualquier frase o ejemplo para ver Inglés y Español lado a lado.",
    "lesson_progression_en": "Lesson progression",
    "lesson_progression_es": "Progresión de la lección",
    "showAnswer_en": "Show Answer",
    "showAnswer_es": "Mostrar respuesta",
    "phrases_en": "Phrases",
    "phrases_es": "Frases",
    "examples_en": "Examples",
    "examples_es": "Ejemplos",
    "paraphrases_en": "Paraphrases",
    "paraphrases_es": "Paráfrasis",
    "pronunciation_en": "Pronunciation",
    "pronunciation_es": "Pronunciación",
    "default_difficulty": "easy",
    "difficulty_en": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
    "difficulty_es": {"easy": "Fácil", "medium": "Medio", "hard": "Difícil"},
}


# ---------------------------------------------------------------------------
# Topic analysis
# ---------------------------------------------------------------------------


def _canonical_topic(topic: str | None) -> str:
    t = re.sub(r"\s+", " ", (topic or "").strip())[:MAX_TOPIC_CHARS].strip()
    return t or "this topic"


def _is_sensitive(topic: str) -> bool:
    return any(word in SENSITIVE_TOPICS for word in re.findall(r"[a-z]+", topic.lower()))


@lru_cache(maxsize=1)
def _inflect_engine():
    if inflect is None:
        return None
    try:
        return inflect.engine()
    except Exception:  # pragma: no cover
        return None


@lru_cache(maxsize=1)
def _spacy_nlp():
    if spacy is None:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _normalize_topic(topic: str) -> dict:
    """Return grammatical forms of the topic used to build sentences.

    Keys: display, safe, singular, plural, is_plural, is_countable.
    ``safe`` is a neutral stand-in ("this topic") for sensitive or
    non-alphanumeric topics.
    """
    t = _canonical_topic(topic)
    if _is_sensitive(t) or not any(c.isalnum() for c in t):
        safe = "this topic"
    else:
        safe = t

    singular, plural, is_plural, is_countable = t, t, False, True
    if " " not in t:
        engine = _inflect_engine()
        if engine:
            try:
                s = engine.singular_noun(t)
                if s:
                    singular, plural, is_plural = s, t, True
                else:
                    plural = engine.plural_noun(t) or t
                is_countable = plural != singular
            except Exception:
                plural = t + "s"
        elif t.endswith("s"):
            singular, is_plural = t.rstrip("s") or t, True
        else:
            plural = t + "s"
    if t.lower() in UNCOUNTABLE:
        singular, plural, is_plural, is_countable = t, t, False, False

    return {
        "display": safe,
        "safe": safe,
        "singular": singular,
        "plural": plural,
        "is_plural": is_plural,
        "is_countable": is_countable,
    }


def _sanitize_plural(singular: str, plural: str) -> str:
    """Prefer inflect's plural, and avoid awkward forms like 'legoes'."""
    engine = _inflect_engine()
    if engine:
        try:
            plural = engine.plural_noun(singular) or plural
        except Exception:
            pass
    if singular.lower().endswith("o") and plural.lower().endswith("oes"):
        return plural[:-3] + "os"
    if singular.lower() == "child" and plural.lower() in {"childs", "childes"}:
        return "children"
    return plural


def _analyze_topic_pos(topic: str) -> str:
    """Guess whether the topic is a 'noun', 'verb' or 'adj'."""
    nlp = _spacy_nlp()
    if nlp is not None:
        try:
            for tok in nlp(topic):
                if tok.is_alpha:
                    pos = tok.pos_.lower()
                    if pos.startswith("v"):
                        return "verb"
                    if pos.startswith("adj"):
                        return "adj"
                    return "noun"
        except Exception:
            pass
    lower = topic.lower()
    if lower.endswith("ly"):
        return "adj"
    if lower.endswith("ing") or lower in {"run", "play", "eat", "sing", "dance", "cook", "swim", "read", "write"}:
        return "verb"
    return "noun"


# ---------------------------------------------------------------------------
# Sentence building
# ---------------------------------------------------------------------------


def _make_canned_phrases(topic: str) -> list[str]:
    info = _normalize_topic(topic)
    pos = _analyze_topic_pos(topic)
    safe, singular, plural = info["safe"], info["singular"], info["plural"]

    phrases = [
        f"Hello! Let's talk about {safe}.",
        f"How do you say '{safe}' in everyday speech?",
    ]
    if safe == "this topic":
        pass
    elif pos == "verb":
        phrases += [f"How do you {singular} in simple sentences?", f"I often {singular} when I am happy."]
    elif pos == "adj":
        phrases += [f"How would you describe something that is {singular}?", f"This is very {singular}."]
    elif info["is_countable"]:
        clean_plural = _sanitize_plural(singular, plural)
        phrases += [f"I like {clean_plural}.", f"Where can I find {clean_plural}?"]
    else:
        phrases += [f"I enjoy learning about {safe}.", f"Where can I learn more about {safe}?"]
    phrases.append(f"Can you describe {safe} in simple words?")
    return phrases


def _make_examples(topic: str) -> list[str]:
    """Three examples, ordered easy -> hard."""
    info = _normalize_topic(topic)
    pos = _analyze_topic_pos(topic)
    safe, singular = info["safe"], info["singular"]

    if safe == "this topic":
        return [
            f"People often talk about {safe} at family gatherings.",
            f"I recently read a short story about {safe}.",
            f"Can you explain {safe} to me in simple words?",
        ]
    if pos == "verb":
        return [
            f"I {singular} every day.",
            f"Yesterday I wanted to {singular} with my friend.",
            f"How would you {singular} if you had more time?",
        ]
    if pos == "adj":
        return [
            f"This is very {singular}.",
            f"She seems {singular} today.",
            f"It was a {singular} moment that I won't forget.",
        ]
    if info["is_countable"]:
        clean_plural = _sanitize_plural(singular, info["plural"])
        return [
            f"When I visit the market I see many {clean_plural}.",
            f"My friend showed me a {singular} yesterday.",
            f"Children often play with {clean_plural} in the afternoon.",
        ]
    return [
        f"When I visit the market I learn about {safe}.",
        f"People often talk about {safe} at family gatherings.",
        f"I recently read a short story about {safe}.",
    ]


def _topic_file_sentences(topic: str) -> list[str]:
    """Sentences from ``data/<topic>.txt`` if a vocabulary file exists.

    File format: first line is comma-separated keywords, the rest are example
    sentences. Only plain lowercase words are looked up, so user input can
    never escape the data directory.
    """
    key = topic.lower().split()[0] if topic.split() else ""
    if not re.fullmatch(r"[a-z]{2,30}", key):
        return []
    for candidate in (key, key + "s", key.rstrip("s")):
        path = DATA_PATH / f"{candidate}.txt"
        if path.is_file():
            break
    else:
        return []
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        logger.warning("Failed to read topic file %s: %s", path, exc)
        return []
    if not lines:
        return []
    keywords = [k.strip() for k in lines[0].split(",") if k.strip()]
    sentences = [f"{k.capitalize()} is a common word related to {topic}." for k in keywords[:5]]
    for line in lines[1:]:
        sentences.extend(s for s in re.split(r"(?<=[.!?])\s+", line) if s)
    return sentences[:10]


def _dedupe(items) -> list[str]:
    return list(dict.fromkeys(i for i in items if i))


def _translate_all(texts: list[str]) -> dict[str, str]:
    """Translate each distinct string once.

    All lines go out in a single request (Google preserves line breaks). If
    the response doesn't line up, fall back to one request per string, in
    parallel.
    """
    try:
        lines = translate("\n".join(texts), source="en", target="es").split("\n")
        if len(lines) == len(texts) and all(line.strip() for line in lines):
            return {src: line.strip() for src, line in zip(texts, lines, strict=True)}
    except TranslationError:
        pass
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(texts, pool.map(translate_to_spanish, texts), strict=True))


def _pair(en: str, translations: dict[str, str], with_paraphrases: bool = False) -> dict:
    es = translations.get(en) or translate_to_spanish(en)
    item = {
        "en": en,
        "es": es,
        "difficulty": difficulty_of(en),
        "phonetic_en": phoneticize(en, "en"),
        "phonetic_es": phoneticize(es, "es"),
    }
    if with_paraphrases:
        paras = paraphrase(en, 2)
        if paras:
            item["paraphrases_en"] = paras
    return item


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_lesson(topic: str, as_struct: bool = False):
    """Generate a bilingual lesson about ``topic``.

    Returns a dict when ``as_struct`` is true, otherwise plain text.
    """
    topic = _canonical_topic(topic)
    try:
        lesson = _build_lesson(topic)
    except Exception:
        logger.exception("Failed to build lesson for %r", topic)
        lesson = _fallback_lesson(topic)
    return lesson if as_struct else lesson_to_text(lesson)


def _build_lesson(topic: str) -> dict:
    info = _normalize_topic(topic)
    subject = info["safe"]

    sentences = [] if subject == "this topic" else _topic_file_sentences(topic)
    if not sentences:
        sentences = _make_canned_phrases(topic)
    if subject != "this topic":
        sentences += [f"You might also hear the word '{r}' related to {subject}." for r in expand_topic(subject)[:2]]
    if not any(subject.lower() in s.lower() for s in sentences):
        sentences.insert(0, f"Let's learn about {subject} today.")
    sentences = _dedupe(sentences)
    examples = _dedupe(_make_examples(topic))

    if subject == "this topic":
        quiz_form = subject
    elif info["is_countable"]:
        quiz_form = _sanitize_plural(info["singular"], info["plural"])
    else:
        quiz_form = info["singular"]
    choices_en = [
        f"I like {quiz_form}.",
        f"Where can I find {quiz_form}?",
        f"Can you describe {quiz_form} in simple words?",
    ]

    translations = _translate_all(_dedupe([*sentences, *examples, *choices_en, subject]))
    phrases = [_pair(s, translations, with_paraphrases=True) for s in sentences]
    example_pairs = [_pair(e, translations) for e in examples]
    choices_es = [translations[c] for c in choices_en]
    topic_es = translations[subject]

    quiz = [
        {
            # Translate-this question: each page asks for the other language.
            "q_en": f'Translate to Spanish: "{choices_en[0]}"',
            "q_es": f"Traduce al inglés: «{choices_es[0]}»",
            "answer_text_en": choices_en[0],
            "answer_text_es": choices_es[0],
        },
        {
            # Multiple choice: English speakers pick among the Spanish choices,
            # Spanish speakers among the English ones.
            "q_en": f"Which sentence asks where to find {quiz_form}?",
            "q_es": f"¿Qué oración pregunta dónde encontrar {topic_es}?",
            "choices_en": choices_en,
            "choices_es": choices_es,
            "answer": 1,
            "answer_text_en": choices_en[1],
            "answer_text_es": choices_es[1],
        },
    ]

    return _assemble(subject, topic_es, phrases, example_pairs, quiz)


def _assemble(topic_en: str, topic_es: str, phrases: list[dict], examples: list[dict], quiz: list[dict]) -> dict:
    def by_difficulty(items):
        return {d: [i for i in items if i.get("difficulty") == d] for d in DIFFICULTIES}

    phrases_by_difficulty = by_difficulty(phrases)
    return {
        "topic_en": topic_en,
        "topic_es": topic_es,
        "phrases": phrases,
        "examples": examples,
        "quiz": quiz,
        "mini_quiz_en": "Mini-quiz",
        "mini_quiz_es": "Mini-prueba",
        "phrases_by_difficulty": phrases_by_difficulty,
        "examples_by_difficulty": by_difficulty(examples),
        "levels": [
            {
                "key": d,
                "label_en": LABELS["difficulty_en"][d],
                "label_es": LABELS["difficulty_es"][d],
                "phrases": phrases_by_difficulty[d],
            }
            for d in DIFFICULTIES
        ],
        # Open on the easiest level that actually has phrases.
        "labels": {**LABELS, "default_difficulty": next((d for d in DIFFICULTIES if phrases_by_difficulty[d]), "easy")},
    }


def _fallback_lesson(topic: str) -> dict:
    """Minimal lesson with the same shape, used if generation fails."""
    subject = _normalize_topic(topic)["safe"]
    line = f"Let's learn about {subject} today."
    item = {"en": line, "es": f"[es] {line}", "difficulty": "medium", "phonetic_en": "", "phonetic_es": ""}
    return _assemble(subject, subject, [item], [], [])


def lesson_to_text(lesson: dict) -> str:
    """Render a lesson struct as plain text (copy/paste friendly)."""
    lines = [f"Lesson: {lesson['topic_en']}", "", "Phrases:"]
    for p in lesson["phrases"]:
        lines += [f"- EN: {p['en']}", f"  ES: {p['es']}"]
    if lesson["examples"]:
        lines += ["", "Examples:"]
        for e in lesson["examples"]:
            lines += [f"- EN: {e['en']}", f"  ES: {e['es']}"]
    if lesson["quiz"]:
        lines += ["", "Mini-quiz:"]
        for n, q in enumerate(lesson["quiz"], 1):
            lines.append(f"{n}) {q['q_en']}")
            for letter, choice in zip("ABC", q.get("choices_en", []), strict=False):
                lines.append(f"   {letter}) {choice}")
            lines.append(f"   Answer: {q['answer_text_es']}")
    return "\n".join(lines)
