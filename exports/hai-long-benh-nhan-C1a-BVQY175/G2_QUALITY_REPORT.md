# G2 QUALITY REPORT — hai-long-benh-nhan-C1a-BVQY175

- Trạng thái: **READY_FOR_IRB_SUBMISSION**
- Hồ sơ sẵn sàng nộp: **True**
- Phê duyệt người thật đủ: **False**

## Kiểm tự động
| ID | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G2-AUTO-01 | Liêm chính nội dung hồ sơ HIỆN HÀNH (PII, số phê duyệt tự gán, tự xưng phê duyệt/khoá, disclaimer) | PASS | R1/R2/R3/R7 sạch trên nội dung hiện hành (guardrail lúc sinh: passed=False) |
| G2-AUTO-02 | G1 đã được PI/methodologist xác nhận (chấm sống) | PASS | G1 chấm sống=PASS_G1_CONFIRMED |
| G2-AUTO-02b | ICH E6(R3) Annex 2 Step 4: IRB/consent/privacy/data governance đủ cho phương pháp mới | PASS | status=NOT_APPLICABLE; methods=không áp dụng |
| G2-AUTO-03 | Bộ hồ sơ IRB/ICF/DMP có đủ cấu trúc bắt buộc (ICF đủ mục theo thiết kế) | PASS | đủ marker tài liệu 1-8, ICF, DMP, rủi ro/bồi thường/COI; ICF đủ mục theo thiết kế |
| G2-AUTO-03b | ICF tiếng Anh tương ứng ICF tiếng Việt (cùng tập mục) | PASS | hai bản ICF có cùng tập mục (hoặc chưa có bản tiếng Anh/tiếng Việt để đối chiếu) |
| G2-AUTO-04 | WHO TRDS 1.3.1 đủ 24 mục | PASS | 24/24 mục đúng số và nhãn |
| G2-AUTO-05 | Không còn placeholder khoa học/vận hành trọng yếu | PASS | còn 0 dòng [CẦN]/ô mẫu chung/ô trống phải điền TRƯỚC khi nộp IRB; 8 dòng chỉ điền được SAU phê duyệt/đăng ký (thông tin, chưa chặn nộp) — ngoài các ô chỉ chứa PII và chỗ ký/ngày điền tay |
| G2-AUTO-06 | Thiết kế và lộ trình đạo đức không còn mơ hồ | PASS | design_code=cross_sectional; ambiguous=False |
| G2-AUTO-06b | Hồ sơ G2 sinh đúng thiết kế G1 hiện hành | PASS | hồ sơ G2 và G1 cùng thiết kế «cross_sectional» |
| G2-AUTO-07 | Kế hoạch an toàn tương xứng thiết kế | PASS | không phải RCT và PI không khai safety_plan_required=true — kế hoạch an toàn theo nguy cơ |
| G2-AUTO-08 | Mục khoa học WHO TRDS (can thiệp/tiêu chí/kết cục) đã có nội dung thật | PASS | mục 13/14/19/20 đã có nội dung |
| G2-AUTO-08b | Mục WHO TRDS tự điền đã được PI khai (9 tiêu đề công khai, 12 tình trạng sức khỏe, 15 masking của RCT) | PASS | mục 9/12 (và masking RCT) đã do PI khai |
| G2-AUTO-10 | Phiên bản đề cương/ICF hiện hành do PI khai | PASS | protocol_version=1.0; icf_version=1.0; «1.0» có thể là giá trị khuôn gieo trước 04/10/2026 — PI xác nhận |
| G2-AUTO-09 | Mã Hội đồng Đạo đức tách biệt khỏi định danh người duyệt chung | PASS | ethics_committee_ref_source=chưa có attestation |

## Phê duyệt người thật
| ID | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G2-HUMAN-01 | Quyết định IRB/IEC có số, ngày, hiệu lực, phạm vi và phiên bản | REVIEW | Chưa có phụ lục quyết định IRB có cấu trúc |
| G2-HUMAN-02 | Approval ledger đúng vai trò IRB và khớp hash artifact | REVIEW | ledger_approved=False |

## Ô chỉ điền được SAU phê duyệt/đăng ký
Không chặn nộp IRB; BẮT BUỘC điền trước khi ký khoá G2 (approve_gate từ chối ký khi còn).
- [Phiên bản phê duyệt sẽ có số IRB, CẦN BỔ SUNG]
- [CẦN — sẽ có sau khi đăng ký trên OSF Registries: mã/URL đăng ký dạng osf.io/xxxxx]
- [CẦN — ngày đăng ký thành công]
- Số phê duyệt IRB: [CẦN sau khi nhận]
- [CẦN — chỉ tuyển sau phê duyệt và đăng ký: ___/___/2026]
- Approval date: [CẦN sau quyết định IRB]
- [CẦN — ngày hoàn tất dự kiến; cập nhật ngày thật khi kết thúc]
- "DRAFT, Điền trường còn [CẦN] trước khi gửi đăng ký."

## Việc còn lại
- Hội đồng/đầu mối được ủy quyền ghi quyết định bằng approve_gate.py.
- Người có thẩm quyền IRB tự ký; agent không được chạy lệnh phê duyệt.

## Giới hạn
PASS_G2_APPROVED chỉ xác nhận dấu vết IRB/IEC, phiên bản và đăng ký đã cung cấp cho hệ thống. HMAC cục bộ không tự chứng minh tính độc lập của Hội đồng; hồ sơ gốc và quyết định thật vẫn phải được kiểm tra.

> Cần bác sĩ kiểm chứng.
