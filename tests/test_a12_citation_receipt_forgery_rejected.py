"""Hồi quy (vòng audit đối kháng 3, 2026-07-16): citation_verification_ok() (cổng A12,
tools/run_g10_assemble.py) trước đây chỉ đối chiếu pmids_hash — công thức CÔNG KHAI
(tools/check_citation_retraction.py::pmids_hash(), không khóa bí mật), nên bất kỳ ai/agent
nào cũng tự viết tay MỘT receipt "sạch" (all_clean=true) rồi tự tính đúng hash cho khớp
pmids_checked, KHÔNG cần thật sự gọi PubMed — tái hiện được bằng script độc lập TRƯỚC khi
vá. Vá: receipt giờ mang thêm `receipt_signature` (HMAC, cùng khóa cục bộ dùng cho phê
duyệt G2/G4/G8/G9) — thiếu/sai chữ ký khi máy CÓ khóa → chặn; đề tài THẬT mà máy CHƯA có
khóa → cũng chặn (fail-closed), không hạ chuẩn.

Dùng out_dir=tmp_path/... xuyên suốt — KHÔNG bao giờ đụng vào exports/ thật.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import check_citation_retraction as CCR  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

REAL_STUDY = "hai-long-benh-nhan-C1a-BVQY175"


def _write_clean_artifact(out_dir: Path, study: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
        "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n",
        encoding="utf-8",
    )


def _write_forged_receipt(out_dir: Path, study: str, pmids: list[str]) -> None:
    """Receipt do 'kẻ giả mạo' tự viết tay — tính ĐÚNG pmids_hash (công khai) nhưng
    KHÔNG có receipt_signature (không có khóa bí mật thật)."""
    receipt = {
        "study": study,
        "checked_at_utc": "2026-07-16T00:00:00+00:00",
        "pmids_checked": sorted(pmids),
        "pmids_hash": CCR.pmids_hash(pmids),
        "all_clean": True,
        "results": {p: {"status": "ok"} for p in pmids},
    }
    (out_dir / "A12_RETRACTION_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False), encoding="utf-8"
    )


def test_forged_receipt_rejected_when_key_configured(tmp_path, monkeypatch):
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-real-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    out_dir = tmp_path / "exports" / REAL_STUDY
    _write_clean_artifact(out_dir, REAL_STUDY)
    _write_forged_receipt(out_dir, REAL_STUDY, ["12345678"])

    ok, reason = G10.citation_verification_ok(REAL_STUDY, out_dir)
    assert ok is False
    assert "chữ ký" in reason


def test_forged_receipt_rejected_for_real_study_when_no_key_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))
    assert GC.signing_key_configured() is False

    out_dir = tmp_path / "exports" / REAL_STUDY
    _write_clean_artifact(out_dir, REAL_STUDY)
    _write_forged_receipt(out_dir, REAL_STUDY, ["12345678"])

    ok, reason = G10.citation_verification_ok(REAL_STUDY, out_dir)
    assert ok is False
    assert "fail-closed" in reason


def test_legitimate_signed_receipt_still_passes(tmp_path, monkeypatch):
    """Đối chứng bắt buộc: receipt THẬT (ghi bởi write_retraction_receipt(), có chữ ký
    hợp lệ) vẫn qua cổng bình thường — bản vá không chặn nhầm luồng đúng.

    monkeypatch.setattr (KHÔNG phải gán tay CCR.REPO_ROOT = ...) — module check_citation_
    retraction được cache trong sys.modules và dùng lại bởi NHIỀU test file khác; gán tay
    sẽ rò rỉ giá trị tmp_path sang các test chạy SAU trong cùng phiên pytest (đã tự bắt
    được lỗi này: 3 test khác trong test_check_citation_retraction.py fail vì REPO_ROOT bị
    đổi vĩnh viễn). monkeypatch tự phục hồi giá trị gốc khi test này kết thúc."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-real-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    monkeypatch.setattr(CCR, "REPO_ROOT", tmp_path)

    study = "PYTEST-A12-FORGE-OK1"
    out_dir = tmp_path / "exports" / study
    _write_clean_artifact(out_dir, study)

    # Ghi receipt qua ĐÚNG hàm thật (không giả lập tay).
    CCR.write_retraction_receipt(study, ["12345678"], {"12345678": {"status": "ok"}})

    ok, reason = G10.citation_verification_ok(study, out_dir)
    assert ok is True, reason
