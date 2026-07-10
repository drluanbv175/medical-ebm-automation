"""
Hợp đồng giao diện adapter nhận dạng cho R1.2.

Chỉ chứa định nghĩa interface và adapter tổng hợp offline.
KHÔNG kết nối SSO/IdP/LDAP/OIDC thật.
KHÔNG tạo session thật, token thật, hoặc xác thực MFA thật.
"""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

# ── Hằng số phụ thuộc chưa triển khai ─────────────────────────────────────

PROD_SSO_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires external institutional SSO provider (SAML2/OIDC/LDAP)"
)
PROD_MFA_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires external MFA service (TOTP/FIDO2/SMS)"
)
PROD_SESSION_STORE_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires external session store (Redis/PostgreSQL)"
)

ATTRIBUTION_MODE_AUTHENTICATED = "AUTHENTICATED"
ATTRIBUTION_MODE_SYNTHETIC = "SYNTHETIC"

_VALID_ATTRIBUTION_MODES = {ATTRIBUTION_MODE_AUTHENTICATED, ATTRIBUTION_MODE_SYNTHETIC}

DISCLAIMER_SYNTHETIC = (
    "Synthetic identity — not for production use. Cần bác sĩ kiểm chứng."
)


@dataclass
class AuthenticationContext:
    """
    Đơn vị nhận dạng được xác thực truyền từ adapter IdP xuống các thành phần hạ nguồn.
    Tất cả trường bắt buộc; không lưu PII; actor_id là định danh giả danh.
    """

    actor_id: str
    email_hash: str
    roles: List[str]
    session_id: str
    issued_at_utc: str
    expires_at_utc: str
    mfa_satisfied: bool
    attribution_mode: str
    disclaimer: str

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Kiểm tra tất cả ràng buộc hợp đồng — ném ValueError nếu vi phạm."""
        if not self.actor_id:
            raise ValueError("actor_id must be non-empty")
        if not self.email_hash:
            raise ValueError("email_hash must be non-empty")
        if not self.roles:
            raise ValueError("roles must contain at least one role")
        if not self.session_id:
            raise ValueError("session_id must be non-empty")
        if not self.issued_at_utc:
            raise ValueError("issued_at_utc must be non-empty")
        if not self.expires_at_utc:
            raise ValueError("expires_at_utc must be non-empty")
        if self.expires_at_utc <= self.issued_at_utc:
            raise ValueError("expires_at_utc must be after issued_at_utc")
        if self.attribution_mode not in _VALID_ATTRIBUTION_MODES:
            raise ValueError(
                f"attribution_mode must be one of {_VALID_ATTRIBUTION_MODES}"
            )
        if self.attribution_mode == ATTRIBUTION_MODE_AUTHENTICATED and not self.mfa_satisfied:
            raise ValueError(
                "AUTHENTICATED context requires mfa_satisfied=True"
            )
        if not self.disclaimer:
            raise ValueError("disclaimer must be non-empty")


class IdentityProviderAdapterInterface(ABC):
    """
    Giao diện trừu tượng cho mọi adapter nhà cung cấp nhận dạng.
    Các provider thật (SAML, OIDC, LDAP) phải triển khai class này.
    Không được khởi tạo trực tiếp.
    """

    @abstractmethod
    def authenticate(self, credential_token: str) -> AuthenticationContext:
        """Xác thực token credential và trả về AuthenticationContext."""

    @abstractmethod
    def validate_session(self, session_id: str) -> bool:
        """Kiểm tra session có hợp lệ, chưa hết hạn và chưa bị thu hồi."""

    @abstractmethod
    def revoke_session(self, session_id: str) -> None:
        """Thu hồi session ngay lập tức; sau đó validate_session() trả False."""

    @abstractmethod
    def get_user_roles(self, actor_id: str) -> List[str]:
        """Trả danh sách vai trò hiện tại của actor từ registry vai trò."""

    @abstractmethod
    def is_mfa_satisfied(self, session_id: str) -> bool:
        """Kiểm tra MFA đã hoàn thành cho session này hay chưa."""


class SyntheticIdentityAdapter(IdentityProviderAdapterInterface):
    """
    Adapter nhận dạng tổng hợp offline — CHỈ dùng trong harness kiểm thử.

    KHÔNG kết nối IdP thật.
    KHÔNG xác thực MFA thật.
    KHÔNG lưu session thật.
    is_mfa_satisfied() LUÔN trả False trong harness offline.
    attribution_mode LUÔN là SYNTHETIC.
    """

    NOT_IMPLEMENTED = (
        "SyntheticIdentityAdapter is an offline test stub only. "
        + PROD_SSO_DEPENDENCY
    )

    def __init__(self, roles: List[str] | None = None) -> None:
        self._roles = roles or ["VIEWER"]
        self._revoked: set[str] = set()

    def authenticate(self, credential_token: str) -> AuthenticationContext:
        """Trả AuthenticationContext tổng hợp không có xác thực thật."""
        actor_id = f"synthetic_actor_{hashlib.sha256(credential_token.encode()).hexdigest()[:8]}"
        email_hash = hashlib.sha256("synthetic@example.invalid".encode()).hexdigest()
        session_id = str(uuid.uuid4())
        return AuthenticationContext(
            actor_id=actor_id,
            email_hash=email_hash,
            roles=list(self._roles),
            session_id=session_id,
            issued_at_utc="2026-06-28T00:00:00Z",
            expires_at_utc="2026-06-28T08:00:00Z",
            mfa_satisfied=False,
            attribution_mode=ATTRIBUTION_MODE_SYNTHETIC,
            disclaimer=DISCLAIMER_SYNTHETIC,
        )

    def validate_session(self, session_id: str) -> bool:
        """Session hợp lệ nếu chưa bị thu hồi trong bộ nhớ tạm."""
        return session_id not in self._revoked

    def revoke_session(self, session_id: str) -> None:
        """Đánh dấu session là đã thu hồi trong bộ nhớ tạm."""
        self._revoked.add(session_id)

    def get_user_roles(self, actor_id: str) -> List[str]:
        """Trả danh sách vai trò tổng hợp cố định."""
        return list(self._roles)

    def is_mfa_satisfied(self, session_id: str) -> bool:
        """MFA LUÔN False trong harness offline tổng hợp."""
        return False
