# 00 - Audit Current State

Ngày audit: 2026-06-18.

## Kết luận trung thực

`medical-ebm-automation/` đã là dự án sống có pipeline EBM, dashboard, scheduler, nguồn mở và test nền mạnh. Trước khi nâng cấp V7, baseline đạt:

- `pytest`: 226 passed, 1 warning.
- `ruff check`: PASS.
- `compileall`: PASS khi chạy bằng venv chuẩn.
- `../tools/audit_ebm_system.py`: PASS.
- `../tools/sync_agents_to_codex.py --check`: PASS, 48/48 agent Claude và Codex đồng bộ.

## Thành phần hiện hữu

- `app/services/`: ingestion, normalization, filtering, synthesis, pipeline, run_state.
- `app/sources/`: PubMed, Crossref, Europe PMC, OpenAlex, Semantic Scholar, openFDA, guideline/RSS.
- `app/models/`: evidence, pipeline run, research, clinical score, changelog/source log.
- `app/reports/`: evidence workbench, weekly EBM, safety reports, exporters.
- `app/dashboard/`: Streamlit dashboard hiện hữu và integrations panel.
- `app/research/`: manager, dossier, checklists.
- `tests/`: 226 test nền.

## Rủi ro còn lại trước V7

- Chưa có control plane chung cho mọi lần chạy agent.
- Chưa có `RunPacket` thống nhất cho Claude Code và Codex.
- Chưa có approval service độc lập cho phát hành lâm sàng/nghiên cứu.
- Chưa có claim registry tách khỏi evidence item.
- Chưa có policy engine chặn PII, thiếu traceability, chưa duyệt, chưa khóa SAP/data.
- Chưa có ChatGPT Project export manifest có policy.

## Quyết định triển khai

V7 được triển khai như lớp song song trong `app/core`, `app/evidence`, `app/safety`, `app/clinical_content`, `app/research_os`, `app/export_bridge`, `app/patient_education`. Pipeline cũ không bị thay thế.
