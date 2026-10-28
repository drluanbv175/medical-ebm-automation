# KẾ HOẠCH TRIỂN KHAI (A13) — hai-long-benh-nhan-C1a-BVQY175
> [DỰ THẢO] Đơn giá, nhân sự và thời lượng thật do chủ nhiệm/đơn vị xác nhận.

## RACI
Vai trò đã khai (`gate_params.G1.team_roles`): Theo đề cương §6.1 (bảng RACI): chủ nhiệm đề tài (A toàn đề tài — định hướng khoa học, duyệt đề cương/SAP/kinh phí, ký hồ sơ đạo đức); thư ký/điều phối (quản lý tài liệu, lịch, sổ tiến độ, Risk Register; quản lý dữ liệu lưu trữ/sao lưu theo §6.5); nhà thống kê/phân tích (R phân tích, A về tính đúng thống kê — cỡ mẫu Whitehead MT2, viết và khoá SAP; khuyến nghị độc lập với người thu thập); điều tra viên phát/thu phiếu (ngoài Khoa C1a); người nhập liệu (nhập đôi 100%, nên khác điều tra viên); giám sát chất lượng QC; tổ mở hòm phiếu 2 người và tổ mã hoá ý kiến mở 2 người + 1 phân xử (đều ngoài khoa; chủ nhiệm không tham gia); hội đồng chuyên gia I-CVI/S-CVI 6–10 người (≥ 2 đại diện người bệnh, ≤ 2 người thuộc C1a); bên thứ ba Phòng CNTT/QLCL trích HIS. Số người cụ thể mỗi vai do chủ nhiệm ấn định theo cỡ mẫu và lưu lượng khám.

## GANTT theo cổng
| Chặng | Phụ thuộc | Thời lượng | Mốc nghiệm thu |
|---|---|---|---|
| G0–G1 | Không | theo lịch đã khai | Thiết kế + protocol map |
| G2 | G1 | theo lịch đã khai | IRB/registration — ★ mốc cứng, chữ ký: G2 (IRB) |
| G3–G4 | G1 | theo lịch đã khai | Cỡ mẫu + SAP lock — ★ mốc cứng, chữ ký: G4 (STATISTICIAN/PI) |
| G5 | G2/G4 | theo lịch đã khai | Pilot/SOP/data tools — ★ mốc cứng, chữ ký: G5 (DATA_MANAGER/PI) |
| G6–G10 | Data lock | theo lịch đã khai | Analysis/report/review/closeout — ★ mốc cứng, chữ ký: G8 (INDEPENDENT_PEER_REVIEWER), G9 (PI), G10 (PI) |

Lịch đã khai (`gate_params.G1.study_schema_timeline`): Theo đề cương §4.9 và §6.2 (mốc T0 = ngày Hội đồng Đạo đức/lãnh đạo BVQY 175 phê duyệt): đăng ký công khai OSF Registries trước T0 → phê duyệt đạo đức (T0, phạm vi gồm cả pha công cụ) → pha phát triển và kiểm định công cụ (bảng truy xuất mục, hội đồng chuyên gia I-CVI/S-CVI, phỏng vấn nhận thức 10–15 người bệnh, pilot n ≈ 50–100 tách khỏi mẫu chính, khoá vFinal) + dry-run chấm F1–F5 → khoá SAP → thu thập mẫu chính n = 1000 (chọn mẫu hệ thống phân tầng ngày × khung giờ; mỗi người đo MỘT lần ngay sau khi hoàn tất lượt khám: sàng lọc → ICF riêng → phiếu tự điền → hòm kín) → ghép thời gian chờ HIS (bên thứ ba) → nhập đôi 100%, làm sạch → khoá dữ liệu → phân tích (chỉ sau khi SAP và dữ liệu đã khoá) → bản thảo STROBE → nghiệm thu. Thời lượng từng pha do chủ nhiệm ấn định theo lịch khoa.

## KINH PHÍ
| Nhóm chi phí | Số lượng | Đơn giá có nguồn | Thành tiền | Trạng thái |
|---|---:|---:|---:|---|
| In phiếu khảo sát phiên bản cuối (kể cả dự phòng) | ≈ 1.300 bản | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| In bản thông tin và phiếu đồng ý tham gia | ≈ 1.300 bản | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Pha phát triển bộ câu hỏi: hội đồng chuyên gia, phỏng vấn nhận thức (10–15 người), khảo sát thử (50–100 người) | 1 đợt | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Thù lao điều tra viên | [CẦN CHỦ NHIỆM ẤN ĐỊNH] công | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Thù lao giám sát chất lượng | [CẦN CHỦ NHIỆM ẤN ĐỊNH] công | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Nhập liệu kép | ≈ 2.000 lượt nhập | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Thù lao nhà thống kê | [CẦN CHỦ NHIỆM ẤN ĐỊNH] công | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Phần mềm thống kê (R – miễn phí) | – | 0 | 0 | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Văn phòng phẩm, hòm phiếu, vật tư | Theo nhu cầu | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Phí công bố bài báo (nếu có) | 1 bài | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |
| Dự phòng | – | – | [CẦN] | Dự thảo — nguồn tự túc (đề cương §6.3, Bảng 6.3) |

## QUALITY-BY-DESIGN
- Critical-to-quality factors và quality tolerance limits đã khai (`gate_params.G1.critical_to_quality`): Theo đề cương §4.4.2, §4.7, §4.8 và §6.5: (1) chọn mẫu hệ thống phân tầng đúng bước k_h — giới hạn chấp nhận F1 ≥ 80%; (2) tỷ lệ đồng ý ≥ 60% (F2), có sổ nhật ký từ chối để báo cáo tỷ lệ đáp ứng; (3) ghép thời gian chờ HIS ≥ 90% phiếu (F3); (4) công cụ rõ nghĩa (F4 trung vị ≤ 20 phút; F5 < 3 mục hiểu sai ≥ 20%); (5) kiểm soát thiên kiến chiều lòng — tự điền ẩn danh, hòm kín, điều tra viên ngoài khoa, đo ngoài buồng khám, cấm trả lời thay; (6) có `ma_ban_kham` giả danh từ phiếu đầu tiên (xử lý gom cụm); (7) nhập đôi 100% với luật range/logic; (8) không PII trong hệ thống dữ liệu của nhóm nghiên cứu; (9) không phân tích trước khi khoá SAP và dữ liệu.
- Monitoring và escalation đã khai (`gate_params.G1.monitoring_plan`): Theo đề cương §4.9 bước 11, §6.1, §6.4, §6.5: giám sát chất lượng (QC, nên độc lập với điều tra viên) kiểm tra ngẫu nhiên phiếu/nhập liệu, tuân thủ chọn mẫu và đối chiếu tỷ lệ đáp ứng; thư ký/điều phối theo dõi mốc và tổng hợp Risk Register (R1–R9), rà lại sau mỗi mốc; hòm phiếu do tổ hai người mở có biên bản; audit trail và nhật ký truy vấn dữ liệu sau khoá; nhật ký huỷ bảng ghép HIS; chủ nhiệm chịu trách nhiệm cuối (A). Không có DSMB vì không can thiệp.

> Cần bác sĩ kiểm chứng.
