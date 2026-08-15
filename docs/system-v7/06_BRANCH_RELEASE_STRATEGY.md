# 06 - Branch Release Strategy

Repo hiện ở branch `main`. Chiến lược release V7 đề xuất:

1. Giữ V7 trong module riêng.
2. Không bật feature flag rủi ro trên `main` cho tới khi shadow mode đạt chuẩn.
3. Mỗi lần nối runtime production phải có:
   - test mới,
   - migration/rollback note,
   - approval của system owner/bác sĩ,
   - audit log không PII.
4. Nếu dùng branch sau này, đặt tên `feature/ebm-os-v7-*`.
5. Release đầu tiên chỉ là `v7_scaffold_shadow_ready`, không phải clinical autonomous release.
