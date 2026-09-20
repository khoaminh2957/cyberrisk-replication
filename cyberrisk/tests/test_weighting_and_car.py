"""Hand-computed checks of the two pieces of arithmetic that no synthetic test can pin down:
the buy-and-hold portfolio weights inside a holding period, and the market-model CAR alignment."""
import numpy as np
import pandas as pd

from cyberrisk.portfolios import holding_returns
from cyberrisk.stats import market_model_car


def _crsp(rets):
    return pd.DataFrame({"permno": [1, 1, 2, 2],
                         "month": [pd.Period("2010-01", "M"), pd.Period("2010-02", "M")] * 2,
                         "ret": rets})


def test_buy_and_hold_weights():
    crsp = _crsp([1.0, 0.0, 0.0, 0.5])          # stock 1: +100%, 0%.  stock 2: 0%, +50%
    ew = holding_returns(pd.DataFrame({"permno": [1, 2], "weight0": [0.5, 0.5]}),
                         crsp, pd.Timestamp("2009-12-31"), 2)
    # month 1: 0.5*1 + 0.5*0.  month 2: weights drift to (2/3, 1/3) -> 1/3 * 0.5
    assert abs(ew.iloc[0] - 0.5) < 1e-12 and abs(ew.iloc[1] - 1 / 6) < 1e-12
    vw = holding_returns(pd.DataFrame({"permno": [1, 2], "weight0": [0.8, 0.2]}),
                         crsp, pd.Timestamp("2009-12-31"), 2)
    assert abs(vw.iloc[0] - 0.8) < 1e-12 and abs(vw.iloc[1] - (0.2 / 1.8) * 0.5) < 1e-12


def test_delisted_stock_drops_out_and_weights_renormalise():
    crsp = _crsp([1.0, 0.0, 0.0, 0.5])
    crsp = crsp[~((crsp["permno"] == 1) & (crsp["month"] == pd.Period("2010-02", "M")))]
    r = holding_returns(pd.DataFrame({"permno": [1, 2], "weight0": [0.5, 0.5]}),
                        crsp, pd.Timestamp("2009-12-31"), 2)
    assert abs(r.iloc[1] - 0.5) < 1e-12          # only stock 2 remains, at weight 1


def test_market_model_car_alignment():
    days = pd.bdate_range("2020-01-01", "2021-01-29")
    rng = np.random.default_rng(0)
    mkt = pd.Series(rng.normal(0, 0.01, len(days)), index=days)
    d = pd.DataFrame({"permno": 1, "date": days, "ret": 0.001 + 1.5 * mkt.values})
    i = days.get_loc(pd.Timestamp("2020-12-14"))
    d.loc[[i - 1, i, i + 1, i + 2, i + 3], "ret"] += [0.01, -0.05, 0.0, 0.02, 0.0]
    out = market_model_car(d, mkt, "2020-12-14").iloc[0]
    assert abs(out["car_-1_1"] + 0.04) < 1e-9 and abs(out["car_-1_3"] + 0.02) < 1e-9
    missing = market_model_car(d.drop(index=i + 1), mkt, "2020-12-14").iloc[0]
    assert np.isnan(missing["car_-1_1"])          # an incomplete event window is not a CAR of zero


# --- the four silent bugs the 2026-09-20 audit found (EVALUATION.md 12.3) ---------------------
def test_a_missing_score_leaves_the_sort():
    """It used to fall through into portfolio 3 -- the leg the strategy buys."""
    from cyberrisk.portfolios import assign_terciles
    s = pd.DataFrame({"permno": [1, 2, 3, 4], "cyber_risk": [0.0, 0.2, 0.9, np.nan]})
    out = assign_terciles(s)
    assert out["permno"].tolist() == [1, 2, 3] and out["portfolio"].tolist() == [1, 2, 3]


def test_a_holding_month_with_no_returns_is_missing_not_zero():
    from cyberrisk.portfolios import holding_returns
    months = pd.period_range("2010-01", periods=3, freq="M")
    crsp = pd.DataFrame({"permno": [1] * 3, "month": months, "ret": [np.nan, 0.05, 0.05]})
    r = holding_returns(pd.DataFrame({"permno": [1], "weight0": [1.0]}), crsp, pd.Timestamp("2009-12-31"))
    assert np.isnan(r.iloc[0]) and abs(r.iloc[1] - 0.05) < 1e-12
    absent = holding_returns(pd.DataFrame({"permno": [999], "weight0": [1.0]}), crsp, pd.Timestamp("2009-12-31"))
    assert absent.isna().all()


def test_table10_drops_missing_factor_days_instead_of_returning_nan():
    from cyberrisk.factor import table10
    idx = pd.bdate_range("2010-01-01", periods=200)
    rng = np.random.default_rng(1)
    f = pd.DataFrame({c: rng.normal(0, .01, 200) for c in ["Mkt-RF", "SMB", "HML", "Mom", "RMW", "CMA"]}, index=idx)
    crf = pd.Series(rng.normal(0, .01, 200), index=idx); crf.iloc[7] = np.nan
    dummy = pd.Series(0, index=idx); dummy.iloc[::20] = 1
    t = table10(crf, dummy, f, lags=5)
    assert np.isfinite(t.select_dtypes("number").values).all()
    assert (t["n"] == 199).all()                       # the missing day is dropped and counted out


def test_absorbed_fixed_effects_are_charged_their_degrees_of_freedom():
    """ols_fe must match a least-squares-dummy-variable fit, as Stata's `areg, absorb()` does."""
    import statsmodels.api as sm
    from cyberrisk.stats import ols_fe
    rng = np.random.default_rng(3)
    F, T = 60, 8
    firm = np.repeat(np.arange(F), T); year = np.tile(np.arange(T), F)
    fe_f = rng.normal(0, 1, F)[firm]
    x = rng.normal(size=F * T) + 0.3 * fe_f
    d = pd.DataFrame({"firm": firm, "year": year, "x": x,
                      "y": 0.7 * x + fe_f + rng.normal(0, .5, T)[year] + rng.normal(0, 1, F * T)})
    a = ols_fe(d, "y", ["x"], fe=("firm", "year"), cluster="firm")
    X = pd.concat([d[["x"]], pd.get_dummies(d["firm"], prefix="f", drop_first=True, dtype=float),
                   pd.get_dummies(d["year"], prefix="t", drop_first=True, dtype=float)], axis=1)
    b = sm.OLS(d["y"], sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": d["firm"]})
    assert abs(a.params["x"] - b.params["x"]) < 1e-9
    assert abs(a.bse["x"] / b.bse["x"] - 1) < 1e-9
    assert a.df_resid == b.df_resid
