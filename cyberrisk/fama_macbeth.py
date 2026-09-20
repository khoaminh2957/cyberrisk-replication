"""Section 4.3 / Table 9 of the paper: Fama-MacBeth cross-sectional regressions of monthly excess
returns (1 to 12 months ahead) on the lagged cybersecurity risk index and standardized controls:
beta, market value, book-to-market, momentum, reversal, illiquidity, coskewness, idiosyncratic
volatility, asset growth, ROA, R&D expenditures, MAX, risk section length (ln), readability (ln).
"""
import pandas as pd

from .stats import fama_macbeth, standardize

CONTROLS = ["beta", "market_value_ln", "book_to_market", "momentum", "reversal", "illiquidity",
            "coskew", "idiosyncratic_volatility", "asset_growth", "roa", "rd_expenditures", "max"]
TEXT_CONTROLS = ["risk_section_length_ln", "readability_ln"]
HORIZONS = (1, 2, 3, 6, 9, 12)


def stock_month_panel(scores, characteristics):
    """One row per stock-month: the score from the most recent 10-K filed on or before the month's
    last day (at most 366 days earlier), the month's characteristics and the risk-free rate.
    scores: permno, filing_date, cyber_risk, risk_section_length_ln, readability_ln.
    characteristics: permno, month, controls..."""
    c = characteristics.copy()
    c["month_end"] = c["month"].dt.to_timestamp(how="end").dt.normalize()
    s = scores.sort_values("filing_date")
    p = pd.merge_asof(c.sort_values("month_end"), s, left_on="month_end", right_on="filing_date",
                      by="permno", direction="backward", tolerance=pd.Timedelta(days=366))
    return p.dropna(subset=["cyber_risk"])


def table9(panel, model="full", horizons=HORIZONS, standardize_within_month=True):
    """panel from stock_month_panel with column `exret` (monthly return minus RF).  For each
    horizon h the dependent variable is exret at month t+h.  Returns {h: DataFrame[coef, t]}."""
    xs = ["cyber_risk"] + (CONTROLS if model in ("controls", "full") else []) + (TEXT_CONTROLS if model == "full" else [])
    p = panel.sort_values(["permno", "month"]).copy()
    if standardize_within_month:
        p[xs] = p.groupby("month")[xs].transform(lambda s: (s - s.mean()) / s.std())
    else:
        p = standardize(p, xs)
    out = {}
    for h in horizons:
        p["y"] = p.groupby("permno")["exret"].shift(-h)
        # months must be consecutive for the shift to mean h months ahead
        gap = p.groupby("permno")["month"].shift(-h).astype("int64") - p["month"].astype("int64")
        p.loc[gap != h, "y"] = float("nan")
        res, _ = fama_macbeth(p.dropna(subset=["y"]), "y", xs, date_col="month")
        out[h] = res
    return out
