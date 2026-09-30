"""Kiểm connector Wiley TDM API — thêm 23/09/2026.

Tất cả test OFFLINE: thư viện `wiley_tdm` bị GIẢ LẬP qua `sys.modules` (một
`TDMClient` giả ghi lại lời gọi thay vì gọi mạng Wiley thật) — không phụ thuộc
việc `wiley-tdm` có được cài trong venv chạy test hay không, và không bao giờ
gọi mạng thật, đúng quy ước `tests/test_scopus.py`.

Sửa 30/09/2026 (lỗi đơn vị của `kich_thuoc_byte`): bản giả cũ trả `size=1234` mà
không có tệp nào trên đĩa, tức ngầm coi `DownloadResult.size` là byte — đúng giả
định sai đã để con số KiB của thư viện (8705 cho tệp 8.913.789 byte) đi ra ngoài
dưới tên «byte». Bản giả nay ghi tệp thật và báo `size` theo KiB như thư viện;
một ca riêng gọi thẳng `FileUtils.save_file` của thư viện THẬT để chính bản giả
cũng bị đối chiếu. Mỗi test đứng trong `tmp_path`, không ghi gì vào cây repo.
"""
from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path
from typing import List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.wiley_tdm import THU_MUC_TAI_MAC_DINH  # noqa: E402

# Hai con số đo 30/09/2026 với DOI 10.1002/jcsm.70385: tệp trên đĩa và số thư viện báo.
_SO_BYTE_DO_THAT = 8_913_789
_SO_KIB_THU_VIEN_BAO = 8705


@pytest.fixture(autouse=True)
def _don_cau_hinh_wiley(monkeypatch, tmp_path):
    """Cô lập cấu hình Wiley TDM khỏi .env thật của máy đang chạy test — mỗi
    test tự đặt giá trị nó cần, không phụ thuộc môi trường ngoài.

    Đứng trong `tmp_path`: thư mục tải mặc định là đường dẫn TƯƠNG ĐỐI, bản giả nay
    ghi tệp thật nên nếu đứng ở gốc repo sẽ rải tệp vào cây làm việc."""
    monkeypatch.setattr(settings, "enable_wiley_tdm", False)
    monkeypatch.setattr(settings, "wiley_tdm_api_token", "")
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", "")
    monkeypatch.setattr(settings, "wiley_tdm_rate_limit_seconds", 10.0)
    monkeypatch.chdir(tmp_path)
    yield


def _kib_nhu_thu_vien(tep: Path) -> int:
    """Đúng công thức của thư viện thật: `FileUtils.get_file_size_kb` = round(st_size / 1024)."""
    return round(tep.stat().st_size / 1024)


_DAU_PDF = b"%PDF-1.7\n"
_DUOI_PDF = b"\nstartxref\n9\n%%EOF\n"


def _noi_dung_pdf_gia(so_byte: int, tron_ven: bool = True) -> bytes:
    """Đúng `so_byte` byte, đầu mang chữ ký «%PDF-». `tron_ven=True` (mặc định): cuối có
    «startxref … %%EOF» như mọi PDF thật. `tron_ven=False`: tệp bị cắt giữa chừng — mất đoạn cuối."""
    if not tron_ven:
        return _DAU_PDF + b"\0" * (so_byte - len(_DAU_PDF))
    return _DAU_PDF + b"\0" * (so_byte - len(_DAU_PDF) - len(_DUOI_PDF)) + _DUOI_PDF


def _ghi_tep_pdf_gia(tep: Path, so_byte: int, tron_ven: bool = True) -> Path:
    """Ghi một tệp dài đúng `so_byte` byte. Ghi tường minh từng byte: `truncate` để nới tệp thì
    kết quả tuỳ nền tảng, mà ca kiểm này sống nhờ con số chính xác.

    Sửa 30/09/2026: bản cũ chỉ ghi chữ ký «%PDF-» rồi toàn byte 0 — đúng hình một tệp GHI DỞ. Từ
    khi `thanh_cong` đòi tệp trông trọn vẹn, tệp «tải xong» của bản giả phải có cả dấu «%%EOF»."""
    tep.parent.mkdir(parents=True, exist_ok=True)
    tep.write_bytes(_noi_dung_pdf_gia(so_byte, tron_ven))
    assert tep.stat().st_size == so_byte
    return tep


class _FakeDownloadStatus:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeDownloadResult:
    """`size` mang KiB làm tròn, như `wiley_tdm.DownloadResult` thật — KHÔNG phải byte."""

    def __init__(self, doi, status_name, comment=None, path=None, size=None, api_status=None):
        self.doi = doi
        self.status = _FakeDownloadStatus(status_name)
        self.comment = comment
        self.path = path
        self.size = size
        self.api_status = api_status


class _FakeTDMClient:
    """Thay cho `wiley_tdm.TDMClient` thật — ghi lại lời gọi, không gọi mạng.

    Giống thư viện thật ở ba điểm mà bản giả cũ bỏ qua: dựng client là tạo thư mục
    tải, tải thành công là CÓ tệp trên đĩa, và `size` là KiB làm tròn."""

    dang_ky_goi_gan_nhat: Optional["_FakeTDMClient"] = None
    so_byte_moi_tep: int = 5000  # cố ý không chia hết cho 1024: 5000 byte, thư viện báo 5

    def __init__(self, api_token=None, download_dir="downloads"):
        if not api_token:
            raise ValueError("Token is required")
        self.api_token = api_token
        self._download_dir = Path(download_dir)
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self.api_rate_limit = 5.0
        self.skip_existing_files = True
        self.goi_download_pdf: List[str] = []
        self.goi_download_pdfs: List[List[str]] = []
        self.ket_qua_tho: List[_FakeDownloadResult] = []
        _FakeTDMClient.dang_ky_goi_gan_nhat = self

    @property
    def download_dir(self):
        return self._download_dir

    def _tai_mot_bai(self, doi):
        tep = _ghi_tep_pdf_gia(
            self._download_dir / (doi.replace("/", "-") + ".pdf"), self.so_byte_moi_tep)
        kq = _FakeDownloadResult(doi, "SUCCESS", path=tep, size=_kib_nhu_thu_vien(tep))
        self.ket_qua_tho.append(kq)
        return kq

    def download_pdf(self, doi):
        self.goi_download_pdf.append(doi)
        return self._tai_mot_bai(doi)

    def download_pdfs(self, dois, on_result=None):
        self.goi_download_pdfs.append(list(dois))
        out = []
        for doi in dois:
            r = self._tai_mot_bai(doi)
            if on_result:
                on_result(r)
            out.append(r)
        return out


@pytest.fixture
def _wiley_tdm_gia(monkeypatch):
    """Cấy module `wiley_tdm` GIẢ vào `sys.modules`, để `from wiley_tdm import
    TDMClient` trong `WileyTdmClient.__init__` nhận bản giả này — không đụng
    thư viện thật (nếu có) và không cần thư viện phải được cài trong venv chạy
    test này."""
    fake_module = types.ModuleType("wiley_tdm")
    fake_module.TDMClient = _FakeTDMClient
    monkeypatch.setitem(sys.modules, "wiley_tdm", fake_module)
    _FakeTDMClient.dang_ky_goi_gan_nhat = None
    yield fake_module


def _bat_wiley(monkeypatch, token: str = "FAKE-TOKEN-UUID") -> None:
    monkeypatch.setattr(settings, "enable_wiley_tdm", True)
    monkeypatch.setattr(settings, "wiley_tdm_api_token", token)


# ════════════════════════════════════════════════════════════════════════════
# Fail-closed: thiếu cờ bật / thiếu token / thiếu thư viện phải NỔ TO
# ════════════════════════════════════════════════════════════════════════════

def test_wiley_tdm_raises_when_flag_not_enabled():
    from app.sources.wiley_tdm import WileyTdmClient
    with pytest.raises(RuntimeError, match="ENABLE_WILEY_TDM"):
        WileyTdmClient()


def test_wiley_tdm_raises_when_token_missing(monkeypatch):
    monkeypatch.setattr(settings, "enable_wiley_tdm", True)
    from app.sources.wiley_tdm import WileyTdmClient
    with pytest.raises(RuntimeError, match="WILEY_TDM_API_TOKEN"):
        WileyTdmClient()


def test_wiley_tdm_raises_clear_error_when_library_missing(monkeypatch):
    """Thư viện `wiley-tdm` chưa cài -> lỗi TIẾNG VIỆT rõ ràng, không phải để
    lọt ModuleNotFoundError tiếng Anh mù mờ của thư viện gốc ra ngoài."""
    _bat_wiley(monkeypatch)
    monkeypatch.setitem(sys.modules, "wiley_tdm", None)  # ép import thất bại
    from app.sources.wiley_tdm import WileyTdmClient
    with pytest.raises(RuntimeError, match="wiley-tdm"):
        WileyTdmClient()


# ════════════════════════════════════════════════════════════════════════════
# Dựng client thành công -> truyền đúng cấu hình cho TDMClient bên dưới
# ════════════════════════════════════════════════════════════════════════════

def test_wiley_tdm_builds_underlying_client_with_token_and_rate_limit(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch, token="REAL-TOKEN-UUID")
    monkeypatch.setattr(settings, "wiley_tdm_rate_limit_seconds", 12.5)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    inner = _FakeTDMClient.dang_ky_goi_gan_nhat
    assert inner.api_token == "REAL-TOKEN-UUID"
    assert inner.api_rate_limit == 12.5
    assert client.download_dir == inner.download_dir


def test_wiley_tdm_default_download_dir_when_not_configured(monkeypatch, _wiley_tdm_gia):
    """Không cấu hình gì -> đúng hằng `THU_MUC_TAI_MAC_DINH`, tương đối so với thư mục đang
    đứng. Tên này có luật riêng trong `.gitignore` (canh ở
    tests/test_toan_van_khong_lot_vao_git_20260930.py): đổi tên thì đổi cả hai."""
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    WileyTdmClient()
    inner = _FakeTDMClient.dang_ky_goi_gan_nhat
    assert inner.download_dir.as_posix() == THU_MUC_TAI_MAC_DINH
    assert not inner.download_dir.is_absolute()
    assert THU_MUC_TAI_MAC_DINH == "downloads_wiley_tdm"


def test_wiley_tdm_custom_download_dir_from_settings(monkeypatch, _wiley_tdm_gia, tmp_path):
    _bat_wiley(monkeypatch)
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", str(tmp_path / "pdfs"))
    from app.sources.wiley_tdm import WileyTdmClient
    WileyTdmClient()
    inner = _FakeTDMClient.dang_ky_goi_gan_nhat
    assert inner.download_dir == tmp_path / "pdfs"


def test_wiley_tdm_explicit_download_dir_argument_overrides_settings(monkeypatch, _wiley_tdm_gia, tmp_path):
    _bat_wiley(monkeypatch)
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", str(tmp_path / "tu_settings"))
    from app.sources.wiley_tdm import WileyTdmClient
    WileyTdmClient(download_dir=str(tmp_path / "tu_tham_so"))
    inner = _FakeTDMClient.dang_ky_goi_gan_nhat
    assert inner.download_dir == tmp_path / "tu_tham_so"


# ════════════════════════════════════════════════════════════════════════════
# Tải MỘT bài — quy đổi kết quả đúng, không bịa khi thất bại
# ════════════════════════════════════════════════════════════════════════════

_CANH_BAO_KHONG_DO_DUOC = "không đo được kích thước tệp"


def test_download_pdf_success_returns_thanh_cong_true(monkeypatch, _wiley_tdm_gia, caplog):
    _bat_wiley(monkeypatch)
    caplog.set_level("WARNING")
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/example.doi")
    assert kq.doi == "10.1002/example.doi"
    assert kq.trang_thai == "SUCCESS"
    assert kq.thanh_cong is True
    assert Path(kq.duong_dan).as_posix() == f"{THU_MUC_TAI_MAC_DINH}/10.1002-example.doi.pdf"
    tho = _FakeTDMClient.dang_ky_goi_gan_nhat.ket_qua_tho[-1]
    assert tho.size == 5, "bản giả phải báo KiB như thư viện thật thì ca này mới có nghĩa"
    assert kq.kich_thuoc_byte == 5000 == Path(kq.duong_dan).stat().st_size
    assert _CANH_BAO_KHONG_DO_DUOC not in caplog.text, "đo được thì không cảnh báo"


def test_download_pdf_access_denied_is_reported_not_hidden(monkeypatch, _wiley_tdm_gia, caplog):
    """Đúng giới hạn IP-based đã ghi ở docstring module — ACCESS_DENIED phải
    hiện nguyên trạng thái thật, KHÔNG bị nuốt thành lỗi chung chung."""
    _bat_wiley(monkeypatch)
    caplog.set_level("WARNING")

    def _tra_ve_tu_choi(self, doi):
        return _FakeDownloadResult(doi, "ACCESS_DENIED", comment="Not entitled", api_status=403)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve_tu_choi)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/khong-open-access")
    assert kq.thanh_cong is False
    assert kq.trang_thai == "ACCESS_DENIED"
    assert kq.ghi_chu == "Not entitled"
    assert kq.ma_http == 403
    assert kq.duong_dan is None
    assert kq.kich_thuoc_byte is None
    assert "tải thất bại" in caplog.text
    assert _CANH_BAO_KHONG_DO_DUOC not in caplog.text, "tải thất bại thì không có tệp nào để đo"


def test_download_pdf_existing_file_counts_as_success(monkeypatch, _wiley_tdm_gia, tmp_path):
    """`EXISTING_FILE`: thư viện thật trả `DownloadResult(doi, EXISTING_FILE, "", path)`, KHÔNG
    có `size`. Tệp vẫn nằm trên đĩa nên `kich_thuoc_byte` là byte thật của nó, không phải None."""
    _bat_wiley(monkeypatch)
    tep = _ghi_tep_pdf_gia(tmp_path / "da_co" / "10.1002-da-co-san.pdf", 7777)

    def _tra_ve_da_co(self, doi):
        return _FakeDownloadResult(doi, "EXISTING_FILE", comment="", path=tep)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve_da_co)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/da-co-san")
    assert kq.thanh_cong is True
    assert kq.trang_thai == "EXISTING_FILE"
    assert kq.kich_thuoc_byte == 7777


def test_download_pdf_unknown_doi_is_not_treated_as_success(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)

    def _tra_ve_khong_biet(self, doi):
        return _FakeDownloadResult(doi, "UNKNOWN_DOI")

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve_khong_biet)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.9999/khong-ton-tai")
    assert kq.thanh_cong is False
    assert kq.trang_thai == "UNKNOWN_DOI"
    assert kq.kich_thuoc_byte is None


# ════════════════════════════════════════════════════════════════════════════
# `kich_thuoc_byte` là BYTE THẬT đo trên đĩa — vá 30/09/2026
# ════════════════════════════════════════════════════════════════════════════

def test_kich_thuoc_byte_la_byte_that_khong_phai_kib_cua_thu_vien(monkeypatch, _wiley_tdm_gia):
    """Tái hiện đúng hai con số đo thật: tệp 8.913.789 byte, thư viện báo 8705. Trước bản
    vá trường `kich_thuoc_byte` mang 8705; nhân lại 1024 cũng chỉ ra 8.913.920."""
    _bat_wiley(monkeypatch)
    monkeypatch.setattr(_FakeTDMClient, "so_byte_moi_tep", _SO_BYTE_DO_THAT)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/jcsm.70385")
    tho = _FakeTDMClient.dang_ky_goi_gan_nhat.ket_qua_tho[-1]
    assert tho.size == _SO_KIB_THU_VIEN_BAO
    assert kq.kich_thuoc_byte == _SO_BYTE_DO_THAT
    assert kq.kich_thuoc_byte == Path(kq.duong_dan).stat().st_size
    assert kq.kich_thuoc_byte != tho.size * 1024


def test_storage_error_khong_bao_kich_thuoc_cua_tep_ghi_do(monkeypatch, _wiley_tdm_gia, tmp_path):
    """`STORAGE_ERROR` để lại tệp ghi dở trên đĩa: kích thước tệp dở KHÔNG phải kích thước
    PDF đã tải, nên không được báo ra như thể tải xong."""
    _bat_wiley(monkeypatch)
    tep_do = _ghi_tep_pdf_gia(tmp_path / "do" / "10.1002-ghi-do.pdf", 321, tron_ven=False)

    def _loi_luu(self, doi):
        return _FakeDownloadResult(
            doi, "STORAGE_ERROR", comment="No space left on device", path=tep_do)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _loi_luu)
    from app.sources.wiley_tdm import WileyTdmClient
    kq = WileyTdmClient().download_pdf("10.1002/ghi-do")
    assert tep_do.stat().st_size == 321, "tệp dở phải có thật thì ca này mới có nghĩa"
    assert kq.thanh_cong is False
    assert kq.trang_thai == "STORAGE_ERROR"
    assert Path(kq.duong_dan) == tep_do
    assert kq.kich_thuoc_byte is None
    # Lời của thư viện được giữ nguyên, kèm chỉ dẫn về tệp dở mà lượt tải sau sẽ vấp phải.
    assert "No space left on device" in kq.ghi_chu
    assert "ghi dở" in kq.ghi_chu and tep_do.name in kq.ghi_chu


def test_storage_error_khong_de_lai_tep_thi_giu_nguyen_loi_cua_thu_vien(monkeypatch, _wiley_tdm_gia, tmp_path):
    """Lỗi ghi mà KHÔNG có tệp nào nằm lại (vd không mở được tệp để ghi): không có tệp dở để báo."""
    _bat_wiley(monkeypatch)
    khong_co = tmp_path / "do" / "10.1002-khong-mo-duoc.pdf"

    def _loi_luu(self, doi):
        return _FakeDownloadResult(doi, "STORAGE_ERROR", comment="Permission denied", path=khong_co)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _loi_luu)
    from app.sources.wiley_tdm import WileyTdmClient
    kq = WileyTdmClient().download_pdf("10.1002/khong-mo-duoc")
    assert (kq.trang_thai, kq.thanh_cong, kq.kich_thuoc_byte) == ("STORAGE_ERROR", False, None)
    assert kq.ghi_chu == "Permission denied"


@pytest.mark.parametrize("kieu", ["khong_ton_tai", "la_thu_muc", "khong_co_duong_dan"])
def test_thanh_cong_ma_khong_do_duoc_tep_thi_none_khong_lay_so_kib(
        monkeypatch, _wiley_tdm_gia, tmp_path, caplog, kieu):
    """Không đo được thì nói «không biết» (None) — không lấy số KiB của thư viện đắp vào — và
    để lại một dòng cảnh báo: «tải thành công» mà không thấy tệp là chuyện bất thường."""
    _bat_wiley(monkeypatch)
    caplog.set_level("WARNING")
    duong = {"khong_ton_tai": tmp_path / "khong-co.pdf", "la_thu_muc": tmp_path, "khong_co_duong_dan": None}[kieu]

    def _tra_ve(self, doi):
        return _FakeDownloadResult(doi, "SUCCESS", path=duong, size=_SO_KIB_THU_VIEN_BAO)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve)
    from app.sources.wiley_tdm import WileyTdmClient
    kq = WileyTdmClient().download_pdf("10.1002/khong-do-duoc")
    assert kq.thanh_cong is True
    assert kq.kich_thuoc_byte is None
    assert _CANH_BAO_KHONG_DO_DUOC in caplog.text


def test_thu_vien_wiley_that_bao_kib_con_ket_qua_cua_ta_la_byte(tmp_path):
    """Hợp đồng với thư viện THẬT, không mạng: `FileUtils.save_file` trả KiB làm tròn, và
    `_quy_doi_ket_qua` đổi đúng kết quả đó thành byte thật. Ca này giữ cho bản giả ở trên
    không tự bịa ra một hợp đồng khác với thư viện (lỗi đơn vị lọt từ 23/09 vì thế)."""
    pytest.importorskip("wiley_tdm")
    from wiley_tdm.download_result import DownloadResult
    from wiley_tdm.download_status import DownloadStatus
    from wiley_tdm.file_utils import FileUtils

    from app.sources.wiley_tdm import _quy_doi_ket_qua

    noi_dung = _noi_dung_pdf_gia(5000)

    class _PhanHoi:
        def iter_content(self, chunk_size=8192):
            yield noi_dung[:3000]
            yield noi_dung[3000:]

    doi = "10.1002/jcsm.70385"
    tep = FileUtils.to_file_path(tmp_path, doi, "pdf")
    kib = FileUtils.save_file(_PhanHoi(), tep)
    assert tep.name == "10.1002-jcsm.70385.pdf"
    assert tep.stat().st_size == 5000
    assert kib == 5, "thư viện đổi đơn vị của `size`: soát lại `_kich_thuoc_byte_tren_dia` và bản giả"
    kq = _quy_doi_ket_qua(DownloadResult(doi, DownloadStatus.SUCCESS, "", tep, kib))
    assert kq.thanh_cong is True
    assert kq.kich_thuoc_byte == 5000
    da_co = _quy_doi_ket_qua(DownloadResult(doi, DownloadStatus.EXISTING_FILE, "", tep))
    assert da_co.thanh_cong is True
    assert da_co.kich_thuoc_byte == 5000


# ════════════════════════════════════════════════════════════════════════════
# Tệp ghi dở không được báo «thành công» — vá 30/09/2026
# ════════════════════════════════════════════════════════════════════════════

# Phần mở đầu của một PDF tuyến tính hoá (linearized), dựng theo đúng hình đo được trên 4 tệp thật
# ngày 30/09/2026: ngay sau bảng tham chiếu trang đầu là «startxref 0 %%EOF», ở byte 450–1364 —
# tức có một dấu «%%EOF» nằm gần ĐẦU tệp. Nội dung tự chế.
_MO_DAU_TUYEN_TINH = (
    b"%PDF-1.6\r%\xe2\xe3\xcf\xd3\r\n1 0 obj\r<</Linearized 1/L 20000/O 3/E 5000/N 1/T 19000/H [ 450 150]>>\rendobj\r\n"
    b"xref\r\n1 2\r\n0000000016 00000 n\r\n0000000600 00000 n\r\n"
    b"trailer\r\n<</Size 3/Prev 19000/Root 2 0 R>>\r\nstartxref\r\n0\r\n%%EOF\r\n"
)
_DUOI_TUYEN_TINH = b"\r\nstartxref\r\n116\r\n%%EOF\r\n"

_CAC_TEP_MAU = {
    # tên ca: (nội dung, mảnh phải có trong lý do — None nghĩa là «trông trọn vẹn»)
    "tron_ven": (_noi_dung_pdf_gia(5000), None),
    "tron_ven_nho_hon_cua_so": (_noi_dung_pdf_gia(64), None),
    "tron_ven_startxref_10": (_DAU_PDF + b"x" * 200 + b"\nstartxref\n10\n%%EOF\n", None),
    "tron_ven_khong_co_startxref": (_DAU_PDF + b"x" * 200 + b"\n%%EOF\n", None),
    "rac_ngan_sau_eof": (_noi_dung_pdf_gia(5000) + b"\n" * 900, None),
    "rac_ngan_truoc_chu_ky": (b"\xef\xbb\xbf\r\n" + _noi_dung_pdf_gia(5000), None),
    "tuyen_tinh_tron_ven": (_MO_DAU_TUYEN_TINH + b"x" * 5000 + _DUOI_TUYEN_TINH, None),
    "tuyen_tinh_tron_ven_nho_hon_cua_so": (_MO_DAU_TUYEN_TINH + b"x" * 100 + _DUOI_TUYEN_TINH, None),
    "rong": (b"", "rỗng"),
    "cut_giua_chung": (_noi_dung_pdf_gia(5000, tron_ven=False), "%%EOF"),
    "cut_ngay_sau_chu_ky": (b"%PDF-1.7\n", "%%EOF"),
    "khong_phai_pdf": (b"<html><body>Service temporarily unavailable</body></html>\n%%EOF\n", "%PDF-"),
    "chu_ky_nam_qua_sau": (b"\0" * 1500 + _noi_dung_pdf_gia(5000), "%PDF-"),
    "rac_dai_sau_eof": (_noi_dung_pdf_gia(5000) + b"\n" * 1100, "%%EOF"),
    "tuyen_tinh_cut_ngay_sau_phan_mo_dau": (_MO_DAU_TUYEN_TINH + b"x" * 300, "startxref 0"),
    "tuyen_tinh_cut_dung_o_phan_mo_dau": (_MO_DAU_TUYEN_TINH, "startxref 0"),
    "tuyen_tinh_cut_xa_phan_mo_dau": (_MO_DAU_TUYEN_TINH + b"x" * 5000, "%%EOF"),
}


@pytest.mark.parametrize("ten_ca", sorted(_CAC_TEP_MAU))
def test_ly_do_pdf_ghi_do_tren_tung_hinh_tep(tmp_path, ten_ca):
    """Phép kiểm cấu trúc hai đầu tệp: tệp trọn vẹn không bị bắt nhầm, tệp cụt và tệp không phải
    PDF đều bị bắt kèm đúng lý do."""
    from app.sources.wiley_tdm import _ly_do_pdf_ghi_do
    noi_dung, manh_ly_do = _CAC_TEP_MAU[ten_ca]
    tep = tmp_path / "10.1002-mau.pdf"
    tep.write_bytes(noi_dung)
    ly_do = _ly_do_pdf_ghi_do(tep)
    if manh_ly_do is None:
        assert ly_do is None, f"tệp trọn vẹn bị coi là ghi dở: {ly_do}"
    else:
        assert ly_do is not None, "tệp cụt hoặc không phải PDF lại được coi là trọn vẹn"
        assert manh_ly_do in ly_do


def test_ly_do_pdf_ghi_do_nhan_ca_duong_dan_dang_chuoi(tmp_path):
    from app.sources.wiley_tdm import _ly_do_pdf_ghi_do
    tep = _ghi_tep_pdf_gia(tmp_path / "10.1002-cut.pdf", 5000, tron_ven=False)
    assert "%%EOF" in _ly_do_pdf_ghi_do(str(tep))


@pytest.mark.parametrize("kieu", ["khong_ton_tai", "la_thu_muc", "khong_co_duong_dan"])
def test_ly_do_pdf_ghi_do_khong_xet_duoc_thi_khong_ket_luan(tmp_path, kieu):
    """Không có tệp để xét thì không kết luận «ghi dở» (đường «thành công mà không thấy tệp» đã có
    cảnh báo riêng ở `_quy_doi_ket_qua`)."""
    from app.sources.wiley_tdm import _ly_do_pdf_ghi_do
    duong = {"khong_ton_tai": tmp_path / "khong-co.pdf", "la_thu_muc": tmp_path, "khong_co_duong_dan": None}[kieu]
    assert _ly_do_pdf_ghi_do(duong) is None


def test_existing_file_la_tep_ghi_do_thi_khong_thanh_cong(monkeypatch, _wiley_tdm_gia, tmp_path, caplog):
    """Đo 30/09/2026: sau một lượt đứt mạng, thư viện trả `EXISTING_FILE` cho tệp 4.009 byte mà
    không gọi mạng. Trước bản vá, đó là `thanh_cong=True` kèm `kich_thuoc_byte=4009`."""
    _bat_wiley(monkeypatch)
    caplog.set_level("WARNING")
    tep_do = _ghi_tep_pdf_gia(tmp_path / "da_co" / "10.1002-cut.pdf", 4009, tron_ven=False)

    def _tra_ve_da_co(self, doi):
        return _FakeDownloadResult(doi, "EXISTING_FILE", comment="", path=tep_do)

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve_da_co)
    from app.sources.wiley_tdm import WileyTdmClient
    kq = WileyTdmClient().download_pdf("10.1002/cut")
    assert kq.trang_thai == "EXISTING_FILE", "trạng thái của thư viện được giữ nguyên"
    assert kq.thanh_cong is False
    assert kq.kich_thuoc_byte is None, "kích thước tệp dở không phải kích thước PDF đã tải"
    assert "ghi dở" in kq.ghi_chu and "%%EOF" in kq.ghi_chu and tep_do.name in kq.ghi_chu
    assert "Xoá tệp đó rồi tải lại" in kq.ghi_chu
    assert "tải thất bại" in caplog.text
    assert _CANH_BAO_KHONG_DO_DUOC not in caplog.text, "đây là «tệp dở», không phải «không đo được»"
    assert tep_do.stat().st_size == 4009, "connector không tự xoá tệp"


def test_download_pdfs_va_callback_cung_bat_tep_ghi_do(monkeypatch, _wiley_tdm_gia):
    """Tải hàng loạt và callback đi qua cùng phép quy đổi: tệp dở của MỘT bài không kéo bài khác
    xuống, và cũng không được bài khác che."""
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    _ghi_tep_pdf_gia(Path(THU_MUC_TAI_MAC_DINH) / "10.1002-cut.pdf", 4009, tron_ven=False)

    def _tai(self, doi):
        """Như thư viện thật: tệp đã có trên đĩa thì trả `EXISTING_FILE`, không tải lại."""
        tep = self._download_dir / (doi.replace("/", "-") + ".pdf")
        if tep.exists():
            return _FakeDownloadResult(doi, "EXISTING_FILE", comment="", path=tep)
        return self._tai_mot_bai(doi)

    def _tai_loat(self, dois, on_result=None):
        ket_qua_tho = []
        for doi in dois:
            mot = _tai(self, doi)
            ket_qua_tho.append(mot)
            if on_result:
                on_result(mot)
        return ket_qua_tho

    monkeypatch.setattr(_FakeTDMClient, "download_pdfs", _tai_loat)
    nhan_duoc = []
    ket_qua = client.download_pdfs(["10.1002/tot", "10.1002/cut"], on_result=nhan_duoc.append)
    for loat in (ket_qua, nhan_duoc):
        assert [(k.doi, k.trang_thai, k.thanh_cong, k.kich_thuoc_byte) for k in loat] == [
            ("10.1002/tot", "SUCCESS", True, 5000), ("10.1002/cut", "EXISTING_FILE", False, None)]


def test_cmd_test_live_wiley_tdm_in_byte_that_tren_dia(monkeypatch, _wiley_tdm_gia):
    """`python run.py wiley-tdm-test <DOI>` in đúng byte của tệp vừa tải, không phải KiB."""
    _bat_wiley(monkeypatch)
    monkeypatch.setattr(_FakeTDMClient, "so_byte_moi_tep", _SO_BYTE_DO_THAT)
    from app.main import cmd_test_live_wiley_tdm
    out = cmd_test_live_wiley_tdm("10.1002/jcsm.70385")
    assert out["trang_thai"] == "SUCCESS"
    assert out["thanh_cong"] is True
    assert out["kich_thuoc_byte"] == _SO_BYTE_DO_THAT
    assert Path(out["duong_dan"]).stat().st_size == out["kich_thuoc_byte"]
    assert Path(out["duong_dan"]).as_posix() == f"{THU_MUC_TAI_MAC_DINH}/10.1002-jcsm.70385.pdf"
    assert Path(out["thu_muc_tai"]).as_posix() == THU_MUC_TAI_MAC_DINH


# ════════════════════════════════════════════════════════════════════════════
# Tải hàng loạt — callback nhận đúng kiểu đã Việt hoá, không phải kiểu gốc
# ════════════════════════════════════════════════════════════════════════════

def test_download_pdfs_batch_calls_underlying_client_with_full_list(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    dois = ["10.1002/a", "10.1002/b", "10.1002/c"]
    ket_qua = client.download_pdfs(dois)
    assert [k.doi for k in ket_qua] == dois
    assert all(k.thanh_cong for k in ket_qua)
    assert _FakeTDMClient.dang_ky_goi_gan_nhat.goi_download_pdfs == [dois]


def test_download_pdfs_on_result_callback_receives_ket_qua_tai_wiley(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import KetQuaTaiWiley, WileyTdmClient
    client = WileyTdmClient()
    nhan_duoc = []
    client.download_pdfs(["10.1002/x"], on_result=nhan_duoc.append)
    assert len(nhan_duoc) == 1
    assert isinstance(nhan_duoc[0], KetQuaTaiWiley)
    assert nhan_duoc[0].doi == "10.1002/x"


def test_download_pdfs_va_callback_cung_bao_byte_that(monkeypatch, _wiley_tdm_gia):
    """Đường tải hàng loạt và callback đi qua cùng một phép quy đổi: cũng phải ra byte thật."""
    _bat_wiley(monkeypatch)
    monkeypatch.setattr(_FakeTDMClient, "so_byte_moi_tep", 3000)  # thư viện báo round(3000/1024) = 3
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    nhan_duoc = []
    ket_qua = client.download_pdfs(["10.1002/a", "10.1002/b"], on_result=nhan_duoc.append)
    assert [r.size for r in _FakeTDMClient.dang_ky_goi_gan_nhat.ket_qua_tho] == [3, 3]
    assert [k.kich_thuoc_byte for k in ket_qua] == [3000, 3000]
    assert [k.kich_thuoc_byte for k in nhan_duoc] == [3000, 3000]


def test_download_pdfs_without_callback_does_not_crash(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    ket_qua = client.download_pdfs(["10.1002/y"])
    assert len(ket_qua) == 1


# ════════════════════════════════════════════════════════════════════════════
# Không tham gia get_enabled_sources()/get_fallback_sources() — kiểm bằng quan
# sát trực tiếp mã nguồn, không suy đoán từ tài liệu.
# ════════════════════════════════════════════════════════════════════════════

def test_wiley_tdm_client_is_exported_but_not_a_discovery_source():
    from app.sources import WileyTdmClient, get_enabled_sources, get_fallback_sources
    assert WileyTdmClient is not None
    src_enabled = inspect.getsource(get_enabled_sources)
    src_fallback = inspect.getsource(get_fallback_sources)
    assert "WileyTdmClient" not in src_enabled
    assert "WileyTdmClient" not in src_fallback
