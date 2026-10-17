# Sổ trạng thái đề tài — hai-long-benh-nhan-C1a-BVQY175

> Sổ riêng của đề tài (G10-T3, schema `.claude/agents/_SO-TRANG-THAI-CHECKPOINT.md`). Mỗi cổng vừa qua = một khối mới ở
> CUỐI; không sửa khối cũ. Ảnh chụp để RESUME — không thay sổ cái phê duyệt (`approval_ledger.json`) hay quyết định của
> bác sĩ. Khối đầu ghi bù ngày 15/10/2026 từ checkpoint đã chấm sống (G0/G1/G3 = PASS…_CONFIRMED).

## CHECKPOINT [2026-10-14] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — câu hỏi nghiên cứu và tính khả thi
- cong_vua_qua:   G0
- ngay:           2026-10-14
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G0_checkpoint.json PASS_G0_CONFIRMED — PI chốt câu hỏi, giả thuyết H0/H1 về thời gian chờ, tổng hợp bằng chứng có bài tạp chí trong nước
- danh_muc_🔴_con_lai: (không)
- buoc_ke:        G1 — thiết kế cắt ngang và đề cương lõi; PI chốt bằng nút «Chot G1 C1a»
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-14] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — thiết kế và đề cương lõi
- cong_vua_qua:   G1
- ngay:           2026-10-14
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G1_checkpoint.json PASS_G1_CONFIRMED — thiết kế cắt ngang, khung đề cương lõi, công cụ đo lường theo COSMIN
- danh_muc_🔴_con_lai: (không)
- buoc_ke:        G3 — cỡ mẫu có hiệu chỉnh gom cụm và bộ biến số
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-14] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — cỡ mẫu và bộ biến số
- cong_vua_qua:   G3
- ngay:           2026-10-14
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G3_checkpoint.json PASS_G3_CONFIRMED — confirmed_n = 1000 (50 bàn khám × 20; tối thiểu 808 sau DE 1,78)
- danh_muc_🔴_con_lai: G2 chưa có quyết định Hội đồng đạo đức (dao-duc-dang-ky đã chuẩn bị hồ sơ READY_FOR_IRB_SUBMISSION); G4 SAP còn ghi N 626 và DE 1,38 — đồng bộ với G3 trước khi ký (thiet-ke-nghien-cuu); G10 gói READY_FOR_G10_PI_RELEASE_APPROVAL chờ PI ký (dieu-phoi-g10)
- buoc_ke:        G2 — PI nộp hồ sơ Hội đồng đạo đức và ghi quyết định bằng approve_gate.py; song song PI ký G10 (mục đích ETHICS_SUBMISSION) sau khi rà gói
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-17] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — kế hoạch phân tích thống kê (SAP) đã khoá
- cong_vua_qua:   G4
- ngay:           2026-10-17
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G4_A5_SAP_FINAL (SAP 1.3) PASS_G4_SAP_LOCKED — ký vai STATISTICIAN 2026-10-17 (mã phê duyệt bf657cdd80b96835; ký lại 48a146b41cfb48e4 cùng băm SAP)
- danh_muc_🔴_con_lai: G10 chữ ký PI ràng buộc bản kê cũ (G4_checkpoint.json làm tươi sau lúc lắp gói) — khoá lại và ký lại G10
- buoc_ke:        G10 — PI bấm lại «Chot G10 C1a», Claude kiểm bản kê khớp, PI ký lại G10
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-17] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — gói nộp Hội đồng Đạo đức (ETHICS_SUBMISSION)
- cong_vua_qua:   G10
- ngay:           2026-10-17
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G10_checkpoint.json — PI ký vai PI 2026-10-17 (mã phê duyệt 2e0b2e7b27f215e0), mục đích ETHICS_SUBMISSION
- danh_muc_🔴_con_lai: G10-AUTO-10 bản kê lệch (G4_checkpoint.json đổi sau lúc lắp gói) — PI khoá lại và ký lại G10; G2 chờ quyết định Hội đồng Đạo đức và đăng ký OSF Registries
- buoc_ke:        PI bấm lại «Chot G10 C1a» → ký lại G10 → nộp gói cho Hội đồng Đạo đức
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-17] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — PI chốt lại câu hỏi nghiên cứu (G0)
- cong_vua_qua:   G0
- ngay:           2026-10-17
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G0_checkpoint.json PASS_G0_CONFIRMED — vai PI chốt lại lúc 2026-10-17T17:00:56+07:00 (study_meta.json gate_params.G0.reviewed_at) sau lượt tìm bổ sung đổi dấu vân tay bằng chứng; đây là căn cứ của G0 PASS hiện tại
- danh_muc_🔴_con_lai: (không — ở G0)
- buoc_ke:        Xem khối G10 cuối sổ (bước kế duy nhất còn lại)
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-17] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — ĐÍNH CHÍNH cỡ mẫu (G3)
- cong_vua_qua:   G3
- ngay:           2026-10-17
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: ĐÍNH CHÍNH khối G3 đề ngày 2026-10-14 (khối cũ giữ nguyên): lần đạt 14/10 dùng DE 1,38 và N tối thiểu 626 (commit 13b02a6); ngày 17/10 G3 chạy lại với CV 1,0 cho DE 1,78 và N tối thiểu 808 (commit f64575c); N xác nhận vẫn là 1000; vai STATISTICIAN chốt lại lúc 2026-10-17T17:04:54+07:00 (gate_params.G3.reviewed_at). Khối 14/10 ghi nhầm số của 17/10, và lời dẫn đầu sổ «ghi bù ngày 15/10» không đúng với khối này. Cùng ngày: hội đồng G3 trả về sửa bộ biến (G3-T2/G3-T3); đã sửa theo biên bản (PR #164) và đang chấm lại
- danh_muc_🔴_con_lai: (không — ở G3; quyết định còn chờ chủ nhiệm của bộ biến ở _quyet-dinh-bo-bien.md §2, phải xong trước khi G5 nạp dữ liệu)
- buoc_ke:        Xem khối G10 cuối sổ (bước kế duy nhất còn lại)
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-17] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — gói nộp Hội đồng Đạo đức khoá lại và ký lại (G10)
- cong_vua_qua:   G10
- ngay:           2026-10-17
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: PI THU HỒI phê duyệt G10 2e0b2e7b27f215e0 bằng bản ghi REJECTED 5f90a588142b112a (2026-10-17T10:25:57Z), khoá lại gói (lắp 17:26) và ký lại bằng bản ghi APPROVED f1da22ceaef38692 (2026-10-17T10:29:02Z), mục đích ETHICS_SUBMISSION; chấm sống bằng ~/.ebm-venv/bin/python: PASS_G10_RELEASE_PACKAGE_LOCKED, G10-AUTO-10 manifest_match=True. Hai khối G4/G10 phía trên ghi «khoá lại và ký lại G10» — việc đó ĐÃ XONG
- danh_muc_🔴_con_lai: G2 ở READY_FOR_IRB_SUBMISSION chờ quyết định Hội đồng Đạo đức (G2-HUMAN-01/02, người: PI); đăng ký OSF Registries trước khi tuyển người tham gia đầu tiên (người: PI)
- buoc_ke:        PI tạo bản sao nộp nằm NGOÀI exports/ và ngoài cây git, điền tay mã OSF, ngày phiên bản, số điện thoại và tổng dự toán trên bản sao đó. Không sửa DE_CUONG_NOP_HOI_DONG .md/.docx trong bản kê G10 (băm 11d2adb3…/b02aa5f3…). Nộp hồ sơ cho Hội đồng Đạo đức; khi có quyết định, PI tự ghi G2 bằng approve_gate.py. Theo đường này không khoá lại hay ký lại G10. ⚠ Sửa tệp trong release_manifest của G10 thì G10-AUTO-10 chặn; chỉ gỡ được bằng một quyết định G10 mới của PI. Đường (b) là lựa chọn của PI, chỉ cho các ô KHÔNG phải thông tin liên lạc (mã OSF, ngày, dự toán): sửa nguồn bản nộp (viet-ban-thao), chấm lại G10, rồi PI khoá lại và tự ghi quyết định G10 mới. Số điện thoại không bao giờ ghi vào tệp trong repo
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-18] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — ĐÍNH CHÍNH vai ký G2 và bước kế (G10)
- cong_vua_qua:   G10
- ngay:           2026-10-18
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: ĐÍNH CHÍNH khối G10 ngày 2026-10-17 (khối cũ giữ nguyên) theo hội đồng G10 chấm lại G10-T3 (biên bản G10-DG-20261018T063450-a3c8bf8b): G2 chỉ nhận vai IRB (tools/gate_contract.py _GATE_REQUIRED_STAKEHOLDERS["G2"] = IRB; G2-HUMAN-01/02 thuộc IRB@G2-T1) — các dòng ghi «người: PI» / «PI tự ghi G2» ở khối G10 17/10 và khối G3 14/10 là SAI vai. Mốc giờ của khối 17/10: thu hồi 17:25:57 và ký lại 17:29:02 giờ Việt Nam (10:25:57Z / 10:29:02Z); lắp gói 17:26 giờ Việt Nam
- danh_muc_🔴_con_lai: G2 ở READY_FOR_IRB_SUBMISSION chờ quyết định Hội đồng Đạo đức (G2-HUMAN-01/02, người: vai IRB); đăng ký OSF Registries (người: PI)
- buoc_ke:        Đường (a) mặc định, theo thứ tự: (1) PI đăng ký OSF Registries TRƯỚC khi nộp (đề cương: bước chuẩn bị dòng 477 và Bảng 6.2 mốc 1 dòng 699; hạn chót tuyệt đối là trước người tham gia đầu tiên, dòng 34). (2) PI tạo BẢN SAO NỘP nằm ngoài exports/ và ngoài cây git, rồi điền tay trên bản sao đó: mã OSF (dòng 34); ngày phiên bản (dòng 35); Bảng 6.3 — số lượng còn trống, đơn giá, thành tiền từng dòng và tổng cộng (dòng 715–730); trang ký — ngày, chữ ký chủ nhiệm, xác nhận + dấu của đơn vị chủ trì (dòng 833–837); số điện thoại của chủ nhiệm và của Hội đồng Y đức trong Bản thông tin (dòng 903–904). (3) KHÔNG sửa DE_CUONG_NOP_HOI_DONG .md/.docx trong exports/ (băm 11d2adb3…/b02aa5f3… trong bản kê G10) — sửa thì G10-AUTO-10 chặn, chỉ gỡ bằng quyết định G10 mới của PI. (4) PI nộp hồ sơ cho Hội đồng Đạo đức. (5) Khi có quyết định, NGƯỜI VAI IRB tự chạy `python3 tools/approve_gate.py --study hai-long-benh-nhan-C1a-BVQY175 --gate G2 --artifact exports/hai-long-benh-nhan-C1a-BVQY175/G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md --reviewer-role IRB` kèm `--g2-approval-number`, `--g2-approval-date`, `--g2-protocol-version`, `--g2-icf-version` theo quyết định (dieu-phoi-g2.md). Bác sĩ kiêm vai thì dùng vai và khoá IRB, không dùng vai PI. Agent không chạy lệnh này. Đường (b) — lựa chọn của PI, chỉ cho ô KHÔNG phải thông tin liên lạc (mã OSF, ngày, dự toán): sửa nguồn bản nộp (viet-ban-thao), chấm lại G10, PI khoá lại và tự ghi quyết định G10 mới. Số điện thoại không bao giờ ghi vào tệp trong repo
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-18] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — sửa đề cương nộp theo hội đồng G10, CHỜ khoá lại và ký lại G10
- cong_vua_qua:   G4
- ngay:           2026-10-18
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: PI chọn sửa cả 5 góp ý của hội đồng G10 cho đề cương nộp (biên bản G10-DG-20261017T192537-eadd7f0a; câu 9 BHYT: PI chọn sửa câu cho khớp biến) — đã sửa DE_CUONG_NOP_HOI_DONG .md và xuất lại .docx (aOR dòng 148; kế hoạch phân tích đã khoá phiên bản 1.3; câu 9 «còn hiệu lực»; DAG D.1 thêm BHYT → hài lòng; ngưỡng CFA dẫn nguồn [45]–[47]); kiem_de_cuong_nop_hoi_dong: ĐẠT. Khối G10 ngày 2026-10-18 phía trên (đường (a), «không khoá lại hay ký lại G10») KHÔNG còn áp dụng
- danh_muc_🔴_con_lai: G10-AUTO-10 bản kê lệch (gói đổi sau lần ký 10:29:02Z) — PI khoá lại và ký lại G10 (người: PI); G2 chờ quyết định Hội đồng Đạo đức (người: vai IRB); đăng ký OSF (người: PI)
- buoc_ke:        (1) PI bấm «Chot G10 C1a» để lắp lại gói. (2) Claude kiểm G10-AUTO-10 manifest_match=True. (3) PI ký lại G10 bằng `approve_gate.py --gate G10 --reviewer-role PI`. (4) Từ đó làm theo các bước (1)–(5) của khối ĐÍNH CHÍNH G10 ngày 2026-10-18 (OSF → bản sao nộp → nộp → người vai IRB ghi G2)
- agent_ghi:      so-cai-ghi-nho

> **«Cần bác sĩ kiểm chứng.»** Sổ trạng thái hỗ trợ liên tục công việc, không thay quyết định của bác sĩ.
