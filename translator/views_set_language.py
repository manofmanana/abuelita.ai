from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def silent_set_language(request):
    """
    Same as Django’s built-in set_language, but without triggering the
    annoying 'Language changed to English' message.
    """
    lang_code = request.POST.get('language', None)
    if lang_code and lang_code in dict(settings.LANGUAGES):
        translation.activate(lang_code)
        if hasattr(request, 'session'):
            request.session[translation.LANGUAGE_SESSION_KEY] = lang_code
        else:
            response = HttpResponseRedirect(request.POST.get('next', '/'))
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
            return response

    next_url = request.POST.get('next', '/')
    return HttpResponseRedirect(next_url)
