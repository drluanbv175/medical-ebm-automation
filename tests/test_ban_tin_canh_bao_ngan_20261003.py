"""Hồi quy HV-05 (03/10/2026): email cảnh báo là bản DUMP 162 KB / 379 mục — nay thân email là
BẢN TIN NGẮN, bản đầy đủ đi kèm dạng tệp. Không mục nào bị LỌC BỎ: phần vượt trần mỗi nhóm nói rõ
«+N mục nữa trong tệp đính kèm»."""
from __future__ import annotations

from email import message_from_string
from types import SimpleNamespace

from app.config import settings
from app.reports import alert_digest as ad
from app.services import notify


def _muc(i, nhom):
    return SimpleNamespace(id=f"{nhom}{i}", title=f"{nhom} số {i}", pmid=str(40000000 + i), doi=None, url=None,
                           nct_id=None, operational_evidence_level=None, reliability_tier=None, safety_signal=None,
                           clinical_area=None, reason_for_exclusion=None)


def _data(n_reg=20, n_gl=12, n_act=9, n_rut=1, n_ft=30, n_faers=40):
    return {"days": 7, "generated_at": "2026-10-03 01:00 UTC", "run_mode": "live", "total_new": 379, "since_date": None,
            "regulatory": [_muc(i, "REG") for i in range(n_reg)],
            "guidelines": [_muc(i, "GL") for i in range(n_gl)],
            "actionable": [_muc(i, "ACT") for i in range(n_act)], "retracted": [_muc(i, "RUT") for i in range(n_rut)],
            "need_full_text": [_muc(i, "FT") for i in range(n_ft)],
            "drug_signals": [_muc(i, "FAERS") for i in range(n_faers)],
            "demo_ids": set()}


def test_ban_tin_ngan_co_tran_va_khong_bo_im_lang():
    s = ad.render_alert_short(_data(), "Alert_Digest_20261003.md")
    dong = s.splitlines()
    assert len(dong) <= 40, f"bản tin ngắn quá dài: {len(dong)} dòng"
    assert "Chế độ: live" in s and "Alert_Digest_20261003.md" in s
    for nhom, tran, tong in (("REG", 8, 20), ("GL", 5, 12), ("ACT", 5, 9)):
        hien = sum(1 for d in dong if d.startswith(f"- {nhom} số "))
        assert hien == tran, (nhom, hien)
        assert f"+{tong - tran} mục nữa trong tệp đính kèm" in s
    assert "(+70 mục «cần đọc toàn văn»/tín hiệu FAERS" in s, "nhóm không liệt kê vẫn phải được ĐẾM"


def test_thu_tu_an_toan_truoc():
    s = ad.render_alert_short(_data())
    vt = [s.index(x) for x in ("BÀI ĐÃ BỊ RÚT", "an toàn thuốc CHÍNH THỨC", "Guideline mới", "Đáng cân nhắc")]
    assert vt == sorted(vt)


def test_nhom_rong_khong_in_va_khong_co_cap_nhat():
    s = ad.render_alert_short(_data(n_reg=0, n_gl=1, n_act=0, n_rut=0, n_ft=0, n_faers=0))
    assert "an toàn thuốc CHÍNH THỨC" not in s and "- GL số 0" in s and "mục nữa" not in s
    d = _data()
    d["total_new"] = 0
    assert "Không có cập nhật mới" in ad.render_alert_short(d)


def test_send_email_dinh_kem_ban_day_du(monkeypatch):
    da_gui = {}

    class _SMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, **k):
            pass

        def login(self, *a):
            pass

        def sendmail(self, frm, to, raw):
            da_gui["raw"] = raw

    for k, v in (("enable_email_alerts", True), ("smtp_host", "smtp.invalid"), ("alert_email_to", "a@b.invalid"),
                 ("smtp_from", "c@d.invalid"), ("smtp_password", "x"), ("smtp_user", "u"), ("smtp_use_tls", True)):
        monkeypatch.setattr(settings, k, v)
    monkeypatch.setattr(notify.smtplib, "SMTP", _SMTP)
    kq = notify.send_email("tiêu đề", "BẢN TIN NGẮN", "<pre>ngắn</pre>",
                           attachments=[("Alert_Digest_x.md", "BẢN ĐẦY ĐỦ", "markdown")])
    assert kq["status"] == "sent"
    msg = message_from_string(da_gui["raw"])
    assert msg.get_content_type() == "multipart/mixed"
    phan = list(msg.walk())
    tep = [p for p in phan if p.get_filename() == "Alert_Digest_x.md"]
    assert tep and tep[0].get_payload(decode=True).decode("utf-8") == "BẢN ĐẦY ĐỦ"
    assert any(p.get_content_type() == "text/plain" and p.get_payload(decode=True).decode("utf-8") == "BẢN TIN NGẮN"
               for p in phan)


def test_khong_dinh_kem_giu_nhu_cu(monkeypatch):
    monkeypatch.setattr(settings, "enable_email_alerts", False)
    assert notify.send_email("s", "b")["status"] == "skipped"


def test_notify_gui_ban_ngan_kem_tep_day_du(monkeypatch):
    goi = []
    monkeypatch.setattr(notify, "ly_do_chan_gui", lambda: None)
    monkeypatch.setattr(notify, "build_alert_data", lambda days, chi_live: _data())
    monkeypatch.setattr(notify, "send_email",
                        lambda subject, body_md, body_html=None, attachments=None: goi.append((body_md, attachments))
                        or {"status": "sent"})
    monkeypatch.setattr(notify, "send_webhook", lambda text, payload_extra=None: {"status": "skipped"})
    kq = notify.notify_high_priority_new(days=7)
    than, dinh_kem = goi[0]
    assert kq["status"] == "sent" and len(than.splitlines()) <= 40 and "REG số 19" not in than
    assert dinh_kem and dinh_kem[0][0].startswith("Alert_Digest_") and "REG số 19" in dinh_kem[0][1], \
        "mục vượt trần của bản ngắn phải nằm trong tệp đính kèm đầy đủ"
