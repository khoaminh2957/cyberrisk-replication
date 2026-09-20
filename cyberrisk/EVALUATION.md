# Đánh giá tổng quan — tái lập *Cybersecurity Risk* (Florackis, Louca, Michaely & Weber, RFS 2023)

Ngày 2026-09-09. Mục tiêu đặt ra: dựng lại toàn bộ bài, kiểm tra nhiều vòng, giống 100%, không làm thừa.

## 1. Kết luận (cập nhật 2026-09-20)

* **Phương pháp của bài được dựng lại, một module cho một bước** (bảng phủ ở mục 2): 12 bảng, 2 hình kết quả (Hình 3 của bài là dòng thời gian vụ SolarWinds, không phải kết quả, nên không dựng), Phụ lục A và B, IA7–IA14. Ngoại lệ: biến patent flow/stock chưa cài; AIA (Bloomberg) là đầu vào, code không tính.
* **Nửa văn bản đã ra số trên dữ liệu công khai** (mục 9, lần chạy v6): 8,390 hồ sơ 10-K tải từ EDGAR; mẫu huấn luyện dựng từ PRC 2005–2018, 288 vụ nối được với 215 công ty. Các con số của bài tái lập được:

| Con số của bài | Bài | Bản này |
|---|---|---|
| Bảng 3: mean / trung vị / P75 / P99 điểm rủi ro | 0.24 / 0.28 / 0.45 / 0.61 | 0.254 / 0.323 / 0.468 / 0.613 |
| Tỷ lệ điểm 0 năm 2018 | 10.59% | 9.2% |
| Bảng 1: Weyerhaeuser FY2015 (điểm thấp nhất bài) | 0.036 | 0.039 |
| Bảng 1: 10 công ty-năm, sai lệch tuyệt đối trung bình | – | 0.037 |
| Bảng 2: toàn bộ ma trận 21 ô, sai lệch trung bình | – | 0.057 |
| Hình 1: 12 năm, sai lệch tuyệt đối trung bình so với số đọc từ biểu đồ | – | 0.023 |
| Hình 2: tương quan hạng thứ tự 12 ngành | – | 0.92 |
| Top-20 từ trùng | 20 | 18 |
| Bảng 6 Model 1 (logit tấn công năm sau): dấu và t-stat | +, 7.10 | +, 7.95 |

* **Kiểm chứng mạnh nhất (2026-09-20, mục 13):** tác giả có công bố thước đo của họ trên Harvard Dataverse. Nối theo tên công ty, trên 1,716 công ty-năm chung, **tương quan giữa điểm của bản này và điểm của tác giả là 0.953** (Spearman 0.942), trung bình 0.2672 so với 0.2675. Đây là đối chiếu ở mức từng công ty-năm, mạnh hơn mọi so sánh theo thống kê tổng hợp.
* **Không giống hệt, và không thể giống hệt bằng dữ liệu công khai**:
  * hệ số Bảng 6 là 1.32 so với 0.961 (khoảng tin cậy 95% [0.99, 1.65] so với khoảng ≈ [0.70, 1.23] của bài);
  * trung vị điểm là 0.323 so với 0.28, cao hơn bài ở cả hai nửa khi chia đôi mẫu (mean, P75, P99 thì sát);
  * tỷ lệ công ty có disclosure thấp hơn bài 8.0 điểm % năm 2007, 11.4 năm 2010, ít nhất 6.9 năm 2012; tỷ lệ điểm 0 năm 2011 cao hơn bài 6.7 điểm %;
  * ở Bảng 1, Great Western Bancorp thấp hơn bài 0.072, còn Hess, Wayside, Sanderson Farms, Dover cao hơn bài 0.02–0.10;
  * số vụ tấn công là 244 theo định nghĩa "+ex-ante disclosure" và 218 nếu thêm "+listed", so với 175.

  Không khác biệt nào có cơ chế được xác lập; các ứng viên ở mục 9. Bốn đầu vào của bài không có ở đây: mẫu Compustat, cờ "major" của Factiva, bảng nối tên làm tay của tác giả, và toàn bộ corpus. Vì corpus nhỏ hơn, từ vựng có 2,092 gốc từ so với 3,210 của bài.
* **Nửa tài chính (Bảng 4–5, 7–12, IA) chưa ra số**: cần CRSP/Compustat/13F/BoardEx/FactSet/Bloomberg. Không có tài khoản WRDS. Code đã viết theo bài, kiểm bằng dữ liệu tổng hợp và bằng ví dụ tính tay; phần này bị chặn bởi dữ liệu, không phải bởi code. Còn 15 lỗi code đã xác nhận ở nửa này chưa sửa: 6 ở mục 11.3 và 9 ở mục 12.3.
* **Test**: 80 test, 79 pass; 1 test mạng chỉ chạy khi bật `--run-network`. Kết quả giống nhau qua 5 hash seed. Độ phủ mã nguồn 79% (đo 2026-09-20, không chạy test mạng). Hai file 0% là `fetch_data.py` (tải dữ liệu) và `wrds_extract.py` (chưa chạy vì không có WRDS). Các con số chính được ghim bằng test hồi quy.

## 2. Bảng phủ

| Phần của bài | Code | Đã kiểm bằng | Dữ liệu |
|---|---|---|---|
| §2.2 crawl 10-K/10-K405/10-KSB40, bỏ /A, năm tài chính + CIK từ header, Item 1A, loại incorporate-by-reference | `edgar.py`, `pipeline.disclosures_edgar` | 8 hồ sơ 2006 thật chạy end-to-end; 4 hồ sơ 2017 thật (Phụ lục A.2); 8,390 hồ sơ 2005–2019 (mục 9) | EDGAR (miễn phí) + index 1993–2026 đã có trong `AI_Innovation_Atlas_data` |
| Phụ lục A.1: bảng từ khóa trực tiếp/gián tiếp, prefix, relevant/irrelevant hit, cửa sổ tới tiêu đề in đậm/nghiêng hoặc 10 câu | `keywords.py`, `extract.py` | **68/68 câu đúng trạng thái bắt/bỏ như bài** (64 bắt, 4 bỏ sót đúng như bài); 7 test luật trong `test_text_modules.py` cộng 4 test Phụ lục A.2 | – |
| §2.3 mẫu huấn luyện PRC: bỏ GOV/EDU/NGO, chỉ HACK, cờ "major" (Factiva), nối tên → công ty | `training.py`, `link_prc.py` | số vụ theo năm so với Hình 1 (mục 9.1); bảng nối theo một quy tắc cố định (mục 5 #33), dựng lại được, có test | PRC export gốc + Tableau archive (miễn phí); Factiva không có |
| §2.4 loại từ, gốc từ, tần suất ≥ 10, vector đếm, cosine & Jaccard, cửa sổ 1 năm/2 năm | `roots.py`, `measure.py` | unit test cửa sổ, loại trừ chính mình, ngưỡng tần suất áp trên từ trước khi quy gốc; 8,390 hồ sơ: 18/20 từ top-20 trùng bài | WordNet (MW bị chặn) |
| §3.2 Bảng 2: số câu CRD, tỷ lệ, từ tiêu cực/chính xác/pháp lý (LM), bảo hiểm mạng | `language.py` | unit test, kể cả luật bảo hiểm "một phần" trong cùng câu | LM 1993–2025 đã có trên đĩa |
| Phụ lục B: các biến, trừ patent flow/stock (chưa cài) | `variables.py` | ví dụ tính tay cho từng biến đã cài (`test_variables.py`); biến "đã từng bị tấn công" chỉ có test tổng hợp | Compustat/CRSP/13F/BoardEx |
| §3 Bảng 1–6, Hình 1–2 | `validation.py` | tổng hợp: dấu + hình dạng | panel firm-year |
| §4.1–4.2 Bảng 7–8 | `portfolios.py` | tổng hợp: P1 = điểm 0, 133 tháng 03/2008–03/2019, phần bù cấy được thu hồi (t > 2), alpha FF5 > 0 | CRSP + Ken French (đã tải) |
| §4.3 Bảng 9 | `fama_macbeth.py` | tổng hợp: hệ số cấy thu hồi | – |
| §4.4 Bảng 10: nhân tố 2×5 (3, 10), Google SVI cửa sổ chồng 100 ngày, SVI bất thường, dummy 1.5/2 SD, 2/4 tuần, placebo +5 ngày/+1 tháng | `factor.py`, `gtrends.py` | Trends thật: vụ Equifax 09/2017 được cờ đúng ngày; tổng hợp: β < 0 khi cấy | Google Trends (miễn phí, có rate limit) |
| §5 Bảng 11–12 SolarWinds | `solarwinds.py` | tổng hợp: CAR P10−P1 < 0 khi cấy | CRSP daily, FactSet, Bloomberg |
| §6 IA7 A–L, IA8–IA14, Oster | `robustness.py` + tùy chọn `auditor=` (measure), `rebalance=` (portfolios), `k=` (factor) | unit test helper | như trên |

## 3. Các vòng kiểm tra

1. **Vòng 1 — ground truth của bài (dữ liệu thật).** `tests/test_appendix_a2.py`: tải 4 hồ sơ 10-K FY2017 từ EDGAR, tách Item 1A, chạy thuật toán, so từng câu với Phụ lục A.2. Kết quả: trạng thái bắt/bỏ trùng 68/68; số câu bắt trùng 23/23, 8/8, 20/20, 13/13. Nhãn *loại câu* (Direct/Company Business/…) trùng 58/64 — và 58 là mức tối đa với **mọi** thứ tự ưu tiên có thể (đã thử cả 24 hoán vị): 6 câu còn lại bài gắn nhãn không suy ra được từ bảng luật đã in (ví dụ Apple #7 chứa "security breach" — từ khóa trực tiếp — nhưng bài ghi Indirect). POST-HOC: nhãn loại câu trong phụ lục không phải là hàm tất định của bảng luật; nhãn không ảnh hưởng đến thước đo (vector lấy toàn bộ câu bắt được).
2. **Vòng 2 — unit test luật và toán** (`test_text_modules.py`, `test_finance_synthetic.py`, `test_tables_synthetic.py` và các file test còn lại; số test hiện tại ở mục 1). Cửa sổ 10 câu (không phải 11), dừng tại tiêu đề, cửa sổ 2 năm dự phòng, loại trừ chính mình, P1 = điểm 0, mẫu 03/2008–03/2019 đúng 133 tháng, Fama-MacBeth và CAR có test riêng; Newey-West và logit có test đối chiếu với một cài đặt thứ hai (thêm 2026-09-20); hiệu ứng cố định hai chiều chỉ được chạy gián tiếp qua test bảng trên dữ liệu tổng hợp — và mục 12 cho thấy chỗ đó có lỗi bậc tự do.
3. **Vòng 3 — audit theo từng trang bài.** Kế hoạch là ba tác nhân độc lập đọc PDF gốc; cả ba bị API cắt (rate limit) trước khi ra bất kỳ phát hiện nào. Vòng này do tôi tự làm — tức là **không độc lập** với người viết code, nên yếu hơn một audit độc lập. Phát hiện và xử lý ở mục 4.
4. **Vòng 4 — chạy lại toàn bộ sau sửa + mẫu dữ liệu thật**: 8 hồ sơ 2006 (đường raw EDGAR), 400 văn bản Item 1A 2019 (đường EDGAR-CORPUS) → từ vựng, vector, thước đo, Bảng 2 chạy thông; top-20 từ trùng bài 16/20.
5. **Vòng 5 — ra số trên dữ liệu thật (2026-09-19).** 7,741 10-K, mẫu huấn luyện từ PRC; so từng con số của bài có thể tính bằng dữ liệu công khai (mục 9). Vòng này tìm ra 10 lỗi (mục 10), trong đó có một luật do chính tôi thêm và bị thí nghiệm bác bỏ. Kết quả chính được tính lại lần hai bằng cài đặt độc lập (8/8 trùng tới 1e-9).
6. **Vòng 6 — kiểm tra hallucination (2026-09-19, tối).** Hai agent đối chiếu độc lập (số của bài với PDF; code với định nghĩa của bài và với tài liệu này), rồi tôi đo lại mọi con số từ dữ liệu đã lưu. Kết quả ở mục 11: không có số nào của bài bị bịa; 19 khẳng định sai trong tài liệu; 4 lỗi code sửa ngay (commit 8f3710e).
7. **Vòng 7 — sửa nửa văn bản và chạy lại (2026-09-19 → 20).** Sửa ba lỗi code của nửa văn bản mà vòng 6 xác nhận: thứ tự ngưỡng tần suất, luật bảo hiểm, quy tắc nối tên. Tải thêm 649 10-K của 54 công ty mới nối (lần chạy v5). Tìm và sửa thêm một lỗi chọn mẫu (mục 10 dòng 11, lần chạy v6). Sau đó ghim lại test hồi quy, chạy lại năm biến thể Bảng 6 và bootstrap, và tính lại Eq. (1) độc lập trên v6 (8/8).

## 4. Kết quả audit vòng 3 (đối chiếu từng dòng với bài)

Ba tác nhân audit song song bị API cắt giữa chừng (session rate limit), nên vòng này do chính tôi
làm, đọc lại toàn văn bài và so từng mục. Kết quả:

**A. Đã đối chiếu ĐÚNG, từng mục:**

1. **Phụ lục A, bảng từ khóa** — đối chiếu từng dòng, từng từ của cả 4 nhóm (trực tiếp; gián tiếp
   2.1 company business, 2.2 internal, 2.3 legal, 2.4 economic). Không thiếu, không thừa, không sai
   chính tả. Một chỗ code sửa chữ của bài: dòng "Business | Adversely, material, harm disruptive,
   negative" được tách thành hai từ "harm" và "disruptive". Bản PDF ở đó **đọc được rõ** (kiểm lại
   2026-09-20, mục 12): bài in "harm disruptive" không có dấu phẩy. Đây là một **lựa chọn** (cụm
   "harm disruptive" gần như không bao giờ xuất hiện), không phải việc đọc một bản scan mờ.
2. **§2.2 loại hồ sơ**: bài dùng 10-K, 10-K405, 10-KSB40, bỏ bản sửa đổi (/A) → `edgar.FORMS`
   đúng nguyên văn. ĐO ĐƯỢC trên index dùng ở đây (đã lọc theo bộ form của Atlas): trong ba loại, các
   năm nộp 2004–2020 chỉ có 10-K (139,788 hồ sơ); 10-K405 xuất hiện lần cuối năm 2002. Index này
   không có 10-KSB40, nên không đo được loại đó có mặt trong kỳ mẫu hay không.
3. **§2.2 liên kết dữ liệu**: "link ... using the fiscal year, the CIK, and the mapping table from
   the WRDS SEC Analytics suite" → đã bổ sung `variables.link_disclosures` (CIK+fyear → gvkey →
   permno, tôn trọng cửa sổ hiệu lực của CCM link). Trước audit bước này chỉ nằm trong tài liệu.
4. **§2.4 Eq. (1)–(2)** và **footnote 9** (không có tấn công trong 1 năm thì lùi 2 năm) → khớp.
5. **§4.1 Bảng 7**: tercile (P1 = không có disclosure), hình thành cuối mỗi quý từ 12/2007, nắm giữ
   quý kế, 03/2008–03/2019, EW/VW, alpha CAPM/FFC/FF5, Newey-West 12 lag (footnote 11), loại công ty
   < 3 năm và không có disclosure suốt kỳ → khớp; số tháng 133 đúng.
6. **§4.4 Bảng 10 và footnote 14**: 2 nhóm quy mô × k nhóm rủi ro (k = 5 chuẩn, 3 và 10 kiểm tra),
   trung bình hai danh mục cao trừ trung bình hai danh mục thấp, value-weighted, dữ liệu ngày → khớp.
   Placebo +1 tuần giao dịch và +1 tháng giao dịch → tham số `shift_days`.
7. **§5 Bảng 11–12**: ngày sự kiện 14/12/2020, CAR[−1,+1] và CAR[−1,+3] bằng market model, điểm
   ex ante 2018 (2017 nếu thiếu), Panel A dùng decile trên/dưới, Panel B dùng biến liên tục +
   dummy tercile trên + dummy decile trên, Table 12 AIA (Bloomberg 3 hoặc 4 trong 5 ngày) → khớp.
   AIA là đầu vào lấy từ Bloomberg; code nhận nó, không tính nó.
8. **Phụ lục B**: các biến đã cài được kiểm bằng ví dụ tính tay (`tests/test_variables.py`; danh
   sách này viết lại 2026-09-20 sau khi thêm test): Tobin's q, ROA = oibdp/at, tangibility =
   ppent/at, R&D thay NaN bằng 0, leverage, asset growth, firm age theo lần đầu xuất hiện trong
   Compustat, momentum t−11..t−1, reversal r(t), beta và IVOL (độ lệch chuẩn phần dư FF3) trên
   cửa sổ 60 tháng, CoSkew, illiquidity Amihud, MAX = trung bình 5 lợi suất ngày cao
   nhất, NCSKEW, EXTR_SIGMA, cash-flow volatility theo ngành, institutional ownership chỉ tính tổ
   chức giữ > 5%, risk committee, secrets (cả biên cửa sổ 5 từ). Chưa cài: patent flow/stock. Biến
   "đã từng bị tấn công" chỉ có test tổng hợp.

**B. Ba điểm code LỆCH so với bài — đã sửa trong vòng này:**

9. **Bảng 5 (§3.5)** — bài chỉ nói *"Cybersecurity risk is measured at the beginning of each year"*;
   code cũ trễ (lag) cả biến kiểm soát. → Sửa: chỉ trễ điểm rủi ro, biến kiểm soát cùng kỳ.
   Hệ quả nếu không sửa: mẫu mất một năm đầu của mỗi công ty và hệ số kiểm soát lệch.
10. **IA10 placebo (§6.2)** — bài xây một thước đo giả từ phần Item 1A *không* liên quan an ninh
    mạng (universe 15,452 từ, cùng mẫu huấn luyện) rồi cho thấy nó *không dự báo nhất quán*
    ("not a consistent predictor") lợi nhuận và vụ tấn công. Code cũ
    chỉ ghi trong tài liệu, chưa có hàm. → Thêm `robustness.placebo_disclosures` +
    `robustness.placebo_measure`; đã chạy thử trên 4 hồ sơ thật.
11. **Bảng 6, độ lớn kinh tế 92.70%** — bài không nói con số đó lấy từ Model 1 hay Model 2. Code cũ
    chỉ tính từ Model 1. → Sửa: trả về cả hai, không chọn thay bài.

**C. Một lựa chọn được dữ liệu của bài xác nhận một phần:**

12. Bài chỉ nói khớp theo tiền tố cho *từ khóa chính* ("captures all the words that start with the
    relevant keyword"), không nói gì cho danh sách relevant/irrelevant. **Thí nghiệm** (chạy lại
    toàn bộ Phụ lục A.2 với hai biến thể): khớp tiền tố cho danh sách relevant → **68/68** câu đúng;
    khớp nguyên từ → **67/68**, mất đúng câu Abbott #5 mà bài ghi là bắt được (câu đó cần
    "increase" khớp "increased costs"). Với danh sách **irrelevant**, tiền tố và nguyên từ đều cho
    68/68, nên A.2 không phân biệt được. Dấu hiệu duy nhất ở danh sách này là chữ của bài: bảng ghi
    "Terror", văn bản ghi "terrorist". Code áp tiền tố cho cả hai danh sách. Hệ quả ở danh sách
    irrelevant: "war" loại cả "warehouse", "warranties", "warning". Kết luận: tiền tố ở danh sách
    relevant có thí nghiệm phân biệt; ở danh sách irrelevant đó là lựa chọn.

**C2. Một mâu thuẫn TRONG CHÍNH BÀI, giải được bằng số liệu của bài:**

13. Phụ lục B định nghĩa *Readability* = "file size in **megabytes** of the SEC complete submission
    text file", nhưng Bảng 3 in mức 10,453,409 (trung bình) / 6,163,418 (trung vị) — là **byte**.
    **Thí nghiệm phân biệt**: lấy log của cả 5 phân vị mức trong Bảng 3 rồi so với 5 phân vị của
    biến *Readability (ln)* cùng bảng (log của trung vị = trung vị của log, nên hai dòng phải khớp
    nếu cùng một đại lượng): đọc là byte → 12.86 / 14.44 / 15.63 / 16.54 / 17.78, **khớp cả 5 con
    số in trong bài**; đọc là megabyte → ln(trung vị) = 1.82 thay vì 15.63. Kết luận: mức là byte,
    và `Readability (ln)` = ln(byte). Code sửa theo bằng chứng này, kèm chứng cứ trong docstring.
    Kiểm chéo tương tự cho *Risk section length*: năm phân vị mức (1, 138, 226, 346, 841) chỉ khớp
    năm phân vị của dòng (ln) trong bài (0.69, 4.93, 5.42, 5.85, 6.74) khi đọc là ln(1 + n); ln(n)
    cho ln 1 = 0.00 (§11.1). Cả hai cặp nay là test cố định.

**D. Không phát hiện lỗi số học** trong các đoạn dễ sai: trọng số buy-and-hold trong kỳ nắm giữ
(kiểm bằng ví dụ tính tay, gồm cả trường hợp cổ phiếu bị huỷ niêm yết giữa kỳ), và căn ngày của CAR
(cửa sổ [−1,+1] và [−1,+3] cho ra đúng con số cấy sẵn; cửa sổ sự kiện thiếu ngày trả NaN chứ không
trả 0). Hai kiểm tra này nay là test cố định.

**E. Độ phủ test: 79%** mã nguồn (không tính file test), đo bằng `coverage` ngày 2026-09-20 với 80 test, không chạy test mạng. Các con số ghi trước đây (91.5%, 88%, 77%) đo trên bộ code và bộ test của thời điểm khác; không dùng nữa. Phần chưa phủ chủ yếu: tải dữ liệu (`fetch_data.py` 0%), trích xuất WRDS (`wrds_extract.py` 0%, chưa chạy vì không có tài khoản), các nhánh gọi mạng của `pipeline.py` và `gtrends.py`. Test mạng chạy bằng `--run-network`; lần chạy gần nhất là 2026-09-19, pass.

## 5. Những điểm bài KHÔNG nêu rõ, code phải tự chọn (mỗi điểm ghi trong docstring)

Nhãn theo RULE 0: đây là **lựa chọn**, không phải "bài làm vậy".

| # | Điểm | Lựa chọn trong code | Thay thế hợp lý |
|---|---|---|---|
| 1 | Prefix match có áp dụng cho danh sách relevant/irrelevant không (bài chỉ nói cho từ khóa chính) | có, cho cả ba danh sách. Danh sách relevant: A.2 xác nhận (68 so với 67). Danh sách irrelevant: A.2 không phân biệt, đây là lựa chọn (mục 4 C12) | exact word cho hit list |
| 2 | Câu tiêu đề của chính đoạn có được bắt không | có, nếu là direct hit (Apple #1 xác nhận) | – |
| 3 | Công ty bị tấn công có so với chính văn bản của mình không | không (loại trừ chính mình) | có (cosine = 1 kéo điểm lên) |
| 4 | N_{t−1} đếm gì khi công ty bị tấn công không có 10-K trong cửa sổ | chỉ đếm công ty có văn bản | đếm tất cả, đóng góp 0 |
| 5 | Văn bản "quá khứ" của công ty huấn luyện là bản nào | bản mới nhất nộp trong cửa sổ trước ngày nộp của i | bản trước ngày bị tấn công |
| 6 | Stop words / "common words" | danh sách NLTK + modal (không dùng sklearn vì list đó chứa "system", một từ top-20 của bài) | – |
| 7 | "Từ chỉ địa danh hoặc tên" | gazetteer nhỏ + token chỉ xuất hiện viết hoa (trừ đầu câu) | NER |
| 8 | Gốc từ | WordNet lemma (MW 403 khi crawl, đo được); adapter MW API nếu có key | – |
| 9 | "Precise words" là danh sách LM nào | Strong_Modal | 1 − (Uncertainty ∪ Weak_Modal) |
| 10 | Cyber insurance = "chỉ bảo hiểm một phần" (bài đọc tay) | regex cụm "insufficient / may not cover / could exceed…" nằm **trong cùng câu** với "insurance" (từ v5; trước đó hai thứ có thể ở hai câu bất kỳ) | đọc tay như bài |
| 11 | Điểm dùng ở ngày hình thành danh mục là bản nộp gần nhất trong bao lâu | ≤ 366 ngày | không giới hạn |
| 12 | Trọng số trong quý nắm giữ | buy-and-hold từ trọng số hình thành | cân lại hằng tháng |
| 13 | Chuẩn hóa biến giải thích Bảng 9 | trong từng tháng (cross-section) | pooled |
| 14 | Xếp nhóm khi nhiều điểm 0 bằng nhau (quintile nhân tố, decile SolarWinds) | cut-point kiểu `xtile`: các giá trị bằng nhau chung nhóm thấp nhất. Khi hơn 1/k số điểm bằng 0, các nhóm kế tiếp rỗng; NaN rơi vào nhóm 1 (lỗi mở, §11.3) | rank(method="first") |
| 15 | Cửa sổ ước lượng market model cho CAR | (−250, −30) ngày giao dịch | (−120, −11), … |
| 16 | Sai số Bảng 11 B | OLS thường | HC1 |
| 17 | Số lag Newey-West cho hồi quy ngày (Bảng 10) | 12 như footnote 11 (bài không nói cho dữ liệu ngày) | 5 / 21 |
| 18 | "Dùng hacker và data breach *jointly*" | ngày cực đoan nếu **một trong hai** topic cực đoan | SVI cộng gộp |
| 19 | Geo của Google Trends | worldwide (mặc định Trends) | US |
| 20 | Lợi suất tuần riêng công ty (NCSKEW) | residual với ±2 lead/lag thị trường (Chen–Hong–Stein 2001) | chỉ đồng thời |
| 21 | R_max trong Oster (2019) | 1.3 × R² có kiểm soát (gợi ý của Oster) | 1.0 |
| 22 | Mẫu "sau 2011" (IA7 A) | hồ sơ nộp từ 13/10/2011 (ngày SEC ban hành hướng dẫn) | năm tài chính ≥ 2012 |
| 23 | EDGAR-CORPUS không có in đậm/nghiêng | luôn dùng cửa sổ 10 câu dự phòng của bài | dùng raw EDGAR (có tiêu đề) |
| 24 | "tần suất < 10" là tổng số lần xuất hiện hay số văn bản chứa từ | tổng số lần xuất hiện trong corpus | document frequency |
| 25 | Hình 1: "tương quan 0.72 với *phần trăm* tấn công mỗi năm" | tương quan với **số** vụ mỗi năm | chuẩn hoá theo số công ty |
| 26 | Bảng 6: 92.70% từ Model 1 hay Model 2 | trả cả hai, không chọn | – |
| 27 | Loại "incorporate by reference" | < 300 từ **và** có cụm "incorporated by reference" | chỉ cần có cụm |
| 28 | Năm tài chính của hồ sơ | quy ước Compustat: kỳ kết thúc tháng 1–5 tính về năm trước (bài nối theo fyear Compustat) | năm dương lịch của kỳ báo cáo |
| 29 | Vũ trụ "U.S.-listed" (CRSP) khi không có CRSP | tên sàn NYSE / NASDAQ / AMEX xuất hiện trong 40,000 ký tự đầu của 10-K (trang bìa và có thể phần sau nó) | có ticker hiện tại (thiên lệch sống sót) |
| 30 | Item 1A dạng "Not applicable" / "smaller reporting company" | loại khỏi mẫu như công ty không có Item 1A | chấm điểm 0 |
| 31 | Item 1A chỉ có trong mục lục, phần thân đặt tiêu đề "Risk Factors" | bỏ các đoạn mà ≥ 25% "câu" là số trang; nếu thiếu thì dùng tiêu đề "Risk Factors" tới Item 1B / Unresolved Staff Comments / Properties | – |
| 32 | Mẫu huấn luyện khi không có cờ "major" của Factiva | mọi vụ đã nối (biến thể bài báo cáo là "unchanged") | – (thiếu dữ liệu) |
| 33 | Nối tên PRC → công ty | quy tắc R*, viết lại sau audit 2026-09-19 (docstring `link_prc.py`). Nhận (a) chính công ty, dưới mọi tên đã dùng trong hồ sơ 2005–2019, hoặc tên công ty tiền nhiệm khi cổ phiếu niêm yết tiếp tục (Google → Alphabet); (b) đơn vị, thương hiệu, quỹ phúc lợi hay sự kiện của công ty tại ngày tấn công, nếu tên chứa một token đặc trưng trong lịch sử tên công ty (Blizzard → Activision Blizzard). Từ chối đơn vị khác tên, đơn vị đã bán, công ty tư nhân, 20-F/40-F, tên mơ hồ. Dòng nêu nhiều công ty lấy công ty nộp 10-K được nêu đầu tiên | tay của tác giả (không công bố) |
| 34 | Công ty bị tấn công không có câu an ninh mạng trong 10-K | không vào mẫu huấn luyện ("with available cybersecurity risk disclosures") | vào với vector rỗng (kéo điểm mọi người xuống) |
| 35 | Tỷ lệ từ (tiêu cực / chính xác / pháp lý) khi không có văn bản | NaN (tỷ lệ trên 0 từ không xác định) | 0 (tạo tương quan giả: 0.84 so với 0.03 của bài) |
| 36 | Mẫu tính Bảng 2 | công ty có văn bản an ninh mạng | mọi công ty (mục 9.5 báo cả ba biến thể) |
| 37 | Bảng 6 khi chỉ có mẫu ngẫu nhiên | case-control: đối chứng = mẫu ngẫu nhiên, ca = công ty-năm ngay trước vụ tấn công; độ dốc logit nhất quán (Prentice & Pyke 1979) | toàn bộ công ty-năm (cần tải mọi 10-K) |
| 38 | 10-K nộp chung nhiều CIK (US Airways Group / US Airways Inc) | là 10-K của mọi đơn vị cùng nộp; bản sao không vào mẫu chấm điểm | chỉ một CIK |
| 39 | Ngưỡng tần suất < 10 áp trên từ hay trên gốc từ | trên từ, trước khi quy về gốc (từ v5). Câu của bài: loại các loại từ, kể cả "words with a frequency less than 10", rồi mới lưu vector "using word roots". Đây là cách đọc thứ tự câu, không có thí nghiệm phân biệt | trên gốc từ (code trước v5) |
| 40 | "common words" trong câu loại từ của §2.4 | **không** loại (bài giữ "result", "include", "system" trong top-20 nên danh sách phải ngắn) | loại theo tần suất tài liệu |
| 41 | Cửa sổ ước lượng phần dư cho NCSKEW / EXTR_SIGMA | một hồi quy thị trường cho toàn bộ lịch sử tuần của công ty, rồi cắt theo năm dương lịch | hồi quy riêng từng công ty-năm |
| 42 | Ngưỡng tối thiểu cho beta và IVOL | dùng chung mức ≥ 24 tháng của CoSkew; bài chỉ nêu mức này cho CoSkew | không đặt ngưỡng cho beta/IVOL |
| 43 | Cửa sổ 60 tháng đếm theo dòng hay theo tháng dương lịch | theo dòng (`vals[k-59:k+1]`), nên chuỗi CRSP bị đứt sẽ trải dài hơn 60 tháng | theo tháng dương lịch |
| 44 | Ngày chú ý cực đoan rơi vào cuối tuần / ngày nghỉ | bỏ (dummy được chiếu về ngày giao dịch) | dời sang ngày giao dịch kế tiếp |
| 45 | IA7 panel B: "median industry value" | trung vị của các điểm **dương** trong ngành-năm | trung vị của mọi điểm, kể cả 0 |
| 46 | Các ngưỡng quan sát tối thiểu bài không nêu | Fama-MacBeth ≥ 30 cổ phiếu/tháng, CAR ≥ 60 ngày ước lượng, NCSKEW ≥ 26 tuần, nhân tố ≥ 2k cổ phiếu/tháng, cash-flow volatility ≥ 3 năm; t-test Welch cho Bảng 12 | các ngưỡng khác |
| 47 | Dòng từ khóa "Business" của bài in "harm disruptive" | tách thành "harm" và "disruptive" | giữ nguyên cụm |

Dòng #27, #28, #30 mô tả đường raw EDGAR, là đường dùng cho mọi con số ở mục 9. Đường EDGAR-CORPUS (chỉ dùng cho phép thử 400 văn bản ở mục 7) không áp `is_stub`, dùng quy tắc by-reference khác, và lấy năm tài chính = năm nộp − 1.

## 6. Truy cập dữ liệu (đo lại 2026-09-19)

| Nguồn | Trạng thái | Hệ quả |
|---|---|---|
| CRSP, Compustat, 13F, BoardEx, CRSP–Compustat link, WRDS SEC Analytics | giấy phép WRDS; không có tài khoản (2026-09-19). `wrds_extract.py` đã viết sẵn, chưa chạy | Bảng 4–5, 7–12, IA chỉ kiểm bằng dữ liệu tổng hợp |
| PRC chronology 2005–2018 | **có, miễn phí**: bản export gốc (mirror công khai, 8,202 dòng) + Tableau archive của chính PRC (9,015 dòng) dùng để kiểm chéo; `fetch_data prc` tải lại được đúng từng byte | mẫu huấn luyện đã dựng (mục 9.1) |
| Tableau archive của PRC | **ngày bị đảo tháng/ngày khi ngày ≤ 12** (Equifax 07/9/2017 lưu thành 2017-07-09; Anthem 05/02/2015 thành 2015-05-02). Thí nghiệm: 97.2% dòng của bản export có trong archive sau khi đảo lại, 62.5% nếu không | chỉ dùng archive để kiểm chéo |
| Factiva (cờ "major"), FactSet Revere (38 khách hàng SolarWinds), Bloomberg (AIA) | giấy phép. Bài mô tả việc làm tay cho phần Factiva (và cho việc nối tên), không cho FactSet hay Bloomberg | dùng biến thể "mọi vụ"; Bảng 11–12 chưa ra số |
| Merriam-Webster (gốc từ) | web 403 (Cloudflare) kể cả UA trình duyệt | WordNet; MW API nếu có key |
| EDGAR | đã tải 8,390 10-K (mục 9): 7,741 ở lần đầu, cộng 649 của 54 công ty mới nối theo quy tắc R*. Tải bằng stream, dừng ở cuối văn bản 10-K, 8 tiến trình (~2 request/s) | 460 MB trên đĩa (Item 1A đã tách, lưu cả cờ tiêu đề) |
| Google Trends | chạy được, rate limit 429 cần nghỉ vài giây/lần | chỉ cần cho Bảng 10 (cần CRSP) |

## 7. Quan sát trên dữ liệu thật (POST-HOC, không kèm cơ chế)

* 6/8 hồ sơ FY2005 không có câu nào về an ninh mạng; văn bản của bài ghi 28.75% công ty có disclosure năm 2007 (và dẫn tới Table IA.1). Hướng nhất quán; N = 8 nên không kết luận.
* 400 Item 1A năm nộp 2019 (split test của EDGAR-CORPUS): 35.5% không có câu nào bắt được; bài: 10.59% điểm 0 năm 2018. Khác biệt. **MECHANISM: UNKNOWN.** Ứng viên chưa phân biệt được: (a) corpus gồm cả công ty rất nhỏ ngoài CRSP/Compustat; (b) năm khác (FY2018 nộp 2019 vs FY2018 của bài); (c) văn bản thuần không có tiêu đề nên cửa sổ khác. Thí nghiệm phân biệt: chạy lại chỉ trên CIK có trong Compustat.
* Top-20 từ trên 400 văn bản trùng 16/20 với top-20 của bài (thiếu: computer, disruption, reputation, unauthorized). Quan sát về tiền xử lý; không suy ra gì về thước đo.

* **Cập nhật 2026-09-19, số đo lại 2026-09-20 (v6) — thí nghiệm cho ứng viên (a) đã chạy.** Trong mẫu ngẫu nhiên EDGAR, tỷ lệ điểm 0 của hồ sơ **không** niêm yết sàn cao hơn hồ sơ niêm yết (2018: 50.0% so với 9.2%, 90 hồ sơ không niêm yết; 2012: 73.5% so với 40.9%). Với bộ lọc niêm yết, tỷ lệ điểm 0 năm 2018 là 9.2% so với 10.59% của bài. Quan sát này nhất quán với (a); nó không loại trừ (b) hay (c). Số 61.9% / 9.7% ghi trước đây bị các Item 1A dạng "Not applicable" làm phình (§11.2 mục 2). Vì sao công ty không niêm yết ít viết về an ninh mạng thì **MECHANISM: UNKNOWN**.

## 8. Việc còn lại để ra phần còn thiếu của bài

1. **Nửa tài chính:** cần WRDS (chưa có tài khoản; `wrds_extract.py` tải đúng các bảng cần khi có). Kéo các bảng liệt kê trong README, chạy `variables.py` để dựng panel, rồi chạy `validation` (Bảng 4–5), `portfolios` (7–8), `fama_macbeth` (9), `factor` + `gtrends` (10), `solarwinds` (11–12), `robustness` (IA). Điểm rủi ro nối vào panel qua `variables.link_disclosures` (CIK + fyear → gvkey → permno).
2. **Tái lập đúng từng con số của nửa văn bản** cần thêm ba đầu vào của tác giả: cờ "major" của Factiva cho từng vụ, bảng nối tên tay của họ, và danh sách công ty-năm Compustat (để thay proxy niêm yết và tải đủ corpus cho từ vựng). Không đầu vào nào công khai.
3. **Nếu chỉ muốn thu hẹp sai lệch bằng dữ liệu công khai:** tải toàn bộ 10-K niêm yết 2006–2019, khoảng 45k hồ sơ, khoảng 7 giờ với 8 tiến trình, tức khoảng 5 lần mẫu hiện tại (8,390). Làm vậy chỉ thay đổi từ vựng và sai số chọn mẫu, không thay đổi ba đầu vào ở mục 2.

## 9. Kết quả bằng số trên dữ liệu công khai (lần chạy v6, 2026-09-20)

**Các lần chạy.** Mọi con số trong mục này là của v7 (v6 cộng bốn định nghĩa lấy theo code của tác giả, mục 13.2; thước đo và Bảng 6 không đổi). Lịch sử: v3 (7,741 hồ sơ, 2026-09-19) → v4 (sửa `is_stub`, §11.1) → v5 (quy tắc nối R*, ngưỡng tần suất trước gốc từ, bảo hiểm trong cùng câu; thêm 649 hồ sơ) → v6 (dữ liệu v5; mẫu ngẫu nhiên là toàn bộ lần rút, mục 10 dòng 11) → v7 (định nghĩa biến ngôn ngữ và độ dài mục rủi ro theo code tác giả). Số của các lần chạy cũ chỉ ghi khi cần so sánh.

**Thiết kế, chốt trước khi so với bài** (`replicate_text.py`):
* 10-K tải từ EDGAR: toàn bộ 10-K 2005–2019 của các công ty trong mẫu huấn luyện và 10 công ty ở Bảng 1, cộng một lần rút ngẫu nhiên 450 hồ sơ mỗi năm nộp 2007–2019. Lần rút có 5,850 dòng index, tức 5,823 hồ sơ khác nhau: một 10-K nộp chung có một dòng index cho mỗi CIK. Tổng 8,390 hồ sơ; mọi hồ sơ lỗi mạng đã tải lại được.
* **Mẫu chấm điểm** chỉ lấy từ lần rút ngẫu nhiên: có Item 1A, không incorporate by reference, 10-K ghi tên sàn niêm yết (mục 5 #29), năm tài chính 2007–2018, một hồ sơ cho mỗi (CIK, năm). N = 3,092 công ty-năm.
* **Mẫu ngẫu nhiên là đủ cho phân phối.** Điểm của một công ty chỉ phụ thuộc vào văn bản của chính nó và của mẫu huấn luyện, không phụ thuộc các công ty khác. Riêng bộ từ vựng thấy một corpus nhỏ hơn.
* **Mẫu huấn luyện:** mọi vụ HACK không thuộc GOV/EDU/NGO trong PRC 2005–2018, nối với CIK theo `link_prc.py` (quy tắc R*): 288 vụ, 215 công ty. Không có cờ "major", nên đây là biến thể "mọi vụ" mà bài báo cáo là "unchanged".
* **Giá trị Hình 1–2 của bài** là số tôi đọc trên biểu đồ. Đo pixel lại thì lệch tối đa 0.0012 (§11).

### 9.1 Mẫu huấn luyện — số vụ tấn công theo năm (Hình 1, số trong ngoặc)

Bốn cách đọc câu "175 cyberattacks ... with available cybersecurity risk disclosures in Item 1A", chốt trước khi xem số:

| năm | paper | linked | +ex-ante Item 1A | +ex-ante disclosure | +listed |
|---|---|---|---|---|---|
| 2005 | 1 | 2 | 0 | 0 | 0 |
| 2006 | 5 | 7 | 5 | 2 | 2 |
| 2007 | 7 | 16 | 13 | 9 | 7 |
| 2008 | 3 | 8 | 8 | 4 | 2 |
| 2009 | 3 | 6 | 5 | 4 | 3 |
| 2010 | 11 | 16 | 15 | 12 | 12 |
| 2011 | 8 | 10 | 8 | 6 | 4 |
| 2012 | 9 | 20 | 20 | 19 | 17 |
| 2013 | 24 | 29 | 28 | 25 | 24 |
| 2014 | 32 | 55 | 54 | 49 | 45 |
| 2015 | 16 | 26 | 26 | 25 | 21 |
| 2016 | 16 | 32 | 32 | 32 | 29 |
| 2017 | 24 | 38 | 36 | 35 | 32 |
| 2018 | 16 | 23 | 22 | 22 | 20 |
| total | 175 | 288 | 272 | 244 | 218 |

Cả bốn cột đều trên 175; cột gần nhất là "+listed" (218). Theo từng năm, 2013 gần bài (25 và 24 so với 24), còn 2012, 2014, 2016, 2017 cao hơn nhiều (ví dụ 2016: 32 so với 16). Từ v4 sang v5 (quy tắc R* cùng 649 hồ sơ tải thêm cho các công ty mới nối), cột "+ex-ante disclosure" tăng từ 184 lên 244. R* được viết sau khi đã thấy số v4 so với 175, để áp nhất quán một quy tắc (§11.2 mục 12). Nó đưa số đếm ra xa 175 hơn, nên không phải được chỉnh để khớp bài. **MECHANISM: UNKNOWN.** Ứng viên chưa phân biệt được: (a) bảng nối tay của tác giả hẹp hơn R*; (b) bài lấy PRC ở thời điểm khác (PRC có sửa lịch sử); (c) bài đếm theo đơn vị khác (cặp công ty–sự kiện so với dòng PRC).

### 9.2 Bảng 3 — phân phối điểm rủi ro

|  | paper | ours |
|---|---|---|
| mean | 0.240 | 0.254 |
| sd | 0.220 | 0.231 |
| p1 | 0.000 | 0.000 |
| p25 | 0.000 | 0.000 |
| p50 | 0.280 | 0.323 |
| p75 | 0.450 | 0.468 |
| p99 | 0.610 | 0.613 |

Chia đôi mẫu theo CIK chẵn/lẻ cho ra mean 0.257 và 0.251, trung vị 0.333 và 0.310 (bài 0.28), P99 0.620 và 0.598. Trung vị cao hơn bài ở cả hai nửa. **MECHANISM: UNKNOWN.**

### 9.3 Hình 1 — theo năm

| năm | n | mean | paper_mean(chart) | se | zero_share | disclosure_share |
|---|---|---|---|---|---|---|
| 2007 | 260 | 0.065 | 0.085 | 0.008 | 0.792 | 0.208 |
| 2008 | 228 | 0.064 | 0.097 | 0.008 | 0.772 | 0.228 |
| 2009 | 236 | 0.101 | 0.092 | 0.010 | 0.674 | 0.331 |
| 2010 | 217 | 0.093 | 0.127 | 0.011 | 0.724 | 0.276 |
| 2011 | 253 | 0.145 | 0.153 | 0.011 | 0.557 | 0.443 |
| 2012 | 264 | 0.259 | 0.218 | 0.014 | 0.409 | 0.591 |
| 2013 | 255 | 0.236 | 0.270 | 0.013 | 0.396 | 0.608 |
| 2014 | 291 | 0.332 | 0.335 | 0.012 | 0.244 | 0.756 |
| 2015 | 263 | 0.375 | 0.390 | 0.012 | 0.202 | 0.798 |
| 2016 | 289 | 0.377 | 0.403 | 0.011 | 0.180 | 0.820 |
| 2017 | 263 | 0.412 | 0.435 | 0.012 | 0.160 | 0.840 |
| 2018 | 273 | 0.485 | 0.455 | 0.010 | 0.092 | 0.908 |

Số của bài trong văn bản (Bảng IA.1 thuộc Internet Appendix, không có trong tay): tỷ lệ có disclosure là 28.75% năm 2007, 39% năm 2010, hơn 66% năm 2012, khoảng 90% năm 2018; tỷ lệ điểm 0 là 49.03% năm 2011 và 10.59% năm 2018. Ở đây năm 2018 khớp (90.8% và 9.2%). Tỷ lệ có disclosure thấp hơn bài 8.0 điểm % năm 2007, 11.4 năm 2010, ít nhất 6.9 năm 2012; tỷ lệ điểm 0 năm 2011 cao hơn bài 6.7 điểm %. Bài không cho tỷ lệ các năm 2008–2009.

So với số đọc từ Hình 1, điểm trung bình ở đây thấp hơn ở 2007, 2008, 2010, 2011 và 2013–2017, cao hơn ở 2009, 2012 và 2018. Sai lệch tuyệt đối trung bình là 0.023, lớn nhất 0.041 (2012). Khoảng tin cậy 95% chứa số của bài ở 5/12 năm: 2009, 2011, 2014, 2015, 2017. **MECHANISM: UNKNOWN.** Ứng viên: (a) proxy niêm yết khác vũ trụ Compustat/CRSP; (b) hồ sơ HTML/text đời đầu tách Item 1A và tiêu đề kém hơn; (c) mẫu huấn luyện các năm đầu nhỏ (0–12 vụ mỗi năm 2005–2011 theo cột "+ex-ante disclosure" ở 9.1).

### 9.4 Bảng 1 — mười công ty-năm được bài in điểm

| công ty | fyear | paper | ours | n_train | crd_sentences |
|---|---|---|---|---|---|
| Walgreens Boots Alliance | 2018 | 0.684 | 0.671 | 24 | 28 |
| Great Western Bancorp | 2016 | 0.683 | 0.611 | 29 | 34 |
| Heritage Commerce | 2017 | 0.676 | 0.653 | 30 | 35 |
| Salem Media Group | 2017 | 0.674 | 0.653 | 30 | 45 |
| Dexcom | 2017 | 0.670 | 0.633 | 30 | 43 |
| Weyerhaeuser | 2015 | 0.036 | 0.039 | 26 | 1 |
| Hess | 2012 | 0.052 | 0.071 | 18 | 1 |
| Wayside Technology | 2013 | 0.078 | 0.123 | 24 | 1 |
| Sanderson Farms | 2012 | 0.109 | 0.141 | 19 | 1 |
| Dover | 2012 | 0.111 | 0.213 | 18 | 2 |

Bảng 1 không phụ thuộc mẫu ngẫu nhiên, nên v5 và v6 giống nhau.

* Bốn trong năm công ty điểm cao nhất của bài có điểm ≥ P99 ở đây (0.613). Great Western Bancorp được 0.611, ngay dưới P99. Cả năm công ty thấp hơn bài 0.013–0.072.
* **Weyerhaeuser FY2015: 0.039 so với 0.036.** Thí nghiệm luật dừng (chạy trên v2): nếu thuật toán tìm vượt qua tiêu đề in đậm của chính mục rủi ro, điểm thành 0.457; dừng ở tiêu đề thì 0.033. Luật "vượt tiêu đề" đã gỡ (mục 10). Thí nghiệm thêm trên v4 (§11.2 mục 5): với từ vựng và mẫu huấn luyện ở đây, mọi tập câu có chứa câu bài trích ("We and our service providers employ what we believe are adequate security measures.") cho điểm 0.17–0.18, còn riêng dòng tiêu đề cho 0.033. Bằng chứng này **ủng hộ, chưa chứng minh** rằng thuật toán của bài không bắt câu trích đó, vì mẫu huấn luyện và từ vựng ở đây khác bài.
* Hess, Wayside, Sanderson Farms, Dover (1–2 câu bắt được) cao hơn bài 0.019–0.102. **MECHANISM: UNKNOWN.** Ứng viên: mẫu huấn luyện "mọi vụ" so với "major" của bài (điểm của văn bản 1–2 câu nhạy với thành phần mẫu huấn luyện); tách câu; từ vựng.

### 9.5 Bảng 2 — tương quan ngôn ngữ

Từ lần chạy v7, bốn biến ngôn ngữ theo **code của tác giả** (mục 13.2), không theo câu chữ Phụ lục B: mẫu số tỷ lệ từ là số từ sau khi loại, "precise" là **âm tỷ lệ từ Uncertainty**, `insurance` chỉ cần nhắc tới bảo hiểm. Cách đọc theo câu chữ của bài vẫn được tính và báo song song.

Cột "ours" tính trên công ty có văn bản an ninh mạng (N = 1,803):

|  | paper | theo code tác giả | theo câu chữ bài |
|---|---|---|---|
| crd_sentences | 0.569 | 0.596 | 0.596 |
| crd_sentences_ratio | 0.443 | 0.415 | 0.415 |
| negative_words | 0.033 | -0.064 | -0.066 |
| precise_words | 0.084 | -0.018 | -0.013 |
| litigious_words | 0.127 | 0.070 | 0.080 |
| cyber_insurance | 0.169 | **0.149** | 0.117 |

**Quan sát quan trọng, đo trên toàn bộ ma trận 21 ô:** theo code tác giả thì sai lệch trung bình là **0.073** (lớn nhất 0.277), còn theo câu chữ bài là **0.059** (lớn nhất 0.145). Nghĩa là đổi theo code của họ làm ô bảo hiểm gần bài hơn (0.117 → 0.149 so với 0.169) nhưng làm cả ma trận xa hơn. Thủ phạm là dòng "precise": ô *precise × negative* của bài in −0.145; dùng âm tỷ lệ Uncertainty cho **+0.132**, dùng Strong_Modal cho −0.065. Tức là **dòng `precise_w = - sent_uncert2_w` trong code của tác giả không tái lập được chính ô Bảng 2 của họ**. **MECHANISM: UNKNOWN**; ứng viên: file .do công bố là bản dọn lại sau, hoặc bảng in dùng định nghĩa khác. Chỉ 6 trên 21 ô là gần bài hơn khi theo code của họ.

Ba định nghĩa mẫu được chốt trước, so trên toàn bộ ma trận (tính theo định nghĩa biến hiện hành):

| Định nghĩa | Sai lệch trung bình | Sai lệch lớn nhất |
|---|---|---|
| (i) tỷ lệ từ = 0 khi không có văn bản, mọi công ty | 0.362 | 0.805 |
| (ii) tỷ lệ từ = NaN khi không có văn bản, từng cặp | 0.093 | 0.277 |
| (iii) chỉ công ty có văn bản | **0.073** | 0.277 |

Nhắc bảo hiểm: 11.4% số công ty-năm, bài 8.43%. Trong số đó 90.7% có điểm trên trung vị, bài 80%.

### 9.6 Từ vựng (§2.4)

Top-20 trùng **18/20** với bài; thiếu reputation, unauthorized, thay bằng attack, access. Từ vựng có 2,092 gốc từ so với 3,210 của bài. Ở v4 là 2,064; con số đổi vì hai thay đổi cùng lúc: thứ tự ngưỡng tần suất và 649 hồ sơ mới. Ngưỡng tần suất ≥ 10 áp trên từ trước khi quy gốc (mục 5 #39), trên corpus 8,390 hồ sơ. Corpus này nhỏ hơn corpus đầy đủ của bài, nên kích thước từ vựng không so trực tiếp được.

### 9.7 Hình 2 — theo ngành Fama-French 12

| ngành | ours_mean | ours_rank | paper_rank |
|---|---|---|---|
| Telcm | 0.311 | 2 | 1 |
| Shops | 0.315 | 1 | 2 |
| BusEq | 0.266 | 5 | 3 |
| Money | 0.283 | 3 | 4 |
| Utils | 0.266 | 4 | 5 |
| NoDur | 0.220 | 9 | 6 |
| Other | 0.260 | 6 | 7 |
| Chems | 0.227 | 7 | 8 |
| Hlth | 0.217 | 10 | 9 |
| Durbl | 0.226 | 8 | 10 |
| Manuf | 0.204 | 11 | 11 |
| Enrgy | 0.153 | 12 | 12 |

Tương quan hạng Spearman với thứ tự của bài: **0.92**. Năng lượng và Chế tạo đứng cuối ở cả hai.

### 9.8 Bảng 6, panel A, Model 1 — điểm dự báo vụ tấn công năm sau

Logit, hiệu ứng cố định năm và FF12, sai số cluster theo công ty, điểm chuẩn hóa. Không biến giải thích nào của Model 1 cần WRDS. Tuy vậy, mẫu của bài cần "complete risk disclosure and financial data", và mẫu ở đây không mô phỏng được điều đó. Thiết kế case-control như mục 5 #37: đối chứng là mẫu ngẫu nhiên, ca là 195 công ty-năm ngay trước vụ tấn công, N = 2,975.

| | Bài | Bản này |
|---|---|---|
| hệ số | 0.961 | 1.320 |
| t | 7.10 | 7.95 |
| N | 41,140 | 2,975 (case-control) |

Dấu và mức ý nghĩa tái lập được; độ lớn cao hơn khoảng 1.4 lần. **MECHANISM: UNKNOWN.** Ứng viên: (a) bài dùng toàn bộ công ty-năm (N = 41,140), không phải case-control; (b) định nghĩa "năm t+1" (năm dương lịch của vụ so với năm tài chính); (c) mẫu huấn luyện "mọi vụ". Pseudo-R² không so được. Dưới case-control, tỷ lệ ca là 6.6% (195/2,975). Trong mẫu của bài, tỷ lệ này tối đa 0.43% (175/41,140); đó là cận trên, vì không phải vụ nào cũng nằm trong mẫu Bảng 6.

**Thí nghiệm: năm biến thể, chốt trước lần chạy đầu trên v4, chạy lại trên v6 bằng cùng code.** Bài: 0.961 (t 7.10, SE ≈ 0.135, khoảng tin cậy ≈ [0.70, 1.23]).

| Biến thể | Hệ số | Khoảng tin cậy 95% | Ca | N |
|---|---|---|---|---|
| V0: năm dương lịch của vụ = năm tài chính + 1 | 1.320 | [0.995, 1.646] | 195 | 2,975 |
| V1: vụ trong 12 tháng sau kết thúc năm tài chính | 1.284 | [0.964, 1.603] | 194 | 2,976 |
| V2: vụ trong 12 tháng sau ngày nộp 10-K | 1.240 | [0.940, 1.540] | 200 | 2,981 |
| V3: hiệu ứng cố định FF48 thay FF12 | 1.164 | [0.822, 1.506] | 195 | 2,699 |
| V4: thêm biến đã từng bị tấn công | 1.238 | [0.924, 1.551] | 195 | 2,975 |
| V0 quy về độ lệch chuẩn 0.22 của bài | 1.258 | – | – | – |

Bootstrap theo công ty cho V0 (400 mẫu, không mẫu nào ước lượng hỏng): trung vị 1.327, khoảng tin cậy [1.05, 1.74]; 1/400 mẫu có hệ số ≤ 0.961.

Quan sát:
* Khoảng tin cậy của V2, V3, V4 chứa 0.961; của V0 và V1 thì không (cận dưới 0.995 và 0.964).
* Không biến thể nào đưa hệ số về gần 0.96; V3 kéo xuống nhiều nhất (−0.156).
* Qua các lần chạy, hệ số V0 là 1.540 (v4), 1.362 (v5), 1.320 (v6).

**MECHANISM: UNKNOWN** cho cả khoảng cách với bài lẫn mức giảm giữa các lần chạy. Các ứng viên chưa kiểm được đều cần dữ liệu không có: toàn bộ công ty-năm thay vì case-control, cờ "major" của Factiva, vũ trụ Compustat, bảng nối tên của tác giả.

### 9.10 Bảng 3 — Readability (bổ sung 2026-09-20)

Bài định nghĩa *Readability* là kích thước file "complete submission" của 10-K. Bộ tải ở đây dừng ở cuối văn bản 10-K nên không biết kích thước cả file; mục 12 (vòng 1) phát hiện ra chỗ thiếu này. Kích thước lấy từ kho submissions bulk của SEC (trường `size`, `pipeline.submission_sizes`). **Kiểm chứng:** với hồ sơ 0001341004-07-003146, trường này ghi 255,269 và file `.txt` tải về đúng 255,269 byte.

| phân vị | bài (byte) | bản này (byte) | bài (ln) | bản này (ln) |
|---|---|---|---|---|
| mean | 10,453,409 | 13,413,927 | 15.52 | 15.78 |
| sd | 11,546,923 | 18,473,190 | 1.22 | 1.25 |
| p1 | 384,975 | 252,225 | 12.86 | 12.44 |
| p25 | 1,865,855 | 2,684,668 | 14.44 | 14.80 |
| p50 | 6,163,418 | 9,280,731 | 15.63 | 16.04 |
| p75 | 15,323,736 | 18,174,560 | 16.54 | 16.72 |
| p99 | 52,900,376 | 72,463,896 | 17.78 | 18.10 |

N = 3,083 trên 3,092 công ty-năm (9 hồ sơ không có trong kho bulk). Hồ sơ ở đây lớn hơn của bài ở mọi phân vị trừ P1; trung vị lệch 0.41 đơn vị log. **MECHANISM: UNKNOWN.** Ứng viên chưa phân biệt được: (a) vũ trụ công ty khác (proxy niêm yết so với Compustat); (b) trường `size` của SEC tính cả phần XBRL đính kèm, còn bài có thể đo bản đã lưu của họ; (c) phân bố năm khác nhau, vì kích thước hồ sơ tăng mạnh theo thời gian.

### 9.9 Kiểm chứng lần hai (RULE 0 mục 5)

* **Eq. (1) tính lại độc lập** (numpy, tự lọc cửa sổ, không dùng `measure.py`) trên 8 công ty-năm ngẫu nhiên của v6: 8/8 trùng tới 1e-9. Trên v4, phép tính này lúc đầu chỉ khớp 6/8. Cả hai ca lệch đều có vụ US Airways trong cửa sổ; khi thêm bản sao của 10-K nộp chung thì khớp 8/8.
* **Mọi con số ở mục 9 được tính lại từ dữ liệu đã lưu** bằng một script riêng. Chạy trên v4, script đó cũng ra đúng các số v4 ghi ở §11: sai lệch trung bình Bảng 2 là 0.050, tỷ lệ điểm 0 là 50.0% / 9.4%, trung vị 314 câu.
* **Các con số chính được ghim** trong `tests/test_replicate_text.py` (v6, kể cả N = 3,092); bảng nối PRC dựng lại đúng từng dòng (288 dòng).
* **Bộ test ổn định qua 5 hash seed** khác nhau.

## 10. Lỗi phát hiện và sửa trong vòng 2026-09-19 → 20 (theo thứ tự tìm ra)

| # | Lỗi | Phát hiện bằng | Sửa |
|---|---|---|---|
| 1 | `fyear` = năm dương lịch của kỳ báo cáo | đối chiếu với quy ước Compustat mà bài dùng để nối | `edgar.compustat_fyear` |
| 2 | Item 1A dạng "Not applicable" / SRC được chấm điểm 0 | đọc Regulation S-K Item 10 trong bài (§2.2) | `edgar.item_1a` trả rỗng, bị loại như bài |
| 3 | Item 1A lấy nhầm mục lục (Weyerhaeuser 2016–2018: 2 và 58 "câu") | phân phối độ dài Item 1A: 5.7% hồ sơ có 1–5 câu | bỏ đoạn có ≥ 25% số trang; dự phòng tiêu đề "Risk Factors". Trung vị trong mẫu chấm điểm là 313 câu (v6) so với 226 của bài, vẫn lệch; **MECHANISM: UNKNOWN** (số 237 ghi trước đây đo trên dữ liệu cũ, §11.2 mục 1) |
| 4 | Công ty bị tấn công không có câu an ninh mạng vẫn vào mẫu huấn luyện (vector rỗng, kéo điểm xuống) | đọc lại câu "with available cybersecurity risk disclosures" | `measure.training_disclosures` bỏ vector rỗng; có test |
| 5 | **Luật "vượt tiêu đề" do tôi thêm là SAI** | thí nghiệm Weyerhaeuser FY2015: bật 0.457, tắt 0.033, bài 0.036 | gỡ luật; test ghi lại bằng chứng |
| 6 | `RecursionError` khi duyệt HTML lồng sâu làm sập cả đợt tải | đợt tải dừng ở 3,576 hồ sơ | duyệt bằng stack tường minh; đầu ra trùng từng phần tử với bản cũ trên 4 hồ sơ A.2 |
| 7 | 251 hồ sơ lỗi mạng | lỗi là `NameResolutionError` (DNS của máy), không phải SEC chặn | resume thử lại hồ sơ lỗi; 0 lỗi còn lại |
| 8 | Tỷ lệ từ = 0 khi không có văn bản tạo tương quan giả (0.84 so với 0.03) | Bảng 2 lệch lớn | NaN; có test |
| 9 | **Bảng nối PRC không tất định**: US Airways Group có hai CIK cùng số năm nộp, thứ tự lấy từ `set` đổi theo hash seed | test dựng lại bảng nối pass khi chạy riêng, fail khi chạy chung | override về công ty mẹ 701345; khóa phụ cố định; 10-K nộp chung gắn cho mọi đơn vị cùng nộp. Các con số không đổi vì văn bản giống hệt |
| 10 | Tableau archive của PRC đảo ngày/tháng | kiểm các vụ có ngày công bố đã biết | dùng bản export gốc; archive chỉ để kiểm chéo |
| 11 | **Mẫu ngẫu nhiên bị bớt 102 hồ sơ rút trúng** (1.7% lần rút). Driver tải mỗi hồ sơ một lần, nên bỏ khỏi phần mẫu các hồ sơ đã có trong phần công ty huấn luyện / Bảng 1; danh sách mẫu lại lập từ phần còn lại. Kết quả là mẫu thiếu đúng các hồ sơ rút trúng của công ty bị tấn công | 2026-09-20, khi đối chiếu 450 × 13 = 5,850 dòng rút với 5,748 dòng ghi trong `plan.json`; kiểm lần hai: cả 102 hồ sơ đều thuộc công ty trong bảng nối v1 hoặc Bảng 1 | danh sách mẫu là toàn bộ lần rút (`run_download.py`), 5,823 hồ sơ khác nhau. 88 hồ sơ (68 công ty) vào lại mẫu chấm điểm, điểm trung bình của chúng 0.395. N 3,004 → 3,092; mean 0.250 → 0.254; trung vị 0.315 → 0.323; hệ số Bảng 6 1.362 → 1.320 |

Hai nhận định sai của chính tôi trong vòng này, ghi lại theo RULE 0 mục 7:
* Tôi đã coi câu trích ở Bảng 1 là văn bản thuật toán bắt được (lỗi 5). Thí nghiệm ủng hộ rằng không phải, nhưng chưa chứng minh (§11.2 mục 5).
* Tôi đếm "hơn 100 lỗi" trong file tải bằng `grep error`, nhưng chữ "error" có sẵn trong văn bản 10-K. Đếm theo khóa JSON thì chỉ có 1 lỗi.

## 11. Kiểm tra hallucination nhiều vòng (2026-09-19, tối)

Ba vòng: (1) một agent đối chiếu mọi con số gán cho "bài" với PDF, kể cả đo pixel Hình 1–2; (2) một agent đối chiếu code với định nghĩa của bài và với các khẳng định trong tài liệu này; (3) tôi đo lại mọi con số "bản tái lập" trực tiếp từ dữ liệu đã lưu. Hai vòng đầu độc lập với người viết code; vòng 3 thì không. Mọi phát hiện của agent mà kiểm được nhanh đều đã được tôi kiểm lại trước khi ghi ở đây; mục nào chỉ do agent báo và chưa đo lại thì ghi rõ.

**Điều giữ vững.** Không có con số nào của bài bị bịa: khoảng 114 giá trị trong `PAPER`, 68 câu Phụ lục A.2 (đúng từng chữ, cờ Yes/No và nhãn loại), toàn bộ số ở Bảng 1, 2, 3, 6, §2.2–2.4, §3.3 đều khớp PDF. Số đọc từ Hình 1 lệch tối đa 0.0012 so với đo pixel (tài liệu ghi ±0.005 là thận trọng). Thứ tự ngành Hình 2 đúng và giảm dần thật. Bảng từ khóa khớp từng dòng.

### 11.1 Lỗi code đã xác nhận và đã sửa ngay (commit 8f3710e, lần chạy v4)

| Lỗi | Bằng chứng | Sửa |
|---|---|---|
| Phép kiểm Item 1A "Not applicable/None/Omitted" bị bỏ qua ở nhánh dự phòng "Risk Factors" | đo: 24 hồ sơ chấm điểm có Item 1A < 5 câu, 14 là dạng này | `edgar.is_stub` áp cho mọi nhánh và trong `reextract`; loại 14 hồ sơ (3,018 → 3,004); mean 0.247 → 0.249, trung vị 0.307 → 0.309, điểm 0 năm 2018 9.7% → 9.4% |
| Độ dài Item 1A dạng log: code dùng ln(n) | Bảng 3: 5 phân vị (1, 138, 226, 346, 841) → (0.69, 4.93, 5.42, 5.85, 6.74) chỉ khớp với ln(1+n) | `np.log1p`; test kiểm cả 5 phân vị |
| Con số 92.70% của Bảng 6 | exp(0.656) − 1 = 92.71%: hệ số Model 2 đọc như odds ratio (Model 1 cho 161%) | `validation.table6` trả exp(b) − 1 cho cả hai model |
| Momentum t−12..t−2 và reversal t−1 | Phụ lục B: "11 months ending one day prior to month t" → t−11..t−1; reversal = "previous month" so với tháng lợi nhuận t+1 → r(t) | cả hai sửa, không còn chồng nhau; test tay |

### 11.1b Lỗi code nửa văn bản đã sửa sau audit (2026-09-19 → 20, lần chạy v5–v6)

Ba mục đầu là các mục §11.3 cũ được chọn sửa (nhóm "code nửa văn bản, đổi số"). Mục thứ tư tìm ra trong lúc cập nhật tài liệu.

| Lỗi | Sửa | Ảnh hưởng đo được |
|---|---|---|
| Ngưỡng tần suất ≥ 10 áp trên gốc từ; câu của bài lọc từ trước khi lưu bằng gốc từ | `roots.build_vocabulary` đếm từ, lọc, rồi mới quy gốc; `vectorize` bỏ từ bị lọc; có test | từ vựng 2,064 → 2,092; v5 gộp thay đổi này với hai thay đổi dưới, nên không tách được phần của riêng nó |
| Cyber insurance: "insurance" ở bất kỳ đâu cộng cụm "một phần" ở bất kỳ đâu, kể cả "limited" trơn | cụm "một phần" phải nằm trong câu có "insurance"; bỏ "limited" trơn; có test | trên mẫu chấm điểm v6, luật cũ mã 1 cho 193 công ty-năm, luật mới cho 122 (cả 122 nằm trong 193). Tương quan điểm × bảo hiểm 0.158 → 0.113 (v5), bài 0.169 |
| Quy tắc nối tên áp không nhất quán (Blizzard không nối, Google Docs thì nối); 3 khóa tay bị cắt 45 ký tự nên không bao giờ khớp | quy tắc R* viết lại (mục 5 #33); đọc thêm ứng viên theo token hiếm và theo chữ đầu; 70 quyết định tay mới, ghi tên đầy đủ; `build()` báo lỗi khi một khóa tay không khớp vụ nào | 218 → 288 vụ, 215 công ty; tải thêm 649 10-K của 54 công ty; hệ số Bảng 6 1.540 → 1.362 |
| Mẫu ngẫu nhiên thiếu 102 hồ sơ rút trúng của công ty huấn luyện / Bảng 1 (mục 10 dòng 11) | danh sách mẫu = toàn bộ lần rút | mẫu chấm điểm 3,004 → 3,092; hệ số Bảng 6 1.362 → 1.320 |

### 11.2 Khẳng định sai trong tài liệu này (hallucination của tôi) — đã xác nhận

1. §10 dòng 3: "trung vị 237 câu so với 226" đo trên dữ liệu cũ. Trung vị thật trong mẫu chấm điểm là **314** câu so với 226 của bài, tức vẫn lệch. **MECHANISM: UNKNOWN**.
2. §7: "không niêm yết 61.9% điểm 0 so với 9.7%" bị các Item 1A dạng "Not applicable" làm phình; sau khi sửa là **50.0% so với 9.4%**.
3. §9.3 / §1: "2007–2011 thấp hơn bài" sai với 2009 (0.098 so với 0.092). Bài không cho số năm 2008–2009. Năm 2012 cũng lệch ≥ 8.9 điểm % mà tài liệu không nhắc. Tiêu đề §9.3 dẫn "IA.1" dù bảng đó không có trong tay.
4. §9.3: "2012 và 2014–2018 sát bài" — năm 2017 lệch 0.032, vượt ngưỡng 0.03 của chính tài liệu; khoảng tin cậy 2017 và 2018 không chứa số của bài.
5. §9.4 / §10: "câu trích ở Bảng 1 không phải văn bản thuật toán bắt được" nói quá. Thí nghiệm mới: với từ vựng và mẫu huấn luyện ở đây, mọi tập câu có chứa câu trích cho 0.17–0.18, chỉ riêng tiêu đề cho 0.033 (bài 0.036). Bằng chứng **ủng hộ, chưa chứng minh**, vì mẫu huấn luyện và từ vựng khác bài.
6. §4 C12: "bài áp tiền tố cho cả hai danh sách hit" — A.2 chỉ phân biệt được danh sách relevant (67 so với 68). Với danh sách irrelevant, tiền tố và nguyên từ đều 68/68. Dấu hiệu duy nhất cho tiền tố ở danh sách irrelevant là chữ của bài: bảng ghi "Terror", văn bản ghi "terrorist". Hệ quả của tiền tố: "war" loại cả "warehouse", "warranties", "warning".
7. §4 A8: "từng biến đã kiểm bằng ví dụ tính tay" — không đúng cho reversal (trước khi sửa), cửa sổ beta, IVOL, illiquidity, NCSKEW, EXTR_SIGMA, biên cửa sổ Secrets, CoSkew, cash-flow volatility.
8. §2 / §4 A7: "Phụ lục B: mọi biến" — patent flow/stock chưa cài; "previous attack dummy" chỉ có trong test tổng hợp; AIA (Bloomberg) là đầu vào, code không tính.
9. §5 #6: "sklearn chứa 'system', 'computer'" — có "system", không có "computer".
10. §5 #29: "trang bìa" — code tìm tên sàn trong 40,000 ký tự đầu, vượt quá trang bìa.
11. §5 #27, #28, #30 chỉ đúng với đường raw EDGAR; đường EDGAR-CORPUS không áp is_stub, dùng quy tắc by-reference khác, và lấy năm tài chính = năm nộp − 1.
12. §5 #33: quy tắc nối tên áp không nhất quán — "Google Docs/Android" (2016–2017) được nối sang Alphabet, còn "Blizzard Entertainment" không được nối sang Activision Blizzard dù tên có "Blizzard". Việc đọc tay chỉ phủ 334 trên 698 cặp ứng viên.
13. §4 A2 và comment trong `edgar.py`: "ĐO ĐƯỢC: 10-K405 dừng 2003, 10-KSB dừng 2009" — index dùng ở đây đã lọc theo bộ form của Atlas, không có 10-KSB40, và chỉ có 1 hồ sơ 10-KSB (2002). Con số 139,788 hồ sơ 10-K thì đúng; hai năm dừng không thể đến từ index này.
14. §6: "bài cũng làm tay" cho FactSet và Bloomberg — bài chỉ mô tả làm tay cho Factiva và việc nối tên.
15. §4 mục 10: IA10 "không dự báo được" — bài viết "not a consistent predictor".
16. §9.8: "tỷ lệ ca khoảng 0.4%" là số suy ra (175/41,140, cận trên), chưa ghi cách suy.
17. Số test và độ phủ mâu thuẫn giữa §1, §3 và §4E.
18. Docstring: "weekly log returns" (code gộp lợi suất đơn); `fama_macbeth` "filed before the month" (code: trên hoặc trước cuối tháng).
19. Trang báo cáo: CRSP cũng cần cho Bảng 12 (CAR); ghi chú dòng "điểm 0 năm 2011" chỉ sai chiều.
20. §9 (trước v6): "mẫu ngẫu nhiên 450 hồ sơ mỗi năm nộp 2007–2019 (5,748)". Lần rút có 450 × 13 = 5,850 dòng; 5,748 là số dòng còn lại sau khi driver bỏ 102 dòng trùng phần công ty huấn luyện. Chính chỗ vênh này dẫn tới lỗi ở mục 10 dòng 11 (tìm ra 2026-09-20).
21. Docstring `link_prc.py`: "The rule was fixed before the counts were compared with the paper" không đúng với quy tắc R*, vì R* được viết sau khi đã thấy số v4 (tìm ra 2026-09-20).

**Trạng thái 2026-09-20:** cả 21 mục đã được sửa ở nơi chúng xuất hiện (vòng kiểm tra sau đó tìm thêm 14 mục nữa, ghi ở mục 12): tài liệu này, docstring và comment trong code, và trang báo cáo. Danh sách giữ lại làm hồ sơ; số trong từng mục là số lúc tìm ra (v4), số hiện hành ở mục 9.

Lỗi của chính vòng audit, tự bắt được: tôi báo "73 hồ sơ Item 1A siêu ngắn (2.4%)" vì tra dữ liệu thô bằng dict mà chưa bỏ 503 dòng lỗi; đúng là 24 (0.8%). Thí nghiệm Bảng 6 dùng 147 ca trong khi pipeline dùng 148; chạy lại cùng tập ca: V0 = 1.540 trùng pipeline, bootstrap 1/400 mẫu ≤ 0.961 (không phải 0/400). Phép tính lại Eq. (1) độc lập trên v4 lúc đầu khớp 6/8; hai ca lệch đều có vụ US Airways trong cửa sổ, thêm bản sao 10-K nộp chung thì khớp 8/8.

### 11.3 Việc còn mở

**Lỗi code đã xác nhận ở nửa tài chính, CHƯA sửa.** Nhóm này không được chọn sửa trong vòng 2026-09-19. Chưa lỗi nào ảnh hưởng tới con số nào, vì nửa tài chính chưa chạy trên dữ liệu thật.

| Lỗi | Ảnh hưởng tới |
|---|---|
| Secrets tính trên HTML thô (ngắt dòng, `&nbsp;`, thẻ làm hỏng cụm từ); cửa sổ cho phép 5 từ chen giữa, bài nói "five-word window" (biên hiện tại được ghim bằng test) | biến kiểm soát Bảng 4–6 |
| Tuổi công ty bị cắt vì truy vấn WRDS chỉ lấy từ 2002 | Bảng 3–6 (khi có WRDS) |
| SIC dạng số < 1000 cắt sai 2 chữ số; asset growth và độ trễ Bảng 5 theo dòng, không theo năm tài chính | biến kiểm soát |
| `quantile_groups` đưa NaN vào nhóm 1; khi > 1/k điểm bằng 0, các nhóm sau rỗng và chân thấp của nhân tố giống nhau cho k = 3, 5, 10 | Bảng 10, 11 |
| P1 = điểm ≤ 0; bài: "không có đoạn viết về an ninh mạng" | Bảng 7 |
| Biến thể 4 tuần của Google SVI đổi cả hai cửa sổ; bài (Panel C) chỉ đổi cửa sổ trung vị | Bảng 10 |

**Quan sát chưa giải thích (POST-HOC, MECHANISM: UNKNOWN).**

| Quan sát | Liên quan |
|---|---|
| IVOL: Bảng 7 Panel B in 3.085 / 2.561 / 2.258, giống IVOL ngày tính theo % hơn là IVOL tháng theo Phụ lục B | Bảng 7–9 |
| Item 1A chỉ có một câu, hầu hết là dòng tiêu đề "Risk Factors": 154 hồ sơ trong lần chạy (186 hồ sơ, 2.6%, có dưới 5 câu). Trong mẫu chấm điểm có 12 hồ sơ dưới 5 câu (0.4%) | mẫu chấm điểm, cột "+ex-ante Item 1A" ở 9.1 |
| Trung vị độ dài Item 1A trong mẫu chấm điểm là 313 câu, bài 226 | Bảng 3 dòng Risk section length |

**Độ phủ của việc đọc tay khi nối tên.** Ở lượt đầu, trong 698 cặp ứng viên fuzzy tốt nhất, 334 cặp được đọc. 364 cặp còn lại có điểm giống tên thấp nhất (0.60–0.70). Lượt đọc theo token hiếm (518 vụ) có phủ 110 vụ trong số đó, và với 56 vụ thì CIK ứng viên fuzzy nằm trong danh sách được đọc. Lượt đọc theo chữ đầu (148 vụ) phủ tới đâu thì chưa đo.

### 11.4 Chỗ bài tự mâu thuẫn

* Tr. 360: "the first cyberattack occurred in 2006", nhưng Hình 1 ghi [1] trên năm 2005 (ở đây dùng số của hình).
* Số trong ngoặc ở Hình 2 cộng lại 179; văn bản nói 175 và "125 (71.4%)".
* Phụ lục A.2 gọi các câu phụ của Apple/GM là "outside Item 1A", nhưng trong báo cáo thật các câu đó nằm trong Item 1A (ở đây trích được từ Item 1A).

## 12. Năm vòng kiểm tra hallucination và thiếu sót (2026-09-20)

**Cách làm.** Ba vòng đầu do ba agent chạy độc lập với nhau và với người viết code: (1) đi từ bài sang code để tìm chỗ bài có mà code không có; (2) đối chiếu mọi con số gán cho "bài" trong tài liệu, README, notebook, trang báo cáo và dict `PAPER` với bản PDF; (3) đọc từng hàm của nửa tài chính — phần chưa bao giờ chạy trên dữ liệu thật — so với câu chữ của bài. Vòng 4 và 5 do tôi làm: kiểm chứng cứ đằng sau mỗi khẳng định trong tài liệu (tên file, tên hàm, tham chiếu mục, mỗi chỗ ghi "có test"), rồi đo lại các con số đầu bảng bằng một cài đặt thứ hai. **Mọi phát hiện của agent đều được tôi chạy lại hoặc đọc lại trước khi ghi vào đây; mục nào tôi không kiểm được thì ghi rõ.**

**Điều giữ vững.** Agent vòng 2 kiểm khoảng 280 giá trị và trích dẫn gán cho bài: **không có con số nào bị bịa**, và không có con số nào tìm không ra trong bài. Toàn bộ dict `PAPER` (Bảng 1, 2, 3, 6, chuỗi 175 vụ, từ vựng 3,210 và danh sách 20 từ, thứ tự ngành Hình 2) khớp PDF. Agent vòng 1 thống kê khoảng 140 đặc tả thao tác của bài và thấy khoảng 105 đã cài đúng. Vòng 5 dựng lại Bảng 3 bằng numpy thuần và Bảng 6 bằng logit tự viết cùng ma trận sandwich cluster tự viết: hệ số trùng tới 1.3e-7 và 1e-4.

### 12.1 Khẳng định sai trong tài liệu, đã sửa

| # | Khẳng định | Sự thật (đã kiểm) |
|---|---|---|
| 1 | Notebook: "§3.6 Bảng 6 Model 1" | Bài không có §3.6; Bảng 6 nằm trong §3.5 "Firm outcomes" |
| 2 | Notebook: "Compustat: 10/16 biến của Bảng 3" | Compustat cấp 7/16 dòng; 10/16 là tổng mọi nguồn có giấy phép, mà 13F và BoardEx đã đếm riêng ở dòng khác |
| 3 | §4 A1: "một chỗ bản PDF nhòe" ở dòng từ khóa Business | Trang 393 đọc rõ ở mức 600 dpi và ở bản kết xuất tôi tự xem: bài in "harm disruptive" không có dấu phẩy. Việc tách hai từ là **lựa chọn** (mục 5 #47), không phải đọc scan mờ |
| 4 | §1: "12 bảng, 2 hình" | Bài có 3 hình; Hình 3 là dòng thời gian vụ SolarWinds |
| 5 | README repo công khai: leverage là biến Compustat của Bảng 3–6 | Leverage chỉ có trong Phụ lục B, không xuất hiện ở Bảng 3, 4, 5, 6 hay 9 |
| 6 | §3 vòng 2: "Newey-West, FE hai chiều, logit — mỗi thứ có một test cụ thể" | Newey-West và logit **nay mới có** test đối chiếu cài đặt thứ hai; FE hai chiều vẫn chỉ chạy gián tiếp, và chính chỗ đó có lỗi (12.3 mục 4) |
| 7 | README + notebook: "bản clone sạch: 68 pass, 6 skip" | Đo trên bản clone thật từ GitHub: **10 test bị bỏ qua, không phải 6** (hiện là 70 pass / 10 skip trên 80 test). Số cũ đo trên thư mục đã bị các ô notebook tải thêm file vào — lại đúng lớp lỗi "đọc trạng thái tạm thời như sự thật" |
| 8 | Comment trong `edgar.py`: "30 hồ sơ Not Applicable bị chấm 0" | Đo lại trên dữ liệu trước khi sửa: **14** trong mẫu chấm điểm, **206** trong toàn bộ lần chạy |
| 9 | §2: "12 unit test luật" cho Phụ lục A.1 | Đếm được 7 test luật trong `test_text_modules.py` cộng 4 test Phụ lục A.2 |
| 10 | §4 A8: "beta và IVOL trên cửa sổ 60 tháng tối thiểu 24" | Phụ lục B chỉ nêu mức tối thiểu 24 tháng cho **CoSkew**; áp cho beta và IVOL là lựa chọn của code (mục 5 #42) |
| 11 | §9.1 gọi chuỗi 175 vụ là "mẫu huấn luyện" của bài | Mẫu huấn luyện gốc của bài là **69 vụ "major" = 54 công ty-năm**; 175 là biến thể "mọi vụ" mà bản này dùng. Hai số 69/54 trước nay chỉ nằm trong docstring `training.py` |
| 12 | §4 C13 và `roots.py`: "3,210 gốc từ của bài" | Bài viết "universe of all **words** ... is 3,210"; gọi là gốc từ là suy ra, không phải chữ của bài |
| 13 | §11 và §9: "số đọc Hình 1 lệch tối đa 0.0012 so với đo pixel" | Lần đo pixel thứ hai cho lệch lớn nhất 0.0017 (năm 2015). Cả hai đều nằm trong sai số đọc ±0.005 đã ghi |
| 14 | Docstring `is_stub`: "bài loại các hồ sơ này" | Bài chỉ nói loại công ty **không có mục Item 1A**; mục Item 1A ghi "Not applicable" là suy luận của bản này (mục 5 #30 ghi đúng là lựa chọn) |

### 12.2 Thiếu sót so với bài — nửa văn bản

| Thiếu | Trạng thái |
|---|---|
| `Readability` (kích thước file nộp) chưa bao giờ được tính, vì bộ tải dừng ở cuối văn bản 10-K | **Đã bổ sung 2026-09-20** bằng kho submissions bulk của SEC; hai dòng Bảng 3 nay so được với bài (mục 9.10) |
| Biến "đã từng bị tấn công" (Bảng 6 Model 2, 4, 6) không có hàm dựng, dù chỉ cần dữ liệu PRC đã có | Chưa làm |
| Footnote 12: tương quan của thước đo với 5 hệ số tải nhân tố FF5 | Chưa cài |
| §6.2: hồi quy alpha 12 ngành — bước chọn ra Energy và Durables cho IA7 panel H | Chưa cài; code chỉ thực hiện **hệ quả** (loại hai ngành đó) |
| Patent flow / stock (IA9); cột `excerpt` cho Bảng 1; tham số hóa Jaccard (IA.2–IA.6) và bộ kiểm soát Bảng 9 (IA11–IA12) | Chưa cài |
| Cửa sổ dự phòng 2 năm kích hoạt khi **không tìm được vector**, còn footnote 9 nói khi **không có vụ tấn công nào** | Đã đo: trong mẫu này **0/3,092** công ty-năm khác nhau giữa hai luật |
| Văn bản quá khứ của công ty huấn luyện phải nộp **trong cửa sổ**; bài chỉ nói vụ tấn công nằm trong cửa sổ | Đã đo: N_train trung bình 18.8 → 19.6, trung vị điểm 0.3234 → 0.3220, 111/3,092 công ty-năm đổi quá 0.01 |

### 12.3 Lỗi code đã xác nhận ở nửa tài chính (chưa chạy trên dữ liệu thật, nên chưa ảnh hưởng con số nào)

Tôi tự chạy lại từng mục dưới đây trên dữ liệu tổng hợp.

| # | Lỗi | Bằng chứng tôi chạy lại |
|---|---|---|
| 1 | `factor.table10` thả NaN ở biến phụ thuộc: một ngày thiếu làm **cả bảng thành NaN**, trong khi cột n vẫn ghi đủ số quan sát | 200 ngày, đặt 1 ngày NaN → cả 4 dòng NaN, n = 200; điền NaN đó thì ra số hữu hạn |
| 2 | `portfolios.assign_terciles` đưa điểm NaN vào **nhóm 3** — chân mua của chênh lệch | điểm {0, 0.2, 0.9, NaN} → nhóm {1, 2, 3, **3**} |
| 3 | `portfolios.holding_returns` ghi **0.00%** cho tháng không có lợi suất nào để nắm | thành viên không có trong CRSP → 0.0 cho cả 3 tháng; thành viên có nhưng thiếu tháng đầu → 0.0 tháng đó |
| 4 | `stats.ols_fe` khử hiệu ứng cố định bằng trừ trung bình nhưng không trừ bậc tự do đã hấp thụ → sai số chuẩn cluster nhỏ hơn thực, t bị thổi | panel 200 công ty × 10 năm: hệ số trùng LSDV tới 1e-6, t 25.74 so với 24.36 (+5.7%), tỷ lệ sai số chuẩn 0.9465 **khớp đúng** hệ số bậc tự do kỳ vọng 0.9465. R² trả về là R² nội bộ, không phải R² của bài |
| 5 | `portfolios.table7_panel_b` nhận `crsp_m` nhưng không dùng, nên Panel B mô tả vũ trụ và điểm cắt khác Panel A | đọc code: `portfolio_returns` lọc theo CRSP trước khi chia nhóm, `table7_panel_b` thì không |
| 6 | `variables.link_disclosures` là merge nhiều-nhiều không chặn: một điểm 10-K nhân thành nhiều dòng công ty-năm nếu có hai liên kết CCM cùng hiệu lực | đọc code: không có bước khử trùng hay kiểm tính duy nhất |
| 7 | `solarwinds.table12` chạy logit không `dropna`, khác với panel B | đọc code |
| 8 | Truy vấn 13F lấy theo `cusip` còn `institutional_ownership` cần `permno`; không có bước nối cusip → permno | đọc `wrds_extract.py` và `variables.py`; `crsp_names` được kéo về nhưng không ai dùng |
| 9 | Winsorize 1%/99% theo năm chỉ chạy trong Bảng 3; bài nói winsorize "the continuous variables **in the sample**" | grep toàn gói: chỉ một chỗ gọi `winsorize_by_year` |

**Trạng thái 2026-09-20:** bốn mục đầu (#1–#4) **đã sửa**, mỗi mục có một test ghim đối chiếu với cài đặt thứ hai (`test_weighting_and_car.py`). Năm mục còn lại chưa sửa. Sửa chúng không đổi con số nào hiện có, vì nửa đó chưa chạy trên dữ liệu thật.

### 12.4 Lỗi của chính vòng kiểm tra này

* Tôi báo "bản clone sạch 68 pass, 6 skip" sau khi đo trên thư mục đã bị ô notebook tải thêm file; số đúng là 64 pass, 10 skip (12.1 mục 7).
* Tôi so file CSV công bố với pickle bằng cách gán chỉ mục theo `accession`, trong khi 9 bản sao hồ sơ nộp chung dùng chung accession, và kết luận sai rằng có sai lệch 0.0197. Khóa lại theo (accession, cik, bản sao) thì lệch lớn nhất là 1e-16.
* Test đối chiếu logit tôi viết lần đầu chỉ tính một trong hai hệ số hiệu chỉnh mẫu nhỏ của statsmodels; test fail và tôi sửa công thức, không sửa ngưỡng.

## 13. Code và dữ liệu của chính tác giả (tìm thấy 2026-09-20)

**Nguồn.** Trang dữ liệu của Michael Weber (Chicago Booth) dẫn tới Harvard Dataverse, DOI
`10.7910/DVN/LCVVG5`, "Replication Codes & Data for *Cybersecurity Risk*", giấy phép CC0, 20 file.
Trong bài không có mục công bố code; chỉ tìm ra qua trang cá nhân của tác giả.

**Có gì trong đó**

| File | Nội dung |
|---|---|
| `RFS_Dataverse_Cybersecurity Risk.sas` (441 dòng) | dựng panel: nhập dữ liệu 10-K, tính biến, nối Compustat/CCM, gắn vụ tấn công vào năm tài chính |
| `RFS_Dataverse_Cybersecurity Risk_Stata_code.do` (584 dòng) | Bảng 2–12: hồi quy, danh mục, Fama-MacBeth, sự kiện SolarWinds |
| `flmw_rfs.dta` (3.7 MB) | **44,972 công ty-năm kèm `cyber_risk_score_cosine`** — chính thước đo của bài |
| 17 file còn lại | `Sim_Lag1/2.xlsx`, `10_K.xlsx`, `sample_final.dta`, `monthly_cyber_index.dta`, danh sách vụ tấn công "major", khách hàng SolarWinds, AIA, sở hữu tổ chức, ủy ban rủi ro |

**Cảnh báo quan trọng:** trừ `flmw_rfs.dta`, các file dữ liệu còn lại **rỗng** — chỉ có dòng tiêu đề, mọi ô giá trị trống (kiểm bằng cách đọc thẳng XML của `Sim_Lag1.xlsx`: các ô có định dạng nhưng không có thẻ `<v>`; `sample_final.dta` và `monthly_cyber_index.dta` có 31 và 24 cột, 0 dòng). Vì sao thì **MECHANISM: UNKNOWN**. Hệ quả: chạy lại nguyên xi bộ này là không thể; nhưng thước đo thì có, và code thì đọc được.

**Phần code xử lý văn bản không được công bố.** SAS chỉ `proc import` điểm tương đồng từ `Sim_Lag1.xlsx`. Nghĩa là đúng phần bản này dựng lại — tách Item 1A, luật Phụ lục A, gốc từ, phương trình (1) — vẫn là hộp đen; cái công bố là **đầu ra** của nó.

### 13.1 So trực tiếp thước đo: 0.95

Nối theo tên công ty (chuẩn hóa hai phía, chỉ giữ tên định danh duy nhất một gvkey và một CIK), rồi ghép theo (tên, năm tài chính):

| | |
|---|---|
| Công ty-năm nối được | 1,716 trên 3,092 của mẫu chấm điểm (55%), 1,407 công ty |
| Trung bình: bản này / tác giả | 0.2672 / 0.2675 |
| Trung vị | 0.3487 / 0.3352 |
| Tỷ lệ điểm 0 | 37.6% / 35.6% |
| **Tương quan Pearson** | **0.953** |
| Tương quan hạng Spearman | 0.942 |
| Sai lệch tuyệt đối trung bình / trung vị | 0.033 / 0.013; 80.6% nằm trong 0.05 |
| Chỉ riêng công ty-năm hai bên đều dương (N = 1,056) | r = 0.870, sai lệch trung bình 0.039 |

Theo từng năm, tương quan nằm trong khoảng 0.85–0.97. Trên **cùng** tập công ty-năm, trung bình hai thước đo bằng nhau tới 0.0003, trong khi trên toàn mẫu bản này là 0.254 so với 0.24 của bài. Quan sát: phần chênh ở Bảng 3 đến từ **thành phần mẫu** (mẫu ngẫu nhiên EDGAR có tên sàn so với vũ trụ Compustat), không phải từ cách đo.

Kiểm chứng phụ: phân phối trong `flmw_rfs.dta` tái lập đúng Bảng 3 của bài (mean 0.2376, sd 0.2214, p50 0.2752, p75 0.4452, p99 0.609), và trung bình theo năm trùng số tôi **đọc từ Hình 1** tới 0.001 (ví dụ 2013: 0.269 so với 0.270; 2016: 0.402 so với 0.403) — xác nhận cách đọc biểu đồ ở mục 9.3.

### 13.2 Những chỗ code của tác giả chốt lại giúp

| Điểm | Code của tác giả | Bản này |
|---|---|---|
| `Readability` | `lnread = log(paperTXTFileSize)` — log của kích thước file .txt tính bằng **byte** | Đúng (mục 4 C13 suy ra bằng thí nghiệm, nay có xác nhận) |
| Số câu công bố dạng log | `log(1 + sentencescounter)` | Đúng (ln1p) |
| **`Risk section length`** | `risk_length = numRiskFactorSentencesTotal − sentencescounter`, rồi `log(1 + risk_length)` — **trừ đi số câu an ninh mạng** | **Lệch**: bản này lấy toàn bộ số câu Item 1A, không trừ |
| **`Precise words`** | `precise_w = − sent_uncert2_w`, tức **âm của tỷ lệ từ Uncertainty (LM)** | **Lệch**: bản này dùng danh sách Strong_Modal (mục 5 #9) |
| **Mẫu số của tỷ lệ từ** | `totalWordsadj` — tổng số từ **sau khi loại** stop words và các loại từ khác | **Lệch**: bản này chia cho số token thô của đoạn công bố |
| **`insurance`** | `if find(up_sentencesdescription,'INSURANCE') then insurance = 1` — chỉ cần **nhắc tới** bảo hiểm | **Lệch**: bản này đòi thêm cụm "chỉ bảo hiểm một phần" (theo đúng câu chữ Phụ lục B, nhưng khác code của họ) |
| Bảng 2 | winsorize 1/99 các tỷ lệ từ và số câu **trước khi** tính tương quan; báo cả bản lọc `sim > 0` | **Lệch**: bản này không winsorize |
| **P1 của Bảng 7** | `replace cyberrisk_port_q = 0 if sorting_var == 0`, phần còn lại chia 2 nhóm bằng `xtile` | **Trùng** — mục 11.3 từng ghi đây là chỗ nghi lệch; nay đóng lại |
| Winsorize | `winsor2 $controls, cuts(1 99) by(fyear)` và **dùng biến `_w`** trong Bảng 3, 4, 5, 6 | **Lệch**: bản này chỉ winsorize trong Bảng 3 (mục 12.3 #9 được xác nhận) |
| Bảng 4 Model 2 | `areg ..., absorb(gvkey)` — Stata trừ bậc tự do của hiệu ứng cố định bị hấp thụ | **Lệch**: `ols_fe` không trừ (mục 12.3 #4 được xác nhận) |
| Bảng 5 | `reg ncskew_w L1.sim_breaches_t_1_all $controls3 i.fyear` — chỉ trễ điểm, hiệu ứng cố định **chỉ theo năm** | Bản này trễ đúng điểm (khớp) nhưng thêm cả hiệu ứng cố định ngành |
| Bảng 6 | `logit atleast1attack_1 ... ind_ff12_dum* i.fyear, vce(cluster gvkey)`; biến phụ thuộc là vụ tấn công ở **năm tài chính kế tiếp** (lead 1) | Khớp; biến thể V0 của bản này là cách đọc gần nhất |
| Bảng 9 | `asreg ..., fmb newey(4)` — Newey-West **4 lag** | **Lệch**: bản này dùng 12 lag cho cả Fama-MacBeth |
| Bảng 7–8 | `newey ..., lag(12)` | Khớp |

**Quyết định 2026-09-20:** theo **code của tác giả**, đồng thời giữ và báo song song cách đọc theo câu chữ bài. Đã áp dụng ở lần chạy v7 cho bốn biến: `risk_section_length` trừ số câu an ninh mạng, `precise_words` = âm tỷ lệ Uncertainty, mẫu số tỷ lệ từ là số từ sau khi loại, `cyber_insurance` chỉ cần nhắc tới bảo hiểm. Cách đọc cũ giữ trong các cột `negative_words_raw`, `precise_words_strong_modal`, `litigious_words_raw`, `cyber_insurance_partial`.

Kết quả đo được sau khi đổi (mục 9.5): ô bảo hiểm gần bài hơn (0.117 → 0.149 so với 0.169), nhưng **toàn bộ ma trận 21 ô lại xa hơn** (0.059 → 0.073), vì dòng `precise_w = - sent_uncert2_w` của họ không tái lập được chính ô *precise × negative* mà bài in. Thước đo rủi ro, Bảng 3 và Bảng 6 không đổi.

Bốn lỗi nửa tài chính ở mục 12.3 (#1–#4) cũng đã sửa trong cùng đợt; sáu mục còn lại ở 13.2 (winsorize, Fama-MacBeth 4 lag, Panel B, hiệu ứng cố định Bảng 5, merge CCM, 13F cusip) chưa sửa.
