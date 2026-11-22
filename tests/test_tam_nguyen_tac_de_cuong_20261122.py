"""Ma trận 8 nguyên tắc của đề cương (K20) và trục tổng 5 tiêu chí — `tools/tam_nguyen_tac_de_cuong.py` (22/11/2026).

Fixture tự dựng, ngoại tuyến. Mỗi phép đo mới (TN-…) có ca DƯƠNG (xanh/không áp dụng đúng điều kiện) và ca ÂM (đỏ hoặc
⚪ đúng luật); luật gộp ô, ánh xạ luật K theo dòng, trục nhất quán, tiêu chí cổng, biên bản Hội đồng Khoa học, K20 và
chốt chống gọi vòng đều có ca riêng."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import skill_standards as S  # noqa: E402
import tam_nguyen_tac_de_cuong as T  # noqa: E402

MA = "ZZTEST-TNT"

DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU

Phiên bản đề cương: 1.0, ngày 22/11/2026

# ĐẶT VẤN ĐỀ

Thời gian chờ liên quan với hài lòng [1].

## MỤC TIÊU NGHIÊN CỨU

1. Mô tả tỷ lệ hài lòng.

# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU

## 1.2. Công cụ đo lường sự hài lòng

Thang đo SERVQUAL được dùng rộng rãi [1].

# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 2.1. Đối tượng nghiên cứu

### 2.1.1. Tiêu chuẩn lựa chọn

- Người bệnh từ đủ 18 tuổi.

### 2.1.2. Tiêu chuẩn loại trừ

- Suy giảm nhận thức.

## 2.5. Cỡ mẫu và phương pháp chọn mẫu

### 2.5.1. Cỡ mẫu

Cỡ mẫu là 1.000 phiếu.

### 2.5.2. Phương pháp chọn mẫu

Chọn mẫu hệ thống, có nhật ký từ chối để báo cáo tỷ lệ đáp ứng.

## 2.6. Phương pháp nghiên cứu

### 2.6.1. Công cụ thu thập số liệu

Bộ câu hỏi tự điền khuyết danh, đã chạy thử trên 30 người bệnh.

### 2.6.6. Xử lý và phân tích số liệu

Phân tích bằng R; kết quả được kiểm tra chéo bằng hai phần mềm.

## 2.7. Đạo đức trong nghiên cứu

Đề cương chỉ triển khai sau khi Hội đồng Đạo đức chấp thuận. Người tham gia nhận bản thông tin và ký phiếu đồng ý; có \
quyền từ chối hoặc rút khỏi nghiên cứu bất cứ lúc nào, không ảnh hưởng đến việc khám chữa bệnh. Nguy cơ tối thiểu.

### 2.7.1. Xung đột lợi ích và biện pháp quản lý

Chủ nhiệm công tác tại khoa được đánh giá; người ngoài khoa độc lập phát và thu phiếu.

# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN

## 3.6. Hạn chế của nghiên cứu

Thiết kế cắt ngang không xác lập nhân quả.

# TÀI LIỆU THAM KHẢO

1. Tác giả A. Tiêu đề. Tạp chí. 2026. PMID: 11111111.

# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ

Hồi quy logistic thứ tự.

# PHỤ LỤC F. KẾ HOẠCH THỰC HIỆN

## Dự trù kinh phí

Kinh phí tự túc của chủ nhiệm, không có nhà tài trợ.
"""

META = {
    "title": "Hài lòng người bệnh ngoại trú",
    "data_governance": {"deidentification": "Phiếu khuyết danh, mã nghiên cứu", "access": "Phân quyền, mật khẩu",
                        "storage": "Lưu trên máy chủ bệnh viện, sao lưu hằng tuần",
                        "breach_procedure": "Sự cố lộ dữ liệu báo chủ nhiệm trong 24 giờ"},
    "gate_params": {
        "G1": {"design": "cross_sectional", "benefit_risk_rationale": "Nguy cơ tối thiểu, lợi ích cải tiến",
               "critical_to_quality": "Chọn mẫu đúng bước nhảy", "monitoring_plan": "Giám sát độc lập kiểm 10% phiếu",
               "team_roles": "Người giám sát độc lập với điều tra viên",
               "risk_register": [{"id": "R1", "xac_suat": "Trung bình", "tac_dong": "Cao", "giam_thieu": "Tập huấn",
                                  "capa": "Bổ sung điều tra viên", "chu_nhan": "Thư ký"}]},
        "G2": {"icf_waiver_requested": False, "external_funding": False,
               "coi": {"summary": "Có xung đột cơ cấu", "structural": "Chủ nhiệm thuộc khoa được đánh giá",
                       "management": "Người ngoài khoa độc lập phát, thu phiếu và nhập liệu"}},
        "G0": {"finer_feasible": "ĐẠT", "finer_interesting": "ĐẠT", "finer_novel": "ĐẠT", "finer_relevant": "ĐẠT",
               "finer_ethical": "ĐẠT"},
    },
}


def _de_tai(tmp_path: Path, md: str = DE_CUONG, meta: dict | None = None) -> Path:
    d = tmp_path / "exports" / MA
    d.mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(md, encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(json.dumps(meta if meta is not None else META, ensure_ascii=False),
                                       encoding="utf-8", newline="\n")
    return d


def _ctx(tmp_path: Path, md: str = DE_CUONG, meta: dict | None = None) -> T.NguCanh:
    return T.NguCanh(_de_tai(tmp_path, md, meta), MA)


def _meta(**sua) -> dict:
    m = json.loads(json.dumps(META))
    for duong, v in sua.items():
        g, k = duong.split("__")
        if v is None:
            m["gate_params"][g].pop(k, None)
        else:
            m["gate_params"][g][k] = v
    return m


@pytest.fixture(autouse=True)
def _xoa_dem():
    T._DEM_KQ.clear()
    yield
    T._DEM_KQ.clear()


# ───────────────────────────────────────── phần của đề cương
def test_tieu_de_canonical_18_muc_nhan_dung_khoa_ben():
    for k in T.PHAN:
        assert T.phan_cua_tieu_de(S.de_cuong_heading(k).lstrip("# ")) == k, k


def test_phan_theo_dong_ngu_canh_tong_quan_du_kien_phu_luc():
    pd = T.phan_theo_dong(DE_CUONG)
    dong = DE_CUONG.split("\n")

    def phan(chu: str) -> str:
        return pd[next(i for i, d in enumerate(dong) if chu in d)]

    assert phan("Thang đo SERVQUAL") == "tongquan"  # «1.2. Công cụ đo lường» của tổng quan KHÔNG là công cụ đề tài
    assert phan("1. Mô tả tỷ lệ hài lòng") == "muctieu"  # MỤC TIÊU dưới ĐẶT VẤN ĐỀ
    assert phan("Thiết kế cắt ngang không xác lập") == "sailech"  # Hạn chế trong chương dự kiến kết quả
    assert phan("Hồi quy logistic thứ tự") == "sap"  # PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH ≠ «Tóm tắt»
    assert phan("Cỡ mẫu là 1.000") == "comau"
    assert phan("Chọn mẫu hệ thống") == "doituong"
    assert phan("Kinh phí tự túc") == "tiendo"
    assert phan("Phiên bản đề cương") == "tomtat"


# ───────────────────────────────────────── luật gộp ô
def _k(tt: str) -> T.KetQuaDo:
    return T._kq("X", "x", "tomtat", "trung_thuc", tt, "lý do")


@pytest.mark.parametrize("ds, mong", [
    ([T.XANH, T.DO], T.DO), ([T.XANH, T.XANH], T.XANH), ([T.XANH, T.CHUA_DO], T.CHUA_DO), ([], T.CHUA_DO),
    ([T.KAD], T.CHUA_DO), ([T.KAD, T.XANH], T.XANH), ([T.CHUA_DO, T.DO], T.DO)])
def test_gop_o(ds, mong):
    assert T.gop_o([_k(x) for x in ds]) == mong


# ───────────────────────────────────────── phép đo mới — dương và âm
def test_tn_ton_01(tmp_path):
    assert T.tn_ton_01(_ctx(tmp_path / "a")).trang_thai == T.XANH
    assert T.tn_ton_01(_ctx(tmp_path / "b", meta=_meta(G2__icf_waiver_requested=True))).trang_thai == T.DO
    md_mien = DE_CUONG.replace("Người tham gia nhận bản thông tin và ký phiếu đồng ý;",
                               "Đề nghị miễn đồng thuận theo Thông tư 43/2024;")
    assert T.tn_ton_01(_ctx(tmp_path / "c", md=md_mien)).trang_thai == T.DO
    assert T.tn_ton_01(_ctx(tmp_path / "d", meta=_meta(G2__icf_waiver_requested=None))).trang_thai == T.CHUA_DO
    assert T.tn_ton_01(_ctx(tmp_path / "e", meta=_meta(G1__design="sr_ma"))).trang_thai == T.KAD


def test_tn_ton_02(tmp_path):
    assert T.tn_ton_02(_ctx(tmp_path / "a")).trang_thai == T.XANH
    md = DE_CUONG.replace(", không ảnh hưởng đến việc khám chữa bệnh", "")
    assert T.tn_ton_02(_ctx(tmp_path / "b", md=md)).trang_thai == T.DO
    md2 = DE_CUONG.replace("quyền từ chối hoặc rút khỏi nghiên cứu bất cứ lúc nào", "quyền được giải thích")
    assert T.tn_ton_02(_ctx(tmp_path / "c", md=md2)).trang_thai == T.DO
    assert T.tn_ton_02(_ctx(tmp_path / "d", meta=_meta(G2__icf_waiver_requested=True))).trang_thai == T.KAD


def test_tn_ton_03(tmp_path):
    assert T.tn_ton_03(_ctx(tmp_path / "a")).trang_thai == T.XANH
    m = _meta()
    m["data_governance"].pop("breach_procedure")
    assert T.tn_ton_03(_ctx(tmp_path / "b", meta=m)).trang_thai == T.DO
    m2 = _meta()
    m2["data_governance"]["access"] = "[CẦN KHAI] phân quyền"
    assert T.tn_ton_03(_ctx(tmp_path / "c", meta=m2)).trang_thai == T.DO
    m3 = _meta()
    m3.pop("data_governance")
    assert T.tn_ton_03(_ctx(tmp_path / "d", meta=m3)).trang_thai == T.CHUA_DO


def test_tn_dd_01(tmp_path):
    assert T.tn_dd_01(_ctx(tmp_path / "a")).trang_thai == T.XANH
    assert T.tn_dd_01(_ctx(tmp_path / "b", meta=_meta(G1__benefit_risk_rationale="[CẦN]"))).trang_thai == T.DO
    assert T.tn_dd_01(_ctx(tmp_path / "c", meta=_meta(G1__benefit_risk_rationale=None))).trang_thai == T.CHUA_DO


def test_tn_tt_01_va_kq_04(tmp_path):
    tt, kq = T.tn_tt_01(_ctx(tmp_path / "a"))
    assert (tt.ma, tt.trang_thai, kq.ma, kq.trang_thai) == ("TN-TT-01", T.XANH, "TN-KQ-04", T.XANH)
    md = DE_CUONG.replace("### 2.7.1. Xung đột lợi ích và biện pháp quản lý", "### 2.7.1. Biện pháp quản lý")
    assert T.tn_tt_01(_ctx(tmp_path / "b", md=md))[0].trang_thai == T.DO
    coi = dict(META["gate_params"]["G2"]["coi"], management="Chủ nhiệm tự giám sát")
    assert T.tn_tt_01(_ctx(tmp_path / "c", meta=_meta(G2__coi=coi)))[1].trang_thai == T.DO
    coi2 = {"summary": "Không có xung đột lợi ích", "structural": ""}
    assert T.tn_tt_01(_ctx(tmp_path / "d", meta=_meta(G2__coi=coi2)))[1].trang_thai == T.KAD


def test_tn_tt_02(tmp_path):
    assert T.tn_tt_02(_ctx(tmp_path / "a")).trang_thai == T.XANH
    md = DE_CUONG.replace("Kinh phí tự túc của chủ nhiệm, không có nhà tài trợ.", "Dự trù chi tiết theo bảng.")
    assert T.tn_tt_02(_ctx(tmp_path / "b", md=md)).trang_thai == T.DO
    assert T.tn_tt_02(_ctx(tmp_path / "c", md=md, meta=_meta(G2__external_funding=True))).trang_thai == T.DO
    assert T.tn_tt_02(_ctx(tmp_path / "d", meta=_meta(G2__external_funding=None))).trang_thai == T.CHUA_DO


def test_tn_kq_01_sap_khoa_truoc_du_lieu(tmp_path):
    m = _meta()
    m.update(sap_lock_date="2026-12-01", data_lock_date="2026-11-30")
    assert T.tn_kq_01(_ctx(tmp_path / "a", meta=m)).trang_thai == T.DO
    m.update(sap_lock_date="2026-11-01")
    assert T.tn_kq_01(_ctx(tmp_path / "b", meta=m)).trang_thai == T.XANH
    m2 = _meta()
    m2.update(data_lock_date="2026-11-30")
    assert T.tn_kq_01(_ctx(tmp_path / "c", meta=m2)).trang_thai == T.DO
    assert T.tn_kq_01(_ctx(tmp_path / "d")).trang_thai == T.CHUA_DO  # chưa có dữ liệu, SAP chưa khoá


def test_tn_kq_02_trich_ho_so_va_tong_quan(tmp_path):
    assert T.tn_kq_02(_ctx(tmp_path / "a")).trang_thai == T.KAD
    md = DE_CUONG.replace("Bộ câu hỏi tự điền khuyết danh", "Phiếu trích xuất từ hồ sơ bệnh án; 10% hồ sơ được người "
                                                           "thứ hai trích lại độc lập")
    assert T.tn_kq_02(_ctx(tmp_path / "b", md=md)).trang_thai == T.DO  # thiếu hệ số đồng thuận
    assert T.tn_kq_02(_ctx(tmp_path / "c", md=md.replace("trích lại độc lập", "trích lại độc lập, tính kappa"))
                      ).trang_thai == T.XANH
    md_sr = DE_CUONG.replace("Bộ câu hỏi tự điền khuyết danh", "Hai người sàng lọc và trích xuất độc lập")
    assert T.tn_kq_02(_ctx(tmp_path / "d", md=md_sr, meta=_meta(G1__design="sr_ma"))).trang_thai == T.XANH


def test_tn_kq_03_khong_bao_gio_do(tmp_path):
    assert T.tn_kq_03(_ctx(tmp_path / "a")).trang_thai == T.XANH
    m = _meta(G1__monitoring_plan="Chủ nhiệm kiểm phiếu", G1__team_roles="Chủ nhiệm, thư ký")
    assert T.tn_kq_03(_ctx(tmp_path / "b", meta=m)).trang_thai == T.CHUA_DO
    assert T.tn_kq_03(_ctx(tmp_path / "c", meta=_meta(G1__monitoring_plan=None, G1__design="rct"))
                      ).trang_thai == T.CHUA_DO


def test_tn_qc_01_02_theo_thiet_ke(tmp_path):
    assert T.tn_qc_01(_ctx(tmp_path / "a")).trang_thai == T.XANH
    assert T.tn_qc_01(_ctx(tmp_path / "b", meta=_meta(G1__critical_to_quality=None))).trang_thai == T.CHUA_DO
    m = _meta(G1__critical_to_quality=None, G1__monitoring_plan="", G1__design="rct")
    assert T.tn_qc_01(_ctx(tmp_path / "c", meta=m)).trang_thai == T.DO
    assert T.tn_qc_02(_ctx(tmp_path / "d", meta=m)).trang_thai == T.DO


def test_tn_qc_03_04_so_rui_ro(tmp_path):
    a, b = T.tn_qc_03(_ctx(tmp_path / "a"))
    assert (a.trang_thai, b.trang_thai) == (T.XANH, T.XANH)
    rr = [dict(META["gate_params"]["G1"]["risk_register"][0], xac_suat="[CẦN]")]
    a, b = T.tn_qc_03(_ctx(tmp_path / "b", meta=_meta(G1__risk_register=rr)))
    assert (a.trang_thai, b.trang_thai) == (T.XANH, T.DO)
    rr2 = [dict(META["gate_params"]["G1"]["risk_register"][0], capa="")]
    assert T.tn_qc_03(_ctx(tmp_path / "c", meta=_meta(G1__risk_register=rr2)))[0].trang_thai == T.DO
    a, b = T.tn_qc_03(_ctx(tmp_path / "d", meta=_meta(G1__risk_register=[], G1__design="rct")))
    assert (a.trang_thai, b.trang_thai) == (T.CHUA_DO, T.CHUA_DO)  # sổ chưa dựng ≠ sổ dựng dở


def test_tn_qc_05_luat_kiem_du_lieu(tmp_path):
    d = _de_tai(tmp_path)
    ctx = T.NguCanh(d, MA)
    assert T.tn_qc_05(ctx).trang_thai == T.CHUA_DO
    (d / "_bo-bien-rieng.csv").write_text("Variable / Field Name,Field Type\nrecord_id,text\ng1,radio\n",
                                          encoding="utf-8", newline="\n")
    (d / "_luat-dq.csv").write_text("ma_luat,bieu_thuc_redcap\nDQ01,[g1] = '9'\n", encoding="utf-8", newline="\n")
    assert T.tn_qc_05(T.NguCanh(d, MA)).trang_thai == T.XANH
    (d / "_luat-dq.csv").write_text("ma_luat,bieu_thuc_redcap\nDQ01,[g9] = '1'\n", encoding="utf-8", newline="\n")
    assert T.tn_qc_05(T.NguCanh(d, MA)).trang_thai == T.DO


def test_tn_tl_01_luot_tim_tai_lap(tmp_path):
    d = _de_tai(tmp_path)
    assert T.tn_tl_01(T.NguCanh(d, MA)).trang_thai == T.CHUA_DO
    sp = {"co_so_du_lieu": "PubMed", "ngay_tra": "2026-11-15T10:00:00", "truy_van_goc": "a AND b"}
    (d / "G0_pubmed_raw.json").write_text(json.dumps({"search_provenance": sp}), encoding="utf-8", newline="\n")
    assert T.tn_tl_01(T.NguCanh(d, MA)).trang_thai == T.XANH
    sp.pop("truy_van_goc")
    (d / "G0_pubmed_raw.json").write_text(json.dumps({"search_provenance": sp}), encoding="utf-8", newline="\n")
    assert T.tn_tl_01(T.NguCanh(d, MA)).trang_thai == T.DO


def test_tn_dd_02_nhom_de_ton_thuong(tmp_path):
    assert T.tn_dd_02(_ctx(tmp_path / "a")).trang_thai == T.XANH  # ≥ 18 tuổi, loại suy giảm nhận thức
    md = DE_CUONG.replace("- Người bệnh từ đủ 18 tuổi.", "- Trẻ em từ 6 đến 15 tuổi.")
    assert T.tn_dd_02(_ctx(tmp_path / "b", md=md)).trang_thai == T.DO
    md2 = md.replace("Nguy cơ tối thiểu.", "Cha mẹ hoặc người giám hộ ký đồng ý; trẻ ký phiếu ưng thuận.")
    assert T.tn_dd_02(_ctx(tmp_path / "c", md=md2)).trang_thai == T.XANH
    md3 = DE_CUONG.replace("- Người bệnh từ đủ 18 tuổi.", "- Người bệnh từ đủ 18 tuổi (bao gồm phụ nữ mang thai).")
    assert T.tn_dd_02(_ctx(tmp_path / "d", md=md3)).trang_thai == T.XANH  # có «nguy cơ tối thiểu»
    assert T.tn_dd_02(_ctx(tmp_path / "e", md=md3.replace("Nguy cơ tối thiểu.", ""))).trang_thai == T.DO


def test_tn_ton_05_phieu_khong_dinh_danh(tmp_path):
    assert T.tn_ton_05(_ctx(tmp_path / "a")).trang_thai == T.XANH
    md = DE_CUONG.replace("Bộ câu hỏi tự điền khuyết danh, đã chạy thử trên 30 người bệnh.",
                          "Bộ câu hỏi tự điền.\n\nHọ và tên người bệnh: ……………")
    assert T.tn_ton_05(_ctx(tmp_path / "b", md=md)).trang_thai == T.DO
    md2 = md.replace("Kinh phí tự túc", "Bảng nối mã lưu riêng do người độc lập giữ. Kinh phí tự túc")
    md2 = md2.replace("## Dự trù kinh phí",
                      "## Kế hoạch quản lý dữ liệu\n\nBảng nối mã lưu riêng.\n\n## Dự trù kinh phí")
    assert T.tn_ton_05(_ctx(tmp_path / "c", md=md2)).trang_thai == T.XANH


@pytest.mark.parametrize("ham, xoa", [
    (T.tn_qc_06, "đã chạy thử trên 30 người bệnh"), (T.tn_qc_07, "có nhật ký từ chối để báo cáo tỷ lệ đáp ứng"),
    (T.tn_qc_08, "kết quả được kiểm tra chéo bằng hai phần mềm")])
def test_phep_do_co_mat_xanh_hoac_trang_khong_bao_gio_do(tmp_path, ham, xoa):
    assert ham(_ctx(tmp_path / "a")).trang_thai == T.XANH
    assert ham(_ctx(tmp_path / "b", md=DE_CUONG.replace(xoa, "nội dung khác"))).trang_thai == T.CHUA_DO


# ───────────────────────────────────────── luật K theo dòng
def test_luat_k_theo_dong_roi_dung_phan(tmp_path):
    dong = DE_CUONG.split("\n")
    so = next(i for i, d in enumerate(dong, 1) if "Thang đo SERVQUAL" in d)
    ctx = T.NguCanh(_de_tai(tmp_path), MA, loi_k=[f"K10 dòng {so}: số liệu không có trích dẫn"])
    k10 = {k.phan: k.trang_thai for k in T.do_luat_k(ctx) if k.ma == "K10"}
    assert k10 == {"datvande": T.XANH, "tongquan": T.DO, "dukien_ketqua": T.XANH}
    assert all(k.nguon_k for k in T.do_luat_k(ctx))


def test_anh_xa_k17_phu_moi_phan_cua_k17():
    assert set(KCM.PHAN) <= set(T.ANH_XA_K17_PHAN), set(KCM.PHAN) - set(T.ANH_XA_K17_PHAN)
    assert all(p in T.PHAN and n in T.NT for p, n, _ in T.ANH_XA_K17_PHAN.values())


# ───────────────────────────────────────── trục nhất quán, cổng, hội đồng
def test_truc_nhat_quan_lech_mem_do_vang_bat_buoc_trang(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)
    monkeypatch.setattr(ctx, "nq", lambda: {"thong_so": [
        {"ma": "ket_cuc_chinh", "muc": "lech_mem", "ghi_chu": "khác"},
        {"ma": "tai_lieu_nop_co_mau", "muc": "lech_mem", "ghi_chu": "N khác"}]})
    kq = {k.ma: k for k in T.do_nhat_quan(ctx)}
    assert kq["NQ:ket_cuc_chinh"].trang_thai == T.DO and not kq["NQ:ket_cuc_chinh"].nguon_k
    assert kq["NQ:tai_lieu_nop_co_mau"].nguon_k  # trùng K5 ⇒ K20 không chặn lần hai
    assert kq["NQ:co_mau"].trang_thai == T.CHUA_DO  # bắt buộc theo thiết kế mà vắng
    assert kq["NQ:dac_ta_phan_tich"].trang_thai == T.KAD  # vắng vì không áp dụng


def test_tieu_chi_cong_chua_chay_block_review(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)
    assert all(k.trang_thai == T.CHUA_DO for k in T.do_cong(ctx))  # không checkpoint ⇒ cổng chưa chạy
    (ctx.out_dir / "G4_checkpoint.json").write_text("{}", encoding="utf-8", newline="\n")
    bc = {"automatic_criteria": [{"id": "G4-AUTO-06", "status": "BLOCK"}, {"id": "G4-AUTO-07", "status": "REVIEW"},
                                 {"id": "G4-AUTO-08", "status": "PASS"}]}
    monkeypatch.setattr(ctx, "cong", lambda g: {"status": "BLOCKED", "muc": "BLOCKED", "bao_cao": bc})
    kq = {k.ma: k.trang_thai for k in T.do_cong(ctx)}
    assert (kq["G4-AUTO-06"], kq["G4-AUTO-07"], kq["G4-AUTO-08"], kq["G4-AUTO-11"]) == (
        T.DO, T.CHUA_DO, T.XANH, T.CHUA_DO)


def _bien_ban(d: Path, md: str, van_de: list, trung_vi: dict, sha: str | None = None) -> None:
    (d / "hoi_dong_khoa_hoc").mkdir(exist_ok=True)
    bb = {"sha": sha or hashlib.sha256(md.encode("utf-8")).hexdigest(),
          "tong_hop": {"trung_vi": trung_vi, "van_de": van_de}}
    (d / "hoi_dong_khoa_hoc" / "BIEN_BAN_HDKH_X_20261122_aaaa.json").write_text(json.dumps(bb), encoding="utf-8",
                                                                             newline="\n")


def test_hoi_dong_khoa_hoc_bien_ban_hieu_luc(tmp_path):
    d = _de_tai(tmp_path / "a")
    assert all(k.trang_thai == T.CHUA_DO for k in T.do_hoi_dong(T.NguCanh(d, MA)))
    so = next(i for i, x in enumerate(DE_CUONG.split("\n"), 1) if "Thang đo SERVQUAL" in x)
    _bien_ban(d, DE_CUONG, [{"muc_phieu": "1", "muc_do": "can_sua", "dong": so, "van_de": "thiếu nguồn"}],
              {"1": 3, "2": 4, "3": 4, "4": 5})
    kq = {(k.ma, k.phan): k.trang_thai for k in T.do_hoi_dong(T.NguCanh(d, MA))}
    assert kq[("HDKH:1", "tongquan")] == T.DO and kq[("HDKH:1", "datvande")] == T.CHUA_DO
    assert kq[("HDKH:2", "sap")] == T.XANH and kq[("HDKH:4", "tltk")] == T.XANH
    d2 = _de_tai(tmp_path / "b")
    _bien_ban(d2, DE_CUONG, [], {"1": 5, "2": 5, "3": 5, "4": 5}, sha="0" * 64)  # biên bản của bản khác
    assert all(k.trang_thai == T.CHUA_DO for k in T.do_hoi_dong(T.NguCanh(d2, MA)))


# ───────────────────────────────────────── ma trận, K20, trục tổng
def test_khong_ap_dung_theo_dieu_kien_he(tmp_path):
    kq = T.tinh(_de_tai(tmp_path, meta=_meta(G1__design="sr_ma")), MA)
    assert all(kq["o"]["comau"][n]["trang_thai"] == T.KAD for n in T.NT)
    assert all(kq["o"][p]["ton_trong"]["trang_thai"] == T.KAD for p in T.PHAN)
    kq2 = T.tinh(_de_tai(tmp_path / "x"), MA)
    assert kq2["tong"][T.KAD] == 0


def test_k20_chi_chan_do_ngoai_k1_k19(tmp_path):
    rr = [dict(META["gate_params"]["G1"]["risk_register"][0], xac_suat="[CẦN]")]
    d = _de_tai(tmp_path, meta=_meta(G1__risk_register=rr))
    loi = T.loi_k20(d, MA, ["K10 dòng 7: số liệu không có trích dẫn"])
    assert any("TN-QC-04" in x for x in loi)
    assert not any("K10" in x.split(":", 1)[1] for x in loi if x.startswith("K20"))  # lỗi K10 không nhân đôi
    T._DEM_KQ.clear()
    assert not [x for x in T.loi_k20(_de_tai(tmp_path / "b"), MA, []) if "TN-QC-04" in x]


def test_k20_noi_vao_kiem_va_khong_goi_vong(tmp_path, monkeypatch):
    rr = [dict(META["gate_params"]["G1"]["risk_register"][0], xac_suat="[CẦN]")]
    d = _de_tai(tmp_path, meta=_meta(G1__risk_register=rr))
    assert any(x.startswith("K20") and "TN-QC-04" in x for x in KDN.kiem(d, MA))
    goi = []
    goc = KDN.kiem

    def dem(*a, **k):
        goi.append(1)
        assert len(goi) < 5, "gọi vòng kiem ↔ K20"
        return goc(*a, **k)

    so_lan_tinh = []
    goc_moi = T.do_phep_do_moi

    def dem_tinh(ctx):
        so_lan_tinh.append(1)
        return goc_moi(ctx)

    T._DEM_KQ.clear()
    monkeypatch.setattr(KDN, "kiem", dem)
    monkeypatch.setattr(T, "BO_DO", tuple(dem_tinh if b is goc_moi else b for b in T.BO_DO))
    T.tinh(d, MA)  # tự gọi kiem() một lần; K20 lồng bên trong phải trả rỗng, không dựng ma trận lần hai
    assert len(goi) == 1 and len(so_lan_tinh) == 1


def test_truc_tong_5_tieu_chi(tmp_path):
    kq = T.tinh(_de_tai(tmp_path), MA)
    assert [t["khoa"] for t in kq["truc_tong"]] == ["gia_tri", "phuong_phap", "kha_thi", "dao_duc", "kiem_chung"]
    T._DEM_KQ.clear()
    kq2 = T.tinh(_de_tai(tmp_path / "b", meta=_meta(G0__finer_feasible="KHÔNG ĐẠT — thiếu nhân lực")), MA)
    kt = next(t for t in kq2["truc_tong"] if t["khoa"] == "kha_thi")
    assert kt["trang_thai"] == T.DO
    T._DEM_KQ.clear()
    kq3 = T.tinh(_de_tai(tmp_path / "c", meta=_meta(G0__finer_feasible="ĐẠT CÓ ĐIỀU KIỆN — còn việc mở")), MA)
    tp = next(x for t in kq3["truc_tong"] if t["khoa"] == "kha_thi" for x in t["thanh_phan"]
              if x["nguon"] == "G0.finer_feasible")
    assert tp["trang_thai"] == T.CHUA_DO
    assert T.markdown(kq).index("Trục tổng 5 tiêu chí") < T.markdown(kq).index("| Phần |")


def test_cli_ma_thoat(tmp_path, capsys):
    assert T.main(["--study", "../x", "--goc", str(tmp_path)]) == 3
    assert T.main(["--study", "KHONG-CO", "--goc", str(tmp_path)]) == 3
    d = _de_tai(tmp_path)
    ma = T.main(["--study", MA, "--goc", str(tmp_path), "--ghi"])
    assert ma in (1, 2)
    assert (d / f"MA_TRAN_8_NGUYEN_TAC_{MA}.md").is_file() and (d / f"MA_TRAN_8_NGUYEN_TAC_{MA}.json").is_file()


def test_nguon_nguyen_tac_co_dinh_danh_da_kiem():
    pmid = {x.pmid for n in T.NGUYEN_TAC for x in n.nguon if x.pmid}
    assert pmid == {"39425955", "21390871", "26113702", "42557573", "20494804", "20169472"}
    assert len(T.NGUYEN_TAC) == 8 and all(n.nguon and n.dinh_nghia for n in T.NGUYEN_TAC)
    assert all(not x.pmid for n in T.NGUYEN_TAC for x in n.nguon if x.ten.startswith(("Thông tư", "Luật", "CIOMS",
                                                                                     "ICH")))
