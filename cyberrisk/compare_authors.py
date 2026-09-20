"""Our measure against the authors' own published measure.

The authors deposited "Replication Codes & Data for Cybersecurity Risk" on Harvard Dataverse
(doi:10.7910/DVN/LCVVG5, CC0).  Of the 20 files only `flmw_rfs.dta` carries values: 44,972
firm-years with `cyber_risk_score_cosine`, the measure itself.  Their key is Compustat's gvkey and
ours is the SEC CIK, so the bridge here is the company name, normalised the same way on both sides
and kept only where a name identifies exactly one gvkey and one CIK.

    python3 -m cyberrisk.compare_authors cyberrisk/data/run/v7_scored.pkl

Result on run v7 (2026-09-20): 1,716 matched firm-years, Pearson r = 0.953, Spearman 0.942,
means 0.2672 (ours) vs 0.2675 (theirs).  EVALUATION.md section 13.
"""
import argparse
import os
import re

import numpy as np
import pandas as pd
from scipy import stats as sps

from .replicate_text import scored_sample

DATAVERSE = "https://dataverse.harvard.edu/api/access/datafile/6820755"   # flmw_rfs.dta
_SUF = r"\b(the|inc|incorporated|corp|corporation|co|company|companies|llc|ltd|limited|plc|lp|holdings?|group|cl a|cl b|na|n a)\b"


def normalise(name):
    x = re.sub(r"[^a-z0-9 ]", " ", str(name).lower())
    return re.sub(r"\s+", " ", re.sub(_SUF, " ", x)).strip()


def fetch(path):
    """Download flmw_rfs.dta from Dataverse if it is not on disk."""
    if not os.path.exists(path):
        import requests
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "wb").write(requests.get(DATAVERSE, timeout=300).content)
    return path


def compare(ours, theirs):
    """ours: the run's scored rows; theirs: flmw_rfs.dta.  Returns (merged, stats)."""
    a = theirs.assign(key=theirs["CONM"].map(normalise))
    s = scored_sample(ours).assign(key=lambda d: d["company"].map(normalise))
    one_gvkey = a.groupby("key")["gvkey"].nunique().eq(1)
    one_cik = s.groupby("key")["cik"].nunique().eq(1)
    good = set(one_gvkey[one_gvkey].index) & set(one_cik[one_cik].index)
    m = (s[s["key"].isin(good)].merge(a[a["key"].isin(good)], on=["key", "fyear"])
         .drop_duplicates(["cik", "fyear"]))
    x, y = m["cyber_risk"].values, m["cyber_risk_score_cosine"].values
    stats = {"matched_firm_years": len(m), "scored_firm_years": len(s), "firms": m["cik"].nunique(),
             "mean_ours": x.mean(), "mean_theirs": y.mean(),
             "median_ours": float(np.median(x)), "median_theirs": float(np.median(y)),
             "pearson": sps.pearsonr(x, y)[0], "spearman": sps.spearmanr(x, y)[0],
             "mean_abs_diff": float(np.mean(np.abs(x - y))), "within_0.05": float(np.mean(np.abs(x - y) <= 0.05)),
             "both_zero": float(np.mean((x == 0) & (y == 0)))}
    return m, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scored", help="v7_scored.pkl, or the published scores_v7.csv")
    ap.add_argument("--dta", default="cyberrisk/data/authors/flmw_rfs.dta")
    a = ap.parse_args(argv)
    ours = (pd.read_pickle(a.scored) if a.scored.endswith(".pkl")
            else pd.read_csv(a.scored, dtype={"cik": str, "sic": str}, parse_dates=["filing_date"]))
    m, stats = compare(ours, pd.read_stata(fetch(a.dta)))
    for k, v in stats.items():
        print(f"{k:22s} {v:.4f}" if isinstance(v, float) else f"{k:22s} {v}")
    g = m.groupby("fyear")
    print("\n" + pd.DataFrame({"n": g.size(), "ours": g["cyber_risk"].mean().round(3),
                               "theirs": g["cyber_risk_score_cosine"].mean().round(3)}).to_string())


if __name__ == "__main__":
    main()
