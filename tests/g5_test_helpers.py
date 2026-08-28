"""Fixture G5 đầy đủ cho kiểm thử tích hợp, chỉ dùng dữ liệu tổng hợp."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import clean_research_dataset as CLEAN  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402
import run_g4_auto as G4  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402


def configure_test_signing_key(
    tmp_path: Path,
    monkeypatch,
    *,
    key_text: str = "pytest-g5-quality-contract-key",
) -> Path:
    """Tạo khóa HMAC tạm trong pytest; không dùng cho nghiên cứu thật."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text(key_text, encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    return key_path


def append_signed_approval(
    study: str,
    artifact: Path,
    gate_id: str,
    reviewer_role: str,
    *,
    repo_root: Path,
) -> None:
    """Thêm một approval test có chữ ký, chuỗi băm và con dấu hợp lệ."""
    ledger_path = artifact.parent / "approval_ledger.json"
    try:
        existing = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        existing = []
    previous = existing[-1] if isinstance(existing, list) and existing else None
    prev_hash = GC.chain_prev_hash(previous if isinstance(previous, dict) else None)
    content = artifact.read_text(encoding="utf-8")
    evidence_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat()
    reviewer_ref = f"PYTEST-{gate_id}-REVIEWER"
    signature = GC.sign_approval(
        gate_id,
        study,
        evidence_hash,
        timestamp,
        reviewer_role=reviewer_role,
        reviewer_ref=reviewer_ref,
        decision="APPROVED",
        is_synthetic=False,
        prev_hash=prev_hash,
    )
    assert signature
    record = ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role=reviewer_role,
        reviewer_ref=reviewer_ref,
        scope="Kiểm thử hợp đồng G5 bằng dữ liệu tổng hợp",
        evidence_content=content,
        decision=ApprovalDecisionEnum.APPROVED,
        approver_signature=signature,
        timestamp_utc=timestamp,
        prev_hash=prev_hash,
    )
    ledger = ApprovalLedger.from_file(ledger_path)
    ok, reason = ledger.add_approval(record)
    assert ok, reason
    ledger.to_file(ledger_path)
    records = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert GC.write_ledger_seal(study, records, repo_root=repo_root)


def write_g5_toolkit(
    study: str,
    out_dir: Path,
    *,
    id_field: str = "record_id",
) -> Path:
    """Tạo bộ DMP/dictionary/script tối thiểu nhưng hợp lệ cho fixture."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dmp = "\n".join(
        [
            "# Kế hoạch quản lý dữ liệu kiểm thử",
            "CẤU TRÚC CRF",
            "REDCAP DATA DICTIONARY",
            "LUẬT KIỂM TRA DỮ LIỆU",
            "AUDIT TRAIL",
            "KHỬ ĐỊNH DANH",
            "PHÂN QUYỀN",
            "SAO LƯU và kiểm thử phục hồi",
            "LƯU TRỮ và hủy dữ liệu",
            "KHÓA CƠ SỞ DỮ LIỆU",
            "CHIA SẺ DỮ LIỆU theo FAIR",
            "Áp dụng ICH E6(R3), CDISC CDASH và FDA electronic records 2024.",
            "PMID: 26978244; DOI: 10.1038/sdata.2016.18.",
            "Cần bác sĩ kiểm chứng.",
            "",
        ]
    )
    (out_dir / f"G5_A6_DATA_MGMT_{study}.md").write_text(
        dmp,
        encoding="utf-8", newline="\n"
    )
    headers = [
        "Variable / Field Name",
        "Form Name",
        "Section Header",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Field Note",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Identifier?",
        "Branching Logic (Show field only if...)",
        "Required Field?",
        "Custom Alignment",
        "Question Number (surveys only)",
        "Matrix Group Name",
        "Matrix Ranking?",
        "Field Annotation",
    ]
    dictionary_path = out_dir / f"G5_REDCap_dictionary_{study}.csv"
    rows = [
        ("record_id", "text", "", "", "", ""),
        ("study_subject_id", "text", "", "", "", ""),
        ("age", "text", "", "number", "0", "120"),
        ("sex", "radio", "F, Nữ | M, Nam", "", "", ""),
        ("group", "radio", "0, Chứng | 1, Phơi nhiễm", "", "", ""),
        ("exposure", "radio", "0, Chứng | 1, Phơi nhiễm", "", "", ""),
        ("exposure_var", "radio", "0, Chứng | 1, Phơi nhiễm", "", "", ""),
        ("primary_outcome", "text", "", "number", "", ""),
        ("outcome_cont", "text", "", "number", "", ""),
        ("outcome_bin", "radio", "0, Không | 1, Có", "", "", ""),
        ("outcome_score", "text", "", "number", "", ""),
        ("bmi", "text", "", "number", "5", "100"),
        ("follow_time", "text", "", "number", "0", ""),
        ("event_flag", "radio", "0, Kiểm duyệt | 1, Biến cố", "", "", ""),
    ]
    with dictionary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for name, field_type, choices, validation, minimum, maximum in rows:
            writer.writerow(
                {
                    "Variable / Field Name": name,
                    "Form Name": "research",
                    "Field Type": field_type,
                    "Field Label": name,
                    "Choices, Calculations, OR Slider Labels": choices,
                    "Text Validation Type OR Show Slider Number": validation,
                    "Text Validation Min": minimum,
                    "Text Validation Max": maximum,
                    "Required Field?": "y" if name == id_field else "n",
                }
            )
    scripts = out_dir / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "data_cleaning.py").write_text(
        "# Fixture; không xử lý dữ liệu thật.\n",
        encoding="utf-8", newline="\n"
    )
    (scripts / "data_quality_report.py").write_text(
        "# Fixture; không xử lý dữ liệu thật.\n",
        encoding="utf-8", newline="\n"
    )
    today = datetime.now().date().isoformat()
    operational = {
        "schema_version": "G5-OPS-2026.1",
        "status": "VERIFIED",
        "access_control_review": {
            "completed": True,
            "reviewed_at": today,
            "least_privilege_confirmed": True,
            "evidence_ref": "PYTEST-ACCESS-001",
        },
        "backup_restore_test": {
            "completed": True,
            "tested_at": today,
            "restore_verified": True,
            "checksum_verified": True,
            "evidence_ref": "PYTEST-BACKUP-001",
        },
        "retention_plan": {
            "confirmed": True,
            "retention_rule": "Fixture chỉ tồn tại trong thời gian chạy pytest.",
        },
        "protocol_deviations": {
            "reconciled": True,
            "open_count": 0,
            "log_ref": "PYTEST-DEVIATION-001",
        },
        "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER",
        "reviewer_ref": "PYTEST-G5-DATA-REVIEWER",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    (out_dir / G5Q.OPERATIONAL_READINESS_JSON).write_text(
        json.dumps(operational, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    checkpoint = {
        "gate": "G5",
        "study": study,
        "quality_contract_version": G5Q.QUALITY_CONTRACT_VERSION,
        "g5_status": "PENDING",
        "guardrail": {"passed": True, "errors": [], "warnings": []},
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    (out_dir / "G5_checkpoint.json").write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    return dictionary_path


_G4_SAP_FILLS = [
    ("- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ", "- **Tiêu chí nhận:** Tuổi 18-75  "),
    ("- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ", "- **Tiêu chí loại:** Chống chỉ định  "),
    ("- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
     "- **Kết cục chính:** Tỷ lệ nhập viện tim mạch trong 12 tháng  "),
    ("- **Đơn vị / ngưỡng:** [CẦN]  ", "- **Đơn vị / ngưỡng:** %  "),
    ("- **Kết cục phụ 1:** [CẦN]  ", "- **Kết cục phụ 1:** Tử vong toàn bộ  "),
    ("- **Kết cục phụ 2:** [CẦN]  ", "- **Kết cục phụ 2:** Đột quỵ  "),
    ("- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ", "- **Kết cục an toàn:** Tiêu cơ vân  "),
    ("- **Biến độc lập đưa vào:** [CẦN BÁC SĨ LIỆT KÊ — kèm lý do lâm sàng / DAG]  ",
     "- **Biến độc lập đưa vào:** Tuổi, HbA1c — EPV=15 cho 8 biến, VIF<5  "),
    ("- **Giả định:** [CẦN kiểm tra PH / normality theo thiết kế]  ", "- **Giả định:** Kiểm PH bằng cox.zph  "),
    ("- **Biến đưa vào mô hình imputation:** [CẦN BÁC SĨ ĐIỀN]  ",
     "- **Biến đưa vào mô hình imputation:** Tuổi, giới, HbA1c nền  "),
    ("- **Nhóm nhỏ tiền định:** [CẦN BÁC SĨ — phải ghi TRƯỚC khi xem dữ liệu]  ",
     "- **Nhóm nhỏ tiền định:** Theo tuổi <65/≥65 — TIỀN ĐỊNH  "),
    ("- **Điều chỉnh:** [CẦN — Bonferroni / FDR nếu >3 kết cục chính]  ",
     "- **Điều chỉnh:** Chỉ 1 kết cục chính nên không cần hiệu chỉnh  "),
    ("- [CẦN BÁC SĨ thêm kịch bản cụ thể]  ", "- Kịch bản: loại trừ bỏ thuốc >30% thời gian theo dõi  "),
    ("- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  ", "- **Phần mềm:** R v4.3.1  "),
    ("- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  ", "- **Packages:** survival, mice  "),
    ("- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ", "- **Random seed:** set.seed(20260730)  "),
]


def prepare_upstream_approvals(
    study: str,
    out_dir: Path,
    *,
    repo_root: Path,
) -> None:
    """Tạo checkpoint và approval G2/G4 hợp lệ cho fixture tổng hợp.

    SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL): trước đây G4
    chỉ ghi tay ``{"g4_status": "LOCKED"}`` vào checkpoint — một chuỗi mà
    KHÔNG pipeline thật nào từng tạo ra (xem run_g4_auto.py), và
    ``g10_quality_gate.py``/``g9_quality_gate.py`` đọc ĐÚNG field text đó
    (``_status_locked``) nên "PASS" của các test này chưa từng chứng minh
    được pipeline thật có thể đạt LOCKED hay không. Nay g10/g9 đã chuyển
    sang chấm trực tiếp qua ``gate_contract.g4_quality_contract_satisfied()``
    (như g5_ok/g9_ok đã làm đúng từ đầu) — fixture này phải dựng một G4 THẬT
    SỰ đạt ``PASS_G4_SAP_LOCKED``: SAP sinh từ ``run_g4_auto.generate()`` rồi
    điền đủ placeholder, G1/G3 checkpoint nhất quán, xác nhận
    ``gate_params.G4``, và ký bằng khóa RIÊNG nhóm STATISTICIAN (không phải
    khóa chung — G4-HUMAN-02 chỉ PASS với khóa vai trò, giống hệt G8-HUMAN-03).
    """
    (out_dir / "G2_checkpoint.json").write_text(
        json.dumps({"g2_status": "LOCKED"}, ensure_ascii=False),
        encoding="utf-8", newline="\n"
    )
    g2_artifact = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    g2_artifact.write_text(
        "Hồ sơ đạo đức fixture tổng hợp. Cần bác sĩ kiểm chứng.",
        encoding="utf-8", newline="\n"
    )
    append_signed_approval(
        study,
        g2_artifact,
        "G2",
        "IRB_ETHICS_COMMITTEE",
        repo_root=repo_root,
    )

    # Design nhất quán với G1 nếu fixture khác đã tạo checkpoint đó trước;
    # mặc định "cohort" khi chưa có (đa số test G9/G10 không cần G1 riêng).
    g1_path = out_dir / "G1_checkpoint.json"
    if g1_path.exists():
        try:
            existing_g1 = json.loads(g1_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            existing_g1 = {}
        design_code = ((existing_g1.get("design") or {}).get("internal_code")) or "cohort"
    else:
        design_code = "cohort"
        g1_path.write_text(
            json.dumps(
                {"gate": "G1", "design": {"internal_code": design_code,
                                          "primary": "Cohort tiến cứu", "ambiguous": False}},
                ensure_ascii=False,
            ),
            encoding="utf-8", newline="\n"
        )

    g3_fields = {
        "gate": "G3", "design_code": design_code, "alpha": 0.05, "power": 0.8,
        "n_adjusted": 200, "confirmed_n": None, "effect_val": 0.7, "effect_type": "RR",
        "hypothesis_type": "superiority", "margin": None, "sd": None, "guardrail": "✅ PASS",
    }
    (out_dir / "G3_checkpoint.json").write_text(
        json.dumps(g3_fields, ensure_ascii=False), encoding="utf-8", newline="\n")

    sap_text = G4.generate(
        study, f"Đề tài fixture tổng hợp {study}", design_code, "Cohort tiến cứu",
        "STROBE 2007", g3_fields["n_adjusted"], g3_fields["alpha"], g3_fields["power"],
        g3_fields["effect_val"], g3_fields["effect_type"], "2026-07-30",
    )
    for old, new in _G4_SAP_FILLS:
        sap_text = sap_text.replace(old, new)
    g4_artifact = out_dir / f"G4_A5_SAP_FINAL_{study}.md"
    g4_artifact.write_text(sap_text, encoding="utf-8", newline="\n")

    (out_dir / "G4_checkpoint.json").write_text(
        json.dumps(
            {"gate": "G4", "study": study, "g4_status": "PENDING — CHỜ BÁC SĨ KÝ SAP",
             "g4_sap_version": "1.0", "design_code": design_code, "guardrail": "✅ PASS"},
            ensure_ascii=False,
        ),
        encoding="utf-8", newline="\n"
    )

    meta = GC.ensure_study_meta(out_dir)
    meta["gate_params"]["G4"].update({
        "epv_vif_reviewed": True,
        "missing_data_mechanism_confirmed": True,
        "subgroup_multiplicity_predefined_confirmed": True,
        "reviewed_by_role": "STATISTICIAN",
        "reviewed_at": "2026-07-30T08:00:00+00:00",
    })
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # Khóa RIÊNG nhóm STATISTICIAN — bắt buộc để G4-HUMAN-02 (mức bảo đảm khóa
    # ký) đạt PASS; ký bằng khóa CHUNG chỉ đạt REVIEW nên KHÔNG BAO GIỜ tới
    # được PASS_G4_SAP_LOCKED (đúng thiết kế, mirror G8-HUMAN-03).
    base_key = os.environ.get("EBM_GATE_KEY_PATH")
    if base_key:
        role_key_path = Path(base_key).with_name(Path(base_key).name + "_STATISTICIAN")
        if not role_key_path.exists():
            role_key_path.write_text("pytest-g4-statistician-role-key", encoding="utf-8", newline="\n")

    append_signed_approval(
        study,
        g4_artifact,
        "G4",
        "METHODS_STATISTICS_REVIEWER",
        repo_root=repo_root,
    )


def prepare_locked_g5_study(
    study: str,
    source_data: Path,
    *,
    exports_root: Path,
    repo_root: Path,
    approve_g5: bool = True,
) -> tuple[Path, dict]:
    """Chạy intake -> cleaning -> lock -> approval G5 cho dữ liệu tổng hợp."""
    out_dir = exports_root / study
    with Path(source_data).open("r", encoding="utf-8-sig", newline="") as handle:
        source_fields = set(csv.DictReader(handle).fieldnames or [])
    id_field = (
        "record_id"
        if "record_id" in source_fields
        else "study_subject_id"
        if "study_subject_id" in source_fields
        else "record_id"
    )
    dictionary_path = write_g5_toolkit(
        study,
        out_dir,
        id_field=id_field,
    )
    prepare_upstream_approvals(study, out_dir, repo_root=repo_root)

    intake = RDI.import_dataset(study, source_data, exports_root=exports_root)
    assert intake["status"] == RDI.READY_STATUS, intake
    raw_path = out_dir / intake["raw_readonly_path"]
    cleaning = CLEAN.clean_dataset(
        study,
        raw_path,
        dictionary_path=dictionary_path,
        exports_root=exports_root,
    )
    assert cleaning["status"] == CLEAN.CLEAN_READY_STATUS, cleaning
    clean_path = out_dir / cleaning["clean_dataset_path"]
    query_log = out_dir / cleaning["query_log"]
    manifest = LAD.lock_dataset(
        study,
        clean_path,
        lock_date=datetime.now().date().isoformat(),
        reviewer_role="DATA_GOVERNANCE_QA_REVIEWER",
        reviewer_ref="PYTEST-G5-DATA-REVIEWER",
        sap_version="1.0",
        query_log=query_log,
        dictionary_path=dictionary_path,
        cleaning_report_path=out_dir / CLEAN.REPORT_NAME,
        exports_root=exports_root,
        repo_root=repo_root,
        confirm_deidentified=True,
        confirm_clean_copy=True,
        confirm_no_open_query=True,
        confirm_sap_locked=True,
        confirm_dictionary_crf_aligned=True,
        confirm_access_control_reviewed=True,
        confirm_backup_restore_tested=True,
        confirm_retention_plan=True,
        confirm_protocol_deviations_reconciled=True,
    )
    assert manifest["status"] == LAD.LOCKED_STATUS, manifest.get("blockers")
    report = G5Q.evaluate_study(
        study,
        out_dir,
        repo_root=repo_root,
        write=True,
    )
    assert report["status"] == G5Q.STATUS_READY, report
    if approve_g5:
        append_signed_approval(
            study,
            out_dir / "G5_checkpoint.json",
            "G5",
            "DATA_GOVERNANCE_QA_REVIEWER",
            repo_root=repo_root,
        )
        report = G5Q.evaluate_study(
            study,
            out_dir,
            repo_root=repo_root,
            write=True,
        )
        assert report["status"] == G5Q.STATUS_LOCKED, report
    locked_path = out_dir / manifest["locked_dataset_path"]
    return locked_path, report
