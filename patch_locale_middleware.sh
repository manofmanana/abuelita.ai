#!/bin/bash
# Adds LocaleMiddleware to settings.py if not already present
SETTINGS_FILE="abuelita_ai/settings.py"
if ! grep -q "django.middleware.locale.LocaleMiddleware" "$SETTINGS_FILE"; then
  awk '/SessionMiddleware/ {
    print $0;
    print "    '\''django.middleware.locale.LocaleMiddleware'\'',";
    next
  }1' "$SETTINGS_FILE" > tmpfile && mv tmpfile "$SETTINGS_FILE"
  echo "✅ LocaleMiddleware added to settings.py"
else
  echo "⚙️ LocaleMiddleware already exists"
fi
