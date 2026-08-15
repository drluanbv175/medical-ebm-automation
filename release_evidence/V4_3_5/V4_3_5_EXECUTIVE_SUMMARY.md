# V4.3.5 Executive Summary — Evidence Intake & Claim Traceability

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Branch:** `feat/v4-3-5-evidence-intake-claim-traceability`  
**Base:** `v4.3.4-frozen` (commit `101ca08a`)  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Tóm tắt một dòng

V4.3.5 bổ sung **Evidence Intake & Claim Traceability** — lớp kiểm soát đảm bảo mọi claim
trong dossier phải liên kết với evidence đã được human verified, và tự động block claim dùng
evidence RETRACTED hoặc UNVERIFIED.

---

## Những gì được thêm

### 1 source module mới
**`research_project/project_claim_traceability.py`** (~230 dòng):
- `ClaimType` enum — 6 loại claim (BACKGROUND/METHODS/SAFETY/GUIDELINE/STATISTICAL/REPORTING)
- `ClaimStatus` enum — 6 trạng thái (REQUIRE_HUMAN_EVIDENCE_INPUT/BLOCKED_*/SUPPORTED/…)
- `ClaimRecord` dataclass — 13 trường, append-only
- `ClaimTraceabilityLedger` — ghi `claim_traceability_ledger.jsonl` append-only
- `compute_claim_status()` — tính trạng thái từ evidence verification states
- `register_claim()` — đăng ký claim + liên kết sources + tính status tự động
- `get_claim_audit()` — trả audit trail, kèm disclaimer

### 1 source module được mở rộng
**`research_project/project_evidence_intake.py`** (V4.3.5 additions, ~160 dòng mới):
- `RetrievalMode` enum — HUMAN_PROVIDED_ONLY (hợp lệ) + AUTO_RETRIEVED/MODEL_GENERATED/
  WEB_SCRAPED/API_FETCHED (bị block ở EvidenceSourceLedger.add())
- `VerificationState` enum — UNVERIFIED/HUMAN_VERIFIED/REQUIRES_HUMAN_REVIEW/RETRACTED/EXCLUDED
- `EvidenceSource` dataclass — 20 trường đầy đủ traceability
- `EvidenceSourceLedger` — ghi `evidence_source_ledger.jsonl` append-only
- `ForbiddenRetrievalMode`, `AutoVerificationForbidden` — exception guards
- `add_evidence_source()` — factory với PII guard + automation verification guard
- `get_evidence_review_queue()` — trả danh sách source cần reviewer xem xét

### D-R8 enhanced (backward-compatible)
**`research_project/project_qa_runner.py`** — D-R8 tách 2 nhánh:
- Nếu `evidence_source_ledger.jsonl` tồn tại → new V4.3.5 logic
- Nếu không → legacy `evidence_manifest.csv` logic (backward compat V4.3.3)

### 4 CLI subcommand mới (trong `project_cli.py`)

| Subcommand | Chức năng |
|------------|-----------|
| `project-evidence-import` | Nhập evidence source vào ledger |
| `project-evidence-list` | Liệt kê sources và review queue |
| `project-claim-register` | Đăng ký claim, liên kết sources |
| `project-claim-audit` | Xem audit trail claim |

### 1 test file mới
**`tests/test_v4_3_5_evidence_claim_traceability.py`** — 20 test, 100% pass.

---

## Bất biến cốt lõi được đảm bảo

| Bất biến | Cơ chế |
|----------|--------|
| Chỉ HUMAN_PROVIDED_ONLY | `EvidenceSourceLedger.add()` → `ForbiddenRetrievalMode` |
| Automation không verify | `AutoVerificationForbidden` khi `automation_caller=True + HUMAN_VERIFIED` |
| RETRACTED block tất cả | D-R8 → FAIL + BLOCK khi có RETRACTED source |
| Claim dùng UNVERIFIED → BLOCK | `compute_claim_status()` → BLOCKED_UNVERIFIED_EVIDENCE |
| Ledger append-only | Chỉ có `add()` — không có `delete()` hay `update()` |
| Không PII | Guard trong `add_evidence_source()` và `register_claim()` |
| No auto-citation | Hệ thống KHÔNG tự tạo DOI/PMID/title — chỉ nhận từ PI |
| Review routing | Tất cả evidence sources định tuyến về `EVIDENCE_CITATION_REVIEWER` |

---

## Kết quả kiểm thử

| Suite | Kết quả |
|-------|---------|
| V4.3.5 (20 test) | **20 PASS** |
| Full suite | **794 PASS, 7 SKIP** — 0 regression |
| Dry run (synthetic) | **PASS** — 3 sources, 3 claims, D-R8 FAIL/BLOCK đúng |

---

## Phạm vi KHÔNG thay đổi

- MRAQ score không thay đổi
- Qualification: vẫn NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
- 19 artifact schema không thay đổi
- 14 quality gate D-R1..D-R7, D-R9..D-R15 không thay đổi
- D-R8 legacy logic (CSV manifest) được GIỮ NGUYÊN cho backward compat
- Không thêm API call, network dependency, hay auto-citation

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
