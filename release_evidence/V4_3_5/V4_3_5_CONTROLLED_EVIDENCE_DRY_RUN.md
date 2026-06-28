# V4.3.5 Controlled Evidence Dry Run

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Mục đích

Dry run này chứng minh hành vi đúng của Evidence Intake và Claim Traceability
với 3 loại evidence source (HUMAN_VERIFIED / UNVERIFIED / RETRACTED) và
3 claim tương ứng, hoàn toàn offline với dữ liệu synthetic.

**KHÔNG** dùng DOI thật, PMID thật, journal thật, author thật, hay bất kỳ
nội dung y khoa thật nào. Mọi metadata là synthetic để kiểm thử logic.

---

## 1. Kịch bản Synthetic

### 1.1 Evidence Sources (PI-provided, HUMAN_PROVIDED_ONLY)

| # | source_id (synthetic) | source_type | verification_state | claim_use_allowed |
|---|----------------------|-------------|-------------------|-------------------|
| S1 | ES-SYNTH-VERIFIED-01 | RCT | HUMAN_VERIFIED | True |
| S2 | ES-SYNTH-UNVERIF-02 | COHORT | UNVERIFIED | False |
| S3 | ES-SYNTH-RETRACT-03 | RCT | RETRACTED | False |

```
S1: title="Synthetic RCT Study Alpha"
    authors="Synthetic Author Group"
    year="2025"
    doi="" pmid=""  ← KHÔNG dùng DOI/PMID thật
    verification_state=HUMAN_VERIFIED
    reviewer_reference=EVIDENCE_CITATION_REVIEWER
    retraction_status=NOT_RETRACTED

S2: title="Synthetic Cohort Study Beta"
    authors="Synthetic Author Group"
    year="2024"
    doi="" pmid=""
    verification_state=UNVERIFIED
    reviewer_reference=EVIDENCE_CITATION_REVIEWER
    retraction_status=NOT_RETRACTED

S3: title="Synthetic RCT Study Gamma (Retracted)"
    authors="Synthetic Author Group"
    year="2023"
    doi="" pmid=""
    verification_state=RETRACTED
    reviewer_reference=EVIDENCE_CITATION_REVIEWER
    retraction_status=RETRACTED_BY_PI_FLAG
```

### 1.2 Draft Claims

| # | claim_id (synthetic) | linked_source | expected_status |
|---|---------------------|---------------|-----------------|
| C1 | CL-SYNTH-SUP-01 | S1 (HUMAN_VERIFIED) | SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE |
| C2 | CL-SYNTH-UNV-02 | S2 (UNVERIFIED) | BLOCKED_UNVERIFIED_EVIDENCE |
| C3 | CL-SYNTH-RET-03 | S3 (RETRACTED) | BLOCKED_RETRACTED_EVIDENCE |

```
C1: claim_text="[SYNTH] Intervention X reduces outcome Y based on verified evidence."
    claim_type=BACKGROUND  ← KHÔNG phải claim y khoa thật

C2: claim_text="[SYNTH] Intervention X may affect outcome Z per unverified source."
    claim_type=BACKGROUND

C3: claim_text="[SYNTH] Source Gamma originally suggested benefit for outcome W."
    claim_type=BACKGROUND
```

---

## 2. Kết quả Dry Run

### 2.1 Evidence Source Ledger

```
evidence_source_ledger.jsonl:
  line 1: {source_id: ES-SYNTH-VERIFIED-01, verification_state: HUMAN_VERIFIED, claim_use_allowed: true}
  line 2: {source_id: ES-SYNTH-UNVERIF-02,  verification_state: UNVERIFIED,      claim_use_allowed: false}
  line 3: {source_id: ES-SYNTH-RETRACT-03,  verification_state: RETRACTED,       claim_use_allowed: false}
```

### 2.2 Claim Traceability Ledger

```
claim_traceability_ledger.jsonl:
  line 1: {claim_id: CL-SYNTH-SUP-01, claim_status: SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE}
  line 2: {claim_id: CL-SYNTH-UNV-02, claim_status: BLOCKED_UNVERIFIED_EVIDENCE}
  line 3: {claim_id: CL-SYNTH-RET-03, claim_status: BLOCKED_RETRACTED_EVIDENCE}
```

### 2.3 D-R8 Gate

```
Input:  3 sources (1 HUMAN_VERIFIED, 1 UNVERIFIED, 1 RETRACTED)
        3 claims  (1 SUPPORTED, 1 BLOCKED_UNVERIFIED, 1 BLOCKED_RETRACTED)

D-R8 check:
  → RETRACTED source detected (ES-SYNTH-RETRACT-03)          ✓ BLOCK trigger
  → Blocked claims detected (CL-SYNTH-UNV-02, CL-SYNTH-RET-03) ✓ BLOCK trigger
  → D-R8 result: FAIL + BLOCK

Expected: D-R8.status = FAIL, D-R8.gate_state = BLOCK
```

### 2.4 Review Queue

```
Evidence review queue (UNVERIFIED + REQUIRES_HUMAN_REVIEW only):
  → ES-SYNTH-UNVERIF-02  reviewer_reference=EVIDENCE_CITATION_REVIEWER
     note: "Evidence verification is manually attested.
            Reviewer identity authentication is not implemented.
            Reviewer independence is not established."

  Note: ES-SYNTH-RETRACT-03 (RETRACTED) KHÔNG vào queue — đã block
```

---

## 3. Kiểm chứng Bất biến

| Bất biến | Kết quả dry run | Đạt/Không |
|----------|----------------|-----------|
| HUMAN_PROVIDED_ONLY | Tất cả sources dùng retrieval_mode=HUMAN_PROVIDED_ONLY | ĐẠT |
| Automation không verify | Không có source nào được verify bởi automation | ĐẠT |
| RETRACTED → BLOCK claim | C3 → BLOCKED_RETRACTED_EVIDENCE | ĐẠT |
| UNVERIFIED → BLOCK claim | C2 → BLOCKED_UNVERIFIED_EVIDENCE | ĐẠT |
| HUMAN_VERIFIED → SUPPORTED | C1 → SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE | ĐẠT |
| D-R8 BLOCK với RETRACTED | D-R8 → FAIL + BLOCK | ĐẠT |
| Review queue đúng target | ES-SYNTH-UNVERIF-02 → EVIDENCE_CITATION_REVIEWER | ĐẠT |
| Ledger append-only | 3 sources × 1 ledger, 3 claims × 1 ledger, không ghi đè | ĐẠT |
| Không PII | Metadata synthetic, không có thông tin định danh người thật | ĐẠT |
| Không DOI/PMID thật | doi="" pmid="" trong mọi source synthetic | ĐẠT |
| Không API/network | Toàn bộ offline, không có HTTP call | ĐẠT |

---

## 4. Giới hạn Dry Run

- Metadata hoàn toàn synthetic — KHÔNG đại diện cho nghiên cứu thật.
- DOI/PMID bỏ trống — chứng minh logic gate, không phải citation thật.
- Reviewer identity authentication KHÔNG được thiết lập.
- Reviewer independence KHÔNG được thiết lập.
- Dry run KHÔNG thay thế kiểm định độc lập trong nghiên cứu thật.

---

## 5. Kết luận

```
Evidence intake control:         PASS (HUMAN_PROVIDED_ONLY enforced)
Evidence source traceability:    PASS (append-only JSONL ledger)
Claim traceability:              PASS (3 status transitions correct)
D-R8 semantic correctness:       PASS (BLOCK on RETRACTED/UNVERIFIED)
Review routing:                  PASS (EVIDENCE_CITATION_REVIEWER)
Automation guard:                PASS (AutoVerificationForbidden enforced)
No real research execution:      CONFIRMED
No API/network calls:            CONFIRMED
```

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
