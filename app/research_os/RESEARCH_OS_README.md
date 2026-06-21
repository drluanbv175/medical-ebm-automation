# Research OS — Branch Riêng (feat/research-os)

**Trạng thái:** Chưa được PO phê duyệt trong Clinical OS roadmap.

**PO Decision (2026-06-21):** Tách Research OS khỏi Sprint 2 release.  
**Branch:** `feat/research-os`  
**Sprint 2 scope:** KHÔNG bao gồm Research OS.

## Modules

- `design_router.py` — Định tuyến thiết kế nghiên cứu (cross-sectional/cohort/RCT/SR)
- `sap_engine.py` — Statistical Analysis Plan engine (G7 gate)
- `reporting_guideline_mapper.py` — Map thiết kế → CONSORT/STROBE/PRISMA/SPIRIT/...
- `causal_inference.py` — Guards: không suy luận nhân quả từ thiết kế quan sát
- `data_lock.py` — Khóa dataset trước phân tích chính
- `study_traceability_matrix.py` — Ma trận đồng bộ mục tiêu–biến–phân tích–bảng
- `methods_review_workflow.py` — Quy trình review methods G0–G9
- `project_registry.py` — Đăng ký đề tài nghiên cứu
- `data_quality_firewall.py` — Tường lửa chất lượng dữ liệu
- `variable_dictionary.py` — Data dictionary / codebook
- `protocol_compiler.py` — Biên soạn protocol tự động
- `reproducibility_runner.py` — Kiểm tra tái lập phân tích
- `pilot.py` — Pilot study tools

## Quan trọng

- Toàn bộ module 100% in-memory, không ORM/SQLAlchemy dependency
- Chưa được test đầy đủ trong Sprint 2 environment
- Không được merge vào main cho đến khi PO phê duyệt
