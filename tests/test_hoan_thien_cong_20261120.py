"""Kiểm toàn hệ nghiên cứu 20/11/2026 — năm lỗi nhỏ đo được trên C1a và BTM.

1. A1 (G0): PI ĐÃ chốt mà PHẦN 1/1b/2 vẫn in khung soạn lần đầu — 27–28 ô «[CẦN BÁC SĨ…]» hỏi lại điều đã quyết;
   trục ③ của kiem_chi_tiet_he_nghien_cuu đếm chúng thành việc của chủ nhiệm.
2. `dung_lai_a1`: ghi checkpoint mỗi lần dựng lại (kể cả khi chỉ đổi dấu giờ) ⇒ G0 mới hơn mọi cổng sau ⇒
   pipeline_freshness báo cả chuỗi «cũ», G10-AUTO-03 chặn. Thêm chế độ `--chi-van-ban` (không ghi checkpoint; guardrail
   chạy TRƯỚC khi ghi, lỗi thì không đụng bản đang có).
3. R2 (PII) của G0: khoảng ngày «01/01/2026–31/12/2026» (cửa sổ hồi cứu đã chốt) bị báo là ngày sinh.
4. A6 (G5): sơ đồ dòng người tham gia in «[CẦN — tiêu chí loại trừ…]», «[CẦN — tên biến phơi nhiễm…]» dù G1 đã chốt,
   và vẽ hai nhánh «có/không phơi nhiễm» cho thiết kế cắt ngang có phơi nhiễm liên tục.
5. Trục ⑤ của kiem_chi_tiet: artifact dựng lại SAU khi ký («NỘI DUNG ĐÃ ĐỔI SAU KHI DUYỆT») bị xếp 🔴 «bất thường sổ
   cái — điều tra, ký lại trên máy hiện tại» thay vì 🟡 «PI rà rồi ký lại».
6. G10 A12: DOI không có PMID đã được kiem_rut_bai_trich_dan.py kiểm (còn hạn) vẫn bị bảo «tra tay»; DOI đã rút/EoC
   trong kết quả ấy không chặn (PMID đã rút thì chặn).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402
import gate_contract as GC  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as KCT  # noqa: E402
import run_g0_auto as G0  # noqa: E402
import run_g5_auto as G5  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402

from tests.g5_test_helpers import configure_test_signing_key  # noqa: E402

STUDY = "S-HTC20"
NEN = ["34445940", "36439278"]
G0_CHOT = {
    "population": "Người bệnh ngoại trú đã khám xong tại Khoa C1a", "intervention": "Thời gian chờ (HIS)",
    "comparison": "Không có nhóm so sánh ngoài", "primary_outcome": "Mức hài lòng chung (Likert 1–5)",
    "primary_outcome_measure": "Câu G1 của phiếu", "primary_outcome_timepoint": "Sau khi khám xong",
    "question_type": "descriptive", "test_type": "descriptive",
    "hypothesis_h0": "OR = 1", "hypothesis_h1": "OR ≠ 1", "expected_direction": "giảm",
    "finer_feasible": "Khả thi: 1.000 người/6 tháng", "finer_interesting": "Có giá trị cho quản lý khoa",
    "finer_novel": "Chưa có khảo sát tại khoa", "finer_ethical": "Ẩn danh, đồng thuận miệng",
    "finer_relevant": "Phục vụ cải tiến chất lượng",
    "pico_confirmed": True, "reviewed_by_role": "PI", "reviewed_at": "2026-10-14T19:17:12+07:00",
    "dau_van_tay_chot": "4678a3407d3ccd57",
}


def _de_tai(tmp_path: Path, g0: dict) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    raw = {"sr_ma": [], "rct": [], "guideline": [], "recent": [],
           "observational": [{"pmid": p, "title": f"T {p}", "year": "2025", "journal": "J", "url": "u"} for p in NEN],
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 2, "recent": 0}}
    cp = {"study": STUDY, "gate": "G0", "topic": "x", "base_query": "q",
          "pubmed_results": {"all_pmids": NEN, "total_found": 2},
          "registry_check": {"checked": True, "n_trials": 0, "n_active": 0, "trials": []}}
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": g0, "G1": {"design": "cross_sectional"}}}
    for ten, v in (("G0_pubmed_raw.json", raw), ("G0_checkpoint.json", cp), ("study_meta.json", meta)):
        (d / ten).write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def _chuan_bi(tmp_path, monkeypatch, g0: dict, guardrail_dat: bool = True) -> Path:
    d = _de_tai(tmp_path, g0)
    monkeypatch.setattr(G0, "_REPO_ROOT", tmp_path.parent)
    ket_qua = {"passed": guardrail_dat, "errors": [] if guardrail_dat else ["R2 🔴 giả lập"], "warnings": []}
    monkeypatch.setattr(G0, "guardrail_check_g0", lambda *_a, **_k: ket_qua)
    monkeypatch.setattr(G0, "PubMedClient", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    return d


# ── 1. A1: đã chốt ⇒ ẩn khung soạn lần đầu ──────────────────────────────────────────────────────────────────────

def test_a1_da_chot_an_khung_soan_lan_dau(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, G0_CHOT)
    assert G0.dung_lai_a1(STUDY, d, chi_van_ban=True) == GC.EXIT_OK
    a1 = (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")
    assert "## PHẦN 1 — PICO / PECO (đã chốt — chỉ đọc)" in a1
    assert "## PHẦN 1b — GIẢ THUYẾT (đã chốt — chỉ đọc)" in a1
    assert "## PHẦN 2 — KIỂM FINER (đã chốt — chỉ đọc)" in a1
    assert "(khung trống — bác sĩ tự viết)" not in a1
    assert "- **F — Khả thi:** Khả thi: 1.000 người/6 tháng" in a1
    phan12 = a1[a1.index("## PHẦN 1 —"):a1.index("## PHẦN 3")]
    assert "[CẦN BÁC SĨ" not in phan12, "phần đã chốt không còn ô hỏi lại PI"


def test_a1_chua_chot_giu_khung_cu_nguyen_van(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, {})
    assert G0.dung_lai_a1(STUDY, d, chi_van_ban=True) == GC.EXIT_OK
    a1 = (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")
    assert "## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)" in a1
    assert "> **Hệ KHÔNG suy ra PICO.**" in a1
    assert "(đã chốt — chỉ đọc)" not in a1


def test_a1_finer_chua_du_thi_phan2_giu_khung(tmp_path, monkeypatch):
    g0 = {k: v for k, v in G0_CHOT.items() if k != "finer_novel"}
    d = _chuan_bi(tmp_path, monkeypatch, g0)
    G0.dung_lai_a1(STUDY, d, chi_van_ban=True)
    a1 = (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")
    assert "## PHẦN 1 — PICO / PECO (đã chốt — chỉ đọc)" in a1
    assert "## PHẦN 2 — KIỂM FINER (đã chốt — chỉ đọc)" not in a1


# ── 2. dung_lai_a1: chỉ văn bản không ghi checkpoint; guardrail lỗi thì không ghi gì ─────────────────────────────

def test_chi_van_ban_khong_ghi_checkpoint(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, G0_CHOT)
    truoc = (d / "G0_checkpoint.json").read_bytes()
    assert G0.dung_lai_a1(STUDY, d, chi_van_ban=True) == GC.EXIT_OK
    assert (d / "G0_checkpoint.json").read_bytes() == truoc
    assert (d / f"G0_A1_PICO_FINER_{STUDY}.md").exists()


def test_chi_van_ban_guardrail_loi_khong_ghi_van_ban(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, G0_CHOT, guardrail_dat=False)
    cu = d / f"G0_A1_PICO_FINER_{STUDY}.md"
    cu.write_text("BẢN CŨ", encoding="utf-8", newline="\n")
    assert G0.dung_lai_a1(STUDY, d, chi_van_ban=True) == GC.EXIT_BLOCKED
    assert cu.read_text(encoding="utf-8") == "BẢN CŨ", "guardrail lỗi ⇒ bản đang có giữ nguyên"
    assert not list(d.glob("*.bak-*.md")) and not list(d.glob("*.docx"))


def test_chi_van_ban_chi_chay_guardrail_mot_lan(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, G0_CHOT)
    dem = []
    monkeypatch.setattr(G0, "guardrail_check_g0",
                        lambda *_a, **_k: dem.append(1) or {"passed": True, "errors": [], "warnings": []})
    G0.dung_lai_a1(STUDY, d, chi_van_ban=True)
    assert len(dem) == 1, "R1C có thể gọi mạng — không chạy guardrail hai lần"


def test_dung_lai_thuong_khong_doi_noi_dung_thi_khong_ghi_checkpoint(tmp_path, monkeypatch):
    d = _chuan_bi(tmp_path, monkeypatch, G0_CHOT)
    G0.dung_lai_a1(STUDY, d)  # lượt đầu: điền các khoá suy ra ⇒ có ghi
    cp_path = d / "G0_checkpoint.json"
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    assert cp.get("a1_dung_lai_luc"), "lượt đầu đổi nội dung suy ra ⇒ phải ghi checkpoint"
    cp["a1_dung_lai_luc"] = "MOC-CANH-GAC"  # hai lượt có thể cùng một giây ⇒ dùng mốc thay vì so byte
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    G0.dung_lai_a1(STUDY, d)  # lượt hai: nội dung suy ra như cũ ⇒ không ghi (chỉ dấu giờ khác)
    assert json.loads(cp_path.read_text(encoding="utf-8"))["a1_dung_lai_luc"] == "MOC-CANH-GAC"


def test_cli_chi_van_ban_phai_di_cung_dung_lai(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_g0_auto.py", "--study", STUDY, "--topic", "x", "--chi-van-ban"])
    with pytest.raises(SystemExit) as e:
        G0.main()
    assert e.value.code == 2
    assert "--chi-van-ban chỉ đi cùng --dung-lai-a1" in capsys.readouterr().err


# ── 3. R2: khoảng ngày khung nghiên cứu không phải PII; ngày lẻ vẫn bị bắt ──────────────────────────────────────

def _r2(van_ban: str) -> list:
    loi = G0.guardrail_check_g0(van_ban + "\n[CẦN BÁC SĨ XÁC NHẬN]\nCần bác sĩ kiểm chứng.", {"all_pmids": []})
    return [e for e in loi["errors"] if e.startswith("R2")]


@pytest.mark.parametrize("khoang", ["01/01/2026–31/12/2026", "01/01/2026 - 31/12/2026", "01-01-2026 đến 31-12-2026",
                                    "01/01/2026—31/12/2026"])
def test_r2_mien_khoang_ngay(khoang):
    assert not [e for e in _r2(f"Cửa sổ hồi cứu {khoang}.") if "ngày tháng năm" in e]


@pytest.mark.parametrize("le", ["Sinh ngày 12/03/1956.", "Khám 05-07-2026.",
                                "Từ 01/01/2026–31/12/2026; sinh 12/03/1956."])
def test_r2_van_bat_ngay_le(le):
    assert any("ngày tháng năm" in e for e in _r2(le))


# ── 4. A6: sơ đồ dùng giá trị G1 đã chốt ────────────────────────────────────────────────────────────────────────

LT = ["Từ chối tham gia", "Không đủ năng lực trả lời", "Nhân viên y tế của chính khoa"]
PN = "Thời gian chờ khám theo mốc HIS, hiệu ứng theo mỗi 15 phút"


def test_so_do_cat_ngang_dung_g1_va_mot_khoi_mau():
    s = G5.build_strobe_flowchart("S", "cross_sectional", 1000, 630, 630, n_toi_thieu=630,
                                  phoi_nhiem=PN, tieu_chi_loai_tru=LT)
    assert "tiêu chí loại trừ theo PICO" not in s and "tên biến phơi nhiễm" not in s
    assert "3 tiêu chuẩn loại trừ đã chốt ở G1" in s
    assert "Chú thích 1 — Tiêu chuẩn loại trừ đã chốt ở G1:\n    1. Từ chối tham gia" in s
    assert f"Chú thích 2 — Phơi nhiễm / biến giải thích đã chốt ở G1: {PN}" in s
    assert "KHÔNG PHƠI" not in s and "MẪU NGHIÊN CỨU (một thời điểm)" in s
    assert "Không đồng thuận" not in s and "[CẦN thêm lý do cụ thể]" not in s


def test_so_do_cohort_giu_hai_nhanh_tro_chu_thich():
    s = G5.build_strobe_flowchart("S", "cohort", 400, 360, 180, phoi_nhiem=PN, tieu_chi_loai_tru=LT)
    assert "KHÔNG PHƠI" in s and "NHIỄM (CT 2)" in s
    assert "THEO DÕI (Follow-up)" in s and "Chú thích 2" in s


def test_so_do_khong_co_g1_giu_nguyen_hanh_vi_cu():
    s = G5.build_strobe_flowchart("S", "cross_sectional", 100, 120, 60)
    assert "[CẦN — tiêu chí loại trừ theo PICO/SAP thật]" in s and "KHÔNG PHƠI" in s
    assert "Chú thích" not in s


@pytest.mark.parametrize("design", ["diagnostic", "prediction", "qualitative"])
def test_so_do_thiet_ke_khac_cung_dung_tieu_chi_g1(design):
    s = G5.build_strobe_flowchart("S", design, 100, 120, 60, tieu_chi_loai_tru=LT)
    assert "tiêu chí loại trừ theo PICO" not in s and "Chú thích 1" in s


def _meta(tmp_path, g1) -> None:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    (d / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": g1}}, ensure_ascii=False),
                                       encoding="utf-8", newline="\n")


def test_doc_g1_chi_khi_da_chot(tmp_path, monkeypatch):
    monkeypatch.setattr(G5, "BASE", tmp_path)
    _meta(tmp_path, {"design_confirmed": True, "exclusion_criteria": LT + ["  "], "intervention_or_exposure": PN})
    assert G5._g1_da_chot_cho_so_do(STUDY) == (PN, LT)


@pytest.mark.parametrize("g1", [{"design_confirmed": False, "exclusion_criteria": LT},
                                {"exclusion_criteria": LT, "intervention_or_exposure": PN},
                                {"design_confirmed": "true", "exclusion_criteria": LT}])
def test_doc_g1_chua_chot_tra_none(tmp_path, monkeypatch, g1):
    monkeypatch.setattr(G5, "BASE", tmp_path)
    _meta(tmp_path, g1)
    assert G5._g1_da_chot_cho_so_do(STUDY) == (None, None)


def test_doc_g1_thieu_tep_hoac_hong(tmp_path, monkeypatch):
    monkeypatch.setattr(G5, "BASE", tmp_path)
    assert G5._g1_da_chot_cho_so_do(STUDY) == (None, None)
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    (d / "study_meta.json").write_text("{hỏng", encoding="utf-8", newline="\n")
    assert G5._g1_da_chot_cho_so_do(STUDY) == (None, None)


# ── 5. Trục ⑤: sửa sau khi duyệt là việc ký lại, không phải sổ cái bất thường ──────────────────────────────────

def test_noi_dung_doi_sau_duyet_la_vang():
    ly_do = ("NỘI DUNG ĐÃ ĐỔI SAU KHI DUYỆT — G10_checkpoint.json hiện có hash 647cecbb6e76… nhưng bản duyệt gắn với "
             "c5db2f…. Phải trình lại bản đã sửa cho người duyệt.")
    assert KCT.mau_ly_do_ky(ly_do) == KCT.VANG


@pytest.mark.parametrize("ly_do", ["chữ ký KHÔNG KHỚP (bị sửa sau khi ký, ký bằng máy/khóa khác, hoặc khóa đã đổi)",
                                   "bản ghi đã THU HỒI", "sổ cái dị dạng: ValueError", "CHUỖI prev_hash gãy"])
def test_bat_thuong_so_cai_van_do(ly_do):
    assert KCT.mau_ly_do_ky(ly_do) == KCT.DO


def test_truc_5_ghi_dung_viec_cho_ky_lai(tmp_path, monkeypatch):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    ly_do = "NỘI DUNG ĐÃ ĐỔI SAU KHI DUYỆT — G10_checkpoint.json hiện có hash 6…"
    monkeypatch.setattr(KCT, "da_ky", lambda *_a: (False, ly_do))
    muc = [m for m in KCT.kiem_cong("G10", STUDY, out, {}, {}, {}, {}) if m.truc == "⑤"]
    assert len(muc) == 1
    assert muc[0].muc == KCT.VANG and "chờ ký lại" in muc[0].nhan
    assert "rà phần đã sửa rồi ký lại" in muc[0].hanh_dong and "điều tra sổ cái" not in muc[0].hanh_dong


def test_truc_5_bat_thuong_that_van_do_va_dieu_tra(tmp_path, monkeypatch):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    monkeypatch.setattr(KCT, "da_ky", lambda *_a: (False, "chữ ký KHÔNG KHỚP (bị sửa sau khi ký)"))
    muc = [m for m in KCT.kiem_cong("G10", STUDY, out, {}, {}, {}, {}) if m.truc == "⑤"]
    assert muc[0].muc == KCT.DO and "BẤT THƯỜNG" in muc[0].nhan and "điều tra sổ cái" in muc[0].hanh_dong


# ── R6: A1 đã chốt đầy đủ (PHẦN 1 + PHẦN 2 chỉ đọc) không còn bắt buộc nhãn [CẦN…] ─────────────────────────────

def _r6(van_ban: str) -> list:
    return [e for e in G0.guardrail_check_g0(van_ban + "\nCần bác sĩ kiểm chứng.", {"all_pmids": []})["errors"]
            if e.startswith("R6")]


def test_r6_da_chot_day_du_khong_doi_nhan_can():
    assert not _r6("## PHẦN 1 — PICO / PECO (đã chốt — chỉ đọc)\n## PHẦN 2 — KIỂM FINER (đã chốt — chỉ đọc)\n")


@pytest.mark.parametrize("van_ban", ["## PHẦN 1 — PICO / PECO (đã chốt — chỉ đọc)\n",
                                     "## PHẦN 2 — KIỂM FINER (đã chốt — chỉ đọc)\n", "Không có gì.\n"])
def test_r6_chua_chot_du_van_doi_nhan_can(van_ban):
    assert _r6(van_ban)


# ── 6. G10 A12: DOI không có PMID dùng kết quả kiem_rut_bai_trich_dan.py còn hạn ───────────────────────────────

DOI_LE = "10.9999/khong-ro"


def _ghi_json(p: Path, v) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")


def _goi_a12(tmp_path, monkeypatch, kiem: dict | None):
    configure_test_signing_key(tmp_path, monkeypatch)
    goc, study = tmp_path / "goc", "S-A12-DOI2"
    out = goc / "exports" / study
    _ghi_json(out / f"A12_CITATION_VERIFICATION_{study}.md",
              "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n")
    _ghi_json(out / f"DE_CUONG_THONG_NHAT_{study}.md",
              "Tài liệu tham khảo\n1. Tác giả A. Nguồn thử. Tạp chí thử. 2018. doi:10.5555/thu-1. PMID: 30560792.\n"
              f"2. Sách không có trên PubMed. doi:{DOI_LE}.\n")
    monkeypatch.setattr(CCR, "REPO_ROOT", goc)
    monkeypatch.setattr(CCM, "REPO_ROOT", goc)
    CCR.write_retraction_receipt(study, ["30560792"], {"30560792": {"status": "ok"}})
    CCM.write_metadata_receipt(study, ["30560792"], {"30560792": {"status": "resolved", "title": "Nguồn thử",
                                                                  "doi": "10.5555/thu-1"}})
    if kiem is not None:
        _ghi_json(out / f"KIEM_RUT_BAI_TRICH_DAN_{study}.json", {"study": study, **kiem})
    return study, out


def _kiem(trang_thai: str, ngay_truoc: int = 2, doi: str = DOI_LE) -> dict:
    luc = (datetime.now(timezone.utc) - timedelta(days=ngay_truoc)).isoformat(timespec="seconds")
    return {"checked_at": luc, "ket_qua": {f"doi:{doi}": {"status": trang_thai, "source": "crossref"}}}


@pytest.mark.parametrize("tt", ["ok", "correction"])
def test_a12_doi_da_kiem_con_han_khong_bat_tra_tay(tmp_path, monkeypatch, capsys, tt):
    study, out = _goi_a12(tmp_path, monkeypatch, _kiem(tt))
    ok, ly_do = G10A.citation_verification_ok(study, out)
    ra = capsys.readouterr().out
    assert ok, ly_do
    assert "1 DOI không có PMID đã kiểm rút bài qua Crossref/Retraction Watch" in ra
    assert "CẢNH BÁO CỔNG A12: phát hiện" not in ra


@pytest.mark.parametrize("tt", ["retracted", "expression_of_concern"])
def test_a12_doi_duong_tinh_thi_chan(tmp_path, monkeypatch, tt):
    study, out = _goi_a12(tmp_path, monkeypatch, _kiem(tt, doi=DOI_LE.upper()))
    ok, ly_do = G10A.citation_verification_ok(study, out)
    assert not ok and "ĐÃ RÚT" in ly_do and tt in ly_do


@pytest.mark.parametrize("kiem", [None, _kiem("ok", ngay_truoc=31), _kiem("unknown"), _kiem("ok", doi="10.1/khac"),
                                  {"checked_at": "2026-11-15T04:54:26", "ket_qua": {f"doi:{DOI_LE}": {"status": "ok"}}},
                                  {"checked_at": "hỏng", "ket_qua": {}}])
def test_a12_doi_chua_kiem_con_han_van_canh_bao(tmp_path, monkeypatch, capsys, kiem):
    study, out = _goi_a12(tmp_path, monkeypatch, kiem)
    ok, ly_do = G10A.citation_verification_ok(study, out)
    ra = capsys.readouterr().out
    assert ok, ly_do
    dong = next(d for d in ra.splitlines() if "CẢNH BÁO CỔNG A12: phát hiện" in d)
    assert DOI_LE in dong and f"kiem_rut_bai_trich_dan.py --study {study} --ghi" in dong


def test_a12_tep_kiem_cua_de_tai_khac_khong_dung(tmp_path, monkeypatch, capsys):
    study, out = _goi_a12(tmp_path, monkeypatch, None)
    _ghi_json(out / f"KIEM_RUT_BAI_TRICH_DAN_{study}.json", {"study": "DE-TAI-KHAC", **_kiem("ok")})
    G10A.citation_verification_ok(study, out)
    assert "CẢNH BÁO CỔNG A12: phát hiện" in capsys.readouterr().out


def test_a12_doi_so_khop_khong_phan_biet_hoa_thuong(tmp_path):
    """DOI không phân biệt hoa/thường: văn bản ghi «10.9999/KHONG-RO», tệp kết quả ghi chữ thường ⇒ vẫn là đã kiểm."""
    study = "S-A12-HOA"
    _ghi_json(tmp_path / f"KIEM_RUT_BAI_TRICH_DAN_{study}.json", {"study": study, **_kiem("ok")})
    da_kiem, duong_tinh = G10A._doi_da_kiem_rut_bai({DOI_LE.upper()}, study, tmp_path)
    assert da_kiem == {DOI_LE.upper()} and duong_tinh == {}
