"""Hồi quy phát hiện #8 (audit vòng 39, 2026-09-06) trong
research_project/identity_adapter_contract.py::SyntheticIdentityAdapter.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def __init__(self, roles=None):
        self._roles = roles or ["VIEWER"]
        self._revoked: set[str] = set()

    def validate_session(self, session_id: str) -> bool:
        return session_id not in self._revoked

`validate_session()` chỉ theo dõi tập `_revoked` — bất kỳ chuỗi session_id
NÀO (kể cả session_id GIẢ MẠO, chưa từng được authenticate() cấp) đều trả
True miễn là nó chưa nằm trong `_revoked`. Điều này mâu thuẫn trực tiếp với
docstring của chính interface: "Session hợp lệ nếu ĐÃ được authenticate()
cấp và chưa bị thu hồi" — về mặt logic, một session KHÔNG TỒN TẠI hiển
nhiên không thể "chưa bị thu hồi" theo nghĩa đã cấp phát hợp lệ.

PHẠM VI ẢNH HƯỞNG: đây là stub offline dùng cho test harness, nhưng chính
là contract mẫu (`IdentityProviderAdapterInterface`) mà một adapter thật
sẽ triển khai theo. Một implementation THẬT sao chép logic "chỉ kiểm
revoked" sẽ chấp nhận session_id đoán mò/brute-force mà không cần xác
thực — lỗ hổng session-fixation/session-forgery kinh điển. Test cho
interface hợp đồng này nên phản ánh đúng ngữ nghĩa "phải đã được cấp"."""
from __future__ import annotations

import uuid

from research_project.identity_adapter_contract import SyntheticIdentityAdapter


class TestCaChinhSessionIdChuaTungCapPhaiKhongHopLe:
    """★★★ Ca chính — session_id KHÔNG do authenticate() cấp (giả mạo/đoán
    mò) phải trả về False, không được coi là hợp lệ chỉ vì chưa bị revoke."""

    def test_session_id_ngau_nhien_chua_tung_cap_khong_hop_le(self):
        adapter = SyntheticIdentityAdapter()
        forged_session_id = str(uuid.uuid4())
        assert adapter.validate_session(forged_session_id) is False, (
            "TRƯỚC bản vá: validate_session() chỉ kiểm tập _revoked — bất kỳ "
            "session_id nào (kể cả chưa từng được cấp) đều trả True miễn "
            "chưa bị revoke."
        )

    def test_session_id_rong_khong_hop_le(self):
        adapter = SyntheticIdentityAdapter()
        assert adapter.validate_session("") is False


class TestDoiChungSessionThatVanHoatDongDungNhuCu:
    """Đối chứng — session THẬT do authenticate() cấp vẫn hợp lệ cho tới
    khi bị revoke; sau revoke vẫn không hợp lệ như hành vi cũ."""

    def test_session_that_sau_authenticate_hop_le(self):
        adapter = SyntheticIdentityAdapter()
        ctx = adapter.authenticate("synthetic-credential-token")
        assert adapter.validate_session(ctx.session_id) is True

    def test_session_that_sau_khi_revoke_khong_con_hop_le(self):
        adapter = SyntheticIdentityAdapter()
        ctx = adapter.authenticate("synthetic-credential-token")
        adapter.revoke_session(ctx.session_id)
        assert adapter.validate_session(ctx.session_id) is False

    def test_hai_session_khac_nhau_deu_duoc_theo_doi_doc_lap(self):
        adapter = SyntheticIdentityAdapter()
        ctx1 = adapter.authenticate("token-1")
        ctx2 = adapter.authenticate("token-2")
        adapter.revoke_session(ctx1.session_id)
        assert adapter.validate_session(ctx1.session_id) is False
        assert adapter.validate_session(ctx2.session_id) is True
