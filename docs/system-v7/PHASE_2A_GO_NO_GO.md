# Phase 2A GO / NO-GO

## Kết luận

GO FOR SHADOW MODE

## Phạm vi GO

Chỉ GO cho shadow mode/read-only/draft-review có bác sĩ giám sát.

Không GO cho clinical production.
Không GO cho auto-apply.
Không GO cho kê đơn, đổi thuốc, gửi lời dặn bệnh nhân, ghi EMR/HIS, hoặc export dữ liệu hạn chế.

## Điều kiện GO

- Safety focused tests PASS.
- Phase 2A focused tests: 31 passed.
- Full pytest: 268 passed, 1 warning.
- Ruff: PASS.
- Compileall: PASS.
- Agent sync: PASS.
- EBM audit: PASS.
- `critical_red_flag_miss = 0`.
- `emergency_referral_miss = 0`.
- `contraindicated_medication_allowed = 0`.
- `missing_required_data_silently_assumed = 0`.
- `unverified_evidence_released = 0`.
- `recommendation_without_claim_id_released = 0`.
- `stale_recommendation_released = 0`.
- `recommendation_without_approval_released = 0`.
- `approval_bypass = 0`.
- `pii_leakage = 0`.
- Citation verification có trạng thái an toàn.
- Dashboard V7 chỉ read-only.
- Export safety focused tests PASS.
- Clinical release flags vẫn false.
- Migration dry-run: 13 governance tables, `destructive=False`.
- ChatGPT manifest: 34 files, `safe_to_upload=true`.

## Feature flags

Vẫn false:

- `v7_clinical_release`
- `v7_patient_education_export`
- `v7_emr_write`
- `v7_production_pathway`
- `v7_auto_apply_recommendations`

Chỉ có thể bật sau duyệt:

- `v7_read_only_dashboard`
- `v7_shadow_mode`

## Rủi ro còn lại

- Chưa chạy migration production.
- Citation verifier mới có adapter protocol và tests deterministic; cần nối live adapter từng nguồn trước khi vận hành online.
- Dashboard read-only mới hiển thị khung governance; chưa có dữ liệu persisted nếu chưa migration.
- Shadow mode cần bác sĩ duyệt tập ca/đề tài synthetic tiếp theo.

## Nội dung cần bác sĩ duyệt

- Duyệt danh sách cờ đỏ tối thiểu.
- Duyệt migration lên DB thật nếu cần.
- Duyệt tiêu chí `GO FOR SHADOW MODE`.
- Duyệt manifest export trước khi tải lên ChatGPT Project.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
