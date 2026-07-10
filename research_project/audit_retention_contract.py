"""
Hợp đồng giao diện adapter lưu trữ audit bất biến cho R1.3.

Chỉ chứa định nghĩa interface và adapter giả lập offline.
KHÔNG kết nối AWS S3 / Azure Blob / GCP / thiết bị WORM thật.
KHÔNG cung cấp lưu trữ WORM thật, sao lưu ngoài hệ thống, hay giữ pháp lý thật.
"""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

# ── Hằng số phụ thuộc chưa triển khai ─────────────────────────────────────

PROD_WORM_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires external WORM-capable storage provider "
    "(AWS S3 Object Lock / Azure Blob Immutability / GCP WORM / on-premises)"
)
PROD_BACKUP_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires off-system backup service in separate region/account"
)
PROD_LEGAL_HOLD_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires institutional legal hold management capability"
)

LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"

DISCLAIMER_FAKE_WORM = (
    "Synthetic simulation — NOT WORM — not for production audit trail. "
    "Cần bác sĩ kiểm chứng."
)
DISCLAIMER_REAL_WORM = (
    "Production WORM — requires human verification of provider compliance. "
    "Cần bác sĩ kiểm chứng."
)

PROVIDER_NAME_FAKE = "FAKE_WORM_OFFLINE_SIMULATION"


@dataclass
class WriteReceipt:
    """
    Biên lai xác nhận ghi sự kiện audit vào lưu trữ WORM.
    Adapter thật phải đặt is_worm_confirmed=True với provider_id thật.
    Adapter giả lập PHẢI đặt is_worm_confirmed=False.
    """

    provider_id: str
    provider_timestamp_utc: str
    immutability_expiry_utc: Optional[str]
    etag: str
    provider_name: str
    region: str
    is_worm_confirmed: bool
    disclaimer: str

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must be non-empty")
        if not self.provider_name:
            raise ValueError("provider_name must be non-empty")
        if not self.disclaimer:
            raise ValueError("disclaimer must be non-empty")
        if self.is_worm_confirmed and self.disclaimer == DISCLAIMER_FAKE_WORM:
            raise ValueError(
                "is_worm_confirmed cannot be True with fake/simulation disclaimer"
            )


@dataclass
class RetentionPolicy:
    """Chính sách lưu trữ audit cho hệ thống nghiên cứu y tế."""

    default_retention_years: int = 7
    clinical_retention_years: int = 10
    ethics_retention_years: int = 15
    legal_hold_indefinite: bool = True
    compliance_mode: str = "COMPLIANCE"
    cross_region_backup: bool = False


class WormRetentionProviderInterface(ABC):
    """
    Giao diện trừu tượng cho mọi adapter nhà cung cấp lưu trữ WORM.
    Các provider thật (AWS/Azure/GCP/on-prem) phải triển khai class này.
    Không được khởi tạo trực tiếp.
    """

    @abstractmethod
    def write_event(self, event: dict) -> WriteReceipt:
        """Ghi một sự kiện audit vào lưu trữ WORM; trả WriteReceipt."""

    @abstractmethod
    def read_event(self, event_id: str) -> dict:
        """Đọc một sự kiện audit theo event_id."""

    @abstractmethod
    def verify_event(self, event_id: str, expected_hash: str) -> bool:
        """Kiểm tra hash sự kiện so với giá trị đã lưu."""

    @abstractmethod
    def create_legal_hold(self, hold_id: str, scope: str) -> None:
        """Tạo giữ pháp lý trên một tập sự kiện — ghi đè hết hạn lưu trữ."""

    @abstractmethod
    def release_legal_hold(self, hold_id: str, authority: str) -> None:
        """Giải phóng giữ pháp lý — yêu cầu xác nhận thẩm quyền rõ ràng."""

    @abstractmethod
    def list_events_in_range(self, from_utc: str, to_utc: str) -> List[str]:
        """Liệt kê event_id trong khoảng thời gian cho trước."""

    @abstractmethod
    def get_retention_policy(self) -> RetentionPolicy:
        """Trả chính sách lưu trữ hiện tại."""

    @abstractmethod
    def provider_health_check(self) -> bool:
        """Kiểm tra khả năng kết nối và ghi của provider."""


class FakeWormRetentionAdapter(WormRetentionProviderInterface):
    """
    Adapter WORM giả lập offline — CHỈ dùng trong harness kiểm thử.

    KHÔNG kết nối cloud storage thật.
    KHÔNG cung cấp bất biến thật.
    is_worm_confirmed LUÔN False.
    Lưu trữ trong bộ nhớ — mất khi process kết thúc.
    """

    NOT_IMPLEMENTED = (
        "FakeWormRetentionAdapter is an offline test stub only. "
        + PROD_WORM_DEPENDENCY
    )

    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}
        self._legal_holds: Dict[str, str] = {}
        self._retention_policy = RetentionPolicy()

    def write_event(self, event: dict) -> WriteReceipt:
        """Ghi sự kiện vào bộ nhớ; trả WriteReceipt với is_worm_confirmed=False."""
        event_id = event.get("event_id", str(uuid.uuid4()))
        content = str(sorted(event.items())).encode()
        etag = hashlib.sha256(content).hexdigest()[:16]
        self._store[event_id] = dict(event)
        return WriteReceipt(
            provider_id=f"fake-{event_id}",
            provider_timestamp_utc="2026-06-28T00:00:00Z",
            immutability_expiry_utc=None,
            etag=etag,
            provider_name=PROVIDER_NAME_FAKE,
            region="OFFLINE_SIMULATION",
            is_worm_confirmed=False,
            disclaimer=DISCLAIMER_FAKE_WORM,
        )

    def read_event(self, event_id: str) -> dict:
        """Đọc sự kiện từ bộ nhớ tạm."""
        if event_id not in self._store:
            raise KeyError(f"event_id not found: {event_id}")
        return dict(self._store[event_id])

    def verify_event(self, event_id: str, expected_hash: str) -> bool:
        """Kiểm tra hash sự kiện so với expected_hash."""
        if event_id not in self._store:
            return False
        event = self._store[event_id]
        actual_hash = event.get("audit_event_hash", "")
        return actual_hash == expected_hash

    def create_legal_hold(self, hold_id: str, scope: str) -> None:
        """Lưu giữ pháp lý vào bộ nhớ tạm."""
        self._legal_holds[hold_id] = scope

    def release_legal_hold(self, hold_id: str, authority: str) -> None:
        """Giải phóng giữ pháp lý nếu tồn tại."""
        if hold_id not in self._legal_holds:
            raise KeyError(f"hold_id not found: {hold_id}")
        if not authority:
            raise ValueError("authority reference must be non-empty for hold release")
        del self._legal_holds[hold_id]

    def list_events_in_range(self, from_utc: str, to_utc: str) -> List[str]:
        """Trả tất cả event_id trong bộ nhớ tạm (giả lập không lọc theo thời gian)."""
        return list(self._store.keys())

    def get_retention_policy(self) -> RetentionPolicy:
        """Trả chính sách lưu trữ mặc định."""
        return self._retention_policy

    def provider_health_check(self) -> bool:
        """Luôn trả True trong harness offline."""
        return True

    @property
    def active_holds(self) -> Dict[str, str]:
        return dict(self._legal_holds)
