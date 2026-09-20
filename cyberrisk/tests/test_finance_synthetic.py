import os
import numpy as np
import pandas as pd
import pytest

from cyberrisk.tests.synthetic import make
from cyberrisk import portfolios as P, fama_macbeth as FM

DATA_FF = os.path.join(os.path.dirname(__file__), "..", "data", "ff")


@pytest.fixture(scope="module")
def econ():
    return make(data_dir=DATA_FF)


def test_tercile_assignment_p1_is_zero_scores():
    s = pd.DataFrame({"permno": range(6), "cyber_risk": [0, 0, 0.1, 0.2, 0.3, 0.4]})
    t = P.assign_terciles(s)
    assert t["portfolio"].tolist() == [1, 1, 2, 2, 3, 3]


def test_portfolio_returns_shape_and_planted_premium(econ):
    scores, crsp_m, f = econ
    ew = P.portfolio_returns(scores, crsp_m, "ew")
    assert list(ew.columns) == [1, 2, 3, "spread"]
    assert ew.index.min() == pd.Period("2008-03", "M") and ew.index.max() == pd.Period("2019-03", "M")
    assert len(ew) == 133                      # March 2008 .. March 2019
    tab = P.table7_panel_a(ew, f)
    assert tab.loc["spread", "excess_return"] > 0 and tab.loc["spread", "t_excess"] > 2
    assert tab.loc["spread", "ff5_alpha"] > 0
    vw = P.portfolio_returns(scores, crsp_m, "vw")
    assert vw.shape == ew.shape


def test_short_zero_firms_excluded():
    s = pd.DataFrame({"permno": [1, 1, 2, 2, 2, 3], "fyear": [2010, 2011, 2010, 2011, 2012, 2010],
                      "cyber_risk": [0, 0, 0, 0, 0, 0.2], "filing_date": pd.Timestamp("2011-03-01")})
    kept = P.exclude_short_zero_firms(s)
    assert set(kept["permno"]) == {2, 3}


def test_table8_double_sort(econ):
    scores, crsp_m, f = econ
    chars = crsp_m[["permno", "month", "me"]].copy()
    t = P.table8(scores, crsp_m, chars, "me", f)
    assert set(t.index) == {("LOW", "ew"), ("LOW", "vw"), ("HIGH", "ew"), ("HIGH", "vw")}
    assert (t["avg_return"] > 0).all()


def test_fama_macbeth_recovers_premium(econ):
    scores, crsp_m, f = econ
    chars = crsp_m[["permno", "month", "ret", "me"]].copy()
    chars["exret"] = chars["ret"] - chars["month"].map(f["RF"])
    chars["market_value_ln"] = np.log(chars["me"])
    panel = FM.stock_month_panel(scores, chars)
    res = FM.table9(panel, model="base", horizons=(1, 3))
    assert res[1].loc["cyber_risk", "coef"] > 0 and res[1].loc["cyber_risk", "t"] > 2
    assert set(res) == {1, 3}
