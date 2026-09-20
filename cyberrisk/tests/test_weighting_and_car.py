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
