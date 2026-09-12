"""Hồi quy phát hiện #4 (audit vòng 39, 2026-09-06) trong
research_project/project_cli.py::_build_parser() — cờ CLI boolean chết.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    p_qa.add_argument("--save-report", action="store_true", default=True, ...)
    p_rp.add_argument("--run-qa-first", action="store_true", default=True)

`action="store_true"` kết hợp `default=True` là một cờ CHẾT: argparse chỉ
cho phép BẬT giá trị True (cờ có mặt → True), không có cách nào để TRUYỀN
False qua dòng lệnh — kể cả khi flag có mặt, giá trị vẫn là True. Không có
cờ `--no-save-report`/`--no-run-qa-first` tương ứng, nên `run_project_qa
(..., save_report=False)` — một hành vi HỢP LỆ và có thật trong hàm được
gọi, được test unit khác dùng trực tiếp — KHÔNG THỂ đạt tới được qua CLI
`researchctl project-qa`/`project-review-pack` dù người dùng có gõ cờ gì.

BẢN VÁ: `action=argparse.BooleanOptionalAction` (có từ Python 3.9, tương
thích sàn `target-version = "py39"` của ruff.toml) — cho cả `--save-report`/
`--no-save-report` và `--run-qa-first`/`--no-run-qa-first`.

PHẠM VI ẢNH HƯỞNG: `researchctl project-qa` và `researchctl
project-review-pack` là 2 trong 20 subcommand thật của CLI chính thức
(`_build_parser()` — nội bộ nhánh mồ côi research_project, nhưng là CLI
thật 100% trong chính thư mục này)."""
from __future__ import annotations

from research_project.project_cli import _build_parser


class TestCaChinhNoSaveReportPhaiChiSangFalse:
    """★★★ Ca chính — cờ --no-save-report / --no-run-qa-first phải thực sự
    truyền False, không bị argparse coi là store_true bất chấp cờ."""

    def test_no_save_report_dat_false(self):
        parser = _build_parser()
        args = parser.parse_args([
            "project-qa", "--project-id", "SYNTH-01", "--no-save-report",
        ])
        assert args.save_report is False, (
            "TRƯỚC bản vá: action='store_true' + default=True khiến "
            "--no-save-report KHÔNG có tác dụng gì — save_report luôn True."
        )

    def test_no_run_qa_first_dat_false(self):
        parser = _build_parser()
        args = parser.parse_args([
            "project-review-pack", "--project-id", "SYNTH-01", "--no-run-qa-first",
        ])
        assert args.run_qa_first is False, (
            "TRƯỚC bản vá: --no-run-qa-first không tồn tại / không có tác "
            "dụng — run_qa_first luôn True bất kể cờ dòng lệnh."
        )


class TestDoiChungMacDinhVaCoDatTrucTiepVanDung:
    """Đối chứng — không truyền cờ vẫn mặc định True (không đổi hành vi
    mặc định cũ); truyền tường minh --save-report/--run-qa-first vẫn True."""

    def test_khong_truyen_co_van_mac_dinh_true(self):
        parser = _build_parser()
        args = parser.parse_args(["project-qa", "--project-id", "SYNTH-01"])
        assert args.save_report is True

        args2 = parser.parse_args(["project-review-pack", "--project-id", "SYNTH-01"])
        assert args2.run_qa_first is True

    def test_truyen_co_duong_tuong_minh_van_true(self):
        parser = _build_parser()
        args = parser.parse_args([
            "project-qa", "--project-id", "SYNTH-01", "--save-report",
        ])
        assert args.save_report is True

        args2 = parser.parse_args([
            "project-review-pack", "--project-id", "SYNTH-01", "--run-qa-first",
        ])
        assert args2.run_qa_first is True
