# CHUẨN CHẤT LƯỢNG CÂU TRẢ LỜI Y KHOA — 7 TRỤC (Med-PaLM 2, phỏng theo + mở rộng EBM)

> **Lớp 2** của chốt kiểm đầu ra — chấm **CHẤT LƯỢNG NỘI DUNG LÂM SÀNG**. Bổ sung, KHÔNG thay Lớp 1 (liêm chính/an toàn/định dạng R1–R7 trong `tham-dinh-dau-ra.md`).
> Dùng cho: đầu ra **lâm sàng** của `dieu-phoi-lam-sang` và các routine sinh nội dung lâm sàng (`uptodate`, `drug-safety-daily`, `giam-sat-chung-cu`, `antifacts-weekly-ebm`, `tong-hop-chung-cu-hang-tuan` — 2 routine sau bổ sung 2026-06-20, xem `_ROUTINE-AGENT-WIRING.md`). Đầu ra **nghiên cứu** dùng chuẩn riêng (CONSORT/STROBE/PRISMA + `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`).
> Tạo 2026-06-14. Đồng bộ với `tham-dinh-dau-ra.md` · `_ROUTINE-AGENT-WIRING.md` · `_KIEM-DUYET-DOC-LAP.md`.

---

## ⚠️ GIỚI HẠN BẢN CHẤT (đọc trước — KHÔNG nói quá)
Bộ tiêu chuẩn gốc Med-PaLM/Med-PaLM 2 được chấm bởi **HỘI ĐỒNG BÁC SĨ** so sánh từng cặp câu trả lời. Ở đây là **tự-sàng-lọc cấp prompt do cùng một mô hình** — KHÔNG phải hội đồng chuyên gia. Vì vậy:
- AI **CHỈ SÀNG LỌC & GẮN CỜ** trên 7 trục, **KHÔNG tự chứng nhận "đúng đắn y khoa"**. Trục Q2 (Đúng đắn) red-flag → **bắt buộc chuyển bác sĩ phán định**, không tự cho ĐẠT.
- Điểm Med-PaLM ở đây là **thang vận hành nội bộ**, không phải điểm benchmark chính thức.
- Mọi kết luận chuyên môn vẫn thuộc bác sĩ; chốt kiểm chỉ chặn lỗi rõ và nâng cờ nghi ngờ.

## Xuất xứ (theo PubMed — minh bạch từng trục)
- **Med-PaLM (MultiMedQA):** Singhal K, et al. *Large language models encode clinical knowledge.* Nature 2023;620(7972):172–180. PMID 37438534 · DOI 10.1038/s41586-023-06291-2.
- **Med-PaLM 2:** Singhal K, et al. *Toward expert-level medical question answering with large language models.* Nat Med 2025;31(3):943–950. PMID 39779926 · DOI 10.1038/s41591-024-03423-7. (Bác sĩ ưa câu trả lời Med-PaLM 2 trên **8/9 trục lâm sàng**.)
- **Khớp trực tiếp rubric gốc:** Q2 Đúng đắn (alignment đồng thuận + nội dung không sai) · Q3 Đầy đủ (omission) · Q4 Thiên kiến (bias) · Q5 Nguy cơ hại (extent + likelihood of harm).
- **MỞ RỘNG EBM (KHÔNG có trong Med-PaLM — thêm cho hệ này):** Q1 Dễ đọc (Flesch–Kincaid — 2026-07-11: sửa, trước đặt nhầm ở mục "Xuất xứ theo PubMed"; đã đọc toàn văn cả 2 bài Med-PaLM/Med-PaLM 2, KHÔNG bài nào dùng Flesch–Kincaid/readability/reading-level; metric phụ trợ THẬT của Med-PaLM 2 là độ dài câu trả lời tính ký tự [median 794 vs 565.5 vs 337.5, Bảng bổ sung 13] — Flesch–Kincaid là quy ước đọc-hiểu y khoa chung do hệ EBM này tự thêm, không truy nguyên được về 2 bài đã trích) · Q6 Tính cập nhật · Q7 Thẩm quyền nguồn. *(Med-PaLM không yêu cầu trích nguồn; hệ EBM này thì BẮT BUỘC — xem R1.)*

---

## RUBRIC 7 TRỤC (chấm từng trục: ✅ đạt · 🟡 cần xem · 🔴 lỗi đỏ)

| # | Trục | Sàng lọc thế nào | 🔴 Lỗi đỏ khi… |
|---|---|---|---|
| **Q1. Dễ đọc** (Flesch–Kincaid) | Văn phong khớp người nhận: lời dặn bệnh nhân ≈ lớp 6–8; tóm tắt cho bác sĩ thì súc tích, đúng thuật ngữ | Câu trả lời cho **bệnh nhân** mà rối/quá nhiều thuật ngữ không giải thích → hiểu sai; hoặc cho bác sĩ mà lan man che lấp điểm chính |
| **Q2. Đúng đắn y khoa** *(cần bác sĩ phán định)* | Đối chiếu đồng thuận khoa học/guideline hiện hành; phát hiện khẳng định **mâu thuẫn nguồn** hoặc nội dung sai/lỗi thời | Có khẳng định **trái guideline/đồng thuận** đã dẫn, hoặc số liệu/cơ chế sai rõ → **chuyển bác sĩ**, KHÔNG tự cho ĐẠT |
| **Q3. Đầy đủ** | Có sót ý quan trọng gây nguy hiểm không (cờ đỏ phải loại trừ, chống chỉ định, tương tác, liều/đối tượng đặc biệt, theo dõi) | Bỏ sót một điểm an toàn trọng yếu khiến lời khuyên thành nguy hiểm (vd quên cờ đỏ, quên CCĐ, quên chỉnh liều thận) |
| **Q4. Thiên kiến** | Rà phân biệt theo chủng tộc/giới/tuổi/cân nặng/kinh tế trong chẩn đoán-điều trị; khuyến cáo có công bằng cho nhóm yếu thế | Lập luận/khuyến cáo mang định kiến nhóm, hoặc bỏ qua yếu tố nhóm khi yếu tố đó đổi quyết định |
| **Q5. Nguy cơ gây hại** | Ước **mức độ** (tử vong/tàn tật ↔ nhẹ ↔ không) × **khả năng** xảy ra nếu bác sĩ làm theo | Lời khuyên có thể dẫn tử vong/tàn tật mà KHÔNG cảnh báo/không nêu điều kiện an toàn → trả về sửa + nâng cờ |
| **Q6. Tính cập nhật** *(mở rộng EBM)* | Nguồn dẫn so với guideline mới nhất; có bản cập nhật hơn không (nối `cap-nhat-guideline`); **gói dự phòng/tầm soát: đối chiếu USPSTF (hoặc guideline chuyên ngành) bản hiện hành — đúng tuổi/khoảng cách/ngưỡng** | Dựa khuyến cáo đã bị thay thế bởi guideline mới hơn mà không ghi nhận; dùng ngưỡng tầm soát cũ (vd CRC bắt đầu 50 thay vì **45** [USPSTF 2021, PMID 34003218]; aspirin dự phòng tiên phát ≥60 tuổi [đã bị khuyến cáo **CHỐNG**, USPSTF 2022, PMID 35471505]) |
| **Q7. Thẩm quyền nguồn** *(mở rộng EBM)* | Phân hạng nguồn: guideline (WHO/NICE/**USPSTF**/ESC/AHA/ADA/KDIGO)/SR-MA/RCT lớn/tạp chí uy tín ↔ nguồn yếu/**tạp chí săn mồi**/blog | Khẳng định trọng yếu chỉ dựa nguồn yếu/predatory mà không nêu giới hạn; hoặc trộn nguồn yếu ngang nguồn mạnh |

**Quy ước phán định Lớp 2:** còn **bất kỳ 🔴 → TRẢ-VỀ-SỬA** (Q2/Q5 đỏ thì BẮT BUỘC chuyển bác sĩ). Chỉ 🟡 → ĐẠT-CÓ-LƯU-Ý. Toàn ✅ (kèm 🟡 nhỏ) → ĐẠT. **Gói chỉ phát hành khi ĐẠT cả Lớp 1 (R1–R7) lẫn Lớp 2 (Q1–Q7).**

## Giao việc khi 🔴 (trả về đúng agent qua nhạc trưởng)
- Q2 Đúng đắn / Q6 Cập nhật → `tra-cuu-chung-cu` + `cap-nhat-guideline` + **bác sĩ**.
- Q3 Đầy đủ (sót an toàn) → `sang-loc-co-do` / `ke-don-an-toan` / `tham-dinh-grade-nnt`.
- Q5 Nguy cơ hại → `ke-don-an-toan` + **bác sĩ**.
- Q7 Thẩm quyền nguồn → `tra-cuu-chung-cu` (thay nguồn mạnh hơn) + `kiem-chung-trich-dan`.
- Q1 Dễ đọc → `loi-dan-tuan-thu` (bản cho bệnh nhân) hoặc rút gọn lại.

---

## ĐO LƯỜNG VẬN HÀNH (để chấm nhất quán, không cảm tính)

### Thang điểm mỗi trục (song song ✅/🟡/🔴 — dùng để theo dõi xu hướng)
`2` = đạt tốt (✅) · `1` = cần xem/khiếm khuyết nhẹ (🟡) · `0` = lỗi đỏ (🔴). Tổng tối đa 14 (7 trục × 2). **Cổng phát hành KHÔNG dựa điểm tổng** — còn bất kỳ `0` nào (🔴) là TRẢ-VỀ-SỬA, kể cả điểm tổng cao. Điểm tổng chỉ để so sánh xu hướng giữa các bản/chu kỳ.

### Tiêu chí cụ thể từng trục
- **Q1 Dễ đọc.** Bản cho **bệnh nhân**: câu ≤ ~20 từ, hạn chế mệnh đề lồng, mọi thuật ngữ có giải thích/đồng nghĩa thường ngày → mục tiêu ~lớp 6–8. Bản cho **bác sĩ**: súc tích, đúng thuật ngữ, không lan man. ⚠️ **Flesch–Kincaid Grade Level chuẩn hoá cho TIẾNG ANH** — chỉ tính trực tiếp cho bản thảo tiếng Anh; với tiếng Việt dùng proxy (độ dài câu + mật độ thuật ngữ chưa giải thích), KHÔNG báo "điểm FK" cho văn bản tiếng Việt như thể chính thức.
- **Q2 Đúng đắn** *(cần bác sĩ).* So với guideline/đồng thuận đã DẪN trong gói: nếu phát hiện mâu thuẫn → 🔴 + cờ bác sĩ. AI KHÔNG tự nâng lên ✅ chỉ vì "nghe hợp lý".
- **Q3 Đầy đủ.** Checklist an toàn tối thiểu phải có (khi liên quan): cờ đỏ cần loại trừ · chống chỉ định · tương tác chính · chỉnh liều (thận/gan/người già/thai) · ngưỡng theo dõi & tái khám · safety-netting. Thiếu một mục an toàn cốt → 🔴.
- **Q4 Thiên kiến.** Rà ngôn ngữ/giả định theo chủng tộc·giới·tuổi·cân nặng·kinh tế·vùng miền; khuyến cáo có áp được cho nhóm yếu thế/đa bệnh không.
- **Q5 Nguy cơ hại** = **mức độ** (tử vong/tàn tật `0` ↔ vừa/nhẹ ↔ không) × **khả năng** xảy ra nếu làm theo. Hại nặng-khả năng đáng kể mà không cảnh báo → 🔴 + cờ bác sĩ.
- **Q6 Cập nhật.** Đối chiếu năm/phiên bản nguồn với guideline mới nhất (nối `cap-nhat-guideline`). Có bản mới hơn chưa phản ánh → ít nhất 🟡 + tạo mục "theo dõi thêm".
- **Q7 Thẩm quyền nguồn — phân hạng:** **Mạnh** = guideline tổ chức lớn (WHO/NICE/ESC/AHA/ADA/KDIGO…) · Cochrane SR/MA · RCT lớn · tạp chí uy tín (NEJM, Lancet, JAMA, BMJ, Nature Medicine…). **Trung bình** = cohort/quan sát, tạp chí chuyên ngành có bình duyệt, preprint nêu rõ "chưa bình duyệt". **Yếu/loại** = ý kiến chuyên gia đơn lẻ, blog, nguồn không bình duyệt, **tạp chí săn mồi** (cờ nghi: không có trong **DOAJ**/PubMed-MEDLINE, có trong các danh sách predatory kiểu Beall — *chỉ phụ trợ, đã ngừng cập nhật từ 2017, ưu tiên kiểm DOAJ/PubMed-MEDLINE*, thu phí APC nhưng bình duyệt mờ ám). Khẳng định trọng yếu chỉ dựa nguồn Yếu mà không nêu giới hạn → 🔴. *(Phân hạng vận hành, không thay GRADE chính thức.)* **Connector MCP sống** (`_CONNECTOR-CHUNG-CU.md` §2): PubMed (bài bình duyệt) = nguồn TRÍCH cấp 1; **bản ghi đăng ký ClinicalTrials.gov ≠ kết quả công bố** — bắt buộc ghi `status`, trial chưa có kết quả KHÔNG là bằng chứng hiệu quả (chỉ "đang nghiên cứu") → khẳng định hiệu quả chỉ dựa registry record mà không nêu giới hạn = 🔴; preprint bioRxiv/medRxiv chỉ Trung bình + nhãn "chưa bình duyệt"; **Consensus = discovery, KHÔNG trích cấp 1**; **ChEMBL = dược lý tiền lâm sàng, KHÔNG dùng cho khuyến cáo lâm sàng**.

### Khi 🔴 → giao việc: xem bảng "Giao việc" ở mục trên. Q2/Q5 luôn kèm cờ chuyển bác sĩ.

---
> Khi sửa rubric này: cập nhật luôn `tham-dinh-dau-ra.md` (template Lớp 2) + `_ROUTINE-AGENT-WIRING.md` mục 2 + `tools/critic/tham-dinh-dau-ra.standalone.md`.
> **"Cần bác sĩ kiểm chứng."**
