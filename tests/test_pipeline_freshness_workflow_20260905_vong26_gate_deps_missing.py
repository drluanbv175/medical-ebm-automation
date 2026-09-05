"""Hồi quy phát hiện #1 (Nghiêm trọng) của Workflow đối kháng đa-agent
2026-09-05 (vòng 26) trong tools/pipeline_freshness.py — bảng GATE_DEPS lạc
hậu so với những gì các run_g*_auto.py THỰC SỰ đọc, làm tắt chính cơ chế
chống stale-checkpoint mà module này sinh ra để bảo vệ.

CƠ CHẾ LỖI: GATE_DEPS trước bản vá khai:
    "G3": ["G0", "G1"],
    "G4": ["G3"],
    "G5": ["G0", "G1", "G3"],
    "G6": ["G5"],
Nhưng đối chiếu trực tiếp mã nguồn (không suy đoán):
    - run_g3_auto.py gọi GC.resolve_design_code(out_dir), hàm này đọc CẢ
      G1_checkpoint.json LẪN G2_checkpoint.json (gate_contract.py dòng
      ~626-627) — G3 THIẾU G2 trong bảng.
    - run_g4_auto.py đọc trực tiếp G0/G1/G3 (load_cp, dòng 496-498) + gọi
      resolve_design_code() đọc thêm G1/G2 (dòng 505) — G4 THIẾU CẢ G0,
      G1, G2.
    - run_g5_auto.py đọc trực tiếp G0/G1/G2/G3 (dòng 2287-2290) — G5
      THIẾU G2.
    - run_g6_auto.py đọc trực tiếp G0/G1/G3/G4 (dòng 3109-3112) + gọi
      resolve_design_code() đọc thêm G1/G2 (dòng 3125) — G6 THIẾU G0, G1,
      G2, G3, G4.

HẠI THẬT: g10_quality_gate.py dùng đúng pipeline_freshness.stale_report()
làm tiêu chí BLOCK cứng (G10-AUTO-03) trước khi lắp gói nộp. Một đề tài mà
bác sĩ SỬA thiết kế ở G2 (vd cohort → RCT, qua --design) SAU KHI đã chạy
G3/G4/G5/G6 sẽ đi qua tiêu chí này mà KHÔNG bị chặn — dù chuẩn báo cáo
(CONSORT/STROBE...)/công thức cỡ mẫu/SAP đang dựa trên thiết kế CŨ. Đây
đúng lớp lỗi "G7 seed nhiễm PMID đề tài khác" mà chính module này (xem
docstring dòng 4-11) tự nhận là lý do ra đời, nay tái diễn ở trục
design_code.

BẢN VÁ: cập nhật GATE_DEPS cho khớp đúng những gì load_cp()/
resolve_design_code() thực sự đọc ở từng run_g*_auto.py.

Nguyên tắc viết test: gọi THẲNG stale_report()/find_stale_gates() thật,
ghi checkpoint bằng os.utime() để kiểm soát mtime chính xác — tái hiện
ĐÚNG kịch bản thật (bác sĩ sửa G2 rất lâu sau khi G3/G4/G5/G6 đã chạy)."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import pipeline_freshness as FRESH  # noqa: E402


def _write_cp(d: Path, gate: str, mtime: float) -> Path:
    p = d / f"{gate}_checkpoint.json"
    p.write_text(json.dumps({"gate": gate}, ensure_ascii=False), encoding="utf-8", newline="\n")
    os.utime(p, (mtime, mtime))
    return p


class TestG3PhuThuocG2:
    """★★★ Ca chính — G3 gọi resolve_design_code() đọc G2, nên G2 đổi SAU
    khi G3 đã chạy phải làm G3 stale."""

    def test_g2_doi_sau_g3_lam_g3_stale(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 5)
        # Bác sĩ SỬA thiết kế ở G2 rất lâu sau khi G3 đã chạy.
        _write_cp(tmp_path, "G2", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G3" in report["stale_gates"], (
            "TRƯỚC bản vá: GATE_DEPS['G3'] không có 'G2' nên thay đổi G2 "
            "sau khi G3 đã chạy KHÔNG BAO GIỜ bị phát hiện — G3 dùng "
            "design_code CŨ mà không ai biết"
        )

    def test_khong_doi_g2_thi_van_tuoi(self, tmp_path):
        """Đối chứng — không ai sửa gì thì chuỗi vẫn tươi (không báo động giả)."""
        base = time.time()
        for i, g in enumerate(["G0", "G1", "G2", "G3"]):
            _write_cp(tmp_path, g, base + i)
        report = FRESH.stale_report(tmp_path)
        assert report["fresh"] is True


class TestG4PhuThuocG0G1G2:
    """★★★ Ca chính — G4 đọc trực tiếp G0/G1 + gọi resolve_design_code()
    đọc G1/G2, nên cả ba đổi SAU khi G4 đã chạy phải làm G4 stale."""

    def test_g0_doi_sau_g4_lam_g4_stale(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 5)
        _write_cp(tmp_path, "G4", base + 6)
        # G0 (topic) được chạy lại rất lâu sau khi G4 (SAP) đã khoá.
        _write_cp(tmp_path, "G0", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G4" in report["stale_gates"], (
            "TRƯỚC bản vá: GATE_DEPS['G4'] chỉ có ['G3'] — thay đổi G0/G1/G2 "
            "sau khi G4 đã chạy KHÔNG BAO GIỜ bị phát hiện"
        )

    def test_g2_doi_sau_g4_lam_g4_stale(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 5)
        _write_cp(tmp_path, "G4", base + 6)
        _write_cp(tmp_path, "G2", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G4" in report["stale_gates"]


class TestG5PhuThuocG2:
    def test_g2_doi_sau_g5_lam_g5_stale(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 3)
        _write_cp(tmp_path, "G5", base + 6)
        _write_cp(tmp_path, "G2", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G5" in report["stale_gates"], (
            "TRƯỚC bản vá: GATE_DEPS['G5'] không có 'G2' — sửa thiết kế ở "
            "G2 sau khi khóa dữ liệu G5 không bị bắt"
        )


class TestG6PhuThuocDayDu:
    """★★★ Ca chính — tái hiện ĐÚNG kịch bản của phát hiện #1: bác sĩ sửa
    G2 rất lâu sau khi cả chuỗi G3→G4→G5→G6 đã chạy xong."""

    def test_g2_doi_sau_toan_bo_chuoi_lam_g6_stale(self, tmp_path):
        base = time.time()
        for i, g in enumerate(["G0", "G1", "G2", "G3", "G4", "G5", "G6"]):
            _write_cp(tmp_path, g, base + i)
        # Bác sĩ sửa --design ở G2 rất lâu sau khi cả chuỗi đã chạy.
        _write_cp(tmp_path, "G2", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G6" in report["stale_gates"], (
            "TRƯỚC bản vá: GATE_DEPS['G6'] chỉ có ['G5'] — G6 sinh script R "
            "theo design_code CŨ mà không có cảnh báo nào, đúng kịch bản "
            "'G7 seed nhiễm PMID đề tài khác' tái diễn ở trục design_code"
        )
        # G3/G4/G5 cũng phải bị bắt cùng lúc — đây là điểm khác biệt chính
        # với hành vi cũ (trước bản vá KHÔNG gate nào trong số này bắt được).
        assert "G3" in report["stale_gates"]
        assert "G4" in report["stale_gates"]
        assert "G5" in report["stale_gates"]

    def test_g4_doi_sau_g6_lam_g6_stale(self, tmp_path):
        base = time.time()
        for i, g in enumerate(["G0", "G1", "G2", "G3", "G4", "G5", "G6"]):
            _write_cp(tmp_path, g, base + i)
        _write_cp(tmp_path, "G4", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G6" in report["stale_gates"], (
            "TRƯỚC bản vá: GATE_DEPS['G6'] chỉ có ['G5'] — không phát hiện "
            "được G4 (chứa g4_status/N/alpha/power) đổi sau khi G6 đã chạy"
        )


class TestG2G3HaiChieuKhongTaoVongLap:
    """Đối chứng — G2 phụ thuộc G3 (đã có từ trước, không đổi) VÀ G3 phụ
    thuộc G2 (mới thêm) là 2 lý do ĐỘC LẬP, không tạo vòng lặp hay crash."""

    def test_g3_doi_sau_g2_lam_g2_stale_dung_nhu_truoc(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 100000)

        report = FRESH.stale_report(tmp_path)

        assert "G2" in report["stale_gates"]

    def test_ca_hai_chieu_cung_luc_khong_crash(self, tmp_path):
        """G2 VÀ G3 đều đổi sau nhau nhiều lần — chỉ cần hàm chạy xong,
        không lặp vô hạn, không ném lỗi."""
        base = time.time()
        _write_cp(tmp_path, "G0", base)
        _write_cp(tmp_path, "G1", base + 1)
        _write_cp(tmp_path, "G2", base + 2)
        _write_cp(tmp_path, "G3", base + 3)
        _write_cp(tmp_path, "G2", base + 4)
        _write_cp(tmp_path, "G3", base + 5)

        report = FRESH.stale_report(tmp_path)  # không được ném lỗi/treo

        assert isinstance(report, dict)
