#!/bin/bash
file="abuelita_ai/urls.py"

# Only add if missing
if ! grep -q "set_language" "$file"; then
  echo "🔧 Adding /i18n/setlang/ route to $file..."
  echo "" >> "$file"
  echo "from django.conf.urls.i18n import set_language" >> "$file"
  echo "urlpatterns += [path('i18n/setlang/', set_language, name='set_language'),]" >> "$file"
else
  echo "✅ set_language already configured."
fi
