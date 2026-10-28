# -*- coding: utf-8 -*-
"""Hồi quy 28/10/2026 — mục 11 «Quản trị dữ liệu» của gói G10 TRƯỚC dữ liệu khi đề tài đã có bộ công cụ G5.

Ca thật C1a: từ 24/10 đề tài có `G5_checkpoint.json` (bộ công cụ G5, `g5_status` PENDING chờ G2). Bản vá 05/10 (G10-09)
chỉ ghi «chưa có — dữ liệu thật chỉ thu thập SAU phê duyệt đạo đức» khi G5 VẮNG ⇒ lắp lại gói trình Hội đồng sau khi G4
ký lại in «[CẦN BỔ SUNG]» cho «Dữ liệu thật đã nhập» và «Dữ liệu phân tích đã khóa» ⇒ G10-AUTO-09 REVIEW, PI không ký
được G10. Gói trước dữ liệu (ETHICS_SUBMISSION/REGISTRY_UPDATE) chưa thể có dữ liệu thật; bản ghi dữ liệu thật trong
study_meta (nếu có) vẫn được in. Ngoại tuyến, dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g10_quality_gate as G10Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402

from tests.test_g8_hoan_thien_20261004 import _ghi  # noqa: E402
from tests.test_g10_hoan_thien_20261005 import _cham10, _chua_dat, _de_tai_truoc_irb, _lap_g10  # noqa: E402

# Hình dạng checkpoint của bộ công cụ G5 thật (run_g5_auto, trước khi có dữ liệu) — ba trường mà các mục khác của đề
# cương đọc (script, cột CRF) có mặt như ở đề tài thật; chỉ trạng thái dữ liệu là «chưa thu thập».
_G5_CHO_G2 = {"gate": "G5", "g5_status": "PENDING",
              "database_lock_status": "PENDING — dữ liệu chưa thu thập (chờ G2 LOCKED)",
              "scripts_generated": ["scripts/data_cleaning.py", "scripts/data_quality_report.py"],
              "crf_columns": ["record_id", "tuoi", "ket_cuc_chinh"], "redcap_rows": 3, "specialty": "bo_bien_rieng"}


def _muc11(muc_dich, meta_them=None) -> str:
    meta = {"_g10": {"muc_dich": muc_dich}, **(meta_them or {})}
    return G10A.sec_quantri_dulieu({"G5": dict(_G5_CHO_G2)}, meta)


def _dong(muc: str, nhan: str) -> str:
    return next(d for d in muc.splitlines() if d.startswith(nhan))


@pytest.mark.parametrize("muc_dich", sorted(G10Q.MUC_DICH_TRUOC_DU_LIEU))
def test_goi_truoc_du_lieu_co_g5_khong_in_o_can_bo_sung(muc_dich):
    muc = _muc11(muc_dich)
    for nhan in ("**Dữ liệu thật đã nhập:**", "**Dữ liệu phân tích đã khóa:**"):
        dong = _dong(muc, nhan)
        assert "[CẦN" not in dong and "chưa có" in dong, dong
    assert "PENDING — dữ liệu chưa thu thập" in _dong(muc, "**Trạng thái khoá cơ sở dữ liệu")


def test_goi_sau_du_lieu_van_doi_bo_sung_du_lieu_that():
    """Mục đích khác (hoặc chưa chọn) đòi đủ G0–G9 ⇒ thiếu bản ghi nhập/khoá dữ liệu vẫn là ô phải điền."""
    for muc_dich in (None, "JOURNAL_SUBMISSION"):
        muc = _muc11(muc_dich)
        assert "[CẦN" in _dong(muc, "**Dữ liệu thật đã nhập:**")
        assert "[CẦN" in _dong(muc, "**Dữ liệu phân tích đã khóa:**")


def test_goi_truoc_du_lieu_van_in_ban_ghi_du_lieu_that_neu_co():
    muc = _muc11("ETHICS_SUBMISSION", {"real_data_intake": {"status": "IMPORTED", "rows": 12, "columns": 5}})
    dong = _dong(muc, "**Dữ liệu thật đã nhập:**")
    assert "IMPORTED" in dong and "N=12" in dong, dong


def test_lap_lai_goi_trinh_hoi_dong_sau_khi_co_bo_cong_cu_g5_van_ready(tmp_path, monkeypatch):
    """Chuỗi THẬT trước IRB (G2 sẵn sàng nộp, G4 chưa ký) → sinh bộ công cụ G5 (PENDING chờ G2) → lắp lại G10."""
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    _ghi(out / "G5_checkpoint.json", json.dumps({**_G5_CHO_G2, "study": study}, ensure_ascii=False, indent=2))
    ma, log = _lap_g10(goc, study, monkeypatch)
    # READY trả EXIT_BLOCKED có chủ ý: gói sẵn sàng nhưng CHƯA phát hành cho tới khi PI ký đúng manifest.
    assert ma == GC.EXIT_BLOCKED and "sẵn sàng để PI rà" in log, log[-1500:]
    noi_dung = (out / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
    assert "[CẦN" not in noi_dung, [d for d in noi_dung.splitlines() if "[CẦN" in d]
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)
