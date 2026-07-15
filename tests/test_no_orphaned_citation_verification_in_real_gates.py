"""Chặn nhánh mồ côi THỨ 4 (app/evidence/citation_verification.py + friends) bị nối
dây vào cổng THẬT — cùng mục đích với TestNoResearchProjectImportInRealGates trong
tests/test_stakeholder_review_audit.py (canh nhánh mồ côi THỨ 2, research_project/),
viết riêng file này vì đây là 2 nhánh mồ côi KHÁC NHAU (xem CLAUDE.md gốc mục
"5 nhánh mồ côi khác", mục (2) và (4)).

Bối cảnh: `app/evidence/citation_verification.py` + `phase_2d_claim_mapping_validator.py`
+ `retraction_monitor.py` là một hệ claim/citation/retraction-tracking THỨ HAI, song
song với `research_project/project_claim_traceability.py` (đã bị canh) — cả hai đều
KHÔNG được `tools/run_g7_auto.py`/`run_g9_auto.py`/`run_g10_assemble.py` gọi tới.
`retraction_monitor.detect_retraction()` của nhánh này chỉ đọc chữ "retracted"/
"withdrawn" ĐÃ CÓ SẴN trong metadata truyền vào — KHÔNG tự tra cứu gì, khác hẳn cơ
chế THẬT đang dùng (`app/sources/pubmed.py::PubMedClient.check_retraction_status()`,
gọi PubMed E-utilities thật — Ngày 4 lộ trình 7 ngày, `tools/check_citation_retraction.py`).

Nếu ai đó vô tình import 1 trong 3 module này vào 1 file cổng thật, cổng đó sẽ
ÂM THẦM dùng cơ chế retraction-check GIẢ (chỉ đọc field có sẵn, không tra cứu) thay
vì cơ chế THẬT — một loại lỗi khó phát hiện bằng mắt vì tên hàm/module rất giống
nhau (`citation_verification`/`retraction_monitor` xuất hiện ở CẢ 2 nhánh).
"""
from __future__ import annotations

from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"

_ORPHANED_IMPORT_PATTERNS = (
    "import app.evidence.citation_verification",
    "from app.evidence.citation_verification",
    "from app.evidence import citation_verification",
    "import app.evidence.phase_2d_claim_mapping_validator",
    "from app.evidence.phase_2d_claim_mapping_validator",
    "from app.evidence import phase_2d_claim_mapping_validator",
    "import app.evidence.retraction_monitor",
    "from app.evidence.retraction_monitor",
    "from app.evidence import retraction_monitor",
)

# Cùng danh sách 6 file cổng thật với TestNoResearchProjectImportInRealGates, cộng
# thêm 2 file THẬT liên quan trực tiếp tới citation/retraction (Ngày 1 + Ngày 4 lộ
# trình 7 ngày) mà bản danh sách gốc không có lý do để canh (vì lúc đó chưa tồn tại).
_REAL_GATE_FILES = (
    "run_g2_auto.py",
    "run_g4_auto.py",
    "run_g7_auto.py",
    "run_g8_auto.py",
    "run_g9_auto.py",
    "run_g10_assemble.py",
    "run_stats_analysis.py",
    "check_citation_retraction.py",
)


class TestNoOrphanedCitationVerificationImportInRealGates:
    def test_none_of_the_real_gate_files_import_orphaned_citation_branch(self):
        offenders = []
        for fname in _REAL_GATE_FILES:
            path = TOOLS_DIR / fname
            assert path.exists(), f"File cổng thật không tồn tại: {path}"
            text = path.read_text(encoding="utf-8")
            hits = [p for p in _ORPHANED_IMPORT_PATTERNS if p in text]
            if hits:
                offenders.append((fname, hits))
        assert offenders == [], (
            f"Các file cổng thật sau đây đã import nhánh mồ côi "
            f"app/evidence/citation_verification.py (KHÔNG được phép): {offenders}"
        )

    def test_real_pubmed_retraction_check_is_not_the_orphaned_one(self):
        """Xác nhận app/sources/pubmed.py (cơ chế THẬT) không lẫn logic từ nhánh mồ
        côi — bắt trường hợp ai đó copy-paste detect_retraction() giả vào chỗ thật."""
        pubmed_path = Path(__file__).resolve().parents[1] / "app" / "sources" / "pubmed.py"
        text = pubmed_path.read_text(encoding="utf-8")
        hits = [p for p in _ORPHANED_IMPORT_PATTERNS if p in text]
        assert hits == [], f"app/sources/pubmed.py đã import nhánh mồ côi: {hits}"
