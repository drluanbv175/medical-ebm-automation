"""Giai đoạn «Công cụ & phương pháp thu thập» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Tiếp tục giai đoạn tiếp theo» — «đảm bảo sự đồng bộ xuyên suốt và chính xác nhất». Kiểm tay C1a:
(1) đề cương nộp + phiếu thông tin G2 hứa «nhập kép», «hủy bảng đối chiếu trong 30 ngày», «lưu 2 năm», «hai người ngoài
khoa mã hoá câu hỏi mở» nhưng DMP G5 chỉ có khuôn chung (kể cả «không dùng một thời hạn cứng»); (2) khối COSMIN của A2
ghi «[CẦN … CVI]» trong khi đề cương 4.5 đã có CVI, EFA/CFA, Cronbach. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nhat_quan_xuyen_cong as NQ  # noqa: E402
import quy_trinh_du_lieu as QTD  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import run_g5_auto as G5  # noqa: E402

STUDY = "ZZTEST-CONG-CU-20261115"
DC = """# ĐỀ CƯƠNG
## 3.2. Công cụ đo lường sự hài lòng của người bệnh
### 3.2.1. Các thang đo quốc tế
Nhiều nghiên cứu dùng phân tích nhân tố khám phá cho SERVQUAL.
# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP
## 4.5. Công cụ thu thập số liệu
### 4.5.1. Bộ câu hỏi
Phiếu do nhóm tự xây dựng gồm sáu lĩnh vực. Hội đồng chuyên gia chấm CVI; phỏng vấn nhận thức 10 người bệnh.
### 4.5.3. Đánh giá đặc tính đo lường của bộ câu hỏi trong mẫu nghiên cứu
Cronbach's alpha cho từng lĩnh vực; hiệu ứng sàn – trần; phân tích nhân tố khám phá và nhân tố khẳng định.
Độ tin cậy lặp lại, sai số đo lường và mức thay đổi tối thiểu có ý nghĩa không thuộc phạm vi đề tài.
## 4.7. Quy trình thu thập
Phiếu tự điền khuyết danh bỏ vào hòm phiếu kín. Nhập kép toàn bộ phiếu.
## 6.5. Bảo mật
Số liệu giấy và điện tử được lưu 2 năm sau khi kết thúc nghiên cứu. Bảng đối chiếu được hủy trong vòng 30 ngày.
"""
G2 = """# GÓI ĐẠO ĐỨC
- Phiếu khảo sát không ghi họ tên. Bảng đối chiếu mã giữ và hủy trong vòng 30 ngày.
- Số liệu lưu 2 năm sau khi kết thúc nghiên cứu rồi hủy.
"""
BANG = [
    ("thu_thap", "Phiếu tự điền khuyết danh, bỏ vào hòm phiếu kín", "đề cương 4.7", "hòm phiếu kín", ""),
    ("an_danh", "Phiếu không ghi họ tên", "đề cương 4.7; G2", "khuyết danh", "không ghi họ tên"),
    ("nhap_lieu", "Nhập kép toàn bộ phiếu", "đề cương 4.7", "Nhập kép toàn bộ phiếu", ""),
    ("huy_bang_noi", "Bảng đối chiếu hủy trong vòng 30 ngày, có biên bản", "đề cương 6.5; G2",
     "hủy trong vòng 30 ngày", "hủy trong vòng 30 ngày"),
    ("luu_tru", "Số liệu lưu 2 năm sau khi kết thúc nghiên cứu", "đề cương 6.5; G2",
     "lưu 2 năm sau khi kết thúc nghiên cứu", "lưu 2 năm sau khi kết thúc nghiên cứu"),
    ("huy_du_lieu", "Phiếu giấy hủy bằng máy hủy tài liệu", "đề cương 6.5", "", ""),
]


def _de_tai(tmp_path: Path, *, bang=BANG, dmp: bool = True, g2: str = G2, dc: str = DC) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    meta = {"topic": "Sự hài lòng của người bệnh", "design_code": "cross_sectional",
            "gate_params": {"G1": {"design": "cross_sectional",
                                   "data_collection_method": "Thu MỚI: phiếu tự điền khuyết danh"}}}
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(dc, encoding="utf-8", newline="\n")
    (d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text(g2, encoding="utf-8", newline="\n")
    if bang is not None:
        with (d / QTD.TEP).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(QTD.COT)
            for r in bang:
                w.writerow(list(r) + [""])
    if dmp:
        dong, _, _ = QTD.doc_bang(d)
        noi_dung = "# A6\n" + "\n".join(QTD.khoi_dmp(dong or [])) + "\n" + (QTD.dong_luu_tru(dong or []) or "") + "\n"
        (d / f"G5_A6_DATA_MGMT_{STUDY}.md").write_text(noi_dung, encoding="utf-8", newline="\n")
    return d


def _ma(kq: dict) -> list:
    return sorted(x["ma"] for x in kq["loi"] + kq["mau_thuan"] + kq["canh_bao"])


def _meta(d: Path) -> dict:
    return json.loads((d / "study_meta.json").read_text(encoding="utf-8"))


# ── ① bảng quy trình dữ liệu ↔ đề cương ↔ G2 ↔ DMP ─────────────────────────────────────────────────────────────────
def test_quy_trinh_dat_khi_moi_tai_lieu_mang_quyet_dinh(tmp_path):
    d = _de_tai(tmp_path)
    kq = QTD.kiem(d, STUDY)
    assert kq["trang_thai"] == QTD.TRANG_THAI_DAT and _ma(kq) == []
    assert NQ._truc_quy_trinh_du_lieu(d, STUDY, _meta(d))["muc"] == NQ.MUC_KHOP


def test_dmp_khuon_chung_thieu_quyet_dinh_la_lech_mem(tmp_path):
    d = _de_tai(tmp_path, dmp=False)
    (d / f"G5_A6_DATA_MGMT_{STUDY}.md").write_text(
        "- **Lưu trữ/hủy:** thời hạn theo IRB; không dùng một thời hạn cứng cho mọi đề tài.\n", encoding="utf-8",
        newline="\n")
    kq = QTD.kiem(d, STUDY)
    assert set(_ma(kq)) == {"QT-06"} and len(kq["loi"]) == len(BANG)
    assert NQ._truc_quy_trinh_du_lieu(d, STUDY, _meta(d))["muc"] == NQ.MUC_LECH_MEM


def test_neo_de_cuong_va_neo_g2_khong_co(tmp_path):
    d = _de_tai(tmp_path, dc=DC.replace("hòm phiếu kín", "hòm thư"), g2=G2.replace("không ghi họ tên", "ẩn danh"))
    assert {x["ma"] for x in QTD.kiem(d, STUDY)["loi"]} == {"QT-04", "QT-05"}


def test_muc_hua_nguoi_tham_gia_phai_co_neo_g2(tmp_path):
    bang = [r if r[0] != "luu_tru" else r[:4] + ("",) for r in BANG]
    d = _de_tai(tmp_path, bang=bang)
    loi = QTD.kiem(d, STUDY)["loi"]
    assert [x["ma"] for x in loi] == ["QT-05"] and "luu_tru" in loi[0]["noi_dung"]


def test_mau_thuan_so_nam_luu_tru_la_lech_cung(tmp_path):
    d = _de_tai(tmp_path, g2=G2 + "- Hồ sơ được lưu trữ 5 năm sau khi kết thúc.\n")
    kq = QTD.kiem(d, STUDY)
    assert [x["ma"] for x in kq["mau_thuan"]] == ["QT-07"] and "5" in kq["mau_thuan"][0]["noi_dung"]
    assert NQ._truc_quy_trinh_du_lieu(d, STUDY, _meta(d))["muc"] == NQ.MUC_LECH_CUNG


def test_mau_thuan_so_ngay_huy_bang_noi(tmp_path):
    d = _de_tai(tmp_path, dc=DC + "Bảng đối chiếu mã hủy sau 60 ngày.\n")
    assert [x["ma"] for x in QTD.kiem(d, STUDY)["mau_thuan"]] == ["QT-07"]


def test_quyet_dinh_cho_pi_la_can_xem_va_thieu_muc_bat_buoc(tmp_path):
    bang = [r if r[0] != "luu_tru" else ("luu_tru", "[CẦN PI QUYẾT — thời hạn]", "—", "", "") for r in BANG]
    d = _de_tai(tmp_path, bang=[r for r in bang if r[0] != "huy_du_lieu"], dmp=False)
    kq = QTD.kiem(d, STUDY)
    assert [x["ma"] for x in kq["canh_bao"]] == ["QT-03"]
    assert any(x["ma"] == "QT-02" and "huy_du_lieu" in x["noi_dung"] for x in kq["loi"])


def test_chua_co_bang_la_chua_du(tmp_path):
    d = _de_tai(tmp_path, bang=None, dmp=False)
    assert QTD.kiem(d, STUDY)["trang_thai"] == QTD.TRANG_THAI_KHONG_CO
    assert NQ._truc_quy_trinh_du_lieu(d, STUDY, _meta(d))["muc"] == NQ.MUC_CHUA_DU


# ── ② bộ sinh G5 in quy trình đã chốt ─────────────────────────────────────────────────────────────────────────────
def test_g5_in_khoi_quy_trinh_va_dong_luu_tru(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, dmp=False)
    monkeypatch.setattr(G5, "BASE", tmp_path)
    khoi = "\n".join(G5._khoi_quy_trinh(STUDY))
    assert "PHẦN 1B" in khoi and all(r[1] in khoi for r in BANG)
    dong = G5._dong_luu_tru_huy(STUDY)
    assert "lưu 2 năm" in dong and "không dùng một thời hạn cứng" not in dong
    (d / QTD.TEP).unlink()
    assert G5._khoi_quy_trinh(STUDY) == [] and "không dùng một thời hạn cứng" in G5._dong_luu_tru_huy(STUDY)


# ── ③ khối COSMIN của A2 truy nguyên về đề cương ────────────────────────────────────────────────────────────────────
def test_cosmin_truy_nguyen_dung_muc_cong_cu(tmp_path):
    d = _de_tai(tmp_path)
    bang = "\n".join(G1._bang_cosmin(d, STUDY))
    assert "Độ giá trị nội dung (content validity): đã có — đề cương nộp mục 4.5.1" in bang
    # 3.2.1 (tổng quan) cũng nhắc «nhân tố khám phá» nhưng mục công cụ 4.5.3 được ưu tiên
    assert "Độ giá trị cấu trúc (EFA/CFA): đã có — đề cương nộp mục 4.5.3" in bang
    assert "Độ tin cậy lặp lại (test–retest ICC): ngoài phạm vi đề tài (đề cương nộp mục 4.5.3 ghi rõ)" in bang
    assert "Dịch thuật & thích nghi văn hóa (nếu công cụ gốc nước ngoài): không áp dụng" in bang
    assert "Độ giá trị hội tụ/phân biệt: [CẦN" in bang  # đề cương chưa nói ⇒ vẫn đòi
    assert G1._bang_cosmin(tmp_path / "khong_co", STUDY) is None


def test_truc_cong_cu_do_luong_a2_cu_la_can_xem_moi_la_khop(tmp_path):
    d = _de_tai(tmp_path, dc=DC.replace("Cronbach's alpha", "Cronbach's alpha; tương quan hội tụ với G1"))
    (d / "pha_cong_cu").mkdir()
    a2 = d / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md"
    a2.write_text("- Độ giá trị nội dung (content validity): [CẦN hội đồng chuyên gia + hệ số CVI]\n", encoding="utf-8",
                  newline="\n")
    assert NQ._truc_cong_cu_do_luong(d, STUDY, _meta(d))["muc"] == NQ.MUC_CAN_XEM
    a2.write_text(G1._specialist_module_section("prom_tool", d, STUDY), encoding="utf-8", newline="\n")
    k = NQ._truc_cong_cu_do_luong(d, STUDY, _meta(d))
    assert k["muc"] == NQ.MUC_KHOP, k["ghi_chu"]
