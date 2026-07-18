# LỘ TRÌNH HẠ TẦNG — hạng mục CẦN CÔNG CỤ NGOÀI (đặc tả, KHÔNG giả vờ đã đạt)

> Mục đích: tách bạch **việc đã làm THẬT ở tầng file/prompt** với **việc cần hạ tầng ngoài** (vector DB, daemon nền, orchestrator runtime, auto-prompt-optimizer, self-evolution). Mỗi hạng mục dưới đây ghi: **trạng thái hiện tại · điều kiện đạt · rủi ro**. Không hạng mục nào ở đây được coi là "đã đạt" cho đến khi có công cụ ngoài + bác sĩ xác nhận.
> Đồng bộ với `_TU-SUA-CHUA-PROTOCOL.md`, `_KIEM-DUYET-DOC-LAP.md`, `_SO-TRANG-THAI-CHECKPOINT.md`, `README.md` (Luồng tự động hóa). Cập nhật 2026-06-13.

## NGUYÊN TẮC LIÊM CHÍNH
Ở tầng file/prompt, hệ chỉ tạo **KHUNG/QUY ƯỚC/ĐẶC TẢ**. Mọi năng lực cần tiến trình chạy ngoài phiên Claude **KHÔNG** được mô tả như đã hoạt động. Đánh dấu **[CẦN CÔNG CỤ NGOÀI]** ở đúng chỗ; không viết văn bản giả vờ đạt.

## 🧪 CẬP NHẬT 2026-06-13 — LỚP CÔNG CỤ NGOÀI (PROTOTYPE CHẠY ĐƯỢC, CHƯA vận hành dữ liệu thật)
> Đã dựng prototype CHẠY ĐƯỢC ở `tools/` cho 3 hạng mục ưu tiên (A/B/C). Tất cả gắn nhãn
> **[PROTOTYPE — cần cài deps + BS duyệt governance trước khi chạy trên dữ liệu thật]**.
> Đã chạy demo trên **dữ liệu synthetic** trong sandbox (KHÔNG phải dữ liệu thật). KHÔNG thêm agent .md mới.

| HM | Việc | Đường dẫn | Demo synthetic | Điều kiện vận hành thật |
|----|------|-----------|----------------|--------------------------|
| **A** | Critic ngoài phiên (`tham-dinh-dau-ra` tự chứa + protocol gọi subagent) | `tools/critic/` | ✅ spec tự chứa + protocol; **PATCH ĐÃ ÁP vào 2 nhạc trưởng** (BS đồng ý 2026-06-13) | Task tool/subagent của runtime **[CẦN MÔI TRƯỜNG HỖ TRỢ]** (patch chỉ là KHUYẾN NGHỊ có điều kiện, không tự bật runtime) |
| **B** | Bộ nhớ vector + RAG (khử PII → embed → query) | `tools/rag/` | ✅ ingest 3 synthetic / từ chối 1 PII; **backend SEMANTIC NHẸ TF-IDF (sklearn) chạy được** — so hashing: top-1 3/3 cả hai nhưng **margin tách hạng 0.299 vs 0.135 (~2,2×)** | (tùy chọn) cài `sentence-transformers` cho ngữ nghĩa neural đầy đủ + BS duyệt + xác nhận nguồn không-PII |
| **C** | Harness đánh giá rule-based (giữ người duyệt) | `tools/eval/` | ✅ **rubric mở rộng qua nhiều đợt hardening/adversarial (2026-07-09), nay 15 kiểm** (2026-07-12: sửa "11" — chạy thật `run_eval.py` xác nhận 15 kiểm). Demo (chạy lại thật): good_output 15/15 · bad_output 7/15 · good_antibiotic 16/16 · bad_causal_cross_sectional 9/17 | bổ sung gold set ẩn danh + quy trình review thủ công; **auto-optimizer VẪN KHÔNG bật** |
| **D** | Validator schema blackboard (siết 1b) | `tools/blackboard/` | ✅ demo synthetic: 3 ĐẠT · 4 lỗi ĐỎ · 2 cảnh báo (exit 1) | dùng làm lint trước khi nạp sổ cái/hub; **vẫn là QUY ƯỚC file, chưa phải bus cưỡng chế → 1b vẫn MỘT PHẦN (chắc hơn)** |

## ✅ PHẦN "TỰ ĐỘNG THẬT" HIỆN CÓ (đã tồn tại ngoài file — ghi nhận, không phóng đại)
**2026-07-12: sửa lại theo kết quả gọi thật `mcp__scheduled-tasks__list_scheduled_tasks`** — bảng cũ ghi taskId/lịch sai (`tu-kiem-dong-bo-agent`/Thứ Hai không tồn tại; `giam-sat-chung-cu-noi-chung` không có trong lịch sống). TaskId THẬT đang chạy:
| taskId | Lịch | Việc | Giao thức nối |
|---|---|---|---|
| `ebm-tu-kiem-dong-bo` | **hằng tuần** (Chủ Nhật 08:10, cron `10 8 * * 0`) | tự kiểm đồng bộ & tự sửa chữa bộ agent | `_TU-SUA-CHUA-PROTOCOL.md` |
| *(giam-sat-chung-cu)* | **[CẦN XÁC NHẬN TẠI ĐƠN VỊ]** — KHÔNG có trong danh sách lịch sống hiện tại (đã gọi tool kiểm trực tiếp) | giám sát chứng cứ/guideline mới nội tổng quát ngoại trú | `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md` → `cap-nhat-guideline` + `tra-cuu-chung-cu` |
*Giới hạn:* các task này **kích hoạt một phiên Claude theo lịch**; trong phiên đó việc gọi subagent/định tuyến tuân theo đặc tả file. Đây là "tự động theo lịch" THẬT, KHÁC với daemon nền tự vá mã liên tục. Phần còn lại dưới đây vẫn cần công cụ ngoài.

## 1. Bộ nhớ dài hạn vector hoá + RAG — [CẦN CÔNG CỤ NGOÀI] · 🧪 PROTOTYPE FUNCTIONAL HƠN: `tools/rag/` (đã có backend SEMANTIC NHẸ TF-IDF chạy được trên synthetic; CHƯA vận hành dữ liệu thật)
- **Trạng thái hiện tại:** mầm ở skill `clinical-evidence-rag` (RAG trên kho do người dùng kiểm soát) + sổ cái văn bản (`_SO-EBM-MASTER.md`, `EBM_MASTER/`, MEMORY.md). Prototype `tools/rag/` nay **đã vượt khóa-từ bằng backend SEMANTIC NHẸ TF-IDF (sklearn)+cosine** — chạy thật trên synthetic, tách hạng tốt hơn hashing (~2,2× margin). TF-IDF là biểu diễn TỪ VỰNG CÓ TRỌNG SỐ (lexical), **chưa** phải embedding neural — muốn ngữ nghĩa đầy đủ cài `sentence-transformers` (backend đã chừa sẵn, ưu tiên cao nhất).
- **Điều kiện đạt:** vector DB (vd FAISS/Chroma/pgvector) + mô hình embedding + pipeline ingest (chunk→embed→index) + lớp truy vấn; quản trị phiên bản chỉ mục.
- **Rủi ro:** trích dẫn ảo nếu RAG trả đoạn không đúng nguồn → vẫn bắt buộc phân giải PMID/DOI qua `kiem-chung-trich-dan`; rò rỉ PII vào index (phải khử định danh trước khi ingest); chi phí/đồng bộ đa máy.

## 2. Lịch chạy nền THẬT cho `Scheduled/` — MỘT PHẦN ĐÃ CÓ (xem trên), phần mở rộng [CẦN CÔNG CỤ NGOÀI]
- **Trạng thái hiện tại:** 2 scheduled task ở mục ✅ là phần tự động thật. Các routine khác ở `Scheduled/` (uptodate, drug-safety-daily, nckh) mô tả ở README là **đặc tả**; lịch chạy thật của chúng `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`.
- **Điều kiện đạt:** scheduler Cowork hoặc launchd/cron tạo task tương ứng; lưu ý launchd shell **không gọi được subagent** → phải qua phiên Claude-driven.
- **Rủi ro:** chạy nền không người trực có thể phát hành kết luận chưa duyệt → mọi đầu ra vẫn vào hàng "chờ bác sĩ duyệt" (Cổng A/B), không tự áp dụng.

## 3. Auto-prompt-optimizer — [CẦN CÔNG CỤ NGOÀI] (rủi ro liêm chính cao) · 🧪 PROTOTYPE harness CHẤM: `tools/eval/` (chỉ con người xem; **optimizer tự động VẪN TẮT**)
- **Trạng thái hiện tại:** prompt agent chỉnh **thủ công**, có sao lưu `.bak` + đọc lại xác minh. KHÔNG có vòng tối ưu tự động. Harness chấm `tools/eval/` nay **15 kiểm** (2026-07-12: sửa "11", đã lỗi thời sau các đợt hardening/adversarial 2026-07-09). **Vẫn CHỈ để con người xem; auto-prompt-optimizer VẪN TẮT.**
- **Điều kiện đạt:** harness đánh giá (bộ ca/đề tài chuẩn + tiêu chí chấm) + người duyệt mỗi thay đổi; nhật ký thay đổi có thể truy vết.
- **Rủi ro:** tối ưu theo điểm số có thể "học mẹo" làm yếu rào an toàn/liêm chính (vd bỏ disclaimer để gọn) → **bắt buộc người duyệt**; không để tự ghi đè prompt.

## 4. Orchestrator runtime + checkpoint tiến trình + tự nhân bản — [CẦN CÔNG CỤ NGOÀI]
- **Trạng thái hiện tại:** "điều phối" là **cấp prompt** (nhạc trưởng gợi ý chuyển tiếp trong một phiên); checkpoint là **bản ghi văn bản** (`_SO-TRANG-THAI-CHECKPOINT.md`), KHÔNG phải trạng thái tiến trình runtime; không có tự nhân bản tiến trình.
- **Điều kiện đạt:** runtime đa-agent thật (hàng đợi tác vụ, trạng thái bền, gọi song song) + cơ chế checkpoint/restore tiến trình.
- **Rủi ro:** mất đồng bộ giữa trạng thái runtime và sổ cái file; tự nhân bản không kiểm soát → chi phí/độ phức tạp; vẫn phải giữ cổng người duyệt.

## 5. Self-evolution online — [CẦN CÔNG CỤ NGOÀI] (giữ rào `ket-qua-hoc-tap`)
- **Trạng thái hiện tại:** `ket-qua-hoc-tap` chỉ sinh **GIẢ THUYẾT cải tiến**, KHÔNG tự đổi thực hành; không có vòng học online cập nhật hành vi/tham số.
- **Điều kiện đạt:** pipeline thu tín hiệu kết cục (ẩn danh) + thẩm định thống kê + **người duyệt** trước khi đổi bất cứ thực hành/prompt nào.
- **Rủi ro:** vòng phản hồi tự củng cố sai lệch; suy nhân quả từ dữ liệu quan sát; **bất biến:** tín hiệu = giả thuyết, KHÔNG tự đổi thực hành; mọi thay đổi qua bác sĩ.

## 6. Critic THẨM ĐỊNH ĐẦU RA chạy ngữ cảnh TÁCH — 🧪 PROTOTYPE: `tools/critic/`
- **Trạng thái hiện tại:** `tham-dinh-dau-ra` bản tự chứa (`tools/critic/tham-dinh-dau-ra.standalone.md`) + giao thức gọi subagent (`critic-protocol.md`). Chạy được ngay ở **một phiên Claude rời** (ngữ cảnh tách thật); gọi tự động qua Task tool là **[CẦN MÔI TRƯỜNG HỖ TRỢ]**.
- **Giới hạn:** cùng họ mô hình → **giảm mù chung, KHÔNG khử** thiên lệch hệ thống. Patch thêm 1 dòng khuyến nghị vào 2 nhạc trưởng (`tools/critic/PATCH-nhac-truong.md`) — **ĐÃ ÁP 2026-06-13 (BS đồng ý)**, có `.bak`; dòng mới nằm CẠNH khối chặn cứng "KẾT QUẢ THẨM ĐỊNH ĐẦU RA", chỉ là **khuyến nghị có điều kiện [CẦN MÔI TRƯỜNG HỖ TRỢ]**, KHÔNG thay khối chặn cứng, KHÔNG thêm agent (không tính vào bộ đếm agent).
- **Điều kiện đạt:** runtime có subagent/Task tool; hoặc dùng phiên rời thủ công.

> **"Cần bác sĩ kiểm chứng."** Tài liệu này mô tả ĐIỀU KIỆN đạt, KHÔNG tuyên bố đã đạt. Cập nhật trạng thái chỉ khi có công cụ ngoài thật + bác sĩ xác nhận.

