"""Thiết kế HỖN HỢP định lượng–định tính trên chuỗi G0–G10 (17/11/2026).

Trước đây `mixed_methods` nằm ngoài 8 mã thiết kế ⇒ G1-AUTO-02c chặn và hệ không có đường nào cho một đề tài hỗn hợp.
Kiến trúc chọn: đề tài mang mã của CẤU PHẦN ĐỊNH LƯỢNG; cấu phần định tính + kế hoạch tích hợp khai ở
`gate_params.G1.mixed_methods` (tools/hon_hop.py). Các phép thử khoá:
  - hon_hop.kiem: đủ mục GRAMMS 1–4; mã thiết kế phải là của cấu phần định lượng;
  - G1-AUTO-02e chặn khi khối thiếu mục, G1-AUTO-02c chỉ đường cho thiết kế hỗn hợp;
  - đề cương nộp: câu thiết kế hỗn hợp + GRAMMS/COREQ, mục cấu phần định tính và tích hợp, bảng tích hợp (joint
    display) ở mục dự kiến kết quả, hướng dẫn phỏng vấn ở Phụ lục C; đề tài không khai ⇒ không có các phần này;
  - phiếu đồng ý G2 có bước phỏng vấn sâu (chỉ ghi âm khi đồng ý, từ chối phỏng vấn vẫn tham gia);
  - SAP §17 khoá kế hoạch phân tích định tính và tích hợp; bản thảo G7 dẫn GRAMMS/COREQ kèm PMID để A12 kiểm.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import g1_quality_gate as G1Q  # noqa: E402
import hon_hop as HH  # noqa: E402
import run_g2_auto as G2  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402
from test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, _de_tai  # noqa: E402

KHOI = {
    "thiet_ke": "giai_thich_tuan_tu",
    "ly_do": "Thử nghiệm không cho biết vì sao một số người không đạt kiểm soát dù nhận tin nhắn",
    "uu_tien": "dinh_luong",
    "cau_phan_dinh_tinh": {
        "muc_tieu": [2],
        "central_phenomenon": "Trải nghiệm nhận tin nhắn nhắc uống thuốc",
        "qualitative_approach": "Phân tích chủ đề theo Braun và Clarke",
        "chon_mau": "Chọn có chủ đích theo kết quả tháng 6",
        "co_mau_du_kien": "Khoảng 16–20 người",
        "data_collection_method": "Phỏng vấn sâu bán cấu trúc 30–45 phút",
        "saturation_criterion": "Ba cuộc phỏng vấn liên tiếp không có mã mới",
        "phan_tich": "Hai người mã hoá độc lập",
        "interview_guide": [{"chu_de": "Rào cản", "cau_hoi": "Điều gì khiến anh/chị quên uống thuốc?",
                             "goi_mo": ["Anh/chị có thể cho một ví dụ không?"]}]},
    "tich_hop": {"thoi_diem": "Sau khi khoá phân tích định lượng", "cach": "Kết nối theo chọn mẫu và bảng tích hợp",
                 "nguoi": "Chủ nhiệm và nghiên cứu viên định tính",
                 "chu_de": [{"chu_de": "Người không đạt kiểm soát dù nhận tin nhắn",
                             "dinh_luong": "Tỷ lệ không đạt kiểm soát nhóm can thiệp",
                             "dinh_tinh": "Rào cản uống thuốc đều đặn"}]},
}


def _meta(khoi=None, design="rct"):
    return {"gate_params": {"G1": {"design": design, **({"mixed_methods": khoi} if khoi is not None else {}),
                                   "primary_outcome": {"name": "Tỷ lệ kiểm soát huyết áp"}}}}


# ─────────────────────────────────────────────────────────────────────────────────────── hon_hop.kiem (GRAMMS)
def test_khoi_day_du_dat_va_de_tai_khong_khai_khong_bi_kiem():
    assert HH.kiem(_meta(KHOI)) == []
    assert HH.kiem(_meta()) == [] and not HH.khoi(_meta())


@pytest.mark.parametrize("sua, mau", [
    (lambda k: k.update(thiet_ke="song_song"), "thiet_ke"),
    (lambda k: k.update(ly_do=""), "ly_do"),
    (lambda k: k.update(uu_tien="khac"), "uu_tien"),
    (lambda k: k["cau_phan_dinh_tinh"].pop("saturation_criterion"), "saturation_criterion"),
    (lambda k: k["cau_phan_dinh_tinh"].update(phan_tich="[CẦN — phương pháp]"), "phan_tich"),
    (lambda k: k["tich_hop"].pop("cach"), "cach"),
    (lambda k: k["cau_phan_dinh_tinh"].pop("muc_tieu"), "muc_tieu"),
    (lambda k: k["cau_phan_dinh_tinh"].update(muc_tieu=["2"]), "muc_tieu"),
])
def test_khoi_thieu_muc_grams_bi_bao(sua, mau):
    k = copy.deepcopy(KHOI)
    sua(k)
    assert any(mau in x for x in HH.kiem(_meta(k))), mau


def test_ma_thiet_ke_phai_la_cua_cau_phan_dinh_luong():
    assert any("ĐỊNH LƯỢNG" in x for x in HH.kiem(_meta(KHOI, design="qualitative")))


def test_bang_tich_hop_tu_khai_hoac_tu_ket_cuc_chinh():
    assert HH.chu_de_tich_hop(_meta(KHOI))[0]["dinh_tinh"] == "Rào cản uống thuốc đều đặn"
    k = copy.deepcopy(KHOI)
    k["tich_hop"].pop("chu_de")
    r = HH.chu_de_tich_hop(_meta(k))[0]
    assert r["dinh_luong"] == "Tỷ lệ kiểm soát huyết áp" and r["dinh_tinh"].startswith("Trải nghiệm")


# ─────────────────────────────────────────────────────────────────────────────────────── G1
def _g1(meta, design=None):
    return G1Q.evaluate_g1_quality(design=design or {"internal_code": "rct"}, artifact_texts={}, artifact_paths={},
                                   g0_checkpoint={}, meta=meta, evidence_identifiers={})


def test_g1_auto_02e_chan_khi_khoi_hon_hop_thieu_va_dat_khi_du():
    k = copy.deepcopy(KHOI)
    k["tich_hop"] = {}
    row = next(c for c in _g1(_meta(k))["automatic_criteria"] if c["id"] == "G1-AUTO-02e")
    assert row["status"] == "BLOCK" and "tich_hop" in row["evidence"]
    row = next(c for c in _g1(_meta(KHOI))["automatic_criteria"] if c["id"] == "G1-AUTO-02e")
    assert row["status"] == "PASS"
    assert not any(c["id"] == "G1-AUTO-02e" for c in _g1(_meta())["automatic_criteria"])


def test_g1_auto_02c_chi_duong_cho_thiet_ke_hon_hop():
    r = _g1({}, design={"internal_code": "cohort", "pin_bi_tu_choi": "mixed_methods"})
    row = next(c for c in r["automatic_criteria"] if c["id"] == "G1-AUTO-02c")
    assert row["status"] == "BLOCK" and "gate_params.G1.mixed_methods" in row["action"]


# ─────────────────────────────────────────────────────────────────────────────────────── đề cương nộp
def _de_tai_hh(tmp_path, khoi=KHOI):
    d = _de_tai(tmp_path)
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    if khoi is not None:
        meta["gate_params"]["G1"]["mixed_methods"] = copy.deepcopy(khoi)
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def test_de_cuong_nop_co_thiet_ke_hon_hop_bang_tich_hop_va_huong_dan_phong_van(tmp_path):
    d = _de_tai_hh(tmp_path)
    kq = SDC.sinh(d, MA, ghi=True)
    assert kq["ma"] == 0, kq.get("loi")
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    assert "thiết kế hỗn hợp định lượng – định tính theo mô hình giải thích tuần tự" in van
    assert "GRAMMS" in van and "COREQ" in van
    assert "Cấu phần định tính và tích hợp dữ liệu" in van and "- Tiêu chí bão hoà: Ba cuộc phỏng vấn" in van
    assert "Khung bảng tích hợp kết quả định lượng và định tính" in van
    assert "| Người không đạt kiểm soát dù nhận tin nhắn | Tỷ lệ không đạt kiểm soát nhóm can thiệp |" in van
    assert "PHIẾU THU THẬP SỐ LIỆU VÀ HƯỚNG DẪN PHỎNG VẤN" in van and "**C2. CẤU PHẦN ĐỊNH TÍNH**" in van
    assert "Điều gì khiến anh/chị quên uống thuốc?" in van
    assert "(30–45 phút)" in van  # thời lượng phỏng vấn lấy từ phương pháp thu thập của cấu phần định tính


def test_de_cuong_nop_khong_khai_hon_hop_thi_khong_co_cac_phan_hon_hop(tmp_path):
    d = _de_tai_hh(tmp_path, khoi=None)
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    for cam in ("hỗn hợp", "GRAMMS", "bảng tích hợp", "C2. CẤU PHẦN ĐỊNH TÍNH"):
        assert cam not in van, cam


def test_gramms_chi_vao_tltk_khi_a12_da_xac_nhan(tmp_path):
    d = _de_tai_hh(tmp_path)
    n = SDC.Nguon(d, MA)
    assert "18416914" not in n.ung_vien  # chưa qua A12 ⇒ không dẫn
    md = json.loads((d / "A12_METADATA_RECEIPT.json").read_text(encoding="utf-8"))
    md["metadata"]["18416914"] = {"status": "resolved", "title": "The quality of mixed methods studies in health "
                                  "services research.", "authors": "O'Cathain A, Murphy E, Nicholl J",
                                  "journal": "J Health Serv Res Policy", "year": "2008"}
    (d / "A12_METADATA_RECEIPT.json").write_text(json.dumps(md), encoding="utf-8", newline="\n")
    rc = json.loads((d / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
    rc["pmids_checked"].append("18416914")
    rc["results"]["18416914"] = {"status": "ok"}
    (d / "A12_RETRACTION_RECEIPT.json").write_text(json.dumps(rc), encoding="utf-8", newline="\n")
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    assert "GRAMMS [" in van and "PMID: 18416914." in van


# ─────────────────────────────────────────────────────────────────────────────────────── G2 · G4 · G7
def test_phieu_dong_y_co_buoc_phong_van_sau_vi_en():
    vi = G2._buoc_phong_van_hon_hop(_meta(KHOI))
    assert "khoảng 30–45 phút" in vi and "chỉ được ghi âm khi anh/chị đồng ý" in vi
    assert "từ chối phần phỏng vấn mà vẫn tiếp tục tham gia" in vi
    en = G2._buoc_phong_van_hon_hop(_meta(KHOI), en=True)
    assert "about 30-45 minutes" in en and "only with your permission" in en
    assert G2._buoc_phong_van_hon_hop(_meta()) == ""


def test_sap_muc_17_khoa_ke_hoach_dinh_tinh_va_tich_hop():
    dong = "\n".join(G4.muc_hon_hop(_meta(KHOI)))
    assert "### §17 CẤU PHẦN ĐỊNH TÍNH VÀ TÍCH HỢP" in dong and "PMID 18416914" in dong
    assert "Kết nối theo chọn mẫu" in dong and "[CẦN" not in dong
    assert G4.muc_hon_hop(_meta()) == []


def test_g7_cau_thiet_ke_hon_hop_kem_pmid_gramms_coreq(tmp_path):
    (tmp_path / "study_meta.json").write_text(json.dumps(_meta(KHOI), ensure_ascii=False), encoding="utf-8",
                                               newline="\n")
    cau = G7._hon_hop_g7(tmp_path)
    assert "giải thích tuần tự" in cau and "PMID 18416914" in cau and "PMID 17872937" in cau
    (tmp_path / "study_meta.json").write_text(json.dumps(_meta()), encoding="utf-8", newline="\n")
    assert G7._hon_hop_g7(tmp_path) is None


def test_muc_tieu_dinh_tinh_vuot_so_muc_tieu_g1_bi_bao():
    m = _meta(KHOI)
    m["gate_params"]["G1"]["objectives"] = ["Mục tiêu định lượng"]
    assert any("vượt số mục tiêu" in x for x in HH.kiem(m))
    m["gate_params"]["G1"]["objectives"].append("Mục tiêu định tính")
    assert HH.kiem(m) == [] and HH.muc_tieu_dinh_tinh(m) == frozenset({2})


def test_ma_tran_khong_doi_bien_cho_muc_tieu_dinh_tinh_cua_de_tai_hon_hop(tmp_path):
    import ma_tran_muc_tieu_bien as MT

    d = _de_tai(tmp_path)
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G1"]["objectives"].append("Tìm hiểu trải nghiệm nhận tin nhắn nhắc uống thuốc")
    loi_mt3 = [x for x in MT.kiem(d, MA, meta=meta)["loi"] if x["ma"] == "MT-03"]
    assert any("Mục tiêu 2" in x["noi_dung"] for x in loi_mt3)  # chưa khai hỗn hợp ⇒ vẫn đòi biến
    meta["gate_params"]["G1"]["mixed_methods"] = copy.deepcopy(KHOI)
    loi_mt3 = [x for x in MT.kiem(d, MA, meta=meta)["loi"] if x["ma"] in ("MT-03", "MT-04")]
    assert not any("Mục tiêu 2" in x["noi_dung"] for x in loi_mt3)


def test_sap_bang_mt_cua_muc_tieu_dinh_tinh_la_bang_chu_de():
    ra = "\n".join(G4._bang_theo_muc_tieu(["So sánh tỷ lệ kiểm soát", "Tìm hiểu trải nghiệm"], frozenset({2})))
    assert "Bảng MT2" in ra and "| Chủ đề | Mô tả chủ đề |" in ra and "theo §17" in ra
    assert "Hiệu ứng thô" in ra.split("Bảng MT2")[0]


def test_g10_ma_tran_truy_xuat_co_hang_cua_muc_tieu_dinh_tinh(tmp_path, monkeypatch):
    """Đề cương lắp G10 từng in «[CẦN BỔ SUNG]» cho mục tiêu định tính (không có biến CRF) ⇒ G10-AUTO-09 chặn."""
    import run_g10_assemble as G10A

    d = _de_tai_hh(tmp_path)
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    mt = ["So sánh tỷ lệ kiểm soát huyết áp", "Tìm hiểu trải nghiệm nhận tin nhắn"]
    meta["gate_params"]["G1"]["objectives"] = mt
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    monkeypatch.setattr(G10A, "_dong_ma_tran_dat", lambda _o: [
        {"muc_tieu": "1", "bien": "kiem_soat", "kieu": "nhi_phan", "vai_tro": "ket_cuc_chinh", "cong_cu": "đo HA",
         "cau_hoi": "C1", "phan_tich_sap": "§4"}])
    van = G10A.build_traceability_matrix({}, {"objectives": mt, "aim": "Mục tiêu chung", "_g10": {"out_dir": str(d)}})
    hang = next(x for x in van.splitlines() if x.startswith("| Mục tiêu cụ thể 2"))
    assert "Chủ đề định tính: Trải nghiệm nhận tin nhắn" in hang and "SAP §17" in hang and "[CẦN" not in hang
    meta["gate_params"]["G1"].pop("mixed_methods")
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    van = G10A.build_traceability_matrix({}, {"objectives": mt, "aim": "Mục tiêu chung", "_g10": {"out_dir": str(d)}})
    assert "[CẦN" in next(x for x in van.splitlines() if x.startswith("| Mục tiêu cụ thể 2"))


# ─────────────────────────────────────────────────────────────────────────────────────── G2 đọc quyết định đã chốt
def test_g2_dang_ky_va_luu_tru_doc_quyet_dinh_da_chot():
    """G2 BTM (17/11/2026): PI chốt không đăng ký + quy trình lưu 2 năm/huỷ bảng nối mà khuôn vẫn hỏi lại."""
    risk = {"register_where": "ClinicalTrials.gov"}
    meta = {"gate_params": {"G2": {"registration_required": False,
                                   "recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}}}
    assert G2._dang_ky_tom_tat(meta, risk).startswith("Không bắt buộc đăng ký thử nghiệm — nghiên cứu hồi cứu")
    meta["gate_params"]["G2"] = {"registration_registry": "ClinicalTrials.gov", "registration_id": "NCT00000001"}
    assert G2._dang_ky_tom_tat(meta, risk) == "ClinicalTrials.gov — NCT00000001"
    assert G2._dang_ky_tom_tat({}, risk) == "[CẦN — ClinicalTrials.gov]"
    qt = [{"muc": "luu_tru", "gia_tri": "Số liệu điện tử lưu 2 năm sau khi kết thúc nghiên cứu"},
          {"muc": "huy_bang_noi", "gia_tri": "Bảng nối mã huỷ sau khi khoá dữ liệu"}]
    assert G2._thoi_gian_luu(qt) == "2 năm sau kết thúc nghiên cứu"
    assert G2._huy_dinh_danh(qt) == "Bảng nối mã huỷ sau khi khoá dữ liệu."
    assert "___" in G2._thoi_gian_luu([]) and "___" in G2._huy_dinh_danh([])
