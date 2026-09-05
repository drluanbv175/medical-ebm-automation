"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 10,
task #95) trong `app/models/evidence.py::EvidenceItem.operational_evidence_level`
— cột khai `String(16)` trong khi `operational_evidence_level()` (app/scoring/
operational_level.py) thực tế trả chuỗi dài hơn 16 ký tự ở NHÁNH PHỔ BIẾN
NHẤT (không có official_grade — không phải guideline nhập tay):
"High (operational)" (19) / "Moderate (operational)" (22) / "Low
(operational)" (18); nhánh "Theo nguồn: <official_grade>" có thể dài tới
44 ký tự.

CƠ CHẾ LỖI: SQLite bỏ qua giới hạn độ dài VARCHAR nên lỗi im lặng trên máy
hiện tại — nhưng `app/database.py` tự khai ý định "nâng cấp PostgreSQL dễ
dàng", và trên Postgres, VARCHAR(16) được THI HÀNH THẬT: mọi lần ghi bản
ghi không có official_grade (đa số) sẽ vỡ `DataError: value too long for
type character varying(16)`, làm hỏng phần lớn lượt ghi của pipeline ngay
khi hệ thống chuyển sang Postgres.

BẢN VÁ: đổi cột sang `Text` (không giới hạn) — cùng kiểu các trường mô tả
khác trong model này (reason_for_exclusion, safety_signal).

Nguyên tắc viết test: dùng khai báo cột THẬT (`EvidenceItem.__table__`) và
ghi một giá trị THẬT do `operational_evidence_level()` sinh ra vào DB thật
(SQLite tạm) — không hand-craft chuỗi giả định độ dài.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from sqlalchemy import Text  # noqa: E402

from app.models import EvidenceItem  # noqa: E402
from app.scoring.operational_level import operational_evidence_level  # noqa: E402


class TestCotKhongConGioiHanDoDaiVarchar:
    """★★★ Ca chính — cột `operational_evidence_level` không còn là
    `String(N)` giới hạn (nguồn gốc lỗi trên Postgres); giá trị dài THẬT
    (do chính hàm scoring sinh ra) vẫn ghi/đọc lại nguyên vẹn qua DB thật."""

    def test_khai_bao_cot_la_text_khong_gioi_han(self):
        # SQLAlchemy: `Text` là lớp con của `String` nhưng KHÔNG có `.length`
        # (None) — đây mới là điều kiện thật sự phân biệt "không giới hạn"
        # với `String(16)` (length=16). isinstance(Text(), String) luôn
        # True nên không dùng được để phân biệt.
        col_type = EvidenceItem.__table__.c.operational_evidence_level.type
        assert isinstance(col_type, Text)
        assert col_type.length is None

    def test_gia_tri_dai_thuc_te_tu_scoring_ghi_duoc_nguyen_ven(self, isolated_db):
        from app.database import session_scope

        # Nhánh PHỔ BIẾN NHẤT (không official_grade) — dài nhất trong 3 mức.
        level, _ = operational_evidence_level({}, evidence_q=60)  # "Moderate (operational)"
        assert len(level) > 16, "Fixture cần giá trị THẬT SỰ vượt String(16) cũ để ca chính có ý nghĩa"
        with session_scope() as s:
            obj = EvidenceItem(source="t-vong10", source_type="article", title="X",
                                operational_evidence_level=level)
            s.add(obj)
            s.flush()
            obj_id = obj.id
        with session_scope() as s:
            row = s.get(EvidenceItem, obj_id)
            assert row.operational_evidence_level == level

    def test_nhanh_theo_nguon_44_ky_tu_van_ghi_duoc(self, isolated_db):
        from app.database import session_scope

        long_official_grade = "X" * 32  # đúng độ dài tối đa cột official_grade
        level, _ = operational_evidence_level({"official_grade": long_official_grade}, 50)
        assert len(level) > 16
        with session_scope() as s:
            obj = EvidenceItem(source="t-vong10", source_type="article", title="X",
                                operational_evidence_level=level,
                                official_grade=long_official_grade)
            s.add(obj)
            s.flush()
            obj_id = obj.id
        with session_scope() as s:
            row = s.get(EvidenceItem, obj_id)
            assert row.operational_evidence_level == level


class TestGiaTriNganVanGhiDocBinhThuong:
    """Đối chứng bắt buộc — giá trị ngắn ("High"/"Low", đúng bản gốc mong
    đợi) vẫn hoạt động như cũ, bản vá không đổi nội dung dữ liệu."""

    def test_gia_tri_ngan_van_hoat_dong(self, isolated_db):
        from app.database import session_scope

        with session_scope() as s:
            obj = EvidenceItem(source="t-vong10", source_type="article", title="X",
                                operational_evidence_level="High")
            s.add(obj)
            s.flush()
            obj_id = obj.id
        with session_scope() as s:
            row = s.get(EvidenceItem, obj_id)
            assert row.operational_evidence_level == "High"


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    """DB sqlite tạm RIÊNG cho test này — không dùng chung DB của conftest."""
    import app.database as db_mod
    from app.config import settings
    from app.database import init_db

    db_path = tmp_path / "vong10_evidence_model.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
