# Migration Guide

## Bọc job cũ bằng V7

```python
from app.core.legacy_adapter import packet_from_legacy_job
from app.core.run_packet import Lane

packet = packet_from_legacy_job(
    lane=Lane.CLINICAL,
    objective="Draft EBM update",
    legacy_payload={"topic": "cerebrovascular disease"},
    trace_id="pmid:12345678",
)
```

## Tạo evidence và claim

```python
from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus
from app.evidence.claim_registry import ClaimRegistry

evidence = EvidenceRegistry()
record = evidence.add(
    title="Verified source",
    source="PubMed",
    evidence_type="guideline",
    identifiers={"pmid": "12345678"},
    status=EvidenceStatus.VERIFIED,
)
claim = ClaimRegistry(evidence).register_claim(
    text="Draft claim",
    evidence_ids=[record.evidence_id],
)
```

## Không làm trong phase này

- Không migrate DB.
- Không bật auto-apply.
- Không export dataset thô.
