"""Bản thảo G7: số sàng lọc từ sổ sơ đồ luồng + Bảng 1 RCT đúng chuẩn (22/11/2026).

Đo trên bản thảo G7 của 24 kịch bản giả lập (gia-lap-16) sau #403:
  (4) chương Kết quả không dùng `SO_DO_LUONG_<mã>.csv` dù sổ đã đủ số và khớp số học ⇒ STROBE 13a/13b và CONSORT
      2025 22a/22b chỉ có «chưa có thông tin»;
  (5) Bảng 1 RCT còn hàng biến định danh (`record_id`, `ngay_ngau_nhien`), cột nhóm ghi «0»/«1» không nhãn
      can thiệp/chứng, chú thích cột p ghi «CONSORT 2010».
Dữ liệu synthetic, không PII; cổng G2/G4/G5 giả lập để chỉ đo phần phân tích.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_stats_analysis as RSA  # noqa: E402


def _gia_lap_cong(monkeypatch, thiet_ke: str = "rct"):
    locked = {"g2_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda study: (True, "giả lập: G4 khoá sống"))
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: (thiet_ke, None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def _du_lieu_rct(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    nhom = np.array([0, 1] * (n // 2))
    return pd.DataFrame({
        "record_id": [f"R{i:04d}" for i in range(n)],
        "ngay_ngau_nhien": [f"2027-0{1 + i % 9}-1{i % 9}" for i in range(n)],
        "tuoi": rng.integers(40, 80, n), "gioi": rng.integers(0, 2, n), "nhom": nhom,
        "tam_thu_6t": 140 - 5 * nhom + rng.normal(0, 10, n)})


def test_engine_bang1_rct_bo_dinh_danh_ngay_va_chu_thich_consort_2025(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu_rct().to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "tam_thu_6t", "--group", "nhom",
        "--outcome-type", "continuous", "--study", "SYN", "--gate", "G6"])
    RSA.main()
    tom = json.loads((tmp_path / "exports" / "SYN" / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    t1 = tom["table1"]
    bien = [r["variable"] for r in t1["rows"]]
    assert bien == ["tuoi", "gioi"]  # không record_id, không ngay_ngau_nhien, không biến nhóm/kết cục
    assert {r["test"] for r in t1["rows"]} == {RSA.KHONG_KIEM_DINH_NEN_RCT}
    assert "CONSORT 2025" in RSA.KHONG_KIEM_DINH_NEN_RCT and "2010" not in RSA.KHONG_KIEM_DINH_NEN_RCT
    assert all(r["p"] is None for r in t1["rows"])


# ═════════════════════════════════════════════════════════════════════════════ G7 — dùng chung fixture N16
TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
import csv  # noqa: E402

import run_g7_auto as G7A  # noqa: E402
from test_g7_bang1_ket_cuc_phu_tu_g6_20261115 import BANG1_G6  # noqa: E402
from test_g7_tu_dien_ket_qua_g6_20261115 import _ghi_tom_tat, _manifest, _sinh, _tom_tat_nhi_phan  # noqa: E402

# Sổ RCT theo mẫu CONSORT (gồm hộp «nhận can thiệp theo phân bổ» — CONSORT 2025 22a), số khớp cộng trừ từng bước
SO_RCT = [
    ("Đánh giá đủ tiêu chuẩn", "300", "chinh", "", ""),
    ("Loại trừ", "40", "loai", "", "Không đủ tiêu chuẩn: 25; Từ chối tham gia: 12; Lý do khác: 3"),
    ("Phân bổ ngẫu nhiên", "260", "chinh", "", ""),
    ("Được phân bổ nhóm can thiệp", "130", "chinh", "Can thiệp", ""),
    ("Không nhận can thiệp theo phân bổ", "4", "loai", "Can thiệp", "Từ chối can thiệp: 3; Lý do khác: 1"),
    ("Nhận can thiệp theo phân bổ", "126", "chinh", "Can thiệp", ""),
    ("Mất theo dõi / ngừng can thiệp", "6", "loai", "Can thiệp", "Mất liên lạc: 4; Rút đồng ý: 2; Lý do khác: 0"),
    ("Đưa vào phân tích", "120", "chinh", "Can thiệp", ""),
    ("Được phân bổ nhóm chứng", "130", "chinh", "Chứng", ""),
    ("Không nhận can thiệp theo phân bổ", "0", "loai", "Chứng", "Từ chối can thiệp: 0; Lý do khác: 0"),
    ("Nhận can thiệp theo phân bổ", "130", "chinh", "Chứng", ""),
    ("Mất theo dõi / ngừng can thiệp", "12", "loai", "Chứng", "Mất liên lạc: 9; Rút đồng ý: 3"),
    ("Đưa vào phân tích", "118", "chinh", "Chứng", ""),
]
SO_CAT_NGANG = [
    ("Đối tượng tiềm năng được tiếp cận", "430", "chinh", "", ""),
    ("Không tham gia", "30", "loai", "", "Không đủ tiêu chuẩn: 18; Từ chối tham gia: 9; Lý do khác: 3"),
    ("Tham gia nghiên cứu", "400", "chinh", "", ""),
    ("Loại khỏi phân tích", "9", "loai", "", "Thiếu dữ liệu kết cục chính: 9; Lý do khác: 0"),
    ("Đưa vào phân tích", "391", "chinh", "", ""),
]


def _ghi_so(out: Path, dong, study: str = "THU") -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"SO_DO_LUONG_{study}.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["buoc", "n", "loai", "nhanh", "ly_do"])
        w.writerows(dong)
    return p


def test_g7_doc_so_chi_dung_khi_du_so_va_khop_so_hoc(tmp_path):
    assert G7A.doc_so_do_luong_g7(tmp_path, "THU") is None                    # vắng sổ
    _ghi_so(tmp_path, SO_RCT)
    k = G7A.doc_so_do_luong_g7(tmp_path, "THU")
    assert k and set(k["nhanh"]) == {"", "Can thiệp", "Chứng"}
    _ghi_so(tmp_path, [r if r[0] != "Phân bổ ngẫu nhiên" else (r[0], "", *r[2:]) for r in SO_RCT])
    assert G7A.doc_so_do_luong_g7(tmp_path, "THU") is None                    # còn ô trống
    _ghi_so(tmp_path, [r if r[0] != "Phân bổ ngẫu nhiên" else (r[0], "261", *r[2:]) for r in SO_RCT])
    assert G7A.doc_so_do_luong_g7(tmp_path, "THU") is None                    # lệch số học (300 − 40 ≠ 261)
    _ghi_so(tmp_path, [(r[0], r[1], r[2], r[3], "Mất liên lạc: 5") if r[0].startswith("Mất") and r[3] == "Chứng"
                       else r for r in SO_RCT])
    assert G7A.doc_so_do_luong_g7(tmp_path, "THU") is None                    # chi tiết lý do cộng ≠ n hộp


def test_g7_khoi_tuyen_chon_rct_theo_nhom_co_ten_va_ly_do_co_so(tmp_path):
    _ghi_so(tmp_path, SO_RCT)
    khoi = "\n".join(G7A.khoi_tuyen_chon_g7(G7A.doc_so_do_luong_g7(tmp_path, "THU"), "rct"))
    assert "260 người được phân bổ ngẫu nhiên: 130 người vào nhóm can thiệp và 130 người vào nhóm chứng." in khoi
    assert ("*Nhóm can thiệp:* Được phân bổ nhóm can thiệp: 130 người. Không nhận can thiệp theo phân bổ: 4 người, "
            "vì từ chối can thiệp (3) và lý do khác (1). Nhận can thiệp theo phân bổ: 126 người. Mất theo dõi / ngừng "
            "can thiệp: 6 người, vì mất liên lạc (4) và rút đồng ý (2). Đưa vào phân tích: 120 người.") in khoi
    assert "Không nhận can thiệp theo phân bổ: không có người nào." in khoi   # hộp 0 vẫn được nêu
    assert "238 người được đưa vào phân tích (120 người ở nhóm can thiệp, 118 người ở nhóm chứng)." in khoi
    assert "Loại trừ: 40 người, vì không đủ tiêu chuẩn (25), từ chối tham gia (12) và lý do khác (3)." in khoi
    assert "lý do khác (0)" not in khoi and "nhóm 0" not in khoi and "nhóm 1" not in khoi
    so_so = {x for r in SO_RCT for x in [r[1]] + [p.split(":")[1].strip() for p in r[4].split(";") if ":" in p]}
    import re as _re
    assert set(_re.findall(r"\d+", khoi)) - so_so == {"238"}   # mọi số khác chép đúng từ sổ; 238 = 120 + 118


def test_g7_khoi_tuyen_chon_quan_sat_va_tong_quan(tmp_path):
    _ghi_so(tmp_path, SO_CAT_NGANG)
    khoi = "\n".join(G7A.khoi_tuyen_chon_g7(G7A.doc_so_do_luong_g7(tmp_path, "THU"), "cross_sectional"))
    assert ("Không tham gia: 30 người, vì không đủ tiêu chuẩn (18), từ chối tham gia (9) và lý do khác (3)."
            in khoi)
    assert "Loại khỏi phân tích: 9 người, vì thiếu dữ liệu kết cục chính (9)." in khoi
    assert khoi.rstrip().endswith("391 người được đưa vào phân tích.")
    assert "phân bổ ngẫu nhiên" not in khoi
    assert G7A.khoi_tuyen_chon_g7(None, "rct") == []
    tq = [("Bản ghi được sàng lọc", "120", "chinh", "", ""), ("Báo cáo bị loại", "105", "loai", "",
                                                              "Sai quần thể: 60; Sai thiết kế: 45"),
          ("Nghiên cứu đưa vào tổng quan", "15", "chinh", "", "")]
    _ghi_so(tmp_path, tq)
    khoi = "\n".join(G7A.khoi_tuyen_chon_g7(G7A.doc_so_do_luong_g7(tmp_path, "THU"), "sr_ma"))
    assert "Báo cáo bị loại: 105, vì sai quần thể (60) và sai thiết kế (45)." in khoi and "người" not in khoi
    assert "15 nghiên cứu được đưa vào tổng quan." in khoi


def test_g7_ban_thao_chen_khoi_tuyen_chon_hoac_giu_o_cho(tmp_path):
    _ghi_so(tmp_path, SO_RCT)
    khoi = G7A.khoi_tuyen_chon_g7(G7A.doc_so_do_luong_g7(tmp_path, "THU"), "rct")
    for kq6 in (None, {"da_dung": True, "nguon": "G6_analysis_summary.json", "n_total_txt": "238",
                       "n_theo_nhom": None, "bien_bang1": [], "s1": ["Phân tích (G6): N = 238  "], "s2": [],
                       "s3": [], "s5": []}):
        co = _sinh(khoi_tuyen_chon=khoi, ket_qua_g6=kq6)
        assert "260 người được phân bổ ngẫu nhiên" in co and "Sàng lọc: N = ___" not in co
        assert "*Lý do loại trừ chính:* [CẦN" not in co
        khong = _sinh(ket_qua_g6=kq6)
        assert "Sàng lọc: N = ___" in khong and "*Lý do loại trừ chính:* [CẦN" in khong
        assert "phân bổ ngẫu nhiên:" not in khong


def _tu_dien_nhom(nhan_1: str = "Can thiệp (tin nhắn nhắc thuốc)") -> list:
    return [{"variable": "nhom", "label": "Nhóm nghiên cứu", "choices": f"0, Chứng | 1, {nhan_1}"},
            {"variable": "tuoi", "label": "Tuổi (năm)", "choices": ""}]


@pytest.mark.parametrize("nhan_1", ["Can thiệp (tin nhắn nhắc thuốc)", "Can thiệp 2 lần/ngày, 12 tuần"])
def test_g7_bang1_cot_nhom_mang_ten_tu_dien_g5(tmp_path, nhan_1):
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(table1=BANG1_G6, dac_ta_phan_tich={"group": "nhom", "outcome": "kiem_soat"}))
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out), tu_dien=_tu_dien_nhom(nhan_1))
    assert kq["da_dung"], kq.get("ly_do")      # nhãn có chữ số («2 lần/ngày, 12 tuần») không làm hỏng bước tự kiểm
    s2 = "\n".join(kq["s2"])
    assert f"| Biến | Nhóm chứng (N=109) | Nhóm {nhan_1[0].lower() + nhan_1[1:]} (N=109) | p / kiểm định |" in s2
    assert "Nhóm `0`" not in s2 and "Nhóm `1`" not in s2
    assert "nhóm chứng: 109; nhóm can thiệp" in s2
    assert kq["nhan_nhom"] == {"0": "Chứng", "1": nhan_1}
    cg = G7A.chu_giai_bang1_g6(_tu_dien_nhom(nhan_1), kq["bien_bang1"], kq["nhan_nhom"])
    assert "`0` = Chứng" in cg and f"`1` = {nhan_1}" in cg
    # không có biến nhóm trong tóm tắt hoặc từ điển không có nhãn ⇒ giữ mã như cũ
    for tt_them, td in (({}, _tu_dien_nhom()), ({"dac_ta_phan_tich": {"group": "nhom"}}, [{"variable": "nhom"}])):
        _ghi_tom_tat(out, _tom_tat_nhi_phan(table1=BANG1_G6, **tt_them))
        kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out), tu_dien=td)
        assert "Nhóm `0` (N=109)" in "\n".join(kq["s2"]) and not kq["nhan_nhom"]


def test_g7_doc_tu_dien_doc_cot_lua_chon(tmp_path):
    p = tmp_path / "G5_REDCap_dictionary_THU.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Variable / Field Name", "Form Name", "Field Type", "Field Label",
                    "Choices, Calculations, OR Slider Labels"])
        w.writerow(["nhom", "phan_bo", "radio", "Nhóm nghiên cứu", "0, Chứng | 1, Can thiệp"])
    bien, _ = G7A.doc_tu_dien_redcap(p)
    assert bien[0]["choices"] == "0, Chứng | 1, Can thiệp"
    assert G7A._nhan_lua_chon(bien[0]["choices"]) == {"0": "Chứng", "1": "Can thiệp"}
    assert G7A._ma_nhom("1.0") == "1" and G7A._ma_nhom("Can thiệp") == "Can thiệp"


def test_mau_so_rct_co_hop_nhan_can_thiep_va_ve_duoc(tmp_path):
    import ve_bieu_do as VB

    rct = VB.mau_so_do_luong("rct")
    for nh in ("Can thiệp", "Chứng"):
        buoc = [r["buoc"] for r in rct if r["nhanh"] == nh]
        assert buoc == [f"Được phân bổ nhóm {nh.lower()}", "Không nhận can thiệp theo phân bổ",
                        "Nhận can thiệp theo phân bổ", "Mất theo dõi / ngừng can thiệp", "Đưa vào phân tích"]
    assert [(r["buoc"], r["loai"], r["nhanh"]) for r in rct] == [(b, lo, nh) for b, _n, lo, nh, _l in SO_RCT]
    pytest.importorskip("matplotlib")
    import bieu_do_bao_cao as BB

    dong = [dict(zip(("buoc", "n", "loai", "nhanh", "ly_do"), r)) for r in SO_RCT]
    BB.ve_so_do_luong(dong, tmp_path / "luong", "CONSORT 2025")
    assert (tmp_path / "luong.png").is_file()
