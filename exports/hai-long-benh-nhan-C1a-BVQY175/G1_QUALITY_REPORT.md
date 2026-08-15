# BÁO CÁO CHẤT LƯỢNG G1 — hai-long-benh-nhan-C1a-BVQY175

**Trạng thái:** `DRAFT_READY_NEEDS_HUMAN_REVIEW`

## Kiểm tra tự động
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G1-AUTO-00 | Guardrail liêm chính G1 sạch | PASS | guardrail_passed=True |
| G1-AUTO-01 | Tiền đề G0 có checkpoint và guardrail sạch | PASS | G0 legacy guardrail passed=True |
| G1-AUTO-02 | Mã thiết kế thuộc vocabulary canonical | PASS | internal_code='cross_sectional' |
| G1-AUTO-03 | Chuẩn báo cáo khớp thiết kế | PASS | đã chọn='STROBE'; canon='STROBE' |
| G1-AUTO-03b | Chuẩn đề cương/protocol khớp thiết kế | PASS | đã chọn='Protocol định trước; đăng ký nếu cần minh bạch'; canon='Protocol định trước; đăng ký nếu cần minh bạch' |
| G1-AUTO-04 | Thiết kế không còn suy luận mơ hồ | PASS | ambiguous=false |
| G1-AUTO-04b | So sánh ít nhất ba phương án và kiểm soát đủ nhóm sai lệch/trustworthiness theo thiết kế | PASS | primary_present=True; alternatives_complete=True; rationale_present=True; bias_controls=7 |
| G1-AUTO-04c | SAP không chứa khuôn phân tích mâu thuẫn với thiết kế | PASS | không phát hiện khuôn sai cho cross_sectional |
| G1-AUTO-05 | Đủ bộ A1b/A2/A2b/A13/A13b và các phần bắt buộc | PASS | 5/5 artifact có mặt và qua kiểm cấu trúc |
| G1-AUTO-06 | Có định danh PMID/DOI khớp chuỗi trong Evidence Ledger (CHƯA xác minh qua PubMed/Crossref — việc đó thuộc cổng A12 kiem-chung-trich-dan) | PASS | 12 PMID/DOI được thu, ledger_traceable=True (khớp CHUỖI, KHÔNG gọi PubMed để xác minh tồn tại) |

## Xác nhận người thật
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G1-HUMAN-01 | PI/methodologist xác nhận thiết kế | REVIEW | pin='cross_sectional'; design_confirmed=False |
| G1-HUMAN-02 | Mục tiêu và kết cục chính vận hành đã chốt | REVIEW | objectives=đủ; outcome_name=có; measure=thiếu; timepoint=thiếu; type=thiếu |
| G1-HUMAN-03 | Quần thể, tiêu chí chọn, tuyển mẫu, bối cảnh và thời gian đã xác định | REVIEW | population=có; inclusion=có; exclusion=có; recruitment=có; setting=có; study_period=thiếu |
| G1-HUMAN-04 | Can thiệp/phơi nhiễm, đối chứng và lịch theo dõi đã xác định | PASS | intervention_or_exposure=có; comparator=có; follow_up_schedule=có |
| G1-HUMAN-05 | Estimand đủ 5 thuộc tính khi là RCT | PASS | N/A cho thiết kế không phải RCT |
| G1-HUMAN-06 | Đề cương lõi, kiểm soát sai lệch và tính khả thi được xác nhận | REVIEW | protocol_core_confirmed=False; bias_controls_confirmed=False; feasibility_confirmed=False |
| G1-HUMAN-07 | Khoảng trống và nội dung trích dẫn đã được người thật đọc lại | REVIEW | evidence_review_confirmed=False; identifiers=12 |
| G1-HUMAN-08 | Có vai trò và thời điểm rà phương pháp | REVIEW | reviewed_by_role=thiếu; reviewed_at=thiếu |

## Manifest artifact
| Artifact | Đường dẫn | SHA-256 |
|---|---|---|
| A2 | exports/hai-long-benh-nhan-C1a-BVQY175/G1_A2_PROTOCOL_DESIGN_hai-long-benh-nhan-C1a-BVQY175.md | `95026d294466fd7bced6fb7249c784df79a8602e3ed2102b22c7909557175107` |
| A1b | exports/hai-long-benh-nhan-C1a-BVQY175/G1_A1b_PROJECT_CHARTER_hai-long-benh-nhan-C1a-BVQY175.md | `29384c97c7e907d213ed81495dfdf0ef6b943a36d0152ae2ad4069c5bd5eaa3a` |
| A2b | exports/hai-long-benh-nhan-C1a-BVQY175/G1_A2b_EVIDENCE_LEDGER_hai-long-benh-nhan-C1a-BVQY175.md | `5066abe7d535d221f76336f963eab2114f751f3d8ca119504141270e8992c728` |
| A13 | exports/hai-long-benh-nhan-C1a-BVQY175/G1_A13_IMPLEMENTATION_PLAN_hai-long-benh-nhan-C1a-BVQY175.md | `5de5087b086310a566d9e16cb13df4ce9a41b5060d585b2ef8560af52dfefcd9` |
| A13b | exports/hai-long-benh-nhan-C1a-BVQY175/G1_A13b_RISK_REGISTER_hai-long-benh-nhan-C1a-BVQY175.md | `ee4142804669315d6fd1e27a4e7a5c67d44e4c09b08a52043950a81e03df52ca` |

## Nền chuẩn
| Chuẩn | Phạm vi | PMID/DOI/URL |
|---|---|---|
| EQUATOR Network | Bản đồ guideline theo loại nghiên cứu | https://www.equator-network.org/library/ |
| SPIRIT 2025 | Protocol thử nghiệm ngẫu nhiên | PMID:40294593; DOI:10.1001/jama.2025.4486 |
| CONSORT 2025 | Báo cáo kết quả thử nghiệm ngẫu nhiên | DOI:10.1136/bmj-2024-081123 |
| PRISMA-P 2015 | Protocol tổng quan hệ thống | DOI:10.1186/2046-4053-4-1 |
| ICH E6(R3) | Quality-by-design và GCP cho thử nghiệm lâm sàng | https://www.ema.europa.eu/en/ich-e6-good-clinical-practice-scientific-guideline |

## Giới hạn phán định
PASS_G1_CONFIRMED chỉ xác nhận thiết kế/reporting map và bộ artifact G1 theo bằng chứng đã ghi; không thay IRB, khóa SAP, dữ liệu thật hoặc thẩm định khoa học độc lập. Checklist báo cáo đánh giá tính đầy đủ của mô tả, không tự chứng minh chất lượng thiết kế hay thực hiện.

> Cần bác sĩ kiểm chứng.
