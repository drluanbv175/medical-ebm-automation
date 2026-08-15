# MẪU "NHẬT KÝ & KHAI BÁO DÙNG AI" CHO NGHIÊN CỨU

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent). Tạo 2026-06-14.
> Dùng khi sản phẩm nghiên cứu/công bố có dùng AI (kể cả hệ agent EBM này). Hai phần: **(I) NHẬT KÝ vận hành** (ghi liên tục trong quá trình làm) + **(II) KHAI BÁO** (đoạn văn dán vào bản thảo/hồ sơ IRB/đề cương).
> Liên quan cổng **G9 / artifact A14**; agent soạn DỰ THẢO, **chủ nhiệm đề tài XÁC NHẬN** (`_HIEN-PHAP` §2, `dieu-phoi-nghien-cuu` G9). Đồng bộ `HUONG-DAN-VAN-HANH.md` §6.
> Chuẩn tham chiếu: **ICMJE** (AI không là tác giả; tác giả chịu trách nhiệm toàn bộ nội dung), **TT 43/2024/TT-BYT**, quy định riêng từng tạp chí → `[CẦN XÁC NHẬN — quy định tạp chí đích]`.
> **"Cần bác sĩ kiểm chứng."**

---

## NGUYÊN TẮC KHAI BÁO (đọc trước khi điền)
1. **AI KHÔNG là tác giả.** Không ghi AI vào danh sách tác giả; tác giả con người **chịu trách nhiệm toàn bộ** nội dung kể cả phần có AI hỗ trợ.
2. **Minh bạch có chừng mực.** Khai rõ công cụ · phiên bản · mục đích dùng · phạm vi · ai kiểm chứng. Không cường điệu ("AI tự viết bài") cũng không giấu.
3. **Mọi đầu ra AI đều được người kiểm chứng.** Số liệu/trích dẫn do AI gợi ý phải đối chiếu nguồn gốc (PMID/DOI) trước khi đưa vào.
4. **Tách rạch ròi** phần AI hỗ trợ **soạn/diễn đạt** với phần AI đụng **dữ liệu/phân tích** (mức khai báo khác nhau, tạp chí quan tâm phần sau hơn).

---

## PHẦN I — NHẬT KÝ VẬN HÀNH (ghi liên tục, lưu trong hồ sơ đề tài)

> Bảng append-only. Mỗi lần dùng AI cho một việc cụ thể → thêm 1 dòng. KHÔNG xóa dòng cũ.

| # | Ngày | Công cụ + model/phiên bản | Agent/skill | Việc cụ thể | Đầu vào (đã khử PII?) | Đầu ra | Người kiểm chứng | Cổng/Artifact |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-__-__ | Claude (Opus 4.x) | `cau-hoi-nghien-cuu` | dựng câu hỏi PICO/PECO + FINER | vấn đề lâm sàng thô (không PII) ✅ | câu hỏi PICO đã chuẩn hoá | BS Luân | A1/G0 |
| 2 | | | | | | | | |
| 3 | | | | | | | | |

> **2026-07-11: sửa dòng ví dụ #1** — bản cũ gán mã "A1/G0" cho `thu-thu-tai-lieu`/việc "dựng chiến lược tìm + danh mục TLTK", nhưng theo bản đồ A1–A18 canonical (`dieu-phoi-nghien-cuu.md`), A1 = PICO/FINER do `cau-hoi-nghien-cuu` phụ trách; `thu-thu-tai-lieu` không sở hữu mã A-code nào trong bảng canonical (việc tìm TLTK gần artifact A2b "Evidence Ledger", do `tong-quan-y-van`+`trich-xuat-y-van` phụ trách). Ví dụ sai có thể khiến người dùng khác sao chép cách gắn mã sai vào nhật ký thật.

**Quy ước cột:**
- **Đầu vào (đã khử PII?):** xác nhận dữ liệu đưa vào KHÔNG chứa PII (theo `_QUAN-TRI-DU-LIEU-PII.md`); nếu là dữ liệu nghiên cứu thật → ghi rõ đã qua G2 + khử định danh.
- **Người kiểm chứng:** người chịu trách nhiệm rà đầu ra AI (đối chiếu nguồn, kiểm số liệu). Không bỏ trống.
- **Cổng/Artifact:** ánh xạ G0–G9 / A1–A18 để truy vết.

### Bảng tổng hợp mức độ dùng AI theo phần bản thảo (điền trước khi nộp)

| Phần bản thảo | Có dùng AI? | Mục đích | Mức can thiệp | AI có đụng dữ liệu thật? |
|---|---|---|---|---|
| Tổng quan/Tài liệu | ☐ Có ☐ Không | tìm/tóm tắt y văn | hỗ trợ soạn | Không |
| Phương pháp | ☐ Có ☐ Không | | | |
| Phân tích dữ liệu | ☐ Có ☐ Không | | | ☐ Có ☐ Không *(nếu Có → mô tả rõ ở khai báo)* |
| Viết/diễn đạt | ☐ Có ☐ Không | hiệu đính ngôn ngữ | sửa văn phong | Không |
| Trích dẫn/TLTK | ☐ Có ☐ Không | dựng/kiểm danh mục | đã verify PMID/DOI | Không |
| Hình/bảng | ☐ Có ☐ Không | | | |

---

## PHẦN II — ĐOẠN KHAI BÁO (dán vào bản thảo / hồ sơ)

> Chọn mẫu phù hợp, điền chỗ `[...]`, **chủ nhiệm rà & xác nhận** trước khi nộp. Đối chiếu yêu cầu cụ thể của tạp chí đích → `[CẦN XÁC NHẬN]`.

### Mẫu A — AI chỉ hỗ trợ ngôn ngữ/tìm tài liệu (mức nhẹ, phổ biến)

> *"Trong quá trình chuẩn bị bản thảo này, nhóm tác giả có sử dụng công cụ trí tuệ nhân tạo [tên công cụ + phiên bản, vd Claude Opus 4.x] để hỗ trợ [tìm kiếm tài liệu / hiệu đính ngôn ngữ / định dạng trích dẫn]. Công cụ AI KHÔNG được dùng để tạo ra dữ liệu, kết quả hay diễn giải khoa học. Toàn bộ nội dung đã được các tác giả kiểm tra, hiệu chỉnh và chịu trách nhiệm hoàn toàn. AI không được liệt kê là tác giả theo khuyến nghị ICMJE."*

### Mẫu B — AI hỗ trợ xử lý/phân tích dữ liệu (mức cần khai chi tiết)

> *"Nhóm nghiên cứu sử dụng [tên công cụ + phiên bản] cho [mô tả CỤ THỂ: vd hỗ trợ viết mã phân tích / kiểm tra logic dữ liệu]. Dữ liệu đưa vào công cụ đã được [khử định danh / xử lý trên bản sao] theo [căn cứ pháp lý: Luật 91/2025/QH15; phê duyệt đạo đức số ___]. Mọi kết quả do công cụ tạo ra đều được [tên người] kiểm chứng độc lập đối chiếu với [nguồn]. Các tác giả chịu trách nhiệm về tính chính xác và toàn vẹn của toàn bộ phân tích."*

### Mẫu C — Khai báo trong hồ sơ đạo đức (IRB) — về xử lý dữ liệu bằng AI

> *"Nghiên cứu có sử dụng công cụ AI [tên] cho [mục đích]. Cam kết: (1) không đưa dữ liệu định danh người bệnh (PII) vào công cụ AI khi chưa có căn cứ pháp lý + phê duyệt + biện pháp bảo vệ; (2) dữ liệu xử lý là bản đã khử định danh, làm trên bản sao, có nhật ký; (3) tuân Luật BVDLCN 91/2025/QH15 + NĐ 356/2025/NĐ-CP và TT 43/2024/TT-BYT; (4) mọi đầu ra AI được nghiên cứu viên kiểm chứng. [CẦN XÁC NHẬN TẠI ĐƠN VỊ: quy định nội bộ về AI/đám mây]."*

---

## CHECKLIST TRƯỚC KHI NỘP (G9 / A14)
- [ ] Nhật ký Phần I đầy đủ; mọi dòng có **người kiểm chứng**.
- [ ] Bảng mức độ dùng AI theo phần đã điền; cột "AI đụng dữ liệu thật" đúng sự thật.
- [ ] Chọn đúng mẫu khai báo (A/B/C); điền hết `[...]`.
- [ ] Mọi số liệu/trích dẫn do AI gợi ý đã verify qua `kiem-chung-trich-dan` (PMID/DOI thật).
- [ ] Đối chiếu **yêu cầu khai báo AI của tạp chí đích** → `[CẦN XÁC NHẬN]`.
- [ ] AI **không** nằm trong danh sách tác giả; đóng góp tác giả (ICMJE) đã rà.
- [ ] COI + tài trợ đã khai (cùng A14).
- [ ] **Chủ nhiệm đề tài XÁC NHẬN** toàn bộ khai báo (cổng G9 — agent chỉ soạn dự thảo).

> Soạn dự thảo: `nop-bai-phan-hoi` + `binh-duyet`. Xác nhận cuối: **chủ nhiệm đề tài**.
> **"Cần bác sĩ kiểm chứng."**
