"""Section 3.2 / Table 2 of the paper: quantitative features of the cybersecurity risk disclosure
language, and the cyber-insurance dummy.

  CRD sentences (#)      number of cybersecurity risk disclosure sentences in Item 1A
  CRD sentences (ratio)  that number / number of sentences in Item 1A
  Negative / Precise / Litigious words (ratio)  Loughran-McDonald (2011) word-list counts / total
                         words in the disclosure.  LM publish Negative and Litigious lists; the
                         paper does not say which LM list is its "precise" list -- Strong_Modal
                         (the complement of the "vague talker" qualifying words the paper cites,
                         Dzielinski, Wagner and Zeckhauser 2017) is used and flagged in EVALUATION.md.
  Cyber insurance        = 1 when a disclosure sentence mentions insurance AND that same sentence says
                         the policy only partially covers cyber claims.  The paper read every such
                         disclosure by hand; the phrase list below stands in for that reading.
"""
import re

import pandas as pd

from .roots import tokens

PRECISE_LIST = "Strong_Modal"
# statements that the insurance covers the firm only partially.  Bare "limited" is not one of them
# ("including but not limited to"); the audit of 2026-09-19 found it and a whole-disclosure match
# coding 1 for firms whose insurance sentence says nothing about partial cover.
_PARTIAL = re.compile(r"insufficient|not (be )?(sufficient|adequate|enough)|may not (fully |adequately )?cover|"
                      r"could exceed|may exceed|in excess of|not cover all|inadequate|only partial|"
                      r"limited (coverage|in (scope|amount))|coverage (is |may be )?limited|coverage limits?|"
                      r"subject to (a )?deductible|may not be available|exceed(s|ed)? (our|the) (insurance )?coverage",
                      re.I)
_INSURANCE = re.compile(r"\binsurance", re.I)


def lm_wordlists(master_dictionary_csv):
    """{'Negative': set, 'Litigious': set, 'Strong_Modal': set, ...} from the LM master dictionary."""
    d = pd.read_csv(master_dictionary_csv, usecols=["Word", "Negative", "Positive", "Uncertainty",
                                                    "Litigious", "Strong_Modal", "Weak_Modal"])
    return {c: set(d.loc[d[c] > 0, "Word"].str.lower()) for c in d.columns if c != "Word"}


def disclosure_features(captured, n_item1a_sentences, lists):
    """captured: list of Captured sentences; lists: lm_wordlists().  One row of Table 2 inputs."""
    text = " ".join(c.text for c in captured)
    words = tokens(text)
    n = len(words)
    # a ratio "to total words in cybersecurity risk disclosures" is undefined without a disclosure
    ratio = lambda name: sum(1 for w in words if w in lists[name]) / n if n else float("nan")
    ins_sentences = [c.text for c in captured if _INSURANCE.search(c.text)]
    mentions_ins = bool(ins_sentences)
    # "explicitly state that such insurance only partially covers them" (Appendix B): the
    # partial-cover statement must be made in a sentence about the insurance
    partial = any(_PARTIAL.search(t) for t in ins_sentences)
    return {
        "crd_sentences": len(captured),
        "crd_sentences_ratio": len(captured) / n_item1a_sentences if n_item1a_sentences else 0.0,
        "negative_words": ratio("Negative"),
        "precise_words": ratio(PRECISE_LIST),
        "litigious_words": ratio("Litigious"),
        "mentions_insurance": int(mentions_ins),
        "cyber_insurance": int(partial),
        "n_words": len(words),
    }
