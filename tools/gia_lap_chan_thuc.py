"""Kịch bản CHÂN THỰC cho bộ giả lập trọn vòng (17/11/2026 — bác sĩ: «Giả lập chân thực trên tất cả các đề tài nghiên
cứu để hệ thống hoàn chỉnh có thể thực hiện được tất cả các nghiên cứu y khoa»).

VÌ SAO: 16 kịch bản cũ dùng bộ biến 7–12 trường, một biểu mẫu, mọi câu bắt buộc, không logic nhánh, không sàng lọc —
dữ liệu sinh phẳng (`gia_lap_tron_vong.sinh_du_lieu`). Buổi diễn tập trên khung THẬT của BTM (94 cột, 6 biểu mẫu, calc
đủ tiêu chuẩn, nhánh theo dõi, câu chọn nhiều bắt buộc, hồ sơ sàng lọc trong bộ dữ liệu) lộ 9 lỗi hệ mà 16 kịch bản cũ
không bao giờ chạm tới. Mỗi kịch bản ở đây KẾ THỪA một kịch bản gốc (cùng đề tài, cùng nền G0, cùng quyết định G0/G1/G3)
nhưng thay phiếu bằng phiếu nhiều phần như đề tài thật:
- Phần sàng lọc ghi MỌI người/hồ sơ đã xét (kể cả bị loại) + trường calc «đủ tiêu chuẩn» làm cổng nhánh cho phần sau;
- nhánh theo dõi (mất dấu/rút lui/tử vong) ⇒ kết cục trống đúng nghĩa; câu chọn nhiều bắt buộc; biến cố bất lợi;
- ngày nối tiếp nhau (sàng lọc → ngẫu nhiên → tái khám); dữ liệu sinh BẰNG từ điển G5 của chính đề tài
  (`sinh_du_lieu_redcap`), trích/tuyển tiếp tới khi đủ N của G3; kết cục sinh theo mô hình khớp giả định G3 (nguồn
  PMID ghi ở từng kịch bản gốc).
Mọi số liệu là MÔ PHỎNG — không dùng lâm sàng.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

DU = "[du_tieu_chuan] = '1'"


def _t(ten: str, loai: str, nhan: str, lua: str = "", kt: str = "", lo: str = "", hi: str = "", *, form: str,
       nhanh: str = "", bat_buoc: bool = True, ghi_chu: str = "", phan: str = "") -> Tuple[Tuple[str, ...], Dict]:
    """Một trường: (7 cột bộ biến cũ) + siêu dữ liệu REDCap (biểu mẫu, nhánh, bắt buộc, ghi chú, tiêu đề phần)."""
    return (ten, loai, nhan, lua, kt, lo, hi), {"form": form, "nhanh": nhanh, "bat_buoc": bat_buoc,
                                                 "ghi_chu": ghi_chu, "phan": phan}


def _bo(truong: List[Tuple[Tuple[str, ...], Dict]]) -> Tuple[List[Tuple[str, ...]], Dict[str, Dict]]:
    """(bộ biến 7 cột, siêu dữ liệu) — mỗi trường nhận MÃ CÂU theo phần của phiếu (A1, A2…, B1…): chữ cái đầu của tiêu
    đề phần đang hiệu lực + số thứ tự trong phần, như phiếu thu thập thật."""
    meta: Dict[str, Dict] = {}
    chu, so = "A", 0
    for t, m in truong:
        if m.get("phan"):
            chu, so = m["phan"].strip()[0].upper(), 0
        so += 1
        meta[t[0]] = {**m, "ma_cau": f"{chu}{so}"}
    return [t for t, _m in truong], meta


def _dong_bo_ma_cau(ma_tran: List[tuple], meta: Dict[str, Dict]) -> List[tuple]:
    """Cột «câu hỏi» của ma trận mục tiêu–biến = mã câu của phiếu (bản gốc đánh C1/R1/A1… không theo phần)."""
    return [tuple(d[:5]) + (meta[d[3]]["ma_cau"],) + tuple(d[6:]) if d[3] in meta else tuple(d) for d in ma_tran]


def _ap_loc(kb: Dict[str, Any], loc: str) -> None:
    """Mọi phân tích của đặc tả G6 chỉ trên QUẦN THỂ PHÂN TÍCH (bộ dữ liệu ghi cả người/hồ sơ bị loại ở sàng lọc).

    Phân tích chính và phân tích tự khai tham số ⇒ `loc` = quần thể (AND lọc riêng nếu có). Phân tích KẾ THỪA tham số
    chính mà có lọc riêng (nhóm nhỏ) ⇒ ghép quần thể vào trước, vì bộ giả lập ghép `{**chính, **riêng}` — lọc riêng ghi
    đè lọc quần thể."""
    for pt in kb["ho_so_tron_vong"]["g6"]:
        ts = pt.get("tham_so")
        if not isinstance(ts, dict):
            continue
        if pt.get("vai") == "chinh" or not pt.get("ke_thua") or ts.get("loc"):
            ts["loc"] = f"{loc} and {ts['loc']}" if ts.get("loc") else loc


def _sao(goc: Dict[str, Any], id_test: str, ma_goc: str, mo_ta: str) -> Dict[str, Any]:
    kb = copy.deepcopy(goc)
    kb.update(id_test=id_test, goc=ma_goc, nen_g0_tu=ma_goc, mo_ta=mo_ta)
    return kb


def _dat_bo_bien(kb: Dict[str, Any], truong: List[Tuple[Tuple[str, ...], Dict]], them_ma_tran: List[tuple]) -> None:
    bo, meta = _bo(truong)
    bs = kb["bien_so"]
    bs["bo_bien"], bs["meta_bien"] = bo, meta
    bs["ma_tran"] = _dong_bo_ma_cau(list(bs["ma_tran"]) + list(them_ma_tran), meta)


def _calc_du(dieu_kien: List[str]) -> str:
    return "if(" + " and ".join(dieu_kien) + ", 1, 0)"


# ══ RCT — tin nhắn nhắc uống thuốc (kế thừa rct_nhi_phan) ══════════════════════════════════════════════════════════
def _rct(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = copy.deepcopy(goc)
    kb.update(id_test="rct_chan_thuc", goc="rct_nhi_phan", nen_g0_tu="rct_nhi_phan",
              mo_ta=("RCT chân thực: sàng lọc + đồng ý, ngẫu nhiên hoá, nền, tái khám tháng 6 có mất dấu, biến cố "
                     "bất lợi"))
    tl = "[theo_doi_t6] = '1'"
    bo, meta = _bo([
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc và đồng ý"),
        _t("ngay_sang_loc", "text", "Ngày sàng lọc", kt="date_dmy", lo="2027-03-01", hi="2027-08-31", form="sang_loc"),
        _t("tc_tuoi18", "yesno", "Tuổi ≥ 18", form="sang_loc"),
        _t("tc_tha_dung_thuoc", "yesno", "Chẩn đoán tăng huyết áp, đang dùng ≥ 1 thuốc hạ áp", form="sang_loc"),
        _t("tc_dien_thoai", "yesno", "Có điện thoại di động nhận được tin nhắn", form="sang_loc"),
        _t("lt_khong_doc_tin", "yesno", "Không đọc được tin nhắn", form="sang_loc"),
        _t("lt_mang_thai", "yesno", "Đang mang thai", form="sang_loc"),
        _t("lt_chuyen_noi", "yesno", "Dự kiến chuyển nơi điều trị trong 6 tháng", form="sang_loc"),
        _t("dong_y", "yesno", "Đồng ý tham gia, đã ký phiếu đồng ý", form="sang_loc",
           nhanh=("[tc_tuoi18] = '1' and [tc_tha_dung_thuoc] = '1' and [tc_dien_thoai] = '1' and "
                  "[lt_khong_doc_tin] = '0' and [lt_mang_thai] = '0' and [lt_chuyen_noi] = '0'")),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn và đồng ý — được ngẫu nhiên hoá (máy tự tính)",
           ("if([tc_tuoi18] = '1' and [tc_tha_dung_thuoc] = '1' and [tc_dien_thoai] = '1' and [lt_khong_doc_tin] = '0' "
            "and [lt_mang_thai] = '0' and [lt_chuyen_noi] = '0' and [dong_y] = '1', 1, 0)"),
           form="sang_loc", bat_buoc=False, ghi_chu="1 = ngẫu nhiên hoá; 0 = không, lý do ở các câu trên"),
        _t("ngay_ngau_nhien", "text", "Ngày ngẫu nhiên hoá", kt="date_dmy", lo="2027-03-01", hi="2027-09-15",
           form="ngau_nhien", nhanh=DU, phan="B. Ngẫu nhiên hoá"),
        _t("nhom", "radio", "Nhóm phân bổ", "1, Tin nhắn SMS | 0, Chăm sóc thường quy", form="ngau_nhien", nhanh=DU),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="18", hi="100", form="nen", nhanh=DU,
           phan="C. Đặc điểm ban đầu"),
        _t("gioi", "radio", "Giới", "1, Nam | 2, Nữ", form="nen", nhanh=DU),
        _t("thoi_gian_tha", "text", "Thời gian mắc tăng huyết áp (năm)", kt="integer", lo="0", hi="60", form="nen",
           nhanh=DU),
        _t("ha_tt_nen", "text", "Huyết áp tâm thu ban đầu, trung bình 2 lần đo (mmHg)", kt="integer", lo="80",
           hi="250", form="nen", nhanh=DU),
        _t("ha_ttr_nen", "text", "Huyết áp tâm trương ban đầu, trung bình 2 lần đo (mmHg)", kt="integer", lo="40",
           hi="150", form="nen", nhanh=DU),
        _t("so_thuoc_nen", "text", "Số thuốc hạ áp đang dùng", kt="integer", lo="1", hi="6", form="nen", nhanh=DU),
        _t("thuoc_nen", "checkbox", "Nhóm thuốc hạ áp đang dùng",
           "1, ACEi hoặc ARB | 2, Chẹn kênh canxi | 3, Lợi tiểu | 4, Chẹn beta | 5, Khác", form="nen", nhanh=DU),
        _t("dtd", "yesno", "Đái tháo đường", form="nen", nhanh=DU),
        _t("hut_thuoc", "radio", "Hút thuốc lá", "1, Đang hút | 2, Đã bỏ | 0, Chưa bao giờ", form="nen", nhanh=DU),
        _t("theo_doi_t6", "radio", "Tình trạng tại tháng 6",
           "1, Đến khám tháng 6 | 2, Mất dấu | 3, Rút khỏi nghiên cứu | 4, Tử vong", form="theo_doi_t6", nhanh=DU,
           phan="D. Tái khám tháng 6"),
        _t("ngay_kham_t6", "text", "Ngày khám tháng 6", kt="date_dmy", lo="2027-08-15", hi="2028-03-31",
           form="theo_doi_t6", nhanh=tl),
        _t("ha_tt_t6", "text", "Huyết áp tâm thu tháng 6, trung bình 2 lần đo (mmHg)", kt="integer", lo="60", hi="260",
           form="theo_doi_t6", nhanh=tl),
        _t("ha_ttr_t6", "text", "Huyết áp tâm trương tháng 6, trung bình 2 lần đo (mmHg)", kt="integer", lo="40",
           hi="150", form="theo_doi_t6", nhanh=tl),
        _t("kiem_soat_t6", "radio", "Kiểm soát huyết áp tháng 6 (< 140/90 mmHg)", "0, Không | 1, Có",
           form="theo_doi_t6", nhanh=tl),
        _t("tuan_thu_t6", "text", "Điểm tuân thủ dùng thuốc tự báo cáo (0–8)", kt="integer", lo="0", hi="8",
           form="theo_doi_t6", nhanh=tl),
        _t("co_bien_co", "yesno", "Có biến cố bất lợi trong 6 tháng", form="bien_co", nhanh=tl,
           phan="E. Biến cố bất lợi"),
        _t("loai_bien_co", "checkbox", "Loại biến cố bất lợi",
           "1, Hạ huyết áp hoặc chóng mặt | 2, Phiền vì tin nhắn | 3, Nhập viện | 4, Khác", form="bien_co",
           nhanh="[co_bien_co] = '1'"),
    ])
    bs = kb["bien_so"]
    bs["bo_bien"], bs["meta_bien"] = bo, meta
    # 22/11/2026: biến tổn hại của RCT gốc (bien_co_*) không có trong bộ biến chân thực — tổn hại ở đây là co_bien_co
    bs["ma_tran"] = _dong_bo_ma_cau([d for d in bs["ma_tran"] if not str(d[3]).startswith("bien_co_")] + [
        ("1", "huyết áp tâm thu ban đầu", "hiep_bien", "ha_tt_nen", "lien_tuc", "", "đo huyết áp chuẩn hoá",
         "SAP §3 mô tả nền"),
        ("1", "đái tháo đường", "hiep_bien", "dtd", "nhi_phan", "", "hồ sơ bệnh án", "SAP §3 mô tả nền"),
        ("1", "tình trạng theo dõi tháng 6", "mo_ta", "theo_doi_t6", "danh_dinh", "", "phiếu tái khám",
         "SAP §6 dữ liệu thiếu"),
        ("1", "biến cố bất lợi", "mo_ta", "co_bien_co", "nhi_phan", "", "phiếu biến cố", "SAP §3 an toàn"),
    ], meta)
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_RCT, "so_ho_so_he_so": 2.5, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# Hình mẫu RCT. Kết cục khớp G3 của kịch bản gốc: p0 = 48%, RR ≈ 1,46 (TEXT4BP, PMID 35342691). Mô hình: HA tâm thu
# tháng 6 = 66 + 0,5 × HA nền − 6,5 × (nhóm SMS) + 3 × (ĐTĐ) + sai số SD 11 ⇒ kiểm soát (< 140/90 mmHg) 41,6% vs 61,0%,
# RR 1,465 (hiệu chỉnh trên 20.000 người mô phỏng — lượt chạy khô 400 người dao động ±0,1 quanh giá trị này).
HINH_MAU_RCT: Dict[str, Any] = {
    "record_id": {"co_dinh": "SMS-{i:03d}"},
    "ngay_sang_loc": {"tu": "2027-03-01", "den": "2027-08-31"},
    "tc_tuoi18": {"p": 0.99}, "tc_tha_dung_thuoc": {"p": 0.95}, "tc_dien_thoai": {"p": 0.9},
    "lt_khong_doc_tin": {"p": 0.04}, "lt_mang_thai": {"p": 0.005}, "lt_chuyen_noi": {"p": 0.03}, "dong_y": {"p": 0.9},
    "ngay_ngau_nhien": {"ngay_sau": ["ngay_sang_loc", 0, 7]},
    "nhom": {"phan_bo": {"1": 0.5, "0": 0.5}},
    "tuoi": {"chuan": (60, 11)}, "gioi": {"phan_bo": {"1": 0.45, "2": 0.55}},
    "thoi_gian_tha": {"lognorm": (7, 1.8)},
    "ha_tt_nen": {"chuan": (150, 14)},
    "ha_ttr_nen": {"tuyen_tinh": {"chan": 30, "he_so": [["ha_tt_nen", 0.4]], "sd": 8}},
    "so_thuoc_nen": {"phan_bo": {"1": 0.35, "2": 0.4, "3": 0.2, "4": 0.05}},
    "thuoc_nen": {"p": {"1": 0.7, "2": 0.6, "3": 0.3, "4": 0.25, "5": 0.05}},
    "dtd": {"p": 0.25}, "hut_thuoc": {"phan_bo": {"1": 0.15, "2": 0.2, "0": 0.65}},
    "theo_doi_t6": {"phan_bo": {"1": 0.85, "2": 0.1, "3": 0.04, "4": 0.01}},
    "ngay_kham_t6": {"ngay_sau": ["ngay_ngau_nhien", 170, 200]},
    "ha_tt_t6": {"tuyen_tinh": {"chan": 66, "he_so": [["ha_tt_nen", 0.5], ["[nhom] = '1'", -6.5], ["[dtd] = '1'", 3]],
                                "sd": 11}},
    "ha_ttr_t6": {"tuyen_tinh": {"chan": 20, "he_so": [["ha_ttr_nen", 0.6], ["[nhom] = '1'", -3]], "sd": 7}},
    "kiem_soat_t6": {"cong_thuc": "if([ha_tt_t6] < 140 and [ha_ttr_t6] < 90, 1, 0)"},
    "tuan_thu_t6": {"tuyen_tinh": {"chan": 5, "he_so": [["[nhom] = '1'", 1.2]], "sd": 1.5}},
    "co_bien_co": {"p": 0.08}, "loai_bien_co": {"p": {"1": 0.5, "2": 0.3, "3": 0.1, "4": 0.2}},
}


# ══ CẮT NGANG — kiểm soát huyết áp (kế thừa cat_ngang_mo_ta) ═════════════════════════════════════════════════════════
def _cat_ngang(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "cross_sectional_chan_thuc", "cat_ngang_mo_ta",
              "Cắt ngang chân thực: sàng lọc + đồng ý, đặc điểm, đo huyết áp 2 lần, kiểm soát suy từ trung bình")
    dong_y = "[tc_tuoi18] = '1' and [tc_tha_3thang] = '1' and [lt_mang_thai] = '0'"
    _dat_bo_bien(kb, [
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc và đồng ý"),
        _t("ngay_kham", "text", "Ngày khám khảo sát", kt="date_dmy", lo="2027-03-01", hi="2027-09-30",
           form="sang_loc"),
        _t("tc_tuoi18", "yesno", "Tuổi ≥ 18", form="sang_loc"),
        _t("tc_tha_3thang", "yesno", "Chẩn đoán tăng huyết áp, điều trị ngoại trú ≥ 3 tháng", form="sang_loc"),
        _t("lt_mang_thai", "yesno", "Đang mang thai", form="sang_loc"),
        _t("dong_y", "yesno", "Đồng ý tham gia", form="sang_loc", nhanh=dong_y),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn và đồng ý — đưa vào khảo sát (máy tự tính)",
           _calc_du([dong_y, "[dong_y] = '1'"]), form="sang_loc", bat_buoc=False),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="18", hi="110", form="dac_diem", nhanh=DU,
           phan="B. Đặc điểm người tham gia"),
        _t("gioi", "radio", "Giới", "1, Nam | 2, Nữ", form="dac_diem", nhanh=DU),
        _t("thoi_gian_tha", "text", "Thời gian mắc tăng huyết áp (năm)", kt="integer", lo="0", hi="60",
           form="dac_diem", nhanh=DU),
        _t("can_nang", "text", "Cân nặng (kg)", kt="number", lo="30", hi="150", form="dac_diem", nhanh=DU),
        _t("chieu_cao", "text", "Chiều cao (cm)", kt="number", lo="130", hi="200", form="dac_diem", nhanh=DU),
        _t("bmi", "calc", "BMI (kg/m², máy tự tính)", "round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)",
           form="dac_diem", nhanh=DU, bat_buoc=False),
        _t("so_thuoc", "text", "Số thuốc hạ áp đang dùng", kt="integer", lo="0", hi="10", form="dac_diem",
           nhanh=DU),
        _t("thuoc_ha_ap", "checkbox", "Nhóm thuốc hạ áp đang dùng",
           "1, ACEi hoặc ARB | 2, Chẹn kênh canxi | 3, Lợi tiểu | 4, Chẹn beta | 5, Khác", form="dac_diem",
           nhanh=DU),
        _t("dtd", "yesno", "Đái tháo đường", form="dac_diem", nhanh=DU),
        _t("benh_than_man", "yesno", "Bệnh thận mạn", form="dac_diem", nhanh=DU),
        _t("thuoc_khac", "text", "Thuốc khác đang dùng, ghi rõ", form="dac_diem", nhanh=DU, bat_buoc=False),
        _t("ha_tt_1", "text", "Huyết áp tâm thu lần 1 (mmHg)", kt="integer", lo="60", hi="260", form="do_huyet_ap",
           nhanh=DU, phan="C. Đo huyết áp (2 lần, cách nhau 1–2 phút)"),
        _t("ha_ttr_1", "text", "Huyết áp tâm trương lần 1 (mmHg)", kt="integer", lo="30", hi="150",
           form="do_huyet_ap", nhanh=DU),
        _t("ha_tt_2", "text", "Huyết áp tâm thu lần 2 (mmHg)", kt="integer", lo="60", hi="260", form="do_huyet_ap",
           nhanh=DU),
        _t("ha_ttr_2", "text", "Huyết áp tâm trương lần 2 (mmHg)", kt="integer", lo="30", hi="150",
           form="do_huyet_ap", nhanh=DU),
        _t("ha_tt_tb", "text", "Huyết áp tâm thu trung bình 2 lần đo (mmHg)", kt="integer", lo="60", hi="260",
           form="do_huyet_ap", nhanh=DU),
        _t("ha_ttr_tb", "text", "Huyết áp tâm trương trung bình 2 lần đo (mmHg)", kt="integer", lo="30", hi="150",
           form="do_huyet_ap", nhanh=DU),
        _t("kiem_soat_ha", "radio", "Đạt kiểm soát huyết áp (< 140/90 mmHg)", "0, Không | 1, Có", form="do_huyet_ap",
           nhanh=DU),
    ], [
        ("1", "đái tháo đường", "mo_ta", "dtd", "nhi_phan", "", "phỏng vấn, hồ sơ", "SAP §3 mô tả"),
        ("1", "huyết áp tâm thu trung bình", "mo_ta", "ha_tt_tb", "lien_tuc", "", "đo huyết áp chuẩn hoá",
         "SAP §3 mô tả"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_CAT_NGANG, "so_ho_so_he_so": 2, "dung_khi": [DU, "N_G3"]}
    # Có câu PHỎNG VẤN ⇒ hệ không tự coi công cụ là phiếu trích hồ sơ; chủ nhiệm (mô phỏng) khai công cụ ở G10.
    kb["ho_so_tron_vong"]["dac_ta_G10"]["instrument"] = {
        "name": "Phiếu phỏng vấn cấu trúc dựng từ bộ biến đã duyệt ở G3 và máy đo huyết áp tự động đã hiệu chuẩn",
        "source": "câu hỏi nhân khẩu học và tiền sử bệnh (không phải thang đo); đo huyết áp theo quy trình chuẩn hoá",
        "note": "Không có thang đo/PROM nên không cần kiểm định COSMIN; máy đo được hiệu chuẩn trước khảo sát.",
    }
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# Tỷ lệ kiểm soát ≈ 45–50% (G3: prevalence giả định 50%). HA tâm thu lần 1 ≈ 112 + 0,35 × tuổi + 2,5 × số thuốc.
HINH_MAU_CAT_NGANG: Dict[str, Any] = {
    "record_id": {"co_dinh": "HA-{i:03d}"}, "ngay_kham": {"tu": "2027-03-01", "den": "2027-09-30"},
    "tc_tuoi18": {"p": 0.99}, "tc_tha_3thang": {"p": 0.95}, "lt_mang_thai": {"p": 0.01}, "dong_y": {"p": 0.93},
    "tuoi": {"chuan": (63, 12)}, "gioi": {"phan_bo": {"1": 0.45, "2": 0.55}},
    "thoi_gian_tha": {"lognorm": (6, 2.0)}, "can_nang": {"chuan": (60, 10)}, "chieu_cao": {"chuan": (158, 8)},
    "so_thuoc": {"phan_bo": {"1": 0.3, "2": 0.4, "3": 0.22, "4": 0.08}},
    "thuoc_ha_ap": {"p": {"1": 0.65, "2": 0.6, "3": 0.3, "4": 0.25, "5": 0.05}},
    "dtd": {"p": 0.28}, "benh_than_man": {"p": 0.12},
    "thuoc_khac": {"chon_chu": ["", "", "", "Statin", "Aspirin liều thấp", "Metformin"]},
    "ha_tt_1": {"tuyen_tinh": {"chan": 112, "he_so": [["tuoi", 0.35], ["so_thuoc", 2.5]], "sd": 14}},
    "ha_ttr_1": {"tuyen_tinh": {"chan": 45, "he_so": [["ha_tt_1", 0.3]], "sd": 7}},
    "ha_tt_2": {"tuyen_tinh": {"chan": -2, "he_so": [["ha_tt_1", 1.0]], "sd": 5}},
    "ha_ttr_2": {"tuyen_tinh": {"chan": -1, "he_so": [["ha_ttr_1", 1.0]], "sd": 4}},
    "ha_tt_tb": {"cong_thuc": "([ha_tt_1] + [ha_tt_2]) / 2", "lam_tron": 0},
    "ha_ttr_tb": {"cong_thuc": "([ha_ttr_1] + [ha_ttr_2]) / 2", "lam_tron": 0},
    "kiem_soat_ha": {"cong_thuc": "if([ha_tt_tb] < 140 and [ha_ttr_tb] < 90, 1, 0)"},
}


# ══ THUẦN TẬP — PPI kéo dài và gãy xương (kế thừa thuan_tap_phoi_nhiem, hồi cứu hồ sơ) ══════════════════════════════
def _thuan_tap(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "cohort_chan_thuc", "thuan_tap_phoi_nhiem",
              "Thuần tập hồi cứu chân thực: sàng lọc hồ sơ, nền, phơi nhiễm, theo dõi tới gãy xương/tử vong/mất dấu/"
              "3 năm")
    mo = "[ho_so_mo_duoc] = '1'"
    _dat_bo_bien(kb, [
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc hồ sơ"),
        _t("ho_so_mo_duoc", "yesno", "Mở được hồ sơ bệnh án điện tử", form="sang_loc"),
        _t("tc_tuoi60", "yesno", "Tuổi ≥ 60 tại ngày bắt đầu theo dõi", form="sang_loc", nhanh=mo),
        _t("tc_2luot", "yesno", "≥ 2 lần khám ngoại trú trong 12 tháng trước ngày bắt đầu", form="sang_loc", nhanh=mo),
        _t("lt_gay_xuong_12t", "yesno", "Gãy xương trong 12 tháng trước ngày bắt đầu", form="sang_loc", nhanh=mo),
        _t("lt_ung_thu_xuong", "yesno", "Ung thư di căn xương hoặc đa u tuỷ", form="sang_loc", nhanh=mo),
        _t("lt_theo_doi_ngan", "yesno", "Hồ sơ theo dõi dưới 6 tháng", form="sang_loc", nhanh=mo),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn — đưa vào thuần tập (máy tự tính)",
           _calc_du([mo, "[tc_tuoi60] = '1'", "[tc_2luot] = '1'", "[lt_gay_xuong_12t] = '0'",
                     "[lt_ung_thu_xuong] = '0'", "[lt_theo_doi_ngan] = '0'"]), form="sang_loc", bat_buoc=False),
        _t("ngay_bat_dau", "text", "Ngày bắt đầu theo dõi", kt="date_dmy", lo="2020-01-01", hi="2022-12-31",
           form="nen", nhanh=DU, phan="B. Đặc điểm nền"),
        _t("tuoi", "text", "Tuổi tại ngày bắt đầu theo dõi (năm)", kt="integer", lo="60", hi="110", form="nen",
           nhanh=DU),
        _t("gioi", "radio", "Giới", "0, Nữ | 1, Nam", form="nen", nhanh=DU),
        _t("corticoid", "yesno", "Dùng corticoid toàn thân ≥ 3 tháng", form="nen", nhanh=DU),
        _t("loang_xuong", "yesno", "Chẩn đoán loãng xương trước ngày bắt đầu", form="nen", nhanh=DU),
        _t("thuoc_loang_xuong", "checkbox", "Thuốc dự phòng/điều trị loãng xương",
           "1, Bisphosphonate | 2, Canxi hoặc vitamin D | 3, Khác | 0, Không dùng thuốc nào", form="nen", nhanh=DU),
        _t("nga_12t", "yesno", "Ngã trong 12 tháng trước ngày bắt đầu", form="nen", nhanh=DU),
        _t("ppi_dai_han", "radio", "Dùng PPI liên tục ≥ 12 tháng (PHƠI NHIỄM)", "0, Không | 1, Có", form="phoi_nhiem",
           nhanh=DU, phan="C. Phơi nhiễm"),
        _t("loai_ppi", "checkbox", "Loại PPI đã dùng",
           "1, Omeprazol | 2, Esomeprazol | 3, Pantoprazol | 4, Lansoprazol hoặc rabeprazol", form="phoi_nhiem",
           nhanh="[ppi_dai_han] = '1'"),
        _t("thoi_gian_theo_doi", "text", "Thời gian theo dõi (tháng)", kt="integer", lo="1", hi="36",
           form="theo_doi", nhanh=DU, phan="D. Theo dõi"),
        _t("trang_thai_ket_thuc", "radio", "Lý do kết thúc theo dõi",
           "1, Gãy xương | 2, Tử vong | 3, Chuyển nơi điều trị hoặc mất dấu | 4, Đủ 3 năm theo dõi", form="theo_doi",
           nhanh=DU),
        _t("ngay_ket_thuc", "text", "Ngày kết thúc theo dõi", kt="date_dmy", lo="2020-01-01", hi="2025-12-31",
           form="theo_doi", nhanh=DU),
        _t("vi_tri_gay", "checkbox", "Vị trí gãy xương", "1, Cổ xương đùi | 2, Đốt sống | 3, Đầu dưới xương quay | "
           "4, Khác", form="theo_doi", nhanh="[trang_thai_ket_thuc] = '1'"),
        _t("gay_xuong_3nam", "radio", "Gãy xương mới trong 3 năm (KẾT CỤC CHÍNH)", "0, Không | 1, Có",
           form="theo_doi", nhanh=DU),
    ], [
        ("1", "lý do kết thúc theo dõi", "mo_ta", "trang_thai_ket_thuc", "danh_dinh", "", "hồ sơ bệnh án",
         "SAP §6 dữ liệu thiếu"),
        ("1", "ngã trong 12 tháng trước", "hiep_bien", "nga_12t", "nhi_phan", "", "hồ sơ bệnh án", "SAP §3 mô tả"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_THUAN_TAP, "so_ho_so_he_so": 1.6, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# Nguy cơ gãy xương mỗi tháng λ = exp(−8,915 + 0,04 × tuổi + 0,3 × PPI + 0,5 × corticoid + 0,6 × loãng xương
# + 0,4 × ngã)
# ⇒ người 71 tuổi không yếu tố nào ≈ 8%/3 năm (G3 p0 8%); HR PPI = e^0,3 ≈ 1,35 (G3 RR 1,33). PPI phụ thuộc corticoid và
# tuổi (gây nhiễu thật). Tử vong 0,3%/tháng, mất dấu 0,4%/tháng, hết 36 tháng ⇒ kiểm duyệt.
HINH_MAU_THUAN_TAP: Dict[str, Any] = {
    "record_id": {"co_dinh": "PPI-{i:04d}"},
    "ho_so_mo_duoc": {"p": 0.97}, "tc_tuoi60": {"p": 0.97}, "tc_2luot": {"p": 0.9}, "lt_gay_xuong_12t": {"p": 0.03},
    "lt_ung_thu_xuong": {"p": 0.01}, "lt_theo_doi_ngan": {"p": 0.04},
    "ngay_bat_dau": {"tu": "2020-01-01", "den": "2022-12-31"},
    "tuoi": {"chuan": (71, 7)}, "gioi": {"phan_bo": {"0": 0.58, "1": 0.42}},
    "corticoid": {"p": 0.1},
    "loang_xuong": {"theo_dieu_kien": [["[gioi] = '0'", {"p": 0.3}], ["", {"p": 0.1}]]},
    "thuoc_loang_xuong": {"p": {"1": 0.12, "2": 0.25, "3": 0.03}, "doc_quyen": "0"},
    "nga_12t": {"p": 0.15},
    "ppi_dai_han": {"logit": {"chan": -1.1, "he_so": [["[corticoid] = '1'", 0.6], ["[tuoi] >= 75", 0.3]]}},
    "loai_ppi": {"p": {"1": 0.6, "2": 0.25, "3": 0.1, "4": 0.08}},
    "thoi_gian_theo_doi": {"song_con": {
        "chan": -8.915, "he_so": [["tuoi", 0.04], ["[ppi_dai_han] = '1'", 0.3], ["[corticoid] = '1'", 0.5],
                                  ["[loang_xuong] = '1'", 0.6], ["[nga_12t] = '1'", 0.4]],
        "toi_da": 36, "tu_vong_moi_thang": 0.003, "mat_dau_moi_thang": 0.004,
        "bien_trang_thai": "trang_thai_ket_thuc", "ma": {"su_kien": 1, "tu_vong": 2, "mat_dau": 3, "het": 4}}},
    "ngay_ket_thuc": {"ngay_cong_thang": ["ngay_bat_dau", "thoi_gian_theo_doi"]},
    "vi_tri_gay": {"p": {"1": 0.3, "2": 0.35, "3": 0.25, "4": 0.15}},
    "gay_xuong_3nam": {"cong_thuc": "if([trang_thai_ket_thuc] = '1', 1, 0)"},
}


# ══ BỆNH–CHỨNG — NSAID và xuất huyết tiêu hoá trên (kế thừa benh_chung) ═════════════════════════════════════════════
def _benh_chung(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "case_control_chan_thuc", "benh_chung",
              "Bệnh–chứng chân thực: sàng lọc ca/chứng, đồng ý, nền, thuốc 30 ngày (chọn nhiều có nhánh)")
    hop_le = ("[tc_tuoi60] = '1' and ([tc_ca_noi_soi] = '1' or [tc_chung_cung_tuan] = '1') and [lt_xo_gan] = '0' "
              "and [lt_ung_thu] = '0' and [lt_khong_nho_thuoc] = '0'")
    _dat_bo_bien(kb, [
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc và đồng ý"),
        _t("ngay_chi_diem", "text", "Ngày chỉ điểm (ngày nhập viện của ca / ngày khám của chứng)", kt="date_dmy",
           lo="2027-03-01", hi="2028-02-29", form="sang_loc"),
        _t("nhom_ca", "radio", "Nhóm (KẾT CỤC CHÍNH: xuất huyết tiêu hoá trên)",
           "0, Chứng | 1, Ca xuất huyết tiêu hoá trên", form="sang_loc"),
        _t("tc_tuoi60", "yesno", "Tuổi ≥ 60", form="sang_loc"),
        _t("tc_ca_noi_soi", "yesno", "Xuất huyết tiêu hoá trên xác nhận qua nội soi", form="sang_loc",
           nhanh="[nhom_ca] = '1'"),
        _t("tc_chung_cung_tuan", "yesno", "Khám ngoại trú trong cùng tuần, không xuất huyết tiêu hoá",
           form="sang_loc", nhanh="[nhom_ca] = '0'"),
        _t("lt_xo_gan", "yesno", "Xơ gan có giãn tĩnh mạch thực quản", form="sang_loc"),
        _t("lt_ung_thu", "yesno", "Ung thư đường tiêu hoá trên", form="sang_loc"),
        _t("lt_khong_nho_thuoc", "yesno", "Không nhớ được thuốc đã dùng và không có hồ sơ đơn thuốc", form="sang_loc"),
        _t("dong_y", "yesno", "Đồng ý tham gia phỏng vấn", form="sang_loc", nhanh=hop_le),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn và đồng ý — đưa vào phân tích (máy tự tính)",
           _calc_du([hop_le, "[dong_y] = '1'"]), form="sang_loc", bat_buoc=False),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="60", hi="110", form="nen", nhanh=DU,
           phan="B. Đặc điểm nền"),
        _t("gioi", "radio", "Giới", "0, Nữ | 1, Nam", form="nen", nhanh=DU),
        _t("hut_thuoc", "radio", "Hút thuốc lá", "1, Đang hút | 2, Đã bỏ | 0, Chưa bao giờ", form="nen", nhanh=DU),
        _t("ruou_nguy_hai", "yesno", "Uống rượu ở mức nguy hại", form="nen", nhanh=DU),
        _t("h_pylori", "radio", "Nhiễm H. pylori", "1, Dương tính | 0, Âm tính | 9, Chưa xét nghiệm", form="nen",
           nhanh=DU),
        _t("nsaid_30ngay", "radio", "Dùng NSAID trong 30 ngày trước ngày chỉ điểm (PHƠI NHIỄM)", "0, Không | 1, Có",
           form="thuoc", nhanh=DU, phan="C. Thuốc dùng trong 30 ngày trước ngày chỉ điểm"),
        _t("loai_nsaid", "checkbox", "Loại NSAID", "1, Ibuprofen | 2, Diclofenac | 3, Meloxicam | 4, Celecoxib | "
           "5, Khác", form="thuoc", nhanh="[nsaid_30ngay] = '1'"),
        _t("chong_dong", "yesno", "Dùng thuốc chống đông/chống kết tập", form="thuoc", nhanh=DU),
        _t("loai_chong_dong", "checkbox", "Loại thuốc chống đông/chống kết tập",
           "1, Aspirin | 2, Clopidogrel | 3, Warfarin | 4, Thuốc chống đông đường uống thế hệ mới", form="thuoc",
           nhanh="[chong_dong] = '1'"),
        _t("ssri", "yesno", "Dùng thuốc chống trầm cảm nhóm SSRI", form="thuoc", nhanh=DU),
        _t("corticoid", "yesno", "Dùng corticoid toàn thân", form="thuoc", nhanh=DU),
        _t("ppi_dang_dung", "yesno", "Đang dùng thuốc ức chế bơm proton", form="thuoc", nhanh=DU),
        _t("tien_su_loet", "yesno", "Tiền sử loét dạ dày–tá tràng", form="thuoc", nhanh=DU),
    ], [
        ("1", "nhiễm H. pylori", "hiep_bien", "h_pylori", "danh_dinh", "", "hồ sơ xét nghiệm", "SAP §3 mô tả"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_BENH_CHUNG, "so_ho_so_he_so": 1.6, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# Phơi nhiễm NSAID ở nhóm chứng 15% (G3 p0); OR = e^0,61 ≈ 1,84 (G3) — độc lập với hiệp biến khi biết nhóm nên OR hiệu
# chỉnh ≈ OR thô. Chống đông và tiền sử loét nhiều hơn ở ca (yếu tố nguy cơ thật). Tỷ số chứng : ca ≈ 2 : 1.
HINH_MAU_BENH_CHUNG: Dict[str, Any] = {
    "record_id": {"co_dinh": "XH-{i:03d}"}, "ngay_chi_diem": {"tu": "2027-03-01", "den": "2028-02-28"},
    "nhom_ca": {"phan_bo": {"1": 0.34, "0": 0.66}},
    "tc_tuoi60": {"p": 0.97}, "tc_ca_noi_soi": {"p": 0.93}, "tc_chung_cung_tuan": {"p": 0.96},
    "lt_xo_gan": {"p": 0.04}, "lt_ung_thu": {"p": 0.02}, "lt_khong_nho_thuoc": {"p": 0.03}, "dong_y": {"p": 0.92},
    "tuoi": {"chuan": (71, 7)}, "gioi": {"phan_bo": {"0": 0.45, "1": 0.55}},
    "hut_thuoc": {"phan_bo": {"1": 0.2, "2": 0.25, "0": 0.55}}, "ruou_nguy_hai": {"p": 0.08},
    "h_pylori": {"phan_bo": {"1": 0.3, "0": 0.35, "9": 0.35}},
    "nsaid_30ngay": {"logit": {"chan": -1.735, "he_so": [["[nhom_ca] = '1'", 0.61]]}},
    "loai_nsaid": {"p": {"1": 0.35, "2": 0.35, "3": 0.2, "4": 0.1, "5": 0.05}},
    "chong_dong": {"logit": {"chan": -1.4, "he_so": [["[nhom_ca] = '1'", 0.7]]}},
    "loai_chong_dong": {"p": {"1": 0.7, "2": 0.25, "3": 0.08, "4": 0.1}},
    "ssri": {"p": 0.05}, "corticoid": {"p": 0.05},
    "ppi_dang_dung": {"logit": {"chan": -1.2, "he_so": [["[nhom_ca] = '1'", -0.4]]}},
    "tien_su_loet": {"logit": {"chan": -2.2, "he_so": [["[nhom_ca] = '1'", 1.1]]}},
}


# ══ CHẨN ĐOÁN — FIB-4 so với đo đàn hồi gan (kế thừa chan_doan) ═════════════════════════════════════════════════════
def _chan_doan(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "diagnostic_chan_thuc", "chan_doan",
              "Chẩn đoán chân thực: sàng lọc, đo đàn hồi (có lượt không hợp lệ), xét nghiệm máu, FIB-4 máy tự tính")
    dong_y = "[tc_tuoi18] = '1' and [tc_gan_nhiem_mo] = '1' and [lt_ruou] = '0' and [lt_viem_gan_virus] = '0'"
    hop_le = "[lsm_hop_le] = '1'"
    _dat_bo_bien(kb, [
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc và đồng ý"),
        _t("ngay_kham", "text", "Ngày khám", kt="date_dmy", lo="2027-03-01", hi="2027-12-31", form="sang_loc"),
        _t("tc_tuoi18", "yesno", "Tuổi ≥ 18", form="sang_loc"),
        _t("tc_gan_nhiem_mo", "yesno", "Gan nhiễm mỡ trên siêu âm kèm ≥ 1 yếu tố chuyển hoá", form="sang_loc"),
        _t("lt_ruou", "yesno", "Uống rượu nguy hại", form="sang_loc"),
        _t("lt_viem_gan_virus", "yesno", "Viêm gan virus B hoặc C đang hoạt động", form="sang_loc"),
        _t("dong_y", "yesno", "Đồng ý tham gia", form="sang_loc", nhanh=dong_y),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn và đồng ý (máy tự tính)", _calc_du([dong_y, "[dong_y] = '1'"]),
           form="sang_loc", bat_buoc=False),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="18", hi="100", form="nen", nhanh=DU,
           phan="B. Đặc điểm nền"),
        _t("gioi", "radio", "Giới", "0, Nữ | 1, Nam", form="nen", nhanh=DU),
        _t("can_nang", "text", "Cân nặng (kg)", kt="number", lo="30", hi="180", form="nen", nhanh=DU),
        _t("chieu_cao", "text", "Chiều cao (cm)", kt="number", lo="130", hi="200", form="nen", nhanh=DU),
        _t("bmi", "calc", "BMI (kg/m², máy tự tính)", "round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)", form="nen",
           nhanh=DU, bat_buoc=False),
        _t("dtd", "yesno", "Đái tháo đường", form="nen", nhanh=DU),
        _t("tha", "yesno", "Tăng huyết áp", form="nen", nhanh=DU),
        _t("lsm_hop_le", "yesno", "Đo đàn hồi hợp lệ (≥ 10 lần đo thành công, IQR/trung vị ≤ 30%)",
           form="dan_hoi", nhanh=DU, phan="C. Đo độ đàn hồi gan (tiêu chuẩn tham chiếu)"),
        _t("lsm_kpa", "text", "Độ đàn hồi gan (kPa)", kt="number", lo="2", hi="75", form="dan_hoi", nhanh=hop_le),
        _t("xo_hoa_tien_trien", "radio", "Xơ hoá tiến triển theo đo đàn hồi ≥ 10 kPa (KẾT CỤC CHÍNH)",
           "0, Không | 1, Có", form="dan_hoi", nhanh=hop_le),
        _t("ast", "text", "AST (U/L)", kt="integer", lo="5", hi="1000", form="xet_nghiem", nhanh=DU,
           phan="D. Xét nghiệm máu (cùng lần khám)"),
        _t("alt", "text", "ALT (U/L)", kt="integer", lo="5", hi="1000", form="xet_nghiem", nhanh=DU),
        _t("tieu_cau", "text", "Tiểu cầu (G/L)", kt="integer", lo="20", hi="800", form="xet_nghiem", nhanh=DU),
        _t("fib4", "calc", "FIB-4 (XÉT NGHIỆM CẦN ĐÁNH GIÁ)", "round(([tuoi]*[ast])/([tieu_cau]*sqrt([alt])),2)",
           form="xet_nghiem", nhanh=DU, bat_buoc=False),
    ], [
        ("1", "đo đàn hồi hợp lệ", "mo_ta", "lsm_hop_le", "nhi_phan", "", "máy đo đàn hồi", "SAP §1 quần thể"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_CHAN_DOAN, "so_ho_so_he_so": 2, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1 and lsm_hop_le == 1")
    return kb


_XN_KHI_KHONG_LSM = {"ast": (39, 14), "alt": (38, 18), "tieu_cau": (223, 58)}  # trung bình chung khi LSM không hợp lệ
# LSM ~ log-chuẩn trung vị 7,8 kPa (≈ 30% ≥10 kPa = G3 prevalence). AST, ALT tăng và tiểu cầu giảm theo LSM ⇒ FIB-4
# phân biệt ở mức AUC ≈ 0,7–0,8 (G3 giả định 0,76).
HINH_MAU_CHAN_DOAN: Dict[str, Any] = {
    "record_id": {"co_dinh": "GAN-{i:03d}"}, "ngay_kham": {"tu": "2027-03-01", "den": "2027-12-31"},
    "tc_tuoi18": {"p": 0.995}, "tc_gan_nhiem_mo": {"p": 0.9}, "lt_ruou": {"p": 0.07},
    "lt_viem_gan_virus": {"p": 0.05}, "dong_y": {"p": 0.92},
    "tuoi": {"chuan": (52, 11)}, "gioi": {"phan_bo": {"0": 0.5, "1": 0.5}},
    "can_nang": {"chuan": (68, 11)}, "chieu_cao": {"chuan": (162, 8)}, "dtd": {"p": 0.3}, "tha": {"p": 0.4},
    "lsm_hop_le": {"p": 0.94}, "lsm_kpa": {"lognorm": (7.8, 1.6)},
    "xo_hoa_tien_trien": {"cong_thuc": "if([lsm_kpa] >= 10, 1, 0)"},
    **{xn: {"theo_dieu_kien": [
        ["[lsm_hop_le] = '1'", {"tuyen_tinh": {"chan": c, "he_so": [["lsm_kpa", h]], "sd": sd}}],
        ["", {"chuan": _XN_KHI_KHONG_LSM[xn]}]]}
       for xn, c, h, sd in (("ast", 25, 1.8, 12), ("alt", 30, 1.0, 18), ("tieu_cau", 262, -5, 55))},
}


# ══ DỰ BÁO — nhập viện 12 tháng ở suy tim ngoại trú (kế thừa mo_hinh_du_bao) ═════════════════════════════════════════
def _du_bao(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "prediction_chan_thuc", "mo_hinh_du_bao",
              "Dự báo chân thực: sàng lọc + đồng ý, yếu tố dự báo, theo dõi 12 tháng có mất dấu, ngày nhập viện")
    dong_y = "[tc_tuoi18] = '1' and [tc_suy_tim] = '1' and [lt_cho_ghep] = '0' and [lt_ky_vong_song] = '0'"
    co_kq = "[theo_doi_12t] = '1'"
    _dat_bo_bien(kb, [
        _t("record_id", "text", "Mã nghiên cứu", form="sang_loc", phan="A. Sàng lọc và đồng ý"),
        _t("ngay_vao_nc", "text", "Ngày vào nghiên cứu", kt="date_dmy", lo="2027-03-01", hi="2028-02-29",
           form="sang_loc"),
        _t("tc_tuoi18", "yesno", "Tuổi ≥ 18", form="sang_loc"),
        _t("tc_suy_tim", "yesno", "Suy tim theo tiêu chuẩn ESC, điều trị ngoại trú ≥ 3 tháng", form="sang_loc"),
        _t("lt_cho_ghep", "yesno", "Đang chờ ghép tim hoặc dùng thiết bị hỗ trợ thất", form="sang_loc"),
        _t("lt_ky_vong_song", "yesno", "Kỳ vọng sống < 12 tháng vì bệnh khác", form="sang_loc"),
        _t("dong_y", "yesno", "Đồng ý tham gia", form="sang_loc", nhanh=dong_y),
        _t("du_tieu_chuan", "calc", "Đủ tiêu chuẩn và đồng ý (máy tự tính)", _calc_du([dong_y, "[dong_y] = '1'"]),
           form="sang_loc", bat_buoc=False),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="18", hi="100", form="du_bao", nhanh=DU,
           phan="B. Yếu tố dự báo lúc vào nghiên cứu"),
        _t("gioi", "radio", "Giới", "0, Nữ | 1, Nam", form="du_bao", nhanh=DU),
        _t("lvef", "text", "Phân suất tống máu thất trái (%)", kt="integer", lo="10", hi="80", form="du_bao",
           nhanh=DU),
        _t("nyha", "radio", "Phân độ NYHA", "1, I | 2, II | 3, III | 4, IV", form="du_bao", nhanh=DU),
        _t("ntprobnp", "text", "NT-proBNP (pg/mL)", kt="number", lo="10", hi="35000", form="du_bao", nhanh=DU),
        _t("egfr", "text", "eGFR (mL/phút/1,73 m²)", kt="integer", lo="5", hi="150", form="du_bao", nhanh=DU),
        _t("natri", "text", "Natri máu (mmol/L)", kt="integer", lo="115", hi="160", form="du_bao", nhanh=DU),
        _t("hb", "text", "Hemoglobin (g/dL)", kt="number", lo="5", hi="20", form="du_bao", nhanh=DU),
        _t("dtd", "yesno", "Đái tháo đường", form="du_bao", nhanh=DU),
        _t("nv_suy_tim_truoc", "yesno", "Nhập viện vì suy tim trong 12 tháng trước", form="du_bao", nhanh=DU),
        _t("thuoc_suy_tim", "checkbox", "Thuốc điều trị suy tim đang dùng",
           "1, ACEi, ARB hoặc ARNI | 2, Chẹn beta | 3, Kháng aldosteron | 4, Ức chế SGLT2 | 5, Lợi tiểu quai",
           form="du_bao", nhanh=DU),
        _t("theo_doi_12t", "radio", "Tình trạng theo dõi", "1, Theo dõi đủ 12 tháng | 2, Mất dấu trước 12 tháng",
           form="theo_doi", nhanh=DU, phan="C. Theo dõi 12 tháng"),
        _t("nhap_vien_12t", "radio", "Nhập viện mọi nguyên nhân trong 12 tháng (KẾT CỤC CHÍNH)", "0, Không | 1, Có",
           form="theo_doi", nhanh=co_kq),
        _t("ngay_nhap_vien_dau", "text", "Ngày nhập viện lần đầu", kt="date_dmy", lo="2027-03-01", hi="2029-03-31",
           form="theo_doi", nhanh="[nhap_vien_12t] = '1'"),
        _t("ly_do_nhap_vien", "radio", "Lý do nhập viện lần đầu", "1, Suy tim | 2, Tim mạch khác | 3, Ngoài tim mạch",
           form="theo_doi", nhanh="[nhap_vien_12t] = '1'"),
    ], [
        ("1", "tình trạng theo dõi 12 tháng", "mo_ta", "theo_doi_12t", "danh_dinh", "", "phiếu theo dõi",
         "SAP §6 dữ liệu thiếu"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_DU_BAO, "so_ho_so_he_so": 1.6, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# Mô hình logistic thật (cùng chiều mô hình của kịch bản gốc), hiệu chỉnh cho tỷ lệ biến cố ≈ 20% (G3 pmsampsize).
HINH_MAU_DU_BAO: Dict[str, Any] = {
    "record_id": {"co_dinh": "ST-{i:04d}"}, "ngay_vao_nc": {"tu": "2027-03-01", "den": "2028-02-28"},
    "tc_tuoi18": {"p": 0.998}, "tc_suy_tim": {"p": 0.95}, "lt_cho_ghep": {"p": 0.01}, "lt_ky_vong_song": {"p": 0.03},
    "dong_y": {"p": 0.93},
    "tuoi": {"chuan": (66, 12)}, "gioi": {"phan_bo": {"0": 0.4, "1": 0.6}}, "lvef": {"chuan": (40, 12)},
    "nyha": {"phan_bo": {"1": 0.15, "2": 0.45, "3": 0.32, "4": 0.08}}, "ntprobnp": {"lognorm": (1500, 2.6)},
    "egfr": {"chuan": (62, 20)}, "natri": {"chuan": (137, 4)}, "hb": {"chuan": (12.8, 1.8)},
    "dtd": {"p": 0.35}, "nv_suy_tim_truoc": {"p": 0.3},
    "thuoc_suy_tim": {"p": {"1": 0.85, "2": 0.8, "3": 0.5, "4": 0.4, "5": 0.6}},
    "theo_doi_12t": {"phan_bo": {"1": 0.95, "2": 0.05}},
    "nhap_vien_12t": {"logit": {"chan": -2.75, "he_so": [["tuoi", 0.03], ["lvef", -0.02], ["ntprobnp", 0.0002],
                                                          ["egfr", -0.01], ["[nv_suy_tim_truoc] = '1'", 0.6]]}},
    "ngay_nhap_vien_dau": {"ngay_sau": ["ngay_vao_nc", 5, 365]},
    "ly_do_nhap_vien": {"phan_bo": {"1": 0.55, "2": 0.2, "3": 0.25}},
}


# ══ TỔNG QUAN GỘP — SGLT2i và nhập viện vì suy tim (kế thừa tong_quan_gop) ═══════════════════════════════════════════
def _tong_quan(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "sr_ma_chan_thuc", "tong_quan_gop",
              "Tổng quan gộp chân thực: phiếu sàng lọc toàn văn (cả bài bị loại + lý do), trích xuất, RoB 2 năm miền")
    vao = ["[tc_rct] = '1'", "[tc_dtd2] = '1'", "[tc_so_sanh] = '1'", "[tc_bao_cao_hhf] = '1'",
           "[lt_chi_suy_tim] = '0'", "[lt_theo_doi_ngan] = '0'", "[lt_khong_tach] = '0'"]
    rob = "1, Thấp | 2, Có lo ngại | 3, Cao"
    mien = [f"[rob_d{k}]" for k in range(1, 6)]
    _dat_bo_bien(kb, [
        _t("study_id", "text", "Mã thử nghiệm (tác giả–năm)", form="sang_loc_toan_van",
           phan="A. Sàng lọc toàn văn (mọi bài đọc toàn văn, kể cả bị loại)"),
        _t("nam_cong_bo", "text", "Năm công bố", kt="integer", lo="2010", hi="2027", form="sang_loc_toan_van"),
        _t("tc_rct", "yesno", "Thử nghiệm ngẫu nhiên có đối chứng", form="sang_loc_toan_van"),
        _t("tc_dtd2", "yesno", "Người trưởng thành ĐTĐ típ 2", form="sang_loc_toan_van"),
        _t("tc_so_sanh", "yesno", "SGLT2i so với giả dược hoặc điều trị chuẩn", form="sang_loc_toan_van"),
        _t("tc_bao_cao_hhf", "yesno", "Báo cáo nhập viện vì suy tim", form="sang_loc_toan_van"),
        _t("lt_chi_suy_tim", "yesno", "Chỉ tuyển người suy tim lúc đầu", form="sang_loc_toan_van"),
        _t("lt_theo_doi_ngan", "yesno", "Theo dõi < 24 tuần", form="sang_loc_toan_van"),
        _t("lt_khong_tach", "yesno", "Không tách được số liệu nhóm không suy tim", form="sang_loc_toan_van"),
        _t("du_tieu_chuan", "calc", "Đưa vào tổng hợp (máy tự tính)", _calc_du(vao), form="sang_loc_toan_van",
           bat_buoc=False),
        _t("thuoc_sglt2", "dropdown", "Thuốc ức chế SGLT2",
           "1, Empagliflozin | 2, Dapagliflozin | 3, Canagliflozin | 4, Ertugliflozin | 5, Khác", form="trich_xuat",
           nhanh=DU, phan="B. Trích xuất (hai người độc lập)"),
        _t("nhanh_chung", "radio", "Nhánh chứng", "1, Giả dược | 2, Điều trị chuẩn", form="trich_xuat", nhanh=DU),
        _t("da_quoc_gia", "yesno", "Thử nghiệm đa quốc gia", form="trich_xuat", nhanh=DU),
        _t("n_can_thiep", "text", "Số người nhánh SGLT2", kt="integer", lo="20", hi="30000", form="trich_xuat",
           nhanh=DU),
        _t("n_chung", "text", "Số người nhánh chứng", kt="integer", lo="20", hi="30000", form="trich_xuat", nhanh=DU),
        _t("bien_co_can_thiep", "text", "Số người nhập viện vì suy tim — nhánh SGLT2", kt="integer", lo="0",
           hi="30000", form="trich_xuat", nhanh=DU),
        _t("bien_co_chung", "text", "Số người nhập viện vì suy tim — nhánh chứng", kt="integer", lo="0", hi="30000",
           form="trich_xuat", nhanh=DU),
        _t("theo_doi_thang", "text", "Thời gian theo dõi trung vị (tháng)", kt="number", lo="3", hi="120",
           form="trich_xuat", nhanh=DU),
        _t("nguon_so_lieu", "checkbox", "Nguồn số liệu", "1, Bài báo chính | 2, Phụ lục | 3, ClinicalTrials.gov | "
           "4, Liên hệ tác giả", form="trich_xuat", nhanh=DU),
        *[_t(f"rob_d{k}", "radio", ten, rob, form="rob2", nhanh=DU, phan="C. Nguy cơ sai lệch RoB 2" if k == 1 else "")
          for k, ten in enumerate(("Miền 1 — quá trình ngẫu nhiên", "Miền 2 — lệch khỏi can thiệp dự kiến",
                                   "Miền 3 — dữ liệu kết cục thiếu", "Miền 4 — đo lường kết cục",
                                   "Miền 5 — chọn kết quả báo cáo"), 1)],
        _t("rob2_tong", "radio", "RoB 2 — đánh giá chung", rob, form="rob2", nhanh=DU),
    ], [
        ("1", "lý do loại toàn văn", "mo_ta", "lt_chi_suy_tim", "nhi_phan", "", "phiếu sàng lọc", "SAP §1 PRISMA"),
    ])
    rob_tong = ("if(" + " or ".join(f"{m} = '3'" for m in mien) + ", 3, if(" + " or ".join(f"{m} = '2'" for m in mien)
                + ", 2, 1))")
    hm = dict(HINH_MAU_TONG_QUAN, rob2_tong={"cong_thuc": rob_tong})
    kb["du_lieu_redcap"] = {"hinh_mau": hm, "so_ho_so": 80, "dung_khi": [DU, 12]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


# 12 thử nghiệm đưa vào; nguy cơ nền nhánh chứng ≈ 3%/thử nghiệm (dao động log SD 0,4); RR thật 0,70 (giảm ~30%
# nhập viện vì suy tim — chiều của các thử nghiệm SGLT2i lớn), dị biệt giữa thử nghiệm τ = 0,1 trên thang log.
_NEN = {"ten": "nguy_co_nen", "bien": "study_id", "sd": 0.4}
HINH_MAU_TONG_QUAN: Dict[str, Any] = {
    "study_id": {"co_dinh": "TV{i:03d}"}, "nam_cong_bo": {"deu": (2015, 2025)},
    "tc_rct": {"p": 0.9}, "tc_dtd2": {"p": 0.92}, "tc_so_sanh": {"p": 0.95}, "tc_bao_cao_hhf": {"p": 0.8},
    "lt_chi_suy_tim": {"p": 0.1}, "lt_theo_doi_ngan": {"p": 0.08}, "lt_khong_tach": {"p": 0.1},
    "thuoc_sglt2": {"phan_bo": {"1": 0.3, "2": 0.3, "3": 0.2, "4": 0.1, "5": 0.1}},
    "nhanh_chung": {"phan_bo": {"1": 0.85, "2": 0.15}}, "da_quoc_gia": {"p": 0.7},
    "n_can_thiep": {"lognorm": (2500, 2.2)},
    "n_chung": {"tuyen_tinh": {"chan": 0, "he_so": [["n_can_thiep", 1.0]], "sd": 30}},
    "bien_co_can_thiep": {"nhi_thuc": {"n": "n_can_thiep", "log_p": {
        "chan": -3.8636, "hieu_ung_cum": [_NEN, {"ten": "di_biet", "bien": "study_id", "sd": 0.1}]}}},
    "bien_co_chung": {"nhi_thuc": {"n": "n_chung", "log_p": {"chan": -3.5066, "hieu_ung_cum": [_NEN]}}},
    "theo_doi_thang": {"lognorm": (30, 1.5)},
    "nguon_so_lieu": {"p": {"1": 0.95, "2": 0.6, "3": 0.3, "4": 0.05}},
    **{f"rob_d{k}": {"phan_bo": {"1": 0.78, "2": 0.18, "3": 0.04}} for k in range(1, 6)},
}


# ══ ĐỊNH TÍNH — trải nghiệm bắt đầu insulin (kế thừa dinh_tinh) ═══════════════════════════════════════════════════════
def _dinh_tinh(goc: Dict[str, Any]) -> Dict[str, Any]:
    kb = _sao(goc, "qualitative_chan_thuc", "dinh_tinh",
              "Định tính chân thực: phiếu tuyển chọn có chủ đích, đặc điểm, nhật ký phỏng vấn, ma trận mã chủ đề")
    _dat_bo_bien(kb, [
        _t("ma_nguoi_tham_gia", "text", "Mã người tham gia", form="tuyen_chon", phan="A. Tuyển chọn có chủ đích"),
        _t("ngay_tiep_can", "text", "Ngày tiếp cận", kt="date_dmy", lo="2027-03-01", hi="2027-08-31",
           form="tuyen_chon"),
        _t("tc_tuoi18", "yesno", "Tuổi ≥ 18", form="tuyen_chon"),
        _t("tc_chi_dinh_insulin", "yesno", "Được chỉ định bắt đầu insulin trong 3 tháng qua", form="tuyen_chon"),
        _t("tc_dong_y_ghi_am", "yesno", "Đồng ý phỏng vấn và ghi âm", form="tuyen_chon"),
        _t("lt_giao_tiep", "yesno", "Suy giảm nhận thức hoặc không giao tiếp được bằng tiếng Việt", form="tuyen_chon"),
        _t("du_tieu_chuan", "calc", "Đưa vào phỏng vấn (máy tự tính)",
           _calc_du(["[tc_tuoi18] = '1'", "[tc_chi_dinh_insulin] = '1'", "[tc_dong_y_ghi_am] = '1'",
                     "[lt_giao_tiep] = '0'"]), form="tuyen_chon", bat_buoc=False),
        _t("tuoi", "text", "Tuổi (năm)", kt="integer", lo="18", hi="100", form="dac_diem", nhanh=DU,
           phan="B. Đặc điểm người tham gia"),
        _t("gioi", "radio", "Giới", "0, Nữ | 1, Nam", form="dac_diem", nhanh=DU),
        _t("hoc_van", "radio", "Trình độ học vấn", "1, Tiểu học | 2, Trung học | 3, Cao đẳng hoặc đại học trở lên",
           form="dac_diem", nhanh=DU),
        _t("thoi_gian_dtd", "text", "Thời gian mắc ĐTĐ (năm)", kt="integer", lo="0", hi="50", form="dac_diem",
           nhanh=DU),
        _t("da_bat_dau_insulin", "yesno", "Đã bắt đầu tiêm insulin", form="dac_diem", nhanh=DU),
        _t("so_tuan_tiem", "text", "Số tuần đã tiêm insulin", kt="integer", lo="0", hi="13", form="dac_diem",
           nhanh="[da_bat_dau_insulin] = '1'"),
        _t("hba1c", "text", "HbA1c gần nhất (%)", kt="number", lo="4", hi="18", form="dac_diem", nhanh=DU),
        _t("transcript_id", "text", "Mã bản gỡ băng (đã khử định danh)", form="phong_van", nhanh=DU,
           phan="C. Phỏng vấn"),
        _t("ngay_phong_van", "text", "Ngày phỏng vấn", kt="date_dmy", lo="2027-03-01", hi="2027-09-30",
           form="phong_van", nhanh=DU),
        _t("thoi_luong_phut", "text", "Thời lượng phỏng vấn (phút)", kt="integer", lo="15", hi="150",
           form="phong_van", nhanh=DU),
        _t("noi_phong_van", "radio", "Nơi phỏng vấn", "1, Phòng khám | 2, Tại nhà | 3, Qua điện thoại",
           form="phong_van", nhanh=DU),
        _t("ma_chu_de", "checkbox", "Mã chủ đề xuất hiện trong phỏng vấn",
           "1, Sợ kim tiêm | 2, Lo hạ đường huyết | 3, Ngại người khác biết | 4, Chi phí và bảo quản | "
           "5, Hỗ trợ của gia đình | 6, Tin tưởng bác sĩ", form="phong_van", nhanh=DU),
        _t("chu_de", "notes", "Chủ đề/mã rút ra từ phỏng vấn (KẾT CỤC CHÍNH)", form="phong_van", nhanh=DU),
    ], [
        ("1", "mã chủ đề xuất hiện", "mo_ta", "ma_chu_de", "danh_dinh", "", "bộ mã", "SAP §3 phân tích chủ đề"),
    ])
    kb["du_lieu_redcap"] = {"hinh_mau": HINH_MAU_DINH_TINH, "so_ho_so": 60, "dung_khi": [DU, "N_G3"]}
    _ap_loc(kb, "du_tieu_chuan == 1")
    return kb


HINH_MAU_DINH_TINH: Dict[str, Any] = {
    "ma_nguoi_tham_gia": {"co_dinh": "PV{i:02d}"}, "ngay_tiep_can": {"tu": "2027-03-01", "den": "2027-08-31"},
    "tc_tuoi18": {"p": 0.99}, "tc_chi_dinh_insulin": {"p": 0.92}, "tc_dong_y_ghi_am": {"p": 0.8},
    "lt_giao_tiep": {"p": 0.04},
    "tuoi": {"chuan": (58, 10)}, "gioi": {"phan_bo": {"0": 0.5, "1": 0.5}},
    "hoc_van": {"phan_bo": {"1": 0.25, "2": 0.5, "3": 0.25}}, "thoi_gian_dtd": {"lognorm": (8, 1.8)},
    "da_bat_dau_insulin": {"p": 0.55}, "so_tuan_tiem": {"deu": (1, 12)}, "hba1c": {"chuan": (9.2, 1.5)},
    "transcript_id": {"co_dinh": "GB{i:02d}"}, "ngay_phong_van": {"ngay_sau": ["ngay_tiep_can", 1, 14]},
    "thoi_luong_phut": {"chuan": (50, 8)}, "noi_phong_van": {"phan_bo": {"1": 0.7, "2": 0.2, "3": 0.1}},
    "ma_chu_de": {"p": {"1": 0.5, "2": 0.6, "3": 0.35, "4": 0.3, "5": 0.45, "6": 0.4}},
    "chu_de": {"chon_chu": ["Sợ kim tiêm; lo phải tiêm suốt đời", "Ngại hạ đường huyết khi đi làm",
                            "Gia đình hỗ trợ học cách tiêm", "Chi phí và việc bảo quản bút tiêm"]},
}


# ══ KIỂM ĐỘ CHÍNH XÁC: hệ phải TÌM LẠI tham số đã dùng để sinh dữ liệu ════════════════════════════════════════════════
# Tham số thật tính ĐỘC LẬP với engine phân tích của hệ: sinh một quần thể lớn bằng CHÍNH mô hình mô phỏng (cùng từ
# điển, cùng hình mẫu) rồi đo ước lượng đích bằng Python thuần. So với ước lượng + KTC 95% hệ báo ở G6: ngoài KTC
# 99,9% ⇒ gần như chắc là lỗi hệ (lọc sai quần thể, mã hoá sai, nhầm nhóm tham chiếu…), không phải do ngẫu nhiên.
def tu_dien_cua(kb: Dict[str, Any]) -> List[Dict[str, str]]:
    import sinh_du_lieu_redcap as SR  # noqa: PLC0415

    bs = kb["bien_so"]
    return [{SR.COT_TEN: t, SR.COT_KIEU: loai, SR.COT_LUA: lc, SR.COT_KIEM: kt, SR.COT_MIN: lo, SR.COT_MAX: hi,
             SR.COT_NHANH: bs["meta_bien"][t]["nhanh"]} for t, loai, _nh, lc, kt, lo, hi in bs["bo_bien"]]


def _quan_the(kb: Dict[str, Any], n: int, seed: int) -> List[Dict[str, Any]]:
    """n bản ghi mô phỏng ĐỦ TIÊU CHUẨN (du_tieu_chuan tính lại như REDCap)."""
    import nhap_lieu_excel as NLE  # noqa: PLC0415
    import sinh_du_lieu_redcap as SR  # noqa: PLC0415

    ct = next(r[3] for r in kb["bien_so"]["bo_bien"] if r[0] == "du_tieu_chuan")
    hm = kb["du_lieu_redcap"]["hinh_mau"]
    ra = []
    for r in SR.sinh(tu_dien_cua(kb), n, hm, seed=seed):
        if NLE.tinh_calc(ct, {k: SR._chuoi(v) for k, v in r.items()}) == "1":
            ra.append(r)
    return ra


def _auc(diem: List[float], nhan: List[int]) -> float:
    """AUC (xác suất một người có bệnh có điểm cao hơn người không bệnh; hoà tính ½) — thống kê Mann–Whitney."""
    cap = sorted(zip(diem, nhan))
    hang, i = [0.0] * len(cap), 0
    while i < len(cap):
        j = i
        while j + 1 < len(cap) and cap[j + 1][0] == cap[i][0]:
            j += 1
        for k in range(i, j + 1):
            hang[k] = (i + j) / 2 + 1
        i = j + 1
    n1 = sum(nh for _d, nh in cap)
    n0 = len(cap) - n1
    return (sum(h for h, (_d, nh) in zip(hang, cap) if nh) - n1 * (n1 + 1) / 2) / (n1 * n0)


def _ty(rows: List[Dict[str, Any]], kc: str) -> float:
    return sum(r[kc] == 1 for r in rows) / len(rows)


def _that_rct(q):
    q = [r for r in q if r["theo_doi_t6"] == 1]
    return _ty([r for r in q if r["nhom"] == 1], "kiem_soat_t6") - _ty([r for r in q if r["nhom"] == 0],
                                                                         "kiem_soat_t6")


def _that_thuan_tap(q):
    return _ty([r for r in q if r["ppi_dai_han"] == 1], "gay_xuong_3nam") - _ty(
        [r for r in q if r["ppi_dai_han"] == 0], "gay_xuong_3nam")


def _that_benh_chung(q):
    ca, chung = [r for r in q if r["nhom_ca"] == 1], [r for r in q if r["nhom_ca"] == 0]
    a, c = _ty(ca, "nsaid_30ngay"), _ty(chung, "nsaid_30ngay")
    return (a / (1 - a)) / (c / (1 - c))


def _that_chan_doan(q):
    q = [r for r in q if r["lsm_hop_le"] == 1]
    fib4 = [round(r["tuoi"] * r["ast"] / (r["tieu_cau"] * r["alt"] ** 0.5), 2) for r in q]
    return _auc(fib4, [r["xo_hoa_tien_trien"] for r in q])


def _that_du_bao(q):
    # Mô hình G6 dùng 4 yếu tố (tuổi, LVEF, NT-proBNP, eGFR) — đích là C của mô hình ĐÚNG trên đúng 4 yếu tố đó.
    q = [r for r in q if r["theo_doi_12t"] == 1]
    lp = [0.03 * r["tuoi"] - 0.02 * r["lvef"] + 0.0002 * r["ntprobnp"] - 0.01 * r["egfr"] for r in q]
    return _auc(lp, [r["nhap_vien_12t"] for r in q])


# ma kịch bản → (khoá ước lượng của bộ giả lập, hàm đích trên quần thể lớn | hằng số, thang log?)
KIEM_CHINH_XAC: Dict[str, Tuple[str, Any, bool]] = {
    "rct_chan_thuc": ("hieu_so_nguy_co", _that_rct, False),
    "cross_sectional_chan_thuc": ("ty_le", lambda q: _ty(q, "kiem_soat_ha"), False),
    "cohort_chan_thuc": ("hieu_so_nguy_co", _that_thuan_tap, False),
    "case_control_chan_thuc": ("or_tho", _that_benh_chung, True),
    "diagnostic_chan_thuc": ("auc", _that_chan_doan, False),
    "prediction_chan_thuc": ("c_statistic", _that_du_bao, False),
    # gộp: log RR mỗi thử nghiệm = ln 0,70 + v (v ~ N(0; 0,1)) ⇒ đích hiệu ứng ngẫu nhiên = exp(E log RR) = 0,70
    "sr_ma_chan_thuc": ("rr_gop", 0.70, True),
}


def tham_so_that(ma: str, n: int = 30000, seed: int = 20261118) -> float:
    """Giá trị đích của kịch bản (hằng số khai sẵn, hoặc đo trên quần thể mô phỏng n bản ghi bằng Python thuần)."""
    _lay, dich, _log = KIEM_CHINH_XAC[ma]
    return float(dich) if not callable(dich) else float(dich(_quan_the(kich_ban_chan_thuc()[ma], n, seed)))


def phan_xet_chinh_xac(that: float, uoc: float, ci: Tuple[float, float], thang_log: bool) -> Dict[str, Any]:
    """DAT (trong KTC 95%) · CANH_BAO (ngoài 95%, trong 99,9% — có thể ngẫu nhiên) · SAI (ngoài 99,9% — nghi lỗi hệ)."""
    import math  # noqa: PLC0415

    f = math.log if thang_log else (lambda x: x)
    u, lo, hi, t = f(uoc), f(ci[0]), f(ci[1]), f(that)
    se = (hi - lo) / (2 * 1.96)
    rong = 3.29 * se
    ket = "DAT" if lo <= t <= hi else ("CANH_BAO" if abs(t - u) <= rong else "SAI")
    return {"ket": ket, "that": round(that, 4), "uoc": round(uoc, 4), "ci_95": [round(ci[0], 4), round(ci[1], 4)],
            "z": round((t - u) / se, 2) if se > 0 else None}


def kich_ban_chan_thuc() -> Dict[str, Dict[str, Any]]:
    import gia_lap_dinh_ky as GL  # noqa: PLC0415 — tránh nhập vòng

    K = GL.KICH_BAN
    return {"rct_chan_thuc": _rct(K["rct_nhi_phan"]),
            "cross_sectional_chan_thuc": _cat_ngang(K["cat_ngang_mo_ta"]),
            "cohort_chan_thuc": _thuan_tap(K["thuan_tap_phoi_nhiem"]),
            "case_control_chan_thuc": _benh_chung(K["benh_chung"]),
            "diagnostic_chan_thuc": _chan_doan(K["chan_doan"]),
            "prediction_chan_thuc": _du_bao(K["mo_hinh_du_bao"]),
            "sr_ma_chan_thuc": _tong_quan(K["tong_quan_gop"]),
            "qualitative_chan_thuc": _dinh_tinh(K["dinh_tinh"])}


def danh_sach() -> List[Tuple[str, str]]:
    """[(mã kịch bản, id test)] — id test ngắn cho pytest/CI."""
    return [(ma, kb["id_test"]) for ma, kb in kich_ban_chan_thuc().items()]
