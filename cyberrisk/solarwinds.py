"""Section 5 / Tables 11-12 of the paper: out-of-sample evidence from the SolarWinds hack.

Event date: 14 December 2020 (SolarWinds' SEC filing).  Market-model CAR[-1,+1] and CAR[-1,+3]
for every sample firm; ex ante cybersecurity risk measured in 2018 (2017 if unavailable).
Table 11 A: average CARs of the top and bottom score deciles and their difference (t-test).
Table 11 B: CAR regressed on the score, on a top-tercile dummy (High cyber risk dummy 1) and on
a top-decile dummy (High cyber risk dummy 2).
Table 12: affected firms = SolarWinds' key customers (FactSet Revere, 38 U.S.-listed firms):
differences in means of abnormal institutional attention (AIA, Bloomberg), CARs and score; logit
of affected on the (standardized) score and the two dummies.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as sps

from .stats import market_model_car, quantile_groups, standardize

EVENT_DATE = "2020-12-14"


def ex_ante_scores(scores):
    """One score per firm: fiscal 2018, else fiscal 2017."""
    s = scores[scores["fyear"].isin([2017, 2018])].sort_values("fyear")
    return s.groupby("permno").tail(1)[["permno", "cyber_risk"]]


def event_sample(scores, crsp_d, market_d):
    s = ex_ante_scores(scores)
    cars = market_model_car(crsp_d, market_d, EVENT_DATE)
    df = s.merge(cars, on="permno")
    df["decile"] = quantile_groups(df["cyber_risk"], 10).values
    df["tercile"] = quantile_groups(df["cyber_risk"], 3).values
    df["high_cyber_risk_dummy_1"] = (df["tercile"] == 3).astype(int)
    df["high_cyber_risk_dummy_2"] = (df["decile"] == 10).astype(int)
    return df


def table11_panel_a(df):
    rows = {}
    for car in ("car_-1_1", "car_-1_3"):
        lo, hi = df.loc[df["decile"] == 1, car].dropna(), df.loc[df["decile"] == 10, car].dropna()
        t, p = sps.ttest_ind(hi, lo, equal_var=False)
        rows[car] = {"P1": lo.mean(), "P10": hi.mean(), "P10-P1": hi.mean() - lo.mean(), "p_value": p}
    return pd.DataFrame(rows).T


def table11_panel_b(df):
    rows = {}
    for car in ("car_-1_1", "car_-1_3"):
        for x in ("cyber_risk", "high_cyber_risk_dummy_1", "high_cyber_risk_dummy_2"):
            d = df[[car, x]].dropna()
            m = sm.OLS(d[car], sm.add_constant(d[[x]])).fit()
            rows[(car, x)] = {"coef": m.params[x], "t": m.tvalues[x], "n": int(m.nobs)}
    return pd.DataFrame(rows).T


def table12(df, affected_permnos, aia=None):
    """affected_permnos: SolarWinds' key customers.  aia: optional Series permno -> 0/1 abnormal
    institutional attention in the five trading days after the disclosure."""
    d = df.copy()
    d["affected"] = d["permno"].isin(set(affected_permnos)).astype(int)
    if aia is not None:
        d["aia"] = d["permno"].map(aia)
    cols = (["aia"] if aia is not None else []) + ["car_-1_1", "car_-1_3", "cyber_risk"]
    a = {}
    for c in cols:
        x, y = d.loc[d["affected"] == 1, c].dropna(), d.loc[d["affected"] == 0, c].dropna()
        a[c] = {"affected": x.mean(), "nonaffected": y.mean(), "p_value": sps.ttest_ind(x, y, equal_var=False)[1]}
    b = {}
    z = standardize(d, ["cyber_risk"])
    for x in ("cyber_risk", "high_cyber_risk_dummy_1", "high_cyber_risk_dummy_2"):
        m = sm.Logit(z["affected"], sm.add_constant(z[[x]])).fit(disp=0)
        b[x] = {"coef": m.params[x], "z": m.tvalues[x], "n": int(m.nobs)}
    return pd.DataFrame(a).T, pd.DataFrame(b).T
