# -*- coding: utf-8 -*-
"""Giả lập trọn vòng — dữ kiện bản thảo có mặt TRƯỚC lượt sinh G7 (22/11/2026, K18 CONSORT 2025 mục 4, 8, 20b, 24b).

Đo đầu–cuối (docs/K18-PHAN-XU-BAN-THAO-20261122.md §3.3): bộ giả lập chạy `run_g7_auto.py` TRƯỚC khi tác giả ghi
`gate_params.G7.data_sharing_statement` và trước khi PI khai đặc tả ở G10 (`ppi_plan`, `concomitant_care_policy`) ⇒
bản thảo cuối thiếu 4, 8, 24b dù gói G10 có đủ dữ kiện; sinh lại G7 sau G10 thì đạt. Sửa: `_khai_truoc_ban_thao` cho
đúng hai vai khai các khoá bộ sinh đọc (`run_g7_auto.KHOA_TAC_GIA_BAN_THAO`, `KHOA_DAC_TA_BAN_THAO`) ngay trước lượt
sinh. Kèm hai chỗ K18 đọc sai trên bản thảo giả lập: 24b nhận TÊN NHÓM CHỨNG «chăm sóc thường quy» làm bằng chứng;
mục 4 không nhận «dữ liệu cá thể» (individual participant data).
"""
from __future__ import annotations

import ast
import inspect
import re
import sys
import textwrap
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import gia_lap_tron_vong as TV  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402

KB = "rct_nhi_phan"


def _tron_vong(tmp_path: Path, meta: dict | None = None) -> TV.TronVong:
    tv = TV.TronVong(KB, tmp_path, chay=lambda *a, **k: {"ma": 0, "dong": []})
    tv.out.mkdir(parents=True)
    tv._ghi_meta(meta or {"gate_params": {"G1": {"design": "rct"}}})
    return tv


# ───────────────────────────── khoá bộ sinh đọc ⇔ khoá giả lập khai ─────────────────────────────
def test_hang_khoa_phu_moi_cho_bo_sinh_doc_loi_khai():
    """Bộ sinh thêm chỗ đọc lời khai mới mà quên thêm khoá vào hằng ⇒ giả lập lại khai SAU lượt sinh (lỗi cũ)."""
    nguon = inspect.getsource(G7)
    doc_pi = set()
    for n in ast.walk(ast.parse(nguon)):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_khai_pi_g7":
            doc_pi |= {a.value for a in n.args[1:] if isinstance(a, ast.Constant) and isinstance(a.value, str)}
    doc_g7 = set(re.findall(r"\bg7\.get\(\"(\w+)\"\)", nguon))
    assert doc_pi and doc_pi <= set(G7.KHOA_DAC_TA_BAN_THAO), doc_pi
    assert doc_g7 and doc_g7 <= set(G7.KHOA_TAC_GIA_BAN_THAO), doc_g7


def test_g7_khai_truoc_roi_moi_sinh_ban_thao():
    """Nối dây: `_khai_truoc_ban_thao()` phải chạy TRƯỚC lệnh «G7 sinh bản thảo» trong `TronVong.g7`."""
    dong: dict = {}
    for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(TV.TronVong.g7)))):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr == "_khai_truoc_ban_thao":
                dong.setdefault("khai", []).append(n.lineno)
            elif n.func.attr == "chay" and n.args and getattr(n.args[0], "value", "") == "G7 sinh bản thảo":
                dong.setdefault("sinh", []).append(n.lineno)
    assert len(dong.get("khai", [])) == len(dong.get("sinh", [])) == 1, dong
    assert dong["khai"][0] < dong["sinh"][0], dong


# ───────────────────────────── khai đúng vai, không đè ─────────────────────────────
def test_khai_truoc_ban_thao_ghi_dung_vai_dung_khoa(tmp_path):
    tv = _tron_vong(tmp_path)
    hs = tv.kb["ho_so_tron_vong"]
    tv._khai_truoc_ban_thao()
    meta = tv._meta()
    g7 = meta["gate_params"]["G7"]
    assert g7["data_sharing_statement"] == hs["tac_gia_G7"]["data_sharing_statement"]
    assert meta["ppi_plan"] == hs["dac_ta_G10"]["ppi_plan"]
    assert meta["concomitant_care_policy"] == hs["dac_ta_G10"]["concomitant_care_policy"]
    # xác nhận đã đọc bản thảo là việc SAU lượt sinh — không được có trước
    assert "manuscript_reviewed_confirmed" not in g7 and "dau_van_tay_chot" not in g7
    # chỉ khoá bộ sinh đọc: đặc tả khác của G10 (tiến độ, sai lệch…) vẫn do PI khai ở G10
    assert "timeline" not in meta and "bias_risks" not in meta
    assert set(tv.du_lieu["khai_truoc_ban_thao"]) == {"gate_params.G7.data_sharing_statement",
                                                      "gate_params.G7.funding_declared", "ppi_plan",
                                                      "concomitant_care_policy"}


def test_khai_truoc_ban_thao_khong_de_loi_khai_da_co(tmp_path):
    tv = _tron_vong(tmp_path, {"gate_params": {"G7": {"data_sharing_statement": "Lời khai riêng của tác giả"}},
                               "ppi_plan": "PI đã khai khác"})
    tv._khai_truoc_ban_thao()
    meta = tv._meta()
    assert meta["gate_params"]["G7"]["data_sharing_statement"] == "Lời khai riêng của tác giả"
    assert meta["ppi_plan"] == "PI đã khai khác"
    assert "ppi_plan" not in tv.du_lieu["khai_truoc_ban_thao"]


def test_khai_dac_ta_g10_khong_khai_lai_khoa_da_khai_truoc_g7(tmp_path, monkeypatch):
    import quyet_dinh_da_chot as QD

    monkeypatch.setattr(QD, "lop_phu", lambda meta, out, study: (dict(meta), {}))
    tv = _tron_vong(tmp_path)
    tv._khai_truoc_ban_thao()
    truoc = tv._meta()["ppi_plan"]
    tv._khai_dac_ta_g10()
    assert tv._meta()["ppi_plan"] == truoc
    ghi = tv.du_lieu["g10_khai_lai"]
    assert ghi["ppi_plan"] == ghi["concomitant_care_policy"] == "đã khai trước bản thảo G7"
    assert ghi["timeline"] == "mới đúng vai (hồ sơ đề tài)"


def test_khoi_consort_cua_bo_sinh_thay_loi_khai_truoc_g7(tmp_path):
    """Hồ sơ RCT thật của giả lập ⇒ khối CONSORT bộ sinh dựng LÚC SINH G7 đã có 4, 8, 24b (chép nguyên chữ)."""
    tv = _tron_vong(tmp_path)
    tv._khai_truoc_ban_thao()
    k = G7.khoi_consort_bo_sung_g7(tv.out, tv.study, "rct")
    assert k["chia_se"].startswith("Dữ liệu cá thể không chia sẻ công khai theo cam kết bảo mật")
    kb, kq = "\n".join(k["khai_bao"]), "\n".join(k["ket_qua"])
    assert "**Sự tham gia của người bệnh và công chúng:**" in kb and "góp ý nội dung và tần suất tin nhắn" in kb
    assert "*Chăm sóc đồng thời theo quy định của đề cương:* Mọi điều chỉnh thuốc hạ áp" in kq
    assert "SPIRIT" not in kb + kq + k["chia_se"]


# ───────────────────────────── K18 đọc đúng bản thảo giả lập ─────────────────────────────
_NEN = ("# THỬ NGHIỆM NGẪU NHIÊN\n\n## TÓM TẮT\n\n**Phương pháp:** x\n\n## 1. ĐẶT VẤN ĐỀ\n\nx [1].\n\n"
        "## 2. PHƯƠNG PHÁP\n\n*Kết cục chính:* kiểm soát huyết áp.\n\n## 3. KẾT QUẢ\n\n{kq}\n\n"
        "## 4. BÀN LUẬN\n\nx [2].\n\n## 5. KẾT LUẬN\n\nx.\n\n## KHAI BÁO\n\n**Tính có sẵn dữ liệu:**  \n{cs}\n")


def _muc(md: str, ma: str) -> K.KetQua:
    kq = K.doi_chieu(md, "rct", che_do="ban_thao", co_so_lieu=True)
    return next(r for r in kq["ket_qua"] if r.chuan == "CONSORT 2025" and r.ma == ma)


#: ba dòng tên nhóm chứng của bản thảo RCT giả lập (mã nhóm dữ liệu khoá · số người theo nhóm · so sánh)
_TEN_NHOM = ("*Nhóm (mã trong dữ liệu khoá):* `0` = Chăm sóc thường quy; `1` = Tin nhắn SMS\n\n"
             "218 người. Số người theo nhóm (G6): nhóm chăm sóc thường quy: 118; nhóm tin nhắn: 100. RR so với chăm "
             "sóc thường quy 1,28.")


def test_k18_24b_ten_nhom_cham_soc_thuong_quy_khong_phai_bang_chung():
    assert _muc(_NEN.format(kq=_TEN_NHOM, cs="x"), "24b").trang_thai == "thieu"
    assert _muc(_NEN.format(kq="218 người. Cả hai nhóm tiếp tục chăm sóc thường quy.", cs="x"), "24b").trang_thai \
        == "dat"


def test_k18_24b_bang_chung_la_dong_chep_dac_ta_khong_phai_tieu_de(tmp_path):
    """Khối Kết quả bộ sinh dựng từ lời khai PI (khai trước G7) ⇒ bằng chứng 24b là DÒNG chép đặc tả — không phải mã
    nhóm, không phải tiêu đề khối (K18 lấy lần khớp đầu tiên)."""
    tv = _tron_vong(tmp_path, {"gate_params": {"G1": {"design": "rct", "study_period": "03/2027–03/2028"}}})
    tv._khai_truoc_ban_thao()
    kq = "\n".join(G7.khoi_consort_bo_sung_g7(tv.out, tv.study, "rct")["ket_qua"])
    r = _muc(_NEN.format(kq=_TEN_NHOM + "\n" + kq, cs="x"), "24b")
    assert r.trang_thai == "dat", r
    assert len(r.bang_chung) == 1 and "*Chăm sóc đồng thời theo quy định của đề cương:* Mọi điều chỉnh" \
        in r.bang_chung[0], r.bang_chung


def test_k18_4_du_lieu_ca_the_chi_con_thieu_cach_truy_cap_bang_chung_la_dong_tuyen_bo():
    cau = "Dữ liệu cá thể không chia sẻ công khai theo cam kết bảo mật với người tham gia; kịch bản phân tích kèm gói."
    r = _muc(_NEN.format(kq="218 người.", cs=cau), "4")
    assert r.trang_thai == "thieu" and r.thieu == ["cách truy cập"], (r.thieu, r.bang_chung)
    # khớp không vắt từ dòng nhãn «**Tính có sẵn dữ liệu:**» sang dòng tuyên bố
    assert all("Tính có sẵn dữ liệu" not in b and "Dữ liệu cá thể" in b for b in r.bang_chung), r.bang_chung
    # nhãn + dòng sau KHÔNG có dữ liệu cá nhân ⇒ không mượn chữ «dữ liệu» của nhãn
    r = _muc(_NEN.format(kq="218 người.", cs="Cá nhân quan tâm liên hệ tác giả."), "4")
    assert "dữ liệu cá nhân đã khử định danh" in r.thieu, r.bang_chung
