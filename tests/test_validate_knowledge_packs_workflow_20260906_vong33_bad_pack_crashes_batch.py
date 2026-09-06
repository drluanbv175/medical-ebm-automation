r"""Hồi quy phát hiện #4 (HIGH) của audit vòng 33 (2026-09-06) trong
tools/validate_knowledge_packs.py::main() — một knowledge pack có cấu trúc
thư mục lỗi làm sập TOÀN BỘ lệnh validate, khiến các pack khác (kể cả pack
hợp lệ) không được validate hay báo cáo.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    results = [validate_pack_version(pack_dir, args.version) for pack_dir in pack_dirs]

Không try/except từng pack. Nếu một pack có thư mục phiên bản (vd
"2026.1-draft/") vô tình tồn tại dưới dạng FILE thay vì thư mục — dễ xảy ra
do merge lỗi, thao tác tay nhầm, hoặc đồng bộ OneDrive dở dang —
``validate_pack_version()`` (app/services/knowledge_pack_schema.py:262,
``version_path.iterdir()``) ném ``NotADirectoryError`` không được bắt, làm
sập toàn bộ lệnh — không pack nào (kể cả các pack hợp lệ khác) được validate
hay báo cáo.

Tái hiện độc lập TRƯỚC khi vá:
    pack_dirs = [pack_good (thư mục hợp lệ), pack_bad (file thay vì thư mục)]
    [validate_pack_version(pd, "2026.1-draft") for pd in pack_dirs]
    -> NotADirectoryError, không pack nào (kể cả pack_good) được báo cáo

BẢN VÁ: bọc từng ``validate_pack_version()`` trong try/except ``OSError`` —
pack lỗi cấu trúc thư mục nay trả về một ``KnowledgePackSchemaResult`` FAIL
kèm lý do cụ thể, thay vì sập cả lô; các pack khác vẫn được validate và báo
cáo bình thường.

Nguyên tắc viết test: gọi ``main()`` THẬT qua monkeypatch ``sys.argv``
(không phải subprocess — module không có phụ thuộc mạng/side-effect nặng
nên gọi trực tiếp trong-tiến-trình là đủ và nhanh hơn), bắt stdout bằng
``capsys`` để xác nhận cả hai pack đều xuất hiện trong output."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import validate_knowledge_packs as VKP  # noqa: E402


def _make_packs(tmp_path: Path) -> Path:
    packs_dir = tmp_path / "knowledge-packs"
    good = packs_dir / "pack_good" / "2026.1-draft"
    good.mkdir(parents=True)
    bad_pack = packs_dir / "pack_bad"
    bad_pack.mkdir(parents=True)
    (bad_pack / "2026.1-draft").write_text(
        "oops — not a directory", encoding="utf-8", newline="\n"
    )
    return packs_dir


class TestMotPackHongKhongLamSapCaLo:
    """★★★ Ca chính — pack có "2026.1-draft" là FILE thay vì thư mục không
    được làm sập validate của các pack khác."""

    def test_pack_hong_khong_sap_lenh_va_pack_tot_van_duoc_bao_cao(
        self, tmp_path, monkeypatch, capsys
    ):
        packs_dir = _make_packs(tmp_path)
        monkeypatch.setattr(
            sys, "argv",
            ["validate_knowledge_packs.py", "--packs-dir", str(packs_dir)],
        )

        try:
            exit_code = VKP.main()
        except NotADirectoryError as exc:
            raise AssertionError(
                "TRƯỚC bản vá: pack_bad/2026.1-draft là file (không phải thư "
                "mục) khiến validate_pack_version() ném NotADirectoryError, "
                f"sập toàn bộ main(). Lỗi: {exc}"
            ) from exc

        out = capsys.readouterr().out
        assert "pack_good" in out, (
            f"pack_good phải xuất hiện trong báo cáo dù pack_bad lỗi. Output: {out!r}"
        )
        assert "pack_bad" in out
        assert exit_code == 1, "Còn pack FAIL (pack_bad lỗi cấu trúc) nên exit code phải là 1"

    def test_pack_hong_duoc_bao_cao_fail_khong_phai_pass_am_tham(self, tmp_path, monkeypatch, capsys):
        packs_dir = _make_packs(tmp_path)
        monkeypatch.setattr(
            sys, "argv",
            ["validate_knowledge_packs.py", "--packs-dir", str(packs_dir)],
        )
        VKP.main()
        out = capsys.readouterr().out

        bad_line = next(line for line in out.splitlines() if line.startswith(("PASS", "FAIL")) and "pack_bad" in line)
        assert bad_line.startswith("FAIL"), (
            f"pack_bad lỗi cấu trúc thư mục phải được báo FAIL, không được coi "
            f"như PASS âm thầm. Dòng thực tế: {bad_line!r}"
        )


class TestDoiChungChiCoPackTotVanChayBinhThuong:
    """Đối chứng — khi không có pack nào lỗi, hành vi cũ (không try/except)
    vẫn hoạt động đúng như trước, bản vá không đổi đường PASS bình thường."""

    def test_chi_co_pack_tot_van_bao_cao_dung(self, tmp_path, monkeypatch, capsys):
        packs_dir = tmp_path / "knowledge-packs"
        (packs_dir / "pack_ok" / "2026.1-draft").mkdir(parents=True)
        monkeypatch.setattr(
            sys, "argv",
            ["validate_knowledge_packs.py", "--packs-dir", str(packs_dir)],
        )
        VKP.main()
        out = capsys.readouterr().out
        assert "pack_ok" in out
