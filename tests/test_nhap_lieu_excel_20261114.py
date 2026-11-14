"""Nhập liệu bằng tay qua Excel (tools/nhap_lieu_excel.py — gói E1, bác sĩ trả lời 14/11/2026: «Nhập liệu bằng tay vào
file Excel»): sinh mẫu có kiểm tra nhập, đọc Excel không đoán, kiểm giá trị như REDCap, luật DQ, nhập kép.

Từ điển + dữ liệu đều GIẢ (không PII). Tệp Excel dựng bằng openpyxl; bản đo bằng Microsoft Excel thật nằm ở báo cáo PR.
"""

from __future__ import annotations

import csv
import json
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as SP  # noqa: E402
import nhap_lieu_excel as N  # noqa: E402

STUDY = "de-tai-thu"
TD_COT = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip
TRUONG = [
    # ten, form, loai, nhan, lua_chon, kiem_tra, min, max, nhanh, bat_buoc, chu_thich
    ("record_id", "phieu", "text", "Mã phiếu", "", "", "", "", "", "y", ""),
    ("gioitinh", "phieu", "radio", "Giới tính", "1, Nam | 2, Nữ", "", "", "", "", "y", ""),
    ("tuoi", "phieu", "text", "Tuổi", "", "integer", "18", "120", "", "y", ""),
    ("nghe", "phieu", "radio", "Nghề", "1, Nông | 9, Khác", "", "", "", "", "n", ""),
    ("nghe_khac", "phieu", "text", "Nghề khác", "", "", "", "", "[nghe] = '9'", "y", ""),
    ("lydo", "phieu", "checkbox", "Lý do", "1, A | 2, B | 3, C", "", "", "", "", "n", "@MAXCHECKED=2"),
    ("kyvong", "phieu", "text", "Kỳ vọng phút", "", "integer", "0", "600", "", "n", ""),
    ("ngay_kham", "phieu", "text", "Ngày khám", "", "date_dmy", "2026-01-01", "", "", "n", ""),
    ("co_bh", "phieu", "yesno", "Có BHYT", "", "", "", "", "", "n", ""),
    ("diem", "phieu", "calc", "Điểm", "[tuoi]*2", "", "", "", "", "n", ""),
    ("gioi_thieu", "phieu", "descriptive", "Phần 2", "", "", "", "", "", "n", ""),
    ("ykien", "phieu", "notes", "Ý kiến", "", "", "", "", "", "n", ""),
    ("thoigian", "his", "text", "Thời gian chờ", "", "number", "0", "1440", "", "y", "@NOMISSING"),
]
MA_THIEU = [("*", "BTR", "Bỏ trống"), ("*", "KDD", "Không đọc được"), ("kyvong", "998", "Không ước lượng")]
LUAT_DQ = [
    ("DQ01", "truy_van", "Nữ dưới 20", "[gioitinh] = '2' and [tuoi] < 20"),
    ("DQ02", "truy_van", "Quá 2 lý do", "([lydo(1)] + [lydo(2)] + [lydo(3)]) > 2"),
]
LUAT_KHONG_HO = ("DQ99", "truy_van", "Hàm chưa hỗ trợ", "datediff([ngay_kham], 'today', 'd') > 1")


def _ghi_csv(p: Path, tieu_de: list[str], hang: list[list[str]]) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows(hang)


@pytest.fixture()
def de_tai(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(SP, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    hang = []
    for ten, form, loai, nhan, lc, kt, mn, mx, nh, bb, ct in TRUONG:
        r = dict.fromkeys(TD_COT, "")
        r.update(
            {
                TD_COT[0]: ten, TD_COT[1]: form, TD_COT[3]: loai, TD_COT[4]: nhan, TD_COT[5]: lc, TD_COT[7]: kt,
                TD_COT[8]: mn, TD_COT[9]: mx, TD_COT[11]: nh, TD_COT[12]: bb, TD_COT[17]: ct,
            }
        )  # fmt: skip
        hang.append([r[k] for k in TD_COT])
    _ghi_csv(d / f"G5_REDCap_dictionary_{STUDY}.csv", TD_COT, hang)
    _ghi_csv(d / "_ma-thieu-theo-bien.csv", ["bien", "ma", "nhan"], [list(x) for x in MA_THIEU])
    _ghi_csv(d / "_luat-dq.csv", ["ma_luat", "muc_do", "mo_ta", "bieu_thuc_redcap"], [list(x) for x in LUAT_DQ])
    return d


def _cot(d: Path):
    td = N.doc_tu_dien_day_du(d / f"G5_REDCap_dictionary_{STUDY}.csv")
    return N.ke_hoach_cot(td, SP.doc_ma_thieu(d / "_ma-thieu-theo-bien.csv"))


def _mau(tmp_path: Path, de_tai: Path, ten: str = "mau.xlsx", so_dong: int = 50) -> Path:
    ra = tmp_path / "ngoai" / ten
    assert N.main(["mau", "--study", STUDY, "--ra", str(ra), "--so-dong", str(so_dong)]) == N.MA_OK
    return ra


def _dien(mau: Path, ra: Path, phieu: list[dict], his: list[dict] | None = None, sua=None) -> Path:
    """Điền dữ liệu vào bản sao của mẫu (như người nhập gõ vào ô). Giá trị Python giữ nguyên kiểu (số/chữ/ngày)."""
    wb = openpyxl.load_workbook(mau)
    for trang, ds in (("phieu", phieu), ("his", his or [])):
        ws = wb[trang]
        ten_cot = {ws.cell(1, j).value: j for j in range(1, ws.max_column + 1)}
        for i, hang in enumerate(ds):
            for k, v in hang.items():
                ws.cell(N.DONG_DAU + i, ten_cot[k], v)
    if sua:
        sua(wb)
    ra.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ra)
    return ra


def _hop_le(ma: str, **them) -> dict:
    h = {"record_id": ma, "gioitinh": 1, "tuoi": 45, "nghe": 1, "lydo___1": 1, "kyvong": 30, "co_bh": 1}
    h.update(them)
    return h


# ───────────────────────────── kế hoạch cột ─────────────────────────────


def test_ke_hoach_cot_tach_checkbox_bo_calc_va_ap_ma_thieu(de_tai):
    cot, bo_qua = _cot(de_tai)
    ten = [c.ten for c in cot]
    assert ten[0] == "record_id" and cot[0].kieu == "id"
    assert ["lydo___1", "lydo___2", "lydo___3"] == [t for t in ten if t.startswith("lydo")]
    assert all(c.toi_da_chon == 2 for c in cot if c.truong == "lydo")
    assert "diem" not in ten and "gioi_thieu" not in ten and any("diem" in b for b in bo_qua)
    theo = {c.ten: c for c in cot}
    assert theo["tuoi"].kieu == "so_nguyen" and list(theo["tuoi"].ma_thieu) == ["BTR", "KDD"]
    assert list(theo["kyvong"].ma_thieu) == ["BTR", "KDD", "998"]  # 998 CHỈ ở kyvong
    assert theo["thoigian"].nomissing and theo["thoigian"].ma_thieu == {}  # @NOMISSING: không mã cấp dự án
    assert theo["co_bh"].lua_chon == {"1": "Có", "0": "Không"} and theo["ngay_kham"].kieu == "ngay"
    assert theo["ykien"].kieu == "van_ban" and theo["lydo___1"].ma_thieu == {}


def test_dau_van_tay_bo_qua_nhan_nhung_bat_doi_ma(de_tai):
    cot, _ = _cot(de_tai)
    goc = N.dau_van_tay_dac_ta(cot)
    cot[1].nhan = "Giới tính (sửa câu chữ)"
    assert N.dau_van_tay_dac_ta(cot) == goc
    cot[1].lua_chon = {**cot[1].lua_chon, "3": "Khác"}
    assert N.dau_van_tay_dac_ta(cot) != goc


# ───────────────────────────── logic REDCap ─────────────────────────────


@pytest.mark.parametrize(
    ("bt", "kq"),
    [
        ("[a] = '2' and [b] <> '7'", False),
        ("[a] = '2' and ([b] = '7' or [c] = '')", True),
        ("([a] = '1') or ([b] = '7')", True),
        ("([x(1)] + [x(2)] + [x(3)]) > 2", True),
        ("([x(1)] + [x(2)]) > 2", False),
        ("[c] + 1 > 0", False),  # ô trống trong phép tính ⇒ NaN ⇒ sai (REDCap)
        ("[a] = 2.0", True),  # so số khi cả hai là số
        ("[c] = ''", True),
        ("[a] > [c]", False),
        ("2 * [a] = 4 and -[a] < 0", True),
    ],
)
def test_danh_gia_logic(bt, kq):
    dong = {"a": "2", "b": "7", "c": "", "x___1": "1", "x___2": "1", "x___3": "1"}
    assert N.danh_gia_logic(bt, dong) is kq


@pytest.mark.parametrize("bt", ["datediff([a],'today')>1", "[khong_co] = '1'", "[a] =", "[a] = '1' [b]", "([a] = '1'"])
def test_logic_ngoai_tap_con_khong_bao_gio_doan(bt):
    with pytest.raises(N.LogicKhongHo):
        N.danh_gia_logic(bt, {"a": "1", "b": "2"})


# ───────────────────────────── sinh mẫu ─────────────────────────────


def test_mau_co_kiem_tra_nhap_dung_va_khong_ghi_ten_nguoi_dung(tmp_path, de_tai):
    p = _mau(tmp_path, de_tai)
    wb = openpyxl.load_workbook(p)
    assert wb.sheetnames[0] == N.TEN_HD and {"phieu", "his", N.TEN_TD} <= set(wb.sheetnames)
    assert wb[N.TEN_META].sheet_state == "veryHidden" and wb[N.TEN_DM].sheet_state == "veryHidden"
    assert wb.properties.creator == "nhap_lieu_excel.py" and wb.properties.lastModifiedBy == "nhap_lieu_excel.py"
    ws = wb["phieu"]
    tieu_de = [ws.cell(1, j).value for j in range(1, ws.max_column + 1)]
    assert tieu_de[0] == "record_id" and "lydo___2" in tieu_de and "diem" not in tieu_de
    assert ws.protection.sheet and ws.cell(N.DONG_DAU, 2).protection.locked is False
    assert ws.cell(1, 1).protection.locked is not False  # hàng tiêu đề khoá
    assert wb["his"].cell(1, 1).value == "record_id"  # cột mã nghiên cứu ở MỌI trang
    dv = {str(d.sqref).split(":")[0]: d for d in ws.data_validations.dataValidation}
    cot = {t: openpyxl.utils.get_column_letter(j) for j, t in enumerate(tieu_de, start=1)}
    o = f"{cot['tuoi']}{N.DONG_DAU}"
    assert dv[o].formula1 == f'IF(ISNUMBER({o}),AND({o}=INT({o}),{o}>=18,{o}<=120),OR({o}="BTR",{o}="KDD"))'
    o = f"{cot['kyvong']}{N.DONG_DAU}"
    assert dv[o].formula1.startswith(f"IF(ISNUMBER({o}),OR({o}=998,AND(")
    assert dv[f"A{N.DONG_DAU}"].formula1 == f"COUNTIF($A${N.DONG_DAU}:$A${N.DONG_DAU + 49},A{N.DONG_DAU})=1"
    o = f"{cot['lydo___2']}{N.DONG_DAU}"
    vung = f"${cot['lydo___1']}{N.DONG_DAU}:${cot['lydo___3']}{N.DONG_DAU}"
    assert dv[o].formula1 == f"AND(OR({o}=0,{o}=1),COUNTIF({vung},1)<=2)"
    o = f"{cot['gioitinh']}{N.DONG_DAU}"
    assert dv[o].type == "list" and dv[o].formula1 == "ds_gioitinh"
    ref = wb.defined_names["ds_gioitinh"].attr_text
    dm = wb[N.TEN_DM]
    cot_dm = ref.split("!")[1].split(":")[0].replace("$", "")[:-1]
    gia = [dm[f"{cot_dm}{r}"].value for r in range(2, 6)]
    assert gia == [1, 2, "BTR", "KDD"]  # mã SỐ là SỐ (Excel so ô gõ 1 với mục danh sách cùng kiểu)
    assert (
        ws[f"A{N.DONG_DAU}"].number_format == "@"
        and ws[f"{cot['ngay_kham']}{N.DONG_DAU}"].number_format == "dd/mm/yyyy"
    )
    meta = N._doc_meta(wb)
    assert meta["dac_ta_sha256"] == N.dau_van_tay_dac_ta(_cot(de_tai)[0]) and meta["dong_du_lieu"] == N.DONG_DAU


def test_mau_khong_ghi_de_tep_da_co_du_lieu(tmp_path, de_tai):
    p = _mau(tmp_path, de_tai)
    assert N.main(["mau", "--study", STUDY, "--ra", str(p)]) == N.MA_TU_CHOI  # đã có ⇒ không ghi đè
    assert N.main(["mau", "--study", STUDY, "--ra", str(p), "--ghi-de"]) == N.MA_OK  # mẫu trống ⇒ được
    _dien(p, p, [_hop_le("P01")])
    assert N.main(["mau", "--study", STUDY, "--ra", str(p), "--ghi-de"]) == N.MA_TU_CHOI
    assert openpyxl.load_workbook(p)["phieu"].cell(N.DONG_DAU, 1).value == "P01"  # dữ liệu còn nguyên


def test_mau_thieu_tu_dien_la_khong_do_duoc(tmp_path, monkeypatch):
    monkeypatch.setattr(SP, "EXPORTS", tmp_path / "exports")
    (tmp_path / "exports" / STUDY).mkdir(parents=True)
    assert N.main(["mau", "--study", STUDY, "--ra", str(tmp_path / "m.xlsx")]) == N.MA_KHONG_DO


# ───────────────────────────── chuyển đổi từng ô ─────────────────────────────


def _c(kieu: str, **kw) -> N.Cot:
    return N.Cot(ten="x", truong="x", form="f", kieu=kieu, **kw)


@pytest.mark.parametrize(
    ("kieu", "v", "mong", "loi"),
    [
        ("so", 18.0, "18", None),
        ("so", 0.1, "0.1", None),
        ("so", 1e-05, "0.00001", None),
        ("so", 37.25, "37.25", None),
        ("so_nguyen", 45, "45", None),
        ("ma", True, "TRUE", "o_kieu_logic_true_false"),
        ("ma", datetime(2026, 2, 1), "2026-02-01 00:00:00", "excel_tu_doi_thanh_ngay_gio"),
        ("ngay", datetime(2026, 3, 12), "2026-03-12", None),
        ("ngay", date(2026, 3, 12), "2026-03-12", None),
        ("ngay", datetime(2026, 3, 12, 8, 30), "2026-03-12 08:30:00", "ngay_co_gio"),
        ("ngay", "12/03/2026", "12/03/2026", "ngay_luu_dang_chu"),
        ("ngay", 46000, "46000", "ngay_luu_dang_so"),
        ("so", "1,5", "1,5", "so_dung_dau_phay"),
        ("id", 12.5, "12.5", "ma_nghien_cuu_la_so_le"),
        ("chu", "a\x07b", "ab", "ky_tu_dieu_khien"),
    ],
)
def test_chuyen_o_khong_doan(kieu, v, mong, loi):
    s, ma_loi, _ = N.chuyen_o(_c(kieu, lua_chon={"1": "A"}), v, "General", {})
    assert (s, ma_loi) == (mong, loi)


def test_chuyen_o_chuan_unicode_khoang_trang_va_ma_viet_khac():
    dem: dict = {}
    nfd = unicodedata.normalize("NFD", "Nguyễn")
    s, loi, _ = N.chuyen_o(_c("chu"), f" {nfd}​ ", "@", dem)
    assert s == "Nguyễn" and loi is None and s == unicodedata.normalize("NFC", s)
    assert dem["chuan_unicode_nfc"] == 1 and dem["bo_khoang_trang_dac_biet"] == 1
    c = _c("ma", lua_chon={"1": "Nam", "2": "Nữ"})
    assert N.chuyen_o(c, "01", "@", {})[1] == "ma_so_viet_khac"
    assert N.chuyen_o(c, "1.0", "@", {})[1] == "ma_so_viet_khac"
    assert N.chuyen_o(c, "1", "@", {})[1] is None
    dem2: dict = {}
    assert N.chuyen_o(_c("so", ma_thieu={"BTR": ""}), "18", "@", dem2) == ("18", None, None)
    assert dem2 == {"so_luu_dang_chu": 1}  # «18» dạng chữ = 18: chuẩn hoá KHÔNG đổi nghĩa, chỉ đếm


# ───────────────────────────── nhập đầu–cuối ─────────────────────────────


def _nhap(p: Path, ra: Path, *them: str) -> int:
    return N.main(["nhap", "--study", STUDY, "--excel", str(p), "--ra", str(ra), *them])


def _doc_bao_cao(ra: Path, p: Path) -> dict:
    return json.loads((ra / f"{p.stem}_bao_cao_nhap.json").read_text(encoding="utf-8"))


def test_nhap_sach_ghi_csv_dung_tung_o(tmp_path, de_tai, capsys):
    mau = _mau(tmp_path, de_tai)
    p = _dien(
        mau,
        tmp_path / "ngoai" / "lan1.xlsx",
        [_hop_le("P01", ykien="Phục vụ tốt", ngay_kham=datetime(2026, 3, 12)), _hop_le("P02", tuoi="BTR", kyvong=998)],
        [{"record_id": "P01", "thoigian": 37.5}, {"record_id": "P02", "thoigian": 0}],
    )
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_OK, capsys.readouterr().out
    with open(ra / "lan1.csv", encoding="utf-8", newline="") as f:
        doc = list(csv.DictReader(f))
    assert [r["record_id"] for r in doc] == ["P01", "P02"]
    assert doc[0]["tuoi"] == "45" and doc[1]["tuoi"] == "BTR" and doc[1]["kyvong"] == "998"
    assert doc[0]["ngay_kham"] == "2026-03-12" and doc[0]["thoigian"] == "37.5" and doc[1]["thoigian"] == "0"
    assert (doc[0]["lydo___1"], doc[0]["lydo___2"], doc[0]["lydo___3"]) == ("1", "0", "0")  # trống ⇒ 0 (REDCap)
    assert doc[0]["ykien"] == "Phục vụ tốt" and doc[1]["nghe_khac"] == ""
    bc = _doc_bao_cao(ra, p)
    assert bc["trang_thai"] == "SACH" and bc["tu_kiem_csv"] == "KHOP" and bc["csv_sha256"]
    assert bc["tu_kiem_doc_bang"][:2] == ["csv", "bộ làm sạch"]
    assert b"\r\n" not in (ra / "lan1.csv").read_bytes()


def test_nhap_bat_truy_van_gia_tri_nhu_redcap(tmp_path, de_tai, capsys):
    mau = _mau(tmp_path, de_tai)
    p = _dien(
        mau,
        tmp_path / "ngoai" / "lan1.xlsx",
        [
            _hop_le("P01", tuoi=121, gioitinh=3, nghe_khac="ghi thêm"),  # khoảng · danh mục · nhánh đang ẩn
            _hop_le("P02", gioitinh=2, tuoi=19, lydo___2=1, lydo___3=1),  # DQ01 + chọn quá 2 + DQ02
            _hop_le("P03", gioitinh=None, nghe=9, kyvong=998),  # thiếu bắt buộc · nghe=9 mà nghe_khac trống
            _hop_le("P04", tuoi=998, co_bh="BTR"),  # 998 KHÔNG phải mã thiếu của tuoi
        ],
        [{"record_id": "P01", "thoigian": "BTR"}]  # @NOMISSING không nhận BTR
        + [{"record_id": m, "thoigian": 5} for m in ("P02", "P03", "P04")],
    )
    with open(de_tai / "_luat-dq.csv", "a", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerow(LUAT_KHONG_HO)
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI
    ph = [(x["ma"], x["ma_nc"], x["cot"]) for x in _doc_bao_cao(ra, p)["phat_hien"] if x["muc"] == N.TRUY_VAN]
    mong = {
        ("tren_khoang", "P01", "tuoi"),
        ("ngoai_danh_muc", "P01", "gioitinh"),
        ("co_gia_tri_khi_bi_an", "P01", "nghe_khac"),
        ("luat_DQ01", "P02", "gioitinh"),
        ("vuot_toi_da_chon", "P02", "lydo___1"),
        ("luat_DQ02", "P02", "lydo___1"),
        ("thieu_bat_buoc", "P03", "gioitinh"),
        ("thieu_bat_buoc", "P03", "nghe_khac"),
        ("tren_khoang", "P04", "tuoi"),
        ("khong_phai_so", "P01", "thoigian"),
    }
    assert set(ph) == mong, set(ph) ^ mong
    canh = {x["cot"]: x["chi_tiet"] for x in _doc_bao_cao(ra, p)["phat_hien"] if x["muc"] == N.CANH_BAO}
    assert canh["DQ99"].startswith("4/4 hàng")  # luật dùng hàm chưa hỗ trợ: CẢNH BÁO, không coi là đạt
    assert (ra / "lan1.csv").exists()  # truy vấn giá trị vẫn ghi CSV (để làm sạch giải quyết nếu cần)
    assert _doc_bao_cao(ra, p)["trang_thai"] == "CAN_DOI_CHIEU"


def test_nhap_loi_cau_truc_khong_ghi_csv_va_xoa_csv_cu(tmp_path, de_tai, capsys):
    mau = _mau(tmp_path, de_tai)
    ra = tmp_path / "ngoai" / "ra"
    sach = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 5}])
    assert _nhap(sach, ra) == N.MA_OK and (ra / "lan1.csv").exists()

    def hong(wb):
        ws = wb["phieu"]
        ws["C6"] = "=40+5"  # công thức
        ws.cell(1, ws.max_column + 2, "cot_la")  # tiêu đề lạ
        ws.cell(N.DONG_DAU + 3, ws.max_column + 3, "rác")  # dữ liệu dưới cột không tên
        ws.cell(N.DONG_DAU + 4, 2, 1)  # có dữ liệu mà trống mã nghiên cứu
        ws.merge_cells(start_row=N.DONG_DAU + 6, start_column=2, end_row=N.DONG_DAU + 6, end_column=3)

    p = _dien(
        mau,
        tmp_path / "ngoai" / "lan1.xlsx",
        [_hop_le("P01"), _hop_le("P01"), _hop_le("P03", gioitinh=datetime(2026, 2, 1))],
        sua=hong,
    )
    assert _nhap(p, ra) == N.MA_LOI
    assert not (ra / "lan1.csv").exists()  # CSV cũ KHÔNG sống sót qua lượt có lỗi
    ma = {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"] if x["muc"] == N.LOI}
    assert {
        "o_cong_thuc",
        "cot_khong_co_trong_tu_dien",
        "du_lieu_o_cot_khong_ten",
        "thieu_ma_nghien_cuu",
        "o_gop",
        "trung_ma_nghien_cuu",
        "excel_tu_doi_thanh_ngay_gio",
    } <= ma


def test_nhap_cong_thuc_chi_nhan_khi_cho_phep_va_co_gia_tri_luu_san(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    p = _dien(
        mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01", tuoi="=40+5")], [{"record_id": "P01", "thoigian": 1}]
    )
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI
    assert _nhap(p, ra, "--cho-phep-cong-thuc") == N.MA_LOI  # openpyxl không lưu giá trị tính sẵn
    assert "cong_thuc_chua_tinh" in {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"]}


def test_nhap_tu_choi_thu_muc_ra_trong_repo(tmp_path, de_tai):
    """Dữ liệu chưa qua cổng tiếp nhận không được ghi vào BẤT KỲ cây git nào. Dùng repo GIẢ trong tmp_path để một
    bản lỗi (đột biến) có bỏ chặn cũng không xả tệp vào repo thật."""
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")])
    (tmp_path / "repo_gia" / ".git").mkdir(parents=True)
    ra = tmp_path / "repo_gia" / "du_lieu"
    assert _nhap(p, ra) == N.MA_TU_CHOI
    assert not ra.exists()


def test_nhap_mau_tu_dien_cu_bi_chan_tru_khi_chap_nhan(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 2}])
    td = de_tai / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text(
        td.read_text(encoding="utf-8").replace("1, Nam | 2, Nữ", "1, Nam | 2, Nữ | 3, Khác"),
        encoding="utf-8",
        newline="\n",
    )
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_TU_CHOI
    assert _nhap(p, ra, "--chap-nhan-tu-dien-moi") == N.MA_OK
    assert "mau_tu_tu_dien_cu" in {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"]}


def test_nhap_excel_tu_lam_khong_tu_mau(tmp_path, de_tai):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["record_id", "GioiTinh", "tuoi", "lydo"])  # «lydo» là checkbox chưa tách cột
    ws.append(["P01", 1, 30, "1,2"])
    p = tmp_path / "ngoai" / "tu_lam.xlsx"
    p.parent.mkdir(parents=True)
    wb.save(p)
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI
    ph = _doc_bao_cao(ra, p)["phat_hien"]
    assert {"cot_checkbox_chua_tach", "tieu_de_khac_hoa_thuong"} <= {x["ma"] for x in ph}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ghi chú tự do"])
    ws.append(["record_id", "gioitinh", "tuoi"])
    ws.append(["P01", 1, 30])
    wb.save(p)
    assert _nhap(p, ra, "--dong-tieu-de", "2") in (N.MA_OK, N.MA_LOI)
    assert (ra / "tu_lam.csv").read_text(encoding="utf-8").splitlines()[:2] == ["record_id,gioitinh,tuoi", "P01,1,30"]


def test_nhap_canh_bao_gia_tri_pandas_doc_thanh_thieu(tmp_path, de_tai):
    pytest.importorskip("pandas")
    mau = _mau(tmp_path, de_tai)
    p = _dien(
        mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01", ykien="NA")], [{"record_id": "P01", "thoigian": 3}]
    )
    ra = tmp_path / "ngoai" / "ra"
    _nhap(p, ra)
    assert "pandas_doc_thanh_thieu" in {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"]}


def test_tu_kiem_csv_that_bai_thi_xoa_csv(tmp_path, de_tai, monkeypatch):
    import clean_research_dataset as CRD

    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 4}])
    goc = CRD._read_csv
    monkeypatch.setattr(CRD, "_read_csv", lambda q: (lambda c, h, d: (c, [{**h[0], "tuoi": "99"}], d))(*goc(q)))
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI and not (ra / "lan1.csv").exists()
    assert any("bộ làm sạch" in x for x in _doc_bao_cao(ra, p)["tu_kiem_csv"])


def test_tiep_nhan_chi_chay_cong_khi_sach(tmp_path, de_tai, monkeypatch):
    mau = _mau(tmp_path, de_tai)
    goi: list[list[str]] = []

    class _Kq:
        returncode = 0

    monkeypatch.setattr(N.subprocess, "run", lambda lenh, check=False: goi.append(lenh) or _Kq())
    ra = tmp_path / "ngoai" / "ra"
    ban = _dien(mau, tmp_path / "ngoai" / "ban.xlsx", [_hop_le("P01", tuoi=121)], [{"record_id": "P01", "thoigian": 1}])
    assert _nhap(ban, ra, "--tiep-nhan") == N.MA_LOI and goi == []
    sach = _dien(mau, tmp_path / "ngoai" / "sach.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 1}])
    assert _nhap(sach, ra, "--tiep-nhan") == 0
    assert goi and goi[0][1].endswith("import_real_dataset.py") and goi[0][-1] == str(ra / "sach.csv")


# ───────────────────────────── nhập kép ─────────────────────────────


def test_so_sanh_nhap_kep_tung_o_va_bang_chung_khong_gia_tri(tmp_path, de_tai, capsys):
    mau = _mau(tmp_path, de_tai)
    his = [{"record_id": "P01", "thoigian": 10}]
    l1 = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01"), _hop_le("P02"), _hop_le("P03")], his)
    l2 = _dien(mau, tmp_path / "ngoai" / "lan2.xlsx", [_hop_le("P01", tuoi=54), _hop_le("P02"), _hop_le("P04")], his)
    ra = tmp_path / "ngoai" / "kep"
    assert N.main(["so-sanh", "--study", STUDY, "--excel1", str(l1), "--excel2", str(l2), "--ra", str(ra)]) == N.MA_LOI
    with open(ra / "NHAP_KEP_chi_tiet.csv", encoding="utf-8", newline="") as f:
        lech = list(csv.DictReader(f))
    assert [(x["ma_nc"], x["cot"], x["gia_tri_lan1"], x["gia_tri_lan2"]) for x in lech] == [("P01", "tuoi", "45", "54")]
    tom = json.loads((ra / "NHAP_KEP_tom_tat.json").read_text(encoding="utf-8"))
    assert tom["so_ma_chi_lan1"] == 1 and tom["so_ma_chi_lan2"] == 1 and tom["so_o_lech"] == 1
    so_cot_phieu = len([c for c in _cot(de_tai)[0] if c.form == "phieu" and c.kieu != "id"])
    assert tom["so_o_so_sanh"] == 2 * so_cot_phieu + 1  # P02 không có trang his ⇒ không tính vào mẫu số
    bc = list((de_tai / "nhap_lieu").glob("NHAP_KEP_tom_tat_*.json"))
    bang_chung = json.loads(bc[0].read_text(encoding="utf-8"))
    assert len(bc) == 1 and "gia_tri" not in bc[0].read_text(encoding="utf-8")  # KHÔNG chứa giá trị dữ liệu
    assert bang_chung["lech_theo_bien"] == {"tuoi": {"so_o": 2, "so_lech": 1}}
    l3 = _dien(mau, tmp_path / "ngoai" / "lan3.xlsx", [_hop_le("P01"), _hop_le("P02"), _hop_le("P03")], his)
    assert N.main(["so-sanh", "--study", STUDY, "--excel1", str(l1), "--excel2", str(l3), "--ra", str(ra)]) == N.MA_OK


def test_so_sanh_cung_mot_tep_bi_tu_choi(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")])
    assert N.main(["so-sanh", "--study", STUDY, "--excel1", str(p), "--excel2", str(p)]) == N.MA_TU_CHOI


def test_logic_nhanh_khong_danh_gia_duoc_thi_khong_doan_la_hien(tmp_path, de_tai):
    """Cột mà logic nhánh tham chiếu VẮNG trong tệp ⇒ không phán «bắt buộc mà trống», chỉ cảnh báo kèm số hàng."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["record_id", "gioitinh", "tuoi", "nghe_khac"])  # không có cột «nghe»
    ws.append(["P01", 1, 30, None])
    ws.append(["P02", 2, 40, None])
    p = tmp_path / "ngoai" / "thieu_nghe.xlsx"
    p.parent.mkdir(parents=True)
    wb.save(p)
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI  # «chưa kiểm được» ⇒ CHUA_DU, KHÔNG BAO GIỜ sạch
    assert _doc_bao_cao(ra, p)["trang_thai"] == "CHUA_DU"
    ph = _doc_bao_cao(ra, p)["phat_hien"]
    assert not [x for x in ph if x["ma"] == "thieu_bat_buoc"]
    canh = [x for x in ph if x["ma"] == "logic_nhanh_khong_danh_gia_duoc"]
    assert len(canh) == 1 and canh[0]["cot"] == "nghe_khac" and canh[0]["chi_tiet"].startswith("2/2 hàng")


def test_ma_khac_hoa_thuong_chuan_ve_ma_tu_dien_va_ma_nc_chi_khac_hoa_thuong_la_trung(tmp_path, de_tai):
    c = N.Cot(ten="tuoi", truong="tuoi", form="f", kieu="so_nguyen", ma_thieu={"BTR": "", "KDD": ""})
    dem: dict = {}
    assert N.chuyen_o(c, "btr", "General", dem)[:2] == ("BTR", None) and dem["chuan_hoa_thuong_ma"] == 1
    m = N.Cot(ten="g", truong="g", form="f", kieu="ma", lua_chon={"A": "x", "a": "y"})
    assert N.chuyen_o(m, "a", "General", {})[0] == "a"  # mã từ điển phân biệt hoa/thường ⇒ không đổi
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01"), _hop_le("p01")])
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI and not (ra / "lan1.csv").exists()
    assert "trung_ma_khac_hoa_thuong" in {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"]}


# ───────────────────────────── rà phản biện độc lập 14/11/2026 ─────────────────────────────


def _ma(ra: Path, p: Path, muc: str | None = None) -> set[str]:
    return {x["ma"] for x in _doc_bao_cao(ra, p)["phat_hien"] if muc is None or x["muc"] == muc}


def test_dinh_dang_o_so_doi_gia_tri_khong_bao_gio_la_sach(tmp_path, de_tai):
    """«50%» được Excel lưu 0.5 ⇒ LỖI; ô số mang định dạng khác mẫu ⇒ TRUY VẤN; số trong cột chữ/mã ⇒ TRUY VẤN."""
    mau = _mau(tmp_path, de_tai)

    def dinh_dang(wb):
        ws = wb["phieu"]
        ten = {ws.cell(1, j).value: j for j in range(1, ws.max_column + 1)}
        ws.cell(N.DONG_DAU, ten["kyvong"]).number_format = "0%"
        ws.cell(N.DONG_DAU + 1, ten["kyvong"]).number_format = "#,##0"

    his = [{"record_id": m, "thoigian": 1} for m in ("P01", "P02", "P03")]
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01", kyvong=0.5), _hop_le("P02", kyvong=1500),
              _hop_le("P03", nghe_khac=7)], his, sua=dinh_dang)  # fmt: skip
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI and not (ra / "lan1.csv").exists()
    assert "dinh_dang_phan_tram" in _ma(ra, p, N.LOI)
    assert {"dinh_dang_o_khac_mau", "so_trong_cot_chu"} <= _ma(ra, p, N.TRUY_VAN)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["record_id", "gioitinh", "tuoi", "kyvong"])
    ws.append([7, 1, 30, 1500])  # mã nghiên cứu dạng SỐ (số 0 đầu có thể đã mất)
    ws["D2"].number_format = "#,##0"
    q = tmp_path / "ngoai" / "tu_lam.xlsx"
    wb.save(q)
    _nhap(q, ra)
    assert {"dinh_dang_hang_nghin", "ma_nghien_cuu_luu_dang_so"} <= _ma(ra, q, N.TRUY_VAN)


def test_ma_lech_giua_cac_trang_la_truy_van_tung_ma(tmp_path, de_tai, monkeypatch):
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("BN001")], [{"record_id": "BN00l", "thoigian": 5}])
    ra = tmp_path / "ngoai" / "ra"
    goi: list = []
    monkeypatch.setattr(N.subprocess, "run", lambda *a, **k: goi.append(a))
    assert _nhap(p, ra, "--tiep-nhan") == N.MA_LOI and goi == []
    tv = [x for x in _doc_bao_cao(ra, p)["phat_hien"] if x["ma"] == "ma_nc_thieu_trang"]
    assert {x["ma_nc"] for x in tv} == {"BN001", "BN00l"} and all(x["muc"] == N.TRUY_VAN for x in tv)
    assert _doc_bao_cao(ra, p)["trang_thai"] == "CAN_DOI_CHIEU"


def test_trang_ngoai_mau_va_hang_tieu_de_bi_sua_la_loi(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    his = [{"record_id": "P01", "thoigian": 1}]

    def them_trang(wb):
        ws = wb.copy_worksheet(wb["phieu"])  # «phieu Copy» — bệnh nhân nhập nhầm sang trang chép thêm
        ws.cell(N.DONG_DAU, 1, "P09")

    p = _dien(mau, tmp_path / "ngoai" / "a.xlsx", [_hop_le("P01")], his, sua=them_trang)
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI and "trang_la_co_du_lieu" in _ma(ra, p, N.LOI)

    def go_hang_3(wb):
        wb["phieu"].protection.sheet = False
        wb["phieu"].cell(N.DONG_DAU - 1, 1, "P08")  # gõ nhầm dữ liệu vào hàng gợi ý

    q = _dien(mau, tmp_path / "ngoai" / "b.xlsx", [_hop_le("P01")], his, sua=go_hang_3)
    assert _nhap(q, ra) == N.MA_LOI and "hang_tieu_de_bi_sua" in _ma(ra, q, N.LOI)
    assert N.main(["mau", "--study", STUDY, "--ra", str(p), "--ghi-de"]) == N.MA_TU_CHOI  # có dữ liệu ở trang thêm


def test_trang_an_co_tieu_de_van_duoc_doc(tmp_path, de_tai):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["record_id", "gioitinh", "tuoi"])
    ws.append(["P01", 1, 30])
    an = wb.create_sheet("an")
    an.append(["record_id", "gioitinh", "tuoi"])
    an.append(["P02", 2, 40])
    an.sheet_state = "hidden"
    p = tmp_path / "ngoai" / "an.xlsx"
    p.parent.mkdir(parents=True)
    wb.save(p)
    ra = tmp_path / "ngoai" / "ra"
    _nhap(p, ra)
    assert "trang_an" in _ma(ra, p) and _doc_bao_cao(ra, p)["so_ma_nghien_cuu"] == 2


def test_chua_kiem_duoc_chan_tiep_nhan(tmp_path, de_tai, monkeypatch):
    with open(de_tai / "_luat-dq.csv", "a", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerow(LUAT_KHONG_HO)
    mau = _mau(tmp_path, de_tai)
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 1}])
    goi: list = []
    monkeypatch.setattr(N.subprocess, "run", lambda *a, **k: goi.append(a))
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra, "--tiep-nhan") == N.MA_LOI and goi == []
    assert _doc_bao_cao(ra, p)["trang_thai"] == "CHUA_DU"


def test_xuong_dong_chu_so_toan_kho_va_so_qua_15_chu_so(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    his = [{"record_id": m, "thoigian": 1} for m in ("P01", "P02", "P03", "P04")]
    phieu = [
        _hop_le("P01", ykien="dòng 1\ndòng 2"),
        _hop_le("P02", tuoi="６０"),
        _hop_le("P03", kyvong="12345678901234567"),
        _hop_le("P04", kyvong="1_0"),
    ]
    p = _dien(mau, tmp_path / "ngoai" / "lan1.xlsx", phieu, his)
    ra = tmp_path / "ngoai" / "ra"
    assert _nhap(p, ra) == N.MA_LOI
    assert "chu_so_khong_ascii" in _ma(ra, p, N.LOI)
    p2 = _dien(mau, tmp_path / "ngoai" / "lan2.xlsx", [phieu[0], *phieu[2:]], his[:1] + his[2:])
    assert _nhap(p2, ra) == N.MA_LOI
    tv = {(x["ma"], x["ma_nc"]) for x in _doc_bao_cao(ra, p2)["phat_hien"] if x["muc"] == N.TRUY_VAN}
    assert {("xuong_dong_trong_o", "P01"), ("so_vuot_do_chinh_xac", "P03"), ("khong_phai_so", "P04")} <= tv


def test_checkbox_duoi_logic_nhanh_khong_sinh_truy_van_gia():
    hop = [N.Cot(ten=f"x___{k}", truong="x", form="f", kieu="hop", ma_hop=str(k), nhanh="[a] = '1'") for k in (1, 2)]
    cot = [N.Cot(ten="id", truong="id", form="f", kieu="id"), N.Cot(ten="a", truong="a", form="f", kieu="ma",
           lua_chon={"1": "", "2": ""}), *hop]  # fmt: skip
    bang = N.Bang(cot, {"P1": {"id": "P1", "a": "2", "x___1": "0", "x___2": "1"}}, {"P1": {}}, {"P1": {"f"}}, [], {},
                  {}, [c.ten for c in cot])  # fmt: skip
    N.kiem_gia_tri(bang, [])
    assert [(x.ma, x.cot) for x in bang.phat_hien] == [("co_gia_tri_khi_bi_an", "x___2")]  # «0» không phải giá trị


def test_logic_nan_khac_dung_va_so_khong_ascii_khong_phai_so():
    assert N.danh_gia_logic("[a] + [b] <> 5", {"a": "", "b": "1"}) is True  # NaN <> 5
    assert N.danh_gia_logic("[a] + [b] = 5", {"a": "", "b": "1"}) is False
    assert N.danh_gia_logic("[z] = 10", {"z": "1_0"}) is False  # «1_0» KHÔNG phải số 10
    assert N._so_chat("６０") is None and N._so_chat("inf") is None and N._so_chat(" 2.5 ") == 2.5


def test_ma_thieu_so_o_cot_ngay_va_ngay_gio_co_giay():
    c = N.Cot(ten="d", truong="d", form="f", kieu="ngay", ma_thieu={"9999": ""})
    assert N.chuyen_o(c, 9999, "General", {}) == ("9999", None, None)
    g = N.Cot(ten="g", truong="g", form="f", kieu="ngay_gio", kiem_tra="datetime_seconds_dmy")
    assert N.chuyen_o(g, datetime(2026, 3, 1, 8, 5, 7), "General", {}) == ("2026-03-01 08:05:07", None, None)
    assert N._dinh_dang_cot(g) == "dd/mm/yyyy hh:mm:ss"


def test_khong_co_pandas_van_canh_bao_o_na(monkeypatch):
    monkeypatch.setitem(sys.modules, "pandas._libs.parsers", None)  # import ⇒ ImportError
    cot = [N.Cot(ten="id", truong="id", form="f", kieu="id"), N.Cot(ten="t", truong="t", form="f", kieu="chu")]
    bang = N.Bang(cot, {"P1": {"id": "P1", "t": "NA"}}, {}, {}, [], {}, {}, ["id", "t"])
    assert N.o_bi_pandas_coi_la_thieu(bang) == [("P1", "t")]


def test_excel_co_du_lieu_trong_repo_bi_canh_bao(tmp_path, de_tai):
    mau = _mau(tmp_path, de_tai)
    (tmp_path / "repo_gia" / ".git").mkdir(parents=True)
    p = _dien(mau, tmp_path / "repo_gia" / "lan1.xlsx", [_hop_le("P01")], [{"record_id": "P01", "thoigian": 1}])
    ra = tmp_path / "ngoai" / "ra"
    _nhap(p, ra)
    assert "excel_trong_repo" in _ma(ra, p, N.CANH_BAO)
