"""Hồi quy phát hiện #4 (THẤP) của Workflow đối kháng đa-agent 2026-09-06 (vòng 28)
trong tools/clinical_calc.py — nhánh CLI của lệnh `nnt` dùng truthy-check thay vì
`is not None` cho `args.n_control`/`args.n_experimental` (cả hai đều là int qua
`argparse(type=int)`).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    elif args.eer is not None and args.n_control and args.n_experimental:
        events_c = round(args.cer * args.n_control)
        ...
    else:
        raise ClinicalCalcError("Cần --rr, hoặc --or, hoặc (--eer + --n-control + "
                                 "--n-experimental).")

Nếu người dùng truyền TƯỜNG MINH `--n-control 0` (cỡ mẫu 0 — dữ liệu sai, nhưng là
một giá trị THẬT SỰ ĐƯỢC CUNG CẤP, không phải "quên truyền"), Python coi số nguyên 0
là falsy nên nhánh `elif` không khớp — code rơi vào `else`, in ra thông điệp CHUNG
CHUNG "Cần --rr, hoặc --or, hoặc (...)" như thể bác sĩ QUÊN truyền tham số, dù thực
ra CẢ BA tham số đều đã có mặt. Trong khi đó `nnt_from_counts()` (hàm tính toán
thật) đã có sẵn guard chính xác hơn nhiều: `if n_control <= 0 or n_experimental <= 0:
raise ClinicalCalcError("Cỡ mẫu mỗi nhóm phải dương.")` — nhưng guard đó KHÔNG BAO
GIỜ được chạm tới vì nhánh `elif` đã chặn trước ở lớp CLI.

Mức độ: KHÔNG gây ra kết quả tính toán SAI (cả hai đường đều dừng bằng
ClinicalCalcError, tức fail-closed) — chỉ sai THÔNG ĐIỆP LỖI, khiến bác sĩ đọc lầm
"tôi quên truyền tham số" thay vì "tôi truyền cỡ mẫu bằng 0, phải sửa số liệu".

BẢN VÁ: đổi điều kiện thành `args.eer is not None and args.n_control is not None
and args.n_experimental is not None` — phân biệt đúng "chưa truyền" (None, argparse
default) với "đã truyền giá trị 0" (int 0), để luồng đi đúng tới
`nnt_from_counts()` và nhận thông điệp chính xác.

Nguyên tắc viết test: gọi THẲNG CC.main() thật qua monkeypatch sys.argv (main()
không nhận tham số argv, đọc trực tiếp sys.argv qua argparse) — không mock nội bộ
nnt_from_counts()/nnt_from_or()/nnt_from_rr(), để test khóa đúng HÀNH VI CLI thật."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import clinical_calc as CC  # noqa: E402


def _run_cli(monkeypatch, argv: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["clinical_calc.py", *argv])
    return CC.main()


class TestNControlBangKhongDiDungNhanhTinhToan:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. --n-control 0 phải đi tới
    nnt_from_counts() (thông điệp 'Cỡ mẫu mỗi nhóm phải dương.'), KHÔNG được rơi
    vào nhánh 'Cần --rr, hoặc --or...' như thể tham số chưa được truyền."""

    def test_n_control_bang_khong_bao_dung_thong_diep(self, monkeypatch, capsys):
        rc = _run_cli(
            monkeypatch,
            ["nnt", "--cer", "0.30", "--eer", "0.20",
             "--n-control", "0", "--n-experimental", "500"],
        )
        out = capsys.readouterr().out

        assert rc == 1
        assert "Cỡ mẫu mỗi nhóm phải dương." in out, (
            "TRƯỚC bản vá: `args.n_control` = int 0 là falsy trong Python nên "
            "`elif args.eer is not None and args.n_control and args.n_experimental` "
            "không khớp — code rơi vào nhánh else, in thông điệp CHUNG CHUNG "
            "'Cần --rr, hoặc --or...' dù cả ba tham số ĐÃ được truyền đầy đủ."
        )
        assert "Cần --rr, hoặc --or" not in out

    def test_n_experimental_bang_khong_cung_dung_nhanh(self, monkeypatch, capsys):
        """Đối xứng: n_experimental=0 phải cho cùng kết quả (không riêng gì
        n_control)."""
        rc = _run_cli(
            monkeypatch,
            ["nnt", "--cer", "0.30", "--eer", "0.20",
             "--n-control", "500", "--n-experimental", "0"],
        )
        out = capsys.readouterr().out

        assert rc == 1
        assert "Cỡ mẫu mỗi nhóm phải dương." in out


class TestDoiChungDuongThieuThamSoVanBaoChung:
    """Đối chứng bắt buộc — khi tham số THỰC SỰ chưa được truyền (None, không phải
    0), thông điệp chung chung 'Cần --rr, hoặc --or...' vẫn phải xuất hiện đúng như
    trước — bản vá không được đổi hành vi của đường THIẾU tham số thật."""

    def test_thieu_n_control_hoan_toan_van_bao_chung(self, monkeypatch, capsys):
        rc = _run_cli(
            monkeypatch,
            ["nnt", "--cer", "0.30", "--eer", "0.20", "--n-experimental", "500"],
        )
        out = capsys.readouterr().out

        assert rc == 1
        assert "Cần --rr, hoặc --or, hoặc (--eer + --n-control + --n-experimental)." in out

    def test_khong_truyen_eer_ma_khong_co_rr_or_van_bao_chung(self, monkeypatch, capsys):
        rc = _run_cli(monkeypatch, ["nnt", "--cer", "0.30"])
        out = capsys.readouterr().out

        assert rc == 1
        assert "Cần --rr, hoặc --or, hoặc (--eer + --n-control + --n-experimental)." in out


class TestDoiChungDuongThanhCongKhongDoi:
    """Đối chứng bắt buộc — đường tính NNT thành công bình thường (n_control/
    n_experimental dương, hợp lệ) không bị ảnh hưởng bởi bản vá."""

    def test_duong_thanh_cong_van_ra_ket_qua_dung(self, monkeypatch, capsys):
        rc = _run_cli(
            monkeypatch,
            ["nnt", "--cer", "0.30", "--eer", "0.20",
             "--n-control", "500", "--n-experimental", "500", "--json"],
        )
        out = capsys.readouterr().out

        assert rc == 0
        assert '"nnt"' in out
        assert "Cần bác sĩ" not in out  # --json không in disclaimer văn xuôi
