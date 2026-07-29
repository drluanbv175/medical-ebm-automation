#!/usr/bin/env python3
"""Hợp đồng chất lượng G8: bình duyệt độc lập trước khi nộp bài.

Vì sao module này tồn tại
─────────────────────────
G8 đã là một cổng KÝ thật (``_GATE_REQUIRED_STAKEHOLDERS["G8"] =
("INDEPENDENT_PEER_REVIEWER",)``) và lớp mật mã quanh nó khá dày: chữ ký
HMAC-SHA256 payload v4 có buộc NHÓM VAI TRÒ, chuỗi băm ``prev_hash`` chống
xóa/đảo/chèn, con dấu ``approval_ledger.seal.json`` chống cắt đuôi, và
``run_g10_assemble.py`` fail-closed khi thiếu chữ ký.

Nhưng có một khoảng trống NỘI DUNG mà lớp mật mã không thể lấp được:

**Artifact mà chữ ký G8 ràng buộc vào — ``G8_A9_PRESUBMISSION_<study>.md`` — là
bản TỰ KIỂM do chính ``run_g8_auto.py`` sinh ra từ checkpoint G0–G7, KHÔNG phải
bản nhận xét của người bình duyệt.** Nó có 7 phần (kiểm toán pipeline, checklist
chuẩn báo cáo, toàn vẹn thống kê, gợi ý tạp chí, gói khai báo tác giả, tự chấm
30 điểm, tiêu chí qua cổng) và không phần nào chứa phát hiện/khuyến nghị của một
người phản biện. Vì vậy một chữ ký G8 hợp lệ chỉ chứng minh:

    "một người truy cập được khóa ký đã xác nhận bản TỰ KIỂM này, với nội dung
     đúng bằng hash tại thời điểm ký, và tự khai vai trò là phản biện độc lập"

Nó KHÔNG chứng minh rằng một cuộc bình duyệt độc lập đã thực sự diễn ra, và cũng
không chứng minh người ký khác chủ nhiệm đề tài — vì HMAC là mật mã ĐỐI XỨNG nên
máy xác minh buộc phải giữ đúng khóa đã ký; trên một máy đơn, cấu hình khả thi
duy nhất lại chính là cấu hình mà một người giữ đủ mọi khóa.

Module này KHÔNG cố sửa giới hạn mật mã đó (việc đó cần chuyển sang chữ ký bất
đối xứng — thuộc thẩm quyền bác sĩ). Nó làm ba việc trong tầm với:

1. **Nói đúng mức bảo đảm.** Không bao giờ phát ngôn "đã có bình duyệt độc lập"
   vô điều kiện; luôn kèm phạm vi khóa (``role`` / ``shared`` / không xác định).
2. **Đòi bằng chứng NỘI DUNG của việc bình duyệt** — một bản nhận xét riêng có
   khuyến nghị, lỗi nghiêm trọng kèm vị trí, và khai báo độc lập/COI của người
   phản biện (doctrine ``binh-duyet.md`` đã quy định mẫu này; code chưa làm).
3. **Kiểm những thứ máy kiểm được mà hiện không ai kiểm**: đổi kết cục chính so
   với SAP (selective outcome reporting), vệt công cụ nội bộ còn sót trong bản
   thảo, và các nghĩa vụ ICMJE bản 1/2026 ở thời điểm tiền nộp bài.

Giới hạn đã biết (ghi rõ để không ai đọc nhầm)
─────────────────────────────────────────────
- ``PASS_G8_REVIEW_RECORDED`` CỐ Ý không mang chữ "ĐỘC LẬP": hệ không biết điều
  đó có thật hay không.
- Module này KHÔNG phải cổng chặn. Chốt fail-closed duy nhất của G8 vẫn là
  ``run_g10_assemble.py`` gọi ``GC.ledger_approved("G8", ...)``.
- KHÔNG được đổi tên ``G8_A9_PRESUBMISSION_<study>.md``: tên này là hợp đồng ba
  bên (run_g8_auto ghi · run_g10_assemble tra ledger · doctrine dạy bác sĩ gõ
  tay vào approve_gate --artifact) và nội dung nó bị băm trong chữ ký. Tên "A9"
  lệch crosswalk (A9 thật = DMP ở G5, bình duyệt = A15) nhưng đó là lệch ĐÃ BIẾT
  và sửa tên sẽ phá cổng G10 lẫn mọi chữ ký cũ.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import gate_contract as GC

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_NEEDS_HUMAN_COMPLETION"
STATUS_READY = "READY_FOR_INDEPENDENT_REVIEW"
STATUS_PENDING = "PENDING_REAL_REVIEW_SIGNATURE"
STATUS_REVIEWED = "PASS_G8_REVIEW_RECORDED"

QUALITY_CONTRACT_VERSION = "G8-2026.1"

REVIEWER_ROLE_GROUP = "INDEPENDENT_PEER_REVIEWER"

# Tên artifact — HỢP ĐỒNG downstream, không được đổi (xem docstring module).
def presubmission_artifact_name(study: str) -> str:
    return f"G8_A9_PRESUBMISSION_{study}.md"


def manuscript_artifact_name(study: str) -> str:
    return f"G7_A8_MANUSCRIPT_{study}.md"


# Artifact MỚI mà hợp đồng này đòi: bản nhận xét THẬT của người bình duyệt.
# run_g8_auto.py không sinh file này (và không nên sinh — máy không được tự viết
# nhận xét phản biện rồi tự ký). Thiếu nó là REVIEW, không phải BLOCK.
def peer_review_report_name(study: str) -> str:
    return f"G8_PEER_REVIEW_REPORT_{study}.md"


# Mục bắt buộc của bản nhận xét phản biện, theo mẫu TỔNG HỢP của
# .claude/agents/binh-duyet.md (khuyến nghị 4 mức · lỗi nghiêm trọng kèm vị trí ·
# góp ý nhỏ · câu hỏi cho tác giả · kết luận tổng thể).
_REVIEW_REPORT_SECTIONS: Sequence[tuple[str, Sequence[str]]] = (
    ("KHUYẾN NGHỊ", ("KHUYẾN NGHỊ", "RECOMMENDATION")),
    ("LỖI NGHIÊM TRỌNG", ("LỖI NGHIÊM TRỌNG", "MAJOR")),
    ("GÓP Ý NHỎ", ("GÓP Ý NHỎ", "MINOR")),
    ("CÂU HỎI CHO TÁC GIẢ", ("CÂU HỎI CHO TÁC GIẢ", "QUESTIONS FOR THE AUTHORS")),
    ("KẾT LUẬN TỔNG THỂ", ("KẾT LUẬN TỔNG THỂ", "OVERALL")),
)

_REVIEW_RECOMMENDATIONS = (
    "CHẤP NHẬN",
    "SỬA NHỎ",
    "SỬA LỚN",
    "TỪ CHỐI",
    "ACCEPT",
    "MINOR REVISION",
    "MAJOR REVISION",
    "REJECT",
)

# "Vệt công cụ nội bộ" — doctrine binh-duyet.md §Lăng kính 3 mục 8 xếp mức CHẶN:
# còn sót bất kỳ mục nào = KHÔNG sẵn sàng nộp, không phải góp ý nhỏ.
_INTERNAL_TRACE_PATTERNS: Sequence[tuple[str, Any]] = (
    ("nhãn [CẦN…] còn trong thân bài", re.compile(r"\[CẦN[^\]]{0,80}\]")),
    ("nhắc tới 'agent' của hệ nội bộ", re.compile(r"\bagent\b", re.IGNORECASE)),
    ("nhắc 'checklist nội bộ'", re.compile(r"checklist\s+nội\s+bộ", re.IGNORECASE)),
    (
        "hướng dẫn biên tập còn sót",
        re.compile(r"(cần chủ nhiệm bổ sung|điền vào đây|TODO|FIXME|XXX)", re.IGNORECASE),
    ),
    (
        "lựa chọn (A) hay (B) còn bỏ ngỏ",
        re.compile(r"\(A\)\s*(hay|hoặc|or)\s*\(B\)", re.IGNORECASE),
    ),
    (
        "tên file/công cụ nội bộ của pipeline",
        re.compile(r"(run_g\d+_auto\.py|G\d_checkpoint\.json|study_meta\.json|approval_ledger)", re.IGNORECASE),
    ),
)

# ICMJE bản Updated January 2026 — Mục V (AI) là phần cấp 1 MỚI; nhãn "ICMJE 2023"
# hiện còn trong run_g8_auto.py là STALE.
_AI_DISCLOSURE_TOKENS = ("trí tuệ nhân tạo", "artificial intelligence", "AI-assisted", "LLM")
_AI_TOOL_NAME_RE = re.compile(
    r"(chatgpt|gpt-?[0-9]|claude|gemini|copilot|bard|llama|mistral)", re.IGNORECASE
)

_REGISTRY_ID_RE = re.compile(
    r"(NCT\d{8}|ISRCTN\d{8}|ChiCTR[-A-Za-z0-9]+|CTRI/\d{4}/\d{2}/\d+|"
    r"IRCT\d+[A-Za-z0-9]*|jRCT\d+|ACTRN\d{14}|EUCTR[\d-]+)"
)

# Thiết kế thỏa ĐỊNH NGHĨA THỬ NGHIỆM của ICMJE ("prospectively assigns people to
# an intervention"). CỐ Ý rộng hơn design_code=="rct": ICMJE liệt kê đích danh cả
# can thiệp cải tiến chất lượng, giáo dục, hành vi. Với thiết kế quan sát, ICMJE
# KHUYẾN KHÍCH chứ không bắt buộc đăng ký ⇒ chỉ nhắc, không tính là lỗi.
_TRIAL_LIKE_DESIGNS = frozenset({"rct"})
_REGISTRATION_ENCOURAGED_DESIGNS = frozenset({"cohort", "cross_sectional", "case_control"})

# 5 trường bắt buộc của data sharing statement (ICMJE §III.L.3).
_DATA_SHARING_FIELDS: Sequence[tuple[str, Sequence[str]]] = (
    ("có chia sẻ IPD hay không", ("chia sẻ", "share")),
    ("dữ liệu nào được chia sẻ", ("dữ liệu nào", "what data")),
    ("tài liệu kèm theo", ("protocol", "đề cương", "SAP")),
    ("mốc thời gian", ("thời gian", "when", "bắt đầu")),
    ("tiêu chí truy cập", ("tiêu chí", "access", "cơ chế")),
)

STANDARDS_BASIS: Sequence[Mapping[str, str]] = (
    {
        "standard": "ICMJE Recommendations (Updated January 2026) — Mục V: Use of AI in Publishing",
        "scope": (
            "V.A: khai báo AI ở CẢ cover letter lẫn bản thảo, nêu công cụ/mục đích, "
            "cấm liệt kê AI là tác giả, cấm trích dẫn nội dung AI làm nguồn gốc; "
            "V.B: người PHẢN BIỆN phải khai dùng AI và không tải bản thảo lên công "
            "cụ không bảo đảm bảo mật"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §II.B.1.b — nghĩa vụ của người bình duyệt",
        "scope": (
            "Người phản biện phải khai mọi quan hệ/hoạt động có thể làm thiên lệch "
            "ý kiến và phải TỪ CHỐI khi có xung đột"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §III.L.1 — đăng ký nghiên cứu trước tuyển ca đầu tiên",
        "scope": (
            "Điều kiện để được xem xét đăng; phê duyệt của Hội đồng Đạo đức KHÔNG "
            "thay thế được đăng ký; đăng ký hồi cứu không đạt mục đích nào"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §III.L.3 — tuyên bố chia sẻ dữ liệu",
        "scope": (
            "Báo cáo kết quả thử nghiệm lâm sàng phải có đủ 5 trường; "
            "'undecided' KHÔNG phải câu trả lời chấp nhận được"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §IV.B — nội dung bắt buộc của cover letter",
        "scope": (
            "Khai mọi bản nộp/báo cáo trước có thể bị coi là trùng lặp; COI; xác nhận "
            "mọi tác giả đã đọc và duyệt; thông tin liên hệ; trạng thái preprint"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "Cochrane RoB — miền báo cáo kết quả chọn lọc (selective reporting)",
        "scope": (
            "Kết cục chính trong bản thảo phải khớp kết cục chính đã định trước ở "
            "SAP/đăng ký; lệch mà không giải trình là sai lệch báo cáo"
        ),
        "url": "https://methods.cochrane.org/risk-bias-2",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════


def _criterion(criterion_id: str, label: str, status: str, evidence: str,
               action: str = "") -> dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _g8_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G8")
    return value if isinstance(value, Mapping) else {}


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return "[CẦN" not in text.upper() and "[CAN" not in text.upper()
    return bool(value)


def _body_without_labels_section(manuscript: str) -> str:
    """Thân bài, bỏ phần phụ lục/checklist ở cuối nếu có.

    Quét vệt công cụ nội bộ chỉ có nghĩa trên phần sẽ gửi tạp chí; nếu bản thảo có
    mục phụ lục kiểm tra nội bộ thì phần đó không phải "sót".
    """
    for marker in ("## PHỤ LỤC", "## APPENDIX", "<!-- INTERNAL", "## CHECKLIST NỘI BỘ"):
        idx = manuscript.find(marker)
        if idx > 0:
            return manuscript[:idx]
    return manuscript


def ledger_records(study: str, repo_root: Path) -> list[dict[str, Any]]:
    """Đọc sổ cái phê duyệt dạng thô (chỉ để ĐỐI CHIẾU, không để phán cổng)."""
    path = Path(repo_root) / "exports" / str(study) / "approval_ledger.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def _latest_approved(records: Sequence[Mapping[str, Any]], gate_id: str) -> Optional[Mapping[str, Any]]:
    """Bản ghi APPROVED mới nhất của một cổng, theo timestamp ISO.

    CỐ Ý chỉ dùng cho việc ĐỐI CHIẾU reviewer_ref giữa các cổng (một báo cáo, không
    phải một phán quyết). Mọi kết luận "cổng đã duyệt hay chưa" phải hỏi
    ``GC.ledger_approved`` để hai nơi không đọc cùng một sổ mà nói hai chuyện.
    """
    candidates = [
        r for r in records
        if str(r.get("gate_id", "")).strip().upper() == gate_id.upper()
        and str(r.get("decision", "")).strip().upper() == "APPROVED"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: str(r.get("timestamp_utc", "")))


def _reviewer_ref(record: Optional[Mapping[str, Any]]) -> str:
    if not record:
        return ""
    for key in ("reviewer_identity_reference", "reviewer_ref"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    return ""


# ════════════════════════════════════════════════════════════════════════════
# Các phép kiểm nội dung
# ════════════════════════════════════════════════════════════════════════════


def scan_internal_traces(manuscript: str) -> list[str]:
    """Tìm vệt công cụ nội bộ còn sót trong bản thảo (doctrine xếp mức CHẶN)."""
    body = _body_without_labels_section(manuscript)
    found: list[str] = []
    for label, pattern in _INTERNAL_TRACE_PATTERNS:
        match = pattern.search(body)
        if match:
            snippet = re.sub(r"\s+", " ", match.group(0))[:60]
            found.append(f"{label} ({snippet!r})")
    return found


def primary_outcome_consistency(
    sap_text: str, manuscript: str, declared_outcome: str
) -> tuple[str, str]:
    """So kết cục chính đã định trước với kết cục chính trong bản thảo.

    Trả (status, evidence). Đây là miền "báo cáo kết quả chọn lọc" của Cochrane RoB
    — lệch mà không giải trình là một trong những sai lệch nặng nhất, và là thứ máy
    kiểm được vì cả SAP lẫn bản thảo đều là văn bản.
    """
    if not _present(declared_outcome):
        return "REVIEW", "chưa khai kết cục chính định trước (gate_params.G8.primary_outcome)"
    needle = declared_outcome.strip().casefold()
    in_sap = bool(sap_text) and needle in sap_text.casefold()
    in_manuscript = bool(manuscript) and needle in manuscript.casefold()
    if not sap_text:
        return "REVIEW", "không đọc được SAP (G4) để đối chiếu kết cục chính"
    if not manuscript:
        return "REVIEW", "không đọc được bản thảo (G7) để đối chiếu kết cục chính"
    if in_sap and in_manuscript:
        return "PASS", f"kết cục chính {declared_outcome[:60]!r} có mặt ở CẢ SAP và bản thảo"
    missing = []
    if not in_sap:
        missing.append("SAP (G4)")
    if not in_manuscript:
        missing.append("bản thảo (G7)")
    return "BLOCK", (
        f"kết cục chính {declared_outcome[:60]!r} KHÔNG tìm thấy trong: "
        f"{', '.join(missing)} — nghi báo cáo kết quả chọn lọc"
    )


def ai_disclosure_issues(manuscript: str, g8: Mapping[str, Any]) -> list[str]:
    """Kiểm khai báo AI theo ICMJE Mục V.A (bản 1/2026)."""
    issues: list[str] = []
    declared = g8.get("ai_use_declared")
    if declared is None:
        issues.append("chưa khai dứt khoát có/không dùng AI (ICMJE: không khai có thể bị coi là misconduct)")
        return issues
    if declared is True:
        if not _present(g8.get("ai_tools")):
            issues.append("khai có dùng AI nhưng thiếu TÊN CÔNG CỤ + phiên bản")
        if not _present(g8.get("ai_purpose")):
            issues.append("khai có dùng AI nhưng thiếu MỤC ĐÍCH sử dụng")
        if g8.get("ai_declared_in_cover_letter") is not True:
            issues.append("thiếu khai AI trong COVER LETTER (ICMJE đòi khai ở CẢ hai nơi)")
        if manuscript and not any(
            token.casefold() in manuscript.casefold() for token in _AI_DISCLOSURE_TOKENS
        ):
            issues.append("thiếu khai AI trong chính BẢN THẢO")
    # Cấm tuyệt đối: AI ở vị trí tác giả, hoặc AI bị trích dẫn làm nguồn gốc.
    if manuscript:
        author_block = manuscript[:3000]
        if _AI_TOOL_NAME_RE.search(author_block) and re.search(
            r"(tác giả|author)", author_block, re.IGNORECASE
        ):
            issues.append("nghi có tên công cụ AI trong khối TÁC GIẢ — ICMJE cấm liệt kê AI là tác giả")
        ref_idx = max(
            manuscript.rfind("TÀI LIỆU THAM KHẢO"),
            manuscript.rfind("REFERENCES"),
        )
        if ref_idx > 0 and _AI_TOOL_NAME_RE.search(manuscript[ref_idx:]):
            issues.append("nghi TRÍCH DẪN nội dung AI trong danh mục tài liệu tham khảo — ICMJE không chấp nhận")
    return issues


def registration_issues(design_code: str, g8: Mapping[str, Any], g2: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Kiểm đăng ký nghiên cứu theo ICMJE §III.L.1.

    Trả (mức, danh sách vấn đề). CỐ Ý không gắn vào ``design_code == "rct"``: định
    nghĩa thử nghiệm của ICMJE rộng hơn (mọi phân bổ TIẾN CỨU vào một can thiệp,
    kể cả can thiệp giáo dục/cải tiến chất lượng). Ngược lại với thiết kế quan sát
    ICMJE nói rõ chỉ KHUYẾN KHÍCH — báo lỗi ở đó là báo sai chuẩn.
    """
    interventional = design_code in _TRIAL_LIKE_DESIGNS or g8.get("interventional") is True
    registration_id = str(
        g8.get("registration_id") or g2.get("g2_registration") or ""
    ).strip()
    problems: list[str] = []
    if not interventional:
        if design_code in _REGISTRATION_ENCOURAGED_DESIGNS and not registration_id:
            return "PASS", ["thiết kế quan sát — ICMJE KHUYẾN KHÍCH đăng ký, không bắt buộc"]
        return "PASS", []
    if not registration_id or not _REGISTRY_ID_RE.search(registration_id):
        problems.append(f"thiếu mã đăng ký hợp lệ (nhận được {registration_id or 'rỗng'!r})")
    reg_date = str(g8.get("registration_date") or "").strip()
    enrol_date = str(g8.get("first_enrolment_date") or "").strip()
    if reg_date and enrol_date:
        if reg_date > enrol_date:
            problems.append(
                f"ĐĂNG KÝ HỒI CỨU: ngày đăng ký {reg_date} SAU ngày tuyển ca đầu {enrol_date}"
            )
    else:
        problems.append("thiếu ngày đăng ký và/hoặc ngày tuyển ca đầu tiên để đối chiếu")
    if g8.get("registration_date_is_irb_date") is True:
        problems.append(
            "dùng ngày phê duyệt Hội đồng Đạo đức thay cho ngày đăng ký — ICMJE nói rõ không thay thế được"
        )
    return ("REVIEW" if problems else "PASS"), problems


def data_sharing_issues(design_code: str, g8: Mapping[str, Any]) -> tuple[str, list[str]]:
    """ICMJE §III.L.3 — chỉ BẮT BUỘC với báo cáo kết quả thử nghiệm lâm sàng."""
    interventional = design_code in _TRIAL_LIKE_DESIGNS or g8.get("interventional") is True
    statement = str(g8.get("data_sharing_statement") or "")
    if not interventional:
        return "PASS", ["không phải báo cáo kết quả thử nghiệm — ICMJE không bắt buộc"]
    if not _present(statement):
        return "REVIEW", ["thiếu tuyên bố chia sẻ dữ liệu (bắt buộc cho thử nghiệm lâm sàng)"]
    problems: list[str] = []
    if re.search(r"(undecided|chưa quyết định|sẽ xem xét sau)", statement, re.IGNORECASE):
        problems.append("chứa 'undecided' — ICMJE nói rõ đây KHÔNG phải câu trả lời chấp nhận được")
    lowered = statement.casefold()
    for label, tokens in _DATA_SHARING_FIELDS:
        if not any(token.casefold() in lowered for token in tokens):
            problems.append(f"thiếu trường: {label}")
    return ("REVIEW" if problems else "PASS"), problems


def review_report_issues(report_text: str) -> list[str]:
    """Bản nhận xét phản biện có đủ cấu trúc mẫu của doctrine binh-duyet.md không."""
    if not report_text.strip():
        return ["chưa có bản nhận xét phản biện"]
    problems: list[str] = []
    upper = report_text.upper()
    for label, alternatives in _REVIEW_REPORT_SECTIONS:
        if not any(alt.upper() in upper for alt in alternatives):
            problems.append(f"thiếu mục '{label}'")
    if not any(rec.upper() in upper for rec in _REVIEW_RECOMMENDATIONS):
        problems.append("thiếu KHUYẾN NGHỊ rõ mức (chấp nhận / sửa nhỏ / sửa lớn / từ chối)")
    return problems


# ════════════════════════════════════════════════════════════════════════════
# Lõi đánh giá
# ════════════════════════════════════════════════════════════════════════════


def evaluate_g8_quality(
    *,
    study: str,
    checkpoint: Mapping[str, Any],
    presubmission_text: str,
    manuscript_text: str,
    sap_text: str,
    review_report_text: str,
    g2_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    citation_ok: bool,
    citation_detail: str,
    ledger_signed: bool,
    ledger_reason: str,
    signature_scope: Optional[str],
    role_key_available: bool,
    cross_gate_refs: Mapping[str, str],
) -> dict[str, Any]:
    """Chấm G8 hai tầng: máy kiểm NỘI DUNG, rồi bằng chứng bình duyệt người thật."""
    g8 = _g8_meta(meta)
    design_code = str(checkpoint.get("design_code") or g2_checkpoint.get("design_code") or "")
    automatic: list[dict[str, str]] = []
    approval: list[dict[str, str]] = []

    # ── G8-AUTO-00 — guardrail nền ─────────────────────────────────────────
    guardrail = checkpoint.get("guardrail")
    guardrail_passed = (
        guardrail.get("passed") is True if isinstance(guardrail, Mapping) else False
    )
    automatic.append(_criterion(
        "G8-AUTO-00",
        "Guardrail liêm chính G8 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail.passed={guardrail_passed}",
        "Sửa lỗi guardrail của run_g8_auto.py trước khi chấm chất lượng.",
    ))

    # ── G8-AUTO-01 — có gói tiền nộp bài ───────────────────────────────────
    automatic.append(_criterion(
        "G8-AUTO-01",
        "Có gói tiền nộp bài A9 để bình duyệt",
        "PASS" if presubmission_text.strip() else "BLOCK",
        f"{len(presubmission_text)} ký tự",
        "Chạy run_g8_auto.py để sinh gói A9 trước.",
    ))

    # ── G8-AUTO-02 — có bản thảo thật ──────────────────────────────────────
    automatic.append(_criterion(
        "G8-AUTO-02",
        "Có bản thảo G7 để đối chiếu nội dung",
        "PASS" if manuscript_text.strip() else "REVIEW",
        f"{len(manuscript_text)} ký tự",
        "Chạy G7 sinh bản thảo; không có bản thảo thì mọi kiểm nội dung đều rỗng.",
    ))

    # ── G8-AUTO-03 — A12 kiểm chứng trích dẫn PHẢI đạt ─────────────────────
    # Hiện A12 chỉ nuôi 2/30 điểm tự chấm và KHÔNG nằm trong 5 điều kiện quyết
    # định g8_status, nên G8 có thể in "PASS — ĐỦ ĐIỀU KIỆN NỘP BÀI" khi A12 chưa
    # từng chạy. Ở hợp đồng này, trích dẫn chưa xác minh là lỗi CHẶN.
    automatic.append(_criterion(
        "G8-AUTO-03",
        "Cổng A12 (kiểm chứng trích dẫn) đã đạt thật",
        "PASS" if citation_ok else "BLOCK",
        citation_detail or f"citation_ok={citation_ok}",
        "Chạy agent kiem-chung-trich-dan và tools/check_citation_retraction.py cho tới khi sạch.",
    ))

    # ── G8-AUTO-04 — vệt công cụ nội bộ trong bản thảo ─────────────────────
    traces = scan_internal_traces(manuscript_text) if manuscript_text else []
    automatic.append(_criterion(
        "G8-AUTO-04",
        "Bản thảo không còn vệt công cụ nội bộ",
        "BLOCK" if traces else "PASS",
        "; ".join(traces) if traces else "không thấy nhãn [CẦN], tên file pipeline hay hướng dẫn biên tập sót lại",
        "Xóa mọi vệt nội bộ khỏi thân bài — doctrine xếp đây là lỗi CHẶN, không phải góp ý nhỏ.",
    ))

    # ── G8-AUTO-05 — báo cáo kết quả chọn lọc ──────────────────────────────
    outcome_status, outcome_evidence = primary_outcome_consistency(
        sap_text, manuscript_text, str(g8.get("primary_outcome") or "")
    )
    automatic.append(_criterion(
        "G8-AUTO-05",
        "Kết cục chính trong bản thảo khớp kết cục đã định trước ở SAP",
        outcome_status,
        outcome_evidence,
        "Ghi gate_params.G8.primary_outcome; nếu đổi kết cục chính thì phải giải trình công khai trong bài.",
    ))

    # ── G8-AUTO-06 — khai báo AI theo ICMJE 1/2026 ─────────────────────────
    ai_issues = ai_disclosure_issues(manuscript_text, g8)
    automatic.append(_criterion(
        "G8-AUTO-06",
        "Khai báo dùng AI đủ theo ICMJE Mục V (bản 1/2026)",
        "REVIEW" if ai_issues else "PASS",
        "; ".join(ai_issues) if ai_issues else "khai báo AI đầy đủ ở cover letter và bản thảo",
        "Khai gate_params.G8: ai_use_declared, ai_tools, ai_purpose, ai_declared_in_cover_letter.",
    ))

    # ── G8-AUTO-07 — đăng ký nghiên cứu ────────────────────────────────────
    reg_status, reg_problems = registration_issues(design_code, g8, g2_checkpoint)
    automatic.append(_criterion(
        "G8-AUTO-07",
        "Đăng ký nghiên cứu đúng ICMJE (tiền cứu, không dùng ngày IRB thay thế)",
        reg_status,
        "; ".join(reg_problems) if reg_problems else "đăng ký hợp lệ hoặc không thuộc diện bắt buộc",
        "Khai registration_id/registration_date/first_enrolment_date trong gate_params.G8.",
    ))

    # ── G8-AUTO-08 — chia sẻ dữ liệu ───────────────────────────────────────
    ds_status, ds_problems = data_sharing_issues(design_code, g8)
    automatic.append(_criterion(
        "G8-AUTO-08",
        "Tuyên bố chia sẻ dữ liệu đủ 5 trường (thử nghiệm lâm sàng)",
        ds_status,
        "; ".join(ds_problems) if ds_problems else "đủ 5 trường theo ICMJE §III.L.3",
        "Viết data_sharing_statement đủ 5 trường; 'undecided' không được chấp nhận.",
    ))

    # ── G8-AUTO-09 — cover letter ──────────────────────────────────────────
    cover_missing = [
        label for label, key in (
            ("khai nộp trùng lặp", "cover_letter_no_duplicate_submission"),
            ("khai xung đột lợi ích", "cover_letter_coi_declared"),
            ("xác nhận mọi tác giả đã duyệt", "cover_letter_all_authors_approved"),
            ("thông tin liên hệ tác giả", "cover_letter_corresponding_contact"),
            ("trạng thái preprint", "cover_letter_preprint_status"),
        )
        if g8.get(key) is not True
    ]
    automatic.append(_criterion(
        "G8-AUTO-09",
        "Cover letter có đủ nội dung bắt buộc (ICMJE §IV.B)",
        "REVIEW" if cover_missing else "PASS",
        "thiếu: " + "; ".join(cover_missing) if cover_missing else "đủ 5 nhóm nội dung",
        "Soạn cover letter theo ICMJE §IV.B rồi đánh dấu từng mục trong gate_params.G8.",
    ))

    # ── G8-AUTO-10 — checklist chuẩn báo cáo có tham gia quyết định không ──
    # Lệch NỘI BỘ đã xác nhận: artifact in "PASS khi đáp ứng TẤT CẢ 6 điều kiện
    # BẮT BUỘC" và liệt kê mục 6 là "checklist ≥ 60%", nhưng g8_status của
    # run_g8_auto.py chỉ tính 5 điều kiện — reporting_ok bị bỏ ngoài. Nghĩa là
    # một đề tài có checklist 30% vẫn in PASS ngay dưới dòng báo 30%.
    reporting_pct = checkpoint.get("reporting_completeness_pct")
    if reporting_pct is None:
        reporting_pct = checkpoint.get("reporting_pct")
    try:
        pct = float(reporting_pct)
    except (TypeError, ValueError):
        pct = None
    if pct is None:
        rep_status, rep_evidence = "REVIEW", "không đọc được % hoàn thành checklist chuẩn báo cáo"
    elif pct < 60:
        rep_status = "REVIEW"
        rep_evidence = (
            f"checklist chuẩn báo cáo {pct:.0f}% < 60% — lưu ý run_g8_auto.py KHÔNG "
            "tính điều kiện này vào g8_status dù artifact in nó là 'bắt buộc'"
        )
    else:
        rep_status, rep_evidence = "PASS", f"checklist chuẩn báo cáo {pct:.0f}%"
    automatic.append(_criterion(
        "G8-AUTO-10",
        "Checklist chuẩn báo cáo đạt ngưỡng đã tuyên bố là bắt buộc",
        rep_status,
        rep_evidence,
        "Bổ sung các mục checklist còn thiếu trong bản thảo trước khi mời phản biện.",
    ))

    # ── Tầng BẰNG CHỨNG BÌNH DUYỆT NGƯỜI THẬT ──────────────────────────────
    report_problems = review_report_issues(review_report_text)
    approval.append(_criterion(
        "G8-HUMAN-01",
        "Có bản NHẬN XÉT phản biện thật (không phải bản tự kiểm do máy sinh)",
        "PASS" if not report_problems else "REVIEW",
        "; ".join(report_problems) if report_problems else "đủ khuyến nghị, lỗi nghiêm trọng, góp ý, câu hỏi, kết luận",
        f"Người phản biện viết {peer_review_report_name(study)} theo mẫu binh-duyet.md.",
    ))

    approval.append(_criterion(
        "G8-HUMAN-02",
        "Sổ cái có phê duyệt G8 hợp lệ đúng vai trò phản biện",
        "PASS" if ledger_signed else "REVIEW",
        ledger_reason or f"ledger_approved={ledger_signed}",
        f"Người phản biện tự ký: approve_gate.py --gate G8 --reviewer-role {GC.required_reviewer_role_hint('G8')}",
    ))

    # Mức bảo đảm của khóa — KHÔNG được diễn giải scope='role' thành "đã độc lập".
    if signature_scope == "role":
        scope_status = "PASS"
        scope_evidence = (
            "ký bằng khóa RIÊNG của nhóm phản biện (scope=role) — có dấu vết tách bạch "
            "vận hành, NHƯNG vẫn không chứng minh được người ký khác chủ nhiệm"
        )
    elif signature_scope == "shared":
        scope_status = "REVIEW"
        scope_evidence = (
            "ký bằng khóa CHUNG (scope=shared) — khóa này ký được MỌI vai trò, nên chữ "
            "ký không phân biệt được phản biện độc lập với chủ nhiệm tự ký"
        )
    else:
        scope_status = "REVIEW"
        scope_evidence = (
            f"chưa xác định phạm vi khóa; khóa riêng nhóm phản biện có sẵn={role_key_available}"
        )
    approval.append(_criterion(
        "G8-HUMAN-03",
        "Mức bảo đảm của khóa ký được nêu đúng (không nói quá)",
        scope_status,
        scope_evidence,
        "Tạo khóa riêng: setup_gate_approval_key.py --role INDEPENDENT_PEER_REVIEWER, và để người phản biện giữ.",
    ))

    # Đối chiếu reviewer_ref giữa các cổng — chỉ số ĐỘC LẬP rẻ nhất hiện có.
    g8_ref = cross_gate_refs.get("G8", "")
    clashes = [
        gate for gate, ref in cross_gate_refs.items()
        if gate != "G8" and ref and g8_ref and ref == g8_ref
    ]
    if not g8_ref:
        ref_status, ref_evidence = "REVIEW", "chưa có bản ghi phê duyệt G8 để đối chiếu"
    elif clashes:
        ref_status = "REVIEW"
        ref_evidence = (
            f"reviewer_ref của G8 ({g8_ref!r}) TRÙNG với cổng {', '.join(sorted(clashes))} "
            "— cùng một người đang ký nhiều vai trò"
        )
    else:
        ref_status = "PASS"
        ref_evidence = f"reviewer_ref của G8 ({g8_ref!r}) khác mọi cổng còn lại"
    approval.append(_criterion(
        "G8-HUMAN-04",
        "Người ký G8 khác người ký các cổng khác (chỉ dấu độc lập)",
        ref_status,
        ref_evidence,
        "Mời người phản biện KHÔNG phải tác giả/chủ nhiệm, và dùng reviewer_ref riêng.",
    ))

    reviewer_declarations = [
        label for label, key in (
            ("khai xung đột lợi ích của người phản biện", "reviewer_coi_declared"),
            ("cam kết không phải tác giả/đồng nghiệp trực tiếp", "reviewer_independence_declared"),
            ("khai có/không dùng AI khi phản biện (ICMJE V.B)", "reviewer_ai_use_declared"),
            ("cam kết không tải bản thảo lên công cụ AI không bảo mật", "reviewer_confidentiality_declared"),
        )
        if g8.get(key) is not True
    ]
    approval.append(_criterion(
        "G8-HUMAN-05",
        "Người phản biện đã khai COI, tính độc lập và việc dùng AI",
        "REVIEW" if reviewer_declarations else "PASS",
        "thiếu: " + "; ".join(reviewer_declarations) if reviewer_declarations else "đủ 4 khai báo",
        "ICMJE §II.B.1.b và §V.B: người phản biện phải khai quan hệ gây thiên lệch và việc dùng AI.",
    ))

    # ── Tổng hợp ───────────────────────────────────────────────────────────
    auto_blocked = any(row["status"] == "BLOCK" for row in automatic)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    approval_complete = all(row["status"] == "PASS" for row in approval)
    has_review_evidence = not report_problems

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT
    elif not has_review_evidence and not ledger_signed:
        status = STATUS_READY
    elif not approval_complete:
        status = STATUS_PENDING
    else:
        status = STATUS_REVIEWED

    pending = [
        row["action"] for row in automatic + approval
        if row["status"] != "PASS" and row.get("action")
    ]
    return {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G8",
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "package_ready_for_review": not auto_blocked and not auto_review,
        "review_evidence_complete": approval_complete,
        "signature_scope": signature_scope,
        "automatic_criteria": automatic,
        "approval_criteria": approval,
        "pending_actions": list(dict.fromkeys(pending)),
        "standards_basis": [dict(item) for item in STANDARDS_BASIS],
        "scope_statement": (
            "PASS_G8_REVIEW_RECORDED CỐ Ý không mang chữ 'ĐỘC LẬP'. Chữ ký G8 chứng "
            "minh rằng một người truy cập được khóa ký đã xác nhận artifact với nội "
            "dung đúng bằng hash lúc ký, và tự khai vai trò phản biện độc lập. Vì "
            "HMAC là mật mã ĐỐI XỨNG (máy xác minh buộc phải giữ khóa đã ký), hệ "
            "KHÔNG chứng minh được người ký khác chủ nhiệm đề tài; khóa riêng theo "
            "vai trò chỉ chứng minh một FILE tồn tại trên cùng máy. Bằng chứng độc "
            "lập THẬT phải đến từ ngoài hệ (thư phản biện có danh tính, biên bản hội "
            "đồng). Cổng chặn thật của G8 vẫn là run_g10_assemble.py."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


# ════════════════════════════════════════════════════════════════════════════
# Xuất báo cáo, cập nhật checkpoint, CLI
# ════════════════════════════════════════════════════════════════════════════


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    out_dir = Path(out_dir)
    (out_dir / "G8_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G8 (BÌNH DUYỆT) — {study}",
        "",
        f"**Trạng thái:** `{report.get('status')}`",
        f"**Phiên bản hợp đồng:** {report.get('contract_version')}",
        f"**Phạm vi khóa ký:** {report.get('signature_scope') or 'không xác định'}",
        "",
        "## Kiểm tự động (máy kiểm NỘI DUNG gói tiền nộp bài)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{str(row.get('evidence') or '').replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Bằng chứng bình duyệt người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("approval_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{str(row.get('evidence') or '').replace('|', '/')} |"
        )
    lines.extend(["", "## Việc còn lại"])
    pending = report.get("pending_actions") or []
    lines.extend(f"- {item}" for item in pending)
    if not pending:
        lines.append("- Không còn mục chờ trong hợp đồng G8.")
    lines.extend([
        "",
        "## Nền chuẩn",
        "| Chuẩn | Phạm vi | Nguồn |",
        "|---|---|---|",
    ])
    for item in report.get("standards_basis", []):
        source = str(item.get("url") or item.get("doi") or item.get("pmid") or "")
        lines.append(
            f"| {item.get('standard')} | {item.get('scope')} | {source.replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Giới hạn phán định",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])
    md_path = out_dir / "G8_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def refresh_checkpoint(*, study: str, out_dir: Path, report: Mapping[str, Any],
                       quality_report_path: Path) -> Path:
    """Gắn kết quả chất lượng vào G8_checkpoint, giữ nguyên khóa downstream."""
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G8_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update({
        "study": study,
        "gate": "G8",
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_gate": dict(report),
    })
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return checkpoint_path


def evaluate_study(study: str, out_dir: Path, *, repo_root: Optional[Path] = None,
                   write: bool = True) -> dict[str, Any]:
    """Chấm lại G8 từ artifact đã có; KHÔNG ký, KHÔNG tự tạo nhận xét phản biện."""
    out_dir = Path(out_dir)
    repo_root = Path(repo_root) if repo_root else out_dir.parent.parent
    checkpoint = _read_json(out_dir / "G8_checkpoint.json")
    presubmission = out_dir / presubmission_artifact_name(study)

    try:
        import run_g10_assemble as G10
        citation_ok, citation_detail = G10.citation_verification_ok(study, out_dir)
    except Exception as exc:  # pragma: no cover - lưới an toàn
        citation_ok, citation_detail = False, f"không kiểm được A12: {exc}"

    ledger_signed = GC.ledger_approved("G8", study, presubmission, repo_root=repo_root)
    try:
        ledger_reason = "" if ledger_signed else GC.gate_block_reason(
            "G8", study, presubmission, repo_root=repo_root
        )
    except Exception:  # pragma: no cover
        ledger_reason = ""
    try:
        scope = GC.approving_signature_scope("G8", study, repo_root=repo_root)
    except Exception:  # pragma: no cover
        scope = None
    try:
        role_key = GC.per_role_key_available(REVIEWER_ROLE_GROUP)
    except Exception:  # pragma: no cover
        role_key = False

    records = ledger_records(study, repo_root)
    cross_refs = {
        gate: _reviewer_ref(_latest_approved(records, gate))
        for gate in ("G2", "G4", "G5", "G8", "G9")
    }

    report = evaluate_g8_quality(
        study=study,
        checkpoint=checkpoint,
        presubmission_text=_read_text(presubmission),
        manuscript_text=_read_text(out_dir / manuscript_artifact_name(study)),
        sap_text=_read_text(out_dir / f"G4_A5_SAP_FINAL_{study}.md"),
        review_report_text=_read_text(out_dir / peer_review_report_name(study)),
        g2_checkpoint=_read_json(out_dir / "G2_checkpoint.json"),
        meta=GC.load_study_meta(out_dir),
        citation_ok=bool(citation_ok),
        citation_detail=str(citation_detail),
        ledger_signed=bool(ledger_signed),
        ledger_reason=str(ledger_reason),
        signature_scope=scope,
        role_key_available=bool(role_key),
        cross_gate_refs=cross_refs,
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        refresh_checkpoint(
            study=study, out_dir=out_dir, report=report,
            quality_report_path=report_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại hợp đồng chất lượng G8; không ký thay người phản biện."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
    repo_root = Path(__file__).resolve().parents[1]
    study = re.sub(r"[^\w\-]", "_", args.study.strip().replace(" ", "-"))
    out_dir = repo_root / "exports" / study
    report = evaluate_study(study, out_dir, repo_root=repo_root, write=True)
    print(f"G8 quality status: {report['status']}")
    print(f"Phạm vi khóa ký: {report.get('signature_scope') or 'không xác định'}")
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["status"] != "PASS":
            print(f"  {row['status']:6} {row['id']} — {row['label']}")
            print(f"         ↳ {row['evidence']}")
    print(f"Báo cáo: {out_dir / 'G8_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
