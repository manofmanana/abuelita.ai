import os

import pytest

# Never hit Google Translate from the test suite: translations become
# deterministic "[es] text" markers (see ai_core/translator.py).
os.environ.setdefault("ABUELITA_OFFLINE", "1")


@pytest.fixture(autouse=True)
def _clear_translation_cache():
    from ai_core.translator import _translate_chunk

    _translate_chunk.cache_clear()
    yield
    _translate_chunk.cache_clear()
