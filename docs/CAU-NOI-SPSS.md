# Cầu nối IBM SPSS Statistics (G5–G6)

Bác sĩ giao ngày 14/11/2026: «xây dựng kết nối với SPSS giúp tôi một cách tốt nhất». Công cụ: `tools/cau_noi_spss.py`
(Python của hệ, `~/.ebm-venv`), trình chạy nền: `tools/spss_chay_nen.py` (do Python ĐI KÈM SPSS thực thi).

## SPSS dùng để làm gì trong hệ

SPSS là **phần mềm thứ hai, chạy độc lập** để tái lập phân tích G6. Phân tích chính vẫn do `run_stats_analysis.py`
chạy (chủ G6). SPSS chạy lại cùng phân tích trên cùng bộ dữ liệu đã khoá rồi đối chiếu từng ước lượng. Ngoài ra, công
cụ xuất dữ liệu khoá sang `.sav` có đủ nhãn để bác sĩ/thống kê viên mở trong SPSS, và nhận tệp `.sav` của bác sĩ vào
cổng tiếp nhận.

SPSS chạy ở **chế độ nền** (external mode): không mở giao diện, không cần bấm. Máy không có SPSS (Windows chưa cài,
Cloud, CI) thì công cụ vẫn sinh cú pháp `.sps` để chạy tay trong SPSS ở máy khác.

## Lệnh

Chạy trong `medical-ebm-automation/`:

| Lệnh | Việc | Đầu ra |
|---|---|---|
| `python3 tools/cau_noi_spss.py kiem` | Tìm SPSS, phiên bản, chạy thử, liệt kê mô-đun được cấp phép | màn hình |
| `… xuat-sav --study <mã>` | Dữ liệu ĐÃ KHOÁ + từ điển REDCap G5 + mã thiếu cấp dự án ⇒ `.sav` có nhãn | `exports/<mã>/spss/<mã>_nhan_bien.sps`, `<mã>_khoa.sav` (chỉ đọc), manifest |
| `… cu-phap --study <mã>` | Cú pháp phân tích khớp đặc tả G6 | `exports/<mã>/spss/<mã>_phan_tich.sps` |
| `… chay --study <mã>` | Chạy cú pháp trong SPSS | `spss/ket_qua/*.xml` (OXML), `<mã>_phan_tich.spv`, `G6_spss_ket_qua.json` |
| `… doi-chieu --study <mã>` | So SPSS ↔ Python | `G6_spss_doi_chieu.md` + `.json` |
| `… nhap-sav --sav <tệp> --ra <thư mục ngoài repo>` | `.sav` của bác sĩ ⇒ CSV + từ điển nhãn + từ điển khuôn REDCap | thư mục `--ra` |

Mã thoát: 0 xong/khớp · 1 lệch hoặc SPSS lỗi · 2 không đo được (không có SPSS, thiếu tệp) · 3 từ chối (PII, dữ liệu
không khớp manifest khoá, tham số sai).

## Thứ tự dùng cho một đề tài

1. G5 khoá dữ liệu (`lock_analysis_dataset.py`) — manifest khoá ghi SHA-256.
2. G6 phân tích chính: `run_stats_analysis.py … --study <mã>` — ghi `G6_analysis_summary.json` kèm khoá
   `dac_ta_phan_tich` (kết cục, nhóm, hiệp biến, loại kết cục, thời gian/biến cố, cột cụm).
3. `xuat-sav` → `cu-phap` → `chay` → `doi-chieu`.

`cu-phap` đọc đặc tả từ bước 2, nên không phải khai lại. Muốn khác đặc tả thì truyền `--outcome/--group/--covariates/
--outcome-type/--time/--event/--cot-cum` như `run_stats_analysis.py`.

## Xuất `.sav` giữ được những gì

- **Tên biến**: lấy «Tên SPSS: X» trong cột Field Annotation của từ điển G5 (đề tài hài lòng C1a đã ghi sẵn); không có
  thì dùng tên REDCap. Tên được kiểm theo luật SPSS (không trùng từ khoá BY/WITH…, ≤ 64 byte).
- **Nhãn biến** (bỏ thẻ HTML của REDCap), **nhãn giá trị** từ lựa chọn radio/dropdown/checkbox/yesno.
- **Mức đo**: SCALE cho số; ORDINAL cho thang ≥ 4 mức mã liên tiếp (Likert); NOMINAL cho phân loại.
- **Mã thiếu cấp dự án** (`exports/<mã>/_ma-thieu-theo-bien.csv`): mã chữ cho mọi trường (BTR, KDD) được `RECODE`
  thành −9991, −9992… và khai `MISSING VALUES` + nhãn; mã số riêng từng biến (vd 998) khai `MISSING VALUES`. Mọi biến
  đổi nằm trong cú pháp — tệp dữ liệu khoá không bị sửa.
- Từ chối khi từ điển đánh dấu cột là định danh (`Identifier? = y`) hoặc SHA-256 dữ liệu không khớp manifest khoá.

## Đối chiếu SPSS ↔ Python — đọc thế nào

Ngưỡng khớp: ước lượng ±0,5 %, KTC ±1,5 %, p ±0,005 (hai bên < 0,001 coi là khớp).

- **✓ khớp**: có thể ghi ở phần phương pháp «kết quả được tái lập độc lập bằng IBM SPSS Statistics <phiên bản>».
- **⚠ lệch nhỏ**: khác phương pháp đã biết, ước lượng điểm trùng:
  - hiệu chỉnh cụm — SPSS GENLIN (GEE độc lập, SE robust) so với Python (sandwich theo cụm có hiệu chỉnh mẫu nhỏ, phân
    phối t); số cụm ít thì KTC của Python rộng hơn rõ;
  - Cox — SPSS xử lý thời điểm trùng bằng Breslow, lifelines bằng Efron;
  - hồi quy thứ tự — statsmodels lấy SE từ Hessian xấp xỉ (KTC lệch ~0,3 %).
  Thống kê viên chọn cách báo cáo theo SAP.
- **✗ LỆCH**: tìm nguyên nhân (mã hoá biến, tập ca phân tích, nhóm tham chiếu) trước khi dùng số. Không sửa Python cho
  khớp SPSS hay ngược lại.

Đo thật 14/11/2026 (SPSS 31.0.1, Mac, dữ liệu giả 240 ca, phía Python gọi đúng hàm của `run_stats_analysis.py`):
logistic, tuyến tính, OR thô, t-test khớp tới 6 chữ số; thứ tự khớp; cụm «lệch nhỏ» đúng như dự đoán; Cox khớp sau khi
cú pháp SPSS lọc đúng tập ca — phép đối chiếu phát hiện HR «thô» của Python được tính trên tập ca đầy đủ hiệp biến của
mô hình hiệu chỉnh (228 ca), không phải toàn bộ 240 ca.

Biến phân loại dạng chữ: SPSS mã hoá khác Python (Indicator so với patsy) nên những hệ số đó hiện «⚪ không so được».

## Máy và cài đặt

- **Mac**: `/Applications/IBM SPSS Statistics/Resources/Python3/bin/python3.13`. Ở SPSS 31.0.1, tệp `python3` cùng thư
  mục bị hỏng liên kết (trỏ thư viện Homebrew `/usr/local/opt/gettext`) — công cụ tự chọn `python3.X`.
- **Windows**: `C:\Program Files\IBM\SPSS Statistics\Python3\python.exe` (tự dò; chưa đo thật trên máy Windows).
- Cài chỗ khác: đặt biến môi trường `EBM_SPSS_PYTHON=<đường dẫn python của SPSS>`.
- Bảng in ra luôn bằng tiếng Anh và hiện TÊN biến (`SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES`) để bộ đọc OXML ổn
  định; nhãn tiếng Việt vẫn nằm trong `.sav` và `.spv`.

## Ranh giới

Kiểm chéo kỹ thuật: không đổi trạng thái cổng G6, không thay G6-HUMAN-01 (thống kê viên), không ký, không ghi
`study_meta.json` hay sổ cái phê duyệt. Đầu ra nằm trong `exports/<mã>/` (ngoài git). Dữ liệu chưa qua cổng tiếp nhận
không được đặt trong repo (`nhap-sav` từ chối thư mục ra trong repo).

Cần bác sĩ kiểm chứng.
