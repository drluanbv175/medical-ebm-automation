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

## CHECKPOINT [2026-10-18] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — PI thu hồi G10 theo tranh biện DP-G10-1; CHỜ sửa bộ lắp → gỡ chuyenkhoa → lắp lại → đánh giá chéo T1/T2 → ký lại G10
- cong_vua_qua:   G4
- ngay:           2026-10-18
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: tranh biện hội đồng G10 DP-G10-1 (biên bản G10-TB-20261018T074752-4af4efab, kết quả «sửa kết luận»); PI ghi quyết định G10 REJECTED a2bbd160c13e942a lúc 08:48:37 giờ Việt Nam (01:48:37Z), thu hồi bản ghi APPROVED f1da22ceaef38692 — ledger_approved(G10) = False; đo lại chấm sống: G0 PASS_G0_CONFIRMED · G1 PASS_G1_CONFIRMED · G2 READY_FOR_IRB_SUBMISSION · G3 PASS_G3_CONFIRMED · G4 PASS_G4_SAP_LOCKED (khớp mốc nền của biên bản); A12 §3b bổ sung 3 DOI ngưỡng CFA (Crossref không có thông báo rút, Retraction Watch không có bản ghi). Bước (1)–(3) của khối CHECKPOINT 2026-10-18 «CHỜ khoá lại và ký lại G10» phía trên KHÔNG còn đúng thứ tự — làm theo khối này
- danh_muc_🔴_con_lai: PR y khoa #168 sửa bộ lắp G10 (phiên bản SAP lấy từ chấm sống G4; mục 8 in biến định trước) chưa gộp (người: bác sĩ); `chuyenkhoa` còn trong study_meta.json variables/confounders (người: PI hoặc người quản lý dữ liệu); owner_ref của G10_RELEASE_READINESS.json ghi họ tên và các cờ release xác nhận 2026-10-15, trước bản sửa 2026-10-18 (người: PI); G2 chờ quyết định Hội đồng Đạo đức (người: vai IRB); đăng ký OSF (người: PI)
- buoc_ke:        (1) Gộp PR #168 (bác sĩ), Claude kéo cây chính. (2) Gỡ `chuyenkhoa`: PI chạy nháp `~/.ebm-worktrees/_tam/go_chuyenkhoa_study_meta_20261018.py` (chạy khô) rồi thêm `--ghi`. (3) PI quyết owner_ref (mã vai PI-C1A-01) và xác nhận lại các cờ release. (4) PI bấm «Chot G10 C1a» — lắp lại MỘT lần. (5) Claude kiểm tiêu chí mở rộng: 0 lần «chuyenkhoa»; 0 lần «PENDING — CHỜ BÁC SĨ KÝ SAP»; mục 12, ma trận truy xuất, kiểm soát phiên bản ghi SAP 1.3; mục 8 không còn «0 biến»; G10-AUTO-06/10/11 đạt. (6) Đánh giá chéo G10-T1/T2 trên gói đã lắp lại (hỏi bác sĩ trước — tốn agent). (7) PI đọc các đoạn đã sửa 2026-10-18 rồi tự ký lại bằng `approve_gate.py --gate G10 --reviewer-role PI`. Sau đó làm các bước OSF → bản sao nộp → nộp → vai IRB ghi G2 như khối ĐÍNH CHÍNH G10 ngày 2026-10-18
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-18] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — PI ký lại G10 trên gói đã lắp lại theo tranh biện DP-G10-1
- cong_vua_qua:   G10
- ngay:           2026-10-18
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: PI làm đủ các bước của khối CHECKPOINT «PI thu hồi G10» phía trên: gỡ `chuyenkhoa` khỏi study_meta.json (08:48:47 giờ Việt Nam); owner_ref đổi sang mã vai PI-C1A-01 và đặt lại 5 cờ khối phát hành (08:54); bấm «Chot G10 C1a» lắp lại gói (08:55) và xác nhận lại khối phát hành; Claude kiểm tiêu chí mở rộng — đạt (0 «chuyenkhoa», 0 «PENDING — CHỜ BÁC SĨ KÝ SAP», SAP 1.3 ở mục 12/ma trận/kiểm soát phiên bản, mục 8 «68 biến định trước», G10-AUTO-06/09/10/11 đạt); PI ký G10 bản ghi 39ef81cb4586f97a lúc 09:12:23 giờ Việt Nam (02:12:23Z, chữ ký ed1:role) ⇒ chấm sống G10 PASS_G10_RELEASE_PACKAGE_LOCKED, G4 PASS_G4_SAP_LOCKED, G2 READY_FOR_IRB_SUBMISSION. Đánh giá chéo G10-T1/T2 trên gói đã lắp lại (bước 6 của khối trên) KHÔNG chạy — PI chọn ký mà không chạy (hội đồng là tư vấn; ước tính 4–10 agent). Biên bản xử lý: tranh biện G10-XL-20261018T090734-4923619e, G10-T3 G10-XL-20261018T090631-f9c42443
- danh_muc_🔴_con_lai: G2 chờ quyết định Hội đồng Đạo đức (người: vai IRB); đăng ký OSF Registries (người: PI); dựng dự án REDCap theo SOP-DL-01 §4 trước G5 (người: thư ký đề tài + quản trị viên REDCap); hội đồng chuyên gia quyết tách C6/C9 trong pha phát triển (người: hội đồng chuyên gia)
- buoc_ke:        Làm theo các bước (1)–(5) của khối ĐÍNH CHÍNH G10 ngày 2026-10-18: (1) PI đăng ký OSF Registries trước khi nộp; (2) PI tạo BẢN SAO NỘP ngoài exports/ và ngoài cây git rồi điền tay các ô (mã OSF, ngày phiên bản, Bảng 6.3, trang ký, số điện thoại trong Bản thông tin); (3) KHÔNG sửa DE_CUONG_NOP_HOI_DONG .md/.docx trong exports/ (nằm trong bản kê G10 vừa ký); (4) PI nộp hồ sơ cho Hội đồng Đạo đức; (5) khi có quyết định, NGƯỜI VAI IRB tự chạy approve_gate.py --gate G2 --reviewer-role IRB kèm số, ngày, phiên bản theo quyết định. Agent không chạy lệnh ký
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-28] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — lượt sửa theo hội đồng G1: chốt lại câu hỏi, đề cương lõi và cỡ mẫu (G0–G3)
- cong_vua_qua:   G3
- ngay:           2026-10-28
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: theo quyết định của bác sĩ 25/10/2026 ở hội đồng G1 (phương án A): hệ số biến thiên cỡ cụm CV ≈ 0,14 (CV 1,0 giữ làm phân tích độ nhạy) ⇒ DE 1,39, cỡ mẫu tối thiểu 630, giữ N = 1.000 phiếu HỢP LỆ (định nghĩa duy nhất); giả thuyết Mục tiêu 2 H₀/H₁ hai phía; phân tích giới hạn cho người bệnh bỏ về trước khi khám — đề cương nộp, SAP 1.4 và study_meta.json đã cập nhật (bộ sinh/công cụ: PR y khoa #196, #199). PI chốt lại G0 lúc 15:06:57 và G1 lúc 15:08:06 giờ Việt Nam; bấm «Chot G2 C1a» ⇒ G2 READY_FOR_IRB_SUBMISSION; vai thống kê viên chốt lại G3 lúc 15:10:15 ⇒ G3 PASS_G3_CONFIRMED; máy chạy liền run_g2_auto → run_g3_auto → run_g4_auto (độ tươi G2↔G3 hai chiều)
- danh_muc_🔴_con_lai: SAP 1.4 chưa ký (người: thống kê viên); gói G10 lắp ngày 18/10 không còn khớp hồ sơ (người: PI)
- buoc_ke:        Thống kê viên bấm «Chot G4 C1a» rồi ký G4; PI thu hồi gói G10 cũ, bấm «Chot G10 C1a» (ETHICS_SUBMISSION) và ký lại G10
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-28] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — kế hoạch phân tích thống kê phiên bản 1.4 đã khoá (G4)
- cong_vua_qua:   G4
- ngay:           2026-10-28
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: vai thống kê viên bấm «Chot G4 C1a» (xác nhận lúc 17:18:09 giờ Việt Nam) và ký G4 bản ghi 8bcb77a0e012f920 lúc 17:19:33 giờ Việt Nam (10:19:33Z, chữ ký ed1:role, mã TKV-C1A-01) ⇒ G4 PASS_G4_SAP_LOCKED; SAP phiên bản 1.4 (sửa đổi 26/10/2026, trước khi có số liệu)
- danh_muc_🔴_con_lai: gói G10 lắp ngày 18/10 không còn khớp hồ sơ (người: PI)
- buoc_ke:        PI ghi quyết định G10 REJECTED để thu hồi gói 18/10, bấm «Chot G10 C1a» (ETHICS_SUBMISSION) rồi ký lại G10
- agent_ghi:      so-cai-ghi-nho

## CHECKPOINT [2026-10-28] — đề tài/ca: hai-long-benh-nhan-C1a-BVQY175 — gói nộp Hội đồng Đạo đức lắp lại và ký lại sau lượt sửa (G10)
- cong_vua_qua:   G10
- ngay:           2026-10-28
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: PI ghi G10 REJECTED bản ghi 4c164a4094b0b334 lúc 17:49:58 giờ Việt Nam (10:49:58Z) thu hồi gói lắp ngày 18/10; lần lắp lại 17:50 dừng ở bản nháp vì mục 11 còn 2 ô «[CẦN BỔ SUNG]» (bộ lắp coi bộ công cụ G5 đang chờ G2 là đã có dữ liệu) ⇒ PR y khoa #201 sửa bộ lắp (đã gộp, 3a37ac0); PI bấm lại «Chot G10 C1a» (ETHICS_SUBMISSION) và ký G10 bản ghi 929f12c076daa911 lúc 19:19:44 giờ Việt Nam (12:19:44Z, chữ ký ed1:role, mã PI-C1A-01) ⇒ chấm sống G10 PASS_G10_RELEASE_PACKAGE_LOCKED, G4 PASS_G4_SAP_LOCKED, G2 READY_FOR_IRB_SUBMISSION. A12: 35 PMID nằm trong biên nhận rút bài; 17 DOI không có PMID song song đã tra Retraction Watch + Crossref ngày 28/10: không bài nào bị rút. kiem_de_cuong_nop_hoi_dong: ĐẠT; bản .docx khớp .md
- danh_muc_🔴_con_lai: G2 chờ quyết định Hội đồng Đạo đức (người: vai IRB); đăng ký OSF Registries (người: PI); bản sao nộp MỚI từ cặp tệp ký 28/10 và điền tay (người: PI); dựng dự án REDCap theo SOP-DL-01 §4 trước G5 (người: thư ký đề tài + quản trị viên REDCap); chỉ định vai DATA_MANAGER khi ký G5 (người: PI)
- buoc_ke:        (1) PI đăng ký OSF Registries trước khi nộp; (2) PI tạo BẢN SAO NỘP MỚI ngoài exports/ và ngoài cây git từ cặp DE_CUONG_NOP_HOI_DONG đã ký ngày 28/10 (bản sao tạo trước 28/10 đã lỗi thời) rồi điền tay theo GHI_CHU_DE_CUONG_NOP_HOI_DONG §4.1; (3) KHÔNG sửa cặp tệp trong exports/ (nằm trong bản kê G10 vừa ký); (4) PI nộp hồ sơ cho Hội đồng Đạo đức; (5) khi có quyết định, NGƯỜI VAI IRB tự chạy approve_gate.py --gate G2 --reviewer-role IRB kèm số, ngày, phiên bản theo quyết định. Agent không chạy lệnh ký
- agent_ghi:      so-cai-ghi-nho

> **«Cần bác sĩ kiểm chứng.»** Sổ trạng thái hỗ trợ liên tục công việc, không thay quyết định của bác sĩ.
