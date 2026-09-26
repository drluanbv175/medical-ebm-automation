"""ESD10 FAIL phải chỉ đúng nút nhập kênh cảnh báo; PASS thì không nhắc — 26/09/2026."""
from __future__ import annotations

from types import SimpleNamespace

import app.config as cfg
from tools import verify_evidence_surveillance_deployment as V


def _dat(monkeypatch, **kw):
    mac_dinh = dict(enable_email_alerts=False, smtp_host="", smtp_password="", smtp_from="",
                    alert_email_to="", alert_webhook_url="")
    mac_dinh.update(kw)
    monkeypatch.setattr(cfg, "settings", SimpleNamespace(**mac_dinh))


def test_thieu_kenh_thi_fail_va_chi_nut(monkeypatch):
    _dat(monkeypatch)
    c = V._check_notification_config()
    assert c.status == V.FAIL
    assert "Nhap Kenh Canh Bao" in c.evidence and "notify-test" in c.evidence


def test_co_webhook_thi_pass_khong_nhac_nut(monkeypatch):
    _dat(monkeypatch, alert_webhook_url="https://hooks.example.org/x")
    c = V._check_notification_config()
    assert c.status == V.PASS and "Nhap Kenh Canh Bao" not in c.evidence
