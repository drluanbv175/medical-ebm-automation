"""Hồi quy ingest cho nguồn Retraction and Replacement."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# CI ĐƠN-REPO (16/08/2026): file này NẠP công cụ của workspace gốc ngay lúc
# import — thiếu workspace thì phải skip Ở MỨC MODULE trước dòng nạp
# (pytestmark không cứu được lỗi collection). Máy bác sĩ chạy đủ.
if not (Path(__file__).resolve().parents[2] / "tools").is_dir():
    pytest.skip("cần workspace gốc (tools/ ở thư mục mẹ) — CI checkout đơn-repo",
                allow_module_level=True)

TOOLS = Path(__file__).resolve().parents[2] / "EBM_MASTER" / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("ingest_dashboard_replacement", TOOLS / "ingest_dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _new_card(decision: str = "apply") -> dict:
    return {
        "id": "EVID-2026-9999",
        "date_added": "2026-08-14",
        "specialty": "",
        "topic": "Bản thay thế — tín hiệu quan sát",
        "source": {"pmid": "", "doi": "10.1001/replacement"},
        "decision": decision,
        "references": ["DOI:10.1001/replacement", "PMID:31021386"],
        "replacement": {"supersedes_pmid": "30267080"},
        "history": [{"date": "2026-08-14", "change": "nạp từ dashboard sửa"}],
    }


def test_explicit_replacement_preserves_identity_demotes_and_consolidates_generated_duplicate():
    old = {
        "id": "EVID-2026-0553",
        "date_added": "2026-07-16",
        "specialty": "Tiêu hóa – Gan mật",
        "topic": "Tín hiệu quan sát cũ",
        "source": {"pmid": "30267080", "doi": "10.1001/replacement"},
        "decision": "consider",
        "history": [{"date": "2026-07-16", "change": "nạp bản cũ"}],
    }
    generated_duplicate = {
        "id": "EVID-2026-1236",
        "topic": "Bản thay thế — tín hiệu quan sát",
        "source": {"pmid": "", "doi": "10.1001/replacement"},
        "history": [{"change": "cùng DOI/PMID nhưng nạp như thẻ mới"}],
    }
    distinct = {
        "id": "EVID-2026-2000",
        "topic": "Khuyến cáo hoàn toàn khác từ cùng guideline",
        "source": {"pmid": "", "doi": "10.1001/replacement"},
        "history": [{"change": "cùng DOI/PMID nhưng nạp như thẻ mới"}],
    }
    data = {"evidence_cards": [old, generated_duplicate, distinct]}

    replaced, removed = MODULE.apply_explicit_replacement(
        data,
        _new_card(),
        "30267080",
        today="2026-08-14",
        dashboard_name="corrected.html",
    )

    assert replaced is True
    assert removed == 1
    assert [card["id"] for card in data["evidence_cards"]] == ["EVID-2026-0553", "EVID-2026-2000"]
    corrected = data["evidence_cards"][0]
    assert corrected["date_added"] == "2026-07-16"
    assert corrected["specialty"] == "Tiêu hóa – Gan mật"
    assert corrected["decision"] == "notyet"
    assert corrected["source"]["pmid"] == ""
    assert corrected["replacement"]["supersedes_pmid"] == "30267080"
    assert any("giữ ID" in event["change"] for event in corrected["history"])


def test_explicit_replacement_fails_closed_when_old_pmid_is_ambiguous():
    data = {
        "evidence_cards": [
            {"id": "A", "source": {"pmid": "30267080"}},
            {"id": "B", "source": {"pmid": "30267080"}},
        ]
    }

    try:
        MODULE.apply_explicit_replacement(
            data,
            _new_card(),
            "30267080",
            today="2026-08-14",
            dashboard_name="corrected.html",
        )
    except RuntimeError as exc:
        assert "cần bác sĩ chọn thẻ đích" in str(exc)
    else:
        raise AssertionError("Nhiều thẻ đích phải fail-closed")
