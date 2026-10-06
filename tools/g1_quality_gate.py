#!/usr/bin/env python3
"""Hợp đồng chất lượng cho pipeline G1: Thiết kế và nền đề cương.

G1 có hai tầng khác nhau:

1. Tầng tự động: sinh đủ artifact, kiểm thiết kế, chuẩn báo cáo, truy nguyên
   bằng chứng và tính nhất quán kỹ thuật.
2. Tầng xác nhận phương pháp: PI/methodologist chốt thiết kế, mục tiêu, kết cục,
   quần thể, tính khả thi và đã đọc lại bằng chứng.

Không được dùng việc "đã sinh file" thay cho kết luận G1 đã qua. Module trả một
trong ba trạng thái:

- BLOCKED: lỗi kỹ thuật/liêm chính hoặc thiếu tiền đề G0.
- DRAFT_READY_NEEDS_HUMAN_REVIEW: phần tự động đạt, còn quyết định người thật.
- PASS_G1_CONFIRMED: cả phần tự động và xác nhận người thật đều đủ.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import annex2_quality_gate as A2X
import cong_song as CS
import placeholder_contract as PC
import skill_standards as S

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G1_CONFIRMED"
QUALITY_CONTRACT_VERSION = "G1-2026.1"

REQUIRED_ARTIFACT_KEYS = ("A1b", "A2", "A2b", "A13", "A13b")

_REQUIRED_SECTIONS: Dict[str, Sequence[str]] = {
    "A1b": (
        "PROJECT CHARTER",
        "Mục tiêu SMART",
        "Phạm vi",
        "Governance",
        "Milestone",
    ),
    "A2": (
        "ĐỀ CƯƠNG LÕI",
        "Quản trị tài liệu",
        "Cơ sở khoa học và khoảng trống",
        "Mục tiêu, câu hỏi và giả thuyết",
        "Thiết kế, địa điểm và thời gian",
        "Quần thể, tiêu chí chọn và tuyển mẫu",
        "Can thiệp/phơi nhiễm và đối chứng",
        "Kết cục và lịch đánh giá",
        "Cỡ mẫu",
        "Quản lý dữ liệu, bảo mật và chất lượng",
        "Đạo đức, an toàn và đăng ký",
        "Giám sát, sửa đổi và phổ biến",
        "Tài liệu tham khảo và phụ lục",
        "BẢNG THIẾT KẾ ỨNG VIÊN",
        "KIỂM SOÁT",
        "Chuẩn báo cáo",
        "Chuẩn đề cương/protocol",
        "SAP SKELETON",
    ),
    "A2b": (
        "EVIDENCE LEDGER",
        "Chiến lược tìm kiếm",
        "PMID/DOI",
        "Khoảng trống",
    ),
    "A13": (
        "RACI",
        "GANTT",
        "KINH PHÍ",
        "QUALITY-BY-DESIGN",
    ),
    "A13b": (
        "RISK REGISTER",
        "CAPA",
        "Chủ nhân",
        "Ngày rà",
    ),
}

_REPORTING_TOKENS: Dict[str, Sequence[str]] = {
    "rct": ("CONSORT 2025",),
    "cohort": ("STROBE",),
    "case_control": ("STROBE",),
    "cross_sectional": ("STROBE",),
    "diagnostic": ("STARD",),
    "sr_ma": ("PRISMA 2020",),
    "prediction": ("TRIPOD+AI",),
    "qualitative": ("COREQ", "SRQR"),
}

_PROTOCOL_TOKENS: Dict[str, Sequence[str]] = {
    "rct": ("SPIRIT 2025",),
    "sr_ma": ("PRISMA-P",),
}

_STANDARDS_BASIS = (
    {
        "standard": "EQUATOR Network",
        "scope": "Bản đồ guideline theo loại nghiên cứu",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "SPIRIT 2025",
        "scope": "Protocol thử nghiệm ngẫu nhiên",
        "pmid": "40294593",
        "doi": "10.1001/jama.2025.4486",
    },
    {
        "standard": "CONSORT 2025",
        "scope": "Báo cáo kết quả thử nghiệm ngẫu nhiên",
        "doi": "10.1136/bmj-2024-081123",
    },
    {
        "standard": A2X.VERSION,
        "scope": "Thử nghiệm có yếu tố phi tập trung, pragmatic và/hoặc RWD",
        "url": A2X.SOURCE_URL,
    },
    {
        "standard": "PRISMA-P 2015",
        "scope": "Protocol tổng quan hệ thống",
        "doi": "10.1186/2046-4053-4-1",
    },
    {
        "standard": "ICH E6(R3)",
        "scope": "Quality-by-design và GCP cho thử nghiệm lâm sàng",
        "url": "https://www.ema.europa.eu/en/ich-e6-good-clinical-practice-scientific-guideline",
    },
)

_REVIEW_ROLES = {
    "pi",
    "principal investigator",
    "research lead",
    "methodologist",
    "nhà phương pháp",
    "chủ nhiệm",
}


# Dấu hiệu «chưa điền» CŨ của G1 — chuỗi con trên value.upper(), không phân biệt hoa/thường. GIỮ NGUYÊN.
_PLACEHOLDER_MARKERS = ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN")
# Bổ sung cho vị từ QUYẾT ĐỊNH tiêu chí (_filled) — vá 03/10/2026 theo kiểm toán (đã chạy: mỗi chuỗi dưới đây
# nằm trong trường gate_params.G1 vẫn ra PASS_G1_CONFIRMED). Hợp marker riêng của G0 («___», «[TODO»,
# «SUY RA TỪ TOPIC» = ô P/I/E của khuôn A1, «XXX») để một trường dùng chung giữa G0/G1 được chấm cùng một
# kiểu; cộng ô mẫu của CHÍNH khuôn G1 mà hợp đồng chung chưa có: «[CHỜ …]» (thẻ chờ của SAP),
# «[từ §2 Bias Control]» (con trỏ đứng thay nội dung), «[tỷ lệ/trung bình]» (lựa chọn chưa chốt ở SAP §12)
# và mặt nạ ngày «[DD/MM/YYYY]». Cố ý KHÔNG đưa vào _present: _present còn dựng chữ cho artifact (_text, kể
# cả TIÊU ĐỀ PubMed ở A2b) — «47,XXX» trong một tiêu đề thật không được bị thay bằng [CẦN BỔ SUNG].
_FIELD_EXTRA_MARKERS = (
    "[TODO", "___", "SUY RA TỪ TOPIC", "XXX",
    "[CHỜ", "[TỪ §", "[TỶ LỆ/TRUNG BÌNH]", "[DD/MM/YYYY]",
)


def _chuoi_that(value: str, them: Sequence[str] = ()) -> bool:
    """Một CHUỖI có nội dung thật không: marker cũ G1 (nguyên văn) VÀ hợp đồng chung (mọi họ) [+ `them`]."""
    text = value.strip()
    if not text:
        return False
    upper = text.upper()
    if any(marker in upper for marker in _PLACEHOLDER_MARKERS):
        return False
    return PC.co_noi_dung_that(text, them=them)


def _present(value: Any) -> bool:
    """Có nội dung thật không — dùng để CHỌN NGUỒN (_first_present) và DỰNG CHỮ artifact (_text).

    Chuỗi: marker cũ + hợp đồng chung `placeholder_contract` (vá 03/10/2026: «[địa điểm]», «[TO BE
    COMPLETED]», «[DỰ THẢO] …», «<CẦN …>», «thuốc/can thiệp X», «……», chuỗi chỉ toàn ô tick… không còn
    được coi là đã điền). Danh sách/dict: GIỮ any() cũ — để _first_present không lặng lẽ bỏ một nguồn chỉ vì
    MỘT phần tử còn trống rồi lấy nguồn dự phòng; phần tử trống đó do _filled bắt khi chấm tiêu chí.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _chuoi_that(value)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _con_o_trong(value: Any) -> bool:
    """True khi giá trị (hoặc phần tử con) là chuỗi CÓ CHỮ nhưng còn dấu hiệu chưa điền (kể cả marker bổ sung)."""
    if isinstance(value, str):
        return bool(value.strip()) and not _chuoi_that(value, _FIELD_EXTRA_MARKERS)
    if isinstance(value, Mapping):
        return any(_con_o_trong(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_con_o_trong(v) for v in value)
    return False


def _filled(value: Any) -> bool:
    """Vị từ QUYẾT ĐỊNH tiêu chí G1: có nội dung thật VÀ không phần tử nào còn ô trống/nhãn nháp.

    Khác _present ở danh sách/dict («["Khoa A", "___"]» là CHƯA điền) và ở marker bổ sung.
    """
    return _present(value) and not _con_o_trong(value)


def _mo_ta(*sources: Any) -> str:
    """Nhãn bằng chứng 'có' / 'còn ô trống/nhãn nháp' / 'thiếu' cho giá trị chọn theo _first_present."""
    chosen = _first_present(*sources) if len(sources) > 1 else (sources[0] if sources else None)
    if _filled(chosen):
        return "có"
    if any(_con_o_trong(v) for v in (chosen, *sources)):
        return "còn ô trống/nhãn nháp"
    return "thiếu"


def _text(value: Any, fallback: str = "[CẦN BỔ SUNG]") -> str:
    if not _present(value):
        return fallback
    if isinstance(value, Mapping):
        for key in ("name", "text", "description", "general"):
            if _present(value.get(key)):
                return str(value[key]).strip()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(v).strip() for v in value if _present(v))
    return str(value).strip()


def _g1_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g1 = gp.get("G1")
    return g1 if isinstance(g1, Mapping) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if _present(value):
            return value
    return None


def _normalise_role(value: Any) -> str:
    return str(value or "").strip().casefold()


def _valid_review_time(value: Any) -> bool:
    """ISO-8601 thật và KHÔNG ở tương lai (VÁ 04/10/2026, G1-09: bản cũ nhận cả «2099-12-31»)."""
    if not _present(value):
        return False
    return CS.iso_khong_tuong_lai(value)


# Khoá xác nhận của gate_params.G1 — KHÔNG đưa vào dấu vân tay (chúng là phần xác nhận, không phải nội dung được chốt).
_KHOA_XAC_NHAN_G1 = frozenset({
    "design_confirmed", "protocol_core_confirmed", "bias_controls_confirmed", "feasibility_confirmed",
    "evidence_review_confirmed", "reviewed_by_role", "reviewed_at", "dau_van_tay_chot",
})

# Thiết kế hợp lệ cho từng loại câu hỏi G0 (G1-06): thiết kế cuối nằm ngoài tập ⇒ REVIEW (PI giải trình/đổi).
_THIET_KE_HOP_LE_THEO_CAU_HOI: Dict[str, frozenset] = {
    "treatment": frozenset({"rct", "cohort", "case_control", "sr_ma"}),
    "harm": frozenset({"cohort", "case_control", "cross_sectional", "sr_ma"}),
    "prognosis": frozenset({"cohort", "prediction", "sr_ma"}),
    "diagnosis": frozenset({"diagnostic", "sr_ma"}),
    "descriptive": frozenset({"cross_sectional", "cohort", "qualitative", "sr_ma"}),
    "qualitative": frozenset({"qualitative"}),
    "prediction_model": frozenset({"prediction", "cohort"}),
}

# Dòng đề cương lõi mang «[CẦN … G2…G10 …]» là việc của CỔNG SAU — không tính là ô trống của G1 (G1-02).
_HOAN_CHO_CONG_SAU = re.compile(r"\[CẦN[^\]]*\bG(?:[2-9]|10)\b[^\]]*\]")


def dau_van_tay_g1(meta: Mapping[str, Any], design: Mapping[str, Any]) -> str:
    """Dấu vân tay NỘI DUNG mà PI chốt ở G1: mọi quyết định trong gate_params.G1 (trừ khoá xác nhận) + thiết kế
    đang dùng + pin. Sinh lại đề cương với quyết định khác ⇒ dấu đổi ⇒ xác nhận cũ hết hiệu lực (VÁ 04/10/2026,
    G1-09). Không băm văn bản A2 (có dấu thời gian sinh ⇒ đổi mỗi lần chạy)."""
    g1 = {k: v for k, v in _g1_meta(meta).items() if k not in _KHOA_XAC_NHAN_G1}
    return CS.dau_van_tay(g1, str(design.get("internal_code") or ""), meta.get("design_code"))


def o_trong_pham_vi_g1(a2_text: str) -> List[str]:
    """Các dòng của PHẦN 0 (đề cương lõi) còn ô trống THUỘC PHẠM VI G1 — bỏ qua dòng hoãn cho cổng sau.

    VÁ 04/10/2026 (soát từng cổng, G1-02): G1 từng PASS_G1_CONFIRMED khi A2 còn hơn 80 «[CẦN» vì G1-AUTO-05 chỉ kiểm
    TIÊU ĐỀ. Nay mỗi dòng của đề cương lõi lấy từ một trường gate_params (khuôn đã có đủ khoá) hoặc ghi rõ cổng sau
    sẽ hoàn thiện; dòng thuộc G1 còn trống ⇒ G1 chưa xác nhận được."""
    text = a2_text or ""
    bat_dau = text.find("PHẦN 0 — ĐỀ CƯƠNG LÕI")
    if bat_dau < 0:
        return []
    ket_thuc = text.find("\n---", bat_dau)
    vung = text[bat_dau: ket_thuc if ket_thuc > 0 else len(text)]
    ra: List[str] = []
    for dong in vung.splitlines():
        d = dong.strip()
        if not d.startswith("-") and not d.startswith("[") and "[CẦN" not in d:
            continue
        if not PC.co_o_trong(d):
            continue
        if _HOAN_CHO_CONG_SAU.search(d) and not PC.co_o_trong(_HOAN_CHO_CONG_SAU.sub("", d)):
            continue
        ra.append(d[:140])
    return ra


def _list_complete(value: Any) -> bool:
    """True khi danh sách KHÔNG rỗng và MỌI mục là nội dung thật (không còn ô trống/nhãn nháp)."""
    return isinstance(value, (list, tuple)) and bool(value) and all(
        _filled(item) for item in value
    )


def _outcome_components(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """Chuẩn hóa kết cục chính thành bốn thành phần vận hành tối thiểu."""
    outcome = _primary_outcome(meta)
    g1 = _g1_meta(meta)
    if isinstance(outcome, Mapping):
        return {
            "name": _first_present(
                outcome.get("name"),
                outcome.get("text"),
                outcome.get("description"),
            ),
            "measure": _first_present(
                outcome.get("measure"),
                outcome.get("measurement"),
                outcome.get("definition"),
                outcome.get("unit"),
            ),
            "timepoint": _first_present(
                outcome.get("timepoint"),
                outcome.get("time_point"),
                outcome.get("assessment_time"),
            ),
            "type": _first_present(
                outcome.get("type"),
                outcome.get("scale_type"),
                outcome.get("data_type"),
            ),
        }
    return {
        "name": outcome,
        "measure": _first_present(
            meta.get("primary_outcome_measure"),
            g1.get("primary_outcome_measure"),
        ),
        "timepoint": _first_present(
            meta.get("primary_outcome_timepoint"),
            g1.get("primary_outcome_timepoint"),
        ),
        "type": _first_present(
            meta.get("primary_outcome_type"),
            g1.get("primary_outcome_type"),
        ),
    }


def _estimand_complete(g1: Mapping[str, Any]) -> bool:
    estimand = g1.get("estimand")
    if not isinstance(estimand, Mapping):
        return False
    required = (
        "population",
        "treatment_condition",
        "variable",
        "intercurrent_events_strategy",
        "population_summary_measure",
    )
    return all(_filled(estimand.get(key)) for key in required)


def build_protocol_core(
    *,
    study: str,
    topic: str,
    design: Mapping[str, Any],
    meta: Mapping[str, Any],
    generated_at: str,
) -> str:
    """Sinh khung đề cương lõi chung; chỗ thiếu luôn mang nhãn, không suy diễn.

    VÁ 04/10/2026 (soát từng cổng, G1-02): mọi dòng THUỘC PHẠM VI G1 nay lấy từ một trường gate_params (khuôn
    gate_contract đã có khoá) — bản cũ in cứng «[CẦN BỔ SUNG]» ở nhiều dòng mà study_meta không có chỗ nào để điền ⇒
    PI không thể hoàn thiện đề cương qua kênh chuẩn. Dòng thuộc cổng sau ghi rõ «Ở Gx» (o_trong_pham_vi_g1 bỏ qua).
    Giả thuyết lấy từ G0 (G0 là nơi chốt — G0-06)."""
    g1 = _g1_meta(meta)
    gp_all = meta.get("gate_params") if isinstance(meta.get("gate_params"), Mapping) else {}
    g0 = gp_all.get("G0") if isinstance(gp_all.get("G0"), Mapping) else {}
    test_type = str(g0.get("test_type") or "").strip().lower()
    if test_type in {"descriptive", "mô tả"}:
        gia_thuyet = "Nghiên cứu mô tả — không kiểm định giả thuyết (test_type=descriptive, chốt ở G0)"
    elif _filled(g0.get("hypothesis_h1")):
        gia_thuyet = (f"{_text(g0.get('hypothesis_h1'))} (chiều kỳ vọng: {_text(g0.get('expected_direction'))}; "
                      f"loại kiểm định: {_text(g0.get('test_type'))})")
    else:
        gia_thuyet = "[CẦN CHỐT Ở G0 — hypothesis_h1/expected_direction/test_type]"
    outcome = _outcome_components(meta)
    reporting = str(design.get("reporting_standard") or "[CẦN BỔ SUNG]")
    protocol = str(design.get("protocol_standard") or "[CẦN BỔ SUNG]")
    estimand = g1.get("estimand")
    estimand = estimand if isinstance(estimand, Mapping) else {}
    internal = str(design.get("internal_code") or "")
    design_specific_core = ""
    if internal == "qualitative":
        design_specific_core = f"""
- Hiện tượng trung tâm: {_text(g1.get("central_phenomenon"))}
- Cách tiếp cận định tính: {_text(g1.get("qualitative_approach"))}
- Phương pháp thu thập dữ liệu: {_text(g1.get("data_collection_method"))}
- Tiêu chí bão hòa/dừng thu thập: {_text(g1.get("saturation_criterion"))}
"""
    elif internal == "sr_ma":
        design_specific_core = f"""
- Nguồn thông tin: {_text(g1.get("information_sources"))}
- Chiến lược tìm kiếm: {_text(g1.get("search_strategy"))}
- Ngày tìm cuối cùng dự kiến: {_text(g1.get("search_last_date"))}
- Quy trình chọn nghiên cứu: {_text(g1.get("study_selection_process"))}
"""
    elif internal == "rct":
        design_specific_core = f"""
- Tạo chuỗi ngẫu nhiên (randomisation): {_text(g1.get("randomisation"))}
- Che giấu phân bổ (allocation concealment): {_text(g1.get("allocation_concealment"))}
- Làm mù (blinding/masking): {_text(g1.get("blinding"))}
"""
    elif internal == "diagnostic":
        design_specific_core = f"""
- Tình trạng đích (target condition): {_text(g1.get("target_condition"))}
- Tiêu chuẩn tham chiếu (reference standard): {_text(g1.get("reference_standard"))}
"""
    elif internal == "case_control":
        design_specific_core = f"""
- Định nghĩa ca bệnh: {_text(g1.get("case_definition"))}
- Nguồn và cách chọn nhóm chứng: {_text(g1.get("control_source"))}
"""
    elif internal == "prediction":
        design_specific_core = f"""
- Yếu tố dự báo ứng viên: {_text(g1.get("candidate_predictors"))}
- Khung thời gian dự báo (prediction horizon): {_text(g1.get("prediction_horizon"))}
"""

    def joined(value: Any) -> str:
        return _text(value)

    khoang_trong = _text(_first_present(g1.get("knowledge_gap"), g0.get("novelty_justification")))
    lieu_tuan_thu = _text(g1.get("intervention_dose_adherence"))

    # Dòng estimand chỉ thuộc phạm vi G1 khi là RCT (G1-HUMAN-05); thiết kế khác ghi N/A thay vì 5 ô «[CẦN]».
    if internal == "rct":
        estimand_dong = (
            f"- Estimand RCT hiện hành: dân số={_text(estimand.get('population'))};\n"
            f"  điều kiện điều trị={_text(estimand.get('treatment_condition'))};\n"
            f"  biến kết cục={_text(estimand.get('variable'))};\n"
            f"  biến cố xen ngang/chiến lược={_text(estimand.get('intercurrent_events_strategy'))};\n"
            f"  thước đo tổng hợp quần thể={_text(estimand.get('population_summary_measure'))}."
        )
    else:
        estimand_dong = "- Estimand (ICH E9(R1)) bắt buộc: N/A — không phải RCT."

    return f"""
## PHẦN 0 — ĐỀ CƯƠNG LÕI

> [DỰ THẢO] Đây là cấu trúc đề cương để nhóm nghiên cứu hoàn thiện và xác nhận.
> Sự có mặt của một mục không chứng minh nội dung khoa học của mục đó đã đúng.

### 0.1 Quản trị tài liệu
- Mã đề tài: `{study}`
- Tên đề tài: {_text(topic)}
- Phiên bản protocol: {_text(g1.get("protocol_version"))}
- Ngày tạo/cập nhật: {generated_at}
- Chủ nhiệm, nhà phương pháp, thống kê viên, quản lý dữ liệu: {_text(g1.get("team_roles"))}
- Tài trợ, bảo hiểm, xung đột lợi ích và vai trò nhà tài trợ: [CẦN HOÀN THIỆN Ở G2/G9]
- Chuẩn đề cương: {protocol}
- Chuẩn báo cáo kết quả dự kiến: {reporting}

### 0.2 Cơ sở khoa học và khoảng trống
- Vấn đề nghiên cứu và gánh nặng liên quan: {_text(g1.get("background_problem"))}
- Bằng chứng hiện có và giới hạn: {_text(g1.get("evidence_summary"))}
- Khoảng trống, tính mới và lý do cần nghiên cứu: {khoang_trong}
- Cân bằng lợi ích, nguy cơ và tính hợp lý khoa học: {_text(g1.get("benefit_risk_rationale"))}

### 0.3 Mục tiêu, câu hỏi và giả thuyết
- Mục tiêu: {joined(_objectives(meta))}
- Câu hỏi nghiên cứu/PICO-PECO-PIRD: {_text(g1.get("research_question"))}
- Giả thuyết chính và hướng hiệu ứng: {gia_thuyet}
- Kết cục chính neo mục tiêu: {_text(outcome["name"])}

### 0.4 Thiết kế, địa điểm và thời gian
- Thiết kế đã chọn: {_text(design.get("primary"))}
- Lý do chọn so với phương án thay thế: {_text(design.get("rationale"))}
- Địa điểm/bối cảnh: {_text(_first_present(meta.get("setting"), g1.get("setting")))}
- Thời gian nghiên cứu: {_text(_first_present(meta.get("study_period"), g1.get("study_period")))}
- Sơ đồ nghiên cứu và lịch tuyển-can thiệp-đánh giá: {_text(g1.get("study_schema_timeline"))}

### 0.5 Quần thể, tiêu chí chọn và tuyển mẫu
- Quần thể đích/nguồn: {_text(_first_present(meta.get("population"), g1.get("population")))}
- Tiêu chí chọn vào: {joined(g1.get("inclusion_criteria"))}
- Tiêu chí loại trừ: {joined(g1.get("exclusion_criteria"))}
- Chiến lược tuyển/chọn mẫu và tránh thiên lệch chọn mẫu: {_text(g1.get("recruitment_strategy"))}
- Đồng thuận tham gia và xử lý rút lui: [CẦN HOÀN THIỆN Ở G2]

### 0.6 Can thiệp/phơi nhiễm và đối chứng
- Can thiệp, phơi nhiễm hoặc index test: {_text(g1.get("intervention_or_exposure"))}
- Đối chứng/comparator hoặc lý do không áp dụng: {_text(g1.get("comparator"))}
- Liều/cường độ, thời lượng, đồng can thiệp, tuân thủ hoặc cách đo phơi nhiễm: {lieu_tuan_thu}
- Tiêu chí dừng/chuyển/điều trị cứu hộ nếu áp dụng: {_text(g1.get("stopping_rescue_rules"))}
{design_specific_core}

### 0.7 Kết cục và lịch đánh giá
- Kết cục chính: {_text(outcome["name"])}
- Định nghĩa/công cụ/đơn vị đo: {_text(outcome["measure"])}
- Thời điểm đánh giá chính: {_text(outcome["timepoint"])}
- Loại dữ liệu/thước đo: {_text(outcome["type"])}
- Kết cục phụ: {joined(g1.get("secondary_outcomes"))}
- Lịch theo dõi/đánh giá: {_text(g1.get("follow_up_schedule"))}

### 0.8 Cỡ mẫu
- Cỡ mẫu và power chính thức: [CẦN TÍNH Ở G3]
- Effect size/MCID, alpha, power, tỷ lệ biến cố, mất theo dõi và design effect:
  [CẦN NGUỒN PMID/DOI HOẶC PILOT — Ở G3]
- Phân bổ theo nhóm/tầng/trung tâm nếu có: [CẦN TÍNH Ở G3]

### 0.9 Quản lý dữ liệu, bảo mật và chất lượng
- CRF/data dictionary, nguồn dữ liệu và quy tắc kiểm tra: [CẦN HOÀN THIỆN G3/G5]
- Mã giả danh, phân quyền, audit trail, lưu trữ và hủy dữ liệu: [CẦN HOÀN THIỆN G2/G5]
- Critical-to-quality factors và quality tolerance limits: {_text(g1.get("critical_to_quality"))}
- Kế hoạch dữ liệu thiếu, sai lệch protocol và CAPA: [CẦN HOÀN THIỆN G4/G5]

### 0.10 Đạo đức, an toàn và đăng ký
- Phê duyệt IRB/IEC, ICF/waiver, bảo mật và bồi thường: [CẦN HỒ SƠ THẬT Ở G2]
- Đăng ký nghiên cứu/protocol trước mốc bắt buộc: [CẦN HỒ SƠ THẬT Ở G2]
- AE/SAE, giám sát an toàn, DMC/DSMB và quy tắc dừng nếu áp dụng: [CẦN HOÀN THIỆN Ở G2/G4]
- Nhóm dễ tổn thương và biện pháp bảo vệ: [CẦN ĐÁNH GIÁ Ở G2]

### 0.11 Giám sát, sửa đổi và phổ biến
- Monitoring/audit và phân công trách nhiệm: {_text(g1.get("monitoring_plan"))}
- Quy trình protocol amendment, cập nhật registry/IRB và thông báo bên liên quan: [CẦN HOÀN THIỆN Ở G2]
- Kế hoạch công bố kể cả kết quả âm, chia sẻ dữ liệu/mã và truyền đạt cho người tham gia:
  [CẦN HOÀN THIỆN Ở G9]
- Tác giả, contributorship, COI, tài trợ và khai báo AI: [CẦN XÁC NHẬN Ở G9]

### 0.12 Tài liệu tham khảo và phụ lục
- Evidence Ledger: `G1_A2b_EVIDENCE_LEDGER_{study}.md`
- Project Charter: `G1_A1b_PROJECT_CHARTER_{study}.md`
- Kế hoạch triển khai/RACI/kinh phí: `G1_A13_IMPLEMENTATION_PLAN_{study}.md`
- Risk Register/CAPA: `G1_A13b_RISK_REGISTER_{study}.md`
{estimand_dong}

> Cần bác sĩ kiểm chứng.

---
"""


def collect_evidence_identifiers(
    out_dir: Path,
    g0_checkpoint: Mapping[str, Any],
    effects: Iterable[Mapping[str, Any]],
) -> Dict[str, List[str]]:
    """Thu PMID/DOI đã xuất hiện thật; không tự tạo định danh mới."""
    pmids: List[str] = []
    dois: List[str] = []

    def add_unique(bucket: List[str], value: Any) -> None:
        text = str(value or "").strip()
        if text and text not in bucket:
            bucket.append(text)

    for effect in effects:
        add_unique(pmids, effect.get("pmid"))
        add_unique(dois, effect.get("doi"))

    pubmed = g0_checkpoint.get("pubmed_results")
    if isinstance(pubmed, Mapping):
        for key in ("pmids", "all_pmids", "pmids_used_as_seed"):
            values = pubmed.get(key)
            if isinstance(values, list):
                for value in values:
                    add_unique(pmids, value)

    candidates: List[Path] = []
    artifacts = g0_checkpoint.get("artifacts")
    if isinstance(artifacts, Mapping):
        raw = artifacts.get("A1_markdown")
        if raw:
            p = Path(str(raw))
            candidates.append(p if p.is_absolute() else Path.cwd() / p)
    candidates.extend(sorted(Path(out_dir).glob("G0_A1_PICO_FINER_*.md")))

    for path in candidates:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for value in re.findall(r"(?i)\bPMID\s*:?\s*(\d{5,9})\b", content):
            add_unique(pmids, value)
        for value in re.findall(r"(?i)\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", content):
            add_unique(dois, value.rstrip(".,;)"))

    return {"pmids": pmids, "dois": dois}


def _objectives(meta: Mapping[str, Any]) -> Any:
    g1 = _g1_meta(meta)
    return _first_present(meta.get("objectives"), g1.get("objectives"))


def _primary_outcome(meta: Mapping[str, Any]) -> Any:
    g1 = _g1_meta(meta)
    return _first_present(meta.get("primary_outcome"), g1.get("primary_outcome"))


def _metadata_tu_g0(out_dir: Path) -> Dict[str, str]:
    """Bảng PMID → «Tiêu đề — Tạp chí (Năm)» lấy từ CHÍNH kết quả tìm PubMed của G0.

    ★ ĐO 02/09/2026 trên đề tài thật C1a: sổ chứng cứ A2b để 12 dòng
    «[CẦN TRÍCH XUẤT METADATA]» — tức việc TAY của chủ nhiệm — trong khi đủ tiêu
    đề/tạp chí/năm của ĐÚNG 12 PMID đó đã nằm sẵn trong `G0_pubmed_raw.json` CÙNG
    THƯ MỤC, do chính G0 tra về trong cùng dây chuyền (đo được 12/12 phủ). Cùng
    lượt sinh, những PMID có effect size thì title ĐƯỢC điền, số còn lại thì
    không — tức năng lực đã có, chỉ thiếu một đoạn dây. Đây là kiểu «tự động hoá
    dở dang» đắt nhất: nó đẩy sang người thật một việc máy vừa làm xong ở dòng trên.

    Ranh giới cố ý: KHÔNG gọi mạng (đọc file đã có), KHÔNG suy đoán — PMID không
    có bản ghi thì GIỮ NGUYÊN nhãn [CẦN. Chỉ cột METADATA; trích xuất dữ liệu,
    thẩm định RoB và xác nhận nội dung vẫn là việc người thật.
    """
    raw_path = Path(out_dir) / "G0_pubmed_raw.json"
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    bang: Dict[str, str] = {}
    for nhom in raw.values():
        if not isinstance(nhom, list):
            continue
        for r in nhom:
            if not isinstance(r, dict):
                continue
            pmid = str(r.get("pmid") or "").strip()
            tieu_de = _o_bang(r.get("title"))
            if not pmid or not tieu_de:
                continue
            tap_chi = _o_bang(r.get("journal"))
            nam = _o_bang(r.get("year"))
            duoi = f"{tap_chi} ({nam})" if tap_chi and nam else (tap_chi or (f"({nam})" if nam else ""))
            bang[pmid] = f"{tieu_de} — {duoi}" if duoi else tieu_de
    return bang


def _o_bang(gia_tri: Any) -> str:
    """Chuỗi an toàn cho MỘT ô bảng markdown — dấu `|` trong tiêu đề sẽ phá cột."""
    return " ".join(str(gia_tri or "").split()).replace("|", "/")


def build_supporting_artifacts(
    *,
    study: str,
    topic: str,
    out_dir: Path,
    design: Mapping[str, Any],
    g0_checkpoint: Mapping[str, Any],
    effects: Sequence[Mapping[str, Any]],
    meta: Mapping[str, Any],
    generated_at: str,
) -> Dict[str, Path]:
    """Sinh bốn artifact G1 còn thiếu ngoài A2; mọi giả định đều mang nhãn."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    g1 = _g1_meta(meta)
    objectives = _text(_objectives(meta))
    primary_outcome = _text(_primary_outcome(meta))
    population = _text(_first_present(meta.get("population"), g1.get("population")))
    setting = _text(_first_present(meta.get("setting"), g1.get("setting")))
    study_period = _text(_first_present(meta.get("study_period"), g1.get("study_period")))
    identifiers = collect_evidence_identifiers(out_dir, g0_checkpoint, effects)
    query = _text(
        _first_present(
            g0_checkpoint.get("base_query"),
            meta.get("query_en"),
            topic,
        )
    )

    charter = f"""# PROJECT CHARTER (A1b) — {study}
> [DỰ THẢO] Sinh tự động {generated_at}; không thay xác nhận của PI/methodologist.

## Phạm vi
- Tên/chủ đề: {_text(topic)}
- Thiết kế dự kiến: {_text(design.get("primary"))}
- Quần thể: {population}
- Bối cảnh: {setting}
- Thời gian nghiên cứu: {study_period}
- Ngoài phạm vi: {_text(_first_present(meta.get("out_of_scope"), g1.get("out_of_scope")))}

## Mục tiêu SMART
- Mục tiêu: {objectives}
- Kết cục chính neo mục tiêu: {primary_outcome}

## Governance
| Quyết định | Vai trò chịu trách nhiệm | Bằng chứng |
|---|---|---|
| Chốt thiết kế G1 | PI/Methodologist | `study_meta.json: gate_params.G1` |
| Phê duyệt đạo đức G2 | IRB/IEC | Approval ledger có chữ ký |
| Khóa SAP G4 | Biostatistician/PI | SAP lock có chữ ký |
| Khóa dữ liệu | Data Manager/PI | Data Lock Memo |
| Bình duyệt G8 | Independent reviewer | Approval ledger đúng vai trò |

## Milestone
| Mốc | Sản phẩm | Điều kiện đóng |
|---|---|---|
| G0 | PICO/FINER + evidence seed | Câu hỏi và khoảng trống được xác nhận |
| G1 | A1b/A2/A2b/A13/A13b | Thiết kế + reporting map được PI/methodologist xác nhận |
| G2 | Ethics/registration package | IRB/IEC thật |
| G3–G4 | Cỡ mẫu + SAP | Tham số có nguồn + SAP lock |
| G5–G6 | Dữ liệu + phân tích | Data lock + phân tích theo SAP |
| G7–G10 | Báo cáo + kiểm duyệt + lắp ráp | A12/G8/G9 sạch và đúng vai trò |

> Cần bác sĩ kiểm chứng.
"""

    evidence_rows: List[str] = []
    for effect in effects:
        pmid = str(effect.get("pmid") or "").strip()
        if not pmid:
            continue
        evidence_rows.append(
            "| PMID:{pmid} | {title} | [CẦN TRÍCH XUẤT] | {effect} | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |".format(
                pmid=pmid,
                title=_text(effect.get("title")),
                effect=f"{effect.get('type', '?')}={effect.get('value', '?')}",
            )
        )
    effect_pmids = {str(effect.get("pmid") or "").strip() for effect in effects}
    meta_g0 = _metadata_tu_g0(out_dir)
    n_tu_g0 = 0
    for pmid in identifiers["pmids"]:
        if pmid in effect_pmids:
            continue
        md = meta_g0.get(str(pmid))
        if md:
            n_tu_g0 += 1
        evidence_rows.append(
            f"| PMID:{pmid} | {md or '[CẦN TRÍCH XUẤT METADATA]'} | "
            "[CẦN TRÍCH XUẤT] | [CẦN TRÍCH XUẤT] | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |"
        )
    for doi in identifiers["dois"]:
        evidence_rows.append(
            f"| DOI:{doi} | [CẦN TRÍCH XUẤT METADATA] | "
            "[CẦN TRÍCH XUẤT] | [CẦN TRÍCH XUẤT] | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |"
        )
    if not evidence_rows:
        evidence_rows.append(
            "| [CẦN PMID/DOI] | [CẦN TRÍCH XUẤT] | [CẦN] | [CẦN] | "
            "[CẦN] | CHƯA ĐỦ BẰNG CHỨNG TRUY NGUYÊN |"
        )

    gap_lines = g0_checkpoint.get("research_gaps")
    if isinstance(gap_lines, list) and gap_lines:
        gap_text = "\n".join(f"- {item}" for item in gap_lines)
    else:
        gap_text = "- [CẦN BỔ SUNG sau tổng quan có hệ thống]"
    ghi_chu_md = (
        f"> Cột **Metadata**: {n_tu_g0} dòng điền TỰ ĐỘNG từ kết quả tìm PubMed của G0 "
        "(`G0_pubmed_raw.json`) — chỉ là tiêu đề/tạp chí/năm, KHÔNG phải thẩm định. "
        "Các cột còn lại vẫn là việc người thật.\n"
    ) if n_tu_g0 else ""
    evidence = f"""# EVIDENCE LEDGER (A2b) — {study}
> [DỰ THẢO] Không tự gán GRADE; chưa đọc toàn văn phải giữ nhãn [CẦN].
{ghi_chu_md}
## Chiến lược tìm kiếm
- Nguồn tối thiểu: PubMed + ít nhất một nguồn phù hợp khác.
- Truy vấn G0: `{query}`
- Ngày rà: {generated_at[:10]}
- Giới hạn truy xuất/recall: [CẦN XÁC NHẬN]

## Bảng Evidence Ledger
| PMID/DOI | Tiêu đề | Thiết kế/N | Hiệu ứng chính | RoB | Trạng thái nội dung |
|---|---|---|---|---|---|
{chr(10).join(evidence_rows)}

## Khoảng trống nghiên cứu
{gap_text}

> Mỗi luận điểm trong protocol phải truy ngược được về dòng PMID/DOI phù hợp.
> Cần bác sĩ kiểm chứng.
"""

    # VÁ 04/10/2026 (G1-03): kinh phí lấy từ study_meta.gate_params.G1.budget (mỗi dòng: nhom/so_luong/don_gia/nguon/
    # thanh_tien/trang_thai); chưa khai thì giữ khuôn [CẦN] — máy KHÔNG bịa đơn giá.
    bud = g1.get("budget")
    kinh_phi_rows = "\n".join(
        "| " + " | ".join(_text(r.get(k), "[CẦN]").replace("|", "/") for k in (
            "nhom", "so_luong", "don_gia", "thanh_tien", "trang_thai")) + " |"
        for r in (bud if isinstance(bud, list) else []) if isinstance(r, Mapping)
    ) or (
        "| Nhân công | [CẦN] | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo |\n"
        "| Thu thập/xét nghiệm | [CẦN] | [CẦN] | [CẦN] | Dự thảo |\n"
        "| Dữ liệu/phần mềm | [CẦN] | [CẦN] | [CẦN] | Dự thảo |\n"
        "| Công bố/lưu trữ | [CẦN] | [CẦN] | [CẦN] | Dự thảo |"
    )

    plan = f"""# KẾ HOẠCH TRIỂN KHAI (A13) — {study}
> [DỰ THẢO] Đơn giá, nhân sự và thời lượng thật do chủ nhiệm/đơn vị xác nhận.

## RACI
| Công việc | PI | Methodologist | Biostatistician | Data Manager | Site team |
|---|---|---|---|---|---|
| Chốt thiết kế/protocol | A | R | C | I | C |
| Cỡ mẫu/SAP | A | C | R | C | I |
| IRB/consent | A | C | I | C | R |
| Thu thập/QC dữ liệu | A | I | C | R | R |
| Phân tích/báo cáo | A | C | R | C | I |

## GANTT theo cổng
| Chặng | Phụ thuộc | Thời lượng | Mốc nghiệm thu |
|---|---|---|---|
| G0–G1 | Không | [CẦN] | Thiết kế + protocol map |
| G2 | G1 | [CẦN] | IRB/registration |
| G3–G4 | G1 | [CẦN] | Cỡ mẫu + SAP lock |
| G5 | G2/G4 | [CẦN] | Pilot/SOP/data tools |
| G6–G10 | Data lock | [CẦN] | Analysis/report/review/closeout |

## KINH PHÍ
| Nhóm chi phí | Số lượng | Đơn giá có nguồn | Thành tiền | Trạng thái |
|---|---:|---:|---:|---|
{kinh_phi_rows}

## QUALITY-BY-DESIGN
- Critical-to-quality factors: quyền/an toàn người tham gia; tính tin cậy kết cục chính;
  tuyển mẫu; missing data; tuân thủ protocol; truy nguyên dữ liệu.
- Quality tolerance limits: [CẦN PI/methodologist ấn định trước triển khai].
- Monitoring và escalation: [CẦN xác nhận tại đơn vị].

> Cần bác sĩ kiểm chứng.
"""

    # VÁ 04/10/2026 (soát từng cổng, G1-03): cột «Ngày rà» từng do MÁY điền bằng ngày sinh tệp — một ngày rà chưa ai
    # rà. Nay để «[CẦN NGƯỜI RÀ]»; nhóm nghiên cứu ghi risk register thật vào study_meta.gate_params.G1.risk_register
    # (mỗi dòng: id/loai/rui_ro/xac_suat/tac_dong/giam_thieu/capa/chu_nhan/trang_thai/ngay_ra) — sửa tay .md bị ghi đè.
    review_date = "[CẦN NGƯỜI RÀ]"
    rr_meta = g1.get("risk_register")
    rr_rows_meta: List[str] = []
    if isinstance(rr_meta, list):
        for row in rr_meta:
            if not isinstance(row, Mapping):
                continue
            o = [_text(row.get(k), "[CẦN]").replace("|", "/") for k in (
                "id", "loai", "rui_ro", "xac_suat", "tac_dong", "giam_thieu", "capa", "chu_nhan", "trang_thai")]
            ngay = row.get("ngay_ra")
            o.append(str(ngay) if _valid_review_time(ngay) else "[CẦN NGƯỜI RÀ]")
            rr_rows_meta.append("| " + " | ".join(o) + " |")
    risk_rows = (
        "| G1-R01 | Thiết kế | Thiết kế không khớp câu hỏi/estimand | [CẦN] | Cao | "
        "Methodologist rà trước G2 | Sửa protocol có version; vô hiệu downstream cũ | "
        f"PI/Methodologist | Mở | {review_date} |",
        "| G1-R02 | Đạo đức | Hồ sơ không khớp phiên bản protocol | [CẦN] | Cao | "
        f"Hash/version mọi artifact | Dừng tuyển; amendment IRB | PI | Mở | {review_date} |",
        "| G1-R03 | Tuyển mẫu | Không đạt tốc độ tuyển dự kiến | [CẦN] | Cao | "
        "Feasibility log + nhiều điểm tuyển | CAPA tuyển mẫu; điều chỉnh timeline đã duyệt | "
        f"Site lead | Mở | {review_date} |",
        "| G1-R04 | Dữ liệu | Thiếu/sai dữ liệu kết cục chính | [CẦN] | Cao | "
        f"CRF validation + pilot | Query/CAPA; không tự điền dữ liệu | Data Manager | Mở | {review_date} |",
        "| G1-R05 | Thống kê | Outcome/SAP thay đổi sau xem dữ liệu | [CẦN] | Cao | "
        "Khóa SAP G4 | Ghi deviation; phân tích gắn nhãn thăm dò | "
        f"Biostatistician | Mở | {review_date} |",
        "| G1-R06 | Liêm chính | Trích dẫn ma/sai nội dung | [CẦN] | Cao | "
        f"Evidence Ledger + A12 | Loại/sửa nguồn; chạy lại A12 | Evidence reviewer | Mở | {review_date} |",
    )
    risks = f"""# RISK REGISTER SỐNG (A13b) — {study}
> [DỰ THẢO] Mức xác suất/tác động phải được nhóm nghiên cứu hiệu chỉnh.

| ID | Loại | Rủi ro | Xác suất | Tác động | Giảm thiểu trước | CAPA nếu xảy ra | Chủ nhân | Trạng thái | Ngày rà |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rr_rows_meta or risk_rows)}

## Quy tắc cập nhật
- Rà sau mỗi cổng và khi có protocol amendment.
- Ghi mọi thay đổi vào `study_meta.json → gate_params.G1.risk_register` (giữ dòng cũ, cập nhật trạng thái, ngày rà,
  nguyên nhân và CAPA) rồi chạy lại G1 — tệp .md này được SINH LẠI, sửa tay sẽ bị ghi đè (bản sửa tay được sao lưu).

> Cần bác sĩ kiểm chứng.
"""

    contents = {
        "A1b": charter,
        "A2b": evidence,
        "A13": plan,
        "A13b": risks,
    }
    paths = {
        "A1b": out_dir / f"G1_A1b_PROJECT_CHARTER_{study}.md",
        "A2b": out_dir / f"G1_A2b_EVIDENCE_LEDGER_{study}.md",
        "A13": out_dir / f"G1_A13_IMPLEMENTATION_PLAN_{study}.md",
        "A13b": out_dir / f"G1_A13b_RISK_REGISTER_{study}.md",
    }
    manifest_cu = _manifest_luot_truoc(out_dir)
    for key, path in paths.items():
        sao_luu_neu_sua_tay(path, manifest_cu.get(key), contents[key])
        path.write_text(contents[key], encoding="utf-8", newline="\n")
    return paths


def _manifest_luot_truoc(out_dir: Path) -> Dict[str, str]:
    """{khoá artifact: sha256} LÚC SINH của lượt run_g1_auto trước — rỗng nếu chưa có (= không biết).

    Chỉ tin `artifact_manifest_luc_sinh`: `artifact_manifest` của báo cáo kiểu cũ có thể được tính SAU khi người đã sửa
    tay (lượt chấm lại), dùng nó làm mốc sẽ coi bản sửa tay là «bản máy sinh» và đè mất."""
    try:
        rep_cu = json.loads((Path(out_dir) / "G1_QUALITY_REPORT.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    man = rep_cu.get("artifact_manifest_luc_sinh") if isinstance(rep_cu, dict) else None
    return {k: str(v.get("sha256")) for k, v in (man or {}).items() if isinstance(v, dict) and v.get("sha256")}


def sao_luu_neu_sua_tay(path: Path, sha_luot_truoc: Optional[str],
                        noi_dung_moi: Optional[str] = None) -> Optional[Path]:
    """Tệp đang có KHÁC bản lượt trước sinh ra (người đã sửa tay) ⇒ sao lưu `<tên>.bak-<thời điểm>` rồi mới ghi đè.

    VÁ 04/10/2026 (soát từng cổng, G1-03): mỗi lần chạy, G1 ghi đè A2/A1b/A2b/A13/A13b vô điều kiện — phần PI sửa tay
    mất trắng không một dòng cảnh báo. Trả đường dẫn bản sao lưu (None nếu không cần).

    sha_luot_truoc vắng = KHÔNG BIẾT bản lượt trước (báo cáo kiểu cũ chưa có mốc lúc sinh): không đoán «chưa ai sửa» —
    tệp nào khác nội dung sắp ghi thì sao lưu (một lần chuyển tiếp; từ lượt sau đã có mốc lúc sinh)."""
    path = Path(path)
    if not path.is_file():
        return None
    try:
        cu = path.read_bytes()
    except OSError:
        return None
    if sha_luot_truoc:
        if hashlib.sha256(cu).hexdigest() == sha_luot_truoc:
            return None
        ly_do = "đã bị sửa tay sau lượt G1 trước"
    else:
        if noi_dung_moi is not None and cu == noi_dung_moi.encode("utf-8"):
            return None
        ly_do = "khác bản sắp sinh mà không có mốc lúc sinh để biết ai sửa (báo cáo G1 kiểu cũ)"
    from datetime import datetime as _dt  # noqa: PLC0415

    goc = f"{path.name}.bak-{_dt.now().strftime('%Y%m%d-%H%M%S')}"
    bak, i = path.with_name(goc), 1
    while bak.exists():  # hai lượt trong cùng một giây không được đè bản sao lưu trước
        bak, i = path.with_name(f"{goc}-{i}"), i + 1
    bak.write_bytes(cu)
    print(f"  ⚠️  {path.name} {ly_do} — sao lưu ở {bak.name} trước khi sinh lại. "
          "Ghi nội dung đó vào study_meta.gate_params.G1 để không mất ở lượt sau.")
    return bak


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str = "",
) -> Dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def evaluate_g1_quality(
    *,
    design: Mapping[str, Any],
    artifact_texts: Mapping[str, str],
    artifact_paths: Mapping[str, Path],
    g0_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    evidence_identifiers: Mapping[str, Sequence[str]],
    guardrail_passed: bool = True,
    g0_song: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Đánh giá G1 theo tiêu chí máy và xác nhận người thật.

    `g0_song` = kết quả cong_song.trang_thai_song("G0", …) — nơi gọi trong sản xuất (run_g1_auto, evaluate_study)
    LUÔN truyền để G1-AUTO-01 dựa trên G0 CHẤM SỐNG; vắng thì đọc trạng thái lưu (chỉ dùng cho kiểm thử trực tiếp)."""
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []

    automatic.append(_criterion(
        "G1-AUTO-00",
        "Guardrail liêm chính G1 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa mọi lỗi PII, vượt cổng, nguồn hoặc disclaimer trước khi tiếp tục.",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G0-01 + G1-04 / CHUNG-A): bản cũ tin `quality_gate.status` LƯU SẴN của G0 (C1a:
    # lưu PASS 02/09, chấm sống DRAFT vì study_meta sửa 04/10) và — với checkpoint G0 kiểu cũ không có
    # quality_contract_version — bỏ qua cả trạng thái lồng bên trong, cho PASS chỉ vì guardrail sạch.
    g0_guard = g0_checkpoint.get("guardrail")
    g0_present = bool(g0_checkpoint)
    g0_quality = g0_checkpoint.get("quality_gate")
    g0_quality_status = (
        str(g0_quality.get("status") or "")
        if isinstance(g0_quality, Mapping)
        else ""
    )
    legacy_g0_ok = bool(
        isinstance(g0_guard, Mapping) and g0_guard.get("passed") is True
    )
    if isinstance(g0_song, Mapping) and g0_song.get("nguon") in (CS.NGUON_SONG, CS.NGUON_LOI):
        muc = g0_song.get("muc")
        luu_khac = (f"; bản LƯU={g0_song.get('trang_thai_luu')}"
                    if g0_song.get("trang_thai_luu") and g0_song.get("trang_thai_luu") != g0_song.get("status")
                    else "")
        if muc == "PASS":
            g0_status, g0_evidence = "PASS", f"G0 chấm sống={g0_song.get('status')}"
        elif muc == "BLOCKED":
            g0_status, g0_evidence = "BLOCK", f"G0 chấm sống=BLOCKED{luu_khac}"
        elif muc == CS.KHONG_DO_DUOC:
            g0_status, g0_evidence = "REVIEW", f"G0 KHÔNG ĐO ĐƯỢC ({g0_song.get('ly_do')}) — không phải «đạt»{luu_khac}"
        else:
            g0_status = "REVIEW"
            g0_evidence = f"G0 chấm sống={g0_song.get('status')} — câu hỏi nghiên cứu chưa được chốt{luu_khac}"
    elif not g0_present:
        g0_status = "REVIEW"
        g0_evidence = "Chưa có G0; chỉ được tạo dự thảo G1 độc lập"
    elif g0_quality_status == "PASS_G0_CONFIRMED":
        g0_status = "PASS"
        g0_evidence = "G0 quality_gate=PASS_G0_CONFIRMED (bản lưu — nơi gọi chưa chấm sống)"
    elif g0_quality_status == "BLOCKED":
        g0_status = "BLOCK"
        g0_evidence = "G0 quality contract đang BLOCKED"
    elif g0_quality_status:
        g0_status = "REVIEW"
        g0_evidence = (
            f"G0 quality_gate={g0_quality_status}; "
            "chưa có xác nhận câu hỏi nghiên cứu"
        )
    elif legacy_g0_ok:
        g0_status = "REVIEW"
        g0_evidence = "G0 kiểu cũ (guardrail sạch nhưng chưa có hợp đồng chất lượng) — chạy lại G0 để chấm"
    else:
        g0_status = "BLOCK"
        g0_evidence = "Có checkpoint G0 nhưng guardrail chưa đạt"
    automatic.append(_criterion(
        "G1-AUTO-01",
        "Tiền đề G0 có checkpoint và guardrail sạch",
        g0_status,
        g0_evidence,
        "Hoàn thiện G0 trước khi xác nhận G1.",
    ))

    internal = str(design.get("internal_code") or "")
    canonical_ok = internal in _REPORTING_TOKENS
    automatic.append(_criterion(
        "G1-AUTO-02",
        "Mã thiết kế thuộc vocabulary canonical",
        "PASS" if canonical_ok else "BLOCK",
        f"internal_code={internal!r}",
        "Chọn một mã thiết kế canonical được hệ hỗ trợ.",
    ))

    # VÁ 04/10/2026 (soát từng cổng): bác sĩ GHIM thiết kế ngoài 8 mã chuỗi hỗ trợ ⇒ run_g1_auto từng lặng lẽ dùng thiết
    # kế suy luận thay cho lựa chọn tường minh của bác sĩ. Nay G1 ghi `design.pin_bi_tu_choi` và cổng CHẶN tới khi PI
    # chọn lại.
    pin_tu_choi = str(design.get("pin_bi_tu_choi") or "").strip()
    automatic.append(_criterion(
        "G1-AUTO-02c",
        "Thiết kế bác sĩ đã ghim được chuỗi G0–G10 hỗ trợ (không bị thay bằng suy luận)",
        "BLOCK" if pin_tu_choi else "PASS",
        (f"pin «{pin_tu_choi}» ngoài 8 mã hỗ trợ; G1 đang dùng thiết kế suy luận «{internal}»"
         if pin_tu_choi else "không có pin bị từ chối"),
        "PI ghim lại study_meta.design_code bằng một trong rct/cohort/case_control/cross_sectional/diagnostic/sr_ma/"
        "prediction/qualitative có chủ ý, hoặc dùng agent chuyên trách cho thiết kế này (vd quasi-experimental → "
        "TREND, cải tiến chất lượng → SQUIRE 2.0, ca lâm sàng → CARE).",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G1-06): thiết kế cuối phải hợp với loại câu hỏi bác sĩ đã chốt ở G0 — bản cũ
    # bỏ qua G0 nên đề tài phân tích yếu tố liên quan bị dựng thành RCT mà không ai báo.
    gp_all = meta.get("gate_params") if isinstance(meta.get("gate_params"), Mapping) else {}
    g0_meta = gp_all.get("G0") if isinstance(gp_all.get("G0"), Mapping) else {}
    qt_g0 = S.chuan_hoa_question_type(g0_meta.get("question_type"))
    hop_le = _THIET_KE_HOP_LE_THEO_CAU_HOI.get(qt_g0 or "")
    if not hop_le:
        tk_status = "PASS"
        tk_evidence = "G0 chưa khai loại câu hỏi — không đối chiếu được (G1-AUTO-01 đã giữ G1 chờ G0 chốt)"
    elif internal in hop_le:
        tk_status, tk_evidence = "PASS", f"thiết kế «{internal}» hợp với loại câu hỏi G0 «{qt_g0}»"
    else:
        tk_status = "REVIEW"
        tk_evidence = (f"thiết kế «{internal}» không thuộc nhóm thiết kế của loại câu hỏi G0 «{qt_g0}» "
                       f"({', '.join(sorted(hop_le))})")
    automatic.append(_criterion(
        "G1-AUTO-02d",
        "Thiết kế hợp với loại câu hỏi đã chốt ở G0",
        tk_status,
        tk_evidence,
        "Đổi thiết kế cho khớp câu hỏi, hoặc sửa question_type ở G0 rồi chạy lại G1 (PI giải trình nếu cố ý).",
    ))

    annex2 = A2X.evaluate(meta, internal, "G1")
    annex2_issues = annex2["errors"] + annex2["missing"]
    # VÁ 04/10/2026 (soát từng cổng, G1-11 / QĐ-15 — mặc định an toàn chờ bác sĩ duyệt qua PR): RCT mà PI CHƯA KHAI
    # annex2.applicable từng được coi là «không áp dụng» và PASS im lặng. Nay phải khai tường minh (true/false).
    annex2_status = {"BLOCK": "BLOCK", "NEEDS_DECLARATION": "REVIEW"}.get(annex2["status"], "PASS")
    automatic.append(_criterion(
        "G1-AUTO-02b",
        f"{A2X.VERSION}: thiết kế phương pháp mới đủ fitness-for-purpose và giám sát",
        annex2_status,
        (
            "; ".join(annex2_issues)
            if annex2_issues
            else ("RCT chưa khai gate_params.G1.annex2.applicable (true/false) — không suy «không áp dụng»"
                  if annex2["status"] == "NEEDS_DECLARATION"
                  else f"status={annex2['status']}; methods={','.join(annex2['methods']) or 'không áp dụng'}")
        ),
        "Điền study_meta.gate_params.G1.annex2 (RCT: applicable=true kèm methodologies, hoặc applicable=false); "
        "không mở G1 khi thiếu.",
    ))

    reporting = str(design.get("reporting_standard") or "")
    expected_tokens = _REPORTING_TOKENS.get(internal, ())
    reporting_ok = bool(expected_tokens) and all(
        token.casefold() in reporting.casefold() for token in expected_tokens
    )
    official = S.reporting_standards_for(internal).get("primary", "")
    automatic.append(_criterion(
        "G1-AUTO-03",
        "Chuẩn báo cáo khớp thiết kế",
        "PASS" if reporting_ok else "BLOCK",
        f"đã chọn={reporting!r}; canon={official!r}",
        "Sửa reporting map theo skill_standards.py.",
    ))

    protocol = str(design.get("protocol_standard") or "")
    protocol_tokens = _PROTOCOL_TOKENS.get(internal, ())
    official_protocol = S.reporting_standards_for(internal).get("protocol", "")
    if protocol_tokens:
        protocol_ok = all(
            token.casefold() in protocol.casefold()
            for token in protocol_tokens
        )
    else:
        protocol_ok = bool(protocol) and protocol.casefold() == official_protocol.casefold()
    automatic.append(_criterion(
        "G1-AUTO-03b",
        "Chuẩn đề cương/protocol khớp thiết kế",
        "PASS" if protocol_ok else "BLOCK",
        f"đã chọn={protocol!r}; canon={official_protocol!r}",
        "Gắn chuẩn protocol riêng; không dùng checklist báo cáo kết quả thay thế.",
    ))

    ambiguous = bool(design.get("ambiguous"))
    automatic.append(_criterion(
        "G1-AUTO-04",
        "Thiết kế không còn suy luận mơ hồ",
        "REVIEW" if ambiguous else "PASS",
        "ambiguous=true" if ambiguous else "ambiguous=false",
        "PI/methodologist phải pin thiết kế sau khi đọc lại khoảng trống.",
    ))

    # «[Đã pin bởi bác sĩ — …]» (run_g1_auto._apply_design_pin) là nội dung HỢP LỆ của alternative_1/2 —
    # hợp đồng chung cố ý không khớp nó (không có quy tắc «ngoặc chung»), nên thiết kế đã pin vẫn PASS ở đây.
    primary_present = _filled(design.get("primary"))
    alternatives_complete = all(
        _filled(design.get(key))
        for key in ("alternative_1", "alternative_2")
    )
    rationale_present = _filled(design.get("rationale"))
    draft_rationale_present = bool(str(design.get("rationale") or "").strip())
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology CRITICAL):
    # ngưỡng >=7 hardcode cho MỌI thiết kế, nhưng run_g1_auto.py::
    # BIAS_CONTROLS["qualitative"] CHỦ Ý chỉ có 5 mục (4 miền trustworthiness
    # Lincoln & Guba — Credibility/Transferability/Dependability/
    # Confirmability — cộng Reporting bias; định tính KHÔNG dùng khung bias
    # định lượng, đã ghi chú tại nơi định nghĩa 2026-07-19) — khiến MỌI đề
    # tài định tính hợp lệ bị BLOCK cứng (main() coi BLOCKED là SystemExit
    # thật, không chỉ REVIEW). Xác nhận thực nghiệm: cả infer_study_design()
    # và _apply_design_pin() (2 đường sản xuất thật gán internal_code=
    # "qualitative") đều trả bias_controls dài 5 — một đề tài định tính ĐÃ
    # ĐIỀN ĐẦY ĐỦ mọi trường G1-HUMAN-01..08 vẫn BLOCK chỉ vì mục này.
    _MIN_BIAS_CONTROLS_BY_DESIGN = {"qualitative": 5}
    _DEFAULT_MIN_BIAS_CONTROLS = 7
    bias_controls = design.get("bias_controls")
    _min_bias = _MIN_BIAS_CONTROLS_BY_DESIGN.get(internal, _DEFAULT_MIN_BIAS_CONTROLS)
    bias_ok = isinstance(bias_controls, (list, tuple)) and len(bias_controls) >= _min_bias
    if (
        not alternatives_complete
        or not bias_ok
        or (ambiguous and not draft_rationale_present)
    ):
        design_comparison_status = "BLOCK"
    elif ambiguous:
        design_comparison_status = "REVIEW"
    elif not primary_present or not rationale_present:
        design_comparison_status = "BLOCK"
    else:
        design_comparison_status = "PASS"
    automatic.append(_criterion(
        "G1-AUTO-04b",
        "So sánh ít nhất ba phương án và kiểm soát đủ nhóm sai lệch/"
        "trustworthiness theo thiết kế",
        design_comparison_status,
        f"primary_present={primary_present}; "
        f"alternatives_complete={alternatives_complete}; "
        f"rationale_present={rationale_present}; "
        f"bias_controls={len(bias_controls) if isinstance(bias_controls, (list, tuple)) else 0}",
        (
            "PI/methodologist chọn một phương án chính từ bảng so sánh."
            if design_comparison_status == "REVIEW"
            else "Bổ sung 3 phương án, lý do chọn/loại và đủ 7 nhóm sai lệch."
        ),
    ))

    a2_text = artifact_texts.get("A2", "")
    method_conflicts: List[str] = []
    conflict_patterns = {
        "case_control": (
            "Phân tích chính: Cox regression",
            "Kaplan-Meier + Cox",
        ),
        "diagnostic": (
            "Calibration: Hosmer-Lemeshow; DCA",
            "EPP ≥ 10",
        ),
        "sr_ma": (
            "DerSimonian-Laird) nếu I²",
            "Fixed-effects nếu I² <",
        ),
        # THÊM 2026-07-30 (audit toàn diện G0-G10, G1-F3 — HIGH): dict này
        # trước đây chỉ có 4/8 mã thiết kế — HOÀN TOÀN THIẾU 'prediction',
        # đúng thiết kế mà chính g1_design_blocks.py (docstring) ghi nhận có
        # lịch sử rơi vào khuôn sr_ma nhiều lần (2026-07-17, 2026-07-21,
        # xem nhánh `elif internal == "prediction"` ở run_g1_auto.py — thêm
        # RIÊNG đúng vì trước đó rơi vào else viết cho sr_ma). Hai cụm dưới
        # xác nhận CHỈ xuất hiện trong nhánh sap_analysis_note của sr_ma
        # (run_g1_auto.py, không xuất hiện ở bất kỳ nhánh thiết kế nào khác) —
        # nếu SAP §4 của một đề tài 'prediction' chứa các cụm này, đó là dấu
        # hiệu khuôn sr_ma đã rò vào thay vì khuôn tiên lượng riêng.
        "prediction": (
            "Hartung-Knapp",
            "funnel plot/Egger",
        ),
        "qualitative": (
            "α: 0.05 (hai đuôi)",
            "Power: [CẦN]%",
            "Mô hình: ☐ Logistic",
        ),
    }
    for pattern in conflict_patterns.get(internal, ()):
        if pattern.casefold() in a2_text.casefold():
            method_conflicts.append(pattern)
    automatic.append(_criterion(
        "G1-AUTO-04c",
        "SAP không chứa khuôn phân tích mâu thuẫn với thiết kế",
        "BLOCK" if method_conflicts else "PASS",
        (
            f"mâu thuẫn={', '.join(method_conflicts)}"
            if method_conflicts
            else f"không phát hiện khuôn sai cho {internal}"
        ),
        "Sinh lại A2 bằng template theo đúng thiết kế; không vá một khuôn RCT cho mọi loại.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): mọi tiêu đề mục
    # trong _REQUIRED_SECTIONS và dòng disclaimer đều được các hàm sinh
    # artifact (build_protocol_core()/build_supporting_artifacts()) in CỨNG
    # VÔ ĐIỀU KIỆN — đã xác nhận thực nghiệm với meta RỖNG HOÀN TOÀN (mọi
    # trường bác sĩ điền tự do rơi về placeholder "[CẦN...]") vẫn PASS 5/5.
    # Tiêu chí này kiểm CẤU TRÚC (đủ mục/đủ disclaimer), không thẩm định nội
    # dung khoa học có đúng/đủ cho đề tài cụ thể hay không — module tự khai
    # đúng phạm vi này trong scope_statement; việc thẩm định nội dung thuộc
    # G1-HUMAN-01..08 (đọc gate_params.G1 thật). Không có ground truth máy
    # đọc được khác để thẩm định câu trả lời tự do dưới mỗi tiêu đề.
    artifact_failures: List[str] = []
    for key in REQUIRED_ARTIFACT_KEYS:
        path = artifact_paths.get(key)
        text = artifact_texts.get(key, "")
        if not path or not Path(path).exists() or not text.strip():
            artifact_failures.append(f"{key}: thiếu file/nội dung")
            continue
        missing_sections = [
            section for section in _REQUIRED_SECTIONS[key]
            if section.casefold() not in text.casefold()
        ]
        if missing_sections:
            artifact_failures.append(f"{key}: thiếu {', '.join(missing_sections)}")
        if "cần bác sĩ kiểm chứng" not in text.casefold():
            artifact_failures.append(f"{key}: thiếu disclaimer")
    automatic.append(_criterion(
        "G1-AUTO-05",
        "Đủ bộ A1b/A2/A2b/A13/A13b và các phần bắt buộc",
        "BLOCK" if artifact_failures else "PASS",
        "; ".join(artifact_failures) if artifact_failures else "5/5 artifact có mặt và qua kiểm cấu trúc",
        "Sinh lại hoặc sửa artifact G1 bị thiếu.",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G1-02): đếm ô trống THUỘC PHẠM VI G1 trong đề cương lõi (PHẦN 0 của A2).
    o_g1 = o_trong_pham_vi_g1(artifact_texts.get("A2", ""))
    automatic.append(_criterion(
        "G1-AUTO-07",
        "Đề cương lõi không còn ô trống thuộc phạm vi G1 (dòng hoãn cho cổng sau được bỏ qua)",
        "REVIEW" if o_g1 else "PASS",
        (f"{len(o_g1)} dòng còn trống: " + " | ".join(x.replace("|", "/") for x in o_g1[:4])
         + (" …" if len(o_g1) > 4 else "")) if o_g1 else "mọi dòng thuộc G1 của PHẦN 0 đã có nội dung",
        "Điền các khoá tương ứng ở study_meta.gate_params.G1 (team_roles, background_problem, evidence_summary, "
        "knowledge_gap, benefit_risk_rationale, study_schema_timeline, intervention_dose_adherence, "
        "stopping_rescue_rules, critical_to_quality, monitoring_plan và khoá theo thiết kế) rồi chạy lại G1; "
        "«N/A — <lý do>» là câu trả lời hợp lệ. KHÔNG sửa tay A2 (bị ghi đè khi chạy lại).",
    ))

    identifiers = list(evidence_identifiers.get("pmids") or []) + list(
        evidence_identifiers.get("dois") or []
    )
    ledger_text = artifact_texts.get("A2b", "")
    ledger_traceable = any(
        str(identifier).casefold() in ledger_text.casefold()
        for identifier in identifiers
    )
    automatic.append(_criterion(
        "G1-AUTO-06",
        # SỬA 2026-07-30 (audit toàn diện G0-G10, G1-F6): nhãn CŨ "có ít nhất
        # một định danh truy nguyên" dễ đọc nhầm là định danh đã được XÁC
        # MINH tồn tại thật — hàm này chỉ so khớp CHUỖI PMID/DOI xuất hiện
        # case-insensitive trong text Evidence Ledger, KHÔNG gọi PubMed/
        # Crossref. Xác minh tồn tại thật thuộc cổng A12 (kiem-chung-trich-dan),
        # không phải G1 (G1 chạy thường xuyên, không có rate-limit/cache
        # mạng như A12 — quyết định phạm vi, không thêm gọi mạng ở đây).
        "Có định danh PMID/DOI khớp chuỗi trong Evidence Ledger (CHƯA xác "
        "minh qua PubMed/Crossref — việc đó thuộc cổng A12 kiem-chung-trich-dan)",
        "PASS" if identifiers and ledger_traceable else "REVIEW",
        (
            f"{len(identifiers)} PMID/DOI được thu, ledger_traceable={ledger_traceable} "
            "(khớp CHUỖI, KHÔNG gọi PubMed để xác minh tồn tại)"
        ),
        "Bổ sung Evidence Ledger có PMID/DOI thật; không bịa nguồn.",
    ))

    g1 = _g1_meta(meta)
    pinned_design = _first_present(meta.get("design_code"), g1.get("design"))
    # VÁ 04/10/2026 (soát từng cổng, G1-12): so pin SAU KHI chuẩn hoá qua bảng bí danh dùng chung — ghim «RCT» hay
    # «systematic_review» từng bị REVIEW vĩnh viễn vì so chuỗi nguyên văn với mã đã chuẩn hoá.
    pin_matches = _present(pinned_design) and S.ma_thiet_ke_chuoi(str(pinned_design)) == internal
    # Vá 03/10/2026: design_rationale không bắt buộc, nhưng ĐÃ khai thì không được còn ô trống/nhãn nháp
    # (kiểm toán: trường này chưa từng được chấm — «[CẦN …]»/«___» ở đây vẫn PASS).
    rationale_residue = _con_o_trong(g1.get("design_rationale"))
    # VÁ 04/10/2026 (soát từng cổng, G1-01): `is True` — bool() từng coi chuỗi «false»/«chưa»/«[CẦN PI XÁC NHẬN]» là
    # PI ĐÃ xác nhận thiết kế.
    design_confirmed = g1.get("design_confirmed") is True and pin_matches and not rationale_residue
    human.append(_criterion(
        "G1-HUMAN-01",
        "PI/methodologist xác nhận thiết kế",
        "PASS" if design_confirmed else "REVIEW",
        f"pin={pinned_design!r}; design_confirmed={g1.get('design_confirmed')!r}"
        + ("; design_rationale=còn ô trống/nhãn nháp" if rationale_residue else ""),
        "Điền design_code/gate_params.G1.design và design_confirmed=true."
        + (" Gỡ ô trống/nhãn nháp còn sót trong design_rationale." if rationale_residue else ""),
    ))

    objectives = _objectives(meta)
    outcome = _outcome_components(meta)
    # Kết cục chính dạng dict: ô trống ở BẤT KỲ khoá nào (kể cả khoá đồng nghĩa measure/unit…) đều chặn — nếu
    # không, «measure: "___"» bị _first_present bỏ qua rồi lấy «unit» thay, lặng lẽ qua cổng.
    outcome_complete = all(_filled(value) for value in outcome.values()) and not _con_o_trong(
        _primary_outcome(meta)
    )
    research_question = g1.get("research_question")
    # Trường KHÔNG bắt buộc (vá 03/10/2026): đã khai thì không được còn ô trống/nhãn nháp.
    optional_fields = [("secondary_outcomes", g1.get("secondary_outcomes"))]
    if internal not in ("qualitative", "sr_ma"):  # hai thiết kế này BẮT BUỘC research_question (chấm riêng)
        optional_fields.append(("research_question", research_question))
    optional_residue = [key for key, value in optional_fields if _con_o_trong(value)]
    optional_note = (
        f"; còn ô trống/nhãn nháp ở trường tuỳ chọn: {', '.join(optional_residue)}"
        if optional_residue else ""
    )
    if internal == "qualitative":
        objective_ok = (
            _list_complete(objectives)
            and _filled(research_question)
            and _filled(g1.get("central_phenomenon"))
            and _filled(g1.get("qualitative_approach"))
            and not optional_residue
        )
        objective_evidence = (
            f"objectives={'đủ' if _list_complete(objectives) else 'thiếu'}; "
            f"research_question={_mo_ta(research_question)}; "
            f"central_phenomenon={_mo_ta(g1.get('central_phenomenon'))}; "
            f"qualitative_approach={_mo_ta(g1.get('qualitative_approach'))}"
            + optional_note
        )
        objective_action = (
            "Điền objectives, research_question, central_phenomenon và "
            "qualitative_approach; không ép kết cục định lượng."
        )
    else:
        objective_ok = (
            _list_complete(objectives)
            and outcome_complete
            and (internal != "sr_ma" or _filled(research_question))
            and not optional_residue
        )
        objective_evidence = (
            f"objectives={'đủ' if _list_complete(objectives) else 'thiếu'}; "
            f"outcome_name={_mo_ta(outcome['name'])}; "
            f"measure={_mo_ta(outcome['measure'])}; "
            f"timepoint={_mo_ta(outcome['timepoint'])}; "
            f"type={_mo_ta(outcome['type'])}"
        )
        if _con_o_trong(_primary_outcome(meta)):
            objective_evidence += "; primary_outcome còn ô trống/nhãn nháp"
        if internal == "sr_ma":
            objective_evidence += (
                f"; research_question={_mo_ta(research_question)}"
            )
        objective_evidence += optional_note
        objective_action = (
            "Điền objectives và primary_outcome gồm tên, định nghĩa/công cụ đo, "
            "thời điểm và loại dữ liệu."
        )
    human.append(_criterion(
        "G1-HUMAN-02",
        (
            "Mục tiêu, câu hỏi và hiện tượng trung tâm đã chốt"
            if internal == "qualitative"
            else "Mục tiêu và kết cục chính vận hành đã chốt"
        ),
        "PASS" if objective_ok else "REVIEW",
        objective_evidence,
        objective_action,
    ))

    population = _first_present(meta.get("population"), g1.get("population"))
    setting = _first_present(meta.get("setting"), g1.get("setting"))
    period = _first_present(meta.get("study_period"), g1.get("study_period"))
    inclusion = g1.get("inclusion_criteria")
    exclusion = g1.get("exclusion_criteria")
    recruitment = g1.get("recruitment_strategy")
    if internal == "sr_ma":
        sources = g1.get("information_sources")
        frame_ok = (
            _list_complete(inclusion)
            and _list_complete(exclusion)
            and _list_complete(sources)
            and all(
                _filled(value)
                for value in (
                    g1.get("search_strategy"),
                    g1.get("search_last_date"),
                    g1.get("study_selection_process"),
                )
            )
        )
        frame_evidence = (
            f"eligibility={'đủ' if _list_complete(inclusion) and _list_complete(exclusion) else 'thiếu'}; "
            f"information_sources={'có' if _list_complete(sources) else 'thiếu'}; "
            f"search_strategy={_mo_ta(g1.get('search_strategy'))}; "
            f"search_last_date={_mo_ta(g1.get('search_last_date'))}; "
            f"selection_process={_mo_ta(g1.get('study_selection_process'))}"
        )
        frame_action = (
            "Điền eligibility, information_sources, search_strategy, "
            "search_last_date và study_selection_process theo PRISMA-P."
        )
    else:
        frame_ok = (
            all(_filled(v) for v in (population, setting, period, recruitment))
            and _list_complete(inclusion)
            and _list_complete(exclusion)
        )
        frame_evidence = (
            f"population={_mo_ta(meta.get('population'), g1.get('population'))}; "
            f"inclusion={'có' if _list_complete(inclusion) else 'thiếu'}; "
            f"exclusion={'có' if _list_complete(exclusion) else 'thiếu'}; "
            f"recruitment={_mo_ta(recruitment)}; "
            f"setting={_mo_ta(meta.get('setting'), g1.get('setting'))}; "
            f"study_period={_mo_ta(meta.get('study_period'), g1.get('study_period'))}"
        )
        frame_action = (
            "Điền population, inclusion/exclusion criteria, recruitment_strategy, "
            "setting và study_period."
        )
    human.append(_criterion(
        "G1-HUMAN-03",
        (
            "Tiêu chí chọn, nguồn tìm và quy trình chọn nghiên cứu đã xác định"
            if internal == "sr_ma"
            else "Quần thể, tiêu chí chọn, tuyển mẫu, bối cảnh và thời gian đã xác định"
        ),
        "PASS" if frame_ok else "REVIEW",
        frame_evidence,
        frame_action,
    ))

    intervention = g1.get("intervention_or_exposure")
    comparator = g1.get("comparator")
    follow_up = g1.get("follow_up_schedule")
    if internal == "qualitative":
        treatment_frame_ok = all(
            _filled(value)
            for value in (
                g1.get("qualitative_approach"),
                g1.get("data_collection_method"),
                g1.get("saturation_criterion"),
            )
        )
        treatment_evidence = (
            f"qualitative_approach={_mo_ta(g1.get('qualitative_approach'))}; "
            f"data_collection_method={_mo_ta(g1.get('data_collection_method'))}; "
            f"saturation_criterion={_mo_ta(g1.get('saturation_criterion'))}"
        )
        treatment_action = (
            "Điền qualitative_approach, data_collection_method và saturation_criterion."
        )
    elif internal == "sr_ma":
        treatment_frame_ok = all(
            _filled(value) for value in (intervention, comparator)
        )
        treatment_evidence = (
            f"intervention_or_exposure={_mo_ta(intervention)}; "
            f"comparator={_mo_ta(comparator)}"
        )
        treatment_action = (
            "Điền intervention_or_exposure và comparator hoặc lý do N/A trong PICO."
        )
    else:
        # «N/A — <lý do>» (vd C1a: «N/A — thiết kế mô tả cắt ngang…») là câu trả lời HỢP LỆ — hành động bên dưới
        # cho phép «lý do N/A»; hợp đồng chung không có luật «N/A» nên vá 03/10/2026 không đổi hành vi này.
        treatment_frame_ok = all(
            _filled(value) for value in (intervention, comparator, follow_up)
        )
        treatment_evidence = (
            f"intervention_or_exposure={_mo_ta(intervention)}; "
            f"comparator={_mo_ta(comparator)}; "
            f"follow_up_schedule={_mo_ta(follow_up)}"
        )
        treatment_action = (
            "Điền intervention_or_exposure, comparator (hoặc lý do N/A) "
            "và follow_up_schedule."
        )
    human.append(_criterion(
        "G1-HUMAN-04",
        (
            "Phương pháp thu thập và quy tắc bão hòa đã xác định"
            if internal == "qualitative"
            else "Can thiệp/phơi nhiễm, đối chứng và lịch theo dõi đã xác định"
        ),
        "PASS" if treatment_frame_ok else "REVIEW",
        treatment_evidence,
        treatment_action,
    ))

    estimand_ok = internal != "rct" or _estimand_complete(g1)
    human.append(_criterion(
        "G1-HUMAN-05",
        "Estimand đủ 5 thuộc tính khi là RCT",
        "PASS" if estimand_ok else "REVIEW",
        (
            "N/A cho thiết kế không phải RCT"
            if internal != "rct"
            else f"estimand_complete={estimand_ok}"
        ),
        "Điền population, treatment condition, variable, intercurrent-event strategy và population summary measure.",
    ))

    feasibility_ok = g1.get("feasibility_confirmed") is True
    protocol_ok = g1.get("protocol_core_confirmed") is True
    bias_review_ok = g1.get("bias_controls_confirmed") is True
    human.append(_criterion(
        "G1-HUMAN-06",
        "Đề cương lõi, kiểm soát sai lệch và tính khả thi được xác nhận",
        "PASS" if feasibility_ok and protocol_ok and bias_review_ok else "REVIEW",
        f"protocol_core_confirmed={protocol_ok}; "
        f"bias_controls_confirmed={bias_review_ok}; "
        f"feasibility_confirmed={feasibility_ok}",
        "PI/methodologist rà toàn bộ protocol core, bảng bias và tính khả thi rồi bật ba cờ xác nhận.",
    ))

    evidence_review_ok = g1.get("evidence_review_confirmed") is True and bool(identifiers)
    human.append(_criterion(
        "G1-HUMAN-07",
        "Khoảng trống và nội dung trích dẫn đã được người thật đọc lại",
        "PASS" if evidence_review_ok else "REVIEW",
        f"evidence_review_confirmed={g1.get('evidence_review_confirmed') is True}; "
        f"identifiers={len(identifiers)}",
        "Evidence reviewer/PI xác nhận nội dung nguồn và khoảng trống.",
    ))

    role = _normalise_role(g1.get("reviewed_by_role"))
    # VÁ 04/10/2026 (soát từng cổng, G1-09 / CHUNG-C): xác nhận phải GẮN với đúng các quyết định đang chốt — sinh lại
    # đề cương với quyết định khác mà cờ cũ vẫn PASS là lỗi; ngày ở tương lai không nhận.
    dau_hien_tai = dau_van_tay_g1(meta, design)
    xn_ok, xn_ly_do = CS.xac_nhan_gan_noi_dung(
        {"reviewed_at": g1.get("reviewed_at"), "dau_van_tay": g1.get("dau_van_tay_chot")}, dau_hien_tai)
    review_ok = role in _REVIEW_ROLES and _valid_review_time(g1.get("reviewed_at")) and xn_ok
    human.append(_criterion(
        "G1-HUMAN-08",
        "Có vai trò, thời điểm rà phương pháp và xác nhận gắn đúng nội dung",
        "PASS" if review_ok else "REVIEW",
        f"reviewed_by_role={role or 'thiếu'}; reviewed_at={g1.get('reviewed_at') or 'thiếu'}; {xn_ly_do}",
        "Ghi reviewed_by_role, reviewed_at dạng ISO-8601 (không ở tương lai) và "
        f"dau_van_tay_chot=\"{dau_hien_tai}\" (dấu của các quyết định G1 đang chốt); không cần lưu danh tính.",
    ))

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
    artifact_manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        artifact_path = Path(path)
        if not artifact_path.exists():
            continue
        artifact_manifest[key] = {
            "path": str(artifact_path),
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        }
    return {
        "schema_version": "1.1",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "artifact_manifest": artifact_manifest,
        "dau_van_tay_hien_tai": dau_hien_tai,
        "standards_basis": list(_STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G1_CONFIRMED chỉ xác nhận thiết kế/reporting map và bộ artifact "
            "G1 theo bằng chứng đã ghi; không thay IRB, khóa SAP, dữ liệu thật hoặc "
            "thẩm định khoa học độc lập. Checklist báo cáo đánh giá tính đầy đủ "
            "của mô tả, không tự chứng minh chất lượng thiết kế hay thực hiện."
        ),
    }


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    """Ghi báo cáo G1 máy-đọc được đồng thời với bản Markdown dễ kiểm toán."""
    out_dir = Path(out_dir)
    json_path = out_dir / "G1_QUALITY_REPORT.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )

    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G1 — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`",
        "",
        "## Kiểm tra tự động",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{row['evidence'].replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Xác nhận người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("human_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{row['evidence'].replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Manifest artifact",
        "| Artifact | Đường dẫn | SHA-256 |",
        "|---|---|---|",
    ])
    for key, item in report.get("artifact_manifest", {}).items():
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
        source = (
            f"PMID:{item['pmid']}" if item.get("pmid") else ""
        )
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
    md_path = out_dir / "G1_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


TEN_ARTIFACT_G1 = {
    "A1b": "G1_A1b_PROJECT_CHARTER_{s}.md",
    "A2": "G1_A2_PROTOCOL_DESIGN_{s}.md",
    "A2b": "G1_A2b_EVIDENCE_LEDGER_{s}.md",
    "A13": "G1_A13_IMPLEMENTATION_PLAN_{s}.md",
    "A13b": "G1_A13b_RISK_REGISTER_{s}.md",
}


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return v if isinstance(v, dict) else {}


def evaluate_study(study: str, out_dir: Path, *, write: bool = True) -> Dict[str, Any]:
    """Chấm LẠI G1 từ checkpoint + artifact đã lưu (không gọi mạng, không sinh lại artifact).

    VÁ 04/10/2026 (soát từng cổng, G1-10 / CHUNG-A): G1 là cổng DUY NHẤT không có hàm này ⇒ cổng sau (G2, G3…) chỉ
    đọc được trạng thái G1 LƯU SẴN — G1 PASS rồi bác sĩ sửa study_meta, G2 vẫn khoá được trên G1 đã cũ. Nay
    cong_song.trang_thai_song("G1") chấm sống được. G0 tiền đề cũng được chấm sống (không tin bản lưu)."""
    out_dir = Path(out_dir)
    cp = _doc_json(out_dir / "G1_checkpoint.json")
    meta = _doc_json(out_dir / "study_meta.json")
    g0_cp = _doc_json(out_dir / "G0_checkpoint.json")
    design = dict(cp.get("design") or {}) if isinstance(cp.get("design"), Mapping) else {}
    paths = {k: out_dir / ten.format(s=study) for k, ten in TEN_ARTIFACT_G1.items()}
    texts: Dict[str, str] = {}
    for k, pth in paths.items():
        try:
            texts[k] = pth.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            texts[k] = ""
    effects = cp.get("effect_size_samples") if isinstance(cp.get("effect_size_samples"), list) else []
    evidence = collect_evidence_identifiers(out_dir, g0_cp, [e for e in effects if isinstance(e, Mapping)])
    guard = cp.get("guardrail")
    guardrail_passed = isinstance(guard, Mapping) and guard.get("passed") is True
    g0_song = CS.trang_thai_song("G0", study, out_dir)
    report = evaluate_g1_quality(
        design=design, artifact_texts=texts, artifact_paths={k: v for k, v in paths.items() if v.exists()},
        g0_checkpoint=g0_cp, meta=meta, evidence_identifiers=evidence, guardrail_passed=guardrail_passed,
        g0_song=g0_song,
    )
    if not cp:
        report["status"] = STATUS_BLOCKED
        report["pending_actions"] = ["Chưa có G1_checkpoint.json — chạy run_g1_auto.py trước."] + list(
            report.get("pending_actions") or [])
    # Giữ manifest LÚC SINH của lượt run_g1_auto (để phát hiện sửa tay) — chấm lại không được ghi đè mốc đó.
    cu = _doc_json(out_dir / "G1_QUALITY_REPORT.json")
    report["artifact_manifest_luc_sinh"] = cu.get("artifact_manifest_luc_sinh") or {}
    if write:
        write_quality_report(study, out_dir, report)
        if cp:
            import pipeline_freshness as PF  # noqa: PLC0415 — import lười

            cp["quality_contract_version"] = QUALITY_CONTRACT_VERSION
            cp["quality_gate"] = {**report, "dau_van_tay_luc_cham": report.get("dau_van_tay_hien_tai")}
            PF.ghi_checkpoint_giu_moc_sinh(out_dir / "G1_checkpoint.json",
                                           json.dumps(cp, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    """CLI CHẤM LẠI G1 từ tệp đã lưu (04/10/2026; trước đó chỉ đọc báo cáo cũ — vá 01/09/2026).

    ★ VÌ SAO TỒN TẠI: G1 là cổng DUY NHẤT trong 11 cổng không có CLI — gọi
    `python3 tools/g1_quality_gate.py --study X` trước bản vá này thì Python
    chỉ import module rồi THOÁT 0 IM LẶNG, bỏ qua toàn bộ đối số: người gọi
    đọc mã thoát 0 tưởng «đã chấm, sạch» trong khi KHÔNG một luật nào chạy —
    đúng họ «yên tâm giả» (BH32) và «công cụ vẫn chạy, thứ cần kiểm thì không
    bao giờ được kiểm».

    Từ 04/10/2026 (soát từng cổng, G1-10): evaluate_study() lắp lại đủ input từ checkpoint + artifact đã lưu nên CLI
    CHẤM LẠI THẬT (G0 tiền đề chấm sống). MẶC ĐỊNH CHỈ IN — không ghi báo cáo/checkpoint: bộ test và agent gọi CLI này
    trên đề tài thật (C1a) không được âm thầm đổi tệp trong exports/. Muốn lưu kết quả chấm lại: thêm `--ghi`.
    Không có checkpoint → mã 2, không bao giờ im lặng thoát 0.
    """
    import argparse

    ap = argparse.ArgumentParser(description="Chấm lại hợp đồng chất lượng cổng G1 từ tệp đã lưu (mặc định chỉ in)")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--ghi", action="store_true",
                    help="Ghi kết quả chấm lại vào G1_QUALITY_REPORT.* và G1_checkpoint.json (mặc định chỉ in)")
    ap.add_argument("--no-write", action="store_true", help="(tương thích cũ — nay là mặc định) chỉ in, không ghi")
    a = ap.parse_args()
    study = re.sub(r"[^\w\-]", "_", a.study.strip().replace(" ", "-"))
    out_dir = Path(__file__).resolve().parent.parent / "exports" / study
    if not (out_dir / "G1_checkpoint.json").exists():
        print(f"⛔ Chưa có G1_checkpoint.json cho đề tài '{study}' — G1 chưa từng chạy nên chưa từng được chấm.")
        print("   Chạy: python3 tools/run_g1_auto.py --study", study)
        return 2
    try:
        bao = evaluate_study(study, out_dir, write=bool(a.ghi) and not a.no_write)
    except Exception as e:  # noqa: BLE001 — chấm hỏng ⇒ mã 2, không bao giờ im lặng thoát 0
        print(f"⛔ Không chấm được G1: {type(e).__name__}: {e}")
        return 2
    status = str(bao.get("status") or "KHÔNG RÕ")
    print(f"G1 QUALITY [{study}]: {status}")
    print("  (CHẤM LẠI từ checkpoint + artifact đã lưu; "
          + ("đã ghi báo cáo/checkpoint" if a.ghi and not a.no_write else "chỉ in, không ghi — thêm --ghi để lưu")
          + "; sinh lại artifact: python3 tools/run_g1_auto.py --study " + study + ")")
    for nhom, ten in (("automatic_criteria", "Tiêu chí máy"), ("human_criteria", "Xác nhận người thật")):
        muc = bao.get(nhom) or []
        print(f"  — {ten}: {len(muc)} mục")
        for c in muc:
            st = str(c.get("status") or "")
            dau = {"PASS": "✅", "BLOCK": "❌"}.get(st, "◌")
            chi_tiet = str(c.get('evidence') or c.get('detail') or c.get('label') or '')[:100]
            print(f"    {dau} {c.get('id')}: {chi_tiet}")
    for hanh_dong in (bao.get("pending_actions") or [])[:8]:
        print(f"  → CẦN: {str(hanh_dong)[:110]}")
    print("Cần bác sĩ kiểm chứng.")
    return {STATUS_BLOCKED: 3, STATUS_DRAFT_READY: 2, STATUS_CONFIRMED: 0}.get(status, 2)


if __name__ == "__main__":
    raise SystemExit(main())
