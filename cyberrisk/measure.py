"""Section 2.4, Equations (1) and (2): the cybersecurity risk measure.

For firm i filing at date d, the training sample is the N_{t-1} firms subject to a cyberattack in
the 1-year period ending at d (2-year period if none, footnote 9).  For each such firm the past
disclosure used is the one it filed in that window (most recent).  The measure is the average
cosine (Eq. 1) / Jaccard (Eq. 2) similarity between i's disclosure vector and those N_{t-1}
disclosure vectors.  A firm without a cybersecurity risk disclosure has an empty vector and a
measure of zero (Table 3: the 25th percentile is zero).

Assumptions not stated in the paper (flagged in EVALUATION.md): a firm is not compared with its
own disclosure; attacked firms with no disclosure in the window contribute nothing and are not
counted in N_{t-1}.
"""
import math

import pandas as pd


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
    na, nb = math.sqrt(sum(x * x for x in a.values())), math.sqrt(sum(x * x for x in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def jaccard(a, b):
    if not a or not b:
        return 0.0
    ka, kb = set(a), set(b)
    return len(ka & kb) / len(ka | kb)


def training_disclosures(attacks, disclosures, firm, filing_date, windows=(1, 2), exclude=()):
    """Vectors of attacked firms' disclosures for one filing.  Returns (list_of_vectors, years).
    `exclude`: further training firms to leave out (§6.1: firms sharing the auditor)."""
    d = pd.Timestamp(filing_date)
    for years in windows:
        lo = d - pd.DateOffset(years=years)
        hit = attacks[(attacks["attack_date"] > lo) & (attacks["attack_date"] <= d)
                      & (attacks["firm"] != firm) & ~attacks["firm"].isin(exclude)]
        vecs = []
        for n in hit["firm"].unique():
            past = disclosures[(disclosures["firm"] == n) & (disclosures["filing_date"] > lo)
                               & (disclosures["filing_date"] <= d)]
            if len(past):
                v = past.sort_values("filing_date").iloc[-1]["vector"]
                if v:            # the paper keeps attacked firms "with available cybersecurity risk
                    vecs.append(v)   # disclosures" (§2.3); an empty disclosure is not training text
        if vecs:
            return vecs, years
    return [], None


def cybersecurity_risk(disclosures, attacks, auditor=None):
    """disclosures: DataFrame[firm, filing_date, fiscal_year, vector(dict)]
    attacks:     DataFrame[firm, attack_date]  (the training sample, §2.3)
    auditor:     optional dict firm -> auditor; training firms with the same auditor as the firm
                 are excluded (the "excluding peers-auditor" measure of §6.1)
    Returns disclosures with columns cyber_risk, cyber_risk_jaccard, n_train, window_years."""
    out = disclosures.copy()
    cos, jac, n, w = [], [], [], []
    for _, row in out.iterrows():
        excl = ()
        if auditor:
            a = auditor.get(row["firm"])
            excl = [f for f, b in auditor.items() if b == a and a is not None]
        vecs, years = training_disclosures(attacks, disclosures, row["firm"], row["filing_date"], exclude=excl)
        if vecs and row["vector"]:
            cos.append(sum(cosine(row["vector"], v) for v in vecs) / len(vecs))
            jac.append(sum(jaccard(row["vector"], v) for v in vecs) / len(vecs))
        else:
            cos.append(0.0); jac.append(0.0)
        n.append(len(vecs)); w.append(years)
    out["cyber_risk"], out["cyber_risk_jaccard"], out["n_train"], out["window_years"] = cos, jac, n, w
    return out
