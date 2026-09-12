"""Hồi quy vá R4 `check_de_cuong.py` 2026-08-30 — tầng BIÊN NHẬN ngoài-pipeline.

Lỗi thật (họ BH08, đo trên đề cương C1a cùng ngày): 10 PMID phương pháp luận
(STROBE 18313558, COSMIN 20494804, Bull 31218671...) được xác minh SỐNG qua kênh
PubMed-MCP nhưng kênh đó không để lại dấu vết nào mà R4 đọc được ⇒ R4 gắn nhãn
"nghi bịa" cho toàn bộ — biến "xác minh không có biên nhận máy-đọc" thành "bịa".

Hợp đồng mới:
- PMID không ở raw/seed/biên-nhận ⇒ vẫn FAIL (không nới cửa bịa).
- Biên nhận hợp lệ ⇒ hạ FAIL→WARN, thông điệp NÊU RÕ mức bảo đảm "TỰ KHAI CÓ
  DẤU VẾT" — không bao giờ thành PASS im lặng (chống tự-chứng-nhận).
- Biên nhận QUÁ HẠN 180 ngày ⇒ KHÔNG cứu được, lỗi nói rõ vì sao (không phải
  "nghi bịa" câm — người đọc biết đường sửa là xác minh lại).
- Mục biên nhận hỏng (sai pmid/ngày) ⇒ không được tính, có cảnh báo riêng.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import check_de_cuong as CDC  # noqa: E402

PMID_LA = "31218671"  # Bull 2019 — chính PMID bị gắn nhãn nhầm trong ca thật


def _mk_doc(tmp_path: Path) -> Path:
    p = tmp_path / "de_cuong.md"
    p.write_text(
        f"# Đề cương thử\nTrích dẫn nền: PMID: {PMID_LA}.\n"
        "Cần bác sĩ kiểm chứng.\n",
        encoding="utf-8",
        newline="\n",
    )
    return p


def _write_receipt(out_dir: Path, muc: list) -> None:
    (out_dir / CDC.BIEN_NHAN_XAC_MINH).write_text(
        json.dumps({"phien_ban": 1, "muc": muc}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def _r4(report: dict) -> str:
    return report["checks"]["R4_pmid_traceable"]


def _r4_errors(report: dict) -> list:
    return [e for e in report["errors"] if e.startswith("R4")]


class TestReceiptTier:
    def test_no_receipt_unknown_pmid_still_fails(self, tmp_path):
        md = _mk_doc(tmp_path)
        report = CDC.validate(md, tmp_path)
        assert _r4(report).startswith("FAIL"), report["checks"]
        assert any("nghi bịa" in e for e in _r4_errors(report))

    def test_valid_receipt_downgrades_to_warn_with_assurance_level(self, tmp_path):
        md = _mk_doc(tmp_path)
        _write_receipt(
            tmp_path,
            [{"pmid": PMID_LA, "ngay": datetime.date.today().isoformat(),
              "kenh": "PubMed (MCP get_article_metadata)"}],
        )
        report = CDC.validate(md, tmp_path)
        assert _r4(report).startswith("WARN"), report["checks"]
        assert not _r4_errors(report)
        canh_bao = [w for w in report["warnings"] if "BIÊN NHẬN" in w]
        assert canh_bao, "phải có cảnh báo nêu đường truy biên nhận"
        assert any("TỰ KHAI CÓ DẤU VẾT" in w for w in canh_bao), (
            "mức bảo đảm phải được NÓI RA — hạ FAIL→WARN im lặng là tự-chứng-nhận"
        )
        assert any("rút bài" in w for w in canh_bao), (
            "phải nhắc biên nhận KHÔNG bảo đảm trạng thái rút bài"
        )

    def test_expired_receipt_does_not_rescue(self, tmp_path):
        md = _mk_doc(tmp_path)
        qua_han = datetime.date.today() - datetime.timedelta(
            days=CDC.BIEN_NHAN_HAN_NGAY + 1
        )
        _write_receipt(
            tmp_path,
            [{"pmid": PMID_LA, "ngay": qua_han.isoformat(), "kenh": "PubMed"}],
        )
        report = CDC.validate(md, tmp_path)
        assert _r4(report).startswith("FAIL"), report["checks"]
        assert any("QUÁ HẠN" in e for e in _r4_errors(report)), (
            "lỗi phải nói rõ biên nhận quá hạn — đường sửa là xác minh lại, "
            "không phải một cờ 'nghi bịa' câm"
        )

    def test_malformed_entries_not_counted_and_flagged(self, tmp_path):
        md = _mk_doc(tmp_path)
        _write_receipt(
            tmp_path,
            [
                {"pmid": "abc123", "ngay": datetime.date.today().isoformat()},
                {"pmid": PMID_LA, "ngay": "khong-phai-ngay"},
            ],
        )
        report = CDC.validate(md, tmp_path)
        assert _r4(report).startswith("FAIL"), (
            "mục hỏng không được lặng lẽ tính là đã xác minh (fail-closed)"
        )
        assert any("mục hỏng" in w for w in report["warnings"])

    def test_raw_verified_stays_pass_untouched_by_receipt(self, tmp_path):
        md = _mk_doc(tmp_path)
        (tmp_path / "G0_pubmed_raw.json").write_text(
            json.dumps({"articles": [{"pmid": PMID_LA}]}),
            encoding="utf-8",
            newline="\n",
        )
        _write_receipt(
            tmp_path,
            [{"pmid": PMID_LA, "ngay": datetime.date.today().isoformat()}],
        )
        report = CDC.validate(md, tmp_path)
        assert _r4(report).startswith("PASS"), (
            "PMID đã đối chiếu raw phải giữ PASS — biên nhận không hạ cấp raw"
        )
