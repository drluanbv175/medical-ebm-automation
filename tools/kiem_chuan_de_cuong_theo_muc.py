#!/usr/bin/env python3
"""Đối chiếu ĐỀ CƯƠNG với TỪNG MỤC của mọi chuẩn áp dụng cho thiết kế — quốc tế và Việt Nam (K17).

VÌ SAO (21/11/2026, bác sĩ): «đề cương nghiên cứu theo từng tiêu chuẩn và từng tiêu chuẩn trong từng cấu trúc đề cương
nghiên cứu phải đạt tiêu chuẩn và sự tin cậy cao nhất»; «những gì không đạt chuẩn sẽ phải được loại bỏ»; «xây dựng hệ
thống cho tất cả các đề tài nghiên cứu y khoa chứ không riêng nghiên cứu mô tả cắt ngang». Trước đó kho chỉ có danh mục
theo mục cho RCT (SPIRIT 2025) và tổng quan hệ thống (PRISMA-P 2015). `protocol_checklist_items.items_for_design` trả
None cho thiết kế quan sát, nên các mục phương pháp STROBE 4–12 chưa từng được kiểm ở đề cương — đúng loại thiết kế
của cả hai đề tài thật.

CÁCH KIỂM (tất định, không gọi mạng):
  1. Chọn chuẩn theo thiết kế (`CHUAN_CO_SO`) + chuẩn có điều kiện (RECORD khi dùng dữ liệu thường quy; CROSS khi
     khảo sát bằng bộ câu hỏi; COSMIN khi phát triển/kiểm định công cụ) + chuẩn Việt Nam (mọi thiết kế).
  2. Mỗi mục gắn với PHẦN của đề cương (nhận theo tên đề mục, chạy được với khuôn BVQY175 lẫn khuôn 18 mục) và một danh
     sách YẾU TỐ bắt buộc (biểu thức). ĐẠT chỉ khi MỌI yếu tố có mặt TRONG phần đó; báo số dòng làm bằng chứng.
  3. Mục «if applicable» chỉ xét khi đề cương có điều kiện tương ứng (vd 12d cắt ngang khi có chọn mẫu cụm/gom cụm).
  4. Chuẩn chưa có tiêu chí tự động ⇒ «chua_do» (⚪), KHÔNG BAO GIỜ tính là đạt.

MỨC ĐỘ: `bat_buoc` (mục phương pháp phải có trong đề cương) · `ke_hoach` (mục kết quả/bàn luận — đề cương phải lên kế
hoạch: khung bảng, sơ đồ chọn mẫu, phần hạn chế) · `bao_cao` (chỉ áp khi viết bài báo, vd tiêu đề/tóm tắt — liệt kê,
không chấm ở đề cương).

GIỚI HẠN (nói thẳng): yếu tố có mặt ≠ nội dung đúng. Bộ kiểm bắt THIẾU một cách tin cậy, còn ĐẠT là «có dấu hiệu đủ
yếu tố» — người phân xử (agent kiem-chung-trich-dan/binh-duyet) đọc bằng chứng từng dòng trước khi kết luận chất lượng.
Nội dung SAI (số không nguồn, câu mơ hồ, trích sai) do K10/K15/A12 bắt và phải loại bỏ.

Bản quyền: nguyên văn STROBE/RECORD (CC BY) lấy từ `chuan_bao_cao_items.py`; CROSS (© Society of General Internal
Medicine 2021) KHÔNG lưu nguyên văn — chỉ mã mục, chủ đề và tiêu chí do hệ viết.

Lệnh:  python3 tools/kiem_chuan_de_cuong_theo_muc.py --study <mã> [--tep <md>] [--chi-tiet] [--json]
Mã thoát: 0 không thiếu mục bắt buộc/kế hoạch · 1 có mục thiếu · 2 thiếu đề cương · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import chuan_bao_cao_items as CBC  # noqa: E402
import skill_standards as S  # noqa: E402

_C = re.IGNORECASE | re.MULTILINE

# ───────────────────────────── phần của đề cương (nhận theo tên đề mục) ─────────────────────────────
PHAN: Dict[str, str] = {
    "bia": r"",  # chữ trước đề mục đầu tiên + «Thông tin chung»/«Tóm tắt»
    "dat_van_de": r"ĐẶT VẤN ĐỀ",
    "muc_tieu": r"MỤC TIÊU",
    "cau_hoi": r"Câu hỏi|Giả thuyết",
    "tong_quan": r"TỔNG QUAN",
    "thiet_ke": r"Thiết kế",
    "dia_diem": r"Địa điểm|Thời gian nghiên cứu|bối cảnh",
    # đề mục BẮT ĐẦU bằng «Đối tượng nghiên cứu» (không lấy «5.1. Đặc điểm đối tượng nghiên cứu» của chương kết quả —
    # từng làm STROBE 6a nhận «lý do loại» của ghi chú sơ đồ là «lý do chọn ca và chứng», 21/11/2026)
    "doi_tuong": r"^(?:[\dIVX]+(?:\.\d+)*\.?\s+)?Đối tượng nghiên cứu|Tiêu chuẩn (lựa )?chọn|Tiêu chuẩn loại|"
                 r"Nhóm bệnh và nhóm chứng",
    "co_mau": r"Cỡ mẫu",
    "chon_mau": r"chọn mẫu|Tuyển mẫu",
    "phoi_nhiem": r"Phơi nhiễm|nhóm so sánh",
    "bien_so": r"Biến số|chỉ số nghiên cứu|Biến kết cục|Biến độc lập",
    "cong_cu": r"Công cụ|kỹ thuật thu thập|Bộ câu hỏi",
    "quy_trinh": r"Quy trình nghiên cứu|Các bước tiến hành",
    "sai_so": r"Sai số|Sai lệch|khống chế",
    "phan_tich": r"phân tích số liệu|phân tích thống kê|Xử lý và phân tích|KẾ HOẠCH PHÂN TÍCH",
    "dao_duc": r"Đạo đức|ĐỒNG Ý THAM GIA|MIỄN ĐỒNG THUẬN|Xung đột lợi ích",
    "du_kien_kq": r"DỰ KIẾN KẾT QUẢ|Kết quả theo mục tiêu|Đặc điểm đối tượng|Phân tích độ nhạy",
    "ban_luan": r"^(?!.*KẾT QUẢ).*bàn luận",
    "han_che": r"Hạn chế",
    "quan_ly_dl": r"quản lý dữ liệu|Quản trị dữ liệu",
    "kinh_phi": r"kinh phí|nguồn lực|THÔNG TIN CHUNG",
    "pho_bien": r"Đăng ký nghiên cứu|phổ biến",
    "phieu": r"PHIẾU (KHẢO SÁT|THU THẬP)|BỘ CÂU HỎI",
    "bang_bien": r"BẢNG BIẾN SỐ|MÃ HO[ÁA]",
    "danh_muc_ma": r"DANH MỤC MÃ",
}
_DE_MUC_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$", re.M)
#: Mục phương pháp không lấy bằng chứng ở Đặt vấn đề/Tổng quan (vd «1.2. Công cụ đo lường…» của tổng quan KHÔNG phải
#: công cụ của đề tài — từng làm CROSS 7a «đạt» nhờ đoạn tổng quan về SERVQUAL, 21/11/2026).
_PHAN_MO_DAU = frozenset({"bia", "dat_van_de", "tong_quan", "muc_tieu"})
_CHUONG_MO_DAU = re.compile(r"ĐẶT VẤN ĐỀ|TỔNG QUAN", re.IGNORECASE)


@dataclass
class Phan:
    """Một khối của đề cương: từ đề mục tới đề mục cùng cấp hoặc cao hơn kế tiếp."""

    tieu_de: str
    dong_dau: int  # số dòng (1-based) của đề mục
    van: str
    chuong: str = ""  # tiêu đề cấp 1 bao ngoài (để loại Đặt vấn đề/Tổng quan khỏi mục phương pháp)


def tach_phan(md: str) -> List[Phan]:
    """Mọi khối đề mục của đề cương (cả khối lồng nhau)."""
    dong = md.split("\n")
    de_muc = [(i, len(m.group(1)), m.group(2)) for i, d in enumerate(dong) for m in [_DE_MUC_RE.match(d)] if m]
    ra = []
    chuong = ""
    for k, (i, cap, td) in enumerate(de_muc):
        if cap == 1:
            chuong = td
        het = len(dong)
        for j, cap2, _ in de_muc[k + 1:]:
            if cap2 <= cap:
                het = j
                break
        ra.append(Phan(td, i + 1, "\n".join(dong[i:het]), chuong))
    dau = de_muc[0][0] if de_muc else len(dong)
    ra.insert(0, Phan("(bìa)", 1, "\n".join(dong[:dau])))
    return ra


def khoi_cua(cac_phan: Sequence[Phan], khoa: Sequence[str]) -> List[Phan]:
    """Các khối thuộc những phần đã nêu (không trùng lặp, bỏ khối nằm trọn trong khối đã chọn)."""
    chon: List[Phan] = []
    for k in khoa:
        if k == "bia":
            chon += [p for p in cac_phan if p.tieu_de == "(bìa)" or re.search(r"THÔNG TIN CHUNG|TÓM TẮT", p.tieu_de)]
            continue
        mau = re.compile(PHAN[k], re.IGNORECASE)
        mo_dau = k in _PHAN_MO_DAU
        chon += [p for p in cac_phan if p.tieu_de != "(bìa)" and mau.search(p.tieu_de)
                 and (mo_dau or not _CHUONG_MO_DAU.search(p.chuong))]
    ra: List[Phan] = []
    for p in sorted(chon, key=lambda x: (x.dong_dau, -len(x.van))):
        het = p.dong_dau + p.van.count("\n")
        if any(q.dong_dau <= p.dong_dau and het <= q.dong_dau + q.van.count("\n") for q in ra):
            continue
        ra.append(p)
    return ra


# ───────────────────────────── mô hình mục kiểm ─────────────────────────────
@dataclass(frozen=True)
class YeuTo:
    """Một yếu tố phải có. `khi`: chỉ đòi khi biểu thức này khớp ở CẢ đề cương."""

    ten: str
    mau: str
    khi: Optional[str] = None
    de_muc: bool = False  # yếu tố «có tiểu mục» — được khớp cả dòng đề mục (vd «2.1.2. Tiêu chuẩn loại trừ»)


@dataclass(frozen=True)
class MucKiem:
    chuan: str
    ma: str
    chu_de: str
    nguyen_van: Optional[str]
    tieu_chi: str
    phan: Tuple[str, ...]
    yeu_to: Tuple[YeuTo, ...]
    muc_do: str = "bat_buoc"
    ap_dung_khi: Optional[str] = None
    ly_do_dieu_kien: str = ""
    cung_doan: bool = False  # mọi yếu tố phải cùng một đoạn văn hoặc một dòng bảng


@dataclass
class KetQua:
    chuan: str
    ma: str
    chu_de: str
    tieu_chi: str
    muc_do: str
    trang_thai: str  # dat · thieu · khong_ap_dung · chua_do · bao_cao
    bang_chung: List[str] = field(default_factory=list)
    thieu: List[str] = field(default_factory=list)
    vi_tri: List[str] = field(default_factory=list)
    ly_do: str = ""
    nguyen_van: Optional[str] = None


# ───────────────────────────── mẫu dùng chung ─────────────────────────────
NGAY = (r"(?:\b\d{1,2}/\d{1,2}/(?:19|20)\d{2}\b|\b\d{1,2}/(?:19|20)\d{2}\b|"
        r"\btháng\s+\d{1,2}(?:/|\s+năm\s+)(?:19|20)\d{2}"
        r"|\b(?:19|20)\d{2}\s*[–-]\s*(?:19|20)?\d{2}\b|\bnăm\s+(?:19|20)\d{2}\b)")
NOI = r"(?:Bệnh viện|\bKhoa\b|phòng khám|Trung tâm|Trạm y tế|cơ sở y tế|địa bàn)"
PHAN_TICH = (r"yếu tố liên quan|mối liên quan|liên quan (với|đến)|so sánh|hồi quy|tỷ số chênh|\bOR\b|\bPR\b|\bRR\b|"
             r"\bHR\b")
#: Tiền tố «@muc_tieu:» ⇒ điều kiện chỉ xét trong phần MỤC TIÊU / CÂU HỎI của đề cương (21/11/2026). Đo trên giả lập
#: cắt ngang MÔ TẢ: `PHAN_TICH` xét trên cả văn bản khớp chữ «OR» của chuỗi tìm PubMed, «liên quan đến» của câu đạo đức
#: và «so sánh» của phân tích độ nhạy ⇒ bộ kiểm đòi phơi nhiễm, giả thuyết, ước lượng thô/hiệu chỉnh cho một đề tài chỉ
#: ước lượng tỷ lệ. «Mục tiêu phân tích liên quan» (STROBE 3) là điều MỤC TIÊU nói, không phải điều văn bản nhắc tới.
MUC_TIEU_PHAN_TICH = "@muc_tieu:" + PHAN_TICH + r"|ảnh hưởng (đến|tới|của)|yếu tố nguy cơ"
DU_LIEU_THUONG_QUY = (r"\bHIS\b|bệnh án điện tử|hồ sơ bệnh án|phần mềm quản lý bệnh viện|dữ liệu (thu thập )?thường quy"
                      r"|cơ sở dữ liệu (quốc gia|bảo hiểm (y tế|xã hội))|trích xuất (dữ liệu|số liệu)")
KHAO_SAT = (r"tự điền|phát phiếu|phiếu khảo sát|bảng hỏi|thu thập (số liệu )?bằng bộ câu hỏi|"
            r"phỏng vấn (trực tiếp )?(người bệnh|đối tượng|bệnh nhân|người tham gia)")
CHON_TU_CSDL = (r"\bICD|khung mẫu.{0,120}(eHospital|\bHIS\b|phần mềm|cơ sở dữ liệu)|"
                r"(danh sách|quần thể).{0,60}(lấy|trích|lọc) (từ|trên) (eHospital|\bHIS\b|phần mềm|cơ sở dữ liệu)")
MA_CHUAN = r"\bICD|mã ATC|mã (bệnh|thuốc|xét nghiệm)"
CONG_CU_DO = (r"\bCVI\b|giá trị nội dung|phỏng vấn nhận thức|phân tích nhân tố|Cronbach|độ tin cậy (nội tại|lặp lại)"
              r"|thích ứng (văn hoá|văn hóa|xuyên)")
# «ghép theo giới và nhóm tuổi…, 2 chứng : 1 ca» là ghép cặp dù không viết chữ «ghép cặp» (21/11/2026: bản cũ coi đề tài
# bệnh–chứng ghép là KHÔNG ghép ⇒ STROBE 6b/12d «không áp dụng» sai)
GHEP_CAP = (r"ghép cặp|bắt cặp|ghép (theo|với)\b|\bmatching\b|\bmatched\b|\d+\s*chứng\s*(:\s*\d+\s*ca|"
            r"(cho )?mỗi ca)")
CUM = r"chọn mẫu cụm|mẫu cụm|gom cụm|nhiều giai đoạn|phân tầng|tương quan nội cụm|\bICC\b|hiệu ứng thiết kế"
LIEN_KET = r"liên kết (dữ liệu|cơ sở dữ liệu)|ghép nối (dữ liệu|cơ sở)|\blinkage\b"
TRUC_TUYEN = r"khảo sát trực tuyến|phiếu (điện tử|trực tuyến)|Google Forms|SurveyMonkey|biểu mẫu (điện tử|trực tuyến)"
THEO_DOI_DOC = r"theo dõi dọc|nhiều lần (đo|khảo sát)|khảo sát lặp lại"

_TK_STROBE = {"cross_sectional": "cat_ngang", "cohort": "thuan_tap", "case_control": "benh_chung"}


def _y(ten: str, mau: str, khi: Optional[str] = None, de_muc: bool = False) -> YeuTo:
    return YeuTo(ten, mau, khi, de_muc)


# ─────────────── STROBE 2007: tiêu chí kiểm ở ĐỀ CƯƠNG (khoá = (mã, thiết kế|chung)) ───────────────
# (phần, mức độ, tiêu chí tiếng Việt, yếu tố, áp dụng khi, lý do điều kiện)
_STROBE_TIEU_CHI: Dict[Tuple[str, str], tuple] = {
    ("1a", "chung"): ((), "bao_cao", "Tiêu đề hoặc tóm tắt bài báo nêu thiết kế bằng thuật ngữ thông dụng.", ()),
    ("1b", "chung"): ((), "bao_cao", "Tóm tắt bài báo cân đối giữa việc đã làm và kết quả.", ()),
    ("2", "chung"): (("dat_van_de", "tong_quan"), "bat_buoc",
                     "Nêu cơ sở khoa học có trích dẫn và lý do thực hiện (khoảng trống cần lấp).",
                     (_y("trích dẫn nguồn", r"\[\d+(?:[,–-]\s*\d+)*\]"),
                      _y("lý do/khoảng trống", r"khoảng trống|chưa (có|thấy|được)|cần (thiết|có)"))),
    ("3", "chung"): (("muc_tieu", "cau_hoi"), "bat_buoc",
                     "Nêu mục tiêu cụ thể; mục tiêu phân tích liên quan phải kèm giả thuyết định trước.",
                     (_y("mục tiêu cụ thể", r"^[ \t]*(?:\d[.)]|-|\*)[ \t]*[*_]*[ \t]*(?:MT\d+[ \t]*:[ \t]*)?(?:Mô tả|"
                                            r"Xác định|Phân tích|Đánh giá|"
                                          r"So sánh|Ước tính|Khảo sát|Xây dựng|Kiểm định)"),
                      _y("giả thuyết định trước", r"giả thuyết|\bH[0₀1₁]\b", khi=MUC_TIEU_PHAN_TICH))),
    ("4", "chung"): (("thiet_ke",), "bat_buoc",
                     "Nêu các yếu tố then chốt của thiết kế: tên thiết kế và hướng thời gian thu thập.",
                     (_y("tên thiết kế", r"cắt ngang|thuần tập|bệnh[\s–-]*chứng"),
                      _y("hướng thời gian", r"hồi cứu|tiến cứu|(một|cùng) thời điểm|theo dõi"))),
    ("5", "chung"): (("dia_diem", "thiet_ke"), "bat_buoc",
                     "Nêu nơi thực hiện và các mốc ngày cụ thể, gồm giai đoạn tuyển chọn/thu thập.",
                     (_y("nơi thực hiện", NOI), _y("mốc ngày cụ thể", NGAY),
                      _y("giai đoạn thu thập", r"thu thập|tuyển|lấy mẫu|trích xuất|khảo sát"))),
    ("6a", "cat_ngang"): (("doi_tuong", "chon_mau"), "bat_buoc",
                          "Nêu tiêu chuẩn chọn, tiêu chuẩn loại, nguồn và cách chọn người tham gia.",
                          (_y("tiêu chuẩn chọn", r"Tiêu chuẩn (lựa )?chọn", de_muc=True),
                           _y("tiêu chuẩn loại", r"Tiêu chuẩn loại", de_muc=True),
                           _y("cách chọn người tham gia",
                              r"chọn mẫu|lấy mẫu|ngẫu nhiên|thuận tiện|toàn bộ|liên tiếp|hệ thống"))),
    ("6a", "thuan_tap"): (("doi_tuong", "chon_mau", "quy_trinh"), "bat_buoc",
                          "Nêu tiêu chuẩn chọn/loại, nguồn và cách chọn người tham gia, và cách theo dõi.",
                          (_y("tiêu chuẩn chọn", r"Tiêu chuẩn (lựa )?chọn", de_muc=True),
                           _y("tiêu chuẩn loại", r"Tiêu chuẩn loại", de_muc=True),
                           _y("cách chọn người tham gia", r"chọn mẫu|lấy mẫu|ngẫu nhiên|toàn bộ|liên tiếp"),
                           _y("cách theo dõi", r"theo dõi|tái khám|kết thúc theo dõi"))),
    ("6a", "benh_chung"): (("doi_tuong", "chon_mau"), "bat_buoc",
                           "Nêu tiêu chuẩn chọn, cách xác định ca, cách chọn chứng và lý do chọn.",
                           (_y("tiêu chuẩn chọn", r"Tiêu chuẩn (lựa )?chọn", de_muc=True),
                            _y("cách xác định ca", r"nhóm bệnh|ca bệnh|định nghĩa ca|xác định ca"),
                            _y("cách chọn chứng", r"nhóm chứng|chọn chứng"),
                            _y("lý do chọn ca và chứng", r"lý do (chọn|lựa chọn)|nhằm|"
                                                        r"để (bảo đảm|tránh|đại diện|nhóm chứng)|"
                                                        r"đại diện cho (quần thể|phân bố)"))),
    ("6b", "thuan_tap"): (("doi_tuong", "chon_mau", "phoi_nhiem"), "bat_buoc",
                          "Nghiên cứu ghép cặp: nêu tiêu chí ghép và số người phơi nhiễm/không phơi nhiễm.",
                          (_y("tiêu chí ghép", r"ghép (cặp )?theo|tiêu chí ghép|bắt cặp theo"),
                           _y("tỷ lệ ghép", r"\b\d\s*:\s*\d\b|tỷ lệ\s*\d")), GHEP_CAP, "có ghép cặp"),
    ("6b", "benh_chung"): (("doi_tuong", "chon_mau"), "bat_buoc",
                           "Nghiên cứu ghép cặp: nêu tiêu chí ghép và số chứng cho mỗi ca.",
                           (_y("tiêu chí ghép", r"ghép (cặp )?theo|tiêu chí ghép|bắt cặp theo"),
                            # «2 chứng : 1 ca» (cách viết của PI ở control_source) từng bị bỏ sót, 21/11/2026
                            _y("số chứng mỗi ca", r"\b\d\s*:\s*\d\b|\d+ chứng (cho )?mỗi ca|"
                                                  r"\d+\s*chứng\s*:\s*\d+\s*ca")),
                            GHEP_CAP, "có ghép cặp"),
    ("7", "chung"): (("bien_so", "bang_bien", "phoi_nhiem"), "bat_buoc",
                     "Định nghĩa rõ kết cục, phơi nhiễm/biến độc lập, yếu tố nhiễu, biến điều chỉnh tác động (khi có)"
                     " và"
                     " tiêu chuẩn chẩn đoán.",
                     (_y("kết cục", r"kết cục|biến (phụ thuộc|kết quả)", de_muc=True),
                      _y("phơi nhiễm/biến độc lập", r"phơi nhiễm|biến độc lập|yếu tố", khi=MUC_TIEU_PHAN_TICH,
                         de_muc=True),
                      _y("yếu tố nhiễu", r"nhiễu|hiệu chỉnh", khi=MUC_TIEU_PHAN_TICH),
                      _y("biến điều chỉnh tác động", r"tương tác|điều chỉnh (tác động|hiệu ứng)|phân nhóm",
                         khi=r"(kiểm định|đánh giá|ước lượng) tương tác|số hạng tương tác|"
                             r"nhóm nhỏ (tiền định|xác định trước)|"
                             r"phân tích (nhóm nhỏ|phân nhóm) (tiền định|xác định trước)"),
                      _y("tiêu chuẩn chẩn đoán/định nghĩa", r"tiêu chuẩn chẩn đoán|định nghĩa|"
                                                            r"theo (KDIGO|ADA|WHO|ESC|Bộ Y tế)"))),
    ("8", "chung"): (("cong_cu", "quy_trinh", "bien_so"), "bat_buoc",
                     "Mỗi biến chính có nguồn dữ liệu và cách đo; nhiều nhóm thì nêu tính tương đồng của cách đo.",
                     (_y("nguồn dữ liệu", r"nguồn (dữ liệu|số liệu)|phỏng vấn|bộ câu hỏi|phiếu|hồ sơ bệnh án|\bHIS\b"
                                          r"|xét nghiệm|trích xuất"),
                      _y("cách đo", r"\bđo\b|đánh giá bằng|thang|định lượng|phương pháp|cách tính"),
                      _y("tương đồng cách đo giữa các nhóm",
                         r"cùng (một )?(cách|phương pháp|quy trình|công cụ|bộ câu hỏi|phiếu|định nghĩa)|cho cả (hai )?"
                         r"nhóm|như nhau|thống nhất|chuẩn hoá|chuẩn hóa",
                         khi=r"nhóm (so sánh|chứng|phơi nhiễm|không phơi nhiễm|can thiệp)"))),
    ("9", "chung"): (("sai_so",), "bat_buoc",
                     "Nêu cụ thể nguồn sai lệch tiềm tàng và biện pháp khống chế từng nguồn.",
                     (_y("nguồn sai lệch cụ thể", r"(sai số|sai lệch) (chọn|thông tin|nhớ lại|đo lường|phân loại)|"
                                                  r"nhiễu"),
                      _y("biện pháp khống chế",
                         r"khống chế|hạn chế|kiểm soát|biện pháp|tập huấn|chuẩn hoá|chuẩn hóa|nhập liệu kép")),
                         None, "", True),
    ("10", "chung"): (("co_mau",), "bat_buoc",
                      "Giải thích cách tính cỡ mẫu: công thức/phương pháp, tham số có nguồn, cỡ mẫu cuối cùng.",
                      (_y("công thức/phương pháp", r"công thức|Cochran|lực mẫu|độ chính xác|\bpower\b|Riley|\bEPV\b"
                                                   r"|n\s*=|toàn bộ"),
                       # p = 0,5 chọn có chủ đích để cỡ mẫu lớn nhất khi chưa có số liệu tại cơ sở là căn cứ hợp lệ
                       # (không phải tham số bịa) — 21/11/2026
                       _y("tham số có nguồn", r"\[\d+|tham khảo|nghiên cứu (trước|thử|của)|"
                                              r"p\s*=\s*0[,.]5\b.{0,100}(lớn nhất|tối đa|thận trọng)"),
                       _y("cỡ mẫu cuối cùng", r"\d[\d.,]*\s*(người|bệnh nhân|đối tượng|hồ sơ|lượt|trường hợp)"))),
    ("11", "chung"): (("phan_tich", "bien_so", "bang_bien"), "bat_buoc",
                      "Nêu cách xử lý biến định lượng trong phân tích (giữ liên tục hay phân nhóm, ngưỡng và lý do).",
                      (_y("biến định lượng", r"định lượng|liên tục"),
                       _y("cách xử lý/ngưỡng", r"phân nhóm|ngưỡng|giữ (nguyên )?dạng liên tục|spline|mỗi \d+|"
                                               r"tuyến tính"),)),
    ("12a", "chung"): (("phan_tich",), "bat_buoc",
                       "Mô tả mọi phương pháp thống kê, gồm cách kiểm soát nhiễu khi có mục tiêu phân tích.",
                       (_y("phương pháp thống kê", r"hồi quy|kiểm định|chi bình phương|χ²|Mann|Wilcoxon|Fisher|logistic"
                                                 r"|Poisson|\bCox\b|khoảng tin cậy|KTC"),
                        _y("kiểm soát nhiễu", r"hiệu chỉnh|đa biến|\bDAG\b|gây nhiễu", khi=MUC_TIEU_PHAN_TICH))),
    ("12b", "chung"): (("phan_tich",), "bat_buoc", "Mô tả phương pháp phân tích nhóm nhỏ và tương tác.",
                       (_y("phương pháp nhóm nhỏ/tương tác", r"tương tác|nhóm nhỏ|số hạng|"
                                                             r"không có phân tích (phân nhóm|"
                                                             r"nhóm nhỏ)"),),
                       r"phân tích (nhóm nhỏ|phân nhóm|theo nhóm)|tương tác", "có kế hoạch phân tích nhóm nhỏ/tương"
                                                                              " tác"),
    ("12c", "chung"): (("phan_tich", "quan_ly_dl"), "bat_buoc", "Nêu cách xử lý dữ liệu thiếu.",
                       (_y("dữ liệu thiếu", r"(dữ liệu|số liệu|giá trị) thiếu|thiếu (dữ liệu|số liệu)|missing"),
                        _y("phương pháp xử lý", r"ca đầy đủ|complete case|đa quy|điền khuyết|multiple imputation|MICE|"
                                               r"trường hợp đủ dữ liệu|gán|loại khỏi|phân tích độ nhạy")),
                                               None, "", True),
    ("12d", "thuan_tap"): (("phan_tich",), "bat_buoc", "Nêu cách xử lý mất theo dõi.",
                           (_y("xử lý mất theo dõi", r"mất theo dõi|kiểm duyệt|censor"),)),
    ("12d", "benh_chung"): (("phan_tich",), "bat_buoc", "Nghiên cứu ghép cặp: nêu cách phân tích có tính đến ghép cặp.",
                            (_y("phân tích theo ghép cặp", r"có điều kiện|conditional|phân tầng theo cặp"),),
                            GHEP_CAP, "có ghép cặp"),
    ("12d", "cat_ngang"): (("phan_tich", "co_mau", "chon_mau"), "bat_buoc",
                           "Chọn mẫu cụm/phân tầng hoặc dữ liệu gom cụm: nêu cách phân tích có tính đến chiến lược"
                           " chọn mẫu.",
                           (_y("phân tích tính chiến lược chọn mẫu", r"hiệu chỉnh (gom )?cụm|robust|\bGEE\b|"
                                                                     r"mô hình (hỗn hợp"
                                                                      r"|đa mức)|hiệu ứng thiết kế|"
                                                                      r"design effect|trọng số"
                                                                      r"|sandwich|ngẫu nhiên theo"),),
                           CUM, "có chọn mẫu cụm/phân tầng hoặc gom cụm"),
    ("12e", "chung"): (("phan_tich", "du_kien_kq"), "bat_buoc", "Mô tả các phân tích độ nhạy.",
                       (_y("phân tích độ nhạy", r"phân tích độ nhạy|sensitivity"),)),
    ("13a", "chung"): (("du_kien_kq", "quy_trinh", "chon_mau"), "ke_hoach",
                       "Lên kế hoạch báo cáo số người ở từng giai đoạn (đủ tiêu chuẩn, tham gia, phân tích).",
                       (_y("số người từng giai đoạn/sơ đồ", r"sơ đồ|lưu đồ|số (người|đối tượng|hồ sơ|lượt).{0,60}"
                                                           r"(đủ tiêu chuẩn|từ chối|bị loại|tham gia|phân tích)"),)),
    ("13b", "chung"): (("du_kien_kq", "quy_trinh", "chon_mau"), "ke_hoach",
                       "Lên kế hoạch ghi lý do không tham gia ở từng giai đoạn.",
                       (_y("lý do không tham gia", r"lý do (từ chối|không tham gia|bị loại|loại)"),)),
    ("13c", "chung"): ((), "bao_cao", "Cân nhắc dùng sơ đồ luồng khi báo cáo.", ()),
    ("14a", "chung"): (("du_kien_kq",), "ke_hoach", "Lên kế hoạch bảng đặc điểm người tham gia và yếu tố nhiễu.",
                       (_y("bảng đặc điểm", r"Đặc điểm (chung|đối tượng|nền)|đặc điểm của", de_muc=True),)),
    ("14b", "chung"): (("du_kien_kq", "phan_tich"), "ke_hoach",
                       "Lên kế hoạch báo cáo số người thiếu dữ liệu theo từng biến.",
                       (_y("dữ liệu thiếu theo biến", r"thiếu.{0,40}(từng|mỗi|theo) biến|"
                                                      r"(từng|mỗi) biến.{0,40}thiếu"),)),
    ("14c", "thuan_tap"): (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch tóm tắt thời gian theo dõi.",
                           (_y("thời gian theo dõi", r"thời gian theo dõi|người[\s-]năm"),)),
    ("15", "cat_ngang"): (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo số ca/tỷ lệ kết cục.",
                          (_y("số ca/tỷ lệ kết cục", r"tỷ lệ|số (ca|người)"),)),
    ("15", "thuan_tap"): (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo số biến cố theo thời gian.",
                          (_y("số biến cố theo thời gian", r"số biến cố|tỷ suất|người[\s-]năm|tích luỹ|tích lũy"),)),
    ("15", "benh_chung"): (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo số người theo mức phơi nhiễm.",
                           (_y("số theo mức phơi nhiễm", r"phơi nhiễm"),)),
    ("16a", "chung"): (("du_kien_kq", "phan_tich"), "ke_hoach",
                       "Lên kế hoạch trình bày ước lượng thô và hiệu chỉnh kèm khoảng tin cậy, nêu biến hiệu chỉnh và"
                       " lý do.",
                       (_y("ước lượng thô", r"\bthô\b|chưa hiệu chỉnh|đơn biến"),
                        _y("ước lượng hiệu chỉnh", r"hiệu chỉnh"),
                        _y("khoảng tin cậy", r"KTC|khoảng tin cậy|\bCI\b")), MUC_TIEU_PHAN_TICH,
                       "có mục tiêu phân tích liên quan"),
    ("16b", "chung"): ((), "bao_cao", "Báo cáo ranh giới nhóm khi phân nhóm biến liên tục.", ()),
    ("16c", "chung"): ((), "bao_cao", "Cân nhắc chuyển nguy cơ tương đối thành nguy cơ tuyệt đối.", ()),
    ("17", "chung"): ((), "bao_cao", "Báo cáo các phân tích khác (đã lên kế hoạch ở 12b, 12e).", ()),
    ("18", "chung"): (("ban_luan",), "ke_hoach", "Lên kế hoạch bàn luận kết quả chính theo từng mục tiêu.",
                      (_y("bàn luận theo mục tiêu", r"mục tiêu", de_muc=True),)),
    ("19", "chung"): (("han_che", "ban_luan", "sai_so"), "ke_hoach",
                      "Bàn hạn chế: nguồn sai lệch hoặc thiếu chính xác, kèm chiều tác động có thể có.",
                      (_y("hạn chế/sai lệch", r"hạn chế|sai lệch|sai số"),
                       _y("chiều tác động của sai lệch", r"(ước lượng|đánh giá) (quá )?(cao|thấp)|làm (tăng|giảm)|"
                                                         r"thấp hơn thực tế|cao hơn thực tế|"
                                                         r"chiều|hướng về")), None, "", True),
    ("20", "chung"): ((), "bao_cao", "Diễn giải thận trọng khi viết bài báo.", ()),
    ("21", "chung"): (("han_che", "ban_luan"), "ke_hoach", "Bàn phạm vi suy rộng (giá trị ngoại) của kết quả.",
                      (_y("suy rộng/giá trị ngoại", r"suy rộng|khái quát|giá trị ngoại|tính đại diện|áp dụng cho",
                          de_muc=True),)),
    ("22", "chung"): (("kinh_phi", "bia", "dao_duc"), "bat_buoc",
                      "Nêu nguồn kinh phí và vai trò của đơn vị tài trợ.",
                      (_y("nguồn kinh phí", r"kinh phí|nguồn (tài trợ|kinh phí)"),
                       _y("vai trò của đơn vị tài trợ",
                          r"vai trò (của )?(nhà |đơn vị )?tài trợ|không tham gia (vào )?(thiết kế|phân tích)|"
                          r"độc lập với|"
                          r"không can thiệp vào (thiết kế|phân tích|công bố)|tự túc|không có (nhà |đơn vị )?tài trợ|"
                          r"không đề nghị cấp kinh phí")), None, "", True),
}

# ─────────────── RECORD 2015 (khi dùng dữ liệu thu thập thường quy) ───────────────
_RECORD_TIEU_CHI: Dict[str, tuple] = {
    "1.1": ((), "bao_cao", "Tiêu đề/tóm tắt nêu loại dữ liệu và tên cơ sở dữ liệu.", ()),
    "1.2": ((), "bao_cao", "Tiêu đề/tóm tắt nêu vùng địa lý và khung thời gian.", ()),
    "1.3": ((), "bao_cao", "Tiêu đề/tóm tắt nêu việc liên kết cơ sở dữ liệu (nếu có).", ()),
    "6.1": (("doi_tuong", "chon_mau", "danh_muc_ma", "quy_trinh"), "bat_buoc",
            "Liệt kê chi tiết cách xác định quần thể từ dữ liệu (mã, điều kiện lọc, thuật toán).",
            (_y("mã/điều kiện lọc", r"\bICD|mã (bệnh|chẩn đoán|thuốc|xét nghiệm|ATC)|điều kiện lọc|truy vấn|"
                                    r"thuật toán"),),
            CHON_TU_CSDL, "quần thể được chọn từ cơ sở dữ liệu"),
    "6.2": (("doi_tuong", "danh_muc_ma", "sai_so", "bien_so"), "bat_buoc",
            "Dẫn nghiên cứu kiểm định mã/thuật toán chọn quần thể, hoặc mô tả cách tự kiểm định (vd đối chiếu mẫu hồ"
            " sơ).",
            (_y("kiểm định mã/thuật toán", r"(kiểm định|thẩm định|xác thực|đối chiếu|kiểm tra chéo).{0,80}"
                                           r"(mã|thuật toán|"
                                          r"hồ sơ)|(mã|thuật toán).{0,80}(kiểm định|thẩm định)|"
                                          r"độ (nhạy|đặc hiệu|chính xác) của (mã|thuật toán)"),),
            r"\bICD|mã (bệnh|chẩn đoán|thuốc|ATC)|thuật toán", "chọn quần thể bằng mã/thuật toán"),
    "6.3": (("quy_trinh", "du_kien_kq"), "ke_hoach", "Liên kết dữ liệu: dùng sơ đồ mô tả quá trình liên kết.",
            (_y("sơ đồ liên kết", r"sơ đồ|lưu đồ"),), LIEN_KET, "có liên kết cơ sở dữ liệu"),
    "7.1": (("bien_so", "bang_bien", "danh_muc_ma", "cong_cu"), "bat_buoc",
            "Cung cấp danh mục đầy đủ mã và thuật toán phân loại phơi nhiễm, kết cục, nhiễu lấy từ dữ liệu thường quy.",
            (_y("danh mục mã", r"danh mục mã|\bICD|mã (ATC|thuốc|xét nghiệm|bệnh)", khi=MA_CHUAN),
             _y("thuật toán/quy tắc phân loại", r"thuật toán|quy tắc (xác định|phân loại)|định nghĩa vận hành|"
                                              r"(được )?xác định (khi|bằng|là|theo)|bằng 1 khi|nhận giá trị|"
                                              r"khoảng thời gian.{0,60}từ .{0,160}đến"))),
    "12.1": (("quan_ly_dl", "cong_cu", "quy_trinh", "dao_duc"), "bat_buoc",
             "Nêu mức độ nhóm nghiên cứu được truy cập cơ sở dữ liệu dùng để tạo quần thể.",
             (_y("quyền truy cập dữ liệu", r"(quyền|được (cấp|phép)) truy cập|"
                                           r"truy xuất|người trích xuất|phân quyền"),)),
    "12.2": (("quan_ly_dl", "phan_tich", "quy_trinh"), "bat_buoc", "Nêu phương pháp làm sạch dữ liệu.",
             (_y("làm sạch dữ liệu", r"làm sạch|kiểm tra (logic|tính hợp lệ|phạm vi)|giá trị (ngoại lai|bất thường)|"
                                    r"trùng lặp"),)),
    "12.3": (("quan_ly_dl", "quy_trinh"), "bat_buoc", "Nêu loại liên kết dữ liệu (cá nhân/cơ sở) và cách đánh giá"
                                                      " chất lượng liên kết.",
             (_y("mức liên kết", r"mức (cá nhân|cơ sở|người bệnh)|theo (mã|định danh) (người bệnh|bệnh nhân)"),
              _y("chất lượng liên kết", r"chất lượng (liên kết|ghép nối)|tỷ lệ (ghép|liên kết) (được|thành công)")),
             LIEN_KET, "có liên kết cơ sở dữ liệu"),
    "13.1": (("du_kien_kq", "quy_trinh", "chon_mau", "bien_so"), "ke_hoach",
             "Lên kế hoạch mô tả chọn quần thể, gồm lọc theo chất lượng và sẵn có của dữ liệu.",
             (_y("lọc theo chất lượng/sẵn có", r"(thiếu|không đủ|không có) (dữ liệu|xét nghiệm|kết quả)|"
                                               r"chất lượng dữ liệu|"
                                             r"bị loại|không ghép được|tỷ lệ (không )?ghép"),)),
    "19.1": (("han_che", "sai_so"), "ke_hoach",
             "Bàn hệ quả của việc dùng dữ liệu không được tạo ra cho câu hỏi nghiên cứu: phân loại sai, nhiễu không đo,"
             " dữ liệu thiếu.",
             (_y("dữ liệu không thu thập cho nghiên cứu", r"(không|chưa) (được )?(thu thập|ghi nhận|tạo) (cho|vì|nhằm)|"
                                                         r"thu thập thường quy|mục đích (lâm sàng|quản lý)|"
                                                         r"ghi nhận (thiếu|"
                                                         r"không đầy đủ)"),
              _y("phân loại sai/nhiễu không đo/thiếu", r"phân loại sai|sai (mã|phân loại)|nhiễu (không|chưa) đo|"
                                                      r"(dữ liệu|số liệu) thiếu"))),
    "22.1": (("pho_bien", "quan_ly_dl"), "bat_buoc",
             "Nêu cách tiếp cận đề cương, dữ liệu thô hoặc mã phân tích.",
             (_y("tài liệu được chia sẻ", r"đề cương|mã (phân tích|lập trình|lệnh|R)|script|dữ liệu (gốc|thô)|"
                                        r"bộ dữ liệu"),
              _y("cách tiếp cận", r"cung cấp|chia sẻ|truy cập|công bố|lưu (trữ|tại)|theo yêu cầu"))),
}

# ─────────────── CROSS 2021 (khảo sát bằng bộ câu hỏi) — KHÔNG lưu nguyên văn (© SGIM) ───────────────
# Chỉ các mục BỔ SUNG so với STROBE; mục trùng (thiết kế, đối tượng, khung thời gian, kết quả, hạn chế…) đã kiểm ở
# STROBE.
_CROSS_TIEU_CHI: Dict[str, tuple] = {
    "5a": ("Questionnaire description", ("cong_cu", "phieu"), "bat_buoc",
           "Mô tả bộ câu hỏi: số phần, số câu và tên các công cụ dùng.",
           (_y("số phần/số câu", r"\d+\s*(phần|câu|mục)"), _y("tên công cụ/nguồn bộ câu hỏi",
                                                              r"Mẫu số|Quyết định|thang|bộ câu hỏi (của|theo|dựa)"))),
    "5b": ("Instruments: validity and scoring", ("cong_cu",), "bat_buoc",
           "Với mỗi công cụ đo: quần thể mục tiêu, độ giá trị/độ tin cậy đã báo cáo, cách chấm điểm, nguồn tham chiếu.",
           (_y("cách chấm điểm/phân loại", r"cách tính điểm|chấm điểm|điểm (trung bình|tổng)|thang (Likert|\d)"),
            _y("độ giá trị/độ tin cậy", r"độ (giá trị|tin cậy)|Cronbach|\bCVI\b|kiểm định"),
            _y("nguồn tham chiếu", r"\[\d+"))),
    "5c": ("Pretesting", ("cong_cu", "quy_trinh"), "bat_buoc",
           "Mô tả thử nghiệm trước bộ câu hỏi: phương pháp, số lần, số người và đặc điểm người thử.",
           (_y("phương pháp thử trước", r"thử nghiệm|khảo sát thử|chạy thử|phỏng vấn nhận thức|pilot"),
            _y("số người thử", r"\d+\s*(người|đối tượng|người bệnh)"))),
    "5d": ("Full questionnaire provided", ("phieu",), "bat_buoc", "Cung cấp toàn bộ bộ câu hỏi (phụ lục).",
           (_y("phụ lục bộ câu hỏi", r"PHIẾU|BỘ CÂU HỎI|câu\s*[A-Z]?\d", de_muc=True),)),
    "6b": ("Sampling technique", ("chon_mau",), "bat_buoc",
           "Mô tả kỹ thuật chọn mẫu; chọn mẫu cụm thì nêu nơi lấy mẫu của từng cụm.",
           (_y("kỹ thuật chọn mẫu", r"ngẫu nhiên|hệ thống|thuận tiện|phân tầng|cụm|liên tiếp|toàn bộ"),)),
    "6d": ("Representativeness", ("chon_mau", "han_che", "sai_so"), "bat_buoc",
           "Nêu mức độ đại diện của mẫu cho quần thể nghiên cứu.",
           (_y("tính đại diện", r"đại diện|suy rộng|khái quát"),)),
    "7a": ("Mode of administration", ("quy_trinh", "cong_cu"), "bat_buoc",
           "Nêu hình thức phát phiếu, số lần liên hệ và nơi thực hiện khảo sát.",
           (_y("hình thức phát phiếu", r"tự điền|phỏng vấn|trực tuyến|phát phiếu|điều tra viên"),
            _y("nơi khảo sát", r"tại (khu vực|phòng|quầy|khoa|bàn)|nơi (khảo sát|phát phiếu)|khu vực"))),
    "7c": ("Data entry", ("quan_ly_dl", "quy_trinh", "sai_so"), "bat_buoc",
           "Nêu biện pháp giảm lỗi nhập liệu (khảo sát giấy) hoặc chống tham gia nhiều lần (khảo sát trực tuyến).",
           (_y("giảm lỗi nhập liệu/chống trùng", r"nhập liệu kép|nhập (hai|2) lần|kiểm tra (nhập liệu|logic)|"
                                                r"chống (trùng|tham gia nhiều lần)|đối chiếu"),)),
    "8": ("Study preparation", ("quy_trinh", "sai_so"), "bat_buoc",
          "Mô tả chuẩn bị trước khảo sát (tập huấn điều tra viên, thông báo khảo sát).",
          (_y("tập huấn/chuẩn bị", r"tập huấn|huấn luyện|hướng dẫn điều tra viên|chuẩn bị"),)),
    "9a": ("Ethical approval and consent", ("dao_duc",), "bat_buoc",
           "Nêu chấp thuận của Hội đồng Đạo đức và đồng thuận tham gia.",
           (_y("Hội đồng Đạo đức", r"Hội đồng (Đạo đức|đạo đức)"),
            _y("đồng thuận", r"đồng (ý|thuận)|tự nguyện"))),
    "9c": ("Anonymity and confidentiality", ("dao_duc", "quan_ly_dl"), "bat_buoc",
           "Nêu tính ẩn danh, bảo mật và cơ chế chống truy cập trái phép.",
           (_y("ẩn danh/bảo mật", r"ẩn danh|bảo mật|khử định danh|mã hoá|mã hóa"),
            _y("chống truy cập trái phép", r"mật khẩu|phân quyền|quyền truy cập|tủ có khoá|tủ có khóa|"
                                           r"chỉ (nghiên cứu viên|"
                                          r"chủ nhiệm)"))),
    "10a": ("Statistical methods and software", ("phan_tich",), "bat_buoc",
            "Mô tả phương pháp thống kê và phần mềm phân tích.",
            (_y("phần mềm", r"phần mềm|\bSPSS\b|\bStata\b|\bSAS\b|\bR\s*(phiên bản|\d)|\bR\b"),)),
    "10b": ("Variable modification", ("phan_tich", "cong_cu", "bien_so"), "bat_buoc",
            "Nêu mọi biến đổi biến dùng trong phân tích (gộp mức, tính điểm, nhị phân hoá) kèm căn cứ.",
            (_y("biến đổi biến", r"gộp|nhị phân|mã hoá lại|mã hóa lại|tính điểm|chuyển (thành|đổi)|"
                                 r"định nghĩa “?hài lòng"),)),
    "10c": ("Missing data", ("phan_tich",), "bat_buoc",
            "Nêu tỷ lệ thiếu, cơ chế thiếu (MCAR/MAR/MNAR) và phương pháp xử lý.",
            (_y("cơ chế thiếu", r"\bMCAR\b|\bMAR\b|\bMNAR\b|ngẫu nhiên hoàn toàn|thiếu ngẫu nhiên|cơ chế|"
                                r"kiểu dữ liệu thiếu"),
             _y("phương pháp xử lý", r"đa quy|điền khuyết|multiple imputation|MICE|ca đầy đủ|trường hợp đủ dữ liệu|"
                                    r"complete case|gán")), None, "", True),
    "10d": ("Non-response error", ("phan_tich", "sai_so", "quy_trinh"), "bat_buoc",
            "Nêu cách xử lý sai số do không trả lời.",
            (_y("không trả lời/từ chối", r"không (trả lời|đáp ứng|tham gia)|từ chối|tỷ lệ đáp ứng"),)),
    "10e": ("Loss to follow-up (longitudinal)", ("phan_tich",), "bat_buoc",
            "Khảo sát dọc: nêu cách xử lý mất theo dõi.",
            (_y("mất theo dõi", r"mất theo dõi"),), THEO_DOI_DOC, "khảo sát dọc"),
    "10f": ("Weighting for non-representativeness", ("phan_tich",), "bat_buoc",
            "Nêu việc dùng trọng số/điểm xu hướng để điều chỉnh mẫu không đại diện, hoặc nêu rõ không dùng và lý do.",
            (_y("trọng số/điều chỉnh", r"trọng số|điểm xu hướng|propensity|hậu phân tầng|"
                                       r"không (dùng|áp dụng) trọng số"),)),
    "10g": ("Sensitivity analysis", ("phan_tich",), "bat_buoc", "Mô tả phân tích độ nhạy.",
            (_y("phân tích độ nhạy", r"phân tích độ nhạy"),)),
    "11c": ("Response rate", ("du_kien_kq", "phan_tich", "quy_trinh"), "ke_hoach",
            "Lên kế hoạch báo cáo tỷ lệ đáp ứng kèm định nghĩa hoặc công thức tính.",
            (_y("tỷ lệ đáp ứng", r"tỷ lệ (đáp ứng|trả lời|tham gia)"),
             _y("định nghĩa/công thức", r"=|/\s*(tổng )?số|chia|trên tổng|công thức|được tính|định nghĩa")),
             None, "", True),
    "11d": ("Unique visitors (web)", ("phan_tich", "quy_trinh"), "ke_hoach",
            "Khảo sát trực tuyến: định nghĩa người truy cập duy nhất và các tỷ lệ xem/tham gia/hoàn thành.",
            (_y("người truy cập duy nhất", r"duy nhất|truy cập"),), TRUC_TUYEN, "khảo sát trực tuyến"),
    "13b": ("Model building and fit", ("phan_tich",), "bat_buoc",
            "Phân tích đa biến: nêu quá trình dựng mô hình, chỉ số phù hợp và giả định của mô hình.",
            (_y("dựng mô hình/chọn biến", r"chọn biến|đưa vào mô hình|\bDAG\b|dựng mô hình|xây dựng mô hình"),
             _y("độ phù hợp/giả định", r"phù hợp|giả định|Hosmer|Brant|đa cộng tuyến|\bVIF\b|tỷ lệ chênh tỷ lệ")),
            r"đa biến|hồi quy", "có phân tích đa biến", True),
    "17": ("Role of funder", ("kinh_phi", "bia", "dao_duc"), "bat_buoc",
           "Nêu vai trò của tổ chức tài trợ trong thiết kế, thực hiện và phân tích.",
           (_y("vai trò tài trợ", r"vai trò (của )?(nhà |đơn vị )?tài trợ|không tham gia (vào )?(thiết kế|phân tích)|"
                                 r"độc lập với|không can thiệp vào (thiết kế|phân tích|công bố)|tự túc|"
                                 r"không có (nhà |đơn vị )?tài trợ|"
                                 r"không đề nghị cấp kinh phí"),)),
    "18": ("Conflict of interest", ("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Khai báo xung đột lợi ích tiềm tàng.",
           (_y("xung đột lợi ích", r"xung đột lợi ích"),)),
}

# ─────────────── Chuẩn Việt Nam (mọi thiết kế) ───────────────
# Căn cứ đã đối chiếu nguyên văn ở `can_cu_dao_duc.py` (TT43/2024/TT-BYT Điều 7 khoản 1 điểm b; Điều 16 khoản 6) và
# danh mục chuẩn của G2 (`g2_quality_gate.py`: Luật 91/2025/QH15, Nghị định 356/2025/NĐ-CP).
MIEN_DONG_THUAN = r"miễn (lấy |thu thập )?(sự |phiếu )?đồng (ý|thuận)|MIỄN ĐỒNG THUẬN"
_VN_TIEU_CHI: Dict[str, tuple] = {
    "TT43-HĐĐ": ("Thông tư 43/2024/TT-BYT — chấp thuận của Hội đồng Đạo đức", ("dao_duc",), "bat_buoc",
                 "Nêu đề tài chỉ được thực hiện sau khi Hội đồng Đạo đức chấp thuận.",
                 (_y("chấp thuận của Hội đồng", r"(chấp thuận|thông qua|phê duyệt) của Hội đồng|"
                                                r"Hội đồng (Đạo đức|đạo đức)"
                                               r".{0,80}(chấp thuận|thông qua|phê duyệt)"),), None, ""),
    "TT43-Đ7.1b": ("Thông tư 43/2024/TT-BYT, Điều 7 khoản 1 điểm b — miễn đồng thuận", ("dao_duc",), "bat_buoc",
                   "Xin miễn đồng thuận: nêu căn cứ Điều 7 khoản 1 điểm b và lý do (nguy cơ tối thiểu, không khả thi"
                   " lấy"
                   " đồng thuận).",
                   (_y("căn cứ TT43 Điều 7", r"43/2024.{0,40}Điều 7|Điều 7.{0,40}43/2024"),
                    _y("lý do miễn", r"nguy cơ tối thiểu|không (khả thi|thể liên hệ)|"
                                     r"dữ liệu (sẵn có|hồi cứu)|hồi cứu")),
                   MIEN_DONG_THUAN, "xin miễn đồng thuận"),
    "TT43-ĐỒNG-THUẬN": ("Thông tư 43/2024/TT-BYT — bản thông tin và phiếu đồng ý", ("dao_duc",), "bat_buoc",
                        "Không xin miễn: có bản thông tin cho người tham gia và phiếu tình nguyện/đồng ý.",
                        (_y("bản thông tin + phiếu đồng ý", r"phiếu (đồng ý|tình nguyện|chấp thuận)|bản thông tin"),),
                        "!" + MIEN_DONG_THUAN, "không xin miễn đồng thuận"),
    "TT43-Đ16.6": ("Thông tư 43/2024/TT-BYT, Điều 16 khoản 6 — thẩm định rút gọn", ("dao_duc",), "bat_buoc",
                   "Đề nghị thẩm định rút gọn: nêu nghiên cứu có nguy cơ tối thiểu.",
                   (_y("nguy cơ tối thiểu", r"nguy cơ tối thiểu"),), r"rút gọn", "đề nghị thẩm định rút gọn"),
    "DLCN": ("Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP — bảo vệ dữ liệu cá nhân", ("dao_duc", "quan_ly_dl"),
             "bat_buoc", "Nêu biện pháp bảo vệ dữ liệu cá nhân: khử định danh/mã hoá, giới hạn quyền truy cập, nơi"
                         " lưu trữ.",
             (_y("khử định danh/mã hoá", r"khử định danh|ẩn danh|mã hoá|mã hóa|mã số (thay|nghiên cứu)"),
              _y("giới hạn truy cập", r"quyền truy cập|phân quyền|mật khẩu|"
                                      r"chỉ (nghiên cứu viên|chủ nhiệm|nhóm nghiên cứu)"),
              _y("nơi lưu trữ", r"lưu (trữ|tại)|máy (tính|chủ)|tủ có kho[áa]")), None, ""),
}

# ─────────────── chuẩn theo thiết kế ───────────────
CHUAN_CO_SO: Dict[str, Tuple[str, ...]] = {
    "cross_sectional": ("STROBE 2007",), "cohort": ("STROBE 2007",), "case_control": ("STROBE 2007",),
    "rct": ("SPIRIT 2025",), "systematic_review": ("PRISMA-P 2015",), "diagnostic": ("STARD 2015",),
    "prediction": ("TRIPOD+AI 2024",), "qualitative": ("COREQ 2007", "SRQR 2014"), "mixed_methods": ("GRAMMS 2008",),
    "quality_improvement": ("SQUIRE 2.0",), "economic": ("CHEERS 2022",), "non_randomized": ("TREND 2004",),
    "case_report": ("CARE 2013",),
}
#: Chuẩn có điều kiện: (tên, biểu thức trên cả đề cương, lý do).
CHUAN_DIEU_KIEN: Tuple[Tuple[str, str, str], ...] = (
    ("RECORD 2015", DU_LIEU_THUONG_QUY, "dùng dữ liệu thu thập thường quy (HIS/hồ sơ bệnh án điện tử)"),
    ("CROSS 2021", KHAO_SAT, "khảo sát bằng bộ câu hỏi"),
    ("COSMIN 2021", (KHAO_SAT, CONG_CU_DO), "phát triển hoặc kiểm định bộ câu hỏi/thang đo"),
)
_KHONG_NGUOI_THAM_GIA = frozenset({"systematic_review"})
NGUON_CHUAN: Dict[str, str] = {
    "STROBE 2007": "von Elm E et al. PLoS Med 2007;4(10):e296 (PMID 17941714); E&E PMID 17941715",
    "RECORD 2015": "Benchimol EI et al. PLoS Med 2015;12(10):e1001885 (PMID 26440803)",
    "CROSS 2021": "Sharma A et al. J Gen Intern Med 2021;36(10):3179-3187 (PMID 33886027)",
    "COSMIN 2021": "Gagnier JJ et al. Qual Life Res 2021;30(8):2197-2218 (PMID 33818733)",
}


def _muc_strobe(thiet_ke: str) -> List[MucKiem]:
    tk = _TK_STROBE.get(thiet_ke, "")
    ra = []
    for ma, loai, chu_de, van in CBC.STROBE_2007_ITEMS:
        if loai not in ("chung", tk):
            continue
        tc = _STROBE_TIEU_CHI[(ma, loai)]
        phan, muc_do, tieu_chi, yeu_to = tc[:4]
        khi, ly_do = (tc[4], tc[5]) if len(tc) > 4 else (None, "")
        cung = bool(tc[6]) if len(tc) > 6 else False
        ra.append(MucKiem("STROBE 2007", ma, chu_de, van, tieu_chi, tuple(phan), tuple(yeu_to), muc_do, khi, ly_do,
                          cung))
    return ra


def _muc_record() -> List[MucKiem]:
    van = dict(CBC.RECORD_2015_ITEMS)
    ra = []
    for ma, tc in _RECORD_TIEU_CHI.items():
        phan, muc_do, tieu_chi, yeu_to = tc[:4]
        khi, ly_do = (tc[4], tc[5]) if len(tc) > 4 else (None, "")
        ra.append(MucKiem("RECORD 2015", ma, "RECORD " + ma, van[ma], tieu_chi, tuple(phan), tuple(yeu_to), muc_do, khi,
                          ly_do))
    return ra


def _muc_bang(chuan: str, bang: Dict[str, tuple]) -> List[MucKiem]:
    ra = []
    for ma, tc in bang.items():
        chu_de, phan, muc_do, tieu_chi, yeu_to = tc[:5]
        khi, ly_do = (tc[5], tc[6]) if len(tc) > 5 else (None, "")
        cung = bool(tc[7]) if len(tc) > 7 else False
        ra.append(MucKiem(chuan, ma, chu_de, None, tieu_chi, tuple(phan), tuple(yeu_to), muc_do, khi, ly_do, cung))
    return ra


def chuan_ap_dung(thiet_ke: str, md: str) -> List[Tuple[str, str]]:
    """[(tên chuẩn, lý do áp dụng)] cho thiết kế và nội dung đề cương."""
    ma = S.canonical_design_code(thiet_ke) or ""
    ra = [(c, f"thiết kế {ma}") for c in CHUAN_CO_SO.get(ma, ())]
    if not ra:
        ra.append(("(không xác định)", f"mã thiết kế «{thiet_ke}» ngoài bảng chuẩn"))
    if ma in _KHONG_NGUOI_THAM_GIA:
        # Tổng quan hệ thống: dữ liệu là các nghiên cứu đã công bố — không có người tham gia, không dữ liệu thường quy.
        return ra
    for ten, mau, ly_do in CHUAN_DIEU_KIEN:
        if all(co_dieu_kien(m, md) for m in ((mau,) if isinstance(mau, str) else mau)):
            ra.append((ten, ly_do))
    ra.append(("Việt Nam", "mọi đề tài có người tham gia thực hiện tại Việt Nam"))
    return ra


# ───────────────────────────── chấm ─────────────────────────────
_PHU_DINH_TRUOC = re.compile(r"\b(không|chưa|ngoài phạm vi)\b[^.;:|]{0,60}$", re.IGNORECASE)
_PHU_DINH_SAU = re.compile(r"^[^.;|]{0,160}(không áp dụng|ngoài phạm vi)", re.IGNORECASE)


def co_dieu_kien(mau: str, md: str) -> bool:
    """Điều kiện có mặt THẬT ở đề cương: bỏ lần khớp nằm trong câu phủ định («Không có phân tích phân nhóm…»,
    «… bộ câu hỏi … — không áp dụng»). Câu phủ định từng làm bộ kiểm đòi mục không áp dụng (21/11/2026)."""
    for m in re.finditer(mau, md, _C):
        dau = md.rfind("\n", 0, m.start()) + 1
        cuoi = md.find("\n", m.end())
        truoc, sau = md[dau:m.start()], md[m.end():cuoi if cuoi >= 0 else len(md)]
        if _PHU_DINH_TRUOC.search(truoc) or _PHU_DINH_SAU.search(sau):
            continue
        # nhãn của ô còn trống («Ghép cặp: ………») không phải quyết định đã có (21/11/2026)
        if o_trong_quanh(truoc + m.group(0) + sau, len(truoc)):
            continue
        return True
    return False


_DE_MUC_MUC_TIEU = re.compile(r"^(?:[\dIVX]+(?:\.\d+)*\.?\s+)?(?:MỤC TIÊU|Câu hỏi|Giả thuyết)", re.IGNORECASE)


def dieu_kien(mau: str, md: str, cac_phan: Optional[Sequence[Phan]] = None) -> bool:
    """`co_dieu_kien` với phạm vi: tiền tố «@muc_tieu:» ⇒ chỉ xét các khối có đề mục BẮT ĐẦU bằng «Mục tiêu»/«Câu hỏi»/
    «Giả thuyết» (không lấy «Bàn luận theo mục tiêu k» hay «Kết quả theo mục tiêu k» của chương kết quả)."""
    if mau.startswith("@muc_tieu:"):
        cac_phan = cac_phan if cac_phan is not None else tach_phan(md)
        van = "\n".join(p.van for p in cac_phan if p.tieu_de != "(bìa)" and _DE_MUC_MUC_TIEU.match(p.tieu_de))
        return co_dieu_kien(mau[len("@muc_tieu:"):], van)
    return co_dieu_kien(mau, md)


def _don_vi(p: Phan, de_muc: bool = False) -> List[Tuple[int, str]]:
    """Đoạn văn của khối: [(số dòng đầu, chữ)]. Dòng đề mục bị bỏ (trừ khi `de_muc`). Mỗi dòng bảng là một đơn vị,
    kèm hàng tiêu đề cột ở cuối (cột «Biện pháp khống chế» cho nghĩa của ô trong dòng)."""
    ra: List[Tuple[int, str]] = []
    gom: List[str] = []
    dau = 0
    tieu_de_bang = ""
    dong = p.van.split("\n")
    ngan = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")
    for i, d in enumerate(dong):
        so = p.dong_dau + i
        la_bang = d.lstrip().startswith("|")
        if not la_bang:
            tieu_de_bang = ""
        if not d.strip() or _DE_MUC_RE.match(d) or la_bang:
            if gom:
                ra.append((dau, "\n".join(gom)))
                gom = []
            if la_bang and not ngan.match(d):
                if not tieu_de_bang and i + 1 < len(dong) and ngan.match(dong[i + 1]):
                    # Hàng tiêu đề cột (ngay sau là hàng ngăn «|---|») chỉ cho nghĩa của ô ở các hàng dưới — KHÔNG là
                    # bằng chứng nội dung (21/11/2026: bảng «| Hạn chế | Chiều hướng sai lệch |» với mọi ô để trống từng
                    # làm STROBE 19 «đạt»). Bảng khoá–giá trị không có hàng ngăn: hàng đầu là dữ liệu.
                    tieu_de_bang = d
                else:
                    ra.append((so, d + (f"\t⟦{tieu_de_bang}⟧" if tieu_de_bang else "")))
            elif de_muc and _DE_MUC_RE.match(d):
                ra.append((so, d))
            continue
        if not gom:
            dau = so
        gom.append(d)
    if gom:
        ra.append((dau, "\n".join(gom)))
    return ra


#: Ô trống để chủ nhiệm điền tay («………», «……………», «.....»). Dòng còn ô trống KHÔNG làm bằng chứng cho yếu tố nào
#: (21/11/2026): nhãn có mặt ≠ nội dung có mặt — «Lý do chọn nhóm bệnh và nhóm chứng: ………» từng đủ để «lý do» được
#: tính là đạt; hàng bảng sai lệch có ô «Chiều ảnh hưởng» bỏ trống vẫn mượn chữ «chiều» của hàng tiêu đề cột.
O_TRONG_RE = re.compile(r"…{3,}|\.{5,}")
_HET_CAU_RE = re.compile(r"[.!?]\s+(?=\S)")


def o_trong_quanh(dong: str, vt: int) -> bool:
    """Lần khớp ở vị trí `vt` của `dong` (có thể kèm «\\t⟦tiêu đề cột⟧») nằm trong mệnh đề còn ô trống: mệnh đề = đoạn
    giữa «|», «;» hoặc ranh giới câu. Khớp ở tiêu đề cột ⇒ xét cả hàng (ô của cột đó có thể là ô trống). Câu thật kèm
    ô số quyết định để trống ở câu SAU («… sau khi có quyết định phê duyệt của Hội đồng. Số quyết định: ………», C1a) vẫn
    là bằng chứng."""
    than = dong.split("\t⟦")[0]
    if vt >= len(than):
        return bool(O_TRONG_RE.search(than))
    dau = max([than.rfind("|", 0, vt), than.rfind(";", 0, vt)]
              + [m.end() - 1 for m in _HET_CAU_RE.finditer(than, 0, vt)]) + 1
    cuoi = [i for i in (than.find("|", vt), than.find(";", vt)) if i >= 0]
    m = _HET_CAU_RE.search(than, vt)
    if m:
        cuoi.append(m.start())
    return bool(O_TRONG_RE.search(than[dau:min(cuoi) if cuoi else len(than)]))


def _tim(mau: str, don_vi: Sequence[Tuple[int, str]]) -> Optional[str]:
    """Bằng chứng «dòng N: «…»» của lần khớp đầu tiên trong các đơn vị; None nếu không khớp. Bỏ qua lần khớp nằm trong
    mệnh đề còn ô trống cho chủ nhiệm điền (`o_trong_quanh`)."""
    for so, chu in don_vi:
        for m in re.finditer(mau, chu, _C):
            vi_tri = m.start() + (len(m.group(0)) - len(m.group(0).lstrip()))
            n = chu.count("\n", 0, vi_tri)
            dong_day = chu.split("\n")[n]
            if o_trong_quanh(dong_day, vi_tri - (chu.rfind("\n", 0, vi_tri) + 1)):
                continue
            return f"dòng {so + n}: «{dong_day.split(chr(9) + '⟦')[0].strip()[:140]}»"
    return None


def cham_muc(muc: MucKiem, md: str, cac_phan: Sequence[Phan]) -> KetQua:
    """Chấm một mục trên đề cương."""
    kq = KetQua(muc.chuan, muc.ma, muc.chu_de, muc.tieu_chi, muc.muc_do, "dat", nguyen_van=muc.nguyen_van)
    if muc.muc_do == "bao_cao":
        kq.trang_thai, kq.ly_do = "bao_cao", "chỉ áp khi viết bài báo"
        return kq
    if muc.ap_dung_khi:
        # Tiền tố «!» = áp dụng khi biểu thức KHÔNG khớp ở cả đề cương.
        phu_dinh = muc.ap_dung_khi.startswith("!")
        co = dieu_kien(muc.ap_dung_khi[1:] if phu_dinh else muc.ap_dung_khi, md, cac_phan)
        if co == phu_dinh:
            kq.trang_thai, kq.ly_do = "khong_ap_dung", f"đề cương không có điều kiện: {muc.ly_do_dieu_kien}"
            return kq
    khoi = khoi_cua(cac_phan, muc.phan)
    kq.vi_tri = [f"dòng {p.dong_dau}: {p.tieu_de}" for p in khoi]
    if not khoi:
        kq.trang_thai = "thieu"
        kq.thieu = [f"không thấy phần đề cương cho mục này ({', '.join(muc.phan)})"]
        return kq
    can = [yt for yt in muc.yeu_to if not (yt.khi and not dieu_kien(yt.khi, md, cac_phan))]
    don_vi = [dv for p in khoi for dv in _don_vi(p)]
    don_vi_dm = [dv for p in khoi for dv in _don_vi(p, de_muc=True)]
    if muc.cung_doan and len(can) > 1:
        tot_nhat: Tuple[int, List[str], List[str]] = (-1, [], [y.ten for y in can])
        for dv in don_vi:
            co, thieu = [], []
            for yt in can:
                bc = _tim(yt.mau, [dv])
                (co.append(f"{yt.ten} — {bc}") if bc else thieu.append(yt.ten))
            if len(co) > tot_nhat[0]:
                tot_nhat = (len(co), co, thieu)
            if not thieu:
                break
        _, kq.bang_chung, thieu = tot_nhat
        kq.thieu = [f"{t} (phải cùng đoạn/dòng bảng với các yếu tố còn lại)" for t in thieu]
    else:
        for yt in can:
            bc = _tim(yt.mau, don_vi_dm if yt.de_muc else don_vi)
            (kq.bang_chung.append(f"{yt.ten} — {bc}") if bc else kq.thieu.append(yt.ten))
    if kq.thieu:
        kq.trang_thai = "thieu"
    return kq


def dieu_kien_muc(chuan: str, ma: str, thiet_ke: str = "") -> Optional[str]:
    """Biểu thức «áp dụng khi» của một mục — để bộ sinh đề cương dùng ĐÚNG điều kiện của K17 (không chép lại biểu
    thức)."""
    for m in danh_sach_muc(chuan, thiet_ke) or []:
        if m.ma == ma:
            return m.ap_dung_khi
    return None


def danh_sach_muc(chuan: str, thiet_ke: str) -> Optional[List[MucKiem]]:
    """Mục kiểm của một chuẩn; None khi chuẩn chưa có tiêu chí tự động."""
    ma = S.canonical_design_code(thiet_ke) or ""
    if chuan == "STROBE 2007":
        return _muc_strobe(ma)
    if chuan == "RECORD 2015":
        return _muc_record()
    if chuan == "CROSS 2021":
        return _muc_bang("CROSS 2021", _CROSS_TIEU_CHI)
    if chuan == "Việt Nam":
        return _muc_bang("Việt Nam", _VN_TIEU_CHI)
    return None


def doi_chieu(md: str, thiet_ke: str) -> Dict[str, object]:
    """Đối chiếu đầy đủ: {'chuan': [...], 'ket_qua': [KetQua], 'chua_do': [(chuẩn, lý do)]}."""
    md = unicodedata.normalize("NFC", md)
    cac_phan = tach_phan(md)
    ap_dung = chuan_ap_dung(thiet_ke, md)
    ket_qua: List[KetQua] = []
    chua_do: List[Tuple[str, str]] = []
    for chuan, _ly_do in ap_dung:
        muc = danh_sach_muc(chuan, thiet_ke)
        if muc is None:
            chua_do.append((chuan, "chuẩn chưa có tiêu chí kiểm tự động theo mục — KHÔNG ĐO ĐƯỢC, không tính là đạt"))
            continue
        ket_qua += [cham_muc(m, md, cac_phan) for m in muc]
    return {"chuan": ap_dung, "ket_qua": ket_qua, "chua_do": chua_do}


def loi_k17(md: str, thiet_ke: str) -> List[str]:
    """Lỗi K17 cho bộ kiểm đề cương nộp: mục bắt buộc/kế hoạch còn thiếu yếu tố."""
    kq = doi_chieu(md, thiet_ke)
    loi = []
    for r in kq["ket_qua"]:
        if r.trang_thai == "thieu":
            loi.append(f"K17 {r.chuan} mục {r.ma} ({r.chu_de}) thiếu: {'; '.join(r.thieu)} — {r.tieu_chi}")
    return loi


# ───────────────────────────── CLI ─────────────────────────────
def _thiet_ke_cua(out_dir: Path) -> str:
    try:
        meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
        return str(((meta.get("gate_params") or {}).get("G1") or {}).get("design") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu đề cương với từng mục của chuẩn quốc tế và Việt Nam (K17).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--tep", type=Path, help="tệp Markdown (mặc định: đề cương nộp Hội đồng của đề tài)")
    ap.add_argument("--thiet-ke", help="ghi đè mã thiết kế (mặc định: study_meta gate_params.G1.design)")
    ap.add_argument("--chi-tiet", action="store_true", help="in cả bằng chứng của mục đạt")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 3
    out_dir = BASE / "exports" / a.study
    tep = a.tep or out_dir / f"DE_CUONG_NOP_HOI_DONG_{a.study}.md"
    if not tep.is_file():
        print(f"Không thấy đề cương: {tep}")
        return 2
    thiet_ke = a.thiet_ke or _thiet_ke_cua(out_dir)
    kq = doi_chieu(tep.read_text(encoding="utf-8"), thiet_ke)
    kqs: List[KetQua] = kq["ket_qua"]
    thieu = [r for r in kqs if r.trang_thai == "thieu"]
    if a.json:
        print(json.dumps({"study": a.study, "thiet_ke": thiet_ke, "chuan": kq["chuan"], "chua_do": kq["chua_do"],
                          "ket_qua": [asdict(r) for r in kqs]}, ensure_ascii=False, indent=1))
        return 1 if thieu else 0
    print(f"Đối chiếu chuẩn theo mục — {a.study} (thiết kế: {thiet_ke or 'chưa ghi'})")
    for ten, ly_do in kq["chuan"]:
        nhom = [r for r in kqs if r.chuan == ten]
        dem = {t: sum(r.trang_thai == t for r in nhom) for t in ("dat", "thieu", "khong_ap_dung", "bao_cao")}
        if ten in dict(kq["chua_do"]):
            print(f"  ⚪ {ten} — {ly_do}: CHƯA ĐO ĐƯỢC (chưa có tiêu chí theo mục)")
            continue
        dau = "✓" if not dem["thieu"] else "✗"
        print(f"  {dau} {ten} — {ly_do}: đạt {dem['dat']} · thiếu {dem['thieu']} · không áp dụng {dem['khong_ap_dung']}"
              f" · chỉ áp khi viết bài báo {dem['bao_cao']}")
    for r in thieu:
        print(f"\n✗ {r.chuan} {r.ma} ({r.chu_de}) — {r.tieu_chi}\n    thiếu: {'; '.join(r.thieu)}")
        if r.vi_tri:
            print(f"    đã tìm ở: {' | '.join(r.vi_tri[:4])}")
        for b in r.bang_chung:
            print(f"    có: {b}")
    if a.chi_tiet:
        for r in kqs:
            if r.trang_thai == "dat":
                print(f"\n✓ {r.chuan} {r.ma} ({r.chu_de})")
                for b in r.bang_chung:
                    print(f"    {b}")
    print("\nĐẠT = có đủ yếu tố trong đúng phần; chất lượng nội dung vẫn cần đọc bằng chứng. Cần bác sĩ kiểm chứng.")
    return 1 if thieu else 0


if __name__ == "__main__":
    sys.exit(main())
