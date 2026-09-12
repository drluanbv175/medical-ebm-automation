"""Hồi quy cho phát hiện #1 của Workflow đối kháng đa-agent 2026-09-03 (đợt rà
toàn diện sau `tools/gate_contract.py::any_signing_key_available()`):

Nhánh ký G4 trong ``approve_gate.py`` là nhánh DUY NHẤT trong 6 cổng cứng
(G2/G4/G5/G8/G9/G10) thiếu phép so khớp ``--artifact`` với đường dẫn CANONICAL
của đề tài — G5 (``study_dir / "G5_checkpoint.json"``), G8
(``G8Q.presubmission_artifact_name``), G9 (``G9Q.CHECKPOINT_JSON``), G10 đều có;
G2 có cơ chế tương đương qua ``_prepare_g2_attestation``. Không có chốt này thì
``--artifact <file bất kỳ>`` vẫn ký được cho G4: chữ ký/con dấu đúng về mặt mật
mã (HMAC/Ed25519 tính trên ĐÚNG nội dung file được truyền), nhưng evidence_hash
không còn khớp NỘI DUNG SAP THẬT — phá vỡ đúng bất biến mà docstring đầu file
``approve_gate.py`` tuyên bố áp dụng cho MỌI cổng ("evidence_hash = SHA256 của
ĐÚNG nội dung file --artifact"). ``G4Q.evaluate_study()`` vẫn đọc SAP thật từ
đường dẫn canonical (tách khỏi ``evidence_content`` truyền vào từ
``--artifact``) nên hướng lệch cuối cùng là fail-closed — G4 không bao giờ hiện
LOCKED vì ``gate_contract.ledger_approved()`` sẽ thấy hash lệch khi tra lại
canonical path — nhưng bản ghi ràng buộc-sai-nội-dung vẫn nằm VĨNH VIỄN trong
sổ cái đã niêm phong, gây nhiễu sổ audit và có thể khiến bác sĩ tưởng đã ký
xong trong khi chưa (không ai đọc kỹ sẽ phân biệt được "có bản ghi trong
ledger" với "cổng thật sự LOCKED").

Bản vá thêm đúng khuôn 5 cổng kia: ``expected_artifact = study_dir /
G4Q.sap_artifact_name(args.study)``; từ chối ký nếu
``artifact_path.resolve() != expected_artifact.resolve()``, đặt TRƯỚC bước gọi
``_g4_sections_still_draft`` — và KHÔNG gạn theo ``decision == "APPROVED"``
(khác G5/G8/G9/G10): SAP là artifact DUY NHẤT hợp lệ cho cổng này bất kể ký
hay từ chối, nên phép so khớp áp dụng vô điều kiện.

★ THIẾT KẾ TEST — bài học tự rút ra bằng mutation-testing lúc viết bộ này:
lượt đầu để ``G4Q.evaluate_study`` chạy THẬT trên canonical path (vốn không
tồn tại trong các kịch bản artifact-sai) — nó CŨNG tự trả BLOCKED (thiếu
file), nên các test "reject" tưởng đang bắt lỗi CHỐT ARTIFACT-PATH thực ra bị
CHE bởi một lý do chặn khác, không mutation-sensitive đúng chỗ (một đột biến
đổi so khớp full-path thành so khớp .name không hề bị bắt). Nay MỌI test
"reject" đều monkeypatch ``G4Q.evaluate_study`` → ``STATUS_READY`` (giống hệt
đối chứng dương tính bên dưới) để cô lập: nếu chốt artifact-path bị gỡ/nới
lỏng, KHÔNG còn gì khác ngăn được ghi ledger — test khi đó mới thật sự chỉ
phụ thuộc vào đúng MỘT chốt cần khóa lại.
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
import g4_quality_gate as G4Q  # noqa: E402

_STUDY = "PYTEST-G4-ARTIFACT-PATH-20260903"

_CLEAN_SAP = (
    "# SAP đã khóa\n"
    # Ghi chú đặt TRƯỚC mọi mục §N — nếu đặt SAU §10 (mục cuối, không còn mục nào
    # theo sau để chặn biên) thì câu ví dụ minh hoạ dưới đây, dù chỉ TRÍCH DẪN
    # chuỗi placeholder trong ngoặc kép, vẫn bị _g4_sections_still_draft quét vào
    # THÂN của §10 và tự chặn — vì hàm chỉ so khớp chuỗi con, không phân biệt
    # trích dẫn minh hoạ với placeholder thật.
    "Nội dung SẠCH (không còn placeholder kiểu ngoặc vuông ở bất kỳ mục nào) để "
    "cô lập phép kiểm artifact-path khỏi _g4_sections_still_draft (đã có test "
    "riêng ở test_approve_gate_g4_content_check.py). Đủ cả 4 mục §1/§2/§5/§10 "
    "(không 'vắng sạch' theo BH97) — mục đích ở đây là điền, không phải bỏ trống.\n"
    "## §1 Tiêu chí nhận/loại (Quần thể phân tích)\n"
    "Người lớn ≥18 tuổi, đã ký ICF.\n"
    "## §2 Kết cục chính\n"
    "Tỷ lệ đáp ứng tại tuần 12.\n"
    "## §5 Covariates/Phân tích đa biến\n"
    "Tuổi, giới, mức độ nặng nền.\n"
    "## §10 Phần mềm + seed\n"
    "Python 3.12, seed=42.\n"
)


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
def _g4q_reports_ready(monkeypatch):
    """Cô lập chốt artifact-path khỏi mọi tiêu chí NỘI DUNG khác của G4Q —
    xem docstring module. Test dương tính cuối file dùng lại đúng patch này."""
    monkeypatch.setattr(
        G4Q, "evaluate_study",
        lambda *a, **k: {"status": G4Q.STATUS_READY, "automatic_criteria": [],
                         "approval_criteria": []},
    )


def _run_main(monkeypatch, *args) -> int:
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", *args])
    return AG.main()


def _ledger_records(study_dir: Path) -> list:
    p = study_dir / "approval_ledger.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def test_g4_rejects_non_canonical_artifact_path_even_with_clean_content(
    monkeypatch, study_dir, capsys,
):
    """★★ Ca chính của lỗ hổng: nội dung SẠCH (qua được _g4_sections_still_draft)
    VÀ G4Q báo READY (không có lý do nào khác để chặn) tại một đường dẫn KHÔNG
    PHẢI SAP canonical — trước bản vá, ca này ký sạch."""
    arbitrary = study_dir / "tu-khai-g4-tuy-y.md"
    arbitrary.write_text(_CLEAN_SAP, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(arbitrary),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc != 0
    out = capsys.readouterr().out
    assert "TỪ CHỐI ký G4" in out
    assert G4Q.sap_artifact_name(_STUDY) in out
    assert _ledger_records(study_dir) == []


def test_g4_rejects_non_canonical_artifact_path_on_rejected_decision_too(
    monkeypatch, study_dir,
):
    """Chốt KHÔNG gạn theo decision — khác G5/G8/G9/G10. REJECTED trên một
    file tùy ý cũng phải bị chặn, vì SAP là artifact hợp lệ DUY NHẤT của G4.
    (Decision REJECTED vốn đã bỏ qua nhánh gọi G4Q — fixture STATUS_READY ở
    đây không đổi hành vi, chỉ giữ đồng nhất với các test khác trong file.)"""
    arbitrary = study_dir / "tu-khai-g4-tuy-y.md"
    arbitrary.write_text(_CLEAN_SAP, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(arbitrary),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01", "--decision", "REJECTED",
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []


def test_g4_rejects_canonical_name_used_for_wrong_study(monkeypatch, study_dir):
    """Tên file đúng KHUÔN nhưng thuộc đề tài KHÁC (mã đề tài trong tên lệch
    với --study) vẫn phải bị chặn — không được chỉ so khớp bằng regex khuôn
    tên, phải so khớp ĐÚNG đường dẫn canonical của CHÍNH đề tài đang ký."""
    wrong_study_name = study_dir / G4Q.sap_artifact_name("MOT-DE-TAI-KHAC")
    wrong_study_name.write_text(_CLEAN_SAP, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact",
        str(wrong_study_name), "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []


def test_g4_rejects_correct_filename_in_wrong_directory(monkeypatch, study_dir, tmp_path):
    """Đúng TÊN FILE canonical nhưng nằm SAI THƯ MỤC (không phải
    exports/<study>/) vẫn phải bị chặn — chốt phải so khớp ĐƯỜNG DẪN đầy đủ đã
    resolve(), không phải chỉ so khớp .name. Mutation-test xác nhận: nới lỏng
    thành so khớp .name (bỏ qua thư mục) sẽ không bị 3 test còn lại bắt được
    (mã đề tài đã nằm sẵn trong tên file nên .name vẫn khác nhau ở đó) — CHỈ
    test này phát hiện được kiểu nới lỏng cụ thể này."""
    elsewhere = tmp_path / G4Q.sap_artifact_name(_STUDY)
    elsewhere.write_text(_CLEAN_SAP, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(elsewhere),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc != 0
    assert _ledger_records(study_dir) == []


def test_g4_accepts_correct_canonical_artifact_path(monkeypatch, study_dir):
    """Đối chứng dương tính: đúng tên canonical + G4Q báo READY vẫn ký được
    bình thường — bản vá không được chặn oan luồng hợp lệ."""
    artifact = study_dir / G4Q.sap_artifact_name(_STUDY)
    artifact.write_text(_CLEAN_SAP, encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(artifact),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc == 0
    records = _ledger_records(study_dir)
    assert len(records) == 1 and records[0]["gate_id"] == "G4"
    # evidence_hash phải khớp ĐÚNG nội dung SAP thật vừa ký — đúng bất biến mà
    # lỗ hổng gốc phá vỡ.
    assert records[0]["evidence_hash"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
