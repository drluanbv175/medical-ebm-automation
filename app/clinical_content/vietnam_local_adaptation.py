"""Khung hiệu chỉnh bối cảnh Việt Nam cho khuyến nghị."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class VietnamAdaptation:
    formulary: str
    bhyt_or_cost: str
    lab_or_imaging_access: str
    referral_route: str
    local_guideline_alignment: str

    def as_metadata(self) -> Mapping[str, str]:
        return {
            "formulary": self.formulary,
            "bhyt_or_cost": self.bhyt_or_cost,
            "lab_or_imaging_access": self.lab_or_imaging_access,
            "referral_route": self.referral_route,
            "local_guideline_alignment": self.local_guideline_alignment,
        }


def needs_local_confirmation() -> VietnamAdaptation:
    marker = "[CẦN XÁC NHẬN TẠI ĐƠN VỊ]"
    return VietnamAdaptation(
        formulary=f"{marker} danh mục thuốc sẵn có",
        bhyt_or_cost=f"{marker} chi phí/BHYT",
        lab_or_imaging_access=f"{marker} năng lực xét nghiệm/chẩn đoán hình ảnh",
        referral_route=f"{marker} tuyến chuyển viện",
        local_guideline_alignment=f"{marker} đối chiếu phác đồ Bộ Y tế/đơn vị",
    )
