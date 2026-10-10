# -*- coding: utf-8 -*-
"""Bảng độ nhạy p × d của thiết kế MÔ TẢ phải đi CÙNG đường tính với N chính, kể cả khi có cụm (09/10/2026).

Lỗi tìm thấy khi chạy G3 trên đề tài C1a (cắt ngang, ICC 0,02, m = 20): N chính 532 (385 × DE 1,38) nhưng ô cơ sở của
bảng độ nhạy in 385 — nhánh p × d của generate_artifact() gọi ap_fpc_cum() mà KHÔNG truyền icc/cluster_size, nên chỉ
nhân FPC, không nhân hiệu ứng thiết kế. G3-AUTO-09 bắt được (REVIEW «ô cơ sở=385 không khớp n_total=532»), nhưng bộ
test G3-06 từng có ca cắt ngang + FPC và ca RCT + cụm, KHÔNG có ca cắt ngang + cụm — đúng chỗ lỗi lọt.

run_g3_auto.main() chạy THẬT trong thư mục tạm (BASE trỏ sang tmp — không ghi exports/ của repo). Dữ liệu tổng hợp,
không mạng. Các giá trị vàng tính ĐỘC LẬP bằng statistics.NormalDist (không dùng mã của repo).
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g3_quality_gate as G3Q  # noqa: E402
import run_g3_auto as R  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402

# Tham số của C1a (07/10/2026): p = 0,5 · d = 5% · ICC 0,02 · m = 20 · bỏ cuộc 15%  ⇒  385 → DE 1,38 → 532 → 626.
ARGV_CUM = ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--cluster-size", "20",
            "--dropout", "0.15"]
ARGV_KHONG_CUM = ["--prevalence", "0.5", "--precision", "0.05", "--dropout", "0.15"]

# Hàng = p ước lượng; cột = d = ±2,5% / ±5% / ±10%. TRƯỚC DE = ⌈z²p(1−p)/d²⌉; SAU DE = ⌈TRƯỚC × 1,38⌉.
BANG_TRUOC_DE = {"0.10": [554, 139, 35], "0.30": [1291, 323, 81], "0.50": [1537, 385, 97]}
BANG_SAU_DE = {"0.10": [765, 192, 49], "0.30": [1782, 446, 112], "0.50": [2122, 532, 134]}


def _chay(tmp_path, monkeypatch, study, thiet_ke, argv, *, meta_g3=None):
    """Dựng G0→G1 chốt thật rồi chạy run_g3_auto.main() thật; trả (thư mục, checkpoint, mã thoát, stdout)."""
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke=thiet_ke, mau_hieu_qua=[], chot_g1=True,
                       them_meta={"G3": meta_g3} if meta_g3 else None)
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = R.main()
    cp = json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8"))
    return d, cp, rc, buf.getvalue()


def _a4(d, study):
    return (d / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")


def _tieu_de_bang(a4):
    """Dòng mô tả bảng p × d (ngay dưới tiêu đề PHẦN 3)."""
    return next(dong for dong in a4.splitlines() if dong.startswith("Bảng: tỷ lệ ước lượng p"))


def _row(cp, tid):
    r = cp["quality_gate"]
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


def test_cat_ngang_co_cum_bang_do_nhay_nhan_he_so_thiet_ke(tmp_path, monkeypatch):
    """Ca C1a: ô cơ sở (p 0,50 × d ±5%) phải là N CHÍNH 532 — không phải 385 trước DE — và G3-AUTO-09 PASS."""
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-CN-CUM", "cross_sectional", ARGV_CUM)
    assert (cp["n_total_truoc_de"], cp["n_total"], cp["n_adjusted"], cp["n_clusters"]) == (385, 532, 626, 27)
    assert abs(cp["design_effect"] - 1.38) < 1e-9

    bang = G3Q.parse_sensitivity_table(_a4(d, "S-CN-CUM"))
    assert bang["kind"] == "prevalence" and bang["cells_na"] == 0
    assert bang["rows"] == BANG_SAU_DE, "mọi ô phải SAU hiệu ứng thiết kế, không riêng ô cơ sở"
    assert G3Q.sensitivity_base_cell(bang, cp["power"]) == cp["n_total"] == 532

    a9 = _row(cp, "G3-AUTO-09")
    assert a9["status"] == "PASS", a9


def test_tieu_de_bang_noi_ro_da_nhan_he_so_thiet_ke(tmp_path, monkeypatch):
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-CN-TD", "cross_sectional", ARGV_CUM)
    a4 = _a4(d, "S-CN-TD")
    tieu_de = _tieu_de_bang(a4)
    assert "hiệu ứng thiết kế" in tieu_de and "DE = 1.38" in tieu_de
    assert "m = 20" in tieu_de and "ICC = 0.02" in tieu_de
    # Chữ mới KHÔNG được bị bộ phân tích của cổng đọc nhầm thành «điều chỉnh N% dropout» (ô là N TRƯỚC bù).
    assert G3Q.parse_sensitivity_table(a4)["header_dropout_pct"] is None
    assert "TRƯỚC khi bù 15% không trả lời" in tieu_de


def test_khong_cum_bang_giu_nguyen_va_tieu_de_khong_khai_de(tmp_path, monkeypatch):
    """Đối chứng: không khai cụm thì bảng KHÔNG đổi (N trước DE = N chính) và tiêu đề không nhắc hiệu ứng thiết kế."""
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-CN-KC", "cross_sectional", ARGV_KHONG_CUM)
    assert cp["n_total"] == 385 and cp["design_effect"] is None
    bang = G3Q.parse_sensitivity_table(_a4(d, "S-CN-KC"))
    assert bang["rows"] == BANG_TRUOC_DE
    assert "hiệu ứng thiết kế" not in _tieu_de_bang(_a4(d, "S-CN-KC"))
    assert _row(cp, "G3-AUTO-09")["status"] == "PASS"


def test_chi_co_icc_thieu_co_chum_thi_khong_nhan_de_va_khong_khai_de(tmp_path, monkeypatch):
    """ap_fpc_cum chỉ nhân DE khi có CẢ icc lẫn cluster_size; tiêu đề phải theo đúng điều kiện đó, không khai khống."""
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-CN-ICC", "cross_sectional",
                             ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--dropout", "0.15"])
    assert cp["n_total"] == 385 and cp["design_effect"] is None
    a4 = _a4(d, "S-CN-ICC")
    assert G3Q.parse_sensitivity_table(a4)["rows"] == BANG_TRUOC_DE
    assert "hiệu ứng thiết kế" not in _tieu_de_bang(a4)


def test_cat_ngang_fpc_va_cum_o_co_so_khop_n_chinh(tmp_path, monkeypatch):
    """FPC (N quần thể 5000) rồi DE — đúng thứ tự doctrine: 385 → 357,47 → ×1,38 = 493,3 → 494. Tiêu đề nêu cả hai."""
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-CN-FPC-CUM", "cross_sectional",
                             [*ARGV_CUM, "--population-n", "5000"])
    assert cp["n_total"] == 494
    a4 = _a4(d, "S-CN-FPC-CUM")
    bang = G3Q.parse_sensitivity_table(a4)
    assert G3Q.sensitivity_base_cell(bang, cp["power"]) == 494
    tieu_de = _tieu_de_bang(a4)
    assert "quần thể hữu hạn N=5000" in tieu_de and "hiệu ứng thiết kế" in tieu_de


def test_ca_c1a_dau_cuoi_khai_50_chum_co_dinh_khong_con_bi_bao_lech(tmp_path, monkeypatch):
    """Đầu–cuối trên cấu hình C1a (50 bàn khám cố định, m = 20, N kế hoạch 1000): bảng độ nhạy neo vào N chính 532 và
    G3-AUTO-12 chấp nhận số chùm khai 50. Khóa đường nối thật: bộ sinh phải ghi confirmed_n vào checkpoint thì bộ chấm
    mới đối chiếu được; checkpoint["n_clusters"] vẫn là số chùm TỐI THIỂU (27) để SAP/G4 không bị đổi nghĩa."""
    meta = {"icc_source": "Adams 2004, PMID 15485730 (ICC chăm sóc ban đầu)", "n_clusters": 50,
            "equal_cluster_sizes": True}
    d, cp, _rc, _out = _chay(tmp_path, monkeypatch, "S-C1A-DIEM", "cross_sectional",
                             [*ARGV_CUM, "--confirmed-n", "1000"], meta_g3=meta)
    assert (cp["n_total"], cp["n_clusters"], cp["confirmed_n"]) == (532, 27, 1000)
    a12 = _row(cp, "G3-AUTO-12")
    assert a12["status"] == "PASS", a12
    assert "số chùm=50" in a12["evidence"] and "tối thiểu cần 27" in a12["evidence"]
    assert "khác số chùm suy từ N" not in a12["evidence"] and "hiệu chỉnh mẫu nhỏ" not in a12["evidence"]
    assert _row(cp, "G3-AUTO-09")["status"] == "PASS"
