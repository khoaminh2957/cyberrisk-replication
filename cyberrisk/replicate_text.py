"""The paper's numbers that the TEXT half produces from public data (EDGAR 10-Ks + the PRC
chronology), recomputed and put next to the paper.  Nothing here needs CRSP/Compustat.

Samples (fixed before any comparison was made):
  scored  -- the random 10-K sample (pipeline.sample_rows, 450 per filing year 2007-2019) restricted
             to filings with an Item 1A (not incorporated by reference), a cover page naming a
             national exchange (proxy for the paper's CRSP universe), fiscal years 2007-2018, one
             filing per CIK and fiscal year.
  train   -- every PRC incident linked by link_prc.py (no Factiva "major" flag exists here: this is
             the paper's own all-incidents variant, §2.3).
  table 1 -- the ten firm-years printed in Table 1, scored against the same training sample.
Paper values marked (chart) were read off Figures 1-2 and carry a reading error of about +-0.005.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
from scipy import stats as sps

from .language import disclosure_features, lm_wordlists
from .extract import Captured
from .measure import cybersecurity_risk
from .roots import Rooter, always_capitalised, build_vocabulary, vectorize

HERE = os.path.dirname(os.path.abspath(__file__))
YEARS = list(range(2007, 2019))

PAPER = {
    "attacks_by_year": dict(zip(range(2005, 2019), [1, 5, 7, 3, 3, 11, 8, 9, 24, 32, 16, 16, 24, 16])),
    "mean_by_year_chart": dict(zip(YEARS, [0.085, 0.097, 0.092, 0.127, 0.153, 0.218, 0.270, 0.335,
                                           0.390, 0.403, 0.435, 0.455])),
    "table3": {"mean": 0.24, "sd": 0.22, "p1": 0.00, "p25": 0.00, "p50": 0.28, "p75": 0.45, "p99": 0.61},
    # Table 3's Readability row: the level is the complete submission's size in BYTES (Appendix B says
    # megabytes; the printed (ln) row only matches bytes -- EVALUATION.md section 4 C2)
    "readability": {"mean": 10453409, "sd": 11546923, "p1": 384975, "p25": 1865855, "p50": 6163418,
                    "p75": 15323736, "p99": 52900376},
    "readability_ln": {"mean": 15.52, "sd": 1.22, "p1": 12.86, "p25": 14.44, "p50": 15.63, "p75": 16.54, "p99": 17.78},
    "zero_share": {2011: 0.4903, 2018: 0.1059},
    "disclosure_share": {2007: 0.2875, 2010: 0.39, 2012: 0.66, 2018: 0.90},
    "vocab_size": 3210,
    "top20": ["security", "system", "information", "result", "business", "breach", "data", "operation",
              "customer", "service", "failure", "loss", "financial", "damage", "computer", "include",
              "technology", "disruption", "reputation", "unauthorized"],
    "table1": {("1618921", 2018): ("Walgreens Boots Alliance", 0.684), ("1613665", 2016): ("Great Western Bancorp", 0.683),
               ("1053352", 2017): ("Heritage Commerce", 0.676), ("1050606", 2017): ("Salem Media Group", 0.674),
               ("1093557", 2017): ("Dexcom", 0.670), ("106535", 2015): ("Weyerhaeuser", 0.036),
               ("4447", 2012): ("Hess", 0.052), ("945983", 2013): ("Wayside Technology", 0.078),
               ("812128", 2012): ("Sanderson Farms", 0.109), ("29905", 2012): ("Dover", 0.111)},
    "table2": {"crd_sentences": 0.569, "crd_sentences_ratio": 0.443, "negative_words": 0.033,
               "precise_words": 0.084, "litigious_words": 0.127, "cyber_insurance": 0.169},
    "insurance_mention_share": 0.0843,
    "table6_model1_all": {"coef": 0.961, "t": 7.10, "n": 41140, "pseudo_r2": 0.093},
    "figure2_order": ["Telcm", "Shops", "BusEq", "Money", "Utils", "NoDur", "Other", "Chems", "Hlth",
                      "Durbl", "Manuf", "Enrgy"],
}
FF12 = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm", "Utils", "Shops", "Hlth", "Money", "Other"]


def load_run(run_dir):
    rows = []
    for p in sorted(glob.glob(os.path.join(run_dir, "disc.*.jsonl"))):
        rows += [json.loads(l) for l in open(p) if l.strip()]
    df = pd.DataFrame(rows)
    if "error" in df:
        df = df[df["error"].isna()]
    return df.drop_duplicates("accession", keep="last")      # a filing is counted once


def add_coregistrants(ok, ciks, index_csv):
    """A combined 10-K (one accession filed under several CIKs, e.g. US Airways Group and US Airways
    Inc) is each registrant's 10-K; the download keeps one copy per accession.  For every
    training-sample CIK without rows of its own, copy the rows of its co-registered accessions
    under its CIK.  Copies are flagged and never enter the scored sample."""
    from .pipeline import target_rows
    need = set(ciks) - set(ok["cik"])
    acc2cik = {os.path.basename(r["file_name"]).replace(".txt", ""): str(int(r["cik"]))
               for r in target_rows(index_csv, need)}
    extra = ok[ok["accession"].isin(acc2cik)].copy()
    extra["cik"] = extra["accession"].map(acc2cik)
    extra["coregistrant_copy"] = True
    return pd.concat([ok.assign(coregistrant_copy=False), extra], ignore_index=True)


def compute(run_dir, link_csv, plan_sample_accessions, lm_csv, sic_csv, ff_dir, cache=None, index_csv=None):
    df = load_run(run_dir)
    ok = df[df["has_item_1a"] & ~df["by_reference"] & df["fyear"].notna()].copy()
    link_ciks = set(pd.read_csv(link_csv, dtype={"cik": str})["cik"])
    ok = add_coregistrants(ok, link_ciks, index_csv) if index_csv else ok.assign(coregistrant_copy=False)
    ok = ok.reset_index(drop=True)
    ok["fyear"] = ok["fyear"].astype(int)
    ok["filing_date"] = pd.to_datetime(ok["filing_date"], format="%Y%m%d")
    texts = ok["disclosure"].tolist()
    originals = ok.loc[~ok["coregistrant_copy"], "disclosure"].tolist()   # a filing counts once
    rooter = Rooter(cache)
    cap = always_capitalised(originals)
    vocab, counts = build_vocabulary(originals, rooter, cap)
    ok["vector"] = [vectorize(t, vocab, rooter, cap) for t in texts]
    link = pd.read_csv(link_csv, dtype={"cik": str}, parse_dates=["attack_date"])
    attacks = link.rename(columns={"cik": "firm"})[["firm", "attack_date"]]
    disc = ok.rename(columns={"cik": "firm", "fyear": "fiscal_year"})[["firm", "filing_date", "fiscal_year", "vector", "accession"]]
    scored = cybersecurity_risk(disc, attacks)                  # same row order as `disc`
    for c in ("cyber_risk", "cyber_risk_jaccard", "n_train"):
        ok[c] = scored[c].values
    lists = lm_wordlists(lm_csv)
    feats = [disclosure_features([Captured(i, c["text"], False, c["direct"], c["indirect"]) for i, c in enumerate(r["captured"])],
                                 r["n_item1a_sentences"], lists) for _, r in ok.iterrows()]
    ok = pd.concat([ok.reset_index(drop=True), pd.DataFrame(feats)], axis=1)
    sic = pd.read_csv(sic_csv, usecols=["cik", "sic"], dtype=str)
    sic["cik"] = sic["cik"].str.lstrip("0")
    ok = ok.merge(sic, on="cik", how="left")
    from .factors_ff import sic_map
    f12 = sic_map(ff_dir, 12)
    ok["ff12"] = ok["sic"].map(lambda s: FF12[f12(s) - 1] if f12(s) else None)
    ok["in_sample"] = ok["accession"].isin(plan_sample_accessions) & ~ok["coregistrant_copy"]
    return ok, vocab, counts, link, df


def attack_counts(link, ok):
    """Yearly attack counts under definitions fixed BEFORE the final numbers were seen, each a
    reading of the paper's "cyberattacks ... with available cybersecurity risk disclosures in
    Item 1A Risk Factors section" (§2.3):
      linked               -- the PRC incident is linked to a 10-K filer (link_prc.py)
      +ex-ante Item 1A     -- the firm filed a 10-K with an Item 1A in the year before the attack
      +ex-ante disclosure  -- ... and that Item 1A has >= 1 cybersecurity risk sentence
      +listed              -- ... and that 10-K's cover names a national exchange (CRSP proxy)"""
    def has_before(r, frame):
        h = frame[(frame["cik"] == r["cik"]) & (frame["filing_date"] <= r["attack_date"])
                  & (frame["filing_date"] > r["attack_date"] - pd.DateOffset(years=1))]
        return len(h) > 0
    item = ok[["cik", "filing_date", "listed"]]
    disc = ok[ok["crd_sentences"] > 0]
    L = link.copy()
    L["item1a"] = L.apply(lambda r: has_before(r, item), axis=1)
    L["disclosure"] = L.apply(lambda r: has_before(r, disc), axis=1)
    L["disclosure_listed"] = L.apply(lambda r: has_before(r, disc[disc["listed"]]), axis=1)
    y = L["attack_date"].dt.year
    col = lambda m: L[m].groupby(y[m]).size()
    out = pd.DataFrame({"paper": pd.Series(PAPER["attacks_by_year"]), "linked": L.groupby(y).size(),
                        "+ex-ante Item 1A": col(L["item1a"]), "+ex-ante disclosure": col(L["disclosure"]),
                        "+listed": col(L["disclosure_listed"])}).fillna(0).astype(int)
    out.loc["total"] = out.sum()
    return out


def scored_sample(ok):
    s = ok[ok["in_sample"] & ok["listed"] & ok["fyear"].between(2007, 2018)]
    return s.sort_values("filing_date").drop_duplicates(["cik", "fyear"], keep="last")


def report(ok, vocab, counts, link):
    s = scored_sample(ok)
    out = {}
    out["attack_counts"] = attack_counts(link, ok)
    g = s.groupby("fyear")
    out["by_year"] = pd.DataFrame({"n": g.size(), "mean": g["cyber_risk"].mean(),
                                   "paper_mean(chart)": pd.Series(PAPER["mean_by_year_chart"]),
                                   "se": g["cyber_risk"].std() / np.sqrt(g.size()),
                                   "zero_share": g["cyber_risk"].apply(lambda x: (x == 0).mean()),
                                   "disclosure_share": g["crd_sentences"].apply(lambda x: (x > 0).mean())})
    q = s["cyber_risk"]
    out["table3"] = pd.DataFrame({"paper": pd.Series(PAPER["table3"]),
                                  "ours": pd.Series({"mean": q.mean(), "sd": q.std(), "p1": q.quantile(.01),
                                                     "p25": q.quantile(.25), "p50": q.quantile(.5),
                                                     "p75": q.quantile(.75), "p99": q.quantile(.99)})})
    t1 = []
    for (cik, fy), (name, val) in PAPER["table1"].items():
        r = ok[(ok["cik"] == cik) & (ok["fyear"] == fy)]
        t1.append({"firm": name, "fyear": fy, "paper": val,
                   "ours": r["cyber_risk"].iloc[-1] if len(r) else np.nan,
                   "n_train": r["n_train"].iloc[-1] if len(r) else np.nan,
                   "crd_sentences": r["crd_sentences"].iloc[-1] if len(r) else np.nan})
    out["table1"] = pd.DataFrame(t1)
    # Table 2 on firm-years WITH a cybersecurity risk disclosure: the word ratios are undefined
    # without one.  Of three definitions fixed in advance this one is closest to the paper's full
    # matrix (EVALUATION.md); the other two are reported there.
    d = s[s["crd_sentences"] > 0]
    t2 = {}
    for k, v in PAPER["table2"].items():
        x = d[["cyber_risk", k]].dropna()
        t2[k] = {"paper": v, "ours": sps.pearsonr(x["cyber_risk"], x[k])[0] if len(x) > 2 else np.nan}
    out["table2"] = pd.DataFrame(t2).T
    # the same correlations under the paper's own wording, which the authors' code contradicts
    # (EVALUATION.md 13.2): raw word counts, Strong_Modal for "precise", partial-cover insurance
    alt = {"negative_words": "negative_words_raw", "precise_words": "precise_words_strong_modal",
           "litigious_words": "litigious_words_raw", "cyber_insurance": "cyber_insurance_partial"}
    t2b = {}
    for k, v in PAPER["table2"].items():
        c = alt.get(k, k)
        x = d[["cyber_risk", c]].dropna()
        t2b[k] = {"paper": v, "ours": sps.pearsonr(x["cyber_risk"], x[c])[0] if len(x) > 2 else np.nan}
    out["table2_paper_wording"] = pd.DataFrame(t2b).T
    if s["readability"].notna().any():                    # filled from the bulk submissions archive
        r, lr = s["readability"].dropna(), np.log(s["readability"].dropna())
        stat = lambda x: {"mean": x.mean(), "sd": x.std(), "p1": x.quantile(.01), "p25": x.quantile(.25),
                          "p50": x.quantile(.5), "p75": x.quantile(.75), "p99": x.quantile(.99)}
        out["readability"] = pd.DataFrame({"paper": pd.Series(PAPER["readability"]), "ours": pd.Series(stat(r))})
        out["readability_ln"] = pd.DataFrame({"paper": pd.Series(PAPER["readability_ln"]), "ours": pd.Series(stat(lr))})
        out["readability_n"] = int(r.notna().sum())
    ins = s[s["mentions_insurance"] == 1]
    out["insurance_above_median"] = {"paper": 0.80, "ours": (ins["cyber_risk"] > s["cyber_risk"].median()).mean()}
    out["insurance"] = {"paper": PAPER["insurance_mention_share"], "ours": s["mentions_insurance"].mean()}
    top = [w for w, _ in sorted(((w, counts[w]) for w in vocab), key=lambda t: -t[1])[:20]]
    out["words"] = {"vocab_size_ours": len(vocab), "vocab_size_paper": PAPER["vocab_size"],
                    "top20_overlap": len(set(top) & set(PAPER["top20"])), "top20_ours": top,
                    "missing_from_ours": sorted(set(PAPER["top20"]) - set(top))}
    f2 = s.groupby("ff12")["cyber_risk"].mean().reindex(PAPER["figure2_order"])
    rank_paper = pd.Series(range(12), index=PAPER["figure2_order"])
    out["figure2"] = pd.DataFrame({"ours_mean": f2, "ours_rank": f2.rank(ascending=False), "paper_rank": rank_paper + 1})
    out["figure2_spearman"] = (sps.spearmanr(f2.values, -rank_paper.values, nan_policy="omit")[0]
                               if f2.notna().sum() > 2 else np.nan)
    return out


def table6_model1(ok, link):
    """Table 6, panel A, Model 1: logit of a cyberattack in year t+1 on the (standardised) score of
    fiscal year t, with year and industry fixed effects (FF12 here -- the paper only says
    "Industry fixed effects: Yes"; FF48 is variant V3 in EVALUATION.md), SE clustered by firm.
    None of Model 1's regressors needs WRDS, so it is estimable here; the paper's SAMPLE does need
    "complete risk disclosure and financial data" (Table 6 note), which this sample cannot mirror.

    Design: controls = the random sample (scored_sample); cases = the firm-year right before each
    linked attack.  Outcome-dependent (case-control) sampling leaves logit SLOPES consistent and
    shifts only the intercept (Prentice & Pyke 1979), which the year effects absorb.  Other
    firm-years of attacked firms are NOT added: including them would make selection depend on
    the firm's outcome history.  The score is standardised with the random sample's mean and SD."""
    from .stats import logit
    s = scored_sample(ok)
    mu, sd = s["cyber_risk"].mean(), s["cyber_risk"].std()
    att = link.assign(year=link["attack_date"].dt.year)[["cik", "year"]].drop_duplicates()
    hit = set(zip(att["cik"], att["year"] - 1))                  # attack in t+1 -> firm-year t
    firm_year = ok[ok["listed"] & ok["fyear"].between(2007, 2017)].sort_values("filing_date") \
        .drop_duplicates(["cik", "fyear"], keep="last")
    cases = firm_year[[ (c, y) in hit for c, y in zip(firm_year["cik"], firm_year["fyear"]) ]]
    d = pd.concat([s[s["fyear"] <= 2017], cases]).drop_duplicates("accession")
    d["attack_next_year"] = [int((c, y) in hit) for c, y in zip(d["cik"], d["fyear"])]
    d["z_cyber_risk"] = (d["cyber_risk"] - mu) / sd
    d = d.dropna(subset=["ff12"])
    # fixed-effect cells without a single attack are perfectly predicted (their dummies diverge);
    # they carry no information on the slope and are dropped, as Stata's logit does
    for fe in ("fyear", "ff12"):
        d = d[d.groupby(fe)["attack_next_year"].transform("max") == 1]
    m = logit(d, "attack_next_year", ["z_cyber_risk"], fe=("fyear", "ff12"), cluster="cik")
    return {"coef": float(m.params["z_cyber_risk"]), "t": float(m.tvalues["z_cyber_risk"]),
            "n": int(m.nobs), "cases": int(d["attack_next_year"].sum()), "pseudo_r2": float(m.prsquared),
            "converged": bool(m.mle_retvals.get("converged", False)),
            "paper": PAPER["table6_model1_all"]}
