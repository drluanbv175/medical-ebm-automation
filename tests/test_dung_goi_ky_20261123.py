"""Lệnh dựng gói ký cho đề tài thật (tools/dung_goi_ky.py, 23/11/2026).

Luật được canh:
  * Chạy tuần tự đúng thứ tự khâu; khâu đầu tiên đỏ (hoặc không đo được) ⇒ DỪNG, khâu sau không chạy, không xuất gói
    ký; có `--ghi` thì ghi báo cáo dừng và dời gói ký cũ vào `goi_ky/_cu/` (không để bản cũ trông như hiện hành).
  * Khâu 1 chỉ đi tiếp khi khâu cần hoàn thiện CHỈ chờ cổng trước khoá và các cổng đó nằm trong danh sách khoá.
  * Xuất Word đề cương nộp đứng TRƯỚC lắp G10 (G10 băm cặp .md/.docx bản nộp vào manifest).
  * Lắp G10: mã 0/2 đạt khâu; 3/1 dừng.
  * K20 chỉ vì công thức phái sinh chờ duyệt (công thức hợp lệ) ⇒ chuyển vào gói ký; lỗi K khác ⇒ dừng.
  * Gói ký đúng thứ tự cổng; mỗi mục có vai, tài liệu kèm SHA-256, lệnh, điều kiện tiên quyết; G2 đòi quyết định của
    Hội đồng; G10 đòi sổ đọc phủ 100%; cổng cứng dùng approve_gate.py đúng từng vai; lệnh không tự ký.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools import dung_goi_ky as DGK  # noqa: E402

STUDY = "de-tai-goi-ky"


def _ctx(tmp_path: Path, ghi: bool = True) -> DGK.NguCanh:
    (tmp_path / "exports" / STUDY).mkdir(parents=True, exist_ok=True)
    return DGK.NguCanh(STUDY, ghi, goc=tmp_path)


def _khau_gia(ma: str, dat, so: int = 1):
    def ham(ctx):
        return DGK._khau(so, ma, ma, f"chot_{ma}", dat, f"kết quả {ma}", ["chi tiết"])
    return ham


def test_thu_tu_khau_xuat_word_truoc_lap_g10() -> None:
    ten = [m for m, _ in DGK.KHAU]
    assert ten == ["khau_dang_mo", "xuat_word", "lap_g10", "kiem_de_cuong", "ho_so", "doi_chieu"]
    assert ten.index("xuat_word") < ten.index("lap_g10"), "G10 băm bản Word nộp — xuất Word phải trước khi lắp"


def test_dung_o_khau_do_dau_tien_va_doi_goi_cu(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    ra = ctx.out_dir / DGK.THU_MUC_RA
    ra.mkdir(parents=True)
    (ra / f"GOI_KY_{STUDY}.md").write_text("gói cũ", encoding="utf-8", newline="\n")
    da_goi = []

    def khong_duoc_goi(ctx):
        da_goi.append("k3")
        return DGK._khau(3, "k3", "k3", "c", True, "")
    kq = DGK.chay(ctx, [("k1", _khau_gia("k1", True)), ("k2", _khau_gia("k2", False, 2)), ("k3", khong_duoc_goi)])
    assert kq["ma_thoat"] == 1 and kq["goi_ky"] is None and da_goi == []
    assert not (ra / f"GOI_KY_{STUDY}.md").exists(), "gói ký cũ phải dời đi khi lượt mới dừng"
    assert any(p.name == f"GOI_KY_{STUDY}.md" for p in (ra / "_cu").rglob("*"))
    bao = (ra / f"DUNG_GOI_KY_{STUDY}.md").read_text(encoding="utf-8")
    assert "DỪNG ở khâu 2" in bao and "chot_k2" in bao and "Chưa xuất gói ký" in bao
    assert json.loads((ra / f"DUNG_GOI_KY_{STUDY}.json").read_text(encoding="utf-8"))["dung_o_khau"] == 2


def test_khong_do_duoc_ma_2_va_chay_kho_khong_ghi(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, ghi=False)
    kq = DGK.chay(ctx, [("k1", _khau_gia("k1", None))])
    assert kq["ma_thoat"] == 2 and kq["tep_ghi"] == []
    assert not (ctx.out_dir / DGK.THU_MUC_RA).exists(), "chạy khô không ghi tệp"


def _bdm(ht_ket="CHO_CONG_TRUOC", cho=("G1",), ma_thoat=1, danh=("G1",)):
    cong = [{"gate": "G0", "da_khoa": True, "status": "PASS_G0_CONFIRMED"},
            {"gate": "G1", "da_khoa": False, "status": "DRAFT_READY_NEEDS_HUMAN_REVIEW", "vi_tri": "CHO_KY"},
            {"gate": "G2", "da_khoa": False, "status": "DRAFT_NEEDS_HUMAN_COMPLETION", "vi_tri": "KHAU_CAN_HOAN_THIEN",
             "ghi_chu": "phụ thuộc cổng trước",
             "hoan_thien": {"ket_luan": ht_ket, "cho_cong": list(cho), "cho_cong_chua_khoa": list(cho),
                            "viec_he_lam_tiep": ["G2-T1: việc còn làm"]}},
            {"gate": "G3", "da_khoa": False, "status": "DRAFT_NEEDS_HUMAN_PARAMETERS"},
            {"gate": "G4", "da_khoa": False, "status": "DRAFT_NEEDS_HUMAN_CONTENT"},
            *({"gate": g, "da_khoa": False, "status": "CHUA_CHAY"} for g in ("G5", "G6", "G7", "G8", "G9")),
            {"gate": "G10", "da_khoa": False, "status": "BLOCKED"}]
    return {"ma_thoat": ma_thoat, "khau_dang_mo": "G1", "khau_can_hoan_thien": "G2", "cong": cong,
            "danh_sach_khoa": [{"gate": g, "vai": ["PI"], "loai": "chot"} for g in danh], "ket_luan": "…"}


@pytest.mark.parametrize("bdm,dat", [
    (_bdm(), True),
    (_bdm(ht_ket="AGENT_CON_VIEC"), False),
    (_bdm(ht_ket="AGENT_XONG_CHO_NGUOI"), False),
    (_bdm(cho=("G1", "G0x"),), False),
    (_bdm(danh=()), False),
    (_bdm(ma_thoat=2), None),
])
def test_khau_dang_mo_chi_di_tiep_khi_chi_cho_khoa(tmp_path, monkeypatch, bdm, dat) -> None:
    import buoc_dang_mo as BDM

    monkeypatch.setattr(BDM, "phan_tich", lambda study, out_dir: bdm)
    assert DGK.khau_buoc_dang_mo(_ctx(tmp_path))["dat"] is dat


@pytest.mark.parametrize("ma,dat", [(0, True), (2, True), (3, False), (1, False)])
def test_lap_g10_theo_ma_thoat(tmp_path, ma, dat) -> None:
    k = DGK.khau_lap_g10(_ctx(tmp_path), chay=lambda ctx: (ma, "dòng một\ndòng cuối"))
    assert k["dat"] is dat and k["du_lieu"]["ma_thoat"] == ma


DONG_PS = "K20 phần «Biến số và kết cục» × Tính tái lập: DC-PHAI-SINH (trạng thái: DA_DUYET 11, HET_HIEU_LUC 1)"


@pytest.mark.parametrize("loi_k,loi_ps,cho_ky,dat", [
    ([DONG_PS], {}, [{"bien": "PhieuHopLe", "trang_thai": "HET_HIEU_LUC", "dau_cong_thuc": "a" * 12}], True),
    ([DONG_PS], {"PhieuHopLe": "cú pháp sai"}, [{"bien": "PhieuHopLe", "trang_thai": "HET_HIEU_LUC",
                                                  "dau_cong_thuc": "a" * 12}], False),
    ([DONG_PS + "; DC-BIEN (lệch biến)"], {}, [{"bien": "X", "trang_thai": "CHUA_DUYET", "dau_cong_thuc": "b" * 12}],
     False),
    (["K11 số thập phân dùng dấu chấm"], {}, [], False),
    ([], {}, [], True),
])
def test_k20_phai_sinh_chuyen_vao_goi_ky(tmp_path, monkeypatch, loi_k, loi_ps, cho_ky, dat) -> None:
    import kiem_de_cuong_nop_hoi_dong as K
    import so_doc_de_cuong as SDD

    monkeypatch.setattr(K, "kiem", lambda out_dir, study: list(loi_k))
    monkeypatch.setattr(K, "canh_bao_k20_k21", lambda out_dir, study: [])
    monkeypatch.setattr(K, "canh_bao_k17", lambda out_dir, study: [])
    monkeypatch.setattr(DGK, "phai_sinh_cho_ky", lambda out_dir, study: {"co_tep": True, "loi": loi_ps,
                                                                         "cho_ky": cho_ky, "tep": "x.csv",
                                                                         "sha256": "0" * 64})
    monkeypatch.setattr(SDD, "trang_thai", lambda out_dir, study: {"tong": 3, "da_doc": 1, "chua_doc": 2,
                                                                    "doi_sau_doc": 0, "can_sua": 0,
                                                                    "ds_chua_doc": [{"ma": "cau:1", "loai": "cau"},
                                                                                    {"ma": "tltk:2", "loai": "tltk"}],
                                                                    "ds_can_sua": []})
    k = DGK.khau_kiem_de_cuong(_ctx(tmp_path))
    assert k["dat"] is dat, k
    assert k["du_lieu"]["so_doc"]["ds_chua_doc"] == ["cau:1", "tltk:2"], "K21: liệt kê đơn vị chưa có bản ghi đọc"
    assert k["du_lieu"]["so_doc"]["theo_loai_chua_doc"] == {"cau": 1, "tltk": 1}


def test_ho_so_dung_khi_kiem_khac_0(tmp_path, monkeypatch) -> None:
    class Gia:
        def __init__(self, ma_kiem):
            self.goi, self.ma_kiem = [], ma_kiem

        def main(self, argv):
            self.goi.append(argv[0])
            if argv[0] == "kiem":
                print("kết quả kiem")
                return self.ma_kiem
            return 0
    hdd, dtcs = Gia(0), Gia(1)
    monkeypatch.setattr(DGK, "_bo_dung", lambda ten: (hdd, "ho_so_hdd/HO_SO_HDD_BVQY175.json") if ten == "hdd"
                        else (dtcs, "ho_so_dtcs/HO_SO_DTCS_BVQY175.json"))
    ctx = _ctx(tmp_path)
    (ctx.out_dir / "ho_so_hdd").mkdir()
    (ctx.out_dir / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json").write_text(json.dumps({"meta": {"quy_trinh": "ca_hai"}}),
                                                                       encoding="utf-8", newline="\n")
    k = DGK.khau_ho_so(ctx)
    assert k["dat"] is False and "đề tài cơ sở" in k["tom_tat"]
    assert hdd.goi == ["trich", "dung", "kiem"] and dtcs.goi == ["trich", "dung", "kiem"]
    dtcs.ma_kiem, hdd.goi, dtcs.goi = 0, [], []
    assert DGK.khau_ho_so(ctx)["dat"] is True
    (ctx.out_dir / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json").write_text("{}", encoding="utf-8", newline="\n")
    k = DGK.khau_ho_so(ctx)
    assert k["dat"] is False and "meta.quy_trinh" in k["tom_tat"], "thiếu quy trình xét duyệt ⇒ không dựng bừa"


def test_doi_chieu_lech_thi_dung(tmp_path, monkeypatch) -> None:
    import ho_so_nguon_chung as HSC

    ctx = _ctx(tmp_path)
    for thu_muc, ten in (("ho_so_hdd", "HO_SO_HDD_BVQY175.json"), ("ho_so_dtcs", "HO_SO_DTCS_BVQY175.json")):
        (ctx.out_dir / thu_muc).mkdir()
        (ctx.out_dir / thu_muc / ten).write_text('{"a": 1}', encoding="utf-8", newline="\n")
    monkeypatch.setattr(HSC, "NguonDeTai", lambda root, study: object())
    dc = [{"truong": "tên đề tài", "tai_lieu": "gói G2", "ket": "lech", "chi_tiet": "khác"},
          {"truong": "mục tiêu", "tai_lieu": "gói G2", "ket": "khop", "chi_tiet": ""}]
    monkeypatch.setattr(HSC, "doi_chieu", lambda n, hdd, dtcs: dc)
    k = DGK.khau_doi_chieu(ctx)
    assert k["dat"] is False and k["du_lieu"]["lech"] == 1
    dc[0]["ket"] = "khop"
    assert DGK.khau_doi_chieu(ctx)["dat"] is True


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_goi_ky_dung_thu_tu_cong_va_du_noi_dung(tmp_path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    od = ctx.out_dir
    for ten in ("G1_A2_PROTOCOL_CORE_{s}.md", "G1_checkpoint.json", "G2_A3_ETHICS_PACKAGE_{s}.md",
                "G4_A5_SAP_FINAL_{s}.md", "G10_checkpoint.json", "DE_CUONG_NOP_HOI_DONG_{s}.md", "_bien-phai-sinh.csv"):
        (od / ten.format(s=STUDY)).write_text(f"nội dung {ten}", encoding="utf-8", newline="\n")
    monkeypatch.setattr(DGK, "_cham_cong_thuong", lambda gate, study, out_dir: {
        "dau": "abcdef0123456789" if gate == "G1" else None,
        "muc": [{"id": f"{gate}-HUMAN-08", "label": "xác nhận gắn dấu", "action": "ghi reviewed_at"}]})
    ctx.kq["khau_dang_mo"] = {"du_lieu": _bdm()}
    ctx.kq["kiem_de_cuong"] = {"du_lieu": {
        "phai_sinh": {"loi": {}, "cho_ky": [{"bien": "PhieuHopLe", "trang_thai": "HET_HIEU_LUC",
                                             "dau_cong_thuc": "1" * 12}], "tep": "_bien-phai-sinh.csv",
                      "sha256": _sha(od / "_bien-phai-sinh.csv")},
        "so_doc": {"tong": 10, "da_doc": 0}}}
    g = DGK.lap_goi_ky(ctx)
    thu_tu = [(m["gate"], m["loai"]) for m in g["muc"]]
    assert thu_tu == [("G1", "chot_cong"), ("G2", "ky_so_cai"), ("G3", "duyet_cong_thuc_phai_sinh"),
                      ("G3", "chot_cong"), ("G4", "ky_so_cai"), ("G10", "ky_so_cai")], thu_tu
    m = {(x["gate"], x["loai"]): x for x in g["muc"]}
    g1 = m[("G1", "chot_cong")]
    assert g1["ky_duoc_ngay"] and g1["dau_noi_dung"] == "abcdef0123456789" and g1["vai"] == ["PI"]
    assert {"tep": f"G1_A2_PROTOCOL_CORE_{STUDY}.md", "sha256": _sha(od / f"G1_A2_PROTOCOL_CORE_{STUDY}.md")} \
        in g1["tai_lieu"]
    g2 = m[("G2", "ky_so_cai")]
    assert not g2["ky_duoc_ngay"] and "G1 khoá trước" in g2["dieu_kien"]
    assert any("quyết định chấp thuận" in x for x in g2["dieu_kien"]) and "trinh_ky_cong.py" in g2["lenh"][0]
    ps = m[("G3", "duyet_cong_thuc_phai_sinh")]
    assert ps["vai"] == ["THONG_KE_VIEN"] and "--bien PhieuHopLe" in ps["lenh"][0] and ps["ky_duoc_ngay"]
    assert "--ap-dung" not in ps["lenh"][0].split("#")[0], "lệnh mẫu chạy khô trước — người duyệt tự thêm --ap-dung"
    g4 = m[("G4", "ky_so_cai")]
    assert [x.split("--reviewer-role ")[1].split()[0] for x in g4["lenh"]] == ["STATISTICIAN", "PI"]
    assert all(f"--artifact exports/{STUDY}/G4_A5_SAP_FINAL_{STUDY}.md" in x for x in g4["lenh"])
    g10 = m[("G10", "ky_so_cai")]
    assert any("sổ đọc" in x and "0/10" in x for x in g10["dieu_kien"])
    assert "G9 khoá trước" in g10["dieu_kien"], "mục đích chưa chọn ⇒ G10 đòi đủ G0–G9 (bi quan)"
    assert any(t["tep"] == f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md" for t in g10["tai_lieu"])
    md = DGK.goi_ky_md({**g, "khau": []})
    assert "KÝ ĐƯỢC NGAY" in md and "CHỜ ĐIỀU KIỆN" in md and "phần của" not in md.lower()
    assert "không ký, không ghi sổ cái, không bật cờ xác nhận" in md


def test_goi_ky_bo_cong_da_khoa_va_tach_sau_trien_khai(tmp_path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    monkeypatch.setattr(DGK, "_cham_cong_thuong", lambda gate, study, out_dir: {"dau": None, "muc": []})
    b = _bdm()
    b["cong"][1]["da_khoa"] = True
    b["cong"][6]["da_khoa"] = True  # G6 khoá (ngoài thứ tự) — không liệt kê lại
    ctx.kq["khau_dang_mo"] = {"du_lieu": b}
    g = DGK.lap_goi_ky(ctx)
    assert "G1" not in [x["gate"] for x in g["muc"]] and "G1" in g["da_khoa"]
    assert [x["gate"] for x in g["sau_trien_khai"]] == ["G5", "G7", "G8", "G9"]
    assert not {"G5", "G7", "G8", "G9"} & {x["gate"] for x in g["muc"]}, "cổng sau triển khai không vào gói trình"


def test_chay_du_khau_thi_ghi_goi_ky_va_cat_bao_cao_dung_cu(tmp_path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    ra = ctx.out_dir / DGK.THU_MUC_RA
    ra.mkdir(parents=True)
    (ra / f"DUNG_GOI_KY_{STUDY}.md").write_text("dừng cũ", encoding="utf-8", newline="\n")
    monkeypatch.setattr(DGK, "lap_goi_ky", lambda c: {"schema": DGK.SCHEMA, "study": STUDY, "ngay_dung": "x",
                                                       "da_khoa": [], "muc": [], "ho_so_don_vi": [],
                                                       "sau_trien_khai": [], "khau": [], "ranh_gioi": "r"})
    kq = DGK.chay(ctx, [("k1", _khau_gia("k1", True))])
    assert kq["ma_thoat"] == 0 and (ra / f"GOI_KY_{STUDY}.json").is_file() and (ra / f"GOI_KY_{STUDY}.md").is_file()
    assert not (ra / f"DUNG_GOI_KY_{STUDY}.md").exists(), "báo cáo dừng của lượt trước phải rời khỏi chỗ hiện hành"


def test_main_tham_so_sai() -> None:
    assert DGK.main(["--study", "khong-co-de-tai-nay-20261123"]) == 3
    assert DGK.main(["--study", "../ngoai"]) == 3


def test_g10_trinh_hoi_dong_chi_dua_g0_g4_va_vai_tu_bang_trach_nhiem(tmp_path, monkeypatch) -> None:
    """ETHICS_SUBMISSION: G10 chỉ đòi G0–G4, G2/G4 ở mức READY; vai cổng thường lấy từ bảng trách nhiệm."""
    ctx = _ctx(tmp_path)
    (ctx.out_dir / "G10_RELEASE_READINESS.json").write_text(json.dumps({"release": {"purpose": "ETHICS_SUBMISSION"}}),
                                                            encoding="utf-8", newline="\n")
    monkeypatch.setattr(DGK, "_cham_cong_thuong", lambda gate, study, out_dir: {"dau": None, "muc": []})
    monkeypatch.setattr(DGK, "_vai_cong_thuong", lambda gate, study, out_dir: ["PI", "THONG_KE_VIEN"])
    b = _bdm()
    b["cong"][4]["muc"] = "READY"  # G4 sẵn sàng
    ctx.kq["khau_dang_mo"] = {"du_lieu": b}
    ctx.kq["kiem_de_cuong"] = {"du_lieu": {"so_doc": {"tong": 4, "da_doc": 4}}}
    g = DGK.lap_goi_ky(ctx)
    m = {(x["gate"], x["loai"]): x for x in g["muc"]}
    g10 = m[("G10", "ky_so_cai")]
    assert g10["muc_dich"] == "ETHICS_SUBMISSION"
    assert not any(x.startswith(("G5", "G6", "G7", "G8", "G9")) for x in g10["dieu_kien"]), g10["dieu_kien"]
    assert "G2 sẵn sàng (READY) hoặc đã khoá" in g10["dieu_kien"] and "G1 khoá trước" in g10["dieu_kien"]
    assert not any(x.startswith("G4") for x in g10["dieu_kien"]), "G4 đã READY — đủ cho gói trình Hội đồng"
    assert not any("sổ đọc" in x for x in g10["dieu_kien"]), "sổ đọc phủ đủ ⇒ không còn điều kiện đó"
    assert m[("G3", "chot_cong")]["vai"] == ["PI", "THONG_KE_VIEN"]
