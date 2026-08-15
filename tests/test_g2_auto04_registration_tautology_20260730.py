"""Hồi quy G2-F1 (audit toàn diện G0-G10, 2026-07-30, HIGH — 1/3 tiêu chí):

tools/g2_quality_gate.py::_registration_draft_errors() trước vá này CHỈ kiểm
số lượng mục (24), nhãn (WHO_TRDS_LABELS) và phiên bản (WHO_TRDS_VERSION) —
cả ba đều do CHÍNH build_registration_draft() (cùng file) sinh ra từ CÙNG các
hằng số mà _registration_draft_errors() đọc lại để so khớp. Không có đầu vào
thật nào (topic, design_code, dữ liệu bác sĩ) có thể khiến hai bên lệch nhau
— G2-AUTO-04 dùng hàm này về mặt toán học KHÔNG BAO GIỜ có thể BLOCK.

Vá: thêm kiểm tra mục 9 (Public Title) và mục 10 (Scientific Title) phải có
nội dung — cả hai lấy từ `topic` (chuỗi THẬT của đề tài, do bác sĩ/G0 cung
cấp). Nếu topic rỗng (đề tài chưa từng chạy G0 thật, hoặc truyền topic rỗng
qua CLI), lỗi này MỚI thật sự xuất hiện — closed the tautology bằng một phụ
thuộc dữ liệu thật thay vì tự so khớp với chính mình."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g2_quality_gate as G2Q  # noqa: E402


def _draft(tmp_path: Path, topic: str) -> dict:
    path = G2Q.build_registration_draft(
        study="TEST-G2-AUTO04",
        topic=topic,
        design_code="rct",
        design_primary="Thử nghiệm ngẫu nhiên có đối chứng",
        risk={
            "registration": "BẮT BUỘC trước tuyển mẫu",
            "register_where": "ClinicalTrials.gov",
        },
        n_target=200,
        out_dir=tmp_path,
        generated_at="2026-07-30T10:00:00+07:00",
    )
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_topic_produces_zero_errors(tmp_path):
    document = _draft(tmp_path, "Can thiệp X ở người trưởng thành có bệnh Y")
    errors = G2Q._registration_draft_errors(document)
    assert errors == []


def test_public_title_item_populated_from_topic_not_none(tmp_path):
    document = _draft(tmp_path, "Can thiệp X ở người trưởng thành có bệnh Y")
    item9 = next(i for i in document["items"] if i["number"] == 9)
    assert item9["value"] == "Can thiệp X ở người trưởng thành có bệnh Y"


def test_empty_topic_is_caught_not_silently_passed(tmp_path):
    document = _draft(tmp_path, "")
    errors = G2Q._registration_draft_errors(document)
    assert any("mục 9" in e for e in errors)
    assert any("mục 10" in e for e in errors)


def test_whitespace_only_topic_is_caught(tmp_path):
    document = _draft(tmp_path, "   ")
    errors = G2Q._registration_draft_errors(document)
    assert any("mục 9" in e for e in errors)


def test_tampered_document_with_none_item9_is_caught_even_with_real_topic(tmp_path):
    """Mô phỏng tampering: mọi thứ khác đúng (24 mục, nhãn, version) nhưng
    mục 9 bị ghi đè thành None — trước vá này sẽ PASS OAN vì hàm cũ không
    đọc value; sau vá này phải BLOCK."""
    document = _draft(tmp_path, "Can thiệp X ở người trưởng thành có bệnh Y")
    for item in document["items"]:
        if item["number"] == 9:
            item["value"] = None
    errors = G2Q._registration_draft_errors(document)
    assert any("mục 9" in e for e in errors)
