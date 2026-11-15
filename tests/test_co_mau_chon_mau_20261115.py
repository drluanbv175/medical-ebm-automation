"""Đồng bộ CỠ MẪU & KỸ THUẬT CHỌN MẪU thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Hãy kiểm tra và đánh giá sự đồng bộ Tính Cỡ Mẫu & Kỹ Thuật Chọn Mẫu một cách trung thực nhất và hoàn
thiện cho tôi» rồi «Với mỗi vấn đề xây dựng và hoàn thiện phải được cập nhật vào hệ thống của tôi để sau đó tất cả các
vấn đề phải được thực hiện sự đồng bộ thống nhất». Phép kiểm tay trên C1a/BTM (tính lại n₀/DE/N cần, rà mọi văn bản, đối
chiếu kỹ thuật chọn mẫu) nay là ba trục của `nhat_quan_xuyen_cong` + hai chỗ vá ở trục chùm. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import nhat_quan_xuyen_cong as NQ  # noqa: E402

STUDY = "CM-THU"


def _meta(**g3) -> dict:
    co_ban = {"hypothesis_type": "descriptive_precision", "prevalence": 0.5, "precision": 0.05, "dropout": 0.15,
              "icc": 0.02, "cluster_size": 20, "cluster_size_cv": 0.14, "n_clusters": 50, "confirmed_n": 1000}
    return {"gate_params": {"G1": {"sampling_design": ["he_thong", "phan_tang", "cum"],
                                   "recruitment_strategy": "Chọn mẫu hệ thống phân tầng theo ngày × khung giờ"},
                            "G3": {**co_ban, **g3}}}


def _cp(d: Path, **ghi) -> None:
    cp = {"alpha": 0.05, "n_total_truoc_de": 385, "n_total": 535, "n_adjusted": 630, "design_effect": 1.38784, **ghi}
    (d / "G3_checkpoint.json").write_text(json.dumps(cp), encoding="utf-8", newline="\n")


def _ghi(d: Path, ten: str, noi_dung: str) -> None:
    (d / ten).write_text(noi_dung, encoding="utf-8", newline="\n")


DC_DUNG = ("Áp dụng phương pháp chọn mẫu hệ thống phân tầng; gom cụm theo bàn khám. Cỡ mẫu 1.000, hiệu ứng thiết kế "
           "DE = 1,39, cỡ mẫu tối thiểu là 535/0,85 = 630. Với CV = 1,0, DE = 1,78 và cỡ mẫu tối thiểu là 808.\n")
SAP_DUNG = "N tối thiểu theo thống kê: 630 (độ nhạy 808). Trọng số hậu phân tầng; SE theo chùm `ma_ban_kham`. DE 1,39\n"


# ── ① tính lại cỡ mẫu ───────────────────────────────────────────────────────────────────────────────────────────────
def test_tinh_lai_khop_khi_g3_sap_de_cuong_cung_so(tmp_path):
    _cp(tmp_path)
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG)
    k = NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(), SAP_DUNG)
    assert k["muc"] == NQ.MUC_KHOP and "N cần 630" in k["ghi_chu"]


def test_tinh_lai_checkpoint_sai_so_hoc_la_lech_cung(tmp_path):
    _cp(tmp_path, n_adjusted=600, design_effect=1.25)
    k = NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(), "")
    assert k["muc"] == NQ.MUC_LECH_CUNG
    assert "n_adjusted = 600" in k["ghi_chu"] and "design_effect" in k["ghi_chu"]


def test_tinh_lai_n_chot_nho_hon_n_can(tmp_path):
    _cp(tmp_path)
    assert NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(confirmed_n=500), "")["muc"] == NQ.MUC_LECH_CUNG
    k = NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(confirmed_n=500,
                                                        underpowered_acceptance_justification="PI chấp nhận vì …"), "")
    assert k["muc"] == NQ.MUC_LECH_MEM  # có giải trình chấp nhận thiếu lực ⇒ chờ chủ nhiệm, không chặn cứng


def test_tinh_lai_van_ban_ghi_n_toi_thieu_khac_la_lech_mem(tmp_path):
    _cp(tmp_path)
    k = NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(), "N tối thiểu 808 (CV 1,0)\n")  # chỉ còn số độ nhạy cũ
    assert k["muc"] == NQ.MUC_LECH_MEM and "SAP" in k["ghi_chu"]


def test_tinh_lai_khong_ap_dung_cho_thiet_ke_so_sanh(tmp_path):
    _cp(tmp_path)
    assert NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(hypothesis_type="superiority"), "") is None


def test_tinh_lai_khong_cum_khong_khong_dap_ung(tmp_path):
    # BTM: p 0,5 · d 0,05 · không cụm · không không-đáp-ứng ⇒ 385
    _cp(tmp_path, n_total=385, n_adjusted=385, design_effect=None)
    k = NQ._truc_tinh_lai_co_mau(tmp_path, STUDY, _meta(icc=None, cluster_size=None, cluster_size_cv=None, dropout=0,
                                                        confirmed_n=None), "")
    assert k["muc"] == NQ.MUC_KHOP and "N cần 385" in k["ghi_chu"]


# ── ② kỹ thuật chọn mẫu ──────────────────────────────────────────────────────────────────────────────────────────────
def test_ky_thuat_khop(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG)
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)["muc"] == NQ.MUC_KHOP


def test_ky_thuat_thieu_trong_de_cuong_va_sap_la_can_xem(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", "Chọn mẫu hệ thống phân tầng.\n")  # không nhắc gom cụm
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), "Phân tích mô tả.\n")  # SAP không nhắc tầng/chùm
    assert k["muc"] == NQ.MUC_CAN_XEM
    assert "đề cương nộp không nhắc cum" in k["ghi_chu"] and "SAP không nhắc phan_tang, cum" in k["ghi_chu"]


def test_ky_thuat_cach_chon_khac_ma_g1(tmp_path):
    them = "Đối tượng được chọn mẫu ngẫu nhiên đơn từ danh sách.\n"
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG + them)
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)["muc"] == NQ.MUC_LECH_MEM


def test_ky_thuat_phi_xac_suat_la_lech_cung_tru_phu_dinh_va_thuat_lai(tmp_path):
    dc = tmp_path / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    _ghi(tmp_path, dc.name, DC_DUNG + "Người bệnh được chọn mẫu thuận tiện tại quầy.\n")
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)["muc"] == NQ.MUC_LECH_CUNG
    _ghi(tmp_path, dc.name, DC_DUNG + "Cách này không dùng chọn mẫu thuận tiện.\n")
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)["muc"] == NQ.MUC_KHOP
    thuat_lai = "Thuyết minh đã nộp ghi phương pháp là chọn mẫu thuận tiện. Đề cương cụ thể hoá.\n"
    _ghi(tmp_path, dc.name, DC_DUNG + thuat_lai)
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)
    assert k["muc"] == NQ.MUC_CAN_XEM and "thuật lại" in k["ghi_chu"]
    # 15/11/2026: đoạn thuật lại TỰ giải trình (đổi + lý do — như đề cương C1a §4.4.3) ⇒ không «cần xem» mãi
    co_ly_do = ("Thuyết minh đã nộp ghi phương pháp là chọn mẫu thuận tiện. Đề cương cụ thể hoá bằng khung phân tầng, "
                "theo hướng chặt chẽ hơn vì thời gian chờ thay đổi theo giờ khám.\n")
    _ghi(tmp_path, dc.name, DC_DUNG + co_ly_do)
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)
    assert k["muc"] == NQ.MUC_KHOP and "ĐÃ giải trình" in k["ghi_chu"]
    _ghi(tmp_path, dc.name, DC_DUNG + co_ly_do.replace("cụ thể hoá", "cụ thể hóa"))  # cách bỏ dấu cũ (đề cương C1a)
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, _meta(), SAP_DUNG)["muc"] == NQ.MUC_KHOP


def test_ky_thuat_g1_chua_khai_la_chua_du(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG)
    meta = _meta()
    meta["gate_params"]["G1"]["sampling_design"] = []
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, meta, SAP_DUNG)["muc"] == NQ.MUC_CHUA_DU


def test_ky_thuat_ngau_nhien_don_btm(tmp_path):
    meta = _meta()
    meta["gate_params"]["G1"] = {"sampling_design": ["ngau_nhien_don"],
                                 "recruitment_strategy": "Chọn mẫu NGẪU NHIÊN ĐƠN ở cấp người bệnh"}
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, STUDY, meta, "§7 Chọn mẫu: chọn mẫu ngẫu nhiên đơn từ toàn bộ khung\n")
    assert k["muc"] == NQ.MUC_KHOP  # chữ HOA vẫn nhận; SAP không buộc nhắc tầng/chùm khi thiết kế không có


# ── ③ tài liệu nộp ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_tai_lieu_nop_thieu_de_hien_hanh_la_lech_mem_tru_ban_cu_da_danh_dau(tmp_path):
    _cp(tmp_path)
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG)
    cu = f"Bai-bao-giao-thuc_{STUDY}.md"
    _ghi(tmp_path, cu, "Cỡ mẫu 1000. Hiệu ứng thiết kế 1 + (m − 1)·ICC, độ chính xác ±4% đến ±6%.\n")
    k = NQ._truc_tai_lieu_nop(tmp_path, STUDY, _meta())
    assert k["muc"] == NQ.MUC_LECH_MEM and cu in k["ghi_chu"] and "1,39" in k["ghi_chu"]
    _ghi(tmp_path, cu, "> **BẢN CŨ — ĐÃ THAY BẰNG** DE_CUONG_NOP_HOI_DONG_CM-THU.md\n\n"
                       "Cỡ mẫu 1000. Hiệu ứng thiết kế ICC.\n")
    k = NQ._truc_tai_lieu_nop(tmp_path, STUDY, _meta())
    assert k["muc"] == NQ.MUC_KHOP and "bỏ qua bản cũ" in k["ghi_chu"]


def test_tai_lieu_nop_ghi_n_khac(tmp_path):
    _cp(tmp_path)
    _ghi(tmp_path, f"DE_CUONG_THONG_NHAT_{STUDY}.md", "Cỡ mẫu 800 người, DE 1,39.\n")
    k = NQ._truc_tai_lieu_nop(tmp_path, STUDY, _meta())
    assert k["muc"] == NQ.MUC_LECH_MEM and "không ghi N đã chốt 1000" in k["ghi_chu"]


def test_tai_lieu_nop_khong_co_tep_la_none(tmp_path):
    _cp(tmp_path)
    assert NQ._truc_tai_lieu_nop(tmp_path, STUDY, _meta()) is None


def test_mau_so_nhan_dau_nghin_va_khong_nhan_so_dai_hon():
    import re
    assert re.search(NQ._mau_so(1000), "cỡ mẫu 1.000 phiếu") and re.search(NQ._mau_so(1000), "n = 1000")
    assert not re.search(NQ._mau_so(630), "6300 lượt") and not re.search(NQ._mau_so(630), "0,630")
    assert not re.search(NQ._mau_so(1000), "10000 lượt") and not re.search(NQ._mau_so(1000), "21.000 phiếu")


# ── ④ trục chùm: mọi DE trong SAP phải hợp lệ; K×m ≠ N là lệch ─────────────────────────────────────────────────────
TD = {"ma_ban_kham": {}, "tuoi": {}}


def test_chum_de_la_trong_sap_bi_bat_du_co_de_dung(tmp_path):
    sap = "SE theo chùm (`ma_ban_kham`). DE 1,39; độ nhạy DE 1,78.\n"
    assert NQ._truc_chon_mau(_meta(), sap, TD)["muc"] == NQ.MUC_KHOP
    k = NQ._truc_chon_mau(_meta(), sap + "Bản cũ ghi DE = 1,55.\n", TD)  # luật cũ any() để lọt
    assert k["muc"] == NQ.MUC_LECH_MEM and "1.55" in k["ghi_chu"]


def test_chum_k_nhan_m_khac_n_la_lech_mem():
    sap = "SE theo chùm (`ma_ban_kham`). DE 1,39\n"
    k = NQ._truc_chon_mau(_meta(n_clusters=40), sap, TD)  # 40 × 20 = 800 ≠ 1000
    assert k["muc"] == NQ.MUC_LECH_MEM and "800" in k["ghi_chu"]


# ── ⑤ nối vào doi_chieu + cổng chịu trách nhiệm ──────────────────────────────────────────────────────────────────────
def test_truc_moi_co_cong_chu_va_nam_trong_doi_chieu(tmp_path):
    for ma in ("co_mau_tinh_lai", "ky_thuat_chon_mau", "tai_lieu_nop_co_mau"):
        assert ma in NQ.TRUC_CHUOI and NQ.TRUC_THEO_CONG.get(ma), ma
    assert "G3" in NQ.TRUC_THEO_CONG["co_mau_tinh_lai"] and "G1" in NQ.TRUC_THEO_CONG["ky_thuat_chon_mau"]
    _cp(tmp_path)
    _ghi(tmp_path, "study_meta.json", json.dumps(_meta()))
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DC_DUNG + "Đối tượng được chọn mẫu thuận tiện.\n")
    ket = NQ.doi_chieu(tmp_path, STUDY)
    ma = {t["ma"]: t["muc"] for t in ket["thong_so"]}
    assert ma.get("co_mau_tinh_lai") == NQ.MUC_KHOP and ma.get("ky_thuat_chon_mau") == NQ.MUC_LECH_CUNG
    assert NQ.tieu_chi_g10(ket)[0] == "BLOCK"
