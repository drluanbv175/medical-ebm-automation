"""Task scheduler (APScheduler) – job hằng ngày/tuần/tháng/quý.

Chạy: python run.py schedule
Mỗi job đều an toàn với dữ liệu cũ (pipeline chỉ thêm/cập nhật, không xóa).
"""
from __future__ import annotations

from app.config import settings
from app.database import init_db, session_scope
from app.models import ChangeLogEntry
from app.reports import (
    export_alert_digest,
    export_antibiotic_report,
    export_dashboard_excel,
    export_drug_safety_report,
    export_source_log_csv,
    export_weekly_ebm_html,
    export_weekly_ebm_markdown,
)
from app.services.notify import notify_high_priority_new
from app.services.pipeline import run_pipeline
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _log_change(summary: str, module: str) -> None:
    with session_scope() as s:
        s.add(ChangeLogEntry(change_summary=summary, source="scheduler",
                             module=module, created_by="scheduler"))


# --- Jobs -----------------------------------------------------------------
def job_daily() -> None:
    """Hằng ngày: quét incremental + bản tin CẢNH BÁO 'mới' (an toàn thuốc/guideline)."""
    logger.info("[job_daily] bắt đầu")
    stats = run_pipeline(max_results_per_query=5, incremental=True)
    alert = export_alert_digest(days=1)
    from app.services.knowledge_pack_surveillance import write_knowledge_pack_update_queue

    queue_path = write_knowledge_pack_update_queue(days=7)
    notify = notify_high_priority_new(days=1)  # gửi nếu có mục ưu tiên cao mới
    _log_change(f"Daily scan: {stats['new_items']} mới; alert={alert['markdown'].name} "
                f"({alert['total_new']} mục); pack_queue={queue_path.name}; notify={notify.get('status')}",
                "scheduler.daily")


def job_weekly() -> None:
    """Hằng tuần: báo cáo EBM tuần + cập nhật dashboard exports."""
    logger.info("[job_weekly] bắt đầu")
    run_pipeline(max_results_per_query=10)
    md = export_weekly_ebm_markdown()
    export_weekly_ebm_html()
    alert = export_alert_digest(days=7)
    drug = export_drug_safety_report()
    antibiotic = export_antibiotic_report()
    export_dashboard_excel()
    export_source_log_csv()
    notify = notify_high_priority_new(days=7)
    tiktok_note = ""
    if settings.enable_tiktok_auto:
        try:
            from app.social import generate_tiktok_batch
            tt = generate_tiktok_batch(limit=settings.tiktok_auto_count,
                                       make_video=settings.tiktok_auto_video)
            tiktok_note = f", tiktok={tt['count']} bài (chờ duyệt)"
        except Exception as exc:  # noqa: BLE001 - không để TikTok làm hỏng job tuần
            logger.warning("[job_weekly] sinh TikTok lỗi: %s", exc)
            tiktok_note = ", tiktok=lỗi"
    _log_change(
        f"Weekly reports: {md.name}, alert={alert['markdown'].name} "
        f"({alert['total_new']} mới), notify={notify.get('status')}, "
        f"{drug['markdown'].name}, {antibiotic['markdown'].name}{tiktok_note}",
        "scheduler.weekly")


def job_monthly() -> None:
    """Hằng tháng: tổng hợp thay đổi thực hành quan trọng (Practice Change Monthly)."""
    logger.info("[job_monthly] bắt đầu")
    export_dashboard_excel()
    _log_change("Practice Change Monthly Review tạo từ dữ liệu hiện có.",
                "scheduler.monthly")


def job_quarterly() -> None:
    """Hằng quý: rà soát thang điểm/nguồn API/guideline nền/DB & changelog."""
    logger.info("[job_quarterly] bắt đầu")
    _log_change("Quarterly review: rà soát clinical scores, nguồn API, guideline nền.",
                "scheduler.quarterly")


def job_evidence_brief() -> None:
    """Hằng tuần: sinh lại bản tổng hợp chứng cứ RAG (tab 'Tổng hợp RAG') từ thang điểm
    verified, để tab không hiển thị dữ liệu cũ nếu app/clinical_scores/verified.py đã được
    cập nhật nhưng chưa ai chạy tay `python scripts/gen_evidence_brief.py`. Không gọi mạng,
    không đụng DB — chỉ đọc VERIFIED_SCORES (dữ liệu tĩnh trong code) và ghi file .md."""
    logger.info("[job_evidence_brief] bắt đầu")
    from scripts.gen_evidence_brief import OUT, build

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    _log_change(f"Evidence brief RAG cập nhật: {OUT.name}", "scheduler.evidence_brief")


def job_morning_brief() -> None:
    """Thứ Hai-Thứ Sáu: sinh bản tin EBM sáng từ knowledge packs và surveillance offline."""
    logger.info("[job_morning_brief] bắt đầu")
    from app.services.knowledge_pack_surveillance import write_knowledge_pack_update_queue
    from tools import gen_morning_brief

    write_knowledge_pack_update_queue(days=7)
    brief = gen_morning_brief.generate_brief()
    fixed_output, dated_output = gen_morning_brief.write_brief_outputs(brief)
    _log_change(
        f"Morning brief tạo: {fixed_output.name}; lưu trữ={dated_output.name}",
        "scheduler.morning_brief",
    )


def build_scheduler():
    """Tạo BlockingScheduler với các job định kỳ."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    init_db()
    sched = BlockingScheduler(timezone=settings.timezone)
    sched.add_job(job_daily, CronTrigger(hour=7, minute=0), id="daily")
    sched.add_job(job_weekly, CronTrigger(day_of_week="mon", hour=7, minute=30), id="weekly")
    sched.add_job(job_monthly, CronTrigger(day=1, hour=8, minute=0), id="monthly")
    sched.add_job(job_quarterly, CronTrigger(month="1,4,7,10", day=1, hour=9), id="quarterly")
    sched.add_job(job_evidence_brief, CronTrigger(day_of_week="mon", hour=7, minute=15),
                  id="evidence_brief")
    sched.add_job(
        job_morning_brief,
        CronTrigger(day_of_week="mon-fri", hour=6, minute=30),
        id="morning_brief",
    )
    logger.info("Scheduler sẵn sàng (TZ=%s). Nhấn Ctrl+C để dừng.", settings.timezone)
    return sched


def run_scheduler() -> None:
    sched = build_scheduler()
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover
        logger.info("Dừng scheduler.")
