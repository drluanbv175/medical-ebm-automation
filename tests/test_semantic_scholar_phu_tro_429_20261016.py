"""Semantic Scholar ở mức PHỤ TRỢ khi bị giới hạn tốc độ 429 (bác sĩ quyết 15/10/2026).

Đo 15/10 (`do_mang_nguon.py`): Semantic Scholar không khoá trả HTTP 429 — giới hạn tốc độ công khai, không phải chặn
mạng; nguồn «hỏng kéo dài» 10 ngày trong hòm việc. Bác sĩ chấp nhận để nguồn ở mức phụ trợ ⇒ lượt ghi chú
`SEMANTIC_SCHOLAR_AUXILIARY_RATE_LIMITED_429_ACCEPTED`, CHỈ khi mọi lỗi của nguồn là 429 VÀ ba nguồn lõi khám phá «ok».
Ngoại tuyến hoàn toàn: log tổng hợp giả, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ingestion import summarize_source_health  # noqa: E402
from app.services.nguon_hong_keo_dai import _ghi_chu_cua  # noqa: E402

GHI_CHU = "SEMANTIC_SCHOLAR_AUXILIARY_RATE_LIMITED_429_ACCEPTED"
LOI_KHAM_PHA = ["pubmed", "europepmc", "crossref"]
LOI_429 = "429 Client Error: Too Many Requests for url: https://api.semanticscholar.org/graph/v1/paper/search"


def _row(src, st="ok", n=5, err=None):
    return {"source": src, "status": st, "record_count": n, "error_message": err}


def _suc_khoe(rows, bo=()):
    logs = [_row(s) for s in LOI_KHAM_PHA if s not in bo] + list(rows)
    nguon = sorted({r["source"] for r in logs} | set(LOI_KHAM_PHA))
    return summarize_source_health(logs, expected_api_sources=nguon, expected_feed_sources=[], safety_enabled=False)


def test_moi_loi_la_429_va_loi_khoe_thi_co_ghi_chu():
    h = _suc_khoe([_row("semantic_scholar", "error", 0, LOI_429)] * 3)
    assert h["sources"]["semantic_scholar"]["error_http_429"] == 3
    assert GHI_CHU in h["mirror_notices"]
    assert _ghi_chu_cua("semantic_scholar", h["mirror_notices"]) == GHI_CHU


def test_loi_kieu_khac_lan_vao_thi_khong_ghi_chu():
    h = _suc_khoe([_row("semantic_scholar", "error", 0, LOI_429),
                   _row("semantic_scholar", "error", 0, "500 Server Error: Internal Server Error")])
    assert GHI_CHU not in h["mirror_notices"]


def test_nguon_loi_khong_khoe_thi_khong_ghi_chu():
    h = _suc_khoe([_row("pubmed", "error", 0, "Read timed out")] + [_row("semantic_scholar", "error", 0, LOI_429)] * 2,
                  bo=("pubmed",))
    assert GHI_CHU not in h["mirror_notices"]


def test_nguon_khac_bi_429_khong_duoc_mien():
    h = _suc_khoe([_row("openalex", "error", 0, LOI_429.replace("semanticscholar", "openalex"))] * 2)
    assert not any(g.startswith("OPENALEX_") for g in h["mirror_notices"])


def test_nguon_chay_duoc_thi_khong_ghi_chu():
    h = _suc_khoe([_row("semantic_scholar", "ok", 4), _row("semantic_scholar", "error", 0, LOI_429)])
    assert GHI_CHU not in h["mirror_notices"]
