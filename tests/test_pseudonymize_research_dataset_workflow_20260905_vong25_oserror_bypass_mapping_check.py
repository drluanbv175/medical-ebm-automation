"""Hồi quy phát hiện #4 (Trung bình, hậu quả nghiêm trọng nếu kích hoạt) của
Workflow đối kháng đa-agent 2026-09-05 (vòng 25) trong
tools/pseudonymize_research_dataset.py::_readable_blocker() — một OSError khi
so sánh đường dẫn làm bỏ qua LUÔN lớp kiểm CỐT LÕI chống rò PII qua bảng ánh
xạ (linkage map).

CƠ CHẾ LỖI:
    try:
        if data_path.resolve() == output_path.resolve():
            return "output_path_must_not_overwrite_source"
    except OSError:
        return None          # <-- BỎ QUA LUÔN _mapping_root_blocker() phía dưới
    return _mapping_root_blocker(mapping_root, exports_root)

`_mapping_root_blocker()` là lớp kiểm CỐT LÕI ngăn bảng ánh xạ (chứa PII gốc:
tên/email/SĐT/CCCD thật) bị ghi vào bên trong repo, `exports/`, hoặc thư mục
đồng bộ OneDrive. Nếu `data_path.resolve()`/`output_path.resolve()` ném
OSError (đường dẫn lạ trên Windows, symlink lỗi/vòng lặp — các tình huống mà
chính codebase này thừa nhận là có thật, xem hàng loạt xử lý riêng cho
Windows trong tools/secure_permissions.py), `return None` khiến hàm trả về
"không có blocker gì" MÀ KHÔNG BAO GIỜ chạy tới `_mapping_root_blocker` —
bỏ qua hoàn toàn lớp bảo vệ chống rò PII, để `pseudonymize_dataset()` tiếp
tục ghi `linkage_map.csv` vào một vị trí lẽ ra phải bị chặn.

Đối lập trực tiếp với triết lý fail-closed mà file này theo đuổi ở MỌI chỗ
khác (vd _mapping_root_blocker tự nó không có đường lách nào khác).

BẢN VÁ: nhánh `except OSError:` không còn `return None` — chỉ `pass` (bỏ
qua được PHÉP kiểm trùng đường dẫn overwrite, vì không so sánh được), rồi
vẫn tiếp tục chạy `_mapping_root_blocker(mapping_root, exports_root)` như
bình thường. Hai việc độc lập, việc trước không được làm tắt việc sau.

Nguyên tắc viết test: gọi THẲNG `_readable_blocker()` thật. Để tái hiện
OSError một cách xác định (không phụ thuộc hành vi symlink-loop khác nhau
giữa các hệ điều hành/phiên bản Python), dùng một đối tượng giả lập tối
giản chỉ ghi đè `.resolve()` để ném OSError, giữ nguyên `.suffix`/`.exists()`
thật — đây là input CHÍNH XÁC kích hoạt đúng nhánh except OSError của hàm
đang kiểm, không phải mock hành vi của hàm."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import pseudonymize_research_dataset as PRD  # noqa: E402


class _GioiHanResolveNemOSError:
    """Bọc một Path thật, chỉ ghi đè .resolve() để ném OSError — mô phỏng
    đúng tình huống thật (symlink vòng lặp, đường dẫn lạ trên Windows) mà
    không phụ thuộc hành vi hệ điều hành."""

    def __init__(self, real_path: Path):
        self._real = real_path

    @property
    def suffix(self) -> str:
        return self._real.suffix

    def exists(self) -> bool:
        return self._real.exists()

    def resolve(self):
        raise OSError("giả lập lỗi resolve() — symlink vòng lặp/đường dẫn lạ")


class TestOSErrorKhiSoSanhDuongDanKhongDuocBoQuaKiemMappingRoot:
    """★★★ Ca chính — OSError khi so sánh data_path/output_path không được
    phép làm tắt lớp kiểm mapping_root (chống rò PII qua bảng ánh xạ)."""

    def test_mapping_root_trong_repo_van_bi_chan_du_resolve_nem_oserror(self, tmp_path):
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\n1,2\n", encoding="utf-8", newline="\n")
        output = tmp_path / "out.csv"
        mapping_root_khong_an_toan = PRD.BASE / "mapping_root_khong_an_toan_test"
        exports_root = tmp_path / "exports"

        ket_qua = PRD._readable_blocker(
            _GioiHanResolveNemOSError(data),
            _GioiHanResolveNemOSError(output),
            mapping_root_khong_an_toan,
            exports_root,
        )

        assert ket_qua == "mapping_root_inside_repo", (
            "TRƯỚC bản vá: except OSError: return None bỏ qua LUÔN "
            "_mapping_root_blocker() — mapping_root nằm trong repo (chứa PII "
            "gốc: tên/email/SĐT/CCCD của bảng ánh xạ) sẽ KHÔNG bị chặn"
        )

    def test_mapping_root_trong_exports_van_bi_chan_du_resolve_nem_oserror(self, tmp_path):
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\n1,2\n", encoding="utf-8", newline="\n")
        output = tmp_path / "out.csv"
        exports_root = tmp_path / "exports"
        mapping_root_khong_an_toan = exports_root / "mapping_lo_pii"

        ket_qua = PRD._readable_blocker(
            _GioiHanResolveNemOSError(data),
            _GioiHanResolveNemOSError(output),
            mapping_root_khong_an_toan,
            exports_root,
        )

        assert ket_qua == "mapping_root_inside_exports"

    def test_mapping_root_an_toan_van_khong_bi_bao_dong_gia(self, tmp_path):
        """Đối chứng bắt buộc — mapping_root NẰM NGOÀI repo/exports/OneDrive
        vẫn phải được chấp nhận (None) ngay cả khi resolve() ném OSError ở
        bước kiểm overwrite — không được biến thành báo động giả."""
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\n1,2\n", encoding="utf-8", newline="\n")
        output = tmp_path / "out.csv"
        exports_root = tmp_path / "exports"
        mapping_root_an_toan = tmp_path / "noi_an_toan" / "mapping"

        ket_qua = PRD._readable_blocker(
            _GioiHanResolveNemOSError(data),
            _GioiHanResolveNemOSError(output),
            mapping_root_an_toan,
            exports_root,
        )

        assert ket_qua is None


class TestKhongCoOSErrorVanHoatDongBinhThuong:
    """Đối chứng bắt buộc — đường đi KHÔNG có OSError (trường hợp thường
    gặp) không bị đổi hành vi sau bản vá."""

    def test_mapping_root_trong_repo_bi_chan_binh_thuong(self, tmp_path):
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\n1,2\n", encoding="utf-8", newline="\n")
        output = tmp_path / "out.csv"
        mapping_root_khong_an_toan = PRD.BASE / "mapping_root_khong_an_toan_test2"
        exports_root = tmp_path / "exports"

        ket_qua = PRD._readable_blocker(data, output, mapping_root_khong_an_toan, exports_root)

        assert ket_qua == "mapping_root_inside_repo"

    def test_mapping_root_an_toan_bi_chan_khi_trung_output_va_data(self, tmp_path):
        same = tmp_path / "same.csv"
        same.write_text("ten,ket_qua\n1,2\n", encoding="utf-8", newline="\n")
        exports_root = tmp_path / "exports"
        mapping_root_an_toan = tmp_path / "noi_an_toan" / "mapping"

        ket_qua = PRD._readable_blocker(same, same, mapping_root_an_toan, exports_root)

        assert ket_qua == "output_path_must_not_overwrite_source"
