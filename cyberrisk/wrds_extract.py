"""Pull, from WRDS, the licensed inputs of the paper's finance half, in the column layout the
modules expect (README, "Data the paper uses that is licensed").  QUT subscribes to WRDS with CRSP,
Compustat, BoardEx and Audit Analytics (QUT library guide, checked 2026-09-19); Thomson-Reuters 13F
is not listed there.

    python3 -m cyberrisk.wrds_extract --user YOUR_WRDS_USERNAME            # everything
    python3 -m cyberrisk.wrds_extract --user YOUR_WRDS_USERNAME --only libraries

The WRDS library asks for the password once (and a Duo push); nothing is stored by this script.
Output: cyberrisk/data/wrds/<table>.csv.gz (git-ignored) and access.json (what the account can
read).  NOT yet run against the live server: written before an account existed.  The first run
writes access.json; a table the account cannot read is recorded there instead of failing the run.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "wrds")

# sample: fiscal years 2007-2018 (+ 5 years before for the 60-month betas / IVOL, + 2019-2020 for
# the SolarWinds event and the IA7 K forward fill)
MONTHLY = ("2002-01-01", "2021-12-31")
DAILY = ("2007-01-01", "2021-03-31")

QUERIES = {
    # Compustat annual, standard screen; cik/sic from the company file; au = auditor (IA7 E)
    "comp": """
        select f.gvkey, f.fyear, f.datadate, c.cik, c.sic, f.au, f.at, f.ceq, f.prcc_f, f.csho,
               f.che, f.ib, f.dp, f.dvc, f.oibdp, f.ppent, f.xrd, f.dltt, f.dlc
        from comp.funda f join comp.company c on f.gvkey = c.gvkey
        where f.indfmt = 'INDL' and f.datafmt = 'STD' and f.popsrc = 'D' and f.consol = 'C'
          and f.fyear between 2002 and 2020""",
    # CRSP-Compustat link, primary links only
    "ccm": """
        select gvkey, lpermno as permno, linkdt, linkenddt
        from crsp.ccmxpf_lnkhist
        where linktype in ('LU', 'LC') and linkprim in ('P', 'C')""",
    # CIK -> gvkey by fiscal year (WRDS SEC Analytics); falls back to comp.company.cik if absent
    "cik_gvkey": """
        select cik, gvkey, fyear from wrdssec.wciklink_gvkey""",
    # CRSP monthly: common shares (10, 11) on NYSE / AMEX / NASDAQ (1, 2, 3)
    "crsp_m": f"""
        select m.permno, m.date, m.ret, m.prc, m.shrout, m.vol, n.shrcd, n.exchcd, n.siccd
        from crsp.msf m join crsp.msenames n
          on m.permno = n.permno and m.date between n.namedt and n.nameendt
        where n.shrcd in (10, 11) and n.exchcd in (1, 2, 3)
          and m.date between '{MONTHLY[0]}' and '{MONTHLY[1]}'""",
    "crsp_delist": """
        select permno, dlstdt, dlret, dlstcd from crsp.msedelist""",
    # Thomson-Reuters 13F holdings (institutional ownership) -- may not be subscribed at QUT
    "tr13f": f"""
        select rdate, mgrno, cusip, shares from tfn.s34
        where rdate between '{MONTHLY[0]}' and '{MONTHLY[1]}'""",
    "crsp_names": """
        select permno, ncusip, namedt, nameendt from crsp.msenames""",
}


def _daily_queries():
    """CRSP daily in yearly chunks (about 2 million rows each)."""
    y0, y1 = int(DAILY[0][:4]), int(DAILY[1][:4])
    for y in range(y0, y1 + 1):
        lo = max(f"{y}-01-01", DAILY[0]); hi = min(f"{y}-12-31", DAILY[1])
        yield f"crsp_d_{y}", f"""
            select d.permno, d.date, d.ret, d.prc, d.vol, d.shrout
            from crsp.dsf d join crsp.msenames n
              on d.permno = n.permno and d.date between n.namedt and n.nameendt
            where n.shrcd in (10, 11) and n.exchcd in (1, 2, 3)
              and d.date between '{lo}' and '{hi}'"""


# BoardEx table names differ across WRDS subscriptions; list what exists before querying it
BOARDEX_LIBRARY = "boardex"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", required=True, help="WRDS username")
    ap.add_argument("--only", nargs="*", help="subset of tables (or 'libraries')")
    a = ap.parse_args(argv)
    import wrds                                   # pip install wrds
    os.makedirs(OUT, exist_ok=True)
    db = wrds.Connection(wrds_username=a.user)
    access = {"libraries": sorted(db.list_libraries())}
    if BOARDEX_LIBRARY in access["libraries"]:
        access["boardex_tables"] = sorted(db.list_tables(BOARDEX_LIBRARY))
    json.dump(access, open(os.path.join(OUT, "access.json"), "w"), indent=1)
    print("libraries readable:", len(access["libraries"]))
    if a.only == ["libraries"]:
        return
    jobs = list(QUERIES.items()) + list(_daily_queries())
    if a.only:
        jobs = [(k, q) for k, q in jobs if k in a.only or any(k.startswith(o) for o in a.only)]
    failed = {}
    for name, sql in jobs:
        path = os.path.join(OUT, f"{name}.csv.gz")
        if os.path.exists(path):
            print("have", name); continue
        try:
            df = db.raw_sql(sql)
        except Exception as e:                   # not subscribed / table absent: record, go on
            failed[name] = repr(e)[:300]; print("FAILED", name, failed[name][:120]); continue
        df.to_csv(path, index=False, compression="gzip")
        print(name, len(df))
    access["failed"] = failed
    json.dump(access, open(os.path.join(OUT, "access.json"), "w"), indent=1)
    db.close()


if __name__ == "__main__":
    main()
