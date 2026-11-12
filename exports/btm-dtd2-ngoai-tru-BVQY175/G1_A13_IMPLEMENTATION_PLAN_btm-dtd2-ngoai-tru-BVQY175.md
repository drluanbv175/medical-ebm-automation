# KẾ HOẠCH TRIỂN KHAI (A13) — btm-dtd2-ngoai-tru-BVQY175
> [DỰ THẢO] Đơn giá, nhân sự và thời lượng thật do chủ nhiệm/đơn vị xác nhận.

## RACI
Vai trò đã khai (`gate_params.G1.team_roles`): Chủ nhiệm đề tài: định hướng khoa học, chốt đề cương và SAP, ký hồ sơ đạo đức, lập khung mẫu và trích hồ sơ trên eHospital, giữ bảng nối mã, chịu trách nhiệm chung. Nhà phương pháp/thống kê: cỡ mẫu (G3), viết và khoá SAP (G4), phân tích (G6). Quản lý dữ liệu: codebook và phiếu thu thập, nhập liệu, kiểm tra chất lượng, khoá cơ sở dữ liệu (G5), lưu trữ tệp đã mã hoá. Người trích lại: trích lại độc lập 10% hồ sơ kiểm chứng. Người đảm nhận các vai ngoài chủ nhiệm do chủ nhiệm phân công (bảng RACI ở A13); một người có thể kiêm nhiều vai, riêng người trích lại phải khác chủ nhiệm.

## GANTT theo cổng
| Chặng | Phụ thuộc | Thời lượng | Mốc nghiệm thu |
|---|---|---|---|
| G0–G1 | Không | theo lịch đã khai | Thiết kế + protocol map |
| G2 | G1 | theo lịch đã khai | IRB/registration — ★ mốc cứng, chữ ký: G2 (IRB) |
| G3–G4 | G1 | theo lịch đã khai | Cỡ mẫu + SAP lock — ★ mốc cứng, chữ ký: G4 (STATISTICIAN/PI) |
| G5 | G2/G4 | theo lịch đã khai | Pilot/SOP/data tools — ★ mốc cứng, chữ ký: G5 (DATA_MANAGER/PI) |
| G6–G10 | Data lock | theo lịch đã khai | Analysis/report/review/closeout — ★ mốc cứng, chữ ký: G8 (INDEPENDENT_PEER_REVIEWER), G9 (PI), G10 (PI) |

Lịch đã khai (`gate_params.G1.study_schema_timeline`): T0 = ngày Hội đồng Đạo đức BVQY175 phê duyệt. Trình tự: chốt G1, cỡ mẫu G3 và codebook (11/2026) → hồ sơ đạo đức G2 và SAP sẵn sàng G4 (09–22/11/2026) → Hội đồng Khoa học, Đạo đức xét duyệt (23/11/2026–18/01/2027) → khoá SAP trước khi trích hồ sơ → cửa sổ dữ liệu khép 31/12/2026 → lập khung mẫu, chọn ngẫu nhiên, chủ nhiệm trích hồ sơ trên eHospital, người thứ hai trích lại mẫu kiểm chứng, khoá dữ liệu G5 (19/01–28/02/2027) → phân tích G6 (01–14/03/2027) → bản thảo G7 (15/03–07/04/2027) → bình duyệt và liêm chính G8–G9 (08–28/04/2027) → nộp Tạp chí Y Dược Thực hành 175 (G10, từ 29/04/2027).

## KINH PHÍ
| Nhóm chi phí | Số lượng | Đơn giá có nguồn | Thành tiền | Trạng thái |
|---|---:|---:|---:|---|
| Lập khung mẫu và trích hồ sơ trên eHospital (chủ nhiệm tự làm) | Theo cỡ mẫu G3 | – | Tự túc | Chủ nhiệm tự túc — lời bác sĩ 28/10/2026: «Kinh phí tôi tự túc»; không lập đơn giá |
| Trích lại mẫu kiểm chứng (người thứ hai) | 10% cỡ mẫu G3 | – | Tự túc | Chủ nhiệm tự túc — lời bác sĩ 28/10/2026: «Kinh phí tôi tự túc»; không lập đơn giá |
| Xử lý, phân tích số liệu và lưu trữ tệp giả danh | Theo SAP (G4) | – | Tự túc | Chủ nhiệm tự túc — lời bác sĩ 28/10/2026: «Kinh phí tôi tự túc»; không lập đơn giá |
| Hồ sơ Hội đồng Khoa học, Đạo đức và công bố (Tạp chí Y Dược Thực hành 175) | 1 bộ hồ sơ, 1 bài báo | – | Tự túc | Chủ nhiệm tự túc — lời bác sĩ 28/10/2026: «Kinh phí tôi tự túc»; không lập đơn giá |

## QUALITY-BY-DESIGN
- Critical-to-quality factors và quality tolerance limits đã khai (`gate_params.G1.critical_to_quality`): (1) Xác định đúng quần thể — mã E11, từ 2 lượt khám, loại trừ theo mã — kiểm bằng sơ đồ chọn; (2) chọn mẫu ngẫu nhiên đúng — khung mẫu ở cấp người bệnh (không lặp), thứ tự ngẫu nhiên có ghi seed, ghi lý do mọi hồ sơ bị loại; (3) độ chính xác của biến kết cục chính XN_DU — người thứ hai trích lại độc lập 10% hồ sơ chọn ngẫu nhiên, ngưỡng chấp nhận đồng thuận từ 95%; (4) phân biệt UACR với nồng độ microalbumin niệu và que nhúng — quy tắc trích liệt kê trước tên xét nghiệm tương ứng trên eHospital; (5) tính eGFR đúng phương trình và đơn vị (creatinin µmol/L hay mg/dL); (6) phiếu và tệp dữ liệu không có trường định danh, bảng nối mã lưu riêng.
- Monitoring và escalation đã khai (`gate_params.G1.monitoring_plan`): Chủ nhiệm rà sổ tiến độ và Risk Register (A13b) sau mỗi mốc cổng; quản lý dữ liệu chạy kiểm tra phạm vi, logic và trùng lặp trên dữ liệu nhập trước khi khoá (G5), ghi nhật ký truy vấn dữ liệu; bản trích lại được so với bản của chủ nhiệm, đo mức đồng thuận ở từng biến chính và giải quyết bất đồng bằng cách mở lại hồ sơ, có biên bản; mọi thay đổi đề cương sau khi Hội đồng duyệt đi qua quy trình sửa đổi và báo Hội đồng trước khi áp dụng.

> Cần bác sĩ kiểm chứng.
