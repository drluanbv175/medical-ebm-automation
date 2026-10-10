# -*- coding: utf-8 -*-
"""G1-T4 (công cụ đo lường): hợp đồng đầu ra + kiểm máy cấp nhiệm vụ · điều phối KHAI nhiệm vụ có điều kiện (10/10).

Bác sĩ giao «Gộp và tiếp tục hoàn thiện từng Agent và từng điều phối». Đo 10/10: G1-T4 (`cong-cu-do-luong`, «khi đề tài
dùng thang đo/bộ câu hỏi») khai đầu ra là đề cương chung nên bảng trách nhiệm không bao giờ đòi sản phẩm riêng của nó
(phiếu CVI + nhật ký phỏng vấn nhận thức của `pha_phat_trien_cong_cu.py`); điều kiện của nó máy không suy được từ thiết
kế nên nhiệm vụ mãi «chưa xác định» — quy tắc 5 của mục 4b chỉ dặn điều phối «khai trong khối bàn giao», không máy nào
đọc lại. Ngoại tuyến, dữ liệu giả.
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
import hoi_dong_cong as HD  # noqa: E402
import pha_phat_trien_cong_cu as PCC  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "G1T4-THU"
LY_DO = "đề tài tự xây bộ câu hỏi hài lòng, đề cương mục 4.5.1 có pha I-CVI"


def _de_tai(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").write_text("# Đề cương\n", encoding="utf-8", newline="\n")
    return out


def _pha(out: Path, so_cg: int = 3, diem: dict | None = None) -> Path:
    thu = out / "pha_cong_cu"
    PCC.sinh_mau(["A1", "A2", "B1"], so_cg, thu)
    if diem:
        p = thu / "phieu_cvi.csv"
        dong = p.read_text(encoding="utf-8").splitlines()
        for muc, gia_tri in diem.items():
            dong = [(f"{muc},{gia_tri}" if d.split(",")[0] == muc else d) for d in dong]
        p.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return thu


# ── Kiểm máy G1-T4 ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_mau_dung_cong_cu_3_chuyen_gia_o_chua_cham_khong_la_loi(tmp_path):
    """Ô chưa chấm là việc của hội đồng chuyên gia — không quy cho agent."""
    out = _de_tai(tmp_path)
    _pha(out)
    assert HD._kiem_pha_cong_cu(out, STUDY) == []


def test_it_hon_3_chuyen_gia_bi_bat(tmp_path):
    out = _de_tai(tmp_path)
    _pha(out, so_cg=2)
    loi = HD._kiem_pha_cong_cu(out, STUDY)
    assert len(loi) == 1 and "2 chuyên gia < 3" in loi[0] and "PMID 17654487" in loi[0]


@pytest.mark.parametrize("diem, can", [
    ({"A1": "5,3,4"}, "không thuộc thang 1–4"),
    ({"A2": "x,3,4"}, "không thuộc thang 1–4"),
])
def test_diem_ngoai_thang_bi_bat(tmp_path, diem, can):
    out = _de_tai(tmp_path)
    _pha(out, diem=diem)
    loi = HD._kiem_pha_cong_cu(out, STUDY)
    assert any(x.startswith("phiếu CVI:") and can in x for x in loi), loi


def test_muc_trung_va_nhat_ky_thieu_cot_bi_bat(tmp_path):
    out = _de_tai(tmp_path)
    thu = _pha(out)
    (thu / "phieu_cvi.csv").write_text("muc,CG01,CG02,CG03\nA1,4,4,3\nA1,3,3,3\n", encoding="utf-8", newline="\n")
    (thu / "nhat_ky_phong_van_nhan_thuc.csv").write_text("ma_nguoi,muc,van_de\nNT01,A1,\n", encoding="utf-8",
                                                          newline="\n")
    loi = HD._kiem_pha_cong_cu(out, STUDY)
    assert any("mã mục trùng" in x for x in loi), loi
    assert any("thiếu cột: loai_van_de, de_xuat_sua" in x for x in loi), loi


def test_dau_ra_g1t4_la_san_pham_cua_cong_cu_that():
    nv = HD._nhiem_vu("G1", "G1-T4")
    assert "pha_cong_cu/phieu_cvi.csv" in nv["dau_ra"]
    assert "pha_cong_cu/nhat_ky_phong_van_nhan_thuc.csv" in nv["dau_ra"]
    assert "G1-T4" in HD.KIEM_NHIEM_VU
    # Chỉ nhánh phát triển/sửa đổi/dịch có pha CVI; thang chuẩn dùng NGUYÊN TRẠNG ⇒ điều phối khai «khong».
    assert "phát triển" in nv["dieu_kien"] and nv["dieu_kien"] not in HD._DIEU_KIEN_THIET_KE


def test_dieu_phoi_duoc_day_lenh_khai_ap_dung():
    for gate in HD.CONG:
        van = (ROOT / ".claude" / "agents" / f"{HD.dieu_phoi_cong(gate)}.md").read_text(encoding="utf-8")
        assert f"hoi_dong_cong.py khai-ap-dung --study <mã> --gate {gate} --nhiem-vu <NV>" in van, gate
    g1 = (ROOT / ".claude" / "agents" / "dieu-phoi-g1.md").read_text(encoding="utf-8")
    assert "Ở G1: G1-T4 `cong-cu-do-luong`" in g1


# ── khai_ap_dung ─────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ma, ly_do, can", [
    ("G1-T9", LY_DO, "không phải nhiệm vụ của cổng G1"),
    ("G1-T1", LY_DO, "không có điều kiện"),
    ("G1-T5", LY_DO, "suy từ thiết kế"),
    ("G1-T4", "có", "≥ 10 ký tự"),
    ("G1-T4", LY_DO + " — liên hệ 0912345678", "SĐT_VN"),  # bimat-mien: số giả để kiểm bộ quét PII
])
def test_khai_ap_dung_tu_choi_khong_ghi(tmp_path, ma, ly_do, can):
    out = _de_tai(tmp_path)
    p, loi = HD.khai_ap_dung("G1", ma, True, ly_do, out)
    assert p is None and any(can in x for x in loi), loi
    assert not (out / "hoi_dong" / "G1" / HD.TEP_KHAI_AP_DUNG).exists()


def test_khai_ap_dung_ghi_va_ghi_de_dung_nhiem_vu(tmp_path):
    out = _de_tai(tmp_path)
    p, loi = HD.khai_ap_dung("G1", "G1-T4", True, LY_DO, out)
    assert loi == [] and p == out / "hoi_dong" / "G1" / HD.TEP_KHAI_AP_DUNG
    v = json.loads(p.read_text(encoding="utf-8"))["G1-T4"]
    assert v["ap_dung"] is True and v["ly_do"] == LY_DO and v["khai_boi"] == "dieu-phoi-g1"
    assert v["dieu_kien"] == HD._nhiem_vu("G1", "G1-T4")["dieu_kien"] and v["thoi_diem"]
    HD.khai_ap_dung("G1", "G1-T4", False, "đề tài dùng thang đã chuẩn hoá có bản tiếng Việt", out)
    assert HD.doc_ap_dung("G1", out)["G1-T4"]["ap_dung"] is False
    p7, loi7 = HD.khai_ap_dung("G7", "G7-T2", True, "nộp tạp chí quốc tế tiếng Anh theo kế hoạch công bố", out)
    assert loi7 == [] and set(HD.doc_ap_dung("G7", out)) == {"G7-T2"}


def test_dieu_kien_thiet_ke_khong_bi_khai_tay_de_len():
    """JSON viết tay cho G1-T5 (điều kiện RCT) không thắng máy: thiết kế cohort ⇒ KHÔNG áp dụng."""
    nv = HD._nhiem_vu("G1", "G1-T5")
    khai = {"G1-T5": {"ap_dung": True}}
    assert HD._ap_dung(nv, "cohort", khai) is False and HD._ap_dung(nv, None, khai) is None
    nv4 = HD._nhiem_vu("G1", "G1-T4")
    assert HD._ap_dung(nv4, "rct", {"G1-T4": {"ap_dung": "co"}}) is None, "ap_dung phải là bool"
    assert HD._ap_dung(nv4, "rct", {"G1-T4": {"ap_dung": False}}) is False


# ── Bảng trách nhiệm dùng khai báo ──────────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def g1_dat(monkeypatch):
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G1"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G1_PROTOCOL_CORE", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})


def _g1t4(kq):
    return {n["ma"]: n for n in kq["nhiem_vu"]}["G1-T4"]


def test_chua_khai_la_chua_xac_dinh_khong_doi_dau_ra(tmp_path, g1_dat):
    kq = HD.trach_nhiem(STUDY, "G1", _de_tai(tmp_path))
    assert _g1t4(kq)["ap_dung"] is None and "G1-T4" in kq["nhiem_vu_chua_xac_dinh"]
    assert not [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G1-T4"]
    assert "khai-ap-dung --study G1T4-THU --gate G1" in HD.in_trach_nhiem(kq)


def test_khai_ap_dung_thi_doi_san_pham_cong_cu_va_kiem_may(tmp_path, g1_dat):
    out = _de_tai(tmp_path)
    HD.khai_ap_dung("G1", "G1-T4", True, LY_DO, out)
    kq = HD.trach_nhiem(STUDY, "G1", out)
    n = _g1t4(kq)
    assert n["ap_dung"] is True and n["khai_ap_dung"]["ly_do"] == LY_DO
    assert sorted(n["dau_ra_thieu"]) == ["pha_cong_cu/nhat_ky_phong_van_nhan_thuc.csv", "pha_cong_cu/phieu_cvi.csv"]
    viec = [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G1-T4"]
    assert viec and all(m["agent"] == "cong-cu-do-luong" and m["id"] == "G1-T4:dau-ra" for m in viec)
    assert "kiem_may" not in n, "thiếu tệp thì không ghi «đã kiểm máy»"
    assert kq["ket_luan"] == "AGENT_CON_VIEC" and "Điều phối đã khai áp dụng: G1-T4 ÁP DỤNG" in HD.in_trach_nhiem(kq)

    _pha(out, so_cg=2)
    kq = HD.trach_nhiem(STUDY, "G1", out)
    viec = [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G1-T4"]
    assert [m["id"] for m in viec] == ["G1-T4:kiem-may"] and "< 3" in viec[0]["viec"]


def test_khai_ap_dung_du_san_pham_hop_le_thi_g1t4_khong_con_viec(tmp_path, g1_dat):
    out = _de_tai(tmp_path)
    HD.khai_ap_dung("G1", "G1-T4", True, LY_DO, out)
    _pha(out, so_cg=6)
    kq = HD.trach_nhiem(STUDY, "G1", out)
    assert _g1t4(kq)["kiem_may"]["loi"] == []
    assert not [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G1-T4"]


def test_khai_khong_ap_dung_thi_khong_doi_gi(tmp_path, g1_dat):
    out = _de_tai(tmp_path)
    HD.khai_ap_dung("G1", "G1-T4", False, "đề tài dùng thang đã chuẩn hoá có bản tiếng Việt", out)
    kq = HD.trach_nhiem(STUDY, "G1", out)
    assert _g1t4(kq)["ap_dung"] is False and "G1-T4" not in kq["nhiem_vu_chua_xac_dinh"]
    assert not [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G1-T4"]


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_cli_khai_ap_dung(monkeypatch, tmp_path, capsys):
    out = _de_tai(tmp_path)
    monkeypatch.setattr(HD, "BASE", tmp_path)
    goc = ["khai-ap-dung", "--study", STUDY, "--gate", "G1", "--nhiem-vu"]
    assert HD.main(goc + ["G1-T4", "--ap-dung", "co", "--ly-do", LY_DO]) == 0
    assert "Đã ghi hoi_dong/G1/ap_dung_nhiem_vu.json — G1-T4: ÁP DỤNG" in capsys.readouterr().out
    assert HD.main(goc + ["G1-T5", "--ap-dung", "co", "--ly-do", LY_DO]) == 3
    assert "KHÔNG ghi" in capsys.readouterr().out and set(HD.doc_ap_dung("G1", out)) == {"G1-T4"}
    assert HD.main(["khai-ap-dung", "--study", "KHONG-CO", "--gate", "G1", "--nhiem-vu", "G1-T4", "--ap-dung", "co",
                    "--ly-do", LY_DO]) == 2
    assert not (tmp_path / "exports" / "KHONG-CO").exists(), "đề tài gõ sai không được tạo thư mục"
