"""Giả lập DỮ LIỆU chân thực trên khung thật BTM (17/11/2026, bác sĩ: «giả lập với dữ liệu để hoàn thiện toàn diện…
chân thực và chính xác») — các lỗi hệ mà dữ liệu sinh đúng theo từ điển REDCap làm lộ ra:

1. Trường calc (REDCap tự tính, không nhập tay) vắng trong tệp Excel/SPSS ⇒ mọi Branching Logic dựa trên nó
   («[du_tieu_chuan] = '1'» — cả phần B–F của phiếu BTM) «không đánh giá được» ở 464/464 hàng ⇒ bộ làm sạch mở
   19.952 query thiếu oan cho hồ sơ bị loại, công cụ nhập Excel thì bỏ qua câu bắt buộc trống. Nay tính lại calc theo
   đúng công thức của từ điển (`nhap_lieu_excel.tinh_calc`), chỉ cho logic.
2. Câu chọn nhiều BẮT BUỘC xuất thành `<biến>___<mã>` — không bao giờ có cột tên gốc ⇒ bộ làm sạch mở
   «missing_required_column» và cổng G5-AUTO-07b chặn mãi (BTM có 5 câu như vậy).
3. Bộ sinh dữ liệu dùng chính bộ đánh giá của hệ (bỏ eval), trích tiếp tới khi đủ N hồ sơ đủ tiêu chuẩn, phân bố có
   điều kiện; bộ giả lập ghi MỌI trang biểu mẫu của mẫu Excel nhiều trang và không ghi đè phiếu chủ nhiệm soạn.

Từ điển + dữ liệu đều GIẢ (không PII). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import clean_research_dataset as CLEAN  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import nhap_lieu_excel as N  # noqa: E402
import sinh_du_lieu_redcap as SR  # noqa: E402

STUDY = "zz-calc-thu"
COT_TD = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip
DU = "[du_tc] = '1'"
CT_DU = "if([mo_duoc] = '1' and [tc_tuoi] = '1', 1, 0)"
# ten, form, loai, lua_chon/cong_thuc, kiem_tra, min, max, nhanh, bat_buoc
TRUONG = [
    ("record_id", "sang_loc", "text", "", "", "", "", "", "y"),
    ("mo_duoc", "sang_loc", "yesno", "", "", "", "", "", "y"),
    ("tc_tuoi", "sang_loc", "yesno", "", "", "", "", "[mo_duoc] = '1'", "y"),
    ("du_tc", "sang_loc", "calc", CT_DU, "", "", "", "", "n"),
    ("tuoi", "chung", "text", "", "integer", "18", "110", DU, "y"),
    ("can_nang", "chung", "text", "", "number", "30", "200", DU, "y"),
    ("chieu_cao", "chung", "text", "", "number", "120", "210", DU, "y"),
    ("bmi", "chung", "calc", "round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)", "", "", "", DU, "n"),
    ("thuoc", "thuoc", "checkbox", "1, Metformin | 2, SGLT2i | 0, Không có", "", "", "", DU, "y"),
]
TIEU_DE = ["record_id", "mo_duoc", "tc_tuoi", "tuoi", "can_nang", "chieu_cao", "thuoc___1", "thuoc___2", "thuoc___0"]


def _tu_dien(p: Path, truong=TRUONG) -> Path:
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_TD, lineterminator="\n")
        w.writeheader()
        for ten, form, loai, lc, kt, mn, mx, nh, bb in truong:
            r = dict.fromkeys(COT_TD, "")
            r.update({COT_TD[0]: ten, COT_TD[1]: form, COT_TD[3]: loai, COT_TD[4]: ten, COT_TD[5]: lc,
                      COT_TD[7]: kt, COT_TD[8]: mn, COT_TD[9]: mx, COT_TD[11]: nh, COT_TD[12]: bb})  # fmt: skip
            w.writerow(r)
    return p


def _csv(p: Path, tieu_de: list[str], hang: list[list[str]]) -> Path:
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows(hang)
    return p


def _du(ma: str, **sua) -> list[str]:
    """Hồ sơ đủ tiêu chuẩn, nhập đủ."""
    h = {"record_id": ma, "mo_duoc": "1", "tc_tuoi": "1", "tuoi": "61", "can_nang": "62", "chieu_cao": "158",
         "thuoc___1": "1", "thuoc___2": "0", "thuoc___0": "0"}  # fmt: skip
    h.update(sua)
    return [h[k] for k in TIEU_DE]


def _loai(ma: str, **sua) -> list[str]:
    """Hồ sơ không mở được: phần sau trống, ô chọn nhiều ghi 0 (quy ước REDCap) — KHÔNG có cột du_tc (calc)."""
    return _du(ma, **{"mo_duoc": "0", "tc_tuoi": "", "tuoi": "", "can_nang": "", "chieu_cao": "", "thuoc___1": "0",
                      **sua})


def _lam_sach(tmp_path: Path, hang, tieu_de=TIEU_DE, truong=TRUONG) -> dict:
    return CLEAN.clean_dataset(
        STUDY, _csv(tmp_path / "du_lieu.csv", tieu_de, hang),
        dictionary_path=_tu_dien(tmp_path / "tu_dien.csv", truong), exports_root=tmp_path / "exports",
    )  # fmt: skip


def _query(rp: dict, tmp_path: Path) -> list[dict]:
    with open(tmp_path / "exports" / STUDY / rp["query_log"], encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["status"] == "open"]


# ───────────────────────────── tinh_calc (bộ đánh giá dùng chung) ─────────────────────────────


@pytest.mark.parametrize(
    ("cong_thuc", "dong", "mong"),
    [
        (CT_DU, {"mo_duoc": "1", "tc_tuoi": "1"}, "1"),
        (CT_DU, {"mo_duoc": "1", "tc_tuoi": "0"}, "0"),
        (CT_DU, {"mo_duoc": "0", "tc_tuoi": ""}, "0"),  # ô trống so chuỗi: '' = '1' sai (như REDCap)
        ("[a] / ([b] * [b])", {"a": "70", "b": "2"}, "17.5"),
        ("[a] + [b]", {"a": "2", "b": "3"}, "5"),  # số nguyên không kèm «.0»
        ("[a] + [b]", {"a": "", "b": "1"}, ""),  # NaN của REDCap ⇒ ô trống
        ("if([a] > 1, if([b] = 'x', 'hai', 'mot'), 'khong')", {"a": "2", "b": "x"}, "hai"),
        ("if([a] = 'x,y', 'p,q', 'r')", {"a": "x,y"}, "p,q"),  # phẩy trong chuỗi không tách đối số
        ("IF([a] = '1', 1, 0)", {"a": "1"}, "1"),
    ],
)
def test_tinh_calc_dung_ngu_nghia_redcap(cong_thuc, dong, mong):
    assert N.tinh_calc(cong_thuc, dong) == mong


@pytest.mark.parametrize(
    ("cong_thuc", "doan"),
    [
        ("round([a], 1)", "round"),
        ("datediff([d1], [d2], 'd')", "datediff"),
        ("if([a] = '1', 1)", "3 đối số"),
        ("if([a] = '1', 1, 0) + 2", "thừa"),
        ("if([a] = '1', 1, 0", "ngoặc"),
        ("[vang] + 1", "không có trong dữ liệu"),
        ("", "rỗng"),
    ],
)
def test_tinh_calc_ngoai_tap_con_khong_bao_gio_doan(cong_thuc, doan):
    with pytest.raises(N.LogicKhongHo, match=doan):
        N.tinh_calc(cong_thuc, {"a": "1"})


def test_calc_can_cho_logic_chi_giu_calc_duoc_tham_chieu_ke_ca_gian_tiep():
    ds = [("a", "[x]"), ("bmi", "round([y], 1)"), ("c", "[a] + 1")]
    assert N.calc_can_cho_logic(ds, ["[c] = '2'", "", "[z(1)] = '1'"]) == [("a", "[x]"), ("c", "[a] + 1")]
    assert N.calc_can_cho_logic(ds, ["[tuoi] > 1"]) == []


def test_dong_kem_calc_giu_gia_tri_ban_xuat_redcap_va_bao_loi_tung_truong():
    ds = [("k", "if([x] = '1', 1, 0)"), ("k2", "[k] * 2"), ("k3", "[vang] + 1")]
    dong, loi = N.dong_kem_calc({"x": "1"}, ds)
    assert (dong["k"], dong["k2"]) == ("1", "2") and set(loi) == {"k3"}
    dong, _ = N.dong_kem_calc({"x": "1", "k": "0"}, ds)  # ô calc đã có (bản xuất REDCap) ⇒ giữ nguyên
    assert (dong["k"], dong["k2"]) == ("0", "0")


# ───────────────────────────── bộ làm sạch ─────────────────────────────


def test_nhanh_dua_tren_calc_vang_cot_danh_gia_duoc_khong_query_oan(tmp_path):
    rp = _lam_sach(tmp_path, [_du("B01"), _du("B02"), _loai("B03"), _loai("B04")])
    q = _query(rp, tmp_path)
    assert q == [], q
    nh = rp["branching_logic"]
    assert nh["calc_tinh_lai"] == ["du_tc"]  # bmi (round, không nhánh nào tham chiếu) KHÔNG cần tính
    assert nh["khong_danh_gia_duoc"] == {} and nh["calc_khong_tinh_duoc"] == {}
    # 2 hồ sơ loại × (tuoi, can_nang, chieu_cao) + tc_tuoi (mo_duoc = 0) = 8 ô trống đúng do nhánh ẩn
    assert nh["required_missing_suppressed"] == 8
    assert rp["ready_for_lock"] is True


def test_ho_so_du_tieu_chuan_bo_trong_van_la_thieu_va_ho_so_loai_co_gia_tri_la_query(tmp_path):
    rp = _lam_sach(tmp_path, [_du("B01", tuoi=""), _loai("B02", tuoi="70")])
    q = {(r["issue_type"], r["column"], r["row"]) for r in _query(rp, tmp_path)}
    assert ("missing_required_value", "tuoi", "1") in q
    assert ("value_when_branch_hidden", "tuoi", "2") in q


def test_cot_calc_co_san_trong_ban_xuat_duoc_giu_nguyen(tmp_path):
    """Bản xuất REDCap có cột calc: giá trị REDCap lưu được dùng, không tính đè."""
    td = [*TIEU_DE, "du_tc"]
    rp = _lam_sach(tmp_path, [[*_loai("B01"), "1"]], tieu_de=td)  # REDCap ghi 1 dù đầu vào nói 0
    q = {(r["issue_type"], r["column"]) for r in _query(rp, tmp_path)}
    assert ("missing_required_value", "tuoi") in q  # nhánh HIỆN theo giá trị đã lưu ⇒ tuổi trống là thiếu


def test_calc_tham_chieu_ma_khong_tinh_duoc_thi_giu_hanh_vi_cu_va_canh_bao(tmp_path):
    truong = [*TRUONG[:3], ("du_tc", "sang_loc", "calc", "round([mo_duoc], 0)", "", "", "", "", "n"), *TRUONG[4:]]
    rp = _lam_sach(tmp_path, [_loai("B01")], truong=truong)
    nh = rp["branching_logic"]
    assert nh["calc_khong_tinh_duoc"]["du_tc"]["so_hang"] == 1
    assert "tuoi" in nh["khong_danh_gia_duoc"]  # fail-safe: không coi là ẩn
    assert any(r["issue_type"] == "missing_required_value" for r in _query(rp, tmp_path))
    assert any("trường calc không tính lại được" in c for c in nh["canh_bao"])


def test_checkbox_bat_buoc_co_cot_con_khong_phai_thieu_bien(tmp_path):
    rp = _lam_sach(tmp_path, [_du("B01")])
    assert not [r for r in _query(rp, tmp_path) if r["issue_type"] == "missing_required_column"]
    # không có cột con nào ⇒ vẫn là thiếu biến bắt buộc
    td = [c for c in TIEU_DE if not c.startswith("thuoc___")]
    rp = _lam_sach(tmp_path, [[v for c, v in zip(TIEU_DE, _du("B01")) if c in td]], tieu_de=td)
    assert ("missing_required_column", "thuoc") in {(r["issue_type"], r["column"]) for r in _query(rp, tmp_path)}


def test_cong_g5_07b_checkbox_bat_buoc_co_cot_con_la_co_mat():
    assert G5Q._bien_bat_buoc_vang(["record_id", "thuoc"], ["record_id", "thuoc___1", "thuoc___0"]) == []
    assert G5Q._bien_bat_buoc_vang(["record_id", "thuoc"], ["record_id", "thuoc_1"]) == ["thuoc"]
    assert G5Q._bien_bat_buoc_vang(["tuoi"], ["record_id"]) == ["tuoi"]


# ───────────────────────────── công cụ nhập Excel ─────────────────────────────


@pytest.fixture()
def de_tai_excel(tmp_path, monkeypatch) -> Path:
    pytest.importorskip("openpyxl")
    import cau_noi_spss as SP

    monkeypatch.setattr(SP, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    _tu_dien(d / f"G5_REDCap_dictionary_{STUDY}.csv")
    return d


def test_nhap_excel_nhieu_trang_danh_gia_nhanh_theo_calc(tmp_path, de_tai_excel):
    import openpyxl

    mau = tmp_path / "ngoai" / "mau.xlsx"
    assert N.main(["mau", "--study", STUDY, "--ra", str(mau), "--so-dong", "10"]) == N.MA_OK
    wb = openpyxl.load_workbook(mau)
    gia = {"B01": dict(zip(TIEU_DE, _du("B01", tuoi=""))), "B02": dict(zip(TIEU_DE, _loai("B02")))}
    for ws in wb.worksheets:
        ten = [c.value for c in ws[1]]
        if "record_id" not in ten:
            continue
        for i, h in enumerate(gia.values()):
            for j, t in enumerate(ten):
                if t and h.get(t, "") != "":
                    ws.cell(N.DONG_DAU + i, j + 1, int(h[t]) if str(h[t]).isdigit() else h[t])
    p = tmp_path / "ngoai" / "lan1.xlsx"
    wb.save(p)
    ra = tmp_path / "ngoai" / "ra"
    N.main(["nhap", "--study", STUDY, "--excel", str(p), "--ra", str(ra)])
    ph = json.loads((ra / "lan1_bao_cao_nhap.json").read_text(encoding="utf-8"))["phat_hien"]
    assert not [x for x in ph if x["ma"] in ("logic_nhanh_khong_danh_gia_duoc", "calc_khong_tinh_duoc")], ph
    thieu = {(x["ma_nc"], x["cot"]) for x in ph if x["ma"] == "thieu_bat_buoc"}
    assert thieu == {("B01", "tuoi")}, thieu  # hồ sơ loại B02 không bị đòi câu nào của phần sau


# ───────────────────────────── bộ sinh dữ liệu theo từ điển ─────────────────────────────


def _td_sinh(tmp_path: Path) -> list[dict]:
    return SR.doc_tu_dien(_tu_dien(tmp_path / "td.csv"))


def test_bo_sinh_ton_trong_nhanh_calc_va_bat_buoc(tmp_path):
    td = _td_sinh(tmp_path)
    hang = SR.sinh(td, 300, {"mo_duoc": {"p": 0.8}, "tc_tuoi": {"p": 0.9}})
    du = [h for h in hang if h["tuoi"] is not None]
    assert 150 < len(du) < 260
    for h in hang:
        assert h["du_tc"] is None and h["bmi"] is None  # calc không nhập tay ⇒ không ghi ra
        hien = h["mo_duoc"] == 1 and h["tc_tuoi"] == 1
        for c in ("tuoi", "can_nang", "chieu_cao"):
            assert (h[c] is not None) == hien, (c, h)
        con = [h[f"thuoc___{m}"] for m in ("1", "2", "0")]
        assert (all(v is None for v in con) if not hien else (set(con) <= {0, 1} and 1 in con)), h
        if hien:
            assert 18 <= h["tuoi"] <= 110


def test_bo_sinh_tat_dinh_theo_hat_giong_va_dung_khi_du_n(tmp_path):
    td = _td_sinh(tmp_path)
    assert SR.sinh(td, 50, seed=7) == SR.sinh(td, 50, seed=7)
    hang = SR.sinh(td, 500, {"mo_duoc": {"p": 0.7}}, dung_khi=["[du_tc] = '1'", 40])
    assert sum(h["tuoi"] is not None for h in hang) == 40 and len(hang) < 500
    with pytest.raises(SR.KhongSinhDuoc, match="trần"):
        SR.sinh(td, 30, {"mo_duoc": {"p": 0.5}}, dung_khi=["[du_tc] = '1'", 40])


def test_bo_sinh_phan_bo_co_dieu_kien(tmp_path):
    td = _td_sinh(tmp_path)
    hm = {"tuoi": {"phan_bo": {"70": 0.5, "40": 0.5}},
          "can_nang": {"theo_dieu_kien": [["[tuoi] >= 65", {"co_dinh": 55}], ["", {"co_dinh": 70}]]}}  # fmt: skip
    hang = SR.sinh(td, 80, {"mo_duoc": {"p": 1.0}, "tc_tuoi": {"p": 1.0}, **hm})
    assert {h["tuoi"] for h in hang} == {70, 40}
    assert all(h["can_nang"] == (55 if h["tuoi"] >= 65 else 70) for h in hang)
    # can_nang sinh SAU tuoi trong từ điển ⇒ điều kiện tham chiếu câu chưa có ⇒ phải dừng rõ, không đoán
    with pytest.raises(SR.KhongSinhDuoc):
        SR.sinh(td, 5, {"mo_duoc": {"p": 1.0}, "tc_tuoi": {"p": 1.0},
                        "tuoi": {"theo_dieu_kien": [["[can_nang] >= 100", {"co_dinh": 99}]]}})


def test_bo_sinh_logic_ngoai_tap_con_thi_dung_ro(tmp_path):
    truong = [*TRUONG[:4], ("tuoi", "chung", "text", "", "integer", "18", "110", "datediff([a],[b],'d') > 1", "y")]
    with pytest.raises(SR.KhongSinhDuoc, match="datediff"):
        SR.sinh(SR.doc_tu_dien(_tu_dien(tmp_path / "td.csv", truong)), 3)


def test_bo_sinh_khong_dung_eval():
    nguon = (ROOT / "tools" / "sinh_du_lieu_redcap.py").read_text(encoding="utf-8")
    assert "eval(" not in nguon


# ───────────────────────────── bộ giả lập trọn vòng ─────────────────────────────


def test_bo_gia_lap_ghi_moi_trang_bieu_mau(tmp_path, de_tai_excel):
    import gia_lap_tron_vong as TV
    import openpyxl

    mau = tmp_path / "ngoai" / "mau.xlsx"
    assert N.main(["mau", "--study", STUDY, "--ra", str(mau), "--so-dong", "10"]) == N.MA_OK
    hang = [{**dict(zip(TIEU_DE, _du("B01"))), "tuoi": 61}, dict(zip(TIEU_DE, _loai("B02")))]
    ra = tmp_path / "ngoai" / "lan1.xlsx"
    TV.TronVong._ghi_excel(None, mau, ra, hang, {})
    wb = openpyxl.load_workbook(ra)
    trang = {ws.title: ws for ws in wb.worksheets if "record_id" in [c.value for c in ws[1]]}
    assert {"sang_loc", "chung", "thuoc"} <= set(trang)
    for ws in trang.values():  # mỗi mã có một hàng ở MỌI trang (kiem_trang_thieu đòi vậy)
        assert [ws.cell(N.DONG_DAU + i, 1).value for i in range(2)] == ["B01", "B02"]
    ten = [c.value for c in trang["chung"][1]]
    assert trang["chung"].cell(N.DONG_DAU, ten.index("tuoi") + 1).value == 61


def test_bo_gia_lap_khong_ghi_de_phieu_thu_thap_chu_nhiem_soan(tmp_path):
    import gia_lap_dinh_ky as GL
    import gia_lap_tron_vong as TV

    tv = object.__new__(TV.TronVong)
    tv.out, tv.study, tv.o = tmp_path, STUDY, []
    tv.kb = {"topic": "Thử", "bien_so": {"bo_bien": [["tuoi", "text", "Tuổi", "", "integer", "18", "110"]],
                                          "ma_tran": []}}  # fmt: skip
    (tmp_path / "study_meta.json").write_text("{}", encoding="utf-8", newline="\n")
    phieu = tmp_path / f"PHIEU_THU_THAP_SO_LIEU_{STUDY}.md"
    phieu.write_text("# PHIẾU do chủ nhiệm soạn\n\nPHẦN A. Sàng lọc hồ sơ\n", encoding="utf-8", newline="\n")
    tv._soan_phieu_thu_thap()
    assert phieu.read_text(encoding="utf-8").startswith("# PHIẾU do chủ nhiệm soạn") and tv.o == []
    # phiếu do chính bộ giả lập sinh ⇒ sinh lại
    phieu.write_text(f"# PHIẾU cũ\n\n{GL.NHAN}\n", encoding="utf-8", newline="\n")
    tv._soan_phieu_thu_thap()
    assert "`tuoi`" in phieu.read_text(encoding="utf-8") and len(tv.o) == 1


# ───────────────────────────── G6 · G8 · G10: lỗi lộ ra khi đi trọn G6→G10 trên khung BTM ─────────────────────────────

SAP_QT = """# SAP

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** mọi hồ sơ có `du_tieu_chuan` = 1, chọn theo thứ tự ngẫu nhiên từ khung mẫu.
- **Quần thể độ nhạy:** người có `so_luot` = 1.

### §2 KẾT CỤC

- **Kết cục chính (MT1):** Được xét nghiệm đủ UACR và creatinin trong 12 tháng — biến `xn_du`
- **Kết cục phụ 1 (MT1):** phân loại BTM — `phan_loai_btm`
- **Kết cục chính và kết cục phụ:** không thiếu theo định nghĩa.
"""


def test_quan_the_chinh_sap_doc_dung_bien_va_gia_tri():
    import chay_sap_g6 as CS6

    assert CS6.quan_the_chinh_sap(SAP_QT) == ("du_tieu_chuan", "1")
    assert CS6.quan_the_chinh_sap("### §1 QUẦN THỂ\n\n- **Quần thể chính:** Toàn bộ mẫu đủ tiêu chí\n") is None
    assert CS6.quan_the_chinh_sap("### §2 KẾT CỤC\n\n- **Quần thể chính:** `a` = 1\n") is None  # chỉ đọc §1


def _dac_ta(tmp_path: Path, loc: str | None, loc_phu: str | None = None) -> dict:
    import chay_sap_g6 as CS6

    (tmp_path / "SAP.md").write_text(SAP_QT, encoding="utf-8", newline="\n")
    ts = {"ty_le": ["xn_du"], **({"loc": loc} if loc else {})}
    ts_phu = {"ty_le": ["phan_loai_btm"], **({"loc": loc_phu} if loc_phu else {})}
    dt = {"nguon_sap": "SAP.md", "sha256_sap": CS6.sha256_tep(tmp_path / "SAP.md"), "phan_tich": [
        {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "tỷ lệ", "sap_neo": "Kết cục chính", "tham_so": ts},
        {"id": "P1", "vai": "phu", "sap_muc": "§4", "mo_ta": "phụ", "sap_neo": "Kết cục phụ 1", "tham_so": ts_phu},
    ]}
    return CS6.kiem_dac_ta(tmp_path, dt)


def test_dac_ta_g6_phan_tich_chinh_khong_loc_quan_the_la_loi(tmp_path):
    k = _dac_ta(tmp_path, None)
    assert any(x.startswith("MT1: SAP §1 khoanh quần thể chính") for x in k["loi"]), k["loi"]
    assert any(x.startswith("P1: SAP §1") for x in k["canh_bao"])  # phân tích phụ: chỉ cảnh báo
    k = _dac_ta(tmp_path, "du_tieu_chuan == 1", "du_tieu_chuan == 1 and so_luot == 1")
    assert not [x for x in k["loi"] + k["canh_bao"] if "SAP §1" in x], k


def test_g8_rut_ket_cuc_chinh_co_ngoac_muc_tieu():
    import g8_quality_gate as G8

    chinh, phu = G8.ket_cuc_sap(SAP_QT)
    assert len(chinh) == 1 and chinh[0].startswith("được xét nghiệm đủ uacr")
    assert len(phu) == 1 and "btm" in phu[0]  # dòng «Kết cục chính và kết cục phụ:» không phải dòng khai


def test_r15_bien_ket_cuc_chinh_la_bien_phai_sinh_da_khai(tmp_path):
    import research_study_spec as RS

    spec = {"outcomes": {"primary": {"name": "XN đủ", "variable_name": "xn_du"}},
            "variables": {"items": ["so_lan_creat", "so_lan_uacr"]}}  # fmt: skip
    ma = {i["code"] for i in RS.semantic_issues(spec, {}, {}, thu_muc=tmp_path)}
    assert "PRIMARY_OUTCOME_VARIABLE_NOT_IN_CRF" in ma  # chưa khai phái sinh ⇒ vẫn lỗi
    _csv(tmp_path / "_bien-phai-sinh.csv", ["ten_bien", "cong_thuc"], [["xn_du", "so_lan_uacr >= 1"]])
    ma = {i["code"] for i in RS.semantic_issues(spec, {}, {}, thu_muc=tmp_path)}
    assert "PRIMARY_OUTCOME_VARIABLE_NOT_IN_CRF" not in ma
    ma = {i["code"] for i in RS.semantic_issues(spec, {}, {})}  # không truyền thư mục ⇒ hành vi cũ
    assert "PRIMARY_OUTCOME_VARIABLE_NOT_IN_CRF" in ma


def test_r4_a12_loi_goi_la_chua_xac_minh_khong_phai_nghi_bia(tmp_path):
    import check_de_cuong as CDC

    md = tmp_path / "de_cuong.md"
    md.write_text("# Đề cương\nKDIGO 2024 (PMID: 38490803). Bài lạ (PMID: 99999901).\nCần bác sĩ kiểm chứng.\n",
                  encoding="utf-8", newline="\n")  # fmt: skip
    loi_goi = {"status": "unknown_mock_or_no_email", "reason": "lỗi gọi PubMed"}
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(
        json.dumps({"metadata": {"38490803": loi_goi}}), encoding="utf-8", newline="\n")
    bc = CDC.validate(md, tmp_path)
    r4 = [e for e in bc["errors"] if e.startswith("R4")]
    assert any("CHƯA XÁC MINH ĐƯỢC" in e and "38490803" in e for e in r4), r4
    assert any("nghi bịa" in e and "99999901" in e and "38490803" not in e for e in r4), r4
    assert bc["checks"]["R4_pmid_traceable"].startswith("FAIL")


def test_bo_gia_lap_muc_tieu_chung_khac_muc_tieu_cu_the():
    import gia_lap_tron_vong as TV

    meta = {"gate_params": {"G1": {"objectives": ["MT1: mô tả", "MT2: mô tả"]}}}
    bang = TV.gia_tri_da_chot(meta, {})
    assert not [ten for mau, _v, ten in bang if mau.search("muc tieu chung")]  # chưa khai aim ⇒ không «đã chốt»
    assert [ten for mau, _v, ten in bang if mau.search("muc tieu cu the")] == ["G1.objectives"]
    meta["gate_params"]["G1"]["aim"] = "Đánh giá thực trạng"
    assert [ten for mau, _v, ten in TV.gia_tri_da_chot(meta, {}) if mau.search("muc tieu chung")] == ["G1.aim"]


def test_cam_ket_huy_bang_noi_ma_theo_quy_trinh_da_chot(tmp_path):
    """Đơn miễn đồng thuận lấy ĐÚNG thời điểm huỷ bảng nối mã của `_quy-trinh-du-lieu.csv` (BTM: «sau khi khoá dữ
    liệu»); bản cũ ghi cứng «sau khi kết thúc nghiên cứu» ⇒ cùng đề cương nói hai thời điểm khác nhau."""
    import sinh_de_cuong_nop_hoi_dong as SDC

    n = object.__new__(SDC.Nguon)
    n.out, n.g1, n.g2 = tmp_path, {}, {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}
    cu = " ".join(SDC.don_mien_dong_thuan(n))
    assert "huỷ sau khi kết thúc nghiên cứu" in cu  # chưa chốt quy trình ⇒ câu khuôn chung
    _csv(tmp_path / "_quy-trinh-du-lieu.csv", ["muc", "gia_tri", "nguon", "neo_g2"],
         [["huy_bang_noi", "Bảng nối mã nghiên cứu với mã người bệnh lưu riêng trong tệp mã hoá, chỉ chủ nhiệm giữ, "
                           "huỷ sau khi khoá dữ liệu", "SOP", ""]])  # fmt: skip
    moi = " ".join(SDC.don_mien_dong_thuan(n))
    assert "huỷ sau khi khoá dữ liệu" in moi and "kết thúc nghiên cứu" not in moi
