# Change Control Policy

## Quy tắc

- Mọi thay đổi V7 có `ChangeRequest`.
- Risk `high` cần rollback plan rõ.
- Không sửa generated TOML agent bằng tay.
- Không thay đổi dashboard template riêng lẻ nếu thay đổi cần áp dụng toàn hệ.
- Không bật feature flag rủi ro trong cùng PR với migration lớn.

## Module

- `app/core/change_control.py`

## Kiểm tra trước merge

- `compileall`
- `pytest`
- `ruff check`
- `../tools/audit_ebm_system.py`
- `../tools/sync_agents_to_codex.py --check`
