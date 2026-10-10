# -*- coding: utf-8 -*-
"""G6-T3 bản diễn giải (số liệu · văn phong · bảng biểu) + G10-T3 sổ trạng thái RIÊNG mỗi đề tài (10/10/2026).

Bác sĩ quyết: «G6-T3 bảo đảm kết quả được diễn giải và trình bày tốt nhất (bao gồm số liệu, văn phong và bảng biểu)» và
«G10-T3 bảo đảm mỗi đề tài lưu trong thư mục riêng». Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import dien_giai_ket_qua as DG  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "DGST-THU"
KQ = "06_ket_qua/DGST-THU_table2_main_outcome.txt"
BAN = """# Diễn giải kết quả — DGST-THU

## 1. Kết quả chính

**Bảng 1.** Kết quả kết cục chính

| Kết cục | Thước đo | Ước lượng điểm | KTC 95% | p | Ý nghĩa lâm sàng | Nguồn kết quả |
|---|---|---|---|---|---|---|
| Tái nhập viện 30 ngày | RR | 0,85 | 0,72–0,98 | 0,041 | giảm tuyệt đối 3%, dưới ngưỡng 5% đã định | `{kq}` |

## 2. Ý nghĩa thống kê và ý nghĩa lâm sàng

Có ý nghĩa thống kê nhưng độ lớn hiệu ứng dưới ngưỡng ý nghĩa lâm sàng đã định trước.

## 3. Đối chiếu y văn

Phù hợp tổng quan trước (PMID 12345678).

## 4. Điểm mạnh và hạn chế

Hạn chế: thiết kế quan sát, nhiễu chưa đo.

## 5. Hàm ý thực hành và hướng nghiên cứu tiếp

Cần thử nghiệm ngẫu nhiên để kiểm chứng.

> Cần bác sĩ kiểm chứng.
""".replace("{kq}", KQ)


def _de_tai(tmp_path: Path, ban: str = BAN, nguon: str = "RR 0.8463 95%CI 0.7214 0.9811 p=0.0412\n") -> Path:
    out = tmp_path / "exports" / STUDY
    (out / "06_ket_qua").mkdir(parents=True)
    (out / KQ).write_text(nguon, encoding="utf-8", newline="\n")
    (out / f"G6_DIEN_GIAI_{STUDY}.md").write_text(ban, encoding="utf-8", newline="\n")
    return out


# ── G6-T3: khung + bản đạt ──────────────────────────────────────────────────────────────────────────────────────────
def test_khung_khong_ghi_de_va_chua_dat(tmp_path):
    out = tmp_path / "exports" / STUDY
    p = DG.sinh_mau(STUDY, out)
    loi = DG.kiem(STUDY, out)
    assert loi and any("[CẦN" in x for x in loi)
    with pytest.raises(DG.LoiDauVao):
        DG.sinh_mau(STUDY, out)
    assert p.read_text(encoding="utf-8").count("## ") == 5


def test_ban_day_du_dat(tmp_path):
    assert DG.kiem(STUDY, _de_tai(tmp_path), "cohort") == []


def test_thieu_tep_la_loi_dau_vao(tmp_path):
    with pytest.raises(DG.LoiDauVao):
        DG.kiem(STUDY, tmp_path)


# ── Số liệu ─────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cu, moi, can", [
    ("| 0,85 |", "| 0,86 |", "ước lượng 0,86 không có trong"),
    ("0,72–0,98", "0,72–0,99", "cận trên 0,99 không có trong"),
    ("| 0,85 | 0,72–0,98", "| 1,05 | 0,72–0,98", "nằm ngoài KTC 95%"),
    ("0,72–0,98", "0,72", "KTC 95% phải ghi hai cận"),
    ("| 0,041 |", "| 0,000 |", "ghi «< 0,001»"),
    ("| 0,041 |", "| 1,5 |", "không hợp lệ"),
    ("| 0,041 |", "| 0,0004 |", "< 0,001 — ghi «< 0,001»"),
    (f"`{KQ}`", "`06_ket_qua/khong_co.txt`", "không tồn tại"),
    (f"`{KQ}`", "`../ngoai.txt`", "«Nguồn kết quả» phải là tệp trong"),
    ("| 0,85 | 0,72–0,98", "| 0.85 | 0,72–0,98", "trộn dấu thập phân"),
])
def test_so_lieu_sai_bi_bat(tmp_path, cu, moi, can):
    assert BAN.count(cu) == 1, cu
    loi = DG.kiem(STUDY, _de_tai(tmp_path, BAN.replace(cu, moi)), "cohort")
    assert any(can in x for x in loi), loi


def test_nguon_ngoai_thu_muc_ket_qua_bi_bat_du_tep_co_that(tmp_path):
    """Tệp nguồn có thật nhưng nằm ngoài 06_ket_qua/ hoặc 06_phan_tich_R/output/ (vd tệp tự gõ ở gốc đề tài)."""
    out = _de_tai(tmp_path, BAN.replace(KQ, "tu_go/so_lieu.txt"))
    (out / "tu_go").mkdir()
    (out / "tu_go" / "so_lieu.txt").write_text("0.8463 0.7214 0.9811\n", encoding="utf-8", newline="\n")
    assert any("«Nguồn kết quả» phải là tệp trong" in x for x in DG.kiem(STUDY, out, "cohort"))


def test_p_duoi_0001_ghi_dung_thi_dat(tmp_path):
    assert DG.kiem(STUDY, _de_tai(tmp_path, BAN.replace("| 0,041 |", "| < 0,001 |")), "cohort") == []


def test_nguon_xlsx_doc_duoc(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    out = _de_tai(tmp_path, BAN.replace(KQ, "06_ket_qua/G6_results_main.xlsx"))
    wb = openpyxl.Workbook()
    wb.active.append(["RR", 0.8463, 0.7214, 0.9811])
    wb.save(out / "06_ket_qua" / "G6_results_main.xlsx")
    assert DG.kiem(STUDY, out, "cohort") == []


# ── Văn phong ───────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cau, thiet_ke, can", [
    ("Nghiên cứu đã chứng minh hiệu quả.", "rct", "đã chứng minh"),
    ("Kết quả chứng minh rằng can thiệp tốt.", "rct", "chứng minh rằng"),
    ("Có xu hướng có ý nghĩa ở nhóm nữ.", "rct", "xu hướng có ý nghĩa"),
    ("Kết quả gần có ý nghĩa.", "rct", "gần có ý nghĩa"),
    ("Kết quả rất có ý nghĩa thống kê.", "rct", "rất có ý nghĩa thống kê"),
    ("Khác biệt với p = 0,000.", "rct", "p = 0,000"),
    ("Hút thuốc gây ra tái nhập viện.", "cohort", "«gây ra»"),
    ("Đây là nguyên nhân chính.", "cross_sectional", "«là nguyên nhân»"),
])
def test_van_phong_qua_muc_bi_bat(tmp_path, cau, thiet_ke, can):
    ban = BAN.replace("Cần thử nghiệm ngẫu nhiên để kiểm chứng.", cau)
    loi = DG.kiem(STUDY, _de_tai(tmp_path, ban), thiet_ke)
    assert any(can in x for x in loi), loi


def test_ngon_ngu_nhan_qua_duoc_dung_voi_rct(tmp_path):
    ban = BAN.replace("Cần thử nghiệm ngẫu nhiên để kiểm chứng.", "Can thiệp gây ra giảm tái nhập viện.")
    assert DG.kiem(STUDY, _de_tai(tmp_path, ban), "rct") == []


def test_ham_y_lam_sang_y_van_han_che_bat_buoc(tmp_path):
    ban = (BAN.replace("Có ý nghĩa thống kê nhưng độ lớn hiệu ứng dưới ngưỡng ý nghĩa lâm sàng đã định trước.",
                       "Có ý nghĩa thống kê.")
           .replace("(PMID 12345678)", "").replace("Hạn chế: thiết kế", "Điểm yếu: thiết kế"))
    loi = DG.kiem(STUDY, _de_tai(tmp_path, ban), "cohort")
    assert any("mục 2" in x for x in loi) and any("mục 3" in x for x in loi) and any("mục 4" in x for x in loi), loi


# ── Bảng biểu ───────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cu, moi, can", [
    ("**Bảng 1.** Kết quả kết cục chính\n", "", "thiếu chú thích «Bảng N.»"),
    ("|---|---|---|---|---|---|---|\n", "", "thiếu hàng gạch"),
    ("| giảm tuyệt đối 3%, dưới ngưỡng 5% đã định |", "|  |", "có ô trống"),
    ("| RR | 0,85", "| RR | thêm | 0,85", "ô ≠"),
    ("| Kết cục | Thước đo |", "| Kết cục | Loại |", "thiếu cột: Thước đo"),
])
def test_bang_bieu_sai_bi_bat(tmp_path, cu, moi, can):
    assert BAN.count(cu) == 1, cu
    loi = DG.kiem(STUDY, _de_tai(tmp_path, BAN.replace(cu, moi)), "cohort")
    assert any(can in x for x in loi), loi


def test_muc_sai_thu_tu_va_thieu_muc(tmp_path):
    ban = BAN.replace("## 4. Điểm mạnh và hạn chế", "## 6. Phụ").replace("## 3. Đối chiếu y văn", "## 5x")
    loi = DG.kiem(STUDY, _de_tai(tmp_path, ban), "cohort")
    assert any("thiếu mục «4. Điểm mạnh" in x for x in loi) and any("thiếu mục «3." in x for x in loi)


def test_cli(monkeypatch, tmp_path, capsys):
    out = _de_tai(tmp_path)
    monkeypatch.setattr(DG, "BASE", tmp_path)
    assert DG.main(["kiem", "--study", STUDY, "--thiet-ke", "cohort", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["dat"] is True
    (out / f"G6_DIEN_GIAI_{STUDY}.md").write_text(BAN.replace("| 0,85 |", "| 0,86 |"), encoding="utf-8", newline="\n")
    assert DG.main(["kiem", "--study", STUDY, "--thiet-ke", "cohort"]) == 1
    assert DG.main(["kiem", "--study", "KHONG-CO"]) == 2


# ── Bảng trách nhiệm G6 dùng đúng hàm kiểm ──────────────────────────────────────────────────────────────────────────
def _g(monkeypatch, gate, thiet_ke="cohort"):
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG[gate]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": f"PASS_{gate}", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})


def test_trach_nhiem_g6_doi_ban_dien_giai_va_kiem_may(monkeypatch, tmp_path):
    _g(monkeypatch, "G6")
    out = _de_tai(tmp_path, BAN.replace("| 0,85 |", "| 0,86 |"))
    (out / f"G6_A7_ANALYSIS_SCRIPTS_{STUDY}.md").write_text("# A7\n", encoding="utf-8", newline="\n")
    (out / "G6_checkpoint.json").write_text("{}\n", encoding="utf-8", newline="\n")
    kq = HD.trach_nhiem(STUDY, "G6", out)
    viec = [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G6-T3"]
    assert [m["id"] for m in viec] == ["G6-T3:kiem-may"] and viec[0]["agent"] == "dien-giai-ket-qua"
    assert "0,86" in viec[0]["viec"]
    (out / f"G6_DIEN_GIAI_{STUDY}.md").unlink()
    kq = HD.trach_nhiem(STUDY, "G6", out)
    assert [m["id"] for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G6-T3"] == ["G6-T3:dau-ra"]


# ── G10-T3: sổ trạng thái RIÊNG mỗi đề tài ──────────────────────────────────────────────────────────────────────────
def _khoi(ngay: str, cong: str, nhan: str = f"{STUDY} — đề tài thử", loai: str = "nghiên cứu") -> str:
    return (f"## CHECKPOINT [{ngay}] — đề tài/ca: {nhan}\n- cong_vua_qua:   {cong}\n- ngay:           {ngay}\n"
            f"- loai_nhiem_vu:  {loai}\n- san_pham_vua_xong: hồ sơ cổng\n- danh_muc_🔴_con_lai: (không)\n"
            "- buoc_ke:        cổng kế — cần PI duyệt\n- agent_ghi:      so-cai-ghi-nho\n\n")


def _so(tmp_path: Path, *khoi: str, ledger=None) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    (out / f"SO_TRANG_THAI_{STUDY}.md").write_text(f"# Sổ trạng thái — {STUDY}\n\n" + "".join(khoi),
                                                     encoding="utf-8", newline="\n")
    if ledger is not None:
        (out / "approval_ledger.json").write_text(json.dumps(ledger), encoding="utf-8", newline="\n")
    return out


def test_so_hop_le_dat(tmp_path):
    out = _so(tmp_path, _khoi("2026-10-01", "G0"), _khoi("2026-10-05", "G2"),
              ledger=[{"gate_id": "G2", "decision": "APPROVED"}])
    assert HD._kiem_so_trang_thai(out, STUDY) == []


@pytest.mark.parametrize("khoi, ledger, can", [
    ((_khoi("2026-10-01", "G0", nhan="DE-TAI-KHAC — x"),), None, "không mở đầu bằng mã đề tài"),
    ((_khoi("2026-10-01", "G0", loai="lâm sàng"),), None, "loai_nhiem_vu phải là «nghiên cứu»"),
    ((_khoi("2026-10-01", "B"),), None, "không phải cổng G0–G10"),
    ((_khoi("2026-10-05", "G0"), _khoi("2026-10-01", "G1")), None, "lùi so với khối trước"),
    ((_khoi("2026-10-01", "G0"),), [{"gate_id": "G2", "decision": "APPROVED"}],
     "thiếu khối checkpoint cho cổng đã ký: G2"),
    ((), None, "chưa có khối"),
    ((_khoi("2026-13-40", "G0"),), None, "không có thật trên lịch"),
    ((_khoi("10/10/2026", "G0"),), None, "INVALID_DATE"),
])
def test_so_sai_bi_bat(tmp_path, khoi, ledger, can):
    loi = HD._kiem_so_trang_thai(_so(tmp_path, *khoi, ledger=ledger), STUDY)
    assert any(can in x for x in loi), loi


def test_ban_ghi_tu_choi_khong_doi_khoi(tmp_path):
    out = _so(tmp_path, _khoi("2026-10-01", "G0"), ledger=[{"gate_id": "G4", "decision": "REJECTED"}])
    assert HD._kiem_so_trang_thai(out, STUDY) == []


def test_trach_nhiem_g10_doi_so_rieng_trong_thu_muc_de_tai(monkeypatch, tmp_path):
    _g(monkeypatch, "G10")
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    kq = HD.trach_nhiem(STUDY, "G10", out)
    viec = [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G10-T3"]
    assert viec and viec[0]["agent"] == "so-cai-ghi-nho" and f"SO_TRANG_THAI_{STUDY}.md" in viec[0]["viec"]
    assert HD._nhiem_vu("G10", "G10-T3")["dau_ra"] == ["SO_TRANG_THAI_<mã>.md"]


def test_tai_lieu_day_so_rieng_va_ban_dien_giai():
    agents = ROOT / ".claude" / "agents"
    for ten in ("so-cai-ghi-nho.md", "dieu-phoi-nghien-cuu.md", "_SO-TRANG-THAI-CHECKPOINT.md"):
        assert "exports/<mã>/SO_TRANG_THAI_<mã>.md" in (agents / ten).read_text(encoding="utf-8"), ten
    dg = (agents / "dien-giai-ket-qua.md").read_text(encoding="utf-8")
    assert "tools/dien_giai_ket_qua.py mau --study <mã>" in dg and "G6_DIEN_GIAI_<mã>.md" in dg
    for cot in DG.COT_BANG_CHINH:
        assert cot in dg, cot
