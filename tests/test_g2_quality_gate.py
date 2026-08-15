"""Kiểm thử hợp đồng chất lượng G2 và đường khóa IRB fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g2_auto as G2  # noqa: E402
import skill_standards as S  # noqa: E402


def _package() -> str:
    return """# A3 — HỒ SƠ ĐẠO ĐỨC
## TÀI LIỆU 1 — Đơn xin phê duyệt IRB
## TÀI LIỆU 2 — Tóm tắt đề cương
## TÀI LIỆU 3 — Bảng RỦI RO lợi ích
## TÀI LIỆU 4 — PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU
## TÀI LIỆU 5 — English informed consent
## TÀI LIỆU 6 — KẾ HOẠCH QUẢN LÝ DỮ LIỆU
## TÀI LIỆU 7 — Checklist nộp Hội đồng
## TÀI LIỆU 8 — NGUỒN TÀI TRỢ VÀ XUNG ĐỘT LỢI ÍCH
### BỒI THƯỜNG KHI CÓ TỔN HẠI
Chính sách đã được đơn vị và Hội đồng rà soát.
### Kế hoạch an toàn
Theo dõi AE/SAE; DSMB/DMC độc lập; quy tắc dừng tiền định.
> Cần bác sĩ kiểm chứng.
"""


def _g1_confirmed() -> dict:
    return {"quality_gate": {"status": "PASS_G1_CONFIRMED"}}


def _meta() -> dict:
    return {
        "gate_params": {
            "G0": {
                "population": "Người trưởng thành mắc bệnh Y",
                "intervention": "Can thiệp X",
                "comparison": "Chăm sóc chuẩn",
                "outcomes": ["Kết cục chính", "Nhập viện"],
                "primary_outcome": "Kết cục chính",
                "primary_outcome_measure": "Tỷ lệ người đạt đáp ứng",
                "primary_outcome_timepoint": "12 tuần",
            },
            "G1": {
                "intervention_or_exposure": "Can thiệp X theo protocol",
                "comparator": "Chăm sóc chuẩn",
                "inclusion_criteria": ["Tuổi từ 18", "Chẩn đoán bệnh Y"],
                "exclusion_criteria": ["Chống chỉ định can thiệp X"],
                "primary_outcome": "Kết cục chính",
                "secondary_outcomes": ["Nhập viện"],
            },
            "G2": {
                "protocol_version": "2.1",
                "icf_version": "2.0",
            }
        }
    }


def _write_registration(tmp_path: Path, study: str) -> Path:
    return G2Q.build_registration_draft(
        study=study,
        topic="Can thiệp X ở người trưởng thành",
        design_code="rct",
        design_primary="Thử nghiệm ngẫu nhiên có đối chứng",
        risk={
            "registration": "BẮT BUỘC trước tuyển mẫu",
            "register_where": "ClinicalTrials.gov",
        },
        n_target=200,
        out_dir=tmp_path,
        generated_at="2026-07-27T10:00:00+07:00",
        meta=_meta(),
    )


def _attestation(study: str, package_text: str, **overrides) -> dict:
    value = {
        "schema_version": G2Q.ATTESTATION_SCHEMA,
        "study": study,
        "ethics_decision": "APPROVED",
        "ethics_committee_ref": "IRB-UNIT-01",
        "approval_number": "IRB-2026-001",
        "approval_date": "2026-07-20",
        "valid_until": "2027-07-20",
        "no_expiry_confirmed": False,
        "approval_scope": "Protocol 2.1 và ICF 2.0",
        "approved_protocol_version": "2.1",
        "approved_icf_version": "2.0",
        "icf_waiver_approved": False,
        "recruitment_mode": "PROSPECTIVE_NEW_PARTICIPANTS",
        "first_enrolment_date": "2026-08-15",
        "registration": {
            "required": True,
            "status": "REGISTERED",
            "registry": "ClinicalTrials.gov",
            "registration_id": "NCT00000001",
            "registration_date": "2026-07-25",
        },
        "package_sha256_before_attestation": hashlib.sha256(
            G2Q.strip_attestation(package_text).encode("utf-8")
        ).hexdigest(),
        "attested_at": "2026-07-27T10:00:00+07:00",
        "ethics_committee_ref_source": "explicit",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    value.update(overrides)
    return value


def _evaluate(tmp_path: Path, package_text: str, *, ledger=True, meta=None):
    study = "TEST-G2"
    package_path = tmp_path / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    package_path.write_text(package_text, encoding="utf-8")
    registration_path = _write_registration(tmp_path, study)
    return G2Q.evaluate_g2_quality(
        study=study,
        design_code="rct",
        package_path=package_path,
        registration_path=registration_path,
        g1_checkpoint=_g1_confirmed(),
        meta=_meta() if meta is None else meta,
        guardrail_passed=True,
        ledger_approved=ledger,
        today=date(2026, 7, 27),
    )


def test_who_registration_draft_has_current_24_items(tmp_path):
    path = _write_registration(tmp_path, "TEST-G2")
    document = json.loads(path.read_text(encoding="utf-8"))

    assert document["who_trds_version"] == "1.3.1"
    assert document["item_count"] == 24
    assert [item["number"] for item in document["items"]] == list(range(1, 25))
    assert document["items"][20]["label"] == "Ethics Review"
    assert document["items"][23]["label"] == "IPD Sharing Statement"


def test_registration_draft_topic_fallback_to_study_code_is_caught(tmp_path):
    """Hồi quy G2-AUTO-04 (audit tautology vòng 2, 2026-07-31): khi thiếu
    --topic và không có G0 checkpoint, tools/run_g2_auto.py::main() fallback
    topic = study (mã đề tài đã làm sạch) — trước bản vá, mục 9/10 vẫn PASS
    vì "không rỗng" dù chỉ là mã đề tài, không phải tiêu đề khoa học thật."""
    path = G2Q.build_registration_draft(
        study="NOTOPIC-2026", topic="NOTOPIC-2026", design_code="rct",
        design_primary="RCT",
        risk={"registration": "BẮT BUỘC", "register_where": "ClinicalTrials.gov"},
        n_target=100, out_dir=tmp_path, generated_at="2026-07-31T00:00:00+07:00",
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    errors = G2Q._registration_draft_errors(document)
    assert any("trùng với mã đề tài" in e for e in errors)


def test_registration_draft_real_topic_not_flagged_as_fallback(tmp_path):
    path = _write_registration(tmp_path, "TEST-G2")
    document = json.loads(path.read_text(encoding="utf-8"))
    errors = G2Q._registration_draft_errors(document)
    assert not any("trùng với mã đề tài" in e for e in errors)


def test_generated_or_placeholder_package_never_claims_g2_approved(tmp_path):
    report = _evaluate(tmp_path, _package() + "\n[CẦN — kết cục chính]\n", ledger=True)

    assert report["status"] == G2Q.STATUS_DRAFT
    assert report["human_approval_complete"] is False
    assert report["status"] != G2Q.STATUS_APPROVED


def test_complete_package_without_real_decision_is_only_ready(tmp_path):
    report = _evaluate(tmp_path, _package(), ledger=False)

    assert report["package_ready_for_submission"] is True
    assert report["status"] == G2Q.STATUS_READY


def test_valid_attestation_and_ledger_can_pass_g2(tmp_path):
    base = _package()
    signed = G2Q.append_attestation(base, _attestation("TEST-G2", base))
    report = _evaluate(tmp_path, signed, ledger=True)

    assert report["status"] == G2Q.STATUS_APPROVED
    assert report["human_approval_complete"] is True


def _row(report, criterion_id):
    for row in report["automatic_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


def test_g2_auto_08_blocks_approval_when_scientific_items_are_missing(tmp_path):
    """Không được khóa G2 nếu WHO TRDS thiếu dữ kiện khoa học do PI pin."""
    base = _package()
    signed = G2Q.append_attestation(base, _attestation("TEST-G2", base))
    study = "TEST-G2"
    package_path = tmp_path / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    package_path.write_text(signed, encoding="utf-8")
    registration_path = G2Q.build_registration_draft(
        study=study,
        topic="Can thiệp X ở người trưởng thành",
        design_code="rct",
        design_primary="Thử nghiệm ngẫu nhiên có đối chứng",
        risk={"registration": "BẮT BUỘC", "register_where": "ClinicalTrials.gov"},
        n_target=200,
        out_dir=tmp_path,
        generated_at="2026-07-27T10:00:00+07:00",
        meta=None,
    )
    report = G2Q.evaluate_g2_quality(
        study=study,
        design_code="rct",
        package_path=package_path,
        registration_path=registration_path,
        g1_checkpoint=_g1_confirmed(),
        meta=_meta(),
        guardrail_passed=True,
        ledger_approved=True,
        today=date(2026, 7, 27),
    )

    row = _row(report, "G2-AUTO-08")
    assert row["status"] == "REVIEW"
    assert "#13" in row["evidence"] and "#14" in row["evidence"]
    assert "#19" in row["evidence"] and "#20" in row["evidence"]
    assert report["status"] == G2Q.STATUS_DRAFT


def test_g2_auto_08_passes_when_scientific_items_filled(tmp_path):
    study = "TEST-G2"
    registration_path = _write_registration(tmp_path, study)
    document = json.loads(registration_path.read_text(encoding="utf-8"))
    filled = {
        13: {"intervention": "Thuốc X 10mg/ngày x 12 tuần", "comparator": "Giả dược"},
        19: {
            "name": "Tử vong do mọi nguyên nhân",
            "measure": "Tỷ lệ tử vong",
            "timepoint": "12 tháng",
        },
        20: ["Nhập viện do suy tim", "Chất lượng sống (KCCQ)"],
    }
    for item in document["items"]:
        if item["number"] in filled:
            item["value"] = filled[item["number"]]
        elif item["number"] == 14:
            item["value"] = {
                "inclusion": ["Tuổi >= 18", "Chẩn đoán xác định"],
                "exclusion": ["Chống chỉ định thuốc nghiên cứu"],
            }
    registration_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    package_path = tmp_path / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    package_path.write_text(_package(), encoding="utf-8")
    report = G2Q.evaluate_g2_quality(
        study=study,
        design_code="rct",
        package_path=package_path,
        registration_path=registration_path,
        g1_checkpoint=_g1_confirmed(),
        meta=_meta(),
        guardrail_passed=True,
        ledger_approved=False,
        today=date(2026, 7, 27),
    )
    row = _row(report, "G2-AUTO-08")
    assert row["status"] == "PASS"


def test_g2_auto_09_ethics_ref_fallback_blocks_approval(tmp_path):
    """Mã hội đồng không được nhập nhèm với định danh người duyệt."""
    base = _package()
    signed = G2Q.append_attestation(
        base,
        _attestation(
            "TEST-G2",
            base,
            ethics_committee_ref_source="reviewer_ref_fallback",
        ),
    )
    report = _evaluate(tmp_path, signed, ledger=True)

    row = _row(report, "G2-AUTO-09")
    assert row["status"] == "REVIEW"
    assert report["status"] == G2Q.STATUS_DRAFT


def test_g2_auto_09_passes_when_ethics_ref_explicit(tmp_path):
    base = _package()
    signed = G2Q.append_attestation(
        base,
        _attestation(
            "TEST-G2", base,
            ethics_committee_ref_source="explicit",
        ),
    )
    report = _evaluate(tmp_path, signed, ledger=True)

    row = _row(report, "G2-AUTO-09")
    assert row["status"] == "PASS"


def test_cli_g2_ethics_committee_ref_flag_records_explicit_source(tmp_path):
    """Đường thật: --g2-ethics-committee-ref tách biệt khỏi --reviewer-ref
    khiến attestation ghi 'explicit' và G2-AUTO-09 PASS ngay lần ký đầu."""
    study = "PYTEST-G2-ETHICS-REF-CLI"
    study_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(study_dir, ignore_errors=True)
    study_dir.mkdir(parents=True)
    try:
        package_path = study_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        package_path.write_text(_package(), encoding="utf-8")
        _write_registration(study_dir, study)
        (study_dir / "G1_checkpoint.json").write_text(
            json.dumps(_g1_confirmed(), ensure_ascii=False), encoding="utf-8"
        )
        (study_dir / "study_meta.json").write_text(
            json.dumps(_meta(), ensure_ascii=False), encoding="utf-8"
        )
        (study_dir / "G2_checkpoint.json").write_text(
            json.dumps({
                "study": study,
                "gate": "G2",
                "design_code": "rct",
                "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
                "guardrail": {"passed": True, "errors": []},
                "artifacts": {"A3_markdown": str(package_path)},
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        key_path = tmp_path / "gate_approval_key"
        key_path.write_text("pytest-g2-ethics-ref-key", encoding="utf-8")
        env = os.environ.copy()
        env["EBM_GATE_KEY_PATH"] = str(key_path)
        result = subprocess.run(
            [
                PYTHON, str(TOOLS_DIR / "approve_gate.py"),
                "--study", study, "--gate", "G2", "--artifact", str(package_path),
                "--reviewer-role", "IRB_ETHICS_COMMITTEE", "--reviewer-ref", "bs-luan",
                "--g2-ethics-committee-ref", "HDDD-BVQY175-2026",
                "--g2-approval-number", "IRB-2026-002",
                "--g2-approval-date", "2026-07-20", "--g2-valid-until", "2027-07-20",
                "--g2-protocol-version", "2.1", "--g2-icf-version", "2.0",
                "--g2-ethics-decision", "APPROVED",
                "--g2-recruitment-mode", "PROSPECTIVE_NEW_PARTICIPANTS",
                "--g2-registration-status", "REGISTERED",
                "--g2-registry", "ClinicalTrials.gov",
                "--g2-registration-id", "NCT00000002",
                "--g2-registration-date", "2026-07-25",
                "--g2-first-enrolment-date", "2026-08-15",
            ],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        checkpoint = json.loads(
            (study_dir / "G2_checkpoint.json").read_text(encoding="utf-8")
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert checkpoint["g2_status"] == "LOCKED"
        attestation = G2Q.extract_attestation(
            package_path.read_text(encoding="utf-8")
        )
        assert attestation["ethics_committee_ref"] == "HDDD-BVQY175-2026"
        assert attestation["ethics_committee_ref_source"] == "explicit"
    finally:
        shutil.rmtree(study_dir, ignore_errors=True)


def test_protocol_version_mismatch_fails_closed(tmp_path):
    base = _package()
    attestation = _attestation(
        "TEST-G2",
        base,
        approved_protocol_version="1.0",
    )
    report = _evaluate(
        tmp_path,
        G2Q.append_attestation(base, attestation),
        ledger=True,
    )

    assert report["status"] == G2Q.STATUS_PENDING
    evidence = " ".join(
        row["evidence"] for row in report["human_approval_criteria"]
    )
    assert "protocol" in evidence


def test_expired_irb_decision_fails_closed(tmp_path):
    base = _package()
    attestation = _attestation("TEST-G2", base, valid_until="2026-07-26")
    report = _evaluate(
        tmp_path,
        G2Q.append_attestation(base, attestation),
        ledger=True,
    )

    assert report["status"] == G2Q.STATUS_PENDING
    assert "hết hiệu lực" in json.dumps(report, ensure_ascii=False)


def test_registration_after_first_enrolment_fails_closed(tmp_path):
    base = _package()
    attestation = _attestation("TEST-G2", base)
    attestation["registration"]["registration_date"] = "2026-08-20"
    report = _evaluate(
        tmp_path,
        G2Q.append_attestation(base, attestation),
        ledger=True,
    )

    assert report["status"] == G2Q.STATUS_PENDING
    assert "muộn hơn" in json.dumps(report, ensure_ascii=False)


def test_sr_ma_registration_after_first_search_fails_closed(tmp_path):
    base = _package()
    attestation = _attestation(
        "TEST-G2",
        base,
        recruitment_mode="NOT_APPLICABLE",
        first_enrolment_date="",
        first_search_date="2026-07-10",
    )
    attestation["registration"].update({
        "registry": "PROSPERO",
        "registration_id": "CRD42026000001",
        "registration_date": "2026-07-11",
    })
    errors = G2Q.validate_attestation(
        attestation=attestation,
        study="TEST-G2",
        design_code="sr_ma",
        package_text=G2Q.append_attestation(base, attestation),
        meta=_meta(),
        today=date(2026, 7, 27),
    )

    assert any("ngày bắt đầu tìm kiếm" in error for error in errors)


def test_new_contract_checkpoint_requires_quality_pass():
    assert GC.g2_quality_contract_satisfied({
        "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
        "quality_gate": {"status": G2Q.STATUS_PENDING},
    }) is False
    assert GC.g2_quality_contract_satisfied({
        "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
        "quality_gate": {"status": G2Q.STATUS_APPROVED},
        "g2_approval_valid_until": "2099-12-31",
    }) is True
    assert GC.g2_quality_contract_satisfied({"g2_status": "LOCKED"}) is True


def test_runtime_rechecks_expiry_and_current_versions():
    checkpoint = {
        "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
        "quality_gate": {"status": G2Q.STATUS_APPROVED},
        "g2_approval_valid_until": "2099-12-31",
        "g2_protocol_version": "2.1",
        "g2_icf_version": "2.0",
    }
    assert GC.g2_quality_contract_satisfied(checkpoint, _meta()) is True

    expired = dict(checkpoint, g2_approval_valid_until="2020-01-01")
    assert GC.g2_quality_contract_satisfied(expired, _meta()) is False

    changed_meta = _meta()
    changed_meta["gate_params"]["G2"]["protocol_version"] = "2.2"
    assert GC.g2_quality_contract_satisfied(checkpoint, changed_meta) is False


def test_meta_boolean_cannot_override_new_g2_quality_contract():
    checkpoints = {
        "G2": {
            "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
            "quality_gate": {"status": G2Q.STATUS_PENDING},
            "guardrail": {"passed": True},
            "g2_irb_number": "IRB-2026-001",
            "g2_approval_date": "2026-07-20",
        }
    }
    signals = S.real_world_signals(
        checkpoints,
        {"irb_approved": True},
    )

    assert signals["irb_approved"] is False


def test_prepare_g2_refuses_unresolved_scientific_placeholders(tmp_path):
    study = "TEST-G2"
    artifact = tmp_path / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    content = _package() + "\nKết cục: [CẦN — xác định]\n"
    artifact.write_text(content, encoding="utf-8")
    args = argparse.Namespace(
        study=study,
        reviewer_ref="IRB-UNIT-01",
        scope="",
        g2_approval_number="IRB-2026-001",
        g2_approval_date="2026-07-20",
        g2_valid_until="2027-07-20",
        g2_no_expiry_confirmed=False,
        g2_protocol_version="2.1",
        g2_icf_version="2.0",
        g2_icf_waiver_approved=False,
        g2_ethics_decision="APPROVED",
        g2_recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS",
        g2_registration_status="REGISTERED",
        g2_registry="ClinicalTrials.gov",
        g2_registration_id="NCT00000001",
        g2_registration_date="2026-07-25",
        g2_first_enrolment_date="2026-08-15",
        g2_first_search_date=None,
        g2_approval_scope="Protocol 2.1",
    )

    prepared, errors = AG._prepare_g2_attestation(
        args,
        artifact,
        content,
        tmp_path,
    )

    assert prepared is None
    assert any("placeholder" in item for item in errors)


def test_human_cli_valid_g2_flow_updates_checkpoint_to_pass(tmp_path):
    """Đường thật: IRB role + metadata + chữ ký khớp mới khóa checkpoint."""
    study = "PYTEST-G2-QUALITY-CLI"
    study_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(study_dir, ignore_errors=True)
    study_dir.mkdir(parents=True)
    try:
        package_path = study_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        package_path.write_text(_package(), encoding="utf-8")
        _write_registration(study_dir, study)
        (study_dir / "G1_checkpoint.json").write_text(
            json.dumps(_g1_confirmed(), ensure_ascii=False),
            encoding="utf-8",
        )
        (study_dir / "study_meta.json").write_text(
            json.dumps(_meta(), ensure_ascii=False),
            encoding="utf-8",
        )
        (study_dir / "G2_checkpoint.json").write_text(
            json.dumps({
                "study": study,
                "gate": "G2",
                "design_code": "rct",
                "quality_contract_version": G2Q.QUALITY_CONTRACT_VERSION,
                "guardrail": {"passed": True, "errors": []},
                "artifacts": {"A3_markdown": str(package_path)},
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        key_path = tmp_path / "gate_approval_key"
        key_path.write_text("pytest-g2-quality-key", encoding="utf-8")
        env = os.environ.copy()
        env["EBM_GATE_KEY_PATH"] = str(key_path)
        result = subprocess.run(
            [
                PYTHON,
                str(TOOLS_DIR / "approve_gate.py"),
                "--study", study,
                "--gate", "G2",
                "--artifact", str(package_path),
                "--reviewer-role", "IRB_ETHICS_COMMITTEE",
                "--reviewer-ref", "IRB-UNIT-01",
                "--g2-ethics-committee-ref", "IRB-UNIT-01",
                "--g2-approval-number", "IRB-2026-001",
                "--g2-approval-date", "2026-07-20",
                "--g2-valid-until", "2027-07-20",
                "--g2-protocol-version", "2.1",
                "--g2-icf-version", "2.0",
                "--g2-ethics-decision", "APPROVED",
                "--g2-recruitment-mode", "PROSPECTIVE_NEW_PARTICIPANTS",
                "--g2-registration-status", "REGISTERED",
                "--g2-registry", "ClinicalTrials.gov",
                "--g2-registration-id", "NCT00000001",
                "--g2-registration-date", "2026-07-25",
                "--g2-first-enrolment-date", "2026-08-15",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        checkpoint = json.loads(
            (study_dir / "G2_checkpoint.json").read_text(encoding="utf-8")
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert checkpoint["g2_status"] == "LOCKED"
        assert checkpoint["quality_gate"]["status"] == G2Q.STATUS_APPROVED
        assert G2Q.ATTESTATION_BEGIN in package_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(study_dir, ignore_errors=True)


def test_run_g2_main_writes_quality_contract_and_never_false_pass(
    tmp_path,
    monkeypatch,
):
    study = "INTEGRATION-G2"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_g2_auto.py",
            "--study", study,
            "--topic", "Can thiệp X ở người trưởng thành",
            "--design", "rct",
            # 2026-07-28: thay cho monkeypatch `search_clinicaltrials` (hàm đã bị
            # gỡ) — cờ CLI thật, giữ test offline mà không cần biết nội bộ hàm tra.
            "--skip-registry",
        ],
    )
    monkeypatch.setattr(G2, "export_docx_g2", lambda *_args: None)

    G2.main()

    study_dir = tmp_path / "exports" / study
    checkpoint = json.loads(
        (study_dir / "G2_checkpoint.json").read_text(encoding="utf-8")
    )
    registration = json.loads(
        (study_dir / f"G2_REGISTRATION_DRAFT_{study}.json").read_text(
            encoding="utf-8"
        )
    )
    assert checkpoint["quality_contract_version"] == G2Q.QUALITY_CONTRACT_VERSION
    assert checkpoint["quality_gate"]["status"] == G2Q.STATUS_DRAFT
    assert checkpoint["g2_status"] == "PENDING"
    assert registration["item_count"] == 24
    assert (study_dir / "G2_QUALITY_REPORT.md").exists()
