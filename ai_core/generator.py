"""Lesson generator that produces bilingual (EN/ES) learning material.

The generator prefers to use a Markov model when available for more varied
phrases; however it always provides a deterministic, helpful fallback so the
application remains useful even when optional dependencies are missing.

Output is a multi-paragraph string containing:
 - A short introduction
 - A set of useful phrases in English with Spanish translations
 - Short example sentences
 - A 2-question mini-quiz (translate / choose)
"""
from typing import List
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

_model = None

try:
    import markovify
except Exception:
    markovify = None

try:
    import inflect
except Exception:
    inflect = None

try:
    import spacy
except Exception:
    spacy = None

from .translator import translate_to_spanish
from .enhancer import expand_topic, paraphrase, difficulty_of, phoneticize

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


def _load_model():
    global _model
    if _model is not None:
        return _model
    if markovify is None:
        return None
    try:
        txt_file = os.path.join(DATA_PATH, "english_lessons.txt")
        if not os.path.exists(txt_file):
            return None
        with open(txt_file, encoding="utf-8") as f:
            text = f.read()
        _model = markovify.Text(text)
        return _model
    except Exception as e:
        logger.warning("Could not load markov model: %s", e)
        return None


def _canonical_topic(topic: str) -> str:
    t = (topic or "this topic").strip()
    return t if t else "this topic"


SENSITIVE_TOPICS = {"sex", "porn", "rape"}


def _normalize_topic(topic: str) -> dict:
    """Return normalized forms for the topic to help build grammatically
    correct sentences.

    Returns a dict with keys: display, safe, singular, plural, is_plural,
    is_countable.
    """
    t = _canonical_topic(topic)
    display = t
    # derive simple safe form: if topic is sensitive or non-alphanumeric, fall
    # back to neutral phrasing
    if any(word in t.lower() for word in SENSITIVE_TOPICS) or not any(c.isalnum() for c in t):
        safe = "this topic"
    else:
        safe = t

    p_engine = None
    if inflect:
        try:
            p_engine = inflect.engine()
        except Exception:
            p_engine = None

    singular = t
    plural = t
    is_plural = False
    is_countable = True

    # If it's multiple words, don't try aggressive pluralization
    if " " in t:
        singular = t
        plural = t
        is_plural = False
        is_countable = True
    else:
        if p_engine:
            try:
                # inflect.singular_noun returns False if word is singular
                s = p_engine.singular_noun(t)
                if s:
                    singular = s
                    plural = t
                    is_plural = True
                else:
                    singular = t
                    plural = p_engine.plural_noun(t) or t
                    is_plural = False
                # crude heuristic for countability: if plural differs, treat as countable
                is_countable = plural != singular
            except Exception:
                singular = t
                plural = t + "s"
                is_plural = False
                is_countable = True
        else:
            # simple heuristics
            if t.endswith('s'):
                singular = t.rstrip('s') or t
                plural = t
                is_plural = True
            else:
                singular = t
                plural = t + 's'
                is_plural = False
            is_countable = True

    return {
        "display": display,
        "safe": safe,
        "singular": singular,
        "plural": plural,
        "is_plural": is_plural,
        "is_countable": is_countable,
        "is_spanish": False,
        "pos": "noun",
    }


def _sanitize_plural(singular: str, plural: str) -> str:
    """Conservative plural cleanup: avoid awkward 'legoes' style forms.

    If plural looks like it was formed by naive 'es' on an 'o' ending,
    convert 'oes' -> 'os' (e.g. 'legoes' -> 'legos'). This is a small,
    conservative heuristic to improve readability.
    """
    # If inflect is available, prefer its pluralization for irregulars
    try:
        if inflect:
            p_engine = inflect.engine()
            auto = p_engine.plural_noun(singular) or plural
            if auto:
                # If inflect suggests a form like 'legoes' for 'lego',
                # normalize to 'legos' for readability.
                if singular and singular.lower().endswith('o') and auto.lower().endswith('oes'):
                    return auto[:-3] + 'os'
                return auto
    except Exception:
        pass
    # Fallback conservative rule: convert 'legoes'->'legos' style errors
    if singular and singular.lower().endswith('o') and plural.lower().endswith('oes'):
        return plural[:-3] + 'os'
    # handle child->children naive cases if someone passed them in
    if singular.lower() == 'child' and plural.lower() in {'childs', 'childes'}:
        return 'children'
    return plural


def _analyze_topic_pos(topic: str) -> str:
    """Return a guessed POS tag for the topic: 'noun', 'verb', or 'adj'.

    Uses spaCy when available; otherwise falls back to heuristics.
    """
    if not topic:
        return 'noun'
    if spacy:
        try:
            # load small English model lazily if available
            nlp = None
            try:
                nlp = spacy.load('en_core_web_sm')
            except Exception:
                # try blank English model
                nlp = spacy.blank('en')
            doc = nlp(topic)
            # pick POS of first token with alpha
            for tok in doc:
                if tok.is_alpha:
                    pos = tok.pos_.lower()
                    if pos.startswith('n'):
                        return 'noun'
                    if pos.startswith('v'):
                        return 'verb'
                    if pos.startswith('a') or pos.startswith('s'):
                        return 'adj'
            return 'noun'
        except Exception:
            pass
    # heuristics: words ending with -ly likely adjectives/adverbs, verbs are common small words
    lower = topic.lower()
    if lower.endswith('ly'):
        return 'adj'
    # common verb forms
    if lower.endswith('ing') or lower in {'run', 'play', 'eat', 'sing', 'dance'}:
        return 'verb'
    # default to noun
    return 'noun'


def _make_canned_phrases(topic: str) -> List[str]:
    info = _normalize_topic(topic)
    pos = _analyze_topic_pos(topic)
    safe = info['safe']
    singular = info['singular']
    plural = info['plural']
    is_countable = info['is_countable']

    phrases = [f"Hello! Let's talk about {info['display']}.",
               f"How do you say '{info['display']}' in everyday speech?"]

    if pos == 'verb':
        phrases.append(f"How do you {singular} in simple sentences?")
        phrases.append(f"I often {singular} when I am happy.")
    elif pos == 'adj':
        phrases.append(f"How would you describe something that is {singular}?")
        phrases.append(f"This is very {singular}.")
    else:
        # noun
        if is_countable:
            phrases.append(f"I like {plural}.")
            phrases.append(f"Where can I find {plural}?")
        else:
            phrases.append(f"I enjoy learning about {safe}.")
            phrases.append(f"Where can I learn more about {safe}?")

    phrases.append(f"Can you describe {safe} in simple words?")
    return phrases


def _make_examples(topic: str) -> List[str]:
    info = _normalize_topic(topic)
    pos = _analyze_topic_pos(topic)
    safe = info['safe']
    singular = info['singular']
    plural = info['plural']
    is_countable = info['is_countable']
    # Build a small, pedagogical set of examples ordered from Easy -> Medium -> Hard
    examples = []
    if pos == 'verb':
        # Easy: simple present/factual
        examples.append(f"I {singular} every day.")
        # Medium: past/simple conversation
        examples.append(f"Yesterday I {singular} with my friend.")
        # Hard: question/conditional
        examples.append(f"How would you {singular} if you had more time?")
    elif pos == 'adj':
        examples.append(f"This is very {singular}.")
        examples.append(f"She seems {singular} today.")
        examples.append(f"It was a {singular} moment that I won't forget.")
    else:
        # For nouns, pick clear examples using singular and plural forms
        clean_plural = _sanitize_plural(singular, plural)
        # Easy: simple observation using plural if countable
        if is_countable:
            examples.append(f"When I visit the market I see many {clean_plural}.")
            examples.append(f"My friend built a small model of {singular} yesterday.")
            examples.append(f"Children often play with {clean_plural} in the afternoon.")
        else:
            examples.append(f"When I visit the market I learn about {safe}.")
            examples.append(f"People often talk about {safe} at family gatherings.")
            examples.append(f"I recently read a short story about {safe}.")

    return examples


def _build_lesson_from_sentences(topic: str, sentences: List[str]) -> str:
    # Translate each sentence to Spanish using translator fallback
    lines = []
    lines.append(f"Lesson: {topic}\n")
    lines.append("Phrases:\n")
    for s in sentences:
        spanish = translate_to_spanish(s)
        lines.append(f"- EN: {s}")
        lines.append(f"  ES: {spanish}\n")

    lines.append("Examples:\n")
    examples = _make_examples(topic)
    for ex in examples:
        lines.append(f"- EN: {ex}")
        lines.append(f"  ES: {translate_to_spanish(ex)}\n")

    lines.append("Mini-quiz:\n")
    # Two simple, deterministic quiz items
    quiz_q1 = f"Translate to Spanish: 'I like {topic}.'"
    quiz_q2 = f"Which sentence asks where to find {topic}?\n  A) I like {topic}.\n  B) Where can I find {topic}?\n  C) Describe {topic}."
    lines.append(f"1) {quiz_q1}")
    lines.append(f"   Answer: {translate_to_spanish('I like ' + topic + '.')}\n")
    lines.append(f"2) {quiz_q2}")
    lines.append(f"   Answer: B) Where can I find {topic}? -> {translate_to_spanish('Where can I find ' + topic + '?')}")

    return "\n".join(lines)


def generate_lesson(topic: str, as_struct: bool = False):
    """Generate a helpful bilingual lesson about a topic.

    The returned string contains English phrases, Spanish translations,
    examples, and a mini-quiz. The function is defensive and will still
    produce useful content when optional libraries or data files are
    unavailable.
    """
    topic = _canonical_topic(topic)
    model = _load_model()

    # Prefer Markov-generated sentences if model available, otherwise use
    # canned, deterministic phrases that are informative. Also look for
    # topic-specific vocabulary files under DATA_PATH (e.g. 'toys.txt').
    sentences: List[str] = []
    # try topic-specific vocab
    topic_key = topic.lower().split()[0]
    topic_file = os.path.join(DATA_PATH, f"{topic_key}.txt")
    if os.path.exists(topic_file):
        try:
            with open(topic_file, encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            # first line: comma-separated keywords
            keywords = []
            if lines:
                keywords = [k.strip() for k in lines[0].split(',') if k.strip()]
            # rest: example sentences
            ex_sentences = lines[1:]
            # Build sentences from keywords and examples
            for k in keywords[:5]:
                sentences.append(f"{k.capitalize()} is a common word related to {topic}.")
            sentences.extend(ex_sentences[:5])
        except Exception as e:
            logger.warning("Failed to read topic file %s: %s", topic_file, e)
    if model:
        try:
            # Try to produce up to 5 distinct sentences
            for _ in range(6):
                s = model.make_sentence()
                if s:
                    sentences.append(s)
                if len(sentences) >= 5:
                    break
        except Exception as e:
            logger.warning("markov generation partial failure: %s", e)

    if not sentences:
        # Use canned phrases but personalize with the topic
        sentences = _make_canned_phrases(topic)

    # Try to expand topic with related keywords to make content richer
    try:
        related = expand_topic(topic)
        # Add a couple of related-keyword sentences to broaden exposure
        for r in related[:2]:
            sentences.append(f"You might also hear the word '{r}' related to {topic}.")
    except Exception:
        pass

    # Ensure we have a compact, helpful set
    # If the generated sentences don't mention the topic, add one that does.
    if not any(topic.lower() in s.lower() for s in sentences):
        sentences.insert(0, f"Let's learn about {topic} today.")

    # Deduplicate sentences while preserving order
    seen = set()
    deduped_sentences = []
    for s in sentences:
        if s and s not in seen:
            deduped_sentences.append(s)
            seen.add(s)
    sentences = deduped_sentences

    try:
        # Collect all unique texts we will translate so each distinct string is
        # translated exactly once. This eliminates redundant network calls and
        # speeds up generation substantially. Translate in parallel to reduce
        # wall-clock time when the translator is network-bound.
        examples_en = _make_examples(topic)
        # deduplicate examples (preserve order)
        seen_ex = set()
        deduped_examples = []
        for ex in examples_en:
            if ex and ex not in seen_ex:
                deduped_examples.append(ex)
                seen_ex.add(ex)
        examples_en = deduped_examples
        quiz_texts = [f"I like {topic}.", f"Where can I find {topic}?"]
        # sanitize plural for quiz display if necessary and pick phrasing
        norm = _normalize_topic(topic)
        clean_plural = _sanitize_plural(norm.get('singular', topic), norm.get('plural', topic))
        if norm.get('is_countable'):
            quiz_texts = [f"I like {clean_plural}.", f"Where can I find {clean_plural}?"]
        else:
            # use singular/topic phrasing for non-countable topics
            quiz_texts = [f"I like {norm.get('singular', topic)}.", f"Where can I find {norm.get('singular', topic)}?"]
        # preserve order and deduplicate so behavior is deterministic across runs
        texts_to_translate = []
        for t in sentences:
            if t and t not in texts_to_translate:
                texts_to_translate.append(t)
        for ex in examples_en:
            if ex and ex not in texts_to_translate:
                texts_to_translate.append(ex)
        for q in quiz_texts:
            if q and q not in texts_to_translate:
                texts_to_translate.append(q)
        if topic and topic not in texts_to_translate:
            texts_to_translate.append(topic)

        translations = {}
        # Use a single shared pool for translations/paraphrase/phoneticization to
        # avoid creating multiple ThreadPoolExecutors (which adds overhead).
        max_workers = min(8, (os.cpu_count() or 2) * 2)
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_to_text = {pool.submit(translate_to_spanish, t): t for t in texts_to_translate}
                for fut in as_completed(future_to_text):
                    t = future_to_text[fut]
                    try:
                        translations[t] = fut.result()
                    except Exception:
                        # Fall back to a direct call if a thread task failed
                        translations[t] = translate_to_spanish(t)
                # After translations complete, build the pairs so we can submit
                # paraphrase and phoneticization tasks into the same pool.
                lines = []
                lines.append(f"Lesson: {topic}\n")
                lines.append("Phrases:\n")
                for s in sentences:
                    spanish = translations.get(s, translate_to_spanish(s))
                    lines.append(f"- EN: {s}")
                    lines.append(f"  ES: {spanish}\n")

                lines.append("Examples:\n")
                for ex in examples_en:
                    lines.append(f"- EN: {ex}")
                    lines.append(f"  ES: {translations.get(ex, translate_to_spanish(ex))}\n")

                lines.append("Mini-quiz:\n")
                quiz_q1 = f"Translate to Spanish: 'I like {topic}.'"
                quiz_q2 = f"Which sentence asks where to find {topic}?\n  A) I like {topic}.\n  B) Where can I find {topic}?\n  C) Describe {topic}."
                lines.append(f"1) {quiz_q1}")
                lines.append(f"   Answer: {translations.get(quiz_texts[0], translate_to_spanish(quiz_texts[0]))}\n")
                lines.append(f"2) {quiz_q2}")
                lines.append(f"   Answer: B) Where can I find {topic}? -> {translations.get(quiz_texts[1], translate_to_spanish(quiz_texts[1]))}")

                lesson_text = "\n".join(lines)

                # Build paired lists so templates can iterate without special filters
                phrases_pairs = [{"en": s, "es": translations.get(s, translate_to_spanish(s)), "difficulty": difficulty_of(s)} for s in sentences]
                examples_pairs = [{"en": e, "es": translations.get(e, translate_to_spanish(e)), "difficulty": difficulty_of(e)} for e in examples_en]

                # Submit paraphrase and phoneticization tasks into the same pool
                para_futures = {pool.submit(paraphrase, p['en'], 2): idx for idx, p in enumerate(phrases_pairs)}
                phonetic_futures = {}
                for idx, p in enumerate(phrases_pairs):
                    f_es = pool.submit(phoneticize, p.get('es', ''), 'es')
                    phonetic_futures[f_es] = ("phrase", idx, 'phonetic_es')
                    f_en = pool.submit(phoneticize, p.get('en', ''), 'en')
                    phonetic_futures[f_en] = ("phrase", idx, 'phonetic_en')

                for idx, e in enumerate(examples_pairs):
                    f_es = pool.submit(phoneticize, e.get('es', ''), 'es')
                    phonetic_futures[f_es] = ("example", idx, 'phonetic_es')
                    f_en = pool.submit(phoneticize, e.get('en', ''), 'en')
                    phonetic_futures[f_en] = ("example", idx, 'phonetic_en')

                # Wait for all futures (paraphrase + phonetic) and apply results
                all_futures = list(para_futures.keys()) + list(phonetic_futures.keys())
                for fut in as_completed(all_futures):
                    if fut in para_futures:
                        idx = para_futures[fut]
                        try:
                            res = fut.result()
                            if res:
                                phrases_pairs[idx]['paraphrases_en'] = res
                        except Exception:
                            pass
                    else:
                        kind, idx, key = phonetic_futures[fut]
                        try:
                            val = fut.result()
                        except Exception:
                            val = ''
                        if kind == 'phrase':
                            phrases_pairs[idx][key] = val
                        else:
                            examples_pairs[idx][key] = val
        except Exception:
            # Fallback: sequential behavior identical to previous implementation
            translations = {t: translate_to_spanish(t) for t in texts_to_translate}
            lines = []
            lines.append(f"Lesson: {topic}\n")
            lines.append("Phrases:\n")
            for s in sentences:
                spanish = translations.get(s, translate_to_spanish(s))
                lines.append(f"- EN: {s}")
                lines.append(f"  ES: {spanish}\n")

            lines.append("Examples:\n")
            for ex in examples_en:
                lines.append(f"- EN: {ex}")
                lines.append(f"  ES: {translations.get(ex, translate_to_spanish(ex))}\n")

            lines.append("Mini-quiz:\n")
            quiz_q1 = f"Translate to Spanish: 'I like {topic}.'"
            quiz_q2 = f"Which sentence asks where to find {topic}?\n  A) I like {topic}.\n  B) Where can I find {topic}?\n  C) Describe {topic}."
            lines.append(f"1) {quiz_q1}")
            lines.append(f"   Answer: {translations.get(quiz_texts[0], translate_to_spanish(quiz_texts[0]))}\n")
            lines.append(f"2) {quiz_q2}")
            lines.append(f"   Answer: B) Where can I find {topic}? -> {translations.get(quiz_texts[1], translate_to_spanish(quiz_texts[1]))}")

            lesson_text = "\n".join(lines)

            phrases_pairs = [{"en": s, "es": translations.get(s, translate_to_spanish(s)), "difficulty": difficulty_of(s)} for s in sentences]
            examples_pairs = [{"en": e, "es": translations.get(e, translate_to_spanish(e)), "difficulty": difficulty_of(e)} for e in examples_en]

            for p in phrases_pairs:
                try:
                    paras = paraphrase(p['en'], max_results=2)
                    if paras:
                        p['paraphrases_en'] = paras
                except Exception:
                    pass
            for e in examples_pairs:
                # cloze removed; only phoneticization would run but we skip here
                try:
                    e['phonetic_es'] = phoneticize(e.get('es', ''), lang='es')
                    e['phonetic_en'] = phoneticize(e.get('en', ''), lang='en')
                except Exception:
                    e['phonetic_es'] = e.get('phonetic_es', '')
                    e['phonetic_en'] = e.get('phonetic_en', '')

        # Build the textual lesson using the translations mapping
        lines = []
        lines.append(f"Lesson: {topic}\n")
        lines.append("Phrases:\n")
        for s in sentences:
            spanish = translations.get(s, translate_to_spanish(s))
            lines.append(f"- EN: {s}")
            lines.append(f"  ES: {spanish}\n")

        lines.append("Examples:\n")
        for ex in examples_en:
            lines.append(f"- EN: {ex}")
            lines.append(f"  ES: {translations.get(ex, translate_to_spanish(ex))}\n")

        lines.append("Mini-quiz:\n")
        quiz_q1 = f"Translate to Spanish: 'I like {topic}.'"
        quiz_q2 = f"Which sentence asks where to find {topic}?\n  A) I like {topic}.\n  B) Where can I find {topic}?\n  C) Describe {topic}."
        lines.append(f"1) {quiz_q1}")
        lines.append(f"   Answer: {translations.get(quiz_texts[0], translate_to_spanish(quiz_texts[0]))}\n")
        lines.append(f"2) {quiz_q2}")
        lines.append(f"   Answer: B) Where can I find {topic}? -> {translations.get(quiz_texts[1], translate_to_spanish(quiz_texts[1]))}")

        lesson_text = "\n".join(lines)

        # Build paired lists so templates can iterate without special filters
        # Build phrase/example pairs first, then compute paraphrases/cloze in
        # parallel so CPU/network bound work can overlap and reduce overall time.
        phrases_pairs = [{"en": s, "es": translations.get(s, translate_to_spanish(s)), "difficulty": difficulty_of(s)} for s in sentences]
        examples_pairs = [{"en": e, "es": translations.get(e, translate_to_spanish(e)), "difficulty": difficulty_of(e)} for e in examples_en]

        # Parallelize enhancer calls (paraphrase and cloze) to speed up
        try:
            with ThreadPoolExecutor(max_workers=4) as ex:
                    para_futures = {ex.submit(paraphrase, p['en'], 2): idx for idx, p in enumerate(phrases_pairs)}

                    for fut in as_completed(para_futures):
                        idx = para_futures[fut]
                        try:
                            res = fut.result()
                            if res:
                                # store paraphrases (EN-side) so UI can choose which to show
                                phrases_pairs[idx]['paraphrases_en'] = res
                        except Exception:
                            # ignore enhancer failure; leave paraphrases absent
                            pass
        except Exception:
            # Fallback: run enhancers sequentially
            for p in phrases_pairs:
                try:
                    paras = paraphrase(p['en'], max_results=2)
                    if paras:
                        p['paraphrases_en'] = paras
                except Exception:
                    pass

        # Prepare bilingual quiz entries: include both EN and ES forms so
        # templates can render the prompt in the page language and reveal the
        # opposite language as the answer.
        quiz_entries = []

        q1_en = f"Translate to Spanish: 'I like {topic}.'"
        q1_es = translations.get(q1_en) or translate_to_spanish(q1_en)
        q1_answer_en = quiz_texts[0]
        q1_answer_es = translations.get(quiz_texts[0], translate_to_spanish(quiz_texts[0]))
        quiz_entries.append({
            "q_en": q1_en,
            "q_es": q1_es,
            "answer_text_en": q1_answer_en,
            "answer_text_es": q1_answer_es,
        })

        q2_en = f"Which sentence asks where to find {topic}?"
        q2_es = translations.get(q2_en) or translate_to_spanish(q2_en)
        choices_en = [f"I like {topic}.", f"Where can I find {topic}?", f"Describe {topic} in simple words."]
        # Translate choices into Spanish as well
        choices_es = [translations.get(c) or translate_to_spanish(c) for c in choices_en]
        q2_answer_en = choices_en[1]
        q2_answer_es = translations.get(q2_answer_en, translate_to_spanish(q2_answer_en))
        quiz_entries.append({
            "q_en": q2_en,
            "q_es": q2_es,
            "choices_en": choices_en,
            "choices_es": choices_es,
            "answer": 1,
            "answer_text_en": q2_answer_en,
            "answer_text_es": q2_answer_es,
        })

        # Topic translations
        topic_en = topic
        topic_es = translations.get(topic) or translate_to_spanish(topic)

        # Attach phonetic hints (parallelized) for each phrase/example.
        # We intentionally do NOT create exercise objects anymore; caller UI
        # should not rely on 'exercise_en' / 'exercise_es' keys.
        try:
            future_map = {}
            with ThreadPoolExecutor(max_workers=6) as pool:
                for idx, p in enumerate(phrases_pairs):
                    f_es = pool.submit(phoneticize, p.get('es', ''), 'es')
                    future_map[f_es] = ("phrase", idx, 'phonetic_es')
                    f_en = pool.submit(phoneticize, p.get('en', ''), 'en')
                    future_map[f_en] = ("phrase", idx, 'phonetic_en')

                for idx, e in enumerate(examples_pairs):
                    f_es = pool.submit(phoneticize, e.get('es', ''), 'es')
                    future_map[f_es] = ("example", idx, 'phonetic_es')
                    f_en = pool.submit(phoneticize, e.get('en', ''), 'en')
                    future_map[f_en] = ("example", idx, 'phonetic_en')

                for fut in as_completed(future_map):
                    kind, idx, key = future_map[fut]
                    try:
                        val = fut.result()
                    except Exception:
                        val = ''
                    if kind == 'phrase':
                        phrases_pairs[idx][key] = val
                    else:
                        examples_pairs[idx][key] = val
        except Exception:
            # Fallback: compute phonetics sequentially
            for p in phrases_pairs:
                try:
                    p['phonetic_es'] = phoneticize(p.get('es', ''), lang='es')
                    p['phonetic_en'] = phoneticize(p.get('en', ''), lang='en')
                except Exception:
                    p['phonetic_es'] = p.get('phonetic_es', '')
                    p['phonetic_en'] = p.get('phonetic_en', '')
            for e in examples_pairs:
                try:
                    e['phonetic_es'] = phoneticize(e.get('es', ''), lang='es')
                    e['phonetic_en'] = phoneticize(e.get('en', ''), lang='en')
                except Exception:
                    e['phonetic_es'] = e.get('phonetic_es', '')
                    e['phonetic_en'] = e.get('phonetic_en', '')

        lesson_struct = {
            "topic_en": topic_en,
            "topic_es": topic_es,
            "phrases": phrases_pairs,
            "examples": examples_pairs,
            "quiz": quiz_entries,
            # Provide localized labels so callers (templates/JS) can display
            # an appropriate heading without relying on Django gettext from
            # this core library.
            "mini_quiz_en": "Mini-quiz",
            "mini_quiz_es": "Mini-prueba",
            # Grouped difficulty views for simple progression UI
            "phrases_by_difficulty": {
                "easy": [p for p in phrases_pairs if p.get('difficulty') == 'easy'],
                "medium": [p for p in phrases_pairs if p.get('difficulty') == 'medium'],
                "hard": [p for p in phrases_pairs if p.get('difficulty') == 'hard'],
            },
            "examples_by_difficulty": {
                "easy": [e for e in examples_pairs if e.get('difficulty') == 'easy'],
                "medium": [e for e in examples_pairs if e.get('difficulty') == 'medium'],
                "hard": [e for e in examples_pairs if e.get('difficulty') == 'hard'],
            },
            # Localized UI labels (generator-provided fallbacks)
            "labels": {
                # Generic labels for headers and small tips
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
                "cloze_en": "Cloze",
                "cloze_es": "Relleno",
                "try_cloze_en": "Try the cloze",
                "try_cloze_es": "Prueba el rellenado",
                # Exercise default selection and naming
                "exercise_en": "Exercise",
                "exercise_es": "Ejercicio",
                # default selected difficulty
                "default_difficulty": "easy",
                "difficulty_en": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
                "difficulty_es": {"easy": "Fácil", "medium": "Medio", "hard": "Difícil"},
            },
        }
        if as_struct:
            return lesson_struct
        return lesson_text
    except Exception as e:
        logger.exception("Failed to build lesson: %s", e)
        # Last-resort fallback
        return f"Let's learn about {topic} today. Here are a few useful phrases about {topic}."
