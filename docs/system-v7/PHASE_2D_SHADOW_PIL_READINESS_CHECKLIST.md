# Phase 2D Shadow Pilot Readiness Checklist

Current readiness: `blocked_review_only`.

- [ ] Pack approval record hợp lệ.
- [ ] Claim quan trọng đã VERIFIED hoặc được ngoại lệ rõ ràng.
- [ ] Không có source retracted/stale chưa xử lý.
- [x] 30 synthetic vignette pass.
- [x] Safety gate pass.
- [x] Red-team pass.
- [x] Dashboard read-only.
- [x] Feature flags rủi ro false.
- [x] Shadow case schema không PII.
- [x] Export manifest safe.
- [ ] Bác sĩ đã duyệt pilot scope.
- [x] Có quy trình xử lý incident.
- [x] Có quy trình stop pilot.
- [x] Có quy trình rollback.

## Stop Criteria

- Phát hiện PII.
- Critical red-flag miss.
- Contraindicated medication allowed.
- Citation mismatch cho claim đang dùng.
- Approval bypass.
- Feature flag bypass.
- Source retracted ảnh hưởng claim.
- Có dấu hiệu output bị dùng như clinical production.

## Stop Actions

When any stop criterion occurs:

1. stop pilot
2. create incident
3. freeze relevant pack version
4. disable shadow mode
5. preserve audit log
6. perform root-cause analysis
7. add regression test

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
