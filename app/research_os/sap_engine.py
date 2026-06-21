"""Statistical Analysis Plan engine — SAP lock + data lock guard (G7)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import uuid4


class SapStatus(str, Enum):
    DRAFT = "draft"
    LOCKED = "locked"


@dataclass(frozen=True)
class StatisticalAnalysisPlan:
    """SAP bất biến. Dùng lock_sap() để khoá — không bao giờ sửa sau khoá."""
    sap_id: str
    primary_analysis: str
    secondary_analyses: List[str] = field(default_factory=list)
    sensitivity_analyses: List[str] = field(default_factory=list)
    missing_data_strategy: str = "complete_case"
    significance_level: float = 0.05
    status: SapStatus = SapStatus.DRAFT

    def can_run_official_analysis(self, data_locked: bool) -> bool:
        """Phân tích chính chỉ được phép khi SAP đã khoá VÀ dữ liệu đã khoá."""
        return self.status is SapStatus.LOCKED and data_locked

    def validate(self) -> List[str]:
        """Trả danh sách vấn đề. [] = không có vấn đề."""
        issues: List[str] = []
        if not self.primary_analysis or not self.primary_analysis.strip():
            issues.append("primary_analysis không được để trống")
        if not (0 < self.significance_level < 1):
            issues.append(f"significance_level không hợp lệ: {self.significance_level}")
        return issues


def create_sap(
    primary_analysis: str,
    secondary_analyses: List[str] | None = None,
    sensitivity_analyses: List[str] | None = None,
    missing_data_strategy: str = "complete_case",
    significance_level: float = 0.05,
) -> StatisticalAnalysisPlan:
    """Factory tạo SAP ở trạng thái DRAFT với ID tự động."""
    sap = StatisticalAnalysisPlan(
        sap_id=f"sap_{uuid4().hex[:12]}",
        primary_analysis=primary_analysis,
        secondary_analyses=list(secondary_analyses or []),
        sensitivity_analyses=list(sensitivity_analyses or []),
        missing_data_strategy=missing_data_strategy,
        significance_level=significance_level,
    )
    issues = sap.validate()
    if issues:
        raise ValueError(f"SAP không hợp lệ: {'; '.join(issues)}")
    return sap


def lock_sap(sap: StatisticalAnalysisPlan) -> StatisticalAnalysisPlan:
    """Khoá SAP — trả bản sao bất biến với status=LOCKED. Ném nếu không hợp lệ."""
    issues = sap.validate()
    if issues:
        raise ValueError(f"Không thể khoá SAP không hợp lệ: {'; '.join(issues)}")
    return StatisticalAnalysisPlan(
        sap_id=sap.sap_id,
        primary_analysis=sap.primary_analysis,
        secondary_analyses=list(sap.secondary_analyses),
        sensitivity_analyses=list(sap.sensitivity_analyses),
        missing_data_strategy=sap.missing_data_strategy,
        significance_level=sap.significance_level,
        status=SapStatus.LOCKED,
    )
