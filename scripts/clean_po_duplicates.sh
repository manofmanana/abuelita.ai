#!/bin/bash
# -----------------------------------------------------------------------------
# 🧹 clean_po_duplicates.sh
# Cleans duplicate msgid entries from all Django .po files safely.
# -----------------------------------------------------------------------------

set -e

# Check dependencies
if ! command -v msguniq &> /dev/null; then
  echo "❌ Error: 'msguniq' not found. Install with: brew install gettext && brew link --force gettext"
  exit 1
fi

# Find and clean every .po file under locale/
for po_file in $(find locale -type f -name "*.po"); do
  echo "🧩 Cleaning duplicates in $po_file ..."
  msguniq --use-first "$po_file" -o "$po_file"
done

echo "✅ All duplicate msgids removed."

# Recompile translations
echo "⚙️ Compiling messages..."
python3 manage.py compilemessages || {
  echo "❌ Error compiling messages. Check for syntax or duplicate msgids."
  exit 1
}

echo "✅ Done. All translations compiled successfully!"
