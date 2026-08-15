# 05 - Baseline Test Report

Ngày chạy: 2026-06-18.

## Trước thay đổi V7

| Lệnh | Kết quả |
|---|---|
| `/Users/nguyenluan/.ebm-venv/bin/python -m compileall -q app scripts tests` | PASS |
| `/Users/nguyenluan/.ebm-venv/bin/python -m pytest` | 226 passed, 1 warning |
| `/Users/nguyenluan/.ebm-venv/bin/ruff check` | PASS |
| `python3 ../tools/audit_ebm_system.py` | PASS |
| `python3 ../tools/sync_agents_to_codex.py --check` | PASS |

## Sau module V7 bước đầu

| Lệnh | Kết quả |
|---|---|
| `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache ... compileall app/core ...` | PASS |
| `pytest tests/test_v7_*` | 15 passed |
| `ruff check app/core ... tests/test_v7_*` | PASS sau auto-fix import |

## Kiểm định cuối toàn repo sau V7

| Lệnh | Kết quả |
|---|---|
| `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m compileall -q app scripts tests` | PASS |
| `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m pytest` | 241 passed, 1 warning |
| `/Users/nguyenluan/.ebm-venv/bin/ruff check` | PASS |
| `python3 ../tools/sync_agents_to_codex.py --check` | PASS |
| `python3 ../tools/audit_ebm_system.py` | PASS |

## Phase 2A cuối cùng

| Lệnh | Kết quả |
|---|---|
| `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m compileall -q app scripts tests` | PASS |
| `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m pytest` | 259 passed, 1 warning |
| `/Users/nguyenluan/.ebm-venv/bin/ruff check` | PASS |
| `python3 ../tools/sync_agents_to_codex.py --check` | PASS |
| `python3 ../tools/audit_ebm_system.py` | PASS |

## Ghi chú môi trường

Python hệ thống thiếu `sqlalchemy`, vì vậy baseline chính thức dùng venv `~/.ebm-venv` theo `AGENTS.md`.

Audit tool root đã được cập nhật để đặt `PYTHONPYCACHEPREFIX` mặc định vào thư mục tạm, tránh lỗi quyền ghi bytecode trên macOS/OneDrive sandbox.
