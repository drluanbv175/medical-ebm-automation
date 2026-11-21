"""K15 (khẳng định mơ hồ không nguồn) + luật định nghĩa bệnh + lớp toàn văn đọc câu nêu tỷ lệ (21/11/2026).

Bác sĩ 21/11/2026: «các lớp kiểm phải nghiêm ngặt từng câu từng chữ … tất cả đều phải dựa trên chứng cứ có độ tin cậy
cao không được trình bày chung chung, sơ xài» và «phải ghi đúng theo tiêu chuẩn bệnh thận mạn chứ không phải cứ albumin
niệu tăng là rất chung chung». Mỗi ca khoá một lỗi THẬT đo trên hai đề cương C1a/BTM.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import duyet_kiem_may_api as DKM  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDC  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import kiem_trich_dan_toan_van as KTV  # noqa: E402


def _de_cuong(than_tq: str, than_pp: str = "Cỡ mẫu tính theo công thức.") -> str:
    return ("# ĐẶT VẤN ĐỀ\n\nĐặt vấn đề có nguồn [1].\n\n# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU\n\n" + than_tq + "\n\n"
            "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n" + than_pp + "\n\n"
            "# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN\n\nĐa số người bệnh sẽ được mô tả theo nhóm tuổi.\n")


# ── K15 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cau,tu", [
    ("Bên cạnh đó, phần lớn nghiên cứu trong nước đo thời gian chờ bằng tự báo cáo.", "phần lớn"),
    ("Đề tài có thiết kế chặt chẽ hơn mức thường gặp ở các đề tài cùng chủ đề.", "thường gặp"),
    ("Các bằng chứng trên gần như toàn bộ là nghiên cứu quan sát, chủ yếu ở Âu – Mỹ – Úc.", "gần như toàn bộ"),
    ("SGLT2i có lợi ích đã được chứng minh được khuyến cáo (khuyến cáo 11.7a); GLP-1 RA cũng được khuyến cáo [13].",
     "đã được chứng minh"),
    ("Nhiều người ĐTĐ típ 2 trì hoãn insulin dù đã có chỉ định.", "Nhiều người"),
    ("Xuất huyết tiêu hoá trên ở người cao tuổi thường liên quan thuốc tự mua.", "thường liên quan"),
])
def test_k15_bat_khang_dinh_mo_ho_khong_nguon(cau, tu):
    loi = KDC.loi_k15(_de_cuong(cau))
    assert len(loi) == 1 and f"«{tu}»" in loi[0]


def test_k15_menh_de_co_nguon_thi_dat():
    md = _de_cuong("Phần lớn nghiên cứu trong nước đo thời gian chờ bằng phỏng vấn người bệnh [41].")
    assert KDC.loi_k15(md) == []


def test_k15_bo_qua_ten_bang_va_chuong_phuong_phap_va_du_kien_ket_qua():
    md = _de_cuong("**Bảng 1.1. Một số nghiên cứu chính về chuỗi chăm sóc thận**",
                   than_pp="Phần lớn hồ sơ được trích trên eHospital.")
    assert KDC.loi_k15(md) == []


def test_k15_nam_trong_ham_kiem_tong():
    nguon = Path(KDC.__file__).read_text(encoding="utf-8")
    assert "loi.extend(loi_k15(md))" in nguon


# ── Luật định nghĩa bệnh trong lời dặn hai lớp ───────────────────────────────────────────────────────────────────
def test_loi_dan_hai_lop_doi_khop_tieu_chuan_chan_doan():
    for he in (KND.HE_THONG, KTV.HE_THONG):
        assert "TIÊU CHUẨN CHẨN ĐOÁN" in he and "KHÔNG phải bệnh thận mạn" in he
        assert "«bệnh thận mạn» ⇒ ho_tro_mot_phan" in he  # mức phán bắt buộc khi định nghĩa lệch


# ── Lớp toàn văn đọc câu nêu tỷ lệ dù abstract đã cho qua ────────────────────────────────────────────────────────
BC = {"cau": [{"id": "C061", "cau": "Tỷ lệ bệnh thận mạn là 15,32% tại Bệnh viện Nguyễn Trãi [10]."},
              {"id": "C087", "cau": "Tính hệ số kappa Cohen kèm khoảng tin cậy [53]."}],
      "ket_qua": [{"id": "C061", "so": 10, "muc": "ho_tro", "co": []},
                  {"id": "C087", "so": 53, "muc": "ho_tro", "co": []}]}


def test_cau_ty_le_ho_tro_van_len_lop_toan_van():
    assert [c["id"] for c in KTV.cap_can_xem(BC)] == ["C061"]
    assert KTV.cap_can_xem(BC, ca_cau_ty_le=False) == []


def test_toan_van_bat_dinh_nghia_lech_thi_thanh_muc_phan_xu(tmp_path):
    d = tmp_path / "exports" / "S1"
    (d / "kiem_may_api").mkdir(parents=True)
    tep = d / "DE_CUONG_NOP_HOI_DONG_S1.md"
    tep.write_text("đề cương\n", encoding="utf-8", newline="\n")
    bc = {**BC, "tep": tep.name, "luc": "2026-11-21T09:00:00"}
    (d / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").write_text(json.dumps(bc, ensure_ascii=False),
                                                                    encoding="utf-8", newline="\n")
    (d / "kiem_may_api" / "A12_TOAN_VAN_S1.json").write_text(json.dumps({"a12_luc": "2026-11-21T09:00:00", "ket_qua": [
        {"id": "C061", "so": 10, "muc_toan_van": "ho_tro_mot_phan", "ly_do": "chỉ dùng eGFR", "nguon": "EndNote"}]},
        ensure_ascii=False), encoding="utf-8", newline="\n")
    muc = DKM.doc_bao_cao("S1", tmp_path)["A12"]["muc"]
    assert [m["khoa"] for m in muc] == ["A12|C061|10"]
    assert any("chỉ dùng eGFR" in c for c in muc[0]["chi_tiet"])


# ── Thang mức liên quan G0: nguyên tắc áp dụng dùng chung agent + máy chấm (21/11/2026) ──────────────────────────────
def test_thang_g0_co_bon_nguyen_tac_ap_dung():
    import g0_tong_hop as T  # noqa: PLC0415
    import kiem_tong_quan_g0_api as KG  # noqa: PLC0415

    thang = T.thang_lien_quan()
    for cum in ("quần thể RỘNG HƠN", "đo HẸP HƠN hay KHÁC CÁCH", "nguồn không thực nghiệm", "khảo sát nhân viên y tế"):
        assert cum in thang
    assert "thang_lien_quan" in Path(KG.__file__).read_text(encoding="utf-8")  # máy chấm đọc cùng một nguồn


# ── K16: phạm vi tìm phải khớp nhật ký PRISMA-S của đề tài ───────────────────────────────────────────────────────────
NHAT_KY = ("# PRISMA-S\n\n## 1. Nguồn đã tra\n| Europe PMC | 2026-10-14 |\n| Crossref | 2026-10-11 |\n\n"
           "**Giới hạn:** y văn không có DOI (luận văn, kỷ yếu) chưa tra.\n\n"
           "## 4. Nguồn KHÔNG tra (để PI tra theo đề cương)\n\nThư viện luận văn, kỷ yếu hội nghị, Scopus.\n")


def _thu_muc_nk(tmp_path):
    (tmp_path / "G0_TIM_BO_SUNG_PRISMA_S_S1.md").write_text(NHAT_KY, encoding="utf-8", newline="\n")
    return tmp_path


def test_k16_bat_khang_dinh_da_tra_nguon_khong_co_trong_nhat_ky(tmp_path):
    md = "Việc rà y văn được thực hiện trên Europe PMC và Google Scholar, cùng thư viện luận văn và kỷ yếu hội nghị."
    loi = KDC.loi_k16(_thu_muc_nk(tmp_path), md)
    assert {x.split("«")[1].split("»")[0] for x in loi} == {"Google Scholar", "luận văn", "kỷ yếu"}


def test_k16_cau_co_phu_dinh_hoac_nguon_da_tra_thi_dat(tmp_path):
    d = _thu_muc_nk(tmp_path)
    assert KDC.loi_k16(d, "Luận văn và kỷ yếu hội nghị chưa được tra cứu có hệ thống.") == []
    assert KDC.loi_k16(d, "Chúng tôi tra Europe PMC và Crossref.") == []


def test_k16_khong_nhat_ky_thi_khong_ket_luan(tmp_path):
    assert KDC.loi_k16(tmp_path, "Đã tra Google Scholar.") == []
    assert KDC.nhat_ky_prisma_s(tmp_path) is None
