"""Google Trends search volume index (SVI) for the search TOPICS "Hacker" and "Data breach"
(Section 4.4).  The paper: daily data only exist for query periods shorter than 9 months, so
daily series are downloaded in windows that overlap by 100 days and rescaled on the overlap;
abnormal SVI = daily SVI / median SVI of the past 2 weeks; an extreme-attention day has abnormal
SVI above the past-2-week mean plus n standard deviations (n = 1.5 benchmark, 2 robustness),
both estimated on a rolling basis.

Topic ids (Google "mid", from the Trends autocomplete API, 2026-09-09):
  Hacker /m/03j50    Data breach /m/03c18t5
No pytrends dependency: the two Trends API calls are made directly.
"""
import json
import time

import pandas as pd
import requests

TOPICS = {"hacker": "/m/03j50", "data breach": "/m/03c18t5"}
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
_EXPLORE = "https://trends.google.com/trends/api/explore"
_MULTILINE = "https://trends.google.com/trends/api/widgetdata/multiline"
WINDOW_DAYS, OVERLAP_DAYS = 240, 100        # < 9 months, 100-day overlap (paper)


class Trends:
    def __init__(self, geo="", hl="en-US", sleep=2.0):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = _UA
        self.geo, self.hl, self.sleep = geo, hl, sleep
        self.s.get("https://trends.google.com/trends/explore", timeout=30)   # sets the NID cookie

    def _get_json(self, url, params):
        for attempt in range(5):
            r = self.s.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(self.sleep * (2 ** attempt))
                continue
            r.raise_for_status()
            return json.loads(r.text.split("\n", 1)[1] if r.text.startswith(")]}'") else r.text)
        raise RuntimeError("Google Trends rate limit (429) persisted")

    def daily(self, mid, start, end):
        """Daily SVI (0-100) of one topic over a window shorter than 9 months."""
        req = {"comparisonItem": [{"keyword": mid, "geo": self.geo, "time": f"{start} {end}"}],
               "category": 0, "property": ""}
        w = self._get_json(_EXPLORE, {"hl": self.hl, "tz": 0, "req": json.dumps(req)})
        widget = next(x for x in w["widgets"] if x["id"] == "TIMESERIES")
        time.sleep(self.sleep)
        d = self._get_json(_MULTILINE, {"hl": self.hl, "tz": 0, "req": json.dumps(widget["request"]),
                                        "token": widget["token"]})
        rows = d["default"]["timelineData"]
        # epoch seconds -> dates via numpy: pd.to_datetime(unit="s") segfaults under pandas 2.3.3 /
        # Python 3.14 on this machine (2026-09-19)
        import numpy as np
        idx = pd.DatetimeIndex(np.array([int(r["time"]) for r in rows], dtype="datetime64[s]"))
        s = pd.Series([r["value"][0] for r in rows], index=idx, dtype=float)
        time.sleep(self.sleep)
        return s

    def daily_stitched(self, mid, start, end, window=WINDOW_DAYS, overlap=OVERLAP_DAYS):
        """Daily SVI over any period: overlapping windows rescaled on the overlap (paper §4.4)."""
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        pieces, a = [], start
        while a <= end:
            b = min(a + pd.Timedelta(days=window - 1), end)
            pieces.append(self.daily(mid, a.date().isoformat(), b.date().isoformat()))
            if b >= end:
                break
            a = b - pd.Timedelta(days=overlap - 1)
        return stitch(pieces)


def stitch(pieces):
    """Chain overlapping daily series: each new piece is scaled so that its mean over the overlap
    equals the mean of the already-stitched series over the same days."""
    out = pieces[0].copy()
    for p in pieces[1:]:
        common = out.index.intersection(p.index)
        prev, cur = out.loc[common].mean(), p.loc[common].mean()
        scale = prev / cur if cur > 0 else 1.0
        p = p * scale
        out = pd.concat([out, p.loc[p.index.difference(out.index)]]).sort_index()
    return out


def abnormal_svi(svi, lookback_days=14):
    """Daily SVI scaled by the median SVI of the past `lookback_days` (2 weeks; 4 weeks = 28)."""
    med = svi.shift(1).rolling(lookback_days, min_periods=lookback_days // 2).median()
    return svi / med


def high_svi_dummy(abn, n_sd=1.5, lookback_days=14):
    """1 on days when abnormal SVI > rolling past-2-week mean + n_sd * rolling past-2-week std."""
    m = abn.shift(1).rolling(lookback_days, min_periods=lookback_days // 2).mean()
    s = abn.shift(1).rolling(lookback_days, min_periods=lookback_days // 2).std()
    return (abn > m + n_sd * s).astype(int)


def joint_dummy(svis, n_sd=1.5, lookback_days=14):
    """The paper reports the dummy "using both 'hacker' and 'data breach' topics jointly"; here
    a day is extreme when either topic is extreme (the paper does not define 'jointly'; results
    per topic are similar, it says).  svis: {topic: daily SVI Series}."""
    ds = [high_svi_dummy(abnormal_svi(s, lookback_days), n_sd, lookback_days) for s in svis.values()]
    return pd.concat(ds, axis=1).max(axis=1).astype(int)
