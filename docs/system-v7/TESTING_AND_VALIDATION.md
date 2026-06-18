# Testing And Validation

## Test mới

- `tests/test_v7_core_control_plane.py`
- `tests/test_v7_evidence_safety_research.py`
- `tests/test_v7_export_bridge_and_clinical_runtime.py`

## Coverage hành vi

- Feature flags mặc định an toàn.
- State machine chặn transition sai.
- Policy chặn PII, thiếu traceability, thiếu citation, chưa duyệt.
- Audit logger redact PII-like text.
- Release cần approval và flag.
- Evidence thiếu truy nguyên bị quarantine.
- Claim cần evidence verified và grade source.
- Safety phát hiện cờ đỏ, thiếu dữ liệu, cặp thuốc nguy cơ.
- ResearchOS khóa SAP/data trước phân tích chính thức.
- ChatGPT export cần flag và manifest.

## Lệnh

```bash
PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python -m pytest
/Users/nguyenluan/.ebm-venv/bin/ruff check
python3 ../tools/audit_ebm_system.py
python3 ../tools/sync_agents_to_codex.py --check
```
