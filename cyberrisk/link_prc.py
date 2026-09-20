"""Section 2.3, last step: link PRC entity names to firms (the paper: "we manually link the names of
these firm-year cyberattacks in the PRC database with firm names in CRSP and Compustat").

CRSP/Compustat are licensed, so names are linked to SEC 10-K filers (CIK) instead:
  1. exact match of normalised names against every 10-K / 10-K405 filer name of 2005-2019, keeping
     CIKs that filed a 10-K within one year of the attack;
  2. MANUAL decisions below, made by reading candidates under ONE fixed rule (restated after the
     2026-09-19 audit found it applied inconsistently):
       accept (a) the PRC entity is the registrant itself, under any name the registrant used in
                  2005-2019 filings, or under its predecessor's name when the listed security
                  continued (Google -> Alphabet);
              (b) the entity is a unit, brand, benefit plan or event of the registrant AT THE ATTACK
                  DATE and its name contains a distinctive token of the registrant's name history
                  (Microsoft xBox, Blizzard -> Activision Blizzard, Booking.com -> Priceline/Booking
                  Holdings, Frost Bank -> Cullen/Frost, AT&T Group Health Plan);
       reject units without the parent's name (Zappos, Pizza Hut, Embassy Suites, Epsilon, HBO),
              entities no longer owned (Arby's 2017), private firms, 20-F / 40-F filers, ambiguous
              names ("Commerce Bank").  A row naming several firms takes the first named registrant.
     Candidates read: the best fuzzy match per incident (334 of 698 read in the first pass), every
     registrant sharing a rare (<= 3 registrants) name token (518 incidents), and every registrant
     sharing the first word for business incidents without such a token (148 incidents).
  3. several CIKs for one name: the CIK with the longest 10-K record among those active, unless
     overridden below; exact duplicates (same CIK, same date -- one breach recorded from two sources)
     are counted once.
The original rule was fixed before the counts were compared with the paper.  Its restatement
above came after the v4 counts (184 vs the paper's 175) were known, to apply the rule consistently
(EVALUATION.md 11.2 item 12); it raised the count to 244, away from 175, so it is not tuned to reach 175.

Output: data/prc/link_prc_cik.csv  [prc_id, company, attack_date, org_type, cik, method]
"""
import json
import os
import re
import sys
from collections import defaultdict

import pandas as pd

from .training import cyberattacks, load_prc

HERE = os.path.dirname(os.path.abspath(__file__))
_SUF = r"\b(the|inc|incorporated|corp|corporation|co|company|companies|llc|l l c|ltd|limited|plc|lp|l p|holdings?|group|n a|na)\b"

# (PRC company as recorded, attack year) -> CIK.  Fuzzy candidates accepted under the rule.
MANUAL_ACCEPT = {
    ("Charles Schwab", 2010): "316709", ("Charles Schwab", 2016): "316709",
    ("W. W. Grainger, Inc.", 2018): "277135", ("Dave & Buster's", 2008): "943823",
    ("Juniper Network", 2015): "1043604", ("Advanced Auto Parts", 2016): "1158449",
    ("Walmart Stores, Inc. ", 2016): "104169",
    ("Northrop Grunman", 2013): "1133421", ("NASDAQ.com", 2013): "1120193",
    ("J.P Morgan Chase", 2014): "19617", ("JPMorgan Chase", 2013): "19617",
    ("First Advantage SBS", 2007): "1210677", ("Polo Ralph Lauren, HSBC", 2005): "1037038",
    ("1-800-Flowers", 2016): "1084869", ("Wells Fargo", 2008): "72971",
    ("Hewlett Packard Enterprise Services ", 2016): "1645590", ("T-Mobile", 2017): "1283699",
    ("Digital River Inc., SWReg Inc.", 2010): "1062530",
    ("1st Source Bank", 2008): "34782", ("LinkedIn.com", 2012): "1271024", ("Smucker's", 2014): "91419",
    ("Northrop Grumman Systems Corporation", 2017): "1133421", ("First Banks Inc, iWire Inc", 2007): "710507",
    ("Microsoft xBox", 2014): "789019", ("Whole Foods", 2017): "865436",
    ("Sally Beauty Supply", 2014): "1368458", ("Sally Beauty Supply", 2015): "1368458",
    ("Google Ads", 2007): "1288776",
    ("Alaska Communications", 2014): "1089511", ("Goldman Sachs & Co. LLC", 2018): "886982",
    ("Verizon Enterprise Solutions", 2016): "732712", ("Wyndham Hotels & Resorts", 2009): "1361658",
    ("Wyndham Hotels & Resorts", 2010): "1361658",
    ("Voya Financial Advisor's Inc. ", 2016): "1535929", ("CoreLogic/Credco", 2017): "36047",
    ("Google Docs", 2017): "1652044", ("North Fork Bank", 2006): "352510",
    ("Jive Software/Producteev", 2016): "1462633", ("Microsoft/Xbox One", 2015): "789019",
    ("E-Trade", 2015): "1015780", ("Blucora (TaxAct)", 2016): "1068875",
    ("Wal-Mart, Sam's Club ", 2010): "104169", ("ABM Parking Services", 2014): "771497",
    ("Scripps Network LLC. (Food.com)", 2015): "1430602", ("Apple Inc., AT&T", 2010): "320193",
    ("Papa John's USA, Inc.", 2014): "901491", ("Rackspace, Incorporating Services, Ltd.", 2012): "1107694",
    ("Bank of Hawaii, First Hawaiian Bank", 2013): "46195", ("Google Android", 2016): "1652044",
    ("SUPERVALU Group Health Plan", 2015): "95521", ("Sonic Drive-In", 2017): "868611",
    ("Direct TV", 2012): "1465112", ("Track Data Securities Corp.", 2007): "922811",
    # second pass (audit 2026-09-19): every unlinked incident with a registrant sharing a rare
    # name token, or sharing its first word, read under the rule in the module docstring
    ('Suffolk County National Bank', 2010): '754673',
    ('Cisco Live 2010 ', 2010): '858877',
    ('Frost Bank', 2006): '39263',
    ('Monadnock Community Bank', 2010): '1283899',
    ('LandAmerica Credit Services, Inc., Diversified Capital', 2006): '877355',
    ('Triple-C, Inc. (TCI), Triple-S Salud, Inc. (TSS)', 2010): '1171662',
    ('vFinance Investments Inc.', 2007): '890285',
    ('Sovereign Bank', 2010): '811830',
    ("TJ stores (TJX), including TJMaxx, Marshalls, Winners, HomeSense, AJWright,  KMaxx, and possibly Bob's Stores in U.S. & Puerto Rico -- Winners and HomeGoods stores in Canada -- and possibly TKMaxx stores in UK and Ireland", 2007): '109198',
    ('MyVetDirect.com, Butler Schein Animal Health (BSAH)', 2011): '1000228',
    ('Yahoo! Voices', 2012): '1011006',
    ('TransUnion LLC, Manufacturers Life Insurance Company (ManuLife)', 2012): '1513514',
    ('Symantec, ImageShack', 2012): '849399',
    ('Carewise Health, Hewlett-Packard Enterprise Services', 2012): '47217',
    ('Adobe, Washington Administrative Office of the Courts', 2013): '796343',
    ('Morningstar Document Research', 2013): '1289419',
    ('Blizzard Entertainment', 2012): '718877',
    ('Saint Louis University, Tenet Healthcare Corporation, SSM Health Care', 2013): '70318',
    ('ADP, Facebook, Gmail, LinkedIn, Twitter, Yahoo, YouTube', 2013): '8670',
    ('Adobe, PR Newswire, National White Collar Crime Center', 2013): '796343',
    ('LexisNexis, Dun & Bradstreet, Kroll Background America', 2013): '1115222',
    ('AutoNation Toyota of South Austin ', 2014): '350698',
    ('Sears Holding Company/K-Mart', 2014): '1310067',
    ('Shutterfly/Tiny Prints/Treats/Wedding Divas', 2014): '1125920',
    ('Bebe Retail', 2014): '1059272',
    ('Natural Grocers', 2015): '1547459',
    ('Hilton/Hilton Honors Program', 2014): '1585689',
    ('Hilton Hotels', 2015): '1585689',
    ('Seagate', 2016): '1137789',
    ('Ecolab Health and Welfare Benefits Plan', 2016): '31462',
    ('Disney Consumer Products and Interactive Media', 2016): '1001039',
    ("Oracle's MICROS Point-of-Sale", 2016): '1341439',
    ('eHealth Insurance', 2017): '1333493',
    ('Abbott Nutrition', 2017): '1800',
    ('Patterson Dental Supply/Patterson Companies', 2013): '891024',
    ('PST Services Inc, a McKesson Co.', 2014): '927653',
    ('Anthem (Working file)', 2015): '1156039',
    ('Anthem, Inc. Affiliated Covered Entity', 2015): '1156039',
    ('AT&T Group Health Plan', 2015): '732717',
    ('ADT LLC Group Health & Welfare Plan', 2015): '1546640',
    ('Humana Inc [case # HU17001CC]', 2017): '49071',
    ('Game Stop', 2017): '1326380',
    ('Booking.com', 2014): '1075531',
    ('Polyone Designed Structures and Solutions', 2014): '1122976',
    ('ProAssurance Mid-Continent Underwriters, Inc.', 2014): '1127703',
    ('Pentair Aquatic Eco Systems, Inc.', 2018): '77360',
    ('OneMain Financial', 2018): '1584207',
    ('Ford-Motor Websites (Connect With Fiesta, Unleashfiesta)', 2012): '37996',
    ('B&G Foods North America, Inc., Maple Grove Farms', 2013): '1278027',
    ('Twinspires.com (Churchill Downs Technology Initiatives Company)', 2012): '20212',
    ('DSW Shoe Warehouse, Retail Ventures', 2005): '874444',
    ('Lincoln Financial Securities Corporation, Red Boat Advisor Resources', 2012): '59558',
    ('Information Handling Services, Inc. (IHS)', 2013): '1316360',
    ('Monster.com', 2009): '1020416',
    ('Monster.com', 2007): '1020416',
    ('LPL Financial (formerly Linsco Private Ledger)', 2008): '1397911',
    ('Citibank', 2008): '831001',
    ('Citibank', 2012): '831001',
    ('Citibank', 2011): '831001',
    ('Fox.com', 2011): '1308161',
    ('Fidelity National Information Services, Inc. (FIS)', 2011): '1136893',
    ('The New York Times, Melbourne IT', 2013): '71691',
    ('CME Group, CME ClearPort', 2013): '1156375',
    ('Las Vegas Sands Hotels and Casinos', 2014): '1300514',
    ('Starwood Hotels', 2015): '316206',
    ('Capital One', 2017): '927628',
    ('The Washington Trust Co.', 2008): '737468',
    ('X-Rite Incorporated, Pantone.com', 2012): '790818',
    ('Southern National Bancorp of Virginia, Inc. d/b/a/ Sonabank', 2018): '1325670',
    ('Federal Home Loan Mortgage Corporation (Freddie Mac)', 2014): '1026214',
}
# exact-name links that pointed at the wrong registrant
OVERRIDE = {
    ("United Airlines", 2015): "100517",                        # parent United Continental Holdings
    ("The Madison Square Garden Company", 2016): "1636519",     # not MSG Networks
    ("Gannett Co", 2017): "1635718",                            # the 2015 spin-off, not TEGNA
    ("US Airways Group", 2013): "701345",                       # the listed parent, not US Airways Inc
}


def norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"/[a-z]{2}/?\s*$", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(_SUF, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def build(prc_csv, filers_json, out_csv):
    a = cyberattacks(load_prc(prc_csv), "2005-01-01", "2018-12-31")
    F = json.load(open(filers_json))
    years = {k: set(v) for k, v in F["years"].items()}
    idx = defaultdict(set)
    for name, ciks in F["names"].items():
        idx[norm(name)].update(ciks)
    keys = set(zip(a["company"].fillna(""), a["attack_date"].dt.year))
    dead = [k for k in list(MANUAL_ACCEPT) + list(OVERRIDE) if k not in keys]
    if dead:          # a truncated or mistyped key silently drops a decision -- fail instead
        raise ValueError(f"manual link keys matching no PRC incident: {dead}")
    rows = []
    for _, r in a.iterrows():
        company, y = r["company"] or "", r["attack_date"].year
        key = (company, y)
        live = sorted((c for c in idx.get(norm(company), ()) if years[c] & {y - 1, y, y + 1}),
                      key=lambda c: (-len(years[c]), int(c)))       # deterministic on ties
        if key in OVERRIDE:
            cik, method = OVERRIDE[key], "override"
        elif live:
            cik, method = live[0], "exact"
        elif key in MANUAL_ACCEPT:
            cik, method = MANUAL_ACCEPT[key], "manual"
        else:
            continue
        rows.append({"prc_id": r["prc_id"], "company": company, "attack_date": r["attack_date"].date(),
                     "org_type": r["org_type"], "cik": cik, "method": method})
    out = pd.DataFrame(rows).drop_duplicates(["cik", "attack_date"]).reset_index(drop=True)
    out.to_csv(out_csv, index=False)
    return out


if __name__ == "__main__":
    d = os.path.join(HERE, "data")
    out = build(os.path.join(d, "prc", "prc_export_jbukuts.csv"),
                os.path.join(d, "edgar_10k_filers_2005_2019.json"),
                os.path.join(d, "prc", "link_prc_cik.csv"))
    print(len(out), out["method"].value_counts().to_dict())
