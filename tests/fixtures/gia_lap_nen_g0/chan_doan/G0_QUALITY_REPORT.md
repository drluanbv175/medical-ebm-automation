# BÁO CÁO CHẤT LƯỢNG G0 — ZZCANARY-CHAN-DOAN

**Trạng thái:** `DRAFT_READY_NEEDS_HUMAN_REVIEW`  ·  **Hợp đồng:** `G0-2026.1`

> G0 = cổng CÂU HỎI NGHIÊN CỨU. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết quả
> ĐÚNG của một lần chạy tự động — không phải lỗi. Chỉ `PASS_G0_CONFIRMED`
> mới có nghĩa câu hỏi đã được người thật chốt.

## Kiểm tra tự động (máy làm được)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-AUTO-00 | Guardrail liêm chính G0 sạch | PASS | guardrail_passed=True |
| G0-AUTO-01 | Đề tài có chủ đề thật (không rỗng/placeholder) | PASS | topic='Giá trị chẩn đoán của chỉ số FIB-4 trong phát hiện xơ hoá gan tiến triển ở người' |
| G0-AUTO-02 | Có bằng chứng THẬT làm nền (≥ 1 PMID từ PubMed) | PASS | n_pmids=26 |
| G0-AUTO-03 | Số hit dùng để kết luận khoảng trống là SỐ THẬT | PASS | counts_are_real=True; nhánh không tra được=[] |
| G0-AUTO-04 | Checkpoint đủ trường hợp đồng cho cổng sau đọc | PASS | 10 khóa gốc + 9 khóa pubmed_results đầy đủ |
| G0-AUTO-05 | Artifact A1 có đủ 6 thành phần theo doctrine | PASS | A1 có đủ 7 mục bắt buộc |
| G0-AUTO-06 | Đã tra ClinicalTrials.gov (chủ yếu phủ thử nghiệm can thiệp; ICTRP/PROSPERO ở G0-HUMAN-08) | PASS | ClinicalTrials.gov: 18 hồ sơ khớp, 6 đang tuyển |
| G0-AUTO-07 | Trường bác sĩ điền ở gate_params.G0 không chứa thông tin định danh | PASS | không thấy mẫu PII trong gate_params.G0 + chủ đề |
| G0-AUTO-08 | Truy vấn PubMed và ClinicalTrials.gov phủ khái niệm PICO đã chốt (P · I/E · O) | PASS | PICO chưa chốt — đối chiếu khi PI chốt PICO |

## Xác nhận người thật (bác sĩ phải chốt)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G0-HUMAN-01 | PICO/PECO đủ 4 thành phần do bác sĩ viết | REVIEW | thiếu: population, intervention, comparison, outcomes |
| G0-HUMAN-02 | Kết cục CHÍNH duy nhất, đo được, có thời điểm | REVIEW | primary_outcome=thiếu; thang đo=thiếu; thời điểm đo=thiếu |
| G0-HUMAN-03 | Giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định | REVIEW | test_type=thiếu; H0=thiếu; H1=thiếu; chiều=thiếu |
| G0-HUMAN-04 | Loại câu hỏi đã xác định | REVIEW | question_type=thiếu |
| G0-HUMAN-05 | FINER đánh giá đủ từng tiêu chí (5/5), kết luận ĐẠT và có lý do | REVIEW | thiếu: feasible, interesting, novel, ethical, relevant |
| G0-HUMAN-06 | Đã đọc lại bằng chứng G0 và biện minh tính mới | REVIEW | evidence_reviewed_confirmed=False; novelty_justification=thiếu |
| G0-HUMAN-07 | Chủ nhiệm/nhà phương pháp chốt PICO (vai trò + thời điểm + gắn đúng nội dung) | REVIEW | pico_confirmed=False; vai trò=thiếu; reviewed_at=thiếu; `reviewed_at` không phải ISO-8601 hợp lệ hoặc ở tương lai |
| G0-HUMAN-08 | PI đã tự tra WHO ICTRP (và PROSPERO cho tổng quan) + đánh giá chồng lấn khi có thử nghiệm đang tuyển | REVIEW | thiếu ngày tra (ISO, không ở tương lai): ictrp; ClinicalTrials.gov có 6 thử nghiệm đang tuyển khớp — thiếu registry_overlap_assessment |

## Việc còn lại trước khi được ghi PASS_G0_CONFIRMED
1. Điền gate_params.G0.population/intervention/comparison/outcomes trong study_meta.json (ghi 'không có nhóm so sánh — mô tả' nếu đúng vậy).
2. Điền primary_outcome (1 kết cục) + primary_outcome_measure + primary_outcome_timepoint.
3. Điền test_type (superiority/non_inferiority/equivalence/descriptive); nếu không phải nghiên cứu mô tả thì điền cả hypothesis_h0/h1 và expected_direction.
4. Điền question_type: treatment (≡ therapy)/diagnosis/prognosis/harm/descriptive/qualitative/prediction_model.
5. Viết cho mỗi khoá finer_* một câu kết luận + lý do (F và E máy KHÔNG thể tự đánh giá). Tiêu chí KHÔNG ĐẠT ⇒ đổi câu hỏi nghiên cứu, hoặc ghi rõ vì sao vẫn chấp nhận.
6. Đọc danh sách PMID ở §3 của A1, rồi đặt evidence_reviewed_confirmed=true và viết novelty_justification.
7. Đặt pico_confirmed=true, reviewed_by_role (PI/chủ nhiệm/methodologist), reviewed_at dạng ISO-8601 (không ở tương lai) và dau_van_tay_chot="a93dc88ea4ffa59b" (dấu của nội dung đang chốt). Không cần lưu danh tính.
8. Tự tra WHO ICTRP (trialsearch.who.int) — và PROSPERO nếu là tổng quan hệ thống — rồi ghi gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD", "prospero": "YYYY-MM-DD"}; có thử nghiệm đang tuyển khớp ⇒ viết registry_overlap_assessment (khác biệt/chồng lấn).

## Chuẩn báo cáo DỰ KIẾN (G1 quyết định chính thức)
- Mã thiết kế suy từ gợi ý G0: `rct`
- Chuẩn báo cáo: CONSORT 2025
- Chuẩn đề cương: SPIRIT 2025; đăng ký trial TRƯỚC tuyển mẫu; ICH-GCP nếu áp dụng

## Manifest artifact
| Artifact | Đường dẫn | SHA-256 |
|---|---|---|
| A1 | /private/var/folders/t_/nspjmxbs4gdb3yw_gwqk533h0000gn/T/gia-lap-dinh-ky-lz545948/repo/exports/ZZCANARY-CHAN-DOAN/G0_A1_PICO_FINER_ZZCANARY-CHAN-DOAN.md | `2d5b546092fcb26b6bbaad932c80a94bb13b43169b4cea5970b7a9e29c02cc85` |

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
