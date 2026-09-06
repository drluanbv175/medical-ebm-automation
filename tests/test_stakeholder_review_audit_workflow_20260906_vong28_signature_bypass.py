"""Hồi quy phát hiện #1 (NGHIÊM TRỌNG) của Workflow đối kháng đa-agent 2026-09-06
(vòng 28) trong tools/stakeholder_review_audit.py — công cụ "CHỈ ĐỂ XEM" trạng thái
stakeholder approval có thể báo [PASS] cho một cổng mà cổng thật (gate_contract.py)
coi là CHƯA duyệt.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _print_real_ledger_status(approval_ledger, gates):
        for gate_id in gates:
            status = approval_ledger.stakeholder_gate_status(gate_id)  # ← nguồn CŨ
            satisfied = bool(status.get("satisfied"))
            ...

`ApprovalLedger.stakeholder_gate_status()` (runtime/approval_ledger.py) ủy quyền cho
`check_required_stakeholder_approval()`, hàm này lọc bản ghi theo gate_id / is_synthetic
/ self-review / reviewer_role — nhưng KHÔNG BAO GIỜ gọi
`gate_contract.verify_approval_signature()`. Grep xác nhận: 0 lượt gọi hàm đó trong
toàn bộ runtime/approval_ledger.py.

Hậu quả: một bản ghi APPROVED KHÔNG có `approver_signature` (hoặc chữ ký sai/không
khớp khóa nào) vẫn được `stakeholder_review_audit.py` báo [PASS], trong khi
`gate_contract.ledger_approved()`/`gate_block_reason()` — nguồn sự thật THẬT mà
`tools/approve_gate.py` và `tools/run_g10_assemble.py` dùng để CHẶN THẬT trước khi ký
sổ cái hoặc lắp gói nộp — coi cổng đó CHƯA duyệt (thiếu điều kiện (5): chữ ký mật mã
phải khớp đúng khóa của nhóm stakeholder). Bất kỳ ai tự tay dựng một bản ghi
approval_ledger.json (kể cả vô tình, ví dụ copy từ đề tài khác rồi sửa gate_id) sẽ
thấy "[PASS] G2" từ công cụ kiểm tra tay này, dù chưa hề có ai KÝ duyệt thật.

HẠI THẬT: đây là công cụ bác sĩ/PI dùng để XEM NHANH trạng thái cổng — chính docstring
module tự nhận "Đây là công cụ BÁC SĨ dùng KIỂM TAY, nên nó TUYỆT ĐỐI không được nói
khác cổng thật" (VÁ 2026-07-27, kiểm chuỗi băm/con dấu của TOÀN VẸN SỔ CÁI). Nhưng bản
vá đó chỉ phủ được toàn vẹn CẤU TRÚC sổ cái (chain/seal) — không phủ được XÁC MINH CHỮ
KÝ của TỪNG bản ghi riêng lẻ, nên khoảng hở "PASS giả" vẫn nguyên vẹn cho tới bản vá
này: một sổ cái có chain/seal hoàn toàn hợp lệ VẪN có thể chứa một approval KHÔNG chữ
ký, và công cụ vẫn báo PASS.

BẢN VÁ: `_print_real_ledger_status()` nay tính artifact_path chuẩn cho từng gate
(_gate_artifact_path — khớp ĐÚNG hằng số/hàm hợp đồng của approve_gate.py) rồi gọi
`gate_contract.gate_block_reason(gate_id, study, artifact_path, repo_root)` — CÙNG một
hàm mà pipeline thật dùng để chặn — làm nguồn satisfied/reason DUY NHẤT.
`ApprovalLedger.stakeholder_gate_status()` chỉ còn dùng để LẤY THÊM chi tiết hiển thị
(approval_id/reviewer_role) SAU KHI đã xác nhận PASS, không bao giờ dùng để quyết định.

Nguyên tắc viết test:
1. Test TRỰC TIẾP nhất — dựng đúng kịch bản lỗ hổng (bản ghi APPROVED, đúng vai trò,
   KHÔNG chữ ký) và xác nhận CLI thật (SRA.main) báo [BLOCKED]/exit 2, không phải
   [PASS]/exit 0.
2. Đối chứng bắt buộc — xác nhận nguồn CŨ (stakeholder_gate_status) vẫn tự nó báo
   satisfied=True cho ĐÚNG bản ghi này (chứng minh lỗ hổng nằm ở CHỖ NÀO được tin
   dùng để quyết định, không phải bản thân stakeholder_gate_status() bị sửa/hỏng).
3. Đường PASS thật (có ký + artifact khớp hash) phải vẫn còn hoạt động — không được
   biến công cụ này thành luôn luôn BLOCKED.
4. Mutation test thủ công (xem ghi chú cuối file) xác nhận: phục hồi
   tools/stakeholder_review_audit.py về đúng git HEAD trước bản vá này làm ca #1 và #2
   thất bại (in ra [PASS] G2 + exit 0), các ca PASS-thật (#3) và đối chứng (#2's phần
   stakeholder_gate_status) không đổi — rồi khôi phục lại bản vá, xác nhận cả 3 lớp
   test xanh trở lại.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = _REPO_ROOT / "tools"
for _p in (str(_REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402
import stakeholder_review_audit as SRA  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402
from tests.g5_test_helpers import (  # noqa: E402
    append_signed_approval,
    configure_test_signing_key,
)

_STUDY = "__vong28_bh_signature_bypass_selftest_delete_me__"


@pytest.fixture()
def study_dir():
    path = _REPO_ROOT / "exports" / _STUDY
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _make_unsigned_approved_g2_record_with_artifact(study_dir: Path) -> Path:
    """Dựng ĐÚNG kịch bản lỗ hổng: một artifact G2 thật trên đĩa (hash sẽ khớp
    evidence_hash) và một bản ghi APPROVED đúng vai trò IRB, nhưng KHÔNG chữ ký
    (approver_signature=None — giá trị mặc định của make_human_approval khi không
    truyền, đúng cách một bản ghi ledger dựng tay/thiếu bước ký sẽ trông như vậy)."""
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    content = "Ethics committee letter — bypass repro content\nCần bác sĩ kiểm chứng.\n"
    artifact.write_text(content, encoding="utf-8", newline="\n")

    ledger = ApprovalLedger()
    record = ApprovalLedger.make_human_approval(
        gate_id="G2",
        reviewer_role="IRB_ETHICS_COMMITTEE",
        reviewer_ref="IRB-BYPASS-REPRO-01",
        scope="Vong 28 signature bypass repro",
        evidence_content=content,
    )
    assert record.approver_signature is None, (
        "Fixture phải mô phỏng ĐÚNG một bản ghi KHÔNG chữ ký — nếu make_human_approval "
        "đổi hành vi mặc định (tự ký khi không truyền approver_signature) thì test này "
        "không còn tái hiện đúng lỗ hổng nữa."
    )
    ok, reason = ledger.add_approval(record)
    assert ok, reason
    ledger.to_file(study_dir / "approval_ledger.json")
    return artifact


class TestSignatureBypassBiChanDung:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. CLI thật phải BLOCKED, không PASS,
    cho một bản ghi APPROVED đúng vai trò nhưng không chữ ký."""

    def test_cli_that_bao_blocked_khong_phai_pass(self, study_dir, capsys):
        _make_unsigned_approved_g2_record_with_artifact(study_dir)

        exit_code = SRA.main(["--study", _STUDY, "--gate", "G2"])
        out = capsys.readouterr().out

        assert exit_code == 2, (
            "TRƯỚC bản vá: exit_code == 0 vì _print_real_ledger_status() tin "
            "ApprovalLedger.stakeholder_gate_status() (không xác minh chữ ký) — một "
            "bản ghi APPROVED không chữ ký vẫn được coi là đã duyệt xong."
        )
        assert "[BLOCKED] G2" in out
        assert "[PASS] G2" not in out

    def test_nguon_that_gate_contract_cung_noi_chua_duyet(self, study_dir):
        """Đối chứng độc lập với CLI: gọi thẳng gate_contract.ledger_approved() —
        nguồn sự thật mà approve_gate.py/run_g10_assemble.py dùng để chặn thật — xác
        nhận cơ chế lỗi nằm ở TẦNG DỮ LIỆU (thiếu chữ ký), không phải một lỗi hiển thị
        riêng của CLI."""
        artifact = _make_unsigned_approved_g2_record_with_artifact(study_dir)

        approved = GC.ledger_approved("G2", _STUDY, artifact, repo_root=_REPO_ROOT)

        assert approved is False


class TestDoiChungStakeholderGateStatusVanBaoSatisfiedTrue:
    """Đối chứng BẮT BUỘC — chứng minh lỗ hổng nằm ở CHỖ ĐƯỢC TIN DÙNG để quyết định,
    không phải ở bản thân ApprovalLedger.stakeholder_gate_status() bị hỏng/sửa. Hàm đó
    VẪN đúng theo đúng thiết kế của riêng nó (lọc theo gate_id/role/is_synthetic) — nó
    chỉ đơn giản chưa từng có nhiệm vụ xác minh chữ ký, và bản vá không đổi hành vi của
    nó, chỉ đổi việc CLI có còn tin nó để quyết định satisfied/exit code hay không."""

    def test_stakeholder_gate_status_tu_no_van_bao_satisfied_true(self, study_dir):
        _make_unsigned_approved_g2_record_with_artifact(study_dir)
        ledger = ApprovalLedger.from_file(study_dir / "approval_ledger.json")

        status = ledger.stakeholder_gate_status("G2")

        assert status.get("satisfied") is True, (
            "Đối chứng: nếu dòng này FAIL nghĩa là ApprovalLedger.stakeholder_gate_status() "
            "đã bị đổi hành vi ở nơi khác — bản vá của vòng 28 KHÔNG chạm tới hàm này, "
            "chỉ chạm _print_real_ledger_status() (nơi tiêu thụ nó)."
        )


class TestDuongPassThatVanConHoatDong:
    """Đối chứng bắt buộc thứ hai — bản vá KHÔNG được biến công cụ thành luôn luôn
    BLOCKED: một phê duyệt THẬT (có chữ ký khớp khóa + artifact khớp hash) vẫn phải
    báo [PASS]/exit 0."""

    def test_phe_duyet_co_ky_va_artifact_khop_van_pass(
        self, study_dir, tmp_path, monkeypatch, capsys
    ):
        configure_test_signing_key(tmp_path, monkeypatch)
        artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
        artifact.write_text(
            "Ethics committee letter — signed happy path\nCần bác sĩ kiểm chứng.\n",
            encoding="utf-8",
            newline="\n",
        )
        append_signed_approval(
            _STUDY, artifact, "G2", "IRB_ETHICS_COMMITTEE", repo_root=_REPO_ROOT
        )

        exit_code = SRA.main(["--study", _STUDY, "--gate", "G2"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "[PASS] G2" in out
