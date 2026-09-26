"""Hồi quy 26/09/2026: seed_governance_test_data() đỏ ngẫu nhiên (~0,1%) vì sentinel PII «cccd»
(toàn chữ hex) khớp chuỗi con trong uuid4().hex của run_id/release_id/approval_id — CI nhánh mặc
định run #837 đỏ, run #838 cùng SHA xanh. Vá: script che khuôn uuid hex 32 ký tự TRƯỚC khi quét;
bộ quét dùng chung (runtime/data_boundary.py) giữ nguyên để không lọt BN001 / CCCD viết liền số.
"""
from __future__ import annotations

import itertools
import uuid

from runtime.data_boundary import DataBoundary
from scripts.phase_2b_seed_governance_test_data import seed_governance_test_data


def _sinh_uuid_co_cccd():
    """Mỗi lần gọi một UUID KHÁC (ràng buộc unique của DB) nhưng đều chứa chuỗi con «cccd»."""
    dem = itertools.count(1)
    return lambda: uuid.UUID(f"0123cccd{next(dem):024x}")


def test_uuid_chua_cccd_khong_bi_coi_la_pii(tmp_path, monkeypatch):
    # Ép MỌI uuid4 của cả 3 nơi sinh ID chứa «cccd» — tái lập chắc chắn ca chập chờn.
    sinh = _sinh_uuid_co_cccd()
    for mod in ("app.core.run_packet", "app.core.release_manager", "app.governance.repository"):
        monkeypatch.setattr(f"{mod}.uuid4", sinh)
    result = seed_governance_test_data(f"sqlite:///{tmp_path / 'seed.db'}")
    assert "cccd" in result["run_id"]          # đúng là ID có chứa chuỗi con nguy hiểm
    assert result["contains_pii"] is False


def test_bo_quet_dung_chung_van_bat_pii_that():
    """Đối chứng: vá KHÔNG được làm yếu bộ quét dùng chung (chiều fail-open nguy hiểm hơn)."""
    db = DataBoundary()
    for text in ("id: BN001", '{"id": "BN0012345"}', "CCCD012345678901", "cccd: 012345678901",
                 '{"cccd": "x"}', "so_cccd=1"):
        assert db.check_pii_in_output(text)[0] is True, text
