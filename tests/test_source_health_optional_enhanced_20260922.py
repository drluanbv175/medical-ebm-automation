"""Vá 22/09/2026 — theo đề nghị "hoàn thiện hệ thống nguồn" của bác sĩ.

`summarize_source_health()` chỉ tính hard-fail/warning cho 3 nguồn lõi (_DISCOVERY_CORE =
{pubmed, europepmc, crossref}). Nhưng Scopus/CORE/Epistemonikos CÓ trong get_enabled_sources()
khi bật cờ — ingest_all() THẬT SỰ gọi chúng mỗi lượt live-update, nên source_rows ghi nhận đúng
sức khoẻ. Trước bản vá: một trong ba nguồn này hỏng 100% (health='unavailable', vd hết quota/sai
key/Cloudflare chặn) không đổi `status` tổng — pipeline vẫn báo PASS dù một nguồn đang bật đã
câm hoàn toàn suốt lượt quét. Nay hạ `status` xuống tối đa "PARTIAL" (cảnh báo, KHÔNG chặn —
đây là nguồn TĂNG CƯỜNG tuỳ chọn, không phải nguồn lõi bắt buộc).
"""
from __future__ import annotations

from app.services.ingestion import summarize_source_health


def _log(source: str, status: str, records: int) -> dict:
    return {"source": source, "status": status, "record_count": records}


def _log_loi_lien_tuc(source: str, so_lan: int) -> list[dict]:
    return [_log(source, "error", 0) for _ in range(so_lan)]


def test_scopus_hong_100_phan_tram_khong_con_pass_im_lang():
    logs = (
        [_log("pubmed", "ok", 10), _log("europepmc", "ok", 10), _log("crossref", "ok", 10)]
        + _log_loi_lien_tuc("scopus", 5)
    )
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref", "scopus"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["sources"]["scopus"]["health"] == "unavailable"
    assert health["status"] == "PARTIAL", "trước đây vẫn PASS dù nguồn đang bật hỏng 100%"
    assert health["optional_enhanced_failed"] == ["scopus"]
    assert any(w.startswith("OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:") for w in health["warnings"])
    assert "scopus" in next(w for w in health["warnings"]
                            if w.startswith("OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:"))


def test_core_hong_100_phan_tram_cung_bi_bat():
    logs = (
        [_log("pubmed", "ok", 10), _log("europepmc", "ok", 10), _log("crossref", "ok", 10)]
        + _log_loi_lien_tuc("core", 3)
    )
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref", "core"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["optional_enhanced_failed"] == ["core"]
    assert health["status"] == "PARTIAL"


def test_khong_bi_nhac_ten_khi_nguon_khong_duoc_goi_lan_nao():
    """Khác «hỏng» — máy CHƯA BẬT Scopus thì `source_rows` không có mục 'scopus' nào cả. Đây
    KHÔNG được tính là «hỏng» — im lặng vì chưa bật khác hẳn im lặng vì hỏng (BH08)."""
    logs = [_log("pubmed", "ok", 10), _log("europepmc", "ok", 10), _log("crossref", "ok", 10)]
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["optional_enhanced_failed"] == []
    assert health["status"] == "PASS"


def test_scopus_hong_mot_phan_khong_bi_tinh_la_unavailable():
    """health='degraded' (một phần lỗi, không phải 100%) KHÔNG rơi vào optional_enhanced_failed —
    chỉ health='unavailable' (live_success == 0, tức HOÀN TOÀN không có phản hồi thành công nào)
    mới bị tính, khớp định nghĩa 'hỏng 100%' đã nêu trong docstring _OPTIONAL_ENHANCED."""
    logs = (
        [_log("pubmed", "ok", 10), _log("europepmc", "ok", 10), _log("crossref", "ok", 10)]
        + [_log("scopus", "ok", 2)] + _log_loi_lien_tuc("scopus", 1)  # error_rate thấp -> "ok", không degraded
    )
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref", "scopus"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["sources"]["scopus"]["health"] != "unavailable"
    assert health["optional_enhanced_failed"] == []


def test_nhieu_nguon_tang_cuong_hong_cung_luc_deu_duoc_liet_ke():
    logs = (
        [_log("pubmed", "ok", 10), _log("europepmc", "ok", 10), _log("crossref", "ok", 10)]
        + _log_loi_lien_tuc("scopus", 3) + _log_loi_lien_tuc("core", 3)
        + _log_loi_lien_tuc("epistemonikos", 3)
    )
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref", "scopus", "core", "epistemonikos"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["optional_enhanced_failed"] == ["core", "epistemonikos", "scopus"]  # sắp xếp theo bảng chữ cái


def test_hard_fail_that_su_van_uu_tien_hon_canh_bao_tang_cuong():
    """Nguồn lõi mất hết mirror (FAIL thật) + nguồn tăng cường cũng hỏng: overall PHẢI là FAIL,
    không bị 'PARTIAL' của optional_enhanced_failed che mất mức độ nghiêm trọng thật."""
    logs = (
        [_log("pubmed", "error", 0), _log("europepmc", "error", 0), _log("crossref", "ok", 10)]
        + _log_loi_lien_tuc("scopus", 3)
    )
    health = summarize_source_health(
        logs, expected_api_sources=["pubmed", "europepmc", "crossref", "scopus"],
        expected_feed_sources=[], safety_enabled=False,
    )
    assert health["status"] == "FAIL"
    assert "DISCOVERY_CORE_COVERAGE_INSUFFICIENT" in health["hard_fail_reasons"]
    assert health["optional_enhanced_failed"] == ["scopus"]  # vẫn được ghi nhận, dù overall đã là FAIL
