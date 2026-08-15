#!/usr/bin/env python3
"""Hợp đồng chất lượng G4: khóa SAP (Statistical Analysis Plan).

Vì sao module này tồn tại
─────────────────────────
G4 đã là cổng KÝ THẬT (``_GATE_REQUIRED_STAKEHOLDERS["G4"] = ("STATISTICIAN",
"PI")``) và là 1 trong 5 cổng cứng của doctrine, nhưng — khác G0/G1/G2/G3/G5/
G7/G8/G9/G10 — CHƯA từng có lớp ``g4_quality_gate.py`` riêng. Lớp bảo vệ NỘI
DUNG hiện có nằm rải ở hai nơi, cả hai đều có lỗ hổng thật (xác nhận bằng đọc
mã nguồn, không suy đoán):

1. ``guardrail()`` trong ``run_g4_auto.py`` — 3/4 luật (R4/R6/R7) đếm đúng
   những chuỗi mà ``generate()`` LUÔN in cứng bất kể tham số đầu vào (≥2 lần
   "DRAFT"/"CHỜ KÝ", ≥5 lần "[CẦN...]", disclaimer cuối bài) — TAUTOLOGY, cùng
   lớp lỗi đã vá ở G3 (R3–R7) và G8 (R6). Luật R3 (thật) chỉ được gọi MỘT LẦN
   ngay sau ``generate()`` trong ``main()`` — không nơi nào khác (kể cả
   ``approve_gate.py``) gọi lại nó trên nội dung mà bác sĩ vừa chỉnh sửa.
2. ``_g4_sections_still_draft()`` trong ``approve_gate.py`` — chốt gác THẬT
   duy nhất ngay trước chữ ký — chỉ từ chối ký khi §1/§2/§5/§10 còn "[CẦN".
   Nó KHÔNG kiểm bất kỳ nội dung phương pháp luận nào mà
   ``thiet-ke-nghien-cuu.md`` đòi hỏi (EPV/VIF ở §5, phân loại MCAR/MAR/MNAR ở
   §6, đa so sánh khớp alpha ở §8): thay mỗi "[CẦN...]" bằng "OK" vẫn ký được.

Nghiêm trọng hơn cả hai điểm trên: **không có bước nào đối chiếu lại số liệu
đã ký (alpha/power/effect_val/effect_type/sd/hypothesis_type/margin/N hiển thị
trong SAP §12 + Lock Certificate) với ``G3_checkpoint.json`` TẠI THỜI ĐIỂM
CHẤM**. Chữ ký mật mã (evidence_hash) chỉ bảo vệ tính TOÀN VẸN của bất kỳ nội
dung nào đang có trong file — không bảo đảm nội dung đó có còn KHỚP với cỡ mẫu
thật hay không. Một SAP bị sửa tay các con số này, hoặc một SAP sinh ra TRƯỚC
khi G3 được chạy lại với tham số khác, vẫn ký sạch mà không ai biết.

Cuối cùng: tín hiệu "G4 đã khóa" mà ``skill_standards.real_world_signals()``,
``g7_quality_gate.py`` (G7-AUTO-06), ``list_studies.py`` đọc
(``g4_lock_date``/``g4_status``/``study_meta.sap_lock_date``) KHÔNG được
``approve_gate.py`` cập nhật khi ký thật — một G4 đã ký hợp lệ vẫn báo "chưa
khóa" ở các công cụ đó, còn một chuỗi "LOCKED" gõ tay lại đánh lừa được chúng
dù ``gate_contract.ledger_approved()`` (cổng thật) vẫn từ chối đúng.

Module này làm bốn việc trong tầm với, KHÔNG viết lại cơ chế mật mã đã đúng:

1. Kiểm NỘI DUNG mà guardrail cũ không kiểm được: đối chiếu số liệu ký với
   G3 hiện tại (đóng lỗ hổng nguy hiểm nhất), EPV/VIF ở §5, MCAR/MAR/MNAR ở
   §6, tiền định hóa subgroup ở §7 (chống HARKing — hiện KHÔNG nằm trong
   ``_g4_sections_still_draft()`` nên có thể ký dù còn placeholder), phần
   mềm+seed cụ thể ở §10 (bắt kiểu "thay [CẦN] bằng OK"), margin(Δ) có nguồn
   cho NI/equivalence, và kết cục chính §2 khớp câu hỏi nghiên cứu gốc (G0/G1).
2. Tái dùng ``_g4_sections_still_draft()`` (import lười) thay vì viết lại.
3. Đòi bằng chứng NGƯỜI THẬT ngoài chữ ký ledger: mức bảo đảm khóa
   (role/shared), reviewer_ref khác cổng khác, và 3 xác nhận mới trong
   ``gate_params.G4`` (EPV/VIF, cơ chế thiếu dữ liệu, subgroup tiền định +
   mốc thời gian trước khi dữ liệu khóa).
4. Đóng khoảng trống tín hiệu phân mảnh: ``refresh_checkpoint()`` ghi
   ``g4_lock_date`` từ TIMESTAMP LEDGER THẬT khi đã khóa — không tự bật cờ
   ``study_meta.sap_lock_date`` (giữ nguyên nguyên tắc "hệ không tự bật cờ
   người thật" — chỉ ghi vào ``pending_actions``).

Giới hạn đã biết (ghi rõ để không ai đọc nhầm)
─────────────────────────────────────────────
- ``PASS_G4_SAP_LOCKED`` chỉ xác nhận: (a) SAP không còn placeholder ở các
  mục bắt buộc, (b) số liệu ký khớp G3 hiện tại, (c) có phê duyệt ledger đúng
  vai trò thống kê/PI, (d) bác sĩ đã tự xác nhận 3 mục EPV/MCAR/subgroup.
  KHÔNG chứng minh nội dung phương pháp luận là ĐÚNG về mặt lâm sàng — việc đó
  vẫn thuộc thống kê viên/PI.
- Module này KHÔNG phải cổng chặn mới. Chốt fail-closed thật của G4 vẫn là
  ``gate_contract.ledger_approved("G4", ...)`` mà ``run_g5_auto.py``/
  ``run_g6_auto.py``/``run_stats_analysis.py`` gọi. ``approve_gate.py`` vẫn
  giữ nguyên ``_g4_sections_still_draft()`` làm chốt trước-ký duy nhất — module
  này CHỈ chấm lại và báo cáo, không thêm điều kiện chặn ký mới (nhất quán với
  cách G3/G8 đã chọn: lớp chất lượng không đổi hành vi exit-code của
  ``run_g4_auto.py``/``approve_gate.py`` đã có test khóa).
- Cùng giới hạn mật mã đã ghi ở ``gate_contract.py``/``g8_quality_gate.py``:
  HMAC là mật mã ĐỐI XỨNG nên máy xác minh buộc phải giữ khóa đã ký — khóa
  riêng theo vai trò chỉ chứng minh một FILE tồn tại trên cùng máy, không
  chứng minh người ký độc lập với chủ nhiệm đề tài.
"""

from __future__ import annotations

import argparse
import json
import re

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import gate_contract as GC
import skill_standards as S

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_NEEDS_HUMAN_CONTENT"
STATUS_READY = "READY_FOR_SIGNATURE"
STATUS_LOCKED = "PASS_G4_SAP_LOCKED"

QUALITY_CONTRACT_VERSION = "G4-2026.1"

REVIEWER_ROLE_GROUPS = ("STATISTICIAN", "PI")  # khớp _GATE_REQUIRED_STAKEHOLDERS["G4"]

# ĐỒNG BỘ TAY với run_g3_auto.py / run_g4_auto.py / g3_quality_gate.py —
# 4 bản độc lập, không cross-import CLI script khác để tránh side-effect (xem
# docstring run_g4_auto.py). Test hồi quy khóa cả 4 bản khớp nhau.
N_NOT_APPLICABLE_DESIGNS = frozenset({"sr_ma", "prediction", "qualitative"})

CANONICAL_DESIGNS = frozenset({
    "rct", "cohort", "cross_sectional", "diagnostic", "sr_ma",
    "case_control", "prediction", "qualitative",
})


def sap_artifact_name(study: str) -> str:
    """Tên artifact — HỢP ĐỒNG downstream (guardrail/approve_gate/G5/G6/G9 đều
    dùng đúng tên này), không được đổi."""
    return f"G4_A5_SAP_FINAL_{study}.md"


STANDARDS_BASIS: Sequence[Mapping[str, str]] = (
    {
        "standard": "ICH E9(R1) — Addendum on Estimands and Sensitivity Analysis",
        "scope": "Khớp quần thể phân tích/estimand giữa đề cương và SAP; kế hoạch xử lý intercurrent events",
        "url": "https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf",
    },
    {
        "standard": "Ogundimu EO et al. J Clin Epidemiol 2016;76:175-82 (PMID 26964707)",
        "scope": "Nguồn thật của ngưỡng EPV≥10 cho hồi quy logistic/Cox đa biến",
        "pmid": "26964707",
    },
    {
        "standard": "van Smeden M et al. BMC Med Res Methodol 2016;16:163 (PMID 27881078)",
        "scope": "Quy tắc EPV cố định được hỗ trợ YẾU — nên khai kèm cảnh báo, không coi là ngưỡng tuyệt đối",
        "pmid": "27881078",
    },
    {
        "standard": "van Buuren S, Groothuis-Oudshoorn K. J Stat Softw 2011;45(3) — mice",
        "scope": "Multiple Imputation dưới giả định MAR; phải khai rõ biến đưa vào mô hình imputation",
        "url": "https://www.jstatsoft.org/article/view/v045i03",
    },
    {
        "standard": "FDA (2016) / EMA (2005) — hướng dẫn biên non-inferiority — LƯU Ý MÂU THUẪN",
        "scope": (
            "FDA chấp nhận M2 = tỷ lệ % của M1; EMA nói rõ định nghĩa biên theo tỷ "
            "lệ hiệu ứng hoạt-chất-vs-giả-dược là KHÔNG phù hợp — margin cần biện "
            "minh lâm sàng + khung pháp lý cụ thể, không chỉ một con số"
        ),
        "url": "https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-choice-non-inferiority-margin_en.pdf",
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


def _gate_params(meta: Mapping[str, Any], gate: str) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get(gate)
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


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _section_body(text: str, section_num: str) -> str:
    """Thân nội dung của mục §N — giữa header §N và header §-kế-tiếp/"## PHẦN".

    Cùng kỹ thuật với ``approve_gate._g4_sections_still_draft`` (đã chạy đúng
    trong production): ranh giới từ (``\\b``) sau số chặn "§1" khớp nhầm "§12".
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^#{{2,3}}\s+{re.escape(section_num)}\b", line):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^#{2,3}\s+§\d", lines[j]) or re.match(r"^##\s+PHẦN", lines[j]):
            end = j
            break
    return "\n".join(lines[start:end])


def parse_signed_numbers(artifact_text: str) -> dict[str, Any]:
    """Đọc lại số liệu đã KÝ ở §12 (alpha/power/N/effect/hypothesis/margin/SD).

    §12 là nơi run_g4_auto.py::generate() in các số này bằng bullet markdown
    thuần (dễ regex, ổn định hơn khối box-drawing của Lock Certificate — cùng
    số liệu xuất hiện ở CẢ hai nơi trong cùng một lần sinh, nên lệch ở §12 đã
    đủ để gắn cờ cho người rà)."""
    section = _section_body(artifact_text, "§12")
    result: dict[str, Any] = {
        "found": bool(section), "alpha": None, "power_pct": None, "n": None,
        "effect_type": None, "effect_val": None, "hypothesis_type": None,
        "margin": None, "sd": None,
    }
    if not section:
        return result
    m = re.search(r"\*\*Alpha \([^)]*\):\*\*\s*([\d.]+)", section)
    if m:
        result["alpha"] = float(m.group(1))
    m = re.search(r"\*\*Power:\*\*\s*(\d+)%", section)
    if m:
        result["power_pct"] = int(m.group(1))
    m = re.search(r"\*\*Cỡ mẫu:\*\*\s*N\s*=\s*(\d+)", section)
    if m:
        result["n"] = int(m.group(1))
    m = re.search(r"\*\*Effect size dự kiến:\*\*\s*(\S+)\s*=\s*([\d.]+)", section)
    if m:
        result["effect_type"] = m.group(1)
        result["effect_val"] = float(m.group(2))
    m = re.search(r"\*\*Loại giả thuyết:\*\*\s*(\S+)", section)
    if m:
        result["hypothesis_type"] = m.group(1)
    m = re.search(r"\*\*Biên \(margin, Δ\):\*\*\s*([\d.]+)", section)
    if m:
        result["margin"] = float(m.group(1))
    m = re.search(r"\*\*Độ lệch chuẩn \(SD\) kết cục:\*\*\s*([\d.]+)", section)
    if m:
        result["sd"] = float(m.group(1))
    return result


def ledger_records(study: str, repo_root: Path) -> list[dict[str, Any]]:
    """Đọc sổ cái phê duyệt dạng thô — chỉ để ĐỐI CHIẾU, không để phán cổng
    (phán cổng luôn qua ``gate_contract.ledger_approved``)."""
    path = Path(repo_root) / "exports" / str(study) / "approval_ledger.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def _latest_approved(records: Sequence[Mapping[str, Any]], gate_id: str) -> Optional[Mapping[str, Any]]:
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
# Lõi đánh giá
# ════════════════════════════════════════════════════════════════════════════


def evaluate_g4_quality(
    *,
    study: str,
    checkpoint: Mapping[str, Any],
    artifact_text: str,
    g3_checkpoint: Mapping[str, Any],
    g1_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    ledger_signed: bool,
    ledger_reason: str,
    signature_scope: Optional[str],
    role_key_available: bool,
    cross_gate_refs: Mapping[str, str],
) -> dict[str, Any]:
    """Chấm G4 hai tầng: máy kiểm NỘI DUNG SAP, rồi bằng chứng ký người thật."""
    g4_meta = _gate_params(meta, "G4")
    design_code = str(checkpoint.get("design_code") or "")
    g3_design_code = str(g3_checkpoint.get("design_code") or "")
    g1_design_code = str((g1_checkpoint.get("design") or {}).get("internal_code") or "")

    automatic: list[dict[str, str]] = []
    approval: list[dict[str, str]] = []

    # ── G4-AUTO-00 — guardrail nền ─────────────────────────────────────────
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G4-F2/F3 — HIGH, phát hiện khi
    # rà lại F10-DESIGN-PROPOSAL): thiết kế gốc của tiêu chí này đọc thẳng
    # checkpoint["guardrail"] — giá trị ĐÓNG BĂNG tại thời điểm run_g4_auto.py
    # sinh artifact — với lý do "đã biết guardrail() tautology". Rà lại code
    # THẬT của guardrail() cho thấy R3 (chống tự công bố đã khóa/duyệt SAP)
    # đã được nâng cấp thành kiểm THEO DÒNG có phân biệt câu điều kiện/quy
    # trình — một luật THẬT SỰ có thể fail — nhưng guardrail() chỉ được
    # main() của run_g4_auto.py gọi ĐÚNG MỘT LẦN ngay sau khi sinh, không ai
    # gọi lại nó trên artifact_text SAU KHI bác sĩ đã chỉnh sửa. Vì
    # evaluate_g4_quality() ở đây ĐÃ nhận artifact_text tươi từ đĩa (tham số
    # hàm, không phải checkpoint cache), chạy lại guardrail() ngay tại đây để
    # bắt được tampering THẬT SỰ xảy ra sau khi sinh — cùng lớp sửa đã áp
    # dụng cho G7-AUTO-00/G8-AUTO-00 trong phiên audit này.
    try:
        import run_g4_auto as G4run  # noqa: PLC0415
        fresh_errors, _fresh_warnings = G4run.guardrail(artifact_text)
        guardrail_passed = not fresh_errors
    except ImportError:  # pragma: no cover - lưới an toàn nếu import thất bại
        guardrail_passed = S._guardrail_passed(dict(checkpoint))
    automatic.append(_criterion(
        "G4-AUTO-00",
        "Guardrail liêm chính G4 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed} (chấm lại trên artifact hiện tại, không tin cache)",
        "Sửa lỗi liêm chính (nguồn, PII, tự claim đã khóa) trước khi chấm chất lượng.",
    ))

    # ── G4-AUTO-01 — G4 không ở trạng thái DỪNG chờ G3 ─────────────────────
    blocked = GC.is_blocked(checkpoint)
    automatic.append(_criterion(
        "G4-AUTO-01",
        "G4 đã có cỡ mẫu hợp lệ từ G3 (không ở trạng thái BLOCKED)",
        "BLOCK" if blocked else "PASS",
        (GC.blocked_detail(checkpoint) or "checkpoint đang DỪNG") if blocked
        else f"g4_status={checkpoint.get('g4_status')!r}",
        "Cấp effect size cho G3 rồi chạy lại G3 → G4 trước khi chấm chất lượng SAP.",
    ))

    # ── G4-AUTO-02 — design_code nhất quán G1→G3→G4 ────────────────────────
    # G3↔G4 là BLOCK (công thức/quần thể phân tích trực tiếp phụ thuộc); G1↔G4
    # chỉ REVIEW vì resolve_design_code() (gate_contract.py) đã tự cảnh báo lệch
    # G1/G2 ở nơi khác — ở đây chỉ cần biết CÓ lệch, không cần xử lý trùng.
    if not g3_design_code or not design_code:
        design_status, design_evidence = "REVIEW", (
            f"thiếu design_code để đối chiếu (G3={g3_design_code!r}, G4={design_code!r})"
        )
    elif g3_design_code != design_code:
        design_status = "BLOCK"
        design_evidence = (
            f"LỆCH THIẾT KẾ: G3 tính cỡ mẫu theo '{g3_design_code}' nhưng SAP G4 "
            f"đang trình bày theo '{design_code}' — công thức/quần thể phân tích "
            "không khớp nhau"
        )
    elif g1_design_code and g1_design_code != design_code:
        design_status = "REVIEW"
        design_evidence = (
            f"G1 suy luận thiết kế '{g1_design_code}' nhưng G4 đang dùng '{design_code}' "
            "(có thể do bác sĩ đã đổi --design ở G2 — xem cảnh báo resolve_design_code)"
        )
    else:
        design_status = "PASS"
        design_evidence = f"design_code={design_code} khớp giữa G1/G3/G4"
    automatic.append(_criterion(
        "G4-AUTO-02",
        "design_code nhất quán giữa G1/G3 (cỡ mẫu) và G4 (SAP)",
        design_status,
        design_evidence,
        "Chạy lại đúng thứ tự G1 → G3 → G4 cho cùng một design_code; không trộn hai đề tài.",
    ))

    # ── G4-AUTO-03 [đóng F5] — số liệu đã ký khớp G3 HIỆN TẠI ──────────────
    parsed = parse_signed_numbers(artifact_text)
    if not parsed["found"]:
        num_status, num_evidence = "REVIEW", "không tìm thấy mục §12 trong artifact để đối chiếu"
    elif not g3_checkpoint:
        num_status, num_evidence = "REVIEW", "không có G3_checkpoint.json để đối chiếu"
    else:
        mismatches: list[str] = []
        g3_alpha = _as_float(g3_checkpoint.get("alpha"))
        if parsed["alpha"] is not None and g3_alpha is not None and abs(parsed["alpha"] - g3_alpha) > 0.001:
            mismatches.append(f"alpha ký={parsed['alpha']} ≠ G3 hiện tại={g3_alpha}")
        g3_power = _as_float(g3_checkpoint.get("power"))
        if parsed["power_pct"] is not None and g3_power is not None and parsed["power_pct"] != round(g3_power * 100):
            mismatches.append(f"power ký={parsed['power_pct']}% ≠ G3 hiện tại={round(g3_power * 100)}%")
        if design_code not in N_NOT_APPLICABLE_DESIGNS:
            # SỬA 2026-07-31: N hiệu lực của SAP là confirmed_n khi chủ nhiệm/Hội
            # đồng đã chốt N (thường lớn hơn N tối thiểu), ngược lại mới là
            # n_adjusted. Trước đây luôn so với n_adjusted cho các thiết kế này,
            # nên một SAP ghi ĐÚNG cỡ mẫu kế hoạch lại bị báo lệch — cùng gốc với
            # lỗi ở run_g4_auto.py, hai module phải đổi đồng thời.
            g3_confirmed = _as_int(g3_checkpoint.get("confirmed_n"))
            g3_n = g3_confirmed if g3_confirmed else _as_int(g3_checkpoint.get("n_adjusted"))
            _n_label = "confirmed_n" if g3_confirmed else "n_adjusted"
            if parsed["n"] is not None and g3_n is not None and parsed["n"] != g3_n:
                mismatches.append(f"N ký={parsed['n']} ≠ G3 hiện tại {_n_label}={g3_n}")
            g3_effect_val = _as_float(g3_checkpoint.get("effect_val"))
            g3_effect_type = str(g3_checkpoint.get("effect_type") or "")
            effect_val_drift = (
                parsed["effect_val"] is not None and g3_effect_val is not None
                and abs(parsed["effect_val"] - g3_effect_val) > 0.005
            )
            if effect_val_drift:
                mismatches.append(f"effect_val ký={parsed['effect_val']} ≠ G3 hiện tại={g3_effect_val}")
            if parsed["effect_type"] and g3_effect_type and parsed["effect_type"] != g3_effect_type:
                mismatches.append(f"effect_type ký={parsed['effect_type']} ≠ G3 hiện tại={g3_effect_type}")
        else:
            g3_confirmed_n = _as_int(g3_checkpoint.get("confirmed_n"))
            if parsed["n"] is not None and g3_confirmed_n is not None and parsed["n"] != g3_confirmed_n:
                mismatches.append(f"N ký={parsed['n']} ≠ G3 hiện tại confirmed_n={g3_confirmed_n}")
        g3_hyp = str(g3_checkpoint.get("hypothesis_type") or "superiority")
        if parsed["hypothesis_type"] and parsed["hypothesis_type"] != g3_hyp:
            mismatches.append(f"hypothesis_type ký={parsed['hypothesis_type']} ≠ G3 hiện tại={g3_hyp}")
        g3_margin = _as_float(g3_checkpoint.get("margin"))
        if parsed["margin"] is not None and g3_margin is not None and abs(parsed["margin"] - g3_margin) > 0.001:
            mismatches.append(f"margin ký={parsed['margin']} ≠ G3 hiện tại={g3_margin}")
        g3_sd = _as_float(g3_checkpoint.get("sd"))
        if parsed["sd"] is not None and g3_sd is not None and abs(parsed["sd"] - g3_sd) > 0.01:
            mismatches.append(f"SD ký={parsed['sd']} ≠ G3 hiện tại={g3_sd}")
        if mismatches:
            num_status, num_evidence = "BLOCK", "; ".join(mismatches)
        else:
            num_status, num_evidence = "PASS", "số liệu ký ở §12 khớp G3_checkpoint.json hiện tại"
    automatic.append(_criterion(
        "G4-AUTO-03",
        "Số liệu đã ký (§12) khớp G3_checkpoint.json HIỆN TẠI",
        num_status,
        num_evidence,
        "SAP bị sửa tay hoặc G3 đã chạy lại với tham số khác SAU khi sinh SAP — "
        "chạy lại run_g4_auto.py để sinh SAP mới khớp G3 hiện tại trước khi ký.",
    ))

    # ── G4-AUTO-04 — EPV/VIF ở §5 (thiết kế hồi quy đa biến) ───────────────
    if design_code == "qualitative":
        epv_status, epv_evidence = "PASS", "qualitative — §5 là CHIẾN LƯỢC MÃ HÓA, không áp dụng EPV/VIF"
    else:
        body5 = _section_body(artifact_text, "§5")
        has_epv_terms = bool(re.search(r"\b(EPV|EPP|pmsampsize|VIF)\b", body5, re.IGNORECASE))
        epv_status = "PASS" if has_epv_terms else "REVIEW"
        epv_evidence = (
            "§5 có nhắc EPV/EPP/pmsampsize/VIF" if has_epv_terms
            else "§5 chưa nhắc EPV/EPP/pmsampsize/VIF nào — mặc định template KHÔNG "
                 "chứa các từ này nên đây là tín hiệu thật, không phải đếm placeholder"
        )
    automatic.append(_criterion(
        "G4-AUTO-04",
        "§5 phân tích đa biến có nhắc EPV/EPP/pmsampsize/VIF khi áp dụng",
        epv_status,
        epv_evidence,
        "Ghi rõ EPV (Ogundimu 2016, PMID 26964707) hoặc VIF cho từng biến độc lập ở §5.",
    ))

    # ── G4-AUTO-05 — §6 dữ liệu thiếu đã điền (không chỉ đếm MCAR/MAR/MNAR) ─
    # LƯU Ý: template mặc định ĐÃ in sẵn "MAR (missing at random)" cho MỌI
    # thiết kế không-định-tính — đếm sự có mặt của từ MCAR/MAR/MNAR sẽ LUÔN
    # PASS kể cả trên bản DRAFT chưa ai đụng tới (đúng lớp lỗi tautology mà
    # audit tìm thấy ở G3/G8/chính G4 này). Tín hiệu THẬT là placeholder
    # "[CẦN BÁC SĨ ĐIỀN]" (biến đưa vào mô hình imputation) đã được thay chưa.
    if design_code == "qualitative":
        missing_status = "PASS"
        missing_evidence = "qualitative — §6 là BÃO HÒA DỮ LIỆU, không áp dụng cơ chế MCAR/MAR/MNAR"
    else:
        body6 = _section_body(artifact_text, "§6")
        if "[CẦN" in body6:
            missing_status = "REVIEW"
            missing_evidence = "§6 còn placeholder '[CẦN' (biến đưa vào mô hình imputation chưa điền)"
        elif not re.search(r"\b(MCAR|MAR|MNAR)\b", body6, re.IGNORECASE):
            missing_status = "REVIEW"
            missing_evidence = "§6 không còn nhắc cơ chế MCAR/MAR/MNAR nào (có thể đã bị xóa khi chỉnh sửa)"
        else:
            missing_status, missing_evidence = "PASS", "§6 đã điền biến imputation và còn nêu cơ chế dữ liệu thiếu"
    automatic.append(_criterion(
        "G4-AUTO-05",
        "§6 dữ liệu thiếu đã điền thật (không chỉ còn nhãn mặc định)",
        missing_status,
        missing_evidence,
        "Điền biến đưa vào mô hình MI ở §6; nếu cơ chế không phải MAR, đổi rõ giả định.",
    ))

    # ── G4-AUTO-06 — §8 đa so sánh, nhất quán số học nếu dùng Bonferroni ───
    body8 = _section_body(artifact_text, "§8")
    if "[CẦN" in body8:
        comparison_status, comparison_evidence = "REVIEW", "§8 còn placeholder '[CẦN' — chưa điền chiến lược đa so sánh"
    elif re.search(r"bonferroni", body8, re.IGNORECASE):
        count_m = re.search(r"(\d+)\s*(kết cục|so sánh|comparisons)", body8, re.IGNORECASE)
        # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology): trước
        # đây lấy SỐ 0.0x ĐẦU TIÊN xuất hiện trong §8 — nhưng câu diễn đạt tự
        # nhiên phổ biến nhất ("alpha gốc 0.05, alpha điều chỉnh = 0.0125")
        # có alpha GỐC (chưa điều chỉnh) đứng trước, nên regex bắt nhầm 0.05
        # thay vì 0.0125 dù toán học của bác sĩ hoàn toàn đúng — báo "không
        # khớp số học" oan. Xác nhận thực nghiệm: câu trên (Bonferroni 4 kết
        # cục, 0.05/4=0.0125 chính xác) bị regex cũ bắt "0.05" → so sánh với
        # expected=0.0125 → lệch 0.0375 > tolerance 0.005 → REVIEW sai. Ưu
        # tiên số có NHÃN "alpha điều chỉnh/hiệu chỉnh" đứng ngay trước; chỉ
        # rơi về số 0.0x đầu tiên khi không có nhãn (giữ nguyên hành vi cũ
        # cho trường hợp không nhãn — không làm yếu khả năng bắt lỗi thật).
        alpha_labeled_m = re.search(
            r"alpha\s*(?:điều chỉnh|hiệu chỉnh)[^0-9]{0,20}(0\.0\d+)", body8, re.IGNORECASE
        )
        alpha_m = alpha_labeled_m or re.search(r"(0\.0\d+)", body8)
        if count_m and alpha_m:
            n_comp = int(count_m.group(1))
            adj_alpha = float(alpha_m.group(1))
            g3_alpha = _as_float(g3_checkpoint.get("alpha")) or 0.05
            expected = g3_alpha / n_comp if n_comp else None
            if expected is not None and abs(expected - adj_alpha) > 0.005:
                comparison_status = "REVIEW"
                comparison_evidence = (
                    f"Bonferroni với {n_comp} so sánh nên alpha điều chỉnh ≈ {expected:.4f}, "
                    f"nhưng §8 ghi {adj_alpha} — không khớp số học"
                )
            else:
                comparison_status = "PASS"
                comparison_evidence = f"Bonferroni {n_comp} so sánh, alpha điều chỉnh {adj_alpha} khớp số học"
        else:
            comparison_status = "REVIEW"
            comparison_evidence = "nhắc Bonferroni nhưng không đọc được số so sánh + alpha điều chỉnh để kiểm số học"
    else:
        comparison_status, comparison_evidence = "PASS", "§8 đã điền (không dùng Bonferroni hoặc không cần hiệu chỉnh)"
    automatic.append(_criterion(
        "G4-AUTO-06",
        "§8 đa so sánh đã điền; nếu Bonferroni thì alpha điều chỉnh khớp số học",
        comparison_status,
        comparison_evidence,
        "Ghi rõ số kết cục chính + phương pháp hiệu chỉnh; nếu Bonferroni, alpha/n phải khớp §12.",
    ))

    # ── G4-AUTO-07 — §7 subgroup tiền định (chống HARKing) ─────────────────
    # KHÔNG nằm trong approve_gate._g4_sections_still_draft() (chỉ kiểm
    # §1/§2/§5/§10) — hiện SAP có thể ký dù §7 còn nguyên placeholder.
    body7 = _section_body(artifact_text, "§7")
    if "[CẦN" in body7:
        subgroup_status = "REVIEW"
        subgroup_evidence = "§7 (subgroup/chọn mẫu đa dạng) còn placeholder '[CẦN' — KHÔNG bị approve_gate chặn ký"
    else:
        subgroup_status, subgroup_evidence = "PASS", "§7 đã điền"
    automatic.append(_criterion(
        "G4-AUTO-07",
        "§7 phân tích nhóm nhỏ/chọn mẫu đã điền (chống HARKing)",
        subgroup_status,
        subgroup_evidence,
        "Điền §7 TRƯỚC khi ký — nhóm nhỏ phải được liệt kê tiền định, không phải sau khi xem dữ liệu.",
    ))

    # ── G4-AUTO-08 [đóng F4] — §10 phần mềm+seed CỤ THỂ, không phải "OK" ───
    body10 = _section_body(artifact_text, "§10")
    has_software = bool(re.search(r"[A-Za-z]+\s*v?\.?\s*\d+(\.\d+)?", body10))
    has_seed = bool(re.search(r"seed\D{0,20}(\d+)", body10, re.IGNORECASE))
    if "[CẦN" in body10:
        software_status, software_evidence = "REVIEW", "§10 còn placeholder '[CẦN' — chưa điền phần mềm/seed"
    elif not has_software or not has_seed:
        software_status = "REVIEW"
        software_evidence = (
            f"§10 đã xóa nhãn '[CẦN' nhưng thiếu {'tên+phiên bản phần mềm' if not has_software else ''}"
            f"{' và ' if not has_software and not has_seed else ''}{'seed dạng số nguyên' if not has_seed else ''} "
            "cụ thể — nghi thay placeholder bằng 'OK'"
        )
    else:
        software_status, software_evidence = "PASS", "§10 có tên+phiên bản phần mềm và seed số nguyên cụ thể"
    automatic.append(_criterion(
        "G4-AUTO-08",
        "§10 phần mềm+seed cụ thể (không phải placeholder bị thay bằng 'OK')",
        software_status,
        software_evidence,
        "Ghi tên+phiên bản phần mềm thật (vd 'R v4.3') và một seed số nguyên cụ thể (vd set.seed(2026)).",
    ))

    # ── G4-AUTO-09 — margin(Δ) cho NI/equivalence phải có nguồn ────────────
    hypothesis_type = str(g3_checkpoint.get("hypothesis_type") or "superiority")
    margin_val = g3_checkpoint.get("margin")
    if hypothesis_type == "superiority":
        margin_status, margin_evidence = "PASS", "hypothesis_type=superiority — không cần margin"
    elif margin_val is None:
        margin_status = "BLOCK"
        margin_evidence = (
            f"hypothesis_type={hypothesis_type} nhưng G3_checkpoint.margin rỗng — "
            "an toàn tối quan trọng cho NI/equivalence"
        )
    else:
        g3_meta = _gate_params(meta, "G3")
        has_justification = _present(g3_meta.get("margin_justification"))
        has_source = _present(g3_meta.get("margin_source"))
        if has_justification and has_source:
            margin_status = "PASS"
            margin_evidence = f"margin={margin_val}, có margin_source + margin_justification trong gate_params.G3"
        else:
            margin_status = "REVIEW"
            margin_evidence = (
                f"margin={margin_val} có giá trị nhưng thiếu margin_source/margin_justification "
                "trong gate_params.G3 — Hội đồng/thống kê viên phải xác nhận biện minh lâm sàng TRƯỚC KHI KÝ"
            )
    automatic.append(_criterion(
        "G4-AUTO-09",
        "Margin(Δ) cho NI/equivalence có giá trị và có nguồn biện minh",
        margin_status,
        margin_evidence,
        "Khai gate_params.G3.margin_source + margin_justification "
        "(FDA/EMA — hai khung có thể mâu thuẫn, xem STANDARDS_BASIS).",
    ))

    # ── G4-AUTO-10 — placeholder ở mục bắt buộc (tái dùng approve_gate) ────
    try:
        import approve_gate as AG  # noqa: PLC0415 — import lười, tránh vòng import khi approve_gate nạp module này
        still_draft = AG._g4_sections_still_draft(artifact_text)
    except ImportError:  # pragma: no cover - lưới an toàn
        still_draft = None
    if still_draft is None:
        placeholder_status = "REVIEW"
        placeholder_evidence = "không import được approve_gate._g4_sections_still_draft để kiểm"
    elif still_draft:
        placeholder_status = "REVIEW"
        placeholder_evidence = f"còn placeholder '[CẦN' ở: {', '.join(still_draft)}"
    else:
        placeholder_status, placeholder_evidence = "PASS", "không còn placeholder '[CẦN' ở §1/§2/§5/§10"
    automatic.append(_criterion(
        "G4-AUTO-10",
        "Không còn placeholder '[CẦN' ở mục bắt buộc (§1/§2/§5/§10)",
        placeholder_status,
        placeholder_evidence,
        "Điền đủ §1/§2/§5/§10 — approve_gate.py cũng từ chối ký khi còn placeholder ở đây.",
    ))

    # ── G4-AUTO-11 — kết cục chính §2 khớp câu hỏi nghiên cứu gốc ──────────
    g0_meta = _gate_params(meta, "G0")
    g1_meta = _gate_params(meta, "G1")
    declared_outcome = str(g0_meta.get("primary_outcome") or g1_meta.get("primary_outcome") or "").strip()
    body2 = _section_body(artifact_text, "§2")
    if not declared_outcome:
        outcome_status = "PASS"
        outcome_evidence = "chưa có gate_params.G0/G1.primary_outcome để đối chiếu (không phải lỗi)"
    elif "[CẦN" in body2:
        outcome_status = "PASS"
        outcome_evidence = "§2 còn placeholder — đã bị chặn riêng ở G4-AUTO-10, không kiểm trùng"
    elif declared_outcome.casefold() in body2.casefold():
        outcome_status, outcome_evidence = "PASS", f"kết cục chính §2 chứa {declared_outcome[:60]!r} đã chốt ở G0/G1"
    else:
        outcome_status = "REVIEW"
        outcome_evidence = (
            f"§2 KHÔNG chứa kết cục chính đã chốt {declared_outcome[:60]!r} ở G0/G1 — "
            "kiểm bằng containment đơn giản, không phải NLP chính xác; có thể là diễn đạt khác nghĩa giống nhau"
        )
    automatic.append(_criterion(
        "G4-AUTO-11",
        "Kết cục chính §2 khớp câu hỏi nghiên cứu đã chốt (G0/G1)",
        outcome_status,
        outcome_evidence,
        "Đối chiếu §2 với gate_params.G0.primary_outcome/G1.primary_outcome; đổi kết cục chính phải giải trình.",
    ))

    # ── Tầng BẰNG CHỨNG KÝ NGƯỜI THẬT ───────────────────────────────────────
    approval.append(_criterion(
        "G4-HUMAN-01",
        "Sổ cái có phê duyệt G4 hợp lệ đúng vai trò thống kê/PI",
        "PASS" if ledger_signed else "REVIEW",
        ledger_reason or f"ledger_approved={ledger_signed}",
        f"Thống kê viên/PI tự ký: approve_gate.py --gate G4 --reviewer-role {GC.required_reviewer_role_hint('G4')}",
    ))

    if signature_scope == "role":
        scope_status = "PASS"
        scope_evidence = (
            "ký bằng khóa RIÊNG của nhóm thống kê/PI (scope=role) — có dấu vết tách bạch "
            "vận hành, NHƯNG vẫn không chứng minh được người ký khác chủ nhiệm"
        )
    elif signature_scope == "shared":
        scope_status = "REVIEW"
        scope_evidence = (
            "ký bằng khóa CHUNG (scope=shared) — khóa này ký được MỌI vai trò, nên chữ "
            "ký không phân biệt được thống kê viên độc lập với chủ nhiệm tự ký"
        )
    else:
        scope_status = "REVIEW"
        scope_evidence = f"chưa xác định phạm vi khóa; khóa riêng nhóm thống kê/PI có sẵn={role_key_available}"
    approval.append(_criterion(
        "G4-HUMAN-02",
        "Mức bảo đảm của khóa ký được nêu đúng (không nói quá)",
        scope_status,
        scope_evidence,
        "Tạo khóa riêng: setup_gate_approval_key.py --role STATISTICIAN, và để thống kê viên giữ.",
    ))

    g4_ref = cross_gate_refs.get("G4", "")
    clashes = [
        gate for gate, ref in cross_gate_refs.items()
        if gate != "G4" and ref and g4_ref and ref == g4_ref
    ]
    if not g4_ref:
        ref_status, ref_evidence = "REVIEW", "chưa có bản ghi phê duyệt G4 để đối chiếu"
    elif clashes:
        ref_status = "REVIEW"
        ref_evidence = (
            f"reviewer_ref của G4 ({g4_ref!r}) TRÙNG với cổng {', '.join(sorted(clashes))} "
            "— cùng một người đang ký nhiều vai trò"
        )
    else:
        ref_status, ref_evidence = "PASS", f"reviewer_ref của G4 ({g4_ref!r}) khác mọi cổng còn lại"
    approval.append(_criterion(
        "G4-HUMAN-03",
        "Người ký G4 khác người ký các cổng khác (chỉ dấu độc lập)",
        ref_status,
        ref_evidence,
        "Cân nhắc để thống kê viên (không phải người đã ký G2/G8/G9) ký G4.",
    ))

    epv_confirmed = g4_meta.get("epv_vif_reviewed") is True
    approval.append(_criterion(
        "G4-HUMAN-04",
        "Bác sĩ/thống kê viên xác nhận đã rà EPV/VIF ở §5",
        "PASS" if epv_confirmed else "REVIEW",
        f"gate_params.G4.epv_vif_reviewed={g4_meta.get('epv_vif_reviewed')!r}",
        "Đặt gate_params.G4.epv_vif_reviewed=true trong study_meta.json sau khi rà §5.",
    ))

    missing_confirmed = g4_meta.get("missing_data_mechanism_confirmed") is True
    approval.append(_criterion(
        "G4-HUMAN-05",
        "Bác sĩ/thống kê viên xác nhận cơ chế dữ liệu thiếu ở §6",
        "PASS" if missing_confirmed else "REVIEW",
        f"gate_params.G4.missing_data_mechanism_confirmed={g4_meta.get('missing_data_mechanism_confirmed')!r}",
        "Đặt gate_params.G4.missing_data_mechanism_confirmed=true sau khi rà §6.",
    ))

    subgroup_confirmed = g4_meta.get("subgroup_multiplicity_predefined_confirmed") is True
    reviewed_at = str(g4_meta.get("reviewed_at") or "")
    data_lock_date = str(meta.get("data_lock_date") or "")
    harking_problem = None
    if _present(reviewed_at) and _present(data_lock_date) and reviewed_at[:10] > data_lock_date[:10]:
        harking_problem = (
            f"reviewed_at ({reviewed_at[:10]}) SAU data_lock_date ({data_lock_date[:10]}) — "
            "nghi xác nhận subgroup SAU khi đã thấy dữ liệu (HARKing)"
        )
    if not subgroup_confirmed:
        subgroup_human_status = "REVIEW"
        subgroup_human_evidence = "gate_params.G4.subgroup_multiplicity_predefined_confirmed chưa bật"
    elif harking_problem:
        subgroup_human_status, subgroup_human_evidence = "REVIEW", harking_problem
    else:
        subgroup_human_status = "PASS"
        subgroup_human_evidence = (
            "subgroup đã xác nhận tiền định, mốc thời gian hợp lý "
            "(hoặc chưa có data_lock_date để đối chiếu)"
        )
    approval.append(_criterion(
        "G4-HUMAN-06",
        "Subgroup/đa so sánh xác nhận TIỀN ĐỊNH trước khi khóa dữ liệu",
        subgroup_human_status,
        subgroup_human_evidence,
        "Đặt gate_params.G4.subgroup_multiplicity_predefined_confirmed=true TRƯỚC khi G5 khóa dữ liệu.",
    ))

    reviewed_by_role = str(g4_meta.get("reviewed_by_role") or "")
    role_ok = bool(reviewed_by_role) and GC.reviewer_role_satisfies_gate("G4", reviewed_by_role)
    approval.append(_criterion(
        "G4-HUMAN-07",
        "reviewed_by_role khớp vai trò bắt buộc của G4",
        "PASS" if role_ok else "REVIEW",
        f"gate_params.G4.reviewed_by_role={reviewed_by_role or '(rỗng)'!r}",
        f"Đặt gate_params.G4.reviewed_by_role đúng nhóm: {GC.required_reviewer_role_hint('G4')}.",
    ))

    # ── Tổng hợp ─────────────────────────────────────────────────────────
    # SỬA 2026-07-31 (audit tautology vòng 2, G4-AUTO-11 — reverse-tautology):
    # containment đơn giản (declared_outcome.casefold() in body2.casefold())
    # là NLP-brittle — cùng kết cục diễn đạt lại tự nhiên (không copy y
    # nguyên) vẫn bị REVIEW dù ý nghĩa lâm sàng giống hệt. Xác nhận thực
    # nghiệm: với SAP đã ký (ledger_signed=True) + mọi human attestation
    # True, chỉ đổi §2 từ copy-nguyên-văn sang diễn đạt tự nhiên tương đương
    # đã khiến report['status'] rơi từ LOCKED xuống DRAFT_NEEDS_HUMAN_CONTENT
    # — một SAP đã ký, đã người thật xác nhận, bị hạ cấp SAI chỉ vì cách
    # diễn đạt câu. TRƯỚC KHI ký, vẫn để G4-AUTO-11 tham gia auto_review bình
    # thường (nhắc bác sĩ đối chiếu, không hại gì vì chưa khóa) — chỉ loại
    # khỏi phép tính khi ledger_signed=True (SAU khi đã ký, không để heuristic
    # dễ vỡ này hạ cấp một quyết định người thật đã chốt). Dòng G4-AUTO-11
    # vẫn hiển thị REVIEW trong báo cáo để bác sĩ đọc, chỉ không gate status.
    _status_driving = [
        row for row in automatic
        if not (row["id"] == "G4-AUTO-11" and ledger_signed)
    ]
    auto_blocked = any(row["status"] == "BLOCK" for row in _status_driving)
    auto_review = any(row["status"] == "REVIEW" for row in _status_driving)
    human_complete = all(row["status"] == "PASS" for row in approval)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT
    elif human_complete:
        status = STATUS_LOCKED
    else:
        status = STATUS_READY

    pending = [
        row["action"] for row in automatic + approval
        if row["status"] != "PASS" and row.get("action")
    ]
    return {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G4",
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "sap_ready_for_signature": not auto_blocked and not auto_review,
        "human_confirmation_complete": human_complete,
        "signature_scope": signature_scope,
        "automatic_criteria": automatic,
        "approval_criteria": approval,
        "pending_actions": list(dict.fromkeys(pending)),
        "standards_basis": [dict(item) for item in STANDARDS_BASIS],
        "scope_statement": (
            "PASS_G4_SAP_LOCKED xác nhận: SAP không còn placeholder ở mục bắt buộc, "
            "số liệu ký khớp G3_checkpoint.json hiện tại, có phê duyệt ledger đúng vai "
            "trò thống kê/PI, và bác sĩ đã tự xác nhận EPV/VIF, cơ chế dữ liệu thiếu, "
            "subgroup tiền định. KHÔNG chứng minh nội dung phương pháp luận ĐÚNG về mặt "
            "lâm sàng, và (như G8) HMAC đối xứng nên không chứng minh người ký độc lập "
            "với chủ nhiệm đề tài. Cổng chặn thật của G4 vẫn là "
            "gate_contract.ledger_approved('G4', ...) mà G5/G6/run_stats_analysis.py gọi."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


# ════════════════════════════════════════════════════════════════════════════
# Xuất báo cáo, cập nhật checkpoint, CLI
# ════════════════════════════════════════════════════════════════════════════


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    out_dir = Path(out_dir)
    (out_dir / "G4_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G4 (KHÓA SAP) — {study}",
        "",
        f"**Trạng thái:** `{report.get('status')}`",
        f"**Phiên bản hợp đồng:** {report.get('contract_version')}",
        f"**Phạm vi khóa ký:** {report.get('signature_scope') or 'không xác định'}",
        "",
        "## Kiểm tự động (máy kiểm NỘI DUNG SAP)",
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
        "## Bằng chứng ký người thật",
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
        lines.append("- Không còn mục chờ trong hợp đồng G4.")
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
    md_path = out_dir / "G4_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def refresh_checkpoint(*, study: str, out_dir: Path, report: Mapping[str, Any],
                       quality_report_path: Path, ledger_lock_timestamp: Optional[str]) -> Path:
    """Gắn kết quả chất lượng vào G4_checkpoint, giữ nguyên khóa downstream.

    [ĐÓNG F6] Khi status==LOCKED, ghi ``g4_lock_date`` từ TIMESTAMP LEDGER THẬT
    (không phải giờ hệ thống lúc chấm) — đây là tín hiệu mà
    ``skill_standards.real_world_signals()``/``g7_quality_gate.py``/
    ``list_studies.py`` đọc, trước đây KHÔNG được ``approve_gate.py`` cập nhật.
    KHÔNG tự ghi ``study_meta.sap_lock_date`` — giữ nguyên nguyên tắc "hệ không
    tự bật cờ người thật", chỉ đề xuất trong pending_actions.
    """
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G4_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update({
        "study": study,
        "gate": "G4",
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_gate": dict(report),
    })
    if report.get("status") == STATUS_LOCKED and ledger_lock_timestamp:
        checkpoint["g4_lock_date"] = ledger_lock_timestamp
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
    """Chấm lại G4 từ artifact đã có; KHÔNG sinh lại SAP, KHÔNG ký thay ai."""
    out_dir = Path(out_dir)
    repo_root = Path(repo_root) if repo_root else out_dir.parent.parent
    checkpoint = _read_json(out_dir / "G4_checkpoint.json")
    artifact_path = out_dir / sap_artifact_name(study)

    ledger_signed = GC.ledger_approved("G4", study, artifact_path, repo_root=repo_root)
    try:
        ledger_reason = "" if ledger_signed else GC.gate_block_reason(
            "G4", study, artifact_path, repo_root=repo_root
        )
    except Exception:  # pragma: no cover
        ledger_reason = ""
    try:
        scope = GC.approving_signature_scope("G4", study, repo_root=repo_root)
    except Exception:  # pragma: no cover
        scope = None
    role_key = any(GC.per_role_key_available(group) for group in REVIEWER_ROLE_GROUPS)

    records = ledger_records(study, repo_root)
    cross_refs = {
        gate: _reviewer_ref(_latest_approved(records, gate))
        for gate in ("G2", "G4", "G5", "G8", "G9")
    }
    ledger_lock_timestamp = None
    latest_g4 = _latest_approved(records, "G4")
    if ledger_signed and latest_g4:
        ledger_lock_timestamp = str(latest_g4.get("timestamp_utc") or "") or None

    report = evaluate_g4_quality(
        study=study,
        checkpoint=checkpoint,
        artifact_text=_read_text(artifact_path),
        g3_checkpoint=_read_json(out_dir / "G3_checkpoint.json"),
        g1_checkpoint=_read_json(out_dir / "G1_checkpoint.json"),
        meta=GC.load_study_meta(out_dir),
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
            ledger_lock_timestamp=ledger_lock_timestamp,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại hợp đồng chất lượng G4; không sinh lại SAP, không ký thay ai."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
    repo_root = Path(__file__).resolve().parents[1]
    study = re.sub(r"[^\w\-]", "_", args.study.strip().replace(" ", "-"))
    out_dir = repo_root / "exports" / study
    report = evaluate_study(study, out_dir, repo_root=repo_root, write=True)
    print(f"G4 quality status: {report['status']}")
    print(f"Phạm vi khóa ký: {report.get('signature_scope') or 'không xác định'}")
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["status"] != "PASS":
            print(f"  {row['status']:6} {row['id']} — {row['label']}")
            print(f"         ↳ {row['evidence']}")
    print(f"Báo cáo: {out_dir / 'G4_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
