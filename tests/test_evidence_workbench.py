"""Xuất Evidence Workbench: đúng schema DATA + qua được cổng liêm chính (offline)."""
import re
from types import SimpleNamespace

from app.reports import evidence_workbench as ew


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


def test_build_data_schema_and_mapping():
    rows = [_fake_row(), _fake_row(is_actionable=False, classification="watch_only",
                                   reliability_tier="C", pmid="32970396")]
    data = ew.build_data("Thận", rows, "2026-06-09", resolved={"36331190", "32970396"})
    assert data["meta"]["question"].startswith("Cập nhật chứng cứ — Thận")
    assert len(data["items"]) == 2
    it = data["items"][0]
    assert it["id"] == "ITEM-01"
    assert it["decision"] == "apply" and it["gradeLevel"] == "high"
    assert it["design"] == "RCT" and it["pmid"] == "36331190"
    assert it["pico"]["P"][1] in ("match", "mis")
    assert it["references"] and "36331190" in it["references"][0]


def test_unresolved_pmid_dropped_but_doi_kept():
    rows = [_fake_row(pmid="99999999")]   # PMID không phân giải
    data = ew.build_data("Thận", rows, "2026-06-09", resolved=set())
    it = data["items"][0]
    assert "pmid" not in it          # bỏ PMID lỗi
    assert it["doi"]                 # vẫn còn DOI -> truy nguyên được


def test_render_passes_integrity_gate_fields():
    """HTML render phải có disclaimer + gradeLevel/decision hợp lệ + định danh."""
    rows = [_fake_row()]
    data = ew.build_data("Thận", rows, "2026-06-09", resolved={"36331190"})
    html = ew.render_html(data)
    assert "Cần bác sĩ kiểm chứng" in html
    assert "const DATA = " in html and ew._DATA_END in html
    block = html[html.find("const DATA"):html.find(ew._DATA_END)]
    grade = re.search(r"gradeLevel:\"(\w+)\"", block).group(1)
    dec = re.search(r"decision:\"(\w+)\"", block).group(1)
    assert grade in {"high", "mod", "low", "vlow", "na"}
    assert dec in {"apply", "consider", "notyet"}


def test_js_serializer_escapes_script():
    out = ew._js({"x": "</script>alert(1)"})
    assert "</script>" not in out and "<\\/script>" in out


def test_dark_template_exists_and_same_markers():
    """Dark Analyst dùng CÙNG marker DATA -> render_html chèn được như EW sáng."""
    assert ew.DARK_TEMPLATE.exists()
    txt = ew.DARK_TEMPLATE.read_text(encoding="utf-8")
    assert "const DATA" in txt and ew._DATA_END in txt


def test_render_single_item_dark_html():
    rows = [_fake_row()]
    data = ew.build_data("Thận", rows, "2026-06-09", resolved={"36331190"})
    html = ew.render_html(data, ew.DARK_TEMPLATE)
    assert "Cần bác sĩ kiểm chứng" in html
    assert "const DATA = " in html and ew._DATA_END in html
    assert len(data["items"]) == 1


def _fake_score(**kw):
    base = dict(score_name="CURB-65", clinical_area="Hô hấp",
                clinical_situation="Viêm phổi cộng đồng — phân tầng nặng & nơi điều trị",
                action_thresholds="0–1 ngoại trú; 2 nhập viện ngắn; ≥3 nặng/ICU",
                components=["Confusion", "Urea", "RR", "BP", "Age≥65"],
                interpretation="Điểm cao → nguy cơ tử vong cao", limitations="Không thay lâm sàng",
                source="Lim WS, et al. Thorax 2003", guideline_reference="BTS",
                update_status="verified", url=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_score_to_data_frame_and_decision():
    it = ew._score_to_data(_fake_score(), 1)
    assert it["frame"] == "Thang điểm" and set(it["frameLabels"]) == {"P", "I", "C", "O"}
    assert it["decision"] == "apply" and it["gradeLevel"] == "high"
    assert it["pico"]["I"][0].startswith("Confusion")
    # chưa xác minh -> notyet, na
    it2 = ew._score_to_data(_fake_score(update_status="needs_verification"), 2)
    assert it2["decision"] == "notyet" and it2["gradeLevel"] == "na"


def test_scores_dashboard_renders_dark():
    html = ew.render_scores_dashboard([_fake_score(), _fake_score(score_name="qSOFA")],
                                      dark=True, vi=False)
    assert "Cần bác sĩ kiểm chứng" in html
    assert "Thang điểm" in html and ew._DATA_END in html
