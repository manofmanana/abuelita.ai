#!/bin/bash
file="abuelita_ai/urls.py"

if ! grep -q "localized_set_language" "$file"; then
  echo "�� Updating $file to use localized_set_language..."
  sed -i '' '/from django.conf.urls.i18n import set_language/d' "$file"
  echo "from translator.views_set_language import localized_set_language" >> "$file"
  sed -i '' "s|path('i18n/setlang/', .*|path('i18n/setlang/', localized_set_language, name='set_language'),|" "$file"
else
  echo "✅ localized_set_language already configured."
fi
