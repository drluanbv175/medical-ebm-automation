"""Test circuit-breaker của sweep_source (app/services/ingestion.py) — offline, không cần DB/network.

Regression test cho lỗi treo máy thật: khi 1 nguồn (vd OpenAlex) lỗi/chậm liên tục, code cũ
vẫn thử hết toàn bộ 45 truy vấn theo CLINICAL_AREAS (~1 giờ+). Nhiều source client tự bắt
exception mạng nội bộ và trả về [] (vd OpenAlexClient.search) nên "status" luôn "ok" — vì vậy
circuit-breaker phải dừng được cả khi tín hiệu là ĐỘ TRỄ bất thường, không chỉ status="error".
"""
from __future__ import annotations

from types import SimpleNamespace

from app.config import CLINICAL_AREAS
from app.services import ingestion as ing

_AREAS = list(CLINICAL_AREAS.keys())
_TOTAL_QUERIES = sum(len(CLINICAL_AREAS[a]) for a in _AREAS)


def _client(name="fake_source"):
    return SimpleNamespace(name=name, use_mock=False, endpoint="http://fake/")


def test_no_errors_runs_all_queries():
    """Nguồn khỏe mạnh -> chạy hết toàn bộ (area, query), không bị cắt sớm."""
    def _ok_fetch(client, query, area, max_results, since_date=None):
        return [], dict(source=client.name, status="ok", record_count=0)

    recs, logs = ing.sweep_source(_client(), areas=_AREAS, max_results_per_query=10, fetch_fn=_ok_fetch)
    assert len(logs) == _TOTAL_QUERIES


def test_consecutive_errors_trigger_early_stop():
    """Đúng _MAX_CONSECUTIVE_ERRORS lỗi liên tiếp -> dừng sớm, KHÔNG thử hết truy vấn."""
    assert _TOTAL_QUERIES > ing._MAX_CONSECUTIVE_ERRORS, "Cần đủ query để test dừng sớm có ý nghĩa"
    calls = {"n": 0}

    def _always_error_fetch(client, query, area, max_results, since_date=None):
        calls["n"] += 1
        return [], dict(source=client.name, status="error", record_count=0, error_message="boom")

    recs, logs = ing.sweep_source(_client(), areas=_AREAS, max_results_per_query=10,
                                   fetch_fn=_always_error_fetch)

    assert len(logs) == ing._MAX_CONSECUTIVE_ERRORS, (
        f"Phải dừng đúng sau {ing._MAX_CONSECUTIVE_ERRORS} lỗi liên tiếp, "
        f"nhưng đã chạy {len(logs)}/{_TOTAL_QUERIES} truy vấn"
    )
    assert calls["n"] == ing._MAX_CONSECUTIVE_ERRORS


def test_consecutive_slow_queries_trigger_early_stop_even_with_status_ok(monkeypatch):
    """Circuit-breaker phải dừng cả khi status='ok' nhưng ĐỘ TRỄ bất thường (client nuốt lỗi
    mạng nội bộ, vd OpenAlexClient.search — đây chính là kịch bản OpenAlex 503 thật đã xảy ra)."""
    clock = {"t": 0.0}
    monkeypatch.setattr(ing.time, "monotonic", lambda: clock["t"])
    calls = {"n": 0}

    def _slow_fetch(client, query, area, max_results, since_date=None):
        calls["n"] += 1
        clock["t"] += ing._SLOW_QUERY_THRESHOLD_SEC + 1  # mỗi lần gọi "mất" hơn ngưỡng chậm
        return [], dict(source=client.name, status="ok", record_count=0)

    recs, logs = ing.sweep_source(_client(), areas=_AREAS, max_results_per_query=10, fetch_fn=_slow_fetch)

    assert len(logs) == ing._MAX_CONSECUTIVE_ERRORS
    assert calls["n"] == ing._MAX_CONSECUTIVE_ERRORS


def test_transient_error_recovers_and_does_not_trip_breaker():
    """Lỗi RỜI RẠC (không liên tiếp) không được kích hoạt breaker — chỉ lỗi LIÊN TỤC mới dừng."""
    calls = {"n": 0}

    def _mostly_ok_fetch(client, query, area, max_results, since_date=None):
        calls["n"] += 1
        # Lỗi ở lần gọi thứ 2 và thứ 5 (rời rạc, xen giữa các lần OK) -> không đủ liên tiếp để trip.
        status = "error" if calls["n"] in (2, 5) else "ok"
        return [], dict(source=client.name, status=status, record_count=0)

    recs, logs = ing.sweep_source(_client(), areas=_AREAS, max_results_per_query=10,
                                   fetch_fn=_mostly_ok_fetch)
    assert len(logs) == _TOTAL_QUERIES  # chạy hết, không bị cắt vì lỗi không liên tiếp đủ dài
