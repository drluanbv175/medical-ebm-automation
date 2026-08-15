# Phase 3A Risk Register

| ID | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| CC-R1 | Synthetic shadow output bị hiểu nhầm là clinical plan | High | Label `shadow_only`, no active clinical plan status |
| CC-R2 | PII lọt vào synthetic dataset | High | PolicyEngine + PII tests + synthetic ID only |
| CC-R3 | Risk draft RED bị hiểu là quyết định cấp cứu | High | Message: physician review required, no auto referral |
| CC-R4 | Care-plan draft approved khi thiếu evidence/claim | High | Evidence gate blocks approval |
| CC-R5 | Dashboard vô tình có button bật risky flags | High | Read-only snapshot only |
| CC-R6 | Audit event thiếu trong workflow | Medium | Service wrapper logs each state-changing action |
| CC-R7 | Export chứa row-level data | High | Aggregate export only + policy validation |
