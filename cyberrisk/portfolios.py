"""Sections 4.1-4.2 of the paper: univariate (Table 7) and bivariate (Table 8) portfolio sorts.

Table 7: from December 2007, at the end of each quarter stocks are sorted on the cybersecurity
risk index into three groups -- P1 = stocks with no cybersecurity risk disclosure (score zero),
P2 / P3 = below / above the median of the remaining scores -- and tracked over the following
quarter.  Monthly returns March 2008 - March 2019, equal- and value-weighted, in excess of the
risk-free rate; CAPM, Carhart (FFC) and Fama-French five-factor alphas; Newey-West t-statistics
(12 lags).  Firms that are in the sample for less than 3 years with no cyber disclosure throughout
are excluded.  Panel B reports average portfolio characteristics.

Table 8: the same tercile sort intersected with an independent median split on a characteristic;
High-Low cyber-risk spread within each half.
"""
import numpy as np
import pandas as pd

from .stats import nw_mean, alpha, quantile_groups

CAPM, FFC, FF5 = ["Mkt-RF"], ["Mkt-RF", "SMB", "HML", "Mom"], ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
SAMPLE = (pd.Period("2008-03", "M"), pd.Period("2019-03", "M"))


def formation_dates(start="2007-12-31", end="2018-12-31", rebalance="Q"):
    """Quarter ends (paper); month ends / year ends for the IA7 panel L rebalancing check."""
    return pd.date_range(start, end, freq={"Q": "QE", "M": "ME", "A": "YE"}[rebalance])


HOLD_MONTHS = {"Q": 3, "M": 1, "A": 12}


def latest_score(scores, formation_date, max_age_days=366):
    """Each firm's most recent score filed on or before the formation date (a 10-K is annual, so
    a score older than a year means the firm has left the sample)."""
    s = scores[(scores["filing_date"] <= formation_date)
               & (scores["filing_date"] > formation_date - pd.Timedelta(days=max_age_days))]
    return s.sort_values("filing_date").groupby("permno").tail(1)


def exclude_short_zero_firms(scores, min_years=3):
    """Paper, Table 7 note: drop firms with < 3 years in the sample and zero disclosures throughout."""
    g = scores.groupby("permno")
    bad = g["fyear"].nunique().lt(min_years) & g["cyber_risk"].max().eq(0)
    return scores[~scores["permno"].isin(bad[bad].index)]


def assign_terciles(s, col="cyber_risk"):
    """P1 = zero score; P2/P3 split at the median of the positive scores."""
    s = s.copy()
    pos = s[s[col] > 0][col]
    med = pos.median() if len(pos) else np.inf
    s["portfolio"] = np.where(s[col] <= 0, 1, np.where(s[col] <= med, 2, 3))
    return s


def holding_returns(members, crsp_m, formation_date, n_months=3):
    """Monthly buy-and-hold returns of a portfolio over the n months after formation.
    members: DataFrame[permno, weight0]; crsp_m: DataFrame[permno, month(Period), ret]."""
    months = [(formation_date.to_period("M") + k) for k in range(1, n_months + 1)]
    r = crsp_m[crsp_m["permno"].isin(members["permno"]) & crsp_m["month"].isin(months)]
    r = r.pivot(index="month", columns="permno", values="ret").reindex(months)
    w = members.set_index("permno")["weight0"].reindex(r.columns).fillna(0.0)
    out = {}
    cum = pd.Series(1.0, index=r.columns)
    for m in months:
        ret = r.loc[m]
        wm = (w * cum).where(ret.notna(), 0.0)
        wm = wm / wm.sum() if wm.sum() > 0 else wm
        out[m] = float((wm * ret.fillna(0.0)).sum())
        cum = cum * (1 + ret.fillna(0.0))
    return pd.Series(out)


def portfolio_returns(scores, crsp_m, weighting="ew", col="cyber_risk", n_groups=3,
                      sample=SAMPLE, formation_start="2007-12-31", formation_end="2018-12-31",
                      rebalance="Q"):
    """Monthly returns of the cyber-risk portfolios.  crsp_m needs permno, month, ret, me
    (market value at month end).  Returns DataFrame indexed by month with one column per group."""
    scores = exclude_short_zero_firms(scores)
    cols = {}
    for fd in formation_dates(formation_start, formation_end, rebalance):
        s = latest_score(scores, fd)
        if s.empty:
            continue
        me = crsp_m[crsp_m["month"] == fd.to_period("M")].set_index("permno")["me"]
        s = s[s["permno"].isin(me.index)]
        s = assign_terciles(s, col) if n_groups == 3 else _quantile_groups(s, col, n_groups)
        for p, g in s.groupby("portfolio"):
            w = me.reindex(g["permno"]).fillna(0.0) if weighting == "vw" else pd.Series(1.0, index=g["permno"])
            members = pd.DataFrame({"permno": g["permno"].values, "weight0": (w / w.sum()).values})
            cols.setdefault(p, []).append(holding_returns(members, crsp_m, fd, HOLD_MONTHS[rebalance]))
    out = pd.DataFrame({p: pd.concat(v) for p, v in cols.items()}).sort_index()
    out = out.loc[sample[0]:sample[1]]
    out["spread"] = out[out.columns.max()] - out[1]
    return out


def _quantile_groups(s, col, n):
    """Quartile / quintile / decile sorts (§6.1): cut points on the full cross-section, ties
    (zero scores) share the lowest group."""
    s = s.copy()
    s["portfolio"] = quantile_groups(s[col], n).values
    return s


def table7_panel_a(port_ret, factors_m):
    """Excess returns and CAPM / FFC / FF5 alphas with Newey-West t-statistics for each portfolio
    and the spread (monthly, in percent)."""
    f = factors_m.reindex(port_ret.index)
    rows = {}
    for p in port_ret.columns:
        ex = port_ret[p] - (0 if p == "spread" else f["RF"])
        m, t, n = nw_mean(ex)
        row = {"excess_return": 100 * m, "t_excess": t, "n_months": n}
        for name, cols in (("capm", CAPM), ("ffc", FFC), ("ff5", FF5)):
            a, ta, _, _ = alpha(ex, f, cols)
            row[f"{name}_alpha"], row[f"t_{name}"] = 100 * a, ta
        rows[p] = row
    return pd.DataFrame(rows).T


def table7_panel_b(scores, characteristics, crsp_m, chars):
    """Average number of firms per portfolio and equally-weighted average characteristics."""
    scores = exclude_short_zero_firms(scores)
    rows = []
    for fd in formation_dates():
        s = latest_score(scores, fd)
        if s.empty:
            continue
        s = assign_terciles(s)
        c = characteristics[characteristics["month"] == fd.to_period("M")]
        s = s.merge(c[["permno"] + chars], on="permno", how="left")
        for p, g in s.groupby("portfolio"):
            rows.append({"portfolio": p, "n_firms": len(g), "cyber_risk": g["cyber_risk"].mean(),
                         **{k: g[k].mean() for k in chars}})
    return pd.DataFrame(rows).groupby("portfolio").mean()


def table8(scores, crsp_m, characteristics, char, factors_m):
    """Double sort on cyber risk terciles x median split of `char` (independent sorts each
    quarter).  Returns avg return and FF5 alpha of High-Low cyber risk within LOW / HIGH `char`,
    equal- and value-weighted."""
    scores = exclude_short_zero_firms(scores)
    out = {}
    for half in ("LOW", "HIGH"):
        for weighting in ("ew", "vw"):
            cols = {}
            for fd in formation_dates():
                s = latest_score(scores, fd)
                c = characteristics[characteristics["month"] == fd.to_period("M")][["permno", char]].dropna()
                if s.empty or c.empty:
                    continue
                med = c[char].median()
                keep = c[(c[char] <= med) if half == "LOW" else (c[char] > med)]["permno"]
                me = crsp_m[crsp_m["month"] == fd.to_period("M")].set_index("permno")["me"]
                s = assign_terciles(s[s["permno"].isin(me.index)])
                s = s[s["permno"].isin(keep)]
                for p in (1, 3):
                    g = s[s["portfolio"] == p]
                    if g.empty:
                        continue
                    w = me.reindex(g["permno"]).fillna(0.0) if weighting == "vw" else pd.Series(1.0, index=g["permno"])
                    members = pd.DataFrame({"permno": g["permno"].values, "weight0": (w / w.sum()).values})
                    cols.setdefault(p, []).append(holding_returns(members, crsp_m, fd))
            pr = pd.DataFrame({p: pd.concat(v) for p, v in cols.items()}).sort_index().loc[SAMPLE[0]:SAMPLE[1]]
            spread = (pr[3] - pr[1]).dropna()
            m, t, _ = nw_mean(spread)
            a, ta, _, _ = alpha(spread, factors_m.reindex(spread.index), FF5)
            out[(half, weighting)] = {"avg_return": 100 * m, "t_avg": t, "ff5_alpha": 100 * a, "t_ff5": ta}
    return pd.DataFrame(out).T
