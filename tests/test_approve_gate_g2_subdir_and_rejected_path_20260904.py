"""Hồi quy 2 phát hiện của Workflow đối kháng đa-agent vòng 2 (2026-09-03/04) trong
tools/approve_gate.py — cùng miền với test_approve_gate_g4_artifact_path_check_20260903.py
(chốt full-path artifact cho các cổng cứng), lần này bắt hai khoảng hở CÒN SÓT:

  #1 HIGH — G2 là cổng DUY NHẤT trong 6 cổng cứng chấp nhận ``--artifact`` ĐÚNG TÊN
     nhưng SAI VỊ TRÍ (thư mục con). ``_prepare_g2_attestation()`` cũ chỉ kiểm (a)
     containment lỏng (``relative_to`` không ném lỗi — tức nằm Ở ĐÂU ĐÓ trong cây
     study_dir, không cần trực tiếp trong đó) và (b) so khớp TÊN file. Một file
     ``exports/<study>/thu-muc-con/G2_A3_ETHICS_PACKAGE_<study>.md`` mang đúng tên
     canonical vẫn ký được — trong khi vị trí canonical thật
     (``study_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"``, nơi DUY NHẤT mà
     g2/g5/g9/g10_quality_gate.py, run_g6_auto.py, run_stats_analysis.py,
     gen_research_docx.py đọc) chưa từng bị đụng tới — ghi một bản ghi ledger đã
     niêm phong với evidence_hash KHÔNG khớp nội dung file canonical thật.

  #2 LOW — nhánh REJECTED/CONDITIONAL của G2/G5/G8/G9/G10 (G4 là ngoại lệ, đã vá
     2026-09-03) trước đây KHÔNG kiểm ``--artifact`` nào cả: chấp nhận MỘT FILE BẤT
     KỲ, ở BẤT KỲ ĐÂU trên đĩa (kể cả ngoài toàn bộ exports/), nội dung không liên
     quan, vẫn ký + ghi ledger + niêm phong thành công. Không mở được cổng (REJECTED
     không bao giờ làm ``ledger_approved()`` trả True) nhưng evidence_hash của một
     bản ghi THU HỒI mất hết ý nghĩa "nội dung nào bị từ chối".

Nguyên tắc thiết kế test — GIỐNG HỆT bài học đã rút ra khi viết bộ G4 (xem docstring
file đó): mọi test "reject" cho nhánh APPROVED monkeypatch GxQ.evaluate_study để
CÔ LẬP đúng chốt artifact-path khỏi mọi tiêu chí nội dung khác — nếu không, test có
thể bị "che" bởi một lý do chặn khác và không mutation-sensitive đúng chỗ.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import g9_quality_gate as G9Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402

_STUDY = "PYTEST-G2-SUBDIR-REJECTED-PATH-20260904"

# Đủ nội dung không có "[CẦN" — tránh G2Q.unresolved_critical_placeholders() gây
# nhiễu vào phép kiểm artifact-path đang được cô lập.
_CLEAN_G2_PACKAGE = (
    "# Hồ sơ đạo đức\n"
    "Nội dung sạch placeholder — cô lập phép kiểm artifact-path khỏi các luật nội "
    "dung khác của _prepare_g2_attestation.\n"
)

# Bộ cờ --g2-* tối thiểu để _prepare_g2_attestation() KHÔNG báo lỗi nào khác ngoài
# artifact-path — dùng RETROSPECTIVE_SECONDARY_DATA để tránh phải khai thêm registry.
_G2_MIN_FLAGS = [
    "--g2-approval-number", "IRB-2026-001",
    "--g2-approval-date", "2026-01-01",
    "--g2-no-expiry-confirmed",
    "--g2-protocol-version", "1.0",
    "--g2-icf-waiver-approved",
    "--g2-ethics-decision", "APPROVED",
    "--g2-recruitment-mode", "RETROSPECTIVE_SECONDARY_DATA",
    "--g2-registration-status", "NOT_REQUIRED",
]


@pytest.fixture()
def study_dir():
    d = REPO_ROOT / "exports" / _STUDY
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def _quality_gates_report_ready(monkeypatch):
    """Cô lập chốt artifact-path khỏi mọi tiêu chí NỘI DUNG khác của từng GxQ —
    cùng lý do đã ghi ở test_approve_gate_g4_artifact_path_check_20260903.py."""
    monkeypatch.setattr(
        G2Q, "evaluate_study",
        lambda *a, **k: {"status": G2Q.STATUS_APPROVED, "automatic_criteria": []},
    )
    monkeypatch.setattr(
        G5Q, "evaluate_study",
        lambda *a, **k: {"status": G5Q.STATUS_READY, "automatic_criteria": []},
    )
    monkeypatch.setattr(
        G8Q, "evaluate_study",
        lambda *a, **k: {"status": G8Q.STATUS_PENDING, "automatic_criteria": []},
    )
    monkeypatch.setattr(
        G9Q, "evaluate_study",
        lambda *a, **k: {"status": G9Q.STATUS_READY, "automatic_criteria": []},
    )
    monkeypatch.setattr(
        G10Q, "evaluate_study",
        lambda *a, **k: {"status": G10Q.STATUS_READY, "automatic_criteria": []},
    )


def _run_main(monkeypatch, *args) -> int:
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", *args])
    return AG.main()


def _ledger_records(study_dir: Path) -> list:
    p = study_dir / "approval_ledger.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


# ════════════════════════════════════════════════════════════════════════════
# #1 HIGH — G2 chấp nhận đúng tên nhưng sai vị trí (thư mục con)
# ════════════════════════════════════════════════════════════════════════════

def test_g2_rejects_correct_filename_in_wrong_subdirectory(monkeypatch, study_dir):
    """★★ Ca chính của lỗ hổng: file MANG ĐÚNG TÊN canonical, nội dung sạch, đặt
    trong một THƯ MỤC CON của study_dir. Trước bản vá, ca này ký sạch (rc=0)."""
    subdir = study_dir / "thu-muc-con-nguy-hiem"
    subdir.mkdir()
    decoy = subdir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    decoy.write_text(_CLEAN_G2_PACKAGE, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G2", "--artifact", str(decoy),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", *_G2_MIN_FLAGS,
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []
    # Vị trí canonical thật chưa từng bị đụng tới.
    assert not (study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md").exists()


def test_g2_rejects_correct_filename_for_wrong_study(monkeypatch, study_dir):
    """Tên file đúng KHUÔN nhưng thuộc đề tài KHÁC (mã đề tài trong tên lệch với
    --study) vẫn phải bị chặn — cùng khuôn test_g4_rejects_canonical_name_used_for_wrong_study."""
    wrong = study_dir / "G2_A3_ETHICS_PACKAGE_MOT-DE-TAI-KHAC.md"
    wrong.write_text(_CLEAN_G2_PACKAGE, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G2", "--artifact", str(wrong),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", *_G2_MIN_FLAGS,
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []


def test_g2_still_rejects_artifact_entirely_outside_study_dir(monkeypatch, study_dir, tmp_path):
    """Đối chứng: file đặt NGOÀI study_dir hoàn toàn vẫn phải bị chặn (hành vi
    containment cũ vẫn đúng — lỗ hổng CHỈ nằm ở thư mục CON, không phải thiếu
    containment hoàn toàn)."""
    elsewhere = tmp_path / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    elsewhere.write_text(_CLEAN_G2_PACKAGE, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G2", "--artifact", str(elsewhere),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", *_G2_MIN_FLAGS,
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []


def test_g2_accepts_correct_canonical_artifact_path(monkeypatch, study_dir):
    """Đối chứng dương tính: đúng tên canonical TRỰC TIẾP trong study_dir vẫn ký
    được bình thường — bản vá không được chặn oan luồng hợp lệ."""
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text(_CLEAN_G2_PACKAGE, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G2", "--artifact", str(artifact),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", *_G2_MIN_FLAGS,
    )
    assert rc == 0, artifact.read_text(encoding="utf-8")
    records = _ledger_records(study_dir)
    assert len(records) == 1 and records[0]["gate_id"] == "G2"
    # Nội dung file đã được ghi attestation bởi _prepare_g2_attestation trước khi
    # hash — evidence_hash phải khớp ĐÚNG bytes hiện có trên đĩa sau bước đó.
    assert records[0]["evidence_hash"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# #2 LOW — nhánh REJECTED/CONDITIONAL trước đây không kiểm --artifact
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("gate,role,checkpoint_name", [
    ("G2", "IRB", None),
    ("G5", "DATA_MANAGER", "G5_checkpoint.json"),
    ("G8", "PEER_REVIEWER", None),
    ("G9", "PI", "G9_checkpoint.json"),
    ("G10", "PI", "G10_checkpoint.json"),
])
def test_rejected_decision_still_rejects_artifact_entirely_outside_exports(
    monkeypatch, study_dir, tmp_path, gate, role, checkpoint_name,
):
    """★★ Ca chính của phát hiện #2: --decision REJECTED với --artifact trỏ tới
    MỘT FILE NGOÀI exports/<study>/ HOÀN TOÀN, nội dung không liên quan gì tới
    cổng đang từ chối. Trước bản vá, ca này ký sạch cho cả 5 cổng (G2/G5/G8/G9/G10)."""
    rogue = tmp_path / "noi_dung_hoan_toan_khong_lien_quan.txt"
    rogue.write_text("nội dung rác, không phải checkpoint/attestation thật", encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", gate, "--artifact", str(rogue),
        "--reviewer-role", role, "--reviewer-ref", f"{role}-01",
        "--decision", "REJECTED",
    )
    assert rc != 0, f"{gate} REJECTED lẽ ra phải bị chặn — artifact ngoài exports/ hoàn toàn"
    assert _ledger_records(study_dir) == []


@pytest.mark.parametrize("gate,role,artifact_factory", [
    ("G5", "DATA_MANAGER", lambda d: (d / "G5_checkpoint.json", "{}")),
    ("G8", "PEER_REVIEWER", lambda d: (d / G8Q.presubmission_artifact_name(_STUDY), "# presubmission\n")),
    ("G9", "PI", lambda d: (d / G9Q.CHECKPOINT_JSON, "{}")),
    ("G10", "PI", lambda d: (d / G10Q.CHECKPOINT_JSON, "{}")),
])
def test_rejected_decision_with_canonical_artifact_still_succeeds(
    monkeypatch, study_dir, gate, role, artifact_factory,
):
    """Đối chứng dương tính cho phát hiện #2: REJECTED trên đúng file canonical
    (kịch bản thật — từ chối một hồ sơ CÓ THẬT) vẫn phải ký được bình thường,
    không bị chặn oan bởi chốt path mới thêm."""
    path, content = artifact_factory(study_dir)
    path.write_text(content, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", gate, "--artifact", str(path),
        "--reviewer-role", role, "--reviewer-ref", f"{role}-01",
        "--decision", "REJECTED",
    )
    assert rc == 0, path.read_text(encoding="utf-8")
    records = _ledger_records(study_dir)
    assert len(records) == 1 and records[0]["gate_id"] == gate
    assert records[0]["decision"] == "REJECTED"
