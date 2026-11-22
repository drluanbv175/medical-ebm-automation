#!/usr/bin/env python3
"""MA TRẬN 8 NGUYÊN TẮC của đề cương: phần cấu trúc × nguyên tắc, mỗi ô là các PHÉP ĐO đã có của hệ (22/11/2026).

VÌ SAO (bác sĩ 22/11/2026): «Đề cương nghiên cứu theo từng tiêu chuẩn và từng tiêu chuẩn trong từng cấu trúc đề cương
nghiên cứu phải Tính trung thực và minh bạch (Integrity), Tính khoa học (Scientific Validity), Tính đạo đức (Ethical
Conduct), Tính khách quan (Objectivity), Tính tái lập (Reproducibility), Tính hợp lệ và tin cậy (Validity &
Reliability), Tôn trọng đối tượng nghiên cứu, Kiểm soát chất lượng liên tục». Nguyên tắc tổng: «Mỗi quyết định trong
nghiên cứu phải dựa trên bằng chứng khoa học, được thực hiện một cách đạo đức, được kiểm chứng khách quan, và chỉ được
chuyển sang bước tiếp theo khi bước hiện tại đã đạt chuẩn xác định trước.» Trước công cụ này hệ đo đề cương theo PHẦN
(K1–K19) và theo MỤC CHUẨN (K17) nhưng không trục nào đo theo 8 nguyên tắc.

CÁCH LÀM (tất định, chỉ đọc `exports/<mã>/`, không gọi mạng, không gọi API trả phí):
  • HÀNG = 18 phần đề cương theo khoá bền `skill_standards.DE_CUONG_SECTION_KEYS` (tiêu đề lấy qua
    `de_cuong_section`, không viết cứng số mục). CỘT = 8 nguyên tắc (`NGUYEN_TAC`, mỗi nguyên tắc có định nghĩa vận hành
    và nguồn chuẩn — PMID đã tra PubMed và kiểm rút bài ngày 22/11/2026; văn bản quy phạm ghi tên, phiên bản, năm).
  • Ô = danh sách PHÉP ĐO đã có, gọi bằng import hàm (không viết lại): K3/K5/K6/K9/K10/K12/K13/K15/K16 và từng mục K17
    của `kiem_de_cuong_nop_hoi_dong`/`kiem_chuan_de_cuong_theo_muc`; các trục `nhat_quan_xuyen_cong`;
    `doi_chieu_sai_lech_sap`, `doi_chieu_bien_de_cuong`, `ma_tran_muc_tieu_bien`, `bien_phai_sinh` (trạng thái duyệt
    công thức); tiêu chí tự động của các cổng chấm SỐNG qua `cong_song.trang_thai_song`; tư vấn số liệu ↔ toàn văn
    `kiem_so_lieu_toan_van`; biên bản Hội đồng Khoa học máy còn hiệu lực (`hoi_dong_khoa_hoc`, đọc tệp). Cộng các phép
    đo MỚI (mã `TN-…`, `PHEP_DO_MOI`) dựng từ dữ kiện máy đọc đã có (study_meta, sổ rủi ro, luật kiểm dữ liệu…).
    Mọi ánh xạ có lý do ghi trong bảng (`ANH_XA_*`): một phép đo chỉ gắn vào ô mà nó thật sự đo.
  • KẾT QUẢ Ô: có phép đo đỏ ⇒ 🔴 · mọi phép đo xanh ⇒ 🟢 · không có phép đo, hoặc còn phép đo «chưa đo được» (kể cả
    khi các phép đo khác xanh — không bao giờ báo xanh khi một phần chưa đo) ⇒ ⚪ · «không áp dụng» chỉ khi phần hoặc
    nguyên tắc không tồn tại với thiết kế theo điều kiện của chính hệ (tổng quan hệ thống không có người tham gia —
    `kiem_chuan_de_cuong_theo_muc._KHONG_NGUOI_THAM_GIA`, `kiem_de_cuong_nop_hoi_dong.KHONG_CAN_DONG_Y`; không có cỡ mẫu
    — `nhat_quan_xuyen_cong.thong_so_bat_buoc`).
  • TRẠNG THÁI TỪNG LOẠI PHÉP ĐO: luật K theo dòng (lỗi «dòng N» rơi vào phần chứa dòng N; không lỗi ⇒ xanh ở các phần
    luật quét); mục K17 đạt/thiếu ⇒ xanh/đỏ, «cảnh báo» (chuẩn chưa đối chiếu bảng gốc) và «chưa đo» ⇒ ⚪; trục nhất
    quán khớp ⇒ xanh, lệch cứng/lệch mềm ⇒ đỏ, cần xem/chưa đủ để so ⇒ ⚪, trục vắng (bộ đối chiếu tự bỏ vì không áp
    dụng) ⇒ không áp dụng, trừ thông số bắt buộc theo thiết kế ⇒ ⚪; tiêu chí cổng PASS ⇒ xanh, BLOCK ⇒ đỏ,
    REVIEW/không đo được ⇒ ⚪, cổng chưa chạy (chưa có checkpoint) ⇒ ⚪ — khâu sau chưa tới không làm đỏ đề cương.

TRỤC TỔNG 5 TIÊU CHÍ (`truc_tong`, in đầu báo cáo): giá trị câu hỏi · phương pháp phù hợp · khả thi · đạo đức · kết
quả kiểm chứng được — mỗi tiêu chí gộp các phép đo của ma trận (bộ lọc có lý do, `TRUC_TONG`) với chốt hệ ngoài ma trận
(FINER G0, cổng chấm sống, xác nhận khả năng tuyển G3, kế hoạch triển khai A13), luật gộp như ô.

K20 (`loi_k20`, nối vào `kiem_de_cuong_nop_hoi_dong.kiem`): ô 🔴 do phép đo NGOÀI K1–K19 thì chặn — lỗi của chính
K1–K19 đã được các luật đó báo tại chỗ, K20 không nhân đôi. Ô ⚪ chỉ BÁO kèm số lượng (`canh_bao_k20`), chưa chặn:
chặn ⚪ khi phép đo chưa xây là làm đỏ giả.

Lệnh:  python3 tools/tam_nguyen_tac_de_cuong.py --study <mã> [--goc <thư mục chứa exports/>] [--json] [--ghi]
       --ghi ghi `MA_TRAN_8_NGUYEN_TAC_<mã>.md/.json` vào thư mục đề tài.
Mã thoát: 0 không 🔴, không ⚪ · 1 có 🔴 · 2 chỉ còn ⚪ · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import skill_standards as S  # noqa: E402

XANH, DO, CHUA_DO, KAD = "xanh", "do", "chua_do", "khong_ap_dung"
BIEU_TUONG = {XANH: "🟢", DO: "🔴", CHUA_DO: "⚪", KAD: "—"}
PHAN: Tuple[str, ...] = tuple(S.DE_CUONG_SECTION_KEYS)


# ═════════════════════════════════ 8 NGUYÊN TẮC — định nghĩa vận hành và nguồn ═════════════════════════════════
@dataclass(frozen=True)
class Nguon:
    ten: str
    phien_ban: str
    nam: str
    pmid: str = ""
    doi: str = ""
    ghi_chu: str = ""


@dataclass(frozen=True)
class NguyenTac:
    khoa: str
    ten_vi: str
    ten_en: str
    dinh_nghia: str
    nguon: Tuple[Nguon, ...]
    goi_y: str  # gợi ý phép đo cần xây cho ô ⚪ của nguyên tắc này


# PMID/DOI dưới đây đã tra PubMed (22/11/2026) và kiểm rút bài bằng tools/check_citation_retraction.py — 6/6 sạch (tầng
# PubMed); hai nguồn của phép đo mới — Gilbert 1996 (PMID 8599488, độ tin cậy giữa người trích hồ sơ) và PRISMA-S
# (PMID 34285662) — tra và kiểm rút bài cùng ngày, sạch. Số đoạn của Tuyên bố Helsinki 2024 đối chiếu trang chính
# thức WMA ngày 22/11/2026 (§16–18 nguy cơ–lợi ích, §19–20 nhóm dễ tổn thương, §21 yêu cầu khoa học,
# §22 nội dung đề cương, §23 hội đồng đạo đức, §24 riêng tư, §26 thông tin cho người tham gia gồm
# quyền từ chối/rút lui, §35 đăng ký, §36 công bố cả kết quả âm tính). Hướng dẫn CIOMS 2016 số 10 và 12 theo
# `can_cu_dao_duc.py` (đã đối chiếu nguyên văn 19/11/2026). Văn bản quy phạm không có PMID: KHÔNG gán định danh.
_HELSINKI = Nguon("Tuyên bố Helsinki (WMA)", "sửa đổi lần thứ 75, Helsinki 10/2024", "2024", pmid="39425955",
                  doi="10.1001/jama.2024.21972")
_SINGAPORE = Nguon("Singapore Statement on Research Integrity (World Conference on Research Integrity)", "2010",
                   "2010", pmid="21390871", doi="10.1080/08989621.2011.557296",
                   ghi_chu="bản đăng lại kèm bình luận: Resnik DB, Shamoo AE. Account Res 2011;18(2):71-5")
_TOP2015 = Nguon("Transparency and Openness Promotion (TOP) Guidelines", "TOP 2015", "2015", pmid="26113702",
                 doi="10.1126/science.aab2374")
_TOP2025 = Nguon("Transparency and Openness Promotion (TOP) Guidelines", "TOP 2025", "2026", pmid="42557573",
                 doi="10.1186/s41073-026-00223-0")
_COSMIN_TAX = Nguon("COSMIN — phân loại và định nghĩa đặc tính đo lường", "Delphi 2010", "2010", pmid="20494804",
                    doi="10.1016/j.jclinepi.2010.02.006")
_COSMIN_CL = Nguon("COSMIN checklist", "2010", "2010", pmid="20169472", doi="10.1007/s11136-010-9606-8")
_CIOMS = Nguon("CIOMS — International Ethical Guidelines for Health-related Research Involving Humans", "2016",
               "2016", ghi_chu="Hướng dẫn 10 (miễn/sửa đổi đồng thuận), Hướng dẫn 12 (dữ liệu)")
_ICH_E6 = Nguon("ICH E6(R3) Good Clinical Practice", "R3 (Step 4)", "2025",
                ghi_chu="chất lượng theo thiết kế, yếu tố trọng yếu chất lượng, quản lý chất lượng dựa trên rủi ro")
_ICH_E9 = Nguon("ICH E9 Statistical Principles for Clinical Trials + phụ lục E9(R1) estimand", "E9 1998; E9(R1) 2019",
                "2019", ghi_chu="định trước kế hoạch phân tích")
_TT43 = Nguon("Thông tư 43/2024/TT-BYT (Hội đồng đạo đức trong nghiên cứu y sinh học)", "ngày 12/12/2024", "2024",
              ghi_chu="Điều 7 khoản 1 điểm b — miễn phiếu tình nguyện; Điều 16 khoản 6 — thẩm định rút gọn")
_LUAT91 = Nguon("Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15", "2025", "2025",
                ghi_chu="kèm Nghị định 356/2025/NĐ-CP hướng dẫn thi hành")

NGUYEN_TAC: Tuple[NguyenTac, ...] = (
    NguyenTac("trung_thuc", "Tính trung thực và minh bạch", "Integrity",
              "Mọi khẳng định và con số có nguồn thật truy được; một thông số mang cùng một giá trị ở mọi hồ sơ trình "
              "các cơ quan; khai kinh phí, xung đột lợi ích, đăng ký; không dẫn bài đã rút.",
              (_SINGAPORE, _HELSINKI, _TOP2025),
              "đối chiếu khẳng định/số liệu của phần này với nguồn có định danh hoặc với cùng thông số ở hồ sơ khác"),
    NguyenTac("khoa_hoc", "Tính khoa học", "Scientific Validity",
              "Câu hỏi dựa trên hiểu biết đầy đủ y văn và khoảng trống thật; thiết kế, cỡ mẫu, kế hoạch phân tích hợp "
              "câu hỏi và mục tiêu; đủ yếu tố của chuẩn báo cáo theo thiết kế (Helsinki §21).",
              (_HELSINKI, _CIOMS),
              "phân xử Hội đồng Khoa học có biên bản còn hiệu lực cho đúng bản đề cương, hoặc tiêu chí chuẩn theo mục"),
    NguyenTac("dao_duc", "Tính đạo đức", "Ethical Conduct",
              "Nghiên cứu chỉ tiến hành sau khi Hội đồng Đạo đức chấp thuận; nguy cơ–gánh nặng được cân với lợi ích và "
              "giảm thiểu; kế hoạch an toàn tương xứng thiết kế (Helsinki §16–18, §23; TT43/2024).",
              (_HELSINKI, _CIOMS, _TT43, _ICH_E6),
              "đối chiếu nội dung đạo đức của phần này với hồ sơ G2 cùng phiên bản"),
    NguyenTac("khach_quan", "Tính khách quan", "Objectivity",
              "Quyết định phân tích và kết cục được định trước, khoá trước dữ liệu, không đổi lén; biện pháp kiểm soát "
              "sai lệch có phân tích tương ứng; vai trò thu thập/giám sát độc lập; khẳng định không khái quát "
              "quá chứng cứ.",
              (_ICH_E9, _TOP2025, _SINGAPORE),
              "kiểm tính định trước: quyết định của phần này đã ghi trước dữ liệu và không đổi giữa các hồ sơ"),
    NguyenTac("tai_lap", "Tính tái lập", "Reproducibility",
              "Người khác làm lại được từ hồ sơ: từ điển biến, công thức phái sinh đã duyệt, đặc tả phân tích máy đọc, "
              "phần mềm và hạt giống, kế hoạch quản lý dữ liệu, tham số cỡ mẫu đủ để tính lại.",
              (_TOP2015, _TOP2025, _ICH_E6),
              "khai đủ tham số/đặc tả máy đọc để người khác làm lại phần này"),
    NguyenTac("hop_le_tin_cay", "Tính hợp lệ và tin cậy", "Validity & Reliability",
              "Biến được định nghĩa và đo đúng khái niệm (giá trị) một cách ổn định (độ tin cậy): công cụ có đặc tính "
              "đo lường, biến khớp công cụ và từ điển, kiểu biến đúng.",
              (_COSMIN_TAX, _COSMIN_CL),
              "đối chiếu định nghĩa đo lường của phần này với công cụ/từ điển (đặc tính đo lường theo COSMIN)"),
    NguyenTac("ton_trong", "Tôn trọng đối tượng nghiên cứu", "Respect for participants",
              "Có đồng thuận tự nguyện hoặc căn cứ miễn hợp pháp; người tham gia được biết quyền từ chối/rút lui không "
              "bị ảnh hưởng chăm sóc; khử định danh, bảo vệ dữ liệu cá nhân (Helsinki §24, §26; CIOMS 2016 HD 10, 12; "
              "TT43/2024; Luật 91/2025/QH15).",
              (_HELSINKI, _CIOMS, _TT43, _LUAT91),
              "đối chiếu biện pháp bảo vệ người tham gia của phần này (đồng thuận, riêng tư, quyền rút lui)"),
    NguyenTac("kiem_soat_cl", "Kiểm soát chất lượng liên tục", "Continuous quality control",
              "Chất lượng theo thiết kế: yếu tố trọng yếu chất lượng, kế hoạch giám sát, sổ rủi ro có biện pháp, CAPA "
              "và người chịu trách nhiệm, luật kiểm dữ liệu — rà lại định kỳ (ICH E6(R3)).",
              (_ICH_E6,),
              "luật kiểm/giới hạn chấp nhận và hành động khắc phục cho hoạt động của phần này"),
)
NT: Tuple[str, ...] = tuple(n.khoa for n in NGUYEN_TAC)
_NT_THEO_KHOA = {n.khoa: n for n in NGUYEN_TAC}


# ═════════════════════════════════ PHẦN của đề cương: nhận theo tiêu đề ═════════════════════════════════
# Thứ tự = ưu tiên. Mẫu ưu tiên chạy TRƯỚC tiêu đề canonical (vd «PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH» là kế hoạch
# phân tích, không phải «Tóm tắt»), tiêu đề canonical của khuôn 18 mục chạy sau, rồi mẫu cho khuôn BVQY175/bản cũ.
_KHONG_PHAN = r"^(?:MỤC LỤC|DANH MỤC)"
_MAU_UU_TIEN: Tuple[Tuple[str, str], ...] = (
    ("tltk", r"TÀI LIỆU THAM KHẢO"),
    ("sap", r"KẾ HOẠCH PHÂN TÍCH|phân tích (số liệu|thống kê)|Xử lý và phân tích"),
    ("dukien_ketqua", r"DỰ KIẾN KẾT QUẢ|Kết quả theo mục tiêu|Đặc điểm đối tượng|bàn luận|khung bảng"),
    ("sailech", r"Hạn chế|Sai số|Sai lệch|khống chế|SƠ ĐỒ NHÂN QUẢ|\bDAG\b|nguy cơ sai lệch"),
)
_MAU_PHAN: Tuple[Tuple[str, str], ...] = (
    ("daoduc", r"Đạo đức|ĐỒNG Ý THAM GIA|ĐỒNG THUẬN|Xung đột lợi ích|PHIẾU ĐỒNG Ý|BẢN THÔNG TIN|An toàn|biến cố"),
    ("quantri_dulieu", r"quản lý dữ liệu|Quản trị dữ liệu|bảo mật"),
    ("phobien", r"phổ biến|Đăng ký nghiên cứu|ứng dụng kết quả"),
    ("tiendo", r"Tiến độ|KẾ HOẠCH THỰC HIỆN|Nhân lực|phân công|kinh phí|nguồn lực|Quản lý rủi ro|CÁN BỘ THAM GIA|"
               r"Tổ chức thực hiện"),
    ("comau", r"Cỡ mẫu"),
    ("doituong", r"chọn mẫu|Tuyển mẫu|Tiêu chuẩn (lựa )?chọn|Tiêu chuẩn loại|Đối tượng nghiên cứu|Nhóm bệnh và nhóm "
                 r"chứng|Lựa chọn nghiên cứu|Sàng lọc"),
    ("bienso", r"Biến số|chỉ số nghiên cứu|Biến kết cục|Biến độc lập|BẢNG BIẾN|MÃ HO[ÁA]|Định nghĩa|Biến dự báo|"
               r"tiêu chuẩn tham chiếu|chuẩn vàng"),
    ("congcu", r"Công cụ|kỹ thuật thu thập|Bộ câu hỏi|Quy trình nghiên cứu|PHIẾU KHẢO SÁT|PHIẾU THU THẬP|"
               r"PHIẾU TRÍCH XUẤT|Cách tính điểm|đặc tính đo lường|Chiến lược tìm|Trích xuất|"
               r"Các bước tiến hành|BỆNH ÁN NGHIÊN CỨU"),
    ("cauhoi", r"Câu hỏi|Giả thuyết"),
    ("muctieu", r"MỤC TIÊU"),
    ("thietke", r"Thiết kế|Địa điểm|Thời gian nghiên cứu|bối cảnh|Ngẫu nhiên|làm mù|giấu phân bổ|Can thiệp|"
                r"ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP|Phương pháp nghiên cứu"),
    ("tongquan", r"TỔNG QUAN|Khung lý thuyết|Khoảng trống"),
    ("datvande", r"ĐẶT VẤN ĐỀ"),
    ("tomtat", r"TÓM TẮT|THÔNG TIN CHUNG|^ĐỀ CƯƠNG"),  # «# ĐỀ CƯƠNG NGHIÊN CỨU…» = khối bìa/tên đề tài
)
_DE_MUC_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_TIEN_TO_DE_MUC = re.compile(r"^\s*(?:PHỤ LỤC\s+[A-Z0-9]+\.?\s*|CHƯƠNG\s+\d+\.?\s*|[\dIVX]+(?:\.\d+)*\.?\s+)",
                             re.IGNORECASE)


def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or ""))


def phan_cua_tieu_de(tieu_de: str) -> Optional[str]:
    """Khoá phần (DE_CUONG_SECTION_KEYS) của MỘT tiêu đề; None khi không nhận ra. «_khong» = mục lục/danh mục."""
    td = re.sub(r"[*_`]", "", _nfc(tieu_de)).strip()
    if re.search(_KHONG_PHAN, td, re.IGNORECASE):
        return "_khong"
    for khoa, mau in _MAU_UU_TIEN:
        if re.search(mau, td, re.IGNORECASE):
            return khoa
    goc = _TIEN_TO_DE_MUC.sub("", td).casefold()
    for khoa in PHAN:
        if goc.startswith(_nfc(S.de_cuong_section(khoa)[1]).casefold()):
            return khoa
    for khoa, mau in _MAU_PHAN:
        if re.search(mau, td, re.IGNORECASE):
            return khoa
    return None


def phan_theo_dong(md: str) -> List[Optional[str]]:
    """Phần của TỪNG dòng (chỉ số 0 = dòng 1). Dòng trước tiêu đề đầu tiên (bìa) thuộc «tomtat».

    Ngữ cảnh: tiêu đề con trong Đặt vấn đề/Tổng quan mang phần của chương (vd «1.2. Công cụ đo lường…» của tổng quan
    KHÔNG phải công cụ của đề tài), trừ «MỤC TIÊU»; trong chương Dự kiến kết quả mang phần của chương, trừ «Hạn chế»;
    nơi khác tiêu đề không nhận ra thì kế thừa tiêu đề cha."""
    dong = _nfc(md).split("\n")
    ra: List[Optional[str]] = []
    ngan: List[Tuple[int, Optional[str]]] = []  # (cấp, phần hiệu lực)
    hien_tai: Optional[str] = "tomtat"
    for d in dong:
        m = _DE_MUC_RE.match(d)
        if m:
            cap = len(m.group(1))
            while ngan and ngan[-1][0] >= cap:
                ngan.pop()
            rieng = phan_cua_tieu_de(m.group(2))
            cha = ngan[-1][1] if ngan else None
            if rieng == "_khong":
                hieu_luc: Optional[str] = None
            elif cha in ("tongquan", "datvande"):
                hieu_luc = "muctieu" if rieng == "muctieu" else cha
            elif cha == "dukien_ketqua":
                hieu_luc = "sailech" if rieng == "sailech" else cha
            else:
                hieu_luc = rieng or cha
            ngan.append((cap, hieu_luc))
            hien_tai = hieu_luc
        ra.append(hien_tai)
    return ra


# ═════════════════════════════════ kết quả phép đo và ngữ cảnh ═════════════════════════════════
@dataclass
class KetQuaDo:
    ma: str
    ten: str
    phan: str
    nguyen_tac: str
    trang_thai: str
    ly_do_anh_xa: str
    chi_tiet: List[str] = field(default_factory=list)
    nguon_k: bool = False  # phép đo thuộc K1–K19 (đã tự báo trong kiem_de_cuong_nop_hoi_dong) — K20 không nhân đôi


_PLACEHOLDER = re.compile(r"\[(?:CẦN|DỰ THẢO)", re.IGNORECASE)
_DONG_RE = re.compile(r"dòng (\d+)")


def _trong(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (list, dict)):
        return not v
    return not str(v).strip() or bool(_PLACEHOLDER.search(str(v)))


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


class NguCanh:
    """Dữ kiện của một đề tài, tính lười và giữ lại (mỗi bộ đo chạy MỘT lần cho cả ma trận)."""

    def __init__(self, out_dir: Path, study: str, loi_k: Optional[List[str]] = None):
        self.out_dir = Path(out_dir)
        self.study = study
        self._loi_k = loi_k
        self._dem: Dict[str, Any] = {}
        p = self.out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
        try:
            self.md: Optional[str] = _nfc(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            self.md = None
        self.meta = _doc_json(self.out_dir / "study_meta.json")
        gp = self.meta.get("gate_params") if isinstance(self.meta.get("gate_params"), dict) else {}
        self.gp: Dict[str, Dict[str, Any]] = {k: (v if isinstance(v, dict) else {}) for k, v in gp.items()}
        self.thiet_ke_tho = str(self.gp.get("G1", {}).get("design") or "").strip()
        self.thiet_ke = S.canonical_design_code(self.thiet_ke_tho) or ""

    def _luu(self, khoa: str, ham: Callable[[], Any]) -> Any:
        if khoa not in self._dem:
            try:
                self._dem[khoa] = ham()
            except Exception as e:  # noqa: BLE001 — bộ đo hỏng ⇒ «không đo được», không bao giờ xanh
                self._dem[khoa] = e
        return self._dem[khoa]

    @property
    def phan_dong(self) -> List[Optional[str]]:
        return self._luu("phan_dong", lambda: phan_theo_dong(self.md or ""))

    @property
    def tieu_de_dong(self) -> List[Optional[str]]:
        """Tiêu đề SÂU NHẤT chứa từng dòng (để phân biệt tiêu chuẩn chọn/loại)."""
        def chay() -> List[Optional[str]]:
            ra: List[Optional[str]] = []
            hien: Optional[str] = None
            for d in (self.md or "").split("\n"):
                m = _DE_MUC_RE.match(d)
                if m:
                    hien = m.group(2)
                ra.append(hien)
            return ra
        return self._luu("tieu_de_dong", chay)

    def phan_cua_dong(self, so: int) -> Optional[str]:
        pd = self.phan_dong
        return pd[so - 1] if isinstance(pd, list) and 1 <= so <= len(pd) else None

    def van_phan(self, *khoa: str) -> str:
        """Văn bản các dòng thuộc những phần đã nêu."""
        pd = self.phan_dong
        if not self.md or not isinstance(pd, list):
            return ""
        return "\n".join(d for d, k in zip(self.md.split("\n"), pd) if k in khoa)

    def co_nguoi_tham_gia(self) -> bool:
        import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415
        import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

        return not (self.thiet_ke in KCM._KHONG_NGUOI_THAM_GIA or self.thiet_ke_tho in KDN.KHONG_CAN_DONG_Y)

    def loi_k(self) -> Any:
        if self._loi_k is not None:
            return self._loi_k

        def chay() -> List[str]:
            import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

            global _DANG_TINH
            _DANG_TINH += 1
            try:
                return KDN.kiem(self.out_dir, self.study)
            finally:
                _DANG_TINH -= 1
        return self._luu("loi_k", chay)

    def k17(self) -> Any:
        import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

        return self._luu("k17", lambda: KCM.doi_chieu(self.md or "", self.thiet_ke_tho))

    def nq(self) -> Any:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

        return self._luu("nq", lambda: NQ.doi_chieu(self.out_dir, self.study))

    def cong(self, gate: str) -> Any:
        def chay() -> Dict[str, Any]:
            import cong_song as CS  # noqa: PLC0415

            return CS.trang_thai_song(gate, self.study, self.out_dir)
        return self._luu("cong_" + gate, chay)


_DANG_TINH = 0  # >0 khi đang gọi kiem_de_cuong_nop_hoi_dong.kiem từ trong mô-đun này — chặn K20 gọi vòng


def _kq(ma: str, ten: str, phan: str, nt: str, tt: str, ly_do: str, chi_tiet: Sequence[str] = (),
        nguon_k: bool = False) -> KetQuaDo:
    return KetQuaDo(ma, ten, phan, nt, tt, ly_do, [str(x) for x in chi_tiet], nguon_k)


# ═════════════════════════════════ A. LUẬT K1–K19 (kiem_de_cuong_nop_hoi_dong) ═════════════════════════════════
# K theo DÒNG: lỗi «dòng N» rơi vào phần chứa dòng N; không lỗi ⇒ xanh ở các phần luật quét. Khoá: (phần, nguyên tắc).
ANH_XA_K_DONG: Tuple[Tuple[str, str, Tuple[str, ...], str, str], ...] = (
    ("K10", "Số liệu kiểu kết quả có trích dẫn trong cùng mệnh đề", ("datvande", "tongquan", "dukien_ketqua"),
     "trung_thuc", "con số không nguồn là khẳng định không truy được (Singapore: trung thực; bác sĩ 20/11/2026)"),
    ("K12", "Mỗi tài liệu tham khảo đỡ một câu cụ thể, không trích gộp", ("datvande", "tongquan", "dukien_ketqua",
                                                                          "tltk"),
     "trung_thuc", "trích gộp/không trích làm mất truy nguyên từng khẳng định"),
    ("K15", "Khẳng định khái quát/định lượng mơ hồ có trích dẫn", ("datvande", "tongquan", "dukien_ketqua"),
     "khach_quan", "«đa số», «đã được chứng minh» không nguồn là khái quát vượt chứng cứ"),
    ("K16", "Câu nêu đã tra nguồn khớp nhật ký PRISMA-S", ("tongquan",),
     "trung_thuc", "khai đã tra một nguồn mà nhật ký không ghi là khai sai quá trình tìm"),
)
_K3_NHAN = {
    "đặt vấn đề": ("datvande", "khoa_hoc"), "mục tiêu nghiên cứu": ("muctieu", "khoa_hoc"),
    "tổng quan tài liệu": ("tongquan", "khoa_hoc"), "đối tượng và phương pháp": ("thietke", "khoa_hoc"),
    "đạo đức nghiên cứu": ("daoduc", "dao_duc"), "dự kiến kết quả": ("dukien_ketqua", "khoa_hoc"),
    "kế hoạch thực hiện": ("tiendo", "khoa_hoc"), "tài liệu tham khảo": ("tltk", "trung_thuc"),
    "phụ lục bản thông tin/phiếu đồng ý": ("daoduc", "ton_trong"),
    "phụ lục công cụ thu thập": ("congcu", "tai_lap"),
}
ANH_XA_K_CO_DINH: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("K5", "Cỡ mẫu, hiệu ứng thiết kế đã chốt ở G3 có trong đề cương", "comau", "trung_thuc",
     "con số trình Hội đồng phải là con số đã tính và chốt"),
    ("K6", "Mọi PMID nằm trong biên nhận rút bài A12 sạch", "tltk", "trung_thuc", "không dẫn bài đã rút"),
    ("K9", "Biểu bảng dự kiến đúng chuẩn, mỗi mục tiêu có bảng/biểu, ước lượng kèm KTC 95%", "dukien_ketqua",
     "khoa_hoc", "kết quả dự kiến phải trả lời từng mục tiêu bằng ước lượng có độ chính xác"),
    ("K13", "Tài liệu có PMID đúng Vancouver/NLM theo biên nhận A12", "tltk", "tai_lap",
     "trích dẫn đúng định danh để người đọc tìm lại được nguồn"),
)


def do_luat_k(ctx: NguCanh) -> List[KetQuaDo]:
    ra: List[KetQuaDo] = []
    if ctx.md is None:
        return ra
    loi = ctx.loi_k()
    if isinstance(loi, Exception):
        ly = f"bộ kiểm đề cương nộp hỏng: {type(loi).__name__}"
        for ma, ten, ds, nt, ly_do in ANH_XA_K_DONG:
            ra += [_kq(ma, ten, p, nt, CHUA_DO, ly_do, [ly], True) for p in ds]
        return ra
    theo_ma: Dict[str, List[str]] = {}
    for x in loi:
        theo_ma.setdefault(str(x).split(" ", 1)[0], []).append(str(x))
    for ma, ten, ds, nt, ly_do in ANH_XA_K_DONG:
        if ma == "K16":
            import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

            if KDN.nhat_ky_prisma_s(ctx.out_dir) is None:
                ra.append(_kq(ma, ten, "tongquan", nt, KAD, ly_do, ["đề tài không có nhật ký PRISMA-S"], True))
                continue
        theo_phan: Dict[str, List[str]] = {p: [] for p in ds}
        for x in theo_ma.get(ma, []):
            m = _DONG_RE.search(x)
            p = ctx.phan_cua_dong(int(m.group(1))) if m else None
            if p is None:
                p = ds[-1] if ma == "K12" and not m else ds[0]
                if m:
                    x += " (dòng ngoài các phần đã nhận diện)"
            theo_phan.setdefault(p, []).append(x)
        for p, ds_loi in theo_phan.items():
            ra.append(_kq(ma, ten, p, nt, DO if ds_loi else XANH, ly_do, ds_loi[:8], True))
    # K3 — đủ chương mục
    k3 = theo_ma.get("K3", [])
    for nhan, (p, nt) in _K3_NHAN.items():
        if nhan.startswith("phụ lục bản thông tin") and not ctx.co_nguoi_tham_gia():
            continue
        thieu = [x for x in k3 if f"«{nhan}»" in x]
        ra.append(_kq("K3", f"Có chương/mục «{nhan}»", p, nt, DO if thieu else XANH,
                      "thiếu chương thì Hội đồng không thẩm định được nội dung đó", thieu, True))
    for ma, ten, p, nt, ly_do in ANH_XA_K_CO_DINH:
        ds_loi = theo_ma.get(ma, [])
        ra.append(_kq(ma, ten, p, nt, DO if ds_loi else XANH, ly_do, ds_loi[:8], True))
    # K14 — chỉ phần «≥ 50% tài liệu xuất bản trong 10 năm» (hiểu biết y văn hiện hành, Helsinki §21); K14 chỉ áp
    # cho đề cương theo khuôn BVQY175 (có «# CHƯƠNG 1.»)
    ly14 = "nền y văn hiện hành: ≥ 50% tài liệu tham khảo trong 10 năm (Helsinki §21 — hiểu biết đầy đủ y văn)"
    if re.search(r"^# CHƯƠNG 1\.", ctx.md, re.M):
        moi = [x for x in theo_ma.get("K14", []) if "xuất bản trong 10 năm" in x]
        ra.append(_kq("K14", "Tài liệu tham khảo cập nhật (10 năm)", "tltk", "khoa_hoc", DO if moi else XANH, ly14,
                      moi, True))
    else:
        ra.append(_kq("K14", "Tài liệu tham khảo cập nhật (10 năm)", "tltk", "khoa_hoc", KAD, ly14,
                      ["K14 chỉ áp cho khuôn BVQY175"], True))
    return ra


# ═════════════════════════════════ B. TỪNG MỤC K17 (kiem_chuan_de_cuong_theo_muc) ═════════════════════════════════
# Phần đầu tiên mục khai (`MucKiem.phan[0]`) là nơi mục sống ⇒ (phần đề cương, nguyên tắc) với lý do.
ANH_XA_K17_PHAN: Dict[str, Tuple[str, str, str]] = {
    "bia": ("tomtat", "trung_thuc", "thông tin nhận diện đề tài, đăng ký, nhà tài trợ"),
    "dau": ("tomtat", "trung_thuc", "tên đề tài nêu đúng thiết kế"),
    "tom_tat": ("tomtat", "trung_thuc", "tóm tắt nêu đúng thiết kế và nội dung"),
    "dat_van_de": ("datvande", "khoa_hoc", "lý do khoa học của đề tài"),
    "tong_quan": ("tongquan", "khoa_hoc", "nền y văn và khoảng trống"),
    "cau_hoi": ("cauhoi", "khoa_hoc", "câu hỏi/giả thuyết định trước"),
    "muc_tieu": ("muctieu", "khoa_hoc", "mục tiêu cụ thể đo được"),
    "thiet_ke": ("thietke", "khoa_hoc", "thiết kế hợp câu hỏi"),
    "dia_diem": ("thietke", "tai_lap", "bối cảnh, thời gian đủ để làm lại"),
    "ngau_nhien": ("thietke", "khach_quan", "ngẫu nhiên hoá/giấu phân bổ/làm mù chống sai lệch"),
    "can_thiep": ("thietke", "tai_lap", "can thiệp mô tả đủ để lặp lại"),
    "tiep_can": ("thietke", "khoa_hoc", "cách tiếp cận định tính hợp câu hỏi"),
    "nhom_nc": ("thietke", "khach_quan", "phản tư/vai trò người thu thập định tính"),
    "doi_tuong": ("doituong", "khoa_hoc", "tiêu chuẩn chọn/loại định nghĩa đúng quần thể"),
    "chon_mau": ("doituong", "khach_quan", "quy trình chọn mẫu chống sai lệch chọn"),
    "chon_nc": ("doituong", "khach_quan", "quy trình chọn nghiên cứu chống sai lệch chọn"),
    "trinh_bay_ca": ("doituong", "khoa_hoc", "mô tả ca đủ thông tin lâm sàng"),
    "co_mau": ("comau", "khoa_hoc", "cỡ mẫu có cơ sở"),
    "bien_so": ("bienso", "hop_le_tin_cay", "biến định nghĩa và đo đúng khái niệm"),
    "phoi_nhiem": ("bienso", "hop_le_tin_cay", "phơi nhiễm định nghĩa và đo đúng"),
    "du_bao": ("bienso", "hop_le_tin_cay", "biến dự báo/kết cục dự báo định nghĩa đúng"),
    "xet_nghiem": ("bienso", "hop_le_tin_cay", "xét nghiệm và chuẩn tham chiếu đo đúng"),
    "bang_bien": ("bienso", "tai_lap", "bảng biến/mã hoá đủ để nhập và phân tích lại"),
    "danh_muc_ma": ("bienso", "tai_lap", "danh mục mã đủ để làm lại"),
    "cong_cu": ("congcu", "hop_le_tin_cay", "công cụ đo có đặc tính đo lường"),
    "phieu": ("congcu", "tai_lap", "phiếu thu thập đính kèm để lặp lại"),
    "quy_trinh": ("congcu", "tai_lap", "quy trình thu thập mô tả đủ"),
    "trich_xuat": ("congcu", "tai_lap", "quy trình trích xuất mô tả đủ"),
    "tim_kiem": ("congcu", "tai_lap", "chiến lược tìm tái lập được"),
    "phu_luc_tim": ("congcu", "tai_lap", "chuỗi tìm đầy đủ trong phụ lục"),
    "quan_ly_dl": ("quantri_dulieu", "tai_lap", "quản lý dữ liệu đủ để truy vết"),
    "phan_tich": ("sap", "khoa_hoc", "phương pháp phân tích hợp mục tiêu"),
    "tong_hop": ("sap", "khoa_hoc", "phương pháp tổng hợp hợp câu hỏi"),
    "kinh_te": ("sap", "khoa_hoc", "phương pháp đánh giá kinh tế"),
    "du_kien_kq": ("dukien_ketqua", "khoa_hoc", "kết quả dự kiến theo mục tiêu"),
    "ban_luan": ("dukien_ketqua", "khach_quan", "bàn luận không vượt chứng cứ"),
    "sai_so": ("sailech", "khach_quan", "nhận diện và khống chế sai lệch"),
    "nguy_co": ("sailech", "khach_quan", "đánh giá nguy cơ sai lệch"),
    "han_che": ("sailech", "trung_thuc", "nêu thẳng hạn chế"),
    "dao_duc": ("daoduc", "dao_duc", "chấp thuận và nội dung đạo đức"),
    "giam_sat": ("daoduc", "kiem_soat_cl", "giám sát an toàn/biến cố"),
    "pho_bien": ("phobien", "trung_thuc", "đăng ký và phổ biến minh bạch"),
    "kinh_phi": ("tiendo", "trung_thuc", "khai nguồn kinh phí"),
    "nhan_luc": ("tiendo", "kiem_soat_cl", "phân công trách nhiệm thực hiện"),
    "tien_do": ("tiendo", "kiem_soat_cl", "tiến độ theo mốc"),
}
# Ghi đè theo CHỦ ĐỀ mục (thắng ánh xạ theo phần): đồng thuận/riêng tư ⇒ tôn trọng đối tượng; kinh phí/xung đột lợi
# ích/đăng ký ⇒ trung thực–minh bạch.
_K17_CHU_DE: Tuple[Tuple[str, str, str], ...] = (
    (r"consent|đồng (ý|thuận)|privacy|confidential|riêng tư|bảo mật|dữ liệu cá nhân|miễn",
     "ton_trong", "đồng thuận/riêng tư của người tham gia"),
    (r"conflict|competing|xung đột lợi ích|fund|tài trợ|kinh phí|sponsor|regist|đăng ký",
     "trung_thuc", "khai kinh phí/xung đột lợi ích/đăng ký"),
)


def do_k17(ctx: NguCanh) -> List[KetQuaDo]:
    if ctx.md is None:
        return []
    kq = ctx.k17()
    if isinstance(kq, Exception):
        return [_kq("K17", "Chuẩn báo cáo theo mục", "thietke", "khoa_hoc", CHUA_DO, "chuẩn theo thiết kế",
                    [f"bộ đối chiếu K17 hỏng: {type(kq).__name__}"], True)]
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    muc_theo_ma: Dict[Tuple[str, str], Any] = {}
    for chuan, _ in kq["chuan"]:
        for m in KCM.danh_sach_muc(chuan, ctx.thiet_ke_tho) or []:
            muc_theo_ma[(m.chuan, m.ma)] = m
    ra: List[KetQuaDo] = []
    for r in kq["ket_qua"]:
        if r.trang_thai in ("khong_ap_dung", "bao_cao"):
            continue
        m = muc_theo_ma.get((r.chuan, r.ma))
        phan_k17 = (m.phan[0] if m and m.phan else "thiet_ke")
        p, nt, ly_do = ANH_XA_K17_PHAN.get(phan_k17, ("thietke", "khoa_hoc", "mục chuẩn theo thiết kế"))
        chu_de = f"{r.chu_de} {r.ma}"
        for mau, nt2, ly2 in _K17_CHU_DE:
            if re.search(mau, chu_de, re.IGNORECASE):
                nt, ly_do = nt2, ly2
                break
        tt = {"dat": XANH, "thieu": DO}.get(r.trang_thai, CHUA_DO)
        chi = list(r.thieu) if r.trang_thai == "thieu" else ([r.ly_do] if r.ly_do else [])
        if r.trang_thai == "canh_bao":
            chi = ["chuẩn chưa đối chiếu bảng gốc — tiêu chí chưa đủ tin cậy để kết luận"] + list(r.thieu)
        if tt == DO and r.chuan in KCM.CHUAN_CHO_BO_SINH:
            chi.append("K17 đang chỉ cảnh báo chuẩn này (chờ bộ sinh phủ) — vẫn là mục chuẩn còn thiếu")
        ra.append(_kq(f"K17:{r.chuan}:{r.ma}", f"{r.chuan} mục {r.ma} — {r.chu_de}", p, nt, tt,
                      f"{ly_do} (phần K17 «{phan_k17}»)", chi[:6], True))
    return ra


# ═════════════════════════════════ C. TRỤC NHẤT QUÁN XUYÊN CỔNG ═════════════════════════════════
# Trục bao bộ đối chiếu đã gọi thẳng ở mục D (kiem_soat_sai_lech, bien_de_cuong, ma_tran_muc_tieu) KHÔNG lặp ở đây.
ANH_XA_NQ: Dict[str, Tuple[str, str, str]] = {
    "co_mau": ("comau", "trung_thuc", "cỡ mẫu cùng một giá trị ở G3, đăng ký, SAP"),
    "alpha": ("comau", "trung_thuc", "alpha cùng giá trị ở G3 và SAP"),
    "power": ("comau", "trung_thuc", "lực mẫu cùng giá trị ở G3 và SAP"),
    "sai_so_d": ("comau", "trung_thuc", "sai số cho phép cùng giá trị ở G3 và SAP"),
    "co_mau_tinh_lai": ("comau", "tai_lap", "tính lại từ tham số đã ghim ra đúng cỡ mẫu"),
    "co_mau_cho_ket_cuc": ("comau", "khoa_hoc", "cỡ mẫu được tính cho kết cục chính"),
    "tai_lieu_nop_co_mau": ("comau", "trung_thuc", "mọi tài liệu nộp ghi đúng cỡ mẫu"),
    "chon_mau_co_mau": ("doituong", "khoa_hoc", "chọn mẫu cụm khớp hiệu ứng thiết kế của cỡ mẫu"),
    "ky_thuat_chon_mau": ("doituong", "trung_thuc", "kỹ thuật chọn mẫu mô tả giống nhau ở mọi hồ sơ"),
    "thiet_ke": ("thietke", "trung_thuc", "mã thiết kế cùng giá trị ở mọi cổng và đăng ký"),
    "mo_ta_thiet_ke": ("thietke", "trung_thuc", "thiết kế, tuyển mẫu, phiên bản SAP mô tả nhất quán"),
    "chuan_bao_cao": ("thietke", "tai_lap", "cùng bộ chuẩn báo cáo ở mọi hồ sơ"),
    "quan_the": ("doituong", "trung_thuc", "quần thể diễn đạt nhất quán giữa các cổng"),
    "ket_cuc_chinh": ("bienso", "khach_quan", "kết cục chính không đổi giữa các cổng (chống đổi kết cục)"),
    "thoi_diem_ket_cuc": ("bienso", "khach_quan", "thời điểm đo kết cục chính không đổi"),
    "loai_gia_thuyet": ("cauhoi", "khach_quan", "loại giả thuyết định trước, cùng ở G0, G3, SAP"),
    "cau_hoi_gia_thuyet": ("cauhoi", "khoa_hoc", "câu hỏi/giả thuyết phủ mục tiêu"),
    "muc_tieu_phan_tich": ("sap", "khoa_hoc", "mỗi mục tiêu có phân tích trong SAP"),
    "muc_tieu_ho_so_g2": ("muctieu", "trung_thuc", "mục tiêu trình Hội đồng Đạo đức giống mục tiêu đã chốt"),
    "tong_quan_khoang_trong": ("tongquan", "khoa_hoc", "có khoảng trống nghiên cứu"),
    "trich_dan_tong_quan": ("tongquan", "trung_thuc", "danh mục tài liệu khớp trích dẫn trong thân"),
    "ten_de_tai": ("tomtat", "trung_thuc", "tên đề tài giống nhau ở mọi nơi"),
    "cong_cu_tu_dien": ("congcu", "hop_le_tin_cay", "mã đáp án của phiếu khớp từ điển nhập liệu"),
    "cong_cu_do_luong": ("congcu", "hop_le_tin_cay", "đặc tính đo lường của công cụ truy nguyên được"),
    "quy_trinh_du_lieu": ("quantri_dulieu", "kiem_soat_cl", "quyết định quy trình dữ liệu không mâu thuẫn"),
    "de_cuong_nop": ("tomtat", "trung_thuc", "phiên bản, kế hoạch phân tích, phiếu đồng ý, kinh phí khớp hồ sơ"),
    "dac_ta_cho_bo_bien": ("sap", "tai_lap", "đặc tả phân tích dùng đúng bộ biến"),
    "dac_ta_phan_tich": ("sap", "tai_lap", "đặc tả phân tích máy đọc chạy được"),
}
_NQ_MUC = {"khop": XANH, "lech_cung": DO, "lech_mem": DO, "can_xem": CHUA_DO, "chua_du": CHUA_DO}
# Trục đo LẠI đúng điều một luật K đã đo trên đề cương nộp ⇒ đánh dấu nguồn K (K20 không chặn lần hai cùng một lỗi).
NQ_TRUNG_K: Dict[str, str] = {"tai_lieu_nop_co_mau": "K5 (cỡ mẫu G3 có trong đề cương)",
                              "trich_dan_tong_quan": "K6/K12 (PMID trong biên nhận A12, mỗi tài liệu được trích)"}


def do_nhat_quan(ctx: NguCanh) -> List[KetQuaDo]:
    kq = ctx.nq()
    ra: List[KetQuaDo] = []
    if isinstance(kq, Exception) or not isinstance(kq, dict):
        for ma, (p, nt, ly) in ANH_XA_NQ.items():
            ra.append(_kq("NQ:" + ma, "Nhất quán xuyên cổng: " + ma, p, nt, CHUA_DO, ly,
                          [f"bộ đối chiếu nhất quán hỏng: {type(kq).__name__}"]))
        return ra
    import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

    theo_ma = {k.get("ma"): k for k in kq.get("thong_so") or []}
    co_loi_chuoi = "chuoi_loi" in theo_ma
    bat_buoc = set(NQ.thong_so_bat_buoc(ctx.thiet_ke_tho or None))
    for ma, (p, nt, ly) in ANH_XA_NQ.items():
        k = theo_ma.get(ma)
        if k is None:
            if ma in bat_buoc:
                ra.append(_kq("NQ:" + ma, "Nhất quán xuyên cổng: " + ma, p, nt, CHUA_DO, ly,
                              ["thông số bắt buộc theo thiết kế nhưng bộ đối chiếu không trả trục này"]))
            elif co_loi_chuoi and ma in NQ.TRUC_CHUOI:
                ra.append(_kq("NQ:" + ma, "Nhất quán xuyên cổng: " + ma, p, nt, CHUA_DO, ly,
                              ["một trục chuỗi lỗi khi chạy — không biết có phải trục này"]))
            else:
                ra.append(_kq("NQ:" + ma, "Nhất quán xuyên cổng: " + ma, p, nt, KAD, ly,
                              ["bộ đối chiếu không áp dụng trục này cho đề tài"]))
            continue
        tt = _NQ_MUC.get(str(k.get("muc")), CHUA_DO)
        chi = [f"{k.get('muc')}: {str(k.get('ghi_chu') or '')[:300]}"]
        if ma in NQ_TRUNG_K:
            chi.append("cùng điều với " + NQ_TRUNG_K[ma] + " — K20 không chặn lần hai")
        ra.append(_kq("NQ:" + ma, f"Nhất quán xuyên cổng: {k.get('ten') or ma}", p, nt, tt, ly, chi,
                      nguon_k=ma in NQ_TRUNG_K))
    return ra


# ═════════════════════════════════ D. TIÊU CHÍ TỰ ĐỘNG CỦA CỔNG (chấm sống) ═════════════════════════════════
# Chỉ tiêu chí đo NỘI DUNG đề cương/hồ sơ; tiêu chí về chữ ký/cổng trước đã chốt chưa (vd G2-AUTO-02, G3-AUTO-01,
# G4-AUTO-12) hay về dữ liệu thật (G5-AUTO-04…09) KHÔNG thuộc ma trận đề cương.
ANH_XA_CONG: Dict[str, Tuple[str, str, str]] = {
    "G0-AUTO-02": ("datvande", "trung_thuc", "nền bằng chứng là PMID thật từ PubMed"),
    "G0-AUTO-03": ("tongquan", "trung_thuc", "số kết quả tìm dùng để kết luận khoảng trống là số thật"),
    "G0-AUTO-06": ("tongquan", "khoa_hoc", "đã tra sổ đăng ký thử nghiệm trước khi khẳng định tính mới"),
    "G1-AUTO-02d": ("thietke", "khoa_hoc", "thiết kế hợp loại câu hỏi đã chốt"),
    "G1-AUTO-02b": ("thietke", "kiem_soat_cl", "ICH E6(R3) Annex 2: phù hợp mục đích và giám sát"),
    "G1-AUTO-03": ("thietke", "khoa_hoc", "chuẩn báo cáo khớp thiết kế"),
    "G1-AUTO-03b": ("thietke", "khoa_hoc", "chuẩn đề cương khớp thiết kế"),
    "G1-AUTO-04b": ("sailech", "khach_quan", "so sánh phương án và kiểm soát đủ nhóm sai lệch"),
    "G1-AUTO-06": ("tongquan", "trung_thuc", "bằng chứng trong sổ chứng cứ có PMID/DOI"),
    "G2-AUTO-01": ("daoduc", "trung_thuc", "hồ sơ không tự gán số phê duyệt, không PII, không tự xưng đã khoá"),
    "G2-AUTO-02b": ("daoduc", "dao_duc", "Annex 2: hội đồng đạo đức, đồng thuận, riêng tư, quản trị dữ liệu"),
    "G2-AUTO-03": ("daoduc", "ton_trong", "bộ hồ sơ có phiếu đồng ý đủ mục theo thiết kế"),
    "G2-AUTO-04": ("phobien", "trung_thuc", "WHO TRDS đủ 24 mục"),
    "G2-AUTO-07": ("daoduc", "dao_duc", "kế hoạch an toàn tương xứng thiết kế"),
    "G2-AUTO-08": ("phobien", "trung_thuc", "mục khoa học của đăng ký có nội dung thật"),
    "G2-AUTO-11": ("phobien", "trung_thuc", "quyết định đăng ký khớp nghĩa vụ đăng ký (Helsinki §35)"),
    "G3-AUTO-05": ("comau", "trung_thuc", "effect size có định danh nguồn thật"),
    "G3-AUTO-06": ("comau", "khoa_hoc", "effect size đọc từ toàn văn, không phải số thô"),
    "G3-AUTO-07": ("comau", "khoa_hoc", "alpha/power theo quy ước, đã xử lý đa so sánh"),
    "G3-AUTO-08": ("comau", "trung_thuc", "tham số phụ của công thức có nguồn"),
    "G3-AUTO-12": ("comau", "hop_le_tin_cay", "thiết kế chùm: ICC có nguồn, hiệu ứng thiết kế đúng số học"),
    "G3-AUTO-13": ("comau", "khoa_hoc", "cỡ mẫu chốt đủ lực, có phương pháp"),
    "G3-AUTO-14": ("comau", "tai_lap", "tham số đã ghim đủ để chạy lại ra cùng cỡ mẫu"),
    "G3-AUTO-15": ("comau", "tai_lap", "khai công thức và phần mềm/phiên bản"),
    "G4-AUTO-03": ("sap", "trung_thuc", "số liệu SAP khớp G3 hiện tại"),
    "G4-AUTO-04": ("sap", "hop_le_tin_cay", "phân tích đa biến có EPV/VIF"),
    "G4-AUTO-05": ("sap", "khoa_hoc", "xử lý dữ liệu thiếu có nội dung thật"),
    "G4-AUTO-06": ("sap", "khach_quan", "đa so sánh định trước"),
    "G4-AUTO-07": ("sap", "khach_quan", "phân nhóm nhỏ định trước (chống HARKing)"),
    "G4-AUTO-08": ("sap", "tai_lap", "phần mềm và hạt giống cụ thể"),
    "G4-AUTO-11": ("sap", "khach_quan", "kết cục chính của SAP khớp câu hỏi đã chốt"),
    "G5-AUTO-01": ("quantri_dulieu", "tai_lap", "có DMP, từ điển dữ liệu, mã làm sạch/kiểm chất lượng"),
    "G5-AUTO-02": ("quantri_dulieu", "ton_trong", "từ điển dữ liệu không có định danh trực tiếp"),
    "G5-AUTO-03": ("quantri_dulieu", "kiem_soat_cl", "DMP phủ vòng đời dữ liệu theo ICH E6(R3)"),
    "G5-AUTO-11": ("bienso", "hop_le_tin_cay", "từ điển nhập liệu ↔ đề cương ↔ phiếu đồng bộ"),
    "G5-AUTO-12": ("bienso", "tai_lap", "từ điển dựng từ bộ biến riêng, phủ ma trận mục tiêu–biến"),
    "G5-AUTO-13": ("congcu", "trung_thuc", "phiếu trình Hội đồng Đạo đức khớp câu hỏi dùng để nhập liệu"),
}
_CONG_MUC = {"PASS": XANH, "BLOCK": DO, "BLOCKED": DO, "FAIL": DO}


def do_cong(ctx: NguCanh) -> List[KetQuaDo]:
    ra: List[KetQuaDo] = []
    theo_cong: Dict[str, List[str]] = {}
    for ma in ANH_XA_CONG:
        theo_cong.setdefault(ma.split("-", 1)[0], []).append(ma)
    for g, ds in theo_cong.items():
        if not (ctx.out_dir / f"{g}_checkpoint.json").is_file():
            for ma in ds:
                p, nt, ly = ANH_XA_CONG[ma]
                ra.append(_kq(ma, f"Tiêu chí {ma}", p, nt, CHUA_DO, ly, [f"cổng {g} chưa chạy (chưa có checkpoint)"]))
            continue
        s = ctx.cong(g)
        bc = s.get("bao_cao") if isinstance(s, dict) else None
        tieu_chi = {c.get("id"): c for c in ((bc or {}).get("automatic_criteria") or []) if isinstance(c, dict)}
        for ma in ds:
            p, nt, ly = ANH_XA_CONG[ma]
            if isinstance(s, Exception) or not bc:
                why = (s.get("ly_do") if isinstance(s, dict) else type(s).__name__)
                ra.append(_kq(ma, f"Tiêu chí {ma}", p, nt, CHUA_DO, ly, [f"cổng {g} không chấm sống được: {why}"]))
                continue
            c = tieu_chi.get(ma)
            if c is None:
                ra.append(_kq(ma, f"Tiêu chí {ma}", p, nt, CHUA_DO, ly, [f"bộ chấm {g} không trả tiêu chí này"]))
                continue
            st = str(c.get("status") or "").upper()
            ra.append(_kq(ma, f"{ma} — {str(c.get('label') or '')[:110]}", p, nt, _CONG_MUC.get(st, CHUA_DO), ly,
                          [f"{st}: {str(c.get('evidence') or '')[:240]}"]))
    return ra


# ═════════════════════════════════ E. BỘ ĐỐI CHIẾU RIÊNG ═════════════════════════════════
def do_doi_chieu(ctx: NguCanh) -> List[KetQuaDo]:
    ra: List[KetQuaDo] = []

    # E1 — biện pháp kiểm soát sai lệch G1 ↔ phân tích SAP
    def e1() -> KetQuaDo:
        import doi_chieu_sai_lech_sap as DSL  # noqa: PLC0415

        ly = "biện pháp khống chế sai lệch đã hứa có phân tích tương ứng trong SAP"
        k = DSL.kiem(ctx.out_dir, ctx.study)
        tt = k.get("trang_thai")
        if tt == DSL.TRANG_THAI_KHONG_CO and k.get("khong_ap_dung"):
            return _kq("DC-SAI-LECH", "Sai lệch G1 ↔ SAP", "sailech", "khach_quan", KAD, ly, [k.get("tom_tat")])
        st = {DSL.TRANG_THAI_DAT: XANH, DSL.TRANG_THAI_CHUA_DAT: DO}.get(tt, CHUA_DO)
        chi = [str(k.get("tom_tat"))] + [f"{x.get('ma')}: {x.get('noi_dung')}" for x in k.get("loi") or []][:6]
        return _kq("DC-SAI-LECH", "Sai lệch G1 ↔ SAP (doi_chieu_sai_lech_sap)", "sailech", "khach_quan", st, ly, chi)

    # E2 — bảng biến của đề cương/bộ biến đã duyệt ↔ bản máy
    def e2() -> KetQuaDo:
        import doi_chieu_bien_de_cuong as DBC  # noqa: PLC0415

        ly = "biến đo đúng như đề cương đã duyệt (mã giá trị, loại biến, biến phái sinh)"
        k = DBC.doi_chieu(ctx.out_dir, ctx.study)
        st = {"DONG_BO": XANH, "LECH": DO}.get(k.trang_thai, CHUA_DO)
        chi = [f"{k.trang_thai}: {k.so_lech} lệch, {len(k.phat_hien) - k.so_lech} cần xem"]
        if k.khong_do_duoc:
            chi.append(str(k.khong_do_duoc))
        chi += [f"{p.luat} {p.bien}: {p.chi_tiet}" for p in k.phat_hien if p.muc == "LECH"][:6]
        return _kq("DC-BIEN", "Biến ↔ đề cương (doi_chieu_bien_de_cuong)", "bienso", "hop_le_tin_cay", st, ly, chi)

    # E3 — ma trận mục tiêu → biến → câu hỏi → phân tích
    def e3() -> KetQuaDo:
        import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415

        ly = "mỗi yếu tố của mục tiêu có biến, câu hỏi và phân tích tương ứng"
        k = MT.kiem(ctx.out_dir, ctx.study)
        st = {MT.TRANG_THAI_DAT: XANH, MT.TRANG_THAI_CHUA_DAT: DO}.get(k.get("trang_thai"), CHUA_DO)
        chi = [f"{k.get('trang_thai')}: {k.get('tom_tat')}"]
        chi += [f"{x.get('ma')}: {x.get('noi_dung')}" for x in k.get("loi") or []][:6]
        return _kq("DC-MA-TRAN", "Ma trận mục tiêu–biến (ma_tran_muc_tieu_bien)", "muctieu", "khoa_hoc", st, ly, chi)

    # E4 — công thức biến phái sinh: hợp lệ và đã duyệt gắn dấu công thức
    def e4() -> KetQuaDo:
        import bien_phai_sinh as BPS  # noqa: PLC0415

        ly = "biến phái sinh tính tất định theo công thức đã được thống kê viên/PI duyệt đúng dấu"
        ma, ten = "DC-PHAI-SINH", "Công thức biến phái sinh (bien_phai_sinh kiem)"
        if not (ctx.out_dir / BPS.TEP_DAC_TA).is_file():
            return _kq(ma, ten, "bienso", "tai_lap", CHUA_DO, ly, [f"chưa có {BPS.TEP_DAC_TA}"])
        bien = BPS.doc_dac_ta(ctx.out_dir)
        kq = BPS.kiem_dac_ta(bien, BPS.doc_danh_muc_tu_dien(ctx.out_dir, ctx.study))
        dem: Dict[str, int] = {}
        for b in bien:
            dem[kq.trang_thai[b.ten]] = dem.get(kq.trang_thai[b.ten], 0) + 1
        hong = sorted({b.goc for b in bien if kq.trang_thai[b.ten] in ("HET_HIEU_LUC", "SAI_DANG")})
        chi = ["trạng thái: " + ", ".join(f"{k} {n}" for k, n in sorted(dem.items()))]
        if kq.loi:
            return _kq(ma, ten, "bienso", "tai_lap", DO, ly,
                       chi + [f"{k}: {v}" for k, v in list(kq.loi.items())[:6]])
        if hong:
            return _kq(ma, ten, "bienso", "tai_lap", DO, ly,
                       chi + ["công thức đổi sau khi duyệt hoặc dòng duyệt sai dạng: " + ", ".join(hong[:8])])
        if dem and set(dem) <= {"DA_DUYET", "NGOAI_TANG"}:
            return _kq(ma, ten, "bienso", "tai_lap", XANH, ly, chi)
        return _kq(ma, ten, "bienso", "tai_lap", CHUA_DO, ly, chi + ["còn công thức chưa có dòng duyệt"])

    for ham in (e1, e2, e3, e4):
        try:
            ra.append(ham())
        except Exception as e:  # noqa: BLE001
            ten = getattr(ham, "__name__", "?")
            ra.append(_kq("DC-" + ten.upper(), "Bộ đối chiếu " + ten, {"e1": "sailech", "e2": "bienso", "e3": "muctieu",
                                                                      "e4": "bienso"}[ten],
                          {"e1": "khach_quan", "e2": "hop_le_tin_cay", "e3": "khoa_hoc", "e4": "tai_lap"}[ten],
                          CHUA_DO, "bộ đối chiếu hỏng", [f"{type(e).__name__}: {str(e)[:160]}"]))
    return ra


# E5 — tư vấn số liệu ↔ toàn văn (không đọc EndNote: phép đo tất định trên tệp của đề tài)
def do_so_lieu_toan_van(ctx: NguCanh) -> List[KetQuaDo]:
    ma, ten = "DC-SO-LIEU-TOAN-VAN", "Con số có trích dẫn thấy trong toàn văn nguồn (kiem_so_lieu_toan_van)"
    ly = "con số dẫn phải có trong chính tài liệu được dẫn"
    if ctx.md is None:
        return []
    try:
        import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415
        import kiem_so_lieu_toan_van as KSL  # noqa: PLC0415

        van = KSL.khoang_van_ban(ctx.md, "ĐẶT VẤN ĐỀ", "ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP")
        if van is None:
            return [_kq(ma, ten, "tongquan", "trung_thuc", CHUA_DO, ly, ["không thấy khoảng Đặt vấn đề → Phương pháp"])]
        _, muc = KDN._tach_tltk(ctx.md)
        khoa = {so: KSL._khoa_muc(nd, so) for so, nd in muc.items()}
        da_doc: Dict[int, str] = {}

        def lay(so: int) -> str:
            if so not in da_doc:
                da_doc[so] = KSL.van_toan_van(ctx.out_dir, khoa[so], None)
            return da_doc[so]

        ket = KSL.doi_chieu(van, muc, lay)
    except Exception as e:  # noqa: BLE001
        return [_kq(ma, ten, "tongquan", "trung_thuc", CHUA_DO, ly, [f"bộ đối chiếu hỏng: {type(e).__name__}"])]
    co_van = [so for so, v in da_doc.items() if v.strip()]
    khong_thay = [v for v in ket if v.khong_thay and not v.thieu_toan_van]
    chua = [v for v in ket if v.thieu_toan_van]
    chi = [f"{len(co_van)}/{len(da_doc)} tài liệu được dẫn có toàn văn trên máy; {len(khong_thay)} vế có con số chưa "
           f"thấy; {len(chua)} vế chưa đối chiếu được"]
    chi += [f"[{', '.join(map(str, v.tai_lieu))}] chưa thấy {v.khong_thay}: {v.trich[:120]}" for v in khong_thay[:5]]
    # Tư vấn có giới hạn đã biết (số viết bằng chữ, số ngắn trùng ngẫu nhiên) ⇒ «chưa thấy» là ⚪ phải đọc đối chiếu,
    # không phải 🔴; chỉ xanh khi mọi vế mang số đều đối chiếu được và thấy đủ.
    if da_doc and co_van and not khong_thay and not chua:
        return [_kq(ma, ten, "tongquan", "trung_thuc", XANH, ly, chi)]
    return [_kq(ma, ten, "tongquan", "trung_thuc", CHUA_DO, ly, chi)]


# ═════════════════════════════════ F. PHÂN XỬ HỘI ĐỒNG KHOA HỌC (biên bản còn hiệu lực) ═════════════════════════════
# Ô cần phán đoán của người (ý nghĩa khoa học, tính hợp lý của phương pháp) đọc biên bản Hội đồng Khoa học máy
# (`tools/hoi_dong_khoa_hoc.py`) — chỉ biên bản có SHA-256 trùng ĐÚNG bản đề cương hiện tại. Mục phiếu nhận xét:
ANH_XA_HDKH: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "1": (("datvande", "khoa_hoc"), ("tongquan", "khoa_hoc")),
    "2": (("muctieu", "khoa_hoc"), ("thietke", "khoa_hoc"), ("sap", "khoa_hoc")),
    "3": (("dukien_ketqua", "khoa_hoc"),),
    "4": (("tltk", "trung_thuc"),),
}
_TEN_MUC_PHIEU = {"1": "tính cấp thiết, ý nghĩa khoa học và thực tiễn", "2": "mục tiêu và phương pháp",
                  "3": "dự kiến kết quả", "4": "chất lượng văn bản, tài liệu trích dẫn"}


def bien_ban_hdkh_hieu_luc(out_dir: Path, md: str) -> Optional[Dict[str, Any]]:
    """Biên bản Hội đồng Khoa học máy (json) MỚI NHẤT có SHA trùng bản đề cương hiện tại; không có ⇒ None."""
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    ds = sorted((Path(out_dir) / "hoi_dong_khoa_hoc").glob("BIEN_BAN_HDKH_*.json"))
    for p in reversed(ds):
        bb = _doc_json(p)
        if bb.get("sha") == sha and isinstance(bb.get("tong_hop"), dict):
            bb["_tep"] = p.name
            return bb
    return None


def do_hoi_dong(ctx: NguCanh) -> List[KetQuaDo]:
    if ctx.md is None:
        return []
    bb = bien_ban_hdkh_hieu_luc(ctx.out_dir, ctx.md)
    ra: List[KetQuaDo] = []
    for muc, cac_o in ANH_XA_HDKH.items():
        ly = f"phân xử của Hội đồng Khoa học — mục phiếu {muc} ({_TEN_MUC_PHIEU[muc]})"
        for p, nt in cac_o:
            ma, ten = f"HDKH:{muc}", f"Hội đồng Khoa học — {_TEN_MUC_PHIEU[muc]}"
            if bb is None:
                ra.append(_kq(ma, ten, p, nt, CHUA_DO, ly,
                              ["chưa có biên bản Hội đồng Khoa học còn hiệu lực cho đúng bản đề cương này"]))
                continue
            th = bb["tong_hop"]
            nang = [f for f in th.get("van_de") or [] if str(f.get("muc_phieu")) == muc
                    and f.get("muc_do") in ("nghiem_trong", "can_sua")]
            nang_o = [f for f in nang if ctx.phan_cua_dong(int(f.get("dong") or 0)) in (p, None)]
            tv = (th.get("trung_vi") or {}).get(muc)
            if nang_o:
                ra.append(_kq(ma, ten, p, nt, DO, ly, [f"{bb['_tep']}: dòng {f.get('dong')} — {f.get('van_de')}"
                                                       for f in nang_o[:5]]))
            elif isinstance(tv, (int, float)) and tv >= 4:
                ra.append(_kq(ma, ten, p, nt, XANH, ly, [f"{bb['_tep']}: trung vị mục {muc} = {tv}"]))
            else:
                ra.append(_kq(ma, ten, p, nt, CHUA_DO, ly, [f"{bb['_tep']}: trung vị mục {muc} = {tv}; "
                                                             f"{len(nang)} vấn đề ở phần khác"]))
    return ra


# ═════════════════════════════════ G. PHÉP ĐO MỚI (TN-…) từ dữ kiện máy đọc ═════════════════════════════════
_RUT_LUI_RE = re.compile(r"rút (khỏi|lui|lại|tên|phiếu)|ngừng tham gia|dừng (tham gia|lại|bất cứ)|"
                         r"từ chối (tham gia|trả lời)|không (đồng ý )?tham gia (nữa|tiếp)|"
                         r"bất cứ (lúc|thời điểm) nào", re.IGNORECASE)
_KHONG_ANH_HUONG_RE = re.compile(r"không (bị )?ảnh hưởng|không (làm )?thay đổi (việc|quyền|chất lượng)|quyền lợi",
                                 re.IGNORECASE)
_DOC_LAP_RE = re.compile(r"độc lập|ngoài (khoa|nhóm)|không thuộc (khoa|nhóm)|không kiêm nhiệm|người thứ (hai|ba)",
                         re.IGNORECASE)
_TU_TUC_RE = re.compile(r"tự túc|không có (nhà |đơn vị )?tài trợ|không nhận tài trợ|kinh phí (của )?(bệnh viện|đơn vị|"
                        r"đề tài cấp|chủ nhiệm)|nguồn kinh phí", re.IGNORECASE)
_TAI_TRO_RE = re.compile(r"tài trợ|nhà tài trợ|sponsor", re.IGNORECASE)
_XUNG_DOT_RE = re.compile(r"xung đột lợi ích", re.IGNORECASE)
_TRICH_TAY_RE = re.compile(r"phiếu trích xuất|BỆNH ÁN NGHIÊN CỨU|trích (xuất|lục) (số liệu |dữ liệu )?(từ )?(hồ sơ|"
                           r"bệnh án)|hồi cứu (hồ sơ|bệnh án)|đọc hồ sơ bệnh án", re.IGNORECASE)
_TRICH_LAI_RE = re.compile(r"trích (lại|xuất lại|độc lập)|người (trích|nhập|đánh giá) thứ hai|hai người (trích|đọc|"
                           r"đánh giá|sàng lọc)|độc lập", re.IGNORECASE)
_DONG_THUAN_HS_RE = re.compile(r"kappa|κ|\bICC\b|tương quan nội lớp|tỷ lệ (đồng thuận|khớp|trùng khớp)|% (đồng "
                               r"thuận|khớp)", re.IGNORECASE)
_RR_TRUONG_BIEN_PHAP = ("giam_thieu", "capa", "chu_nhan")
_RR_TRUONG_DANH_GIA = ("xac_suat", "tac_dong")


def _mien_dong_thuan_trong(van: str) -> bool:
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    return KCM.co_dieu_kien(KCM.MIEN_DONG_THUAN, van)


def _can_thiep(ctx: NguCanh) -> bool:
    import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

    return ctx.thiet_ke in NQ.THIET_KE_CAN_THIEP


def tn_ton_01(ctx: NguCanh) -> KetQuaDo:
    """Căn cứ đồng thuận của đề cương khớp quyết định đã khai ở G2 (icf_waiver_requested)."""
    ma, ten, p, nt = "TN-TON-01", "Đồng thuận/miễn đồng thuận của đề cương khớp hồ sơ G2", "daoduc", "ton_trong"
    ly = "đề cương và hồ sơ G2 phải nói cùng một con đường đồng thuận (CIOMS 2016 HD 10; TT43/2024 Điều 7.1b)"
    if not ctx.co_nguoi_tham_gia():
        return _kq(ma, ten, p, nt, KAD, ly, ["thiết kế không có người tham gia"])
    mien = ctx.gp.get("G2", {}).get("icf_waiver_requested")
    if not isinstance(mien, bool):
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["G2 chưa khai icf_waiver_requested (đúng/sai)"])
    van = ctx.van_phan("daoduc")
    if not van.strip():
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["đề cương không có phần đạo đức để đối chiếu"])
    co_mien = _mien_dong_thuan_trong(van)
    if mien and not co_mien:
        return _kq(ma, ten, p, nt, DO, ly, ["G2 xin miễn đồng thuận nhưng phần đạo đức của đề cương không nêu miễn"])
    if not mien and co_mien:
        return _kq(ma, ten, p, nt, DO, ly, ["G2 không xin miễn nhưng phần đạo đức của đề cương nêu miễn đồng thuận"])
    if not mien and not re.search(r"phiếu (đồng ý|tình nguyện|chấp thuận)|bản thông tin", van, re.IGNORECASE):
        return _kq(ma, ten, p, nt, DO, ly, ["G2 lấy đồng thuận nhưng phần đạo đức không có bản thông tin/phiếu đồng ý"])
    return _kq(ma, ten, p, nt, XANH, ly, ["miễn đồng thuận" if mien else "có bản thông tin và phiếu đồng ý"])


def tn_ton_02(ctx: NguCanh) -> KetQuaDo:
    """Người tham gia được biết quyền từ chối/rút lui mà không ảnh hưởng chăm sóc (Helsinki §26)."""
    ma, ten, p, nt = "TN-TON-02", "Quyền từ chối/rút lui không ảnh hưởng chăm sóc", "daoduc", "ton_trong"
    ly = "người tham gia phải được biết quyền từ chối hoặc rút lui bất cứ lúc nào không bị ảnh hưởng (Helsinki §26)"
    if not ctx.co_nguoi_tham_gia():
        return _kq(ma, ten, p, nt, KAD, ly, ["thiết kế không có người tham gia"])
    mien = ctx.gp.get("G2", {}).get("icf_waiver_requested")
    if mien is True:
        return _kq(ma, ten, p, nt, KAD, ly, ["miễn đồng thuận — không tiếp xúc người tham gia"])
    if mien is not False:
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["G2 chưa khai icf_waiver_requested"])
    van = ctx.van_phan("daoduc")
    thieu = [t for t, rx in (("quyền từ chối/rút lui", _RUT_LUI_RE), ("không ảnh hưởng quyền lợi/chăm sóc",
                                                                       _KHONG_ANH_HUONG_RE)) if not rx.search(van)]
    if thieu:
        return _kq(ma, ten, p, nt, DO, ly, ["phần đạo đức/phiếu đồng ý thiếu: " + "; ".join(thieu)])
    return _kq(ma, ten, p, nt, XANH, ly, ["có quyền từ chối/rút lui và cam kết không ảnh hưởng"])


def tn_ton_03(ctx: NguCanh) -> KetQuaDo:
    """Quản trị dữ liệu máy đọc (study_meta.data_governance) đủ bốn lớp bảo vệ dữ liệu cá nhân."""
    ma, ten, p, nt = "TN-TON-03", "Bảo vệ dữ liệu cá nhân khai trong quản trị dữ liệu", "quantri_dulieu", "ton_trong"
    ly = ("dữ liệu người tham gia được khử định danh, giới hạn truy cập, lưu an toàn, có quy trình sự cố "
          "(Helsinki §24; Luật 91/2025/QH15)")
    if not ctx.co_nguoi_tham_gia():
        return _kq(ma, ten, p, nt, KAD, ly, ["thiết kế không có người tham gia"])
    dg = ctx.meta.get("data_governance")
    if not isinstance(dg, dict) or not dg:
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["study_meta chưa có data_governance máy đọc"])
    gop = " ".join(f"{k}: {v}" for k, v in dg.items() if not _trong(v))
    lop = (("khử định danh/giả danh/mã hoá", r"khử định danh|ẩn danh|nặc danh|khuyết danh|giả danh|mã (hoá|hóa)|mã "
                                              r"(số )?nghiên cứu|deidentif"),
           ("giới hạn truy cập", r"truy cập|phân quyền|mật khẩu|access"),
           ("nơi lưu trữ/sao lưu", r"lưu (trữ|tại)|máy chủ|ổ đĩa|sao lưu|backup|storage"),
           ("xử lý sự cố lộ dữ liệu", r"sự cố|vi phạm|breach|lộ (thông tin|dữ liệu)"))
    thieu = [t for t, rx in lop if not re.search(rx, gop, re.IGNORECASE)]
    oc = [k for k, v in dg.items() if isinstance(v, str) and _PLACEHOLDER.search(v)]
    if thieu or oc:
        chi = (["thiếu lớp: " + "; ".join(thieu)] if thieu else []) + ([f"ô [CẦN…]: {', '.join(oc)}"] if oc else [])
        return _kq(ma, ten, p, nt, DO, ly, chi)
    return _kq(ma, ten, p, nt, XANH, ly, [f"đủ 4 lớp ({len(dg)} trường)"])


def tn_dd_01(ctx: NguCanh) -> KetQuaDo:
    """Cân nhắc nguy cơ–gánh nặng–lợi ích đã khai (Helsinki §16–18)."""
    ma, ten, p, nt = "TN-DD-01", "Đánh giá nguy cơ–gánh nặng–lợi ích", "daoduc", "dao_duc"
    ly = "nguy cơ và gánh nặng phải được đánh giá, giảm thiểu và cân với lợi ích (Helsinki §16–18)"
    g1 = ctx.gp.get("G1", {})
    if "benefit_risk_rationale" not in g1:
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["G1 chưa có trường benefit_risk_rationale"])
    if _trong(g1.get("benefit_risk_rationale")):
        return _kq(ma, ten, p, nt, DO, ly, ["G1.benefit_risk_rationale trống hoặc còn ô [CẦN…]"])
    return _kq(ma, ten, p, nt, XANH, ly, [str(g1["benefit_risk_rationale"])[:160]])


def tn_tt_01(ctx: NguCanh) -> List[KetQuaDo]:
    """Xung đột lợi ích: khai ở G2, quản lý khi có xung đột cơ cấu, nêu trong đề cương; quản lý bằng vai trò độc lập."""
    p = "daoduc"
    ly_tt = "đề cương phải nêu xung đột lợi ích (Helsinki §22) và hồ sơ G2 khai cùng nội dung"
    ly_kq = "xung đột cơ cấu phải được quản lý bằng vai trò độc lập với người có xung đột"
    coi = ctx.gp.get("G2", {}).get("coi")
    if coi is None:
        return [_kq("TN-TT-01", "Khai xung đột lợi ích", p, "trung_thuc", CHUA_DO, ly_tt, ["G2 chưa có khoá coi"]),
                _kq("TN-KQ-04", "Quản lý xung đột lợi ích bằng vai trò độc lập", p, "khach_quan", CHUA_DO, ly_kq,
                    ["G2 chưa có khoá coi"])]
    tom = coi.get("summary") if isinstance(coi, dict) else coi
    van = ctx.van_phan("daoduc")
    ra: List[KetQuaDo] = []
    loi_tt = []
    if _trong(tom):
        loi_tt.append("G2.coi chưa có tóm tắt (summary)")
    if not _XUNG_DOT_RE.search(van):
        loi_tt.append("phần đạo đức của đề cương không nêu xung đột lợi ích")
    ra.append(_kq("TN-TT-01", "Khai xung đột lợi ích", p, "trung_thuc", DO if loi_tt else XANH, ly_tt,
                  loi_tt or [str(tom)[:160]]))
    co_cau = coi.get("structural") if isinstance(coi, dict) else None
    if _trong(co_cau):
        ra.append(_kq("TN-KQ-04", "Quản lý xung đột lợi ích bằng vai trò độc lập", p, "khach_quan", KAD, ly_kq,
                      ["G2 không khai xung đột cơ cấu"]))
    else:
        ql = coi.get("management") if isinstance(coi, dict) else None
        loi = []
        if _trong(ql):
            loi.append("có xung đột cơ cấu nhưng G2.coi.management trống")
        elif not _DOC_LAP_RE.search(str(ql)):
            loi.append("biện pháp quản lý không giao việc cho người độc lập/ngoài đơn vị")
        if not _DOC_LAP_RE.search(van):
            loi.append("phần đạo đức của đề cương không nêu vai trò độc lập")
        ra.append(_kq("TN-KQ-04", "Quản lý xung đột lợi ích bằng vai trò độc lập", p, "khach_quan",
                      DO if loi else XANH, ly_kq, loi or [str(ql)[:160]]))
    return ra


def tn_tt_02(ctx: NguCanh) -> KetQuaDo:
    """Nguồn kinh phí khai ở G2 và nêu trong đề cương, hai bên cùng chiều."""
    ma, ten, p, nt = "TN-TT-02", "Nguồn kinh phí khai rõ và khớp G2", "tiendo", "trung_thuc"
    ly = "đề cương phải nêu nguồn kinh phí (Helsinki §22) và khớp khai báo tài trợ ở G2"
    ext = ctx.gp.get("G2", {}).get("external_funding")
    if not isinstance(ext, bool):
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["G2 chưa khai external_funding (đúng/sai)"])
    van = ctx.van_phan("tiendo", "tomtat", "daoduc")
    if ext and not _TAI_TRO_RE.search(van):
        return _kq(ma, ten, p, nt, DO, ly, ["G2 khai có tài trợ ngoài nhưng đề cương không nêu nhà tài trợ"])
    if not ext and not _TU_TUC_RE.search(van):
        return _kq(ma, ten, p, nt, DO, ly, ["G2 khai không tài trợ ngoài nhưng đề cương không nêu nguồn kinh phí"])
    return _kq(ma, ten, p, nt, XANH, ly, ["có tài trợ ngoài" if ext else "kinh phí không từ tài trợ ngoài"])


def _ngay_iso(v: Any) -> Optional[str]:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v or ""))
    return m.group(1) if m else None


def tn_kq_01(ctx: NguCanh) -> KetQuaDo:
    """SAP khoá TRƯỚC dữ liệu (ICH E9; TOP 2025 — đăng ký trước kế hoạch phân tích)."""
    ma, ten, p, nt = "TN-KQ-01", "Kế hoạch phân tích khoá trước dữ liệu", "sap", "khach_quan"
    ly = "kế hoạch phân tích được định trước và khoá trước khi có dữ liệu"
    cp4 = _doc_json(ctx.out_dir / "G4_checkpoint.json")
    ngay_sap = _ngay_iso(ctx.meta.get("sap_lock_date")) or _ngay_iso(cp4.get("g4_lock_date"))
    ngay_dl = _ngay_iso(ctx.meta.get("data_lock_date"))
    g5 = _doc_json(ctx.out_dir / "G5_QUALITY_REPORT.json")
    co_dl = bool(ngay_dl) or g5.get("real_data_present") is True
    s4 = ctx.cong("G4") if (ctx.out_dir / "G4_checkpoint.json").is_file() else None
    khoa = isinstance(s4, dict) and str(s4.get("status") or "").upper() == "PASS_G4_SAP_LOCKED"
    if co_dl:
        if not ngay_sap:
            return _kq(ma, ten, p, nt, DO, ly, ["đã có dữ liệu thật nhưng không có ngày khoá SAP"])
        if ngay_dl and ngay_sap > ngay_dl:
            return _kq(ma, ten, p, nt, DO, ly, [f"SAP khoá {ngay_sap} SAU ngày khoá dữ liệu {ngay_dl}"])
        return _kq(ma, ten, p, nt, XANH, ly, [f"SAP khoá {ngay_sap}" + (f" ≤ dữ liệu {ngay_dl}" if ngay_dl else "")])
    if khoa:
        return _kq(ma, ten, p, nt, XANH, ly, [f"SAP đã khoá (chấm sống G4){' ngày ' + ngay_sap if ngay_sap else ''}; "
                                               "chưa có dữ liệu thật"])
    st = s4.get("status") if isinstance(s4, dict) else "chưa chạy"
    return _kq(ma, ten, p, nt, CHUA_DO, ly, [f"chưa có dữ liệu; G4 chấm sống: {st} — chưa tới mốc so"])


def tn_kq_02(ctx: NguCanh) -> KetQuaDo:
    """Trích xuất thủ công (hồ sơ bệnh án, tổng quan hệ thống) có trích lại độc lập kèm hệ số đồng thuận."""
    ma, ten, p, nt = "TN-KQ-02", "Trích xuất thủ công có trích lại độc lập kèm hệ số đồng thuận", "congcu", "khach_quan"
    ly = ("dữ liệu trích tay phải được người thứ hai trích lại độc lập và báo hệ số đồng thuận (Gilbert 1996, PMID "
          "8599488); tổng quan hệ thống: hai người độc lập (PRISMA-P 11b/11c)")
    if ctx.md is None:
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["chưa có đề cương nộp"])
    sr = ctx.thiet_ke == "systematic_review"
    if not sr and not _TRICH_TAY_RE.search(ctx.md):
        return _kq(ma, ten, p, nt, KAD, ly, ["đề cương không có trích xuất thủ công từ hồ sơ/nghiên cứu"])
    van = ctx.van_phan("congcu", "quantri_dulieu", "sailech", "bienso", "doituong")
    if sr:
        # PRISMA-P 2015 mục 11b/11c: chọn nghiên cứu và trích xuất do HAI người ĐỘC LẬP — hệ số đồng thuận không
        # bắt buộc
        if _TRICH_LAI_RE.search(van):
            return _kq(ma, ten, p, nt, XANH, ly, ["chọn/trích xuất do hai người độc lập (PRISMA-P 11b/11c)"])
        return _kq(ma, ten, p, nt, DO, ly, ["tổng quan hệ thống không nêu hai người độc lập chọn/trích xuất"])
    # Trích hồ sơ bệnh án: đo độ tin cậy giữa người trích (Gilbert 1996, PMID 8599488)
    thieu = [t for t, rx in (("trích lại/đánh giá độc lập", _TRICH_LAI_RE), ("hệ số đồng thuận", _DONG_THUAN_HS_RE))
             if not rx.search(van)]
    if thieu:
        return _kq(ma, ten, p, nt, DO, ly, ["thiếu: " + "; ".join(thieu)])
    return _kq(ma, ten, p, nt, XANH, ly, ["có trích lại độc lập và hệ số đồng thuận"])


def tn_kq_03(ctx: NguCanh) -> KetQuaDo:
    """Kế hoạch giám sát giao kiểm tra cho người độc lập với người thu thập."""
    ma, ten, p, nt = "TN-KQ-03", "Giám sát/kiểm tra do người độc lập với người thu thập", "tiendo", "khach_quan"
    ly = "người kiểm tra chất lượng độc lập với người thu thập để đánh giá khách quan"
    g1 = ctx.gp.get("G1", {})
    gop = " ".join(str(g1.get(k) or "") for k in ("monitoring_plan", "team_roles"))
    # Không bao giờ ĐỎ: chuẩn không đòi chung mọi thiết kế giao kiểm tra cho người độc lập — vắng thì «chưa chứng minh».
    if _trong(g1.get("monitoring_plan")):
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["G1 chưa khai monitoring_plan"])
    if not _DOC_LAP_RE.search(gop):
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["kế hoạch giám sát/phân công chưa nêu người kiểm tra độc lập"])
    return _kq(ma, ten, p, nt, XANH, ly, ["có vai trò kiểm tra độc lập"])


def _truong_g1_cl(ctx: NguCanh, khoa: str, ma: str, ten: str, p: str, ly: str) -> KetQuaDo:
    v = ctx.gp.get("G1", {}).get(khoa)
    if _trong(v):
        if _can_thiep(ctx):
            return _kq(ma, ten, p, "kiem_soat_cl", DO, ly, [f"thiết kế can thiệp mà G1.{khoa} trống"])
        return _kq(ma, ten, p, "kiem_soat_cl", CHUA_DO, ly, [f"G1.{khoa} chưa khai (ICH E6(R3) bắt buộc với thử "
                                                              "nghiệm can thiệp; thiết kế quan sát chưa đo)"])
    return _kq(ma, ten, p, "kiem_soat_cl", XANH, ly, [str(v)[:160]])


def tn_qc_01(ctx: NguCanh) -> KetQuaDo:
    return _truong_g1_cl(ctx, "critical_to_quality", "TN-QC-01", "Yếu tố trọng yếu chất lượng đã xác định", "thietke",
                         "chất lượng theo thiết kế bắt đầu từ yếu tố trọng yếu chất lượng (ICH E6(R3))")


def tn_qc_02(ctx: NguCanh) -> KetQuaDo:
    return _truong_g1_cl(ctx, "monitoring_plan", "TN-QC-02", "Kế hoạch giám sát", "tiendo",
                         "giám sát dựa trên rủi ro theo kế hoạch định trước (ICH E6(R3))")


def tn_qc_03(ctx: NguCanh) -> List[KetQuaDo]:
    """Sổ rủi ro A13b: mỗi rủi ro có biện pháp, CAPA, người chịu trách nhiệm; và được đánh giá xác suất × tác động."""
    p, nt = "tiendo", "kiem_soat_cl"
    ly_a = "mỗi rủi ro có biện pháp phòng ngừa, hành động khắc phục (CAPA) và người chịu trách nhiệm (ICH E6(R3))"
    ly_b = "đánh giá rủi ro gồm khả năng xảy ra và tác động (ICH E6(R3) — đánh giá rủi ro)"
    rr = ctx.gp.get("G1", {}).get("risk_register")
    if not isinstance(rr, list) or not rr:
        # sổ CHƯA dựng ⇒ chưa đo được; sổ đã dựng mà còn ô trống/[CẦN…] mới là sản phẩm chưa hoàn thành (đỏ)
        why = ["G1.risk_register chưa khai (sổ rủi ro máy đọc chưa dựng)"]
        return [_kq("TN-QC-03", "Sổ rủi ro có biện pháp, CAPA, người chịu trách nhiệm", p, nt, CHUA_DO, ly_a, why),
                _kq("TN-QC-04", "Sổ rủi ro đánh giá xác suất × tác động", p, nt, CHUA_DO, ly_b, why)]
    thieu_a, thieu_b = [], []
    for r in rr:
        if not isinstance(r, dict):
            continue
        a = [k for k in _RR_TRUONG_BIEN_PHAP if _trong(r.get(k))]
        b = [k for k in _RR_TRUONG_DANH_GIA if _trong(r.get(k))]
        if a:
            thieu_a.append(f"{r.get('id', '?')}: {', '.join(a)}")
        if b:
            thieu_b.append(f"{r.get('id', '?')}: {', '.join(b)}")
    return [_kq("TN-QC-03", "Sổ rủi ro có biện pháp, CAPA, người chịu trách nhiệm", p, nt, DO if thieu_a else XANH,
                ly_a, thieu_a[:9] or [f"{len(rr)} rủi ro đủ biện pháp, CAPA, người chịu trách nhiệm"]),
            _kq("TN-QC-04", "Sổ rủi ro đánh giá xác suất × tác động", p, nt, DO if thieu_b else XANH, ly_b,
                (["ô trống/[CẦN…]: " + "; ".join(thieu_b[:9])] if thieu_b else [f"{len(rr)} rủi ro đã đánh giá"]))]


def tn_qc_05(ctx: NguCanh) -> KetQuaDo:
    """Luật kiểm dữ liệu (`_luat-dq.csv`) đọc được và chỉ trỏ tới biến có trong bộ biến."""
    ma, ten, p, nt = "TN-QC-05", "Luật kiểm dữ liệu trỏ đúng biến", "quantri_dulieu", "kiem_soat_cl"
    ly = "kiểm dữ liệu liên tục bằng luật range/logic định trước trên đúng biến của đề tài"
    tep = ctx.out_dir / "_luat-dq.csv"
    if not tep.is_file():
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["chưa có _luat-dq.csv (bộ luật kiểm dữ liệu dựng ở khâu dữ liệu)"])
    try:
        with open(tep, encoding="utf-8-sig", newline="") as f:
            dong = list(csv.DictReader(f))
    except (OSError, ValueError, csv.Error) as e:
        return _kq(ma, ten, p, nt, DO, ly, [f"_luat-dq.csv không đọc được: {e}"])
    import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415

    bo_bien, _ = MT.doc_bo_bien(ctx.out_dir)
    phai_sinh = MT.doc_phai_sinh(ctx.out_dir)
    if not dong:
        return _kq(ma, ten, p, nt, DO, ly, ["_luat-dq.csv không có luật nào"])
    if not bo_bien:
        return _kq(ma, ten, p, nt, CHUA_DO, ly, [f"{len(dong)} luật; chưa đọc được bộ biến để đối chiếu"])
    ten_bien = {k.casefold() for k in bo_bien} | {k.casefold() for k in phai_sinh}
    la = []
    for r in dong:
        for b in re.findall(r"\[([A-Za-z][A-Za-z0-9_]*)(?:\(\d+\))?\]", r.get("bieu_thuc_redcap") or ""):
            if b.casefold() not in ten_bien:
                la.append(f"{r.get('ma_luat')}: [{b}]")
    if la:
        return _kq(ma, ten, p, nt, DO, ly, ["luật trỏ biến không có trong bộ biến: " + "; ".join(la[:8])])
    return _kq(ma, ten, p, nt, XANH, ly, [f"{len(dong)} luật, mọi biến được trỏ có trong bộ biến"])


def tn_tl_01(ctx: NguCanh) -> KetQuaDo:
    """Lượt tìm y văn của G0 ghi đủ để lặp lại: cơ sở dữ liệu, ngày tra, truy vấn nguyên văn (PRISMA-S)."""
    ma, ten, p, nt = "TN-TL-01", "Lượt tìm y văn ghi đủ để lặp lại", "tongquan", "tai_lap"
    ly = "tổng quan tái lập được khi ghi cơ sở dữ liệu, ngày tra và truy vấn nguyên văn (PRISMA-S, PMID 34285662)"
    raw = ctx.out_dir / "G0_pubmed_raw.json"
    if not raw.is_file():
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["chưa có G0_pubmed_raw.json"])
    sp = _doc_json(raw).get("search_provenance")
    sp = sp if isinstance(sp, dict) else {}
    thieu = [t for t, k in (("cơ sở dữ liệu", "co_so_du_lieu"), ("ngày tra", "ngay_tra"), ("truy vấn", "truy_van_goc"))
             if _trong(sp.get(k))]
    if thieu:
        return _kq(ma, ten, p, nt, DO, ly, ["search_provenance thiếu: " + ", ".join(thieu)])
    return _kq(ma, ten, p, nt, XANH, ly, [f"{sp.get('co_so_du_lieu')} · {str(sp.get('ngay_tra'))[:10]}"])


# Hai nhóm dễ tổn thương có biện pháp bảo vệ KHÁC nhau: (a) thiếu năng lực đồng ý (trẻ em, suy giảm nhận thức) cần
# người đại diện hợp pháp và sự ưng thuận (Helsinki §29–30); (b) phụ nữ mang thai, người bị giam giữ cần nêu nguy cơ với
# chính nhóm đó (nghiên cứu nguy cơ tối thiểu/không can thiệp) — đòi «người đại diện» cho thai phụ là đỏ giả.
_THIEU_NANG_LUC_RE = re.compile(r"trẻ em|dưới 18 tuổi|<\s*18 tuổi|vị thành niên|suy giảm (nhận thức|trí nhớ)|"
                                r"sa sút trí tuệ|không đủ năng lực", re.IGNORECASE)
_NHOM_KHAC_RE = re.compile(r"phụ nữ (có thai|mang thai)|thai phụ|tù nhân|người bị giam giữ", re.IGNORECASE)
_TU_18_RE = re.compile(r"(≥|từ|trên|đủ)\s*18\s*tuổi|18 tuổi trở lên", re.IGNORECASE)
_BAO_VE_NANG_LUC_RE = re.compile(r"người giám hộ|đại diện hợp pháp|người đại diện|ưng thuận", re.IGNORECASE)
_BAO_VE_NHOM_KHAC_RE = re.compile(r"nguy cơ tối thiểu|không (có )?nguy cơ (cho|với|đến) (thai|thai nhi)|"
                                  r"không can thiệp|bảo vệ (đặc biệt|bổ sung)", re.IGNORECASE)


def tn_dd_02(ctx: NguCanh) -> KetQuaDo:
    """Nhóm dễ tổn thương: không đưa vào, hoặc đưa vào thì có biện pháp bảo vệ đúng loại (Helsinki §19–20, §29–30)."""
    ma, ten, p, nt = "TN-DD-02", "Nhóm dễ tổn thương được loại hoặc được bảo vệ", "doituong", "dao_duc"
    ly = "nhóm dễ tổn thương chỉ được đưa vào khi có biện pháp bảo vệ đúng loại (Helsinki §19–20, §29–30)"
    if not ctx.co_nguoi_tham_gia():
        return _kq(ma, ten, p, nt, KAD, ly, ["thiết kế không có người tham gia"])
    tieu_de = ctx.tieu_de_dong
    chon, loai = [], []
    for so, (d, k) in enumerate(zip((ctx.md or "").split("\n"), ctx.phan_dong), 1):
        if k != "doituong" or not isinstance(tieu_de, list):
            continue
        td = tieu_de[so - 1] or ""
        if re.search(r"loại", td, re.IGNORECASE):
            loai.append(d)
        elif re.search(r"chọn", td, re.IGNORECASE):
            chon.append(d)
    dao_duc = ctx.van_phan("daoduc")
    chi: List[str] = []
    for rx, bao_ve, nhom in ((_THIEU_NANG_LUC_RE, _BAO_VE_NANG_LUC_RE, "thiếu năng lực đồng ý"),
                             (_NHOM_KHAC_RE, _BAO_VE_NHOM_KHAC_RE, "thai phụ/người bị giam giữ")):
        co = [d for d in chon if rx.search(d) and not re.search(r"\b(không|loại)\b", d, re.IGNORECASE)]
        if not co:
            continue
        if not bao_ve.search(dao_duc):
            return _kq(ma, ten, p, nt, DO, ly, [f"tiêu chuẩn chọn có nhóm {nhom} nhưng phần đạo đức không nêu biện "
                                                 f"pháp bảo vệ tương ứng: {co[0].strip()[:120]}"])
        chi.append(f"có nhóm {nhom}, phần đạo đức nêu biện pháp bảo vệ tương ứng")
    if chi:
        return _kq(ma, ten, p, nt, XANH, ly, chi)
    if any(_TU_18_RE.search(d) for d in chon) or any(_THIEU_NANG_LUC_RE.search(d) or _NHOM_KHAC_RE.search(d)
                                                     for d in loai):
        return _kq(ma, ten, p, nt, XANH, ly, ["không đưa nhóm dễ tổn thương vào (tuổi ≥ 18 hoặc loại trừ rõ)"])
    return _kq(ma, ten, p, nt, CHUA_DO, ly, ["không xác định được tiêu chuẩn chọn/loại về nhóm dễ tổn thương"])


_DINH_DANH_TRUC_TIEP_RE = re.compile(r"(?:Họ (?:và )?tên|Số điện thoại|Điện thoại|Địa chỉ(?: nhà| liên hệ)?|Số CCCD|"
                                     r"CCCD|CMND|Căn cước|Số thẻ BHYT|Email)\s*(?:người bệnh|bệnh nhân|người tham gia)?"
                                     r"\s*(?::|…|\.{3,}|\|)", re.IGNORECASE)
_TACH_DINH_DANH_RE = re.compile(r"bảng (nối|ghép) mã|lưu riêng|tách riêng|tách biệt|giả danh", re.IGNORECASE)


def tn_ton_05(ctx: NguCanh) -> KetQuaDo:
    """Công cụ thu thập không có ô định danh trực tiếp, hoặc định danh được tách riêng khỏi dữ liệu nghiên cứu."""
    ma, ten, p, nt = "TN-TON-05", "Phiếu thu thập không gắn định danh trực tiếp", "congcu", "ton_trong"
    ly = ("chỉ thu dữ liệu cần thiết; định danh trực tiếp (nếu cần) tách khỏi dữ liệu nghiên cứu (Helsinki §24; "
          "Luật 91/2025/QH15)")
    if not ctx.co_nguoi_tham_gia():
        return _kq(ma, ten, p, nt, KAD, ly, ["thiết kế không có người tham gia"])
    van = ctx.van_phan("congcu")
    if not van.strip():
        return _kq(ma, ten, p, nt, CHUA_DO, ly, ["đề cương không có phần công cụ/phiếu để đối chiếu"])
    o = [d.strip()[:100] for d in van.split("\n") if _DINH_DANH_TRUC_TIEP_RE.search(d)
         and not re.search(r"không (ghi|thu|có ô|chứa|hỏi)", d, re.IGNORECASE)]
    if not o:
        return _kq(ma, ten, p, nt, XANH, ly, ["công cụ không có ô định danh trực tiếp"])
    if _TACH_DINH_DANH_RE.search(ctx.van_phan("quantri_dulieu", "daoduc")):
        return _kq(ma, ten, p, nt, XANH, ly, [f"{len(o)} ô định danh, có tách/giả danh hoá ở quản trị dữ liệu"])
    return _kq(ma, ten, p, nt, DO, ly, [f"ô định danh trực tiếp mà không nêu tách riêng: {o[0]}"])


def _co_mau(ctx: NguCanh, ma: str, ten: str, p: str, ly: str, rx: "re.Pattern[str]", phan: Tuple[str, ...],
            them: str = "") -> KetQuaDo:
    """Phép đo CÓ MẶT (xanh hoặc ⚪): vắng không phải lỗi theo mọi chuẩn, nhưng chưa chứng minh được."""
    van = ctx.van_phan(*phan) + ("\n" + them if them else "")
    m = rx.search(van)
    if m:
        return _kq(ma, ten, p, "kiem_soat_cl", XANH, ly, [f"có: «{m.group(0)}»"])
    return _kq(ma, ten, p, "kiem_soat_cl", CHUA_DO, ly, ["đề cương chưa nêu — chưa chứng minh được"])


def tn_qc_06(ctx: NguCanh) -> KetQuaDo:
    return _co_mau(ctx, "TN-QC-06", "Thử nghiệm trước công cụ/quy trình (pilot, chạy thử)", "congcu",
                   "công cụ và quy trình được thử trước khi thu thập chính thức để phát hiện lỗi sớm",
                   re.compile(r"thử nghiệm (trước|bộ câu hỏi|phiếu|công cụ)|chạy thử|pilot|tiền kiểm|"
                              r"thử (phiếu|công cụ)|dry-run|thử trích", re.IGNORECASE),
                   ("congcu", "thietke", "quantri_dulieu"), str(ctx.meta.get("pilot") or ""))


def tn_qc_07(ctx: NguCanh) -> KetQuaDo:
    return _co_mau(ctx, "TN-QC-07", "Nhật ký tuyển/chọn mẫu và tỷ lệ đáp ứng được theo dõi", "doituong",
                   "theo dõi tuân thủ chọn mẫu và tỷ lệ đáp ứng trong khi thu thập để sửa kịp",
                   re.compile(r"nhật ký (từ chối|chọn mẫu|sàng lọc|tuyển)|sổ (theo dõi|nhật ký) (tuyển|chọn|sàng lọc)|"
                              r"sơ đồ (chọn mẫu|luồng|tuyển|chọn hồ sơ|PRISMA)|tỷ lệ (đáp ứng|tham gia|từ chối)",
                              re.IGNORECASE),
                   ("doituong", "congcu", "dukien_ketqua", "sailech"))


def tn_qc_08(ctx: NguCanh) -> KetQuaDo:
    return _co_mau(ctx, "TN-QC-08", "Kiểm tra chéo kết quả phân tích", "sap",
                   "kết quả phân tích được kiểm tra chéo (phân tích lại độc lập/hai phần mềm) trước khi báo cáo",
                   re.compile(r"kiểm tra chéo|phân tích lại độc lập|hai phần mềm|đối chiếu kết quả giữa|"
                              r"chạy lại độc lập", re.IGNORECASE),
                   ("sap",))


PHEP_DO_MOI: Tuple[Tuple[str, Callable[[NguCanh], Any]], ...] = (
    ("TN-TON-01", tn_ton_01), ("TN-TON-02", tn_ton_02), ("TN-TON-03", tn_ton_03), ("TN-DD-01", tn_dd_01),
    ("TN-TT-01", tn_tt_01), ("TN-TT-02", tn_tt_02), ("TN-KQ-01", tn_kq_01), ("TN-KQ-02", tn_kq_02),
    ("TN-KQ-03", tn_kq_03), ("TN-QC-01", tn_qc_01), ("TN-QC-02", tn_qc_02), ("TN-QC-03", tn_qc_03),
    ("TN-QC-05", tn_qc_05), ("TN-TL-01", tn_tl_01), ("TN-DD-02", tn_dd_02), ("TN-TON-05", tn_ton_05),
    ("TN-QC-06", tn_qc_06), ("TN-QC-07", tn_qc_07), ("TN-QC-08", tn_qc_08),
)
# Vị trí tĩnh của phép đo mới (để in bảng ánh xạ và báo khi một phép đo hỏng).
VI_TRI_PHEP_DO_MOI: Dict[str, Tuple[str, str]] = {
    "TN-TON-01": ("daoduc", "ton_trong"), "TN-TON-02": ("daoduc", "ton_trong"),
    "TN-TON-03": ("quantri_dulieu", "ton_trong"), "TN-DD-01": ("daoduc", "dao_duc"),
    "TN-TT-01": ("daoduc", "trung_thuc"), "TN-KQ-04": ("daoduc", "khach_quan"), "TN-TT-02": ("tiendo", "trung_thuc"),
    "TN-KQ-01": ("sap", "khach_quan"), "TN-KQ-02": ("congcu", "khach_quan"), "TN-KQ-03": ("tiendo", "khach_quan"),
    "TN-QC-01": ("thietke", "kiem_soat_cl"), "TN-QC-02": ("tiendo", "kiem_soat_cl"),
    "TN-QC-03": ("tiendo", "kiem_soat_cl"), "TN-QC-04": ("tiendo", "kiem_soat_cl"),
    "TN-QC-05": ("quantri_dulieu", "kiem_soat_cl"), "TN-TL-01": ("tongquan", "tai_lap"),
    "TN-DD-02": ("doituong", "dao_duc"), "TN-TON-05": ("congcu", "ton_trong"),
    "TN-QC-06": ("congcu", "kiem_soat_cl"), "TN-QC-07": ("doituong", "kiem_soat_cl"),
    "TN-QC-08": ("sap", "kiem_soat_cl"),
}


def do_phep_do_moi(ctx: NguCanh) -> List[KetQuaDo]:
    ra: List[KetQuaDo] = []
    for ma, ham in PHEP_DO_MOI:
        try:
            k = ham(ctx)
        except Exception as e:  # noqa: BLE001
            p, nt = VI_TRI_PHEP_DO_MOI[ma]
            k = _kq(ma, ma, p, nt, CHUA_DO, "phép đo hỏng", [f"{type(e).__name__}: {str(e)[:160]}"])
        ra += k if isinstance(k, list) else [k]
    return ra


# ═════════════════════════════════ TRỤC TỔNG 5 TIÊU CHÍ (đứng trên ma trận) ═════════════════════════════════
# Bác sĩ 22/11/2026: «Một đề cương nghiên cứu y khoa tốt phải trả lời được một câu hỏi có giá trị bằng phương pháp khoa
# học phù hợp, khả thi về triển khai, tuân thủ đạo đức và tạo ra kết quả có thể kiểm chứng.» Mỗi tiêu chí là phép đo
# TỔNG HỢP: chọn các phép đo của ma trận (bộ lọc có lý do) + chốt hệ đã có ngoài ma trận (FINER G0, cổng chấm sống,
# xác nhận khả năng tuyển G3, đủ kế hoạch triển khai A13). Luật gộp như ô: có thành phần đỏ ⇒ 🔴; mọi thành phần xanh ⇒
# 🟢; còn lại ⇒ ⚪. Trục tổng chỉ BÁO (in đầu báo cáo K20); chặn vẫn theo ô ma trận để không nhân đôi lỗi.
def _co_ma(*ma: str) -> Callable[[KetQuaDo], bool]:
    return lambda k: k.ma in ma


def _tien_to(*tt: str) -> Callable[[KetQuaDo], bool]:
    return lambda k: k.ma.startswith(tt)


TRUC_TONG: Tuple[Tuple[str, str, str, Tuple[Tuple[str, Callable[[KetQuaDo], bool]], ...]], ...] = (
    ("gia_tri", "Câu hỏi có giá trị", "câu hỏi đáng trả lời: khoảng trống có nguồn, nền y văn truy được, FINER",
     (("khoảng trống nghiên cứu có mặt và nhất quán", _co_ma("NQ:tong_quan_khoang_trong")),
      ("nền bằng chứng là PMID thật, số kết quả tìm thật, đã tra sổ đăng ký", _co_ma("G0-AUTO-02", "G0-AUTO-03",
                                                                                   "G0-AUTO-06")),
      ("lượt tìm y văn tái lập được", _co_ma("TN-TL-01")),
      ("số liệu nền có trích dẫn", lambda k: k.ma == "K10" and k.phan in ("datvande", "tongquan")),
      ("mục chuẩn của đặt vấn đề/tổng quan", lambda k: k.ma.startswith("K17:") and k.phan in ("datvande", "tongquan")),
      ("Hội đồng Khoa học — tính cấp thiết, ý nghĩa", _tien_to("HDKH:1")))),
    ("phuong_phap", "Phương pháp khoa học phù hợp", "thiết kế, cỡ mẫu, biến, phân tích hợp câu hỏi và nhất quán",
     (("mọi mục chuẩn báo cáo theo thiết kế (K17)", _tien_to("K17:")),
      ("nhất quán xuyên cổng", _tien_to("NQ:")),
      ("tiêu chí G1/G3/G4 về thiết kế, cỡ mẫu, SAP", _tien_to("G1-AUTO-", "G3-AUTO-", "G4-AUTO-")),
      ("sai lệch ↔ SAP, ma trận mục tiêu–biến, biến ↔ đề cương", _co_ma("DC-SAI-LECH", "DC-MA-TRAN", "DC-BIEN")),
      ("Hội đồng Khoa học — mục tiêu và phương pháp", _tien_to("HDKH:2")))),
    ("kha_thi", "Khả thi về triển khai", "đủ người, thời gian, kế hoạch, rủi ro được quản lý, công cụ đã thử",
     (("có chương kế hoạch thực hiện", lambda k: k.ma == "K3" and k.phan == "tiendo"),
      ("kế hoạch giám sát, sổ rủi ro, thử trước công cụ", _co_ma("TN-QC-02", "TN-QC-03", "TN-QC-04", "TN-QC-06")))),
    ("dao_duc", "Tuân thủ đạo đức", "chấp thuận, nguy cơ–lợi ích, đồng thuận, riêng tư, xung đột lợi ích",
     (("mọi phép đo cột Đạo đức và Tôn trọng đối tượng", lambda k: k.nguyen_tac in ("dao_duc", "ton_trong")),
      ("khai và quản lý xung đột lợi ích", _co_ma("TN-TT-01", "TN-KQ-04")))),
    ("kiem_chung", "Kết quả kiểm chứng được", "kết cục định trước, đo được, phân tích khoá trước và tái lập được",
     (("SAP khoá trước dữ liệu, kết cục chính không đổi", _co_ma("TN-KQ-01", "NQ:ket_cuc_chinh", "NQ:thoi_diem_ket_cuc",
                                                                 "G4-AUTO-11", "G4-AUTO-06", "G4-AUTO-07")),
      ("kết cục/biến đo được, hợp lệ", lambda k: k.nguyen_tac == "hop_le_tin_cay" and k.phan == "bienso"),
      ("mọi phép đo cột Tái lập", lambda k: k.nguyen_tac == "tai_lap"))),
)


def _finer(ctx: NguCanh, khoa: str, nhan: str) -> Dict[str, Any]:
    v = ctx.gp.get("G0", {}).get(khoa)
    ly = f"FINER «{nhan}» do G0 chốt (gate_params.G0.{khoa})"
    if isinstance(v, bool):
        return {"nguon": f"G0.{khoa}", "trang_thai": XANH if v else DO, "ly_do": ly, "chi_tiet": [str(v)]}
    t = _nfc(v).strip().upper()
    if not t or _PLACEHOLDER.search(t):
        return {"nguon": f"G0.{khoa}", "trang_thai": CHUA_DO, "ly_do": ly, "chi_tiet": ["chưa chốt"]}
    if t.startswith(("KHÔNG ĐẠT", "CHƯA ĐẠT")):
        tt = DO
    elif t.startswith("ĐẠT CÓ ĐIỀU KIỆN"):
        tt = CHUA_DO  # điều kiện còn mở ⇒ chưa chứng minh xong
    elif t.startswith("ĐẠT"):
        tt = XANH
    else:
        tt = CHUA_DO
    return {"nguon": f"G0.{khoa}", "trang_thai": tt, "ly_do": ly, "chi_tiet": [_nfc(v)[:160]]}


def _cong_song_tp(ctx: NguCanh, g: str, ly: str) -> Dict[str, Any]:
    if not (ctx.out_dir / f"{g}_checkpoint.json").is_file():
        return {"nguon": f"{g} chấm sống", "trang_thai": CHUA_DO, "ly_do": ly, "chi_tiet": ["cổng chưa chạy"]}
    s = ctx.cong(g)
    muc = s.get("muc") if isinstance(s, dict) else None
    tt = {"PASS": XANH, "READY": XANH, "BLOCKED": DO}.get(str(muc), CHUA_DO)
    st = s.get("status") if isinstance(s, dict) else type(s).__name__
    return {"nguon": f"{g} chấm sống", "trang_thai": tt, "ly_do": ly, "chi_tiet": [str(st)]}


def _xac_nhan(ctx: NguCanh, g: str, khoa: str, ly: str) -> Dict[str, Any]:
    v = ctx.gp.get(g, {}).get(khoa)
    tt = XANH if v is True else (DO if v is False else CHUA_DO)
    return {"nguon": f"{g}.{khoa}", "trang_thai": tt, "ly_do": ly, "chi_tiet": [str(v)]}


def _tieu_chi_cong(ctx: NguCanh, ma: str, ly: str) -> Dict[str, Any]:
    g = ma.split("-", 1)[0]
    if not (ctx.out_dir / f"{g}_checkpoint.json").is_file():
        return {"nguon": ma, "trang_thai": CHUA_DO, "ly_do": ly, "chi_tiet": ["cổng chưa chạy"]}
    s = ctx.cong(g)
    bc = s.get("bao_cao") if isinstance(s, dict) else None
    c = next((x for x in ((bc or {}).get("automatic_criteria") or []) if x.get("id") == ma), None)
    if c is None:
        return {"nguon": ma, "trang_thai": CHUA_DO, "ly_do": ly, "chi_tiet": ["không có tiêu chí trong bộ chấm"]}
    st = str(c.get("status") or "").upper()
    return {"nguon": ma, "trang_thai": _CONG_MUC.get(st, CHUA_DO), "ly_do": ly, "chi_tiet": [st]}


def _ngoai_ma_tran(ctx: NguCanh, khoa: str) -> List[Dict[str, Any]]:
    """Chốt hệ đã có, nằm ngoài ma trận, cho từng tiêu chí."""
    if khoa == "gia_tri":
        return [_finer(ctx, "finer_interesting", "thú vị"), _finer(ctx, "finer_novel", "mới"),
                _finer(ctx, "finer_relevant", "phù hợp"),
                _cong_song_tp(ctx, "G0", "cổng câu hỏi nghiên cứu chấm sống")]
    if khoa == "phuong_phap":
        return [_cong_song_tp(ctx, "G3", "cỡ mẫu chấm sống"), _cong_song_tp(ctx, "G4", "SAP chấm sống")]
    if khoa == "kha_thi":
        return [_finer(ctx, "finer_feasible", "khả thi"),
                _xac_nhan(ctx, "G3", "recruitment_feasibility_confirmed",
                          "khả năng tuyển đủ cỡ mẫu trong thời gian/khung mẫu đã được xác nhận ở G3"),
                _tieu_chi_cong(ctx, "G1-AUTO-05", "đủ kế hoạch triển khai A13 và sổ rủi ro A13b")]
    if khoa == "dao_duc":
        return [_finer(ctx, "finer_ethical", "đạo đức"), _cong_song_tp(ctx, "G2", "hồ sơ đạo đức chấm sống")]
    return []


def truc_tong(ctx: NguCanh, do: Sequence[KetQuaDo]) -> List[Dict[str, Any]]:
    ra: List[Dict[str, Any]] = []
    for khoa, ten, mo_ta, bo_loc in TRUC_TONG:
        tp: List[Dict[str, Any]] = []
        for nhan, loc in bo_loc:
            ds = [k for k in do if loc(k) and k.trang_thai != KAD]
            if not ds:
                tp.append({"nguon": nhan, "trang_thai": CHUA_DO, "ly_do": nhan, "chi_tiet": ["không có phép đo"]})
                continue
            dem = {t: sum(1 for k in ds if k.trang_thai == t) for t in (XANH, DO, CHUA_DO)}
            tt = DO if dem[DO] else (XANH if dem[XANH] == len(ds) else CHUA_DO)
            chi = [f"{len(ds)} phép đo: 🟢 {dem[XANH]} · 🔴 {dem[DO]} · ⚪ {dem[CHUA_DO]}"]
            chi += [f"{k.ma}: {(k.chi_tiet or [''])[0][:100]}" for k in ds if k.trang_thai == DO][:3]
            tp.append({"nguon": nhan, "trang_thai": tt, "ly_do": nhan, "chi_tiet": chi})
        tp += _ngoai_ma_tran(ctx, khoa)
        tt = DO if any(x["trang_thai"] == DO for x in tp) else (
            XANH if tp and all(x["trang_thai"] == XANH for x in tp) else CHUA_DO)
        ra.append({"khoa": khoa, "ten": ten, "mo_ta": mo_ta, "trang_thai": tt, "thanh_phan": tp})
    return ra


# ═════════════════════════════════ TỔNG HỢP MA TRẬN ═════════════════════════════════
BO_DO: Tuple[Callable[[NguCanh], List[KetQuaDo]], ...] = (do_luat_k, do_k17, do_nhat_quan, do_cong, do_doi_chieu,
                                                          do_so_lieu_toan_van, do_hoi_dong, do_phep_do_moi)


def phan_khong_ap_dung(ctx: NguCanh) -> Dict[str, str]:
    """{phần: lý do} không tồn tại với thiết kế — theo điều kiện của hệ (không danh sách tay)."""
    import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

    ra: Dict[str, str] = {}
    if ctx.thiet_ke_tho and "co_mau" not in NQ.thong_so_bat_buoc(ctx.thiet_ke_tho):
        ra["comau"] = f"thiết kế {ctx.thiet_ke_tho} không có cỡ mẫu tính theo công thức (nhat_quan.thong_so_bat_buoc)"
    return ra


def nguyen_tac_khong_ap_dung(ctx: NguCanh) -> Dict[str, str]:
    if ctx.thiet_ke_tho and not ctx.co_nguoi_tham_gia():
        return {"ton_trong": f"thiết kế {ctx.thiet_ke_tho} không có người tham gia"}
    return {}


def gop_o(ds: Sequence[KetQuaDo]) -> str:
    """Luật ô: đỏ nếu có phép đo đỏ; xanh chỉ khi MỌI phép đo áp dụng đều xanh; còn lại ⚪."""
    ap = [k for k in ds if k.trang_thai != KAD]
    if any(k.trang_thai == DO for k in ap):
        return DO
    if ap and all(k.trang_thai == XANH for k in ap):
        return XANH
    return CHUA_DO


def tinh(out_dir: Path, study: str, *, loi_k: Optional[List[str]] = None) -> Dict[str, Any]:
    """Ma trận đầy đủ của một đề tài (chỉ đọc). Giữ trong bộ nhớ theo (thư mục, mã, SHA đề cương)."""
    out_dir = Path(out_dir)
    ctx = NguCanh(out_dir, study, loi_k)
    khoa_dem = (str(out_dir.resolve()), study, hashlib.sha256((ctx.md or "").encode("utf-8")).hexdigest(),
                json.dumps(ctx.meta, sort_keys=True, ensure_ascii=False, default=str))
    if khoa_dem in _DEM_KQ:
        return _DEM_KQ[khoa_dem]
    do: List[KetQuaDo] = []
    global _DANG_TINH
    _DANG_TINH += 1  # mọi lời gọi kiem_de_cuong_nop_hoi_dong.kiem lồng bên trong ⇒ K20 trả rỗng (không gọi vòng)
    try:
        for bo in BO_DO:
            try:
                do += bo(ctx)
            except Exception as e:  # noqa: BLE001
                do.append(_kq("BO-DO-HONG", bo.__name__, "tomtat", "trung_thuc", CHUA_DO, "bộ đo hỏng",
                              [f"{type(e).__name__}: {str(e)[:200]}"]))
    finally:
        _DANG_TINH -= 1
    pkad, nkad = phan_khong_ap_dung(ctx), nguyen_tac_khong_ap_dung(ctx)
    o: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for p in PHAN:
        o[p] = {}
        for n in NT:
            ds = [k for k in do if k.phan == p and k.nguyen_tac == n]
            if p in pkad or n in nkad:
                o[p][n] = {"trang_thai": KAD, "ly_do": pkad.get(p) or nkad.get(n), "phep_do": [asdict(k) for k in ds]}
                continue
            o[p][n] = {"trang_thai": gop_o(ds), "phep_do": [asdict(k) for k in ds]}
    tong = {t: sum(1 for p in PHAN for n in NT if o[p][n]["trang_thai"] == t) for t in (XANH, DO, CHUA_DO, KAD)}
    try:
        tong5 = truc_tong(ctx, do)
    except Exception as e:  # noqa: BLE001
        tong5 = [{"khoa": k, "ten": t, "mo_ta": m, "trang_thai": CHUA_DO,
                  "thanh_phan": [{"nguon": "trục tổng", "trang_thai": CHUA_DO, "ly_do": "lỗi",
                                  "chi_tiet": [f"{type(e).__name__}: {e}"]}]} for k, t, m, _ in TRUC_TONG]
    kq = {"study": study, "thiet_ke": ctx.thiet_ke_tho, "co_de_cuong": ctx.md is not None, "o": o, "tong": tong,
          "truc_tong": tong5, "phan_khong_ap_dung": pkad, "nguyen_tac_khong_ap_dung": nkad, "so_phep_do": len(do)}
    _DEM_KQ[khoa_dem] = kq
    return kq


_DEM_KQ: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}


def ma_thoat(kq: Dict[str, Any]) -> int:
    if kq["tong"][DO]:
        return 1
    if kq["tong"][CHUA_DO]:
        return 2
    return 0


def o_theo_trang_thai(kq: Dict[str, Any], tt: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    return [(p, n, kq["o"][p][n]) for p in PHAN for n in NT if kq["o"][p][n]["trang_thai"] == tt]


def ten_phan(p: str) -> str:
    return S.de_cuong_section(p)[1]


def goi_y_o_trang(p: str, n: str, o: Dict[str, Any]) -> str:
    """Gợi ý phép đo cần xây cho ô ⚪ (không phép đo / còn phép đo chưa đo được)."""
    ds = [k for k in o["phep_do"] if k["trang_thai"] == CHUA_DO]
    if not o["phep_do"] or all(k["trang_thai"] == KAD for k in o["phep_do"]):
        return f"chưa có phép đo — xây: {_NT_THEO_KHOA[n].goi_y}"
    return "; ".join(f"{k['ma']}: {(k['chi_tiet'] or [''])[0][:140]}" for k in ds[:3])


# ═════════════════════════════════ K20 (nối vào kiem_de_cuong_nop_hoi_dong) ═════════════════════════════════
def loi_k20(out_dir: Path, study: str, loi_truoc: List[str]) -> List[str]:
    """Lỗi K20: ô 🔴 do phép đo NGOÀI K1–K19 (K1–K19 tự báo lỗi của mình tại chỗ, không nhân đôi). ⚪ không chặn."""
    if _DANG_TINH:
        return []
    if not (Path(out_dir) / f"DE_CUONG_NOP_HOI_DONG_{study}.md").is_file():
        return []
    kq = tinh(out_dir, study, loi_k=list(loi_truoc))
    ra: List[str] = []
    for p, n, o in o_theo_trang_thai(kq, DO):
        do = [k for k in o["phep_do"] if k["trang_thai"] == DO and not k["nguon_k"]]
        if not do:
            continue
        chi = "; ".join(f"{k['ma']} ({(k['chi_tiet'] or [''])[0][:120]})" for k in do[:3])
        ra.append(f"K20 phần «{ten_phan(p)}» × {_NT_THEO_KHOA[n].ten_vi}: {chi}")
    return ra


def canh_bao_k20(out_dir: Path, study: str) -> List[str]:
    """Cảnh báo K20 (không chặn): số ô ⚪ «chưa đo được» theo nguyên tắc — đo chi tiết bằng chính công cụ này."""
    if not (Path(out_dir) / f"DE_CUONG_NOP_HOI_DONG_{study}.md").is_file():
        return []
    kq = tinh(out_dir, study)
    ra = ["K20 trục tổng: " + " · ".join(f"{t['ten']} {BIEU_TUONG[t['trang_thai']]}"
                                         for t in kq.get("truc_tong") or [])]
    trang = o_theo_trang_thai(kq, CHUA_DO)
    if trang:
        dem = {n: sum(1 for _, x, _ in trang if x == n) for n in NT}
        tom = ", ".join(f"{_NT_THEO_KHOA[n].ten_vi} {c}" for n, c in dem.items() if c)
        ra.append(f"K20 {len(trang)} ô ⚪ chưa đo được của ma trận 8 nguyên tắc ({tom}) — chưa chặn; chi tiết: "
                  f"tools/tam_nguyen_tac_de_cuong.py --study {study}")
    return ra


# ═════════════════════════════════ ĐẦU RA ═════════════════════════════════
def bang_anh_xa() -> List[Dict[str, str]]:
    """Bảng ánh xạ TĨNH (phép đo → ô, lý do) — K17 theo phần nên in theo luật phần → ô."""
    ra: List[Dict[str, str]] = []
    for ma, ten, ds, nt, ly in ANH_XA_K_DONG:
        ra += [{"phep_do": ma, "ten": ten, "phan": p, "nguyen_tac": nt, "ly_do": ly} for p in ds]
    for nhan, (p, nt) in _K3_NHAN.items():
        ra.append({"phep_do": "K3", "ten": f"Có chương «{nhan}»", "phan": p, "nguyen_tac": nt,
                   "ly_do": "thiếu chương thì Hội đồng không thẩm định được nội dung đó"})
    for ma, ten, p, nt, ly in ANH_XA_K_CO_DINH:
        ra.append({"phep_do": ma, "ten": ten, "phan": p, "nguyen_tac": nt, "ly_do": ly})
    for k, (p, nt, ly) in ANH_XA_K17_PHAN.items():
        if ly:
            ra.append({"phep_do": f"K17 (mục có phần «{k}»)", "ten": "mục chuẩn theo thiết kế", "phan": p,
                       "nguyen_tac": nt, "ly_do": ly})
    for mau, nt, ly in _K17_CHU_DE:
        ra.append({"phep_do": "K17 (ghi đè theo chủ đề)", "ten": f"chủ đề khớp /{mau[:50]}…/", "phan": "(phần của mục)",
                   "nguyen_tac": nt, "ly_do": ly})
    for ma, (p, nt, ly) in ANH_XA_NQ.items():
        ra.append({"phep_do": "NQ:" + ma, "ten": "nhat_quan_xuyen_cong", "phan": p, "nguyen_tac": nt, "ly_do": ly})
    for ma, (p, nt, ly) in ANH_XA_CONG.items():
        ra.append({"phep_do": ma, "ten": "tiêu chí cổng (chấm sống)", "phan": p, "nguyen_tac": nt, "ly_do": ly})
    for ma, p, nt, ly in (("DC-SAI-LECH", "sailech", "khach_quan", "biện pháp khống chế sai lệch có phân tích SAP"),
                          ("DC-BIEN", "bienso", "hop_le_tin_cay", "biến đo đúng như đề cương đã duyệt"),
                          ("DC-MA-TRAN", "muctieu", "khoa_hoc", "mỗi yếu tố của mục tiêu có biến và phân tích"),
                          ("DC-PHAI-SINH", "bienso", "tai_lap", "công thức phái sinh hợp lệ, đã duyệt đúng dấu"),
                          ("DC-SO-LIEU-TOAN-VAN", "tongquan", "trung_thuc", "con số dẫn có trong toàn văn nguồn")):
        ra.append({"phep_do": ma, "ten": "bộ đối chiếu", "phan": p, "nguyen_tac": nt, "ly_do": ly})
    for muc, cac_o in ANH_XA_HDKH.items():
        ra += [{"phep_do": f"HDKH:{muc}", "ten": "biên bản Hội đồng Khoa học còn hiệu lực", "phan": p,
                "nguyen_tac": nt, "ly_do": f"phán đoán của hội đồng — mục phiếu {muc}"} for p, nt in cac_o]
    for ma, (p, nt) in VI_TRI_PHEP_DO_MOI.items():
        ra.append({"phep_do": ma, "ten": "phép đo mới", "phan": p, "nguyen_tac": nt, "ly_do": "xem docstring hàm"})
    return ra


def markdown(kq: Dict[str, Any]) -> str:
    L: List[str] = [f"# Ma trận 8 nguyên tắc của đề cương — {kq['study']}", "",
                    f"Thiết kế: {kq['thiet_ke'] or 'chưa ghi'} · {kq['so_phep_do']} kết quả phép đo · "
                    f"🟢 {kq['tong'][XANH]} · 🔴 {kq['tong'][DO]} · ⚪ {kq['tong'][CHUA_DO]} · không áp dụng "
                    f"{kq['tong'][KAD]}", "",
                    "## Trục tổng 5 tiêu chí", "",
                    "«Một đề cương nghiên cứu y khoa tốt phải trả lời được một câu hỏi có giá trị bằng phương pháp "
                    "khoa học phù hợp, khả thi về triển khai, tuân thủ đạo đức và tạo ra kết quả có thể kiểm chứng.»",
                    ""] + [f"- {BIEU_TUONG[t['trang_thai']]} **{t['ten']}** — {t['mo_ta']}: "
                           + "; ".join(f"{BIEU_TUONG[x['trang_thai']]} {x['nguon']}" for x in t["thanh_phan"])
                           for t in kq.get("truc_tong") or []] + ["", "## Ma trận phần × nguyên tắc", "",
                    "Luật ô: 🔴 có phép đo đỏ · 🟢 mọi phép đo xanh · ⚪ không có phép đo hoặc còn phép đo chưa "
                    "đo được (không bao giờ báo xanh khi một phần chưa đo) · — không áp dụng theo điều kiện "
                    "của hệ.", ""]
    L.append("| Phần | " + " | ".join(_NT_THEO_KHOA[n].ten_vi for n in NT) + " |")
    L.append("|---|" + "---|" * len(NT))
    for p in PHAN:
        so = S.de_cuong_section(p)[0]
        L.append(f"| {so}. {ten_phan(p)} | "
                 + " | ".join(BIEU_TUONG[kq["o"][p][n]["trang_thai"]] for n in NT) + " |")
    L += ["", "## Ô 🔴", ""]
    do = o_theo_trang_thai(kq, DO)
    if not do:
        L.append("Không có.")
    for p, n, o in do:
        L.append(f"- **{ten_phan(p)} × {_NT_THEO_KHOA[n].ten_vi}**")
        for k in o["phep_do"]:
            if k["trang_thai"] == DO:
                L.append(f"  - {k['ma']} — {k['ten']}: {' | '.join(k['chi_tiet'][:3])}")
    L += ["", "## Ô ⚪ và phép đo cần xây", ""]
    trang = o_theo_trang_thai(kq, CHUA_DO)
    if not trang:
        L.append("Không có.")
    for p, n, o in trang:
        L.append(f"- {ten_phan(p)} × {_NT_THEO_KHOA[n].ten_vi}: {goi_y_o_trang(p, n, o)}")
    L += ["", "## Tám nguyên tắc — định nghĩa vận hành và nguồn", ""]
    for nt in NGUYEN_TAC:
        nguon = "; ".join(f"{x.ten}, {x.phien_ban}" + (f", PMID {x.pmid}" if x.pmid else "")
                          + (f", doi:{x.doi}" if x.doi else "") for x in nt.nguon)
        L.append(f"- **{nt.ten_vi} ({nt.ten_en})** — {nt.dinh_nghia} Nguồn: {nguon}.")
    L.append("")
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Ma trận 8 nguyên tắc của đề cương (phần × nguyên tắc).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--goc", type=Path, default=BASE, help="thư mục chứa exports/ (mặc định: repo này)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ghi", action="store_true", help="ghi MA_TRAN_8_NGUYEN_TAC_<mã>.md/.json vào thư mục đề tài")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 3
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print(f"Mã đề tài không hợp lệ: {a.study!r}")
        return 3
    out_dir = Path(a.goc) / "exports" / a.study
    if not out_dir.is_dir():
        print(f"Không có thư mục đề tài: {out_dir}")
        return 3
    kq = tinh(out_dir, a.study)
    if a.ghi:
        ten = f"MA_TRAN_8_NGUYEN_TAC_{a.study}"
        (out_dir / f"{ten}.md").write_text(markdown(kq), encoding="utf-8", newline="\n")
        (out_dir / f"{ten}.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                             newline="\n")
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=1))
    else:
        print(markdown(kq))
    return ma_thoat(kq)


if __name__ == "__main__":
    raise SystemExit(main())
