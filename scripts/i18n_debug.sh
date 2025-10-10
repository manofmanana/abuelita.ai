#!/usr/bin/env bash
set -euo pipefail

PO="locale/es/LC_MESSAGES/django.po"
MO="locale/es/LC_MESSAGES/django.mo"

mkdir -p locale/es/LC_MESSAGES logs
cp -f "$PO" "locale/es/LC_MESSAGES/django.po.pre_debug.$(date +%s).bak" 2>/dev/null || true

echo "== check gettext binaries =="
command -v msgfmt || { echo "msgfmt missing (brew install gettext && brew link --force gettext)"; exit 1; }
command -v msguniq || echo "msguniq missing (brew install gettext && brew link --force gettext)"

echo "== validate PO with msgfmt (full errors) =="
if ! msgfmt -cv -o /tmp/django_test.mo "$PO" 2> logs/msgfmt_first.err ; then
  echo "== msgfmt reported errors (first pass) =="
  cat logs/msgfmt_first.err || true

  if command -v msguniq >/dev/null 2>&1; then
    echo "== try dedup/cleanup with msguniq =="
    msguniq --use-first "$PO" -o "$PO".dedup || true
    mv "$PO".dedup "$PO"

    echo "== re-validate after dedup =="
    if ! msgfmt -cv -o /tmp/django_test.mo "$PO" 2> logs/msgfmt_after_dedup.err ; then
      echo "== still failing; showing errors =="
      cat logs/msgfmt_after_dedup.err || true
      exit 2
    fi
  else
    echo "== cannot auto-fix duplicates without msguniq =="
    exit 2
  fi
fi

echo "== compilemessages (verbose) =="
django-admin compilemessages -v 3 --traceback 2>&1 | tee logs/compilemessages.log

echo "== done =="
