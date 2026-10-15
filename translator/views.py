import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import content_disposition_header
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from ai_core import TranslationError, generate_lesson, lesson_to_text, recommend_similar, translate

from .documents import DocumentError, extract_text
from .forms import TranslationForm
from .models import Lesson

logger = logging.getLogger(__name__)

# Translated documents are kept in the user's session (not on disk) so the
# download link works across worker processes and nothing leaks on the server.
SESSION_DOWNLOADS_KEY = "translated_files"
MAX_SESSION_DOWNLOADS = 3
LESSON_SUGGESTIONS = ["food", "travel", "toys", "family", "cook", "music"]


def _is_ajax(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _remember_download(request, original_name: str, text: str) -> str:
    uid = uuid.uuid4().hex
    downloads = request.session.get(SESSION_DOWNLOADS_KEY, {})
    downloads[uid] = {"name": f"{Path(original_name).stem}_translated.txt", "text": text}
    # Keep only the most recent few files.
    request.session[SESSION_DOWNLOADS_KEY] = dict(list(downloads.items())[-MAX_SESSION_DOWNLOADS:])
    return reverse("translator:download_translated", args=[uid])


@require_http_methods(["GET", "POST"])
def home(request):
    context = {"form": TranslationForm()}
    if request.method == "GET":
        return render(request, "translator/index.html", context)

    form = TranslationForm(request.POST, request.FILES)
    context["form"] = form
    error = None
    if not form.is_valid():
        error = " ".join(msg for msgs in form.errors.values() for msg in msgs)
    else:
        data = form.cleaned_data
        uploaded = data["file_upload"]
        try:
            content = extract_text(uploaded) if uploaded else data["text_input"]
            content = content.strip()
            if not content:
                raise DocumentError(_("We couldn't find any text to translate."))

            limit = settings.ABUELITA_MAX_TRANSLATE_CHARS
            truncated = len(content) > limit
            content = content[:limit]

            source, target = data["source_language"], data["target_language"]
            result = translate(content, source, target)
            # Output identical to the input means the text was already in the
            # target language (e.g. Spanish typed with "From: English"). The
            # user almost certainly wants the other direction, so flip it.
            if result.strip().lower() == content.lower():
                flipped = translate(content, "auto", source)
                if flipped and flipped.strip().lower() != content.lower():
                    result, target = flipped, source

            context.update(
                translation_result=result,
                target_language=target,
                truncated=truncated,
                download_url=_remember_download(request, uploaded.name, result) if uploaded else None,
            )
        except DocumentError as exc:
            error = str(exc)
        except TranslationError:
            error = _("The translation service is unavailable right now. Please try again in a moment.")

    context["error"] = error
    if _is_ajax(request):
        if error:
            return JsonResponse({"ok": False, "error": error}, status=400)
        return JsonResponse(
            {
                "ok": True,
                "translation_result": context["translation_result"],
                "target_language": context["target_language"],
                "download_url": context["download_url"],
                "truncated": context["truncated"],
            }
        )
    return render(request, "translator/index.html", context, status=400 if error else 200)


@require_GET
def download_translated(request, uid):
    info = request.session.get(SESSION_DOWNLOADS_KEY, {}).get(uid)
    if not info:
        raise Http404("Translated file not found")
    response = HttpResponse(info["text"], content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = content_disposition_header(as_attachment=True, filename=info["name"])
    return response


@require_http_methods(["GET", "POST"])
def learn(request):
    # GET ?topic=... makes lessons linkable; POST keeps the classic form flow.
    topic = (request.POST.get("input_text") if request.method == "POST" else request.GET.get("topic")) or ""
    topic = topic.strip()
    lesson_struct = generate_lesson(topic, as_struct=True) if topic else None

    if lesson_struct and _is_ajax(request):
        # The rendered fragment lets the page swap in the lesson without
        # duplicating the template in JavaScript.
        html = render_to_string("translator/partials/lesson.html", {"lesson_struct": lesson_struct}, request=request)
        return JsonResponse(
            {
                "ok": True,
                "lesson_struct": lesson_struct,
                "lesson_output": lesson_to_text(lesson_struct),
                "html": html,
            }
        )
    return render(
        request,
        "translator/learn.html",
        {"lesson_struct": lesson_struct, "topic": topic, "suggestions": LESSON_SUGGESTIONS},
    )


def about(request):
    return render(request, "translator/about.html")


def health(request):
    return JsonResponse({"ok": True, "view": "health", "about_url": "/about/"})


@require_POST
def save_lesson(request):
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"error": "content required"}, status=400)
    lesson = Lesson.objects.create(
        title=(request.POST.get("title") or "")[:200],
        content=content,
        language=(request.POST.get("language") or "es")[:10],
    )
    return JsonResponse({"ok": True, "id": lesson.id})


@require_POST
def recommend(request):
    content = request.POST.get("content") or ""
    corpus = list(Lesson.objects.order_by("-created_at").values_list("content", flat=True)[:50])
    return JsonResponse({"ok": True, "recommendations": recommend_similar(content, corpus_texts=corpus, topn=3)})
