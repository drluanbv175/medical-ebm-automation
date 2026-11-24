"""K11 — số đo huyết áp ghi đúng định dạng (bác sĩ 22/11/2026: «180/110 mmHg là số đo huyết áp phải ghi đúng định
dạng»). Đo được trước bản vá: hồ sơ giả lập có 16 chỗ «<140/90», «≥180/110 mmHg», nhãn biến «(<140/90)» thiếu đơn vị;
bảng biến G3 của đề tài BTM ghi «từ 140/90 ở 2 lượt khám» — không chốt nào bắt."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402


@pytest.mark.parametrize("dong, loi", [
    ("Thêm huyết áp đo được từ 140/90 ở 2 lượt khám", "thiếu đơn vị mmHg"),
    ("Kiểm soát huyết áp tháng 6 (<140/90)", "thiếu đơn vị mmHg"),
    ("Ngừng khi HA ≥180/110 mmHg", "dấu so sánh cách số"),
    ("huyết áp 140 / 90 mmHg", "khoảng trắng quanh «/»"),
    ("huyết áp đích 130/80mmHg", "một khoảng trắng trước đơn vị"),
])
def test_bat_dinh_dang_huyet_ap_sai(dong, loi):
    assert loi in (K.loi_huyet_ap(dong) or "")


@pytest.mark.parametrize("dong", [
    "Cơn tăng huyết áp ≥ 180/110 mmHg phải xử trí",
    "Kiểm soát huyết áp tháng 6 (< 140/90 mmHg)",
    "Huyết áp mục tiêu 120/80 mmHg",
    "Threshold Criteria of 140/90 or 130/80 mmHg",                     # đơn vị dùng chung, tiêu đề nguyên văn
    "huyết áp 140/90 hoặc 130/80 mmHg",
    "ngày 17/11/2026, phiên bản 1.0",                                   # ngày
    "Kiểm soát huyết áp — nhóm chứng: 57/118 (48.3%)",                  # tỷ số đếm
    "Đạt kiểm soát huyết áp: 120/100 người bệnh",                      # tỷ số đếm (tử > mẫu vẫn không phải huyết áp)
    "Kiểm soát huyết áp tháng 6: 118/100 (54,1%)",
    "Không có số đo nào trong câu này",
])
def test_khong_bat_nham(dong):
    assert K.loi_huyet_ap(dong) is None


def test_loi_k11_bao_dong_huyet_ap_ngoai_tltk():
    md = ("# ĐẶT VẤN ĐỀ\n\nNgười bệnh có huyết áp từ 140/90 ở 2 lượt khám.\n\n"
          "# TÀI LIỆU THAM KHẢO\n\n1. Smith. BP <140/90 in adults. 2020.\n")
    loi = [x for x in K.loi_k11(md) if "huyết áp" in x]
    assert loi == ["K11 dòng 3: số đo huyết áp «140/90» — thiếu đơn vị mmHg (vd «≥ 180/110 mmHg»)"]


def test_ho_so_gia_lap_khong_con_so_do_huyet_ap_sai():
    """Chuỗi hồ sơ giả lập đi thẳng vào đề cương/bản thảo — mọi số đo huyết áp phải đúng định dạng."""
    sai = []
    for ten in ("gia_lap_dinh_ky.py", "gia_lap_chan_thuc.py", "gia_lap_bien_the_kho.py", "gia_lap_tron_vong.py",
                "gia_lap_ho_so_sau_g6.py", "gia_lap_kich_ban_them.py"):
        for so, d in enumerate((ROOT / "tools" / ten).read_text(encoding="utf-8").splitlines(), 1):
            if d.lstrip().startswith("#"):
                continue
            loi = K.loi_huyet_ap(d)
            if loi:
                sai.append(f"{ten}:{so}: {loi}")
    assert sai == []


@pytest.mark.parametrize("dong, loi", [
    ("Tuổi ≥18", "dấu so sánh dính số"),
    ("p<0,001", "dấu so sánh dính số"),
    ("liều 100mg/ngày", "số dính đơn vị"),
    ("nhiệt độ 37,5°C", "số dính đơn vị"),
    ("lấy 5 ml máu tĩnh mạch", "viết «mL»"),
    ("glucose 126 mg/dl", "viết «mg/dL»"),
    ("BMI 25 kg/m2", "viết «kg/m²»"),
])
def test_so_do_chung_bat_sai(dong, loi):
    assert loi in (K.loi_so_do(dong) or "")


@pytest.mark.parametrize("dong", [
    "Tuổi ≥ 18, liều 100 mg/ngày, 37,5 °C, 5 mL, glucose 126 mg/dL, BMI 25 kg/m², tỷ lệ 48,3%",
    "eGFR ≥ 60 mL/phút/1,73 m², HbA1c < 7%, p < 0,001",
    "Mã G6_TH_bien_co, mục A12, HbA1c, Bảng 1",
])
def test_so_do_chung_khong_bat_nham(dong):
    assert K.loi_so_do(dong) is None


def test_ho_so_gia_lap_moi_so_do_dung_chuan():
    """Mọi chuỗi văn bản của hồ sơ giả lập (đi thẳng vào đề cương/bản thảo) đạt luật số đo chung."""
    import re as _re

    chuoi = _re.compile(r"\"(?:[^\"\\\n]|\\.)*\"")
    sai = []
    for ten in ("gia_lap_dinh_ky.py", "gia_lap_chan_thuc.py", "gia_lap_bien_the_kho.py", "gia_lap_tron_vong.py",
                "gia_lap_ho_so_sau_g6.py", "gia_lap_kich_ban_them.py"):
        for so, d in enumerate((ROOT / "tools" / ten).read_text(encoding="utf-8").splitlines(), 1):
            if d.lstrip().startswith("#") or _re.search(r"re\.(?:compile|search|match|sub)|\br\"", d):
                continue  # biểu thức regex không phải văn bản
            for m in chuoi.finditer(d):
                loi = K.loi_so_do(m.group(0))
                if loi:
                    sai.append(f"{ten}:{so}: {loi}")
    assert sai == []


def test_gia_lap_soat_moi_van_ban_de_tai_va_cong_phan_bao_do(tmp_path):
    """Bộ giả lập soát MỌI văn bản .md của đề tài (không riêng đề cương nộp); tiêu đề nguyên văn/đối chiếu máy miễn."""
    import json

    import gia_lap_tron_vong as TV
    import kiem_gia_lap_16 as KG

    out = tmp_path / "exports" / "X"
    (out / "_dau_may_sinh").mkdir(parents=True)
    (out / "G4_A5_SAP_FINAL_X.md").write_text("# SAP\n\nĐiều chỉnh nếu >3 kết cục chính.\n", encoding="utf-8",
                                               newline="\n")
    (out / "G2_A3_ETHICS_PACKAGE_X.md").write_text("Tóm tắt ≤ 1 trang; huyết áp ≥ 180/110 mmHg.\n",
                                                   encoding="utf-8", newline="\n")
    (out / "A12_CITATION_VERIFICATION_X.md").write_text("| Title | BP <140/90 in adults |\n", encoding="utf-8",
                                                        newline="\n")
    (out / "G6_kiem_cheo.md").write_text("p<0.001\n", encoding="utf-8", newline="\n")
    (out / "_dau_may_sinh" / "y.md").write_text("Tuổi ≥18\n", encoding="utf-8", newline="\n")

    class _O:
        _KHONG_SOAT_SO_DO = TV.TronVong._KHONG_SOAT_SO_DO
        _soat_so_do = TV.TronVong._soat_so_do

    o = _O()
    o.out = out
    o.study = "X"  # 23/11/2026: _soat_so_do soát thêm báo cáo tổng hợp của đề tài (cần mã đề tài như TronVong thật)
    sai = o._soat_so_do()
    assert len(sai) == 1 and sai[0].startswith("G4_A5_SAP_FINAL_X.md: K11 dòng 3: dấu so sánh dính số «>3»"), sai
    bc = tmp_path / "bc.json"
    bc.write_text(json.dumps({"ma": "x", "so_do_sai": sai}), encoding="utf-8", newline="\n")
    assert any("trình bày số đo sai chuẩn ở 1 chỗ" in x for x in KG.kiem_mot(bc))
    bc.write_text(json.dumps({"ma": "x", "so_do_sai": []}), encoding="utf-8", newline="\n")
    assert not any("trình bày số đo" in x for x in KG.kiem_mot(bc))
