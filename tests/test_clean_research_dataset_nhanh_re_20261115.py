"""N2 (giả lập RCT lần 2, 14/11/2026): bộ làm sạch tôn trọng Branching Logic của từ điển REDCap.

Trước bản vá, `clean_research_dataset` kiểm «Required Field?» như mọi trường luôn hiện ⇒ mọi người mất theo dõi sinh
query «thiếu bắt buộc» cho từng trường «chỉ hiện khi theo dõi được» (lượt giả lập: 170 query giả = 34 người × 5
trường), trong khi công cụ nhập Excel (`nhap_lieu_excel`) đánh giá đúng nhánh ⇒ hai công cụ cùng dây chuyền mâu thuẫn.

Bản vá dùng ĐÚNG `nhap_lieu_excel.danh_gia_logic` (không viết bộ phân tích thứ hai):
- nhánh ẩn + trống ⇒ không query thiếu (đếm vào `required_missing_suppressed` để kiểm toán);
- nhánh ẩn + có giá trị ⇒ query `value_when_branch_hidden` (ô chọn nhiều «0» không tính — quy ước REDCap);
- biểu thức không đánh giá được / bộ đánh giá không nạp được ⇒ giữ hành vi cũ + cảnh báo trong báo cáo.

Từ điển + dữ liệu đều GIẢ (không PII). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import clean_research_dataset as CLEAN  # noqa: E402
import nhap_lieu_excel as NLE  # noqa: E402

STUDY = "ZZ-NHANH-RE-THU"
COT_TD = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip
THEO_DOI = "[mat_theo_doi] = '0'"
# ten, loai, lua_chon, kiem_tra, min, max, nhanh, bat_buoc
TRUONG_RCT = [
    ("record_id", "text", "", "", "", "", "", "y"),
    ("nhom", "radio", "0, Chứng | 1, Can thiệp", "", "", "", "", "y"),
    ("tuoi", "text", "", "integer", "18", "120", "", "y"),
    ("mat_theo_doi", "radio", "0, Theo dõi được | 1, Mất theo dõi", "", "", "", "", "y"),
    ("ha_tt_t6", "text", "", "integer", "60", "260", THEO_DOI, "y"),
    ("kiem_soat_t6", "radio", "0, Không | 1, Có", "", "", "", THEO_DOI, "y"),
    ("diem_tuan_thu_t6", "text", "", "integer", "0", "10", THEO_DOI, "y"),
    ("trieu_chung", "checkbox", "1, Chóng mặt | 2, Mệt", "", "", "", THEO_DOI, "n"),
]
TIEU_DE = ["record_id", "nhom", "tuoi", "mat_theo_doi", "ha_tt_t6", "kiem_soat_t6", "diem_tuan_thu_t6",
           "trieu_chung___1", "trieu_chung___2"]  # fmt: skip


def _tu_dien(path: Path, truong=TRUONG_RCT) -> Path:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_TD, lineterminator="\n")
        w.writeheader()
        for ten, loai, lc, kt, mn, mx, nh, bb in truong:
            r = dict.fromkeys(COT_TD, "")
            r.update({COT_TD[0]: ten, COT_TD[1]: "phieu", COT_TD[3]: loai, COT_TD[4]: ten, COT_TD[5]: lc,
                      COT_TD[7]: kt, COT_TD[8]: mn, COT_TD[9]: mx, COT_TD[11]: nh, COT_TD[12]: bb})  # fmt: skip
            w.writerow(r)
    return path


def _du_lieu(path: Path, hang: list[list[str]], tieu_de=TIEU_DE) -> Path:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows(hang)
    return path


def _theo_doi(ma: str, **sua) -> list[str]:
    h = {"record_id": ma, "nhom": "1", "tuoi": "61", "mat_theo_doi": "0", "ha_tt_t6": "138", "kiem_soat_t6": "1",
         "diem_tuan_thu_t6": "7", "trieu_chung___1": "0", "trieu_chung___2": "1"}  # fmt: skip
    h.update(sua)
    return [h[k] for k in TIEU_DE]


def _mat(ma: str, **sua) -> list[str]:
    """Người mất theo dõi: mọi trường «chỉ hiện khi theo dõi được» TRỐNG, ô chọn nhiều ghi 0 (quy ước REDCap)."""
    mac_dinh = {"mat_theo_doi": "1", "ha_tt_t6": "", "kiem_soat_t6": "", "diem_tuan_thu_t6": "",
                "trieu_chung___1": "0", "trieu_chung___2": "0"}  # fmt: skip
    return _theo_doi(ma, **{**mac_dinh, **sua})


def _lam_sach(tmp_path: Path, hang, *, truong=TRUONG_RCT, tieu_de=TIEU_DE, ma_thieu=None) -> dict:
    exports = tmp_path / "exports"
    if ma_thieu:
        (exports / STUDY).mkdir(parents=True, exist_ok=True)
        _du_lieu(exports / STUDY / CLEAN.MA_THIEU_TEN_FILE, [[b, m, "nhãn"] for b, m in ma_thieu],
                 tieu_de=["bien", "ma", "nhan"])  # fmt: skip
    return CLEAN.clean_dataset(
        STUDY, _du_lieu(tmp_path / "du_lieu.csv", hang, tieu_de),
        dictionary_path=_tu_dien(tmp_path / "tu_dien.csv", truong), exports_root=exports,
    )  # fmt: skip


def _query(rp: dict, tmp_path: Path) -> list[dict]:
    with open(tmp_path / "exports" / STUDY / rp["query_log"], encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["status"] == "open"]


# ───────────────────────────── đọc từ điển ─────────────────────────────


def test_doc_branching_tu_ca_tieu_de_redcap_lan_ten_cot_api():
    r = CLEAN._normalise_rule({"Variable / Field Name": "x", "Branching Logic (Show field only if...)": THEO_DOI})
    assert r["branching"] == THEO_DOI
    assert CLEAN._normalise_rule({"field_name": "x", "branching_logic": "[a] = '1'"})["branching"] == "[a] = '1'"
    assert CLEAN._normalise_rule({"field_name": "x"})["branching"] == ""


def test_cot_con_checkbox_thua_huong_nhanh_va_duoc_danh_dau():
    goc, *con = CLEAN._rules_cua_dong({"Variable / Field Name": "tc", "Field Type": "checkbox",
                                       "Choices, Calculations, OR Slider Labels": "1, A | 2, B",
                                       "Branching Logic (Show field only if...)": THEO_DOI})  # fmt: skip
    assert [c["name"] for c in con] == ["tc___1", "tc___2"]
    assert all(c["branching"] == THEO_DOI and c["checkbox_of"] == "tc" for c in con)
    assert "checkbox_of" not in goc


# ───────────────────────────── hành vi chính (N2) ─────────────────────────────


def test_n2_mat_theo_doi_khong_sinh_query_thieu_gia(tmp_path):
    """Ca của lượt giả lập thu nhỏ: 2 người mất theo dõi × 3 trường bắt buộc «chỉ hiện khi» ⇒ 0 query (bản cũ: 6)."""
    rp = _lam_sach(tmp_path, [_theo_doi("R01"), _mat("R02"), _theo_doi("R03"), _mat("R04")])
    assert rp["query_summary"] == {}, rp["query_summary"]
    assert rp["status"] == CLEAN.CLEAN_READY_STATUS and rp["ready_for_lock"] is True
    nh = rp["branching_logic"]
    assert nh["required_missing_suppressed"] == 6 and nh["value_when_hidden_queries"] == 0
    assert nh["evaluator"] == "nhap_lieu_excel.danh_gia_logic" and nh["canh_bao"] == []
    assert nh["fields_with_logic"] == ["ha_tt_t6", "kiem_soat_t6", "diem_tuan_thu_t6", "trieu_chung___1",
                                       "trieu_chung___2"]  # fmt: skip


def test_nhanh_hien_ma_trong_van_la_thieu_bat_buoc(tmp_path):
    """Không bớt quá tay: người THEO DÕI ĐƯỢC mà trống HA tháng 6 vẫn là query thiếu."""
    rp = _lam_sach(tmp_path, [_theo_doi("R01", ha_tt_t6=""), _mat("R02")])
    assert rp["query_summary"] == {"missing_required_value": 1}
    q = _query(rp, tmp_path)
    assert [(r["issue_type"], r["column"], r["row"]) for r in q] == [("missing_required_value", "ha_tt_t6", "1")]
    assert rp["branching_logic"]["required_missing_suppressed"] == 3


def test_nhanh_an_ma_co_gia_tri_thi_query_va_khong_luu_gia_tri(tmp_path):
    rp = _lam_sach(tmp_path, [_theo_doi("R01"), _mat("R02", ha_tt_t6="183")])
    assert rp["query_summary"] == {"value_when_branch_hidden": 1}
    assert rp["status"] == CLEAN.CLEAN_QUERY_STATUS
    q = _query(rp, tmp_path)
    assert [(r["issue_type"], r["column"], r["row"]) for r in q] == [("value_when_branch_hidden", "ha_tt_t6", "2")]
    assert THEO_DOI in q[0]["detail"] and "183" not in (tmp_path / "exports" / STUDY / rp["query_log"]).read_text(
        encoding="utf-8")
    assert rp["branching_logic"]["value_when_hidden_queries"] == 1


def test_checkbox_0_duoi_nhanh_an_khong_phai_gia_tri_nhung_1_thi_co(tmp_path):
    rp = _lam_sach(tmp_path, [_mat("R01"), _mat("R02", trieu_chung___2="1")])
    q = _query(rp, tmp_path)
    assert [(r["issue_type"], r["column"], r["row"]) for r in q] == [
        ("value_when_branch_hidden", "trieu_chung___2", "2")
    ]


def test_ma_thieu_o_truong_bi_an_khong_tinh_la_gia_tri(tmp_path):
    """«BTR» (mã thiếu đã khai) ở trường bị ẩn: bản sạch ghi trống ⇒ không phải «có giá trị khi nhánh ẩn»."""
    rp = _lam_sach(tmp_path, [_mat("R01", ha_tt_t6="BTR")], ma_thieu=[("*", "BTR")])
    assert rp["query_summary"] == {}, rp["query_summary"]


def test_danh_gia_tren_gia_tri_giu_nguyen_ma_thieu_nhu_cong_cu_nhap(tmp_path):
    """Biến điều khiển mang mã thiếu SỐ (tuoi=998, khai thiếu cho tuoi): đánh giá chữ-như-chữ như công cụ nhập ⇒
    «[tuoi] >= 65» ĐÚNG ⇒ trường hiện ⇒ trống là query thiếu. Nếu quy 998 về trống TRƯỚC khi đánh giá, nhánh thành
    ẩn và query bị nuốt — chiều bớt query, không an toàn."""
    truong = [
        ("record_id", "text", "", "", "", "", "", "y"),
        ("tuoi", "text", "", "integer", "18", "120", "", "y"),
        ("sang_loc_nga", "radio", "0, Không | 1, Có", "", "", "", "[tuoi] >= 65", "y"),
    ]
    tieu_de = ["record_id", "tuoi", "sang_loc_nga"]
    rp = _lam_sach(tmp_path, [["R01", "998", ""], ["R02", "40", ""]], truong=truong, tieu_de=tieu_de,
                   ma_thieu=[("tuoi", "998")])  # fmt: skip
    q = {(r["issue_type"], r["column"], r["row"]) for r in _query(rp, tmp_path)}
    assert ("missing_required_value", "sang_loc_nga", "1") in q, q
    assert ("missing_required_value", "sang_loc_nga", "2") not in q, "tuổi 40 ⇒ nhánh ẩn ⇒ trống là đúng"
    assert NLE.danh_gia_logic("[tuoi] >= 65", {"tuoi": "998"}) is True  # công cụ nhập phán y hệt


def test_cot_ma_ban_ghi_khong_xet_nhanh(tmp_path):
    """REDCap: trường mã bản ghi không có nhánh (công cụ nhập cũng bỏ nhánh của trường đầu tiên)."""
    truong = [("record_id", "text", "", "", "", "", "[nhom] = '9'", "y"), ("nhom", "radio", "0, A | 1, B", "", "",
              "", "", "y")]  # fmt: skip
    rp = _lam_sach(tmp_path, [["R01", "0"]], truong=truong, tieu_de=["record_id", "nhom"])
    assert rp["query_summary"] == {}, rp["query_summary"]
    assert rp["branching_logic"]["fields_with_logic"] == []


# ───────────────────────────── fail-safe ─────────────────────────────


@pytest.mark.parametrize(
    "bieu_thuc",
    ["datediff([ngay_a], [ngay_b], 'd', true) > 3", "[khong_co_trong_du_lieu] = '1'", "[mat_theo_doi] == '0'"],
)
def test_bieu_thuc_khong_danh_gia_duoc_giu_hanh_vi_cu_va_canh_bao(tmp_path, bieu_thuc):
    truong = [t if t[0] != "ha_tt_t6" else (*t[:6], bieu_thuc, t[7]) for t in TRUONG_RCT]
    rp = _lam_sach(tmp_path, [_mat("R01"), _mat("R02", ha_tt_t6="183")], truong=truong)
    q = {(r["issue_type"], r["column"], r["row"]) for r in _query(rp, tmp_path)}
    assert ("missing_required_value", "ha_tt_t6", "1") in q, "không đánh giá được ⇒ KHÔNG coi là ẩn (giữ query cũ)"
    assert not [x for x in q if x[1] == "ha_tt_t6" and x[0] == "value_when_branch_hidden"]
    nh = rp["branching_logic"]
    assert nh["khong_danh_gia_duoc"]["ha_tt_t6"]["so_hang"] == 2 and nh["khong_danh_gia_duoc"]["ha_tt_t6"]["ly_do"]
    assert len(nh["canh_bao"]) == 1 and nh["canh_bao"][0].startswith("ha_tt_t6:") and "2/2 hàng" in nh["canh_bao"][0]
    assert nh["required_missing_suppressed"] == 4, "các trường khác vẫn đánh giá bình thường"
    assert "183" not in json.dumps(nh, ensure_ascii=False)


def test_bo_danh_gia_dung_chung_khong_nap_duoc_thi_giu_hanh_vi_cu(tmp_path, monkeypatch):
    monkeypatch.setattr(CLEAN, "_bo_danh_gia_nhanh", lambda: (None, (), "không nạp được (giả lập)"))
    rp = _lam_sach(tmp_path, [_mat("R01")])
    assert rp["query_summary"] == {"missing_required_value": 3}, "hành vi cũ: 3 trường bắt buộc trống"
    nh = rp["branching_logic"]
    assert nh["required_missing_suppressed"] == 0 and len(nh["canh_bao"]) == 5
    assert all("không nạp được (giả lập)" in c for c in nh["canh_bao"])


def test_nap_mo_dun_dung_chung_hong_thi_khong_sap_va_giu_hanh_vi_cu(tmp_path, monkeypatch):
    """Đường nạp THẬT (không giả hàm nạp): mô-đun công cụ nhập không import được ⇒ bộ làm sạch vẫn chạy, hành vi cũ."""
    monkeypatch.setitem(sys.modules, "nhap_lieu_excel", None)  # import ⇒ ModuleNotFoundError (lớp con ImportError)
    rp = _lam_sach(tmp_path, [_mat("R01")])
    assert rp["query_summary"] == {"missing_required_value": 3}
    ly_do = rp["branching_logic"]["khong_danh_gia_duoc"]["ha_tt_t6"]["ly_do"]
    assert ly_do.startswith("không nạp được bộ đánh giá logic dùng chung") and "ModuleNotFoundError" in ly_do


def test_loi_la_cua_bo_danh_gia_cung_ve_hanh_vi_cu(tmp_path, monkeypatch):
    def _no(_bt, _dong):
        raise RuntimeError("hỏng")

    monkeypatch.setattr(NLE, "danh_gia_logic", _no)
    rp = _lam_sach(tmp_path, [_mat("R01")])
    assert rp["query_summary"] == {"missing_required_value": 3}
    assert rp["branching_logic"]["khong_danh_gia_duoc"]["ha_tt_t6"]["ly_do"] == "lỗi bộ đánh giá: RuntimeError"


# ───────────────────────────── dùng CHUNG với công cụ nhập ─────────────────────────────


def test_dung_dung_ham_danh_gia_cua_cong_cu_nhap(tmp_path, monkeypatch):
    """Chốt «một bộ phân tích»: mọi biểu thức nhánh phải đi qua nhap_lieu_excel.danh_gia_logic."""
    goi: list[str] = []
    goc = NLE.danh_gia_logic

    def _do_tham(bt, dong):
        goi.append(bt)
        return goc(bt, dong)

    monkeypatch.setattr(NLE, "danh_gia_logic", _do_tham)
    _lam_sach(tmp_path, [_theo_doi("R01"), _mat("R02")])
    assert goi and set(goi) == {THEO_DOI} and len(goi) == 2 * 5  # 2 hàng × 5 cột có nhánh


def test_dau_cuoi_excel_roi_lam_sach_cung_ket_luan(tmp_path, monkeypatch):
    """Đầu–cuối: công cụ nhập Excel (0 truy vấn cho người mất theo dõi) → CSV → bộ làm sạch: cũng 0 query."""
    openpyxl = pytest.importorskip("openpyxl")
    import cau_noi_spss as SP  # noqa: PLC0415

    exports = tmp_path / "exports"
    monkeypatch.setattr(SP, "EXPORTS", exports)
    d = exports / STUDY
    d.mkdir(parents=True)
    tu_dien = _tu_dien(d / f"G5_REDCap_dictionary_{STUDY}.csv")
    _du_lieu(d / CLEAN.MA_THIEU_TEN_FILE, [["*", "BTR", "Bỏ trống"]], tieu_de=["bien", "ma", "nhan"])
    mau = tmp_path / "ngoai" / "mau.xlsx"
    assert NLE.main(["mau", "--study", STUDY, "--ra", str(mau), "--so-dong", "10"]) == NLE.MA_OK
    wb = openpyxl.load_workbook(mau)
    ws = wb["phieu"]
    ten_cot = {ws.cell(1, j).value: j for j in range(1, ws.max_column + 1)}
    hang = [
        {"record_id": "R01", "nhom": 1, "tuoi": 61, "mat_theo_doi": 0, "ha_tt_t6": 138, "kiem_soat_t6": 1,
         "diem_tuan_thu_t6": 7, "trieu_chung___2": 1},
        {"record_id": "R02", "nhom": 0, "tuoi": 54, "mat_theo_doi": 1},
    ]  # fmt: skip
    for i, h in enumerate(hang):
        for k, v in h.items():
            ws.cell(NLE.DONG_DAU + i, ten_cot[k], v)
    excel = tmp_path / "ngoai" / "lan1.xlsx"
    wb.save(excel)
    ra = tmp_path / "ngoai" / "ra"
    assert NLE.main(["nhap", "--study", STUDY, "--excel", str(excel), "--ra", str(ra)]) == NLE.MA_OK
    bc = json.loads((ra / "lan1_bao_cao_nhap.json").read_text(encoding="utf-8"))
    assert bc["trang_thai"] == "SACH" and not [x for x in bc["phat_hien"] if x["muc"] == NLE.TRUY_VAN]
    rp = CLEAN.clean_dataset(STUDY, ra / "lan1.csv", dictionary_path=tu_dien, exports_root=tmp_path / "exports_lam")
    assert rp["query_summary"] == {}, rp["query_summary"]
    assert rp["status"] == CLEAN.CLEAN_READY_STATUS
    assert rp["branching_logic"]["required_missing_suppressed"] == 3
