# Implementation Report

Ngày triển khai: 2026-06-18.

## 20 hạng mục đã thực hiện

1. Chạy baseline trước thay đổi: pytest, ruff, compileall, audit, agent sync.
2. Thêm `app/core/feature_flags.py` với risky flags mặc định `False`.
3. Thêm `app/core/run_packet.py`.
4. Thêm `app/core/run_state_machine.py`.
5. Thêm `app/core/policy_engine.py`.
6. Thêm `app/core/audit_logger.py` có scrub PII-like text.
7. Thêm `app/core/approval_service.py`.
8. Thêm `app/core/release_manager.py`.
9. Thêm `app/core/incident_manager.py`.
10. Thêm retry, idempotency, schema validator, export policy, legacy adapter, change control, shadow mode.
11. Thêm `app/evidence/evidence_registry.py`.
12. Thêm `app/evidence/claim_registry.py`.
13. Thêm citation, freshness, lifecycle, conflict, delta, pathway impact, retraction helpers.
14. Thêm safety kernel: data sufficiency, red flag, medication, contraindication, referral, uncertainty.
15. Thêm clinical content runtime và Clinical Knowledge Pack standard.
16. Thêm Vietnam local adaptation markers.
17. Thêm ResearchOS modules: project, design, protocol, traceability, variables, instruments, causal, SAP, data quality, data lock, reproducibility, guideline map, health score, methods review.
18. Thêm dashboard V7 section registry.
19. Thêm ChatGPT Project bridge và patient education gate.
20. Thêm 15 test V7, bộ docs `docs/system-v7` và staging `exports/chatgpt_project/v7_manifest.json`.

## Kết quả kiểm thử cuối cùng

- Full pytest: 241 passed, 1 warning.
- Full ruff: PASS.
- Full compileall: PASS với `PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache`.
- Agent sync check: PASS.
- EBM system audit: PASS.

## Ghi chú hạ tầng

Root audit tool `tools/audit_ebm_system.py` đã được vá để các subprocess Python dùng cache bytecode trong thư mục tạm có quyền ghi. Điều này giúp audit không FAIL giả do macOS sandbox/OneDrive cache.

## Giới hạn trung thực

Đây là V7 scaffold đã test, không phải autonomous clinical deployment. Cần shadow mode, dashboard wiring, persistent migration và review của bác sĩ trước khi bật clinical release.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
