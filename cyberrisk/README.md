# Replication of *Cybersecurity Risk* (Florackis, Louca, Michaely & Weber, RFS 2023)

One module per step of the paper, no more.  Every function name says which table or section it
reproduces; every unstated choice is flagged in `EVALUATION.md`.

## Paper → code

| Paper | Module / function | Data |
|---|---|---|
| §2.2 10-K crawl, Item 1A, fiscal year, CIK, incorporate-by-reference filter | `edgar.py` (`filings_from_index`, `fetch`, `submission_header`, `main_document`, `html_sentences`, `item_1a`) | SEC EDGAR (free) |
| App. A.1 keyword tables and extraction algorithm | `keywords.py`, `extract.py` (`extract`) | – |
| App. A.2 four worked examples (19/19, 8/8, 18/20, 13/15) | `tests/test_appendix_a2.py` (real filings in `data/edgar/`) | SEC EDGAR |
| §2.3 training sample (PRC breaches, business + hacking only, Factiva "major", name link) | `training.py`, `link_prc.py` (the name link, one fixed rule + the manual decisions) | PRC export (public mirror) + PRC Tableau archive; Factiva not available |
| §2.4 word exclusions, roots, frequency ≥ 10, count vectors | `roots.py` | WordNet (Merriam-Webster API if `MW_API_KEY`) |
| §2.4 Eq. (1)-(2), 1-year window ending at the filing date, 2-year fallback | `measure.py` (`cybersecurity_risk`) | – |
| §3.2 Table 2 language measures, cyber insurance | `language.py` | Loughran-McDonald master dictionary |
| §2.2 link 10-K (CIK, fiscal year) → Compustat → CRSP | `variables.link_disclosures` | WRDS SEC Analytics + CCM link |
| App. B variable definitions | `variables.py` | Compustat, CRSP, 13F, BoardEx (WRDS) |
| §3 Tables 1-6, Figures 1-2 | `validation.py` | firm-year panel |
| §4.1-4.2 Tables 7-8 | `portfolios.py` | CRSP monthly, Ken French factors |
| §4.3 Table 9 | `fama_macbeth.py` | stock-month panel |
| §4.4 Table 10 factor and Google SVI | `factor.py`, `gtrends.py` | CRSP daily, Google Trends (free) |
| §5 Tables 11-12 SolarWinds | `solarwinds.py` | CRSP daily, FactSet Revere customers, Bloomberg AIA |
| §6 IA7-IA14 robustness, incl. the IA10 non-cyber placebo measure | `robustness.py` (+ options in `measure.py`, `portfolios.py`, `factor.py`) | as above |
| estimators (Newey-West 12 lags, FE-OLS clustered, logit, Fama-MacBeth, market model, quantile groups) | `stats.py` | – |
| Ken French factors / industries | `factors_ff.py` | Ken French library (free) |
| orchestration of the text half | `pipeline.py` (streaming EDGAR fetch, 8-way parallel, resume, offline `reextract`) | – |
| the paper's numbers the text half yields (Tables 1, 2, 3, 6-Model 1, Figures 1-2, word list) next to ours | `replicate_text.py` | the run below |

## Getting the public inputs (not kept in git)

```bash
export EDGAR_USER_AGENT="Your Name your@email"      # SEC fair-access rule
python3 -m cyberrisk.fetch_data all                 # the four Appendix A.2 10-Ks, the Ken French files,
                                                    # the PRC sample, the PRC 2005-2018 export + archive
                                                    # (archive needs `pip install tableauhyperapi==0.0.26479`)
```

`test_appendix_a2.py` skips without the four filings; the synthetic finance tests download the Ken
French files on first use.

## Running the text half (public data)

```bash
# Item 1A -> cybersecurity risk disclosures, from raw EDGAR complete submissions
python3 -m cyberrisk.pipeline disclosures-edgar \
    --index AI_Innovation_Atlas_data/02_data_sources/sec_edgar/full_index_all/edgar_filings_index_1993_now_atlas_forms.csv \
    --out cyberrisk/data/disclosures.jsonl --cache cyberrisk/data/edgar_cache
# or from EDGAR-CORPUS (eloukas/edgar-corpus on Hugging Face, per-year train/validate/test .jsonl)
python3 -m cyberrisk.pipeline disclosures-corpus --jsonl data/edgar_corpus/2008/*.jsonl ... --out cyberrisk/data/disclosures.jsonl
# the measure (needs the training sample: firm = CIK, attack_date)
python3 -m cyberrisk.pipeline measure --disclosures cyberrisk/data/disclosures.jsonl \
    --attacks cyberrisk/data/prc/training_sample.csv --out cyberrisk/data/cyber_risk.csv \
    --lm AI_Innovation_Atlas_data/02_data_sources/other_public/loughran_mcdonald_dictionary/Loughran-McDonald_MasterDictionary_1993-2025.csv
```

Set `EDGAR_USER_AGENT="name email"` (SEC fair-access rule; 10 requests/s max, the fetcher sleeps).
Raw EDGAR gives bold/italic risk-factor titles (the paper's stopping rule); EDGAR-CORPUS is plain
text, so the 10-sentence fallback window applies to every sentence.  Sizes: the 10-K index rows
for 2006-2019 are ~110k filings (a complete submission is 1-20 MB); EDGAR-CORPUS is ~1.8 GB per
year.  The 2026-09-19 run (below) used the raw-EDGAR path on a sample.

## Reproducing the numbers in `EVALUATION.md` section 9

```bash
python3 -m cyberrisk.link_prc                        # PRC -> CIK link: data/prc/link_prc_cik.csv (288 incidents, 215 firms)
python3 cyberrisk/data/run/run_download.py           # 10-Ks of the training + Table 1 firms and a 450/yr random draw;
                                                     # writes sample_accessions.json (the whole draw, 5,823 filings)
python3 - <<'PY'
import json, pickle, pandas as pd
from cyberrisk import replicate_text as R
acc = set(json.load(open("cyberrisk/data/run/sample_accessions.json")))
ok, vocab, counts, link, _ = R.compute(RUN_DIR, "cyberrisk/data/prc/link_prc_cik.csv", acc,
    LM_CSV, ENTITY_MASTER_CSV, "cyberrisk/data/ff", cache="cyberrisk/data/roots_cache.json", index_csv=EDGAR_INDEX_CSV)
out = R.report(ok, vocab, counts, link); out["table6_model1"] = R.table6_model1(ok, link)
PY
```

The numbers in section 9 (run v6) were produced in steps, not by one fresh run: `run_download.py`
with the earlier 218-incident link (7,741 filings) → `pipeline.reextract` → the 649 10-Ks of the 54
firms the rule-R* link added (same `target_rows` call), concatenated and re-extracted into
`data/run/v5` → `compute` on `data/run/v5` with the whole draw as the sample.  A fresh
`run_download.py` with the current link fetches both sets at once; that path has not been re-run
end to end.

`LM_CSV`, `ENTITY_MASTER_CSV` (SIC per CIK) and `EDGAR_INDEX_CSV` are the files under
`AI_Innovation_Atlas_data/02_data_sources/` named in `EVALUATION.md`.

## Data the paper uses that is licensed (WRDS) — expected columns

* Compustat annual (`comp`): gvkey, fyear, datadate, cik, sic, au, at, ceq, prcc_f, csho, che, ib, dp, dvc, oibdp, ppent, xrd, dltt, dlc
* CRSP monthly (`crsp_m`): permno, date, ret, prc, shrout;  CRSP daily (`crsp_d`): permno, date, ret, prc, vol
* CRSP-Compustat link (permno ↔ gvkey) and WRDS SEC Analytics `wrds_forms` (cik, accession, fyear) for the Item 1A → Compustat link
* Thomson-Reuters 13F (`tr13f`): permno, rdate, mgrno, shares
* BoardEx (`boardex`): gvkey, fyear, n_directors, n_independent, committee_names
* FactSet Revere: SolarWinds key customers (38 U.S.-listed, direct and reverse relationships) → list of permnos
* Bloomberg: daily attention score → AIA dummy (max score 3 or 4 in the 5 trading days after 2020-12-14)
* Factiva: the "major" flag of each PRC hacking incident (global outlets / major newswires)
* DISCERN patents: patent flow and stock per firm-year; Hassan et al. / Sautner et al. risk measures (IA11)

The functions take these as DataFrames with exactly those column names; nothing else is assumed.

**Getting them (QUT):** the QUT library subscribes to WRDS with CRSP, Compustat, BoardEx and Audit
Analytics; Thomson-Reuters 13F, FactSet Revere, Bloomberg and Factiva are not in its list.  With a
WRDS account (register at wrds-www.wharton.upenn.edu, institution Queensland University of
Technology, university email; the library's WRDS representative approves it):

```bash
pip install --no-deps wrds && pip install sqlalchemy psycopg2-binary   # plain `pip install wrds` pins
                                                                        # pandas<2.3 and downgrades it; pandas 2.2.3
                                                                        # segfaults under Python 3.14 here
python3 -m cyberrisk.wrds_extract --user YOUR_WRDS_USERNAME --only libraries   # what the account can read
python3 -m cyberrisk.wrds_extract --user YOUR_WRDS_USERNAME                    # CRSP, Compustat, link tables
```

The extractor was written before an account existed and has not run against the live server; its
first run records in `data/wrds/access.json` which tables the account can read.

## Tests (`python3 -m pytest cyberrisk/tests -q`)

* `test_appendix_a2.py` — the extractor on the real Apple / Abbott / GM / Verizon FY2017 10-Ks against the paper's Appendix A.2 sentence lists.
* `test_text_modules.py` — Appendix A rules, sentence splitter, roots / vocabulary, Eq. (1)-(2) windows, Table 2 features, PRC filters.
* `test_finance_synthetic.py`, `test_tables_synthetic.py` — every table routine on a synthetic economy with a planted premium (shapes, signs, planted effects recovered).
* `test_variables.py` — Appendix B formulas against hand-computed values; the CIK → gvkey → permno link.
* `test_weighting_and_car.py` — buy-and-hold portfolio weights inside a holding period and market-model CAR alignment, both against hand calculations.
* `test_edgar_raw.py`, `test_coverage_gaps.py` — the raw-EDGAR path, the PRC loader on the real sample export, the Ken French readers, the pipeline, and the robustness helpers.
* `test_replicate_text.py` — the attack-count definitions, the PRC link rebuilt row for row, and the headline numbers of run v6 pinned (skipped when the run output is absent).

74 tests; 79% line coverage on 2026-09-20 without the network test (`fetch_data.py` and `wrds_extract.py` are at 0%; the run-level modules `link_prc.py`, `replicate_text.py` are exercised mainly by the real run and pinned by the regression tests).  Tests that hit the network (SEC EDGAR, Google Trends) are skipped unless you
pass `--run-network`.
