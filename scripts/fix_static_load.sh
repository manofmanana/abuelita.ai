#!/usr/bin/env bash
set -euo pipefail

for template in translator/templates/translator/{learn,culture,about}.html; do
  if ! grep -q "{% load static" "$template"; then
    echo "⚙️  Adding '{% load static %}' to $template"
    # Insert right after the extends line
    awk 'NR==1{print; print "{% load static %}"; next}1' "$template" > "$template.tmp" && mv "$template.tmp" "$template"
  else
    echo "✅ $template already has {% load static %}"
  fi
done
