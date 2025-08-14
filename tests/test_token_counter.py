from backend.pdf_to_audiobook.token_counter import count_tokens, count_tokens_streaming

def test_simple_count():
    s = "Hello world"
    t = count_tokens(s)
    assert isinstance(t, int) and t > 0

def test_stream_vs_direct():
    s = "This is a longer text. " * 1000
    a = count_tokens(s)
    b = count_tokens_streaming(s, chunk_chars=1000)
    assert abs(a - b) <= 5  # small tolerance
