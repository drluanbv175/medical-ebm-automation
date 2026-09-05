"""Đánh giá phát hiện LOW-MEDIUM của Workflow đối kháng đa-agent 2026-09-04
(vòng 2, task #73): `app/core/run_packet.py::RunPacket.__post_init__()` —
nhánh kiểm `trace_ids` cho lane CLINICAL/RESEARCH/DASHBOARD là DEAD CODE.

CƠ CHẾ: dòng gốc
    if self.lane in {Lane.CLINICAL, Lane.RESEARCH, Lane.DASHBOARD} and not self.trace_ids:
        object.__setattr__(self, "trace_ids", [])
chỉ đúng điều kiện khi `trace_ids` đã RỖNG (falsy), và hành động là gán lại
đúng giá trị RỖNG — không có khả năng thay đổi hành vi quan sát được trên
BẤT KỲ đường mã thật nào. `RunPacket(...)` (hàm khởi tạo dataclass) chỉ được
gọi trực tiếp ở ĐÚNG MỘT nơi trong toàn repo — bên trong `new_run_packet()`
— và hàm đó LUÔN chuẩn hoá `trace_ids=list(trace_ids or [])` trước khi
truyền vào, nên `self.trace_ids` không bao giờ là `None` tại điểm này.

QUYẾT ĐỊNH (không phải bug cần vá bằng enforcement thật): nhánh này đã bị
XOÁ thay vì được "hoàn thiện" thành một enforcement thật (vd raise khi lane
CLINICAL/RESEARCH/DASHBOARD thiếu trace_ids) — vì `ChronicCareService.__init__`
(người gọi CLINICAL-lane DUY NHẤT của `new_run_packet()` trong toàn bộ repo,
xem app/chronic_care/service.py) không hề truyền `trace_ids`. Thêm chặn cứng
ở đây sẽ phá vỡ TOÀN BỘ module chronic_care mà không có test/doctrine nào
từng đòi hỏi yêu cầu đó — đúng nguyên tắc không tự bịa ra yêu cầu sản phẩm
mới ngoài phạm vi được giao.

Test này khoá lại TRẠNG THÁI ĐÃ XÁC NHẬN (không phải hành vi mới): trace_ids
cho lane CLINICAL/RESEARCH/DASHBOARD hoạt động y hệt các lane khác — giữ
nguyên giá trị được truyền vào, mặc định `[]` khi không truyền, KHÔNG có
enforcement/raise nào cho các lane này. Nếu một lần sửa sau này vô tình
biến nhánh chết thành enforcement thật (hoặc ngược lại, làm hỏng việc giữ
nguyên trace_ids đã truyền), test dưới đây sẽ bắt được.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.run_packet import Lane, new_run_packet  # noqa: E402


class TestKhongEnforcementChoLaneNeuKhongTruyenTraceIds:
    """★★ Ca chính — CLINICAL/RESEARCH/DASHBOARD KHÔNG raise khi thiếu
    trace_ids, đúng hành vi hiện tại của ChronicCareService.__init__()."""

    def test_clinical_khong_truyen_trace_ids_khong_raise(self):
        packet = new_run_packet(Lane.CLINICAL, "mục tiêu test")
        assert packet.trace_ids == []

    def test_research_khong_truyen_trace_ids_khong_raise(self):
        packet = new_run_packet(Lane.RESEARCH, "mục tiêu test")
        assert packet.trace_ids == []

    def test_dashboard_khong_truyen_trace_ids_khong_raise(self):
        packet = new_run_packet(Lane.DASHBOARD, "mục tiêu test")
        assert packet.trace_ids == []


class TestTraceIdsGiuNguyenGiaTriDaTruyen:
    """Đối chứng — trace_ids ĐÃ truyền phải được giữ nguyên cho cả ba lane
    "đặc biệt" lẫn lane khác, không bị nhánh __post_init__ can thiệp."""

    def test_clinical_giu_nguyen_trace_ids_da_truyen(self):
        packet = new_run_packet(Lane.CLINICAL, "mục tiêu test", trace_ids=["t1", "t2"])
        assert packet.trace_ids == ["t1", "t2"]

    def test_system_lane_hanh_vi_giong_het_clinical(self):
        """Lane KHÔNG nằm trong {CLINICAL, RESEARCH, DASHBOARD} — hành vi
        trace_ids phải giống hệt (không có khác biệt nào giữa hai nhóm lane,
        đúng kết luận nhánh cũ là dead code)."""
        packet_khong_truyen = new_run_packet(Lane.SYSTEM, "mục tiêu test")
        packet_co_truyen = new_run_packet(Lane.SYSTEM, "mục tiêu test", trace_ids=["t1"])
        assert packet_khong_truyen.trace_ids == []
        assert packet_co_truyen.trace_ids == ["t1"]

    def test_to_dict_khong_crash_voi_trace_ids_rong(self):
        packet = new_run_packet(Lane.CLINICAL, "mục tiêu test")
        d = packet.to_dict()
        assert d["trace_ids"] == []
