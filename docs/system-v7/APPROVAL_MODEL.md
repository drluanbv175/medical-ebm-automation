# Approval Model

## Vai trò có quyền duyệt

- `physician`: đầu ra lâm sàng.
- `principal_investigator`: nghiên cứu.
- `system_owner`: thay đổi vận hành hệ thống.

## Luồng

1. Agent tạo draft.
2. `ApprovalCenter.submit`.
3. Reviewer duyệt hoặc từ chối.
4. `ReleaseManager.release` kiểm tra approval và policy.
5. Audit log ghi sự kiện đã khử PII.

Không có approval thì không phát hành lâm sàng.
