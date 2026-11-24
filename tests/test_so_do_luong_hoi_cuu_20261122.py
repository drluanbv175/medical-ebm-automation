"""Mẫu sơ đồ luồng theo đúng cách thu thập đã chốt (22/11/2026).

Đo trước khi vá: `hinh_g6` tự tạo `SO_DO_LUONG_<mã>.csv` bằng mẫu tiến cứu chung («Đối tượng tiềm năng được tiếp
cận → Không tham gia: Không đủ tiêu chuẩn; Từ chối tham gia…») kể cả cho đề tài hồi cứu trên hồ sơ có sẵn, miễn đồng
thuận (BTM) — ô «Từ chối» không bao giờ có số thật. Khung đề cương và G6 đoán «hồi cứu» bằng hai quy tắc riêng. Sơ đồ
khung có ô loại cao (BTM: 13 dòng lý do) đè lên ô loại phía trên.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import bieu_do_bao_cao as BB  # noqa: E402
import hinh_g6 as HG  # noqa: E402
import khung_bieu_bang as KBB  # noqa: E402
import ve_bieu_do as VB  # noqa: E402


def _meta(d: Path, mien, cach: str = "") -> None:
    gp = {"G1": {"design": "cross_sectional", "data_collection_method": cach}}
    if mien is not None:
        gp["G2"] = {"icf_waiver_requested": mien}
    (d / "study_meta.json").write_text(json.dumps({"gate_params": gp}, ensure_ascii=False), encoding="utf-8",
                                       newline="\n")


def _doc(p: Path):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ── 1. Khuôn hồi cứu của ve_bieu_do ───────────────────────────────────────────────────────────────────────────────
def test_mau_hoi_cuu_khong_co_buoc_moi_tu_choi():
    hc = VB.mau_so_do_luong("cross_sectional", hoi_cuu=True)
    assert [(r["buoc"], r["loai"]) for r in hc] == [
        ("Hồ sơ trong khung chọn mẫu", "chinh"), ("Không đủ tiêu chuẩn lựa chọn", "loai"),
        ("Hồ sơ đủ tiêu chuẩn lựa chọn", "chinh"), ("Thuộc tiêu chuẩn loại trừ", "loai"),
        ("Đưa vào phân tích", "chinh")]
    for tk in ("cross_sectional", "cohort", "case_control", "diagnostic", "survival"):
        chu = json.dumps(VB.mau_so_do_luong(tk, hoi_cuu=True), ensure_ascii=False).lower()
        assert not any(t in chu for t in ("từ chối", "mời", "phiếu", "tham gia")), tk
    # tiến cứu giữ nguyên; thiết kế không thể hồi cứu (RCT) không đổi khuôn
    assert any("Từ chối" in r["ly_do"] for r in VB.mau_so_do_luong("cross_sectional"))
    assert VB.mau_so_do_luong("rct", hoi_cuu=True) == VB.mau_so_do_luong("rct")


@pytest.mark.parametrize("tk", ["cross_sectional", "cohort", "case_control", "diagnostic", "prediction"])
def test_mau_hoi_cuu_hop_le_voi_phep_kiem_so_hoc_g6(tk):
    """Điền số giả nhất quán ⇒ `kiem_so_hoc_luong` (G6) không báo lỗi: khuôn dùng được ngay khi có số thật."""
    dong = VB.mau_so_do_luong(tk, hoi_cuu=True)
    nhanh: dict = {}
    for r in dong:
        nhanh.setdefault(r["nhanh"], []).append(r)
    for ds in nhanh.values():
        n = 1000
        for r in ds:
            if r["loai"] == "chinh":
                r["n"] = str(n)
            else:
                r["n"] = "10"
                n -= 10
                if r["ly_do"]:
                    ten = [x.split(":")[0].strip() for x in r["ly_do"].split(";") if x.strip()]
                    r["ly_do"] = "; ".join(f"{t}: {10 // len(ten) + (10 % len(ten) if k == 0 else 0)}"
                                           for k, t in enumerate(ten))
    assert BB.kiem_so_hoc_luong(dong)["loi"] == []


@pytest.mark.parametrize("mien, cach, ky_vong", [
    (True, "phiếu tự điền", True), (False, "khai thác nguồn CÓ SẴN trên HIS", False),
    (None, "trích hồ sơ có sẵn", True), (None, "nghiên cứu hồi cứu", True), (None, "phỏng vấn trực tiếp", False)])
def test_la_hoi_cuu_mot_quy_tac(tmp_path, mien, cach, ky_vong):
    _meta(tmp_path, mien, cach)
    meta = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
    assert VB.la_hoi_cuu(meta) is ky_vong
    assert KBB.nap_ngu_canh(tmp_path, "S").hoi_cuu is ky_vong  # khung đề cương dùng CÙNG quy tắc


# ── 2. G6 tự tạo mẫu theo cách thu thập đã chốt ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mien, ky_vong_hc", [(True, True), (False, False)])
def test_g6_tu_tao_mau_theo_cach_thu_thap(tmp_path, mien, ky_vong_hc):
    _meta(tmp_path, mien)
    kq = HG.sinh("x", tmp_path, [], {"phan_tich": []}, "cross_sectional", nap=lambda s, c, loc: None)
    dong = _doc(tmp_path / "SO_DO_LUONG_x.csv")
    assert dong == VB.mau_so_do_luong("cross_sectional", hoi_cuu=ky_vong_hc)
    h = next(x for x in kq["hinh"] if x["id"] == "G5")
    assert h["trang_thai"] == "CHUA_DU_SO" and (("hồ sơ có sẵn" in h["ly_do"]) is ky_vong_hc)


def test_khung_coi_mau_hoi_cuu_g6_tu_tao_la_mau_chung(tmp_path):
    """Mẫu hồi cứu G6 tự tạo chưa mang thông tin riêng ⇒ khung đề cương vẫn dùng khung chuẩn của thiết kế."""
    _meta(tmp_path, True)
    VB.ghi_mau_so_do_luong("cross_sectional", tmp_path / "SO_DO_LUONG_S.csv", hoi_cuu=True)
    assert KBB.nap_ngu_canh(tmp_path, "S").luong == []


def test_cli_mau_so_do_luong_hoi_cuu(tmp_path):
    assert VB.main(["mau-so-do-luong", "--thiet-ke", "cohort", "--hoi-cuu", "--ra", str(tmp_path / "a.csv")]) == 0
    assert _doc(tmp_path / "a.csv") == VB.mau_so_do_luong("cohort", hoi_cuu=True)


# ── 3. Sơ đồ khung: ô loại cao không đè ô loại kề ────────────────────────────────────────────────────────────────
def _hop_ben(fig):
    import matplotlib.patches as mp  # noqa: PLC0415

    ax = fig.axes[0]
    return sorted([(p.get_y(), p.get_y() + p.get_height()) for p in ax.patches
                   if isinstance(p, mp.FancyBboxPatch) and p.get_x() > 0.5])


def test_so_do_o_loai_cao_khong_de_nhau():
    plt = KBB._plt()
    dai = "Bị loại (n = …)\n" + "\n".join(f"– Lý do loại số {k} khá dài để phải ngắt dòng (n = …)" for k in range(9))
    buoc = [("A (n = …)", "Ô loại ngắn (n = …)"), ("B (n = …)", dai), ("C (n = …)", None)]
    fig = KBB._ve_so_do(plt, buoc, [])
    ben = _hop_ben(fig)
    assert len(ben) == 2 and ben[0][1] <= ben[1][0]  # (y dưới, y trên): ô dưới kết thúc trước khi ô trên bắt đầu
    plt.close(fig)
    # ô vừa ⇒ bố cục cũ (ảnh cũ vẽ lại không đổi)
    fig2 = KBB._ve_so_do(plt, [("A (n = …)", "Ngắn (n = …)"), ("B (n = …)", None)], [])
    assert abs(fig2.get_size_inches()[1] - (1.35 * 2 + 0.4)) < 1e-9
    plt.close(fig2)


def test_cao_o_nhieu_dong_tinh_dan_dong_that():
    ngan = "Một\nHai\nBa"
    assert abs(KBB._cao_hop_in(ngan, 0.34) - (3 * 8 * 1.35 / 72 + 0.12)) < 1e-9  # ≤ 6 dòng: công thức cũ
    dai = "\n".join(str(k) for k in range(13))
    assert KBB._cao_hop_in(dai, 0.34) > 13 * 8 * 1.35 / 72 + 0.12


def test_mau_hoi_cuu_co_cho_ly_do_theo_strobe_13b_record_13_1():
    """Ô loại của khuôn hồi cứu có chỗ ghi lý do (STROBE 13b) và có lý do về độ sẵn có của dữ liệu (RECORD 13.1) —
    câu Kết quả G7 dựng từ sổ nêu «vì …» và «thiếu dữ liệu» (giả lập thuần tập hồi cứu từng trượt 13b khi ô loại
    không có lý do)."""
    import run_g7_auto as G7  # noqa: PLC0415

    d = VB.mau_so_do_luong("cohort", hoi_cuu=True)
    assert all(len([x for x in r["ly_do"].split(";") if x.strip()]) >= 2 for r in d if r["loai"] == "loai")
    for r, n in zip(d, (1000, 100, 900, 50, 850)):
        r["n"] = str(n)
    d[1]["ly_do"] = "Không đạt tiêu chuẩn lựa chọn: 70; Hồ sơ thiếu dữ liệu để xét tiêu chuẩn: 30"
    d[3]["ly_do"] = "Có tiêu chí loại trừ của đề tài: 45; Hồ sơ trùng lặp: 5"
    cau = " ".join(G7.khoi_tuyen_chon_g7(BB.kiem_so_hoc_luong(d), "cohort"))
    assert "Không đủ tiêu chuẩn lựa chọn: 100 người, vì" in cau and "thiếu dữ liệu" in cau
