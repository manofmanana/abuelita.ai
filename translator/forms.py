from pathlib import Path

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .documents import SUPPORTED_EXTENSIONS

LANG_CHOICES = [
    ("en", _("English")),
    ("es", _("Spanish")),
]


class TranslationForm(forms.Form):
    source_language = forms.ChoiceField(
        choices=LANG_CHOICES,
        initial="en",
        label=_("From"),
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    target_language = forms.ChoiceField(
        choices=LANG_CHOICES,
        initial="es",
        label=_("To"),
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    file_upload = forms.FileField(
        required=False,
        label=_("Upload a document (TXT, DOCX, PDF)"),
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ",".join(SUPPORTED_EXTENSIONS)}),
    )
    text_input = forms.CharField(
        required=False,
        label=_("Text to translate"),
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "class": "form-control",
                "maxlength": settings.ABUELITA_MAX_TRANSLATE_CHARS,
                "placeholder": _("Type or paste text, or use the microphone…"),
            }
        ),
    )

    def clean_file_upload(self):
        f = self.cleaned_data.get("file_upload")
        if not f:
            return f
        if Path(f.name).suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise forms.ValidationError(_("Unsupported file type."))
        if f.size > settings.ABUELITA_MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(
                _("That file is too large (max %(mb)s MB).") % {"mb": settings.ABUELITA_MAX_UPLOAD_MB}
            )
        return f

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("source_language") and cleaned.get("source_language") == cleaned.get("target_language"):
            raise forms.ValidationError(_("Please choose two different languages."))
        if not cleaned.get("file_upload") and not (cleaned.get("text_input") or "").strip():
            raise forms.ValidationError(_("Please enter or upload text to translate."))
        return cleaned
