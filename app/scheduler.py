"""Task scheduler (APScheduler) – job hằng ngày/tuần/tháng/quý.

Chạy: python run.py schedule
Mỗi job đều an toàn với dữ liệu cũ (pipeline chỉ thêm/cập nhật, không xóa).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.database import init_db, session_scope
from app.models import ChangeLogEntry
from app.reports import (export_alert_digest, export_antibiotic_report,
                         export_dashboard_excel, export_drug_safety_report,
                         export_source_log_csv, export_weekly_ebm_html,
                         export_weekly_ebm_markdown)
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
    notify = notify_high_priority_new(days=1)  # gửi nếu có mục ưu tiên cao mới
    _log_change(f"Daily scan: {stats['new_items']} mới; alert={alert['markdown'].name} "
                f"({alert['total_new']} mục); notify={notify.get('status')}",
                "scheduler.daily")


def job_weekly() -> None:
    """Hằng tuần: báo cáo EBM tuần + cập nhật dashboard exports."""
    logger.info("[job_weekly] bắt đầu")
    run_pipeline(max_results_per_query=10)
    md = export_weekly_ebm_markdown()
    html = export_weekly_ebm_html()
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
    logger.info("Scheduler sẵn sàng (TZ=%s). Nhấn Ctrl+C để dừng.", settings.timezone)
    return sched


def run_scheduler() -> None:
    sched = build_scheduler()
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover
        logger.info("Dừng scheduler.")
