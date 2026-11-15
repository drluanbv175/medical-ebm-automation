#!/usr/bin/env python3
"""Sáu kịch bản giả lập còn lại của canary `gia_lap_dinh_ky.py` — để canary phủ đủ 8 thiết kế (bác sĩ 15/11/2026:
«Hãy giả lập hoàn thiện chi tiết 8 loại thiết kế rồi từ đó vá để hệ thống đang ở trạng thái tự động tốt nhất»).

Hai kịch bản đầu (RCT, cắt ngang) ở `gia_lap_dinh_ky.KICH_BAN`. Tệp này thêm thuần tập, bệnh–chứng, chẩn đoán, mô hình
dự báo, tổng quan hệ thống/phân tích gộp, định tính. Mỗi kịch bản là một đề tài ngoại trú TỔNG HỢP có nhãn GIẢ LẬP,
không PII; nội dung viết như một chủ nhiệm thật khai, không viết cho vừa cổng.

NGUỒN SỐ (đã tra PubMed 15/11/2026, kiểm rút bài bằng `check_citation_retraction.py` trước khi dùng):
- Thuần tập: PMID 26462494 (Zhou 2016, Osteoporos Int) — PPI và gãy xương mọi vị trí RR 1,33 (KTC 95% 1,15–1,54).
- Bệnh–chứng: PMID 23137151 (Castellsague 2012, Drug Saf, dự án SOS) — ibuprofen và biến chứng tiêu hoá trên RR 1,84
  (KTC 95% 1,54–2,20), mức thấp nhất trong các NSAID thông dụng ⇒ giả định thận trọng.
- Chẩn đoán: PMID 34001645 (Mózes 2021, Gut, IPD MA) — AUROC của FIB-4 cho xơ hoá tiến triển 0,76; 30% có xơ hoá
  tiến triển trong các nghiên cứu gộp.
- Mô hình dự báo: Riley 2020 (BMJ 2020;368:m441, PMID 32188600) — tiêu chí cỡ mẫu; số tính bằng công thức của bài
  (10 tham số, tỷ lệ biến cố 20%, R²_CS = 15% R²_CS tối đa, co rút 0,9) ⇒ N = 898.
- Phân tích gộp: RIS tính cho tỷ lệ biến cố nhóm chứng GIẢ ĐỊNH 3%, giảm nguy cơ tương đối 25%, α 0,05, lực 90%,
  hiệu chỉnh dị biệt D² 25% ⇒ 25 462 người.

Hàm `kich_ban_them(vi, tien_to, hom_nay)` nhận tiện ích của canary (tránh import vòng) và trả dict cùng khuôn KICH_BAN.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

_XAC_NHAN = {
    "G0": {"pico_confirmed": True, "reviewed_by_role": "PI"},
    "G1": {"reviewed_by_role": "methodologist"},
    "G3": {"reviewed_by_role": "STATISTICIAN"},
}

_CO_XAC_NHAN_G1 = {"bias_controls_confirmed": True, "protocol_core_confirmed": True,
                   "feasibility_confirmed": True, "evidence_review_confirmed": True}
_CO_XAC_NHAN_G3 = {"effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
                   "recruitment_feasibility_confirmed": True}


def _finer(vi: Callable[[str], str], kha_thi: str, thu_vi: str, moi: str, dao_duc: str, phu_hop: str) -> Dict[str, str]:
    return {"finer_feasible": vi(kha_thi), "finer_interesting": vi(thu_vi), "finer_novel": vi(moi),
            "finer_ethical": vi(dao_duc), "finer_relevant": vi(phu_hop)}


def _g0_chung(hom_nay: str) -> Dict[str, Any]:
    return {"evidence_reviewed_confirmed": True,
            "registry_manual_checked": {"ictrp": hom_nay, "prospero": None}}


def _g1_chung(vi: Callable[[str], str]) -> Dict[str, Any]:
    return {"protocol_version": "0.1-canary", "design_confirmed": True,
            "team_roles": vi("Chủ nhiệm (PI), nhà phương pháp, thống kê viên, quản lý dữ liệu — vai trò, không ghi "
                             "danh "
                             "tính"),
            "risk_register": [], "budget": [], "annex2": {"applicable": False, "methodologies": []},
            **_CO_XAC_NHAN_G1}


def kich_ban_them(vi: Callable[[str], str], tien_to: str, hom_nay: str = "<HOM_NAY>") -> Dict[str, Dict[str, Any]]:
    """Sáu kịch bản thêm (thuần tập · bệnh–chứng · chẩn đoán · dự báo · tổng quan/gộp · định tính)."""
    kb: Dict[str, Dict[str, Any]] = {}

    # ── 1. THUẦN TẬP hồi cứu — phơi nhiễm thuốc và biến cố (câu hỏi tác hại)
    kc_tt = {"name": "Gãy xương mọi vị trí trong thời gian theo dõi",
             "measure": "Chẩn đoán gãy xương mới (mã ICD-10 S22, S32, S42, S52, S62, S72, S82, M48.4, M80) có phim "
                        "X-quang xác nhận trong hồ sơ",
             "timepoint": "Trong 3 năm kể từ ngày bắt đầu theo dõi", "type": "nhị phân"}
    kb["thuan_tap_phoi_nhiem"] = {
        "study": f"{tien_to}THUAN-TAP",
        "thiet_ke": "cohort",
        "mo_ta": "Thuần tập hồi cứu từ hồ sơ ngoại trú, phơi nhiễm thuốc → biến cố nhị phân (RR)",
        "topic": ("Sử dụng thuốc ức chế bơm proton kéo dài và nguy cơ gãy xương ở người từ 60 tuổi điều trị ngoại "
                  "trú: nghiên cứu thuần tập hồi cứu"),
        "query_en": ('("Proton Pump Inhibitors"[MeSH] OR "proton pump inhibitor*"[tiab] OR omeprazole[tiab] OR '
                     'esomeprazole[tiab] OR pantoprazole[tiab]) AND ("Fractures, Bone"[MeSH] OR fracture*[tiab]) AND '
                     '(aged[MeSH] OR elderly[tiab] OR "older adults"[tiab])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người từ 60 tuổi điều trị ngoại trú, có ít nhất 2 lần khám trong năm trước ngày "
                                 "bắt đầu theo dõi"),
                "intervention": "Dùng thuốc ức chế bơm proton liên tục ≥12 tháng (phơi nhiễm)",
                "comparison": "Không dùng thuốc ức chế bơm proton trong cùng giai đoạn",
                "outcomes": ["Gãy xương mọi vị trí trong 3 năm", "Gãy cổ xương đùi trong 3 năm"],
                "primary_outcome": kc_tt["name"],
                "primary_outcome_measure": kc_tt["measure"],
                "primary_outcome_timepoint": kc_tt["timepoint"],
                "hypothesis_h0": "Nguy cơ gãy xương ở nhóm dùng PPI kéo dài bằng nhóm không dùng",
                "hypothesis_h1": "Nguy cơ gãy xương ở nhóm dùng PPI kéo dài khác nhóm không dùng",
                "expected_direction": "Nhóm dùng PPI kéo dài có nguy cơ gãy xương cao hơn",
                "test_type": "superiority",
                "question_type": "harm",
                **_finer(vi, "Đạt — hồ sơ ngoại trú điện tử lưu ≥5 năm, đủ người từ 60 tuổi dùng PPI",
                         "Đạt — PPI kê rất phổ biến ở người cao tuổi ngoại trú",
                         "Đạt — chưa có số liệu thuần tập tại Việt Nam (theo nền bằng chứng G0)",
                         "Đạt — dữ liệu hồi cứu đã khử định danh, không can thiệp",
                         "Đạt — hỗ trợ rà soát kê PPI kéo dài không cần thiết"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Các phân tích gộp quốc tế (PMID 26462494) báo nguy cơ tăng vừa phải, "
                                            "dị biệt cao; chưa có thuần tập trên người cao tuổi ngoại trú Việt Nam"),
                "registry_overlap_assessment": vi("CHƯA tra WHO ICTRP thật; nghiên cứu quan sát hồi cứu tại một cơ "
                                                  "sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "cohort",
                "design_rationale": vi("Câu hỏi tác hại (G0 harm) với phơi nhiễm không thể phân bổ ngẫu nhiên vì lý "
                                       "do đạo đức — thuần tập hồi cứu từ hồ sơ có sẵn"),
                "objectives": ["So sánh nguy cơ gãy xương mọi vị trí trong 3 năm giữa người từ 60 tuổi dùng thuốc "
                               "ức chế bơm proton kéo dài và người không dùng"],
                "research_question": ("Ở người từ 60 tuổi điều trị ngoại trú, dùng thuốc ức chế bơm proton ≥12 tháng "
                                      "có làm tăng nguy cơ gãy xương trong 3 năm so với không dùng không?"),
                "primary_outcome": dict(kc_tt),
                "secondary_outcomes": ["Gãy cổ xương đùi trong 3 năm", "Thời gian đến gãy xương đầu tiên"],
                "population": ("Người từ 60 tuổi điều trị ngoại trú, có ít nhất 2 lần khám trong năm trước ngày bắt "
                                 "đầu theo dõi"),
                "inclusion_criteria": ["Tuổi ≥60 tại ngày bắt đầu theo dõi",
                                       "Có ≥2 lần khám ngoại trú trong 12 tháng trước ngày bắt đầu theo dõi"],
                "exclusion_criteria": ["Gãy xương trong 12 tháng trước ngày bắt đầu theo dõi",
                                       "Ung thư di căn xương hoặc đa u tuỷy", "Theo dõi <6 tháng"],
                "setting": "Phòng khám ngoại trú bệnh viện (giả lập)",
                "study_period": "Dữ liệu 2020-01 đến 2025-12; phân tích 2027-03 đến 2027-09",
                "intervention_or_exposure": ("Dùng thuốc ức chế bơm proton liên tục ≥12 tháng (≥80% số ngày có thuốc "
                                             "theo đơn cấp)"),
                "comparator": "Không có đơn thuốc ức chế bơm proton trong giai đoạn xác định phơi nhiễm",
                "recruitment_strategy": "Trích toàn bộ hồ sơ đủ tiêu chuẩn từ cơ sở dữ liệu ngoại trú",
                "follow_up_schedule": "Theo dõi qua hồ sơ từ ngày bắt đầu đến biến cố, tử vong, mất dấu hoặc 3 năm",
                "estimand": {"population": "Người từ 60 tuổi điều trị ngoại trú đủ tiêu chuẩn",
                             "treatment_condition": "Dùng PPI kéo dài so với không dùng",
                             "variable": "Gãy xương mọi vị trí trong 3 năm",
                             "intercurrent_events_strategy": "Tử vong trước gãy xương: biến cố cạnh tranh",
                             "population_summary_measure": "Nguy cơ tương đối (RR) hiệu chỉnh"},
                "background_problem": vi("Thuốc ức chế bơm proton thường được kê kéo dài ở người cao tuổi mà không "
                                         "đánh giá lại chỉ định"),
                "evidence_summary": vi("Phân tích gộp quan sát (PMID 26462494) báo nguy cơ gãy xương mọi vị trí "
                                       "tăng vừa phải ở người dùng PPI"),
                "knowledge_gap": vi("Thiếu thuần tập trên người cao tuổi ngoại trú Việt Nam"),
                "benefit_risk_rationale": vi("Không can thiệp; nguy cơ duy nhất là lộ dữ liệu — khử định danh trước "
                                             "phân tích"),
                "study_schema_timeline": ("Xác định nhóm phơi nhiễm 12 tháng → ngày bắt đầu theo dõi → theo dõi 3 "
                                          "năm qua hồ sơ"),
                "intervention_dose_adherence": ("Không can thiệp; phơi nhiễm đo bằng tỷ lệ số ngày có thuốc theo đơn "
                                                "cấp (≥80%)"),
                "stopping_rescue_rules": "Không áp dụng — nghiên cứu hồi cứu, không can thiệp",
                "critical_to_quality": vi("Định nghĩa phơi nhiễm và biến cố thống nhất; kiểm 10% hồ sơ biến cố "
                                          "bằng phim X-quang"),
                "monitoring_plan": vi("Kiểm chất lượng trích dữ liệu sau mỗi 500 hồ sơ"),
            },
            "G3": {
                "effect_size": 1.33, "effect_type": "RR", "p0": 0.08, "dropout": 0.1,
                "alpha": 0.05, "power": 0.8, "hypothesis_type": "superiority",
                "effect_source": ("PMID: 26462494 (Zhou 2016, Osteoporos Int) — PPI và gãy xương mọi vị trí RR 1,33 "
                                  "(KTC 95% 1,15–1,54)"),
                "p0_source": vi("Giả định 8% gãy xương mọi vị trí trong 3 năm ở người từ 60 tuổi không dùng PPI — "
                                "chưa có số liệu tại cơ sở"),
                "dropout_source": vi("Giả định 10% hồ sơ thiếu dữ liệu theo dõi — chưa có nguồn y văn"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": kc_tt["name"],
                "software": "run_g3_auto.py (so sánh hai tỷ lệ — thuần tập)",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }

    # ── 2. BỆNH–CHỨNG — yếu tố nguy cơ của biến cố hiếm
    kc_bc = {"name": "Xuất huyết tiêu hoá trên",
             "measure": ("Nôn máu hoặc đi ngoài phân đen kèm nội soi xác định tổn thương chảy máu ở thực quản, dạ dày "
                         "hoặc tá tràng (định nghĩa ca)"),
             "timepoint": "Tại ngày chỉ điểm (ngày nhập viện của ca; ngày khám của chứng)", "type": "nhị phân"}
    kb["benh_chung"] = {
        "study": f"{tien_to}BENH-CHUNG",
        "thiet_ke": "case_control",
        "mo_ta": "Bệnh–chứng, so phơi nhiễm giữa ca và chứng (OR)",
        "topic": ("Sử dụng thuốc chống viêm không steroid và xuất huyết tiêu hoá trên ở người từ 60 tuổi: nghiên cứu "
                  "bệnh–chứng"),
        "query_en": ('("Anti-Inflammatory Agents, Non-Steroidal"[MeSH] OR NSAID*[tiab] OR "non-steroidal '
                     'anti-inflammatory"[tiab]) AND ("Gastrointestinal Hemorrhage"[MeSH] OR "upper gastrointestinal '
                     'bleeding"[tiab] OR "peptic ulcer bleeding"[tiab]) AND ("case-control"[tiab] OR '
                     '"Case-Control Studies"[MeSH])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người từ 60 tuổi nhập viện vì xuất huyết tiêu hoá trên (ca) và người cùng tuổi khám "
                                 "ngoại trú không xuất huyết (chứng)"),
                "intervention": "Phơi nhiễm NSAID trong 30 ngày trước ngày chỉ điểm",
                "comparison": "Không phơi nhiễm NSAID trong cùng khoảng",
                "outcomes": ["Xuất huyết tiêu hoá trên (ca so với chứng)", "Liên quan theo từng loại NSAID"],
                "primary_outcome": kc_bc["name"],
                "primary_outcome_measure": kc_bc["measure"],
                "primary_outcome_timepoint": kc_bc["timepoint"],
                "hypothesis_h0": "Tỷ lệ phơi nhiễm NSAID ở nhóm ca bằng nhóm chứng (OR = 1)",
                "hypothesis_h1": "Tỷ lệ phơi nhiễm NSAID ở nhóm ca khác nhóm chứng (OR ≠ 1)",
                "expected_direction": "Nhóm ca có tỷ lệ phơi nhiễm NSAID cao hơn",
                "test_type": "superiority",
                "question_type": "harm",
                **_finer(vi, "Đạt — khoa tiêu hoá tiếp nhận đủ ca xuất huyết tiêu hoá trên mỗi năm",
                         "Đạt — NSAID tự mua phổ biến ở người cao tuổi",
                         "Đạt — chưa có số liệu theo loại NSAID tại cơ sở (theo nền bằng chứng G0)",
                         "Đạt — chỉ phỏng vấn và trích hồ sơ, nguy cơ tối thiểu",
                         "Đạt — hỗ trợ tư vấn dùng NSAID an toàn ở người cao tuổi"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Phân tích gộp (PMID 23137151) cho thấy nguy cơ khác nhau theo từng "
                                            "NSAID; chưa có số liệu theo loại NSAID ở người cao tuổi Việt Nam"),
                "registry_overlap_assessment": vi("CHƯA tra WHO ICTRP thật; nghiên cứu quan sát tại một cơ sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "case_control",
                "design_rationale": vi("Biến cố tương đối hiếm, cần đánh giá nhiều phơi nhiễm — bệnh–chứng hiệu quả "
                                       "hơn thuần tập"),
                "objectives": ["So sánh tỷ lệ phơi nhiễm NSAID trong 30 ngày giữa người từ 60 tuổi xuất huyết tiêu "
                               "hoá trên và người cùng tuổi không xuất huyết"],
                "research_question": ("Ở người từ 60 tuổi, phơi nhiễm NSAID trong 30 ngày có liên quan với xuất huyết "
                                      "tiêu hoá trên không?"),
                "primary_outcome": dict(kc_bc),
                "secondary_outcomes": ["Phơi nhiễm theo từng loại NSAID", "Phơi nhiễm đồng thời NSAID và thuốc chống "
                                       "đông"],
                "population": ("Người từ 60 tuổi: ca xuất huyết tiêu hoá trên nhập viện; chứng khám ngoại trú cùng "
                                 "cơ sở"),
                "inclusion_criteria": ["Tuổi ≥60", "Ca: xuất huyết tiêu hoá trên xác nhận qua nội soi",
                                       "Chứng: khám ngoại trú trong cùng tuần, không xuất huyết tiêu hoá"],
                "exclusion_criteria": ["Xơ gan có giãn tĩnh mạch thực quản", "Ung thư đường tiêu hoá trên",
                                       "Không nhớ được thuốc đã dùng và không có hồ sơ đơn thuốc"],
                "setting": "Khoa tiêu hoá và phòng khám ngoại trú bệnh viện (giả lập)",
                "study_period": "2027-03 đến 2028-02",
                "intervention_or_exposure": "Phơi nhiễm NSAID trong 30 ngày trước ngày chỉ điểm",
                "comparator": "Không phơi nhiễm NSAID",
                "case_definition": ("Người từ 60 tuổi nhập viện vì nôn máu hoặc đi ngoài phân đen, nội soi xác định "
                                    "tổn thương chảy máu ở thực quản, dạ dày hoặc tá tràng"),
                "control_source": ("Người khám ngoại trú cùng cơ sở trong cùng tuần với ca, ghép theo giới và nhóm "
                                   "tuổi "
                                   "5 năm, tỷ lệ 2 chứng : 1 ca"),
                "recruitment_strategy": "Tuyển liên tiếp ca đủ tiêu chuẩn; chọn chứng theo danh sách khám cùng tuần",
                "follow_up_schedule": "Không theo dõi — phỏng vấn một lần và trích hồ sơ",
                "estimand": {"population": "Người từ 60 tuổi tại cơ sở",
                             "treatment_condition": "Phơi nhiễm NSAID so với không phơi nhiễm",
                             "variable": "Xuất huyết tiêu hoá trên",
                             "intercurrent_events_strategy": "Không áp dụng (đo phơi nhiễm một lần)",
                             "population_summary_measure": "Tỷ số chênh (OR) hiệu chỉnh"},
                "background_problem": vi("Xuất huyết tiêu hoá trên ở người cao tuổi thường liên quan thuốc tự mua"),
                "evidence_summary": vi("Phân tích gộp quan sát (PMID 23137151) báo nguy cơ biến chứng tiêu hoá trên "
                                       "tăng với mọi NSAID, khác nhau theo loại"),
                "knowledge_gap": vi("Thiếu số liệu phơi nhiễm theo loại NSAID ở người cao tuổi Việt Nam"),
                "benefit_risk_rationale": vi("Không can thiệp; chỉ phỏng vấn và trích hồ sơ"),
                "study_schema_timeline": "Xác định ca → chọn 2 chứng ghép → phỏng vấn phơi nhiễm → trích hồ sơ đơn "
                                         "thuốc",
                "intervention_dose_adherence": "Không can thiệp; phơi nhiễm đo bằng phỏng vấn có hình thuốc và hồ sơ",
                "stopping_rescue_rules": "Không áp dụng — nghiên cứu quan sát",
                "critical_to_quality": vi("Người phỏng vấn không biết giả thuyết; cùng bộ câu hỏi cho ca và chứng"),
                "monitoring_plan": vi("Kiểm chất lượng phỏng vấn hằng tháng"),
            },
            "G3": {
                "effect_size": 1.84, "effect_type": "OR", "p0": 0.15, "dropout": 0.05,
                "alpha": 0.05, "power": 0.8, "hypothesis_type": "superiority",
                "effect_source": ("PMID: 23137151 (Castellsague 2012, Drug Saf) — ibuprofen và biến chứng tiêu hoá "
                                  "trên "
                                  "RR 1,84 (KTC 95% 1,54–2,20), mức thấp nhất trong các NSAID thông dụng"),
                "p0_source": vi("Giả định 15% người từ 60 tuổi khám ngoại trú dùng NSAID trong 30 ngày — chưa có số "
                                "liệu tại cơ sở"),
                "dropout_source": vi("Giả định 5% phiếu không dùng được — chưa có nguồn y văn"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": kc_bc["name"],
                "software": "run_g3_auto.py (bệnh–chứng, OR)",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }

    # ── 3. CHẨN ĐOÁN — độ chính xác của một chỉ số so với tiêu chuẩn tham chiếu
    kc_cd = {"name": "Độ chính xác chẩn đoán của FIB-4 đối với xơ hoá gan tiến triển",
             "measure": "Diện tích dưới đường cong ROC của FIB-4 so với đo độ đàn hồi gan ≥10 kPa",
             "timepoint": "Tại lần khám tuyển (FIB-4 và đo đàn hồi trong cùng 30 ngày)",
             "type": "nhị phân (có/không xơ hoá tiến triển theo tiêu chuẩn tham chiếu)"}
    kb["chan_doan"] = {
        "study": f"{tien_to}CHAN-DOAN",
        "thiet_ke": "diagnostic",
        "mo_ta": "Độ chính xác chẩn đoán (AUC), tiêu chuẩn tham chiếu là đo độ đàn hồi gan",
        "topic": ("Giá trị chẩn đoán của chỉ số FIB-4 trong phát hiện xơ hoá gan tiến triển ở người bệnh gan nhiễm mỡ "
                  "liên quan chuyển hoá điều trị ngoại trú"),
        "query_en": ('("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR '
                     'NAFLD[tiab] OR MASLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR '
                     'elastography[tiab]) AND '
                     '("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người trưởng thành có gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú"),
                "intervention": "Chỉ số FIB-4 (xét nghiệm cần đánh giá)",
                "comparison": "Đo độ đàn hồi gan thoáng qua (tiêu chuẩn tham chiếu)",
                "outcomes": ["AUC của FIB-4 đối với xơ hoá tiến triển", "Độ nhạy, độ đặc hiệu tại ngưỡng 1,3 và 2,67"],
                "primary_outcome": kc_cd["name"],
                "primary_outcome_measure": kc_cd["measure"],
                "primary_outcome_timepoint": kc_cd["timepoint"],
                "hypothesis_h0": "AUC của FIB-4 bằng 0,5",
                "hypothesis_h1": "AUC của FIB-4 khác 0,5",
                "expected_direction": "AUC của FIB-4 lớn hơn 0,5",
                "test_type": "superiority",
                "question_type": "diagnosis",
                **_finer(vi, "Đạt — phòng khám gan có máy đo đàn hồi và đủ người bệnh gan nhiễm mỡ",
                         "Đạt — FIB-4 rẻ, sẵn có ở tuyến ngoại trú",
                         "Đạt — chưa có số liệu kiểm định tại cơ sở (theo nền bằng chứng G0)",
                         "Đạt — xét nghiệm thường quy, nguy cơ tối thiểu",
                         "Đạt — giúp chọn người cần chuyển đo đàn hồi"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Phân tích gộp dữ liệu cá thể (PMID 34001645) báo AUROC 0,76 trong các "
                                            "nghiên cứu có sinh thiết; chưa có kiểm định ở người ngoại trú Việt Nam"),
                "registry_overlap_assessment": vi("CHƯA tra WHO ICTRP thật; nghiên cứu chẩn đoán tại một cơ sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "diagnostic",
                "design_rationale": vi("Câu hỏi chẩn đoán (G0 diagnosis) — nghiên cứu độ chính xác cắt ngang, mọi "
                                       "người tham gia làm cả xét nghiệm cần đánh giá và tiêu chuẩn tham chiếu"),
                "objectives": ["Xác định độ chính xác chẩn đoán của FIB-4 đối với xơ hoá gan tiến triển ở người bệnh "
                               "gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú"],
                "research_question": ("Ở người bệnh gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú, FIB-4 phát "
                                      "hiện xơ hoá gan tiến triển chính xác đến mức nào so với đo độ đàn hồi gan?"),
                "primary_outcome": dict(kc_cd),
                "secondary_outcomes": ["Độ nhạy, độ đặc hiệu, giá trị dự báo tại ngưỡng 1,3 và 2,67"],
                "population": ("Người trưởng thành có gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú"),
                "inclusion_criteria": ["Tuổi ≥18", "Gan nhiễm mỡ trên siêu âm kèm ≥1 yếu tố chuyển hoá"],
                "exclusion_criteria": ["Uống rượu nguy hại", "Viêm gan virus B hoặc C đang hoạt động",
                                       "Không đo được độ đàn hồi gan hợp lệ"],
                "setting": "Phòng khám gan mật ngoại trú bệnh viện (giả lập)",
                "study_period": "2027-03 đến 2027-12",
                "intervention_or_exposure": "Chỉ số FIB-4 tính từ tuổi, AST, ALT, tiểu cầu",
                "comparator": "Đo độ đàn hồi gan thoáng qua",
                "target_condition": "Xơ hoá gan tiến triển (tương đương F3–F4)",
                "reference_standard": ("Đo độ đàn hồi gan thoáng qua ≥10 kPa (≥10 lần đo hợp lệ, IQR/trung vị ≤30%), "
                                       "người đọc không biết kết quả FIB-4"),
                "recruitment_strategy": "Tuyển liên tiếp người bệnh đủ tiêu chuẩn đến khám",
                "follow_up_schedule": "Không theo dõi — xét nghiệm và đo đàn hồi trong cùng 30 ngày",
                "estimand": {"population": "Người bệnh gan nhiễm mỡ ngoại trú đủ tiêu chuẩn",
                             "treatment_condition": "Không áp dụng (độ chính xác chẩn đoán)",
                             "variable": "Có/không xơ hoá tiến triển theo tiêu chuẩn tham chiếu",
                             "intercurrent_events_strategy": "Không áp dụng (một lần đo)",
                             "population_summary_measure": "AUC kèm KTC 95%; độ nhạy, độ đặc hiệu"},
                "background_problem": vi("Không phải người bệnh gan nhiễm mỡ nào cũng tiếp cận được máy đo đàn hồi"),
                "evidence_summary": vi("Phân tích gộp dữ liệu cá thể (PMID 34001645) báo AUROC của FIB-4 0,76 cho xơ "
                                       "hoá tiến triển"),
                "knowledge_gap": vi("Chưa có kiểm định FIB-4 ở người ngoại trú Việt Nam"),
                "benefit_risk_rationale": vi("Xét nghiệm và đo đàn hồi thường quy, không xâm lấn"),
                "study_schema_timeline": "Tuyển → xét nghiệm máu (FIB-4) → đo đàn hồi trong 30 ngày → đối chiếu",
                "intervention_dose_adherence": "Không can thiệp điều trị; xét nghiệm làm một lần",
                "stopping_rescue_rules": "Không áp dụng — không can thiệp; kết quả bất thường chuyển bác sĩ điều trị",
                "critical_to_quality": vi("Làm mù người đo đàn hồi với FIB-4; tiêu chuẩn đo hợp lệ thống nhất"),
                "monitoring_plan": vi("Kiểm chất lượng đo đàn hồi hằng tháng"),
            },
            "G3": {
                "effect_size": 0.76, "effect_type": "AUC", "prevalence": 0.3, "dropout": 0.1,
                "alpha": 0.05, "power": 0.8, "hypothesis_type": "superiority",
                "effect_source": "PMID: 34001645 (Mózes 2021, Gut) — AUROC của FIB-4 cho xơ hoá tiến triển 0,76",
                "prevalence_source": ("PMID: 34001645 — 30% có xơ hoá tiến triển trong các nghiên cứu gộp (quần thể có "
                                      "sinh thiết, có thể cao hơn ngoại trú)"),
                "dropout_source": vi("Giả định 10% đo đàn hồi không hợp lệ — chưa có nguồn y văn"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": kc_cd["name"],
                "software": "run_g3_auto.py (Hanley–McNeil, AUC so với 0,5)",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }

    # ── 4. MÔ HÌNH DỰ BÁO — phát triển mô hình nguy cơ
    kc_db = {"name": "Nhập viện vì mọi nguyên nhân trong 12 tháng",
             "measure": "Có ≥1 lần nhập viện ≥24 giờ ghi trong hồ sơ hoặc người bệnh báo, đối chiếu giấy ra viện",
             "timepoint": "Trong 12 tháng kể từ lần khám tuyển", "type": "nhị phân"}
    kb["mo_hinh_du_bao"] = {
        "study": f"{tien_to}DU-BAO",
        "thiet_ke": "prediction",
        "mo_ta": "Phát triển mô hình dự báo nguy cơ (TRIPOD+AI), cỡ mẫu theo Riley",
        "topic": ("Phát triển mô hình dự báo nguy cơ nhập viện trong 12 tháng ở người suy tim điều trị ngoại trú"),
        "query_en": ('("Heart Failure"[MeSH] OR "heart failure"[tiab]) AND (outpatient*[tiab] OR ambulatory[tiab]) AND '
                     '("prediction model"[tiab] OR "risk score"[tiab] OR "prognostic model"[tiab]) AND '
                     '(hospitalization[tiab] OR hospitalisation[tiab] OR "Hospitalization"[MeSH])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người trưởng thành suy tim điều trị ngoại trú ổn định"),
                "intervention": "Các yếu tố dự báo ứng viên đo tại lần khám tuyển",
                "comparison": "Không áp dụng — phát triển mô hình dự báo",
                "outcomes": ["Nhập viện vì mọi nguyên nhân trong 12 tháng", "Nhập viện vì suy tim trong 12 tháng"],
                "primary_outcome": kc_db["name"],
                "primary_outcome_measure": kc_db["measure"],
                "primary_outcome_timepoint": kc_db["timepoint"],
                "hypothesis_h0": "Không áp dụng — phát triển mô hình, không kiểm định giả thuyết",
                "hypothesis_h1": "Không áp dụng — phát triển mô hình, không kiểm định giả thuyết",
                "expected_direction": "Không áp dụng — ước lượng hiệu năng (phân biệt, hiệu chuẩn) của mô hình",
                "test_type": "descriptive",
                "question_type": "prediction_model",
                "descriptive_justification": vi("Mục tiêu là phát triển và kiểm định nội mô hình dự báo, không so sánh "
                                                "nhóm"),
                **_finer(vi, "Đạt — phòng khám suy tim quản lý đủ người bệnh, theo dõi qua hồ sơ 12 tháng",
                         "Đạt — phân tầng nguy cơ giúp lên lịch tái khám",
                         "Đạt — chưa có mô hình kiểm định cho người suy tim ngoại trú tại cơ sở",
                         "Đạt — quan sát, không can thiệp",
                         "Đạt — áp dụng trực tiếp cho lịch tái khám và điều dưỡng gọi điện"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Các mô hình hiện có phát triển ở quần thể khác; chưa có mô hình kiểm định "
                                            "cho người suy tim ngoại trú Việt Nam"),
                "registry_overlap_assessment": vi("CHƯA tra WHO ICTRP thật; nghiên cứu quan sát tại một cơ sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "prediction",
                "design_rationale": vi("Câu hỏi dự báo (G0 prediction_model) — thuần tập tiến cứu phát triển mô hình, "
                                       "báo cáo theo TRIPOD+AI"),
                "objectives": ["Phát triển và kiểm định nội một mô hình dự báo nguy cơ nhập viện trong 12 tháng ở "
                               "người suy tim điều trị ngoại trú"],
                "research_question": ("Có thể dự báo nguy cơ nhập viện trong 12 tháng của người suy tim ngoại trú từ "
                                      "các yếu tố đo thường quy tại phòng khám với độ phân biệt và hiệu chuẩn chấp "
                                      "nhận "
                                      "được không?"),
                "primary_outcome": dict(kc_db),
                "secondary_outcomes": ["Nhập viện vì suy tim trong 12 tháng"],
                "population": ("Người trưởng thành suy tim điều trị ngoại trú ổn định"),
                "inclusion_criteria": ["Tuổi ≥18", "Chẩn đoán suy tim theo tiêu chuẩn ESC, điều trị ngoại trú ≥3 "
                                                   "tháng"],
                "exclusion_criteria": ["Đang chờ ghép tim hoặc dùng thiết bị hỗ trợ thất",
                                       "Kỳ vọng sống <12 tháng vì bệnh khác"],
                "setting": "Phòng khám suy tim ngoại trú bệnh viện (giả lập)",
                "study_period": "2027-03 đến 2029-03",
                "intervention_or_exposure": "Không can thiệp — yếu tố dự báo đo tại lần khám tuyển",
                "comparator": "Không áp dụng",
                "candidate_predictors": ["Tuổi", "Giới", "Phân suất tống máu thất trái", "NYHA", "NT-proBNP (log)",
                                         "eGFR", "Natri máu", "Hemoglobin", "Đái tháo đường",
                                         "Nhập viện vì suy tim trong 12 tháng trước"],
                "prediction_horizon": "12 tháng kể từ lần khám tuyển",
                "recruitment_strategy": "Tuyển liên tiếp người bệnh đủ tiêu chuẩn đến khám",
                "follow_up_schedule": "Tái khám thường quy; kiểm biến cố nhập viện tại tháng 6 và tháng 12",
                "estimand": {"population": "Người suy tim ngoại trú đủ tiêu chuẩn",
                             "treatment_condition": "Không áp dụng (dự báo)",
                             "variable": "Nhập viện vì mọi nguyên nhân trong 12 tháng",
                             "intercurrent_events_strategy": "Tử vong trước nhập viện: biến cố cạnh tranh, báo cáo "
                                                             "riêng",
                             "population_summary_measure": "Chỉ số C, độ dốc hiệu chuẩn, đường cong hiệu chuẩn"},
                "background_problem": vi("Người suy tim ngoại trú có nguy cơ nhập viện khác nhau nhưng lịch tái khám "
                                         "như nhau"),
                "evidence_summary": vi("Các mô hình nguy cơ suy tim hiện có chủ yếu từ quần thể châu Âu và Bắc Mỹ"),
                "knowledge_gap": vi("Thiếu mô hình kiểm định cho người suy tim ngoại trú Việt Nam"),
                "benefit_risk_rationale": vi("Quan sát, không can thiệp; nguy cơ tối thiểu"),
                "study_schema_timeline": "Tuyển → đo yếu tố dự báo → theo dõi 12 tháng → phát triển và kiểm định nội",
                "intervention_dose_adherence": "Không can thiệp; yếu tố dự báo đo một lần tại lần khám tuyển",
                "stopping_rescue_rules": "Không áp dụng — quan sát; điều trị theo bác sĩ phụ trách",
                "critical_to_quality": vi("Định nghĩa yếu tố dự báo và kết cục cố định trước; người xác định kết cục "
                                          "không biết giá trị yếu tố dự báo"),
                "monitoring_plan": vi("Kiểm dữ liệu thiếu và biến cố mỗi quý"),
            },
            "G3": {
                "confirmed_n": 900, "dropout": 0.05, "alpha": 0.05,
                "hypothesis_type": "descriptive_precision",
                "confirmed_n_method": ("pmsampsize theo Riley 2020 (BMJ 2020;368:m441, PMID 32188600), kết cục nhị "
                                       "phân: 10 tham số dự báo, tỷ lệ biến cố 20%, R²_CS giả định 0,095 (15% R²_CS "
                                       "tối "
                                       "đa — khuyến nghị thận trọng khi chưa có mô hình trước), co rút 0,9 ⇒ N tối "
                                       "thiểu 898 (~180 biến cố, EPP ≈ 18); chốt 900"),
                "dropout_source": vi("Giả định 5% mất dấu trong 12 tháng — chưa có nguồn y văn"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": kc_db["name"],
                "software": "Công thức Riley 2020 (tính tay, đối chiếu pmsampsize)",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }

    # ── 5. TỔNG QUAN HỆ THỐNG / PHÂN TÍCH GỘP
    kc_sr = {"name": "Nhập viện vì suy tim",
             "measure": "Biến cố nhập viện vì suy tim theo định nghĩa của từng thử nghiệm, gộp bằng RR",
             "timepoint": "Thời gian theo dõi dài nhất của từng thử nghiệm", "type": "nhị phân"}
    kb["tong_quan_gop"] = {
        "study": f"{tien_to}TONG-QUAN-GOP",
        "thiet_ke": "sr_ma",
        "mo_ta": "Tổng quan hệ thống và phân tích gộp RCT (PRISMA 2020, PRISMA-P)",
        "topic": ("Hiệu quả của thuốc ức chế SGLT2 lên nhập viện vì suy tim ở người đái tháo đường típ 2 không có suy "
                  "tim lúc đầu: tổng quan hệ thống và phân tích gộp các thử nghiệm ngẫu nhiên"),
        "query_en": ('("Sodium-Glucose Transporter 2 Inhibitors"[MeSH] OR "SGLT2 inhibitor*"[tiab] OR '
                     'empagliflozin[tiab] OR dapagliflozin[tiab] OR canagliflozin[tiab]) AND ("Diabetes Mellitus, '
                     'Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND ("heart failure"[tiab] OR "Heart Failure"[MeSH]) '
                     'AND ("randomized controlled trial"[pt] OR randomi*[tiab])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người trưởng thành đái tháo đường típ 2 không có suy tim lúc vào nghiên cứu"),
                "intervention": "Thuốc ức chế SGLT2",
                "comparison": "Giả dược hoặc điều trị chuẩn không có SGLT2",
                "outcomes": ["Nhập viện vì suy tim", "Tử vong tim mạch", "Biến cố bất lợi nghiêm trọng"],
                "primary_outcome": kc_sr["name"],
                "primary_outcome_measure": kc_sr["measure"],
                "primary_outcome_timepoint": kc_sr["timepoint"],
                "hypothesis_h0": "Nguy cơ nhập viện vì suy tim ở nhóm SGLT2 bằng nhóm chứng (RR = 1)",
                "hypothesis_h1": "Nguy cơ nhập viện vì suy tim ở nhóm SGLT2 khác nhóm chứng (RR ≠ 1)",
                "expected_direction": "Nhóm SGLT2 có nguy cơ nhập viện vì suy tim thấp hơn",
                "test_type": "superiority",
                "question_type": "treatment",
                **_finer(vi, "Đạt — dữ liệu đã công bố, không cần tuyển người",
                         "Đạt — lựa chọn thuốc hạ đường huyết có lợi tim mạch là câu hỏi thường gặp",
                         "Đạt — cập nhật thêm các thử nghiệm mới sau tổng quan gần nhất (theo nền bằng chứng G0)",
                         "Đạt — chỉ dùng dữ liệu đã công bố",
                         "Đạt — hỗ trợ lựa chọn thuốc ở người ĐTĐ típ 2 ngoại trú"),
                "evidence_reviewed_confirmed": True,
                "registry_manual_checked": {"ictrp": hom_nay, "prospero": hom_nay},
                "novelty_justification": vi("Đã có các phân tích gộp trước; tổng quan này cập nhật thử nghiệm mới và "
                                            "giới hạn ở người không có suy tim lúc đầu"),
                "registry_overlap_assessment": vi("CHƯA tra PROSPERO thật; cần tra trước khi đăng ký"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "sr_ma",
                "design_rationale": vi("Câu hỏi điều trị đã có nhiều RCT — tổng hợp định lượng bằng tổng quan hệ "
                                       "thống và phân tích gộp"),
                "objectives": ["Ước lượng hiệu quả của thuốc ức chế SGLT2 lên nhập viện vì suy tim ở người đái tháo "
                               "đường típ 2 không có suy tim lúc đầu"],
                "research_question": ("Ở người đái tháo đường típ 2 không có suy tim lúc đầu, thuốc ức chế SGLT2 có "
                                      "giảm nhập viện vì suy tim so với giả dược hoặc điều trị chuẩn không?"),
                "primary_outcome": dict(kc_sr),
                "secondary_outcomes": ["Tử vong tim mạch", "Biến cố bất lợi nghiêm trọng"],
                "population": ("Người trưởng thành đái tháo đường típ 2 không có suy tim lúc vào nghiên cứu"),
                "inclusion_criteria": ["Thử nghiệm ngẫu nhiên có đối chứng", "Người trưởng thành ĐTĐ típ 2",
                                       "So sánh thuốc ức chế SGLT2 với giả dược hoặc điều trị chuẩn",
                                       "Báo cáo nhập viện vì suy tim"],
                "exclusion_criteria": ["Thử nghiệm chỉ tuyển người suy tim lúc đầu", "Theo dõi <24 tuần",
                                       "Không tách được số liệu nhóm không suy tim"],
                "setting": "Tổng quan dữ liệu đã công bố (không có cơ sở tuyển)",
                "study_period": "2027-03 đến 2027-12",
                "intervention_or_exposure": "Thuốc ức chế SGLT2 bất kỳ, mọi liều",
                "comparator": "Giả dược hoặc điều trị chuẩn không có SGLT2",
                "information_sources": ["PubMed/MEDLINE", "Embase", "Cochrane CENTRAL", "ClinicalTrials.gov",
                                        "WHO ICTRP"],
                "search_strategy": ("Chiến lược tìm kết hợp MeSH và từ khoá cho thuốc ức chế SGLT2, ĐTĐ típ 2 và bộ "
                                    "lọc RCT Cochrane; báo cáo theo PRISMA-S"),
                "search_last_date": "2027-06-30",
                "study_selection_process": ("Hai người sàng lọc độc lập tiêu đề–tóm tắt rồi toàn văn; bất đồng do "
                                            "người thứ ba quyết định"),
                "recruitment_strategy": "Không áp dụng — dữ liệu đã công bố",
                "follow_up_schedule": "Không áp dụng — dữ liệu đã công bố",
                "estimand": {"population": "Người ĐTĐ típ 2 không suy tim lúc đầu trong các RCT",
                             "treatment_condition": "SGLT2 so với giả dược hoặc điều trị chuẩn",
                             "variable": "Nhập viện vì suy tim",
                             "intercurrent_events_strategy": "Theo định nghĩa của từng thử nghiệm (ITT)",
                             "population_summary_measure": "RR gộp (mô hình hiệu ứng ngẫu nhiên, REML, "
                                                           "Hartung–Knapp)"},
                "background_problem": vi("Suy tim là biến chứng thường gặp ở người ĐTĐ típ 2"),
                "evidence_summary": vi("Các thử nghiệm kết cục tim mạch lớn báo giảm nhập viện vì suy tim với thuốc ức "
                                       "chế SGLT2"),
                "knowledge_gap": vi("Ước lượng riêng cho người không có suy tim lúc đầu chưa được cập nhật"),
                "benefit_risk_rationale": vi("Không có người tham gia trực tiếp"),
                "study_schema_timeline": ("Đăng ký PROSPERO → tìm kiếm → sàng lọc → trích xuất → đánh giá RoB 2 → "
                                          "gộp → "
                                          "GRADE"),
                "intervention_dose_adherence": "Không áp dụng — trích liều và tuân thủ theo báo cáo của từng thử "
                                               "nghiệm",
                "stopping_rescue_rules": "Không áp dụng — tổng quan dữ liệu đã công bố",
                "critical_to_quality": vi("Trích xuất kép độc lập; RoB 2 hai người"),
                "monitoring_plan": vi("Đối chiếu bảng trích xuất sau mỗi 5 thử nghiệm"),
            },
            "G3": {
                "confirmed_n": 25462, "dropout": 0.0, "alpha": 0.05,
                "hypothesis_type": "superiority",
                "confirmed_n_method": ("RIS cho kết cục chính: tỷ lệ biến cố nhóm chứng GIẢ ĐỊNH 3%, giảm nguy cơ "
                                       "tương "
                                       "đối 25%, α 0,05, lực 90%, hiệu chỉnh dị biệt D² 25% ⇒ 25 462 người; dùng làm "
                                       "ngưỡng TSA"),
                "dropout_source": vi("Không áp dụng — tổng quan dữ liệu đã công bố"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": kc_sr["name"],
                "software": "RIS/TSA (tính tay, đối chiếu phần mềm TSA)",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }

    # ── 6. ĐỊNH TÍNH — phân tích chủ đề
    kb["dinh_tinh"] = {
        "study": f"{tien_to}DINH-TINH",
        "thiet_ke": "qualitative",
        "mo_ta": "Định tính, phỏng vấn sâu, phân tích chủ đề, cỡ mẫu theo bão hoà (COREQ)",
        "topic": ("Trải nghiệm và rào cản khi bắt đầu tiêm insulin của người đái tháo đường típ 2 điều trị ngoại trú: "
                  "nghiên cứu định tính"),
        "query_en": ('("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND (insulin[tiab]) AND '
                     '("psychological insulin resistance"[tiab] OR barrier*[tiab] OR experience*[tiab]) AND '
                     '("Qualitative Research"[MeSH] OR qualitative[tiab] OR interview*[tiab])'),
        "cong_dung_mong_doi": "G5",
        "pi": {
            "G0": {
                "population": ("Người trưởng thành đái tháo đường típ 2 điều trị ngoại trú được chỉ định bắt đầu "
                                 "tiêm insulin"),
                "intervention": "Không áp dụng — nghiên cứu định tính (hiện tượng: trải nghiệm bắt đầu insulin)",
                "comparison": "Không áp dụng — nghiên cứu định tính",
                "outcomes": ["Chủ đề về trải nghiệm và rào cản khi bắt đầu insulin"],
                "primary_outcome": "Trải nghiệm và rào cản khi bắt đầu tiêm insulin",
                "primary_outcome_measure": "Chủ đề rút ra từ phỏng vấn sâu bán cấu trúc (phân tích chủ đề)",
                "primary_outcome_timepoint": "Trong 3 tháng sau khi được chỉ định insulin",
                "hypothesis_h0": "Không áp dụng — nghiên cứu định tính",
                "hypothesis_h1": "Không áp dụng — nghiên cứu định tính",
                "expected_direction": "Không áp dụng — nghiên cứu định tính",
                "test_type": "descriptive",
                "question_type": "qualitative",
                "descriptive_justification": vi("Mục tiêu là hiểu trải nghiệm và rào cản, không ước lượng hay so sánh"),
                **_finer(vi, "Đạt — phòng khám nội tiết có đủ người được chỉ định insulin mỗi tháng",
                         "Đạt — trì hoãn insulin là vấn đề thực hành thường gặp",
                         "Đạt — chưa có dữ liệu định tính tại cơ sở (theo nền bằng chứng G0)",
                         "Đạt — phỏng vấn có đồng ý, nguy cơ tối thiểu",
                         "Đạt — dùng để thiết kế tư vấn bắt đầu insulin"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Nghiên cứu định tính về bắt đầu insulin chủ yếu ở quốc gia thu nhập cao; "
                                            "chưa có ở người ngoại trú Việt Nam"),
                "registry_overlap_assessment": vi("CHƯA tra WHO ICTRP thật; nghiên cứu định tính tại một cơ sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "qualitative",
                "design_rationale": vi("Câu hỏi định tính (G0 qualitative) — phỏng vấn sâu bán cấu trúc, phân tích "
                                       "chủ đề, báo cáo theo COREQ"),
                "objectives": ["Mô tả trải nghiệm và rào cản khi bắt đầu tiêm insulin của người đái tháo đường típ 2 "
                               "điều trị ngoại trú"],
                "research_question": ("Người đái tháo đường típ 2 điều trị ngoại trú trải nghiệm việc bắt đầu tiêm "
                                      "insulin như thế nào, và điều gì cản trở họ?"),
                "central_phenomenon": "Trải nghiệm và rào cản khi bắt đầu tiêm insulin",
                "qualitative_approach": "Phân tích chủ đề phản tư (reflexive thematic analysis, Braun & Clarke)",
                "data_collection_method": "Phỏng vấn sâu bán cấu trúc 45–60 phút, ghi âm có đồng ý, gỡ băng nguyên văn",
                "saturation_criterion": "Dừng khi 3 phỏng vấn liên tiếp không xuất hiện mã mới (tối thiểu 12 phỏng "
                                        "vấn)",
                "primary_outcome": {"name": "Trải nghiệm và rào cản khi bắt đầu tiêm insulin",
                                    "measure": "Chủ đề rút ra từ phỏng vấn sâu bán cấu trúc (phân tích chủ đề)",
                                    "timepoint": "Trong 3 tháng sau khi được chỉ định insulin", "type": "định tính"},
                "secondary_outcomes": [],
                "population": ("Người trưởng thành ĐTĐ típ 2 điều trị ngoại trú được chỉ định bắt đầu insulin"),
                "inclusion_criteria": ["Tuổi ≥18", "Được chỉ định bắt đầu insulin trong 3 tháng qua",
                                       "Đồng ý phỏng vấn và ghi âm"],
                "exclusion_criteria": ["Suy giảm nhận thức hoặc không giao tiếp được bằng tiếng Việt"],
                "setting": "Phòng khám nội tiết ngoại trú bệnh viện (giả lập)",
                "study_period": "2027-03 đến 2027-09",
                "intervention_or_exposure": "Không áp dụng — nghiên cứu định tính",
                "comparator": "Không áp dụng",
                "recruitment_strategy": ("Chọn mẫu có chủ đích đa dạng theo tuổi, giới, trình độ học vấn và việc đã "
                                         "bắt đầu hay còn trì hoãn insulin"),
                "follow_up_schedule": "Không theo dõi — một cuộc phỏng vấn; phỏng vấn lại nếu cần làm rõ",
                "estimand": {"population": "Không áp dụng (định tính)", "treatment_condition": "Không áp dụng",
                             "variable": "Không áp dụng", "intercurrent_events_strategy": "Không áp dụng",
                             "population_summary_measure": "Không áp dụng"},
                "background_problem": vi("Nhiều người ĐTĐ típ 2 trì hoãn insulin dù đã có chỉ định"),
                "evidence_summary": vi("Y văn quốc tế mô tả «kháng insulin tâm lý»; bối cảnh Việt Nam chưa được mô tả"),
                "knowledge_gap": vi("Chưa có dữ liệu định tính ở người ngoại trú Việt Nam"),
                "benefit_risk_rationale": vi("Phỏng vấn có đồng ý; nguy cơ khó chịu cảm xúc thấp, có thể dừng bất cứ "
                                             "lúc nào"),
                "study_schema_timeline": "Chọn mẫu có chủ đích → phỏng vấn → mã hoá song song → phân tích chủ đề",
                "intervention_dose_adherence": "Không áp dụng — không can thiệp",
                "stopping_rescue_rules": "Dừng phỏng vấn khi người tham gia khó chịu; chuyển tư vấn nếu cần",
                "critical_to_quality": vi("Hai người mã hoá độc lập; nhật ký phản tư; kiểm chứng với người tham gia"),
                "monitoring_plan": vi("Họp nhóm phân tích sau mỗi 4 phỏng vấn để theo dõi bão hoà"),
            },
            "G3": {
                "confirmed_n": 20, "dropout": 0.0,
                "hypothesis_type": "descriptive_precision",
                "confirmed_n_method": ("Bão hoà dữ liệu: dự kiến 20 phỏng vấn, dừng khi 3 phỏng vấn liên tiếp không có "
                                       "mã mới (tối thiểu 12)"),
                "saturation_stopping_rule": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới (tối thiểu 12 phỏng vấn)",
                "dropout_source": vi("Không áp dụng — người từ chối được thay bằng người cùng nhóm chọn mẫu"),
                **_CO_XAC_NHAN_G3,
                "powered_for_outcome": "Trải nghiệm và rào cản khi bắt đầu tiêm insulin",
                "software": "Không áp dụng — cỡ mẫu theo bão hoà",
            },
        },
        "xac_nhan": _XAC_NHAN,
    }
    return kb


# ══════════════════════════════════════════════════════════════════════════════════════════════ bộ biến + ma trận
# Hồ sơ biến của 6 đề tài mới — việc G3-T2 (agent bien-so-nghien-cuu) dựng ở G3 (G3-AUTO-19 đòi `_bo-bien-rieng.csv` +
# ma trận mục tiêu → biến). Hai kịch bản đầu (RCT, cắt ngang) đã có `bien_so` ở gia_lap_dinh_ky (#281). Biến đúng cái
# SAP §4/§5 dùng, không thừa không thiếu.
_CO_KHONG = "0, Không | 1, Có"
_GIOI = "0, Nữ | 1, Nam"


def _ho_so_bien_6() -> Dict[str, Dict[str, list]]:
    """Bộ biến (tên, loại, nhãn, lựa chọn, kiểm, mục) + ma trận của 6 kịch bản mới."""
    so = "integer"
    return {
        "thuan_tap_phoi_nhiem": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "Trích hồ sơ"),
                ("tuoi", "text", "Tuổi tại ngày bắt đầu theo dõi (năm)", "", so, "Trích hồ sơ"),
                ("gioi", "radio", "Giới", _GIOI, "", "Trích hồ sơ"),
                ("ppi_dai_han", "radio", "Dùng PPI liên tục ≥12 tháng (PHƠI NHIỄM)", _CO_KHONG, "", "Phơi nhiễm"),
                ("corticoid", "yesno", "Dùng corticoid toàn thân ≥3 tháng", "", "", "Hiệp biến"),
                ("loang_xuong", "yesno", "Chẩn đoán loãng xương trước ngày bắt đầu", "", "", "Hiệp biến"),
                ("gay_xuong_3nam", "radio", "Gãy xương mới trong 3 năm (KẾT CỤC CHÍNH)", _CO_KHONG, "", "Kết cục"),
                ("thoi_gian_theo_doi", "text", "Thời gian theo dõi (tháng)", "", so, "Kết cục"),
            ],
            "ma_tran": [
                ("1", "Gãy xương mọi vị trí trong 3 năm", "ket_cuc_chinh", "gay_xuong_3nam", "nhi_phan", "KC1",
                 "Hồ sơ + phim X-quang", "§4"),
                ("1", "Dùng thuốc ức chế bơm proton kéo dài", "phoi_nhiem", "ppi_dai_han", "nhi_phan", "PN1",
                 "Đơn thuốc cấp phát", "§4"),
                ("1", "Tuổi", "hiep_bien", "tuoi", "lien_tuc", "HB1", "Hồ sơ", "§5"),
                ("1", "Corticoid toàn thân", "hiep_bien", "corticoid", "nhi_phan", "HB2", "Đơn thuốc", "§5"),
                ("1", "Loãng xương trước đó", "hiep_bien", "loang_xuong", "nhi_phan", "HB3", "Hồ sơ", "§5"),
            ],
        },
        "benh_chung": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "Tuyển chọn"),
                ("nhom_ca", "radio", "Nhóm (KẾT CỤC CHÍNH: xuất huyết tiêu hoá trên)",
                 "0, Chứng | 1, Ca xuất huyết tiêu hoá trên", "", "Tuyển chọn"),
                ("tuoi", "text", "Tuổi (năm)", "", so, "Phỏng vấn"),
                ("gioi", "radio", "Giới", _GIOI, "", "Phỏng vấn"),
                ("nsaid_30ngay", "radio", "Dùng NSAID trong 30 ngày trước ngày chỉ điểm (PHƠI NHIỄM)", _CO_KHONG, "",
                 "Phơi nhiễm"),
                ("chong_dong", "yesno", "Dùng thuốc chống đông/chống kết tập", "", "", "Phơi nhiễm"),
                ("tien_su_loet", "yesno", "Tiền sử loét dạ dày–tá tràng", "", "", "Hiệp biến"),
            ],
            "ma_tran": [
                ("1", "Xuất huyết tiêu hoá trên", "ket_cuc_chinh", "nhom_ca", "nhi_phan", "TC1",
                 "Định nghĩa ca qua nội soi", "§4"),
                ("1", "Phơi nhiễm NSAID trong 30 ngày", "phoi_nhiem", "nsaid_30ngay", "nhi_phan", "PN1",
                 "Phỏng vấn có hình thuốc + hồ sơ", "§4"),
                ("1", "Thuốc chống đông", "hiep_bien", "chong_dong", "nhi_phan", "PN2", "Phỏng vấn + hồ sơ", "§5"),
                ("1", "Tiền sử loét", "hiep_bien", "tien_su_loet", "nhi_phan", "HB1", "Phỏng vấn + hồ sơ", "§5"),
            ],
        },
        "chan_doan": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "Tuyển chọn"),
                ("tuoi", "text", "Tuổi (năm)", "", so, "Ban đầu"),
                ("gioi", "radio", "Giới", _GIOI, "", "Ban đầu"),
                ("ast", "text", "AST (U/L)", "", so, "Xét nghiệm"),
                ("alt", "text", "ALT (U/L)", "", so, "Xét nghiệm"),
                ("tieu_cau", "text", "Tiểu cầu (G/L)", "", so, "Xét nghiệm"),
                ("fib4", "calc", "FIB-4 (XÉT NGHIỆM CẦN ĐÁNH GIÁ)",
                 "round(([tuoi]*[ast])/([tieu_cau]*sqrt([alt])),2)", "", "Xét nghiệm"),
                ("lsm_kpa", "text", "Độ đàn hồi gan (kPa)", "", "number", "Tiêu chuẩn tham chiếu"),
                ("xo_hoa_tien_trien", "radio", "Xơ hoá tiến triển theo đo đàn hồi ≥10 kPa (KẾT CỤC CHÍNH)",
                 _CO_KHONG, "", "Tiêu chuẩn tham chiếu"),
            ],
            "ma_tran": [
                ("1", "Xơ hoá gan tiến triển", "ket_cuc_chinh", "xo_hoa_tien_trien", "nhi_phan", "TC1",
                 "Đo độ đàn hồi gan thoáng qua", "§4"),
                ("1", "Chỉ số FIB-4", "phoi_nhiem", "fib4", "lien_tuc", "XN4", "Xét nghiệm máu", "§4"),
                ("1", "Tuổi", "mo_ta", "tuoi", "lien_tuc", "B1", "Phiếu ban đầu", "§4"),
            ],
        },
        "mo_hinh_du_bao": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "Tuyển chọn"),
                ("tuoi", "text", "Tuổi (năm)", "", so, "Yếu tố dự báo"),
                ("gioi", "radio", "Giới", _GIOI, "", "Yếu tố dự báo"),
                ("lvef", "text", "Phân suất tống máu thất trái (%)", "", so, "Yếu tố dự báo"),
                ("nyha", "radio", "Phân độ NYHA", "1, I | 2, II | 3, III | 4, IV", "", "Yếu tố dự báo"),
                ("ntprobnp", "text", "NT-proBNP (pg/mL)", "", "number", "Yếu tố dự báo"),
                ("egfr", "text", "eGFR (mL/phút/1,73 m²)", "", so, "Yếu tố dự báo"),
                ("natri", "text", "Natri máu (mmol/L)", "", so, "Yếu tố dự báo"),
                ("hb", "text", "Hemoglobin (g/dL)", "", "number", "Yếu tố dự báo"),
                ("dtd", "yesno", "Đái tháo đường", "", "", "Yếu tố dự báo"),
                ("nv_suy_tim_truoc", "yesno", "Nhập viện vì suy tim trong 12 tháng trước", "", "", "Yếu tố dự báo"),
                ("nhap_vien_12t", "radio", "Nhập viện mọi nguyên nhân trong 12 tháng (KẾT CỤC CHÍNH)", _CO_KHONG, "",
                 "Kết cục"),
            ],
            "ma_tran": [
                ("1", "Nhập viện trong 12 tháng", "ket_cuc_chinh", "nhap_vien_12t", "nhi_phan", "KC1",
                 "Hồ sơ + giấy ra viện", "§4"),
                ("1", "Tuổi", "yeu_to", "tuoi", "lien_tuc", "YT1", "Phiếu ban đầu", "§4"),
                ("1", "Phân suất tống máu", "yeu_to", "lvef", "lien_tuc", "YT3", "Siêu âm tim", "§4"),
                ("1", "NT-proBNP", "yeu_to", "ntprobnp", "lien_tuc", "YT5", "Xét nghiệm", "§4"),
                ("1", "eGFR", "yeu_to", "egfr", "lien_tuc", "YT6", "Xét nghiệm", "§4"),
            ],
        },
        "tong_quan_gop": {
            "bo_bien": [
                ("study_id", "text", "Mã thử nghiệm (tác giả–năm)", "", "", "Trích xuất"),
                ("thuoc_sglt2", "dropdown", "Thuốc ức chế SGLT2",
                 "1, Empagliflozin | 2, Dapagliflozin | 3, Canagliflozin | 4, Ertugliflozin | 5, Khác", "",
                 "Trích xuất"),
                ("n_can_thiep", "text", "Số người nhánh SGLT2", "", so, "Kết cục"),
                ("bien_co_can_thiep", "text", "Số người nhập viện vì suy tim — nhánh SGLT2", "", so, "Kết cục"),
                ("n_chung", "text", "Số người nhánh chứng", "", so, "Kết cục"),
                ("bien_co_chung", "text", "Số người nhập viện vì suy tim — nhánh chứng", "", so, "Kết cục"),
                ("theo_doi_thang", "text", "Thời gian theo dõi trung vị (tháng)", "", "number", "Trích xuất"),
                ("rob2_tong", "radio", "RoB 2 — đánh giá chung", "1, Thấp | 2, Có lo ngại | 3, Cao", "",
                 "Nguy cơ sai lệch"),
            ],
            "ma_tran": [
                ("1", "Nhập viện vì suy tim", "ket_cuc_chinh", "bien_co_can_thiep", "dem", "KC1",
                 "Bảng trích xuất kép", "§4"),
                ("1", "Nhập viện vì suy tim nhánh chứng", "ket_cuc_chinh", "bien_co_chung", "dem", "KC2",
                 "Bảng trích xuất kép", "§4"),
                ("1", "Thuốc ức chế SGLT2", "phoi_nhiem", "thuoc_sglt2", "danh_dinh", "TX1", "Bảng trích xuất", "§5"),
                ("1", "Nguy cơ sai lệch", "phan_tang", "rob2_tong", "thu_tu", "RB1", "RoB 2", "§5"),
            ],
        },
        "dinh_tinh": {
            "bo_bien": [
                ("ma_nguoi_tham_gia", "text", "Mã người tham gia", "", "", "Đặc điểm người tham gia"),
                ("tuoi", "text", "Tuổi (năm)", "", so, "Đặc điểm người tham gia"),
                ("gioi", "radio", "Giới", _GIOI, "", "Đặc điểm người tham gia"),
                ("da_bat_dau_insulin", "yesno", "Đã bắt đầu tiêm insulin", "", "", "Đặc điểm người tham gia"),
                ("thoi_gian_dtd", "text", "Thời gian mắc ĐTĐ (năm)", "", so, "Đặc điểm người tham gia"),
                ("chu_de", "notes", "Chủ đề/mã rút ra từ phỏng vấn (KẾT CỤC CHÍNH)", "", "", "Phân tích"),
            ],
            "ma_tran": [
                ("1", "Trải nghiệm và rào cản khi bắt đầu tiêm insulin", "ket_cuc_chinh", "chu_de", "van_ban", "PV",
                 "Hướng dẫn phỏng vấn sâu bán cấu trúc", "§4"),
                ("1", "Đã bắt đầu insulin", "mo_ta", "da_bat_dau_insulin", "nhi_phan", "DD4",
                 "Phiếu đặc điểm người tham gia", "§4"),
            ],
        },
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════ hồ sơ trọn vòng
# Hồ sơ của từng vai sau G3 (G2 trở đi) — dùng bởi `gia_lap_tron_vong.py`. Ngày tương đối «<HOM_NAY>»/«<+30>» thay lúc
# chạy. Tham số ký của Hội đồng là ô CHỈ CÓ SAU phê duyệt (số, ngày) — giá trị giả lập.
def _ky_g2(che_do: str, dang_ky: str, *, mien_icf: bool = False, quyet_dinh: str = "APPROVED",
           registry: str = "", ma_dk: str = "") -> Dict[str, Any]:
    ky: Dict[str, Any] = {"--g2-ethics-committee-ref": "GIA-LAP-HOI-DONG", "--g2-approval-number": "GL-001/2026",
                          "--g2-approval-date": "<HOM_NAY>", "--g2-valid-until": "<+730>",
                          "--g2-protocol-version": "1.0", "--g2-ethics-decision": quyet_dinh,
                          "--g2-recruitment-mode": che_do, "--g2-registration-status": dang_ky,
                          "--g2-approval-scope": "Toàn bộ đề cương v1.0 (giả lập)"}
    if mien_icf:
        ky["--g2-icf-waiver-approved"] = True
    else:
        ky["--g2-icf-version"] = "1.0"
    if dang_ky == "REGISTERED":
        ky.update({"--g2-registry": registry, "--g2-registration-id": ma_dk, "--g2-registration-date": "<HOM_NAY>"})
    if che_do == "PROSPECTIVE_NEW_PARTICIPANTS":
        ky["--g2-first-enrolment-date"] = "<+30>"
    return ky


def ho_so_tron_vong() -> Dict[str, Dict[str, Any]]:
    """gate_params.G2 + tham số ký G2 + câu trả lời riêng của các vai theo từng kịch bản."""
    chung = {"protocol_version": "1.0", "icf_version": "1.0"}
    tien_cuu = "PROSPECTIVE_NEW_PARTICIPANTS"
    return {
        "rct_nhi_phan": {
            "G2": {**chung, "public_title": "Tin nhắn nhắc uống thuốc giúp kiểm soát huyết áp (giả lập)",
                   "health_condition": "Tăng huyết áp nguyên phát (ICD-10 I10)", "primary_purpose": "treatment",
                   "intervention_type": "behavioral", "recruitment_mode": tien_cuu, "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov", "safety_plan_confirmed": True},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999999"),
        },
        "cat_ngang_mo_ta": {
            "G2": {**chung, "public_title": "Tỷ lệ kiểm soát huyết áp ở người điều trị ngoại trú (giả lập)",
                   "health_condition": "Tăng huyết áp nguyên phát (ICD-10 I10)", "recruitment_mode": tien_cuu,
                   "registration_required": False},
            "ky_G2": _ky_g2(tien_cuu, "NOT_REQUIRED"),
        },
        "thuan_tap_phoi_nhiem": {
            "G2": {**chung, "public_title": "PPI kéo dài và gãy xương ở người cao tuổi (giả lập)",
                   "health_condition": "Gãy xương do loãng xương (ICD-10 M80)",
                   "recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA", "registration_required": False,
                   "icf_waiver_requested": True},
            "ky_G2": _ky_g2("RETROSPECTIVE_SECONDARY_DATA", "NOT_REQUIRED", mien_icf=True),
        },
        "benh_chung": {
            "G2": {**chung, "public_title": "NSAID và xuất huyết tiêu hoá trên ở người cao tuổi (giả lập)",
                   "health_condition": "Xuất huyết tiêu hoá trên (ICD-10 K92.2)", "recruitment_mode": tien_cuu,
                   "registration_required": False},
            "ky_G2": _ky_g2(tien_cuu, "NOT_REQUIRED"),
        },
        "chan_doan": {
            "G2": {**chung, "public_title": "FIB-4 phát hiện xơ hoá gan tiến triển (giả lập)",
                   "health_condition": "Gan nhiễm mỡ liên quan chuyển hoá (ICD-10 K76.0)",
                   "recruitment_mode": tien_cuu, "registration_required": False},
            "ky_G2": _ky_g2(tien_cuu, "NOT_REQUIRED"),
        },
        "mo_hinh_du_bao": {
            "G2": {**chung, "public_title": "Mô hình dự báo nhập viện ở người suy tim ngoại trú (giả lập)",
                   "health_condition": "Suy tim (ICD-10 I50)", "recruitment_mode": tien_cuu,
                   "registration_required": False},
            "ky_G2": _ky_g2(tien_cuu, "NOT_REQUIRED"),
        },
        "tong_quan_gop": {
            "G2": {"protocol_version": "1.0", "public_title": "SGLT2 và nhập viện vì suy tim ở ĐTĐ típ 2 (giả lập)",
                   "health_condition": "Đái tháo đường típ 2 (ICD-10 E11)",
                   "recruitment_mode": "NOT_APPLICABLE", "registration_required": True,
                   "registration_registry": "PROSPERO", "icf_waiver_requested": True},
            "ky_G2": {**_ky_g2("NOT_APPLICABLE", "REGISTERED", mien_icf=True,
                               quyet_dinh="EXEMPT", registry="PROSPERO", ma_dk="CRD42099999999"),
                      "--g2-first-search-date": "<+15>"},
        },
        "dinh_tinh": {
            "G2": {**chung, "public_title": "Trải nghiệm bắt đầu tiêm insulin (giả lập)",
                   "health_condition": "Đái tháo đường típ 2 (ICD-10 E11)", "recruitment_mode": tien_cuu,
                   "registration_required": False},
            "ky_G2": _ky_g2(tien_cuu, "NOT_REQUIRED"),
        },
    }


def bien_so_them() -> Dict[str, Dict[str, list]]:
    """Bộ biến + ma trận của 6 kịch bản mới theo khuôn `bien_so` của canary.

    Mỗi biến: (tên, loại, nhãn, lựa chọn, kiểm, min, max)."""
    return {ma: {"bo_bien": [(t, k, n, lc, v, "", "") for t, k, n, lc, v, _muc in hs["bo_bien"]],
                 "ma_tran": list(hs["ma_tran"])}
            for ma, hs in _ho_so_bien_6().items()}
