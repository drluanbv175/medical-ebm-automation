"""Hồi quy: sổ chứng cứ A2b điền metadata từ CHÍNH kết quả PubMed của G0 (02/09/2026).

Khoảng hở đo được trên đề tài thật C1a: A2b để 12 dòng «[CẦN TRÍCH XUẤT METADATA]»
— việc TAY của chủ nhiệm — trong khi đủ tiêu đề/tạp chí/năm của ĐÚNG 12 PMID đó đã
nằm sẵn ở `G0_pubmed_raw.json` CÙNG THƯ MỤC, do chính G0 tra về trong cùng dây
chuyền (đo 12/12 phủ). Trong CÙNG lượt sinh, PMID nào có effect size thì title được
điền, số còn lại thì không — năng lực đã có, chỉ thiếu một đoạn dây. Đây là kiểu
«tự động hoá dở dang» đắt nhất: đẩy sang người thật một việc máy vừa làm ở dòng trên.

Khoá bốn hành vi:
1. Có bản ghi trong G0 ⇒ điền metadata; KHÔNG có ⇒ GIỮ nhãn (không bịa).
2. Chỉ cột METADATA — RoB và xác nhận nội dung vẫn là việc người thật.
3. Có dòng khai nguồn kèm ĐÚNG số dòng đã điền; không điền được thì không khai.
4. Dấu `|` trong tiêu đề không được phá cột bảng markdown.
"""

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import g1_quality_gate as G1Q  # noqa: E402

STUDY = "PYTEST-G1-META"
_G0_RAW = {
    "observational": [
        {"pmid": "34445940", "title": "Hài lòng người bệnh tại Việt Nam",
         "journal": "Hospital topics", "year": "2021"},
        {"pmid": "32584904", "title": "Thang đo | có dấu ống", "journal": "PloS one", "year": "2020"},
        {"pmid": "99999999", "title": "", "journal": "X", "year": "2020"},  # thiếu tiêu đề → bỏ
    ],
    "rct": [],
    "true_counts": {"rct": 0},  # khoá không phải list → không được làm chết hàm
}


def _seed(tmp_path: Path, raw=None) -> Path:
    d = tmp_path / STUDY
    d.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (d / "G0_pubmed_raw.json").write_text(json.dumps(raw, ensure_ascii=False),
                                              encoding="utf-8", newline="\n")
    return d


def _dung_a2b(d: Path, pmids: list[str]) -> str:
    G1Q.build_supporting_artifacts(
        study=STUDY, topic="Chủ đề thử", out_dir=d,
        design={"internal_code": "cross_sectional", "primary": "Cắt ngang",
                "reporting_standard": "STROBE 2007"},
        g0_checkpoint={"topic": "Chủ đề thử",
                       "pubmed_results": {"all_pmids": pmids}},  # hình dạng THẬT của C1a
        effects=[], meta={}, generated_at="2026-09-02T07:00:00+07:00")
    return (d / f"G1_A2b_EVIDENCE_LEDGER_{STUDY}.md").read_text(encoding="utf-8")


class TestMetadataTuG0:
    def test_doc_bang_pmid_bo_qua_ban_ghi_hong(self, tmp_path):
        d = _seed(tmp_path, _G0_RAW)
        bang = G1Q._metadata_tu_g0(d)
        assert bang["34445940"] == "Hài lòng người bệnh tại Việt Nam — Hospital topics (2021)"
        assert "99999999" not in bang, "thiếu tiêu đề thì không được điền gì"
        assert "|" not in bang["32584904"], "dấu ống phải bị thay để không phá cột bảng"

    def test_thieu_file_tra_bang_rong_khong_chet(self, tmp_path):
        assert G1Q._metadata_tu_g0(_seed(tmp_path)) == {}

    def test_dien_dung_dong_va_giu_nhan_cho_pmid_khong_co(self, tmp_path):
        d = _seed(tmp_path, _G0_RAW)
        text = _dung_a2b(d, ["34445940", "32584904", "11112222"])
        assert "Hài lòng người bệnh tại Việt Nam — Hospital topics (2021)" in text
        assert "| PMID:11112222 | [CẦN TRÍCH XUẤT METADATA] |" in text, "không có nguồn thì GIỮ nhãn"
        assert text.count("[CẦN TRÍCH XUẤT METADATA]") == 1

    def test_khong_dung_toi_cot_cua_nguoi_that(self, tmp_path):
        d = _seed(tmp_path, _G0_RAW)
        text = _dung_a2b(d, ["34445940"])
        assert text.count("[CẦN THẨM ĐỊNH RoB]") >= 1
        assert text.count("[CẦN XÁC NHẬN NỘI DUNG]") >= 1

    def test_dong_khai_nguon_dung_so_luong(self, tmp_path):
        d = _seed(tmp_path, _G0_RAW)
        assert "Cột **Metadata**: 2 dòng điền TỰ ĐỘNG" in _dung_a2b(d, ["34445940", "32584904"])

    def test_khong_dien_duoc_thi_khong_khai(self, tmp_path):
        d = _seed(tmp_path)
        text = _dung_a2b(d, ["11112222"])
        assert "dòng điền TỰ ĐỘNG" not in text, "không điền được thì không được khai là có"
        assert "[CẦN TRÍCH XUẤT METADATA]" in text
