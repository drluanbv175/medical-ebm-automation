# -*- coding: utf-8 -*-
"""Biên bản XỬ LÝ VIỆC SỬA (`xu_ly_viec_sua`) — 17/10/2026.

Bác sĩ: «Đã họp và tốn token với lần họp vừa rồi». Biên bản hội đồng gắn SHA-256 tài liệu; agent làm đúng việc hội đồng
giao thì tài liệu đổi ⇒ biên bản «cũ» ⇒ hồ sơ cổng đòi họp lại toàn bộ (C1a G0: 4,2–8,7 triệu token). Test chốt:
① gốc «qua» + xử lý đủ ⇒ vẫn «qua», không chấm lại; ② thiếu một việc ⇒ từ chối ghi; ③ gốc «trả về sửa» + xử lý ⇒
«đã sửa — chờ chấm lại» (KHÔNG thành «qua»), hết «việc agent còn nợ»; ④ tài liệu đổi SAU biên bản xử lý ⇒ lại «cũ»;
⑤ kiểm máy nhiệm vụ còn lỗi ⇒ từ chối; ⑥ tranh biện «sửa kết luận» + xử lý ⇒ DP còn hiệu lực, không «CẦN SỬA»;
⑦ rào thẩm quyền / chuyển PI phải ghi nơi trình; ⑧ Markdown + khuôn `mau`. Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402
from test_hoi_dong_tiet_kiem_20261010 import SAP, STUDY, _danh_gia, _nv, _song, _tranh_bien  # noqa: E402


@pytest.fixture()
def de_tai(tmp_path: Path, monkeypatch) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / SAP).write_text("\n".join(f"Dòng {i} của SAP" for i in range(1, 21)) + "\n", encoding="utf-8",
                           newline="\n")
    (out / "G4_checkpoint.json").write_text('{"gate": "G4"}\n', encoding="utf-8", newline="\n")
    monkeypatch.setattr(HD, "KIEM_NHIEM_VU", {"G4-T1": ("kiểm giả", lambda _o, _s: [])})
    _song(monkeypatch)
    return out


def _ghi(de_tai: Path, bb: dict):
    return HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)


def _ghi_ok(de_tai: Path, bb: dict) -> str:
    p, kq = _ghi(de_tai, bb)
    assert p is not None, kq["loi"]
    return json.loads(p.read_text(encoding="utf-8"))["id"]


def _dg_co_luu_y() -> dict:
    bb = _danh_gia("dat_co_luu_y", "dat_co_luu_y")
    t = next(t for t in bb["danh_gia"][1]["tieu_chi"] if t["ma"] == "RQ5")
    t.update(muc="can_sua", nhan_xet="§9 chưa nêu cách xử lý dữ liệu thiếu",
             can_cu=[{"loai": "tep", "gia_tri": f"{SAP}:9"}])
    return bb


def _xl(goc: str, *nguon: str, **them) -> dict:
    viec = [{"nguon": n, "noi_dung": "việc biên bản giao", "cach_xu_ly": "da_sua", "mo_ta": "Đã bổ sung §9",
             "can_cu": [{"loai": "tep", "gia_tri": f"{SAP}:9"}]} for n in nguon]
    return {"loai": HD.LOAI_XU_LY, "bien_ban_goc": goc, "nguoi_ghi": "dieu-phoi-g4 (agent làm việc sửa)",
            "viec": viec, **them}


def _sua_sap(de_tai: Path, noi_dung: str = "SAP đã sửa theo biên bản\n") -> None:
    (de_tai / SAP).write_text(noi_dung, encoding="utf-8", newline="\n")


def test_goc_qua_co_luu_y_xu_ly_du_thi_van_qua(de_tai):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    _sua_sap(de_tai)
    assert _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")["danh_gia_cheo"]["trang_thai"] == "cu"
    xl = _ghi_ok(de_tai, _xl(goc, "giam-khao-cong:RQ5"))
    assert xl.startswith("G4-XL-")
    dg = HD.danh_gia_cheo_moi_nhat("G4", de_tai)["G4-T1"]
    assert dg == {"trang_thai": "qua", "id": goc, "xu_ly": xl}
    t1 = _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")
    assert t1["tinh_trang"] == "da_qua" and not t1["can_cham"] and xl in t1["ly_do"]
    assert not any("HỎNG" in str(x) for x in HD.tom_tat_cong("G4", de_tai)["ly_do"])


def test_thieu_mot_viec_thi_tu_choi(de_tai):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    p, kq = _ghi(de_tai, _xl(goc, "phan-tich-thong-ke:RQ5"))
    assert p is None and any("chưa xử lý 1 việc" in x and "giam-khao-cong:RQ5" in x for x in kq["loi"])


def test_goc_tra_ve_sua_chi_thanh_da_sua_cho_cham_lai(de_tai):
    goc = _ghi_ok(de_tai, _danh_gia("tra_ve_sua", "tra_ve_sua"))
    assert any(x["id"] == "G4-T1:danh-gia-cheo" for x in HD.trach_nhiem(STUDY, "G4", de_tai)["agent_con_viec"])
    _sua_sap(de_tai)
    xl = _ghi_ok(de_tai, _xl(goc, "giam-khao-cong:RQ5"))
    dg = HD.danh_gia_cheo_moi_nhat("G4", de_tai)["G4-T1"]
    assert dg["trang_thai"] == "da_sua_cho_cham_lai" and dg["xu_ly"] == xl, "tự sửa KHÔNG bao giờ tự thành «qua»"
    t1 = _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")
    assert t1["can_cham"] and "chưa chấm lại độc lập" in t1["ly_do"]
    tn = HD.trach_nhiem(STUDY, "G4", de_tai)
    assert not any(x["id"] == "G4-T1:danh-gia-cheo" for x in tn["agent_con_viec"]), "agent đã sửa — hết nợ sửa"
    tt = HD.tom_tat_cong("G4", de_tai)
    assert not any("G4-T1: hội đồng yêu cầu sửa" == x for x in tt["ly_do"])


def test_tai_lieu_doi_sau_bien_ban_xu_ly_thi_lai_cu(de_tai):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    _sua_sap(de_tai)
    _ghi_ok(de_tai, _xl(goc, "giam-khao-cong:RQ5"))
    _sua_sap(de_tai, "SAP đổi THÊM sau khi ghi biên bản xử lý\n")
    assert HD.danh_gia_cheo_moi_nhat("G4", de_tai)["G4-T1"]["trang_thai"] == "cu"


def test_kiem_may_con_loi_thi_tu_choi(de_tai, monkeypatch):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    monkeypatch.setattr(HD, "KIEM_NHIEM_VU", {"G4-T1": ("kiểm giả", lambda _o, _s: ["§9 vẫn trống"])})
    p, kq = _ghi(de_tai, _xl(goc, "giam-khao-cong:RQ5"))
    assert p is None and any("kiểm máy G4-T1 còn lỗi sau khi sửa: §9 vẫn trống" in x for x in kq["loi"])


def test_tranh_bien_sua_ket_luan_da_xu_ly_thi_khong_can_sua(de_tai):
    tb = _tranh_bien("DP-G4-1", "sua_ket_luan")
    tb["phan_quyet"]["viec_sua"] = ["Bổ sung cách xử lý dữ liệu thiếu vào §9 — thiet-ke-nghien-cuu"]
    goc = _ghi_ok(de_tai, tb)
    assert "DP-G4-1: hội đồng yêu cầu sửa" in HD.tom_tat_cong("G4", de_tai)["ly_do"]
    _sua_sap(de_tai)
    assert "DP-G4-1" not in HD._tranh_bien_hieu_luc("G4", de_tai)
    xl = _ghi_ok(de_tai, _xl(goc, "viec_sua:1"))
    t = HD._tranh_bien_hieu_luc("G4", de_tai)["DP-G4-1"]
    assert t["id"] == goc and t["xu_ly"] == xl
    assert "DP-G4-1: hội đồng yêu cầu sửa" not in HD.tom_tat_cong("G4", de_tai)["ly_do"]
    dp = next(d for d in HD.ho_so_cong(STUDY, "G4", de_tai)["dp"] if d["ma"] == "DP-G4-1")
    assert not dp["can_tranh_bien"] and xl in dp["ly_do"]


def test_rao_tham_quyen_va_chuyen_pi(de_tai):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    bb = _xl(goc, "giam-khao-cong:RQ5")
    bb["viec"][0]["mo_ta"] = "Đã sửa, cổng PASS_G4_SAP_LOCKED"
    p, kq = _ghi(de_tai, bb)
    assert p is None and any("thẩm quyền người" in x for x in kq["loi"])
    bb = _xl(goc, "giam-khao-cong:RQ5")
    bb["viec"][0].update(cach_xu_ly="chuyen_pi", can_cu=[])
    p, kq = _ghi(de_tai, bb)
    assert p is None and any("noi_trinh_pi" in x for x in kq["loi"])
    bb["viec"][0]["noi_trinh_pi"] = "PI quyết khi chốt G4 (nút chốt G4, VIỆC 2/3)"
    assert _ghi(de_tai, bb)[0] is not None


def test_goc_khong_ton_tai_thi_tu_choi(de_tai):
    p, kq = _ghi(de_tai, _xl("G4-DG-20990101T000000-deadbeef", "giam-khao-cong:RQ5"))
    assert p is None and any("bien_ban_goc" in x for x in kq["loi"])


def test_markdown_va_khuon(de_tai):
    goc = _ghi_ok(de_tai, _dg_co_luu_y())
    _sua_sap(de_tai)
    p, _kq = _ghi(de_tai, _xl(goc, "giam-khao-cong:RQ5"))
    md = p.with_suffix(".md").read_text(encoding="utf-8")
    assert f"Xử lý việc sửa của biên bản `{goc}`" in md and "KHÔNG phải đánh giá độc lập" in md
    assert "| `giam-khao-cong:RQ5` |" in md
    khuon = HD.mau_bien_ban(HD.LOAI_XU_LY, "G4")
    assert khuon["loai"] == HD.LOAI_XU_LY and khuon["viec"][0]["cach_xu_ly"] == "|".join(HD.CACH_XU_LY)
    assert HD.viec_can_xu_ly(json.loads(Path(str(p).replace(p.name, f"{goc}.json")).read_text(
        encoding="utf-8"))) == ["giam-khao-cong:RQ5"]
