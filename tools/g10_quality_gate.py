#!/usr/bin/env python3
"""Hợp đồng chất lượng G10 cho gói nghiên cứu cuối và khóa phát hành.

G10 là cổng capstone nằm ngoài trục khoa học G0-G9. Nó không thay thế phê
duyệt đạo đức, khóa SAP, khóa dữ liệu, bình duyệt độc lập hoặc liêm chính tác
giả. G10 chỉ được xem là đạt khi:

1. mọi cổng tiền đề còn hợp lệ khi chấm trực tiếp;
2. đề cương/StudySpec/gói quyết định hoàn chỉnh và nhất quán;
3. hồ sơ phát hành, bảo mật, lưu trữ và trách nhiệm đã được xác nhận;
4. manifest SHA-256 khớp toàn bộ gói cuối; và
5. PI tự tay phê duyệt đúng ``G10_checkpoint.json`` chứa manifest đó.

Bốn trạng thái fail-closed:

- ``BLOCKED``: hồ sơ hỏng, có nguy cơ an toàn hoặc gói đã đổi sau khóa.
- ``DRAFT_ASSEMBLED_NEEDS_COMPLETION``: đã lắp nháp nhưng còn việc phải làm.
- ``READY_FOR_G10_PI_RELEASE_APPROVAL``: đủ tiêu chí, chờ PI duyệt gói cuối.
- ``PASS_G10_RELEASE_PACKAGE_LOCKED``: PI đã duyệt đúng checkpoint và mọi
  hash/tiền đề vẫn hợp lệ.

PASS G10 chỉ có nghĩa "gói được khóa để phát hành thủ công". Module này không
tự nộp hồ sơ và không chứng minh IRB, registry hay tạp chí đã tiếp nhận/chấp
nhận. Không lưu tên, email, điện thoại hoặc thông tin định danh trong readiness.
"""

from __future__ import annotations

import hashlib
import html
import json
import re

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import gate_contract as GC
import pipeline_freshness as PF
import placeholder_contract as PC

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_ASSEMBLED_NEEDS_COMPLETION"
STATUS_READY = "READY_FOR_G10_PI_RELEASE_APPROVAL"
STATUS_LOCKED = "PASS_G10_RELEASE_PACKAGE_LOCKED"
QUALITY_CONTRACT_VERSION = "G10-2026.1"

READINESS_JSON = "G10_RELEASE_READINESS.json"
REPORT_JSON = "G10_QUALITY_REPORT.json"
REPORT_MD = "G10_QUALITY_REPORT.md"
CHECKPOINT_JSON = "G10_checkpoint.json"

RELEASE_PURPOSES = {
    "ETHICS_SUBMISSION",
    "REGISTRY_UPDATE",
    "JOURNAL_SUBMISSION",
    "INSTITUTIONAL_ARCHIVE",
    "INTERNAL_HANDOFF",
    "RESEARCH_DOSSIER",
}

STANDARDS_BASIS = (
    {
        "standard": "ICMJE Recommendations, updated January 2026",
        "scope": (
            "Tác giả phê duyệt bản cuối, chịu trách nhiệm, khai báo và minh bạch "
            "trước công bố"
        ),
        "url": (
            "https://www.icmje.org/recommendations/browse/roles-and-responsibilities/"
            "defining-the-role-of-authors-and-contributors.html"
        ),
    },
    {
        "standard": "EQUATOR Network reporting guideline library",
        "scope": "Checklist đúng thiết kế và đủ thông tin để hiểu, tái lập và thẩm định",
        "url": "https://www.equator-network.org/reporting-guidelines/",
    },
    {
        "standard": "SPIRIT 2025",
        "scope": (
            "Với thử nghiệm: protocol, SAP, registry và tài liệu liên quan phải "
            "đầy đủ, nhất quán trước REC/IRB"
        ),
        "doi": "10.1136/bmj-2024-081477",
        "pmid": "42290521",
    },
    {
        "standard": "CONSORT 2025",
        "scope": (
            "Với thử nghiệm: báo cáo kết quả, registration, protocol/SAP, dữ liệu "
            "và công khai lợi ích"
        ),
        "doi": "10.1136/bmj-2024-081123",
        "pmid": "40228499",
    },
    {
        "standard": "ICH E6(R3) Good Clinical Practice",
        "scope": (
            "Quality by design, độ tin cậy kết quả, quản trị dữ liệu và hồ sơ "
            "thiết yếu của thử nghiệm"
        ),
        "url": (
            "https://database.ich.org/sites/default/files/"
            "ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf"
        ),
    },
    {
        "standard": "WHO Trial Registration Data Set v1.3.1",
        "scope": (
            "Với thử nghiệm: định danh, ethics, kết cục, kết quả, protocol và "
            "tuyên bố chia sẻ IPD"
        ),
        "url": (
            "https://www.who.int/tools/clinical-trials-registry-platform/network/"
            "who-data-set"
        ),
    },
    {
        "standard": "FAIR Guiding Principles",
        "scope": "Dữ liệu, metadata, thuật toán và workflow có provenance và khả năng tái sử dụng",
        "doi": "10.1038/sdata.2016.18",
        "pmid": "26978244",
    },
)

# Mẫu RIÊNG cũ của G10 — GIỮ NGUYÊN ngữ nghĩa (IGNORECASE, ngoặc vuông phải đóng, ngoặc nhọn chứa
# điền/fill/name/date: «<điền tên>», «<Name>», «<date>», «[CAN_BO_SUNG]», «[todo: x]»…). SỬA 03/10/2026 (lượt đo ô
# trống 11 cổng): CHỈ bỏ báo nhầm đã đo của nhánh «[CAN» không ranh giới từ — «[CAN» liền một CHỮ CÁI («[Cancer…]»,
# «[Canxi]») hoặc «[can thiệp…]» (mục checklist hợp lệ, vd «☐ [Can thiệp thuốc]» của G2). Văn bản phải chuẩn hoá NFC
# trước khi so (xem _placeholder_hits) để «thiệp» dựng sẵn/tổ hợp đều khớp.
_PLACEHOLDER_RE = re.compile(
    r"\[(?:CẦN|TBD|TODO|PENDING)[^\]]*\]|"
    r"\[CAN(?![^\W\d_])(?!\s+thi[eệ]p)[^\]]*\]|"
    r"<[^>\n]*(?:điền|fill|name|date)[^>\n]*>",
    re.IGNORECASE,
)
# THÊM 03/10/2026 — hợp đồng ô trống dùng chung (tools/placeholder_contract.py). Quét TÀI LIỆU (đề cương .md, gói quyết
# định, CHỮ HIỂN THỊ của .docx) bằng họ NHAN + MAU_CHUNG («[TO BE COMPLETED]», «[nơi thực hiện]», «thuốc/can thiệp X»,
# «<CẦN …>», «CHƯA XÁC NHẬN»…). CỐ Ý KHÔNG bật NHAP/TRONG/THU_CONG: khuôn G10 in VÔ ĐIỀU KIỆN «[DỰ THẢO]» (dòng «Trạng
# thái khóa tài liệu», _META_DRAFT_NOTE), câu chú giải «mọi ô để trống `___`» (§13) và nhãn hướng dẫn vĩnh viễn
# «[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]» — bật các họ đó là chặn MỌI đề tài mãi mãi (đúng lỗi tautology G10-02).
_HO_TAI_LIEU = PC.HO_MAC_DINH
# Câu mặc định khuôn G10 in khi StudySpec thiếu nguồn dữ liệu (run_g10_assemble «Dữ liệu hiện có») — ô trống văn xuôi.
_THEM_TAI_LIEU = ("Chưa có dữ liệu thật/nguồn chưa xác nhận",)
# «<» đứng trước một số là PHÉP SO SÁNH lâm sàng («nằm viện < 3 ngày hoặc tuổi > 80»), không phải ô mẫu ngoặc nhọn — che
# trước khi gọi họ NHAN (nhánh ngoặc nhọn của hợp đồng có từ «ngày/tên»). Mẫu cũ _PLACEHOLDER_RE vẫn chạy trên bản gốc.
_SO_SANH_TRUOC_SO_RE = re.compile(r"<(?=\s*[\d.,])")
# Dư lượng riêng của khuôn G10 (run_g10_assemble.py) không mang nhãn: số liệu thiếu in «?» (default="?" của n_sr/n_rct/
# α/power/n…, «| ? | ? |» tạp chí), mã thiết kế None in thành «`None`», băng-rôn «🚧 BẢN NHÁP — CHƯA SẴN SÀNG NỘP» do
# main() chèn đầu tài liệu (lắp lại mới xoá — chấm độc lập vẫn phải thấy).
_O_HOI_TRONG_RE = re.compile(r"(?<![\w?])\?(?![\w?])")
_NONE_IN_RA_RE = re.compile(r"`None`|Mã thiết kế nội bộ:\W*None\b")
_BANG_RON_NHAP_RE = re.compile(r"BẢN NHÁP\s+—")
# Bảng «Kiểm soát phiên bản»: ô GIÁ TRỊ của 4 dòng này phải là nội dung thật theo vị từ trường (MỌI họ) — khuôn in
# «[DỰ THẢO]» khi thiếu phiên bản và in NGUYÊN giá trị meta thô (không qua is_present). KHÔNG gồm «Trạng thái khóa tài
# liệu» (nhãn «[DỰ THẢO]» cố định có chủ ý tới khi G2/G4/G6/G9 có bằng chứng thật).
_DONG_KIEM_SOAT_RE = re.compile(
    r"^\|\s*(Phiên bản tài liệu|Ngày tạo/cập nhật|Người soạn/cập nhật|Người phê duyệt/chủ nhiệm)\s*\|([^|\n]*)\|",
    re.MULTILINE,
)
# Vị từ GIÁ TRỊ TRƯỜNG (_real_text): «TO BE COMPLETED» không ngoặc cũng là ô trống của một mã tham chiếu.
_THEM_TRUONG = ("TO BE COMPLETED",)
# Đường dẫn additional_artifacts: không bật TRONG (tên tệp thật có thể chứa «___»; tệp vắng đã bị bắt ở bước tồn tại).
_HO_DUONG_DAN = (PC.NHAN, PC.NHAP, PC.MAU_CHUNG, PC.THU_CONG)
# Phần chữ của .docx được quét (thân bài + đầu/chân trang + chú thích cuối trang).
_DOCX_PHAN_PHU_RE = re.compile(r"word/(?:header\d*|footer\d*|footnotes|endnotes)\.xml")
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


def _real_text(value: Any, *, ho: Optional[tuple[str, ...]] = None) -> bool:
    """Vị từ GIÁ TRỊ TRƯỜNG cho mã tham chiếu readiness (và đường dẫn additional_artifacts).

    SỬA 03/10/2026: luật cũ (mẫu riêng G10 + tập từ «none/null/unknown…») GIỮ NGUYÊN và AND thêm vị từ chung
    `placeholder_contract.co_noi_dung_that` — trước đây «___», «……», «[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]», «[DỰ THẢO]»,
    «[TO BE COMPLETED]», «[đơn vị]», «?», «-» đều được coi là mã thật nên G10-HUMAN-01/04 PASS (đã đo). `ho=None` ⇒
    MỌI họ dấu hiệu; đường dẫn truyền _HO_DUONG_DAN."""
    text = unicodedata.normalize("NFC", str(value or "")).strip()
    return bool(
        text
        and not _PLACEHOLDER_RE.search(text)
        and text.casefold()
        not in {
            "none",
            "null",
            "unknown",
            "undecided",
            "not decided",
            "chưa quyết định",
            "n/a",
        }
        and PC.co_noi_dung_that(text, ho=ho, them=_THEM_TRUONG)
    )


def _iso_datetime(value: Any) -> bool:
    text = str(value or "").strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return bool(text)


# Vá 2026-09-06 (audit vòng 33, phát hiện #5 — LOW/MEDIUM, lỗi tiềm ẩn): so
# khớp chuỗi con "PASS in status" không có ranh giới từ khiến một giá trị
# guardrail dạng text mang nghĩa THẤT BẠI nhưng tình cờ chứa chuỗi con "PASS"
# (vd "BYPASSED", "SURPASSED_THRESHOLD_ERROR") bị chấm PASS sai cho cổng
# phát hành cuối cùng (G10). Hiện chưa module nào trong repo ghi guardrail
# dạng text như vậy (mọi checkpoint thật đều dùng dict {"passed": bool}, xử
# lý ở nhánh "passed" in guardrail phía trên) nên đây là lỗi CHƯA bị kích
# hoạt bởi dữ liệu sản xuất — vá trước khi có gate/dữ liệu mới kích hoạt nó.
_PASS_WORD = re.compile(r"\bPASS\b")


def _guardrail_ok(checkpoint: Mapping[str, Any]) -> bool:
    guardrail = checkpoint.get("guardrail")
    if isinstance(guardrail, Mapping):
        if "passed" in guardrail:
            return guardrail.get("passed") is True
        status = str(guardrail.get("status") or "").upper()
    else:
        status = str(guardrail or "").upper()
    return bool(
        (_PASS_WORD.search(status) or "✅" in status or "[OK]" in status)
        and not any(token in status for token in ("FAIL", "BLOCK", "LỖI", "🔴"))
    )


def _status_locked(value: Any) -> bool:
    text = str(value or "").upper()
    if any(token in text for token in ("UNLOCK", "NOT LOCK", "CHƯA", "PENDING")):
        return False
    return bool(re.search(r"\bLOCKED\b", text))


def _safe_child(base: Path, value: Any) -> Optional[Path]:
    if not _real_text(value, ho=_HO_DUONG_DAN):
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


def build_readiness_template(study: str) -> Dict[str, Any]:
    """Tạo hồ sơ G10 fail-closed; không tự xác nhận thay PI."""
    return {
        "schema_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "status": STATUS_DRAFT,
        "release": {
            "purpose": None,
            "package_version": None,
            "target_system_or_recipient_ref": None,
            "target_requirements_checked": False,
            "prepared_at": None,
            "owner_ref": None,
            "change_log_reviewed": False,
            "final_files_confirmed": False,
            "no_unresolved_critical_issues": False,
            "prepared_for_pi_review": False,
        },
        "cross_document_consistency": {
            "protocol_sap_consistent": False,
            "registry_protocol_consistent_or_not_applicable": False,
            "manuscript_results_consistent": False,
            "ethics_consent_consistent": False,
            "reporting_checklist_complete": False,
            "analysis_deviations_disclosed_or_none": False,
            "data_code_statements_consistent": False,
        },
        "privacy_and_permissions": {
            "no_direct_identifiers_confirmed": False,
            "residual_reidentification_risk_reviewed": False,
            "access_controls_confirmed": False,
            "external_release_permissions_confirmed": False,
        },
        "archive_and_reproducibility": {
            "archive_location_ref": None,
            "retention_policy_ref": None,
            "software_environment_captured": False,
            "data_dictionary_included_or_not_applicable": False,
            "audit_trail_preserved": False,
            "responsible_owner_ref": None,
        },
        "additional_artifacts": [],
        "automation_limits": {
            "external_submission_performed_by_g10": False,
            "receipt_or_acceptance_claimed_by_g10": False,
        },
        "pi_release_approval": {
            "required": True,
            "artifact": CHECKPOINT_JSON,
            "completed_by_system": False,
        },
        "pii_policy": "Chỉ dùng mã tham chiếu; không ghi tên đầy đủ hoặc thông tin liên hệ.",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


def ensure_readiness(study: str, out_dir: Path) -> Path:
    """Tạo readiness một lần; không ghi đè xác nhận đời thực đã có."""
    path = Path(out_dir) / READINESS_JSON
    if not path.exists():
        path.write_text(
            json.dumps(build_readiness_template(study), ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    return path


def _release_readiness_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    release = payload.get("release")
    release = release if isinstance(release, Mapping) else {}
    purpose = str(release.get("purpose") or "").strip().upper()
    checks = (
        purpose in RELEASE_PURPOSES,
        _real_text(release.get("package_version")),
        _real_text(release.get("target_system_or_recipient_ref")),
        release.get("target_requirements_checked") is True,
        _iso_datetime(release.get("prepared_at")),
        _real_text(release.get("owner_ref")),
        release.get("change_log_reviewed") is True,
        release.get("final_files_confirmed") is True,
        release.get("no_unresolved_critical_issues") is True,
        release.get("prepared_for_pi_review") is True,
    )
    return all(checks), f"purpose={purpose or None}; completed={sum(checks)}/{len(checks)}"


def _all_true_section(
    payload: Mapping[str, Any],
    section: str,
    keys: tuple[str, ...],
) -> tuple[bool, str]:
    value = payload.get(section)
    value = value if isinstance(value, Mapping) else {}
    missing = [key for key in keys if value.get(key) is not True]
    return not missing, "missing=" + (",".join(missing) if missing else "none")


def _archive_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("archive_and_reproducibility")
    value = value if isinstance(value, Mapping) else {}
    boolean_keys = (
        "software_environment_captured",
        "data_dictionary_included_or_not_applicable",
        "audit_trail_preserved",
    )
    missing = [key for key in boolean_keys if value.get(key) is not True]
    text_missing = [
        key
        for key in ("archive_location_ref", "retention_policy_ref", "responsible_owner_ref")
        if not _real_text(value.get(key))
    ]
    return (
        not missing and not text_missing,
        f"missing_flags={missing}; missing_refs={text_missing}",
    )


def _automation_limits_ok(payload: Mapping[str, Any]) -> tuple[bool, str]:
    value = payload.get("automation_limits")
    value = value if isinstance(value, Mapping) else {}
    submit = value.get("external_submission_performed_by_g10")
    acceptance = value.get("receipt_or_acceptance_claimed_by_g10")
    ok = submit is False and acceptance is False
    return ok, f"submission_claim={submit}; receipt_or_acceptance_claim={acceptance}"


def _package_files(
    study: str,
    out_dir: Path,
    readiness: Mapping[str, Any],
) -> tuple[Dict[str, Optional[Path]], list[str]]:
    files: Dict[str, Optional[Path]] = {
        "final_protocol_md": out_dir / f"DE_CUONG_THONG_NHAT_{study}.md",
        "final_protocol_docx": out_dir / f"DE_CUONG_THONG_NHAT_{study}.docx",
        "study_spec": out_dir / f"STUDY_SPEC_{study}.json",
        "decision_package": out_dir / f"GOI_QUYET_DINH_{study}.md",
        "release_readiness": out_dir / READINESS_JSON,
        "g8_peer_review": out_dir / f"G8_A9_PRESUBMISSION_{study}.md",
        "g9_checkpoint": out_dir / "G9_checkpoint.json",
        "g9_publication_readiness": out_dir / "G9_PUBLICATION_READINESS.json",
        "citation_verification": out_dir / f"A12_CITATION_VERIFICATION_{study}.md",
        "citation_retraction_receipt": out_dir / "A12_RETRACTION_RECEIPT.json",
        "citation_metadata_receipt": out_dir / "A12_METADATA_RECEIPT.json",
    }
    for index in range(10):
        files[f"checkpoint_g{index}"] = out_dir / f"G{index}_checkpoint.json"

    invalid: list[str] = []
    additional = readiness.get("additional_artifacts")
    if additional is not None and not isinstance(additional, list):
        invalid.append("additional_artifacts:not_list")
    elif isinstance(additional, list):
        for index, value in enumerate(additional, start=1):
            path = _safe_child(out_dir, value)
            if path is None:
                invalid.append(f"additional_artifact_{index}:unsafe_or_placeholder")
            files[f"additional_artifact_{index:02d}"] = path
    return files, invalid


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


def _so_dong(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _placeholder_hits(text: Any) -> list[str]:
    """Các ô còn trống trong VĂN BẢN HIỂN THỊ (đề cương .md, gói quyết định, chữ của .docx) — «L<dòng>:<dấu hiệu>».

    THÊM 03/10/2026. Hợp của: (1) mẫu riêng cũ _PLACEHOLDER_RE (không yếu hơn danh sách cũ của G10); (2) họ NHAN +
    MAU_CHUNG của hợp đồng chung + câu mặc định thiếu nguồn dữ liệu; (3) dư lượng riêng của khuôn G10: «?» đứng một
    mình thay số liệu, «`None`», băng-rôn bản nháp, ô giá trị trống của bảng kiểm soát phiên bản. Bằng chứng chỉ mang
    số dòng + dấu hiệu mẫu (không chép cả dòng — tránh kéo tên người vào báo cáo)."""
    vb = unicodedata.normalize("NFC", str(text or ""))
    hits: list[tuple[int, str]] = []
    for m in _PLACEHOLDER_RE.finditer(vb):
        hits.append((_so_dong(vb, m.start()), m.group(0)))
    da_che = _SO_SANH_TRUOC_SO_RE.sub("‹", vb)  # thay 1 ký tự lấy 1 ký tự ⇒ số dòng giữ nguyên
    for p in PC.tim(da_che, _HO_TAI_LIEU, _THEM_TAI_LIEU):
        hits.append((p.dong_so, p.khop))
    for m in _O_HOI_TRONG_RE.finditer(vb):
        sau = vb[m.end():].split("\n", 1)[0].strip()
        if not sau:
            continue  # «?» cuối dòng = câu hỏi văn xuôi («… là bao nhiêu ?»)
        if len(sau) > 1 and sau[0].isupper() and sau[1].islower():
            continue  # «… bao nhiêu ? Yếu tố nào …» = sang câu mới, không phải ô số liệu
        hits.append((_so_dong(vb, m.start()), "? " + sau[:12].rstrip()))
    for rx in (_NONE_IN_RA_RE, _BANG_RON_NHAP_RE):
        for m in rx.finditer(vb):
            hits.append((_so_dong(vb, m.start()), m.group(0)))
    for m in _DONG_KIEM_SOAT_RE.finditer(vb):
        if not PC.co_noi_dung_that(m.group(2)):
            hits.append((_so_dong(vb, m.start()), f"{m.group(1)}: ô giá trị trống"))
    ra: list[str] = []
    for dong, dau in sorted(hits):
        muc = f"L{dong}:{dau[:60]}"
        if muc not in ra:
            ra.append(muc)
    return ra


def _xml_sang_chu(xml: str) -> str:
    """Chữ của một phần XML trong .docx: bỏ THẺ (kể cả «<w:shd w:fill=…/>»), mỗi đoạn «</w:p>» một dòng, giải mã thực
    thể (&lt;điền tên&gt; ⇒ «<điền tên>»). Giữ mọi nút chữ như bản XML thô cũ đã thấy (w:t, w:delText, w:instrText)."""
    x = re.sub(r"<w:tab\b[^>]*/>", "\t", xml)
    x = re.sub(r"<w:(?:br|cr)\b[^>]*/>", "\n", x)
    x = x.replace("</w:p>", "\n")
    return html.unescape(re.sub(r"<[^>]*>", "", x))


def _docx_visible_text(archive: zipfile.ZipFile, document_xml: str) -> str:
    """VĂN BẢN HIỂN THỊ của .docx để dò ô trống — THÊM 03/10/2026 thay cho quét XML THÔ.

    Quét XML thô từng báo nhầm VĨNH VIỄN: nhánh «<…fill…>» khớp thẻ «<w:shd w:fill="D9EAF7"/>» md2docx_vn chèn cho
    hàng tiêu đề MỌI bảng (76–90 lần/tài liệu ⇒ G10-AUTO-09 không bao giờ PASS qua assembler thật), còn chữ thật
    «<điền tên>» (đã escape thành &lt;) lại không bao giờ khớp; nhãn bị tách giữa hai run cũng lọt. Ở đây: chữ theo
    đoạn + mỗi hàng bảng thêm một dòng dạng «| ô | ô |» (để luật theo hàng như bảng kiểm soát phiên bản chạy được
    trên .docx), cộng phần đầu/chân trang/chú thích."""
    phan = [_xml_sang_chu(document_xml)]
    xmls = [document_xml]
    for name in sorted(n for n in archive.namelist() if _DOCX_PHAN_PHU_RE.fullmatch(n)):
        xml = archive.read(name).decode("utf-8", errors="replace")
        xmls.append(xml)
        phan.append(_xml_sang_chu(xml))
    for xml in xmls:
        for tr in re.finditer(r"<w:tr\b[^>]*>(.*?)</w:tr>", xml, re.S):
            cells = [
                " ".join(_xml_sang_chu(tc.group(1)).split())
                for tc in re.finditer(r"<w:tc\b[^>]*>(.*?)</w:tc>", tr.group(1), re.S)
            ]
            phan.append("| " + " | ".join(cells) + " |")
    return "\n".join(phan)


def _documents_clean(
    files: Mapping[str, Optional[Path]],
) -> tuple[bool, str, bool]:
    missing = [
        key
        for key, path in files.items()
        if path is None or not path.is_file() or _sha256(path) is None
    ]
    if missing:
        return False, "missing_or_unreadable=" + ",".join(missing), False

    placeholder_hits: list[str] = []
    placeholder_lines: list[str] = []
    trace_hits: list[str] = []
    contact_pii_hits: list[str] = []
    for key in ("final_protocol_md", "decision_package"):
        path = files[key]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False, f"unreadable_text={key}", True
        found = _placeholder_hits(text)
        if found:
            placeholder_hits.append(key)
            placeholder_lines.extend(f"{key}:{item}" for item in found[:3])
        if _INTERNAL_TRACE_RE.search(text):
            trace_hits.append(key)
        if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
            contact_pii_hits.append(key)
    docx_path = files["final_protocol_docx"]
    try:
        with zipfile.ZipFile(docx_path) as archive:
            docx_text = archive.read("word/document.xml").decode(
                "utf-8", errors="strict"
            )
            # SỬA 03/10/2026: dò ô trống trên CHỮ HIỂN THỊ (không trên thẻ XML); dấu vết nội bộ/PII vẫn quét
            # XML thô như cũ (không nới).
            docx_visible = _docx_visible_text(archive, docx_text)
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile):
        return False, "invalid_docx_container=true", True
    found = _placeholder_hits(docx_visible)
    if found:
        placeholder_hits.append("final_protocol_docx")
        placeholder_lines.extend(f"final_protocol_docx:{item}" for item in found[:3])
    if _INTERNAL_TRACE_RE.search(docx_text):
        trace_hits.append("final_protocol_docx")
    if _EMAIL_RE.search(docx_text) or _PHONE_RE.search(docx_text):
        contact_pii_hits.append("final_protocol_docx")
    clean = not placeholder_hits and not trace_hits and not contact_pii_hits
    return (
        clean,
        (
            f"placeholders={placeholder_hits}; internal_traces={trace_hits}; "
            f"contact_pii={contact_pii_hits}; placeholder_lines={placeholder_lines}"
        ),
        bool(trace_hits or contact_pii_hits),
    )


def _readiness_has_contact_pii(readiness_path: Path) -> bool:
    try:
        text = readiness_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True
    return bool(_EMAIL_RE.search(text) or _PHONE_RE.search(text))


def _write_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# BÁO CÁO CHẤT LƯỢNG G10",
        "",
        f"**Đề tài:** {report.get('study')}",
        f"**Hợp đồng:** {report.get('quality_contract_version')}",
        f"**Trạng thái:** `{report.get('status')}`",
        f"**Trạng thái nộp bên ngoài:** `{report.get('external_submission_state')}`",
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
    """Chấm G10 từ artifact hiện hành; không tin report hoặc cờ tự khai."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / CHECKPOINT_JSON
    readiness_path = out_dir / READINESS_JSON
    checkpoint = _read_json(checkpoint_path)
    readiness = _read_json(readiness_path)
    rows: list[Dict[str, str]] = []

    structure_ok = bool(
        checkpoint.get("gate") == "G10"
        and checkpoint.get("study") == study
        and checkpoint.get("quality_contract_version") == QUALITY_CONTRACT_VERSION
        and readiness.get("schema_version") == QUALITY_CONTRACT_VERSION
        and readiness.get("study") == study
        and readiness.get("disclaimer") == "Cần bác sĩ kiểm chứng."
    )
    rows.append(
        _criterion(
            "G10-AUTO-01",
            "Checkpoint và release-readiness đúng schema G10-2026.1",
            "PASS" if structure_ok else "BLOCK",
            (
                f"checkpoint={bool(checkpoint)}; readiness={bool(readiness)}; "
                f"schema={readiness.get('schema_version')}"
            ),
            "Chạy lại run_g10_assemble.py; không ký file tự tạo hoặc schema cũ.",
        )
    )

    checkpoints = {
        f"G{index}": _read_json(out_dir / f"G{index}_checkpoint.json")
        for index in range(10)
    }
    missing_checkpoints = [gate for gate, value in checkpoints.items() if not value]
    bad_guardrails = [
        gate for gate, value in checkpoints.items() if value and not _guardrail_ok(value)
    ]
    chain_ok = not missing_checkpoints and not bad_guardrails and _guardrail_ok(checkpoint)
    rows.append(
        _criterion(
            "G10-AUTO-02",
            "Đủ G0-G9 và mọi guardrail kỹ thuật còn đạt",
            "PASS" if chain_ok else "BLOCK",
            (
                f"missing={missing_checkpoints}; bad_guardrails={bad_guardrails}; "
                f"g10_guardrail={_guardrail_ok(checkpoint)}"
            ),
            "Sửa hoặc chạy lại cổng thiếu/lỗi trước khi lắp gói cuối.",
        )
    )

    expected_quality_status = {
        "G0": "PASS_G0_CONFIRMED",
        "G1": "PASS_G1_CONFIRMED",
        "G3": "PASS_G3_CONFIRMED",
        "G8": "PASS_G8_REVIEW_RECORDED",
    }
    legacy_quality = []
    bad_quality = []
    for gate, expected in expected_quality_status.items():
        gate_checkpoint = checkpoints.get(gate) or {}
        quality = gate_checkpoint.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, Mapping) else None
        if not gate_checkpoint.get("quality_contract_version"):
            legacy_quality.append(gate)
        elif quality_status != expected:
            bad_quality.append(f"{gate}:{quality_status or 'missing'}")
    modern_quality_ok = not legacy_quality and not bad_quality
    rows.append(
        _criterion(
            "G10-AUTO-02B",
            "Các hợp đồng chất lượng G0/G1/G3/G8 đều ở trạng thái xác nhận cuối",
            "PASS" if modern_quality_ok else "REVIEW",
            f"legacy={legacy_quality}; not_confirmed={bad_quality}",
            (
                "Nâng checkpoint lịch sử lên hợp đồng chất lượng hiện hành và hoàn tất "
                "xác nhận con người đúng vai trò trước G10."
            ),
        )
    )

    try:
        import pipeline_freshness as freshness  # noqa: PLC0415

        fresh_report = freshness.stale_report(out_dir)
        freshness_ok = bool(fresh_report.get("fresh"))
        freshness_evidence = (
            f"fresh={freshness_ok}; issues={fresh_report.get('issues', [])}"
        )
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        freshness_ok = False
        freshness_evidence = str(exc)
    rows.append(
        _criterion(
            "G10-AUTO-03",
            "Chuỗi checkpoint tươi, không có downstream cũ hoặc mồ côi",
            "PASS" if freshness_ok else "BLOCK",
            freshness_evidence,
            "Chạy pipeline_freshness.py và chạy lại mọi cổng stale trước G10.",
        )
    )

    g2 = checkpoints.get("G2") or {}
    g8_artifact = out_dir / f"G8_A9_PRESUBMISSION_{study}.md"
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL): g2_ok/g4_ok trước
    # đây AND thêm `_status_locked(g*.get("g*_status"))` — một kiểm text tìm chuỗi
    # "LOCKED" trong g2_status/g4_status. Nhưng run_g2_auto.py/run_g4_auto.py CHỈ BAO
    # GIỜ ghi "PENDING"/"BLOCKED — ..." vào các trường này; KHÔNG đoạn code nào trong
    # repo từng ghi "LOCKED" vào đó (approve_gate.py --gate G2/G4 chỉ cập nhật
    # approval_ledger.json + quality_gate report, không đụng g2_status/g4_status thô).
    # Hệ quả: g2_ok luôn False, còn g4_ok (chưa từng có g4_quality_contract_satisfied
    # để bù) LUÔN False vĩnh viễn cho MỌI đề tài thật — G10-AUTO-04 không bao giờ PASS
    # được dù cả 5 cổng thượng nguồn đã ký hợp lệ. g5_ok/g9_ok bên dưới KHÔNG mắc lỗi
    # này vì đã dùng đúng hàm chấm trực tiếp (g5_quality_contract_satisfied/g9_...).
    # Vá: bỏ _status_locked() (tín hiệu không tồn tại), g2_ok giữ ledger_approved +
    # g2_quality_contract_satisfied (đã có, chỉ bỏ điều kiện chết); g4_ok đổi sang
    # cùng khuôn g5_ok/g9_ok — gọi thẳng g4_quality_contract_satisfied() (mới xây,
    # tự bao gồm cả ledger_approved qua tiêu chí G4-HUMAN-01 bên trong).
    g2_ok = bool(
        GC.ledger_approved(
            "G2",
            study,
            out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md",
            repo_root=root,
        )
        and GC.g2_quality_contract_satisfied(
            g2, GC.load_study_meta(out_dir), study=study, out_dir=out_dir)
    )
    g4_ok = GC.g4_quality_contract_satisfied(study, repo_root=root)
    g5_ok = GC.g5_quality_contract_satisfied(study, repo_root=root)
    g8_ok = GC.ledger_approved("G8", study, g8_artifact, repo_root=root)
    g9_ok = GC.g9_quality_contract_satisfied(study, repo_root=root)
    upstream_ok = all((g2_ok, g4_ok, g5_ok, g8_ok, g9_ok))
    rows.append(
        _criterion(
            "G10-AUTO-04",
            "G2, G4, G5, G8 và G9 còn khóa hợp lệ khi chấm trực tiếp",
            "PASS" if upstream_ok else "REVIEW",
            f"G2={g2_ok}; G4={g4_ok}; G5={g5_ok}; G8={g8_ok}; G9={g9_ok}",
            "Khôi phục đúng cổng tiền đề; G10 không được hợp thức hóa khóa đã mất hiệu lực.",
        )
    )

    try:
        import run_g10_assemble as G10  # noqa: PLC0415

        citation_ok, citation_reason = G10.citation_verification_ok(study, out_dir)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        citation_ok, citation_reason = False, str(exc)
    rows.append(
        _criterion(
            "G10-AUTO-05",
            "A12 phủ toàn bộ trích dẫn của chính gói G10 cuối",
            "PASS" if citation_ok else "REVIEW",
            citation_reason or "A12 current receipts valid",
            "Chạy lại check_citations.py trên toàn bộ PMID/DOI của gói cuối.",
        )
    )

    spec = checkpoint.get("study_spec")
    spec = spec if isinstance(spec, Mapping) else {}
    spec_ok = bool(
        spec.get("scientific_content_complete") is True
        and spec.get("protocol_content_complete") is True
        and not spec.get("missing_requirement_ids")
        and not spec.get("semantic_error_codes")
    )
    rows.append(
        _criterion(
            "G10-AUTO-06",
            "StudySpec hoàn chỉnh về nội dung và không có mâu thuẫn ngữ nghĩa",
            "PASS" if spec_ok else "REVIEW",
            (
                f"scientific={spec.get('scientific_content_complete')}; "
                f"protocol={spec.get('protocol_content_complete')}; "
                f"missing={spec.get('missing_requirement_ids')}; "
                f"semantic={spec.get('semantic_error_codes')}"
            ),
            "Điền dữ kiện thật và xử lý mọi lỗi StudySpec; không dùng placeholder để phát hành.",
        )
    )

    # G10-AUTO-11 (04/10/2026 — điều phối thống nhất G0–G10): thông số then chốt phải mang CÙNG giá trị ở mọi cổng giữ
    # bản sao của nó (tools/nhat_quan_xuyen_cong.py). Lệch cứng (N · α · power · thiết kế · loại nghiên cứu đăng ký) ⇒
    # BLOCK; lệch mềm (kết cục chính khác nhau giữa các cổng — outcome switching) ⇒ REVIEW chờ chủ nhiệm giải trình. Bộ
    # đối chiếu hỏng ⇒ REVIEW (không đo được ≠ khớp).
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

        nq_status, nq_evidence = NQ.tieu_chi_g10(NQ.doi_chieu(out_dir, study))
    except Exception as exc:  # noqa: BLE001 — bộ đối chiếu hỏng phải hiện ra, không im lặng như «khớp»
        nq_status, nq_evidence = "REVIEW", f"không chạy được bộ đối chiếu xuyên cổng: {type(exc).__name__}: {exc}"
    rows.append(
        _criterion(
            "G10-AUTO-11",
            "Thông số then chốt nhất quán xuyên cổng (N · α · power · thiết kế · kết cục chính)",
            nq_status,
            nq_evidence,
            "Chạy python3 tools/nhat_quan_xuyen_cong.py --study <mã>; sửa về MỘT giá trị tại cổng gốc rồi chạy lại "
            "các cổng sau; đổi kết cục chính phải có chủ nhiệm giải trình công khai.",
        )
    )

    release_ok, release_evidence = _release_readiness_ok(readiness)
    rows.append(
        _criterion(
            "G10-HUMAN-01",
            "Mục đích, đích nhận, phiên bản và owner của gói cuối đã chốt",
            "PASS" if release_ok else "REVIEW",
            release_evidence,
            "PI/nhóm nghiên cứu hoàn tất khối release bằng mã tham chiếu không định danh.",
        )
    )

    consistency_ok, consistency_evidence = _all_true_section(
        readiness,
        "cross_document_consistency",
        (
            "protocol_sap_consistent",
            "registry_protocol_consistent_or_not_applicable",
            "manuscript_results_consistent",
            "ethics_consent_consistent",
            "reporting_checklist_complete",
            "analysis_deviations_disclosed_or_none",
            "data_code_statements_consistent",
        ),
    )
    rows.append(
        _criterion(
            "G10-HUMAN-02",
            "Protocol, SAP, registry, results, ethics và checklist nhất quán",
            "PASS" if consistency_ok else "REVIEW",
            consistency_evidence,
            "Đối chiếu từng tài liệu; nêu rõ sai lệch hợp lệ thay vì sửa ngầm.",
        )
    )

    privacy_ok, privacy_evidence = _all_true_section(
        readiness,
        "privacy_and_permissions",
        (
            "no_direct_identifiers_confirmed",
            "residual_reidentification_risk_reviewed",
            "access_controls_confirmed",
            "external_release_permissions_confirmed",
        ),
    )
    rows.append(
        _criterion(
            "G10-HUMAN-03",
            "Bảo mật, nguy cơ tái định danh, quyền truy cập và quyền phát hành đã rà",
            "PASS" if privacy_ok else "REVIEW",
            privacy_evidence,
            "Người có trách nhiệm rà dữ liệu/hình/phụ lục và quyền phát hành thật.",
        )
    )

    archive_ok, archive_evidence = _archive_ok(readiness)
    rows.append(
        _criterion(
            "G10-HUMAN-04",
            "Lưu trữ, retention, môi trường phần mềm, data dictionary và audit trail đủ",
            "PASS" if archive_ok else "REVIEW",
            archive_evidence,
            "Chốt nơi lưu, retention, owner và bằng chứng tái lập trước khi khóa gói.",
        )
    )

    limits_ok, limits_evidence = _automation_limits_ok(readiness)
    rows.append(
        _criterion(
            "G10-AUTO-07",
            "Không tự tuyên bố đã nộp, có receipt hoặc được chấp nhận",
            "PASS" if limits_ok else "BLOCK",
            limits_evidence,
            "Xóa tuyên bố không có bằng chứng; việc nộp bên ngoài luôn là hành động riêng.",
        )
    )

    contact_pii = _readiness_has_contact_pii(readiness_path)
    rows.append(
        _criterion(
            "G10-AUTO-08",
            "Release-readiness chỉ dùng mã tham chiếu, không lưu email/điện thoại",
            "BLOCK" if contact_pii else "PASS",
            f"contact_pii_detected={contact_pii}",
            "Xóa PII khỏi JSON; lưu danh tính/chữ ký ở hệ thống được kiểm soát.",
        )
    )

    files, invalid_paths = _package_files(study, out_dir, readiness)
    docs_ok, docs_evidence, internal_trace = _documents_clean(files)
    document_status = (
        "BLOCK"
        if invalid_paths or internal_trace
        else ("PASS" if docs_ok else "REVIEW")
    )
    rows.append(
        _criterion(
            "G10-AUTO-09",
            "Gói cuối đủ file, đường dẫn an toàn, không placeholder/dấu vết nội bộ",
            document_status,
            f"{docs_evidence}; invalid_paths={invalid_paths}",
            "Hoàn thiện hoặc loại file lỗi; không đưa đường dẫn ngoài thư mục đề tài vào gói.",
        )
    )

    current_manifest = _manifest(out_dir, files)
    saved_manifest = checkpoint.get("release_manifest")
    g10_approved = bool(
        checkpoint_path.exists()
        and GC.ledger_approved("G10", study, checkpoint_path, repo_root=root)
    )
    manifest_ok = _manifest_matches(saved_manifest, current_manifest)
    manifest_status = (
        "PASS"
        if manifest_ok or (write and not g10_approved)
        else ("BLOCK" if g10_approved else "REVIEW")
    )
    rows.append(
        _criterion(
            "G10-AUTO-10",
            "Manifest SHA-256 ràng buộc toàn bộ gói và còn nguyên sau khóa",
            manifest_status,
            (
                f"manifest_match={manifest_ok}; g10_approved={g10_approved}; "
                f"package_sha256={current_manifest['package_sha256']}"
            ),
            (
                "Trước ký: chạy lại g10_quality_gate.py để cập nhật manifest. "
                "Sau ký: điều tra thay đổi và ghi quyết định G10 mới có chủ ý."
            ),
        )
    )

    rows.append(
        _criterion(
            "G10-HUMAN-05",
            "PI phê duyệt đúng G10_checkpoint.json chứa manifest cuối",
            "PASS" if g10_approved else "REVIEW",
            f"approval_ledger_G10={g10_approved}",
            (
                "PI tự tay chạy approve_gate.py --gate G10 sau khi rà đúng gói; "
                "agent không tự phê duyệt."
            ),
        )
    )

    any_block = any(row["status"] == "BLOCK" for row in rows)
    non_pi_pending = any(
        row["status"] != "PASS" and row["id"] != "G10-HUMAN-05" for row in rows
    )
    # Một gói đã có chữ ký PI mà bất kỳ tiền đề/nội dung nào không còn PASS là
    # sự cố khóa, không phải "draft" thông thường. Buộc BLOCKED để điều tra.
    if any_block or (g10_approved and non_pi_pending):
        status = STATUS_BLOCKED
    elif non_pi_pending:
        status = STATUS_DRAFT
    elif not g10_approved:
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
        "kind": "g10_quality_report",
        "study": study,
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "automatic_criteria": rows,
        "actions": actions,
        "standards_basis": list(STANDARDS_BASIS),
        "package_sha256": current_manifest["package_sha256"],
        "human_approval_valid": g10_approved,
        "external_submission_state": "NOT_PERFORMED_OR_PROVEN_BY_G10",
        "release_rule": (
            "Chỉ PASS_G10_RELEASE_PACKAGE_LOCKED khi mọi tiêu chí còn PASS và "
            "PI đã ký đúng G10_checkpoint.json chứa manifest."
        ),
        "assurance_limit": (
            "G10 chứng minh tính nhất quán và toàn vẹn cục bộ của gói tại thời điểm "
            "khóa. HMAC cục bộ không tự chứng minh danh tính pháp lý, việc nộp, receipt, "
            "phê duyệt IRB/registry/tạp chí hoặc sự chấp nhận bên ngoài."
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
        meta = GC.ensure_study_meta(out_dir)
        meta["g10_quality_status"] = status
        if checkpoint and not g10_approved:
            checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION
            checkpoint["release_manifest"] = current_manifest
            checkpoint["quality_gate"] = {
                "status": status,
                "report": REPORT_JSON,
                "package_sha256": current_manifest["package_sha256"],
                "human_approval_valid": False,
                "external_submission_state": "NOT_PERFORMED_OR_PROVEN_BY_G10",
            }
            checkpoint["release_package_ready"] = status == STATUS_READY
            checkpoint["release_package_locked"] = False
            PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Chấm hợp đồng chất lượng G10.")
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
    print(f"G10 quality status: {report['status']}")
    print(f"Report: exports/{study}/{REPORT_JSON}")
    print("External submission: NOT_PERFORMED_OR_PROVEN_BY_G10")
    print("Cần bác sĩ kiểm chứng.")
    if report["status"] == STATUS_LOCKED:
        return GC.EXIT_OK
    if report["status"] == STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    return GC.EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
