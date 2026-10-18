# -*- coding: utf-8 -*-
"""Luật kiểm dữ liệu chéo trường `_luat-dq.csv` + ghi chú từ điển gộp Field Annotation — 18/10/2026 (hội đồng G3 C1a,
chấm lại G3-DG-20261018T063841-8490f642: G3-T3 RQ5 «luật logic chỉ có dạng văn xuôi», RQ2 «Field Note hiện ngay dưới
ô nhập — dời tài liệu nội bộ sang Field Annotation»).

Test chốt: ① `_kiem_crf` bắt luật DQ tham chiếu biến không có, mã checkbox không có trong danh sách lựa chọn, mã trong
ngoặc ở trường không phải checkbox, mức độ sai, mã luật trùng, lệch ngoặc, thiếu cột; tệp vắng thì không kiểm;
② bảng truy xuất nguồn gốc câu hỏi giữ phần chữ của Field Annotation (bỏ action tag).
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402
import pha_phat_trien_cong_cu as PCC  # noqa: E402
import run_g5_auto as G5  # noqa: E402

STUDY = "LUAT-DQ-THU"
COT = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
       "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
       "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
       "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
       "Matrix Ranking?", "Field Annotation"]
HOP_LE = [("DQ01", "truy_van", "Câu 1 = 2 mà câu 2 khác 7", "[co_yc] = '2' and [dung_bs] <> '7'", "phiếu"),
          ("DQ02", "chan", "Chọn quá 2 lý do", "([ly_do(1)] + [ly_do(2)] + [ly_do(3)]) > 2", "phiếu")]


def _bo_bien(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    dong = [
        {"Variable / Field Name": "record_id", "Form Name": "phieu", "Field Type": "text", "Field Label": "Mã phiếu",
         "Required Field?": "y"},
        {"Variable / Field Name": "co_yc", "Form Name": "phieu", "Field Type": "radio", "Field Label": "Có yêu cầu",
         "Choices, Calculations, OR Slider Labels": "1, Có | 2, Không", "Required Field?": "y"},
        {"Variable / Field Name": "dung_bs", "Form Name": "phieu", "Field Type": "radio", "Field Label": "Đúng bác sĩ",
         "Choices, Calculations, OR Slider Labels": "1, Có | 2, Không | 7, Không áp dụng"},
        {"Variable / Field Name": "ly_do", "Form Name": "phieu", "Field Type": "checkbox", "Field Label": "Lý do",
         "Choices, Calculations, OR Slider Labels": "1, A | 2, B | 3, C"},
    ]
    with (out / G5.BO_BIEN_RIENG_TEN_FILE).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT)
        w.writeheader()
        w.writerows(dong)


def _luat(out: Path, dong=HOP_LE, cot=HD.COT_LUAT_DQ) -> None:
    with (out / HD.LUAT_DQ_TEN_FILE).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cot)
        w.writerows(dong)


def _loi_dq(out: Path) -> list:
    return [x for x in HD._kiem_crf(out, STUDY) if x.startswith(("luật DQ", HD.LUAT_DQ_TEN_FILE))]


def test_khong_co_tep_thi_khong_kiem_va_luat_hop_le_thi_sach(tmp_path):
    _bo_bien(tmp_path)
    assert HD._kiem_crf(tmp_path, STUDY) == []
    _luat(tmp_path)
    assert HD._kiem_crf(tmp_path, STUDY) == []


def test_bat_bien_khong_co_va_ma_checkbox_sai(tmp_path):
    _bo_bien(tmp_path)
    _luat(tmp_path, HOP_LE + [("DQ03", "chan", "x", "[khong_co] = '1'", "y"),
                              ("DQ04", "chan", "x", "[ly_do(9)] = '1'", "y"),
                              ("DQ05", "chan", "x", "[co_yc(1)] = '1'", "y")])
    loi = " | ".join(_loi_dq(tmp_path))
    assert "DQ03: [khong_co] không có trong bộ biến" in loi
    assert "DQ04: [ly_do(9)] — mã không có trong danh sách lựa chọn" in loi
    assert "DQ05: [co_yc(1)] — chỉ trường checkbox" in loi
    assert "DQ01" not in loi and "DQ02" not in loi


def test_bat_muc_do_ma_trung_lech_ngoac_va_thieu_cot(tmp_path):
    _bo_bien(tmp_path)
    _luat(tmp_path, HOP_LE + [("DQ01", "chan", "x", "[co_yc] = '1'", "y"),
                              ("DQ06", "cam", "x", "[co_yc] = '1'", "y"),
                              ("DQ07", "chan", "x", "([co_yc] = '1'", "y")])
    loi = " | ".join(_loi_dq(tmp_path))
    assert "DQ01: ma_luat trống hoặc trùng" in loi
    assert "DQ06: muc_do phải là chan/truy_van" in loi
    assert "DQ07: biểu thức trống hoặc lệch ngoặc" in loi
    _luat(tmp_path, [("DQ01", "chan", "[co_yc] = '1'")], cot=("ma_luat", "muc_do", "bieu_thuc_redcap"))
    assert any("thiếu cột" in x for x in _loi_dq(tmp_path))


def test_ghi_chu_tu_dien_gop_annotation_bo_action_tag(tmp_path):
    td = tmp_path / "td.csv"
    td.write_text("Variable / Field Name,Section Header,Field Label,Field Note,Field Annotation\n"
                  "A1,Phần A,Câu A1,Bỏ trống ⇒ 9,@NOMISSING Nhãn theo phiếu gốc (Phụ lục C)\n"
                  "A2,,Câu A2,,\n", encoding="utf-8", newline="\n")
    p = PCC.sinh_truy_xuat(["A1", "A2"], td, tmp_path / "o")
    with open(p, encoding="utf-8") as f:
        ds = {d["muc"]: d for d in csv.DictReader(f)}
    assert ds["A1"]["ghi_chu_tu_dien"] == "Bỏ trống ⇒ 9 · Nhãn theo phiếu gốc (Phụ lục C)"
    assert "@" not in ds["A1"]["ghi_chu_tu_dien"] and ds["A2"]["ghi_chu_tu_dien"] == ""
    assert PCC._ghi_chu_tu_dien("", "@MAXCHECKED=2") == "" and PCC._ghi_chu_tu_dien(None, None) == ""
