# Giá trị cấu trúc bộ câu hỏi — EFA/CFA qua R (G6)

Bác sĩ giao ngày 21/11/2026: «kiểm và hoàn thiện các khoảng trống hệ nghiên cứu». Đề cương nộp Hội đồng của C1a (mục
4.5.3 ý 4) và SAP §3 cam kết kiểm cấu trúc năm lĩnh vực A–E (29 câu) bằng phân tích nhân tố khám phá (EFA) trên nửa
mẫu thứ nhất và phân tích nhân tố khẳng định (CFA) trên nửa mẫu độc lập còn lại. Trước ngày này repo chỉ có
`tools/kiem_tin_cay_thang_do.py` (Cronbach α, ICC); `G6_DAC_TA_SAP.json` của C1a ghi mục này là «chua_tu_dong».

Công cụ: `tools/phan_tich_nhan_to_r.py` (Python của hệ, `~/.ebm-venv`; R chạy bằng `Rscript --vanilla`, dùng lại phần
tìm/chạy R của `tools/cau_noi_r.py`).

## Làm đúng SAP đã khoá

Công cụ đọc phương pháp từ chính SAP, không tự quyết:

- Mệnh đề «giá trị cấu trúc» của SAP phải còn đủ: chia ngẫu nhiên hai nửa, phân tầng, nhân tố khám phá, polychoric,
  phân tích song song, xoay xiên, nhân tố khẳng định, WLSMV. Thiếu một ⇒ **từ chối** (mã 3): SAP đã sửa đổi thì cập nhật
  công cụ theo SAP mới, không chạy phương pháp cũ.
- Số câu («29 câu»), dải lĩnh vực («A–E») và số nhân tố («năm nhân tố») đọc từ mệnh đề đó. Câu của từng lĩnh vực lấy từ
  tiêu đề phần của từ điển G5 («… · A. Khả năng tiếp cận dịch vụ»). Đếm lệch SAP ⇒ từ chối.
- Hạt giống: `set.seed(N)` của SAP §10 (C1a: 20260830). `--seed` khác SAP chạy được nhưng báo cáo ghi «KHÁC SAP».
- Thang hợp lệ của từng câu: dãy mã liền nhau từ mã nhỏ nhất (1–5); mã sau khoảng trống (8, 9) và mọi giá trị ngoài thang
  (7, KDD, BTR, ô trống) là thiếu — báo cáo đếm theo từng mã.
- Quần thể: `--loc` bằng ngôn ngữ công thức, qua ĐÚNG hàm của `run_stats_analysis` (C1a: `PhieuHopLe == 1`, biến phái sinh
  tính từ `_bien-phai-sinh.csv` đã duyệt).
- Không tính chỉ số hiệu chỉnh (modification indices): SAP cấm sửa mô hình theo chỉ số hiệu chỉnh rồi báo như mô hình định
  trước.

## Ngưỡng chỉ số phù hợp

Chỉ phân loại khi SAP còn ghi đúng các ngưỡng định trước: phù hợp tốt khi CFI ≥ 0,95, TLI ≥ 0,95, RMSEA ≤ 0,06 và
SRMR ≤ 0,08; chấp nhận được khi CFI và TLI ≥ 0,90 và RMSEA ≤ 0,08. Không đủ ⇒ chỉ in số. Không tô ngưỡng hệ số tải
vì SAP không định ngưỡng tải.

Nguồn (đề cương [46]–[48]; DOI đối chiếu metadata Crossref ngày 21/11/2026; ba bài ở tạp chí phương pháp luận nên không
có PMID):

- Hu L, Bentler PM. Struct Equ Modeling. 1999;6(1):1-55. doi:10.1080/10705519909540118
- Bentler PM, Bonett DG. Psychol Bull. 1980;88(3):588-606. doi:10.1037/0033-2909.88.3.588
- Browne MW, Cudeck R. Sociol Methods Res. 1992;21(2):230-258. doi:10.1177/0049124192021002005

Ghi chú in kèm cho thống kê viên (không đổi ngưỡng): ngưỡng quy ước xây dựng cho ML với dữ liệu liên tục; với dữ liệu
thứ bậc ước lượng DWLS/ULS, áp ngưỡng này có xu hướng không phát hiện mô hình sai — Xia Y, Yang Y. Behav Res Methods.
2019;51(1):409-428. PMID 29869222, doi:10.3758/s13428-018-1055-2 (kiểm rút bài 21/11/2026 bằng
`check_citation_retraction.py`: không rút).

## Lựa chọn kỹ thuật SAP không nêu — [CẦN THỐNG KÊ VIÊN XÁC NHẬN]

Báo cáo in đủ danh sách này ở mỗi lượt chạy:

- Phương pháp trích: minres (mặc định psych) cho phân tích song song và EFA.
- Phân tích song song so trị riêng NHÂN TỐ trên ma trận polychoric với trung bình 20 bộ **tái chọn mẫu từng cột** (giữ
  phân bố từng câu; `sim = FALSE`). Không dùng mặc định `sim = TRUE` của psych: khi đó psych so với dữ liệu chuẩn liên
  tục (tương quan Pearson). Diễn tập 21/11/2026 trên dữ liệu nhiễu thuần (29 câu độc lập, n 497): mặc định gợi ý 5 nhân
  tố, `sim = FALSE` gợi ý 0. Trên dữ liệu giả lập 5 nhân tố, cả hai gợi ý 4 (lĩnh vực E chỉ có 2 câu). `sim = FALSE`
  chỉ bỏ độ lệch HỆ THỐNG: một bộ nhiễu khác (nửa mẫu 298 phiếu) vẫn ra 3 nhân tố giả theo cả tiêu chí trung bình lẫn
  phân vị 95% ⇒ đọc số nhân tố cùng hệ số tải và CFA trên nửa độc lập.
- Số nhân tố theo PHÂN VỊ 95% của cùng các vòng tái chọn mẫu được báo kèm để tham khảo; EFA dùng tiêu chí trung bình (mặc
  định psych).
- Chạy TUẦN TỰ (`options(mc.cores = 1L)`): psych mặc định chạy song song 2 tiến trình qua `mclapply`; với RNG
  Mersenne-Twister, tiến trình con lấy hạt giống ngẫu nhiên nên cùng `set.seed` vẫn ra kết quả khác (đo 21/11/2026: cùng
  bộ nhiễu ra 0 rồi 3 nhân tố). Tuần tự thì trùng khớp từng chữ số giữa các lần chạy và giống nhau trên Mac lẫn Windows
  (thời gian ~30–40 giây cho nửa mẫu ~500 phiếu).
- Phép xoay xiên: oblimin.
- Ô thiếu: mặc định listwise (SAP §6 lấy complete-case làm phân tích chính). Listwise bỏ ≥ 5% một nửa mẫu ⇒ cảnh báo theo
  đúng luật «< 5%» của SAP §6; `--thieu pairwise` cho thống kê viên chọn.
- Chia nửa: trong mỗi tầng (khung giờ × bàn khám, duyệt theo mã ký tự — giống nhau trên Mac và Windows) xáo trộn ngẫu
  nhiên, nửa 1 nhận ⌊k/2⌋ ca, tầng lẻ rút ngẫu nhiên ca dư. Python kiểm độc lập: mọi dòng thuộc đúng một nửa, mỗi tầng hai
  nửa lệch ≤ 1 ca.
- CFA: mỗi câu tải lên đúng lĩnh vực của nó, nhân tố tương quan tự do, cố định tải câu đầu (mặc định lavaan); báo ba phiên
  bản chỉ số (thường · scaled · robust), phân loại riêng từng phiên bản.

## Lệnh

Chạy trong `medical-ebm-automation/`:

| Lệnh | Việc |
|---|---|
| `python3 tools/phan_tich_nhan_to_r.py kiem` | Rscript + gói `jsonlite`, `psych`, `lavaan`, `GPArotation` |
| `… cai-goi [--ap-dung]` | Cài gói thiếu từ CRAN (mặc định chạy khô) |
| `… gia-lap --ra <tệp ngoài repo> [--kich-ban nam_nhan_to\|khong_cau_truc] [--n 1000]` | Dữ liệu GIẢ LẬP khuôn C1a |
| `… cu-phap --study <mã> --tang khunggio_kham,ma_ban_kham --loc "PhieuHopLe == 1"` | Tập phân tích + script R |
| `… chay --study <mã> --tang … --loc …` | `cu-phap` rồi chạy R ⇒ `<gate>_analysis_summary.json` + `<gate>_ket_qua.md` |

Mặc định dùng bộ dữ liệu ĐÃ KHOÁ G5 (`cau_noi_spss.tim_du_lieu_khoa`, kiểm SHA-256) và đòi G4 khoá theo trạng thái sống
(`run_stats_analysis._g4_khoa_song`); đầu ra vào `exports/<mã>/` (ngoài git), gate mặc định `G6_MO_nhan_to`.

Diễn tập/bản nháp: `--data <csv> --ban-nhap --thu-muc-ra <thư mục NGOÀI repo>`. Đầu ra gắn nhãn BẢN NHÁP, không có khoá
`data_lock` (G7 không dựng Kết quả từ đó), không ghi gì vào `exports/`.

Mã thoát: 0 xong · 1 R lỗi, khối lỗi, CFA không hội tụ hoặc kiểm chia nửa hỏng · 2 không đo được (không có R/gói, thiếu
SAP/từ điển, dữ liệu chưa khoá) · 3 từ chối (SAP không còn khớp phương pháp, G4 chưa khoá, PII, tham số sai).

## Nối vào `chay_sap_g6.py`

`G6_DAC_TA_SAP.json` nhận thêm khoá `phan_tich_nhan_to` (giá trị duy nhất `efa_cfa`), `tang` (danh sách cột) và tuỳ chọn
`thieu`; `loc` như cũ. Mục có khoá này chạy `phan_tich_nhan_to_r.py chay` (tự đọc bộ khoá bằng cùng hàm của cổng, không
có kiểm chéo SPSS), chỉ mục ghi số nhân tố gợi ý, CFI/TLI/RMSEA scaled, SRMR và phân loại.

Đề xuất cho C1a (CHƯA áp — sửa đặc tả là việc của thống kê viên, sửa xong phải duyệt lại): tách mục `MO_do_luong` thành
`MO_do_luong` (giữ `chua_tu_dong` cho phân bố điểm, Cronbach α, omega G1–G3, sàn–trần) và

```json
{"id": "MO_nhan_to", "vai": "mo_ta", "sap_muc": "§3", "sap_neo": ["giá trị cấu trúc"],
 "mo_ta": "Giá trị cấu trúc (đề cương 4.5.3 ý 4): EFA nửa 1 (polychoric, phân tích song song, xoay xiên) + CFA nửa 2 (WLSMV)",
 "tham_so": {"phan_tich_nhan_to": "efa_cfa", "tang": ["khunggio_kham", "ma_ban_kham"], "loc": "PhieuHopLe == 1"}}
```

## Đo thật (21/11/2026, R 4.6.2 Mac — psych 2.6.9, lavaan 0.7.3, GPArotation 2026.8.2)

Dữ liệu GIẢ LẬP khuôn C1a 1.000 phiếu (mã 8/9/KDD ≈ 1,7% ô; ~2% phiếu bỏ trống ≥ 7 câu), đọc SAP + từ điển + biến phái
sinh THẬT của C1a (chỉ đọc), quần thể `PhieuHopLe == 1` còn 985 phiếu, chia 497/488 qua 194 tầng, lệch tối đa 1 ca/tầng.

| Kịch bản | Ô thiếu | Phân tích song song | CFA (scaled) | Phân loại |
|---|---|---|---|---|
| 5 nhân tố | listwise (EFA 303/497, CFA 324/488 — cảnh báo SAP §6) | 4 | hội tụ, CFI 1,000, RMSEA 0,000, SRMR 0,042 | phù hợp tốt |
| 5 nhân tố | pairwise | 4 | hội tụ, CFI 1,000, RMSEA 0,000, SRMR 0,034 | phù hợp tốt |
| câu độc lập | pairwise | 0 | nghiệm không chấp nhận được (ma trận nhân tố không xác định dương) | không phân loại |

Bài học từ diễn tập:

- Với 29 câu, mỗi câu thiếu ~1,7% đã làm listwise bỏ hơn 30% mỗi nửa — thống kê viên cần quyết cách xử lý ô thiếu trước
  khi chạy trên dữ liệu thật.
- Lĩnh vực E chỉ 2 câu nên EFA khó tách thành nhân tố riêng (tải e1/e2 thấp).
- Trên dữ liệu NHIỄU THUẦN, CFA vẫn ra CFI scaled 1,000, TLI −20,1, RMSEA 0,000, SRMR 0,044 — CFI và RMSEA trông «hoàn
  hảo» dù nghiệm không chấp nhận được. Vì vậy công cụ KHÔNG phân loại khi `lavInspect(fit, "post.check")` sai hoặc mô hình
  không hội tụ; chỉ đọc CFI/RMSEA sẽ báo «phù hợp tốt» cho nhiễu.
- Bản đầu để psych chạy song song: pytest toàn repo bắt được phân tích song song đổi kết quả giữa hai lần chạy cùng hạt
  giống (0 rồi 3 nhân tố trên cùng bộ nhiễu) ⇒ ép chạy tuần tự; test R thật nay so từng chữ số trị riêng giữa hai lần.

Kiểm đột biến (CLAUDE.md §0.8, sao lưu + `cmp`, `python -B`, xoá `__pycache__`, nền xanh): 17 phép — bỏ yêu cầu xoay xiên,
ngưỡng ≥ thành >, `sim = TRUE`, lỗi `-seq_len(0)` khi chia tầng, ULSMV thay WLSMV, chia nửa cho lệch 2, luật 5% thành > 5%,
CFA không hội tụ vẫn mã 0, bỏ đối chiếu số câu, `chay_sap_g6` không định tuyến, không bắt thiếu `tang`, nhận mọi số nguyên,
bỏ rào thư mục ngoài repo, nhận nhiều hạt giống, sắp tầng theo locale, bỏ chốt `post.check`, bỏ chạy tuần tự — cả 17 làm
test đỏ đúng chỗ rồi phục hồi xanh (phép sắp theo locale lọt ở lượt đầu; đã thêm chốt khớp dòng thi hành rồi đo lại: đỏ).

## SPSS

`cau_noi_spss.py` không được dùng cho phần này: lệnh FACTOR của SPSS chỉ làm EFA trên ma trận Pearson (không polychoric),
SPSS Statistics không có CFA (cần AMOS). Chạy EFA Pearson bằng SPSS KHÔNG tương đương phương pháp SAP đã khoá.

## Ranh giới

Không đổi trạng thái cổng nào, không ký, không ghi `study_meta.json`, sổ cái phê duyệt hay `G6_DAC_TA_SAP.json`. R chỉ
nhận câu hỏi và cột phân tầng; cột «Identifier?=y» hoặc ngoài từ điển G5 ⇒ từ chối. Ngoài phạm vi: phân bố điểm, Cronbach
α, omega G1–G3, sàn–trần (4.5.3 ý 1–3).

Cần bác sĩ kiểm chứng.
