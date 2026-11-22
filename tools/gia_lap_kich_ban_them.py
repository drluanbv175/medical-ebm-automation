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

from typing import Any, Callable, Dict, List, Tuple

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


# 21/11/2026 (K17 STROBE 9/19 — «chiều tác động của sai lệch»): sổ sai lệch RIÊNG mà PI của từng đề tài quan sát khai ở
# `gate_params.G1.bias_controls` (cùng khuôn {sai_lech, bien_phap, chieu} với đề cương BTM thật). Biện pháp chỉ nhắc
# điều đã có trong quyết định khác của cùng hồ sơ (tiêu chuẩn chọn/loại, CTQ, SAP §5/§6/§9) — không thêm thủ tục mới.
SAI_LECH_PI: Dict[str, List[Dict[str, str]]] = {
    "cohort": [
        {"sai_lech": "Nhiễu do chỉ định: người dùng thuốc ức chế bơm proton kéo dài có nhiều bệnh kèm hơn",
         "bien_phap": ("Hiệu chỉnh đa biến theo DAG (tuổi, corticoid toàn thân, loãng xương trước đó); phân tích "
                       "độ nhạy với định nghĩa thay thế của phơi nhiễm"),
         "chieu": "Nhiễu còn sót có thể làm nguy cơ tương đối được ước lượng cao hơn thực tế"},
        {"sai_lech": "Sai lệch phân loại phơi nhiễm từ đơn cấp phát (thuốc mua ngoài không được ghi nhận)",
         "bien_phap": "Định nghĩa phơi nhiễm bằng ít nhất 80% số ngày có thuốc theo đơn cấp trong 12 tháng",
         "chieu": "Phân loại sai không phân biệt theo kết cục kéo ước lượng về giá trị 1 (thấp hơn thực tế)"},
        {"sai_lech": "Sai lệch thông tin do mã chẩn đoán gãy xương",
         "bien_phap": "Kiểm 10% hồ sơ biến cố bằng phim X-quang",
         "chieu": "Ghi mã thiếu như nhau ở hai nhóm làm nguy cơ tương đối được ước lượng thấp hơn thực tế"},
        {"sai_lech": "Sai lệch do mất theo dõi khi người bệnh chuyển nơi khám",
         "bien_phap": "Loại người theo dõi dưới 6 tháng; gán đa trị kết cục thiếu; phân tích độ nhạy loại người theo "
                      "dõi dưới 12 tháng",
         "chieu": ("Chiều lệch không xác định trước; nếu người mất theo dõi có nguy cơ gãy xương cao hơn, ước "
                   "lượng thấp hơn thực tế")},
    ],
    "case_control": [
        {"sai_lech": "Sai lệch nhớ lại phơi nhiễm NSAID (ca nhớ thuốc đã dùng kỹ hơn chứng)",
         "bien_phap": "Cùng bộ câu hỏi cho ca và chứng; người phỏng vấn không biết giả thuyết; đối chiếu với hồ sơ đơn "
                      "thuốc",
         "chieu": "Ca khai phơi nhiễm đầy đủ hơn chứng làm tỷ số chênh được ước lượng cao hơn thực tế"},
        {"sai_lech": "Sai lệch chọn nhóm chứng từ người khám ngoại trú",
         "bien_phap": "Chọn chứng cùng cơ sở và cùng tuần với ca, ghép theo giới và nhóm tuổi 5 năm",
         "chieu": "Nếu người khám ngoại trú dùng NSAID nhiều hơn quần thể nguồn, tỷ số chênh được ước lượng thấp hơn "
                  "thực tế"},
        {"sai_lech": "Nhiễu do thuốc chống đông, chống kết tập tiểu cầu và tiền sử loét",
         "bien_phap": "Thu thập và hiệu chỉnh trong mô hình hồi quy logistic có điều kiện",
         "chieu": "Nhiễu còn sót có thể làm tỷ số chênh được ước lượng cao hơn thực tế"},
    ],
    "cross_sectional": [
        {"sai_lech": "Sai lệch chọn do chọn mẫu liên tiếp người đến khám",
         "bien_phap": "Tuyển liên tiếp mọi người đủ tiêu chuẩn trong các ngày khám; ghi số người từ chối và lý do",
         "chieu": "Người tái khám đều đặn có khả năng kiểm soát tốt hơn người bỏ khám nên tỷ lệ kiểm soát có thể được "
                  "ước lượng cao hơn thực tế"},
        {"sai_lech": "Sai lệch đo lường huyết áp (hiệu ứng áo choàng trắng)",
         "bien_phap": "Đo chuẩn hoá bằng máy đã hiệu chuẩn, đo 2 lần",
         "chieu": "Huyết áp đo tại phòng khám cao hơn huyết áp thường ngày nên tỷ lệ kiểm soát có thể được ước lượng "
                  "thấp hơn thực tế"},
    ],
}


def _g0_chung(hom_nay: str) -> Dict[str, Any]:
    return {"evidence_reviewed_confirmed": True,
            "registry_manual_checked": {"ictrp": hom_nay, "prospero": None}}


def _g1_chung(vi: Callable[[str], str]) -> Dict[str, Any]:
    return {"protocol_version": "1.0", "design_confirmed": True,
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
                "intervention": "Dùng thuốc ức chế bơm proton liên tục ≥ 12 tháng (phơi nhiễm)",
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
                **_finer(vi, "Đạt — hồ sơ ngoại trú điện tử lưu ≥ 5 năm, đủ người từ 60 tuổi dùng PPI",
                         "Đạt — PPI kê rất phổ biến ở người cao tuổi ngoại trú",
                         "Đạt — chưa có số liệu thuần tập tại Việt Nam (theo nền bằng chứng G0)",
                         "Đạt — dữ liệu hồi cứu đã khử định danh, không can thiệp",
                         "Đạt — hỗ trợ rà soát kê PPI kéo dài không cần thiết"),
                **_g0_chung(hom_nay),
                "novelty_justification": vi("Các phân tích gộp quốc tế (PMID 26462494) báo nguy cơ tăng vừa phải, "
                                            "dị biệt cao; chưa có thuần tập trên người cao tuổi ngoại trú Việt Nam"),
                "registry_overlap_assessment": vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                  "nghiên cứu quan sát hồi cứu tại một cơ "
                                                  "sở"),
            },
            "G1": {
                **_g1_chung(vi),
                "design": "cohort",
                "design_rationale": vi("Câu hỏi tác hại (G0 harm) với phơi nhiễm không thể phân bổ ngẫu nhiên vì lý "
                                       "do đạo đức — thuần tập hồi cứu từ hồ sơ có sẵn"),
                "objectives": ["So sánh nguy cơ gãy xương mọi vị trí trong 3 năm giữa người từ 60 tuổi dùng thuốc "
                               "ức chế bơm proton kéo dài và người không dùng"],
                "research_question": ("Ở người từ 60 tuổi điều trị ngoại trú, dùng thuốc ức chế bơm proton ≥ 12 tháng "
                                      "có làm tăng nguy cơ gãy xương trong 3 năm so với không dùng không?"),
                "primary_outcome": dict(kc_tt),
                "secondary_outcomes": ["Gãy cổ xương đùi trong 3 năm", "Thời gian đến gãy xương đầu tiên"],
                "population": ("Người từ 60 tuổi điều trị ngoại trú, có ít nhất 2 lần khám trong năm trước ngày bắt "
                                 "đầu theo dõi"),
                "inclusion_criteria": ["Tuổi ≥ 60 tại ngày bắt đầu theo dõi",
                                       "Có ≥ 2 lần khám ngoại trú trong 12 tháng trước ngày bắt đầu theo dõi"],
                "exclusion_criteria": ["Gãy xương trong 12 tháng trước ngày bắt đầu theo dõi",
                                       "Ung thư di căn xương hoặc đa u tuỷy", "Theo dõi < 6 tháng"],
                "setting": "Phòng khám ngoại trú bệnh viện",
                "study_period": "Dữ liệu 2020-01 đến 2025-12; phân tích 2027-03 đến 2027-09",
                "intervention_or_exposure": ("Dùng thuốc ức chế bơm proton liên tục ≥ 12 tháng (≥ 80% số ngày có thuốc "
                                             "theo đơn cấp)"),
                "comparator": "Không có đơn thuốc ức chế bơm proton trong giai đoạn xác định phơi nhiễm",
                "recruitment_strategy": "Trích toàn bộ hồ sơ đủ tiêu chuẩn từ cơ sở dữ liệu ngoại trú",
                "follow_up_schedule": "Theo dõi qua hồ sơ từ ngày bắt đầu đến biến cố, tử vong, mất dấu hoặc 3 năm",
                "estimand": {"population": "Người từ 60 tuổi điều trị ngoại trú đủ tiêu chuẩn",
                             "treatment_condition": "Dùng PPI kéo dài so với không dùng",
                             "variable": "Gãy xương mọi vị trí trong 3 năm",
                             "intercurrent_events_strategy": "Tử vong trước gãy xương: biến cố cạnh tranh",
                             "population_summary_measure": "Nguy cơ tương đối (RR) hiệu chỉnh"},
                # 21/11/2026 — K15: câu bối cảnh không nguồn «thường được kê kéo dài» ⇒ dẫn nguồn đã kiểm của kịch bản
                "background_problem": vi("Dùng thuốc ức chế bơm proton đi kèm nguy cơ gãy xương cao hơn "
                                         "(PMID 26462494), nên việc kê kéo dài ở người cao tuổi cần được đánh giá lại"),
                # 22/11/2026 — SANRA mục 6 (số liệu kết cục có nguồn): câu bằng chứng chép đúng số trong abstract PubMed
                # của PMID đã kiểm chứng (kho A12 giả lập), không còn câu định tính không số.
                "evidence_summary": vi("Phân tích gộp 18 nghiên cứu quan sát (PMID 26462494) báo dùng PPI làm tăng "
                                       "vừa phải nguy cơ gãy xương hông (RR 1,26; KTC 95%: 1,16–1,36) và gãy xương "
                                       "mọi vị trí (RR 1,33; KTC 95%: 1,15–1,54)"),
                "knowledge_gap": vi("Thiếu thuần tập trên người cao tuổi ngoại trú Việt Nam"),
                "benefit_risk_rationale": vi("Không can thiệp; nguy cơ duy nhất là lộ dữ liệu — khử định danh trước "
                                             "phân tích"),
                "study_schema_timeline": ("Xác định nhóm phơi nhiễm 12 tháng → ngày bắt đầu theo dõi → theo dõi 3 "
                                          "năm qua hồ sơ"),
                "intervention_dose_adherence": ("Không can thiệp; phơi nhiễm đo bằng tỷ lệ số ngày có thuốc theo đơn "
                                                "cấp (≥ 80%)"),
                "stopping_rescue_rules": "Không áp dụng — nghiên cứu hồi cứu, không can thiệp",
                "critical_to_quality": vi("Định nghĩa phơi nhiễm và biến cố thống nhất; kiểm 10% hồ sơ biến cố "
                                          "bằng phim X-quang"),
                "monitoring_plan": vi("Kiểm chất lượng trích dữ liệu sau mỗi 500 hồ sơ"),
                # 21/11/2026 (K17 STROBE 9/19): sổ sai lệch RIÊNG của đề tài — PI khai từng nguồn, biện pháp và chiều
                # ảnh hưởng dự kiến lên ước lượng (khuôn G1 A2 chỉ là danh mục chung theo thiết kế)
                "bias_controls": SAI_LECH_PI["cohort"],
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
                "registry_overlap_assessment": vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                  "nghiên cứu quan sát tại một cơ sở"),
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
                "inclusion_criteria": ["Tuổi ≥ 60", "Ca: xuất huyết tiêu hoá trên xác nhận qua nội soi",
                                       "Chứng: khám ngoại trú trong cùng tuần, không xuất huyết tiêu hoá"],
                "exclusion_criteria": ["Xơ gan có giãn tĩnh mạch thực quản", "Ung thư đường tiêu hoá trên",
                                       "Không nhớ được thuốc đã dùng và không có hồ sơ đơn thuốc"],
                "setting": "Khoa tiêu hoá và phòng khám ngoại trú bệnh viện",
                "study_period": "2027-03 đến 2028-02",
                "intervention_or_exposure": "Phơi nhiễm NSAID trong 30 ngày trước ngày chỉ điểm",
                "comparator": "Không phơi nhiễm NSAID",
                "case_definition": ("Người từ 60 tuổi nhập viện vì nôn máu hoặc đi ngoài phân đen, nội soi xác định "
                                    "tổn thương chảy máu ở thực quản, dạ dày hoặc tá tràng"),
                # 21/11/2026 (K17 STROBE 6a): PI nêu lý do chọn chứng ngay trong nguồn chọn chứng
                "control_source": ("Người khám ngoại trú cùng cơ sở trong cùng tuần với ca, ghép theo giới và nhóm "
                                   "tuổi "
                                   "5 năm, tỷ lệ 2 chứng : 1 ca, để nhóm chứng đại diện cho phân bố phơi nhiễm NSAID "
                                   "của quần thể nguồn sinh ra ca trong cùng thời gian"),
                "recruitment_strategy": "Tuyển liên tiếp ca đủ tiêu chuẩn; chọn chứng theo danh sách khám cùng tuần",
                "follow_up_schedule": "Không theo dõi — phỏng vấn một lần và trích hồ sơ",
                "estimand": {"population": "Người từ 60 tuổi tại cơ sở",
                             "treatment_condition": "Phơi nhiễm NSAID so với không phơi nhiễm",
                             "variable": "Xuất huyết tiêu hoá trên",
                             "intercurrent_events_strategy": "Không áp dụng (đo phơi nhiễm một lần)",
                             "population_summary_measure": "Tỷ số chênh (OR) hiệu chỉnh"},
                "background_problem": vi("Nguy cơ biến chứng tiêu hoá trên khác nhau theo từng thuốc chống viêm không "
                                         "steroid (PMID 23137151)"),
                # 22/11/2026 — SANRA mục 6 (số liệu kết cục có nguồn): câu bằng chứng chép đúng số trong abstract PubMed
                # của PMID đã kiểm chứng (kho A12 giả lập), không còn câu định tính không số.
                "evidence_summary": vi("Phân tích gộp 28 nghiên cứu quan sát (PMID 23137151) báo nguy cơ tương đối "
                                       "biến chứng tiêu hoá trên khác nhau theo từng NSAID, từ 1,43 (KTC 95%: "
                                       "0,65–3,15) với aceclofenac đến 18,45 (KTC 95%: 10,99–30,97) với azapropazone, "
                                       "với ibuprofen là 1,84 (KTC 95%: 1,54–2,20)"),
                "knowledge_gap": vi("Thiếu số liệu phơi nhiễm theo loại NSAID ở người cao tuổi Việt Nam"),
                "benefit_risk_rationale": vi("Không can thiệp; chỉ phỏng vấn và trích hồ sơ"),
                "study_schema_timeline": "Xác định ca → chọn 2 chứng ghép → phỏng vấn phơi nhiễm → trích hồ sơ đơn "
                                         "thuốc",
                "intervention_dose_adherence": "Không can thiệp; phơi nhiễm đo bằng phỏng vấn có hình thuốc và hồ sơ",
                "stopping_rescue_rules": "Không áp dụng — nghiên cứu quan sát",
                "critical_to_quality": vi("Người phỏng vấn không biết giả thuyết; cùng bộ câu hỏi cho ca và chứng"),
                "monitoring_plan": vi("Kiểm chất lượng phỏng vấn hằng tháng"),
                "bias_controls": SAI_LECH_PI["case_control"],
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
             "measure": "Diện tích dưới đường cong ROC của FIB-4 so với đo độ đàn hồi gan ≥ 10 kPa",
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
                "registry_overlap_assessment": vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                  "nghiên cứu chẩn đoán tại một cơ sở"),
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
                "inclusion_criteria": ["Tuổi ≥ 18", "Gan nhiễm mỡ trên siêu âm kèm ≥ 1 yếu tố chuyển hoá"],
                "exclusion_criteria": ["Uống rượu nguy hại", "Viêm gan virus B hoặc C đang hoạt động",
                                       "Không đo được độ đàn hồi gan hợp lệ"],
                "setting": "Phòng khám gan mật ngoại trú bệnh viện",
                "study_period": "2027-03 đến 2027-12",
                "intervention_or_exposure": "Chỉ số FIB-4 tính từ tuổi, AST, ALT, tiểu cầu",
                "comparator": "Đo độ đàn hồi gan thoáng qua",
                "target_condition": "Xơ hoá gan tiến triển (tương đương F3–F4)",
                "reference_standard": ("Đo độ đàn hồi gan thoáng qua ≥ 10 kPa (≥ 10 lần đo hợp lệ, IQR/trung vị "
                                       "≤ 30%), người đọc không biết kết quả FIB-4"),
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
             "measure": "Có ≥ 1 lần nhập viện ≥ 24 giờ ghi trong hồ sơ hoặc người bệnh báo, đối chiếu giấy ra viện",
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
                "registry_overlap_assessment": vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                  "nghiên cứu quan sát tại một cơ sở"),
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
                "inclusion_criteria": ["Tuổi ≥ 18", "Chẩn đoán suy tim theo tiêu chuẩn ESC, điều trị ngoại trú ≥ 3 "
                                                   "tháng"],
                "exclusion_criteria": ["Đang chờ ghép tim hoặc dùng thiết bị hỗ trợ thất",
                                       "Kỳ vọng sống < 12 tháng vì bệnh khác"],
                "setting": "Phòng khám suy tim ngoại trú bệnh viện",
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
                # 22/11/2026 — SANRA mục 6 (số liệu kết cục có nguồn): câu bằng chứng chép đúng số trong abstract PubMed
                # của PMID đã kiểm chứng (kho A12 giả lập), không còn câu định tính không số.
                "evidence_summary": vi("Tổng quan hệ thống 117 mô hình tiên lượng trong 55 bài (PMID 25194294) báo "
                                       "khả năng phân biệt còn khiêm tốn: C-statistic trung bình 0,71 với mô hình dự "
                                       "báo tử vong và 0,68 với mô hình dự báo nhập viện vì suy tim"),
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
                "registry_overlap_assessment": vi("Đã tra PROSPERO: chưa có tổng quan đăng ký trùng câu hỏi"),
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
                "exclusion_criteria": ["Thử nghiệm chỉ tuyển người suy tim lúc đầu", "Theo dõi < 24 tuần",
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
                # 21/11/2026 — K15: kịch bản không có nguồn dịch tễ ⇒ phát biểu VẤN ĐỀ, không khẳng định không nguồn
                "background_problem": vi("Cần ước lượng gộp tác dụng của thuốc ức chế SGLT2 lên nhập viện vì suy tim "
                                         "riêng ở người ĐTĐ típ 2 chưa có suy tim lúc đầu"),
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
                # 22/11/2026: tham số RIS CÓ CẤU TRÚC (thống kê viên ghim) — G3 tính lại RIS theo Wetterslev 2009 và
                # đối chiếu N đã chốt; trước đây chỉ có trong lời chốt nên checkpoint ghi lực 0,8 · p0 0,3 mặc định máy
                "p0": 0.03, "power": 0.90, "ris_giam_nguy_co_tuong_doi": 0.25, "ris_d2": 0.25,
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
                "registry_overlap_assessment": vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                  "nghiên cứu định tính tại một cơ sở"),
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
                # Hướng dẫn phỏng vấn bán cấu trúc do PI soạn (COREQ mục 14) — 17/11/2026
                "interview_guide": [
                    {"chu_de": "Mở đầu", "cau_hoi": "Anh/chị có thể kể lại lần đầu tiên bác sĩ đề nghị chuyển sang "
                                                    "tiêm insulin không?",
                     "goi_mo": ["Lúc đó anh/chị nghĩ gì, cảm thấy thế nào?", "Anh/chị đã hỏi bác sĩ những gì?"]},
                    {"chu_de": "Trải nghiệm khi bắt đầu tiêm", "cau_hoi": "Những tuần đầu tự tiêm insulin của "
                                                                         "anh/chị diễn ra như thế nào?",
                     "goi_mo": ["Việc gì dễ, việc gì khó?", "Ai giúp anh/chị học cách tiêm?",
                                "Có lúc nào anh/chị bỏ mũi tiêm không? Vì sao?"]},
                    {"chu_de": "Rào cản", "cau_hoi": "Điều gì khiến anh/chị ngần ngại hoặc trì hoãn việc tiêm "
                                                     "insulin?",
                     "goi_mo": ["Nỗi sợ kim, sợ hạ đường huyết, chi phí hay thời gian?",
                                "Gia đình, công việc ảnh hưởng thế nào?"]},
                    {"chu_de": "Hỗ trợ", "cau_hoi": "Theo anh/chị, phòng khám có thể làm gì để việc bắt đầu tiêm "
                                                    "insulin thuận lợi hơn?",
                     "goi_mo": ["Thông tin nào anh/chị mong được biết sớm hơn?"]},
                ],
                "qualitative_approach": "Phân tích chủ đề phản tư (reflexive thematic analysis, Braun & Clarke)",
                "data_collection_method": "Phỏng vấn sâu bán cấu trúc 45–60 phút, ghi âm có đồng ý, gỡ băng nguyên văn",
                "saturation_criterion": "Dừng khi 3 phỏng vấn liên tiếp không xuất hiện mã mới (tối thiểu 12 phỏng "
                                        "vấn)",
                # 22/11/2026 (COREQ 2007, SRQR 2014): PI chốt quy trình định tính khi thiết kế — khoá ở
                # hon_hop.KHOA_QUY_TRINH_DINH_TINH; khớp đội ngũ (2 người phỏng vấn và mã hoá được tập huấn), SAP §5/§10
                # (bộ mã, hai người mã hoá, bảng tính, không phần mềm QDA) và đặc tả phản tư ở G10
                **QUY_TRINH_DINH_TINH_INSULIN,
                "primary_outcome": {"name": "Trải nghiệm và rào cản khi bắt đầu tiêm insulin",
                                    "measure": "Chủ đề rút ra từ phỏng vấn sâu bán cấu trúc (phân tích chủ đề)",
                                    "timepoint": "Trong 3 tháng sau khi được chỉ định insulin", "type": "định tính"},
                "secondary_outcomes": [],
                "population": ("Người trưởng thành ĐTĐ típ 2 điều trị ngoại trú được chỉ định bắt đầu insulin"),
                "inclusion_criteria": ["Tuổi ≥ 18", "Được chỉ định bắt đầu insulin trong 3 tháng qua",
                                       "Đồng ý phỏng vấn và ghi âm"],
                "exclusion_criteria": ["Suy giảm nhận thức hoặc không giao tiếp được bằng tiếng Việt"],
                "setting": "Phòng khám nội tiết ngoại trú bệnh viện",
                "study_period": "2027-03 đến 2027-09",
                "intervention_or_exposure": "Không áp dụng — nghiên cứu định tính",
                "comparator": "Không áp dụng",
                "recruitment_strategy": ("Chọn mẫu có chủ đích đa dạng theo tuổi, giới, trình độ học vấn và việc đã "
                                         "bắt đầu hay còn trì hoãn insulin"),
                "follow_up_schedule": "Không theo dõi — một cuộc phỏng vấn; phỏng vấn lại nếu cần làm rõ",
                "estimand": {"population": "Không áp dụng (định tính)", "treatment_condition": "Không áp dụng",
                             "variable": "Không áp dụng", "intercurrent_events_strategy": "Không áp dụng",
                             "population_summary_measure": "Không áp dụng"},
                "background_problem": vi("Lý do người ĐTĐ típ 2 đã có chỉ định insulin nhưng trì hoãn bắt đầu điều trị "
                                         "chưa được mô tả tại phòng khám ngoại trú ở Việt Nam"),
                # 22/11/2026 — SANRA mục 6 (số liệu kết cục có nguồn): câu bằng chứng chép đúng số trong abstract PubMed
                # của PMID đã kiểm chứng (kho A12 giả lập), không còn câu định tính không số.
                "evidence_summary": vi("Khảo sát trực tuyến 1.400 người ĐTĐ típ 2 chưa dùng insulin ở tám nước phương "
                                       "Tây (PMID 21469914) ghi nhận tỷ lệ không sẵn lòng bắt đầu insulin («kháng "
                                       "insulin tâm lý») là 17,2%, dao động từ 5,9% (Tây Ban Nha) đến 37,3% (Ý)"),
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

#: 22/11/2026 — quy trình định tính PI chốt ở G1 cho đề tài định tính «bắt đầu insulin» (khoá
#: `hon_hop.KHOA_QUY_TRINH_DINH_TINH`); kịch bản định tính chân thực thừa hưởng nguyên khối G1 này.
QUY_TRINH_DINH_TINH_INSULIN = {
    "research_paradigm": ("Hệ hình kiến tạo – diễn giải: trải nghiệm bắt đầu insulin được hiểu qua ý nghĩa người "
                          "bệnh gán cho nó, phù hợp với mục tiêu tìm hiểu sâu từ góc nhìn của chính người bệnh"),
    "interviewer": ("Người phỏng vấn là điều dưỡng của phòng khám nội tiết (hai người, đều là nữ, trình độ cử "
                    "nhân điều dưỡng), đã được tập huấn phỏng vấn định tính trước khi thu thập; hai điều dưỡng "
                    "trực tiếp phỏng vấn, không điều trị và không quen biết người tham gia trước nghiên cứu"),
    "participant_information": ("Trước khi phỏng vấn, người phỏng vấn giới thiệu bản thân, vai trò trong nghiên "
                                "cứu và mục đích nghiên cứu khi đọc bản thông tin và phiếu đồng ý với người tham "
                                "gia"),
    "researcher_reflexivity": ("Nhóm nghiên cứu là nhân viên y tế của phòng khám, có thể mang giả định rằng hướng"
                               " dẫn kỹ thuật tiêm là rào cản chính; người phỏng vấn ghi nhật ký phản tư sau mỗi "
                               "cuộc phỏng vấn và nhóm thảo luận ảnh hưởng của vai trò nhân viên y tế lên câu trả"
                               " lời"),
    "participant_approach": ("Điều dưỡng mời trực tiếp người bệnh đủ tiêu chuẩn tại phòng khám khi tái khám; "
                             "người không đến tái khám được liên hệ qua điện thoại"),
    "non_participation": ("Số người từ chối tham gia hoặc rút lui và lý do được ghi vào sổ tuyển chọn"),
    "interview_setting": ("Phỏng vấn tại phòng riêng của phòng khám; chỉ có người phỏng vấn và người tham gia, "
                          "không có người khác có mặt"),
    "interview_guide_pilot": ("Hướng dẫn phỏng vấn bán cấu trúc gồm câu hỏi chính và câu hỏi gợi mở (Phụ lục C), "
                              "đã thử trước trên 2 người ngoài mẫu và giữ nguyên trong suốt quá trình thu thập"),
    "repeat_interviews": ("Mỗi người tham gia được phỏng vấn một lần, không phỏng vấn lại"),
    "recording_field_notes": ("Mọi cuộc phỏng vấn được ghi âm bằng máy ghi âm kỹ thuật số khi người tham gia đồng"
                              " ý; người phỏng vấn ghi chép thực địa ngay sau mỗi cuộc phỏng vấn"),
    "transcript_return": ("Không gửi lại bản gỡ băng cho người tham gia; bản tóm tắt chủ đề được kiểm tra lại với"
                          " người tham gia"),
    "coding_process": ("Bộ mã do hai người mã hoá độc lập xây dựng từ 3 bản gỡ băng đầu, cây mã trình bày ở phụ "
                       "lục; chủ đề rút ra từ dữ liệu theo hướng quy nạp, phân tích tiến hành song song với thu "
                       "thập dữ liệu; mã được quản lý bằng bảng tính có kiểm soát phiên bản, không dùng phần mềm "
                       "phân tích định tính chuyên dụng; nhật ký quyết định mã hoá được lưu; bản tóm tắt chủ đề "
                       "được kiểm tra lại với người tham gia; kết quả trình bày theo chủ đề kèm trích lời minh "
                       "hoạ đã khử định danh có mã người tham gia, cùng mô tả dày bối cảnh để người đọc đánh giá "
                       "khả năng chuyển giao"),
}
_CHAN_DOAN_KHAC = ("1, Không có hoặc xơ hoá nhẹ (F0–F1) | 2, Xơ hoá đáng kể chưa tiến triển (F2) | "
                   "3, Bệnh gan khác kèm theo")


def _ho_so_bien_6() -> Dict[str, Dict[str, list]]:
    """Bộ biến (tên, loại, nhãn, lựa chọn, kiểm, mục) + ma trận của 6 kịch bản mới."""
    so = "integer"
    return {
        "thuan_tap_phoi_nhiem": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "Trích hồ sơ"),
                ("tuoi", "text", "Tuổi tại ngày bắt đầu theo dõi (năm)", "", so, "Trích hồ sơ"),
                ("gioi", "radio", "Giới", _GIOI, "", "Trích hồ sơ"),
                ("ppi_dai_han", "radio", "Dùng PPI liên tục ≥ 12 tháng (PHƠI NHIỄM)", _CO_KHONG, "", "Phơi nhiễm"),
                # 22/11/2026: thang đo gốc của phơi nhiễm — định nghĩa thay thế SAP §9 (mỗi 1 SD)
                ("so_thang_ppi", "text", "Số tháng dùng PPI liên tục trước ngày bắt đầu theo dõi", "", so,
                 "Phơi nhiễm"),
                ("corticoid", "yesno", "Dùng corticoid toàn thân ≥ 3 tháng", "", "", "Hiệp biến"),
                ("loang_xuong", "yesno", "Chẩn đoán loãng xương trước ngày bắt đầu", "", "", "Hiệp biến"),
                ("gay_xuong_3nam", "radio", "Gãy xương mới trong 3 năm (KẾT CỤC CHÍNH)", _CO_KHONG, "", "Kết cục"),
                ("thoi_gian_theo_doi", "text", "Thời gian theo dõi (tháng)", "", so, "Kết cục"),
            ],
            "ma_tran": [
                ("1", "Gãy xương mọi vị trí trong 3 năm", "ket_cuc_chinh", "gay_xuong_3nam", "nhi_phan", "KC1",
                 "Hồ sơ + phim X-quang", "§4"),
                ("1", "Dùng thuốc ức chế bơm proton kéo dài", "phoi_nhiem", "ppi_dai_han", "nhi_phan", "PN1",
                 "Đơn thuốc cấp phát", "§4"),
                ("1", "Dùng thuốc ức chế bơm proton kéo dài", "dinh_nghia_thay_the", "so_thang_ppi", "lien_tuc", "PN2",
                 "Thời lượng dùng PPI ở thang liên tục (tháng), hiệu ứng trên mỗi 1 SD — thang đo gốc thay cho ngưỡng "
                 "≥ 12 tháng (Altman & Royston 2006, PMID 16675816)", "§9"),
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
                ("so_ngay_nsaid_30", "text", "Số ngày dùng NSAID trong 30 ngày trước ngày chỉ điểm", "", so,
                 "Phơi nhiễm"),
                ("chong_dong", "yesno", "Dùng thuốc chống đông/chống kết tập", "", "", "Phơi nhiễm"),
                ("tien_su_loet", "yesno", "Tiền sử loét dạ dày–tá tràng", "", "", "Hiệp biến"),
            ],
            "ma_tran": [
                ("1", "Xuất huyết tiêu hoá trên", "ket_cuc_chinh", "nhom_ca", "nhi_phan", "TC1",
                 "Định nghĩa ca qua nội soi", "§4"),
                ("1", "Phơi nhiễm NSAID trong 30 ngày", "dinh_nghia_thay_the", "so_ngay_nsaid_30", "lien_tuc", "PN2",
                 "Số ngày dùng NSAID trong 30 ngày ở thang liên tục, hiệu ứng trên mỗi 1 SD — thang đo gốc thay cho "
                 "«có dùng» (Altman & Royston 2006, PMID 16675816)", "§9"),
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
                ("fib4_tren_1_3", "calc", "FIB-4 ≥ 1,3 (ngưỡng loại trừ — máy tự tính)", "if([fib4] >= 1.3, 1, 0)",
                 "", "Xét nghiệm"),
                ("lsm_kpa", "text", "Độ đàn hồi gan (kPa)", "", "number", "Tiêu chuẩn tham chiếu"),
                ("xo_hoa_tien_trien", "radio", "Xơ hoá tiến triển theo đo đàn hồi ≥ 10 kPa (KẾT CỤC CHÍNH)",
                 _CO_KHONG, "", "Tiêu chuẩn tham chiếu"),
                # 22/11/2026 (STARD 2015 mục 21b): người đọc chuẩn tham chiếu ghi chẩn đoán ở người KHÔNG có bệnh đích
                # (chỉ hỏi khi xơ hoá tiến triển = Không — logic nhánh ở `meta_bien`); ≥ 3 lựa chọn để G6 trình bày
                # thành biến phân loại có nhãn ở Bảng 1 theo chuẩn tham chiếu
                ("chan_doan_khac", "radio", "Chẩn đoán theo chuẩn tham chiếu ở người không có xơ hoá tiến triển",
                 _CHAN_DOAN_KHAC, "", "Tiêu chuẩn tham chiếu"),
            ],
            "meta_bien": {"chan_doan_khac": {"nhanh": "[xo_hoa_tien_trien] = '0'"}},
            "ma_tran": [
                ("1", "Xơ hoá gan tiến triển", "ket_cuc_chinh", "xo_hoa_tien_trien", "nhi_phan", "TC1",
                 "Đo độ đàn hồi gan thoáng qua", "§4"),
                ("1", "Chỉ số FIB-4", "phoi_nhiem", "fib4", "lien_tuc", "XN4", "Xét nghiệm máu", "§4"),
                ("1", "Chỉ số FIB-4", "dinh_nghia_thay_the", "fib4_tren_1_3", "nhi_phan", "XN5",
                 "Dương tính theo ngưỡng loại trừ FIB-4 ≥ 1,3 (Shah 2009, PMID 19523535)", "§9"),
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
                ("ntprobnp_can2", "calc", "Căn bậc hai NT-proBNP (máy tự tính)", "sqrt([ntprobnp])", "",
                 "Yếu tố dự báo"),
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
                ("1", "NT-proBNP", "dinh_nghia_thay_the", "ntprobnp_can2", "lien_tuc", "YT5b",
                 "NT-proBNP biến đổi căn bậc hai (đa thức phân số bậc 0,5) cho biến lệch phải, giữ thang liên tục "
                 "(Royston, Altman & Sauerbrei 2006, PMID 16217841)", "§9"),
                ("1", "eGFR", "yeu_to", "egfr", "lien_tuc", "YT6", "Xét nghiệm", "§4"),
            ],
        },
        "tong_quan_gop": {
            "bo_bien": [
                ("study_id", "text", "Mã thử nghiệm (tác giả–năm)", "", "", "Trích xuất"),
                # 22/11/2026 (PRISMA 2020 mục 17): định danh báo cáo nguồn của từng thử nghiệm — bản ghi đăng ký thử
                # nghiệm (PRISMA 2020 coi bản ghi đăng ký là một «báo cáo» của nghiên cứu); người trích ghi để trích dẫn
                ("ma_dang_ky", "text", "Mã đăng ký thử nghiệm (bản ghi đăng ký là báo cáo nguồn)", "", "",
                 "Trích xuất"),
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
                # 16/11/2026: nối người tham gia ↔ bản gỡ băng đã khử định danh (G5-AUTO-10 đòi cột này lúc khoá)
                ("transcript_id", "text", "Mã bản gỡ băng (đã khử định danh)", "", "", "Đặc điểm người tham gia"),
                ("tuoi", "text", "Tuổi (năm)", "", so, "Đặc điểm người tham gia"),
                ("gioi", "radio", "Giới", _GIOI, "", "Đặc điểm người tham gia"),
                ("da_bat_dau_insulin", "yesno", "Đã bắt đầu tiêm insulin", "", "", "Đặc điểm người tham gia"),
                ("thoi_gian_dtd", "text", "Thời gian mắc ĐTĐ (năm)", "", so, "Đặc điểm người tham gia"),
                ("chu_de", "notes", "Chủ đề/mã rút ra từ phỏng vấn (KẾT CỤC CHÍNH)", "", "", "Phân tích"),
                # 22/11/2026 (SAP §9 confirmability): người mã hoá thứ hai gán độc lập theo cùng bộ mã ⇒ kappa
                ("chu_de_nguoi_2", "notes", "Chủ đề/mã do người mã hoá thứ hai gán độc lập (cùng bộ mã)", "", "",
                 "Phân tích"),
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
                          "--g2-approval-scope": "Toàn bộ đề cương v1.0"}
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
    """gate_params.G2 + tham số ký G2 + câu trả lời riêng của các vai theo từng kịch bản.

    16/11/2026: đề tài TIẾN CỨU tuyển người mới phải đăng ký trước người tham gia đầu tiên (Helsinki §35 — cùng quy
    tắc approve_gate/G2-AUTO-11) ⇒ PI chốt registration_required=true + ClinicalTrials.gov, mã NCT giả riêng từng đề
    tài. Trước đó hồ sơ giả lập ghim «không bắt buộc» cho 5 đề tài tiến cứu ⇒ ký G2 bị từ chối."""
    chung = {"protocol_version": "1.0", "icf_version": "1.0"}
    tien_cuu = "PROSPECTIVE_NEW_PARTICIPANTS"
    hs: Dict[str, Dict[str, Any]] = {
        "rct_nhi_phan": {
            "G2": {**chung, "public_title": "Tin nhắn nhắc uống thuốc giúp kiểm soát huyết áp",
                   "health_condition": "Tăng huyết áp nguyên phát (ICD-10 I10)", "primary_purpose": "treatment",
                   "intervention_type": "behavioral", "recruitment_mode": tien_cuu, "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov", "safety_plan_confirmed": True},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999999"),
        },
        "cat_ngang_mo_ta": {
            "G2": {**chung, "public_title": "Tỷ lệ kiểm soát huyết áp ở người điều trị ngoại trú",
                   "health_condition": "Tăng huyết áp nguyên phát (ICD-10 I10)", "recruitment_mode": tien_cuu,
                   "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov"},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999991"),
        },
        "thuan_tap_phoi_nhiem": {
            "G2": {**chung, "public_title": "PPI kéo dài và gãy xương ở người cao tuổi",
                   "health_condition": "Gãy xương do loãng xương (ICD-10 M80)",
                   "recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA", "registration_required": False,
                   "icf_waiver_requested": True},
            "ky_G2": _ky_g2("RETROSPECTIVE_SECONDARY_DATA", "NOT_REQUIRED", mien_icf=True),
        },
        "benh_chung": {
            "G2": {**chung, "public_title": "NSAID và xuất huyết tiêu hoá trên ở người cao tuổi",
                   "health_condition": "Xuất huyết tiêu hoá trên (ICD-10 K92.2)", "recruitment_mode": tien_cuu,
                   "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov"},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999992"),
        },
        "chan_doan": {
            "G2": {**chung, "public_title": "FIB-4 phát hiện xơ hoá gan tiến triển",
                   "health_condition": "Gan nhiễm mỡ liên quan chuyển hoá (ICD-10 K76.0)",
                   "recruitment_mode": tien_cuu, "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov"},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999993"),
        },
        "mo_hinh_du_bao": {
            "G2": {**chung, "public_title": "Mô hình dự báo nhập viện ở người suy tim ngoại trú",
                   "health_condition": "Suy tim (ICD-10 I50)", "recruitment_mode": tien_cuu,
                   "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov"},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999994"),
        },
        "tong_quan_gop": {
            "G2": {"protocol_version": "1.0", "public_title": "SGLT2 và nhập viện vì suy tim ở ĐTĐ típ 2",
                   "health_condition": "Đái tháo đường típ 2 (ICD-10 E11)",
                   "recruitment_mode": "NOT_APPLICABLE", "registration_required": True,
                   "registration_registry": "PROSPERO", "icf_waiver_requested": True},
            "ky_G2": {**_ky_g2("NOT_APPLICABLE", "REGISTERED", mien_icf=True,
                               quyet_dinh="EXEMPT", registry="PROSPERO", ma_dk="CRD42099999999"),
                      "--g2-first-search-date": "<+15>"},
            # 22/11/2026 (PRISMA 2020 mục 16b): nhóm sàng lọc ghi các báo cáo đọc toàn văn có vẻ đạt tiêu chí (thuốc ức
            # chế SGLT2, kết cục nhập viện vì suy tim, thử nghiệm ngẫu nhiên) nhưng bị loại — thử nghiệm THẬT, PMID và
            # tác giả đầu đã tra PubMed 22/11/2026, kiểm rút bài (check_citation_retraction.py: không rút); lý do loại
            # đọc từ phần Phương pháp của tóm tắt bài gốc (quần thể chỉ gồm người suy tim lúc vào nghiên cứu ⇒ trái tiêu
            # chí loại «chỉ tuyển người suy tim lúc đầu»), thuộc nhóm «Sai quần thể» của sổ sàng lọc
            "sang_loc_toan_van_loai": [
                {"bao_cao": "DAPA-HF", "trich_dan": "McMurray và cộng sự 2019, PMID 31535829",
                 "nhom_ly_do": "Sai quần thể",
                 "ly_do": "chỉ tuyển người suy tim phân suất tống máu ≤ 40%, có hoặc không đái tháo đường"},
                {"bao_cao": "EMPEROR-Reduced", "trich_dan": "Packer và cộng sự 2020, PMID 32865377",
                 "nhom_ly_do": "Sai quần thể", "ly_do": "chỉ tuyển người suy tim phân suất tống máu ≤ 40%"},
                {"bao_cao": "SOLOIST-WHF", "trich_dan": "Bhatt và cộng sự 2021, PMID 33200892",
                 "nhom_ly_do": "Sai quần thể",
                 "ly_do": "chỉ tuyển người đái tháo đường típ 2 vừa nhập viện vì suy tim nặng lên"},
            ],
        },
        "dinh_tinh": {
            "G2": {**chung, "public_title": "Trải nghiệm bắt đầu tiêm insulin",
                   "health_condition": "Đái tháo đường típ 2 (ICD-10 E11)", "recruitment_mode": tien_cuu,
                   "registration_required": True,
                   "registration_registry": "ClinicalTrials.gov"},
            "ky_G2": _ky_g2(tien_cuu, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999995"),
        },
    }
    for ma, them in sap_g6_tron_vong().items():
        hs.setdefault(ma, {}).update(them)
    # 16/11/2026: hồ sơ vai G6.5→G10 cho 7 thiết kế ngoài thuần tập (trước chỉ thuần tập đi hết G10)
    from gia_lap_ho_so_sau_g6 import ho_so_sau_g6  # noqa: PLC0415 — mô-đun đó nhập _TAC_GIA_G7 từ đây

    for ma, them in ho_so_sau_g6().items():
        hs.setdefault(ma, {}).update(them)
    return hs


#: 18/11/2026 (đo 24 đề tài giả lập, G3-T3): khoảng hợp lệ (min, max) cho MỌI trường số của 6 kịch bản — như từ điển
#: REDCap của đề tài thật, khoảng theo giới hạn sinh lý/đo được của phép đo (không phải khoảng tham chiếu bình thường):
#: giá trị ngoài khoảng là lỗi nhập, không phải bệnh lý nặng. Trước đây cả 6 kịch bản ghi min/max rỗng ⇒ G3-T3 báo
#: «trường số thiếu khoảng hợp lệ» và luật kiểm tra dữ liệu của G5 không có ngưỡng để bắt lỗi nhập.
KHOANG_HOP_LE: Dict[str, Tuple[str, str]] = {
    "tuoi": ("18", "110"),                  # năm — đề tài người trưởng thành
    "thoi_gian_theo_doi": ("0", "60"),      # tháng — cửa sổ theo dõi 3 năm
    "ast": ("1", "5000"), "alt": ("1", "5000"),  # U/L
    "tieu_cau": ("1", "1500"),              # G/L
    "lsm_kpa": ("1.5", "75"),               # kPa — dải đo của máy đo đàn hồi gan thoáng qua
    "lvef": ("5", "90"),                    # %
    "ntprobnp": ("0", "70000"),             # pg/mL
    "egfr": ("0", "200"),                   # mL/phút/1,73 m²
    "natri": ("100", "180"),                # mmol/L
    "hb": ("2", "25"),                      # g/dL
    "thoi_gian_dtd": ("0", "80"),           # năm
    "n_can_thiep": ("1", "100000"), "n_chung": ("1", "100000"),            # người/nhánh của một thử nghiệm
    "bien_co_can_thiep": ("0", "100000"), "bien_co_chung": ("0", "100000"),
    "theo_doi_thang": ("0", "240"),         # tháng
    "so_thang_ppi": ("0", "240"),           # tháng dùng PPI liên tục trước mốc
    "so_ngay_nsaid_30": ("0", "30"),        # ngày trong cửa sổ 30 ngày
}


def bien_so_them() -> Dict[str, Dict[str, list]]:
    """Bộ biến + ma trận của 6 kịch bản mới theo khuôn `bien_so` của canary.

    Mỗi biến: (tên, loại, nhãn, lựa chọn, kiểm, min, max) — trường số lấy (min, max) ở `KHOANG_HOP_LE`."""
    def _khoang(ten: str, kiem: str) -> Tuple[str, str]:
        return KHOANG_HOP_LE.get(ten, ("", "")) if kiem in ("integer", "number") else ("", "")

    return {ma: {"bo_bien": [(t, k, n, lc, v, *_khoang(t, v)) for t, k, n, lc, v, _muc in hs["bo_bien"]],
                 "ma_tran": list(hs["ma_tran"]),
                 # 22/11/2026: logic nhánh của phiếu (vd «chẩn đoán khác» chỉ hỏi ở người không có bệnh đích)
                 **({"meta_bien": dict(hs["meta_bien"])} if hs.get("meta_bien") else {})}
            for ma, hs in _ho_so_bien_6().items()}


# ── Quyết định SAP (G4) + đặc tả phân tích (G6) mà thống kê viên/PI của TỪNG đề tài viết ──────────────────────────
# Giả lập như đề tài thật: ô «[CẦN …]» của SAP do người đúng vai điền TỪ hồ sơ này (không lấp bằng nhãn chung), và
# đặc tả G6 bám đúng cụm chữ trong SAP đã khoá (`sap_neo`). Mục G6 `ke_thua` lấy tham số của phân tích chính rồi đè
# phần khai (giá trị None = bỏ tham số đó). Thiết kế mà engine phân tích chưa hỗ trợ (chẩn đoán, dự báo, gộp, định tính)
# không có `g6` — bộ giả lập ghi khoảng trống đó thay vì ép một phân tích sai phương pháp.
_DIEU_CHINH_1_KC = "Không điều chỉnh — một kết cục chính; kết cục phụ và nhóm nhỏ chỉ diễn giải thăm dò"
# Phân tích ĐẶC THÙ (chẩn đoán/dự báo) không gán đa trị — «ca đầy đủ» trùng phân tích chính (ghi rõ, vẫn chạy)
_CC_DAC_THU = {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Complete case vs MI",
               "mo_ta": "Ca đầy đủ — phân tích đặc thù không gán đa trị (trùng phân tích chính)", "ke_thua": True,
               "tham_so": {}}
_CC_MI = {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Complete case vs MI",
          "mo_ta": "Phân tích ca đầy đủ (không impute) đối chiếu với phân tích chính", "ke_thua": True,
          "tham_so": {"n_imputations": 0}}


def _tra_loi_sap(an_toan: str, dag: str, gia_dinh: str, nhom_nho: str, kich_ban: str) -> List[Tuple[str, str]]:
    return [(r"ket cuc an toan", an_toan), (r"dag|ly do lam sang", dag), (r"^gia dinh", gia_dinh),
            (r"nhom nho tien dinh", nhom_nho), (r"^dieu chinh", _DIEU_CHINH_1_KC), (r"kich ban cu the", kich_ban)]


def _nhom_gioi(ma_nam: int, ma_nu: int) -> List[Dict[str, Any]]:
    return [{"id": f"NC_{ten}", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Giới (nam/nữ)",
             "mo_ta": f"Nhóm nhỏ tiền định: {nhan}", "ke_thua": True, "tham_so": {"loc": f"gioi == {ma}"}}
            for ten, nhan, ma in (("nam", "nam", ma_nam), ("nu", "nữ", ma_nu))]


def _sd_khong_ap_dung(ly_do: str) -> Dict[str, Any]:
    """22/11/2026: định nghĩa thay thế nay khai ở ma trận G3 (vai trò dinh_nghia_thay_the) và SAP §9 chép cụ thể —
    mục hồ sơ chỉ còn là DẤU để bộ giả lập dựng mục đặc tả TỪ ma trận (tools/dinh_nghia_thay_the.py). `ly_do` cũ giữ
    trong mô tả để đọc lịch sử."""
    return {"id": "DN_dinh_nghia", "vai": "do_nhay", "sap_muc": "§9", "tu_ma_tran": "dinh_nghia_thay_the",
            "mo_ta": f"Định nghĩa thay thế (dựng từ ma trận G3; trước đây: {ly_do})"}


# Bản diễn giải (G6.5) do người diễn giải viết TỪ tệp kết quả thật: số trong bảng lấy từ tóm tắt phân tích (bộ giả lập
# chép, không gõ tay); lời văn dưới đây dùng {chỗ giữ} điền bằng chính các số đó. Y văn đối chiếu đã tra PubMed:
# Zhou 2016, Osteoporos Int — gộp quan sát, gãy xương mọi vị trí RR 1,33 (1,15–1,54) (PMID 26462494).
_DIEN_GIAI_THUAN_TAP: Dict[str, Any] = {
    "bang": [
        {"ket_cuc": "Gãy xương mọi vị trí trong 3 năm", "thuoc_do": "RR hiệu chỉnh (Poisson, sai số robust)",
         "lay": "pr_hieu_chinh", "gate": "G6",
         "y_nghia": "Tăng nguy cơ tương đối khoảng một phần ba; hiệu số tuyệt đối nhỏ (dòng 2)"},
        {"ket_cuc": "Gãy xương mọi vị trí trong 3 năm", "thuoc_do": "Hiệu số nguy cơ thô",
         "lay": "hieu_so_nguy_co", "gate": "G6",
         "y_nghia": "Khoảng 3 ca gãy xương thêm trên 100 người dùng PPI kéo dài trong 3 năm"},
        {"ket_cuc": "Nhóm nhỏ: nữ", "thuoc_do": "RR hiệu chỉnh", "lay": "pr_hieu_chinh", "gate": "G6_NC_nu",
         "y_nghia": "Cùng chiều phân tích chính; thăm dò"},
        {"ket_cuc": "Nhóm nhỏ: nam", "thuoc_do": "RR hiệu chỉnh", "lay": "pr_hieu_chinh", "gate": "G6_NC_nam",
         "y_nghia": "Cùng chiều, KTC rộng do ít biến cố; thăm dò"},
        {"ket_cuc": "Độ nhạy: theo dõi ≥ 12 tháng", "thuoc_do": "RR hiệu chỉnh", "lay": "pr_hieu_chinh",
         "gate": "G6_DN_theo_doi_12t", "y_nghia": "Kết quả không đổi chiều khi loại người theo dõi ngắn"},
    ],
    "muc_2": ("Phơi nhiễm PPI kéo dài đi kèm nguy cơ gãy xương cao hơn có ý nghĩa thống kê (RR hiệu chỉnh "
              "{rr}; KTC 95% {rr_duoi}–{rr_tren}). Về ý nghĩa lâm sàng, hiệu số nguy cơ tuyệt đối khoảng "
              "{rd_phan_tram} điểm phần trăm trong 3 năm ({pct1}% so với {pct0}%), tức số người cần dùng PPI kéo "
              "dài để thêm một ca gãy xương vào khoảng {nnh}. Hai trục được báo tách riêng: ý nghĩa thống kê không "
              "đồng nghĩa với độ lớn lâm sàng."),
    "muc_3": ("Ước lượng tương đồng với phân tích gộp các nghiên cứu quan sát của Zhou và cộng sự (2016): gãy xương "
              "mọi vị trí RR 1,33 (KTC 95% 1,15–1,54) ở người dùng PPI (PMID 26462494). Phân tích gộp đó có "
              "không đồng nhất đáng kể giữa các nghiên cứu, nên mức tương đồng chỉ là đối chiếu chiều và độ lớn."),
    "muc_4": ("Điểm mạnh: cỡ mẫu {n} người với {bien_co} biến cố, phân tích theo SAP đã khoá, kiểm chéo SPSS và R "
              "khớp. Hạn chế: thiết kế hồi cứu có thể còn nhiễu tồn dư (chỉ định PPI, thể trạng, té ngã), phân loại "
              "phơi nhiễm từ đơn thuốc cấp phát, kết cục dựa trên mã chẩn đoán và phim X-quang trong hồ sơ, và kết quả "
              "chỉ khái quát cho người từ 60 tuổi khám ngoại trú. Phân loại sai phơi nhiễm từ đơn cấp phát nhiều khả "
              "năng không phụ thuộc kết cục, nên có thể kéo ước lượng về phía giá trị không; ngược lại, nhiễu do chỉ "
              "định (người nhiều bệnh nền được kê PPI hơn) có thể làm ước lượng cao hơn thực."),
    "muc_5": ("Hàm ý cho thực hành giới hạn ở mức liên quan, không phải quan hệ nhân quả: rà lại chỉ định khi kê PPI "
              "kéo dài cho người cao tuổi có nguy cơ gãy xương. Hướng tiếp: nghiên cứu có đo liều và thời gian dùng "
              "PPI theo tháng, và phân tích thời gian đến gãy xương."),
}


# Tác giả (vai trò mã hoá, KHÔNG tên người thật) + khai báo ICMJE cho bản thảo G7 của đề tài tổng hợp.
_TAC_GIA_G7: Dict[str, Any] = {
    "authors": "BS. Nguyễn Văn A (chủ nhiệm) · ThS. Trần Thị B (thống kê viên) — Phòng khám ngoại trú "
               "bệnh viện",
    "author_contributions": "Tác giả 1: ý tưởng, thiết kế, thu thập dữ liệu, viết bản thảo; Tác giả 2: kế hoạch phân "
                            "tích, phân tích số liệu, duyệt bản thảo (CRediT)",
    "coi_declared": "Các tác giả không có xung đột lợi ích liên quan đề tài",
    "funding_declared": "Không có tài trợ bên ngoài",
    # 22/11/2026 (chiều, K18 CONSORT 4 / TRIPOD+AI 18e–18f): tuyên bố của tác giả nêu CÁCH truy cập mã và từ điển dữ
    # liệu (bản cũ «kịch bản phân tích kèm gói phát hành» không nói người đọc lấy bằng cách nào); phiếu G9 chép đúng
    # câu này.
    "data_sharing_statement": ("Dữ liệu cá thể không chia sẻ công khai theo cam kết bảo mật với người tham gia; mã "
                               "phân tích (kịch bản R) và từ điển dữ liệu được cung cấp theo yêu cầu gửi tác giả "
                               "liên lạc"),
    # 22/11/2026 (chiều, K18 CONSORT 3/10, STARD 29, TRIPOD+AI 18c, PRISMA 24b/24c): tác giả khai nơi truy cập đề cương
    # và thay đổi so với đề cương — khớp phiếu G9 (`results_match_locked_analysis`, `analysis_deviations_disclosed`)
    # và bảng «PHẦN 4 — THAY ĐỔI SAU KHI KHOÁ» trống của SAP các đề tài giả lập.
    "protocol_access_statement": ("Đề cương nghiên cứu và kế hoạch phân tích thống kê đã khoá được cung cấp theo yêu "
                                  "cầu gửi tác giả liên lạc"),
    "protocol_changes_statement": ("Không có thay đổi nào so với đề cương và kế hoạch phân tích đã khoá sau khi bắt "
                                   "đầu nghiên cứu"),
    "ai_use_declared": "Bản thảo được soạn với hỗ trợ của công cụ trí tuệ nhân tạo; tác giả đã đọc lại, đối chiếu số "
                       "liệu và chịu trách nhiệm toàn văn",
    "ai_manuscript_statement": ("Bản thảo được soạn với hỗ trợ của công cụ trí tuệ nhân tạo để dựng khung và chép số "
                                "liệu từ tệp kết quả; các tác giả đã đọc lại toàn "
                                "văn, đối chiếu số liệu và chịu trách nhiệm nội dung. Công cụ không phải tác giả."
                                ),
}
# Ô bản thảo G7 mà hồ sơ trả lời (mẫu so trên nhãn/nội dung ô đã bỏ dấu). Chỗ giữ {…} lấy số từ tệp kết quả G6 và lời
# văn của bản diễn giải G6.5 — không gõ tay con số.
_TRA_LOI_G7_THUAN_TAP: List[Tuple[str, str]] = [
    (r"khong dien truoc khi phan tich", "Trong {n} người ({bien_co} biến cố), dùng PPI kéo dài đi kèm nguy cơ gãy "
     "xương "
     "3 năm cao hơn: RR hiệu chỉnh {rr} (KTC 95% {rr_duoi}–{rr_tren}); hiệu số nguy cơ {rd_phan_tram} điểm phần trăm "
     "({pct1}% so với {pct0}%)."),
    (r"^conclusions?$|2.3 cau tom tat", "Ở người từ 60 tuổi khám ngoại trú, dùng PPI kéo dài liên quan với nguy cơ gãy "
     "xương cao hơn khoảng một phần ba; hiệu số tuyệt đối nhỏ. Cần rà chỉ định khi kê PPI kéo dài."),
    (r"khong chua ket cuc phu", "Kết cục phụ (gãy cổ xương đùi; thời gian đến gãy xương đầu tiên) chưa phân tích ở đợt "
     "này — báo cáo riêng theo SAP §2"),
    (r"khong chay gan da tri", "Không có dữ liệu thiếu ở 5 biến phân tích nên không gán đa trị; phân tích ca đầy đủ "
     "là phân tích chính (khớp SAP §6)"),
    (r"dien sau khi co section iii|tom tat phat hien chinh", "{muc_2}"),
    (r"giai thich sinh hoc", "Một giả thuyết được nêu trong y văn là PPI làm giảm hấp thu canxi; nghiên cứu này không "
     "đánh giá cơ chế"),
    (r"diem manh khac", "Kết quả được kiểm chéo độc lập bằng SPSS và R, khớp với engine phân tích chính"),
    (r"liet ke han che", "{muc_4}"),
    (r"tac dong voi thuc hanh|khuyen cao", "{muc_5}"),
    (r"phan tich so sanh khi co ket qua", "Đối chiếu chi tiết ở đoạn so sánh với phân tích gộp Zhou 2016 (PMID "
     "26462494); tác giả chưa đọc toàn văn bài này"),
    (r"mesh terms", "Proton Pump Inhibitors; Fractures, Bone; Aged; Cohort Studies"),
    (r"dinh dang khi da chon tap chi", "Định dạng theo hướng dẫn tác giả của tạp chí đích"),
    (r"tac gia lien lac", "BS. Nguyễn Văn A — liên hệ qua đơn vị chủ trì"),
    (r"ho ten", "BS. Nguyễn Văn A · ThS. Trần Thị B (thống kê viên)"),
    (r"don vi thu 2", "Không có"),
    (r"icmje form|xem tai lieu 8", "Các tác giả không có xung đột lợi ích liên quan đề tài"),
]


# Bản nhận xét của người phản biện ĐỘC LẬP mô phỏng (G8) — góp ý là điều đo được thật trên bản thảo đề tài này.
_PHAN_BIEN_THUAN_TAP: Dict[str, Any] = {
    "ten_bai": "PPI kéo dài và gãy xương ở người từ 60 tuổi", "thiet_ke": "Thuần tập hồi cứu",
    "ly_do": ("Thiết kế, cỡ mẫu và phân tích theo SAP đã khoá; RR hiệu chỉnh {rr} (KTC 95% {rr_duoi}–{rr_tren}) được "
              "kiểm chéo SPSS/R khớp. Còn vài điểm trình bày và hai phân tích độ nhạy chờ làm tay."),
    "gop_y_nho": [
        ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
        ("Phương pháp — phơi nhiễm", "Mô tả cách xác định dùng PPI liên tục ≥ 12 tháng từ đơn cấp phát (STROBE "
                                     "mục 7)"),
        ("Kết quả — kết cục phụ", "Hai kết cục phụ SAP §2 chưa phân tích; ghi rõ là báo cáo riêng"),
        ("Độ nhạy SAP §9", "Mục định nghĩa thay thế ở SAP §9 chưa khai cụ thể — cần SAP sửa đổi hoặc ghi lý do"),
    ],
    "cau_hoi": ["Tỷ lệ mất theo dõi trước 3 năm là bao nhiêu và có khác giữa hai nhóm không?",
                "Phơi nhiễm PPI được xác định thế nào khi người bệnh dùng ngắt quãng?"],
    "checklist": "STROBE (cohort)", "checklist_dat": "20/22 mục (91%)",
    "checklist_thieu": "mục 13 (sơ đồ dòng người tham gia), mục 16c (nguy cơ tuyệt đối theo thời gian)",
}


def sap_g6_tron_vong() -> Dict[str, Dict[str, Any]]:
    nhom_gioi = "Giới (nam/nữ) — ghi trước khi xem dữ liệu"
    gia_dinh_poisson = "Kiểm quá phân tán (Pearson χ²/df), dạng tuyến tính của tuổi, VIF < 5"
    return {
        "rct_nhi_phan": {
            "tra_loi_G4": _tra_loi_sap(
                "Biến cố bất lợi do tin nhắn (phàn nàn, lo âu) ghi theo phiếu biến cố", "tuổi và giới là yếu tố "
                "tiên lượng mạnh của kiểm soát huyết áp, hiệu chỉnh để tăng độ chính xác (không phải gây nhiễu do "
                "đã ngẫu nhiên hoá)", "Kiểm dạng tuyến tính của tuổi; VIF < 5", nhom_gioi,
                "Mô hình không hiệu chỉnh hiệp biến (so sánh thô hai nhóm)"),
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Kiểm soát huyết áp tháng 6: tin nhắn SMS so với chăm sóc thường quy",
                    "tham_so": {"outcome": "kiem_soat_t6", "group": "nhom", "covariates": ["tuoi", "gioi"],
                                "hiep_bien_phan_loai": ["gioi"]}},
                   *_nhom_gioi(1, 2), _CC_MI,
                   _sd_khong_ap_dung("kết cục và nhóm so sánh đều nhị phân — định nghĩa thay thế chưa khai cụ thể; "
                                     "thống kê viên "
                                     "sửa mục này trong SAP sửa đổi"),
                   {"id": "DN_tho", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Mô hình không hiệu chỉnh hiệp biến", "mo_ta": "So sánh thô hai nhóm",
                    "ke_thua": True, "tham_so": {"covariates": None, "hiep_bien_phan_loai": None}}],
        },
        "cat_ngang_mo_ta": {
            "tra_loi_G4": _tra_loi_sap(
                "Không áp dụng — nghiên cứu cắt ngang mô tả, không có can thiệp", "Không áp dụng — mục tiêu mô tả tỷ "
                "lệ, không ước lượng hiệu ứng nhân quả", "Tỷ lệ theo khoảng tin cậy Wilson", nhom_gioi,
                "Tỷ lệ kiểm soát theo từng giới"),
            "g6": [{"id": "MT1_ty_le", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Tỷ lệ kiểm soát huyết áp + KTC 95%", "tham_so": {"ty_le": ["kiem_soat_ha"]}},
                   *_nhom_gioi(1, 2), _CC_MI,
                   _sd_khong_ap_dung("kết cục nhị phân — định nghĩa thay thế chưa khai cụ thể"),
                   {"id": "DN_theo_gioi", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Tỷ lệ kiểm soát theo từng giới", "mo_ta": "Tỷ lệ kiểm soát theo giới",
                    "tham_so": {"ty_le": ["kiem_soat_ha"], "loc": "gioi == 2"}}],
        },
        "thuan_tap_phoi_nhiem": {
            "tra_loi_G4": _tra_loi_sap(
                "Không áp dụng — nghiên cứu quan sát hồi cứu, không có can thiệp do nghiên cứu chỉ định",
                "tuổi, corticoid toàn thân và loãng xương trước đó liên quan cả chỉ định PPI lẫn nguy cơ gãy xương "
                "(gây nhiễu trên DAG); không đưa biến trung gian", gia_dinh_poisson, nhom_gioi,
                "Loại người theo dõi dưới 12 tháng"),
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Nguy cơ gãy xương 3 năm: PPI kéo dài so với không dùng (RR hiệu chỉnh)",
                    "tham_so": {"outcome": "gay_xuong_3nam", "group": "ppi_dai_han",
                                "covariates": ["tuoi", "corticoid", "loang_xuong"]}},
                   *_nhom_gioi(1, 0), _CC_MI,
                   _sd_khong_ap_dung("phơi nhiễm và kết cục đều nhị phân — định nghĩa thay thế chưa khai cụ thể; "
                                     "định nghĩa thay thế "
                                     "cần số tháng dùng PPI (chưa có trong bộ biến)"),
                   {"id": "DN_theo_doi_12t", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Loại người theo dõi dưới 12 tháng", "mo_ta": "Chỉ người theo dõi ≥ 12 tháng",
                    "ke_thua": True, "tham_so": {"loc": "thoi_gian_theo_doi >= 12"}}],
            "dien_giai": _DIEN_GIAI_THUAN_TAP,
            "tac_gia_G7": _TAC_GIA_G7,
            "tra_loi_G7": _TRA_LOI_G7_THUAN_TAP,
            "phan_bien_G8": _PHAN_BIEN_THUAN_TAP,
            "dac_ta_G10": {
                "bias_risks": "Nhiễu do chỉ định PPI; sai lệch phân loại phơi nhiễm từ đơn cấp phát; mất theo dõi",
                "bias_controls": "Hiệu chỉnh đa biến theo DAG; định nghĩa phơi nhiễm ≥ 12 tháng liên tục; độ nhạy loại "
                                 "người theo dõi dưới 12 tháng",
                "timeline": "18 tháng: chuẩn bị và đạo đức 3 tháng; trích hồ sơ 6 tháng; phân tích 3 tháng; viết và "
                            "công bố 6 tháng",
                "team": "Chủ nhiệm đề tài (BS. Nguyễn Văn A), thống kê viên, quản lý dữ liệu, 2 người trích hồ sơ",
                "budget": "Kinh phí đơn vị cấp cho trích hồ sơ và phân tích",
                "literature_review": "Phân tích gộp quan sát (Zhou 2016, PMID 26462494) ghi nhận nguy cơ gãy xương "
                                     "tăng ở người dùng PPI; dữ liệu ở người cao tuổi ngoại trú Việt Nam còn thiếu",
                "theoretical_framework_not_applicable": ("Nghiên cứu dịch tễ học quan sát về phơi nhiễm thuốc — "
                                                         "không dựa trên khung lý thuyết hành vi; mô hình nhân quả "
                                                         "trình bày bằng DAG"),
                "literature_consensus": "Các nghiên cứu quan sát cùng chiều: dùng PPI đi kèm nguy cơ gãy xương tăng "
                                        "nhẹ–vừa; mức không đồng nhất giữa nghiên cứu còn lớn",
                "summary": ("Bối cảnh: PPI được kê kéo dài phổ biến ở người cao tuổi. Mục tiêu: so sánh nguy cơ "
                            "gãy xương 3 năm giữa người dùng PPI kéo dài và không dùng. Phương pháp: thuần tập hồi cứu "
                            "từ hồ sơ ngoại trú, hồi quy Poisson sai số robust ước lượng RR hiệu chỉnh."),
                "org_lines": ["Phòng khám ngoại trú bệnh viện"],
                "place_year": "TP. Hồ Chí Minh – 2026",
                "literature_disagreements": "Độ lớn liên quan khác nhau theo vị trí gãy và thời gian dùng; nhiễu do "
                                            "chỉ định có thể giải thích một phần",
                "pilot": "Thử phiếu trích trên 20 hồ sơ ngoài mẫu nghiên cứu; chỉnh định nghĩa biến trước khi trích "
                         "chính thức",
                "safety_plan": ("Không có can thiệp nên không phát sinh biến cố do nghiên cứu; sự cố bảo mật dữ "
                                "liệu báo cáo theo quy trình đơn vị"),
                "dissemination_plan": "Báo cáo tại đơn vị và nộp tạp chí đích",
                "limitations": "Một cơ sở ngoại trú; phơi nhiễm từ đơn cấp phát (không đo tuân thủ); không có liều "
                               "PPI theo tháng; kết cục dựa hồ sơ có phim — có thể bỏ sót gãy không đi khám",
                "vietnamese_references_not_applicable": "PubMed không có nghiên cứu trong nước cùng câu hỏi; chưa tra "
                                                        "tay tạp chí trong nước; bổ sung khi có",
                # 22/11/2026 (chiều, RECORD 6.2 + 12.1): PI khai cách kiểm định mã chọn quần thể/kết cục và mức truy
                # cập cơ sở dữ liệu — khớp định nghĩa kết cục đã chốt (mã ICD-10 + phim X-quang trong hồ sơ), phiếu thử
                # trên 20 hồ sơ và đội 2 người trích hồ sơ ở trên
                "routine_code_validation": ("Chưa có nghiên cứu kiểm định mã ICD-10 gãy xương tại cơ sở; nhóm tự "
                                            "kiểm định bằng cách đối chiếu mã chẩn đoán với phim X-quang trong hồ sơ "
                                            "cho mọi ca gãy xương và đối chiếu 20 hồ sơ của đợt thử phiếu trích"),
                "routine_database_access": ("Nhóm nghiên cứu được đơn vị cấp quyền truy xuất hồ sơ bệnh án điện tử "
                                            "ngoại trú của người đủ tiêu chuẩn giai đoạn 2020–2025; 2 người trích hồ "
                                            "sơ truy xuất, người phân tích chỉ nhận bộ dữ liệu đã khử định danh"),
            },
            "tham_so_G8": {"primary_outcome": "Gãy xương mọi vị trí trong 3 năm (gay_xuong_3nam)",
                           "ai_use_declared": True, "ai_tools": "bộ giả lập trọn vòng của hệ",
                           "ai_purpose": "soạn nháp và kiểm dây chuyền; tác giả đọc lại toàn văn",
                           "ai_declared_in_cover_letter": True, "ipd_sharing": False,
                           **{k: True for k in ("cover_letter_no_duplicate_submission", "cover_letter_coi_declared",
                                                "cover_letter_all_authors_approved",
                                                "cover_letter_corresponding_contact", "cover_letter_preprint_status")}},
        },
        "benh_chung": {
            "tra_loi_G4": _tra_loi_sap(
                "Không áp dụng — nghiên cứu bệnh–chứng, không có can thiệp", "thuốc chống đông/chống kết tập và "
                "tiền sử loét liên quan cả việc dùng NSAID lẫn xuất huyết (gây nhiễu)",
                "Kiểm dạng tuyến tính của tuổi; VIF < 5", nhom_gioi, "Loại người dùng thuốc chống đông"),
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "NSAID 30 ngày và xuất huyết tiêu hoá trên (OR hiệu chỉnh)",
                    "tham_so": {"outcome": "nhom_ca", "group": "nsaid_30ngay",
                                "covariates": ["chong_dong", "tien_su_loet"]}},
                   *_nhom_gioi(1, 0), _CC_MI,
                   _sd_khong_ap_dung("phơi nhiễm và kết cục nhị phân — định nghĩa thay thế chưa khai cụ thể"),
                   {"id": "DN_khong_chong_dong", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Loại người dùng thuốc chống đông", "mo_ta": "Chỉ người không dùng chống đông",
                    "ke_thua": True, "tham_so": {"loc": "chong_dong == 0", "covariates": ["tien_su_loet"]}}],
        },
        "chan_doan": {"tra_loi_G4": _tra_loi_sap(
            "Không áp dụng — nghiên cứu chẩn đoán, chỉ lấy máu xét nghiệm thường quy", "Không áp dụng — mục tiêu "
            "độ chính xác chẩn đoán", "Ngưỡng FIB-4 1,3 và 2,67 định trước", nhom_gioi, "Loại người ALT > 5 lần ULN"),
            # 16/11/2026: phân tích đặc thù (AUC + độ nhạy/đặc hiệu tại ngưỡng SAP) — phan_tich_thiet_ke_dac_thu.py
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Độ chính xác FIB-4 phát hiện xơ hoá tiến triển: AUC + độ nhạy/đặc hiệu tại ngưỡng 2,67",
                    "tham_so": {"loai_dac_thu": "chan_doan", "tham_chieu": "xo_hoa_tien_trien", "chi_so": "fib4",
                                "nguong": 2.67}},
                   *_nhom_gioi(1, 0), _CC_DAC_THU,
                   _sd_khong_ap_dung("độ chính xác chẩn đoán — định nghĩa thay thế chưa khai cụ thể; "
                                     "ngưỡng thứ hai 1,3 ở §5"),
                   {"id": "DN_alt", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Loại người ALT > 5 lần ULN",
                    "mo_ta": "Loại người ALT > 200 U/L (5 lần ULN 40 U/L)", "ke_thua": True,
                    "tham_so": {"loc": "alt <= 200"}}]},
        "mo_hinh_du_bao": {"tra_loi_G4": _tra_loi_sap(
            "Không áp dụng — nghiên cứu quan sát", "yếu tố dự báo chọn theo y văn trước khi xem dữ liệu, không chọn "
            "theo p", "Dạng tuyến tính kiểm bằng spline; hiệu chuẩn bằng biểu đồ", nhom_gioi,
            "Bootstrap 500 lần để hiệu chỉnh lạc quan"),
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Mô hình logistic dự báo nhập viện 12 tháng: OR, C-statistic, Brier",
                    "tham_so": {"loai_dac_thu": "du_bao", "outcome": "nhap_vien_12t",
                                "covariates": ["tuoi", "lvef", "ntprobnp", "egfr"]}},
                   *_nhom_gioi(1, 0), _CC_DAC_THU,
                   _sd_khong_ap_dung("mô hình dự báo — định nghĩa thay thế chưa khai cụ thể"),
                   {"id": "DN_bootstrap", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Bootstrap 500 lần để hiệu chỉnh lạc quan",
                    "mo_ta": "Hiệu chỉnh lạc quan bằng bootstrap",
                    "chua_tu_dong": "chạy rms::validate trong kịch bản R đã sinh (r/G6_du_bao.R, B tuỳ SAP) — "
                                    "engine Python báo C-statistic trong mẫu"}]},
        "tong_quan_gop": {"tra_loi_G4": [
            # 16/11/2026: SAP tổng quan–gộp có khung riêng (§5 tổng hợp, §6 thiếu cấp nghiên cứu, §10 metafor)
            (r"thuoc do hieu ung", "RR (nguy cơ tương đối) — kết cục nhị phân nhập viện vì suy tim"),
            (r"phan mem", "R 4.6 (metafor 4.6); kiểm chéo SPSS 31"),
            (r"packages", "metafor 4.6, meta 8.0"),
        ] + _tra_loi_sap(
            "Không áp dụng — tổng quan hệ thống", "Không áp dụng — gộp ở cấp nghiên cứu", "Mô hình hiệu ứng ngẫu "
            "nhiên DerSimonian–Laird; độ nhạy: hiệu ứng cố định", "Loại thuốc SGLT2",
            "Loại nghiên cứu nguy cơ sai lệch cao"),
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "RR gộp nhập viện vì suy tim (ngẫu nhiên DL) + RR cố định, τ², I²",
                    "tham_so": {"loai_dac_thu": "gop", "nhan_nghien_cuu": "study_id",
                                "su_kien_can_thiep": "bien_co_can_thiep", "n_can_thiep": "n_can_thiep",
                                "su_kien_chung": "bien_co_chung", "n_chung": "n_chung"}},
                   # 22/11/2026 (PRISMA 2020 mục 20c): engine gộp có phân nhóm SAP §7 — gộp DL riêng từng thuốc +
                   # Q giữa nhóm (phân nhóm một thử nghiệm vẫn vào kiểm định), kiểm chéo metafor; trước là «làm tay»
                   {"id": "NC_thuoc", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Loại thuốc SGLT2",
                    "mo_ta": "Phân nhóm theo thuốc SGLT2 (gộp riêng từng thuốc, Q giữa nhóm)", "ke_thua": True,
                    "tham_so": {"phan_nhom": "thuoc_sglt2"}},
                   {"id": "DN_co_dinh", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Hiệu ứng cố định so với hiệu ứng ngẫu nhiên",
                    "mo_ta": "RR gộp hiệu ứng cố định (nghịch đảo phương sai)",
                    # 22/11/2026: engine gộp tính cả hai mô hình trong một lượt; mo_hinh «co_dinh» báo ước lượng
                    # cố định làm kết quả mục này, kiểm chéo metafor method = "FE" (trước ghi «chờ làm tay»)
                    "ke_thua": True, "tham_so": {"mo_hinh": "co_dinh"}},
                   {"id": "DN_rob_thap", "vai": "do_nhay", "sap_muc": "§9",
                    "sap_neo": "Loại nghiên cứu nguy cơ sai lệch cao", "mo_ta": "Loại thử nghiệm RoB 2 «cao»",
                    "ke_thua": True, "tham_so": {"loc": "rob2_tong != 3"}}]},
        "dinh_tinh": {"tra_loi_G4": _tra_loi_sap(
            "Không áp dụng — nghiên cứu định tính", "Không áp dụng — phân tích chủ đề", "Bão hoà dữ liệu sau 3 cuộc "
            "phỏng vấn liên tiếp không có mã mới", "Đã/chưa bắt đầu insulin", "Mã hoá độc lập bởi 2 người") + [
            # 16/11/2026: SAP ĐỊNH TÍNH có khung riêng (§7 chọn mẫu đa dạng, §9 trustworthiness Lincoln & Guba)
            (r"chien luoc chon mau", "Chọn mẫu có chủ đích theo đã/chưa bắt đầu insulin, giới và thời gian mắc ĐTĐ"),
            # 16/11/2026: ô §5/§10 SAP định tính — trước rơi vào câu trả lời chung «R 4.6 …» (khớp chữ «phần mềm»)
            (r"so nguoi ma hoa", "2 người mã hoá độc lập theo bộ mã (codebook) trên bảng tính có kiểm soát phiên bản; "
                                 "không dùng phần mềm QDA thương mại"),
            (r"lien.nguoi.ma", "Thảo luận đồng thuận sau mỗi 5 bản gỡ băng; bất đồng do người thứ ba phân xử"),
            (r"phan mem phan tich dinh tinh", "Bảng tính LibreOffice Calc 24.8 (mã tay theo codebook) — không dùng "
                                              "phần mềm QDA"),
            (r"tieu chi da dang", "Đã/chưa bắt đầu insulin; nam/nữ; mắc ĐTĐ dưới/từ 10 năm"),
            (r"credibility", "Kiểm tra lại với người tham gia (member checking) trên tóm tắt chủ đề"),
            (r"transferability", "Mô tả dày bối cảnh phòng khám và đặc điểm người tham gia"),
            (r"dependability", "Nhật ký quyết định mã hoá (audit trail) lưu cùng bộ mã"),
            (r"confirmability", "Mã hoá độc lập bởi 2 người; bất đồng giải quyết bằng thảo luận, có người thứ ba"),
        ],
            "g6": [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                    "mo_ta": "Tần suất các chủ đề đã mã hoá (mô tả)",
                    "tham_so": {"loai_dac_thu": "dinh_tinh", "chu_de": "chu_de"}},
                   {"id": "NC_da_tiem", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Tiêu chí đa dạng",
                    "mo_ta": "Chủ đề ở người ĐÃ bắt đầu insulin", "ke_thua": True,
                    "tham_so": {"loc": "da_bat_dau_insulin == 1"}},
                   {"id": "NC_chua_tiem", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Tiêu chí đa dạng",
                    "mo_ta": "Chủ đề ở người CHƯA bắt đầu insulin", "ke_thua": True,
                    "tham_so": {"loc": "da_bat_dau_insulin == 0"}},
                   # 22/11/2026: độ tin cậy định tính = kiểm BẰNG CHỨNG THỦ TỤC (nhật ký kiểm lại với người tham
                   # gia · nhật ký quyết định mã hoá · mô tả dày bối cảnh) — tools/bang_chung_dinh_tinh.py
                   *[{"id": f"TT_{ma}", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": neo, "mo_ta": mo,
                      "tham_so": {"bang_chung": ma}} for ma, neo, mo in (
                       ("credibility", "Credibility", "Bằng chứng kiểm lại với người tham gia (member checking)"),
                       ("transferability", "Transferability", "Bằng chứng mô tả dày bối cảnh và người tham gia"),
                       ("dependability", "Dependability", "Bằng chứng nhật ký quyết định mã hoá (audit trail)"))],
                   # 22/11/2026: người mã hoá thứ hai gán mã độc lập (cột chu_de_nguoi_2) ⇒ kappa Cohen tự tính
                   {"id": "DN_hai_nguoi_ma", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Confirmability",
                    "mo_ta": "Độ thống nhất mã hoá giữa hai người (kappa Cohen)", "ke_thua": True,
                    "tham_so": {"chu_de_nguoi_2": "chu_de_nguoi_2"}}]},
    }
