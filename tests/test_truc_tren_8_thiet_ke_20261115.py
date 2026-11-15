"""Mọi trục nhất quán chạy được và không báo lệch sai trên đề tài giả NHẤT QUÁN của cả 8 thiết kế (15/11/2026).

Bác sĩ 15/11/2026: «… đạt chuẩn để có thể thực hiện với tất cả các nghiên cứu y khoa chưa chứ không phải chỉ cho 2 đề
tài trên». Các trục đồng bộ được kiểm sâu trên hai đề tài thật (đều cắt ngang); test này khoá hành vi trên đề tài giả đi
trọn G0→G10 của từng thiết kế (`_de_tai_g10_that`, cùng đồ gá test đầu–cuối G10): không trục nào sập, không lệch
cứng/lệch mềm, trục thời điểm không báo sai (đo lần đầu bắt được trục thời điểm đòi SAP định tính nêu thời điểm đo).
«Cần xem» do đồ gá (tên đề tài, câu hỏi nghiên cứu, kết cục có xác nhận) KHÔNG bị khoá ở đây.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nhat_quan_xuyen_cong as NQ  # noqa: E402

from tests.test_g10_hoan_thien_20261005 import THIET_KE_DAU_CUOI, _de_tai_g10_that  # noqa: E402


@pytest.mark.parametrize("thiet_ke", THIET_KE_DAU_CUOI)
def test_truc_nhat_quan_tren_de_tai_gia_nhat_quan(tmp_path, monkeypatch, thiet_ke):
    study, out, _goc = _de_tai_g10_that(tmp_path, monkeypatch, thiet_ke)
    kq = NQ.doi_chieu(out, study)
    lech = [(t["ma"], t["muc"], t.get("ghi_chu", "")[:160]) for t in kq["thong_so"]
            if t["muc"] in (NQ.MUC_LECH_CUNG, NQ.MUC_LECH_MEM)]
    assert lech == [], lech
    tdk = next(t for t in kq["thong_so"] if t["ma"] == "thoi_diem_ket_cuc")
    assert tdk["muc"] in (NQ.MUC_KHOP, NQ.MUC_CHUA_DU), (thiet_ke, tdk["ghi_chu"])
