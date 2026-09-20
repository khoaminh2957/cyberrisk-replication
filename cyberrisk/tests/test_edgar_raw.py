"""§2.2 on a cached raw EDGAR complete submission: header fields, main 10-K document, Item 1A."""
import glob, os
import pytest
from cyberrisk import edgar

CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "edgar_cache")


def test_header_document_and_item_1a():
    files = sorted(glob.glob(os.path.join(CACHE, "*.txt")))
    if not files:
        pytest.skip("no cached complete submissions")
    raw = open(files[0], "rb").read()
    h = edgar.submission_header(raw)
    assert h["form"] in edgar.FORMS and h["cik"].isdigit()
    assert len(h["period"]) == 8 and len(h["filed"]) == 8 and h["period"] <= h["filed"]
    doc = edgar.main_document(raw)
    assert len(doc) < len(raw) and "<" in doc[:5000].lower()
    sents = edgar.html_sentences(doc)
    span, by_ref = edgar.item_1a(sents)
    assert span and not by_ref
    assert not any(edgar._ITEM_1A.match(s.text) for s in span[1:])       # TOC entry not chosen
