# -*- coding: utf-8 -*-
"""Kiểm `tools/buoc_dang_mo.py` — khâu nào của đề tài đang mở (chỉ thị bác sĩ 22/11/2026: sửa đúng khâu rồi khoá mới
đi tiếp).

Ba lỗi phải bị bắt (kiểm đột biến): (1) bỏ thứ tự G0→G10 — sắp theo chữ, hoặc không dừng ở khâu chưa đạt; (2) coi
READY của cổng cứng là đã khoá; (3) coi «không đo được» là đã khoá. Phần lớn ca dùng bộ đo GIẢ tiêm vào (nhanh, tất
định); một ca dùng chuỗi G0→G1 chốt THẬT (`_chuoi_da_chot`) và chấm sống thật qua CLI, kèm kiểm «không ghi tệp nào».
Dữ liệu tổng hợp, không PII, không gọi mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pytest

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent / "tools"
for _p in (str(_TOOLS), str(_TESTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import buoc_dang_mo as B  # noqa: E402
import gate_contract as GC  # noqa: E402

STUDY = "de-tai-thu-khoa-buoc"
_STATUS_MAC_DINH = {"PASS": "PASS_{g}_GIA", "READY": "READY_FOR_SIGNATURE", "DRAFT": "DRAFT_NEEDS_HUMAN_CONTENT",
                    "BLOCKED": "BLOCKED", "KHONG_DO_DUOC": "KHONG_DO_DUOC"}


def _thu_muc(tmp_path: Path, co: Iterable[str] = B.CONG) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    for g in co:
        (d / f"{g}_checkpoint.json").write_text("{}\n", encoding="utf-8", newline="\n")
    return d


class _BoDo:
    """Bộ đo giả: mức chấm sống theo cổng (mặc định PASS), chữ ký G2, bảng trách nhiệm (mặc định mã 0)."""

    def __init__(self, muc: Optional[Dict[str, str]] = None, status: Optional[Dict[str, str]] = None,
                 g2: bool = True, tn: Optional[Dict[str, str]] = None, vai: Optional[Dict[str, str]] = None,
                 loi_cham: Iterable[str] = (), loi_g2: bool = False, loi_tn: Iterable[str] = ()) -> None:
        self.muc, self.status, self.g2, self.tn, self.vai = muc or {}, status or {}, g2, tn or {}, vai or {}
        self.loi_cham, self.loi_g2, self.loi_tn = set(loi_cham), loi_g2, set(loi_tn)
        self.da_cham: list = []

    def cham(self, gate: str, study: str, out_dir: Path) -> Dict[str, Any]:
        self.da_cham.append(gate)
        if gate in self.loi_cham:
            raise RuntimeError("bộ chấm hỏng (giả)")
        m = self.muc.get(gate, "PASS")
        st = self.status.get(gate, _STATUS_MAC_DINH[m].format(g=gate))
        return {"muc": m, "status": st, "nguon": "song", "ly_do": "giả"}

    def khoa_g2(self, study: str, out_dir: Path):
        if self.loi_g2:
            raise RuntimeError("sổ cái không đọc được (giả)")
        return self.g2, "giả"

    def trach_nhiem(self, study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
        if gate in self.loi_tn:
            raise RuntimeError("bảng trách nhiệm hỏng (giả)")
        kl = self.tn.get(gate, "AGENT_XONG_CHO_NGUOI")
        con = [{"id": f"{gate}-AUTO-01", "viec": "sửa nguồn"}] if kl == "AGENT_CON_VIEC" else []
        return {"ket_luan": kl, "cho_nguoi": [{"id": f"{gate}-HUMAN-01", "vai": self.vai.get(gate, "PI")}],
                "agent_con_viec": con, "cho_cong_truoc": []}

    def chay(self, d: Path) -> Dict[str, Any]:
        return B.phan_tich(STUDY, d, cham=self.cham, khoa_g2=self.khoa_g2, trach_nhiem=self.trach_nhiem)


def _vi_tri(kq: Dict[str, Any]) -> Dict[str, str]:
    return {r["gate"]: r["vi_tri"] for r in kq["cong"]}


# ───────────────────────────────────────────────────────────────────────────── khoá
def test_moi_khau_da_khoa_ma_0(tmp_path):
    kq = _BoDo().chay(_thu_muc(tmp_path))
    assert kq["ma_thoat"] == 0 and kq["khau_dang_mo"] is None and kq["danh_sach_khoa"] == []
    assert set(_vi_tri(kq).values()) == {B.DA_KHOA}


@pytest.mark.parametrize("gate", ["G4", "G5", "G8", "G9", "G10"])
def test_ready_cong_cung_khong_phai_khoa(tmp_path, gate):
    """Đột biến (2): READY của cổng cứng mà tính là khoá ⇒ đề tài trông như đã khoá hết (mã 0)."""
    kq = _BoDo(muc={gate: "READY"}).chay(_thu_muc(tmp_path))
    assert kq["khau_dang_mo"] == gate
    assert kq["ma_thoat"] == 1
    hang = next(r for r in kq["cong"] if r["gate"] == gate)
    assert hang["da_khoa"] is False and hang["vi_tri"] == B.CHO_KY
    assert [m["gate"] for m in kq["danh_sach_khoa"]] == [gate]


def test_g2_khoa_theo_chu_ky_khong_theo_muc(tmp_path):
    """G2 khoá theo g2_da_duyet (cùng nghĩa với G5–G10): chấm sống PASS mà chưa có chữ ký hợp lệ ⇒ vẫn mở."""
    kq = _BoDo(g2=False).chay(_thu_muc(tmp_path))
    assert kq["khau_dang_mo"] == "G2"
    kq2 = _BoDo(muc={"G2": "READY"}, g2=False).chay(_thu_muc(tmp_path / "b"))
    assert kq2["khau_dang_mo"] == "G2" and kq2["danh_sach_khoa"][0]["vai"] == ["IRB"]


def test_khong_do_duoc_khong_phai_khoa(tmp_path):
    """Đột biến (3): «không đo được» mà tính là khoá ⇒ mã 0 giả."""
    kq = _BoDo(muc={"G1": "KHONG_DO_DUOC"}).chay(_thu_muc(tmp_path))
    assert kq["khau_dang_mo"] == "G1" and kq["khau_can_hoan_thien"] == "G1"
    assert kq["ma_thoat"] == 2
    g1 = next(r for r in kq["cong"] if r["gate"] == "G1")
    assert g1["da_khoa"] is None and g1["khong_do"] is True


def test_bo_cham_hong_la_khong_do_duoc(tmp_path):
    kq = _BoDo(loi_cham={"G3"}).chay(_thu_muc(tmp_path))
    assert kq["khau_dang_mo"] == "G3" and kq["ma_thoat"] == 2


def test_chu_ky_g2_khong_do_duoc_khong_phai_khoa(tmp_path):
    kq = _BoDo(loi_g2=True).chay(_thu_muc(tmp_path))
    assert kq["khau_dang_mo"] == "G2" and kq["ma_thoat"] == 2


def test_bang_trach_nhiem_khong_do_duoc_khong_vao_goi_ky(tmp_path):
    kq = _BoDo(muc={"G4": "READY"}, loi_tn={"G4"}).chay(_thu_muc(tmp_path))
    assert kq["danh_sach_khoa"] == [] and kq["khau_can_hoan_thien"] == "G4" and kq["ma_thoat"] == 2


# ───────────────────────────────────────────────────────────────────────────── thứ tự
def test_dung_o_khau_chua_dat_cong_sau_chua_duoc_lam_tiep(tmp_path):
    """Đột biến (1b): không dừng ở khâu chưa đạt ⇒ G4 READY lọt vào gói ký khi G2 còn dự thảo."""
    kq = _BoDo(muc={"G2": "DRAFT", "G4": "READY", "G5": "BLOCKED"}, g2=False).chay(_thu_muc(tmp_path))
    vt = _vi_tri(kq)
    assert kq["khau_dang_mo"] == "G2" and kq["khau_can_hoan_thien"] == "G2"
    assert kq["danh_sach_khoa"] == []
    assert vt["G3"] == B.KHOA_NGOAI_THU_TU and vt["G4"] == B.CHUA_LAM_TIEP and vt["G5"] == B.CHUA_LAM_TIEP
    g4 = next(r for r in kq["cong"] if r["gate"] == "G4")
    assert g4["ghi_chu"] == B.GHI_CHU_CHUA_LAM_TIEP
    assert kq["chua_lam_tiep"] == ["G4", "G5"] and kq["khoa_ngoai_thu_tu"] == ["G3", "G6", "G7", "G8", "G9", "G10"]


def test_thu_tu_so_khong_theo_chu(tmp_path):
    """Đột biến (1a): sắp theo chữ đặt G10 trước G2 ⇒ khâu đang mở thành G10."""
    kq = _BoDo(muc={"G2": "DRAFT", "G10": "READY"}, g2=False).chay(_thu_muc(tmp_path))
    assert [r["gate"] for r in kq["cong"]] == [f"G{i}" for i in range(11)]
    assert kq["khau_dang_mo"] == "G2" and kq["danh_sach_khoa"] == []
    assert _vi_tri(kq)["G10"] == B.CHUA_LAM_TIEP


def test_goi_ky_dung_thu_tu_va_dung_vai(tmp_path):
    muc = {"G2": "READY", "G3": "DRAFT", "G4": "READY", "G5": "BLOCKED", "G6": "DRAFT", "G7": "DRAFT",
           "G8": "DRAFT", "G9": "DRAFT", "G10": "DRAFT"}
    kq = _BoDo(muc=muc, status={"G3": "DRAFT_READY_NEEDS_STATISTICIAN_REVIEW"}, g2=False,
               vai={"G3": "STATISTICIAN"}).chay(_thu_muc(tmp_path))
    ds = kq["danh_sach_khoa"]
    assert [(m["thu_tu"], m["gate"], m["loai"]) for m in ds] == [(1, "G2", "ky"), (2, "G3", "chot"), (3, "G4", "ky")]
    assert ds[0]["vai"] == list(GC._GATE_REQUIRED_STAKEHOLDERS["G2"])
    assert ds[2]["vai"] == list(GC._GATE_REQUIRED_STAKEHOLDERS["G4"])
    assert ds[1]["vai"] == ["STATISTICIAN"] and ds[1]["muc_ky"] == ["G3-HUMAN-01"]
    assert kq["khau_dang_mo"] == "G2" and kq["khau_can_hoan_thien"] == "G5" and kq["ma_thoat"] == 1
    assert kq["chua_lam_tiep"] == ["G6", "G7", "G8", "G9", "G10"]


def test_cong_thuong_chi_vao_goi_khi_toi_buoc_chot(tmp_path):
    kq = _BoDo(muc={"G0": "DRAFT"}, status={"G0": "DRAFT_NEEDS_HUMAN_PARAMETERS"}).chay(_thu_muc(tmp_path))
    assert kq["khau_can_hoan_thien"] == "G0" and kq["danh_sach_khoa"] == []
    kq2 = _BoDo(muc={"G0": "DRAFT"}, status={"G0": "DRAFT_READY_NEEDS_HUMAN_REVIEW"}).chay(_thu_muc(tmp_path / "b"))
    assert [m["gate"] for m in kq2["danh_sach_khoa"]] == ["G0"] and kq2["khau_can_hoan_thien"] is None


def test_he_chua_hoan_thien_khong_vao_goi_ky(tmp_path):
    kq = _BoDo(muc={"G4": "READY"}, tn={"G4": "AGENT_CON_VIEC"}).chay(_thu_muc(tmp_path))
    assert kq["danh_sach_khoa"] == [] and kq["khau_can_hoan_thien"] == "G4" and kq["ma_thoat"] == 1
    g4 = next(r for r in kq["cong"] if r["gate"] == "G4")
    assert "chỗ DUY NHẤT được sửa" in g4["ghi_chu"]


def test_chua_chay_khong_goi_bo_cham(tmp_path):
    bo = _BoDo()
    kq = bo.chay(_thu_muc(tmp_path, co=()))
    assert bo.da_cham == []
    assert kq["khau_dang_mo"] == "G0" and kq["ma_thoat"] == 1
    vt = _vi_tri(kq)
    assert vt["G0"] == B.KHAU_CAN_HOAN_THIEN and {vt[g] for g in B.CONG[1:]} == {B.CHUA_TOI_LUOT}


def test_cong_cung_lay_tu_gate_contract():
    assert B.cong_cung() == tuple(g for g in B.CONG if g in GC._GATE_REQUIRED_STAKEHOLDERS)
    assert B.cong_cung() == ("G2", "G4", "G5", "G8", "G9", "G10")


def test_trinh_bay_noi_ve_san_pham_khong_chia_phan(tmp_path):
    """Chỉ thị 22/11/2026 (thứ hai): lời trình bày nói về sản phẩm — không «phần máy / phần của người»."""
    kq = _BoDo(muc={"G2": "READY", "G5": "DRAFT"}, g2=False).chay(_thu_muc(tmp_path))
    vb = B.in_bao_cao(kq)
    assert "GÓI KÝ ĐÃ CHUẨN BỊ" in vb and "KHÂU ĐANG MỞ: G2" in vb
    for cum in ("phần máy", "phần của", "việc người", "chờ người", "việc còn lại cho người"):
        assert cum not in vb.lower(), cum


# ───────────────────────────────────────────────────────────────────────────── CLI
def test_cli_tham_so_sai_ma_3(tmp_path):
    assert B.main(["--study", "khong-co-de-tai", "--goc", str(tmp_path)]) == 3
    assert B.main(["--study", "../ra-ngoai", "--goc", str(tmp_path)]) == 3
    assert B.main([]) == 3


def _anh_chup(d: Path) -> Dict[str, tuple]:
    return {str(p.relative_to(d)): (p.stat().st_mtime_ns, p.stat().st_size) for p in d.rglob("*") if p.is_file()}


def test_chuoi_that_g0_g1_da_chot_khau_mo_la_g2_va_khong_ghi_gi(tmp_path, capsys):
    """Chuỗi G0→G1 chốt THẬT (chấm sống thật): G0/G1 đã khoá, khâu đang mở G2 (chưa chạy); không tệp nào bị ghi."""
    from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: PLC0415 — import nặng, chỉ ca này cần

    d = tmp_path / "exports" / STUDY
    dung_g0_g1_da_chot(d, STUDY)
    truoc = _anh_chup(tmp_path)
    ma = B.main(["--study", STUDY, "--goc", str(tmp_path), "--json"])
    kq = json.loads(capsys.readouterr().out)
    assert ma == 1 and kq["ma_thoat"] == 1
    vt = _vi_tri(kq)
    assert vt["G0"] == B.DA_KHOA and vt["G1"] == B.DA_KHOA
    assert kq["khau_dang_mo"] == "G2" and kq["khau_can_hoan_thien"] == "G2"
    assert next(r for r in kq["cong"] if r["gate"] == "G2")["muc"] == B.CHUA_CHAY
    assert _anh_chup(tmp_path) == truoc
