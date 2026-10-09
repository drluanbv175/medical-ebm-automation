# -*- coding: utf-8 -*-
"""Trách nhiệm hoàn chỉnh của điều phối cổng (09/10/2026) — `hoi_dong_cong.PHAN_CONG` + lệnh `trach-nhiem`.

Bác sĩ giao: «Từng cổng hãy đảm bảo với các Agent thực hiện một cách hoàn chỉnh các vấn đề của cổng đó và điều phối
của cổng đó chịu trách nhiệm về kết quả thực hiện nhiệm vụ của chính cổng đó». Test chốt:
① mọi tiêu chí mà 11 bộ chấm phát ra có ĐÚNG MỘT bên chịu trách nhiệm (đối chiếu cây cú pháp từng gN_quality_gate.py);
② ô phân công hợp lệ (nhiệm vụ có thật, vai có thật, tiền đề là cổng TRƯỚC, tiêu chí người của cổng cứng thuộc đúng vai
  ký); ③ mục 4b của từng dieu-phoi-gN.md chép đúng bảng; ④ chuẩn hoá đủ 4 khuôn báo cáo (lỗi cũ: `cham-song` bỏ sót
  tiêu chí phê duyệt G2/G4/G8 và toàn bộ G6); ⑤ phân loại + mã thoát; ⑥ bản lưu `--ghi` không làm hỏng biên bản.
Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "TN-THU"


def _ma_bo_cham(gate: str) -> set:
    """Mã tiêu chí bộ chấm `gate` dùng trong MÃ (hằng chuỗi khớp trọn mẫu mã) — không đọc chú thích."""
    src = (REPO_ROOT / "tools" / f"{gate.lower()}_quality_gate.py").read_text(encoding="utf-8")
    rx = re.compile(rf"^{gate}-(AUTO|HUMAN)-\d+[A-Za-z]?$")
    return {n.value for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and rx.match(n.value)}


# ── ① ② bảng phân công ───────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("gate", HD.CONG)
def test_phan_cong_phu_dung_tap_ma_bo_cham(gate):
    ma = _ma_bo_cham(gate)
    assert ma, gate
    assert set(HD.PHAN_CONG[gate]) == ma, (
        f"thiếu gán: {sorted(ma - set(HD.PHAN_CONG[gate]))} · gán thừa: {sorted(set(HD.PHAN_CONG[gate]) - ma)}")


def test_tong_so_tieu_chi_da_gan():
    assert sum(len(v) for v in HD.PHAN_CONG.values()) == 203


@pytest.mark.parametrize("gate", HD.CONG)
def test_moi_o_phan_cong_hop_le(gate):
    cong_cung = GC._GATE_REQUIRED_STAKEHOLDERS
    for ma in HD.PHAN_CONG[gate]:
        pc = HD.phan_cong(gate, ma)
        assert pc is not None, ma
        if pc["loai"] == "agent":
            assert pc["agent"], (ma, pc)
        elif pc["loai"] == "nguoi":
            assert pc["vai"] in HD.THAM_QUYEN and pc["agent"], (ma, pc)
            if gate in cong_cung and "-HUMAN-" in ma:
                assert pc["vai"] in cong_cung[gate], (ma, pc["vai"], "tiêu chí người của cổng cứng phải thuộc vai ký")
        else:
            for g in pc["cong"]:
                if g == "*":
                    assert gate == "G10", (ma, "«*» chỉ dành cho cổng phát hành")
                else:
                    assert g in HD.CONG and int(g[1:]) < int(gate[1:]), (ma, g, "tiền đề phải là cổng TRƯỚC")


# ── ③ tài liệu agent chép đúng bảng ──────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("gate", HD.CONG)
def test_muc_4b_cua_dieu_phoi_cong_chep_dung_phan_cong(gate):
    van_ban = (REPO_ROOT / ".claude" / "agents" / f"{HD.dieu_phoi_cong(gate)}.md").read_text(encoding="utf-8")
    m = re.search(rf"^## 4b\. Trách nhiệm hoàn chỉnh của cổng {gate}\b.*?(?=^## )", van_ban, re.S | re.M)
    assert m, f"{HD.dieu_phoi_cong(gate)}.md thiếu mục 4b"
    dung_lai = {}
    for dong in m.group(0).splitlines():
        o = [x.strip() for x in dong.strip().strip("|").split("|")]
        if len(o) == 2 and o[0].startswith("`"):
            spec = o[0].split("`")[1]
            for ma in (x.strip() for x in o[1].split(",")):
                assert ma not in dung_lai, (gate, ma, "một tiêu chí hai chủ")
                dung_lai[ma] = spec
    assert dung_lai == HD.PHAN_CONG[gate]
    assert f"trach-nhiem --study <mã> --gate {gate}" in van_ban
    assert "CHỊU TRÁCH NHIỆM kết quả" in van_ban and "Bạn không phải owner" not in van_ban


def test_dieu_phoi_tong_nhan_cong_theo_bang_trach_nhiem():
    van_ban = (REPO_ROOT / ".claude" / "agents" / "dieu-phoi-nghien-cuu.md").read_text(encoding="utf-8")
    assert "Giao cổng — nhận cổng" in van_ban and "trach-nhiem --study <mã> --gate G<N>" in van_ban
    hd = (REPO_ROOT / ".claude" / "agents" / "_HOI-DONG-CONG.md").read_text(encoding="utf-8")
    assert "## 1b. Trách nhiệm hoàn chỉnh của điều phối cổng" in hd and "Trách nhiệm cổng (§1b)" in hd


# ── ④ chuẩn hoá bốn khuôn báo cáo ────────────────────────────────────────────────────────────────────────────────────
def test_hang_tieu_chi_doc_du_bon_khuon_va_trang_thai_la_khong_thanh_dat():
    bao = {
        "automatic_criteria": [{"id": "G4-AUTO-01", "status": "PASS"}, {"id": "khong-phai-ma", "status": "PASS"}],
        "approval_criteria": [{"id": "G4-HUMAN-01", "status": "REVIEW", "label": "ký", "action": "ký đi"}],
        "human_approval_criteria": [{"id": "G2-HUMAN-01", "status": "BLOCK"}],
        "checks": [{"id": "G6-AUTO-00", "pass": True}, {"id": "G6-AUTO-02", "pass": None},
                   {"id": "G6-AUTO-03", "pass": False, "blocking": True}, {"id": "G6-AUTO-04", "pass": False},
                   {"id": "G6-AUTO-05", "status": "WEIRD"}],
    }
    r = {x["id"]: x["status"] for x in HD.hang_tieu_chi(bao)}
    assert r == {"G4-AUTO-01": "PASS", "G4-HUMAN-01": "REVIEW", "G2-HUMAN-01": "BLOCK", "G6-AUTO-00": "PASS",
                 "G6-AUTO-02": "REVIEW", "G6-AUTO-03": "BLOCK", "G6-AUTO-04": "REVIEW", "G6-AUTO-05": "REVIEW"}
    assert HD.hang_tieu_chi(None) == [] and HD.hang_tieu_chi({"x": "y"}) == []


def test_cham_song_khong_con_bo_sot_tieu_chi_phe_duyet_va_g6(monkeypatch, tmp_path):
    """Lỗi cũ: chỉ đọc automatic_criteria + human_criteria ⇒ «không còn tiêu chí chưa đạt» khi G4 chưa ký."""
    bao = {"automatic_criteria": [{"id": "G4-AUTO-01", "status": "PASS"}],
           "approval_criteria": [{"id": "G4-HUMAN-01", "status": "REVIEW", "evidence": "chưa ký"}]}
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "DRAFT_X", "nguon": "song", "bao_cao": bao})
    assert [r["id"] for r in HD.cham_song(STUDY, "G4", tmp_path)["chua_dat"]] == ["G4-HUMAN-01"]
    bao6 = {"checks": [{"id": "G6-AUTO-00", "pass": False, "blocking": True, "detail": "thiếu tệp"}]}
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "BLOCKED", "nguon": "song", "bao_cao": bao6})
    assert [r["id"] for r in HD.cham_song(STUDY, "G6", tmp_path)["chua_dat"]] == ["G6-AUTO-00"]


# ── ⑤ phân loại + mã thoát ───────────────────────────────────────────────────────────────────────────────────────────
def _de_tai(tmp_path: Path, du_dau_ra: bool = True) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    if du_dau_ra:
        for ten in (f"G3_A4_SAMPLE_SIZE_{STUDY}.md", "G3_checkpoint.json"):
            (out / ten).write_text("{}\n", encoding="utf-8", newline="\n")
    return out


def _song(monkeypatch, theo_cong: dict, thiet_ke=None):
    """Giả chấm sống: theo_cong = {cổng: (status, {mã: trạng thái})}; cổng vắng ⇒ PASS_<cổng>_X."""
    def gia(gate, study, out_dir, repo_root=None):
        st, hang = theo_cong.get(gate, (f"PASS_{gate}_X", {}))
        return {"status": st, "nguon": "song",
                "bao_cao": {"automatic_criteria": [{"id": k, "status": v, "action": f"việc {k}"}
                                                   for k, v in hang.items()]}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})


def _g3(**doi):
    hang = {ma: "PASS" for ma in HD.PHAN_CONG["G3"]}
    hang.update(doi)
    return hang


def test_moi_tieu_chi_dat_va_du_dau_ra_la_dat_tieu_chi(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("PASS_G3_CONFIRMED", _g3())})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "DAT_TIEU_CHI" and HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == 0
    assert kq["so_dat"] == kq["so_tieu_chi"] == 26 and kq["dieu_phoi"] == "dieu-phoi-g3"


def test_chi_con_viec_cua_nguoi_la_agent_xong_va_neu_ai_chuan_bi(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_READY", _g3(**{"G3-HUMAN-01": "REVIEW"}))})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "AGENT_XONG_CHO_NGUOI" and HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == 0
    m = kq["cho_nguoi"][0]
    assert (m["vai"], m["chuan_bi"], m["agent_chuan_bi"]) == ("STATISTICIAN", "G3-T1", "co-mau-nghien-cuu")


def test_tieu_chi_cua_agent_chua_dat_la_agent_con_viec(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**{"G3-AUTO-05": "REVIEW", "G3-HUMAN-01": "REVIEW"}))})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "AGENT_CON_VIEC" and HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == 1
    assert [(m["id"], m["nhiem_vu"], m["agent"]) for m in kq["agent_con_viec"]] == [
        ("G3-AUTO-05", "G3-T1", "co-mau-nghien-cuu")]
    assert "G3-AUTO-05" in HD.in_trach_nhiem(kq)


def test_thieu_dau_ra_nhiem_vu_la_agent_con_viec(monkeypatch, tmp_path):
    out = _de_tai(tmp_path, du_dau_ra=False)
    _song(monkeypatch, {"G3": ("PASS_G3_CONFIRMED", _g3())})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "AGENT_CON_VIEC"
    assert {m["id"] for m in kq["agent_con_viec"]} >= {"G3-T1:dau-ra", "G3-T2:dau-ra", "G3-T3:dau-ra"}


def test_tien_de_chua_dat_khi_khong_bi_chan_van_uu_tien_viec_agent(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**{"G3-AUTO-01": "REVIEW"}))})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "CHO_CONG_TRUOC" and kq["cho_cong_truoc"][0]["cong"] == ["G0", "G1"]
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**{"G3-AUTO-01": "REVIEW", "G3-AUTO-09": "REVIEW"}))})
    assert HD.trach_nhiem(STUDY, "G3", out)["ket_luan"] == "AGENT_CON_VIEC", \
        "cổng chưa bị chặn: việc agent làm được ngay vẫn là việc của điều phối cổng này"


def test_cong_bi_chan_dung_som_tu_cham_cong_tien_de(monkeypatch, tmp_path):
    """Đúng ca G6 của C1a: bộ chấm dừng ở G6-AUTO-00 nên không phát G6-AUTO-01 (^G4) — G4 chưa khoá ⇒ chờ cổng trước."""
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("DRAFT_NEEDS_HUMAN_CONTENT", {})})
    kq = HD.trach_nhiem(STUDY, "G6", out)
    assert kq["ket_luan"] == "CHO_CONG_TRUOC"
    assert [m["id"] for m in kq["cho_cong_truoc"]] == ["G6:tien-de-G4"]
    assert "G6-AUTO-01" in kq["chua_cham"] and kq["agent_con_viec"], "việc agent vẫn được liệt kê"
    _song(monkeypatch, {"G6": ("BLOCKED", {"G6-AUTO-00": "BLOCK"}), "G4": ("PASS_G4_SAP_LOCKED", {})})
    assert HD.trach_nhiem(STUDY, "G6", out)["ket_luan"] == "AGENT_CON_VIEC", "G4 đã khoá ⇒ là việc của G6"


def test_ma_chua_gan_va_khong_do_duoc(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**{"G3-AUTO-99": "REVIEW"}))})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "CHUA_PHAN_CONG" and HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == 1
    _song(monkeypatch, {"G3": (None, {})})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "KHONG_DO_DUOC" and HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == 2
    _song(monkeypatch, {"G3": (None, _g3())})
    assert HD.trach_nhiem(STUDY, "G3", out)["ket_luan"] == "KHONG_DO_DUOC", \
        "bộ chấm lỗi giữa chừng mà còn dòng PASS — vẫn KHÔNG ĐO ĐƯỢC, không bao giờ «đạt»"


@pytest.mark.parametrize("thiet_ke, ap_dung_t5", [("rct", True), ("cross_sectional", False), (None, None)])
def test_nhiem_vu_co_dieu_kien_theo_thiet_ke(monkeypatch, tmp_path, thiet_ke, ap_dung_t5):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    _song(monkeypatch, {"G1": ("DRAFT_X", {ma: "PASS" for ma in HD.PHAN_CONG["G1"]})}, thiet_ke=thiet_ke)
    kq = HD.trach_nhiem(STUDY, "G1", out)
    nv = {n["ma"]: n for n in kq["nhiem_vu"]}
    assert nv["G1-T5"]["ap_dung"] is ap_dung_t5 and nv["G1-T4"]["ap_dung"] is None
    assert "G1-T4" in kq["nhiem_vu_chua_xac_dinh"]
    assert bool(nv["G1-T5"]["dau_ra_thieu"]) is bool(ap_dung_t5), "chỉ đòi đầu ra của nhiệm vụ áp dụng"


# ── ⑥ bản lưu lúc bàn giao + CLI ─────────────────────────────────────────────────────────────────────────────────────
def test_ghi_trach_nhiem_o_thu_muc_con_khong_bi_doc_thanh_bien_ban_hong(monkeypatch, tmp_path):
    out = _de_tai(tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**{"G3-HUMAN-01": "REVIEW"}))})
    p = HD.ghi_trach_nhiem(HD.trach_nhiem(STUDY, "G3", out), out)
    assert p.parent == out / "hoi_dong" / "G3" / "trach_nhiem"
    ban = json.loads(p.read_text(encoding="utf-8"))
    assert ban["ket_luan"] == "AGENT_XONG_CHO_NGUOI" and "dieu-phoi-g3 chịu trách nhiệm" in ban["cam_ket"]
    assert set(ban["tai_lieu_luc_ghi"]) == {f"G3_A4_SAMPLE_SIZE_{STUDY}.md", "G3_checkpoint.json"}
    assert HD.doc_bien_ban(out, "G3") == [] and HD.tom_tat_cong("G3", out)["trang_thai"] == "CHƯA HỌP"


@pytest.mark.parametrize("hang, ma", [({}, 0), ({"G3-AUTO-05": "REVIEW"}, 1)])
def test_cli_trach_nhiem_ma_thoat(monkeypatch, tmp_path, capsys, hang, ma):
    out = _de_tai(tmp_path)
    monkeypatch.setattr(HD, "BASE", tmp_path)
    _song(monkeypatch, {"G3": ("DRAFT_X", _g3(**hang))})
    assert HD.main(["trach-nhiem", "--study", STUDY, "--gate", "G3", "--ghi"]) == ma
    ra = capsys.readouterr().out
    assert "TRÁCH NHIỆM CỔNG G3" in ra and "đã lưu: hoi_dong/G3/trach_nhiem/TN-" in ra.replace("\\", "/")
    assert list((out / "hoi_dong" / "G3" / "trach_nhiem").glob("TN-*.json"))
