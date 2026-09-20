"""Section 4.4 / Table 10 of the paper: a cybersecurity risk factor and its time-series variation.

Factor: at the end of each month, stocks are sorted into two size groups (median market value)
and, independently, into k cyber-risk groups (k = 5 benchmark; 3 and 10 for robustness).  The
factor is the average return of the two value-weighted high-cyber-risk portfolios minus the
average of the two value-weighted low-cyber-risk portfolios, daily, March 2008 - March 2019.

Regression (3): CRF_t = a + b * High_Google_SVI_dummy_t + g' X_t + e, X = none / CAPM / FFC /
FF5 daily factors, Newey-West t-statistics.  Placebos shift the dummy by one trading week and one
trading month after the SVI peak.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .portfolios import latest_score
from .stats import NW_LAGS, quantile_groups

CAPM, FFC, FF5 = ["Mkt-RF"], ["Mkt-RF", "SMB", "HML", "Mom"], ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]


def cyber_factor(scores, crsp_d, me_m, k=5, start="2008-03-01", end="2019-03-31"):
    """Daily factor returns.  scores: permno, filing_date, fyear, cyber_risk.  crsp_d: permno,
    date, ret.  me_m: DataFrame[permno, month(Period), me] month-end market value."""
    crsp_d = crsp_d.copy(); crsp_d["date"] = pd.to_datetime(crsp_d["date"])
    crsp_d["month"] = crsp_d["date"].dt.to_period("M")
    out = []
    for m in pd.period_range(pd.Period(start, "M") - 1, pd.Period(end, "M") - 1, freq="M"):
        fd = m.to_timestamp(how="end").normalize()
        s = latest_score(scores, fd)
        me = me_m[me_m["month"] == m].set_index("permno")["me"]
        s = s[s["permno"].isin(me.index)].copy()
        if len(s) < 2 * k:
            continue
        s["size"] = (me.reindex(s["permno"]).values > me.reindex(s["permno"]).median()).astype(int)
        s["cyber"] = quantile_groups(s["cyber_risk"], k).values
        s["me"] = me.reindex(s["permno"]).values
        nxt = crsp_d[crsp_d["month"] == m + 1]
        piv = nxt.pivot(index="date", columns="permno", values="ret")
        legs = {}
        for size in (0, 1):
            for cyber in (1, k):
                g = s[(s["size"] == size) & (s["cyber"] == cyber)]
                if g.empty:
                    legs[(size, cyber)] = pd.Series(np.nan, index=piv.index); continue
                w = pd.Series(g["me"].values, index=g["permno"].values)
                w = w.reindex(piv.columns).fillna(0.0)
                cum, rets = pd.Series(1.0, index=piv.columns), {}
                for d in piv.index:
                    r = piv.loc[d]
                    wd = (w * cum).where(r.notna(), 0.0)
                    rets[d] = float((wd / wd.sum() * r.fillna(0.0)).sum()) if wd.sum() > 0 else np.nan
                    cum = cum * (1 + r.fillna(0.0))
                legs[(size, cyber)] = pd.Series(rets)
        crf = (legs[(0, k)] + legs[(1, k)]) / 2 - (legs[(0, 1)] + legs[(1, 1)]) / 2
        out.append(crf)
    return pd.concat(out).sort_index().loc[start:end].rename("CRF")


def table10(crf, dummy, factors_d, lags=NW_LAGS, shift_days=0):
    """Eq. (3) for the four control sets.  `dummy` is a daily 0/1 Series (calendar days); it is
    aligned to trading days and, for the placebos, shifted forward by `shift_days` trading days."""
    df = pd.DataFrame({"CRF": crf}).join(factors_d, how="left")
    d = dummy.reindex(df.index).fillna(0).astype(int)
    df["High_Google_SVI_dummy"] = d.shift(shift_days).fillna(0).astype(int) if shift_days else d
    rows = {}
    for name, cols in (("NONE", []), ("CAPM", CAPM), ("FFC", FFC), ("FF-5", FF5)):
        x = df[["High_Google_SVI_dummy"] + cols].dropna()
        m = sm.OLS(df.loc[x.index, "CRF"], sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
        rows[name] = {"constant": m.params["const"], "t_constant": m.tvalues["const"],
                      "high_svi": m.params["High_Google_SVI_dummy"], "t_high_svi": m.tvalues["High_Google_SVI_dummy"],
                      "n": int(m.nobs)}
    return pd.DataFrame(rows).T


def cyber_beta(crsp_m_exret, crf_monthly, window=60, min_obs=24):
    """IA13: rolling 60-month betas of each stock's monthly excess return on the (monthly) cyber
    factor.  crsp_m_exret: DataFrame[permno, month, exret]; crf_monthly: Series by month."""
    out = []
    for permno, g in crsp_m_exret.sort_values("month").groupby("permno"):
        g = g.set_index("month")
        x = crf_monthly.reindex(g.index)
        y = g["exret"]
        for k in range(len(g)):
            yy, xx = y.iloc[max(0, k - window + 1):k + 1], x.iloc[max(0, k - window + 1):k + 1]
            ok = yy.notna() & xx.notna()
            if ok.sum() >= min_obs:
                b = np.polyfit(xx[ok].values, yy[ok].values, 1)[0]
                out.append({"permno": permno, "month": g.index[k], "cyber_beta": b})
    return pd.DataFrame(out)
