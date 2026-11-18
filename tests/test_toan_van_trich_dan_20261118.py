"""Hồi quy 18/11/2026 — chốt TOÀN VĂN cho mọi trích dẫn của đề tài (bác sĩ: «tất cả trích dẫn cho nghiên cứu … phải
luôn là toàn văn, nếu không phải toàn văn và không thể lấy được toàn văn thì loại bỏ»; cùng luật 25/10/2026).

Đo 18/11 trên thư viện EndNote thật: đề cương nộp C1a 24/58 TLTK có toàn văn mà không cổng nào báo. Nay
`tools/toan_van_trich_dan.py` đọc biên nhận `TOAN_VAN_TLTK_<mã>.json` và G10-AUTO-12 chặn fail-closed.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import danh_muc_trich_dan as DMT  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import gia_lap_tron_vong as GTV  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import toan_van_trich_dan as TVT  # noqa: E402

from tests.test_g10_quality_gate import _criterion, _patch_upstream, _write_ready_fixture  # noqa: E402

S = "SYNTH-TOAN-VAN"
DE_CUONG = (
    "# ĐỀ CƯƠNG\n\nNền tảng [1, 2]. Văn bản quy phạm [3].\n\n# 7. TÀI LIỆU THAM KHẢO\n\n"
    "1. Tác giả A. Bài một. Tạp chí. 2020. doi:10.1000/abc1. PMID: 11111111.\n"
    "2. Tác giả B. Bài hai. Tạp chí. 2021. PMID: 22222222.\n"
    "3. Bộ Y tế. Quyết định số 56/QĐ-BYT về đo lường hài lòng. Hà Nội; 2024.\n\n# PHỤ LỤC A\n\n9. Không phải TLTK.\n"
)
BAN_THAO = ("# Bản thảo\n\n## TÀI LIỆU THAM KHẢO (Vancouver format)\n\n"
            "[1] [Tác giả] et al. Bài hai. Tạp chí. 2021; PMID:22222222\n"
            "[2] [Tác giả] et al. Bài ba. Tạp chí. 2022; PMID:33333333\n")


def _ghi(p: Path, van: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(van, encoding="utf-8", newline="\n")


def _de_tai(tmp_path: Path, ban_thao: bool = False) -> Path:
    d = tmp_path / S
    _ghi(d / f"DE_CUONG_NOP_HOI_DONG_{S}.md", DE_CUONG)
    if ban_thao:
        _ghi(d / f"G7_A8_MANUSCRIPT_{S}.md", BAN_THAO)
    return d


def _bien_nhan(d: Path, sua: dict | None = None) -> None:
    """Biên nhận đủ toàn văn; `sua` = {khoá: các trường đè lên mục khớp khoá}."""
    bn = TVT.dung_bien_nhan(d, S, toan_van=True, nguon="endnote", nguoi_do="kiểm thử")
    for m in bn["muc"]:
        for k, v in (sua or {}).items():
            if k in m["khoa"]:
                m.update(v)
    TVT.ghi_bien_nhan(d, S, bn)


HAI_LAN = [{"lan": "truy_cap_mo", "ngay": "2026-11-01", "ket_qua": "không có bản mở"},
           {"lan": "trinh_duyet", "ngay": "2026-11-02", "ket_qua": "không có quyền"}]


# ── tách TLTK & khoá ──────────────────────────────────────────────────────────────────────────────────────────────
def test_tach_tltk_nhan_hai_khuon_va_dung_o_tieu_de_ke_tiep():
    assert set(TVT.tach_tltk(DE_CUONG)) == {1, 2, 3}  # «9. Không phải TLTK» của PHỤ LỤC A không bị lấy
    assert TVT.tach_tltk(BAN_THAO) == {1: "[Tác giả] et al. Bài hai. Tạp chí. 2021; PMID:22222222",
                                        2: "[Tác giả] et al. Bài ba. Tạp chí. 2022; PMID:33333333"}
    assert TVT.tach_tltk("# Không có mục tài liệu\n\n1. abc\n") is None


def test_khoa_tltk_dinh_danh_va_bam_cau_khong_dinh_danh_on_dinh():
    assert TVT.khoa_tltk("x. doi:10.1000/ABC1. PMID: 11111111.") == {"pmid:11111111", "doi:10.1000/abc1"}
    a = TVT.khoa_tltk("Bộ Y tế. Quyết định số 56/QĐ-BYT. Hà Nội; 2024.")
    b = TVT.khoa_tltk("  Bộ  Y tế — Quyết định số 56/QĐ-BYT, Hà Nội 2024 ")
    assert a == b and next(iter(a)).startswith("van:")


# ── kết luận từng mục ────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("muc,ket", [
    ({"toan_van": True}, "co"),
    ({"toan_van": None}, "khong_do"),
    ({"toan_van": False, "lan_da_thu": HAI_LAN}, "khong_lay_duoc"),
    ({"toan_van": False, "lan_da_thu": HAI_LAN[:1]}, "chua_thu_het"),
    ({"toan_van": False, "lan_da_thu": [HAI_LAN[0], {**HAI_LAN[1], "ngay": "2999-01-01"}]}, "chua_thu_het"),
    ({"toan_van": False, "lan_da_thu": [HAI_LAN[0], {"lan": "trinh_duyet", "ngay": "không phải ngày"}]},
     "chua_thu_het"),
])
def test_ket_luan_muc(muc, ket):
    assert TVT.ket_luan_muc(muc) == ket


# ── đánh giá đề tài ───────────────────────────────────────────────────────────────────────────────────────────────
def test_khong_bien_nhan_thi_khong_do_duoc_va_g10_review(tmp_path):
    d = _de_tai(tmp_path)
    assert TVT.danh_gia(d, S)["trang_thai"] == "KHONG_DO_DUOC"
    st, ev = TVT.tieu_chi_g10(d, S)
    assert st == "REVIEW" and "--ghi-bien-nhan-toan-van" in ev


def test_du_toan_van_thi_dat(tmp_path):
    d = _de_tai(tmp_path, ban_thao=True)
    _bien_nhan(d)
    kq = TVT.danh_gia(d, S)
    assert kq["trang_thai"] == "DAT" and kq["dem"]["co"] == 5
    assert TVT.tieu_chi_g10(d, S)[0] == "PASS"


def test_khop_theo_khoa_khong_theo_so_thu_tu(tmp_path):
    """Đánh số lại TLTK (chèn bài mới lên đầu) không làm mất biên nhận của bài cũ — chỉ bài MỚI là «chưa đo»."""
    d = _de_tai(tmp_path)
    _bien_nhan(d)
    _ghi(d / f"DE_CUONG_NOP_HOI_DONG_{S}.md", DE_CUONG.replace(
        "1. Tác giả A.", "1. Tác giả Z. Bài mới. PMID: 44444444.\n4. Tác giả A."))
    kq = TVT.danh_gia(d, S)
    assert kq["trang_thai"] == "CON_VIEC"
    assert [x["so"] for x in kq["tltk"] if x["ket_luan"] == "khong_do"] == [1]


def test_con_lan_chua_thu_thi_con_viec(tmp_path):
    d = _de_tai(tmp_path)
    _bien_nhan(d, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN[:1]}})
    assert TVT.danh_gia(d, S)["trang_thai"] == "CON_VIEC"
    assert TVT.tieu_chi_g10(d, S)[0] == "REVIEW"


def test_khong_lay_duoc_ma_con_trich_thi_vi_pham_va_g10_block(tmp_path):
    d = _de_tai(tmp_path)
    _bien_nhan(d, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN}})
    assert TVT.danh_gia(d, S)["trang_thai"] == "VI_PHAM"
    st, ev = TVT.tieu_chi_g10(d, S)
    assert st == "BLOCK" and "TLTK 2" in ev


def test_da_o_loai_bo_ma_con_trich_thi_vi_pham(tmp_path):
    d = _de_tai(tmp_path)
    _bien_nhan(d)
    _ghi(d / DMT.TEP.format(study=S), json.dumps({"trich_dan": [], "loai_bo": [{"pmid": "11111111", "ly_do": "x"}]}))
    kq = TVT.danh_gia(d, S)
    assert kq["trang_thai"] == "VI_PHAM" and kq["dem"]["da_loai_ma_con_trich"] == 1


def test_bien_nhan_hong_hoac_sai_khuon_khong_bao_gio_dat(tmp_path):
    d = _de_tai(tmp_path)
    _ghi(d / TVT.TEP_BIEN_NHAN.format(study=S), "{hỏng")
    assert TVT.danh_gia(d, S)["trang_thai"] == "KHONG_DO_DUOC"
    _ghi(d / TVT.TEP_BIEN_NHAN.format(study=S), json.dumps({"schema": "khac", "muc": []}))
    assert TVT.tieu_chi_g10(d, S)[0] == "REVIEW"


def test_khong_co_trich_dan_nao_thi_dat_nhung_co_dinh_danh_ma_khong_tach_duoc_thi_khong_do(tmp_path):
    d = tmp_path / S
    _ghi(d / f"G7_A8_MANUSCRIPT_{S}.md", "Bản thảo chưa có trích dẫn.\n")
    assert TVT.danh_gia(d, S)["trang_thai"] == "KHONG_CO_TRICH_DAN"
    assert TVT.tieu_chi_g10(d, S)[0] == "PASS"
    _ghi(d / f"G7_A8_MANUSCRIPT_{S}.md", "Bản thảo dẫn PMID 12345678 nhưng mục tài liệu đặt tên lạ.\n")
    assert TVT.danh_gia(d, S)["trang_thai"] == "KHONG_DO_DUOC"
    assert TVT.tieu_chi_g10(d, S)[0] == "REVIEW"


# ── loại bỏ ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_loai_bo_chay_kho_khong_ghi_ap_dung_moi_ghi_va_sao_luu(tmp_path):
    d = _de_tai(tmp_path)
    _ghi(d / DMT.TEP.format(study=S), json.dumps({"schema": "de_tai/danh_muc_trich_dan/v1", "trich_dan": []}))
    _bien_nhan(d, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN}})
    van_ban_khoa = [k for k in TVT.khoa_tltk(TVT.tach_tltk(DE_CUONG)[3])][0]
    _bien_nhan(d, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN},
                   van_ban_khoa: {"toan_van": False, "lan_da_thu": HAI_LAN}})
    dx = TVT.de_xuat_loai_bo(d, S)
    assert [x["pmid"] for x in dx["loai"]] == ["22222222"]
    assert dx["loai"][0]["nhom_ly_do"] == TVT.NHOM_LY_DO and "truy cập mở" in dx["loai"][0]["ly_do"]
    assert len(dx["sua_tay"]) == 1 and "TLTK 3" in dx["sua_tay"][0]  # văn bản quy phạm: sửa tay
    assert "loai_bo" not in DMT.doc(d, S)                              # chạy khô không ghi
    kq = TVT.ap_dung_loai_bo(d, S, "nguyên văn bác sĩ")
    assert kq["da_ghi"] == 1
    dm = DMT.doc(d, S)
    assert dm["loai_bo"][0]["pmid"] == "22222222"
    assert dm["quyet_dinh_loai_bo_toan_van"]["loi_bac_si"] == "nguyên văn bác sĩ"
    assert list(d.glob("DANH_MUC_TRICH_DAN_*.bak-*-truoc-loai-toan-van.json"))
    assert TVT.ap_dung_loai_bo(d, S)["da_ghi"] == 0  # chạy lại: bài đã ở loai_bo không ghi trùng
    assert (d / DMT.TEP.format(study=S)).read_bytes().endswith(b"}\n")


def test_cli_kiem_ma_thoat(tmp_path, capsys):
    d = _de_tai(tmp_path)
    assert TVT.main(["kiem", "--study", S], exports=tmp_path) == 2
    _bien_nhan(d)
    assert TVT.main(["kiem", "--study", S], exports=tmp_path) == 0
    _bien_nhan(d, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN}})
    assert TVT.main(["kiem", "--study", S], exports=tmp_path) == 1
    assert TVT.main(["kiem", "--study", "../x"], exports=tmp_path) == 3
    assert "Cần bác sĩ kiểm chứng" in capsys.readouterr().out


# ── cổng G10, hội đồng, bộ giả lập ────────────────────────────────────────────────────────────────────────────────
def _g10(tmp_path, monkeypatch, sua=None, *, bien_nhan=True, da_ky=False):
    """Đồ gá «sẵn sàng» của test_g10_quality_gate + mục TLTK trong bản thảo G7 (tệp hợp đồng của gói)."""
    _write_ready_fixture(tmp_path, S)
    _ghi(tmp_path / f"G7_A8_MANUSCRIPT_{S}.md", BAN_THAO)
    if bien_nhan:
        _bien_nhan(tmp_path, sua)
    _patch_upstream(monkeypatch, {"g10": da_ky})
    return G10Q.evaluate_study(S, tmp_path, repo_root=tmp_path, write=True)


def test_g10_auto_12_du_toan_van_thi_pass_va_ready(tmp_path, monkeypatch):
    bao = _g10(tmp_path, monkeypatch)
    assert _criterion(bao, "G10-AUTO-12")["status"] == "PASS"
    assert bao["status"] == G10Q.STATUS_READY


def test_g10_auto_12_thieu_bien_nhan_thi_khong_ready(tmp_path, monkeypatch):
    bao = _g10(tmp_path, monkeypatch, bien_nhan=False)
    assert _criterion(bao, "G10-AUTO-12")["status"] == "REVIEW"
    assert bao["status"] != G10Q.STATUS_READY


def test_g10_auto_12_khong_lay_duoc_toan_van_thi_block(tmp_path, monkeypatch):
    bao = _g10(tmp_path, monkeypatch, {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN}})
    assert _criterion(bao, "G10-AUTO-12")["status"] == "BLOCK"
    assert bao["status"] == G10Q.STATUS_BLOCKED


def test_g10_auto_12_goi_da_khoa_chi_canh_bao(tmp_path, monkeypatch):
    sai = {"pmid:22222222": {"toan_van": False, "lan_da_thu": HAI_LAN}}
    bao = _g10(tmp_path, monkeypatch, sai, da_ky=True)
    row = _criterion(bao, "G10-AUTO-12")
    assert row["status"] == "PASS" and row["evidence"].startswith("⚠") and "không huỷ khoá" in row["evidence"]


def test_hoi_dong_gan_g10_auto_12_cho_g10_t2_va_doi_bien_nhan():
    assert HD.PHAN_CONG["G10"]["G10-AUTO-12"] == "G10-T2"
    nv = next(x for x in HD.NHIEM_VU["G10"] if x["ma"] == "G10-T2")
    assert "TOAN_VAN_TLTK_<mã>.json" in nv["dau_ra"]


def test_bo_gia_lap_ghi_bien_nhan_phu_moi_tltk(tmp_path):
    d = _de_tai(tmp_path, ban_thao=True)
    gia = types.SimpleNamespace(out=d, study=S, buoc=[])
    GTV.TronVong._bien_nhan_toan_van(gia)
    assert TVT.danh_gia(d, S)["trang_thai"] == "DAT"
    bn = json.loads((d / TVT.TEP_BIEN_NHAN.format(study=S)).read_text(encoding="utf-8"))
    assert len(bn["muc"]) == 5 and all(m["nguon"] == "gia_lap" for m in bn["muc"])
    assert gia.buoc[-1]["ma"] == 0


def test_bo_gia_lap_goi_bien_nhan_sau_de_cuong_nop_truoc_lap_lai_g10():
    """Dòng THI HÀNH (AST): trong `TronVong.g10`, `_bien_nhan_toan_van()` đứng sau `_de_cuong_nop()` và trước lượt lắp
    lại G10 (biên nhận phải phủ TLTK của đề cương nộp vừa sinh)."""
    import ast  # noqa: PLC0415
    import inspect  # noqa: PLC0415
    import textwrap  # noqa: PLC0415

    cay = ast.parse(textwrap.dedent(inspect.getsource(GTV.TronVong.g10)))
    goi = {ast.unparse(n.func): n.lineno for n in ast.walk(cay) if isinstance(n, ast.Call)
           and ast.unparse(n.func) in ("self._de_cuong_nop", "self._bien_nhan_toan_van")}
    lap_lai = [n.lineno for n in ast.walk(cay)
               if isinstance(n, ast.Constant) and n.value == "G10 lắp lại gói sau khi PI khai"]
    assert goi.get("self._de_cuong_nop") < goi.get("self._bien_nhan_toan_van") < lap_lai[0]
