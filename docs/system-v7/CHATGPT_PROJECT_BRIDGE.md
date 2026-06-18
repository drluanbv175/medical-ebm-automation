# ChatGPT Project Bridge

## Mục tiêu

Xuất gói dùng cho ChatGPT Project mà không mang theo PII, secrets, hoặc dataset thô.

## Module

- `app/export_bridge/chatgpt_project_bridge.py`
- `app/core/export_policy.py`

## Chính sách

Blocked:

- `.env`
- `secrets.json`
- `credentials.json`
- `.db`, `.sqlite`, `.parquet`, `.sav`, `.dta`, `.sas7bdat`
- text có mẫu PII

Allowed:

- agent markdown đã khử định danh
- docs
- schema
- dashboard HTML đã verify
- manifest hash

Feature flag `v7_chatgpt_project_export` mặc định tắt.

## Artifact hiện có

- `exports/chatgpt_project/README.md`
- `exports/chatgpt_project/v7_manifest.json`

Manifest hiện stage 24 file tài liệu V7 và tất cả được policy đánh dấu `allowed: true`.
