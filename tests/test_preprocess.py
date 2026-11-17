from src.data.preprocess import clean_text, normalize


def test_clean_strips_urls_mentions_hashtag_symbol():
    assert clean_text("@bob LOVE this!! http://t.co/abc #nova") == "love this nova"


def test_normalize_keeps_negation_drops_stopwords():
    out = normalize("this is not good")
    assert "not" in out.split() and "this" not in out.split()
