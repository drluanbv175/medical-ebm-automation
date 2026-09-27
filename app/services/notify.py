"""Gửi CẢNH BÁO khi có mục MỚI ưu tiên cao: email (SMTP) và/hoặc webhook.

Nguyên tắc an toàn:
- Chỉ gửi khi đã cấu hình (ENABLE_EMAIL_ALERTS + SMTP / ALERT_WEBHOOK_URL).
- Chỉ gửi khi THỰC SỰ có mục ưu tiên cao mới (cảnh báo an toàn thuốc chính thức,
  guideline mới, hoặc mục actionable mới). Không có gì mới -> không gửi (không spam).
- Không bao giờ bịa nội dung; chỉ chuyển tiếp dữ liệu đã truy vết.
- Chỉ gửi khi lượt chạy mới nhất là LIVE + source_health PASS, và chỉ gửi mục của lượt
  LIVE — mục DEMO/mock không bao giờ đi ra ngoài, kể cả force (vá 26/09/2026, synthesis #6).
"""
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List

from app.config import settings
from app.reports.alert_digest import build_alert_data, render_alert_markdown
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _high_priority(data: Dict) -> List:
    """Các mục đáng GỬI cảnh báo: cảnh báo quản lý + guideline + actionable mới."""
    return data.get("regulatory", []) + data.get("guidelines", []) + data.get("actionable", [])


def send_email(subject: str, body_md: str, body_html: str | None = None) -> Dict:
    """Gửi email qua SMTP. Trả về status; 'skipped' nếu chưa cấu hình."""
    if not (settings.enable_email_alerts and settings.smtp_host
            and settings.alert_email_to and settings.smtp_from
            and settings.smtp_password):
        reason = ("missing_app_password" if (settings.enable_email_alerts
                  and not settings.smtp_password) else "email_not_configured")
        return {"status": "skipped", "reason": reason}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = settings.alert_email_to
        msg.attach(MIMEText(body_md, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from,
                            [a.strip() for a in settings.alert_email_to.split(",")],
                            msg.as_string())
        logger.info("Đã gửi email cảnh báo tới %s", settings.alert_email_to)
        return {"status": "sent", "to": settings.alert_email_to}
    except Exception as exc:  # pragma: no cover - phụ thuộc SMTP thật
        logger.warning("Gửi email thất bại: %s", exc)
        return {"status": "error", "error": str(exc)}


def send_webhook(text: str, payload_extra: Dict | None = None) -> Dict:
    """POST tới webhook (Slack/Telegram/n8n…). 'skipped' nếu chưa cấu hình.

    CHỦ Ý dùng `requests.post()` trực tiếp, KHÔNG qua `app.utils.http.HttpClient`: HttpClient có
    retry tự động cho lỗi tạm thời (429/5xx) — an toàn cho GET (không tác dụng phụ) nhưng NGUY
    HIỂM cho POST không-idempotent như gửi cảnh báo: nếu server đã nhận và xử lý request nhưng
    phản hồi bị mất/chậm, retry sẽ GỬI TRÙNG cảnh báo. Timeout=20s đã đủ để không treo vô hạn;
    không cần thêm retry cho hàm chạy 1 lần/digest (tần suất thấp, không phải vòng lặp).
    """
    if not settings.alert_webhook_url:
        return {"status": "skipped", "reason": "webhook_not_configured"}
    try:
        # 'text' là khóa phổ biến (Slack/Telegram-bridge). Kèm payload thô.
        body = {"text": text}
        if payload_extra:
            body.update(payload_extra)
        import requests
        r = requests.post(settings.alert_webhook_url, json=body, timeout=20)
        r.raise_for_status()
        logger.info("Đã gửi webhook cảnh báo (HTTP %s)", r.status_code)
        return {"status": "sent", "http": r.status_code}
    except Exception as exc:  # pragma: no cover
        logger.warning("Gửi webhook thất bại: %s", exc)
        return {"status": "error", "error": str(exc)}


def ly_do_chan_gui() -> str | None:
    """Cổng GỬI cảnh báo nội dung, áp cho MỌI nơi gọi (vá 26/09/2026, synthesis #6).

    Chỉ cho gửi khi lượt chạy MỚI NHẤT là lượt LIVE đã kết thúc với source_health PASS.
    Trước đây chỉ `cmd_live_update` có cổng này; `scheduler.job_daily/job_weekly` (lệnh
    `run.py schedule` trong README) gửi cả sau lượt PARTIAL/FAIL và ở chế độ mock. Trả lý do
    chặn (chuỗi) hoặc None nếu được gửi. Không đọc được trạng thái ⇒ CHẶN (fail-closed)."""
    from app.services import run_state

    try:
        run = run_state.latest_run()
    except Exception as exc:  # noqa: BLE001 - không đọc được sổ lượt chạy ⇒ không gửi
        return f"khong_doc_duoc_luot_chay: {exc}"
    if run is None:
        return "chua_co_luot_chay"
    if (run.status or "") == "running" or run.finished_at is None:
        return "luot_moi_nhat_chua_ket_thuc"
    if (run.mode or "") != "live":
        return f"luot_moi_nhat_khong_phai_live ({run.mode or 'khong_ro'})"
    source_health = dict((run.stats or {}).get("source_health") or {})
    trang_thai = str(source_health.get("status") or "khong_ro")
    if trang_thai != "PASS":
        return f"source_health_{trang_thai.lower()}"
    return None


def notify_high_priority_new(days: int = 7, force: bool = False) -> Dict:
    """Dựng bản tin 'mới' và gửi nếu có mục ưu tiên cao (hoặc force=True).

    Cổng `ly_do_chan_gui()` áp TRƯỚC, kể cả khi force=True: lượt mới nhất không phải live
    PASS ⇒ không gửi. Bản tin gửi đi chỉ gồm mục của lượt LIVE (`chi_live=True`) — mục của
    lượt mock KHÔNG BAO GIỜ được gửi, kể cả force.

    Trả về tổng hợp kết quả gửi (email/webhook) + số mục.
    """
    ly_do = ly_do_chan_gui()
    if ly_do:
        logger.info("Không gửi cảnh báo nội dung: %s", ly_do)
        return {"days": days, "total_new": 0, "high_priority": 0,
                "status": "blocked", "reason": ly_do,
                "email": {"status": "skipped", "reason": ly_do},
                "webhook": {"status": "skipped", "reason": ly_do}}

    data = build_alert_data(days=days, chi_live=True)
    if data.get("n_demo"):
        # Không thể xảy ra khi chi_live=True; nếu có ⇒ lỗi logic, CHẶN chứ không gửi.
        ly_do = f"ban_tin_con_{data['n_demo']}_muc_demo"
        return {"days": days, "total_new": data["total_new"], "high_priority": 0,
                "status": "blocked", "reason": ly_do,
                "email": {"status": "skipped", "reason": ly_do},
                "webhook": {"status": "skipped", "reason": ly_do}}
    hp = _high_priority(data)
    result: Dict = {"days": days, "total_new": data["total_new"],
                    "high_priority": len(hp)}

    if not hp and not force:
        result["status"] = "no_high_priority_new"
        result["email"] = {"status": "skipped", "reason": "nothing_to_send"}
        result["webhook"] = {"status": "skipped", "reason": "nothing_to_send"}
        return result

    md = render_alert_markdown(data)
    n_reg = len(data.get("regulatory", []))
    n_gl = len(data.get("guidelines", []))
    n_act = len(data.get("actionable", []))
    subject = (f"[EBM Alert] {len(hp)} mục mới ưu tiên cao "
               f"({n_reg} an toàn thuốc, {n_gl} guideline, {n_act} actionable)")
    try:
        import markdown as md_lib
        html = md_lib.markdown(md, extensions=["tables"])
    except Exception:  # pragma: no cover
        html = None

    result["email"] = send_email(subject, md, html)
    result["webhook"] = send_webhook(subject + "\n\n" + md[:1500])
    result["status"] = "sent" if (result["email"]["status"] == "sent"
                                  or result["webhook"]["status"] == "sent") else "not_delivered"
    return result
