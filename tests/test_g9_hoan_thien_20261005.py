# -*- coding: utf-8 -*-
"""Soát từng cổng G9 (05/10/2026) — kiểm hồi quy cho từng phát hiện, kèm chuỗi THẬT G0→G8 PASS → G9.

G9-01 Ô trống: _real_text AND placeholder_contract.co_noi_dung_that («___», «-», «[TO BE COMPLETED]», «[đơn vị]»… không
      còn là «đã điền»); _documents_clean quét A10/checklist/cover letter bằng hợp đồng chung (cover letter thêm «___»),
      bản thảo bằng CHÍNH bộ quét G8; khuôn sinh không còn ô mẫu không nhãn.
      Bổ sung: _PLACEHOLDER_RE không còn chặn oan «[Todorov 2020]», «[can thiệp giáo dục]».
G9-02 reporting_checklist_path không mặc định trỏ vào A9; trỏ vào A9 ⇒ REVIEW có hướng dẫn.
G9-03 Phần 7 thành tệp riêng (A10 chỉ trỏ); chấm lại: R2 (DOI người điền) và R4 (gỡ nhãn nháp) chỉ còn cảnh báo; R2 xét
      MỌI DOI.
G9-04 G9-AUTO-03 đòi G8 chấm SỐNG PASS_G8_REVIEW_RECORDED — bản thảo sửa sau bình duyệt ⇒ không READY.
G9-05 Thiết kế rct (resolve_design_code) mà data_availability.clinical_trial ≠ true ⇒ HUMAN-05 REVIEW.
G9-06 Chạy lại run_g9_auto không đè mất bản người đã sửa (.bak; chỉ khác mốc thời gian thì không); --n-authors tường
      minh ghi đè pin; số tác giả đổi ⇒ chỉ dựng lại mảng authors, giữ khối khác.
G9-07 Tên vai trò CRediT chép nguyên (gạch ngang dài) được nhận; vai trò sai được nêu tên.
G9-09 A10 dùng AUTHOR-NN; email/điện thoại trong A10 ⇒ G9-AUTO-06 CHẶN.
G9-10 skill_standards không còn tin trường g9_quality_status (không ai ghi).
Điều phối G8↔G9: khai báo AI và quyết định chia sẻ dữ liệu của G9 phải khớp G8; «G2 đã duyệt» = g2_da_duyet dùng chung.
Mọi luồng có ký chạy trong pytest với khoá giả tạm. Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402
import cong_song as CS  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import g9_quality_gate as G9Q  # noqa: E402
import placeholder_contract as PC  # noqa: E402
import run_g9_auto as G9A  # noqa: E402
import skill_standards as SS  # noqa: E402

from tests.g5_test_helpers import append_signed_approval  # noqa: E402
from tests.test_g8_hoan_thien_20261004 import _cham8, _de_tai_g8_that, _ghi, _ky_g8  # noqa: E402
from tests.test_g9_quality_gate import (  # noqa: E402
    _complete_readiness,
    _patch_upstream,
    _prepare_study,
    _write_json,
    ghi_checklist_bao_cao,
)


def _ck(bao: dict, ma: str) -> dict:
    return next(r for r in bao["automatic_criteria"] if r["id"] == ma)


def _chay_g9(goc: Path, study: str, monkeypatch, *them: str) -> tuple[int, str]:
    monkeypatch.setattr(G9A, "_REPO_ROOT", goc)
    monkeypatch.setattr(sys, "argv", ["run_g9_auto.py", "--study", study, *them])
    CS.xoa_dem()
    ma, buf = 0, io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            G9A.main()
    except SystemExit as exc:
        ma = int(exc.code or 0)
    CS.xoa_dem()
    return ma, buf.getvalue()


def _cham9(study: str, out: Path, goc: Path, *, write: bool = False) -> dict:
    CS.xoa_dem()
    return G9Q.evaluate_study(study, out, repo_root=goc, write=write)


# ── Chuỗi THẬT G0→G8 PASS → G9 ──────────────────────────────────────────────────────────────────────────────────────

_O_CAN_RE = re.compile(r"\[\s*CẦN[^\]\n]*\]")


def _dien_nhu_nguoi_that(text: str) -> str:
    """Tác giả hoàn tất khuôn: soạn mọi ô [CẦN …], gỡ nhãn nháp DRAFT/CHỜ của gói đã chốt (R4 chỉ còn cảnh báo khi
    chấm lại), điền dòng ký «___»."""
    text = _O_CAN_RE.sub("nội dung tác giả đã soạn", text)
    text = text.replace("DRAFT", "BẢN CHỐT").replace("CHỜ", "ĐÃ")
    return re.sub(r"_{3,}", "đã điền", text)


_METADATA_THU = {"title": "Nguồn thử nghiệm tổng hợp", "authors": ["Tác giả A", "Tác giả B"],
                 "journal": "Tạp chí thử nghiệm", "year": "2018"}


def _de_tai_g9_that(tmp_path: Path, monkeypatch, thiet_ke: str = "cohort",
                    pmid_a12: tuple = ("12345678",)) -> tuple[str, Path, Path]:
    """G0→G7 PASS → G8 PASS_G8_REVIEW_RECORDED (người phản biện ký bằng khoá giả riêng nhóm) → run_g9_auto (2 tác giả)
    → tác giả/PI hoàn tất A10, cover letter, checklist chuẩn báo cáo, hồ sơ readiness (khớp khai báo G8) → chấm G9
    ghi manifest. `pmid_a12`: toàn bộ PMID gói sẽ trích (vd thêm PMID nguồn giả định G3 mà đề cương G10 in) — chạy A12
    (rút bài + metadata) trên ĐỦ danh sách TRƯỚC khi PI ký G9, như người thật."""
    study, out, goc = _de_tai_g8_that(tmp_path, monkeypatch, thiet_ke)
    _ky_g8(study, out, goc)
    assert _cham8(study, out, goc)["status"] == G8Q.STATUS_REVIEWED
    ma, _in = _chay_g9(goc, study, monkeypatch, "--n-authors", "2", "--target-journal", "Journal of Test Medicine")
    assert ma == 0
    for ten in (f"G9_A10_AUTHOR_INTEGRITY_{study}.md", f"G9_COVER_LETTER_{study}.md"):
        p = out / ten
        _ghi(p, _dien_nhu_nguoi_that(p.read_text(encoding="utf-8")))
    ghi_checklist_bao_cao(out, study)
    # A12 metadata: chạy check_citation_metadata như bước thật (chuỗi G7 đã có receipt rút bài cho PMID gốc).
    monkeypatch.setattr(CCM, "REPO_ROOT", goc)
    if tuple(pmid_a12) != ("12345678",):
        import check_citation_retraction as CCR  # noqa: PLC0415

        monkeypatch.setattr(CCR, "REPO_ROOT", goc)
        CCR.write_retraction_receipt(study, list(pmid_a12), {p: {"status": "ok"} for p in pmid_a12})
    CCM.write_metadata_receipt(study, list(pmid_a12), {p: {"status": "resolved", **_METADATA_THU} for p in pmid_a12})
    readiness = _complete_readiness(study, 2)
    readiness["ai_disclosure"].update({"ai_used": True, "tools": ["Claude (Anthropic)"],
                                       "purposes": ["hỗ trợ soạn khung bản thảo"]})  # khớp gate_params.G8 (G8-08)
    if thiet_ke == "rct":
        readiness["data_availability"].update({
            "clinical_trial": True, "what_data": "Dữ liệu cá nhân đã khử định danh của kết cục chính.",
            "related_documents": ["Study Protocol", "Statistical Analysis Plan"],
            "available_from": "6 tháng sau công bố", "availability_duration": "5 năm",
            "access_criteria": "Nhà nghiên cứu có đề cương được hội đồng độc lập duyệt.",
            "access_mechanism": "Kho dữ liệu của đơn vị, ký thoả thuận truy cập dữ liệu.",
            "registry_statement_consistent": True})
    _write_json(out / G9Q.READINESS_JSON, readiness)
    _cham9(study, out, goc, write=True)  # = chạy g9_quality_gate.py: ghi manifest trước ký
    return study, out, goc


@pytest.mark.parametrize("thiet_ke", ["cohort", "rct"])
def test_chung_h_dau_cuoi_g9_toi_ready_khoa_va_rang_buoc(tmp_path, monkeypatch, thiet_ke):
    study, out, goc = _de_tai_g9_that(tmp_path, monkeypatch, thiet_ke)
    bao = _cham9(study, out, goc)
    assert bao["status"] == G9Q.STATUS_READY, [(r["id"], r["evidence"][:160]) for r in bao["automatic_criteria"]
                                                if r["status"] != "PASS"]
    assert "G2=True" in _ck(bao, "G9-AUTO-03")["evidence"] and "PASS_G8_REVIEW_RECORDED" in _ck(
        bao, "G9-AUTO-03")["evidence"]
    a10 = (out / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").read_text(encoding="utf-8")
    assert "PHẦN 7" in a10 and "Comment R1-1" not in a10, "G9-03: mẫu phản hồi phản biện ở tệp riêng"
    assert (out / f"G9_RESPONSE_TEMPLATE_{study}.md").is_file()

    # PI ký đúng G9_checkpoint.json ⇒ khoá.
    append_signed_approval(study, out / G9Q.CHECKPOINT_JSON, "G9", "PI_PROJECT_OWNER", repo_root=goc)
    assert _cham9(study, out, goc, write=True)["status"] == G9Q.STATUS_LOCKED

    # G9-04: sửa bản thảo SAU khi G8 (và G9) đã ký ⇒ G8 sống hết PASS ⇒ G9 không còn khoá.
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    _ghi(md, md.read_text(encoding="utf-8") + "\nCâu thêm sau khi bình duyệt.\n")
    sau = _cham9(study, out, goc)
    assert _ck(sau, "G9-AUTO-03")["status"] == "REVIEW" and "G8=False" in _ck(sau, "G9-AUTO-03")["evidence"]
    assert sau["status"] != G9Q.STATUS_LOCKED


def test_g9_04_ban_thao_sua_sau_g8_truoc_g9_thi_khong_ready(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g9_that(tmp_path, monkeypatch)
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    _ghi(md, md.read_text(encoding="utf-8").replace("Kết cục chính:", "Kết cục chính (sửa sau phản biện):", 1))
    bao = _cham9(study, out, goc, write=True)
    assert _ck(bao, "G9-AUTO-03")["status"] == "REVIEW" and bao["status"] != G9Q.STATUS_READY


def test_g9_04_g2_chua_duyet_thi_khong_ready(tmp_path, monkeypatch):
    """«G2 đã duyệt» = g7_quality_gate.g2_da_duyet (sổ cái + hợp đồng chất lượng) — dùng chung với G5/G6/G7/G8/G10."""
    study = "PYTEST-G9-G2"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    _patch_upstream(monkeypatch, {"G2": False})
    bao = G9Q.evaluate_study(study, out, repo_root=tmp_path, write=True)
    row = _ck(bao, "G9-AUTO-03")
    assert row["status"] == "REVIEW" and "G2=False" in row["evidence"] and "sổ cái G2" in row["evidence"], row
    assert bao["status"] != G9Q.STATUS_READY


def test_dieu_phoi_g8_g9_khai_bao_ai_va_chia_se_du_lieu_phai_khop(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g9_that(tmp_path, monkeypatch)
    readiness = json.loads((out / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["ai_disclosure"].update({"ai_used": False, "tools": [], "purposes": []})
    _write_json(out / G9Q.READINESS_JSON, readiness)
    bao = _cham9(study, out, goc, write=True)
    row = next(r for r in bao["automatic_criteria"] if r["id"] == "G9-HUMAN-04")
    assert row["status"] == "REVIEW" and "LỆCH khai báo AI" in row["evidence"], row

    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["gate_params"]["G8"]["ipd_sharing"] = False
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    bao = _cham9(study, out, goc, write=True)
    row = next(r for r in bao["automatic_criteria"] if r["id"] == "G9-HUMAN-05")
    assert row["status"] == "REVIEW" and "LỆCH chia sẻ dữ liệu" in row["evidence"], row


# ── G9-01 / bổ sung: ô trống ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("gia_tri", ["___", "-", "[TO BE COMPLETED]", "[BÁC SĨ ĐIỀN]", "[đơn vị]", "TBD", "none", " "])
def test_g9_01_real_text_dung_hop_dong_chung(gia_tri):
    assert G9Q._real_text(gia_tri) is False, gia_tri


@pytest.mark.parametrize("gia_tri", ["Không có nhà tài trợ.", "Quỹ phát triển khoa học, mã 108.02-2025.01"])
def test_g9_01_real_text_nhan_noi_dung_that(gia_tri):
    assert G9Q._real_text(gia_tri) is True


@pytest.mark.parametrize("van_ban,ket", [
    ("[CẦN — điền]", True), ("[cần bổ sung]", True), ("[CAN điền]", True), ("[TBD]", True), ("[todo: viết]", True),
    ("<điền ngày>", True),
    ("[Todorov 2020]", False), ("[Canadian Task Force on Preventive Health Care]", False),
    ("[can thiệp giáo dục]", False), ("[Pendleton 2019]", False),
])
def test_g9_bo_sung_placeholder_re_khong_chan_oan_trich_dan(van_ban, ket):
    assert bool(G9Q._PLACEHOLDER_RE.search(van_ban)) is ket, van_ban


@pytest.mark.parametrize("khoa,them", [
    ("cover_letter", "\nSincerely,\n_______________  Ngày: ___/___/2026\n"),
    ("integrity_package", "\nĐơn vị chủ trì: [đơn vị]\n"),
    ("reporting_checklist", "\nMục 7 — Kết cục: trang [CẦN — số trang]\n"),
    ("manuscript", "\n[TRÍCH DẪN CHƯA XÁC MINH — kiểm A12]\n"),
])
def test_g9_01_documents_clean_bat_o_mau_khong_nhan(tmp_path, khoa, them):
    study = "PYTEST-G9-O-TRONG"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    files = G9Q._package_files(study, out, json.loads((out / G9Q.READINESS_JSON).read_text(encoding="utf-8")))
    sach, _bc, _vet = G9Q._documents_clean(files)
    assert sach, _bc
    p = files[khoa]
    _ghi(p, p.read_text(encoding="utf-8") + them)
    sach, bang_chung, _vet = G9Q._documents_clean(files)
    assert not sach and khoa in bang_chung, bang_chung


def test_g9_01_ban_thao_co_vet_noi_bo_theo_bo_quet_g8_thi_chan(tmp_path):
    """Bản thảo quét bằng CHÍNH scan_internal_traces của G8 (tên agent kebab-case, tên tệp pipeline…) — bộ dò riêng của
    G9 chỉ biết «chain-of-thought/system prompt»."""
    study = "PYTEST-G9-VET"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    files = G9Q._package_files(study, out, json.loads((out / G9Q.READINESS_JSON).read_text(encoding="utf-8")))
    md = files["manuscript"]
    _ghi(md, md.read_text(encoding="utf-8") + "\nKết quả do agent tra-cuu-chung-cu tổng hợp.\n")
    sach, bang_chung, vet = G9Q._documents_clean(files)
    assert not sach and vet is True and "manuscript" in bang_chung, bang_chung


def test_g9_01_khuon_sinh_khong_con_o_mau_khong_nhan(tmp_path, monkeypatch):
    goc = tmp_path / "goc"
    study = "PYTEST-G9-KHUON"
    (goc / "exports" / study).mkdir(parents=True)
    ma, _in = _chay_g9(goc, study, monkeypatch, "--n-authors", "2")
    assert ma == 0
    out = goc / "exports" / study
    for ten in (f"G9_A10_AUTHOR_INTEGRITY_{study}.md", f"G9_COVER_LETTER_{study}.md"):
        text = (out / ten).read_text(encoding="utf-8")
        con_lai = _O_CAN_RE.sub("", text)
        for cu in ("[TOOL, PROVIDER, VERSION]", "[PURPOSE AND SECTION]", "[Tên tác giả]", "[Tên + Địa chỉ",
                   "[Điền sau khi", "Option [A/B/C]", "HỌ TÊN ĐẦY ĐỦ + ĐƠN VỊ + EMAIL"):
            assert cu not in text, (ten, cu)
        assert not PC.co_o_trong(con_lai, ho=(PC.MAU_CHUNG,)), (ten, PC.dong_con_trong(con_lai, ho=(PC.MAU_CHUNG,)))


# ── G9-02: checklist chuẩn báo cáo không phải A9 ─────────────────────────────────────────────────────────────────────

def test_g9_02_khuon_readiness_khong_tro_checklist_vao_a9():
    assert G9Q.build_readiness_template("S", 1)["final_package"]["reporting_checklist_path"] is None


def test_g9_02_tro_checklist_vao_a9_thi_review_co_huong_dan(tmp_path):
    study = "PYTEST-G9-A9"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    readiness = json.loads((out / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["final_package"]["reporting_checklist_path"] = f"G8_A9_PRESUBMISSION_{study}.md"
    sach, bang_chung, _vet = G9Q._documents_clean(G9Q._package_files(study, out, readiness))
    assert not sach and "trỏ vào A9" in bang_chung, bang_chung


# ── G9-03: guardrail khi chấm lại; Phần 7 tệp riêng ──────────────────────────────────────────────────────────────────

_A10_DU_PHAN = "\n".join(f"## PHẦN {i}\nĐã điền.\n" for i in range(1, 9)) + "\nCần bác sĩ kiểm chứng.\n"


def test_g9_03_doi_that_va_go_nhan_nhap_chi_canh_bao_khi_cham_lai():
    goi = _A10_DU_PHAN + "\nDữ liệu: Dryad doi:10.5061/dryad.abc123 (truy cập có kiểm soát).\n"
    sinh = G9A.guardrail_check_g9(goi)
    assert any(e.startswith("R2") for e in sinh["errors"]) and any(e.startswith("R4") for e in sinh["errors"])
    lai = G9A.guardrail_check_g9(goi, cham_lai=True)
    assert lai["passed"] is True, lai["errors"]
    assert any(w.startswith("R2 ⚠") for w in lai["warnings"]) and any(w.startswith("R4 ⚠") for w in lai["warnings"])


def test_g9_03_r2_xet_moi_doi_khong_chi_doi_dau():
    goi = ("DRAFT DRAFT DRAFT CHỜ CHỜ\n" + _A10_DU_PHAN + "\n[CẦN — DOI kho] 10.5061/dryad.dau123\n"
           + "x" * 80 + "\nDOI bịa: 10.1234/bia.sau456\n")
    loi = G9A.guardrail_check_g9(goi)["errors"]
    assert any("10.1234/bia.sau456" in e for e in loi), loi


# ── G10-05 dùng chung ở G9: biên nhận rút bài còn hạn 30 ngày lúc ký ─────────────────────────────────────────────────

@pytest.mark.parametrize("tuoi_ngay,mong", [(1, None), (29, None), (31, "hết"), (400, "hết")])
def test_g10_05_han_bien_nhan_rut_bai(tmp_path, tuoi_ngay, mong):
    import run_g10_assemble as G10  # noqa: PLC0415
    bay_gio = datetime(2026, 10, 5, tzinfo=timezone.utc)
    _write_json(tmp_path / "A12_RETRACTION_RECEIPT.json",
                {"all_clean": True, "checked_at_utc": (bay_gio - timedelta(days=tuoi_ngay)).isoformat()})
    canh_bao, tuoi = G10.han_bien_nhan_rut_bai(tmp_path, bay_gio=bay_gio)
    assert round(tuoi) == tuoi_ngay and ((canh_bao is None) if mong is None else (mong in canh_bao)), canh_bao


@pytest.mark.parametrize("bien_nhan", [{"all_clean": True}, {"all_clean": True, "checked_at_utc": "hôm qua"},
                                       {"all_clean": True, "checked_at_utc": "2026-10-04T10:00:00"}])
def test_g10_05_khong_doc_duoc_moc_kiem_thi_coi_nhu_het_han(tmp_path, bien_nhan):
    import run_g10_assemble as G10  # noqa: PLC0415
    _write_json(tmp_path / "A12_RETRACTION_RECEIPT.json", bien_nhan)
    canh_bao, _tuoi = G10.han_bien_nhan_rut_bai(tmp_path)
    assert canh_bao and "coi như hết hạn" in canh_bao


def test_g9_bien_nhan_rut_bai_cu_chan_truoc_ky_chi_canh_bao_sau_khoa(tmp_path, monkeypatch):
    study = "PYTEST-G9-A12-CU"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    cu = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    _write_json(out / "A12_RETRACTION_RECEIPT.json", {"all_clean": True, "checked_at_utc": cu})
    trang_thai = _patch_upstream(monkeypatch)
    row = _ck(G9Q.evaluate_study(study, out, repo_root=tmp_path, write=True), "G9-AUTO-04")
    assert row["status"] == "REVIEW" and "45 ngày" in row["evidence"], row
    trang_thai["G9"] = True  # PI đã khoá G9 trước đó — sau khoá chỉ cảnh báo, không tự huỷ khoá
    row = _ck(G9Q.evaluate_study(study, out, repo_root=tmp_path, write=False), "G9-AUTO-04")
    assert row["status"] == "PASS" and row["evidence"].startswith("⚠") and "không huỷ khoá" in row["evidence"], row


# ── G9-05: thiết kế rct ⇒ clinical_trial phải true ───────────────────────────────────────────────────────────────────

def test_g9_05_rct_khai_khong_phai_thu_nghiem_thi_review(tmp_path, monkeypatch):
    study = "PYTEST-G9-RCT"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    _ghi(out / "G1_checkpoint.json", json.dumps({"design": {"internal_code": "rct"}}))
    _patch_upstream(monkeypatch)
    row = next(r for r in G9Q.evaluate_study(study, out, repo_root=tmp_path, write=True)["automatic_criteria"]
               if r["id"] == "G9-HUMAN-05")
    assert row["status"] == "REVIEW" and "thiết kế rct" in row["evidence"], row


# ── G9-06: không đè mất bản người đã sửa ─────────────────────────────────────────────────────────────────────────────

def test_g9_06_chay_lai_sao_luu_ban_nguoi_sua_va_khong_de_bak_rac(tmp_path, monkeypatch):
    goc = tmp_path / "goc"
    study = "PYTEST-G9-BAK"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    assert _chay_g9(goc, study, monkeypatch, "--n-authors", "2")[0] == 0
    assert not list(out.glob("*.bak-*")), "lần đầu không có gì để sao lưu"
    assert _chay_g9(goc, study, monkeypatch)[0] == 0
    assert not list(out.glob("*.bak-*")), "chạy lại khuôn chưa ai sửa (chỉ khác mốc giờ) ⇒ không đẻ .bak"
    a10 = out / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
    ban_nguoi = a10.read_text(encoding="utf-8").replace("[CẦN", "[đã soạn", 3)
    _ghi(a10, ban_nguoi)
    assert _chay_g9(goc, study, monkeypatch)[0] == 0
    bak = list(out.glob(f"G9_A10_AUTHOR_INTEGRITY_{study}.bak-*.md"))
    assert len(bak) == 1 and bak[0].read_text(encoding="utf-8") == ban_nguoi


def test_g9_06_ghi_giu_ban_cu_bo_qua_moc_thoi_gian(tmp_path):
    p = tmp_path / "A10.md"
    _ghi(p, "**Ngày tạo:** 2026-10-05 10:00\nNội dung khuôn.\n")
    G9A._ghi_giu_ban_cu(p, "**Ngày tạo:** 2026-10-06 11:30\nNội dung khuôn.\n")
    assert not list(tmp_path.glob("*.bak-*")) and "2026-10-06 11:30" in p.read_text(encoding="utf-8")
    G9A._ghi_giu_ban_cu(p, "**Ngày tạo:** 2026-10-06 11:31\nNội dung KHÁC.\n")
    bak = list(tmp_path.glob("A10.bak-*.md"))
    assert len(bak) == 1 and "Nội dung khuôn." in bak[0].read_text(encoding="utf-8")


def test_g9_06_n_authors_tuong_minh_ghi_de_pin(tmp_path, monkeypatch):
    goc = tmp_path / "goc"
    study = "PYTEST-G9-PIN"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    assert _chay_g9(goc, study, monkeypatch, "--n-authors", "2")[0] == 0
    assert _chay_g9(goc, study, monkeypatch, "--n-authors", "3")[0] == 0
    meta = json.loads((out / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["gate_params"]["G9"]["n_authors"] == 3
    assert json.loads((out / G9Q.READINESS_JSON).read_text(encoding="utf-8"))["n_authors"] == 3
    _chay_g9(goc, study, monkeypatch)
    assert json.loads((out / G9Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))["n_authors"] == 3, "pin mới thắng"
    # Gõ tường minh 1 (một đồng tác giả rút tên) cũng ghi đè pin — lần chạy sau không quay lại 3.
    _chay_g9(goc, study, monkeypatch, "--n-authors", "1")
    _chay_g9(goc, study, monkeypatch)
    assert json.loads((out / G9Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))["n_authors"] == 1


@pytest.mark.parametrize("co_xac_nhan", [False, True])
def test_g9_06_doi_so_tac_gia_chi_dung_lai_mang_authors(tmp_path, co_xac_nhan):
    """Bản cũ: chưa có xác nhận ⇒ ghi đè TOÀN BỘ hồ sơ bằng khuôn trắng; đã có xác nhận ⇒ không ghi gì (số tác giả lệch
    mãi). Nay cả hai: dựng lại mảng authors, giữ tác giả cũ và mọi khối khác."""
    study = "PYTEST-G9-SO-TG"
    hs = _complete_readiness(study, 2)
    if not co_xac_nhan:
        for tg in hs["authors"]:
            tg["attestation_evidence_ref"] = tg["coi_evidence_ref"] = None
    _write_json(tmp_path / G9Q.READINESS_JSON, hs)
    G9Q.write_readiness_template(tmp_path, study, 3, "Journal of Test Medicine")
    moi = json.loads((tmp_path / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    assert moi["n_authors"] == 3 and len(moi["authors"]) == 3
    assert moi["authors"][0]["credit_roles"] == hs["authors"][0]["credit_roles"], "tác giả cũ giữ nguyên"
    assert moi["data_availability"] == hs["data_availability"], "khối khác giữ nguyên (bản cũ ghi đè khuôn trắng)"
    assert moi["venue_due_diligence"] == hs["venue_due_diligence"]
    assert list(tmp_path.glob("G9_PUBLICATION_READINESS.bak-*.json")), "bản cũ được sao lưu"


def test_g9_06_bot_tac_gia_da_xac_nhan_that_thi_khong_tu_bo(tmp_path, capsys):
    study = "PYTEST-G9-BOT"
    hs = _complete_readiness(study, 2)
    _write_json(tmp_path / G9Q.READINESS_JSON, hs)
    G9Q.write_readiness_template(tmp_path, study, 1, "Journal of Test Medicine")
    assert json.loads((tmp_path / G9Q.READINESS_JSON).read_text(encoding="utf-8")) == hs
    assert "KHÔNG" in capsys.readouterr().out


# ── G9-07: CRediT ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_g9_07_credit_gach_ngang_dai_duoc_nhan_vai_sai_duoc_neu_ten():
    hs = _complete_readiness("S", 2)
    hs["authors"][0]["credit_roles"] = ["Writing – original draft", "Writing — review & editing"]
    ok, bang_chung = G9Q._authors_ok(hs, 2)
    assert ok, bang_chung
    hs["authors"][1]["credit_roles"] = ["Investigation", "Ghost writing"]
    ok, bang_chung = G9Q._authors_ok(hs, 2)
    assert not ok and "Ghost writing" in bang_chung, bang_chung


# ── G9-09: PII trong A10 ────────────────────────────────────────────────────────────────────────────────────────────

def test_g9_09_a10_co_email_thi_chan(tmp_path, monkeypatch):
    study = "PYTEST-G9-PII"
    out = tmp_path / "exports" / study
    _prepare_study(out, study)
    a10 = out / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
    _ghi(a10, a10.read_text(encoding="utf-8") + "\nLiên hệ: tac.gia@benhvien.example.vn\n")
    _patch_upstream(monkeypatch)
    bao = G9Q.evaluate_study(study, out, repo_root=tmp_path, write=True)
    assert _ck(bao, "G9-AUTO-06")["status"] == "BLOCK" and bao["status"] == G9Q.STATUS_BLOCKED


def test_g9_09_khuon_a10_dung_ma_tac_gia():
    dong = G9A.build_part1_icmje(2, "S")
    assert "AUTHOR-01" in dong and "AUTHOR-02" in dong and "EMAIL]" not in dong


# ── G9-10: skill_standards không tin trường không ai ghi ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("study", ["KHONG-CO-THU-MUC-XYZ", "ten/sai"])
def test_g9_10_skill_standards_khong_tin_g9_quality_status_luu_tay(study):
    tin_hieu = SS.real_world_signals({"G9": {"quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION, "study": study}},
                                     meta={"g9_quality_status": G9Q.STATUS_LOCKED})
    assert tin_hieu["integrity_signed"] is False
