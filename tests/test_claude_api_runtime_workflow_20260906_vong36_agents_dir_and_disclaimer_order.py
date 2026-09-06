"""Hồi quy 2 phát hiện của audit vòng 36 (2026-09-06) trong
runtime/claude_api_runtime.py.

── Phát hiện #1 (latent) — _AGENTS_DIR thừa một .parent ───────────────────
CƠ CHẾ LỖI (TRƯỚC bản vá):
    _AGENTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "agents"
`__file__` = runtime/claude_api_runtime.py ⇒ .parent = runtime/,
.parent.parent = GỐC REPO (nơi thật sự có .claude/agents/*.md). Thêm MỘT
.parent nữa trỏ LÊN TRÊN gốc repo, ra thư mục không tồn tại.
_load_agent_spec() vì vậy LUÔN LUÔN rơi vào fallback generic 1 dòng
("Agent: <id>\\nVai trò: trợ lý EBM y khoa tổng quát") — không exception,
không log — nên system_prompt gọi Claude API thật không bao giờ mang nội
dung/ràng buộc hành vi thật của agent.
Vá: bớt một .parent.

── Phát hiện #2 (latent) — disclaimer nối vào TRƯỚC khi chấm điểm ─────────
CƠ CHẾ LỖI (TRƯỚC bản vá), trong run():
    response_text = message.content[0].text + _DISCLAIMER_SUFFIX
    policy = _evaluate_live_output(response_text)
`_DISCLAIMER_SUFFIX` tự nó chứa chuỗi "Cần bác sĩ kiểm chứng". Nối vào
TRƯỚC rồi mới chấm điểm khiến `has_disclaimer` trong
`_evaluate_live_output()` LUÔN LUÔN True bất kể model có thật sự tự đưa
disclaimer hay không — vô hiệu hoá hoàn toàn guard REVIEW_REQUIRED cho
tuyên bố lâm sàng quá tự tin không kèm disclaimer thật.
Vá: chấm điểm trên văn bản GỐC (raw_text), rồi mới nối suffix vào bản
hiển thị cuối cùng.

LƯU Ý PHẠM VI (đã xác minh bằng grep, không suy diễn): caller thật của
`ClaudeApiRuntime.run()` với API key khác rỗng chưa tồn tại trong repo —
mọi test hiện có (tests/test_v4_4_claude_api_runtime.py) chỉ test đường
KHÔNG có key (fallback MockAgentRuntime); không file `.py` nào ngoài
`tests/` khởi tạo ClaudeApiRuntime với key thật. Cả hai bug vẫn THẬT (tái
hiện được bằng client mock) nên vẫn sửa — chỉ không phóng đại thành đang
gây hại trong sản xuất hiện tại (latent/dormant, sẽ lộ ra khi ai đó thật
sự "bật" runtime này bằng ANTHROPIC_API_KEY như docstring dự tính)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runtime.claude_api_runtime import (
    _AGENTS_DIR,
    ClaudeApiRuntime,
    _load_agent_spec,
)
from runtime.schemas import PolicyDecisionEnum

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_mock_client(response_text: str) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=response_text)]
    message.stop_reason = "end_turn"
    client.messages.create.return_value = message
    return client


class TestCaChinhAgentsDirDungGocRepo:
    """★★★ Ca chính phát hiện #1 — _AGENTS_DIR phải trỏ ĐÚNG vào
    <gốc repo>/.claude/agents, và _load_agent_spec() phải nạp được nội
    dung THẬT của một agent có sẵn trong repo."""

    def test_agents_dir_ton_tai_va_dung_vi_tri(self):
        assert _AGENTS_DIR == REPO_ROOT / ".claude" / "agents"
        assert _AGENTS_DIR.exists(), (
            "TRƯỚC bản vá: _AGENTS_DIR trỏ lên NGOÀI gốc repo (thừa một "
            f".parent), thư mục không tồn tại: {_AGENTS_DIR}"
        )

    def test_load_agent_spec_nap_duoc_noi_dung_that(self):
        spec_text = _load_agent_spec("co-mau-nghien-cuu")
        assert len(spec_text) > 500, (
            "TRƯỚC bản vá: _load_agent_spec() luôn rơi vào fallback "
            f"generic 1 dòng. Nội dung nạp được: {spec_text!r}"
        )
        assert "co-mau-nghien-cuu" in spec_text
        # Fallback generic có định dạng cố định — xác nhận KHÔNG phải nó.
        assert spec_text != (
            "Agent: co-mau-nghien-cuu\nVai trò: trợ lý EBM y khoa tổng quát."
        )


class TestCaChinhDisclaimerKhongVoHieuHoaGuard:
    """★★★ Ca chính phát hiện #2 — run() phải chấm điểm trên văn bản GỐC
    của model, không phải bản đã nối disclaimer."""

    def test_tuyen_bo_lam_sang_qua_tu_tin_khong_disclaimer_bi_review_required(self):
        rt = ClaudeApiRuntime(api_key="fake-key-for-test")
        rt._client = _make_mock_client(
            "Liều thuốc điều trị là 1000mg mỗi ngày, không cần xem xét thêm.",
        )
        out = rt.run(agent_id="ke-don-an-toan", fixture_id="test-review", input_data={})
        assert out.expected_policy_decision == PolicyDecisionEnum.REVIEW_REQUIRED, (
            "TRƯỚC bản vá: disclaimer bị nối vào response_text TRƯỚC khi "
            "chấm điểm, has_disclaimer luôn True, guard REVIEW_REQUIRED "
            f"không bao giờ kích hoạt. Kết quả thực tế: "
            f"{out.expected_policy_decision}"
        )

    def test_disclaimer_van_co_mat_trong_ban_hien_thi_cuoi(self):
        # Bản vá KHÔNG được bỏ mất disclaimer hiển thị cho bác sĩ — chỉ
        # đổi THỨ TỰ (chấm điểm trước, nối suffix sau).
        rt = ClaudeApiRuntime(api_key="fake-key-for-test")
        rt._client = _make_mock_client(
            "Liều thuốc điều trị là 1000mg mỗi ngày, không cần xem xét thêm.",
        )
        out = rt.run(agent_id="ke-don-an-toan", fixture_id="test-review", input_data={})
        assert "Cần bác sĩ kiểm chứng" in out.simulated_output["response"]


class TestDoiChungTuyenBoDaCoDisclaimerThatVanPass:
    """Đối chứng — một câu trả lời lâm sàng ĐÃ tự kèm disclaimer thật
    (không nhờ suffix) vẫn phải PASS như cũ."""

    def test_co_disclaimer_that_van_pass(self):
        rt = ClaudeApiRuntime(api_key="fake-key-for-test")
        rt._client = _make_mock_client(
            "Liều thuốc điều trị là 1000mg mỗi ngày. Cần bác sĩ kiểm chứng "
            "trước khi áp dụng.",
        )
        out = rt.run(agent_id="ke-don-an-toan", fixture_id="test-pass", input_data={})
        assert out.expected_policy_decision == PolicyDecisionEnum.PASS

    def test_khong_co_tu_khoa_lam_sang_van_pass(self):
        rt = ClaudeApiRuntime(api_key="fake-key-for-test")
        rt._client = _make_mock_client("Tóm tắt tổng quan y văn về chủ đề X.")
        out = rt.run(agent_id="tra-cuu-chung-cu", fixture_id="test-nonclinical", input_data={})
        assert out.expected_policy_decision == PolicyDecisionEnum.PASS

    def test_agent_khong_ton_tai_van_fallback_generic_khong_crash(self):
        # Đường fallback (.exists() == False cho MỘT agent_id lạ, không
        # phải toàn bộ _AGENTS_DIR) vẫn phải hoạt động, không crash.
        spec_text = _load_agent_spec("khong-ton-tai-agent-lang-thang-xyz")
        assert spec_text == (
            "Agent: khong-ton-tai-agent-lang-thang-xyz\n"
            "Vai trò: trợ lý EBM y khoa tổng quát."
        )
