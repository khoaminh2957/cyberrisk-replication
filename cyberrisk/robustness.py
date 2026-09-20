"""Section 6 of the paper (Internet Appendix Tables IA7-IA14): further evidence and robustness.
Each function returns the modified input that the corresponding baseline routine (portfolios.py,
fama_macbeth.py, validation.py) is then re-run on, or the statistic itself.

IA7  A post-2011 sample        B zeros -> 4-digit-SIC industry median   C zeros backfilled
     D drop peer industries    E training sample excludes same-auditor firms (measure.py, auditor=)
     F industry-adjusted returns   G leave one industry out   H drop Energy & Durables
     I drop cyber-insured firms    J drop training-sample firms   K forward-fill to 2020
     L monthly / annual rebalancing (portfolios.portfolio_returns(rebalance=))
IA9  double sorts on R&D, patent flow, patent stock (portfolios.table8)
IA10 placebo: similarity of the NON-cyber Item 1A text        IA11 other text-based risk controls
IA12 IVOL / ROA subsumption and orthogonalized score; Oster (2019) bounds
IA13 cyber beta (factor.cyber_beta) in Fama-MacBeth            IA14 simpler alternative measures
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .stats import logit, standardize


# --- IA7 sample / score modifications -------------------------------------------------------------
def post_2011(scores):
    """Scores filed after the SEC's cybersecurity disclosure guidance of 13 October 2011."""
    return scores[scores["filing_date"] >= "2011-10-13"]


def zeros_to_industry_median(scores, sic4):
    """Replace zero scores with the median score of the 4-digit SIC industry in the same year.
    sic4: Series permno -> SIC code."""
    s = scores.copy()
    s["sic4"] = s["permno"].map(sic4)
    med = s[s["cyber_risk"] > 0].groupby(["sic4", "fyear"])["cyber_risk"].median()
    fill = pd.Series(list(zip(s["sic4"], s["fyear"]))).map(med).values
    s.loc[(s["cyber_risk"] == 0) & pd.notna(fill), "cyber_risk"] = fill[(s["cyber_risk"] == 0).values & pd.notna(fill)]
    return s.drop(columns="sic4")


def backfill_zeros(scores):
    """Replace a firm's zero scores with its first available non-zero score."""
    s = scores.sort_values(["permno", "fyear"]).copy()
    first = s[s["cyber_risk"] > 0].groupby("permno")["cyber_risk"].first()
    z = s["cyber_risk"] == 0
    s.loc[z, "cyber_risk"] = s.loc[z, "permno"].map(first).fillna(0.0).values
    return s


def exclude_firms(scores, permnos):
    return scores[~scores["permno"].isin(set(permnos))]


def exclude_peer_industries(scores, training_permnos, ff48):
    """Drop every firm in a Fama-French 48 industry that contains a training-sample firm."""
    peers = {ff48.get(p) for p in training_permnos} - {None}
    return scores[~scores["permno"].map(ff48).isin(peers)]


def exclude_industries(scores, ff12, drop):
    """IA7 G (one industry at a time) and H (Energy = 4 and Durables = 2)."""
    return scores[~scores["permno"].map(ff12).isin(set(drop))]


def industry_adjust(crsp_m, ff12, industry_returns):
    """Stock return minus its FF12 industry return in the month (industry_returns: DataFrame by
    month with the 12 industry columns in Ken French order)."""
    m = crsp_m.copy()
    ind = m["permno"].map(ff12)
    cols = list(industry_returns.columns)
    ir = industry_returns.stack().rename("ind_ret")
    ir.index = ir.index.set_names(["month", "ind"])
    key = pd.MultiIndex.from_arrays([m["month"], ind.map(lambda i: cols[int(i) - 1] if pd.notna(i) else None)])
    m["ret"] = m["ret"] - ir.reindex(key).values
    return m


def forward_fill_to_2020(scores):
    """Missing 2019 / 2020 scores replaced by the firm's last score from 2017 or 2018; the
    filing date is moved forward by whole years so the portfolio code keeps using it."""
    s = scores.sort_values(["permno", "fyear"]).copy()
    last = s[s["fyear"].isin([2017, 2018])].groupby("permno").tail(1)
    extra = []
    for _, r in last.iterrows():
        for fy in (2019, 2020):
            if not ((s["permno"] == r["permno"]) & (s["fyear"] == fy)).any():
                extra.append({**r.to_dict(), "fyear": fy,
                              "filing_date": r["filing_date"] + pd.DateOffset(years=fy - r["fyear"])})
    return pd.concat([s, pd.DataFrame(extra)], ignore_index=True)


# --- IA10: placebo measure from the NON-cybersecurity Item 1A text ------------------------------
def placebo_disclosures(item_1a_sentences, captured_indices):
    """The Item 1A text that the cyber extraction did NOT capture (§6.2: "we extract all the
    non-cybersecurity risk disclosures in the Item 1.A Risk Factors section")."""
    return " ".join(s.text for i, s in enumerate(item_1a_sentences) if i not in set(captured_indices))


def placebo_measure(placebo_texts, meta, attacks, rooter, min_freq=10):
    """Cosine similarity of the non-cyber text against the SAME training sample (§6.2; the paper's
    universe there is 15,452 words).  meta: DataFrame[firm, filing_date, fiscal_year] aligned with
    `placebo_texts`.  Returns meta with cyber_risk = the placebo score."""
    from .measure import cybersecurity_risk
    from .roots import always_capitalised, build_vocabulary, vectorize
    cap = always_capitalised(placebo_texts)
    vocab, _ = build_vocabulary(placebo_texts, rooter, cap, min_freq=min_freq)
    d = meta.copy()
    d["vector"] = [vectorize(t, vocab, rooter, cap) for t in placebo_texts]
    out = cybersecurity_risk(d, attacks)
    return out.drop(columns=["vector"]), len(vocab)


# --- IA12: subsumption, orthogonalization, Oster bounds ------------------------------------------
def orthogonalize(panel, col="cyber_risk", against=("idiosyncratic_volatility",), by="month"):
    """Residual of `col` on `against` in each cross-section, as a new column `<col>_orth`."""
    p = panel.copy()

    def resid(g):
        d = g[[col] + list(against)].dropna()
        if len(d) < len(against) + 5:
            return pd.Series(np.nan, index=g.index)
        m = sm.OLS(d[col], sm.add_constant(d[list(against)])).fit()
        return pd.Series(m.resid, index=d.index).reindex(g.index)
    p[f"{col}_orth"] = p.groupby(by, group_keys=False)[[col] + list(against)].apply(resid)
    return p


def oster(beta_short, r2_short, beta_long, r2_long, r_max=None, delta=2.0):
    """Oster (2019) coefficient stability.  Returns the bias-adjusted coefficient at `delta`
    (proportional selection) and the delta that would drive the coefficient to zero.  R_max
    defaults to Oster's 1.3 x R2 of the controlled regression (the paper does not report its
    choice)."""
    r_max = 1.3 * r2_long if r_max is None else r_max
    beta_star = beta_long - delta * (beta_short - beta_long) * (r_max - r2_long) / (r2_long - r2_short)
    delta_zero = beta_long * (r2_long - r2_short) / ((beta_short - beta_long) * (r_max - r2_long))
    return {"beta_star_delta": beta_star, "delta_for_zero": delta_zero, "r_max": r_max}


# --- IA14: simpler alternative measures --------------------------------------------------------------
def cyberattack_probability(panel, controls, attack_col="attack", firm_col="firm", year_col="fyear"):
    """Logit of an attack in year t on firm variables of t-1; the fitted coefficients applied to
    year t variables give the probability for t+1 (Appendix B, Cyberattack probability)."""
    p = panel.sort_values([firm_col, year_col]).copy()
    lagged = [f"{c}_lag" for c in controls]
    for c in controls:
        p[f"{c}_lag"] = p.groupby(firm_col)[c].shift(1)
    m = logit(p, attack_col, lagged)
    X = sm.add_constant(p[controls].astype(float).rename(columns=dict(zip(controls, lagged))))
    p["cyberattack_probability"] = m.predict(X[m.params.index])
    return p


def compare_measures(panel, attack_next_col, measures, fe=("ff12", "fyear")):
    """Logit of next-year attack on each alternative measure (standardized), clustered by firm."""
    rows = {}
    for meas in measures:
        z = standardize(panel, [meas])
        m = logit(z, attack_next_col, [meas], fe=fe, cluster="firm")
        rows[meas] = {"coef": m.params[meas], "z": m.tvalues[meas], "n": int(m.nobs), "pseudo_r2": m.prsquared}
    return pd.DataFrame(rows).T
