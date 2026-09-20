"""Orchestration of the text half of the paper on public data (Sections 2.2-2.4):

  disclosures-edgar   EDGAR full index -> 10-K complete submissions -> Item 1A -> App. A extraction
  disclosures-corpus  the same from EDGAR-CORPUS `section_1A` text (no bold/italic titles: the
                      extraction uses the paper's 10-sentence fallback window)
  measure             word roots, vocabulary, count vectors, Eq. (1)-(2) against the training sample

Each step writes JSONL / CSV under --out and can be resumed.  The finance half (Sections 3-6) needs
the WRDS extracts described in README.md and is driven from notebooks / scripts on top of the
table functions (validation.py, portfolios.py, fama_macbeth.py, factor.py, solarwinds.py,
robustness.py).
"""
import argparse
import json
import os
import sys

import pandas as pd

from . import edgar
from .extract import disclosure_text, extract
from .edgar import text_sentences
from .language import disclosure_features, lm_wordlists
from .measure import cybersecurity_risk
from .roots import Rooter, always_capitalised, build_vocabulary, vectorize
from .variables import readability, risk_section_length, secrets_dummy


def _done(path):
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        rows = [json.loads(l) for l in f if l.strip()]
    return {r["accession"] for r in rows if "error" not in r}      # failed fetches are retried


def _record(cik, fyear, filing_date, accession, item1a_sents, by_ref, extra=None):
    caps = extract(item1a_sents) if item1a_sents else []
    # n_item1a_sentences is the whole section; risk_section_length nets out the cyber sentences,
    # as the authors' SAS does (EVALUATION.md 13.2)
    n_net, n_net_ln = risk_section_length(item1a_sents, len(caps))
    return {"cik": str(int(cik)), "fyear": fyear, "filing_date": filing_date, "accession": accession,
            "has_item_1a": bool(item1a_sents), "by_reference": by_ref,
            "n_item1a_sentences": len(item1a_sents), "risk_section_length": n_net,
            "risk_section_length_ln": n_net_ln,
            "n_titles": sum(s.is_title for s in item1a_sents),
            "disclosure": disclosure_text(item1a_sents, captured=caps),
            "captured": [{"text": c.text, "direct": c.direct, "indirect": c.indirect} for c in caps],
            # Item 1A as parsed (text, title flag): lets the App. A extraction be re-run offline
            "item1a": [[s.text, s.is_title] for s in item1a_sents],
            **(extra or {})}


def disclosures_edgar(index_csv, out, cache_dir, years=range(2006, 2020), limit=None, rows=None):
    """Paper §2.2 on raw EDGAR filings.  One JSONL row per filing.  `rows` (index rows) restricts
    the run to a given set of filings -- a sample or a list of target firms; without it every
    filing in the index is processed.  With cache_dir=None the main document is streamed and
    nothing is cached (readability, which needs the complete file size, is then None)."""
    done = _done(out)
    n = 0
    it = rows if rows is not None else edgar.filings_from_index(index_csv, years=years)
    with open(out, "a") as fo:
        for r in it:
            acc = os.path.basename(r["file_name"]).replace(".txt", "")
            if acc in done:
                continue
            url = "https://www.sec.gov/Archives/" + r["file_name"]
            try:
                raw = edgar.fetch(url, cache_dir) if cache_dir else edgar.fetch_main_document(url)
            except Exception as e:                       # one bad filing must not stop a long run
                fo.write(json.dumps({"accession": acc, "cik": str(int(r["cik"])), "error": repr(e)[:200],
                                     "has_item_1a": False, "by_reference": False}) + "\n"); fo.flush()
                continue
            hdr = edgar.submission_header(raw)
            fyear = edgar.compustat_fyear(hdr["period"])
            doc = edgar.main_document(raw)
            try:
                sents = edgar.html_sentences(doc) if "<" in doc[:5000].lower() else text_sentences(doc)
                span, by_ref = edgar.item_1a(sents)
            except Exception as e:                       # a malformed document is recorded, not fatal
                fo.write(json.dumps({"accession": acc, "cik": str(int(r["cik"])), "error": "parse: " + repr(e)[:180],
                                     "has_item_1a": False, "by_reference": False}) + "\n"); fo.flush()
                continue
            size, size_ln = readability(raw) if cache_dir else (None, None)
            rec = _record(r["cik"], fyear, hdr["filed"], acc, span, by_ref,
                          {"form": r["form"], "period": hdr["period"], "readability": size,
                           "readability_ln": size_ln, "secrets": secrets_dummy(doc),
                           "listed": edgar.listed_on_exchange(doc), "company": r.get("company_name")})
            fo.write(json.dumps(rec) + "\n"); fo.flush()
            n += 1
            if limit and n >= limit:
                break
    return out


def reextract(jsonl_in, jsonl_out):
    """Re-run the Appendix A extraction on the Item 1A sentences stored in each record (no
    download): for a change to the extraction rules, not to Item 1A location."""
    from .extract import Sentence
    with open(jsonl_in) as fi, open(jsonl_out, "w") as fo:
        for line in fi:
            r = json.loads(line)
            if r.get("item1a") is not None:
                sents = [Sentence(t, bool(ti)) for t, ti in r["item1a"]]
                if edgar.is_stub(sents):                 # same exclusion as edgar.item_1a
                    r["has_item_1a"], r["item1a"] = False, []
                    sents = []
                caps = extract(sents)
                r["n_item1a_sentences"] = len(sents)
                r["risk_section_length"], r["risk_section_length_ln"] = risk_section_length(sents, len(caps))
                r["captured"] = [{"text": c.text, "direct": c.direct, "indirect": c.indirect} for c in caps]
                r["disclosure"] = disclosure_text(sents, captured=caps)
            fo.write(json.dumps(r) + "\n")
    return jsonl_out


def _worker(args):
    rows, out = args
    disclosures_edgar(None, out, None, rows=rows)
    return out


def disclosures_edgar_parallel(rows, out_prefix, workers=4):
    """disclosures_edgar over `rows` split round-robin across processes (each writes
    <out_prefix>.<i>.jsonl and resumes independently).  4 workers ~ 2 requests/second, well under
    EDGAR's 10/second fair-access limit."""
    import glob
    from multiprocessing import Pool
    done = set()
    for p in glob.glob(f"{out_prefix}.*.jsonl"):          # resume across a change of worker count
        done |= _done(p)
    rows = [r for r in rows if os.path.basename(r["file_name"]).replace(".txt", "") not in done]
    jobs = [(rows[i::workers], f"{out_prefix}.{i}.jsonl") for i in range(workers)]
    with Pool(workers) as pool:
        return pool.map(_worker, jobs)


def sample_rows(index_csv, per_year, seed=20260919, years=range(2007, 2020)):
    """A simple random sample of `per_year` 10-K filings per filing year (the paper processes every
    filing; a sample is used here only to bound the download -- the measure of a firm depends on
    its own disclosure and the training sample, not on the other firms, so a random sample gives
    unbiased year-level means and percentiles; only the vocabulary threshold sees the smaller corpus)."""
    import random
    rng = random.Random(seed)
    by = {}
    for r in edgar.filings_from_index(index_csv, years=years):
        by.setdefault(int(r["date_filed"][:4]), []).append(r)
    out = []
    for y in sorted(by):
        out += rng.sample(by[y], min(per_year, len(by[y])))
    return out


def target_rows(index_csv, ciks, years=range(2005, 2020)):
    """Every 10-K filing of the given CIKs (training-sample firms, Table 1 firms)."""
    ciks = {str(int(c)) for c in ciks}
    return [r for r in edgar.filings_from_index(index_csv, years=years) if str(int(r["cik"])) in ciks]


def submission_sizes(cik_accessions, submissions_zip):
    """Appendix B `Readability` = "file size ... of the SEC complete submission text file".  The
    streaming fetch stops at the first </DOCUMENT>, so the run never sees the whole file; SEC's
    bulk submissions archive (https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip)
    carries a `size` per accession instead.  MEASURED 2026-09-20: for accession 0001341004-07-003146
    the field is 255,269 and the served .txt is 255,269 bytes.

    cik_accessions: iterable of (cik, accession).  Returns {accession: size_in_bytes}."""
    import zipfile
    need = {}
    for cik, acc in cik_accessions:
        need.setdefault(f"CIK{int(cik):010d}", set()).add(acc)
    z = zipfile.ZipFile(submissions_zip)
    names = set(z.namelist())
    out = {}
    for key, accs in need.items():
        for name in [f"{key}.json"] + [f"{key}-submissions-{i:03d}.json" for i in range(1, 12)]:
            if name not in names:
                continue
            d = json.loads(z.read(name))
            rec = d["filings"]["recent"] if "filings" in d else d
            out.update({a: s for a, s in zip(rec["accessionNumber"], rec["size"]) if a in accs})
    return out


def disclosures_corpus(jsonl_paths, out, limit=None):
    """Paper §2.2 from EDGAR-CORPUS rows (filename, cik, year, section_1A)."""
    done = _done(out)
    n = 0
    with open(out, "a") as fo:
        for path in jsonl_paths:
            with open(path) as f:
                for line in f:
                    d = json.loads(line)
                    acc = d["filename"]
                    if acc in done:
                        continue
                    sents = text_sentences(d.get("section_1A") or "")
                    span, by_ref = sents, bool(sents) and len(" ".join(s.text for s in sents).split()) < 300 \
                        and "by reference" in " ".join(s.text for s in sents).lower()
                    rec = _record(d["cik"], int(d["year"]) - 1, None, acc, span, by_ref,
                                  {"form": "10-K", "source": "edgar-corpus", "filing_year": int(d["year"])})
                    fo.write(json.dumps(rec) + "\n"); fo.flush()
                    n += 1
                    if limit and n >= limit:
                        return out
    return out


def measure(disclosures_jsonl, attacks_csv, out_csv, lm_csv=None, cache_dir=None):
    """§2.4: vocabulary (roots with frequency >= 10), count vectors, Eq. (1)-(2).
    attacks_csv: firm (cik), attack_date -- the training sample from training.py."""
    rows = [json.loads(l) for l in open(disclosures_jsonl) if l.strip()]
    rows = [r for r in rows if r["has_item_1a"] and not r["by_reference"]]
    texts = [r["disclosure"] for r in rows]
    rooter = Rooter(os.path.join(cache_dir, "roots_cache.json") if cache_dir else None)
    cap = always_capitalised(texts)
    vocab, counts = build_vocabulary(texts, rooter, cap)
    rooter.save()
    disc = pd.DataFrame({
        "firm": [r["cik"] for r in rows],
        "filing_date": pd.to_datetime([r["filing_date"] or f"{r['filing_year']}-06-30" for r in rows]),
        "fiscal_year": [r["fyear"] for r in rows],
        "accession": [r["accession"] for r in rows],
        "vector": [vectorize(t, vocab, rooter, cap) for t in texts],
        "n_item1a_sentences": [r["n_item1a_sentences"] for r in rows],
        "crd_sentences": [len(r["captured"]) for r in rows],
    })
    attacks = pd.read_csv(attacks_csv, dtype={"firm": str}, parse_dates=["attack_date"])
    res = cybersecurity_risk(disc, attacks)
    if lm_csv:
        lists = lm_wordlists(lm_csv)
        from .extract import Captured
        feats = [disclosure_features([Captured(i, c["text"], False, c["direct"], c["indirect"])
                                      for i, c in enumerate(r["captured"])], r["n_item1a_sentences"], lists)
                 for r in rows]
        res = pd.concat([res.reset_index(drop=True), pd.DataFrame(feats)], axis=1)
    res.drop(columns=["vector"]).to_csv(out_csv, index=False)
    json.dump({"vocabulary_size": len(vocab), "vocabulary": vocab,
               "top20": [w for w, _ in sorted(((w, counts[w]) for w in vocab), key=lambda t: -t[1])[:20]]},
              open(out_csv.replace(".csv", "_vocab.json"), "w"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("disclosures-edgar"); a.add_argument("--index", required=True); a.add_argument("--out", required=True)
    a.add_argument("--cache", required=True); a.add_argument("--limit", type=int)
    b = sub.add_parser("disclosures-corpus"); b.add_argument("--jsonl", nargs="+", required=True); b.add_argument("--out", required=True)
    b.add_argument("--limit", type=int)
    c = sub.add_parser("measure"); c.add_argument("--disclosures", required=True); c.add_argument("--attacks", required=True)
    c.add_argument("--out", required=True); c.add_argument("--lm"); c.add_argument("--cache")
    args = ap.parse_args(argv)
    if args.cmd == "disclosures-edgar":
        disclosures_edgar(args.index, args.out, args.cache, limit=args.limit)
    elif args.cmd == "disclosures-corpus":
        disclosures_corpus(args.jsonl, args.out, limit=args.limit)
    else:
        measure(args.disclosures, args.attacks, args.out, args.lm, args.cache)


if __name__ == "__main__":
    main()
