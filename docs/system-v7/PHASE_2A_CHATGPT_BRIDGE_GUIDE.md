# Phase 2A ChatGPT Bridge Guide

Ngày: 2026-06-18.

## Mục tiêu

Bridge cho phép đưa bối cảnh hệ Agent, dashboard và tài liệu V7 sang ChatGPT Project ở dạng safe context. Bridge không đưa raw dataset, PII, secret, hoặc recommendation production.

## Module

- `app/core/export_policy.py`
- `app/export_bridge/chatgpt_project_bridge.py`

## Manifest bắt buộc

Manifest phải có:

- `generated_at`
- `system_version`
- `environment`
- `contains_pii`
- `safe_to_upload`
- `approval_queue_count`
- `failed_runs_count`
- `stale_sources_count`
- `recommendation_unapproved_count`
- `retracted_sources_count`
- `files`
- `sha256`

Mỗi file phải có `classification`, `allowed`, `reasons`, `sha256`. File review-only cần `review_only_label_present`; evidence chưa verified cần `needs_review_label_present`.

## Quy tắc block

- PII-like text.
- Raw/restricted dataset.
- Secret file.
- Missing hash.
- Checksum mismatch.
- Missing classification.
- Stale/retracted source.
- Unapproved recommendation thiếu nhãn review-only.
- Review-only safe context thiếu nhãn.
- Unverified evidence thiếu nhãn needs-review.

## Quy trình an toàn

1. Chỉ chọn file `.md`, `.txt`, `.html`, `.json`, `.toml`, `.py` đã được phân loại safe context.
2. Sinh manifest bằng `prepare_chatgpt_project_export`.
3. Chạy `validate_project_manifest`.
4. Chỉ upload khi `valid=true`, `safe_to_upload=true`, `contains_pii=false`.
5. Không upload raw DB, dataset, `.env`, credential, hoặc file bệnh nhân.

## Giới hạn

ChatGPT bridge không thay thế approval của bác sĩ. Nội dung đưa sang ChatGPT chỉ dùng để review, học thuật, tổng hợp hoặc hỗ trợ vận hành hệ thống. Không dùng để gửi bệnh nhân hoặc ghi EMR/HIS.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
