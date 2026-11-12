# KẾ HOẠCH HOÀN THIỆN ĐỀ TÀI

**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026
**Mã:** `btm-dtd2-ngoai-tru-BVQY175` · **Thiết kế dự kiến:** cắt ngang mô tả có phân tích, hồi cứu hồ sơ (mã `cross_sectional`; loại câu hỏi `descriptive`)
**Tạp chí đích:** Tạp chí Y Dược Thực hành 175 (ISSN 2354-1024, DOI 10.59354)
**Lập ngày:** 26/10/2026 — bản đề xuất của Claude; mốc thời gian là ƯỚC TÍNH, chủ nhiệm chỉnh theo thực tế.

---

## 1. Đang ở đâu (đo bằng `tools/study_readiness.py`, 26/10/2026)

| Mục | Trạng thái thật |
|---|---|
| Vị trí trên lộ trình A | Bước 2 — **Cổng G0** |
| G0 | 🟡 `DRAFT_READY_NEEDS_HUMAN_REVIEW` — PICO và kết cục chính CHƯA được bác sĩ chốt |
| G1 → G10 | Chưa chạy |
| Cổng cứng đã ký (G2 · G4 · G5 · G8 · G9 · G10) | **0/6** — mọi hồ sơ hiện có là DỰ THẢO |
| Trích dẫn | 47 bài, **47/47 có toàn văn** trong nhóm EndNote đề tài (đã loại 19 bài ngày 25/10) |

- **Việc kế tiếp (một việc):** bác sĩ đọc `DE-XUAT-GATE-PARAMS-G0_20261025.json`, sửa theo ý mình rồi ghi vào `study_meta.json → gate_params.G0`. Sau đó chạy `python tools/g0_quality_gate.py --study btm-dtd2-ngoai-tru-BVQY175` để lên `PASS_G0_CONFIRMED`. Vì sao: mọi cổng sau (thiết kế, cỡ mẫu, SAP) đọc PICO đã chốt ở G0; chưa chốt thì G1 bị giữ lại.
- **Cổng ký gần nhất phía trước:** **G2 — Đạo đức.** Hội đồng Đạo đức BVQY175 phê duyệt; sau khi có quyết định, chủ nhiệm ký G2 bằng `approve_gate.py --gate G2`. Không trích dữ liệu bệnh án trước khi G2 được ký.

---

## 2. Thể lệ tạp chí đích — ràng buộc phải bám từ bây giờ

Nguồn: trang «Thể lệ viết bài» và «Tài liệu tham khảo» của tạp chí trên jpmp175.vn (đọc 26/10/2026).

| Yêu cầu | Quy định |
|---|---|
| Độ dài | ≤ 5.000 từ, TÍNH CẢ trang tiêu đề, tóm tắt, tài liệu tham khảo, bảng và chú thích hình (≈ 10 trang A4) |
| Bảng, hình | ≤ 5 bảng kết quả và ≤ 5 hình hoặc biểu đồ |
| Tài liệu tham khảo | **≤ 20**, tiêu biểu và cập nhật, có DOI nếu có |
| Kiểu trích dẫn | Vancouver theo thứ tự xuất hiện, không tách theo ngôn ngữ; ghi 3 tác giả đầu rồi «và cộng sự»/«et al.» |
| Tiêu đề | IN HOA, ≤ 30 từ |
| Tóm tắt | Tiếng Việt ≤ 250 từ, 4 phần (Đặt vấn đề · Phương pháp · Kết quả · Kết luận), kèm bản tiếng Anh; ≤ 6 từ khoá |
| Cấu trúc | Đặt vấn đề · Đối tượng và phương pháp · Kết quả · Bàn luận · Kết luận · Lời cảm ơn · Kiến nghị (nếu có) · Tài liệu tham khảo |
| Phương pháp | Bắt buộc có sơ đồ nghiên cứu và **số quyết định, ngày ký, cơ quan cấp của Hội đồng Đạo đức** |
| Tác giả | Thường ≤ 10, xếp theo mức đóng góp, không ghi học hàm học vị |
| Định dạng | A4, Times New Roman 13, giãn dòng 1,3; lề trái 3 cm, phải/trên/dưới 2 cm |
| Đạo văn | Kiểm bằng iThenticate; trùng lặp > 25% thì không đưa phản biện |
| Phản biện | Kín hai chiều; trang chủ ghi: sàng lọc 1–5 ngày, phản biện 30–40 ngày, chấp nhận 20–30 ngày sau phản biện; 4 số/năm |

> Hệ quả quan trọng: đề cương được dùng cả 47 trích dẫn, nhưng **bài báo chỉ được ≤ 20** — chọn ở G7 (đề xuất sơ bộ ở Phụ lục).

---

## 3. Bảng kế hoạch theo giai đoạn

Ký hiệu người làm: 🤖 máy soạn (agent/công cụ) · 👤 bác sĩ/chủ nhiệm · 🏛 hội đồng, phòng ban (ngoài hệ thống) · ✍ người phản biện ngoài nhóm.

### Giai đoạn 1 — Đặt vấn đề và thiết kế (Tuần 1–2: 26/10 → 08/11/2026)

| # | Việc | Lệnh / công cụ | Ai | Xong khi có | Trạng thái |
|---|---|---|---|---|---|
| 1.1 | Khoảng trống + tính mới | `/tim-khoang-trong` | 🤖 | `G0_KHOANG_TRONG` | ✅ dự thảo xong 25/10 |
| 1.2 | Tổng quan nền + danh mục trích dẫn có toàn văn | `/tong-quan-y-van`, EndNote | 🤖 | 47 bài, 47/47 toàn văn | ✅ 25/10 |
| 1.3 | **Chốt PICO, kết cục, FINER** (khả thi, đạo đức), cửa sổ 12 tháng, danh sách biến giải thích | sửa đề xuất → `gate_params.G0` | 👤 | `pico_confirmed`, `reviewed_by_role`, `reviewed_at`, `dau_van_tay_chot` | ⏳ **việc kế tiếp** |
| 1.4 | Tra WHO ICTRP | trialsearch.who.int | 👤 | `registry_manual_checked.ictrp` | ⏳ |
| 1.5 | Hỏi phòng CNTT: HIS có xuất được creatinin, UACR, mã ICD, đơn thuốc theo mã ẩn danh trong 12 tháng không | — | 👤🏛 | Câu trả lời bằng văn bản | ⏳ rủi ro lớn nhất |
| 1.6 | Lên G0 | `python tools/g0_quality_gate.py --study btm-dtd2-ngoai-tru-BVQY175` | 🤖 | `PASS_G0_CONFIRMED` | ⏳ |
| 1.7 | **G1** — thiết kế, kiểm soát sai lệch, khung phân tích; chuẩn báo cáo STROBE + RECORD (dữ liệu thường quy) | `/thiet-ke-de-tai` (`run_g1_auto.py`, `g1_quality_gate.py`) | 🤖 → 👤 duyệt | Đề cương lõi + định nghĩa ca BTM (KDIGO 2024, 2 lần đo cách ≥ 90 ngày) và «đủ chỉ định» (KDIGO 2022) | — |
| 1.8 | Kế hoạch triển khai: nhân lực trích dữ liệu, tiến độ, kinh phí | agent `ke-hoach-trien-khai` | 🤖 → 👤 điền đơn giá | A13 | — |
| 1.9 | **G3** — cỡ mẫu ước lượng một tỷ lệ | `/tinh-co-mau` (`run_g3_auto.py --prevalence … --precision …`, thêm `--population-n` nếu lấy theo quần thể hữu hạn của khoa) | 🤖 → 👤 chọn p, d | N kèm NGUỒN p (gợi ý PMID 38922613: 24,9% làm đủ cả hai xét nghiệm; PMID 33722396: 43,3% có UACR) | — |
| 1.10 | Bộ biến số + CRF/codebook | `/dat-bien-so` | 🤖 → 👤 | Codebook (tuổi, giới, thời gian mắc, HbA1c, huyết áp, BMI, creatinin/UACR kèm ngày, mã ICD, thuốc ACEi/ARB/SGLT2i/GLP-1 RA, số lượt khám, nhóm đối tượng) | — |

### Giai đoạn 2 — Hồ sơ xét duyệt (Tuần 3–4: 09/11 → 22/11/2026), cổng G2 · G4 ở mức SẴN SÀNG

| # | Việc | Lệnh / công cụ | Ai | Xong khi có | Trạng thái |
|---|---|---|---|---|---|
| 2.1 | Hồ sơ Hội đồng Đạo đức: đề cương, đơn xin miễn đồng thuận (hồi cứu hồ sơ), cam kết bảo mật, kế hoạch quản lý dữ liệu (DMP), khai xung đột lợi ích; quyết định có đăng ký nghiên cứu hay không | `/lam-ho-so-dao-duc` | 🤖 → 👤 | Bộ hồ sơ G2 `READY` | — |
| 2.2 | SAP: tỷ lệ kèm KTC 95%; phân bố G/A; Poisson phương sai vững (tỷ số tỷ lệ hiện mắc) cho yếu tố liên quan; xử lý dữ liệu thiếu; phân tích độ nhạy | `/thiet-ke-de-tai` (`run_g4_auto.py`, `g4_quality_gate.py`) | 🤖 → 👤 | SAP `READY` (chưa khoá) | — |
| 2.3 | Gói nộp hội đồng | `run_g10_assemble.py` với mục đích `ETHICS_SUBMISSION` (chỉ đòi G0–G4, G2/G4 ở mức READY) | 🤖 | Đề cương thống nhất + Word | — |
| 2.4 | Kiểm nhất quán N, thiết kế, kết cục chính giữa các cổng | `python tools/nhat_quan_xuyen_cong.py --study btm-dtd2-ngoai-tru-BVQY175` | 🤖 | Không lệch cứng | — |

### Giai đoạn 3 — Xét duyệt (ngoài hệ thống, ước 4–8 tuần: 23/11/2026 → 01/2027)

| # | Việc | Ai | Xong khi có |
|---|---|---|---|
| 3.1 | Nộp Hội đồng Khoa học (xét duyệt đề cương cấp cơ sở) và Hội đồng Đạo đức BVQY175 — **[CẦN BÁC SĨ XÁC NHẬN quy trình, mẫu hồ sơ, lịch họp của BVQY175]** | 👤🏛 | Quyết định phê duyệt: **số, ngày ký, cơ quan cấp** (tạp chí bắt buộc ghi) |
| 3.2 | **Ký G2** ngay khi có quyết định | 👤 `approve_gate.py --gate G2` | Sổ cái niêm phong |
| 3.3 | **Khoá và ký G4 (SAP) TRƯỚC khi nhìn dữ liệu** | 👤 (thống kê viên hoặc chủ nhiệm) `approve_gate.py --gate G4` | SAP khoá |

### Giai đoạn 4 — Dữ liệu (ước 4–6 tuần: 01 → 02/2027)

| # | Việc | Lệnh / công cụ | Ai | Xong khi có |
|---|---|---|---|---|
| 4.1 | Xin trích xuất HIS theo cửa sổ 12 tháng — chỉ mã nghiên cứu ẩn danh, không trường định danh | — | 👤🏛 (phòng CNTT) | Tệp trích xuất |
| 4.2 | Từ điển dữ liệu ngay khi nhận | `/tu-dien-du-lieu` | 🤖 | Codebook đối chiếu |
| 4.3 | Khử định danh (ngay khi trích) | `/khu-dinh-danh` | 🤖 → 👤 | Dữ liệu sạch PII |
| 4.4 | Làm sạch, bác sĩ duyệt từng quyết định | `/lam-sach-du-lieu` | 🤖 → 👤 | Nhật ký làm sạch |
| 4.5 | **Khoá cơ sở dữ liệu → ký G5** | `/khoa-du-lieu` → `approve_gate.py --gate G5` | 👤 | DB khoá |

### Giai đoạn 5 — Phân tích và bản thảo (ước 5 tuần: 02 → 03/2027)

| # | Việc | Lệnh / công cụ | Ai | Xong khi có |
|---|---|---|---|---|
| 5.1 | **G6** — chạy đúng SAP đã khoá | `/chay-thong-ke` | 🤖 | Bảng kết quả |
| 5.2 | Bảng 1 + sơ đồ chọn mẫu + biểu đồ chuỗi chăm sóc (xét nghiệm → phát hiện → ghi nhận → điều trị) — tổng ≤ 5 bảng, ≤ 5 hình | `/lam-bang-mot`, `/ve-hinh-bai-bao` | 🤖 | Bảng/hình đạt chuẩn |
| 5.3 | Diễn giải ý nghĩa lâm sàng, so với y văn | `/dien-giai-so-lieu` | 🤖 → 👤 | Nội dung Bàn luận |
| 5.4 | **G7** — bản thảo tiếng Việt đúng thể lệ (≤ 5.000 từ, tóm tắt 250 từ + bản Anh, ≤ 6 từ khoá) | `/viet-bai-bao` | 🤖 → 👤 | Bản thảo |
| 5.5 | Chọn ≤ 20 tài liệu tham khảo từ 47 bài; kiểm PMID/DOI, bài bị rút | `/kiem-trich-dan` | 🤖 → 👤 | Danh mục Vancouver ≤ 20 |
| 5.6 | Đối chiếu STROBE + RECORD | `/kiem-chuan-bao-cao` | 🤖 | Bảng kiểm |
| 5.7 | Gọt tóm tắt tiếng Anh; tự rà bằng con mắt phản biện | `/got-tieng-anh`, `/tu-ra-bai` | 🤖 → 👤 | Bản thảo sửa |

### Giai đoạn 6 — Bình duyệt, liêm chính, nộp (ước 3–4 tuần: 03 → 04/2027)

| # | Việc | Lệnh / công cụ | Ai | Xong khi có |
|---|---|---|---|---|
| 6.1 | Phản biện nội bộ thử | `/nho-phan-bien` | 🤖 | Danh sách góp ý |
| 6.2 | **Người phản biện thật ngoài nhóm** viết báo cáo → **ký G8** | `G8_PEER_REVIEW_REPORT_btm-dtd2-ngoai-tru-BVQY175.md` | ✍ → 👤 | `PASS_G8_REVIEW_RECORDED` |
| 6.3 | Tác giả (ICMJE 4 tiêu chí, CRediT), COI, khai dùng AI, khả dụng dữ liệu, xác nhận thể chế → **ký G9** | `/nop-bai` | 👤 | G9 ký |
| 6.4 | Tự kiểm trùng lặp trước khi nộp (ngưỡng tạp chí 25%) | — | 👤 | Tỷ lệ trùng lặp |
| 6.5 | Đóng gói nộp → **ký G10** → nộp qua mục «Gửi bài mới» | `/nop-bai` | 👤 | Mã bài nộp |
| 6.6 | Nhận góp ý phản biện (≈ 30–40 ngày) → thư phản hồi từng điểm | `/tra-loi-phan-bien` | 🤖 → 👤 | Bản sửa + thư phản hồi |

---

## 4. Quyết định thuộc thẩm quyền chủ nhiệm (máy KHÔNG tự điền)

| # | Quyết định | Cần trước |
|---|---|---|
| Q1 | Cửa sổ hồi cứu 12 tháng: ngày đầu – ngày cuối | G0 |
| Q2 | Danh sách biến giải thích cho mục tiêu phụ 4 | G0 / G1 |
| Q3 | FINER khả thi + đạo đức (HIS xuất được gì, hình thức miễn đồng thuận) | G0 |
| Q4 | Lấy toàn bộ hồ sơ đủ tiêu chuẩn hay mẫu ngẫu nhiên | G1 / G3 |
| Q5 | Giá trị p và sai số d cho cỡ mẫu (kèm nguồn) | G3 |
| Q6 | Có đăng ký nghiên cứu hay không (quan sát — không bắt buộc như thử nghiệm) | G2 |
| Q7 | Người phản biện ngoài nhóm | G8 |
| Q8 | Danh sách tác giả, thứ tự đóng góp, kinh phí | G1 (A13) / G9 |

---

## 5. Rủi ro và cách giảm

| Rủi ro | Ảnh hưởng | Cách giảm |
|---|---|---|
| HIS không xuất được UACR/creatinin/ICD/đơn thuốc theo mã ẩn danh | Không làm được đề tài | Hỏi phòng CNTT ngay tuần 1 (việc 1.5), trước khi đầu tư G1–G4 |
| UACR làm ở cơ sở khác không có trong HIS | Đánh giá thấp tỷ lệ được xét nghiệm | Ghi là hạn chế; phân tích độ nhạy trong SAP |
| Yêu cầu 2 lần đo cách ≥ 90 ngày | Nhiều ca chỉ có 1 lần đo | Nhóm «nghi BTM» riêng (đã có trong đề xuất G0) |
| Mã ICD ghi không đủ | Sai lệch kết cục «BTM chưa ghi nhận» | Định nghĩa vận hành rõ ở G1; kiểm ngẫu nhiên một phần hồ sơ |
| Đơn kê ≠ thuốc bệnh nhân thật sự dùng | Ước lượng sai tỷ lệ điều trị | Ghi rõ «được kê đơn»; nêu là hạn chế |
| Bài báo giới hạn 20 tài liệu tham khảo | Phải cắt từ 47 | Chọn ở G7 theo Phụ lục |
| Lịch hội đồng BVQY175 không chắc chắn | Lùi toàn bộ tiến độ | Nộp hồ sơ sớm; giai đoạn 1–2 làm song song việc hỏi quy trình |

---

## Phụ lục — Đề xuất sơ bộ 20 tài liệu tham khảo cho bài báo (chốt ở G7)

Chọn từ 47 bài đã có toàn văn trong nhóm EndNote đề tài; ưu tiên bài đo đúng kết cục của đề tài và bối cảnh trong nước.

- **Hướng dẫn (3):** KDIGO 2024 — PMID 38490803; KDIGO 2022 ĐTĐ trong BTM — PMID 36272764; ADA Standards of Care 2026 mục 11 — PMID 41358881.
- **Tỷ lệ xét nghiệm (4):** PMID 38922613; PMID 33722396; tổng quan hệ thống và phân tích gộp PMID 41345917; Việt Nam PMID 41916900.
- **BTM chưa được chẩn đoán/ghi nhận (4):** PMID 41741270; PMID 40428801; PMID 39023418; PMID 35177470.
- **Khoảng trống điều trị và bối cảnh tương tự (3):** PMID 36352203; PMID 39507052 (Thái Lan); PMID 42838586 (nội khoa ngoại trú tuyến cuối).
- **Can thiệp tiếp nối (1):** RCT CKD-DETECT — PMID 42031191.
- **Trong nước (5):** DOI 10.34071/jmp.2026.5.914; DOI 10.56283/1859-0381/390 (Bệnh viện Quân y 103); DOI 10.51298/vmj.v534i2.8190; DOI 10.51298/vmj.v545i1.12165; DOI 10.52389/ydls.v0i0.879.

Ghi chú: Hướng dẫn quốc gia của Bộ Y tế (QĐ 5481/QĐ-BYT, sửa bởi QĐ 1353/QĐ-BYT) chưa có trong danh mục vì chưa có toàn văn — nếu chủ nhiệm muốn trích, cần lấy văn bản gốc rồi thay một mục ở trên. Chuẩn báo cáo dùng để tự kiểm (không bắt buộc trích): STROBE — PMID 18064739; RECORD — PMID 26440803.

Cần bác sĩ kiểm chứng.
