# Phase 2A Export Safety

## Module

- `app/core/export_policy.py`
- `app/export_bridge/chatgpt_project_bridge.py`

## Manifest bắt buộc

Manifest Phase 2A có:

- `generated_at`
- `system_version`
- `environment`
- `contains_pii`
- `safe_to_upload`
- `approval_queue_count`
- `failed_runs_count`
- `stale_sources_count`
- `files`
- `sha256`

Mỗi file trong `files` phải có:

- `classification`
- `allowed`
- `reasons`
- `sha256`
- `review_only_label_present` nếu có nội dung recommendation chưa duyệt.
- `needs_review_label_present` nếu có evidence chưa verified.

## Quy tắc chặn

- `contains_pii=true` -> block.
- `safe_to_upload=false` -> block.
- Raw/restricted dataset -> block.
- Missing file hash -> block.
- Missing file classification -> block.
- Stale/retracted source -> block.
- Checksum mismatch -> block.
- Review-only safe context nhưng thiếu nhãn review-only -> block.
- Unverified evidence thiếu nhãn needs-review -> block.
- Recommendation chưa duyệt thiếu nhãn review-only -> block.

Recommendation chưa duyệt không được đánh dấu production; nếu có nhãn review-only hợp lệ, manifest warning `clinical_recommendations_are_review_only`.

## Test coverage

Đã test:

- Manifest thiếu hash.
- Manifest thiếu classification.
- Manifest có PII.
- Raw dataset trong export.
- Recommendation chưa duyệt.
- Safe context review-only thiếu nhãn.
- Source stale/retracted.
- File checksum mismatch.

## Artifact

- `exports/chatgpt_project/v7_manifest.json`
- Stage cuối: 34 files, `safe_to_upload=true`, mọi file có `classification`.
