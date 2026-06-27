"""
research_studio — Offline Medical Research Studio (V4.3).

Domain layer NẰM TRÊN control-plane offline đã hardened (runtime/). Mô phỏng
vòng đời nghiên cứu y khoa bằng synthetic fixtures, có kiểm soát qua
ControlledOrchestrator. KHÔNG API, KHÔNG network, KHÔNG dữ liệu thật/PII.

Bất biến toàn cục:
  - draft_only = True cho MỌI artifact.
  - human_review_required = True.
  - not_valid_for_real_research = True.
  - Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

QUALIFICATION = "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE"
STUDIO_BANNER = (
    "Development / synthetic internal QA only. "
    "All outputs are DRAFT — REQUIRE HUMAN REVIEW. "
    "Live Agent behavior NOT VERIFIED."
)
NOT_VALID_FOR_REAL_RESEARCH = True
