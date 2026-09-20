"""Appendix B formulas in variables.py on small hand-made or simulated inputs."""
import os
import numpy as np
import pandas as pd

from cyberrisk import variables as V
from cyberrisk.factors_ff import factors

DATA_FF = os.path.join(os.path.dirname(__file__), "..", "data", "ff")


def test_compustat_formulas():
    comp = pd.DataFrame({
        "gvkey": [1, 1], "fyear": [2010, 2011], "sic": [3571, 3571],
        "at": [100.0, 120.0], "ceq": [40.0, 50.0], "prcc_f": [10.0, 12.0], "csho": [8.0, 8.0],
        "che": [10.0, 12.0], "ib": [5.0, 6.0], "dp": [2.0, 2.0], "dvc": [1.0, 1.0], "oibdp": [9.0, 12.0],
        "ppent": [30.0, 36.0], "xrd": [np.nan, 6.0], "dltt": [20.0, 24.0], "dlc": [5.0, 6.0]})
    c = V.compustat_variables(comp).set_index("fyear")
    assert c.loc[2011, "firm_age"] == 2 and abs(c.loc[2011, "firm_age_ln"] - np.log(2)) < 1e-12
    assert abs(c.loc[2010, "tobins_q"] - (100 - 40 + 80) / 100) < 1e-12
    assert abs(c.loc[2011, "roa"] - 0.1) < 1e-12 and abs(c.loc[2011, "tangibility"] - 0.3) < 1e-12
    assert c.loc[2010, "rd_expenditures"] == 0.0 and abs(c.loc[2011, "rd_expenditures"] - 0.05) < 1e-12
    assert abs(c.loc[2011, "leverage"] - 0.25) < 1e-12 and abs(c.loc[2011, "asset_growth"] - 0.2) < 1e-12
    assert abs(c.loc[2010, "book_to_market"] - 0.5) < 1e-12


def test_secrets_dummy():
    assert V.secrets_dummy("We rely on trade secrets and take steps to protect them.") == 1
    assert V.secrets_dummy("We must safeguard our confidential information at all times.") == 1
    assert V.secrets_dummy("Our confidential information is valuable. Twelve words later we mention that we protect assets.") == 0


def test_crsp_monthly_variables_recover_beta():
    rng = np.random.default_rng(0)
    f = factors(DATA_FF)
    months = pd.period_range("2005-01", "2014-12", freq="M")
    rows = []
    for p, beta in ((1, 0.8), (2, 1.5)):
        for m in months:
            r = f.loc[m, "RF"] + beta * f.loc[m, "Mkt-RF"] + rng.normal(0, 0.02)
            rows.append({"permno": p, "date": m.to_timestamp(how="end"), "ret": r, "prc": 20.0, "shrout": 1000.0})
    out = V.crsp_monthly_variables(pd.DataFrame(rows), f)
    last = out.groupby("permno").tail(1).set_index("permno")
    assert abs(last.loc[1, "beta"] - 0.8) < 0.15 and abs(last.loc[2, "beta"] - 1.5) < 0.15
    assert last["idiosyncratic_volatility"].between(0.01, 0.04).all()
    assert out["momentum"].notna().sum() > 0 and out["reversal"].notna().sum() > 0
    # momentum at month t = cumulative return over t-11 .. t-1 ("11 months ending one day prior to month t")
    g = out[out["permno"] == 1].reset_index(drop=True)
    k = 30
    expect = np.prod(1 + g.loc[k - 11:k - 1, "ret"]) - 1
    assert abs(g.loc[k, "momentum"] - expect) < 1e-9
    assert abs(g.loc[k, "reversal"] - g.loc[k, "ret"]) < 1e-12          # r(t): not inside the momentum window


def test_crsp_daily_variables():
    days = pd.bdate_range("2010-01-01", "2010-02-28")
    d = pd.DataFrame({"permno": 1, "date": days, "ret": np.linspace(-0.02, 0.02, len(days)),
                      "prc": 10.0, "vol": 1000.0})
    out = V.crsp_daily_variables(d).set_index("month")
    jan = out.loc[pd.Period("2010-01", "M")]
    assert jan["n"] == (days.month == 1).sum() and jan["illiquidity"] > 0
    top5 = d[d["date"].dt.month == 1]["ret"].nlargest(5).mean()
    assert abs(jan["max"] - top5) < 1e-12
    d2 = d[d["date"] < "2010-01-15"]                 # < 15 days -> illiquidity missing
    assert np.isnan(V.crsp_daily_variables(d2)["illiquidity"].iloc[0])


def test_weekly_returns_and_crash_measures():
    rng = np.random.default_rng(1)
    days = pd.bdate_range("2010-01-01", "2012-12-31")
    mkt = pd.Series(rng.normal(0, 0.01, len(days)), index=days)
    d = pd.DataFrame({"permno": 1, "date": days, "ret": 1.2 * mkt.values + rng.normal(0, 0.02, len(days))})
    w = V.weekly_firm_specific_returns(d, mkt)
    assert {"permno", "week", "W"} <= set(w.columns) and len(w) > 100
    cm = V.crash_measures(w)
    assert set(cm["year"]) <= {2010, 2011, 2012} and cm["extr_sigma"].gt(0).all()


def test_ownership_and_governance():
    tr = pd.DataFrame({"permno": [1, 1, 1], "rdate": ["2010-12-31"] * 3, "mgrno": [1, 2, 3],
                       "shares": [600, 40, 100]})
    sh = pd.DataFrame({"permno": [1], "rdate": ["2010-12-31"], "shrout": [1000]})
    io = V.institutional_ownership(tr, sh)
    assert abs(io["institutional_ownership"].iloc[0] - 0.7) < 1e-12     # holders > 5% only
    b = pd.DataFrame({"gvkey": [1], "fyear": [2010], "n_directors": [10], "n_independent": [8],
                      "committee_names": ["Audit; Risk Oversight"]})
    g = V.governance(b)
    assert g["independent_directors"].iloc[0] == 0.8 and g["risk_committee"].iloc[0] == 1


def test_link_disclosures_respects_the_ccm_window():
    scores = pd.DataFrame({"firm": ["0000320193", "0000320193", "999"], "fiscal_year": [2016, 2017, 2017],
                           "filing_date": pd.to_datetime(["2016-10-26", "2017-11-03", "2017-11-03"]),
                           "cyber_risk": [0.4, 0.5, 0.6]})
    cik_gvkey = pd.DataFrame({"cik": ["320193", "320193"], "gvkey": ["001690"] * 2, "fyear": [2016, 2017]})
    ccm = pd.DataFrame({"gvkey": ["001690", "001690"], "permno": [14593, 14593],
                        "linkdt": ["1980-12-12", "2018-01-01"], "linkenddt": ["2017-12-31", None]})
    out = V.link_disclosures(scores, cik_gvkey, ccm)
    assert len(out) == 2 and set(out["permno"]) == {14593}      # CIK 999 has no gvkey
    assert out["cik"].tolist() == ["320193", "320193"]          # leading zeros stripped on both sides
    # a filing outside every link window is dropped
    late = scores.assign(filing_date=pd.Timestamp("2017-12-31") + pd.Timedelta(days=1))
    assert len(V.link_disclosures(late, cik_gvkey, ccm[ccm["linkenddt"].notna()])) == 0


def test_readability_is_bytes_not_megabytes():
    """Appendix B says megabytes; Table 3's own percentiles say bytes (see variables.readability)."""
    raw = b"x" * 6163418
    level, ln = V.readability(raw)
    assert level == 6163418 and abs(ln - 15.63) < 0.005          # Table 3 P50 pair
    # Table 3: percentiles of Risk section length and of its ln -- all five must map
    for n_sent, printed in ((1, 0.69), (138, 4.93), (226, 5.42), (346, 5.85), (841, 6.74)):
        n, n_ln = V.risk_section_length([object()] * n_sent)
        assert n == n_sent and abs(n_ln - printed) < 0.005, (n_sent, n_ln, printed)


# --- hand-computed checks added after the 2026-09-19 audit (EVALUATION.md 11.2 item 7) ---------------
def _monthly_panel(n=80, seed=3):
    f = factors(DATA_FF)
    months = pd.period_range("2005-01", periods=n, freq="M")
    rng = np.random.default_rng(seed)
    ret = f.loc[months, "RF"].values + 1.1 * f.loc[months, "Mkt-RF"].values + rng.normal(0, 0.03, n)
    df = pd.DataFrame({"permno": 1, "date": months.to_timestamp(how="end"), "ret": ret, "prc": 20.0, "shrout": 1000.0})
    return V.crsp_monthly_variables(df, f).reset_index(drop=True), f.loc[months].reset_index(drop=True)


def test_beta_ivol_coskew_windows_by_hand():
    """Row k uses months k-59..k (60 months ending at the row month) -- recomputed independently."""
    out, f = _monthly_panel()
    k = 75
    w = slice(k - 59, k)                                   # .loc is label-inclusive: 60 rows
    y = out.loc[w, "ret"].values - f.loc[w, "RF"].values
    mkt, smb, hml = f.loc[w, "Mkt-RF"].values, f.loc[w, "SMB"].values, f.loc[w, "HML"].values
    beta = np.polyfit(mkt, y, 1)[0]
    X3 = np.column_stack([np.ones_like(mkt), mkt, smb, hml]); b3 = np.linalg.lstsq(X3, y, rcond=None)[0]
    ivol = np.std(y - X3 @ b3, ddof=1)
    X2 = np.column_stack([np.ones_like(mkt), mkt, mkt ** 2]); cosk = np.linalg.lstsq(X2, y, rcond=None)[0][2]
    assert abs(out.loc[k, "beta"] - beta) < 1e-9
    assert abs(out.loc[k, "idiosyncratic_volatility"] - ivol) < 1e-9
    assert abs(out.loc[k, "coskew"] - cosk) < 1e-9
    assert np.isnan(out.loc[22, "beta"]) and not np.isnan(out.loc[23, "beta"])      # >= 24 months


def test_illiquidity_by_hand():
    days = pd.bdate_range("2010-03-01", "2010-03-31")
    ret = np.resize([0.01, -0.02, 0.03], len(days)); prc = np.resize([10.0, -12.0], len(days)); vol = np.resize([1000.0, 500.0, 2000.0], len(days))
    d = pd.DataFrame({"permno": 1, "date": days, "ret": ret, "prc": prc, "vol": vol})
    expect = np.mean(np.abs(ret) / (np.abs(prc) * vol))
    assert abs(V.crsp_daily_variables(d)["illiquidity"].iloc[0] - expect) < 1e-15


def test_ncskew_and_extr_sigma_by_hand():
    W = np.array([0.01, -0.03, 0.02, 0.00, -0.08, 0.015, 0.005, -0.01, 0.02, 0.03] * 3)
    weeks = pd.period_range("2012-01-02", periods=len(W), freq="W")
    out = V.crash_measures(pd.DataFrame({"permno": 1, "week": weeks, "W": W})).set_index("year")
    n, dev = len(W), W - W.mean()
    ncskew = -(n * (n - 1) ** 1.5 * np.sum(dev ** 3)) / ((n - 1) * (n - 2) * np.sum(dev ** 2) ** 1.5)
    extr = -(W.min() - W.mean()) / W.std(ddof=1)
    assert abs(out.loc[2012, "ncskew"] - ncskew) < 1e-12 and abs(out.loc[2012, "extr_sigma"] - extr) < 1e-12


def test_cash_flow_volatility_by_hand():
    """Firm rolling 5-year SD of (ib + dp - dvc)/at (at least 3 years), averaged over 2-digit SIC."""
    rows = []
    for g, sic, cf in ((1, 3571, [0.10, 0.12, 0.08, 0.11, 0.09]), (2, 3572, [0.05, 0.07, 0.06, 0.02, 0.04])):
        for i, x in enumerate(cf):
            rows.append({"gvkey": g, "fyear": 2010 + i, "sic": sic, "at": 100.0, "ceq": 50.0, "prcc_f": 10.0, "csho": 5.0,
                         "che": 1.0, "ib": 100 * x, "dp": 0.0, "dvc": 0.0, "oibdp": 1.0, "ppent": 1.0, "xrd": 0.0, "dltt": 0.0, "dlc": 0.0})
    c = V.compustat_variables(pd.DataFrame(rows))
    sd1, sd2 = np.std([0.10, 0.12, 0.08, 0.11, 0.09], ddof=1), np.std([0.05, 0.07, 0.06, 0.02, 0.04], ddof=1)
    got = c[c["fyear"] == 2014]["cash_flow_volatility_industry"].unique()
    assert len(got) == 1 and abs(got[0] - (sd1 + sd2) / 2) < 1e-12
    assert c[c["fyear"] == 2011]["cash_flow_volatility_industry"].isna().all()     # < 3 years


def test_secrets_window_boundary():
    """Pins the CURRENT rule: 'protect' may be up to 5 words away from the key phrase.  The paper's
    'within a five-word window' may mean at most 4 intervening words -- open item, EVALUATION 11.3."""
    assert V.secrets_dummy("protect a b c d e trade secrets") == 1
    assert V.secrets_dummy("protect a b c d e f trade secrets") == 0


# --- estimators in stats.py, each against a second implementation ------------------------------
def test_newey_west_matches_the_bartlett_formula():
    """nw_mean must be the textbook HAC mean: S = g0 + 2*sum (1 - l/(L+1)) * gl, var = S/n."""
    from cyberrisk.stats import nw_mean
    rng = np.random.default_rng(7)
    e = rng.normal(size=400); x = np.empty(400); x[0] = e[0]
    for i in range(1, 400):
        x[i] = 0.5 * x[i - 1] + e[i]                      # AR(1): HAC differs from OLS here
    L, n, dev = 12, len(x), x - x.mean()
    S = dev @ dev / n + 2 * sum((1 - l / (L + 1)) * (dev[l:] @ dev[:-l]) / n for l in range(1, L + 1))
    mean, t, k = nw_mean(x, lags=L)
    assert k == n and abs(mean - x.mean()) < 1e-12
    assert abs(t - x.mean() / np.sqrt(S / n)) < 1e-9


def test_logit_matches_an_independent_fit_and_cluster_sandwich():
    """stats.logit (statsmodels) against a hand-rolled likelihood and cluster sandwich.  The
    coefficient must agree to 1e-6; the standard error differs only by the two finite-sample
    factors statsmodels applies to a cluster covariance, (N - 1) / (N - k) and G / (G - 1)
    -- measured 2026-09-20."""
    from scipy import optimize
    from cyberrisk.stats import logit
    rng = np.random.default_rng(11)
    n_firms, T = 120, 8
    firm = np.repeat(np.arange(n_firms), T); year = np.tile(np.arange(T), n_firms)
    x = rng.normal(size=n_firms * T)
    p = 1 / (1 + np.exp(-(-1.5 + 0.8 * x + 0.3 * rng.normal(0, 1, n_firms)[firm])))
    d = pd.DataFrame({"firm": firm, "year": year, "x": x, "y": rng.binomial(1, p)})
    m = logit(d, "y", ["x"], fe=("year",), cluster="firm")

    X = np.column_stack([np.ones(len(d)), d["x"].values, pd.get_dummies(d["year"], drop_first=True, dtype=float).values])
    y = d["y"].values.astype(float)
    nll = lambda b: np.sum(np.log1p(np.exp(X @ b)) - y * (X @ b))
    grad = lambda b: X.T @ (1 / (1 + np.exp(-(X @ b))) - y)
    b = optimize.minimize(nll, np.zeros(X.shape[1]), jac=grad, method="BFGS", options={"maxiter": 2000}).x
    pr = 1 / (1 + np.exp(-(X @ b)))
    A = np.linalg.inv((X * (pr * (1 - pr))[:, None]).T @ X)
    u = X * (y - pr)[:, None]
    meat = sum(np.outer(u[d["firm"].values == f].sum(0), u[d["firm"].values == f].sum(0)) for f in d["firm"].unique())
    se_hand = np.sqrt((A @ meat @ A)[1, 1])
    n, k, G = len(d), X.shape[1], d["firm"].nunique()
    assert abs(m.params["x"] - b[1]) < 1e-6
    assert abs(m.bse["x"] / se_hand - np.sqrt((n - 1) / (n - k) * G / (G - 1))) < 1e-6
