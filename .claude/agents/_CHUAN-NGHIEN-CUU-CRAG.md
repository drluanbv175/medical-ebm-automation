# CHUẨN CHẤT LƯỢNG NGHIÊN CỨU — C-RAG (Corrective Retrieval-Augmented Generation)

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent). Tạo 2026-06-14.
> Bộ tiêu chuẩn đánh giá NĂNG LỰC NGHIÊN CỨU của các agent truy xuất/thẩm định y văn. Bổ trợ cho chuẩn chất lượng câu trả lời lâm sàng (`_CHUAN-CHAT-LUONG-MEDPALM.md`) — hai chuẩn khác trục: Med-PaLM soi *câu trả lời*, C-RAG soi *quá trình truy xuất + đọc nguồn*.
> Áp cho: `tra-cuu-chung-cu`, `tong-quan-y-van`, `tham-dinh-phe-binh`, `thu-thu-tai-lieu`, `kiem-chung-trich-dan`, `trich-xuat-y-van`, `meta-phan-tich`.
> **"Cần bác sĩ kiểm chứng."**

---

## 3 TRỤC C-RAG (mỗi trục: nơi cưỡng chế trong agent + cách test)

### Trục 1 — KHẢ NĂNG TỰ SỬA LỖI (corrective self-RAG)
**Định nghĩa:** khi rút kết luận từ một bài, agent tự chất vấn "tôi có đang hiểu sai context không?" và tự sửa (loại bài lệch, mở rộng truy vấn, nêu mâu thuẫn) TRƯỚC khi kết luận.

| Câu tự chất vấn bắt buộc | Bẫy chống được |
|---|---|
| Bài có khớp **P/I/O** không? | lấy bài lệch dân số/can thiệp/kết cục |
| Kết cục **lâm sàng cứng** hay **surrogate**? | "HDL tăng → giảm tử vong" (sai nhân quả surrogate) |
| "Không khác biệt" = **âm tính thật** hay **non-inferiority/thiếu lực**? | đọc nhầm underpowered thành "vô hiệu" |
| Kết quả là **chính** hay **dưới nhóm/post-hoc**? | thổi phồng dưới nhóm |
| Thiết kế quan sát bị đọc thành **nhân quả**? | overclaim từ cắt ngang/cohort |
| Bài có **bị rút (retracted)** / bị nghiên cứu lớn hơn bác bỏ? | trích bài đã thu hồi |
| Truy xuất nghèo/lệch → **mở rộng truy vấn rồi lọc lại**? | kết luận chắc trên dữ liệu mỏng |

**Cưỡng chế tại:** `tra-cuu-chung-cu` §3 bước 5 (🔄 TỰ SỬA); `tong-quan-y-van` §3 bước 3b (tự sửa độ phủ); `tham-dinh-phe-binh` §3 bước 1b (tự chất vấn context). *(Trước 2026-06-14: hành vi này chỉ "nổi lên" theo năng lực mô hình, chưa được đặc tả bắt buộc.)*

### Trục 2 — ĐỘ PHỦ NGUỒN (Recall ⟂ Precision)
**Định nghĩa:** tìm được ĐỦ bài liên quan (recall) mà không lẫn bài linh tinh (precision). Hai ngữ cảnh khác mục tiêu:

| Ngữ cảnh | Ưu tiên | Agent |
|---|---|---|
| Điểm khám (1 câu hỏi nhanh) | **PRECISION** — đúng PICO, gọn; coverage hạn chế thì gắn PARTIAL | `tra-cuu-chung-cu` |
| Đề tài / SR | **RECALL cao** — ≥2 CSDL · đồng nghĩa/MeSH · snowball · văn liệu xám · **ghi rõ nguồn KHÔNG tra** · đối chiếu bài mốc | `tong-quan-y-van`, `thu-thu-tai-lieu` |

**Cưỡng chế tại:** `tra-cuu-chung-cu` §3 bước 4 (precision-first + bàn giao recall); `tong-quan-y-van` §3 bước 2 (recall-first) + 3b (tự sửa độ phủ vs bài mốc).
**Cách test định lượng:** chọn 1 SR đã biết (tập bài đưa vào = gold) → cho agent tìm → đo **Recall = |tìm được ∩ gold| / |gold|**, **Precision = |tìm được ∩ gold| / |tìm được|**. *(Cần gold-set thật; [CẦN CHẠY ĐỊNH KỲ].)*

### Trục 3 — CHỐNG BỊA TRÍCH DẪN (phantom DOI = 0%)
**Định nghĩa:** **tỷ lệ bài ảo (DOI/PMID không phân giải được) phải = 0%.**

**Cưỡng chế tại:** `tra-cuu-chung-cu` §3 bước 4 (loại nguồn không phân giải) + bước 6 (trích từ trí nhớ → `[CẦN KIỂM CHỨNG]`, KHÔNG vào bảng chính); **cổng cứng `kiem-chung-trich-dan`** (verify từng PMID/DOI, bắt citation washing, retracted); guardrail `tham-dinh-dau-ra` R1.
**Cách test:** lấy mọi PMID/DOI trong đầu ra → phân giải qua PubMed/Crossref → đếm số không tồn tại/sai khớp. Mục tiêu = 0.

---

## BẰNG CHỨNG TEST (2026-06-14 — câu hỏi "niacin + statin → MACE?")
Chạy `tra-cuu-chung-cu` (bẫy surrogate HDL), verify PMID qua PubMed MCP:
- **Trục 1: ĐẠT thực** — bắt bẫy surrogate (HDL≠MACE); bác meta dương tính (PMID 23265337) vì trộn dữ liệu tiền-statin; **tự loại 1 PMID sai** (23432189 = PREDIMED, lại retracted).
- **Trục 3: ĐẠT — 0% ảo** — 5/5 PMID có thật; 4/4 bài trình bày khớp đúng claim (HPS2-THRIVE 25014686 · AIM-HIGH 22085343 · meta 23265337 · SR 30903687); trích từ trí nhớ (AIM-HIGH) được gắn nhãn cần verify (và thực tế đúng).
- **Trục 2: ĐẠT định lượng (2026-06-14)** — test recall/precision với câu hỏi "GLP-1 RA vs giả dược về MACE ở ĐTĐ2", gold = 8 CVOT kinh điển (ELIXA·LEADER·SUSTAIN-6·EXSCEL·Harmony·REWIND·PIONEER 6·AMPLITUDE-O), verify PMID qua PubMed:
  - **Recall = 8/8 = 100%** (`tong-quan-y-van` tìm đủ; còn tìm THÊM SOUL 2025 — CVOT thật ngoài gold).
  - **Precision = 9/9 = 100%** (mọi bài đưa vào là CVOT thật; loại đúng 4 bài nhiễu: STEP béo phì · meta gộp · sub-analysis SGLT2i · báo cáo thận thứ phát LEADER).
  - **Phantom = 0%** (9/9 PMID phân giải thật).
  - *Giới hạn trung thực:* gold là bộ trial NỔI BẬT (PubMed-indexed cao, dễ tìm); agent tự khai PARTIAL (chỉ tra PubMed, chưa Cochrane/Embase/ClinicalTrials.gov) → recall "đầy đủ" cho SR chính thức cần ≥2 CSDL + citation chasing. Test khó hơn cần SR có bài included khó tra.
- **Phát hiện meta đắt giá:** trong test này NGƯỜI ĐÁNH GIÁ (Claude chính) **bịa 2 PMID từ trí nhớ** (Harmony, AMPLITUDE-O — 1 cái là SPRINT), còn AGENT (corrective self-RAG + verify PubMed) **bịa 0**. → minh chứng kỷ luật "verify công cụ > tin trí nhớ" của C-RAG là thật sự cần thiết.
- *Nguồn dữ liệu test: PubMed (E-utilities/MCP).*

## GẮN VÀO KIỂM TOÁN ĐỊNH KỲ
Thêm vào rà nghiên cứu (`_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`) + tự-kiểm tuần: với gói có truy xuất y văn → soi 3 trục C-RAG (tự sửa có chạy? recall đủ/ghi giới hạn? phantom DOI = 0?). *(2026-07-11: đã gắn cross-reference THẬT vào `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` §A dòng A2b — trước đó tiêu đề mục này overclaim, file kia không hề nhắc C-RAG dù grep 0 kết quả.)*

> **"Cần bác sĩ kiểm chứng."**
