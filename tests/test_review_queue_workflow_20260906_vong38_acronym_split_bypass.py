"""Hồi quy phát hiện #1 (audit vòng 38, 2026-09-06) trong
research_automation/review_queue.py::_looks_non_human().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    tokens = re.split(r"[^a-z0-9]+", ref.lower())
    joined = "".join(t for t in tokens if t)
    for tok in tokens:
        if tok in _NON_HUMAN_REF_TOKENS:
            return tok
    if "dryrun" in joined or "testbot" in joined:
        return "dryrun/testbot"
    return None

Ref bị chèn dấu chấm/gạch GIỮA TỪNG CHỮ CÁI của một mục NGẮN trong denylist
("A.I." → token ["a","i"], "G.P.T." → ["g","p","t"], "B.O.T." → ["b","o","t"])
tách vụn tới mức không token đơn lẻ nào khớp denylist, và cũng không thuộc 2
ngoại lệ hard-code "dryrun"/"testbot" — lọt qua hoàn toàn dù `joined`
("ai"/"gpt"/"bot") chứa nguyên mục denylist.

Hệ quả: `ReviewQueue.human_decision(review_id, HUMAN_APPROVED_DRAFT, "A.I.")`
sẽ THÀNH CÔNG thay vì raise AutoApprovalForbidden, phá bất biến mà chính
docstring của module tuyên bố (KHÔNG dùng "chữ ký giả đóng vai người thật").

BẢN VÁ ĐÚNG (lưu ý: bản vá ĐẦU sai — xem dưới): chỉ nối các LOẠT TOKEN
1-KÝ-TỰ LIÊN TIẾP (dấu hiệu acronym bị chèn dấu câu giữa từng chữ) rồi so
KHỚP TUYỆT ĐỐI với denylist — KHÔNG so `entry in joined` cho toàn bộ
denylist, vì cách đó khớp nhầm "Dr.Abbott" (token ["dr","abbott"], "abbott"
chứa "bot") — đúng vấn đề mà thiết kế theo-token ban đầu cố tránh (xem
docstring _NON_HUMAN_REF_TOKENS trong review_queue.py). Tên thật tách bởi
dấu câu luôn cho token NHIỀU ký tự, không bao giờ tạo loạt token 1-ký-tự
liên tiếp dài như spelling-out một acronym."""
from __future__ import annotations

from research_automation.review_queue import (
    AutoApprovalForbidden,
    ReviewQueue,
    ReviewStatus,
    _looks_non_human,
)


class TestCaChinhAcronymBiTachTungChuVanBiChan:
    """★★★ Ca chính — acronym bị chèn dấu câu giữa từng chữ vẫn phải bị nhận
    diện là phi-người, không được lọt qua."""

    def test_ai_voi_dau_cham_van_bi_bat(self):
        assert _looks_non_human("A.I.") == "ai", (
            "TRƯỚC bản vá: 'A.I.' tách thành token ['a','i'], không token nào "
            "khớp denylist ('ai' nguyên khối), và cũng không thuộc 2 ngoại lệ "
            "hard-code 'dryrun'/'testbot' — lọt qua thành None."
        )

    def test_gpt_voi_dau_cham_van_bi_bat(self):
        assert _looks_non_human("G.P.T.") == "gpt"

    def test_bot_voi_dau_cham_van_bi_bat(self):
        assert _looks_non_human("B.O.T.") == "bot"

    def test_human_decision_tu_choi_ai_voi_dau_cham(self):
        q = ReviewQueue()
        item = q.add(project_id="P1", artifact_id="A1", review_reason="r",
                    blocking_gate=None, required_human_role="PI",
                    missing_information=[], risks=[], audit_event_id=None)
        try:
            q.human_decision(item.review_id, ReviewStatus.HUMAN_APPROVED_DRAFT,
                             "A.I. Reviewer")
            assert False, "phải raise AutoApprovalForbidden, không được thành công"
        except AutoApprovalForbidden:
            pass


class TestDoiChungKhongChanNhamTenThatChuaSubstringVoHai:
    """Đối chứng — QUAN TRỌNG: bất biến "Dr.Abbott chứa 'bot' nhưng KHÔNG bị
    chặn" (ghi trong docstring gốc của _NON_HUMAN_REF_TOKENS) phải giữ
    nguyên sau bản vá — một fix ngây thơ (so `entry in joined` cho toàn bộ
    denylist) sẽ phá đúng bất biến này."""

    def test_dr_abbott_khong_bi_chan(self):
        assert _looks_non_human("Dr.Abbott") is None, (
            "Fix sai (so substring trên toàn bộ joined) sẽ khớp nhầm 'abbott' "
            "chứa 'bot' — đúng vấn đề mà thiết kế theo-token ban đầu cố tránh."
        )

    def test_ten_nguoi_thuong_khong_bi_chan(self):
        assert _looks_non_human("Nguyen Van A") is None
        assert _looks_non_human("J. Smith") is None

    def test_ten_ro_rang_phi_nguoi_van_bi_bat_nhu_cu(self):
        assert _looks_non_human("QA-Bot-42") == "bot"
        assert _looks_non_human("GPT-4o") == "gpt"
        assert _looks_non_human("PI-SYNTH-01") == "synth"
        assert _looks_non_human("claude") == "claude"

    def test_dryrun_testbot_hard_code_cu_van_hoat_dong(self):
        assert _looks_non_human("dry-run") == "dryrun/testbot"

    def test_svc_bi_chan_tach_chu(self):
        assert _looks_non_human("S.V.C.") == "svc"
