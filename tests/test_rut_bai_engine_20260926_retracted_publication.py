"""Hồi quy synthesis #4 (26/09/2026): engine phải nhận nhãn rút bài của PubMed/Europe PMC.

CƠ CHẾ LỖI (đã tái lập): `pubmed._parse_efetch` chỉ dùng PublicationType để suy study_type, bỏ qua
«Retracted Publication»; `normalize` vứt `raw` ⇒ guideline đã rút được tier A/điểm 100, được tính
«đáng tin», lọt email «guideline mới» và bridge EBM_MASTER. Docstring `hang_do_manh` hứa «tầng sau
gắn cờ» nhưng không tầng nào làm.

BẢN VÁ: `_trang_thai_rut_bai(art)` (PubMed) và `trang_thai_rut_bai_epmc(r)` (Europe PMC) KHỚP ĐÚNG
TOKEN ⇒ raw["rut_bai"]; `normalize` ⇒ reason_for_exclusion (tier D) + `_rut_bai`; `classify` nhánh
đầu ⇒ 'excluded' kèm lý do rút bài; EoC ⇒ tối đa need_full_text, không Tier A; dedup lan cờ sang
bản chính; bản tin có mục đỏ riêng. «Retraction of Publication» (chính thông báo) KHÔNG bị loại.

Kiểm đột biến: bỏ nhánh classify / bỏ nhánh normalize / nới thành khớp chuỗi con 'retract' / bỏ
lan cờ dedup / bỏ mục đỏ của bản tin — mỗi phép phải làm đỏ đúng nhóm test.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.evidence_sufficiency import _chuan_hoa_va_cham, la_tin_cay  # noqa: E402
from app.services.filtering import (  # noqa: E402
    TIEN_TO_LY_DO_RUT_BAI,
    classify,
    la_ly_do_rut_bai,
)
from app.sources.base import RawRecord  # noqa: E402
from app.sources.europepmc import EuropePMCClient, trang_thai_rut_bai_epmc  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402

TIEU_DE_MANH = ("2025 guideline for the management of heart failure in outpatient primary care: "
                "recommendations for older adults with CKD")
# Tiêu đề KHÁC HẲN để dedup (so tiêu đề gần giống) không gộp bài sạch đối chứng vào nhóm bài rút.
TIEU_DE_SACH_KHAC = ("KDIGO 2025 clinical practice guideline recommendations on hypertension control "
                     "in outpatient primary care for older adults with CKD")
TOM_TAT_MANH = ("We recommend first-line therapy and dose adjustment in renal impairment; "
                "clinicians should no longer use the previous regimen.")


def _bai(pmid: str, pubtypes, cc=(), title: str = TIEU_DE_MANH, abstract: str = TOM_TAT_MANH,
         doi: str = "") -> str:
    """Một <PubmedArticle> dựng theo DTD pubmed_250101 (MedlineCitation/Article/PublicationTypeList,
    MedlineCitation/CommentsCorrectionsList)."""
    pt = "".join(f"<PublicationType>{p}</PublicationType>" for p in pubtypes)
    ccx = "".join(
        f'<CommentsCorrections RefType="{rt}"><RefSource>{src}</RefSource><PMID>{pm}</PMID>'
        f"</CommentsCorrections>" for rt, src, pm in cc)
    ds_cc = f"<CommentsCorrectionsList>{ccx}</CommentsCorrectionsList>" if cc else ""
    doi_x = (f'<ELocationID EIdType="doi" ValidYN="Y">{doi}</ELocationID>' if doi else "")
    return (f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article>"
            f"<Journal><Title>Circulation</Title><JournalIssue><PubDate><Year>2025</Year></PubDate>"
            f"</JournalIssue></Journal><ArticleTitle>{title}</ArticleTitle>{doi_x}"
            f"<Abstract><AbstractText>{abstract}</AbstractText></Abstract>"
            f"<AuthorList><Author><LastName>Nguyen</LastName><Initials>A</Initials></Author>"
            f"</AuthorList><PublicationTypeList>{pt}</PublicationTypeList></Article>{ds_cc}"
            f"</MedlineCitation></PubmedArticle>")


# Ba bộ pubtypes ĐÃ ĐO khi tái lập (verdict synthesis #4) + các ca biên.
CA = {
    "gl_rut": _bai("41110921", ["Journal Article", "Practice Guideline", "Retracted Publication"],
                   cc=[("RetractionIn", "Circulation. 2026;1:e1", "41999999")]),
    "rct_rut": _bai("40000002", ["Journal Article", "Randomized Controlled Trial",
                                 "Multicenter Study", "Retracted Publication"],
                    title="Randomized trial of drug X in heart failure"),
    "gl_rut_tieu_de_chung": _bai("40000003", ["Journal Article", "Practice Guideline",
                                              "Retracted Publication"],
                                 title="Clinical practice guideline", abstract=""),
    "chi_retraction_in": _bai("40000004", ["Journal Article", "Practice Guideline"],
                              cc=[("RetractionIn", "Lancet. 2026;2:3", "41888888")]),
    "thong_bao_rut": _bai("41999999", ["Journal Article", "Retraction of Publication"],
                          cc=[("RetractionOf", "Circulation. 2025;1:e0", "41110921")],
                          title="Retraction notice: 2025 guideline for heart failure"),
    "eoc": _bai("40000006", ["Journal Article", "Practice Guideline"],
                cc=[("ExpressionOfConcernIn", "Circulation. 2026;3:e9", "41777777")]),
    "thong_bao_eoc": _bai("41777777", ["Journal Article", "Expression of Concern"],
                          cc=[("ExpressionOfConcernFor", "Circulation. 2025", "40000006")],
                          title="Expression of concern: guideline for heart failure"),
    "sach": _bai("40000008", ["Journal Article", "Practice Guideline"],
                 cc=[("CommentIn", "Circulation. 2026;4:1", "41666666"),
                     ("ErratumIn", "Circulation. 2026;4:2", "41555555")]),
}
KY_VONG = {"gl_rut": "retracted", "rct_rut": "retracted", "gl_rut_tieu_de_chung": "retracted",
           "chi_retraction_in": "retracted", "thong_bao_rut": None, "eoc": "eoc",
           "thong_bao_eoc": None, "sach": None}


def _parse(ten: str) -> RawRecord:
    recs = PubMedClient()._parse_efetch(f"<PubmedArticleSet>{CA[ten]}</PubmedArticleSet>",
                                        "cardiology", "heart failure")
    assert len(recs) == 1, f"fixture {ten} không parse ra đúng 1 bản ghi"
    return recs[0]


@pytest.mark.parametrize("ten", sorted(CA))
def test_parse_efetch_gan_co_rut_bai_dung_token(ten):
    rec = _parse(ten)
    assert rec.raw.get("rut_bai") == KY_VONG[ten], (ten, rec.raw)
    assert rec.raw.get("publication_types"), "không được mất publication_types sẵn có"


def test_luat_retracted_trung_voi_parser_a12():
    """Luật «retracted» của dây chuyền khám phá phải TRÙNG cổng A12 (`_parse_retraction_xml`)."""
    xml = "<PubmedArticleSet>" + "".join(CA.values()) + "</PubmedArticleSet>"
    a12 = PubMedClient._parse_retraction_xml(xml, [])
    for ten in CA:
        pmid = _parse(ten).pmid
        la_rut_kham_pha = KY_VONG[ten] == "retracted"
        assert (a12[pmid]["status"] == "retracted") == la_rut_kham_pha, (ten, a12[pmid])


def test_thong_bao_rut_chua_pmid_thong_bao_trong_ly_do():
    item = _chuan_hoa_va_cham(_parse("gl_rut"))
    assert "41999999" in (item.get("reason_for_exclusion") or "")


@pytest.mark.parametrize("ten", ["gl_rut", "rct_rut", "gl_rut_tieu_de_chung", "chi_retraction_in"])
def test_bai_rut_ve_tier_d_khong_dang_tin_va_bi_loai(ten):
    item = _chuan_hoa_va_cham(_parse(ten))
    assert item["reliability_tier"] == "D", (ten, item["reliability_tier"])
    assert la_tin_cay(item) is False
    phan_loai, actionable, _a, ly_do = classify(item)
    assert phan_loai == "excluded" and actionable is False
    assert ly_do.startswith(TIEN_TO_LY_DO_RUT_BAI), f"lý do bị ghi đè chung chung: {ly_do!r}"


def test_doi_chung_cung_bai_khong_nhan_rut_thi_tier_a_actionable():
    """Đối chứng: fixture đủ mạnh — bỏ nhãn rút thì guideline này tier A/actionable/đáng tin.
    Vậy việc bị loại ở test trên là DO nhãn rút bài, không do fixture yếu."""
    xml = _bai("40000099", ["Journal Article", "Practice Guideline"])
    rec = PubMedClient()._parse_efetch(f"<PubmedArticleSet>{xml}</PubmedArticleSet>", "c", "q")[0]
    item = _chuan_hoa_va_cham(rec)
    assert item["reliability_tier"] == "A" and la_tin_cay(item) is True
    assert classify(item)[0] == "actionable"


@pytest.mark.parametrize("ten", ["thong_bao_rut", "thong_bao_eoc", "sach"])
def test_thong_bao_rut_va_dinh_chinh_khong_bi_loai_vi_rut_bai(ten):
    """Bất đối xứng: CHÍNH thông báo rút / thông báo quan ngại / erratum KHÔNG phải bài bị rút."""
    item = _chuan_hoa_va_cham(_parse(ten))
    assert not item.get("_rut_bai")
    assert not la_ly_do_rut_bai(classify(item)[3])


def test_eoc_toi_da_need_full_text_khong_tier_a():
    item = _chuan_hoa_va_cham(_parse("eoc"))
    assert item["reliability_tier"] != "A"
    phan_loai, actionable, _a, ly_do = classify(item)
    assert phan_loai == "need_full_text" and actionable is False
    assert "Expression of Concern" in ly_do


# ---------------------------------------------------------------------------
# Europe PMC
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ban_ghi,ky_vong", [
    ({"pubTypeList": {"pubType": ["Practice Guideline", "Retracted Publication"]}}, "retracted"),
    ({"pubType": "retracted publication; journal article"}, "retracted"),
    ({"commentCorrectionList": {"commentCorrection": [{"type": "Retraction in", "id": "1"}]}},
     "retracted"),
    ({"pubTypeList": {"pubType": ["Retraction of Publication"]},
      "commentCorrectionList": {"commentCorrection": [{"type": "Retraction of", "id": "2"}]}}, None),
    ({"commentCorrectionList": {"commentCorrection": [{"type": "Expression of concern in"}]}},
     "eoc"),
    ({"pubTypeList": {"pubType": ["Expression of Concern"]}}, None),
    ({"pubTypeList": {"pubType": ["Practice Guideline"]},
      "commentCorrectionList": {"commentCorrection": [{"type": "Erratum in"}]}}, None),
])
def test_europepmc_khop_dung_token(ban_ghi, ky_vong):
    assert trang_thai_rut_bai_epmc(ban_ghi) == ky_vong


def test_europepmc_search_gan_raw_rut_bai(monkeypatch):
    client = EuropePMCClient()
    monkeypatch.setattr(client, "use_mock", False)
    du_lieu = {"resultList": {"result": [
        {"id": "1", "source": "MED", "pmid": "41110921", "title": TIEU_DE_MANH,
         "journalTitle": "Circulation", "pubType": "practice guideline; retracted publication",
         "pubTypeList": {"pubType": ["Practice Guideline", "Retracted Publication"]},
         "abstractText": TOM_TAT_MANH},
        {"id": "2", "source": "MED", "pmid": "40000099", "title": TIEU_DE_MANH + " (bản sạch)",
         "journalTitle": "Circulation", "pubType": "practice guideline",
         "abstractText": TOM_TAT_MANH},
    ]}}
    monkeypatch.setattr(client.http, "get_json", lambda *a, **k: du_lieu)
    monkeypatch.setattr(client, "save_raw", lambda *a, **k: None)
    recs = client.search("heart failure guideline")
    assert [r.raw.get("rut_bai") for r in recs] == ["retracted", None]
    item = _chuan_hoa_va_cham(recs[0])
    assert item["reliability_tier"] == "D" and classify(item)[0] == "excluded"


# ---------------------------------------------------------------------------
# Đầu–cuối qua run_pipeline: dedup, bridge EBM_MASTER, bản tin
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_tam(monkeypatch, tmp_path):
    import app.database as db_mod
    from app.database import init_db

    db_file = tmp_path / "rut.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_file}")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    settings.ensure_dirs()
    init_db()
    yield db_file
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


def _chay_pipeline(monkeypatch):
    from app.services import pipeline as pipeline_mod

    # Bản Europe PMC KHÔNG mang cờ đứng TRƯỚC ⇒ thành bản chính; bản PubMed mang cờ là bản trùng.
    epmc_sach = RawRecord(source="europepmc", title=TIEU_DE_MANH, doi="10.1161/cir.2025.0001",
                          pmid="41110921", journal_or_organization="Circulation",
                          publication_date="2025", abstract=TOM_TAT_MANH,
                          document_type="practice guideline", study_type="guideline",
                          clinical_area="cardiology")
    pm_rut = _parse("gl_rut")
    pm_rut.doi = "10.1161/cir.2025.0001"
    pm_sach = PubMedClient()._parse_efetch(
        "<PubmedArticleSet>" + _bai("40000099", ["Journal Article", "Practice Guideline"],
                                    title=TIEU_DE_SACH_KHAC,
                                    doi="10.1161/cir.2025.0099") + "</PubmedArticleSet>",
        "cardiology", "q")[0]
    monkeypatch.setattr(settings, "use_mock_sources", False)
    return pipeline_mod.run_pipeline(records=[epmc_sach, pm_rut, pm_sach], incremental=False)


def _hang(db_file):
    con = sqlite3.connect(str(db_file))
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("SELECT * FROM evidence_items")]
    finally:
        con.close()


def test_dedup_lan_co_rut_sang_ban_chinh(db_tam, monkeypatch):
    _chay_pipeline(monkeypatch)
    hang = {(r["source"], r["pmid"]): r for r in _hang(db_tam)}
    chinh = hang[("europepmc", "41110921")]
    assert chinh["is_primary_record"] == 1, "fixture sai: bản Europe PMC phải là bản chính"
    assert chinh["classification"] == "excluded", chinh["classification"]
    assert chinh["reliability_tier"] == "D" and not chinh["is_actionable"]
    assert la_ly_do_rut_bai(chinh["reason_for_exclusion"])
    sach = hang[("pubmed", "40000099")]
    assert sach["classification"] == "actionable", "đối chứng: bài sạch vẫn actionable"


def test_bridge_ebm_master_khong_chon_ban_ghi_rut(db_tam, monkeypatch):
    """Chạy ĐÚNG câu SELECT của scripts/bridge_to_ebm_master.py trên DB sau pipeline."""
    _chay_pipeline(monkeypatch)
    nguon = (REPO_ROOT / "scripts" / "bridge_to_ebm_master.py").read_text(encoding="utf-8")
    m = re.search(r'con\.execute\("""\s*(SELECT \* FROM evidence_items.*?)"""\)', nguon, re.S)
    assert m, "không tìm thấy câu SELECT của bridge — cập nhật test nếu bridge đổi cấu trúc"
    con = sqlite3.connect(str(db_tam))
    con.row_factory = sqlite3.Row
    try:
        chon = [dict(r) for r in con.execute(m.group(1))]
    finally:
        con.close()
    pmid_chon = {r["pmid"] for r in chon}
    assert "41110921" not in pmid_chon, "bridge chọn bản ghi ĐÃ BỊ RÚT"
    assert "40000099" in pmid_chon, "đối chứng: bridge vẫn chọn guideline sạch tier A/actionable"


def test_ban_tin_co_muc_do_rieng_va_khong_liet_ke_guideline_rut(db_tam, monkeypatch):
    from app.reports.alert_digest import build_alert_data, render_alert_markdown

    _chay_pipeline(monkeypatch)
    data = build_alert_data(days=7)
    pmid_gl = {r.pmid for r in data["guidelines"] + data["actionable"] + data["need_full_text"]}
    assert "41110921" not in pmid_gl, "bản tin liệt kê bài đã rút như guideline/actionable"
    assert {r.pmid for r in data["retracted"]} == {"41110921"}
    md = render_alert_markdown(data)
    assert "⛔ Bài đã bị rút — KHÔNG dùng (1)" in md
    assert "40000099" in md, "đối chứng: guideline sạch vẫn có trong bản tin"
