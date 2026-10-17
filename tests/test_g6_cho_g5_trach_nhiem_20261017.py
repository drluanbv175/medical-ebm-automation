# -*- coding: utf-8 -*-
"""G6 chờ G5 thay vì «agent còn việc» — 17/10/2026 (C1a: PI vừa ký G4 ⇒ G6 hiện AGENT_CON_VIEC dù chưa có dữ liệu khoá).

Bộ chấm G6 dừng sớm ở G6-AUTO-00 (chưa có kịch bản/checkpoint) nên chỉ phát tiêu chí gắn «^G4»; G6-T1 «phân tích trên dữ
liệu ĐÃ KHOÁ» lại cần từ điển REDCap + DATA_LOCK của G5, và G6-AUTO-06 chỉ xét G5 khi ĐÃ có tệp kết quả. Test chốt:
① cổng G6 bị chặn, G4 PASS, G5 chưa PASS ⇒ CHO_CONG_TRUOC với «G6:tien-de-G5», việc agent vẫn được liệt kê;
② G4 lẫn G5 chưa PASS ⇒ nêu cả hai, đúng thứ tự cổng; G5 PASS ⇒ trở lại AGENT_CON_VIEC (việc thật của G6);
③ cổng CHƯA bị chặn ⇒ tiền đề cả cổng không đè việc agent làm được ngay;
④ hồ sơ hội đồng (`ho_so_cong`) cũng nêu G5 là cổng trước chưa đạt;
⑤ bảng TIEN_DE_CA_CONG chỉ trỏ cổng TRƯỚC có thật.
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

STUDY = "G6-CHO-G5"


def _song(monkeypatch, theo_cong: dict) -> None:
    """Giả chấm sống: theo_cong = {cổng: (status, {mã: trạng thái})}; cổng vắng ⇒ PASS_<cổng>_X."""
    def gia(gate, study, out_dir, repo_root=None):
        st, hang = theo_cong.get(gate, (f"PASS_{gate}_X", {}))
        return {"status": st, "nguon": "song",
                "bao_cao": {"automatic_criteria": [{"id": k, "status": v, "action": f"việc {k}"}
                                                   for k, v in hang.items()]}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})


def _out(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    return out


def test_g6_bi_chan_g4_da_khoa_g5_chua_dat_la_cho_cong_truoc(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("PASS_G4_SAP_LOCKED", {}),
                        "G5": ("BLOCKED", {})})
    kq = HD.trach_nhiem(STUDY, "G6", out)
    assert kq["ket_luan"] == "CHO_CONG_TRUOC"
    assert [m["id"] for m in kq["cho_cong_truoc"]] == ["G6:tien-de-G5"]
    assert kq["cho_cong_truoc"][0]["cong"] == ["G5"] and "BLOCKED" in kq["cho_cong_truoc"][0]["viec"]
    assert any(m["id"] == "G6-AUTO-00" for m in kq["agent_con_viec"]), "việc agent vẫn được liệt kê"


def test_g6_neu_ca_g4_lan_g5_va_tro_lai_viec_agent_khi_g5_dat(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("DRAFT_NEEDS_HUMAN_CONTENT", {}),
                        "G5": (None, {})})
    kq = HD.trach_nhiem(STUDY, "G6", out)
    assert [m["id"] for m in kq["cho_cong_truoc"]] == ["G6:tien-de-G4", "G6:tien-de-G5"]
    assert "không đo được" in kq["cho_cong_truoc"][1]["viec"], "G5 không đo được KHÔNG phải «đạt»"
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("PASS_G4_SAP_LOCKED", {}),
                        "G5": ("PASS_G5_DATA_LOCKED", {})})
    assert HD.trach_nhiem(STUDY, "G6", out)["ket_luan"] == "AGENT_CON_VIEC", "G4 + G5 đã đạt ⇒ là việc của G6"


def test_cong_chua_bi_chan_khong_bi_tien_de_ca_cong_de(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {"G6": ("DRAFT_NEEDS_HUMAN_PARAMETERS", {"G6-AUTO-02": "REVIEW"}), "G5": ("BLOCKED", {})})
    kq = HD.trach_nhiem(STUDY, "G6", out)
    assert kq["ket_luan"] == "AGENT_CON_VIEC" and not kq["cho_cong_truoc"]


def test_ho_so_hoi_dong_neu_g5_la_cong_truoc_chua_dat(monkeypatch, tmp_path):
    out = _out(tmp_path)
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("PASS_G4_SAP_LOCKED", {}),
                        "G5": ("BLOCKED", {})})
    hs = HD.ho_so_cong(STUDY, "G6", out)
    assert {"gate": "G5", "trang_thai_song": "BLOCKED"} in hs["cong_truoc_chua_dat"]
    assert all(c["gate"] != "G4" for c in hs["cong_truoc_chua_dat"])


def test_bang_tien_de_ca_cong_chi_tro_cong_truoc_co_that():
    assert HD.TIEN_DE_CA_CONG["G6"] == ("G5",)
    for gate, ds in HD.TIEN_DE_CA_CONG.items():
        assert gate in HD.CONG and ds, gate
        assert all(g in HD.CONG and HD.CONG.index(g) < HD.CONG.index(gate) for g in ds), (gate, ds)
