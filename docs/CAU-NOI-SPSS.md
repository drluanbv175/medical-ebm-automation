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
| `… xuat-sav --study <mã>` | Dữ liệu ĐÃ KHOÁ + từ điển REDCap G5 + mã thiếu cấp dự án ⇒ `.sav` có nhãn | `exports/<mã>/spss/<mã>_nhan_bien.sps`, `<mã>_khoa.sav` (chỉ đọc), manifest, `de-xuat-ma-thieu.csv` (nếu có) |
| `… cu-phap --study <mã>` | Cú pháp phân tích khớp đặc tả G6 | `exports/<mã>/spss/<mã>_phan_tich.sps` |
| `… chay --study <mã>` | Chạy cú pháp trong SPSS | `spss/ket_qua/*.xml` (OXML), `<mã>_phan_tich.spv`, `G6_spss_ket_qua.json` |
| `… doi-chieu --study <mã>` | So SPSS ↔ Python | `G6_spss_doi_chieu.md` + `.json` |
| `… cu-phap --study <mã> --thang-do "A:a1,a2,a3"` | Thêm RELIABILITY cho thang đo (lặp được) | `<mã>_phan_tich_bo_sung.sps` |
| `… nhap-sav --sav <tệp> --ra <thư mục ngoài repo>` | `.sav` của bác sĩ ⇒ CSV + từ điển nhãn + từ điển khuôn REDCap | thư mục `--ra` |

Mã thoát: 0 xong/khớp · 1 lệch hoặc SPSS lỗi · 2 không đo được (không có SPSS, thiếu tệp) · 3 từ chối (PII, dữ liệu
không khớp manifest khoá, tham số sai).

## Một lệnh cho cả SPSS + R (tự động hoá 14/11/2026)

`python3 tools/kiem_cheo_g6.py chay --study <mã>` chạy trọn hai chuỗi lệnh:
- SPSS: `xuat-sav` (chỉ khi `.sav` chưa có hoặc không khớp dữ liệu khoá) → `cu-phap` → `chay` → `doi-chieu`.
- R (`tools/cau_noi_r.py`): `cu-phap` → `chay` → `doi-chieu`.

Kết quả ghi MỘT báo cáo chung `G6_kiem_cheo.md/.json`:
- Trạng thái chung theo thứ tự ưu tiên: LỆCH > lỗi > từ chối > lệch nhỏ > khớp.
- Máy thiếu một phần mềm ⇒ phần đó «⚪ không đo được», phần kia vẫn chạy.
- Tuỳ chọn: `--chi spss|r` để chạy riêng một phần mềm; `--thang-do` truyền cho SPSS.

Trạng thái đọc nhanh, không chạy phần mềm nào: `… trang-thai --study <mã>` hoặc `--tat-ca`.
- Báo «CŨ» khi `G6_analysis_summary.json` hoặc dữ liệu khoá đổi sau lượt kiểm chéo (so bằng dấu vân tay SHA-256).
- Ba nơi dùng chung hàm này (chỉ hiển thị, không mở/chặn cổng):
  - Hòm việc (repo gốc `tu_de_xuat_viec.py`): chưa kiểm chéo/CŨ ⇒ 🛎, LỆCH/lỗi ⇒ 👤.
  - `study_readiness.py`: mục «KIỂM CHÉO G6», đếm là việc còn treo.
  - Đài kiểm soát `audit_research_gates.py`: dòng `kiem_cheo_g6=…`, gắn vào cổng G6.
- Agent `dieu-phoi-g6` chạy lệnh này sau G6-T1; khi LỆCH thì trả về `phan-tich-thong-ke`.

## Khứ hồi từng ô, kiểm từ điển và bản .rds cho R (E3 · E2 · E4 — 14/11/2026)

**E3 — khứ hồi từng ô, tự động ở mọi lượt `xuat-sav`.** SPSS tạo `.sav` trong vùng tạm, rồi cầu nối gọi
`spss_chay_nen.py --du-lieu` đọc lại MỌI ca bằng `spss.Cursor` (giá trị thô — `SAVE TRANSLATE /TYPE=CSV` làm tròn theo định
dạng hiển thị nên không dùng). Từng biến × từng ca được so với giá trị suy từ CSV nguồn qua CÙNG kế hoạch biến: biến số =
`float(ô)` (ô rỗng ⇒ SYSMIS, mã chữ BTR/KDD… ⇒ −9991/−9992…), biến chuỗi = ô gốc bỏ dấu cách cuối. Lệch dù một ô ⇒ bỏ
`.sav`, mã 1, in tối đa 10 lệch đầu (ca · biến · kỳ vọng · nhận được · loại: cắt cụt theo độ rộng, hỏng mã hoá tiếng Việt,
mất số thành SYSMIS, dịch dòng…; giá trị biến chữ tự do bị che) và ghi `khu_hoi` vào manifest. So số theo ngưỡng 8 ulp: bộ
đọc số của SPSS 31 (và R) lệch `float()` của Python tới 6 ulp với số 16–17 chữ số. Luật GET DATA đo thật: ô rỗng/chỉ dấu
cách ⇒ SYSMIS; dấu cách quanh số bị bỏ nhưng TAB thì không (`\t3` ⇒ SYSMIS); `NA`, `1_000`, `3,5`, `1,000` ⇒ SYSMIS; chuỗi
giữ khoảng trắng đầu, bỏ dấu cách cuối, quá độ rộng thì cắt theo byte; dòng trống bị bỏ, ô có xuống dòng bị tách thành
hai ca. Phép khứ hồi đã tìm ra một lỗi thật (độ rộng A đo trên ô đã bỏ khoảng trắng đầu ⇒ «  Nguyễn Văn» bị cắt), đã vá.

**E2 — từ điển `.sav` ↔ kế hoạch.** Cùng lượt đọc lại (một lần khởi động SPSS), so tên + thứ tự biến, số/chuỗi (độ rộng
A), nhãn biến, nhãn giá trị (kể cả nhãn mã thiếu), MISSING VALUES, mức đo; lệch ⇒ bỏ tệp, mã 1, ghi `kiem_tu_dien`.

**E2 — `.rds` có nhãn cho R/RStudio:** `python3 tools/cau_noi_r.py xuat-rds --study <mã>` (bản nháp: `--data <csv>
--ban-nhap`). Dựng từ CÙNG kế hoạch biến với `.sav` ⇒ `exports/<mã>/r/<mã>_khoa.rds` (chỉ đọc) + manifest + script `.R`
chạy tay được. Script chỉ cần BASE R để ghi; thuộc tính theo khuôn haven (`labels` gồm nhãn mã thiếu, `na_values`/
`na_range`, `label`, `format.spss`) nên `haven::as_factor`/`zap_missing` dùng được ngay. Sau khi ghi, đọc lại `.rds` và so
TỪNG ô với nguồn + thuộc tính với kế hoạch; máy có haven thì thêm chặng `.sav` ↔ `.rds`. Kết quả ba chiều: từ điển ↔ .sav ·
từ điển ↔ .rds · .sav ↔ .rds — chặng không đo được ghi «chưa đo», không bao giờ «khớp». Mã: 0 khớp · 1 lệch/R lỗi · 2 không
có R · 3 từ chối. Mã thiếu của biến CHUỖI («» và mã chữ) không mang sang `.rds`. Tên cột của `.rds`/`.sav` là tên SPSS
(«Tên SPSS: …» trong Field Annotation, vd `Tuoi`, `GioiTinh`).

**E4 — kiểm chéo ngay sau phân tích chính:** `python3 tools/run_stats_analysis.py … --kiem-cheo` chạy `kiem_cheo_g6.py chay`
sau khi ghi `G6_analysis_summary.json`. Chỉ TƯ VẤN: không đổi mã thoát, không đổi trạng thái cổng; thiếu SPSS/R hay kiểm
chéo lỗi chỉ in ra.

**Đo đầu–cuối trên Mac của bác sĩ (14/11/2026, từ điển C1a thật, dữ liệu giả):** Excel nhập tay ⇒ `nhap_lieu_excel.py
nhap` (CSV, tự kiểm khớp từng ô) ⇒ `xuat-sav --ban-nhap` (E3: 231 ô khớp, E2 khớp) ⇒ `xuat-rds --ban-nhap` (231 ô khớp ·
từ điển ↔ .sav ↔ .rds đều khớp); RStudio đọc nhãn tiếng Việt UTF-8, `zap_missing` biến BTR (−9991) thành NA.

## Thứ tự dùng cho một đề tài

1. G5 khoá dữ liệu (`lock_analysis_dataset.py`) — manifest khoá ghi SHA-256.
2. G6 phân tích chính: `run_stats_analysis.py … --study <mã>` — ghi `G6_analysis_summary.json` kèm khoá
   `dac_ta_phan_tich` (kết cục, nhóm, hiệp biến, loại kết cục, thời gian/biến cố, cột cụm).
3. `xuat-sav` → `cu-phap` → `chay` → `doi-chieu`.

`cu-phap` đọc đặc tả từ bước 2, nên không phải khai lại. Muốn khác đặc tả thì truyền `--outcome/--group/--covariates/
--outcome-type/--time/--event/--cot-cum/--don-vi-phoi-nhiem` như `run_stats_analysis.py` — nhưng `doi-chieu` sẽ TỪ CHỐI
khi đặc tả SPSS đã chạy khác đặc tả Python (kết cục, nhóm, hiệp biến, cụm, đơn vị phơi nhiễm).

Thiết kế kết cục THỨ TỰ + phơi nhiễm LIÊN TỤC (> 10 giá trị — C1a: thời gian chờ) theo đúng luật của Python: không có
Bảng 1 phân nhóm, không có so sánh thô 2 nhóm; `--don-vi-phoi-nhiem 15` ⇒ cú pháp `COMPUTE <biến>_dv = <biến> / 15.`
để OR là «mỗi 15 phút» như Python.

## Xuất `.sav` giữ được những gì

- **Tên biến**: lấy «Tên SPSS: X» trong cột Field Annotation của từ điển G5 (đề tài hài lòng C1a đã ghi sẵn); không có
  thì dùng tên REDCap. Tên được kiểm theo luật SPSS (không trùng từ khoá BY/WITH…, ≤ 64 byte).
- **Nhãn biến** (bỏ thẻ HTML của REDCap), **nhãn giá trị** từ lựa chọn radio/dropdown/checkbox/yesno.
- **Mức đo**: SCALE cho số; ORDINAL cho thang ≥ 3 mã LIÊN TIẾP mà ≥ một nửa nhãn mang dấu hiệu thứ bậc (rất · kém ·
  tốt · hài lòng · dưới · trên…, hoặc nhãn là số/khoảng) — mã giống-thiếu (8/9) không tính; NOMINAL cho phân loại. Đo
  trên từ điển C1a: 30 câu Likert, khoảng cách, thu nhập, số lần khám ⇒ ORDINAL; nghề nghiệp, hôn nhân, phương tiện,
  ngày trong tuần ⇒ NOMINAL (học vấn ra NOMINAL — thống kê viên chỉnh trong SPSS nếu muốn). Mức đo chỉ là siêu dữ liệu.
- **Mã thiếu cấp dự án** (`exports/<mã>/_ma-thieu-theo-bien.csv`, cột `bien,ma,nhan`):
  - `bien = *` áp MỌI trường nhưng CHỈ cho mã CHỮ (BTR, KDD): với biến số, mã chữ được `RECODE` thành −9991, −9992… (độ
    rộng đọc vào luôn đủ chứa mã thay — bản đầu đọc `A3` nên «BTR» bị cắt thành −99 HỢP LỆ); với biến chuỗi, mã chữ giữ
    nguyên và khai thiếu trực tiếp.
  - `bien` là mẫu glob (vd `[a-f][0-9]*`, `a?`) ⇒ áp cho mọi cột khớp, kể cả mã SỐ (vd 8/9 của 30 câu Likert C1a).
  - Còn lại: tên đúng một trường (vd `kyvong_thoigiancho,998`).
  - SPSS chỉ khai được 3 giá trị rời, hoặc một khoảng + một giá trị: mã chữ gom thành `LO THRU -9991`; không khai được
    hết ⇒ từ chối (mã 3) thay vì giữ 3 mã đầu.
  - Biến chuỗi: ô RỖNG khai là thiếu (`MISSING VALUES x ('')`) — SPSS mặc định coi ô rỗng là một mức hợp lệ (cụm «»
    riêng trong GENLIN), còn pandas coi là NaN ⇒ hai bên dùng tập ca khác nhau.
  - Mọi biến đổi nằm trong cú pháp — tệp dữ liệu khoá không bị sửa.
- **Đề xuất mã thiếu** `spss/de-xuat-ma-thieu.csv`: mã lựa chọn có nhãn giống thiếu («Không biết», «Không nhớ», «Từ
  chối», «Không áp dụng»…) mà chưa khai. Máy KHÔNG tự khai — thống kê viên quyết rồi ghi vào `_ma-thieu-theo-bien.csv`.
- **Trường «notes»** (văn bản tự do — dễ chứa tên, số điện thoại) bị bỏ khỏi `.sav` (`/DROP`); `--giu-ghi-chu` để giữ.
- Từ chối khi: từ điển đánh dấu cột là định danh (`Identifier? = y`); TÊN cột nghi định danh (luật quét tiêu đề của
  `import_real_dataset.py`, kể cả cột không có trong từ điển); bộ dữ liệu chưa qua cổng khoá (kiểm bằng
  `gate_contract.locked_analysis_dataset_blockers` — status `LOCKED_FOR_ANALYSIS`, `analysis_allowed`, có và khớp
  SHA-256).

## Phân tích bổ sung (mở rộng 14/11/2026)

`cu-phap` sinh thêm tệp `<mã>_phan_tich_bo_sung.sps`. `chay` chạy tệp này như một lượt SPSS RIÊNG, SAU phân tích chính.
Một khối hỏng (ví dụ GENLINMIXED không hội tụ) chỉ làm các dòng của khối đó thành «⚪ không so được»; phần đối chiếu
chính vẫn còn nguyên.

| Khối | Khi nào sinh | SPSS | Tham chiếu |
|---|---|---|---|
| Mô hình hỗn hợp | có cột cụm, kết cục thứ tự/nhị phân (`--khong-hon-hop` để tắt) | GENLINMIXED, intercept ngẫu nhiên theo cụm | R `ordinal::clmm` / `lme4::glmer` (Laplace) trên CÙNG tệp .sav |
| Trọng số hậu phân tầng | `G6_checkpoint.json → trong_so` (run_g6_auto rút từ SAP §4) + `his_tong_hop/N_tang_HIS.csv` (`--khong-trong-so` để tắt) | CSPLAN + CSDESCRIPTIVES (tỷ lệ hài lòng) + CSORDINAL (svyolr) | R `survey`: trọng số CỐ ĐỊNH (phải khớp) và `postStratify` (SAP — lệch nhỏ ở SE) |
| Độ tin cậy | `--thang-do "TÊN:mục1,mục2,…"` (lặp được) | RELIABILITY + ICC nhất quán (KTC Feldt) | `kiem_tin_cay_thang_do.py` trên cùng dữ liệu, cùng mã thiếu |
| Giả định tỷ lệ odds | kết cục thứ tự ≥ 3 mức | LOGISTIC nhị phân tại từng ngưỡng Y > k + Test of Parallel Lines | bảng OR theo ngưỡng + Brant của `run_stats_analysis.ordinal_model` |

Tham chiếu R chạy bằng `Rscript --vanilla` trên đúng tệp .sav SPSS dùng (haven, mã thiếu người dùng ⇒ NA). Script và kết
quả lưu ở `spss/ket_qua/r_doi_chieu.R` + `r_kq.json`. Không có R ⇒ dòng «⚪ không so được» (`--khong-r` để bỏ hẳn).

Trọng số:
- Bảng tầng (gộp tầng nₕ < ngưỡng, quy tắc kích hoạt) được tính hai lần: bằng bản Python của cầu nối, và bằng chính hàm R
  `04a_ham_trong_so.R` mà G6 sinh từ SAP.
- Dòng «Trọng số — bảng tầng sau gộp» LỆCH ⇒ dừng, báo thống kê viên. Đây là hai bản của cùng một thuật toán.
- `chay` từ chối khi `N_tang_HIS.csv` đổi sau `cu-phap`.

Đo thật 14/11/2026 (SPSS 31.0.1 · R 4.6.2 · dữ liệu GIẢ 420 phiếu, 10 bàn khám, mô phỏng C1a):
- OR theo ngưỡng 12/12 khớp. Cronbach α khớp tới 15 chữ số. Bảng tầng hai bản trùng nhau (16 tầng, đều kích hoạt).
- Tỷ lệ có trọng số và svyolr của SPSS khớp R (trọng số cố định) tới từng chữ số, cả KTC. Với R `postStratify`, ước
  lượng trùng, SE khác (đúng dự đoán).
- GENLINMIXED so với clmm: «lệch nhỏ» khoảng 1 % SE.
- Brant (Wald) và Test of Parallel Lines (LR) là hai kiểm định khác nhau — chỉ so kết luận ở ngưỡng 0,05.

Bẫy SPSS đã gặp khi xây khối này:
- GENLINMIXED chỉ ra bảng qua OMS khi có `SET MDISPLAY=TABLES`.
- GENLINMIXED coi biến số mức NOMINAL là YẾU TỐ, nên cú pháp tạm đặt biến dự báo dạng số về SCALE như Python.
- Kết cục nhị phân cần `REFERENCE=<mã thấp>` để mô hình hoá P(mã cao) như glmer.
- Tên biến SPSS KHÔNG phân biệt hoa/thường: `ebm_Nh` và `ebm_nh` là MỘT biến. Lỗi này từng làm mọi trọng số = 1; nay có
  chốt test.
- Bảng Complex Samples dùng t (bậc tự do = số cụm − 1), còn R dùng z. Bộ đọc dựng lại KTC/p từ SE để so cùng thang.
- DEFF: SPSS trùng R `deff=TRUE`; 04a dùng `deff="replace"` (n hiệu dụng cho KTC Wilson) — báo cả hai, không so.

### Cú pháp xem trước ở G6

`run_g6_auto.py` ghi `scripts/05_spss_phan_tich.sps` (và `05b_spss_bo_sung.sps` nếu có khối bổ sung) cạnh script R:
- Cùng đặc tả với script R: tên biến thật, kết cục/phơi nhiễm theo SAP, OR mỗi k phút theo SAP §4.
- Dựng từ từ điển G5, TRƯỚC khi có dữ liệu. Sau khi khoá dữ liệu: `xuat-sav` → `cu-phap` sinh lại bản khớp dữ liệu.
- Bộ chấm G6 chỉ đọc `.R/.py`: tệp .sps không vào dấu vân tay G6-HUMAN-01 và không đổi trạng thái cổng.
- Lỗi khi sinh .sps không làm hỏng việc sinh script R.
- Checkpoint G6 ghi thêm `trong_so` (tham số SAP §4) và `spss_cu_phap`.

## Đối chiếu SPSS ↔ Python — đọc thế nào

Ngưỡng khớp: ước lượng lệch ≤ 0,2 % SE, cận KTC ≤ 1 % SE — OR/HR so trên THANG LOG (β), cộng nửa đơn vị làm tròn
của Python (OR/HR 3 chữ số lẻ, β 4 chữ số); p ±0,005 (hai bên < 0,001 coi là khớp). p hai bên khác phía 0,05 thì
không bao giờ «khớp». Bản đầu so ±0,5 % trên thang OR — OR 1,030 so 1,035 thành «khớp» dù β lệch 16 %.

Chốt trước khi so (thiếu/không khớp ⇒ dừng): SHA-256 nguồn của `.sav` = `data_lock.sha256` của Python; kết quả SPSS
thuộc ĐÚNG tệp `.sav` hiện tại; đặc tả SPSS đã chạy = `dac_ta_phan_tich` của Python. Mục Python có mà SPSS thiếu (hoặc
Python báo lỗi/bỏ qua) vẫn ra dòng «⚪ không so được» kèm lý do — không bỏ dòng im lặng; có cụm mà SPSS thiếu GENLIN thì
KHÔNG lùi về so với mô hình không hiệu chỉnh cụm.

- **✓ khớp**: có thể ghi ở phần phương pháp «kết quả được tái lập độc lập bằng IBM SPSS Statistics <phiên bản>».
- **⚠ lệch nhỏ**: khác phương pháp đã biết, ước lượng điểm lệch ≤ 10 % SE:
  - hiệu chỉnh cụm — SPSS GENLIN (GEE độc lập, SE robust) so với Python (sandwich theo cụm có hiệu chỉnh mẫu nhỏ, phân
    phối t); số cụm ít thì KTC của Python rộng hơn rõ;
  - Cox — SPSS xử lý thời điểm trùng bằng Breslow, lifelines bằng Efron;
  - hồi quy thứ tự — statsmodels lấy SE từ Hessian xấp xỉ (KTC lệch ~0,3 %).
  Thống kê viên chọn cách báo cáo theo SAP.
- **✗ LỆCH**: tìm nguyên nhân (mã hoá biến, tập ca phân tích, nhóm tham chiếu) trước khi dùng số. Không sửa Python cho
  khớp SPSS hay ngược lại.

Đo lại sau bản vá (14/11/2026, cùng dữ liệu giả): nhị phân, liên tục, Cox ✓ khớp; thứ tự và cụm ⚠ lệch nhỏ đúng dự
đoán (cụm: một biến được gắn cờ «p khác phía 0,05» — Python có hiệu chỉnh mẫu nhỏ không có ý nghĩa, GEE của SPSS có).
Thiết kế chính C1a trên từ điển thật + 300 phiếu GIẢ (g1 thứ tự ~ thời gian chờ mỗi 15 phút + hiệp biến, cụm bàn khám):
OR 1,164 trùng hai bên, KTC lệch nhỏ do cách hiệu chỉnh cụm.

Đo thật 14/11/2026 (SPSS 31.0.1, Mac, dữ liệu giả 240 ca, phía Python gọi đúng hàm của `run_stats_analysis.py`):
logistic, tuyến tính, OR thô, t-test khớp tới 6 chữ số; thứ tự khớp; cụm «lệch nhỏ» đúng như dự đoán; Cox khớp sau khi
cú pháp SPSS lọc đúng tập ca — phép đối chiếu phát hiện HR «thô» của Python được tính trên tập ca đầy đủ hiệp biến của
mô hình hiệu chỉnh (228 ca), không phải toàn bộ 240 ca.

Biến phân loại dạng chữ: SPSS mã hoá khác Python (Indicator so với patsy) nên những hệ số đó hiện «⚪ không so được».

## Chạy nền an toàn

- Lượt chạy tự động làm việc trong VÙNG TẠM có đường dẫn ngắn (`/tmp/ebm-spss-…` hoặc thư mục tạm của Windows) rồi chép
  kết quả về `exports/`: đo 14/11/2026, SPSS báo «Serious error» khi đường dẫn tệp dài quá ~255 byte (đường OneDrive +
  worktree dễ vượt). Tệp `.sps` lưu trong `exports/` vẫn ghi đường dẫn thật để mở và chạy tay.
- `chay` chạy cú pháp SINH LẠI từ đặc tả + `.sav` hiện tại và đòi nó trùng tệp `<mã>_phan_tich.sps`; sửa tay ⇒ từ chối
  (muốn chạy bản sửa tay thì mở trong SPSS). Lượt `chay` mới xoá kết quả/đối chiếu cũ trước — lượt hỏng không để lại
  kết quả lượt trước cho `doi-chieu` đọc nhầm.
- Đầu ra SPSS ghi vào tệp tạm, không qua ống dẫn (lỗi nghiêm trọng của SPSS từng làm lệnh chờ hết 20 phút); quá hạn
  hoặc trình nền đã thoát ⇒ dừng cả nhóm tiến trình (lõi SPSS mồ côi giữ tệp và có thể giữ giấy phép).
- Dòng cú pháp gói ≤ ~200 byte (SPSS lỗi «syntax is incomplete» khi một dòng > ~1024 byte); chú thích luôn kết thúc
  bằng dấu chấm (chú thích thiếu dấu chấm nuốt lệnh kế tiếp).
- `nhap-sav`: quét tên/nhãn nghi PII TRƯỚC khi ghi bất kỳ tệp dữ liệu nào; từ chối thư mục ra nằm trong BẤT KỲ repo git
  nào (so không phân biệt hoa/thường); mã thiếu dạng khoảng ghi «LO THRU -1».

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
