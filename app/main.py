"""Điểm vào logic chính (CLI nội bộ). Dùng qua run.py.

Cung cấp các lệnh: init, seed, run, report, export, scheduler.
"""
from __future__ import annotations

from typing import Dict, Optional

from app.database import init_db
from app.reports import (
    export_alert_digest,
    export_antibiotic_report,
    export_dashboard_excel,
    export_drug_safety_report,
    export_research_tracker_excel,
    export_source_log_csv,
    export_weekly_ebm_docx,
    export_weekly_ebm_html,
    export_weekly_ebm_markdown,
    export_zotero_bibtex,
)
from app.services.filtering import classify
from app.services.normalization import normalize
from app.services.pipeline import run_pipeline, score_item
from app.utils.logging_config import get_logger
from app.utils.seed import seed_all

logger = get_logger(__name__)


def cmd_init() -> None:
    init_db()
    logger.info("Đã khởi tạo database.")


def cmd_seed() -> Dict:
    return seed_all(run_pipeline_mock=True)


def cmd_run_pipeline() -> Dict:
    init_db()
    return run_pipeline()


def cmd_live_update(max_results_per_query: int = 8, *, strict_source_health: bool = True) -> Dict:
    """Luồng cập nhật THỰC TẾ hằng tuần: quét API thật toàn bộ nguồn đang bật,
    chạy pipeline, lưu DB và sinh đầy đủ báo cáo (EBM tuần + an toàn thuốc + kháng sinh).

    Tạm ép USE_MOCK_SOURCES=false cho lần chạy này (khôi phục sau khi xong).
    Khuyến nghị điền NCBI_EMAIL/OPENALEX_EMAIL/UNPAYWALL_EMAIL trong .env để gọi
    lịch sự đúng chuẩn (polite pool). Nguồn lỗi được ghi Source Log và làm trạng thái
    PARTIAL/FAIL; strict mode tuyệt đối không dùng mock để phát hành hoặc nối sang Hub.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22, phát hiện #3) —
    khuôn ép-cờ-rồi-chạy-pipeline-rồi-khôi-phục này KHÔNG khoá, trong khi
    app/utils/seed.py::seed_all() làm y hệt ở CHIỀU NGƯỢC LẠI trên CÙNG cờ
    toàn cục `settings.use_mock_sources`. Dashboard gọi cả hai đường từ hai
    nút bấm khác nhau trong CÙNG một tiến trình Streamlit — bấm gần như
    đồng thời có thể khiến lượt cập nhật THẬT (vài phút) đọc trúng cờ đã bị
    lượt "Dữ liệu mẫu" (chạy nhanh, xen giữa) đẩy tạm về True, làm dữ liệu
    MOCK lẫn vào một lượt cập nhật tưởng là dữ liệu THẬT mà không cảnh báo.
    Khoá dùng chung `settings.use_mock_sources_override_lock` với
    seed_all() để tuần tự hoá hai lượt.
    """
    from app.config import settings, use_mock_sources_override_lock

    init_db()
    with use_mock_sources_override_lock:
        previous = settings.use_mock_sources
        settings.use_mock_sources = False
        try:
            stats = run_pipeline(
                max_results_per_query=max_results_per_query,
                strict_source_health=strict_source_health,
            )
        finally:
            settings.use_mock_sources = previous

    alert = export_alert_digest(days=7)
    reports = {
        "alert_digest_md": str(alert["markdown"]),
        "alert_digest_html": str(alert["html"]),
        "weekly_md": str(export_weekly_ebm_markdown()),
        "weekly_html": str(export_weekly_ebm_html()),
        "drug_safety_md": str(export_drug_safety_report()["markdown"]),
        "antibiotic_md": str(export_antibiotic_report()["markdown"]),
    }
    docx = export_weekly_ebm_docx()
    if docx:
        reports["weekly_docx"] = str(docx)
    source_health = dict(stats.get("source_health") or {})
    deployment_status = str(source_health.get("status") or "FAIL")
    # Không gửi cảnh báo nội dung khi lượt quét không đầy đủ: tránh biến dữ liệu PARTIAL
    # thành thông điệp có vẻ đã bao quát. launchd vẫn nhận mã thoát khác 0 để báo lỗi vận hành.
    if deployment_status == "PASS":
        from app.services.notify import notify_high_priority_new
        notify = notify_high_priority_new(days=7)
    else:
        notify = {
            "status": "blocked",
            "reason": f"source_health_{deployment_status.lower()}",
        }
    # Dịch trước (cache) nội dung dashboard -> bác sĩ mở Dark Analyst là hiện NGAY (việt hoá đủ).
    warmed = 0
    if deployment_status == "PASS":
        try:
            from app.reports.evidence_workbench import prewarm_translations
            warmed = prewarm_translations(per_area=10)
        except Exception:  # pragma: no cover
            warmed = 0
    return {"mode": "live", "pipeline": stats,
            "new_this_run": stats.get("new_items"),
            "new_in_digest": alert["total_new"], "notify": notify, "reports": reports,
            "prewarmed_topics": warmed,
            "deployment_status": deployment_status,
            "bridge_allowed": deployment_status == "PASS"}


def cmd_alert(days: int = 7) -> Dict:
    """Xuất bản tin cảnh báo 'mới trong N ngày' (không chạy pipeline)."""
    init_db()
    res = export_alert_digest(days=days)
    return {"alert_markdown": str(res["markdown"]), "alert_html": str(res["html"]),
            "total_new": res["total_new"], "days": days}


def cmd_notify(days: int = 7, force: bool = False) -> Dict:
    """Gửi cảnh báo email/webhook nếu có mục mới ưu tiên cao (cần cấu hình SMTP/webhook)."""
    from app.services.notify import notify_high_priority_new
    init_db()
    return notify_high_priority_new(days=days, force=force)


def cmd_weekly_report() -> Dict:
    init_db()
    run_pipeline()
    paths = {
        "markdown": str(export_weekly_ebm_markdown()),
        "html": str(export_weekly_ebm_html()),
    }
    docx = export_weekly_ebm_docx()
    if docx:
        paths["docx"] = str(docx)
    alert = export_alert_digest(days=7)
    paths["alert_digest_md"] = str(alert["markdown"])
    drug = export_drug_safety_report()
    antibiotic = export_antibiotic_report()
    paths["drug_safety_md"] = str(drug["markdown"])
    paths["antibiotic_md"] = str(antibiotic["markdown"])
    return paths


def cmd_tiktok(limit: int = 5, include_watch: bool = False,
               queue_only: bool = False, make_video: bool = False,
               style: str = "clinical", draw_on: bool = False) -> Dict:
    """Sinh một lô GÓI nội dung TikTok (slideshow + caption [+ video]) từ kho chứng cứ.

    Mặc định chỉ lấy tài liệu đủ mạnh (recommendation); include_watch=True mới
    thêm 'tin nhanh – chưa kết luận'. make_video=True dựng thêm video dọc + giọng
    đọc tiếng Việt (cần macOS say + ffmpeg). Không gọi mạng (dùng dữ liệu trong DB).
    """
    init_db()
    from app.social import generate_tiktok_batch
    return generate_tiktok_batch(limit=limit, include_watch=include_watch,
                                 queue_only=queue_only, make_video=make_video,
                                 style=style, draw_on=draw_on)


# Bản đồ tên nguồn -> class connector (cho lệnh test-live).
_SOURCE_MAP = {}


def _build_source_map():
    if _SOURCE_MAP:
        return _SOURCE_MAP
    from app.sources import (
        ClinicalTrialsClient,
        ConsensusClient,
        CoreClient,
        CrossrefClient,
        EpistemonikosClient,
        EuropePMCClient,
        OpenAlexClient,
        OpenFDAClient,
        PubMedClient,
        ScopusClient,
        SemanticScholarClient,
        SerpApiScholarClient,
    )
    _SOURCE_MAP.update({
        "pubmed": PubMedClient, "europepmc": EuropePMCClient,
        "crossref": CrossrefClient, "clinicaltrials": ClinicalTrialsClient,
        "openalex": OpenAlexClient, "semantic_scholar": SemanticScholarClient,
        "openfda": OpenFDAClient, "scopus": ScopusClient, "core": CoreClient,
        "epistemonikos": EpistemonikosClient,
        # Mỗi lần test-live thật tốn 1 search SerpApi; thiếu SERPAPI_API_KEY sẽ nổ RuntimeError rõ ràng.
        "serpapi_scholar": SerpApiScholarClient,
        # Tầng 1 của bậc thang dự phòng; mỗi lần test-live thật tốn 1 lượt của hạn mức THÁNG (dùng chung với
        # MCP của bác sĩ) và thiếu CONSENSUS_API_KEY sẽ nổ ConsensusLoi rõ ràng.
        "consensus": ConsensusClient,
    })
    return _SOURCE_MAP


# Truy vấn mặc định THEO NGUỒN cho `test-live` khi không gõ từ khoá. openFDA FAERS tìm theo TÊN
# THUỐC (patient.drug.medicinalproduct) — cụm «atrial fibrillation guideline 2024» luôn trả 404
# NOT_FOUND nên không kiểm được gì (đo 24/09/2026: «metformin» ⇒ 5 kết quả, khoá «FDA CHAP NHAN»).
TRUY_VAN_TEST_LIVE_CHUNG = "atrial fibrillation guideline 2024"
TRUY_VAN_TEST_LIVE_THEO_NGUON = {"openfda": "metformin"}


def truy_van_test_live_mac_dinh(source: str) -> str:
    return TRUY_VAN_TEST_LIVE_THEO_NGUON.get(source, TRUY_VAN_TEST_LIVE_CHUNG)


def cmd_test_live(source: str = "europepmc",
                  query: Optional[str] = None,
                  clinical_area: str = "Tim mạch", limit: int = 5) -> Dict:
    """Gọi MỘT nguồn ở chế độ API THẬT (bỏ qua USE_MOCK_SOURCES) và chấm điểm thử.

    Không ghi vào DB; chỉ trả kết quả để kiểm chứng kết nối + pipeline scoring.
    Khuyến nghị dùng nguồn không cần key: europepmc, crossref, clinicaltrials.
    `query=None` ⇒ truy vấn mặc định hợp với nguồn (openfda: một tên thuốc).
    """
    if not query:
        query = truy_van_test_live_mac_dinh(source)
    smap = _build_source_map()
    if source not in smap:
        return {"error": f"Nguồn '{source}' không hợp lệ. Chọn: {list(smap)}"}
    client = smap[source]()
    client.use_mock = False  # ép gọi thật cho riêng lần test này
    records = client.search(query, clinical_area=clinical_area, max_results=limit)
    results = []
    for rec in records:
        item = normalize(rec)
        score_item(item)
        classification, actionable, a_reason, x_reason = classify(item)
        results.append({
            "title": item["title"][:80], "source": item["source"],
            "doi": item["doi"], "pmid": item["pmid"], "year": item["publication_date"],
            "study_type": item["study_type"],
            "evidence_quality": item["evidence_quality_score"],
            "practice_change": item["practice_change_score"],
            "tier": item["reliability_tier"], "classification": classification,
            "is_mock": rec.raw.get("_mock", False),
        })
    # SỬA 24/09/2026 (kiểm nguồn trên Cloud): `live` từng LUÔN là True — kể cả khi connector
    # tự lùi về dữ liệu minh hoạ dù đã ép `use_mock=False` (đo thật: PubMed thiếu NCBI_EMAIL trả
    # 2 bản ghi mock, đầu ra vẫn ghi «live: true, count: 2»). `live` nay chỉ True khi KHÔNG có bản
    # ghi mock nào; lỗi mạng bị connector nuốt thành [] cũng được nói ra thay vì «count: 0» câm.
    so_mock = sum(1 for r in results if r["is_mock"])
    out = {"source": source, "query": query, "live": so_mock == 0,
           "count": len(results), "results": results}
    if so_mock:
        out["so_ban_ghi_mock"] = so_mock
        out["canh_bao"] = (f"{so_mock}/{len(results)} bản ghi là DỮ LIỆU MINH HOẠ (mock) — nguồn "
                           "CHƯA được gọi thật (vd PubMed khi thiếu NCBI_EMAIL). KHÔNG dùng kết "
                           "quả này để kết luận nguồn đang chạy.")
    http = getattr(client, "http", None)
    loi_mang = getattr(http, "last_error", "") if http is not None else ""
    if getattr(client, "khong_khop", False):
        # 404 NOT_FOUND của openFDA = truy vấn hợp lệ, 0 bản ghi khớp — KHÔNG phải lỗi mạng.
        out["ghi_chu"] = ("openFDA trả 404 NOT_FOUND = 0 báo cáo FAERS khớp truy vấn này (không phải "
                          "lỗi mạng). openFDA tìm theo TÊN THUỐC, vd: run.py test-live openfda metformin")
    elif loi_mang and not results:
        out["loi_goi_mang"] = loi_mang  # đã che khoá bởi HttpClient._record_terminal_failure
    if source == "openfda":
        # Chỉ báo TRẠNG THÁI — tuyệt đối không in giá trị khoá. Để bác sĩ xác nhận khoá đã nạp VÀ
        # được FDA chấp nhận mà không phải mở file secrets.
        from app.config import settings  # noqa: PLC0415
        from app.sources import openfda as _ofda  # noqa: PLC0415
        if not settings.openfda_api_key:
            out["khoa_api_openfda"] = "khong (chay khong khoa)"
        elif _ofda.trang_thai_khoa == "chap_nhan":
            out["khoa_api_openfda"] = "co — FDA CHAP NHAN"
        elif _ofda.trang_thai_khoa == "bi_tu_choi":
            out["khoa_api_openfda"] = "co — BI TU CHOI (403), kiem lai khoa; da tu lui ve khong khoa"
        else:
            out["khoa_api_openfda"] = "co nhung chua goi duoc lan nao (xem log mang)"
    return out


def cmd_test_live_wiley_tdm(doi: str) -> Dict:
    """Gọi Wiley TDM API THẬT để tải MỘT PDF theo DOI đã biết và kiểm chứng kết nối.

    KHÁC `cmd_test_live`: Wiley TDM không phải nguồn tìm kiếm (không có `.search()`), nên
    dùng lệnh riêng thay vì nhét vào `_SOURCE_MAP`. Không ghi vào DB; chỉ tải 1 file để
    xác nhận token + quyền truy cập theo IP đang hoạt động đến đâu (xem giới hạn IP-based
    ở app/sources/wiley_tdm.py). Dùng một DOI Open Access trước để tách lỗi token khỏi
    lỗi phạm vi IP; DOI không phải Open Access ACCESS_DENIED dù token đúng là tín hiệu
    "tài khoản WOL của bác sĩ không được cấp quyền IP từ mạng đang chạy lệnh này", không
    phải lỗi cấu hình.
    """
    from app.sources import WileyTdmClient

    if WileyTdmClient is None:
        return {"error": "Thiếu thư viện `wiley-tdm` — cài: "
                          "~/.ebm-venv/bin/pip install wiley-tdm"}
    client = WileyTdmClient()
    ket_qua = client.download_pdf(doi)
    return {
        "doi": ket_qua.doi,
        "trang_thai": ket_qua.trang_thai,
        "thanh_cong": ket_qua.thanh_cong,
        "duong_dan": ket_qua.duong_dan,
        "kich_thuoc_byte": ket_qua.kich_thuoc_byte,
        "ghi_chu": ket_qua.ghi_chu,
        "ma_http": ket_qua.ma_http,
        "thu_muc_tai": str(client.download_dir),
    }


def cmd_export_all() -> Dict:
    init_db()
    return {
        "dashboard_excel": str(export_dashboard_excel()),
        "research_tracker": str(export_research_tracker_excel()),
        "source_log_csv": str(export_source_log_csv()),
        "zotero_bibtex": str(export_zotero_bibtex()),
    }
