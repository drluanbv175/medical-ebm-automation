# THƯ VIỆN KỸ NĂNG & PLAYBOOK — bản đồ skill ↔ agent ↔ tình huống (tham chiếu dùng chung)

> Mục đích: tra nhanh **dùng skill nào / agent nào** cho một tình huống, và vài **playbook** cho tình huống nội khoa hay gặp. KHÔNG lặp nội dung lâm sàng/nghiên cứu (đã ở từng agent/skill) — chỉ TRỎ tới đúng nơi.
> Đồng bộ với `README.md` (ma trận định tuyến), `_BAN-DO-KET-NOI.md` (mạng kết nối), 2 nhạc trưởng. Cập nhật 2026-06-13.
> *Lưu ý:* tên skill dưới đây là **skill đã cài** trong môi trường (kho `skills/`). Nếu một skill chưa cài/không khả dụng → agent vẫn tự làm theo đặc tả của mình; đánh dấu `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` nếu phụ thuộc skill chưa chắc có.

## 1. BẢNG skill ↔ agent ↔ khi dùng (lâm sàng)
| Tình huống | Skill (kho `skills/`) | Agent vào cửa |
|---|---|---|
| Tiếp cận 1 triệu chứng → cờ đỏ/chuyển tuyến | `tiep-can-chan-doan-co-do-chuyen-tuyen` | `sang-loc-co-do` → `dieu-phoi-lam-sang` |
| Khám 1 ca ngoại trú trọn 5 bước EBM | `kham-ngoai-tru-ebm` | `dieu-phoi-lam-sang` |
| Thẩm định nhanh 1 bài để quyết đổi thực hành | `tham-dinh-chung-cu-grade-nnt` | `tham-dinh-grade-nnt` |
| Rà đơn/kê đơn an toàn bệnh mạn | `ke-don-an-toan-benh-man` | `ke-don-an-toan` |
| Người cao tuổi đa bệnh – đa thuốc | `nguoi-cao-tuoi-da-benh-da-thuoc` | `ke-don-an-toan` (+`quyet-dinh-chung`) |
| Giao tiếp/quyết định cùng BN, ghi SOAP | `giao-tiep-quyet-dinh-soap` | `quyet-dinh-chung` |
| Lời dặn & nhắc tái khám (A5) | `ehospital-mini`, `tuan-thu-dieu-tri` | `loi-dan-tuan-thu` |
| Cập nhật chứng cứ 1 vấn đề + Web Dashboard | `cap-nhat-chung-cu-y-khoa` (Evidence Workbench, nền sáng) · `dark-analyst` (CÙNG schema `DATA`, nền tối — khi bác sĩ yêu cầu) | `huong-dan-lam-sang` / `cap-nhat-guideline` |
| Tra cứu có trích dẫn (RAG kho y văn) | `clinical-evidence-rag`, `paper-lookup` | `tra-cuu-chung-cu` |
| Quản lý kho cập nhật đã lưu (sổ cái) + nền tảng EBM hợp nhất | `quan-ly-cap-nhat-ebm`, `dashboard-master-ebm-ngoai-tru`, `ebm-master` (nền tảng EBM hợp nhất: lâm sàng·nghiên cứu·thống kê·giám sát guideline·an toàn thuốc·kháng sinh·thang điểm·dashboard) | `so-cai-ghi-nho` |

## 2. BẢNG skill ↔ agent ↔ khi dùng (nghiên cứu)
| Tình huống | Skill | Agent vào cửa |
|---|---|---|
| Câu hỏi/đề cương/protocol/cổng G0–G9 | `nghien-cuu-y-khoa-chuan-quoc-te`, `nghien-cuu-ebm-tong-hop` | `dieu-phoi-nghien-cuu` |
| Tìm bài / dựng danh mục TLTK | `paper-lookup`, `research-lookup` | `thu-thu-tai-lieu` |
| Tổng quan hệ thống PRISMA | `literature-review` | `tong-quan-y-van` |
| Kiểm chứng trích dẫn (PMID/DOI) | `citation-management` | `kiem-chung-trich-dan` |
| Tính cỡ mẫu / phân tích thống kê | `statistical-analysis` | `co-mau-nghien-cuu` / `phan-tich-thong-ke` |
| Viết IMRAD theo chuẩn báo cáo | `scientific-writing` | `viet-ban-thao` |
| Bình duyệt trước nộp | `peer-review` | `binh-duyet` |
| Sản phẩm đào tạo/slide/Word/PDF | `dao-tao-slide-tai-lieu-y-khoa`, `pptx`/`docx`/`pdf`/`xlsx` | (đầu ra) — gọi sau khi nội dung đã chốt |

## 3. PLAYBOOK tình huống nội khoa hay gặp (chỉ TRỎ — không lặp nội dung lâm sàng)
> Mỗi playbook = chuỗi agent gợi ý; nhạc trưởng tự chạy theo Giao thức tự động, dừng ở cổng. Nội dung lâm sàng cụ thể nằm trong agent/skill, KHÔNG ở đây.

- **PB1 — Đa bệnh đồng mắc + đa thuốc (ĐTĐ2 + CKD + THA…):** `dieu-phoi-lam-sang` → `sang-loc-co-do` (cờ đỏ) → `pico-lam-sang` → `tra-cuu-chung-cu` → `tham-dinh-grade-nnt` → `ke-don-an-toan` (chỉnh liều theo eGFR, tương tác) → `quyet-dinh-chung` → `tham-dinh-dau-ra` → Cổng A.
- **PB2 — Câu hỏi CHẨN ĐOÁN (có nên làm xét nghiệm / khả năng bệnh X):** `dieu-phoi-lam-sang` → `sang-loc-co-do` → `pico-lam-sang` → rẽ nhánh `chan-doan-xac-suat` (pretest→LR→hậu nghiệm→ngưỡng test–treat) → `tham-dinh-dau-ra` → Cổng A.
- **PB3 — "Khuyến cáo này còn đúng không / có cập nhật gì":** `cap-nhat-guideline` / `huong-dan-lam-sang` (GRADE EtD) → (tùy chọn) skill `cap-nhat-chung-cu-y-khoa` dựng dashboard → `tham-dinh-dau-ra` → Cổng B (EBM_MASTER hàng chờ duyệt).
- **PB4 — Người cao tuổi nghi tác dụng phụ/giảm thuốc (deprescribing):** `dieu-phoi-lam-sang` → `ke-don-an-toan` (Beers/STOPP-START, gánh nặng kháng cholinergic) → `quyet-dinh-chung` → `loi-dan-tuan-thu` → `tham-dinh-dau-ra` → Cổng A.
- **PB5 — Khởi động một đề tài từ ý tưởng:** `dieu-phoi-nghien-cuu` (RESUME từ sổ trạng thái) → G0 `cau-hoi-nghien-cuu` → `khoang-trong-nghien-cuu` → `thu-thu-tai-lieu` → completeness-critic → `tham-dinh-dau-ra` → DỪNG xin xác nhận PICO.

> **"Cần bác sĩ kiểm chứng."** Thư viện này HỖ TRỢ tra cứu định tuyến, không thay phán đoán của bác sĩ.
