#!/usr/bin/env python3
"""Canary đầu-cuối cho chuỗi cổng NGHIÊN CỨU G0–G10 (tác vụ Harness 6.1).

LÝ DO MODULE NÀY TỒN TẠI
------------------------
Dự án này có một bài học nền, đã tái diễn nhiều lần: **công cụ vẫn chạy, vẫn
in ra kết quả trông hợp lệ, nhưng thứ cần kiểm thì không bao giờ được kiểm.**
Ba ca thật (phía chứng cứ lâm sàng, xem CLAUDE.md mục "CANARY ĐẦU-CUỐI"):
``verify_dashboard.py`` có ``return`` sớm che 73 mục nguy hiểm; cổng A12
fail-open ký "all_clean=true" khi không một trích dẫn nào được kiểm; guardrail
G3/G8 phần lớn TAUTOLOGY (đếm chuỗi do chính hàm sinh in cứng).

Phía chứng cứ lâm sàng đã có thuốc chữa: ``tools/thu_dau_cuoi_chung_cu.py``
(repo GỐC — thư mục cha của repo này) gài lỗi biết trước vào một gói giả rồi
đòi dây chuyền bắt đủ, và đã CHỨNG MINH giá trị bằng đột biến (tái hiện lỗi
``return`` sớm → canary đỏ đúng chỗ).

**Phía NGHIÊN CỨU — chuỗi 11 quality gate ``tools/g0..g10_quality_gate.py`` —
KHÔNG có gì tương đương, cho tới module này.**

CÁCH HOẠT ĐỘNG
---------------
Module KHÔNG chạy pipeline `run_g*_auto.py` trên đề tài thật (không đụng
``exports/``, không ký, không gọi mạng). Thay vào đó nó gọi TRỰC TIẾP các hàm
``evaluate_gN_quality(...)`` — đúng bề mặt mà bộ test hồi quy của từng cổng
(``tests/test_g3_quality_gate.py``, ``test_g4_quality_gate.py``,
``test_g8_quality_gate.py``) đã dùng — với dữ liệu TỔNG HỢP (synthetic),
KHÔNG PII.

Mỗi lỗi gài (``InjectedError``) mang: mã, cổng chịu trách nhiệm, một dòng lý
do LỊCH SỬ (lỗi này từng xảy ra thật ở đâu/khi nào, hại gì), tiêu chí (id) kỳ
vọng bị chặn, và một hàm dựng report từ baseline "gói tốt" + MỘT thay đổi duy
nhất tạo ra lỗi đó.

Nếu một lỗi gài mà KHÔNG cổng nào bắt được, đây KHÔNG được coi là bug của
canary để "sửa cho hết đỏ" — nó có thể là một khoảng trống THẬT của hệ cổng.
``run_canary()`` phản ánh đúng sự thật: tách rõ nhóm "đã có gate canh" và
nhóm "chưa ai canh", và không bao giờ tự ý nới lỏng kỳ vọng để canary xanh giả.

Chạy: ``python tools/thu_dau_cuoi_cong_nghien_cuu.py`` — ngoại tuyến, < 5 giây.
Mã thoát: 0 = mọi lỗi gài đều bị đúng cổng bắt; khác 0 = có lỗi gài bị lọt.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g3_quality_gate as G3Q  # noqa: E402
import run_g3_auto as G3  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402

STUDY = "CANARY-NC-6.1"


# ════════════════════════════════════════════════════════════════════════════
# Đồ gá — G3 (cỡ mẫu). Mượn đúng hình dạng artifact/checkpoint mà
# tests/test_g3_quality_gate.py đã xác nhận là "gói tốt" đạt PASS.
# ════════════════════════════════════════════════════════════════════════════

def _g3_artifact(
    *,
    n_total: int = 942,
    n_adjusted: int = 1178,
    dropout_pct: int = 20,
    base_cell: Optional[int] = None,
    na_cells: bool = False,
    standard_token: str = "CONSORT 2025",
) -> str:
    base = n_adjusted if base_cell is None else base_cell
    low = "N/A" if na_cells else str(int(base * 1.5))
    high = "N/A" if na_cells else str(int(base * 0.7))
    return f"""# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)

## PHẦN 2 — KẾT QUẢ TÍNH TOÁN

| N tổng (không dropout) | **{n_total}** |
| N điều chỉnh | **{n_adjusted}** |

## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)

Bảng: Power × Effect size → N tổng (điều chỉnh {dropout_pct}% dropout)

| Power | ES × 0.8 (80%) | ES × 1.0 (cơ sở) | ES × 1.2 (120%) |
|---|---|---|---|
| 70% | {low} | {int(base * 0.8)} | {high} |
| 80% | {low} | {base} | {high} |
| 90% | {low} | {int(base * 1.3)} | {high} |

## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)

Khối này viết theo {standard_token}.

*Cần bác sĩ kiểm chứng.*
"""


def _g3_checkpoint(**overrides) -> Dict[str, Any]:
    value = {
        "gate": "G3",
        "study": STUDY,
        "design_code": "rct",
        "design_ambiguous": False,
        "alpha": 0.05,
        "power": 0.80,
        "effect_val": 8.0,
        "effect_type": "ARR%",
        "effect_quality": "labeled",
        "n_per_group": 471,
        "n_total": 942,
        "n_adjusted": 1178,
        "confirmed_n": None,
        "dropout": 0.20,
        "formula_used": "Hai tỷ lệ độc lập (xấp xỉ chuẩn), z(α/2)=1.96",
        "p_event": 0.30,
        "p0": 0.30,
        "sd": None,
        "hypothesis_type": "superiority",
        "margin": None,
        "guardrail": "✅ PASS",
    }
    value.update(overrides)
    return value


def _g3_full_meta(**g3_overrides) -> Dict[str, Any]:
    g3 = {
        "effect_size": 8.0,
        "effect_type": "ARR%",
        "effect_source": "PMID: 30560792",
        "effect_source_confirmed": True,
        "p0_source": "PMID: 30560792 — tỷ lệ biến cố nhóm chứng 30%",
        "dropout_source": "Pilot nội bộ tổng hợp, tỷ lệ bỏ cuộc 18%",
        "assumptions_confirmed": True,
        "hypothesis_confirmed": True,
        "powered_for_outcome": "Kết cục tổng hợp canary",
        "recruitment_feasibility_confirmed": True,
        "reviewed_by_role": "BIOSTATISTICIAN",
        "reviewed_at": "2026-08-22T09:00:00",
        "software": "run_g3_auto.py + scipy",
    }
    g3.update(g3_overrides)
    return {
        "gate_params": {
            "G1": {"primary_outcome": "Kết cục tổng hợp canary"},
            "G3": g3,
        }
    }


def _evaluate_g3(tmp_path: Path, *, checkpoint=None, meta=None, artifact=None) -> Dict[str, Any]:
    artifact_path = tmp_path / f"G3_A4_SAMPLE_SIZE_{STUDY}.md"
    artifact_path.write_text(
        _g3_artifact() if artifact is None else artifact, encoding="utf-8", newline="\n"
    )
    return G3Q.evaluate_g3_quality(
        study=STUDY,
        checkpoint=_g3_checkpoint() if checkpoint is None else checkpoint,
        artifact_path=artifact_path,
        g0_checkpoint={"gate": "G0"},
        g1_checkpoint={"gate": "G1"},
        meta=_g3_full_meta() if meta is None else meta,
    )


# ════════════════════════════════════════════════════════════════════════════
# Đồ gá — G4 (khóa SAP). Mượn từ tests/test_g4_quality_gate.py.
# ════════════════════════════════════════════════════════════════════════════

_COMPARATIVE_FILLS: Sequence[tuple] = (
    ("- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ", "- **Tiêu chí nhận:** Tuổi 18-75  "),
    ("- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ", "- **Tiêu chí loại:** Chống chỉ định  "),
    ("- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
     "- **Kết cục chính:** Kết cục tổng hợp canary  "),
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
    ("- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ", "- **Random seed:** set.seed(20260822)  "),
    ("| 1.0 | 2026-08-22 | [CẦN TÊN TÁC GIẢ] | Bản đầu tiên (tự động từ G1) |",
     "| 1.0 | 2026-08-22 | BS. Canary  | Bản đầu tiên (tự động từ G1) |"),
    ("| [CẦN thêm biến] | | | |", "| age, hba1c_baseline | | | |"),
    ("| [CẦN KẾT QUẢ THẬT] | | | |", "| (điền sau khi có dữ liệu thật) | | | |"),
    ("║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]                 ║",
     "║ KQ chính  : Kết cục tổng hợp canary                        ║"),
    ("║ Phân tích : [CẦN BÁC SĨ ĐIỀN — quần thể phân tích]        ║",
     "║ Phân tích : Intention-to-treat (ITT)                      ║"),
)


def _g4_fresh_sap(design_code: str = "rct", **overrides) -> str:
    kwargs = dict(
        study=STUDY, topic="Đề tài canary G4", design_primary="RCT song song",
        reporting_std="CONSORT 2025", n_adjusted=400, alpha=0.05, power=0.8,
        effect_val=0.7, effect_type="RR", run_date="2026-08-22",
    )
    kwargs.update(overrides)
    return G4.generate(
        kwargs["study"], kwargs["topic"], design_code, kwargs["design_primary"],
        kwargs["reporting_std"], kwargs["n_adjusted"], kwargs["alpha"],
        kwargs["power"], kwargs["effect_val"], kwargs["effect_type"],
        kwargs["run_date"], kwargs.get("sd"),
        hypothesis_type=kwargs.get("hypothesis_type", "superiority"),
        margin=kwargs.get("margin"),
    )


def _g4_filled_sap(**overrides) -> str:
    text = _g4_fresh_sap(design_code=overrides.pop("design_code", "rct"), **overrides)
    for old, new in _COMPARATIVE_FILLS:
        if old not in text:
            raise AssertionError(f"template G4 đã đổi hình dạng, thiếu placeholder: {old[:50]!r}")
        text = text.replace(old, new)
    return text


def _g4_checkpoint(**overrides) -> Dict[str, Any]:
    value = {"gate": "G4", "study": STUDY, "design_code": "rct", "guardrail": "✅ PASS"}
    value.update(overrides)
    return value


def _g4_g3_checkpoint(**overrides) -> Dict[str, Any]:
    value = {
        "design_code": "rct", "alpha": 0.05, "power": 0.8, "n_adjusted": 400,
        "confirmed_n": None, "effect_val": 0.7, "effect_type": "RR",
        "hypothesis_type": "superiority", "margin": None, "sd": None,
    }
    value.update(overrides)
    return value


def _g4_meta(g4_overrides=None, g3_overrides=None) -> Dict[str, Any]:
    g4 = {
        "epv_vif_reviewed": True, "missing_data_mechanism_confirmed": True,
        "subgroup_multiplicity_predefined_confirmed": True,
        "reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-08-22T08:00:00+00:00",
    }
    g4.update(g4_overrides or {})
    g3 = dict(g3_overrides or {})
    return {"gate_params": {"G4": g4, "G0": {}, "G1": {}, "G3": g3}}


def _evaluate_g4(**overrides) -> Dict[str, Any]:
    kwargs = dict(
        study=STUDY,
        checkpoint=_g4_checkpoint(),
        artifact_text=_g4_filled_sap(),
        g3_checkpoint=_g4_g3_checkpoint(),
        g1_checkpoint={"design": {"internal_code": "rct"}},
        meta=_g4_meta(),
        ledger_signed=True,
        ledger_reason="",
        signature_scope="role",
        role_key_available=True,
        cross_gate_refs={"G2": "IRB-CANARY", "G4": "STAT-CANARY", "G8": "REV-CANARY", "G9": "PI-CANARY"},
    )
    kwargs.update(overrides)
    return G4Q.evaluate_g4_quality(**kwargs)


# ════════════════════════════════════════════════════════════════════════════
# Đồ gá — G8 (bình duyệt độc lập). Mượn từ tests/test_g8_quality_gate.py.
# ════════════════════════════════════════════════════════════════════════════

_G8_CLEAN_MANUSCRIPT = """# Bản thảo

## Tóm tắt
Nghiên cứu canary đánh giá can thiệp tổng hợp.

## Phương pháp
Kết cục chính là kết cục tổng hợp canary.
Nhóm nghiên cứu có sử dụng công cụ trí tuệ nhân tạo để hiệu đính ngôn ngữ.

## Kết quả
Kết quả sẽ được điền sau khi khóa dữ liệu.

## TÀI LIỆU THAM KHẢO
1. Tác giả canary. Tạp chí tổng hợp 2026.
"""

_G8_SAP_TEXT = "# SAP\nKết cục chính: kết cục tổng hợp canary.\n"

_G8_REVIEW_REPORT = """# NHẬN XÉT PHẢN BIỆN

## KHUYẾN NGHỊ
SỬA NHỎ

## LỖI NGHIÊM TRỌNG (phải sửa trước khi nộp)
| Vị trí | Vấn đề |
|---|---|
| Mục 3.2 | Thiếu khoảng tin cậy |

## GÓP Ý NHỎ
- Rút gọn phần mở đầu.

## CÂU HỎI CHO TÁC GIẢ
1. Vì sao chọn ngưỡng này?

## KẾT LUẬN TỔNG THỂ
Cần sửa thêm trước khi nộp.
"""

_G8_PRESUBMISSION_TEXT = (
    "# A9 — GÓI TIỀN NỘP BÀI\n"
    "Nội dung tự kiểm toàn bộ pipeline G0-G7.\n"
    "[CAN] Vài mục hành chính (CRediT/COI) còn chờ bác sĩ điền.\n"
    "Cần bác sĩ kiểm chứng.\n"
)


def _g8_checkpoint(**overrides) -> Dict[str, Any]:
    value = {
        "gate": "G8",
        "study": STUDY,
        "design_code": "rct",
        "guardrail": {"passed": True},
        "reporting_score_pct": 82.0,
        "pipeline_completeness": {
            f"G{i}": {"status": "PASS", "artifact": f"G{i}_ARTIFACT", "checkpoint_exists": True}
            for i in range(8)
        },
        "pipeline_pass_count": 8,
    }
    value.update(overrides)
    return value


def _g8_meta(**g8_overrides) -> Dict[str, Any]:
    g8 = {
        "primary_outcome": "kết cục tổng hợp canary",
        "ai_use_declared": True,
        "ai_tools": "Claude Opus 5",
        "ai_purpose": "hiệu đính ngôn ngữ",
        "ai_declared_in_cover_letter": True,
        "interventional": True,
        "registration_id": "NCT00000000",
        "registration_date": "2026-01-10",
        "first_enrolment_date": "2026-02-01",
        "data_sharing_statement": (
            "Chúng tôi sẽ chia sẻ dữ liệu cá nhân đã khử định danh; dữ liệu nào: bộ "
            "biến kết cục chính; kèm đề cương và SAP; thời gian: từ 6 tháng sau công "
            "bố, không có ngày kết thúc; tiêu chí truy cập: nhà nghiên cứu có đề cương "
            "được duyệt, qua cơ chế kho dữ liệu của đơn vị."
        ),
        "cover_letter_no_duplicate_submission": True,
        "cover_letter_coi_declared": True,
        "cover_letter_all_authors_approved": True,
        "cover_letter_corresponding_contact": True,
        "cover_letter_preprint_status": True,
        "reviewer_coi_declared": True,
        "reviewer_independence_declared": True,
        "reviewer_ai_use_declared": True,
        "reviewer_confidentiality_declared": True,
    }
    g8.update(g8_overrides)
    return {"gate_params": {"G8": g8}}


def _evaluate_g8(**overrides) -> Dict[str, Any]:
    kwargs = dict(
        study=STUDY,
        checkpoint=_g8_checkpoint(),
        presubmission_text=_G8_PRESUBMISSION_TEXT,
        manuscript_text=_G8_CLEAN_MANUSCRIPT,
        sap_text=_G8_SAP_TEXT,
        review_report_text=_G8_REVIEW_REPORT,
        g2_checkpoint={},
        meta=_g8_meta(),
        citation_ok=True,
        citation_detail="A12 đạt (canary)",
        ledger_signed=True,
        ledger_reason="",
        signature_scope="role",
        role_key_available=True,
        cross_gate_refs={"G2": "IRB-CANARY", "G4": "STAT-CANARY", "G8": "REV-CANARY", "G9": "PI-CANARY"},
    )
    kwargs.update(overrides)
    return G8Q.evaluate_g8_quality(**kwargs)


# ════════════════════════════════════════════════════════════════════════════
# Khung lỗi gài
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class InjectedError:
    code: str
    gate: str
    history: str
    build_report: Callable[[], Dict[str, Any]]
    criterion_id: str
    expect_criterion_status: frozenset
    bad_overall_statuses: frozenset  # tổng trạng thái KHÔNG được rơi vào đây
    tmp_needed: bool = False


def _row(report: Mapping[str, Any], criterion_id: str) -> Optional[Dict[str, Any]]:
    for key in ("automatic_criteria", "approval_criteria", "human_criteria"):
        for row in report.get(key, []):
            if row["id"] == criterion_id:
                return row
    return None


def build_injected_errors(tmp_path: Optional[Path] = None) -> List[InjectedError]:
    """Danh sách N lỗi BIẾT TRƯỚC, ưu tiên đúng các họ lỗi mà chuỗi cổng G0–G10
    đã từng mắc thật (xem CLAUDE.md + docstring các module gN_quality_gate.py)."""
    tmp_path = tmp_path or Path.cwd()

    errors: List[InjectedError] = []

    # ── G3 — bảng độ nhạy tự mâu thuẫn với N chính đã kết luận ─────────────
    errors.append(InjectedError(
        code="G3-SENS-TABLE-BASE-DRIFT",
        gate="G3 (cỡ mẫu)",
        history=(
            "guardrail_check() cũ của G3 chỉ soi VĂN BẢN do chính run_g3_auto.py "
            "sinh ra (tautology), không kiểm SỐ — bảng độ nhạy có thể tự mâu thuẫn "
            "với N đã kết luận mà không ai bắt được. Vá 2026-07-28, criterion "
            "G3-AUTO-09."
        ),
        build_report=lambda: _evaluate_g3(tmp_path, artifact=_g3_artifact(base_cell=245)),
        criterion_id="G3-AUTO-09",
        expect_criterion_status=frozenset({"REVIEW", "BLOCK"}),
        bad_overall_statuses=frozenset({"PASS_G3_CONFIRMED"}),
    ))

    errors.append(InjectedError(
        code="G3-N-PER-GROUP-MISMATCH",
        gate="G3 (cỡ mẫu)",
        history=(
            "checkpoint n_per_group không khớp phép cộng ra N tổng (n_per_group×2 "
            "≠ n_adjusted) — cùng lớp lỗi 'con số không đo thứ nó tự nhận' đã tìm "
            "thấy nhiều lần trong dự án (BH30-33). Criterion G3-AUTO-09."
        ),
        build_report=lambda: _evaluate_g3(tmp_path, checkpoint=_g3_checkpoint(n_per_group=100)),
        criterion_id="G3-AUTO-09",
        expect_criterion_status=frozenset({"REVIEW", "BLOCK"}),
        bad_overall_statuses=frozenset({"PASS_G3_CONFIRMED"}),
    ))

    errors.append(InjectedError(
        code="G3-NI-MARGIN-MISSING",
        gate="G3 (cỡ mẫu)",
        history=(
            "hypothesis_type=non_inferiority nhưng margin(Δ) rỗng — an toàn tối "
            "quan trọng cho NI/equivalence (FDA/EMA đều đòi Δ có nguồn). Criterion "
            "G3-AUTO-11, vá 2026-07-28."
        ),
        build_report=lambda: _evaluate_g3(
            tmp_path, checkpoint=_g3_checkpoint(hypothesis_type="non_inferiority", margin=None)
        ),
        criterion_id="G3-AUTO-11",
        expect_criterion_status=frozenset({"BLOCK"}),
        bad_overall_statuses=frozenset({"PASS_G3_CONFIRMED"}),
    ))

    # ── G4 — SAP đã ký không còn khớp G3_checkpoint HIỆN TẠI (F5) ──────────
    errors.append(InjectedError(
        code="G4-SAP-ALPHA-DRIFT",
        gate="G4 (khóa SAP)",
        history=(
            "SAP §12 ký alpha=0.05, nhưng G3 chạy LẠI SAU khi sinh SAP với "
            "alpha=0.10 — chữ ký mật mã chỉ bảo vệ TOÀN VẸN nội dung đang có, "
            "không bảo đảm nội dung đó còn ĐÚNG với cỡ mẫu thật. Phát hiện F5, "
            "audit toàn diện G0-G10 2026-07-29. Criterion G4-AUTO-03."
        ),
        build_report=lambda: _evaluate_g4(g3_checkpoint=_g4_g3_checkpoint(alpha=0.10)),
        criterion_id="G4-AUTO-03",
        expect_criterion_status=frozenset({"BLOCK"}),
        bad_overall_statuses=frozenset({G4Q.STATUS_LOCKED}),
    ))

    errors.append(InjectedError(
        code="G4-SAP-N-DRIFT",
        gate="G4 (khóa SAP)",
        history=(
            "SAP đã ký N=400, G3_checkpoint HIỆN TẠI N=999 (G3 rerun sau khi SAP "
            "sinh, không ai ký lại) — SAP của Hội đồng ghi một N khác với cỡ mẫu "
            "kế hoạch thật. Cùng phát hiện F5, criterion G4-AUTO-03."
        ),
        build_report=lambda: _evaluate_g4(g3_checkpoint=_g4_g3_checkpoint(n_adjusted=999)),
        criterion_id="G4-AUTO-03",
        expect_criterion_status=frozenset({"BLOCK"}),
        bad_overall_statuses=frozenset({G4Q.STATUS_LOCKED}),
    ))

    errors.append(InjectedError(
        code="G4-NI-MARGIN-MISSING",
        gate="G4 (khóa SAP)",
        history=(
            "Cùng lỗ hổng an toàn NI/equivalence như ở G3, nhưng kiểm ĐỘC LẬP ở "
            "tầng G4 (đối chiếu ngược lại G3_checkpoint tại thời điểm ký) — hai "
            "cổng canh cùng một rủi ro theo hai đường khác nhau. Criterion "
            "G4-AUTO-09."
        ),
        build_report=lambda: _evaluate_g4(
            g3_checkpoint=_g4_g3_checkpoint(hypothesis_type="non_inferiority", margin=None)
        ),
        criterion_id="G4-AUTO-09",
        expect_criterion_status=frozenset({"BLOCK"}),
        bad_overall_statuses=frozenset({G4Q.STATUS_LOCKED}),
    ))

    errors.append(InjectedError(
        code="G4-SAP-UNFILLED-PLACEHOLDER",
        gate="G4 (khóa SAP)",
        history=(
            "SAP còn NGUYÊN placeholder '[CẦN...]' (chưa ai điền) mà chốt gác cũ "
            "(_g4_sections_still_draft) chỉ đếm 4/12 mục — SAP có thể ký dù §6/§7/"
            "§8/§10 còn trống hoàn toàn. Đúng họ lỗi 'cổng tuyên bố ĐẠT khi nội "
            "dung then chốt vẫn placeholder'. Criterion G4-AUTO-10."
        ),
        build_report=lambda: _evaluate_g4(artifact_text=_g4_fresh_sap()),
        criterion_id="G4-AUTO-10",
        expect_criterion_status=frozenset({"REVIEW", "BLOCK"}),
        bad_overall_statuses=frozenset({G4Q.STATUS_LOCKED}),
    ))

    # ── G8 — trích dẫn/rút bài chưa xác minh bị đọc thành 'không vấn đề' ───
    errors.append(InjectedError(
        code="G8-CITATION-NOT-VERIFIED",
        gate="G8 (bình duyệt độc lập)",
        history=(
            "Cổng A12 (kiểm chứng trích dẫn/rút bài) chưa từng chạy hoặc chưa "
            "sạch — đúng họ lỗi FAIL-OPEN của BH27 (2026-08-14): khi trạng thái "
            "'chưa kiểm được' bị đọc nhầm thành 'không có vấn đề', all_clean=true "
            "được KÝ dù không một trích dẫn nào được kiểm. Criterion G8-AUTO-03."
        ),
        build_report=lambda: _evaluate_g8(citation_ok=False, citation_detail="A12 chưa chạy (canary)"),
        criterion_id="G8-AUTO-03",
        expect_criterion_status=frozenset({"BLOCK"}),
        bad_overall_statuses=frozenset({G8Q.STATUS_REVIEWED}),
    ))

    errors.append(InjectedError(
        code="G8-REVIEWER-NOT-INDEPENDENT",
        gate="G8 (bình duyệt độc lập)",
        history=(
            "Người ký G8 (reviewer_ref) TRÙNG với người ký G4 — một người đang "
            "tự duyệt cả cỡ mẫu lẫn bản thảo của chính mình. HMAC đối xứng không "
            "chứng minh được độc lập bằng mật mã; dấu hiệu rẻ nhất là đối chiếu "
            "reviewer_ref chéo cổng. Criterion G8-HUMAN-04, audit 2026-07-30/31."
        ),
        build_report=lambda: _evaluate_g8(
            cross_gate_refs={"G2": "IRB-CANARY", "G4": "SAME-PERSON", "G8": "SAME-PERSON", "G9": "PI-CANARY"}
        ),
        criterion_id="G8-HUMAN-04",
        expect_criterion_status=frozenset({"REVIEW"}),
        bad_overall_statuses=frozenset({G8Q.STATUS_REVIEWED}),
    ))

    return errors


# ════════════════════════════════════════════════════════════════════════════
# Chạy canary
# ════════════════════════════════════════════════════════════════════════════

def _clean_baselines(tmp_path: Path) -> Dict[str, Dict[str, Any]]:
    return {
        "G3": _evaluate_g3(tmp_path),
        "G4": _evaluate_g4(),
        "G8": _evaluate_g8(),
    }


_CLEAN_BEST_STATUS = {
    "G3": {G3Q.STATUS_CONFIRMED},
    "G4": {G4Q.STATUS_LOCKED},
    "G8": {G8Q.STATUS_REVIEWED},
}


def run_canary(tmp_path: Optional[Path] = None) -> Dict[str, Any]:
    """Chạy toàn bộ canary: (1) xác nhận gói TỐT xanh trên cả 3 cổng đã nối
    dây, (2) gài từng lỗi biết trước và kiểm cổng có bắt đúng không."""
    import tempfile

    if tmp_path is None:
        with tempfile.TemporaryDirectory(prefix="canary-nc-") as td:
            return run_canary(Path(td))

    baselines = _clean_baselines(tmp_path)
    clean_findings: List[str] = []
    for gate, report in baselines.items():
        status = report["status"]
        if status not in _CLEAN_BEST_STATUS[gate]:
            clean_findings.append(f"{gate}: gói TỐT không đạt trạng thái tốt nhất (status={status!r})")
        bad_rows = [
            r for r in report.get("automatic_criteria", []) + report.get("approval_criteria", [])
            if r["status"] not in ("PASS",)
        ]
        for row in bad_rows:
            clean_findings.append(f"{gate}: gói TỐT vẫn bị {row['id']}={row['status']} ({row['evidence']})")

    injected_results: List[Dict[str, Any]] = []
    for err in build_injected_errors(tmp_path):
        report = err.build_report()
        row = _row(report, err.criterion_id)
        caught = bool(
            row is not None
            and row["status"] in err.expect_criterion_status
            and report["status"] not in err.bad_overall_statuses
        )
        injected_results.append({
            "code": err.code,
            "gate": err.gate,
            "history": err.history,
            "criterion_id": err.criterion_id,
            "criterion_status": row["status"] if row else None,
            "overall_status": report["status"],
            "caught": caught,
        })

    all_caught = all(r["caught"] for r in injected_results)
    clean_ok = not clean_findings
    exit_code = 0 if (all_caught and clean_ok) else 1

    return {
        "study": STUDY,
        "clean_baseline_ok": clean_ok,
        "clean_baseline_findings": clean_findings,
        "clean_baseline_statuses": {g: r["status"] for g, r in baselines.items()},
        "injected_results": injected_results,
        "exit_code": exit_code,
    }


def _print_report(result: Mapping[str, Any]) -> None:
    print("=" * 78)
    print(f"CANARY ĐẦU-CUỐI — chuỗi cổng NGHIÊN CỨU G0–G10 (đề tài giả: {result['study']})")
    print("=" * 78)
    print()
    print("① Gói TỐT (baseline sạch) trên 3 cổng đã nối dây:")
    for gate, status in result["clean_baseline_statuses"].items():
        mark = "✅" if not result["clean_baseline_findings"] else "⚠️"
        print(f"   {mark} {gate}: {status}")
    if result["clean_baseline_findings"]:
        print("   PHÁT HIỆN (gói TỐT lẽ ra phải sạch nhưng không):")
        for f in result["clean_baseline_findings"]:
            print(f"     - {f}")
    print()
    print("② Lỗi gài BIẾT TRƯỚC — cổng nào phải bắt, đã bắt chưa:")
    for r in result["injected_results"]:
        mark = "✅ BẮT ĐƯỢC" if r["caught"] else "❌ LỌT"
        print(f"   [{mark}] {r['code']} — {r['gate']} — tiêu chí {r['criterion_id']}="
              f"{r['criterion_status']!r}, tổng trạng thái={r['overall_status']!r}")
        print(f"        Lý do lịch sử: {r['history']}")
    print()
    n_total = len(result["injected_results"])
    n_caught = sum(1 for r in result["injected_results"] if r["caught"])
    print(f"Tổng kết: {n_caught}/{n_total} lỗi gài bị bắt đúng cổng.")
    if result["exit_code"] == 0:
        print("CANARY XANH — chuỗi cổng NGHIÊN CỨU G0–G10 bắt đủ lỗi biết trước.")
    else:
        print("CANARY ĐỎ — có lỗi gài KHÔNG bị cổng nào bắt, hoặc gói TỐT không sạch.")
        print("KHÔNG tự sửa canary cho hết đỏ mà không xác minh gate thật đã bắt —")
        print("một lỗi lọt có thể là khoảng trống THẬT của hệ cổng, không phải bug canary.")
    print("=" * 78)


def main() -> int:
    result = run_canary()
    _print_report(result)
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
