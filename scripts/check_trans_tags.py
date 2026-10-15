#!/usr/bin/env python3
"""Check repository templates for multi-line/split `{% trans %}` occurrences.

This script scans the repository for `{% trans %}` template tags that are
split across multiple lines (for example, the opening token or the string
literal broken onto separate lines). Those splits break Django's i18n
message extraction and often lead to missing translations at runtime.

Exit code 0 if no issues found, 1 if any problematic tags are discovered.
"""

import re
from pathlib import Path


def find_multiline_trans_tags(root: Path) -> list[tuple[str, str]]:
    """Return a list of (filepath, matched_snippet) for multi-line trans tags.

    We look for `{% trans` ... `%}` sequences and report those whose
    matched content contains a newline (i.e., split across lines).
    """
    pattern = re.compile(r"\{%\s*trans\b[\s\S]*?%\}", re.MULTILINE)
    failures = []
    # Search any templates folder anywhere in the repo
    for p in root.rglob("**/templates/**/*.html"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            # ignore files we can't read
            continue
        for m in pattern.finditer(txt):
            s = m.group(0)
            if "\n" in s:
                failures.append((str(p), s.strip()))
    return failures


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    failures = find_multiline_trans_tags(repo_root)
    if failures:
        print("Found multi-line/split {% trans %} occurrences in templates:\n")
        for fp, snippet in failures:
            print(f"File: {fp}\n{snippet}\n---\n")
        return 1

    print("No multi-line {% trans %} occurrences found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
