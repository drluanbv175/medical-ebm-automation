#!/usr/bin/env python3
"""Hợp đồng chất lượng G9 cho liêm chính tác giả và sẵn sàng công bố.

G9 không đạt chỉ vì đã sinh một bộ biểu mẫu hoặc có một chữ ký PI. Cổng này
đối chiếu trực tiếp gói công bố, xác nhận của từng tác giả bằng mã tham chiếu
không định danh, các cổng tiền đề và chữ ký PI trên đúng checkpoint.

Bốn trạng thái fail-closed:

- ``BLOCKED``: hồ sơ hỏng, có dấu hiệu sửa sau khóa hoặc vi phạm an toàn.
- ``DRAFT_READY_NEEDS_REAL_ATTESTATIONS``: còn xác nhận/bằng chứng đời thực.
- ``READY_FOR_G9_PI_APPROVAL``: mọi tiêu chí đã đủ, chờ PI tự tay phê duyệt.
- ``PASS_G9_PUBLICATION_INTEGRITY_LOCKED``: PI đã ký đúng checkpoint và mọi
  hash/tiền đề vẫn còn hợp lệ.

Module không xác minh danh tính mật mã của từng đồng tác giả. ``evidence_ref``
chỉ là tham chiếu tới form/chữ ký được quản lý bên ngoài repo; PI chịu trách
nhiệm kiểm chúng trước khi ký G9. Không lưu tên, email, điện thoại hoặc PII.
"""

from __future__ import annotations

import hashlib
import json
import re

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import gate_contract as GC

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_READY_NEEDS_REAL_ATTESTATIONS"
STATUS_READY = "READY_FOR_G9_PI_APPROVAL"
STATUS_LOCKED = "PASS_G9_PUBLICATION_INTEGRITY_LOCKED"
QUALITY_CONTRACT_VERSION = "G9-2026.2"

READINESS_JSON = "G9_PUBLICATION_READINESS.json"
REPORT_JSON = "G9_QUALITY_REPORT.json"
REPORT_MD = "G9_QUALITY_REPORT.md"
CHECKPOINT_JSON = "G9_checkpoint.json"

CREDIT_ROLES = {
    "Conceptualization",
    "Data curation",
    "Formal analysis",
    "Funding acquisition",
    "Investigation",
    "Methodology",
    "Project administration",
    "Resources",
    "Software",
    "Supervision",
    "Validation",
    "Visualization",
    "Writing - original draft",
    "Writing - review & editing",
}

STANDARDS_BASIS = (
    {
        "standard": "ICMJE Recommendations, updated January 2026",
        "scope": "Bốn tiêu chí tác giả, phê duyệt bản cuối và trách nhiệm giải trình",
        "url": (
            "https://www.icmje.org/recommendations/browse/roles-and-responsibilities/"
            "defining-the-role-of-authors-and-contributors.html"
        ),
    },
    {
        "standard": "ICMJE Disclosure Form",
        "scope": "Khai báo quan hệ, hoạt động, tài trợ và vai trò nhà tài trợ",
        "url": "https://www.icmje.org/disclosure-of-interest/",
    },
    {
        "standard": "ICMJE Recommendations: AI Use by Authors",
        "scope": "Công khai công cụ/mục đích AI, trách nhiệm con người và bảo mật",
        "url": (
            "https://www.icmje.org/recommendations/browse/artificial-intelligence/"
            "ai-use-by-authors.html"
        ),
    },
    {
        "standard": "ICMJE Clinical Trials and Data Sharing",
        "scope": "Đăng ký và tuyên bố chia sẻ dữ liệu thử nghiệm lâm sàng",
        "url": (
            "https://www.icmje.org/recommendations/browse/publishing-and-editorial-"
            "issues/clinical-trial-registration.html"
        ),
    },
    {
        "standard": "ICMJE Authors' Access to Data, updated January 2026",
        "scope": (
            "Mọi tác giả có thể rà dữ liệu hỗ trợ kết quả; ít nhất một tác giả "
            "phù hợp truy cập dữ liệu gốc và tham gia phân tích; hợp đồng tài trợ "
            "không hạn chế quyền truy cập hoặc độc lập công bố"
        ),
        "url": (
            "https://www.icmje.org/recommendations/browse/publishing-and-editorial-"
            "issues/clinical-trial-registration.html"
        ),
    },
    {
        "standard": "NISO CRediT",
        "scope": "Mười bốn vai trò đóng góp chuẩn hóa; không đồng nghĩa tư cách tác giả",
        "url": "https://credit.niso.org/contributor-roles-defined/",
    },
    {
        # SỬA 2026-07-30 (audit toàn diện G0-G10, G9-F3 — HIGH, trích dẫn sai): DOI
        # cũ "10.24318/LQU1h9US" xác minh trực tiếp qua doi.org REDIRECT tới
        # publicationethics.org/guidance/discussion-document/best-practice-theses-
        # publishing — một tài liệu 2017 về XUẤT BẢN LUẬN VĂN, không liên quan
        # tác giả/AI. DOI đúng cho "COPE Position Statement — Authorship and AI
        # Tools" là "10.24318/cCVRZBms" (redirect xác nhận tới .../cope-position/
        # authorship-and-ai-tools). Đây là báo cáo chất lượng của CHÍNH cổng liêm
        # chính tác giả/AI nên trích sai nguồn này đặc biệt nghiêm trọng.
        "standard": "COPE Position Statement — Authorship and AI Tools",
        "scope": "Tranh chấp tác giả, trách nhiệm và AI không thể là tác giả",
        "doi": "10.24318/cCVRZBms",
    },
    {
        "standard": "COPE Ethical Editing for New Editors",
        "scope": "Minh bạch, sửa sai, rút bài và liêm chính biên tập",
        "doi": "10.24318/cope.2019.1.8",
    },
    {
        "standard": "Think. Check. Submit. / WAME",
        "scope": "Thẩm tra tạp chí đích và nguy cơ tạp chí săn mồi",
        "url": "https://thinkchecksubmit.org/",
    },
)

_PLACEHOLDER_RE = re.compile(
    r"\[(?:CẦN|CAN|TBD|TODO|PENDING)[^\]]*\]|<[^>\n]*(?:điền|fill|name|date)[^>\n]*>",
    re.IGNORECASE,
)
_INTERNAL_TRACE_RE = re.compile(
    r"\b(?:chain[- ]of[- ]thought|internal reasoning|system prompt|agent scratchpad)\b",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?84|0)\s?(?:\d[\s.-]?){8,10}(?!\w)")


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str,
) -> Dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _real_text(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(
        text
        and not _PLACEHOLDER_RE.search(text)
        and text.casefold()
        not in {"none", "null", "unknown", "undecided", "not decided", "chưa quyết định"}
    )


def _iso_date(value: Any) -> bool:
    text = str(value or "").strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return bool(text)


def _guardrail_ok(checkpoint: Mapping[str, Any]) -> bool:
    guardrail = checkpoint.get("guardrail")
    if isinstance(guardrail, Mapping):
        return guardrail.get("passed") is True
    text = str(guardrail or "").upper()
    return "PASS" in text and not any(x in text for x in ("FAIL", "BLOCK", "LỖI"))


def _status_locked(value: Any) -> bool:
    text = str(value or "").upper()
    if any(token in text for token in ("UNLOCK", "NOT LOCK", "CHƯA", "PENDING")):
        return False
    return bool(re.search(r"\bLOCKED\b", text))


def _safe_child(base: Path, value: Any) -> Optional[Path]:
    if not _real_text(value):
        return None
    candidate = Path(str(value))
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(base.resolve())
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved


def _safe_relative(base: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except (OSError, RuntimeError, ValueError):
        return ""


def build_readiness_template(
    study: str,
    n_authors: int,
    target_journal: str = "",
) -> Dict[str, Any]:
    """Tạo hồ sơ G9 fail-closed; không tự xác nhận thay tác giả/PI."""
    return {
        "schema_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "status": STATUS_DRAFT,
        "n_authors": max(1, int(n_authors)),
        "authors": [
            {
                "author_ref": f"AUTHOR-{index:02d}",
                "icmje_criteria": {
                    "substantial_contribution": False,
                    "drafting_or_critical_revision": False,
                    "final_approval": False,
                    "accountability": False,
                },
                "credit_roles": [],
                "coi_form_completed": False,
                "coi_evidence_ref": None,
                "data_access_confirmed": False,
                "attested_at": None,
                "attestation_evidence_ref": None,
            }
            for index in range(1, max(1, int(n_authors)) + 1)
        ],
        "authorship": {
            "order_confirmed": False,
            "credit_mapping_confirmed": False,
            "acknowledgements_permission_confirmed": False,
            "guarantor_author_ref": None,
            "dispute_absent_or_resolved": False,
        },
        "coi_funding": {
            "all_author_forms_complete": False,
            "collective_coi_statement": None,
            "funding_statement": None,
            "sponsor_role_statement": None,
            "sponsor_no_publication_restriction_confirmed": False,
        },
        "ai_disclosure": {
            "ai_used": None,
            "tools": [],
            "purposes": [],
            "human_verification_confirmed": False,
            "sensitive_or_confidential_data_uploaded": None,
            "ai_not_author_confirmed": False,
            "manuscript_statement_final": False,
            "cover_letter_statement_final": False,
            "confirmed_at": None,
        },
        "data_availability": {
            "decision": None,
            "statement_final": False,
            "clinical_trial": None,
            "what_data": None,
            "related_documents": [],
            "available_from": None,
            "availability_duration": None,
            "access_criteria": None,
            "access_mechanism": None,
            "registry_statement_consistent": False,
        },
        "data_access_governance": {
            "all_authors_can_review_supporting_data": False,
            "primary_data_access_author_ref": None,
            "primary_data_access_confirmed": False,
            "analysis_participation_confirmed": False,
            "academic_nonacademic_collaboration": None,
            "primary_data_access_author_is_academic": None,
            "sponsored_research": None,
            "sponsor_agreement_preserves_data_access": False,
            "sponsor_agreement_preserves_publication_independence": False,
            "sponsor_agreement_evidence_ref": None,
            "confirmed_at": None,
        },
        "publication_integrity": {
            "original_work_confirmed": False,
            "duplicate_submission_absent": False,
            "overlap_disclosed": False,
            "preprint_status_declared": False,
            "plagiarism_review_completed": False,
            "plagiarism_report_ref": None,
            "journal_or_institution_criterion": None,
            "human_similarity_review_confirmed": False,
            "image_integrity_reviewed": False,
            "results_match_locked_analysis": False,
            "analysis_deviations_disclosed": False,
        },
        "venue_due_diligence": {
            "target_journal": target_journal or None,
            "official_journal_url": None,
            "scope_fit_confirmed": False,
            "peer_review_process_checked": False,
            "fees_checked": False,
            "archiving_checked": False,
            "correction_retraction_policy_checked": False,
            "indexing_verified_from_primary_source": False,
            "checked_at": None,
        },
        "ethics_and_privacy": {
            "ethics_statement_final": False,
            "consent_or_waiver_statement_final": False,
            "registration_statement_final": False,
            "no_identifiable_participant_content_confirmed": False,
        },
        # THÊM 2026-07-31 (audit tích hợp plugin — khoảng trống NHÓM D của checklist
        # "PHẦN 8 — Hard Gate" mà run_g9_auto.py::build_part8_gate_criteria() in ra
        # cho bác sĩ đọc/ký trên giấy/Word: D1 trưởng đơn vị · D2 hội đồng xét duyệt
        # nội bộ · D3 nhà tài trợ duyệt nội dung — 3 mục này KHÔNG có field cấu trúc
        # nào trước đây (0 kết quả grep "institution"/"sponsor_approv"/"department_head"
        # trong g9_quality_gate.py); mọi mục KHÁC của Phần 8 (NHÓM A/B/C) đã có ánh xạ
        # điện tử qua các khối/tiêu chí khác. Mỗi nhóm dùng cặp *_required (None=chưa
        # xác định, False="không cần" theo đúng checklist gốc, True="cần") + *_confirmed
        # + *_confirmed_at, cùng khuôn venue_due_diligence/ethics_and_privacy ở trên.
        "institutional_confirmation": {
            "department_head_required": None,
            "department_head_confirmed": False,
            "department_head_confirmed_at": None,
            "internal_review_required": None,
            "internal_review_confirmed": False,
            "internal_review_confirmed_at": None,
            "sponsor_review_required": None,
            "sponsor_review_confirmed": False,
            "sponsor_review_confirmed_at": None,
        },
        "final_package": {
            "manuscript_path": f"G7_A8_MANUSCRIPT_{study}.md",
            "reporting_checklist_path": f"G8_A9_PRESUBMISSION_{study}.md",
            "cover_letter_path": f"G9_COVER_LETTER_{study}.md",
            "supplements_paths": [],
            "manuscript_version": None,
            "package_version": None,
            "finalized_at": None,
            "prepared_for_pi_review": False,
        },
        "evidence_policy": (
            "Chỉ dùng author_ref/evidence_ref không định danh. Form chữ ký thật được "
            "quản lý ngoài repo; không ghi tên, email, điện thoại hoặc giấy tờ tùy thân."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


def write_readiness_template(
    out_dir: Path,
    study: str,
    n_authors: int,
    target_journal: str = "",
) -> Path:
    """Ghi hoặc nâng schema template mà không đè xác nhận đời thực đã có."""
    path = out_dir / READINESS_JSON
    existing = _read_json(path)
    authors = existing.get("authors")
    has_real_attestation = bool(
        isinstance(authors, list)
        and any(
            isinstance(author, Mapping)
            and (
                _real_text(author.get("attestation_evidence_ref"))
                or _real_text(author.get("coi_evidence_ref"))
            )
            for author in authors
        )
    )
    author_count_changed = bool(
        existing
        and (
            existing.get("n_authors") != max(1, int(n_authors))
            or not isinstance(authors, list)
            or len(authors) != max(1, int(n_authors))
        )
    )
    template = build_readiness_template(study, n_authors, target_journal)
    if not existing or (author_count_changed and not has_real_attestation):
        path.write_text(
            json.dumps(
                template,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8", newline="\n"
        )
    elif not author_count_changed:
        migrated = deepcopy(existing)

        def fill_missing(target: Dict[str, Any], defaults: Mapping[str, Any]) -> None:
            for key, default in defaults.items():
                if key not in target:
                    target[key] = deepcopy(default)
                elif isinstance(target[key], dict) and isinstance(default, Mapping):
                    fill_missing(target[key], default)

        fill_missing(migrated, template)
        migrated["schema_version"] = QUALITY_CONTRACT_VERSION
        if migrated != existing:
            path.write_text(
                json.dumps(migrated, ensure_ascii=False, indent=2),
                encoding="utf-8", newline="\n"
            )
    return path


def _authors_ok(payload: Mapping[str, Any], expected: int) -> tuple[bool, str]:
    authors = payload.get("authors")
    if not isinstance(authors, list) or len(authors) != expected:
        return False, f"authors={len(authors) if isinstance(authors, list) else 'invalid'}/{expected}"
    refs: list[str] = []
    issues: list[str] = []
    for index, author in enumerate(authors, start=1):
        if not isinstance(author, Mapping):
            issues.append(f"author_{index}:invalid")
            continue
        ref = str(author.get("author_ref") or "").strip()
        refs.append(ref)
        criteria = author.get("icmje_criteria")
        criteria_ok = isinstance(criteria, Mapping) and all(
            criteria.get(key) is True
            for key in (
                "substantial_contribution",
                "drafting_or_critical_revision",
                "final_approval",
                "accountability",
            )
        )
        roles = author.get("credit_roles")
        roles_ok = bool(
            isinstance(roles, list)
            and roles
            and all(str(role) in CREDIT_ROLES for role in roles)
        )
        row_ok = all(
            (
                _real_text(ref),
                criteria_ok,
                roles_ok,
                author.get("coi_form_completed") is True,
                _real_text(author.get("coi_evidence_ref")),
                author.get("data_access_confirmed") is True,
                _iso_date(author.get("attested_at")),
                _real_text(author.get("attestation_evidence_ref")),
            )
        )
        if not row_ok:
            issues.append(f"author_{index}:incomplete")
    if len(set(refs)) != len(refs):
        issues.append("duplicate_author_ref")
    return not issues, ", ".join(issues) or f"{expected} author attestations complete"


def _authorship_ok(payload: Mapping[str, Any], author_refs: set[str]) -> tuple[bool, str]:
    value = payload.get("authorship")
    value = value if isinstance(value, Mapping) else {}
    guarantor = str(value.get("guarantor_author_ref") or "").strip()
    ok = all(
        (
            value.get("order_confirmed") is True,
            value.get("credit_mapping_confirmed") is True,
            value.get("acknowledgements_permission_confirmed") is True,
            value.get("dispute_absent_or_resolved") is True,
            guarantor in author_refs,
        )
    )
    return ok, f"guarantor={guarantor or 'missing'}; confirmations={ok}"


def _coi_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("coi_funding")
    value = value if isinstance(value, Mapping) else {}
    ok = all(
        (
            value.get("all_author_forms_complete") is True,
            _real_text(value.get("collective_coi_statement")),
            _real_text(value.get("funding_statement")),
            _real_text(value.get("sponsor_role_statement")),
            value.get("sponsor_no_publication_restriction_confirmed") is True,
        )
    )
    return ok, f"all_forms={value.get('all_author_forms_complete')}; statements_complete={ok}"


def _ai_ok(payload: Mapping[str, Any]) -> tuple[bool, str, bool]:
    value = payload.get("ai_disclosure")
    value = value if isinstance(value, Mapping) else {}
    ai_used = value.get("ai_used")
    unsafe = value.get("sensitive_or_confidential_data_uploaded") is True
    common = all(
        (
            ai_used in {True, False},
            value.get("human_verification_confirmed") is True,
            value.get("sensitive_or_confidential_data_uploaded") is False,
            value.get("ai_not_author_confirmed") is True,
            value.get("manuscript_statement_final") is True,
            value.get("cover_letter_statement_final") is True,
            _iso_date(value.get("confirmed_at")),
        )
    )
    details = True
    if ai_used is True:
        tools = value.get("tools")
        purposes = value.get("purposes")
        details = bool(
            isinstance(tools, list)
            and tools
            and all(_real_text(item) for item in tools)
            and isinstance(purposes, list)
            and purposes
            and all(_real_text(item) for item in purposes)
        )
    return common and details, f"ai_used={ai_used}; unsafe_upload={unsafe}; details={details}", unsafe


def _data_availability_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("data_availability")
    value = value if isinstance(value, Mapping) else {}
    decision = str(value.get("decision") or "").strip().upper()
    base = bool(
        decision in {"OPEN", "CONTROLLED_ACCESS", "NOT_SHARED_WITH_JUSTIFICATION"}
        and value.get("statement_final") is True
        and value.get("clinical_trial") in {True, False}
    )
    trial_ok = True
    if value.get("clinical_trial") is True:
        related = value.get("related_documents")
        trial_ok = all(
            (
                _real_text(value.get("what_data")),
                isinstance(related, list) and bool(related),
                _real_text(value.get("available_from")),
                _real_text(value.get("availability_duration")),
                _real_text(value.get("access_criteria")),
                _real_text(value.get("access_mechanism")),
                value.get("registry_statement_consistent") is True,
            )
        )
    elif decision in {"OPEN", "CONTROLLED_ACCESS"}:
        trial_ok = all(
            (
                _real_text(value.get("what_data")),
                _real_text(value.get("access_mechanism")),
            )
        )
    elif decision == "NOT_SHARED_WITH_JUSTIFICATION":
        trial_ok = _real_text(value.get("access_criteria"))
    return base and trial_ok, f"decision={decision or 'missing'}; trial_detail={trial_ok}"


def data_access_governance_ok(
    payload: Mapping[str, Any],
    author_refs: set[str],
) -> tuple[bool, str]:
    """Kiểm nghĩa vụ quyền truy cập dữ liệu mới của ICMJE 1/2026."""
    value = payload.get("data_access_governance")
    value = value if isinstance(value, Mapping) else {}
    author_ref = str(value.get("primary_data_access_author_ref") or "").strip()
    collaboration = value.get("academic_nonacademic_collaboration")
    sponsored = value.get("sponsored_research")
    base_ok = all(
        (
            value.get("all_authors_can_review_supporting_data") is True,
            author_ref in author_refs,
            value.get("primary_data_access_confirmed") is True,
            value.get("analysis_participation_confirmed") is True,
            isinstance(collaboration, bool),
            isinstance(sponsored, bool),
            _iso_date(value.get("confirmed_at")),
        )
    )
    collaboration_ok = (
        collaboration is False
        or value.get("primary_data_access_author_is_academic") is True
    )
    sponsor_ok = sponsored is False or all(
        (
            value.get("sponsor_agreement_preserves_data_access") is True,
            value.get("sponsor_agreement_preserves_publication_independence") is True,
            _real_text(value.get("sponsor_agreement_evidence_ref")),
        )
    )
    ok = base_ok and collaboration_ok and sponsor_ok
    return ok, (
        f"author_ref={author_ref or 'missing'}; all_authors_review="
        f"{value.get('all_authors_can_review_supporting_data')}; "
        f"collaboration_ok={collaboration_ok}; sponsored={sponsored}; sponsor_ok={sponsor_ok}"
    )


def _publication_integrity_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("publication_integrity")
    value = value if isinstance(value, Mapping) else {}
    ok = all(
        (
            value.get("original_work_confirmed") is True,
            value.get("duplicate_submission_absent") is True,
            value.get("overlap_disclosed") is True,
            value.get("preprint_status_declared") is True,
            value.get("plagiarism_review_completed") is True,
            _real_text(value.get("plagiarism_report_ref")),
            _real_text(value.get("journal_or_institution_criterion")),
            value.get("human_similarity_review_confirmed") is True,
            value.get("image_integrity_reviewed") is True,
            value.get("results_match_locked_analysis") is True,
            value.get("analysis_deviations_disclosed") is True,
        )
    )
    return ok, (
        f"original={value.get('original_work_confirmed')}; "
        f"similarity_review={value.get('human_similarity_review_confirmed')}; "
        f"results_locked={value.get('results_match_locked_analysis')}"
    )


def _venue_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("venue_due_diligence")
    value = value if isinstance(value, Mapping) else {}
    url = str(value.get("official_journal_url") or "").strip()
    ok = all(
        (
            _real_text(value.get("target_journal")),
            bool(re.match(r"^https://", url, re.IGNORECASE)),
            value.get("scope_fit_confirmed") is True,
            value.get("peer_review_process_checked") is True,
            value.get("fees_checked") is True,
            value.get("archiving_checked") is True,
            value.get("correction_retraction_policy_checked") is True,
            value.get("indexing_verified_from_primary_source") is True,
            _iso_date(value.get("checked_at")),
        )
    )
    return ok, f"journal={value.get('target_journal') or 'missing'}; due_diligence={ok}"


def _ethics_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("ethics_and_privacy")
    value = value if isinstance(value, Mapping) else {}
    ok = all(
        value.get(key) is True
        for key in (
            "ethics_statement_final",
            "consent_or_waiver_statement_final",
            "registration_statement_final",
            "no_identifiable_participant_content_confirmed",
        )
    )
    return ok, f"final_ethics_privacy_statements={ok}"


def _institutional_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    """NHÓM D của checklist Phần 8 (run_g9_auto.py) — xem THÊM 2026-07-31 ở
    build_readiness_template(). Mỗi nhóm OK khi: (a) đánh dấu rõ "không cần"
    (required=False, đúng lựa chọn ☐ Không cần trên checklist gốc), hoặc
    (b) required=True VÀ đã xác nhận VÀ có ngày xác nhận thật. required=None
    (chưa trả lời) KHÔNG ok — bác sĩ phải trả lời rõ, không được bỏ trống."""
    value = payload.get("institutional_confirmation")
    value = value if isinstance(value, Mapping) else {}

    def _group_ok(prefix: str) -> bool:
        required = value.get(f"{prefix}_required")
        if required is False:
            return True
        if required is True:
            return (
                value.get(f"{prefix}_confirmed") is True
                and _iso_date(value.get(f"{prefix}_confirmed_at"))
            )
        return False

    groups = ("department_head", "internal_review", "sponsor_review")
    ok = all(_group_ok(g) for g in groups)
    detail = "; ".join(
        f"{g}(required={value.get(f'{g}_required')!r},confirmed={value.get(f'{g}_confirmed')!r})"
        for g in groups
    )
    return ok, detail


def _package_files(
    study: str,
    out_dir: Path,
    readiness: Mapping[str, Any],
) -> Dict[str, Optional[Path]]:
    final = readiness.get("final_package")
    final = final if isinstance(final, Mapping) else {}
    files: Dict[str, Optional[Path]] = {
        "integrity_package": out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md",
        "manuscript": _safe_child(out_dir, final.get("manuscript_path")),
        "reporting_checklist": _safe_child(out_dir, final.get("reporting_checklist_path")),
        "cover_letter": _safe_child(out_dir, final.get("cover_letter_path")),
        "presubmission_review": out_dir / f"G8_A9_PRESUBMISSION_{study}.md",
        "citation_verification": out_dir / f"A12_CITATION_VERIFICATION_{study}.md",
        "citation_retraction_receipt": out_dir / "A12_RETRACTION_RECEIPT.json",
        "citation_metadata_receipt": out_dir / "A12_METADATA_RECEIPT.json",
        "publication_readiness": out_dir / READINESS_JSON,
    }
    supplements = final.get("supplements_paths")
    if isinstance(supplements, list):
        for index, value in enumerate(supplements, start=1):
            files[f"supplement_{index:02d}"] = _safe_child(out_dir, value)
    return files


def _manifest(out_dir: Path, files: Mapping[str, Optional[Path]]) -> Dict[str, Any]:
    rows: Dict[str, Any] = {}
    for key, path in files.items():
        rows[key] = {
            "path": _safe_relative(out_dir, path) if path else "",
            "sha256": _sha256(path),
        }
    package_digest = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"algorithm": "SHA-256", "files": rows, "package_sha256": package_digest}


def _manifest_matches(expected: Any, current: Mapping[str, Any]) -> bool:
    return isinstance(expected, Mapping) and dict(expected) == dict(current)


def _documents_clean(files: Mapping[str, Optional[Path]]) -> tuple[bool, str, bool]:
    required = (
        "integrity_package",
        "manuscript",
        "reporting_checklist",
        "cover_letter",
        "presubmission_review",
        "citation_verification",
        "citation_retraction_receipt",
        "citation_metadata_receipt",
        "publication_readiness",
    )
    missing = [key for key in required if not files.get(key) or not files[key].is_file()]
    if missing:
        return False, "missing=" + ",".join(missing), False
    placeholder_hits: list[str] = []
    trace_hits: list[str] = []
    for key in ("integrity_package", "manuscript", "reporting_checklist", "cover_letter"):
        path = files[key]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False, f"unreadable={key}", True
        if _PLACEHOLDER_RE.search(text):
            placeholder_hits.append(key)
        if _INTERNAL_TRACE_RE.search(text):
            trace_hits.append(key)
    clean = not placeholder_hits and not trace_hits
    return clean, f"placeholders={placeholder_hits}; internal_traces={trace_hits}", bool(trace_hits)


def _readiness_has_contact_pii(readiness_path: Path) -> bool:
    try:
        text = readiness_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True
    return bool(_EMAIL_RE.search(text) or _PHONE_RE.search(text))


# THÊM 2026-08-30 (audit cổng, khoảng hở #5): đọc NGƯỢC trạng thái tick ☐/☑
# của mục "Phần 8 — Hard Gate" trong A10. Chỉ đếm ☑/☒/[x] — các ký tự bác sĩ
# gõ THAY cho ☐ khi tích tay; CỐ Ý không đếm ✅ vì template run_g9_auto.py tự
# in ✅ cho trạng thái cổng dẫn xuất (G2/G4...) ngay trong artifact — đếm nó là
# tự-dương-tính (cùng họ tautology đã vá ở G3/G8).
_PART8_HEADER_RE = re.compile(r"ph[ầa]n\s*8", re.IGNORECASE)
_PART8_TICKED_RE = re.compile(r"[☑☒]|\[[xX]\]")


def _part8_tick_state(a10_path: Path) -> tuple[Optional[bool], int, int]:
    """Trả (tìm_thấy_mục_Phần_8, số_ô_đã_tích, số_ô_còn_trống).

    ``None`` ở phần tử đầu nghĩa là KHÔNG đọc được (file thiếu / đổi khuôn) —
    khác với "đọc được nhưng 0 tick"; người gọi không được gộp hai trạng thái
    này (bài học BH08: không biến CHƯA BIẾT thành CÓ VẤN ĐỀ hay ngược lại).
    """
    try:
        text = a10_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (None, 0, 0)
    m = _PART8_HEADER_RE.search(text)
    if not m:
        return (None, 0, 0)
    # Phần 8 là mục cuối của A10 theo thiết kế run_g9_auto.py — lấy từ header
    # tới hết file; nếu khuôn đổi (Phần 8 không còn cuối) thì tick của mục sau
    # cũng bị đếm, nhưng đó là sai lệch về phía CẢNH BÁO THÊM chứ không im lặng.
    section = text[m.start():]
    ticked = len(_PART8_TICKED_RE.findall(section))
    unticked = section.count("☐") + section.count("[ ]")
    return (True, ticked, unticked)


def _part8_consistency(
    found: Optional[bool],
    ticked: int,
    unticked: int,
    pre_pending: bool,
    approved: bool,
) -> tuple[str, str]:
    """Phán quyết chỉ-dấu G9-AUTO-08 — hàm THUẦN để test đủ 4 nhánh.

    Hai chiều lệch tờ-giấy ↔ hồ-sơ-điện-tử; mọi nhánh đều REVIEW (advisory),
    không bao giờ BLOCK — tờ Phần 8 là bản tóm tắt, không phải cổng.
    """
    if found is None:
        return "REVIEW", (
            "không đọc được mục 'Phần 8' trong A10 (file thiếu hoặc đổi khuôn) — "
            "chưa biết trạng thái tick, KHÔNG suy đoán"
        )
    if ticked and pre_pending and not approved:
        return "REVIEW", (
            f"tờ Phần 8 đã tích {ticked} ô nhưng hồ sơ điện tử còn tiêu chí "
            "chưa đạt — tờ giấy không phải cổng, cổng thật đọc gate_params/JSON"
        )
    if approved and ticked == 0:
        return "REVIEW", (
            f"sổ cái đã ký G9 nhưng tờ Phần 8 chưa tích ô nào (☐ còn {unticked}) "
            "— bản in không còn khớp hồ sơ"
        )
    return "PASS", (
        f"tick ☑/☒/[x]={ticked}, ☐ còn {unticked}; nhất quán với hồ sơ điện tử"
    )


def _write_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# BÁO CÁO CHẤT LƯỢNG G9",
        "",
        f"**Đề tài:** {report.get('study')}",
        f"**Hợp đồng:** {report.get('quality_contract_version')}",
        f"**Trạng thái:** `{report.get('status')}`",
        "",
        "| Tiêu chí | Kết quả | Bằng chứng |",
        "|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        lines.append(
            f"| {row.get('id')} — {row.get('label')} | {row.get('status')} | "
            f"{str(row.get('evidence') or '').replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Việc còn lại",
            "",
            *[f"- {item}" for item in report.get("actions", [])],
            "",
            "## Giới hạn bảo đảm",
            "",
            str(report.get("assurance_limit") or ""),
            "",
            "Cần bác sĩ kiểm chứng.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def evaluate_study(
    study: str,
    out_dir: Path,
    *,
    repo_root: Optional[Path] = None,
    write: bool = False,
) -> Dict[str, Any]:
    """Chấm G9 trực tiếp từ artifact hiện hành; không tin report lưu sẵn."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / CHECKPOINT_JSON
    readiness_path = out_dir / READINESS_JSON
    checkpoint = _read_json(checkpoint_path)
    readiness = _read_json(readiness_path)
    meta = GC.load_study_meta(out_dir)
    rows: list[Dict[str, str]] = []

    structure_ok = bool(
        checkpoint.get("gate") == "G9"
        and checkpoint.get("study") == study
        and checkpoint.get("quality_contract_version") == QUALITY_CONTRACT_VERSION
        and readiness.get("schema_version") == QUALITY_CONTRACT_VERSION
        and readiness.get("study") == study
        and readiness.get("disclaimer") == "Cần bác sĩ kiểm chứng."
    )
    rows.append(
        _criterion(
            "G9-AUTO-01",
            f"Checkpoint và hồ sơ readiness đúng schema {QUALITY_CONTRACT_VERSION}",
            "PASS" if structure_ok else "BLOCK",
            f"checkpoint={bool(checkpoint)}; readiness={bool(readiness)}; schema={readiness.get('schema_version')}",
            "Chạy lại run_g9_auto.py; không ký file tự tạo hoặc schema không hợp lệ.",
        )
    )

    # SỬA 2026-07-30 (audit toàn diện G0-G10, G9-F5 — MEDIUM, cùng lớp "tin
    # cache cũ" đã đóng ở G7-AUTO-00/G8-AUTO-00/G4-AUTO-00 trong phiên này):
    # trước đây đọc thẳng checkpoint["guardrail"] — giá trị ĐÓNG BĂNG tại thời
    # điểm run_g9_auto.py sinh artifact — dù file A10 thật (G9_A10_AUTHOR_
    # INTEGRITY_<study>.md) có thể đọc lại FRESH từ đĩa ngay tại đây. Đồng
    # thời: 4/7 luật (R4/R5/R6/R7) kiểm boilerplate mà generator luôn in cứng
    # (nhãn DRAFT/CHỜ, placeholder [CẦN], 8 tiêu đề PHẦN, disclaimer) — không
    # thể fail bất kể nội dung — chỉ R1(PII)/R2(DOI bịa)/R3(tự claim PASSED)
    # thật sự phản ứng với nội dung. Chạy lại guardrail_check_g9() trên file
    # thật ít nhất để R1-R3 bắt được tampering xảy ra SAU khi sinh.
    try:
        import run_g9_auto as G9run  # noqa: PLC0415
        a10_path = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
        a10_text = a10_path.read_text(encoding="utf-8") if a10_path.exists() else ""
        fresh_guardrail = G9run.guardrail_check_g9(a10_text)
        guardrail_ok = bool(fresh_guardrail.get("passed")) if a10_text else False
        guardrail_evidence = f"guardrail_passed={guardrail_ok} (chấm lại trên A10 hiện tại, không tin cache)"
    except ImportError:  # pragma: no cover - lưới an toàn nếu import thất bại
        guardrail_ok = _guardrail_ok(checkpoint)
        guardrail_evidence = f"guardrail={checkpoint.get('guardrail')}"
    rows.append(
        _criterion(
            "G9-AUTO-02",
            "Guardrail gói G9 đạt và không tự tuyên bố PASSED",
            "PASS" if guardrail_ok else "BLOCK",
            guardrail_evidence,
            "Sửa mọi lỗi guardrail trong gói G9 trước khi thu xác nhận.",
        )
    )

    g2_cp = _read_json(out_dir / "G2_checkpoint.json")
    g8_artifact = out_dir / f"G8_A9_PRESUBMISSION_{study}.md"
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL, cùng lỗi cũng thấy ở
    # g10_quality_gate.py::G10-AUTO-04): _status_locked(g2/g4.get("g*_status")) kiểm
    # một chuỗi mà run_g2_auto.py/run_g4_auto.py KHÔNG BAO GIỜ ghi ("LOCKED") — cả hai
    # chỉ ghi "PENDING"/"BLOCKED — ...". g4_ok vì vậy vĩnh viễn False cho MỌI đề tài
    # thật, dù chữ ký ledger G4 hợp lệ. Vá theo đúng khuôn g5_ok bên dưới đã dùng đúng
    # (chấm trực tiếp qua hàm hợp đồng chất lượng, không đọc field text đã lỗi thời).
    g2_ok = bool(
        GC.ledger_approved(
            "G2", study, out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md", repo_root=root
        )
        and GC.g2_quality_contract_satisfied(g2_cp, meta)
    )
    g4_ok = GC.g4_quality_contract_satisfied(study, repo_root=root)
    g5_ok = GC.g5_quality_contract_satisfied(study, repo_root=root)
    g8_ok = bool(
        g8_artifact.exists()
        and GC.ledger_approved("G8", study, g8_artifact, repo_root=root)
    )
    upstream_ok = g2_ok and g4_ok and g5_ok and g8_ok
    rows.append(
        _criterion(
            "G9-AUTO-03",
            "G2, G4, G5 và G8 còn khóa hợp lệ",
            "PASS" if upstream_ok else "REVIEW",
            f"G2={g2_ok}; G4={g4_ok}; G5={g5_ok}; G8={g8_ok}",
            "Hoàn tất các cổng tiền đề bằng đúng vai trò và artifact trước G9.",
        )
    )

    try:
        import run_g10_assemble as G10  # noqa: PLC0415

        citation_ok, citation_reason = G10.citation_verification_ok(study, out_dir)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        citation_ok, citation_reason = False, str(exc)
    rows.append(
        _criterion(
            "G9-AUTO-04",
            "A12 xác minh trích dẫn, rút bài và metadata",
            "PASS" if citation_ok else "REVIEW",
            citation_reason or "A12 current receipts valid",
            "Chạy lại A12 trên toàn bộ trích dẫn và xử lý mọi cảnh báo trước G9.",
        )
    )

    expected_authors = int(checkpoint.get("n_authors") or 0)
    authors_ok, authors_evidence = _authors_ok(readiness, expected_authors)
    rows.append(
        _criterion(
            "G9-HUMAN-01",
            "Mỗi tác giả xác nhận đủ 4 tiêu chí ICMJE, CRediT, COI và bản cuối",
            "PASS" if authors_ok else "REVIEW",
            authors_evidence,
            "Thu form thật của từng tác giả; chỉ ghi author_ref/evidence_ref không định danh.",
        )
    )
    author_refs = {
        str(row.get("author_ref") or "").strip()
        for row in readiness.get("authors", [])
        if isinstance(row, Mapping)
    }
    authorship_ok, authorship_evidence = _authorship_ok(readiness, author_refs)
    rows.append(
        _criterion(
            "G9-HUMAN-02",
            "Thứ tự tác giả, CRediT, acknowledgements và guarantor đã chốt",
            "PASS" if authorship_ok else "REVIEW",
            authorship_evidence,
            "Giải quyết tranh chấp và xác nhận mapping đóng góp trước khi PI ký.",
        )
    )

    coi_ok, coi_evidence = _coi_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-03",
            "COI, tài trợ và vai trò nhà tài trợ đầy đủ",
            "PASS" if coi_ok else "REVIEW",
            coi_evidence,
            "Hoàn tất form ICMJE hiện hành và tuyên bố tập thể/funding/sponsor.",
        )
    )

    ai_ok, ai_evidence, unsafe_ai = _ai_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-04",
            "Khai báo AI đúng công cụ/mục đích, con người chịu trách nhiệm và không tải dữ liệu nhạy cảm",
            "BLOCK" if unsafe_ai else ("PASS" if ai_ok else "REVIEW"),
            ai_evidence,
            (
                "Nếu đã tải dữ liệu nhạy cảm lên AI, dừng phát hành và thực hiện xử lý sự cố "
                "bảo mật; nếu không, hoàn tất khai báo AI thực tế."
            ),
        )
    )

    data_ok, data_evidence = _data_availability_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-05",
            "Tuyên bố dữ liệu cuối cùng; thử nghiệm có đủ who/what/when/how",
            "PASS" if data_ok else "REVIEW",
            data_evidence,
            "Chốt quyết định chia sẻ và chi tiết ICMJE; không để UNDECIDED.",
        )
    )

    access_ok, access_evidence = data_access_governance_ok(readiness, author_refs)
    rows.append(
        _criterion(
            "G9-HUMAN-05A",
            "Quyền tác giả truy cập dữ liệu và độc lập phân tích/công bố theo ICMJE 1/2026",
            "PASS" if access_ok else "REVIEW",
            access_evidence,
            (
                "Xác nhận mọi tác giả có thể rà dữ liệu hỗ trợ; chỉ định author_ref đã "
                "truy cập dữ liệu gốc và tham gia phân tích; nếu có tài trợ, dẫn chiếu "
                "hợp đồng bảo toàn quyền truy cập và độc lập công bố."
            ),
        )
    )

    integrity_ok, integrity_evidence = _publication_integrity_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-06",
            "Nguyên gốc, không nộp song song, overlap/preprint, similarity và kết quả đã rà",
            "PASS" if integrity_ok else "REVIEW",
            integrity_evidence,
            (
                "Rà similarity theo tiêu chí của tạp chí/cơ sở và phán đoán con người; "
                "không dùng một ngưỡng phần trăm phổ quát để kết luận đạo văn."
            ),
        )
    )

    venue_ok, venue_evidence = _venue_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-07",
            "Tạp chí đích được kiểm từ nguồn chính thức",
            "PASS" if venue_ok else "REVIEW",
            venue_evidence,
            "Kiểm scope, peer review, phí, lưu trữ, sửa/rút bài và indexing từ nguồn gốc.",
        )
    )

    ethics_ok, ethics_evidence = _ethics_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-08",
            "Ethics/consent/registration cuối và không lộ định danh người tham gia",
            "PASS" if ethics_ok else "REVIEW",
            ethics_evidence,
            "PI rà toàn văn và hình/phụ lục; loại dữ liệu nhận diện trước phát hành.",
        )
    )

    # THÊM 2026-07-31 (audit tích hợp plugin): đóng khoảng trống NHÓM D của
    # checklist "PHẦN 8 — Hard Gate" (run_g9_auto.py) — trưởng đơn vị/hội đồng
    # nội bộ/nhà tài trợ duyệt nội dung trước khi nộp. Trước bản vá này, đây là
    # khoảng trống THẬT duy nhất trong Phần 8 (NHÓM A/B/C đều đã có ánh xạ điện
    # tử qua các tiêu chí khác). Tờ giấy Phần 8 vẫn là bản TÓM TẮT cho bác sĩ
    # đọc — xác nhận thật vẫn qua gate_params/JSON như mọi G9-HUMAN khác.
    # CẬP NHẬT 2026-08-30: cơ chế đọc ngược tick ☐/☑ (trước đây "để ngỏ cho
    # tới khi có yêu cầu rõ") nay ĐÃ CÓ ở G9-AUTO-08 dưới — advisory-only,
    # không thay xác nhận điện tử.
    institutional_ok, institutional_evidence = _institutional_ok(readiness)
    rows.append(
        _criterion(
            "G9-HUMAN-11",
            "Xác nhận thể chế (NHÓM D — trưởng đơn vị/hội đồng nội bộ/nhà tài trợ)",
            "PASS" if institutional_ok else "REVIEW",
            institutional_evidence,
            (
                "Với mỗi nhóm: đánh dấu 'không cần' nếu đúng, hoặc xác nhận đã duyệt kèm "
                "ngày trong institutional_confirmation của G9_PUBLICATION_READINESS.json."
            ),
        )
    )

    final = readiness.get("final_package")
    final = final if isinstance(final, Mapping) else {}
    package_meta_ok = all(
        (
            _real_text(final.get("manuscript_version")),
            _real_text(final.get("package_version")),
            _iso_date(final.get("finalized_at")),
            final.get("prepared_for_pi_review") is True,
        )
    )
    files = _package_files(study, out_dir, readiness)
    docs_ok, docs_evidence, internal_trace = _documents_clean(files)
    rows.append(
        _criterion(
            "G9-AUTO-05",
            "Gói cuối đủ file, không placeholder và không lộ dấu vết nội bộ",
            "BLOCK" if internal_trace else ("PASS" if docs_ok and package_meta_ok else "REVIEW"),
            f"{docs_evidence}; package_metadata={package_meta_ok}",
            "Hoàn thiện manuscript/checklist/cover letter/supplement và xóa mọi placeholder.",
        )
    )

    contact_pii = _readiness_has_contact_pii(readiness_path)
    rows.append(
        _criterion(
            "G9-AUTO-06",
            "Hồ sơ readiness chỉ dùng mã tham chiếu, không lưu email/điện thoại",
            "BLOCK" if contact_pii else "PASS",
            f"contact_pii_detected={contact_pii}",
            "Xóa PII khỏi JSON; lưu form nhận diện/chữ ký ở hệ thống được kiểm soát.",
        )
    )

    current_manifest = _manifest(out_dir, files)
    saved_manifest = checkpoint.get("publication_manifest")
    g9_approved = bool(
        checkpoint_path.exists()
        and GC.ledger_approved("G9", study, checkpoint_path, repo_root=root)
    )
    manifest_ok = _manifest_matches(saved_manifest, current_manifest)
    # Trước chữ ký, evaluator được phép tạo/cập nhật manifest. Sau chữ ký, mọi
    # thay đổi phải chặn thay vì âm thầm "hợp thức hóa" hash mới.
    manifest_status = (
        "PASS"
        if manifest_ok or (write and not g9_approved)
        else ("BLOCK" if g9_approved else "REVIEW")
    )
    rows.append(
        _criterion(
            "G9-AUTO-07",
            "Manifest SHA-256 ràng buộc toàn bộ gói và còn nguyên sau khóa",
            manifest_status,
            (
                f"manifest_match={manifest_ok}; g9_approved={g9_approved}; "
                f"package_sha256={current_manifest['package_sha256']}"
            ),
            "Trước ký: chạy lại g9_quality_gate.py để cập nhật manifest. Sau ký: điều tra thay đổi và ký lại có chủ ý.",
        )
    )

    rows.append(
        _criterion(
            "G9-HUMAN-09",
            "PI phê duyệt đúng G9_checkpoint.json sau khi mọi tiêu chí đạt",
            "PASS" if g9_approved else "REVIEW",
            f"approval_ledger_G9={g9_approved}",
            (
                "PI tự tay chạy approve_gate.py cho G9 sau khi kiểm form từng tác giả; "
                "agent không tự phê duyệt."
            ),
        )
    )

    # SỬA 2026-07-30 (audit toàn diện G0-G10, G9-F6 — MEDIUM): g8_quality_gate.py
    # (G8-HUMAN-04) đã đối chiếu reviewer_ref của G8 với TẤT CẢ cổng khác — kể cả
    # G9 — để phát hiện "cùng một người ký nhiều vai trò". Nhưng vì G8 thường ký
    # TRƯỚC G9 trong luồng chuẩn, lúc đó G9 CHƯA có bản ghi nên phép đối chiếu ở
    # G8 luôn "chưa có gì để so" — thời điểm DUY NHẤT phép so khớp này có ý nghĩa
    # thật (sau khi CẢ HAI đã ký) là ở phía G9, nhưng g9_quality_gate.py trước vá
    # này không có đối chiếu ngược lại nào (grep xác nhận 0 kết quả cho
    # "reviewer_ref"/"cross_gate"). Tái dùng ledger_records/_latest_approved/
    # _reviewer_ref của g8_quality_gate.py (import lười, không viết lại).
    try:
        import g8_quality_gate as G8Q  # noqa: PLC0415
        records = G8Q.ledger_records(study, root)
        cross_refs = {
            gate: G8Q._reviewer_ref(G8Q._latest_approved(records, gate))
            for gate in ("G2", "G4", "G5", "G8", "G9")
        }
        g9_ref = cross_refs.get("G9", "")
        clashes = [
            gate for gate, ref in cross_refs.items()
            if gate != "G9" and ref and g9_ref and ref == g9_ref
        ]
        if not g9_ref:
            ref_status, ref_evidence = "REVIEW", "chưa có bản ghi phê duyệt G9 để đối chiếu"
        elif clashes:
            ref_status = "REVIEW"
            ref_evidence = (
                f"reviewer_ref của G9 ({g9_ref!r}) TRÙNG với cổng {', '.join(sorted(clashes))} "
                "— cùng một người đang ký nhiều vai trò"
            )
        else:
            ref_status = "PASS"
            ref_evidence = f"reviewer_ref của G9 ({g9_ref!r}) khác mọi cổng còn lại"
    except ImportError:  # pragma: no cover - lưới an toàn nếu import thất bại
        ref_status, ref_evidence = "REVIEW", "không đọc được g8_quality_gate.py để đối chiếu"
    rows.append(
        _criterion(
            "G9-HUMAN-10",
            "Người ký G9 (PI) khác người ký các cổng khác (chỉ dấu độc lập)",
            ref_status,
            ref_evidence,
            "Đối chiếu vai trò ký; nếu trùng người, cân nhắc mời phản biện/thống kê viên độc lập khác cho lần sau.",
        )
    )

    # THÊM 2026-08-30 (audit cổng, khoảng hở #5): cơ chế ĐỌC NGƯỢC tick ☐/☑
    # của checklist "Phần 8 — Hard Gate" — đóng đúng khoảng trống mà chú thích
    # G9-HUMAN-11 từng ghi "để ngỏ cho tới khi có yêu cầu rõ" (yêu cầu rõ: chỉ
    # thị bác sĩ 30/08 «các khoảng hở... hoàn thiện cho xanh»). Tờ Phần 8 vẫn
    # KHÔNG phải cổng — tiêu chí này chỉ soi HAI chiều lệch giữa tờ giấy và hồ
    # sơ điện tử: (a) tờ đã tích mà tiêu chí điện tử còn thiếu — bác sĩ tưởng
    # xong nhưng cổng thật chưa được nạp; (b) sổ cái đã ký mà tờ chưa tích ô
    # nào — bản in không còn khớp hồ sơ. pre_rows_pending phải tính TRƯỚC khi
    # append tiêu chí này (tự tham chiếu là vòng lặp).
    a10_for_part8 = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
    part8_found, part8_ticked, part8_unticked = _part8_tick_state(a10_for_part8)
    pre_rows_pending = any(
        row["status"] != "PASS" and row["id"] not in ("G9-HUMAN-09", "G9-HUMAN-10")
        for row in rows
    )
    part8_status, part8_evidence = _part8_consistency(
        part8_found, part8_ticked, part8_unticked, pre_rows_pending, g9_approved
    )
    rows.append(
        _criterion(
            "G9-AUTO-08",
            "Đọc ngược tick ☐/☑ tờ 'Phần 8 — Hard Gate' và đối chiếu hồ sơ điện tử (chỉ dấu)",
            part8_status,
            part8_evidence,
            (
                "Đồng bộ tờ Phần 8 với gate_params/G9_PUBLICATION_READINESS.json; "
                "tờ giấy là bản tóm tắt cho bác sĩ, cổng thật đọc JSON."
            ),
        )
    )

    # G9-HUMAN-10 CỐ Ý không gate STATUS_LOCKED (loại trừ khỏi non_pi_pending
    # cùng G9-HUMAN-09): g9_ref chỉ có giá trị SAU KHI G9 đã ký, nên nếu tiêu
    # chí này gate LOCKED, một đề tài sẽ KHÔNG BAO GIỜ đạt READY_FOR_G9_PI_
    # APPROVAL trước khi ký (bẫy con-gà-quả-trứng) — mô hình 4 trạng thái của
    # G9 (khác 5 trạng thái của G8) không có chỗ cho một mức "đã ký nhưng còn
    # cảnh báo độc lập" riêng. Đây vẫn là tín hiệu THẬT hiển thị trong báo cáo
    # (không bị ẩn), chỉ không tự động chặn khóa — cùng tinh thần "chỉ dấu,
    # không phải phán quyết" mà G8-HUMAN-04 đã ghi.
    # G9-AUTO-08 cũng ADVISORY-ONLY (cùng danh sách loại trừ): gate hoá tín
    # hiệu tờ-giấy sẽ (a) lật trạng thái đề tài ĐÃ khóa từ trước — hồi quy
    # thật với mọi consumer của G9Q, và (b) phạt chính việc bác sĩ tích tờ
    # sớm — đúng lỗi "phạt người điền thật" đã phải vá ở G8 R6 (2026-07-30).
    any_block = any(row["status"] == "BLOCK" for row in rows)
    non_pi_pending = any(
        row["status"] != "PASS"
        and row["id"] not in ("G9-HUMAN-09", "G9-HUMAN-10", "G9-AUTO-08")
        for row in rows
    )
    if any_block:
        status = STATUS_BLOCKED
    elif non_pi_pending:
        status = STATUS_DRAFT
    elif not g9_approved:
        status = STATUS_READY
    else:
        status = STATUS_LOCKED

    actions = list(
        dict.fromkeys(
            row["action"]
            for row in rows
            if row["status"] != "PASS" and row.get("action")
        )
    )
    report: Dict[str, Any] = {
        "kind": "g9_quality_report",
        "study": study,
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "automatic_criteria": rows,
        "actions": actions,
        "standards_basis": list(STANDARDS_BASIS),
        "package_sha256": current_manifest["package_sha256"],
        "human_approval_valid": g9_approved,
        "release_rule": (
            "Chỉ PASS_G9_PUBLICATION_INTEGRITY_LOCKED khi mọi tiêu chí còn PASS "
            "và PI đã ký đúng G9_checkpoint.json."
        ),
        "assurance_limit": (
            "HMAC cục bộ và evidence_ref không chứng minh danh tính/chữ ký riêng của "
            "từng tác giả. PI phải đối chiếu form thật; bảo đảm mạnh hơn cần chữ ký số "
            "bất đối xứng hoặc hệ thống quản lý danh tính bên ngoài."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }

    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / REPORT_JSON).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8", newline="\n"
        )
        _write_markdown(out_dir / REPORT_MD, report)
        meta_for_write = GC.ensure_study_meta(out_dir)
        meta_for_write["g9_quality_status"] = status
        # Không sửa checkpoint sau chữ ký vì sẽ làm mất hiệu lực ledger.
        if checkpoint and not g9_approved:
            checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION
            checkpoint["publication_manifest"] = current_manifest
            checkpoint["quality_gate"] = {
                "status": status,
                "report": REPORT_JSON,
                "package_sha256": current_manifest["package_sha256"],
                "human_approval_valid": False,
            }
            checkpoint["submission_package_ready"] = status == STATUS_READY
            checkpoint_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2),
                encoding="utf-8", newline="\n"
            )
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Chấm hợp đồng chất lượng G9.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    study = re.sub(r"[^\w-]", "_", args.study.strip().replace(" ", "-"))
    report = evaluate_study(
        study,
        root / "exports" / study,
        repo_root=root,
        write=True,
    )
    print(f"G9 quality status: {report['status']}")
    print(f"Report: exports/{study}/{REPORT_JSON}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
