"""SANRA 2019 cho chương TỔNG QUAN TÀI LIỆU của đề cương (K17) + bộ sinh dựng đủ mục từ dữ kiện G0 (22/11/2026).

Bác sĩ 22/11/2026: «Tổng quan tài liệu đã có nền, hãy tiếp tục nâng cấp.» Chương tổng quan của đề cương là tổng quan
tường thuật ⇒ chuẩn đã kiểm định là SANRA (Baethge 2019, PMID 30962953, CC BY 4.0); mục 3 (mô tả tìm kiếm) đối chiếu
PRISMA-S (PMID 34285662) ở ba mục áp dụng được: nguồn (1), câu tìm đầy đủ (8), ngày tìm (13).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402
import tieu_chi_chuan_de_cuong as TC  # noqa: E402
from test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, _de_tai  # noqa: E402

DAT = """# ĐẶT VẤN ĐỀ

Tăng huyết áp là nguyên nhân hàng đầu của biến cố tim mạch [1].

## MỤC TIÊU NGHIÊN CỨU

1. Xác định tỷ lệ kiểm soát huyết áp ở người bệnh ngoại trú.

# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU

## 1.1. Chiến lược tìm kiếm tài liệu

| Nguồn | Câu tìm | Ngày tra |
|---|---|---|
| PubMed | `hypertension[tiab] AND control[tiab]` | 15/11/2026 |

## 1.2. Bằng chứng hiện có

Một nghiên cứu cắt ngang tại Thụy Điển ghi nhận tỷ lệ kiểm soát 41% [2].

Bằng chứng trong nước còn gián tiếp vì khác bối cảnh [3].

# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

Nội dung.
"""


def _sanra(md: str, tk: str = "cross_sectional") -> dict:
    kq = K.doi_chieu(md, tk)
    return {r.ma: r for r in kq["ket_qua"] if r.chuan == "SANRA 2019"}


# ───────────────────────────── đăng ký chuẩn và điều kiện ─────────────────────────────
def test_sanra_ap_dung_khi_co_chuong_tong_quan_khong_ap_cho_tong_quan_he_thong():
    ten = lambda md, tk="cross_sectional": [c for c, _ in K.chuan_ap_dung(tk, md)]  # noqa: E731
    assert "SANRA 2019" in ten(DAT)
    assert "SANRA 2019" in ten(DAT.replace("# CHƯƠNG 1. TỔNG QUAN", "# 3. TỔNG QUAN"))  # khuôn cũ 1–7
    assert "SANRA 2019" not in ten(DAT.replace("TỔNG QUAN TÀI LIỆU", "CƠ SỞ LÝ LUẬN"))
    assert "SANRA 2019" not in ten("Câu nhắc tổng quan tài liệu trong văn.\n")  # phải là đề mục chương
    assert ten(DAT, "sr_ma") == ["PRISMA-P 2015"]  # tổng quan hệ thống: PRISMA-P, không SANRA


def test_bang_tieu_chi_du_sau_muc_khong_luu_nguyen_van_va_co_nguon():
    muc = TC.danh_sach_muc_them("SANRA 2019")
    assert [m.ma for m in muc] == ["1", "2", "3", "4", "5", "6"]
    assert all(m.nguyen_van is None and m.chan for m in muc)
    assert all(p in K.PHAN for m in muc for p in m.phan)
    assert "30962953" in TC.NGUON_CHUAN_THEM["SANRA 2019"] and "34285662" in TC.NGUON_CHUAN_THEM["SANRA 2019"]


def test_van_ban_du_sau_muc_thi_dat():
    kq = _sanra(DAT)
    assert {ma: r.trang_thai for ma, r in kq.items()} == {str(i): "dat" for i in range(1, 7)}, \
        {ma: r.thieu for ma, r in kq.items()}


# ───────────────────────────── từng mục đỏ đúng chỗ ─────────────────────────────
def test_muc_1_thieu_tam_quan_trong_hoac_trich_dan():
    md = DAT.replace("Tăng huyết áp là nguyên nhân hàng đầu của biến cố tim mạch [1].", "Đề tài thực hiện tại khoa.")
    md = md.replace("ghi nhận tỷ lệ kiểm soát 41% [2]", "ghi nhận 41 phần trăm đạt đích [2]")
    md = md.replace("Xác định tỷ lệ kiểm soát huyết áp", "Xác định mức kiểm soát huyết áp")  # mục tiêu nằm trong ĐVĐ
    assert _sanra(md)["1"].thieu == ["tầm quan trọng của vấn đề"]


def test_muc_3_prisma_s_thieu_ngay_thieu_cau_tim_thieu_nguon():
    assert _sanra(DAT.replace("15/11/2026", "gần đây"))["3"].thieu == ["ngày tìm (PRISMA-S 13)"]
    khong_cau = DAT.replace("`hypertension[tiab] AND control[tiab]`", "tăng huyết áp và kiểm soát")
    assert _sanra(khong_cau)["3"].thieu == ["chiến lược/câu tìm đầy đủ (PRISMA-S 8)"]
    # «and» viết thường trong tiêu đề tiếng Anh không phải câu tìm Boole
    for tieu_de in ("Hypertension and (control) trends", "Hypertension (control) or trends"):
        assert _sanra(khong_cau.replace("tăng huyết áp và kiểm soát", tieu_de))["3"].thieu \
            == ["chiến lược/câu tìm đầy đủ (PRISMA-S 8)"], tieu_de
    co_cau = khong_cau.replace("tăng huyết áp và kiểm soát", "(hypertension) AND control")
    assert _sanra(co_cau)["3"].trang_thai == "dat"
    assert _sanra(DAT.replace("| PubMed |", "| Thư viện |"))["3"].thieu == ["nguồn đã tra (PRISMA-S 1)"]


def test_muc_4_cau_so_lieu_khong_nguon_bi_bat():
    md = DAT.replace("Bằng chứng trong nước", "Tỷ lệ kiểm soát trong nước khoảng 30%. Bằng chứng trong nước")
    r = _sanra(md)["4"]
    assert r.trang_thai == "thieu" and r.thieu[0].startswith("câu nêu số liệu không dẫn nguồn")
    # có rào đón/có trích dẫn ⇒ không phải câu số liệu trôi nổi
    assert _sanra(md.replace("khoảng 30%.", "khoảng 30% [3]."))["4"].trang_thai == "dat"


def test_muc_5_thieu_gioi_han_bang_chung():
    md = DAT.replace("Bằng chứng trong nước còn gián tiếp vì khác bối cảnh [3].", "Thêm thông tin [3].")
    assert _sanra(md)["5"].thieu == ["giới hạn của bằng chứng"]


def test_muc_6_so_lieu_phai_cung_doan_voi_trich_dan():
    md = DAT.replace("ghi nhận tỷ lệ kiểm soát 41% [2].", "ghi nhận tỷ lệ kiểm soát 41%.\n\nNguồn: [2].")
    r = _sanra(md)["6"]
    assert r.trang_thai == "thieu" and "số liệu kết cục" in r.thieu[0] or "trích dẫn nguồn" in r.thieu[0]
    assert _sanra(DAT.replace("41% [2]", "C-statistic trung bình 0,71 [2]"))["6"].trang_thai == "dat"


# ───────────────────────────── bộ sinh: dựng đủ mục từ dữ kiện G0 ─────────────────────────────
def test_bo_sinh_dung_bang_tim_kiem_tu_g0_va_dat_sanra(tmp_path):
    d = _de_tai(tmp_path, "cross_sectional")
    # Checkpoint G0 HỢP LỆ như một lượt G0 thật: chủ đề + kết quả PubMed (khớp G0_pubmed_raw.json và hai PMID đã sàng
    # của G0_TONG_HOP_BANG_CHUNG) + tra cơ sở đăng ký — chốt G0 (K20 đọc G0-AUTO-02) không chặn vì thiếu nền bằng chứng.
    (d / "G0_checkpoint.json").write_text(json.dumps({
        "topic": "Tin nhắn nhắc uống thuốc và kiểm soát huyết áp ngoại trú",
        "pubmed_results": {"n_pmids": 2, "pmids": ["11111111", "22222222"]},
        "registry_check": {
            "registry": "ClinicalTrials.gov", "query": "hypertension AND SMS", "checked": True, "n_trials": 7,
            "n_active": 2, "checked_at": "2026-11-15T10:00:00"}}), encoding="utf-8", newline="\n")
    (d / "G0_TRA_ICTRP_20261116.md").write_text(
        "| # | Trường tra | Trạng thái tuyển | Kết quả |\n|---|---|---|---|\n"
        "| 1 | Condition = `hypertension` · Countries = Viet Nam | ALL | 40 thử nghiệm |\n", encoding="utf-8",
        newline="\n")
    m = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    m["gate_params"]["G0"]["registry_manual_checked"] = {"ictrp": "2026-11-16", "ictrp_ket_qua": "không trùng"}
    (d / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    kq = SDC.sinh(d, MA, ghi=True)
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    assert kq["ma"] == 0, kq.get("loi")
    assert "Nguồn và chiến lược tìm kiếm tài liệu" in van
    assert ("| ClinicalTrials.gov | `hypertension AND SMS` | 15/11/2026 | 7 hồ sơ đăng ký, 2 đang hoặc sắp tuyển |"
            in van)
    assert ("| WHO ICTRP | Condition = hypertension · Countries = Viet Nam (40 thử nghiệm) | 16/11/2026 | không trùng |"
            in van)
    assert "1 bài liên quan trực tiếp và 1 bài chỉ liên quan gián tiếp" in van
    # câu tóm lược G0 dẫn PMID đã kiểm chứng ⇒ giữ, đổi số; câu dẫn PMID chưa kiểm chứng ⇒ bỏ cả câu (không số mồ côi)
    assert "tỷ lệ kiểm soát 70% ở nhóm nhận tin nhắn [" in van and "61%" not in van and "99999999" not in van
    assert "G0" not in van.split("# 3. TỔNG QUAN", 1)[1].split("# 4.", 1)[0]  # không mã cổng trong chương (K4)
    r = _sanra(van)
    assert r and all(x.trang_thai == "dat" for x in r.values()), {ma: x.thieu for ma, x in r.items()}


def test_vang_du_kien_g0_thi_khong_bia_hang(tmp_path):
    d = _de_tai(tmp_path, "cross_sectional")
    (d / "G0_pubmed_raw.json").unlink()
    (d / f"G0_TONG_HOP_BANG_CHUNG_{MA}.json").unlink()
    n = SDC.Nguon(d, MA)
    assert SDC.hang_tim_kiem(n) == [] and SDC.cau_bang_chung_g0(n) == []


def test_cach_tim_cua_agent_bo_ten_tep_va_ma_cong():
    nguon, cau = SDC._cach_tim_nguon("PubMed E-utilities (esearch + esummary), nhánh không lọc thiết kế của truy vấn "
                                     "G0: x[tiab] — ngày 2026-11-19")
    assert nguon == "PubMed (tra bổ sung)" and "G0" not in cau and "E-utilities" not in cau
    nguon, cau = SDC._cach_tim_nguon("Europe PMC (G0_pubmed_raw.json → khong_loc) theo truy vấn G0, tra 2026-10-25")
    assert nguon == "Europe PMC (tra bổ sung)" and ".json" not in cau and "G0" not in cau
    assert cau == "Europe PMC theo chiến lược tìm chính"


def test_tieu_de_tu_khai_thiet_ke_quan_sat_thang_nhanh_tim(tmp_path):
    d = _de_tai(tmp_path, "cross_sectional")
    n = SDC.Nguon(d, MA)
    n.td.md["11111111"]["title"] = "Factors associated with control: a cross-sectional study."
    n.g0raw["rct"] = [{"pmid": "11111111"}]  # nhánh RCT của G0 (lọc hợp nhiều loại xuất bản)
    assert SDC._loai_bai(n, "11111111") == "Nghiên cứu quan sát"
    n.td.md["11111111"]["title"] = "A prospective cohort study of a community intervention"
    assert SDC._loai_bai(n, "11111111") == "Nghiên cứu quan sát"
    n.td.md["11111111"]["title"] = "Text messages to improve control: a randomised trial"
    assert SDC._loai_bai(n, "11111111") == "Thử nghiệm ngẫu nhiên"
