"""Appendix A.1 of the paper: extract the cybersecurity-risk discussion from "Item 1A Risk Factors".

Algorithm (paper, App. A.1):
  1. A sentence with a DIRECT hit (keywords.DIRECT) is captured.
  2. After every direct sentence, the following sentences are searched for INDIRECT hits
     (keywords.INDIRECT).  The search stops at the next sentence that is a risk-factor title
     (bold or italics); if no such sentence is found it stops after 10 sentences.
  3. Matching is case-insensitive and by prefix at a word boundary.

Input: a list of Sentence(text, is_title).  Output: the captured sentences with their types.
"""
import re
from dataclasses import dataclass, field

from . import keywords as K

INDIRECT_WINDOW = 10


@dataclass
class Sentence:
    text: str
    is_title: bool = False


@dataclass
class Captured:
    index: int
    text: str
    is_title: bool
    direct: bool
    indirect: list = field(default_factory=list)   # categories, in keywords.INDIRECT_ORDER

    @property
    def sentence_type(self):
        if self.direct:
            return "Direct"
        return "Indirect: " + self.indirect[0] if self.indirect else "Indirect"


def _term_regex(term):
    # prefix match at a word boundary; spaces in phrases tolerate any whitespace / hyphen
    parts = [re.escape(p) for p in term.split()]
    return r"\b" + r"[\s\-]+".join(parts)


def _compile(rules):
    out = []
    for kws, rel, irr in rules:
        out.append((
            re.compile("|".join(_term_regex(t) for t in kws), re.I),
            re.compile("|".join(_term_regex(t) for t in rel), re.I) if rel else None,
            re.compile("|".join(_term_regex(t) for t in irr), re.I) if irr else None,
        ))
    return out


_DIRECT = _compile(K.DIRECT)
_INDIRECT = {cat: _compile(rules) for cat, rules in K.INDIRECT.items()}


def _fires(compiled, text):
    for kw, rel, irr in compiled:
        if not kw.search(text):
            continue
        if rel is not None and not rel.search(text):
            continue
        if irr is not None and irr.search(text):
            continue
        return True
    return False


def direct_hit(text):
    return _fires(_DIRECT, text)


def indirect_hits(text):
    return [cat for cat in K.INDIRECT_ORDER if _fires(_INDIRECT[cat], text)]


# --- sentence splitting -------------------------------------------------------------------
_ABBREV = r"(?:Inc|Corp|Co|Ltd|L\.P|U\.S|U\.K|e\.g|i\.e|No|Nos|Mr|Ms|Mrs|Dr|vs|St|et al|approx|Jr|Sr|LLC|" \
          r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|[A-Z])"
_SPLIT = re.compile(r"(?<=[.!?])[\"'”’)]?\s+(?=[\"'“‘(]?[A-Z0-9])")


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    out, start = [], 0
    for m in _SPLIT.finditer(text):
        before = text[start:m.start() + 1]
        if re.search(r"\b" + _ABBREV + r"\.$", before):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
    out.append(text[start:].strip())
    return [s for s in out if s]


# --- the extraction algorithm -------------------------------------------------------------
def extract(sentences, window=INDIRECT_WINDOW):
    """Return the list of Captured sentences, in document order."""
    captured = {}
    for i, s in enumerate(sentences):
        if not direct_hit(s.text):
            continue
        c = captured.get(i) or Captured(i, s.text, s.is_title, True)
        c.direct = True
        captured[i] = c
        # the search stops at the next bold/italic sentence even when the direct hit is itself a
        # heading followed by the factor's own title: Weyerhaeuser FY2015 ("CYBERSECURITY RISKS"
        # then a bold title) scores 0.033 this way vs 0.036 in Table 1; searching past the title
        # gives 0.457 (experiment of 2026-09-19, EVALUATION.md)
        for j in range(i + 1, min(i + window, len(sentences) - 1) + 1):
            if sentences[j].is_title:
                break
            cats = indirect_hits(sentences[j].text)
            if not cats:
                continue
            cj = captured.get(j) or Captured(j, sentences[j].text, sentences[j].is_title, False)
            for cat in cats:
                if cat not in cj.indirect:
                    cj.indirect.append(cat)
            cj.indirect.sort(key=K.INDIRECT_ORDER.index)
            captured[j] = cj
    return [captured[k] for k in sorted(captured)]


def disclosure_text(sentences, window=INDIRECT_WINDOW, captured=None):
    """The firm's cybersecurity risk disclosure = the captured sentences, in document order."""
    return " ".join(c.text for c in (captured if captured is not None else extract(sentences, window)))
