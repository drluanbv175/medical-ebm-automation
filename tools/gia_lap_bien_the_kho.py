"""Kịch bản BIẾN THỂ KHÓ cho bộ giả lập trọn vòng (16/11/2026 — bác sĩ: «Làm tiếp giả lập thêm các biến thể khó, mỗi
biến thể một kịch bản»).

Mỗi biến thể KẾ THỪA một kịch bản gốc của `gia_lap_dinh_ky.KICH_BAN` (sao sâu) rồi ghi đè phần khác — không chép lặp.
Sổ RIÊNG (không nhập vào KICH_BAN) để lượt giả lập định kỳ hằng ngày không phình thêm 8 đề tài nặng; chỉ bộ giả lập
trọn vòng (`tests/test_gia_lap_bien_the_kho_20261116.py`, cần GIA_LAP_TRON_VONG=1) chạy chúng.

Khoá `bien_the` (đọc bởi `gia_lap_tron_vong.sinh_du_lieu`) mô tả cách sinh dữ liệu đặc thù: không kém hơn (p_test /
p_control), cụm (mã cụm + hiệu ứng ngẫu nhiên cụm), sống còn (thời gian–biến cố có kiểm duyệt), thiếu dữ liệu MAR.
Mọi số liệu là MÔ PHỎNG; nguồn giả định có PMID đã tra PubMed (ghi ở từng chỗ).
"""
from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List, Tuple

TIEN_CUU = "PROSPECTIVE_NEW_PARTICIPANTS"


def _sao(nguon: Dict[str, Any], **ghi_de: Any) -> Dict[str, Any]:
    kb = copy.deepcopy(nguon)
    kb.update(ghi_de)
    return kb


def _dong(ket_cuc: str, thuoc_do: str, lay: str, gate: str, y_nghia: str) -> Dict[str, str]:
    return {"ket_cuc": ket_cuc, "thuoc_do": thuoc_do, "lay": lay, "gate": gate, "y_nghia": y_nghia}


def _thay_ma_tran(ma_tran: List[tuple], bien: str, moi: tuple) -> List[tuple]:
    return [moi if d[3] == bien else d for d in ma_tran]


def kich_ban_kho() -> Dict[str, Dict[str, Any]]:  # noqa: PLR0915 — dữ liệu kịch bản
    import gia_lap_dinh_ky as GL  # noqa: PLC0415 — tránh nhập vòng (GL nhập kich_ban_them)
    from gia_lap_kich_ban_them import _ky_g2, _nhom_gioi, _sd_khong_ap_dung, _tra_loi_sap  # noqa: PLC0415

    vi: Callable[[str], str] = GL._vi
    tt = GL.TIEN_TO_DE_TAI
    rct, coh = GL.KICH_BAN["rct_nhi_phan"], GL.KICH_BAN["thuan_tap_phoi_nhiem"]
    kb: Dict[str, Dict[str, Any]] = {}

    # ══ 1. RCT KHÔNG KÉM HƠN — tái khám qua điện thoại so với trực tiếp ═════════════════════════════════════════
    # Biên 10 điểm %: mức PI chấp nhận đổi lấy tiện lợi (giả lập — cần biện minh lâm sàng thật). p_test = p_control =
    # 60%: tỷ lệ đạt đích HA nhóm chứng TEXT4BP sau 3 tháng 48% và nhóm can thiệp 70% (PMID 35342691) — chọn giữa.
    ni = _sao(rct, study=f"{tt}RCT-KHONG-KEM", id_test="rct_ni", goc="rct_nhi_phan",
              mo_ta="RCT không kém hơn (biên hiệu số tỷ lệ −10 điểm %)",
              topic=("Tái khám qua điện thoại so với tái khám trực tiếp trong kiểm soát huyết áp sau 6 tháng ở người "
                     "tăng huyết áp điều trị ngoại trú: thử nghiệm ngẫu nhiên không kém hơn"),
              query_en=('(telephone[tiab] OR telemedicine[tiab] OR "remote consultation"[tiab] OR '
                        'telemonitoring[tiab]) AND (hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure '
                        'control"[tiab] OR "blood pressure"[tiab]) AND (non-inferiority[tiab] OR noninferiority[tiab] '
                        'OR follow-up[tiab])'),
              bien_the={"khong_kem": True})
    bs = ni["bien_so"]
    bs["bo_bien"] = [("nhom", "radio", "Nhóm phân bổ", "1, Tái khám qua điện thoại | 0, Tái khám trực tiếp", "", "",
                      "") if d[0] == "nhom" else d for d in bs["bo_bien"]]
    bs["ma_tran"] = _thay_ma_tran(bs["ma_tran"], "nhom", (
        "1", "nhóm tái khám qua điện thoại", "phoi_nhiem", "nhom", "nhi_phan", "R1", "danh sách ngẫu nhiên",
        "SAP §4 nhóm so sánh"))
    g0, g1, g3 = ni["pi"]["G0"], ni["pi"]["G1"], ni["pi"]["G3"]
    g0.update({"intervention": "Tái khám định kỳ qua điện thoại (gọi video/thoại) mỗi tháng trong 6 tháng",
               "comparison": "Tái khám trực tiếp tại phòng khám mỗi tháng",
               "hypothesis_h0": "Tỷ lệ kiểm soát nhóm điện thoại thấp hơn nhóm trực tiếp từ 10 điểm % trở lên",
               "hypothesis_h1": "Tỷ lệ kiểm soát nhóm điện thoại thấp hơn nhóm trực tiếp không quá 10 điểm %",
               "expected_direction": "Tỷ lệ kiểm soát hai nhóm tương đương (không kém hơn quá biên 10 điểm %)",
               "test_type": "non_inferiority",
               "novelty_justification": vi("Thử nghiệm tái khám từ xa ở nước thu nhập cao; thiếu thử nghiệm không kém "
                                           "hơn tại phòng khám ngoại trú Việt Nam")})
    g1.update({"objectives": ["Đánh giá tái khám qua điện thoại có không kém hơn tái khám trực tiếp về tỷ lệ kiểm soát "
                              "huyết áp tại tháng 6 (biên −10 điểm %)"],
               "research_question": ("Ở người tăng huyết áp điều trị ngoại trú, tái khám qua điện thoại có không kém "
                                     "hơn tái khám trực tiếp về tỷ lệ kiểm soát huyết áp sau 6 tháng không?"),
               "design_rationale": vi("Câu hỏi điều trị dạng KHÔNG KÉM HƠN — RCT song song 2 nhánh tỷ lệ 1:1, biên "
                                      "hiệu số tỷ lệ −10 điểm %"),
               "intervention_or_exposure": "Tái khám định kỳ qua điện thoại mỗi tháng trong 6 tháng",
               "comparator": "Tái khám trực tiếp tại phòng khám mỗi tháng",
               "intervention_dose_adherence": "6 lần tái khám qua điện thoại; tuân thủ = số lần gọi thành công",
               "evidence_summary": vi("TEXT4BP (PMID 35342691) báo tỷ lệ đạt đích HA 48–70% sau 3 tháng ở nhóm can "
                                      "thiệp nhắn tin; chưa có thử nghiệm không kém hơn về tái khám qua điện thoại"),
               # 23/11/2026: bối cảnh riêng của can thiệp tái khám từ xa — không thừa hưởng câu «quên uống thuốc» của
               # kịch bản nhắn tin gốc (Giới thiệu §1 của G7 điền từ khoá này)
               "background_problem": vi("Tỷ lệ kiểm soát huyết áp ở người tăng huyết áp điều trị ngoại trú còn thấp; "
                                        "tái khám trực tiếp hằng tháng đòi người bệnh đi lại nhiều lần nên dễ bị bỏ "
                                        "lỡ lần tái khám"),
               "knowledge_gap": vi("Thiếu thử nghiệm không kém hơn về tái khám qua điện thoại tại Việt Nam"),
               # 22/11/2026 (CONSORT 2010 mở rộng NI — Piaggio 2012, PMID 23268518 — mục 2a, 4a, 5, 6a)
               "ni_rationale": vi("Chọn thiết kế không kém hơn vì tái khám qua điện thoại giảm đi lại và thời gian "
                                  "chờ cho người bệnh; câu hỏi là tỷ lệ kiểm soát có giảm quá biên chấp nhận được "
                                  "không, không phải chứng minh vượt trội"),
               "ni_constancy": vi("Hiệu ứng của theo dõi có cấu trúc so với chăm sóc thường quy (cơ sở của biên) lấy "
                                  "từ TEXT4BP (PMID 35342691): quần thể tương tự (người tăng huyết áp ngoại trú đang "
                                  "dùng thuốc), nhóm chứng ở đề tài này (tái khám trực tiếp hằng tháng) khác can thiệp "
                                  "của TEXT4BP (nhắn tin), kết cục tương tự (đạt đích huyết áp) nhưng thời điểm khác "
                                  "(6 so với 3 tháng) — giả định hằng định chỉ đạt một phần, nêu là hạn chế; giả "
                                  "thuyết không kém hơn chỉ áp cho kết cục chính, kết cục phụ phân tích thăm dò")})
    g1["estimand"] = {**g1["estimand"], "treatment_condition": "Tái khám qua điện thoại so với trực tiếp",
                      "population_summary_measure": "Hiệu số tỷ lệ (điện thoại − trực tiếp); biên không kém hơn −10 "
                                                    "điểm %"}
    g3.clear()
    g3.update({"effect_size": 0.60, "effect_type": "NI_PROPORTION", "p0": 0.60, "dropout": 0.15, "alpha": 0.025,
               "power": 0.8, "hypothesis_type": "non_inferiority", "margin": 0.10,
               "outcome_direction": "higher_better", "ni_regulatory_framework": "FDA",
               "margin_justification": vi("Cách biên cố định M1/M2: M1 ≈ 22 điểm % — hiệu ứng của hỗ trợ theo dõi "
                                          "có cấu trúc so với chăm sóc thường quy (TEXT4BP: 70% so với 48% sau 3 "
                                          "tháng); giữ ≥ 50% hiệu ứng ⇒ M2 ≤ 11 điểm %; PI chọn 10 điểm %"),
               "effect_source": ("PMID: 35342691 (TEXT4BP) — tỷ lệ đạt đích HA 48% (chứng) và 70% (can thiệp) sau 3 "
                                 "tháng; giả định p_test = p_control = 60% (giữa hai giá trị)"),
               "p0_source": "PMID: 35342691 — giả định tỷ lệ kiểm soát tái khám trực tiếp 60%",
               "margin_source": ("PMID: 35342691 (TEXT4BP) — tỷ lệ đạt đích HA 70% (can thiệp) so với 48% (chứng) "
                                 "sau 3 tháng ⇒ M1 ≈ 22 điểm %"),
               "dropout_source": vi("Giả định 15% mất theo dõi — chưa có nguồn y văn"),
               "effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
               "powered_for_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
               "recruitment_feasibility_confirmed": True,
               "software": "run_g3_auto.py (hai tỷ lệ, không kém hơn — Chow 2008)"})
    kb["rct_khong_kem"] = ni

    # ══ 2. RCT THEO CỤM — chương trình nhắc thuốc ngẫu nhiên theo phòng khám ════════════════════════════════════
    # ICC 0,05 cho kết cục kiểm soát HA giữa phòng khám: giả định (PMID 35342691 không báo ICC) — cần nguồn thật.
    cum = _sao(rct, study=f"{tt}RCT-CUM", id_test="rct_cum", goc="rct_nhi_phan",
               mo_ta="RCT theo cụm (phòng khám), ICC 0,05",
               topic=("Chương trình tin nhắn nhắc uống thuốc triển khai theo phòng khám và tỷ lệ kiểm soát huyết áp "
                      "sau 6 tháng ở người tăng huyết áp ngoại trú: thử nghiệm ngẫu nhiên theo cụm"),
               bien_the={"cum": {"cot": "ma_phong_kham", "co_cum": 8, "sd_cum": 0.35}})
    bs = cum["bien_so"]
    bs["bo_bien"] = list(bs["bo_bien"]) + [("ma_phong_kham", "text", "Mã phòng khám (cụm ngẫu nhiên hoá)", "",
                                            "integer", "1", "60")]
    bs["ma_tran"] = list(bs["ma_tran"]) + [("1", "phòng khám (cụm ngẫu nhiên hoá)", "cum", "ma_phong_kham",
                                            "lien_tuc", "K1", "danh sách phòng khám", "SAP §4 hiệu chỉnh cụm")]
    g1, g3 = cum["pi"]["G1"], cum["pi"]["G3"]
    g1.update({"design_rationale": vi("Can thiệp triển khai ở cấp PHÒNG KHÁM (nhiễm chéo nếu ngẫu nhiên cá nhân) — RCT "
                                      "theo cụm, ngẫu nhiên phòng khám tỷ lệ 1:1"),
               "objectives": ["So sánh tỷ lệ kiểm soát huyết áp tại tháng 6 giữa phòng khám triển khai chương trình "
                              "tin nhắn và phòng khám chăm sóc thường quy"],
               "research_question": ("Ở người tăng huyết áp điều trị ngoại trú, chương trình tin nhắn nhắc thuốc triển "
                                     "khai theo phòng khám có làm tăng tỷ lệ kiểm soát huyết áp sau 6 tháng không?"),
               "randomisation": vi("Ngẫu nhiên hoá theo CỤM: danh sách phòng khám ngẫu nhiên tỷ lệ 1:1, phân tầng "
                                   "theo quy mô phòng khám"),
               "recruitment_strategy": "Tuyển liên tiếp ĐÚNG 8 người bệnh đủ tiêu chuẩn mỗi phòng khám (40 phòng "
                                       "khám — cỡ chùm đều)",
               # 22/11/2026 (K18 bản thảo báo thiếu CONSORT 2025 mục 19 — ai được tiếp cận trình tự): lời khai cũ chỉ
               # nói ai phân bổ. Thử nghiệm cụm phân bổ TRƯỚC khi tuyển nên người tuyển biết nhánh — CONSORT mở rộng
               # cho thử nghiệm cụm (PMID 22951546) đòi nêu rõ điều này cùng biện pháp hạn chế sai lệch tuyển chọn.
               "allocation_concealment": ("Thống kê viên độc lập, không tham gia tuyển phòng khám hay người bệnh, sinh "
                                          "và giữ danh sách phân bổ; 40 phòng khám được ghi danh trước rồi mới phân bổ "
                                          "cùng một lượt cho cả danh sách. Vì phòng khám được phân bổ trước khi tuyển "
                                          "người bệnh, người tuyển người bệnh tại phòng khám biết nhánh của phòng khám "
                                          "mình; sai lệch tuyển chọn được hạn chế bằng cách tuyển liên tiếp đúng 8 "
                                          "người bệnh đủ tiêu chuẩn mỗi phòng khám"),
               # 22/11/2026 (CONSORT 2010 mở rộng cụm — Campbell 2012, PMID 22951546 — mục 2b, 3a, 4a, 5, 6a, 10c)
               "cluster_definition": vi("Cụm là phòng khám ngoại trú; chương trình tin nhắn (can thiệp) triển khai ở "
                                        "mức cụm (toàn phòng khám), còn mục tiêu và kết cục chính (kiểm soát huyết áp "
                                        "tháng 6) đánh giá ở mức cá nhân người bệnh"),
               "cluster_eligibility": ["Phòng khám ngoại trú thuộc chương trình của bệnh viện chủ trì, có bác sĩ "
                                       "quản lý tăng huyết áp", "Mỗi tháng có ít nhất 8 người tăng huyết áp đủ tiêu "
                                       "chuẩn đến khám", "Chưa triển khai chương trình nhắc uống thuốc bằng tin nhắn"],
               "cluster_consent": vi("Lãnh đạo từng phòng khám ký đồng ý tham gia trước khi ngẫu nhiên hoá cụm; từng "
                                     "người bệnh được giải thích và ký phiếu đồng ý sau khi phòng khám đã được phân "
                                     "bổ, trước khi thu thập số liệu")})
    # ICC: Adams 2004 (PMID 15485730) — ICC huyết áp tâm thu 0–0,052 ở 4 bộ dữ liệu chăm sóc ban đầu ⇒ 0,05 là cận
    # trên (bảo thủ). 40 phòng khám CỐ ĐỊNH (≥ 40 chùm: không cần hiệu chỉnh mẫu nhỏ — Kahan 2016) × 8 người = 320.
    g3.update({"icc": 0.05, "cluster_size": 8, "n_clusters": 40, "confirmed_n": 320, "equal_cluster_sizes": True,
               "confirmed_n_method": vi("40 phòng khám cố định của chương trình × 8 người mỗi phòng khám"),
               "icc_source": ("PMID: 15485730 (Adams 2004, J Clin Epidemiol) — ICC huyết áp tâm thu 0–0,052 trong 4 bộ "
                              "dữ liệu chăm sóc ban đầu; chọn 0,05 (cận trên, bảo thủ)")})
    cum["pi"]["G1"]["sampling_design"] = ["cum", "khac:chọn mẫu liên tiếp trong từng phòng khám"]
    kb["rct_cum"] = cum

    # ══ 3. THUẦN TẬP SỐNG CÒN — thời gian đến gãy xương (Cox) ════════════════════════════════════════════════════
    kc_sc = {"name": "Thời gian đến gãy xương đầu tiên",
             "measure": "Số tháng từ ngày bắt đầu theo dõi đến gãy xương mới có phim xác nhận; kiểm duyệt khi tử vong, "
                        "mất dấu hoặc hết 36 tháng",
             "timepoint": "Theo dõi tối đa 36 tháng", "type": "thời gian đến sự kiện"}
    sc = _sao(coh, study=f"{tt}SONG-CON", id_test="cohort_cox", goc="thuan_tap_phoi_nhiem",
              mo_ta="Thuần tập hồi cứu, thời gian đến biến cố (Cox, HR)",
              topic=("Sử dụng thuốc ức chế bơm proton kéo dài và thời gian đến gãy xương ở người từ 60 tuổi điều trị "
                     "ngoại trú: nghiên cứu thuần tập hồi cứu phân tích sống còn"),
              bien_the={"song_con": {"thoi_gian": "thoi_gian_den_gay", "bien_co": "gay_xuong", "toi_da": 36}})
    bs = sc["bien_so"]
    bs["bo_bien"] = [d for d in bs["bo_bien"] if d[0] not in ("gay_xuong_3nam", "thoi_gian_theo_doi")] + [
        ("gay_xuong", "radio", "Gãy xương mới trong thời gian theo dõi (BIẾN CỐ)", "0, Không | 1, Có", "", "", ""),
        ("thoi_gian_den_gay", "text", "Thời gian đến gãy xương hoặc kiểm duyệt (tháng)", "", "number", "0", "36")]
    bs["ma_tran"] = [d for d in bs["ma_tran"] if d[3] != "gay_xuong_3nam"] + [
        ("1", "Thời gian đến gãy xương đầu tiên (kiểm duyệt khi tử vong/mất dấu/hết 36 tháng)", "ket_cuc_chinh",
         "thoi_gian_den_gay", "thoi_gian_den_su_kien", "KC1", "Hồ sơ (ngày biến cố/kiểm duyệt)", "§4"),
        ("1", "Gãy xương mới (chỉ báo biến cố: 1 = gãy, 0 = kiểm duyệt)", "su_kien", "gay_xuong", "nhi_phan", "SK1",
         "Hồ sơ + phim X-quang", "§4")]
    g0, g1, g3 = sc["pi"]["G0"], sc["pi"]["G1"], sc["pi"]["G3"]
    g0.update({"primary_outcome": kc_sc["name"], "primary_outcome_measure": kc_sc["measure"],
               "primary_outcome_timepoint": kc_sc["timepoint"],
               "outcomes": ["Thời gian đến gãy xương đầu tiên", "Gãy cổ xương đùi trong thời gian theo dõi"],
               "hypothesis_h0": "Nguy cơ tức thời gãy xương ở nhóm dùng PPI kéo dài bằng nhóm không dùng (HR = 1)",
               "hypothesis_h1": "Nguy cơ tức thời gãy xương ở nhóm dùng PPI kéo dài khác nhóm không dùng (HR ≠ 1)"})
    g1.update({"primary_outcome": dict(kc_sc),
               "objectives": ["So sánh thời gian đến gãy xương giữa người từ 60 tuổi dùng thuốc ức chế bơm proton kéo "
                              "dài và người không dùng"],
               "research_question": ("Ở người từ 60 tuổi điều trị ngoại trú, dùng PPI ≥ 12 tháng có làm tăng nguy cơ "
                                     "tức thời gãy xương (HR) so với không dùng không?"),
               "secondary_outcomes": ["Gãy cổ xương đùi trong thời gian theo dõi"]})
    g1["estimand"] = {**g1["estimand"], "variable": "Thời gian đến gãy xương đầu tiên",
                      "population_summary_measure": "Tỷ số nguy cơ tức thời (HR) hiệu chỉnh"}
    g3.update({"effect_size": 1.33, "effect_type": "HR", "p_event": 0.10,
               "effect_source": ("PMID: 26462494 (Zhou 2016, Osteoporos Int) — PPI và gãy xương mọi vị trí RR 1,33 "
                                 "(KTC 95% 1,15–1,54); dùng làm HR giả định (biến cố hiếm)"),
               "p_event_source": vi("Giả định 10% có biến cố trong 36 tháng — chưa có số liệu tại cơ sở"),
               "powered_for_outcome": kc_sc["name"], "software": "run_g3_auto.py (log-rank — Schoenfeld)"})
    g3.pop("p0", None)
    g3.pop("p0_source", None)
    kb["thuan_tap_song_con"] = sc

    # ══ 4. THUẦN TẬP CÓ DỮ LIỆU THIẾU — gán đa trị (MI m=20) là phân tích chính ═════════════════════════════════
    mi = _sao(coh, study=f"{tt}THIEU-MI", id_test="cohort_mi", goc="thuan_tap_phoi_nhiem",
              mo_ta="Thuần tập hồi cứu, hiệp biến thiếu 15% theo MAR (gán đa trị)",
              topic=("Sử dụng thuốc ức chế bơm proton kéo dài và nguy cơ gãy xương ở người từ 60 tuổi điều trị ngoại "
                     "trú khi hồ sơ thiếu dữ liệu hiệp biến: nghiên cứu thuần tập hồi cứu có gán đa trị"),
              bien_the={"thieu": {"cot": ["corticoid", "loang_xuong"], "ty_le": 0.15, "phu_thuoc": "tuoi",
                                  "ma": "KDD", "nhan": "Không có dữ liệu — hồ sơ hồi cứu không ghi"}})
    mi["pi"]["G1"].update({"critical_to_quality": vi("Hồ sơ hồi cứu thiếu ghi chép corticoid/loãng xương ~15% — kế "
                                                     "hoạch gán đa trị định trước ở SAP §6"),
                           "monitoring_plan": vi("Báo cáo tỷ lệ thiếu từng biến sau mỗi 500 hồ sơ")})
    kb["thuan_tap_mi"] = mi

    _ho_so_bien_the(kb, rct, coh, _ky_g2, _nhom_gioi, _sd_khong_ap_dung, _tra_loi_sap)

    # Hai biến thể dưới đây GIỮ NGUYÊN mã đề tài + G0–G6 của kịch bản gốc (khác ở G7/G8) ⇒ dùng chung nền G0 của gốc.
    # ══ 5. TRÍCH DẪN ĐÃ RÚT — tác giả trích nhầm một bài đã rút; A12 phải chặn, tác giả thay nguồn rồi kiểm lại ══════
    # PMID 18453793 (Morisky 2008, J Clin Hypertens) mang loại xuất bản «Retracted Publication» trên PubMed (tra
    # 16/11/2026); nguồn thay: Morisky 1986 (PMID 3945130, Med Care) — tóm tắt: 75% người điểm tuân thủ cao ở năm 2 đạt
    # kiểm soát HA ở năm 5 so với 47% người điểm thấp (P < 0,01).
    rb = _sao(rct, id_test="rct_rut_bai", goc="rct_nhi_phan",
              mo_ta="RCT gốc — bản thảo trích một bài ĐÃ RÚT; A12 phải chặn, tác giả thay nguồn rồi kiểm lại")
    rb["ho_so_tron_vong"]["rut_bai"] = {
        "pmid_rut": "18453793", "pmid_thay": "3945130", "muc": "## I. GIỚI THIỆU",
        "cau_rut": ("Tuân thủ dùng thuốc kém là nguyên nhân thường gặp của huyết áp không kiểm soát; thang tự "
                    "báo cáo 8 câu được báo có giá trị dự báo kiểm soát huyết áp ở người tăng huyết áp ngoại trú "
                    "(PMID 18453793)."),
        "tltk_rut": ("Morisky DE, Ang A, Krousel-Wood M, Ward HJ. Predictive validity of a medication adherence "
                     "measure in an outpatient setting. J Clin Hypertens (Greenwich). 2008;10(5):348-54. "
                     "PMID:18453793"),
        "cau_thay": ("Tuân thủ dùng thuốc kém là nguyên nhân thường gặp của huyết áp không kiểm soát: ở người tăng "
                     "huyết áp tham gia chương trình giáo dục ngoại trú, 75% người có điểm tuân thủ cao ở năm thứ 2 "
                     "đạt kiểm soát huyết áp ở năm thứ 5, so với 47% người có điểm thấp (PMID 3945130)."),
        "tltk_thay": ("Morisky DE, Green LW, Levine DM. Concurrent and predictive validity of a self-reported "
                      "measure of medication adherence. Med Care. 1986;24(1):67-74. PMID:3945130")}
    kb["rct_rut_bai"] = rb

    # ══ 6. VÒNG SỬA SAU PHẢN BIỆN — vòng 1 «Sửa lớn», tác giả sửa, PI xác nhận lại bản thảo, vòng 2 cho nộp ═══════════
    vs = _sao(coh, id_test="cohort_vong_sua", goc="thuan_tap_phoi_nhiem",
              mo_ta="Thuần tập gốc — phản biện vòng 1 «Sửa lớn» (2 lỗi nghiêm trọng), tác giả sửa, vòng 2 cho nộp")
    them_han_che = (
        "Hạn chế về nhiễu chưa đo: hồ sơ ngoại trú không ghi mật độ xương, chỉ số khối cơ thể, hút thuốc và nguy "
        "cơ té ngã — các yếu tố liên quan cả chỉ định PPI lẫn gãy xương. Nhiễu tồn dư này thường làm ước lượng lệch "
        "XA giá trị 1, nên RR quan sát được có thể phóng đại mối liên quan; kết quả cần được kiểm chứng bằng thiết kế "
        "kiểm soát nhiễu mạnh hơn.")
    them_ket_luan = ("Đây là mối LIÊN QUAN trong một nghiên cứu quan sát hồi cứu, không đủ để kết luận PPI gây gãy "
                     "xương; quyết định ngừng hay duy trì PPI vẫn dựa trên chỉ định lâm sàng của từng người bệnh.")
    vs["ho_so_tron_vong"]["vong_sua_G8"] = {
        "vong_1": {
            "ly_do": ("Phương pháp và phân tích theo SAP, nhưng Bàn luận chưa nêu nhiễu chưa đo quan trọng và Kết luận "
                      "có thể đọc thành quan hệ nhân quả cho một thiết kế quan sát."),
            "loi": [("IV. BÀN LUẬN — hạn chế",
                     "Chưa thảo luận nhiễu chưa đo (mật độ xương, chỉ số khối cơ thể, hút thuốc, nguy cơ té ngã) và "
                     "hướng lệch của nó", "Thêm đoạn hạn chế về nhiễu chưa đo và hướng ảnh hưởng lên RR"),
                    ("V. KẾT LUẬN", "Kết luận chưa nói rõ đây là mối liên quan quan sát — dễ đọc thành nhân quả",
                     "Ghi rõ «liên quan», không suy nhân quả; nêu quyết định lâm sàng vẫn theo chỉ định")]},
        "sua": [("## IV. BÀN LUẬN", them_han_che), ("## V. KẾT LUẬN", them_ket_luan)],
        "vong_2": {
            "ly_do": ("Vòng 2: tác giả đã thêm đoạn nhiễu chưa đo ở Bàn luận và sửa Kết luận theo ngôn ngữ «liên "
                      "quan»; hai lỗi nghiêm trọng của vòng 1 đã được xử lý."),
            "doi_chieu": ["IV. BÀN LUẬN — hạn chế: đã thêm đoạn «Hạn chế về nhiễu chưa đo» (đã đọc lại bản sửa)",
                          "V. KẾT LUẬN: đã thêm câu nói rõ mối liên quan quan sát (đã đọc lại bản sửa)"],
            "kiem_co": [them_han_che[:60], them_ket_luan[:60]]}}
    kb["thuan_tap_vong_sua"] = vs

    # ══ 7. KINH TẾ Y TẾ — chi phí–hiệu quả đi kèm RCT gốc (CHEERS 2022, PMID 35017145) ═════════════════════════════
    # Chi phí MÔ PHỎNG (VND): nền 1,8 triệu ± 0,4 triệu/6 tháng; chương trình tin nhắn +600 nghìn/người; người đạt kiểm
    # soát tiết kiệm 150 nghìn (ít khám ngoài kế hoạch). Ngưỡng WTP do chủ nhiệm ấn định cho đơn vị tự nhiên.
    kt = _sao(rct, id_test="rct_kinh_te", goc="rct_nhi_phan",
              mo_ta="RCT gốc + đánh giá chi phí–hiệu quả đi kèm thử nghiệm (ICER, bootstrap, CEAC; CHEERS 2022)",
              bien_the={"kinh_te": {"cot": "chi_phi_6t", "nen": 1_800_000, "sd": 400_000, "chuong_trinh": 600_000,
                                    "tiet_kiem": 150_000}})
    bs = kt["bien_so"]
    bs["bo_bien"] = list(bs["bo_bien"]) + [("chi_phi_6t", "text", "Tổng chi phí y tế trực tiếp 6 tháng (VND, góc nhìn "
                                            "cơ sở y tế)", "", "integer", "0", "20000000")]
    bs["ma_tran"] = list(bs["ma_tran"]) + [
        ("2", "chi phí y tế trực tiếp 6 tháng (góc nhìn cơ sở y tế)", "ket_cuc_phu", "chi_phi_6t", "lien_tuc", "KT1",
         "phiếu chi phí + biểu giá dịch vụ", "SAP §16 chi phí"),
        ("2", "kiểm soát huyết áp tháng 6 (đơn vị hiệu quả)", "ket_cuc_phu", "kiem_soat_t6", "nhi_phan", "C1",
         "đo huyết áp chuẩn hoá", "SAP §16 hiệu quả"),
        ("2", "nhóm nhận tin nhắn SMS", "phoi_nhiem", "nhom", "nhi_phan", "R1", "danh sách ngẫu nhiên",
         "SAP §16 nhánh")]
    g1 = kt["pi"]["G1"]
    g1["objectives"] = list(g1["objectives"]) + [
        "Đánh giá chi phí–hiệu quả của chương trình tin nhắn so với chăm sóc thường quy trong 6 tháng (ICER: chi phí "
        "cho thêm một người đạt kiểm soát huyết áp, góc nhìn cơ sở y tế)"]
    g1["aim"] = ("Đánh giá hiệu quả và chi phí–hiệu quả của chương trình tin nhắn nhắc uống thuốc so với chăm sóc "
                 "thường quy ở người tăng huyết áp điều trị ngoại trú")
    g1["secondary_outcomes"] = list(g1.get("secondary_outcomes") or []) + [
        "Chi phí y tế trực tiếp 6 tháng (VND) và tỷ số chi phí–hiệu quả gia tăng (ICER)"]
    g1["economic_evaluation"] = {
        "loai_phan_tich": "Phân tích chi phí–hiệu quả (CEA) đi kèm thử nghiệm, trên dữ liệu cá thể",
        "perspective": "Cơ sở y tế (chi phí trực tiếp y tế do phòng khám chi trả)",
        "comparator": "Chăm sóc thường quy — nhánh chứng của thử nghiệm",
        "time_horizon": "6 tháng, bằng thời gian theo dõi (không ngoại suy)",
        "discounting": "Không chiết khấu — khung thời gian ≤ 1 năm",
        "currency_year": "VND, giá năm 2026",
        "cost_items": vi("Khám, thuốc hạ áp, xét nghiệm theo dõi (biểu giá dịch vụ của bệnh viện) và chi phí vận hành "
                         "chương trình tin nhắn (hợp đồng nhà mạng, nhân lực)"),
        "effect_measure": "Thêm một người đạt kiểm soát huyết áp tại tháng 6 (đơn vị tự nhiên)",
        # 22/11/2026 (CHEERS 2022 mục 13, 18 — chuẩn đòi nêu rõ cả khi không làm; mục 19 ở dưới): lời khai của chủ nhiệm
        "outcome_valuation": ("Không định giá theo thoả dụng: hiệu quả tính bằng số người đạt kiểm soát huyết áp (đơn "
                              "vị tự nhiên), không quy đổi QALY nên không dùng bộ trọng số thoả dụng"),
        "wtp": "5.000.000 VND cho thêm một người đạt kiểm soát huyết áp",
        "wtp_source": vi("Chủ nhiệm ấn định cho đơn vị tự nhiên — chưa có ngưỡng chuẩn quốc gia; báo CEAC 0–3 × "
                         "ngưỡng để người đọc tự đặt ngưỡng"),
        "heterogeneity": ("Không ước lượng chi phí–hiệu quả theo phân nhóm: cỡ mẫu tính cho kết cục lâm sàng chính, "
                          "không đủ lực cho phân nhóm; phân nhóm nam/nữ định trước chỉ áp cho kết cục lâm sàng"),
        "patient_involvement": ("Không có người bệnh tham gia thiết kế phân tích kinh tế (ghi rõ theo CHEERS 2022 mục "
                                "21)"),
        # 22/11/2026 (CHEERS 2022 mục 19)
        "distributional_effects": vi("Không phân tích tác động phân bố theo nhóm thu nhập hay vùng vì phiếu thu thập "
                                     "không ghi thu nhập và mẫu từ một cơ sở; nêu là hạn chế khi diễn giải"),
        "bien_nhom": "nhom", "bien_chi_phi": "chi_phi_6t", "bien_hieu_qua": "kiem_soat_t6"}
    hs = kt["ho_so_tron_vong"]
    hs["g6"] = list(hs["g6"]) + [{
        "id": "KT_chi_phi_hieu_qua", "vai": "phu", "sap_muc": "§16", "sap_neo": "ICER = ΔC/ΔE",
        "mo_ta": "Chi phí–hiệu quả 6 tháng: ICER, NMB, bootstrap 2000 lần, CEAC (CHEERS 2022)",
        "tham_so": {"loai_dac_thu": "kinh_te", "nhom": "nhom", "chi_phi": "chi_phi_6t", "hieu_qua": "kiem_soat_t6",
                    "nguong_wtp": 5000000}}]
    dg = copy.deepcopy(hs["dien_giai"])
    dg["bang"] = list(dg["bang"]) + [
        _dong("Chi phí y tế trực tiếp 6 tháng", "Chi phí gia tăng ΔC (VND, KTC 95% bootstrap)", "delta_c",
              "G6_KT_chi_phi_hieu_qua", "ICER {icer} VND cho thêm một người đạt kiểm soát ({goc_phan_tu})"),
        _dong("Chi phí–hiệu quả tại ngưỡng WTP {wtp} VND", "Lợi ích ròng gia tăng NMB (VND, KTC 95% bootstrap)", "nmb",
              "G6_KT_chi_phi_hieu_qua", "{ceac_wtp}% lần lặp bootstrap cho thấy chi phí–hiệu quả tại ngưỡng")]
    dg["muc_2"] = dg["muc_2"] + (
        " Về kinh tế (SAP §16), chương trình tin nhắn tốn thêm {delta_c} VND mỗi người trong 6 tháng "
        "(KTC 95% bootstrap {delta_c_duoi} đến {delta_c_tren}); ICER {icer} VND cho thêm một người đạt "
        "kiểm soát huyết áp. Tại ngưỡng {wtp} VND do chủ nhiệm ấn định, NMB là {nmb} VND (KTC 95% "
        "{nmb_duoi} đến {nmb_tren}) và {ceac_wtp}% lần lặp bootstrap cho thấy chi phí–hiệu quả; ngưỡng "
        "không phải chuẩn quốc gia nên đường CEAC được báo đủ 0–3 lần ngưỡng.")
    dg["muc_4"] = dg["muc_4"] + (
        " Hạn chế của phần kinh tế: góc nhìn cơ sở y tế bỏ qua chi phí của người bệnh (đi lại, mất ngày công); khung 6 "
        "tháng không gồm biến cố tim mạch dài hạn mà kiểm soát huyết áp phòng được.")
    hs["dien_giai"] = dg
    hs["phan_bien_G8"] = {**hs["phan_bien_G8"], "checklist": "CONSORT 2025 + CHEERS 2022 (PMID 35017145)"}
    # 23/11/2026: ô §3 «ai thực hiện can thiệp» — cùng chương trình tin nhắn, kèm ghi nguồn lực làm dữ liệu chi phí
    hs["tra_loi_G7"] = [(r"ai thuc hien can thiep", (
        "Điều dưỡng phụ trách chương trình tin nhắn (không tham gia đo huyết áp) cài lịch gửi tự động và kiểm nhật ký "
        "gửi tin hằng tuần; tuân thủ đo bằng tỷ lệ tin nhắn gửi thành công; giờ công điều dưỡng và cước tin nhắn của "
        "chương trình được ghi hằng tháng làm dữ liệu chi phí")), *hs["tra_loi_G7"]]
    kb["rct_kinh_te"] = kt

    # ══ 8. HỖN HỢP GIẢI THÍCH TUẦN TỰ — RCT gốc + phỏng vấn sâu giải thích kết quả (GRAMMS, PMID 18416914) ═════════
    # Đề tài giữ mã thiết kế «rct» (cấu phần định lượng); cấu phần định tính + tích hợp khai ở G1.mixed_methods
    # (tools/hon_hop.py). Phỏng vấn sau khi khoá phân tích định lượng, chọn có chủ đích theo kết quả (đạt/không đạt
    # kiểm soát) — đúng mô hình giải thích tuần tự của Creswell & Plano Clark.
    # Giữ mã đề tài của RCT gốc ⇒ dùng chung nền G0 đã lưu (giả lập ngoại tuyến), như «kinh tế», «trích dẫn đã rút».
    hh = _sao(rct, id_test="rct_hon_hop", goc="rct_nhi_phan",
              mo_ta="RCT gốc + cấu phần định tính giải thích tuần tự (thiết kế hỗn hợp; GRAMMS + COREQ)")
    g1 = hh["pi"]["G1"]
    g1["objectives"] = list(g1["objectives"]) + [
        "Tìm hiểu trải nghiệm của người bệnh với chương trình tin nhắn và lý do đạt hoặc không đạt kiểm soát huyết áp "
        "sau 6 tháng, nhằm giải thích kết quả của thử nghiệm"]
    g1["aim"] = ("Đánh giá hiệu quả của chương trình tin nhắn nhắc uống thuốc lên kiểm soát huyết áp và tìm hiểu trải "
                 "nghiệm của người bệnh để giải thích kết quả, ở người tăng huyết áp điều trị ngoại trú")
    # 22/11/2026 (SRQR 2014 mục S3): khoảng trống của đề tài hỗn hợp gồm cả phần cấu phần định tính trả lời
    g1["knowledge_gap"] = ("Thiếu RCT tại Việt Nam với kết cục tỷ lệ kiểm soát huyết áp sau 6 tháng, và chưa có nghiên "
                           "cứu tìm hiểu vì sao một số người vẫn không đạt kiểm soát dù nhận tin nhắn")
    g1["mixed_methods"] = {
        "thiet_ke": "giai_thich_tuan_tu",
        "ly_do": vi("Thử nghiệm trả lời chương trình tin nhắn có cải thiện kiểm soát huyết áp hay không, nhưng không "
                    "cho biết vì sao một số người vẫn không đạt kiểm soát dù nhận tin nhắn; phỏng vấn sâu sau thử "
                    "nghiệm giúp giải thích kết quả và gợi ý cách điều chỉnh chương trình trước khi triển khai rộng"),
        "uu_tien": "dinh_luong",
        "cau_phan_dinh_tinh": {
            "muc_tieu": [len(g1["objectives"])],  # mục tiêu vừa thêm ở trên — cấu phần định tính trả lời
            "central_phenomenon": vi("Trải nghiệm nhận tin nhắn nhắc uống thuốc và các yếu tố giúp hoặc cản trở việc "
                                     "uống thuốc đều đặn"),
            "qualitative_approach": "Phân tích chủ đề (thematic analysis) theo Braun và Clarke",
            "chon_mau": vi("Chọn mẫu có chủ đích trong nhóm can thiệp theo kết quả tháng 6 (đạt và không đạt kiểm "
                           "soát huyết áp), đa dạng về giới và nhóm tuổi"),
            "co_mau_du_kien": "Khoảng 16–20 người (8–10 người mỗi nhóm kết quả), dừng khi đạt bão hoà",
            # 22/11/2026 (SRQR 2014 mục S10 — tính lặp của quy trình thu thập): thu thập và phân tích xen kẽ tới bão hoà
            "data_collection_method": vi("Phỏng vấn sâu bán cấu trúc 30–45 phút tại phòng khám hoặc qua điện thoại, "
                                         "ghi âm khi người tham gia đồng ý, gỡ băng nguyên văn; thu thập lặp lại song "
                                         "song với phân tích cho tới khi đạt bão hoà"),
            "saturation_criterion": "Ba cuộc phỏng vấn liên tiếp không xuất hiện mã mới",
            # 22/11/2026 (COREQ 2007, SRQR 2014): quy trình định tính PI chốt khi thiết kế — cùng khoá với đề tài định
            # tính (hon_hop.KHOA_QUY_TRINH_DINH_TINH); khớp «hai nghiên cứu viên mã hoá độc lập» ở phan_tich
            "research_paradigm": ("Hệ hình thực dụng của nghiên cứu hỗn hợp: cấu phần định tính nhằm giải thích "
                                  "kết quả định lượng từ góc nhìn người bệnh, phù hợp với mô hình giải thích tuần"
                                  " tự"),
            "interviewer": ("Người phỏng vấn là cán bộ nghiên cứu định tính của nhóm (một người, nữ, thạc sĩ y tế"
                            " công cộng), đã được tập huấn phỏng vấn sâu; nghiên cứu viên này trực tiếp phỏng "
                            "vấn, không điều trị và không quen biết người tham gia trước nghiên cứu"),
            "participant_information": ("Khi liên hệ và trước khi phỏng vấn, người phỏng vấn giới thiệu bản thân,"
                                        " vai trò trong nhóm nghiên cứu và mục đích của cấu phần định tính"),
            "researcher_reflexivity": ("Người phỏng vấn biết kết quả định lượng của thử nghiệm nên có thể thiên "
                                       "về giải thích có lợi cho chương trình tin nhắn; nhóm ghi nhật ký phản tư "
                                       "sau mỗi cuộc phỏng vấn và mời một thành viên không tham gia thiết kế "
                                       "chương trình rà soát bộ mã"),
            "participant_approach": ("Cán bộ nghiên cứu liên hệ qua điện thoại người được chọn trong nhóm can "
                                     "thiệp, giới thiệu mục đích và hẹn lịch phỏng vấn"),
            "non_participation": ("Số người từ chối tham gia hoặc rút lui và lý do được ghi vào sổ tuyển chọn của"
                                  " cấu phần định tính"),
            "interview_setting": ("Phỏng vấn tại phòng riêng của phòng khám hoặc qua điện thoại khi người tham "
                                  "gia ở xa; chỉ có người phỏng vấn và người tham gia, không có người khác có mặt"),
            "interview_guide_pilot": ("Hướng dẫn phỏng vấn bán cấu trúc (Phụ lục C) đã thử trước trên 2 người "
                                      "bệnh ngoài mẫu và giữ nguyên trong suốt quá trình thu thập"),
            "repeat_interviews": ("Mỗi người tham gia được phỏng vấn một lần, không phỏng vấn lại"),
            "recording_field_notes": ("Mọi cuộc phỏng vấn được ghi âm bằng máy ghi âm kỹ thuật số khi người tham "
                                      "gia đồng ý; người phỏng vấn ghi chép thực địa ngay sau mỗi cuộc phỏng vấn"),
            "transcript_return": ("Không gửi lại bản gỡ băng cho người tham gia; bản tóm tắt chủ đề được kiểm tra"
                                  " lại với người tham gia"),
            "coding_process": ("Bộ mã do hai nghiên cứu viên mã hoá độc lập xây dựng từ 3 bản gỡ băng đầu, cây mã"
                               " trình bày ở phụ lục; chủ đề rút ra từ dữ liệu theo hướng quy nạp, phân tích tiến"
                               " hành song song với thu thập dữ liệu; mã được quản lý bằng bảng tính có kiểm soát"
                               " phiên bản, không dùng phần mềm phân tích định tính chuyên dụng; nhật ký quyết "
                               "định mã hoá được lưu; kết quả trình bày theo chủ đề kèm trích lời minh hoạ đã khử"
                               " định danh có mã người tham gia, cùng mô tả dày bối cảnh để người đọc đánh giá "
                               "khả năng chuyển giao"),
            "phan_tich": vi("Hai nghiên cứu viên mã hoá độc lập theo bộ mã xây dựng từ 3 bản gỡ băng đầu, thảo luận "
                            "đồng thuận; người thứ ba phân xử khi bất đồng"),
            "interview_guide": [
                {"chu_de": "Mở đầu", "cau_hoi": "Anh/chị có thể kể lại những tháng nhận tin nhắn nhắc uống thuốc?",
                 "goi_mo": ["Tin nhắn thường đến vào lúc nào trong ngày?",
                            "Anh/chị thường làm gì khi nhận được tin nhắn?"]},
                {"chu_de": "Việc uống thuốc hằng ngày", "cau_hoi": vi("Điều gì giúp anh/chị uống thuốc huyết áp đều "
                                                                     "đặn, và điều gì khiến anh/chị đôi khi quên "
                                                                     "hoặc bỏ thuốc?"),
                 "goi_mo": ["Anh/chị có thể cho một ví dụ cụ thể không?",
                            "Gia đình có vai trò gì trong việc này?"]},
                {"chu_de": "Đánh giá chương trình", "cau_hoi": vi("Theo anh/chị, tin nhắn có ích ở điểm nào và "
                                                                  "chưa phù hợp ở điểm nào?"),
                 "goi_mo": ["Nội dung, giờ gửi hoặc số lần gửi nên thay đổi thế nào?"]},
                {"chu_de": "Kết thúc", "cau_hoi": "Còn điều gì anh/chị muốn chia sẻ thêm mà chúng tôi chưa hỏi?",
                 "goi_mo": []}]},
        "tich_hop": {
            "thoi_diem": vi("Sau khi khoá phân tích định lượng: kết quả tháng 6 dùng để chọn người phỏng vấn, và hai "
                            "bộ kết quả được hợp nhất ở giai đoạn diễn giải"),
            "cach": vi("Kết nối theo chọn mẫu (kết quả định lượng xác định nhóm được mời phỏng vấn) và hợp nhất bằng "
                       "bảng tích hợp, đối chiếu từng kết quả định lượng với chủ đề định tính tương ứng"),
            "nguoi": vi("Chủ nhiệm đề tài cùng nghiên cứu viên định tính; thống kê viên tham gia đối chiếu kết quả "
                        "định lượng"),
            # 22/11/2026 (GRAMMS 2008 mục 5, 6): hạn chế phát sinh do kết hợp và hiểu biết dự kiến thu được nhờ kết hợp
            "han_che": ("Hạn chế do kết hợp hai cấu phần: người được phỏng vấn đã biết mình ở nhóm can thiệp và "
                        "kết quả huyết áp tháng 6 của mình, nên lời kể của cấu phần định tính có thể bị kết quả "
                        "định lượng định hướng; ngược lại cấu phần định lượng không đo được lý do không đạt kiểm "
                        "soát"),
            "hieu_biet_du_kien": ("Kết hợp hai cấu phần giúp giải thích vì sao một số người nhận tin nhắn vẫn "
                                  "không đạt kiểm soát huyết áp và gợi ý cách điều chỉnh nội dung, giờ gửi tin "
                                  "nhắn trước khi triển khai rộng"),
            "chu_de": [
                {"chu_de": "Hiệu quả của chương trình tin nhắn",
                 "dinh_luong": "Tỷ lệ kiểm soát huyết áp tháng 6 theo nhóm (kết cục chính)",
                 "dinh_tinh": "Trải nghiệm nhận tin nhắn và cách người bệnh phản hồi"},
                {"chu_de": "Người không đạt kiểm soát dù nhận tin nhắn",
                 "dinh_luong": "Tỷ lệ không đạt kiểm soát trong nhóm can thiệp",
                 "dinh_tinh": "Rào cản uống thuốc đều đặn"},
                {"chu_de": "Khả năng áp dụng rộng",
                 "dinh_luong": "Điểm tuân thủ thuốc tháng 6",
                 "dinh_tinh": "Đề xuất điều chỉnh nội dung và giờ gửi tin nhắn"}]}}
    hs = hh["ho_so_tron_vong"]
    dg = copy.deepcopy(hs["dien_giai"])
    dg["muc_4"] = dg["muc_4"] + (
        " Cấu phần định tính giải thích (phỏng vấn sâu người nhóm can thiệp đạt và không đạt kiểm soát) được thực "
        "hiện sau khi khoá phân tích định lượng theo SAP §17; kết quả tích hợp trình bày bằng bảng tích hợp và báo "
        "cáo theo GRAMMS. Khả năng chuyển giao của kết quả định tính giới hạn ở người tăng huyết áp điều trị ngoại "
        "trú có bối cảnh tương tự, nhờ mô tả dày bối cảnh phòng khám và đặc điểm người được phỏng vấn.")
    # GRAMMS 2008 mục 5, 6 ở bàn luận: bộ sinh G7 viết từ tich_hop.han_che (G1) và chủ đề định tính theo nhóm kết quả
    # (khoi_dinh_tinh_g7) — không chép lại ở diễn giải để bản thảo khỏi nói hai lần
    hs["dien_giai"] = dg
    hs["phan_bien_G8"] = {**hs["phan_bien_G8"],
                          "checklist": "CONSORT 2025 + GRAMMS (PMID 18416914) + COREQ (PMID 17872937)"}
    # 23/11/2026: ô §3 «ai thực hiện can thiệp» — người gửi tin tách khỏi người đo huyết áp và người phỏng vấn sâu
    hs["tra_loi_G7"] = [(r"ai thuc hien can thiep", (
        "Điều dưỡng phụ trách chương trình tin nhắn (không tham gia đo huyết áp, không phỏng vấn sâu ở cấu phần định "
        "tính) cài lịch gửi tự động và kiểm nhật ký gửi tin hằng tuần; tuân thủ đo bằng tỷ lệ tin nhắn gửi thành "
        "công")), *hs["tra_loi_G7"]]
    kb["rct_hon_hop"] = hh
    kb["benh_chung_ghep_cap"] = _ghep_cap(GL.KICH_BAN["benh_chung"], _ky_g2, _tra_loi_sap)
    kb["benh_chung_ghep_cap_thieu"] = _ghep_cap_thieu(kb["benh_chung_ghep_cap"])
    kb["benh_chung_ghep_cap_hiem"] = _ghep_cap_hiem(kb["benh_chung_ghep_cap"])
    kb["cat_ngang_pls_sem"] = _pls_sem(GL.KICH_BAN["cat_ngang_mo_ta"], vi, tt, _ky_g2, _tra_loi_sap, _nhom_gioi)
    return kb


def _ghep_cap(bc: Dict[str, Any], _ky_g2: Callable, _tra_loi_sap: Callable) -> Dict[str, Any]:
    """BỆNH–CHỨNG GHÉP CẶP CÁ THỂ 1 ca : 2 chứng theo giới và tuổi ± 2 năm (23/11/2026 — điều phối giao: «logistic có
    điều kiện cho bệnh–chứng ghép cặp cá thể … dữ liệu giả lập cần một biến thể có mã bộ ghép thật»).

    Kế thừa kịch bản bệnh–chứng ghép tần suất; khác ở chỗ PI chốt matching_type individual ⇒ SAP §4 hồi quy logistic CÓ
    ĐIỀU KIỆN theo bộ ghép ⇒ G6 chạy statsmodels ConditionalLogit theo `ma_bo_ghep`, R survival::clogit, SPSS COXREG
    phân tầng. Giới, tuổi là BIẾN GHÉP (vai trò bien_ghep — hằng/gần hằng trong bộ) ⇒ không vào mô hình có điều kiện,
    nhưng vào mô hình gán đa trị. 23/11/2026 (chiều): cỡ mẫu theo Dupont 1988 (M = 2, φ), biến cố hiếm theo Firth có
    điều kiện (firth_dk)."""
    # GIỮ mã đề tài + chủ đề của kịch bản gốc (G0 trùng hệt) ⇒ đọc thẳng nền G0 đã lưu của gốc (`nen_g0_tu`, như kịch
    # bản chân thực); khác ở thiết kế chọn chứng (G1) trở đi
    gc = _sao(bc, id_test="case_control_ghep_cap", goc="benh_chung", nen_g0_tu="benh_chung",
              mo_ta="Bệnh–chứng ghép cặp cá thể 1:2 theo giới và tuổi (logistic có điều kiện theo bộ ghép)",
              bien_the={"ghep_cap": {"cot": "ma_bo_ghep", "so_chung": 2, "dung": ["gioi"], "lech": {"tuoi": 2}}})
    bs = gc["bien_so"]
    bs["bo_bien"] = list(bs["bo_bien"]) + [("ma_bo_ghep", "text", "Mã bộ ghép (một ca và 2 chứng ghép cặp với ca đó)",
                                            "", "integer", "1", "9999")]
    bs["ma_tran"] = [d for d in bs["ma_tran"] if d[3] not in ("tuoi", "gioi")] + [
        ("1", "Tuổi (biến ghép cặp cá thể, chênh ≤ 2 năm trong bộ)", "bien_ghep", "tuoi", "lien_tuc", "HB2",
         "Phỏng vấn + hồ sơ", "§6"),
        ("1", "Giới (biến ghép cặp cá thể, trùng trong bộ)", "bien_ghep", "gioi", "nhi_phan", "HB3", "Phỏng vấn",
         "§6"),
        ("1", "Bộ ghép (một ca cùng 2 chứng ghép cặp theo giới và tuổi ± 2 năm)", "bo_ghep", "ma_bo_ghep", "lien_tuc",
         "BG1", "Sổ tuyển chọn chứng", "§4")]
    g1 = gc["pi"]["G1"]
    g1.update({
        # STROBE 6b (K17): nêu tiêu chí ghép và số chứng cho mỗi ca
        "control_source": ("Người khám ngoại trú cùng cơ sở trong cùng tuần với ca, ghép cặp cá thể: mỗi ca được ghép "
                           "cặp theo đúng giới và tuổi chênh không quá 2 năm với 2 chứng (2 chứng cho mỗi ca; mỗi ca "
                           "cùng 2 chứng của mình là một bộ ghép có mã bộ ghép riêng), để nhóm chứng đại diện cho phân "
                           "bố phơi nhiễm NSAID của quần thể nguồn sinh ra ca trong cùng thời gian"),
        "matching_type": "individual",
        "study_schema_timeline": ("Xác định ca → chọn 2 chứng ghép cặp cá thể theo giới và tuổi (± 2 năm), ghi mã bộ "
                                  "ghép → phỏng vấn phơi nhiễm → trích hồ sơ đơn thuốc"),
        "bias_controls": [
            dict(g1["bias_controls"][0]),
            {**g1["bias_controls"][1],
             "bien_phap": ("Chọn chứng cùng cơ sở và cùng tuần với ca, ghép cặp cá thể 2 chứng : 1 ca theo giới và "
                           "tuổi (± 2 năm), ghi mã bộ ghép cho từng bộ")},
            {**g1["bias_controls"][2],
             "bien_phap": ("Thu thập và hiệu chỉnh trong hồi quy logistic có điều kiện theo bộ ghép; giới và tuổi đã "
                           "được kiểm soát bằng ghép cặp cá thể")}]})
    g1["estimand"] = {**g1["estimand"], "population_summary_measure": "Tỷ số chênh (OR) có điều kiện hiệu chỉnh"}
    # 23/11/2026 (chiều): cỡ mẫu bệnh–chứng ghép cặp cá thể theo Dupont 1988 (G3 run_g3_auto, không còn công thức hai tỷ
    # lệ không ghép) — M = số chứng mỗi ca, φ = tương quan phơi nhiễm giữa ca và chứng cùng bộ
    gc["pi"]["G3"].update({
        "so_chung_moi_ca": 2, "phi": 0.2,
        "phi_source": ("Giả định φ = 0,2 (tương quan phơi nhiễm vừa giữa ca và chứng cùng giới, cùng tuổi) — chưa có "
                       "số liệu tại cơ sở; lực giảm khi φ tăng (Dupont 1988, PMID 3233252)"),
        "software": "run_g3_auto.py (bệnh–chứng ghép cặp cá thể — Dupont 1988)"})
    hs = gc["ho_so_tron_vong"]
    hs["G2"] = {**hs["G2"], "public_title": "NSAID và xuất huyết tiêu hoá trên ở người cao tuổi (ghép cặp cá thể)"}
    hs["ky_G2"] = _ky_g2(TIEN_CUU, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999983")
    # thống kê viên chọn phương pháp biến cố hiếm CÓ ĐIỀU KIỆN cho thiết kế ghép (khuôn G4 chỉ đưa lựa chọn này)
    from gia_lap_kich_ban_them import TRA_LOI_FIRTH_DK  # noqa: PLC0415

    hs["tra_loi_G4"] = [(r"bien co hiem", TRA_LOI_FIRTH_DK)] + _tra_loi_sap(
        "Không áp dụng — nghiên cứu bệnh–chứng, không có can thiệp", "thuốc chống đông/chống kết tập và tiền sử loét "
        "liên quan cả việc dùng NSAID lẫn xuất huyết (gây nhiễu); giới và tuổi đã được kiểm soát bằng ghép cặp cá thể "
        "(hằng trong bộ ghép) nên không đưa vào mô hình logistic có điều kiện", "VIF < 5 cho các hiệp biến",
        "Giới (nam/nữ) — ghi trước khi xem dữ liệu", "Loại người dùng thuốc chống đông")
    for pt in hs["g6"]:  # giới, tuổi là biến ghép — không ước lượng được trong hồi quy có điều kiện
        ts = pt.get("tham_so")
        if isinstance(ts, dict) and ts.get("covariates"):
            pt["tham_so"] = {**ts, "covariates": [c for c in ts["covariates"] if c not in ("tuoi", "gioi")]}
    hs["g6"][0]["mo_ta"] = "NSAID 30 ngày và xuất huyết tiêu hoá trên (OR có điều kiện theo bộ ghép, hiệu chỉnh)"
    dg = copy.deepcopy(hs["dien_giai"])
    dg["bang"] = [({**d, "thuoc_do": "OR thô có điều kiện (theo bộ ghép)", "lay": "or_tho_dk",
                    "y_nghia": "Gần với OR hiệu chỉnh — nhiễu đo được ít"} if d.get("lay") == "or_tho" else
                   {**d, "thuoc_do": d["thuoc_do"].replace("hồi quy logistic", "hồi quy logistic có điều kiện")})
                  for d in dg["bang"]]
    gc["ho_so_tron_vong"]["dien_giai"] = dg
    hs["dac_ta_G10"] = {**hs["dac_ta_G10"],
                        "bias_controls": ("Phơi nhiễm lấy từ hồ sơ kê đơn; chứng ghép cặp cá thể theo giới và tuổi "
                                          "(± 2 năm), mỗi bộ ghép có mã riêng, phân tích bằng hồi quy logistic có điều "
                                          "kiện theo bộ ghép hiệu chỉnh chống đông, tiền sử loét; độ nhạy loại người "
                                          "dùng chống đông"),
                        "summary": ("Bối cảnh: NSAID dùng phổ biến ở người cao tuổi. Mục tiêu: đánh giá liên quan giữa "
                                    "dùng NSAID 30 ngày và xuất huyết tiêu hoá trên. Phương pháp: bệnh–chứng ghép cặp "
                                    "cá thể, hồi quy logistic có điều kiện theo bộ ghép ước lượng OR hiệu chỉnh.")}
    hs["phan_bien_G8"] = {**hs["phan_bien_G8"], "thiet_ke": "Bệnh–chứng ghép cặp cá thể"}
    return gc


def _ghep_cap_thieu(gc: Dict[str, Any]) -> Dict[str, Any]:
    """BỆNH–CHỨNG GHÉP CẶP CÁ THỂ CÓ GIÁ TRỊ THIẾU (23/11/2026 chiều — điều phối giao: «biến thể có giá trị thiếu»):
    hiệp biến chống đông, tiền sử loét thiếu 15 % theo MAR (phụ thuộc tuổi). Phân tích chính: gán đa trị m = 20 giữ cấu
    trúc ghép (mô hình gán gồm ca/chứng + biến ghép — Seaman & Keogh 2015, PMID 26237003), hồi quy logistic có điều
    kiện trong từng bộ, gộp Rubin; ca đầy đủ báo song song. Đối chiếu R mice + clogit + gộp Rubin."""
    k = _sao(gc, id_test="case_control_ghep_cap_thieu",
             mo_ta="Bệnh–chứng ghép cặp cá thể 1:2, hiệp biến thiếu 15% theo MAR (gán đa trị giữ cấu trúc ghép)")
    k["bien_the"] = {**k["bien_the"], "thieu": {"cot": ["chong_dong", "tien_su_loet"], "ty_le": 0.15,
                                                "phu_thuoc": "tuoi", "ma": "KDD",
                                                "nhan": "Không có dữ liệu — hồ sơ và phỏng vấn không xác định được"}}
    k["pi"]["G1"].update({"critical_to_quality": ("Hồ sơ và phỏng vấn có thể thiếu thông tin thuốc chống đông/tiền sử "
                                                  "loét ~15% — kế hoạch gán đa trị giữ cấu trúc ghép định trước ở SAP "
                                                  "§6"),
                          "monitoring_plan": "Báo cáo tỷ lệ thiếu từng biến sau mỗi 50 bộ ghép"})
    hs = k["ho_so_tron_vong"]
    hs["ky_G2"] = {**hs["ky_G2"]}
    hs["g6"][0] = {**hs["g6"][0], "mo_ta": ("NSAID 30 ngày và xuất huyết tiêu hoá trên: OR có điều kiện theo bộ ghép "
                                            "sau gán đa trị (m = 20)"),
                   "tham_so": {**hs["g6"][0]["tham_so"], "n_imputations": 20}}
    dg = copy.deepcopy(hs["dien_giai"])
    dg["bang"] = [
        _dong("Xuất huyết tiêu hoá trên", "OR có điều kiện hiệu chỉnh sau gán đa trị (m = 20)", "pr_mi", "G6",
              "Phân tích chính theo SAP §6 ({pct_thieu}% số dòng thiếu ≥ 1 hiệp biến)"),
        _dong("Xuất huyết tiêu hoá trên", "OR có điều kiện hiệu chỉnh — ca đầy đủ", "or_hieu_chinh", "G6",
              "Đối chiếu: ca đầy đủ có thể lệch nếu thiếu không hoàn toàn ngẫu nhiên")]
    dg["muc_2"] = ("Sau gán đa trị 20 bộ dữ liệu giữ cấu trúc ghép ({pct_thieu}% số dòng thiếu ít nhất một hiệp biến), "
                   "dùng NSAID trong 30 ngày trước đi kèm odds xuất huyết tiêu hoá trên cao hơn: OR có điều kiện hiệu "
                   "chỉnh {pr_mi} (KTC 95% {pr_mi_duoi}–{pr_mi_tren}); phân tích ca đầy đủ cho OR {or_hieu_chinh} "
                   "({or_hieu_chinh_duoi}–{or_hieu_chinh_tren}). Về ý nghĩa lâm sàng, thiết kế bệnh–chứng không ước "
                   "lượng được nguy cơ tuyệt đối.")
    dg["muc_4"] = (dg["muc_4"] + " Gán đa trị đúng khi thiếu ngẫu nhiên có điều kiện (MAR), không kiểm chứng được từ "
                   "dữ liệu; nếu thiếu phụ thuộc chính giá trị bị thiếu (MNAR) thì cả hai cách đều có thể sai lệch, "
                   "nên kết quả ca đầy đủ được báo song song.")
    hs["dien_giai"] = dg
    tl = dict(hs["tra_loi_G7"])
    tl.update({r"khong dien truoc khi phan tich": ("Trong {n} người ({pct_thieu}% số dòng thiếu ≥ 1 hiệp biến), sau "
                                                   "gán đa trị giữ cấu trúc ghép (m = 20), dùng NSAID 30 ngày đi kèm "
                                                   "odds xuất huyết tiêu hoá trên cao hơn: OR có điều kiện hiệu chỉnh "
                                                   "{pr_mi} (KTC 95% {pr_mi_duoi}–{pr_mi_tren})."),
               r"khong chay gan da tri": ("Hiệp biến thiếu được gán đa trị m = 20 (mô hình gán gồm tình trạng ca/chứng "
                                          "và các biến ghép, giả định MAR), phân tích có điều kiện trong từng bộ, gộp "
                                          "Rubin; phân tích ca đầy đủ báo song song (SAP §6)")})
    hs["tra_loi_G7"] = list(tl.items())
    hs["phan_bien_G8"] = {**hs["phan_bien_G8"],
                          "ly_do": ("Gán đa trị giữ cấu trúc ghép theo SAP, OR có điều kiện sau gán {pr_mi} (KTC 95% "
                                    "{pr_mi_duoi}–{pr_mi_tren}) và ca đầy đủ báo song song; cần thảo luận giả định "
                                    "MAR.")}
    return k


def _ghep_cap_hiem(gc: Dict[str, Any]) -> Dict[str, Any]:
    """BỆNH–CHỨNG GHÉP CẶP CÁ THỂ ÍT CA — BIẾN CỐ HIẾM (23/11/2026 chiều — điều phối giao: «biến thể biến cố hiếm»):
    1 ca : 4 chứng, OR giả định 4,3 (NSAID không chọn lọc đơn trị, Masclee 2014, PMID 24937265) ⇒ Dupont 1988 cho ~27
    bộ ⇒ số ca dưới 10 × số tham số ⇒ rào EPV chặn hồi quy có điều kiện ⇒ G6 chạy phương pháp SAP §5 khai: hồi quy
    logistic có điều kiện có phạt Firth (Heinze & Puhr 2010, PMID 20213709); R đối chiếu, SPSS ghi không đối chiếu
    được."""
    k = _sao(gc, id_test="case_control_ghep_cap_hiem",
             mo_ta="Bệnh–chứng ghép cặp cá thể 1:4 ít ca (biến cố hiếm — Firth có điều kiện)")
    k["bien_the"] = {"ghep_cap": {**k["bien_the"]["ghep_cap"], "so_chung": 4}}
    bs = k["bien_so"]
    bs["bo_bien"] = [(b[0], b[1], "Mã bộ ghép (một ca và 4 chứng ghép cặp với ca đó)", *b[3:]) if b[0] == "ma_bo_ghep"
                     else b for b in bs["bo_bien"]]
    bs["ma_tran"] = [(*d[:1], "Bộ ghép (một ca cùng 4 chứng ghép cặp theo giới và tuổi ± 2 năm)", *d[2:])
                     if d[3] == "ma_bo_ghep" else d for d in bs["ma_tran"]]
    g1 = k["pi"]["G1"]
    g1.update({
        "control_source": g1["control_source"].replace("với 2 chứng (2 chứng cho mỗi ca; mỗi ca cùng 2 chứng",
                                                       "với 4 chứng (4 chứng cho mỗi ca; mỗi ca cùng 4 chứng"),
        "study_schema_timeline": g1["study_schema_timeline"].replace("chọn 2 chứng", "chọn 4 chứng"),
        "bias_controls": [dict(g1["bias_controls"][0]),
                          {**g1["bias_controls"][1],
                           "bien_phap": g1["bias_controls"][1]["bien_phap"].replace("2 chứng : 1 ca",
                                                                                    "4 chứng : 1 ca")},
                          dict(g1["bias_controls"][2])]})
    g3 = k["pi"]["G3"]
    g3.update({"effect_size": 4.3, "so_chung_moi_ca": 4,
               "effect_source": ("PMID: 24937265 (Masclee 2014, Gastroenterology) — đơn trị NSAID không chọn lọc làm "
                                 "tăng nguy cơ xuất huyết tiêu hoá trên (IRR 4,3, phân tích chuỗi ca); dùng làm OR giả "
                                 "định cho phơi nhiễm NSAID không chọn lọc")})
    from gia_lap_kich_ban_them import TRA_LOI_FIRTH_DK  # noqa: PLC0415

    hs = k["ho_so_tron_vong"]
    hs["tra_loi_G4"] = [(r"bien co hiem", TRA_LOI_FIRTH_DK)] + [x for x in hs["tra_loi_G4"] if x[0] != r"bien co hiem"]
    dg = copy.deepcopy(hs["dien_giai"])
    dg["bang"] = [_dong("Xuất huyết tiêu hoá trên", "OR có điều kiện có phạt Firth (biến cố hiếm)", "or_firth", "G6",
                        "Số ca dưới 10 lần số tham số — thay hồi quy có điều kiện theo SAP §5")]
    dg["muc_2"] = ("Với số ca ít so với số tham số của mô hình, hồi quy logistic có điều kiện có phạt Firth theo bộ "
                   "ghép (khai trước ở SAP §5) cho OR {or_firth} (KTC 95% hợp lý phạt hồ sơ {or_firth_duoi}–"
                   "{or_firth_tren}; p = {or_firth_p}). Về ý nghĩa lâm sàng, thiết kế bệnh–chứng không ước lượng được "
                   "nguy cơ tuyệt đối; khoảng tin cậy rộng phản ánh số ca ít.")
    dg["muc_4"] = (dg["muc_4"] + " Số ca ít nên ước lượng không chắc chắn; phương pháp có phạt Firth giảm lệch của ước "
                   "lượng khi dữ liệu thưa nhưng không thay được cỡ mẫu lớn hơn.")
    hs["dien_giai"] = dg
    tl = dict(hs["tra_loi_G7"])
    tl.update({r"khong dien truoc khi phan tich": ("Trong {n} người, hồi quy logistic có điều kiện có phạt Firth theo "
                                                   "bộ ghép cho OR {or_firth} (KTC 95% {or_firth_duoi}–"
                                                   "{or_firth_tren}).")})
    hs["tra_loi_G7"] = list(tl.items())
    hs["phan_bien_G8"] = {**hs["phan_bien_G8"],
                          "ly_do": ("Số ca ít; phương pháp biến cố hiếm định trước (Firth có điều kiện) cho OR "
                                    "{or_firth} (KTC 95% {or_firth_duoi}–{or_firth_tren}); cần thảo luận độ chắc chắn "
                                    "của ước lượng.")}
    return k


def _ho_so_bien_the(kb, rct, coh, _ky_g2, _nhom_gioi, _sd_khong_ap_dung, _tra_loi_sap) -> None:  # noqa: PLR0913
    """Hồ sơ trọn vòng (G2 → G10) của từng biến thể — sao từ kịch bản gốc, ghi đè phần khác."""
    gia_dinh_poisson = "Kiểm quá phân tán (Pearson χ²/df), dạng tuyến tính của tuổi, VIF < 5"
    nhom_gioi = "Giới (nam/nữ) — ghi trước khi xem dữ liệu"

    # ── 1. không kém hơn
    hs = copy.deepcopy(rct["ho_so_tron_vong"])
    hs["G2"].update({"public_title": "Tái khám qua điện thoại so với trực tiếp trong kiểm soát huyết áp",
                     "intervention_type": "other"})
    hs["ky_G2"] = _ky_g2(TIEN_CUU, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999981")
    hs["tra_loi_G4"] = _tra_loi_sap(
        "Biến cố do trì hoãn khám trực tiếp (huyết áp ≥ 180/110 mmHg, nhập viện) ghi theo phiếu biến cố",
        "tuổi và giới là yếu tố tiên lượng mạnh của kiểm soát huyết áp, hiệu chỉnh để tăng độ chính xác",
        "Kiểm dạng tuyến tính của tuổi; VIF < 5", nhom_gioi, "Phân tích theo đề cương (per-protocol)")
    hs["g6"] = [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                 "mo_ta": "Kiểm soát HA tháng 6: hiệu số tỷ lệ điện thoại − trực tiếp so với biên −10 điểm %",
                 "tham_so": {"outcome": "kiem_soat_t6", "group": "nhom", "covariates": ["tuoi", "gioi"],
                             "hiep_bien_phan_loai": ["gioi"]}},
                *_nhom_gioi(1, 2),
                {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Complete case vs MI",
                 "mo_ta": "Phân tích ca đầy đủ (không impute) đối chiếu với phân tích chính", "ke_thua": True,
                 "tham_so": {"n_imputations": 0}},
                _sd_khong_ap_dung("kết cục và nhóm so sánh đều nhị phân — định nghĩa thay thế chưa khai cụ thể"),
                # 22/11/2026: biến tuân thủ đề cương có trong bộ biến RCT (vai trò tuan_thu_de_cuong) ⇒ dựng từ ma trận
                {"id": "DN_theo_de_cuong", "vai": "do_nhay", "sap_muc": "§9", "tu_ma_tran": "theo_de_cuong",
                 "mo_ta": "Phân tích theo đề cương"}]
    hs["dien_giai"] = {
        "bang": [_dong("Kiểm soát huyết áp tháng 6", "Hiệu số tỷ lệ (điện thoại − trực tiếp)", "hieu_so_nguy_co",
                       "G6", "So với biên −{bien_ni} điểm %: {ni_ket_luan}"),
                 # SAP §4 của thử nghiệm không kém hơn: phân tích chính là HIỆU SỐ TỶ LỆ so với biên — không có RR
                 _dong("Nhóm nhỏ: nữ", "Hiệu số tỷ lệ", "hieu_so_nguy_co", "G6_NC_nu", "Thăm dò"),
                 _dong("Nhóm nhỏ: nam", "Hiệu số tỷ lệ", "hieu_so_nguy_co", "G6_NC_nam", "Thăm dò")],
        "muc_2": ("Hiệu số tỷ lệ kiểm soát huyết áp (điện thoại − trực tiếp) là {hieu_so_phan_tram} điểm % (KTC 95% "
                  "{hieu_so_duoi_pt} đến {hieu_so_tren_pt} điểm %). Cận dưới KTC so với biên −{bien_ni} điểm %: "
                  "{ni_ket_luan}. Trong thử nghiệm không kém hơn, kết luận dựa trên VỊ TRÍ cận dưới KTC so với biên, "
                  "không dựa trên giá trị p của kiểm định vượt trội. Về ý nghĩa lâm sàng, biên 10 điểm % là mức PI "
                  "chấp nhận đổi lấy sự tiện lợi của tái khám từ xa."),
        "muc_3": ("Thử nghiệm TEXT4BP (PMID 35342691) báo tỷ lệ đạt đích huyết áp 70% ở nhóm nhắn tin so với 48% ở "
                  "nhóm chứng sau 3 tháng; số liệu đó dùng để giả định tỷ lệ kiểm soát khoảng 60% khi tính cỡ mẫu. "
                  "Can thiệp và thiết kế khác (vượt trội, nhắn tin) nên chỉ đối chiếu mức tỷ lệ nền; tác giả chưa đọc "
                  "toàn văn bài này."),
        "muc_4": ("Điểm mạnh: ngẫu nhiên hoá, biên định trước trong SAP, cỡ mẫu {n} người, kiểm chéo SPSS–R khớp. Hạn "
                  "chế: phân tích theo đề cương chỉ gồm người tuân thủ (≥ 80% số lần can thiệp theo nhánh) nên có "
                  "thể lệch do chọn lọc sau ngẫu nhiên hoá và phải đọc cùng ITT; không làm mù người tham gia; một cơ "
                  "sở, nên kết quả chỉ khái quát cho người tăng huyết áp ổn định khám tại cơ sở tương tự."),
        "muc_5": ("Hàm ý cho thực hành: nếu kết luận vững ở cả ITT và per-protocol, tái khám qua điện thoại có thể "
                  "thay một phần tái khám trực tiếp cho người tăng huyết áp ổn định. Hướng tiếp: đo tuân thủ đề cương, "
                  "đánh giá chi phí và sự hài lòng."),
    }
    tl = dict(hs["tra_loi_G7"])
    tl.update({r"khong dien truoc khi phan tich": ("Trong {n} người được ngẫu nhiên hoá, hiệu số tỷ lệ kiểm soát huyết "
                                                   "áp (điện thoại − trực tiếp) là {hieu_so_phan_tram} điểm % (KTC 95% "
                                                   "{hieu_so_duoi_pt} đến {hieu_so_tren_pt}); so với biên −{bien_ni} "
                                                   "điểm %: {ni_ket_luan}."),
               r"^conclusions?$|2.3 cau tom tat": ("Tái khám qua điện thoại được so với tái khám trực tiếp theo biên "
                                                   "không kém hơn 10 điểm %: {ni_ket_luan}."),
               r"phan tich so sanh khi co ket qua": ("Đối chiếu tỷ lệ nền với TEXT4BP (PMID 35342691); tác giả "
                                                     "chưa đọc toàn văn bài này"),
               r"mesh terms": "Hypertension; Telemedicine; Equivalence Trial; Blood Pressure",
               # 23/11/2026: ô §3 «ai thực hiện can thiệp» — can thiệp của kịch bản này là TÁI KHÁM QUA ĐIỆN THOẠI
               r"ai thuc hien can thiep": ("Hai điều dưỡng phòng khám được tập huấn gọi tái khám hằng tháng theo "
                                           "kịch bản chuẩn; chủ nhiệm rà phiếu ghi cuộc gọi của ngẫu nhiên 10% số lần "
                                           "gọi để kiểm soát chất lượng; tuân thủ đo bằng số lần gọi thành công trên "
                                           "6 lần theo kế hoạch"),
               # thống kê viên viết lại đoạn diễn giải NI của G6 (chiều nhóm là quyết định người — engine không đoán)
               r"dien giai non.?inferiority": ("Nhóm 1 (tái khám qua điện thoại) là nhóm THỬ NGHIỆM, nhóm 0 (tái khám "
                                               "trực tiếp) là CHỨNG. Hiệu số tỷ lệ kiểm soát (thử − chứng) "
                                               "{hieu_so_phan_tram} điểm % (KTC 95% {hieu_so_duoi_pt} đến "
                                               "{hieu_so_tren_pt}); so với biên −{bien_ni} điểm %: {ni_ket_luan}. Kết "
                                               "luận dựa trên vị trí cận dưới KTC, không dựa trên p vượt trội.")})
    hs["tra_loi_G7"] = list(tl.items())
    hs["phan_bien_G8"].update({
        "ten_bai": "Tái khám qua điện thoại so với trực tiếp trong kiểm soát huyết áp",
        "thiet_ke": "Thử nghiệm ngẫu nhiên không kém hơn",
        "ly_do": ("Biên không kém hơn định trước, hiệu số tỷ lệ {hieu_so_phan_tram} điểm % (KTC 95% "
                  "{hieu_so_duoi_pt} đến {hieu_so_tren_pt}); cần đọc cùng phân tích theo đề cương."),
        "gop_y_nho": [("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng MeSH"),
                      ("Phương pháp — biên", "Biện minh biên 10 điểm % bằng dữ liệu lâm sàng (CONSORT mở rộng NI)"),
                      ("Kết quả — per-protocol", "Báo cáo phân tích theo đề cương cạnh ITT")],
        "cau_hoi": ["Biên 10 điểm % được chọn dựa trên nghiên cứu nào?",
                    "Bao nhiêu người ở nhóm điện thoại phải chuyển sang khám trực tiếp?"],
        "checklist": "CONSORT 2010 mở rộng không kém hơn (PMID 23268518)"})
    hs["dac_ta_G10"].update({
        "summary": ("Bối cảnh: tái khám từ xa có thể giảm gánh nặng đi lại. Mục tiêu: đánh giá tái khám qua điện thoại "
                    "có không kém hơn tái khám trực tiếp về kiểm soát huyết áp 6 tháng. Phương pháp: RCT không kém "
                    "hơn, biên hiệu số tỷ lệ −10 điểm %."),
        "comparator_rationale": "Tái khám trực tiếp là chuẩn chăm sóc hiện tại — so sánh không kém hơn (SPIRIT 9b)",
        "literature_review": "TEXT4BP (PMID 35342691) cho tỷ lệ đạt đích HA nền; chưa có thử nghiệm không kém hơn "
                             "tương tự tại Việt Nam"})
    kb["rct_khong_kem"]["ho_so_tron_vong"] = hs

    # ── 2. cụm
    hs = copy.deepcopy(rct["ho_so_tron_vong"])
    hs["G2"].update({"public_title": "Chương trình tin nhắn theo phòng khám và kiểm soát huyết áp"})
    hs["ky_G2"] = _ky_g2(TIEN_CUU, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999982")
    for pt in hs["g6"]:  # phân tích không kế thừa (chính, nhóm con) khai cột cụm; kế thừa thì nhận từ chính
        if pt.get("tham_so") and not pt.get("chua_tu_dong") and not pt.get("ke_thua"):
            pt["tham_so"] = {**pt["tham_so"], "cot_cum": "ma_phong_kham"}
    hs["g6"][0]["mo_ta"] = "Kiểm soát HA tháng 6: RR hiệu chỉnh, sai số theo cụm phòng khám"
    hs["dien_giai"] = copy.deepcopy(hs["dien_giai"])
    hs["dien_giai"]["bang"] = [
        _dong("Kiểm soát huyết áp tháng 6", "RR hiệu chỉnh (Poisson, sai số theo cụm)", "pr_hieu_chinh", "G6",
              "ICC {icc}, hiệu ứng thiết kế {de}"),
        _dong("Kiểm soát huyết áp tháng 6", "Hiệu số nguy cơ thô", "hieu_so_nguy_co", "G6", "NNT khoảng {nnh}"),
        _dong("Nhóm nhỏ: nữ", "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nu", "Thăm dò"),
        _dong("Nhóm nhỏ: nam", "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nam", "Thăm dò")]
    hs["dien_giai"]["muc_2"] = (
        "Chương trình tin nhắn đi kèm tỷ lệ kiểm soát huyết áp tháng 6 cao hơn (RR hiệu chỉnh {rr}; KTC 95% "
        "{rr_duoi}–{rr_tren}; p = {p}), khoảng tin cậy đã tính cấu trúc cụm phòng khám (ICC {icc}; hiệu ứng thiết kế "
        "{de}). Về ý nghĩa lâm sàng, hiệu số tuyệt đối khoảng {rd_phan_tram} điểm % ({pct1}% so với {pct0}%). Hai trục "
        "được báo tách riêng: ý nghĩa thống kê không đồng nghĩa với độ lớn lâm sàng.")
    hs["dien_giai"]["muc_4"] = (
        "Điểm mạnh: ngẫu nhiên hoá theo cụm tránh nhiễm chéo giữa người bệnh cùng phòng khám, phân tích tính ICC, cỡ "
        "mẫu {n} người, kiểm chéo SPSS–R khớp. Hạn chế: số cụm ít làm KTC theo cụm kém ổn định, người bệnh trong cùng "
        "phòng khám không độc lập, không làm mù; kết quả khái quát cho các phòng khám có cách tổ chức tương tự.")
    hs["phan_bien_G8"].update({"thiet_ke": "Thử nghiệm ngẫu nhiên theo cụm",
                               "ten_bai": "Chương trình tin nhắn theo phòng khám và kiểm soát huyết áp",
                               "checklist": "CONSORT 2010 mở rộng thử nghiệm cụm (PMID 22951546)"})
    hs["dac_ta_G10"].update({"randomization_type": "Ngẫu nhiên theo cụm (phòng khám) tỷ lệ 1:1, phân tầng theo quy "
                                                   "mô (SPIRIT 21b)",
                             # 22/11/2026 (CONSORT mở rộng cụm mục 10a): người sinh trình tự, mời và phân bổ CỤM — bản
                             # kế thừa từ RCT cá nhân («người tuyển mở phong bì kế tiếp») sai với thiết kế cụm
                             "allocation_access_control": ("Thống kê viên độc lập sinh và giữ danh sách phân bổ phòng "
                                                           "khám; chủ nhiệm mời phòng khám tham gia; sau khi lãnh đạo "
                                                           "phòng khám đồng ý, thống kê viên thông báo nhánh cho "
                                                           "phòng khám (SPIRIT 23)")})
    # thống kê viên chọn cách tính cấu trúc cụm ở SAP §4 (khớp G6: Poisson sai số chuẩn theo cụm phòng khám)
    # 23/11/2026: RCT gốc khai Firth cho biến cố hiếm; thiết kế CỤM giữ mô tả chính xác (Firth không có sai số chuẩn
    # theo cụm — chay_sap_g6 `kiem` chặn Firth kèm cột cụm)
    from gia_lap_kich_ban_them import TRA_LOI_MO_TA_CHINH_XAC  # noqa: PLC0415

    hs["tra_loi_G4"] = [(r"cau truc cum", "Hồi quy Poisson với sai số chuẩn theo cụm (cluster-robust), phòng khám là "
                                          "cụm"), (r"bien co hiem", TRA_LOI_MO_TA_CHINH_XAC)] + [
        x for x in hs.get("tra_loi_G4") or [] if x[0] != r"bien co hiem"]
    # 23/11/2026: thống kê viên xét cảnh báo SỐ CỤM mà G6 gắn dưới mọi ước lượng theo cụm (§3 và từng phân tích độ nhạy
    # ở §5) — một quyết định, khớp cách tính cấu trúc cụm đã chốt ở SAP §4; trước đây ô này rơi về «chưa có thông tin»
    hs["tra_loi_G7"] = [(r"ai thuc hien can thiep",  # 23/11/2026: tin nhắn triển khai theo PHÒNG KHÁM (cụm)
                         "Điều dưỡng đầu mối tại mỗi phòng khám thuộc nhánh can thiệp cài lịch gửi tin tự động cho "
                         "người bệnh của phòng khám mình và kiểm nhật ký gửi tin hằng tuần; nhóm nghiên cứu đối chiếu "
                         "tỷ lệ tin gửi thành công theo từng phòng khám hằng tháng"),
                        (r"g6 canh bao gan voi so o tren: so cum",
                         "Thống kê viên đã xét cảnh báo số cụm của G6: giữ sai số chuẩn hiệu chỉnh cụm có hiệu "
                         "chỉnh cỡ mẫu nhỏ và suy luận theo phân phối t với số bậc tự do bằng số cụm trừ một, đúng "
                         "cách tính cấu trúc cụm đã chốt ở SAP")] + list(hs.get("tra_loi_G7") or [])
    kb["rct_cum"]["ho_so_tron_vong"] = hs

    # ── 3. sống còn
    hs = copy.deepcopy(coh["ho_so_tron_vong"])
    hs["G2"].update({"public_title": "PPI kéo dài và thời gian đến gãy xương ở người cao tuổi"})
    hs["tra_loi_G4"] = _tra_loi_sap(
        "Không áp dụng — nghiên cứu quan sát hồi cứu, không có can thiệp do nghiên cứu chỉ định",
        "tuổi, corticoid toàn thân và loãng xương trước đó liên quan cả chỉ định PPI lẫn nguy cơ gãy xương (gây nhiễu "
        "trên DAG)", "Giả định nguy cơ tương xứng kiểm bằng phần dư Schoenfeld (cox.zph)", nhom_gioi,
        "Loại người theo dõi dưới 12 tháng")
    hs["g6"] = [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                 "mo_ta": "Thời gian đến gãy xương: HR hiệu chỉnh (Cox)",
                 "tham_so": {"time": "thoi_gian_den_gay", "event": "gay_xuong", "group": "ppi_dai_han",
                             "covariates": ["tuoi", "corticoid", "loang_xuong"]}},
                *_nhom_gioi(1, 0),
                {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Complete case vs MI",
                 "mo_ta": "Phân tích ca đầy đủ", "ke_thua": True, "tham_so": {"n_imputations": 0}},
                _sd_khong_ap_dung("phơi nhiễm nhị phân — định nghĩa thay thế chưa khai cụ thể"),
                {"id": "DN_theo_doi_12t", "vai": "do_nhay", "sap_muc": "§9",
                 "sap_neo": "Loại người theo dõi dưới 12 tháng", "mo_ta": "Chỉ người theo dõi ≥ 12 tháng",
                 "ke_thua": True, "tham_so": {"loc": "thoi_gian_den_gay >= 12"}}]
    hs["dien_giai"] = copy.deepcopy(hs["dien_giai"])
    hs["dien_giai"]["bang"] = [
        _dong("Thời gian đến gãy xương", "HR hiệu chỉnh (Cox)", "hr_hieu_chinh", "G6",
              "Tăng nguy cơ tức thời; đọc cùng tỷ lệ biến cố"),
        _dong("Thời gian đến gãy xương", "HR thô (Cox)", "hr_tho", "G6", "Gần HR hiệu chỉnh"),
        _dong("Nhóm nhỏ: nữ", "HR hiệu chỉnh", "hr_hieu_chinh", "G6_NC_nu", "Thăm dò"),
        _dong("Nhóm nhỏ: nam", "HR hiệu chỉnh", "hr_hieu_chinh", "G6_NC_nam", "Thăm dò"),
        _dong("Độ nhạy: theo dõi ≥ 12 tháng", "HR hiệu chỉnh", "hr_hieu_chinh", "G6_DN_theo_doi_12t",
              "Không đổi chiều khi loại người theo dõi ngắn")]
    hs["dien_giai"]["muc_2"] = (
        "Dùng PPI kéo dài đi kèm nguy cơ tức thời gãy xương cao hơn (HR hiệu chỉnh {hr_hieu_chinh}; KTC 95% "
        "{hr_hieu_chinh_duoi}–{hr_hieu_chinh_tren}; p = {hr_hieu_chinh_p}), với {bien_co_sc} biến cố trong {n} "
        "người. Về ý nghĩa lâm sàng, HR là tỷ số nguy cơ tức thời — cần đọc cùng nguy cơ tuyệt đối theo thời gian "
        "(đường Kaplan–Meier); hai trục được báo tách riêng.")
    hs["dien_giai"]["muc_3"] = (
        "Ước lượng cùng chiều với phân tích gộp quan sát của Zhou và cộng sự (2016): gãy xương mọi vị trí RR 1,33 (KTC "
        "95% 1,15–1,54) ở người dùng PPI (PMID 26462494). Thước đo khác (RR so với HR) nên chỉ đối chiếu chiều và độ "
        "lớn; tác giả chưa đọc toàn văn bài này.")
    hs["dien_giai"]["muc_4"] = (
        "Điểm mạnh: dùng trọn thông tin thời gian và kiểm duyệt, cỡ mẫu {n} người, kiểm chéo SPSS–R khớp. Hạn chế: "
        "giả định nguy cơ tương xứng cần kiểm bằng phần dư Schoenfeld, tử vong là biến cố cạnh tranh chưa mô hình hoá, "
        "nhiễu tồn dư của thiết kế hồi cứu. Tử vong cạnh tranh chưa mô hình hoá có thể làm ước tính cao nguy cơ tích "
        "luỹ gãy xương theo Kaplan–Meier, còn nhiễu do chỉ định có thể làm HR cao hơn thực; kết quả chỉ khái quát cho "
        "người từ 60 tuổi khám ngoại trú.")
    tl = dict(hs["tra_loi_G7"])
    tl.update({r"khong dien truoc khi phan tich": ("Trong {n} người ({bien_co_sc} biến cố), dùng PPI kéo dài đi kèm "
                                                   "nguy cơ tức thời gãy xương cao hơn: HR hiệu chỉnh {hr_hieu_chinh} "
                                                   "(KTC 95% {hr_hieu_chinh_duoi}–{hr_hieu_chinh_tren})."),
               r"^conclusions?$|2.3 cau tom tat": ("Ở người từ 60 tuổi khám ngoại trú, dùng PPI kéo dài liên quan với "
                                                   "nguy cơ tức thời gãy xương cao hơn."),
               r"khong chua ket cuc phu": "Kết cục phụ (gãy cổ xương đùi) chưa phân tích ở đợt này — báo cáo riêng"})
    hs["tra_loi_G7"] = list(tl.items())
    hs["phan_bien_G8"].update({"ten_bai": "PPI kéo dài và thời gian đến gãy xương",
                               "ly_do": ("Phân tích sống còn theo SAP, HR hiệu chỉnh {hr_hieu_chinh} (KTC 95% "
                                         "{hr_hieu_chinh_duoi}–{hr_hieu_chinh_tren}); cần báo kiểm định nguy cơ tương "
                                         "xứng và biến cố cạnh tranh."),
                               "gop_y_nho": [("Từ khoá (trang đầu)", "Thay bằng thuật ngữ MeSH"),
                                             ("Kết quả — Kaplan–Meier", "Thêm đường Kaplan–Meier và số người còn nguy "
                                                                        "cơ theo mốc"),
                                             ("Phương pháp — PH", "Báo kiểm định phần dư Schoenfeld (cox.zph)")]})
    hs["tham_so_G8"]["primary_outcome"] = "Thời gian đến gãy xương đầu tiên"
    kb["thuan_tap_song_con"]["ho_so_tron_vong"] = hs

    # ── 4. dữ liệu thiếu + MI
    hs = copy.deepcopy(coh["ho_so_tron_vong"])
    hs["tra_loi_G4"] = _tra_loi_sap(
        "Không áp dụng — nghiên cứu quan sát hồi cứu, không có can thiệp do nghiên cứu chỉ định",
        "tuổi, corticoid toàn thân và loãng xương trước đó liên quan cả chỉ định PPI lẫn nguy cơ gãy xương (gây nhiễu "
        "trên DAG)", gia_dinh_poisson, nhom_gioi, "Loại người theo dõi dưới 12 tháng")
    hs["g6"] = [{"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                 "mo_ta": "Nguy cơ gãy xương 3 năm: RR hiệu chỉnh sau gán đa trị (MI m=20)",
                 "tham_so": {"outcome": "gay_xuong_3nam", "group": "ppi_dai_han",
                             "covariates": ["tuoi", "corticoid", "loang_xuong"], "n_imputations": 20}},
                *_nhom_gioi(1, 0),
                {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Complete case vs MI",
                 "mo_ta": "Phân tích ca đầy đủ (không gán đa trị) đối chiếu MI", "ke_thua": True,
                 "tham_so": {"n_imputations": 0}},
                _sd_khong_ap_dung("phơi nhiễm và kết cục nhị phân — định nghĩa thay thế chưa khai cụ thể"),
                {"id": "DN_theo_doi_12t", "vai": "do_nhay", "sap_muc": "§9",
                 "sap_neo": "Loại người theo dõi dưới 12 tháng", "mo_ta": "Chỉ người theo dõi ≥ 12 tháng",
                 "ke_thua": True, "tham_so": {"loc": "thoi_gian_theo_doi >= 12"}}]
    hs["dien_giai"] = copy.deepcopy(hs["dien_giai"])
    hs["dien_giai"]["bang"] = [
        _dong("Gãy xương mọi vị trí trong 3 năm", "RR hiệu chỉnh sau gán đa trị (MI m=20)", "pr_mi", "G6",
              "Phân tích chính theo SAP §6 ({pct_thieu}% số dòng thiếu ≥ 1 biến)"),
        _dong("Gãy xương mọi vị trí trong 3 năm", "RR hiệu chỉnh — ca đầy đủ", "pr_hieu_chinh", "G6",
              "Đối chiếu: ca đầy đủ có thể lệch nếu thiếu không hoàn toàn ngẫu nhiên"),
        _dong("Nhóm nhỏ: nữ", "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nu", "Thăm dò"),
        _dong("Nhóm nhỏ: nam", "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nam", "Thăm dò")]
    hs["dien_giai"]["muc_2"] = (
        "Sau gán đa trị 20 bộ dữ liệu cho hiệp biến thiếu ({pct_thieu}% số dòng thiếu ít nhất một biến), dùng PPI kéo "
        "dài đi kèm nguy cơ gãy xương cao hơn: RR hiệu chỉnh {pr_mi} (KTC 95% {pr_mi_duoi}–{pr_mi_tren}); phân "
        "tích ca đầy đủ cho RR {pr_hieu_chinh} ({pr_hieu_chinh_duoi}–{pr_hieu_chinh_tren}). Về ý nghĩa lâm sàng, "
        "hiệu số nguy cơ khoảng {rd_phan_tram} điểm %. Hai trục được báo tách riêng.")
    hs["dien_giai"]["muc_4"] = (
        "Điểm mạnh: kế hoạch gán đa trị định trước (SAP §6), báo song song ca đầy đủ, cỡ mẫu {n} người, kiểm chéo "
        "SPSS–R khớp. Hạn chế: gán đa trị đúng khi thiếu ngẫu nhiên có điều kiện (MAR) — không kiểm chứng được từ "
        "dữ liệu; nếu thiếu phụ thuộc chính giá trị bị thiếu (MNAR) thì cả hai cách đều có thể sai lệch. Hướng của sai "
        "lệch phụ thuộc cơ chế thiếu, nên kết quả ca đầy đủ được báo song song để người đọc thấy độ lớn chênh lệch; "
        "nhiễu tồn dư của thiết kế hồi cứu vẫn còn, và kết quả chỉ khái quát cho người từ 60 tuổi khám ngoại trú.")
    tl = dict(hs["tra_loi_G7"])
    tl.update({r"khong dien truoc khi phan tich": ("Trong {n} người ({pct_thieu}% số dòng thiếu ≥ 1 hiệp biến), sau "
                                                   "gán đa trị (m = 20) dùng PPI kéo dài đi kèm nguy cơ gãy xương cao "
                                                   "hơn: RR hiệu chỉnh {pr_mi} (KTC 95% {pr_mi_duoi}–{pr_mi_tren})."),
               r"khong chay gan da tri": ("Hiệp biến thiếu được gán đa trị m = 20 (MICE, giả định MAR); phân tích ca "
                                          "đầy đủ báo song song (SAP §6)")})
    hs["tra_loi_G7"] = list(tl.items())
    hs["phan_bien_G8"].update({"ly_do": ("Gán đa trị theo SAP, RR sau MI {pr_mi} (KTC 95% {pr_mi_duoi}–{pr_mi_tren}) "
                                         "và ca đầy đủ báo song song; cần thảo luận giả định MAR."),
                               "gop_y_nho": [("Từ khoá (trang đầu)", "Thay bằng thuật ngữ MeSH"),
                                             ("Phương pháp — MI", "Liệt kê biến trong mô hình gán và số vòng lặp"),
                                             ("Thảo luận — MNAR", "Thêm phân tích độ nhạy delta-adjustment cho MNAR")]})
    kb["thuan_tap_mi"]["ho_so_tron_vong"] = hs


def danh_sach() -> List[Tuple[str, str]]:
    """(mã kịch bản, id test) theo thứ tự — cho tệp test trọn vòng."""
    return [(ma, kb["id_test"]) for ma, kb in kich_ban_kho().items()]


# ══ PLS-SEM — khảo sát cắt ngang có cấu trúc tiềm ẩn (23/11/2026) ════════════════════════════════════════════════════
_LIKERT = "1, Rất không đồng ý | 2, Không đồng ý | 3, Phân vân | 4, Đồng ý | 5, Rất đồng ý"
_CAU_PLS = (
    ("GT", "Giao tiếp bác sĩ – người bệnh", "A", (
        ("gt_1", "Bác sĩ giải thích rõ về bệnh và thuốc cho tôi"),
        ("gt_2", "Bác sĩ lắng nghe điều tôi lo lắng"),
        ("gt_3", "Tôi có đủ thời gian hỏi bác sĩ khi khám"))),
    ("HB", "Hiểu biết về bệnh tăng huyết áp", "B", (
        ("hb_1", "Tôi biết huyết áp mục tiêu của mình"),
        ("hb_2", "Tôi biết tác hại của tăng huyết áp không kiểm soát"),
        ("hb_3", "Tôi biết cách dùng và tác dụng phụ thường gặp của thuốc"))),
    ("NT", "Niềm tin vào điều trị", "A", (
        ("nt_1", "Thuốc hạ áp giúp tôi phòng biến chứng"),
        ("nt_2", "Lợi ích của thuốc lớn hơn phiền toái khi dùng"),
        ("nt_3", "Tôi tin điều trị hiện tại phù hợp với tôi"))),
    ("TT", "Tuân thủ điều trị", "A", (
        ("tt_1", "Tôi uống thuốc đúng giờ mỗi ngày"),
        ("tt_2", "Tôi không tự ý bỏ thuốc khi thấy khoẻ"),
        ("tt_3", "Tôi không quên uống thuốc trong tuần qua"))),
)
_DD_PLS = [["GT", "NT"], ["HB", "NT"], ["GT", "TT"], ["HB", "TT"], ["NT", "TT"]]


def _pls_sem(cn: Dict[str, Any], vi: Callable[[str], str], tt: str, _ky_g2: Callable, _tra_loi_sap: Callable,
             _nhom_gioi: Callable) -> Dict[str, Any]:
    """CẮT NGANG PHÂN TÍCH BẰNG PLS-SEM (23/11/2026 — bác sĩ: «PLS-SEM tốt nhất, tương tự SPSS/R»).

    Khảo sát người tăng huyết áp điều trị ngoại trú: bốn cấu trúc tiềm ẩn đo bằng câu hỏi Likert 1–5 — giao tiếp bác
    sĩ – người bệnh (kết quả, Mode A), hiểu biết về bệnh (CẤU TẠO, Mode B), niềm tin vào điều trị (Mode A), tuân thủ
    điều trị (Mode A); năm đường dẫn giả thuyết. PI chốt mô hình ở G1 (gate_params.G1.pls_sem) ⇒ SAP §4 in khối
    PLS-SEM ⇒ G6 chạy pls_sem.py (seminr chính + cSEM kiểm chéo) ⇒ G7 chép bảng trình bày theo Hair 2019. Cỡ mẫu theo
    căn bậc hai nghịch đảo (Kock & Hadaya 2018) với |β_min| = 0,20. Dữ liệu MÔ PHỎNG từ mô hình cấu trúc đã khai
    (bien_the.pls_sem)."""
    kb = _sao(cn, study=f"{tt}CAT-NGANG-PLS-SEM", id_test="cross_sectional_pls_sem", goc="cat_ngang_mo_ta",
              mo_ta="Cắt ngang phân tích bằng PLS-SEM (4 cấu trúc tiềm ẩn, 1 cấu trúc cấu tạo)",
              topic=("Giao tiếp bác sĩ – người bệnh, hiểu biết về bệnh, niềm tin vào điều trị và tuân thủ điều trị ở "
                     "người tăng huyết áp điều trị ngoại trú: nghiên cứu cắt ngang phân tích bằng mô hình PLS-SEM"),
              query_en=('(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR '
                        'adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR '
                        '"health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path '
                        'analysis"[tiab] OR "partial least squares"[tiab])'),
              bien_the={"pls_sem": {
                  "cau_truc": [{"ma": "GT", "muc": ["gt_1", "gt_2", "gt_3"], "mode": "A", "tai": 0.82},
                               {"ma": "HB", "muc": ["hb_1", "hb_2", "hb_3"], "mode": "B", "trong_so": [0.5, 0.4, 0.3],
                                "r_chi_bao": 0.3},
                               {"ma": "NT", "muc": ["nt_1", "nt_2", "nt_3"], "mode": "A", "tai": 0.8},
                               {"ma": "TT", "muc": ["tt_1", "tt_2", "tt_3"], "mode": "A", "tai": 0.8}],
                  "duong_dan": [["NT", {"GT": 0.35, "HB": 0.25}], ["TT", {"GT": 0.15, "HB": 0.15, "NT": 0.4}]],
                  "duong_dan_chinh": "NT -> TT", "r_ngoai": 0.3, "sd_nhieu": 0.8},
                  # phiếu tự điền: câu bỏ trống ghi mã thiếu dự án «BTR» (câu bắt buộc không để ô trống)
                  "thieu": {"cot": ["gt_3", "nt_3", "tt_3"], "ty_le": 0.03, "phu_thuoc": "tuoi", "ma": "BTR",
                            "nhan": "Bỏ trống — người trả lời không đánh dấu câu này"}})
    muc = [(m, nhan) for _ma, _ten, _mode, ds in _CAU_PLS for m, nhan in ds]
    kb["bien_so"] = {
        "bo_bien": [("record_id", "text", "Mã nghiên cứu", "", "", "", ""),
                    ("ngay_kham", "text", "Ngày khám khảo sát", "", "date_dmy", "", ""),
                    ("tuoi", "text", "Tuổi (năm)", "", "integer", "18", "110"),
                    ("gioi", "radio", "Giới", "1, Nam | 2, Nữ", "", "", ""),
                    *[(m, "radio", nhan, _LIKERT, "", "", "") for m, nhan in muc],
                    ("diem_tt", "calc", "Điểm tuân thủ trung bình 3 câu (1–5, máy tự tính)",
                     "([tt_1] + [tt_2] + [tt_3]) / 3", "", "", "")],
        "ma_tran": [("1", "tuân thủ điều trị (điểm trung bình thang tuân thủ)", "ket_cuc_chinh", "diem_tt",
                     "lien_tuc", "D1", "thang tuân thủ 3 câu", "SAP §2 kết cục chính; cấu trúc TT ở SAP §4"),
                    *[("1", f"{ten.lower()} — câu {m}", "yeu_to", m, "thu_tu", f"C{i + 1}", "phỏng vấn bộ câu hỏi",
                       "SAP §4 mô hình đo lường PLS-SEM")
                      for i, (ma, ten, _mode, ds) in enumerate(_CAU_PLS) for m, _nhan in ds],
                    ("1", "tuổi", "mo_ta", "tuoi", "lien_tuc", "A1", "phiếu", "SAP §3 mô tả"),
                    ("1", "giới", "mo_ta", "gioi", "nhi_phan", "A2", "phiếu", "SAP §3 mô tả")],
    }
    g0, g1 = kb["pi"]["G0"], kb["pi"]["G1"]
    g0.update({
        "intervention": "Không áp dụng — nghiên cứu quan sát (yếu tố khảo sát: giao tiếp, hiểu biết, niềm tin)",
        "comparison": "Không áp dụng — mô hình cấu trúc trên một nhóm",
        "outcomes": ["Tuân thủ điều trị thuốc hạ áp (cấu trúc tiềm ẩn đo bằng 3 câu)",
                     "Ảnh hưởng của giao tiếp, hiểu biết và niềm tin lên tuân thủ (hệ số đường dẫn)"],
        "primary_outcome": "Tuân thủ điều trị thuốc hạ áp",
        "primary_outcome_measure": "Thang tuân thủ 3 câu Likert 1–5 (cấu trúc TT của mô hình PLS-SEM)",
        "primary_outcome_timepoint": "Tại lần khám khảo sát",
        "hypothesis_h0": "Hệ số đường dẫn từ niềm tin vào điều trị đến tuân thủ điều trị bằng 0",
        "hypothesis_h1": "Hệ số đường dẫn từ niềm tin vào điều trị đến tuân thủ điều trị khác 0",
        "expected_direction": "Niềm tin vào điều trị cao hơn đi kèm tuân thủ tốt hơn (hệ số dương)",
        "test_type": "superiority", "question_type": "harm",
        "novelty_justification": vi("Chưa có mô hình cấu trúc giao tiếp – hiểu biết – niềm tin – tuân thủ ở người "
                                    "tăng huyết áp ngoại trú tại cơ sở này")})
    g0.pop("descriptive_justification", None)
    g1.update({
        "design_rationale": vi("Câu hỏi về liên quan giữa các cấu trúc tiềm ẩn đo một lần — cắt ngang phân tích; "
                               "mô hình cấu trúc ước lượng bằng PLS-SEM"),
        # động từ mục tiêu theo khuôn STROBE mục 3 của K17 (Phân tích/Ước tính/Xác định…)
        "objectives": ["Phân tích ảnh hưởng của giao tiếp bác sĩ – người bệnh, hiểu biết về bệnh và niềm tin vào "
                       "điều trị lên tuân thủ điều trị ở người tăng huyết áp điều trị ngoại trú"],
        "research_question": ("Ở người tăng huyết áp điều trị ngoại trú, giao tiếp bác sĩ – người bệnh, hiểu biết về "
                              "bệnh và niềm tin vào điều trị ảnh hưởng thế nào đến tuân thủ điều trị?"),
        "primary_outcome": {"name": "Tuân thủ điều trị thuốc hạ áp",
                            "measure": "Thang tuân thủ 3 câu Likert 1–5 (cấu trúc TT của mô hình PLS-SEM)",
                            "timepoint": "Tại lần khám khảo sát", "type": "liên tục"},
        "secondary_outcomes": ["Ảnh hưởng của giao tiếp, hiểu biết và niềm tin lên tuân thủ (hệ số đường dẫn)"],
        "intervention_or_exposure": "Giao tiếp bác sĩ – người bệnh, hiểu biết về bệnh, niềm tin vào điều trị",
        "data_collection_method": "Phỏng vấn bộ câu hỏi 12 câu Likert tại phòng khám, ghi vào phiếu thu thập",
        "critical_to_quality": "Bộ câu hỏi phỏng vấn chuẩn hoá, điều tra viên tập huấn, đọc nguyên văn câu hỏi",
        "estimand": {
            "population": "Người tăng huyết áp điều trị ngoại trú đủ tiêu chuẩn",
            "treatment_condition": "Không áp dụng (quan sát)",
            "variable": "Tuân thủ điều trị (cấu trúc tiềm ẩn TT)",
            "intercurrent_events_strategy": "Không áp dụng (một lần đo)",
            "population_summary_measure": "Hệ số đường dẫn PLS-SEM kèm KTC 95% bootstrap phân vị"},
        "background_problem": vi("Tuân thủ điều trị thuốc hạ áp ở người điều trị ngoại trú chưa được đo cùng các yếu "
                                 "tố giao tiếp, hiểu biết và niềm tin"),
        "knowledge_gap": vi("Thiếu mô hình cấu trúc các yếu tố tâm lý – giao tiếp của tuân thủ điều trị tại cơ sở này"),
        # câu bằng chứng chép đúng số trong abstract PubMed (PMID 36803662, BMC Cardiovasc Disord 2023) — kho A12
        "evidence_summary": ("Nghiên cứu cắt ngang cộng đồng trên 1697 người tăng huyết áp tại Thượng Hải (PMID "
                             "36803662) dùng mô hình phương trình cấu trúc ghi nhận tỷ lệ người bệnh tuân thủ thuốc "
                             "ở mức thấp là 38,54%; hiểu biết sức khoẻ ảnh hưởng trực tiếp lên tuân thủ (β = 0,291) "
                             "và hỗ trợ xã hội ảnh hưởng trực tiếp lên tuân thủ (β = 0,165)"),
        "bias_controls": [
            {"sai_lech": "Sai lệch chọn do chọn mẫu liên tiếp người đến khám",
             "bien_phap": "Tuyển liên tiếp mọi người đủ tiêu chuẩn trong các ngày khám; ghi số người từ chối và lý do",
             "chieu": "Người tái khám đều đặn thường tuân thủ tốt hơn nên mức tuân thủ có thể được ước lượng cao hơn"},
            {"sai_lech": "Sai lệch mong muốn xã hội khi tự khai tuân thủ",
             "bien_phap": ("Điều tra viên không phải bác sĩ điều trị; phỏng vấn riêng, nhắc không có câu trả lời "
                           "đúng sai"),
             "chieu": "Người bệnh có xu hướng khai tuân thủ tốt hơn thực tế nên hệ số đường dẫn có thể bị thu nhỏ"}],
        "pls_sem": {
            "cau_truc": [{"ma": ma, "ten": ten, "muc": [m for m, _n in ds], "mode": mode}
                         for ma, ten, mode, ds in _CAU_PLS],
            "duong_dan": [list(x) for x in _DD_PLS],
            "bien_minh": ("Mục tiêu giải thích và dự báo tuân thủ (cấu trúc đích TT) trên mô hình có cấu trúc CẤU TẠO "
                          "(hiểu biết về bệnh là chỉ số gộp ba hiểu biết riêng, không phải nhân tố chung) — tình huống "
                          "Hair và cộng sự 2019 khuyến nghị PLS-SEM; CB-SEM giả định mọi cấu trúc là nhân tố chung"),
            "bootstrap": 5000, "plspredict": {"k": 10, "lap": 10, "dich": ["TT"]}, "du_lieu_thieu": "listwise"},
    })
    g3 = kb["pi"]["G3"]
    g3.clear()
    g3.update({"effect_size": 0.2, "effect_type": "PLS_PATH", "alpha": 0.05, "power": 0.8, "dropout": 0.1,
               "hypothesis_type": "superiority",
               # nguồn |β_min| là nghiên cứu trước có số liệu thật trong abstract PubMed (kho A12): β 0,165 và 0,291
               "effect_source": ("PMID: 36803662 (nghiên cứu cắt ngang tại Thượng Hải) — các hệ số đường dẫn trực tiếp "
                                 "tới tuân thủ ghi nhận 0,165 và 0,291; chọn |β_min| = 0,20 trong khoảng này"),
               "dropout_source": "Giả định 10% phiếu không dùng được — chưa có nguồn y văn",
               "effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
               # tên kết cục chính G1 (G3-HUMAN-04): lực cho các hệ số đường dẫn tới cấu trúc tuân thủ, nhỏ nhất 0,20
               "powered_for_outcome": "Tuân thủ điều trị thuốc hạ áp",
               "recruitment_feasibility_confirmed": True,
               "software": "run_g3_auto.py (PLS-SEM — căn bậc hai nghịch đảo, Kock & Hadaya 2018)"})
    hs = kb["ho_so_tron_vong"]
    hs["G2"] = {**hs["G2"], "public_title": "Giao tiếp, hiểu biết, niềm tin và tuân thủ điều trị tăng huyết áp"}
    hs["ky_G2"] = _ky_g2(TIEN_CUU, "REGISTERED", registry="ClinicalTrials.gov", ma_dk="NCT99999979")
    hs["tra_loi_G4"] = _tra_loi_sap(
        "Không áp dụng — nghiên cứu cắt ngang quan sát, không có can thiệp", "các cấu trúc tiền tố theo mô hình lý "
        "thuyết G1 — không thêm biến hiệu chỉnh ngoài mô hình", "VIF < 3 cho chỉ báo cấu tạo và cấu trúc tiền tố",
        "Giới (nam/nữ) — ghi trước khi xem dữ liệu", "Ô thiếu thay bằng trung bình chỉ báo")
    hs["g6"] = [{"id": "MT1_pls_sem", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                 "mo_ta": "Mô hình PLS-SEM: giao tiếp, hiểu biết, niềm tin → tuân thủ điều trị",
                 "tham_so": {"pls_sem": "pls_pm", "bootstrap_pls": 5000}},
                *_nhom_gioi(1, 2),
                {"id": "DN_trung_binh", "vai": "do_nhay", "sap_muc": "§9",
                 "sap_neo": "ô thiếu thay bằng trung bình chỉ báo", "ke_thua": True,
                 "mo_ta": "Độ nhạy: ô thiếu thay bằng trung bình chỉ báo (phân tích chính: listwise)",
                 "tham_so": {"du_lieu_thieu": "trung_binh"}}]
    hs["dien_giai"] = {
        "bang": [{"ket_cuc": "Niềm tin vào điều trị → tuân thủ điều trị", "thuoc_do": "Hệ số đường dẫn PLS-SEM (β)",
                  "lay": "pls_beta", "gate": "G6", "y_nghia": "Giả thuyết chính — ảnh hưởng dương trung bình"},
                 {"ket_cuc": "Nhóm nhỏ: nam", "thuoc_do": "β (niềm tin → tuân thủ)", "lay": "pls_beta",
                  "gate": "G6_NC_nam", "y_nghia": "Mô tả theo nhóm định trước; thăm dò"},
                 {"ket_cuc": "Nhóm nhỏ: nữ", "thuoc_do": "β (niềm tin → tuân thủ)", "lay": "pls_beta",
                  "gate": "G6_NC_nu", "y_nghia": "Mô tả theo nhóm định trước; thăm dò"}],
        "muc_2": ("Niềm tin vào điều trị có ảnh hưởng dương lên tuân thủ điều trị (β = {pls_beta}; KTC 95% bootstrap "
                  "{pls_beta_duoi}–{pls_beta_tren}). Đây là ước lượng của mô hình cấu trúc trên dữ liệu cắt "
                  "ngang: hệ số đường dẫn mô tả liên quan có hướng theo mô hình lý thuyết, không chứng minh quan hệ "
                  "nhân quả. Về ý nghĩa lâm sàng, hệ số chuẩn hoá này cho biết người có niềm tin vào điều trị cao hơn "
                  "một độ lệch chuẩn có điểm tuân thủ cao hơn khoảng {pls_beta} độ lệch chuẩn khi giao tiếp và hiểu "
                  "biết như nhau; thang tuân thủ chưa có ngưỡng khác biệt tối thiểu có ý nghĩa lâm sàng nên độ lớn "
                  "này chưa quy đổi được thành tỷ lệ người bệnh dùng thuốc đúng."),
        "muc_3": ("Nghiên cứu cắt ngang cộng đồng tại Thượng Hải (PMID 36803662) dùng mô hình phương trình cấu trúc "
                  "hiệp phương sai ghi nhận hiểu biết sức khoẻ ảnh hưởng trực tiếp lên tuân thủ (β = 0,291). Thang đo, "
                  "phương pháp ước lượng và quần thể khác nhau nên hai hệ số không so trực tiếp được."),
        "muc_4": ("Điểm mạnh: cỡ mẫu {n} người theo tính toán G3, mô hình định trước ở SAP, ước lượng bằng seminr và "
                  "kiểm chéo độc lập bằng cSEM. Hạn chế: một thời điểm đo nên không xác định chiều thời gian; tuân thủ "
                  "tự khai có thể bị sai lệch mong muốn xã hội — người bệnh khai tuân thủ cao hơn thực tế làm thu hẹp "
                  "phân tán điểm tuân thủ nên hệ số đường dẫn tới tuân thủ có xu hướng bị ước lượng thấp; một cơ sở "
                  "nên khái quát cho người tăng huyết áp điều trị ngoại trú ở cơ sở tương tự."),
        "muc_5": ("Hàm ý cho thực hành: cải thiện giao tiếp và củng cố niềm tin vào điều trị là đích can thiệp có thể "
                  "thử ở phòng khám. Hướng tiếp: thử nghiệm can thiệp giao tiếp có đo tuân thủ khách quan.")}
    hs["tra_loi_G7"] = [
        ("khong dien truoc khi phan tich", "Trong {n} người tăng huyết áp điều trị ngoại trú, niềm tin vào điều trị "
         "ảnh hưởng dương lên tuân thủ điều trị: β = {pls_beta} (KTC 95% {pls_beta_duoi}–{pls_beta_tren})."),
        ("^conclusions?$|2.3 cau tom tat", "Niềm tin vào điều trị liên quan dương với tuân thủ điều trị ở người tăng "
         "huyết áp điều trị ngoại trú; hệ số đường dẫn của mô hình cấu trúc trên dữ liệu cắt ngang không chứng minh "
         "quan hệ nhân quả."),
        ("khong chua ket cuc phu", "Ảnh hưởng của giao tiếp và hiểu biết lên tuân thủ trình bày ở bảng mô hình cấu "
         "trúc PLS-SEM (Kết quả, mục kết cục chính)"),
        ("khong chay gan da tri", "Không gán đa trị — ô thiếu xử lý theo SAP §4 (listwise), độ nhạy thay trung bình "
         "chỉ báo theo SAP §9"),
        *[x for x in hs["tra_loi_G7"] if x[0] not in ("khong dien truoc khi phan tich",
                                                       "^conclusions?$|2.3 cau tom tat",
                                                       "khong chua ket cuc phu", "khong chay gan da tri",
                                                       "mesh terms", "phan tich so sanh khi co ket qua",
                                                       "giai thich sinh hoc")],
        ("giai thich sinh hoc", "Không áp dụng — nghiên cứu hành vi, không đánh giá cơ chế sinh học"),
        ("phan tich so sanh khi co ket qua", "Đối chiếu ở đoạn so sánh với nghiên cứu Thượng Hải (PMID 36803662); tác "
         "giả chưa đọc toàn văn bài này"),
        ("mesh terms", "Hypertension; Medication Adherence; Physician-Patient Relations; Latent Class Analysis")]
    hs["phan_bien_G8"] = {
        **hs["phan_bien_G8"], "ten_bai": "Giao tiếp, niềm tin và tuân thủ điều trị ở người tăng huyết áp ngoại trú",
        "thiet_ke": "Cắt ngang phân tích — mô hình PLS-SEM",
        "ly_do": ("Mô hình định trước ở SAP, β niềm tin → tuân thủ {pls_beta} (KTC 95% {pls_beta_duoi}–"
                  "{pls_beta_tren}) kiểm chéo seminr–cSEM khớp. Còn vài điểm trình bày theo STROBE và Hair 2019."),
        "gop_y_nho": [("Từ khoá (trang đầu)", "Thay bằng thuật ngữ MeSH"),
                      ("Phương pháp — bộ câu hỏi", "Nêu nguồn gốc và quy trình thích nghi bộ câu hỏi (STROBE mục 8)")],
        "cau_hoi": ["Vì sao hiểu biết về bệnh được mô hình hoá là cấu trúc cấu tạo?",
                    "Đã kiểm sai lệch phương pháp chung (common method bias) chưa?"]}
    hs["dac_ta_G10"] = {
        **{k: v for k, v in hs["dac_ta_G10"].items() if k != "theoretical_framework_not_applicable"},
        "bias_risks": "Sai lệch chọn (một cơ sở); sai lệch mong muốn xã hội khi tự khai tuân thủ; sai lệch phương pháp "
                      "chung do mọi câu hỏi cùng một lần phỏng vấn",
        "bias_controls": "Chọn liên tiếp theo danh sách khám; điều tra viên không phải bác sĩ điều trị; mô hình định "
                         "trước và kiểm chéo độc lập bằng cSEM",
        "literature_review": "Mô hình phương trình cấu trúc trên 1697 người tăng huyết áp tại Thượng Hải (PMID "
                             "36803662) cho thấy hiểu biết sức khoẻ và hỗ trợ xã hội ảnh hưởng trực tiếp lên tuân thủ; "
                             "mô hình cấu trúc tại phòng khám ngoại trú Việt Nam còn ít",
        "theoretical_framework": "Mô hình niềm tin sức khoẻ: giao tiếp và hiểu biết ảnh hưởng niềm tin, niềm tin ảnh "
                                 "hưởng hành vi tuân thủ — năm đường dẫn ở SAP §4",
        "literature_consensus": "Niềm tin vào sự cần thiết của thuốc liên quan tuân thủ tốt hơn",
        "literature_disagreements": "Độ lớn liên quan khác nhau theo thang đo tuân thủ và bối cảnh",
        "summary": ("Bối cảnh: tuân thủ điều trị tăng huyết áp chưa được đo cùng yếu tố giao tiếp và niềm tin. Mục "
                    "tiêu: phân tích ảnh hưởng của giao tiếp, hiểu biết và niềm tin lên tuân thủ. Phương pháp: cắt "
                    "ngang, mô hình PLS-SEM (seminr, kiểm chéo cSEM)."),
        "pilot": "Thử bộ câu hỏi trên 15 người ngoài mẫu nghiên cứu",
        "limitations": "Một cơ sở; một thời điểm đo; tuân thủ tự khai"}
    kb["ho_so_tron_vong"] = hs
    return kb
