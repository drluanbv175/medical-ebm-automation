r"""Hồi quy phát hiện #1 (Cao) của Workflow đối kháng đa-agent 2026-09-05
(vòng 25) trong tools/tham_dinh_toan_van.py — CÙNG HỌ LỖI với phát hiện đã vá
tuần trước ở file song sinh tools/doc_toan_van.py, nhưng KHÔNG được backport
sang đây khi vá lần đầu.

CƠ CHẾ LỖI: `kho.glob("PMID-*.xml")` (dòng ~123) chấp nhận MỌI file khớp tiền
tố "PMID-" + hậu tố ".xml" (lỏng). Nhưng dict-comprehension xử lý
`re.search(r"PMID-(\d+)_", f.name).group(1)` đòi khuôn chặt hơn: phải có "_"
ngay sau chuỗi số (vd "PMID-11111111_PMC2222222.xml"). Nếu có MỘT file khớp
glob nhưng không khớp regex — vd "PMID-19393038.xml" (thiếu "_PMC...", do một
lần gom toàn văn thất bại một phần, hoặc bác sĩ tự đổi tên) — `re.search(...)`
trả None, và `.group(1)` ném AttributeError NGAY TRONG dict-comprehension,
TRƯỚC khi vào bất kỳ try/except nào. Ngoại lệ văng thẳng khỏi main(), sập
toàn bộ công cụ — mất kết quả thẩm định của MỌI PMID hợp lệ khác trong kho,
không chỉ file lỗi.

BẢN VÁ: dựng dict `xmls` bằng vòng lặp tường minh, kiểm `m is None` trước khi
gọi `.group(1)`; nếu None, in cảnh báo ra stderr và bỏ qua đúng file đó —
không dừng vòng lặp. Khớp đúng cách `tools/doc_toan_van.py` đã xử lý.

Nguyên tắc viết test: gọi THẲNG main() thật qua CLI thật (monkeypatch
T.EXPORTS + sys.argv), dựng đề cương .md tối giản có đủ marker [n] + danh
mục TLTK + kho toàn văn OA XML tối giản — không mock nội bộ."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import tham_dinh_toan_van as T  # noqa: E402

_XML = '<article><body><p>{}</p></body></article>'


def _dung_de_tai(tmp_path, study: str, *, pmid: str = "11111111", pmcid: str = "2222222",
                  cau: str = "Tỷ lệ đáp ứng là 12,5% [1].", noi_dung_xml: str = "response rate 12.5%",
                  malformed_pmid: str | None = "19393038"):
    sdir = tmp_path / study
    kho = sdir / "toan_van_oa"
    kho.mkdir(parents=True)
    if malformed_pmid is not None:
        (kho / f"PMID-{malformed_pmid}.xml").write_text(
            _XML.format("nội dung không liên quan"), encoding="utf-8", newline="\n"
        )
    (kho / f"PMID-{pmid}_PMC{pmcid}.xml").write_text(
        _XML.format(noi_dung_xml), encoding="utf-8", newline="\n"
    )
    doc = sdir / f"De-cuong_{study}.md"
    doc.write_text(
        f"# Đề cương\n\n{cau}\n\n"
        "## Tài liệu tham khảo\n"
        f"1. Tác giả X. Tạp chí. 2020. PMID: {pmid}\n",
        encoding="utf-8", newline="\n",
    )
    return sdir


class TestMotFileTenSaiKhuongKhongDuocLamSapCaBatch:
    """★★★ Ca chính — file khớp glob PMID-*.xml nhưng không khớp khuôn
    PMID-<số>_..., đứng lẫn trong kho, không được phép làm sập toàn bộ
    công cụ và mất kết quả của PMID hợp lệ khác."""

    def test_pmid_hop_le_van_duoc_doi_chieu_du_co_file_ten_sai(self, tmp_path, monkeypatch, capsys):
        _dung_de_tai(tmp_path, "STUDY-VONG25")
        monkeypatch.setattr(T, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["tham_dinh_toan_van.py", "--study", "STUDY-VONG25"])

        rc = T.main()  # TRƯỚC bản vá: ném AttributeError tại đây, test tự fail

        assert rc == 0
        out = capsys.readouterr().out
        assert "✓ 1" in out, (
            "TRƯỚC bản vá: file tên sai (PMID-19393038.xml) làm sập dict-comprehension "
            "ngay khi dựng danh sách kho, mất luôn kết quả đối chiếu PMID hợp lệ"
        )

    def test_canh_bao_duoc_in_ra_cho_file_ten_sai(self, tmp_path, monkeypatch, capsys):
        _dung_de_tai(tmp_path, "STUDY-VONG25B")
        monkeypatch.setattr(T, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["tham_dinh_toan_van.py", "--study", "STUDY-VONG25B"])

        rc = T.main()

        assert rc == 0
        err = capsys.readouterr().err
        assert "PMID-19393038.xml" in err
        assert "không đúng khuôn" in err

    def test_bao_cao_van_duoc_sinh_ra(self, tmp_path, monkeypatch, capsys):
        sdir = _dung_de_tai(tmp_path, "STUDY-VONG25C")
        monkeypatch.setattr(T, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["tham_dinh_toan_van.py", "--study", "STUDY-VONG25C"])

        rc = T.main()

        assert rc == 0
        bao_cao = list(sdir.glob("THAM-DINH-TOAN-VAN_*.md"))
        assert len(bao_cao) == 1


class TestKhoChiCoFileDungKhuongVanHoatDongBinhThuong:
    """Đối chứng bắt buộc — kho toàn CHỈ có file đúng khuôn không bị đổi
    hành vi sau bản vá."""

    def test_khong_co_file_loi_thi_bao_cao_dung_nhu_cu(self, tmp_path, monkeypatch, capsys):
        _dung_de_tai(tmp_path, "STUDY-VONG25D", malformed_pmid=None)
        monkeypatch.setattr(T, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["tham_dinh_toan_van.py", "--study", "STUDY-VONG25D"])

        rc = T.main()

        assert rc == 0
        out = capsys.readouterr().out
        assert "✓ 1" in out
        err = capsys.readouterr().err
        assert err == ""

    def test_khong_co_kho_toan_van_van_bao_loi_1_nhu_cu(self, tmp_path, monkeypatch):
        (tmp_path / "STUDY-VONG25E").mkdir()
        monkeypatch.setattr(T, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["tham_dinh_toan_van.py", "--study", "STUDY-VONG25E"])

        rc = T.main()

        assert rc == 1
