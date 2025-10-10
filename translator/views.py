import os
from django.shortcuts import render
from deep_translator import GoogleTranslator
from PyPDF2 import PdfReader
from docx import Document
from .forms import TranslationForm
from django.http import JsonResponse, FileResponse, Http404
import uuid
import tempfile
from pathlib import Path
from .models import Lesson
import logging

logger = logging.getLogger(__name__)

def home(request):
    translation_result = None
    download_url = None
    if request.method == "POST":
        form = TranslationForm(request.POST, request.FILES)
        if form.is_valid():
            from django.utils.translation import gettext as _
            src = form.cleaned_data["source_language"]
            tgt = form.cleaned_data["target_language"]
            text_input = form.cleaned_data["text_input"]
            uploaded_file = form.cleaned_data["file_upload"]

            if src == tgt:
                translation_result = _("Please choose two different languages.")
                return render(request, "translator/index.html", {"form": form, "translation_result": translation_result})

            content = ""
            # Handle file uploads
            if uploaded_file:
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                try:
                    if ext == ".txt":
                        content = uploaded_file.read().decode("utf-8")
                    elif ext == ".pdf":
                        reader = PdfReader(uploaded_file)
                        content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    elif ext == ".docx":
                        doc = Document(uploaded_file)
                        content = "\n".join([p.text for p in doc.paragraphs])
                    else:
                        translation_result = _("Unsupported file type.")
                except Exception as e:
                    translation_result = _("Error reading file: ") + str(e)
            else:
                content = text_input.strip()

            # Perform translation
            if content:
                try:
                    # Attempt translation using the client-provided source/target.
                    translator = GoogleTranslator(source=src, target=tgt)
                    translation_result = translator.translate(content)
                    # If the translation is identical to the input (common when
                    # the provided source language is wrong), retry with auto
                    # language detection. This is a conservative fallback that
                    # helps mobile users who may accidentally have the source
                    # set incorrectly.
                    try:
                        if translation_result and content and translation_result.strip().lower() == content.strip().lower() and src != 'auto':
                            auto_translator = GoogleTranslator(source='auto', target=tgt)
                            alt = auto_translator.translate(content)
                            if alt and alt.strip().lower() != content.strip().lower():
                                translation_result = alt
                    except Exception:
                        # If auto-detect retry fails for any reason, stick with original result
                        pass
                    # If user uploaded a file, write translated text to a temp file
                    # and provide a download URL so the user can retrieve it.
                    if uploaded_file:
                        try:
                            uid = str(uuid.uuid4())
                            # Preserve original filename base and use .txt for translated output
                            orig_name = Path(uploaded_file.name).stem
                            out_name = f"{orig_name}_translated.txt"
                            tmp = tempfile.NamedTemporaryFile(delete=False, prefix=f"translated_{uid}_", suffix='.txt')
                            tmp.write(translation_result.encode('utf-8'))
                            tmp.flush()
                            tmp.close()
                            # store mapping in module-level dict for retrieval
                            try:
                                TRANSLATED_FILES
                            except NameError:
                                TRANSLATED_FILES = {}
                            TRANSLATED_FILES[uid] = {'path': tmp.name, 'name': out_name}
                            from django.urls import reverse
                            download_url = reverse('translator:download_translated', args=[uid])
                        except Exception:
                            download_url = None
                except Exception as e:
                    translation_result = _("Translation error: ") + str(e)
            else:
                translation_result = _("Please enter or upload text to translate.")
    else:
        form = TranslationForm()

    return render(request, "translator/index.html", {"form": form, "translation_result": translation_result, "download_url": download_url})


def download_translated(request, uid):
    """Serve a previously-generated translated file stored in a temp file.

    This uses an in-memory mapping of uid -> temp file path created when the
    translation was performed. It's intentionally simple for demo/testing and
    not intended as a production storage strategy.
    """
    try:
        TRANSLATED_FILES
    except NameError:
        TRANSLATED_FILES = {}
    info = TRANSLATED_FILES.get(str(uid))
    if not info:
        raise Http404("Translated file not found")
    path = info.get('path')
    name = info.get('name')
    try:
        return FileResponse(open(path, 'rb'), as_attachment=True, filename=name)
    except Exception:
        raise Http404("Could not open translated file")

def learn(request):
    lesson_output = None
    lesson_struct = None
    if request.method == "POST":
        prompt = request.POST.get("input_text", "").strip()
        if prompt:
            try:
                # Request structured lesson data so templates can render EN/ES separately
                # Lazy import AI helpers to avoid import-time side effects during test collection
                from ai_core import generate_lesson, _build_lesson_from_sentences
                lesson_struct = generate_lesson(prompt, as_struct=True)
                # Build a simple text rendering for older code paths by extracting
                # the English phrases from the structured output.
                phrases_en = [p.get("en") for p in lesson_struct.get("phrases", []) if isinstance(p, dict) and p.get("en")]
                lesson_output = _build_lesson_from_sentences(prompt, phrases_en)

                # If this is an AJAX request, return JSON so the frontend can update
                if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                    return JsonResponse({"ok": True, "lesson_struct": lesson_struct, "lesson_output": lesson_output})
            except Exception as e:
                # Safety: never crash the view if AI backend fails
                lesson_output = f"[error generating lesson] {e}"
    return render(request, "translator/learn.html", {"lesson_output": lesson_output, "lesson_struct": lesson_struct})

# Culture page removed per product decision.

def about(request):
    return render(request, "translator/about.html")


def save_lesson(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    title = request.POST.get('title') or ''
    content = request.POST.get('content') or ''
    lang = request.POST.get('language') or 'es'
    if not content:
        return JsonResponse({'error': 'content required'}, status=400)
    l = Lesson.objects.create(title=title, content=content, language=lang)
    return JsonResponse({'ok': True, 'id': l.id})


def recommend(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    content = request.POST.get('content') or ''
    # For demo, build a small corpus from recent lessons
    corpus = [l.content for l in Lesson.objects.all().order_by('-created_at')[:50]]
    try:
        # Lazy import the recommender helper to avoid import-time heavy work
        from ai_core import recommend_similar
        recs = recommend_similar(content, corpus_texts=corpus, topn=3)
        return JsonResponse({'ok': True, 'recommendations': recs})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def clear_cookies(request):
    """Development helper: clear the language cookie so you can test language switching.

    Removes the `django_language` cookie and redirects back to the Referer or site root.
    This is safe for development and doesn't modify server-side session data.
    """
    from django.shortcuts import redirect

    next_url = request.META.get("HTTP_REFERER") or "/"
    response = redirect(next_url)
    # Remove django language cookie
    response.delete_cookie("django_language")
    return response

from django.http import JsonResponse
import pyttsx3
import tempfile
import os

def health(request):
    """Lightweight health endpoint used by tests.

    Returns a predictable JSON payload that the test asserts on.
    """
    return JsonResponse({"ok": True, "view": "health", "about_url": "/about/"})

def speak_api(request):
    """
    Temporary speech endpoint — supports offline TTS with pyttsx3.
    Future-ready for hybrid AI (like HuggingFace TTS or OpenAI).
    """
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if not text:
            return JsonResponse({"error": "No text provided"}, status=400)

        try:
            engine = pyttsx3.init()
            # Set Spanish or English voice based on text language guess
            if any(word in text.lower() for word in ["hola", "buenos", "gracias", "mañana"]):
                # Try to use a Spanish voice if available
                for voice in engine.getProperty("voices"):
                    if "spanish" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            else:
                for voice in engine.getProperty("voices"):
                    if "english" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break

            # Save to temporary audio file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                engine.save_to_file(text, tmp.name)
                engine.runAndWait()
                tmp_path = tmp.name

            # Return just confirmation for now
            return JsonResponse({"success": True, "message": "Speech generated locally."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)
from .views_speak import speak_api


# Note: LMS and OOAPI integrations removed in favor of local ai_core-based features.
