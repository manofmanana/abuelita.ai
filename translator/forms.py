from django import forms

LANG_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

class TranslationForm(forms.Form):
    source_language = forms.ChoiceField(choices=LANG_CHOICES, label="From")
    target_language = forms.ChoiceField(choices=LANG_CHOICES, label="To")
    file_upload = forms.FileField(
        required=False,
        label="Upload a document (TXT, DOCX, PDF)"
    )
    text_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False,
        label="Text to translate"
    )
