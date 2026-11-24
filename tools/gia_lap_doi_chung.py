"""Kịch bản ĐỐI CHỨNG CÔNG KHAI cho bộ giả lập trọn vòng (24/11/2026 — bác sĩ duyệt 23/11): G0 → G10 như mọi kịch bản,
nhưng G5 nhập DỮ LIỆU THẬT đã công bố thay cho dữ liệu sinh, và báo cáo có phép «đối chứng»: ước lượng G6 phải tìm lại
số đã công bố trong sai số làm tròn (bộ dữ liệu, giấy phép, ước lượng công bố và nguyên nhân lệch đã chứng minh:
tools/doi_chung_cong_khai.py).

Đề tài: phân tích thứ cấp bộ dữ liệu cắt ngang công khai (Dryad doi 10.5061/dryad.k3j9kd5bg, CC0) của Mayito và cộng
sự 2023 (PMID 36972254) — tỷ lệ QuantiFERON-TB Gold Plus dương tính (mục tiêu 1) và yếu tố liên quan (mục tiêu 2) ở
người lớn tiếp xúc gần với người bệnh lao phổi tại Kampala. SAP theo đúng phương pháp bài báo (tỷ lệ + KTC 95%; hồi quy
logistic đơn biến từng yếu tố; mô hình đa biến 13 biến), cộng chuẩn của hệ: rào EPV ⇒ Firth theo SAP §5. Hồ sơ vai
(PI, thống kê viên, tác giả, phản biện) chỉ điền từ bài gốc và dữ liệu — không bịa số.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List

MA = "cat_ngang_doi_chung_qft"
_PMID_BAI, _PMID_BIRARO = "36972254", "25372043"
_YEU_TO_DA_BIEN = ["tuoi", "gioi_nam", "hoc_van_thap", "lao_dong_chan_tay", "bmi", "nhieu_ca_nguon",
                   "tiep_xuc_trong_ho", "quan_he_gia_dinh", "cuong_do_cao", "hut_thuoc", "hiv", "seo_bcg"]
_NHAN_YEU_TO = {"gioi_nam": "giới nam", "hoc_van_thap": "học vấn tiểu học trở xuống",
                "lao_dong_chan_tay": "lao động chân tay hoặc không có việc làm", "bmi": "chỉ số khối cơ thể",
                "nhieu_ca_nguon": "tiếp xúc từ 2 ca nguồn trở lên", "tiep_xuc_trong_ho": "tiếp xúc trong hộ gia đình",
                "quan_he_gia_dinh": "quan hệ gia đình với ca nguồn", "cuong_do_cao": "tiếp xúc trên 50% thời gian",
                "cung_nha": "sống cùng nhà với ca nguồn", "hut_thuoc": "đang hút thuốc lá", "hiv": "nhiễm HIV",
                "seo_bcg": "có sẹo BCG"}


def hang_du_lieu_that(kb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Phiếu gốc của kịch bản = bộ dữ liệu công khai đã kiểm SHA-256 (doi_chung_cong_khai.doc_du_lieu); NaN ⇒ None để
    G5 ghi mã thiếu PI đã khai (bien_the.thieu)."""
    import math  # noqa: PLC0415

    import doi_chung_cong_khai as DC  # noqa: PLC0415

    ten = [b[0] for b in kb["bien_so"]["bo_bien"]]
    ra = []
    for r in DC.doc_du_lieu().to_dict("records"):
        h: Dict[str, Any] = {}
        for c in ten:
            v = r[c]
            if isinstance(v, float) and math.isnan(v):
                h[c] = None
            elif c in ("record_id",):
                h[c] = v
            elif c == "bmi":
                h[c] = round(float(v), 5)
            else:
                h[c] = int(v)
        ra.append(h)
    return ra


def kich_ban_doi_chung() -> Dict[str, Dict[str, Any]]:  # noqa: PLR0915 — dữ liệu kịch bản
    import gia_lap_dinh_ky as GL  # noqa: PLC0415 — tránh nhập vòng
    from gia_lap_kich_ban_them import _CC_MI, TRA_LOI_FIRTH, _ky_g2, _sd_khong_ap_dung, _tra_loi_sap  # noqa: PLC0415

    vi = GL._vi
    kb = copy.deepcopy(GL.KICH_BAN["cat_ngang_mo_ta"])
    kb.update(
        study=f"{GL.TIEN_TO_DE_TAI}DOI-CHUNG-QFT", id_test="cross_sectional_doi_chung", goc="cat_ngang_mo_ta",
        mo_ta="Đối chứng công khai — phân tích thứ cấp dữ liệu thật đã công bố (QFT-Plus, Uganda; CC0)",
        topic=("Tỷ lệ nhiễm lao tiềm ẩn chẩn đoán bằng QuantiFERON-TB Gold Plus và yếu tố liên quan ở người lớn tiếp "
               "xúc gần với người bệnh lao phổi tại Kampala, Uganda: phân tích thứ cấp bộ dữ liệu cắt ngang công khai"),
        query_en=('("Interferon-gamma Release Tests"[MeSH] OR QuantiFERON[tiab] OR "interferon gamma release"[tiab]) '
                  'AND ("Contact Tracing"[MeSH] OR contacts[tiab] OR "household contacts"[tiab]) AND '
                  '("Latent Tuberculosis"[MeSH] OR "latent tuberculosis"[tiab] OR "tuberculosis infection"[tiab])'),
        bien_the={"du_lieu_that": "qft_uganda",
                  "thieu": {"ma": "KXD", "nhan": "Không xác định hoặc không đo", "cot": ["qft_duong", "seo_bcg"]}},
    )
    kb.pop("nen_g0_tu", None)
    kb["bien_so"] = {
        "bo_bien": [
            ("record_id", "text", "Mã người tham gia (số thứ tự tuyển của bộ dữ liệu gốc)", "", "", "", ""),
            ("tuoi", "text", "Tuổi (năm)", "", "integer", "18", "90"),
            ("gioi_nam", "radio", "Giới", "1, Nam | 0, Nữ", "", "", ""),
            ("hoc_van_thap", "radio", "Học vấn", "1, Tiểu học trở xuống | 0, Trên tiểu học", "", "", ""),
            ("lao_dong_chan_tay", "radio", "Nghề nghiệp",
             "1, Lao động chân tay hoặc không có việc làm | 0, Việc làm không chân tay", "", "", ""),
            ("bmi", "text", "Chỉ số khối cơ thể (kg/m²)", "", "number", "10", "60"),
            ("nhieu_ca_nguon", "radio", "Số ca bệnh nguồn đã tiếp xúc", "1, Từ 2 ca trở lên | 0, 1 ca", "", "", ""),
            ("tiep_xuc_trong_ho", "radio", "Nơi tiếp xúc với ca nguồn", "1, Trong hộ gia đình | 0, Ngoài hộ gia đình",
             "", "", ""),
            ("quan_he_gia_dinh", "radio", "Quan hệ với ca nguồn", "1, Người trong gia đình | 0, Không phải gia đình",
             "", "", ""),
            ("cuong_do_cao", "radio", "Cường độ tiếp xúc",
             "1, Trên 50% thời gian trong ngày hoặc không hằng ngày | 0, Dưới 50% thời gian trong ngày", "", "", ""),
            ("cung_nha", "radio", "Nơi ở so với ca nguồn", "1, Cùng nhà | 0, Khác nhà", "", "", ""),
            ("hut_thuoc", "radio", "Hút thuốc lá", "1, Đang hút | 0, Không hút", "", "", ""),
            ("hiv", "radio", "Tình trạng HIV", "1, Nhiễm HIV | 0, Không nhiễm HIV", "", "", ""),
            ("seo_bcg", "radio", "Sẹo BCG", "1, Có sẹo | 0, Không có sẹo", "", "", ""),
            ("qft_duong", "radio", "Kết quả QuantiFERON-TB Gold Plus", "1, Dương tính | 0, Âm tính", "", "", ""),
        ],
        "ma_tran": [
            ("1", "Nhiễm lao tiềm ẩn (QuantiFERON-TB Gold Plus dương tính)", "ket_cuc_chinh", "qft_duong", "nhi_phan",
             "C1", "Xét nghiệm QuantiFERON-TB Gold Plus theo quy trình nhà sản xuất", "SAP §4 tỷ lệ + KTC 95%"),
            ("2", "Tuổi", "yeu_to", "tuoi", "lien_tuc", "A1", "Phỏng vấn", "SAP §5 hồi quy logistic"),
            ("2", "Giới", "yeu_to", "gioi_nam", "nhi_phan", "A2", "Phỏng vấn", "SAP §5 hồi quy logistic"),
            ("2", "Học vấn", "yeu_to", "hoc_van_thap", "nhi_phan", "A3", "Phỏng vấn", "SAP §5 hồi quy logistic"),
            ("2", "Nghề nghiệp", "yeu_to", "lao_dong_chan_tay", "nhi_phan", "A4", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Chỉ số khối cơ thể", "yeu_to", "bmi", "lien_tuc", "A5", "Đo cân nặng, chiều cao",
             "SAP §5 hồi quy logistic"),
            ("2", "Số ca bệnh nguồn đã tiếp xúc", "yeu_to", "nhieu_ca_nguon", "nhi_phan", "B1", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Nơi tiếp xúc với ca nguồn", "yeu_to", "tiep_xuc_trong_ho", "nhi_phan", "B2", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Quan hệ với ca nguồn", "yeu_to", "quan_he_gia_dinh", "nhi_phan", "B3", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Cường độ tiếp xúc", "yeu_to", "cuong_do_cao", "nhi_phan", "B4", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Sống cùng nhà với ca nguồn", "phoi_nhiem", "cung_nha", "nhi_phan", "B5", "Phỏng vấn",
             "SAP §5 hồi quy logistic"),
            ("2", "Hút thuốc lá", "yeu_to", "hut_thuoc", "nhi_phan", "A6", "Phỏng vấn", "SAP §5 hồi quy logistic"),
            ("2", "Tình trạng HIV", "yeu_to", "hiv", "nhi_phan", "A7", "Xét nghiệm HIV theo phác đồ quốc gia",
             "SAP §5 hồi quy logistic"),
            ("2", "Sẹo BCG", "yeu_to", "seo_bcg", "nhi_phan", "A8", "Khám", "SAP §5 hồi quy logistic"),
        ],
    }
    kc = {"name": "Tỷ lệ người tiếp xúc có kết quả QuantiFERON-TB Gold Plus dương tính",
          "measure": "QuantiFERON-TB Gold Plus dương tính theo quy trình chuẩn của nhà sản xuất; kết quả không xác "
                     "định loại khỏi mẫu số",
          "timepoint": "Một lần xét nghiệm lúc vào nghiên cứu", "type": "nhị phân"}
    g0 = kb["pi"]["G0"]
    g0.update({
        "population": ("Người từ 18 tuổi tiếp xúc gần với người bệnh lao phổi có xác nhận vi khuẩn, sàng lọc triệu "
                       "chứng lao âm tính và X-quang ngực bình thường"),
        "intervention": ("Không áp dụng — phân tích thứ cấp; yếu tố khảo sát: đặc điểm cá nhân và đặc điểm tiếp xúc "
                         "với ca nguồn"),
        "comparison": "Không áp dụng — nghiên cứu mô tả một nhóm, so sánh theo yếu tố ở mục tiêu 2",
        "outcomes": [kc["name"], "Yếu tố liên quan với QuantiFERON-TB Gold Plus dương tính"],
        "primary_outcome": kc["name"], "primary_outcome_measure": kc["measure"],
        "primary_outcome_timepoint": kc["timepoint"],
        "hypothesis_secondary": vi("Sống cùng nhà, quan hệ gia đình với ca nguồn và các đặc điểm cá nhân (nghề nghiệp, "
                                   "chỉ số khối cơ thể, hút thuốc lá) liên quan với QuantiFERON-TB Gold Plus dương "
                                   "tính (OR khác 1)"),
        "descriptive_justification": vi("Mục tiêu 1 ước lượng tỷ lệ nhiễm lao tiềm ẩn ở người tiếp xúc gần; mục tiêu 2 "
                                        "mô tả yếu tố liên quan, không kiểm định giả thuyết nhân quả"),
        "finer_feasible": vi("Đạt — bộ dữ liệu công khai 202 người đã thu thập và khử định danh"),
        "finer_interesting": vi("Đạt — chọn người cần điều trị dự phòng lao là câu hỏi thực hành"),
        "finer_novel": vi("Đạt có điều kiện — đề tài đối chứng: tái lập kết quả đã công bố để kiểm chứng dây chuyền "
                          "phân tích của hệ"),
        "finer_ethical": vi("Đạt — dữ liệu công khai đã khử định danh, không tiếp xúc người tham gia"),
        "finer_relevant": vi("Đạt — chứng minh hệ tái lập được ước lượng đã công bố trên dữ liệu thật"),
        "novelty_justification": vi(f"Đề tài đối chứng: tái lập kết quả của nghiên cứu gốc (PMID {_PMID_BAI}) trên "
                                    "chính bộ dữ liệu công khai của nghiên cứu đó"),
        "registry_overlap_assessment": vi("Không đăng ký mới — phân tích thứ cấp bộ dữ liệu công khai của nghiên cứu "
                                          "đã công bố"),
    })
    g1 = kb["pi"]["G1"]
    g1.update({
        "design_rationale": vi("Phân tích thứ cấp bộ dữ liệu cắt ngang công khai đã khử định danh (Dryad, giấy phép "
                               "CC0): mục tiêu 1 mô tả tỷ lệ, mục tiêu 2 yếu tố liên quan"),
        # mục tiêu chung PI chốt cho đề tài HAI mục tiêu (G1.aim — khác danh sách mục tiêu cụ thể, như đề tài thật BTM)
        "aim": vi("Mô tả tình trạng nhiễm lao tiềm ẩn và yếu tố liên quan ở người lớn tiếp xúc gần với người bệnh lao "
                  "phổi"),
        "objectives": ["Xác định tỷ lệ QuantiFERON-TB Gold Plus dương tính ở người lớn tiếp xúc gần với người bệnh lao "
                       "phổi", "Xác định một số yếu tố liên quan với QuantiFERON-TB Gold Plus dương tính"],
        "research_question": ("Tỷ lệ người tiếp xúc gần có QuantiFERON-TB Gold Plus dương tính là bao nhiêu và những "
                              "yếu tố nào liên quan?"),
        "primary_outcome": dict(kc),
        "secondary_outcomes": ["Yếu tố liên quan với QuantiFERON-TB Gold Plus dương tính (OR hiệu chỉnh)"],
        "population": g0["population"],
        "inclusion_criteria": ["Tuổi ≥ 18", "Tiếp xúc gần với người bệnh lao phổi có xác nhận vi khuẩn trong 3 tháng "
                               "trước khi ca nguồn điều trị", "Sàng lọc triệu chứng lao âm tính, X-quang ngực bình "
                               "thường"],
        "exclusion_criteria": ["Đã điều trị thuốc lao trước đó"],
        "setting": ("Bộ dữ liệu gốc thu tại Viện Bệnh truyền nhiễm, Bệnh viện Mulago và phòng khám lao của Kampala "
                    "Capital City Authority, Kampala, Uganda"),
        "study_period": "Thu thập gốc 06/2019–06/2020; phân tích thứ cấp 2027",
        "intervention_or_exposure": "Không áp dụng — mô tả đặc điểm cá nhân và đặc điểm tiếp xúc với ca nguồn",
        "comparator": "Không áp dụng",
        "recruitment_strategy": "Toàn bộ 202 người trong bộ dữ liệu công khai (không chọn mẫu lại)",
        "follow_up_schedule": "Không theo dõi — một lần xét nghiệm",
        "estimand": {"population": g0["population"], "treatment_condition": "Không áp dụng (mô tả)",
                     "variable": "QuantiFERON-TB Gold Plus dương tính lúc vào nghiên cứu",
                     "intercurrent_events_strategy": "Không áp dụng (một lần đo)",
                     "population_summary_measure": "Tỷ lệ kèm KTC 95%; OR hiệu chỉnh cho mục tiêu 2"},
        "background_problem": vi("Người tiếp xúc gần với người bệnh lao phổi có nguy cơ nhiễm lao cao; xét nghiệm "
                                 "giải phóng interferon gamma xác định người cần điều trị dự phòng"),
        "evidence_summary": vi(f"Nghiên cứu thuần tập người tiếp xúc hộ gia đình tại Kampala (PMID {_PMID_BIRARO}) ghi "
                               "nhận nhiễm lao tiềm ẩn bằng QuantiFERON-TB Gold In-Tube ở 65% (179/277) người tiếp "
                               "xúc"),
        # STROBE 2: lý do thực hiện là kiểm chứng độc lập kết quả đã công bố (không khẳng định «chưa ai tái lập»)
        "knowledge_gap": vi("Tái lập độc lập các ước lượng của nghiên cứu gốc trên chính bộ dữ liệu đã công bố là cần "
                            "thiết để kiểm chứng kết quả trước khi dùng cho lập kế hoạch dự phòng nhiễm lao tiềm ẩn"),
        "benefit_risk_rationale": vi("Không tiếp xúc người tham gia; dữ liệu công khai đã khử định danh — nguy cơ tối "
                                     "thiểu"),
        "study_schema_timeline": "Tải bộ dữ liệu công khai → kiểm dấu SHA-256 → nhập theo từ điển → khoá → phân tích",
        "intervention_dose_adherence": "N/A — phân tích thứ cấp, không có can thiệp",
        "stopping_rescue_rules": "N/A — không can thiệp, không tiếp xúc người tham gia",
        "critical_to_quality": vi("Dấu SHA-256 của tệp gốc khớp kho dữ liệu; mã hoá biến theo README của tác giả"),
        "monitoring_plan": vi("Đối chiếu nhập kép và đối chiếu bảng đếm với bài gốc"),
        "bias_controls": [
            {"sai_lech": "Sai lệch chọn của bộ dữ liệu gốc (người tiếp xúc tuyển tại phòng khám lao)",
             "bien_phap": "Dùng toàn bộ bộ dữ liệu đã công bố, không lấy mẫu con; nêu rõ quần thể nguồn khi khái quát",
             "chieu": ("Người tiếp xúc đến được phòng khám có thể khác người không đến; chiều lệch của tỷ lệ không "
                       "xác định trước")},
            {"sai_lech": "Sai lệch phân loại do kết quả QuantiFERON không xác định",
             "bien_phap": "Loại kết quả không xác định khỏi mẫu số như bài gốc; báo số người bị loại",
             "chieu": ("Kết quả không xác định thường gặp hơn ở người suy giảm miễn dịch nên tỷ lệ dương tính có thể "
                       "được ước lượng cao hơn thực tế")},
            {"sai_lech": "Nhiễu và quá khớp ở mô hình đa biến 13 biến (6,7 biến cố/biến)",
             "bien_phap": ("Hồi quy logistic có phạt Firth theo SAP §5; mô hình rút gọn đạt EPV ≥ 10 ở phân tích độ "
                           "nhạy"),
             "chieu": "Mô hình không phạt cho OR xa 1 hơn thực tế khi số biến cố/biến thấp"},
        ],
        "sampling_design": ["toan_bo"],
        "data_collection_method": ("Trích bộ dữ liệu công khai đã khử định danh (Dryad doi 10.5061/dryad.k3j9kd5bg, "
                                   "giấy phép CC0) theo từ điển dữ liệu của đề tài"),
    })
    g3 = kb["pi"]["G3"]
    g3.clear()
    g3.update({
        "prevalence": 0.65, "precision": 0.07, "dropout": 0.05, "alpha": 0.05,
        "hypothesis_type": "descriptive_precision",
        "prevalence_source": (f"PMID: {_PMID_BIRARO} (Biraro 2014, PLoS One) — nhiễm lao tiềm ẩn 65% (179/277) ở "
                              "người tiếp xúc hộ gia đình tại Kampala"),
        "dropout_source": vi("Giả định 5% kết quả QuantiFERON không xác định — chưa có nguồn y văn"),
        "confirmed_n": 202,
        "confirmed_n_method": vi("Toàn bộ 202 người của bộ dữ liệu công khai (phân tích thứ cấp, cỡ mẫu cố định)"),
        "effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
        "powered_for_outcome": kc["name"], "recruitment_feasibility_confirmed": True,
        "software": "run_g3_auto.py (ước lượng một tỷ lệ theo độ chính xác)",
    })
    hs = kb["ho_so_tron_vong"]
    hs["G2"] = {"protocol_version": "1.0", "icf_version": "1.0",
                "public_title": "Nhiễm lao tiềm ẩn ở người tiếp xúc gần với người bệnh lao phổi",
                "health_condition": "Nhiễm lao tiềm ẩn (ICD-10 Z22.7)",
                "recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA", "registration_required": False,
                "icf_waiver_requested": True}
    hs["ky_G2"] = _ky_g2("RETROSPECTIVE_SECONDARY_DATA", "NOT_REQUIRED", mien_icf=True)
    da_bien = ("theo đúng bài gốc (PMID " + _PMID_BAI + "): tuổi, giới, học vấn, nghề nghiệp, chỉ số khối cơ thể, số "
               "ca nguồn, nơi tiếp xúc, quan hệ với ca nguồn, cường độ tiếp xúc, sống cùng nhà, hút thuốc lá, HIV, "
               "sẹo BCG (13 biến, đưa vào toàn bộ, không dựng DAG vì mục tiêu là tái lập mô hình đã công bố); phân "
               "tích đơn biến từng yếu tố (OR thô) trước mô hình đa biến")
    hs["tra_loi_G4"] = [(r"bien co hiem", TRA_LOI_FIRTH)] + _tra_loi_sap(
        "Không áp dụng — phân tích thứ cấp, không có can thiệp", da_bien,
        "Kiểm dạng tuyến tính của tuổi và chỉ số khối cơ thể; VIF < 5",
        "Tình trạng HIV (nhiễm/không nhiễm) — ghi trước khi xem dữ liệu",
        "Mô hình rút gọn đạt EPV ≥ 10: tuổi, nghề nghiệp, chỉ số khối cơ thể, quan hệ gia đình, sống cùng nhà, hút "
        "thuốc lá")
    don_bien = [{"id": f"DB_{b}", "vai": "phu", "sap_muc": "§5", "sap_neo": "phân tích đơn biến từng yếu tố",
                 "mo_ta": f"Mục tiêu 2 — phân tích đơn biến: {_NHAN_YEU_TO[b]} (OR thô)",
                 "tham_so": {"outcome": "qft_duong", "group": b, "outcome_type": "binary"}}
                for b in [x for x in _YEU_TO_DA_BIEN if x != "tuoi"] + ["cung_nha"]]
    hs["g6"] = [
        {"id": "MT1_ty_le", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
         "mo_ta": "Tỷ lệ QuantiFERON-TB Gold Plus dương tính + KTC 95%", "tham_so": {"ty_le": ["qft_duong"]}},
        *[{"id": f"NC_hiv_{ten}", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Tình trạng HIV",
           "mo_ta": f"Nhóm nhỏ tiền định: {nhan}", "ke_thua": True, "tham_so": {"loc": f"hiv == {ma}"}}
          for ten, nhan, ma in (("duong", "nhiễm HIV", 1), ("am", "không nhiễm HIV", 0))],
        _CC_MI, _sd_khong_ap_dung("kết cục nhị phân — định nghĩa thay thế chưa khai cụ thể"),
        {"id": "MT2_da_bien", "vai": "phu", "sap_muc": "§5", "sap_neo": "13 biến, đưa vào toàn bộ",
         "mo_ta": "Mục tiêu 2 — mô hình đa biến 13 biến của bài gốc (OR hiệu chỉnh)",
         "tham_so": {"outcome": "qft_duong", "group": "cung_nha", "covariates": list(_YEU_TO_DA_BIEN),
                     "outcome_type": "binary"}},
        *don_bien,
        {"id": "DN_rut_gon", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": "Mô hình rút gọn đạt EPV ≥ 10",
         "mo_ta": "Mô hình rút gọn 6 biến (EPV ≥ 10)",
         "tham_so": {"outcome": "qft_duong", "group": "cung_nha", "outcome_type": "binary",
                     "covariates": ["tuoi", "lao_dong_chan_tay", "bmi", "quan_he_gia_dinh", "hut_thuoc"]}},
    ]
    hs.update(_ho_so_sau_g6())
    return {MA: kb}


def _ho_so_sau_g6() -> Dict[str, Any]:
    from gia_lap_ho_so_sau_g6 import _dac_ta_g10, _dong, _ho_so, _tra_loi_g7  # noqa: PLC0415

    nguon = (f"bài gốc (PMID {_PMID_BAI}; dữ liệu Dryad doi 10.5061/dryad.k3j9kd5bg, CC0)")
    return _ho_so(
        ten_bai="Tỷ lệ nhiễm lao tiềm ẩn và yếu tố liên quan ở người tiếp xúc gần với người bệnh lao phổi",
        thiet_ke="Cắt ngang (phân tích thứ cấp dữ liệu công khai)",
        bang=[
            _dong("QuantiFERON-TB Gold Plus dương tính", "Tỷ lệ % (KTC 95% Wilson)", "ty_le", "G6",
                  "Khoảng một nửa người tiếp xúc gần nhiễm lao tiềm ẩn"),
            _dong("Nhóm nhỏ: nhiễm HIV", "Tỷ lệ %", "ty_le", "G6_NC_hiv_duong", "Mô tả theo nhóm định trước"),
            _dong("Nhóm nhỏ: không nhiễm HIV", "Tỷ lệ %", "ty_le", "G6_NC_hiv_am", "Mô tả theo nhóm định trước"),
            _dong("Sống cùng nhà với ca nguồn (mục tiêu 2)", "OR hiệu chỉnh (Firth, 13 biến)", "or_firth",
                  "G6_MT2_da_bien", "Odds nhiễm lao tiềm ẩn cao hơn khi sống cùng nhà với ca nguồn"),
            _dong("Sống cùng nhà — mô hình rút gọn", "OR hiệu chỉnh (logistic, 6 biến)", "or_hieu_chinh",
                  "G6_DN_rut_gon", "Cùng chiều với mô hình đầy đủ"),
        ],
        muc=(
            ("Tỷ lệ QuantiFERON-TB Gold Plus dương tính là {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%; "
             "{so_su_kien}/{n_ty_le} người có kết quả xác định). Đây là ước lượng mô tả, không kiểm định giả thuyết "
             "nên không có giá trị p. Về ý nghĩa lâm sàng, khoảng một nửa người tiếp xúc gần đã nhiễm lao tiềm ẩn — "
             "nhóm cần cân nhắc điều trị dự phòng."),
            ("Số người dương tính và KTC 95% trùng " + nguon + ". Tỷ lệ thấp hơn mức 65% ở người tiếp xúc hộ gia đình "
             f"tại Kampala (PMID {_PMID_BIRARO}); nghiên cứu đó dùng QuantiFERON-TB Gold In-Tube và gồm cả trẻ em nên "
             "hai con số không so trực tiếp được."),
            ("Điểm mạnh: dữ liệu thật đã công bố, kiểm dấu SHA-256, phân tích theo SAP đã khoá và kiểm chéo SPSS–R. "
             "Hạn chế: mô hình đa biến 13 biến chỉ có 6,7 biến cố/biến nên hệ dùng hồi quy Firth thay cho hồi quy "
             "logistic thường của bài gốc; tệp nộp kho là bản sửa, bảng đếm của nơi tiếp xúc và sống cùng nhà khác bài "
             "gốc; thiết kế cắt ngang không cho biết chiều thời gian. Loại kết quả QuantiFERON không xác định (hay gặp "
             "ở người suy giảm miễn dịch) gây sai lệch phân loại có thể làm tỷ lệ được ước lượng cao hơn thực tế; sai "
             "lệch chọn của bộ dữ liệu gốc (người tiếp xúc đến được phòng khám lao) có chiều không xác định trước. Kết "
             "quả khái quát cho người tiếp xúc gần đến phòng khám lao ở bối cảnh gánh nặng lao cao."),
            ("Hàm ý cho thực hành: người tiếp xúc gần, nhất là sống cùng nhà và có quan hệ gia đình với ca nguồn, nên "
             "được xét nghiệm nhiễm lao tiềm ẩn. Hướng tiếp: nghiên cứu theo dõi dọc chuyển sang lao hoạt động ở người "
             "dương tính."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n_ty_le} người tiếp xúc gần có kết quả xác định, {so_su_kien} người có QuantiFERON-TB "
                     "Gold Plus dương tính: tỷ lệ {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%)."),
            ket_luan=("Khoảng một nửa người lớn tiếp xúc gần với người bệnh lao phổi nhiễm lao tiềm ẩn; sống cùng nhà "
                      "và quan hệ gia đình với ca nguồn đi kèm odds nhiễm cao hơn."),
            ket_cuc_phu=("Yếu tố liên quan (mục tiêu 2) trình bày ở bảng phân tích đơn biến và mô hình đa biến theo "
                         "SAP §5"),
            du_lieu_thieu=("Mười người có kết quả QuantiFERON không xác định bị loại khỏi mẫu số như bài gốc; không "
                           "gán đa trị kết cục (khớp SAP §6)"),
            # cắt ngang: nêu cơ chế hợp lý, không khẳng định nhân quả (STROBE 20 — tieu_chi_ban_thao.CAU_NHAN_QUA)
            giai_thich=("Tiếp xúc gần và kéo dài đi kèm mức phơi nhiễm cao hơn với vi khuẩn lao lây qua đường hô hấp "
                        "— cơ chế hợp lý cho mối liên quan quan sát được; thiết kế cắt ngang không cho phép kết luận "
                        "nhân quả"),
            diem_manh="Kết quả được kiểm chéo độc lập bằng SPSS và R, khớp với engine phân tích chính",
            so_sanh=f"Đối chiếu với bài gốc (PMID {_PMID_BAI}) và nghiên cứu tại Kampala (PMID {_PMID_BIRARO})",
            mesh="Latent Tuberculosis; Interferon-gamma Release Tests; Contact Tracing; Cross-Sectional Studies",
        ),
        ly_do=("Tái lập đúng tỷ lệ {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%) của bài gốc trên dữ liệu thật; kiểm "
               "chéo SPSS/R khớp. Cần nêu rõ khác phương pháp ở mô hình đa biến (Firth do EPV thấp)."),
        gop_y=[("Phương pháp — mô hình đa biến", "Nêu số biến cố/biến và lý do dùng Firth (Peduzzi 1996)"),
               ("Kết quả — dữ liệu sửa", "Ghi bảng đếm khác bài gốc của nơi tiếp xúc và sống cùng nhà")],
        cau_hoi=["Cách nhóm cường độ tiếp xúc (mã «không hằng ngày») có theo đúng bài gốc không?",
                 "Kết quả không xác định có liên quan tình trạng HIV không?"],
        checklist=("STROBE (cắt ngang)", "20/22 mục (91%)", "mục 13 (sơ đồ dòng người tham gia), mục 12d"),
        dac_ta=_dac_ta_g10(
            bias_risks="Sai lệch chọn của bộ dữ liệu gốc; sai lệch phân loại do kết quả không xác định",
            bias_controls=("Dùng toàn bộ bộ dữ liệu đã công bố; loại kết quả không xác định như bài gốc; Firth cho EPV "
                           "thấp"),
            timeline="6 tháng: chuẩn bị 1 tháng; nhập và khoá dữ liệu 1 tháng; phân tích 2 tháng; viết 2 tháng",
            literature_review=(f"Nhiễm lao tiềm ẩn ở người tiếp xúc hộ gia đình tại Kampala 65% (PMID {_PMID_BIRARO}); "
                               f"bài gốc của bộ dữ liệu (PMID {_PMID_BAI})"),
            theoretical_framework_not_applicable=("Nghiên cứu dịch tễ mô tả và yếu tố liên quan — không dựa trên khung "
                                                  "lý thuyết"),
            literature_consensus="Tiếp xúc gần với ca nguồn liên quan với nguy cơ nhiễm lao tiềm ẩn cao hơn",
            literature_disagreements="Tỷ lệ khác nhau theo loại xét nghiệm (TST, QuantiFERON) và nhóm tuổi được tuyển",
            summary=("Bối cảnh: người tiếp xúc gần với người bệnh lao phổi có nguy cơ nhiễm lao tiềm ẩn. Mục tiêu: ước "
                     "lượng tỷ lệ QuantiFERON-TB Gold Plus dương tính và yếu tố liên quan. Phương pháp: phân tích thứ "
                     "cấp bộ dữ liệu cắt ngang công khai; tỷ lệ và KTC 95% Wilson; hồi quy logistic."),
            pilot="Không áp dụng — dữ liệu đã thu thập; kiểm thử nhập liệu trên 10 bản ghi đầu",
            safety_plan="Không có can thiệp, không tiếp xúc người tham gia",
            limitations="Phân tích thứ cấp; tệp nộp kho là bản sửa; mô hình đa biến có số biến cố/biến thấp",
            # Ma trận G3 có nguồn «Phỏng vấn» (của nghiên cứu gốc) ⇒ hệ không tự suy công cụ là phiếu trích
            # (quyet_dinh_da_chot); chủ nhiệm (mô phỏng) khai công cụ ở G10 như gia_lap_chan_thuc.
            instrument={"name": ("Phiếu trích dữ liệu từ bộ dữ liệu công khai (Dryad doi 10.5061/dryad.k3j9kd5bg) "
                                 "theo từ điển dữ liệu của đề tài"),
                        "source": (f"biến do nghiên cứu gốc đo (PMID {_PMID_BAI}): QuantiFERON-TB Gold Plus theo "
                                   "quy trình nhà sản xuất, phỏng vấn nhân khẩu học và tiếp xúc, nhân trắc, xét nghiệm "
                                   "HIV"),
                        "note": ("Không có thang đo/PROM nên không cần kiểm định COSMIN; mã hoá biến theo README của "
                                 "tác giả bộ dữ liệu.")},
        ),
    )
