"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 7,
task #92) trong `app/reports/evidence_workbench.py::_reference()` — PMID
KHÔNG phân giải được (chưa xác minh qua PubMed) vẫn hiện nguyên văn trong
trường `references`, đánh bại đúng cổng fail-closed `resolve_pmids()` sinh
ra để chống trích dẫn ma (sự cố EVID-0030, xem docstring `resolve_pmids()`).

CƠ CHẾ LỖI: `_item_to_data()` đúng khi CHỈ gắn `item["pmid"]` nếu
`resolved is None or str(r.pmid) in resolved` — nhưng gọi `_reference(r)`
KHÔNG truyền `resolved`, nên hàm này luôn thêm `"PMID {r.pmid}"` vào chuỗi
Vancouver bất kể có xác minh được hay không. Kết quả: một PMID giả/sai bị
SUPPRESS đúng ở `item["pmid"]` (dashboard JSON) nhưng vẫn hiện NGUYÊN VĂN
trong `item["references"][0]` — chuỗi mà `export_workbench_docx()` in
thẳng vào bản Word — như thể đã được xác minh.

BẢN VÁ: `_reference(r, resolved)` áp CÙNG điều kiện gating với
`item["pmid"]`.

Nguyên tắc viết test: gọi THẲNG `ew.build_data()` thật với `resolved` rỗng
(mô phỏng PMID không phân giải được), kiểm cả `item["pmid"]` LẪN
`item["references"][0]`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.reports import evidence_workbench as ew  # noqa: E402


def _fake_row(**kw):
    base = dict(title="Empagliflozin in CKD", journal_or_organization="N Engl J Med",
                source="pubmed", publication_date="2023-01-12", study_type="rct",
                clinical_area="Thận", reliability_tier="A", official_grade=None,
                is_actionable=True, classification="actionable",
                practice_change_score=80, evidence_quality_score=90,
                operational_evidence_level="High (operational)",
                authors="EMPA-KIDNEY Collaborative Group",
                abstract=("Background:\nPatients with chronic kidney disease were studied.\n\n"
                          "Results:\nEmpagliflozin reduced the primary outcome (hazard ratio 0.72; "
                          "95% CI 0.64 to 0.82; p<0.001).\n\nConclusion:\nEmpagliflozin slows CKD "
                          "progression and should be considered."),
                pmid="36331190", doi="10.1056/nejmoa2204233", nct_id=None,
                url="https://pubmed.ncbi.nlm.nih.gov/36331190/",
                safety_signal="Theo dõi tụt eGFR ban đầu; nhiễm nấm sinh dục.",
                synthesis={})
    base.update(kw)
    return SimpleNamespace(**base)


class TestPmidKhongPhanGiaiKhongDuocHienTrongReferences:
    """★★★ Ca chính — PMID không phân giải (resolved=set()) phải VẮNG MẶT
    trong cả item["pmid"] LẪN item["references"][0], không chỉ pmid."""

    def test_pmid_gia_bi_loai_khoi_ca_pmid_lan_references(self):
        rows = [_fake_row(pmid="99999999")]
        data = ew.build_data("Thận", rows, "2026-06-09", resolved=set())
        it = data["items"][0]
        assert "pmid" not in it
        assert "99999999" not in it["references"][0], (
            f"PMID chưa xác minh vẫn hiện trong references: {it['references'][0]!r}"
        )
        # DOI vẫn phải còn — vẫn truy nguyên được qua kênh khác.
        assert it["doi"]
        assert it["doi"] in it["references"][0]


class TestPmidPhanGiaiDuocVanHienNhuCu:
    """Đối chứng bắt buộc — PMID xác minh được (trong `resolved`) vẫn hiện
    đúng như hành vi gốc ở cả pmid lẫn references."""

    def test_pmid_da_xac_minh_hien_ca_hai_noi(self):
        rows = [_fake_row(pmid="36331190")]
        data = ew.build_data("Thận", rows, "2026-06-09", resolved={"36331190"})
        it = data["items"][0]
        assert it["pmid"] == "36331190"
        assert "36331190" in it["references"][0]


class TestResolvedNoneGiuHanhViCu:
    """Đối chứng bắt buộc — `resolved=None` (không bật xác minh, vd luồng
    offline/test cũ) vẫn hiện PMID như hành vi gốc, không bị chặn oan."""

    def test_resolved_none_van_hien_pmid_trong_references(self):
        rows = [_fake_row(pmid="36331190")]
        data = ew.build_data("Thận", rows, "2026-06-09", resolved=None)
        it = data["items"][0]
        assert it["pmid"] == "36331190"
        assert "36331190" in it["references"][0]
