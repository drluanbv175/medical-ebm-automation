"""Kiểm connector Wiley TDM API — thêm 23/09/2026.

Tất cả test OFFLINE: thư viện `wiley_tdm` bị GIẢ LẬP qua `sys.modules` (một
`TDMClient` giả ghi lại lời gọi thay vì gọi mạng Wiley thật) — không phụ thuộc
việc `wiley-tdm` có được cài trong venv chạy test hay không, và không bao giờ
gọi mạng thật, đúng quy ước `tests/test_scopus.py`.
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


@pytest.fixture(autouse=True)
def _don_cau_hinh_wiley(monkeypatch):
    """Cô lập cấu hình Wiley TDM khỏi .env thật của máy đang chạy test — mỗi
    test tự đặt giá trị nó cần, không phụ thuộc môi trường ngoài."""
    monkeypatch.setattr(settings, "enable_wiley_tdm", False)
    monkeypatch.setattr(settings, "wiley_tdm_api_token", "")
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", "")
    monkeypatch.setattr(settings, "wiley_tdm_rate_limit_seconds", 10.0)
    yield


class _FakeDownloadStatus:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeDownloadResult:
    def __init__(self, doi, status_name, comment=None, path=None, size=None, api_status=None):
        self.doi = doi
        self.status = _FakeDownloadStatus(status_name)
        self.comment = comment
        self.path = path
        self.size = size
        self.api_status = api_status


class _FakeTDMClient:
    """Thay cho `wiley_tdm.TDMClient` thật — ghi lại lời gọi, không gọi mạng."""

    dang_ky_goi_gan_nhat: Optional["_FakeTDMClient"] = None

    def __init__(self, api_token=None, download_dir="downloads"):
        if not api_token:
            raise ValueError("Token is required")
        self.api_token = api_token
        self._download_dir = Path(download_dir)
        self.api_rate_limit = 5.0
        self.skip_existing_files = True
        self.goi_download_pdf: List[str] = []
        self.goi_download_pdfs: List[List[str]] = []
        _FakeTDMClient.dang_ky_goi_gan_nhat = self

    @property
    def download_dir(self):
        return self._download_dir

    def download_pdf(self, doi):
        self.goi_download_pdf.append(doi)
        return _FakeDownloadResult(
            doi, "SUCCESS", path=self._download_dir / f"{doi}.pdf", size=1234)

    def download_pdfs(self, dois, on_result=None):
        self.goi_download_pdfs.append(list(dois))
        out = []
        for doi in dois:
            r = _FakeDownloadResult(doi, "SUCCESS", path=self._download_dir / f"{doi}.pdf", size=1)
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
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    WileyTdmClient()
    inner = _FakeTDMClient.dang_ky_goi_gan_nhat
    assert str(inner.download_dir) == "downloads_wiley_tdm"


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

def test_download_pdf_success_returns_thanh_cong_true(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/example.doi")
    assert kq.doi == "10.1002/example.doi"
    assert kq.trang_thai == "SUCCESS"
    assert kq.thanh_cong is True
    assert kq.duong_dan is not None
    assert kq.kich_thuoc_byte == 1234


def test_download_pdf_access_denied_is_reported_not_hidden(monkeypatch, _wiley_tdm_gia):
    """Đúng giới hạn IP-based đã ghi ở docstring module — ACCESS_DENIED phải
    hiện nguyên trạng thái thật, KHÔNG bị nuốt thành lỗi chung chung."""
    _bat_wiley(monkeypatch)

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


def test_download_pdf_existing_file_counts_as_success(monkeypatch, _wiley_tdm_gia):
    _bat_wiley(monkeypatch)

    def _tra_ve_da_co(self, doi):
        return _FakeDownloadResult(
            doi, "EXISTING_FILE", path=Path("downloads_wiley_tdm") / f"{doi}.pdf")

    monkeypatch.setattr(_FakeTDMClient, "download_pdf", _tra_ve_da_co)
    from app.sources.wiley_tdm import WileyTdmClient
    client = WileyTdmClient()
    kq = client.download_pdf("10.1002/da-co-san")
    assert kq.thanh_cong is True
    assert kq.trang_thai == "EXISTING_FILE"


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
