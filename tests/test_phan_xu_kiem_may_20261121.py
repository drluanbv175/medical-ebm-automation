"""Dựng lại lớp kiểm máy sau khi phân xử 99 phát hiện C1a/BTM bằng toàn văn (21/11/2026).

Bác sĩ 21/11/2026: «không phải tìm và bắt tôi phải đi tìm lại chứng cứ và duyệt lại»; «việc chính của tôi là lấy số
liệu và cung cấp số liệu thật». Đối chiếu toàn văn cho thấy đa số phát hiện là máy báo nhầm vì lỗi của chính lớp kiểm:
(1) chữ Việt Crossref không ở dạng NFC ⇒ cờ «can_cu_khong_khop» giả; (2) cờ số bắt «KTC 95%», số của mệnh đề khác,
số viết bằng chữ; (3) lớp toàn văn lẫn số TLTK đề cương với số trong danh mục của bài; (4) phiếu bỏ qua kết quả lớp toàn
văn; (5) mục còn lại không có đường phân xử nào ngoài bác sĩ. Mỗi ca dưới đây khoá một lỗi THẬT.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import api_claude_nc as API  # noqa: E402
import duyet_kiem_may_api as DKM  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import kiem_trich_dan_toan_van as KTV  # noqa: E402


# ── (1) Unicode tiếng Việt ───────────────────────────────────────────────────────────────────────────────────────────
def test_trich_nfc_khop_nguon_crossref_dang_to_hop():
    """Ca thật: tiêu đề bài BV TƯQĐ 108 (doi:10.52163/yhc.v64i1.573) Crossref trả dạng tổ hợp (NFD)."""
    trich = "Đánh giá sự hài lòng của người bệnh về chất lượng dịch vụ tại khoa Khám bệnh đa khoa"
    nguon = unicodedata.normalize("NFD", "Tiêu đề.\n" + trich + ", Bệnh viện Trung ương Quân Đội 108")
    assert not unicodedata.is_normalized("NFC", nguon)
    assert API.co_nguyen_van(unicodedata.normalize("NFC", trich), nguon)


def test_trich_tu_viet_lai_van_bi_chan():
    assert not API.co_nguyen_van("Đánh giá mức hài lòng của bệnh nhân", unicodedata.normalize("NFD", "Đánh giá sự hài "
                                                                                              "lòng của người bệnh"))


# ── (2) Cờ số liệu ───────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("doan", [
    "tính tỷ lệ đồng thuận tuyệt đối kèm KTC 95% Wilson [53]",
    "và giới hạn đồng thuận 95% Bland–Altman [57]",
    "báo cáo 95% CI cho mọi ước lượng [12]",
])
def test_muc_tin_cay_95_khong_la_so_lieu(doan):
    assert "95" not in KND.so_lieu(doan)


def test_ty_le_95_phan_tram_van_la_so_lieu():
    assert "95" in KND.so_lieu("95% người bệnh được xét nghiệm creatinin [7]")


def test_so_cua_menh_de_khac_khong_quy_cho_tai_lieu():
    """Ca thật BTM mục 60: hai số đầu thuộc mệnh đề không có trích dẫn."""
    doan = ("Ở Việt Nam, các nghiên cứu đo tỷ lệ BTM (15,32% đến 31,1%) hoặc mô tả kê đơn; trong phạm vi đã tra chỉ "
            "thấy một nghiên cứu đo tỷ lệ làm UACR, ở người tăng huyết áp nội trú (34,3%, [4]).")
    assert KND.so_lieu(KND.phan_cua_tai_lieu(doan)) == ["34.3"]


def test_dau_cham_phay_trong_ngoac_khong_cat_menh_de():
    doan = "ICC chọn thận trọng theo phân bố (trung vị 0,010; khoảng tứ phân vị 0–0,032) [12]"
    assert "0.010" in KND.so_lieu(KND.phan_cua_tai_lieu(doan))


def test_so_viet_bang_chu_trong_abstract():
    """Ca thật BTM mục 3: «Sixty percent of patients…»."""
    assert KND.so_co_trong("60", "Sixty percent of patients with CKD received SGLT2i")
    assert not KND.so_co_trong("60", "sixty-five patients")
    assert not KND.so_co_trong("60", "fifty patients")


# ── (3) Lớp toàn văn: che số TLTK của đề cương ───────────────────────────────────────────────────────────────────────
def test_che_so_tltk():
    cau = "Hiệu ứng sàn–trần trên 15% là hạn chế đo lường [45]; COSMIN [36, 47]; khoảng [2–4]; nguồn khác [12]."
    assert KTV.che_so_tltk(cau, 45).count("[tài liệu đang kiểm]") == 1
    ra = KTV.che_so_tltk(cau, 36)
    assert "[tài liệu đang kiểm, tài liệu khác]" in ra and "[45]" not in ra and "[12]" not in ra
    assert "[tài liệu đang kiểm, tài liệu khác]" in KTV.che_so_tltk(cau, 3)


def test_cap_can_xem_khong_gui_so_tltk():
    bc = {"cau": [{"id": "C068", "cau": "tỷ lệ trên 15% được ghi nhận là hạn chế đo lường [45]."}],
          "ket_qua": [{"id": "C068", "so": 45, "muc": "ho_tro_mot_phan", "co": []}]}
    cap = KTV.cap_can_xem(bc)
    assert cap[0]["cau"].endswith("[tài liệu đang kiểm].") and "[45]" not in cap[0]["cau"]


def test_loi_dan_hai_lop_co_luat_phan_de_cuong_tu_dat():
    for he in (KND.HE_THONG, KTV.HE_THONG):
        assert "quyết định RIÊNG của đề cương" in he
    assert "danh mục tài liệu của chính bài" in KTV.HE_THONG


# ── (4)(5) Phiếu gộp lớp toàn văn · phân xử của agent ────────────────────────────────────────────────────────────────
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture
def goc(tmp_path):
    d = tmp_path / "exports" / "S1"
    (d / "kiem_may_api").mkdir(parents=True)
    tep = d / "DE_CUONG_NOP_HOI_DONG_S1.md"
    tep.write_text("đề cương\n", encoding="utf-8", newline="\n")
    bc = {"tep": tep.name, "tep_sha256": _sha(tep), "luc": "2026-11-21T09:00:00",
          "cau": [{"id": f"C00{i}", "cau": f"câu {i} [{i}]"} for i in (1, 2, 3)],
          "ket_qua": [{"id": "C001", "so": 1, "muc": "ho_tro_mot_phan", "co": [], "ly_do": "thiếu chi tiết"},
                      {"id": "C002", "so": 2, "muc": "can_xem", "co": ["can_cu_khong_khop"], "ly_do": "khớp"},
                      {"id": "C003", "so": 3, "muc": "khong_ho_tro", "co": [], "ly_do": "khác"}]}
    (d / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").write_text(json.dumps(bc, ensure_ascii=False),
                                                                    encoding="utf-8", newline="\n")
    return tmp_path


def _ghi_toan_van(goc, a12_luc, ket):
    p = goc / "exports" / "S1" / "kiem_may_api" / "A12_TOAN_VAN_S1.json"
    p.write_text(json.dumps({"a12_luc": a12_luc, "ket_qua": ket}, ensure_ascii=False), encoding="utf-8", newline="\n")


def test_toan_van_ho_tro_la_da_giai_quyet(goc):
    _ghi_toan_van(goc, "2026-11-21T09:00:00", [
        {"id": "C002", "so": 2, "muc_toan_van": "ho_tro", "ly_do": "khớp 433 người", "nguon": "EndNote"},
        {"id": "C003", "so": 3, "muc_toan_van": "khong_ho_tro", "ly_do": "lẫn số", "nguon": "PDF"}])
    x = DKM.doc_bao_cao("S1", goc)["A12"]
    khoa = [m["khoa"] for m in x["muc"]]
    assert khoa == ["A12|C001|1", "A12|C003|3"] and x["giai_quyet_toan_van"] == 1
    m3 = next(m for m in x["muc"] if m["khoa"] == "A12|C003|3")
    assert any(c.startswith("Toàn văn: «khong_ho_tro»") for c in m3["chi_tiet"])


def test_toan_van_cua_luot_khac_khong_duoc_gop(goc):
    _ghi_toan_van(goc, "2026-11-20T09:00:00", [{"id": "C002", "so": 2, "muc_toan_van": "ho_tro"}])
    assert len(DKM.doc_bao_cao("S1", goc)["A12"]["muc"]) == 3


def _tep_phan_xu(tmp_path, muc, nguoi="agent — đối chiếu toàn văn"):
    p = tmp_path / "px.json"
    p.write_text(json.dumps({"nguoi_phan_xu": nguoi, "muc": muc}, ensure_ascii=False), encoding="utf-8", newline="\n")
    return p


MUC_HOP_LE = [
    {"so": 1, "ket_luan": "may_dung", "hanh_dong": "da_sua", "ly_do": "tách nguồn", "can_cu": "«waiting time»"},
    {"so": 2, "ket_luan": "may_sai", "hanh_dong": "khong_can_sua", "ly_do": "NFC", "can_cu": "tiêu đề Crossref"},
    {"so": 3, "ket_luan": "chua_du_can_cu", "hanh_dong": "khong_can_sua", "ly_do": "toàn văn đóng"},
]


def test_phan_xu_ghi_va_do_ty_le_dung_ghi_ro_nguon(goc, tmp_path):
    DKM.dung_phieu("S1", goc)
    assert DKM.main(["phan-xu", "--study", "S1", "--tu", str(_tep_phan_xu(tmp_path, MUC_HOP_LE))], goc=goc) == 0
    assert not DKM.tep_phan_xu("S1", goc).exists()  # chạy khô không ghi
    DKM.main(["phan-xu", "--study", "S1", "--tu", str(_tep_phan_xu(tmp_path, MUC_HOP_LE)), "--ap-dung"], goc=goc)
    d = json.loads(DKM.tep_phan_xu("S1", goc).read_text(encoding="utf-8"))
    assert "không phải nhãn bác sĩ" in d["ghi_chu"]
    t = DKM.tinh_trang("S1", goc)
    tong = t["do_dung"]["tong"]
    assert tong["ty_le_dung"] == 0.5 and tong["khong_ro"] == 1 and tong["nguon_phan_xu"] == 3
    assert tong["nguon_bac_si"] == 0 and DKM.ma_thoat([t]) == 0
    assert not DKM.tep_duyet("S1", goc).exists()  # phân xử KHÔNG bao giờ ghi vào tệp nhãn bác sĩ


def test_nhan_bac_si_di_truoc_phan_xu(goc, tmp_path):
    DKM.dung_phieu("S1", goc)
    DKM.main(["phan-xu", "--study", "S1", "--tu", str(_tep_phan_xu(tmp_path, MUC_HOP_LE)), "--ap-dung"], goc=goc)
    DKM.ghi_nhan("S1", "2 đúng", ap_dung=True, goc=goc)
    tong = DKM.tinh_trang("S1", goc)["do_dung"]["tong"]
    assert tong["nguon_bac_si"] == 1 and tong["dung"] == 2 and tong["sai"] == 0


def test_bao_cao_chay_lai_thi_phan_xu_cu_het_hieu_luc(goc, tmp_path):
    DKM.dung_phieu("S1", goc)
    DKM.main(["phan-xu", "--study", "S1", "--tu", str(_tep_phan_xu(tmp_path, MUC_HOP_LE)), "--ap-dung"], goc=goc)
    p = goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json"
    bc = json.loads(p.read_text(encoding="utf-8"))
    bc["luc"] = "2026-11-22T09:00:00"
    p.write_text(json.dumps(bc, ensure_ascii=False), encoding="utf-8", newline="\n")
    t = DKM.tinh_trang("S1", goc)
    assert t["do_dung"]["tong"]["chua_duyet"] == 3 and DKM.ma_thoat([t]) == 1


@pytest.mark.parametrize("muc,nguoi,thong_bao", [
    ([{"so": 2, "ket_luan": "may_sai", "hanh_dong": "da_sua", "ly_do": "x", "can_cu": "y"}], "agent", "da_sua"),
    ([{"so": 1, "ket_luan": "may_dung", "hanh_dong": "da_sua", "ly_do": "x"}], "agent", "can_cu"),
    ([{"so": 1, "ket_luan": "may_dung", "hanh_dong": "da_sua", "can_cu": "y"}], "agent", "ly_do"),
    ([{"so": 9, "ket_luan": "may_dung", "hanh_dong": "da_sua", "ly_do": "x", "can_cu": "y"}], "agent", "không có"),
    ([{"so": 1, "ket_luan": "dung", "hanh_dong": "da_sua", "ly_do": "x", "can_cu": "y"}], "agent", "ket_luan"),
    (MUC_HOP_LE, "bác sĩ Luận", "vai bác sĩ"),
    (MUC_HOP_LE, "", "nguoi_phan_xu"),
])
def test_phan_xu_sai_luat_bi_tu_choi(goc, tmp_path, muc, nguoi, thong_bao):
    DKM.dung_phieu("S1", goc)
    du_lieu = json.loads(_tep_phan_xu(tmp_path, muc, nguoi).read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match=thong_bao):
        DKM.ghi_phan_xu("S1", du_lieu, ap_dung=True, goc=goc)
    assert not DKM.tep_phan_xu("S1", goc).exists()


def test_phieu_noi_ro_bac_si_khong_phai_tra_loi(goc):
    md, _, n = DKM.dung_phieu("S1", goc)
    noi_dung = md.read_text(encoding="utf-8")
    assert n == 3 and "Bác sĩ KHÔNG phải" in noi_dung and "phan-xu" in noi_dung
