r"""Hồi quy phát hiện #5 (audit vòng 34, 2026-09-06) trong
scripts/build_library_catalog.py — ``classify()`` so khớp CHUỖI CON thuần,
không có ranh giới bên TRÁI, khiến từ khóa "af " (nhận diện rung nhĩ/AF
trong danh mục "Tim mạch") khớp NHẦM vào một họ (surname) kết thúc bằng
"af" theo sau khoảng trắng.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def classify(name_norm, table, default=None):
        for label, kws in table:
            for kw in kws:
                if kw.strip() and kw in name_norm:
                    return label
        return default

``SPECIALTY`` liệt "Tim mạch" ĐẦU TIÊN với từ khóa ``"af "`` (khoảng
trắng chỉ ở CUỐI, không có ở đầu). Với tên file
``"BS Graf bai giang than kinh.pdf"`` (một bài giảng THẦN KINH, có ghi rõ
"than kinh" ngay trong tên) — sau khi ``norm()`` hạ thường/bỏ dấu:
``"bs graf bai giang than kinh.pdf"`` — chuỗi con ``"af "`` xuất hiện bên
trong "gr-AF- " (đuôi họ "Graf" + khoảng trắng theo sau), khớp NGAY LẬP
TỨC ở nhánh Tim mạch (kiểm TRƯỚC Thần kinh trong SPECIALTY), trả về
"Tim mạch" — SAI — dù "than kinh" (từ khóa đúng của Thần kinh) cũng có
mặt ngay trong CHÍNH tên file đó nhưng không bao giờ được xét tới vì
``classify()`` trả về ngay khi gặp khớp đầu tiên.

BẢN VÁ: với từ khóa dạng "xxx " (khoảng trắng CUỐI, KHÔNG có ở đầu — từ
khóa có CẢ HAI như " esc " vốn đã an toàn, không đổi hành vi), chỉ nhận
khớp khi ký tự ngay TRƯỚC vị trí khớp không phải chữ/số ASCII (đứng đầu
chuỗi hoặc sau một ranh giới không phải chữ-số) — dùng
``name_norm.find(kw, ...)`` lặp qua MỌI vị trí xuất hiện (không chỉ vị
trí đầu tiên) để không bỏ sót khớp hợp lệ đứng sau một khớp giả ở vị trí
sớm hơn."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_library_catalog.py"


def _nap():
    spec = importlib.util.spec_from_file_location(
        "build_library_catalog_vong34_test", SCRIPT_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_library_catalog_vong34_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCaChinhHoGrafKhongBiNhanNhamTimMach:
    """★★★ Ca chính — file có họ tác giả kết thúc bằng "af" + khoảng trắng
    (vd "Graf") KHÔNG được nhận nhầm là Tim mạch khi chuyên khoa thật
    (Thần kinh) đã nêu rõ trong chính tên file."""

    def test_bai_giang_than_kinh_cua_bs_graf_khong_thanh_tim_mach(self):
        mod = _nap()
        name_norm = mod.norm("BS Graf bai giang than kinh.pdf")
        result = mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH")
        assert result == "Thần kinh", (
            "TRƯỚC bản vá: chuỗi con 'af ' (không ranh giới trái) khớp "
            "NHẦM vào đuôi họ 'Graf' + khoảng trắng, khiến tài liệu Thần "
            f"kinh rõ ràng bị phân vào 'Tim mạch'. name_norm={name_norm!r} "
            f"kết quả thực tế={result!r}"
        )

    def test_dot_quy_cua_tac_gia_graf_khong_thanh_tim_mach(self):
        mod = _nap()
        name_norm = mod.norm("Graf 2023 dot quy huong dan.pdf")
        result = mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH")
        assert result == "Thần kinh"


class TestDoiChungTuKhoaAfVaThaVanHoatDongDung:
    """Đối chứng — từ khóa "af "/"tha " vẫn PHẢI nhận diện đúng Tim mạch khi
    xuất hiện hợp lệ (không phải đuôi một từ khác)."""

    def test_af_dung_dau_chuoi_van_nhan_tim_mach(self):
        mod = _nap()
        name_norm = mod.norm("AF guideline 2024.pdf")
        assert mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH") == "Tim mạch"

    def test_af_dung_sau_khoang_trang_van_nhan_tim_mach(self):
        mod = _nap()
        name_norm = mod.norm("huong dan af rung nhi 2024.pdf")
        assert mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH") == "Tim mạch"

    def test_tha_dung_hop_le_van_nhan_tim_mach(self):
        # "tha " có cùng cấu trúc lỗi (khoảng trắng chỉ ở cuối) — xác nhận
        # bản vá không làm mất khả năng nhận diện hợp lệ của nó.
        mod = _nap()
        name_norm = mod.norm("tang huyet ap tha guideline 2024.pdf")
        assert mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH") == "Tim mạch"

    def test_tu_khoa_hai_dau_khoang_trang_khong_doi_hanh_vi(self):
        # " esc " (khoảng trắng CẢ HAI đầu) không thuộc diện sửa — vẫn phải
        # khớp đúng như cũ khi đứng giữa các từ khác.
        mod = _nap()
        name_norm = mod.norm("khuyen cao esc 2024 tim mach.pdf")
        assert mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH") == "Tim mạch"

    def test_khong_co_tu_khoa_nao_khop_tra_ve_mac_dinh(self):
        mod = _nap()
        name_norm = mod.norm("chua ro chuyen khoa.pdf")
        assert mod.classify(name_norm, mod.SPECIALTY, "MẶC ĐỊNH") == "MẶC ĐỊNH"
