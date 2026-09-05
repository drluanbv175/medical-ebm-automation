"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 9,
task #94) trong `app/services/pipeline.py` (nhánh `else` của
`_decorate_item()`, gọi từ `run_pipeline()`) — điểm số/lý do loại trừ/
synthesis CŨ sống sót qua lần chạy khi một bản ghi từng là PRIMARY chuyển
thành DUPLICATE.

CƠ CHẾ LỖI: `normalize()` không đặt `reason_for_exclusion`/`evidence_
quality_score`/`practice_change_score`/`reliability_tier`/`operational_
evidence_level`/`synthesis` — các trường này CHỈ được gán trong nhánh
`is_primary` (qua `score_item()`/`classify()`/`synthesize()`). Nhánh bản
trùng trước đây chỉ reset `classification`/`is_actionable`/
`actionable_reason`, nên `item` dict ở lần chạy đó KHÔNG hề chứa các khoá
kia. `_upsert()` xây `payload` trực tiếp từ `item.items()` rồi chỉ
`setattr()` những khoá THẬT SỰ CÓ MẶT trong payload — một bản ghi trong DB
đã có `reliability_tier`/`reason_for_exclusion`/`synthesis` từ lần chạy
TRƯỚC (khi nó còn là primary) sẽ giữ NGUYÊN các giá trị đó dù
`classification` đổi đúng thành "duplicate" ở lần chạy sau.

HẬU QUẢ: dashboard hiện một bản ghi dán nhãn "duplicate" nhưng vẫn mang lý
do loại trừ/điểm số/synthesis của một phân loại "excluded"/"actionable" đã
không còn đúng — thông tin lâm sàng tự mâu thuẫn.

BẢN VÁ: tách logic "gắn điểm/phân loại HOẶC reset" thành hàm riêng
`_decorate_item(item, is_primary)` (trước đây nằm inline trong vòng lặp của
`run_pipeline()`, không gọi độc lập được để test) — nhánh reset nay xoá cả
6 trường phái sinh về `None`.

Nguyên tắc viết test: gọi THẲNG `_decorate_item()` VÀ `_upsert()` thật, nối
tiếp hai lần đúng như `run_pipeline()` làm (không hand-craft dict giả lập
kết quả mong đợi — item ở lần 2 phải do CHÍNH `_decorate_item(is_primary=
False)` sinh ra, để mutation-test bắt được nếu ai lỡ revert `_decorate_
item()` mà quên/để sai chỗ gọi nó)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.database import session_scope  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.services.pipeline import _decorate_item, _upsert  # noqa: E402

_SHARED_FIELDS = {
    "source": "t-vong9", "source_type": "article", "title": "Some RCT title vong9",
    "doi": "10.1/vong9-example", "pmid": "999999", "nct_id": None, "authors": "A B",
    "journal_or_organization": "NEJM", "publication_date": "2026-01-01",
    "study_type": "preprint", "abstract": None, "safety_signal": None,
}


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    """DB sqlite tạm RIÊNG cho test này (không dùng chung DB của conftest) —
    _upsert() thao tác trực tiếp qua session_scope() nên cần schema thật."""
    import app.database as db_mod
    from app.database import init_db

    db_path = tmp_path / "vong9_pipeline.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    from app.config import settings
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


class TestFieldCuKhongDuocSongSotQuaLanChayDuplicate:
    """★★★ Ca chính — gọi ĐÚNG chuỗi `_decorate_item()` -> `_upsert()` hai
    lần liên tiếp (mô phỏng 2 lần chạy pipeline với cùng 1 bản ghi qua DOI):
    lần 1 là primary (được điểm + lý do loại + synthesis), lần 2 CÙNG bản
    ghi đó nhưng là duplicate — mọi trường phái sinh phải về None."""

    def test_reliability_tier_reason_synthesis_ve_none_sau_khi_thanh_duplicate(self, isolated_db):
        item1 = dict(_SHARED_FIELDS)
        _decorate_item(item1, is_primary=True)
        # Item preprint gần như chắc chắn bị loại (Tier D/watch) — không quan
        # trọng CHÍNH XÁC classify() trả gì, miễn nó set các trường phái sinh.
        with session_scope() as s:
            obj1, created1 = _upsert(s, item1, is_primary=True, run_id=1)
            obj_id = obj1.id
        assert created1 is True

        with session_scope() as s:
            row = s.get(EvidenceItem, obj_id)
            had_derived_fields_before = any([
                row.reliability_tier is not None,
                row.reason_for_exclusion is not None,
                row.synthesis is not None,
                row.evidence_quality_score is not None,
            ])
        assert had_derived_fields_before, (
            "Fixture cần record thật sự CÓ điểm/lý do/synthesis sau lần chạy 1 "
            "để ca chính có ý nghĩa — kiểm lại _SHARED_FIELDS/classify()."
        )

        # Lần chạy 2: CÙNG bản ghi (khớp doi), nay là duplicate.
        item2 = dict(_SHARED_FIELDS)
        _decorate_item(item2, is_primary=False)
        with session_scope() as s:
            obj2, created2 = _upsert(s, item2, is_primary=False, run_id=2)
        assert created2 is False
        assert obj2.id == obj_id

        with session_scope() as s:
            row = s.get(EvidenceItem, obj_id)
            assert row.classification == "duplicate"
            assert row.reliability_tier is None
            assert row.reason_for_exclusion is None
            assert row.evidence_quality_score is None
            assert row.practice_change_score is None
            assert row.operational_evidence_level is None
            assert row.synthesis is None


class TestBanGhiThatSuMoiVanChayDungNhuCu:
    """Đối chứng bắt buộc — bản ghi PRIMARY (dù là lần đầu hay không) vẫn
    được `_decorate_item()` gắn đủ điểm/phân loại/synthesis như hành vi
    gốc — bản vá KHÔNG ảnh hưởng nhánh is_primary=True."""

    def test_item_primary_van_duoc_gan_du_truong(self):
        item = dict(_SHARED_FIELDS)
        result = _decorate_item(item, is_primary=True)
        assert result is item  # mutates & returns, không tạo dict mới
        assert item["classification"] in {"actionable", "need_full_text", "watch_only", "excluded"}
        assert item["reliability_tier"] is not None
        assert "evidence_quality_score" in item
        assert "synthesis" in item

    def test_item_duplicate_reset_ca_9_truong(self):
        item = dict(_SHARED_FIELDS)
        # Giả lập item đã từng mang giá trị "primary" từ dict trước đó (đúng
        # tình huống thật: cùng dict Python được tái sử dụng qua các lần gọi
        # trong vòng lặp là KHÔNG xảy ra trong pipeline thật — nhưng ở đây ta
        # cố tình gieo sẵn giá trị cũ để kiểm _decorate_item() THỰC SỰ ghi đè
        # bằng None chứ không chỉ "vô tình" không có khoá đó).
        item.update({
            "reason_for_exclusion": "old reason", "evidence_quality_score": 99,
            "practice_change_score": 99, "reliability_tier": "A",
            "operational_evidence_level": "High", "synthesis": {"x": "old"},
        })
        _decorate_item(item, is_primary=False)
        assert item["classification"] == "duplicate"
        assert item["is_actionable"] is False
        assert item["actionable_reason"] is None
        assert item["reason_for_exclusion"] is None
        assert item["evidence_quality_score"] is None
        assert item["practice_change_score"] is None
        assert item["reliability_tier"] is None
        assert item["operational_evidence_level"] is None
        assert item["synthesis"] is None
