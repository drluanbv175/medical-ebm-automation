#!/usr/bin/env python3
"""Hợp đồng chất lượng cho cổng G7: BẢN THẢO IMRAD.

LÝ DO MODULE NÀY TỒN TẠI
------------------------
G7 sinh artifact A8 — **bản thảo sẽ gửi tạp chí**. Đây là cổng có đầu ra đi ra
ngoài xa nhất, nên sai ở đây là sai công khai.

Trước 2026-07-28, G7 không có hợp đồng chất lượng riêng (G0/G1/G2/G3 đều đã có).
Hệ quả TÁI HIỆN ĐƯỢC, không phải suy đoán — chạy thử trên một đề tài chỉ có G0
(và G0 còn đang BLOCKED, thoát mã 2), không hề có G1–G6:

    python tools/run_g7_auto.py --study ZZ-G7-PROBE
    → "✅ G7 HOÀN THÀNH", guardrail "✅ PASS", thoát mã 0
    → sinh trọn bản thảo IMRAD 3.547 từ, có Methods, có cỡ mẫu, có mục đạo đức,
      có tài liệu tham khảo

Tức G7 viết một bản thảo hoàn chỉnh cho đề tài **chưa có câu hỏi nghiên cứu, chưa
có thiết kế, chưa qua Hội đồng Đạo đức, chưa tính cỡ mẫu, chưa có dữ liệu, chưa
phân tích** — rồi tuyên bố hoàn thành.

ĐIỂM KHÁC CỐT LÕI so với g0/g1/g2/g3_quality_gate
-------------------------------------------------
Module này **đọc lại artifact A8 TỪ ĐĨA**, không chấm bản vừa sinh trong bộ nhớ.
Lý do: G7 là cổng mà bản thảo phải chuyển từ SKELETON sang BẢN THẢO THẬT bằng tay
bác sĩ. Chấm bản do chính công cụ vừa sinh ra thì mãi mãi chỉ đo được công cụ, và
không bao giờ biết bác sĩ đã điền tới đâu.

BA TRẠNG THÁI
-------------
- ``BLOCKED``: thiếu tiền đề bắt buộc (không có G1 → chuẩn báo cáo chọn sai), lỗi
  liêm chính, hoặc artifact khuyết.
- ``DRAFT_READY_NEEDS_HUMAN_REVIEW``: khung bản thảo đã dựng đúng; còn chờ kết quả
  thật và phần viết của bác sĩ. **Đây là trạng thái ĐÚNG của một lần chạy G7 sớm.**
- ``PASS_G7_CONFIRMED``: hết ô [CẦN KẾT QUẢ THẬT], có kết quả phân tích thật, trích
  dẫn đã kiểm chứng (A12), và tác giả đã chốt khai báo ICMJE. Chỉ khi đó mới được
  nói bản thảo sẵn sàng cho G8 (bình duyệt).

GIỚI HẠN PHÁN ĐỊNH: ``PASS_G7_CONFIRMED`` KHÔNG có nghĩa bản thảo tốt, đúng khoa
học, hay đáng đăng. Nó chỉ nói: không còn chỗ trống, không còn khẳng định về việc
chưa làm, và người thật đã xác nhận (SỬA 2026-07-30, audit toàn diện G0-G10,
G7-F4: G7 KHÔNG có trong ``_GATE_REQUIRED_STAKEHOLDERS`` của gate_contract.py —
đây là xác nhận nội dung, không phải chữ ký mật mã như G2/G4/G5/G8/G9/G10).
Thẩm định khoa học là việc của G8.

Chạy lại độc lập (không sinh lại bản thảo, không ghi đè bản bác sĩ đã sửa):
    python tools/g7_quality_gate.py --study <MÃ-ĐỀ-TÀI>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G7_CONFIRMED"

QUALITY_CONTRACT_VERSION = "G7-2026.1"

# Mục IMRAD bắt buộc phải có trong A8.
REQUIRED_A8_SECTIONS: Sequence[str] = (
    "TÓM TẮT",
    "I. GIỚI THIỆU",
    "II. PHƯƠNG PHÁP",
    "III. KẾT QUẢ",
    "IV. BÀN LUẬN",
    "V. KẾT LUẬN",
    "TÀI LIỆU THAM KHẢO",
)

# Khai báo bắt buộc theo ICMJE — thiếu là tạp chí trả lại.
ICMJE_DECLARATIONS: Sequence[tuple[str, str]] = (
    ("author_contributions", "Đóng góp tác giả (CRediT/ICMJE 4 tiêu chí)"),
    ("coi_declared", "Xung đột lợi ích"),
    ("funding_declared", "Nguồn tài trợ"),
    ("data_sharing_statement", "Tuyên bố chia sẻ dữ liệu"),
    ("ai_use_declared", "Khai báo sử dụng công cụ AI"),
)

_REVIEW_ROLES = {
    "pi", "principal investigator", "corresponding author", "tác giả liên lạc",
    "chủ nhiệm", "chủ nhiệm đề tài", "tác giả chính", "first author",
}

_PLACEHOLDER_MARKERS = ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "[TODO", "___")

# Câu KHẲNG ĐỊNH TRẦN về việc có thể chưa xảy ra. Đây là lớp phòng thủ cuối: kể cả
# khi bác sĩ tự viết tay vào bản thảo, những câu này không được đứng một mình mà
# thiếu bằng chứng tương ứng ở cổng trước.
_UNSUPPORTED_CLAIM_PATTERNS: Sequence[tuple[str, str, str]] = (
    (r"được\s+Hội\s*đồng\s*Đạo\s*đức\s+phê\s*duyệt", "irb_approved",
     "khẳng định đã được Hội đồng Đạo đức phê duyệt"),
    (r"đã\s+được\s+đăng\s*ký\s+(?:tại|trên)\s+ClinicalTrials", "registered",
     "khẳng định đã đăng ký ClinicalTrials.gov"),
    (r"SAP\s+đã\s+(?:được\s+)?khóa|kế\s*hoạch\s*phân\s*tích\s+đã\s+khóa", "sap_locked",
     "khẳng định đã khóa SAP"),
    (r"cơ\s*sở\s*dữ\s*liệu\s+đã\s+(?:được\s+)?khóa|dữ\s*liệu\s+đã\s+khóa", "db_locked",
     "khẳng định đã khóa cơ sở dữ liệu"),
)

_STANDARDS_BASIS = (
    {
        "standard": "ICMJE Recommendations",
        "scope": "Tiêu chí tác giả, khai báo COI/tài trợ/chia sẻ dữ liệu/AI",
        "url": "https://www.icmje.org/recommendations/",
    },
    {
        "standard": "EQUATOR Network",
        "scope": "Chuẩn báo cáo theo thiết kế (CONSORT/STROBE/PRISMA/STARD/TRIPOD+AI)",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "COPE",
        "scope": "Đạo đức xuất bản — không khẳng định điều chưa xảy ra",
        "url": "https://publicationethics.org/guidance",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════

def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return not any(m in text.upper() for m in _PLACEHOLDER_MARKERS)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _g7_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g7 = gp.get("G7")
    return g7 if isinstance(g7, Mapping) else {}


def _valid_iso_time(value: Any) -> bool:
    if not _present(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _criterion(criterion_id: str, label: str, status: str,
               evidence: str, action: str = "") -> Dict[str, str]:
    return {"id": criterion_id, "label": label, "status": status,
            "evidence": evidence, "action": action}


def count_placeholders(text: str) -> Dict[str, int]:
    """Đếm ô còn trống trong bản thảo HIỆN TẠI (bản trên đĩa, không phải bản mẫu)."""
    return {
        "total": len(re.findall(r"\[CẦN", text)),
        "results": len(re.findall(r"\[CẦN KẾT QUẢ THẬT", text)),
        "methods": len(re.findall(r"\[CẦN", _section(text, "II. PHƯƠNG PHÁP", "III. KẾT QUẢ"))),
        "results_section": len(re.findall(r"\[CẦN", _section(text, "III. KẾT QUẢ", "IV. BÀN LUẬN"))),
    }


def _section(text: str, start_marker: str, end_marker: str) -> str:
    """Cắt một mục của bản thảo (rỗng nếu không tìm thấy)."""
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i)
    return text[i:j] if j > i else text[i:]


def strip_placeholder_blocks(text: str) -> str:
    """Bỏ nội dung nằm TRONG nhãn [CẦN …] trước khi soi khẳng định.

    Nội dung trong nhãn là CHỈ DẪN cho bác sĩ ("KHÔNG được viết 'nghiên cứu được
    Hội đồng Đạo đức phê duyệt' trước khi việc đó xảy ra"), không phải khẳng định
    của bản thảo. Không bóc ra thì chính lời cảnh báo lại bị bắt là vi phạm — đã
    xảy ra thật khi chạy thử bản vá đầu tiên.
    """
    # Nhãn có thể dài, xuống dòng, và chứa ngoặc vuông lồng thì không — dùng
    # non-greedy tới "]" gần nhất, DOTALL để qua được xuống dòng.
    return re.sub(r"\[CẦN.*?\]", " ", text, flags=re.DOTALL)


def find_unsupported_claims(text: str, signals: Mapping[str, bool]) -> List[str]:
    """Câu khẳng định điều CHƯA có bằng chứng ở cổng trước.

    Đây là lớp phòng thủ cuối cùng trước khi bản thảo rời hệ thống: kể cả khi bác
    sĩ tự gõ vào, "nghiên cứu được Hội đồng Đạo đức phê duyệt" mà không có G2 thật
    vẫn phải bị chặn.
    """
    body = strip_placeholder_blocks(text or "")
    found: List[str] = []
    for pattern, signal, human in _UNSUPPORTED_CLAIM_PATTERNS:
        if re.search(pattern, body, re.IGNORECASE) and not signals.get(signal):
            found.append(human)
    return found


def _gate_present(cp: Mapping[str, Any]) -> bool:
    """Checkpoint có tồn tại và KHÔNG ở trạng thái chặn."""
    return bool(cp) and not GC.is_blocked(dict(cp))


# ════════════════════════════════════════════════════════════════════════════
# Đánh giá
# ════════════════════════════════════════════════════════════════════════════

def evaluate_g7_quality(
    *,
    manuscript_text: str,
    checkpoints: Mapping[str, Mapping[str, Any]],
    meta: Mapping[str, Any],
    artifact_paths: Optional[Mapping[str, Path]] = None,
    citation_verification_ok: Optional[bool] = None,
    guardrail_passed: Optional[bool] = None,
) -> Dict[str, Any]:
    """Chấm G7 theo hai tầng: máy kiểm được vs người thật phải chốt.

    `checkpoints` là dict {"G0": {...}, "G1": {...}, …, "G7": {...}}.
    """
    artifact_paths = artifact_paths or {}
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []

    g7cp = checkpoints.get("G7") or {}
    if guardrail_passed is None:
        guard = g7cp.get("guardrail")
        status_str = str((guard or {}).get("status", "")) if isinstance(guard, Mapping) else ""
        errs = (guard or {}).get("errors") if isinstance(guard, Mapping) else None
        guardrail_passed = bool(status_str) and not errs

    automatic.append(_criterion(
        "G7-AUTO-00", "Guardrail liêm chính G7 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa lỗi guardrail rồi sinh lại bản thảo.",
    ))

    # ── Tiền đề cổng trước ───────────────────────────────────────────────────
    # G1 là tiền đề CỨNG: không có thiết kế thì chuẩn báo cáo bị chọn sai
    # (run_g7_auto.py rơi về "cohort"/STROBE cho mọi đề tài), kéo theo cả checklist
    # phụ lục sai. Đó là sai có thể nhìn thấy từ bên ngoài, ở ngay trang đầu.
    g1_ok = _gate_present(checkpoints.get("G1") or {})
    automatic.append(_criterion(
        "G7-AUTO-01", "Có thiết kế nghiên cứu từ G1 (quyết định chuẩn báo cáo)",
        "PASS" if g1_ok else "BLOCK",
        f"G1_checkpoint={'có' if g1_ok else 'THIẾU/BLOCKED'}",
        "Chạy `python tools/run_g1_auto.py --study <mã>` trước; không có thiết kế "
        "thì chuẩn báo cáo (CONSORT/STROBE/PRISMA…) sẽ bị chọn sai cho cả bản thảo.",
    ))

    design_drift = g7cp.get("design_drift_warning")
    automatic.append(_criterion(
        "G7-AUTO-01b", "Mã thiết kế KHÔNG lệch giữa G1 và G2",
        "BLOCK" if design_drift else "PASS",
        design_drift or "G1/G2 khớp thiết kế (hoặc chỉ một nơi có giá trị)",
        "G1 suy luận và G2 (nơi bác sĩ có thể truyền --design tường minh) lệch nhau — "
        "chạy lại G1/G2 cho khớp trước khi tin chuẩn báo cáo của bản thảo này. Xem "
        "gate_contract.py::resolve_design_code().",
    ))

    missing_gates = [g for g in ("G0", "G2", "G3", "G4")
                     if not _gate_present(checkpoints.get(g) or {})]
    automatic.append(_criterion(
        "G7-AUTO-02", "Đủ tiền đề G0/G2/G3/G4 (câu hỏi · đạo đức · cỡ mẫu · SAP)",
        "PASS" if not missing_gates else "REVIEW",
        f"thiếu/chặn: {', '.join(missing_gates)}" if missing_gates
        else "G0/G2/G3/G4 đều có checkpoint không bị chặn",
        "Bản thảo chỉ là KHUNG cho tới khi các cổng này xong; đừng gửi đi.",
    ))

    # ── Kết quả thật ─────────────────────────────────────────────────────────
    results_final = bool(meta.get("results_final"))
    g6_ok = _gate_present(checkpoints.get("G6") or {})
    automatic.append(_criterion(
        "G7-AUTO-03", "Đã có kết quả phân tích THẬT (G6 + results_final)",
        "PASS" if (results_final and g6_ok) else "REVIEW",
        f"G6_checkpoint={'có' if g6_ok else 'thiếu'}; "
        f"study_meta.results_final={results_final}",
        "Khóa dữ liệu (G5) → chạy phân tích (G6/run_stats_analysis.py) → bác sĩ đặt "
        "results_final=true trong study_meta.json. Hệ KHÔNG tự bật cờ này.",
    ))

    # ── Artifact ─────────────────────────────────────────────────────────────
    text = manuscript_text or ""
    missing_sections = [s for s in REQUIRED_A8_SECTIONS
                        if s.casefold() not in text.casefold()]
    if not text.strip():
        art_status, art_evidence = "BLOCK", "Không đọc được artifact A8"
    elif missing_sections:
        art_status = "BLOCK"
        art_evidence = f"A8 thiếu mục: {', '.join(missing_sections)}"
    else:
        art_status = "PASS"
        art_evidence = f"A8 đủ {len(REQUIRED_A8_SECTIONS)} mục IMRAD"
    automatic.append(_criterion(
        "G7-AUTO-04", "Artifact A8 có đủ cấu trúc IMRAD", art_status, art_evidence,
        "Sinh lại bản thảo bằng run_g7_auto.py.",
    ))

    # ── Ô còn trống — đọc TỪ ĐĨA nên phản ánh phần bác sĩ đã điền ────────────
    ph = count_placeholders(text)
    automatic.append(_criterion(
        "G7-AUTO-05", "Không còn ô [CẦN KẾT QUẢ THẬT] trong bản thảo",
        "PASS" if ph["results"] == 0 else "REVIEW",
        f"còn {ph['results']} ô [CẦN KẾT QUẢ THẬT]; "
        f"tổng {ph['total']} ô [CẦN…] (Methods {ph['methods']}, Results {ph['results_section']})",
        "Điền kết quả thật vào Section III và Tóm tắt; KHÔNG nộp khi còn ô này.",
    ))

    # ── Khẳng định trần về việc chưa làm ─────────────────────────────────────
    g2cp = checkpoints.get("G2") or {}
    g4cp = checkpoints.get("G4") or {}
    signals = {
        "irb_approved": bool(meta.get("irb_approved")) or bool(g2cp.get("g2_irb_number")),
        "registered": _present(g2cp.get("g2_registration")),
        "sap_locked": bool(meta.get("sap_lock_date")) or str(
            g4cp.get("g4_status", "")).upper().startswith("LOCKED"),
        "db_locked": bool(meta.get("data_lock_date")),
    }
    claims = find_unsupported_claims(text, signals)
    automatic.append(_criterion(
        "G7-AUTO-06", "Không khẳng định việc chưa có bằng chứng ở cổng trước",
        "BLOCK" if claims else "PASS",
        "; ".join(claims) if claims else "không thấy khẳng định trần",
        "Xoá hoặc đổi thành [CẦN…] cho tới khi việc đó xảy ra thật. Đây là loại sai "
        "phạm liêm chính bị tạp chí rút bài.",
    ))

    # ── Trích dẫn đã kiểm chứng (A12) ────────────────────────────────────────
    if citation_verification_ok is None:
        cit_status, cit_evidence = "REVIEW", "chưa có artifact A12"
    elif citation_verification_ok:
        cit_status, cit_evidence = "PASS", "A12 có mặt"
    else:
        cit_status, cit_evidence = "REVIEW", "A12 có nhưng chưa sạch"
    automatic.append(_criterion(
        "G7-AUTO-07", "Trích dẫn đã được kiểm chứng (A12)", cit_status, cit_evidence,
        "Chạy agent `kiem-chung-trich-dan`, ghi kết quả vào "
        "A12_CITATION_VERIFICATION_<study>.md — run_g10_assemble.py sẽ CHẶN nếu thiếu.",
    ))

    # ── Tầng HUMAN ───────────────────────────────────────────────────────────
    g7 = _g7_meta(meta)

    title_ok = _present(g7.get("title"))
    authors_ok = _present(g7.get("authors"))
    human.append(_criterion(
        "G7-HUMAN-01", "Tiêu đề và danh sách tác giả đã chốt",
        "PASS" if (title_ok and authors_ok) else "REVIEW",
        f"title={'có' if title_ok else 'thiếu'}; authors={'có' if authors_ok else 'thiếu'}",
        "Điền gate_params.G7.title và .authors (tên/đơn vị/ORCID).",
    ))

    missing_decl = [label for key, label in ICMJE_DECLARATIONS if not _present(g7.get(key))]
    human.append(_criterion(
        "G7-HUMAN-02", "Đủ khai báo bắt buộc theo ICMJE",
        "PASS" if not missing_decl else "REVIEW",
        f"thiếu: {', '.join(missing_decl)}" if missing_decl else "5/5 khai báo có nội dung",
        "Điền author_contributions · coi_declared · funding_declared · "
        "data_sharing_statement · ai_use_declared trong gate_params.G7.",
    ))

    journal_ok = _present(g7.get("target_journal"))
    human.append(_criterion(
        "G7-HUMAN-03", "Đã chọn tạp chí đích",
        "PASS" if journal_ok else "REVIEW",
        f"target_journal={g7.get('target_journal') or 'thiếu'}",
        "Điền target_journal; định dạng và giới hạn từ phụ thuộc tạp chí.",
    ))

    read_ok = g7.get("manuscript_reviewed_confirmed") is True
    human.append(_criterion(
        "G7-HUMAN-04", "Tác giả đã đọc lại TOÀN VĂN bản thảo",
        "PASS" if read_ok else "REVIEW",
        f"manuscript_reviewed_confirmed={read_ok}",
        "Đọc lại toàn văn (đặc biệt Methods §7 đạo đức và Section III kết quả) rồi "
        "đặt manuscript_reviewed_confirmed=true. Bản nháp do công cụ sinh KHÔNG được "
        "gửi đi khi chưa có người đọc lại.",
    ))

    role = str(g7.get("reviewed_by_role") or "").strip().casefold()
    sign_ok = role in _REVIEW_ROLES and _valid_iso_time(g7.get("reviewed_at"))
    human.append(_criterion(
        "G7-HUMAN-05", "Có vai trò và thời điểm chốt bản thảo",
        "PASS" if sign_ok else "REVIEW",
        f"vai trò={role or 'thiếu'}; reviewed_at={g7.get('reviewed_at') or 'thiếu'}",
        "Ghi reviewed_by_role (PI/tác giả liên lạc) và reviewed_at dạng ISO-8601.",
    ))

    # ── Kết luận ─────────────────────────────────────────────────────────────
    auto_blocked = any(r["status"] == "BLOCK" for r in automatic)
    auto_review = any(r["status"] == "REVIEW" for r in automatic)
    human_complete = all(r["status"] == "PASS" for r in human)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review or not human_complete:
        status = STATUS_DRAFT_READY
    else:
        status = STATUS_CONFIRMED

    pending = [r["action"] for r in automatic + human
               if r["status"] != "PASS" and r.get("action")]

    manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        p = Path(path)
        if p.exists():
            manifest[key] = {"path": str(p),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "placeholder_counts": ph,
        "unsupported_claims": claims,
        "artifact_manifest": manifest,
        "standards_basis": list(_STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G7_CONFIRMED KHÔNG có nghĩa bản thảo tốt, đúng khoa học hay đáng "
            "đăng. Nó chỉ xác nhận: không còn ô trống bắt buộc, không còn khẳng định "
            "về việc chưa làm, trích dẫn đã qua A12, và tác giả thật đã đọc lại và "
            "chốt khai báo ICMJE. Thẩm định khoa học là việc của G8 (bình duyệt độc "
            "lập) và của người bình duyệt tạp chí."
        ),
    }

    if status == STATUS_DRAFT_READY:
        report["needs_input"] = GC.needs_input(
            GC.REASON_MISSING_DATA if ph["results"] else GC.REASON_MISSING_INTEGRITY,
            (f"Bản thảo còn {ph['results']} ô [CẦN KẾT QUẢ THẬT]"
             if ph["results"] else
             "Bản thảo đã đủ nội dung nhưng tác giả chưa chốt khai báo/đọc lại toàn văn")
            + " — chưa được coi là sẵn sàng cho G8.",
            "sửa exports/<study>/study_meta.json → gate_params.G7 rồi chạy: "
            "python tools/g7_quality_gate.py --study <study>",
            must_not_fabricate=["kết quả thống kê", "số IRB", "số đăng ký",
                                "danh sách tác giả"],
            study_meta_patch={"gate_params": {"G7": {"manuscript_reviewed_confirmed": True}}},
        )
    return report


# ════════════════════════════════════════════════════════════════════════════
# Báo cáo
# ════════════════════════════════════════════════════════════════════════════

def write_quality_report(study: str, out_dir: Path,
                         report: Mapping[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "G7_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def _rows(key: str) -> List[str]:
        return [
            f"| {r['id']} | {r['label']} | {r['status']} | "
            f"{str(r['evidence']).replace('|', '/')} |"
            for r in report.get(key, [])
        ]

    ph = report.get("placeholder_counts") or {}
    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G7 (BẢN THẢO) — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`  ·  "
        f"**Hợp đồng:** `{report.get('contract_version', '')}`",
        "",
        "> Báo cáo này chấm BẢN THẢO ĐANG CÓ TRÊN ĐĨA (kể cả phần bác sĩ đã viết tay),",
        "> không chấm bản do công cụ vừa sinh. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết",
        "> quả ĐÚNG khi chưa có kết quả phân tích thật.",
        "",
        f"**Ô còn trống:** {ph.get('total', '?')} ô `[CẦN…]` — trong đó "
        f"{ph.get('results', '?')} ô `[CẦN KẾT QUẢ THẬT]` "
        f"(Methods {ph.get('methods', '?')} · Results {ph.get('results_section', '?')})",
        "",
        "## Kiểm tra tự động",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("automatic_criteria"),
        "",
        "## Xác nhận người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("human_criteria"),
    ]

    claims = report.get("unsupported_claims") or []
    if claims:
        lines.extend(["", "## ⚠️ KHẲNG ĐỊNH CHƯA CÓ BẰNG CHỨNG (phải sửa trước khi nộp)"])
        lines.extend(f"- {c}" for c in claims)

    pending = report.get("pending_actions") or []
    if pending:
        lines.extend(["", "## Việc còn lại trước khi được ghi PASS_G7_CONFIRMED"])
        lines.extend(f"{i}. {a}" for i, a in enumerate(pending, 1))

    manifest = report.get("artifact_manifest") or {}
    if manifest:
        lines.extend(["", "## Manifest artifact",
                      "| Artifact | Đường dẫn | SHA-256 |", "|---|---|---|"])
        for key, item in manifest.items():
            lines.append(f"| {key} | {str(item['path']).replace('|', '/')} | "
                         f"`{item['sha256']}` |")

    lines.extend(["", "## Nền chuẩn", "| Chuẩn | Phạm vi | Nguồn |", "|---|---|---|"])
    for item in report.get("standards_basis", []):
        lines.append(f"| {item['standard']} | {item['scope']} | {item.get('url', '')} |")

    lines.extend(["", "## Giới hạn phán định",
                  str(report.get("scope_statement") or ""),
                  "", "> Cần bác sĩ kiểm chứng."])

    md_path = out_dir / "G7_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def evaluate_study(study: str, out_dir: Path, *, write: bool = True) -> Dict[str, Any]:
    """Chấm lại G7 từ các file đã có — KHÔNG sinh lại bản thảo.

    Quan trọng: đọc artifact A8 TỪ ĐĨA, nên nếu bác sĩ đã viết tay vào đó, báo cáo
    này phản ánh đúng bản hiện tại chứ không phải bản khung ban đầu.
    """
    out_dir = Path(out_dir)
    checkpoints = {g: _read_json(out_dir / f"{g}_checkpoint.json")
                   for g in ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7")}
    meta = _read_json(out_dir / "study_meta.json")

    md_path = out_dir / f"G7_A8_MANUSCRIPT_{study}.md"
    if not md_path.exists():
        found = sorted(out_dir.glob("G7_A8_MANUSCRIPT_*.md"))
        md_path = found[0] if found else md_path
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        text = ""

    a12 = out_dir / f"A12_CITATION_VERIFICATION_{study}.md"
    if a12.exists():
        try:
            a12_text = a12.read_text(encoding="utf-8")
        except OSError:
            a12_text = ""
        citation_ok = bool(a12_text.strip()) and "KHÔNG XÁC MINH ĐƯỢC" not in a12_text.upper()
    else:
        citation_ok = None

    # SỬA 2026-07-30 (audit toàn diện G0-G10, G7-F1 — HIGH, FABRICATION_RISK):
    # trước đây KHÔNG truyền guardrail_passed ở đây → evaluate_g7_quality() rơi
    # vào nhánh mặc định đọc guardrail ĐÃ CACHE từ checkpoint (giá trị ghi MỘT
    # LẦN lúc run_g7_auto.py sinh khung ban đầu). Module này tự giới thiệu là
    # chấm bản thảo TỪ ĐĨA — "kể cả phần bác sĩ đã viết tay" — nhưng nếu bác sĩ
    # (hoặc agent) chèn PII/số liệu bịa (HR/CI/p không kèm nhãn [CẦN...]) thẳng
    # vào bản thảo SAU khi checkpoint đã ghi "PASS", G7-AUTO-00 vẫn báo PASS vì
    # chưa từng soi lại text hiện tại — mâu thuẫn trực tiếp với vai trò "lớp
    # phòng thủ cuối cùng trước khi bản thảo rời hệ thống". Vá: chạy lại
    # guardrail_g7() (run_g7_auto.py) TRÊN CHÍNH `text` vừa đọc, không tin cache.
    # Import lười tránh vòng import (run_g7_auto.py đã `import g7_quality_gate
    # as G7Q` ở cấp module).
    try:
        import run_g7_auto as G7  # noqa: PLC0415

        # KHÔNG đặc cách text rỗng — guardrail_g7("") tự nhiên trả lỗi thật
        # (thiếu nhãn DRAFT, thiếu disclaimer...) nên không cần ép PASS/BLOCK
        # riêng cho trường hợp thiếu bản thảo.
        fresh_errors, _fresh_warnings = G7.guardrail_g7(text)
        guardrail_passed = not fresh_errors
    except ImportError:  # pragma: no cover - lưới an toàn
        guardrail_passed = None

    report = evaluate_g7_quality(
        manuscript_text=text,
        checkpoints=checkpoints,
        meta=meta,
        artifact_paths={"A8": md_path} if md_path.exists() else {},
        citation_verification_ok=citation_ok,
        guardrail_passed=guardrail_passed,
    )
    if write:
        write_quality_report(study, out_dir, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại cổng G7 từ bản thảo + checkpoint đã có (không sinh lại bản thảo)."
    )
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--exports-dir", default=None,
                        help="Thư mục gốc exports (mặc định: <repo>/exports)")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in, không ghi báo cáo")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    base = Path(args.exports_dir) if args.exports_dir else (
        Path(__file__).resolve().parent.parent / "exports")
    out_dir = base / args.study
    if not out_dir.exists():
        print(f"🚧 Không thấy thư mục đề tài: {out_dir}")
        return GC.EXIT_BLOCKED

    report = evaluate_study(args.study, out_dir, write=not args.no_write)

    print(f"\n{'='*68}")
    print(f"  CHẤT LƯỢNG G7 (BẢN THẢO) — {args.study}")
    print(f"{'='*68}")
    for row in report["automatic_criteria"] + report["human_criteria"]:
        icon = {"PASS": "✅", "REVIEW": "🟡", "BLOCK": "🔴"}.get(row["status"], "•")
        print(f"  {icon} {row['id']}  {row['label']}")
        print(f"       {row['evidence']}")
    ph = report["placeholder_counts"]
    print(f"\n  📝 Ô còn trống: {ph['total']} tổng · {ph['results']} [CẦN KẾT QUẢ THẬT]")
    if report["unsupported_claims"]:
        print("\n  ⚠️  KHẲNG ĐỊNH CHƯA CÓ BẰNG CHỨNG:")
        for c in report["unsupported_claims"]:
            print(f"     • {c}")
    print(f"\n  → Trạng thái: {report['status']}")
    if report["pending_actions"]:
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI ĐƯỢC GHI PASS_G7_CONFIRMED:")
        for i, action in enumerate(report["pending_actions"], 1):
            print(f"  {i}. {action}")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*68}\n")

    if report["status"] == STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    if report["status"] == STATUS_DRAFT_READY:
        return GC.EXIT_BLOCKED
    return GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
