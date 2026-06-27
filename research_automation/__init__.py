"""
research_automation — Offline automation operations layer (V4.3.2).

Tự động điều phối workflow nghiên cứu SYNTHETIC trên research_studio + runtime:
intake → route → tạo DRAFT theo template → quality gates → review queue → schedule.

OFFLINE-ONLY · DETERMINISTIC · SYNTHETIC-ONLY. KHÔNG API/network/SDK/Local Model.
KHÔNG PII/dữ liệu thật/eHospital. KHÔNG tự nộp/approval người giả/đổi NO-GO.

Bất biến: mọi artifact draft_only + human_review_required; mọi output DRAFT.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

QUALIFICATION = "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE"
AUTOMATION_BANNER = (
    "Offline automation — Development / synthetic internal QA only. "
    "All outputs are DRAFT — REQUIRE HUMAN REVIEW. Live Agent behavior NOT VERIFIED."
)
