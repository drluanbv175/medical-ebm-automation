# -*- coding: utf-8 -*-
"""Bảng trách nhiệm TOÀN ĐỀ TÀI cho điều phối tổng — `trach-nhiem --gate ALL` (10/10/2026, «từng điều phối»).

`dieu-phoi-nghien-cuu` «giao cổng — nhận cổng» cần một chỗ trả lời: cổng nào phần agent hoàn chỉnh, cổng nào còn việc,
GIAO TRƯỚC cho điều phối cổng nào (cổng đầu tiên G0→G10 còn việc agent/chưa phân công). Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402

STUDY = "TONG-THU"


def _gia(ket_luan_theo_cong: dict):
    def trach_nhiem(study, gate, out_dir):
        kl = ket_luan_theo_cong.get(gate, "DAT_TIEU_CHI")
        viec = ([{"id": f"{gate}-AUTO-01", "status": "REVIEW", "viec": f"việc của {gate}", "nhiem_vu": f"{gate}-T1",
                  "agent": "agent-gia"}] if kl == "AGENT_CON_VIEC" else [])
        chua = [{"id": f"{gate}-AUTO-99", "status": "REVIEW", "viec": "mã lạ"}] if kl == "CHUA_PHAN_CONG" else []
        return {"gate": gate, "study": study, "dieu_phoi": HD.dieu_phoi_cong(gate), "trang_thai_song": "X",
                "ket_luan": kl, "agent_con_viec": viec, "cho_nguoi": [], "cho_cong_truoc": [],
                "chat_luong_chua_bao_dam": [], "chua_phan_cong": chua}
    return trach_nhiem


@pytest.mark.parametrize("bang, giao, ma", [
    ({"G1": "AGENT_XONG_CHO_NGUOI", "G2": "AGENT_CON_VIEC", "G3": "CHUA_PHAN_CONG", "G5": "CHO_CONG_TRUOC"}, "G2", 1),
    ({"G0": "CHO_CONG_TRUOC", "G4": "CHUA_PHAN_CONG"}, "G4", 1),
    ({"G1": "AGENT_XONG_CHO_NGUOI"}, None, 0),
    ({"G7": "KHONG_DO_DUOC"}, None, 2),
    ({"G7": "KHONG_DO_DUOC", "G9": "AGENT_CON_VIEC"}, "G9", 1),
])
def test_chon_cong_can_giao_va_ma_thoat(monkeypatch, tmp_path, bang, giao, ma):
    monkeypatch.setattr(HD, "trach_nhiem", _gia(bang))
    kq = HD.tong_trach_nhiem(STUDY, tmp_path)
    assert [k["gate"] for k in kq["cong"]] == list(HD.CONG)
    assert kq["cong_can_giao"] == giao and HD.ma_thoat_tong(kq) == ma
    assert kq["dieu_phoi_can_giao"] == (HD.dieu_phoi_cong(giao) if giao else None)
    ban = HD.in_tong_trach_nhiem(kq)
    assert (f"GIAO TRƯỚC: cổng {giao} cho `dieu-phoi-{giao.lower()}`" in ban) if giao else ("Không cổng nào" in ban)
    assert ban.count("\n| G") == 11


def test_cli_all_in_bang_va_ghi_du_11_cong(monkeypatch, tmp_path, capsys):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    monkeypatch.setattr(HD, "BASE", tmp_path)
    monkeypatch.setattr(HD, "trach_nhiem", _gia({"G3": "AGENT_CON_VIEC"}))
    assert HD.main(["trach-nhiem", "--study", STUDY, "--gate", "ALL", "--ghi"]) == 1
    ra = capsys.readouterr().out
    assert "TRÁCH NHIỆM TOÀN ĐỀ TÀI" in ra and "đã lưu 11 bảng cổng" in ra
    assert sorted(p.parent.parent.name for p in out.glob("hoi_dong/*/trach_nhiem/TN-*.json")) == sorted(HD.CONG)
    assert HD.main(["trach-nhiem", "--study", STUDY, "--gate", "ALL", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["cong_can_giao"] == "G3"


def test_all_chi_danh_cho_trach_nhiem(capsys):
    with pytest.raises(SystemExit):
        HD.main(["cham-song", "--study", STUDY, "--gate", "ALL"])
