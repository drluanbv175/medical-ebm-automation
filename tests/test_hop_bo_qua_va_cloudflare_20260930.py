"""Hai bản vá 29/09 cùng sửa `summarize_source_health` phải chạy ĐƯỢC CÙNG NHAU (30/09/2026).

PR #47 (nguồn không hiểu thẻ trường PubMed thì bỏ qua truy vấn — dòng `skipped`, health `not_queried`) và PR #48
(Scopus bị Cloudflare chặn theo IP mạng ⇒ ghi chú thay vì PARTIAL) xung đột ở `app/services/ingestion.py`; bản gộp
giữ thay đổi của cả hai bên. Bộ test riêng của từng PR chỉ kiểm từng nửa — tệp này kiểm chỗ hai nửa CHẠM nhau trong
cùng một lượt quét. Offline hoàn toàn: chỉ dựng dòng Source Log, không mở socket.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ingestion import summarize_source_health  # noqa: E402
from app.sources.base import LY_DO_BO_QUA_CU_PHAP_PUBMED  # noqa: E402
from app.utils.http import DAU_CLOUDFLARE_CHAN  # noqa: E402

CF_403 = f"{DAU_CLOUDFLARE_CHAN} HTTPError: 403 Client Error: Forbidden for url: https://api.elsevier.com/x"
# Đúng thông điệp `_fetch` ghi cho một truy vấn bị bỏ qua có chủ đích.
BO_QUA = (f"{LY_DO_BO_QUA_CU_PHAP_PUBMED}: không gửi truy vấn tới nguồn không hiểu cú pháp này — "
          "bỏ qua có chủ đích, không phải lỗi")
API = ["pubmed", "europepmc", "crossref", "scopus"]


def _dong(nguon: str, trang_thai: str, so_dong: int, ban_ghi: int = 0, loi: str | None = None) -> list:
    return [{"source": nguon, "status": trang_thai, "record_count": ban_ghi, "error_message": loi}
            for _ in range(so_dong)]


def _suc_khoe(logs: list) -> dict:
    return summarize_source_health(logs, expected_api_sources=API, expected_feed_sources=[], safety_enabled=False)


def test_luot_tuan_vpn_bat_co_ca_bo_qua_lan_cloudflare_la_pass_kem_ghi_chu():
    """Lượt tuần khi VPN bật, sau khi có CẢ HAI bản vá: Europe PMC/Crossref/Scopus bỏ qua 8 truy vấn mang thẻ PubMed;
    3 truy vấn Scopus đã gửi đều nhận trang chặn Cloudflare (breaker cắt phần còn lại). Dòng bỏ qua không phải
    request nên không được làm lệch phép so «MỌI lỗi của Scopus là trang chặn Cloudflare»."""
    kq = _suc_khoe(_dong("pubmed", "ok", 53, 5)
                   + _dong("europepmc", "ok", 45, 5) + _dong("europepmc", "skipped", 8, loi=BO_QUA)
                   + _dong("crossref", "ok", 45, 5) + _dong("crossref", "skipped", 8, loi=BO_QUA)
                   + _dong("scopus", "skipped", 8, loi=BO_QUA) + _dong("scopus", "error", 3, loi=CF_403))
    assert kq["status"] == "PASS", kq["warnings"]
    assert kq["warnings"] == []
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" in kq["mirror_notices"]
    scopus = kq["sources"]["scopus"]
    assert (scopus["requests"], scopus["skipped"], scopus["error"], scopus["error_http_403_cloudflare"],
            scopus["health"]) == (3, 8, 3, 3, "unavailable")
    for ten in ("europepmc", "crossref"):
        hang = kq["sources"][ten]
        assert (hang["requests"], hang["skipped"], hang["health"]) == (45, 8, "ok")
    assert kq["optional_enhanced_failed"] == ["scopus"]           # sự thật «hỏng 100%» vẫn ghi
    assert kq["optional_enhanced_blocked_by_cloudflare"] == ["scopus"]


def test_co_dong_bo_qua_van_khong_mien_khi_scopus_lan_loi_khac_cloudflare():
    """Có dòng bỏ qua không được nới điều kiện miễn: Scopus lẫn một lỗi KHÔNG phải trang chặn Cloudflare (mất mạng)
    thì vẫn PARTIAL như khi chưa có dòng bỏ qua nào."""
    kq = _suc_khoe(_dong("pubmed", "ok", 53, 5)
                   + _dong("europepmc", "ok", 45, 5) + _dong("europepmc", "skipped", 8, loi=BO_QUA)
                   + _dong("crossref", "ok", 45, 5) + _dong("crossref", "skipped", 8, loi=BO_QUA)
                   + _dong("scopus", "skipped", 8, loi=BO_QUA) + _dong("scopus", "error", 2, loi=CF_403)
                   + _dong("scopus", "error", 1, loi="RuntimeError: Gọi API thất bại sau 4 lần: x"))
    scopus = kq["sources"]["scopus"]
    assert (scopus["error"], scopus["error_http_403_cloudflare"], scopus["skipped"]) == (3, 2, 8)
    assert kq["status"] == "PARTIAL"
    assert "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in kq["warnings"]
    assert kq["optional_enhanced_blocked_by_cloudflare"] == []
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" not in kq["mirror_notices"]


def test_nguon_loi_bi_bo_qua_sach_thi_khong_mien_cloudflare_va_mang_ca_hai_canh_bao():
    """Crossref bị bỏ qua SẠCH (`not_queried`) thì không còn «đủ ba nguồn lõi khoẻ»: Scopus bị Cloudflare chặn KHÔNG
    được miễn, và lượt mang CẢ HAI cảnh báo — khối của PR này không được nuốt khối của PR kia."""
    kq = _suc_khoe(_dong("pubmed", "ok", 5, 5) + _dong("europepmc", "ok", 5, 5)
                   + _dong("crossref", "skipped", 8, loi=BO_QUA) + _dong("scopus", "error", 3, loi=CF_403))
    assert kq["sources"]["crossref"]["health"] == "not_queried"
    assert kq["status"] == "PARTIAL"
    assert "REQUIRED_SOURCE_NOT_QUERIED:crossref" in kq["warnings"]
    assert "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in kq["warnings"]
    assert kq["optional_enhanced_blocked_by_cloudflare"] == []
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" not in kq["mirror_notices"]


def test_scopus_bi_bo_qua_sach_khong_phai_hong_cung_khong_phai_bi_cloudflare_chan():
    """Scopus chỉ có dòng bỏ qua (không gửi truy vấn nào): `not_queried` — không vào danh sách «hỏng 100%», không có
    ghi chú Cloudflare, không hạ trạng thái lượt (Scopus là nguồn tuỳ chọn)."""
    kq = _suc_khoe(_dong("pubmed", "ok", 5, 5) + _dong("europepmc", "ok", 5, 5) + _dong("crossref", "ok", 5, 5)
                   + _dong("scopus", "skipped", 8, loi=BO_QUA))
    assert kq["sources"]["scopus"]["health"] == "not_queried"
    assert kq["optional_enhanced_failed"] == [] and kq["optional_enhanced_blocked_by_cloudflare"] == []
    assert kq["status"] == "PASS", kq["warnings"]
    assert not any(n.startswith("SCOPUS_") for n in kq["mirror_notices"])
