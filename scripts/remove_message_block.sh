#!/bin/bash
# Removes the Django messages alert block from base.html safely.

file="translator/templates/translator/base.html"

if grep -q "{% if messages %}" "$file"; then
  # Delete the message block safely
  sed -i '' '/{% if messages %}/,/{% endif %}/d' "$file"
  echo "✅ Removed Django message alerts block from base.html."
else
  echo "ℹ️ No message block found in base.html — already clean."
fi
