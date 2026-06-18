# Evidence Lifecycle

1. Ingest nguồn.
2. Kiểm tra PMID/DOI/URL.
3. Nếu thiếu truy nguyên: quarantine.
4. Nếu có truy nguyên: đưa vào `EvidenceRegistry`.
5. Xác minh và gắn status `verified`.
6. Tạo claim từ evidence verified.
7. Tạo recommendation card từ claim.
8. Nếu retract/supersede: cập nhật lifecycle và pathway impact.

## Bất biến

- Evidence chính phải có traceability.
- Claim bắt buộc có `evidence_ids`.
- Grade phải có `grade_source` nếu không phải `ungraded`.
- Recommendation card phải nối với claim.
