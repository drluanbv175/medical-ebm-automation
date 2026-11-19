"""Hồi quy 19/11/2026 — ba văn bản agent mà bộ giả lập trọn vòng trước đây bỏ trống (G0-T3, G0-T4, G10-T3) và lỗ G7
lộ ra khi có chúng (hạt giống bản thảo bỏ qua sàng lọc G0-T3).

Mọi đầu ra phải qua ĐÚNG bộ kiểm của hệ — `g0_tong_hop.kiem_tong_hop/kiem_khoang_trong`,
`hoi_dong_cong._kiem_so_trang_thai` — không nới bộ kiểm nào. Ngoại tuyến: dùng nền G0 + nhánh không lọc đầy đủ đã lưu
ở tests/fixtures/gia_lap_nen_g0/.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import g0_tong_hop as GT  # noqa: E402
import gia_lap_van_ban_tac_tu as VB  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402

NEN = Path(__file__).resolve().parent / "fixtures" / "gia_lap_nen_g0"
CAC_NEN = sorted(p.name for p in NEN.iterdir() if p.is_dir() and not p.name.startswith("_"))
HOM_NAY = date(2026, 11, 19)


def _cp_raw(ten: str):
    d = NEN / ten
    return d, json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8")), \
        json.loads((d / "G0_pubmed_raw.json").read_text(encoding="utf-8"))


# ── G0-T3: tổng hợp bằng chứng ───────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", CAC_NEN)
def test_tong_hop_dat_bo_kiem_g0t3_moi_nen(ten):
    d, cp, raw = _cp_raw(ten)
    th = VB.soan_tong_hop(d, cp["study"], NEN, HOM_NAY)
    assert GT.kiem_tong_hop(th, cp["pubmed_results"]["all_pmids"], VB.nhanh_khong_loc(raw)) == []
    # Sàng ĐỦ: mọi PMID nền đúng một lần; mọi bản ghi nhánh không lọc ngoài nền nằm ở bổ sung hoặc lạc đề.
    assert sorted(x["pmid"] for x in th["sang_loc"]) == sorted(map(str, cp["pubmed_results"]["all_pmids"]))
    ngoai = {x["pmid"] for x in th["nguon_bo_sung"]} | {x["pmid"] for x in th["sang_loc_khong_loc"]}
    assert not ngoai & {x["pmid"] for x in th["sang_loc"]}


def test_tong_hop_thieu_nhanh_day_du_thi_bo_kiem_bao_thieu_khong_bia_pmid():
    d, cp, raw = _cp_raw("rct_nhi_phan")
    th = VB.soan_tong_hop(d, cp["study"], None, HOM_NAY)  # không có thư mục nền ⇒ không có nhánh đầy đủ
    assert "khong_loc_vuot_tran" not in th
    loi = GT.kiem_tong_hop(th, cp["pubmed_results"]["all_pmids"], VB.nhanh_khong_loc(raw))
    assert any("khong_loc_vuot_tran" in x for x in loi), loi


def test_tong_hop_nhanh_day_du_khac_truy_van_thi_khong_dung(tmp_path):
    d, cp, raw = _cp_raw("rct_nhi_phan")
    q = VB.nhanh_khong_loc(raw)["truy_van"]
    gia = json.loads(VB.tep_day_du(NEN, q).read_text(encoding="utf-8"))
    gia["truy_van"] = q + " AND khac"
    VB._ghi_json(VB.tep_day_du(tmp_path, q), gia)
    assert VB.doc_day_du(tmp_path, q) is None


def test_khoi_khai_niem_bo_khoi_thiet_ke_va_boi_canh():
    q = ('(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab]) AND (outpatient*[tiab] OR '
         '"primary care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])')
    assert VB.khoi_khai_niem(q) == [["hypertension"], ["blood pressure control"]]


@pytest.mark.parametrize("tieu_de,muc", [
    ("Text messaging to improve adherence in hypertension", "truc_tiep"),
    ("Text messaging to improve adherence in diabetes", "gian_tiep"),
    ("Text messaging for smoking cessation", "khong"),
    ("Statins and cancer", "khong"),
])
def test_xep_lien_quan_theo_so_khoi_cham(tieu_de, muc):
    khoi = [["text messaging"], ["hypertension"], ["adherence"]]
    assert VB.xep_lien_quan(tieu_de, khoi)[0] == muc


def test_xep_lien_quan_mot_khoi_thieu_la_khong_lien_quan():
    assert VB.xep_lien_quan("Statins", [["hypertension"]])[0] == "khong"
    assert VB.xep_lien_quan("Hypertension", [["hypertension"]])[0] == "truc_tiep"


def test_rut_bai_khong_liet_ke_pmid_chua_kiem(tmp_path):
    """PMID chưa kiểm không được xuất hiện trong `rut_bai` (kể cả danh sách `pmid_da_kiem` mà bộ đối chiếu xuyên cổng
    tin); không bao giờ ghi «chưa bị rút»."""
    kho = tmp_path / "a12.json"
    kho.write_text(json.dumps({"retraction": {"11111111": {"status": "ok"},
                                              "22222222": {"status": "retracted"}}}), encoding="utf-8", newline="\n")
    rb = VB._rut_bai(["11111111", "22222222", "33333333"], kho, HOM_NAY)
    assert "33333333" not in json.dumps(rb)
    assert "22222222" in rb["ket_qua"] and "1 PMID còn lại chưa kiểm" in rb["ket_qua"]
    assert "chưa bị rút" not in rb["ket_qua"]
    assert rb["pmid_da_kiem"] == ["11111111", "22222222"]
    rb0 = VB._rut_bai(["33333333"], None, HOM_NAY)
    assert "0/1" in rb0["ket_qua"] and "33333333" not in json.dumps(rb0) and rb0["pmid_da_kiem"] == []


# ── G0-T4: khoảng trống ──────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", CAC_NEN)
def test_khoang_trong_dat_bo_kiem_g0t4_moi_nen(ten):
    import gia_lap_dinh_ky as GL

    d, cp, _raw = _cp_raw(ten)
    kb = next((k for k in GL.KICH_BAN.values() if k["study"] == cp["study"]), {})
    kt = VB.soan_khoang_trong(d, cp["study"], {"gate_params": {"G0": (kb.get("pi") or {}).get("G0") or {}}}, HOM_NAY)
    assert GT.kiem_khoang_trong(kt) == []
    for k in GT.FINER_CHI_PI:
        assert kt["nhap_finer"][k].startswith(GT.TIEN_TO_PI)


def test_khoang_trong_ha_khang_dinh_tuyet_doi(tmp_path):
    d, cp, _raw = _cp_raw("rct_nhi_phan")
    kt = VB.soan_khoang_trong(d, cp["study"], {"gate_params": {"G0": {
        "novelty_justification": "Đây là nghiên cứu lần đầu tiên tại Việt Nam về tin nhắn nhắc thuốc."}}}, HOM_NAY)
    assert not GT._TUYET_DOI.search(kt["phat_bieu_khoang_trong"])
    assert GT.kiem_khoang_trong(kt) == []


def test_khoang_trong_guideline_chi_co_tieu_de_ghi_partial(tmp_path):
    """Dòng guideline mới có tiêu đề (bộ giả lập không đọc văn bản) phải tự khai PARTIAL — bộ đối chiếu xuyên cổng bỏ
    qua dòng đó thay vì đòi trích vào TLTK một văn bản chưa ai đọc."""
    d = tmp_path / "S"
    d.mkdir()
    (d / "G0_checkpoint.json").write_text("{}", encoding="utf-8", newline="\n")
    (d / "G0_pubmed_raw.json").write_text(json.dumps({"guideline": [
        {"pmid": "37345492", "title": "2023 ESH Guidelines for the management of arterial hypertension",
         "journal": "J Hypertens", "year": "2023"}]}), encoding="utf-8", newline="\n")
    kt = VB.soan_khoang_trong(d, "S", {}, HOM_NAY)
    assert kt["guideline_lien_quan"][0]["noi_dung"].startswith("PARTIAL")
    assert GT.kiem_khoang_trong(kt) == []


# ── G10-T3: sổ trạng thái ────────────────────────────────────────────────────────────────────────────────────────
def _so_cai(d: Path, cong):
    so_cai = json.dumps([{"gate_id": g, "decision": "APPROVED"} for g in cong])
    (d / "approval_ledger.json").write_text(so_cai, encoding="utf-8", newline="\n")


def test_so_trang_thai_dat_bo_kiem_g10t3(tmp_path):
    s = "ZZCANARY-THU"
    _so_cai(tmp_path, ["G2", "G4"])
    VB.noi_so_trang_thai(tmp_path, s, "G2", "2026-11-19", "G2_A3 — vai IRB ký")
    VB.noi_so_trang_thai(tmp_path, s, "G4", "2026-11-19", "SAP — vai PI ký")
    assert HD._kiem_so_trang_thai(tmp_path, s) == []


def test_so_trang_thai_thieu_cong_da_ky_thi_bao(tmp_path):
    s = "ZZCANARY-THU"
    _so_cai(tmp_path, ["G2", "G4"])
    VB.noi_so_trang_thai(tmp_path, s, "G2", "2026-11-19", "G2_A3 — vai IRB ký")
    loi = HD._kiem_so_trang_thai(tmp_path, s)
    assert any("G4" in x for x in loi), loi


def test_so_trang_thai_chi_noi_them(tmp_path):
    s = "ZZCANARY-THU"
    p = VB.noi_so_trang_thai(tmp_path, s, "G2", "2026-11-18", "lần một")
    truoc = p.read_text(encoding="utf-8")
    VB.noi_so_trang_thai(tmp_path, s, "G4", "2026-11-19", "lần hai")
    sau = p.read_text(encoding="utf-8")
    assert sau.startswith(truoc.rstrip("\n")) and sau.count("## CHECKPOINT") == 2
    assert "ZZCANARY-THU — G10" not in sau
    assert re.search(r"buoc_ke:\s+G5", sau)


# ── nối vào bộ giả lập ───────────────────────────────────────────────────────────────────────────────────────────
def _gia_lap(tmp_path, ma="rct_nhi_phan"):
    import gia_lap_dinh_ky as GL

    kb = GL.KICH_BAN[ma]
    goi = []

    def chay(cmd, *_a, **_k):
        goi.append([str(x) for x in cmd])
        return {"ma": 0, "ra": "", "crash": False}

    gl = GL.GiaLap(ma, kb, tmp_path / "repo", False, chay=chay, cham=lambda *a, **k: {}, nen_g0_dir=NEN)
    gl.out.mkdir(parents=True)
    for p in (NEN / ma).iterdir():
        if p.is_file() and p.name.startswith("G0_"):
            shutil.copy2(p, gl.out / p.name)
    return gl, goi


def test_buoc_agent_g0_soan_hai_tep_dung_lai_a1_va_khong_lap(tmp_path, monkeypatch):
    monkeypatch.delenv("GIA_LAP_A12_KHO", raising=False)
    gl, goi = _gia_lap(tmp_path)
    assert gl._soan_van_ban_g0() is True
    assert (gl.out / GT.TEP_TONG_HOP.format(study=gl.study)).is_file()
    assert (gl.out / GT.TEP_KHOANG_TRONG.format(study=gl.study)).is_file()
    assert any("run_g0_auto.py" in " ".join(c) and "--dung-lai-a1" in c for c in goi)
    ct = gl.can_thiep[-1]
    assert ct["loai"] == "soan_van_ban_g0" and ct["do_may"] is False
    assert gl._soan_van_ban_g0() is False  # đã soạn cho tập PMID này — không lặp


def test_buoc_agent_g0_soan_xong_van_loi_thi_khong_lap(tmp_path, monkeypatch):
    """Thiếu nhánh đầy đủ ⇒ tổng hợp soạn ra vẫn không đạt bộ kiểm; lần gọi sau KHÔNG soạn lại (lỗi đó là khiếm khuyết
    thật để báo, không phải lý do quay vòng tới hết 14 lượt PI)."""
    monkeypatch.delenv("GIA_LAP_A12_KHO", raising=False)
    gl, goi = _gia_lap(tmp_path)
    gl.nen_g0_dir = tmp_path / "nen-trong"
    assert gl._soan_van_ban_g0() is True
    th = json.loads((gl.out / GT.TEP_TONG_HOP.format(study=gl.study)).read_text(encoding="utf-8"))
    assert GT.kiem_tong_hop(th, json.loads((gl.out / "G0_checkpoint.json").read_text(encoding="utf-8"))
                            ["pubmed_results"]["all_pmids"],
                            VB.nhanh_khong_loc(json.loads((gl.out / "G0_pubmed_raw.json").read_text(encoding="utf-8"))))
    n = len(goi)
    assert gl._soan_van_ban_g0() is False and len(goi) == n


def test_buoc_agent_g0_khong_soan_lai_khi_tep_con_dat(tmp_path, monkeypatch):
    monkeypatch.delenv("GIA_LAP_A12_KHO", raising=False)
    gl, goi = _gia_lap(tmp_path)
    gl._soan_van_ban_g0()
    gl._da_soan_g0.clear()
    n = len(goi)
    assert gl._soan_van_ban_g0() is False and len(goi) == n


def test_luu_nen_khong_chep_tep_cua_agent(tmp_path, monkeypatch):
    import gia_lap_dinh_ky as GL

    gl, _goi = _gia_lap(tmp_path)
    gl._soan_van_ban_g0()
    gl.nen_g0_dir = tmp_path / "nen"
    monkeypatch.setattr(GL.GiaLap, "_luu_nhanh_day_du", lambda self: None)
    gl.luu_nen_g0()
    ten = {p.name for p in (tmp_path / "nen" / "rct_nhi_phan").iterdir()}
    assert "G0_checkpoint.json" in ten
    assert not {GT.TEP_TONG_HOP.format(study=gl.study), GT.TEP_KHOANG_TRONG.format(study=gl.study)} & ten


def test_ky_thanh_cong_noi_so_trang_thai_ky_hong_thi_khong(tmp_path, monkeypatch):
    import gia_lap_tron_vong as TV

    ma = {"v": 0}
    tv = TV.TronVong("rct_nhi_phan", tmp_path / "repo", hom_nay=HOM_NAY,
                     chay=lambda *a, **k: {"ma": ma["v"], "ra": "", "crash": False}, nen_g0_dir=NEN)
    tv.out.mkdir(parents=True)
    monkeypatch.setattr(TV, "duoi_pytest_khoa_gia", lambda: True)
    tv.env.update({"PYTEST_CURRENT_TEST": "x", "EBM_GATE_KEY_PATH": str(tmp_path / "khoa")})
    so = tv.out / VB.TEP_SO_TRANG_THAI.format(study=tv.study)
    ma["v"] = 3
    tv._ky("G2", "G2_A3.md", "IRB", "R")
    assert not so.exists()
    ma["v"] = 0
    tv._ky("G2", "G2_A3.md", "IRB", "R")
    assert so.read_text(encoding="utf-8").count("cong_vua_qua:   G2") == 1


# ── G7: hạt giống bản thảo theo sàng lọc G0-T3 ──────────────────────────────────────────────────────────────────
def test_g7_hat_giong_bo_lac_de_uu_tien_truc_tiep(tmp_path):
    import run_g7_auto as G7

    s = "S"
    (tmp_path / GT.TEP_TONG_HOP.format(study=s)).write_text(json.dumps({
        "sang_loc": [{"pmid": "1000001", "lien_quan": "khong"}, {"pmid": "1000002", "lien_quan": "gian_tiep"},
                     {"pmid": "1000003", "lien_quan": "truc_tiep"}],
        "sang_loc_khong_loc": [{"pmid": "1000004", "lien_quan": "khong"}],
        "nguon_bo_sung": [{"pmid": "1000005", "lien_quan": "truc_tiep"}]}), encoding="utf-8", newline="\n")
    ds = ["1000001", "1000002", "1000003", "1000004", "1000005", "1000006"]
    assert G7.uu_tien_theo_sang_loc_g0(tmp_path, s, ds) == ["1000003", "1000005", "1000002", "1000006"]


def test_g7_hat_giong_khong_co_tong_hop_giu_nguyen(tmp_path):
    import run_g7_auto as G7

    assert G7.uu_tien_theo_sang_loc_g0(tmp_path, "S", ["3", "1", "2"]) == ["3", "1", "2"]
    (tmp_path / GT.TEP_TONG_HOP.format(study="S")).write_text("{hỏng", encoding="utf-8", newline="\n")
    assert G7.uu_tien_theo_sang_loc_g0(tmp_path, "S", ["3", "1", "2"]) == ["3", "1", "2"]


def test_g7_main_that_dung_hat_giong_theo_sang_loc_g0(tmp_path, monkeypatch):
    """Dây nối: run_g7_auto.main() THẬT (chuỗi G0→G6 khoá của test G7) ghi `pmids_used_as_seed` đã bỏ bài lạc đề và
    xếp bài trực tiếp đứng đầu — không chỉ hàm thuần đúng mà main phải GỌI nó."""
    from tests.test_g7_hoan_thien_20261004 import _chay_g7, _de_tai_g6_that, _xac_nhan_g6

    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, "rct")
    _xac_nhan_g6(out, study)
    bai = [{"pmid": p, "title": f"Bài {p}", "year": "2025", "journal": "J"} for p in ("30000001", "30000002",
                                                                                       "30000003")]
    (out / "G0_pubmed_raw.json").write_text(json.dumps({"sr_ma": bai}), encoding="utf-8", newline="\n")
    (out / GT.TEP_TONG_HOP.format(study=study)).write_text(json.dumps({"sang_loc": [
        {"pmid": "30000001", "lien_quan": "khong"}, {"pmid": "30000002", "lien_quan": "gian_tiep"},
        {"pmid": "30000003", "lien_quan": "truc_tiep"}]}), encoding="utf-8", newline="\n")
    _chay_g7(goc, study, monkeypatch)
    cp = json.loads((out / "G7_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["pmids_used_as_seed"] == ["30000003", "30000002"]


def test_bai_ho_so_da_dan_khong_bi_xep_lac_de_chi_vi_tieu_de():
    """PMID 36828607 (SR/MA «digital health interventions … hypertension») chủ nhiệm dẫn làm bằng chứng nền; tiêu đề
    không nêu «text messaging»/«adherence» nên luật tiêu đề xếp «khong» ⇒ TLTK đề cương trích «bài lạc đề» (trục
    trich_dan_tong_quan cần xem, đo 19/11/2026). Bài hồ sơ đã dẫn ⇒ tối thiểu gián tiếp, tóm tắt nói rõ lý do."""
    d, cp, raw = _cp_raw("rct_nhi_phan")
    import gia_lap_dinh_ky as GL

    da_dan = VB.pmid_trong(GL.KICH_BAN["rct_nhi_phan"]["pi"])
    assert "36828607" in da_dan
    tron = {x["pmid"]: x for x in VB.soan_tong_hop(d, cp["study"], NEN, HOM_NAY)["sang_loc"]}
    assert tron["36828607"]["lien_quan"] == "khong"  # luật tiêu đề một mình
    th = VB.soan_tong_hop(d, cp["study"], NEN, HOM_NAY, pmid_da_dan=da_dan)
    x = next(x for x in th["sang_loc"] if x["pmid"] == "36828607")
    assert x["lien_quan"] == "gian_tiep" and "Hồ sơ đề tài dẫn" in x["tom_tat"] and "ly_do" not in x
    assert GT.kiem_tong_hop(th, cp["pubmed_results"]["all_pmids"], VB.nhanh_khong_loc(raw)) == []


def test_buoc_agent_g0_truyen_pmid_ho_so_da_dan(tmp_path, monkeypatch):
    """Dây nối: bước agent G0 của bộ giả lập truyền PMID nội dung kịch bản vào bộ soạn ⇒ 36828607 không lạc đề."""
    monkeypatch.delenv("GIA_LAP_A12_KHO", raising=False)
    gl, _goi = _gia_lap(tmp_path)
    gl._soan_van_ban_g0()
    th = json.loads((gl.out / GT.TEP_TONG_HOP.format(study=gl.study)).read_text(encoding="utf-8"))
    assert next(x for x in th["sang_loc"] if x["pmid"] == "36828607")["lien_quan"] == "gian_tiep"
