"""Section 2.2 of the paper: 10-K filings from SEC EDGAR and the "Item 1A Risk Factors" section.

The paper downloads all 10-K, 10-K405 and 10-KSB40 filings (no amendments), extracts fiscal year
and CIK, extracts Item 1A, drops filings without an Item 1A (smaller reporting companies) and
filings that incorporate Item 1A by reference (as Hoberg and Phillips 2010).

Risk-factor titles are set in bold or italics (App. A.1); they bound the indirect-keyword search.
An HTML filing therefore yields paragraphs with a `is_title` flag; a plain-text filing cannot,
and the extraction then falls back to the paper's 10-sentence window.
"""
import json
import os
import re
import time
from html import unescape

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from .extract import split_sentences, Sentence

USER_AGENT = os.environ.get("EDGAR_USER_AGENT", "academic replication contact@example.edu")
FORMS = ("10-K", "10-K405", "10-KSB40")          # paper §2.2; amendments (/A) excluded
# OBSERVED in the EDGAR index used here (Atlas form subset) for filing years 2004-2020: of the three
# forms only 10-K occurs (139,788 filings); 10-K405 last appears in 2002.  10-KSB40 is not in this
# index at all, so its absence from the sample years is not measured here.
_BLOCK = {"p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "table", "ul", "ol",
          "blockquote", "center", "pre", "hr", "title", "body"}
_STYLED_TAGS = {"b", "strong", "i", "em"}
_STYLED_CSS = re.compile(r"font-weight\s*:\s*(bold|[6-9]00)|font-style\s*:\s*italic", re.I)


# --- fetching ------------------------------------------------------------------------------
def fetch(url, cache_dir=None, sleep=0.12):
    """GET with the SEC-required User-Agent; EDGAR fair-access limit is 10 requests/second."""
    if cache_dir:
        path = os.path.join(cache_dir, re.sub(r"[^A-Za-z0-9._-]", "_", url.split("://", 1)[-1]))
        if os.path.exists(path):
            return open(path, "rb").read()
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    data = r.content
    time.sleep(sleep)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        open(path, "wb").write(data)
    return data


def fetch_main_document(url, sleep=0.12, max_bytes=60_000_000):
    """Stream a complete-submission .txt and stop at the end of its FIRST <DOCUMENT> (the 10-K
    itself), so exhibits and XBRL are never downloaded.  Returns the bytes read."""
    import requests
    got = bytearray()
    with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=120) as r:
        r.raise_for_status()
        for chunk in r.iter_content(1 << 16):
            got += chunk
            if b"</DOCUMENT>" in got or len(got) > max_bytes:
                break
    time.sleep(sleep)
    return bytes(got)


def compustat_fyear(period):
    """Compustat fiscal-year convention (the paper links on Compustat fyear): a fiscal year that
    ends in January-May belongs to the previous year.  period = 'YYYYMMDD'."""
    if not period or len(period) < 6:
        return None
    y, m = int(period[:4]), int(period[4:6])
    return y if m >= 6 else y - 1


_EXCHANGE = re.compile(r"new york stock exchange|\bnyse\b|nasdaq|american stock exchange|\bamex\b", re.I)


def listed_on_exchange(doc, head_chars=40_000):
    """True when the 10-K cover page names a national exchange (NYSE, NASDAQ, AMEX).  A proxy for
    the paper's universe of U.S.-listed (CRSP) firms, which cannot be taken from CRSP here."""
    head = doc[:head_chars * 6]
    text = re.sub(r"<[^>]+>", " ", head)
    text = unescape(re.sub(r"\s+", " ", text))[:head_chars]
    return bool(_EXCHANGE.search(text))


def filings_from_index(index_csv, forms=FORMS, years=range(2006, 2020)):
    """Rows of the EDGAR full index (form, company_name, cik, date_filed, file_name) for the
    forms and filing years used by the paper (fiscal years 2007-2018 are filed 2007-2019; 2006
    filings are kept for the 1-year-prior training window)."""
    import csv
    years = set(years)
    with open(index_csv, newline="") as f:
        for r in csv.DictReader(f):
            if r["form"] in forms and int(r["date_filed"][:4]) in years:
                yield r


def submission_header(accession_txt):
    """CIK, form, period of report (fiscal year end) and filing date from the SEC header of a
    complete-submission .txt file."""
    head = accession_txt[:20000].decode("latin-1") if isinstance(accession_txt, bytes) else accession_txt[:20000]
    def grab(k):
        m = re.search(k + r":\s*(\S+)", head)
        return m.group(1) if m else None
    return {"cik": grab("CENTRAL INDEX KEY"), "form": grab("CONFORMED SUBMISSION TYPE"),
            "period": grab("CONFORMED PERIOD OF REPORT"), "filed": grab("FILED AS OF DATE")}


def main_document(complete_submission):
    """The 10-K document (first <DOCUMENT> whose <TYPE> is a 10-K form) of a complete submission."""
    txt = complete_submission.decode("latin-1") if isinstance(complete_submission, bytes) else complete_submission
    for m in re.finditer(r"<DOCUMENT>(.*?)</DOCUMENT>", txt, re.S):
        doc = m.group(1)
        t = re.search(r"<TYPE>([^\s<]+)", doc)
        if t and t.group(1).upper().startswith("10-K"):
            body = re.search(r"<TEXT>(.*)</TEXT>", doc, re.S)
            return body.group(1) if body else doc
    return txt


# --- HTML -> paragraphs with a title flag ----------------------------------------------------
def _is_styled(tag):
    if tag.name in _STYLED_TAGS:
        return True
    style = tag.get("style") if isinstance(tag, Tag) else None
    return bool(style and _STYLED_CSS.search(style))


class _Text:
    """A text node on the walk stack (a leaf: no children)."""
    __slots__ = ("s", "children")

    def __init__(self, s):
        self.s, self.children = str(s), ()


def html_paragraphs(html):
    """Yield (text, is_title) paragraphs.  A paragraph is a title when essentially all of its
    text is bold or italic (the run-in bold sentence that opens a paragraph is handled at the
    sentence level by html_sentences)."""
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "head"]):
        t.decompose()
    runs, paras = [], []

    def flush():
        if runs:
            paras.append(list(runs))
            runs.clear()

    # depth-first walk with an explicit stack (some filings nest tags deeper than Python's
    # recursion limit); same visiting order as the recursive walk: flush, children, flush
    stack = [(soup, False)]
    while stack:
        node, styled = stack.pop()
        if node is None:
            flush()
            continue
        for child in reversed(list(node.children)):
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                stack.append((_Text(child), styled))
            elif isinstance(child, Tag):
                block = child.name in _BLOCK
                if block:
                    stack.append((None, None))
                stack.append((child, styled or _is_styled(child)))
                if block:
                    stack.append((None, None))
        if isinstance(node, _Text):
            s = node.s.replace("\xa0", " ")
            if s.strip():
                runs.append((s, styled))
            elif s and runs:
                runs.append((" ", styled))
    flush()
    return [_runs_to_paragraph(r) for r in paras]


def _runs_to_paragraph(runs):
    text = re.sub(r"\s+", " ", "".join(t for t, _ in runs)).strip()
    return text, runs


def html_sentences(html):
    """Sentences of an HTML document with the bold/italic title flag resolved per sentence."""
    out = []
    for text, runs in html_paragraphs(html):
        if not text:
            continue
        # character-level style mask aligned with the whitespace-collapsed text
        raw = "".join(t for t, _ in runs)
        mask = "".join(("1" if styled else "0") * len(t) for t, styled in runs)
        collapsed, cmask, prev_space = [], [], False
        for ch, m in zip(raw, mask):
            if ch.isspace():
                if prev_space:
                    continue
                prev_space = True
                collapsed.append(" "); cmask.append(m)
            else:
                prev_space = False
                collapsed.append(ch); cmask.append(m)
        ctext = "".join(collapsed).strip()
        cm = "".join(cmask)[len("".join(collapsed)) - len("".join(collapsed).lstrip()):]
        pos = 0
        for s in split_sentences(ctext):
            i = ctext.find(s, pos)
            if i < 0:
                out.append(Sentence(s, False)); continue
            seg = cm[i:i + len(s)]
            letters = [seg[k] for k, ch in enumerate(s) if not ch.isspace()]
            styled_share = (sum(1 for k in letters if k == "1") / len(letters)) if letters else 0.0
            out.append(Sentence(s, styled_share >= 0.9))
            pos = i + len(s)
    return out


def text_sentences(text):
    """Sentences of a plain-text Item 1A (e.g. EDGAR-CORPUS `section_1A`); no title flags."""
    return [Sentence(s, False) for s in split_sentences(text)]


# --- Item 1A ---------------------------------------------------------------------------------
_ITEM_1A = re.compile(r"^\s*item\s*1a\b[\s.:\-—–]*(risk\s+factors)?", re.I)
_ITEM_END = re.compile(r"^\s*item\s*(1b|2)\b", re.I)
_BY_REF = re.compile(r"incorporated (herein )?by reference", re.I)
_NOT_PROVIDED = re.compile(r"not applicable|not required|smaller reporting compan|^\s*(none|omitted)\b", re.I)
_RF_TITLE = re.compile(r"^\s*risk\s+factors\.?\s*$", re.I)
_RF_END = re.compile(r"^\s*(item\s*(1b|2)\b|unresolved\s+staff\s+comments\.?\s*$|properties\.?\s*$)", re.I)
MIN_SPAN = 15


_PAGE_NO = re.compile(r"^\s*(page\s*)?\d{1,3}\s*$", re.I)


def _is_toc(span):
    """A table-of-contents span: a quarter or more of its 'sentences' are bare page numbers."""
    return len(span) > 0 and sum(bool(_PAGE_NO.match(s.text)) for s in span) >= 0.25 * len(span)


def is_stub(span):
    """An Item 1A that provides no risk factors: "Not applicable", "None", "Omitted", "As a smaller
    reporting company we are not required ...".  The paper drops these firms (Regulation S-K
    Item 10); it does not score them zero."""
    words = sum(len(s.text.split()) for s in span)
    return bool(span) and words < 250 and any(_NOT_PROVIDED.search(s.text) for s in span)


def _longest_span(sentences, start_re, end_re):
    best, best_len = None, 0
    for i, s in enumerate(sentences):
        if not start_re.match(s.text):
            continue
        j = next((k for k in range(i + 1, len(sentences)) if end_re.match(sentences[k].text)), len(sentences))
        if _is_toc(sentences[i + 1:j]):
            continue
        length = sum(len(x.text) for x in sentences[i + 1:j])
        if length > best_len:
            best, best_len = (i + 1, j), length
    return best


def item_1a(sentences):
    """The Item 1A span: among all (Item 1A heading .. next Item 1B/2 heading) candidates, the
    longest one (the table-of-contents entry is a short span).  Returns (sentences, by_reference).

    Some filers put "Item 1A" only in the table of contents and head the section itself
    "RISK FACTORS" (e.g. Weyerhaeuser 2017-2018).  When the Item 1A span is shorter than
    MIN_SPAN sentences, a stand-alone "Risk Factors" heading ending at Item 1B / Unresolved Staff
    Comments / Properties is used instead if it is longer."""
    best = _longest_span(sentences, _ITEM_1A, _ITEM_END)
    span = sentences[best[0]:best[1]] if best else []
    if is_stub(span):
        return [], False
    if len(span) < MIN_SPAN:
        alt = _longest_span(sentences, _RF_TITLE, _RF_END)
        if alt and alt[1] - alt[0] > len(span):
            span = sentences[alt[0]:alt[1]]
    # the stub test applies to whichever span was chosen (it used to be skipped on the "Risk
    # Factors" fallback path, so stubs were scored 0: 14 of them in the scored sample and 206 in
    # the whole 2026-09-19 run -- re-measured 2026-09-20 on the pre-fix output)
    if not span or is_stub(span):
        return [], False
    words = sum(len(s.text.split()) for s in span)
    by_ref = words < 300 and any(_BY_REF.search(s.text) for s in span)
    return span, by_ref


def item_1a_from_html(html):
    return item_1a(html_sentences(html))
