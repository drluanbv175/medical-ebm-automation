"""Xác nhận «cùng một kết cục» không hết hiệu lực khi cổng sau chỉ CHÉP NGUYÊN VĂN mô tả đã xác nhận (15/11/2026).

Chạy G2 cho BTM: chủ nhiệm đã xác nhận {G0, G1} (dấu ea600fdb…); TRDS mục 19 chép nguyên văn G1 ⇒ dấu cả tập đổi ⇒ trục
`ket_cuc_chinh` từng rơi về LỆCH MỀM. Diễn đạt MỚI vẫn phải làm xác nhận hết hiệu lực. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import nhat_quan_xuyen_cong as NQ  # noqa: E402

G0 = {"cong": "G0", "noi": "G0.primary_outcome", "gia_tri": "Tỷ lệ được xét nghiệm đủ UACR trong 12 tháng"}
G1 = {"cong": "G1", "noi": "G1.primary_outcome", "gia_tri": "Được xét nghiệm đủ UACR (biến XN_DU)"}


def _meta(dau: str) -> dict:
    return {"gate_params": {"G10": {"xac_nhan_ket_cuc_chinh": {
        "giai_trinh": "Chủ nhiệm xác nhận cùng một kết cục, khác diễn đạt", "reviewed_at": "2026-11-15T07:41:40+07:00",
        "dau_van_tay": dau}}}}


DAU_CU = NQ.dau_van_tay_ket_cuc([G0, G1])


def test_dau_dung_tap_van_hop_le():
    assert NQ._xac_nhan_ket_cuc(_meta(DAU_CU), DAU_CU, [G0, G1])[0] is True


def test_cong_moi_chep_nguyen_van_giu_hieu_luc():
    g2 = {"cong": "G2", "noi": "TRDS mục 19", "gia_tri": "Được  xét nghiệm đủ UACR (biến XN_DU) "}
    nguon = [G0, G1, g2]
    ok, ly_do = NQ._xac_nhan_ket_cuc(_meta(DAU_CU), NQ.dau_van_tay_ket_cuc(nguon), nguon)
    assert ok is True and ly_do.startswith("[G2 chép nguyên văn")


def test_cong_moi_dien_dat_khac_het_hieu_luc():
    g2 = {"cong": "G2", "noi": "TRDS mục 19", "gia_tri": "Được xét nghiệm đủ UACR và eGFR (biến XN_DU)"}
    nguon = [G0, G1, g2]
    ok, ly_do = NQ._xac_nhan_ket_cuc(_meta(DAU_CU), NQ.dau_van_tay_ket_cuc(nguon), nguon)
    assert ok is False and "mô tả đã đổi" in ly_do


def test_khong_truyen_nguon_giu_hanh_vi_cu():
    nguon = [G0, G1, dict(G1, cong="G2", noi="TRDS mục 19")]
    assert NQ._xac_nhan_ket_cuc(_meta(DAU_CU), NQ.dau_van_tay_ket_cuc(nguon))[0] is False


def test_truc_ket_cuc_chinh_qua_doi_chieu(tmp_path):
    from datetime import datetime, timedelta

    for _p in (str(ROOT),):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from tests.test_dieu_phoi_thong_nhat_g0g10_20261004 import STUDY, _de_tai, _muc, _sua_meta

    sap = "Điểm hài lòng tổng thể khi rời phòng khám"
    out = _de_tai(tmp_path, kc_g0="Mức hài lòng chung của người bệnh", kc_sap=sap)
    dau = NQ.dau_van_tay_ket_cuc(_muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["nguon"])
    hom_qua = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")

    def xn(dau_vt, g8=None):
        def sua(m):
            m["gate_params"].setdefault("G10", {})["xac_nhan_ket_cuc_chinh"] = {
                "giai_trinh": "Hai cách diễn đạt cùng một thang hài lòng chung", "reviewed_at": hom_qua,
                "dau_van_tay": dau_vt}
            if g8 is not None:
                m["gate_params"].setdefault("G8", {})["primary_outcome"] = g8
        _sua_meta(out, sua)
        return _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["muc"]

    assert xn(dau) == NQ.MUC_CAN_XEM
    assert xn(dau, g8=sap) == NQ.MUC_CAN_XEM, "G8 chép nguyên văn SAP §2 ⇒ xác nhận cũ còn hiệu lực"
    assert xn("0" * 16, g8=sap) == NQ.MUC_LECH_MEM, "xác nhận gắn tập khác ⇒ bản sao không cứu được"
    assert xn(dau, g8=sap + " sau 30 ngày") == NQ.MUC_LECH_MEM, "diễn đạt mới ⇒ phải xác nhận lại"


def test_quan_the_doc_ca_tieu_chi_loai_cua_trds_muc_14(tmp_path):
    """WHO TRDS mục 14 = «Key Inclusion AND Exclusion Criteria» — trục `quan_the` đọc cả hai phần (BTM, 15/11/2026)."""
    import json

    from tests.test_dieu_phoi_thong_nhat_g0g10_20261004 import STUDY, _de_tai, _ghi, _muc

    qt = "Người lớn ĐTĐ típ 2 ngoại trú; loại trừ: lọc máu hoặc ghép thận, có thai, ĐTĐ típ 1"
    out = _de_tai(tmp_path, quan_the_g0=qt)
    p = out / f"G2_REGISTRATION_DRAFT_{STUDY}.json"
    reg = json.loads(p.read_text(encoding="utf-8"))
    reg["items"].append({"number": 14, "label": "Key Inclusion and Exclusion Criteria", "value": {
        "inclusion": ["Người lớn ĐTĐ típ 2 ngoại trú"],
        "exclusion": ["Lọc máu hoặc ghép thận", "Có thai", "ĐTĐ típ 1"]}})
    _ghi(p, reg)
    kq = _muc(NQ.doi_chieu(out, STUDY), "quan_the")
    g2 = next(n for n in kq["nguon"] if n["cong"] == "G2")
    assert "ghép thận" in g2["gia_tri"] and "Có thai" in g2["gia_tri"]
