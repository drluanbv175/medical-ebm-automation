"""Test job scheduler mới: sinh lại bản tổng hợp chứng cứ RAG (tab 'Tổng hợp RAG').

Không gọi mạng thật (build() chỉ đọc VERIFIED_SCORES tĩnh trong code); dùng monkeypatch
để job ghi vào tmp_path thay vì đè file thật trong evidence/reviews/.
"""
from __future__ import annotations

from apscheduler.triggers.cron import CronTrigger

import scripts.gen_evidence_brief as geb
import tools.gen_morning_brief as gmb
from app.database import session_scope
from app.models import ChangeLogEntry
from app.scheduler import build_scheduler, job_evidence_brief, job_morning_brief


def test_job_evidence_brief_writes_file_from_verified_scores(tmp_path, monkeypatch):
    fake_out = tmp_path / "tong-hop-chung-cu-thang-diem-2026.md"
    monkeypatch.setattr(geb, "OUT", fake_out)

    job_evidence_brief()

    assert fake_out.exists()
    content = fake_out.read_text(encoding="utf-8")
    assert "Tổng hợp chứng cứ" in content
    # Phải chứa ít nhất 1 thang điểm verified thật (không bịa nội dung).
    assert geb.VERIFIED_SCORES[0]["score_name"] in content


def test_job_evidence_brief_logs_changelog_entry(tmp_path, monkeypatch):
    fake_out = tmp_path / "brief.md"
    monkeypatch.setattr(geb, "OUT", fake_out)

    with session_scope() as s:
        before = s.query(ChangeLogEntry).filter(
            ChangeLogEntry.module == "scheduler.evidence_brief").count()

    job_evidence_brief()

    with session_scope() as s:
        after = s.query(ChangeLogEntry).filter(
            ChangeLogEntry.module == "scheduler.evidence_brief").count()
    assert after == before + 1


def test_job_evidence_brief_creates_missing_parent_dir(tmp_path, monkeypatch):
    fake_out = tmp_path / "nested" / "reviews" / "brief.md"
    monkeypatch.setattr(geb, "OUT", fake_out)

    job_evidence_brief()

    assert fake_out.exists()


def test_freshness_label_missing_file_returns_placeholder(tmp_path):
    missing = tmp_path / "khong-ton-tai.md"
    assert geb.freshness_label(missing) == "chưa sinh"


def test_freshness_label_uses_real_mtime(tmp_path):
    from datetime import datetime

    f = tmp_path / "brief.md"
    f.write_text("nội dung", encoding="utf-8")
    expected = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    assert geb.freshness_label(f) == expected


def test_build_scheduler_registers_evidence_brief_job():
    # build_scheduler() chỉ tạo BlockingScheduler + đăng ký job, KHÔNG start() —
    # nên không cần (và không thể) shutdown() một scheduler chưa chạy.
    sched = build_scheduler()
    job = sched.get_job("evidence_brief")
    assert job is not None
    assert job.func is job_evidence_brief
    assert isinstance(job.trigger, CronTrigger)
    field_by_name = {f.name: str(f) for f in job.trigger.fields}
    assert field_by_name["day_of_week"] == "mon"


def test_job_morning_brief_writes_daily_and_archived_files(tmp_path, monkeypatch):
    monkeypatch.setattr(gmb, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(gmb, "EXPORTS_DIR", tmp_path / "exports" / "morning_brief")
    monkeypatch.setattr(gmb, "generate_brief", lambda: "# Morning Brief\nCần bác sĩ kiểm chứng")

    job_morning_brief()

    fixed_output = tmp_path / "results" / "daily_ebm_brief.md"
    archived = list((tmp_path / "exports" / "morning_brief").glob("EBM_SANG_*.md"))
    assert fixed_output.read_text(encoding="utf-8").startswith("# Morning Brief")
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == fixed_output.read_text(encoding="utf-8")


def test_job_morning_brief_logs_changelog_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(gmb, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(gmb, "EXPORTS_DIR", tmp_path / "exports" / "morning_brief")
    monkeypatch.setattr(gmb, "generate_brief", lambda: "# Morning Brief\nCần bác sĩ kiểm chứng")

    with session_scope() as s:
        before = s.query(ChangeLogEntry).filter(
            ChangeLogEntry.module == "scheduler.morning_brief").count()

    job_morning_brief()

    with session_scope() as s:
        after = s.query(ChangeLogEntry).filter(
            ChangeLogEntry.module == "scheduler.morning_brief").count()
    assert after == before + 1


def test_build_scheduler_registers_weekday_morning_brief_job():
    sched = build_scheduler()
    job = sched.get_job("morning_brief")
    assert job is not None
    assert job.func is job_morning_brief
    assert isinstance(job.trigger, CronTrigger)
    field_by_name = {f.name: str(f) for f in job.trigger.fields}
    assert field_by_name["day_of_week"] == "mon-fri"
    assert field_by_name["hour"] == "6"
    assert field_by_name["minute"] == "30"
