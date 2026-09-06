r"""Hồi quy phát hiện #1 (MEDIUM) của audit đa-agent 2026-09-06 (vòng 31) trong
tools/skill_standards.py::_status_is_locked() — ranh giới từ `\b` coi `_` là
ký tự "từ" nên KHÔNG khớp được với chính giá trị THẬT hệ thống dùng làm
chuẩn "đã khóa dữ liệu".

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _status_is_locked(status):
        ...
        return re.search(r"\bLOCKED\b", up) is not None

Trong regex Python, `\w` (và do đó `\b`) coi dấu gạch dưới `_` là ký tự
"thuộc từ". Vì vậy `\bLOCKED\b` KHÔNG có ranh giới ở giữa "D" và "_" trong
chuỗi kiểu SCREAMING_SNAKE_CASE — không khớp được với "LOCKED_FOR_ANALYSIS"
hay "LOCKED_REAL_SIGNAL".

Nhưng đây CHÍNH LÀ định dạng THẬT mà hệ thống dùng:
    tools/lock_analysis_dataset.py:
        LOCKED_STATUS = "LOCKED_FOR_ANALYSIS"          # dòng 53
        ...
        "status": LOCKED_STATUS if not blockers else BLOCKED_STATUS   # dòng 621
        checkpoint["database_lock_status"] = manifest["status"]        # dòng 697

`_status_is_locked()` được `real_world_signals()` gọi ở nhánh TƯƠNG THÍCH
(khi checkpoint G5 KHÔNG có `quality_contract_version` — dòng 824-826 của
skill_standards.py): `db = _status_is_locked(g5.get("database_lock_status"))
or _is_real_value(meta.get("data_lock_date"))`. Một checkpoint G5 hợp lệ
mang đúng giá trị "LOCKED_FOR_ANALYSIS" (dữ liệu ĐÃ khóa thật) vẫn bị hàm
này báo `False` — "chưa khóa" — sai sự thật ngược hướng fail-closed cho
đúng cổng cứng G5 (Cổng An toàn dữ liệu) mà toàn hệ coi là quan trọng nhất.

Test cũ (tests/test_skill_standards.py, dòng 160-165) chỉ dùng "LOCKED
2026-09-01" (có khoảng trắng, ranh giới còn nguyên) — không phủ định dạng
gạch dưới thật của lock_analysis_dataset.py, nên lỗ hổng chưa từng bị bắt.

BẢN VÁ: đổi `\bLOCKED\b` thành `(?<![A-Z])LOCKED(?![A-Z])` — ranh giới CHỮ
CÁI (không tính `_`/số): "LOCKED" không được có chữ cái NGAY TRƯỚC/SAU.
Vẫn loại đúng "BLOCKED..." (B là chữ cái liền trước, không khớp) và
"UNLOCKED" (đã bị chặn ở lớp phủ định `UNLOCK` phía trên, không đổi).

Nguyên tắc viết test:
1. Ca chính — "LOCKED_FOR_ANALYSIS"/"LOCKED_REAL_SIGNAL"/"LOCKED_REAL_EVIDENCE"
   (giá trị THẬT của lock_analysis_dataset.py/audit_research_gates.py) phải
   được nhận diện là ĐÃ KHÓA.
2. Ca chính đầu-cuối — real_world_signals() với checkpoint G5 legacy (không
   có quality_contract_version) mang database_lock_status="LOCKED_FOR_ANALYSIS"
   phải trả tín hiệu database_locked=True.
3. Đối chứng — mọi ca đã có trong test cũ (LOCKED/UNLOCKED/NOT LOCKED/CHƯA
   LOCKED/PENDING/DATABASE LOCKED...) vẫn giữ nguyên kết quả; đặc biệt
   "BLOCKED_DATA_LOCK_REQUIREMENTS" (giá trị THẬT khi data lock BỊ CHẶN,
   cùng module lock_analysis_dataset.py) vẫn phải là False — bản vá không
   được biến trạng thái BLOCKED thành LOCKED."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import skill_standards as S  # noqa: E402


class TestStatusIsLockedNhanDienGachDuoiThat:
    """★★★ Ca chính — giá trị THẬT dạng SCREAMING_SNAKE_CASE của
    lock_analysis_dataset.py/audit_research_gates.py phải được nhận diện."""

    def test_locked_for_analysis(self):
        assert S._status_is_locked("LOCKED_FOR_ANALYSIS") is True, (
            "TRƯỚC bản vá: \\bLOCKED\\b không khớp vì '_' được \\w coi là ký tự "
            "từ — đây CHÍNH LÀ giá trị lock_analysis_dataset.py ghi khi khóa "
            "dữ liệu THÀNH CÔNG (LOCKED_STATUS, dòng 53/621/697)."
        )

    def test_locked_real_signal(self):
        assert S._status_is_locked("LOCKED_REAL_SIGNAL") is True

    def test_locked_real_evidence(self):
        assert S._status_is_locked("LOCKED_REAL_EVIDENCE") is True


class TestDauCuoiRealWorldSignalsG5Legacy:
    """★★★ Ca chính đầu-cuối — checkpoint G5 legacy (không có
    quality_contract_version) mang database_lock_status THẬT phải khiến
    real_world_signals() báo database_locked=True."""

    def test_g5_legacy_locked_for_analysis_bao_da_khoa(self):
        checkpoints = {
            "G2": {}, "G4": {}, "G5": {"database_lock_status": "LOCKED_FOR_ANALYSIS"},
        }
        tin_hieu = S.real_world_signals(checkpoints, meta={})
        assert tin_hieu["db_locked"] is True, (
            "TRƯỚC bản vá: checkpoint G5 hợp lệ (đã khóa thật, đúng giá trị "
            "lock_analysis_dataset.py ghi) vẫn báo db_locked=False."
        )


class TestDoiChungHanhViCuKhongDoi:
    """Đối chứng — mọi ca test cũ (test_skill_standards.py dòng 160-165) giữ
    nguyên kết quả; BLOCKED_DATA_LOCK_REQUIREMENTS (giá trị THẬT khi bị chặn,
    cùng module) vẫn phải là False."""

    def test_locked_don_gian(self):
        assert S._status_is_locked("LOCKED") is True

    def test_unlocked(self):
        assert S._status_is_locked("UNLOCKED") is False

    def test_not_locked(self):
        assert S._status_is_locked("NOT LOCKED") is False

    def test_chua_locked(self):
        assert S._status_is_locked("CHƯA LOCKED") is False

    def test_pending(self):
        assert S._status_is_locked("PENDING — chưa thu thập") is False

    def test_database_locked_co_khoang_trang(self):
        assert S._status_is_locked("DATABASE LOCKED 2026-09-01") is True

    def test_locked_co_khoang_trang_va_ngay(self):
        assert S._status_is_locked("LOCKED 2026-09-01") is True

    def test_blocked_data_lock_requirements_khong_phai_da_khoa(self):
        assert S._status_is_locked("BLOCKED_DATA_LOCK_REQUIREMENTS") is False, (
            "Giá trị THẬT khi lock_analysis_dataset.py CHẶN khóa (có blockers) — "
            "'B' đứng ngay trước 'LOCKED' nên không được coi là đã khóa."
        )

    def test_none_va_rong(self):
        assert S._status_is_locked(None) is False
        assert S._status_is_locked("") is False
