# -*- coding: utf-8 -*-
"""Trách nhiệm TỪNG AGENT + chủ có điều kiện + đánh giá chéo trong bảng trách nhiệm cổng (10/10/2026).

Bác sĩ giao «Tiếp tục hoàn thiện từng cổng từng Agent và từng điều phối». Test chốt:
① tài liệu 34 agent (11 điều phối + 23 agent làm/chấm chéo nhiệm vụ cổng) KHỚP bản sinh từ `hoi_dong_cong` (không chép
  tay, không lệch); mỗi agent thấy đúng nhiệm vụ nó làm và tiêu chí nó phải đưa tới ĐẠT; sinh lại là idempotent;
② ô có điều kiện «G2-T2|G2-T1»: RCT ⇒ an-toan-nghien-cuu chịu, còn lại ⇒ dao-duc-dang-ky;
③ biên bản đánh giá chéo «trả về sửa» là việc agent còn nợ; nhiệm vụ không có tiêu chí máy mà chưa được đánh giá chéo
  ⇒ «chất lượng chưa được bảo đảm» (nói thật, không đổi kết luận máy).
Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import sinh_tai_lieu_trach_nhiem as SG  # noqa: E402
import skill_standards as SK  # noqa: E402
from test_hoi_dong_cong_20261006 import CAN_CU, SAP, STUDY, _danh_gia, _sua_tieu_chi  # noqa: E402

AGENTS = ROOT / ".claude" / "agents"


@pytest.fixture()
def de_tai(tmp_path: Path) -> Path:
    """Đề tài giả có SAP + checkpoint G4 (cùng khuôn test hội đồng — biên bản mẫu xét tệp SAP này)."""
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / SAP).write_text("\n".join(f"Dòng {i} của SAP" for i in range(1, 21)) + "\n", encoding="utf-8",
                           newline="\n")
    (out / "G4_checkpoint.json").write_text('{"gate": "G4"}\n', encoding="utf-8", newline="\n")
    return out


# ── ① tài liệu từng agent khớp bản sinh ──────────────────────────────────────────────────────────────────────────────
def test_tai_lieu_agent_khop_ban_sinh():
    lech = [p.name for p, cu, moi in SG.ke_hoach(AGENTS) if cu != moi]
    assert not lech, f"chạy `python3 tools/sinh_tai_lieu_trach_nhiem.py --ghi` (ở repo gốc rồi chép sang): {lech}"


def test_sinh_lai_la_idempotent():
    for p, _cu, moi in SG.ke_hoach(AGENTS)[:14]:
        g = p.stem.replace("dieu-phoi-", "").upper()
        lai = SG.ap_dung_cong(moi, g) if p.stem.startswith("dieu-phoi-g") else SG.ap_dung_agent(moi, p.stem)
        assert lai == moi, p.name


@pytest.mark.parametrize("agent", sorted(SG.vai_agent()))
def test_moi_agent_thay_dung_nhiem_vu_va_tieu_chi_cua_minh(agent):
    van = (AGENTS / f"{agent}.md").read_text(encoding="utf-8")
    assert van.count("<!-- TRACH-NHIEM-AGENT:BAT-DAU") == 1 and van.count(SG.DAU_AGENT[1]) == 1, agent
    khoi = van[van.index("<!-- TRACH-NHIEM-AGENT:BAT-DAU"):van.index(SG.DAU_AGENT[1])]
    for g, nv in SG.vai_agent()[agent]["lam"]:
        dong = next((d for d in khoi.splitlines() if d.startswith(f"| `{nv['ma']}` ")), None)
        assert dong, (agent, nv["ma"])
        chiu, chuan_bi = SG._tieu_chi_cua_nhiem_vu(g, nv["ma"])
        for ma in [c.split(" ")[0] for c in chiu] + [m for ds in chuan_bi.values() for m in ds]:
            assert ma in dong, (agent, nv["ma"], ma)
    for _g, nv in SG.vai_agent()[agent]["cham"]:
        assert f"`{nv['ma']}` ({nv['agent']})" in khoi, (agent, nv["ma"])
    assert "## BƯỚC TỰ KIỂM" not in khoi and "EBM-MANDATORY-FINAL-GUARDRAIL" not in khoi


def test_khoi_agent_chen_truoc_buoc_tu_kiem_va_giu_noi_dung_cu():
    van = "# a\nnội dung\n\n## BƯỚC TỰ KIỂM — x\n1. y\n\n<!-- EBM-MANDATORY-FINAL-GUARDRAIL -->\nz\n"
    moi = SG.ap_dung_agent(van, "co-mau-nghien-cuu")
    assert moi.index("TRACH-NHIEM-AGENT:BAT-DAU") < moi.index("## BƯỚC TỰ KIỂM") < moi.index("EBM-MANDATORY")
    assert moi.replace(SG.khoi_agent("co-mau-nghien-cuu") + "\n", "") == van


def test_kiem_bao_lech_ma_1_va_ghi_sua_duoc(tmp_path, capsys):
    import shutil

    for p, _cu, _moi in SG.ke_hoach(AGENTS):
        shutil.copy2(p, tmp_path / p.name)
    t = tmp_path / "co-mau-nghien-cuu.md"
    t.write_text(t.read_text(encoding="utf-8").replace("G3-AUTO-05, ", ""), encoding="utf-8", newline="\n")
    assert SG.main(["--agents-dir", str(tmp_path)]) == 1
    assert "co-mau-nghien-cuu.md" in capsys.readouterr().out
    assert SG.main(["--agents-dir", str(tmp_path), "--ghi"]) == 0
    assert SG.main(["--agents-dir", str(tmp_path)]) == 0
    (tmp_path / "binh-duyet.md").unlink()
    assert SG.main(["--agents-dir", str(tmp_path)]) == 2


# ── ② chủ có điều kiện ───────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("thiet_ke, nhiem_vu", [("rct", "G2-T2"), ("cross_sectional", "G2-T1"), (None, "G2-T1")])
def test_chu_co_dieu_kien_theo_thiet_ke(thiet_ke, nhiem_vu):
    pc = HD.phan_cong("G2", "G2-AUTO-07", thiet_ke)
    assert (pc["loai"], pc["nhiem_vu"], pc["lua_chon"]) == ("agent", nhiem_vu, ["G2-T2", "G2-T1"])
    assert pc["agent"] == ("an-toan-nghien-cuu" if nhiem_vu == "G2-T2" else "dao-duc-dang-ky")


def test_nhiem_vu_khong_tieu_chi_tinh_ca_lua_chon_co_dieu_kien():
    assert "G2-T2" not in HD.nhiem_vu_khong_tieu_chi("G2"), "G2-T2 là lựa chọn của G2-AUTO-07"
    assert HD.nhiem_vu_khong_tieu_chi("G3") == ["G3-T2", "G3-T3"]


# ── ③ đánh giá chéo trong bảng trách nhiệm ───────────────────────────────────────────────────────────────────────────
def _song_g4_dat(monkeypatch, thiet_ke=None):
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G4"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G4_SAP_LOCKED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})


def test_hoi_dong_tra_ve_sua_la_viec_agent_con_no(monkeypatch, de_tai):
    bb = _sua_tieu_chi(_danh_gia("tra_ve_sua", "tra_ve_sua"), "RQ5", muc="loi_do", nhan_xet="Thiếu §9",
                       can_cu=CAN_CU)
    assert HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)[0] is not None
    _song_g4_dat(monkeypatch)
    kq = HD.trach_nhiem(STUDY, "G4", de_tai)
    assert kq["ket_luan"] == "AGENT_CON_VIEC", "mọi tiêu chí máy đạt nhưng hội đồng trả về sửa ⇒ chưa xong"
    m = next(m for m in kq["agent_con_viec"] if m["id"] == "G4-T1:danh-gia-cheo")
    assert m["agent"] == "thiet-ke-nghien-cuu" and "sửa theo biên bản" in m["viec"]


def test_hoi_dong_qua_khong_tao_viec(monkeypatch, de_tai):
    assert HD.ghi_bien_ban(STUDY, "G4", _danh_gia(), de_tai, de_tai.parent.parent)[0] is not None
    _song_g4_dat(monkeypatch)
    kq = HD.trach_nhiem(STUDY, "G4", de_tai)
    assert kq["ket_luan"] == "DAT_TIEU_CHI"
    assert {n["ma"]: n["danh_gia_cheo"]["trang_thai"] for n in kq["nhiem_vu"]}["G4-T1"] == "qua"


@pytest.mark.parametrize("thiet_ke, liet_ke", [("rct", True), ("cross_sectional", False)])
def test_nhiem_vu_khong_tieu_chi_chua_danh_gia_la_chat_luong_chua_bao_dam(monkeypatch, de_tai, thiet_ke, liet_ke):
    _song_g4_dat(monkeypatch, thiet_ke)
    (de_tai / "G4_A5_SAP_FINAL_HD-THU.md").write_text("SAP\n", encoding="utf-8", newline="\n")
    kq = HD.trach_nhiem(STUDY, "G4", de_tai)
    assert ("G4-T2" in kq["chat_luong_chua_bao_dam"]) is liet_ke
    assert kq["ket_luan"] == "DAT_TIEU_CHI", "chưa đánh giá chéo chỉ là cảnh báo nói thật, không đổi kết luận máy"
    if liet_ke:
        assert "CHẤT LƯỢNG CHƯA ĐƯỢC BẢO ĐẢM: G4-T2" in HD.in_trach_nhiem(kq)


def test_nhiem_vu_khong_tieu_chi_da_danh_gia_qua_thi_het_canh_bao(monkeypatch, de_tai):
    bb = _danh_gia()
    bb["dau_ra"].update(ma_nhiem_vu="G4-T2", tac_gia="an-toan-nghien-cuu")
    p, kq = HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)
    assert p is not None, kq["loi"]
    _song_g4_dat(monkeypatch, "rct")
    kq = HD.trach_nhiem(STUDY, "G4", de_tai)
    assert kq["chat_luong_chua_bao_dam"] == []
    assert [m["danh_gia_cheo"] for m in kq["chi_dam_bao_bang_danh_gia_cheo"]] == ["qua"]


def test_lay_bien_ban_danh_gia_moi_nhat(monkeypatch, de_tai):
    """Trả về sửa rồi sửa xong, đánh giá lại «qua» ⇒ không còn nợ; ngược lại «qua» rồi «trả về sửa» ⇒ còn nợ."""
    tra = _sua_tieu_chi(_danh_gia("tra_ve_sua", "tra_ve_sua"), "RQ5", muc="loi_do", nhan_xet="Thiếu §9",
                        can_cu=CAN_CU)
    for bb in (tra, _danh_gia()):
        assert HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)[0] is not None
    assert HD.danh_gia_cheo_moi_nhat("G4", de_tai)["G4-T1"]["trang_thai"] == "qua"
    assert HD.ghi_bien_ban(STUDY, "G4", tra, de_tai, de_tai.parent.parent)[0] is not None
    assert HD.danh_gia_cheo_moi_nhat("G4", de_tai)["G4-T1"]["trang_thai"] == "tra_ve_sua"
