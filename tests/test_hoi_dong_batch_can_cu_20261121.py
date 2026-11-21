"""Hội đồng Batch: căn cứ sai DẠNG bị bắt ngay khi nhận kết quả ⇒ đi luật gửi lại một lần (21/11/2026).

Đo thật C1a G10-T1: người chấm ghi «A12 R4_pmid_traceable» làm mã tiêu chí cổng — chỉ bị chặn LÚC GHI biên bản, phần đó
không được gửi lại, phải xử lý tay. Ngoại tuyến.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import hoi_dong_cong_batch as HB  # noqa: E402


def _cham(cc):
    return {"tieu_chi": [{"ma": "RQ3", "muc": "can_sua", "nhan_xet": "x", "can_cu": [cc]}], "ket_luan": "tra_ve_sua"}


@pytest.mark.parametrize("cc", [
    {"loai": "tieu_chi", "gia_tri": "A12 R4_pmid_traceable"},
    {"loai": "pmid", "gia_tri": "PMID 123"},
    {"loai": "doi", "gia_tri": "doi.org/10.1/x"},
    {"loai": "lenh", "gia_tri": "python3 x.py"},
    {"loai": "trang_web", "gia_tri": "x"},
])
def test_can_cu_sai_dang_la_ket_qua_hong(cc):
    with pytest.raises(API.KetQuaHong, match="căn cứ sai dạng"):
        HB._hop_cham(_cham(cc))


def test_can_cu_dung_dang_qua():
    for cc in ({"loai": "tieu_chi", "gia_tri": "G10-AUTO-09"}, {"loai": "tieu_chi", "gia_tri": "G4-HUMAN-04"},
               {"loai": "pmid", "gia_tri": "17654487"}, {"loai": "doi", "gia_tri": "10.1002/nur.20199"},
               {"loai": "lenh", "gia_tri": "python3 x.py", "ket_qua": "PASS"}, {"loai": "tep", "gia_tri": "a.md:3"}):
        assert HB._hop_cham(_cham(cc))
    with pytest.raises(API.KetQuaHong):
        HB._hop_luan_diem({"ket_luan_de_xuat": "k", "luan_diem": [{"ma": "L1", "can_cu": [
            {"loai": "tieu_chi", "gia_tri": "RQ3"}]}]}, True)


def _st():
    return {"cham": {"T1": {"ket": {"chuyen_mon": None, "giam_khao": None}, "loi": [], "chuyen_mon": "tham-dinh-dau-ra",
                            "tai_lieu": []}}, "tranh": {},
            "batch": {"yeu_cau": {"cm_000": {"loai": "cham", "ma": "T1", "vai": "chuyen_mon"}}}}


def _ket(dl):
    return {"cm_000": {"loai": "succeeded", "stop_reason": "end_turn", "nhom": None,
                       "text": json.dumps(dl, ensure_ascii=False), "vao": 0, "ra": 0}}


def test_can_cu_sai_dang_gui_lai_mot_lan_roi_moi_loi():
    st = _st()
    bad = _cham({"loai": "tieu_chi", "gia_tri": "A12 R4_pmid_traceable"})
    dem = HB.ap_ket_qua(st, _ket(bad))
    c = st["cham"]["T1"]
    assert dem["gui_lai"] == 1 and c["loi"] == [] and c["ket"]["chuyen_mon"] is None
    HB.ap_ket_qua(st, _ket(bad))
    assert c["loi"] and "căn cứ sai dạng" in c["loi"][0] and "đã gửi lại 1 lần" in c["loi"][0]


def test_loi_dan_noi_ro_dang_ma_tieu_chi():
    assert "G<số cổng>-AUTO-<2 số>" in HB.QUY_TAC_API and "KHÔNG phải mã tiêu chí cổng" in HB.QUY_TAC_API


def test_nang_cap_trang_thai_cu_nhan_can_cu_sai_dang():
    st = {"cham": {"T1": {"ket": {"chuyen_mon": None, "giam_khao": {}}, "loi": [
        "cm_000: căn cứ sai dạng: mã tiêu chí «A12 R4»"]}}, "tranh": {}}
    assert HB.nang_cap_loi_json_cu(st) == 1 and st["cham"]["T1"]["gui_lai"] == {"chuyen_mon": 1}
