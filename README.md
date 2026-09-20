# Tái lập "Cybersecurity Risk" (Florackis, Louca, Michaely & Weber, RFS 2023)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/khoaminh2957/cyberrisk-replication/blob/main/cyberrisk_replication.ipynb)

Bài gốc: Florackis, C., Louca, C., Michaely, R. & Weber, M. (2023). *Cybersecurity Risk.*
The Review of Financial Studies 36(1), 351–407. Bài đo rủi ro an ninh mạng của từng công ty
niêm yết ở Mỹ bằng cách so đoạn "Item 1A Risk Factors" trong 10-K với đoạn của các công ty
vừa bị tấn công, rồi kiểm xem điểm đó có được thị trường định giá không.

Repo này dựng lại **toàn bộ phương pháp** của bài (một module cho một bước) và **đã ra số cho
nửa văn bản** bằng dữ liệu công khai. Nửa tài chính cần CRSP/Compustat qua WRDS, hiện không có.

Mở notebook bằng nút Colab ở trên để xem tóm tắt và chạy lại từng bước.

## Đã làm được

| Phần của bài | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ lục A: thuật toán trích câu an ninh mạng | Xong | Trùng **68/68** quyết định bắt/bỏ câu trên 4 báo cáo 10-K thật mà bài in ở Phụ lục A.2 |
| §2.3 mẫu huấn luyện từ dữ liệu PRC | Xong | 288 vụ tấn công nối với 215 công ty nộp 10-K, theo một quy tắc cố định ghi trong `link_prc.py` |
| §2.4 phương trình (1)–(2), từ vựng, gốc từ | Xong | Tính lại độc lập bằng numpy trên 8 công ty-năm: trùng tới 1e-9 |
| Phụ lục B: Readability (kích thước file nộp) | Xong 20/9 | Lấy từ kho submissions bulk của SEC; hai dòng Bảng 3 so được với bài |
| Bảng 1, Bảng 2, Bảng 3 (phần văn bản), Hình 1, Hình 2 | Xong | Xem bảng số bên dưới |
| Bảng 6 Model 1 | Xong, thiết kế khác | Case-control, vì không liệt kê được 41,140 công ty-năm của bài |
| Bảng 4–5, 7–12, IA7–IA14 | Code xong, **chưa ra số** | Thiếu WRDS |

Bộ test: 76 test. Trong bản clone sạch: **66 pass, 10 skip** — 10 test cần dữ liệu không kèm repo (4 hồ sơ 10-K của Phụ lục A.2, bản PRC đầy đủ, index EDGAR, từ điển Loughran–McDonald, cache EDGAR, test mạng). Sau khi notebook tải hai thứ đầu: **71 pass, 5 skip**. Trên máy có đủ dữ liệu: 75 pass và 1 test mạng.

Lần chạy hiện tại (v6): 8,390 báo cáo 10-K tải từ SEC EDGAR, 3,092 công ty-năm được chấm điểm.

| Con số của bài | Bài | Bản này |
|---|---|---|
| Bảng 3: mean / trung vị / P75 / P99 | 0.24 / 0.28 / 0.45 / 0.61 | 0.254 / 0.323 / 0.468 / 0.613 |
| Tỷ lệ điểm 0 năm 2018 | 10.59% | 9.2% |
| Bảng 1: Weyerhaeuser FY2015 (điểm thấp nhất bài) | 0.036 | 0.039 |
| Bảng 1: 10 công ty-năm, sai lệch tuyệt đối trung bình | – | 0.037 |
| Bảng 2: ma trận 21 ô, sai lệch trung bình | – | 0.057 |
| Hình 1: 12 năm, sai lệch tuyệt đối trung bình | – | 0.023 |
| Hình 2: tương quan hạng 12 ngành (Spearman) | – | 0.92 |
| Top-20 từ phổ biến trùng bài | 20 | 18 |
| Bảng 6 Model 1: hệ số (t) | 0.961 (7.10) | 1.320 (7.95) |
| Bảng 3: Readability, trung vị (byte) | 6,163,418 | 9,280,731 |

## Kiểm chứng mạnh nhất: so với thước đo của chính tác giả

Tác giả công bố thước đo của họ trên Harvard Dataverse (DOI `10.7910/DVN/LCVVG5`, CC0, file
`flmw_rfs.dta`: 44,972 công ty-năm). Nối theo tên công ty với mẫu chấm điểm ở đây:

| | |
|---|---|
| Công ty-năm nối được | 1,716 (1,407 công ty) |
| Trung bình: bản này / tác giả | 0.2672 / 0.2675 |
| **Tương quan Pearson** | **0.953** (Spearman 0.942) |
| Sai lệch tuyệt đối trung bình | 0.033; 80.6% nằm trong 0.05 |

```bash
python3 -m cyberrisk.compare_authors cyberrisk/data/results/scores_v6.csv   # tự tải file của tác giả
```

Bộ của tác giả có code SAS và Stata cho phần tài chính, nhưng **không có code xử lý văn bản** (SAS
chỉ nhập điểm tương đồng từ một file Excel), và 19 trong 20 file dữ liệu đã bị xóa hết giá trị, chỉ
còn tiêu đề. Chi tiết và danh sách những định nghĩa mà code của họ chốt lại giúp: `cyberrisk/EVALUATION.md` mục 13.

## Chưa làm được, và vì sao

Tất cả đều vì thiếu dữ liệu có giấy phép, không phải vì thiếu code.

| Cần | Dùng cho |
|---|---|
| CRSP (giá, lợi suất, gồm công ty đã hủy niêm yết) | Bảng 5, 7–12 và toàn bộ Internet Appendix |
| Compustat | 7/16 biến của Bảng 3 và các biến kiểm soát Bảng 4–6: quy mô, tuổi công ty, Tobin's q, ROA, tangibility, R&D, biến động dòng tiền ngành |
| Thomson-Reuters 13F | sở hữu tổ chức (một biến kiểm soát) |
| BoardEx | tỷ lệ thành viên độc lập, ủy ban rủi ro |
| CRSP–Compustat link + WRDS SEC Analytics | cầu nối CIK + năm tài chính → gvkey → permno |
| Factiva | cờ "vụ lớn" của mẫu huấn luyện (đang dùng biến thể "mọi vụ") |
| FactSet Revere, Bloomberg | Bảng 12 (khách hàng SolarWinds, chỉ số chú ý) |

Hệ quả trực tiếp: **kết quả chính của bài — danh mục điểm cao sinh lời hơn tới 8.3%/năm —
chưa kiểm được dòng nào.** Chi tiết từng biến và từng bảng: [`cyberrisk/EVALUATION.md`](cyberrisk/EVALUATION.md).

## Trung thực về chất lượng

`EVALUATION.md` ghi lại cả những chỗ tự làm sai: mục 10 liệt kê 11 lỗi đã tìm ra và sửa, mục 11
và mục 12 là hai đợt kiểm tra hallucination bằng agent độc lập (đối chiếu số của bài với PDF, đối
chiếu code với định nghĩa của bài, rà chứng cứ sau mỗi khẳng định, đo lại bằng cài đặt thứ hai) —
tổng cộng 35 khẳng định sai trong chính tài liệu đã được tìm ra và sửa. Mục 12.3 liệt kê 9 lỗi code
của nửa tài chính còn mở, mỗi lỗi kèm cách tôi chạy lại để xác nhận. Mọi chỗ lệch với bài đều ghi **MECHANISM: UNKNOWN** kèm danh sách ứng
viên, không chọn ứng viên nào khi chưa có thí nghiệm phân biệt.

## Cấu trúc

```
cyberrisk/
  edgar.py extract.py keywords.py      §2.2 tải 10-K, tách Item 1A; Phụ lục A luật từ khóa
  training.py link_prc.py              §2.3 mẫu huấn luyện PRC + bảng nối tên → CIK
  roots.py measure.py                  §2.4 gốc từ, từ vựng, phương trình (1)–(2)
  language.py                          §3.2 biến ngôn ngữ Bảng 2
  variables.py                         Phụ lục B: mọi biến kiểm soát
  validation.py portfolios.py          Bảng 1–6; Bảng 7–8
  fama_macbeth.py factor.py            Bảng 9; Bảng 10 + Google Trends
  solarwinds.py robustness.py          Bảng 11–12; IA7–IA14
  pipeline.py replicate_text.py        điều phối lần chạy; so số với bài
  wrds_extract.py                      truy vấn WRDS (viết sẵn, chưa chạy)
  tests/                               76 test (bản clone sạch: 66 pass, 10 skip vì thiếu dữ liệu lớn)
  data/results/                        kết quả lần chạy v6 (điểm từng công ty-năm + các bảng)
cyberrisk_replication.ipynb            notebook tóm tắt + chạy lại (Colab)
```

## Chạy

```bash
pip install -r requirements.txt
python -m pytest cyberrisk/tests -q                    # bản clone sạch: 66 pass, 10 skip (thiếu dữ liệu lớn)

export EDGAR_USER_AGENT="Ten Ban email@truong.edu"     # SEC yêu cầu contact trong User-Agent
python -m cyberrisk.fetch_data appendix-a2             # 4 hồ sơ 10-K của Phụ lục A.2
python -m pytest cyberrisk/tests/test_appendix_a2.py -q
```

Dựng lại toàn bộ số của mục 9 cần tải 8,390 hồ sơ 10-K (khoảng 45–60 phút, 460 MB) — xem
`cyberrisk/README.md`. Kết quả của lần chạy đó đã kèm sẵn trong `cyberrisk/data/results/`,
nên notebook dựng lại mọi bảng trong vài giây mà không cần tải lại.

## Dữ liệu công khai đã dùng

SEC EDGAR (10-K), Privacy Rights Clearinghouse (lịch sử vụ lộ dữ liệu, qua bản mirror công khai),
thư viện dữ liệu Kenneth French (nhân tố và phân ngành), từ điển Loughran–McDonald, WordNet.
Dữ liệu trong `cyberrisk/data/results/` là số liệu dẫn xuất từ các nguồn công khai đó.
