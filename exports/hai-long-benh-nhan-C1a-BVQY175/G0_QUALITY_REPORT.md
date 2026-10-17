# BÁO CÁO CHẤT LƯỢNG G0 — hai-long-benh-nhan-C1a-BVQY175

**Trạng thái:** `DRAFT_READY_NEEDS_HUMAN_REVIEW`  ·  **Hợp đồng:** `G0-2026.1`

> G0 = cổng CÂU HỎI NGHIÊN CỨU. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết quả
> ĐÚNG của một lần chạy tự động — không phải lỗi. Chỉ `PASS_G0_CONFIRMED`
> mới có nghĩa câu hỏi đã được người thật chốt.

## Kiểm tra tự động (máy làm được)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-AUTO-00 | Guardrail liêm chính G0 sạch | PASS | guardrail_passed=True |
| G0-AUTO-01 | Đề tài có chủ đề thật (không rỗng/placeholder) | PASS | topic='Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo' |
| G0-AUTO-02 | Có bằng chứng THẬT làm nền (≥1 PMID từ PubMed) | PASS | n_pmids=16 |
| G0-AUTO-03 | Số hit dùng để kết luận khoảng trống là SỐ THẬT | PASS | counts_are_real=True; nhánh không tra được=[] |
| G0-AUTO-04 | Checkpoint đủ trường hợp đồng cho cổng sau đọc | PASS | 10 khóa gốc + 9 khóa pubmed_results đầy đủ |
| G0-AUTO-05 | Artifact A1 có đủ 6 thành phần theo doctrine | PASS | A1 có đủ 7 mục bắt buộc |
| G0-AUTO-06 | Đã tra ClinicalTrials.gov (chủ yếu phủ thử nghiệm can thiệp; ICTRP/PROSPERO ở G0-HUMAN-08) | PASS | ClinicalTrials.gov: 5 hồ sơ khớp, 3 đang tuyển |
| G0-AUTO-07 | Trường bác sĩ điền ở gate_params.G0 không chứa thông tin định danh | PASS | không thấy mẫu PII trong gate_params.G0 + chủ đề |

## Xác nhận người thật (bác sĩ phải chốt)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-HUMAN-01 | PICO/PECO đủ 4 thành phần do bác sĩ viết | PASS | P/I/C/O đều có nội dung |
| G0-HUMAN-02 | Kết cục CHÍNH duy nhất, đo được, có thời điểm | PASS | 1 kết cục chính, có thang đo và thời điểm đo |
| G0-HUMAN-03 | Giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định | PASS | test_type=descriptive; H0=có; H1=có; chiều=có |
| G0-HUMAN-04 | Loại câu hỏi đã xác định | PASS | question_type=descriptive (chuẩn hoá: descriptive) |
| G0-HUMAN-05 | FINER đánh giá đủ từng tiêu chí (5/5), kết luận ĐẠT và có lý do | PASS | 5/5 tiêu chí có kết luận đạt kèm lý do |
| G0-HUMAN-06 | Đã đọc lại bằng chứng G0 và biện minh tính mới | PASS | evidence_reviewed_confirmed=True; novelty_justification=có |
| G0-HUMAN-07 | Chủ nhiệm/nhà phương pháp chốt PICO (vai trò + thời điểm + gắn đúng nội dung) | REVIEW | pico_confirmed=True; vai trò=pi; reviewed_at=2026-10-14T19:17:12+07:00; nội dung đã đổi sau khi xác nhận (dấu lúc xác nhận 4678a3407d3ccd57 ≠ hiện tại f619939b4c69e1e5) — chủ nhiệm đọc lại rồi xác nhận lại |
| G0-HUMAN-08 | PI đã tự tra WHO ICTRP (và PROSPERO cho tổng quan) + đánh giá chồng lấn khi có thử nghiệm đang tuyển | PASS | đã ghi ngày tra |

## Việc còn lại trước khi được ghi PASS_G0_CONFIRMED
1. Đặt pico_confirmed=true, reviewed_by_role (PI/chủ nhiệm/methodologist), reviewed_at dạng ISO-8601 (không ở tương lai) và dau_van_tay_chot="f619939b4c69e1e5" (dấu của nội dung đang chốt). Không cần lưu danh tính.

## Chuẩn báo cáo DỰ KIẾN (G1 quyết định chính thức)
- Mã thiết kế suy từ gợi ý G0: `cross_sectional`
- Chuẩn báo cáo: STROBE
- Chuẩn đề cương: Protocol định trước; đăng ký nếu cần minh bạch

## Manifest artifact
| Artifact | Đường dẫn | SHA-256 |
|---|---|---|
| A1 | /Users/nguyenluan/.ebm-worktrees/yk-c1a-g0-dp-20261017/exports/hai-long-benh-nhan-C1a-BVQY175/G0_A1_PICO_FINER_hai-long-benh-nhan-C1a-BVQY175.md | `ea33bc87500360552ba41ccdad260001149ae8c118d8f8010194b2b16b8e402c` |

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
