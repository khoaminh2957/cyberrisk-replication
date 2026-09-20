"""Fetch the public inputs the tests and the text pipeline need (they are not kept in git):

  appendix-a2   the four FY2017 10-K documents of Appendix A.2 (Apple, Abbott, GM, Verizon)
  ff            the Ken French factor and industry files
  prc-sample    the free sample of the Privacy Rights Clearinghouse data-breach chronology
  prc           the PRC chronology 2005-2018 in its original export layout (a public mirror of the
                pre-2020 export) and PRC's own Tableau archive 2005-2019 used to verify it: 97.2% of
                the mirror's (company, date, type) rows are in the archive once the archive's
                day/month swap for days <= 12 is undone, 62.5% without undoing it (2026-09-19)
"""
import argparse
import json
import os

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = os.environ.get("EDGAR_USER_AGENT", "academic replication contact@example.edu")
# CIK, accession, primary document -- the filings quoted in Appendix A.2
APPENDIX_A2 = [
    ("0000320193", "0000320193-17-000070", "a10-k20179302017.htm"),   # Apple, FY ended 2017-09-30
    ("0000001800", "0001047469-18-000856", "a2234264z10-k.htm"),      # Abbott, FY2017
    ("0001467858", "0001467858-18-000022", "gm201710k.htm"),          # General Motors, FY2017
    ("0000732712", "0000732712-18-000009", "a201710-k.htm"),          # Verizon, FY2017
]
PRC_SAMPLE = "https://cdn.shopify.com/s/files/1/0571/5489/5955/files/Data_Breach_Chronology_sample.csv"
PRC_MIRROR = "https://raw.githubusercontent.com/jbukuts/databreaches/HEAD/data/data_breaches.csv"
PRC_ARCHIVE = ("https://public.tableau.com/workbooks/"
               "DataBreachChronologyArchive-PRCHistoricalData2005-2019.twb")


def appendix_a2(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "data", "edgar")
    os.makedirs(out_dir, exist_ok=True)
    for cik, acc, doc in APPENDIX_A2:
        path = os.path.join(out_dir, f"{cik}_{acc}_{doc}")
        if os.path.exists(path):
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
        r = requests.get(url, headers={"User-Agent": UA}, timeout=120)
        r.raise_for_status()
        open(path, "wb").write(r.content)
        print(path, len(r.content))


def ff(out_dir=None):
    from .factors_ff import FILES, download
    out_dir = out_dir or os.path.join(HERE, "data", "ff")
    for name in FILES:
        print(download(name, out_dir))


def prc_sample(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "data", "prc")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "prc_chronology_sample.csv")
    r = requests.get(PRC_SAMPLE, timeout=120)
    r.raise_for_status()
    open(path, "wb").write(r.content)
    print(path, len(r.content))


def prc(out_dir=None):
    """Mirror CSV -> data/prc/prc_export_jbukuts.csv; Tableau archive -> prc_historical_2005_2019.csv
    (needs `tableauhyperapi`, macOS arm64 wheels exist up to 0.0.26479)."""
    import io, tempfile, zipfile
    out_dir = out_dir or os.path.join(HERE, "data", "prc")
    os.makedirs(out_dir, exist_ok=True)
    r = requests.get(PRC_MIRROR, timeout=120); r.raise_for_status()
    open(os.path.join(out_dir, "prc_export_jbukuts.csv"), "wb").write(r.content)
    ua = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"}
    r = requests.get(PRC_ARCHIVE, headers=ua, timeout=120); r.raise_for_status()
    tmp = tempfile.mkdtemp()
    zipfile.ZipFile(io.BytesIO(r.content)).extractall(tmp)
    hyper = next(os.path.join(d, f) for d, _, fs in os.walk(tmp) for f in fs if f.endswith(".hyper"))
    import pandas as pd
    from tableauhyperapi import Connection, CreateMode, HyperProcess, TableName, Telemetry
    t = TableName("Extract", "Extract")
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, hyper, CreateMode.NONE) as c:
            cols = [col.name.unescaped for col in c.catalog.get_table_definition(t).columns]
            rows = c.execute_list_query(f"SELECT * FROM {t}")
    pd.DataFrame(rows, columns=cols).to_csv(os.path.join(out_dir, "prc_historical_2005_2019.csv"), index=False)
    print(out_dir)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["appendix-a2", "ff", "prc-sample", "prc", "all"])
    a = ap.parse_args(argv)
    for k, f in (("appendix-a2", appendix_a2), ("ff", ff), ("prc-sample", prc_sample), ("prc", prc)):
        if a.what in (k, "all"):
            f()


if __name__ == "__main__":
    main()
