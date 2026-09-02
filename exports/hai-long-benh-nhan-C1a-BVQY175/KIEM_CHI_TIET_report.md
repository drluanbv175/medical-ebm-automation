# Kiểm chi tiết hệ nghiên cứu — hai-long-benh-nhan-C1a-BVQY175

Sinh lúc 2026-09-02T07:20:40. Chỉ ĐO và BÁO. 🟡 là việc của người thật, không phải lỗi. Cần bác sĩ kiểm chứng.

| Cổng | ① Tự động | ② Chuẩn | ③ Tài liệu | ④ Trình bày | ⑤ Điểm dừng người |
|---|---|---|---|---|---|
| G0 | 🟢 | 🟢 | 🟡 | 🟢 | · |
| G1 | 🟡 | 🟡 | 🟡 | 🟢 | · |
| G2 | 🟡 | 🟡 | 🟡 | 🟢 | 🟡 |
| G3 | 🟡 | 🟡 | 🟡 | 🟢 | · |
| G4 | 🟡 | 🟡 | 🟡 | 🟢 | 🟡 |
| G5 | 🟡 | 🟡 | 🟡 | · | 🟡 |
| G6 | 🟡 | 🟡 | 🟡 | 🟢 | · |
| G7 | 🟡 | 🟡 | 🟡 | · | · |
| G8 | 🟡 | 🟡 | 🟡 | · | 🟡 |
| G9 | 🟡 | 🟡 | 🟡 | 🟢 | 🟡 |
| G10 | 🟡 | 🟡 | 🟡 | 🟢 | 🟡 |

**Tổng:** 🟢 42 · 🟡 39 · 🔴 0 · ⚪ 0 — mã thoát 1

## Chi tiết

| Cổng | Trục | Màu | Mục | Bằng chứng | Hành động |
|---|---|---|---|---|---|
| G0 | ① | 🟢 | Checkpoint có, guardrail PASS | G0_checkpoint.json |  |
| G0 | ② | 🟢 | Hợp đồng chất lượng G0 | PASS_G0_CONFIRMED (chấm sống); tự động FAIL 0 · REVIEW 0 · người 0 treo |  |
| G0 | ③ | 🟢 | G0_A1_PICO_FINER_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 24 |  |
| G0 | ③ | 🟡 | Còn 24 nhãn [CẦN…] trong 1 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G0 | ④ | 🟢 | G0_A1_PICO_FINER_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt | 0 ký tự trang trí |  |
| G1 | ① | 🟢 | Checkpoint có, guardrail PASS | G1_checkpoint.json |  |
| G1 | ① | 🟡 | Độ tươi (theo mtime): CŨ hơn thượng nguồn | G1 sinh TRƯỚC thượng nguồn G0 (> 120s) → cần chạy lại để đồng bộ dữ liệu mới nhất — nội dung có khớp hay không xem trục ② (chấm sống) | chạy lại theo chuỗi khi thượng nguồn đã ổn (run_pipeline.py --from …) |
| G1 | ② | 🟡 | Hợp đồng chất lượng G1 | DRAFT_READY_NEEDS_HUMAN_REVIEW (bản đã lưu — chấm lại = chạy run_g1_auto); tự động FAIL 0 · REVIEW 0 · người 5 treo | người thật điền study_meta.json → gate_params.G1: G1-HUMAN-01, G1-HUMAN-03, G1-HUMAN-06, G1-HUMAN-07, G1-HUMAN-08 |
| G1 | ② | 🟢 | Chuẩn báo cáo STROBE được đề cương gọi tên | thiết kế cross_sectional |  |
| G1 | ③ | 🟢 | G1_A2_PROTOCOL_DESIGN_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 89 |  |
| G1 | ③ | 🟢 | G1_A1b_PROJECT_CHARTER_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 2 |  |
| G1 | ③ | 🟢 | G1_A2b_EVIDENCE_LEDGER_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 62 |  |
| G1 | ③ | 🟢 | G1_A13_IMPLEMENTATION_PLAN_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 19 |  |
| G1 | ③ | 🟢 | G1_A13b_RISK_REGISTER_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 6 |  |
| G1 | ③ | 🟡 | Còn 178 nhãn [CẦN…] trong 5 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G1 | ④ | 🟢 | G1_A13_IMPLEMENTATION_PLAN_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G1 | ④ | 🟢 | G1_A13b_RISK_REGISTER_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G1 | ④ | 🟢 | G1_A1b_PROJECT_CHARTER_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G1 | ④ | 🟢 | G1_A2_PROTOCOL_DESIGN_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G1 | ④ | 🟢 | G1_A2b_EVIDENCE_LEDGER_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G2 | ① | 🟢 | Checkpoint có, guardrail PASS | G2_checkpoint.json |  |
| G2 | ① | 🟡 | Độ tươi (theo mtime): CŨ hơn thượng nguồn | G2 sinh TRƯỚC thượng nguồn G0 (> 120s) → cần chạy lại để đồng bộ dữ liệu mới nhất — nội dung có khớp hay không xem trục ② (chấm sống) | chạy lại theo chuỗi khi thượng nguồn đã ổn (run_pipeline.py --from …) |
| G2 | ② | 🟡 | Hợp đồng chất lượng G2 | DRAFT_NEEDS_HUMAN_COMPLETION (chấm sống); tự động FAIL 0 · REVIEW 3 · người 2 treo | người thật điền study_meta.json → gate_params.G2: G2-AUTO-02, G2-AUTO-05, G2-AUTO-08, G2-HUMAN-01, G2-HUMAN-02 |
| G2 | ③ | 🟢 | G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 49 |  |
| G2 | ③ | 🟡 | Còn 49 nhãn [CẦN…] trong 1 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G2 | ④ | 🟢 | G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G2 | ⑤ | 🟡 | Sổ cái: chưa ký | chưa có sổ cái phê duyệt (approval_ledger.json) cho đề tài này | IRB / IRB_ETHICS_COMMITTEE / ETHICS_COMMITTEE — tools/trinh_ky_cong.py hoặc approve_gate.py --gate G2 |
| G3 | ① | 🟢 | Checkpoint có, guardrail PASS | G3_checkpoint.json |  |
| G3 | ① | 🟡 | Độ tươi (theo mtime): CŨ hơn thượng nguồn | G3 sinh TRƯỚC thượng nguồn G0, G1 (> 120s) → cần chạy lại để đồng bộ dữ liệu mới nhất — nội dung có khớp hay không xem trục ② (chấm sống) | chạy lại theo chuỗi khi thượng nguồn đã ổn (run_pipeline.py --from …) |
| G3 | ② | 🟡 | Hợp đồng chất lượng G3 | DRAFT_READY_NEEDS_STATISTICIAN_REVIEW (chấm sống); tự động FAIL 0 · REVIEW 0 · người 6 treo | người thật điền study_meta.json → gate_params.G3: G3-HUMAN-01, G3-HUMAN-02, G3-HUMAN-03, G3-HUMAN-04, G3-HUMAN-05, G3-HUMAN-06 |
| G3 | ③ | 🟢 | G3_A4_SAMPLE_SIZE_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 5 |  |
| G3 | ③ | 🟡 | Còn 5 nhãn [CẦN…] trong 1 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G3 | ④ | 🟢 | G3_A4_SAMPLE_SIZE_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G4 | ① | 🟢 | Checkpoint có, guardrail PASS | G4_checkpoint.json |  |
| G4 | ① | 🟡 | Độ tươi (theo mtime): CŨ hơn thượng nguồn | G4 sinh TRƯỚC thượng nguồn G3 (> 120s) → cần chạy lại để đồng bộ dữ liệu mới nhất — nội dung có khớp hay không xem trục ② (chấm sống) | chạy lại theo chuỗi khi thượng nguồn đã ổn (run_pipeline.py --from …) |
| G4 | ② | 🟡 | Hợp đồng chất lượng G4 | DRAFT_NEEDS_HUMAN_CONTENT (chấm sống); tự động FAIL 0 · REVIEW 1 · người 7 treo | người thật điền study_meta.json → gate_params.G4: G4-AUTO-10, G4-HUMAN-01, G4-HUMAN-02, G4-HUMAN-03, G4-HUMAN-04, G4-HUMAN-05 |
| G4 | ③ | 🟢 | G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 3 |  |
| G4 | ③ | 🟡 | Còn 3 nhãn [CẦN…] trong 1 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G4 | ④ | 🟢 | G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G4 | ⑤ | 🟡 | Sổ cái: chưa ký | chưa có sổ cái phê duyệt (approval_ledger.json) cho đề tài này | METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR — tools/trinh_ky_cong.py hoặc approve_gate.py --gate G4 |
| G5 | ① | 🟡 | Cổng chưa chạy | chờ ký thật cổng G4 (METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR) — approve_gate.py --gate G4 |  |
| G5 | ② | 🟡 | Hợp đồng chất lượng | chưa tới lượt |  |
| G5 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | data_management, redcap_dictionary, g5_quality_report | chưa tới lượt |
| G5 | ⑤ | 🟡 | Chưa có artifact để ký | chưa tới lượt |  |
| G6 | ① | 🟡 | Cổng chưa chạy | chờ ký thật cổng G5 (DATA_MANAGER / DATA_GOVERNANCE_QA_REVIEWER / DATA_STEWARD HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR) — approve_gate.py --gate G5 |  |
| G6 | ② | 🟡 | Hợp đồng chất lượng | chưa tới lượt |  |
| G6 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | analysis_scripts | chưa tới lượt |
| G6 | ④ | 🟢 | G6a_ANALYSIS_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt | 0 ký tự trang trí |  |
| G6 | ④ | 🟢 | G6b_INTERPRETATION_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt | 0 ký tự trang trí |  |
| G6 | ④ | 🟢 | G6d_CLINICAL-GUIDELINE_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt | 0 ký tự trang trí |  |
| G7 | ① | 🟡 | Cổng chưa chạy | chờ G6 chạy trước → chờ ký thật cổng G5 (DATA_MANAGER / DATA_GOVERNANCE_QA_REVIEWER / DATA_STEWARD HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR) — approve_gate.py --gate G5 |  |
| G7 | ② | 🟡 | Hợp đồng chất lượng | chưa tới lượt |  |
| G7 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | manuscript | chưa tới lượt |
| G8 | ① | 🟡 | Cổng chưa chạy | chờ G7 chạy trước → chờ G6 chạy trước → chờ ký thật cổng G5 (DATA_MANAGER / DATA_GOVERNANCE_QA_REVIEWER / DATA_STEWARD HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR) — approve_gate.py --gate G5 |  |
| G8 | ② | 🟡 | Hợp đồng chất lượng | chưa tới lượt |  |
| G8 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | presubmission | chưa tới lượt |
| G8 | ⑤ | 🟡 | Chưa có artifact để ký | chưa tới lượt |  |
| G9 | ① | 🟡 | Cổng chưa chạy | chờ G7 chạy trước → chờ G6 chạy trước → chờ ký thật cổng G5 (DATA_MANAGER / DATA_GOVERNANCE_QA_REVIEWER / DATA_STEWARD HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR) — approve_gate.py --gate G5 |  |
| G9 | ② | 🟡 | Hợp đồng chất lượng | chưa tới lượt |  |
| G9 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | author_integrity, publication_readiness, quality_report | chưa tới lượt |
| G9 | ④ | 🟢 | G9_READINESS_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G9 | ⑤ | 🟡 | Chưa có artifact để ký | chưa tới lượt |  |
| G10 | ① | 🟡 | Checkpoint BLOCKED = từ chối fail-closed ĐÚNG | Trích dẫn (cổng A12) chưa chạy agent `kiem-chung-trich-dan` (thiếu artifact A12). → pytho… · chờ ký thật cổng G8 (PHAN_BIEN / PEER_REVIEWER / EXTERNAL_REVIEWER) — approve_gate.py --gate G8 |  |
| G10 | ① | 🟡 | Độ tươi (theo mtime): MỒ CÔI (thượng nguồn thiếu) | G10 có checkpoint nhưng thượng nguồn còn THIẾU: G5, G6, G7, G8, G9 — nội dung có khớp hay không xem trục ② (chấm sống) | chạy lại theo chuỗi khi thượng nguồn đã ổn (run_pipeline.py --from …) |
| G10 | ② | 🟡 | Hợp đồng chất lượng | cổng đang BLOCKED — chưa có gì để chấm |  |
| G10 | ③ | 🟡 | Artifact BẮT BUỘC thiếu | quality_report | chưa tới lượt |
| G10 | ③ | 🟢 | DE_CUONG_THONG_NHAT_hai-long-benh-nhan-C1a-BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 66 |  |
| G10 | ③ | 🟢 | Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 4 |  |
| G10 | ③ | 🟢 | De-cuong_Hai-long-C1a_BVQY175.md: 5 luật liêm chính sạch | [CẦN còn 4 |  |
| G10 | ③ | 🟡 | Còn 74 nhãn [CẦN…] trong 3 file | thẩm quyền chủ nhiệm/thống kê viên | điền rồi chạy lại quality gate của cổng |
| G10 | ④ | 🟢 | Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.docx: Times New Roman 13pt | 0 ký tự trang trí |  |
| G10 | ④ | 🟢 | DE_CUONG_THONG_NHAT_hai-long-benh-nhan-C1a-BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G10 | ④ | 🟢 | De-cuong_Hai-long-C1a_BVQY175.docx: Times New Roman 13pt/bảng 11pt | 0 ký tự trang trí |  |
| G10 | ⑤ | 🟡 | Sổ cái: chưa ký | chưa có sổ cái phê duyệt (approval_ledger.json) cho đề tài này | PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR — tools/trinh_ky_cong.py hoặc approve_gate.py --gate G10 |
| HỆ | S | 🟢 | 11/11 script cổng + approve_gate + gate_contract biên dịch | 13/13 biên dịch sạch |  |
| HỆ | S | 🟢 | 11/11 gN_quality_gate.py có mặt + có CLI main() | 11/11 |  |
| HỆ | S | 🟢 | approve_gate gọi quality gate của 6 cổng cứng TRƯỚC khi ghi sổ cái | G2·G4·G5·G8·G9·G10 đều nối |  |
| HỆ | S | 🟢 | Không bộ sinh .docx nào gán font qua p.style; 11 điểm doc.save đi qua chuan_trinh_bay | 11/11 nối, 0 vi phạm p.style |  |
| HỆ | S | 🟢 | G5/G6/G10 tự tra sổ cái thượng nguồn (fail-closed tĩnh) | 3/3 tham chiếu ledger_approved |  |
| HỆ | S | 🟢 | gen_research_docx.ARTIFACT_MAP ≥ 32 bộ sinh | 38 khoá |  |
| HỆ | S | 🟢 | Canary: lỗi gài biết trước bị bắt + approve_gate từ chối đúng (G2/G4/G8) | gài 9/9 bắt được · dây nối 3/3 |  |
