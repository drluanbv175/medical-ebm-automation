# -*- coding: utf-8 -*-
"""Kiểm máy cấp nhiệm vụ G4-T2 (SAP RCT §13–§15) + khối «tiêu chí tiền đề» sinh trong §2 của 11 điều phối (10/10/2026).

Bác sĩ giao «Tiếp tục hoàn thiện từng Agent và từng điều phối». Đo 10/10: G4-T2 (`an-toan-nghien-cuu`, RCT) không có
tiêu chí máy nào gắn trách nhiệm dù bước ký G4 đã kiểm §13–§15; văn xuôi «Tiền đề» §2 của điều phối lệch tiêu chí bộ
chấm thật kiểm (G3 thiếu G0, G8 thiếu G2, G9 thiếu G2, G2 ghi G0 trong khi G2-AUTO-02 chỉ chấm sống G1).
Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import sinh_tai_lieu_trach_nhiem as SG  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "RCT-THU"
_MUC = {f"§{i}": f"Nội dung thật của mục {i}." for i in range(1, 16)}


def _sap(**doi) -> str:
    muc = dict(_MUC)
    muc.update(doi)
    than = "\n\n".join(f"### {so} Mục\n{nd}" for so, nd in muc.items() if nd is not None)
    return f"# A5 — SAP\n\n## PHẦN 3 — SAP\n\n{than}\n\n## PHẦN 5 — CHỨNG CHỈ KHOÁ\nĐã điền.\n"


def _de_tai(tmp_path: Path, sap: str) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(sap, encoding="utf-8", newline="\n")
    (out / "G4_checkpoint.json").write_text("{}\n", encoding="utf-8", newline="\n")
    return out


# ── G4-T2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_sap_rct_du_13_15_qua(tmp_path):
    assert HD._kiem_sap_rct(_de_tai(tmp_path, _sap()), STUDY) == []


@pytest.mark.parametrize("doi, can", [
    ({"§14": None}, "SAP §14"),
    ({"§13": "[CẦN BÁC SĨ] quy tắc dừng"}, "SAP §13"),
    ({"§15": None, "§13": None}, "SAP §13"),
])
def test_sap_rct_thieu_hoac_con_o_trong_13_15_bi_bat(tmp_path, doi, can):
    loi = HD._kiem_sap_rct(_de_tai(tmp_path, _sap(**doi)), STUDY)
    assert loi and any(x.startswith(can) for x in loi), loi


def test_muc_1_12_trong_khong_quy_cho_g4t2(tmp_path):
    """§1–§12 là của G4-T1 (tiêu chí G4-AUTO-10) — kiểm G4-T2 không nhận lỗi của chúng."""
    assert HD._kiem_sap_rct(_de_tai(tmp_path, _sap(**{"§4": None, "§9": "[CẦN BÁC SĨ]"})), STUDY) == []


@pytest.mark.parametrize("thiet_ke, chay", [("rct", True), ("cohort", False), (None, False)])
def test_chi_kiem_khi_chac_la_rct(monkeypatch, tmp_path, thiet_ke, chay):
    out = _de_tai(tmp_path, _sap(**{"§14": None}))
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G4"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G4_SAP_LOCKED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})
    kq = HD.trach_nhiem(STUDY, "G4", out)
    nv = {n["ma"]: n for n in kq["nhiem_vu"]}
    viec = [m for m in kq["agent_con_viec"] if m["id"] == "G4-T2:kiem-may"]
    assert bool(viec) is chay and (nv["G4-T2"].get("kiem_may") is not None) is chay
    if chay:
        assert viec[0]["agent"] == "an-toan-nghien-cuu" and kq["ket_luan"] == "AGENT_CON_VIEC"


# ── Khối tiêu chí tiền đề §2 ─────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("gate", HD.CONG)
def test_muc_2_cua_dieu_phoi_neu_du_tieu_chi_tien_de(gate):
    van = (ROOT / ".claude" / "agents" / f"{HD.dieu_phoi_cong(gate)}.md").read_text(encoding="utf-8")
    muc2 = re.search(r"^## 2\. .*?(?=^## 3\. )", van, re.S | re.M).group(0)
    assert muc2.count("<!-- TIEN-DE-CONG:BAT-DAU") == 1 and SG.DAU_TIEN_DE[1] in muc2
    tien_de = [ma for ma, s in HD.PHAN_CONG[gate].items() if s.startswith("^")]
    for ma in tien_de:
        assert f"`{ma}` →" in muc2, (gate, ma)
    if not tien_de:
        assert "không có — " in muc2
    assert muc2.index("TIEN-DE-CONG:KET-THUC") < muc2.index("- Lệnh: `python3 tools/hoi_dong_cong.py cham-song")


def test_khoi_tien_de_idempotent_va_bao_loi_khi_thieu_neo():
    van = "## 2. Tiền đề\n- G1 PASS.\n- Lệnh: `python3 tools/hoi_dong_cong.py cham-song --study x --gate G3`\n## 3. x\n"
    mot = SG._ap_dung_tien_de(van, "G3")
    assert SG._ap_dung_tien_de(mot, "G3") == mot and "`G3-AUTO-01` → G0, G1" in mot
    assert mot.index("TIEN-DE-CONG:KET-THUC") < mot.index("- Lệnh: `python3") < mot.index("## 3."), \
        "lần chèn đầu phải nằm TRONG §2, ngay trước dòng lệnh chấm sống"
    with pytest.raises(ValueError):
        SG._ap_dung_tien_de("## 2. Tiền đề\nkhông có dòng lệnh\n", "G3")
