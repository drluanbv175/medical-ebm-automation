#!/usr/bin/env python3
"""Hồ sơ Hội đồng Đạo đức trong nghiên cứu y sinh học, Bệnh viện Quân y 175.

Mục đích
--------
Dựng NHÁP toàn bộ Quyển 1 (Thuyết minh đề cương) + Quyển 2 (Hồ sơ đăng ký
đánh giá đạo đức) theo đúng bộ mẫu của Hội đồng Đạo đức BVQY175, cho MỖI
đề tài trong `exports/<mã>/`. Công cụ KHÔNG tự ký, KHÔNG tự gửi email,
KHÔNG tự chuyển lệ phí — những việc đó thuộc về bác sĩ (chủ nhiệm đề tài).

Ba lệnh con, theo đúng thứ tự dùng:

    python3 tools/ho_so_hdd_bvqy175.py mau
        Dò bộ mẫu của bệnh viện (ngoài git). Báo tệp nào có/thiếu.
        KHÔNG BAO GIỜ tự báo "đạt" khi thiếu tệp (mã thoát 2).

    python3 tools/ho_so_hdd_bvqy175.py trich --study <mã> [--ghi] [--ghi-de]
        Trích TẤT ĐỊNH dữ kiện đã chốt của đề tài (study_meta.json,
        G2_A3_ETHICS_PACKAGE_*.md, G2_checkpoint.json, đề cương nộp) vào
        exports/<mã>/ho_so_hdd/HO_SO_HDD_BVQY175.json. Ô không trích được
        ghi "[CẦN ...]", KHÔNG BAO GIỜ bịa. Chạy khô mặc định; `--ghi` mới
        ghi tệp; tệp đã có chỉ được BỔ SUNG khoá còn thiếu (không ghi đè
        giá trị đã có) trừ khi dùng thêm `--ghi-de` (có sao lưu).

    python3 tools/ho_so_hdd_bvqy175.py dung --study <mã> \
        --quy-trinh rut_gon|day_du|ca_hai [--ghi]
        Điền các mẫu Word của bệnh viện bằng dữ kiện trong JSON ở trên,
        xuất vào exports/<mã>/ho_so_hdd/. Giữ bố cục mẫu gốc (Times New
        Roman, ô đánh dấu ☒/☐). Sinh thêm DANH_MUC_HO_SO_HDD_<mã>.md.

    python3 tools/ho_so_hdd_bvqy175.py kiem --study <mã>
        Kiểm JSON + tệp Word: đủ khoá theo schema? khớp đề cương nộp?
        logic ô có mâu thuẫn? tệp Word có mới hơn JSON? còn bao nhiêu ô
        "[CẦN"? Mã thoát: 0 sạch · 1 còn việc · 2 không đo được.

Cấu trúc JSON (`phien_ban_schema`)
----------------------------------
Khoá cấp 1:

- `phien_ban_schema` (str) — phiên bản schema, hiện "1.0".
- `meta` — {study, title, quy_trinh, ngay_trich, nguon_du_lieu}
- `bia` — bìa Quyển 1 (Mẫu 2) và Quyển 2 (Mẫu 3): ten_de_tai, ma_so,
  chuyen_nganh, nghien_cuu_vien_chinh, co_quan_cong_tac, don_vi_chu_tri,
  thoi_gian_tu, thoi_gian_den, nam_nop.
- `don_mau4` — Đơn xin đánh giá đạo đức (Mẫu 4, Phụ lục 6): thông tin chủ
  nhiệm + đơn vị chủ trì + địa điểm/thời gian + cờ hồ sơ kèm theo
  (`ho_so_kem_theo`, khoá theo đúng quy trình đã chọn).
- `ly_lich_khoa_hoc` — list, mỗi phần tử là một người (chủ nhiệm +
  nghiên cứu viên chính), theo đúng 10 mục của Mẫu 5 (ô cá nhân luôn để
  `[CẦN BÁC SĨ ĐIỀN]` — máy không có và không được đoán ngày sinh, học vị…).
- `phu_luc_10` — Bảng kiểm quy trình RÚT GỌN (Mẫu 6): phan_mot (con người/
  động vật), phan_hai (tên NCYSH, nghiên cứu viên chính, người giám sát),
  phan_ba (A1–A10, B1–B11, mỗi mục {gia_tri: bool|null, giai_thich}),
  phan_bon (C1–C3 văn xuôi), phan_nam (C4–C7), thoi_gian (3 cặp từ–đến),
  nghien_cuu_vien_khac, phan_khai (kết luận NCV chính/người hướng dẫn/
  trưởng khoa/chủ tịch Hội đồng — để trống cho người có thẩm quyền).
- `phu_luc_11` — Phiếu quy trình ĐẦY ĐỦ (Mẫu 7): tinh_chat (8 cờ), ten_ncysh,
  nghien_cuu_vien (list), don_vi_chu_tri, nguoi_giao_dich, nhieu_co_quan
  (list), quy_che_dac_biet (12 cờ), nguon_tai_tro, thong_tin_sinh_vien,
  muc (dict khoá "1a".."13", mỗi mục là văn xuôi theo đúng số mục của
  Phụ lục 11 — xem `MUC_PHU_LUC_11` để biết tên đầy đủ từng mục), cam_ket
  (ngày + chữ ký NCV, để trống).
- `icf` — Bản thông tin + chấp thuận (Mẫu 8, Phụ lục 8), DÙNG KHI
  `gate_params.G2.icf_waiver_requested` != true: ten_nghien_cuu, nha_tai_tro,
  nghien_cuu_vien_chinh, don_vi_chu_tri, muc (dict "1".."6" theo 6 mục của
  Phụ lục 8).
- `mien_icf` — Đề nghị miễn thủ tục đồng thuận (sinh thay ICF khi
  `icf_waiver_requested` = true): can_cu, ten_de_tai, chu_nhiem, ngay,
  bon_dieu_kien (4 cờ + diễn giải), dam_bao_bao_mat (4 mục), co_do (2 cờ).
- `phieu_thu_thap` — nguồn trích phần phụ lục phiếu thu thập số liệu của
  đề cương nộp (đường dẫn + tiêu đề mục, không chép lại toàn văn ở đây).
- `viec_bac_si` — list việc CHỈ bác sĩ làm được (ký, thư giới thiệu, quyết
  định phân công, chuyển lệ phí, gửi email…), sinh ra ở bước `dung`.
- `_nguon` — dict "đường.dẫn.khoá" → "tên tệp#mục/khoá" cho MỌI trường đã
  trích tự động (truy nguyên); trường bác sĩ tự điền không có mục này.

Ranh giới
---------
Công cụ chỉ soạn NHÁP. Không tự ký, không tự xin thư giới thiệu/quyết
định phân công, không tự chuyển lệ phí, không tự gửi email cho thư ký
Hội đồng. Ô liên quan thông tin cá nhân (ngày sinh, học vị, địa chỉ nhà,
số điện thoại cá nhân…) LUÔN để `[CẦN BÁC SĨ ĐIỀN]` — máy không bịa.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import docx  # type: ignore
    from docx.shared import Pt  # type: ignore
except ImportError:  # pragma: no cover - môi trường thiếu python-docx
    docx = None  # type: ignore
    Pt = None  # type: ignore

CAN_BO_SUNG = "[CẦN BỔ SUNG]"
CAN_BAC_SI_DIEN = "[CẦN BÁC SĨ ĐIỀN]"
CAN_KY = "[CẦN KÝ]"
SCHEMA_VERSION = "1.0"

# 13 mục của Phụ lục 11 (Mẫu 7, quy trình đầy đủ) — tên đầy đủ để sinh văn bản
MUC_PHU_LUC_11 = {
    "1a": "Mô tả dự án",
    "1b": "Qui trình thực hiện",
    "1c": "Mục đích/giả thuyết/vấn đề nghiên cứu",
    "1d": "Vấn đề liên quan đến người dân tộc thiểu số",
    "1e": "Địa điểm nghiên cứu",
    "1f": "Nghiên cứu tại nơi làm việc của người tham gia",
    "2a": "Có các nguy cơ nào?",
    "2b": "So sánh mức độ rủi ro khi tham gia nghiên cứu với sinh hoạt hàng ngày",
    "2c": "Qui trình giảm thiểu rủi ro",
    "2d": "Cách xử lí khi xảy ra rủi ro",
    "2e": "Các nguy cơ về sức khoẻ và tính an toàn",
    "2f": "Các vấn đề về an toàn sinh học",
    "2g": "Thao tác gen",
    "3a": "Có những lợi ích gì?",
    "3b": "Ai được lợi?",
    "3c": "Đóng góp khoa học của nghiên cứu",
    "3d": "So sánh giữa nguy cơ và lợi ích của người tham gia",
    "4a": "Người tham gia dự kiến?",
    "4b": "Cách xác định, tiếp xúc, và tuyển mộ",
    "5": "Qui trình xin chấp thuận tình nguyện",
    "6a": "Thu thập dữ liệu trực tiếp?",
    "6b": "Tiếp cận thông tin cá nhân?",
    "6c": "Dữ liệu sẽ được ghi lại như thế nào?",
    "6d": "Thông tin cá nhân/nhạy cảm",
    "6e": "Bảo mật thông tin",
    "6f": "Bảo quản và lưu trữ",
    "6g": "Bảo vệ thông tin cá nhân",
    "7a": "Thời gian thử nghiệm của nghiên cứu",
    "7b": "Thời gian thu thập dữ liệu của nghiên cứu",
    "7c": "Tổng quỹ thời gian của nghiên cứu",
    "8a": "Nghiên cứu theo yêu cầu của (thay cho) người tài trợ/tổ chức thương mại?",
    "8b": "Sự phụ thuộc hoặc liên quan về tài chính",
    "8c": "Lợi ích tài chính trực tiếp/gián tiếp của nhóm nghiên cứu",
    "9": "Những cân nhắc đạo đức khác",
    "10": "Tổng quan, tổng quan tài liệu, kế hoạch và phương pháp",
}

MUC_PHU_LUC_8 = {
    "1": "Mục đích và tiến hành nghiên cứu",
    "2": "Các lợi ích và nguy cơ bất lợi",
    "3": "Bồi thường/điều trị khi có tổn thương liên quan đến nghiên cứu",
    "4": "Người liên hệ",
    "5": "Sự tự nguyện tham gia",
    "6": "Tính bảo mật",
}

A_LABELS = {
    "A1": "Thử nghiệm dược phẩm mới",
    "A2": "Thử nghiệm chế phẩm sinh học mới",
    "A3": "Thử nghiệm các phương pháp điều trị mới không dùng thuốc",
    "A4": "Thử nghiệm các thiết bị y tế mới",
    "A5": "Sử dụng phương pháp xạ trị và siêu âm",
    "A6": "Sử dụng các thủ thuật, phẫu thuật",
    "A7": "Bối cảnh giáo dục đã được chấp nhận rộng rãi",
    "A8": "Test giáo dục/quy trình điều tra/phỏng vấn/quan sát hành vi công cộng",
    "A9": "Số liệu, văn bản, hồ sơ, bệnh phẩm hay bệnh phẩm chẩn đoán sẵn có",
    "A10": "Chương trình dịch vụ hay phúc lợi công",
}
B_LABELS = {
    "B1": "Ghi/lưu trữ thông tin xác định danh tính cá nhân",
    "B2": "Sự tham gia của người không có năng lực hành vi",
    "B3": "Sự tham gia của vị thành niên",
    "B4": "Sự tham gia của người có quan hệ phụ thuộc vào nghiên cứu viên",
    "B5": "Các vấn đề nhạy cảm về văn hoá",
    "B6": "Gây đau đớn hoặc mệt mỏi tâm lý cao hơn mức thông thường",
    "B7": "Có chi trả khuyến khích",
    "B8": "Có thu thập thông tin nhạy cảm",
    "B9": "Có thu thập bí mật cá nhân",
    "B10": "Có thể liên quan đến trách nhiệm pháp lý",
    "B11": "Có sự tham gia có chọn lọc của người thiểu số",
}

# Tên tệp mẫu CHUẨN của bệnh viện, tương đối so với thư mục mẫu.
TEN_TEP_MAU = {
    "don_mau4": "4 - MH175.IRB.Phu_luc_6_Đơn xin đánh giá đạo đức_Nghiên cứu viên.docx",
    "ly_lich": "5 - Mẫu Lý lịch Khoa học.docx",
    "phu_luc_10": "6 - MH175.IRB.phu_luc_10-lựa chọn quy trình xem xét đạo đức_Quy trình rút gọn.docx",
    "phu_luc_10_huong_dan": (
        "6 - MH175.IRB.phu_luc_10-lựa chọn quy trình xem xét đạo đức"
        "_Quy trình rút gọn_[hướng dẫn].docx"
    ),
    "phu_luc_11": "7 - MH175.IRB.Phu_luc_11-lựa chọn quy trình xem xét đạo đức_Quy trình xem xét đầy đủ.docx",
    "phu_luc_11_huong_dan": (
        "7 - MH175.IRB.Phu_luc_11-lựa chọn quy trình xem xét đạo đức"
        "_Quy trình xem xét đầy đủ_[hướng dẫn].docx"
    ),
    "icf": "8 - MH175.IRB.phu_luc_8_Bản thông tin dành cho đối tượng nghiên cứu_ICF.docx",
    "icf_huong_dan": (
        "8 - MH175.IRB.phu_luc_8_Bản thông tin dành cho đối tượng nghiên cứu"
        "_ICF_hướng dẫn.docx"
    ),
    "bia_thuyet_minh": "2 - Mẫu bìa Thuyết minh đề cương.docx",
    "bia_ho_so": "3 - Mẫu bìa Hồ sơ đăng ký.docx",
    "huong_dan_quy_trinh": (
        "1 - Hồ sơ đăng ký đánh giá đạo đức trong nghiên cứu y sinh học BV Quân y 175.docx"
    ),
}

VAN_BAN_LE_PHI = "THÔNG TIN CHUYỂN KHOẢN.docx"


def tim_thu_muc_mau() -> Path | None:
    """Tìm thư mục chứa bộ mẫu bệnh viện (ngoài git).

    Ưu tiên biến môi trường ``EBM_MAU_HDD_BVQY175``; nếu không có, suy ra
    từ vị trí tệp này: mẫu nằm ở ``<cha-của-OneDrive>/Đề tài NCKH/
    Mau HDDD BV175/docx``. KHÔNG bịa đường dẫn khi không tìm thấy — trả None.
    """
    override = os.environ.get("EBM_MAU_HDD_BVQY175")
    if override:
        p = Path(override)
        if p.is_dir():
            return p
    # tools/ho_so_hdd_bvqy175.py -> .../medical-ebm-automation/tools
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if ancestor.name == "medical-ebm-automation":
            onedrive_cha = ancestor.parent.parent  # .../Claude AI -> .../OneDrive-Personal
            ung_vien = onedrive_cha / "Đề tài NCKH" / "Mau HDDD BV175" / "docx"
            if ung_vien.is_dir():
                return ung_vien
            # trường hợp cấu trúc "Claude AI" là gốc trực tiếp dưới OneDrive
            ung_vien2 = ancestor.parent / "Đề tài NCKH" / "Mau HDDD BV175" / "docx"
            if ung_vien2.is_dir():
                return ung_vien2
            break
    return None


def kiem_mau(args: argparse.Namespace) -> int:
    """Lệnh `mau`: dò bộ mẫu, báo tệp nào có/thiếu."""
    thu_muc = tim_thu_muc_mau()
    if thu_muc is None:
        print("KHÔNG TÌM THẤY thư mục bộ mẫu Hội đồng Đạo đức BVQY175.")
        print(
            "Đặt biến môi trường EBM_MAU_HDD_BVQY175 trỏ tới thư mục chứa các"
            " tệp .docx, hoặc để đúng cấu trúc <OneDrive>/Đề tài NCKH/"
            "Mau HDDD BV175/docx/."
        )
        return 2
    print(f"Thư mục mẫu: {thu_muc}")
    thieu = []
    for khoa, ten in TEN_TEP_MAU.items():
        duong_dan = thu_muc / ten
        dau = "✓" if duong_dan.is_file() else "✗ THIẾU"
        print(f"  [{dau}] {khoa}: {ten}")
        if not duong_dan.is_file():
            thieu.append(khoa)
    le_phi = thu_muc.parent / "goc" / VAN_BAN_LE_PHI
    print(f"  [{'✓' if le_phi.is_file() else '✗ THIẾU'}] (tham khảo, KHÔNG dùng số tài khoản) {VAN_BAN_LE_PHI}")
    if thieu:
        print(f"\nTHIẾU {len(thieu)} tệp mẫu — chưa thể chạy `dung` đầy đủ.")
        return 2
    print("\nĐủ bộ mẫu cần cho `dung`.")
    return 0


# ---------------------------------------------------------------------------
# Trích xuất tất định từ dữ liệu đề tài đã chốt
# ---------------------------------------------------------------------------


def _doc(exports_root: Path, study: str) -> Path:
    return exports_root / study


def _doc_hdd(exports_root: Path, study: str) -> Path:
    return _doc(exports_root, study) / "ho_so_hdd"


def _lay(d: dict, *path: str, default: Any = None) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _doc_md_mien_icf(noi_dung_md: str) -> dict | None:
    """Trích khối «TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF» từ G2_A3_ETHICS_PACKAGE_*.md."""
    m = re.search(
        r"## TÀI LIỆU 9\. ĐỀ NGHỊ MIỄN ICF.*?```\n(.*?)\n```",
        noi_dung_md,
        re.S,
    )
    if not m:
        return None
    than = m.group(1)
    ra: dict[str, Any] = {}
    chu_nhiem = re.search(r"Chủ nhiệm:\s*(.+)", than)
    if chu_nhiem:
        ra["chu_nhiem"] = chu_nhiem.group(1).strip() or CAN_BO_SUNG
    ngay = re.search(r"^Ngày:\s*(.+)$", than, re.M)
    if ngay:
        ra["ngay"] = ngay.group(1).strip()
    ma_hoa = re.search(r"Mã hóa:\s*(.+)", than)
    if ma_hoa:
        ra.setdefault("dam_bao_bao_mat", {})["ma_hoa"] = ma_hoa.group(1).strip()
    quyen = re.search(r"Quyền truy cập:\s*(.+)", than)
    if quyen:
        ra.setdefault("dam_bao_bao_mat", {})["quyen_truy_cap"] = quyen.group(1).strip()
    huy = re.search(r"Kế hoạch hủy:\s*(.+)", than)
    if huy:
        ra.setdefault("dam_bao_bao_mat", {})["ke_hoach_huy"] = huy.group(1).strip()
    loai_du_lieu = re.search(r"Loại dữ liệu:\s*(.+)", than)
    if loai_du_lieu:
        ra.setdefault("dam_bao_bao_mat", {})["loai_du_lieu"] = loai_du_lieu.group(1).strip()
    return ra


def _doc_md_dia_diem_thoi_gian(noi_dung_md: str) -> str | None:
    m = re.search(r"Nơi thực hiện:\s*(.+)", noi_dung_md)
    if m:
        return m.group(1).split(".")[0].strip()
    return None


def _doc_md_co_mau(noi_dung_md: str) -> str | None:
    m = re.search(r"Cỡ mẫu dự kiến:\s*(.+)", noi_dung_md)
    return m.group(1).strip() if m else None


def trich_du_kien(exports_root: Path, study: str) -> tuple[dict, list[str]]:
    """Trích tất định dữ kiện đã chốt của một đề tài.

    Trả về (dữ liệu, ghi chú). KHÔNG bịa — ô không trích được giữ nguyên
    placeholder [CẦN ...].
    """
    ghi_chu: list[str] = []
    thu_muc = _doc(exports_root, study)
    meta_path = thu_muc / "study_meta.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"Không thấy {meta_path} — đề tài chưa tồn tại hoặc sai mã.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    title = meta.get("title") or CAN_BO_SUNG
    gp = meta.get("gate_params", {})
    g2 = gp.get("G2", {}) or {}

    md_path = thu_muc / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    noi_dung_md = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    if not noi_dung_md:
        ghi_chu.append(f"Không thấy {md_path.name} — một số trường phải để [CẦN].")

    de_cuong_path = thu_muc / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    noi_dung_de_cuong = de_cuong_path.read_text(encoding="utf-8") if de_cuong_path.is_file() else ""

    icf_waiver = bool(g2.get("icf_waiver_requested"))
    dia_diem_thoi_gian = _doc_md_dia_diem_thoi_gian(noi_dung_md) or CAN_BO_SUNG
    co_mau = _doc_md_co_mau(noi_dung_md)

    nguon: dict[str, str] = {}

    def dat(path: str, value: Any, nguon_tag: str | None = None) -> Any:
        if nguon_tag:
            nguon[path] = nguon_tag
        return value

    bia = {
        "ten_de_tai": dat("bia.ten_de_tai", title, "study_meta.json#title"),
        "ma_so": CAN_BO_SUNG,
        "chuyen_nganh": CAN_BO_SUNG,
        "nghien_cuu_vien_chinh": CAN_BAC_SI_DIEN,
        "co_quan_cong_tac": CAN_BAC_SI_DIEN,
        "don_vi_chu_tri": CAN_BO_SUNG,
        "thoi_gian_tu": CAN_BO_SUNG,
        "thoi_gian_den": CAN_BO_SUNG,
        "nam_nop": str(datetime.now(timezone.utc).year),
    }

    don_mau4 = {
        "ho_ten_chu_nhiem": CAN_BAC_SI_DIEN,
        "chuc_vu": CAN_BAC_SI_DIEN,
        "don_vi": CAN_BAC_SI_DIEN,
        "dia_chi": CAN_BAC_SI_DIEN,
        "dien_thoai": CAN_BAC_SI_DIEN,
        "fax": "",
        "email": CAN_BAC_SI_DIEN,
        "ten_de_tai": dat("don_mau4.ten_de_tai", title, "study_meta.json#title"),
        "ten_don_vi_chu_tri": CAN_BO_SUNG,
        "dia_chi_don_vi_chu_tri": CAN_BO_SUNG,
        "dien_thoai_don_vi": "",
        "fax_don_vi": "",
        "email_don_vi": "",
        "dia_diem_thoi_gian": dat(
            "don_mau4.dia_diem_thoi_gian", dia_diem_thoi_gian,
            f"{md_path.name}#Nơi thực hiện" if dia_diem_thoi_gian != CAN_BO_SUNG else None,
        ),
        "ho_so_kem_theo": {
            "bang_kiem_rut_gon": None,
            "phieu_day_du": None,
            "de_cuong": True,
            "bang_cau_hoi_phu_luc": None,
            "phieu_chap_thuan": not icf_waiver,
            "trang_thong_tin": None,
            "ly_lich_khoa_hoc": True,
            "tai_lieu_khac": "",
        },
    }

    ly_lich_khoa_hoc = [
        {
            "vai_tro": "Chủ nhiệm đề tài",
            "ho_ten": CAN_BAC_SI_DIEN,
            "ngay_thang_nam_sinh": CAN_BAC_SI_DIEN,
            "nam_nu": CAN_BAC_SI_DIEN,
            "dia_chi_gui_thu": CAN_BAC_SI_DIEN,
            "mobile": CAN_BAC_SI_DIEN,
            "email": CAN_BAC_SI_DIEN,
            "chuc_vu": CAN_BAC_SI_DIEN,
            "co_quan_noi_lam_viec": CAN_BAC_SI_DIEN,
            "ten_lanh_dao_co_quan": CAN_BAC_SI_DIEN,
            "dien_thoai_lanh_dao_co_quan": CAN_BAC_SI_DIEN,
            "dia_chi_co_quan": CAN_BAC_SI_DIEN,
            "trinh_do": {
                "hoc_vi": CAN_BAC_SI_DIEN,
                "nam_nhan_bang": CAN_BAC_SI_DIEN,
                "chuyen_nganh_dao_tao": CAN_BAC_SI_DIEN,
                "hoc_ham": CAN_BAC_SI_DIEN,
            },
            "kinh_nghiem_nghien_cuu": [],
        }
    ]

    design = gp.get("G1", {}).get("design") if isinstance(gp.get("G1"), dict) else None
    recruitment_mode = g2.get("recruitment_mode")
    la_hoi_cuu_du_lieu_san_co = recruitment_mode == "RETROSPECTIVE_SECONDARY_DATA"
    la_tien_cuu_moi = recruitment_mode == "PROSPECTIVE_NEW_PARTICIPANTS"

    def co_khong(gia_tri: bool | None) -> dict:
        return {"gia_tri": gia_tri, "giai_thich": "" if gia_tri is not None else CAN_BAC_SI_DIEN}

    phan_ba_a = {k: co_khong(None) for k in A_LABELS}
    if la_hoi_cuu_du_lieu_san_co:
        phan_ba_a["A9"] = co_khong(True)
        phan_ba_a["A9"]["giai_thich"] = (
            "Hồi cứu dữ liệu sẵn có trên HIS (eHospital), không can thiệp — "
            f"nguồn: {meta_path.name}#gate_params.G2.recruitment_mode"
        )
        nguon["phu_luc_10.phan_ba.A.A9"] = "study_meta.json#gate_params.G2.recruitment_mode"
        for k in ("A1", "A2", "A3", "A4", "A5", "A6"):
            phan_ba_a[k] = co_khong(False)
    phan_ba_b = {k: co_khong(None) for k in B_LABELS}
    if la_hoi_cuu_du_lieu_san_co:
        phan_ba_b["B1"] = co_khong(True)
        phan_ba_b["B1"]["giai_thich"] = (
            "Phiếu trích chỉ mang mã nghiên cứu; bảng nối mã lưu riêng, huỷ sau khi"
            f" khoá dữ liệu — nguồn: {md_path.name}#TÀI LIỆU 6 (DMP)"
        )
        nguon["phu_luc_10.phan_ba.B.B1"] = f"{md_path.name}#TÀI LIỆU 6. KẾ HOẠCH QUẢN LÝ DỮ LIỆU"

    phu_luc_10 = {
        "phan_mot": {
            "doi_tuong_con_nguoi": True,
            "doi_tuong_dong_vat": False,
        },
        "phan_hai": {
            "ten_ncysh": dat("phu_luc_10.phan_hai.ten_ncysh", title, "study_meta.json#title"),
            "nghien_cuu_vien_chinh": {
                "khoa_bo_mon": CAN_BAC_SI_DIEN,
                "truong_don_vi": CAN_BAC_SI_DIEN,
                "dien_thoai": CAN_BAC_SI_DIEN,
                "thu_dien_tu": CAN_BAC_SI_DIEN,
                "dia_chi_lien_he": CAN_BAC_SI_DIEN,
            },
            "nguoi_giam_sat": {
                "noi_lam_viec": "",
                "dien_thoai": "",
                "thu_dien_tu": "",
            },
        },
        "phan_ba": {"A": phan_ba_a, "B": phan_ba_b},
        "phan_bon": {
            "C1_huy_dong_chon_nguoi_tham_gia": CAN_BO_SUNG,
            "C2_thu_thap_so_lieu": CAN_BO_SUNG,
            "C3_xin_chap_thuan_tu_nguyen": (
                "Xin miễn thủ tục đồng thuận (xem mien_icf)" if icf_waiver else CAN_BO_SUNG
            ),
        },
        "phan_nam": {
            "C4_thu_nghiem_thuoc_can_thiep": co_khong(False if la_hoi_cuu_du_lieu_san_co else None),
            "C5_nguy_co_toi_thieu_de_quan_ly": co_khong(True if la_hoi_cuu_du_lieu_san_co else None),
            "C6_nhieu_co_quan": co_khong(None),
            "C7_gia_han_tai_xin_phep": co_khong(False),
        },
        "thoi_gian": {
            "thu_nghiem": {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG},
            "thu_thap": {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG},
            "toan_bo": {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG},
        },
        "nghien_cuu_vien_khac": "",
        "phan_khai": {
            "ket_luan_nghien_cuu_vien_chinh": None,
            "ket_luan_nguoi_huong_dan": None,
            "ket_luan_truong_khoa": None,
            "ket_luan_chu_tich_hoi_dong": None,
        },
    }

    muc_11: dict[str, str] = {k: CAN_BO_SUNG for k in MUC_PHU_LUC_11}
    muc_11["10"] = (
        "Xem đề cương đầy đủ đã nộp (tệp DE_CUONG_NOP_HOI_DONG_"
        f"{study}.md/.docx) — đính kèm, không chép lại ở đây (giới hạn 6 trang)."
    )
    nguon["phu_luc_11.muc.10"] = f"DE_CUONG_NOP_HOI_DONG_{study}.md"

    phu_luc_11 = {
        "tinh_chat": {
            "duoc_tai_tro": False,
            "hoc_vien_sau_dai_hoc": None,
            "sinh_vien_dai_hoc": None,
            "xin_phep_tap_the": None,
            "don_xin_tai_cap_phep": False,
            "so_giay_phep_cu": "",
            "khong_thuoc_nhom_nao_tren": None,
        },
        "ten_ncysh": dat("phu_luc_11.ten_ncysh", title, "study_meta.json#title"),
        "nghien_cuu_vien": [
            {"ho_ten": CAN_BAC_SI_DIEN, "chuc_danh": CAN_BAC_SI_DIEN, "chuc_vu_noi_cong_tac": CAN_BAC_SI_DIEN}
        ],
        "don_vi_chu_tri": CAN_BO_SUNG,
        "nguoi_giao_dich": {
            "ho_ten_chuc_danh": "",
            "dia_chi_giao_dich": "",
            "dien_thoai_cq": "",
            "dien_thoai_nr": "",
            "di_dong": "",
            "thu_dien_tu": "",
        },
        "nhieu_co_quan": [],
        "quy_che_dac_biet": {k: None for k in (
            "tre_em_vi_thanh_nien",
            "ton_thuong_than_kinh_thieu_nang_tri_tue",
            "can_cham_soc_y_te_thuong_xuyen",
            "quan_he_le_thuoc_khong_binh_dang",
            "tap_the_nhom_nguoi",
            "dan_toc_thieu_so",
            "phong_xa_chat_ion_hoa",
            "cong_nghe_sinh_san_co_tro_giup",
            "thu_nghiem_lam_sang",
            "phac_do_dieu_tri_thu_thuat_moi",
            "nghien_cuu_dich_te_hoc",
            "mau_mo_chat_dich_nguoi",
            "gien_nguoi",
        )},
        "nguon_tai_tro": CAN_BO_SUNG,
        "thong_tin_sinh_vien": "",
        "muc": muc_11,
        "cam_ket": [],
    }
    if la_hoi_cuu_du_lieu_san_co:
        phu_luc_11["quy_che_dac_biet"]["mau_mo_chat_dich_nguoi"] = False

    if icf_waiver:
        mien_icf_md = _doc_md_mien_icf(noi_dung_md) or {}
        mien_icf = {
            "can_cu": "TT43/2024/TT-BYT Điều 15 · Helsinki (WMA, bản sửa 2024) §29",
            "ten_de_tai": dat("mien_icf.ten_de_tai", title, "study_meta.json#title"),
            "chu_nhiem": mien_icf_md.get("chu_nhiem", CAN_BAC_SI_DIEN),
            "ngay": mien_icf_md.get("ngay", CAN_BO_SUNG),
            "bon_dieu_kien": {
                "du_lieu_co_san_gia_danh_hoa": True,
                "khong_can_thiep_bo_sung": True,
                "rui_ro_khong_vuot_toi_thieu": True,
                "khong_kha_thi_icf_day_du": True,
            },
            "dam_bao_bao_mat": mien_icf_md.get("dam_bao_bao_mat", {
                "loai_du_lieu": CAN_BO_SUNG,
                "ma_hoa": CAN_BO_SUNG,
                "quyen_truy_cap": CAN_BO_SUNG,
                "ke_hoach_huy": CAN_BO_SUNG,
            }),
            "co_do": {
                "co_du_lieu_ca_nhan_nhan_dang_duoc": False,
                "co_tiep_xuc_nguoi_tham_gia": False,
            },
        }
        if mien_icf_md:
            nguon["mien_icf"] = f"{md_path.name}#TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF"
        icf = None
    else:
        mien_icf = None
        icf = {
            "ten_nghien_cuu": dat("icf.ten_nghien_cuu", title, "study_meta.json#title"),
            "nha_tai_tro": CAN_BO_SUNG,
            "nghien_cuu_vien_chinh": CAN_BAC_SI_DIEN,
            "don_vi_chu_tri": CAN_BO_SUNG,
            "muc": {k: CAN_BO_SUNG for k in MUC_PHU_LUC_8},
        }

    du_lieu: dict[str, Any] = {
        "phien_ban_schema": SCHEMA_VERSION,
        "meta": {
            "study": study,
            "title": title,
            "quy_trinh": "rut_gon" if la_hoi_cuu_du_lieu_san_co else "day_du" if la_tien_cuu_moi else CAN_BO_SUNG,
            "ngay_trich": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "co_mau_du_kien": co_mau or CAN_BO_SUNG,
        },
        "bia": bia,
        "don_mau4": don_mau4,
        "ly_lich_khoa_hoc": ly_lich_khoa_hoc,
        "phu_luc_10": phu_luc_10,
        "phu_luc_11": phu_luc_11,
        "icf": icf,
        "mien_icf": mien_icf,
        "phieu_thu_thap": {
            "nguon": f"DE_CUONG_NOP_HOI_DONG_{study}.md#phụ lục phiếu thu thập" if noi_dung_de_cuong else CAN_BO_SUNG,
        },
        "viec_bac_si": [],
        "_nguon": nguon,
    }
    if not design:
        ghi_chu.append("Chưa thấy gate_params.G1.design trong study_meta.json — một số suy luận A/B để trống.")
    return du_lieu, ghi_chu


def _hop_nhat_bo_sung(cu: dict, moi: dict) -> dict:
    """Hợp nhất đệ quy: giữ giá trị CŨ, chỉ thêm khoá MỚI còn thiếu."""
    ra = copy.deepcopy(cu)
    for k, v in moi.items():
        if k not in ra:
            ra[k] = v
        elif isinstance(v, dict) and isinstance(ra[k], dict):
            ra[k] = _hop_nhat_bo_sung(ra[k], v)
        # list và scalar: giữ nguyên bản cũ, không ghi đè
    return ra


def lenh_trich(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    try:
        moi, ghi_chu = trich_du_kien(exports_root, args.study)
    except FileNotFoundError as exc:
        print(f"LỖI: {exc}")
        return 2
    for g in ghi_chu:
        print(f"[chú ý] {g}")

    duong_dan_json = _doc_hdd(exports_root, args.study) / "HO_SO_HDD_BVQY175.json"
    if duong_dan_json.is_file():
        cu = json.loads(duong_dan_json.read_text(encoding="utf-8"))
        if args.ghi_de:
            ket_qua = moi
            print("Ghi ĐÈ toàn bộ (do --ghi-de).")
        else:
            ket_qua = _hop_nhat_bo_sung(cu, moi)
            print("Đã có JSON — chỉ bổ sung khoá còn thiếu, giữ nguyên giá trị đã sửa.")
    else:
        ket_qua = moi

    so_can = _dem_can(ket_qua)
    print(f"Số ô còn [CẦN...]: {so_can}")

    if not args.ghi:
        print("(chạy khô — thêm --ghi để lưu tệp)")
        print(json.dumps(ket_qua, ensure_ascii=False, indent=1)[:4000])
        return 0

    duong_dan_json.parent.mkdir(parents=True, exist_ok=True)
    if duong_dan_json.is_file() and args.ghi_de:
        sao_luu = duong_dan_json.with_suffix(
            f".bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        )
        shutil.copy2(duong_dan_json, sao_luu)
        print(f"Đã sao lưu bản cũ: {sao_luu}")
    duong_dan_json.write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Đã ghi: {duong_dan_json}")
    return 0


def _dem_can(obj: Any) -> int:
    dem = 0
    if isinstance(obj, str):
        if "[CẦN" in obj:
            dem += 1
    elif isinstance(obj, dict):
        for v in obj.values():
            dem += _dem_can(v)
    elif isinstance(obj, list):
        for v in obj:
            dem += _dem_can(v)
    return dem


# ---------------------------------------------------------------------------
# Điền mẫu Word
# ---------------------------------------------------------------------------


def _can_docx() -> None:
    if docx is None:
        raise RuntimeError(
            "Thiếu python-docx — cài bằng: pip install python-docx (hoặc dùng venv ~/.ebm-venv)."
        )


def _dat_times_new_roman(doc) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    if Pt is not None:
        style.font.size = Pt(13)


def _dien_cho_trong(text: str, nhan: str, gia_tri: str) -> str:
    """Thay chuỗi `nhan` (vd 'Họ và tên Chủ nhiệm đề tài (dự án):') bằng
    `nhan gia_tri`, chỉ khi `nhan` xuất hiện và chưa có nội dung sau nó."""
    if nhan in text:
        return text.replace(nhan, f"{nhan} {gia_tri}", 1)
    return text


def _gan_checkbox(paragraph, danh_sach_bool: list[bool | None]) -> None:
    """Thay MỌI 'FORMCHECKBOX' trong đoạn văn bằng ☒/☐ theo thứ tự.

    `danh_sach_bool`: True -> ☒, False/None -> ☐ (None nghĩa là chưa quyết
    định — vẫn vẽ ô trống, KHÔNG được tự đánh dấu khi chưa chắc).
    """
    idx = 0
    for run in paragraph.runs:
        while "FORMCHECKBOX" in run.text and idx < len(danh_sach_bool):
            dau = "☒" if danh_sach_bool[idx] else "☐"
            run.text = run.text.replace("FORMCHECKBOX", dau, 1)
            idx += 1


def _danh_dau_tat_ca_formcheckbox(doc, gia_tri: bool | None = None) -> int:
    """Quét toàn văn bản, thay FORMCHECKBOX còn lại bằng ☐ (mặc định trống).

    Dùng cho các mẫu có nhiều checkbox không map 1-1 theo paragraph index
    ổn định — an toàn hơn là để trống (☐) thay vì đoán đánh dấu (☒).
    """
    so_thay = 0
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if "FORMCHECKBOX" in run.text:
                dau = "☒" if gia_tri else "☐"
                run.text = run.text.replace("FORMCHECKBOX", dau)
                so_thay += 1
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if "FORMCHECKBOX" in run.text:
                            run.text = run.text.replace("FORMCHECKBOX", "☐")
                            so_thay += 1
    return so_thay


def _them_doan(doc, text: str) -> None:
    doc.add_paragraph(text)


def dung_don_mau4(mau_dir: Path, ra_dir: Path, d: dict, quy_trinh: str) -> Path:
    _can_docx()
    src = mau_dir / TEN_TEP_MAU["don_mau4"]
    doc = docx.Document(str(src))
    don = d["don_mau4"]
    thay_the = {
        "Họ và tên Chủ nhiệm đề tài (dự án):": don["ho_ten_chu_nhiem"],
        "Đơn vị:": don["don_vi"],
        "Tên đề tài (dự án) xin đánh giá đạo đức trong nghiên cứu:": don["ten_de_tai"],
        "Tên đơn vị chủ trì đề tài (dự án):": don["ten_don_vi_chu_tri"],
        "Địa điểm, thời gian triển khai nghiên cứu:": don["dia_diem_thoi_gian"],
    }
    for p in doc.paragraphs:
        for nhan, gia_tri in thay_the.items():
            if p.text.strip() == nhan:
                for run in list(p.runs):
                    run.text = ""
                p.runs[0].text = f"{nhan} {gia_tri}" if p.runs else f"{nhan} {gia_tri}"
                if not p.runs:
                    p.add_run(f"{nhan} {gia_tri}")

    ho_so = don["ho_so_kem_theo"]
    co_rut_gon = quy_trinh in ("rut_gon", "ca_hai")
    co_day_du = quy_trinh in ("day_du", "ca_hai")
    gia_tri_checkbox = [
        co_rut_gon,  # Bảng kiểm lựa chọn qui trình (phụ lục 10)
        co_day_du,  # Phiếu thông tin xem xét quy trình đầy đủ (phụ lục 11)
        bool(ho_so.get("de_cuong", True)),
        bool(ho_so.get("bang_cau_hoi_phu_luc")),
        bool(ho_so.get("phieu_chap_thuan")),
        bool(ho_so.get("trang_thong_tin")),
        bool(ho_so.get("ly_lich_khoa_hoc", True)),
        bool(ho_so.get("tai_lieu_khac")),
    ]
    idx = 0
    for p in doc.paragraphs:
        if "FORMCHECKBOX" in p.text and idx < len(gia_tri_checkbox):
            _gan_checkbox(p, [gia_tri_checkbox[idx]])
            idx += 1
    _danh_dau_tat_ca_formcheckbox(doc)  # phần còn lại (nếu lệch số lượng) để trống

    ra_dir.mkdir(parents=True, exist_ok=True)
    out = ra_dir / f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{d['meta']['study']}.docx"
    doc.save(str(out))
    return out


def dung_ly_lich(mau_dir: Path, ra_dir: Path, d: dict) -> list[Path]:
    _can_docx()
    src = mau_dir / TEN_TEP_MAU["ly_lich"]
    ra: list[Path] = []
    ra_dir.mkdir(parents=True, exist_ok=True)
    for i, nguoi in enumerate(d["ly_lich_khoa_hoc"], start=1):
        doc = docx.Document(str(src))
        thay_the = {
            "1. Họ và tên: ": nguoi["ho_ten"],
            "2. Ngày tháng năm sinh: ": nguoi["ngay_thang_nam_sinh"],
            "3. Nam, nữ: ": nguoi["nam_nu"],
            "4. Địa chỉ gửi thư: ": nguoi["dia_chi_gui_thu"],
            "5. Mobile: ": nguoi["mobile"],
            "6. E-mail: ": nguoi["email"],
            "7. Chức vụ: ": nguoi["chuc_vu"],
            "8. Cơ quan - nơi  làm việc: ": nguoi["co_quan_noi_lam_viec"],
        }
        for p in doc.paragraphs:
            for nhan, gia_tri in thay_the.items():
                if p.text.strip() == nhan.strip():
                    for run in list(p.runs):
                        run.text = ""
                    if p.runs:
                        p.runs[0].text = f"{nhan}{gia_tri}"
                    else:
                        p.add_run(f"{nhan}{gia_tri}")
        out = ra_dir / f"MAU5_LY_LICH_KHOA_HOC_{d['meta']['study']}_{i:02d}.docx"
        doc.save(str(out))
        ra.append(out)
    return ra


def dung_mien_icf(ra_dir: Path, d: dict) -> Path:
    """Sinh văn bản Đề nghị miễn thủ tục đồng thuận (không có mẫu riêng
    của bệnh viện cho văn bản này — tự soạn, theo đúng khung Tài liệu 9
    của A3 ETHICS PACKAGE)."""
    _can_docx()
    mi = d["mien_icf"]
    doc = docx.Document()
    _dat_times_new_roman(doc)
    doc.add_heading("YÊU CẦU MIỄN THỦ TỤC ĐỒNG THUẬN (ICF Waiver Request)", level=1)
    _them_doan(doc, f"Căn cứ: {mi['can_cu']}")
    _them_doan(doc, f"Tên đề tài: {mi['ten_de_tai']}")
    _them_doan(doc, f"Chủ nhiệm: {mi['chu_nhiem']}")
    _them_doan(doc, f"Ngày: {mi['ngay']}")
    doc.add_heading("CƠ SỞ XIN MIỄN (phải thỏa CẢ 4 điều kiện)", level=2)
    dk = mi["bon_dieu_kien"]
    nhan_dk = {
        "du_lieu_co_san_gia_danh_hoa": "Dùng hồ sơ có sẵn, giả danh hoá/ẩn danh",
        "khong_can_thiep_bo_sung": "Không có can thiệp/thủ thuật bổ sung lên người tham gia",
        "rui_ro_khong_vuot_toi_thieu": "Rủi ro không vượt nguy cơ tối thiểu",
        "khong_kha_thi_icf_day_du": "Không khả thi yêu cầu ICF đầy đủ",
    }
    for khoa, nhan in nhan_dk.items():
        dau = "☑" if dk.get(khoa) else "☐"
        _them_doan(doc, f"{dau} {nhan}")
    doc.add_heading("ĐẢM BẢO BẢO MẬT", level=2)
    for khoa, nhan in {
        "loai_du_lieu": "Loại dữ liệu",
        "ma_hoa": "Mã hóa",
        "quyen_truy_cap": "Quyền truy cập",
        "ke_hoach_huy": "Kế hoạch hủy",
    }.items():
        _them_doan(doc, f"{nhan}: {mi['dam_bao_bao_mat'].get(khoa, CAN_BO_SUNG)}")
    doc.add_heading("CỜ ĐỎ (bất kỳ → PHẢI lấy ICF đầy đủ)", level=2)
    cd = mi["co_do"]
    dau_nhan_dang = "☒" if cd.get("co_du_lieu_ca_nhan_nhan_dang_duoc") else "☐"
    _them_doan(doc, f"{dau_nhan_dang} Có dữ liệu cá nhân nhận dạng được")
    dau_tiep_xuc = "☒" if cd.get("co_tiep_xuc_nguoi_tham_gia") else "☐"
    _them_doan(doc, f"{dau_tiep_xuc} Có tiếp xúc người tham gia")
    _them_doan(doc, "")
    _them_doan(doc, f"Chữ ký chủ nhiệm: {CAN_KY} | Ngày: ___/___/20…")
    _them_doan(doc, '"DRAFT — Cần Hội đồng Đạo đức phê duyệt."')
    ra_dir.mkdir(parents=True, exist_ok=True)
    out = ra_dir / f"MIEN_ICF_{d['meta']['study']}.docx"
    doc.save(str(out))
    return out


def dung_phieu_thu_thap(exports_root: Path, ra_dir: Path, d: dict) -> Path | None:
    """Trích phần phụ lục phiếu thu thập số liệu từ đề cương nộp ra Word
    riêng (yêu cầu của Quyển 2, mục 7)."""
    study = d["meta"]["study"]
    de_cuong_md = exports_root / study / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    if not de_cuong_md.is_file():
        return None
    noi_dung = de_cuong_md.read_text(encoding="utf-8")
    m = re.search(r"(## .*(?:[Pp]hụ lục|[Pp]hiếu thu thập).*?)(?=\n## |\Z)", noi_dung, re.S)
    if not m:
        return None
    _can_docx()
    doc = docx.Document()
    _dat_times_new_roman(doc)
    doc.add_heading(f"PHỤ LỤC PHIẾU THU THẬP SỐ LIỆU — {d['meta']['title']}", level=1)
    for dong in m.group(1).splitlines():
        if dong.strip():
            _them_doan(doc, dong)
    ra_dir.mkdir(parents=True, exist_ok=True)
    out = ra_dir / f"PHIEU_THU_THAP_SO_LIEU_{study}.docx"
    doc.save(str(out))
    return out


def sinh_danh_muc(ra_dir: Path, d: dict, quy_trinh: str, tep_da_sinh: list[str]) -> Path:
    study = d["meta"]["study"]
    icf_waiver = d["icf"] is None
    dong: list[str] = []
    dong.append(f"# Danh mục hồ sơ Hội đồng Đạo đức BVQY175 — {study}")
    dong.append("")
    dong.append(f"Đề tài: {d['meta']['title']}")
    dong.append(f"Quy trình: {quy_trinh}")
    dong.append("")
    dong.append("## Quyển 1 — Thuyết minh đề cương (bìa Mẫu 2)")
    dong.append("- [NGOÀI PHẠM VI CÔNG CỤ NÀY] Ghép bìa Mẫu 2 với bản Word đề cương nộp hiện có"
                 f" (`DE_CUONG_NOP_HOI_DONG_{study}.docx`).")
    dong.append("")
    dong.append("## Quyển 2 — Hồ sơ đăng ký (bìa Mẫu 3), theo đúng 8 mục")

    def _da_soan(khoa: str) -> str:
        return "đã soạn" if any(khoa in t for t in tep_da_sinh) else "CHƯA soạn"

    dong.append(f"1. Đơn xin đánh giá đạo đức (Mẫu 4) — {_da_soan('MAU4')}")
    dong.append("2. Thư giới thiệu của đơn vị chủ trì — **[CẦN BÁC SĨ XIN, máy không soạn]**")
    dong.append("3. Bản sao quyết định phân công người hướng dẫn — **[CẦN BÁC SĨ XIN, máy không soạn]**")
    dong.append(
        f"4. Lý lịch khoa học (Mẫu 5) — {_da_soan('MAU5')}"
        " (ô cá nhân để trống cho bác sĩ điền và ký)"
    )
    if quy_trinh in ("rut_gon", "ca_hai"):
        dong.append(f"5a. Bảng kiểm quy trình rút gọn (Mẫu 6, Phụ lục 10) — {_da_soan('PHU_LUC_10')}")
    if quy_trinh in ("day_du", "ca_hai"):
        dong.append(f"5b. Phiếu quy trình đầy đủ (Mẫu 7, Phụ lục 11) — {_da_soan('PHU_LUC_11')}")
    if icf_waiver:
        dong.append(f"6. Đề nghị miễn thủ tục đồng thuận (thay ICF) — {_da_soan('MIEN_ICF')}")
    else:
        dong.append(
            "6. Bản thông tin + chấp thuận tham gia (Mẫu 8, ICF) — "
            "**[CẦN TỰ SOẠN, công cụ chưa điền mẫu này — xem docs]**"
        )
    da_trich_phieu = any("PHIEU_THU_THAP" in t for t in tep_da_sinh)
    trang_thai_phieu = "đã trích" if da_trich_phieu else "CHƯA trích được, kiểm lại đề cương nộp"
    dong.append(f"7. Bệnh án/phiếu thu thập số liệu và phụ lục của đề cương — {trang_thai_phieu}")
    dong.append(
        "8. Giấy chấp thuận đạo đức nơi khác (nếu có) — áp dụng khi nghiên cứu nhiều"
        " cơ quan; để trống nếu không có"
    )
    dong.append("")
    dong.append("## Việc CHỈ bác sĩ làm được")
    dong.append("- Điền toàn bộ ô cá nhân (ngày sinh, học vị, địa chỉ, số điện thoại…) trong Mẫu 4, 5, 6/7.")
    dong.append(
        "- Ký tất cả mẫu cần chữ ký (Đơn Mẫu 4, Lý lịch khoa học, Bảng kiểm/Phiếu"
        " quy trình, Đề nghị miễn ICF nếu có)."
    )
    dong.append("- Xin thư giới thiệu của đơn vị chủ trì và bản sao quyết định phân công người hướng dẫn (nếu có).")
    dong.append("- Đóng dấu xác nhận cơ quan (trừ khi là CB/VC/NV/HV BVQY175 được miễn xác nhận).")
    if quy_trinh == "rut_gon":
        so_bo = "03 bộ (quy trình rút gọn)"
    elif quy_trinh == "day_du":
        so_bo = "07 bộ (quy trình đầy đủ)"
    else:
        so_bo = "03 bộ (rút gọn) + 07 bộ (đầy đủ) nếu nộp cả hai"
    dong.append(f"- Chuẩn bị bản cứng: {so_bo}.")
    dong.append(
        "- Gửi bản mềm (PDF/scan: 1 tệp thuyết minh đề cương + 1 tệp hồ sơ đăng ký) tới"
        " thuky.hddd.bvqy175@gmail.com TRƯỚC khi nộp bản cứng — máy không tự gửi email."
    )
    dong.append(
        "- Chuyển lệ phí 2.000.000 đ/hồ sơ theo thông tin tài khoản ở Phụ lục 2 của hướng dẫn gốc"
        " (KHÔNG lưu số tài khoản trong repo git) — máy không tự chuyển khoản."
    )
    dong.append("- Theo dõi 5 mốc thời gian làm việc của quy trình (5/2/2/10/2 ngày làm việc) sau khi nộp.")
    dong.append("")
    dong.append(
        f"Số ô còn `[CẦN...]` trong `HO_SO_HDD_BVQY175.json`: {_dem_can(d)}"
        " — chạy `kiem` để xem chi tiết theo nhóm."
    )
    ra = ra_dir / f"DANH_MUC_HO_SO_HDD_{study}.md"
    ra.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return ra


def lenh_dung(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    quy_trinh = args.quy_trinh
    thu_muc_hdd = _doc_hdd(exports_root, args.study)
    duong_dan_json = thu_muc_hdd / "HO_SO_HDD_BVQY175.json"
    if not duong_dan_json.is_file():
        print(f"LỖI: chưa có {duong_dan_json} — chạy `trich --study {args.study} --ghi` trước.")
        return 2
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))

    mau_dir = tim_thu_muc_mau()
    if mau_dir is None:
        print("LỖI: không tìm thấy bộ mẫu bệnh viện — chạy `mau` để kiểm.")
        return 2
    if docx is None:
        print("LỖI: thiếu python-docx. pip install python-docx")
        return 2

    if not args.ghi:
        print("(chạy khô — thêm --ghi để sinh tệp Word thật)")
        print(f"Sẽ dựng hồ sơ cho {args.study}, quy trình={quy_trinh}, vào {thu_muc_hdd}")
        print(f"Số ô còn [CẦN...]: {_dem_can(d)}")
        return 0

    tep_da_sinh: list[str] = []
    out1 = dung_don_mau4(mau_dir, thu_muc_hdd, d, quy_trinh)
    tep_da_sinh.append(out1.name)
    for p in dung_ly_lich(mau_dir, thu_muc_hdd, d):
        tep_da_sinh.append(p.name)
    if d.get("mien_icf"):
        out3 = dung_mien_icf(thu_muc_hdd, d)
        tep_da_sinh.append(out3.name)
    out4 = dung_phieu_thu_thap(exports_root, thu_muc_hdd, d)
    if out4:
        tep_da_sinh.append(out4.name)
    danh_muc = sinh_danh_muc(thu_muc_hdd, d, quy_trinh, tep_da_sinh)
    print(f"Đã sinh {len(tep_da_sinh)} tệp Word + danh mục: {danh_muc}")
    for t in tep_da_sinh:
        print(f"  - {t}")
    return 0


# ---------------------------------------------------------------------------
# Kiểm
# ---------------------------------------------------------------------------


def lenh_kiem(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    study = args.study
    thu_muc_hdd = _doc_hdd(exports_root, study)
    duong_dan_json = thu_muc_hdd / "HO_SO_HDD_BVQY175.json"
    if not duong_dan_json.is_file():
        print(f"KHÔNG ĐO ĐƯỢC: chưa có {duong_dan_json}.")
        return 2
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))

    van_de: list[str] = []
    khoa_bat_buoc = ["phien_ban_schema", "meta", "bia", "don_mau4", "ly_lich_khoa_hoc", "phu_luc_10", "phu_luc_11"]
    for k in khoa_bat_buoc:
        if k not in d:
            van_de.append(f"THIẾU khoá bắt buộc: {k}")

    if (d.get("icf") is None) == (d.get("mien_icf") is None):
        van_de.append("LOGIC: phải có ĐÚNG MỘT trong hai, icf HOẶC mien_icf (loại trừ nhau).")

    meta_path = _doc(exports_root, study) / "study_meta.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title_thuc = meta.get("title")
        if title_thuc and d.get("bia", {}).get("ten_de_tai") not in (title_thuc, None):
            if d["bia"]["ten_de_tai"] != title_thuc:
                van_de.append(
                    f"LỆCH TÊN ĐỀ TÀI: JSON='{d['bia']['ten_de_tai']}' khác study_meta.title='{title_thuc}'"
                )
    else:
        van_de.append(f"KHÔNG ĐO ĐƯỢC: thiếu {meta_path}")

    gp = (meta.get("gate_params") if meta_path.is_file() else {}) or {}
    g2 = gp.get("G2", {}) or {}
    if g2.get("icf_waiver_requested") and d.get("icf") is not None:
        van_de.append(
            "LOGIC: gate_params.G2.icf_waiver_requested=true nhưng JSON vẫn có"
            " khối icf (phải dùng mien_icf)."
        )
    if g2.get("icf_waiver_requested") is False and d.get("mien_icf") is not None:
        van_de.append(
            "LOGIC: gate_params.G2.icf_waiver_requested=false nhưng JSON lại có mien_icf."
        )

    a9 = _lay(d, "phu_luc_10", "phan_ba", "A", "A9", "gia_tri")
    if g2.get("recruitment_mode") == "RETROSPECTIVE_SECONDARY_DATA" and a9 is False:
        van_de.append("LOGIC: recruitment_mode hồi cứu dữ liệu sẵn có nhưng Phụ lục 10/A9 lại đánh 'Không'.")

    so_can = _dem_can(d)
    nhom_can: dict[str, int] = {}
    for khoa_top in ("bia", "don_mau4", "ly_lich_khoa_hoc", "phu_luc_10", "phu_luc_11", "icf", "mien_icf"):
        nhom_can[khoa_top] = _dem_can(d.get(khoa_top))

    word_docs = sorted(thu_muc_hdd.glob("*.docx")) if thu_muc_hdd.is_dir() else []
    moi_hon = False
    if word_docs:
        newest_word = max(p.stat().st_mtime for p in word_docs)
        if newest_word < duong_dan_json.stat().st_mtime:
            moi_hon = True

    print(f"=== Kiểm hồ sơ HĐĐĐ BVQY175 — {study} ===")
    print(f"Tổng ô còn [CẦN...]: {so_can}")
    for k, v in nhom_can.items():
        print(f"  - {k}: {v}")
    if word_docs:
        print(f"Số tệp Word đã dựng: {len(word_docs)}" + (" (CŨ HƠN JSON — chạy lại `dung`)" if moi_hon else ""))
    else:
        print("Chưa có tệp Word nào — chạy `dung --ghi` để điền mẫu.")

    if van_de:
        print("\nVẤN ĐỀ:")
        for v in van_de:
            print(f"  ✗ {v}")
        return 1
    if so_can > 0 or not word_docs or moi_hon:
        print("\nCòn việc cần làm (xem trên).")
        return 1
    print("\nSạch — không phát hiện vấn đề cấu trúc/logic (KHÔNG thay việc bác sĩ tự kiểm nội dung).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Hồ sơ Hội đồng Đạo đức BVQY175 — sinh nháp Quyển 1 + Quyển 2."
    )
    sub = p.add_subparsers(dest="lenh", required=True)

    p_mau = sub.add_parser("mau", help="Dò bộ mẫu bệnh viện")
    p_mau.set_defaults(func=kiem_mau)

    p_trich = sub.add_parser("trich", help="Trích dữ kiện đề tài vào JSON nháp")
    p_trich.add_argument("--study", required=True)
    p_trich.add_argument("--exports-root", default="exports")
    p_trich.add_argument("--ghi", action="store_true")
    p_trich.add_argument("--ghi-de", action="store_true")
    p_trich.set_defaults(func=lenh_trich)

    p_dung = sub.add_parser("dung", help="Điền mẫu Word của bệnh viện")
    p_dung.add_argument("--study", required=True)
    p_dung.add_argument("--exports-root", default="exports")
    p_dung.add_argument("--quy-trinh", choices=["rut_gon", "day_du", "ca_hai"], required=True)
    p_dung.add_argument("--ghi", action="store_true")
    p_dung.set_defaults(func=lenh_dung)

    p_kiem = sub.add_parser("kiem", help="Kiểm JSON + Word")
    p_kiem.add_argument("--study", required=True)
    p_kiem.add_argument("--exports-root", default="exports")
    p_kiem.set_defaults(func=lenh_kiem)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
