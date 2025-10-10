from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.contrib import admin

# Include i18n endpoint globally
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # Language switch endpoint
]

# Wrap main routes with i18n_patterns for multilingual behavior
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("translator.urls")),
)

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
