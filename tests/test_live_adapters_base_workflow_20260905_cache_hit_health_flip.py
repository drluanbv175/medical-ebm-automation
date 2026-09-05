"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 12) trong app/evidence/live_adapters/base.py::LiveSourceAdapter.lookup().

CƠ CHẾ LỖI: khi cache hit (`cached is not None and cached.payload`), code CŨ LUÔN gọi
`self.monitor.success(...)` — kể cả khi payload đã lưu là kết quả `unavailable=True`
(lỗi cấu hình DAI DẲNG, vd thiếu NCBI_EMAIL — không phải ngoại lệ tạm thời). Cache TTL
tới 24h (mặc định), nên `health_status` bị "lành" giả ngay từ lượt tra thứ hai và giữ
"ok" suốt 24h dù nguồn vẫn hỏng thật — nhánh KHÔNG cache (phần dưới của `lookup()`) đã
đúng khi rẽ theo `source.unavailable`, nhưng nhánh cache lại không làm giống vậy.

Lưu ý phạm vi: bug này CHỈ làm sai tầng quan sát/health-dashboard — quyết định xác minh
trích dẫn thật trong `CitationVerifier.verify()` đọc trực tiếp `SourceMetadata.unavailable`
của kết quả trả về (payload cache vẫn đúng `unavailable=True`), nên KHÔNG bị ảnh hưởng.

BẢN VÁ: nhánh cache hit cũng rẽ theo `cached.payload.get("unavailable")` — unavailable
thì gọi `monitor.failure(...)`, ngược lại mới gọi `monitor.success(...)`.

Nguyên tắc viết test: gọi THẲNG `LiveSourceAdapter.lookup()`/`SourceHealthMonitor` thật
qua một adapter con tối giản (cùng khuôn `UnavailableAdapter` trong
tests/test_phase_2b_live_source_validation.py), không mock nội bộ.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.citation_cache import InMemoryCitationCache  # noqa: E402
from app.evidence.citation_verification import SourceMetadata  # noqa: E402
from app.evidence.live_adapters.base import LiveSourceAdapter, LiveSourceConfig  # noqa: E402


class _PersistentlyUnavailableAdapter(LiveSourceAdapter):
    """Mô phỏng lỗi cấu hình DAI DẲNG (vd thiếu NCBI_EMAIL) — không raise exception,
    chỉ trả SourceMetadata(unavailable=True) mỗi lần _lookup_live() được gọi."""

    def __init__(self, cache):
        super().__init__(
            LiveSourceConfig("persistent_source", "article", "https://example.test"),
            cache=cache,
        )
        self.live_calls = 0

    def _lookup_live(self, identifiers):
        self.live_calls += 1
        return SourceMetadata(found=False, unavailable=True, raw={"error_state": "ncbi_email_required"})


class TestCacheHitVoiPayloadUnavailableKhongDuocBaoLaSuccess:
    """★★★ Ca chính — lần tra THỨ HAI (phục vụ từ cache, cùng payload unavailable=True
    của lần đầu) phải giữ nguyên health_status='unavailable', KHÔNG được lật thành 'ok'."""

    def test_lan_hai_tu_cache_van_bao_unavailable(self):
        cache = InMemoryCitationCache()
        adapter = _PersistentlyUnavailableAdapter(cache)
        identifiers = {"pmid": "12345678"}

        first = adapter.lookup(identifiers)
        assert first.unavailable is True
        health_after_first = adapter.monitor.snapshot()["persistent_source"]
        assert health_after_first.health_status == "unavailable"
        assert health_after_first.failure_reason

        second = adapter.lookup(identifiers)  # phục vụ từ cache — KHÔNG gọi _lookup_live() lần 2
        assert adapter.live_calls == 1, "Lần 2 phải phục vụ từ cache, không gọi mạng lại"
        assert second.unavailable is True

        health_after_second = adapter.monitor.snapshot()["persistent_source"]
        assert health_after_second.health_status == "unavailable", (
            "TRƯỚC bản vá: cache hit luôn gọi monitor.success() bất kể payload là "
            "unavailable=True, làm health_status lật giả về 'ok'"
        )
        assert health_after_second.failure_reason, "Lý do lỗi không được xoá khi vẫn còn unavailable"


class TestCacheHitVoiPayloadHopLeVanBaoSuccessNhuCu:
    """Đối chứng bắt buộc — cache hit cho một kết quả TÌM THẤY hợp lệ vẫn phải báo
    'ok' như hành vi gốc, bản vá không làm hỏng đường vui."""

    def test_cache_hit_hop_le_van_bao_ok(self):
        cache = InMemoryCitationCache()

        class _FoundAdapter(LiveSourceAdapter):
            def __init__(self, cache):
                super().__init__(LiveSourceConfig("found_source", "article", "https://example.test"), cache=cache)
                self.live_calls = 0

            def _lookup_live(self, identifiers):
                self.live_calls += 1
                return SourceMetadata(
                    found=True, title="X", authors_or_organization="Y",
                    year_or_version="2026", source_type="article", population="Adults",
                )

        adapter = _FoundAdapter(cache)
        identifiers = {"doi": "10.1000/test"}

        adapter.lookup(identifiers)
        adapter.lookup(identifiers)  # phục vụ từ cache
        assert adapter.live_calls == 1

        health = adapter.monitor.snapshot()["found_source"]
        assert health.health_status == "ok"
        assert health.failure_reason == ""
