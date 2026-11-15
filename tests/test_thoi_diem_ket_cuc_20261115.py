"""Trục `thoi_diem_ket_cuc` — chữ T của PICO(T) (15/11/2026, «Tiếp tục vấn đề còn lại» sau kiểm toàn hệ 12 bước).

Thời điểm đo kết cục chính G0 ↔ G1 ↔ TRDS 19 ↔ SAP §2. Kèm hồi quy: `_ket_cuc_chinh_sap` nhận «**Kết cục chính (MT1):**»
(SAP BTM từng lặng lẽ rơi khỏi trục kết cục chính). Mỗi test khoá một hành vi.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import nhat_quan_xuyen_cong as NQ  # noqa: E402

CUA_SO = "Cửa sổ hồi cứu 12 tháng: 01/01/2026–31/12/2026"


def _sap(kc: str, thoi_diem: str = "") -> str:
    dong = f"- **Thời điểm đo:** {thoi_diem}\n" if thoi_diem else ""
    return f"# SAP\n\n### §2 KẾT CỤC\n\n- **Kết cục chính:** {kc}\n{dong}\n### §3 MÔ TẢ\n\n- x\n"


def _meta(g0: str = "", g1: str = "") -> dict:
    return {"gate_params": {"G0": {"primary_outcome_timepoint": g0},
                            "G1": {"primary_outcome": {"name": "Kết cục X", "timepoint": g1}}}}


def test_moc_thoi_gian():
    assert NQ.moc_thoi_gian(CUA_SO) == (frozenset({"12 tháng"}), frozenset({"01/01", "31/12", "2026"}))
    assert NQ.moc_thoi_gian("trong 01/01–31/12/2026, cửa sổ 12 tháng") == NQ.moc_thoi_gian(CUA_SO)
    assert NQ.moc_thoi_gian("ADA 2026, PMID 41358881, mục 4.3.1") == (frozenset(), frozenset())


def test_cung_moc_la_khop():
    g1 = "Một khoảng cắt ngang: cửa sổ 12 tháng 01/01/2026–31/12/2026"
    sap = _sap("Tỷ lệ X trong cửa sổ 12 tháng — 01/01–31/12/2026")
    kq = NQ.truc_thoi_diem_ket_cuc(_meta(CUA_SO, g1), {"19": {"timepoint": CUA_SO}}, sap)
    assert kq["muc"] == NQ.MUC_KHOP and len(kq["nguon"]) == 4


def test_khoang_thoi_gian_khac_nhau_la_lech_mem():
    kq = NQ.truc_thoi_diem_ket_cuc(_meta("Tử vong trong 30 ngày", "Tử vong trong 90 ngày"), {}, "")
    assert kq["muc"] == NQ.MUC_LECH_MEM and "khoảng thời gian khác nhau" in kq["ghi_chu"]


def test_noi_co_moc_noi_khong_la_can_xem():
    kq = NQ.truc_thoi_diem_ket_cuc(_meta(CUA_SO, "Đo một lần tại lượt khám"), {}, "")
    assert kq["muc"] == NQ.MUC_CAN_XEM and "G1 không nêu mốc" in kq["ghi_chu"]


def test_khong_moc_so_trung_tu():
    g0 = "Đo một lần ngay sau khi hoàn thành quy trình khám"
    assert NQ.truc_thoi_diem_ket_cuc(_meta(g0, g0 + " — chờ thanh toán"), {}, "")["muc"] == NQ.MUC_KHOP
    assert NQ.truc_thoi_diem_ket_cuc(_meta(g0, "Phỏng vấn qua điện thoại tuần kế tiếp"), {}, "")["muc"] != NQ.MUC_KHOP


def test_sap_thieu_thoi_diem_la_can_xem_them_dong_la_khop():
    g0 = "Đo một lần ngay sau khi hoàn thành quy trình khám"
    meta = _meta(g0, g0)
    kq = NQ.truc_thoi_diem_ket_cuc(meta, {}, _sap("Mức hài lòng chung (biến G1)"))
    assert kq["muc"] == NQ.MUC_CAN_XEM and "SAP §2 chưa nêu thời điểm" in kq["ghi_chu"]
    kq = NQ.truc_thoi_diem_ket_cuc(meta, {}, _sap("Mức hài lòng chung (biến G1)", g0))
    assert kq["muc"] == NQ.MUC_KHOP and any(n["cong"] == "G4" for n in kq["nguon"])


def test_mot_noi_la_chua_du():
    assert NQ.truc_thoi_diem_ket_cuc(_meta(CUA_SO), {}, "")["muc"] == NQ.MUC_CHUA_DU


def test_ket_cuc_chinh_sap_nhan_nhan_muc_tieu():
    sap = "# SAP\n\n### §2 KẾT CỤC\n\n- **Kết cục chính (MT1):** Được xét nghiệm đủ UACR (biến XN_DU)\n\n### §3\n"
    assert NQ._ket_cuc_chinh_sap(sap) == "Được xét nghiệm đủ UACR (biến XN_DU)"


def test_truc_co_trong_doi_chieu_va_trach_nhiem_cong(tmp_path):
    for _p in (str(ROOT),):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from tests.test_dieu_phoi_thong_nhat_g0g10_20261004 import STUDY, _de_tai, _muc, _sua_meta

    out = _de_tai(tmp_path)
    _sua_meta(out, lambda m: (m["gate_params"]["G0"].update({"primary_outcome_timepoint": "30 ngày sau nhập viện"}),
                              m["gate_params"]["G1"]["primary_outcome"].update({"timepoint": "90 ngày sau nhập viện"})))
    assert _muc(NQ.doi_chieu(out, STUDY), "thoi_diem_ket_cuc")["muc"] == NQ.MUC_LECH_MEM
    assert NQ.TRUC_THEO_CONG["thoi_diem_ket_cuc"] == ("G0", "G1", "G2", "G4", "G10")


def test_dinh_tinh_khong_doi_sap_neu_thoi_diem():
    g0 = "Phỏng vấn sâu một lần sau khi người bệnh kết thúc đợt điều trị"
    sap = _sap("Trải nghiệm của người bệnh về quá trình điều trị (hiện tượng nghiên cứu)")
    assert NQ.truc_thoi_diem_ket_cuc(_meta(g0, g0), {}, sap, thiet_ke="qualitative")["muc"] == NQ.MUC_KHOP
    assert NQ.truc_thoi_diem_ket_cuc(_meta(g0, g0), {}, sap, thiet_ke="cohort")["muc"] == NQ.MUC_CAN_XEM
