# BÁO CÁO CHẤT LƯỢNG G0 — hai-long-benh-nhan-C1a-BVQY175

**Trạng thái:** `PASS_G0_CONFIRMED`  ·  **Hợp đồng:** `G0-2026.1`

> G0 = cổng CÂU HỎI NGHIÊN CỨU. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết quả
> ĐÚNG của một lần chạy tự động — không phải lỗi. Chỉ `PASS_G0_CONFIRMED`
> mới có nghĩa câu hỏi đã được người thật chốt.

## Kiểm tra tự động (máy làm được)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-AUTO-00 | Guardrail liêm chính G0 sạch | PASS | guardrail_passed=True |
| G0-AUTO-01 | Đề tài có chủ đề thật (không rỗng/placeholder) | PASS | topic='Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo' |
| G0-AUTO-02 | Có bằng chứng THẬT làm nền (≥1 PMID từ PubMed) | PASS | n_pmids=12 |
| G0-AUTO-03 | Số hit dùng để kết luận khoảng trống là SỐ THẬT | PASS | counts_are_real=True; nhánh không tra được=[] |
| G0-AUTO-04 | Checkpoint đủ trường hợp đồng cho cổng sau đọc | PASS | 10 khóa gốc + 9 khóa pubmed_results đầy đủ |
| G0-AUTO-05 | Artifact A1 có đủ 6 thành phần theo doctrine | PASS | A1 có đủ 7 mục bắt buộc |
| G0-AUTO-06 | Đã tra đăng ký nghiên cứu đang tiến hành (trùng lặp) | PASS | ClinicalTrials.gov: 0 hồ sơ khớp, 0 đang tuyển |

## Xác nhận người thật (bác sĩ phải chốt)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-HUMAN-01 | PICO/PECO đủ 4 thành phần do bác sĩ viết | PASS | P/I/C/O đều có nội dung |
| G0-HUMAN-02 | Kết cục CHÍNH duy nhất, đo được, có thời điểm | PASS | 1 kết cục chính, có thang đo và thời điểm đo |
| G0-HUMAN-03 | Giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định | PASS | test_type=descriptive; H0=thiếu; H1=thiếu; chiều=thiếu |
| G0-HUMAN-04 | Loại câu hỏi đã xác định | PASS | question_type=descriptive |
| G0-HUMAN-05 | FINER đánh giá đủ từng tiêu chí (5/5) | PASS | 5/5 tiêu chí có kết luận |
| G0-HUMAN-06 | Đã đọc lại bằng chứng G0 và biện minh tính mới | PASS | evidence_reviewed_confirmed=True; novelty_justification=có |
| G0-HUMAN-07 | Chủ nhiệm/nhà phương pháp chốt PICO (vai trò + thời điểm) | PASS | pico_confirmed=True; vai trò=pi; reviewed_at=2026-08-15 |

## Chuẩn báo cáo DỰ KIẾN (G1 quyết định chính thức)
- Mã thiết kế suy từ gợi ý G0: `rct`
- Chuẩn báo cáo: CONSORT 2025
- Chuẩn đề cương: SPIRIT 2025; đăng ký trial TRƯỚC tuyển mẫu; ICH-GCP nếu áp dụng

## Manifest artifact
| Artifact | Đường dẫn | SHA-256 |
|---|---|---|
| A1 | exports/hai-long-benh-nhan-C1a-BVQY175/G0_A1_PICO_FINER_hai-long-benh-nhan-C1a-BVQY175.md | `5a0c0940832ad678080716cb6c49ad149af57d78715883d234ec94c9650c3180` |

## Nền chuẩn
| Chuẩn | Phạm vi | PMID/DOI/URL |
|---|---|---|
| PICO framework | Khung câu hỏi lâm sàng/nghiên cứu 4 thành phần | PMID:7582737 |
| FINER criteria (Hulley, Designing Clinical Research) | Sàng lọc câu hỏi nghiên cứu: Feasible/Interesting/Novel/Ethical/Relevant | https://www.equator-network.org/library/ |
| EQUATOR Network | Bản đồ chuẩn báo cáo theo loại thiết kế (dùng cho chuẩn dự kiến ở G0) | https://www.equator-network.org/library/ |
| ICMJE Recommendations | Đăng ký nghiên cứu trước khi tuyển người tham gia đầu tiên | https://www.icmje.org/recommendations/ |

## Giới hạn phán định
PASS_G0_CONFIRMED chỉ xác nhận rằng câu hỏi nghiên cứu ĐÃ ĐƯỢC MỘT NGƯỜI THẬT VIẾT RA VÀ CHỐT, và nền bằng chứng máy dựng là thật. KHÔNG thẩm định chất lượng khoa học của câu hỏi, không thay tổng quan y văn có hệ thống, không thay Hội đồng Đạo đức. Một PICO đầy đủ vẫn có thể là một PICO tồi.

> Cần bác sĩ kiểm chứng.
