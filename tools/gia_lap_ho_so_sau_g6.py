"""Hồ sơ vai G6.5 → G10 cho 7 thiết kế ngoài thuần tập của bộ giả lập trọn vòng (16/11/2026).

Bác sĩ giao: «hoàn thiện các đề tài giả lập … sau giả lập hoàn thiện hệ thống». Trước đây chỉ đề tài thuần tập có hồ sơ
của người diễn giải (G6.5), tác giả (G7), người phản biện độc lập (G8) và PI (G10) ⇒ 7 thiết kế còn lại dừng ở G6.

Nguyên tắc (như hồ sơ thuần tập):
- KHÔNG gõ tay con số kết quả: lời văn dùng chỗ giữ {…} mà bộ giả lập điền từ tệp kết quả G6 (`_gia_tri_ket_qua`);
  bảng diễn giải chỉ khai thước đo + cổng, số do bộ giả lập chép từ tệp nguồn.
- Đối chiếu y văn: mỗi thiết kế MỘT–HAI bài đã tra PubMed (metadata + tóm tắt, 16/11/2026); chỉ dùng số có nguyên văn
  trong tóm tắt, ghi rõ tác giả CHƯA đọc toàn văn. Bài đối chiếu khác thiết kế/kết cục với đề tài thì nói rõ.
- Tác giả, người phản biện, PI là VAI mã hoá (không tên thật); mọi văn bản gắn nhãn giả lập.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

TAP_CHI = "Tạp chí Y học Việt Nam"
_DON_VI = ["Phòng khám ngoại trú bệnh viện"]
_NOI_NAM = "TP. Hồ Chí Minh – 2026"
_PHO_BIEN = "Báo cáo tại đơn vị và nộp tạp chí đích"
_KHONG_TV = ("PubMed không có nghiên cứu trong nước cùng câu hỏi; chưa tra tay tạp chí trong nước (giả lập — ghi để "
             "bác sĩ bổ sung)")

# Khai báo dùng AI + thư ngỏ của G8 — chung mọi thiết kế; kết cục chính lấy từ quyết định đã chốt (bộ giả lập đọc G1).
_THAM_SO_G8: Dict[str, Any] = {
    "ai_use_declared": True, "ai_tools": "bộ giả lập trọn vòng của hệ",
    "ai_purpose": "soạn nháp và kiểm dây chuyền; tác giả đọc lại toàn văn",
    "ai_declared_in_cover_letter": True, "ipd_sharing": False,
    **{k: True for k in ("cover_letter_no_duplicate_submission", "cover_letter_coi_declared",
                         "cover_letter_all_authors_approved", "cover_letter_corresponding_contact",
                         "cover_letter_preprint_status")}}


def _dong(ket_cuc: str, thuoc_do: str, lay: str, gate: str, y_nghia: str) -> Dict[str, str]:
    return {"ket_cuc": ket_cuc, "thuoc_do": thuoc_do, "lay": lay, "gate": gate, "y_nghia": y_nghia}


def _tra_loi_g7(*, ket_qua: str, ket_luan: str, ket_cuc_phu: str, du_lieu_thieu: str, giai_thich: str,
                diem_manh: str, so_sanh: str, mesh: str) -> List[Tuple[str, str]]:
    """Ô bản thảo G7 tác giả trả lời — CÙNG bộ mẫu ô như hồ sơ thuần tập; {muc_N} là lời văn bản diễn giải G6.5."""
    return [
        (r"khong dien truoc khi phan tich", ket_qua),
        (r"^conclusions?$|2.3 cau tom tat", ket_luan),
        (r"khong chua ket cuc phu", ket_cuc_phu),
        (r"khong chay gan da tri", du_lieu_thieu),
        (r"dien sau khi co section iii|tom tat phat hien chinh", "{muc_2}"),
        (r"giai thich sinh hoc", giai_thich),
        (r"diem manh khac", diem_manh),
        (r"liet ke han che", "{muc_4}"),
        (r"tac dong voi thuc hanh|khuyen cao", "{muc_5}"),
        (r"phan tich so sanh khi co ket qua", so_sanh),
        (r"mesh terms", mesh),
        (r"dinh dang khi da chon tap chi", "Định dạng theo hướng dẫn tác giả của tạp chí đích"),
        (r"tac gia lien lac", "BS. Nguyễn Văn A — liên hệ qua đơn vị chủ trì"),
        (r"ho ten", "BS. Nguyễn Văn A · ThS. Trần Thị B (thống kê viên)"),
        (r"don vi thu 2", "Không có"),
        (r"icmje form|xem tai lieu 8", "Các tác giả không có xung đột lợi ích liên quan đề tài"),
    ]


def _dac_ta_g10(**rieng: str) -> Dict[str, Any]:
    """Thành phần đề cương MỚI PI khai ở G10 — phần chung + phần riêng từng đề tài."""
    return {"team": "Chủ nhiệm đề tài (BS. Nguyễn Văn A), thống kê viên, quản lý dữ liệu, 2 điều tra viên",
            "budget": "Kinh phí đơn vị cấp cho thu thập và phân tích", "org_lines": _DON_VI,
            "place_year": _NOI_NAM, "dissemination_plan": _PHO_BIEN, "vietnamese_references_not_applicable": _KHONG_TV,
            **rieng}


def _ho_so(*, ten_bai: str, thiet_ke: str, bang: List[Dict[str, str]], muc: Tuple[str, str, str, str],
           tra_loi_g7: List[Tuple[str, str]], ly_do: str, gop_y: List[Tuple[str, str]], cau_hoi: List[str],
           checklist: Tuple[str, str, str], dac_ta: Dict[str, Any]) -> Dict[str, Any]:
    from gia_lap_kich_ban_them import _TAC_GIA_G7  # noqa: PLC0415 — tránh nhập vòng

    return {"dien_giai": {"bang": bang, **{f"muc_{i}": v for i, v in enumerate(muc, 2)}},
            "tac_gia_G7": _TAC_GIA_G7, "tra_loi_G7": tra_loi_g7,
            "phan_bien_G8": {"ten_bai": ten_bai, "thiet_ke": thiet_ke, "ly_do": ly_do, "gop_y_nho": gop_y,
                             "cau_hoi": cau_hoi, "checklist": checklist[0], "checklist_dat": checklist[1],
                             "checklist_thieu": checklist[2]},
            "dac_ta_G10": dac_ta, "tham_so_G8": dict(_THAM_SO_G8)}


_GIOI = "Nhóm nhỏ: {gioi}"
_KC_TRUNG = "chưa đọc toàn văn bài này"


def ho_so_sau_g6() -> Dict[str, Dict[str, Any]]:  # noqa: PLR0915 — dữ liệu hồ sơ, không phải logic
    hs: Dict[str, Dict[str, Any]] = {}

    # ── RCT: tin nhắn nhắc uống thuốc ⇒ kiểm soát huyết áp tháng 6 ───────────────────────────────────────────
    # Thakkar 2016, JAMA Intern Med — gộp 16 RCT: tin nhắn tăng tuân thủ thuốc OR 2,11 (1,52–2,93), I² 62%; kết cục là
    # TUÂN THỦ (đa số tự khai), không phải kiểm soát huyết áp (PMID 26831740).
    hs["rct_nhi_phan"] = _ho_so(
        ten_bai="Tin nhắn nhắc uống thuốc và kiểm soát huyết áp sau 6 tháng",
        thiet_ke="Thử nghiệm ngẫu nhiên có đối chứng, hai nhánh song song",
        bang=[
            _dong("Kiểm soát huyết áp tháng 6", "RR hiệu chỉnh (Poisson, sai số robust)", "pr_hieu_chinh", "G6",
                  "Khả năng đạt kiểm soát cao hơn khoảng {pct1}% so với {pct0}% ở nhóm chứng"),
            _dong("Kiểm soát huyết áp tháng 6", "Hiệu số nguy cơ thô", "hieu_so_nguy_co", "G6",
                  "Cứ khoảng {nnh} người được nhắn tin thì thêm 1 người đạt kiểm soát (NNT)"),
            _dong(_GIOI.format(gioi="nữ"), "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nu", "Thăm dò; cùng chiều chính"),
            _dong(_GIOI.format(gioi="nam"), "RR hiệu chỉnh", "pr_hieu_chinh", "G6_NC_nam", "Thăm dò; KTC rộng hơn"),
            _dong("Độ nhạy: không hiệu chỉnh hiệp biến", "RR", "pr_hieu_chinh", "G6_DN_tho",
                  "Ước lượng thô gần với ước lượng hiệu chỉnh — phù hợp ngẫu nhiên hoá cân bằng"),
        ],
        muc=(
            ("Nhắn tin nhắc uống thuốc đi kèm tỷ lệ kiểm soát huyết áp tháng 6 cao hơn có ý nghĩa thống kê (RR hiệu "
             "chỉnh {rr}; KTC 95% {rr_duoi}–{rr_tren}; p = {p}). Về ý nghĩa lâm sàng, hiệu số tuyệt đối khoảng "
             "{rd_phan_tram} điểm phần trăm ({pct1}% so với {pct0}%), tức cần nhắn tin cho khoảng {nnh} người để thêm "
             "một người đạt kiểm soát. Hai trục được báo tách riêng: ý nghĩa thống kê không đồng nghĩa với độ lớn lâm "
             "sàng."),
            ("Chiều hiệu quả phù hợp với phân tích gộp 16 thử nghiệm của Thakkar và cộng sự (2016): tin nhắn làm tăng "
             "tuân thủ dùng thuốc (OR 2,11; KTC 95% 1,52–2,93; I² 62%) (PMID 26831740). Kết cục của phân tích gộp đó "
             "là tuân thủ, phần lớn tự khai, không phải kiểm soát huyết áp, nên chỉ đối chiếu được chiều tác động; "
             "tác giả " + _KC_TRUNG + "."),
            ("Điểm mạnh: ngẫu nhiên hoá, kết cục đo khách quan tại phòng khám, cỡ mẫu {n} người, phân tích theo SAP "
             "đã khoá và kiểm chéo SPSS–R khớp. Hạn chế: không làm mù người tham gia (bản chất can thiệp) nên không "
             "loại được sai lệch thực hiện, dù kết cục được đo khách quan; một cơ sở, "
             "theo dõi 6 tháng nên chưa biết hiệu quả có duy trì, và kết quả chỉ khái quát cho người tăng huyết áp có "
             "điện thoại nhận tin nhắn."),
            ("Hàm ý cho thực hành: có thể cân nhắc tin nhắn nhắc thuốc như biện pháp bổ trợ chi phí thấp cho người "
             "tăng huyết áp ngoại trú, kèm đánh giá chi phí triển khai. Hướng tiếp: thử nghiệm đa trung tâm theo dõi "
             "≥ 12 tháng, đo tuân thủ khách quan và biến cố tim mạch."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n} người được ngẫu nhiên hoá, nhóm nhắn tin đạt kiểm soát huyết áp tháng 6 nhiều hơn: "
                     "{pct1}% so với {pct0}% (RR hiệu chỉnh {rr}; KTC 95% {rr_duoi}–{rr_tren}); hiệu số "
                     "{rd_phan_tram} điểm phần trăm, NNT khoảng {nnh}."),
            ket_luan=("Ở người tăng huyết áp điều trị ngoại trú, tin nhắn nhắc uống thuốc làm tăng tỷ lệ kiểm soát "
                      "huyết áp sau 6 tháng so với chăm sóc thường quy."),
            ket_cuc_phu=("Kết cục phụ (huyết áp tâm thu trung bình tháng 6; tuân thủ tự khai) chưa phân tích ở đợt này "
                         "— báo cáo riêng theo SAP §2"),
            du_lieu_thieu=("Không có dữ liệu thiếu ở các biến phân tích nên không gán đa trị; phân tích ca đầy đủ là "
                           "phân tích chính (khớp SAP §6)"),
            giai_thich=("Cơ chế giả định là tin nhắn giảm quên liều, tăng tuân thủ dùng thuốc hạ áp; nghiên cứu này "
                        "không đo tuân thủ khách quan"),
            diem_manh="Ngẫu nhiên hoá và kiểm chéo độc lập bằng SPSS và R, khớp với engine phân tích chính",
            so_sanh=("Đối chiếu chi tiết ở đoạn so sánh với phân tích gộp Thakkar 2016 (PMID 26831740); tác giả "
                     + _KC_TRUNG),
            mesh="Hypertension; Text Messaging; Medication Adherence; Randomized Controlled Trial",
        ),
        ly_do=("Ngẫu nhiên hoá, kết cục khách quan và phân tích theo SAP đã khoá; RR hiệu chỉnh {rr} (KTC 95% "
               "{rr_duoi}–{rr_tren}) kiểm chéo SPSS/R khớp. Còn vài điểm trình bày theo CONSORT."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Phương pháp — ngẫu nhiên hoá", "Nêu người tạo và người giữ danh sách ngẫu nhiên (CONSORT 2025 mục "
                                             "10–11)"),
            ("Kết quả — kết cục phụ", "Hai kết cục phụ SAP §2 chưa phân tích; ghi rõ là báo cáo riêng"),
            ("Độ nhạy SAP §9", "Mục định nghĩa thay thế ở SAP §9 chưa khai cụ thể — cần SAP sửa đổi hoặc ghi lý do"),
        ],
        cau_hoi=["Bao nhiêu người mất theo dõi trước tháng 6 ở mỗi nhánh và đã xử lý thế nào?",
                 "Tin nhắn được gửi với tần suất nào và có ghi nhận người tham gia đọc tin không?"],
        checklist=("CONSORT 2025", "27/30 mục (90%)",
                   "mục sơ đồ dòng người tham gia, mục tác hại (biến cố bất lợi do tin nhắn), mục tiếp cận đề cương"),
        dac_ta=_dac_ta_g10(
            bias_risks="Không làm mù người tham gia; nhiễm chéo (nhóm chứng tự cài nhắc thuốc); mất theo dõi",
            bias_controls=("Ngẫu nhiên hoá theo khối, giấu phân bổ; người đo huyết áp không biết nhánh; phân tích "
                           "theo ý định điều trị"),
            timeline=("18 tháng: chuẩn bị, đạo đức, đăng ký 3 tháng; tuyển và can thiệp 9 tháng; phân tích 2 tháng; "
                      "viết và công bố 4 tháng"),
            literature_review=("Phân tích gộp 16 thử nghiệm (Thakkar 2016, PMID 26831740) ghi nhận tin nhắn tăng tuân "
                               "thủ thuốc; dữ liệu về kiểm soát huyết áp ở người Việt Nam ngoại trú còn thiếu"),
            theoretical_framework_not_applicable=("Thử nghiệm hiệu quả can thiệp hành vi đơn giản — không dựa trên "
                                                  "khung lý thuyết hành vi; logic can thiệp mô tả theo TIDieR"),
            literature_consensus="Các thử nghiệm cùng chiều: tin nhắn tăng tuân thủ dùng thuốc ở bệnh mạn",
            literature_disagreements=("Độ lớn tác động khác nhau theo cách đo tuân thủ; ít thử nghiệm đo kết cục "
                                      "lâm sàng như kiểm soát huyết áp"),
            summary=("Bối cảnh: tuân thủ thuốc hạ áp còn thấp. Mục tiêu: so sánh tỷ lệ kiểm soát huyết áp tháng 6 "
                     "giữa nhóm nhận tin nhắn nhắc thuốc và chăm sóc thường quy. Phương pháp: thử nghiệm ngẫu nhiên "
                     "hai nhánh, hồi quy Poisson sai số robust ước lượng RR hiệu chỉnh."),
            pilot="Thử nội dung tin nhắn trên 10 người ngoài mẫu nghiên cứu; chỉnh lời văn trước khi tuyển",
            safety_plan=("Ghi biến cố bất lợi liên quan tin nhắn (phàn nàn, lo âu); người tham gia rút khỏi nghiên "
                         "cứu bất kỳ lúc nào; huyết áp ≥ 180/110 mmHg chuyển khám ngay"),
            limitations=("Một cơ sở; không làm mù người tham gia; theo dõi 6 tháng; chỉ người có điện thoại nhận tin "
                         "nhắn"),
            # SPIRIT 2025 — chi tiết thử nghiệm PI khai ở G10 (chưa có ở cổng nào trước)
            comparator_rationale=("Chăm sóc thường quy là thực hành hiện tại của phòng khám; so sánh trực tiếp cho "
                                  "biết giá trị cộng thêm của tin nhắn (SPIRIT 9b)"),
            concomitant_care_policy=("Mọi điều chỉnh thuốc hạ áp theo bác sĩ điều trị ở cả hai nhánh; không cấm ứng "
                                     "dụng nhắc thuốc khác nhưng ghi nhận khi tái khám (SPIRIT 15d)"),
            randomization_type="Ngẫu nhiên khối hoán vị cỡ 4–6, tỷ lệ 1:1, không phân tầng (SPIRIT 21b)",
            allocation_access_control=("Thống kê viên độc lập sinh và giữ trình tự; người tuyển chỉ mở phong bì kế "
                                       "tiếp sau khi người tham gia ký đồng thuận (SPIRIT 23)"),
            unblinding_procedure=("Người đo huyết áp và thống kê viên được làm mù; mở mù chỉ khi có biến cố cần biết "
                                  "nhánh, do PI quyết định và ghi biên bản (SPIRIT 24c)"),
            ppi_plan=("Hai người bệnh tăng huyết áp góp ý nội dung và tần suất tin nhắn trước khi tuyển; kết quả gửi "
                      "người tham gia bằng tờ tóm tắt (SPIRIT 11)"),
            # 22/11/2026 (chiều, CONSORT 2025 mục 20b): cách làm mù — khớp G1 «người đo huyết áp và thống kê viên được
            # làm mù; người tham gia không làm mù được» và thủ tục mở mù ở trên
            blinding_how=("Tách riêng người gửi tin nhắn và người đo huyết áp; phiếu đo không ghi nhánh; thống kê viên "
                          "nhận dữ liệu với mã nhánh che (A/B) đến khi khoá phân tích; tin nhắn và chăm sóc thường quy "
                          "không thể làm giống nhau nên người tham gia biết nhánh (SPIRIT 24b)"),
        ),
    )

    # ── Cắt ngang mô tả: tỷ lệ kiểm soát huyết áp ─────────────────────────────────────────────────────────────
    # NCD-RisC 2021, Lancet — 2019 toàn cầu: tỷ lệ kiểm soát trong số người tăng huyết áp 23% (nữ, KTC 20–27) và 18%
    # (nam, 16–21); mẫu số là MỌI người tăng huyết áp, kể cả chưa chẩn đoán/chưa điều trị (PMID 34450083).
    hs["cat_ngang_mo_ta"] = _ho_so(
        ten_bai="Tỷ lệ kiểm soát huyết áp ở người tăng huyết áp điều trị ngoại trú",
        thiet_ke="Cắt ngang mô tả",
        bang=[
            _dong("Kiểm soát huyết áp (< 140/90 mmHg)", "Tỷ lệ % (KTC 95% Wilson)", "ty_le", "G6",
                  "Khoảng một nửa người đang điều trị chưa đạt đích"),
            _dong(_GIOI.format(gioi="nam"), "Tỷ lệ %", "ty_le", "G6_NC_nam", "Mô tả theo nhóm định trước"),
            _dong(_GIOI.format(gioi="nữ"), "Tỷ lệ %", "ty_le", "G6_NC_nu", "Mô tả theo nhóm định trước"),
        ],
        muc=(
            ("Tỷ lệ kiểm soát huyết áp là {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%; {so_su_kien}/{n_ty_le} "
             "người). Đây là ước lượng mô tả, không kiểm định giả thuyết nên không có giá trị p. Về ý nghĩa lâm sàng, "
             "khoảng một nửa người đang điều trị ngoại trú chưa đạt đích huyết áp — gánh nặng chưa kiểm soát đủ lớn "
             "để ưu tiên rà soát điều trị."),
            ("Tỷ lệ cao hơn ước tính toàn cầu năm 2019 của NCD-RisC: kiểm soát 23% (nữ) và 18% (nam) trong số người "
             "tăng huyết áp (PMID 34450083). Mẫu số khác nhau: NCD-RisC tính trên mọi người tăng huyết áp kể cả chưa "
             "chẩn đoán, chưa điều trị, còn đề tài này chỉ gồm người đang điều trị ngoại trú, nên hai con số không so "
             "trực tiếp được; tác giả " + _KC_TRUNG + "."),
            ("Điểm mạnh: cỡ mẫu {n} người theo tính toán G3, đo huyết áp chuẩn hoá, phân tích theo SAP đã khoá và "
             "kiểm chéo SPSS–R khớp. Hạn chế: một lần đo tại một thời điểm, lấy mẫu tại một cơ sở nên có thể sai lệch "
             "chọn, không đo tuân thủ thuốc, và thiết kế cắt ngang không cho biết chiều thời gian. Người đến khám đều "
             "đặn thường tuân thủ điều trị tốt hơn, nên sai lệch chọn này có thể làm ước tính cao tỷ lệ kiểm soát so "
             "với toàn bộ người tăng huyết áp của cơ sở. Kết quả khái quát cho người tăng huyết áp đang khám ngoại trú "
             "ở cơ sở có điều kiện tương tự, chưa khái quát cho cộng đồng."),
            ("Hàm ý cho thực hành: rà soát điều trị cho người chưa đạt đích (điều chỉnh liều, phối hợp thuốc, tuân "
             "thủ) là việc có thể làm ngay tại phòng khám. Hướng tiếp: nghiên cứu phân tích yếu tố liên quan và theo "
             "dõi dọc tỷ lệ kiểm soát sau can thiệp."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n_ty_le} người tăng huyết áp điều trị ngoại trú, {so_su_kien} người đạt kiểm soát huyết "
                     "áp: tỷ lệ {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%)."),
            ket_luan=("Khoảng một nửa người tăng huyết áp điều trị ngoại trú đạt kiểm soát huyết áp; cần rà soát điều "
                      "trị cho nhóm chưa đạt đích."),
            # 22/11/2026 (chiều): kết cục phụ ĐÃ CHỐT ở G1 là «Đặc điểm điều trị hạ áp hiện tại» (biến số thuốc hạ áp,
            # có ở Bảng 1) — bản cũ ghi «yếu tố liên quan … chưa phân tích», mâu thuẫn mục tiêu mô tả duy nhất
            ket_cuc_phu=("Đặc điểm điều trị hạ áp hiện tại (số thuốc hạ áp đang dùng) được mô tả ở Bảng 1 theo SAP "
                         "§3"),
            du_lieu_thieu="Không có dữ liệu thiếu ở biến kết cục nên không gán đa trị (khớp SAP §6)",
            giai_thich="Không áp dụng — nghiên cứu mô tả, không đánh giá cơ chế",
            diem_manh="Kết quả được kiểm chéo độc lập bằng SPSS và R, khớp với engine phân tích chính",
            so_sanh="Đối chiếu ở đoạn so sánh với NCD-RisC 2021 (PMID 34450083); tác giả " + _KC_TRUNG,
            mesh="Hypertension; Blood Pressure; Outpatients; Cross-Sectional Studies",
        ),
        ly_do=("Mục tiêu mô tả rõ, cỡ mẫu theo tính toán, tỷ lệ {ty_le}% (KTC 95% {ty_le_duoi}–{ty_le_tren}%) kiểm "
               "chéo SPSS/R khớp. Còn vài điểm trình bày theo STROBE."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Phương pháp — đo huyết áp", "Ghi rõ số lần đo, tư thế và thiết bị (STROBE mục 8)"),
        ],
        cau_hoi=["Người tham gia được chọn liên tiếp hay ngẫu nhiên trong danh sách khám?",
                 "Đích huyết áp < 140/90 mmHg có điều chỉnh cho người cao tuổi hoặc đái tháo đường không?"],
        checklist=("STROBE (cắt ngang)", "20/22 mục (91%)",
                   "mục 12d (cách xử lý chiến lược chọn mẫu), mục 13 (sơ đồ dòng người tham gia)"),
        dac_ta=_dac_ta_g10(
            bias_risks="Sai lệch chọn (một cơ sở, người đến khám thường xuyên hơn); sai số đo huyết áp",
            bias_controls="Chọn liên tiếp theo danh sách khám; đo huyết áp chuẩn hoá hai lần, lấy trung bình",
            timeline=("12 tháng: chuẩn bị và đạo đức 3 tháng; thu thập 4 tháng; phân tích 2 tháng; viết và công bố "
                      "3 tháng"),
            literature_review=("NCD-RisC 2021 (PMID 34450083) ước tính tỷ lệ kiểm soát huyết áp toàn cầu còn thấp; "
                               "số liệu ở người đang điều trị ngoại trú tại Việt Nam còn ít"),
            theoretical_framework_not_applicable=("Nghiên cứu dịch tễ mô tả — không dựa trên khung lý thuyết; mục tiêu "
                                                  "là ước lượng tỷ lệ"),
            literature_consensus=("Tỷ lệ kiểm soát huyết áp ở các nước thu nhập thấp–trung bình thấp hơn ở các "
                                  "nước thu nhập cao (PMID 34450083)"),
            literature_disagreements="Con số khác nhau theo định nghĩa mẫu số (mọi người tăng huyết áp hay người "
                                     "đang điều trị) và đích huyết áp",
            summary=("Bối cảnh: kiểm soát huyết áp ở người điều trị ngoại trú chưa được đo thường quy. Mục tiêu: ước "
                     "lượng tỷ lệ kiểm soát huyết áp. Phương pháp: cắt ngang mô tả, tỷ lệ và KTC 95% Wilson."
                     ),
            pilot="Thử phiếu thu thập trên 15 người ngoài mẫu nghiên cứu",
            safety_plan=("Không có can thiệp; người có huyết áp ≥ 180/110 mmHg khi đo được chuyển khám ngay theo quy "
                         "trình phòng khám"),
            limitations="Một cơ sở; một thời điểm đo; không đo tuân thủ thuốc",
        ),
    )

    # ── Bệnh–chứng: NSAID và xuất huyết tiêu hoá trên ─────────────────────────────────────────────────────────
    # Masclee 2014, Gastroenterology — chuỗi ca tự đối chứng, 7 cơ sở dữ liệu châu Âu: NSAID không chọn lọc đơn trị IRR
    # 4,3 cho xuất huyết tiêu hoá trên (PMID 24937265). Thiết kế khác (không phải bệnh–chứng).
    hs["benh_chung"] = _ho_so(
        ten_bai="NSAID và xuất huyết tiêu hoá trên ở người từ 60 tuổi",
        thiet_ke="Bệnh–chứng",
        bang=[
            _dong("Xuất huyết tiêu hoá trên", "OR hiệu chỉnh (hồi quy logistic)", "or_hieu_chinh", "G6",
                  "Odds phơi nhiễm NSAID ở nhóm bệnh cao hơn nhóm chứng"),
            _dong("Xuất huyết tiêu hoá trên", "OR thô", "or_tho", "G6", "Gần với OR hiệu chỉnh — nhiễu đo được ít"),
            _dong(_GIOI.format(gioi="nữ"), "OR hiệu chỉnh", "or_hieu_chinh", "G6_NC_nu", "Thăm dò"),
            _dong(_GIOI.format(gioi="nam"), "OR hiệu chỉnh", "or_hieu_chinh", "G6_NC_nam", "Thăm dò"),
            _dong("Độ nhạy: loại người dùng chống đông", "OR hiệu chỉnh", "or_hieu_chinh", "G6_DN_khong_chong_dong",
                  "Liên quan còn khi loại nhóm nguy cơ chảy máu cao"),
        ],
        muc=(
            ("Dùng NSAID trong 30 ngày trước đi kèm odds xuất huyết tiêu hoá trên cao hơn có ý nghĩa thống kê (OR "
             "hiệu chỉnh {or_hieu_chinh}; KTC 95% {or_hieu_chinh_duoi}–{or_hieu_chinh_tren}; p = {or_hieu_chinh_p}). "
             "Về ý nghĩa lâm sàng, thiết kế bệnh–chứng không ước lượng được nguy cơ tuyệt đối; với biến cố hiếm, OR "
             "xấp xỉ nguy cơ tương đối nên mức tăng khoảng hai phần ba là đáng kể ở người cao tuổi."),
            ("Chiều liên quan phù hợp với phân tích chuỗi ca tự đối chứng trên 7 cơ sở dữ liệu châu Âu của Masclee và "
             "cộng sự (2014): NSAID không chọn lọc đơn trị đi kèm tỷ suất xuất huyết tiêu hoá trên 4,3 lần (PMID "
             "24937265). Thiết kế và định nghĩa phơi nhiễm khác nhau nên độ lớn không so trực tiếp được; tác giả "
             + _KC_TRUNG + "."),
            ("Điểm mạnh: ca bệnh được xác định bằng nội soi, cỡ mẫu {n} người, phân tích theo SAP đã khoá và kiểm "
             "chéo SPSS–R khớp. Hạn chế: sai lệch nhớ lại về phơi nhiễm, nhiễu tồn dư (rượu, Helicobacter pylori, "
             "aspirin liều thấp), chọn nhóm chứng tại bệnh viện có thể không đại diện, và chỉ khái quát cho người từ "
             "60 tuổi. Sai lệch nhớ lại thường làm ước tính cao mối liên quan vì ca bệnh hay nhớ việc dùng thuốc kỹ "
             "hơn nhóm chứng; nhiễu tồn dư có thể lệch theo cả hai hướng."),
            ("Hàm ý cho thực hành: cân nhắc kỹ chỉ định NSAID ở người cao tuổi, ưu tiên liều thấp nhất trong thời gian "
             "ngắn nhất và bảo vệ dạ dày khi có yếu tố nguy cơ. Hướng tiếp: nghiên cứu thuần tập có đo liều, thời gian "
             "dùng và thuốc phối hợp."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n} người ({su_kien1} ca có phơi nhiễm, {su_kien0} ca không phơi nhiễm), dùng NSAID 30 "
                     "ngày đi kèm odds xuất huyết tiêu hoá trên cao hơn: OR hiệu chỉnh {or_hieu_chinh} (KTC 95% "
                     "{or_hieu_chinh_duoi}–{or_hieu_chinh_tren})."),
            ket_luan=("Ở người từ 60 tuổi, dùng NSAID trong 30 ngày trước liên quan với odds xuất huyết tiêu hoá trên "
                      "cao hơn; cần cân nhắc chỉ định và bảo vệ dạ dày."),
            ket_cuc_phu=("Kết cục phụ (mức độ nặng của xuất huyết) chưa phân tích ở đợt này — báo cáo riêng theo SAP "
                         "§2"),
            du_lieu_thieu=("Không có dữ liệu thiếu ở các biến phân tích nên không gán đa trị; phân tích ca đầy đủ là "
                           "phân tích chính (khớp SAP §6)"),
            giai_thich=("Một giả thuyết được nêu trong y văn là NSAID ức chế prostaglandin bảo vệ niêm mạc dạ dày; "
                        "nghiên cứu này không đánh giá cơ chế"),
            diem_manh="Ca bệnh xác định bằng nội soi; kết quả kiểm chéo độc lập bằng SPSS và R",
            so_sanh="Đối chiếu ở đoạn so sánh với Masclee 2014 (PMID 24937265); tác giả " + _KC_TRUNG,
            mesh="Anti-Inflammatory Agents, Non-Steroidal; Gastrointestinal Hemorrhage; Aged; Case-Control Studies",
        ),
        ly_do=("Định nghĩa ca bằng nội soi, phân tích theo SAP đã khoá; OR hiệu chỉnh {or_hieu_chinh} (KTC 95% "
               "{or_hieu_chinh_duoi}–{or_hieu_chinh_tren}) kiểm chéo SPSS/R khớp. Còn điểm trình bày theo STROBE."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Phương pháp — phơi nhiễm", "Ghi rõ mốc tính cửa sổ 30 ngày ở nhóm chứng (STROBE mục 7)"),
            ("Phương pháp — chọn nhóm chứng", "Ghi rõ tiêu chí và cách bắt cặp nhóm chứng (STROBE mục 6b)"),
        ],
        cau_hoi=["Phơi nhiễm NSAID được xác định từ hồ sơ kê đơn hay phỏng vấn?",
                 "Aspirin liều thấp được xử lý thế nào trong định nghĩa phơi nhiễm?"],
        checklist=("STROBE (bệnh–chứng)", "20/22 mục (91%)",
                   "mục 6b (tiêu chí bắt cặp nhóm chứng), mục 12d (xử lý bắt cặp trong phân tích)"),
        dac_ta=_dac_ta_g10(
            bias_risks="Sai lệch nhớ lại về phơi nhiễm; nhiễu do chỉ định; chọn nhóm chứng không đại diện",
            bias_controls=("Phơi nhiễm lấy từ hồ sơ kê đơn; hiệu chỉnh chống đông và tiền sử loét theo DAG; độ nhạy "
                           "loại người dùng chống đông"),
            timeline=("15 tháng: chuẩn bị và đạo đức 3 tháng; thu thập 6 tháng; phân tích 2 tháng; viết và công bố "
                      "4 tháng"),
            literature_review=("Masclee 2014 (PMID 24937265) ghi nhận NSAID tăng nguy cơ xuất huyết tiêu hoá trên; "
                               "dữ liệu ở người cao tuổi Việt Nam còn ít"),
            theoretical_framework_not_applicable=("Nghiên cứu dịch tễ học quan sát về phơi nhiễm thuốc — mô hình "
                                                  "nhân quả trình bày bằng DAG"),
            literature_consensus="Các nghiên cứu cùng chiều: NSAID tăng nguy cơ xuất huyết tiêu hoá trên",
            literature_disagreements="Độ lớn khác nhau theo loại NSAID, liều và thuốc dùng kèm",
            summary=("Bối cảnh: NSAID dùng phổ biến ở người cao tuổi. Mục tiêu: đánh giá liên quan giữa dùng NSAID "
                     "30 ngày và xuất huyết tiêu hoá trên. Phương pháp: bệnh–chứng, hồi quy logistic ước lượng OR "
                     "hiệu chỉnh."),
            pilot="Thử phiếu trích hồ sơ trên 20 hồ sơ ngoài mẫu nghiên cứu",
            safety_plan="Không có can thiệp; sự cố bảo mật dữ liệu báo cáo theo quy trình đơn vị",
            limitations="Chọn nhóm chứng tại bệnh viện; không đo liều NSAID; nhiễu tồn dư",
            instrument={"name": "Bộ câu hỏi phỏng vấn cấu trúc về thuốc dùng trong 30 ngày, có kèm hình ảnh thuốc, "
                                "đối chiếu hồ sơ kê đơn (soạn cho đề tài)",
                        "source": "Phỏng vấn trực tiếp + hồ sơ bệnh án (ma trận G3)",
                        "note": "Không phải thang đo/PROM — bộ câu hỏi sự kiện dùng thuốc; thử trên 10 người ngoài "
                                "mẫu trước khi thu thập"},
        ),
    )

    # ── Chẩn đoán: FIB-4 phát hiện xơ hoá tiến triển ──────────────────────────────────────────────────────────
    # Shah 2009, Clin Gastroenterol Hepatol — 541 người NAFLD: AUROC FIB-4 0,802 (0,758–0,847); FIB-4 ≥ 2,67 có PPV
    # 80% (PMID 19523535).
    hs["chan_doan"] = _ho_so(
        ten_bai="Giá trị chẩn đoán của FIB-4 phát hiện xơ hoá gan tiến triển",
        thiet_ke="Nghiên cứu độ chính xác chẩn đoán, cắt ngang",
        bang=[
            _dong("Xơ hoá tiến triển", "AUC (Hanley–McNeil)", "auc", "G6", "Khả năng phân biệt thấp"),
            _dong("Xơ hoá tiến triển, ngưỡng {nguong}", "Độ nhạy (Wilson)", "do_nhay", "G6",
                  "Bỏ sót phần lớn người có xơ hoá tiến triển ở ngưỡng này"),
            _dong("Xơ hoá tiến triển, ngưỡng {nguong}", "Độ đặc hiệu (Wilson)", "do_dac_hieu", "G6",
                  "Đa số người không xơ hoá có FIB-4 dưới ngưỡng"),
            _dong("Độ nhạy: loại ALT > 200 U/L", "AUC", "auc", "G6_DN_alt", "So với AUC phân tích chính"),
        ],
        muc=(
            ("AUC của FIB-4 là {auc} (KTC 95% {auc_duoi}–{auc_tren}); tại ngưỡng {nguong}, độ nhạy {do_nhay} "
             "({do_nhay_duoi}–{do_nhay_tren}) và độ đặc hiệu {do_dac_hieu} ({do_dac_hieu_duoi}–{do_dac_hieu_tren}); "
             "LR+ {lr_duong}, LR− {lr_am}. Đây là ước lượng độ chính xác, không kiểm định giả thuyết. Về ý nghĩa lâm "
             "sàng, ở ngưỡng {nguong} FIB-4 bỏ sót phần lớn người có xơ hoá tiến triển ({so_fn} âm tính giả so "
             "với {so_tp} dương tính thật) nên không dùng một mình để loại trừ."),
            ("Kết quả thấp hơn nghiên cứu gốc của Shah và cộng sự (2009) trên 541 người NAFLD: AUROC 0,802 (KTC 95% "
             "0,758–0,847), FIB-4 ≥ 2,67 có giá trị dự đoán dương 80% (PMID 19523535). Cỡ mẫu đề tài nhỏ ({n} người) "
             "nên KTC rộng, và quần thể khác (ngoại trú, gan nhiễm mỡ liên quan chuyển hoá); tác giả " + _KC_TRUNG
             + "."),
            ("Điểm mạnh: chuẩn tham chiếu đo trên mọi người tham gia, ngưỡng định trước trong SAP, kiểm chéo SPSS–R "
             "khớp. Hạn chế: cỡ mẫu {n} người với {so_tp} + {so_fn} người có bệnh nên KTC rộng, một cơ sở, chưa đánh "
             "giá ngưỡng thứ hai 1,3 (SAP §5), và phổ bệnh tại cơ sở khám có thể khác cộng đồng, nên khả năng khái "
             "quát cho sàng lọc cộng đồng còn hạn chế."),
            ("Hàm ý cho thực hành: tại ngưỡng {nguong}, FIB-4 không đủ để loại trừ xơ hoá tiến triển; nên phối hợp "
             "ngưỡng thấp và đo độ đàn hồi gan theo hướng dẫn hiện hành. Hướng tiếp: nghiên cứu cỡ mẫu lớn hơn, đánh "
             "giá chiến lược hai ngưỡng."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n} người, AUC của FIB-4 là {auc} (KTC 95% {auc_duoi}–{auc_tren}); tại ngưỡng {nguong} độ "
                     "nhạy {do_nhay} và độ đặc hiệu {do_dac_hieu}."),
            ket_luan=("Ở người gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú, FIB-4 tại ngưỡng 2,67 có độ nhạy "
                      "thấp, không đủ để loại trừ xơ hoá tiến triển."),
            ket_cuc_phu="Độ chính xác tại ngưỡng 1,3 chưa phân tích ở đợt này — báo cáo riêng theo SAP §5",
            du_lieu_thieu=("Không có dữ liệu thiếu ở chỉ số và chuẩn tham chiếu nên không gán đa trị (khớp SAP §6)"),
            giai_thich="Không áp dụng — nghiên cứu độ chính xác chẩn đoán, không đánh giá cơ chế",
            diem_manh="Chuẩn tham chiếu đo trên mọi người tham gia; kiểm chéo độc lập bằng SPSS và R",
            so_sanh="Đối chiếu ở đoạn so sánh với Shah 2009 (PMID 19523535); tác giả " + _KC_TRUNG,
            mesh="Liver Cirrhosis; Non-alcoholic Fatty Liver Disease; Sensitivity and Specificity; ROC Curve",
        ),
        ly_do=("Ngưỡng định trước, chuẩn tham chiếu trên mọi người tham gia; AUC {auc} (KTC 95% {auc_duoi}–"
               "{auc_tren}) kiểm chéo SPSS/R khớp. Cỡ mẫu nhỏ cần nêu rõ trong hạn chế."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Kết quả — bảng 2×2", "Trình bày bảng 2×2 tại ngưỡng và sơ đồ dòng người tham gia (STARD mục 19)"),
            ("Phương pháp — mù đọc", "Ghi rõ người đánh giá chuẩn tham chiếu có biết FIB-4 không (STARD mục 13)"),
        ],
        cau_hoi=["Khoảng thời gian giữa xét nghiệm FIB-4 và chuẩn tham chiếu là bao lâu?",
                 "Cỡ mẫu thực tế có đạt số người có bệnh mà G3 tính không?"],
        checklist=("STARD 2015", "26/30 mục (87%)",
                   "mục 19 (sơ đồ dòng người tham gia), mục 13a–b (mù khi đọc), mục 24 (chỉ số tại ngưỡng khác)"),
        dac_ta=_dac_ta_g10(
            bias_risks="Sai lệch phổ bệnh; sai lệch xác minh; cỡ mẫu nhỏ",
            bias_controls=("Chọn liên tiếp; chuẩn tham chiếu trên mọi người tham gia; người đọc chuẩn tham chiếu "
                           "không biết FIB-4; ngưỡng định trước"),
            timeline=("12 tháng: chuẩn bị và đạo đức 3 tháng; thu thập 5 tháng; phân tích 1 tháng; viết và công bố "
                      "3 tháng"),
            literature_review=("FIB-4 được Shah 2009 (PMID 19523535) đánh giá ở người NAFLD với AUROC khoảng 0,8; "
                               "dữ liệu ở người ngoại trú Việt Nam còn thiếu"),
            theoretical_framework_not_applicable="Nghiên cứu độ chính xác chẩn đoán — không dựa trên khung lý thuyết",
            literature_consensus="FIB-4 có giá trị dự đoán âm cao ở ngưỡng thấp, giá trị dự đoán dương vừa phải",
            literature_disagreements="Độ chính xác khác nhau theo tuổi và phổ bệnh của quần thể",
            summary=("Bối cảnh: cần công cụ đơn giản phát hiện xơ hoá gan tiến triển. Mục tiêu: đánh giá độ chính "
                     "xác của FIB-4. Phương pháp: nghiên cứu độ chính xác chẩn đoán, AUC và độ nhạy/đặc hiệu tại "
                     "ngưỡng định trước."),
            pilot="Thử quy trình lấy mẫu và đo chuẩn tham chiếu trên 5 người ngoài mẫu",
            safety_plan="Chỉ lấy máu xét nghiệm thường quy; không có can thiệp do nghiên cứu",
            limitations="Cỡ mẫu nhỏ; một cơ sở; chưa đánh giá ngưỡng 1,3",
            # 22/11/2026 (chiều, STARD 2015 mục 3, 11, 12a, 12b, 21a): PI khai vai trò dự kiến của FIB-4, lý do chọn
            # chuẩn tham chiếu và ngưỡng, biến đo mức độ bệnh — khớp G1 (bệnh đích F3–F4, đo đàn hồi ≥ 10 kPa) và SAP
            # (ngưỡng 1,3 và 2,67 định trước); nguồn ngưỡng 2,67 là bài gốc Shah 2009 đã tra ở hồ sơ G6.5
            index_test_role=("Xét nghiệm phân loại ban đầu tại phòng khám ngoại trú, trước khi chỉ định đo độ đàn hồi "
                             "gan cho người có nguy cơ xơ hoá tiến triển"),
            reference_standard_rationale=("Đo độ đàn hồi gan thoáng qua được chọn làm chuẩn tham chiếu vì làm được "
                                          "cho mọi người tham gia ngoại trú trong cùng lần khám, người đọc độc lập "
                                          "với kết quả FIB-4"),
            index_threshold_rationale=("Ngưỡng 2,67 (ngưỡng chính) và 1,3 (ngưỡng phụ) định trước trong SAP, dựa trên "
                                       "y văn gốc của Shah 2009 (PMID 19523535); không chọn ngưỡng theo dữ liệu"),
            reference_threshold_rationale=("Ngưỡng 10 kPa của đo đàn hồi gan được dùng vì tương ứng xơ hoá tiến triển "
                                           "F3–F4, bệnh đích đã chốt ở đề cương"),
            disease_severity_variable="lsm_kpa",
            # 22/11/2026 (STARD 2015 mục 21b): biến ghi chẩn đoán ở người không có bệnh đích (phiếu thu thập, nhánh
            # «xơ hoá tiến triển = Không») — G6 mô tả ở Bảng 1 theo chuẩn tham chiếu, bộ sinh G7 chép từ đó
            alternative_diagnosis_variable="chan_doan_khac",
        ),
    )

    # ── Dự báo: mô hình nguy cơ nhập viện 12 tháng ở người suy tim ────────────────────────────────────────────
    # Ouwerkerk 2014, JACC Heart Fail — tổng quan 117 mô hình: C-statistic trung bình 0,68 cho mô hình dự báo nhập
    # viện vì suy tim (PMID 25194294).
    hs["mo_hinh_du_bao"] = _ho_so(
        ten_bai="Mô hình dự báo nguy cơ nhập viện 12 tháng ở người suy tim ngoại trú",
        thiet_ke="Phát triển mô hình dự báo, thuần tập",
        bang=[
            _dong("Nhập viện trong 12 tháng", "C-statistic (trong mẫu)", "c_statistic", "G6",
                  "Phân biệt mức vừa; chưa hiệu chỉnh lạc quan"),
            _dong(_GIOI.format(gioi="nữ"), "C-statistic", "c_statistic", "G6_NC_nu", "Thăm dò"),
            _dong(_GIOI.format(gioi="nam"), "C-statistic", "c_statistic", "G6_NC_nam", "Thăm dò"),
        ],
        muc=(
            ("Mô hình bốn yếu tố dự báo có C-statistic trong mẫu {c_statistic} (KTC 95% {c_statistic_duoi}–"
             "{c_statistic_tren}) và Brier {brier}, với {epv} biến cố trên mỗi yếu tố dự báo. Không kiểm định giả "
             "thuyết; ý nghĩa lâm sàng nằm ở khả năng phân biệt mức vừa — đủ để phân tầng nguy cơ sơ bộ, chưa đủ để "
             "quyết định cá nhân khi chưa kiểm định ngoài."),
            ("C-statistic tương đương mức trung bình của các mô hình dự báo nhập viện vì suy tim trong tổng quan 117 "
             "mô hình của Ouwerkerk và cộng sự (2014): C-statistic trung bình 0,68 (PMID 25194294). Giá trị của đề "
             "tài là ước lượng trong mẫu, chưa hiệu chỉnh lạc quan; tác giả " + _KC_TRUNG + "."),
            ("Điểm mạnh: yếu tố dự báo chọn theo y văn trước khi xem dữ liệu, số biến cố trên mỗi yếu tố đủ lớn, cỡ "
             "mẫu {n} người, kiểm chéo SPSS–R khớp. Hạn chế: C-statistic trong mẫu (bootstrap hiệu chỉnh lạc quan chạy "
             "trong kịch bản R, chưa báo ở đây), chưa kiểm định ngoài, một cơ sở, và chưa có biểu đồ hiệu chuẩn trong "
             "bản này."),
            ("Hàm ý cho thực hành: chưa dùng mô hình cho quyết định cá nhân trước khi kiểm định ngoài; có thể dùng để "
             "thử phân tầng theo dõi. Hướng tiếp: kiểm định ngoài ở cơ sở khác, báo hiệu chuẩn và lợi ích ròng "
             "(decision curve)."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Trong {n} người suy tim, mô hình gồm tuổi, LVEF, NT-proBNP và eGFR có C-statistic trong mẫu "
                     "{c_statistic} (KTC 95% {c_statistic_duoi}–{c_statistic_tren}) và Brier {brier}."),
            ket_luan=("Mô hình bốn yếu tố dự báo nhập viện 12 tháng ở người suy tim ngoại trú có khả năng phân biệt "
                      "mức vừa; cần kiểm định ngoài trước khi dùng."),
            ket_cuc_phu="Hiệu chuẩn và hiệu chỉnh lạc quan báo riêng theo SAP §9 (kịch bản R đã sinh)",
            du_lieu_thieu=("Không có dữ liệu thiếu ở các yếu tố dự báo nên không gán đa trị (khớp SAP §6)"),
            giai_thich="Không áp dụng — mô hình dự báo, không ước lượng hiệu ứng nhân quả",
            diem_manh="Yếu tố dự báo định trước theo y văn; kiểm chéo độc lập bằng SPSS và R",
            so_sanh="Đối chiếu ở đoạn so sánh với Ouwerkerk 2014 (PMID 25194294); tác giả " + _KC_TRUNG,
            mesh="Heart Failure; Hospitalization; Risk Assessment; Models, Statistical",
        ),
        ly_do=("Yếu tố dự báo định trước, EPV đủ; C-statistic {c_statistic} (KTC 95% {c_statistic_duoi}–"
               "{c_statistic_tren}) kiểm chéo SPSS/R khớp. Cần báo hiệu chuẩn và hiệu chỉnh lạc quan theo TRIPOD."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Kết quả — hiệu chuẩn", "Thêm biểu đồ hiệu chuẩn và độ dốc hiệu chuẩn (TRIPOD+AI mục 23)"),
            ("Kết quả — lạc quan", "Báo C-statistic sau hiệu chỉnh lạc quan bằng bootstrap (SAP §9)"),
        ],
        cau_hoi=["Mô hình đầy đủ (phương trình hệ số) có được công bố để người khác kiểm định ngoài không?",
                 "Người tử vong trước 12 tháng được xử lý thế nào (biến cố cạnh tranh)?"],
        checklist=("TRIPOD+AI", "24/27 mục (89%)",
                   "mục 23 (hiệu chuẩn), mục 12 (hiệu chỉnh lạc quan), mục 27 (truy cập mô hình)"),
        dac_ta=_dac_ta_g10(
            bias_risks="Quá khớp; chọn yếu tố dự báo theo dữ liệu; biến cố cạnh tranh (tử vong)",
            bias_controls=("Yếu tố dự báo định trước theo y văn; EPV ≥ 10; bootstrap hiệu chỉnh lạc quan; báo cáo "
                           "theo TRIPOD+AI"),
            timeline=("15 tháng: chuẩn bị và đạo đức 3 tháng; thu thập và theo dõi 6 tháng; phân tích 2 tháng; viết "
                      "và công bố 4 tháng"),
            literature_review=("Tổng quan 117 mô hình (Ouwerkerk 2014, PMID 25194294) cho thấy dự báo nhập viện vì "
                               "suy tim chỉ đạt mức vừa; chưa có mô hình kiểm định ở người Việt Nam ngoại trú"),
            theoretical_framework_not_applicable="Nghiên cứu mô hình dự báo — không dựa trên khung lý thuyết",
            literature_consensus="Dự báo nhập viện vì suy tim khó hơn dự báo tử vong; C-statistic thường 0,6–0,7",
            literature_disagreements="Yếu tố dự báo mạnh nhất khác nhau giữa các mô hình",
            summary=("Bối cảnh: người suy tim ngoại trú có nguy cơ nhập viện cao. Mục tiêu: phát triển mô hình dự "
                     "báo nhập viện 12 tháng. Phương pháp: thuần tập, hồi quy logistic với yếu tố dự báo định trước, "
                     "C-statistic và Brier."),
            pilot="Thử phiếu thu thập trên 10 hồ sơ ngoài mẫu",
            safety_plan="Không có can thiệp; sự cố bảo mật dữ liệu báo cáo theo quy trình đơn vị",
            limitations="Chưa kiểm định ngoài; một cơ sở; C-statistic trong mẫu",
            # 22/11/2026 (chiều, TRIPOD+AI 3b, 3c, 6c, 8c, 15, 19, 27a, 27b): PI khai mục đích sử dụng, bất bình đẳng,
            # cách xử lý điều trị, che giấu khi xác định kết cục, đầu ra/ngưỡng, sự tham gia của người bệnh và cách áp
            # dụng — khớp G1 (yếu tố đo thường quy, khung 12 tháng) và hàm ý «chưa dùng cho quyết định cá nhân»
            model_intended_use=("Hỗ trợ bác sĩ phòng khám suy tim phân tầng nguy cơ nhập viện 12 tháng tại lần khám "
                                "định kỳ để sắp lịch tái khám; người dùng dự kiến là bác sĩ và điều dưỡng phòng khám"),
            health_inequalities=("Chưa có dữ liệu trong nước về khác biệt nguy cơ nhập viện vì suy tim giữa các nhóm "
                                 "dân số; khác biệt theo giới được đánh giá bằng phân tích nhóm nhỏ tiền định"),
            model_treatment_handling=("Người tham gia điều trị suy tim theo hướng dẫn tại phòng khám; điều trị không "
                                      "đưa vào mô hình làm yếu tố dự báo vì mô hình dự báo nguy cơ dưới chăm sóc "
                                      "thường quy"),
            outcome_assessment_blinding=("Người xác định nhập viện đối chiếu giấy ra viện mà không biết giá trị yếu tố "
                                         "dự báo của người tham gia"),
            model_output_threshold=("Mô hình cho xác suất nhập viện trong 12 tháng của từng người; không đặt ngưỡng "
                                    "phân loại vì mục đích là phân tầng theo dõi, chưa dùng cho quyết định cá nhân"),
            ppi_plan=("Không có sự tham gia của người bệnh hoặc công chúng trong thiết kế và thực hiện nghiên cứu; kết "
                      "quả được phổ biến tới người bệnh qua phòng khám"),
            model_input_handling=("Chưa áp dụng mô hình khi thiếu một trong bốn giá trị tuổi, LVEF, NT-proBNP, eGFR "
                                  "của lần khám gần nhất; không gán giá trị thay thế khi sử dụng mô hình"),
            model_user_interaction=("Người dùng nhập bốn giá trị có sẵn trong hồ sơ khám; không cần kỹ năng thống kê, "
                                    "chỉ cần đọc đúng đơn vị của NT-proBNP và eGFR"),
        ),
    )

    # ── Tổng quan hệ thống + phân tích gộp: SGLT2i và nhập viện vì suy tim ────────────────────────────────────
    # Zelniker 2019, Lancet — gộp 3 thử nghiệm, 34.322 người: SGLT2i giảm tử vong tim mạch hoặc nhập viện vì suy tim
    # HR 0,77 (0,71–0,84), lợi ích tương tự dù có hay không tiền sử suy tim (PMID 30424892).
    hs["tong_quan_gop"] = _ho_so(
        ten_bai="Thuốc ức chế SGLT2 và nhập viện vì suy tim ở người đái tháo đường típ 2: tổng quan hệ thống và phân "
                "tích gộp",
        thiet_ke="Tổng quan hệ thống và phân tích gộp",
        bang=[
            _dong("Nhập viện vì suy tim", "RR gộp (ngẫu nhiên, DerSimonian–Laird)", "rr_gop", "G6",
                  "Giảm khoảng một phần ba nguy cơ tương đối"),
            _dong("Nhập viện vì suy tim", "RR gộp (cố định)", "rr_gop_co_dinh", "G6", "Trùng mô hình ngẫu nhiên "
                  "do không có không đồng nhất"),
            _dong("Độ nhạy: loại thử nghiệm nguy cơ sai lệch cao", "RR gộp (ngẫu nhiên)", "rr_gop", "G6_DN_rob_thap",
                  "Kết quả không đổi khi loại thử nghiệm chất lượng thấp"),
        ],
        muc=(
            ("Gộp {k} thử nghiệm cho RR nhập viện vì suy tim {rr_gop} (KTC 95% {rr_gop_duoi}–{rr_gop_tren}); I² "
             "{i2_pct}%, τ² {tau2}. Về ý nghĩa lâm sàng, mức giảm khoảng một phần ba nguy cơ tương đối là đáng kể; "
             "nguy cơ tuyệt đối phụ thuộc nguy cơ nền của từng nhóm người bệnh, nên cần đọc cùng tỷ lệ biến cố ở nhóm "
             "chứng."),
            ("Chiều và độ lớn phù hợp với phân tích gộp 3 thử nghiệm kết cục tim mạch (34.322 người) của Zelniker và "
             "cộng sự (2019): SGLT2i giảm tử vong tim mạch hoặc nhập viện vì suy tim với HR 0,77 (KTC 95% 0,71–0,84), "
             "lợi ích tương tự dù có hay không tiền sử suy tim (PMID 30424892). Kết cục khác nhau (gộp so với riêng "
             "nhập viện vì suy tim); tác giả " + _KC_TRUNG + "."),
            ("Điểm mạnh: chiến lược tìm theo PRISMA-S, đánh giá RoB 2 cho từng thử nghiệm, độ nhạy loại thử nghiệm "
             "nguy cơ sai lệch cao, kiểm chéo R (metafor) và SPSS khớp. Hạn chế: không đồng nhất có thể bị ước lượng "
             "thấp khi ít thử nghiệm lớn chi phối, chưa đánh giá sai lệch công bố (cần ≥ 10 thử nghiệm và biểu đồ "
             "phễu), và chưa phân nhóm theo thuốc."),
            ("Hàm ý cho thực hành: chứng cứ gộp ủng hộ cân nhắc SGLT2i ở người đái tháo đường típ 2 có nguy cơ tim "
             "mạch để giảm nhập viện vì suy tim, theo hướng dẫn hiện hành. Hướng tiếp: phân nhóm theo thuốc và chức "
             "năng thận, đánh giá mức chắc chắn GRADE."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Gộp {k} thử nghiệm: SGLT2i giảm nhập viện vì suy tim với RR {rr_gop} (KTC 95% {rr_gop_duoi}–"
                     "{rr_gop_tren}); I² {i2_pct}%."),
            ket_luan=("Ở người đái tháo đường típ 2 không có suy tim lúc đầu, SGLT2i giảm nhập viện vì suy tim khoảng "
                      "một phần ba."),
            ket_cuc_phu=("Kết cục phụ (tử vong tim mạch; biến cố thận) chưa gộp ở đợt này — báo cáo riêng theo "
                         "đề cương PROSPERO"),
            du_lieu_thieu="Gộp ở cấp nghiên cứu — không có dữ liệu thiếu cấp cá nhân (khớp SAP §6)",
            giai_thich=("Một giả thuyết được nêu trong y văn là tác dụng lợi niệu thải natri và giảm tiền gánh; tổng "
                        "quan này không đánh giá cơ chế"),
            diem_manh="Hai người trích dữ liệu độc lập; kiểm chéo R (metafor) và SPSS khớp",
            so_sanh="Đối chiếu ở đoạn so sánh với Zelniker 2019 (PMID 30424892); tác giả " + _KC_TRUNG,
            mesh="Sodium-Glucose Transporter 2 Inhibitors; Heart Failure; Diabetes Mellitus, Type 2; Meta-Analysis",
        ),
        ly_do=("Tìm theo PRISMA-S, RoB 2 từng thử nghiệm; RR gộp {rr_gop} (KTC 95% {rr_gop_duoi}–{rr_gop_tren}) "
               "kiểm chéo metafor khớp. Cần thêm đánh giá sai lệch công bố và GRADE."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Kết quả — sai lệch công bố", "Thêm biểu đồ phễu và kiểm định Egger (PRISMA 2020 mục 21)"),
            ("Kết quả — GRADE", "Thêm bảng tóm tắt phát hiện với mức chắc chắn GRADE (PRISMA 2020 mục 22)"),
        ],
        cau_hoi=["Các thử nghiệm có định nghĩa nhập viện vì suy tim thống nhất không?",
                 "Có thử nghiệm nào bị loại vì thiếu dữ liệu biến cố không?"],
        checklist=("PRISMA 2020", "24/27 mục (89%)",
                   "mục 21 (sai lệch công bố), mục 22 (mức chắc chắn), mục 24c (sửa đổi đề cương)"),
        dac_ta=_dac_ta_g10(
            team="Chủ nhiệm đề tài (BS. Nguyễn Văn A), thống kê viên, 2 người sàng lọc và trích dữ liệu độc lập",
            budget="Kinh phí đơn vị cấp cho truy cập toàn văn và phân tích",
            bias_risks="Sai lệch công bố; sai lệch chọn nghiên cứu; không đồng nhất định nghĩa kết cục",
            bias_controls=("Tìm nhiều nguồn theo PRISMA-S; hai người sàng lọc và trích độc lập; RoB 2; độ nhạy loại "
                           "thử nghiệm nguy cơ sai lệch cao"),
            timeline=("10 tháng: đăng ký PROSPERO và tìm 2 tháng; sàng lọc và trích 3 tháng; phân tích 2 tháng; viết "
                      "và công bố 3 tháng"),
            literature_review=("Zelniker 2019 (PMID 30424892) gộp 3 thử nghiệm kết cục tim mạch; cần cập nhật với các "
                               "thử nghiệm mới và tập trung riêng nhập viện vì suy tim"),
            theoretical_framework_not_applicable=("Tổng quan hệ thống chứng cứ can thiệp — không dựa trên khung lý "
                                                  "thuyết"),
            literature_consensus="SGLT2i giảm nhập viện vì suy tim nhất quán qua các thử nghiệm lớn",
            literature_disagreements="Độ lớn lợi ích trên biến cố xơ vữa khác nhau theo bệnh tim mạch nền",
            summary=("Bối cảnh: SGLT2i có thể giảm nhập viện vì suy tim. Mục tiêu: gộp hiệu quả trên nhập viện vì "
                     "suy tim ở người đái tháo đường típ 2. Phương pháp: tổng quan hệ thống theo PRISMA 2020, gộp RR "
                     "bằng mô hình ngẫu nhiên DerSimonian–Laird."),
            pilot="Thử chiến lược tìm và phiếu trích trên 3 thử nghiệm đã biết",
            safety_plan="Không có người tham gia — tổng quan dữ liệu đã công bố",
            limitations="Ít thử nghiệm lớn chi phối; chưa đánh giá sai lệch công bố; chưa phân nhóm theo thuốc",
            # 22/11/2026 (chiều, PRISMA 2020 mục 7, 11 và tóm tắt A5): PI khai câu lệnh tìm đầy đủ và cách đánh giá
            # nguy cơ sai lệch — khớp G1 (MeSH + từ khoá, bộ lọc RCT Cochrane; hai người sàng lọc độc lập) và biến
            # «RoB 2 — đánh giá chung» của bảng trích xuất
            search_strings_full=('PubMed: ("Sodium-Glucose Transporter 2 Inhibitors"[MeSH] OR gliflozin*[tiab] OR '
                                 'empagliflozin[tiab] OR dapagliflozin[tiab] OR canagliflozin[tiab] OR '
                                 'ertugliflozin[tiab]) AND ("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 '
                                 'diabetes"[tiab]) AND (randomized controlled trial[pt] OR randomi*[tiab]); bộ lọc RCT '
                                 'Cochrane, không giới hạn ngôn ngữ; câu lệnh tương ứng cho Embase, Cochrane CENTRAL, '
                                 'ClinicalTrials.gov và WHO ICTRP'),
            rob_assessment_process=("RoB 2 cho từng thử nghiệm; hai người đánh giá độc lập, bất đồng do người thứ ba "
                                    "quyết định"),
        ),
    )

    # ── Định tính: trải nghiệm và rào cản khi bắt đầu insulin ─────────────────────────────────────────────────
    # Polonsky 2011, Curr Med Res Opin — khảo sát 1.400 người ĐTĐ típ 2 chưa dùng insulin ở 8 nước: 17,2% không sẵn
    # sàng, 34,7% phân vân (PMID 21469914). Polonsky 2019, J Diabetes Complications — người bệnh đánh giá việc
    # «hướng dẫn cách tiêm» là hữu ích và đi kèm ít trì hoãn bắt đầu insulin hơn (PMID 30709604).
    hs["dinh_tinh"] = _ho_so(
        ten_bai="Trải nghiệm và rào cản khi bắt đầu tiêm insulin ở người đái tháo đường típ 2",
        thiet_ke="Nghiên cứu định tính, phân tích chủ đề",
        bang=[
            _dong("Chủ đề phổ biến nhất: {chu_de_1_ten}", "Tỷ lệ bản gỡ băng có chủ đề (Wilson, mô tả)", "chu_de_1",
                  "G6", "Mô tả độ phổ biến; không suy rộng thống kê"),
            _dong("Chủ đề phổ biến nhất — người đã bắt đầu insulin", "Tỷ lệ (mô tả)", "chu_de_1", "G6_NC_da_tiem",
                  "So sánh mô tả theo tiêu chí đa dạng"),
            _dong("Chủ đề phổ biến nhất — người chưa bắt đầu insulin", "Tỷ lệ (mô tả)", "chu_de_1", "G6_NC_chua_tiem",
                  "So sánh mô tả theo tiêu chí đa dạng"),
        ],
        muc=(
            ("Phân tích {n_ban_go_bang} bản gỡ băng cho {so_chu_de} chủ đề; phổ biến nhất là «{chu_de_1_ten}» "
             "({chu_de_1_n}/{n_ban_go_bang} bản, tỷ lệ {chu_de_1}; KTC 95% {chu_de_1_duoi}–{chu_de_1_tren}), tiếp "
             "theo là «{chu_de_2_ten}». Nghiên cứu định tính không kiểm định ý nghĩa thống kê; tần suất chỉ mô tả độ "
             "phổ biến. Ý nghĩa lâm sàng: hỗ trợ của gia đình và nỗi lo hạ đường huyết là hai điểm bác sĩ có thể "
             "chủ động trao đổi khi đề xuất insulin."),
            ("Phù hợp với khảo sát 1.400 người đái tháo đường típ 2 chưa dùng insulin ở 8 nước của Polonsky và cộng sự "
             "(2011): 17,2% không sẵn sàng và 34,7% phân vân khi được đề nghị insulin (PMID 21469914); nghiên cứu "
             "quốc tế sau đó ghi nhận người bệnh đánh giá việc được hướng dẫn cách tiêm là hữu ích (PMID 30709604). "
             "Bối cảnh văn hoá và hệ thống y tế khác nhau; tác giả " + _KC_TRUNG + "."),
            ("Điểm mạnh: chọn mẫu có chủ đích theo tiêu chí đa dạng định trước, hai người mã hoá, nhật ký quyết định "
             "mã hoá, kiểm tra lại với người tham gia. Hạn chế: một cơ sở, người đồng ý phỏng vấn có thể cởi mở hơn, "
             "vai trò của người phỏng vấn (nhân viên y tế) có thể ảnh hưởng câu trả lời, và kết quả không suy rộng "
             "thống kê; khả năng chuyển giao giới hạn ở người bệnh được đề xuất khởi trị insulin tại cơ sở ngoại trú "
             "có bối cảnh tương tự."),
            ("Hàm ý cho thực hành: khi đề xuất insulin, mời người nhà cùng học cách tiêm và trao đổi kế hoạch phòng hạ "
             "đường huyết khi đi làm. Hướng tiếp: xây dựng và thử nghiệm can thiệp giáo dục có người nhà tham gia."),
        ),
        tra_loi_g7=_tra_loi_g7(
            ket_qua=("Từ {n_ban_go_bang} bản gỡ băng, {so_chu_de} chủ đề được xác định; phổ biến nhất là "
                     "«{chu_de_1_ten}» ({chu_de_1_n}/{n_ban_go_bang} bản) và «{chu_de_2_ten}»."),
            ket_luan=("Hỗ trợ của gia đình và nỗi lo hạ đường huyết khi đi làm định hình trải nghiệm bắt đầu insulin "
                      "của người đái tháo đường típ 2 ngoại trú."),
            ket_cuc_phu="Không áp dụng — nghiên cứu định tính không có kết cục phụ định lượng",
            du_lieu_thieu="Không áp dụng — dữ liệu là bản gỡ băng phỏng vấn, không có biến thiếu cần gán",
            giai_thich="Không áp dụng — nghiên cứu định tính mô tả trải nghiệm, không đánh giá cơ chế sinh học",
            diem_manh="Hai người mã hoá độc lập, nhật ký quyết định mã hoá, kiểm tra lại với người tham gia",
            so_sanh="Đối chiếu ở đoạn so sánh với Polonsky 2011 (PMID 21469914); tác giả " + _KC_TRUNG,
            mesh="Diabetes Mellitus, Type 2; Insulin; Qualitative Research; Patient Acceptance of Health Care",
        ),
        ly_do=("Chọn mẫu có chủ đích, hai người mã hoá, trình bày theo COREQ; chủ đề «{chu_de_1_ten}» có trích dẫn "
               "minh hoạ. Cần nêu rõ bão hoà dữ liệu và phản tư của người phỏng vấn."),
        gop_y=[
            ("Từ khoá (trang đầu)", "Dòng từ khoá do máy tách từng chữ của tiêu đề — thay bằng thuật ngữ MeSH"),
            ("Phương pháp — phản tư", "Mô tả vai trò và quan hệ của người phỏng vấn với người tham gia (COREQ 1–8)"),
            ("Kết quả — bão hoà", "Nêu rõ thời điểm đạt bão hoà dữ liệu (COREQ mục 22)"),
        ],
        cau_hoi=["Người phỏng vấn có phải là bác sĩ điều trị của người tham gia không?",
                 "Bộ mã ban đầu được xây dựng theo hướng suy diễn hay quy nạp?"],
        checklist=("COREQ", "29/32 mục (91%)",
                   "mục 1–8 (phản tư người nghiên cứu), mục 22 (bão hoà dữ liệu), mục 28 (người tham gia kiểm tra)"),
        dac_ta=_dac_ta_g10(
            team="Chủ nhiệm đề tài (BS. Nguyễn Văn A), 2 người phỏng vấn và mã hoá được tập huấn, người thứ ba phân xử",
            bias_risks="Ảnh hưởng của người phỏng vấn; người tham gia trả lời theo mong đợi xã hội",
            bias_controls=("Người phỏng vấn không phải bác sĩ điều trị; hai người mã hoá độc lập; nhật ký phản tư; "
                           "kiểm tra lại với người tham gia"),
            timeline=("10 tháng: chuẩn bị và đạo đức 3 tháng; phỏng vấn và gỡ băng 3 tháng; mã hoá và phân tích 2 "
                      "tháng; viết và công bố 2 tháng"),
            literature_review=("Polonsky 2011 (PMID 21469914) ghi nhận tỷ lệ đáng kể người bệnh không sẵn sàng bắt "
                               "đầu insulin; dữ liệu định tính ở người Việt Nam ngoại trú còn thiếu"),
            theoretical_framework=("Mô hình niềm tin sức khoẻ (Health Belief Model) định hướng câu hỏi phỏng vấn về "
                                   "lợi ích, rào cản và tín hiệu hành động"),
            literature_consensus="Rào cản tâm lý (sợ kim, sợ hạ đường huyết, kỳ thị) phổ biến khi bắt đầu insulin",
            literature_disagreements="Mức độ rào cản khác nhau rõ giữa các nước và bối cảnh văn hoá",
            summary=("Bối cảnh: nhiều người đái tháo đường típ 2 trì hoãn bắt đầu insulin. Mục tiêu: tìm hiểu trải "
                     "nghiệm và rào cản khi bắt đầu tiêm insulin. Phương pháp: phỏng vấn sâu bán cấu trúc, phân tích "
                     "chủ đề, báo cáo theo COREQ."),
            pilot="Thử bộ câu hỏi phỏng vấn trên 2 người ngoài mẫu; chỉnh câu hỏi trước khi phỏng vấn chính thức",
            safety_plan=("Người tham gia có thể dừng phỏng vấn bất kỳ lúc nào; người bộc lộ lo âu nặng được giới "
                         "thiệu tư vấn theo quy trình phòng khám"),
            limitations="Một cơ sở; không suy rộng thống kê; ảnh hưởng của người phỏng vấn",
            reflexivity_statement=("Người phỏng vấn là điều dưỡng được tập huấn, không điều trị người tham gia; nhóm "
                                   "ghi nhật ký phản tư sau mỗi cuộc phỏng vấn và thảo luận ảnh hưởng của vai trò "
                                   "nhân viên y tế lên câu trả lời"),
        ),
    )
    # 22/11/2026 (chiều, PRISMA 2020 for Abstracts A9): tóm tắt tổng quan có ô «Limitations» — tác giả viết hạn chế
    # chính của BẰNG CHỨNG (ít thử nghiệm lớn chi phối — như bản diễn giải; định nghĩa kết cục theo từng thử nghiệm —
    # như G1; chưa phân nhóm theo thuốc — như hạn chế đã khai ở đặc tả)
    hs["tong_quan_gop"]["tra_loi_G7"] = [*hs["tong_quan_gop"]["tra_loi_G7"], (
        r"^limitations$", "Ít thử nghiệm lớn chi phối kết quả gộp; định nghĩa nhập viện vì suy tim theo từng thử "
                          "nghiệm, không thống nhất; chưa phân nhóm theo thuốc.")]
    return hs
