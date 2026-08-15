# 03 - Compatibility Matrix

| Thành phần | Hiện tại | V7 mới | Tương thích |
|---|---|---|---|
| Python | venv `~/.ebm-venv`, Python 3.9.6 | Code dùng `from __future__ import annotations`, không dùng cú pháp 3.10-only | Có |
| Tests | Pytest 226 nền | Thêm 15 test V7 | Có |
| Lint | Ruff | Ruff sạch với module mới | Có |
| DB | SQLAlchemy models hiện hữu | V7 hiện in-memory/dataclass | Không phá DB |
| Dashboard | Streamlit + HTML Evidence Workbench | `v7_registry` mô tả section/gate | Chưa nối runtime |
| Agents | `.claude/agents` và `.Codex/agents` | Giữ đồng bộ bằng tool root | Có |
| Export ChatGPT | ZIP/export cũ ở root | Bridge có manifest và policy | Có ở mức module |

## Lưu ý compileall

Trong sandbox Codex, Python 3.9 có thể cố ghi bytecode vào `~/Library/Caches/com.apple.python`, ngoài quyền ghi. Khi kiểm tra, dùng:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m compileall -q app scripts tests
```
