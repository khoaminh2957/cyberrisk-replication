"""Estimators the paper uses, as thin wrappers on statsmodels:
  Newey-West t-statistics (12 lags, footnote 11) for portfolio means and Fama-MacBeth slopes,
  OLS with fixed effects and firm-clustered standard errors (Tables 4, 5),
  logit with firm-clustered standard errors (Tables 6, 12),
  Fama-MacBeth (1973) cross-sectional regressions (Table 9),
  the market model for cumulative abnormal returns (Table 11).
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

NW_LAGS = 12


def nw_mean(x, lags=NW_LAGS):
    """Mean of a series with a Newey-West (HAC) t-statistic.  Returns (mean, t, n)."""
    x = pd.Series(x).dropna().astype(float)
    if len(x) < 3:
        return float("nan"), float("nan"), len(x)
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(m.params[0]), float(m.tvalues[0]), len(x)


def alpha(excess_returns, factors_df, cols, lags=NW_LAGS):
    """Intercept (alpha) and its Newey-West t from a time-series regression on factor columns."""
    df = pd.concat([pd.Series(excess_returns, name="y"), factors_df[cols]], axis=1, join="inner").dropna()
    m = sm.OLS(df["y"], sm.add_constant(df[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(m.params["const"]), float(m.tvalues["const"]), len(df), m


def quantile_groups(x, k):
    """Sort into k groups on cut points at the 1/k .. (k-1)/k quantiles of x; a value equal to a
    cut point goes to the lower group, so tied values (the zero scores) share a group.  Returns
    integers 1..k (a group can be empty when ties straddle a cut point)."""
    x = pd.Series(x, dtype=float)
    cuts = x.quantile([j / k for j in range(1, k)]).values
    return pd.Series(1 + (x.values[:, None] > cuts[None, :]).sum(axis=1), index=x.index)


def standardize(df, cols):
    """Demean and divide by the standard deviation (the paper standardizes regressors in
    Tables 5, 6, 9, 12)."""
    out = df.copy()
    for c in cols:
        out[c] = (out[c] - out[c].mean()) / out[c].std()
    return out


def winsorize_by_year(df, cols, year_col="fyear", lo=0.01, hi=0.99):
    """Table 3: continuous variables winsorized at the 1st/99th percentiles, by year."""
    out = df.copy()
    for c in cols:
        q = out.groupby(year_col)[c].transform(lambda s: s.clip(s.quantile(lo), s.quantile(hi)))
        out[c] = q
    return out


def _demean(df, cols, fe):
    """Within transformation for one or two sets of fixed effects (alternating projections)."""
    x = df[cols].astype(float).copy()
    if len(fe) == 1:
        return x - x.groupby(df[fe[0]]).transform("mean") + x.mean()
    for _ in range(50):
        prev = x.copy()
        for f in fe:
            x = x - x.groupby(df[f]).transform("mean")
        if (x - prev).abs().max().max() < 1e-10:
            break
    return x + df[cols].astype(float).mean()


def ols_fe(df, y, xs, fe=(), cluster=None):
    """OLS of y on xs with fixed effects `fe` (absorbed) and standard errors clustered on
    `cluster`.  Returns the fitted statsmodels result (params, tvalues, rsquared...).

    The within transformation hides the absorbed dummies from statsmodels, which would then divide
    by N - k with k counting only the surviving regressors and report standard errors that are too
    small (measured: t inflated 5.7% on a 200-firm x 10-year panel).  The covariance is rescaled and
    df_resid set so the result matches a least-squares-dummy-variable fit, which is what the
    authors' own `areg, absorb(gvkey)` does (EVALUATION.md 12.3 #4, 13.2)."""
    d = df[list(dict.fromkeys([y, *xs, *fe] + ([cluster] if cluster else [])))].dropna()
    w = _demean(d, [y] + list(xs), list(fe)) if fe else d[[y] + list(xs)].astype(float)
    kw = {"cov_type": "cluster", "cov_kwds": {"groups": pd.factorize(d[cluster])[0]}} if cluster else {}
    res = sm.OLS(w[y], sm.add_constant(w[list(xs)])).fit(**kw)
    if fe:
        k_fe = sum(d[f].nunique() - 1 for f in fe)
        n, k = int(res.nobs), len(res.params)
        if n - k - k_fe > 0:
            r = res._results                      # the wrapper delegates; the fields live here
            r.cov_params_default = r.cov_params_default * ((n - k) / (n - k - k_fe))
            r.df_resid = n - k - k_fe
            r._cache.pop("bse", None); r._cache.pop("tvalues", None); r._cache.pop("pvalues", None)
    return res


def logit(df, y, xs, fe=(), cluster=None):
    """Logit of a 0/1 outcome on xs with fixed-effect dummies `fe` and clustered standard errors."""
    d = df[list(dict.fromkeys([y, *xs, *fe] + ([cluster] if cluster else [])))].dropna()
    X = d[list(xs)].astype(float)
    for f in fe:
        X = X.join(pd.get_dummies(d[f], prefix=f, drop_first=True, dtype=float))
    kw = {"cov_type": "cluster", "cov_kwds": {"groups": pd.factorize(d[cluster])[0]}} if cluster else {}
    return sm.Logit(d[y].astype(float), sm.add_constant(X)).fit(disp=0, maxiter=200, **kw)


def fama_macbeth(panel, y, xs, date_col="date", lags=NW_LAGS, min_obs=30):
    """Fama-MacBeth: a cross-sectional OLS per date, then the time-series mean of each slope with
    a Newey-West t-statistic.  Returns DataFrame[coef, t, n_periods] indexed by regressor."""
    rows = []
    for dt, g in panel.groupby(date_col):
        g = g[[y] + list(xs)].dropna()
        if len(g) < min_obs:
            continue
        b = sm.OLS(g[y], sm.add_constant(g[list(xs)])).fit().params
        rows.append(b.rename(dt))
    slopes = pd.DataFrame(rows)
    out = {}
    for c in slopes.columns:
        m, t, n = nw_mean(slopes[c], lags)
        out[c] = {"coef": m, "t": t, "n_periods": n}
    return pd.DataFrame(out).T, slopes


def market_model_car(daily, market, event_date, est_window=(-250, -30), windows=((-1, 1), (-1, 3))):
    """CARs from the market model.  daily: DataFrame[permno, date, ret]; market: Series of market
    returns indexed by date.  Trading-day offsets are relative to `event_date` (day 0)."""
    dates = market.index.sort_values()
    if pd.Timestamp(event_date) not in dates:
        raise ValueError("event date is not a trading day in the market series")
    pos = dates.get_loc(pd.Timestamp(event_date))
    day_of = pd.Series(np.arange(len(dates)) - pos, index=dates)
    d = daily.copy()
    d["tau"] = d["date"].map(day_of)
    d["mkt"] = d["date"].map(market)
    out = []
    for permno, g in d.dropna(subset=["tau"]).groupby("permno"):
        est = g[(g["tau"] >= est_window[0]) & (g["tau"] <= est_window[1])].dropna(subset=["ret", "mkt"])
        if len(est) < 60:
            continue
        b = sm.OLS(est["ret"], sm.add_constant(est["mkt"])).fit().params
        row = {"permno": permno}
        for lo, hi in windows:
            ev = g[(g["tau"] >= lo) & (g["tau"] <= hi)]
            if ev["ret"].isna().any() or len(ev) < hi - lo + 1:
                row[f"car_{lo}_{hi}"] = np.nan
            else:
                row[f"car_{lo}_{hi}"] = float((ev["ret"] - (b["const"] + b["mkt"] * ev["mkt"])).sum())
        out.append(row)
    return pd.DataFrame(out)
