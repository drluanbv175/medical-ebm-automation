"""
retry_loop.py — Vòng lặp retry Python thực sự cho pipeline nghiên cứu

Cung cấp cơ chế retry có cấu trúc (không chỉ là prompt instruction) để
orchestrator có thể thực sự gọi lại agent sau khi guardrail phát hiện 🔴.

Sử dụng trong pipeline:
    from tools.retry_loop import RetryLoop, GuardrailResult, EscalateToUser

    loop = RetryLoop(study="TEN-DE-TAI", gate="G6", max_retries=3)
    result = loop.run(
        agent_fn=my_agent_fn,          # fn(context) -> str output
        check_fn=my_guardrail_fn,      # fn(output) -> GuardrailResult
        initial_context={"...": "..."}
    )
    # result.output = đầu ra đã pass guardrail
    # result.retries_used = số lần đã retry

Tích hợp với _TU-CHINH-SUA-PROTOCOL.md §2 (BẢNG AUTO-FIX).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# KIỂU DỮ LIỆU
# ════════════════════════════════════════════════════════════════════════════

class ErrorSeverity(Enum):
    AUTO_FIX = "auto_fix"         # Tự sửa được (R1, R4-R8, XGATE)
    ESCALATE_HARD = "escalate"    # Phải báo bác sĩ ngay (PII, vượt cổng)
    WAIT_INPUT = "wait_input"     # Cần input đời thực (IRB/data/SAP/auth)


@dataclass
class ErrorItem:
    code: str              # R1, R2, R3, XGATE-a, A-code, Q2, G4-lock...
    message: str           # Mô tả cụ thể
    severity: ErrorSeverity
    fix_agent: str = ""    # Agent có thể sửa (nếu AUTO_FIX)
    location: str = ""     # Vị trí trong output (nếu biết)


@dataclass
class GuardrailResult:
    passed: bool
    errors: list[ErrorItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def must_escalate(self) -> bool:
        return any(e.severity == ErrorSeverity.ESCALATE_HARD for e in self.errors)

    @property
    def needs_real_input(self) -> bool:
        return any(e.severity == ErrorSeverity.WAIT_INPUT for e in self.errors)

    @property
    def auto_fixable_errors(self) -> list[ErrorItem]:
        return [e for e in self.errors if e.severity == ErrorSeverity.AUTO_FIX]

    def summary(self) -> str:
        if self.passed:
            return "ĐẠT ✅"
        lines = [f"TRẢ-VỀ-SỬA ({len(self.errors)} lỗi):"]
        for e in self.errors:
            lines.append(f"  🔴 [{e.code}] {e.message} ({e.severity.value})")
        return "\n".join(lines)


@dataclass
class RetryResult:
    success: bool
    output: Optional[str]
    final_check: Optional[GuardrailResult]
    retries_used: int
    escalation_reason: Optional[str] = None
    audit_log: list[dict] = field(default_factory=list)


class EscalateToUser(Exception):
    def __init__(self, errors: list[ErrorItem], after_retries: int):
        self.errors = errors
        self.after_retries = after_retries
        super().__init__(f"Leo thang sau {after_retries} vòng: {[e.code for e in errors]}")


# ════════════════════════════════════════════════════════════════════════════
# BẢNG AUTO-FIX (đồng bộ _TU-CHINH-SUA-PROTOCOL.md §2)
# ════════════════════════════════════════════════════════════════════════════

# Ánh xạ error code → (severity, fix_agent)
ERROR_ROUTING_TABLE: dict[str, tuple[ErrorSeverity, str]] = {
    "R1":       (ErrorSeverity.AUTO_FIX, "tra-cuu-chung-cu + kiem-chung-trich-dan"),
    "R1b":      (ErrorSeverity.AUTO_FIX, "agent-goc (bổ nguồn thật)"),
    "R2":       (ErrorSeverity.ESCALATE_HARD, "DỪNG NGAY — PII phát hiện"),
    "R3":       (ErrorSeverity.ESCALATE_HARD, "DỪNG NGAY — vượt cổng cứng"),
    "R4":       (ErrorSeverity.AUTO_FIX, "tham-dinh-grade-nnt hoặc xóa nhãn"),
    "R5":       (ErrorSeverity.AUTO_FIX, "agent-goc (tách 2 trục)"),
    "R6":       (ErrorSeverity.AUTO_FIX, "agent-goc (gắn nhãn [CẦN…])"),
    "R7":       (ErrorSeverity.AUTO_FIX, "agent-goc (thêm disclaimer)"),
    "R8":       (ErrorSeverity.AUTO_FIX, "phan-tich-thong-ke (bổ CI)"),
    "XGATE-a":  (ErrorSeverity.AUTO_FIX, "bien-so-nghien-cuu → quan-ly-du-lieu"),
    "XGATE-b":  (ErrorSeverity.AUTO_FIX, "thiet-ke-nghien-cuu (chỉnh SAP)"),
    "XGATE-c":  (ErrorSeverity.AUTO_FIX, "co-mau-nghien-cuu"),
    "A-code":   (ErrorSeverity.AUTO_FIX, "agent phụ trách (tra bảng A _KIEM-TOAN)"),
    "Q2":       (ErrorSeverity.ESCALATE_HARD, "bác sĩ phán định — sai guideline"),
    "Q5":       (ErrorSeverity.ESCALATE_HARD, "bác sĩ phán định — nguy cơ hại"),
    "G2-lock":  (ErrorSeverity.WAIT_INPUT, "chờ phê duyệt IRB thật"),
    "G4-lock":  (ErrorSeverity.WAIT_INPUT, "chờ xác nhận KHÓA SAP"),
    "G5-data":  (ErrorSeverity.WAIT_INPUT, "chờ file dữ liệu thật"),
    "G9-auth":  (ErrorSeverity.WAIT_INPUT, "chờ khai báo liêm chính"),
    # R9-R12: THÊM 2026-07-04 để nối tools/eval/run_eval.py (chấm rule-based CAFÉ-S)
    # vào MỘT bảng routing dùng chung — trước đây run_eval.py kiểm được các lỗi EBM
    # đặc thù này (source_has_year/WHO AWaRe/suy nhân quả/cờ đỏ) nhưng KHÔNG có mã
    # chuẩn để định tuyến agent sửa, buộc LLM tự suy diễn lại mỗi lần (vá khoảng
    # trống A6 — retry_loop trước đây là thư viện không ai import).
    "R9":       (ErrorSeverity.AUTO_FIX, "tra-cuu-chung-cu (bổ năm/phiên bản nguồn)"),
    "R10":      (ErrorSeverity.AUTO_FIX, "ke-don-an-toan (xét WHO AWaRe khi có kháng sinh)"),
    "R11":      (ErrorSeverity.ESCALATE_HARD, "DỪNG NGAY — suy nhân quả vượt thiết kế cắt ngang/quan sát"),
    "R12":      (ErrorSeverity.ESCALATE_HARD, "DỪNG NGAY — thiếu cờ đỏ/safety-net bắt buộc (Q3/Q5)"),
    # R13: THÊM 2026-07-04 — mã hóa _CAU-HOI-AN-TOAN-BAT-BUOC.md (S1 tự sát/S2 thai kỳ)
    # từ phán đoán LLM thuần túy (tham-dinh-dau-ra §3ter) thành check rule-based thật.
    "R13":      (ErrorSeverity.ESCALATE_HARD,
                 "DỪNG NGAY — thiếu câu hỏi an toàn bắt buộc (sang-loc-co-do + ke-don-an-toan hỏi lại)"),
    # R14: THÊM 2026-07-07 — tham-dinh-dau-ra.md §3/§8 định nghĩa R14 (an toàn kê đơn:
    # tương tác/CCĐ/chỉnh liều) là HARD-RED đối xứng R12/R13, nhưng bảng này trước đây
    # THIẾU entry cho R14 → classify_error() fallback về AUTO_FIX/"agent-goc" thay vì
    # ESCALATE_HARD, ngược hẳn hành vi tài liệu mô tả (phát hiện qua audit đối kháng).
    "R14":      (ErrorSeverity.ESCALATE_HARD,
                 "DỪNG NGAY — thiếu rà an toàn kê đơn (tương tác/CCĐ/chỉnh liều) → ke-don-an-toan"),
}

# ════════════════════════════════════════════════════════════════════════════
# ÁNH XẠ R-CODE → MÃ LESSONS LEDGER (thêm 2026-07-08 — Prompt 4 wiring)
# ════════════════════════════════════════════════════════════════════════════
# Cầu nối 1 CHIỀU: mã R (kỹ thuật nội bộ, dùng ở ERROR_ROUTING_TABLE/CHECK_ID_TO_RCODE/
# test_classify.py — KHÔNG đổi tên để không vỡ test suite hiện có) → mã ledger có kiểm
# soát (dùng ở .claude/agents/_LESSONS-LEDGER-TAXONOMY.md, ghi vào LEDGER_LESSONS.jsonl
# qua so-cai-ghi-nho.md §3c). Quyết định vận hành: xem
# .claude/agents/_RUBRIC-EVALUATE-CUNG-QA-GATE.md §7 và
# observability/LEDGER_RUBRIC_RECONCILIATION_2026-07-08.md cho lý do + bằng chứng.
# R7/R8 CHỦ Ý không có mã ledger (đã bàn trong reconciliation — mức AUTO_FIX, rủi ro
# thấp hơn nhiều so an toàn lâm sàng trực tiếp, giữ như check định dạng độc lập).
RCODE_TO_LESSON_CODE: dict[str, str] = {
    "R1":  "CIT-GHOST",
    "R1b": "GAP-MISSING",
    "R2":  "SEC-PII",
    "R3":  "SEC-BYPASS",
    "R4":  "GRD-SELF",
    "R5":  "GRD-CONF",
    "R6":  "GAP-MISSING",
    "R9":  "SRC-STALE",
    "R10": "DRG-ABX",
    "R11": "INFER-CAUSAL",
    "R12": "CLIN-REDFLAG",
    "R13": "CLIN-SAFETYQ",
    "R14": "DRG-INCOMPLETE",
}


def to_lesson_code(rcode: str) -> str | None:
    """Tra mã ledger tương ứng với 1 mã R — trả None nếu R-code không có mã ledger
    (vd R7/R8, chủ ý chưa đưa vào ledger — xem bảng trên)."""
    return RCODE_TO_LESSON_CODE.get(rcode)


def classify_error(code: str, message: str = "") -> ErrorItem:
    """Tạo ErrorItem từ error code, tra ROUTING TABLE."""
    routing = ERROR_ROUTING_TABLE.get(code)
    if routing:
        severity, fix_agent = routing
    else:
        severity = ErrorSeverity.AUTO_FIX
        fix_agent = "agent-goc"
    return ErrorItem(code=code, message=message, severity=severity, fix_agent=fix_agent)


# ════════════════════════════════════════════════════════════════════════════
# RETRY LOOP
# ════════════════════════════════════════════════════════════════════════════

class RetryLoop:
    """
    Thực thi agent với retry logic thật (vòng Python, không chỉ là prompt).

    Params:
        study:       Tên đề tài (dùng đặt tên log)
        gate:        Cổng hiện tại (G0–G9)
        max_retries: Số lần tối đa (mặc định 3 theo _TU-CHINH-SUA-PROTOCOL.md §1)
        log_dir:     Thư mục ghi audit log (None = không ghi)
    """

    def __init__(self, study: str = "STUDY", gate: str = "G0",
                 max_retries: int = 3, log_dir: Optional[Path] = None):
        self.study = study
        self.gate = gate
        self.max_retries = max_retries
        self.log_dir = log_dir
        self._audit: list[dict] = []

    def run(
        self,
        agent_fn: Callable[[dict], str],
        check_fn: Callable[[str], GuardrailResult],
        initial_context: dict,
        artifact_code: str = "",
    ) -> RetryResult:
        """
        Chạy agent → kiểm guardrail → retry nếu cần, tối đa max_retries lần.

        agent_fn(context) → str output
        check_fn(output)  → GuardrailResult
        """
        context = dict(initial_context)
        context["_retry_meta"] = {"study": self.study, "gate": self.gate, "attempt": 1}

        for attempt in range(1, self.max_retries + 1):
            context["_retry_meta"]["attempt"] = attempt
            self._log(f"Vòng {attempt}/{self.max_retries}", context)

            try:
                output = agent_fn(context)
            except Exception as e:
                self._log(f"Agent lỗi vòng {attempt}", {"error": str(e)})
                if attempt == self.max_retries:
                    return RetryResult(
                        success=False, output=None, final_check=None,
                        retries_used=attempt,
                        escalation_reason=f"Agent exception sau {attempt} lần: {e}",
                        audit_log=self._audit
                    )
                continue

            check = check_fn(output)
            self._log(f"Guardrail vòng {attempt}", {"passed": check.passed,
                                                      "errors": [e.code for e in check.errors]})

            if check.passed:
                self._save_audit()
                return RetryResult(
                    success=True, output=output, final_check=check,
                    retries_used=attempt - 1, audit_log=self._audit
                )

            # Dừng ngay nếu phải leo thang (PII, vượt cổng, cần input thật)
            if check.must_escalate or check.needs_real_input:
                reason = self._escalation_message(check, attempt)
                self._save_audit()
                return RetryResult(
                    success=False, output=output, final_check=check,
                    retries_used=attempt,
                    escalation_reason=reason,
                    audit_log=self._audit
                )

            # Chuẩn bị context cho vòng kế (bổ thêm danh sách lỗi cụ thể)
            if attempt < self.max_retries:
                context = self._augment_context_with_errors(context, check, attempt)

        # Hết max_retries vẫn lỗi → leo thang
        final_check = check_fn(output) if "output" in dir() else None  # type: ignore
        reason = self._escalation_message(final_check, self.max_retries)
        self._save_audit()
        return RetryResult(
            success=False, output=output if "output" in dir() else None,  # type: ignore
            final_check=final_check, retries_used=self.max_retries,
            escalation_reason=reason, audit_log=self._audit
        )

    def _augment_context_with_errors(self, ctx: dict, check: GuardrailResult, attempt: int) -> dict:
        """Thêm danh sách 🔴 vào context để agent sửa đúng vòng kế."""
        new_ctx = dict(ctx)
        error_list = "\n".join(
            f"🔴 [{e.code}] {e.message} → sửa bằng: {e.fix_agent}"
            for e in check.auto_fixable_errors
        )
        new_ctx["_self_correction"] = {
            "attempt": attempt,
            "max_retries": self.max_retries,
            "errors_to_fix": [{"code": e.code, "message": e.message, "fix_agent": e.fix_agent}
                               for e in check.auto_fixable_errors],
            "instruction": (
                f"[VÒNG TỰ SỬA {attempt + 1}/{self.max_retries}]\n"
                f"Lỗi 🔴 cần sửa NGAY:\n{error_list}\n"
                f"Sửa ĐÚNG các mục trên — KHÔNG thay nội dung khoa học/số liệu khác."
            )
        }
        return new_ctx

    def _escalation_message(self, check: Optional[GuardrailResult], after: int) -> str:
        if check is None:
            return f"Agent không trả kết quả sau {after} lần"
        lines = [f"⚠ LEO THANG SAU {after} VÒNG TỰ SỬA — {self.study} · Cổng {self.gate}"]
        for e in check.errors:
            lines.append(f"  🔴 [{e.code}] {e.message}")
            if e.severity == ErrorSeverity.ESCALATE_HARD:
                lines.append(f"     → Cần bác sĩ: {e.fix_agent}")
            elif e.severity == ErrorSeverity.WAIT_INPUT:
                lines.append(f"     → Cần input đời thực: {e.fix_agent}")
        lines.append("Bước tiếp theo: xem danh sách 🔴 ở trên và xử lý từng mục.")
        return "\n".join(lines)

    def _log(self, event: str, data: dict):
        entry = {"ts": datetime.now().isoformat(), "event": event, **data}
        self._audit.append(entry)
        logger.debug(f"[RetryLoop {self.gate}] {event}: {data}")

    def _save_audit(self):
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"retry_audit_{self.study}_{self.gate}_{ts}.json"
            log_file.write_text(
                json.dumps(self._audit, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )


# ════════════════════════════════════════════════════════════════════════════
# HÀM TIỆN ÍCH — tạo GuardrailResult từ text output đơn giản
# ════════════════════════════════════════════════════════════════════════════

def simple_guardrail(output: str) -> GuardrailResult:
    """
    Guardrail đơn giản dựa trên text matching.
    Dùng khi không có agent tham-dinh-dau-ra trong pipeline Python.
    """
    errors = []
    warnings = []

    text_lower = output.lower()

    # R2 — PII
    pii_patterns = ["tên bệnh nhân", "ngày sinh", "cccd", "số hồ sơ", "địa chỉ", "sdt"]
    for p in pii_patterns:
        if p in text_lower:
            errors.append(classify_error("R2", f"Phát hiện PII candidate: '{p}'"))
            break

    # R7 — Disclaimer
    if "cần bác sĩ kiểm chứng" not in text_lower:
        errors.append(classify_error("R7", "Thiếu disclaimer 'Cần bác sĩ kiểm chứng.'"))

    # R1 — Thiếu nguồn
    has_citation = bool(
        ("pmid" in text_lower) or ("doi" in text_lower) or
        ("[cần kiểm chứng]" in text_lower) or ("[cần bổ sung]" in text_lower)
    )
    if not has_citation:
        warnings.append("Không tìm thấy PMID/DOI — kiểm thủ công")

    # R8 — p-value đơn độc
    import re
    if re.search(r'\bp\s*[<=]\s*0\.\d+\b', output) and "95%" not in output and "CI" not in output.upper():
        errors.append(classify_error("R8", "Báo p-value nhưng thiếu 95%CI"))

    return GuardrailResult(passed=len(errors) == 0, errors=errors, warnings=warnings)


# ════════════════════════════════════════════════════════════════════════════
# CLI — demo / test nhanh
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test RetryLoop với ví dụ đơn giản")
    parser.add_argument("--demo", action="store_true", help="Chạy demo với mock agent")
    args = parser.parse_args()

    if args.demo:
        call_count = [0]

        def mock_agent(ctx: dict) -> str:
            call_count[0] += 1
            attempt = ctx.get("_retry_meta", {}).get("attempt", 1)
            if attempt < 3:
                return f"Bản thảo vòng {attempt} (thiếu disclaimer và PMID)"
            return "Kết quả đầy đủ với PMID: 12345678. Cần bác sĩ kiểm chứng."

        loop = RetryLoop(study="DEMO", gate="G6", max_retries=3)
        result = loop.run(
            agent_fn=mock_agent,
            check_fn=simple_guardrail,
            initial_context={"prompt": "Tạo tóm tắt kết quả"},
        )

        print(f"\nKết quả: {'✅ PASS' if result.success else '❌ FAIL'}")
        print(f"Đã dùng {result.retries_used} vòng retry / {call_count[0]} lần gọi agent")
        if result.escalation_reason:
            print(f"\nLý do leo thang:\n{result.escalation_reason}")
        if result.output:
            print(f"\nĐầu ra cuối:\n{result.output}")
    else:
        print("Thư viện retry_loop.py đã sẵn sàng.")
        print("Dùng --demo để xem ví dụ, hoặc import RetryLoop vào pipeline của bạn.")
