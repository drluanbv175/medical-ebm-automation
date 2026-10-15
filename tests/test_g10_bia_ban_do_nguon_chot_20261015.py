"""Hồi quy 15/10/2026: bìa Word và bản đồ nghiên cứu của đề cương G10 (C1a, gói ETHICS_SUBMISSION) còn ô «[CẦN…]».

Bìa đọc org_lines/authors/place_year nhưng thông tin PI điền ở G2 nằm trong khối `administrative`; ma trận truy xuất đọc
`exposure` nhưng phơi nhiễm đã chốt ở SAP §5. `bo_sung_tu_nguon_da_chot` nay lấp các khoá đó (chỉ khi trống).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import run_g10_assemble as A  # noqa: E402

MA = "de-tai-thu"
ADM = {"principal_investigator": "Bác sĩ Thử", "pi_title": "BS.CKI",
       "pi_unit": "Khoa Khám bệnh X, Trung tâm Y, Bệnh viện Z"}


def _thu_muc(tmp_path: Path) -> Path:
    (tmp_path / f"G4_A5_SAP_FINAL_{MA}.md").write_text(
        "### §5 PHÂN TÍCH ĐA BIẾN\n- **Exposure chính:** `thoigian_cho` (phút; mốc HIS).\n", encoding="utf-8",
        newline="\n")
    return tmp_path


def test_lap_bia_va_phoi_nhiem(tmp_path):
    meta = {"administrative": dict(ADM), "document_date": "2026-10-15"}
    da = A.bo_sung_tu_nguon_da_chot(meta, {}, _thu_muc(tmp_path))
    assert meta["exposure"] == "`thoigian_cho` (phút; mốc HIS) (SAP §5)"
    assert meta["org_lines"] == ["Bệnh viện Z", "Trung tâm Y", "Khoa Khám bệnh X"]
    assert meta["authors"] == "BS.CKI Bác sĩ Thử (chủ nhiệm đề tài)"
    assert meta["place_year"] == "Bệnh viện Z – 2026"
    assert {"exposure", "org_lines", "authors", "place_year"} <= set(da)
    bia = A.title_page_dict(MA, {"G0": {}}, meta)
    assert bia["org_lines"][0] == "Bệnh viện Z" and "[CẦN" not in bia["place_year"]
    assert not any("[CẦN" in d for d in bia["meta_lines"])


def test_khong_ghi_de_bia_da_khai(tmp_path):
    meta = {"administrative": dict(ADM), "org_lines": ["Đơn vị PI tự khai"], "authors": "Nhóm PI tự khai",
            "place_year": "TP. Hồ Chí Minh – 2026"}
    A.bo_sung_tu_nguon_da_chot(meta, {}, _thu_muc(tmp_path))
    assert meta["org_lines"] == ["Đơn vị PI tự khai"] and meta["authors"] == "Nhóm PI tự khai"
    assert meta["place_year"] == "TP. Hồ Chí Minh – 2026"


def test_khong_co_administrative_thi_khong_lap(tmp_path):
    meta: dict = {}
    A.bo_sung_tu_nguon_da_chot(meta, {}, _thu_muc(tmp_path))
    assert "org_lines" not in meta and "authors" not in meta and "place_year" not in meta
