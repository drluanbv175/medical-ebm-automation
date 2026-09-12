r"""Hồi quy phát hiện #4 (audit vòng 34, 2026-09-06) trong
scripts/phase_2b_live_source_smoke_test.py — biểu thức "safe_status" cũ là
một HẰNG ĐÚNG (tautology logic thuần), khiến smoke test không bao giờ phát
hiện được điều nó tuyên bố kiểm.

CƠ CHẾ LỖI (TRƯỚC bản vá), dòng cũ trong main():
    safe_status = (
        result.status is not CitationVerificationStatus.VERIFIED
        or result.safe_for_verified_evidence
    )

``CitationVerificationResult.safe_for_verified_evidence`` (app/evidence/
citation_verification.py) được định nghĩa CHÍNH XÁC là::

    @property
    def safe_for_verified_evidence(self) -> bool:
        return self.status is CitationVerificationStatus.VERIFIED

Đặt X = (status is VERIFIED). Biểu thức cũ là "(not X) or X" — theo luật
loại trừ thứ ba, đây là HẰNG ĐÚNG với MỌI giá trị của status, không phụ
thuộc bất kỳ dữ kiện thực tế nào (nguồn có unavailable/timeout hay không).
Do đó ``unsafe = not safe_status`` KHÔNG BAO GIỜ trở thành True, và
``main()`` LUÔN trả mã 0 (PASS) — smoke test hoàn toàn không thể phát hiện
được điều nó tự khai trong report: ``"policy":
"unavailable_or_timeout_must_not_be_verified"``.

BẢN VÁ: trích xuất phép tính này thành hàm thuần ``_is_safe(result_status,
health_status)``, đối chiếu ĐÚNG tín hiệu mà policy khai — health_status
THẬT của adapter (do SourceHealthMonitor.failure() ghi khi lookup ném
exception/timeout hoặc source tự báo unavailable — xem
app/evidence/live_adapters/base.py) — với status verifier trả về: unsafe
khi và chỉ khi nguồn unavailable NHƯNG verifier vẫn báo VERIFIED.

Test này gọi THẲNG hàm thuần ``_is_safe()`` (nạp module bằng
importlib.util.spec_from_file_location + đăng ký sys.modules TRƯỚC
exec_module — không cần mạng, không cần argparse, không đụng adapter
thật) — tách biệt hoàn toàn khỏi test hiện có
(tests/test_phase_2b_live_source_smoke_test.py, nếu có) vốn kiểm hành vi
CLI/mạng."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "phase_2b_live_source_smoke_test.py"


def _nap():
    spec = importlib.util.spec_from_file_location(
        "phase_2b_live_source_smoke_test_vong34_test", SCRIPT_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase_2b_live_source_smoke_test_vong34_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCaChinhToHopNguyHiemPhaiBiBatDuoc:
    """★★★ Ca chính — nguồn health_status="unavailable" mà verifier vẫn báo
    VERIFIED PHẢI bị coi là KHÔNG an toàn (False)."""

    def test_verified_nhung_nguon_unavailable_la_khong_an_toan(self):
        mod = _nap()
        S = mod.CitationVerificationStatus
        assert mod._is_safe(S.VERIFIED, "unavailable") is False, (
            "TRƯỚC bản vá: safe_status = 'status is not VERIFIED or "
            "safe_for_verified_evidence' là hằng đúng (vì "
            "safe_for_verified_evidence CHÍNH LÀ 'status is VERIFIED'), nên "
            "tổ hợp nguy hiểm 'nguồn unavailable nhưng verifier báo "
            "VERIFIED' không bao giờ bị phát hiện."
        )


class TestDoiChungCacToHopAnToan:
    """Đối chứng — các tổ hợp hợp lệ vẫn phải được coi là AN TOÀN (True)."""

    def test_verified_va_nguon_ok_la_an_toan(self):
        mod = _nap()
        S = mod.CitationVerificationStatus
        assert mod._is_safe(S.VERIFIED, "ok") is True

    def test_source_unavailable_status_va_health_unavailable_la_an_toan(self):
        # Trường hợp bình thường nhất: verifier ĐÃ đúng đắn hạ status
        # xuống SOURCE_UNAVAILABLE khi nguồn hỏng — không phải tổ hợp
        # nguy hiểm.
        mod = _nap()
        S = mod.CitationVerificationStatus
        assert mod._is_safe(S.SOURCE_UNAVAILABLE, "unavailable") is True

    def test_mismatch_va_nguon_ok_la_an_toan(self):
        mod = _nap()
        S = mod.CitationVerificationStatus
        assert mod._is_safe(S.MISMATCH, "ok") is True

    def test_verified_va_health_unknown_la_an_toan(self):
        # health_status="unknown" (giá trị mặc định trước khi có lượt tra
        # cứu nào) KHÔNG phải "unavailable" — không được coi là nguy hiểm.
        mod = _nap()
        S = mod.CitationVerificationStatus
        assert mod._is_safe(S.VERIFIED, "unknown") is True
