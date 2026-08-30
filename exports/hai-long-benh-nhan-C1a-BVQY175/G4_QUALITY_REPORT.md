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
| G4-AUTO-03 | Số liệu đã ký (§12) khớp G3_checkpoint.json HIỆN TẠI | PASS | số liệu ký ở §12 khớp G3_checkpoint.json hiện tại |
| G4-AUTO-04 | §5 phân tích đa biến có nhắc EPV/EPP/pmsampsize/VIF khi áp dụng | PASS | §5 có nhắc EPV/EPP/pmsampsize/VIF |
| G4-AUTO-05 | §6 dữ liệu thiếu đã điền thật (không chỉ còn nhãn mặc định) | PASS | §6 đã điền biến imputation và còn nêu cơ chế dữ liệu thiếu |
| G4-AUTO-06 | §8 đa so sánh đã điền; nếu Bonferroni thì alpha điều chỉnh khớp số học | PASS | §8 đã điền (không dùng Bonferroni hoặc không cần hiệu chỉnh) |
| G4-AUTO-07 | §7 phân tích nhóm nhỏ/chọn mẫu đã điền (chống HARKing) | PASS | §7 đã điền |
| G4-AUTO-08 | §10 phần mềm+seed cụ thể (không phải placeholder bị thay bằng 'OK') | PASS | §10 có tên+phiên bản phần mềm và seed số nguyên cụ thể |
| G4-AUTO-09 | Margin(Δ) cho NI/equivalence có giá trị và có nguồn biện minh | PASS | hypothesis_type=superiority — không cần margin |
| G4-AUTO-10 | Không còn placeholder '[CẦN' ở mục bắt buộc (§1/§2/§5/§10) | REVIEW | còn placeholder '[CẦN' ở: §5 (Covariates/Phân tích đa biến) |
| G4-AUTO-11 | Kết cục chính §2 khớp câu hỏi nghiên cứu đã chốt (G0/G1) | PASS | kết cục chính §2 chứa 'G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_Truc' đã chốt ở G0/G1 |

## Bằng chứng ký người thật
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G4-HUMAN-01 | Sổ cái có phê duyệt G4 hợp lệ đúng vai trò thống kê/PI | REVIEW | chưa có sổ cái phê duyệt (approval_ledger.json) cho đề tài này |
| G4-HUMAN-02 | Mức bảo đảm của khóa ký được nêu đúng (không nói quá) | REVIEW | chưa xác định phạm vi khóa; khóa riêng nhóm thống kê/PI có sẵn=False |
| G4-HUMAN-03 | Người ký G4 khác người ký các cổng khác (chỉ dấu độc lập) | REVIEW | chưa có bản ghi phê duyệt G4 để đối chiếu |
| G4-HUMAN-04 | Bác sĩ/thống kê viên xác nhận đã rà EPV/VIF ở §5 | REVIEW | gate_params.G4.epv_vif_reviewed=False |
| G4-HUMAN-05 | Bác sĩ/thống kê viên xác nhận cơ chế dữ liệu thiếu ở §6 | REVIEW | gate_params.G4.missing_data_mechanism_confirmed=False |
| G4-HUMAN-06 | Subgroup/đa so sánh xác nhận TIỀN ĐỊNH trước khi khóa dữ liệu | REVIEW | gate_params.G4.subgroup_multiplicity_predefined_confirmed chưa bật |
| G4-HUMAN-07 | reviewed_by_role khớp vai trò bắt buộc của G4 | REVIEW | gate_params.G4.reviewed_by_role='(rỗng)' |

## Việc còn lại
- Điền đủ §1/§2/§5/§10 — approve_gate.py cũng từ chối ký khi còn placeholder ở đây.
- Thống kê viên/PI tự ký: approve_gate.py --gate G4 --reviewer-role METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
- Tạo khóa riêng: setup_gate_approval_key.py --role STATISTICIAN, và để thống kê viên giữ.
- Cân nhắc để thống kê viên (không phải người đã ký G2/G8/G9) ký G4.
- Đặt gate_params.G4.epv_vif_reviewed=true trong study_meta.json sau khi rà §5.
- Đặt gate_params.G4.missing_data_mechanism_confirmed=true sau khi rà §6.
- Đặt gate_params.G4.subgroup_multiplicity_predefined_confirmed=true TRƯỚC khi G5 khóa dữ liệu.
- Đặt gate_params.G4.reviewed_by_role đúng nhóm: METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR.

## Nền chuẩn
| Chuẩn | Phạm vi | Nguồn |
|---|---|---|
| ICH E9(R1) — Addendum on Estimands and Sensitivity Analysis | Khớp quần thể phân tích/estimand giữa đề cương và SAP; kế hoạch xử lý intercurrent events | https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf |
| Ogundimu EO et al. J Clin Epidemiol 2016;76:175-82 (PMID 26964707) | Nguồn thật của ngưỡng EPV≥10 cho hồi quy logistic/Cox đa biến | 26964707 |
| van Smeden M et al. BMC Med Res Methodol 2016;16:163 (PMID 27881078) | Quy tắc EPV cố định được hỗ trợ YẾU — nên khai kèm cảnh báo, không coi là ngưỡng tuyệt đối | 27881078 |
| van Buuren S, Groothuis-Oudshoorn K. J Stat Softw 2011;45(3) — mice | Multiple Imputation dưới giả định MAR; phải khai rõ biến đưa vào mô hình imputation | https://www.jstatsoft.org/article/view/v045i03 |
| FDA (2016) / EMA (2005) — hướng dẫn biên non-inferiority — LƯU Ý MÂU THUẪN | FDA chấp nhận M2 = tỷ lệ % của M1; EMA nói rõ định nghĩa biên theo tỷ lệ hiệu ứng hoạt-chất-vs-giả-dược là KHÔNG phù hợp — margin cần biện minh lâm sàng + khung pháp lý cụ thể, không chỉ một con số | https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-choice-non-inferiority-margin_en.pdf |

## Giới hạn phán định
PASS_G4_SAP_LOCKED xác nhận: SAP không còn placeholder ở mục bắt buộc, số liệu ký khớp G3_checkpoint.json hiện tại, có phê duyệt ledger đúng vai trò thống kê/PI, và bác sĩ đã tự xác nhận EPV/VIF, cơ chế dữ liệu thiếu, subgroup tiền định. KHÔNG chứng minh nội dung phương pháp luận ĐÚNG về mặt lâm sàng, và (như G8) HMAC đối xứng nên không chứng minh người ký độc lập với chủ nhiệm đề tài. Cổng chặn thật của G4 vẫn là gate_contract.ledger_approved('G4', ...) mà G5/G6/run_stats_analysis.py gọi.

> Cần bác sĩ kiểm chứng.
