# -*- coding: utf-8 -*-
"""Hạ tầng dùng chung `tools/cong_song.py` (soát từng cổng G0–G10, 04/10/2026).

Khoá các hành vi:
  • trang_thai_song: chấm SỐNG qua evaluate_study(write=False); bản LƯU không bao giờ cho dat=True khi chấm sống ra
    khác; lỗi / SystemExit / vòng lặp ⇒ KHÔNG ĐO ĐƯỢC, dat=False; cổng chưa có evaluate_study ⇒ bản lưu, nguon="luu",
    pin thiết kế bị từ chối ⇒ BLOCKED; đệm theo chữ ký tệp (tệp đổi ⇒ chấm lại).
  • iso_khong_tuong_lai, dau_van_tay, dau_van_tay_tep, xac_nhan_gan_noi_dung.
Ngoại tuyến (thư mục tạm, bộ chấm giả cắm vào sys.modules qua monkeypatch).
"""
from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import cong_song as CS  # noqa: E402


def _ghi(p: Path, v) -> None:
    p.write_text(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")


@pytest.fixture(autouse=True)
def _xoa_dem():
    CS.xoa_dem()
    yield
    CS.xoa_dem()


def _de_tai(tmp_path: Path, luu: str | None = "PASS_G0_CONFIRMED", design: dict | None = None) -> Path:
    out = tmp_path / "exports" / "de-tai-thu"
    out.mkdir(parents=True)
    cp = {"gate": "G0"}
    if luu:
        cp["quality_gate"] = {"status": luu}
    if design is not None:
        cp["design"] = design
    _ghi(out / "G0_checkpoint.json", cp)
    return out


def _cam_bo_cham(monkeypatch, ten: str, evaluate=None):
    mod = types.ModuleType(ten)
    if evaluate is not None:
        mod.evaluate_study = evaluate
    monkeypatch.setitem(sys.modules, ten, mod)
    return mod


# ───────────────────────────────────────────────────────────────────────────── chấm sống
def test_cham_song_pass_thi_dat(tmp_path, monkeypatch):
    goi = []

    def ev(study, out_dir, *, repo_root=None, write=True):
        goi.append((study, Path(out_dir), Path(repo_root), write))
        return {"status": "PASS_G0_CONFIRMED"}
    _cam_bo_cham(monkeypatch, "g0_quality_gate", ev)
    out = _de_tai(tmp_path)
    r = CS.trang_thai_song("G0", "de-tai-thu", out)
    assert r["dat"] is True and r["nguon"] == CS.NGUON_SONG and r["muc"] == "PASS"
    assert goi == [("de-tai-thu", out, tmp_path, False)], "chỉ đọc (write=False), repo_root suy từ out_dir"


def test_ban_luu_pass_ma_cham_song_draft_thi_khong_dat(tmp_path, monkeypatch):
    # Ca thật C1a 04/10/2026: checkpoint G0 lưu PASS_G0_CONFIRMED, chấm sống DRAFT.
    _cam_bo_cham(monkeypatch, "g0_quality_gate",
                 lambda s, out_dir, write=True: {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW"})
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path, luu="PASS_G0_CONFIRMED"))
    assert r["dat"] is False and r["muc"] == "DRAFT" and r["trang_thai_luu"] == "PASS_G0_CONFIRMED"


@pytest.mark.parametrize("loi", [KeyError("x"), ValueError("hỏng"), SystemExit(3)])
def test_bo_cham_hong_la_khong_do_duoc_khong_bao_gio_dat(tmp_path, monkeypatch, loi):
    def ev(study, out_dir, write=True):
        raise loi
    _cam_bo_cham(monkeypatch, "g0_quality_gate", ev)
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path, luu="PASS_G0_CONFIRMED"))
    assert r["dat"] is False and r["nguon"] == CS.NGUON_LOI and r["status"] == CS.KHONG_DO_DUOC
    assert r["trang_thai_luu"] == "PASS_G0_CONFIRMED", "bản lưu chỉ để hiển thị"


def test_bo_cham_tra_khong_phai_dict_la_khong_do_duoc(tmp_path, monkeypatch):
    _cam_bo_cham(monkeypatch, "g0_quality_gate", lambda s, out_dir, write=True: None)
    assert CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path))["nguon"] == CS.NGUON_LOI


def test_khong_co_evaluate_study_thi_doc_ban_luu_kem_tin_cay(tmp_path, monkeypatch):
    _cam_bo_cham(monkeypatch, "g0_quality_gate")
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path, luu="PASS_G0_CONFIRMED"))
    assert r["nguon"] == CS.NGUON_LUU and r["dat"] is True and "kém tin cậy" in r["ly_do"]
    CS.xoa_dem()
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path / "b", luu=None))
    assert r["dat"] is False and r["nguon"] == CS.NGUON_LOI


def test_pin_thiet_ke_bi_tu_choi_luon_bi_chan(tmp_path, monkeypatch):
    _cam_bo_cham(monkeypatch, "g0_quality_gate")
    out = _de_tai(tmp_path, luu="PASS_G0_CONFIRMED", design={"internal_code": "cohort",
                                                            "pin_bi_tu_choi": "quality_improvement"})
    r = CS.trang_thai_song("G0", "de-tai-thu", out)
    assert r["bi_chan"] is True and r["dat"] is False and "quality_improvement" in r["ly_do"]


def test_dem_theo_chu_ky_tep(tmp_path, monkeypatch):
    dem = {"n": 0}

    def ev(study, out_dir, write=True):
        dem["n"] += 1
        return {"status": "PASS_G0_CONFIRMED"}
    _cam_bo_cham(monkeypatch, "g0_quality_gate", ev)
    out = _de_tai(tmp_path)
    CS.trang_thai_song("G0", "de-tai-thu", out)
    CS.trang_thai_song("G0", "de-tai-thu", out)
    assert dem["n"] == 1, "cùng chữ ký tệp ⇒ dùng đệm"
    _ghi(out / "study_meta.json", {"gate_params": {"G0": {"topic": "đổi"}}})
    CS.trang_thai_song("G0", "de-tai-thu", out)
    assert dem["n"] == 2, "tệp đổi ⇒ chấm lại"


def test_vong_lap_cham_song_khong_de_quy_vo_han(tmp_path, monkeypatch):
    goi = {"n": 0}

    def ev(study, out_dir, write=True):
        goi["n"] += 1
        return {"status": CS.trang_thai_song("G0", study, out_dir)["status"]}
    _cam_bo_cham(monkeypatch, "g0_quality_gate", ev)
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path))
    assert r["dat"] is False and r["status"] == CS.KHONG_DO_DUOC
    assert goi["n"] == 1, "lượt gọi lại chính nó phải dừng NGAY (không đệ quy tới giới hạn rồi mới bắt lỗi)"


def test_cong_khong_nap_duoc_bo_cham(tmp_path, monkeypatch):
    r = CS.trang_thai_song("G99", "de-tai-thu", _de_tai(tmp_path))
    assert r["nguon"] == CS.NGUON_LOI and r["dat"] is False


@pytest.mark.parametrize("st,muc", [("PASS_G4_SAP_LOCKED", "PASS"), ("BLOCKED", "BLOCKED"),
                                    ("READY_FOR_SIGNATURE", "READY"), ("PENDING_REAL_REVIEW_SIGNATURE", "READY"),
                                    ("DRAFT_NEEDS_HUMAN_CONTENT", "DRAFT"), ("", CS.KHONG_DO_DUOC),
                                    (None, CS.KHONG_DO_DUOC)])
def test_xep_muc_trang_thai(st, muc):
    assert CS.muc_cua_trang_thai(st) == muc


def test_cham_song_g0_that_tren_thu_muc_tam_khong_sap(tmp_path):
    """Bộ chấm G0 THẬT trên một thư mục thiếu gần hết tệp: hoặc chấm được (không PASS), hoặc không đo được — không
    bao giờ ném lỗi ra ngoài, không bao giờ dat=True."""
    r = CS.trang_thai_song("G0", "de-tai-thu", _de_tai(tmp_path, luu="PASS_G0_CONFIRMED"))
    assert r["dat"] is False and r["nguon"] in (CS.NGUON_SONG, CS.NGUON_LOI)


# ───────────────────────────────────────────────────────────────────────────── xác nhận gắn nội dung
def test_iso_khong_tuong_lai():
    hom_qua = datetime.now() - timedelta(days=1)
    assert CS.iso_khong_tuong_lai(hom_qua.isoformat(timespec="seconds"))
    assert CS.iso_khong_tuong_lai(datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    assert not CS.iso_khong_tuong_lai("2099-12-31T00:00:00")
    assert not CS.iso_khong_tuong_lai("04/10/2026")
    assert not CS.iso_khong_tuong_lai("") and not CS.iso_khong_tuong_lai(None)


def test_dau_van_tay_on_dinh_va_nhay_noi_dung():
    a = CS.dau_van_tay({"b": "Tử vong  30 ngày", "a": [1, 2]})
    assert a == CS.dau_van_tay({"a": [1, 2], "b": "Tử vong 30 ngày"}), "thứ tự khoá và khoảng trắng thừa không đổi dấu"
    import unicodedata
    goc = "Tử vong 30 ngày"
    assert CS.dau_van_tay(unicodedata.normalize("NFD", goc)) == CS.dau_van_tay(unicodedata.normalize("NFC", goc)), \
        "chữ Việt dựng sẵn (NFC) và tổ hợp (NFD, thường gặp khi chép từ macOS) cho cùng dấu"
    assert a != CS.dau_van_tay({"a": [1, 2], "b": "Tử vong 90 ngày"})
    assert len(a) == 16 and all(c in "0123456789abcdef" for c in a)


def test_dau_van_tay_tep_bo_qua_crlf(tmp_path):
    lf, crlf = tmp_path / "lf.md", tmp_path / "crlf.md"
    lf.write_bytes(b"dong 1\ndong 2\n")
    crlf.write_bytes(b"dong 1\r\ndong 2\r\n")
    assert CS.dau_van_tay_tep(lf) == CS.dau_van_tay_tep(crlf)
    assert CS.dau_van_tay_tep(lf) != CS.dau_van_tay_tep(tmp_path / "vang.md")


def test_xac_nhan_gan_noi_dung():
    dau = CS.dau_van_tay("nội dung đã xác nhận")
    hom_qua = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
    assert CS.xac_nhan_gan_noi_dung({"reviewed_at": hom_qua, "dau_van_tay": dau}, dau)[0] is True
    ok, ly_do = CS.xac_nhan_gan_noi_dung({"reviewed_at": hom_qua, "confirmed": True}, dau)
    assert ok is False and "kiểu cũ" in ly_do and dau in ly_do, \
        "xác nhận kiểu cũ: lý do phải nói rõ là kiểu cũ và chỉ dấu hiện tại để chủ nhiệm xác nhận lại"
    ok, ly_do = CS.xac_nhan_gan_noi_dung({"reviewed_at": hom_qua, "dau_van_tay": "0" * 16}, dau)
    assert ok is False and "đã đổi" in ly_do
    assert CS.xac_nhan_gan_noi_dung({"reviewed_at": "2099-01-01T00:00:00", "dau_van_tay": dau}, dau)[0] is False
    assert CS.xac_nhan_gan_noi_dung(True, dau)[0] is False and CS.xac_nhan_gan_noi_dung(None, dau)[0] is False


# ───────────────────────────────────────────────────────────────────────────── hợp đồng băm chuỗi bản thảo (CHUNG-E)
def test_hop_dong_bam_a9_khop_bo_trich_cua_g8(tmp_path):
    import hashlib

    import g8_quality_gate as G8Q
    ban_thao = tmp_path / "G7_A8_MANUSCRIPT_x.md"
    ban_thao.write_bytes("Kết quả: HR 0,80\r\n".encode("utf-8"))
    bam = CS.bam_van_ban_tep(ban_thao)
    assert bam == hashlib.sha256("Kết quả: HR 0,80\n".encode("utf-8")).hexdigest(), "đúng cách run_g8_auto băm"
    bao_cao = "b" * 64
    a9 = "\n".join(["# A9", CS.dong_bam_a9(CS.NHAN_BAM_BAN_THAO, ban_thao.name, bam),
                    CS.dong_bam_a9(CS.NHAN_BAM_BAO_CAO_PHAN_BIEN, "G8_PEER_REVIEW_REPORT_x.md", bao_cao)])
    assert CS.trich_bam_a9(a9) == {"ban_thao": bam, "bao_cao_phan_bien": bao_cao}
    assert G8Q._trich_hash_ban_thao_da_ky(a9) == bam, "dòng do cong_song sinh phải đọc được bằng bộ trích sẵn có của G8"
    assert CS.trich_bam_a9("A9 kiểu cũ") == {"ban_thao": None, "bao_cao_phan_bien": None}
    assert CS.bam_van_ban_tep(tmp_path / "vang.md") is None
