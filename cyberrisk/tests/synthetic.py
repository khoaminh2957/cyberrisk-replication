"""A small synthetic economy with a planted cyber-risk premium, used to check that every
finance routine recovers what was planted and returns the table shapes the paper reports."""
import numpy as np
import pandas as pd

from cyberrisk.factors_ff import factors


def make(seed=0, n_firms=200, data_dir=None, premium=0.01, start="2006-01", end="2019-12"):
    rng = np.random.default_rng(seed)
    months = pd.period_range(start, end, freq="M")
    f = factors(data_dir).reindex(months)
    permnos = np.arange(1, n_firms + 1)
    # one score per firm-year, filed ~ 3 months after fiscal year end (Dec FYE); zero share falls over time
    rows = []
    for p in permnos:
        base = rng.uniform(0, 0.6)
        for fy in range(2006, 2019):
            zero = rng.uniform() < max(0.05, 0.6 - 0.05 * (fy - 2006))
            score = 0.0 if zero else float(np.clip(base + rng.normal(0, 0.05), 0.01, 0.7))
            rows.append({"permno": p, "fyear": fy, "cyber_risk": score,
                         "filing_date": pd.Timestamp(f"{fy + 1}-03-01") + pd.Timedelta(days=int(rng.integers(0, 25)))})
    scores = pd.DataFrame(rows)
    z = scores.copy(); z["z"] = (z["cyber_risk"] - z["cyber_risk"].mean()) / z["cyber_risk"].std()
    beta = rng.uniform(0.5, 1.5, n_firms)
    me0 = np.exp(rng.normal(12, 1.5, n_firms))
    recs = []
    for i, p in enumerate(permnos):
        sc = z[z["permno"] == p].set_index("fyear")["z"]
        me = me0[i]
        for m in months:
            fy = m.year - 1 if m.month <= 3 else m.year      # score known after the March filing
            zz = sc.get(fy, 0.0)
            r = f.loc[m, "RF"] + beta[i] * f.loc[m, "Mkt-RF"] + premium * zz + rng.normal(0, 0.08)
            me *= (1 + r)
            recs.append({"permno": p, "month": m, "ret": r, "me": me, "prc": me / 1e6, "shrout": 1e6})
    crsp_m = pd.DataFrame(recs)
    crsp_m["date"] = crsp_m["month"].dt.to_timestamp(how="end").dt.normalize()
    return scores, crsp_m, f
