# -*- coding: utf-8 -*-
"""Soát từng cổng G0–G10 (04/10/2026) — cổng G7 (bản thảo IMRAD A8): khoá hành vi các bản vá G7-01…G7-13 + bổ sung.

G7-01 Tiền đề G0–G6 chấm SỐNG (cong_song) — «checkpoint tồn tại» không còn đủ; riêng G2 dùng CÙNG hợp đồng với
      G5/G6/G10 (g2_da_duyet = chữ ký sổ cái + g2_quality_contract_satisfied) — điều phối thống nhất.
G7-02 G7-AUTO-06 bắt khẳng định trần: bị động «bởi», chủ động, «khoá», không «đã», đồng thuận, câu do bộ sinh cũ in,
      tiếng Anh, văn bản NFD; tín hiệu lấy từ nguồn thẩm quyền (G2/G4/G5 đạt), không từ cờ meta.
G7-03 Bộ sinh in «IRB đã duyệt» / «SAP đã khoá» chỉ theo nguồn thẩm quyền; ngày ký SAP đọc từ sổ cái khi checkpoint G4
      chưa ghi; bỏ chuỗi nội bộ «(G4=LOCKED)».
G7-04 IRB duyệt MIỄN đồng thuận ⇒ không in «ký phiếu đồng thuận»; chưa có phiên bản ICF ⇒ ô [CẦN]; Helsinki 2024 dùng
      chung với G10.
G7-05 Kết quả G6 thật: tóm tắt G6 (Python CLI ở gốc đề tài HOẶC khối cuối 03_analysis.R ở 06_phan_tich_R/output) từ
      ĐÚNG dataset khoá (sha256) + N có trong Tóm tắt/Kết quả; gợi ý phương pháp RR/ARR% khớp mô hình G6 sinh.
G7-06 Ô trống: bộ quét DÙNG CHUNG với G8 (gồm cờ «[TRÍCH DẪN CHƯA XÁC MINH]» của doctrine viet-ban-thao) + khai báo
      ICMJE phải là nội dung thật (placeholder_contract).
G7-07 A12 qua hàm chuẩn của G10 (dòng kết luận sạch + receipt có chữ ký).
G7-08 Guardrail: NCT trùng số G2 đã duyệt không phải bịa; R5 bắt «OR 1,8; 95% CI», hạ cảnh báo khi kết quả đã thật;
      R4 (nhãn DRAFT) không còn bắt buộc khi kết quả đã thật — banner DRAFT chính là ô mẫu bộ quét chung đòi gỡ.
G7-09 Xác nhận đọc lại gắn dấu bản thảo.  G7-10 «STROBE mục 9» chỉ cho thiết kế quan sát.
G7-11 Đếm checklist từ chính phụ lục.  G7-13 Không chấm nhầm bản .bak.
Bổ sung (phản biện): ô «[CẦN …» không đóng ngoặc không còn che khẳng định phía sau (đếm ngoặc lồng, không vượt dòng
trống) và bị báo là lỗi cấu trúc.
Mọi luồng có ký chạy trong pytest với khoá giả tạm (EBM_GATE_KEY_PATH chỉ có hiệu lực dưới pytest). Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_retraction as CCR  # noqa: E402
import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import g7_quality_gate as G7Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g6_auto as G6A  # noqa: E402
import run_g7_auto as G7A  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import skill_standards as S  # noqa: E402

from tests.test_g6_hoan_thien_20261004 import _de_tai_g6_that  # noqa: E402

THIET_KE = ["rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "sr_ma", "qualitative"]
RSCRIPT = shutil.which("Rscript")
_CONG = ("G0", "G1", "G2", "G3", "G4", "G5", "G6")
_KQ_DAT = {"status": "PASS", "evidence": "giả lập: tóm tắt G6 từ dataset khoá; N khớp bản thảo"}
N_PHAN_TICH = 6  # số dòng dữ liệu tổng hợp mà _de_tai_g6_that khoá


def _td(**muc) -> dict:
    """Tiền đề chấm sống G0–G6: mặc định PASS; `_td(G2="REVIEW")` đè từng cổng."""
    return {g: {"status": muc.get(g, "PASS"), "evidence": f"{g}={muc.get(g, 'PASS')}"} for g in _CONG}


def _ghi(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _ck(bao: dict, ma: str) -> dict:
    return next(r for r in bao["automatic_criteria"] + bao["human_criteria"] if r["id"] == ma)


def _cham(study: str, out: Path, goc: Path) -> dict:
    CS.xoa_dem()
    return G7Q.evaluate_study(study, out, write=False, repo_root=goc)


def _chua_dat(bao: dict) -> list:
    return [(r["id"], r["status"], r["evidence"][:160]) for r in bao["automatic_criteria"] + bao["human_criteria"]
            if r["status"] != "PASS"]


# ── Chuỗi THẬT G0→G6 rồi G7 ────────────────────────────────────────────────────────────────────────────────────────

def _xac_nhan_g6(out: Path, study: str) -> None:
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta.setdefault("gate_params", {})["G6"] = {
        "scripts_match_sap_confirmed": True, "reviewed_by_role": "STATISTICIAN",
        "reviewed_at": datetime.now().date().isoformat(), "dau_van_tay_chot": G6Q.dau_van_tay_script(out, study)}
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    CS.xoa_dem()


def _chay_g7(goc: Path, study: str, monkeypatch) -> int:
    """run_g7_auto.main() THẬT; trả mã thoát (0 chốt · 2 chờ input thật · 3 guardrail/kiểm tự động chặn)."""
    monkeypatch.setattr(G7A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g7_auto.py", "--study", study])
    CS.xoa_dem()
    ma = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            G7A.main()
    except SystemExit as exc:
        ma = int(exc.code or 0)
    CS.xoa_dem()
    return ma


def _de_tai_g7_that(tmp_path: Path, monkeypatch, thiet_ke: str) -> tuple[str, Path, Path, int]:
    """Chuỗi THẬT G0→G5 khoá (ký bằng khoá giả tạm) → run_g6_auto → thống kê viên xác nhận G6 gắn dấu → run_g7_auto."""
    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, thiet_ke)
    _xac_nhan_g6(out, study)
    return study, out, goc, _chay_g7(goc, study, monkeypatch)


def _dien_ban_thao(text: str, n: int) -> str:
    """Tác giả hoàn thiện bản thảo như người thật: gỡ dòng chỉ dẫn của khuôn (banner DRAFT, gợi ý cấu trúc, trỏ tệp
    bảng nội bộ), bỏ chú thích khuôn ở tiêu đề mục, soạn mọi ô [CẦN …], điền số N phân tích vào mục Kết quả."""
    chu_thich = G8Q._G7_TEMPLATE_PATTERNS[1][1]
    giu = []
    for dong in text.splitlines():
        khuon = any(k.casefold() in dong.casefold() for k in G8Q._G7_TEMPLATE_LITERALS) or any(
            m.search(dong) for _nhan, m in G8Q._G7_TEMPLATE_PATTERNS)
        if dong.startswith("#"):
            dong = chu_thich.sub("", dong).rstrip()
            if any(k.casefold() in dong.casefold() for k in G8Q._G7_TEMPLATE_LITERALS) or "KẾT QUẢ THẬT" in dong:
                dong = "# Bản thảo"
            giu.append(dong)
        elif not khuon:
            giu.append(dong)
    text = "\n".join(giu) + "\n"
    khoang, _ho = G7Q._khoi_can(text)
    phan, truoc = [], 0
    for a, b in khoang:
        phan += [text[truoc:a], "nội dung tác giả đã soạn"]
        truoc = b
    phan.append(text[truoc:])
    text = re.sub(r"_{3,}", "đã điền", "".join(phan))
    return text.replace("## III. KẾT QUẢ", f"## III. KẾT QUẢ\n\nTổng cộng {n} người tham gia được phân tích.\n", 1)


_G7_DA_CHOT = {
    "title": "Tiêu đề thật của bản thảo", "authors": "Tác giả A (Bệnh viện X; ORCID 0000-0000-0000-0001)",
    "author_contributions": "A: ý tưởng, phân tích, viết bản thảo; đáp ứng 4 tiêu chí ICMJE",
    "coi_declared": "Các tác giả không có xung đột lợi ích", "funding_declared": "Không nhận tài trợ",
    "data_sharing_statement": "Dữ liệu đã khử định danh chia sẻ theo yêu cầu hợp lý",
    "ai_use_declared": "Có dùng công cụ AI hỗ trợ soạn khung; tác giả chịu trách nhiệm toàn bộ nội dung",
    "target_journal": "Tạp chí Y học Việt Nam", "manuscript_reviewed_confirmed": True, "reviewed_by_role": "PI",
}


def _ghi_tom_tat_g6(out: Path, study: str, thiet_ke: str, n: int, **de) -> Path:
    """Tóm tắt G6 đúng KHUÔN mà công cụ thật ghi: Python CLI (run_stats_analysis.py — data_lock.sha256) ở gốc đề tài;
    định tính/SR-MA (CLI từ chối hai thiết kế này) theo khối cuối 03_analysis.R ở 06_phan_tich_R/output."""
    sha = json.loads((out / "DATA_LOCK_manifest.json").read_text(encoding="utf-8")).get("sha256")
    bay_gio = datetime.now().isoformat()
    if thiet_ke in ("qualitative", "sr_ma"):
        p = out / "06_phan_tich_R" / "output" / "G6_analysis_summary.json"
        noi_dung = {"study": study, "nguon": "03_analysis.R", "doi_tuong": "codes" if thiet_ke == "qualitative"
                    else "extracted", "n_total": n, "locked_data_sha256": sha, "generated": bay_gio}
    else:
        p = out / "G6_analysis_summary.json"
        noi_dung = {"study": study, "gate": "G6", "generated": bay_gio, "data_lock": {"sha256": sha}, "n_total": n,
                    "disclaimer": "Cần bác sĩ kiểm chứng."}
    noi_dung.update(de)
    return _ghi(p, json.dumps(noi_dung, ensure_ascii=False))


def _ghi_a12_that(out: Path, study: str, goc: Path, monkeypatch) -> None:
    _ghi(out / f"A12_CITATION_VERIFICATION_{study}.md",
         "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n")
    monkeypatch.setattr(CCR, "REPO_ROOT", goc)
    CCR.write_retraction_receipt(study, ["12345678"], {"12345678": {"status": "ok"}})


def _chot_g7(out: Path, text: str) -> None:
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["results_final"] = True
    meta.setdefault("gate_params", {})["G7"] = dict(
        _G7_DA_CHOT, reviewed_at=datetime.now().replace(microsecond=0).isoformat(),
        dau_van_tay_chot=CS.dau_van_tay(text.replace("\r\n", "\n")))
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    CS.xoa_dem()


def _hoan_thien(study: str, out: Path, goc: Path, monkeypatch, thiet_ke: str) -> str:
    """Bác sĩ hoàn thiện G7: kết quả G6 thật, bản thảo soạn xong, A12 thật (receipt có chữ ký), khai báo ICMJE,
    đọc lại toàn văn và xác nhận gắn dấu ĐÚNG bản này."""
    _ghi_tom_tat_g6(out, study, thiet_ke, N_PHAN_TICH)
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    text = _dien_ban_thao(md.read_text(encoding="utf-8"), N_PHAN_TICH)
    _ghi(md, text)
    _ghi_a12_that(out, study, goc, monkeypatch)
    _chot_g7(out, text)
    return text


# ── CHUNG-H: chuỗi đầu–cuối G0→G7 cho 8 thiết kế ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("thiet_ke", THIET_KE)
def test_chung_h_dau_cuoi_g7_8_thiet_ke_toi_pass_va_xac_nhan_gan_dau(tmp_path, monkeypatch, thiet_ke):
    study, out, goc, ma = _de_tai_g7_that(tmp_path, monkeypatch, thiet_ke)
    assert ma == GC.EXIT_BLOCKED, "khung vừa sinh: DỪNG chờ input thật (không 0, không 3)"
    bao = _cham(study, out, goc)
    assert bao["status"] == G7Q.STATUS_DRAFT_READY, _chua_dat(bao)
    for ma_tc in ("G7-AUTO-00", "G7-AUTO-01", "G7-AUTO-01b", "G7-AUTO-02", "G7-AUTO-04", "G7-AUTO-06"):
        assert _ck(bao, ma_tc)["status"] == "PASS", (ma_tc, _ck(bao, ma_tc)["evidence"])
    assert _ck(bao, "G7-AUTO-03")["status"] == "REVIEW" and "thiếu G6_analysis_summary" in _ck(bao, "G7-AUTO-03")[
        "evidence"], "chưa chạy phân tích ⇒ chưa có kết quả thật"
    ban_khung = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    assert "(G4=LOCKED)" not in ban_khung and "Helsinki 2013" not in ban_khung

    text = _hoan_thien(study, out, goc, monkeypatch, thiet_ke)
    assert text.count("DRAFT") < 2, "bản hoàn thiện đã gỡ banner DRAFT — R4 không còn bắt buộc khi kết quả đã thật"
    bao = _cham(study, out, goc)
    assert bao["status"] == G7Q.STATUS_CONFIRMED, _chua_dat(bao)
    assert "khớp bản thảo" in _ck(bao, "G7-AUTO-03")["evidence"]
    assert G8Q.manuscript_residues(text) == [] and G8Q.scan_internal_traces(text) == [], \
        "điều phối G7↔G8: bản thảo G7 đã PASS thì G8-AUTO-04 không còn gì để chặn"

    # G7-09: sửa bản thảo SAU khi xác nhận ⇒ xác nhận hết hiệu lực.
    _ghi(out / f"G7_A8_MANUSCRIPT_{study}.md", text + "\nCâu thêm sau khi tác giả đã xác nhận.\n")
    sau = _cham(study, out, goc)
    assert sau["status"] != G7Q.STATUS_CONFIRMED
    assert _ck(sau, "G7-HUMAN-04")["status"] == "REVIEW" and "dau_van_tay_chot" in _ck(sau, "G7-HUMAN-04")["evidence"]


# ── Đột biến trên MỘT bản thảo đã hoàn thiện (cohort) ─────────────────────────────────────────────────────────────────

@pytest.fixture
def ban_hoan_thien(tmp_path, monkeypatch):
    study, out, goc, _ma = _de_tai_g7_that(tmp_path, monkeypatch, "cohort")
    text = _hoan_thien(study, out, goc, monkeypatch, "cohort")
    assert _cham(study, out, goc)["status"] == G7Q.STATUS_CONFIRMED
    return study, out, goc, text


def test_g7_07_a12_qua_ham_chuan_g10(ban_hoan_thien):
    study, out, goc, _text = ban_hoan_thien
    a12 = out / f"A12_CITATION_VERIFICATION_{study}.md"
    goc_a12 = a12.read_text(encoding="utf-8")
    _ghi(a12, "KẾT QUẢ CỔNG A12: CÒN 🔴 CHƯA XỬ LÝ — CHƯA ĐẠT\n")
    bao = _cham(study, out, goc)
    assert _ck(bao, "G7-AUTO-07")["status"] == "REVIEW" and bao["status"] != G7Q.STATUS_CONFIRMED, \
        "bản cũ nhận A12 mang dòng kết luận THẤT BẠI chính thức (chỉ soi «KHÔNG XÁC MINH ĐƯỢC»)"
    _ghi(a12, goc_a12)
    receipt = out / "A12_RETRACTION_RECEIPT.json"
    noi_dung = receipt.read_text(encoding="utf-8")
    receipt.unlink()
    bao = _cham(study, out, goc)
    assert _ck(bao, "G7-AUTO-07")["status"] == "REVIEW" and "receipt" in _ck(bao, "G7-AUTO-07")["evidence"]
    _ghi(receipt, noi_dung)
    assert _cham(study, out, goc)["status"] == G7Q.STATUS_CONFIRMED


def test_g7_05_ket_qua_g6_tren_chuoi_that(ban_hoan_thien):
    study, out, goc, _text = ban_hoan_thien
    tom_tat = out / "G6_analysis_summary.json"
    goc_tt = tom_tat.read_text(encoding="utf-8")
    _ghi_tom_tat_g6(out, study, "cohort", N_PHAN_TICH, data_lock={"sha256": "0" * 64})
    bao = _cham(study, out, goc)
    assert _ck(bao, "G7-AUTO-03")["status"] == "BLOCK" and bao["status"] == G7Q.STATUS_BLOCKED, \
        "kết quả phân tích từ dataset KHÁC bản khoá hiện hành"
    _ghi_tom_tat_g6(out, study, "cohort", 999)
    bao = _cham(study, out, goc)
    assert _ck(bao, "G7-AUTO-03")["status"] == "REVIEW" and "999" in _ck(bao, "G7-AUTO-03")["evidence"]
    assert _ck(bao, "G7-AUTO-00")["status"] == "BLOCK", \
        "N chưa khớp tóm tắt G6 ⇒ kết quả CHƯA là thật ⇒ bản thảo đã gỡ banner phải bị R4 (nhãn DRAFT) chặn"
    _ghi(tom_tat, goc_tt)
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["results_final"] = "true"
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False))
    assert _ck(_cham(study, out, goc), "G7-AUTO-03")["status"] == "REVIEW", "cờ phải là True thật, không phải chuỗi"


def test_g7_06_o_mau_va_co_trich_dan_chua_xac_minh_tren_ban_hoan_thien(ban_hoan_thien):
    study, out, goc, text = ban_hoan_thien
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    for chen in ("Kết quả phụ [TRÍCH DẪN CHƯA XÁC MINH].", "Sàng lọc: N = ___ người.", "[1] [Tác giả] et al. [Năm].",
                 "Đăng ký [CẦN SỐ ĐĂNG KÝ CLINICALTRIALS.GOV/PROSPERO]."):
        moi = text.replace("## IV. BÀN LUẬN", f"{chen}\n\n## IV. BÀN LUẬN", 1)
        _ghi(md, moi)
        _chot_g7(out, moi)  # xác nhận lại ĐÚNG bản này — chỉ còn ô mẫu là lý do không đạt
        bao = _cham(study, out, goc)
        assert _ck(bao, "G7-AUTO-05")["status"] == "REVIEW" and bao["status"] != G7Q.STATUS_CONFIRMED, chen


def test_g7_08_nct_trung_g2_da_duyet_khong_phai_bia(ban_hoan_thien):
    study, out, goc, text = ban_hoan_thien
    cp_p = out / "G2_checkpoint.json"
    cp = json.loads(cp_p.read_text(encoding="utf-8"))
    cp["g2_registration"] = "NCT01234567"
    _ghi(cp_p, json.dumps(cp, ensure_ascii=False))
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    for nct, dat in (("NCT01234567", True), ("NCT07654321", False)):
        moi = text.replace("## IV. BÀN LUẬN", f"Đăng ký: {nct}\n\n## IV. BÀN LUẬN", 1)
        _ghi(md, moi)
        _chot_g7(out, moi)
        bao = _cham(study, out, goc)
        assert (_ck(bao, "G7-AUTO-00")["status"] == "PASS") is dat, (nct, _ck(bao, "G7-AUTO-00"))
        assert (bao["status"] == G7Q.STATUS_CONFIRMED) is dat


def test_g7_11_dem_checklist_tu_chinh_phu_luc(ban_hoan_thien):
    _study, out, _goc, _text = ban_hoan_thien
    cp = json.loads((out / "G7_checkpoint.json").read_text(encoding="utf-8"))
    _ten, tong, muc = G7A._checklist_cho_thiet_ke("cohort")
    _khoi, tu_dien, so_dong = G7A._render_checklist_block(muc, "STROBE 2007", tong)
    ck = cp["checklist"]
    assert (ck["items_auto"], ck["items_total"], ck["items_needed"]) == (tu_dien, so_dong, so_dong - tu_dien), \
        "số trên checkpoint phải là số của CHÍNH phụ lục (bản cũ: heuristic từ khoá + số mục chính thức)"


def test_g7_01_g7_03_sap_sua_sau_khi_ky_thi_g7_chan_va_bo_sinh_khong_khang_dinh(ban_hoan_thien, monkeypatch):
    study, out, goc, text = ban_hoan_thien
    assert re.search(r"\(SAP\) đã khoá, ký ngày \d{4}-\d{2}-\d{2}", text), \
        "G4 khoá thật ⇒ ngày ký lấy từ sổ cái (checkpoint G4 chưa ghi g4_lock_date vì chưa chấm lại sau khi ký)"
    sap = out / f"G4_A5_SAP_FINAL_{study}.md"
    _ghi(sap, sap.read_text(encoding="utf-8") + "\nSửa SAP sau khi đã ký.\n")
    bao = _cham(study, out, goc)
    assert bao["status"] == G7Q.STATUS_BLOCKED
    assert _ck(bao, "G7-AUTO-02")["status"] != "PASS", "tiền đề G4 chấm SỐNG — chữ ký không còn khớp SAP"
    assert _ck(bao, "G7-AUTO-06")["status"] == "BLOCK" and "khẳng định đã khóa SAP" in bao["unsupported_claims"]
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_GUARDRAIL_FAIL
    moi = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    assert "SAP [CẦN NGÀY KÝ G4" in moi and "ký ngày" not in moi and "(G4=LOCKED)" not in moi


def test_dieu_phoi_g2_mot_dinh_nghia_cho_g5_g6_g7(tmp_path, monkeypatch):
    """«G2 đã duyệt» = chữ ký sổ cái khớp gói đạo đức + hợp đồng chất lượng G2 — ĐÚNG phép kiểm của G5/G6 (chốt khoá
    phân tích) — ở cả bộ chấm lẫn bộ sinh G7. Sửa gói đạo đức sau khi ký ⇒ mọi nơi cùng thấy «chưa duyệt»."""
    study, out, goc, _ma = _de_tai_g7_that(tmp_path, monkeypatch, "cohort")
    cp_p = out / "G2_checkpoint.json"
    cp = json.loads(cp_p.read_text(encoding="utf-8"))
    cp.update({"g2_irb_number": "IRB-2026-001", "g2_icf_version": "2.0"})
    _ghi(cp_p, json.dumps(cp, ensure_ascii=False))
    assert G7Q.g2_da_duyet(study, out, goc)[0] is True
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_BLOCKED
    ban = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    assert "Hội đồng Đạo đức phê duyệt (số: IRB-2026-001; ICF phiên bản: 2.0)" in ban
    assert S.TUYEN_NGON_HELSINKI in ban and "Mọi người tham gia ký Phiếu đồng thuận" in ban

    cp["g2_icf_waiver_approved"] = True  # IRB duyệt MIỄN phiếu đồng thuận (vd hồi cứu)
    _ghi(cp_p, json.dumps(cp, ensure_ascii=False))
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_BLOCKED
    ban = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    assert "chấp thuận MIỄN lấy phiếu đồng thuận" in ban and "ký Phiếu đồng thuận" not in ban, \
        "bộ sinh phải lấy quyết định miễn đồng thuận từ G2 đã duyệt"

    goi = out / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    _ghi(goi, goi.read_text(encoding="utf-8") + "\nSửa sau khi Hội đồng đã duyệt.\n")
    CS.xoa_dem()
    ok, ly_do = G7Q.g2_da_duyet(study, out, goc)
    assert ok is False and "sổ cái" in ly_do
    assert G7Q.tien_de_song(study, out, goc)["G2"]["status"] != "PASS"
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_GUARDRAIL_FAIL
    ban = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    assert "IRB-2026-001" not in ban and "[CẦN — CHƯA CÓ PHÊ DUYỆT ĐẠO ĐỨC THẬT" in ban, \
        "bản cũ tin g2_irb_number còn sót trong checkpoint"


def test_g2_da_duyet_hop_dong_chat_luong_chua_dat(tmp_path, monkeypatch):
    study, out, goc, _ma = _de_tai_g7_that(tmp_path, monkeypatch, "cohort")
    cp_p = out / "G2_checkpoint.json"
    cp = json.loads(cp_p.read_text(encoding="utf-8"))
    cp.update({"quality_contract_version": "G2-2026.1", "quality_gate": {"status": "DRAFT_NEEDS_HUMAN_COMPLETION"}})
    _ghi(cp_p, json.dumps(cp, ensure_ascii=False))
    ok, ly_do = G7Q.g2_da_duyet(study, out, goc)
    assert ok is False and "hợp đồng chất lượng" in ly_do
    assert G7Q.g2_da_duyet("KHONG-CO", tmp_path / "exports" / "KHONG-CO", tmp_path)[0] is False


# ── G7-01: tiền đề vắng / không đạt ─────────────────────────────────────────────────────────────────────────────────

def _ban_day_du() -> str:
    from tests.test_g7_quality_gate_20260728 import _manuscript  # noqa: PLC0415
    return _manuscript(with_results=True)


def _meta_day_du(text: str) -> dict:
    return {"results_final": True, "gate_params": {"G7": dict(
        _G7_DA_CHOT, reviewed_at="2026-10-04T10:00:00", dau_van_tay_chot=CS.dau_van_tay(text))}}


def _danh_gia(text: str, **kw) -> dict:
    tham_so = {"manuscript_text": text, "checkpoints": {}, "meta": _meta_day_du(text), "citation_verification_ok": True,
               "guardrail_passed": True, "tien_de": _td(), "ket_qua_g6": _KQ_DAT}
    tham_so.update(kw)
    return G7Q.evaluate_g7_quality(**tham_so)


def test_g7_01_doi_chung_du_dieu_kien_thi_pass():
    assert _danh_gia(_ban_day_du())["status"] == G7Q.STATUS_CONFIRMED


def test_g7_01_thieu_tien_de_la_khong_do_duoc_khong_bao_gio_pass():
    bao = _danh_gia(_ban_day_du(), tien_de=None)
    assert bao["status"] != G7Q.STATUS_CONFIRMED
    for ma in ("G7-AUTO-01", "G7-AUTO-02"):
        assert _ck(bao, ma)["status"] == "REVIEW" and "không đo được" in _ck(bao, ma)["evidence"]


@pytest.mark.parametrize("cong,muc,ma_tc,ky_vong", [
    ("G1", "BLOCK", "G7-AUTO-01", "BLOCK"), ("G1", "REVIEW", "G7-AUTO-01", "REVIEW"),
    ("G0", "REVIEW", "G7-AUTO-02", "REVIEW"), ("G2", "BLOCK", "G7-AUTO-02", "BLOCK"),
    ("G3", "REVIEW", "G7-AUTO-02", "REVIEW"), ("G4", "REVIEW", "G7-AUTO-02", "REVIEW"),
    ("G5", "BLOCK", "G7-AUTO-03", "BLOCK"), ("G5", "REVIEW", "G7-AUTO-03", "REVIEW"),
    ("G6", "BLOCK", "G7-AUTO-03", "BLOCK"), ("G6", "REVIEW", "G7-AUTO-03", "REVIEW"),
])
def test_g7_01_moi_cong_truoc_khong_dat_thi_khong_pass(cong, muc, ma_tc, ky_vong):
    bao = _danh_gia(_ban_day_du(), tien_de=_td(**{cong: muc}))
    assert _ck(bao, ma_tc)["status"] == ky_vong and bao["status"] != G7Q.STATUS_CONFIRMED


def test_g7_05_ket_qua_g6_chua_doi_chieu_hoac_chan():
    assert _ck(_danh_gia(_ban_day_du(), ket_qua_g6=None), "G7-AUTO-03")["status"] == "REVIEW"
    assert _ck(_danh_gia(_ban_day_du(), ket_qua_g6={"status": "BLOCK", "evidence": "x"}), "G7-AUTO-03")[
        "status"] == "BLOCK"


# ── G7-02: khẳng định trần ───────────────────────────────────────────────────────────────────────────────────────────

_TAT = {"irb_approved": False, "registered": False, "sap_locked": False, "db_locked": False, "consent": False}
_NHAN = {"irb_approved": "khẳng định đã được Hội đồng Đạo đức/IRB phê duyệt",
         "registered": "khẳng định đã đăng ký ClinicalTrials.gov", "sap_locked": "khẳng định đã khóa SAP",
         "db_locked": "khẳng định đã khóa cơ sở dữ liệu"}


@pytest.mark.parametrize("cau,tin_hieu", [
    ("Nghiên cứu được phê duyệt bởi Hội đồng Đạo đức Bệnh viện X.", "irb_approved"),
    ("Hội đồng Đạo đức Bệnh viện X đã phê duyệt đề cương.", "irb_approved"),
    ("The study was approved by the Ethics Committee of Hospital X.", "irb_approved"),
    ("The institutional review board approved the protocol.", "irb_approved"),
    ("The trial was registered at ClinicalTrials.gov before enrolment.", "registered"),
    ("SAP đã được khoá trước khi xem dữ liệu.", "sap_locked"),
    ("SAP phiên bản 1.0 ký ngày 2026-09-01 (G4=LOCKED).", "sap_locked"),
    ("Kế hoạch phân tích được khóa ngày 01/09/2026.", "sap_locked"),
    ("The statistical analysis plan was finalised before unblinding.", "sap_locked"),
    ("Cơ sở dữ liệu được khoá ngày 01/09/2026.", "db_locked"),
    ("The database was locked on 1 September 2026.", "db_locked"),
    ("Mọi người tham gia đã ký phiếu đồng thuận.", "consent"),
    ("Written informed consent was obtained from all participants.", "consent"),
    ("Participants provided written informed consent.", "consent"),
])
def test_g7_02_khang_dinh_tran_bi_bat_va_tin_hieu_dung_moi_go(cau, tin_hieu):
    claims = G7Q.find_unsupported_claims(cau, _TAT)
    assert claims, f"lọt: {cau}"
    if tin_hieu in _NHAN:
        assert _NHAN[tin_hieu] in claims
    assert G7Q.find_unsupported_claims(cau, dict(_TAT, **{tin_hieu: True})) == [], "tín hiệu đúng phải gỡ được"


def test_g7_02_van_ban_nfd_van_bi_bat_va_chi_dan_nfd_khong_bat_nham():
    nfd = unicodedata.normalize("NFD", "Dữ liệu đã được khoá trước phân tích.")
    assert "khẳng định đã khóa cơ sở dữ liệu" in G7Q.find_unsupported_claims(nfd, _TAT)
    chi_dan = unicodedata.normalize("NFD", "[CẦN — KHÔNG được viết 'Hội đồng Đạo đức đã phê duyệt' khi chưa có G2]")
    assert G7Q.find_unsupported_claims(chi_dan, _TAT) == []


def test_g7_02_tin_hieu_tu_nguon_tham_quyen_khong_tu_co_meta():
    text = _ban_day_du() + "\nDữ liệu đã được khóa ngày 01/09/2026. SAP đã được khóa trước phân tích.\n"
    meta = dict(_meta_day_du(text), irb_approved=True, sap_lock_date="[CẦN NGÀY]", data_lock_date="2026-09-01")
    bao = _danh_gia(text, meta=meta, tien_de=_td(G4="REVIEW", G5="REVIEW"),
                    checkpoints={"G2": {"g2_irb_number": "IRB-1"}, "G4": {"g4_status": "LOCKED"}})
    assert _ck(bao, "G7-AUTO-06")["status"] == "BLOCK"
    assert {"khẳng định đã khóa SAP", "khẳng định đã khóa cơ sở dữ liệu"} <= set(bao["unsupported_claims"])


def test_g7_04_mien_dong_thuan_thi_khang_dinh_ky_phieu_la_tran():
    text = _ban_day_du() + "\nMọi người tham gia đã ký phiếu đồng thuận.\n"
    bao = _danh_gia(text, checkpoints={"G2": {"g2_icf_waiver_approved": True}})
    assert _ck(bao, "G7-AUTO-06")["status"] == "BLOCK" and any("đồng thuận" in c for c in bao["unsupported_claims"])


# ── Bổ sung: ô [CẦN … không đóng ngoặc ───────────────────────────────────────────────────────────────────────────────

def test_o_can_khong_dong_khong_con_che_khang_dinh_phia_sau():
    text = ("Dịch tễ [CẦN bổ sung số liệu dịch tễ.\n\n"
            "§7: Đề tài đã được Hội đồng Đạo đức Bệnh viện Quân y 175 phê duyệt. SAP đã được khóa ngày 1/9 [1].\n")
    claims = G7Q.find_unsupported_claims(text, _TAT)
    assert _NHAN["irb_approved"] in claims and _NHAN["sap_locked"] in claims, "bản cũ: DOTALL bóc tới «[1]» ⇒ []"
    assert G7Q.o_can_chua_dong(text) and G7Q.o_can_chua_dong(text)[0].startswith("[CẦN bổ sung")
    bao = _danh_gia(_ban_day_du() + "\n" + text, tien_de=_td(G2="REVIEW", G4="REVIEW"))
    assert _ck(bao, "G7-AUTO-05")["status"] == "REVIEW" and "KHÔNG đóng ngoặc" in _ck(bao, "G7-AUTO-05")["evidence"]


def test_o_can_khong_dong_khong_keo_qua_dong_trong_toi_ngoac_thua():
    """«]]» gõ thừa ở đoạn SAU không được «đóng hộ» một ô [CẦN mở ở đoạn trước (ô không vượt dòng trống)."""
    text = ("Dịch tễ [CẦN bổ sung số liệu dịch tễ.\n\n"
            "Đề tài đã được Hội đồng Đạo đức Bệnh viện X phê duyệt.\n\n"
            "Theo y văn [1, 2]].\n")
    assert _NHAN["irb_approved"] in G7Q.find_unsupported_claims(text, _TAT)
    assert G7Q.o_can_chua_dong(text), "ô mở ở đoạn 1 phải được báo là KHÔNG đóng"


@pytest.mark.parametrize("dong", ["> • Dùng agent `kiem-chung-trich-dan` hoặc PubMed trực tiếp",
                                  "> • Xác minh tác giả/volume/số/trang toàn văn cho mỗi PMID",
                                  "Chạy agent `kiem-chung-trich-dan` trước khi nộp.",
                                  "Xem tệp study_meta.json để biết thêm."])
def test_dieu_phoi_g7_g8_dong_chi_dan_va_vet_noi_bo_khong_qua_g7(dong):
    bao = _danh_gia(_ban_day_du().replace("## IV. BÀN LUẬN", dong + "\n\n## IV. BÀN LUẬN", 1))
    assert _ck(bao, "G7-AUTO-05")["status"] == "REVIEW" and bao["status"] != G7Q.STATUS_CONFIRMED, dong


def test_o_can_long_ngoac_duoc_boc_tron_ven():
    text = "[CẦN — tài trợ; IRB: [CẦN SỐ IRB THẬT]; KHÔNG được viết 'Hội đồng Đạo đức đã phê duyệt' trước khi có G2]"
    assert G7Q.find_unsupported_claims(text, _TAT) == [], "bản cũ dừng ở «]» của ô con ⇒ bắt nhầm lời chỉ dẫn"
    assert G7Q.o_can_chua_dong(text) == []
    assert G7Q.strip_placeholder_blocks("A " + text + " B").split() == ["A", "B"]


# ── G7-03 / G7-04 / G7-10 / gợi ý phương pháp: bộ sinh ────────────────────────────────────────────────────────────────

def _sinh(**kw) -> str:
    tham_so = dict(study="S", topic="Chủ đề", n_sr=1, n_rct=1, n_guideline=1, research_gaps=["g"], pmids=["12345678"],
                   pmid_meta={}, design_code="cohort", design_primary="Cohort", reporting_std="STROBE 2007",
                   irb_number="[CẦN SỐ IRB THẬT]", icf_version="[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT]",
                   registration="[CẦN SỐ ĐĂNG KÝ]", n_total=100, n_adjusted=110, alpha=0.05, power=0.8, effect_val=0.8,
                   effect_type="RR", formula_used="f", g4_status="PENDING", g4_lock_date=None, target_journal="J",
                   word_limit=3000, run_date="2026-10-04")
    tham_so.update(kw)
    return G7A.generate_manuscript(**tham_so)


def test_g7_03_bo_sinh_chi_khang_dinh_sap_khoa_theo_trang_thai_tham_quyen():
    cu = _sinh(g4_status="PENDING", g4_lock_date="2026-09-01")
    assert "ký ngày 2026-09-01" not in cu and "SAP [CẦN NGÀY KÝ G4" in cu, "bản cũ chỉ xét g4_lock_date"
    khoa = _sinh(g4_status="LOCKED", g4_lock_date="2026-09-01")
    assert "(SAP) đã khoá, ký ngày 2026-09-01" in khoa and "G4=LOCKED" not in khoa


def test_g7_04_mien_dong_thuan_va_icf_chua_co_va_helsinki_dung_chung():
    mien = _sinh(irb_number="IRB-2026-001", icf_version="[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT]", mien_dong_thuan=True)
    assert "chấp thuận MIỄN lấy phiếu đồng thuận" in mien and "ký Phiếu đồng thuận" not in mien
    assert "ICF phiên bản" not in mien
    chua_icf = _sinh(irb_number="IRB-2026-001")
    assert "Mọi người tham gia ký" not in chua_icf and "[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT — chưa được viết" in chua_icf
    du = _sinh(irb_number="IRB-2026-001", icf_version="2.0")
    assert "Mọi người tham gia ký Phiếu đồng thuận" in du
    for ban in (mien, chua_icf, du, G10.sec_daoduc({"G2": {}}, {})):
        assert S.TUYEN_NGON_HELSINKI in ban and "Helsinki 2013" not in ban
    assert "2024" in S.TUYEN_NGON_HELSINKI


@pytest.mark.parametrize("thiet_ke,co", [("cohort", True), ("case_control", True), ("cross_sectional", True),
                                         ("rct", False), ("diagnostic", False), ("sr_ma", False),
                                         ("prediction", False), ("qualitative", False)])
def test_g7_10_strobe_muc_9_chi_cho_thiet_ke_quan_sat(thiet_ke, co):
    assert ("STROBE mục 9" in _sinh(design_code=thiet_ke)) is co


def test_dieu_phoi_g6_g7_goi_y_phuong_phap_khop_mo_hinh_g6():
    assert "Poisson sai số robust" in _sinh(effect_type="RR")
    assert "hiệu nguy cơ" in _sinh(effect_type="ARR%")


# ── G7-05: đối chiếu kết quả G6 (đơn vị) ─────────────────────────────────────────────────────────────────────────────

_SHA = "a" * 64


def _thu_muc_khoa(tmp_path: Path, locked_at: str = "2026-10-01T09:00:00") -> Path:
    out = tmp_path / "exports" / "S"
    _ghi(out / "DATA_LOCK_manifest.json", json.dumps({"status": "LOCKED_FOR_ANALYSIS", "locked_at": locked_at,
                                                      "sha256": _SHA}))
    return out


_BAN_N = "## TÓM TẮT\n\nN = 120.\n\n## I. GIỚI THIỆU\n\n## III. KẾT QUẢ\n\nPhân tích 120 người.\n\n## IV. BÀN LUẬN\n"


def _tt(out: Path, rel: str = "G6_analysis_summary.json", **noi_dung) -> Path:
    return _ghi(out / rel, json.dumps(noi_dung, ensure_ascii=False))


def test_g7_05_thieu_tom_tat_la_review(tmp_path):
    kq = G7Q.doi_chieu_ket_qua_g6("S", _thu_muc_khoa(tmp_path), _BAN_N)
    assert kq["status"] == "REVIEW" and "06_phan_tich_R/output" in kq["evidence"]


def test_g7_05_chua_khoa_du_lieu_la_chan(tmp_path):
    out = tmp_path / "exports" / "S"
    _tt(out, n_total=120, data_lock={"sha256": _SHA})
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "BLOCK"


@pytest.mark.parametrize("rel,noi_dung", [
    ("G6_analysis_summary.json", {"n_total": 120, "data_lock": {"sha256": _SHA}, "generated": "2026-10-02T10:00:00"}),
    ("06_ket_qua/G6_analysis_summary.json", {"n_total": 120, "data_lock": {"sha256": _SHA}}),
    ("06_phan_tich_R/output/G6_analysis_summary.json", {"n_total": 120, "locked_data_sha256": _SHA.upper()}),
])
def test_g7_05_tom_tat_cli_hoac_r_tu_dung_dataset_khoa_la_pass(tmp_path, rel, noi_dung):
    out = _thu_muc_khoa(tmp_path)
    _tt(out, rel, **noi_dung)
    kq = G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)
    assert kq["status"] == "PASS", kq


def test_g7_05_sha_lech_la_chan_va_khoa_lai_cung_du_lieu_van_dat(tmp_path):
    out = _thu_muc_khoa(tmp_path, locked_at="2026-10-05T09:00:00")  # khoá lại SAU lần phân tích, cùng dữ liệu
    _tt(out, n_total=120, data_lock={"sha256": _SHA}, generated="2026-10-02T10:00:00")
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "PASS", "dấu nội dung trùng ⇒ kết quả còn hiệu lực"
    _tt(out, "06_phan_tich_R/output/G6_analysis_summary.json", n_total=120, locked_data_sha256="b" * 64)
    kq = G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)
    assert kq["status"] == "BLOCK" and "KHÁC bản khoá" in kq["evidence"], "tóm tắt cũ từ dataset khác còn nằm đó"


def test_g7_05_khong_co_dau_thi_xet_thoi_diem_sinh(tmp_path):
    out = _thu_muc_khoa(tmp_path)
    _tt(out, n_total=120, generated="2026-09-30T10:00:00")
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "BLOCK"
    _tt(out, n_total=120, generated="2026-10-02T10:00:00+00:00")  # có múi giờ — quy về giờ máy, mọi múi giờ đều sau
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "PASS"
    _tt(out, n_total=120, generated="2026-10-03T10:00:00")
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "PASS"


def test_g7_05_n_khong_co_trong_ban_thao_la_review(tmp_path):
    out = _thu_muc_khoa(tmp_path)
    _tt(out, n_total=121, data_lock={"sha256": _SHA})
    kq = G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)
    assert kq["status"] == "REVIEW" and "121" in kq["evidence"]
    _tt(out, n_total="nhiều", data_lock={"sha256": _SHA})
    assert G7Q.doi_chieu_ket_qua_g6("S", out, _BAN_N)["status"] == "REVIEW"


@pytest.mark.skipif(RSCRIPT is None, reason="máy không có Rscript")
@pytest.mark.parametrize("nap,n", [
    ('df <- data.frame(x = 1:7)', 7),
    ('extracted <- data.frame(study = c("A", "B", "C"))', 3),
    ('codes <- data.frame(transcript_id = c("T1", "T1", "T2"), ma = c("a", "b", "c"))', 2),
    ("", None),
])
def test_dieu_phoi_g6_g7_khoi_r_ghi_tom_tat_ma_g7_doc_duoc(tmp_path, nap, n):
    """Khối cuối 03_analysis.R (R THẬT) ghi tóm tắt mà G7 đọc được: đúng đối tượng phân tích của thiết kế; chưa nạp đối
    tượng nào thì KHÔNG ghi (không bịa N)."""
    khoi = G6A.hau_xu_ly_script_r("", "S", (), la_03=True)
    out = tmp_path / "exports" / "S"
    ra = out / "06_phan_tich_R" / "output"
    ra.mkdir(parents=True)
    tep = _ghi(tmp_path / "chay.R", f'STUDY <- "S"\nLOCKED_SHA <- "{_SHA}"\nOUTPUT <- "{ra.as_posix()}"\n'
                                     f"{nap}\n{khoi}")
    kq = subprocess.run([RSCRIPT, str(tep)], capture_output=True, text=True, timeout=120)
    assert kq.returncode == 0, kq.stderr[-800:]
    tom_tat = ra / "G6_analysis_summary.json"
    if n is None:
        assert not tom_tat.exists()
        return
    du_lieu = json.loads(tom_tat.read_text(encoding="utf-8"))
    assert du_lieu["n_total"] == n and du_lieu["locked_data_sha256"] == _SHA
    _ghi(out / "DATA_LOCK_manifest.json", json.dumps({"status": "LOCKED_FOR_ANALYSIS",
                                                      "locked_at": "2026-01-01T00:00:00", "sha256": _SHA}))
    ban = f"## TÓM TẮT\n\nN = {n}.\n\n## I. GIỚI THIỆU\n"
    assert G7Q.doi_chieu_ket_qua_g6("S", out, ban)["status"] == "PASS"


# ── G7-06: khai báo phải là nội dung thật ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("gia_tri", [True, 1, "TBD", "[TBD]", "[TÁC GIẢ ĐIỀN: tuyên bố COI]", "", "___"])
def test_g7_06_khai_bao_icmje_phai_la_noi_dung_that(gia_tri):
    text = _ban_day_du()
    meta = _meta_day_du(text)
    meta["gate_params"]["G7"]["coi_declared"] = gia_tri
    bao = _danh_gia(text, meta=meta)
    assert _ck(bao, "G7-HUMAN-02")["status"] == "REVIEW" and "Xung đột lợi ích" in _ck(bao, "G7-HUMAN-02")["evidence"]


@pytest.mark.parametrize("khoa,ma", [("title", "G7-HUMAN-01"), ("authors", "G7-HUMAN-01"),
                                     ("target_journal", "G7-HUMAN-03")])
def test_g7_06_tieu_de_tac_gia_tap_chi_phai_la_noi_dung_that(khoa, ma):
    text = _ban_day_du()
    for gia_tri in (True, "[TBD]", "[CẦN — xác định trước khi định dạng]"):
        meta = _meta_day_du(text)
        meta["gate_params"]["G7"][khoa] = gia_tri
        assert _ck(_danh_gia(text, meta=meta), ma)["status"] == "REVIEW", (khoa, gia_tri)


# ── G7-08: guardrail ─────────────────────────────────────────────────────────────────────────────────────────────────

_NEN = "DRAFT DRAFT. Cần bác sĩ kiểm chứng.\n"


@pytest.mark.parametrize("cau", ["OR 1,8; 95% CI 1,2–2,7", "cOR: 1,8 [95% CI 1,2–2,7]", "HR = 0.64 (95%CI 0.5–0.8)",
                                 "RR 0.80, 95 % CI 0.70–0.91"])
def test_g7_08_r5_bat_uoc_luong_cung_va_ha_canh_bao_khi_ket_qua_that(cau):
    loi, _cb = G7A.guardrail_g7(_NEN + cau)
    assert any(x.startswith("R5") for x in loi), cau
    loi, cb = G7A.guardrail_g7(_NEN + cau, ket_qua_that=True)
    assert not any(x.startswith("R5") for x in loi) and any(x.startswith("R5 ⚠") for x in cb)


def test_g7_08_r2_nct_chi_loi_khi_khac_so_g2_da_duyet():
    cau = _NEN + "Đăng ký: NCT01234567"
    assert any(x.startswith("R2") for x in G7A.guardrail_g7(cau)[0])
    assert not any(x.startswith("R2") for x in G7A.guardrail_g7(cau, dang_ky_g2="NCT01234567")[0])
    assert any(x.startswith("R2") for x in G7A.guardrail_g7(cau, dang_ky_g2="NCT07654321")[0])


def test_g7_08_r4_draft_chi_bat_buoc_khi_chua_co_ket_qua_that():
    ban = "Bản thảo hoàn thiện. Cần bác sĩ kiểm chứng.\n"
    assert any(x.startswith("R4") for x in G7A.guardrail_g7(ban)[0])
    assert not any(x.startswith("R4") for x in G7A.guardrail_g7(ban, ket_qua_that=True)[0])
    assert any(x.startswith("R7") for x in G7A.guardrail_g7("DRAFT DRAFT", ket_qua_that=True)[0]), "R7 giữ nguyên"


# ── G7-09: xác nhận gắn dấu (đơn vị) ─────────────────────────────────────────────────────────────────────────────────

def test_g7_09_xac_nhan_khong_dau_hoac_lech_dau_la_review_va_goi_y_dau():
    text = _ban_day_du()
    meta = _meta_day_du(text)
    del meta["gate_params"]["G7"]["dau_van_tay_chot"]
    bao = _danh_gia(text, meta=meta)
    assert _ck(bao, "G7-HUMAN-04")["status"] == "REVIEW" and bao["status"] != G7Q.STATUS_CONFIRMED
    dau = CS.dau_van_tay(text)
    assert bao["needs_input"]["remediation"]["study_meta_patch"]["gate_params"]["G7"]["dau_van_tay_chot"] == dau
    meta["gate_params"]["G7"]["dau_van_tay_chot"] = dau
    assert _danh_gia(text, meta=meta)["status"] == G7Q.STATUS_CONFIRMED
    assert _danh_gia(text + "\nSửa thêm.\n", meta=meta)["status"] != G7Q.STATUS_CONFIRMED


# ── G7-13: chỉ chấm ĐÚNG tệp của đề tài ──────────────────────────────────────────────────────────────────────────────

def test_g7_13_chi_co_ban_bak_thi_chan(tmp_path, monkeypatch):
    out = tmp_path / "exports" / "S"
    _ghi(out / "G7_A8_MANUSCRIPT_S.bak-20261004-101010.md", _ban_day_du())
    _ghi(out / "G7_A8_MANUSCRIPT_KHAC.md", _ban_day_du())
    monkeypatch.setattr(G7Q, "tien_de_song", lambda *a, **k: _td())
    monkeypatch.setattr(G7Q, "doi_chieu_ket_qua_g6", lambda *a, **k: dict(_KQ_DAT))
    bao = G7Q.evaluate_study("S", out, write=False, repo_root=tmp_path)
    assert bao["status"] == G7Q.STATUS_BLOCKED and _ck(bao, "G7-AUTO-04")["status"] == "BLOCK"

