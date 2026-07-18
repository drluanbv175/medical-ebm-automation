# SỔ TRẠNG THÁI — CHECKPOINT "KHÔI PHỤC NHANH" (quy ước dùng chung)

> Mục đích: chuẩn hóa khối **"KHÔI PHỤC NHANH"** thành một **bản ghi checkpoint cố định** ghi SAU MỖI CỔNG (G_/A/B) để phiên sau (và máy khác qua sync) RESUME đúng chỗ, không làm lại.
> Đồng bộ với `_SO-EBM-MASTER.md` (schema bản ghi), `so-cai-ghi-nho.md` (agent ghi sổ cái), `dieu-phoi-lam-sang.md` + `dieu-phoi-nghien-cuu.md` (BƯỚC 0 RESUME), `_TU-SUA-CHUA-PROTOCOL.md`. Append-only, backup `.bak` trước khi ghi. Cập nhật 2026-06-13.

## ⚠️ GIỚI HẠN BẢN CHẤT
Đây là **bản ghi trạng thái dạng văn bản** để mô hình đọc lại khi khởi động phiên — KHÔNG phải checkpoint tiến trình runtime, KHÔNG tự khôi phục nếu không có phiên Claude đọc nó. "Khôi phục" = nhạc trưởng đọc bản ghi gần nhất ở BƯỚC 0 rồi tiếp tục. Checkpoint tiến trình thật của orchestrator → `_LO-TRINH-HA-TANG.md` **[CẦN CÔNG CỤ NGOÀI]**.

**Vá 2026-07-04 (audit "trưởng thành thật" — A2/S2):** dù đây là bản ghi văn bản, TÍNH
HỢP LỆ của bản ghi (đúng schema · không ghi Cổng A/B khi còn 🔴 · Cổng A trước Cổng B ·
không PII) NAY có máy kiểm THẬT — `medical-ebm-automation/tools/clinical_checkpoint.py`
(không phải chỉ LLM tự chấm ✅/🟡/🔴 bằng lời văn ở completeness-critic C1–C9 nữa):
```bash
python medical-ebm-automation/tools/clinical_checkpoint.py <file_so_trang_thai>.md --json
```
Kiểm: schema đủ trường · `cong_vua_qua` hợp lệ (G0-G99/A/B) · ngày đúng định dạng ·
**Cổng A/B không được ghi PASS khi `danh_muc_🔴_con_lai` còn liệt kê mục** (bản dịch máy
kiểm của quy tắc "CẤM kết luận đủ khi còn 🔴") · Cổng B không đứng trước Cổng A cùng ca ·
không PII. Trả `verdict: ĐẠT/TRẢ-VỀ-SỬA` + danh sách vi phạm cụ thể (dòng nào, ca nào).

## SCHEMA BẢN GHI CHECKPOINT (ghi 1 khối sau MỖI cổng)
> **2026-07-12: đổi kiểu ngoặc placeholder từ `[...]` sang `«...»`** — khối ví dụ dưới đây trước dùng `[YYYY-MM-DD]` giống hệt cú pháp `_HEADER_RE` của `clinical_checkpoint.py` (`## CHECKPOINT [...] — đề tài/ca: ...`), khiến công cụ hiểu nhầm CHÍNH KHỐI VÍ DỤ này là một checkpoint thật rồi chấm các placeholder là giá trị sai (`INVALID_GATE_TOKEN`/`INVALID_DATE`/`INVALID_TASK_TYPE`) → chạy đúng lệnh khuyến nghị bên dưới trên CHÍNH file này sẽ luôn báo `TRẢ-VỀ-SỬA` giả dù không có checkpoint thật nào sai. Đổi ngoặc để khối ví dụ không khớp regex nữa (đã tự kiểm: `«...»` không khớp `_HEADER_RE`, các khối CHECKPOINT thật dùng `[...]` bên dưới KHÔNG bị ảnh hưởng).
```
## CHECKPOINT «YYYY-MM-DD» — đề tài/ca: «mã hoặc mô tả ngắn, KHÔNG PII»
- cong_vua_qua:   «G0..G9 | A | B»      (cổng/bước vừa PASS — đề tài NGHIÊN CỨU ghi THEO TRỤC AGENT: Đạo đức=G2 · SAP=G4 · Phân tích=G6; xem _CROSSWALK-NGHIEN-CUU.md §1)
- ngay:           «YYYY-MM-DD»
- loai_nhiem_vu:  «lâm sàng | nghiên cứu»
- san_pham_vua_xong: «1 dòng: artifact/quyết định vừa hoàn tất»
- danh_muc_🔴_con_lai: «liệt kê mục 🔴 bắt buộc còn thiếu + agent phụ trách; "(không)" nếu sạch»
- buoc_ke:        «cổng/bước kế tiếp + CHÍNH XÁC cần bác sĩ cấp gì để đi tiếp»
- agent_ghi:      «so-cai-ghi-nho | nhạc trưởng»
- guardrail_dau_ra: «ĐẠT | TRẢ-VỀ-SỬA — BẮT BUỘC khi cong_vua_qua=A hoặc B, tùy chọn cho G0-G9»
```
Quy ước: mỗi cổng = 1 khối mới ở CUỐI; KHÔNG sửa khối cũ. Bản ghi này là "ảnh chụp" để RESUME, khác bản ghi nội dung chi tiết (đó là việc của `_SO-EBM-MASTER.md`/hub `EBM_MASTER/`).

**2026-07-12 (rà kiến trúc đội agent — vá "guardrail chỉ là quy ước prompt"):** thêm trường
`guardrail_dau_ra` — ghi verdict THẬT của `tham-dinh-dau-ra` (ĐẠT/TRẢ-VỀ-SỬA) ngay trước khi
ghi khối Cổng A/B. `clinical_checkpoint.py` nay CHẶN (mã `GATE_WITHOUT_GUARDRAIL_VERDICT`) mọi
khối Cổng A/B thiếu trường này hoặc chưa ghi ĐẠT — guardrail không còn chỉ là quy ước cấp
prompt cho riêng khối này, mà có máy kiểm thật đối chiếu. Trường KHÔNG bắt buộc cho khối
G0-G9 trung gian (chưa tới lúc trả gói cho bác sĩ).

## CÁCH NỐI VÀO DÂY CHUYỀN
- **Ghi (sau mỗi cổng):** nhạc trưởng giao `so-cai-ghi-nho` ghi 1 khối checkpoint theo schema trên vào sổ trạng thái (file này — 2026-07-12: sửa "hoặc `EBM_MASTER/MEMORY.md` theo CLAUDE.md", file đó KHÔNG tồn tại trên đĩa và CLAUDE.md không hề nhắc tới đường dẫn này; bộ nhớ dài hạn thật là `sync/memory/MEMORY.md`/`memory-sync/MEMORY.md`, khác mục đích với sổ checkpoint) — ngay sau khi một cổng PASS, cùng lúc ghi bản ghi nội dung vào `_SO-EBM-MASTER.md`. **NGAY SAU KHI GHI**, chạy `clinical_checkpoint.py` trên file vừa ghi — còn 🔴 (vd `GATE_WITH_OUTSTANDING_RED_ITEMS`) → SỬA khối vừa ghi trước khi bàn giao, KHÔNG để lại bản ghi hỏng cho phiên sau đọc nhầm.
- **Đọc (BƯỚC 0):** cả `dieu-phoi-lam-sang` (BƯỚC 0 trước cờ đỏ) và `dieu-phoi-nghien-cuu` (BƯỚC 0 khôi phục trạng thái) đọc **khối checkpoint gần nhất** của ca/đề tài → xác định cổng PASS gần nhất → RESUME từ cổng kế; nếu chưa có khối nào → bắt đầu từ đầu (cờ đỏ/G0). **TRƯỚC KHI TIN bản ghi để RESUME** (đặc biệt khi máy khác/phiên khác đã ghi qua OneDrive sync), chạy `clinical_checkpoint.py` — `verdict: TRẢ-VỀ-SỬA` → KHÔNG resume mù theo bản ghi hỏng, nêu rõ cho bác sĩ rồi hỏi lại từ cổng an toàn gần nhất.

## NHẬT KÝ CHECKPOINT (append khối mới ở CUỐI — KHÔNG xóa khối cũ)
<!-- BẮT ĐẦU GHI TỪ DƯỚI DÒNG NÀY -->

## CHECKPOINT [2026-07-06] — đề tài/ca: TEST-RESUME-VALIDATION-20260706 (ĐỀ TÀI GIẢ LẬP - CHỈ ĐỂ KIỂM THỬ HỆ THỐNG, KHÔNG PHẢI NGHIÊN CỨU THẬT)
- cong_vua_qua:   G1
- ngay:           2026-07-06
- loai_nhiem_vu:  nghiên cứu
- san_pham_vua_xong: G0 (PICO giả lập P=bệnh nhân giả lập/I=biện pháp X giả lập/C=chăm sóc chuẩn giả lập/O=kết cục Y giả lập, kết cục chính = thay đổi chỉ số Y giả lập sau 12 tuần) + G1 (thiết kế giả lập = thử nghiệm giả lập nhóm song song 2 nhánh, đề cương khung tối thiểu) đã soạn Ở MỨC TỐI THIỂU chỉ để kiểm thử cơ chế checkpoint/resume — KHÔNG dùng cho quyết định lâm sàng/nghiên cứu thật
- danh_muc_🔴_con_lai: (không)
- buoc_ke:        G2 (Đạo đức & đăng ký) — CHỜ kiểm thử RESUME ở phiên/agent khác; KHÔNG march tiếp trong phiên này theo yêu cầu kiểm thử; nếu là đề tài thật thì bước kế cần bác sĩ cấp: tên Hội đồng Đạo đức + ngày dự kiến nộp hồ sơ
- agent_ghi:      so-cai-ghi-nho

> **"Cần bác sĩ kiểm chứng."** Sổ trạng thái HỖ TRỢ liên tục công việc, không thay quyết định của bác sĩ.
