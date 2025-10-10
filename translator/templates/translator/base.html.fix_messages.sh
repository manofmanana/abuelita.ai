#!/bin/bash
# Remove message alerts section from base.html to stop "Language changed" banner.

sed -i '' '/{% if messages %}/,/{% endif %}/d' translator/templates/translator/base.html

echo "✅ Removed the Django message alerts block from base.html."
