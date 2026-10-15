import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ai_core import translator as core_translator

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


def post(client, data, ajax=True):
    return client.post("/en/", data, **(AJAX if ajax else {}))


@pytest.mark.django_db
def test_index_renders_language_selects(client):
    resp = client.get("/en/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="id_source_language"' in content
    assert 'id="id_target_language"' in content
    assert "translation-result" in content


@pytest.mark.django_db
def test_translate_text_server_render(client):
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "Hello world"}, ajax=False)
    assert resp.status_code == 200
    assert "[es] Hello world" in resp.content.decode()


@pytest.mark.django_db
def test_translate_ajax_returns_json(client):
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "Hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "ok": True,
        "translation_result": "[es] Hello",
        "target_language": "es",
        "download_url": None,
        "truncated": False,
    }


@pytest.mark.django_db
def test_same_language_is_rejected(client):
    resp = post(client, {"source_language": "en", "target_language": "en", "text_input": "Hello"})
    assert resp.status_code == 400
    assert "two different languages" in resp.json()["error"]


@pytest.mark.django_db
def test_empty_input_is_rejected(client):
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "   "})
    assert resp.status_code == 400
    assert resp.json()["ok"] is False


@pytest.mark.django_db
def test_unsupported_file_type_is_rejected(client):
    upload = SimpleUploadedFile("notes.exe", b"MZ...")
    resp = post(client, {"source_language": "en", "target_language": "es", "file_upload": upload})
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["error"]


@pytest.mark.django_db
def test_txt_upload_can_be_downloaded(client):
    upload = SimpleUploadedFile("carta.txt", b"Dear grandma, I miss you.")
    resp = post(client, {"source_language": "en", "target_language": "es", "file_upload": upload})
    data = resp.json()
    assert data["ok"] and data["download_url"]

    download = client.get(data["download_url"])
    assert download.status_code == 200
    assert "carta_translated.txt" in download["Content-Disposition"]
    assert download.content.decode() == "[es] Dear grandma, I miss you."


@pytest.mark.django_db
def test_docx_upload_is_translated(client):
    from docx import Document

    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Take one pill every morning.")
    doc.save(buf)
    upload = SimpleUploadedFile("receta.docx", buf.getvalue())
    resp = post(client, {"source_language": "en", "target_language": "es", "file_upload": upload})
    assert resp.json()["translation_result"] == "[es] Take one pill every morning."


@pytest.mark.django_db
def test_download_link_is_private_to_the_session(client):
    from django.test import Client

    upload = SimpleUploadedFile("a.txt", b"Hello")
    url = post(client, {"source_language": "en", "target_language": "es", "file_upload": upload}).json()["download_url"]
    assert Client().get(url).status_code == 404


@pytest.mark.django_db
def test_text_already_in_target_language_is_flipped(client, monkeypatch):
    calls = []

    def fake_translate(text, source="auto", target="es"):
        calls.append((source, target))
        return "Where is the pharmacy?" if target == "en" else text

    monkeypatch.setattr("translator.views.translate", fake_translate)
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "¿Dónde está la farmacia?"})
    data = resp.json()
    assert data["translation_result"] == "Where is the pharmacy?"
    assert data["target_language"] == "en"
    assert calls == [("en", "es"), ("auto", "en")]


@pytest.mark.django_db
def test_service_outage_shows_friendly_error(client, monkeypatch):
    def broken(*args, **kwargs):
        raise core_translator.TranslationError("boom")

    monkeypatch.setattr("translator.views.translate", broken)
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "Hello"})
    assert resp.status_code == 400
    assert "unavailable" in resp.json()["error"]


@pytest.mark.django_db
def test_long_text_is_truncated(client, settings):
    settings.ABUELITA_MAX_TRANSLATE_CHARS = 10
    resp = post(client, {"source_language": "en", "target_language": "es", "text_input": "a" * 50})
    data = resp.json()
    assert data["truncated"] is True
    assert data["translation_result"] == "[es] " + "a" * 10


def test_split_into_chunks_respects_limit():
    text = ("This is a sentence. " * 400 + "\n\n") * 3
    chunks = core_translator.split_into_chunks(text, limit=500)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)
    assert "".join(chunks).split() == text.split()


def test_translate_joins_chunks(monkeypatch):
    monkeypatch.setattr(core_translator, "MAX_CHUNK_CHARS", 20)
    text = "One two three. Four five six. Seven eight nine."
    out = core_translator.translate(text, "en", "es")
    assert out.count("[es]") > 1
