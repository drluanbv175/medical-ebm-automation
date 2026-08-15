# Incident Response

## Loại sự cố

- PII leakage.
- Citation hallucination.
- Dashboard integrity fail.
- Red flag bị bỏ qua.
- Research analysis chạy trước data lock.
- Export chứa raw dataset.

## Luồng xử trí

1. Mở incident bằng `IncidentManager.open`.
2. Đặt severity.
3. Tạm tắt feature flag liên quan.
4. Quarantine output/evidence bị ảnh hưởng.
5. Ghi audit log.
6. Review nguyên nhân.
7. Chỉ đóng incident khi có test hoặc guardrail bổ sung.
