# 04 - Migration Plan

## Nguyên tắc

- Không thay thế production pipeline trong một bước.
- V7 chạy song song qua adapter.
- Feature flag mặc định tắt cho mọi hành vi rủi ro.
- Bác sĩ duyệt trước khi phát hành lâm sàng.

## Giai đoạn

1. Phase 0 - Baseline: đã chạy pytest, ruff, compileall, audit, agent sync.
2. Phase 1 - Scaffold: thêm module V7 độc lập, không đổi DB.
3. Phase 2 - Shadow mode: bọc pipeline cũ bằng `packet_from_legacy_job`.
4. Phase 3 - Dashboard read-only: hiển thị registry/gate trạng thái, không auto-apply.
5. Phase 4 - Persistent migration: thêm bảng V7 sau khi schema được duyệt.
6. Phase 5 - Controlled release: bật từng feature flag sau red-team eval và bác sĩ duyệt.

## Rollback

Vì V7 hiện là lớp thêm mới, rollback tối thiểu là tắt feature flags và không import module V7 trong runtime production.
