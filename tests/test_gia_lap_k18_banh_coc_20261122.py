"""Chốt CI bánh cóc chuẩn báo cáo theo mục (K18) cho bản thảo và báo cáo tổng hợp — tools/kiem_gia_lap_16.py.

22/11/2026: bác sĩ giao hoàn thiện SAP/bản thảo/báo cáo nghiệm thu cho 8 thiết kế; trước đó CI giả lập không đo chuẩn
báo cáo theo mục của bản thảo và báo cáo tổng hợp, nên một thay đổi làm lùi chuẩn vẫn qua CI xanh."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import kiem_gia_lap_16 as K  # noqa: E402

SO_NO = {"kich_ban": {"rct_nhi_phan": {"ban_thao": ["CONSORT 2025 3"], "bao_cao": ["CONSORT 2025 3"]}}}


def _j(bt, bc, cau_truc=None):
    return {"chuan_bao_cao": {"ban_thao_thieu": bt, "bao_cao_thieu": bc, "bao_cao_cau_truc": cau_truc or []}}


def test_dung_so_no_thi_dat():
    assert K.kiem_chuan_bao_cao("rct_nhi_phan", _j(["CONSORT 2025 3"], ["CONSORT 2025 3"]), SO_NO) == []


def test_muc_moi_thieu_la_lui_chuan():
    loi = K.kiem_chuan_bao_cao("rct_nhi_phan", _j(["CONSORT 2025 3", "CONSORT 2025 4"], ["CONSORT 2025 3"]), SO_NO)
    assert any("LÙI" in x and "CONSORT 2025 4" in x for x in loi)


def test_da_dat_them_phai_rut_khoi_so():
    loi = K.kiem_chuan_bao_cao("rct_nhi_phan", _j([], ["CONSORT 2025 3"]), SO_NO)
    assert any("rút khỏi sổ nợ" in x for x in loi)


def test_chua_do_khong_bao_gio_la_dat():
    assert K.kiem_chuan_bao_cao("rct_nhi_phan", {}, SO_NO)
    assert K.kiem_chuan_bao_cao("rct_nhi_phan", {"chuan_bao_cao": {"loi": "chưa có bản thảo G7"}}, SO_NO)


def test_cau_truc_bao_cao_sai_thi_do():
    loi = K.kiem_chuan_bao_cao("rct_nhi_phan", _j(["CONSORT 2025 3"], ["CONSORT 2025 3"], ["thiếu: Kết luận"]), SO_NO)
    assert any("cấu trúc" in x for x in loi)


def test_kich_ban_ngoai_so_chi_do_khong_phan():
    assert K.kiem_chuan_bao_cao("rct_cum", {}, SO_NO) == []


def test_ghi_so_no_tu_choi_them_muc(tmp_path, monkeypatch):
    so = tmp_path / "so.json"
    so.write_text(json.dumps(SO_NO), encoding="utf-8", newline="\n")
    monkeypatch.setattr(K, "SO_NO_K18", so)
    (tmp_path / "rct_nhi_phan.json").write_text(json.dumps(_j(["CONSORT 2025 3", "CONSORT 2025 4"], [])),
                                                encoding="utf-8", newline="\n")
    assert K.ghi_so_no(tmp_path, ["rct"]) == 1                          # thêm mục ⇒ từ chối
    assert json.loads(so.read_text(encoding="utf-8")) == SO_NO          # sổ không đổi
    assert K.ghi_so_no(tmp_path, ["rct"], cho_them=True) == 0
    (tmp_path / "rct_nhi_phan.json").write_text(json.dumps(_j([], [])), encoding="utf-8", newline="\n")
    assert K.ghi_so_no(tmp_path, ["rct"]) == 0                          # giảm ⇒ được
    assert json.loads(so.read_text(encoding="utf-8"))["kich_ban"]["rct_nhi_phan"] == {"ban_thao": [], "bao_cao": []}


def test_so_no_that_doc_duoc_va_dung_ten_kich_ban():
    so = json.loads(K.SO_NO_K18.read_text(encoding="utf-8"))
    assert set(so["kich_ban"]) <= set(K.KICH_BAN.values()) | set(K.CHAN_THUC.values())
    for v in so["kich_ban"].values():
        assert set(v) == {"ban_thao", "bao_cao"}


def test_kiem_mot_goi_chot_chuan_bao_cao(tmp_path, monkeypatch):
    so = tmp_path / "so.json"
    so.write_text(json.dumps(SO_NO), encoding="utf-8", newline="\n")
    monkeypatch.setattr(K, "SO_NO_K18", so)
    p = tmp_path / "rct_nhi_phan.json"
    p.write_text(json.dumps(_j(["CONSORT 2025 3", "CONSORT 2025 10"], ["CONSORT 2025 3"])),
                 encoding="utf-8", newline="\n")
    assert any("LÙI" in x for x in K.kiem_mot(p))


def test_gia_lap_do_chuan_bao_cao_theo_muc(tmp_path):
    import types

    import gia_lap_tron_vong as TV

    sys.path.insert(0, str(ROOT / "tests"))
    import test_bao_cao_tong_hop_20261122 as F  # noqa: PLC0415 — dùng lại fixture đề cương/bản thảo nhỏ

    ns = types.SimpleNamespace(study=F.S, thiet_ke="cross_sectional", out=tmp_path / "trong")
    assert "loi" in TV.TronVong._chuan_bao_cao(ns)                     # chưa có bản thảo ⇒ lỗi, không «đạt»
    ns.out = F._dung(tmp_path)
    kq = TV.TronVong._chuan_bao_cao(ns)
    assert {"ban_thao_thieu", "bao_cao_thieu", "bao_cao_cau_truc"} <= set(kq) and "loi" not in kq
    assert all(isinstance(x, str) and " " in x for x in kq["ban_thao_thieu"] + kq["bao_cao_thieu"])
