# PLS-SEM trong hệ nghiên cứu — seminr tính chính, cSEM kiểm chéo, sách Hair 2021 làm mốc chuẩn

Bác sĩ chủ nhiệm (23/11/2026) muốn PLS-SEM «tốt nhất, tương tự SPSS/R». Bác sĩ không có bản quyền SmartPLS; SmartPLS 4
chỉ có giao diện, không có CLI/API công khai. Năng lực PLS-SEM của hệ đi theo đúng mô hình cầu nối SPSS ↔ R: một phần
mềm tính chính, một bản cài đặt độc lập kiểm chéo từng đại lượng, một mốc chuẩn công khai.

Công cụ: `tools/pls_sem.py` (chủ: `phan-tich-thong-ke`). Kịch bản R nằm trong cầu nối R duy nhất
(`tools/cau_noi_r.py` — `R_PLS_SEM`, `kich_ban_pls_sem()`); gói cài qua `python3 tools/cau_noi_r.py cai-goi --ap-dung`
(`seminr`, `cSEM` đã khai trong `GOI_CAN`).

## 1. Ba lớp

| Lớp | Phần mềm | Việc |
|---|---|---|
| Tính chính | R `seminr` (đo 23/11/2026: 2.6.0) | PLS-PM, Mode A (kết quả) / Mode B (cấu tạo), sơ đồ trọng số trong theo đường dẫn, bootstrap đúng số lần SAP khai, PLSpredict (tiền tố trực tiếp) |
| Kiểm chéo | R `cSEM` (0.7.1) | CÙNG mô hình, CÙNG dữ liệu; `.disattenuate = FALSE`; ρA Dijkstra–Henseler từ lượt PLSc trên cùng trọng số Mode A; f² theo đúng định nghĩa seminr (ước lượng lại mô hình bỏ đường dẫn) |
| Mốc chuẩn | sách Hair và cộng sự 2021, doi:10.1007/978-3-030-80519-7 (CC BY 4.0) | `pls_sem.py chuan` chạy lại hai mô hình corporate reputation (dữ liệu `seminr::corp_rep_data`) và so với số in trong VĂN BẢN chương 4–6 |

## 2. Lệnh

```bash
python3 tools/pls_sem.py kiem                      # R + jsonlite/seminr/cSEM
python3 tools/pls_sem.py cai-goi [--ap-dung]       # qua cau_noi_r cai-goi
python3 tools/pls_sem.py cu-phap --study <mã>      # tập phân tích + cấu hình + script R (không cần R)
python3 tools/pls_sem.py chay --study <mã> [--gate G6] [--loc "<biểu thức>"]
python3 tools/pls_sem.py chuan [--thu-muc-ra <NGOÀI repo>]
```

Mặc định đọc bộ dữ liệu ĐÃ KHOÁ G5 và chỉ chạy khi G4 khoá theo trạng thái sống (cùng hàm `run_stats_analysis`). Diễn
tập: `--data <csv> --ban-nhap --thu-muc-ra <NGOÀI repo>` (không mang `data_lock`, G7 không dựng Kết quả từ đó).

Phiên bản tối thiểu: seminr ≥ 2.6.0 (`PHIEN_BAN_TOI_THIEU`) — NEWS.md của seminr 2.6.0 ghi trước bản này `predict_pls`
lặp lại kiểm định chéo trên CÙNG các fold khi `reps > 1`; bản cũ hơn ⇒ mã 2, không chạy PLSpredict bằng bản có lỗi đã biết.
cSEM không có lỗi tương đương được ghi nhận nên không đặt sàn (đã đo với 0.7.1).

Dữ liệu vào R: giá trị không thuộc thang từ điển G5 ⇒ thiếu và CẢNH BÁO «ngoài thang» (đối chiếu phiếu gốc); mã thiếu cấp
dự án ở `_ma-thieu-theo-bien.csv` (BTR, KDD, 9…, đúng luật áp mã `cau_noi_spss._ap_cho_cot` dùng cho SPSS/nhập liệu) ⇒ thiếu,
đếm riêng (`ma_thieu_khai_theo_chi_bao`), không cảnh báo; rồi xử lý đúng cách SAP §4 khai.

Mã thoát: 0 seminr ra kết quả và kiểm chéo khớp · 1 R/seminr lỗi hoặc kiểm chéo LỆCH · 2 không đo được (không có R/gói,
kiểm chéo không so được) · 3 từ chối (SAP không khai/khai thiếu PLS-SEM, dữ liệu hoặc G4 chưa khoá, PII, đặc tả lệch SAP).

## 3. SAP là nguồn duy nhất của mô hình

PI chốt mô hình lý thuyết ở G1: `gate_params.G1.pls_sem` =

```json
{"cau_truc": [{"ma": "GT", "ten": "…", "muc": ["gt_1", "gt_2", "gt_3"], "mode": "A"},
              {"ma": "HB", "ten": "…", "muc": ["hb_1", "hb_2", "hb_3"], "mode": "B"}],
 "duong_dan": [["GT", "NT"], ["HB", "NT"], ["NT", "TT"]],
 "bien_minh": "vì sao PLS-SEM thay CB-SEM (Hair 2019)", "bootstrap": 5000,
 "plspredict": {"k": 10, "lap": 10, "dich": ["TT"]}, "du_lieu_thieu": "listwise"}
```

`run_g4_auto.py` in khối máy đọc được ở SAP §4 (`pls_sem.dong_sap`): phương pháp, biện minh PLS-SEM thay CB-SEM, mô
hình đo lường từng cấu trúc (mã — tên — Mode A/B: chỉ báo), mô hình cấu trúc (`A` → `B`), bootstrap (`5.000 mẫu lặp`,
KTC phân vị 95% cho đường dẫn/trọng số/tải, KTC 90% cho HTMT), PLSpredict, xử lý dữ liệu thiếu, ngưỡng đánh giá định trước
kèm nguồn đã kiểm. §5/§6 theo PLS-SEM (biến độc lập = tiền tố theo mô hình; VIF; thiếu theo §4, giả định MCAR, nghi
MAR/MNAR ⇒ độ nhạy §9). Hạt giống ở §10 (`set.seed(N)` hoặc `**Random seed:** N`); §10 ghi phần mềm có phiên bản.
G4-AUTO-10 đọc lại khối bằng ĐÚNG hàm G6 chạy (`pls_sem.doc_sap`): khối thiếu/hỏng hoặc G1 khai mà SAP không có ⇒ REVIEW.
Bộ đọc chỉ dựa vào mã cấu trúc trong backtick, cụm «kết quả (reflective, Mode A)»/«cấu tạo (formative, Mode B)» và danh
sách chỉ báo trong backtick — không dựa vào dấu ngăn cách, vì bộ chuẩn hoá văn phong của G4 (`vn_prose_style`) đổi « — »
thành «. »/«, » (lượt giả lập đầu 23/11/2026 từng bị chặn oan vì vậy; phép thử
`test_khoi_sap_doc_duoc_sau_chuan_hoa_van_phong_g4`).

Ngưỡng định trước (chỉ PHÂN LOẠI khi SAP còn ghi đủ các cụm `CUM_NGUONG_SAP`; thiếu ⇒ chỉ in số):

| Tiêu chí | Ngưỡng | Nguồn (DOI) |
|---|---|---|
| Tải ngoài (Mode A) | ≥ 0,708 | Hair 2019, 10.1108/EBR-11-2018-0203 |
| Cronbach α, ρA, ρC | 0,70–0,95 | Hair 2019; Dijkstra & Henseler 2015, 10.25300/MISQ/2015/39.2.02 |
| AVE | ≥ 0,50 | Fornell & Larcker 1981, 10.2307/3151312 |
| HTMT | < 0,90 và cận trên KTC 90% < 0,90 | Henseler 2015, 10.1007/s11747-014-0403-8 |
| Chỉ báo cấu tạo | VIF < 3 (3–5 cần xem; ≥ 5 đa cộng tuyến); trọng số có KTC không chứa 0, nếu không thì tải ≥ 0,50 | Hair 2019 |
| Mô hình cấu trúc | VIF < 3 (3–5; ≥ 5); đường dẫn có ý nghĩa khi KTC phân vị không chứa 0 | Hair 2019 |
| R² (mô tả) | 0,75 / 0,50 / 0,25 | Hair, Ringle & Sarstedt 2011, 10.2753/MTP1069-6679190202 |
| f² | 0,02 / 0,15 / 0,35 | Cohen 1988, 10.4324/9780203771587 |
| PLSpredict | Q²predict > 0; RMSE (MAE) PLS so với mô hình tuyến tính chuẩn | Shmueli 2019, 10.1108/EJM-02-2019-0189 |

DOI đối chiếu metadata Crossref 23/11/2026; kiểm rút bài 23/11/2026 (Crossref `updated-by`: không có thông báo; Retraction
Watch bản 07/11/2026: không có bản ghi). Các bài ở tạp chí kinh doanh/hệ thống thông tin nên không có PMID.

## 4. Cỡ mẫu (G3)

`run_g3_auto.py --effect-type PLS_PATH --effect-size <|β_min|>` (thiết kế cắt ngang): phương pháp căn bậc hai nghịch đảo
(Kock & Hadaya 2018, doi:10.1111/isj.12131) n > ((z₁₋α/₂ + z₁₋β)/|β_min|)². Công thức gốc dùng α MỘT phía (z₁₋α — với
|β_min| = 0,2 ra 155, đúng con số sách Hair 2021 chương 5 nêu); SAP kiểm hệ số đường dẫn bằng KTC bootstrap HAI phía nên
hệ dùng z₁₋α/₂ (|β_min| = 0,2 ⇒ 197, thận trọng hơn). |β_min| phải có nguồn (G3-AUTO-05).

## 5. G6 — đặc tả, chạy, chốt họ mô hình

Đặc tả `G6_DAC_TA_SAP.json`: phân tích chính khai `tham_so = {"pls_sem": "pls_pm", "bootstrap_pls": <N>, "loc": …}` —
mô hình KHÔNG nằm trong đặc tả (đọc từ SAP §4). Độ nhạy xử lý thiếu của SAP §9 khai thêm `"du_lieu_thieu":
"trung_binh"` (hoặc `"listwise"`). `chay_sap_g6.py kiem` chặn khi: SAP §4 khai PLS-SEM mà phân tích chính không phải
PLS-SEM; `bootstrap_pls` khác SAP; phân tích CHÍNH khai `du_lieu_thieu` khác SAP §4; đặc tả khai PLS-SEM mà SAP không có
khối; khối SAP hỏng (`kiem_pls_sap`). `chay` gọi `pls_sem.py chay` → `G6_analysis_summary.json` (khối `pls_sem`), `G6_ket_qua.md`,
`G6_kiem_cheo.json` (khuôn `kiem_cheo_g6`).

Chốt G6-AUTO-09 (cùng họ): `pls_sem` là họ RIÊNG và ĐỘC QUYỀN ở SAP §4 (từ khoá «PLS-SEM», «partial least squares»…; các
họ khác mà khối PLS-SEM vô tình nhắc — «mô hình tuyến tính chuẩn» của PLSpredict — bị bỏ); script nhận ra
`estimate_pls(`/`csem(`; lượt chạy nhận ra khối `pls_sem` có `danh_gia` và seminr không lỗi. SAP khai PLS-SEM mà lượt chạy
là họ khác ⇒ CHẶN; SAP không khai mà lượt chạy là PLS-SEM ⇒ CHẶN.

`run_g6_auto.py` sinh `scripts/03_analysis.R` PLS-SEM chép từ khối SAP (dòng `estimate_pls(` thi hành, đánh dấu ◆).

## 6. Luật kiểm chéo seminr ↔ cSEM

- **Tất định** (tải, trọng số, α, ρA, ρC, AVE, HTMT, VIF chỉ báo cấu tạo, VIF cấu trúc, β, R², R² hiệu chỉnh, f², hiệu ứng
  tổng): |Δ| ≤ 1e-5 (VIF: tương đối). Hai gói lặp tới hội tụ (seminr 10⁻⁷, cSEM 10⁻¹⁰) — đo trên corp_rep_data trùng
  tới ~10⁻⁸.
- **Phạm vi theo loại cấu trúc** (Hair 2019): α/ρA chỉ cho Mode A ≥ 2 chỉ báo; ρC/AVE/HTMT cho Mode A; VIF chỉ báo và
  trọng số cho Mode B; tải bootstrap cho Mode A.
- **Bootstrap** (hai bộ sinh số độc lập): hiệu hai SD so theo √(Var SD_seminr + Var SD_cSEM), mỗi Var(SD) ≈
  SD²(2 + κ)/(4B) với SD và κ (độ nhọn dư) của CHÍNH phân phối bootstrap gói đó; hiệu hai cận KTC theo
  √(p(1−p)·(s_seminr²/B₁ + s_cSEM²/B₂)), s độ thưa thực nghiệm của từng gói trên cửa sổ h = max(0,01; 15/B). Ngưỡng
  Bonferroni cho CẢ HỌ phép so (α họ = 0,01) — giữ xác suất báo lệch giả của cả lượt ≤ 1%. Lý do dùng phân phối riêng
  từng gói (đo 23/11/2026, giả lập nhóm nam 144 ca): 1/5.000 mẫu lặp cSEM đổi dấu cấu trúc TT (tải tt_1 = −0,911),
  seminr không — SD cSEM 0,041–0,048 so với 0,033 trong khi KTC phân vị trùng; độ nhọn của riêng seminr không giải
  thích được.
- **Đổi dấu cấu trúc trong bootstrap** (thành phần PLS xác định tới một dấu): đếm mẫu lặp mà MỌI tải của một cấu trúc
  Mode A ngược dấu ước lượng gốc, cho cả hai gói (`doi_dau_bootstrap`); seminr (phân tích chính) có mẫu đổi dấu ⇒ cảnh
  báo trong tóm tắt (SD và t bị thổi phồng; ý nghĩa đọc theo KTC phân vị). Không gói nào tự sửa dấu (seminr không có cơ
  chế; cSEM để mặc định `.sign_change_option = "none"`).
- **HTMT bootstrap**: seminr lấy trị tuyệt đối TỪNG tương quan (`seminr:::HTMT`); `cSEM::calculateHTMT` dùng tương quan
  CÓ DẤU rồi lấy trị tuyệt đối của HTMT — trùng khi mọi tương quan dương (HTMT gốc khớp ~10⁻⁸), khác khi mẫu lặp có
  tương quan ≤ 0 (đo 23/11/2026, nhóm nữ 59 ca: phân vị 5% HTMT GT–NT seminr 0,216 · cSEM 0,172 · mã độc lập theo định
  nghĩa seminr 0,219–0,220). Ngoài ra `cSEM::assess(.inference = "bootstrap")` lấy mẫu lại RIÊNG với mặc định 499 mẫu
  KHÔNG hạt giống (hai lượt cùng dữ liệu ra KHOP rồi LECH). Hệ vì vậy tính HTMT bootstrap phía cSEM bằng hàm người dùng
  (`.user_funs`) trên CHÍNH mẫu lặp của cSEM với công thức đúng định nghĩa seminr, và ghi số mẫu lặp có tương quan ≤ 0
  (`htmt_mau_tuong_quan_am`).
- **PLSpredict**: chia phần ngẫu nhiên ⇒ J lượt độc lập mỗi gói (mặc định 5), so trung bình RMSE/MAE của PLS theo t họ
  Bonferroni. Khi lặp r > 1 hai gói KHÁC định nghĩa: seminr lấy trung bình DỰ BÁO qua các lần lặp rồi tính RMSE/MAE
  (`mean_over_reps` trong `seminr::predict_pls`), cSEM tính chỉ số TỪNG lần lặp rồi lấy trung bình (`cSEM::predict`)
  ⇒ phép kiểm chéo dùng J lượt r = 1 ở cả hai gói (`luot_doi_chieu`); số báo cáo vẫn là lượt đúng r của SAP. Đo
  23/11/2026: so lượt r = 10 từng báo LỆCH chập chờn (MAE tt_2 0,6829 so với 0,6850). seminr chạy `cores = 1` vì chia phần
  song song không tái lập theo `set.seed`. Mô hình tuyến tính chuẩn (LM) KHÁC định nghĩa (seminr: chỉ báo tiền tố trực tiếp; cSEM «lm»: mọi chỉ báo
  ngoại sinh) ⇒ «không so». Q²predict chỉ cSEM tính (định nghĩa Shmueli 2019) ⇒ «không so», báo cáo kèm nhãn nguồn.
- **f²**: seminr (`seminr:::fSquared`) ước lượng LẠI PLS-PM không có đường dẫn; `cSEM::calculatef2` dùng điểm cấu trúc
  của mô hình đầy đủ — hai định nghĩa khác nhau (đo: CUSA → CUSL 0,403 so với 0,412). Hệ kiểm chéo ĐÚNG định nghĩa
  seminr (sách dùng): cSEM ước lượng lại mô hình bỏ đường dẫn; f² gốc của cSEM ghi riêng `f2_csem_goc`.
- seminr đặt hạt giống `seed + i` cho mẫu bootstrap thứ i ⇒ hai lượt seminr hạt giống liền nhau trùng gần hết mẫu (đo:
  hạt giống 1 và 2 với B = 4000 cho cùng phân vị 2,5% và 97,5%) — không bao giờ coi là hai lượt độc lập.

## 7. Mốc chuẩn — số đo 23/11/2026 (R 4.6.2, seminr 2.6.0, cSEM 0.7.1; bootstrap 1000, seed 123 như sách)

Số in trong sách là ẢNH CHỤP RStudio chạy SEMinR (chú thích hình «authors' screenshot from RStudio»; mã in trong chương
dùng `library(seminr)`) — **không phải số SmartPLS**. Hệ chỉ khẳng định «tái lập đúng số in trong sách Hair 2021 (tính
bằng SEMinR)», KHÔNG khẳng định «ngang SmartPLS».

| Nhóm | Số in trong văn bản sách | seminr khớp | cSEM khớp (đại lượng tất định) |
|---|---|---|---|
| Chương 4 (mô hình đơn giản): α, ρA, ρC, AVE, tải, số vòng lặp, KTC 90% HTMT COMP–CUSA | 17 | 17 | 14/14 tất định |
| Chương 5 (Mode B): VIF qual_3, tải qual_2, KTC trọng số csor_2 (2 cận), số vòng lặp | 5 | 5 | 2/2 tất định |
| Chương 6 (cấu trúc): VIF QUAL, 6 hệ số β, 9 giá trị t bootstrap, 4 hiệu ứng tổng, 4 R², 4 f², 3 RMSE PLS | 31 | 31 | 19/19 tất định |
| Chương 6: RMSE mô hình tuyến tính chuẩn (cusl_1–3) | 3 | khác phiên bản | — |

Ba giá trị khác: sách 1,228 / 1,312 / 1,380; seminr 2.6.0 1,205 / 1,254 / 1,334. NEWS.md của seminr 2.6.0: trước 2.6.0
`predict_pls(reps = k)` «repeated the cross-validation on the same folds» — kết quả đổi với mọi lệnh reps > 1; sách chạy
bản cũ, không đặt hạt giống. RMSE của PLS vẫn khớp (1,193 / 1,239 / 1,312 so với 1,192 / 1,239 / 1,312).

Kiểm chéo seminr ↔ cSEM trên dữ liệu đủ (đo lại 23/11/2026 sau khi thêm r thô, HTMT bootstrap cùng định nghĩa và
PLSpredict 1 lần lặp): mô hình đơn giản 141 khớp, 0 lệch, 5 không so; mô hình mở rộng 397 khớp, 0 lệch, 15 không so (LM,
Q²predict, tải bootstrap của cấu trúc một chỉ báo…). Mốc chuẩn sách không đổi: 53 khớp, 3 khác phiên bản.

Giả lập `cross_sectional_pls_sem` (dữ liệu mô phỏng, bootstrap 5.000, hạt giống SAP): phân tích chính 203 ca, nhóm nam
144 ca, nhóm nữ 59 ca — mỗi lượt 144 khớp, 0 lệch, 7 không so sau hai lần sửa ở trên (trước khi sửa: chính 1 lệch HTMT, nam
4 lệch SD tải TT, nữ 4 lệch HTMT).

## 8. G7

`run_g7_auto.py` chép NGUYÊN VĂN các dòng `pls_sem.trinh_bay_md` mà G6 dựng (thứ tự Hair 2019: đo lường trước, cấu trúc
sau; số kiểu Việt ba chữ số, dấu trừ «−», KTC có cận âm viết «a đến b») — phép tự kiểm số của G7 đối chiếu chuỗi số với
tệp tóm tắt. Bảng mô hình cấu trúc có cả r thô (tương quan chưa hiệu chỉnh giữa điểm hai cấu trúc, KTC 95% Fisher z,
kiểm chéo tất định với `Construct_VCV` của cSEM) và β hiệu chỉnh — STROBE 16a. G6 tự sinh hình cột điểm trung bình các
cấu trúc Mode A kèm KTC 95% (`hinh_g6`, hình bắt buộc của cắt ngang). Đề cương G10: yếu tố nhiễu lấy từ dòng «Kiểm soát
nhiễu» SAP §5 (`quyet_dinh_da_chot`). Kiểm chéo cSEM không khớp ⇒ ô
[CẦN THỐNG KÊ VIÊN]; seminr lỗi ⇒ ô [CẦN THỐNG KÊ VIÊN] thay bảng.

## 9. Ghi chú cho đề tài thật C1a (hai-long-benh-nhan-C1a-BVQY175) — KHÔNG áp dụng tự động

SAP C1a đã khoá với giá trị cấu trúc bằng EFA (nửa 1) + CFA WLSMV (nửa 2, `lavaan`) — mô hình nhân tố CHUNG (CB-SEM),
và phân tích chính là hồi quy thứ tự. Hệ KHÔNG đổi C1a sang PLS-SEM. Muốn dùng PLS-SEM cho C1a phải SỬA ĐỔI SAP TRƯỚC KHI
CÓ DỮ LIỆU (sau khi xem dữ liệu thì mọi phân tích PLS-SEM chỉ là THĂM DÒ):

1. **G1 — PI**: khai `gate_params.G1.pls_sem` (năm lĩnh vực A–E là cấu trúc nào, Mode A hay B và lý do, đường dẫn tới
   hài lòng chung, biện minh chọn PLS-SEM thay CB-SEM — vd mục tiêu dự báo, có cấu trúc cấu tạo); nếu đổi mục tiêu thì sửa
   mục tiêu G1.
2. **G3 — thống kê viên/PI**: N hiện tại theo độ chính xác của tỷ lệ; nêu |β_min| có nguồn và đối chiếu với N đã chốt
   (`--effect-type PLS_PATH`) — không đổi N âm thầm.
3. **G4 — thống kê viên + PI ký** (`approve_gate.py --gate G4`, vai STATISTICIAN và PI): SAP sửa đổi (ghi PHẦN 4 «SAP
   AMENDMENT») gồm khối PLS-SEM §4, §5/§6 theo PLS-SEM, hạt giống §10, ngưỡng định trước kèm nguồn; quyết định giữ hay bỏ
   EFA/CFA (PLS-SEM KHÔNG thay CFA trong đánh giá giá trị cấu trúc theo mô hình nhân tố chung).
4. **G2 — Hội đồng đạo đức (IRB)**: đổi phương pháp phân tích chính/mục tiêu là sửa đổi đề cương ⇒ thông báo/xin chấp
   thuận sửa đổi theo quy định đơn vị; cập nhật đăng ký nghiên cứu (mục đích phát hành REGISTRY_UPDATE).
5. **G6**: soạn lại `G6_DAC_TA_SAP.json` theo SAP mới (`pls_sem` + `bootstrap_pls`), thống kê viên/PI duyệt lại đặc tả.

Không ký thay, không sửa `exports/` của C1a trong lượt này.

Cần bác sĩ kiểm chứng.
