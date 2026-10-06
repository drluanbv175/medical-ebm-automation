"""Hoàn thiện từng bước sau đợt soát G0–G10 (06/10/2026) — bốn việc treo trong VIEC-CON.

1. exports/<study>/ neo theo GỐC REPO, không theo thư mục đang đứng: run_g0/g1/g2_auto (+ cờ --repo-root),
   g0_quality_gate (--exports-dir mặc định), run_stats_analysis (BASE). Lộ thật: agent hướng dẫn
   `python medical-ebm-automation/tools/run_g0_auto.py` từ repo gốc ⇒ G0–G2 ghi exports/ ở repo gốc trong khi G3–G10
   đọc medical-ebm-automation/exports/ (hồ sơ một đề tài tách đôi; repo gốc còn thư mục rác PYTEST-GATEEXIT-G1).
2. G0-06: loại giả thuyết mặc định của G3 lấy từ test_type G0 đã khai — CÓ XÉT thiết kế (định tính/SR-MA/tiên lượng
   không dùng khung giả thuyết: «descriptive» của chúng KHÔNG phải «cỡ mẫu theo độ chính xác»).
3. Đề cương G10 «Dự trù kinh phí» đọc gate_params.G1.budget (cùng nguồn bảng KINH PHÍ của A13).
4. A12: DOI in KÈM PMID đã kiểm rút bài (Vancouver từ metadata PubMed, tài liệu chuẩn SPIRIT/PRISMA-P) không còn bị
   cảnh báo «phải tự tra Retraction Watch»; DOI không ghép được PMID đã kiểm vẫn cảnh báo.

Dữ liệu tổng hợp, không PII. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402
import cong_song as CS  # noqa: E402
import protocol_checklist_items as PCI  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g0_auto as G0A  # noqa: E402
import run_g1_auto as G1A  # noqa: E402
import run_g2_auto as G2A  # noqa: E402
import run_g3_auto as R3  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402
import skill_standards as S  # noqa: E402

from tests._chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402
from tests.g5_test_helpers import configure_test_signing_key  # noqa: E402

PYTHON = sys.executable


def _ghi(p: Path, noi_dung) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(noi_dung, str):
        noi_dung = json.dumps(noi_dung, ensure_ascii=False, indent=2)
    p.write_text(noi_dung, encoding="utf-8", newline="\n")
    return p


# ═══════════════════════════════════ 1. exports neo theo gốc repo ═══════════════════════════════════════════════════
def _goi_path_exports(tep: Path) -> list:
    """Các lời gọi THI HÀNH dạng Path("exports") trong tệp — đọc bằng AST nên chú thích/docstring không tính."""
    cay = ast.parse(tep.read_text(encoding="utf-8"))
    return [n.lineno for n in ast.walk(cay)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Path"
            and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value in ("exports", "exports/")]


def test_khong_con_duong_dan_exports_theo_thu_muc_dang_dung():
    for ten in ("run_g0_auto.py", "run_g1_auto.py", "run_g2_auto.py", "run_stats_analysis.py", "g0_quality_gate.py"):
        assert _goi_path_exports(REPO_ROOT / "tools" / ten) == [], f"{ten} còn Path('exports') theo thư mục đang đứng"


def test_moc_mac_dinh_la_goc_repo_y_khoa_va_va_duoc(tmp_path, monkeypatch):
    for mod in (G0A, G1A, G2A):
        assert mod._REPO_ROOT == REPO_ROOT, mod.__name__
    assert RSA.BASE == REPO_ROOT
    khac = tmp_path / "noi-khac"
    khac.mkdir()
    monkeypatch.chdir(khac)  # thư mục đang đứng KHÔNG được ảnh hưởng
    for mod in (G0A, G1A, G2A):
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path / "goc")
        assert mod._thu_muc_de_tai("S") == tmp_path / "goc" / "exports" / "S", mod.__name__
    monkeypatch.setattr(RSA, "BASE", tmp_path / "goc")
    assert RSA._thu_muc_de_tai("S") == tmp_path / "goc" / "exports" / "S"


def test_run_g0_cli_ghi_vao_goc_repo_khong_theo_cwd(tmp_path):
    goc, khac = tmp_path / "goc", tmp_path / "khac"
    khac.mkdir()
    env = dict(os.environ, USE_MOCK_SOURCES="true", PYTHONUTF8="1")
    r = subprocess.run([PYTHON, str(REPO_ROOT / "tools" / "run_g0_auto.py"), "--study", "S-GOC", "--topic", " ",
                        "--repo-root", str(goc)], cwd=khac, env=env, capture_output=True, text=True, timeout=180)
    assert r.returncode == 2, r.stdout[-600:] + r.stderr[-600:]
    assert (goc / "exports" / "S-GOC" / "G0_checkpoint.json").is_file()
    assert not (khac / "exports").exists(), "run_g0_auto vẫn ghi theo thư mục đang đứng"


def test_g0_quality_gate_mac_dinh_doc_exports_cua_repo(tmp_path):
    khac = tmp_path / "khac"
    khac.mkdir()
    r = subprocess.run([PYTHON, str(REPO_ROOT / "tools" / "g0_quality_gate.py"), "--study", "KHONG-CO-DE-TAI-NAY"],
                       cwd=khac, env=dict(os.environ, PYTHONUTF8="1"), capture_output=True, text=True, timeout=120)
    assert str(REPO_ROOT / "exports" / "KHONG-CO-DE-TAI-NAY") in r.stdout, r.stdout[-400:]


def test_run_stats_doc_checkpoint_manifest_va_so_cai_theo_base(tmp_path, monkeypatch):
    goc = tmp_path / "goc"
    _ghi(goc / "exports" / "S" / "G3_checkpoint.json", {"hypothesis_type": "superiority"})
    _ghi(goc / "exports" / "S" / "study_meta.json", {"real_data_lock": {"manifest": "khoa/DATA_LOCK_manifest.json"}})
    monkeypatch.setattr(RSA, "BASE", goc)
    monkeypatch.chdir(tmp_path)
    assert RSA._load_checkpoint("S", "G3") == {"hypothesis_type": "superiority"}
    assert RSA._data_lock_manifest_path("S") == goc / "exports" / "S" / "khoa" / "DATA_LOCK_manifest.json"
    goi = []
    monkeypatch.setattr(RSA.GC, "ledger_approved", lambda *a, **k: goi.append(k) or False)
    monkeypatch.setattr(RSA.GC, "locked_analysis_dataset_blockers", lambda *a, **k: goi.append(k) or ([], {}))
    RSA._ledger_approved("S", "G4", goc / "exports" / "S" / "x.md")
    with contextlib.redirect_stdout(io.StringIO()):
        RSA._require_locked_analysis_dataset("S", "d.csv")
    assert len(goi) == 2 and all(k.get("repo_root") == goc for k in goi), goi


# ═══════════════════════════════════ 2. G0-06 — giả thuyết từ test_type G0 ═════════════════════════════════════════
def test_gia_thuyet_tu_test_type_co_xet_thiet_ke():
    assert S.gia_thuyet_tu_test_type("non_inferiority", "rct") == "non_inferiority"
    assert S.gia_thuyet_tu_test_type("Equivalence", "cohort") == "equivalence"
    assert S.gia_thuyet_tu_test_type("descriptive", "cross_sectional") == "descriptive_precision"
    for ma in ("qualitative", "sr_ma", "prediction", "Định tính"):
        assert S.gia_thuyet_tu_test_type("descriptive", ma) is None, ma
    assert S.gia_thuyet_tu_test_type("superiority", "sr_ma") is None
    assert S.gia_thuyet_tu_test_type(None, "rct") is None and S.gia_thuyet_tu_test_type("xyz", "rct") is None


def test_dac_ta_dung_lai_lay_test_type_g0_khi_g3_chua_ghim(tmp_path):
    _ghi(tmp_path / "study_meta.json", {"design_code": "cohort", "gate_params": {"G0": {"test_type": "equivalence"}}})
    assert S.dac_ta_thiet_ke(tmp_path)["hypothesis_type"] == "equivalence"
    _ghi(tmp_path / "study_meta.json", {"design_code": "cohort", "gate_params": {
        "G0": {"test_type": "equivalence"}, "G3": {"hypothesis_type": "superiority"}}})
    assert S.dac_ta_thiet_ke(tmp_path)["hypothesis_type"] == "superiority", "G3 đã ghim thắng G0"
    _ghi(tmp_path / "study_meta.json",
         {"design_code": "qualitative", "gate_params": {"G0": {"test_type": "descriptive"}}})
    assert S.dac_ta_thiet_ke(tmp_path)["hypothesis_type"] is None


def test_khoi_dac_ta_g1_cung_luat_co_xet_thiet_ke():
    meta = {"gate_params": {"G0": {"test_type": "descriptive"}}}
    assert G1A.dac_ta_thiet_ke_g1({"internal_code": "qualitative"}, "qualitative", meta)["hypothesis_type"] is None
    assert G1A.dac_ta_thiet_ke_g1({"internal_code": "cross_sectional"}, "descriptive", meta)["hypothesis_type"] == \
        "descriptive_precision"
    meta_ni = {"gate_params": {"G0": {"test_type": "non_inferiority"}}}
    assert G1A.dac_ta_thiet_ke_g1({"internal_code": "rct"}, "therapy", meta_ni)["hypothesis_type"] == "non_inferiority"


def _chay_g3(tmp_path, monkeypatch, study, argv, *, khoi_g1_khong_gia_thuyet: bool):
    """G0/G1 rct (G0 khai test_type non_inferiority SAU khi chốt — không kiểm sống) rồi chạy run_g3_auto THẬT."""
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="rct", mau_hieu_qua=[], kiem=False, them_meta={
        "G0": {"test_type": "non_inferiority"}, "G3": {"margin": 0.10, "outcome_direction": "higher_better"}})
    if khoi_g1_khong_gia_thuyet:  # G1 đã ghi khối đặc tả TRƯỚC khi G0 khai test_type
        cp1 = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))
        cp1["dac_ta_thiet_ke"] = {**{k: None for k in S.DAC_TA_KHOA}, "design_code": "rct"}
        _ghi(d / "G1_checkpoint.json", cp1)
    monkeypatch.setattr(R3, "BASE", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    CS.xoa_dem()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
        R3.main()
    return json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8"))


def test_g3_lay_gia_thuyet_tu_g0_khi_khoi_g1_khong_mang(tmp_path, monkeypatch):
    cp = _chay_g3(tmp_path, monkeypatch, "S-G006", ["--effect-size", "0.85", "--p0", "0.65"],
                  khoi_g1_khong_gia_thuyet=True)
    assert cp["hypothesis_type"] == "non_inferiority" and cp["n_per_group"] == 25
    assert cp["nguon_tham_so"]["hypothesis_type"] == "G0 test_type (study_meta.gate_params.G0)"


def test_g3_lay_gia_thuyet_tu_g0_qua_dac_ta_dung_lai(tmp_path, monkeypatch):
    cp = _chay_g3(tmp_path, monkeypatch, "S-G006B", ["--effect-size", "0.85", "--p0", "0.65"],
                  khoi_g1_khong_gia_thuyet=False)
    assert cp["hypothesis_type"] == "non_inferiority"
    assert cp["nguon_tham_so"]["hypothesis_type"] == "đặc tả thiết kế G1 (suy_lai)"


def test_g3_cli_van_thang_g0(tmp_path, monkeypatch):
    cp = _chay_g3(tmp_path, monkeypatch, "S-G006C",
                  ["--effect-size", "5", "--effect-type", "MD", "--sd", "10", "--hypothesis-type", "superiority"],
                  khoi_g1_khong_gia_thuyet=True)
    assert cp["hypothesis_type"] == "superiority" and cp["nguon_tham_so"]["hypothesis_type"] == "CLI"


# ═══════════════════════════════════ 3. Kinh phí G1 → đề cương G10 ═══════════════════════════════════════════════════
_KINH_PHI = [{"nhom": "Nhân công", "so_luong": 2, "don_gia": "5.000.000 đ/tháng", "nguon": "Định mức đơn vị 2026",
              "thanh_tien": "60.000.000 đ", "trang_thai": "Dự thảo"},
             {"nhom": "Văn phòng phẩm", "so_luong": 1, "don_gia": "2.000.000 đ", "thanh_tien": "2.000.000 đ",
              "trang_thai": "Đã duyệt"}]


def test_tom_tat_kinh_phi_g1_chi_khi_du_o():
    van = RS._kinh_phi_g1(_KINH_PHI)
    assert van == ("Nhân công: số lượng 2 × đơn giá 5.000.000 đ/tháng (nguồn đơn giá: Định mức đơn vị 2026) = "
                   "60.000.000 đ — Dự thảo; Văn phòng phẩm: số lượng 1 × đơn giá 2.000.000 đ = 2.000.000 đ — Đã duyệt "
                   "(bảng KINH PHÍ của A13)")
    thieu = [dict(_KINH_PHI[0]), {"nhom": "Văn phòng phẩm", "so_luong": 1}]
    assert RS._kinh_phi_g1(thieu) is None, "còn ô trống ⇒ đề cương giữ [CẦN], không in dự trù dở dang"
    assert RS._kinh_phi_g1([]) is None and RS._kinh_phi_g1(None) is None and RS._kinh_phi_g1(["chuỗi"]) is None


def test_studyspec_va_meta_render_lay_kinh_phi_tu_g1():
    meta = {"gate_params": {"G1": {"budget": _KINH_PHI, "team_roles": "PI: bác sĩ A; thống kê: B"}}}
    spec = RS.build_study_spec("S", {}, meta)
    assert "Nhân công" in spec["resources"]["budget"] and spec["resources"]["team"].startswith("PI:")
    tho = {"resources": {"team": "Nhóm do PI khai trực tiếp"}, **meta}
    ra = RS.meta_for_render(tho, spec)
    assert ra["resources"]["team"] == "Nhóm do PI khai trực tiếp", "khoá PI khai trực tiếp vẫn thắng"
    assert "Nhân công" in ra["resources"]["budget"]
    assert tho["resources"] == {"team": "Nhóm do PI khai trực tiếp"}, "không sửa dict thô của study_meta"
    assert "Nhân công: số lượng 2" in G10A.sec_tiendo({}, ra)
    meta_thieu = {"gate_params": {"G1": {"budget": [{"nhom": "Nhân công"}]}}}
    assert RS.build_study_spec("S", {}, meta_thieu)["resources"]["budget"] is None


# ═══════════════════════════════════ 4. A12 — DOI kèm PMID đã kiểm ═══════════════════════════════════════════════════
def test_cap_doi_pmid_tai_lieu_chuan_khop_tap_pmid_chuan():
    cap = PCI.cap_doi_pmid_tai_lieu_chuan()
    assert cap == {"10.1001/jama.2025.4486": "40294593", "10.1136/bmj-2024-081660": "40294956",
                   "10.1186/2046-4053-4-1": "25554246"}
    assert set(cap.values()) <= set(PCI.pmid_tai_lieu_chuan())


def test_doi_chi_duoc_coi_la_da_phu_khi_pmid_song_song_da_kiem(tmp_path):
    _ghi(tmp_path / "A12_METADATA_RECEIPT.json", {"metadata": {
        "11111111": {"status": "resolved", "doi": "10.5555/Phu.Qua.Metadata"},
        "22222222": {"status": "resolved", "doi": "10.5555/pmid-chua-kiem"},
        "33333333": {"status": "not_found", "doi": "10.5555/chua-phan-giai"}}})
    dois = {"10.5555/phu.qua.metadata", "10.5555/pmid-chua-kiem", "10.5555/chua-phan-giai", "10.1001/JAMA.2025.4486",
            "10.1136/bmj-2024-081660", "10.9999/khong-ro"}
    phu = G10A._doi_co_pmid_da_kiem(dois, {"11111111", "33333333", "40294593"}, tmp_path)
    assert phu == {"10.5555/phu.qua.metadata", "10.1001/JAMA.2025.4486"}
    assert G10A._doi_co_pmid_da_kiem(dois, set(), tmp_path) == set()
    _ghi(tmp_path / "A12_METADATA_RECEIPT.json", "[]")  # biên nhận dị dạng ⇒ chỉ còn cặp tài liệu chuẩn
    assert G10A._doi_co_pmid_da_kiem(dois, {"11111111", "40294956"}, tmp_path) == {"10.1136/bmj-2024-081660"}


def test_a12_chi_canh_bao_doi_khong_ghep_duoc(tmp_path, monkeypatch, capsys):
    configure_test_signing_key(tmp_path, monkeypatch)
    goc, study = tmp_path / "goc", "S-A12-DOI"
    out = goc / "exports" / study
    _ghi(out / f"A12_CITATION_VERIFICATION_{study}.md",
         "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n")
    _ghi(out / f"DE_CUONG_THONG_NHAT_{study}.md",
         "Tài liệu tham khảo\n1. Chan AW. SPIRIT 2025. JAMA. 2025. doi:10.1001/jama.2025.4486. PMID: 40294593.\n"
         "2. Tác giả A. Nguồn thử. Tạp chí thử. 2018. doi:10.5555/thu-1. PMID: 30560792.\n"
         "3. Hướng dẫn không có trên PubMed. doi:10.9999/khong-ro.\n")
    monkeypatch.setattr(CCR, "REPO_ROOT", goc)
    monkeypatch.setattr(CCM, "REPO_ROOT", goc)
    pmids = ["40294593", "30560792"]
    CCR.write_retraction_receipt(study, pmids, {p: {"status": "ok"} for p in pmids})
    CCM.write_metadata_receipt(study, pmids, {"40294593": {"status": "resolved", "title": "SPIRIT 2025"},
                                              "30560792": {"status": "resolved", "title": "Nguồn thử",
                                                           "doi": "10.5555/thu-1"}})
    ok, ly_do = G10A.citation_verification_ok(study, out)
    ra = capsys.readouterr().out
    assert ok, ly_do
    assert "2 DOI có PMID song song đã nằm trong biên nhận rút bài" in ra
    canh_bao = next(d for d in ra.splitlines() if "CẢNH BÁO CỔNG A12: phát hiện" in d)
    assert "phát hiện 1 DOI" in canh_bao and "10.9999/khong-ro" in canh_bao and "jama.2025.4486" not in canh_bao
