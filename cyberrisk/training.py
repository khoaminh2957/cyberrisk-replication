"""Section 2.3 of the paper: the training sample of firms subject to a major cyberattack.

Source: Privacy Rights Clearinghouse (PRC) data-breach chronology -- date made public, company,
type of breach, type of organization, records affected.  Paper filters: drop governments,
educational institutions and nonprofits; keep only "hacking or malware -- electronic entry by an
outside party" (PRC breach type HACK).  Each remaining incident is cross-referenced by hand in
Factiva; those covered by global news outlets (CNBC, FT, WSJ) or major newswires (AP, Bloomberg,
Reuters) are "major".  Paper counts, 2005-2018: 175 attacks with an Item 1A disclosure available,
69 major, 54 firm-years.  Firm names are linked by hand to CRSP / Compustat.

The Factiva check and the name link are manual inputs here too: `major_csv` and `link_csv`.
"""
import pandas as pd

# PRC historical chronology (2005-2019 export) column names and codes
ORG_EXCLUDED = {"GOV", "EDU", "NGO"}          # governments, educational institutions, nonprofits
BREACH_KEEP = {"HACK"}                        # hacking or malware by an outside party
_HIST_COLS = {"Date Made Public": "attack_date", "Company": "company",
              "Type of breach": "breach_type", "Type of organization": "org_type",
              "Total Records": "records", "Description of incident": "description"}
# the post-2020 PRC export uses these names instead
_NEW_COLS = {"reported_date": "attack_date", "org_name": "company", "breach_type": "breach_type",
             "organization_type": "org_type", "total_affected": "records",
             "incident_details": "description"}


# the PRC "Data Breach Chronology Archive - PRC Historical Data 2005-2019" (Tableau Public, the
# free source of the paper-era data; see fetch_data.prc_archive)
_ARCHIVE_COLS = {"Reported Date": "attack_date", "Name of Entity": "company",
                 "Type of Breach": "breach_type", "Organization Type": "org_type",
                 "Records Affected": "records", "Description": "description"}


def load_prc(path):
    """PRC chronology (any of the three export layouts) -> DataFrame[attack_date, company,
    breach_type, org_type, records, description, prc_id]."""
    sep = "|" if open(path, encoding="utf-8-sig").readline().count("|") > 3 else ","
    raw = pd.read_csv(path, sep=sep, encoding="utf-8-sig", dtype=str)
    cols = (_HIST_COLS if "Date Made Public" in raw.columns
            else _ARCHIVE_COLS if "Name of Entity" in raw.columns else _NEW_COLS)
    df = raw.rename(columns=cols)[list(cols.values())].copy()
    df["attack_date"] = pd.to_datetime(df["attack_date"], errors="coerce")
    df["prc_id"] = raw["id"] if "id" in raw.columns else raw.index.astype(str)
    return df


def cyberattacks(prc, start="2005-01-01", end="2018-12-31"):
    """Paper §2.3 filters on the PRC chronology."""
    df = prc[prc["attack_date"].between(start, end)]
    df = df[~df["org_type"].fillna("").str.upper().isin(ORG_EXCLUDED)]
    df = df[df["breach_type"].fillna("").str.upper().str.startswith(tuple(BREACH_KEEP))]
    return df.reset_index(drop=True)


def training_sample(attacks, link_csv, major_csv=None, major_only=True):
    """Join the hand-made link and, when available, the hand-made Factiva "major" flag.
    link_csv: (prc_id, cik) per incident -- see link_prc.py -- or (company, firm) by name.
    major_csv: (prc_id, major).  Without it every incident is used: the paper's own robustness
    variant ("we repeat our measurement using all incidents ... results are unchanged", §2.3).
    Returns DataFrame[firm, attack_date, major, company, prc_id]; one row per attack."""
    link = pd.read_csv(link_csv, dtype=str)
    if "prc_id" in link.columns:
        df = attacks.merge(link[["prc_id", "cik"]].rename(columns={"cik": "firm"}), on="prc_id", how="inner")
    else:
        df = attacks.merge(link[["company", "firm"]], on="company", how="inner")
    if major_csv is not None:
        major = pd.read_csv(major_csv, dtype={"prc_id": str})
        df = df.merge(major[["prc_id", "major"]], on="prc_id", how="left")
        df["major"] = df["major"].fillna(0).astype(int)
        if major_only:
            df = df[df["major"] == 1]
    else:
        df["major"] = pd.NA
    return df[["firm", "attack_date", "major", "company", "prc_id"]].reset_index(drop=True)


def firm_years(sample):
    """The paper's unit: firm-year cyberattacks (a firm may have several attacks in a year)."""
    fy = sample.assign(year=sample["attack_date"].dt.year)
    return fy.drop_duplicates(["firm", "year"])[["firm", "year"]].reset_index(drop=True)
