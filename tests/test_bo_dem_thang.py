"""Test đơn vị cho `app/utils/bo_dem_thang.py` — bộ đếm lượt gọi THEO THÁNG, bền, fail-closed.

Không gọi mạng; đồng hồ được thay bằng đồng hồ giả để kiểm chuyển tháng.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.bo_dem_thang import BoDemThang, HetTran  # noqa: E402


class DongHoGia:
    def __init__(self, nam: int = 2026, thang: int = 9, ngay: int = 20) -> None:
        self.gio = datetime(nam, thang, ngay, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.gio

    def sang(self, nam: int, thang: int) -> None:
        self.gio = datetime(nam, thang, 1, 0, 5, tzinfo=timezone.utc)


@pytest.fixture()
def dh() -> DongHoGia:
    return DongHoGia()


@pytest.fixture()
def tep(tmp_path) -> Path:
    return tmp_path / "state" / "usage.json"


def _bd(tep: Path, dh: DongHoGia) -> BoDemThang:
    return BoDemThang("thu", lambda: tep, dh)


def _doc(tep: Path) -> dict:
    return json.loads(tep.read_text(encoding="utf-8"))


def _viet(tep: Path, noi_dung: str) -> None:
    tep.parent.mkdir(parents=True, exist_ok=True)
    tep.write_text(noi_dung, encoding="utf-8", newline="\n")


def test_first_call_creates_the_state_file_and_counts_one(tep, dh):
    _bd(tep, dh).giu_cho(5)
    d = _doc(tep)
    assert (d["thang"], d["da_goi"], d["het_quota"], d["phien_ban"]) == ("2026-09", 1, False, 1)


def test_cap_is_enforced_and_the_refused_call_is_not_counted(tep, dh):
    bd = _bd(tep, dh)
    bd.giu_cho(2)
    bd.giu_cho(2)
    with pytest.raises(HetTran) as ei:
        bd.giu_cho(2)
    assert ei.value.pham_vi == "thang"
    assert _doc(tep)["da_goi"] == 2


def test_zero_cap_refuses_every_call(tep, dh):
    with pytest.raises(HetTran):
        _bd(tep, dh).giu_cho(0)


def test_two_instances_share_the_count_through_the_file(tep, dh):
    """Hai BoDemThang khác nhau (hai tiến trình) cùng tệp: số đếm cộng dồn."""
    _bd(tep, dh).giu_cho(3)
    _bd(tep, dh).giu_cho(3)
    _bd(tep, dh).giu_cho(3)
    with pytest.raises(HetTran):
        _bd(tep, dh).giu_cho(3)


def test_new_month_resets_the_count(tep, dh):
    bd = _bd(tep, dh)
    bd.giu_cho(1)
    with pytest.raises(HetTran):
        bd.giu_cho(1)
    dh.sang(2026, 10)
    bd.giu_cho(1)
    assert (_doc(tep)["thang"], _doc(tep)["da_goi"]) == ("2026-10", 1)


def test_a_file_from_a_future_month_keeps_its_count_instead_of_resetting(tep, dh):
    """Đồng hồ lùi / tệp từ máy lệch giờ: KHÔNG được coi là 'tháng mới' rồi đặt lại về 0."""
    _viet(tep, json.dumps({"phien_ban": 1, "thang": "2026-11", "da_goi": 7, "het_quota": False}))
    with pytest.raises(HetTran):
        _bd(tep, dh).giu_cho(7)


@pytest.mark.parametrize("noi_dung", [
    "{khong phai json", "[]", "null", '"chuoi"',
    json.dumps({"phien_ban": 2, "thang": "2026-09", "da_goi": 1, "het_quota": False}),
    json.dumps({"phien_ban": True, "thang": "2026-09", "da_goi": 1, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "2026-13", "da_goi": 1, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "09/2026", "da_goi": 1, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": 202609, "da_goi": 1, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "2026-09", "da_goi": -1, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "2026-09", "da_goi": True, "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "2026-09", "da_goi": "3", "het_quota": False}),
    json.dumps({"phien_ban": 1, "thang": "2026-09", "da_goi": 1, "het_quota": "khong"}),
    json.dumps({"phien_ban": 1, "da_goi": 1, "het_quota": False}),
])
def test_any_corrupt_state_is_treated_as_capped_and_never_overwritten(tep, dh, noi_dung):
    _viet(tep, noi_dung)
    with pytest.raises(HetTran) as ei:
        _bd(tep, dh).giu_cho(1000)
    assert ei.value.pham_vi == "trang_thai_hong"
    assert tep.read_text(encoding="utf-8") == noi_dung


def test_an_unwritable_state_location_refuses_the_call(tmp_path, dh):
    """Thư mục cha là một FILE thường: không tạo được tệp trạng thái => không gọi (fail-closed)."""
    chan = tmp_path / "la_mot_file"
    chan.write_text("x", encoding="utf-8", newline="\n")
    bd = BoDemThang("thu", lambda: chan / "usage.json", dh)
    with pytest.raises(HetTran) as ei:
        bd.giu_cho(5)
    assert ei.value.pham_vi in {"khong_ghi_duoc", "trang_thai_hong"}


def test_refund_decrements_but_never_below_zero(tep, dh):
    bd = _bd(tep, dh)
    bd.hoan()
    assert not tep.exists() or _doc(tep)["da_goi"] == 0
    bd.giu_cho(5)
    bd.hoan()
    bd.hoan()
    assert _doc(tep)["da_goi"] == 0


def test_refund_on_a_corrupt_file_leaves_it_alone(tep, dh):
    _viet(tep, "{hong")
    _bd(tep, dh).hoan()
    assert tep.read_text(encoding="utf-8") == "{hong"


def test_marking_exhausted_blocks_the_rest_of_the_month_but_not_the_next(tep, dh):
    bd = _bd(tep, dh)
    bd.giu_cho(100)
    bd.danh_dau_het(100)
    with pytest.raises(HetTran) as ei:
        bd.giu_cho(100)
    assert ei.value.pham_vi == "het_quota"
    assert _doc(tep)["da_goi"] == 100
    dh.sang(2026, 10)
    bd.giu_cho(100)


def test_marking_exhausted_on_a_corrupt_file_does_not_overwrite_it(tep, dh):
    _viet(tep, "{hong")
    _bd(tep, dh).danh_dau_het(10)
    assert tep.read_text(encoding="utf-8") == "{hong"


def test_snapshot_reports_without_mutating(tep, dh):
    bd = _bd(tep, dh)
    a0 = bd.anh_chup(4)
    assert (a0["da_goi_thang"], a0["con_lai_thang"], a0["trang_thai_hong"]) == (0, 4, False)
    assert not tep.exists(), "chụp ảnh không được tạo tệp"
    bd.giu_cho(4)
    a1 = bd.anh_chup(4)
    assert (a1["da_goi_thang"], a1["con_lai_thang"]) == (1, 3)


def test_snapshot_of_a_corrupt_file_reports_zero_left(tep, dh):
    _viet(tep, "{hong")
    a = _bd(tep, dh).anh_chup(4)
    assert (a["trang_thai_hong"], a["con_lai_thang"], a["da_goi_thang"]) == (True, 0, None)


def test_writes_leave_no_temp_files_behind(tep, dh):
    bd = _bd(tep, dh)
    for _ in range(3):
        bd.giu_cho(10)
    bd.hoan()
    bd.danh_dau_het(10)
    assert sorted(p.name for p in tep.parent.iterdir()) == ["usage.json"]
