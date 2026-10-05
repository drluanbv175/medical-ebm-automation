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
2. ``_g4_sections_still_draft()`` trong ``approve_gate.py`` — chốt gác ngay
   trước chữ ký — từ chối ký khi mục bắt buộc §1/§2/§4/§5/§9/§10 (RCT thêm
   §13/§14/§15) còn ô trống HOẶC vắng hẳn (§4/§9, §13–§15 RCT và luật «vắng ⇒
   chặn» thêm 04/10/2026). Riêng nó KHÔNG kiểm nội dung phương pháp luận mà
   ``thiet-ke-nghien-cuu.md`` đòi hỏi (EPV/VIF ở §5, phân loại MCAR/MAR/MNAR ở
   §6, đa so sánh khớp alpha ở §8): thay mỗi "[CẦN...]" bằng "OK" vẫn lọt — vì
   vậy approve_gate gọi THÊM module này trước khi ký (xem «Giới hạn đã biết»).

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
- Chốt fail-closed của G4 phía tầng sau là ``gate_contract.ledger_approved
  ("G4", ...)`` mà ``run_g5_auto.py``/``run_g6_auto.py``/``run_stats_analysis.py``
  gọi. TỪ 24/08/2026 module này CŨNG là điều kiện chặn ký: ``approve_gate.py``
  gọi ``evaluate_study(write=False)`` TRƯỚC khi ghi sổ cái và từ chối khi
  BLOCKED/DRAFT; từ 04/10/2026 còn từ chối khi tiêu chí người kiểm được trước
  lúc ký (G4-HUMAN-04…08) chưa đạt và khi ký SAU ngày khoá dữ liệu mà không
  khai «SAP AMENDMENT». (Câu cũ «không thêm điều kiện chặn ký mới» đã sai từ
  24/08 — VÁ 04/10/2026, soát từng cổng G4-11.)
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
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import cong_song as CS
import gate_contract as GC
import pipeline_freshness as PF
import placeholder_contract as PC
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
# Mục SAP thành bắt buộc từ 04/10/2026 (soát từng cổng) — SAP đã ký trước mốc đó không bị hạ cấp vì các mục này:
# §4/§9 (mọi thiết kế) và §13/§14/§15 (RCT — QĐ-1, G4-02).
_G4_MUC_BAT_BUOC_TU_20261004 = frozenset({"§4", "§9", "§13", "§14", "§15"})

# VÁ 04/10/2026 (soát từng cổng, G4-03/G1-08): 5 thuộc tính estimand ICH E9(R1) — CÙNG tên khoá với
# gate_params.G1.estimand (gate_contract._GATE_PARAMS_SKELETON) và g1_quality_gate._estimand_complete.
KHOA_ESTIMAND = ("population", "treatment_condition", "variable", "intercurrent_events_strategy",
                 "population_summary_measure")

# Nhãn dòng trong SAP (run_g4_auto.generate in đúng các nhãn này) — bộ đọc §12/§1/PHẦN 5 dựa vào chúng.
NHAN_LOAI_THIEU_LUC = "THẤP HƠN N tối thiểu"
_RE_ISO_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}")

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
        # VÁ 04/10/2026 (G4-03): phạm vi này từng được TUYÊN BỐ mà không tiêu chí nào đọc estimand — nay G4-AUTO-15
        # đối chiếu 5 thuộc tính estimand khai ở G1 với §4 của SAP RCT.
        "scope": "Estimand (5 thuộc tính) khai ở G1 phải có mặt ở §4 SAP RCT (G4-AUTO-15); quần thể phân tích chính "
                 "khớp chiến lược biến cố xen ngang",
        "url": "https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf",
    },
    {
        "standard": "Kahan BC et al. The estimands framework: a primer on the ICH E9(R1) addendum. "
                    "BMJ 2024;384:e076316 (PMID 38262663)",
        "scope": "Cách khai estimand và liên hệ với quần thể phân tích/phân tích độ nhạy trong SAP",
        "pmid": "38262663",
    },
    {
        "standard": "Gamble C et al. Guidelines for the Content of Statistical Analysis Plans in Clinical Trials. "
                    "JAMA 2017;318(23):2337-43 (PMID 29260229)",
        "scope": "Tập mục tối thiểu của SAP — căn cứ cho mục bắt buộc §1/§2/§4/§5/§9/§10 (và §13–§15 với RCT)",
        "pmid": "29260229",
    },
    {
        "standard": "Moher D et al. CONSORT 2010 explanation and elaboration. BMJ 2010;340:c869 (PMID 20332511)",
        "scope": "RCT: không kiểm định ý nghĩa khác biệt đặc điểm nền giữa các nhóm đã ngẫu nhiên hoá — bảng 1 "
                 "của SAP RCT không có cột p",
        "pmid": "20332511",
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


def _gon_chu_tho(value: Any) -> str:
    """So khớp KHÔNG phụ thuộc dấu câu: NFC, chữ thường, bỏ dấu câu/ký tự khung, gọn khoảng trắng.

    VÁ 04/10/2026 (đo C1a): kết cục G1 «… (biến X, Phần 3 phiếu)» và §2 «… (biến X), Phần 3 phiếu» chỉ khác vị trí dấu
    ngoặc mà phép chứa chuỗi thô báo «không khớp» — báo động giả trên văn bản bác sĩ đã soạn."""
    text = unicodedata.normalize("NFC", str(value or "")).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def _ty_le_tu_chung(a: Any, b: Any) -> float:
    """Tỷ lệ TỪ (≥ 2 ký tự) của a có mặt trong b — đo «cùng nói một kết cục» khi người soạn diễn đạt lại (heuristic,
    không phải NLP; chỉ dùng cho tiêu chí REVIEW trước khi ký)."""
    tu_a = {t for t in _gon_chu_tho(a).split() if len(t) >= 2}
    tu_b = set(_gon_chu_tho(b).split())
    return len(tu_a & tu_b) / len(tu_a) if tu_a else 1.0


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


def _phan_body(text: str, so_phan: str) -> str:
    """Thân «## PHẦN <so_phan>» tới «## PHẦN» kế tiếp (hoặc hết tệp) — "" nếu không có."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^##\s+PHẦN\s+{re.escape(so_phan)}\b", line):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^##\s+PHẦN\b", lines[j]):
            end = j
            break
    return "\n".join(lines[start:end])


def _than_muc(text: str, section_num: str) -> str:
    """Nội dung §N KHÔNG kể dòng tiêu đề — rỗng nghĩa là mục chỉ còn tiêu đề (bị xoá thân) hoặc vắng hẳn."""
    body = _section_body(text, section_num)
    return "\n".join(body.splitlines()[1:]).strip() if body else ""


# Bộ đọc số liệu đã ký: (khoá, mẫu, kiểu). Nhãn khớp ĐÚNG dòng run_g4_auto.generate() in ở §12.
_MAU_SO_MUC12: tuple[tuple[str, str, Any], ...] = (
    ("alpha", r"\*\*Alpha \([^)]*\):\*\*\s*([\d.]+)", float),
    ("power_pct", r"\*\*Power:\*\*\s*(\d+)%", int),
    ("n", r"\*\*Cỡ mẫu:\*\*\s*N\s*=\s*(\d+)", int),
    ("hypothesis_type", r"\*\*Loại giả thuyết:\*\*\s*(\S+)", str),
    ("margin", r"\*\*Biên \(margin, Δ\):\*\*\s*([\d.]+)", float),
    ("sd", r"\*\*Độ lệch chuẩn \(SD\) kết cục:\*\*\s*([\d.]+)", float),
    # VÁ 04/10/2026 (soát từng cổng, G4-06/G4-08): tham số QUYẾT ĐỊNH N mà SAP ký từng không ghi (sai số d của thiết
    # kế theo độ chính xác, p0, bỏ cuộc, chiều kết cục NI, cụm, chẩn đoán, FPC) — nay in ở §12 và đối chiếu G3.
    ("precision", r"\*\*Sai số tuyệt đối cho phép \(d\):\*\*\s*±?\s*([\d.]+)", float),
    ("p_uoc_luong", r"\*\*Tỷ lệ ước lượng \(p\):\*\*\s*([\d.]+)", float),
    ("p0", r"\*\*Tỷ lệ biến cố nhóm chứng \(p0\):\*\*\s*([\d.]+)", float),
    ("p_event", r"\*\*Tỷ lệ biến cố \(log-rank, p_event\):\*\*\s*([\d.]+)", float),
    ("dropout", r"\*\*Tỷ lệ bỏ cuộc dự kiến:\*\*\s*([\d.]+)", float),
    ("outcome_direction", r"\*\*Chiều kết cục:\*\*\s*(higher_better|lower_better)", str),
    ("design_effect", r"\*\*Hiệu ứng thiết kế \(DE\):\*\*\s*([\d.]+)", float),
    ("icc", r"\*\*ICC:\*\*\s*([\d.]+)", float),
    ("cluster_size", r"\*\*Cỡ cụm trung bình \(m\):\*\*\s*([\d.]+)", float),
    ("n_clusters", r"\*\*Số cụm:\*\*\s*(\d+)", int),
    ("n_benh", r"\*\*Số ca bệnh cần:\*\*\s*(\d+)", int),
    ("n_khong_benh", r"\*\*Số ca không bệnh cần:\*\*\s*(\d+)", int),
    ("prevalence", r"\*\*Tỷ lệ hiện mắc dự kiến:\*\*\s*([\d.]+)", float),
    ("population_n", r"\*\*Quần thể hữu hạn \(FPC\):\*\*\s*N\s*=\s*(\d+)", int),
)


def parse_signed_numbers(artifact_text: str) -> dict[str, Any]:
    """Đọc lại số liệu đã KÝ: §12 (alpha/power/N/effect/giả thuyết/margin/SD + tham số quyết định N), cộng N ở §1 và ở
    chứng chỉ khoá PHẦN 5.

    VÁ 04/10/2026 (soát từng cổng, G4-08): bản cũ chỉ đọc §12 — «cùng số liệu xuất hiện ở CẢ hai nơi nên lệch ở §12
    đã đủ» — nhưng chứng chỉ khoá mới là VĂN BẢN ĐƯỢC KÝ, và đổi N ở §1/chứng chỉ thành 999 trong khi §12 bị xoá dòng
    thì mọi phép so đều «None ⇒ không lệch ⇒ PASS». Nay đọc cả ba nơi (`n_muc1`, `n_chung_chi`) để G4-AUTO-03 đối
    chiếu chéo; `alpha_khong_ap_dung`/`power_khong_ap_dung` = SAP khai tường minh «KHÔNG ÁP DỤNG» (không phải thiếu số).
    """
    section = _section_body(artifact_text, "§12")
    result: dict[str, Any] = {"found": bool(section), "effect_type": None, "effect_val": None,
                              "alpha_khong_ap_dung": False, "power_khong_ap_dung": False}
    result.update({khoa: None for khoa, _mau, _kieu in _MAU_SO_MUC12})
    if section:
        for khoa, mau, kieu in _MAU_SO_MUC12:
            m = re.search(mau, section)
            if m:
                result[khoa] = kieu(m.group(1))
        m = re.search(r"\*\*Effect size dự kiến:\*\*\s*(\S+)\s*=\s*([\d.]+)", section)
        if m:
            result["effect_type"] = m.group(1)
            result["effect_val"] = float(m.group(2))
        result["alpha_khong_ap_dung"] = bool(re.search(r"\*\*Alpha[^*\n]*:\*\*\s*KHÔNG ÁP DỤNG", section))
        result["power_khong_ap_dung"] = bool(re.search(r"\*\*Power:\*\*\s*KHÔNG ÁP DỤNG", section))
    m1 = re.search(r"\*\*Cỡ mẫu cuối:\*\*\s*N\s*=\s*(\d+)", _section_body(artifact_text, "§1"))
    result["n_muc1"] = int(m1.group(1)) if m1 else None
    m5 = re.search(r"Cỡ mẫu\s*:\s*N\s*=\s*(\d+)", _phan_body(artifact_text, "5"))
    result["n_chung_chi"] = int(m5.group(1)) if m5 else None
    return result


def loai_muc_12(design_code: Any, g3_checkpoint: Mapping[str, Any]) -> str:
    """Khung §12/chứng chỉ khoá theo CÁCH N được quyết định (bộ sinh run_g4_auto và bộ chấm dùng CHUNG hàm này).

    VÁ 04/10/2026 (soát từng cổng, G4-06 ≡ G3-08): bản cũ in «Alpha + Power 80%» cho MỌI thiết kế — kể cả định tính
    (mâu thuẫn ngay §8 «không kiểm định giả thuyết bằng p-value»), SR/MA, mô hình dự báo và cắt ngang tính theo độ
    chính xác (C1a: SAP ký «Power: 80%» trong khi N do sai số d quyết định).
      • "dinh_tinh"   — định tính: không alpha/power; N (nếu chốt) theo bão hoà dữ liệu.
      • "khong_power" — sr_ma/prediction: N theo phương pháp riêng (RIS/TSA, pmsampsize) — Power KHÔNG ÁP DỤNG cho
                         công thức của G3; alpha vẫn dùng cho khoảng tin cậy.
      • "chinh_xac"   — G3 tính theo độ chính xác (effect_type PREVALENCE): alpha → độ tin cậy, p ước lượng, sai số d.
      • "power"       — còn lại (so sánh/kiểm định): alpha, power, effect size (+ margin/SD/cụm/chẩn đoán)."""
    ma = str(design_code or "").strip().lower()
    if ma == "qualitative":
        return "dinh_tinh"
    if ma in N_NOT_APPLICABLE_DESIGNS:
        return "khong_power"
    if str((g3_checkpoint or {}).get("effect_type") or "").strip().upper() == "PREVALENCE":
        return "chinh_xac"
    return "power"


def dau_van_tay_g4(artifact_text: str) -> str:
    """Dấu 16 hex của NỘI DUNG PHƯƠNG PHÁP SAP (PHẦN 3 — §1…§12/§15) mà xác nhận G4 của người chứng cho.

    VÁ 04/10/2026 (soát từng cổng, CHUNG-C/QĐ-7): epv_vif_reviewed / missing_data_mechanism_confirmed /
    subgroup_multiplicity_predefined_confirmed từng là cờ True trơn — sửa §5/§6/§7 SAU khi xác nhận vẫn PASS. Nay
    G4-HUMAN-08 đòi gate_params.G4.dau_van_tay_chot = dấu này. Chỉ băm PHẦN 3 (không băm lịch sử phiên bản/chứng chỉ ký)
    để ghi tên người soạn hay ký tay chứng chỉ không làm mất hiệu lực xác nhận phương pháp. Khoảng trắng không tính
    (cong_song.dau_van_tay chuẩn hoá NFC + gọn khoảng trắng). SAP không có PHẦN 3 (sai khuôn) ⇒ băm toàn văn."""
    phan3 = _phan_body(artifact_text, "3")
    return CS.dau_van_tay(phan3 if phan3 else artifact_text)


def _dong_sua_doi_sap(artifact_text: str) -> list[str]:
    """Các DÒNG BẢNG ở PHẦN 4 (thay đổi sau khi khoá) có cột «Loại» là SAP AMENDMENT kèm mô tả — không tính câu quy tắc
    in sẵn («… phân loại TIỀN ĐỊNH / THĂM DÒ / SAP AMENDMENT»), vốn LUÔN có mặt (đếm chữ trên cả PHẦN 4 là
    tautology)."""
    ra = []
    for dong in _phan_body(artifact_text, "4").splitlines():
        if not dong.strip().startswith("|"):
            continue
        o = [c.strip() for c in dong.strip().strip("|").split("|")]
        if len(o) >= 3 and re.search(r"SAP\s+AMENDMENT", o[2], re.IGNORECASE) and o[1] and not PC.co_o_trong(o[1]):
            ra.append(dong.strip())
    return ra


def ky_sau_khoa_du_lieu(artifact_text: str, data_lock_date: Any, thoi_diem_ky: Any) -> Optional[str]:
    """Lý do (chuỗi) khi một lần KÝ G4 ở thời điểm `thoi_diem_ky` rơi SAU ngày khoá dữ liệu mà PHẦN 4 không có dòng
    «SAP AMENDMENT»; None nếu chưa khoá dữ liệu, ký trước khoá, hoặc đã khai sửa đổi.

    VÁ 04/10/2026 (soát từng cổng, G4-07): chốt HARKing cũ chỉ so `reviewed_at` TỰ KHAI với data_lock_date (bằng so
    chuỗi [:10] không kiểm dạng — «15/09/2026» luôn «nhỏ hơn» «2026-09-01» nên không bao giờ bật); một lần ký LẠI sau
    khi sửa SAP lúc đã khoá dữ liệu không bị gắn cờ. Ngày sai dạng ISO ⇒ trả lý do (không so được ≠ ổn)."""
    dld = str(data_lock_date or "").strip()
    if not dld:
        return None
    if not _RE_ISO_NGAY.match(dld):
        return (f"data_lock_date={dld!r} không đúng dạng ISO YYYY-MM-DD — không so được thời điểm ký với lúc khoá "
                "dữ liệu")
    tk = str(thoi_diem_ky or "").strip()
    if not tk:
        return None
    if not _RE_ISO_NGAY.match(tk):
        return f"thời điểm ký {tk!r} không đúng dạng ISO — không so được với ngày khoá dữ liệu"
    if tk[:10] <= dld[:10] or _dong_sua_doi_sap(artifact_text):
        return None
    return (f"ký G4 ngày {tk[:10]} SAU ngày khoá dữ liệu {dld[:10]} mà PHẦN 4 không có dòng «SAP AMENDMENT» kèm "
            "mô tả — "
            "nghi đổi SAP sau khi đã thấy dữ liệu (HARKing)")


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
    g3_song: Optional[Mapping[str, Any]] = None,
    ledger_lock_timestamp: Optional[str] = None,
    dac_ta: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Chấm G4 hai tầng: máy kiểm NỘI DUNG SAP, rồi bằng chứng ký người thật.

    g3_song: kết quả cong_song.trang_thai_song("G3") — G3 CHẤM SỐNG (evaluate_study truyền vào). VẮNG ⇒ G4-AUTO-12
      REVIEW «không đo được» (fail-closed: nơi gọi trực tiếp phải tự chấm G3 rồi truyền vào, không được ngầm «đạt»).
    ledger_lock_timestamp: timestamp_utc của bản ghi phê duyệt G4 mới nhất còn hợp lệ — so với data_lock_date (G4-07).
    dac_ta: skill_standards.dac_ta_thiet_ke(out_dir) — estimand G1 cho G4-AUTO-15; vắng thì đọc gate_params.G1."""
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

    # ── G4-AUTO-03 [đóng F5 + G4-06/G4-08] — số liệu đã ký khớp G3 HIỆN TẠI, ĐỦ số, nhất quán §1/§12/chứng chỉ ──
    # VÁ 04/10/2026 (soát từng cổng): (G4-08) thiếu số ở §12 từng là «None ⇒ không lệch ⇒ PASS» — xoá dòng Alpha/Power/
    # Cỡ mẫu rồi đổi N ở §1 và chứng chỉ thành 999 vẫn READY. Nay số BẮT BUỘC theo loại §12 vắng ⇒ REVIEW, và N ở §1/
    # §12/chứng chỉ phải khớp nhau và khớp G3 (lệch ⇒ BLOCK). (G4-06) thiết kế theo ĐỘ CHÍNH XÁC phải ký sai số d và p
    # ước lượng (không phải Power); SAP in «Power: x%» cho thiết kế không dùng power ⇒ REVIEW (khung sai).
    parsed = parse_signed_numbers(artifact_text)
    loai12 = loai_muc_12(design_code, g3_checkpoint)
    if not parsed["found"]:
        num_status, num_evidence = "REVIEW", "không tìm thấy mục §12 trong artifact để đối chiếu"
    elif not g3_checkpoint:
        num_status, num_evidence = "REVIEW", "không có G3_checkpoint.json để đối chiếu"
    else:
        mismatches: list[str] = []
        thieu: list[str] = []
        sai_khung: list[str] = []

        def _lech_so(nhan: str, ky: Any, g3_gt: Any, dung_sai: float) -> None:
            fk, fg = _as_float(ky), _as_float(g3_gt)
            if fk is not None and fg is not None and abs(fk - fg) > dung_sai:
                mismatches.append(f"{nhan} ký={ky} ≠ G3 hiện tại={g3_gt}")

        g3_alpha = _as_float(g3_checkpoint.get("alpha"))
        if loai12 == "dinh_tinh":
            if parsed["alpha"] is not None or parsed["power_pct"] is not None:
                sai_khung.append("SAP định tính in Alpha/Power số — định tính không kiểm định giả thuyết bằng p-value")
        elif parsed["alpha"] is None:
            thieu.append("Alpha")
        else:
            _lech_so("alpha", parsed["alpha"], g3_alpha, 0.001)

        g3_power = _as_float(g3_checkpoint.get("power"))
        if loai12 == "power":
            if parsed["power_pct"] is None:
                thieu.append("Power")
            elif g3_power is not None and parsed["power_pct"] != round(g3_power * 100):
                mismatches.append(f"power ký={parsed['power_pct']}% ≠ G3 hiện tại={round(g3_power * 100)}%")
        elif parsed["power_pct"] is not None:
            sai_khung.append(f"SAP in «Power: {parsed['power_pct']}%» cho thiết kế không tính N theo power "
                             f"(loại §12={loai12}) — khung ký sai, ghi tham số thật quyết định N")

        if loai12 == "chinh_xac":
            if parsed["precision"] is None:
                thieu.append("sai số tuyệt đối cho phép d")
            else:
                _lech_so("sai số d", parsed["precision"], g3_checkpoint.get("precision"), 1e-6)
            if parsed["p_uoc_luong"] is None:
                thieu.append("tỷ lệ ước lượng p")
            else:
                _lech_so("tỷ lệ ước lượng p", parsed["p_uoc_luong"], g3_checkpoint.get("effect_val"), 1e-6)

        # SỬA 2026-07-31: N hiệu lực của SAP là confirmed_n khi chủ nhiệm/Hội đồng đã chốt N, ngược lại mới là
        # n_adjusted (thiết kế không dùng power: chỉ confirmed_n).
        g3_confirmed = _as_int(g3_checkpoint.get("confirmed_n"))
        if design_code in N_NOT_APPLICABLE_DESIGNS:
            n_can, n_nhan = g3_confirmed, "confirmed_n"
        else:
            n_can = g3_confirmed if g3_confirmed else _as_int(g3_checkpoint.get("n_adjusted"))
            n_nhan = "confirmed_n" if g3_confirmed else "n_adjusted"
        if n_can:
            if parsed["n"] is None:
                thieu.append("Cỡ mẫu N")
            elif parsed["n"] != n_can:
                mismatches.append(f"N ký ở §12={parsed['n']} ≠ G3 hiện tại {n_nhan}={n_can}")
        for khoa, noi in (("n_muc1", "§1"), ("n_chung_chi", "chứng chỉ khoá (PHẦN 5)")):
            n_noi = parsed.get(khoa)
            if n_noi is None:
                continue
            if n_can and n_noi != n_can:
                mismatches.append(f"N ở {noi}={n_noi} ≠ G3 hiện tại {n_nhan}={n_can}")
            elif parsed["n"] is not None and n_noi != parsed["n"]:
                mismatches.append(f"N ở {noi}={n_noi} ≠ N ở §12={parsed['n']}")

        if loai12 == "power":
            g3_effect_val = _as_float(g3_checkpoint.get("effect_val"))
            g3_effect_type = str(g3_checkpoint.get("effect_type") or "")
            if g3_effect_val is not None and parsed["effect_val"] is None:
                thieu.append("effect size")
            _lech_so("effect_val", parsed["effect_val"], g3_effect_val, 0.005)
            if parsed["effect_type"] and g3_effect_type and parsed["effect_type"] != g3_effect_type:
                mismatches.append(f"effect_type ký={parsed['effect_type']} ≠ G3 hiện tại={g3_effect_type}")

        g3_hyp = str(g3_checkpoint.get("hypothesis_type") or "superiority")
        if parsed["hypothesis_type"] and parsed["hypothesis_type"] != g3_hyp:
            mismatches.append(f"hypothesis_type ký={parsed['hypothesis_type']} ≠ G3 hiện tại={g3_hyp}")
        if g3_hyp in ("non_inferiority", "equivalence") and g3_checkpoint.get("margin") is not None \
                and parsed["margin"] is None:
            thieu.append("biên margin Δ")
        _lech_so("margin", parsed["margin"], g3_checkpoint.get("margin"), 0.001)
        if str(g3_checkpoint.get("effect_type") or "") == "MD" and g3_checkpoint.get("sd") is not None \
                and parsed["sd"] is None:
            thieu.append("SD kết cục")
        _lech_so("SD", parsed["sd"], g3_checkpoint.get("sd"), 0.01)
        # Tham số quyết định N khác (G3 ghi từ 04/10/2026): SAP có ghi thì phải khớp G3.
        for khoa, nhan, dung_sai in (("p0", "p0", 1e-6), ("p_event", "p_event", 1e-6),
                                     ("dropout", "tỷ lệ bỏ cuộc", 1e-6),
                                     ("icc", "ICC", 1e-6), ("cluster_size", "cỡ cụm m", 1e-6),
                                     ("design_effect", "hiệu ứng thiết kế DE", 1e-4), ("n_clusters", "số cụm", 0.5),
                                     ("n_benh", "số ca bệnh", 0.5), ("n_khong_benh", "số ca không bệnh", 0.5),
                                     ("prevalence", "tỷ lệ hiện mắc dự kiến", 1e-6),
                                     ("population_n", "quần thể FPC", 0.5)):
            _lech_so(nhan, parsed.get(khoa), g3_checkpoint.get(khoa), dung_sai)
        if parsed["outcome_direction"] and g3_checkpoint.get("outcome_direction") \
                and parsed["outcome_direction"] != g3_checkpoint.get("outcome_direction"):
            mismatches.append(f"chiều kết cục ký={parsed['outcome_direction']} ≠ G3 hiện tại="
                              f"{g3_checkpoint.get('outcome_direction')}")
        if mismatches:
            num_status, num_evidence = "BLOCK", "; ".join(mismatches)
        elif thieu or sai_khung:
            num_status = "REVIEW"
            num_evidence = "; ".join(([f"§12 thiếu số ký: {', '.join(thieu)}"] if thieu else []) + sai_khung)
        else:
            num_status, num_evidence = "PASS", (f"số liệu ký (§12 loại {loai12}, N ở §1/chứng chỉ) khớp "
                                                "G3_checkpoint.json hiện tại")
    automatic.append(_criterion(
        "G4-AUTO-03",
        "Số liệu đã ký (§12, N ở §1 và chứng chỉ khoá) đủ và khớp G3_checkpoint.json HIỆN TẠI",
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
        if PC.co_o_trong(body6):
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
    # VÁ 04/10/2026 (soát từng cổng, G4-01): §8 bị XOÁ thân (hoặc cả mục) từng ra «§8 đã điền» ⇒ PASS. Nay rỗng ⇒
    # REVIEW; ô trống nhận theo hợp đồng chung placeholder_contract (CHUNG-B).
    body8 = _section_body(artifact_text, "§8")
    if not _than_muc(artifact_text, "§8"):
        comparison_status = "REVIEW"
        comparison_evidence = "§8 vắng hoặc không có nội dung — chiến lược đa so sánh chưa ghi"
    elif PC.co_o_trong(body8):
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
    # §7 không nằm trong tập mục bắt buộc của approve_gate._g4_sections_still_draft, nhưng REVIEW ở đây làm trạng thái
    # G4 = DRAFT và approve_gate (gọi bộ chấm này trước khi ký) TỪ CHỐI ký. VÁ 04/10/2026 (G4-01): §7 bị XOÁ thân/cả mục
    # từng ra «§7 đã điền» ⇒ nay REVIEW.
    body7 = _section_body(artifact_text, "§7")
    if not _than_muc(artifact_text, "§7"):
        subgroup_status = "REVIEW"
        subgroup_evidence = "§7 vắng hoặc không có nội dung — nhóm nhỏ tiền định (hoặc chiến lược chọn mẫu) chưa ghi"
    elif PC.co_o_trong(body7):
        subgroup_status = "REVIEW"
        subgroup_evidence = ("§7 (subgroup/chọn mẫu đa dạng) còn placeholder '[CẦN' — G4 ở DRAFT nên approve_gate "
                             "từ chối ký tới khi điền")
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
    # VÁ 04/10/2026 (soát từng cổng, G4-10): bản cũ dò «tên+phiên bản» trên CẢ §10 nên chính cụm «seed 42» ở dòng seed
    # khớp mẫu chữ+số ⇒ «Phần mềm: OK» vẫn PASS. Nay chỉ dò trên DÒNG «**Phần mềm:**» (bỏ cụm «seed …» nếu lẫn vào);
    # seed đọc trên dòng «**Random seed:**» nếu có. Định tính: seed «KHÔNG ÁP DỤNG» là hợp lệ (không có bước ngẫu
    # nhiên).
    m_pm = re.search(r"\*\*Phần mềm:\*\*([^\n]*)", body10)
    dong_pm = re.sub(r"seed\D{0,20}\d+", " ", m_pm.group(1) if m_pm else "", flags=re.IGNORECASE)
    has_software = bool(re.search(r"[A-Za-z]+\s*v?\.?\s*\d+(\.\d+)?", dong_pm))
    m_seed = re.search(r"\*\*Random seed:\*\*([^\n]*)", body10)
    dong_seed = m_seed.group(1) if m_seed else body10
    has_seed = bool(re.search(r"seed\D{0,20}(\d+)", dong_seed, re.IGNORECASE)) or bool(
        m_seed and re.fullmatch(r"\s*(?:set\.seed\()?\s*\d+\s*\)?\s*", dong_seed))
    if design_code == "qualitative" and re.search(r"KHÔNG ÁP DỤNG", dong_seed):
        has_seed = True
    if PC.co_o_trong(body10):
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
    # VÁ 04/10/2026 (soát từng cổng — lộ ở kiểm đầu–cuối 8 thiết kế): bản cũ coi MỌI giả thuyết khác «superiority» là
    # NI/tương đương ⇒ đề tài MÔ TẢ (descriptive_precision — như C1a) bị BLOCK vĩnh viễn vì «thiếu margin». Margin chỉ
    # thuộc về NI/tương đương (cùng tập NI_HYPOTHESES mà G3-AUTO-11 dùng).
    if hypothesis_type not in ("non_inferiority", "equivalence"):
        margin_status, margin_evidence = "PASS", f"hypothesis_type={hypothesis_type} — không cần margin"
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
        still_draft = AG._g4_sections_still_draft(artifact_text, design_code)
        muc_bat_buoc = list(AG._g4_muc_bat_buoc(artifact_text, design_code))
    except ImportError:  # pragma: no cover - lưới an toàn
        still_draft = None
        muc_bat_buoc = []
    # §4/§9 (mọi thiết kế) và §13–§15 (RCT, QĐ-1) thành bắt buộc từ 04/10/2026. SAP ĐÃ KÝ sổ cái trước mốc đó mà các mục
    # này còn ô trống/vắng thì dòng này vẫn hiện REVIEW để bác sĩ đọc, nhưng KHÔNG hạ cấp trạng thái một quyết định
    # người thật đã chốt (cùng nguyên tắc với G4-AUTO-11 ở dưới) — muốn điền thì đi đường sửa đổi SAP (amendment).
    # Mục bắt buộc cũ (§1/§2/§5/§10) vẫn hạ cấp như trước.
    auto10_khong_ha_cap = False
    if still_draft is None:
        placeholder_status = "REVIEW"
        placeholder_evidence = "không import được approve_gate._g4_sections_still_draft để kiểm"
    elif still_draft and ledger_signed and all(m.split()[0] in _G4_MUC_BAT_BUOC_TU_20261004 for m in still_draft):
        placeholder_status = "REVIEW"
        auto10_khong_ha_cap = True
        placeholder_evidence = (
            f"SAP đã ký sổ cái nhưng còn ô trống/vắng ở: {', '.join(still_draft)} — các mục này mới thành bắt "
            "buộc từ 04/10/2026, không hạ cấp quyết định đã ký; điền qua sửa đổi SAP (amendment) nếu cần"
        )
    elif still_draft:
        placeholder_status = "REVIEW"
        placeholder_evidence = f"còn ô trống hoặc VẮNG ở mục bắt buộc: {', '.join(still_draft)}"
    else:
        placeholder_status = "PASS"
        placeholder_evidence = "không còn ô trống ở " + "/".join(muc_bat_buoc)
    automatic.append(_criterion(
        "G4-AUTO-10",
        "Mục bắt buộc có mặt và không còn ô trống (§1/§2/§4/§5/§9/§10; RCT thêm §13/§14/§15)",
        placeholder_status,
        placeholder_evidence,
        "Điền đủ (và khôi phục nếu đã xoá) §1/§2/§4/§5/§9/§10, RCT thêm §13/§14/§15 — approve_gate.py cũng từ chối "
        "ký khi mục bắt buộc còn ô trống hoặc vắng.",
    ))

    # ── G4-AUTO-11 — kết cục chính §2 khớp câu hỏi nghiên cứu gốc ──────────
    g0_meta = _gate_params(meta, "G0")
    g1_meta = _gate_params(meta, "G1")

    def _ten_ket_cuc(value: Any) -> str:
        # VÁ 04/10/2026 (soát từng cổng): G1 ghim kết cục chính CÓ CẤU TRÚC {name, measure, timepoint, type} (G1-02) —
        # str(dict) cũ thành «{'name': …}» không bao giờ nằm trong §2 ⇒ REVIEW oan. Lấy «name» như G3-HUMAN-04.
        if isinstance(value, Mapping):
            value = value.get("name") or value.get("text")
        return str(value or "").strip()

    # Ưu tiên kết cục ĐÃ GHIM ở G1 (thiết kế — G3 tính N cho đúng kết cục này), rồi mới tới câu hỏi G0.
    declared_outcome = _ten_ket_cuc(g1_meta.get("primary_outcome")) or _ten_ket_cuc(g0_meta.get("primary_outcome"))
    body2 = _section_body(artifact_text, "§2")
    if not declared_outcome:
        outcome_status = "PASS"
        outcome_evidence = "chưa có gate_params.G0/G1.primary_outcome để đối chiếu (không phải lỗi)"
    elif PC.co_o_trong(body2):
        outcome_status = "PASS"
        outcome_evidence = "§2 còn placeholder — đã bị chặn riêng ở G4-AUTO-10, không kiểm trùng"
    elif _gon_chu_tho(declared_outcome) in _gon_chu_tho(body2):
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

    # ── G4-AUTO-12 — G3 CHẤM SỐNG đã chốt, không bị chặn (G4-04 ≡ G3-05, CHUNG-A) ───────────────────────────────────
    # VÁ 04/10/2026 (soát từng cổng): G4 từng không xét trạng thái chất lượng G3 — run_g3_auto ghi G3_checkpoint (kèm N)
    # TRƯỚC khi chấm rồi mới thoát mã 3 khi BLOCKED, nên SAP khoá được N mà chính G3 tự đánh giá là sai (vd FPC áp cho
    # RCT). G4-AUTO-03 so SAP với chính số G3 đang bị chặn nên luôn khớp. Nay chấm SỐNG G3 (cong_song, write=False):
    # BLOCKED ⇒ BLOCK; chưa chốt (DRAFT/READY) ⇒ REVIEW — SAP không khoá trên N chưa được thống kê viên/PI chốt;
    # không đo được ⇒ REVIEW (không đo được ≠ đạt). G3 chấm sống lại chấm sống G1 ⇒ G1 bị chặn (pin thiết kế bị từ
    # chối) cũng tới đây.
    if not isinstance(g3_song, Mapping):
        g3s_status = "REVIEW"
        g3s_evidence = "G3 không được chấm sống (nơi gọi không truyền g3_song) — KHÔNG ĐO ĐƯỢC, không phải «đạt»"
    else:
        muc_g3 = g3_song.get("muc")
        if muc_g3 == "PASS":
            g3s_status, g3s_evidence = "PASS", f"G3 chấm sống={g3_song.get('status')}"
        elif muc_g3 == "BLOCKED":
            bao_cao_g3 = g3_song.get("bao_cao") if isinstance(g3_song.get("bao_cao"), Mapping) else {}
            chan = [str(r.get("id")) for r in bao_cao_g3.get("automatic_criteria") or []
                    if isinstance(r, Mapping) and r.get("status") == "BLOCK"]
            g3s_status = "BLOCK"
            g3s_evidence = (f"G3 chấm sống=BLOCKED ({', '.join(chan) or g3_song.get('ly_do')}) — cỡ mẫu/tham số mà SAP "
                            "sắp khoá đang bị chính G3 chặn")
        elif muc_g3 == CS.KHONG_DO_DUOC:
            g3s_status = "REVIEW"
            g3s_evidence = f"G3 KHÔNG ĐO ĐƯỢC ({g3_song.get('ly_do')}) — không phải «đạt»"
        else:
            g3s_status = "REVIEW"
            g3s_evidence = (f"G3 chấm sống={g3_song.get('status')} — cỡ mẫu chưa được thống kê viên/PI chốt "
                            "(PASS_G3_CONFIRMED); SAP không được khoá trên N chưa chốt")
    automatic.append(_criterion(
        "G4-AUTO-12",
        "G3 (cỡ mẫu) chấm sống đã chốt PASS_G3_CONFIRMED — không bị chặn",
        g3s_status,
        g3s_evidence,
        "Chạy python3 tools/g3_quality_gate.py --study <đề tài>, xử lý mục BLOCK/REVIEW của G3 (thống kê viên/PI xác "
        "nhận tham số gắn dấu vân tay) rồi chấm lại G4.",
    ))

    # ── G4-AUTO-13 — chứng chỉ khoá (PHẦN 5) đã điền và khớp §2 (G4-09, CHUNG-B) ─────────────────────────────────────
    # VÁ 04/10/2026 (soát từng cổng): hai ô «KQ chính»/«Phân tích» của chứng chỉ — VĂN BẢN THẬT SỰ ĐƯỢC KÝ — luôn sinh
    # là «[CẦN BÁC SĨ ĐIỀN…]», nhưng cả _g4_sections_still_draft lẫn _section_body chỉ duyệt khối §N (dừng ở
    # «## PHẦN») nên PHẦN 5 chưa bao giờ được kiểm ⇒ ký được chứng chỉ trống. Dòng ký tay «____» (họ TRONG) KHÔNG
    # tính là ô trống.
    phan5 = _phan_body(artifact_text, "5")
    if not phan5:
        cc_status, cc_evidence = "REVIEW", "không có PHẦN 5 — chứng chỉ khoá SAP (văn bản được ký) vắng"
    elif PC.co_o_trong(phan5):
        cc_status = "REVIEW"
        cc_evidence = "chứng chỉ khoá còn ô trống: " + " | ".join(PC.dong_con_trong(phan5)[:3])
    else:
        m_kq = re.search(r"KQ chính\s*:\s*([^║\n]+)", phan5)
        m_kc = re.search(r"\*\*Kết cục chính:\*\*\s*([^\n]+)", body2)
        # Diễn đạt lại cùng kết cục là bình thường (C1a: «G1 hài lòng chung (thứ hạng 1-5)…» ở chứng chỉ, «G1 — mức hài
        # lòng chung…» ở §2) — chỉ REVIEW khi KHÔNG QUÁ NỬA số từ của «KQ chính» có trong dòng kết cục chính §2
        # (dấu hiệu nói một kết cục khác).
        if m_kq and m_kc and _ty_le_tu_chung(m_kq.group(1), m_kc.group(1)) <= 0.5:
            cc_status = "REVIEW"
            cc_evidence = (f"«KQ chính» ở chứng chỉ ({m_kq.group(1).strip()[:60]!r}) khác «Kết cục chính» ở §2 "
                           f"({m_kc.group(1).strip()[:60]!r}) — văn bản ký phải nói cùng một kết cục chính")
        else:
            cc_status, cc_evidence = "PASS", "chứng chỉ khoá đã điền, «KQ chính» cùng kết cục với §2"
    automatic.append(_criterion(
        "G4-AUTO-13",
        "Chứng chỉ khoá SAP (PHẦN 5) đã điền đủ và «KQ chính» khớp §2",
        cc_status,
        cc_evidence,
        "Điền «KQ chính»/«Phân tích» ở chứng chỉ khoá (PHẦN 5) đúng như §2/§4 trước khi ký.",
    ))

    # ── G4-AUTO-14 — N kế hoạch THẤP HƠN N tối thiểu phải được NÓI THẬT và giải trình (G4-05) ─────────────────────────
    # VÁ 04/10/2026 (soát từng cổng): run_g4_auto in «N ở trên … lớn hơn mức tối thiểu» chỉ với điều kiện N kế hoạch ≠ N
    # tối thiểu — không xét CHIỀU — nên SAP ký khẳng định SAI khi confirmed_n < n_adjusted (đề tài thiếu lực);
    # G4-AUTO-03 so với confirmed_n nên vẫn PASS. Nay: SAP còn câu «lớn hơn mức tối thiểu» ⇒ BLOCK (khẳng định sai
    # trong văn bản ký);
    # SAP không nêu «THẤP HƠN N tối thiểu» ⇒ REVIEW; chưa có giải trình của người thật (gate_params.G3.
    # underpowered_acceptance_justification — cùng trường G3-AUTO-13 đọc) ⇒ REVIEW.
    n_toi_thieu = _as_int(g3_checkpoint.get("n_adjusted")) or 0
    n_chot = _as_int(g3_checkpoint.get("confirmed_n"))
    giai_trinh = _gate_params(meta, "G3").get("underpowered_acceptance_justification")
    if n_chot and n_toi_thieu > 0 and n_chot < n_toi_thieu:
        if "lớn hơn mức tối thiểu" in artifact_text:
            ul_status = "BLOCK"
            ul_evidence = (f"SAP khẳng định N kế hoạch «lớn hơn mức tối thiểu» trong khi confirmed_n={n_chot} < N tối "
                           f"thiểu={n_toi_thieu} — khẳng định SAI trong văn bản sẽ ký")
        elif NHAN_LOAI_THIEU_LUC not in artifact_text:
            ul_status = "REVIEW"
            ul_evidence = (f"confirmed_n={n_chot} < N tối thiểu={n_toi_thieu} nhưng SAP không nêu "
                           f"«{NHAN_LOAI_THIEU_LUC}» "
                           "— người đọc SAP không biết đề tài thiếu lực/thiếu độ chính xác")
        elif not _present(giai_trinh):
            ul_status = "REVIEW"
            ul_evidence = (f"confirmed_n={n_chot} < N tối thiểu={n_toi_thieu} — chưa có giải trình của thống kê "
                           "viên/PI "
                           "ở gate_params.G3.underpowered_acceptance_justification")
        else:
            ul_status = "PASS"
            ul_evidence = (f"confirmed_n={n_chot} < N tối thiểu={n_toi_thieu}: SAP nêu rõ và đã có giải trình "
                           "chấp nhận "
                           f"({str(giai_trinh)[:80]})")
    else:
        ul_status, ul_evidence = "PASS", "N kế hoạch ≥ N tối thiểu (hoặc chưa chốt N riêng)"
    automatic.append(_criterion(
        "G4-AUTO-14",
        "N kế hoạch thấp hơn N tối thiểu được nêu thật và có giải trình",
        ul_status,
        ul_evidence,
        "Nâng N, hoặc thống kê viên/PI ghi gate_params.G3.underpowered_acceptance_justification (vì sao chấp nhận, hệ "
        "quả lên diễn giải) rồi chạy lại G3 → G4.",
    ))

    # ── G4-AUTO-15 — estimand ICH E9(R1) khai ở G1 có mặt ở §4 SAP RCT (G4-03 ≡ G1-08, CHUNG-F) ─────────────────────
    # VÁ 04/10/2026 (soát từng cổng): STANDARDS_BASIS tuyên bố đối chiếu estimand/biến cố xen ngang nhưng không tiêu chí
    # nào đọc estimand; SAP RCT in cứng «ITT, PP» mà không nói cái nào CHÍNH. Nay §4 của SAP RCT phải chứa ĐỦ 5 thuộc
    # tính estimand đã khai ở G1 (đặc tả thiết kế khoá ở G1 — không suy lại) và dòng «Quần thể phân tích CHÍNH».
    if design_code != "rct":
        est_status = "PASS"
        est_evidence = f"thiết kế {design_code or '?'} — estimand bắt buộc (G1-HUMAN-05) chỉ cho RCT"
    else:
        est = (dac_ta or {}).get("estimand") if dac_ta is not None else _gate_params(meta, "G1").get("estimand")
        est = est if isinstance(est, Mapping) else {}
        thieu_g1 = [k for k in KHOA_ESTIMAND if not _present(est.get(k))]
        than4 = _gon_chu_tho(_section_body(artifact_text, "§4"))
        if thieu_g1:
            est_status = "REVIEW"
            est_evidence = (f"G1 chưa khai đủ estimand ({', '.join(thieu_g1)}) — SAP RCT chưa thể khoá chiến lược/quần "
                            "thể phân tích chính")
        else:
            khong_co = [k for k in KHOA_ESTIMAND if _gon_chu_tho(est.get(k)) not in than4]
            if khong_co:
                est_status = "REVIEW"
                est_evidence = f"§4 không chứa estimand đã khai ở G1 ({', '.join(khong_co)})"
            elif "quần thể phân tích chính" not in than4:
                est_status, est_evidence = "REVIEW", "§4 chưa nêu «Quần thể phân tích CHÍNH»"
            else:
                est_status, est_evidence = "PASS", "§4 chứa đủ 5 thuộc tính estimand của G1 và quần thể phân tích chính"
    automatic.append(_criterion(
        "G4-AUTO-15",
        "RCT: §4 chứa estimand ICH E9(R1) đã khai ở G1 và quần thể phân tích chính",
        est_status,
        est_evidence,
        "Khai gate_params.G1.estimand (5 thuộc tính) rồi chạy lại G1 → G4; chốt «Quần thể phân tích CHÍNH» ở §4.",
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
    reviewed_at = str(g4_meta.get("reviewed_at") or "").strip()
    data_lock_date = str(meta.get("data_lock_date") or "").strip()
    # VÁ 04/10/2026 (soát từng cổng, G4-07 + bỏ sót CHUNG-C): (a) ngày từng so bằng chuỗi [:10] không kiểm dạng — ghi
    # «15/09/2026» thì luôn «nhỏ hơn» «2026-09-01» nên chốt HARKing không bao giờ bật; nay ngày sai dạng ISO ⇒ REVIEW
    # (không so được ≠ ổn). (b) Thời điểm KÝ thật trên sổ cái (timestamp bản ghi G4) từng không được so với ngày khoá dữ
    # liệu: ký lại sau khi sửa SAP lúc đã khoá dữ liệu vẫn PASS ⇒ nay REVIEW trừ khi PHẦN 4 có dòng «SAP AMENDMENT».
    harking_problems: list[str] = []
    if reviewed_at and not CS.iso_khong_tuong_lai(reviewed_at):
        harking_problems.append(f"reviewed_at={reviewed_at!r} không phải ISO-8601 hợp lệ hoặc ở tương lai — không so "
                                "được với ngày khoá dữ liệu")
    if data_lock_date and not _RE_ISO_NGAY.match(data_lock_date):
        harking_problems.append(f"data_lock_date={data_lock_date!r} không đúng dạng ISO YYYY-MM-DD")
    elif data_lock_date and not reviewed_at:
        harking_problems.append("dữ liệu đã khoá nhưng xác nhận G4 không có reviewed_at — không chứng minh được xác "
                                "nhận TRƯỚC khi khoá")
    elif data_lock_date and _RE_ISO_NGAY.match(reviewed_at) and reviewed_at[:10] > data_lock_date[:10]:
        harking_problems.append(f"reviewed_at ({reviewed_at[:10]}) SAU data_lock_date ({data_lock_date[:10]}) — nghi "
                                "xác nhận subgroup SAU khi đã thấy dữ liệu (HARKing)")
    if ledger_signed and ledger_lock_timestamp:
        ky_sau = ky_sau_khoa_du_lieu(artifact_text, data_lock_date, ledger_lock_timestamp)
        if ky_sau:
            harking_problems.append(ky_sau)
    if not subgroup_confirmed:
        subgroup_human_status = "REVIEW"
        subgroup_human_evidence = "gate_params.G4.subgroup_multiplicity_predefined_confirmed chưa bật"
    elif harking_problems:
        subgroup_human_status, subgroup_human_evidence = "REVIEW", "; ".join(harking_problems)
    else:
        subgroup_human_status = "PASS"
        subgroup_human_evidence = (
            "subgroup đã xác nhận tiền định, mốc thời gian hợp lý "
            "(hoặc chưa có data_lock_date để đối chiếu)"
        )
    approval.append(_criterion(
        "G4-HUMAN-06",
        "Subgroup/đa so sánh xác nhận TIỀN ĐỊNH trước khi khóa dữ liệu (ngày ISO, ký trước khoá hoặc có amendment)",
        subgroup_human_status,
        subgroup_human_evidence,
        "Đặt gate_params.G4.subgroup_multiplicity_predefined_confirmed=true và reviewed_at dạng ISO-8601 TRƯỚC khi G5 "
        "khoá dữ liệu; sửa SAP sau khi khoá dữ liệu phải ghi dòng «SAP AMENDMENT» ở PHẦN 4.",
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

    # VÁ 04/10/2026 (soát từng cổng, CHUNG-C/QĐ-7): ba xác nhận G4-HUMAN-04/05/06 từng là cờ True trơn — sửa §5/§6/§7
    # SAU khi xác nhận vẫn PASS. Nay xác nhận phải gắn DẤU NỘI DUNG PHẦN 3 hiện tại (dau_van_tay_g4); xác nhận kiểu cũ
    # không dấu ⇒ REVIEW tới khi thống kê viên/PI xác nhận lại (chuyển tiếp QĐ-7). Dấu hiện tại in trong hành động.
    dau_hien_tai = dau_van_tay_g4(artifact_text)
    xn_ok, xn_ly_do = CS.xac_nhan_gan_noi_dung(
        {"reviewed_at": g4_meta.get("reviewed_at"), "dau_van_tay": g4_meta.get("dau_van_tay_chot")}, dau_hien_tai)
    approval.append(_criterion(
        "G4-HUMAN-08",
        "Xác nhận G4 của thống kê viên/PI gắn đúng nội dung SAP hiện tại (dấu vân tay)",
        "PASS" if xn_ok else "REVIEW",
        xn_ly_do,
        f'Sau khi đọc lại SAP, ghi gate_params.G4.dau_van_tay_chot="{dau_hien_tai}" (dấu nội dung PHẦN 3 hiện tại) '
        "cùng reviewed_at dạng ISO-8601; sửa SAP sau đó phải xác nhận lại.",
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
    # VÁ 04/10/2026 (soát từng cổng): cùng nguyên tắc «luật mới không hạ cấp quyết định đã ký» — G4-AUTO-13 (chứng chỉ
    # khoá, chưa từng được kiểm trước 04/10) và G4-AUTO-15 (estimand, so khớp chuỗi dễ vỡ như AUTO-11) chỉ HIỂN THỊ sau
    # khi đã ký. Chữ ký mới luôn phải qua chúng vì approve_gate chấm TRƯỚC khi ký (lúc đó ledger_signed=False); sửa SAP
    # sau khi ký làm lệch băm ⇒ ledger_signed=False ⇒ chúng lại tham gia. Thay đổi ở G1 lan tới qua G4-AUTO-12 (G3 chấm
    # sống G1). G4-AUTO-12 (G3 sống) và G4-AUTO-14 LUÔN tham gia: chúng phản ánh trạng thái HIỆN TẠI của cổng trước.
    _chi_hien_thi_sau_ky = {"G4-AUTO-11", "G4-AUTO-13", "G4-AUTO-15"}
    _status_driving = [
        row for row in automatic
        if not (row["id"] in _chi_hien_thi_sau_ky and ledger_signed)
        and not (row["id"] == "G4-AUTO-10" and auto10_khong_ha_cap)
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
            "PASS_G4_SAP_LOCKED xác nhận: SAP có đủ mục bắt buộc không còn ô trống (RCT gồm §13–§15), "
            "số liệu ký khớp G3_checkpoint.json hiện tại và G3 chấm sống đã chốt, chứng chỉ khoá đã điền, "
            "có phê duyệt ledger đúng vai trò thống kê/PI, và thống kê viên/PI đã xác nhận EPV/VIF, cơ chế "
            "dữ liệu thiếu, subgroup tiền định — gắn dấu nội dung SAP hiện tại. KHÔNG chứng minh nội dung "
            "phương pháp luận ĐÚNG về mặt "
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
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
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
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
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
    elif checkpoint.get("g4_lock_date"):
        # VÁ 04/10/2026 (soát từng cổng, G7-03 phía G4): trạng thái TỤT khỏi LOCKED (SAP sửa sau khi ký, G3 chạy lại…)
        # mà g4_lock_date cũ vẫn nằm đó ⇒ G7/list_studies/real_world_signals in «SAP đã khoá ngày X» sai. Xoá về None
        # (giữ khoá — run_g4_auto luôn ghi khoá này, tầng sau đọc .get()).
        checkpoint["g4_lock_date"] = None
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
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
        # VÁ 04/10/2026 (soát từng cổng): G3 CHẤM SỐNG (G4-04), mốc ký sổ cái so với khoá dữ liệu (G4-07), đặc tả thiết
        # kế khoá ở G1 cho estimand (G4-03).
        g3_song=CS.trang_thai_song("G3", study, out_dir, repo_root=repo_root),
        ledger_lock_timestamp=ledger_lock_timestamp,
        dac_ta=S.dac_ta_thiet_ke(out_dir),
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        # VÁ 26/08/2026 (cùng họ lỗi BH06 với g2/g8_quality_gate.py): out_dir luôn
        # tuyệt đối nên report_path cũng tuyệt đối — chỉ đổi CHUỖI ghi vào
        # checkpoint sang tương đối với repo_root, không đổi hành vi ghi file thật.
        try:
            recorded_path = report_path.relative_to(repo_root)
        except ValueError:
            recorded_path = report_path
        refresh_checkpoint(
            study=study, out_dir=out_dir, report=report,
            quality_report_path=recorded_path,
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
