#!/usr/bin/env python3
"""Hợp đồng chất lượng cho cổng G0: CÂU HỎI NGHIÊN CỨU.

LÝ DO MODULE NÀY TỒN TẠI
------------------------
Trước 2026-07-28, G0 là cổng DUY NHẤT trong chuỗi G0–G10 không có hợp đồng chất
lượng riêng (G1 có ``g1_quality_gate.py``, G2 có ``g2_quality_gate.py``). Hệ quả
đo được, không phải suy đoán: chạy ``run_g0_auto.py`` trên một đề tài bất kỳ,
màn hình in **"✅ G0 HOÀN THÀNH"** và tiến trình thoát mã 0 — trong khi mọi ô
P/I/C/O của artifact A1 vẫn nguyên placeholder ``[CẦN BÁC SĨ XÁC NHẬN]``, chưa
có kết cục chính, chưa có giả thuyết, chưa ai đánh giá FINER. Nói cách khác: cổng
KHỞI ĐẦU của một nghiên cứu tuyên bố hoàn thành khi **câu hỏi nghiên cứu chưa
tồn tại**. Đây đúng là kiểu "thành công giả" mà chính docstring của run_g0_auto.py
đã cảnh báo ở một chỗ khác.

Hằng số ``GC.REASON_MISSING_PICO`` ("G0: PICO chưa được xác nhận") đã nằm sẵn
trong ``gate_contract.py`` từ đầu nhưng chưa từng có dòng code nào dùng — bằng
chứng cho thấy tình huống này đã được dự trù mà chưa bao giờ được thực thi.

BA TRẠNG THÁI (cùng ngữ nghĩa với G1/G2 để cả chuỗi đọc nhất quán)
-----------------------------------------------------------------
- ``BLOCKED``: lỗi kỹ thuật/liêm chính — không có bằng chứng thật, guardrail bẩn,
  artifact khuyết, hoặc checkpoint thiếu trường mà cổng sau phụ thuộc.
- ``DRAFT_READY_NEEDS_HUMAN_REVIEW``: phần máy làm được đã đạt; còn chờ bác sĩ
  chốt PICO, kết cục chính, giả thuyết, FINER. **Đây là trạng thái ĐÚNG của một
  lần chạy G0 tự động bình thường** — không phải lỗi.
- ``PASS_G0_CONFIRMED``: bác sĩ đã pin đủ quyết định vào
  ``study_meta.json → gate_params.G0``. Chỉ khi đó mới được nói G0 đã qua.

Nền doctrine: ``.claude/agents/cau-hoi-nghien-cuu.md`` — "Đạt G0 khi: 6 thành
phần hoàn chỉnh · kết cục chính DUY NHẤT đã định nghĩa đo được · FINER đánh giá
từng tiêu chí · thiết kế gợi ý có lý do · bác sĩ xác nhận PICO + kết cục".

GIỚI HẠN PHÁN ĐỊNH: module này KHÔNG thẩm định chất lượng khoa học của câu hỏi.
Nó chỉ kiểm rằng câu hỏi ĐÃ ĐƯỢC MỘT NGƯỜI THẬT VIẾT RA VÀ CHỐT, và rằng nền
bằng chứng máy dựng là thật. Một PICO đầy đủ vẫn có thể là một PICO tồi.

Chạy lại độc lập (sau khi bác sĩ điền study_meta.json, KHÔNG cần gọi lại PubMed):
    python tools/g0_quality_gate.py --study <MÃ-ĐỀ-TÀI>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402
import skill_standards as S  # noqa: E402

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G0_CONFIRMED"

QUALITY_CONTRACT_VERSION = "G0-2026.1"

# Các mục BẮT BUỘC phải hiện diện trong artifact A1 — ánh xạ 1-1 với 6 THÀNH PHẦN
# của doctrine cau-hoi-nghien-cuu.md. Thiếu mục nào = artifact chưa đủ khung để
# bác sĩ điền, nên chặn ở tầng AUTO (lỗi của hệ, không phải của bác sĩ).
REQUIRED_A1_SECTIONS: Sequence[str] = (
    "PICO / PECO",
    "KIỂM FINER",
    "GIẢ THUYẾT",
    "BẰNG CHỨNG HIỆN CÓ",
    "PHÂN TÍCH KHOẢNG TRỐNG",
    "THIẾT KẾ GỢI Ý",
    "TIÊU CHÍ QUA CỔNG G0",
)

# Trường checkpoint mà các cổng sau ĐỌC THẬT (đã grep run_g1..g10, list_studies,
# study_readiness, g1_quality_gate.collect_evidence_identifiers). Thiếu = lệch
# hợp đồng im lặng: cổng sau lùi về mặc định mà không báo gì.
REQUIRED_CHECKPOINT_KEYS: Sequence[str] = (
    "study", "gate", "topic", "base_query",
    "evidence_level", "research_gaps", "design_suggestion",
    "pubmed_results", "guardrail", "artifacts",
)
REQUIRED_PUBMED_KEYS: Sequence[str] = (
    "total_found", "n_pmids", "all_pmids", "n_sr", "n_rct",
    "n_guideline", "n_observational", "n_recent", "counts_are_real",
)

_QUESTION_TYPES = {
    "therapy", "diagnosis", "prognosis", "harm", "descriptive",
    "điều trị", "chẩn đoán", "tiên lượng", "tác hại", "mô tả",
}
_TEST_TYPES = {
    "superiority", "non_inferiority", "non-inferiority", "equivalence",
    "descriptive", "mô tả",
}
# Vai trò được phép chốt câu hỏi nghiên cứu ở G0. Cố ý KHÁC danh sách của G2
# (IRB) — G0 là quyết định khoa học của chủ nhiệm/nhà phương pháp, không phải
# quyết định đạo đức.
_REVIEW_ROLES = {
    "pi", "principal investigator", "research lead", "methodologist",
    "nhà phương pháp", "chủ nhiệm", "chủ nhiệm đề tài",
}

_PLACEHOLDER_MARKERS = (
    "[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "[TODO", "___",
    "SUY RA TỪ TOPIC", "XXX",
)

_STANDARDS_BASIS = (
    {
        "standard": "PICO framework",
        "scope": "Khung câu hỏi lâm sàng/nghiên cứu 4 thành phần",
        "pmid": "7582737",
    },
    {
        "standard": "FINER criteria (Hulley, Designing Clinical Research)",
        "scope": "Sàng lọc câu hỏi nghiên cứu: Feasible/Interesting/Novel/Ethical/Relevant",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "EQUATOR Network",
        "scope": "Bản đồ chuẩn báo cáo theo loại thiết kế (dùng cho chuẩn dự kiến ở G0)",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "ICMJE Recommendations",
        "scope": "Đăng ký nghiên cứu trước khi tuyển người tham gia đầu tiên",
        "url": "https://www.icmje.org/recommendations/",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════

def _present(value: Any) -> bool:
    """Giá trị có NỘI DUNG THẬT không (placeholder không tính là có)."""
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
        upper = text.upper()
        return not any(marker in upper for marker in _PLACEHOLDER_MARKERS)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _g0_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g0 = gp.get("G0")
    return g0 if isinstance(g0, Mapping) else {}


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
    return {
        "id": criterion_id, "label": label, "status": status,
        "evidence": evidence, "action": action,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _count_unique_primary_outcomes(value: Any) -> int:
    """Đếm số kết cục CHÍNH được khai — doctrine bắt buộc DUY NHẤT 1.

    Chấp nhận chuỗi (1 kết cục) hoặc list. Chuỗi có dấu phân tách kiểu liệt kê
    (";" hoặc " và " hoặc ",") KHÔNG bị coi là nhiều kết cục: nhiều kết cục hợp
    lệ được viết dưới dạng "tỷ lệ tử vong do mọi nguyên nhân, đo tại 30 ngày".
    Chỉ list mới coi là nhiều — nếu bác sĩ thật sự muốn khai 2 kết cục chính thì
    họ sẽ viết list, và đó chính là điều cần chặn.
    """
    if isinstance(value, (list, tuple, set)):
        return len([v for v in value if _present(v)])
    return 1 if _present(value) else 0


# ════════════════════════════════════════════════════════════════════════════
# Chuẩn báo cáo dự kiến từ gợi ý thiết kế của G0
# ════════════════════════════════════════════════════════════════════════════

# G0 chỉ GỢI Ý thiết kế (G1 mới quyết định). Bản đồ này chuyển gợi ý văn xuôi
# tiếng Việt của analyze_evidence_gaps() thành mã canonical để tra chuẩn báo cáo
# dự kiến — doctrine THÀNH PHẦN 5 yêu cầu nêu "Chuẩn báo cáo dự kiến", mà artifact
# A1 trước đây không có dòng nào.
_DESIGN_HINT_PATTERNS: Sequence[tuple[str, str]] = (
    (r"sr\s*/\s*meta|meta-?analysis|tổng quan hệ thống", "sr_ma"),
    (r"\brct\b|ngẫu nhiên có đối chứng|pragmatic trial", "rct"),
    (r"cohort|thuần tập", "cohort"),
    (r"bệnh[- ]chứng|case[- ]control", "case_control"),
    (r"cắt ngang|cross[- ]sectional", "cross_sectional"),
    (r"chẩn đoán|diagnostic|độ chính xác", "diagnostic"),
    (r"tiên lượng|prediction|mô hình dự báo", "prediction"),
    (r"định tính|qualitative", "qualitative"),
)


def infer_design_code_from_hint(design_hint: Optional[str]) -> Optional[str]:
    """Suy mã thiết kế canonical từ câu gợi ý của G0 (None nếu không chắc).

    Cố ý trả None thay vì đoán bừa: chọn sai mã thiết kế kéo theo chọn sai chuẩn
    báo cáo — đúng lỗi đã xảy ra thật ở G2→G3/G4/G6 (xem resolve_design_code).
    """
    text = str(design_hint or "").strip().lower()
    if not text:
        return None
    # RCT xuất hiện cùng "SR/Meta-analysis (tổng hợp RCT hiện có)" → SR thắng vì
    # mẫu SR được duyệt trước; thứ tự trong _DESIGN_HINT_PATTERNS là có chủ ý.
    for pattern, code in _DESIGN_HINT_PATTERNS:
        if re.search(pattern, text):
            return code
    return None


def expected_reporting_standard(design_hint: Optional[str]) -> Dict[str, str]:
    """Gói chuẩn báo cáo DỰ KIẾN cho gợi ý thiết kế của G0."""
    code = infer_design_code_from_hint(design_hint)
    if not code:
        return {
            "design_code": "",
            "primary": "[CẦN XÁC ĐỊNH Ở G1] — tra EQUATOR Network theo thiết kế thật",
            "protocol": "[CẦN XÁC ĐỊNH Ở G1]",
        }
    pack = S.reporting_standards_for(code)
    return {
        "design_code": code,
        "primary": pack.get("primary", ""),
        "protocol": pack.get("protocol", ""),
    }


# ════════════════════════════════════════════════════════════════════════════
# Đánh giá
# ════════════════════════════════════════════════════════════════════════════

def evaluate_g0_quality(
    *,
    checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    artifact_text: str = "",
    artifact_paths: Optional[Mapping[str, Path]] = None,
    guardrail_passed: Optional[bool] = None,
    registry_check: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Chấm G0 theo hai tầng: máy kiểm được vs người thật phải chốt."""
    artifact_paths = artifact_paths or {}
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []

    # ── Tầng AUTO ────────────────────────────────────────────────────────────
    guard = checkpoint.get("guardrail")
    if guardrail_passed is None:
        guardrail_passed = bool(
            isinstance(guard, Mapping) and guard.get("passed") is True
        )
    automatic.append(_criterion(
        "G0-AUTO-00", "Guardrail liêm chính G0 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa mọi lỗi R1–R7 (nguồn, PII, vượt cổng, disclaimer) rồi chạy lại G0.",
    ))

    topic = checkpoint.get("topic")
    automatic.append(_criterion(
        "G0-AUTO-01", "Đề tài có chủ đề thật (không rỗng/placeholder)",
        "PASS" if _present(topic) else "BLOCK",
        f"topic={str(topic or '')[:80]!r}",
        "Chạy lại với --topic mô tả đúng vấn đề nghiên cứu.",
    ))

    pubmed = checkpoint.get("pubmed_results")
    pubmed = pubmed if isinstance(pubmed, Mapping) else {}
    n_pmids = pubmed.get("n_pmids")
    n_pmids = int(n_pmids) if isinstance(n_pmids, int) else 0
    automatic.append(_criterion(
        "G0-AUTO-02", "Có bằng chứng THẬT làm nền (≥1 PMID từ PubMed)",
        "PASS" if n_pmids > 0 else "BLOCK",
        f"n_pmids={n_pmids}",
        'Chạy lại với --query-en "<từ khóa tiếng Anh>"; hệ KHÔNG bịa PMID.',
    ))

    # Số hit THẬT (esearch Count) vs số bài lấy về: nếu không phải số thật thì mọi
    # kết luận "khoảng trống" chỉ là ước lượng dưới — không được để nó lặng lẽ đi
    # tiếp dưới nhãn PASS.
    counts_are_real = pubmed.get("counts_are_real")
    unavailable = pubmed.get("counts_unavailable") or []
    automatic.append(_criterion(
        "G0-AUTO-03", "Số hit dùng để kết luận khoảng trống là SỐ THẬT",
        "PASS" if counts_are_real is True else "REVIEW",
        f"counts_are_real={counts_are_real}; nhánh không tra được={list(unavailable)}",
        "Chạy lại G0 khi mạng ổn định; đừng kết luận 'khoảng trống' trên số ước lượng dưới.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): write_checkpoint()
    # trong run_g0_auto.py in CỨNG đủ 19 khóa này (10 REQUIRED_CHECKPOINT_KEYS
    # + 9 REQUIRED_PUBMED_KEYS) VÔ ĐIỀU KIỆN cho MỌI checkpoint mới do pipeline
    # thật sinh (đã xác nhận thực nghiệm với 4 tổ hợp topic/results khác
    # nhau) — tiêu chí này KHÔNG BAO GIỜ tự phát hiện được nội dung THIẾU CHẤT
    # LƯỢNG cho một checkpoint MỚI. Nó vẫn có giá trị THẬT: bắt checkpoint CŨ/
    # hỏng/sửa tay/ghi bởi writer khác (đã xác nhận: checkpoint bị xoá tay 1
    # khóa → BLOCK đúng) — đây là kiểm SCHEMA/toàn vẹn, không phải thước đo
    # chất lượng câu hỏi nghiên cứu cho đề tài cụ thể (việc đó thuộc
    # G0-HUMAN-01..07, đọc study_meta.json).
    missing_cp = [k for k in REQUIRED_CHECKPOINT_KEYS if k not in checkpoint]
    missing_pm = [k for k in REQUIRED_PUBMED_KEYS if k not in pubmed]
    cp_problems = (
        [f"checkpoint thiếu: {', '.join(missing_cp)}"] if missing_cp else []
    ) + (
        [f"pubmed_results thiếu: {', '.join(missing_pm)}"] if missing_pm else []
    )
    automatic.append(_criterion(
        "G0-AUTO-04", "Checkpoint đủ trường hợp đồng cho cổng sau đọc",
        "BLOCK" if cp_problems else "PASS",
        "; ".join(cp_problems) if cp_problems else
        f"{len(REQUIRED_CHECKPOINT_KEYS)} khóa gốc + "
        f"{len(REQUIRED_PUBMED_KEYS)} khóa pubmed_results đầy đủ",
        "Chạy lại G0 bản hiện hành để ghi checkpoint đúng schema.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): 7 tiêu đề mục trong
    # REQUIRED_A1_SECTIONS là header markdown TĨNH được generate_a1_artifact()
    # in CỨNG VÔ ĐIỀU KIỆN — không phụ thuộc topic/gaps/results (đã xác nhận
    # thực nghiệm nhiều tổ hợp topic×results, không case nào thiếu mục). Tiêu
    # chí này chỉ có khả năng BLOCK thật khi artifact bị TRUNCATE/tampering
    # SAU khi file .md đã ghi ra đĩa (đã xác nhận: cắt tay 1 header → BLOCK
    # đúng) — không phải thước đo bác sĩ đã điền PICO/FINER/giả thuyết đủ nội
    # dung hay chưa (việc đó thuộc G0-HUMAN-01..07).
    missing_sections = [
        s for s in REQUIRED_A1_SECTIONS
        if s.casefold() not in (artifact_text or "").casefold()
    ]
    if not (artifact_text or "").strip():
        art_status, art_evidence = "BLOCK", "Không đọc được artifact A1"
    elif missing_sections:
        art_status = "BLOCK"
        art_evidence = f"A1 thiếu mục: {', '.join(missing_sections)}"
    else:
        art_status = "PASS"
        art_evidence = f"A1 có đủ {len(REQUIRED_A1_SECTIONS)} mục bắt buộc"
    automatic.append(_criterion(
        "G0-AUTO-05", "Artifact A1 có đủ 6 thành phần theo doctrine",
        art_status, art_evidence,
        "Sinh lại A1 bằng run_g0_auto.py bản hiện hành.",
    ))

    # Trùng lặp nghiên cứu: PubMed trả lời "đã CÔNG BỐ gì", không trả lời "đang có
    # ai LÀM chưa". Thiếu vế sau, bác sĩ có thể khởi động một đề tài trùng hoàn
    # toàn với thử nghiệm đang tuyển bệnh.
    if isinstance(registry_check, Mapping) and registry_check:
        checked = registry_check.get("checked") is True
        n_trials = registry_check.get("n_trials")
        n_trials = int(n_trials) if isinstance(n_trials, int) else 0
        n_recruiting = registry_check.get("n_recruiting")
        n_recruiting = int(n_recruiting) if isinstance(n_recruiting, int) else 0
        reg_status = "PASS" if checked else "REVIEW"
        reg_evidence = (
            f"ClinicalTrials.gov: {n_trials} hồ sơ khớp, "
            f"{n_recruiting} đang tuyển"
            if checked else
            f"chưa tra được ({registry_check.get('error') or 'không rõ lý do'})"
        )
    else:
        reg_status = "REVIEW"
        reg_evidence = "chưa tra đăng ký nghiên cứu"
    automatic.append(_criterion(
        "G0-AUTO-06", "Đã tra đăng ký nghiên cứu đang tiến hành (trùng lặp)",
        reg_status, reg_evidence,
        "Chạy lại G0 khi có mạng, hoặc tự tra ClinicalTrials.gov/WHO ICTRP "
        "trước khi khẳng định đề tài là mới.",
    ))

    # ── Tầng HUMAN — đọc study_meta.json → gate_params.G0 ─────────────────────
    g0 = _g0_meta(meta)

    pico_fields = {
        "population": g0.get("population"),
        "intervention": g0.get("intervention"),
        "comparison": g0.get("comparison"),
        "outcomes": g0.get("outcomes"),
    }
    pico_missing = [k for k, v in pico_fields.items() if not _present(v)]
    human.append(_criterion(
        "G0-HUMAN-01", "PICO/PECO đủ 4 thành phần do bác sĩ viết",
        "PASS" if not pico_missing else "REVIEW",
        f"thiếu: {', '.join(pico_missing)}" if pico_missing else "P/I/C/O đều có nội dung",
        "Điền gate_params.G0.population/intervention/comparison/outcomes "
        "trong study_meta.json (ghi 'không có nhóm so sánh — mô tả' nếu đúng vậy).",
    ))

    n_primary = _count_unique_primary_outcomes(g0.get("primary_outcome"))
    measure_ok = _present(g0.get("primary_outcome_measure"))
    timepoint_ok = _present(g0.get("primary_outcome_timepoint"))
    if n_primary == 1 and measure_ok and timepoint_ok:
        po_status = "PASS"
        po_evidence = "1 kết cục chính, có thang đo và thời điểm đo"
    elif n_primary > 1:
        po_status = "REVIEW"
        po_evidence = (
            f"khai {n_primary} kết cục CHÍNH — doctrine yêu cầu DUY NHẤT 1 "
            "(các kết cục còn lại chuyển sang outcomes phụ)"
        )
    else:
        po_status = "REVIEW"
        po_evidence = (
            f"primary_outcome={'có' if n_primary else 'thiếu'}; "
            f"thang đo={'có' if measure_ok else 'thiếu'}; "
            f"thời điểm đo={'có' if timepoint_ok else 'thiếu'}"
        )
    human.append(_criterion(
        "G0-HUMAN-02", "Kết cục CHÍNH duy nhất, đo được, có thời điểm",
        po_status, po_evidence,
        "Điền primary_outcome (1 kết cục) + primary_outcome_measure + "
        "primary_outcome_timepoint.",
    ))

    h0_ok = _present(g0.get("hypothesis_h0"))
    h1_ok = _present(g0.get("hypothesis_h1"))
    dir_ok = _present(g0.get("expected_direction"))
    test_type = str(g0.get("test_type") or "").strip().lower()
    test_ok = test_type in _TEST_TYPES
    # Nghiên cứu mô tả không cần H0/H1 — ép có giả thuyết ở đây sẽ đẩy bác sĩ
    # đến chỗ bịa một giả thuyết cho một đề tài mô tả thuần.
    descriptive = test_type in {"descriptive", "mô tả"}
    hypo_ok = test_ok and (descriptive or (h0_ok and h1_ok and dir_ok))
    human.append(_criterion(
        "G0-HUMAN-03", "Giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định",
        "PASS" if hypo_ok else "REVIEW",
        f"test_type={test_type or 'thiếu'}; H0={'có' if h0_ok else 'thiếu'}; "
        f"H1={'có' if h1_ok else 'thiếu'}; chiều={'có' if dir_ok else 'thiếu'}",
        "Điền test_type (superiority/non_inferiority/equivalence/descriptive); "
        "nếu không phải nghiên cứu mô tả thì điền cả hypothesis_h0/h1 và "
        "expected_direction.",
    ))

    qtype = str(g0.get("question_type") or "").strip().lower()
    human.append(_criterion(
        "G0-HUMAN-04", "Loại câu hỏi đã xác định",
        "PASS" if qtype in _QUESTION_TYPES else "REVIEW",
        f"question_type={qtype or 'thiếu'}",
        "Điền question_type: therapy/diagnosis/prognosis/harm/descriptive.",
    ))

    finer_keys = ("finer_feasible", "finer_interesting", "finer_novel",
                  "finer_ethical", "finer_relevant")
    finer_missing = [k for k in finer_keys if not _present(g0.get(k))]
    human.append(_criterion(
        "G0-HUMAN-05", "FINER đánh giá đủ từng tiêu chí (5/5)",
        "PASS" if not finer_missing else "REVIEW",
        f"thiếu: {', '.join(k.replace('finer_', '') for k in finer_missing)}"
        if finer_missing else "5/5 tiêu chí có kết luận",
        "Điền 5 khóa finer_* — F và E là hai tiêu chí máy KHÔNG thể tự đánh giá.",
    ))

    evidence_reviewed = g0.get("evidence_reviewed_confirmed") is True
    novelty_ok = _present(g0.get("novelty_justification"))
    human.append(_criterion(
        "G0-HUMAN-06", "Đã đọc lại bằng chứng G0 và biện minh tính mới",
        "PASS" if (evidence_reviewed and novelty_ok) else "REVIEW",
        f"evidence_reviewed_confirmed={evidence_reviewed}; "
        f"novelty_justification={'có' if novelty_ok else 'thiếu'}",
        "Đọc danh sách PMID ở §3 của A1, rồi đặt evidence_reviewed_confirmed=true "
        "và viết novelty_justification.",
    ))

    role = str(g0.get("reviewed_by_role") or "").strip().casefold()
    pico_confirmed = g0.get("pico_confirmed") is True
    sign_ok = pico_confirmed and role in _REVIEW_ROLES and _valid_iso_time(g0.get("reviewed_at"))
    human.append(_criterion(
        "G0-HUMAN-07", "Chủ nhiệm/nhà phương pháp chốt PICO (vai trò + thời điểm)",
        "PASS" if sign_ok else "REVIEW",
        f"pico_confirmed={pico_confirmed}; vai trò={role or 'thiếu'}; "
        f"reviewed_at={g0.get('reviewed_at') or 'thiếu'}",
        "Đặt pico_confirmed=true, reviewed_by_role (PI/chủ nhiệm/methodologist) "
        "và reviewed_at dạng ISO-8601. Không cần lưu danh tính.",
    ))

    # ── Kết luận ─────────────────────────────────────────────────────────────
    auto_blocked = any(row["status"] == "BLOCK" for row in automatic)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    human_complete = all(row["status"] == "PASS" for row in human)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review or not human_complete:
        status = STATUS_DRAFT_READY
    else:
        status = STATUS_CONFIRMED

    pending = [
        row["action"] for row in automatic + human
        if row["status"] != "PASS" and row.get("action")
    ]

    manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        p = Path(path)
        if p.exists():
            manifest[key] = {
                "path": str(p),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "artifact_manifest": manifest,
        "standards_basis": list(_STANDARDS_BASIS),
        "expected_reporting_standard": expected_reporting_standard(
            checkpoint.get("design_suggestion")
        ),
        "scope_statement": (
            "PASS_G0_CONFIRMED chỉ xác nhận rằng câu hỏi nghiên cứu ĐÃ ĐƯỢC MỘT "
            "NGƯỜI THẬT VIẾT RA VÀ CHỐT, và nền bằng chứng máy dựng là thật. "
            "KHÔNG thẩm định chất lượng khoa học của câu hỏi, không thay tổng quan "
            "y văn có hệ thống, không thay Hội đồng Đạo đức. Một PICO đầy đủ vẫn "
            "có thể là một PICO tồi."
        ),
    }

    # needs_input máy-đọc-được cho pipeline: chỉ khi phần máy đã sạch mà người
    # thật chưa chốt — đây là lần đầu REASON_MISSING_PICO được dùng thật.
    if status == STATUS_DRAFT_READY and not human_complete:
        report["needs_input"] = GC.needs_input(
            GC.REASON_MISSING_PICO,
            "G0 đã dựng xong NỀN BẰNG CHỨNG nhưng CÂU HỎI NGHIÊN CỨU chưa được "
            "bác sĩ chốt (PICO/kết cục chính/FINER còn trống). Hệ KHÔNG tự viết "
            "PICO thay bác sĩ.",
            "sửa exports/<study>/study_meta.json → gate_params.G0 rồi chạy: "
            "python tools/g0_quality_gate.py --study <study>",
            must_not_fabricate=["PICO", "primary_outcome", "FINER", "hypothesis"],
            study_meta_patch={"gate_params": {"G0": {"pico_confirmed": True}}},
        )
    return report


# ════════════════════════════════════════════════════════════════════════════
# Báo cáo
# ════════════════════════════════════════════════════════════════════════════

def write_quality_report(study: str, out_dir: Path,
                         report: Mapping[str, Any]) -> Path:
    """Ghi báo cáo G0 (JSON máy đọc + Markdown bác sĩ đọc)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "G0_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    def _rows(key: str) -> List[str]:
        out = []
        for row in report.get(key, []):
            out.append(
                f"| {row['id']} | {row['label']} | {row['status']} | "
                f"{str(row['evidence']).replace('|', '/')} |"
            )
        return out

    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G0 — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`  ·  "
        f"**Hợp đồng:** `{report.get('contract_version', '')}`",
        "",
        "> G0 = cổng CÂU HỎI NGHIÊN CỨU. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết quả",
        "> ĐÚNG của một lần chạy tự động — không phải lỗi. Chỉ `PASS_G0_CONFIRMED`",
        "> mới có nghĩa câu hỏi đã được người thật chốt.",
        "",
        "## Kiểm tra tự động (máy làm được)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("automatic_criteria"),
        "",
        "## Xác nhận người thật (bác sĩ phải chốt)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("human_criteria"),
    ]

    pending = report.get("pending_actions") or []
    if pending:
        lines.extend(["", "## Việc còn lại trước khi được ghi PASS_G0_CONFIRMED"])
        lines.extend(f"{i}. {a}" for i, a in enumerate(pending, 1))

    std = report.get("expected_reporting_standard") or {}
    if std:
        lines.extend([
            "",
            "## Chuẩn báo cáo DỰ KIẾN (G1 quyết định chính thức)",
            f"- Mã thiết kế suy từ gợi ý G0: `{std.get('design_code') or '[chưa suy được]'}`",
            f"- Chuẩn báo cáo: {std.get('primary', '')}",
            f"- Chuẩn đề cương: {std.get('protocol', '')}",
        ])

    manifest = report.get("artifact_manifest") or {}
    if manifest:
        lines.extend([
            "",
            "## Manifest artifact",
            "| Artifact | Đường dẫn | SHA-256 |",
            "|---|---|---|",
        ])
        for key, item in manifest.items():
            lines.append(
                f"| {key} | {str(item['path']).replace('|', '/')} | `{item['sha256']}` |"
            )

    lines.extend([
        "",
        "## Nền chuẩn",
        "| Chuẩn | Phạm vi | PMID/DOI/URL |",
        "|---|---|---|",
    ])
    for item in report.get("standards_basis", []):
        source = f"PMID:{item['pmid']}" if item.get("pmid") else ""
        if item.get("doi"):
            source = f"{source}; DOI:{item['doi']}".strip("; ")
        if item.get("url"):
            source = f"{source}; {item['url']}".strip("; ")
        lines.append(
            f"| {item['standard']} | {item['scope']} | {source.replace('|', '/')} |"
        )

    lines.extend([
        "",
        "## Giới hạn phán định",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])

    md_path = out_dir / "G0_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


def refresh_checkpoint(*, study: str, out_dir: Path,
                       report: Mapping[str, Any]) -> Path:
    """Đồng bộ G0_checkpoint.json['quality_gate'] khi chấm ĐỘC LẬP.

    SỬA 2026-07-30 (audit toàn diện G0-G10, G0-04 — MEDIUM): trước đây CHỈ
    run_g0_auto.py (một lượt CHẠY LẠI TOÀN BỘ, kể cả gọi lại PubMed tốn thời
    gian) mới ghi ``cp["quality_gate"]``. Doctrine + docstring module này đều
    hướng dẫn bác sĩ, sau khi điền study_meta.json, chạy ĐỘC LẬP
    ``python tools/g0_quality_gate.py --study <MÃ>`` để chấm lại "không cần
    gọi lại PubMed" — nhưng đường đó chỉ ghi G0_QUALITY_REPORT.json/.md, để
    checkpoint đứng yên ở giá trị CŨ. Bất kỳ công cụ nào đọc trực tiếp
    checkpoint (đài kiểm soát, study_readiness.py) sẽ thấy dữ liệu lỗi thời.
    """
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G0_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint["quality_gate"] = {
        "status": report["status"],
        "contract_version": report.get("contract_version"),
        "automated_checks_passed": report.get("automated_checks_passed"),
        "human_confirmation_complete": report.get("human_confirmation_complete"),
        "pending_actions": report.get("pending_actions", []),
    }
    # Không để needs_input (PICO chưa chốt) ghi đè needs_input NẶNG HƠN đã có
    # (0 PMID) — mirror đúng guard `if not blocked and ...` của run_g0_auto.py.
    existing = checkpoint.get("needs_input")
    existing = existing if isinstance(existing, dict) else {}
    existing_reason = existing.get("reason_code")
    already_blocked_on_pubmed = existing_reason == GC.REASON_MISSING_PUBMED
    if report.get("needs_input") and not already_blocked_on_pubmed:
        checkpoint["needs_input"] = report["needs_input"]
    elif (report.get("status") == STATUS_CONFIRMED and existing.get("blocked")
          and existing_reason == GC.REASON_MISSING_PICO):
        # SỬA 02/09/2026 (kiểm chi tiết 5 trục, lần chạy đầu trên C1a): bác sĩ đã chốt
        # PICO — hợp đồng trả PASS_G0_CONFIRMED — nhưng cờ chặn MISSING_PICO từ lượt chạy
        # đầu vẫn nằm lại trong checkpoint ⇒ GC.is_blocked() vẫn True, đài kiểm soát
        # (audit_research_gates) vẫn đòi "chốt PICO" và study_readiness/kiểm chi tiết nói
        # ngược nhau về CÙNG một cổng. Hai lớp kể hai chuyện. Giữ bản ghi để truy vết,
        # chỉ gỡ cờ chặn và ghi rõ ai/khi nào gỡ. Cờ MISSING_PUBMED KHÔNG gỡ ở đây —
        # 0 PMID không thể được "xác nhận" qua.
        checkpoint["needs_input"] = {
            **existing, "blocked": False,
            "resolved_by": "g0_quality_gate.refresh_checkpoint",
            "resolved_at": datetime.now().isoformat(timespec="seconds"),
        }
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return checkpoint_path


def evaluate_study(study: str, out_dir: Path, *, write: bool = True) -> Dict[str, Any]:
    """Chấm lại G0 từ các file đã có — KHÔNG gọi lại PubMed.

    Đây là đường bác sĩ dùng sau khi điền study_meta.json: không phải chờ 30 giây
    tìm kiếm lại chỉ để biết mình đã điền đủ chưa.
    """
    out_dir = Path(out_dir)
    checkpoint = _read_json(out_dir / "G0_checkpoint.json")
    meta = _read_json(out_dir / "study_meta.json")

    artifact_path = out_dir / f"G0_A1_PICO_FINER_{study}.md"
    if not artifact_path.exists():
        found = sorted(out_dir.glob("G0_A1_PICO_FINER_*.md"))
        artifact_path = found[0] if found else artifact_path
    try:
        artifact_text = artifact_path.read_text(encoding="utf-8")
    except OSError:
        artifact_text = ""

    report = evaluate_g0_quality(
        checkpoint=checkpoint,
        meta=meta,
        artifact_text=artifact_text,
        artifact_paths={"A1": artifact_path} if artifact_path.exists() else {},
        registry_check=checkpoint.get("registry_check"),
    )
    if write:
        write_quality_report(study, out_dir, report)
        refresh_checkpoint(study=study, out_dir=out_dir, report=report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại cổng G0 từ artifact + study_meta đã có (không gọi PubMed)."
    )
    parser.add_argument("--study", required=True, help="Mã đề tài (tên thư mục exports/<study>)")
    parser.add_argument("--exports-dir", default="exports", help="Thư mục gốc exports")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in, không ghi báo cáo")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    out_dir = Path(args.exports_dir) / args.study
    if not out_dir.exists():
        print(f"🚧 Không thấy thư mục đề tài: {out_dir}")
        return GC.EXIT_BLOCKED

    report = evaluate_study(args.study, out_dir, write=not args.no_write)

    print(f"\n{'='*65}")
    print(f"  CHẤT LƯỢNG G0 — {args.study}")
    print(f"{'='*65}")
    for row in report["automatic_criteria"] + report["human_criteria"]:
        icon = {"PASS": "✅", "REVIEW": "🟡", "BLOCK": "🔴"}.get(row["status"], "•")
        print(f"  {icon} {row['id']}  {row['label']}")
        print(f"       {row['evidence']}")
    print(f"\n  → Trạng thái: {report['status']}")
    if report["pending_actions"]:
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI ĐƯỢC GHI PASS_G0_CONFIRMED:")
        for i, action in enumerate(report["pending_actions"], 1):
            print(f"  {i}. {action}")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")

    if report["status"] == STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    if report["status"] == STATUS_DRAFT_READY:
        return GC.EXIT_BLOCKED
    return GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
