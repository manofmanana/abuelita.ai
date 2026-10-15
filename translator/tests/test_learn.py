import pytest

from ai_core import generate_lesson

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


@pytest.mark.django_db
def test_learn_ajax_returns_struct_text_and_html(client):
    resp = client.post("/en/learn/", {"input_text": "legos"}, **AJAX)
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/json"
    data = resp.json()
    assert data["ok"] is True
    assert {"lesson_struct", "lesson_output", "html"} <= data.keys()
    assert 'class="translation-result lesson' in data["html"]
    for item in data["lesson_struct"]["phrases"] + data["lesson_struct"]["examples"]:
        assert item["en"].strip() and item["es"].strip()


@pytest.mark.django_db
def test_learn_get_with_topic_renders_lesson(client):
    resp = client.get("/en/learn/", {"topic": "travel"})
    content = resp.content.decode()
    assert resp.status_code == 200
    assert "Lesson Result" in content
    assert "Topic: travel" in content


@pytest.mark.django_db
def test_learn_shows_easy_level_by_default(client):
    content = client.get("/en/learn/", {"topic": "lego"}).content.decode()
    assert 'data-diff="easy" role="tabpanel" >' in content or 'data-diff="easy" role="tabpanel">' in content
    assert 'data-diff="hard" role="tabpanel" hidden' in content


@pytest.mark.django_db
def test_learn_escapes_user_input(client):
    payload = "<img src=x onerror=alert(1)>"
    data = client.post("/en/learn/", {"input_text": payload}, **AJAX).json()
    assert "<img src=x" not in data["html"]
    assert "&lt;img" in data["html"]


@pytest.mark.django_db
def test_quiz_direction_matches_page_language(client):
    en = client.get("/en/learn/", {"topic": "lego"}).content.decode()
    es = client.get("/es/learn/", {"topic": "lego"}).content.decode()
    # English speakers translate *to* Spanish; Spanish speakers *to* English.
    assert "Translate to Spanish" in en
    assert "Traduce al inglés" in es
    assert 'class="quiz-answer mt-1 fw-semibold" hidden lang="es"' in en
    assert 'class="quiz-answer mt-1 fw-semibold" hidden lang="en"' in es


@pytest.mark.parametrize("topic", ["../../abuelita_ai/settings", "..", "/etc/passwd", "toys/../../x"])
def test_topic_cannot_read_files_outside_data_dir(topic, monkeypatch):
    from ai_core import generator

    opened = []
    real_read_text = generator.Path.read_text

    def spy(self, *args, **kwargs):
        opened.append(self)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(generator.Path, "read_text", spy)
    generate_lesson(topic, as_struct=True)
    assert all(p.parent == generator.DATA_PATH for p in opened)


def test_generator_failure_still_returns_struct(monkeypatch):
    from ai_core import generator

    def boom(topic):
        raise RuntimeError("nope")

    monkeypatch.setattr(generator, "_build_lesson", boom)
    lesson = generate_lesson("cats", as_struct=True)
    assert isinstance(lesson, dict)
    assert lesson["phrases"] and lesson["levels"]


def test_topic_length_is_capped():
    lesson = generate_lesson("word " * 100, as_struct=True)
    assert len(lesson["topic_en"]) <= 80


def test_text_rendering():
    text = generate_lesson("food")
    assert text.startswith("Lesson: food")
    assert "Mini-quiz:" in text


def test_mass_nouns_are_not_pluralised():
    lesson = generate_lesson("music", as_struct=True)
    text = " ".join(p["en"] for p in lesson["phrases"] + lesson["examples"])
    assert "musics" not in text
    assert lesson["quiz"][0]["answer_text_en"] == "I like music."
