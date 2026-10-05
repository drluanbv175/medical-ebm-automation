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
    extra_date_columns: frozenset[str] = frozenset(),
) -> Path:
    """Tạo bộ DMP/dictionary/script tối thiểu nhưng hợp lệ cho fixture.

    `extra_date_columns`: tên các cột NGHIÊN CỨU (vd `visit_date`) mà
    `source_data` có sẵn và đã được khai tường minh kiểu "date" ở một
    dictionary khác (vd data_dictionary.json của pipeline pseudonymize) —
    được ghi THÊM vào chính dictionary REDCap canonical này (không tạo
    dictionary thứ hai) để `RDI.import_dataset()`/`CLEAN.clean_dataset()`/
    `LAD.lock_dataset()` MIỄN mẫu PII "date" cho đúng cột đó, đồng thời
    `g5_quality_gate.evaluate_study()` — vốn đọc CHÍNH file này ở đường dẫn
    canonical để chấm G5-AUTO-02..09 — vẫn thấy MỘT dictionary duy nhất,
    không lệch hash với bước intake/clean/lock.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    # NỘI DUNG THẬT (không chỉ nhãn trần) sau mỗi mục bắt buộc — kể từ khi
    # G5-AUTO-03 được vá 10/09/2026 để đòi thân mục có nội dung, không chỉ
    # đếm nhãn có mặt (đóng tautology G5-F3, xem g5_quality_gate.py). Fixture
    # cũ chỉ liệt 11 nhãn trần liên tiếp — hợp lệ cho các test khác trong chuỗi
    # G5 nhưng KHÔNG còn qua được chính luật nó phải PASS; sửa fixture cho hợp
    # lệ theo đúng tiền lệ BH97 (không nới lỏng luật để fixture cũ qua được).
    dmp = "\n".join(
        [
            "# Kế hoạch quản lý dữ liệu kiểm thử",
            "",
            "## CẤU TRÚC CRF",
            "CRF kiểm thử gồm mã đối tượng, ngày khám và kết cục chính; xem dictionary đính kèm.",
            "",
            "## REDCAP DATA DICTIONARY",
            "File dictionary CSV liệt kê tên biến, loại dữ liệu, nhãn và phạm vi hợp lệ.",
            "",
            "## LUẬT KIỂM TRA DỮ LIỆU",
            "Áp dụng range-check và logic-check cho biến số/biến ngày trước khi khóa dữ liệu.",
            "",
            "## AUDIT TRAIL",
            "Mọi thay đổi giá trị lưu bản gốc, lý do sửa, thời điểm và người thực hiện.",
            "",
            "## KHỬ ĐỊNH DANH",
            "Bảng ánh xạ định danh tách khỏi dataset phân tích, không đưa PII vào bản chạy thống kê.",
            "",
            "## PHÂN QUYỀN",
            "Truy cập theo nguyên tắc tối thiểu cần biết; người phân tích chỉ nhận bản đã khóa.",
            "",
            "## SAO LƯU và kiểm thử phục hồi",
            "Sao lưu định kỳ có mã hóa, đã thử khôi phục thành công trong môi trường kiểm thử.",
            "",
            "## LƯU TRỮ và hủy dữ liệu",
            "Thời hạn lưu trữ và hủy theo chính sách đơn vị, có ghi rõ người chịu trách nhiệm.",
            "",
            "## KHÓA CƠ SỞ DỮ LIỆU",
            "Checklist khóa DB đã hoàn tất, có chữ ký người khóa và người chứng kiến.",
            "",
            "## CHIA SẺ DỮ LIỆU theo FAIR",
            "Chia sẻ dữ liệu tuân thủ FAIR khi được phép, không công khai dữ liệu nhạy cảm.",
            "",
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
    declared_names = {name for name, *_ in rows}
    for extra_name in sorted(extra_date_columns):
        if extra_name in declared_names:
            continue
        # validation "date_ymd" -> _normalise_rule() trong clean_research_dataset.py
        # đọc thành type="date" (bắt đầu bằng "date_"); đúng khuôn REDCap thật.
        rows.append((extra_name, "text", "", "date_ymd", "", ""))
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


def _doc_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def prepare_upstream_approvals(
    study: str,
    out_dir: Path,
    *,
    repo_root: Path,
) -> None:
    """Tạo checkpoint và approval G2/G4 hợp lệ cho fixture tổng hợp.

    SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL): trước đây G4 chỉ ghi tay ``{"g4_status": "LOCKED"}`` —
    fixture phải dựng một G4 THẬT SỰ đạt ``PASS_G4_SAP_LOCKED``.

    SỬA 04/10/2026 (soát từng cổng G4): G4 nay CHẤM SỐNG G3 (G4-AUTO-12), đòi chứng chỉ khoá đã điền, estimand/§13–§15
    cho RCT và xác nhận gắn DẤU nội dung SAP (G4-HUMAN-08) — «G1/G3 checkpoint trơn + SAP generate() điền chuỗi cố
    định» không còn khoá được G4 (đúng luật). Fixture dựng chuỗi G0→G1→G3 ĐÃ CHỐT THẬT theo THIẾT KẾ của đề tài
    (tests/_chuoi_da_chot.py — thiết kế lấy từ G1 test tự ghi trước: design.internal_code hoặc design_code, mặc định
    cohort), giữ nguyên khoá riêng test đã ghi (G1_checkpoint, gate_params cổng khác), sinh SAP bằng run_g4_auto THẬT,
    điền như người thật, xác nhận G4 gắn dấu, ký bằng khoá RIÊNG nhóm STATISTICIAN — rồi TỰ KIỂM G4 chấm sống LOCKED
    (fixture hỏng thì lộ ngay ở đây, không lộ ở test G5–G10 phía sau).
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cong_song as CS  # noqa: PLC0415
    import g4_quality_gate as G4Q  # noqa: PLC0415
    import skill_standards as SK  # noqa: PLC0415
    from _chuoi_da_chot import (  # noqa: PLC0415
        dien_sap_g4,
        dung_g0_g3_da_chot,
        sinh_sap_g4_that,
        xac_nhan_g4,
    )

    g1_path = out_dir / "G1_checkpoint.json"
    g1_cu = _doc_json(g1_path)
    meta_cu = _doc_json(out_dir / "study_meta.json")
    tho = ((g1_cu.get("design") or {}).get("internal_code") if isinstance(g1_cu.get("design"), dict) else None) \
        or g1_cu.get("design_code") or "cohort"
    design_code = SK.ma_thiet_ke_chuoi(tho) or "cohort"
    dung_g0_g3_da_chot(out_dir, study, thiet_ke=design_code)
    # Giữ khoá riêng mà test đã ghi (vd specialist_modules ở G1, gate_params của cổng khác) — chuỗi chỉ làm chủ
    # G0/G1/G3.
    if g1_cu:
        g1_moi = _doc_json(g1_path)
        for khoa, gia_tri in g1_cu.items():
            if khoa != "design" and khoa not in g1_moi:
                g1_moi[khoa] = gia_tri
        g1_path.write_text(json.dumps(g1_moi, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    if meta_cu:
        meta_moi = _doc_json(out_dir / "study_meta.json")
        for khoa, gia_tri in meta_cu.items():
            if khoa == "gate_params" and isinstance(gia_tri, dict):
                for cong, khoi in gia_tri.items():
                    meta_moi.setdefault("gate_params", {}).setdefault(cong, khoi)
            else:
                meta_moi.setdefault(khoa, gia_tri)
        (out_dir / "study_meta.json").write_text(json.dumps(meta_moi, ensure_ascii=False, indent=2),
                                                 encoding="utf-8", newline="\n")

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

    g4_artifact = sinh_sap_g4_that(out_dir, study)
    sap_text = dien_sap_g4(g4_artifact.read_text(encoding="utf-8"))
    g4_artifact.write_text(sap_text, encoding="utf-8", newline="\n")
    xac_nhan_g4(out_dir, sap_text)

    # Khóa RIÊNG nhóm STATISTICIAN — bắt buộc để G4-HUMAN-02 (mức bảo đảm khóa ký) đạt PASS; ký bằng khóa CHUNG chỉ
    # đạt REVIEW nên KHÔNG BAO GIỜ tới được PASS_G4_SAP_LOCKED (đúng thiết kế, mirror G8-HUMAN-03).
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
    CS.xoa_dem()
    bao_cao = G4Q.evaluate_study(study, out_dir, repo_root=repo_root, write=False)
    chua_dat = [(c["id"], c["evidence"][:120]) for c in bao_cao["automatic_criteria"] + bao_cao["approval_criteria"]
                if c["status"] != "PASS"]
    assert bao_cao["status"] == G4Q.STATUS_LOCKED, f"fixture G4 ({design_code}) chưa khoá: {chua_dat}"
    CS.xoa_dem()


def prepare_locked_g5_study(
    study: str,
    source_data: Path,
    *,
    exports_root: Path,
    repo_root: Path,
    approve_g5: bool = True,
    extra_date_columns: frozenset[str] = frozenset(),
) -> tuple[Path, dict]:
    """Chạy intake -> cleaning -> lock -> approval G5 cho dữ liệu tổng hợp.

    `extra_date_columns`: tên cột NGHIÊN CỨU trong `source_data` đã khai
    tường minh kiểu "date" ở nơi khác (vd data_dictionary.json của pipeline
    pseudonymize) — được ghi vào CHÍNH dictionary REDCap canonical mà
    `write_g5_toolkit()` sinh ra, để cả bước quét PII (intake/clean/lock)
    LẪN `g5_quality_gate.evaluate_study()` (vốn đọc dictionary ở đường dẫn
    canonical để chấm G5-AUTO-02..09) đều thấy ĐÚNG MỘT dictionary — tránh
    lệch hash nếu dùng hai file dictionary khác nhau cho hai việc.
    """
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
        extra_date_columns=extra_date_columns,
    )
    prepare_upstream_approvals(study, out_dir, repo_root=repo_root)

    loaded_dictionary = CLEAN._load_dictionary(dictionary_path)
    exempt_date_columns = frozenset(
        RDI._normalize_header(str(rule["name"]))
        for rule in (loaded_dictionary.get("variables") or [])
        if isinstance(rule, dict) and rule.get("type") == "date" and rule.get("name")
    )

    intake = RDI.import_dataset(
        study,
        source_data,
        exports_root=exports_root,
        exempt_date_columns=exempt_date_columns,
    )
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
