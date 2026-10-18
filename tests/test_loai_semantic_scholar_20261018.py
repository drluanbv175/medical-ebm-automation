"""Semantic Scholar LOẠI KHỎI VẬN HÀNH — 18/10/2026 (bác sĩ quyết).

Kênh không khoá của Semantic Scholar trả HTTP 429 kéo dài (đo 22/09; «hỏng kéo dài» 3 lượt live liền 01→18/10), bác sĩ
quyết loại bỏ. Test chốt: dù cờ ENABLE_SEMANTIC_SCHOLAR có bật, nguồn này KHÔNG vào danh sách nguồn engine truy vấn,
không vào bản đồ `test-live`, không vào danh sách adapter đo sống, không vào phép đo mạng; mặc định cờ là tắt.
Ngoại tuyến (không gọi mạng).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import app.sources as SRC  # noqa: E402
from app.config import Settings  # noqa: E402


def test_mac_dinh_tat(monkeypatch):
    monkeypatch.delenv("ENABLE_SEMANTIC_SCHOLAR", raising=False)
    assert Settings().enable_semantic_scholar is False


def test_bat_co_van_khong_vao_danh_sach_nguon(monkeypatch):
    monkeypatch.setattr(SRC.settings, "enable_semantic_scholar", True)
    ten = {type(c).__name__ for c in SRC.get_enabled_sources()}
    assert "SemanticScholarClient" not in ten
    assert "PubMedClient" in ten or not SRC.settings.enable_pubmed, "danh sách nguồn còn lại vẫn dựng bình thường"


def test_khong_con_trong_test_live_va_adapter_do_song():
    import app.main as M
    from app.evidence.live_adapter_registry import ADAPTER_CLASSES

    assert "semantic_scholar" not in M._build_source_map()
    assert "semantic_scholar" not in ADAPTER_CLASSES


def test_khong_con_trong_phep_do_mang():
    import do_mang_nguon as DM

    from app.config import settings

    diem = DM.danh_sach_diem(settings)  # chỉ dựng danh sách điểm đo, không gọi mạng
    assert diem and not any("semanticscholar" in str(d) for d in diem)
