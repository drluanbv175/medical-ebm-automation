"""Kiểm `tools/ho_so_nguon_chung.py` và phần nâng cấp 22/11/2026 của hai bộ hồ sơ (Hội đồng Đạo đức · đề tài cơ sở).

Luật được canh:
  * Ba loại ô chưa điền: (a) «[CẦN …]» suy được từ nguồn đã chốt — đích 0; (b) «[GÓI KÝ: …]» chữ ký/ngày ký/văn bản
    ký/tự khai; (c) «[DỮ KIỆN CẦN NHẬP: …]» chỉ có khi triển khai. Ô cá nhân lấy từ sổ lý lịch lúc dựng Word.
  * Hai bộ hồ sơ đọc CÙNG nguồn với gói G2 (đơn vị chủ trì/công tác, chủ nhiệm, kinh phí tự túc, xung đột lợi ích,
    quản trị dữ liệu, mục tiêu G1 nguyên văn, căn cứ miễn đồng thuận, bản thông tin của đề cương).
  * Khối dữ kiện riêng của biểu mẫu trong study_meta không ghi đè ô dùng chung.
  * Đối chiếu nhất quán đề cương ↔ G2 ↔ hai bộ hồ sơ: lệch ⇒ `kiem` mã 1.
  * Văn bản nộp không còn «[CẦN» hay dấu nội bộ; danh mục có GÓI KÝ và DỮ KIỆN CẦN NHẬP.

Đề tài GIẢ, sổ lý lịch GIẢ trong tmp_path — không dữ liệu thật, không chạm vị trí thật.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")

from tests import test_ho_so_dtcs_bvqy175_20261121 as TDTCS  # noqa: E402
from tests import test_ho_so_hdd_bvqy175_20261119 as THDD  # noqa: E402
from tools import ho_so_dtcs_bvqy175 as DTCS  # noqa: E402
from tools import ho_so_hdd_bvqy175 as HDD  # noqa: E402
from tools import ho_so_nguon_chung as HSC  # noqa: E402

STUDY = "de-tai-nguon-chung"
TEN = "Đề tài nguồn chung giả định"
MT = ["Xác định tỷ lệ A ở người bệnh giả định", "Phân tích một số yếu tố liên quan đến A"]
DV_CONG_TAC = "Khoa Giả C1, Trung tâm Giả C, Bệnh viện Quân y 175"
DV_CHU_TRI = "Khoa Giả, Bệnh viện Quân y 175"
LL = ["Không khả thi vì lý do giả A.", "Giá trị xã hội giả B.", "Nguy cơ tối thiểu giả C."]
TL4 = """```
6c. BỒI THƯỜNG KHI CÓ TỔN HẠI
 Nghiên cứu quan sát; tổn hại liên quan được xử trí theo quy trình thường quy.

7. THÔNG TIN LIÊN HỆ
 Thắc mắc: chủ nhiệm
```"""

DE_CUONG = f"""# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## MỤC TIÊU NGHIÊN CỨU

1. ***MT1: {MT[0]}.***
2. ***MT2: {MT[1]}.***

# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 2.3. Thiết kế nghiên cứu

Nghiên cứu cắt ngang mô tả có phân tích.

## 2.5.1. Cỡ mẫu

Cỡ mẫu 1.000 người.

## 2.7. Đạo đức trong nghiên cứu

- Mức nguy cơ: Nguy cơ tối thiểu.
- Hình thức xét duyệt: Đề nghị xét duyệt theo quy trình rút gọn.
- Xung đột lợi ích: Chủ nhiệm công tác tại khoa được đánh giá — xung đột lợi ích không tài chính.

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU

*(Tài liệu riêng. Phiên bản 1.0, ngày ……/……/2026.)*

**BẢN THÔNG TIN DÀNH CHO NGƯỜI THAM GIA NGHIÊN CỨU**

**1. Mục đích của nghiên cứu.** Tìm hiểu tỷ lệ A.

**2. Nếu đồng ý tham gia, Ông/Bà sẽ:**
- Ký phiếu đồng ý;
- Điền một phiếu *khuyết danh*.

**3. Nguy cơ và bất tiện.** Mất khoảng 15 phút.

**4. Lợi ích.** Không có lợi ích trực tiếp.

**5. Kinh phí và xung đột lợi ích.** Kinh phí tự túc.

**6. Bảo mật thông tin.** Phiếu không ghi họ tên.

**7. Quyền tự nguyện và quyền rút lui.** Tham gia tự nguyện.

**8. Thông tin liên hệ.**
- Thắc mắc về nghiên cứu: BS.CKI Trần Thị Giả – Điện thoại: ……………………
- Thắc mắc về quyền của người tham gia: Hội đồng Y đức giả – Điện thoại: ……………………

Nghiên cứu đã được Hội đồng phê duyệt theo Quyết định số ……………… ngày ……/……/………

**PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU**

Tôi tự nguyện đồng ý tham gia nghiên cứu.

# PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU

**Mã nghiên cứu:** ……

# PHỤ LỤC F. KẾ HOẠCH THỰC HIỆN

## Tiến độ thực hiện

| # | Nội dung công việc | Thời gian dự kiến | Sản phẩm |
|---|---|---|---|
| 1 | Hoàn thiện đề cương | 11/2026 | Đề cương |
| 2 | Thu thập số liệu | 01–03/2027 | Phiếu |

## Dự trù kinh phí

| # | Nội dung chi | Số lượng | Đơn giá (đồng) | Thành tiền (đồng) |
|---|---|---|---|---|
| 1 | In phiếu khảo sát | ≈ 1.300 bản | ……… | ……… |
| | **Tổng cộng** | | | **………** |

## Kế hoạch quản lý dữ liệu

- **Phân quyền truy cập:** chỉ người được phân quyền.
- **Định danh duy nhất:** mã nghiên cứu của phiếu.
- **Thời hạn lưu trữ và hủy:** số liệu được lưu 2 năm sau khi kết thúc nghiên cứu, sau đó hủy có biên bản.

# PHỤ LỤC G. THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | {TEN} |
| Đơn vị thực hiện | Khoa Giả C1, Bệnh viện Quân y 175, Thành phố Hồ Chí Minh |
| Thiết kế | Nghiên cứu cắt ngang mô tả có phân tích |
| Thời gian thực hiện | Thực hiện dự kiến 11/2026–09/2027 |
| Kinh phí | Tự túc, không đề nghị cấp kinh phí |
"""

G2_MD = f"""# A3 | {STUDY}

## TÀI LIỆU 1. ĐƠN XIN PHÊ DUYỆT IRB

```
 Tên đề tài: {TEN}
 Thiết kế: Nghiên cứu cắt ngang · Cỡ mẫu: 1.000 · Thời gian thực hiện: 11/2026–09/2027
 Nơi thực hiện: Khoa Giả C1, Bệnh viện Quân y 175.
 Mục tiêu: {MT[0]}; {MT[1]}.
 Xung đột lợi ích: có xung đột lợi ích không tài chính.
 Thời gian lưu: lưu 2 năm sau kết thúc nghiên cứu.
```
"""

_KHONG = {"gia_tri": False, "giai_thich": "Không."}
KHOI_HDD = {
    "meta": {"quy_trinh": "rut_gon"},
    "phu_luc_10": {"phan_ba": {"A": {f"A{i}": _KHONG for i in range(1, 11)},
                               "B": {f"B{i}": _KHONG for i in range(1, 12)}},
                   "phan_nam": {k: _KHONG for k in ("C4_thu_nghiem_thuoc_can_thiep", "C5_nguy_co_toi_thieu_de_quan_ly",
                                                    "C6_nhieu_co_quan")}},
    "bia": {"don_vi_chu_tri": "KHOÁ DÙNG CHUNG — KHÔNG ĐƯỢC GHI ĐÈ"},
    "phu_luc_11": {"muc": {"1a": "Mô tả dự án giả định — nghiên cứu cắt ngang.", "3a": "Lợi ích cho Bệnh viện giả.",
                           "3c": "Đóng góp khoa học giả định (mục 2.6.1)."},
                   "thong_tin_sinh_vien": "Không áp dụng."},
    "goi_ky": [HSC.goi_ky("văn bản giả của Ban Giám đốc cho phép truy cập dữ liệu")],
}
# Khối đầy đủ như đề tài thật: mọi câu trả lời riêng của biểu mẫu (ô dùng chung vẫn do nguồn chung điền)
KHOI_HDD["phu_luc_10"]["phan_bon"] = {k: f"Mô tả giả định {k}." for k in (
    "C1_huy_dong_chon_nguoi_tham_gia", "C2_thu_thap_so_lieu", "C3_xin_chap_thuan_tu_nguyen")}
KHOI_HDD["phu_luc_10"]["thoi_gian"] = {"thu_nghiem": {"tu": "12/2026", "den": "12/2026"},
                                       "thu_thap": {"tu": "01/2027", "den": "03/2027"}}
KHOI_HDD["phu_luc_10"]["nghien_cuu_vien_khac"] = "Thư ký: " + HSC.can_nhap("họ tên thư ký giả")
for _k in HDD.MUC_PHU_LUC_11:
    KHOI_HDD["phu_luc_11"]["muc"].setdefault(_k, f"Trả lời giả định mục {_k}.")
KHOI_HDD["phu_luc_11"].update({
    "tinh_chat": {"duoc_tai_tro": True, "hoc_vien_sau_dai_hoc": False, "sinh_vien_dai_hoc": False,
                  "xin_phep_tap_the": False, "khong_thuoc_nhom_nao_tren": True},
    "quy_che_dac_biet": {k: False for k in HDD.QUY_CHE_DAC_BIET},
    "nguy_co_xay_ra_voi": {"nhom_nghien_cuu": False, "nguoi_tham_gia": True, "cong_dong_cua_truong": False,
                           "cong_dong_lon_hon": False},
    "chap_thuan_bo_mon_luu_tru": {"i": HSC.goi_ky("xác nhận lãnh đạo khoa nơi lưu trữ"), "ii": False},
})
KHOI_DTCS = {
    "thuyet_minh": {"m6_loai_de_tai": "Độc lập.", "m4_tong_kinh_phi": "KHÔNG ĐƯỢC GHI ĐÈ KINH PHÍ TỰ TÚC"},
    "m21_hang": [{"dau": "Thu thập số liệu", "chu_tri": "Thư ký khoa học"},
                 {"dau": "Dòng không còn trong đề cương", "chu_tri": "X"}],
}


def _meta(icf_waiver: bool = False) -> dict:
    return {
        "title": TEN,
        "administrative": {"principal_investigator": "Trần Thị Giả", "pi_title": "Bác sĩ Chuyên khoa I (BS.CKI)",
                           "pi_unit": DV_CONG_TAC, "don_vi_chu_tri": DV_CHU_TRI, "irb_name": "Hội đồng Y đức giả",
                           "sponsor": "Không có tài trợ bên ngoài — kinh phí tự túc"},
        "gate_params": {
            "G1": {"design": "cross_sectional", "objectives": [f"MT1 (mô tả): {MT[0]}", f"MT2 (phân tích): {MT[1]}"],
                   "study_period": "Thực hiện dự kiến 11/2026–09/2027."},
            "G2": {"icf_waiver_requested": icf_waiver, "recruitment_mode": "PROSPECTIVE_NEW_PARTICIPANTS",
                   "external_funding": False,
                   "coi": {"summary": "Có xung đột lợi ích không tài chính", "structural": "Chủ nhiệm công tác tại"
                           " khoa được đánh giá.", "management": "người ngoài khoa thu thập số liệu"},
                   "mien_icf_lap_luan": {"i_khong_kha_thi": LL[0], "ii_gia_tri_xa_hoi": LL[1],
                                         "iii_nguy_co_toi_thieu": LL[2]},
                   "da_soan": {"tl4": TL4}, "ho_so_hdd": KHOI_HDD},
            "G3": {"confirmed_n": 1000},
        },
        "data_governance": {"storage_location": "máy chủ giả của Bệnh viện", "access": "Phân quyền truy cập: chỉ"
                            " người được phân quyền"},
    }


SDT_GIA = "0900000001"  # bimat-mien: số điện thoại giả của đề tài giả
SO = {"phien_ban_schema": "1.0", "nguoi": {"tran-thi-gia": {
    "ho_ten": "Trần Thị Giả", "ngay_sinh": "01/01/1980", "gioi_tinh": "Nữ",
    "mobile": SDT_GIA,
    "email": "gia@example.org", "noi_lam_viec": {"ten_to_chuc": "Bệnh viện Quân y 175", "lanh_dao": "Lãnh Đạo Giả",
                                                 "dia_chi": "Địa chỉ cơ quan giả"},
    "dao_tao": [{"bac": "Chuyên khoa I", "chuyen_mon": "Nội tổng quát", "nam": "2019", "noi": "Học viện giả"}],
    "cong_tac": [{"thoi_gian": "2019 – nay", "vi_tri": "Bác sĩ điều trị", "to_chuc": "Khoa Giả C1"}],
    "nhiem_vu_chu_tri": [], "nhiem_vu_tham_gia": []}}}


@pytest.fixture()
def de_tai(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Đề tài giả đủ nguồn + bộ mẫu giả của hai bộ hồ sơ + sổ lý lịch giả."""
    mau_hdd = tmp_path / "mau_hdd"
    THDD._tao_bo_mau_gia(mau_hdd)
    mau_dtcs = tmp_path / "mau_dtcs"
    (mau_dtcs / "docx").mkdir(parents=True)
    TDTCS._mau_dang_ky(mau_dtcs / "docx" / f"{DTCS.TEN_TEP_MAU['dang_ky']}.docx")
    TDTCS._mau_thuyet_minh(mau_dtcs / "docx" / f"{DTCS.TEN_TEP_MAU['thuyet_minh']}.docx")
    TDTCS._mau_ly_lich(mau_dtcs / "docx" / f"{DTCS.TEN_TEP_MAU['ly_lich']}.docx")
    TDTCS._mau_pdx(mau_dtcs / "docx" / f"{DTCS.TEN_TEP_MAU['de_xuat']}.docx")
    so = tmp_path / "so"
    so.mkdir()
    (so / "LY_LICH_CA_NHAN.json").write_text(json.dumps(SO, ensure_ascii=False), encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_MAU_HDD_BVQY175", str(mau_hdd))
    monkeypatch.setenv(DTCS.ENV_MAU, str(mau_dtcs))
    monkeypatch.setenv(DTCS.ENV_CA_NHAN, str(so))
    monkeypatch.delenv(HDD.ENV_EMAIL_THU_KY, raising=False)

    def tao(icf_waiver: bool = False, meta_sua=None) -> Path:
        goc = tmp_path / ("exp_mien" if icf_waiver else "exp")
        tm = goc / STUDY
        tm.mkdir(parents=True, exist_ok=True)
        meta = _meta(icf_waiver)
        if meta_sua:
            meta_sua(meta)
        (tm / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
        dc = DE_CUONG
        if icf_waiver:
            dc = dc.replace("# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU",
                            f"# PHỤ LỤC B. ĐƠN ĐỀ NGHỊ MIỄN ĐỒNG THUẬN\n\n(1) {LL[0]}\n(2) {LL[1]}\n"
                            f"(3) {LL[2]}\n\nNhóm nghiên cứu cam kết: chỉ trích thông tin"
                            " cần thiết; kết quả chỉ công bố tổng hợp.\n\n# PHỤ LỤC B9. CŨ")
        (tm / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(dc, encoding="utf-8", newline="\n")
        g2 = G2_MD + (f"\n{' '.join(LL)}\n" if icf_waiver else "")
        (tm / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text(g2, encoding="utf-8", newline="\n")
        return goc
    return tao


def _chay_hdd(goc: Path, *lenh: str) -> int:
    return HDD.main([lenh[0], "--study", STUDY, "--exports-root", str(goc), *lenh[1:]])


def _chay_dtcs(goc: Path, *lenh: str) -> int:
    return DTCS.main([lenh[0], "--study", STUDY, "--exports-root", str(goc), *lenh[1:]])


def _json_hdd(goc: Path) -> dict:
    return json.loads((goc / STUDY / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json").read_text(encoding="utf-8"))


def _json_dtcs(goc: Path) -> dict:
    return json.loads((goc / STUDY / "ho_so_dtcs" / DTCS.TEN_JSON).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Ba loại ô chưa điền
# ---------------------------------------------------------------------------


def test_phan_loai_ba_loai_va_json_cu() -> None:
    co_so = HSC.ham_so_co(SO["nguoi"], "tran-thi-gia")
    assert HSC.phan_loai_o("x", HSC.goi_ky("ngày ký")) == "b"
    assert HSC.phan_loai_o("x", HSC.can_nhap("mã đăng ký")) == "c"
    assert HSC.phan_loai_o("x", HSC.so_ly_lich("tran-thi-gia", "mobile"), co_so) is None, "sổ có ⇒ đã điền"
    assert HSC.phan_loai_o("x", HSC.so_ly_lich("tran-thi-gia", "hoc_ham"), co_so) == "b", "sổ thiếu ⇒ tự khai"
    assert HSC.phan_loai_o("bia.ma_so", "[CẦN BÁC SĨ ĐIỀN]") == "c"
    assert HSC.phan_loai_o("mien_icf.ngay", "[CẦN BÁC SĨ ĐIỀN]") == "b"
    assert HSC.phan_loai_o("ly_lich_khoa_hoc[0].mobile", "[CẦN BÁC SĨ ĐIỀN]", co_so) == "a", "sổ có mà chưa điền"
    assert HSC.phan_loai_o("ly_lich_khoa_hoc[0].mobile", "[CẦN BÁC SĨ ĐIỀN]") == "b", "không sổ ⇒ tự khai"
    assert HSC.phan_loai_o("phu_luc_11.muc.2a", "[CẦN BỔ SUNG]") == "a"
    assert HSC.phan_loai_o("x", "đã điền") is None
    ba = HSC.dem_ba_loai({"a": "[CẦN BỔ SUNG]", "b": [HSC.goi_ky("ký")], "_nguon": {"z": "[CẦN x]"}})
    assert (len(ba["a"]), len(ba["b"]), len(ba["c"])) == (1, 1, 0), "khoá «_» không tính"


def test_o_danh_dau_chua_quyet_cua_nghien_cuu_vien_la_a() -> None:
    d = {"phu_luc_10": {"phan_ba": {"A": {"A1": {"gia_tri": None, "giai_thich": ""}}},
                        "phan_khai": {"ket_luan_chu_tich_hoi_dong": None}},
         "phu_luc_11": {"tinh_chat": {"duoc_tai_tro": False}}, "ly_lich_khoa_hoc": [{"ho_ten": "Trần Thị Giả"}]}
    ba = HDD.ba_loai_hdd(d, SO["nguoi"])
    assert [x[0] for x in ba["a"]] == ["phu_luc_10.phan_ba.A.A1.gia_tri"], "ô của Chủ tịch Hội đồng không tính"


def test_hoan_thien_docx_giai_dau(tmp_path: Path) -> None:
    p = tmp_path / "t.docx"
    d = docx.Document()
    d.add_paragraph(f"Điện thoại: {HSC.so_ly_lich('tran-thi-gia', 'mobile')}")
    d.add_paragraph(f"Học hàm: {HSC.so_ly_lich('tran-thi-gia', 'hoc_ham')}")
    d.add_paragraph(f"Mã số: {HSC.can_nhap('mã số được cấp')}")
    d.add_table(rows=1, cols=1).cell(0, 0).text = f"Ngày: {HSC.goi_ky('ngày ký đơn')}"
    d.save(str(p))
    ra = HSC.hoan_thien_docx(p, SO["nguoi"])
    van = "\n".join(HDD._van_ban_docx(p))
    assert SDT_GIA in van and "Học hàm: " + HSC.DONG_CHAM in van and "Mã số: " + HSC.DONG_CHAM in van
    assert not HSC.DAU_DANH_DAU.search(van)
    assert ra["can_nhap"] == ["mã số được cấp"] and ra["goi_ky"] == ["ngày ký đơn"] and ra["tu_khai"] == ["học hàm"]


def test_hoan_thien_docx_giai_dau_trong_bang_long(tmp_path: Path) -> None:
    p = tmp_path / "long.docx"
    d = docx.Document()
    o = d.add_table(rows=1, cols=1).cell(0, 0)
    o.add_table(rows=1, cols=1).cell(0, 0).text = f"Thư ký: {HSC.can_nhap('họ tên thư ký')}"
    d.save(str(p))
    ra = HSC.hoan_thien_docx(p, SO["nguoi"])
    assert not HSC.DAU_DANH_DAU.search("\n".join(HDD._van_ban_docx(p))), "bảng lồng trong ô cũng phải giải dấu"
    assert ra["can_nhap"] == ["họ tên thư ký"]


# ---------------------------------------------------------------------------
# Hồ sơ Hội đồng Đạo đức đọc cùng nguồn
# ---------------------------------------------------------------------------


def test_trich_hdd_doc_cung_nguon_g2(de_tai) -> None:
    goc = de_tai()
    d, ghi = HDD.trich_du_kien(goc, STUDY)
    assert d["bia"]["don_vi_chu_tri"] == DV_CHU_TRI and d["bia"]["co_quan_cong_tac"] == DV_CONG_TAC
    assert d["don_mau4"]["don_vi"] == DV_CONG_TAC and d["phu_luc_11"]["don_vi_chu_tri"] == DV_CHU_TRI
    assert d["bia"]["nghien_cuu_vien_chinh"] == "BS.CKI Trần Thị Giả"
    assert d["don_mau4"]["dien_thoai"] == HSC.so_ly_lich("tran-thi-gia", "mobile"), "ô cá nhân không vào JSON"
    assert d["bia"]["ma_so"].startswith(HSC.TIEN_TO_CAN_NHAP)
    assert d["phu_luc_11"]["muc"]["1c"] == f"Mục tiêu: (1) {MT[0]}; (2) {MT[1]}.", "mục tiêu G1 nguyên văn"
    assert d["phu_luc_11"]["muc"]["8a"].startswith("Không — Tự túc")
    assert "không tài chính" in d["phu_luc_11"]["muc"]["8c"] and "người ngoài khoa" in d["phu_luc_11"]["muc"]["8c"]
    assert d["phu_luc_11"]["luu_tru_so_nam"] == "02" and d["phu_luc_11"]["tinh_chat"]["duoc_tai_tro"] is False
    assert d["phu_luc_11"]["muc"]["6f_i_dia_diem"] == "Máy chủ giả của Bệnh viện"
    assert d["meta"]["co_mau_du_kien"] == "1.000" and d["meta"]["quy_trinh_de_xuat"] == "rut_gon"
    assert d["phu_luc_10"]["phan_khai"]["ket_luan_nghien_cuu_vien_chinh"] == "rut_gon"
    # Bản thông tin: nguyên văn phụ lục đề cương, xếp vào mục 1–6 của Mẫu 8; mục 3 thiếu ⇒ đoạn Tài liệu 4 gói G2
    icf = d["icf"]
    assert icf["muc"]["1"].startswith("Mục đích của nghiên cứu. Tìm hiểu tỷ lệ A.")
    assert "Nếu đồng ý tham gia, Ông/Bà sẽ:\n- Ký phiếu đồng ý;" in icf["muc"]["1"] and "*" not in icf["muc"]["1"]
    assert "Nguy cơ" in icf["muc"]["2"] and "Lợi ích" in icf["muc"]["2"]
    assert icf["muc"]["3"].startswith("Nghiên cứu quan sát; tổn hại"), "dự phòng mục bồi thường từ Tài liệu 4"
    assert any("mục 3 của Mẫu 8" in g for g in ghi)
    assert HSC.so_ly_lich("tran-thi-gia", "mobile") in icf["muc"]["4"]
    assert HSC.TIEN_TO_CAN_NHAP in icf["muc"]["4"], "số quyết định/điện thoại Hội đồng là dữ kiện cần nhập"
    assert icf["ten_muc_bo_sung"] == {"7": "Nguồn kinh phí và xung đột lợi ích"}
    assert icf["phien_ban"] == "Tài liệu riêng. Phiên bản 1.0, ngày ……/……/2026."
    assert HSC.dem_ba_loai(d, HSC.ham_so_co(SO["nguoi"], "tran-thi-gia"))["a"] == [], "(a) = 0"


def test_khoi_rieng_ap_duoc_nhung_khong_ghi_de_nguon_chung(de_tai) -> None:
    goc = de_tai()
    d, ghi = HDD.trich_du_kien(goc, STUDY)
    assert d["phu_luc_11"]["muc"]["1a"] == KHOI_HDD["phu_luc_11"]["muc"]["1a"]
    assert d["phu_luc_11"]["thong_tin_sinh_vien"] == "Không áp dụng."
    assert d["bia"]["don_vi_chu_tri"] == DV_CHU_TRI, "khoá dùng chung trong khối bị bỏ"
    assert any("bia.don_vi_chu_tri" in g for g in ghi)
    assert d["goi_ky"] == KHOI_HDD["goi_ky"]


def test_khoi_rieng_khong_ghi_o_dung_chung_ke_ca_khi_nguon_vang(de_tai) -> None:
    def bo_don_vi(m: dict) -> None:
        m["administrative"].pop("don_vi_chu_tri")
        m["administrative"].pop("pi_unit")
    goc = de_tai(meta_sua=bo_don_vi)
    d, ghi = HDD.trich_du_kien(goc, STUDY)
    assert "KHÔNG ĐƯỢC GHI ĐÈ" not in d["bia"]["don_vi_chu_tri"], "nguồn vắng ⇒ ô (a), không lấy khối riêng"
    assert any("bia.don_vi_chu_tri" in g for g in ghi)


def test_mien_dong_thuan_doc_lap_luan_g2_va_ke_hoach_du_lieu(de_tai) -> None:
    goc = de_tai(icf_waiver=True)
    d, _ = HDD.trich_du_kien(goc, STUDY)
    mi = d["mien_icf"]
    assert mi["ba_dieu_kien_cioms"]["i_khong_kha_thi"] == LL[0], "cùng lập luận đã chốt ở G2"
    assert mi["dam_bao_bao_mat"]["ke_hoach_huy"].startswith("số liệu được lưu 2 năm")
    assert mi["dam_bao_bao_mat"]["ma_hoa"] == "mã nghiên cứu của phiếu."
    assert mi["ngay"].startswith(HSC.TIEN_TO_GOI_KY) and mi["chu_nhiem"] == "BS.CKI Trần Thị Giả"
    assert mi["cam_ket"] == ["chỉ trích thông tin cần thiết.", "kết quả chỉ công bố tổng hợp."]
    assert "không tài chính" in mi["xung_dot_loi_ich"].lower()


def test_dung_kiem_hdd_sach_goi_ky_va_du_kien_can_nhap(de_tai, capsys) -> None:
    goc = de_tai()
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_hdd(goc, "dung", "--quy-trinh", "ca_hai", "--ghi") == 0
    ra = goc / STUDY / "ho_so_hdd"
    for p in ra.glob("*.docx"):
        van = "\n".join(HDD._van_ban_docx(p))
        assert "[CẦN" not in van and not HSC.DAU_DANH_DAU.search(van), p.name
    don = "\n".join(HDD._van_ban_docx(next(ra.glob("MAU4_*.docx"))))
    assert SDT_GIA in don and "gia@example.org" in don, "ô cá nhân lấy từ sổ lúc dựng Word"
    dm = (ra / f"DANH_MUC_HO_SO_HDD_{STUDY}.md").read_text(encoding="utf-8")
    assert "## Gói ký" in dm and "## Dữ kiện cần nhập" in dm and "Việc CHỈ bác sĩ" not in dm
    assert "Mã số đề tài" in dm and "Văn bản giả của Ban Giám đốc" in dm and "Họ tên thư ký giả" in dm
    assert "Xác nhận lãnh đạo khoa nơi lưu trữ" in dm, "ô đánh dấu thuộc gói ký vào danh mục"
    capsys.readouterr()
    assert _chay_hdd(goc, "kiem") == 0
    out = capsys.readouterr().out
    assert "(a) suy được từ nguồn đã chốt 0" in out and "lệch 0" in out


@pytest.mark.parametrize("sua,truong", [
    (lambda d: d["bia"].__setitem__("don_vi_chu_tri", "Khoa Khác"), "đơn vị chủ trì"),
    (lambda d: d["phu_luc_11"]["muc"].__setitem__("1c", "Mục tiêu khác hẳn."), "mục tiêu"),
    (lambda d: d["phu_luc_11"]["muc"].__setitem__("8c", "Không có xung đột lợi ích."), "xung đột lợi ích"),
    (lambda d: d["phu_luc_11"].__setitem__("luu_tru_so_nam", "05"), "quản trị dữ liệu"),
    (lambda d: d["phu_luc_11"]["muc"].__setitem__("10", "Nghiên cứu đoàn hệ tiến cứu."), "thiết kế"),
])
def test_kiem_bat_lech_nhat_quan(de_tai, capsys, sua, truong) -> None:
    goc = de_tai()
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_hdd(goc, "dung", "--quy-trinh", "rut_gon", "--ghi") == 0
    p = goc / STUDY / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    if truong == "thiết kế":
        d["phu_luc_11"]["muc"]["1a"] = "Mô tả dự án."
    sua(d)
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")
    capsys.readouterr()
    assert _chay_hdd(goc, "kiem") == 1
    out = capsys.readouterr().out
    assert f"[LỆCH] {truong} — hồ sơ Hội đồng Đạo đức" in out


def test_mien_lech_lap_luan_bi_bat(de_tai) -> None:
    goc = de_tai(icf_waiver=True)
    d, _ = HDD.trich_du_kien(goc, STUDY)
    d["mien_icf"]["ba_dieu_kien_cioms"]["ii_gia_tri_xa_hoi"] = "Lập luận khác hẳn."
    dong = HSC.doi_chieu(HSC.NguonDeTai(goc, STUDY, SO["nguoi"]), d, None)
    lech = [x for x in dong if x["ket"] == "lech"]
    assert [(x["truong"], x["tai_lieu"]) for x in lech] == [("căn cứ miễn đồng thuận", "hồ sơ Hội đồng Đạo đức")]


def test_thiet_ke_khong_neu_o_ho_so_la_khong_do_duoc(de_tai) -> None:
    goc = de_tai()
    d, _ = HDD.trich_du_kien(goc, STUDY)
    d["phu_luc_11"]["muc"]["1a"] = "Mô tả dự án."
    d["phu_luc_11"]["muc"]["10"] = "Tóm tắt không nêu thiết kế."
    dong = HSC.doi_chieu(HSC.NguonDeTai(goc, STUDY, SO["nguoi"]), d, None)
    tk = next(x for x in dong if x["truong"] == "thiết kế" and x["tai_lieu"] == "hồ sơ Hội đồng Đạo đức")
    assert tk["ket"] == "khong_do_duoc", "vắng ≠ lệch; nêu thiết kế khác mới là lệch"


def test_kiem_bao_nguon_doi_sau_luot_trich(de_tai, capsys) -> None:
    goc = de_tai()
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_hdd(goc, "dung", "--quy-trinh", "rut_gon", "--ghi") == 0
    p = goc / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nBổ sung.\n", encoding="utf-8", newline="\n")
    capsys.readouterr()
    assert _chay_hdd(goc, "kiem") == 1
    assert "đổi sau lượt trích" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Hồ sơ đề tài cơ sở đọc cùng nguồn
# ---------------------------------------------------------------------------


def test_trich_dtcs_tu_tuc_goi_ky_can_nhap_va_khoi(de_tai) -> None:
    goc = de_tai(meta_sua=lambda m: m["gate_params"].setdefault("G1", {}).__setitem__("ho_so_dtcs", KHOI_DTCS))
    d, ghi = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    tm = d["thuyet_minh"]
    assert tm["m4_tong_kinh_phi"] == "Tự túc, không đề nghị cấp kinh phí.", "khối không ghi đè kinh phí đã suy"
    assert tm["m5_khoan_chi"].startswith("Không áp dụng — đề tài tự túc")
    assert tm["phu_luc_tmdt"].endswith("In phiếu khảo sát.") and "Tổng cộng" not in tm["phu_luc_tmdt"]
    assert all(h["kinh_phi"] == "Tự túc" for h in tm["m21_tien_do"])
    assert tm["m10_don_vi_chu_tri"] == DV_CHU_TRI and d["dang_ky"]["don_vi_chu_tri"] == DV_CHU_TRI
    assert tm["m10_thu_truong_don_vi"].startswith(HSC.TIEN_TO_GOI_KY)
    assert d["nhan_su"][0]["ho_ten"] == "Trần Thị Giả" and d["nhan_su"][1]["ho_ten"].startswith(HSC.TIEN_TO_CAN_NHAP)
    assert tm["m6_loai_de_tai"] == "Độc lập."
    hang = {h["noi_dung"]: h for h in tm["m21_tien_do"]}
    assert hang["Thu thập số liệu"]["chu_tri"] == "Thư ký khoa học"
    assert any("Dòng không còn" in g for g in ghi), "dòng khối không khớp tiến độ ⇒ bỏ và báo"
    assert tm["m25_tac_dong"]["25.2"] == "Đóng góp khoa học giả định (mục 2.6.1 của đề cương).", "từ khối HĐĐĐ"
    assert tm["m25_tac_dong"]["25.3"] == "Lợi ích cho Bệnh viện giả."
    assert tm["m17_cong_viec"].startswith("Các công việc thực hiện chung")
    assert "(2) Thu thập số liệu" in tm["m17_cong_viec"]


def test_dtcs_dung_kiem_sach_va_doi_chieu(de_tai, capsys) -> None:
    goc = de_tai()
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "dung", "--ghi") == 0
    ra = goc / STUDY / "ho_so_dtcs"
    for p in ra.glob("*.docx"):
        van = "\n".join(HDD._van_ban_docx(p))
        assert not HSC.DAU_DANH_DAU.search(van), p.name
    dm = (ra / f"DANH_MUC_HO_SO_DTCS_{STUDY}.md").read_text(encoding="utf-8")
    assert "## Gói ký" in dm and "## Dữ kiện cần nhập" in dm and "Việc của bác sĩ" not in dm
    capsys.readouterr()
    _chay_dtcs(goc, "kiem")
    out = capsys.readouterr().out
    assert "Đối chiếu nhất quán" in out and "lệch 0" in out


def test_dtcs_van_ban_quy_pham_xac_minh_qua_danh_muc_giu_chuan(tmp_path: Path) -> None:
    import toan_van_trich_dan as TVTD

    dong = "Bộ Y tế. Quyết định số 1/QĐ-BYT ngày 01/01/2024 ban hành hướng dẫn giả. Hà Nội: Bộ Y tế; 2024."
    khoa = sorted(TVTD.khoa_tltk(dong))[0]
    dat = {"dinh_danh": {"dat": True, "mo_ta": "văn bản quy phạm: nhận diện cơ quan ban hành + số hiệu"},
           "loai_nguon": {"dat": True}, "rut_bai": {"dat": True}}
    tn = {"loai": {}, "kiem_rut": {}, "a12_rut": {}, "a12_meta": {}, "trich": {},
          "giu": {khoa: {"khoa": [khoa], "tieu_chi": dat}}}
    assert DTCS.xac_minh_tltk(dong, tn)[0] == "da_xac_minh"
    tn["giu"][khoa]["tieu_chi"]["loai_nguon"] = {"dat": False}
    assert DTCS.xac_minh_tltk(dong, tn)[0] == "khong_dinh_danh", "chưa đạt mọi tiêu chí ⇒ không xác minh"
