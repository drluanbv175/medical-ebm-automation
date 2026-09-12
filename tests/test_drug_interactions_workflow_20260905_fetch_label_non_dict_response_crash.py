"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 17) trong app/integrations/drug_interactions.py::fetch_label().

CƠ CHẾ LỖI: sau khối try/except quanh `self.http.get_json(...)`, dòng
`results = data.get("results") or []` giả định `data` LUÔN là dict khi
không có exception nào được ném. Một phản hồi bất thường từ tầng HTTP
(body rỗng đọc thành `None`, proxy không chuẩn, lỗi cache) khiến `data`
là `None` (hoặc list/chuỗi) — `.get(...)` ném `AttributeError` THÔ, KHÔNG
bị `except DrugInteractionError` ở `screen_regimen()` bắt được (chỉ bắt
đúng `DrugInteractionError`), nên lỗi lan ra ngoài và SẬP TOÀN BỘ lượt
sàng lọc đơn thuốc — mọi thuốc khác trong cùng đơn cũng mất kết quả, thay
vì chỉ ghi nhận `lookup_failed` cho riêng thuốc gặp lỗi.

BẢN VÁ: kiểm `isinstance(data, dict)` ngay sau khối try/except; nếu
không phải dict thì raise `DrugInteractionError` tường minh (được
`screen_regimen()` bắt đúng, chuyển thành mục `lookup_failed` — không sập
cả lô).

Nguyên tắc viết test: gọi THẲNG `DrugSafetyChecker.fetch_label()` và
`screen_regimen()` thật, tiêm một HttpClient giả trả None/list thay vì
dict (không mock nội bộ hàm cần kiểm)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.integrations.drug_interactions import (  # noqa: E402
    DrugInteractionError,
    DrugSafetyChecker,
)


class NoneReturningHttp:
    """Mô phỏng phản hồi bất thường: get_json() trả None thay vì dict."""

    def get_json(self, url, params=None, use_cache=True):
        return None


class ListReturningHttp:
    """Mô phỏng phản hồi bất thường khác: get_json() trả list."""

    def get_json(self, url, params=None, use_cache=True):
        return ["unexpected", "shape"]


class TestPhanHoiKhongPhaiDictKhongDuocLamSapCaLo:
    """★★★ Ca chính — get_json() trả về giá trị không phải dict phải sinh
    DrugInteractionError có kiểm soát (→ lookup_failed ở screen_regimen()),
    KHÔNG được để AttributeError thô lan ra ngoài."""

    def test_fetch_label_raise_drug_interaction_error_khi_data_la_none(self):
        chk = DrugSafetyChecker(http=NoneReturningHttp())
        with pytest.raises(DrugInteractionError):
            chk.fetch_label("metoprolol")

    def test_fetch_label_raise_drug_interaction_error_khi_data_la_list(self):
        chk = DrugSafetyChecker(http=ListReturningHttp())
        with pytest.raises(DrugInteractionError):
            chk.fetch_label("verapamil")

    def test_screen_regimen_khong_sap_ca_don_khi_mot_thuoc_gap_phan_hoi_hong(self):
        chk = DrugSafetyChecker(http=NoneReturningHttp())
        warns = chk.screen_regimen(["metoprolol", "verapamil"])
        assert not any(w["type"] == "boxed_warning" for w in warns) or True  # không crash là đủ
        assert len(warns) == 2
        assert all(w["type"] == "lookup_failed" for w in warns), (
            "TRƯỚC bản vá: AttributeError thô từ fetch_label() không bị "
            "except DrugInteractionError bắt được ở screen_regimen(), làm "
            "sập toàn bộ lượt sàng lọc thay vì trả về lookup_failed cho "
            "từng thuốc"
        )


class TestPhanHoiHopLeVanHoatDongBinhThuong:
    """Đối chứng bắt buộc — phản hồi dict hợp lệ (hành vi gốc) vẫn parse
    đúng như trước bản vá."""

    def test_fetch_label_parse_dung_khi_data_la_dict_hop_le(self):
        class GoodHttp:
            def get_json(self, url, params=None, use_cache=True):
                return {"results": [{
                    "openfda": {"generic_name": ["metoprolol"], "brand_name": ["Lopressor"],
                                "spl_set_id": ["SET-1"]},
                    "set_id": "SET-1",
                    "drug_interactions": ["Use with verapamil may cause bradycardia."],
                }]}

        chk = DrugSafetyChecker(http=GoodHttp())
        lab = chk.fetch_label("metoprolol")
        assert lab is not None
        assert "metoprolol" in [g.lower() for g in lab["generic_names"]]

    def test_fetch_label_tra_none_khi_khong_co_ket_qua(self):
        class EmptyHttp:
            def get_json(self, url, params=None, use_cache=True):
                return {"results": []}

        chk = DrugSafetyChecker(http=EmptyHttp())
        assert chk.fetch_label("khongtontai") is None
