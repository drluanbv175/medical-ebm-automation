# Báo cáo chất lượng G5

- Hợp đồng: `G5-2026.2`
- Trạng thái: **DRAFT_READY_NEEDS_REAL_DATA**
- Sinh lúc: 2026-10-24T03:17:22.268853+00:00
- Vai đã ký G5: chưa có

## Tiêu chí tự động

| ID | Tiêu chí | Kết quả | Bằng chứng |
|---|---|---|---|
| G5-AUTO-00 | Guardrail liêm chính G5 sạch | PASS | guardrail='✅ PASS' |
| G5-AUTO-01 | Đủ DMP, data dictionary và script QC tái lập | PASS | DMP=True, dictionary=True, cleaning_script=True, quality_script=True |
| G5-AUTO-02 | Data dictionary là CSV có cấu trúc, tên biến duy nhất và không có định danh trực tiếp | PASS | rows=71; placeholder=False |
| G5-AUTO-03 | DMP phủ vòng đời dữ liệu theo ICH E6(R3), có NỘI DUNG thật dưới mỗi mục; hoàn tất khi khoá dữ liệu | PASS | đủ 11 nhãn, mỗi mục có tiêu đề riêng và nội dung thật (capture/QC/audit/privacy/access/backup/retention/lock/sharing) |
| G5-AUTO-04 | Hồ sơ vận hành xác minh access, backup/restore, retention và deviation | REVIEW | valid=False; issues=['status_not_verified', 'access_control_not_verified', 'backup_restore_not_verified', 'retention_plan_not_confirmed', 'protocol_deviations_not_reconciled', 'audit_trail_not_reviewed', 'thieu_bang_chung:access_control_review.evidence_ref', 'thieu_bang_chung:backup_restore_test.evidence_ref', 'thieu_bang_chung:protocol_deviations.log_ref', 'thieu_bang_chung:audit_trail_review.evidence_ref', 'invalid_reviewer_role', 'missing_reviewer_ref', 'invalid_reviewed_at', 'invalid_tested_at', 'invalid_audit_reviewed_at', 'unresolved_placeholder']; sha256=ee6eb2c94494e32d938c62fad4c0fa2ce61863906a2a7976effd2b89713bbaa3 |
| G5-AUTO-04b | Kế hoạch kiểm dữ liệu nguồn (SDV/spot-check) đã khai và hoàn tất, hoặc khai không áp dụng kèm lý do | REVIEW | sdv_chua_khai_hoac_chua_xong: khai source_data_verification {method, fraction_or_n, completed, evidence_ref} hoặc not_applicable_reason |
| G5-AUTO-05 | G2 và G4 đã khóa bằng phê duyệt hợp lệ trước xử lý dữ liệu thật | REVIEW | G2=False; G4=True |
| G5-AUTO-05b | Dữ liệu được nạp/làm sạch SAU khi G2 (IRB) và G4 (SAP) được ký | PASS | chưa có dữ liệu |
| G5-AUTO-06 | Bản raw khử định danh có checksum và chỉ đọc | REVIEW | status=None; hash_match=True; readonly=False |
| G5-AUTO-07 | Làm sạch có provenance, dictionary và checksum khớp | REVIEW | status=None; output_hash_match=True; source_matches_intake=True; dictionary_loaded=None |
| G5-AUTO-07b | Mọi cột của bộ dữ liệu có trong data dictionary và đủ biến bắt buộc | PASS | chưa có dữ liệu |
| G5-AUTO-08 | Query log tồn tại, mọi query đã đóng và hash khớp | REVIEW | rows=0; open=0; issues=['missing_query_log']; hash_match=True; giai_quyet_khop=True |
| G5-AUTO-09 | Manifest khóa liên kết toàn bộ hồ sơ và dataset chỉ đọc | REVIEW | status=None; checksum=True; readonly=False; reviewer_group=None; confirmations=False; checkpoint_hashes=False |
| G5-AUTO-10 | Định tính: bản gỡ băng có TRANSCRIPT_manifest (băm, khử định danh, chỉ đọc, không còn mẫu PII) | PASS | không áp dụng (không phải định tính hoặc chưa có dữ liệu) |
| G5-HUMAN-01 | Người quản trị dữ liệu/PI phê duyệt G5 gắn với hash checkpoint | REVIEW | approval_ledger_G5=False |

## Hành động còn lại

- Hoàn tất G5_OPERATIONAL_READINESS.json bằng bằng chứng vận hành và người quản trị dữ liệu/PI xác nhận.
- Ghi source_data_verification trong G5_OPERATIONAL_READINESS.json (QĐ-10).
- Hoàn tất G2 IRB/IEC và G4 SAP trong approval ledger trước intake/lock.
- Nạp dữ liệu qua import_real_dataset.py; không khóa file ngoài provenance intake.
- Chạy clean_research_dataset.py trên raw readonly với đúng data dictionary G5.
- Đối chiếu nguồn rồi ghi tệp giải quyết query (clean_research_dataset.py --query-resolutions: mã da_sua/xac_nhan_dung/khong_ap_dung_co_ly_do + lý do + người đóng + thời điểm ISO); không tự sửa giá trị.
- Khóa lại qua lock_analysis_dataset.py sau khi mọi điều kiện đã đủ.
- Người có thẩm quyền tự chạy approve_gate.py cho G5 sau khi đọc DATA_LOCK_memo và G5_QUALITY_REPORT; agent không tự phê duyệt.

Cần bác sĩ kiểm chứng.
