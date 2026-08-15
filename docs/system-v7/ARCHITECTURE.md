# Architecture

```mermaid
flowchart TD
    A["Agent request"] --> B["RunPacket"]
    B --> C["PolicyEngine"]
    C --> D["Evidence / Claim Registry"]
    C --> E["Safety Kernel"]
    C --> F["ResearchOS Gates"]
    D --> G["ApprovalCenter"]
    E --> G
    F --> G
    G --> H["ReleaseManager"]
    H --> I["Dashboard / ChatGPT Export / Patient Education"]
    C --> J["AuditLogger"]
```

## Module map

- `app/core`: control plane.
- `app/evidence`: evidence and claim lifecycle.
- `app/safety`: safety kernel.
- `app/clinical_content`: clinical knowledge pack and draft runtime.
- `app/research_os`: research operating system.
- `app/export_bridge`: ChatGPT Project export.
- `app/patient_education`: patient education gate.
- `app/dashboard/v7_registry.py`: dashboard section contract.
