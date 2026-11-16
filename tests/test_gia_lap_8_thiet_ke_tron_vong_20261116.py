"""Giả lập trọn vòng 8 thiết kế (bác sĩ 16/11/2026: «Hãy hoàn thiện các đề tài giả lập… sau giả lập hãy hoàn thiện một
cách hoàn chỉnh hệ thống»). Mỗi phép thử khoá MỘT lỗi hệ thống đo được khi đưa 7 thiết kế ngoài thuần tập đi G2→G6:

G2 — ICF để ô mẫu chung PI phải tự xoá (mọi thiết kế có ICF bị từ chối ký); PROSPERO hỏi lại PICO đã chốt; PI ghim
     «không bắt buộc đăng ký» cho đề tài tiến cứu ⇒ cổng READY nhưng approve_gate từ chối (G2-AUTO-11).
G4 — ô «KQ chính» của chứng chỉ khoá chép lệch §2; cắt ngang MÔ TẢ in «hồi quy logistic» ở §4.
G5 — tổng quan–gộp mở đầu bằng khoá đã duyệt `study_id` nhưng từ điển chèn thêm record_id (V7); kịch bản báo cáo chất
     lượng sinh ra LỖI CÚ PHÁP; biến tính toán (calc, vd FIB-4) bị đòi «bắt buộc» lúc làm sạch/khoá; cổng tiếp nhận chặn
     cột ngày đã khai trong từ điển (bộ làm sạch/khoá thì miễn).
G6 — cắt ngang MÔ TẢ sinh khuôn logistic, G6-AUTO-09 không nhận họ «ước lượng tỷ lệ».
Bộ giả lập — sinh giá trị ngoài khoảng đã khai; kết cục «kiểm soát» mâu thuẫn trị số huyết áp.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402

# ── G2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_g2_prospero_lay_pico_da_chot_khong_de_o_mau_chung():
    import g2_quality_gate as G2Q
    import run_g2_auto as G2

    meta = {"gate_params": {
        "G0": {"population": "Người ĐTĐ típ 2", "intervention": "SGLT2", "comparison": "Giả dược",
               "primary_outcome": "Nhập viện vì suy tim"},
        "G1": {"research_question": "SGLT2 có giảm nhập viện vì suy tim?", "information_sources": ["PubMed", "Embase"],
               "inclusion_criteria": ["Thử nghiệm ngẫu nhiên có đối chứng", "Người trưởng thành"],
               "secondary_outcomes": ["Tử vong tim mạch"], "study_period": "2027-03 đến 2027-12"}}}
    khoi = G2._khoi_prospero(meta)
    for chuoi in ("SGLT2 có giảm nhập viện vì suy tim?", "PubMed; Embase", "Thử nghiệm ngẫu nhiên có đối chứng",
                  "RoB 2", "Start date: 2027-03", "Expected completion: 2027-12", "Secondary — Tử vong tim mạch"):
        assert chuoi in khoi, chuoi
    con = " ".join(G2Q.unresolved_critical_placeholders(khoi))
    for o_mau in ("topic in English", "RCT / Observational", "RoB 2 / ROBINS-I", "sẽ bổ sung sau"):
        assert o_mau not in con and o_mau not in khoi, o_mau


@pytest.mark.parametrize("che_do, bat_buoc, ky_vong", [
    ("PROSPECTIVE_NEW_PARTICIPANTS", False, "BLOCK"),
    ("PROSPECTIVE_NEW_PARTICIPANTS", True, "PASS"),
    ("RETROSPECTIVE_SECONDARY_DATA", False, "PASS"),
])
def test_g2_auto_11_dang_ky_khop_nghia_vu(tmp_path, che_do, bat_buoc, ky_vong):
    from test_g2_quality_gate import _evaluate, _meta, _package

    meta = _meta()
    meta["gate_params"].setdefault("G2", {}).update({"recruitment_mode": che_do, "registration_required": bat_buoc})
    report = _evaluate(tmp_path, _package(), ledger=False, meta=meta)
    dong = next(c for c in report["automatic_criteria"] if c["id"] == "G2-AUTO-11")
    assert dong["status"] == ky_vong, dong


# ── G4 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_g4_chung_chi_khoa_chep_dung_ket_cuc_chinh_par_2():
    import run_g4_auto as G4

    sap = ("- **Kết cục chính:** Trải nghiệm khi bắt đầu tiêm insulin *(điền sẵn từ quyết định đã chốt — thống kê "
           "viên/PI sửa nếu cần)*  \n\n║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]                 ║\n")
    moi = G4._dong_bo_chung_chi(sap)
    assert "║ KQ chính  : Trải nghiệm khi bắt đầu tiêm insulin ║" in moi
    con_trong = ("- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: …]  \n"
                 "║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]       ║")
    assert G4._dong_bo_chung_chi(con_trong) == con_trong  # §2 còn trống ⇒ giữ ô cho người điền


def test_g4_cat_ngang_mo_ta_phuong_phap_la_uoc_luong_ty_le():
    import run_g4_auto as G4

    def sap(**kw):
        return G4.generate("ZZ-CN", "Kiểm soát huyết áp", "cross_sectional", "Cắt ngang", "STROBE", 400, 0.05, 0.8,
                           None, None, "2026-11-16", g3={"precision": 0.05, "prevalence": 0.5}, **kw)
    assert "Ước lượng tỷ lệ + KTC 95% (Wilson)" in sap()
    phan_tich = G4.generate("ZZ-CN", "x", "cross_sectional", "Cắt ngang", "STROBE", 400, 0.05, 0.8, 1.5, "OR",
                            "2026-11-16", g3={})
    assert "Ước lượng tỷ lệ" not in phan_tich  # cắt ngang PHÂN TÍCH (có thước đo hiệu ứng) giữ khuôn hồi quy


# ── G5 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def _bo_bien_csv(thu_muc: Path, dong_dau: str) -> None:
    import run_g5_auto as G5

    cot = list(G5._BO_BIEN_COT_BAT_BUOC)
    with (thu_muc / G5.BO_BIEN_RIENG_TEN_FILE).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        for ten, kieu, kiem in ((dong_dau, "text", ""), ("n_can_thiep", "text", "integer")):
            w.writerow({**{c: "" for c in cot}, "Variable / Field Name": ten, "Form Name": "trich_xuat",
                        "Field Type": kieu, "Field Label": ten, "Text Validation Type OR Show Slider Number": kiem})


def test_g5_giu_khoa_ban_ghi_da_duyet_o_truong_dau(tmp_path):
    import run_g5_auto as G5

    _bo_bien_csv(tmp_path, "study_id")
    rows = G5.nap_bo_bien_rieng(tmp_path, "ZZ")
    assert [r[0] for r in rows] == ["study_id", "n_can_thiep"]  # không chèn record_id trước khoá đã duyệt
    (tmp_path / G5.BO_BIEN_RIENG_TEN_FILE).unlink()
    _bo_bien_csv(tmp_path, "tuoi")
    assert G5.nap_bo_bien_rieng(tmp_path, "ZZ")[0][0] == "record_id"  # chưa có khoá ⇒ vẫn thêm record_id


def test_g5_kich_ban_sinh_ra_chay_duoc_va_kiem_trung_theo_truong_dau():
    import run_g5_auto as G5

    rows = [("study_id", "f", "", "text", "Mã", "", "", "", "", "", "y", "", "", ""),
            ("n_can_thiep", "f", "", "text", "n", "", "", "integer", "0", "99999", "y", "", "", "")]
    for ham in (G5.gen_data_cleaning_script, G5.gen_data_quality_report_script):
        ma = ham("ZZ", "sr_ma", rows)
        compile(ma, ham.__name__, "exec")  # khuôn báo cáo chất lượng từng có newline="<xuống dòng thật>" ⇒ SyntaxError
        assert "ID_COL = 'study_id'" in ma and '"record_id" in df.columns' not in ma


def test_g5_bien_tinh_toan_khong_bi_doi_bat_buoc_luc_lam_sach_va_khoa(tmp_path):
    import clean_research_dataset as CRD
    import g5_quality_gate as G5Q

    td = tmp_path / "dict.csv"
    hang = [{"Variable / Field Name": "record_id", "Form Name": "f", "Field Type": "text", "Field Label": "Mã",
             "Required Field?": "y"},
            {"Variable / Field Name": "ast", "Form Name": "f", "Field Type": "text", "Field Label": "AST",
             "Text Validation Type OR Show Slider Number": "integer", "Required Field?": "y"},
            {"Variable / Field Name": "fib4", "Form Name": "f", "Field Type": "calc", "Field Label": "FIB-4",
             "Choices, Calculations, OR Slider Labels": "[ast]/2", "Required Field?": "y"}]
    cot = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
           "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
           "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
           "Required Field?"]
    with td.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        for h in hang:
            w.writerow({c: h.get(c, "") for c in cot})
    du = G5Q._read_redcap_dictionary(td)
    assert "ast" in du["required_names"] and "fib4" not in du["required_names"]
    dl = tmp_path / "dl.csv"
    dl.write_text("record_id,ast\nR0001,30\nR0002,41\n", encoding="utf-8", newline="\n")
    out = tmp_path / "exports" / "ZZ-CALC"
    out.mkdir(parents=True)
    kq = CRD.clean_dataset("ZZ-CALC", dl, exports_root=tmp_path / "exports", dictionary_path=td)
    loai = json.dumps(kq, ensure_ascii=False)
    assert "missing_required_column" not in loai, loai[:600]


def test_tiep_nhan_mien_cot_ngay_da_khai_trong_tu_dien(tmp_path):
    import import_real_dataset as RDI

    td = tmp_path / "dict.csv"
    td.write_text("Variable / Field Name,Form Name,Field Type,Field Label,Text Validation Type OR Show Slider Number\n"
                  "record_id,f,text,Mã,\nngay_ngau_nhien,f,text,Ngày ngẫu nhiên hoá,date_dmy\n",
                  encoding="utf-8", newline="\n")
    assert RDI.cot_ngay_tu_dien(td) == frozenset({"ngay_ngau_nhien"})
    assert RDI.cot_ngay_tu_dien(tmp_path / "khong_co.csv") == frozenset()
    dl = tmp_path / "dl.csv"
    dl.write_text("record_id,ngay_ngau_nhien\nR0001,2027-03-02\nR0002,2027-04-18\n", encoding="utf-8", newline="\n")
    chan = RDI.import_dataset("ZZ-NGAY", dl, exports_root=tmp_path / "e1")
    assert chan["status"] == "BLOCKED_PII_OR_UNSAFE"  # không có từ điển ⇒ quét nghiêm như cũ
    qua = RDI.import_dataset("ZZ-NGAY", dl, exports_root=tmp_path / "e2", exempt_date_columns=RDI.cot_ngay_tu_dien(td))
    # chốt «SAP phải khoá trước khi nạp» độc lập vẫn chạy — chỉ khẳng định không còn chặn vì cột NGÀY đã khai
    assert not [i for i in qua["pii_scan"]["issues"] if str(i.get("type")).startswith("value_pii:date")]
    assert [i for i in chan["pii_scan"]["issues"] if str(i.get("type")).startswith("value_pii:date")]


# ── G6 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("dong, ky_vong", [
    ("Ước lượng tỷ lệ + KTC 95% (Wilson); tỷ lệ theo phân nhóm tiền định ở §7", True),
    ("Hồi quy logistic/tuyến tính", False),
    ("Hồi quy logistic thứ tự có trọng số; KTC Wilson trên n hiệu dụng", False),
])
def test_phuong_phap_la_ty_le(dong, ky_vong):
    assert GC.phuong_phap_la_ty_le(dong) is ky_vong


def test_g6_cat_ngang_mo_ta_sinh_khuon_ty_le_va_cong_nhan_ho_ty_le(tmp_path):
    import g6_quality_gate as G6Q
    import run_g6_auto as G6

    (tmp_path / "G4_A5_SAP_FINAL_ZZ.md").write_text(
        "### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Ước lượng tỷ lệ + KTC 95% (Wilson)  \n\n### §5 HIỆP BIẾN\n",
        encoding="utf-8", newline="\n")
    assert GC.sap_declares_proportion(tmp_path, "ZZ")
    r03 = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", {"exposure": "exposure", "outcome": "kiem_soat_ha",
                                                     "covariates": [], "mo_ta_ty_le": True}, 400, 0.05, 0.8, None, None)
    assert "BinomCI" in r03 and "glm(" not in r03
    bat = "\n".join(d[2:] if d.startswith("# fit_") or d.startswith("# df <-") else d for d in r03.splitlines())
    assert G6Q._ho_mo_hinh_script("\n".join(G6Q._dong_thi_hanh(bat)))[0] == "proportion"
    assert "proportion" in G6Q._ho_mo_hinh_sap("- **Phương pháp:** Ước lượng tỷ lệ + KTC 95% (Wilson)")


# ── Bộ giả lập ────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_gia_lap_sinh_du_lieu_trong_khoang_da_khai_va_khong_tu_mau_thuan():
    import gia_lap_dinh_ky as GL
    import gia_lap_tron_vong as TV

    kb = GL.KICH_BAN["cat_ngang_mo_ta"]
    hang = TV.sinh_du_lieu("cross_sectional", kb["bien_so"], {"prevalence": 0.5}, 300)
    assert all(60 <= r["ha_tt_tb"] <= 260 for r in hang)
    assert all((r["ha_tt_tb"] < 140) == (r["kiem_soat_ha"] == 1) for r in hang)
    rct = TV.sinh_du_lieu("rct", GL.KICH_BAN["rct_nhi_phan"]["bien_so"], {"p0": 0.4, "effect_size": 1.4}, 300)
    assert all((r["ha_tt_t6"] < 140) == (r["kiem_soat_t6"] == 1) for r in rct)
    assert json.dumps(hang[0], ensure_ascii=False)


def test_g4_generate_chung_chi_khoa_dong_bo_voi_par_2():
    """Ở mức bộ sinh: SAP có §2 điền từ khung đã chốt ⇒ chứng chỉ khoá in đúng chuỗi đó (không còn ô hỏi lại)."""
    import run_g4_auto as G4

    sap = G4.generate("ZZ-CC", "x", "cohort", "Thuần tập", "STROBE", 400, 0.05, 0.8, 1.3, "RR", "2026-11-16", g3={},
                      khung={"ket_cuc": {"name": "Gãy xương", "measure": "phim X-quang", "timepoint": "3 năm"}})
    assert "║ KQ chính  : Gãy xương; đo bằng phim X-quang; thời điểm: 3 năm ║" in sap
    assert "[CẦN BÁC SĨ ĐIỀN — từ SAP §2]" not in sap


# ── G6: quy ước «◆ MÔ HÌNH CHÍNH (SAP §4)» + nhóm con lọc theo hiệp biến ─────────────────────────────────────────────


@pytest.mark.parametrize("thiet_ke, v_them", [
    ("case_control", {}), ("diagnostic", {"ref_standard": "xo_hoa", "index_test": "fib4"}), ("prediction", {}),
    ("sr_ma", {}), ("cross_sectional", {"mo_ta_ty_le": True}),
])
def test_g6_moi_khuon_danh_dau_dung_mot_dong_mo_hinh_chinh(thiet_ke, v_them):
    import gia_lap_tron_vong as TV
    import run_g6_auto as G6

    v = {"exposure": "phoi", "outcome": "kc", "covariates": ["tuoi"], "time_col": "t", **v_them}
    r03 = G6.R_ANALYSIS_MAP_FUNC(thiet_ke, v, 400, 0.05, 0.8, 1.5, "OR")
    dong = [d for d in r03.splitlines() if "◆ MÔ HÌNH CHÍNH (SAP §4)" in d]
    assert len(dong) == 1 and dong[0].startswith("# "), dong
    bat = TV.TronVong.DONG_MO_HINH_CHINH.sub(r"\1", r03)  # vai thống kê viên bật đúng dòng có dấu
    assert any("◆ MÔ HÌNH CHÍNH" in d and not d.startswith("#") for d in bat.splitlines())


def test_g6_nhan_hiep_bien_khong_ap_dung_cho_tong_hop_va_dinh_tinh():
    import run_g6_auto as G6

    assert G6._nhan_hiep_bien([], "sr_ma").startswith("Không áp dụng")
    assert G6._nhan_hiep_bien([], "qualitative").startswith("Không áp dụng")
    assert G6._nhan_hiep_bien([], "cohort") == "[xem SAP §5]"
    assert G6._nhan_hiep_bien(["tuoi", "gioi"], "sr_ma") == "tuoi, gioi"


def test_bo_may_loai_hiep_bien_hang_sau_loc_nhom_con(tmp_path, monkeypatch):
    """Nhóm con «gioi == 1» với hiệp biến phân loại «gioi»: trước đây DỪNG («chỉ có 1 mức»); nay loại khỏi mô hình nhóm
    con và ghi vào đặc tả (SPSS/R kiểm chéo cùng mô hình). Không lọc thì giữ nguyên hành vi cũ."""
    import run_stats_analysis as RSA

    src = Path(RSA.__file__).read_text(encoding="utf-8")
    i = src.index("hang_sau_loc: list = []")
    khoi = src[i:src.index("# 1c. HIỆP BIẾN PHÂN LOẠI", i)]
    assert "if args.loc.strip():" in khoi and "nunique() <= 1" in khoi
    assert '"hiep_bien_hang_sau_loc": hang_sau_loc' in src


# ── G6.5 → G10: bộ giả lập đọc ĐÚNG thước đo của từng thiết kế (16/11/2026 — trước chỉ thuần tập đi hết G10) ──────────
def _tom_tat_theo_thiet_ke() -> dict:
    """Tóm tắt G6 tổng hợp theo đúng khoá engine ghi — phần đặc thù dựng bằng chính hàm của mô-đun phân tích."""
    import phan_tich_thiet_ke_dac_thu as P

    nhi_phan = {"outcome_type": "binary", "group_1": {"n": 100, "events": 67, "pct": 67.0},
                "group_0": {"n": 118, "events": 57, "pct": 48.3}, "or_crude": 2.173, "ci_95": [1.252, 3.772],
                "risk_diff": 0.1869, "risk_diff_ci_95": [0.058, 0.3159], "p_value": 0.0083}
    chan = P.chan_doan([{"y": y, "x": x} for y, x in ((1, 3.0), (1, 2.9), (1, 1.0), (0, 2.8), (0, 1.0), (0, 0.5),
                                                      (0, 0.2), (1, 2.7))], "y", "x", 2.67)
    du_bao = P.du_bao([{"y": int(i % 3 == 0 or i > 25), "t": float(i), "u": float((i * 7) % 11)} for i in range(40)],
                      "y", ["t", "u"])
    gop = P.gop([{"s": "A", "a": 10, "n1": 100, "c": 20, "n0": 100},
                 {"s": "B", "a": 15, "n1": 200, "c": 30, "n0": 200}], "s", "a", "n1", "c", "n0")
    dinh_tinh = P.dinh_tinh([{"c": "Gia đình hỗ trợ"}] * 3 + [{"c": "Sợ hạ đường huyết"}] * 2, "c")
    return {
        "rct_nhi_phan": {"n_total": 218, "dac_ta_phan_tich": {"group": "nhom"}, "primary_outcome": nhi_phan,
                         "poisson_pr": {"n_bien_co": 124,
                                        "tho": [{"variable": "nhom", "PR": 1.387, "CI_95": [1.1, 1.749], "p": 0.0057}],
                                        "results": [{"variable": "nhom", "PR_adj": 1.39, "CI_95": [1.103, 1.751],
                                                     "p": 0.0053}]}},
        "cat_ngang_mo_ta": {"n_total": 428, "ty_le": [{"ty_le": 0.486, "CI_95_wilson_doc_lap": [0.439, 0.5332],
                                                       "so_su_kien": 208, "n": 428}]},
        "benh_chung": {"n_total": 577, "dac_ta_phan_tich": {"group": "nsaid"},
                       "primary_outcome": {k: v for k, v in nhi_phan.items() if not k.startswith("risk_diff")},
                       "multivariate": {"results": [{"variable": "nsaid", "OR_adj": 1.667, "CI_95": [1.087, 2.557],
                                                     "p": 0.0192}]}},
        "chan_doan": {"n_total": 8, "dac_thu": chan},
        "mo_hinh_du_bao": {"n_total": 40, "dac_thu": du_bao},
        "tong_quan_gop": {"n_total": 2, "dac_thu": gop},
        "dinh_tinh": {"n_total": 5, "dac_thu": dinh_tinh},
    }


def _bo_doc(tmp_path, tom: dict):
    import gia_lap_tron_vong as TV

    class _O:  # chỉ các thuộc tính _uoc_luong/_gia_tri_ket_qua dùng — không dựng sandbox repo
        THUOC_DO = TV.TronVong.THUOC_DO
        _so_vn = staticmethod(TV.TronVong._so_vn)
        _uoc_luong = TV.TronVong._uoc_luong
        _gia_tri_ket_qua = TV.TronVong._gia_tri_ket_qua
        _gia_tri_kinh_te = TV.TronVong._gia_tri_kinh_te  # 16/11/2026: _gia_tri_ket_qua gộp khoá lời văn kinh tế

    o = _O()
    o.out = tmp_path
    o.kb = {}  # kịch bản không có phân tích kinh tế ⇒ _gia_tri_kinh_te trả {}
    (tmp_path / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    return o


@pytest.mark.parametrize("ma, lay, uoc, nguon", [
    ("rct_nhi_phan", "pr_hieu_chinh", 1.39, "G6_table4_poisson_pr.txt"),
    ("rct_nhi_phan", "hieu_so_nguy_co", 0.1869, "G6_table2_main_outcome.txt"),
    ("cat_ngang_mo_ta", "ty_le", 48.6, "G6_table1b_proportions.txt"),
    ("benh_chung", "or_hieu_chinh", 1.667, "G6_table4_multivariate.txt"),
    ("chan_doan", "do_nhay", 0.75, "G6_analysis_summary.json"),
    ("tong_quan_gop", "rr_gop", None, "G6_analysis_summary.json"),
    ("dinh_tinh", "chu_de_1", 0.6, "G6_analysis_summary.json"),
])
def test_bo_doc_uoc_luong_dung_khoa_va_tep_nguon_tung_thiet_ke(tmp_path, ma, lay, uoc, nguon):
    o = _bo_doc(tmp_path, _tom_tat_theo_thiet_ke()[ma])
    u = o._uoc_luong(lay, "G6")
    assert u and u["nguon"] == nguon and u["ci"][0] <= u["uoc"] <= u["ci"][1]
    if uoc is not None:
        assert abs(u["uoc"] - uoc) < 1e-9
    assert o._uoc_luong("hieu_so_nguy_co", "G6") is None or ma == "rct_nhi_phan"  # bệnh–chứng KHÔNG có hiệu số


def test_moi_cho_giu_trong_ho_so_sau_g6_deu_co_gia_tri(tmp_path):
    """Lời văn hồ sơ 7 thiết kế chỉ dùng chỗ giữ mà bộ đọc SINH RA cho đúng thiết kế đó (chỗ giữ sai ⇒ KeyError giữa
    lượt chạy, tức hồ sơ không bao giờ tới G7)."""
    import string

    import gia_lap_ho_so_sau_g6 as HS

    tom = _tom_tat_theo_thiet_ke()
    for ma, hs in HS.ho_so_sau_g6().items():
        d = tmp_path / ma
        d.mkdir()
        gt = _bo_doc(d, tom[ma])._gia_tri_ket_qua()
        dg = hs["dien_giai"]
        gt.update({f"muc_{i}": dg[f"muc_{i}"].format(**gt) for i in range(2, 6)})
        van = ([dg[f"muc_{i}"] for i in range(2, 6)] + [hs["phan_bien_G8"]["ly_do"]]
               + [v for _m, v in hs["tra_loi_G7"]] + [r[k] for r in dg["bang"] for k in ("ket_cuc", "y_nghia")])
        for t in van:
            thieu = {f for _l, f, _s, _c in string.Formatter().parse(t) if f} - set(gt)
            assert not thieu, f"{ma}: chỗ giữ không có giá trị {thieu} trong «{t[:60]}…»"
        for r in dg["bang"]:  # mọi dòng bảng diễn giải đọc được ước lượng từ tóm tắt cùng khuôn
            if r["gate"] == "G6":
                assert _bo_doc(d, tom[ma])._uoc_luong(r["lay"], "G6"), f"{ma}: {r['lay']}"
        assert hs["tac_gia_G7"] and hs["dac_ta_G10"]["summary"] and hs["tham_so_G8"]["ai_use_declared"] is True
