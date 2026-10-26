# -*- coding: utf-8 -*-
"""Hồi quy 26/10/2026 — bốn lỗi máy lộ ra khi thi công lượt sửa C1a (phương án A: CV cỡ chùm 0,14) và diễn tập đường PI.

1. G10-AUTO-03 (gói TRƯỚC dữ liệu): checkpoint G5 dự thảo (có từ 24/10) sinh trước G1–G4 vừa chạy lại ⇒ «G5 cũ» chặn
   gói trình Hội đồng Y đức, trong khi gói không mang tài liệu G5–G9 và G5 chỉ chạy lại được sau khi G4 KÝ (vòng chặn).
2. A4 của G3: bảng độ nhạy in «DE = 1.39 (= 1+(m−1)×ICC…)» — con số là công thức Eldridge có CV, nhãn là công thức
   cụm đều.
3. A2 của G1: «hệ số thiết kế 1.38784» — in thô số G3 lưu đủ chữ số.
4. Hội đồng: «không áp dụng (thiết kế can thiệp (RCT))» đọc như thể đề tài cắt ngang LÀ RCT.
5–7. Việc sửa của hội đồng G1 25/10/2026 (G1-T1 RQ5/RQ8, G1-T2 RQ3/RQ4/RQ8) mà bộ sinh viết cứng: ô «Chọn mẫu»/«Thước
   đo kết hợp» không bao giờ được đánh dấu; PHẦN 7 của A2 ghi «☐ … [CHỜ]» cho xác nhận người đã PASS, «Chưa có effect
   size» cho thiết kế độ chính xác, «SAP skeleton đã sinh» ngay dưới PHẦN 5 nói khung đã thay; sổ A2b gắn «(theo tóm
   tắt) … chưa đọc toàn văn» cho dòng đã đọc toàn văn và cho xã luận không có tóm tắt, ghi ngày SINH tệp làm ngày rà,
   đếm cả PMID lạc đề vào «n dòng điền tự động», để câu «Không có SR/MA … 5 năm» cạnh một SR/MA trong bảng.
Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g0_tong_hop as GT  # noqa: E402
import g1_design_blocks as G1D  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g1_auto as G1A  # noqa: E402
import run_g3_auto as R3  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402

# ── 1. Độ tươi của gói trước dữ liệu ─────────────────────────────────────────────────────────────────────────────────

def test_loc_do_tuoi_truoc_du_lieu_bo_g5_g9_giu_g0_g4():
    van_de = [
        {"gate": "G5", "kind": "stale", "offending_upstream": ["G1", "G2", "G3"]},
        {"gate": "G10", "kind": "orphan_downstream", "offending_upstream": ["G6", "G7", "G8", "G9"]},
        {"gate": "G10", "kind": "stale", "offending_upstream": ["G5"]},
        {"gate": "G3", "kind": "stale", "offending_upstream": ["G1"]},
        {"gate": "G10", "kind": "stale", "offending_upstream": ["G3", "G5"]},
        {"gate": "G4", "kind": "orphan_downstream", "offending_upstream": ["G3"]},
    ]
    con = G10Q.loc_do_tuoi_truoc_du_lieu(van_de)
    assert con == [van_de[3], van_de[4], van_de[5]], "vấn đề của G0–G4, và của G10 do G0–G4, vẫn chặn"
    assert G10Q.loc_do_tuoi_truoc_du_lieu([]) == []


def _nap_g10_hoan_thien():
    sp = importlib.util.spec_from_file_location("_g10_hoan_thien_luot_sua",
                                                ROOT / "tests" / "test_g10_hoan_thien_20261005.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _lui_moc(tep: Path, giay: float) -> None:
    t = time.time() - giay
    os.utime(tep, (t, t))


def test_goi_truoc_irb_khong_bi_chan_boi_g5_du_thao_cu_nhung_van_chan_g3_cu(tmp_path, monkeypatch):
    H = _nap_g10_hoan_thien()
    study, out, goc = H._de_tai_truoc_irb(tmp_path, monkeypatch)
    assert H._cham10(study, out, goc)["status"] == G10Q.STATUS_READY
    g5 = out / "G5_checkpoint.json"  # G5 dự thảo có từ trước (như C1a 24/10), sinh TRƯỚC G1–G4
    g5.write_text(json.dumps({"gate": "G5", "status": "DRAFT_READY_NEEDS_REAL_DATA"}), encoding="utf-8", newline="\n")
    _lui_moc(g5, 86_400)
    CS.xoa_dem()
    bao = H._cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, H._chua_dat(bao)
    assert H._ck(bao, "G10-AUTO-03")["status"] == "PASS"
    # Đối chứng: một cổng G0–G4 cũ hơn thượng nguồn (G3 trước G1) vẫn chặn gói.
    _lui_moc(out / "G3_checkpoint.json", 2 * 86_400)
    CS.xoa_dem()
    a03 = H._ck(H._cham10(study, out, goc), "G10-AUTO-03")
    assert a03["status"] == "BLOCK" and "'gate': 'G3'" in a03["evidence"], a03


# ── 2. Nhãn công thức DE trong bảng độ nhạy của G3 ──────────────────────────────────────────────────────────────────

def _chay_g3(tmp_path, monkeypatch, study, argv):
    monkeypatch.setattr(R3, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True)
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    with contextlib.redirect_stdout(io.StringIO()):
        R3.main()
    a4 = (d / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
    return next(dong for dong in a4.splitlines() if dong.startswith("Bảng: tỷ lệ ước lượng p"))


_ARGV = ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--cluster-size", "20", "--dropout", "0.15"]


def test_bang_do_nhay_ghi_dung_cong_thuc_de(tmp_path, monkeypatch):
    co_cv = _chay_g3(tmp_path / "a", monkeypatch, "G3-CV", _ARGV + ["--cluster-cv", "0.14"])
    assert "DE = 1.39 (= 1+((CV²+1)×m−1)×ICC, CV = 0.14, m = 20, ICC = 0.02)" in co_cv, co_cv
    deu = _chay_g3(tmp_path / "b", monkeypatch, "G3-DEU", _ARGV)
    assert "DE = 1.38 (= 1+(m−1)×ICC, m = 20, ICC = 0.02)" in deu, deu


# ── 3. A2 của G1 in DE làm tròn ─────────────────────────────────────────────────────────────────────────────────────

def test_cau_co_mau_g1_lam_tron_he_so_thiet_ke(tmp_path):
    (tmp_path / "G3_checkpoint.json").write_text(json.dumps({"n_adjusted": 630, "confirmed_n": 1000,
                                                             "design_effect": 1.38784}), encoding="utf-8",
                                                  newline="\n")
    cau = G1A._cau_co_mau_g3(tmp_path)
    assert "hệ số thiết kế 1.39" in cau and "1.38784" not in cau, cau


# ── 4. Câu «không áp dụng» của hội đồng ─────────────────────────────────────────────────────────────────────────────

def test_ly_do_khong_ap_dung_noi_ro_pham_vi_nhiem_vu(tmp_path):
    study = "HD-CAT-NGANG"
    out = tmp_path / "exports" / study
    dung_g0_g1_da_chot(out, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True)
    CS.xoa_dem()
    hs = HD.ho_so_cong(study, "G2", out)
    t2 = next(n for n in hs["nhiem_vu"] if n["ma"] == "G2-T2")
    assert t2["tinh_trang"] == "khong_ap_dung"
    assert t2["ly_do"].startswith("không áp dụng — nhiệm vụ chỉ dành cho "), t2["ly_do"]
    assert "(thiết kế can thiệp" not in t2["ly_do"].split("—")[0]


# ── 5. Khối thiết kế đánh dấu ô chọn mẫu / thước đo kết hợp từ khoá PI đã khai ────────────────────────────────────────

def test_khoi_thiet_ke_danh_dau_o_chon_mau_va_thuoc_do():
    body = G1D.design_block_body("cross_sectional")
    dong = G1D.dien_tu_quyet_dinh(body, {"sampling_design": ["he_thong", "phan_tang", "cum", "la"],
                                         "association_measures": ["prevalence", "khac:OR chung (MT2)"]}).splitlines()
    i = next(k for k, x in enumerate(dong) if x.startswith("Chọn mẫu:"))
    assert "☑ Hệ thống" in dong[i] and "☐ Toàn bộ" in dong[i] and "☐ Ngẫu nhiên đơn" in dong[i]
    assert "☑ Phân tầng" in dong[i + 1] and "☑ Cụm" in dong[i + 1], "khối tràn sang dòng thụt lề kế tiếp"
    assert dong[i + 1].endswith("(PI đã chốt — gate_params.G1.sampling_design)") and "mã lạ" in dong[i + 1]
    td = next(x for x in dong if x.startswith("Thước đo kết hợp định trước:"))
    assert "☑ tỷ lệ hiện mắc (prevalence)" in td and "☐ prevalence OR" in td and "☐ PR" in td
    assert "☑ khác: OR chung (MT2)" in td
    assert G1D.dien_tu_quyet_dinh(body, {}) == body, "chưa khai thì khối giữ nguyên ô trống"


# ── 6. PHẦN 7 của A2 ────────────────────────────────────────────────────────────────────────────────────────────────

def _a2(out_dir: Path) -> str:
    design = G1A.infer_study_design("descriptive", {}, "hài lòng người bệnh ngoại trú")
    return G1A.generate_g1_artifact("t", "S", "descriptive", design, [], {}, "2026-10-26 10:00",
                                    meta={"gate_params": {"G1": {}}}, out_dir=out_dir)


def test_phan_7_khong_ghi_trang_thai_nguoi_va_dung_voi_thiet_ke_do_chinh_xac(tmp_path):
    (tmp_path / "G3_checkpoint.json").write_text(json.dumps({"hypothesis_type": "descriptive_precision",
                                                             "n_adjusted": 630}), encoding="utf-8", newline="\n")
    (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text("**Phiên bản SAP:** 1.4\n", encoding="utf-8", newline="\n")
    a2 = _a2(tmp_path)
    p7 = a2.split("## PHẦN 7")[1]
    assert "[CHỜ]" not in p7 and "☐ PI/methodologist" not in p7, "tệp sinh trước khi chấm không ghi trạng thái người"
    assert "• PI/methodologist xác nhận thiết kế" in p7 and "python3 tools/g1_quality_gate.py --study S" in p7
    assert "study_readiness.py --study S" in p7 and "PI/methodologist hoàn thiện `study_meta.json`" not in p7
    assert "Chưa có effect size truy nguyên" not in a2 and "☑ Kết cục chính ước lượng theo độ chính xác" in p7
    assert "SAP skeleton 12 mục đã sinh" not in p7 and "SAP chính thức G4 (phiên bản 1.4" in p7
    # Đối chứng: chưa có G3/SAP ⇒ dòng effect size và khung SAP như cũ.
    a2_0 = _a2(tmp_path / "trong")
    assert "Chưa có effect size truy nguyên" in a2_0 and "☑ SAP skeleton 12 mục đã sinh" in a2_0


# ── 7. Sổ A2b ───────────────────────────────────────────────────────────────────────────────────────────────────────

_S2B = "S2B"
_GAP_SR = ("Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên "
           "cứu quan sát")


def _so_a2b(tmp_path: Path, g1: dict | None = None) -> str:
    d = tmp_path / "exports" / _S2B
    d.mkdir(parents=True)
    cp0 = {"study": _S2B, "gate": "G0", "base_query": "q",
           "pubmed_results": {"all_pmids": ["11111111", "22222222"]},
           "danh_muc_doc_bo_sung": ["pmid:33333333", "pmid:44444444", "pmid:55555555"], "research_gaps": [_GAP_SR]}
    (d / "G0_checkpoint.json").write_text(json.dumps(cp0, ensure_ascii=False), encoding="utf-8", newline="\n")
    raw = {"recent": [{"pmid": "11111111", "title": "Bài A", "journal": "J", "year": "2024"},
                      {"pmid": "22222222", "title": "Bài lạc đề", "journal": "J", "year": "2020"}],
           "search_provenance": {"ngay_tra": "2026-10-14T18:22:29"}}
    (d / "G0_pubmed_raw.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8", newline="\n")
    th = {"schema": GT.SCHEMA_TONG_HOP, "ngay_soan": "2026-10-17",
          "sang_loc": [{"pmid": "11111111", "thiet_ke_that": "Cắt ngang", "lien_quan": "truc_tiep",
                        "tom_tat": "Chờ 32 phút (toàn văn, CC BY 4.0)"},
                       {"pmid": "22222222", "thiet_ke_that": "phẫu thuật", "lien_quan": "khong", "tom_tat": "x",
                        "ly_do": "khác chủ đề"}],
          "nguon_bo_sung": [{"pmid": "33333333", "tieu_de": "Xã luận", "thiet_ke_that": "Xã luận (editorial) — không "
                             "có tóm tắt trên PubMed", "lien_quan": "gian_tiep", "tom_tat": "Bàn về hướng dẫn"},
                            {"pmid": "44444444", "tieu_de": "SR", "thiet_ke_that": "Tổng quan hệ thống (35 nghiên cứu)",
                             "lien_quan": "gian_tiep", "tom_tat": "Hài lòng thấp với chờ"},
                            {"pmid": "55555555", "tieu_de": "Bài đọc", "thiet_ke_that": "Cắt ngang", "lien_quan":
                             "truc_tiep", "tom_tat": "Chờ 26–175 phút — đọc toàn văn 2026-10-17."}]}
    (d / GT.TEP_TONG_HOP.format(study=_S2B)).write_text(json.dumps(th, ensure_ascii=False), encoding="utf-8",
                                                          newline="\n")
    meta = {"gate_params": {"G1": g1 or {}}}
    G1Q.build_supporting_artifacts(study=_S2B, topic="T", out_dir=d, design={"primary": "Cắt ngang"},
                                   g0_checkpoint=cp0, effects=[], meta=meta, generated_at="2026-10-26 10:00")
    return (d / f"G1_A2b_EVIDENCE_LEDGER_{_S2B}.md").read_text(encoding="utf-8")


def _dong(so: str, ma: str) -> str:
    return next(x for x in so.splitlines() if x.startswith(f"| {ma} "))


def test_so_a2b_ghi_dung_nguon_doc_ngay_tim_so_dong_va_pham_vi(tmp_path):
    so = _so_a2b(tmp_path, {"reviewed_at": "2026-10-14T19:21:13+07:00"})
    a = _dong(so, "PMID:11111111")
    assert "(theo toàn văn)" in a and "ĐÃ đọc toàn văn (ghi ở sàng lọc G0)" in a and "(theo tóm tắt)" not in a
    b = _dong(so, "PMID:55555555")
    assert "ĐÃ đọc toàn văn 2026-10-17" in b and "chưa đọc toàn văn" not in b
    x = _dong(so, "PMID:33333333")
    assert "(theo tóm tắt)" not in x and "không có tóm tắt" in x and "tiêu đề + nội dung bài" in x
    assert "chưa đọc toàn văn" in _dong(so, "PMID:44444444"), "không có nhãn đọc toàn văn ⇒ giữ mặc định thận trọng"
    assert "Ngày tìm cuối (PubMed, truy vấn G0): 2026-10-14" in so and "ngày sinh sổ: 2026-10-26" in so
    assert "Cột **Metadata**: 1 dòng điền TỰ ĐỘNG" in so, "PMID lạc đề không được đếm vào số dòng điền"
    gap = next(x for x in so.splitlines() if x.startswith("- Không có SR/MA"))
    assert "phạm vi: chỉ các nhánh tìm PubMed của truy vấn G0" in gap and "PMID:44444444" in gap
    assert "SAU lần PI xác nhận G1 (2026-10-14)" in so
    assert "Việc còn lại của sổ" in so


def test_so_a2b_pi_xac_nhan_sau_khi_soan_thi_khong_canh_bao(tmp_path):
    so = _so_a2b(tmp_path, {"reviewed_at": "2026-10-27T09:00:00+07:00"})
    assert "SAU lần PI xác nhận G1" not in so


def test_dong_luc_muc_tieu_phu_lam_tron_he_so_thiet_ke():
    kq = {"muc_tieu": "MT2", "phan_tich": "logistic thứ tự", "n_danh_nghia": 1000, "n_phan_tich": 850,
          "alpha": 0.05, "power": 0.8, "buoc": 15, "don_vi": "phút", "phoi_nhiem": "chờ", "design_effect": 1.38784,
          "n_hieu_dung": 612.5, "khoang_or_hieu_dung": [1.09, 1.2], "khoang_or_chieu_giam_hieu_dung": [0.84, 0.92],
          "khoang_or_danh_nghia": [1.07, 1.15]}
    dong = R3.dong_luc_muc_tieu_phu(kq)
    assert "÷ DE 1.39)" in dong and "1.38784" not in dong, dong
