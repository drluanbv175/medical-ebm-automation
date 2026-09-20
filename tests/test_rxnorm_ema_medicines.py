"""Kiểm OFFLINE (không gọi mạng) cho `app/sources/rxnorm.py`, `app/sources/ema_medicines.py` và `tools/tra_thuoc_quoc_te.py`.

Hình dạng phản hồi trong fixture lấy từ CÁC LỜI GỌI THẬT ngày 20/09/2026 (RxNav rxcui/approximateTerm/properties/related/
historystatus; báo cáo JSON của EMA) — không bịa cấu trúc.

Ba luật được canh, mỗi luật từng là một lỗi CÓ THẬT khi đo:
  * `loi` (không hỏi được) KHÔNG BAO GIỜ được thành `khong_thay` — cùng lớp BH27/BH08.
  * `gan_dung` KHÔNG BAO GIỜ được thành `khop_chinh_xac` («metfromin» → merbromin, một thuốc sát khuẩn khác hẳn).
  * tham số `tty` phải cách nhau bằng dấu cách (dấu «+» thô bị mã hoá thành %2B ⇒ HTTP 400).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sources.ema_medicines import EMA_URL, EmaMedicinesClient  # noqa: E402
from app.sources.rxnorm import BASE, RxNormClient  # noqa: E402
from tools.tra_thuoc_quoc_te import ma_thoat  # noqa: E402


class FakeHttp:
    """Thay HttpClient: trả theo hậu tố URL, ghi lại mọi lời gọi (để kiểm «không gọi mạng» và tham số)."""

    def __init__(self, tuyen: Dict[str, Any], loi_o: Optional[str] = None) -> None:
        self.tuyen = tuyen
        self.loi_o = loi_o
        self.goi: List[Dict[str, Any]] = []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        self.goi.append({"url": url, "params": params})
        if self.loi_o and self.loi_o in url:
            raise ConnectionError("mất mạng giả lập")
        for hau_to, phan_hoi in self.tuyen.items():
            if url.endswith(hau_to):
                return phan_hoi
        raise AssertionError(f"lời gọi ngoài dự kiến: {url}")


# ---------------------------------------------------------------- RxNorm
def _tuyen_glucophage() -> Dict[str, Any]:
    return {
        "rxcui.json": {"idGroup": {"name": "Glucophage", "rxnormId": ["151827"]}},
        "rxcui/151827/properties.json": {"properties": {"rxcui": "151827", "name": "Glucophage", "tty": "BN"}},
        "rxcui/151827/related.json": {"relatedGroup": {"conceptGroup": [
            {"tty": "IN", "conceptProperties": [{"rxcui": "6809", "name": "metformin", "tty": "IN"}]},
            {"tty": "PIN", "conceptProperties": [{"rxcui": "235743", "name": "metformin hydrochloride", "tty": "PIN"}]}]}},
    }


def test_rxnorm_khop_chinh_xac_tra_ve_hoat_chat():
    kq = RxNormClient(FakeHttp(_tuyen_glucophage())).chuan_hoa("Glucophage")
    assert kq["trang_thai"] == "khop_chinh_xac"
    assert [h["ten"] for h in kq["ket_qua"][0]["hoat_chat"]] == ["metformin", "metformin hydrochloride"]
    assert kq["ket_qua"][0]["hieu_luc"] is True


def test_rxnorm_tty_cach_nhau_bang_dau_cach_khong_phai_dau_cong():
    """Lỗi thật 20/09: «IN+MIN+PIN» thô bị mã hoá thành %2B ⇒ RxNav trả HTTP 400."""
    http = FakeHttp(_tuyen_glucophage())
    RxNormClient(http).chuan_hoa("Glucophage")
    related = [g for g in http.goi if g["url"].endswith("related.json")]
    assert related and related[0]["params"]["tty"] == "IN MIN PIN"
    assert "+" not in related[0]["params"]["tty"]


def test_rxnorm_hoat_chat_don_khong_goi_related():
    http = FakeHttp({"rxcui.json": {"idGroup": {"rxnormId": ["6809"]}},
                     "rxcui/6809/properties.json": {"properties": {"rxcui": "6809", "name": "metformin", "tty": "IN"}}})
    kq = RxNormClient(http).chuan_hoa("metformin")
    assert kq["trang_thai"] == "khop_chinh_xac" and kq["ket_qua"][0]["hoat_chat"] == []
    assert not any(g["url"].endswith("related.json") for g in http.goi)


def _tuyen_gan_dung() -> Dict[str, Any]:
    return {
        "rxcui.json": {"idGroup": {"name": "metfromin"}},  # KHÔNG có rxnormId
        "approximateTerm.json": {"approximateGroup": {"candidate": [
            {"rxcui": "6762", "score": "9.15", "rank": "1"}, {"rxcui": "6762", "score": "9.15", "rank": "2"},
            {"rxcui": "372781", "score": "8.83", "rank": "3"}]}},
        "rxcui/6762/properties.json": {"properties": {"rxcui": "6762", "name": "merbromin", "tty": "IN"}},
        "rxcui/372781/properties.json": {"properties": {"rxcui": "372781", "name": "merbromin Topical Solution", "tty": "SCDF"}},
        "rxcui/372781/related.json": {"relatedGroup": {"conceptGroup": [
            {"tty": "IN", "conceptProperties": [{"rxcui": "6762", "name": "merbromin", "tty": "IN"}]}]}},
    }


def test_rxnorm_gan_dung_khong_bao_gio_thanh_khop_chinh_xac_va_gop_trung():
    kq = RxNormClient(FakeHttp(_tuyen_gan_dung())).chuan_hoa("metfromin")
    assert kq["trang_thai"] == "gan_dung" and kq["trang_thai"] != "khop_chinh_xac"
    assert [r["rxcui"] for r in kq["ket_qua"]] == ["6762", "372781"]  # rxcui 6762 lặp hai lần → gộp còn một
    assert any("look-alike" in c for c in kq["canh_bao"])


def test_rxnorm_gop_trung_giu_thu_hang_tot_nhat_khong_phai_thu_hang_cuoi():
    """rxcui A xuất hiện hạng 1 rồi hạng 5; B hạng 2. Giữ ĐÚNG hạng tốt nhất ⇒ [A, B]; giữ nhầm hạng cuối ⇒ [B, A]."""
    tuyen = {
        "rxcui.json": {"idGroup": {}},
        "approximateTerm.json": {"approximateGroup": {"candidate": [
            {"rxcui": "111", "score": "9", "rank": "1"}, {"rxcui": "222", "score": "8", "rank": "2"},
            {"rxcui": "111", "score": "5", "rank": "5"}]}},
        "rxcui/111/properties.json": {"properties": {"rxcui": "111", "name": "thuoc-A", "tty": "IN"}},
        "rxcui/222/properties.json": {"properties": {"rxcui": "222", "name": "thuoc-B", "tty": "IN"}},
    }
    kq = RxNormClient(FakeHttp(tuyen)).chuan_hoa("thuoc")
    assert [r["rxcui"] for r in kq["ket_qua"]] == ["111", "222"]


def test_rxnorm_khong_thay_khac_loi():
    http = FakeHttp({"rxcui.json": {"idGroup": {}}, "approximateTerm.json": {"approximateGroup": {}}})
    kq = RxNormClient(http).chuan_hoa("xyzqwertyuiop")
    assert kq["trang_thai"] == "khong_thay"
    assert any("KHÔNG có nghĩa thuốc không tồn tại" in c for c in kq["canh_bao"])


@pytest.mark.parametrize("loi_o", ["rxcui.json", "approximateTerm.json", "properties.json", "related.json"])
def test_rxnorm_loi_mang_o_bat_ky_buoc_nao_la_loi_khong_phai_khong_thay(loi_o):
    tuyen = {**_tuyen_glucophage(), "approximateTerm.json": {"approximateGroup": {}}}
    if loi_o == "approximateTerm.json":
        tuyen["rxcui.json"] = {"idGroup": {}}
    kq = RxNormClient(FakeHttp(tuyen, loi_o=loi_o)).chuan_hoa("Glucophage")
    assert kq["trang_thai"] == "loi" and kq["trang_thai"] != "khong_thay"
    assert kq["ket_qua"] == [] and any("KHÔNG BIẾT" in c for c in kq["canh_bao"])


def test_rxnorm_ma_ngung_duoc_gan_co_va_canh_bao():
    """«Coversyl» → toàn mã Obsolete: properties rỗng, tên lấy từ historystatus, không có hoạt chất."""
    http = FakeHttp({
        "rxcui.json": {"idGroup": {"rxnormId": ["196500"]}},
        "rxcui/196500/properties.json": {"properties": {}},
        "rxcui/196500/historystatus.json": {"rxcuiStatusHistory": {"metaData": {"status": "Obsolete"},
                                                                    "attributes": {"name": "Coversyl", "tty": "BN"}}}})
    kq = RxNormClient(http).chuan_hoa("Coversyl")
    r = kq["ket_qua"][0]
    assert r["hieu_luc"] is False and r["trang_thai_rxcui"] == "Obsolete" and r["hoat_chat"] == [] and r["ten"] == "Coversyl"
    assert any("ĐÃ NGỪNG" in c for c in kq["canh_bao"])


@pytest.mark.parametrize("dau_vao", ["", "   ", "x" * 101, "bệnh nhân Nguyễn Văn A số điện thoại 0912345678 dùng metformin"])
def test_rxnorm_tu_choi_dau_vao_xau_khong_goi_mang(dau_vao):
    http = FakeHttp({})
    kq = RxNormClient(http).chuan_hoa(dau_vao)
    assert kq["trang_thai"] == "loi" and http.goi == []


# ---------------------------------------------------------------- EMA
def _bg(ten, hoat_chat, trang_thai="Authorised", cap_nhat="01/01/2026", loai="Human", **them) -> Dict[str, Any]:
    b = {"name_of_medicine": ten, "active_substance": hoat_chat, "international_non_proprietary_name_common_name": hoat_chat.lower(),
         "category": loai, "medicine_status": trang_thai, "additional_monitoring": "No", "conditional_approval": "No",
         "patient_safety": "No", "generic": "No", "biosimilar": "No", "orphan_medicine": "No", "atc_code_human": "A10BA02",
         "therapeutic_area_mesh": "", "marketing_authorisation_date": "", "last_updated_date": cap_nhat,
         "withdrawal_expiry_revocation_lapse_of_marketing_authorisation_date": "", "withdrawal_of_application_date": "",
         "refusal_of_marketing_authorisation_date": "", "suspension_of_marketing_authorisation_date": "",
         "ema_product_number": "EMEA/H/C/000001", "medicine_url": "https://www.ema.europa.eu/en/medicines/human/EPAR/x"}
    b.update(them)
    return b


def _ema(du_lieu: List[Dict[str, Any]], **kw: Any) -> EmaMedicinesClient:
    return EmaMedicinesClient(FakeHttp({EMA_URL.rsplit("/", 1)[-1]: {"meta": {"total_records": len(du_lieu), "timestamp": "2026-09-20T06:00:00Z"},
                                                                       "data": du_lieu}}, **kw))


def test_ema_tim_theo_hoat_chat_uu_tien_authorised_truoc_du_ngay_cu_hon():
    kq = _ema([_bg("Cũ nhưng còn hiệu lực", "Rosiglitazone", "Authorised", "01/01/2010"),
               _bg("Mới nhưng đã rút", "Rosiglitazone", "Withdrawn", "20/09/2026")]).tra("rosiglitazone")
    assert kq["trang_thai"] == "co_ket_qua"
    assert [b["medicine_status"] for b in kq["ket_qua"]] == ["Authorised", "Withdrawn"]
    assert kq["theo_trang_thai"] == {"Authorised": 1, "Withdrawn": 1} and kq["du_lieu_luc"] == "2026-09-20T06:00:00Z"


def test_ema_khop_theo_tu_nguyen_khong_khop_giua_chu():
    kq = _ema([_bg("A", "Metformin hydrochloride"), _bg("B", "Metforminx"), _bg("C", "Sitagliptin / Metformin hydrochloride")]).tra("metformin")
    assert sorted(b["name_of_medicine"] for b in kq["ket_qua"]) == ["A", "C"]


def test_ema_khong_thay_kem_canh_bao_cap_phep_quoc_gia():
    kq = _ema([_bg("A", "Metformin")]).tra("zzzzqqqq")
    assert kq["trang_thai"] == "khong_thay" and kq["so_khop"] == 0
    assert any("cấp phép quốc gia" in c for c in kq["canh_bao"])
    assert any("KHÔNG kèm lý do" in c for c in kq["canh_bao"])


def test_ema_loi_mang_la_loi_khong_phai_khong_thay():
    kq = _ema([_bg("A", "Metformin")], loi_o="medicines_json").tra("metformin")
    assert kq["trang_thai"] == "loi" and any("KHÔNG BIẾT" in c for c in kq["canh_bao"])


@pytest.mark.parametrize("phan_hoi", [{"meta": {}, "data": []}, {"meta": {}}, {"data": "khong-phai-danh-sach"}, []])
def test_ema_bo_cuc_doi_hoac_rong_la_loi_khong_phai_khong_thay(phan_hoi):
    """Danh sách rỗng/bố cục lạ KHÔNG được đọc thành «không có thuốc nào khớp»."""
    kq = EmaMedicinesClient(FakeHttp({EMA_URL.rsplit("/", 1)[-1]: phan_hoi})).tra("metformin")
    assert kq["trang_thai"] == "loi"


@pytest.mark.parametrize("tu_khoa", ["", "ab", "x" * 101, "bệnh nhân Trần Thị B số 0987654321 dùng metformin"])
def test_ema_tu_choi_dau_vao_xau_khong_goi_mang(tu_khoa):
    http = FakeHttp({})
    kq = EmaMedicinesClient(http).tra(tu_khoa)
    assert kq["trang_thai"] == "loi" and http.goi == []


def test_ema_thu_y_bi_loai_mac_dinh_va_them_khi_yeu_cau():
    du_lieu = [_bg("Người", "Enrofloxacin", loai="Human"), _bg("Thú y", "Enrofloxacin", loai="Veterinary")]
    assert [b["name_of_medicine"] for b in _ema(du_lieu).tra("enrofloxacin")["ket_qua"]] == ["Người"]
    assert len(_ema(du_lieu).tra("enrofloxacin", ca_thu_y=True)["ket_qua"]) == 2


def test_ema_cat_bot_bao_so_con_lai():
    kq = _ema([_bg(f"T{i}", "Metformin") for i in range(7)]).tra("metformin", toi_da=3)
    assert len(kq["ket_qua"]) == 3 and kq["bi_cat_bot"] == 4 and kq["so_khop"] == 7


# ---------------------------------------------------------------- CLI
@pytest.mark.parametrize("trang_thai,ma", [("khop_chinh_xac", 0), ("gan_dung", 0), ("co_ket_qua", 0), ("khong_thay", 1), ("loi", 2), ("la-hoac", 2), (None, 2)])
def test_ma_thoat_loi_khong_bao_gio_la_khong_thay(trang_thai, ma):
    assert ma_thoat({"trang_thai": trang_thai}) == ma


def test_base_url_dung_chinh_thuc():
    assert BASE == "https://rxnav.nlm.nih.gov/REST" and EMA_URL.startswith("https://www.ema.europa.eu/")
