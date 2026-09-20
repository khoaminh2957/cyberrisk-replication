"""The remaining logic that the other test files do not reach: the PRC loader on the real sample
export, the Ken French readers on the downloaded files, the pipeline on a tiny corpus fixture,
and the robustness / factor helpers."""
import json
import os
import numpy as np
import pandas as pd
import pytest

from cyberrisk import factors_ff as FF, robustness as R, factor as F, portfolios as P, gtrends as G, pipeline
from cyberrisk.training import load_prc, cyberattacks, training_sample, firm_years
from cyberrisk.tests.synthetic import make

HERE = os.path.dirname(__file__)
DATA_FF = os.path.join(HERE, "..", "data", "ff")
PRC = os.path.join(HERE, "..", "data", "prc", "prc_chronology_sample.csv")


# --- §2.3 on the real PRC export -----------------------------------------------------------
def test_prc_loader_and_training_sample(tmp_path):
    if not os.path.exists(PRC):
        pytest.skip("PRC sample not on disk")
    prc = load_prc(PRC)
    assert {"attack_date", "company", "breach_type", "org_type", "prc_id"} <= set(prc.columns)
    assert prc["attack_date"].notna().mean() > 0.9
    a = cyberattacks(prc, "2005-01-01", "2026-12-31")
    assert (a["breach_type"].str.upper() == "HACK").all()
    assert not a["org_type"].str.upper().isin({"GOV", "EDU", "NGO"}).any()
    assert len(a) < len(prc)
    # the Factiva flag and the name link are hand-made inputs
    major = tmp_path / "major.csv"; link = tmp_path / "link.csv"
    keep = a.head(4)
    pd.DataFrame({"prc_id": keep["prc_id"], "major": [1, 1, 0, 1]}).to_csv(major, index=False)
    pd.DataFrame({"company": keep["company"], "firm": ["c1", "c2", "c3", "c4"]}).to_csv(link, index=False)
    ts = training_sample(a, link, major)
    assert set(ts["firm"]) == {"c1", "c2", "c4"} and (ts["major"] == 1).all()
    assert len(training_sample(a, link, major, major_only=False)) == 4
    assert len(training_sample(a, link)) == 4            # no Factiva flag: every incident is used
    per_incident = tmp_path / "per_incident.csv"         # link_prc.py layout: one CIK per incident
    pd.DataFrame({"prc_id": keep["prc_id"], "cik": ["9", "8", "7", "6"]}).to_csv(per_incident, index=False)
    assert set(training_sample(a, per_incident)["firm"]) == {"9", "8", "7", "6"}
    fy = firm_years(ts)
    assert len(fy) == fy.drop_duplicates(["firm", "year"]).shape[0]


# --- Ken French readers ---------------------------------------------------------------------
def test_ken_french_readers():
    m = FF.factors(DATA_FF)
    assert list(m.columns) == ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "Mom"]
    assert m.index.freqstr == "M" and m["Mkt-RF"].abs().max() < 0.5      # decimals, not percent
    d = FF.factors(DATA_FF, daily=True)
    assert isinstance(d.index, pd.DatetimeIndex) and d.loc["2008-10-13", "Mkt-RF"] > 0.10
    i12 = FF.industry_portfolios(DATA_FF, 12, "value")
    assert i12.shape[1] == 12 and "BusEq" in i12.columns
    assert FF.industry_portfolios(DATA_FF, 48, "equal").shape[1] == 48
    f12, f48 = FF.sic_map(DATA_FF, 12), FF.sic_map(DATA_FF, 48)
    assert f12(3571) == 6 and f12(4813) == 7 and f12(1311) == 4      # BusEq, Telcm, Enrgy
    assert f12(9999) == 12 and f12(None) is None and f48(3571) == 35


# --- pipeline (offline paths) ----------------------------------------------------------------
def test_pipeline_corpus_and_measure(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    # the §2.4 rule drops roots occurring fewer than 10 times, so the fixture repeats the two
    # disclosure texts across enough firms for their words to survive
    rows = []
    for k in range(10):
        rows.append({"filename": f"a{k}.htm", "cik": f"1{k}", "year": "2018",
                     "section_1A": "Item 1A. Risk Factors. Hackers may attack our systems. Our reputation could be harmed."})
        rows.append({"filename": f"b{k}.htm", "cik": f"2{k}", "year": "2018",
                     "section_1A": "Item 1A. Risk Factors. A cyber attack on our systems could occur. We may face litigation."})
    rows.append({"filename": "c.htm", "cik": "3", "year": "2018", "section_1A": "We sell furniture."})
    corpus.write_text("\n".join(json.dumps(r) for r in rows))
    out = tmp_path / "disc.jsonl"
    pipeline.disclosures_corpus([str(corpus)], str(out))
    recs = [json.loads(l) for l in open(out)]
    assert len(recs) == len(rows) and recs[0]["fyear"] == 2017 and len(recs[-1]["captured"]) == 0
    pipeline.disclosures_corpus([str(corpus)], str(out))       # resumable: no duplicate rows
    assert len(open(out).read().strip().split("\n")) == len(rows)
    attacks = tmp_path / "att.csv"
    pd.DataFrame({"firm": ["10"], "attack_date": ["2018-03-01"]}).to_csv(attacks, index=False)
    res = pipeline.measure(str(out), str(attacks), str(tmp_path / "cr.csv"), cache_dir=str(tmp_path)).set_index("firm")
    assert res.loc["20", "cyber_risk"] > 0        # b-firms are similar to the attacked firm 10
    assert res.loc["10", "cyber_risk"] == 0.0     # a firm is not compared with itself
    assert res.loc["3", "cyber_risk"] == 0.0      # no cyber disclosure -> empty vector -> zero
    v = json.load(open(str(tmp_path / "cr_vocab.json")))
    assert v["vocabulary_size"] == len(v["vocabulary"]) and len(v["top20"]) <= 20


# --- robustness helpers not covered elsewhere ---------------------------------------------------
def test_robustness_remaining():
    scores = pd.DataFrame({"permno": [1, 2, 3], "fyear": 2015, "cyber_risk": [0.1, 0.2, 0.3],
                           "filing_date": pd.to_datetime(["2011-06-01", "2012-06-01", "2016-06-01"])})
    assert R.post_2011(scores)["permno"].tolist() == [2, 3]
    assert R.exclude_firms(scores, [2])["permno"].tolist() == [1, 3]
    ff48 = {1: 35, 2: 35, 3: 12}
    assert R.exclude_peer_industries(scores, [1], ff48)["permno"].tolist() == [3]
    ff12 = {1: 6, 2: 7, 3: 6}
    ind = pd.DataFrame(0.01, index=pd.period_range("2015-01", "2015-03", freq="M"),
                       columns=["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm",
                                "Utils", "Shops", "Hlth", "Money", "Other"])
    crsp = pd.DataFrame({"permno": [1, 2], "month": pd.Period("2015-01", "M"), "ret": [0.05, 0.05]})
    adj = R.industry_adjust(crsp, ff12, ind)
    assert np.allclose(adj["ret"], 0.04)
    panel = pd.DataFrame({"month": np.repeat(np.arange(20), 50), "cyber_risk": np.random.default_rng(0).normal(size=1000)})
    panel["idiosyncratic_volatility"] = 0.5 * panel["cyber_risk"] + np.random.default_rng(1).normal(size=1000)
    o = R.orthogonalize(panel)
    assert abs(np.corrcoef(o.dropna()["cyber_risk_orth"], o.dropna()["idiosyncratic_volatility"])[0, 1]) < 1e-8


def test_cyberattack_probability_and_compare(econ_panel=None):
    rng = np.random.default_rng(4)
    n = 800
    p = pd.DataFrame({"firm": np.repeat(np.arange(80), 10), "fyear": np.tile(np.arange(2009, 2019), 80),
                      "ff12": np.repeat(rng.integers(1, 13, 80), 10)})
    p["firm_size_ln"] = rng.normal(6, 2, n)
    p["cyber_risk"] = 0.05 * p["firm_size_ln"] + rng.uniform(0, .3, n)
    p["crd_sentences"] = (p["cyber_risk"] * 50).astype(int)
    p["attack"] = (rng.uniform(size=n) < 1 / (1 + np.exp(-(-3 + 0.2 * p["firm_size_ln"])))).astype(int)
    p = p.sort_values(["firm", "fyear"])
    p["attack_next"] = p.groupby("firm")["attack"].shift(-1)
    out = R.cyberattack_probability(p.dropna(subset=["attack_next"]), ["firm_size_ln"])
    assert out["cyberattack_probability"].between(0, 1).all()
    cmp = R.compare_measures(out.dropna(subset=["attack_next"]).assign(attack_next=lambda d: d["attack_next"].astype(int)),
                             "attack_next", ["cyber_risk", "crd_sentences", "cyberattack_probability"])
    assert set(cmp.index) == {"cyber_risk", "crd_sentences", "cyberattack_probability"}
    assert cmp["n"].gt(0).all()


# --- factor / portfolio helpers ---------------------------------------------------------------
def test_cyber_beta_and_panel_b():
    scores, crsp_m, f = make(data_dir=DATA_FF, n_firms=40, end="2013-12")
    ex = crsp_m[["permno", "month"]].copy()
    ex["exret"] = crsp_m["ret"] - crsp_m["month"].map(f["RF"])
    crf = pd.Series(np.random.default_rng(0).normal(0, 0.02, len(f)), index=f.index)
    b = F.cyber_beta(ex, crf, window=60, min_obs=24)
    assert {"permno", "month", "cyber_beta"} == set(b.columns) and b["cyber_beta"].notna().all()
    chars = crsp_m[["permno", "month", "me"]].copy()
    pb = P.table7_panel_b(scores, chars, crsp_m, ["me"])
    assert list(pb.index) == [1, 2, 3] and pb.loc[1, "cyber_risk"] == 0.0
    assert pb.loc[3, "cyber_risk"] > pb.loc[2, "cyber_risk"] > 0


def test_joint_dummy():
    idx = pd.date_range("2020-01-01", periods=40)
    a = pd.Series(10.0, index=idx); a.iloc[30] = 100.0
    b = pd.Series(10.0, index=idx); b.iloc[35] = 100.0
    j = G.joint_dummy({"hacker": a, "data breach": b})
    assert j.iloc[30] == 1 and j.iloc[35] == 1 and j.sum() == 2


# --- offline pieces of the network paths ------------------------------------------------------
INDEX = os.path.join(HERE, "..", "..", "AI_Innovation_Atlas_data", "02_data_sources", "sec_edgar",
                     "full_index_all", "edgar_filings_index_1993_now_atlas_forms.csv")


def test_filings_from_index_filters_forms_and_years():
    if not os.path.exists(INDEX):
        pytest.skip("EDGAR index not on disk")
    from itertools import islice
    from cyberrisk.edgar import filings_from_index, FORMS
    rows = list(islice(filings_from_index(INDEX, years=range(2006, 2008)), 50))
    assert rows and all(r["form"] in FORMS for r in rows)
    assert all(2006 <= int(r["date_filed"][:4]) <= 2007 for r in rows)


def test_cli_dispatch(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(pipeline, "disclosures_corpus", lambda j, o, limit=None: seen.update(j=j, o=o, limit=limit))
    pipeline.main(["disclosures-corpus", "--jsonl", "x.jsonl", "--out", str(tmp_path / "o.jsonl"), "--limit", "5"])
    assert seen["j"] == ["x.jsonl"] and seen["limit"] == 5
    with pytest.raises(SystemExit):
        pipeline.main(["nope"])


@pytest.mark.network
def test_edgar_fetch_and_google_trends(tmp_path):
    """Only when --run-network is passed: the two live endpoints the paper needs."""
    from cyberrisk.edgar import fetch, submission_header
    raw = fetch("https://www.sec.gov/Archives/edgar/data/320193/000032019317000070/0000320193-17-000070-index.htm",
                str(tmp_path))
    assert b"10-K" in raw
    t = G.Trends()
    s = t.daily(G.TOPICS["data breach"], "2017-08-15", "2017-10-15")
    assert len(s) > 50 and s.max() == 100 and s.idxmax().month == 9      # the Equifax disclosure
