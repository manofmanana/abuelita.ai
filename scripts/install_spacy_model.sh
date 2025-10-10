#!/usr/bin/env bash
# Install spaCy English model for CI and local dev if not already present.
# Usage: ./scripts/install_spacy_model.sh
set -euo pipefail

# Use python from .venv if present
PYTHON=python3
if [ -f ".venv/bin/python" ]; then
  PYTHON=.venv/bin/python
fi

# Install spaCy model
echo "Checking spaCy model en_core_web_sm..."
if ${PYTHON} -c "import importlib, sys
try:
    importlib.import_module('en_core_web_sm')
    sys.exit(0)
except Exception:
    sys.exit(1)"; then
  echo "spaCy model en_core_web_sm already installed"
else
  echo "Installing spaCy model en_core_web_sm..."
  ${PYTHON} -m spacy download en_core_web_sm
fi

echo "spaCy model check complete."
