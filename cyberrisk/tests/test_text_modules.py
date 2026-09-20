"""Unit checks of the text half of the pipeline on hand-made sentences (rules of Appendix A,
word roots and vectors of §2.4, Eq. 1-2 of §2.4, Table 2 features, the §2.3 PRC filters)."""
import os
import pandas as pd
import pytest

from cyberrisk.extract import Sentence, direct_hit, indirect_hits, extract, split_sentences
from cyberrisk.roots import Rooter, tokens, build_vocabulary, vectorize, always_capitalised
from cyberrisk.measure import cosine, jaccard, cybersecurity_risk
from cyberrisk.language import disclosure_features
from cyberrisk.training import cyberattacks

LM = os.path.join(os.path.dirname(__file__), "..", "..", "AI_Innovation_Atlas_data", "02_data_sources",
                  "other_public", "loughran_mcdonald_dictionary", "Loughran-McDonald_MasterDictionary_1993-2025.csv")


# --- Appendix A rules ---------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("A cyber attack on our systems.", True),                       # attack + cyber
    ("A terrorist attack on our systems.", False),                  # irrelevant hit blocks
    ("Threats to our networks are growing.", True),                 # prefix: threats
    ("Competitors threaten our margins.", False),                   # threaten is an irrelevant hit
    ("Computer viruses may infect us.", True),                      # computer + viruses
    ("Breaches of these covenants would be costly.", False),        # breaches + covenant
    ("Breaches could expose customer data.", True),                 # breaches alone
    ("Phishing is common.", True),                                  # standalone keyword
    ("We may face unauthorized access to systems.", True),
    ("Attacks occur.", False),                                      # attack without a relevant hit
    ("Malicious software could harm us.", True),
    ("Malicious product sales claims are software issues.", False),  # irrelevant: product sales
])
def test_direct_rules(text, expected):
    assert direct_hit(text) is expected


def test_indirect_categories():
    assert indirect_hits("The Company's business stores confidential information.") == ["Company Business"]
    assert "Legal Consequences" in indirect_hits("This may lead to litigation.")
    assert "Economic Consequences" in indirect_hits("It would harm our reputation.")
    assert "Internal Consequences" in indirect_hits("Theft of intellectual property may occur.")
    assert indirect_hits("The weather was fine.") == []


def test_window_stops_at_title_and_at_ten_sentences():
    direct = Sentence("Hackers may target us.")
    ind = Sentence("Our reputation could be harmed.")
    plain = Sentence("Nothing here.")
    # a title sentence stops the search
    caps = extract([direct, ind, Sentence("Next risk factor title.", is_title=True), ind])
    assert [c.index for c in caps] == [0, 1]
    # without a title the search runs 10 sentences, not 11
    caps = extract([direct] + [plain] * 9 + [ind, ind])
    assert [c.index for c in caps] == [0, 10]
    # a direct title sentence is itself captured and starts a window
    caps = extract([Sentence("Cyberattacks could hurt us.", is_title=True), ind])
    assert [c.index for c in caps] == [0, 1] and caps[0].direct and caps[0].is_title


def test_sentence_splitter_keeps_abbreviations():
    s = split_sentences("Apple Inc. sells in the U.S. and Europe. It uses e.g. encryption. Risks remain.")
    assert s == ["Apple Inc. sells in the U.S. and Europe.", "It uses e.g. encryption.", "Risks remain."]


# --- §2.4 word roots and vectors -------------------------------------------------------------
def test_roots_vocabulary_and_vectors():
    r = Rooter()
    docs = ["Hackers attacked our systems and networks."] * 10 + ["The systems of Verizon were breached."] * 10
    cap = always_capitalised(docs)
    assert "verizon" in cap and "hackers" not in cap
    vocab, counts = build_vocabulary(docs, r, cap)
    assert "system" in vocab and "network" in vocab and "hacker" in vocab
    assert "verizon" not in vocab and "the" not in vocab and "our" not in vocab
    v = vectorize(docs[0], vocab, r, cap)
    assert v == {"hacker": 1, "attack": 1, "system": 1, "network": 1}
    assert tokens("third-party company's data") == ["company", "data"]     # compound word dropped


def test_min_frequency_filter():
    r = Rooter()
    docs = ["hackers attacked"] * 9 + ["systems failed"] * 10
    vocab, _ = build_vocabulary(docs, r, min_freq=10)
    assert vocab == ["fail", "system"]


def test_frequency_threshold_applies_to_words_before_roots():
    """§2.4 excludes 'words with a frequency less than 10' and only then stores word roots: two
    surface forms of 6 and 5 do not make a root of 11."""
    r = Rooter()
    docs = ["hacked"] * 6 + ["hacks"] * 5 + ["systems"] * 10
    vocab, counts = build_vocabulary(docs, r, min_freq=10)
    assert vocab == ["system"] and "hack" not in counts
    assert vectorize("hacked systems", vocab, r) == {"system": 1}


def test_similarities():
    a, b = {"x": 1, "y": 2}, {"y": 2, "z": 1}
    assert abs(cosine(a, b) - 4 / 5) < 1e-12 and abs(jaccard(a, b) - 1 / 3) < 1e-12
    assert cosine({}, b) == 0.0 and jaccard(a, {}) == 0.0


def test_measure_windows_and_self_exclusion():
    disc = pd.DataFrame({
        "firm": ["A", "B", "C", "C"],
        "filing_date": pd.to_datetime(["2012-02-01", "2012-05-01", "2011-06-01", "2013-03-01"]),
        "fiscal_year": [2011, 2011, 2010, 2012],
        "vector": [{"x": 1}, {"x": 1, "y": 1}, {"y": 1}, {"x": 1}],
    })
    attacks = pd.DataFrame({"firm": ["A", "C"], "attack_date": pd.to_datetime(["2012-01-15", "2011-09-01"])})
    out = cybersecurity_risk(disc, attacks).set_index(["firm", "fiscal_year"])
    # B at 2012-05-01: attacked in the past year = A (2012-01) and C (2011-09); A's vector {x} and
    # C's 2011 vector {y}; B = {x, y}: cos = mean(1/sqrt2, 1/sqrt2)
    assert abs(out.loc[("B", 2011), "cyber_risk"] - 2 ** -0.5) < 1e-9 and out.loc[("B", 2011), "n_train"] == 2
    # A does not compare with itself: only C remains -> cos({x},{y}) = 0
    assert out.loc[("A", 2011), "cyber_risk"] == 0.0 and out.loc[("A", 2011), "n_train"] == 1
    # C in 2013: no attack in the 1-year window -> 2-year window picks A (2012-01)
    assert out.loc[("C", 2012), "window_years"] == 2 and out.loc[("C", 2012), "cyber_risk"] == 1.0
    # zero vector -> zero score
    disc2 = disc.copy(); disc2["vector"] = [{"x": 1}, {}, {"y": 1}, {"x": 1}]
    assert cybersecurity_risk(disc2, attacks).set_index("firm").loc["B", "cyber_risk"] == 0.0


# --- Table 2 features ----------------------------------------------------------------------
def test_disclosure_features():
    if not os.path.exists(LM):
        pytest.skip("LM dictionary not on disk")
    from cyberrisk.language import lm_wordlists
    lists = lm_wordlists(LM)
    from cyberrisk.extract import Captured
    caps = [Captured(0, "Hackers may cause losses and litigation; our insurance may be insufficient to cover all claims.", False, True)]
    f = disclosure_features(caps, 50, lists)
    assert f["crd_sentences"] == 1 and f["crd_sentences_ratio"] == 0.02
    assert f["negative_words"] > 0 and f["litigious_words"] > 0
    assert f["mentions_insurance"] == 1 and f["cyber_insurance"] == 1 and f["cyber_insurance_partial"] == 1
    # the ratios divide by the post-exclusion word count (the authors' totalWordsadj)
    assert f["n_words_adj"] < f["n_words"] and f["negative_words"] > f["negative_words_raw"]
    assert f["precise_words"] <= 0                       # minus the LM uncertainty ratio


# --- §2.3 PRC filters ----------------------------------------------------------------------
def test_prc_filters():
    prc = pd.DataFrame({
        "attack_date": pd.to_datetime(["2010-01-01", "2010-02-01", "2010-03-01", "2019-01-01"]),
        "company": ["A", "B", "C", "D"], "breach_type": ["HACK", "PORT", "HACK", "HACK"],
        "org_type": ["BSR", "BSF", "GOV", "BSO"], "records": [1, 1, 1, 1], "description": [""] * 4,
        "prc_id": ["1", "2", "3", "4"]})
    out = cyberattacks(prc)
    assert out["company"].tolist() == ["A"]      # B: not hacking; C: government; D: after 2018


def test_empty_training_disclosure_is_not_training_text():
    """§2.3: attacked firms enter the training sample only 'with available cybersecurity risk
    disclosures'; a firm whose 10-K has no cyber sentence must not add a zero to the average."""
    import pandas as pd
    from cyberrisk.measure import cybersecurity_risk
    d = pd.DataFrame({"firm": ["i", "a", "b"],
                      "filing_date": pd.to_datetime(["2016-03-01", "2016-01-15", "2016-01-20"]),
                      "fiscal_year": 2015,
                      "vector": [{"attack": 2, "system": 1}, {"attack": 2, "system": 1}, {}]})
    att = pd.DataFrame({"firm": ["a", "b"], "attack_date": pd.to_datetime(["2015-10-01", "2015-11-01"])})
    r = cybersecurity_risk(d, att).set_index("firm")
    assert r.loc["i", "n_train"] == 1 and abs(r.loc["i", "cyber_risk"] - 1.0) < 1e-12


def test_item_1a_skips_table_of_contents_and_uses_risk_factors_heading():
    """Weyerhaeuser 2016-2018: 'Item 1A' appears only in the table of contents (risk-factor lines
    with page numbers); the section itself is headed 'RISK FACTORS'."""
    from cyberrisk.edgar import item_1a
    from cyberrisk.extract import Sentence
    toc = ["Item 1A.", "Risk Factors", "• CYBERSECURITY RISKS", "30", "• STOCK PRICE", "31", "Item 1B.", "Unresolved", "32"]
    body = ["RISK FACTORS"] + [f"Risk sentence number {k} about our business." for k in range(40)] + ["UNRESOLVED STAFF COMMENTS"]
    span, by_ref = item_1a([Sentence(t) for t in toc + body])
    assert len(span) == 40 and not by_ref


def test_search_stops_at_the_title_after_a_heading_hit():
    """Weyerhaeuser FY2015: a direct-hit category heading ("CYBERSECURITY RISKS") followed by the
    factor's own bold title.  Stopping at that title reproduces Table 1 (0.033 vs the paper's
    0.036); searching past it gives 0.457.  So the heading is captured alone."""
    from cyberrisk.extract import Sentence, extract
    s = [Sentence("CYBERSECURITY RISKS", True),
         Sentence("We rely on information technology to support our operations.", True),
         Sentence("We and our service providers employ what we believe are adequate security measures.")]
    assert [c.index for c in extract(s)] == [0]


def test_word_ratios_undefined_without_disclosure():
    """Negative / precise / litigious words are ratios to the disclosure's words (Table 2 note);
    with no disclosure they are undefined (NaN), not zero -- zeros for the ~40% of firm-years
    without a disclosure manufacture a correlation (0.84 vs the paper's 0.03 for negative words)."""
    import math
    f = disclosure_features([], 120, {"Negative": {"loss"}, "Strong_Modal": {"must"}, "Litigious": {"claim"}, "Uncertainty": {"may"}})
    assert f["crd_sentences"] == 0 and math.isnan(f["negative_words"]) and math.isnan(f["litigious_words"])


def test_stub_item_1a_is_dropped_on_every_path():
    """'Not Applicable' / 'None' / 'Omitted' Item 1A sections are excluded (paper: firms without
    Item 1A are dropped), including when the section is found through the 'Risk Factors' heading
    fallback -- that path used to skip the test (audit 2026-09-19)."""
    from cyberrisk.edgar import item_1a
    from cyberrisk.extract import Sentence
    for body in (["Not Applicable Item 1B."], ["None."], ["Omitted as permitted by Instruction J to Form 10-K."]):
        sents = [Sentence("RISK FACTORS")] + [Sentence(t) for t in body] + [Sentence("PROPERTIES")]
        assert item_1a(sents) == ([], False), body
        sents = [Sentence("Item 1A.")] + [Sentence(t) for t in body] + [Sentence("Item 1B.")]
        assert item_1a(sents) == ([], False), body


def test_cyber_insurance_needs_partial_cover_in_the_insurance_sentence():
    """Appendix B: firms 'explicitly state that such insurance only partially covers them'.  A
    partial-cover phrase elsewhere in the disclosure, or 'not limited to', does not count.  This is
    `cyber_insurance_partial`; `cyber_insurance` itself follows the authors' code, which only looks
    for the word "insurance" (EVALUATION.md 13.2)."""
    from cyberrisk.extract import Captured
    lists = {"Negative": set(), "Strong_Modal": set(), "Litigious": set(), "Uncertainty": set()}
    f = lambda *ts: disclosure_features([Captured(i, t, False, True, []) for i, t in enumerate(ts)], 10, lists)
    assert f("We maintain insurance coverage.", "Attacks including but not limited to phishing.")["cyber_insurance_partial"] == 0
    assert f("We maintain cyber insurance.", "Our security measures may be insufficient.")["cyber_insurance_partial"] == 0
    assert f("Such insurance coverage may be insufficient to cover all losses.")["cyber_insurance_partial"] == 1   # Apple FY2017
    assert f("The potential costs could exceed the insurance coverage we maintain.")["cyber_insurance_partial"] == 1  # Verizon FY2017
    assert f("We maintain cyber insurance.")["mentions_insurance"] == 1
    assert f("We maintain cyber insurance.")["cyber_insurance"] == 1      # the authors' own rule
    assert f("Hackers attacked our systems.")["cyber_insurance"] == 0
