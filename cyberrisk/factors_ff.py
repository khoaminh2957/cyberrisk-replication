"""Kenneth French data library: Fama-French 5 factors (2x3), momentum, 12/48 industry portfolios
and SIC-code industry definitions, at monthly and daily frequency.  Used for CAPM / FFC / FF5
alphas (Table 7-8), the daily factor regressions (Table 10), industry adjustment (IA7 F-H) and the
Fama-French 12 / 48 industry classification (Fig. 2, §6.1).
"""
import io
import os
import re
import zipfile

import pandas as pd
import requests

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FILES = {
    "ff5_monthly": "F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "ff5_daily": "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
    "mom_monthly": "F-F_Momentum_Factor_CSV.zip",
    "mom_daily": "F-F_Momentum_Factor_daily_CSV.zip",
    "ind12_monthly": "12_Industry_Portfolios_CSV.zip",
    "ind48_monthly": "48_Industry_Portfolios_CSV.zip",
    "sic12": "Siccodes12.zip",
    "sic48": "Siccodes48.zip",
}


def download(name, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, FILES[name])
    if not os.path.exists(path):
        r = requests.get(BASE + FILES[name], headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
        r.raise_for_status()
        open(path, "wb").write(r.content)
    return path


def _csv_sections(zip_path):
    """Ken French CSVs hold several blank-line-separated tables; yield (title, DataFrame)."""
    z = zipfile.ZipFile(zip_path)
    text = z.read(z.namelist()[0]).decode("latin-1")
    blocks = re.split(r"\n\s*\n", text)
    title = ""
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        if not lines:
            continue
        # a data table starts with a header line beginning with a comma
        k = next((i for i, l in enumerate(lines) if l.startswith(",")), None)
        if k is None:
            title = lines[-1].strip()
            continue
        if k > 0:
            title = lines[k - 1].strip()
        df = pd.read_csv(io.StringIO("\n".join(lines[k:])), index_col=0)
        df.index = df.index.astype(str).str.strip()
        yield title, df
        title = ""


def _dated(df, daily):
    df = df[df.index.str.fullmatch(r"\d{8}" if daily else r"\d{6}")]
    df.index = pd.to_datetime(df.index, format="%Y%m%d" if daily else "%Y%m")
    if not daily:
        df.index = df.index.to_period("M")
    df = df.astype(float).replace([-99.99, -999.0], float("nan"))
    df.columns = [c.strip() for c in df.columns]
    return df / 100.0                       # percent -> decimal


def factors(data_dir, daily=False):
    """DataFrame [Mkt-RF, SMB, HML, RMW, CMA, RF, Mom] in decimals, indexed by day or month."""
    ff5 = next(_csv_sections(download("ff5_daily" if daily else "ff5_monthly", data_dir)))[1]
    mom = next(_csv_sections(download("mom_daily" if daily else "mom_monthly", data_dir)))[1]
    out = _dated(ff5, daily).join(_dated(mom, daily), how="left")
    return out


def industry_portfolios(data_dir, n=12, weighted="value"):
    """Monthly returns of the 12 or 48 industry portfolios (value- or equal-weighted)."""
    key = "ind12_monthly" if n == 12 else "ind48_monthly"
    want = "Value Weighted" if weighted == "value" else "Equal Weighted"
    for title, df in _csv_sections(download(key, data_dir)):
        if want in title and "Monthly" in title:
            return _dated(df, daily=False)
    raise ValueError("industry table not found")


def sic_map(data_dir, n=12):
    """SIC code -> Fama-French industry number (1..n).  Codes not listed map to the last
    industry ('Other')."""
    z = zipfile.ZipFile(download("sic12" if n == 12 else "sic48", data_dir))
    ranges, cur = [], None
    for line in z.read(z.namelist()[0]).decode("latin-1").splitlines():
        m = re.match(r"^\s*(\d+)\s+(\w+)", line)
        if m:
            cur = int(m.group(1)); continue
        r = re.match(r"^\s*(\d{4})-(\d{4})", line)
        if r and cur is not None:
            ranges.append((int(r.group(1)), int(r.group(2)), cur))

    def f(sic):
        try:
            s = int(sic)
        except (TypeError, ValueError):
            return None
        for lo, hi, ind in ranges:
            if lo <= s <= hi:
                return ind
        return n
    return f
