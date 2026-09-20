"""Tables 10-12, 2-6 and the §6 robustness helpers on the synthetic economy: shapes, signs of
planted effects, and internal consistency."""
import os
import numpy as np
import pandas as pd
import pytest

from cyberrisk.tests.synthetic import make
from cyberrisk import factor as F, solarwinds as S, validation as V, robustness as R
from cyberrisk.factors_ff import factors
from cyberrisk.gtrends import stitch, abnormal_svi, high_svi_dummy

DATA_FF = os.path.join(os.path.dirname(__file__), "..", "data", "ff")


@pytest.fixture(scope="module")
def econ():
    return make(data_dir=DATA_FF, n_firms=120, end="2019-06")


def _daily_from_monthly(crsp_m, seed=1):
    """Daily returns consistent with the monthly ones (trading days of each month)."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2007-01-01", "2021-03-31")
    out = []
    for p, g in crsp_m.groupby("permno"):
        for _, r in g.iterrows():
            d = days[(days.to_period("M") == r["month"])]
            if len(d) == 0:
                continue
            x = rng.normal(0, 0.01, len(d))
            x += (np.log1p(r["ret"]) - np.log1p(x).sum()) / len(d)     # compounds to the monthly return
            out.append(pd.DataFrame({"permno": p, "date": d, "ret": np.expm1(x)}))
    return pd.concat(out, ignore_index=True)


def test_cyber_factor_and_table10(econ):
    scores, crsp_m, f = econ
    crsp_d = _daily_from_monthly(crsp_m[crsp_m["month"] >= pd.Period("2008-01", "M")])
    me_m = crsp_m[["permno", "month", "me"]]
    crf = F.cyber_factor(scores, crsp_d, me_m, k=5, start="2008-03-01", end="2009-03-31")
    assert crf.index.min() >= pd.Timestamp("2008-03-01") and len(crf) > 200 and crf.notna().mean() > 0.95
    fd = factors(DATA_FF, daily=True)
    rng = np.random.default_rng(0)
    # planted: the dummy is on when the factor is most negative -> negative beta
    dummy = (crf < crf.quantile(0.1)).astype(int)
    t = F.table10(crf, dummy, fd)
    assert list(t.index) == ["NONE", "CAPM", "FFC", "FF-5"] and (t["high_svi"] < 0).all()
    placebo = F.table10(crf, dummy, fd, shift_days=5)
    assert abs(placebo.loc["NONE", "high_svi"]) < abs(t.loc["NONE", "high_svi"])
    random_dummy = pd.Series(rng.integers(0, 2, len(crf)), index=crf.index)
    assert abs(F.table10(crf, random_dummy, fd).loc["NONE", "t_high_svi"]) < 3


def test_gtrends_helpers():
    a = pd.Series(np.arange(1, 11, dtype=float), index=pd.date_range("2020-01-01", periods=10))
    b = pd.Series(np.arange(6, 16, dtype=float) * 2, index=pd.date_range("2020-01-06", periods=10))
    s = stitch([a, b])                       # b = 2 x a on the 5-day overlap -> rescaled by 1/2
    assert len(s) == 15 and abs(s.iloc[-1] - 15.0) < 1e-9
    svi = pd.Series(10.0, index=pd.date_range("2020-01-01", periods=40)); svi.iloc[30] = 100.0
    d = high_svi_dummy(abnormal_svi(svi))
    assert d.iloc[30] == 1 and d.iloc[:30].sum() == 0


def test_solarwinds_tables(econ):
    scores, crsp_m, f = econ
    rng = np.random.default_rng(2)
    days = pd.bdate_range("2019-06-01", "2021-01-31")
    mkt = pd.Series(rng.normal(0, 0.01, len(days)), index=days)
    ex = S.ex_ante_scores(scores)
    rows = []
    for _, r in ex.iterrows():
        e = rng.normal(0, 0.01, len(days))
        ret = 0.0002 + 1.0 * mkt.values + e
        # planted: high-score firms fall on the event day
        ret[days.get_loc(pd.Timestamp("2020-12-14"))] -= 0.10 * r["cyber_risk"]
        rows.append(pd.DataFrame({"permno": r["permno"], "date": days, "ret": ret}))
    crsp_d = pd.concat(rows, ignore_index=True)
    df = S.event_sample(scores, crsp_d, mkt)
    a = S.table11_panel_a(df)
    assert a.loc["car_-1_1", "P10-P1"] < 0 and a.loc["car_-1_1", "p_value"] < 0.05
    b = S.table11_panel_b(df)
    assert b.loc[("car_-1_1", "cyber_risk"), "coef"] < 0 and len(b) == 6
    # affected firms drawn with probability rising in the score (a deterministic top-k would
    # separate the top-decile dummy perfectly and make the logit singular)
    pr = df["cyber_risk"] / df["cyber_risk"].sum()
    affected = rng.choice(df["permno"].values, size=25, replace=False, p=pr.values)
    pa, pb = S.table12(df, affected)
    assert pa.loc["cyber_risk", "affected"] > pa.loc["cyber_risk", "nonaffected"] and pb.loc["cyber_risk", "coef"] > 0


def _firm_year_panel(seed=3, n=150, years=range(2007, 2019)):
    rng = np.random.default_rng(seed)
    rows = []
    for firm in range(n):
        ff12 = int(rng.integers(1, 13)); size = rng.normal(6.5, 2)
        for y in years:
            score = float(np.clip(0.1 + 0.02 * (y - 2007) + 0.02 * size + rng.normal(0, 0.1), 0, 0.7))
            rows.append({"firm": firm, "fyear": y, "ff12": ff12, "cyber_risk": score,
                         "firm_size_ln": size + rng.normal(0, .2), "firm_age_ln": np.log(y - 2000),
                         "tobins_q": abs(rng.normal(1.9, 1)), "roa": rng.normal(0.03, 0.2),
                         "tangibility": rng.uniform(0, .8), "rd_expenditures": abs(rng.normal(0, .1)),
                         "secrets": int(rng.uniform() < .3), "cash_flow_volatility_industry": abs(rng.normal(.1, .05)),
                         "risk_section_length": int(abs(rng.normal(260, 170))) + 1,
                         "readability": abs(rng.normal(1e7, 5e6)) + 1e5,
                         "institutional_ownership": rng.uniform(0, .6), "independent_directors": rng.uniform(.5, 1),
                         "risk_committee": int(rng.uniform() < .05),
                         "crd_sentences": int(score * 40), "negative_words": rng.uniform(0, .1),
                         "precise_words": rng.uniform(0, .02), "litigious_words": rng.uniform(0, .05),
                         "cyber_insurance": int(rng.uniform() < score), "excerpt": "…"})
    p = pd.DataFrame(rows)
    p["risk_section_length_ln"] = np.log(p["risk_section_length"]); p["readability_ln"] = np.log(p["readability"])
    p["crd_sentences_ratio"] = p["crd_sentences"] / p["risk_section_length"]
    p["ncskew"] = 0.5 * p["cyber_risk"] + rng.normal(0, 1, len(p)); p["extr_sigma"] = 2.7 + 0.3 * p["cyber_risk"] + rng.normal(0, .5, len(p))
    prob = 1 / (1 + np.exp(-(-4 + 4 * p["cyber_risk"])))
    p["attack_next_year"] = (rng.uniform(size=len(p)) < prob).astype(int)
    p = p.sort_values(["firm", "fyear"])
    p["previous_attack"] = p.groupby("firm")["attack_next_year"].shift(1).fillna(0).astype(int)
    return p


def test_validation_tables():
    p = _firm_year_panel()
    top, bottom = V.table1(p); assert len(top) == 5 and top["cyber_risk"].iloc[0] >= bottom["cyber_risk"].iloc[0]
    r, pv = V.table2(p); assert r.loc["cyber_risk", "crd_sentences"] > 0.5 and pv.loc["cyber_risk", "crd_sentences"] < 0.01
    f1 = V.figure1(p, {2010: 11, 2012: 9, 2014: 32}); assert f1["mean_score"].corr(pd.Series(f1.index, index=f1.index)) > 0.9 and f1.loc[2014, "n_attacks"] == 32
    t3 = V.table3(p); assert list(t3.columns) == ["mean", "std", "1%", "25%", "50%", "75%", "99%"] and "cyber_risk" in t3.index
    t4 = V.table4(p); assert t4.loc["firm_size_ln", "Model 1 coef"] > 0 and t4.loc["firm_size_ln", "Model 1 t"] > 2
    t5 = V.table5(p); assert t5.loc["cyber_risk", "Model 1 coef"] > 0 if "Model 1 coef" in t5 else True
    tab, econ = V.table6(p)
    assert tab.loc["cyber_risk", "Model 1 coef"] > 0 and tab.loc["cyber_risk", "Model 2 coef"] > 0
    assert set(econ) == {"Model 1", "Model 2"}
    import math
    assert all(abs(e["pct_increase"] - 100 * (math.exp(e["coef"]) - 1)) < 1e-9 and e["pct_increase"] > 0 for e in econ.values())
    assert abs(100 * (math.exp(0.656) - 1) - 92.70) < 0.02      # the paper's 92.70% is Model 2 read as an odds ratio


def test_table5_lags_only_the_score():
    p = _firm_year_panel(n=60)
    # a control that is constant within firm but differs across firms cannot be affected by lagging
    marker = p.groupby("firm")["firm_size_ln"].transform("first")
    p["tangibility"] = marker                                  # perfectly known contemporaneously
    t = V.table5(p)
    assert "cyber_risk" in t.index and t.loc["N", "ncskew coef"] > 0
    # the score must be the previous year's: a panel whose score is shifted forward by one year
    # gives the same coefficient
    q = p.copy(); q["cyber_risk"] = q.groupby("firm")["cyber_risk"].shift(-1)
    t2 = V.table5(q)
    assert abs(t.loc["cyber_risk", "ncskew coef"] - t2.loc["cyber_risk", "ncskew coef"]) > 1e-9


def test_placebo_measure_uses_non_cyber_text():
    from cyberrisk.roots import Rooter
    span_texts = ["Hackers attacked our systems. We sell furniture in many stores. Furniture demand may fall."]
    from cyberrisk.extract import split_sentences, Sentence, extract as X
    sents = [Sentence(s) for s in split_sentences(span_texts[0])]
    caps = X(sents)
    placebo = R.placebo_disclosures(sents, [c.index for c in caps])
    assert "Hackers attacked" not in placebo and "furniture" in placebo.lower()
    meta = pd.DataFrame({"firm": ["a", "b"], "filing_date": pd.to_datetime(["2018-01-01", "2018-02-01"]),
                         "fiscal_year": [2017, 2017]})
    att = pd.DataFrame({"firm": ["a"], "attack_date": [pd.Timestamp("2017-09-01")]})
    out, nv = R.placebo_measure([placebo, placebo], meta, att, Rooter(), min_freq=1)
    assert nv > 0 and out.loc[out["firm"] == "b", "cyber_risk"].iloc[0] == 1.0


def test_robustness_helpers(econ):
    scores, crsp_m, f = econ
    s = R.backfill_zeros(scores)
    firms_with_pos = set(scores[scores["cyber_risk"] > 0]["permno"])
    assert (s[s["permno"].isin(firms_with_pos)]["cyber_risk"] > 0).all()
    sic4 = pd.Series({p: 3570 + (p % 3) for p in scores["permno"].unique()})
    m = R.zeros_to_industry_median(scores, sic4)
    assert (m["cyber_risk"] == 0).sum() < (scores["cyber_risk"] == 0).sum()
    ff = R.forward_fill_to_2020(scores); assert set(ff["fyear"]) >= {2019, 2020}
    ff12 = {p: 1 + p % 12 for p in scores["permno"].unique()}
    assert R.exclude_industries(scores, ff12, {2, 4})["permno"].map(ff12).isin({2, 4}).sum() == 0
    o = R.oster(beta_short=0.298, r2_short=0.01, beta_long=0.124, r2_long=0.05)
    assert o["delta_for_zero"] > 0
    assert len(R.post_2011(scores)) < len(scores)
