# 02 - Gap Analysis

## Gap đã xử lý trong bản này

- Thiếu control plane: thêm `app/core`.
- Thiếu schema run: thêm `RunPacket`.
- Thiếu policy deterministic: thêm `PolicyEngine`.
- Thiếu approval: thêm `ApprovalCenter`.
- Thiếu release gate: thêm `ReleaseManager`.
- Thiếu audit scrub PII: thêm `AuditLogger`.
- Thiếu evidence/claim separation: thêm `EvidenceRegistry` và `ClaimRegistry`.
- Thiếu safety kernel độc lập: thêm red flag, data sufficiency, medication, contraindication, uncertainty.
- Thiếu ResearchOS gates: thêm SAP lock, data lock, traceability, data-quality firewall.
- Thiếu ChatGPT export policy: thêm export manifest và bridge.

## Gap còn lại

- Chưa nối V7 vào Streamlit production dashboard.
- Chưa có persistent DB migration cho V7 tables.
- Chưa có online citation verification trong V7 module mới; online verification hiện vẫn nằm ở audit/dashboard tools.
- Chưa có full red-team clinical eval set ngoài test deterministic.
- Chưa bật feature flag V7 release.

## Đánh giá mức sẵn sàng

V7 hiện đạt mức scaffold vận hành có test và policy gate. Chưa nên gọi là hệ tự động áp dụng lâm sàng. Mức phù hợp hiện tại: shadow mode, draft mode, review mode.
