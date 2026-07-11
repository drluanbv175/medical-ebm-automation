"""Test ONLINE (opt-in) — xác minh 32 PMID nguồn gốc thang điểm 'verified' còn PHÂN GIẢI
ĐÚNG trên PubMed thật, không chỉ đúng ĐỊNH DẠNG (xem test_verified_identifiers.py, offline).

Vá 2026-07-11 (vòng tiếp theo): trước đây độ phủ trích dẫn của 32 thang chỉ được canh gác
bằng test OFFLINE (định dạng số/chuỗi) — không có gì bảo vệ chống một PMID bị gõ sai/đổi
sau này (sai 1-2 chữ số vẫn ĐÚNG định dạng nhưng trỏ nhầm bài, hoặc bài bị rút sau khi đã
trích dẫn). BỎ QUA MẶC ĐỊNH — không gọi mạng trong pytest thường/CI (nhất quán với
MRAQ_OFFLINE_CI ở conftest.py) — chỉ chạy khi đặt EBM_RUN_ONLINE_PMID_TEST=1, cùng triết lý
--online opt-in đã dùng ở EBM-Dashboards/tools/verify_dashboard.py và
EBM_MASTER/tools/integrity_guard.py.

Fail-CLOSED có điều kiện: PMID PubMed xác nhận KHÔNG TỒN TẠI luôn FAIL (bất kể mạng có lỗi
ở PMID khác) — nhưng nếu TOÀN BỘ lỗi chỉ do mạng (không xác minh được, không phải "không
tồn tại"), test SKIP (không kết luận) thay vì PASS giả hoặc FAIL oan, cùng nguyên tắc
tri-state đã áp dụng cho verify_dashboard.py --online vòng 9.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

import pytest

from app.clinical_scores.verified import VERIFIED_SCORES

pytestmark = pytest.mark.skipif(
    os.environ.get("EBM_RUN_ONLINE_PMID_TEST") != "1",
    reason="Test online (gọi PubMed thật qua mạng) — chỉ chạy khi đặt EBM_RUN_ONLINE_PMID_TEST=1",
)


def _verify_pmid_online(pmid: str, retries: int = 2) -> bool | None:
    """Tri-state True/False/None. Cùng mẫu với verify_dashboard.py:verify_pmid_online() và
    integrity_guard.py:verify_pubmed() — KHÔNG tái dùng trực tiếp (2 hàm đó ở ngoài repo
    medical-ebm-automation, không import được). Không dùng app/sources/pubmed.py:PubMedClient
    — hàm search() ở đó lọc theo publication-type (SR/MA/RCT/guideline); nhiều thang verified
    có nguồn là nghiên cứu derivation/validation KHÔNG thuộc các loại này, sẽ bị lọc mất dù
    PMID hoàn toàn đúng — sai công cụ cho việc kiểm tồn tại của MỘT PMID đã biết."""
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
           "?db=pubmed&retmode=json&id=" + pmid)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                j = json.loads(r.read().decode("utf-8"))
            res = j.get("result", {})
            return pmid in res and bool(res.get(pmid, {}).get("title"))
        except Exception:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
    return None


def test_all_verified_score_pmids_resolve_on_pubmed():
    pmids = sorted({s["pmid"] for s in VERIFIED_SCORES if s.get("pmid")})
    assert pmids, "Không có PMID nào để kiểm — VERIFIED_SCORES rỗng?"

    unresolved: list[str] = []
    unverified: list[str] = []
    for i, pmid in enumerate(pmids):
        if i:
            time.sleep(0.34)  # ~3 req/s, NCBI E-utilities không key
        ok = _verify_pmid_online(pmid)
        if ok is False:
            unresolved.append(pmid)
        elif ok is None:
            unverified.append(pmid)

    if unverified and not unresolved:
        pytest.skip(
            f"Mạng lỗi/không xác minh được {len(unverified)}/{len(pmids)} PMID — "
            f"không kết luận được, thử lại khi mạng ổn định: {unverified}"
        )
    assert not unresolved, (
        f"PMID KHÔNG tồn tại trên PubMed (nghi gõ sai/bị rút): {unresolved} — "
        f"rà lại app/clinical_scores/verified.py::_VERIFIED_IDS."
    )
