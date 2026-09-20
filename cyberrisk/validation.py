"""Section 3 of the paper: validation of the measure (Tables 1-6, Figures 1-2).

Inputs are the firm-year panel produced by the pipeline: one row per (firm, fyear) with
cyber_risk, the Table 2 language features, Appendix B characteristics, attack flags.
"""
import numpy as np
import pandas as pd
from scipy import stats as sps

from .stats import logit, ols_fe, standardize, winsorize_by_year

FIRM_CONTROLS = ["firm_size_ln", "firm_age_ln", "tobins_q", "roa", "tangibility", "rd_expenditures",
                 "secrets", "cash_flow_volatility_industry", "risk_section_length_ln", "readability_ln",
                 "institutional_ownership", "independent_directors", "risk_committee"]
TABLE3_VARS = ["cyber_risk", "firm_size_ln", "firm_age_ln", "tobins_q", "roa", "tangibility",
               "rd_expenditures", "secrets", "cash_flow_volatility_industry", "risk_section_length",
               "risk_section_length_ln", "readability", "readability_ln", "institutional_ownership",
               "independent_directors", "risk_committee"]
TABLE2_VARS = ["cyber_risk", "crd_sentences", "crd_sentences_ratio", "negative_words",
               "precise_words", "litigious_words", "cyber_insurance"]


def table1(panel, k=5):
    """Highest and lowest non-zero scores with the disclosure excerpt (first sentence)."""
    p = panel[panel["cyber_risk"] > 0].sort_values("cyber_risk")
    cols = ["firm", "fyear", "cyber_risk", "excerpt"]
    return p.tail(k)[cols][::-1], p.head(k)[cols]


def table2(panel):
    """Pearson correlations of the score with the disclosure-language measures, with p-values."""
    d = panel[TABLE2_VARS].dropna()
    r, p = d.corr(), pd.DataFrame(index=TABLE2_VARS, columns=TABLE2_VARS, dtype=float)
    for a in TABLE2_VARS:
        for b in TABLE2_VARS:
            p.loc[a, b] = sps.pearsonr(d[a], d[b])[1]
    return r, p


def figure1(panel, attacks_by_year):
    """Yearly mean score, share of zero scores, and number of cyberattacks."""
    g = panel.groupby("fyear")["cyber_risk"]
    out = pd.DataFrame({"mean_score": g.mean(), "share_zero": g.apply(lambda s: (s == 0).mean()),
                        "n_firms": g.size()})
    out["n_attacks"] = pd.Series(attacks_by_year).reindex(out.index).fillna(0).astype(int)
    out["corr_score_attacks"] = out["mean_score"].corr(out["n_attacks"])
    return out


def figure2(panel, attacks_by_industry):
    g = panel.groupby("ff12")["cyber_risk"].mean().rename("mean_score").to_frame()
    g["n_attacks"] = pd.Series(attacks_by_industry).reindex(g.index).fillna(0).astype(int)
    return g.sort_values("mean_score", ascending=False)


def table3(panel):
    cont = [v for v in TABLE3_VARS if v not in ("secrets", "risk_committee")]
    p = winsorize_by_year(panel, [c for c in cont if c in panel])
    q = p[[v for v in TABLE3_VARS if v in p]].describe(percentiles=[.01, .25, .5, .75, .99]).T
    return q[["mean", "std", "1%", "25%", "50%", "75%", "99%"]]


def table4(panel):
    """Score on firm, industry, 10-K and governance characteristics.  Model 1: industry + year
    FE; Model 2: firm + year FE; SE clustered by firm."""
    m1 = ols_fe(panel, "cyber_risk", FIRM_CONTROLS, fe=("ff12", "fyear"), cluster="firm")
    m2 = ols_fe(panel, "cyber_risk", FIRM_CONTROLS, fe=("firm", "fyear"), cluster="firm")
    return _side_by_side({"Model 1": m1, "Model 2": m2})


def table5(panel):
    """NCSKEW and EXTR_SIGMA (year t) on the score measured at the beginning of the year (the
    previous fiscal year's 10-K) and contemporaneous controls; industry + year FE; clustered by
    firm; continuous variables standardized."""
    p = panel.sort_values(["firm", "fyear"]).copy()
    p["cyber_risk"] = p.groupby("firm")["cyber_risk"].shift(1)      # only the score is lagged
    lag = ["cyber_risk"] + FIRM_CONTROLS
    z = standardize(p, [c for c in lag if c not in ("secrets", "risk_committee")])
    out = {}
    for y in ("ncskew", "extr_sigma"):
        out[y] = ols_fe(z, y, lag, fe=("ff12", "fyear"), cluster="firm")
    return _side_by_side(out)


def table6(panel, attack_col="attack_next_year", previous_col="previous_attack"):
    """Logit of a cyberattack in t+1 on the score in t; Model 1 FE only, Model 2 adds the
    previous-attack dummy and controls.  Run with attack_col = all / major / nonmajor attacks."""
    z = standardize(panel, ["cyber_risk"] + [c for c in FIRM_CONTROLS if c not in ("secrets", "risk_committee")])
    m1 = logit(z, attack_col, ["cyber_risk"], fe=("ff12", "fyear"), cluster="firm")
    m2 = logit(z, attack_col, ["cyber_risk", previous_col] + FIRM_CONTROLS, fe=("ff12", "fyear"), cluster="firm")
    tab = _side_by_side({"Model 1": m1, "Model 2": m2})
    # Economic magnitude.  The paper: "a one-standard-deviation increase in our measure increases
    # the probability of a cyberattack by 92.70%".  That number is exp(0.656) - 1 = 92.71%, i.e.
    # Model 2's coefficient on the standardized score read as an odds ratio (Model 1's 0.961 would
    # give 161%) -- audit 2026-09-19.  Returned for both models.
    import numpy as np
    econ = {name: {"coef": float(m.params["cyber_risk"]),
                   "pct_increase": 100 * (np.exp(float(m.params["cyber_risk"])) - 1)}
            for name, m in (("Model 1", m1), ("Model 2", m2))}
    return tab, econ


def sm_design(model, df):
    """Design matrix in the column order of a fitted statsmodels result (dummies included)."""
    X = pd.DataFrame(index=df.index)
    for c in model.params.index:
        if c == "const":
            X[c] = 1.0
        elif c in df:
            X[c] = df[c].astype(float)
        else:
            f, _, level = c.partition("_")
            X[c] = (df[f].astype(str) == level).astype(float)
    return X


def _side_by_side(models):
    rows = {}
    for name, m in models.items():
        for k in m.params.index:
            rows.setdefault(k, {})[f"{name} coef"] = m.params[k]
            rows[k][f"{name} t"] = m.tvalues[k]
    out = pd.DataFrame(rows).T
    out.loc["N"] = {f"{n} coef": int(m.nobs) for n, m in models.items()}
    out.loc["R2 / pseudo-R2"] = {f"{n} coef": getattr(m, "rsquared", getattr(m, "prsquared", np.nan)) for n, m in models.items()}
    return out
