# Phase 2B Research Gates

Ngày: 2026-06-18.

## Gates

- Protocol completeness.
- Instrument consistency.
- Dictionary consistency.
- SAP lock readiness.
- Data lock status.
- Syntax version status.
- Expected table alignment.
- Reporting checklist status.

## NO-GO conditions

Không gọi `analysis-ready` nếu:

- SAP chưa lock.
- Data dictionary không đồng bộ.
- Outcome không có biến đo.
- Bảng kết quả ngoài SAP.
- Syntax không version.
- Dataset không rõ status.

## Current pilot status

Test synthetic metadata PASS. Real research pilot vẫn cần PI/bác sĩ duyệt hồ sơ thật và xác nhận không có raw/PII trước khi export.
