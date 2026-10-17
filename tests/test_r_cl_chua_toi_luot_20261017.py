# -*- coding: utf-8 -*-
"""Tách «chưa tới lượt đánh giá chéo» khỏi «chất lượng chưa bảo đảm» — 17/10/2026 (bác sĩ chọn trên Đài hoàn thiện).

C1a: R-CL = 7 trong đó G6-T3 (diễn giải — cần dữ liệu thật) và G7-T2 (hiệu đính tiếng Anh — cần bản thảo) CHƯA CÓ đầu
ra nên không thể chấm chéo trước 2027. Test chốt:
① nhiệm vụ không tiêu chí máy, đầu ra CÓ mà chưa chấm ⇒ «chất lượng chưa bảo đảm» như cũ;
② đầu ra CHƯA CÓ ⇒ chuyển sang «chưa tới lượt» kèm tên tệp thiếu — vẫn hiện, không bao giờ thành «đạt»;
③ nhiệm vụ có điều kiện máy không suy được (áp dụng = None) ⇒ lý do nói rõ «chưa xác định áp dụng»;
④ bảng ALL in dòng «⏳ Chưa tới lượt».
Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "RCL-THU"


def _song(monkeypatch, theo_cong: dict, thiet_ke="cross_sectional") -> None:
    """Giả chấm sống: theo_cong = {cổng: status}; mọi tiêu chí của cổng PASS trừ khi status BLOCKED (dừng sớm)."""
    def gia(gate, study, out_dir, repo_root=None):
        st = theo_cong.get(gate, f"PASS_{gate}_X")
        hang = ([{"id": f"{gate}-AUTO-00", "status": "BLOCK", "action": "dừng sớm"}] if st == "BLOCKED"
                else [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG[gate]])
        return {"status": st, "nguon": "song", "bao_cao": {"automatic_criteria": hang}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})


def _out(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    return out


def test_dau_ra_co_ma_chua_cham_van_la_chat_luong_chua_bao_dam(monkeypatch, tmp_path):
    out = _out(tmp_path)
    (out / "_bo-bien-rieng.csv").write_text("bien,kieu\nx,text\n", encoding="utf-8", newline="\n")
    _song(monkeypatch, {})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["chat_luong_chua_bao_dam"] == ["G3-T2", "G3-T3"] and kq["chat_luong_chua_toi_luot"] == []
    assert "CHẤT LƯỢNG CHƯA ĐƯỢC BẢO ĐẢM: G3-T2, G3-T3" in HD.in_trach_nhiem(kq)


def test_dau_ra_chua_co_la_chua_toi_luot_khong_phai_dat(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["chat_luong_chua_bao_dam"] == []
    assert [m["ma"] for m in kq["chat_luong_chua_toi_luot"]] == ["G3-T2", "G3-T3"]
    assert all("_bo-bien-rieng.csv" in m["ly_do"] for m in kq["chat_luong_chua_toi_luot"])
    van = HD.in_trach_nhiem(kq)
    assert "⏳ CHƯA TỚI LƯỢT ĐÁNH GIÁ CHÉO (không phải «đạt»): G3-T2 — chưa có đầu ra" in van
    assert "CHẤT LƯỢNG CHƯA ĐƯỢC BẢO ĐẢM" not in van
    assert all(m["danh_gia_cheo"] == "chua_danh_gia" for m in kq["chi_dam_bao_bang_danh_gia_cheo"]), \
        "trạng thái đánh giá chéo giữ nguyên — chỉ đổi nơi xếp"


def test_ap_dung_chua_xac_dinh_noi_ro_trong_ly_do(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {"G7": "BLOCKED"})
    kq = HD.trach_nhiem(STUDY, "G7", out)
    m = next(m for m in kq["chat_luong_chua_toi_luot"] if m["ma"] == "G7-T2")
    assert f"G7_A8_MANUSCRIPT_EN_{STUDY}.md" in m["ly_do"] and "chưa xác định áp dụng" in m["ly_do"]
    assert "G7-T2" not in kq["chat_luong_chua_bao_dam"]


def test_bang_all_in_dong_chua_toi_luot(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {})
    van = HD.in_tong_trach_nhiem(HD.tong_trach_nhiem(STUDY, out))
    dong = next(x for x in van.splitlines() if x.startswith("⏳ Chưa tới lượt đánh giá chéo"))
    assert "G3-T2" in dong and "G3-T3" in dong
