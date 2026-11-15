"""Nhất quán xuyên cổng ĐẦY ĐỦ chuỗi + chốt máy G5-AUTO-11 + nối vào trách nhiệm cổng / hồ sơ hội đồng (15/11/2026).

Bác sĩ 15/11/2026: «Phải đạt sự đồng bộ giữa các cổng, từ vấn đề nghiên cứu … biến, công cụ nghiên cứu và đề cương
nghiên cứu» rồi «Phải đảm bảo nhất quán xuyên suốt và đồng bộ, đã có sự kiểm tra chéo, điều phối nhưng đã không thực
hiện được và được báo cáo hoàn thiện». Trước đó `nhat_quan_xuyen_cong` chỉ so 8 thông số (N, α, thiết kế…) và đồng bộ từ
điển ↔ phiếu ↔ đề cương ở G5 chỉ là ô người tự xác nhận ⇒ cổng báo «hoàn thiện» khi biến còn sai.

Mỗi test khoá MỘT hành vi: trục chuỗi đọc đúng mức (khop · lech_cung · lech_mem · can_xem · chua_du), «không đo được»
không bao giờ là «khớp», lệch cứng làm G5 BLOCKED và bảng trách nhiệm không còn DAT/AGENT_XONG, hồ sơ hội đồng mang số
đo cho RQ4.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g5_quality_gate as G5Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402

from tests.g5_test_helpers import configure_test_signing_key, prepare_locked_g5_study  # noqa: E402

STUDY = "NQ-DAY-DU"
COT = ["Variable / Field Name", "Form Name", "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
       "Text Validation Type OR Show Slider Number", "Text Validation Min", "Text Validation Max"]


def _tu_dien(d: Path, hang) -> None:
    with open(d / f"G5_REDCap_dictionary_{STUDY}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT)
        w.writeheader()
        for ten, kieu, lua_chon, kiem in hang:
            w.writerow({"Variable / Field Name": ten, "Form Name": "f", "Field Type": kieu, "Field Label": ten,
                        "Choices, Calculations, OR Slider Labels": lua_chon,
                        "Text Validation Type OR Show Slider Number": kiem})


HANG = [("record_id", "text", "", ""), ("tuoi", "text", "", "integer"), ("gioi", "radio", "1, Nam | 2, Nữ", "")]


def _bo_bien_g3(d: Path, hang) -> None:
    dong = "\n".join(f"| {t} | {t} | {loai} | {gt} |" for t, loai, gt in hang)
    (d / f"G3_BO_BIEN_SO_{STUDY}.md").write_text(
        "# Bộ biến\n\n| Tên biến | Nhãn | Loại | Giá trị hợp lệ |\n|---|---|---|---|\n" + dong + "\n",
        encoding="utf-8", newline="\n",
    )


G3_KHOP = [("tuoi", "Định lượng", "18–100"), ("gioi", "Phân loại", "1 = Nam; 2 = Nữ")]


# ── ① trục biến ↔ đề cương/bộ biến ────────────────────────────────────────────────────────────────────────────────
def test_bien_de_cuong_khong_co_nguon_chuan_la_chua_du_khong_phai_khop(tmp_path):
    _tu_dien(tmp_path, HANG)
    k = NQ._truc_bien_de_cuong(tmp_path, STUDY)
    assert k["muc"] == NQ.MUC_CHUA_DU and "không có chuẩn" in k["ghi_chu"]


def test_bien_de_cuong_khop_va_lech_nhap_lieu(tmp_path):
    _tu_dien(tmp_path, HANG)
    _bo_bien_g3(tmp_path, G3_KHOP)
    assert NQ._truc_bien_de_cuong(tmp_path, STUDY)["muc"] == NQ.MUC_KHOP
    _bo_bien_g3(tmp_path, G3_KHOP + [("hba1c", "Định lượng", "4–20")])  # bộ biến có, từ điển thiếu ⇒ mẫu nhập sai
    k = NQ._truc_bien_de_cuong(tmp_path, STUDY)
    assert k["muc"] == NQ.MUC_LECH_CUNG and "NHẬP LIỆU" in k["ghi_chu"]
    assert any("hba1c" in n["noi"] for n in k["nguon"])


def test_bien_de_cuong_sai_ma_phan_loai_la_lech_cung(tmp_path):
    _tu_dien(tmp_path, HANG)
    _bo_bien_g3(tmp_path, [("tuoi", "Định lượng", "18–100"), ("gioi", "Phân loại", "1 = Nam; 2 = Nữ; 3 = Khác")])
    assert NQ._truc_bien_de_cuong(tmp_path, STUDY)["muc"] == NQ.MUC_LECH_CUNG


# ── ② trục công cụ thu thập ↔ từ điển ─────────────────────────────────────────────────────────────────────────────
def test_cong_cu_phieu_rieng_thieu_truong_la_lech_cung(tmp_path):
    _tu_dien(tmp_path, HANG)
    td = NQ._tu_dien(tmp_path, STUDY)
    phieu = tmp_path / f"PHIEU_THU_THAP_SO_LIEU_{STUDY}.md"
    phieu.write_text("1. tuoi: ____\n2. gioi: ☐1 Nam ☐2 Nữ\n", encoding="utf-8", newline="\n")
    assert NQ._truc_cong_cu(tmp_path, STUDY, td)["muc"] == NQ.MUC_KHOP
    phieu.write_text("1. tuoi: ____\n", encoding="utf-8", newline="\n")
    k = NQ._truc_cong_cu(tmp_path, STUDY, td)
    assert k["muc"] == NQ.MUC_LECH_CUNG and "gioi" in k["nguon"][0]["gia_tri"]


def test_cong_cu_khong_co_phieu_la_chua_du(tmp_path):
    _tu_dien(tmp_path, HANG)
    assert NQ._truc_cong_cu(tmp_path, STUDY, NQ._tu_dien(tmp_path, STUDY))["muc"] == NQ.MUC_CHUA_DU
    assert NQ._truc_cong_cu(tmp_path, STUDY, {})["muc"] == NQ.MUC_CHUA_DU


def _de_cuong_phu_luc(d: Path, cau1: str, ksd_a1: str = "—") -> None:
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        "# PHỤ LỤC C. PHIẾU\n\nPHẦN 1\n\n" + f"1. Giới tính: {cau1}\n\n"
        "PHẦN 2\n\n| Mục | Nội dung | 1 | 2 | KSD |\n|---|---|---|---|---|\n"
        f"| A1 | Nhân viên niềm nở | ☐ | ☐ | {ksd_a1} |\n\nPHẦN 3\n\n"
        "# PHỤ LỤC D. KHÁC\n\n# PHỤ LỤC E. BẢNG BIẾN SỐ\n\n"
        "| Mã biến | Nhãn | Loại | Mã hoá | Nguồn |\n|---|---|---|---|---|\n"
        "| gioi | Giới tính | Phân loại | 1 = Nam; 2 = Nữ | Phiếu – câu 1 |\n",
        encoding="utf-8", newline="\n",
    )


def test_cong_cu_phu_luc_c_doi_chieu_ma_tung_cau_va_o_ksd(tmp_path):
    _tu_dien(tmp_path, HANG + [("a1", "radio", "1, Không | 2, Có | 7, Không sử dụng", "")])
    td = NQ._tu_dien(tmp_path, STUDY)
    _de_cuong_phu_luc(tmp_path, "☐ 1 Nam ☐ 2 Nữ", ksd_a1="☐")
    assert NQ._truc_cong_cu(tmp_path, STUDY, td)["muc"] == NQ.MUC_KHOP
    _de_cuong_phu_luc(tmp_path, "☐ 1 Nam ☐ 2 Nữ ☐ 3 Khác", ksd_a1="☐")  # phiếu có mã 3, từ điển không
    assert NQ._truc_cong_cu(tmp_path, STUDY, td)["muc"] == NQ.MUC_LECH_CUNG
    _de_cuong_phu_luc(tmp_path, "☐ 1 Nam ☐ 2 Nữ", ksd_a1="—")  # từ điển có mã 7 nhưng phiếu không có ô KSD
    k = NQ._truc_cong_cu(tmp_path, STUDY, td)
    assert k["muc"] == NQ.MUC_LECH_CUNG and any("KSD" in n["gia_tri"] for n in k["nguon"])


# ── ③ mục tiêu ↔ SAP · ④ chọn mẫu ↔ cỡ mẫu · ⑤ đặc tả chờ bộ biến · ⑥ tổng quan ↔ đề cương ─────────────────────
def test_muc_tieu_khong_duoc_sap_goi_ten_la_can_xem():
    meta = {"gate_params": {"G1": {"objectives": ["MT1: mô tả tỷ lệ", "MT2: xác định yếu tố liên quan"]}}}
    assert NQ._truc_muc_tieu(meta, "Phân tích cho MT1 và MT2")["muc"] == NQ.MUC_KHOP
    k = NQ._truc_muc_tieu(meta, "Phân tích cho MT1")
    assert k["muc"] == NQ.MUC_CAN_XEM and "1/2" in k["ghi_chu"]
    assert NQ._truc_muc_tieu({}, "MT1") is None  # không có mục tiêu G1 ⇒ trục không áp dụng


def _meta_chum(**g3):
    return {"gate_params": {"G1": {"sampling_design": ["cum"]}, "G3": g3}}


def test_chon_mau_chum_thieu_icc_la_lech_cung():
    assert NQ._truc_chon_mau(_meta_chum(cluster_size=20), "", {})["muc"] == NQ.MUC_LECH_CUNG


def test_chon_mau_chum_de_va_bien_chum():
    td = {"ma_ban": {}, "tuoi": {}}
    meta = _meta_chum(cluster_size=20, icc=0.02, cluster_size_cv=0.14)  # DE = 1 + ((0,14²+1)·20 − 1)·0,02 = 1,39
    assert NQ._truc_chon_mau(meta, "hiệu chỉnh chùm (`ma_ban`), DE = 1,39", td)["muc"] == NQ.MUC_KHOP
    assert NQ._truc_chon_mau(meta, "hiệu chỉnh chùm (`ma_ban`), DE = 1,80", td)["muc"] == NQ.MUC_LECH_MEM
    k = NQ._truc_chon_mau(meta, "hiệu chỉnh chùm (`vcovCL`), DE = 1,39", td)  # tên hàm R không phải biến chùm
    assert k["muc"] == NQ.MUC_LECH_CUNG
    assert NQ._truc_chon_mau({"gate_params": {"G1": {"sampling_design": ["ngau_nhien_don"]}}}, "", td) is None


def test_dac_ta_cho_bo_sung_bo_bien_la_lech_mem(tmp_path):
    assert NQ._truc_dac_ta(tmp_path) is None
    dac_ta = {"phan_tich": [{"id": "PT-01"}, {"id": "PT-07", "chua_tu_dong": "chờ bổ sung bộ biến (HbA1c 3 mức)"}]}
    (tmp_path / "G6_DAC_TA_SAP.json").write_text(json.dumps(dac_ta), encoding="utf-8", newline="\n")
    k = NQ._truc_dac_ta(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "PT-07" in k["nguon"][0]["gia_tri"]


def test_tong_quan_co_khoang_trong_ma_de_cuong_khong_co_muc_la_can_xem(tmp_path):
    # câu khoảng trống mở bằng «Chưa có…» là cách viết phổ biến — không được coi là ô trống
    meta = {"gate_params": {"G1": {"knowledge_gap": "Chưa có nghiên cứu ngoại trú tại Việt Nam"}}}
    assert NQ._truc_tong_quan(tmp_path, STUDY, {"gate_params": {"G1": {"knowledge_gap": "[CẦN PI]"}}})["muc"] \
        == NQ.MUC_CHUA_DU
    assert NQ._truc_tong_quan(tmp_path, STUDY, meta)["muc"] == NQ.MUC_CHUA_DU  # chưa có đề cương
    dc = tmp_path / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    dc.write_text("# 1. Đặt vấn đề\n\nnội dung\n", encoding="utf-8", newline="\n")
    assert NQ._truc_tong_quan(tmp_path, STUDY, meta)["muc"] == NQ.MUC_CAN_XEM
    dc.write_text("# 1. Đặt vấn đề\n\n## 1.5 Khoảng trống nghiên cứu\n\nnội dung\n", encoding="utf-8", newline="\n")
    assert NQ._truc_tong_quan(tmp_path, STUDY, meta)["muc"] == NQ.MUC_KHOP


def test_mot_truc_hong_khong_lam_mat_truc_khac(tmp_path, monkeypatch):
    _tu_dien(tmp_path, HANG)

    def hong(*_a, **_k):
        raise RuntimeError("bộ đo hỏng")

    monkeypatch.setattr(NQ, "_truc_cong_cu", hong)
    ra = NQ.truc_chuoi(tmp_path, STUDY, {}, "")
    ma = [k["ma"] for k in ra]
    assert "chuoi_loi" in ma and "bien_de_cuong" in ma
    assert next(k for k in ra if k["ma"] == "chuoi_loi")["muc"] == NQ.MUC_CHUA_DU


def test_truc_chuoi_nam_trong_doi_chieu_va_g10_khong_pass_khi_lech_cung(tmp_path):
    _tu_dien(tmp_path, HANG)
    _bo_bien_g3(tmp_path, G3_KHOP + [("hba1c", "Định lượng", "4–20")])
    ket = NQ.doi_chieu(tmp_path, STUDY)
    assert any(k["ma"] == "bien_de_cuong" and k["muc"] == NQ.MUC_LECH_CUNG for k in ket["thong_so"])
    assert NQ.tieu_chi_g10(ket)[0] == "BLOCK"


def test_moi_truc_chuoi_co_cong_chu():
    for ma in ("bien_de_cuong", "cong_cu_tu_dien", "muc_tieu_phan_tich", "chon_mau_co_mau", "dac_ta_cho_bo_bien",
               "tong_quan_khoang_trong"):
        assert NQ.TRUC_THEO_CONG.get(ma), ma
    assert "G5" in NQ.TRUC_THEO_CONG["bien_de_cuong"] and "G5" in NQ.TRUC_THEO_CONG["cong_cu_tu_dien"]


# ── ⑦ G5-AUTO-11: chốt MÁY ở cổng khoá dữ liệu ─────────────────────────────────────────────────────────────────────
def _source(path: Path) -> Path:
    path.write_text("record_id,age,sex,exposure_var,primary_outcome\nS001,45,F,0,0\nS002,52,M,1,1\n",
                    encoding="utf-8", newline="\n")
    return path


def _g5_san_sang(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    exports_root = tmp_path / "exports"
    _, report = prepare_locked_g5_study(STUDY, _source(tmp_path / "source.csv"), exports_root=exports_root,
                                        repo_root=tmp_path, approve_g5=False)
    return exports_root / STUDY, report


def _auto11(report):
    return next(c for c in report["automatic_criteria"] if c["id"] == "G5-AUTO-11")


def test_g5_auto_11_chuoi_day_du_pass_lech_cung_block_thieu_nguon_review(tmp_path, monkeypatch):
    out_dir, report = _g5_san_sang(tmp_path, monkeypatch)
    assert _auto11(report)["status"] == "PASS" and report["status"] == G5Q.STATUS_READY
    # bộ biến G3 khai thêm một biến mà từ điển không có ⇒ mẫu nhập sai ⇒ không được khoá
    g3 = out_dir / f"G3_BO_BIEN_SO_{STUDY}.md"
    goc = g3.read_text(encoding="utf-8")
    g3.write_text(goc + "| hba1c | hba1c | Định lượng | 4–20 |\n", encoding="utf-8", newline="\n")
    report = G5Q.evaluate_study(STUDY, out_dir, repo_root=tmp_path, write=False)
    assert _auto11(report)["status"] == "BLOCK" and report["status"] == G5Q.STATUS_BLOCKED
    # không còn nguồn chuẩn để so ⇒ REVIEW (không bao giờ PASS khi không đo được)
    g3.unlink()
    report = G5Q.evaluate_study(STUDY, out_dir, repo_root=tmp_path, write=False)
    assert _auto11(report)["status"] == "REVIEW" and report["status"] != G5Q.STATUS_READY


def test_g5_auto_11_bo_do_hong_la_review(tmp_path, monkeypatch):
    out_dir, _ = _g5_san_sang(tmp_path, monkeypatch)

    def hong(*_a, **_k):
        raise RuntimeError("hỏng")

    monkeypatch.setattr(NQ, "_truc_bien_de_cuong", hong)
    report = G5Q.evaluate_study(STUDY, out_dir, repo_root=tmp_path, write=False)
    assert _auto11(report)["status"] == "REVIEW" and "không đo được" in _auto11(report)["evidence"]


def test_g5_auto_11_lech_phan_tich_khong_chan_khoa_nhap_lieu(tmp_path, monkeypatch):
    # lệch PHÂN TÍCH (vd C1a NhomTuoi 3 mức ≠ đề cương 4 mức) không làm sai mẫu nhập; G6 chặn biến phái sinh chưa duyệt
    out_dir, _ = _g5_san_sang(tmp_path, monkeypatch)
    monkeypatch.setattr(NQ, "_truc_bien_de_cuong", lambda *_a, **_k: NQ._ket(
        "bien_de_cuong", "Biến ↔ đề cương/bộ biến đã duyệt", [], NQ.MUC_LECH_MEM, "1 lệch PHÂN TÍCH (giả lập)"))
    report = G5Q.evaluate_study(STUDY, out_dir, repo_root=tmp_path, write=False)
    assert _auto11(report)["status"] == "PASS" and "lech_mem" in _auto11(report)["evidence"]


def test_g5_auto_11_co_chu_trong_bang_phan_cong():
    assert HD.PHAN_CONG["G5"]["G5-AUTO-11"] == "G5-T1"


# ── ⑧ bảng trách nhiệm cổng + hồ sơ hội đồng mang số đo ────────────────────────────────────────────────────────────
def _nq_gia(muc_bien: str):
    def doi_chieu(_out_dir, _study=None):
        return {"thong_so": [
            {"ma": "bien_de_cuong", "ten": "Biến ↔ đề cương/bộ biến đã duyệt", "muc": muc_bien, "ghi_chu": "giả lập"},
            {"ma": "muc_tieu_phan_tich", "ten": "Mục tiêu ↔ SAP", "muc": "lech_cung", "ghi_chu": "không thuộc G5"}]}
    return doi_chieu


def test_nhat_quan_cua_cong_loc_theo_cong_va_bo_do_hong_la_chua_du(monkeypatch, tmp_path):
    monkeypatch.setattr(NQ, "doi_chieu", _nq_gia("khop"))
    ra = HD.nhat_quan_cua_cong(STUDY, "G5", tmp_path)
    assert [k["ma"] for k in ra] == ["bien_de_cuong"]  # mục tiêu ↔ SAP không thuộc G5

    def hong(*_a, **_k):
        raise RuntimeError("hỏng")

    monkeypatch.setattr(NQ, "doi_chieu", hong)
    ra = HD.nhat_quan_cua_cong(STUDY, "G5", tmp_path)
    assert len(ra) == 1 and ra[0]["muc"] == "chua_du"


@pytest.mark.parametrize("muc,ket_luan_cam", [("lech_cung", ("DAT_TIEU_CHI", "AGENT_XONG_CHO_NGUOI")),
                                              ("lech_mem", ("DAT_TIEU_CHI",))])
def test_trach_nhiem_g5_khong_bao_hoan_thien_khi_chuoi_lech(tmp_path, monkeypatch, muc, ket_luan_cam):
    out_dir, _ = _g5_san_sang(tmp_path, monkeypatch)
    monkeypatch.setattr(NQ, "doi_chieu", _nq_gia("khop"))
    goc = HD.trach_nhiem(STUDY, "G5", out_dir)
    assert not [m for m in goc["agent_con_viec"] if "nhat-quan" in m["id"]]
    monkeypatch.setattr(NQ, "doi_chieu", _nq_gia(muc))
    kq = HD.trach_nhiem(STUDY, "G5", out_dir)
    assert kq["ket_luan"] not in ket_luan_cam
    ds = kq["agent_con_viec"] if muc == "lech_cung" else kq["cho_nguoi"]
    muc_nq = next(m for m in ds if m["id"] == "G5:nhat-quan-bien_de_cuong")
    assert muc_nq["status"] == ("BLOCK" if muc == "lech_cung" else "REVIEW")
    assert [k["ma"] for k in kq["nhat_quan_xuyen_cong"]] == ["bien_de_cuong"]


def test_ho_so_hoi_dong_mang_so_do_nhat_quan_cho_rq4(tmp_path, monkeypatch):
    out_dir, _ = _g5_san_sang(tmp_path, monkeypatch)
    monkeypatch.setattr(NQ, "doi_chieu", _nq_gia("lech_cung"))
    hs = HD.ho_so_cong(STUDY, "G5", out_dir)
    assert hs["nhat_quan_xuyen_cong"] == [
        {"ma": "bien_de_cuong", "ten": "Biến ↔ đề cương/bộ biến đã duyệt", "muc": "lech_cung", "ghi_chu": "giả lập"}]
