"""Selection gate cho Phase 2C real Clinical Knowledge Pack pilot."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ALLOWED_PHASE_2C_PACKS = {
    "hypertension_adult_outpatient",
    "adult_asthma_outpatient",
    "type_2_diabetes_outpatient",
}


@dataclass(frozen=True)
class Phase2CPackSelection:
    selected_pack: Optional[str]
    physician_approval_required: bool = True
    approval_record_path: Optional[str] = None
    approval_status: str = "missing"
    allowed_packs: List[str] = field(default_factory=lambda: sorted(ALLOWED_PHASE_2C_PACKS))

    @property
    def approved_for_real_pack_build(self) -> bool:
        return (
            self.selected_pack in ALLOWED_PHASE_2C_PACKS
            and self.physician_approval_required
            and bool(self.approval_record_path)
            and self.approval_status == "approved"
        )

    @property
    def blocked_reasons(self) -> List[str]:
        reasons: List[str] = []
        if not self.selected_pack:
            reasons.append("selected_pack_missing")
        elif self.selected_pack not in ALLOWED_PHASE_2C_PACKS:
            reasons.append("selected_pack_not_allowed")
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 15) —
        # approved_for_real_pack_build đòi physician_approval_required
        # phải True, nhưng blocked_reasons trước đây không hề kiểm field
        # này: khi curator/YAML tắt nhầm cờ này (physician_approval_
        # required=False) trong khi mọi field khác hợp lệ, pathway build
        # vẫn bị chặn ĐÚNG (an toàn) nhưng blocked_reasons trả về RỖNG —
        # người xem log/CI không biết vì sao bị chặn.
        if not self.physician_approval_required:
            reasons.append("physician_approval_required_flag_is_false")
        if not self.approval_record_path:
            reasons.append("approval_record_missing")
        elif self.approval_status != "approved":
            reasons.append(f"approval_not_approved:{self.approval_status}")
        return reasons


def _scalar(value: str) -> Optional[str]:
    cleaned = value.strip().strip('"').strip("'")
    if cleaned in {"", "null", "None"}:
        return None
    return cleaned


def load_phase_2c_selection(path: Path) -> Phase2CPackSelection:
    selected_pack: Optional[str] = None
    approval_required = True
    approval_record_path: Optional[str] = None
    approval_status = "missing"
    allowed: List[str] = []
    in_allowed = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("allowed_packs:"):
            in_allowed = True
            continue
        if in_allowed and line.startswith("- "):
            allowed.append(str(_scalar(line[2:]) or ""))
            continue
        in_allowed = False
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key == "selected_pack":
            selected_pack = _scalar(value)
        elif key == "physician_approval_required":
            approval_required = str(_scalar(value)).lower() == "true"
        elif key == "approval_record_path":
            approval_record_path = _scalar(value)
    if approval_record_path:
        record_path = Path(approval_record_path)
        if not record_path.is_absolute():
            record_path = path.parent.parent / record_path
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            approval_status = str(record.get("status") or "missing")
        except (OSError, json.JSONDecodeError):
            approval_status = "unreadable"
    return Phase2CPackSelection(
        selected_pack=selected_pack,
        physician_approval_required=approval_required,
        approval_record_path=approval_record_path,
        approval_status=approval_status,
        allowed_packs=allowed or sorted(ALLOWED_PHASE_2C_PACKS),
    )
