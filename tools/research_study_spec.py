#!/usr/bin/env python3
"""Chuẩn hóa StudySpec và kiểm tính đầy đủ/ngữ nghĩa của đề cương G10.

`study_meta.json` trước đây là một dict mở, còn checkpoint G0-G9 dùng nhiều
schema khác nhau. Module này tạo một biểu diễn chuẩn duy nhất, tương thích ngược,
để assembler, validator và giao diện cùng đọc một nguồn sự thật.

Module không tự tạo dữ kiện khoa học hoặc phê duyệt. Trường chưa có vẫn rỗng và
được đưa vào gói quyết định cần bác sĩ/chủ nhiệm xác nhận.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import placeholder_contract as PC
import skill_standards as S

SCHEMA_VERSION = "1.0"

_PLACEHOLDERS = {
    "",
    "?",
    "none",
    "null",
    "n/a",
    "na",
    "tbd",
    "todo",
    "unknown",
    "chưa có",
    "chưa xác định",
}

# «<» đứng trước một số là phép so sánh lâm sàng («nằm viện < 3 ngày hoặc tuổi > 80»), không phải ô mẫu «<điền tên>»
# — che trước khi hỏi vị từ chung (nhánh ngoặc nhọn của họ NHAN có từ «ngày/tên»).
_SO_SANH_TRUOC_SO_RE = re.compile(r"<(?=\s*[\d.,])")


def is_present(value: Any) -> bool:
    """True khi giá trị có nội dung thật, không phải placeholder/trạng thái.

    SỬA 03/10/2026 (hợp đồng ô trống chung `tools/placeholder_contract.py`): chuỗi phải qua thêm
    `co_noi_dung_that` (MỌI họ dấu hiệu) — trước đây «[nơi thực hiện]», «___», «thuốc/can thiệp X», «[TO BE
    COMPLETED]», «……», «CHƯA XÁC NHẬN», «[Cần bổ sung]», «<CẦN ĐIỀN>» được coi là CÓ: vừa làm StudySpec báo đủ
    (G10-AUTO-06 PASS) vừa được `run_g10_assemble._text()` in nguyên văn như giá trị thật. Chỉ AND thêm — giữ
    `_PLACEHOLDERS`, tiền tố «[CẦN»/«[DỰ THẢO]», số 0 vẫn là giá trị thật, dict/list vẫn theo any()."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 23, phát hiện #1):
        # bản gốc dùng `value > 0`, coi số 0 (một giá trị THẬT, hợp lệ — vd
        # kinh phí=0 cho nghiên cứu hồi cứu không tốn chi phí, dropout=0%)
        # ngang hàng với "chưa nhập". `None` đã bị loại ở nhánh trên, nên
        # MỌI số thật còn lại (kể cả 0 và số âm) đều là dữ liệu đã có —
        # không được đoán thêm điều kiện "dương mới tính là có".
        return True
    if isinstance(value, str):
        text = value.strip()
        lowered = text.lower()
        return (
            bool(text)
            and lowered not in _PLACEHOLDERS
            and not text.startswith(("[CẦN", "[DỰ THẢO]"))
            and PC.co_noi_dung_that(_SO_SANH_TRUOC_SO_RE.sub("‹", text))
        )
    if isinstance(value, dict):
        return any(is_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(is_present(v) for v in value)
    return True


def _get(obj: Optional[dict], *keys: str, default=None):
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def _first(*values):
    for value in values:
        if is_present(value):
            return value
    return None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value] if is_present(value) else []


def _as_dict(value: Any, *, text_key: str = "description") -> dict:
    if isinstance(value, dict):
        return dict(value)
    if is_present(value):
        return {text_key: value}
    return {}


def _kinh_phi_g1(rows: Any) -> Optional[str]:
    """Tóm tắt kinh phí từ gate_params.G1.budget — CÙNG nguồn với bảng KINH PHÍ của A13; None khi chưa khai dòng nào
    HOẶC còn dòng thiếu ô (nhom/so_luong/don_gia/thanh_tien/trang_thai).

    06/10/2026: mục «Dự trù kinh phí» của đề cương G10 in «[CẦN]» dù PI đã khai kinh phí ở G1 (doctrine
    ke-hoach-trien-khai: kinh phí THẬT ghi ở gate_params.G1.budget, A13 sinh lại từ đó). Bảng còn ô trống thì đề cương
    giữ «[CẦN]» (ô nào thiếu xem A13) — không in một dự trù dở dang, máy KHÔNG bịa đơn giá/thành tiền."""
    dong = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict):
            continue
        if not all(is_present(r.get(k)) for k in ("nhom", "so_luong", "don_gia", "thanh_tien", "trang_thai")):
            return None
        nguon = f" (nguồn đơn giá: {r['nguon']})" if is_present(r.get("nguon")) else ""
        dong.append(f"{r['nhom']}: số lượng {r['so_luong']} × đơn giá {r['don_gia']}{nguon} = {r['thanh_tien']} "
                    f"— {r['trang_thai']}")
    return ("; ".join(dong) + " (bảng KINH PHÍ của A13)") if dong else None


def _outcome(value: Any) -> dict:
    if isinstance(value, dict):
        out = dict(value)
        out["name"] = _first(
            out.get("name"),
            out.get("label"),
            out.get("outcome"),
            out.get("ten"),
        )
        out["definition"] = _first(
            out.get("definition"),
            out.get("operational_definition"),
            out.get("dinh_nghia"),
            out.get("measure"),  # 06/10/2026: khối kết cục chính của G1 (name/measure/timepoint/type)
        )
        out["timepoint"] = _first(
            out.get("timepoint"),
            out.get("measurement_time"),
            out.get("thoi_diem"),
        )
        out["source"] = _first(
            out.get("source"),
            out.get("data_source"),
            out.get("instrument"),
        )
        out["variable_name"] = _first(
            out.get("variable_name"),
            out.get("field_name"),
            out.get("variable"),
        )
        return out
    return {"name": value} if is_present(value) else {}


def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("label") or "").strip()
    return str(value or "").strip()


def _dedupe(values: Iterable[Any]) -> List[Any]:
    seen: set[str] = set()
    out: List[Any] = []
    for value in values:
        marker = _name(value).casefold() or str(value).casefold()
        if not marker or marker in seen:
            continue
        seen.add(marker)
        out.append(value)
    return out


def _kc_tu_g0(g0_quyet: dict) -> dict:
    """Kết cục chính PI chốt ở G0 (tên + cách đo + thời điểm) dưới dạng khối kết cục."""
    if not is_present(g0_quyet.get("primary_outcome")):
        return {}
    return {"name": g0_quyet.get("primary_outcome"), "definition": g0_quyet.get("primary_outcome_measure"),
            "timepoint": g0_quyet.get("primary_outcome_timepoint")}


def _pico_tu_g0(g0_quyet: dict) -> dict:
    """PICO/PECO PI đã chốt ở G0 (population/intervention/comparison/primary_outcome) — chỉ để HIỂN THỊ khi study_meta
    không khai khối pico; không dùng làm nguồn suy cho trường khác (G1 tinh hơn G0)."""
    pico = {"p": g0_quyet.get("population"), "i_e": g0_quyet.get("intervention"),
            "c": g0_quyet.get("comparison"), "o": g0_quyet.get("primary_outcome")}
    return {k: v for k, v in pico.items() if is_present(v)}


def _canonical_meta(meta: Optional[dict]) -> dict:
    """Cho phép StudySpec nằm trực tiếp hoặc trong key `study_spec`."""
    meta = dict(meta or {})
    nested = meta.get("study_spec")
    if isinstance(nested, dict):
        merged = dict(meta)
        merged.update(nested)
        return merged
    return meta


def build_study_spec(study: str, checkpoints: Dict[str, dict],
                     meta: Optional[dict] = None) -> dict:
    """Hợp nhất checkpoint + study_meta thành StudySpec chuẩn, không bịa dữ kiện."""
    raw = _canonical_meta(meta)
    # THÊM 06/10/2026 (soát từng cổng — CHUNG-F/CHUNG-H, đo trên bản sao C1a): quyết định PI đã CHỐT ở G0/G1 (và G3)
    # nằm ở study_meta.gate_params — nguồn của A2 PHẦN 0, WHO TRDS và bộ chấm G1. StudySpec cũ chỉ đọc khoá CẤP CAO của
    # study_meta ⇒ C1a (G1 đủ câu hỏi, mục tiêu, bối cảnh, quần thể, tiêu chuẩn, cách tuyển, kết cục) vẫn bị báo thiếu
    # D02/D03/D05–D08 và đề cương thống nhất in «[CẦN BỔ SUNG]»: bác sĩ phải khai LẠI điều đã chốt. Nay là nguồn KẾ
    # TIẾP — khoá cấp cao (PI ghi đè có chủ ý) vẫn thắng; G1 trước G0 (G1 chốt sau, tinh hơn).
    _gp_all = _as_dict(raw.get("gate_params"))
    g0_quyet = _as_dict(_gp_all.get("G0"))
    g1_quyet = _as_dict(_gp_all.get("G1"))
    g3_quyet = _as_dict(_gp_all.get("G3"))
    g0 = checkpoints.get("G0") or {}
    g1 = checkpoints.get("G1") or {}
    g2 = checkpoints.get("G2") or {}
    g3 = checkpoints.get("G3") or {}
    g4 = checkpoints.get("G4") or {}
    g5 = checkpoints.get("G5") or {}
    g6 = checkpoints.get("G6") or {}
    g7 = checkpoints.get("G7") or {}

    document = _as_dict(raw.get("document"))
    pico = _as_dict(_first(raw.get("pico"), raw.get("pico_or_equivalent")))
    objectives_raw = _first(raw.get("objectives"), _get(raw, "objectives", "specific"),
                            g1_quyet.get("objectives"))
    objectives = _as_list(objectives_raw)
    aim = _first(raw.get("aim"), _get(raw, "objectives", "general"))

    outcomes_input = _as_list(raw.get("outcomes"))
    # Cả KHỐI theo đúng thứ tự bộ chấm G1 đọc (g1_quality_gate._primary_outcome: cấp cao → G1) rồi G0 — một định nghĩa
    # «kết cục chính» cho mọi cổng; không ghép trường của hai khối (lớp cấp cao thiếu tên làm chính G1 tụt DRAFT).
    primary = _outcome(_first(raw.get("primary_outcome"),
                              outcomes_input[0] if outcomes_input else None,
                              g1_quyet.get("primary_outcome"), _kc_tu_g0(g0_quyet)))
    if not primary and "primary_outcome" in (_get(g5, "crf_columns", default=[]) or []):
        primary = {"name": "primary_outcome", "variable_name": "primary_outcome"}
    secondary_input = _first(raw.get("secondary_outcomes"),
                             outcomes_input[1:] if outcomes_input else None,
                             g1_quyet.get("secondary_outcomes"))
    secondary = [_outcome(item) for item in _as_list(secondary_input)]
    secondary = [item for item in secondary if item]

    intervention = _as_dict(raw.get("intervention"))
    exposure = _as_dict(_first(
        raw.get("exposure"),
        raw.get("main_predictor"),
        pico.get("i_e"),
    ))
    exposure_intervention = dict(exposure)
    exposure_intervention.update(intervention)
    exposure_intervention["description"] = _first(
        intervention.get("description"),
        intervention.get("name"),
        exposure.get("description"),
        exposure.get("name"),
        pico.get("i_e"),
    )
    exposure_intervention["comparator"] = _first(
        raw.get("comparator"),
        intervention.get("comparator"),
        pico.get("c"),
    )
    # THÊM 06/09/2026 (bác sĩ: "đảm bảo hoàn thiện... đạt tiêu chuẩn quốc tế"):
    # SPIRIT 2025 mục 9b (lý do chọn comparator) + 15d (điều trị đi kèm được
    # phép/cấm) — trước đây KHÔNG có chỗ chứa nào trong `sec_thietke()` (§6 chỉ
    # có tên thiết kế). Dùng CHUNG khối exposure_intervention đã có (cùng khái
    # niệm PICO I/C với intervention/comparator ở trên), không tạo namespace mới.
    exposure_intervention["comparator_rationale"] = _first(
        raw.get("comparator_rationale"), intervention.get("comparator_rationale"))
    exposure_intervention["concomitant_care"] = _first(
        raw.get("concomitant_care_policy"), intervention.get("concomitant_care"))
    # THÊM 06/10/2026 (soát từng cổng — CHUNG-H RCT / CHUNG-F): quyết định PI đã CHỐT ở G0/G1 (gate_params — cũng là
    # nguồn của A2 PHẦN 0 và WHO TRDS #13) là nguồn kế tiếp cho can thiệp/đối chứng của đề cương G10. Bản cũ chỉ đọc
    # khoá riêng của study_meta ⇒ PI phải khai LẠI, chưa khai thì §6 mang «[CẦN BỔ SUNG]» dù G1 đã chốt.
    if not is_present(exposure_intervention.get("description")):
        exposure_intervention["description"] = _first(
            "; ".join(str(x) for x in (g1_quyet.get("intervention_or_exposure"),
                                       g1_quyet.get("intervention_dose_adherence")) if is_present(x)) or None,
            g0_quyet.get("intervention"))
    if not is_present(exposure_intervention.get("comparator")):
        exposure_intervention["comparator"] = _first(g1_quyet.get("comparator"), g0_quyet.get("comparison"))

    instrument = _as_dict(raw.get("instrument"), text_key="name")
    variables = _first(raw.get("variables"), _get(g5, "crf_columns"))
    sample_meta = _as_dict(raw.get("sample_size"))
    analysis_meta = _as_dict(_first(raw.get("analysis"), raw.get("sap")))
    bias_meta = _as_dict(raw.get("bias"))
    ethics_meta = _as_dict(raw.get("ethics"))
    governance_meta = _as_dict(
        _first(raw.get("data_governance"), raw.get("data_management"))
    )
    registration_meta = _as_dict(raw.get("registration"))
    resources_meta = _as_dict(raw.get("resources"))
    design_specific = _as_dict(raw.get("design_specific"))

    pmids = _dedupe(
        _as_list(_get(g7, "pmids_used_as_seed"))
        + _as_list(_get(g0, "pmids_used_as_seed"))
        + _as_list(raw.get("pmids"))
    )
    dois = _dedupe(_as_list(raw.get("dois")))

    design_code = S.canonical_design_code(_first(
        raw.get("design_code"),
        _get(g1, "design", "internal_code"),
        g3.get("design_code"),
        g5.get("design_code"),
        g6.get("design_code"),
    ))
    reporting = S.reporting_standards_for(design_code)

    # THÊM 06/09/2026: bổ sung field cho `design_specific` — trước đây chỉ
    # `_DESIGN_FIELD_REQUIREMENTS["rct"]` tra `randomization`/`allocation_
    # concealment`/`harms`/`stopping_rules` để liệt "quyết định còn treo"
    # (R01-R03), nhưng KHÔNG nơi nào trong `run_g10_assemble.py` render các
    # field này vào văn bản đề cương thật — bác sĩ điền xong vẫn không thấy
    # trong §6. Bổ sung field mù/lịch trình/PPI còn thiếu + fallback tên phẳng
    # (design_specific là dict PASSTHROUGH, không có logic chuẩn hoá nào khác).
    for _key, _aliases in (
        ("randomization", ("randomization_sequence_method", "randomization_method")),
        ("randomization_type", ("randomization_type",)),
        ("allocation_concealment", ("allocation_concealment_mechanism",)),
        ("allocation_access", ("allocation_access_control",)),
        ("blinding_who", ("blinding_who",)),
        ("blinding_how", ("blinding_how",)),
        ("unblinding_procedure", ("unblinding_procedure",)),
        ("harms", ("harms_definition",)),
        ("stopping_rules", ("stopping_rules",)),
        ("schedule", ("schedule_description",)),
        ("ppi_plan", ("ppi_plan",)),
    ):
        if is_present(design_specific.get(_key)):
            continue
        for _alias in _aliases:
            if is_present(raw.get(_alias)):
                design_specific[_key] = raw.get(_alias)
                break
            # Bác sĩ có thể nest TÊN DÀI (giữ nguyên, không đổi tên) ngay dưới
            # design_specific.* thay vì key ngắn chuẩn hoá — chấp nhận cả hai.
            if _alias != _key and is_present(design_specific.get(_alias)):
                design_specific[_key] = design_specific.get(_alias)
                break
    # THÊM 06/10/2026 (CHUNG-H RCT / CHUNG-F): khoá theo thiết kế PI đã chốt ở G1 (gate_params.G1) là nguồn kế tiếp —
    # không bắt khai lại ở design_specific. Tác hại (R03): RCT có kế hoạch an toàn G2 (G2_SAFETY_PLAN — định nghĩa/phân
    # độ AE-SAE, báo cáo, DMC) mà PI đã xác nhận ⇒ trỏ sang kế hoạch đó, không chép nội dung.
    for _key, _g1_keys in (("randomization", ("randomisation", "randomization")),
                           ("allocation_concealment", ("allocation_concealment",)),
                           ("blinding", ("blinding", "masking")),
                           ("stopping_rules", ("stopping_rescue_rules",)),
                           ("schedule", ("study_schema_timeline", "follow_up_schedule")),
                           ("reference_standard", ("reference_standard",)),
                           ("target_condition", ("target_condition",)),
                           ("search_strategy", ("search_strategy",))):
        if is_present(design_specific.get(_key)):
            continue
        _gia_tri = _first(*(g1_quyet.get(k) for k in _g1_keys))
        if is_present(_gia_tri):
            design_specific[_key] = _gia_tri
    if design_code == "diagnostic" and not is_present(design_specific.get("index_test")):
        _gia_tri = g1_quyet.get("intervention_or_exposure")
        if is_present(_gia_tri):
            design_specific["index_test"] = _gia_tri
    if not is_present(design_specific.get("harms")) and \
            _as_dict(_as_dict(raw.get("gate_params")).get("G2")).get("safety_plan_confirmed") is True:
        design_specific["harms"] = (f"Theo kế hoạch an toàn G2 (G2_SAFETY_PLAN_{study}.md — định nghĩa/phân độ "
                                    "biến cố bất lợi, báo cáo, hội đồng theo dõi), PI đã xác nhận")
    # Thiết kế quan sát KHÔNG có ngẫu nhiên hoá/làm mù/can thiệp — sự thật CẤU
    # TRÚC suy trực tiếp từ design_code (không phải nội dung lâm sàng bịa), CÙNG
    # khuôn với `theory.not_applicable_rationale` (P22) và các cờ *_not_applicable
    # của run_g3_auto.py/run_g4_auto.py. RCT thì KHÔNG tự gán — phải điền thật.
    if design_code and design_code != "rct":
        design_specific["not_applicable_rationale"] = (
            f"Thiết kế {design_code} không có can thiệp/ngẫu nhiên hoá/làm mù — "
            "các mục SPIRIT 2025 9b/11/15a/15d/18/21-24 không áp dụng."
        )
    else:
        design_specific["not_applicable_rationale"] = _first(
            raw.get("intervention_design_not_applicable"),
            design_specific.get("not_applicable_rationale"))

    spec = {
        "schema_version": SCHEMA_VERSION,
        "study_id": study,
        "title": _first(raw.get("title"), g0.get("topic"), study),
        "document": {
            "version": _first(
                document.get("version"),
                raw.get("document_version"),
                raw.get("protocol_version"),
                raw.get("version"),
            ),
            "date": _first(
                document.get("date"),
                raw.get("document_date"),
                raw.get("version_date"),
                raw.get("updated_at"),
            ),
            "status": _first(document.get("status"), raw.get("document_status"),
                             S.STATUS_TAGS["DU_THAO"]),
        },
        "summary": _first(raw.get("summary"), raw.get("protocol_summary")),
        "rationale": {
            "problem": _first(
                raw.get("problem_statement"),
                raw.get("background"),
                raw.get("rationale"),
                g1_quyet.get("background_problem"),
            ),
            "evidence_gap": _first(
                raw.get("evidence_gap"),
                raw.get("research_gap"),
                g0.get("research_gaps"),
                g1_quyet.get("knowledge_gap"),
                g0_quyet.get("novelty_justification"),
            ),
            "local_context": _first(raw.get("local_context"),
                                    raw.get("practice_context")),
        },
        "question": {
            "text": _first(raw.get("research_question"),
                           raw.get("clinical_question"),
                           g1_quyet.get("research_question")),
            "framework": _first(raw.get("question_framework"), "PICO/PECO"),
            "pico": pico if is_present(pico) else _pico_tu_g0(g0_quyet),
            "hypothesis": raw.get("hypothesis"),
        },
        "objectives": {
            "general": aim,
            "specific": objectives,
        },
        "design": {
            "code": design_code,
            "label": _first(raw.get("design"),
                            _get(g1, "design", "primary")),
            "rationale": _first(raw.get("design_rationale"),
                                _get(g1, "design", "rationale"),
                                g1_quyet.get("design_rationale")),
            "setting": _first(raw.get("setting"), raw.get("site"),
                              raw.get("location"), g1_quyet.get("setting")),
            "period": _first(raw.get("study_period"), raw.get("period"),
                             raw.get("timeframe"), g1_quyet.get("study_period")),
            "reporting_primary": reporting["primary"],
            "protocol_standard": reporting["protocol"],
            "additional_standards": reporting["extra"],
        },
        "population": {
            # Quyết định quần thể CHÍNH THỨC của G1 đứng trước P của khối PICO (bản tóm tắt) — 06/10/2026.
            "description": _first(raw.get("population"), g1_quyet.get("population"),
                                  pico.get("p"), g0_quyet.get("population")),
            "inclusion": _as_list(_first(raw.get("inclusion_criteria"),
                                         g1_quyet.get("inclusion_criteria"))),
            "exclusion": _as_list(_first(raw.get("exclusion_criteria"),
                                         g1_quyet.get("exclusion_criteria"))),
            "sampling": _first(raw.get("sampling_method"),
                               raw.get("sampling_strategy")),
            "recruitment": _first(raw.get("recruitment_plan"),
                                  raw.get("recruitment"),
                                  g1_quyet.get("recruitment_strategy")),
            "consent": _first(raw.get("consent_plan"),
                              ethics_meta.get("consent"),
                              raw.get("consent")),
        },
        "exposure_intervention": exposure_intervention,
        "outcomes": {
            "primary": primary,
            "secondary": secondary,
        },
        "variables": {
            "items": _as_list(variables),
            "confounders": _as_list(_first(raw.get("confounders"),
                                           raw.get("covariates"))),
            "effect_modifiers": _as_list(raw.get("effect_modifiers")),
        },
        "sample_size": {
            "calculated_n": _first(sample_meta.get("calculated_n"),
                                   g3.get("n_adjusted"),
                                   g3.get("n_total")),
            "confirmed_n": _first(sample_meta.get("confirmed_n"),
                                  g3.get("confirmed_n")),
            "formula": _first(sample_meta.get("formula"),
                              g3.get("formula_used")),
            "alpha": _first(sample_meta.get("alpha"), g3.get("alpha")),
            "power": _first(sample_meta.get("power"), g3.get("power")),
            "dropout": _first(sample_meta.get("dropout"), g3.get("dropout")),
            "assumptions": _first(sample_meta.get("assumptions"),
                                  raw.get("sample_size_assumptions")),
            "assumptions_source": _first(
                sample_meta.get("assumptions_source"),
                raw.get("sample_size_assumption_source"),
                # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 23, phát
                # hiện #2): `g3` ở đây là G3_checkpoint.json (do
                # run_g3_auto.py ghi) — file đó KHÔNG BAO GIỜ chứa
                # effect_source/assumption_source (đã xác nhận bằng grep:
                # 0 lần ghi). Nguồn giả định cỡ mẫu mà bác sĩ THẬT SỰ xác
                # nhận nằm ở study_meta.json → gate_params.G3.effect_source
                # (xem tools/g3_quality_gate.py::_g3_meta(), G3-AUTO-05) —
                # một object KHÁC hẳn `g3` (checkpoint) mà build_study_spec()
                # nhận riêng qua tham số `meta`/`raw`. Hai dòng g3.get(...)
                # cũ là dead fallback trên object sai; đã thêm đúng đường
                # dẫn thật, GIỮ NGUYÊN 2 fallback cũ (không phá test hiện có
                # dùng schema phẳng sample_size_assumption_source).
                _get(raw, "gate_params", "G3", "effect_source"),
                _get(raw, "gate_params", "G3", "assumption_source"),
                g3.get("effect_source"),
                g3.get("assumption_source"),
            ),
            "sampling_sufficiency": _first(
                sample_meta.get("sampling_sufficiency"),
                raw.get("sampling_sufficiency"),
                raw.get("saturation_plan"),
                g1_quyet.get("saturation_criterion"),
                g3_quyet.get("saturation_stopping_rule"),
            ),
            "confirmed_n_adequate": g3.get("confirmed_n_adequate"),
        },
        "data_collection": {
            "instrument": instrument,
            "source": _first(raw.get("data_source"),
                             raw.get("source_data")),
            "procedures": _first(raw.get("data_collection_procedure"),
                                 raw.get("data_collection")),
            "measurement_times": _first(raw.get("measurement_times"),
                                        raw.get("timepoints"),
                                        g1_quyet.get("follow_up_schedule")),
            "quality_control": _first(raw.get("quality_control"),
                                      raw.get("qc_plan")),
            "pilot": _first(raw.get("pilot"), raw.get("pilot_plan")),
        },
        "data_governance": {
            "plan": _first(governance_meta.get("plan"),
                           raw.get("data_management_plan")),
            "storage": _first(governance_meta.get("storage"),
                              raw.get("data_storage")),
            "access": _first(governance_meta.get("access"),
                             raw.get("data_access")),
            "retention": _first(governance_meta.get("retention"),
                                raw.get("data_retention")),
            "deidentification": _first(
                governance_meta.get("deidentification"),
                raw.get("deidentification_plan"),
                raw.get("real_data_deidentification"),
            ),
            "missing_data": _first(governance_meta.get("missing_data"),
                                   raw.get("missing_data_plan")),
        },
        "analysis": {
            "sap_version": _first(analysis_meta.get("sap_version"),
                                  g4.get("g4_sap_version")),
            "sap_status": _first(analysis_meta.get("sap_status"),
                                 g4.get("g4_status")),
            "primary_outcome": _first(analysis_meta.get("primary_outcome"),
                                      raw.get("sap_primary_outcome")),
            "primary_method": _first(
                analysis_meta.get("primary_method"),
                analysis_meta.get("primary_analysis"),
                raw.get("primary_analysis"),
                g6.get("analysis_name"),
            ),
            "secondary_methods": _first(
                analysis_meta.get("secondary_methods"),
                raw.get("secondary_analyses"),
            ),
            "missing_data": _first(analysis_meta.get("missing_data"),
                                   raw.get("missing_data_analysis")),
            "sensitivity": _first(analysis_meta.get("sensitivity"),
                                  raw.get("sensitivity_analysis")),
            "multiplicity": _first(analysis_meta.get("multiplicity"),
                                   raw.get("multiplicity_plan")),
            "software": _first(analysis_meta.get("software"),
                               raw.get("analysis_software")),
        },
        # THÊM 06/09/2026 (khuôn 18 mục / 23 thành phần): ba khối nội dung mà
        # khuôn cũ không có chỗ chứa. Chỉ ĐỌC từ study_meta/checkpoint — không bịa.
        "literature": {
            "summary": _first(raw.get("literature_review"),
                              raw.get("literature_summary"),
                              _get(raw, "literature", "summary"),
                              g1_quyet.get("evidence_summary")),
            "consensus": _first(raw.get("literature_consensus"),
                                _get(raw, "literature", "consensus")),
            "disagreements": _first(raw.get("literature_disagreements"),
                                    raw.get("conflicting_evidence"),
                                    _get(raw, "literature", "disagreements")),
            "novelty": _first(raw.get("novelty"), raw.get("differentiation"),
                              _get(raw, "literature", "novelty"),
                              g0.get("novelty_concern")),
            "ledger_artifact": _first(
                _get(g1, "artifacts", "A2b_evidence_ledger"),
                _get(g1, "artifacts", "A2b_markdown"),
                _get(g1, "artifacts", "A2b"),
            ),
        },
        "theory": {
            "framework": _first(raw.get("theoretical_framework"),
                                raw.get("conceptual_framework"),
                                _get(raw, "theory", "framework")),
            # Thiết kế thuần sinh học/dược lý có thể KHÔNG dựa khung lý thuyết —
            # nhưng phải NÓI RA kèm lý do, không để trống.
            "not_applicable_rationale": _first(
                raw.get("theoretical_framework_not_applicable"),
                _get(raw, "theory", "not_applicable_rationale"),
            ),
        },
        "expected_results": {
            "summary": _first(raw.get("expected_results"),
                              raw.get("anticipated_results"),
                              _get(raw, "expected_results_block", "summary")),
            "table_shells": _as_list(_first(raw.get("table_shells"),
                                            raw.get("dummy_tables"),
                                            _get(raw, "expected_results_block",
                                                 "table_shells"))),
            "flow_diagram": _first(raw.get("flow_diagram_plan"),
                                   raw.get("participant_flow_plan")),
        },
        "bias": {
            "risks": _first(bias_meta.get("risks"), raw.get("bias_risks")),
            "mitigations": _first(
                bias_meta.get("mitigations"),
                raw.get("bias_controls"),
                raw.get("bias_mitigation"),
            ),
            # THÊM 06/09/2026: phạm vi & hạn chế dự kiến (mục 14 khuôn mới; P16).
            "limitations": _first(bias_meta.get("limitations"),
                                  raw.get("limitations"),
                                  raw.get("scope_limitations")),
        },
        "ethics": {
            "risk_level": _first(ethics_meta.get("risk_level"),
                                 g2.get("risk_level")),
            "irb_route": _first(ethics_meta.get("irb_route"),
                                g2.get("irb_route")),
            "benefit_risk": _first(ethics_meta.get("benefit_risk"),
                                   raw.get("risk_benefit"),
                                   g1_quyet.get("benefit_risk_rationale")),
            "consent": _first(ethics_meta.get("consent"),
                              raw.get("consent_plan")),
            "privacy": _first(ethics_meta.get("privacy"),
                              raw.get("privacy_plan"),
                              governance_meta.get("deidentification")),
            "safety": _first(ethics_meta.get("safety"),
                             raw.get("safety_plan")),
        },
        "registration_dissemination": {
            "required": _first(registration_meta.get("required"),
                               g2.get("registration_required")),
            "registry": _first(registration_meta.get("registry"),
                               g2.get("register_where")),
            "registration_id": _first(registration_meta.get("id"),
                                      raw.get("registration_id")),
            "plan": _first(registration_meta.get("plan"),
                           raw.get("registration_plan")),
            "dissemination": _first(registration_meta.get("dissemination"),
                                    raw.get("dissemination_plan"),
                                    raw.get("knowledge_translation_plan")),
        },
        "resources": {
            "timeline": _first(resources_meta.get("timeline"),
                               raw.get("timeline")),
            "team": _first(resources_meta.get("team"),
                           raw.get("team"),
                           raw.get("personnel"),
                           g1_quyet.get("team_roles")),
            "budget": _first(resources_meta.get("budget"),
                             raw.get("budget"),
                             _kinh_phi_g1(g1_quyet.get("budget"))),
        },
        "references": {
            "pmids": pmids,
            "dois": dois,
            "verification_status": _first(
                raw.get("citation_verification_status"),
                raw.get("references_verified"),
            ),
        },
        "appendices": {
            "required": list(S.DE_CUONG_PHU_LUC),
            "provided": _as_list(raw.get("appendices")),
        },
        "traceability": _as_list(raw.get("traceability_matrix")),
        "design_specific": design_specific,
        "provenance": {
            "study_meta": "study_meta.json" if meta else None,
            "checkpoints": [
                gate for gate in (f"G{i}" for i in range(10))
                if checkpoints.get(gate)
            ],
        },
    }
    return spec


def _path(spec: dict, dotted: str):
    cur: Any = spec
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


# Mỗi tuple con là một yêu cầu; chỉ cần MỘT path trong tuple có dữ liệu.
_PROTOCOL_RULES: Dict[str, Tuple[Tuple[str, Tuple[str, ...]], ...]] = {
    "P01": (
        ("Tên đề tài", ("title",)),
        ("Phiên bản", ("document.version",)),
        ("Ngày tài liệu", ("document.date",)),
    ),
    "P02": (("Tóm tắt protocol", ("summary",)),),
    "P03": (
        ("Bối cảnh/khoảng trống", (
            "rationale.problem", "rationale.evidence_gap",
        )),
    ),
    "P04": (("Câu hỏi nghiên cứu", ("question.text",)),),
    "P05": (
        ("Mục tiêu", ("objectives.general", "objectives.specific")),
    ),
    "P06": (
        ("Thiết kế", ("design.code",)),
        ("Bối cảnh", ("design.setting",)),
        ("Thời gian", ("design.period",)),
    ),
    "P07": (
        ("Quần thể", ("population.description",)),
        ("Tiêu chuẩn chọn", ("population.inclusion",)),
        ("Tiêu chuẩn loại", ("population.exclusion",)),
    ),
    "P08": (
        ("Tuyển/chọn mẫu", ("population.sampling", "population.recruitment")),
        ("Đồng thuận", ("population.consent", "ethics.consent")),
    ),
    "P09": (
        ("Phơi nhiễm/can thiệp/đánh giá", (
            "exposure_intervention.description",
            "design_specific.evaluation",
        )),
    ),
    "P10": (
        ("Tên kết cục chính", ("outcomes.primary.name",)),
        ("Định nghĩa vận hành", ("outcomes.primary.definition",)),
        ("Thời điểm đo", ("outcomes.primary.timepoint",)),
        ("Nguồn đo", ("outcomes.primary.source",)),
    ),
    "P11": (
        ("Danh mục biến", ("variables.items",)),
        ("Kế hoạch nhiễu/tương tác", (
            "variables.confounders",
            "variables.effect_modifiers",
            "design_specific.no_confounding_applicable",
        )),
    ),
    "P12": (
        ("Cỡ mẫu hoặc bão hòa", (
            "sample_size.confirmed_n",
            "sample_size.calculated_n",
            "sample_size.sampling_sufficiency",
        )),
        ("Nguồn giả định", (
            "sample_size.assumptions_source",
            "sample_size.sampling_sufficiency",
        )),
    ),
    "P13": (
        ("Công cụ/nguồn dữ liệu", (
            "data_collection.instrument.name",
            "data_collection.source",
        )),
        ("Quy trình thu thập", ("data_collection.procedures",)),
        ("Kiểm soát chất lượng/pilot", (
            "data_collection.quality_control",
            "data_collection.pilot",
        )),
    ),
    "P14": (
        ("Kế hoạch dữ liệu", ("data_governance.plan",)),
        ("Lưu trữ/phân quyền", (
            "data_governance.storage",
            "data_governance.access",
        )),
        ("Khử định danh", ("data_governance.deidentification",)),
    ),
    "P15": (
        ("SAP", ("analysis.sap_version",)),
        ("Phân tích chính", ("analysis.primary_method",)),
        ("Dữ liệu thiếu", (
            "analysis.missing_data",
            "data_governance.missing_data",
        )),
    ),
    "P16": (
        ("Nguy cơ sai lệch", ("bias.risks",)),
        ("Biện pháp giảm thiểu", ("bias.mitigations",)),
        ("Phạm vi và hạn chế dự kiến", ("bias.limitations",)),
    ),
    "P17": (
        ("Đánh giá lợi ích-nguy cơ", ("ethics.benefit_risk",)),
        ("Đồng thuận", ("ethics.consent", "population.consent")),
        ("Bảo mật/an toàn", ("ethics.privacy", "ethics.safety")),
    ),
    "P18": (
        ("Kế hoạch đăng ký", (
            "registration_dissemination.plan",
            "registration_dissemination.registry",
        )),
        ("Phổ biến kết quả", ("registration_dissemination.dissemination",)),
    ),
    "P19": (
        ("Tiến độ", ("resources.timeline",)),
        ("Nhân lực", ("resources.team",)),
        ("Kinh phí", ("resources.budget",)),
    ),
    "P20": (
        ("Tài liệu tham khảo", ("references.pmids", "references.dois")),
        ("Phụ lục", ("appendices.required",)),
    ),
    # THÊM 06/09/2026 — khuôn 18 mục.
    "P21": (
        ("Tổng hợp nghiên cứu trước", ("literature.summary",)),
        ("Điểm đồng thuận/bất đồng", ("literature.consensus",
                                      "literature.disagreements")),
    ),
    "P22": (
        ("Khung lý thuyết/mô hình khái niệm (hoặc lý do không áp dụng)",
         ("theory.framework", "theory.not_applicable_rationale")),
    ),
    "P23": (
        ("Khung bảng trống (dummy tables)", ("expected_results.table_shells",)),
        ("Tóm tắt kết quả dự kiến — không số liệu", ("expected_results.summary",)),
    ),
    "P24": (
        ("Mô tả can thiệp/đối chứng (TIDieR) hoặc không áp dụng",
         ("exposure_intervention.description", "design_specific.not_applicable_rationale")),
        ("Ngẫu nhiên hoá/làm mù hoặc không áp dụng",
         ("design_specific.randomization", "design_specific.not_applicable_rationale")),
    ),
}

_PROTOCOL_SOURCES = {
    "P01": "study_meta/G0",
    "P02": "study_meta/G10",
    "P03": "study_meta/G0",
    "P04": "study_meta/G0-G1",
    "P05": "study_meta/G0",
    "P06": "study_meta/G1",
    "P07": "study_meta",
    "P08": "study_meta/G2",
    "P09": "study_meta/G1-G2",
    "P10": "study_meta/G5",
    "P11": "study_meta/G5",
    "P12": "study_meta/G3",
    "P13": "study_meta/G5",
    "P14": "study_meta/G2/G5",
    "P15": "study_meta/G4/G6",
    "P16": "study_meta/G1",
    "P17": "study_meta/G2",
    "P18": "study_meta/G2/G8",
    "P19": "study_meta",
    "P20": "G0/G7 + phụ lục G10",
    "P21": "study_meta/G0-G1 (Evidence Ledger A2b)",
    "P22": "study_meta",
    "P23": "study_meta/G4 (SAP §11) + danh mục bảng/hình G10",
    "P24": "study_meta (exposure_intervention/design_specific) — chỉ RCT, "
           "tự ĐẠT cho thiết kế khác (không áp dụng)",
}


def protocol_coverage(spec: dict) -> List[dict]:
    """Đánh giá đủ/một phần/thiếu cho từng thành phần protocol (len(PROTOCOL_CORE_ITEMS))."""
    rows: List[dict] = []
    for item_id, title in S.PROTOCOL_CORE_ITEMS:
        rules = _PROTOCOL_RULES[item_id]
        missing = [
            label for label, paths in rules
            if not any(is_present(_path(spec, path)) for path in paths)
        ]
        if not missing:
            status = "ĐỦ DỮ LIỆU DỰ THẢO"
        elif len(missing) == len(rules):
            status = "THIẾU"
        else:
            status = "MỘT PHẦN"
        rows.append({
            "id": item_id,
            "title": title,
            "status": status,
            "missing": missing,
            "source": _PROTOCOL_SOURCES[item_id],
        })
    return rows


_BASE_REQUIREMENTS: Tuple[
    Tuple[str, str, Tuple[Tuple[str, ...], ...], str], ...
] = (
    ("D01", "Tên đề tài", (("title",),), "Chủ nhiệm đề tài"),
    ("D02", "Câu hỏi nghiên cứu", (("question.text",),), "Chủ nhiệm đề tài"),
    ("D03", "Mục tiêu chính/cụ thể",
     (("objectives.general", "objectives.specific"),), "Chủ nhiệm đề tài"),
    ("D04", "Thiết kế nghiên cứu", (("design.code",),), "Chủ nhiệm + phương pháp"),
    ("D05", "Bối cảnh và thời gian",
     (("design.setting",), ("design.period",)), "Chủ nhiệm/đơn vị"),
    ("D06", "Quần thể và tiêu chuẩn chọn/loại",
     (("population.description",), ("population.inclusion",),
      ("population.exclusion",)),
     "Chủ nhiệm đề tài"),
    ("D07", "Phương pháp chọn mẫu/tuyển mẫu",
     (("population.sampling", "population.recruitment"),), "Chủ nhiệm đề tài"),
    ("D08", "Kết cục chính có định nghĩa, nguồn và thời điểm đo",
     (("outcomes.primary.name",), ("outcomes.primary.definition",),
      ("outcomes.primary.source",), ("outcomes.primary.timepoint",)),
     "Chủ nhiệm + thống kê viên"),
    ("D09", "Cơ sở cỡ mẫu/bão hòa",
     (("sample_size.calculated_n", "sample_size.confirmed_n",
       "sample_size.sampling_sufficiency"),), "Thống kê viên/chủ nhiệm"),
    ("D10", "Nguồn giả định cỡ mẫu",
     (("sample_size.assumptions_source", "sample_size.sampling_sufficiency"),),
     "Thống kê viên/chủ nhiệm"),
    ("D11", "Công cụ hoặc nguồn dữ liệu",
     (("data_collection.instrument.name", "data_collection.source"),),
     "Chủ nhiệm + quản lý dữ liệu"),
    ("D12", "Phân tích chính định trước",
     (("analysis.primary_method",),), "Thống kê viên"),
    ("D13", "Kế hoạch xử lý dữ liệu thiếu",
     (("analysis.missing_data", "data_governance.missing_data"),), "Thống kê viên"),
    ("D14", "Sai lệch và biện pháp giảm thiểu",
     (("bias.risks",), ("bias.mitigations",)), "Chủ nhiệm + phương pháp"),
    ("D15", "Consent, lợi ích-nguy cơ và bảo mật",
     (("ethics.consent", "population.consent"), ("ethics.benefit_risk",),
      ("ethics.privacy",)), "Chủ nhiệm + Hội đồng đạo đức"),
    ("D16", "Tiến độ, nhân lực và kinh phí",
     (("resources.timeline",), ("resources.team",), ("resources.budget",)),
     "Chủ nhiệm/đơn vị"),
    # THÊM 06/09/2026 — khuôn 18 mục: hai quyết định khoa học hội đồng luôn hỏi.
    ("D17", "Tổng quan tài liệu và khung lý thuyết (hoặc lý do không áp dụng)",
     (("literature.summary",),
      ("theory.framework", "theory.not_applicable_rationale")),
     "Chủ nhiệm + EBM specialist"),
    ("D18", "Dự kiến kết quả: khung bảng trống theo ma trận truy xuất, không số liệu",
     (("expected_results.table_shells", "expected_results.summary"),),
     "Thống kê viên/chủ nhiệm"),
)

_DESIGN_FIELD_REQUIREMENTS: Dict[
    str, Tuple[Tuple[str, str, Tuple[Tuple[str, ...], ...], str], ...]
] = {
    "rct": (
        ("R01", "Can thiệp và comparator",
         (("exposure_intervention.description",),
          ("exposure_intervention.comparator",)),
         "Chủ nhiệm + dược/lâm sàng"),
        ("R02", "Randomization và che giấu phân bổ",
         (("design_specific.randomization",),
          ("design_specific.allocation_concealment",)),
         "Thống kê viên/chủ nhiệm"),
        ("R03", "Theo dõi harms và stopping rules",
         (("design_specific.harms",), ("design_specific.stopping_rules",)),
         "Hội đồng an toàn/chủ nhiệm"),
    ),
    "diagnostic": (
        ("X01", "Index test, reference standard và ngưỡng",
         (("design_specific.index_test",),
          ("design_specific.reference_standard",),
          ("design_specific.threshold",)), "Chủ nhiệm + chuyên gia chẩn đoán"),
    ),
    "prediction": (
        ("M01", "Validation, calibration và discrimination",
         (("design_specific.validation",), ("design_specific.calibration",),
          ("design_specific.discrimination",)), "Thống kê/ML + chủ nhiệm"),
    ),
    "systematic_review": (
        ("S01", "Eligibility, chiến lược tìm kiếm và risk of bias",
         (("design_specific.eligibility",),
          ("design_specific.search_strategy",),
          ("design_specific.risk_of_bias",)), "Nhóm tổng quan"),
    ),
    "qualitative": (
        ("Q01", "Sampling, bão hòa/information power và reflexivity",
         (("population.sampling",), ("sample_size.sampling_sufficiency",),
          ("design_specific.reflexivity",)), "Nhóm định tính"),
        ("Q02", "Quy trình mã hóa, phần mềm mã hóa và audit trail",
         (("analysis.primary_method",), ("design_specific.audit_trail",),
          ("analysis.software", "design_specific.qda_software")),
         "Nhóm định tính"),
    ),
}


def missing_requirements(spec: dict) -> List[dict]:
    """Danh sách quyết định còn thiếu theo các nhóm path thay thế."""
    design = spec.get("design", {}).get("code")
    requirements = list(_BASE_REQUIREMENTS)
    requirements.extend(_DESIGN_FIELD_REQUIREMENTS.get(design, ()))
    missing: List[dict] = []
    for req_id, label, path_groups, owner in requirements:
        absent_groups = [
            paths for paths in path_groups
            if not any(is_present(_path(spec, path)) for path in paths)
        ]
        if absent_groups:
            missing.append({
                "id": req_id,
                "label": label,
                "paths": [" | ".join(paths) for paths in absent_groups],
                "owner": owner,
                "action": "Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10.",
            })
    return missing


def semantic_issues(spec: dict, checkpoints: Dict[str, dict],
                    meta: Optional[dict] = None) -> List[dict]:
    """Phát hiện mâu thuẫn khoa học có cấu trúc giữa meta và checkpoint."""
    raw = _canonical_meta(meta)
    issues: List[dict] = []

    design_candidates = {
        S.canonical_design_code(value)
        for value in (
            raw.get("design_code"),
            _get(checkpoints.get("G1"), "design", "internal_code"),
            _get(checkpoints.get("G3"), "design_code"),
            _get(checkpoints.get("G5"), "design_code"),
            _get(checkpoints.get("G6"), "design_code"),
        )
        if is_present(value)
    }
    design_candidates.discard(None)
    if len(design_candidates) > 1:
        issues.append({
            "severity": "ERROR",
            "code": "DESIGN_CONFLICT",
            "path": "design.code",
            "message": "Mã thiết kế mâu thuẫn giữa study_meta và checkpoint: "
                       + ", ".join(sorted(design_candidates)),
        })

    primary_name = _name(_get(spec, "outcomes", "primary"))
    all_outcome_names = {
        _name(item).casefold()
        for item in _as_list(raw.get("outcomes"))
        if _name(item)
    }
    if primary_name and all_outcome_names and primary_name.casefold() not in all_outcome_names:
        issues.append({
            "severity": "ERROR",
            "code": "PRIMARY_OUTCOME_NOT_IN_OUTCOMES",
            "path": "outcomes.primary",
            "message": "Kết cục chính không xuất hiện trong danh sách outcomes.",
        })

    sap_primary = _name(_get(spec, "analysis", "primary_outcome"))
    if primary_name and sap_primary and primary_name.casefold() != sap_primary.casefold():
        issues.append({
            "severity": "ERROR",
            "code": "SAP_PRIMARY_OUTCOME_MISMATCH",
            "path": "analysis.primary_outcome",
            "message": "Kết cục chính trong SAP không khớp protocol.",
        })

    primary_variable = _get(spec, "outcomes", "primary", "variable_name")
    crf_variables = {
        str(item).strip() for item in _get(spec, "variables", "items", default=[])
        if is_present(item)
    }
    if is_present(primary_variable) and crf_variables and primary_variable not in crf_variables:
        issues.append({
            "severity": "ERROR",
            "code": "PRIMARY_OUTCOME_VARIABLE_NOT_IN_CRF",
            "path": "outcomes.primary.variable_name",
            "message": f"Biến kết cục chính `{primary_variable}` không có trong CRF/codebook.",
        })

    if _get(spec, "sample_size", "confirmed_n_adequate") is False:
        issues.append({
            "severity": "ERROR",
            "code": "CONFIRMED_N_UNDERPOWERED",
            "path": "sample_size.confirmed_n",
            "message": "Cỡ mẫu chủ nhiệm chốt thấp hơn cỡ mẫu tối thiểu tính toán.",
        })

    instrument = _get(spec, "data_collection", "instrument", default={}) or {}
    if is_present(instrument.get("name")) and not is_present(instrument.get("source")):
        issues.append({
            "severity": "WARNING",
            "code": "INSTRUMENT_SOURCE_MISSING",
            "path": "data_collection.instrument.source",
            "message": "Công cụ đo đã có tên nhưng chưa có nguồn/bản quyền hoặc bằng chứng thẩm định.",
        })

    objectives = [
        str(item).strip().casefold()
        for item in _get(spec, "objectives", "specific", default=[])
        if is_present(item)
    ]
    if len(objectives) != len(set(objectives)):
        issues.append({
            "severity": "WARNING",
            "code": "DUPLICATE_OBJECTIVES",
            "path": "objectives.specific",
            "message": "Danh sách mục tiêu cụ thể có mục trùng lặp.",
        })
    return issues


def evaluate_study_spec(spec: dict, checkpoints: Dict[str, dict],
                        meta: Optional[dict] = None) -> dict:
    """Tổng hợp độ đầy đủ, lỗi ngữ nghĩa và mức sẵn sàng của StudySpec."""
    coverage = protocol_coverage(spec)
    missing = missing_requirements(spec)
    issues = semantic_issues(spec, checkpoints, meta)
    errors = [issue for issue in issues if issue["severity"] == "ERROR"]
    complete_items = sum(row["status"] == "ĐỦ DỮ LIỆU DỰ THẢO" for row in coverage)
    scientific_complete = not missing and not errors
    protocol_complete = complete_items == len(S.PROTOCOL_CORE_ITEMS)
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_coverage": coverage,
        "protocol_complete_items": complete_items,
        "protocol_total_items": len(S.PROTOCOL_CORE_ITEMS),
        "missing_requirements": missing,
        "semantic_issues": issues,
        "scientific_content_complete": scientific_complete,
        "protocol_content_complete": protocol_complete,
        "readiness_level": (
            "SCIENTIFIC_CONTENT_COMPLETE_DRAFT"
            if scientific_complete and protocol_complete
            else "STRUCTURE_COMPLETE_WITH_OPEN_DECISIONS"
        ),
    }


def meta_for_render(meta: Optional[dict], spec: dict) -> dict:
    """Chiếu StudySpec về các key cũ để các section builder tương thích ngược."""
    out = dict(meta or {})
    defaults = {
        "title": spec.get("title"),
        "document_version": _get(spec, "document", "version"),
        "document_date": _get(spec, "document", "date"),
        "summary": spec.get("summary"),
        "problem_statement": _get(spec, "rationale", "problem"),
        "evidence_gap": _get(spec, "rationale", "evidence_gap"),
        "local_context": _get(spec, "rationale", "local_context"),
        "research_question": _get(spec, "question", "text"),
        "pico": _get(spec, "question", "pico"),
        "hypothesis": _get(spec, "question", "hypothesis"),
        "aim": _get(spec, "objectives", "general"),
        "objectives": _get(spec, "objectives", "specific"),
        "design_code": _get(spec, "design", "code"),
        "setting": _get(spec, "design", "setting"),
        "study_period": _get(spec, "design", "period"),
        "population": _get(spec, "population", "description"),
        "inclusion_criteria": _get(spec, "population", "inclusion"),
        "exclusion_criteria": _get(spec, "population", "exclusion"),
        "sampling_method": _get(spec, "population", "sampling"),
        "recruitment_plan": _get(spec, "population", "recruitment"),
        "consent_plan": _get(spec, "population", "consent"),
        "primary_outcome": _get(spec, "outcomes", "primary"),
        "secondary_outcomes": _get(spec, "outcomes", "secondary"),
        "variables": _get(spec, "variables", "items"),
        "confounders": _get(spec, "variables", "confounders"),
        "effect_modifiers": _get(spec, "variables", "effect_modifiers"),
        "instrument": _get(spec, "data_collection", "instrument"),
        "data_source": _get(spec, "data_collection", "source"),
        "data_collection_procedure": _get(
            spec, "data_collection", "procedures"
        ),
        "measurement_times": _get(spec, "data_collection", "measurement_times"),
        "quality_control": _get(spec, "data_collection", "quality_control"),
        "pilot": _get(spec, "data_collection", "pilot"),
        "analysis": spec.get("analysis"),
        "bias": spec.get("bias"),
        "literature": spec.get("literature"),
        "theory": spec.get("theory"),
        "expected_results": spec.get("expected_results"),
        "ethics": spec.get("ethics"),
        "registration": spec.get("registration_dissemination"),
        "resources": spec.get("resources"),
        "traceability_matrix": spec.get("traceability"),
    }
    for key, value in defaults.items():
        if key not in out and is_present(value):
            out[key] = value
    # THÊM 06/09/2026 (SPIRIT 2025 9b/11/15a/15d/18/21-24) — GHI ĐÈ, không theo
    # luật "if key not in out" ở trên. Lý do: `out` khởi tạo từ BẢN SAO của
    # `meta` thô, mà `design_specific` HẦU NHƯ LUÔN đã tồn tại sẵn trong
    # study_meta.json thật (bác sĩ đặt trực tiếp) — luật "chỉ điền khi thiếu"
    # khiến `sec_thietke()` mãi mãi đọc bản THÔ chưa qua alias-hoá/tự-suy
    # not_applicable_rationale của `build_study_spec()`, dù `spec["design_specific"]`
    # đã có đủ dữ liệu (đo được: quá trình debug 06/09/2026 phát hiện đúng ca này
    # — bản ghi đè bằng tay không bao giờ tới nơi render). `spec["design_specific"]`
    # luôn là SUPERSET của bản thô (chỉ CỘNG thêm alias/not_applicable_rationale,
    # không bao giờ bớt) nên ghi đè vô điều kiện là AN TOÀN, không mất dữ liệu.
    if is_present(spec.get("exposure_intervention")):
        out["exposure_intervention"] = spec["exposure_intervention"]
    if is_present(spec.get("design_specific")):
        out["design_specific"] = spec["design_specific"]
    # THÊM 05/10/2026 (soát từng cổng G10 — lộ khi chạy chuỗi THẬT tới G10): các KHỐI mà section builder đọc như dict
    # (expected_results, literature, theory, analysis, bias, ethics, registration, resources) — study_meta thô hay ghi
    # dạng phẳng (vd "expected_results": "<chuỗi>" + "table_shells": [...] ở cấp cao nhất). StudySpec gom đúng vào khối
    # dict (D18 đạt) nhưng luật «chỉ điền khi thiếu» giữ CHUỖI thô ⇒ builder thấy không phải dict ⇒ in «[CẦN BỔ SUNG]»
    # dù dữ kiện đã có: đề cương và StudySpec nói hai chuyện. Bản thô không phải dict ⇒ dùng khối của StudySpec.
    for key in ("expected_results", "literature", "theory", "analysis", "bias", "ethics", "registration",
                "resources"):
        value = defaults.get(key)
        if isinstance(value, dict) and is_present(value) and not isinstance(out.get(key), dict):
            out[key] = value
    # 06/10/2026: khối resources thô LÀ dict nhưng thiếu khoá (vd chỉ có team) ⇒ bổ sung khoá còn trống từ StudySpec
    # (G1.team_roles, G1.budget) — dựng dict MỚI, không sửa bản thô của study_meta.
    res_spec = defaults.get("resources")
    if isinstance(out.get("resources"), dict) and isinstance(res_spec, dict):
        bo_sung = {k: v for k, v in res_spec.items() if is_present(v) and not is_present(out["resources"].get(k))}
        if bo_sung:
            out["resources"] = {**out["resources"], **bo_sung}
    return out


def decision_package_markdown(study: str, spec: dict, evaluation: dict) -> str:
    """Sinh một gói quyết định duy nhất thay cho hỏi rời rạc từng trường."""
    lines = [
        f"# Gói quyết định hoàn thiện đề cương — {study}",
        "",
        f"**Mức hiện tại:** {evaluation['readiness_level']}.  ",
        f"**Bao phủ protocol:** {evaluation['protocol_complete_items']}/"
        f"{evaluation['protocol_total_items']} thành phần đủ dữ liệu dự thảo.",
        "",
        "## Quyết định khoa học/hành chính còn thiếu",
        "",
        "| Mã | Nội dung cần xác nhận | Trường còn thiếu | Người quyết định | Hành động |",
        "|---|---|---|---|---|",
    ]
    missing = evaluation["missing_requirements"]
    if missing:
        for row in missing:
            lines.append(
                f"| {row['id']} | {row['label']} | `{', '.join(row['paths'])}` | "
                f"{row['owner']} | {row['action']} |"
            )
    else:
        lines.append(
            "| — | Không còn trường khoa học cốt lõi bị thiếu | — | Chủ nhiệm "
            "| Rà soát và ký xác nhận; các cổng đời thực vẫn áp dụng. |"
        )

    lines.extend([
        "",
        "## Vấn đề ngữ nghĩa",
        "",
        "| Mức | Mã | Vị trí | Vấn đề |",
        "|---|---|---|---|",
    ])
    issues = evaluation["semantic_issues"]
    if issues:
        for issue in issues:
            lines.append(
                f"| {issue['severity']} | {issue['code']} | `{issue['path']}` | "
                f"{issue['message']} |"
            )
    else:
        lines.append("| — | — | — | Chưa phát hiện mâu thuẫn có cấu trúc. |")

    design = _get(spec, "design", "code")
    lines.extend([
        "",
        "## Checklist đặc thù thiết kế",
        "",
    ])
    requirements = S.DESIGN_PROTOCOL_REQUIREMENTS.get(design, ())
    if requirements:
        lines.extend(f"- {item}" for item in requirements)
    else:
        lines.append(
            f"- {S.TAG_CAN_KIEM_CHUNG_NGUON}: chưa có profile đặc thù cho "
            f"`{design or 'chưa xác định'}`; phải tra EQUATOR/nguồn chính thức."
        )
    lines.extend([
        "",
        "> Hệ thống không tự điền IRB, chữ ký, giả định cỡ mẫu, bản quyền công "
        "cụ hoặc quyết định của chủ nhiệm. Cần bác sĩ kiểm chứng.",
        "",
    ])
    return "\n".join(lines)
