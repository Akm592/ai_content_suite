import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import tiktoken; if unavailable, use fallback
try:
    import tiktoken
    _HAS_TIKTOKEN = True
except Exception:
    _HAS_TIKTOKEN = False

# Default model name (adjust to whatever model you target)
DEFAULT_MODEL = "gpt-4o"  # change as needed

# Cache encoding to avoid repeated lookups
_ENCODING_CACHE = {}

def _get_encoding_for_model(model: str = DEFAULT_MODEL):
    """Return a tiktoken encoding object for the specified model; cache results."""
    if not _HAS_TIKTOKEN:
        return None
    if model in _ENCODING_CACHE:
        return _ENCODING_CACHE[model]
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        # fallback to a commonly-used encoding when model lookup fails
        enc = tiktoken.get_encoding("cl100k_base")
    _ENCODING_CACHE[model] = enc
    return enc

def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    """
    Count tokens for a given text using tiktoken if available, otherwise use
    a conservative estimate (chars / 4).
    """
    if not text:
        return 0
    if _HAS_TIKTOKEN:
        enc = _get_encoding_for_model(model)
        try:
            token_ids = enc.encode(text)
            return len(token_ids)
        except Exception as e:
            logger.warning("tiktoken failed to encode text; falling back to estimate: %s", e)

    # Conservative fallback estimate: ~4 characters per token (safe guard)
    avg_chars_per_token = 4
    return max(1, len(text) // avg_chars_per_token)

def count_tokens_streaming(text: str, model: str = DEFAULT_MODEL, chunk_chars: int = 20000) -> int:
    """
    Count tokens by splitting text into chunks to avoid large allocations for huge docs.
    Useful when text can be very large.
    """
    if not text:
        return 0
    if not _HAS_TIKTOKEN:
        # fallback estimate
        return count_tokens(text, model)

    enc = _get_encoding_for_model(model)
    total = 0
    for i in range(0, len(text), chunk_chars):
        chunk = text[i:i + chunk_chars]
        total += len(enc.encode(chunk))
    return total
