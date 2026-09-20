"""One-off driver for the 2026-09-19 text-half run (sets A, B, C in pipeline order)."""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
# SEC fair access asks for a contact in the User-Agent; set EDGAR_USER_AGENT="Name email" before running
os.environ.setdefault("EDGAR_USER_AGENT", "academic replication contact@example.edu")
import pandas as pd
from cyberrisk.pipeline import target_rows, sample_rows, disclosures_edgar_parallel
IDX = "AI_Innovation_Atlas_data/02_data_sources/sec_edgar/full_index_all/edgar_filings_index_1993_now_atlas_forms.csv"
RUN = "cyberrisk/data/run"
if __name__ == "__main__":
    link = pd.read_csv("cyberrisk/data/prc/link_prc_cik.csv", dtype={"cik": str})
    table1 = ["1618921", "1613665", "1053352", "1050606", "1093557", "106535", "4447", "945983", "812128", "29905"]
    A = target_rows(IDX, set(link["cik"]) | set(table1), years=range(2005, 2020))
    seen = {r["file_name"] for r in A}
    drawn = sample_rows(IDX, 450, seed=20260919, years=range(2007, 2020))
    C = [r for r in drawn if r["file_name"] not in seen]          # download each filing once
    rows = A + C
    json.dump({"A_B_targets": len(A), "C_sample": len(C)}, open(f"{RUN}/plan.json", "w"))
    # the scored sample is the whole draw: a drawn filing of a training / Table 1 firm is downloaded
    # through A but still belongs to the random sample (EVALUATION.md section 10, row 11)
    json.dump(sorted({os.path.basename(r["file_name"]).replace(".txt", "") for r in drawn}),
              open(f"{RUN}/sample_accessions.json", "w"))
    os.makedirs(f"{RUN}/v3", exist_ok=True)
    print("targets", len(A), "sample", len(C), flush=True)
    disclosures_edgar_parallel(rows, f"{RUN}/v3/disc", workers=8)
    print("DONE", flush=True)
