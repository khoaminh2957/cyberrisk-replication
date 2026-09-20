"""Section 2.4 of the paper: from cybersecurity risk disclosures to word-root count vectors.

Paper: "After excluding certain types of words (e.g., pronouns, conjunctions, stop words, common
words and/or articles, compound words, words that refer to geographic locations or names, and
words with a frequency less than 10), we store the text in separate word vectors using word
roots rather than actual words. We identify word roots using a web-crawling algorithm and
Merriam-Webster online."  The resulting universe in the paper is 3,210 roots.

Word roots: Merriam-Webster blocks scripted access to its website (HTTP 403 behind Cloudflare,
measured 2026-09-09).  The root is therefore the WordNet lemma (a dictionary headword, the same
object) unless a Merriam-Webster API key is supplied in MW_API_KEY, in which case the headword
returned by the official dictionary API is used and cached.
"""
import json
import os
import re
from collections import Counter

MIN_FREQ = 10
_TOKEN = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

# pronouns, conjunctions, articles, prepositions, auxiliaries (the NLTK English list) plus the
# modal / filler words a 10-K uses everywhere.  Kept deliberately short: the paper's top-20 words
# include "result", "include", "system" -- generic words are NOT removed.
STOP_WORDS = set("""i me my myself we our ours ourselves you your yours yourself yourselves he him his
himself she her hers herself it its itself they them their theirs themselves what which who whom this
that these those am is are was were be been being have has had having do does did doing a an the and
but if or because as until while of at by for with about against between into through during before
after above below to from up down in out on off over under again further then once here there when
where why how all any both each few more most other some such no nor not only own same so than too
very s t can will just don should now d ll m o re ve y ain aren couldn didn doesn hadn hasn haven isn
ma mightn mustn needn shan shouldn wasn weren won wouldn
may might could would shall must also etc per upon among via within without whether either neither
whereas thereof therein hereby herein thereto hereto""".split())

# words that refer to geographic locations or names (paper: excluded); extend as the corpus
# dictates -- this list only carries what the appendix examples and the top-20 words need
GEOGRAPHIC = {
    "u.s", "us", "usa", "america", "american", "americas", "europe", "european", "asia", "asian",
    "china", "chinese", "japan", "japanese", "canada", "canadian", "mexico", "india", "germany",
    "france", "uk", "britain", "british", "australia", "california", "texas", "york", "delaware",
    "washington", "florida", "illinois", "ohio", "nevada", "virginia", "georgia", "carolina",
    "boston", "chicago", "london", "hong", "kong", "singapore", "brazil", "russia", "korea",
    "israel", "ireland", "netherlands", "switzerland", "taiwan", "africa", "pacific", "atlantic",
}


def tokens(text):
    """Lower-case alphabetic tokens; possessives stripped; hyphenated compound words dropped."""
    out = []
    for t in _TOKEN.findall(text):
        t = re.sub(r"['’]s$", "", t).strip("'’").lower()
        if "-" in t or not t:
            continue
        out.append(t)
    return out


class Rooter:
    """word -> root.  WordNet lemma (noun, then verb, then adjective) or Merriam-Webster headword."""

    def __init__(self, cache_path=None):
        from nltk.stem import WordNetLemmatizer
        self._wn = WordNetLemmatizer()
        self._key = os.environ.get("MW_API_KEY")
        self._cache_path = cache_path
        self._cache = json.load(open(cache_path)) if cache_path and os.path.exists(cache_path) else {}

    def root(self, word):
        w = word.lower()
        if w in self._cache:
            return self._cache[w]
        r = self._merriam_webster(w) if self._key else None
        if r is None:
            r = self._wn.lemmatize(w, "n")
            if r == w:
                r = self._wn.lemmatize(w, "v")
            if r == w:
                r = self._wn.lemmatize(w, "a")
        self._cache[w] = r
        return r

    def _merriam_webster(self, w):
        import requests
        url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{w}?key={self._key}"
        try:
            data = requests.get(url, timeout=30).json()
        except Exception:
            return None
        for entry in data:
            if isinstance(entry, dict) and "hwi" in entry:
                hw = entry["hwi"]["hw"].replace("*", "")
                return hw.lower()
        return None

    def save(self):
        if self._cache_path:
            json.dump(self._cache, open(self._cache_path, "w"))


def is_excluded(word):
    return word in STOP_WORDS or word in GEOGRAPHIC or len(word) < 2


class Vocabulary(list):
    """The sorted root vocabulary (a plain list for every caller), carrying the set of surface
    words that passed the frequency threshold."""
    words = None


def build_vocabulary(disclosures, rooter, capitalised=None, min_freq=MIN_FREQ):
    """disclosures: iterable of disclosure texts.  Returns (vocabulary, root_counts).

    Paper §2.4: "After excluding certain types of words (... words with a frequency less than 10),
    we store the text in separate word vectors using word roots".  The threshold therefore applies
    to WORDS before they are reduced to roots (it was applied to roots until the 2026-09-19 audit):
    "hacked" (6) + "hacks" (5) no longer make a root "hack" of 11.
    Names are removed as tokens that only ever occur capitalised in the corpus (when
    `capitalised` -- a set of such tokens from `always_capitalised` -- is given)."""
    word_counts = Counter()
    for text in disclosures:
        for t in tokens(text):
            if is_excluded(t) or (capitalised and t in capitalised):
                continue
            word_counts[t] += 1
    kept = {w for w, n in word_counts.items() if n >= min_freq}
    counts = Counter()
    for w in kept:
        counts[rooter.root(w)] += word_counts[w]
    vocab = Vocabulary(sorted(r for r in counts if not is_excluded(r)))
    vocab.words = frozenset(kept)
    return vocab, counts


def always_capitalised(disclosures):
    """Tokens that never appear in lower case anywhere in the corpus (names: Verizon, Abbott...).
    The first word of a sentence is capitalised by convention and is not evidence of a name."""
    from .extract import split_sentences
    lower, cap = set(), set()
    for text in disclosures:
        for sent in split_sentences(text):
            for i, t in enumerate(_TOKEN.findall(sent)):
                t = re.sub(r"['’]s$", "", t)
                if t[:1].isupper():
                    if i > 0:
                        cap.add(t.lower())
                else:
                    lower.add(t.lower())
    return cap - lower


def vectorize(text, vocab, rooter, capitalised=None):
    """Counts of each vocabulary root in one disclosure, as a dict root -> count."""
    vset = set(vocab)
    words = getattr(vocab, "words", None)          # surface words kept by build_vocabulary
    v = Counter()
    for t in tokens(text):
        if is_excluded(t) or (capitalised and t in capitalised):
            continue
        if words is not None and t not in words:
            continue
        r = rooter.root(t)
        if r in vset:
            v[r] += 1
    return dict(v)
