#!/usr/bin/env python3
"""Chốt CHUNG «điền sai kiểu» cho mọi văn bản đầu ra của đề tài (23/11/2026, bác sĩ duyệt đề xuất).

VÌ SAO: ba lỗi tồn tại lâu nhất chỉ được agent phát hiện khi ĐỌC, không chốt máy nào bắt:
  · mọi bản thảo giả lập kết thúc §1 Giới thiệu bằng «… [1][2][3]. 2.» (số thứ tự đứng lẻ thành câu);
  · ô «ai thực hiện can thiệp» bị điền «6» (ô hỏi người/vai trò nhận mã số);
  · số chưa làm tròn «2382054.5454545454» (dấu chấm thập phân, quá nhiều chữ số) — bộ kiểm PII còn nhận nhầm là số định
    danh.
Các chốt hiện có đo nội dung theo chuẩn (K17/K18) hoặc trình bày số đo (K11: «0.1», số dính đơn vị) — không đo KIỂU của
giá trị được điền. Chốt này quét kiểu, dùng chung cho đề cương, SAP, bản thảo G7, báo cáo tổng hợp, hồ sơ Hội đồng Đạo
đức/đề tài cơ sở, phiếu thu thập.

LUẬT (mỗi dòng báo tối đa một lỗi mỗi luật):
  Q1 số đứng lẻ thành câu — dòng chỉ có một số thứ tự («2.»), hoặc câu cuối dòng chỉ là một số sau dấu kết câu/trích dẫn
     («… [3]. 2.»).
  Q2 ô hỏi chữ (người, vai trò, chức danh, mô tả…) chứa mã số đơn lẻ — `hoi_chu` (gồm `hoi_nguoi_vai_tro` của agent
     G7) + `la_ma_so_don_le`, một bản duy nhất ở đây; bộ giả lập trọn vòng nhập từ mô-đun này.
  Q3 số thập phân từ 5 chữ số lẻ trở lên — chưa làm tròn (văn xuôi lẫn ô bảng).
  Q4 dấu chấm thập phân trong câu tiếng Việt («1.46», «0.70», «-0.0187») — trừ nhóm nghìn («10.000»; nhưng ngay sau ký
     hiệu ước lượng «OR = 2.783» là thập phân), số hiệu tham chiếu («mục 4.1», «§3.4–3.5», «khuyến cáo 11.8», «RECORD
     12.2»), đánh số đầu dòng và đầu ô bảng, phiên bản («R ≥ 4.3», «`survey` ≥ 4.5», «Phiên bản: 1.0»), mã (ICD «E11.9»,
     trong `…`), PMID/DOI/URL, ô công thức («= if(…)», «[ten_bien]»), dòng tiếng Anh (≥ 4 từ tiếng Anh, không dấu tiếng
     Việt — dòng chỉ có số và ký hiệu vẫn theo quy ước tiếng Việt).
Bộ sinh in số bằng `viet_so` (một giá trị) và `viet_hoa_so` (khối số máy chép từ dữ liệu, vd số G6 của bản thảo G7
sau tự kiểm nguyên văn) — cùng phạm vi ngoại lệ với Q3/Q4.
  Q5 câu khuôn còn ký hiệu nội bộ — chỗ giữ chưa thay («{ten_bien}», «@@…@@», «⟦…⟧»), giá trị rỗng của máy («None»,
     «nan», «null»), «TODO/FIXME».
Bỏ qua: danh mục tài liệu tham khảo (giữ nguyên văn nguồn), khối mã ```…```, dòng chuỗi tìm kiếm ([tiab]/[Mesh]…).

Lệnh:  python3 tools/quet_dien_sai_kieu.py --study <mã> [--exports-root …] [--json]
       python3 tools/quet_dien_sai_kieu.py --tep <tệp.md|.docx> …
Mã thoát: 0 sạch · 1 có lỗi · 2 không có văn bản để quét.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent

#: Văn bản đầu ra được quét (tên tệp trong thư mục đề tài) — bản .bak và tệp máy (_dau_may_sinh) không quét
MAU_TEP = ("DE_CUONG_NOP_HOI_DONG_*", "DE_CUONG_THONG_NHAT_*", "G4_A5_SAP_FINAL_*", "G7_A8_MANUSCRIPT_*",
           "G2_A3_ETHICS_PACKAGE_*", "PHIEU_THU_THAP_SO_LIEU_*", "BAO_CAO_TONG_HOP_*")
#: hồ sơ Hội đồng Đạo đức (`ho_so_hdd_bvqy175.py` → ho_so_hdd/) và đề tài cơ sở (`ho_so_dtcs_bvqy175.py` → ho_so_dtcs/)
MAU_TEP_HO_SO = {"ho_so_hdd": ("MAU[2-8]_*", "MIEN_ICF_*", "PHIEU_THU_THAP_SO_LIEU_*", "DANH_MUC_HO_SO_*"),
                 "ho_so_dtcs": ("XDNV01_*", "DKCT0*", "DANH_MUC_HO_SO_*")}


# ══════════════════════════════════════════════════════════ Q2 — một bản duy nhất (agent G7, 23/11/2026)
def hoi_nguoi_vai_tro(nhan_khong_dau: str) -> bool:
    """Ô hỏi NGƯỜI hoặc VAI TRÒ (ai thực hiện, người phụ trách, chức danh, thành viên…) — không phải ô hỏi số lượng
    («số người», «bao nhiêu người»). Nhãn đã bỏ dấu (`bo_dau`)."""
    k = str(nhan_khong_dau or "")
    if re.search(r"\bso\b|bao nhieu|\bty le\b", k):
        return False
    return bool(re.search(r"\bai (thuc hien|phu trach|chiu trach nhiem|danh gia|phong van|nhap|kiem tra|giu)|"
                          r"\bnguoi (thuc hien|phu trach|chiu trach nhiem|danh gia|phong van|kiem tra|giu)|"
                          r"vai tro|chuc danh|chuc vu|thanh vien|ho ten", k))


def hoi_chu(nhan_khong_dau: str) -> bool:
    """Ô hỏi CHỮ — người/vai trò (`hoi_nguoi_vai_tro`) hoặc MÔ TẢ (mô tả, liệt kê, lý do, giải thích, trình bày, nêu rõ,
    diễn giải). Ô hỏi số lượng/thời gian («số…», «bao nhiêu», «tỷ lệ», «thời gian») không tính. Nhãn đã bỏ dấu."""
    k = str(nhan_khong_dau or "")
    if hoi_nguoi_vai_tro(k):
        return True
    if re.search(r"\bso\b|bao nhieu|\bty le\b|thoi gian|\bngay\b|\bthang\b|\bnam\b|\bphien ban\b", k):
        return False
    return bool(re.search(r"\bmo ta\b|\bliet ke\b|\bly do\b|\bgiai thich\b|\btrinh bay\b|\bneu ro\b|\bdien giai\b", k))


def la_ma_so_don_le(gia_tri: Any) -> bool:
    """Giá trị chỉ là một con số (vd «6», «2,5») — không phải câu trả lời cho ô hỏi người/vai trò."""
    return bool(re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", str(gia_tri or "")))


def bo_dau(s: Any) -> str:
    t = unicodedata.normalize("NFD", unicodedata.normalize("NFC", str(s or "")).replace("đ", "d").replace("Đ", "D"))
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn")).strip().lower()


# ══════════════════════════════════════════════════════════ quy ước số dùng chung cho BỘ SINH
#: số chữ số lẻ tối đa của số trong văn bản (Q3 báo từ 5 chữ số lẻ trở lên)
LE_TOI_DA = 4


def viet_so(x: Any, le: Optional[int] = None) -> str:
    """Số theo quy ước văn bản tiếng Việt — bộ sinh văn bản dùng hàm này để không sinh ra lỗi Q3/Q4:
    dấu phẩy thập phân; từ 10.000 trở lên nhóm nghìn bằng dấu chấm (K11); `le` = số chữ số lẻ cố định (quy ước bảng:
    tỷ lệ % 1, tỷ số 2, p 3…), vắng ⇒ giữ đúng chữ số của giá trị (`repr`) nhưng không quá LE_TOI_DA. Không phải số
    (chuỗi, None) ⇒ trả nguyên văn; bool ⇒ nguyên văn (không đổi True thành 1)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    if le is None:
        if isinstance(x, int):
            chuoi = str(x)
        else:
            chuoi = repr(round(x, LE_TOI_DA))
            if "e" in chuoi or "E" in chuoi:
                chuoi = f"{round(x, LE_TOI_DA):.{LE_TOI_DA}f}".rstrip("0").rstrip(".")
            if chuoi.endswith(".0"):
                chuoi = chuoi[:-2]
    else:
        chuoi = f"{x:.{le}f}"
    am = chuoi.startswith("-")
    nguyen, _, le_phan = chuoi.lstrip("-").partition(".")
    if len(nguyen) >= 5:
        nguyen = f"{int(nguyen):,}".replace(",", ".")
    return ("-" if am else "") + nguyen + ("," + le_phan if le_phan else "")


# ══════════════════════════════════════════════════════════ tiền xử lý
_DE_MUC_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_TLTK_RE = re.compile(r"TÀI LIỆU THAM KHẢO|REFERENCES|DANH MỤC TÀI LIỆU", re.IGNORECASE)
_TIM_KIEM_RE = re.compile(r"\[(?:Mesh|tiab|pt|ti|tw|majr|dp)\]", re.IGNORECASE)
_URL_RE = re.compile(r"https?://\S+|www\.\S+|\b10\.\d{4,9}/\S+|doi:\s*\S+", re.IGNORECASE)
_MA_RE = re.compile(r"`[^`\n]*`|\$[^$\n]+\$")
_DINH_DANH_RE = re.compile(r"PMID:?\s*\d+|PMCID:?\s*PMC\d+|\bPMC\d+|\bNCT\d+|\bISSN\s*[\d-]+X?|\bISBN\s*[\d-]+",
                           re.IGNORECASE)
_VIET_RE = re.compile(r"[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]", re.IGNORECASE)


def _sach(d: str) -> str:
    """Dòng bỏ mã `…`/$…$, URL/DOI, PMID/NCT/ISSN (giữ độ dài để vị trí không trôi)."""
    for bt in (_MA_RE, _URL_RE, _DINH_DANH_RE):
        d = bt.sub(lambda m: " " * len(m.group(0)), d)
    return d


def _dong_quet(van: str) -> Iterable[Tuple[int, str, str, bool]]:
    """(số dòng, dòng đã làm sạch, dòng gốc, là đề mục) — bỏ TLTK, khối mã, dòng chuỗi tìm kiếm."""
    trong_tltk = trong_ma = False
    cap_tltk = 0
    for so, d in enumerate(unicodedata.normalize("NFC", van).splitlines(), 1):
        if d.strip().startswith("```"):
            trong_ma = not trong_ma
            continue
        if trong_ma:
            continue
        m = _DE_MUC_RE.match(d)
        if m:
            if trong_tltk and len(m.group(1)) <= cap_tltk:
                trong_tltk = False
            if _TLTK_RE.search(m.group(2)):
                trong_tltk, cap_tltk = True, len(m.group(1))
                continue
        if trong_tltk or _TIM_KIEM_RE.search(d) or d.lstrip().startswith("!["):
            continue
        yield so, _sach(d), d, bool(m)


# ══════════════════════════════════════════════════════════ luật
_SO_LE_DONG_RE = re.compile(r"^\s*(?:[-*]\s*)?\d{1,3}\.?\s*$")
_SO_LE_CUOI_RE = re.compile(r"(?:[.!?…]|\])\s+(\d{1,3})\.?\s*$")
_THAP_PHAN_DAI_RE = re.compile(r"(?<![\w.,/:-])\d+[.,]\d{5,}(?!\d)")
#: số thập phân dấu chấm; dấu «-» ngay trước chỉ được nhận là DẤU ÂM khi trước nó không phải chữ/số («-0.0187»,
#: «–-0.0073»), không nhận khi là gạch nối («ISO-9001.2015», «1.2-3.4»)
_CHAM_THAP_PHAN_RE = re.compile(r"(?<![\w.,/:])(?<![\w.,]-)\d+\.\d+(?![\w/]|[.,]\d)")
_NHOM_NGHIN_RE = re.compile(r"[1-9]\d{0,2}(?:\.\d{3})+")  # «0.668» không phải nhóm nghìn
#: ngay sau ký hiệu ƯỚC LƯỢNG thống kê («OR = 2.783», «AUC: 0.812», «p = 0.041») thì «2.783» là số thập phân dấu chấm —
#: không đọc thành nhóm nghìn như «1.298 người»
_KY_HIEU_UOC_LUONG_RE = re.compile(
    r"(?<!\w)(?:a?OR|cOR|RR|aRR|HR|aHR|PR|IRR|RD|MD|SMD|AUC|ICC|kappa|κ|β|beta|p|r|R²|LR[+−-]?|Brier|SD|ĐLC|TB)"
    r"\s*(?:hiệu chỉnh|thô|gộp)?\s*[=:≈]\s*[-−]?$")
#: dòng khai PHẦN MỀM/GÓI — số đứng ngay sau tên gói ASCII là phiên bản («Phần mềm: R 4.6 (metafor 4.6)»)
_DONG_PHAN_MEM_RE = re.compile(r"phần mềm|\bpackages?\b|\bgói\b|\bsoftware\b|thư viện", re.IGNORECASE)
#: từ tiếng Việt viết không dấu hay đứng trước số («trong 1.5 năm») — không phải tên gói
_TU_VIET_KHONG_DAU = frozenset({"trong", "khi", "cho", "con", "ca", "hai", "thi", "ra", "tinh", "sinh", "nhin", "xin",
                                "chinh", "kinh", "thanh", "binh", "linh", "hinh", "minh", "tim", "nhanh", "canh"})
#: nhãn mô tả số của DỮ LIỆU MÁY (chỉ bộ đổi `viet_hoa_so` dùng): «trung bình 132.418», «(SD 14.207)»
_NHAN_MO_TA_SO_RE = re.compile(r"(?<!\w)(?:trung bình|trung vị|SD|ĐLC|IQR)\s*[=:≈]?\s*\(?[-−]?$")
_PHIEN_BAN_RE = re.compile(r"(?:phiên bản|version|\bbản số|\bver\.?)[^;|]{0,30}$", re.IGNORECASE)
#: số đứng sau từ dẫn THAM CHIẾU (mục/bảng/hình/§, mục đề cương, khuyến cáo số, mục chuẩn báo cáo, phiên bản phần mềm,
#: tiền tố DOI) — kể cả dãy tham chiếu «mục 2.6.1, 2.6.4, 2.7», «§3.4–3.5», «R ≥ 4.3» — là số hiệu, không phải số đo
_THAM_CHIEU_TRUOC_RE = re.compile(
    r"(?:(?<!\w)(?:mục tiêu|mục|phần|bảng|hình|biểu đồ|chương|phụ lục|tiểu mục|điều|khoản|câu|bước|giai đoạn|"
    r"công việc|nội dung|nhiệm vụ|hoạt động|"
    r"đề cương(?: nộp)?|khuyến cáo|table|figure|section|item|recommendation|R|SPSS|Stata|SAS|Python|RStudio|"
    r"R Studio|REDCap|Excel|SAP|DOI|phiên bản|version|bản|ICH|E6|GPP|II|v|RECORD|STROBE|CONSORT|SPIRIT|STARD|TRIPOD|"
    r"PRISMA|CHEERS|COREQ|SRQR|CARE|SQUIRE|CROSS|AGREE|RIGHT)|§)"
    r"\s*(?:[≥≤<>=]+\s*)?\(?\s*(?:\d+(?:\.\d+)*[a-z]?\s*(?:[–,-]|và|and)\s*§?\s*)*$",
    re.IGNORECASE)


def _la_tham_chieu(truoc: str) -> bool:
    """Chuỗi ngay TRƯỚC một số (≤ 40 ký tự) kết thúc bằng từ dẫn tham chiếu/phiên bản ⇒ số là số hiệu."""
    return bool(_THAM_CHIEU_TRUOC_RE.search(truoc) or _PHIEN_BAN_RE.search(truoc))


_DANH_SO_DAU_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?\d+(?:\.\d+)+\.?(?:\*\*)?\s")
_NOI_BO_RE = re.compile(r"\{[a-z_][a-z0-9_]*\}|@@[A-Z_]+@@|[⟦⟧]|\bTODO\b|\bFIXME\b")
_RONG_MAY_RE = re.compile(r"(?:^|[:=|(]\s*|\s)(None|NaN|nan|null|undefined)(?=\s*(?:[|,;.)]|$))")


def _o_bang(d: str) -> List[str]:
    return [x.strip() for x in d.strip().strip("|").split("|")]


def _q1(s: str, de_muc: bool, truoc: str) -> Optional[str]:
    """`truoc` = dòng có chữ gần nhất phía trên: dòng nhãn kết thúc bằng «:» («Trường 17, Target sample size:» / «218»
    — hồ sơ đăng ký dạng nhãn–giá trị trên hai dòng) ⇒ số là GIÁ TRỊ của nhãn, không phải số đứng lẻ."""
    if de_muc or s.lstrip().startswith("|"):
        return None
    if _SO_LE_DONG_RE.match(s):
        if re.search(r":\**\s*$", truoc):
            return None
        return f"số đứng lẻ thành dòng «{s.strip()}»"
    m = _SO_LE_CUOI_RE.search(s)
    if m and len(s.strip()) > 20:
        return f"số đứng lẻ thành câu cuối đoạn «…{s.rstrip()[-20:]}»"
    return None


_NHAN_GIA_TRI_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*|\*|_)?(?P<nhan>[^:*_|]{3,90}?)(?:\*\*|\*|_)?\s*:\s*(?:\*\*|\*)?"
                              r"(?P<gia_tri>[^|]*?)(?:\*\*|\*)?\s*\.?\s*$")


def _q2(s: str) -> Optional[str]:
    if s.lstrip().startswith("|"):
        o = _o_bang(s)
        if len(o) >= 2 and hoi_chu(bo_dau(o[0])):
            so = [x for x in o[1:] if la_ma_so_don_le(x.rstrip("."))]
            if so:
                return f"ô hỏi chữ (người/vai trò/mô tả) «{o[0][:50]}» điền mã số «{so[0]}»"
        return None
    m = _NHAN_GIA_TRI_RE.match(s)
    if m and hoi_chu(bo_dau(m["nhan"])) and la_ma_so_don_le(m["gia_tri"].rstrip(".")):
        return f"ô hỏi chữ (người/vai trò/mô tả) «{m['nhan'].strip()[:50]}» điền mã số «{m['gia_tri'].strip()}»"
    return None


def _q3(s: str) -> Optional[str]:
    for m in _THAP_PHAN_DAI_RE.finditer(s):
        if not _la_tham_chieu(s[max(0, m.start() - 40):m.start()]):  # «tiền tố DOI 10.59354» là số hiệu
            return f"số thập phân chưa làm tròn «{m.group(0)}»"
    return None


#: ô CÔNG THỨC của bảng biến số (REDCap): mở bằng «=», có «if(» hoặc tham chiếu biến «[ten_bien]» — KHÔNG dùng dấu so
#: sánh làm dấu hiệu (ô văn bản «p < 0,001», «< 140/90 mmHg» không phải công thức)
_CONG_THUC_O_RE = re.compile(r"^\s*=|\bif\s*\(|\[[a-z_][a-z0-9_]*\]")


def _o_dau(s: str) -> Tuple[int, str]:
    """(vị trí bắt đầu, nội dung đã bỏ ** và khoảng trắng) của ô ĐẦU dòng bảng."""
    i = s.index("|") + 1
    j = s.find("|", i)
    o = s[i:j if j > 0 else len(s)]
    trai = len(o) - len(o.lstrip(" *"))
    return i + trai, o.strip(" *")


def _bo_o_khong_xet(s: str) -> str:
    """Dòng bảng: ô CÔNG THỨC («= if(fib4 >= 3.25, 1, 0)», «[lsm_kpa] < 8») và ô giá trị của nhãn PHIÊN BẢN
    («| Phiên bản đề cương | 1.0 |») thay bằng khoảng trắng cùng độ dài."""
    if not s.lstrip().startswith("|"):
        return s
    ra, nhan_phien_ban = [], False
    for k, o in enumerate(s.split("|")):
        if k > 0 and (_CONG_THUC_O_RE.search(o) or (nhan_phien_ban and k > 1)):
            o = " " * len(o)
        if k == 1:
            nhan_phien_ban = bool(re.search(r"phiên bản|version", o, re.IGNORECASE))
        ra.append(o)
    return "|".join(ra)


#: ký hiệu/tên phương pháp thống kê ASCII — không tính là «từ tiếng Anh» khi xét một dòng có phải tiếng Anh
_KY_HIEU_TK = frozenset({"AUC", "ICC", "IQR", "KTC", "EPV", "VIF", "ICER", "QALY", "DALY", "SMD", "NNT", "NNH", "NPV",
                         "PPV", "BMI", "LOG", "RANK", "COX", "OLS", "GLM", "GEE", "MICE", "WALD", "FISHER", "POISSON",
                         "KAPLAN", "MEIER", "WILSON", "CLOPPER", "PEARSON", "BRIER", "FIRTH", "TOST", "CEAC", "WTP",
                         "NMB", "RMST", "BOOTSTRAP", "TWO", "ONE", "SIDED"})


def _la_dong_tieng_anh(goc: str) -> bool:
    """Dòng TIẾNG ANH trong văn bản tiếng Việt (bản dịch phiếu đồng ý, tóm tắt/trường đăng ký tiếng Anh): không dấu
    tiếng Việt và có ≥ 4 từ ASCII ≥ 3 chữ cái ngoài ký hiệu thống kê. Dòng chỉ có số và ký hiệu («HR = 0.668 (95% CI …),
    p = 0.0265», «| 0.873 | 0.801–0.951 |») KHÔNG phải tiếng Anh — vẫn theo quy ước số của văn bản tiếng Việt."""
    if _VIET_RE.search(goc):
        return False
    tu = [w for w in re.findall(r"[A-Za-z]{3,}", _MA_RE.sub(" ", goc)) if w.upper() not in _KY_HIEU_TK]
    return len(tu) >= 4


def _so_can_doi(s: str, goc: str, de_muc: bool, ca_so_dai: bool = False,
                du_lieu_may: bool = False) -> Iterable["re.Match[str]"]:
    """Các số thập phân viết dấu chấm của MỘT dòng tiếng Việt phải đổi sang dấu phẩy (Q4) — đã trừ nhóm nghìn, số hiệu
    tham chiếu/phiên bản, số mục đầu dòng/đầu ô bảng, ô công thức. `ca_so_dai` = gồm cả số ≥ 5 chữ số lẻ (Q3 báo riêng,
    nhưng bộ đổi `viet_hoa_so` cũng phải đổi); `du_lieu_may` = số máy chép từ dữ liệu: số dạng nhóm nghìn («1.536»)
    là THẬP PHÂN khi dòng có bằng chứng kiểu dấu chấm thập phân (một số dấu chấm không thể là nhóm nghìn — «0.0006»,
    «14.25») hoặc đứng sau nhãn ước lượng/mô tả («trung bình 132.418 (SD 14.207)»); không có bằng chứng thì giữ — G6
    đã trình bày kiểu Việt («| Chi phí gia tăng ΔC | 649.953 |» là 649 953 đồng)."""
    if de_muc or _la_dong_tieng_anh(goc) or _DANH_SO_DAU_RE.match(s):
        return
    s = re.sub(r"\bif\s*\([^)]*\)", lambda m: " " * len(m.group(0)), _bo_o_khong_xet(s))
    dau_o = _o_dau(s) if s.lstrip().startswith("|") else None
    tat_ca = list(_CHAM_THAP_PHAN_RE.finditer(s))

    def _co_nhan(x: "re.Match[str]") -> bool:
        tr = s[max(0, x.start() - 40):x.start()]
        return bool(_KY_HIEU_UOC_LUONG_RE.search(tr) or (du_lieu_may and _NHAN_MO_TA_SO_RE.search(tr)))

    # bằng chứng cả dòng (chỉ dữ liệu máy): một số dấu chấm không thể là nhóm nghìn, hoặc một số có nhãn ước lượng —
    # «OR = 2.783 (95% CI 1.536–5.043)» ⇒ cả KTC cũng là thập phân
    bang_chung_dong = du_lieu_may and any(not _NHOM_NGHIN_RE.fullmatch(x.group(0)) or _co_nhan(x) for x in tat_ca)
    dong_phan_mem = bool(_DONG_PHAN_MEM_RE.search(goc))
    for m in tat_ca:
        so = m.group(0)
        truoc = s[max(0, m.start() - 40):m.start()]
        thap_phan = _co_nhan(m) or bang_chung_dong
        if (_NHOM_NGHIN_RE.fullmatch(so) and not thap_phan) or (len(so.split(".")[1]) >= 5 and not ca_so_dai):
            continue  # nhóm nghìn «10.000» đúng quy ước; ≥ 5 chữ số lẻ đã báo ở Q3
        if _la_tham_chieu(truoc) or re.search(r"`[^`]+`\s*(?:≥|>=)\s*$", goc[max(0, m.start() - 40):m.start()]):
            continue  # số mục/bảng/hình, phiên bản phần mềm/chuẩn/tài liệu, phiên bản gói «`survey` ≥ 4.5»
        ten_goi = re.search(r"(?<![\w.])([A-Za-z][\w.+-]*)\s+$", truoc) if dong_phan_mem else None
        if ten_goi and ten_goi.group(1).lower() not in _TU_VIET_KHONG_DAU:
            continue  # dòng khai phần mềm/gói: «metafor 4.6, meta 8.0» là phiên bản
        if dau_o and m.start() == dau_o[0] and re.fullmatch(r"\d{1,2}(?:\.\d{1,2})+", so):
            continue  # số mục ở đầu ô đầu dòng bảng («| 1.1 — Tiêu đề…», «| 4.2 |»)
        yield m


def _q4(s: str, goc: str, de_muc: bool) -> Optional[str]:
    for m in _so_can_doi(s, goc, de_muc):
        so = m.group(0)
        return f"dấu chấm thập phân «{so}» — viết dấu phẩy ({so.replace('.', ',')})"
    return None


#: số dạng mũ của máy («2.8210158508762194e-08» — repr của p rất nhỏ)
_SO_MU_RE = re.compile(r"(?<![\w.,])-?\d+(?:\.\d+)?[eE][-+]?\d+(?![\w.])")


def viet_so_mu(chuoi: str) -> str:
    """Một số dạng mũ theo quy ước văn bản: |giá trị| < 10⁻⁴ ⇒ «< 0,0001» (hoặc «> -0,0001»), còn lại như `viet_so`."""
    gt = float(chuoi)
    if gt == 0:
        return "0"
    if abs(gt) < 10 ** -LE_TOI_DA:
        return ("< 0," if gt > 0 else "> -0,") + "0" * (LE_TOI_DA - 1) + "1"
    return viet_so(round(gt, LE_TOI_DA))


def viet_hoa_so(van: str) -> str:
    """Đổi số trong khối văn bản do MÁY dựng từ dữ liệu (vd số G6 bản thảo G7 chép SAU khi đã tự kiểm nguyên văn)
    sang quy ước tiếng Việt: dấu phẩy thập phân, làm tròn tối đa LE_TOI_DA chữ số lẻ. Dữ liệu máy luôn dùng dấu chấm
    thập phân ⇒ «1.536» là MỘT PHẨY NĂM BA SÁU (không phải nhóm nghìn như chữ người viết). Cùng phạm vi với Q3/Q4 —
    số hiệu tham chiếu, phiên bản, mã `…`, URL/DOI/PMID, dòng tiếng Anh giữ nguyên; dòng không có số cần đổi giữ
    nguyên từng ký tự."""
    ra = []
    for d in unicodedata.normalize("NFC", van or "").split("\n"):
        s = _sach(d)
        de_muc = bool(_DE_MUC_RE.match(d))
        doi = list(_so_can_doi(s, d, de_muc, ca_so_dai=True, du_lieu_may=True))
        doi_dai = [m for m in _THAP_PHAN_DAI_RE.finditer(s) if "," in m.group(0)
                   and not _la_tham_chieu(s[max(0, m.start() - 40):m.start()]) and not de_muc]
        mu = [] if de_muc or _la_dong_tieng_anh(d) else list(_SO_MU_RE.finditer(s))
        for m in sorted(doi + doi_dai + mu, key=lambda x: x.start(), reverse=True):
            if m.re is _SO_MU_RE:
                d = d[:m.start()] + viet_so_mu(m.group(0)) + d[m.end():]
                continue
            gt = float(m.group(0).replace(",", "."))
            le = min(len(re.split(r"[.,]", m.group(0))[1]), LE_TOI_DA)
            d = d[:m.start()] + viet_so(round(gt, le), le) + d[m.end():]
        ra.append(d)
    return "\n".join(ra)


def _q5(s: str) -> Optional[str]:
    m = _NOI_BO_RE.search(s)
    if m:
        return f"ký hiệu nội bộ còn trong câu «{m.group(0)}»"
    m = _RONG_MAY_RE.search(s)
    if m and _VIET_RE.search(s):
        return f"giá trị rỗng của máy «{m.group(1)}»"
    return None


def quet(van: str) -> List[str]:
    """Lỗi điền sai kiểu của một văn bản: «Qn dòng N: …» (rỗng = sạch)."""
    loi: List[str] = []
    truoc = ""
    for so, s, goc, de_muc in _dong_quet(van):
        for ma, kq in (("Q1", _q1(s, de_muc, truoc)), ("Q2", _q2(s)), ("Q3", _q3(s)), ("Q4", _q4(s, goc, de_muc)),
                       ("Q5", _q5(s))):
            if kq:
                loi.append(f"{ma} dòng {so}: {kq}")
        if s.strip():
            truoc = s
    return loi


# ══════════════════════════════════════════════════════════ tệp, thư mục đề tài
def doc_van_ban(p: Path) -> str:
    """Chữ của tệp .md/.txt; .docx đọc đoạn và ô bảng (mỗi hàng bảng một dòng «| … |») — cần python-docx."""
    if p.suffix.lower() != ".docx":
        return p.read_text(encoding="utf-8")
    import docx  # noqa: PLC0415 — chỉ khi quét .docx

    tl = docx.Document(str(p))
    dong = [para.text for para in tl.paragraphs]
    for bang in tl.tables:
        for hang in bang.rows:
            dong.append("| " + " | ".join(c.text.replace("\n", " ") for c in hang.cells) + " |")
    return "\n".join(dong)


def tep_dau_ra(out_dir: Path) -> List[Path]:
    """Văn bản đầu ra của thư mục đề tài (MAU_TEP; bỏ .bak và _dau_may_sinh). Bản .docx dựng TỪ bản .md cùng tên
    không quét lại (cùng nội dung, lỗi đếm hai lần); .docx chỉ quét khi không có .md (hồ sơ dựng thẳng Word)."""
    out_dir = Path(out_dir)
    ra: List[Path] = []
    cap = [(out_dir, m) for m in MAU_TEP] + [(out_dir / tm, m) for tm, ds in MAU_TEP_HO_SO.items() for m in ds]
    for thu_muc, mau in cap:
        for p in sorted(thu_muc.glob(mau)):
            if p.suffix.lower() not in (".md", ".docx") or ".bak" in p.name or p in ra:
                continue
            if p.suffix.lower() == ".docx" and p.with_suffix(".md").is_file():
                continue
            ra.append(p)
    return ra


def quet_thu_muc(out_dir: Path, them: Optional[Dict[str, str]] = None) -> List[str]:
    """«tệp: Qn dòng N: …» cho mọi văn bản đầu ra của đề tài; `them` = {tên: văn bản} dựng trong bộ nhớ (vd báo cáo
    tổng hợp)."""
    ra: List[str] = []
    for p in tep_dau_ra(out_dir):
        ten = p.relative_to(out_dir).as_posix()
        try:
            van = doc_van_ban(p)
        except Exception as exc:  # noqa: BLE001 — tệp hỏng/thiếu thư viện: báo, không im lặng
            ra.append(f"{ten}: không đọc được ({type(exc).__name__}) — CHƯA QUÉT")
            continue
        ra += [f"{ten}: {x}" for x in quet(van)]
    for ten, van in (them or {}).items():
        ra += [f"{ten}: {x}" for x in quet(van)]
    return ra


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Chốt chung «điền sai kiểu» cho văn bản đầu ra của đề tài.")
    nhom = ap.add_mutually_exclusive_group(required=True)
    nhom.add_argument("--study")
    nhom.add_argument("--tep", nargs="+")
    ap.add_argument("--exports-root", default=str(BASE / "exports"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.study:
        out = Path(a.exports_root) / a.study
        if not tep_dau_ra(out):
            print(f"không có văn bản đầu ra để quét trong {out}")
            return 2
        loi = quet_thu_muc(out)
    else:
        loi = []
        for t in a.tep:
            loi += [f"{Path(t).name}: {x}" for x in quet(doc_van_ban(Path(t)))]
    if a.json:
        print(json.dumps({"so_loi": len(loi), "loi": loi}, ensure_ascii=False, indent=2))
    else:
        for x in loi:
            print(f"  ✗ {x}")
        print("✓ sạch — không có lỗi điền sai kiểu" if not loi else f"{len(loi)} lỗi điền sai kiểu")
    return 1 if loi else 0


if __name__ == "__main__":
    raise SystemExit(main())
