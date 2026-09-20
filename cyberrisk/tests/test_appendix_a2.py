"""Round-1 check against the paper's own ground truth (Appendix A.2): on the real FY2017 10-Ks of
Apple, Abbott, GM and Verizon, the extractor must capture exactly the sentences the paper says
its algorithm captured, and miss exactly the ones it says it missed."""
import difflib, os, re
import pytest
from cyberrisk.edgar import item_1a_from_html
from cyberrisk.extract import extract
from cyberrisk.tests.appendix_a2_fixture import FILINGS, EXPECTED

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "edgar")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _run(firm):
    fname, n_captured = FILINGS[firm]
    path = os.path.join(DATA, fname)
    if not os.path.exists(path):
        pytest.skip("filing not downloaded: " + fname)
    span, by_ref = item_1a_from_html(open(path, encoding="utf-8", errors="ignore").read())
    assert span and not by_ref
    caps = {c.index: c for c in extract(span)}
    return span, caps, n_captured


@pytest.mark.parametrize("firm", list(FILINGS))
def test_capture_matches_paper(firm):
    span, caps, n_paper = _run(firm)
    normed = [norm(s.text) for s in span]
    mismatches, type_disagreements = [], []
    for want_captured, want_type, sentence in EXPECTED[firm]:
        # the appendix transcription is not verbatim (e.g. "cyber attack" -> "cyberattack",
        # dropped words), so take the most similar Item 1A sentence
        target = norm(sentence)
        i, score = max(((k, difflib.SequenceMatcher(None, target, n).ratio()) for k, n in enumerate(normed)),
                       key=lambda t: t[1])
        assert score >= 0.75, f"{firm}: sentence not found in Item 1A after splitting: {sentence[:60]}"
        got = i in caps
        if got != want_captured:
            mismatches.append((want_captured, sentence[:70]))
        elif got and caps[i].sentence_type != want_type:
            type_disagreements.append((want_type, caps[i].sentence_type, caps[i].indirect, sentence[:50]))
    assert not mismatches, f"{firm}: captured status differs from paper for {mismatches}"
    # the paper reports N captured for the relevant paragraph + "other paragraphs"
    assert len(caps) == n_paper, f"{firm}: captured {len(caps)} sentences, paper reports {n_paper}"
    print(f"\n{firm}: {len(caps)} captured (paper {n_paper}); type disagreements (informational): "
          f"{len(type_disagreements)}/{len(EXPECTED[firm])}")
    for t in type_disagreements:
        print("   paper=%s ours=%s cats=%s | %s" % t)
