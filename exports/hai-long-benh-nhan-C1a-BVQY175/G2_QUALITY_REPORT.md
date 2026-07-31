# G2 QUALITY REPORT — hai-long-benh-nhan-C1a-BVQY175

- Trạng thái: **DRAFT_NEEDS_HUMAN_COMPLETION**
- Hồ sơ sẵn sàng nộp: **False**
- Phê duyệt người thật đủ: **False**

## Kiểm tự động
| ID | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G2-AUTO-01 | Guardrail liêm chính G2 sạch | PASS | guardrail_passed=True |
| G2-AUTO-02 | G1 đã được PI/methodologist xác nhận | REVIEW | G1 quality status=DRAFT_READY_NEEDS_HUMAN_REVIEW |
| G2-AUTO-03 | Bộ hồ sơ IRB/ICF/DMP có đủ cấu trúc bắt buộc | PASS | đủ marker tài liệu 1-8, ICF, DMP, rủi ro/bồi thường/COI |
| G2-AUTO-04 | WHO TRDS 1.3.1 đủ 24 mục | PASS | 24/24 mục đúng số và nhãn |
| G2-AUTO-05 | Không còn placeholder khoa học/vận hành trọng yếu | REVIEW | còn 71 dòng [CẦN] ngoài các dòng chỉ chứa PII |
| G2-AUTO-06 | Thiết kế và lộ trình đạo đức không còn mơ hồ | PASS | design_code=cross_sectional; ambiguous=False |
| G2-AUTO-07 | Kế hoạch an toàn tương xứng thiết kế | PASS | không phải RCT; kế hoạch an toàn điều chỉnh theo nguy cơ |
| G2-AUTO-08 | Mục khoa học WHO TRDS (can thiệp/tiêu chí/kết cục) đã có nội dung thật | REVIEW | còn trống: #13 Intervention(s), #14 Key Inclusion and Exclusion Criteria, #19 Primary Outcome(s), #20 Key Secondary Outcomes |
| G2-AUTO-09 | Mã Hội đồng Đạo đức tách biệt khỏi định danh người duyệt chung | PASS | ethics_committee_ref_source=chưa có attestation |

## Phê duyệt người thật
| ID | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G2-HUMAN-01 | Quyết định IRB/IEC có số, ngày, hiệu lực, phạm vi và phiên bản | REVIEW | Chưa có phụ lục quyết định IRB có cấu trúc |
| G2-HUMAN-02 | Approval ledger đúng vai trò IRB và khớp hash artifact | REVIEW | ledger_approved=False |

## Việc còn lại
- Hoàn tất xác nhận phương pháp G1; có thể soạn G2 song song nhưng chưa khóa.
- Điền nội dung thật; với PII dùng bản nộp ngoài hệ thống và giữ bản redacted.
- Điền Intervention(s)/Inclusion-Exclusion/Primary-Secondary Outcome từ PICO thật của đề tài (checkpoint G1) trước khi đăng ký thật.
- Hội đồng/đầu mối được ủy quyền ghi quyết định bằng approve_gate.py.
- Người có thẩm quyền IRB tự ký; agent không được chạy lệnh phê duyệt.

## Giới hạn
PASS_G2_APPROVED chỉ xác nhận dấu vết IRB/IEC, phiên bản và đăng ký đã cung cấp cho hệ thống. HMAC cục bộ không tự chứng minh tính độc lập của Hội đồng; hồ sơ gốc và quyết định thật vẫn phải được kiểm tra.

> Cần bác sĩ kiểm chứng.
