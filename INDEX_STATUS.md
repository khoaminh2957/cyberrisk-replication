# Cybersecurity risk index — làm tới đâu rồi

Cập nhật 21/9/2026. File này chỉ nói về **phần chỉ số rủi ro an ninh mạng** (§2 của bài), không nói
phần định giá (§3–§5).

**Kết luận một dòng:** phương pháp dựng xong và kiểm chứng được ở ba tầng độc lập; chỉ số đã tính
cho mẫu 3,092 công ty-năm, nhưng **chưa tính cho đúng vũ trụ công ty của bài** vì việc đó cần Compustat.

---

## 1. Đường đi của chỉ số, từng bước

| Bước của bài | Code | Trạng thái |
|---|---|---|
| §2.2 Tải 10-K từ EDGAR, tách mục Item 1A, bỏ hồ sơ dẫn chiếu | `cyberrisk/edgar.py`, `pipeline.py` | Xong — 8,390 hồ sơ, không còn lỗi |
| Phụ lục A Bảng từ khóa trực tiếp / gián tiếp, cửa sổ 10 câu, dừng ở tiêu đề in đậm | `keywords.py`, `extract.py` | Xong — khớp 68/68 với đáp án bài in |
| §2.3 Mẫu huấn luyện từ dữ liệu PRC, nối tên sang công ty nộp 10-K | `training.py`, `link_prc.py` | Xong — 288 vụ, 215 công ty (bài: 175 vụ) |
| §2.4 Loại từ, quy gốc từ, ngưỡng tần suất ≥ 10, vector đếm | `roots.py` | Xong — từ vựng 2,092 gốc từ (bài: 3,210) |
| §2.4 Phương trình (1) cosine và (2) Jaccard, cửa sổ 1 năm, dự phòng 2 năm | `measure.py` | Xong — tính lại độc lập trùng tới 1e-9 |
| §3.2 Biến ngôn ngữ của Bảng 2 | `language.py` | Xong — theo code tác giả, giữ cả cách đọc theo câu chữ bài |
| Phụ lục B Độ dài mục rủi ro, dung lượng hồ sơ, biến bí mật thương mại | `variables.py`, `pipeline.py` | Xong |
| §2.2 Nối sang Compustat bằng CIK + năm tài chính | `variables.link_disclosures` | **Chưa chạy được** — cần WRDS |

---

## 2. Độ chính xác: bốn phép kiểm độc lập

| Kiểm ở tầng nào | Kết quả | Chạy lại bằng |
|---|---|---|
| Luật trích câu, so với đáp án bài in ở Phụ lục A.2 | **68/68** quyết định bắt/bỏ câu, trên 10-K thật của Apple, Abbott, GM, Verizon | `python3 -m cyberrisk.fetch_data appendix-a2` rồi `pytest cyberrisk/tests/test_appendix_a2.py` |
| Điểm từng công ty-năm, so với thước đo **do chính tác giả công bố** | **r = 0.953**, Spearman 0.942, trên 1,716 công ty-năm | `python3 -m cyberrisk.compare_authors cyberrisk/data/results/scores_v7.csv` |
| Bảng 1 của bài — 10 công ty-năm được in điểm sẵn | sai lệch tuyệt đối trung bình **0.037** | notebook, mục 5 |
| Hình 1 — điểm trung bình 12 năm | sai lệch trung bình **0.023** | notebook, mục 5 |

Phép tính Eq. (1) còn được dựng lại lần hai bằng numpy thuần, không dùng `measure.py`: trùng tới
**1e-9** trên 8 công ty-năm rút ngẫu nhiên.

### "r = 0.953" nghĩa là gì khi nhìn từng dòng

* trung bình: **0.2672** (bản này) so với **0.2675** (tác giả)
* sai lệch trung vị **0.013**; **80.6%** số công ty-năm lệch dưới 0.05
* riêng các dòng cả hai bên đều dương (N = 1,056): r = **0.870**, sai lệch trung bình 0.039
* 34.7% số dòng cả hai cùng bằng 0; 2.9% bản này chấm 0 còn tác giả chấm dương; 0.9% ngược lại

Nguồn thước đo của tác giả: Harvard Dataverse, DOI `10.7910/DVN/LCVVG5`, file `flmw_rfs.dta`
(44,972 công ty-năm, giấy phép CC0). Trong bộ đó **không có code xử lý văn bản** — chỉ có code SAS
và Stata cho phần tài chính — và 19 trong 20 file dữ liệu đã bị xóa hết giá trị.

---

## 3. Con số hiện tại của chỉ số

Lần chạy v7, mẫu chấm điểm 3,092 công ty-năm, 2007–2018.

| Bảng 3 của bài | Bài | Bản này |
|---|---|---|
| trung bình | 0.24 | 0.254 |
| độ lệch chuẩn | 0.22 | 0.231 |
| phân vị 25 | 0.00 | 0.000 |
| trung vị | 0.28 | 0.323 |
| phân vị 75 | 0.45 | 0.468 |
| phân vị 99 | 0.61 | 0.613 |

Theo thời gian: tỷ lệ công ty-năm có điểm 0 giảm từ 79.2% (2007) xuống **9.2%** (2018); bài ghi
10.59% cho 2018. Theo ngành: tương quan hạng với thứ tự 12 ngành của bài là **0.92**; năng lượng và
chế tạo đứng cuối ở cả hai. Top-20 từ phổ biến trùng bài **18/20**.

---

## 4. Ba chỗ chưa gọi là xong

1. **Vũ trụ công ty.** Bài chấm điểm cho các công ty-năm trong Compustat (Bảng 6 dùng 41,140 quan
   sát). Bản này chấm 3,092 công ty-năm rút ngẫu nhiên từ EDGAR, lọc niêm yết bằng **tên sàn in
   trong chính 10-K**. Đo được ảnh hưởng: tỷ lệ điểm 0 năm 2018 là 9.2% ở nhóm "niêm yết" và 50.0%
   ở nhóm còn lại — tức bộ lọc này quyết định phân phối điểm. Đây là nguyên nhân hàng đầu của chênh
   lệch trung vị 0.323 so với 0.28.
2. **Từ vựng.** Ngưỡng "xuất hiện ít nhất 10 lần" chạy trên 8,390 hồ sơ thay vì toàn bộ corpus của
   bài, nên ra 2,092 gốc từ so với 3,210. Muốn bằng phải tải khoảng 45 nghìn hồ sơ (~7 giờ).
3. **Mẫu huấn luyện.** Không có cờ "vụ lớn" của Factiva nên dùng **mọi vụ** — đúng biến thể mà bài
   nói cho kết quả "unchanged". Bảng nối tên cũng là quy tắc tự viết (288 vụ / 215 công ty), không
   phải bảng tay của tác giả (175 vụ).

Thêm một giới hạn của chính con số 0.953: nó đo trên **55%** mẫu, phần nối được theo tên công ty.
Có Compustat thì nối bằng gvkey — đúng khóa tác giả dùng — và kiểm được gần như toàn bộ.

---

## 5. Cần gì để chốt phần này

| Cần | Dùng để làm gì với chỉ số |
|---|---|
| **Compustat** (funda + company) | liệt kê đúng tập công ty-năm mà bài chấm điểm, thay cho proxy "tên sàn" |
| **CRSP–Compustat link** và **WRDS SEC Analytics** | nối CIK của 10-K sang gvkey / permno, để kiểm lại r = 0.953 trên toàn mẫu |
| Tải thêm 10-K (miễn phí, ~7 giờ) | dựng từ vựng trên corpus đầy đủ, tiến gần 3,210 gốc từ |

CRSP chỉ cần cho phần định giá (§4–§5), **không cần cho chỉ số**.

---

## 6. Nhật ký các lần chạy

| Lần | Thay đổi | Ảnh hưởng tới chỉ số |
|---|---|---|
| v3 | lần chạy đầu, 7,741 hồ sơ | – |
| v4 | loại mục Item 1A dạng "Not applicable" ở mọi nhánh | mẫu 3,018 → 3,004 |
| v5 | quy tắc nối tên R*, ngưỡng tần suất áp trên từ trước khi quy gốc, luật bảo hiểm cùng câu | 218 → 288 vụ; từ vựng 2,064 → 2,092 |
| v6 | sửa lỗi chọn mẫu: 102 hồ sơ rút trúng của công ty huấn luyện bị bỏ sót | mẫu 3,004 → 3,092 |
| v7 | bốn định nghĩa biến ngôn ngữ lấy theo code tác giả | chỉ số **không đổi**; chỉ Bảng 2 và độ dài mục rủi ro đổi |

Chi tiết từng con số và từng lỗi: `cyberrisk/EVALUATION.md` mục 9 (số liệu), mục 10 (11 lỗi đã tìm
và sửa), mục 12 (năm vòng kiểm tra), mục 13 (code và dữ liệu của tác giả).
