"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng 5, task
#83) trong `app/sources/europepmc.py::EuropePMCClient.search()` — MỘT bản ghi hỏng
trong trang kết quả làm rớt CẢ TRANG.

CƠ CHẾ LỖI: bản gốc bọc CẢ vòng lặp phân tích bản ghi (`for r in
data.get("resultList", {}).get("result", [])`) vào CÙNG một `try/except Exception:
return []` với lệnh gọi mạng (`self.http.get_json(...)`). Nếu MỘT phần tử `r` trong
mảng kết quả không phải dict hợp lệ (vd `None` — có thật ở API bên ngoài khi trả về
dữ liệu không đồng nhất, hoặc lỗi parse JSON cục bộ), gọi `r.get(...)` ném
`AttributeError`, bay ra khỏi vòng lặp, bị khối `except` NGOÀI bắt và trả `[]` —
XOÁ SẠCH mọi bản ghi đã phân tích THÀNH CÔNG trước đó trong cùng trang, không chỉ
phần tử hỏng.

HẬU QUẢ KÉP: (1) mất dữ liệu — N-1 bản ghi hợp lệ bị vứt bỏ chỉ vì 1 bản ghi hỏng;
(2) báo động ẩn — `app/services/ingestion.py::_fetch()` đọc trạng thái nguồn qua bộ
đếm HTTP (`HttpClient.health_snapshot()`), và lệnh gọi mạng ĐÃ THÀNH CÔNG trước khi
vòng lặp phân tích mới hỏng, nên `_fetch()` vẫn ghi `status="ok"` dù `record_count=0`
— tầng giám sát sức khoẻ nguồn không thấy gì bất thường.

BẢN VÁ: tách khối try/except THÀNH HAI — một cho lệnh gọi mạng (giữ nguyên hành vi
cũ: lỗi mạng → trả `[]`), một RIÊNG cho từng bản ghi trong vòng lặp (lỗi 1 bản ghi →
bỏ qua đúng bản ghi đó, giữ các bản ghi khác).

Nguyên tắc viết test: mock `client.http.get_json` để trả về payload có XEN bản ghi
hỏng (`None`) giữa các bản ghi hợp lệ, gọi THẲNG `search()` thật, không grep chuỗi
trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.europepmc import EuropePMCClient  # noqa: E402


def _client(monkeypatch, response: dict):
    client = EuropePMCClient()
    client.use_mock = False
    monkeypatch.setattr(client.http, "get_json", lambda *a, **k: response)
    monkeypatch.setattr(client, "save_raw", lambda *a, **k: None)
    return client


_BAN_GHI_HOP_LE_1 = {
    "title": "Bài báo hợp lệ 1", "pubType": "journal article",
    "journalTitle": "J Test", "pmid": "111", "doi": "10.1/aaa",
}
_BAN_GHI_HOP_LE_2 = {
    "title": "Bài báo hợp lệ 2", "pubType": "journal article",
    "journalTitle": "J Test", "pmid": "222", "doi": "10.1/bbb",
}


class TestMotBanGhiHongKhongLamRotCaTrang:
    """★★★ Ca chính — trang kết quả có 1 bản ghi `None` xen giữa 2 bản ghi hợp lệ:
    CẢ HAI bản ghi hợp lệ phải được giữ lại, không bị vứt bỏ theo bản ghi hỏng."""

    def test_ban_ghi_none_xen_giua_khong_lam_mat_ban_ghi_hop_le(self, monkeypatch):
        client = _client(monkeypatch, {
            "resultList": {"result": [_BAN_GHI_HOP_LE_1, None, _BAN_GHI_HOP_LE_2]}
        })
        out = client.search("test query")
        pmids = {r.pmid for r in out}
        assert pmids == {"111", "222"}, (
            f"kỳ vọng giữ lại 2 bản ghi hợp lệ, chỉ mất bản ghi None — thực tế: {pmids}"
        )

    def test_ban_ghi_hong_o_dau_trang_khong_lam_mat_cac_ban_ghi_sau(self, monkeypatch):
        """Bản ghi hỏng đứng ĐẦU — kiểm tra cả trường hợp lỗi xảy ra SỚM trong vòng
        lặp, không chỉ ở giữa."""
        client = _client(monkeypatch, {
            "resultList": {"result": [None, _BAN_GHI_HOP_LE_1, _BAN_GHI_HOP_LE_2]}
        })
        out = client.search("test query")
        pmids = {r.pmid for r in out}
        assert pmids == {"111", "222"}

    def test_ban_ghi_hong_o_cuoi_trang_khong_lam_mat_cac_ban_ghi_truoc(self, monkeypatch):
        client = _client(monkeypatch, {
            "resultList": {"result": [_BAN_GHI_HOP_LE_1, _BAN_GHI_HOP_LE_2, None]}
        })
        out = client.search("test query")
        pmids = {r.pmid for r in out}
        assert pmids == {"111", "222"}


class TestKhongCoBanGhiHongVanDungNhuCu:
    """Đối chứng — trang kết quả TOÀN bản ghi hợp lệ vẫn hoạt động y hệt trước bản
    vá, không bị ảnh hưởng bởi việc thêm try/except cho từng bản ghi."""

    def test_toan_bo_ban_ghi_hop_le_deu_duoc_giu(self, monkeypatch):
        client = _client(monkeypatch, {
            "resultList": {"result": [_BAN_GHI_HOP_LE_1, _BAN_GHI_HOP_LE_2]}
        })
        out = client.search("test query")
        assert len(out) == 2
        assert {r.pmid for r in out} == {"111", "222"}


class TestLoiMangThatVanTraVeRong:
    """Đối chứng bắt buộc — lỗi MẠNG THẬT (không phải lỗi phân tích bản ghi) vẫn
    phải trả về `[]` như hành vi gốc, không bị đổi ngữ nghĩa."""

    def test_loi_mang_van_tra_ve_rong(self, monkeypatch):
        client = EuropePMCClient()
        client.use_mock = False

        def _boom(*a, **k):
            raise RuntimeError("network down")

        monkeypatch.setattr(client.http, "get_json", _boom)
        out = client.search("test query")
        assert out == []
