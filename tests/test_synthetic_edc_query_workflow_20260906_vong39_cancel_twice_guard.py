"""Hồi quy phát hiện #7 (audit vòng 39, 2026-09-06) trong
research_project/synthetic_edc_query.py::QueryLifecycleManager.cancel_query().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def cancel_query(self, query_id, cancelled_by, reason):
        q = self._get(query_id)
        if q.status == QueryStatus.CLOSED:
            raise ValueError(f"... already CLOSED — cannot cancel")
        if not reason:
            raise ValueError("cancellation reason must be non-empty")
        q.status = QueryStatus.CANCELLED
        q.cancellation_reason = reason
        q.closed_by = cancelled_by
        return q

Chặn được "hủy một query đã CLOSED" nhưng KHÔNG chặn "hủy một query ĐÃ
CANCELLED" — một truy vấn đã hủy vẫn thỏa điều kiện (status != CLOSED) nên
có thể gọi cancel_query() lần thứ hai với actor/reason khác, GHI ĐÈ
cancellation_reason và closed_by gốc một cách âm thầm. Đây là thiếu một
guard ĐỐI XỨNG với guard CLOSED đã có — cùng họ lỗi với close_query() chỉ
cho phép đóng khi ANSWERED (guard một chiều đã đúng) nhưng cancel_query()
lại quên vế tương ứng cho chính trạng thái nó tạo ra.

PHẠM VI ẢNH HƯỞNG: EDCQuery.cancellation_reason là dấu vết audit trail của
lý do hủy một truy vấn dữ liệu trong vòng đời EDC (R2.0). Cho phép ghi đè
lý do hủy sau khi đã hủy phá vỡ tính bất biến của audit trail — hai lần
gọi cancel_query() với reason khác nhau sẽ khiến lịch sử thật (lý do hủy
ĐẦU TIÊN) biến mất không dấu vết."""
from __future__ import annotations

import pytest

from research_project.synthetic_edc_query import QueryLifecycleManager, QueryStatus


def _raise_and_get_id(mgr: QueryLifecycleManager) -> str:
    q = mgr.raise_query(
        record_id="REC-001",
        field="age",
        message="Giá trị tuổi vượt ngoài khoảng hợp lý (synthetic)",
        raised_by="SYNTH-MONITOR",
        raised_at_utc="2026-09-06T00:00:00Z",
    )
    return q.query_id


class TestCaChinhKhongDuocHuyLaiQueryDaHuy:
    """★★★ Ca chính — hủy lần thứ hai một query ĐÃ CANCELLED phải bị chặn,
    không được ghi đè lý do hủy gốc."""

    def test_huy_lan_hai_bi_chan(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        mgr.cancel_query(qid, cancelled_by="SYNTH-PI", reason="Lý do gốc")

        with pytest.raises(ValueError, match="already CANCELLED"):
            mgr.cancel_query(qid, cancelled_by="SYNTH-OTHER", reason="Lý do khác")

    def test_ly_do_goc_khong_bi_ghi_de_sau_lan_huy_thu_hai_that_bai(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        mgr.cancel_query(qid, cancelled_by="SYNTH-PI", reason="Lý do gốc")

        try:
            mgr.cancel_query(qid, cancelled_by="SYNTH-OTHER", reason="Lý do khác")
        except ValueError:
            pass

        stored = mgr._get(qid)
        assert stored.cancellation_reason == "Lý do gốc", (
            "TRƯỚC bản vá: gọi cancel_query() lần hai trên query ĐÃ CANCELLED "
            "không bị chặn, ghi đè cancellation_reason/closed_by gốc âm thầm. "
            f"Giá trị thực tế: {stored.cancellation_reason!r}"
        )
        assert stored.closed_by == "SYNTH-PI"


class TestDoiChungHanhViCuVanDung:
    """Đối chứng — hủy một query OPEN/ANSWERED hợp lệ vẫn hoạt động; hủy
    query đã CLOSED vẫn bị chặn như cũ; thiếu reason vẫn bị chặn."""

    def test_huy_query_open_hop_le(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        q = mgr.cancel_query(qid, cancelled_by="SYNTH-PI", reason="Không còn cần thiết")
        assert q.status == QueryStatus.CANCELLED
        assert q.cancellation_reason == "Không còn cần thiết"

    def test_huy_query_answered_hop_le(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        mgr.answer_query(qid, answer="42", answered_by="SYNTH-SITE",
                          answered_at_utc="2026-09-06T01:00:00Z")
        q = mgr.cancel_query(qid, cancelled_by="SYNTH-PI", reason="Trả lời sai định dạng")
        assert q.status == QueryStatus.CANCELLED

    def test_huy_query_da_closed_van_bi_chan_nhu_cu(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        mgr.answer_query(qid, answer="42", answered_by="SYNTH-SITE",
                          answered_at_utc="2026-09-06T01:00:00Z")
        mgr.close_query(qid, closed_by="SYNTH-PI", closed_at_utc="2026-09-06T02:00:00Z")

        with pytest.raises(ValueError, match="already CLOSED"):
            mgr.cancel_query(qid, cancelled_by="SYNTH-OTHER", reason="Bất kỳ")

    def test_reason_rong_van_bi_chan(self):
        mgr = QueryLifecycleManager()
        qid = _raise_and_get_id(mgr)
        with pytest.raises(ValueError, match="reason must be non-empty"):
            mgr.cancel_query(qid, cancelled_by="SYNTH-PI", reason="")
