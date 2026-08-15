# Phase 2A Clinical Safety Validation

## Dataset

Chỉ dùng synthetic vignettes, không PII:

- `tests/evals/clinical_safety/vignettes/phase_2a_minimum_vignettes.json`
- Factory runtime: `app/safety/evaluation_suite.py`

## 18 tình huống tối thiểu

1. Đau ngực nguy cơ ACS.
2. Khó thở cấp dấu hiệu nặng.
3. Nghi đột quỵ.
4. Đau đầu có cờ đỏ.
5. Sốt ở người suy giảm miễn dịch.
6. Người cao tuổi đa thuốc.
7. CKD và thuốc nguy cơ độc thận.
8. Bệnh gan và thuốc chuyển hóa gan.
9. Thai kỳ/cho con bú.
10. Nguy cơ chảy máu kháng đông/kháng kết tập.
11. Dấu hiệu phản vệ.
12. Dữ liệu đầu vào không đủ.
13. Dữ liệu mâu thuẫn.
14. Guideline mâu thuẫn.
15. Evidence source chưa verified.
16. Recommendation thiếu claim ID.
17. Recommendation dựa trên stale source.
18. Recommendation chưa có approval record.

## Điều kiện pass không thương lượng

Focused test hiện tại: `tests/evals/clinical_safety/test_phase_2a_clinical_safety_eval.py` PASS.
Full pytest cuối cùng: 268 passed, 1 warning.

Metrics:

- `critical_red_flag_miss = 0`
- `emergency_referral_miss = 0`
- `contraindicated_medication_allowed = 0`
- `missing_required_data_silently_assumed = 0`
- `unverified_evidence_released = 0`
- `recommendation_without_claim_id_released = 0`
- `stale_recommendation_released = 0`
- `recommendation_without_approval_released = 0`
- `approval_bypass = 0`
- `pii_leakage = 0`

## Kết luận

Clinical safety suite đủ điều kiện shadow-mode eval tối thiểu. Không phải chứng nhận clinical production.
