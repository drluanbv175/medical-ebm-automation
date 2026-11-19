"""Biểu bảng chuẩn của chương «Dự kiến kết quả» và trình bày kết quả G6 (bác sĩ 19/11/2026: «phần trình bày biểu bảng
chưa có và chưa đúng chuẩn … và cả đồ thị và tất cả vấn đề liên quan số liệu phân tích, kết quả phân tích»).

Đo trước khi vá: chương 5 do máy dựng chỉ có 2–4 bảng chung (bảng nền 2 dòng, ô kết cục «…», dòng «(12 biến)»), không
sơ đồ chọn đối tượng, không biểu đồ, không ghi chú chữ viết tắt; bản soạn tay đặt tên bảng nghiêng và dựng «Hình 5.1»
bằng một cái bảng; chỉ mục kết quả G6 in chuỗi JSON thô. K1–K8 không luật nào đo phần này.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import chay_sap_g6 as G6  # noqa: E402
import khung_bieu_bang as KBB  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402

THIET_KE = ("rct", "cross_sectional", "cohort", "case_control", "diagnostic", "prediction", "sr_ma", "qualitative")


def _ngu_canh(tk: str) -> KBB.NguCanh:
    bien = {
        "nhom": KBB.Bien("nhom", "Nhóm", "nhi_phan", [("1", "Can thiệp"), ("0", "Chăm sóc thường quy")]),
        "kq": KBB.Bien("kq", "Kiểm soát huyết áp", "nhi_phan", [("1", "Có"), ("0", "Không")]),
        "tuoi": KBB.Bien("tuoi", "Tuổi", "lien_tuc", [], "năm"),
        "gioi": KBB.Bien("gioi", "Giới", "nhi_phan", [("1", "Nam"), ("2", "Nữ")]),
        "hoc_van": KBB.Bien("hoc_van", "Học vấn", "thu_tu", [("1", "Tiểu học"), ("2", "THCS"), ("3", "THPT")]),
        "dtd": KBB.Bien("dtd", "Đái tháo đường", "nhi_phan", [("1", "Có"), ("0", "Không")]),
    }
    ma_tran = [
        {"muc_tieu": "1", "khai_niem": "kiểm soát huyết áp", "vai_tro": "ket_cuc_chinh", "bien": "kq",
         "kieu": "nhi_phan"},
        {"muc_tieu": "1", "khai_niem": "nhóm can thiệp", "vai_tro": "phoi_nhiem", "bien": "nhom", "kieu": "nhi_phan"},
        {"muc_tieu": "1", "khai_niem": "tuổi", "vai_tro": "hiep_bien", "bien": "tuoi", "kieu": "lien_tuc"},
        {"muc_tieu": "1", "khai_niem": "giới", "vai_tro": "hiep_bien", "bien": "gioi", "kieu": "nhi_phan"},
        {"muc_tieu": "1", "khai_niem": "học vấn", "vai_tro": "hiep_bien", "bien": "hoc_van", "kieu": "thu_tu"},
        {"muc_tieu": "1", "khai_niem": "đái tháo đường", "vai_tro": "hiep_bien", "bien": "dtd", "kieu": "nhi_phan"},
        {"muc_tieu": "1", "khai_niem": "biến cố bất lợi", "vai_tro": "mo_ta", "bien": "dtd", "kieu": "nhi_phan"},
    ]
    pt = [{"id": "MT1_chinh", "vai": "chinh", "mo_ta": "Phân tích chính",
           "tham_so": {"outcome": "kq", "group": "nhom", "covariates": ["tuoi", "gioi"], "outcome_type": "poisson_pr"}},
          {"id": "NC_nam", "vai": "nhom_con", "mo_ta": "Tỷ lệ kq — gioi = 1 (nam)"},
          {"id": "NC_nu", "vai": "nhom_con", "mo_ta": "Tỷ lệ kq — gioi = 2 (nữ)"},
          {"id": "DN1", "vai": "do_nhay", "mo_ta": "Ca đầy đủ"}]
    return KBB.NguCanh(tk, ["So sánh tỷ lệ kiểm soát huyết áp giữa hai nhóm"], bien, ma_tran, pt, 218)


def _chuong(tk: str, tmp_path: Path, ve_anh: bool = False) -> str:
    dong, loi_ve = KBB.ve_chuong(KBB.dung_khung(_ngu_canh(tk)), 5, tmp_path if ve_anh else None, ve_anh)
    assert not loi_ve, loi_ve
    return "\n".join(dong)


# ── 1. Mọi thiết kế: chương dựng ra qua K9 và K4/K8 ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tk", THIET_KE)
def test_chuong_moi_thiet_ke_dat_k9_k4_k8(tk, tmp_path):
    md = _chuong(tk, tmp_path)
    assert KBB.kiem_bieu_bang(md, tk, 1) == []
    assert KDN.loi_k8(md) == []
    assert "Biểu đồ 5.1" in md or tk == "qualitative" and "Biểu đồ" in md


def test_chuong_ve_anh_that_va_k9_kiem_tep_hinh(tmp_path):
    md = _chuong("rct", tmp_path, ve_anh=True)
    assert (tmp_path / KBB.THU_MUC_HINH / "hinh-5-1.png").is_file()
    assert KBB.kiem_bieu_bang(md, "rct", 1, goc=tmp_path) == []
    (tmp_path / KBB.THU_MUC_HINH / "hinh-5-1.png").unlink()
    assert any("thiếu tệp hình" in x for x in KBB.kiem_bieu_bang(md, "rct", 1, goc=tmp_path))


def test_rct_dung_chuan_consort(tmp_path):
    md = _chuong("rct", tmp_path)
    assert "CONSORT" in md and "Biến cố bất lợi theo nhóm phân bổ" in md
    nen = md[md.index("Đặc điểm nền"):].split("*Ghi chú:*")[0]
    assert "| p |" not in nen  # CONSORT: không kiểm định đặc điểm nền
    assert "Hiệu số tuyệt đối (KTC 95%)" in md  # kết cục nhị phân: cả hiệu ứng tuyệt đối và tương đối


# ── 2. K9 bắt đúng từng lỗi trình bày ─────────────────────────────────────────────────────────────────────────────
def _md_hop_le(tmp_path):
    return _chuong("cross_sectional", tmp_path)


@pytest.mark.parametrize("sua, mau", [
    (lambda m: m.replace("**Bảng 5.1. ", "*Bảng 5.1. ", 1).replace("người tham gia**", "người tham gia*", 1)
     if "**Bảng 5.1. " in m else m, "chưa đúng chuẩn"),
    (lambda m: m.replace("**Bảng 5.2.", "**Bảng 5.3.", 1), "không liên tục"),
    (lambda m: m.replace("| Tuổi (năm), TB ± ĐLC hoặc trung vị [KTPV] |", "| (12 biến) |", 1), "hàng giữ chỗ"),
    (lambda m: m.replace("*Ghi chú:* Chữ viết tắt — TB: trung bình; ĐLC: độ lệch chuẩn; KTPV: khoảng tứ phân vị.",
                         "*Ghi chú:* Biến định lượng.", 1), "chưa giải thích"),
    (lambda m: m.replace("(Mục tiêu 1)", "(mục tiêu chính)"), "mục tiêu 1 chưa có"),
    (lambda m: m.replace("Hình 5.1. Sơ đồ chọn đối tượng nghiên cứu (theo STROBE)", "Hình 5.1. Quy trình"),
     "STROBE"),
])
def test_k9_bat_tung_loi(tmp_path, sua, mau):
    md = sua(_md_hop_le(tmp_path))
    loi = KBB.kiem_bieu_bang(md, "cross_sectional", 1)
    assert any(mau in x for x in loi), loi


def test_k9_bat_ten_hinh_dat_tren_hinh_va_bang_nen_co_cot_p(tmp_path):
    md = _chuong("rct", tmp_path)
    i = md.index("*Mô tả hình:*")
    j = md.index("**Hình 5.1.")
    dao = md[:i] + md[j:md.index("\n", j) + 1] + "\n" + md[i:j] + md[md.index("\n", j) + 1:]
    assert any("PHÍA DƯỚI" in x for x in KBB.kiem_bieu_bang(dao, "rct", 1))
    p_nen = md.replace("| Đặc điểm | Can thiệp (n = …)", "| Đặc điểm | p | Can thiệp (n = …)", 1)
    assert any("cột p" in x for x in KBB.kiem_bieu_bang(p_nen, "rct", 1))


def test_k9_bat_chuong_cu_cua_bo_sinh_truoc_19_11():
    cu = ("# 5. DỰ KIẾN KẾT QUẢ\n\n**Bảng 5.1. Đặc điểm nền theo nhóm ngẫu nhiên hoá**\n\n| Biến | A | B |\n"
          "|---|---|---|\n"
          "| Tuổi (năm) | … ± … | … ± … |\n\n**Bảng 5.2. Kết cục chính**\n\n| Kết cục | A | B | Hiệu ứng |\n"
          "|---|---|---|---|\n| … | … | … | … |\n\n# 6. KẾ HOẠCH\n")
    loi = KBB.kiem_bieu_bang(cu, "rct", 1)
    assert any("hình/biểu đồ" in x for x in loi)
    assert any(x.startswith("K9 thiếu hình bắt buộc") and "CONSORT" in x for x in loi)  # sơ đồ CONSORT
    assert any("mục tiêu 1" in x for x in loi) and any("KTC" in x for x in loi)


# ── 3. Nâng cấp tại chỗ chương soạn tay ──────────────────────────────────────────────────────────────────────────
def test_nang_cap_chuong_soan_tay(tmp_path):
    md = ("# 5. DỰ KIẾN KẾT QUẢ\n\nKết quả được trình bày theo các bảng dưới đây.\n\n"
          "*Bảng 5.1. Đặc điểm chung (n = 218).*\n\n| Đặc điểm | n (%) hoặc TB ± ĐLC |\n|---|---|\n| Tuổi | — |\n\n"
          "*Bảng 5.2. Tỷ lệ kiểm soát (Mục tiêu 1).*\n\n| Chỉ số | Tỷ lệ % (KTC 95%) |\n|---|---|\n"
          "| Kiểm soát | — |\n\n"
          "*Tỷ lệ tính trên người đến khám.*\n\n"
          "*Bảng 5.3. Phân tích độ nhạy.* Trình bày ước lượng trong từng kịch bản.\n\n"
          "*Hình 5.1. Sơ đồ tuyển chọn (theo STROBE).*\n\n| Bước | Số lượng |\n|---|---|\n| Được mời | n = … |\n"
          "| → Từ chối | n = … |\n| **Đưa vào phân tích** | **n = …** |\n\n# 6. KẾ HOẠCH\n")
    moi, loi_ve = KBB.nang_cap_chuong(md, _ngu_canh("cross_sectional"), tmp_path, True)
    assert not loi_ve
    assert "Quy ước trình bày:" in moi
    assert "**Bảng 5.1. Đặc điểm chung (n = 218)**" in moi and not re.search(r"^\*(?:Bảng|Hình) ", moi, re.M)
    assert "Chữ viết tắt — TB: trung bình" in moi and "Tỷ lệ tính trên người đến khám." in moi
    assert "| Phân tích | Loại |" in moi  # «Bảng 5.3» chỉ có một câu ⇒ bảng thật dựng từ đặc tả
    assert moi.index("**Hình 5.1.") < moi.index("**Bảng 5.1.")  # sơ đồ chọn đối tượng lên đầu chương
    assert (tmp_path / KBB.THU_MUC_HINH / "hinh-5-1.png").is_file()
    assert "**Biểu đồ 5.1." in moi
    assert KBB.kiem_bieu_bang(moi, "cross_sectional", 1, goc=tmp_path) == []


# ── 4. K4: giai đoạn eGFR theo KDIGO không phải mã cổng ──────────────────────────────────────────────────────────
def test_k4_mien_giai_doan_egfr_kdigo():
    bt = next(b for b, nhan in KDN._KY_HIEU_NOI_BO if nhan == "mã cổng G0/G4–G10")
    assert bt.search("| – G4 (eGFR 15–29) | …/… |")  # chính luật vẫn khớp …
    assert KBB._nhan_muc_kem_khoang([("5", "G4")], "G4 15–29; G5 < 15", "Nhóm eGFR theo KDIGO") == \
        [("5", "G4 (eGFR 15–29)")]  # … nên khung luôn ghi kèm eGFR, và K4 miễn đúng dòng có eGFR


# ── 5. Word: ảnh thật + tên căn giữa ──────────────────────────────────────────────────────────────────────────────
def test_md2docx_chen_anh_va_can_giua_ten(tmp_path):
    import md2docx_vn as M  # noqa: PLC0415

    md = _chuong("rct", tmp_path, ve_anh=True)
    out = tmp_path / "x.docx"
    M.markdown_to_docx(md, out)
    with zipfile.ZipFile(out) as z:
        ten = z.namelist()
        xml = z.read("word/document.xml").decode("utf-8")
    assert any(n.startswith("word/media/") for n in ten)
    i = xml.index("Hình 5.1.")
    assert 'w:jc w:val="center"' in xml[xml.rfind("<w:p>", 0, i) if xml.rfind("<w:p>", 0, i) > 0 else 0:i] or \
        'w:val="center"' in xml[max(0, i - 600):i]


# ── 6. G6: ước lượng viết theo chuẩn, không JSON thô; forest từ số thật ──────────────────────────────────────────
def test_g6_dinh_dang_uoc_luong_va_forest(tmp_path):
    cm = {"study": "S", "luc": "2026-11-19", "dac_ta": {"tep": "x", "dau": "y", "duyet": "DA_DUYET"},
          "du_lieu_khoa": {"sha256": "0" * 64}, "kiem_cheo": False,
          "phan_tich": [{"id": "MT1_chinh", "vai": "chinh", "trang_thai": "DA_CHAY", "mo_ta": "Chính",
                         "uoc_luong": {"poisson_pr": {"PR_adj": 1.3493, "CI_95": [1.0164, 1.7913], "p": 0.0382}}},
                        {"id": "NC_nam", "vai": "nhom_con", "trang_thai": "DA_CHAY", "mo_ta": "Tỷ lệ — nam",
                         "uoc_luong": {"poisson_pr": {"PR_adj": 1.255, "CI_95": [0.854, 1.8441], "p": 0.0004}}},
                        {"id": "MO", "vai": "mo_ta", "trang_thai": "DA_CHAY",
                         "uoc_luong": {"ty_le": [{"ty_le": 42.06, "ci_95": [37.47, 46.78], "n": 400}]}}]}
    assert G6.dinh_dang_uoc_luong(cm["phan_tich"][0]["uoc_luong"]) == \
        "PR hiệu chỉnh 1,35 (KTC 95% 1,02–1,79); p = 0,038"
    assert G6.dinh_dang_uoc_luong(cm["phan_tich"][1]["uoc_luong"]).endswith("p < 0,001")
    assert G6.dinh_dang_uoc_luong(cm["phan_tich"][2]["uoc_luong"]) == "Tỷ lệ 42,1% (KTC 95% 37,5–46,8); n = 400"
    hinh = G6.ve_forest_g6(cm, tmp_path)
    assert hinh and (tmp_path / hinh).is_file()
    md = G6.md_chi_muc(cm, hinh)
    bang = md.split("|---|---|---|---|---|---|---|")[1].split("*Ghi chú:*")[0]
    assert "{" not in bang and "PR hiệu chỉnh 1,35 (KTC 95% 1,02–1,79)" in bang
    assert "KTC: khoảng tin cậy" in md
    assert "![Biểu đồ ước lượng]" in md and json.dumps(cm)  # cm không bị đổi


# ── 7. G9 «Phần 8»: tích theo phép kiểm điện tử TRƯỚC chữ ký; B1–B3 theo chấm sống ─────────────────────────────────
def test_phan_8_tich_theo_phep_kiem_va_nhom_d():
    import run_g9_auto as G9A  # noqa: PLC0415

    to = ("A1. ICMJE\n    ☐ Chưa ký  ☐ Đã ký đầy đủ\n\nA2. COI\n    ☐ Chưa nộp  ☐ Đã nộp đủ\n\n"
          "A7. Quyền truy cập\n    ☐ Mọi tác giả rà được dữ liệu\n\n"
          "D1. Trưởng đơn vị\n    ☐ Không cần  ☐ Cần -> ☐ Đã ký\n\n"
          "D3. Nhà tài trợ\n    ☐ Không có tài trợ  ☐ Đã duyệt\n")
    tt = {"G9-HUMAN-01": "PASS", "G9-HUMAN-03": "BLOCKED", "G9-HUMAN-05A": "PASS", "G9-HUMAN-11": "PASS"}
    rd = {"institutional_confirmation": {"department_head_required": True, "department_head_confirmed": True,
                                         "sponsor_review_required": False}}
    ra = G9A.tich_phan_8(to, tt, rd)
    assert "☐ Chưa ký  ☑ Đã ký đầy đủ" in ra          # A1 đạt ⇒ tích ô «đã xong»
    assert "☐ Chưa nộp  ☐ Đã nộp đủ" in ra            # A2 chưa đạt ⇒ không tích
    assert "☑ Mọi tác giả rà được dữ liệu" in ra      # mục một ô
    assert "☐ Không cần  ☐ Cần -> ☑ Đã ký" in ra      # D1 cần và đã ký
    assert "☑ Không có tài trợ  ☐ Đã duyệt" in ra     # D3 không cần
    assert G9A.tich_phan_8(to, {}, rd) == to          # không chấm được ⇒ không tích bừa
