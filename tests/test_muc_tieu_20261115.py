"""Giai đoạn «Xác định mục tiêu nghiên cứu» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Tiếp tục các giai đoạn còn lại … đảm bảo sự đồng bộ xuyên suốt và chính xác nhất». Đo thật: C1a và
BTM chưa có ma trận mục tiêu → biến (MT-01); dựng ma trận lộ ra (1) biến phái sinh dùng quy ước lặp «_k»
(`uacr_k_ngay`) bị MT-08 báo «biến không có» oan; (2) khung SAP trong A2 của G1 ghi cứng «Mục tiêu 1»/«Mục tiêu 2 — nếu
có» trong khi BTM có MT3 mới là phân tích; (3) chưa có luật nào đòi mỗi mục tiêu có bảng giả định trước (MT-11). Mỗi
test khoá MỘT hành vi.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT / "tests"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ma_tran_muc_tieu_bien as MT  # noqa: E402
import run_g1_auto as G1  # noqa: E402
from test_dong_bo_xuyen_cong_20261115 import BIEN_DUNG, STUDY, _de_tai, _ghi_bo_bien, _ghi_ma_tran  # noqa: E402

SAP_DU = """# SAP
### §4 PHÂN TÍCH CHÍNH
tuan_thu tuoi so_thuoc so_lan_ngay ho_tro_gd
### §5 PHÂN TÍCH ĐA BIẾN
### §11 DUMMY TABLES
**Bảng 2, Tỷ lệ tuân thủ — MT1:**
**Bảng 3, Yếu tố liên quan (Mục tiêu 2):**
"""


def _sap(d: Path, noi_dung: str = SAP_DU) -> None:
    (d / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(noi_dung, encoding="utf-8", newline="\n")


def _mt11(kq) -> list:
    return [x["noi_dung"] for x in kq["loi"] if x["ma"] == "MT-11"]


# ── ① quy ước lặp «_k» của biến phái sinh ─────────────────────────────────────────────────────────────────────────
def test_bien_nguon_lap_k_duoc_mo_rong():
    bo = {"uacr_1_ngay": {}, "uacr_2_ngay": {}, "creat_1_gt": {}}
    ps = {"uacr_mg_g_k": {}}
    assert MT._co_bien_nguon("uacr_k_ngay", bo, ps) and MT._co_bien_nguon("creat_k_gt", bo, ps)
    assert MT._co_bien_nguon("uacr_mg_g_k", bo, ps)  # tên phái sinh có «_k» đứng nguyên
    assert not MT._co_bien_nguon("hba1c_k_gt", bo, ps)  # không bản mở rộng nào có ⇒ vẫn thiếu
    assert not MT._co_bien_nguon("khong_co", bo, ps)


# ── ② MT-11: mục tiêu ↔ phân tích SAP ↔ bảng giả ────────────────────────────────────────────────────────────────────
def test_mt11_dat_khi_moi_muc_tieu_co_bang_gia_gan_nhan(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    _sap(d)
    assert _mt11(MT.kiem(d, STUDY)) == []


def test_mt11_muc_tieu_khong_co_bang_gia(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    _sap(d, SAP_DU.replace("**Bảng 3, Yếu tố liên quan (Mục tiêu 2):**\n", ""))
    loi = _mt11(MT.kiem(d, STUDY))
    assert len(loi) == 1 and "Mục tiêu 2 chưa có bảng" in loi[0]
    # bảng gắn nhãn ở phần Dự kiến kết quả của ĐỀ CƯƠNG NỘP cũng tính (C1a: SAP §11 trỏ sang Bảng 5.x đề cương)
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        "# 5. DỰ KIẾN KẾT QUẢ\n\n*Bảng 5.4. Mô hình đa biến các yếu tố liên quan (Mục tiêu 2 – phân tích chính).*\n",
        encoding="utf-8", newline="\n")
    assert _mt11(MT.kiem(d, STUDY)) == []


def test_mt11_nhan_mt1_khong_khop_mt12(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    _sap(d, SAP_DU.replace("— MT1:", "— MT12:"))
    assert any("Mục tiêu 1 chưa có bảng" in x for x in _mt11(MT.kiem(d, STUDY)))


def test_mt11_ma_tran_tro_muc_sap_khong_co(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    _sap(d, SAP_DU.replace("### §5 PHÂN TÍCH ĐA BIẾN\n", ""))
    assert any("mục SAP không có: §5" in x for x in _mt11(MT.kiem(d, STUDY)))


def test_mt11_chua_co_sap_thi_khong_bao(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    assert _mt11(MT.kiem(d, STUDY)) == []  # không đo được ≠ lỗi (MT-09 đã nói SAP vắng)


# ── ③ nhãn mục tiêu của khung SAP trong A2 (G1) ──────────────────────────────────────────────────────────────────────
def test_nhan_muc_tieu_khung_sap_theo_g1():
    def _m(ob):
        return {"gate_params": {"G1": {"objectives": ob}}}

    assert G1._nhan_muc_tieu_sap(_m(["MT1: Mô tả A", "MT2: Mô tả B", "MT3: Phân tích một số yếu tố liên quan"])) \
        == ("MT1", "MT3")
    assert G1._nhan_muc_tieu_sap(_m(["MT1 (mô tả): X", "MT2 (phân tích): Đánh giá yếu tố"])) == ("MT1", "MT2")
    assert G1._nhan_muc_tieu_sap(_m(["Mô tả tỷ lệ"]))[1].startswith("không có mục tiêu phân tích")
    assert G1._nhan_muc_tieu_sap({}) == ("mục tiêu chính", "mục tiêu phân tích — nếu có")
    src = (ROOT / "tools" / "run_g1_auto.py").read_text(encoding="utf-8")
    assert "### SAP §5 — Phân tích đa biến ({nhan_sap5})" in src and "Mục tiêu 2 — nếu có)" not in src


# ── ④ trục ma_tran_muc_tieu trong bảng đồng bộ ─────────────────────────────────────────────────────────────────────
def test_truc_ma_tran_muc_tieu(tmp_path):
    import nhat_quan_xuyen_cong as NQ

    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    meta = MT.doc_meta(d)
    assert NQ._truc_ma_tran_muc_tieu(d, STUDY, meta)["muc"] == NQ.MUC_CHUA_DU  # chưa có ma trận ≠ khớp
    _ghi_ma_tran(d)
    _sap(d, SAP_DU.replace("**Bảng 3, Yếu tố liên quan (Mục tiêu 2):**\n", ""))
    assert NQ._truc_ma_tran_muc_tieu(d, STUDY, meta)["muc"] == NQ.MUC_LECH_MEM  # MT-11 lỗi
    _sap(d)
    k = NQ._truc_ma_tran_muc_tieu(d, STUDY, meta)
    assert k["muc"] in (NQ.MUC_KHOP, NQ.MUC_CAN_XEM)
    assert NQ._truc_ma_tran_muc_tieu(d, STUDY, {"gate_params": {}}) is None  # chưa chốt mục tiêu
    assert "ma_tran_muc_tieu" in NQ.TRUC_CHUOI and NQ.TRUC_THEO_CONG["ma_tran_muc_tieu"] == ("G1", "G3", "G4", "G10")


# ── ⑤ MT-08 với biến do mô-đun chính thức của SAP tính («@mô-đun», 15/11/2026) ────────────────────────────────────
def _phai_sinh_tuan_thu(d: Path, cong_thuc: str, nguoi_duyet: str = "") -> None:
    _ghi_bo_bien(d, [b for b in BIEN_DUNG if b[0] != "tuan_thu"] + [("tt1", "text", "Câu 1", "", "integer", "")])
    (d / MT.TEP_PHAI_SINH).write_text(
        "ten_bien,nhan,kieu,bien_nguon,cong_thuc,nhan_gia_tri,nguoi_duyet\n"
        f"tuan_thu,Tuân thủ,nhị phân,tt1,{cong_thuc},0=Không; 1=Có,{nguoi_duyet}\n", encoding="utf-8", newline="\n")
    _ghi_ma_tran(d)


def _mt08(kq) -> list:
    return [(x["muc"], x["noi_dung"]) for x in kq["loi"] + kq["canh_bao"] if x["ma"] == "MT-08"]


def test_mt08_mo_dun_chinh_thuc_khong_doi_nguoi_duyet(tmp_path):
    # bien_phai_sinh xếp «@…» NGOAI_TANG, lệnh `duyet` không ghi được ⇒ chốt qua SAP G4, không qua nguoi_duyet.
    d = _de_tai(tmp_path)
    _phai_sinh_tuan_thu(d, "@g6_trong_so_survey")
    assert _mt08(MT.kiem(d, STUDY)) == []


def test_mt08_mo_dun_khong_co_that_la_loi(tmp_path):
    d = _de_tai(tmp_path)
    _phai_sinh_tuan_thu(d, "@mo_dun_khong_ton_tai")
    assert [m for m, _ in _mt08(MT.kiem(d, STUDY))] == ["loi"]


def test_mt08_cong_thuc_thuong_van_doi_nguoi_duyet(tmp_path):
    d = _de_tai(tmp_path)
    _phai_sinh_tuan_thu(d, "tt1 >= 1")
    assert [m for m, _ in _mt08(MT.kiem(d, STUDY))] == ["canh_bao"]
