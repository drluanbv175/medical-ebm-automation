"""Gói rà khuôn SAP cho thống kê viên (tools/goi_ra_khuon_sap.py, 23/11/2026).

Luật được canh:
  * Mỗi thiết kế/biến thể (8 mã + cụm, không kém hơn, ghép cặp) một trang; nội dung là câu NGUYÊN VĂN Phần 3 của SAP ví
    dụ: §4 họ mô hình, dòng KTC (không lấy hàng bảng giả §11), §6 dữ liệu thiếu, dòng biến cố hiếm, §9 độ nhạy, mỗi PMID
    một dòng.
  * Hạng mục khuôn không có ⇒ ghi rõ «không có dòng nào», không bịa.
  * Cột thống kê viên để TRỐNG (ô chưa đánh dấu, dòng chấm); không có nhận xét máy.
  * Mã băm SAP nguồn trong mục lục và trên trang; thiếu SAP nguồn ⇒ trang được liệt kê thiếu, mã 1.
  * Thư mục gói trong repo ⇒ từ chối (mã 3).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")

from tools import goi_ra_khuon_sap as GRS  # noqa: E402

SAP_RCT = """# A5, SAP FINAL
## PHẦN 1, THÔNG TIN ĐỀ TÀI
- Thiết kế: rct
## PHẦN 3, SAP 15 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH
- **Quần thể:** ITT
### §4 PHÂN TÍCH CHÍNH
- **Phương pháp:** Hồi quy Poisson với sai số chuẩn robust → RR
- **Estimand chính (ICH E9(R1); Kahan BC et al. BMJ 2024, PMID 38262663)**
- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc
### §5 PHÂN TÍCH ĐA BIẾN
- **Biến cố hiếm:** hồi quy logistic Firth (KTC hợp lý phạt hồ sơ)
### §6 DỮ LIỆU THIẾU
- **Chiến lược:** Multiple Imputation (MI, m=20)
### §9 PHÂN TÍCH ĐỘ NHẠY
- Per-protocol (CONSORT 2010 E&E, PMID 20332511)
### §11 DUMMY TABLES (Khung bảng kết quả)
| Kết cục | N (%) | 95%CI | p |
|---|---|---|---|
*Ghi chú trình bày bảng: KTC 95% ghi trong ngoặc*
### §12 ALPHA + POWER
| α | 0,05 | 95%CI hai phía |
- Alpha 0,05 hai phía
## PHẦN 4, THAY ĐỔI SAU KHI KHÓA
- PMID 99999999 ngoài Phần 3 không được lấy
"""
SAP_DINH_TINH = """## PHẦN 3, SAP 12 MỤC CUỐI
### §4 PHÂN TÍCH CHÍNH
- **Phương pháp:** Phân tích chủ đề (Braun & Clarke)
### §6 BÃO HÒA DỮ LIỆU (thay Dữ liệu thiếu, không áp dụng cho định tính)
- Dừng khi không xuất hiện mã mới
### §9 TRUSTWORTHINESS (thay Phân tích độ nhạy)
- Kiểm tra thành viên
## PHẦN 4, X
"""


def _nguon(tmp_path: Path, chi: tuple = ("rct_nhi_phan", "dinh_tinh")) -> Path:
    goc = tmp_path / "gia_lap"
    for kb in chi:
        study = f"ZZCANARY-{kb.upper()}"
        d = goc / kb / "repo" / "exports" / study
        d.mkdir(parents=True)
        (d / f"G4_A5_SAP_FINAL_{study}.md").write_text(SAP_DINH_TINH if kb == "dinh_tinh" else SAP_RCT,
                                                        encoding="utf-8", newline="\n")
    return goc


def test_danh_muc_du_8_thiet_ke_va_3_bien_the() -> None:
    assert len(GRS.DANH_MUC) == 11
    assert {tk for _m, _k, tk, _n in GRS.DANH_MUC} == {"rct", "cohort", "case_control", "cross_sectional",
                                                       "diagnostic", "prediction", "sr_ma", "qualitative"}
    assert {"rct_khong_kem", "rct_cum", "case_control_ghep_cap"} <= {m for m, *_ in GRS.DANH_MUC}


def test_trich_hang_muc_nguyen_van() -> None:
    h = GRS.trich_hang_muc(SAP_RCT)
    assert h["mo_hinh"][0] == "§4 PHÂN TÍCH CHÍNH"
    assert "Phương pháp: Hồi quy Poisson với sai số chuẩn robust → RR" in h["mo_hinh"]
    assert "Trình bày: ước lượng + 95%CI; không báo p-value đơn độc" in h["ktc"]
    assert not any("|" in x for x in h["ktc"]), "hàng bảng (§11, §12) không phải câu phương pháp KTC"
    assert not any("Ghi chú trình bày bảng" in x for x in h["ktc"]), "§11 là khung bảng giả — không lấy"
    assert h["hiem"] == ["Biến cố hiếm: hồi quy logistic Firth (KTC hợp lý phạt hồ sơ)"]
    assert h["thieu"] == ["§6 DỮ LIỆU THIẾU", "Chiến lược: Multiple Imputation (MI, m=20)"]
    assert h["do_nhay"][0] == "§9 PHÂN TÍCH ĐỘ NHẠY"
    pm = [x.split(" — ")[0] for x in h["pmid"]]
    assert pm == ["PMID 38262663", "PMID 20332511"], "mỗi PMID một dòng, chỉ trong Phần 3"


def test_hang_muc_khong_co_thi_ghi_ro(tmp_path: Path) -> None:
    h = GRS.trich_hang_muc(SAP_DINH_TINH)
    assert h["ktc"] == [] and h["hiem"] == [] and h["pmid"] == []
    assert h["thieu"][0].startswith("§6 BÃO HÒA DỮ LIỆU"), "giữ đúng tiêu đề §6 của thiết kế"
    ml = GRS.dung_goi(_nguon(tmp_path), tmp_path / "goi", pdf=False)
    dt = next(t for t in ml["trang"] if t["ma"] == "qualitative")
    assert set(dt["hang_muc_trong"]) == {"ktc", "hiem", "pmid"}
    bang = docx.Document(str(tmp_path / "goi" / dt["tep_docx"])).tables[0]
    o = {r.cells[0].text: r.cells[1].text for r in bang.rows[1:]}
    assert o["Khoảng tin cậy"] == GRS.KHONG_CO and o["Căn cứ PMID"] == GRS.KHONG_CO


def test_trang_word_cot_thong_ke_vien_de_trong_va_co_ma_bam(tmp_path: Path) -> None:
    nguon = _nguon(tmp_path)
    ml = GRS.dung_goi(nguon, tmp_path / "goi", pdf=False)
    t = next(x for x in ml["trang"] if x["ma"] == "rct")
    sap = next(nguon.glob("rct_nhi_phan/repo/exports/*/G4_A5_SAP_FINAL_*.md"))
    assert t["sha256"] == hashlib.sha256(sap.read_bytes()).hexdigest()
    d = docx.Document(str(tmp_path / "goi" / t["tep_docx"]))
    bang = d.tables[0]
    assert [r.cells[0].text for r in bang.rows] == ["Hạng mục"] + [n for _k, n in GRS.HANG_MUC]
    for r in bang.rows[1:]:
        assert r.cells[2].text == "\n".join(GRS.O_THONG_KE_VIEN), "cột thống kê viên phải để trống"
        assert "☑" not in r.cells[2].text and "☒" not in r.cells[2].text
    van = "\n".join(p.text for p in d.paragraphs)
    assert t["sha256"] in van and "rct_nhi_phan" in van and "Phương pháp: Hồi quy Poisson" in van
    assert "Chữ ký: ……" in van and "Họ và tên: ……" in van


def test_thieu_nguon_thi_liet_ke_va_ma_1(tmp_path: Path, capsys) -> None:
    nguon = _nguon(tmp_path)
    ma = GRS.main(["--nguon", str(nguon), "--ra", str(tmp_path / "goi"), "--khong-pdf"])
    assert ma == 1
    ml = json.loads((tmp_path / "goi" / "MUC_LUC.json").read_text(encoding="utf-8"))
    assert len(ml["thieu_nguon"]) == 9 and {x["kich_ban"] for x in ml["thieu_nguon"]} >= {"rct_cum", "chan_doan"}
    hd = (tmp_path / "goi" / "HUONG_DAN_RA_KHUON_SAP.md").read_text(encoding="utf-8")
    assert "Trang chưa dựng" in hd and "rct_cum" in hd and "GIA_LAP_DEN_CONG=G4" in hd
    assert "không ghi đánh giá thay thống kê viên" in hd
    assert not (tmp_path / "goi" / "03_RA_KHUON_SAP_rct_cum.docx").exists()


def test_du_nguon_thi_ma_0(tmp_path: Path) -> None:
    nguon = _nguon(tmp_path, chi=tuple(kb for _m, kb, _t, _n in GRS.DANH_MUC))
    assert GRS.main(["--nguon", str(nguon), "--ra", str(tmp_path / "goi"), "--khong-pdf"]) == 0
    assert len(list((tmp_path / "goi").glob("*_RA_KHUON_SAP_*.docx"))) == 11


def test_tu_choi_thu_muc_goi_trong_repo(tmp_path: Path) -> None:
    import shutil

    nguon = _nguon(tmp_path)
    dich = ROOT / "state" / "_khong_duoc_ghi_goi_ra"  # đường dẫn riêng của test — dọn trước và sau
    shutil.rmtree(dich, ignore_errors=True)
    try:
        assert GRS.main(["--nguon", str(nguon), "--ra", str(dich)]) == 3
        assert not dich.exists(), "không được ghi gói rà vào trong repo"
    finally:
        shutil.rmtree(dich, ignore_errors=True)
    assert GRS.main(["--ra", str(tmp_path / "goi")]) == 3
