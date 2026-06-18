# Phase 2A Dashboard Read-only

## Module

- `app/dashboard/v7_readonly.py`
- Nối vào tab 13 trong `app/dashboard/main.py`: `V7 Shadow Read-only`

## Màn hình bắt buộc

Tab V7 hiển thị read-only:

- Run Monitor.
- Approval Inbox.
- Evidence Registry.
- Claim Registry.
- Citation Verification Status.
- Evidence Freshness.
- Conflict Queue.
- Clinical Safety Queue.
- Clinical Decision Record Explorer.
- Research Lock Status.
- Incident Center.
- Feature Flag Status.
- Shadow Mode Status.
- ChatGPT Export Safety.

## Trạng thái hiển thị

- Environment.
- Feature flags.
- Approval/governance schema status.
- Clinical release blocked reason.
- Shadow readiness reason.
- Citation/freshness status.
- Last updated.
- Run/release ID nếu có.

## Cấm trong dashboard V7

- Không có nút auto-apply.
- Không kê đơn.
- Không gửi lời dặn bệnh nhân.
- Không ghi EMR/HIS.
- Không edit evidence trực tiếp.
- Không có nút enable release.
- Không có nút write EMR/HIS.

Mỗi màn hình trong danh sách bắt buộc phải hiển thị hoặc expose trong row read-only: `environment`, `approval_status`, `citation_status`, `freshness_status`, `blocked_reason`, `feature_flags`, `shadow_mode`, `last_updated`, `run_id`, `release_id`.
