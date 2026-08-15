# Phase 2B Test Database Migration

Ngày: 2026-06-18.

## Script

- `scripts/phase_2b_migrate_test_db.py`
- `scripts/phase_2b_seed_governance_test_data.py`

## Scope

Chỉ dùng isolated SQLite test database: `sqlite:////private/tmp/ebm_phase_2b_governance.db`. Không chạm production DB.

## Tables

Migration test tạo đủ 13 bảng governance V7:

- `run_packets`
- `approval_records`
- `audit_events`
- `incident_records`
- `evidence_records_v2`
- `claim_records`
- `recommendation_cards`
- `clinical_decision_records`
- `research_lock_records`
- `release_manifests`
- `export_manifests`
- `feature_flag_audit`
- `citation_verification_records`

## Result

PASS:

- Apply migration trên empty test DB.
- Seed synthetic governance data không PII.
- Tạo RunPacket.
- Valid transition applied.
- Invalid direct release transition blocked.
- Approval record created.
- Release chưa approved blocked.
- Release sau approved allowed trong test environment.
- Incident created.
- Rollback event audit created.
- Audit trail present.

Cần bác sĩ/system owner duyệt riêng nếu muốn chạy migration thật.
