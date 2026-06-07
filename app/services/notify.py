"""Gửi CẢNH BÁO khi có mục MỚI ưu tiên cao: email (SMTP) và/hoặc webhook.

Nguyên tắc an toàn:
- Chỉ gửi khi đã cấu hình (ENABLE_EMAIL_ALERTS + SMTP / ALERT_WEBHOOK_URL).
- Chỉ gửi khi THỰC SỰ có mục ưu tiên cao mới (cảnh báo an toàn thuốc chính thức,
  guideline mới, hoặc mục actionable mới). Không có gì mới -> không gửi (không spam).
- Không bao giờ bịa nội dung; chỉ chuyển tiếp dữ liệu đã truy vết.
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
    """POST tới webhook (Slack/Telegram/n8n…). 'skipped' nếu chưa cấu hình."""
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


def notify_high_priority_new(days: int = 7, force: bool = False) -> Dict:
    """Dựng bản tin 'mới' và gửi nếu có mục ưu tiên cao (hoặc force=True).

    Trả về tổng hợp kết quả gửi (email/webhook) + số mục.
    """
    data = build_alert_data(days=days)
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
