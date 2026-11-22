# -*- coding: utf-8 -*-
"""Sổ phân công công cụ + chiều đo C1–C6 của tiêu chuẩn hoàn thiện (22/11/2026).

Bác sĩ (22/11/2026): «Tất cả vấn đề đều có nền sẵn nhưng chưa xây dựng nguyên tắc và phân công đúng; hãy kiểm tra lại
và hoàn thiện nâng cấp.» Mỗi công cụ của hệ nghiên cứu phải có ĐÚNG MỘT agent chủ gắn cổng, chốt kiểm đo đầu ra, nguyên
tắc kèm lý do; agent chủ và người kiểm phải biết công cụ. Đo trước khi sửa (agent chưa sửa, sổ vừa lập): 39 công cụ
không agent nào nhắc, 78 chủ chưa nhắc công cụ/chốt kiểm, 38 người kiểm chưa nhắc, 14 cặp tiêu chí–agent chưa có bộ
chấm. Sau sửa: 0 mọi mục — test giữ mức đó và chứng minh mỗi hạng mục bắt được vi phạm. Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tieu_chuan_hoan_thien as TC  # noqa: E402

SO = json.loads((ROOT / "config" / "phan_cong_cong_cu.json").read_text(encoding="utf-8"))


def _van(thu_muc: Path = ROOT / ".claude" / "agents"):
    return {p.stem: p.read_text(encoding="utf-8") for p in thu_muc.glob("*.md")
            if not p.stem.startswith("_") and p.stem != "README"}


def _do(so=None, van=None, plugin=None):
    return TC.do_cong_cu(_van() if van is None else van, copy.deepcopy(SO) if so is None else so, ROOT, plugin)


# ── Chốt KHÔNG LÙI trên hệ thật ─────────────────────────────────────────────────────────────────────────────────────
def test_he_that_c1_c6_dat_va_so_do_bang_0():
    kq = _do()
    assert kq["dat"], {m: v for m, v in kq["hang_muc"].items() if v != "✅"}
    assert all(v == 0 for v in kq["so_do"].values()), kq["so_do"]
    assert kq["nghien_cuu"] >= 150 and kq["ngoai_pham_vi"] >= 30


def test_do_tong_va_ma_thoat_gom_chieu_cong_cu(capsys):
    kq = TC.do()
    assert kq["tong"]["cong_cu_dat"] == kq["tong"]["cong_cu"] == 6
    assert TC.dat_tron(kq)
    assert TC.main([]) == 0
    assert "công cụ 6/6 ĐẠT" in capsys.readouterr().out


def test_moi_tep_cong_cu_dung_mot_muc_va_khoa_hop_le():
    tep = TC.tep_cong_cu(ROOT)
    assert sorted(SO["cong_cu"]) == tep
    for t, v in SO["cong_cu"].items():
        assert v["pham_vi"] in TC.PHAM_VI, t
        if v["pham_vi"] == "nghien_cuu":
            assert isinstance(v["chu"], str) and v["chot_kiem"] and v["nguyen_tac"], t


def test_khoa_nguyen_tac_khop_bang_cua_so_va_tam_nguyen_tac():
    assert {n: tuple(SO["nguyen_tac"][n]) for n in TC.KHOA_NGUYEN_TAC} == {
        n: tuple(k) for n, k in TC.KHOA_NGUYEN_TAC.items()}
    tn = TC._khoa_tam_nguyen_tac()
    if tn is None:
        pytest.skip("tam_nguyen_tac_de_cuong chưa gộp vào nhánh này")
    assert set(tn["nt"]) == set(TC.KHOA_NGUYEN_TAC["nt"])
    assert set(tn["dct"]) == set(TC.KHOA_NGUYEN_TAC["dct"])


def test_chu_khop_so_chu_plugin_runtime():
    """Ba runtime nghiên cứu của sổ plugin (repo gốc) có cùng chủ trong sổ công cụ — không lập nguồn thứ hai."""
    pl = {"run_pipeline.py": "dieu-phoi-nghien-cuu", "run_stats_analysis.py": "phan-tich-thong-ke",
          "run_g3_auto.py": "co-mau-nghien-cuu"}
    assert _do(plugin=pl)["hang_muc"]["C2"] == "✅"


# ── Mỗi hạng mục bắt được vi phạm ───────────────────────────────────────────────────────────────────────────────────
def test_c1_cong_cu_chua_vao_so_va_muc_thua():
    so = copy.deepcopy(SO)
    so["cong_cu"].pop("hinh_g6.py")
    so["cong_cu"]["khong_co_that.py"] = {"pham_vi": "ngoai_pham_vi", "ly_do": "mục thử nghiệm không có tệp"}
    kq = _do(so)
    assert "hinh_g6.py chưa vào sổ" in kq["hang_muc"]["C1"]
    assert "khong_co_that.py có trong sổ nhưng không có tệp" in kq["hang_muc"]["C1"]
    assert kq["so_do"]["chua_vao_so"] == 1 and kq["so_do"]["muc_thua"] == 1 and not kq["dat"]


def test_c1_pham_vi_la():
    so = copy.deepcopy(SO)
    so["cong_cu"]["normal_dist.py"]["pham_vi"] = "tam_gac"
    assert "normal_dist.py phạm vi không hợp lệ" in _do(so)["hang_muc"]["C1"]


def test_c2_hai_chu_trong_so():
    so = copy.deepcopy(SO)
    so["cong_cu"]["hinh_g6.py"]["chu"] = ["phan-tich-thong-ke", "viet-ban-thao"]
    kq = _do(so)
    assert "hinh_g6.py: chủ phải là MỘT agent có thật" in kq["hang_muc"]["C2"]
    assert kq["so_do"]["hai_chu"] == 1


def test_c2_agent_khac_tu_khai_chu(tmp_path):
    van = _van()
    van["viet-ban-thao"] += "\n- Công cụ `tools/hinh_g6.py` (chủ) — vẽ hình kết quả.\n"
    kq = _do(van=van)
    assert "hinh_g6.py: viet-ban-thao tự khai «(chủ)»" in kq["hang_muc"]["C2"]
    assert kq["so_do"]["hai_chu"] == 1


def test_c2_lech_so_chu_plugin():
    kq = _do(plugin={"run_stats_analysis.py": "thiet-ke-nghien-cuu"})
    assert "sổ chủ plugin ghi thiet-ke-nghien-cuu" in kq["hang_muc"]["C2"]
    assert kq["so_do"]["hai_chu"] == 1


def test_c2_chu_khong_gan_cong_va_khong_lam_nhiem_vu():
    so = copy.deepcopy(SO)
    v = so["cong_cu"]["run_g3_auto.py"]
    v["chu"], v["nguoi_dung_phu"], v["nguoi_kiem"] = "nop-bai-phan-hoi", [], []
    hm = _do(so)["hang_muc"]["C2"]
    assert "chủ nop-bai-phan-hoi không gắn cổng G3" in hm
    assert "không làm nhiệm vụ đã khai" in hm


def test_c2_chu_dong_thoi_la_nguoi_kiem_va_nhiem_vu_la():
    so = copy.deepcopy(SO)
    so["cong_cu"]["hinh_g6.py"]["nguoi_kiem"].append("phan-tich-thong-ke")
    so["cong_cu"]["hinh_g6.py"]["nhiem_vu"] = ["G6-T99"]
    hm = _do(so)["hang_muc"]["C2"]
    assert "đồng thời là người kiểm" in hm and "G6-T99 không có trong danh mục" in hm


def test_c3_chu_chua_nhac_cong_cu(tmp_path):
    van = _van()
    van["phan-tich-thong-ke"] = van["phan-tich-thong-ke"].replace("hinh_g6", "hinh_khac")
    kq = _do(van=van)
    assert "hinh_g6.py: phan-tich-thong-ke chưa nhắc công cụ" in kq["hang_muc"]["C3"]
    assert kq["so_do"]["chu_khong_nhac"] >= 1


def test_c3_chu_chua_nhac_chot_kiem():
    so = copy.deepcopy(SO)
    so["cong_cu"]["hinh_g6.py"]["chot_kiem"] = ["tests/test_hinh_g6_20261121.py"]
    van = _van()
    van["phan-tich-thong-ke"] = van["phan-tich-thong-ke"].replace("test_hinh_g6_20261121", "x")
    assert "hinh_g6.py: phan-tich-thong-ke chưa nhắc chốt kiểm" in _do(so, van)["hang_muc"]["C3"]


def test_c3_chot_kiem_khong_hop_le():
    so = copy.deepcopy(SO)
    so["cong_cu"]["hinh_g6.py"]["chot_kiem"] = ["tools/khong_ton_tai.py", "G6-AUTO-99", "tools/hinh_g6.py"]
    hm = _do(so)["hang_muc"]["C3"]
    assert "chốt kiểm không hợp lệ" in hm and "khong_ton_tai" in hm and "G6-AUTO-99" in hm
    so["cong_cu"]["hinh_g6.py"]["chot_kiem"] = []
    assert "hinh_g6.py: chưa khai chốt kiểm" in _do(so)["hang_muc"]["C3"]


def test_c4_nguoi_kiem_chua_nhac_va_tu_khai_lech():
    van = _van()
    van["binh-duyet"] = van["binh-duyet"].replace("tieu_chi_ban_thao", "tieu_chi_x")
    van["kinh-te-y-te"] += "\n- Công cụ `tools/hinh_g6.py` (kiểm) — kiểm hình.\n"
    kq = _do(van=van)
    assert "tieu_chi_ban_thao.py: người kiểm binh-duyet chưa nhắc" in kq["hang_muc"]["C4"]
    assert "hinh_g6.py: kinh-te-y-te tự khai «(kiểm)»" in kq["hang_muc"]["C4"]
    assert kq["so_do"]["kiem_khong_nhac"] >= 1


def test_c5_agent_nhiem_vu_khong_biet_bo_cham():
    van = _van()
    van["thu-thu-tai-lieu"] = van["thu-thu-tai-lieu"].replace("g0_quality_gate", "g0_x")
    so = copy.deepcopy(SO)
    so["cong_cu"]["g3_quality_gate.py"]["nguoi_dung_phu"].remove("bien-so-nghien-cuu")
    kq = _do(so, van)
    hm = kq["hang_muc"]["C5"]
    assert "G0 G0-T2 thu-thu-tai-lieu: g0_quality_gate.py — tệp agent chưa nhắc" in kq["loi"]["C5"]
    assert any(x.startswith("G3 G3-T2 bien-so-nghien-cuu") and "không có tên trong mục sổ" in x
               for x in kq["loi"]["C5"]), hm
    assert kq["so_do"]["tieu_chi_khong_cong_cu"] == 2


def test_c6_nguyen_tac_thieu_ly_do_khoa_la_va_ngoai_pham_vi_khong_ly_do():
    so = copy.deepcopy(SO)
    so["cong_cu"]["hinh_g6.py"]["nguyen_tac"] = {"nt:tai_lap": "", "nt:dep": "lý do đủ dài cho khoá lạ"}
    so["cong_cu"]["normal_dist.py"]["nguyen_tac"] = {}
    so["cong_cu"]["goc_ebm.py"]["ly_do"] = "hạ tầng"
    so["cong_cu"]["ve_bieu_do.py"]["nguyen_tac"]["nt:tai_lap"] = "[CẦN BỔ SUNG lý do]"
    kq = _do(so)
    hm = kq["hang_muc"]["C6"]
    assert kq["so_do"]["nguyen_tac_khong_ly_do"] == 4, kq["loi"]["C6"]
    assert "khoá nguyên tắc lạ nt:dep" in " ".join(kq["loi"]["C6"]), hm


def test_c6_bang_nguyen_tac_lech_tap_khoa():
    so = copy.deepcopy(SO)
    so["nguyen_tac"]["nt"].pop("ton_trong")
    assert "bảng nguyên tắc «nt» lệch" in _do(so)["hang_muc"]["C6"]


def test_so_hong_thi_do_va_ma_thoat_1(monkeypatch, tmp_path, capsys):
    p = tmp_path / "so.json"
    p.write_text("{hỏng", encoding="utf-8", newline="\n")
    monkeypatch.setattr(TC, "SO_CONG_CU", p)
    monkeypatch.setattr(TC, "doc_so", lambda q=p: json.loads(Path(q).read_text(encoding="utf-8")))
    kq = TC.do()
    assert kq["cong_cu"]["dat"] is False and kq["tong"]["cong_cu_dat"] < 6
    assert not TC.dat_tron(kq)
    assert TC.main([]) == 1
    assert "không đọc được sổ công cụ" in capsys.readouterr().out


def test_do_voi_ban_sao_agent_va_so_sai_thi_tong_khong_dat(tmp_path):
    agents = tmp_path / ".claude" / "agents"
    shutil.copytree(ROOT / ".claude" / "agents", agents)
    so = copy.deepcopy(SO)
    so["cong_cu"].pop("hinh_g6.py")
    kq = TC.do(agents, so_cong_cu=so, plugin=None)
    assert kq["tong"]["agent_dat"] == kq["tong"]["agent"] and not TC.dat_tron(kq)
    assert "chưa vào sổ" in kq["cong_cu"]["hang_muc"]["C1"]


def test_nhac_khop_dung_ten_khong_khop_tien_to():
    assert TC.nhac("chạy `tools/hinh_g6.py` nhé", "hinh_g6.py")
    assert not TC.nhac("chạy hinh_g6x", "hinh_g6.py")
    assert TC.nhac("đo K18 trên bản thảo", "K18") and not TC.nhac("K180", "K18")
    assert TC.nhac("xem test_ve_bieu_do_20261121", "tests/test_ve_bieu_do_20261121.py")


def test_gan_cong_dung_danh_muc():
    assert "G6" in TC.gan_cong("phan-tich-thong-ke") and "G3" in TC.gan_cong("phan-tich-thong-ke")
    assert TC.gan_cong("dieu-phoi-g4") == {"G4"}
    assert TC.gan_cong("dieu-phoi-nghien-cuu") == set(TC.HD.CONG)
