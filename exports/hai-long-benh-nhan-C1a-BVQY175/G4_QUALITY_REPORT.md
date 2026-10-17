# BÁO CÁO CHẤT LƯỢNG G4 (KHÓA SAP) — hai-long-benh-nhan-C1a-BVQY175

**Trạng thái:** `DRAFT_NEEDS_HUMAN_CONTENT`
**Phiên bản hợp đồng:** G4-2026.1
**Phạm vi khóa ký:** không xác định

## Kiểm tự động (máy kiểm NỘI DUNG SAP)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G4-AUTO-00 | Guardrail liêm chính G4 sạch | PASS | guardrail_passed=True (chấm lại trên artifact hiện tại, không tin cache) |
| G4-AUTO-01 | G4 đã có cỡ mẫu hợp lệ từ G3 (không ở trạng thái BLOCKED) | PASS | g4_status='PENDING — CHỜ BÁC SĨ KÝ SAP' |
| G4-AUTO-02 | design_code nhất quán giữa G1/G3 (cỡ mẫu) và G4 (SAP) | PASS | design_code=cross_sectional khớp giữa G1/G3/G4 |
| G4-AUTO-03 | Số liệu đã ký (§12, N ở §1 và chứng chỉ khoá) đủ và khớp G3_checkpoint.json HIỆN TẠI | PASS | số liệu ký (§12 loại chinh_xac, N ở §1/chứng chỉ) khớp G3_checkpoint.json hiện tại |
| G4-AUTO-04 | §5 phân tích đa biến có nhắc EPV/EPP/pmsampsize/VIF khi áp dụng | PASS | §5 có nhắc EPV/EPP/pmsampsize/VIF |
| G4-AUTO-05 | §6 dữ liệu thiếu đã điền thật (không chỉ còn nhãn mặc định) | PASS | §6 đã điền biến imputation và còn nêu cơ chế dữ liệu thiếu |
| G4-AUTO-06 | §8 đa so sánh đã điền; nếu Bonferroni thì alpha điều chỉnh khớp số học | PASS | §8 đã điền (không dùng Bonferroni hoặc không cần hiệu chỉnh) |
| G4-AUTO-07 | §7 phân tích nhóm nhỏ/chọn mẫu đã điền (chống HARKing) | PASS | §7 đã điền |
| G4-AUTO-08 | §10 phần mềm+seed cụ thể (không phải placeholder bị thay bằng 'OK') | PASS | §10 có tên+phiên bản phần mềm và seed số nguyên cụ thể |
| G4-AUTO-09 | Margin(Δ) cho NI/equivalence có giá trị và có nguồn biện minh | PASS | hypothesis_type=descriptive_precision — không cần margin |
| G4-AUTO-10 | Mục bắt buộc có mặt và không còn ô trống (§1/§2/§4/§5/§9/§10; RCT thêm §13/§14/§15) | PASS | không còn ô trống ở §1/§2/§4/§5/§9/§10 |
| G4-AUTO-11 | Kết cục chính §2 khớp câu hỏi nghiên cứu đã chốt (G0/G1) | PASS | kết cục chính §2 chứa 'G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_Truc' đã chốt ở G0/G1 |
| G4-AUTO-12 | G3 (cỡ mẫu) chấm sống đã chốt PASS_G3_CONFIRMED — không bị chặn | REVIEW | G3 chấm sống=DRAFT_READY_NEEDS_STATISTICIAN_REVIEW — cỡ mẫu chưa được thống kê viên/PI chốt (PASS_G3_CONFIRMED); SAP không được khoá trên N chưa chốt |
| G4-AUTO-13 | Chứng chỉ khoá SAP (PHẦN 5) đã điền đủ và «KQ chính» khớp §2 | PASS | chứng chỉ khoá đã điền, «KQ chính» cùng kết cục với §2 |
| G4-AUTO-14 | N kế hoạch thấp hơn N tối thiểu được nêu thật và có giải trình | PASS | N kế hoạch ≥ N tối thiểu (hoặc chưa chốt N riêng) |
| G4-AUTO-15 | RCT: §4 chứa estimand ICH E9(R1) đã khai ở G1 và quần thể phân tích chính | PASS | thiết kế cross_sectional — estimand bắt buộc (G1-HUMAN-05) chỉ cho RCT |

## Bằng chứng ký người thật
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G4-HUMAN-01 | Sổ cái có phê duyệt G4 hợp lệ đúng vai trò thống kê/PI | REVIEW | chưa có sổ cái phê duyệt (approval_ledger.json) cho đề tài này |
| G4-HUMAN-02 | Mức bảo đảm của khóa ký được nêu đúng (không nói quá) | REVIEW | chưa xác định phạm vi khóa; khóa riêng nhóm thống kê/PI có sẵn=False |
| G4-HUMAN-03 | Người ký G4 khác người ký các cổng khác (chỉ dấu độc lập) | REVIEW | chưa có bản ghi phê duyệt G4 để đối chiếu |
| G4-HUMAN-04 | Bác sĩ/thống kê viên xác nhận đã rà EPV/VIF ở §5 | PASS | gate_params.G4.epv_vif_reviewed=True |
| G4-HUMAN-05 | Bác sĩ/thống kê viên xác nhận cơ chế dữ liệu thiếu ở §6 | PASS | gate_params.G4.missing_data_mechanism_confirmed=True |
| G4-HUMAN-06 | Subgroup/đa so sánh xác nhận TIỀN ĐỊNH trước khi khóa dữ liệu (ngày ISO, ký trước khoá hoặc có amendment) | PASS | subgroup đã xác nhận tiền định, mốc thời gian hợp lý (hoặc chưa có data_lock_date để đối chiếu) |
| G4-HUMAN-07 | reviewed_by_role khớp vai trò bắt buộc của G4 | PASS | gate_params.G4.reviewed_by_role='STATISTICIAN' |
| G4-HUMAN-08 | Xác nhận G4 của thống kê viên/PI gắn đúng nội dung SAP hiện tại (dấu vân tay) | REVIEW | nội dung đã đổi sau khi xác nhận (dấu lúc xác nhận 0c69d8d3e0c7d060 ≠ hiện tại ab7b9d4f59a46729) — chủ nhiệm đọc lại rồi xác nhận lại |

## Việc còn lại
- Chạy python3 tools/g3_quality_gate.py --study <đề tài>, xử lý mục BLOCK/REVIEW của G3 (thống kê viên/PI xác nhận tham số gắn dấu vân tay) rồi chấm lại G4.
- Thống kê viên/PI tự ký: approve_gate.py --gate G4 --reviewer-role METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
- Tạo khóa riêng: setup_gate_approval_key.py --role STATISTICIAN, và để thống kê viên giữ.
- Cân nhắc để thống kê viên (không phải người đã ký G2/G8/G9) ký G4.
- Sau khi đọc lại SAP, ghi gate_params.G4.dau_van_tay_chot="ab7b9d4f59a46729" (dấu nội dung PHẦN 3 hiện tại) cùng reviewed_at dạng ISO-8601; sửa SAP sau đó phải xác nhận lại.

## Nền chuẩn
| Chuẩn | Phạm vi | Nguồn |
|---|---|---|
| ICH E9(R1) — Addendum on Estimands and Sensitivity Analysis | Estimand (5 thuộc tính) khai ở G1 phải có mặt ở §4 SAP RCT (G4-AUTO-15); quần thể phân tích chính khớp chiến lược biến cố xen ngang | https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf |
| Kahan BC et al. The estimands framework: a primer on the ICH E9(R1) addendum. BMJ 2024;384:e076316 (PMID 38262663) | Cách khai estimand và liên hệ với quần thể phân tích/phân tích độ nhạy trong SAP | 38262663 |
| Gamble C et al. Guidelines for the Content of Statistical Analysis Plans in Clinical Trials. JAMA 2017;318(23):2337-43 (PMID 29260229) | Tập mục tối thiểu của SAP — căn cứ cho mục bắt buộc §1/§2/§4/§5/§9/§10 (và §13–§15 với RCT) | 29260229 |
| Moher D et al. CONSORT 2010 explanation and elaboration. BMJ 2010;340:c869 (PMID 20332511) | RCT: không kiểm định ý nghĩa khác biệt đặc điểm nền giữa các nhóm đã ngẫu nhiên hoá — bảng 1 của SAP RCT không có cột p | 20332511 |
| Ogundimu EO et al. J Clin Epidemiol 2016;76:175-82 (PMID 26964707) | Nguồn thật của ngưỡng EPV≥10 cho hồi quy logistic/Cox đa biến | 26964707 |
| van Smeden M et al. BMC Med Res Methodol 2016;16:163 (PMID 27881078) | Quy tắc EPV cố định được hỗ trợ YẾU — nên khai kèm cảnh báo, không coi là ngưỡng tuyệt đối | 27881078 |
| van Buuren S, Groothuis-Oudshoorn K. J Stat Softw 2011;45(3) — mice | Multiple Imputation dưới giả định MAR; phải khai rõ biến đưa vào mô hình imputation | https://www.jstatsoft.org/article/view/v045i03 |
| FDA (2016) / EMA (2005) — hướng dẫn biên non-inferiority — LƯU Ý MÂU THUẪN | FDA chấp nhận M2 = tỷ lệ % của M1; EMA nói rõ định nghĩa biên theo tỷ lệ hiệu ứng hoạt-chất-vs-giả-dược là KHÔNG phù hợp — margin cần biện minh lâm sàng + khung pháp lý cụ thể, không chỉ một con số | https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-choice-non-inferiority-margin_en.pdf |

## Giới hạn phán định
PASS_G4_SAP_LOCKED xác nhận: SAP có đủ mục bắt buộc không còn ô trống (RCT gồm §13–§15), số liệu ký khớp G3_checkpoint.json hiện tại và G3 chấm sống đã chốt, chứng chỉ khoá đã điền, có phê duyệt ledger đúng vai trò thống kê/PI, và thống kê viên/PI đã xác nhận EPV/VIF, cơ chế dữ liệu thiếu, subgroup tiền định — gắn dấu nội dung SAP hiện tại. KHÔNG chứng minh nội dung phương pháp luận ĐÚNG về mặt lâm sàng, và (như G8) HMAC đối xứng nên không chứng minh người ký độc lập với chủ nhiệm đề tài. Cổng chặn thật của G4 vẫn là gate_contract.ledger_approved('G4', ...) mà G5/G6/run_stats_analysis.py gọi.

> Cần bác sĩ kiểm chứng.
