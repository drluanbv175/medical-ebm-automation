# -*- coding: utf-8 -*-
"""Cột «Field Annotation» của bộ biến riêng tới được từ điển REDCap của G5 — 17/10/2026 (hội đồng G3 C1a).

Hội đồng G3 trả về sửa bộ biến C1a vì câu 13 «chọn tối đa 2» không có luật chặn; thêm `@MAXCHECKED=2` vào Field
Annotation thì `generate_csv` vẫn luôn ghi cột này rỗng ⇒ luật mất khi sinh từ điển G5. Test chốt:
① bộ nạp mang Field Annotation ở phần tử thứ 14; ② generate_csv ghi đúng giá trị đó; ③ bundle (12 trường) và record_id
tự chèn vẫn ghi rỗng, không vỡ. Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_g5_auto as G5A  # noqa: E402

COT = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
       "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
       "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
       "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
       "Matrix Ranking?", "Field Annotation"]


def _bo_bien(out_dir: Path, co_record_id: bool = True) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dong = ([{"Variable / Field Name": "record_id", "Form Name": "phieu", "Field Type": "text",
              "Field Label": "Mã phiếu"}] if co_record_id else [])
    dong.append({"Variable / Field Name": "lydo_chon", "Form Name": "phieu", "Field Type": "checkbox",
                 "Field Label": "Lý do chọn (tối đa 2)",
                 "Choices, Calculations, OR Slider Labels": "1, A | 2, B | 3, C",
                 "Field Annotation": " @MAXCHECKED=2 "})
    with (out_dir / G5A.BO_BIEN_RIENG_TEN_FILE).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT)
        w.writeheader()
        w.writerows(dong)


def _doc(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as f:
        return {r["Variable / Field Name"]: r["Field Annotation"] for r in csv.DictReader(f)}


def test_bo_nap_va_tu_dien_g5_giu_field_annotation(tmp_path):
    out = tmp_path / "S"
    _bo_bien(out)
    rows = G5A.nap_bo_bien_rieng(out, "S")
    assert {r[0]: r[13] for r in rows} == {"record_id": "", "lydo_chon": "@MAXCHECKED=2"}
    path, _ = G5A.generate_csv("S", out, rows)
    assert _doc(path) == {"record_id": "", "lydo_chon": "@MAXCHECKED=2"}


def test_record_id_tu_chen_va_bundle_ghi_rong(tmp_path):
    out = tmp_path / "T"
    _bo_bien(out, co_record_id=False)
    rows = G5A.nap_bo_bien_rieng(out, "T")
    assert rows[0][0] == "record_id" and len(rows[0]) == 14 and rows[0][13] == ""
    rows_b, _ = G5A.build_redcap_rows("cohort", "Tăng huyết áp")
    path, _ = G5A.generate_csv("B", tmp_path, rows_b)
    assert set(_doc(path).values()) == {""}
