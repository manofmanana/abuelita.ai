#!/usr/bin/env bash
set -euo pipefail

if ! command -v msgfmt >/dev/null 2>&1; then
  echo "gettext not found. Install with: brew install gettext && brew link --force gettext"
fi

mkdir -p locale/es/LC_MESSAGES
cp -f locale/es/LC_MESSAGES/django.po "locale/es/LC_MESSAGES/django.po.bak.$(date +%s)" 2>/dev/null || true

django-admin makemessages -l es

python3 - <<'PY'
import re, os
po_path = "locale/es/LC_MESSAGES/django.po"
target = "Bridge language barriers with bilingual translation and cultural wisdom — inspired by my grandmother, Francisca Martínez."
trans  = "Rompe las barreras del idioma con traducción bilingüe y sabiduría cultural — inspirada por mi abuela, Francisca Martínez."
if os.path.exists(po_path):
    text = open(po_path, "r", encoding="utf-8").read()
    pattern = re.compile(r'(?ms)^msgid "' + re.escape(target) + r'"\s*^msgstr ".*?"')
    if pattern.search(text):
        text = pattern.sub(f'msgid "{target}"\nmsgstr "{trans}"', text)
    else:
        text += f'\n\n#: translator/templates/translator/index.html\nmsgid "{target}"\nmsgstr "{trans}"\n'
    open(po_path, "w", encoding="utf-8").write(text)
PY

django-admin compilemessages -v 2
