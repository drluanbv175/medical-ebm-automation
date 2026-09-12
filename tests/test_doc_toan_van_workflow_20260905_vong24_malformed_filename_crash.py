r"""Hồi quy phát hiện #3 (Trung bình) của Workflow đối kháng đa-agent 2026-09-05
(vòng 24) trong tools/doc_toan_van.py::main() — một filename không đúng khuôn
dạng làm sập TOÀN BỘ lệnh tìm kiếm (--tim), không chỉ bỏ qua bản ghi lỗi.

CƠ CHẾ LỖI: `files = sorted(kho.glob("PMID-*.xml"))` (dòng ~57) là glob LỎNG,
chỉ đòi hỏi tiền tố "PMID-" + hậu tố ".xml" — chấp nhận MỌI file khớp mẫu
này. Nhưng dòng xử lý (~79) `pm = re.search(r"PMID-(\d+)_PMC(\d+)", f.name)`
đòi khuôn CHẶT HƠN hẳn: đúng "PMID-<số>_PMC<số>.xml". Nếu có file khớp glob
nhưng KHÔNG khớp regex (vd bác sĩ tự đổi tên thành "PMID-19393038_ghichu.xml"
để ghi chú riêng, hoặc copy nhầm 1 file từ nguồn khác vào thư mục
toan_van_oa/) VÀ nội dung file đó CÓ chứa cụm từ đang tìm — trước bản vá,
`pm.group(1)` được gọi ngay không kiểm `pm is not None`, ném
`AttributeError: 'NoneType' object has no attribute 'group'` NGAY LẬP TỨC,
làm sập toàn bộ vòng lặp `for f in files:` — KHÔNG chỉ mất kết quả của file
lỗi mà còn mất kết quả của MỌI file hợp lệ đứng SAU nó trong danh sách đã
`sorted()` theo alphabet.

Đúng họ lỗi "một bản ghi lỗi làm sập cả batch" đã lặp lại nhiều lần trong
repo này. Khác các ca trước ở chỗ: crash chỉ xảy ra khi file lỗi VỪA khớp
glob VỪA có nội dung khớp cụm tìm — nên là lỗi "ẩn mình" tới khi đúng điều
kiện, không phải crash ngay từ lần chạy đầu.

BẢN VÁ: kiểm `pm is None` trước khi gọi `.group()`; nếu None, in cảnh báo
ra stderr và `continue` sang file tiếp theo — không dừng vòng lặp. Đồng thời
dời `thay += 1` xuống SAU bước kiểm này để không đếm nhầm file bị bỏ qua vào
tổng số bài "chứa cụm tìm" (vì không hiển thị được kết quả của nó).

Nguyên tắc viết test: gọi THẲNG main() thật qua CLI thật (monkeypatch
D.EXPORTS trỏ vào tmp_path, monkeypatch sys.argv), với dữ liệu XML tối giản
đọc được bằng chính _van_ban() — không mock nội bộ."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import doc_toan_van as D  # noqa: E402

_XML = '<article><body><p>{}</p></body></article>'


def _dung_kho(tmp_path, study: str) -> Path:
    kho = tmp_path / study / "toan_van_oa"
    kho.mkdir(parents=True)
    return kho


class TestMotFileTenSaiKhuongKhongDuocLamSapCaBatch:
    """★★★ Ca chính — file khớp glob PMID-*.xml nhưng KHÔNG khớp khuôn
    PMID-<số>_PMC<số>.xml, có nội dung khớp cụm tìm, không được phép làm
    dừng vòng lặp và mất kết quả của các file hợp lệ khác."""

    def test_file_hop_le_van_duoc_bao_cao_du_co_file_ten_sai_dung_truoc(
        self, tmp_path, monkeypatch, capsys
    ):
        kho = _dung_kho(tmp_path, "STUDY-VONG24")
        # Tên "PMID-1..." sắp xếp TRƯỚC "PMID-9..." theo alphabet — đặt file
        # lỗi đứng TRƯỚC để chứng minh nó không chặn file hợp lệ đứng SAU.
        (kho / "PMID-19393038_ghichu.xml").write_text(
            _XML.format("response rate was also noted here"), encoding="utf-8", newline="\n"
        )
        (kho / "PMID-99999999_PMC8888888.xml").write_text(
            _XML.format("response rate was measured"), encoding="utf-8", newline="\n"
        )
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "STUDY-VONG24", "--tim", "response rate"])

        rc = D.main()  # TRƯỚC bản vá: ném AttributeError tại đây, test tự fail

        assert rc == 0
        out = capsys.readouterr().out
        assert "99999999" in out, (
            "TRƯỚC bản vá: crash ở file tên sai (PMID-19393038_ghichu.xml) làm mất "
            "hoàn toàn kết quả của PMID-99999999_PMC8888888.xml — file hợp lệ đứng "
            "SAU trong danh sách đã sắp xếp"
        )
        assert "PMC8888888" in out

    def test_canh_bao_duoc_in_ra_cho_file_ten_sai(self, tmp_path, monkeypatch, capsys):
        kho = _dung_kho(tmp_path, "STUDY-VONG24B")
        (kho / "PMID-19393038_ghichu.xml").write_text(
            _XML.format("response rate was also noted here"), encoding="utf-8", newline="\n"
        )
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "STUDY-VONG24B", "--tim", "response rate"])

        rc = D.main()

        assert rc == 0
        err = capsys.readouterr().err
        assert "PMID-19393038_ghichu.xml" in err
        assert "không đúng khuôn" in err

    def test_file_ten_sai_khong_bi_tinh_vao_so_bai_chua_cum_tim(self, tmp_path, monkeypatch, capsys):
        """File bị bỏ qua không được đếm vào tổng số bài 'chứa cụm tìm' —
        báo cáo phải trung thực rằng KHÔNG bài nào thật sự hiển thị được
        kết quả (thay = 0), dù file có nội dung khớp trên đĩa."""
        kho = _dung_kho(tmp_path, "STUDY-VONG24C")
        (kho / "PMID-19393038_ghichu.xml").write_text(
            _XML.format("response rate was also noted here"), encoding="utf-8", newline="\n"
        )
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "STUDY-VONG24C", "--tim", "response rate"])

        D.main()
        out = capsys.readouterr().out
        assert "Không bài nào trong 1 toàn văn" in out, (
            "thay phải giữ = 0 vì file duy nhất bị bỏ qua (tên sai khuôn), "
            "không được đếm nhầm là 'đã hiển thị kết quả'"
        )


class TestFileDungKhuongVanHoatDongBinhThuong:
    """Đối chứng bắt buộc — kho toàn CHỈ có file đúng khuôn không bị đổi
    hành vi sau bản vá."""

    def test_khong_co_file_loi_thi_bao_cao_dung_nhu_cu(self, tmp_path, monkeypatch, capsys):
        kho = _dung_kho(tmp_path, "STUDY-VONG24D")
        (kho / "PMID-11111111_PMC2222222.xml").write_text(
            _XML.format("response rate was measured"), encoding="utf-8", newline="\n"
        )
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "STUDY-VONG24D", "--tim", "response rate"])

        rc = D.main()

        assert rc == 0
        out = capsys.readouterr().out
        assert "PMID 11111111" in out
        assert "1/1 bài" in out

    def test_khong_khop_cum_tim_thi_bao_khong_co_dung_nhu_cu(self, tmp_path, monkeypatch, capsys):
        kho = _dung_kho(tmp_path, "STUDY-VONG24E")
        (kho / "PMID-11111111_PMC2222222.xml").write_text(
            _XML.format("unrelated content only"), encoding="utf-8", newline="\n"
        )
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "STUDY-VONG24E", "--tim", "response rate"])

        rc = D.main()

        assert rc == 0
        out = capsys.readouterr().out
        assert "Không bài nào" in out


class TestKhoRongVanBaoDoUngNhuCu:
    def test_thu_muc_khong_ton_tai_bao_loi_1(self, tmp_path, monkeypatch):
        monkeypatch.setattr(D, "EXPORTS", tmp_path)
        monkeypatch.setattr(sys, "argv", ["doc_toan_van.py", "--study", "KHONG-TON-TAI", "--tim", "x"])
        rc = D.main()
        assert rc == 1
