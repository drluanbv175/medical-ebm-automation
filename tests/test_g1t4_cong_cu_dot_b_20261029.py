"""Công cụ pha phát triển bộ câu hỏi — đợt B theo tranh biện hội đồng G1 C1a (G1-TB-20261028T204958-b2aab6a1).

THÊM 29/10/2026.

Lỗi đã đo trên C1a:
① `cvi` lấy trung bình S-CVI trên MỌI dòng của phiếu, kể cả câu thông tin chung và câu kết cục ⇒ không còn là giá trị
  nội dung của THANG;
② `truy-xuat` chỉ phủ các mục đem chấm CVI (43/58 câu của phiếu), chỉ lấy «Field Label» rút gọn (câu 11 mất mệnh đề
  «tính từ lúc lấy số đến lúc được vào phòng khám») và không sinh lại được mà giữ các cột chủ nhiệm đã điền;
③ không có hướng dẫn mã hoá các biểu mẫu;
④ kiểm máy G1-T4 đòi bảng truy xuất BẰNG tập mục phiếu CVI ⇒ phủ đủ câu của phiếu lại bị coi là lỗi.
Test chốt từng việc. Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402
import pha_phat_trien_cong_cu as PCC  # noqa: E402

TU_DIEN = (
    "Variable / Field Name,Form Name,Section Header,Field Type,Field Label,Field Note,Field Annotation\n"
    "record_id,phieu,Hành chính,text,Mã số phiếu,,\n"
    "nghe,phieu,Nhân khẩu,dropdown,Câu 5. Nghề nghiệp,,\n"
    "nghekhac,phieu,,text,Câu 5. Nghề nghiệp — ghi rõ nếu chọn Khác,,\n"
    "kyvong,phieu,Kỳ vọng,text,Câu 11. Chờ dự kiến (phút),,\n"
    "gioi_thieu,phieu,,descriptive,Phần 2 — hướng dẫn,,\n"
    "a1,phieu,Phần 2 — Likert,radio,A1. Chờ đăng ký,Likert,@NOMISSING Nhãn 5 mức\n"
    "a2,phieu,,radio,A2. Chờ gặp bác sĩ,,\n"
    "ykien,phieu,Phần 4 — Ý kiến mở,notes,Ý kiến đóng góp khác,,\n"
    "thoigian_cho,lop_his,Phơi nhiễm,text,Thời gian chờ (phút),,\n"
)

PHU_LUC = """# PHỤ LỤC B. BẢNG KHÁC

11. Câu đánh số của phụ lục khác — không được lấy.

# PHỤ LỤC C. PHIẾU KHẢO SÁT

Kính gửi Ông/Bà,

**PHẦN 1. THÔNG TIN CHUNG**

5. Nghề nghiệp chính hiện tại: ☐ 1. Cán bộ ☐ 2. Khác (ghi rõ) ……
11. Trước khi đến, Ông/Bà nghĩ phải chờ bao lâu tính từ lúc lấy số đến lúc được vào phòng khám? …… phút

**PHẦN 2. ĐÁNH GIÁ**

Xin Ông/Bà cho biết mức độ hài lòng.

| Mã | Nội dung đánh giá | 1 | 2 |
|---|---|---|---|
| **A** | **KHẢ NĂNG TIẾP CẬN** | | |
| A1 | Thời gian chờ đợi để làm thủ tục đăng ký khám | ☐ | ☐ |
| A2 | Thời gian chờ đợi để được vào gặp bác sĩ khám | ☐ | ☐ |

*¹ Chú thích cuối bảng.*

**PHẦN 4. Ý KIẾN ĐÓNG GÓP KHÁC**

Ông/Bà có đề xuất hoặc góp ý gì thêm không?

……………………

# PHỤ LỤC D. SƠ ĐỒ

12. Câu sau phụ lục C — không được lấy.
"""


def _ghi(p: Path, van: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(van, encoding="utf-8", newline="\n")
    return p


def _phieu_cvi(p: Path) -> Path:
    return _ghi(p, "muc,CG01,CG02,CG03\nA1,4,4,4\nA2,4,3,4\nkyvong,1,1,2\n")


# ---------------------------------------------------------------- ① S-CVI theo phạm vi thang
def test_s_cvi_chi_tinh_tren_muc_thuoc_thang(tmp_path, capsys):
    cot, dong = PCC._doc_csv(_phieu_cvi(tmp_path / "cvi.csv"))
    cu = PCC.tinh_cvi(cot, dong)
    assert cu["s_cvi_ave"] == pytest.approx(2 / 3) and cu["pham_vi_s_cvi"]["da_khai"] is False
    assert any("chưa khai phạm vi thang" in c for c in cu["canh_bao"])
    moi = PCC.tinh_cvi(cot, dong, muc_thang=["[A-F][0-9]*"])
    assert moi["s_cvi_ave"] == pytest.approx(1.0) and moi["s_cvi_ua"] == pytest.approx(1.0)
    assert moi["pham_vi_s_cvi"] == {"da_khai": True, "mau": ["[A-F][0-9]*"], "so_muc_thang": 2,
                                    "muc_ngoai_thang": ["kyvong"]}
    assert any("I-CVI <" in c and "kyvong" in c for c in moi["canh_bao"]), "mục ngoài thang vẫn báo I-CVI"
    assert not any("chưa khai phạm vi thang" in c for c in moi["canh_bao"])
    with pytest.raises(PCC.LoiDauVao, match="không khớp mục nào"):
        PCC.tinh_cvi(cot, dong, muc_thang=["[A-F][0-9]*", "Z9"])
    assert PCC.main(["cvi", str(tmp_path / "cvi.csv"), "--muc-thang", "A*"]) == 0
    assert "Phạm vi S-CVI: 2 mục thuộc thang" in capsys.readouterr().out


# ---------------------------------------------------------------- ② bảng truy xuất
def test_truong_can_truy_xuat_bo_ma_ban_ghi_truong_phu_va_mo_ta(tmp_path):
    truong = PCC._doc_tu_dien(_ghi(tmp_path / "td.csv", TU_DIEN))
    assert PCC.truong_can_truy_xuat(truong, "phieu") == ["nghe", "kyvong", "a1", "a2", "ykien"]
    assert PCC.truong_can_truy_xuat(truong, "lop_his") == ["thoigian_cho"]


def test_truy_xuat_them_form_va_nguyen_van_phu_luc(tmp_path):
    td, md = _ghi(tmp_path / "td.csv", TU_DIEN), _ghi(tmp_path / "de_cuong.md", PHU_LUC)
    p, canh_bao = PCC.sinh_truy_xuat_chi_tiet(["A1", "A2", "kyvong"], td, tmp_path / "o", them_form="phieu",
                                              nguyen_van=md)
    cot, dong = PCC._doc_csv(p)
    assert cot == PCC.COT_TRUY_XUAT + [PCC.COT_NGUYEN_VAN]
    assert [d["muc"] for d in dong] == ["A1", "A2", "kyvong", "nghe", "ykien"], "mục CVI trước, câu còn lại theo form"
    ds = {d["muc"]: d for d in dong}
    assert "tính từ lúc lấy số đến lúc được vào phòng khám" in ds["kyvong"][PCC.COT_NGUYEN_VAN]
    assert ds["kyvong"]["noi_dung"] == "Câu 11. Chờ dự kiến (phút)", "nội dung vẫn là nhãn từ điển"
    assert ds["A1"][PCC.COT_NGUYEN_VAN] == "Thời gian chờ đợi để làm thủ tục đăng ký khám"
    assert ds["nghe"][PCC.COT_NGUYEN_VAN].startswith("Nghề nghiệp chính hiện tại")
    assert ds["ykien"][PCC.COT_NGUYEN_VAN] == "Ông/Bà có đề xuất hoặc góp ý gì thêm không?"
    assert canh_bao == [], canh_bao
    with pytest.raises(PCC.LoiDauVao, match="không có form"):
        PCC.sinh_truy_xuat_chi_tiet(["A1"], td, tmp_path / "o2", them_form="khong_co")
    with pytest.raises(PCC.LoiDauVao, match="không thấy tiêu đề"):
        PCC.sinh_truy_xuat_chi_tiet(["A1"], td, tmp_path / "o3", nguyen_van=md, phu_luc="PHỤ LỤC Z")


def test_truy_xuat_bao_cau_khong_tim_thay_nguyen_van(tmp_path):
    td = _ghi(tmp_path / "td.csv", TU_DIEN)
    bo_a2 = "| A2 | Thời gian chờ đợi để được vào gặp bác sĩ khám | ☐ | ☐ |\n"
    md = _ghi(tmp_path / "de_cuong.md", PHU_LUC.replace(bo_a2, ""))
    p, canh_bao = PCC.sinh_truy_xuat_chi_tiet(["A1", "A2"], td, tmp_path / "o", nguyen_van=md)
    assert {d["muc"]: d[PCC.COT_NGUYEN_VAN] for d in PCC._doc_csv(p)[1]}["A2"] == ""
    assert len(canh_bao) == 1 and canh_bao[0].endswith(": A2")


def test_truy_xuat_tron_giu_cot_chu_nhiem_va_chep_ban_cu(tmp_path):
    td, thu = _ghi(tmp_path / "td.csv", TU_DIEN), tmp_path / "o"
    p = PCC.sinh_truy_xuat(["A1", "A2"], td, thu)
    van = p.read_text(encoding="utf-8").replace(
        f"A1,A1. Chờ đăng ký,Phần 2 — Likert,{PCC.CHO_CHU_NHIEM},{PCC.CHO_CHU_NHIEM}",
        f"A1,A1. Chờ đăng ký,Phần 2 — Likert,Mẫu số 2,{PCC.CHO_CHU_NHIEM}")
    assert "Mẫu số 2" in van
    p.write_text(van, encoding="utf-8", newline="\n")
    with pytest.raises(PCC.LoiDauVao, match="không ghi đè"):
        PCC.sinh_truy_xuat(["A1", "A2"], td, thu)
    _ghi(td, TU_DIEN.replace("A2. Chờ gặp bác sĩ,,", "A2. Chờ gặp bác sĩ,Đã sửa ghi chú,"))
    p2, canh_bao = PCC.sinh_truy_xuat_chi_tiet(["A1", "A2"], td, thu, them_form="phieu", tron=True)
    ds = {d["muc"]: d for d in PCC._doc_csv(p2)[1]}
    assert ds["A1"]["nguon_goc"] == "Mẫu số 2", "giữ ô chủ nhiệm đã điền"
    assert ds["A1"]["ly_do_dua_vao"] == PCC.CHO_CHU_NHIEM and ds["nghe"]["nguon_goc"] == PCC.CHO_CHU_NHIEM
    assert ds["A2"]["ghi_chu_tu_dien"] == "Đã sửa ghi chú", "ghi chú làm mới từ từ điển"
    luu = list((thu / "_ban_luu").glob("bang_truy_xuat_cau_hoi_*.csv"))
    assert len(luu) == 1 and "Mẫu số 2" in luu[0].read_text(encoding="utf-8")
    assert any("_ban_luu" in c for c in canh_bao)
    with pytest.raises(PCC.LoiDauVao, match="không còn trong danh sách mới"):
        PCC.sinh_truy_xuat(["A1"], td, thu, tron=True)


# ---------------------------------------------------------------- ③ hướng dẫn mã hoá
def test_huong_dan_ma_hoa_co_ma_cau_tham_do_va_luu_y_sua_doi(tmp_path):
    td, thu = _ghi(tmp_path / "td.csv", TU_DIEN), tmp_path / "o"
    PCC.sinh_truy_xuat(["A1", "A2"], td, thu, nguyen_van=_ghi(tmp_path / "dc.md", PHU_LUC))
    p = PCC.sinh_huong_dan_ma_hoa(thu, tham_do=["a2"], muc_nhat_ky_them=["C6a", "C6b"])
    van = p.read_text(encoding="utf-8")
    for can in ("`4` = Rất liên quan", "`van_de`", "`hieu_cau_hoi`", "`dai_dien_nguoi_benh`", "km1_khia_canh_thieu",
                "Thời gian chờ đợi để được vào gặp bác sĩ khám", "`C6a`, `C6b`", "Hội đồng Đạo đức", "OSF",
                "DỰ THẢO", "Cần bác sĩ kiểm chứng"):
        assert can in van, can
    with pytest.raises(PCC.LoiDauVao, match="không ghi đè"):
        PCC.sinh_huong_dan_ma_hoa(thu)
    with pytest.raises(PCC.LoiDauVao, match="không có trong"):
        PCC.sinh_huong_dan_ma_hoa(tmp_path / "khac", tham_do=["B3"])


# ---------------------------------------------------------------- ④ kiểm máy G1-T4
def _bo(out: Path) -> Path:
    thu = out / "pha_cong_cu"
    _phieu_cvi(thu / "phieu_cvi.csv")
    PCC.sinh_mau(["A1"], 3, out / "rac")
    (out / "rac" / "nhat_ky_phong_van_nhan_thuc.csv").rename(thu / "nhat_ky_phong_van_nhan_thuc.csv")
    PCC.sinh_bo_sung(3, thu)
    _ghi(out / "G5_REDCap_dictionary_S.csv", TU_DIEN)
    return thu


def test_kiem_may_bang_truy_xuat_chua_muc_cvi_va_phu_form(tmp_path):
    out = tmp_path / "S"
    thu = _bo(out)
    PCC.sinh_truy_xuat(["A1", "A2", "kyvong"], out / "G5_REDCap_dictionary_S.csv", thu)
    loi = HD._kiem_pha_cong_cu(out, "S")
    assert len(loi) == 1 and "chưa phủ 2 câu của form «phieu»" in loi[0] and "nghe, ykien" in loi[0], loi
    PCC.sinh_truy_xuat(["A1", "A2", "kyvong"], out / "G5_REDCap_dictionary_S.csv", thu, them_form="phieu", tron=True)
    assert HD._kiem_pha_cong_cu(out, "S") == [], "bảng truy xuất CHỨA mục CVI và phủ form ⇒ sạch"
    (out / "G5_REDCap_dictionary_S.csv").unlink()
    assert HD._kiem_pha_cong_cu(out, "S") == [], "chưa có từ điển ⇒ không kiểm phần phủ form"


def test_kiem_may_van_bat_bang_truy_xuat_thieu_muc_cvi(tmp_path):
    out = tmp_path / "S"
    thu = _bo(out)
    PCC.sinh_truy_xuat(["a1", "kyvong", "nghe", "ykien"], out / "G5_REDCap_dictionary_S.csv", thu)
    loi = HD._kiem_pha_cong_cu(out, "S")
    assert any("thiếu mục của phiếu CVI (A2)" in x for x in loi), loi
    assert not any("A1" in x for x in loi), "so mục không phân biệt hoa thường"
    assert any("chưa phủ 1 câu" in x and "(a2)" in x for x in loi), loi
