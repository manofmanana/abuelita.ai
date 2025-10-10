import os
import tempfile
import pyttsx3
from django.http import JsonResponse
from django.conf import settings

def speak_api(request):
    """Generate TTS audio from text and return URL."""
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if not text:
            return JsonResponse({"error": "No text provided."})

        try:
            # Create temporary audio file
            temp_dir = os.path.join(settings.MEDIA_ROOT, "tts")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, "abuelita_voice.mp3")

            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.save_to_file(text, file_path)
            engine.runAndWait()

            audio_url = f"{settings.MEDIA_URL}tts/abuelita_voice.mp3"
            return JsonResponse({"success": True, "audio_url": audio_url})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Invalid request."})
