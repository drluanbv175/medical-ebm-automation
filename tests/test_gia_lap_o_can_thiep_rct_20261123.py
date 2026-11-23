# -*- coding: utf-8 -*-
"""Giả lập trọn vòng: ô «ai thực hiện can thiệp» của RCT không còn bị điền «6» (23/11/2026).

Nhãn của ô §3 bản thảo «[CẦN bổ sung: ai thực hiện can thiệp, kiểm soát chất lượng/tuân thủ — không có trong REDCap
dictionary]» bị cắt ở 80 ký tự, kết thúc «… không có trong», nên khớp nhánh «trong\\s*$» của quy tắc chung
`(r"xoa/huy|huy vat ly|trong\\s*$", "6")` ⇒ bản thảo mọi kịch bản RCT có một dòng «6». Nay:
  (a) quy tắc chung neo vào NỘI DUNG câu hỏi, không vào đuôi nhãn bị cắt («trong\\s*$» và «nam\\]?$» — nhãn «… Việt
      Nam» từng bị điền «2»);
  (b) mỗi kịch bản RCT có câu trả lời riêng cho ô này, đúng can thiệp của kịch bản;
  (c) ô hỏi người/vai trò mà câu trả lời là mã số đơn lẻ ⇒ loại «dien_sai_kieu», tính là ô lỗi máy (kiem_gia_lap_16).

Dữ liệu mô phỏng, không PII.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import gia_lap_bien_the_kho as BTK  # noqa: E402
import gia_lap_chan_thuc as GCT  # noqa: E402
import gia_lap_dinh_ky as GL  # noqa: E402
import gia_lap_tron_vong as GT  # noqa: E402

O_CAN_THIEP = ("[CẦN bổ sung: ai thực hiện can thiệp, kiểm soát chất lượng/tuân thủ — không có trong REDCap "
               "dictionary]  \n")


def _o(txt: str, cong: str = "G2", tra_loi=None) -> list:
    return GT.phan_loai_o(txt, cong, "X.md", {"gate_params": {}}, {}, "rct",
                          list(tra_loi if tra_loi is not None else GT.TRA_LOI_CHUNG), {})


def test_quy_tac_chung_khong_khop_duoi_nhan_bi_cat():
    o = _o(O_CAN_THIEP, "G7")[0]
    assert o["nhan"].endswith("khong co trong "), "tiền đề: nhãn bị cắt ở 80 ký tự, đuôi «… không có trong»"
    assert o["dien"] != "6" and o["loai"] == "chua_co_ho_so"
    # nhãn kết thúc «… Việt Nam» không còn bị điền «2»
    o2 = _o("Cơ sở: [CẦN — tên cơ sở nghiên cứu tại Việt Nam]\n")[0]
    assert o2["dien"] != "2" and o2["loai"] == "chua_co_ho_so"


def test_dong_dmp_that_van_duoc_dien():
    assert _o("   ✅ Huỷ bảng nối mã: xóa/hủy vật lý trong ___ tháng\n")[0]["dien"] == "6"
    assert _o("   ✅ Dữ liệu nhận dạng được xóa/ẩn danh hóa trong vòng [CẦN] năm\n")[0]["dien"] == "2"
    assert _o("- **Thời gian lưu:** ___ năm\n")[0]["dien"] == "2"


def test_o_hoi_nguoi_ma_tra_loi_ma_so_la_loi_may():
    o = _o(O_CAN_THIEP, "G7", [(r"ai thuc hien can thiep", "6")])[0]
    assert o["loai"] == "dien_sai_kieu" and "dien_sai_kieu" in GT.LOAI_O_LOI_MAY
    # ô hỏi SỐ LƯỢNG người: mã số là câu trả lời đúng kiểu
    o2 = _o("Số người phỏng vấn dự kiến: [CẦN]\n", "G4", [(r"so nguoi phong van", "20")])[0]
    assert o2["loai"] == "moi_dung_vai" and o2["dien"] == "20"
    # ô hỏi người trả lời bằng văn bản: đúng vai
    o3 = _o(O_CAN_THIEP, "G7", [(r"ai thuc hien can thiep", "Điều dưỡng phụ trách")])[0]
    assert o3["loai"] == "moi_dung_vai"
    # báo cáo đếm loại mới ở mục ô lỗi máy
    assert GT.tom_tat_o([o, o2, o3])["dien_sai_kieu"] == 1


def test_nhan_dien_o_hoi_nguoi_va_ma_so():
    assert GT.hoi_nguoi_vai_tro("bo sung: ai thuc hien can thiep, kiem soat chat luong/tuan thu")
    assert GT.hoi_nguoi_vai_tro("nguoi phu trach nhap lieu") and GT.hoi_nguoi_vai_tro("vai tro trong nhom")
    assert not GT.hoi_nguoi_vai_tro("so nguoi phong van") and not GT.hoi_nguoi_vai_tro("bao nhieu thanh vien")
    assert not GT.hoi_nguoi_vai_tro("thoi gian luu")
    assert GT.la_ma_so_don_le("6") and GT.la_ma_so_don_le(" 2,5 ") and not GT.la_ma_so_don_le("6 tháng")


def _kich_ban_rct() -> dict:
    kb = dict(GL.KICH_BAN)
    kb.update(BTK.kich_ban_kho())
    kb.update(GCT.kich_ban_chan_thuc())
    return kb


#: từ khoá can thiệp RIÊNG của từng kịch bản phải có trong câu trả lời (đúng can thiệp, không chép chung)
DAU_HIEU = {"rct_nhi_phan": "tin nhắn", "rct_khong_kem": "gọi tái khám", "rct_cum": "mỗi phòng khám",
            "rct_kinh_te": "dữ liệu chi phí", "rct_hon_hop": "cấu phần định tính", "rct_chan_thuc": "ngẫu nhiên hoá"}


def test_moi_kich_ban_rct_co_cau_tra_loi_rieng_dung_can_thiep():
    kb = _kich_ban_rct()
    nhan = _o(O_CAN_THIEP, "G7")[0]["nhan"]
    da_thay = {}
    for ma, dau_hieu in DAU_HIEU.items():
        tl = list((kb[ma].get("ho_so_tron_vong") or {}).get("tra_loi_G7") or []) + list(GT.TRA_LOI_CHUNG)
        o = _o(O_CAN_THIEP, "G7", tl)[0]
        assert o["nhan"] == nhan and o["loai"] == "moi_dung_vai", (ma, o)
        assert dau_hieu in o["dien"] and not GT.la_ma_so_don_le(o["dien"]), (ma, o["dien"])
        da_thay[ma] = o["dien"]
    # kịch bản không kém hơn (điện thoại) không nhận câu về tin nhắn
    assert "tin nhắn" not in da_thay["rct_khong_kem"]
    assert len(set(da_thay.values())) == len(da_thay), "mỗi kịch bản một câu riêng"


def test_khong_quy_tac_chung_nao_chi_neo_duoi_nhan():
    """Quy tắc chung không được neo CHỈ vào đuôi nhãn («…$» không có «^» và không có cụm hỏi phía trước) — nhãn dài
    bị cắt 80 ký tự thì đuôi là chữ ngẫu nhiên."""
    xau = []
    for mau, _v in GT.TRA_LOI_CHUNG:
        for nhanh in mau.split("|"):
            if not nhanh.endswith("$") or nhanh.startswith("^"):
                continue
            loi = re.sub(r"(?:\\s\*|\\\]\?)*\$$", "", nhanh)  # bỏ «\s*», «\]?» và «$» ở cuối
            if not re.search(r"\\s|\s", loi):  # còn lại một chữ đơn ⇒ neo vào đuôi nhãn
                xau.append(nhanh)
    assert xau == [], xau


# ── ô bối cảnh Giới thiệu §1: từng rơi vào nhánh «nam\]?$» và bị điền «2»; nay bộ sinh lấy G1.background_problem

O_BOI_CANH = "[CẦN bổ sung: dịch tễ học/tỷ lệ mắc/gánh nặng kinh tế tại Việt Nam]"


def _meta_g1(d: Path, g1: dict) -> Path:
    import json

    d.mkdir(parents=True, exist_ok=True)
    (d / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": g1}}, ensure_ascii=False), encoding="utf-8",
                                       newline="\n")
    return d


def test_bo_sinh_dien_boi_canh_tu_g1_va_chot_bat_o_khi_co_du_kien(tmp_path):
    import g7_quality_gate as G7Q
    import run_g7_auto as G7

    bc = "Tỷ lệ kiểm soát huyết áp ngoại trú còn thấp, một phần do quên thuốc."
    d = _meta_g1(tmp_path, {"background_problem": bc})
    van, da = G7.lap_o_da_chot_g7(f"…khuyến cáo[1]. {O_BOI_CANH}.  ", d, "X")
    assert van == "…khuyến cáo[1]. Tỷ lệ kiểm soát huyết áp ngoại trú còn thấp, một phần do quên thuốc.  "
    assert "boi_canh" in da
    assert any("bối cảnh/gánh nặng" in x for x in G7Q.o_cho_co_du_kien(d, "X", O_BOI_CANH, design_code="rct"))
    # G1 chưa khai ⇒ ô là phần của tác giả (không phải lỗi bộ sinh), giả lập không điền «2»
    d2 = _meta_g1(tmp_path / "trong", {})
    assert not any("bối cảnh" in x for x in G7Q.o_cho_co_du_kien(d2, "X", O_BOI_CANH, design_code="rct"))
    assert _o(f"{O_BOI_CANH}\n", "G7")[0]["dien"] != "2"
