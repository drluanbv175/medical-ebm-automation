"""G8 nối hợp đồng ô trống chung (03–04/10/2026).

Đo 03/10: G8-AUTO-04 (cổng CHẶN duy nhất về ô trống của bản thảo) chỉ nhận «[CẦN…]» ≤ 80 ký tự viết hoa ⇒ bản thảo
khuôn G7 còn «___», nhãn dài, «[cần …]», ô mẫu chung vẫn PASS_G8_REVIEW_RECORDED; bản nhận xét phản biện chép nguyên
mẫu (liệt kê đủ 4 mức khuyến nghị, không chọn) được tính là nhận xét thật; `_present('___')` là True. Đồng thời
không kế thừa báo nhầm cũ («agent» là thuật ngữ y khoa, «TODO»/«XXX» không ranh giới từ). Fixture dùng lại của
tests/test_g8_quality_gate.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import g8_quality_gate as G8Q  # noqa: E402
from test_g8_quality_gate import CLEAN_MANUSCRIPT, REVIEW_REPORT, _evaluate  # noqa: E402


def _ck(report, ma):
    return next(r for r in report["automatic_criteria"] + report.get("human_criteria", []) if r["id"] == ma)


# ── bản thảo ──────────────────────────────────────────────────────────────────────────────────────────────────────
NHAN_DAI = "[CẦN " + "x" * 120 + "]"


@pytest.mark.parametrize("o", ["[CẦN SỐ LIỆU]", "[cần bổ sung]", "[Cần kiểm chứng]", NHAN_DAI, "[CAN]", "[TODO]",
                               "[đơn vị]", "thuốc/can thiệp X", "Cỡ mẫu ___ người", "[Ước lượng hiệu quả]",
                               "CẦN KẾT QUẢ THẬT"])
def test_ban_thao_con_o_bi_g8_auto_04_chan(o):
    ban = CLEAN_MANUSCRIPT.replace("## Kết quả\n", f"## Kết quả\nĐoạn có {o} cần điền.\n")
    assert G8Q.manuscript_residues(ban), o
    r = _evaluate(manuscript_text=ban)
    assert _ck(r, "G8-AUTO-04")["status"] != "PASS" and r["status"] != G8Q.STATUS_REVIEWED, o


def test_ban_thao_sach_van_pass():
    assert G8Q.manuscript_residues(CLEAN_MANUSCRIPT) == []
    assert _ck(_evaluate(), "G8-AUTO-04")["status"] == "PASS"


@pytest.mark.parametrize("dong", ["| ___ | ___ |", "Tác nhân gây bệnh (agent) được xác định bằng PCR.",
                                  "Thuật ngữ TODOROVIC syndrome và mã KXXX1 không phải ô trống.",
                                  "Độ tuổi trung vị ... năm theo nhóm."])
def test_ban_thao_khong_bao_nham(dong):
    """Bộ dò chung KHÔNG kế thừa báo nhầm của luật vệt nội bộ («agent», TODO/XXX không ranh giới)."""
    ban = CLEAN_MANUSCRIPT.replace("## Kết quả\n", f"## Kết quả\n{dong}\n")
    assert G8Q.manuscript_residues(ban) == [], dong


def test_vet_noi_bo_todo_xxx_co_ranh_gioi_tu():
    ban = CLEAN_MANUSCRIPT.replace("## Kết quả\n", "## Kết quả\nThuật ngữ TODOROVIC và mã KXXX1.\n")
    assert G8Q.scan_internal_traces(ban) == []
    assert G8Q.scan_internal_traces(CLEAN_MANUSCRIPT + "\nTODO: viết lại đoạn này\n")
    # «agent» vẫn là luật CHẶN của doctrine binh-duyet.md (báo nhầm thuật ngữ y khoa ĐÃ BIẾT — bác sĩ quyết nới)


def test_duoi_sau_phu_luc_van_duoc_quet():
    ban = (CLEAN_MANUSCRIPT + "\n## PHỤ LỤC — CHECKLIST\n- mục nội bộ [CẦN]\n\n---\n"
           "[BẢN NHÁP TỰ ĐỘNG — DRAFT G7] chờ điền\n")
    assert any("BẢN NHÁP TỰ ĐỘNG" in x for x in G8Q.manuscript_residues(ban))
    chi_phu_luc = CLEAN_MANUSCRIPT + "\n## PHỤ LỤC — CHECKLIST\n- mục nội bộ [CẦN]\n"
    assert G8Q.manuscript_residues(chi_phu_luc) == []          # phụ lục kiểm tra nội bộ: bỏ như quy ước cũ


# ── gate_params.G8 ────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("v", ["___", "[TBD]", "[đơn vị]", "?", "-", "xxx", "[CẦN X]", "[can bo sung]", ["___"]])
def test_present_g8_khong_coi_o_trong_la_da_dien(v):
    assert G8Q._present(v) is False, v


def test_present_g8_gia_tri_that():
    assert G8Q._present("Claude Opus 5") is True and G8Q._present(["NCT01234567"]) is True


def test_ai_tools_o_trong_khong_con_qua_g8_auto_06():
    from test_g8_quality_gate import _meta
    r_that = _evaluate(meta=_meta())
    r_trong = _evaluate(meta=_meta(ai_tools="___", ai_purpose="___"))
    assert _ck(r_that, "G8-AUTO-06")["status"] == "PASS"
    assert _ck(r_trong, "G8-AUTO-06")["status"] != "PASS"


# ── bản nhận xét phản biện ────────────────────────────────────────────────────────────────────────────────────────
MAU_TRONG = REVIEW_REPORT.replace("SỬA NHỎ", "☐ CHẤP NHẬN ☐ SỬA NHỎ ☐ SỬA LỚN ☐ TỪ CHỐI")


def test_mau_chua_chon_khuyen_nghi_khong_tinh_la_nhan_xet():
    assert G8Q.review_report_issues(REVIEW_REPORT) == []
    van_de = G8Q.review_report_issues(MAU_TRONG)
    assert van_de and any("KHUYẾN NGHỊ" in v.upper() or "chọn" in v for v in van_de)
    assert _evaluate(review_report_text=MAU_TRONG)["status"] != G8Q.STATUS_REVIEWED


def test_tich_mot_muc_la_da_chon_tich_hai_muc_la_chua():
    mot = REVIEW_REPORT.replace("SỬA NHỎ", "☐ CHẤP NHẬN ☑ SỬA NHỎ ☐ SỬA LỚN ☐ TỪ CHỐI")
    hai = REVIEW_REPORT.replace("SỬA NHỎ", "☑ CHẤP NHẬN ☑ SỬA NHỎ ☐ SỬA LỚN ☐ TỪ CHỐI")
    assert G8Q.review_report_issues(mot) == []
    assert G8Q.review_report_issues(hai)


def test_ket_luan_de_ca_hai_lua_chon_va_o_mau():
    r = REVIEW_REPORT.replace("Sẵn sàng nộp.", "Sẵn sàng nộp / cần sửa thêm")
    assert r != REVIEW_REPORT
    assert any("KẾT LUẬN" in v for v in G8Q.review_report_issues(r))
    o_mau = REVIEW_REPORT + "\nBài: [Tên bài] — ngày [Ngày]\n"
    assert any("ô mẫu" in v for v in G8Q.review_report_issues(o_mau))


def test_trich_nguyen_van_o_trong_cua_ban_thao_khong_bi_tinh():
    r = REVIEW_REPORT.replace("- Rút gọn phần mở đầu.", "- Bảng 2 còn «___» và `[CẦN SỐ LIỆU]` — tác giả điền.")
    assert G8Q.review_report_issues(r) == []
