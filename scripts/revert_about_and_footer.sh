#!/usr/bin/env bash
set -euo pipefail

# Restore original about.html from git or manual backup if available
if [ -f translator/templates/translator/about.html.bak ]; then
  mv translator/templates/translator/about.html.bak translator/templates/translator/about.html
  echo "✅ Restored translator/about.html from backup"
else
  echo "⚠️ No .bak file found for about.html — skipping restore"
fi

# Restore base.html footer and CSS edits
if [ -f translator/templates/translator/base.html.bak ]; then
  mv translator/templates/translator/base.html.bak translator/templates/translator/base.html
  echo "✅ Restored translator/base.html from backup"
else
  echo "⚠️ No .bak file found for base.html — skipping restore"
fi

# Remove the script that caused the footer edits
rm -f scripts/fix_footer_and_scroll.sh
echo "🧹 Removed fix_footer_and_scroll.sh"
