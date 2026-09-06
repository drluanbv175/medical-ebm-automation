"""Hồi quy phát hiện #2 (Trung bình) của Workflow đối kháng đa-agent
2026-09-05 (vòng 26) trong tools/verify_exports_integrity.py — nhánh
"+84..." của regex bắt số điện thoại quốc tế không bao giờ khớp được, do
`\\b` không nhận biên giữa hai ký tự KHÔNG PHẢI \\w.

CƠ CHẾ LỖI:
    (re.compile(r"\\b(?:0|\\+84)\\d{9,10}\\b"), "số điện thoại")

`\\b` chỉ khớp tại ranh giới giữa MỘT ký tự \\w và MỘT ký tự không phải
\\w. Vì "+" không phải \\w, và ký tự đứng trước nó trong văn bản thật
(khoảng trắng, dấu ":", đầu dòng) CŨNG không phải \\w, nên `\\b` KHÔNG BAO
GIỜ khớp ngay trước "+84" trong bất kỳ cách viết số điện thoại quốc tế
thông thường nào. Đã kiểm chứng bằng thực nghiệm (xem docstring/commit):
"+84912345678" không khớp trong mọi ngữ cảnh, trong khi nhánh "0..." vẫn
khớp bình thường (vì "0" LÀ \\w, và ký tự trước nó thường không phải \\w
nên \\b hoạt động đúng ở đó).

HẠI THẬT: tools/verify_exports_integrity.py được `.githooks/pre-commit`
gọi (--staged) để cảnh báo PII trong tài liệu nghiên cứu ở exports/. Một
số điện thoại bệnh nhân viết theo định dạng quốc tế "+84xxxxxxxxx" (phổ
biến khi copy từ hồ sơ/Excel) lọt qua HOÀN TOÀN, không một cảnh báo
EXP-PII nào được sinh ra.

BẢN VÁ: thay `\\b` bằng lookaround dựa trên chữ số — `(?<!\\d)` và
`(?!\\d)` — thay vì dựa vào \\w, cùng cách tools/clinical_checkpoint.py
đã làm cho mẫu SĐT_VN của nó.

Nguyên tắc viết test: gọi THẲNG check_file() thật (đọc file thật từ đĩa,
không mock regex nội bộ), kiểm Report.findings có đúng code EXP-PII cho
đúng dòng chứa số +84."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import verify_exports_integrity as VEI  # noqa: E402


def _pii_phone_findings(rep: VEI.Report) -> list:
    return [f for f in rep.findings if f.code == "EXP-PII" and "điện thoại" in f.message]


class TestSoDienThoaiQuocTePlus84:
    """★★★ Ca chính — số điện thoại dạng "+84..." phải được nhận diện là
    PII, không được lọt qua vì lỗi regex \\b."""

    def test_so_dien_thoai_plus84_dau_dong_duoc_bat(self, tmp_path):
        f = tmp_path / "PYTEST-du-lieu.md"
        f.write_text("+84912345678\n", encoding="utf-8", newline="\n")
        rep = VEI.Report()

        VEI.check_file(f, rep)

        assert _pii_phone_findings(rep), (
            "TRƯỚC bản vá: \\b không khớp được ngay trước '+' nên số điện "
            "thoại quốc tế '+84...' ở đầu dòng lọt qua hoàn toàn"
        )

    def test_so_dien_thoai_plus84_trong_cau_van_duoc_bat(self, tmp_path):
        f = tmp_path / "PYTEST-du-lieu.md"
        f.write_text("Liên hệ: +84912345678 để biết thêm chi tiết.\n", encoding="utf-8", newline="\n")
        rep = VEI.Report()

        VEI.check_file(f, rep)

        assert _pii_phone_findings(rep), (
            "TRƯỚC bản vá: '+84...' đứng sau dấu hai chấm/khoảng trắng "
            "(ngữ cảnh THẬT của tài liệu nghiên cứu) vẫn KHÔNG bị bắt"
        )

    def test_so_dien_thoai_trong_nuoc_0_van_duoc_bat_nhu_cu(self, tmp_path):
        """Đối chứng bắt buộc — nhánh "0..." (chưa bao giờ lỗi) vẫn hoạt
        động đúng như trước bản vá, không bị đổi hành vi."""
        f = tmp_path / "PYTEST-du-lieu.md"
        f.write_text("Số điện thoại: 0912345678\n", encoding="utf-8", newline="\n")
        rep = VEI.Report()

        VEI.check_file(f, rep)

        assert _pii_phone_findings(rep)

    def test_khong_co_so_dien_thoai_thi_khong_bao_dong_gia(self, tmp_path):
        """Đối chứng bắt buộc — PMID 8-9 chữ số không bị hiểu nhầm là số
        điện thoại (không dính lookaround mới)."""
        f = tmp_path / "PYTEST-du-lieu.md"
        f.write_text("PMID: 30267080\n", encoding="utf-8", newline="\n")
        rep = VEI.Report()

        VEI.check_file(f, rep)

        assert not _pii_phone_findings(rep)
