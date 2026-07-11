"""
AgentRuntime — Abstract interface cho tất cả runtime implementations.
V4.4: ClaudeApiRuntime thật đã implement trong claude_api_runtime.py.
"""

from __future__ import annotations
import abc
from typing import Optional
from .schemas import FixtureOutput, RuntimeTypeEnum


class AgentRuntime(abc.ABC):
    """
    Interface dùng chung cho mọi agent runtime.

    Contract:
    - run() trả FixtureOutput — không raise ngoại lệ thô.
    - Không log PII, raw prompt, hoặc raw exception.
    """

    @abc.abstractmethod
    def run(
        self,
        agent_id: str,
        fixture_id: str,
        input_data: dict,
        context: Optional[dict] = None,
    ) -> FixtureOutput:
        """Chạy một agent với input cho trước. Trả FixtureOutput."""

    @abc.abstractmethod
    def get_runtime_type(self) -> RuntimeTypeEnum:
        """Trả loại runtime (MOCK / CLAUDE_API / ...)."""

    @abc.abstractmethod
    def is_api_runtime(self) -> bool:
        """True nếu runtime có thể gọi network."""

    def assert_offline(self) -> None:
        """Block nếu đây là API runtime đang chạy trong offline mode."""
        if self.is_api_runtime():
            raise RuntimeError(
                "API runtime bị block trong Offline/Internal QA mode. "
                "Cần gate APPROVED trước khi dùng ClaudeApiRuntime."
            )


# V4.4: ClaudeApiRuntime thật — xem claude_api_runtime.py
# Re-export qua module __getattr__ (PEP 562): cho phép
#   from runtime.agent_runtime import ClaudeApiRuntime
# mà KHÔNG import claude_api_runtime lúc nạp module. Bắt buộc lazy vì
# claude_api_runtime.py import AgentRuntime từ đây ở top-level; import top-level
# hai chiều sẽ gây circular ImportError khi claude_api_runtime được nạp trước.
def __getattr__(name: str):
    if name == "ClaudeApiRuntime":
        from .claude_api_runtime import ClaudeApiRuntime  # noqa: PLC0415
        return ClaudeApiRuntime
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _get_claude_api_runtime_class():
    from .claude_api_runtime import ClaudeApiRuntime  # noqa: PLC0415
    return ClaudeApiRuntime


class OpenAIApiRuntime(AgentRuntime):
    """Placeholder — không thuộc scope dự án."""

    def run(self, agent_id, fixture_id, input_data, context=None):
        raise RuntimeError("OpenAIApiRuntime không thuộc scope EBM Copilot.")

    def get_runtime_type(self) -> RuntimeTypeEnum:
        return RuntimeTypeEnum.OPENAI_API

    def is_api_runtime(self) -> bool:
        return True


class LocalModelRuntime(AgentRuntime):
    """Placeholder — cần setup riêng (Ollama/llama.cpp). Chưa implement."""

    def run(self, agent_id, fixture_id, input_data, context=None):
        raise RuntimeError("LocalModelRuntime chưa implement. Dùng MockAgentRuntime.")

    def get_runtime_type(self) -> RuntimeTypeEnum:
        return RuntimeTypeEnum.LOCAL_MODEL

    def is_api_runtime(self) -> bool:
        return True
