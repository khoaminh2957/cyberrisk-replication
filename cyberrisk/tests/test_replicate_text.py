import pandas as pd

from cyberrisk.replicate_text import attack_counts, PAPER


def test_attack_counts_ex_ante_window():
    """An attack counts as 'with available cybersecurity risk disclosures' only when the firm filed
    a 10-K with >= 1 cyber sentence in the year BEFORE the attack; a later filing does not count."""
    link = pd.DataFrame({"cik": ["1", "2", "3"], "attack_date": pd.to_datetime(["2014-06-01"] * 3)})
    ok = pd.DataFrame({"cik": ["1", "2", "3"],
                       "filing_date": pd.to_datetime(["2014-02-01", "2014-09-01", "2012-02-01"]),
                       "crd_sentences": [3, 3, 3], "listed": [True, True, False]})
    t = attack_counts(link, ok)
    assert t.loc[2014, "linked"] == 3
    assert t.loc[2014, "+ex-ante Item 1A"] == 1             # same window, cyber content not required
    assert t.loc[2014, "+ex-ante disclosure"] == 1          # firm 2 filed after, firm 3 too early
    assert t.loc[2014, "+listed"] == 1
    assert t.loc["total", "paper"] == 175 == sum(PAPER["attacks_by_year"].values())


import os
import pytest

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")


def test_link_prc_rebuilds_the_link_file(tmp_path):
    """The hand-made PRC -> CIK link (link_prc.py) is reproducible from the PRC export."""
    from cyberrisk import link_prc
    src = os.path.join(DATA, "prc", "prc_export_jbukuts.csv")
    filers = os.path.join(DATA, "edgar_10k_filers_2005_2019.json")
    if not (os.path.exists(src) and os.path.exists(filers)):
        pytest.skip("PRC export / filer table not on disk")
    out = link_prc.build(src, filers, str(tmp_path / "link.csv"))
    ref = pd.read_csv(os.path.join(DATA, "prc", "link_prc_cik.csv"), dtype={"cik": str, "prc_id": str})
    got = pd.read_csv(tmp_path / "link.csv", dtype={"cik": str, "prc_id": str})
    assert len(got) == 288 and got.equals(ref)
    assert out["method"].value_counts().to_dict() == {"exact": 158, "manual": 125, "override": 5}


def test_headline_numbers_are_pinned():
    """The public-data run v6 (run v5's filings -- rule R* link, frequency before roots, insurance in the
    same sentence -- scored on the whole random draw; EVALUATION.md section 9); fails if a code
    change moves them."""
    from cyberrisk import replicate_text as R
    p, csv = os.path.join(DATA, "run", "v6_scored.pkl"), os.path.join(DATA, "results", "scores_v6.csv")
    if os.path.exists(p):
        ok = pd.read_pickle(p)
    elif os.path.exists(csv):                       # the published repo ships the scores, not the texts
        ok = pd.read_csv(csv, dtype={"cik": str, "sic": str}, parse_dates=["filing_date"])
    else:
        pytest.skip("run output not on disk")
    link = pd.read_csv(os.path.join(DATA, "prc", "link_prc_cik.csv"), dtype={"cik": str}, parse_dates=["attack_date"])
    out = R.report(ok, [], {}, link)
    assert len(R.scored_sample(ok)) == 3092
    t3 = out["table3"]["ours"]
    assert abs(t3["mean"] - 0.254) < 0.001 and abs(t3["p50"] - 0.323) < 0.001 and abs(t3["p99"] - 0.613) < 0.001
    t1 = out["table1"].set_index("firm")["ours"]
    assert abs(t1["Weyerhaeuser"] - 0.039) < 0.001 and abs(t1["Walgreens Boots Alliance"] - 0.671) < 0.001
    assert out["attack_counts"].loc["total", "+ex-ante disclosure"] == 244
    t6 = R.table6_model1(ok, link)
    assert abs(t6["coef"] - 1.320) < 0.001 and t6["cases"] == 195
