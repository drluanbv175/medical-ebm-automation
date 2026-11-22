# -*- coding: utf-8 -*-
"""COREQ 2007 và SRQR 2014 bật chặn (22/11/2026) — bộ sinh viết đủ mục, giả lập đóng vai người khai.

Đo trên gói giả lập trọn vòng (bật chặn trong tiến trình đo): định tính và định tính chân thực thiếu 8 mục ở đề cương
nộp, 22 ở bản thảo, 18 ở báo cáo tổng hợp; RCT hỗn hợp thiếu ~30 mục COREQ/SRQR ở đề cương nộp (mục cấu phần định tính
mang tiêu đề bộ đo không nhận là phần nào) và ~29 ở bản thảo. Sửa tại nguồn:
- khoá quy trình định tính dùng chung (`hon_hop.KHOA_QUY_TRINH_DINH_TINH`, `hon_hop.nguon_dinh_tinh`), PI giả lập khai ở
  G1 (định tính) hoặc `mixed_methods.cau_phan_dinh_tinh` (hỗn hợp);
- đề cương nộp: ba tiểu mục mang tên đúng phần đề cương mà chuẩn đặt mục (nhóm nghiên cứu/phản tư · chọn mẫu, tiếp cận,
  thu thập · xử lý và phân tích); hạn chế và hiểu biết do kết hợp (GRAMMS 5, 6);
- bản thảo G7: câu hỏi nghiên cứu, quy trình định tính, kết quả (người được mời, từ chối kèm lý do, đặc điểm, chủ đề,
  trích lời nguyên văn từ bản gỡ băng đã khử định danh); vắng dữ kiện ⇒ ô [CẦN];
- giả lập: bản gỡ băng mang lời kể theo chủ đề (không phải nhãn mã), đề tài hỗn hợp có cấu phần định tính mô phỏng có
  kiểm soát sau khi khoá phân tích định lượng; K18 COREQ 4 đo ở Phương pháp như bảng gốc.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import gia_lap_bien_the_kho as BTK  # noqa: E402
import gia_lap_dinh_ky as GL  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402
import hon_hop as HH  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

from tests.test_g7_chuan_bao_cao_5_thiet_ke_20261122 import _ban_thao, _ghi, _meta, _nop  # noqa: E402

KHOA = [k for k, *_r in HH.KHOA_QUY_TRINH_DINH_TINH]


# ───────────────────────────── khoá dùng chung + hồ sơ giả lập ─────────────────────────────
def test_nguon_dinh_tinh_theo_loai_de_tai():
    assert HH.nguon_dinh_tinh({"gate_params": {"G1": {"design": "qualitative", "interviewer": "x"}}})["interviewer"]
    hh = {"gate_params": {"G1": {"design": "rct", "mixed_methods": {"cau_phan_dinh_tinh": {"interviewer": "y"}}}}}
    assert HH.nguon_dinh_tinh(hh) == {"interviewer": "y"}
    assert HH.nguon_dinh_tinh({"gate_params": {"G1": {"design": "cohort"}}}) == {}


def test_ho_so_gia_lap_khai_du_khoa_quy_trinh_dinh_tinh():
    g1 = GL.KICH_BAN["dinh_tinh"]["pi"]["G1"]
    cp = BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]["cau_phan_dinh_tinh"]
    for nguon in (g1, cp):
        assert all(str(nguon.get(k) or "").strip() for k in KHOA), [k for k in KHOA if not nguon.get(k)]
    th = BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]["tich_hop"]
    assert th["han_che"] and th["hieu_biet_du_kien"]


# ───────────────────────────── đề cương nộp: ba tiểu mục đúng phần ─────────────────────────────
def _de_cuong_dinh_tinh(g: dict, ten_muc: str = "Cách tiếp cận và phương pháp thu thập dữ liệu định tính") -> str:
    return ("# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC\n\n## ĐỀ TÀI THỬ\n\n## THÔNG TIN CHUNG VỀ ĐỀ TÀI\n\n"
            "| Kinh phí | Đơn vị cấp |\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n"
            f"## 4.5. {ten_muc}\n\n" + "\n".join(SDC.khoi_quy_trinh_dinh_tinh(g, "4.5", cham=True)) + "\n")


def test_khoi_quy_trinh_dinh_tinh_ba_tieu_muc_va_k17_dat_cac_muc_quy_trinh():
    g1 = GL.KICH_BAN["dinh_tinh"]["pi"]["G1"]
    dong = SDC.khoi_quy_trinh_dinh_tinh(g1, "4.5", cham=True)
    assert [d for d in dong if d.startswith("### ")] == [
        "### 4.5.1. Người phỏng vấn và phản tư của nhóm nghiên cứu",
        "### 4.5.2. Chọn mẫu, tiếp cận và thu thập dữ liệu định tính",
        "### 4.5.3. Xử lý và phân tích dữ liệu định tính"]
    kq = {(r.chuan, r.ma): r for r in K.doi_chieu(_de_cuong_dinh_tinh(g1), "qualitative")["ket_qua"]}
    for ma in ("1", "3", "4", "5", "6", "7", "8", "11", "13", "15", "17", "18", "19", "20", "22", "23", "24", "25",
               "26", "27", "28"):
        assert kq[("COREQ 2007", ma)].trang_thai == "dat", (ma, kq[("COREQ 2007", ma)].thieu)
    for ma in ("S5", "S6", "S11", "S14", "S15"):
        assert kq[("SRQR 2014", ma)].trang_thai == "dat", (ma, kq[("SRQR 2014", ma)].thieu)


def test_khoi_quy_trinh_dinh_tinh_vang_khai_thi_o_trong_hoac_bo_dong():
    rong = SDC.khoi_quy_trinh_dinh_tinh({}, "4.5", cham=True)
    assert f"- Người phỏng vấn: {SDC.CHAM}" in rong  # đề tài định tính: chủ nhiệm điền ô trống
    assert SDC.khoi_quy_trinh_dinh_tinh({}, "4.7", cham=False) == []  # cấu phần hỗn hợp: chỉ in khoá đã khai
    kq = {(r.chuan, r.ma): r for r in K.doi_chieu(_de_cuong_dinh_tinh({}), "qualitative")["ket_qua"]}
    assert kq[("COREQ 2007", "1")].trang_thai == "thieu"


def test_tieu_muc_hon_hop_cung_dat_du_tieu_de_khong_doi():
    cp = BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]["cau_phan_dinh_tinh"]
    md = _de_cuong_dinh_tinh(cp, "Cấu phần định tính và tích hợp dữ liệu").replace(
        "\n".join(SDC.khoi_quy_trinh_dinh_tinh(cp, "4.5", cham=True)),
        "\n".join(SDC.khoi_quy_trinh_dinh_tinh(cp, "4.5", cham=False)))
    kq = {(r.chuan, r.ma): r for r in K.doi_chieu(md, "qualitative")["ket_qua"]}
    for ma in ("1", "3", "4", "6", "8", "9", "11", "15", "18", "19", "20", "21", "22", "23", "24", "25", "26", "28"):
        assert kq[("COREQ 2007", ma)].trang_thai == "dat", (ma, kq[("COREQ 2007", ma)].thieu)


# ───────────────────────────── bản thảo G7 ─────────────────────────────
def _de_tai_dinh_tinh(d: Path, monkeypatch) -> Path:
    g1 = dict(GL.KICH_BAN["dinh_tinh"]["pi"]["G1"])
    _meta(d, {"G1": g1})
    _ghi(d / "SO_DO_LUONG_X.csv", "buoc,n,loai,nhanh,ly_do\nNgười được mời tham gia,24,chinh,,\n"
                                  "Không tham gia,4,loai,,Từ chối: 3; Không liên lạc được: 1\n"
                                  "Được phỏng vấn / tham gia thảo luận nhóm,20,chinh,,\n")
    _ghi(d / "05_clean_locked/x.locked.csv", "ma_nguoi_tham_gia,transcript_id,chu_de\nR0001,GB01,Ngại hạ đường huyết "
                                             "khi đi làm\nR0002,GB02,Gia đình hỗ trợ học cách tiêm\n")
    _ghi(d / "DATA_LOCK_manifest.json", json.dumps({"locked_dataset_path": "05_clean_locked/x.locked.csv"}))
    for tid, loi in (("GB01", TV.LOI_KE_CHU_DE["Ngại hạ đường huyết khi đi làm"]),
                     ("GB02", TV.LOI_KE_CHU_DE["Gia đình hỗ trợ học cách tiêm"])):
        _ghi(d / f"transcripts/{tid}.txt", f"BẢN GỠ BĂNG — {tid}\n\nNgười phỏng vấn: Hỏi?\nNgười tham gia: {loi}\n")
    g6 = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {"loai_dac_thu": "dinh_tinh", "dac_thu": {
        "n_ban_go_bang": 20, "chu_de": [{"chu_de": "Gia đình hỗ trợ học cách tiêm", "n": 8},
                                        {"chu_de": "Ngại hạ đường huyết khi đi làm", "n": 6}]}}}
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: g6)
    return d


MUC_COREQ_BAN_THAO = ("1", "2", "3", "4", "5", "6", "7", "11", "13", "15", "16", "17", "18", "20", "23", "24", "25",
                      "29")


def test_ban_thao_dinh_tinh_dat_cac_muc_coreq_srqr_tu_du_kien_that(tmp_path, monkeypatch):
    d = _de_tai_dinh_tinh(tmp_path, monkeypatch)
    md = _ban_thao(d, "qualitative", "Nghiên cứu Định tính (Qualitative Research)", "COREQ")
    kq = {(r.chuan, r.ma): r for r in TB.doi_chieu_ban_thao(_nop(md), "qualitative", co_so_lieu=True)["ket_qua"]}
    for ma in MUC_COREQ_BAN_THAO:
        assert kq[("COREQ 2007", ma)].trang_thai == "dat", (ma, kq[("COREQ 2007", ma)].thieu)
    for ma in ("S4", "S5", "S11", "S16", "S17"):
        assert kq[("SRQR 2014", ma)].trang_thai == "dat", (ma, kq[("SRQR 2014", ma)].thieu)
    assert ("*Người được mời và người không tham gia:* 24 người được mời; 4 người từ chối hoặc không tham gia, lý do: "
            "từ chối (3) và không liên lạc được (1); 20 người được phỏng vấn.") in md
    # trích lời NGUYÊN VĂN từ bản gỡ băng, chủ đề phổ biến nhất trước
    loi = TV.LOI_KE_CHU_DE["Gia đình hỗ trợ học cách tiêm"].rstrip(".")
    assert f"«{loi}» (GB02, chủ đề «Gia đình hỗ trợ học cách tiêm»)" in md
    assert md.index("(GB02, chủ đề") < md.index("(GB01, chủ đề")  # chủ đề phổ biến nhất được trích trước
    assert ("*Chủ đề chính:* «Gia đình hỗ trợ học cách tiêm» (8/20 bản gỡ băng); «Ngại hạ đường huyết khi đi làm» "
            "(6/20 bản gỡ băng).") in md


def test_ban_thao_dinh_tinh_vang_du_kien_thi_o_can(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    _meta(tmp_path, {"G1": {"design": "qualitative"}})
    k = G7.khoi_dinh_tinh_g7(tmp_path, G7._doc_meta_g7(tmp_path), HH.nguon_dinh_tinh(G7._doc_meta_g7(tmp_path)))
    van = "\n".join(k["phuong_phap_3"] + k["ket_qua"] + k["gioi_thieu"])
    assert van.count("[CẦN — ") == len(KHOA) + 5  # 12 khoá quy trình + câu hỏi + 4 dòng kết quả
    assert "«" not in van  # không dựng trích lời khi không có bản gỡ băng


def test_ban_thao_hon_hop_doc_ket_qua_cau_phan_dinh_tinh(tmp_path):
    cp = BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]
    _meta(tmp_path, {"G1": {"design": "rct", "mixed_methods": cp, "research_question": "Câu hỏi thử?"}})
    _ghi(tmp_path / G7.TEP_KET_QUA_DINH_TINH_HH, json.dumps({
        "so_moi": 20, "khong_tham_gia": {"Không sắp xếp được thời gian": 2, "Không đồng ý ghi âm": 1},
        "so_phong_van": 17, "dac_diem": "8 người đạt và 9 người không đạt kiểm soát", "tong_ban": 17,
        "chu_de": [{"ten": "Quên thuốc khi đi làm xa hoặc đổi ca", "so_ban": 3, "ban_go_bang": ["PV09"]},
                   {"ten": "Tin nhắn đến đúng giờ giúp hình thành thói quen uống thuốc", "so_ban": 4,
                    "ban_go_bang": ["PV01"]}]}, ensure_ascii=False))
    _ghi(tmp_path / G7.THU_MUC_BAN_GO_BANG_HH / "PV01.txt", "X\n\nNgười tham gia: Tin nhắn đến đúng giờ sáng.\n")
    meta = G7._doc_meta_g7(tmp_path)
    kq = "\n".join(G7.khoi_dinh_tinh_g7(tmp_path, meta, HH.nguon_dinh_tinh(meta))["ket_qua"])
    assert "20 người được mời; 3 người từ chối hoặc không tham gia" in kq and "17 người được phỏng vấn" in kq
    assert kq.index("Tin nhắn đến đúng giờ giúp") < kq.index("Quên thuốc")  # chủ đề phổ biến nhất trước
    assert "«Tin nhắn đến đúng giờ sáng» (PV01" in kq
    assert "PV09" not in kq  # bản gỡ băng không tồn tại ⇒ không trích


def test_k18_coreq_4_nhan_gioi_nguoi_phong_van_o_phuong_phap():
    md = ("# Bài\n\n## TÓM TẮT\n\nx.\n\n## I. GIỚI THIỆU\n\nx [1].\n\n## II. PHƯƠNG PHÁP\n\n"
          "*Người phỏng vấn:* Người phỏng vấn là điều dưỡng của phòng khám (hai người, nữ).\n\n## III. KẾT QUẢ\n\n"
          "20 người.\n\n## IV. BÀN LUẬN\n\nx [2].\n\n## V. KẾT LUẬN\n\nx.\n")
    r = next(x for x in TB.doi_chieu_ban_thao(md, "qualitative", co_so_lieu=True)["ket_qua"]
             if x.chuan == "COREQ 2007" and x.ma == "4")
    assert r.trang_thai == "dat", r.thieu
    assert next(x for x in TB.doi_chieu_ban_thao(md.replace("(hai người, nữ)", ""), "qualitative", co_so_lieu=True)[
        "ket_qua"] if x.chuan == "COREQ 2007" and x.ma == "4").trang_thai == "thieu"


# ───────────────────────────── giả lập: bản gỡ băng + cấu phần định tính hỗn hợp ─────────────────────────────
def test_ban_go_bang_ghi_loi_ke_khong_ghi_nhan_ma(tmp_path):
    tv = TV.TronVong("dinh_tinh", tmp_path, chay=lambda *a, **k: {"ma": 0, "dong": []})
    tv.out.mkdir(parents=True)
    tv._ban_go_bang([{"transcript_id": "GB01", "chu_de": "Sợ kim tiêm; lo phải tiêm suốt đời"}])
    van = (tv.out / "transcripts" / "GB01.txt").read_text(encoding="utf-8")
    assert f"Người tham gia: {TV.LOI_KE_CHU_DE['Sợ kim tiêm; lo phải tiêm suốt đời']}" in van
    assert "Người tham gia: Sợ kim tiêm; lo phải tiêm suốt đời" not in van
    assert GL.NHAN in van.splitlines()[0]  # nhãn dữ liệu mô phỏng ở đầu tệp


def _tv_hon_hop(tmp_path: Path) -> TV.TronVong:
    tv = TV.TronVong("rct_hon_hop", tmp_path, chay=lambda *a, **k: {"ma": 0, "dong": []})
    tv.out.mkdir(parents=True)
    tv._ghi_meta({"gate_params": {"G1": {"design": "rct", "mixed_methods": tv.kb["pi"]["G1"]["mixed_methods"]}}})
    with (tv.out / "khoa.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record_id", "nhom", "tuoi", "gioi", "kiem_soat_t6"])
        for i in range(60):
            w.writerow([f"R{i:04d}", i % 2, 40 + i % 30, 1 + i % 2, (i // 2) % 2])
    _ghi(tv.out / "DATA_LOCK_manifest.json", json.dumps({"locked_dataset_path": "khoa.csv"}))
    with (tv.out / f"G5_REDCap_dictionary_{tv.study}.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Variable / Field Name", "Choices, Calculations, OR Slider Labels"])
        w.writerow(["gioi", "1, Nam | 2, Nữ"])
    return tv


def test_cau_phan_dinh_tinh_hon_hop_so_dem_khop_ban_go_bang(tmp_path):
    tv = _tv_hon_hop(tmp_path)
    tv._cau_phan_dinh_tinh_hon_hop()
    kq = json.loads((tv.out / G7.TEP_KET_QUA_DINH_TINH_HH).read_text(encoding="utf-8"))
    assert kq["nguon"].startswith("MÔ PHỎNG CÓ KIỂM SOÁT")
    assert kq["so_phong_van"] == kq["so_moi"] - sum(kq["khong_tham_gia"].values()) == kq["tong_ban"]
    assert sum(c["so_ban"] for c in kq["chu_de"]) == kq["tong_ban"]
    assert {c["nhom"] for c in kq["chu_de"]} == {"người đạt kiểm soát huyết áp tại tháng 6",
                                                 "người không đạt kiểm soát huyết áp tại tháng 6"}  # GRAMMS 6
    tep = sorted((tv.out / G7.THU_MUC_BAN_GO_BANG_HH).glob("PV*.txt"))
    assert len(tep) == kq["tong_ban"] and all(t.stem in sum((c["ban_go_bang"] for c in kq["chu_de"]), []) for t in tep)
    van = "".join(t.read_text(encoding="utf-8") for t in tep)
    assert "R00" not in van and GL.NHAN in van  # khử định danh: không mang mã người tham gia của thử nghiệm
    assert " nữ" in kq["dac_diem"] and "tuổi trung vị" in kq["dac_diem"]


def test_cau_phan_dinh_tinh_khong_hon_hop_thi_khong_lam_gi(tmp_path):
    tv = _tv_hon_hop(tmp_path)
    tv._ghi_meta({"gate_params": {"G1": {"design": "rct"}}})
    tv._cau_phan_dinh_tinh_hon_hop()
    assert not (tv.out / G7.TEP_KET_QUA_DINH_TINH_HH).exists()


def test_g7_goi_cau_phan_dinh_tinh_truoc_khi_sinh_ban_thao():
    import ast  # noqa: PLC0415
    import inspect  # noqa: PLC0415
    import textwrap  # noqa: PLC0415

    dong: dict = {}
    for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(TV.TronVong.g7)))):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr == "_cau_phan_dinh_tinh_hon_hop":
                dong.setdefault("cp", []).append(n.lineno)
            elif n.func.attr == "chay" and n.args and getattr(n.args[0], "value", "") == "G7 sinh bản thảo":
                dong.setdefault("sinh", []).append(n.lineno)
    assert len(dong.get("cp", [])) == 1 and dong["cp"][0] < dong["sinh"][0], dong


def test_de_cuong_hon_hop_in_han_che_do_ket_hop_gramms_5():
    import types  # noqa: PLC0415

    mm = BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]
    n = types.SimpleNamespace(meta={"gate_params": {"G1": {"mixed_methods": mm}}}, s=lambda *a: None, g1={},
                              td=types.SimpleNamespace(thay=lambda x: x), thiet_ke="rct")
    ra = SDC.han_che_suy_rong(n)
    assert any(d.startswith("- Hạn chế do kết hợp hai cấu phần:") for d in ra), ra
    kq = {(r.chuan, r.ma): r for r in K.doi_chieu(
        "# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC\n\n## T\n\n## THÔNG TIN CHUNG VỀ ĐỀ TÀI\n\n| Kinh phí | Đơn vị cấp |\n\n"
        "# 5. DỰ KIẾN KẾT QUẢ\n\n## 5.8. Hạn chế của nghiên cứu\n\n" + "\n".join(ra),
        "mixed_methods")["ket_qua"]}
    assert kq[("GRAMMS 2008", "5")].trang_thai == "dat", kq[("GRAMMS 2008", "5")].thieu


# ───────────────────────────── GRAMMS 2008 mục 5, 6 ở bàn luận bản thảo đề tài hỗn hợp ─────────────────────────────
def _gramms_ban_thao(tmp_path: Path, han_che: bool = True, nhom: bool = True) -> tuple:
    mm = json.loads(json.dumps(BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]))
    if not han_che:
        mm["tich_hop"].pop("han_che")
    _meta(tmp_path, {"G1": {"design": "rct", "mixed_methods": mm, "research_question": "Câu hỏi thử?"}})
    cd = [{"ten": "Quên thuốc khi đi làm xa hoặc đổi ca", "so_ban": 3, "ban_go_bang": ["PV09"],
           "nhom": "Người không đạt kiểm soát huyết áp tại tháng 6"},
          {"ten": "Tự giảm thuốc vì lo tác dụng phụ", "so_ban": 2, "ban_go_bang": ["PV10"],
           "nhom": "Người không đạt kiểm soát huyết áp tại tháng 6"},
          {"ten": "Tin nhắn đến đúng giờ giúp hình thành thói quen uống thuốc", "so_ban": 4, "ban_go_bang": ["PV01"],
           "nhom": "Người đạt kiểm soát huyết áp tại tháng 6"}]
    if not nhom:
        cd[0].pop("nhom")
    _ghi(tmp_path / G7.TEP_KET_QUA_DINH_TINH_HH, json.dumps(
        {"so_moi": 12, "khong_tham_gia": {}, "so_phong_van": 9, "tong_ban": 9, "chu_de": cd}, ensure_ascii=False))
    meta = G7._doc_meta_g7(tmp_path)
    kt = G7.khoi_dinh_tinh_g7(tmp_path, meta, HH.nguon_dinh_tinh(meta))
    md = ("# Bài\n\n## TÓM TẮT\n\nx.\n\n## I. GIỚI THIỆU\n\nx [1].\n\n## II. PHƯƠNG PHÁP\n\nThử nghiệm có "
          "cấu phần định tính giải thích tuần tự.\n\n## III. KẾT QUẢ\n\n9 người.\n\n## IV. BÀN LUẬN\n\n"
          "**§5 Hạn chế:**  \n" + "\n".join(kt["ban_luan_han_che"]) + "\n\n**§6 Ý nghĩa:**  \n"
          + "\n".join(kt["ban_luan_ap_dung"]) + "\n\nx [2].\n\n## V. KẾT LUẬN\n\nx.\n")
    r = {(x.chuan, x.ma): x for x in TB.doi_chieu_ban_thao(md, "rct", co_so_lieu=True)["ket_qua"]
         if x.chuan == "GRAMMS 2008"}
    return kt, r


def test_ban_thao_hon_hop_gramms_5_6_tu_khai_g1_va_chu_de_theo_nhom(tmp_path):
    kt, r = _gramms_ban_thao(tmp_path)
    assert kt["ban_luan_han_che"] == [
        BTK.kich_ban_kho()["rct_hon_hop"]["pi"]["G1"]["mixed_methods"]["tich_hop"]["han_che"] + ".  "]
    ad = "\n".join(kt["ban_luan_ap_dung"])
    # nhóm có chủ đề phổ biến nhất đứng trước; trong nhóm, chủ đề nhiều bản gỡ băng trước
    assert ("Tích hợp kết quả hai cấu phần giúp giải thích kết quả định lượng theo nhóm: người đạt kiểm soát huyết áp "
            "tại tháng 6 nêu «Tin nhắn đến đúng giờ giúp hình thành thói quen uống thuốc» (4/9 bản gỡ băng); người "
            "không đạt kiểm soát huyết áp tại tháng 6 nêu «Quên thuốc khi đi làm xa hoặc đổi ca» (3/9 bản gỡ băng) và "
            "«Tự giảm thuốc vì lo tác dụng phụ» (2/9 bản gỡ băng).") in ad, ad
    assert r[("GRAMMS 2008", "5")].trang_thai == "dat", r[("GRAMMS 2008", "5")].thieu
    assert r[("GRAMMS 2008", "6")].trang_thai == "dat", r[("GRAMMS 2008", "6")].thieu


def test_ban_thao_hon_hop_gramms_5_6_vang_du_kien_thi_o_can_va_k18_bao_thieu(tmp_path):
    kt, r = _gramms_ban_thao(tmp_path, han_che=False, nhom=False)
    assert "[CẦN — hạn chế của một cấu phần phát sinh do có mặt cấu phần kia" in kt["ban_luan_han_che"][0]
    assert "[CẦN — hiểu biết thu được nhờ tích hợp" in kt["ban_luan_ap_dung"][0]
    assert r[("GRAMMS 2008", "5")].trang_thai != "dat" and r[("GRAMMS 2008", "6")].trang_thai != "dat"


def test_de_tai_dinh_tinh_khong_co_dong_gramms(tmp_path, monkeypatch):
    d = _de_tai_dinh_tinh(tmp_path, monkeypatch)
    meta = G7._doc_meta_g7(d)
    kt = G7.khoi_dinh_tinh_g7(d, meta, HH.nguon_dinh_tinh(meta))
    assert kt["ban_luan_han_che"] == [] and kt["ban_luan_ap_dung"] == []


def test_dien_giai_gia_lap_khong_chep_lai_gramms_5_6():
    dg = BTK.kich_ban_kho()["rct_hon_hop"]["ho_so_tron_vong"]["dien_giai"]
    van = " ".join(str(v) for v in dg.values())
    assert "Hạn chế do kết hợp" not in van and "Hạn chế của thiết kế hỗn hợp" not in van
    assert "Kết hợp hai cấu phần giúp" not in van
