"""Appendix B of the paper: variable definitions.  Compustat item names in brackets follow the
paper.  Each function takes the WRDS extract(s) it needs and returns a keyed DataFrame.

  comp   Compustat annual: gvkey, fyear, datadate, cik, sic, at, ceq, prcc_f, csho, che, ib, dp,
         dvc, oibdp, ppent, xrd, dltt, dlc
  crsp_m CRSP monthly: permno, date (month end), ret, prc, shrout
  crsp_d CRSP daily:   permno, date, ret, prc, vol
  tr13f  Thomson-Reuters 13F: permno, rdate, mgrno, shares      (institutional ownership)
  boardex BoardEx: gvkey, fyear, n_directors, n_independent, committee_names
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .extract import split_sentences


# --- §2.2 link: 10-K (CIK) -> Compustat (gvkey) -> CRSP (permno) -------------------------------
def link_disclosures(scores, cik_gvkey, ccm):
    """Paper §2.2: "we link each firm's cybersecurity risk disclosures with Compustat using the
    fiscal year, the CIK, and the mapping table from the WRDS SEC Analytics suite", and Compustat
    to CRSP through the CCM link.

    scores:    output of measure.cybersecurity_risk (firm = CIK, fiscal_year, filing_date, ...)
    cik_gvkey: DataFrame[cik, gvkey, fyear]        (WRDS SEC Analytics / Compustat)
    ccm:       DataFrame[gvkey, permno, linkdt, linkenddt]   (CRSP-Compustat link, primary links)
    Returns the scores with gvkey, permno, fyear -- the key the finance modules expect."""
    s = scores.rename(columns={"firm": "cik", "fiscal_year": "fyear"}).copy()
    s["cik"] = s["cik"].astype(str).str.lstrip("0")
    m = cik_gvkey.copy(); m["cik"] = m["cik"].astype(str).str.lstrip("0")
    out = s.merge(m[["cik", "gvkey", "fyear"]], on=["cik", "fyear"], how="inner")
    out = out.merge(ccm[["gvkey", "permno", "linkdt", "linkenddt"]], on="gvkey", how="inner")
    ok = (out["filing_date"] >= pd.to_datetime(out["linkdt"])) & \
         (out["filing_date"] <= pd.to_datetime(out["linkenddt"]).fillna(pd.Timestamp.max))
    return out[ok].drop(columns=["linkdt", "linkenddt"]).reset_index(drop=True)


# --- Compustat -----------------------------------------------------------------------------
def compustat_variables(comp):
    c = comp.sort_values(["gvkey", "fyear"]).copy()
    first = c.groupby("gvkey")["fyear"].transform("min")
    c["firm_size"] = c["at"]
    c["firm_size_ln"] = np.log(c["at"])
    c["firm_age"] = c["fyear"] - first + 1
    c["firm_age_ln"] = np.log(c["firm_age"])
    c["mve"] = c["prcc_f"] * c["csho"]
    c["tobins_q"] = (c["at"] - c["ceq"] + c["mve"]) / c["at"]
    c["roa"] = c["oibdp"] / c["at"]
    c["tangibility"] = c["ppent"] / c["at"]
    c["rd_expenditures"] = c["xrd"].fillna(0) / c["at"]
    c["cash_holdings"] = c["che"] / c["at"]
    c["leverage"] = (c["dltt"].fillna(0) + c["dlc"].fillna(0)) / c["at"]
    c["book_to_market"] = c["ceq"] / c["mve"]
    c["asset_growth"] = c.groupby("gvkey")["at"].pct_change()
    # cash flow volatility (industry): 2-digit SIC average of the firm's rolling 5-year std of CFO/at
    cfo = (c["ib"] + c["dp"] - c["dvc"].fillna(0)) / c["at"]
    c["cfo_vol"] = cfo.groupby(c["gvkey"]).transform(lambda s: s.rolling(5, min_periods=3).std())
    c["sic2"] = c["sic"].astype(str).str[:2]
    c["cash_flow_volatility_industry"] = c.groupby(["sic2", "fyear"])["cfo_vol"].transform("mean")
    return c


# --- 10-K text ---------------------------------------------------------------------------
_SECRET_KEYS = r"(trade secrets?|confidential information|proprietary information)"
_PROTECT = r"(protect|protection|safeguard)"


def secrets_dummy(text_10k):
    """Secrets = 1 if a key phrase occurs with protect/protection/safeguard within five words
    before or after it."""
    import re
    pat = re.compile(r"\b%s\b(?:\W+\w+){0,5}?\W+%s\b|\b%s\b(?:\W+\w+){0,5}?\W+%s\b"
                     % (_PROTECT, _SECRET_KEYS, _SECRET_KEYS, _PROTECT), re.I)
    return int(bool(pat.search(text_10k)))


def risk_section_length(item_1a_sentences):
    """Number of sentences in Item 1A (Appendix B) and its log.  The paper does not state the log
    transform; Table 3 fixes it: the five percentiles of "Risk section length" (1, 138, 226, 346,
    841) map to the printed "Risk section length (ln)" row (0.69, 4.93, 5.42, 5.85, 6.74) under
    ln(1 + n) and NOT under ln(n) (ln 1 = 0.00, ln 841 = 6.73) -- audit 2026-09-19."""
    n = len(item_1a_sentences) if not isinstance(item_1a_sentences, str) else len(split_sentences(item_1a_sentences))
    return n, float(np.log1p(n))


def readability(complete_submission_bytes):
    """File size of the SEC "complete submission text file" (Appendix B).

    Appendix B says "file size in megabytes", but Table 3 reports the level in BYTES: all five of
    its Readability percentiles equal the exponential of the matching Readability (ln) percentile
    when read as bytes -- P1 384,975 -> 12.86, P25 1,865,855 -> 14.44, P50 6,163,418 -> 15.63,
    P75 15,323,736 -> 16.54, P99 52,900,376 -> 17.78, all exact to the two decimals printed.  In
    megabytes ln(P50) would be 1.82, not 15.63.  So the level is bytes and the log is ln(bytes)."""
    n = len(complete_submission_bytes)
    return n, np.log(n)


# --- ownership / governance -------------------------------------------------------------------
def institutional_ownership(tr13f, shrout):
    """Shares held by 13F institutions owning more than 5% of the firm / shares outstanding.
    tr13f: permno, rdate, mgrno, shares; shrout: DataFrame[permno, rdate, shrout] (same units)."""
    h = tr13f.merge(shrout, on=["permno", "rdate"])
    h["frac"] = h["shares"] / h["shrout"]
    big = h[h["frac"] > 0.05]
    io = big.groupby(["permno", "rdate"])["frac"].sum().rename("institutional_ownership").reset_index()
    return io


def governance(boardex):
    b = boardex.copy()
    b["independent_directors"] = b["n_independent"] / b["n_directors"]
    b["risk_committee"] = b["committee_names"].fillna("").str.contains("risk", case=False).astype(int)
    return b[["gvkey", "fyear", "independent_directors", "risk_committee"]]


# --- CRSP monthly ---------------------------------------------------------------------------
def crsp_monthly_variables(crsp_m, factors_m):
    """beta (60-month rolling), momentum (t-11..t-1: "11 months ending one day prior to month t",
    Appendix B, read literally), reversal (month t itself; see the comment below), idiosyncratic volatility
    (FF3 residual std over the prior 5 years), coskewness (>= 24 months), market value (ln).
    factors_m: monthly factor DataFrame from factors_ff.factors (period index)."""
    m = crsp_m.sort_values(["permno", "date"]).copy()
    m["month"] = pd.to_datetime(m["date"]).dt.to_period("M")
    f = factors_m.copy()
    m = m.merge(f[["Mkt-RF", "SMB", "HML", "RF"]], left_on="month", right_index=True, how="left")
    m["exret"] = m["ret"] - m["RF"]
    m["mkt2"] = m["Mkt-RF"] ** 2
    m["market_value"] = m["prc"].abs() * m["shrout"]
    m["market_value_ln"] = np.log(m["market_value"])
    # Row t predicts the return of month t+1 (fama_macbeth.table9).  Reversal = "the stock returns
    # over the previous month" = r(t); momentum = r(t-11..t-1): the two do not overlap, and relative
    # to the predicted month t+1 they are the usual t-1 / t-12..t-2 pair (audit 2026-09-19).
    m["reversal"] = m["ret"]
    lr = np.log1p(m["ret"])
    m["momentum"] = np.expm1(lr.groupby(m["permno"]).transform(lambda s: s.shift(1).rolling(11, min_periods=11).sum()))

    def rolling_stats(g):
        out = pd.DataFrame(index=g.index, columns=["beta", "idiosyncratic_volatility", "coskew"], dtype=float)
        vals = g[["exret", "Mkt-RF", "SMB", "HML", "mkt2"]].values
        for k in range(len(g)):
            w = vals[max(0, k - 59):k + 1]
            w = w[~np.isnan(w).any(axis=1)]
            if len(w) >= 24:
                X1 = sm.add_constant(w[:, 1]); b1 = np.linalg.lstsq(X1, w[:, 0], rcond=None)[0]
                out.iat[k, 0] = b1[1]
                X3 = sm.add_constant(w[:, 1:4]); b3 = np.linalg.lstsq(X3, w[:, 0], rcond=None)[0]
                out.iat[k, 1] = np.std(w[:, 0] - X3 @ b3, ddof=1)
                X2 = sm.add_constant(w[:, [1, 4]]); b2 = np.linalg.lstsq(X2, w[:, 0], rcond=None)[0]
                out.iat[k, 2] = b2[2]
        return out

    stats = m.groupby("permno", group_keys=False).apply(rolling_stats, include_groups=False)
    m = m.join(stats)
    return m.drop(columns=["mkt2"])


# --- CRSP daily -----------------------------------------------------------------------------
def crsp_daily_variables(crsp_d):
    """Illiquidity (Amihud, monthly average of |ret| / dollar volume, >= 15 days) and MAX (mean of
    the five highest daily returns in the month)."""
    d = crsp_d.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["month"] = d["date"].dt.to_period("M")
    d["dvol"] = d["prc"].abs() * d["vol"]
    d["amihud"] = d["ret"].abs() / d["dvol"].replace(0, np.nan)
    g = d.groupby(["permno", "month"])
    out = g.agg(n=("ret", "count"), illiquidity=("amihud", "mean"),
                max5=("ret", lambda s: s.nlargest(5).mean())).reset_index()
    out.loc[out["n"] < 15, "illiquidity"] = np.nan
    return out.rename(columns={"max5": "max"})


def weekly_firm_specific_returns(crsp_d, market_d):
    """Firm-specific weekly returns: residual of weekly simple returns (daily returns compounded
    within the week) on the market's weekly return with two leads and two lags (Chen, Hong and
    Stein 2001), W = ln(1 + residual).
    market_d: Series of daily market returns indexed by date."""
    d = crsp_d.copy(); d["date"] = pd.to_datetime(d["date"])
    d["week"] = d["date"].dt.to_period("W")
    wk = d.groupby(["permno", "week"])["ret"].apply(lambda s: np.prod(1 + s) - 1).rename("ret").reset_index()
    mk = (1 + market_d).groupby(market_d.index.to_period("W")).prod() - 1
    out = []
    for permno, g in wk.groupby("permno"):
        g = g.set_index("week")["ret"].to_frame()
        X = pd.DataFrame({f"m{k}": mk.shift(-k) for k in (-2, -1, 0, 1, 2)}).reindex(g.index)
        df = g.join(X).dropna()
        if len(df) < 26:
            continue
        b = np.linalg.lstsq(sm.add_constant(df.drop(columns="ret").values), df["ret"].values, rcond=None)[0]
        res = df["ret"].values - sm.add_constant(df.drop(columns="ret").values) @ b
        out.append(pd.DataFrame({"permno": permno, "week": df.index, "W": np.log1p(res)}))
    return pd.concat(out, ignore_index=True)


def crash_measures(weekly):
    """NCSKEW and EXTR_SIGMA per firm-year from firm-specific weekly returns W."""
    w = weekly.copy()
    w["year"] = w["week"].dt.year

    def f(s):
        s = s.dropna().values
        n = len(s)
        if n < 26:
            return pd.Series({"ncskew": np.nan, "extr_sigma": np.nan})
        dev = s - s.mean()
        ncskew = -(n * (n - 1) ** 1.5 * np.sum(dev ** 3)) / ((n - 1) * (n - 2) * np.sum(dev ** 2) ** 1.5)
        extr = -(s.min() - s.mean()) / s.std(ddof=1)
        return pd.Series({"ncskew": ncskew, "extr_sigma": extr})
    return w.groupby(["permno", "year"])["W"].apply(f).unstack().reset_index()
