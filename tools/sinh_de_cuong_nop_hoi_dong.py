#!/usr/bin/env python3
"""Sinh ĐỀ CƯƠNG NỘP HỘI ĐỒNG `exports/<mã>/DE_CUONG_NOP_HOI_DONG_<mã>.md` + `.docx` từ quyết định ĐÃ CHỐT (16/11/2026).

Vì sao có: bác sĩ đọc đề cương của các đề tài giả lập và chê «không đúng với một đề cương hoàn chỉnh vì những câu chữ,
từ ngữ không phù hợp» — bản lắp máy `DE_CUONG_THONG_NHAT_<mã>` là hồ sơ TRUY XUẤT nội bộ (bảng cổng, ma trận 24 thành
phần, chú thích nguồn «(G1 — đã chốt)», «SAP §4», tên biến trong văn xuôi, đường dẫn máy), còn bản nộp Hội đồng trước
nay chỉ có cách viết TAY (C1a). Công cụ này dựng bản nộp theo cấu trúc đề cương tiếng Việt chuẩn (đặt vấn đề → mục tiêu
→ tổng quan → đối tượng và phương pháp → dự kiến kết quả → kế hoạch → tài liệu tham khảo → phụ lục) bằng văn xuôi, chỉ
từ dữ kiện đã chốt: StudySpec (study_meta + checkpoint), khối cỡ mẫu G3, SAP đã khoá, phiếu đồng ý G2, từ điển dữ liệu,
biên nhận trích dẫn A12. Không bịa: thiếu dữ kiện ⇒ dòng chấm «………» cho chủ nhiệm điền tay.

Lớp làm sạch `lam_sach()` gỡ mọi dấu vết nội bộ (chú thích nguồn, mã cổng, «§», nhãn giả lập, mã vai trò, tên biến
trong ngoặc, cảnh báo ⚠). Văn bản ra phải qua `kiem_de_cuong_nop_hoi_dong.kiem()` (K1–K7) — công cụ tự chạy và báo.

KHÔNG GHI ĐÈ bản người đã sửa: dấu bản máy sinh nằm NGOÀI văn bản (`_dau_may_sinh/<tệp>.json`, sha256 — công cụ
`dau_may_sinh`); tệp hiện có khớp dấu ⇒ chưa ai sửa, được sinh lại; lệch dấu hoặc không có dấu ⇒ bản người viết/sửa ⇒
từ chối (mã 4). Văn bản nộp KHÔNG mang dấu vết máy/bản nháp nào (bác sĩ 17/11/2026; luật K8). Bản sinh ra là bản cho chủ
nhiệm biên tập — không phải văn bản đã duyệt.

Lệnh:  python3 tools/sinh_de_cuong_nop_hoi_dong.py --study <mã> [--ghi] [--json]
Mã thoát: 0 đã sinh và K1–K7 đạt · 1 đã sinh nhưng còn lỗi K · 2 thiếu dữ liệu nền (study_meta) · 4 từ chối ghi đè
bản viết tay. Không có --ghi ⇒ chạy khô: in đường dẫn + số dòng, không ghi tệp.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

TEN = "DE_CUONG_NOP_HOI_DONG_{study}"
DAU_MAY = "<!-- sinh-de-cuong-nop-hoi-dong: bản máy soạn từ quyết định đã chốt — chủ nhiệm biên tập trước khi nộp -->"
CHAM = "………"
TIEN_TO_TONG_HOP = "ZZCANARY"

# ══════════════════════════════════════════════════════════════════════════════════════════════════ làm sạch câu chữ
# Chú thích nguồn/nhãn nội bộ bị GỠ HẲN (kèm khoảng trắng đứng trước).
_BO_HAN = [re.compile(x, re.IGNORECASE) for x in (
    r"\s*\*\([^()]*\)\*",                                                  # ghi chú nghiêng *(điền sẵn …)* của SAP
    r"\s*\([^()]*\bgiả lập\b[^()]*\)",                                      # (chủ nhiệm —, giả lập)
    r"\s*\(khớp khai báo COI[^()]*\)",
    r"\s*\((?:GIẢ LẬP|GIA LAP)\b[^()]*\)",  # (GIẢ LẬP CANARY — …), (GIẢ LẬP — chưa có)
    r"\s*\(giả lập\b[^()]*\)",
    r"\s*\((?:G\d{1,2}|SAP)(?:\s*§\s*\d+)?\s*[—–-][^()]*\)",                # (G1 — đã chốt), (SAP §4 — đã chốt ở G4)
    r"\s*\((?:PI|bác sĩ|chủ nhiệm)\s+đã\s+chốt[^()]*\)",                  # (PI đã chốt — gate_params.G2.…)
    # 18/11/2026: ghi chú nguồn gốc quyết định mà K8 nay bắt (đề cương BTM + 22/24 đề cương giả lập mang «(quy trình dữ
    # liệu đã chốt)» do quyet_dinh_da_chot gắn để truy vết) — giữ ở dữ kiện, gỡ khi in văn bản nộp.
    r"\s*\([^()]{0,24}\bđã\s+(?:chốt|duyệt)\s*\)",                         # (quy trình dữ liệu đã chốt), (PICO đã chốt)
    r"\s*\(SPIRIT(?:\s+2025)?(?:\s+mục)?\s+\d+[a-z]?(?:\s*[,;]\s*\d+[a-z]?)*\)",
    r"\s*\((?:hồ sơ vận hành G5|xác nhận lúc khoá G5|từ ma trận mục tiêu[–-]biến)[^()]*\)",
    r"\s*\(nguồn đo từng biến[^()]*\)",
    r"\s*\*?\(điền sẵn[^()]*\)\*?",
    r"\s*\(tự động từ G\d+\)",
    r"\s*\([^()]*\b[A-Z][A-Z0-9]*_[A-Za-z0-9_]+(?:-[A-Za-z0-9-]+)?\.md\b[^()]*\)",   # (G2_SAFETY_PLAN_X.md — …)
    r"\s*\(`[^`()]+`\)",                                                      # (`nhom`)
    r"⚠️?\s*",
    r"\s*\(DRAFT[^()]*\)",
    # 17/11/2026 (đề cương BTM): cụm dẫn TỆP NỘI BỘ mở đầu câu «Theo G0 §3.0:», «Theo G0_KHOANG_TRONG (25/10/2026):»
    # — từng thành «Theo:» hoặc lộ nguyên tên tệp; tên biến trong ngoặc «(biến XN_DU)» thuộc bảng biến số, không thuộc
    # văn xuôi.
    r"\bTheo\s+(?:G\d{1,2}(?:\s*§\s*[\d.]*\d)?|[A-Z][A-Z0-9]*_[A-Z0-9_]+)(?:\s*\([^()]*\))?\s*:\s*",
    r"\s*\(biến\s+[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\)",
    # 17/11/2026 (phản biện máy Claude API trên đề cương BTM — dấu vết K1–K8 bỏ sót): chỉ dẫn tệp nội bộ «(xem
    # G0_KHOANG_TRONG)», dấu quyết định «(quyết ở G2)», lời ghi nguồn gốc quyết định «(chủ nhiệm duyệt C1–C3)»,
    # «, chủ nhiệm chọn tham chiếu 15/11/2026», trỏ phiếu đề xuất nội bộ «xem điểm S6 của phiếu đề xuất», và câu nói
    # về công cụ máy «qua công cụ phân tích của hệ thống (`…`)».
    r"\s*\(xem\s+[A-Z][A-Z0-9]*_[A-Z0-9_]+[^()]*\)",
    r"\s*\((?:quyết|chốt|duyệt)(?:\s+(?:ở|tại)\s+(?:cổng\s+)?G\d{1,2})?\)",
    r"\s*\((?:PI|chủ nhiệm)(?:\s+đề tài)?\s+(?:chọn|chốt|duyệt|quyết)[^()]*\)",
    r",\s*(?:PI|chủ nhiệm)(?:\s+đề tài)?\s+(?:chọn|chốt|duyệt|quyết)[^,;()]*?\d{1,2}/\d{1,2}/\d{4}",
    r"[;,]?\s*(?:cách đo\s+)?xem điểm\s+S\d+\s+của phiếu đề xuất",
    r"\s*qua công cụ phân tích của hệ thống(?:\s*\([^()]*\))?",
)]
# Thay cụm nội bộ bằng cách nói của văn bản nộp.
# 17/11/2026 (đề cương BTM): khoá trường đã chốt «gate_params.G0.intervention» từng thành «như.intervention»; mã cổng
# làm tân ngữ «cho thống nhất với G3;» từng thành «với;». Đổi sang cách nói của văn bản nộp thay vì xoá.
_NHAN_KHOA_DA_CHOT = {"intervention": "các yếu tố khảo sát liệt kê ở Phụ lục D", "population": "quần thể nghiên cứu",
                      "comparison": "nhóm so sánh", "outcomes": "các kết cục nghiên cứu"}
_NHAN_CONG = {"0": "câu hỏi nghiên cứu", "1": "thiết kế nghiên cứu", "2": "hồ sơ đạo đức", "3": "cách tính cỡ mẫu",
              "4": "kế hoạch phân tích thống kê", "5": "kế hoạch quản lý dữ liệu"}
_THAY = [(re.compile(a, re.IGNORECASE), b) for a, b in (
    (r"\bgate_params\.G\d{1,2}\.([a-z_]+)",
     lambda m: _NHAN_KHOA_DA_CHOT.get(m.group(1).lower(), "các nội dung đã chốt")),
    (r"\b((?:so\s+)?với|cho)\s+G([0-5])\b(?!\s*[–-]\s*G)", lambda m: f"{m.group(1)} {_NHAN_CONG[m.group(2)]}"),
    (r"\s*\(bảng RACI ở A13[^()]*\)", " (mục 6.1)"),
    # 18/11/2026: bác sĩ xác nhận «mã quy trình nội bộ chưa định nghĩa» là lỗi thật (phản biện máy BTM, mục 19) ⇒ in
    # bằng lời, không giữ mã SOP-… (K8 nay bắt mã này). Cùng lượt: «mục 4.5» không có danh sách yếu tố (mục 11).
    (r"\(\s*(SOP-[A-Z]+-\d+)\s*\)", "(theo quy trình chuẩn của đề tài)"),
    (r"Tài liệu\s+4\s*[–-]\s*5\s+hồ sơ\s+G2", "Phụ lục B"),
    (r"\bhồ sơ\s+G2\b", "hồ sơ đạo đức"),
    (r"\bkế hoạch an toàn G2\b", "kế hoạch an toàn"),
    (r"\bKế hoạch quản lý dữ liệu G5\b", "Kế hoạch quản lý dữ liệu"),
    (r"\s+(?:ở|tại|theo)\s+§\s*\d+(?:\.\d+)*", ""),
    (r"\bSAP\s*§\s*\d+(?:\.\d+)*", "kế hoạch phân tích thống kê"),
    (r"\bđề cương thống nhất\s*§\s*[\d.]+[^,.;]*", "mục can thiệp của đề cương"),
    (r"§\s*\d+(?:\.\d+)*", ""),
    (r"§", ""),
    (r"\bSAP\b", "kế hoạch phân tích thống kê"),
    (r"\bPI-REF-\d+\b", "chủ nhiệm đề tài"),
    (r"\bmã vai trò\b", ""),
    (r"\s*\bG\d{1,2}\s*[–-]\s*G\d{1,2}\b", ""),  # «liêm chính G8–G9 (…)» (17/11/2026, lịch trình BTM)
    (r"\bN/A\b", "Không áp dụng"),
    (r"\s+(?:ở|tại|theo)\s+(?:cổng\s+)?G\d{1,2}\b", ""),
    (r"\bcổng\s+G\d{1,2}\b", "bước thẩm định"),
    (r"\bG(?:0|[1-9]|10)\b(?!\s*[–-]\s*G)", ""),
    (r"\bITT analysis\b", "phân tích theo ý định điều trị"),
    (r"\bin SAP\b", "theo kế hoạch phân tích"),
    (r"\b95%\s*CI\b", "khoảng tin cậy 95%"),
    (r"\bp-value\b", "giá trị p"),
    (r"\bComplete case vs MI\b", "So sánh phân tích ca đầy đủ với gán đa trị"),
    (r"\(complete case\)", "(phân tích ca đầy đủ)"),
    (r"\bMultiple Imputation \(MI, m=(\d+), method=pmm\)",
     r"gán đa trị (multiple imputation, MI) với \1 bộ dữ liệu, phương pháp so khớp trung bình dự báo"),
    (r"\bMAR \(missing at random\)", "thiếu ngẫu nhiên (missing at random, MAR)"),
    (r"\binteraction term\b", "số hạng tương tác"),
    (r"chiến lược\s+treatment-policy", "chiến lược theo chính sách điều trị (treatment-policy)"),
    (r"(?<!\()\bTreatment-policy\b(?!\))", "chiến lược theo chính sách điều trị (treatment-policy)"),
    (r"\bPI\b", "chủ nhiệm đề tài"),
    (r"\bICF\b", "phiếu đồng ý"),
    (r"\s\+\s", " và "),
    (r"\bmanifest SHA-256\b", "mã băm SHA-256"),
    (r"\bkiểm checksum\b", "kiểm tra mã băm"),
    (r"\s*(?:trong|bằng|của|theo)\s+(?:công cụ|tệp|lệnh|kịch bản)\s+[\w./-]+\.(?:py|R|sps|json|md|csv)\b", ""),
    (r"\s*\b[\w-]+\.(?:py|sps|json)\b", ""),
    (r"\bhigher_better\b", "(giá trị cao hơn là tốt hơn)"),
    (r"\blower_better\b", "(giá trị thấp hơn là tốt hơn)"),
    (r"\bvnd\b", "đồng"),
    (r"\s*⇒\s*", " → "),
    (r"\bRandom/Fixed effects meta-analysis\b", "phân tích gộp theo mô hình hiệu ứng ngẫu nhiên hoặc cố định"),
    (r"\bmeta-regression\b", "hồi quy gộp (meta-regression)"),
    (r",?\s*lấy từ\s*:?\s*$", ""),
    (r"\s*→\s*RR\b", " để ước lượng tỷ số nguy cơ (RR)"),
    (r"\s*→\s*OR\b", " để ước lượng tỷ số chênh (OR)"),
    (r"\s*→\s*HR\b", " để ước lượng tỷ số rủi ro (HR)"),
    (r"\bvs\b", "so với"),
    (r"\bNTG\b", "người tham gia"),
)]
_TEN_BIEN_TRONG_NGOAC = re.compile(r"`([a-z][a-z0-9_]*)`\s*\(([^()]+)\)")
NHAN_BIEN: Dict[str, str] = {}  # tên biến → nhãn (Nguon nạp từ từ điển dữ liệu)
_TEN_BIEN_TRAN = re.compile(r"`([a-z][a-z0-9_]*)`")


def _nhan_giua_cau(nhan: str) -> str:
    """Nhãn biến lồng vào giữa câu: hạ chữ đầu thường, GIỮ từ viết tắt (17/11/2026 — bản cũ `.lower()` cả nhãn ⇒
    «acei/arb theo kdigo 2022», «uacr», «mt3» trong đề cương BTM)."""
    nhan = str(nhan or "").strip()
    if len(nhan) > 1 and nhan[0].isupper() and not nhan[1].isupper():
        return nhan[0].lower() + nhan[1:]
    return nhan


def lam_sach(x: Any) -> str:
    """Chuỗi sạch dấu vết nội bộ — dùng cho MỌI giá trị đi vào văn xuôi của đề cương nộp."""
    if x is None:
        return ""
    if isinstance(x, (list, tuple)):
        x = "; ".join(str(v) for v in x if str(v).strip())
    s = unicodedata.normalize("NFC", str(x))
    if "[CẦN" in s.upper() or "[TO BE COMPLETED" in s.upper():
        s = re.sub(r"\[(?:CẦN|TO BE COMPLETED)[^\]]*\]?", CHAM, s, flags=re.IGNORECASE)
    for _ in range(2):  # chú thích lồng («(… (GIẢ LẬP …))») lộ ra sau lượt đầu
        for bt in _BO_HAN:
            s = bt.sub("", s)
    s = _TEN_BIEN_TRONG_NGOAC.sub(lambda m: m.group(2), s)
    s = _TEN_BIEN_TRAN.sub(lambda m: _nhan_giua_cau(NHAN_BIEN.get(m.group(1), "")), s)
    # định danh máy dạng ten_bien còn trần trong câu (vd «chiều kết cục higher_better» của SAP): nhãn biến nếu có
    # trong từ điển, không thì bỏ — tên biến chỉ được ở bảng/phụ lục (K4)
    s = re.sub(r"(?:,\s*){2,}", ", ", s)
    for bt, moi in _THAY:
        s = bt.sub(moi, s)
    for cu in ("(GIẢ LẬP — hồ sơ chưa có)", "chưa có thông tin"):  # ô hồ sơ chưa có ⇒ dòng chấm điền tay
        s = s.replace(cu, CHAM)
    s = re.sub(r"(?<![\w./`-])([a-z][a-z0-9]*_[a-z0-9_]+)(?![\w`])",
               lambda m: _nhan_giua_cau(NHAN_BIEN.get(m.group(1), "")), s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\(\s*[,;]\s*", "(", s)  # «(G10, từ 29/04/2027)» sau khi bỏ ký hiệu cổng
    s = re.sub(r"\s*[,;]\s*\)", ")", s)  # «(thiết kế theo độ chính xác,)» sau khi bỏ tham chiếu mục
    s = re.sub(r"\s*\(\s*\)", "", s)
    s = re.sub(r"\s+([,;.:)])", r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"([,;])\1+", r"\1", s)
    s = re.sub(r"\.{2,}(?!\.)", ".", s) if "…" not in s else s
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip(" ;,—–-")


_GIU_HOA = {"RCT", "ITT", "RR", "OR", "HR", "SMS", "MAR", "DAG", "VIF", "ICC", "KTC", "ROC", "AUC", "SD", "IQR",
            "MI", "CI", "PPI", "NSAID", "ĐTĐ", "HA", "SR", "MA", "TSA", "RIS", "ICER", "NMB", "CEAC", "WTP", "QALY",
            "AES-256", "SHA-256", "CRF", "SGLT2", "FIB-4", "COREQ", "SRQR", "STROBE", "STARD", "TRIPOD", "PRISMA",
            "CONSORT", "SPIRIT", "CHEERS", "TIDIER", "BHYT", "BVDLCN"}


def _ha_hoa_nhan_manh(s: str) -> str:
    """Chữ IN HOA nhấn mạnh của khuôn máy («KHÔNG kiểm định», «Quần thể CHÍNH») → chữ thường trong văn xuôi;
    giữ từ viết tắt và tên chuẩn quốc tế."""
    def _mot(m: re.Match) -> str:
        w = m.group(0)
        # 18/11/2026: cụm IN HOA có chữ số là MÃ (ĐN2, MT1…), không phải chữ nhấn mạnh — bản cũ hạ «ĐN2» (có «Đ» ngoài
        # ASCII) thành «Đn2» trong đề cương BTM, lệch nhãn «ĐN2» của kế hoạch phân tích.
        return w if w in _GIU_HOA or w.isascii() or any(c.isdigit() for c in w) else w.lower()
    return re.sub(r"(?<![\w-])[A-ZÀ-ỸĐ][A-ZÀ-ỸĐ0-9-]+(?![\w-])",
                  lambda m: _mot(m) if m.group(0) == m.group(0).upper() and m.group(0) != m.group(0).lower()
                  else m.group(0), s)


def _cau(x: Any) -> str:
    """Câu hoàn chỉnh: sạch + bỏ in hoa nhấn mạnh + viết hoa chữ đầu + dấu chấm cuối (rỗng ⇒ chuỗi rỗng)."""
    s = _ha_hoa_nhan_manh(lam_sach(x))
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    return s if s[-1] in ".!?…" else s + "."


def _thuong(x: Any) -> str:
    """Hạ chữ cái đầu để lồng cụm vào giữa câu (giữ từ viết tắt toàn hoa)."""
    s = _ha_hoa_nhan_manh(lam_sach(x)).rstrip(".")
    if len(s) > 1 and s[0].isupper() and not s[1].isupper():
        return s[0].lower() + s[1:]
    return s


def _hoa_dau(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _co(x: Any) -> bool:
    s = lam_sach(x)
    return bool(s) and s != CHAM and bool(re.search(r"\w{2}", s))


def _so(v: Any, nd: int = 2) -> str:
    """Số kiểu Việt Nam: dấu phẩy thập phân, bỏ số 0 thừa (0.05 → «0,05», 1.4583 → «1,46»)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    s = f"{f:.{nd}f}".rstrip("0").rstrip(".") if nd else str(int(round(f)))
    return s.replace(".", ",")


def _pt(v: Any) -> str:
    try:
        return f"{_so(float(v) * 100, 1)}%"
    except (TypeError, ValueError):
        return str(v)


def _n(v: Any) -> str:
    """Số nguyên có dấu chấm ngăn nghìn (4396 → «4.396»)."""
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(v)


_KHOANG_THANG_RE = re.compile(r"(?<![\w/])(?:từ\s+)?(\d{4})-(\d{2})(?:-\d{2})?\s*(?:đến|–|-|tới)\s*"
                              r"(\d{4})-(\d{2})(?:-\d{2})?(?![\w/])")
_THANG_ISO_RE = re.compile(r"(?<![\w/-])(\d{4})-(\d{2})(?![\w/-])")


def _thoi_gian(x: Any) -> str:
    """«2027-03 đến 2028-03» → «từ tháng 03/2027 đến tháng 03/2028», kể cả khi khoảng nằm giữa câu («Dữ liệu 2020-01
    đến 2025-12; phân tích 2027-03 đến 2027-09» — 21/11/2026: bản cũ chỉ đổi khi CẢ chuỗi là một khoảng, nên thời gian
    của thuần tập hồi cứu in nguyên «2020-01», không phải mốc ngày kiểu Việt Nam và K17 STROBE 5 không nhận)."""
    s = lam_sach(x)
    s = _KHOANG_THANG_RE.sub(lambda m: f"từ tháng {m.group(2)}/{m.group(1)} đến tháng {m.group(4)}/{m.group(3)}", s)
    return _THANG_ISO_RE.sub(lambda m: f"tháng {m.group(2)}/{m.group(1)}", s)


# ══════════════════════════════════════════════════════════════════════════════════════════════════ trích dẫn
class TrichDan:
    """Đánh số trích dẫn Vancouver theo thứ tự xuất hiện; chỉ PMID đã phân giải (A12) và KHÔNG bị rút."""

    def __init__(self, metadata: Dict[str, dict], sach: Iterable[str]) -> None:
        self.md = metadata
        self.cho_phep = {str(p) for p in sach if str(p) in metadata}
        self.thu_tu: List[str] = []

    def so(self, pmid: Any) -> Optional[int]:
        pmid = str(pmid)
        if pmid not in self.cho_phep:
            return None
        if pmid not in self.thu_tu:
            self.thu_tu.append(pmid)
        return self.thu_tu.index(pmid) + 1

    def thay(self, text: str) -> str:
        """Đổi «(Tác giả năm, PMID n)» / «PMID: n» trong câu thành số [k]; PMID ngoài phạm vi kiểm chứng ⇒ bỏ số."""
        def _ngoac(m: re.Match) -> str:
            k = self.so(m.group(2))
            truoc = m.group(1).strip(" ,;")
            # 17/11/2026 (kiểm nội dung trích dẫn bằng Claude API, đề cương BTM): «(Ogundimu 2016, PMID 26964707: EPV
            # nên dựa vào dữ liệu, không phải quy tắc cứng)» từng thành «[41]» trần — mất lời giải thích, câu đọc như
            # bài [41] ủng hộ ngưỡng cứng mà bài phản đối. Lời sau dấu «:»/«—» là NỘI DUNG, phải giữ.
            duoi = re.sub(r"^\s*[,;]?\s*(?:DOI|doi)\s*:?\s*10\.\d{4,9}/\S+?(?=[:;—–]|$)", "", m.group(3) or "")
            ghi = re.sub(r"^\s*[:—–]\s*", "", duoi).strip(" ,;") if re.match(r"^\s*[:—–]", duoi) else ""
            if k is None:
                noi = "; ".join(x for x in (truoc, ghi) if x)
                return f" ({noi})" if noi else ""
            return f" ({ghi} [{k}])" if ghi else f" [{k}]"

        text = re.sub(r"\s*\(([^()]*?)[,;]?\s*PMID:?\s*(\d{5,9})([^()]*)\)", _ngoac, text)

        def _tran(m: re.Match) -> str:
            k = self.so(m.group(1))
            return f"[{k}]" if k else ""

        # 17/11/2026 (đề cương BTM): «PMID n, DOI 10.x/…» — DOI đi kèm cùng một bài ⇒ thay/bỏ cả cụm; bỏ PMID chưa kiểm
        # để lại khoảng trắng trước dấu câu ⇒ dọn (chỉ khi thực sự có PMID bị thay, không đụng văn bản khác).
        moi = re.sub(r"PMID:?\s*(\d{5,9})(?:\s*[,;]?\s*(?:DOI|doi)\s*:?\s*10\.\d{4,9}/[^\s,;)]*[^\s,;).])?", _tran,
                     text)
        if moi != text:
            moi = re.sub(r"[ \t]+([,.;:)])", r"\1", moi)
            moi = re.sub(r"\([ \t]+", "(", moi)
            moi = re.sub(r"[ \t]{2,}", " ", moi)
        return moi

    def nguon(self, s: Any) -> Tuple[str, str]:
        """Tách chuỗi nguồn «PMID: n (Nhãn) — mô tả» thành (cụm nhắc nguồn có số [k], mô tả đã sạch)."""
        s = str(s or "")
        m = re.match(r"\s*PMID:?\s*(\d{5,9})\s*(?:\(([^()]+)\))?\s*[—–-]?\s*(.*)$", s)
        if not m:
            return "", lam_sach(self.thay(s))
        k = self.so(m.group(1))
        nhan = lam_sach(m.group(2) or "")
        cum = (f"{nhan} [{k}]" if nhan else f"[{k}]") if k else nhan
        return cum, lam_sach(self.thay(m.group(3)))

    def danh_muc(self) -> List[str]:
        import run_g10_assemble as G10A  # noqa: PLC0415

        ra = []
        for i, pmid in enumerate(self.thu_tu, 1):
            dong = G10A._vancouver(pmid, self.md.get(pmid) or {})
            if dong:
                ra.append(f"{i}. {dong}")
        return ra


def _trich_dan(out_dir: Path) -> Tuple[Dict[str, dict], set]:
    """Metadata A12 đã phân giải + tập PMID «sạch» (đã kiểm rút bài, không bị rút). Vắng biên nhận ⇒ rỗng."""
    try:
        md = json.loads((out_dir / "A12_METADATA_RECEIPT.json").read_text(encoding="utf-8")).get("metadata") or {}
    except (OSError, ValueError, AttributeError):
        md = {}
    md = {str(k): v for k, v in md.items() if isinstance(v, dict) and v.get("status") == "resolved"}
    try:
        rc = json.loads((out_dir / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rc = {}
    kq = rc.get("results") or {}
    sach = set()
    for p in rc.get("pmids_checked") or []:
        r = kq.get(str(p)) or {}
        if str(r.get("status", "ok")).lower() in ("ok", "clean", "not_retracted"):
            sach.add(str(p))
    return md, sach


# ══════════════════════════════════════════════════════════════════════════════════════════════════ dữ liệu nguồn
def _doc_json(p: Path) -> dict:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def _doc_csv(p: Path) -> List[Dict[str, str]]:
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return [dict(r) for r in csv.DictReader(f)]
    except (OSError, csv.Error):
        return []


_TIEU_DE_CHUAN = {"GRAMMS": "QUALITY OF MIXED METHODS STUDIES"}


def nap_nhan_bien_phai_sinh(out_dir: Path) -> None:
    """Nhãn biến PHÁI SINH (xn_du, phan_loai_btm…) từ `_bien-phai-sinh.csv` vào NHAN_BIEN (không đè nhãn từ điển thô).

    17/11/2026 (đề cương BTM): biến phái sinh không có trong từ điển thô ⇒ tên biến trong văn xuôi bị xoá trơn
    («người có khác 9»). Bỏ tiền tố vai trò «KẾT CỤC CHÍNH —» của nhãn."""
    for r in _doc_csv(Path(out_dir) / "_bien-phai-sinh.csv"):
        ten, nhan = str(r.get("ten_bien") or "").strip(), str(r.get("nhan") or "").strip()
        if ten and nhan:
            NHAN_BIEN.setdefault(ten, re.sub(r"^\s*kết\s+cục\s+(?:chính|phụ)[^—–]*[—–]\s*", "", nhan, flags=re.I))


class _TruongTrichDan(dict):
    """Trường G1 do PI viết: `.get` đổi trích dẫn liền «PMID n» thành số Vancouver (PMID đã qua A12) hoặc bỏ (chưa
    qua) NGAY lúc đọc — tức theo đúng thứ tự xuất hiện trong văn bản như mọi trích dẫn khác (17/11/2026). Đo trên BTM:
    22 chỗ in trường G1 tự do (lý do thiết kế, thời điểm kết cục…) từng in PMID thô vào văn bản nộp (K6). Chuỗi không
    có «PMID» và giá trị không phải chuỗi giữ nguyên."""

    def __init__(self, goc: Any, nguon: "Nguon") -> None:
        super().__init__(goc if isinstance(goc, dict) else {})
        self._nguon = nguon

    def get(self, k: Any, mac_dinh: Any = None) -> Any:
        v = super().get(k, mac_dinh)
        td = getattr(self._nguon, "td", None)
        return td.thay(v) if isinstance(v, str) and td is not None and "PMID" in v else v


class Nguon:
    """Gom dữ kiện đã chốt của một đề tài (chỉ đọc)."""

    def __init__(self, out_dir: Path, study: str) -> None:
        import research_study_spec as RS  # noqa: PLC0415
        import run_g10_assemble as G10A  # noqa: PLC0415

        self.out, self.study = Path(out_dir), study
        self.cps = G10A.load_checkpoints(self.out)
        self.meta = G10A.load_meta(self.out)
        try:
            sap = RS.sap_song(study, self.out, repo_root=BASE)
        except Exception:  # noqa: BLE001 — SAP chưa có/không đọc được: StudySpec vẫn dựng được từ checkpoint
            sap = None
        self.spec = RS.build_study_spec(study, self.cps, self.meta, sap=sap)
        gp = self.meta.get("gate_params") or {}
        self.g0, self.g1, self.g2, self.g3 = (gp.get(g) or {} for g in ("G0", "G1", "G2", "G3"))
        self.g1 = _TruongTrichDan(self.g1, self)
        self.g3cp = self.cps.get("G3") or {}
        self.thiet_ke = str(self.g1.get("design") or (self.spec.get("design") or {}).get("code") or
                            self.g3cp.get("design_code") or "").strip()
        self.sap_text = self._doc(f"G4_A5_SAP_FINAL_{study}.md")
        self.g0raw = _doc_json(self.out / "G0_pubmed_raw.json")
        self.g2_text = self._doc(f"G2_A3_ETHICS_PACKAGE_{study}.md")
        tu_dien = self.out / f"G5_REDCap_dictionary_{study}.csv"
        self.tu_dien = _doc_csv(tu_dien) if tu_dien.is_file() else _doc_csv(self.out / "_bo-bien-rieng.csv")
        self.ma_tran = _doc_csv(self.out / "_ma-tran-muc-tieu-bien.csv")
        NHAN_BIEN.clear()
        NHAN_BIEN.update({r.get("Variable / Field Name", ""): re.sub(r"\s*\([^()]*\)$", "", r.get("Field Label") or "")
                          for r in self.tu_dien if r.get("Variable / Field Name")})
        nap_nhan_bien_phai_sinh(self.out)
        md, sach = _trich_dan(self.out)
        self.td = TrichDan(md, sach)
        self.ung_vien = self._ung_vien()

    def _ung_vien(self) -> List[str]:
        """PMID mà TLTK đề cương nộp phải phủ: tài liệu của đề tài (StudySpec), nguồn dẫn ở SAP, đề cương lắp G10, tham
        số G3 (*_source) và danh mục trích dẫn — trừ bài chủ nhiệm đã LOẠI; DOI tài liệu chuẩn quy về PMID. Chỉ giữ
        PMID đã phân giải và sạch rút bài (A12) — nguồn chưa kiểm chứng không vào đề cương nộp."""
        import danh_muc_trich_dan as DMT  # noqa: PLC0415

        ds = [str(x) for x in (self.s("references", "pmids") or [])]
        if _hh().khoi(self.meta):
            ds += list(_hh().PMID_CHUAN)  # GRAMMS + COREQ — vẫn chỉ giữ khi A12 đã xác nhận sạch (lọc ở cuối hàm)
        # 17/11/2026: văn bản cổng dùng CHUNG với trục trich_dan_tong_quan (thêm thiết kế G1 A2 + bộ biến G3 — trước chỉ
        # SAP, đề cương lắp G10 và G3 *_source); DOI tài liệu chuẩn quy về PMID qua cặp đã xác minh.
        ds += DMT.pmid_cua_van_ban(*DMT.van_ban_nguon_cong(self.out, self.study, self.meta))
        loai: set = set()
        try:
            for k, v in (DMT.trich_dan(self.out, self.study) or {}).items():
                if str(k).startswith("pmid:"):
                    ds.append(str(k).split(":", 1)[1])
            loai = {str(k).split(":", 1)[1] for k in (DMT.loai_bo(self.out, self.study) or {}) if
                    str(k).startswith("pmid:")}
        except Exception:  # noqa: BLE001 — danh mục vắng/hỏng: dùng các nguồn còn lại
            pass
        return [p for p in dict.fromkeys(ds) if p in self.td.cho_phep and p not in loai]

    def chuan(self, ten: str) -> str:
        """« [k]» cho chuẩn báo cáo tên `ten` (vd «SPIRIT 2025») khi nó là nguồn đã kiểm chứng của đề tài. Chuẩn mà
        tiêu đề bài gốc không mang tên viết tắt (GRAMMS — O'Cathain 2008) khớp qua `_TIEU_DE_CHUAN`."""
        khoa = _TIEU_DE_CHUAN.get(ten.upper(), ten.upper())
        for p in self.ung_vien:
            if khoa in str((self.td.md.get(p) or {}).get("title") or "").upper():
                k = self.td.so(p)
                return f" [{k}]" if k else ""
        return ""

    def _doc(self, ten: str) -> str:
        try:
            return (self.out / ten).read_text(encoding="utf-8")
        except OSError:
            return ""

    def s(self, *duong: str) -> Any:
        cur: Any = self.spec
        for k in duong:
            cur = cur.get(k) if isinstance(cur, dict) else None
        return cur

    @property
    def tong_hop(self) -> bool:
        return self.study.upper().startswith(TIEN_TO_TONG_HOP) or self.meta.get("study_kind") == "synthetic_test"


# ══════════════════════════════════════════════════════════════════════════════════════════════════ SAP
_MUC_SAP_RE = re.compile(r"^###\s*§\s*(\d+)\s+([^\n]*)$", re.MULTILINE)


def muc_sap(sap_text: str) -> Dict[int, List[Tuple[str, str]]]:
    """Các mục §n của SAP → danh sách (nhãn, nội dung) của từng gạch đầu dòng (dòng con gộp vào nhãn cha)."""
    ra: Dict[int, List[Tuple[str, str]]] = {}
    vi_tri = list(_MUC_SAP_RE.finditer(sap_text))
    for i, m in enumerate(vi_tri):
        than = sap_text[m.end(): vi_tri[i + 1].start() if i + 1 < len(vi_tri) else len(sap_text)]
        than = than.split("\n---", 1)[0].split("\n## ", 1)[0]
        dong: List[Tuple[str, str]] = []
        for ln in than.splitlines():
            mm = re.match(r"^(\s*)-\s+(.*\S)\s*$", ln)
            if not mm:
                continue
            noi = mm.group(2)
            nhan = ""
            m2 = re.match(r"\*\*([^*]+?):?\*\*:?\s*(.*)$", noi)
            if m2:
                nhan, noi = m2.group(1).strip().rstrip(":"), m2.group(2)
            if mm.group(1) and dong:
                dong.append(("•", noi))
            else:
                dong.append((nhan, noi))
        ra[int(m.group(1))] = dong
    return ra


def tieu_de_sap(sap_text: str) -> Dict[int, str]:
    """Tên mục §n của SAP đổi sang chữ thường câu («TỔNG HỢP ĐỊNH LƯỢNG (thay …)» → «Tổng hợp định lượng»).
    Mục «KHÔNG ÁP DỤNG» trả rỗng (bỏ)."""
    ra: Dict[int, str] = {}
    for m in _MUC_SAP_RE.finditer(sap_text):
        t = re.sub(r"\s*\(.*$", "", m.group(2)).replace("+ SEED", "").strip()
        if t.upper().startswith("KHÔNG ÁP DỤNG") or t.upper().startswith("KHÔNG KIỂM ĐỊNH"):
            ra[int(m.group(1))] = ""
            continue
        t = {"TRUSTWORTHINESS": "Độ tin cậy của kết quả định tính"}.get(t.upper(), t)
        ra[int(m.group(1))] = (t[:1] + t[1:].lower()) if t.isupper() else t
    return ra


def bang_sap(sap_text: str) -> List[Tuple[str, List[str]]]:
    """Khung bảng kết quả (§11) của SAP: [(tiêu đề, các dòng bảng markdown)]."""
    m = re.search(r"^###\s*§\s*11\b[^\n]*\n(.*?)(?=^###\s*§|\Z)", sap_text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    ra: List[Tuple[str, List[str]]] = []
    tieu_de, bang = "", []
    for ln in m.group(1).splitlines():
        t = re.match(r"^\*\*(.+?)\*\*\s*$", ln.strip())
        if t:
            if bang:
                ra.append((tieu_de, bang))
            tieu_de, bang = t.group(1).rstrip(":"), []
        elif ln.lstrip().startswith("|"):
            bang.append(ln.strip())
        elif bang and not ln.strip():
            ra.append((tieu_de, bang))
            tieu_de, bang = "", []
    if bang:
        ra.append((tieu_de, bang))
    return [(t, b) for t, b in ra if len(b) >= 2]


def _o_bang(o: str) -> str:
    o = re.sub(r"\[(?:CẦN|CẦN)[^\]]*\]", "", o)
    o = re.sub(r"_{2,}", "…", o)
    o = re.sub(r"\(\s*_\s*\)", "(…)", o)
    return lam_sach(o) if o.strip() else ""


# ══════════════════════════════════════════════════════════════════════════════════════════════════ phiếu & biến số
_NHOM_VAI = (
    ("PHẦN 1. THÔNG TIN HÀNH CHÍNH", ("hanh_chinh", "dinh_danh")),
    ("PHẦN 2. ĐẶC ĐIỂM CHUNG CỦA ĐỐI TƯỢNG", ("hiep_bien", "mo_ta", "yeu_to", "nhieu", "dieu_chinh")),
    ("PHẦN 3. CAN THIỆP / PHƠI NHIỄM", ("phoi_nhiem", "can_thiep", "du_bao", "xet_nghiem")),
    ("PHẦN 4. KẾT CỤC", ("ket_cuc_chinh", "ket_cuc_phu", "su_kien", "thoi_gian", "thoi_gian_den_su_kien", "chi_phi",
                         "tham_chieu", "ket_cuc")),
)


def _lua_chon(chuoi: str) -> List[Tuple[str, str]]:
    ra = []
    for phan in str(chuoi or "").split("|"):
        m = re.match(r"\s*([^,]+?)\s*,\s*(.+?)\s*$", phan)
        if m:
            ra.append((m.group(1), m.group(2)))
    return ra


def _so_hien(s: str) -> str:
    """Số trong phiếu/bảng biến số theo kiểu Việt Nam (soát 20/11/2026): thập phân dấu phẩy («0.1» → «0,1»), nhóm nghìn
    bằng dấu chấm từ 5 chữ số («10000» → «10.000»; số 4 chữ số giữ nguyên để không nhầm năm «1950–2026»); ngày ISO
    «2026-01-01» → «01/01/2026». Chuỗi khác giữ nguyên."""
    s = (s or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m[3]}/{m[2]}/{m[1]}"
    m = re.fullmatch(r"(-?)(\d+)(?:\.(\d+))?", s)
    if not m:
        return s
    nguyen = f"{int(m[2]):,}".replace(",", ".") if len(m[2]) >= 5 else m[2]
    return m[1] + nguyen + (f",{m[3]}" if m[3] else "")


_TU_THU_BAC = re.compile(r"\b(?:rất|hoàn toàn|mức|bình thường|trung lập|nhẹ|vừa|nặng|thấp|cao|kém|tốt)\b", re.I)


def _o_tra_loi(r: Dict[str, str]) -> str:
    kieu = (r.get("Field Type") or "").strip()
    if kieu in ("radio", "dropdown", "checkbox"):
        return "  ".join(f"☐ {ma}. {nhan}" for ma, nhan in _lua_chon(r.get("Choices, Calculations, OR Slider Labels")))
    if kieu in ("yesno", "truefalse"):
        return "☐ 1. Có  ☐ 0. Không"
    kiem = (r.get("Text Validation Type OR Show Slider Number") or "").strip()
    if kiem.startswith("date"):
        return "…… /…… /…………"
    lo, hi = (r.get("Text Validation Min") or "").strip(), (r.get("Text Validation Max") or "").strip()
    if kiem in ("integer", "number") or lo or hi:
        return f"{CHAM}" + (f" (từ {_so_hien(lo)} đến {_so_hien(hi)})" if lo and hi else "")
    if kieu == "calc":
        return "(tính từ các câu trên)"
    return CHAM


def _loai_bien(r: Dict[str, str]) -> str:
    kieu = (r.get("Field Type") or "").strip()
    kiem = (r.get("Text Validation Type OR Show Slider Number") or "").strip()
    if kieu == "calc":
        return "Tính toán"
    if kieu in ("radio", "dropdown", "checkbox", "yesno", "truefalse"):
        lc = _lua_chon(r.get("Choices, Calculations, OR Slider Labels"))
        if kieu == "checkbox":
            return "Định danh (chọn nhiều)"
        if (len(lc) or 2) == 2:
            return "Nhị phân"
        # «Định danh/thứ bậc» (trước 20/11/2026) bỏ lửng cho người đọc: thang có thứ tự (Likert «Rất … / Bình thường /
        # …») là thứ bậc, còn lại là định danh.
        return "Thứ bậc" if sum(1 for _ma, nhan in lc if _TU_THU_BAC.search(nhan)) >= 2 else "Định danh"
    if kiem.startswith("date"):
        return "Ngày tháng"
    if kiem in ("integer", "number"):
        return "Định lượng"
    return "Chuỗi ký tự"


def _vai(n: Nguon) -> Dict[str, Dict[str, str]]:
    return {r.get("bien", ""): r for r in n.ma_tran if r.get("bien")}


def phieu_thu_thap(n: Nguon) -> List[str]:
    """Phiếu thu thập số liệu dựng từ từ điển dữ liệu (đã chốt ở G3/G5), chia phần theo vai trò biến."""
    if not n.tu_dien:
        return [f"Phiếu thu thập số liệu: {CHAM}"]
    vai = _vai(n)
    nhom: Dict[str, List[Dict[str, str]]] = {t: [] for t, _ in _NHOM_VAI}
    for r in n.tu_dien:
        ten = r.get("Variable / Field Name") or ""
        v = (vai.get(ten) or {}).get("vai_tro", "")
        mac_dinh = _NHOM_VAI[3][0] if re.search(r"tháng\s*\d|tuần\s*\d|năm\s*\d|sau\s+\d|tại thời điểm",
                                                 r.get("Field Label") or "") else _NHOM_VAI[1][0]
        tieu_de = next((t for t, cac in _NHOM_VAI if v in cac), mac_dinh)
        if ten == "record_id" or ten.startswith("ngay") and not v:
            tieu_de = _NHOM_VAI[0][0]
        nhom[tieu_de].append(r)
    dong: List[str] = []
    stt = 0
    so_phan = 0
    for tieu_de, ds in nhom.items():
        if not ds:
            continue
        # 17/11/2026 (phản biện máy Claude API): phần rỗng bị bỏ mà số giữ nguyên ⇒ «PHẦN 2 → PHẦN 4»; mã biến bọc
        # dấu ` đọc như mã phần mềm. Đánh số liên tục; mã biến để trần (cột «Mã biến» là của người nhập liệu).
        so_phan += 1
        # ngoài f-string: Python 3.11 cấm «\» trong biểu thức f-string
        ten_phan = re.sub(r"^PHẦN \d+\.", f"PHẦN {so_phan}.", tieu_de)
        dong += [f"**{ten_phan}**", "",
                 "| Câu | Nội dung | Trả lời | Mã biến |", "|---|---|---|---|"]
        for r in ds:
            stt += 1
            nhan = lam_sach(r.get("Field Label") or "") or CHAM
            dong.append(f"| {stt} | {nhan} | {_o_tra_loi(r)} | {r.get('Variable / Field Name')} |")
        dong.append("")
    dong.append("Người thu thập: ……………………………   Ngày thu thập: …… /…… /…………")
    return dong


def cong_thuc_doc(calc: Any) -> str:
    """Công thức biến tính toán (trường calc REDCap) dạng người đọc: bỏ ngoặc vuông tên biến, tách round(…, k) thành
    «làm tròn k chữ số thập phân», mũ 2 ⇒ «²». 17/11/2026: trước đó công thức đi qua bộ tách lựa chọn «mã, nhãn» ⇒
    dấu phẩy của round() bị cắt thành «round(([tuoi]*[ast])/(…)) = 2)» (FIB-4 giả lập, BMI của BTM)."""
    t = re.sub(r"\s+", " ", str(calc or "")).strip()
    lam_tron = None
    m = re.fullmatch(r"round\((.*),\s*(\d+)\s*\)", t, re.I)
    if m:
        t, lam_tron = m.group(1).strip(), m.group(2)
    t = re.sub(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", r"\1", t)
    t = re.sub(r"\s*\^\s*2\b", "²", t)
    if not t:
        return "Tính toán từ các biến khác"
    return f"= {t}" + (f" (làm tròn {lam_tron} chữ số thập phân)" if lam_tron else "")


def bang_bien_so(n: Nguon) -> List[str]:
    if not n.tu_dien:
        return [f"Bảng biến số: {CHAM}"]
    vai = _vai(n)
    dong = ["| Mã biến | Tên biến | Loại biến | Giá trị/cách mã hoá | Nguồn thu thập |", "|---|---|---|---|---|"]
    for r in n.tu_dien:
        ten = r.get("Variable / Field Name") or ""
        la_calc = (r.get("Field Type") or "").strip() == "calc"
        lc = [] if la_calc else _lua_chon(r.get("Choices, Calculations, OR Slider Labels"))
        if la_calc:
            ma = cong_thuc_doc(r.get("Choices, Calculations, OR Slider Labels"))
        elif lc:
            ma = "; ".join(f"{a} = {lam_sach(b)}" for a, b in lc)
        elif (r.get("Field Type") or "") in ("yesno", "truefalse"):
            ma = "1 = Có; 0 = Không"
        else:
            lo, hi = (r.get("Text Validation Min") or "").strip(), (r.get("Text Validation Max") or "").strip()
            ma = f"{_so_hien(lo)}–{_so_hien(hi)}" if lo and hi else ("dd/mm/yyyy" if "date" in (r.get(
                "Text Validation Type OR Show Slider Number") or "") else "Giá trị ghi nhận")
        nguon = lam_sach((vai.get(ten) or {}).get("cong_cu", "")) or "Phiếu thu thập số liệu"
        nguon = nguon[:1].upper() + nguon[1:]
        dong.append(f"| {ten} | {lam_sach(r.get('Field Label') or '')} | {_loai_bien(r)} | {ma} | {nguon} |")
    return dong


# ══════════════════════════════════════════════════════════════════════════════════════════════════ phiếu đồng ý
def _khoi_icf(g2_text: str) -> str:
    m = re.search(r"^##\s*TÀI LIỆU 4\b[^\n]*\n(.*?)(?=^##\s*TÀI LIỆU [5-9]\b|\Z)", g2_text, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    k = re.search(r"```\s*\n(.*?)\n```", m.group(1), re.DOTALL)
    return k.group(1) if k else ""


def _la_tieu_de_hoa(chu: str) -> bool:
    """Từ IN HOA của tiêu đề mục (kể cả từ ngắn «Ý», «RO», «KỲ», «HỖ»)."""
    chu = re.sub(r"[^\wÀ-ỹ]", "", chu)
    return bool(chu) and chu == chu.upper() and chu != chu.lower()


# Từ nối cuối dòng ⇒ dòng sau là phần tiếp của câu dù mở đầu bằng chữ hoa («… được bảo vệ theo» ⏎ «Luật …»).
_TU_NOI_CUOI = re.compile(r"(?:\b(?:theo|của|và|với|tại|cho|từ|trong|khi|là|được|các|những|có|không|hoặc|nếu|về|"
                          r"đến|vì|do|bởi|như|mà|thì|để)|[,/(–—-])$", re.IGNORECASE)


def phieu_dong_y(n: Nguon) -> List[str]:
    """Bản thông tin và phiếu đồng ý (Tài liệu 4 của hồ sơ đạo đức) chuyển sang văn bản liền mạch, đã làm sạch.

    Khuôn G2 là khối chữ đơn cách (khung ═/│, dòng ngắt cứng): mục «1. MỤC ĐÍCH…» thành tiêu đề đậm; dòng nối
    (bắt đầu chữ thường) gộp vào đoạn; mỗi câu/ý bắt đầu chữ hoa thành đoạn riêng; ô tích «☐» và các bước thành danh
    sách; mục chỉ để ghi «không áp dụng» (vd mẫu sinh học) và bước «không áp dụng» bị bỏ, các bước đánh số lại."""
    tho = _khoi_icf(n.g2_text)
    if not tho:
        return [f"Bản thông tin và phiếu đồng ý tham gia: {CHAM}"]
    ra: List[str] = []
    doan: List[str] = []
    buoc = 0
    bo_muc = bo_ngoac = False

    def _xa() -> None:
        if doan:
            ra.extend([" ".join(doan), ""])
            doan.clear()

    for ln in tho.splitlines():
        t = ln.strip().strip("│").strip()
        if bo_ngoac:  # đuôi ghi chú ngoặc của tiêu đề mục («… (đề tài có lấy mẫu máu/mô/dịch» ⏎ «cơ thể)»)
            bo_ngoac = ")" not in t
            continue
        if not t or re.fullmatch(r"[─━═\-–—┌┐└┘│\s]+", t):
            _xa()
            continue
        if re.search(r"do AI hỗ trợ soạn thảo|Cần chủ nhiệm kiểm chứng và HĐ|^\"?Tài liệu này", t):
            continue
        if re.search(r"\bDRAFT\b", t):
            t = re.sub(r"\bDRAFT\s*", "", t).strip(" ,—")
        if re.search(r"số IRB|Số phê duyệt", t, re.IGNORECASE):
            t = f"Số phê duyệt của Hội đồng Đạo đức: {CHAM}"
        t = t.replace("(GIẢ LẬP — hồ sơ chưa có)", CHAM).replace("chưa có thông tin", CHAM)
        mt = re.match(r"^(\d+[a-h]?)\.\s+(.+)$", t)
        if mt:
            tu = mt.group(2).split()
            hoa = []
            for w in tu:
                if not _la_tieu_de_hoa(w) and not re.fullmatch(r"[/&–—-]+", w):
                    break
                hoa.append(w)
            if len(hoa) >= 2:
                _xa()
                bo_muc = False
                ra += [f"**{mt.group(1)}. {' '.join(hoa).rstrip(',(')}**", ""]
                du = " ".join(tu[len(hoa):]).strip()
                if du.startswith("(") and ")" not in du:
                    bo_ngoac = True
                elif du and not du.startswith("("):
                    doan.append(lam_sach(du))
                continue
        if re.fullmatch(r"PHẦN [A-ZÀ-ỸĐ ,]+(?:\(.*\))?", t) or t.startswith("PHIẾU ĐỒNG Ý THAM GIA"):
            _xa()
            bo_muc = False
            ra += [f"**{t}**", ""]
            continue
        if bo_muc:
            continue
        if re.search(r"Không áp dụng\s*[—–-]", t):
            if re.match(r"☐\s*Bước", t):
                continue
            k = len(ra) - 1
            while k >= 0 and not ra[k].startswith("**"):
                k -= 1
            if k >= 0 and re.match(r"\*\*\d+[a-h]?\.", ra[k]):  # mục con chỉ ghi «không áp dụng» ⇒ bỏ cả mục
                del ra[k:]
                doan.clear()
                bo_muc = True
                continue
        mb = re.match(r"☐\s*Bước\s*\d+\s*:\s*(.*)$", t)
        if mb:
            _xa()
            buoc += 1
            ra.append(f"- Bước {buoc}: {lam_sach(mb.group(1))}")
            continue
        if t.startswith("☐"):
            _xa()
            ra.append(f"- {t}")
            continue
        if ra and ra[-1].startswith("- ") and not doan and t[:1].islower():
            # dòng ngắt cứng của một gạch đầu dòng (rủi ro dài) — nối lại rồi làm sạch cả dòng
            ra[-1] = ra[-1] + " " + t if ra[-1].startswith("- ☐") else "- " + lam_sach(ra[-1][2:] + " " + t)
            continue
        if re.match(r"^[•✅∎]\s*", t):
            _xa()
            ra.append("- " + lam_sach(re.sub(r"^[•✅∎]\s*", "", t)))
            continue
        if re.match(r"^(?:Họ tên|Ký tên|Ngày)\b", t):
            _xa()
            ra += [re.sub(r"_{3,}", "……………………", lam_sach(t)), ""]
            continue
        sach = lam_sach(t)
        tu_dau = sach.split(" ", 1)[0]
        nhan_manh = len(tu_dau) > 1 and tu_dau == tu_dau.upper() and tu_dau != tu_dau.lower()
        if doan and (sach[:1].isupper() or sach[:1].isdigit()) and doan[-1][-1:] in ".:;)" + "…":
            _xa()  # câu/ý mới
        elif doan and sach[:1].isupper() and not nhan_manh and not _TU_NOI_CUOI.search(doan[-1]):
            _xa()  # ý mới của khuôn (gạch đầu dòng đã mất ký hiệu) — trừ dòng nối sau từ nối / chữ in hoa nhấn mạnh
        doan.append(sach)
    _xa()
    gon, truoc = [], ""
    for d in ra:
        if d == "" and truoc == "":
            continue
        if d and not d.startswith("- ") and truoc.startswith("- "):
            gon.append("")  # kết thúc danh sách trước đoạn/tiêu đề — không để Markdown gộp vào gạch đầu dòng cuối
        gon.append(d)
        truoc = d
    return gon


def _luc_huy_bang_noi(out_dir: Path) -> str:
    """Thời điểm huỷ bảng nối mã theo quy trình dữ liệu ĐÃ CHỐT (`_quy-trinh-du-lieu.csv`, mục huy_bang_noi) — vd «sau
    khi khoá dữ liệu». Chưa chốt ⇒ câu khuôn chung «sau khi kết thúc nghiên cứu».

    17/11/2026 (giả lập dữ liệu trên khung BTM): đơn miễn đồng thuận ghi cứng «huỷ sau khi kết thúc nghiên cứu» trong
    khi mục bảo mật và DMP của CÙNG đề cương in quy trình đã chốt «huỷ sau khi khoá dữ liệu» ⇒ hai thời điểm khác
    nhau."""
    import quy_trinh_du_lieu as QT  # noqa: PLC0415

    dong, _, _ = QT.doc_bang(Path(out_dir))
    for r in dong or []:
        if r.get("muc") == "huy_bang_noi":
            m = re.search(r"h(?:uỷ|ủy)\s+(sau khi [^;.,]+)", unicodedata.normalize("NFC", r.get("gia_tri") or ""))
            if m:
                return m.group(1).strip()
    return "sau khi kết thúc nghiên cứu"


def don_mien_dong_thuan(n: Nguon) -> List[str]:
    hoi_cuu = "RETRO" in str(n.g2.get("recruitment_mode") or "").upper() or "hồi cứu" in lam_sach(
        n.g1.get("design_rationale")).lower()
    ly_do = ("Đề tài chỉ sử dụng dữ liệu hồi cứu trích từ hồ sơ bệnh án; dữ liệu được khử định danh trước khi phân "
             "tích. Việc liên lạc lại từng người bệnh để xin đồng ý là không khả thi, và nghiên cứu không làm thay đổi "
             "chăm sóc của người bệnh nên nguy cơ là tối thiểu.") if hoi_cuu else f"Lý do đề nghị: {CHAM}"
    import can_cu_dao_duc as CCDD  # noqa: PLC0415

    return [ly_do, "", f"Căn cứ đề nghị: {CCDD.CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP}", "",
            "Nhóm nghiên cứu cam kết: chỉ trích những thông tin cần cho mục tiêu nghiên cứu; không ghi họ tên, địa "
            "chỉ, số điện thoại của người bệnh vào phiếu; bảng đối chiếu mã nghiên cứu với hồ sơ được lưu riêng, có "
            f"phân quyền và huỷ {_luc_huy_bang_noi(n.out)}; kết quả chỉ công bố ở dạng tổng hợp.", "",
            "Kính đề nghị Hội đồng Đạo đức xem xét cho phép miễn thủ tục đồng thuận tham gia nghiên cứu.", "",
            "Chủ nhiệm đề tài (ký, ghi rõ họ tên): ……………………………   Ngày: …… /…… /…………"]


# ══════════════════════════════════════════════════════════════════════════════════════════════════ các chương
_TEN_THIET_KE = {
    "rct": "thử nghiệm lâm sàng ngẫu nhiên có đối chứng, song song hai nhánh",
    "cohort": "nghiên cứu thuần tập",
    "case_control": "nghiên cứu bệnh – chứng",
    "cross_sectional": "nghiên cứu cắt ngang mô tả",
    "diagnostic": "nghiên cứu đánh giá độ chính xác chẩn đoán",
    "prediction": "nghiên cứu phát triển và kiểm định mô hình dự báo",
    "sr_ma": "tổng quan hệ thống và phân tích gộp",
    "qualitative": "nghiên cứu định tính",
}
def ten_thiet_ke(n: "Nguon") -> str:
    """Tên thiết kế cho văn xuôi: cắt ngang có mục tiêu PHÂN TÍCH ⇒ «cắt ngang mô tả có phân tích» (17/11/2026 — trục
    mo_ta_thiet_ke TK-01 báo đề cương BTM ghi «cắt ngang mô tả» dù MT3 phân tích yếu tố liên quan)."""
    import skill_standards as SK  # noqa: PLC0415

    ten = _TEN_THIET_KE.get(n.thiet_ke, "")
    if n.thiet_ke == "cross_sectional" and SK.co_muc_tieu_phan_tich(n.g1.get("objectives")):
        ten = "nghiên cứu cắt ngang mô tả có phân tích"
    return ten


_CHUAN = {
    "rct": ("SPIRIT 2025", "CONSORT 2025"), "cohort": ("STROBE", "STROBE"), "case_control": ("STROBE", "STROBE"),
    "cross_sectional": ("STROBE", "STROBE"), "diagnostic": ("STARD 2015", "STARD 2015"),
    "prediction": ("TRIPOD+AI", "TRIPOD+AI"), "sr_ma": ("PRISMA-P 2015", "PRISMA 2020"),
    "qualitative": ("SRQR", "COREQ"),
}
_VIET_TAT = {
    "KTC": "Khoảng tin cậy", "RR": "Tỷ số nguy cơ (risk ratio)", "OR": "Tỷ số chênh (odds ratio)",
    "HR": "Tỷ số rủi ro (hazard ratio)", "ITT": "Phân tích theo ý định điều trị (intention-to-treat)",
    "ICC": "Hệ số tương quan nội cụm (intraclass correlation coefficient)", "DE": "Hiệu ứng thiết kế (design effect)",
    "MI": "Gán đa trị (multiple imputation)", "MAR": "Thiếu ngẫu nhiên (missing at random)",
    "SMS": "Tin nhắn văn bản (short message service)", "PPI": "Thuốc ức chế bơm proton (proton pump inhibitor)",
    "NSAID": "Thuốc chống viêm không steroid", "AUC": "Diện tích dưới đường cong ROC",
    "ROC": "Đường cong đặc tính hoạt động của bộ thu nhận", "ICER": "Tỷ số chi phí – hiệu quả gia tăng",
    "NMB": "Lợi ích ròng tính bằng tiền (net monetary benefit)", "CEAC": "Đường cong chấp nhận chi phí – hiệu quả",
    "WTP": "Ngưỡng sẵn lòng chi trả (willingness to pay)", "ĐTĐ": "Đái tháo đường", "HA": "Huyết áp",
    "SGLT2": "Đồng vận chuyển natri–glucose 2", "FIB-4": "Chỉ số xơ hoá gan FIB-4", "RIS": "Cỡ thông tin cần thiết",
    "TSA": "Phân tích tuần tự thử nghiệm (trial sequential analysis)",
    "RCT": "Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (randomised controlled trial)",
    "SR/MA": "Tổng quan hệ thống/phân tích gộp", "DAG": "Đồ thị nhân quả có hướng không chu trình",
    "VIF": "Hệ số phóng đại phương sai", "SD": "Độ lệch chuẩn", "IQR": "Khoảng tứ phân vị",
    "CRF": "Phiếu thu thập số liệu (case report form)", "TIDieR": "Hướng dẫn mô tả can thiệp TIDieR",
    # 17/11/2026 (phản biện máy, BTM): từ viết tắt dùng trong văn bản mà danh mục thiếu
    "UACR": "Tỷ số albumin/creatinin niệu (urine albumin-to-creatinine ratio)",
    "eGFR": "Mức lọc cầu thận ước tính (estimated glomerular filtration rate)", "BTM": "Bệnh thận mạn",
    "BHYT": "Bảo hiểm y tế", "HIS": "Hệ thống thông tin bệnh viện (hospital information system)",
    "PR": "Tỷ số tỷ lệ hiện mắc (prevalence ratio)", "ACEi": "Thuốc ức chế men chuyển angiotensin",
    "ARB": "Thuốc chẹn thụ thể angiotensin II", "RAASi": "Thuốc ức chế hệ renin–angiotensin–aldosteron",
    "KDIGO": "Tổ chức Cải thiện kết cục toàn cầu về bệnh thận (Kidney Disease: Improving Global Outcomes)",
    "ADA": "Hiệp hội Đái tháo đường Hoa Kỳ (American Diabetes Association)",
    "EPV": "Số biến cố trên mỗi tham số (events per variable)", "BMI": "Chỉ số khối cơ thể (body mass index)",
    "HbA1c": "Huyết sắc tố gắn glucose (glycated haemoglobin)",
    # 21/11/2026 (phản biện máy C1a + chốt K11 chiều ngược): tên chuẩn báo cáo/thẩm định dùng trong văn bản phải có
    # trong danh mục — bộ sinh trích STROBE/CONSORT/PRISMA… ở mục thiết kế mà danh mục bỏ sót.
    "AGReMA": "Hướng dẫn báo cáo phân tích trung gian (A Guideline for Reporting Mediation Analyses)",
    "AGREE": "Công cụ thẩm định hướng dẫn thực hành lâm sàng (Appraisal of Guidelines for Research and Evaluation)",
    "AMSTAR": "Công cụ đánh giá chất lượng tổng quan hệ thống (A MeaSurement Tool to Assess systematic Reviews)",
    "CARE": "Hướng dẫn báo cáo ca lâm sàng (CAse REport guidelines)",
    "CHEERS": "Chuẩn báo cáo đánh giá kinh tế y tế (Consolidated Health Economic Evaluation Reporting Standards)",
    "CONSORT": "Hướng dẫn báo cáo thử nghiệm ngẫu nhiên có đối chứng (Consolidated Standards of Reporting Trials)",
    "COREQ": "Tiêu chí hợp nhất báo cáo nghiên cứu định tính (Consolidated Criteria for Reporting Qualitative "
             "Research)",
    "COSMIN": "Hướng dẫn chọn lựa công cụ đo lường sức khỏe dựa trên đồng thuận (COnsensus-based Standards for the "
              "selection of health Measurement INstruments)",
    "CROSS": "Bảng kiểm báo cáo nghiên cứu khảo sát (Consensus-Based Checklist for Reporting of Survey Studies)",
    "GRADE": "Hệ thống phân hạng chất lượng chứng cứ và độ mạnh khuyến cáo (Grading of Recommendations, Assessment, "
             "Development and Evaluations)",
    "GRIPP2": "Hướng dẫn báo cáo sự tham gia của người bệnh và công chúng (Guidance for Reporting Involvement of "
              "Patients and the Public, phiên bản 2)",
    "MOOSE": "Hướng dẫn báo cáo phân tích gộp nghiên cứu quan sát (Meta-analysis Of Observational Studies in "
             "Epidemiology)",
    "PRISMA": "Hướng dẫn báo cáo tổng quan hệ thống và phân tích gộp (Preferred Reporting Items for Systematic "
              "Reviews and Meta-Analyses)",
    "PRISMA-P": "Hướng dẫn báo cáo đề cương tổng quan hệ thống (PRISMA for systematic review Protocols)",
    "PROBAST": "Công cụ đánh giá nguy cơ sai lệch của nghiên cứu mô hình dự báo (Prediction model Risk Of Bias "
               "ASsessment Tool)",
    "QUADAS": "Công cụ đánh giá chất lượng nghiên cứu độ chính xác chẩn đoán (Quality Assessment of Diagnostic "
              "Accuracy Studies)",
    "RECORD": "Hướng dẫn báo cáo nghiên cứu dùng dữ liệu y tế thu thập thường quy (REporting of studies Conducted "
              "using Observational Routinely-collected health Data)",
    "ROBINS-I": "Công cụ đánh giá nguy cơ sai lệch của nghiên cứu can thiệp không ngẫu nhiên (Risk Of Bias In "
                "Non-randomised Studies of Interventions)",
    "SPIRIT": "Hướng dẫn soạn đề cương thử nghiệm lâm sàng (Standard Protocol Items: Recommendations for "
              "Interventional Trials)",
    "SQUIRE": "Hướng dẫn báo cáo cải tiến chất lượng (Standards for QUality Improvement Reporting Excellence)",
    "SRQR": "Chuẩn báo cáo nghiên cứu định tính (Standards for Reporting Qualitative Research)",
    "STARD": "Hướng dẫn báo cáo nghiên cứu độ chính xác chẩn đoán (Standards for Reporting of Diagnostic Accuracy "
             "Studies)",
    "STROBE": "Hướng dẫn báo cáo nghiên cứu quan sát (Strengthening the Reporting of Observational Studies in "
              "Epidemiology)",
    "TRIPOD": "Hướng dẫn báo cáo mô hình dự báo đa biến (Transparent Reporting of a multivariable prediction model "
              "for Individual Prognosis Or Diagnosis)",
}


def _hh():
    import hon_hop  # noqa: PLC0415 — thiết kế hỗn hợp (17/11/2026)

    return hon_hop


def _danh_sach(x: Any) -> List[str]:
    if isinstance(x, (list, tuple)):
        return [lam_sach(v) for v in x if _co(v)]
    s = lam_sach(x)
    if not s:
        return []
    return [p.strip() for p in re.split(r"\s*;\s*", s) if p.strip()]


def _muc_tieu(n: Nguon) -> List[str]:
    ds = n.g1.get("objectives") or n.s("objectives", "specific") or []
    ds = [_cau(v) for v in (ds if isinstance(ds, list) else [ds]) if _co(v)]
    return ds or [_cau(n.s("objectives", "general"))]


def chuong_dat_van_de(n: Nguon) -> List[str]:
    td = n.td
    van_de = _cau(td.thay(str(n.g1.get("background_problem") or n.s("rationale", "problem") or "")))
    khoang = _cau(td.thay(str(n.g1.get("knowledge_gap") or n.s("rationale", "evidence_gap") or "")))
    dong = ["# 1. ĐẶT VẤN ĐỀ", ""]
    dong_thuan = _cau(td.thay(str(n.s("literature", "consensus") or "")))
    for d in (van_de, dong_thuan, khoang):
        if d:
            dong += [d, ""]
    # 22/11/2026 (STARD 2015 mục 3 — bối cảnh lâm sàng gồm mục đích sử dụng và vai trò của xét nghiệm đánh giá): đề tài
    # chẩn đoán có lời khai của PI (`index_test_role`) ⇒ đặt vấn đề nêu vai trò dự kiến; báo cáo tổng hợp nghiệm thu lấy
    # đặt vấn đề từ đây nên trước đó thiếu mục 3 dù bản thảo G7 đã có
    vai_tro = _thuong(td.thay(str(n.meta.get("index_test_role") or ""))) if n.thiet_ke == "diagnostic" else ""
    if _co(vai_tro):
        dong += [f"Vai trò dự kiến của xét nghiệm đánh giá trong lộ trình chẩn đoán: {vai_tro}.", ""]
    ten = lam_sach(n.meta.get("title") or n.s("title"))
    dong += [f"Xuất phát từ thực tế trên, chúng tôi tiến hành đề tài «{ten}» với các mục tiêu sau:", ""]
    dong += [f"{i}. {m}" for i, m in enumerate(_muc_tieu(n), 1)] + [""]
    return dong


def chuong_muc_tieu(n: Nguon) -> List[str]:
    dong = ["# 2. MỤC TIÊU NGHIÊN CỨU", "", "## 2.1. Mục tiêu", ""]
    chung = _cau(n.g1.get("aim") or n.s("objectives", "general"))
    cu_the = _muc_tieu(n)
    if chung and len(cu_the) > 1:
        dong += [f"**Mục tiêu chung:** {chung}", "", "**Mục tiêu cụ thể:**", ""]
    dong += [f"{i}. {m}" for i, m in enumerate(cu_the, 1)] + [""]
    cau_hoi = _cau(n.g1.get("research_question") or n.s("question", "text"))
    if cau_hoi:
        dong += ["## 2.2. Câu hỏi nghiên cứu", "", cau_hoi, ""]
    h0, h1 = _cau(n.g0.get("hypothesis_h0")), _cau(n.g0.get("hypothesis_h1"))
    gt = str(n.g3.get("hypothesis_type") or n.g3cp.get("hypothesis_type") or "")
    dong += ["## 2.3. Giả thuyết nghiên cứu", ""]
    if n.thiet_ke in ("cross_sectional", "qualitative") or gt.startswith("descriptive"):
        dong += ["Đây là nghiên cứu " + ("định tính" if n.thiet_ke == "qualitative" else "mô tả") +
                 ", không kiểm định giả thuyết thống kê; mục tiêu là "
                 + ("tìm hiểu sâu hiện tượng nghiên cứu." if n.thiet_ke == "qualitative" else
                    "ước lượng chỉ số nghiên cứu với độ chính xác định trước."), ""]
    elif h1:
        dong += [f"- Giả thuyết không (H0): {h0}" if h0 else "", f"- Giả thuyết đối (H1): {h1}", ""]
    else:
        dong += [CHAM, ""]
    return [d for d in dong if d is not None]


_LOAI_BAI = (("sr_ma", "Tổng quan hệ thống/phân tích gộp"), ("guideline", "Hướng dẫn thực hành"),
             ("rct", "Thử nghiệm ngẫu nhiên"), ("observational", "Nghiên cứu quan sát"))


# Dấu hiệu MẠNH của văn bản hướng dẫn/đồng thuận ở tiêu đề (17/11/2026, đề cương BTM): ADA «Standards of Care» nằm ở
# nhánh tổng quan của G0 (PubMed gắn «Review») mà vẫn là hướng dẫn; ngược lại một nghiên cứu quan sát «… according to
# … guidelines …» KHÔNG phải hướng dẫn — chỉ nhắc chữ «guideline» không đủ.
_HUONG_DAN_MANH = re.compile(r"standards of (?:medical )?care|clinical practice guideline|\bguidelines? (?:for|on)\b|"
                             r"recommendations? (?:for|on)\b", re.I)
# 17/11/2026 (kiểm nội dung trích dẫn bằng Claude API): báo cáo hội nghị/đồng thuận — «KDIGO Summit Recommendations
# on …» (PubMed: Journal Article) — từng bị xếp «Hướng dẫn thực hành». Có khuyến nghị nhưng không phải hướng dẫn chính
# thức ⇒ loại riêng, vẫn vào bảng 3.1. Xét TRƯỚC `_HUONG_DAN_MANH` («recommendations on» nằm trong tiêu đề summit).
_DONG_THUAN = re.compile(r"consensus (?:statement|report|recommendations?)|position statement|"
                         r"\bsummit (?:recommendations?|report)|controversies conference", re.I)
LOAI_DONG_THUAN = "Đồng thuận chuyên môn/báo cáo hội nghị"
# Nghiên cứu ĐO sự tuân thủ hướng dẫn («Concordance With … Guidelines for …», «adherence to guidelines») không phải
# hướng dẫn — từng lọt vào suất «hướng dẫn» của bảng 3.1 khi bản summit chuyển sang loại đồng thuận (17/11/2026).
_DO_TUAN_THU = re.compile(r"\b(?:concordance|adherence|compliance|uptake|guideline-directed|according to|"
                          r"in line with)\b", re.I)


def _loai_bai(n: Nguon, pmid: str) -> str:
    """Loại tài liệu: dấu hiệu hướng dẫn MẠNH ở tiêu đề trước, rồi nhánh tìm của G0 (lọc publication type của PubMed);
    ngoài các nhánh ⇒ suy từ tiêu đề."""
    tieu_de = str((n.td.md.get(pmid) or {}).get("title") or "")
    if _DONG_THUAN.search(tieu_de):
        return LOAI_DONG_THUAN
    if _HUONG_DAN_MANH.search(tieu_de) and not _DO_TUAN_THU.search(tieu_de):
        return _LOAI_BAI[1][1]
    for k, nhan in _LOAI_BAI:
        if any(isinstance(x, dict) and str(x.get("pmid")) == pmid for x in n.g0raw.get(k) or []):
            return nhan
    t = str((n.td.md.get(pmid) or {}).get("title") or "").lower()
    if re.search(r"systematic review|meta-analys|umbrella review", t):
        return _LOAI_BAI[0][1]
    if _HUONG_DAN_MANH.search(t) and not _DO_TUAN_THU.search(t):
        return _LOAI_BAI[1][1]
    if re.search(r"randomi[sz]ed|randomi[sz]ation|\btrial\b", t):
        return _LOAI_BAI[2][1]
    if re.search(r"cohort|case-control|cross-sectional|observational", t):
        return _LOAI_BAI[3][1]
    return "Nghiên cứu khác"


def tai_lieu_bang_31(n: Any, loai_nhan: Sequence[str]) -> List[str]:
    """Ứng viên bảng 3.1: đúng loại tài liệu, TRỪ tài liệu chuẩn/phương pháp hệ chèn (SPIRIT 2025, CONSORT, Piaggio…)
    — 17/11/2026 (phản biện máy, 6/16 đề tài): chúng không phải bằng chứng của chủ đề mà từng chiếm suất «hướng dẫn»."""
    try:
        import protocol_checklist_items as PCI  # noqa: PLC0415

        he_thong = {str(v) for v in PCI.cap_doi_pmid_he_thong().values()}
    except Exception:  # noqa: BLE001 — thiếu bảng thì giữ hành vi cũ
        he_thong = set()
    return [p for p in n.ung_vien if _loai_bai(n, p) in loai_nhan and str(p) not in he_thong]


def _tac_gia_to_chuc(tieu_de: str) -> str:
    """Tác giả TỔ CHỨC khi metadata PubMed không có tác giả cá nhân (17/11/2026 — bảng 3.1 từng ghi «Tác giả và cộng
    sự» cho ADA/KDIGO): suy từ tiêu đề; không suy được ⇒ «Nhóm tác giả»."""
    if re.search(r"standards of (?:medical )?care in diabetes", tieu_de, re.I):
        return "Hiệp hội Đái tháo đường Hoa Kỳ (ADA)"
    m = re.match(r"\s*([A-Z]{3,}(?:/[A-Z]{2,})?)\b", tieu_de)
    return m.group(1) if m else "Nhóm tác giả"


def _ngay_vn(x: Any) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(x or ""))
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else ""


def chuong_tong_quan(n: Nguon, con_lai: Sequence[str] = ()) -> List[str]:
    """Tổng quan: chiến lược tìm kiếm (nguồn, ngày, truy vấn, số kết quả theo loại — PRISMA-S), các bằng chứng hiện có
    + bảng tài liệu chính (tổng quan hệ thống, hướng dẫn, thử nghiệm đã kiểm chứng), khoảng trống + đối chiếu sổ đăng
    ký thử nghiệm, khung lý thuyết. Mọi dữ kiện lấy từ G0/G1 đã chạy — không viết thêm điều nguồn không nói."""
    td = n.td
    dong = ["# 3. TỔNG QUAN TÀI LIỆU", ""]
    so = [0]

    def muc(ten: str) -> None:
        so[0] += 1
        dong.extend([f"## 3.{so[0]}. {ten}", ""])

    prov = n.g0raw.get("search_provenance") or {}
    if _co(prov.get("truy_van_goc")):
        muc("Chiến lược tìm kiếm tài liệu")
        dong += [f"Tài liệu được tìm trên {lam_sach(prov.get('co_so_du_lieu')) or 'PubMed'} ngày "
                 f"{_ngay_vn(prov.get('ngay_tra')) or CHAM} với chiến lược tìm kiếm:", "",
                 f"> {str(prov.get('truy_van_goc')).strip()}", ""]
        dem = n.g0raw.get("true_counts") or {}
        phan = [f"{int(dem[k])} {nhan.lower()}" for k, nhan in _LOAI_BAI if isinstance(dem.get(k), (int, float))
                and int(dem[k]) > 0]
        if phan:
            khong = [nhan.lower() for k, nhan in _LOAI_BAI if dem.get(k) == 0]
            dong += [f"Kết quả gồm {', '.join(phan)}" + (f"; không có {', '.join(khong)} được PubMed đánh chỉ mục"
                                                         if khong else "") + ".", ""]
        dong += ["Mọi tài liệu được trích dẫn trong đề cương đã được đối chiếu thông tin thư mục với PubMed và kiểm "
                 "tra tình trạng rút bài trước khi sử dụng.", ""]
    if _co(n.s("rationale", "local_context")):
        muc("Bối cảnh của vấn đề nghiên cứu")
        dong += [_cau(td.thay(str(n.s("rationale", "local_context")))), ""]
    muc("Các bằng chứng hiện có")
    for x in (n.g1.get("evidence_summary") or n.s("literature", "summary"), n.s("literature", "disagreements")):
        if _co(x):
            dong += [_cau(td.thay(str(x))), ""]
    thu_tu = [_LOAI_BAI[0][1], _LOAI_BAI[1][1], LOAI_DONG_THUAN, _LOAI_BAI[2][1], _LOAI_BAI[3][1], "Nghiên cứu khác"]
    chinh = tai_lieu_bang_31(n, thu_tu[:4])
    chinh.sort(key=lambda p: (thu_tu.index(_loai_bai(n, p)),
                              -int(str((td.md.get(p) or {}).get("year") or "0")[:4] or 0)))
    if chinh:
        ten_loai = {_LOAI_BAI[0][1]: "tổng quan hệ thống", _LOAI_BAI[1][1]: "hướng dẫn",
                    LOAI_DONG_THUAN: "đồng thuận chuyên môn", _LOAI_BAI[2][1]: "thử nghiệm"}
        co = [ten_loai[x] for x in thu_tu[:4] if any(_loai_bai(n, p) == x for p in chinh)]
        tieu = ", ".join(co[:-1]) + (" và " if len(co) > 1 else "") + co[-1]
        dong += [f"**Bảng 3.1. Các {tieu} chính liên quan đến đề tài**", "",
                 "| Tài liệu | Năm | Loại nghiên cứu | Tên bài (nguyên văn) |", "|---|---|---|---|"]
        tran = {_LOAI_BAI[0][1]: 5, _LOAI_BAI[1][1]: 3, LOAI_DONG_THUAN: 2, _LOAI_BAI[2][1]: 4}  # cân đối các loại
        dem_loai: Dict[str, int] = {}
        chon = []
        to_chuc_da_co: set = set()
        for p in chinh:
            lb = _loai_bai(n, p)
            m = td.md.get(p) or {}
            # 17/11/2026: mỗi tổ chức tác giả một dòng — ba chương ADA Standards từng chiếm cả ba suất «hướng dẫn», đẩy
            # KDIGO 2024 (hướng dẫn trung tâm của đề tài BTM) ra khỏi bảng
            to_chuc = "" if str(m.get("authors") or "").strip() else _tac_gia_to_chuc(str(m.get("title") or ""))
            if to_chuc and to_chuc != "Nhóm tác giả" and to_chuc in to_chuc_da_co:
                continue
            if dem_loai.get(lb, 0) < tran.get(lb, 0):
                if to_chuc:
                    to_chuc_da_co.add(to_chuc)
                dem_loai[lb] = dem_loai.get(lb, 0) + 1
                chon.append(p)
        for p in chon:
            m = td.md.get(p) or {}
            tg = str(m.get("authors") or "").split(",")[0].strip()
            k = td.so(p)
            ten_tg = f"{tg.split(' ')[0]} và cộng sự" if tg else _tac_gia_to_chuc(str(m.get("title") or ""))
            dong.append(f"| {ten_tg} [{k}] | {str(m.get('year') or '')[:4]} | {_loai_bai(n, p)} | "
                        f"{lam_sach(str(m.get('title') or '')).rstrip('.')} |")
        dong.append("")
    # 20/11/2026 (bác sĩ: hoàn thiện tổng quan; phản biện BTM mục O13): câu cũ «Các tổng quan, nghiên cứu và hướng dẫn
    # liên quan khác đã được rà soát … [15–36]» là khối trích dẫn gộp — không tài liệu nào đỡ một câu cụ thể, Hội đồng
    # coi là trích dẫn độn (K12 chặn). Máy không đọc bài nên không viết thay nhận định; mỗi tài liệu còn lại vì vậy đứng
    # MỘT dòng bảng kèm tên bài nguyên văn — người viết đề cương thay dần bằng câu có số liệu hoặc bỏ tài liệu đó.
    dong_con = []
    for p in con_lai:
        k = n.td.so(p)
        if not k:
            continue
        m = td.md.get(p) or {}
        tg = str(m.get("authors") or "").split(",")[0].strip()
        ten_tg = f"{tg.split(' ')[0]} và cộng sự" if tg else _tac_gia_to_chuc(str(m.get("title") or ""))
        dong_con.append(f"| {ten_tg} [{k}] | {str(m.get('year') or '')[:4]} | {_loai_bai(n, p)} | "
                        f"{lam_sach(str(m.get('title') or '')).rstrip('.')} |")
    if dong_con:
        so_bang = "3.2" if chinh else "3.1"
        dong += [f"Các tài liệu liên quan khác đã được rà soát khi xây dựng đề cương được liệt kê ở Bảng {so_bang}.",
                 "",
                 f"**Bảng {so_bang}. Các tài liệu liên quan khác đã được rà soát**", "",
                 "| Tài liệu | Năm | Loại nghiên cứu | Tên bài (nguyên văn) |", "|---|---|---|---|"] + dong_con + [""]
    muc("Khoảng trống nghiên cứu và đóng góp của đề tài")
    moi = n.g0.get("novelty_justification")
    for x in ((moi,) if _co(moi) else (n.g1.get("knowledge_gap") or n.s("rationale", "evidence_gap"),)):
        if _co(x):
            dong += [_cau(td.thay(str(x))), ""]
    rc = (n.cps.get("G0") or {}).get("registry_check") or {}
    if rc.get("checked") and isinstance(rc.get("n_trials"), int):
        dong += [f"Tra cứu {rc.get('registry') or 'ClinicalTrials.gov'} ngày {_ngay_vn(rc.get('checked_at')) or CHAM} "
                 f"với cùng chiến lược ghi nhận {_n(rc['n_trials'])} hồ sơ đăng ký, trong đó "
                 f"{_n(rc.get('n_active') or 0)} nghiên cứu đang hoặc sắp tuyển người tham gia."
                 + (f" {_cau(n.g0.get('registry_overlap_assessment'))}" if _co(n.g0.get("registry_overlap_assessment"))
                    else ""), ""]
    ly_thuyet = n.s("theory", "framework") or n.s("theory", "not_applicable_rationale")
    if _co(ly_thuyet):
        muc("Khung lý thuyết của nghiên cứu")
        dong += [_cau(td.thay(str(ly_thuyet))), ""]
    return dong


def huong_dan_phong_van(n: Nguon, g: Optional[Dict[str, Any]] = None) -> List[str]:
    """Hướng dẫn phỏng vấn sâu bán cấu trúc (COREQ mục 14). Nguồn: `gate_params.G1` (đề tài định tính) hoặc
    `gate_params.G1.mixed_methods.cau_phan_dinh_tinh` (cấu phần định tính của đề tài hỗn hợp), truyền qua `g`.
    Chủ nhiệm khai `interview_guide` (danh sách {chu_de, cau_hoi, goi_mo[]}) ⇒ in đúng bộ câu hỏi đó; chưa khai ⇒ bộ
    câu hỏi dựng từ hiện tượng trung tâm (mỗi khía cạnh nối bằng «và» thành một câu hỏi chính). Văn bản nộp không
    mang nhãn «bản nháp» — chủ nhiệm sửa trực tiếp; nguồn gốc máy ghi ở dấu `_dau_may_sinh/`."""
    g = n.g1 if g is None else g
    khai = g.get("interview_guide")
    cau: List[Dict[str, Any]] = []
    if isinstance(khai, list):
        for x in khai:
            if isinstance(x, dict) and _co(x.get("cau_hoi")):
                cau.append({"chu_de": lam_sach(x.get("chu_de")), "cau_hoi": _cau(x.get("cau_hoi")),
                            "goi_mo": [_cau(g) for g in (x.get("goi_mo") or []) if _co(g)]})
            elif isinstance(x, str) and _co(x):
                cau.append({"chu_de": "", "cau_hoi": _cau(x), "goi_mo": []})
    nhap = not cau
    if nhap:
        ht = lam_sach(g.get("central_phenomenon") or n.s("outcomes", "primary", "name"))
        m = re.match(r"(.+?)\s+(khi|trong|ở|của)\s+(.+)$", ht)
        khia, boi = ((m.group(1), f"{m.group(2)} {m.group(3)}") if m else (ht, ""))
        mo_dau = f"Anh/chị có thể kể lại câu chuyện của mình {boi}?".replace("  ", " ").replace(" ?", "?")
        cau.append({"chu_de": "Mở đầu", "cau_hoi": mo_dau, "goi_mo": ["Lúc đó anh/chị nghĩ gì, cảm thấy thế nào?"]})
        for k in [x.strip() for x in re.split(r"\s+và\s+|,\s*", khia) if x.strip()]:
            cau.append({"chu_de": k[:1].upper() + k[1:], "cau_hoi": f"Anh/chị có thể chia sẻ về {_thuong(k)} {boi}?",
                        "goi_mo": ["Anh/chị có thể cho một ví dụ cụ thể không?",
                                   "Điều gì khiến anh/chị cảm thấy như vậy?"]})
        cau.append({"chu_de": "Kết thúc", "cau_hoi": "Còn điều gì anh/chị muốn chia sẻ thêm mà chúng tôi chưa hỏi?",
                    "goi_mo": []})
    tl = re.search(r"(\d+\s*[–-]\s*\d+|\d+)\s*phút", lam_sach(g.get("data_collection_method")))
    dong = ["**HƯỚNG DẪN PHỎNG VẤN SÂU BÁN CẤU TRÚC**", ""]
    dong += ["**A. Mở đầu buổi phỏng vấn**", "",
             "- Giới thiệu người phỏng vấn, mục đích nghiên cứu và thời lượng dự kiến"
             + (f" ({tl.group(1)} phút)." if tl else "."),
             "- Nhắc lại quyền từ chối trả lời bất kỳ câu hỏi nào và dừng phỏng vấn bất kỳ lúc nào.",
             "- Xin phép ghi âm; chỉ ghi âm khi người tham gia đồng ý.", "",
             "**B. Câu hỏi chính và câu hỏi gợi mở**", ""]
    for i, c in enumerate(cau, 1):
        dong.append(f"{i}. " + (f"*{c['chu_de']}.* " if c["chu_de"] else "") + c["cau_hoi"])
        dong += [f"   - Gợi mở: {g}" for g in c["goi_mo"]]
    dong += ["", "**C. Kết thúc**", "", "- Tóm tắt lại các ý chính để người tham gia xác nhận hoặc bổ sung.",
             "- Cảm ơn người tham gia; nhắc cách liên hệ nhóm nghiên cứu khi cần.", ""]
    pilot = n.s("data_collection", "pilot") or n.meta.get("pilot")
    if _co(pilot):
        dong += [f"Bộ câu hỏi được thử nghiệm trước: {_thuong(pilot)}.", ""]
    return dong


def doan_co_mau(n: Nguon) -> List[str]:
    """Đoạn cỡ mẫu tiếng Việt dựng từ con số G3 đã chốt (không chép khối «dán đề cương» còn lời dặn dòng lệnh)."""
    c, g3, td = n.g3cp, n.g3, n.td
    loai = str(c.get("effect_type") or g3.get("effect_type") or "").upper()
    an = _so(c.get("alpha") or g3.get("alpha") or 0.05)
    luc = _pt(c.get("power") or g3.get("power") or 0.8)
    chot = c.get("confirmed_n") or g3.get("confirmed_n")
    n_dc = c.get("n_adjusted")
    bo = c.get("dropout")
    nguon_hq, mo_ta_hq = td.nguon(g3.get("effect_source"))
    nguon_p0, _ = td.nguon(g3.get("p0_source"))
    ket_cuc = _thuong((n.g1.get("primary_outcome") or {}).get("name") if isinstance(n.g1.get("primary_outcome"), dict)
                      else n.s("outcomes", "primary", "name"))
    dong: List[str] = []
    if n.thiet_ke == "qualitative":
        quy_tac = _thuong(g3.get("saturation_stopping_rule") or n.g1.get("saturation_criterion"))
        dong.append(f"Nghiên cứu định tính không tính cỡ mẫu theo công thức. Số người tham gia được quyết định theo "
                    f"nguyên tắc bão hoà dữ liệu: {quy_tac}. Dự kiến phỏng vấn khoảng {_n(chot)} người."
                    if quy_tac else f"Dự kiến phỏng vấn khoảng {_n(chot)} người, dừng khi đạt bão hoà dữ liệu.")
        return dong
    if n.thiet_ke == "sr_ma":
        dong.append("Tổng quan hệ thống không tính cỡ mẫu cho một nghiên cứu đơn lẻ; mọi nghiên cứu đáp ứng tiêu chuẩn "
                    "lựa chọn đều được đưa vào. " + _cau(g3.get("confirmed_n_method") or "") +
                    (f" Cỡ thông tin cần thiết cho kết cục chính là {_n(chot)} người." if chot else ""))
        return [d.replace("  ", " ") for d in dong]
    if n.thiet_ke == "prediction" or (chot and not c.get("n_total") and g3.get("confirmed_n_method")):
        cach = _cau(td.thay(str(g3.get("confirmed_n_method") or "")))
        dong.append(f"{cach} Cỡ mẫu được chốt là {_n(chot)} người." if cach else
                    f"Cỡ mẫu được chốt là {_n(chot)} người.")
    elif loai in ("RR", "OR") and c.get("p0"):
        p0 = float(c["p0"])
        hq = float(c.get("effect_val") or g3.get("effect_size") or 0)
        p1 = p0 * hq if loai == "RR" else hq * p0 / (1 - p0 + hq * p0)
        ten_hq = "tỷ số nguy cơ" if loai == "RR" else "tỷ số chênh"
        nhom = "nhóm can thiệp" if n.thiet_ke == "rct" else ("nhóm bệnh" if n.thiet_ke == "case_control"
                                                             else "nhóm phơi nhiễm")
        nhom0 = "nhóm chứng" if n.thiet_ke in ("rct", "case_control") else "nhóm không phơi nhiễm"
        chi_so = ("tỷ lệ phơi nhiễm" if n.thiet_ke == "case_control" else
                  (ket_cuc if ket_cuc.startswith("tỷ lệ") else f"tỷ lệ {ket_cuc}") if ket_cuc else "tỷ lệ kết cục")
        cung_nguon = re.findall(r"\d{5,9}", str(g3.get("p0_source"))) == re.findall(r"\d{5,9}", str(
            g3.get("effect_source")))
        dong.append(
            f"Cỡ mẫu được tính theo công thức so sánh hai tỷ lệ, với mức ý nghĩa α = {an} (hai phía) và lực mẫu "
            f"{luc}. Giả định {chi_so} ở {nhom0} là {_pt(p0)}"
            + (f" theo {nguon_p0}" if nguon_p0 and not cung_nguon else "")
            + f" và {ten_hq} kỳ vọng là {_so(hq)} (tương ứng {_pt(p1)} ở {nhom})"
            + (f", dựa trên {nguon_hq}" if nguon_hq else "") + ". "
            + f"Cỡ mẫu tính được là {_n(c.get('n_per_group'))} người mỗi nhóm (tổng {_n(c.get('n_total'))} người).")
    elif loai == "NI_PROPORTION":
        # 17/11/2026 (phản biện máy): «tỷ lệ tỷ lệ …» khi tên kết cục đã mở đầu bằng «tỷ lệ»
        ty_le_kc = ket_cuc if ket_cuc.startswith("tỷ lệ") else "tỷ lệ " + (ket_cuc or "kết cục")
        dong.append(
            f"Cỡ mẫu được tính cho giả thuyết không kém hơn của hai tỷ lệ, với mức ý nghĩa α = {an} (một phía), lực "
            f"mẫu {luc}, {ty_le_kc} kỳ vọng ở cả hai nhóm là {_pt(c.get('p0'))} và biên không kém "
            f"hơn Δ = {_so(float(c.get('margin') or 0) * 100, 1)} điểm phần trăm"
            + (f" (căn cứ {nguon_hq})" if nguon_hq else "") + ". "
            + f"Cỡ mẫu tính được là {_n(c.get('n_per_group'))} người mỗi nhóm (tổng {_n(c.get('n_total'))} người).")
    elif loai == "HR":
        dong.append(
            f"Cỡ mẫu được tính theo phương pháp Schoenfeld cho kiểm định log-rank, với α = {an} (hai phía), lực mẫu "
            f"{luc}, tỷ số rủi ro kỳ vọng HR = {_so(c.get('effect_val'))}"
            + (f" dựa trên {nguon_hq}" if nguon_hq else "")
            + f" và tỷ lệ biến cố dự kiến trong thời gian theo dõi là {_pt(c.get('p_event'))}. "
            + f"Cỡ mẫu tính được là {_n(c.get('n_total'))} người.")
    elif loai in ("PREVALENCE", "PROPORTION") or c.get("precision"):
        p = c.get("prevalence") or c.get("effect_val") or 0.5
        dong.append(
            f"Cỡ mẫu được tính theo công thức ước lượng một tỷ lệ: n = Z²(1−α/2) × p(1 − p) / d², với độ tin cậy 95%, "
            f"tỷ lệ ước tính p = {_so(p)} (chọn p = 0,5 để có cỡ mẫu lớn nhất khi chưa có số liệu tại cơ sở) và sai "
            f"số tuyệt đối cho phép d = {_so(c.get('precision'))}. Cỡ mẫu tính được là {_n(c.get('n_total'))} người."
            if float(p) == 0.5 else
            f"Cỡ mẫu được tính theo công thức ước lượng một tỷ lệ: n = Z²(1−α/2) × p(1 − p) / d², với độ tin cậy 95%, "
            f"tỷ lệ ước tính p = {_so(p)} và sai số tuyệt đối cho phép d = {_so(c.get('precision'))}. Cỡ mẫu tính "
            f"được là {_n(c.get('n_total'))} người.")
    elif loai == "AUC":
        dong.append(
            f"Cỡ mẫu được tính theo phương pháp Hanley và McNeil để kiểm định diện tích dưới đường cong ROC kỳ vọng "
            f"AUC = {_so(c.get('effect_val'))} so với 0,5, với α = {an} (hai phía), lực mẫu {luc} và tỷ lệ hiện mắc "
            f"{_pt(c.get('prevalence'))}" + (f", theo {nguon_hq}" if nguon_hq else "") + ". "
            + f"Cần {_n(c.get('n_benh'))} người bệnh và {_n(c.get('n_khong_benh'))} người không bệnh "
            f"(tổng {_n(c.get('n_total'))} người).")
    else:
        cong_thuc = lam_sach(re.sub(r"\[CẦN[^\]]*\]\.?", "", str(c.get("formula_used") or "")))
        dong.append(f"Cỡ mẫu được tính theo {_thuong(cong_thuc)}, với α = {an} và lực mẫu {luc}."
                    if cong_thuc else f"Cỡ mẫu: {CHAM}")
    de = c.get("design_effect")
    if isinstance(de, (int, float)) and float(de) > 1:
        nguon_icc, _ = td.nguon(g3.get("icc_source"))
        dong.append(
            f"Do phân bổ theo cụm, cỡ mẫu được nhân với hiệu ứng thiết kế DE = 1 + (m − 1) × ICC = {_so(de)}, với "
            f"m = {_n(c.get('cluster_size'))} người mỗi cụm và ICC = {_so(c.get('icc'))}"
            + (f" theo {nguon_icc}" if nguon_icc else "") + ".")
    if bo and n_dc:
        dong.append(f"Dự trù {_pt(bo)} mất theo dõi hoặc phiếu không dùng được, cỡ mẫu tối thiểu là {_n(n_dc)} người.")
    if chot and n_dc and int(chot) != int(n_dc):
        cum = ""
        if c.get("cluster_size") and int(chot) % int(c["cluster_size"]) == 0:
            cum = f" ({_n(int(chot) // int(c['cluster_size']))} cụm × {_n(c['cluster_size'])} người)"
        dong.append(f"Nhóm nghiên cứu chốt cỡ mẫu {_n(chot)} người{cum}, không thấp hơn cỡ mẫu tối thiểu.")
    elif chot and not n_dc and n.thiet_ke != "prediction":
        dong.append(f"Cỡ mẫu được chốt là {_n(chot)} người.")
    return [" ".join(dong)]


def bang_sai_lech(ds: Any) -> List[str]:
    """Bảng «nguồn sai lệch · chiều ảnh hưởng · biện pháp khống chế» từ sổ kiểm soát sai lệch G1 đã chốt
    (`gate_params.G1.bias_controls` = [{sai_lech, bien_phap, chieu, …}]). 17/11/2026: bộ sinh chỉ đọc khoá cấp ngoài
    cùng của study_meta ⇒ mục sai số của đề cương BTM để trống dù PI đã chốt 11 nguồn sai lệch. Không có sổ ⇒ []."""
    hang = [x for x in (ds if isinstance(ds, list) else []) if isinstance(x, dict) and _co(x.get("sai_lech"))]
    if not hang:
        return []
    ra = ["| Nguồn sai lệch | Chiều ảnh hưởng dự kiến | Biện pháp khống chế |", "|---|---|---|"]
    for x in hang:
        ra.append(f"| {_cau(x.get('sai_lech')).rstrip('.')} | {_cau(x.get('chieu')) or CHAM} | "
                  f"{_cau(x.get('bien_phap')) or CHAM} |")
    return ra + [""]


# ══════════════════════════════════════════════════════════════════════════ mục chuẩn báo cáo theo từng mục (K17)
# 21/11/2026 (bác sĩ: «mọi đề tài, mọi thiết kế phải đạt từng mục chuẩn quốc tế và Việt Nam»). Đo K17 trên 8 đề cương
# giả lập: dữ kiện ĐÃ CHỐT có sẵn (G1 control_source ghi tiêu chí ghép và tỷ lệ chứng/ca, critical_to_quality ghi «cùng
# bộ câu hỏi cho ca và chứng», SAP §7 ghi nhóm nhỏ tiền định, G9 ghi vai trò nhà tài trợ…) nhưng bộ sinh không in ra
# hoặc in vào mục mà chuẩn không tìm. Mỗi hàm dưới đây dựng MỘT mục từ quyết định đã chốt; thiếu dữ kiện ⇒ ô «………»
# cho chủ nhiệm (K17 không nhận dòng còn ô trống là có yếu tố — `kiem_chuan_de_cuong_theo_muc.o_trong_quanh`).
_NHOM_SO_SANH = {"rct": ("nhóm can thiệp", "nhóm chứng"), "cohort": ("nhóm phơi nhiễm", "nhóm không phơi nhiễm"),
                 "case_control": ("nhóm bệnh", "nhóm chứng")}
# Mệnh đề lý do do PI viết trong trường mô tả («…, tỷ lệ 2 chứng : 1 ca, để nhóm chứng đại diện cho…»). Không nhận «vì»,
# «do» — hai từ này trong câu mô tả thường là nguyên nhân/tác nhân («nhập viện vì nôn máu»), không phải lý do chọn.
_LY_DO_RE = re.compile(r"(?:,\s*|\s+[—–]\s+|\s+)((?:để|nhằm|với lý do|lý do là)\s[^;.]*)", re.I)
_TU_CSDL_RE = re.compile(r"cơ sở dữ liệu|\bHIS\b|bệnh án điện tử|eHospital|phần mềm quản lý|trích (?:toàn bộ |xuất )?"
                         r"hồ sơ|khung mẫu", re.I)


def _tach_ly_do(s: str) -> Tuple[str, str]:
    """(phần mô tả, mệnh đề lý do) — lý do chỉ khi PI đã viết («để/nhằm/với lý do…»)."""
    m = _LY_DO_RE.search(s or "")
    if not m:
        return s or "", ""
    return s[:m.start()].rstrip(" ,;—–"), m.group(1).strip()


def nhom_benh_chung(n: "Nguon") -> List[str]:
    """STROBE 6a/6b (bệnh–chứng): định nghĩa và cách xác định ca, nguồn và cách chọn chứng (gồm tiêu chí ghép, số chứng
    mỗi ca), lý do chọn — từ G1 case_definition/control_source. Lý do chỉ lấy khi PI đã viết; không có ⇒ ô trống."""
    chung, ly_do = _tach_ly_do(lam_sach(n.td.thay(str(n.g1.get("control_source") or ""))))
    if not ly_do:
        _, ly_do = _tach_ly_do(lam_sach(n.g1.get("case_definition")))
    return [f"- Nhóm bệnh (định nghĩa và cách xác định ca): {_cau(n.g1.get('case_definition')) or CHAM}",
            f"- Nhóm chứng (nguồn và cách chọn): {_cau(chung) or CHAM}",
            f"- Lý do chọn nhóm bệnh và nhóm chứng: {_cau(ly_do) or CHAM}"]


def giai_doan_thu_thap(n: "Nguon") -> str:
    """STROBE 5 «giai đoạn tuyển chọn/thu thập»: cách và lịch thu thập đã chốt ở G1 (data_collection_method,
    follow_up_schedule); mốc ngày nằm ở dòng thời gian nghiên cứu ngay trên. Không có ⇒ ô trống."""
    cach = re.sub(r"^thu mới\s*:\s*", "", _thuong(n.g1.get("data_collection_method")), flags=re.I)
    lich = _thuong(n.g1.get("follow_up_schedule"))
    phan = [x for x in (cach, lich) if x and not x.lower().startswith("không áp dụng")]
    if not phan:
        return f"- Giai đoạn thu thập số liệu: {CHAM}"
    return f"- Giai đoạn thu thập số liệu: trong thời gian nghiên cứu, {'; '.join(phan)}."


def dieu_kien_loc(n: "Nguon") -> List[str]:
    """RECORD 6.1: quần thể lấy từ cơ sở dữ liệu ⇒ nêu điều kiện lọc hồ sơ = tiêu chuẩn chọn/loại đã chốt (kèm mã ICD
    nếu PI đã ghi). Đề tài tuyển mới không có dòng này."""
    nguon = " ".join(lam_sach(n.g1.get(k)) for k in ("recruitment_strategy", "data_collection_method"))
    if n.thiet_ke in ("sr_ma", "qualitative") or not _TU_CSDL_RE.search(nguon) or re.search(r"thu mới", nguon, re.I):
        return []
    chon = [_thuong(x) for x in _danh_sach(n.g1.get("inclusion_criteria") or n.s("population", "inclusion"))]
    loai = [_thuong(x) for x in _danh_sach(n.g1.get("exclusion_criteria") or n.s("population", "exclusion"))]
    if not chon:
        return [f"- Điều kiện lọc hồ sơ trên cơ sở dữ liệu: {CHAM}"]
    return ["- Điều kiện lọc hồ sơ trên cơ sở dữ liệu: " + "; ".join(chon)
            + (f"; loại hồ sơ có: {'; '.join(loai)}" if loai else "") + "."]


DAU_DOI_CHIEU_MA = "@@DOI_CHIEU_MA@@"


def kiem_dinh_ma(n: "Nguon", van: str) -> List[str]:
    """RECORD 6.2: đề tài dùng dữ liệu thường quy và xác định quần thể/biến bằng mã (ICD…) — đo trên TOÀN văn bằng CHÍNH
    điều kiện của K17 (21/11/2026: giả lập thuần tập sống còn có sổ sai lệch «sai lệch thông tin do mã chẩn đoán» nên
    K17 đòi mục này, còn bộ sinh chỉ tìm mã ở quần thể/cách đo kết cục) ⇒ nêu bước đối chiếu mã với hồ sơ gốc mà PI đã
    chốt (G1 critical_to_quality / monitoring_plan / biện pháp trong sổ sai lệch có «kiểm/đối chiếu … hồ sơ/phim/xét
    nghiệm»). Không có ⇒ ô trống."""
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    van = van.replace(DAU_DOI_CHIEU_MA, "").replace(DAU_THUONG_QUY, "")
    if n.thiet_ke in ("sr_ma", "qualitative") or not du_lieu_thuong_quy(n, van) or not KCM.co_dieu_kien(
            KCM.dieu_kien_muc("RECORD 2015", "6.2"), van):
        return []
    cum_ds = [c for k in ("critical_to_quality", "monitoring_plan") for c in _danh_sach(n.g1.get(k))]
    cum_ds += [c for x in (n.g1.get("bias_controls") or []) if isinstance(x, dict)
               for c in _danh_sach(x.get("bien_phap"))]
    for cum in cum_ds:
        if re.search(r"\b(kiểm|đối chiếu|xác nhận|thẩm định)\b.{0,60}(hồ sơ|phim|xét nghiệm|bệnh án)", cum, re.I):
            return [f"- Đối chiếu cách xác định bằng mã với hồ sơ gốc: {_thuong(cum)}."]
    return [f"- Đối chiếu cách xác định bằng mã với hồ sơ gốc: {CHAM}"]


def nhom_nho_tien_dinh(n: "Nguon") -> str:
    """Nội dung «nhóm nhỏ tiền định» của SAP §7 đã khoá; '' khi SAP không có hoặc khai không phân tích nhóm nhỏ."""
    for nh, nd in muc_sap(n.sap_text).get(7, []):
        s = lam_sach(nd)
        if re.search(r"nhóm nhỏ|phân nhóm", nh or "", re.I) and _co(s) and not re.match(r"không\b", s, re.I):
            return re.sub(r"\s*[—–-]\s*ghi trước khi xem dữ liệu\.?$", "", s)
    return ""


def bien_dieu_chinh_tac_dong(n: "Nguon") -> List[str]:
    """STROBE 7 «effect modifiers»: biến phân nhóm tiền định của SAP §7 (+ biến vai trò phân nhóm/điều chỉnh tác động
    của ma trận mục tiêu – biến). Không có nhóm nhỏ tiền định ⇒ không có dòng."""
    ds = [x for x in (nhom_nho_tien_dinh(n),) if x]
    ds += [lam_sach(r.get("khai_niem")) for r in n.ma_tran if r.get("vai_tro") in ("phan_nhom", "dieu_chinh")]
    ds = list(dict.fromkeys(x for x in ds if x))
    if not ds:
        return []
    tuong_tac = any(re.search(r"tương tác|interaction", f"{nh} {nd}", re.I)
                    for nh, nd in muc_sap(n.sap_text).get(7, []))
    return ["- Biến điều chỉnh tác động (phân nhóm tiền định" + (", đánh giá bằng số hạng tương tác" if tuong_tac
                                                                  else "") + "): " + "; ".join(ds) + "."]


def do_luong_nhu_nhau(n: "Nguon") -> List[str]:
    """STROBE 8: chất lượng đo lường PI đã chốt (G1 critical_to_quality, monitoring_plan) + tương đồng cách đo giữa các
    nhóm so sánh — một phiếu, một từ điển biến và một lịch thu thập dùng chung cho mọi nhóm (cấu trúc của chính đề
    cương: Phụ lục C, Phụ lục D)."""
    ra = []
    for nhan, k in (("Bảo đảm chất lượng đo lường", "critical_to_quality"), ("Giám sát chất lượng", "monitoring_plan")):
        if _co(n.g1.get(k)):
            ra.append(f"- {nhan}: {_cau(n.g1.get(k))}")
    if n.thiet_ke in _NHOM_SO_SANH:
        a, b = _NHOM_SO_SANH[n.thiet_ke]
        ra.append(f"- Đo lường như nhau giữa các nhóm: {a} và {b} được thu thập bằng cùng một phiếu (Phụ lục C), cùng "
                  "định nghĩa biến (Phụ lục D) và theo cùng lịch thu thập.")
    return ra


def xu_ly_mat_theo_doi(n: "Nguon") -> List[str]:
    """STROBE 12d (thuần tập) / TRIPOD+AI: cách xử lý mất theo dõi ghép từ quyết định đã chốt — câu SAP nói thẳng về mất
    theo dõi/kiểm duyệt; tiêu chí loại liên quan thời gian theo dõi (G1); kết cục chính thiếu do mất theo dõi khi SAP §6
    đưa chính biến kết cục vào kế hoạch dữ liệu thiếu; phân tích độ nhạy theo thời gian theo dõi (SAP §9). Không có ⇒ ô
    trống."""
    if n.thiet_ke not in ("cohort", "prediction"):
        return []
    muc = muc_sap(n.sap_text)
    phan: List[str] = []
    for so in (4, 5, 6, 9):
        for nh, nd in muc.get(so, []):
            if re.search(r"mất theo dõi|mất dấu|kiểm duyệt|censor", f"{nh} {nd}", re.I):
                phan.append(_thuong(f"{nh}: {nd}" if nh and nh != "•" else nd))
    # chỉ tiêu chí loại VỀ thời gian theo dõi («Theo dõi <6 tháng») — không lấy «gãy xương trong 12 tháng trước ngày bắt
    # đầu theo dõi» (tiêu chí bệnh trước đó, chỉ tình cờ chứa chữ «theo dõi»)
    loai = [_thuong(x) for x in _danh_sach(n.g1.get("exclusion_criteria"))
            if re.match(r"(?:thời gian\s+)?theo dõi\s*(?:<|≤|dưới|ít hơn|không đủ|ngắn hơn)", x, re.I)
            or re.search(r"mất (?:theo dõi|dấu)", x, re.I)]
    if loai:
        phan.append("loại khỏi mẫu: " + "; ".join(loai))
    kc = [r.get("bien") for r in n.ma_tran if r.get("vai_tro") == "ket_cuc_chinh" and r.get("bien")]
    s6 = muc.get(6, [])
    chien_luoc = next((lam_sach(nd) for nh, nd in s6 if re.search(r"chiến lược", nh or "", re.I) and _co(nd)), "")
    if chien_luoc and kc and any(re.search(rf"\b{re.escape(b)}\b", n.sap_text) for b in kc) and any(
            re.search(rf"\b{re.escape(b)}\b", nd) for b in kc for _nh, nd in s6):
        phan.append("kết cục chính chưa xác định được do mất theo dõi trước thời điểm đánh giá được xử lý như dữ liệu "
                    f"thiếu theo kế hoạch ở trên ({_thuong(chien_luoc)})")
    phan += ["phân tích độ nhạy: " + _thuong(nd) for _nh, nd in muc.get(9, []) if re.search(r"theo dõi", nd, re.I)]
    phan = list(dict.fromkeys(x for x in phan if x))
    return [f"- Xử lý mất theo dõi: {'; '.join(phan)}." if phan else f"- Xử lý mất theo dõi: {CHAM}"]


def _g9(n: "Nguon") -> Dict[str, Any]:
    return _doc_json(n.out / "G9_PUBLICATION_READINESS.json")


def kinh_phi_tai_tro(n: "Nguon") -> str:
    """STROBE 22: nguồn kinh phí và vai trò của đơn vị tài trợ — khai báo của PI (G9 coi_funding, G7 funding_declared,
    kinh phí đã khai ở study_meta). Thiếu vai trò ⇒ ô trống."""
    cf = _g9(n).get("coi_funding") or {}
    g7 = (n.meta.get("gate_params") or {}).get("G7") or {}
    nguon = next((x for x in (cf.get("funding_statement"), g7.get("funding_declared"), n.meta.get("funding"))
                  if _co(x)), "")
    vai = cf.get("sponsor_role_statement")
    return (f"- Nguồn kinh phí và vai trò của đơn vị tài trợ: {_thuong(nguon) or CHAM}; "
            f"{_thuong(vai) if _co(vai) else CHAM}.")


def chia_se_tai_lieu(n: "Nguon") -> str:
    """RECORD 22.1: cách tiếp cận đề cương, dữ liệu và mã phân tích — khai báo của PI (G9 data_availability, G7
    data_sharing_statement). Không có ⇒ ô trống."""
    da = _g9(n).get("data_availability") or {}
    g7 = (n.meta.get("gate_params") or {}).get("G7") or {}
    noi = [_thuong(x) for x in (da.get("what_data"), da.get("access_criteria"), da.get("access_mechanism"),
                                da.get("available_from"), g7.get("data_sharing_statement")) if _co(x)]
    noi = list(dict.fromkeys(noi))
    return ("- Khả năng tiếp cận đề cương, dữ liệu và mã phân tích: " + ("; ".join(noi) + "." if noi else CHAM))


def lam_sach_so_lieu(n: "Nguon") -> str:
    """RECORD 12.2: phương pháp làm sạch số liệu — đếm từ CHÍNH từ điển dữ liệu G5 (miền giá trị, trường bắt buộc, logic
    nhánh) mà công cụ làm sạch áp khi khoá dữ liệu, cộng bước kiểm chứng nhập liệu đã chốt
    (`_quy-trinh-du-lieu.csv`)."""
    td = n.tu_dien or []
    gioi_han = sum(1 for r in td if _co(r.get("Text Validation Min")) or _co(r.get("Text Validation Max")))
    bat_buoc = sum(1 for r in td if str(r.get("Required Field?") or "").strip().lower() in ("y", "yes"))
    nhanh = sum(1 for r in td if str(r.get("Branching Logic (Show field only if...)") or "").strip())
    kiem = ""
    try:
        import quy_trinh_du_lieu as QT  # noqa: PLC0415

        dong, _, _ = QT.doc_bang(n.out)
        kiem = next((lam_sach(r.get("gia_tri")) for r in dong or [] if r.get("muc") == "kiem_chung"), "")
    except Exception:  # noqa: BLE001 — chưa chốt quy trình dữ liệu: vẫn dựng được phần từ điển
        kiem = ""
    phan = ([f"miền giá trị hợp lệ của {gioi_han} biến"] if gioi_han else []) + (
        [f"{bat_buoc} trường bắt buộc"] if bat_buoc else []) + ([f"logic nhánh của {nhanh} trường"] if nhanh else [])
    if not phan and not kiem:
        return f"- Làm sạch số liệu: {CHAM}"
    cau = ("trước khi khoá dữ liệu, kiểm tra " + ", ".join(phan) + " theo từ điển dữ liệu (Phụ lục D); giá trị ngoài "
           "phạm vi hoặc để trống được tạo truy vấn") if phan else ""
    return "- Làm sạch số liệu: " + "; ".join(x for x in (cau, _thuong(kiem)) if x) + "."


def nguon_so_lieu(n: "Nguon") -> List[str]:
    """Nguồn số liệu đã chốt, bỏ mục nằm trọn trong mục khác («Hồ sơ» khi đã có «Hồ sơ và phim X-quang»)."""
    ds = list(dict.fromkeys(x for x in _danh_sach(n.s("data_collection", "source")) if x))
    return [x for x in ds if not any(x != y and x.lower() in y.lower() for y in ds)]


def du_lieu_thuong_quy(n: "Nguon", van: str) -> bool:
    """Đề tài dùng dữ liệu thu thập thường quy (RECORD 2015) — cùng biểu thức với K17 để hai nơi không lệch nhau."""
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    return KCM.co_dieu_kien(KCM.DU_LIEU_THUONG_QUY, van)


def _mo_ta_chon_mau(n: "Nguon") -> str:
    ma = [str(x) for x in (n.g1.get("sampling_design") or [])]
    if "toan_bo" in ma:
        return "lấy toàn bộ đối tượng đủ tiêu chuẩn trong thời gian nghiên cứu"
    if any("ngau_nhien" in x or "ngẫu nhiên" in x for x in ma):
        return "chọn ngẫu nhiên từ khung mẫu"
    khac = [x.split(":", 1)[1].strip() for x in ma if x.startswith("khac:") and "không áp dụng" not in x]
    return khac[0] if khac else ""


DAU_THUONG_QUY = "@@HE_QUA_DU_LIEU_THUONG_QUY@@"


def he_qua_thuong_quy(n: "Nguon", van: str) -> List[str]:
    """RECORD 19.1 — chỉ khi đề tài dùng dữ liệu thu thập thường quy (đo trên TOÀN văn bằng cùng biểu thức với K17):
    nguồn dữ liệu đã chốt, biến xác định bằng mã chẩn đoán/đơn thuốc (nếu văn bản có), dữ liệu thiếu, nhiễu chưa đo."""
    if n.thiet_ke in ("sr_ma", "qualitative") or not du_lieu_thuong_quy(n, van.replace(DAU_THUONG_QUY, "")):
        return []
    nguon = "; ".join(_thuong(x) for x in nguon_so_lieu(n))
    ma = [r for r, bt in (("mã chẩn đoán", r"\bICD"), ("đơn thuốc", r"đơn thuốc|cấp phát")) if re.search(bt, van)]
    return ["- Hệ quả của dữ liệu thu thập thường quy: dữ liệu " + (f"từ {nguon} " if nguon else "")
            + "được ghi nhận cho mục đích lâm sàng, không được thu thập cho câu hỏi nghiên cứu này, nên có thể "
            + ("phân loại sai các biến xác định bằng " + " và ".join(ma) + ", " if ma else "phân loại sai, ")
            + "có dữ liệu thiếu ở các biến ghi chép không đầy đủ (xử lý theo kế hoạch dữ liệu thiếu) và nhiễu chưa đo "
              "được do các yếu tố không được ghi trong hồ sơ."]


def han_che_suy_rong(n: "Nguon") -> List[str]:
    """STROBE 19/21 · RECORD 19.1: hạn chế (PI khai ở study_meta/StudySpec), sai lệch kèm chiều ảnh hưởng (bảng ở mục
    sai số), hệ quả của dữ liệu thường quy (dấu `DAU_THUONG_QUY`, thay ở `dung_de_cuong` khi đã có toàn văn), phạm vi
    suy rộng (quần thể · nơi · cách chọn mẫu đã chốt)."""
    ra: List[str] = []
    hc = n.meta.get("limitations") or n.s("bias", "limitations")
    if _co(hc):
        ra.append(f"- Hạn chế đã xác định: {_thuong(n.td.thay(str(hc)))}.")
    if any(isinstance(x, dict) and _co(x.get("chieu")) for x in (n.g1.get("bias_controls") or [])):
        ra.append("- Sai lệch và chiều ảnh hưởng dự kiến: các nguồn sai lệch, chiều tác động có thể có lên ước lượng "
                  "và biện pháp khống chế đã nêu ở bảng của mục sai số; kết quả được diễn giải có tính đến các "
                  "chiều lệch này.")
    ra.append(DAU_THUONG_QUY)
    pop = _thuong(n.g1.get("population") or n.s("population", "description"))
    noi = _thuong(n.g1.get("setting") or n.s("design", "setting"))
    if n.thiet_ke == "sr_ma":
        ra.append(f"- Phạm vi suy rộng: kết luận áp dụng cho quần thể của các nghiên cứu được gộp ({pop or CHAM}); "
                  "mức chắc chắn của bằng chứng theo GRADE quyết định mức độ áp dụng vào thực hành.")
    elif n.thiet_ke == "qualitative":
        ra.append(f"- Phạm vi suy rộng: kết quả định tính không nhằm suy rộng thống kê; tính chuyển giao sang bối cảnh "
                  f"khác dựa trên mô tả chi tiết người tham gia ({pop or CHAM}) và bối cảnh ({noi or CHAM}).")
    elif pop or noi:
        cm = _mo_ta_chon_mau(n)
        ra.append(f"- Phạm vi suy rộng: kết quả phản ánh {pop or CHAM} tại {noi or CHAM}" + (f" ({cm})" if cm else "")
                  + "; áp dụng cho cơ sở hoặc quần thể khác cần cân nhắc khác biệt về đặc điểm người bệnh và cách "
                    "chăm sóc.")
    else:
        ra.append(f"- Phạm vi suy rộng: {CHAM}")
    return ra


def ban_luan_du_kien(n: "Nguon", dong_chuong: Sequence[str], so: int) -> List[str]:
    """STROBE 18: khung bàn luận theo TỪNG mục tiêu — nêu đúng bảng/biểu đồ trả lời mục tiêu đó (chú thích «(Mục tiêu
    k)» của khung biểu bảng) và tài liệu đã dẫn ở bằng chứng nền (G1 evidence_summary/background_problem); ý bàn luận
    chính để chủ nhiệm bổ sung."""
    ra = [f"## 5.{so}. Dự kiến bàn luận", ""]
    nen = " ".join(str(n.g1.get(k) or "") for k in ("evidence_summary", "background_problem", "knowledge_gap"))
    so_tl = sorted({n.td.thu_tu.index(p) + 1 for p in re.findall(r"\d{5,9}", nen) if p in n.td.thu_tu})
    ref = ("[" + ", ".join(map(str, so_tl)) + "]") if so_tl else ""
    for k, ten in enumerate(_muc_tieu(n), 1):
        bb = [f"{m.group(1)} {m.group(2)}" for d in dong_chuong
              for m in [re.match(r"^\*\*(Bảng|Hình|Biểu đồ) (5\.\d+)\. (.+)\*\*$", d.strip())]
              if m and re.search(rf"\(Mục tiêu {k}(?!\d)", m.group(3))]
        ra += [f"### 5.{so}.{k}. Bàn luận theo mục tiêu {k}", "",
               f"Bàn luận kết quả trả lời mục tiêu {k} ({_thuong(ten).rstrip('.')})"
               + (f", trình bày ở {', '.join(bb)}" if bb else "")
               + ": so sánh với các nghiên cứu trong nước và quốc tế đã tổng quan" + (f", trước hết là {ref}" if ref
                                                                                     else "")
               + ", nêu điểm giống, điểm khác và lý giải sự khác biệt; diễn giải ý nghĩa của kết quả đối với thực hành "
                 "tại đơn vị.", "", f"Các ý bàn luận chính do chủ nhiệm bổ sung: {CHAM}", ""]
    return ra


def _g1(n: Nguon, k: str) -> str:
    # 17/11/2026: trường G1 do PI viết có thể chứa trích dẫn liền («KDIGO 2024 (PMID 38490803)») ⇒ đổi thành số
    # Vancouver khi PMID đã qua A12, bỏ khi chưa (đề cương nộp không in PMID thô — K6, đo trên BTM).
    v = n.g1.get(k)
    return lam_sach(n.td.thay(str(v)) if isinstance(v, str) else v)


def chuong_phuong_phap(n: Nguon) -> List[str]:
    tk = n.thiet_ke
    dong = ["# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", ""]
    so = [0]

    def muc(ten: str) -> None:
        so[0] += 1
        dong.extend([f"## 4.{so[0]}. {ten}", ""])

    # 4.x Thiết kế
    muc("Thiết kế nghiên cứu")
    ly_do = _g1(n, "design_rationale")
    ly_do = re.sub(r"^.*?Lý do của PI:\s*", "", ly_do)
    ly_do = re.sub(r"^Câu hỏi [^—]*—\s*", "", ly_do)
    de_cuong, bao_cao = _CHUAN.get(tk, ("", ""))
    cau = f"Nghiên cứu được thiết kế theo phương pháp {ten_thiet_ke(n) or lam_sach(n.s('design', 'label'))}."
    tu_tk = set(re.findall(r"\w+", cau.lower()))
    tu_ld = re.findall(r"\w+", ly_do.lower())
    if ly_do and sum(t in tu_tk for t in tu_ld) < 0.6 * len(tu_ld):
        cau += f" {_cau(ly_do)}"
    if de_cuong:
        cau += (f" Đề cương được xây dựng theo hướng dẫn {de_cuong}{n.chuan(de_cuong)}; kết quả sẽ được báo cáo theo "
                f"{bao_cao}{n.chuan(bao_cao)}." if de_cuong != bao_cao else
                f" Đề cương và báo cáo kết quả tuân theo hướng dẫn {bao_cao}{n.chuan(bao_cao)}.")
    HH = _hh()
    hon_hop = bool(HH.khoi(n.meta))
    if hon_hop:
        mt = HH.mo_ta(n.meta)
        ly = _cau(HH.khoi(n.meta).get("ly_do"))
        cau += (f" Nghiên cứu sử dụng thiết kế hỗn hợp định lượng – định tính theo mô hình {mt['ten']}: "
                f"{mt['mo_ta']}; {mt['uu_tien']}." + (f" {ly}" if ly else "")
                + f" Cấu phần định tính được báo cáo theo COREQ{n.chuan('COREQ')} và toàn bộ nghiên cứu hỗn hợp theo "
                  f"GRAMMS{n.chuan('GRAMMS')}.")
    dong += [cau, ""]
    # STROBE 4 (21/11/2026): hướng thời gian thu thập — chế độ tuyển PI đã khai ở G2
    huong = {"PROSPECTIVE_NEW_PARTICIPANTS": "tiến cứu — tuyển mới người tham gia và thu thập số liệu mới trong thời "
                                             "gian nghiên cứu",
             "RETROSPECTIVE_SECONDARY_DATA": "hồi cứu — sử dụng dữ liệu đã có, không tuyển mới người tham gia"}.get(
        str(n.g2.get("recruitment_mode") or "").upper())
    if huong and tk != "sr_ma":
        dong += [f"Hướng thu thập số liệu: {huong}.", ""]
    # Địa điểm, thời gian
    muc("Địa điểm và thời gian nghiên cứu")
    dong += [f"- Địa điểm: {_cau(n.g1.get('setting') or n.s('design', 'setting')) or CHAM}",
             f"- Thời gian nghiên cứu: {_thoi_gian(n.g1.get('study_period') or n.s('design', 'period')) or CHAM}."]
    if tk != "sr_ma":
        dong.append(giai_doan_thu_thap(n))
    dong.append("")
    # Đối tượng
    muc("Đối tượng nghiên cứu" if tk != "sr_ma" else "Tiêu chuẩn lựa chọn nghiên cứu")
    if tk != "sr_ma":
        dong += [_cau(n.g1.get("population") or n.s("population", "description")) or CHAM, ""]
    dong += [f"### 4.{so[0]}.1. Tiêu chuẩn lựa chọn", ""]
    dong += [f"- {_cau(x)}" for x in _danh_sach(n.g1.get("inclusion_criteria") or n.s("population", "inclusion"))]
    dong += ["", f"### 4.{so[0]}.2. Tiêu chuẩn loại trừ", ""]
    dong += [f"- {_cau(x)}" for x in _danh_sach(n.g1.get("exclusion_criteria") or n.s("population", "exclusion"))]
    dong.append("")
    if tk == "case_control":  # STROBE 6a/6b thuộc mục đối tượng (trước 21/11/2026 nằm ở mục riêng, chuẩn không tìm)
        dong += [f"### 4.{so[0]}.3. Nhóm bệnh và nhóm chứng", ""] + nhom_benh_chung(n) + [""]
    # Cỡ mẫu
    muc("Cỡ mẫu và phương pháp chọn mẫu")
    dong += [f"### 4.{so[0]}.1. Cỡ mẫu", ""] + doan_co_mau(n) + [""] + _cau_phuong_phap_hoc(n)
    chon = "" if tk == "sr_ma" else _cau(n.g1.get("recruitment_strategy") or n.s("population", "recruitment")
                                         or n.s("population", "sampling"))
    if tk == "rct":
        chon = (chon + " " if chon else "") + ("Người tham gia đủ tiêu chuẩn và đồng ý tham gia được phân bổ ngẫu "
                                               "nhiên vào hai nhóm (mục ngẫu nhiên hoá dưới đây).")
    if tk != "sr_ma":
        loc = dieu_kien_loc(n)
        dong += [f"### 4.{so[0]}.2. Phương pháp chọn mẫu", "", chon or CHAM, ""] + (loc + [""] if loc else [])
    # Khối riêng theo thiết kế
    if tk == "rct":
        muc("Can thiệp và nhóm chứng")
        ct = n.g1.get("intervention_or_exposure") or n.s("exposure_intervention", "description")
        dong += [f"- Nhóm can thiệp: {_cau(ct)}"]
        if _co(n.g1.get("intervention_dose_adherence")):
            dong.append(f"- Liều lượng và tuân thủ can thiệp: {_cau(n.g1.get('intervention_dose_adherence'))}")
        dong.append(f"- Nhóm chứng: {_cau(n.g1.get('comparator') or n.s('exposure_intervention', 'comparator'))}")
        for nhan, k in (("Lý do chọn nhóm chứng", ("exposure_intervention", "comparator_rationale")),
                        ("Chăm sóc đồng thời", ("exposure_intervention", "concomitant_care"))):
            if _co(n.s(*k)):
                dong.append(f"- {nhan}: {_cau(n.s(*k))}")
        dong.append("")
        muc("Ngẫu nhiên hoá, giấu phân bổ và làm mù")
        for nhan, x in (("Tạo trình tự ngẫu nhiên", n.g1.get("randomisation") or
                         n.s("design_specific", "randomization")),
                        ("Kiểu ngẫu nhiên hoá", n.s("design_specific", "randomization_type")),
                        ("Giấu phân bổ", n.g1.get("allocation_concealment") or n.s("design_specific",
                                                                                     "allocation_concealment")),
                        ("Kiểm soát tiếp cận trình tự", n.s("design_specific", "allocation_access")),
                        ("Làm mù", n.g1.get("blinding") or n.s("design_specific", "blinding")),
                        ("Mở mù", n.s("design_specific", "unblinding_procedure"))):
            if _co(x):
                dong.append(f"- {nhan}: {_cau(x)}")
        dong.append("")
    elif tk == "cohort":
        muc("Phơi nhiễm và nhóm so sánh")
        pn = n.g1.get("intervention_or_exposure") or n.s("exposure_intervention", "description")
        ss = n.g1.get("comparator") or n.s("exposure_intervention", "comparator")
        dong += [f"- Nhóm phơi nhiễm: {_cau(pn)}", f"- Nhóm không phơi nhiễm: {_cau(ss)}",
                 ""]
    elif tk == "case_control":
        muc("Phơi nhiễm quan tâm")
        dong += [f"- Phơi nhiễm: {_cau(n.g1.get('intervention_or_exposure')) or CHAM}"]
        if _co(n.g1.get("comparator")):
            dong.append(f"- Mức so sánh: {_cau(n.g1.get('comparator'))}")
        dong.append("")
    elif tk == "diagnostic":
        muc("Xét nghiệm cần đánh giá và tiêu chuẩn tham chiếu")
        dong += [f"- Bệnh đích: {_cau(n.g1.get('target_condition')) or CHAM}",
                 f"- Xét nghiệm cần đánh giá: {_cau(n.g1.get('intervention_or_exposure')) or CHAM}",
                 f"- Tiêu chuẩn tham chiếu: {_cau(n.g1.get('reference_standard')) or CHAM}", ""]
    elif tk == "prediction":
        muc("Biến dự báo và kết cục dự báo")
        dong += [f"- Các biến dự báo ứng viên: {_cau(n.g1.get('candidate_predictors')) or CHAM}",
                 f"- Khoảng thời gian dự báo: {_cau(n.g1.get('prediction_horizon')) or CHAM}", ""]
    elif tk == "sr_ma":
        muc("Nguồn dữ liệu, chiến lược tìm kiếm và chọn lọc nghiên cứu")
        for nhan, k in (("Nguồn dữ liệu", "information_sources"), ("Chiến lược tìm kiếm", "search_strategy"),
                        ("Ngày tìm kiếm cuối", "search_last_date"), ("Quy trình chọn lọc", "study_selection_process")):
            dong.append(f"- {nhan}: {_cau(n.g1.get(k)) or CHAM}")
        dong.append("")
    elif tk == "qualitative":
        muc("Cách tiếp cận và phương pháp thu thập dữ liệu định tính")
        for nhan, k in (("Hiện tượng trung tâm", "central_phenomenon"), ("Cách tiếp cận", "qualitative_approach"),
                        ("Phương pháp thu thập", "data_collection_method"),
                        ("Tiêu chí bão hoà", "saturation_criterion")):
            dong.append(f"- {nhan}: {_cau(n.g1.get(k)) or CHAM}")
        dong.append("")
    if hon_hop:
        muc("Cấu phần định tính và tích hợp dữ liệu")
        dt, th = HH.dinh_tinh(n.meta), HH.tich_hop(n.meta)
        for nhan, k in (("Hiện tượng trung tâm", "central_phenomenon"), ("Cách tiếp cận", "qualitative_approach"),
                        ("Chọn người tham gia", "chon_mau"), ("Cỡ mẫu dự kiến", "co_mau_du_kien"),
                        ("Phương pháp thu thập", "data_collection_method"),
                        ("Tiêu chí bão hoà", "saturation_criterion"), ("Phân tích dữ liệu định tính", "phan_tich")):
            if _co(dt.get(k)):
                dong.append(f"- {nhan}: {_cau(dt.get(k))}")
        for nhan, k in (("Thời điểm tích hợp", "thoi_diem"), ("Cách tích hợp", "cach"),
                        ("Người thực hiện tích hợp", "nguoi")):
            if _co(th.get(k)):
                dong.append(f"- {nhan}: {_cau(th.get(k))}")
        dong += ["- Hướng dẫn phỏng vấn trình bày ở Phụ lục C; khung bảng tích hợp kết quả trình bày ở mục 5.", ""]
    # Biến số
    muc("Biến số và chỉ số nghiên cứu")
    kc = n.g1.get("primary_outcome") if isinstance(n.g1.get("primary_outcome"), dict) else {}
    ten_kc = lam_sach(n.td.thay(str(kc.get("name") or n.s("outcomes", "primary", "name") or "")))
    do_kc = lam_sach(n.td.thay(str(kc.get("measure") or n.s("outcomes", "primary", "definition") or "")))
    tg_kc = lam_sach(n.td.thay(str(kc.get("timepoint") or n.s("outcomes", "primary", "timepoint") or "")))
    nhan_kc = "Hiện tượng nghiên cứu" if tk == "qualitative" else "Kết cục chính"
    tg = _thuong(tg_kc)
    tg = tg if re.match(r"(?:tại|trong|sau|vào|lúc|khi|ở)\b", tg) else f"tại {tg}"  # không «tại trong 3 tháng»
    dong.append(f"- {nhan_kc}: {ten_kc}" + (f", xác định bằng {_thuong(do_kc)}" if do_kc else "")
                + (f", đánh giá {tg}" if tg_kc else "") + ".")
    phu = _danh_sach(n.g1.get("secondary_outcomes")) or [lam_sach((x or {}).get("name")) for x in
                                                          (n.s("outcomes", "secondary") or []) if isinstance(x, dict)]
    phu = [lam_sach(n.td.thay(str(x))) for x in phu]
    if phu:
        dong.append("- Kết cục phụ: " + "; ".join(_thuong(x) for x in phu if x) + ".")
    # 21/11/2026 (STROBE 7): cắt ngang có mục tiêu phân tích ⇒ nêu biến độc lập (phơi nhiễm/yếu tố khảo sát) của ma trận
    # mục tiêu – biến; thiết kế có nhóm so sánh đã có mục phơi nhiễm riêng.
    if tk == "cross_sectional":
        doc_lap = list(dict.fromkeys(lam_sach(r.get("khai_niem")) for r in n.ma_tran
                                     if r.get("vai_tro") in ("phoi_nhiem", "yeu_to") and _co(r.get("khai_niem"))))
        if doc_lap:
            dong.append("- Biến độc lập (phơi nhiễm, yếu tố khảo sát): " + "; ".join(doc_lap) + ".")
    hiep = [lam_sach(r.get("khai_niem")) for r in n.ma_tran if r.get("vai_tro") in ("hiep_bien", "nhieu", "mo_ta")]
    hiep = list(dict.fromkeys(x for x in hiep if x))
    if hiep:
        dong.append(("- Đặc điểm người tham gia: " if tk == "qualitative" else
                     "- Các biến khác (đặc điểm chung, biến hiệu chỉnh): ") + "; ".join(hiep) + ".")
    dong += bien_dieu_chinh_tac_dong(n)
    dong += ["- Định nghĩa, loại biến và cách mã hoá của từng biến trình bày ở Phụ lục D.", ""]
    # Công cụ & kỹ thuật thu thập
    muc("Công cụ và kỹ thuật thu thập số liệu")
    for nhan, x in (("Công cụ", n.s("data_collection", "instrument", "name")),
                    ("Nguồn số liệu", "; ".join(nguon_so_lieu(n))),
                    ("Thời điểm thu thập", n.g1.get("follow_up_schedule") or
                     n.s("data_collection", "measurement_times")),
                    ("Kiểm soát chất lượng", n.s("data_collection", "quality_control")),
                    ("Thử nghiệm công cụ", n.s("data_collection", "pilot") or n.meta.get("pilot"))):
        if _co(x):
            ten_phieu = "Phiếu trích xuất dữ liệu" if tk == "sr_ma" else "Phiếu thu thập số liệu"
            x = re.sub(r"(?i)^Phiếu trích hồ sơ \(CRF\) dựng từ bộ biến đã duyệt.*$",
                       f"{ten_phieu} (Phụ lục C), xây dựng từ bộ biến số của đề tài", str(x))
            dong.append(f"- {nhan}: {_cau(x)}")
    dong += do_luong_nhu_nhau(n)
    dong.append("")
    # Quy trình
    so_do = n.g1.get("study_schema_timeline") or n.s("design_specific", "schedule")
    if _co(so_do):
        muc("Quy trình nghiên cứu")
        buoc = [b.strip() for b in re.split(r"\s*→\s*", lam_sach(so_do)) if b.strip()]
        dong += ([f"{i}. {_cau(b)}" for i, b in enumerate(buoc, 1)] if len(buoc) > 1 else [_cau(so_do)]) + [""]
    # Sai số
    muc("Sai số và biện pháp khống chế sai số")
    bang_sl = bang_sai_lech(n.g1.get("bias_controls"))
    # RECORD 6.2 — bước đối chiếu mã khống chế sai lệch phân loại (dấu, thay ở `dung_de_cuong` khi đã có toàn văn)
    if bang_sl:
        dong += bang_sl + [DAU_DOI_CHIEU_MA, ""]
    else:
        dong.append(DAU_DOI_CHIEU_MA)
        rui = n.meta.get("bias_risks") or n.s("bias", "risks")
        kiem = n.meta.get("bias_controls") or n.s("bias", "mitigations")
        # 21/11/2026 (STROBE 19): chưa có sổ sai lệch {sai_lech, bien_phap, chieu} ⇒ dòng chiều ảnh hưởng để trống cho
        # chủ nhiệm — không đoán chiều lệch thay PI.
        dong += [f"- Nguồn sai số có thể gặp: {_thuong(rui)}." if _co(rui) else f"- Nguồn sai số: {CHAM}",
                 f"- Biện pháp khống chế: {_thuong(kiem)}." if _co(kiem) else f"- Biện pháp khống chế: {CHAM}",
                 f"- Chiều ảnh hưởng dự kiến của từng nguồn sai lệch: {CHAM}", ""]
    # Phân tích
    muc("Xử lý và phân tích số liệu")
    dong += phan_tich(n)
    dong += xu_ly_mat_theo_doi(n) + [""]
    # Đạo đức
    muc("Đạo đức trong nghiên cứu")
    dong += dao_duc(n) + [""]
    # Hạn chế: chuyển sang chương 5 cùng phạm vi suy rộng (21/11/2026 — STROBE 19/21 thuộc phần bàn luận)
    return dong


_TEN_MUC_SAP = {1: "Quần thể phân tích", 3: "Thống kê mô tả", 4: "Phân tích chính", 5: "Phân tích đa biến",
                6: "Xử lý dữ liệu thiếu", 7: "Phân tích nhóm nhỏ", 8: "Kiểm soát đa so sánh", 9: "Phân tích độ nhạy",
                10: "Phần mềm", 16: "Đánh giá kinh tế"}
_BO_NHAN_SAP = re.compile(r"^(?:Mô tả can thiệp|Cỡ mẫu cuối|Tiêu chí nhận|Tiêu chí loại|Packages|Random seed|"
                          r"Kết cục được coi là kết cục chính|Cảnh báo)", re.IGNORECASE)


def phan_tich(n: Nguon) -> List[str]:
    muc = muc_sap(n.sap_text)
    td = n.td
    dong: List[str] = []
    if not muc:
        pp = n.s("analysis", "primary_method")
        return [f"- Phương pháp phân tích chính: {_cau(pp) or CHAM}"]
    pb = lam_sach(n.s("analysis", "sap_version"))
    dong.append(f"Kế hoạch phân tích thống kê{f' (phiên bản {pb})' if re.fullmatch(r'[0-9.]+', pb) else ''} được khoá "
                "trước khi thu thập số liệu; tóm tắt các phân tích trình bày ở Phụ lục A.")
    dong.append("")
    ten_sap = tieu_de_sap(n.sap_text)
    for so, ten in _TEN_MUC_SAP.items():
        if so not in muc:
            continue
        if so in ten_sap:
            if not ten_sap[so]:
                continue
            ten = ten_sap[so] if so not in (10,) else ten
        cac = [(nh, nd) for nh, nd in muc[so] if not _BO_NHAN_SAP.match(nh or "")]
        cac = [(nh, nd) for i, (nh, nd) in enumerate(cac) if _co(nd) or (
            nh and nh != "•" and i + 1 < len(cac) and cac[i + 1][0] == "•")]
        if not cac:
            continue
        dong.append(f"**{ten}.**")
        dong.append("")
        for nh, nd in cac:
            noi = _cau(td.thay(nd))
            if nh == "•":
                dong.append(f"  - {noi}")
            elif nh and not _co(nd):
                dong.append(f"- {_cau(td.thay(nh)).rstrip('.')}:")
            elif nh:
                dong.append(f"- {_cau(td.thay(nh)).rstrip('.')}: {noi}")
            else:
                dong.append(f"- {noi}")
        dong.append("")
    return dong


def _muc_nguy_co(x: Any) -> str:
    s = lam_sach(x)
    if not s:
        return ""
    muc = re.split(r"\s*\(", s, maxsplit=1)[0].strip().lower()
    return f"Nguy cơ {muc}; Hội đồng Đạo đức quyết định mức nguy cơ cuối cùng."


def _lo_trinh(x: Any) -> str:
    s = str(x or "").upper()
    if "RÚT GỌN" in s and "FULL" in s:
        return ("Đề nghị xét duyệt theo quy trình rút gọn; nếu Hội đồng không chấp nhận, đề cương được xét tại phiên "
                "họp toàn Hội đồng.")
    if "RÚT GỌN" in s or "EXPEDITED" in s:  # 17/11/2026: «EXPEDITED REVIEW» từng in nguyên tiếng Anh
        return "Đề nghị xét duyệt theo quy trình rút gọn."
    if "MIỄN" in s or "EXEMPT" in s:
        return "Đề nghị Hội đồng xem xét miễn xét duyệt."
    if "FULL" in s or "TOÀN HỘI ĐỒNG" in s:
        return "Xét duyệt tại phiên họp toàn Hội đồng."
    return _cau(x)


def _muc_an_toan(muc: Dict[int, List[Tuple[str, str]]]) -> List[str]:
    """§13–§15 của SAP thử nghiệm thành câu: giữa kỳ, hội đồng theo dõi dữ liệu, tổn hại và tuân thủ."""
    def _gt(so: int, mau: str) -> str:
        for nh, nd in muc.get(so, []):
            if re.search(mau, (nh or "") + " " + nd[:40], re.IGNORECASE) and _co(nd):
                return lam_sach(re.sub(r"^[^:]{0,60}:\s*", "", nd) if not nh else nd)
        return ""

    ra = []
    co_gk, ly_gk, dung = _gt(13, r"có phân tích giữa kỳ"), _gt(13, r"nếu không có phân tích"), _gt(13, r"quy tắc dừng")
    if co_gk.lower().startswith("không"):
        ra.append("- Phân tích giữa kỳ: không thực hiện" + (f" vì {_thuong(ly_gk)}" if ly_gk else "") + "."
                  + (f" {_cau(dung)}" if dung else ""))
    elif co_gk:
        ra.append(f"- Phân tích giữa kỳ: {_cau(co_gk)}" + (f" Quy tắc dừng: {_thuong(dung)}." if dung else ""))
    co_dmc, ly_dmc = _gt(14, r"có dmc|có dsmb"), _gt(14, r"nếu không cần")
    if co_dmc.lower().startswith("không"):
        ra.append("- Hội đồng theo dõi dữ liệu và an toàn: không thành lập" + (f" vì {_thuong(ly_dmc)}" if ly_dmc
                                                                               else "") + ".")
    elif co_dmc:
        tp = _gt(14, r"thành phần")
        ra.append(f"- Hội đồng theo dõi dữ liệu và an toàn: {_cau(co_dmc)}" + (f" {_cau(tp)}" if tp else ""))
    th, cach, ngung, tt = (_gt(15, r"định nghĩa tổn hại"), _gt(15, r"cách đánh giá"), _gt(15, r"tiêu chí ngừng"),
                           _gt(15, r"tuân thủ"))
    if th:
        ra.append(f"- Tổn hại: {_cau(th)}" + (f" Cách ghi nhận: {_thuong(cach)}." if cach else ""))
    if ngung:
        ra.append(f"- Ngừng can thiệp ở từng người tham gia: {_cau(ngung)}")
    if tt:
        ra.append(f"- Theo dõi tuân thủ can thiệp: {_cau(tt)}")
    return ra


def dao_duc(n: Nguon) -> List[str]:
    td = n.td
    dong = ["Nghiên cứu tuân thủ Tuyên bố Helsinki và các quy định hiện hành của Việt Nam về đạo đức trong nghiên "
            "cứu y sinh học; đề cương được trình Hội đồng Đạo đức xét duyệt và chỉ triển khai sau khi được chấp "
            "thuận.", ""]
    if n.thiet_ke == "sr_ma":
        dong.append("- Tổng quan chỉ sử dụng dữ liệu đã công bố, không tiếp cận người tham gia hay hồ sơ bệnh án nên "
                    "không cần thủ tục đồng thuận.")
    else:
        dong.append(f"- Mức nguy cơ: {_muc_nguy_co(n.s('ethics', 'risk_level')) or CHAM}")
        dong.append(f"- Hình thức xét duyệt: {_lo_trinh(n.s('ethics', 'irb_route')) or CHAM}")
        # 21/11/2026 (chuẩn Việt Nam, K17): xin miễn ⇒ nêu đúng căn cứ đã đối chiếu nguyên văn (`can_cu_dao_duc.py`)
        dong.append("- Quy trình đồng thuận: " + ("đề nghị Hội đồng Đạo đức chấp thuận miễn lấy bản cung cấp thông tin "
                                                  "nghiên cứu và phiếu tình nguyện tham gia theo Thông tư "
                                                  "43/2024/TT-BYT, Điều 7 khoản 1 điểm b; lý do và căn cứ trình bày "
                                                  "trong đơn đề nghị (Phụ lục B)." if
                                                  n.g2.get("icf_waiver_requested") else
                                                  "người tham gia được giải thích đầy đủ và ký phiếu đồng ý trước khi "
                                                  "tham gia (Phụ lục B)."))
    for nhan, x in (("Bảo mật thông tin", n.s("ethics", "privacy")),
                    ("An toàn người tham gia", n.s("ethics", "safety") or n.meta.get("safety_plan")),
                    ("Đăng ký nghiên cứu", n.s("registration_dissemination", "plan"))):
        if _co(x):
            dong.append(f"- {nhan}: {_thuong(td.thay(str(x)))}.")
    dong += _muc_an_toan(muc_sap(n.sap_text))
    # 22/11/2026 (hội đồng đề tài, F35): câu cũ in cứng «nhóm nghiên cứu cam kết không có xung đột lợi ích» cho MỌI
    # đề tài — tức khai thay người ký, trái hồ sơ khi chủ nhiệm là bác sĩ của đơn vị được đánh giá. Nay đọc xung đột
    # theo hồ sơ + biện pháp quản lý từ study_meta (tools/xung_dot_loi_ich.py, cùng nguồn với hồ sơ G2).
    import xung_dot_loi_ich as XDLI  # noqa: PLC0415

    dong += XDLI.cau_de_cuong(XDLI.doc(n.meta))
    return dong


def chuong_du_kien(n: Nguon) -> List[str]:
    """Chương 5 — biểu bảng chuẩn (19/11/2026, bác sĩ: «phần trình bày biểu bảng chưa có và chưa đúng chuẩn»): dựng từ
    ma trận mục tiêu – biến + bộ biến + đặc tả phân tích qua `khung_bieu_bang` (sơ đồ chọn đối tượng theo chuẩn báo cáo,
    bảng đặc điểm, bảng và biểu đồ cho TỪNG mục tiêu, nhóm nhỏ/độ nhạy, an toàn). Chưa có ma trận (đề tài cũ) ⇒ chép
    khung bảng của kế hoạch phân tích như trước."""
    if n.ma_tran:
        import khung_bieu_bang as KBB  # noqa: PLC0415

        ngu_canh = KBB.nap_ngu_canh(n.out, n.study, thiet_ke=n.thiet_ke, muc_tieu=_muc_tieu(n), tu_dien=n.tu_dien,
                                    ma_tran=n.ma_tran)
        cac_muc = KBB.dung_khung(ngu_canh)
        HH = _hh()
        if HH.khoi(n.meta):
            dong_hh = [[_hoa_dau(lam_sach(r["chu_de"])), _hoa_dau(lam_sach(r["dinh_luong"])) or "…",
                        _hoa_dau(lam_sach(r["dinh_tinh"])) or "…", "Hội tụ / bổ sung / bất đồng"]
                       for r in HH.chu_de_tich_hop(n.meta)]
            cac_muc.append(KBB.Muc("Tích hợp kết quả định lượng và định tính", [KBB.Khung(
                "bang", "Khung bảng tích hợp kết quả định lượng và định tính",
                ["Nội dung tích hợp", "Kết quả định lượng", "Kết quả định tính", "Nhận định tích hợp"],
                dong_hh or [["Nội dung tích hợp", "…", "…", "Hội tụ / bổ sung / bất đồng"]],
                ["Mỗi nội dung được đối chiếu kết quả của hai cấu phần và kết luận là hội tụ, bổ sung cho nhau hoặc "
                 "bất đồng; trường hợp bất đồng được phân tích trong phần bàn luận."])]))
        dong, loi_ve = KBB.ve_chuong(cac_muc, 5, n.out, ve_anh=getattr(n, "ve_anh", False))
        n.loi_ve_bieu_bang = loi_ve
        return dong + [""] + _ban_luan_han_che(n, dong)
    dong = ["# 5. DỰ KIẾN KẾT QUẢ", ""]
    muc = _muc_tieu(n)
    bang = bang_sap(n.sap_text)
    if not bang:
        for i, ten in enumerate(n.s("expected_results", "table_shells") or [], 1):
            dong += [f"**Bảng 5.{i}. {lam_sach(ten)}**", "", "| Nội dung | Kết quả |", "|---|---|", "| … | … |", ""]
    for i, (tieu_de, dong_bang) in enumerate(bang, 1):
        tieu = re.sub(r"^Bảng\s+[\w.]+[,.:]?\s*", "", lam_sach(tieu_de))
        dong += [f"**Bảng 5.{i}. {tieu}**", ""]
        for j, ln in enumerate(dong_bang):
            o = [x.strip() for x in ln.strip().strip("|").split("|")]
            if j == 1 and all(re.fullmatch(r":?-{2,}:?", x) for x in o):
                dong.append(ln)
                continue
            o = [_o_bang(x) for x in o]
            if j >= 2 and ";" in o[0] and not any(o[1:]):
                continue  # dòng liệt kê nhãn biến (tuổi; giới) của khung máy — không phải hàng của bảng
            if j >= 2 and not o[0]:
                o[0] = "…"
            dong.append("| " + " | ".join(x or "…" for x in o) + " |")
        dong.append("")
    HH = _hh()
    if HH.khoi(n.meta):
        so_bang = sum(1 for x in dong if x.startswith("**Bảng 5.")) + 1
        dong += [f"**Bảng 5.{so_bang}. Khung bảng tích hợp kết quả định lượng và định tính (joint display)**", "",
                 "| Nội dung tích hợp | Kết quả định lượng | Kết quả định tính | Nhận định tích hợp |",
                 "|---|---|---|---|"]
        for r in HH.chu_de_tich_hop(n.meta):
            dong.append(f"| {_hoa_dau(lam_sach(r['chu_de']))} | {_hoa_dau(lam_sach(r['dinh_luong'])) or '…'} | "
                        f"{_hoa_dau(lam_sach(r['dinh_tinh'])) or '…'} | Hội tụ / bổ sung / bất đồng |")
        dong += ["", "Mỗi nội dung được đối chiếu kết quả của hai cấu phần và kết luận là hội tụ, bổ sung cho nhau "
                     "hoặc bất đồng; trường hợp bất đồng được phân tích và trình bày trong phần bàn luận.", ""]
    dong += ["Kết quả sẽ được trình bày và bàn luận theo từng mục tiêu nghiên cứu"
             + (f" ({len(muc)} mục tiêu)" if len(muc) > 1 else "")
             + ", đối chiếu với các nghiên cứu đã công bố và nêu rõ ý nghĩa thực hành cũng như hạn chế của nghiên "
               "cứu.", ""]
    return dong + _ban_luan_han_che(n, dong)


def _ban_luan_han_che(n: "Nguon", dong_chuong: Sequence[str]) -> List[str]:
    """Hai mục cuối chương 5 (21/11/2026 — STROBE 18/19/21, RECORD 19.1): «Dự kiến bàn luận» theo từng mục tiêu và
    «Hạn chế của nghiên cứu và phạm vi suy rộng kết quả». Bộ chuyển khuôn BVQY175 giữ nguyên hai mục này (không thêm
    bản thứ hai)."""
    so = 1 + max([int(m.group(1)) for d in dong_chuong for m in [re.match(r"^## 5\.(\d+)\.", d)] if m] or [0])
    return (ban_luan_du_kien(n, dong_chuong, so)
            + [f"## 5.{so + 1}. Hạn chế của nghiên cứu và phạm vi suy rộng kết quả", ""] + han_che_suy_rong(n) + [""])


def _tien_do(chuoi: str) -> List[str]:
    s = lam_sach(chuoi)
    phan = re.findall(r"([^;:]+?)\s+(\d+)\s*tháng", s.split(":", 1)[-1])
    if len(phan) < 2:
        return [f"- Tiến độ: {_cau(s) or CHAM}"]
    dong = ["| Giai đoạn | Thời gian | Tháng thực hiện |", "|---|---|---|"]
    bat_dau = 1
    for ten, so in phan:
        so_i = int(so)
        dong.append(f"| {_cau(ten).rstrip('.')} | {so_i} tháng | {bat_dau}–{bat_dau + so_i - 1} |")
        bat_dau += so_i
    return dong


def chuong_ke_hoach(n: Nguon) -> List[str]:
    dong = ["# 6. KẾ HOẠCH THỰC HIỆN", "", "## 6.1. Nhân lực và phân công nhiệm vụ", ""]
    doi = n.meta.get("team") or n.s("resources", "team")
    dong += [_cau(doi) or CHAM, "", "## 6.2. Tiến độ thực hiện", ""]
    dong += _tien_do(str(n.meta.get("timeline") or n.s("resources", "timeline") or "")) + [""]
    dong += ["## 6.3. Dự trù kinh phí", "", kinh_phi_tai_tro(n), "",
             _cau(n.meta.get("budget") or n.s("resources", "budget")) or CHAM, ""]
    kp = [r for r in (n.g1.get("budget") or []) if isinstance(r, dict) and _co(r.get("nhom"))]
    if kp:
        dong += ["| STT | Khoản chi | Số lượng | Đơn giá | Thành tiền |", "|---|---|---|---|---|"]
        dong += [f"| {i} | {lam_sach(r.get('nhom'))} | {lam_sach(r.get('so_luong')) or CHAM} | "
                 f"{lam_sach(r.get('don_gia')) or CHAM} | {lam_sach(r.get('thanh_tien')) or CHAM} |"
                 for i, r in enumerate(kp, 1)]
    else:
        dong.append(f"Dự toán chi tiết theo biểu mẫu của đơn vị: {CHAM}")
    dong.append("")
    dong += ["## 6.4. Kế hoạch quản lý dữ liệu", ""]
    for nhan, k in (("Lưu trữ", "storage"), ("Phân quyền truy cập", "access"), ("Thời hạn lưu", "retention"),
                    ("Khử định danh", "deidentification")):
        if _co(n.s("data_governance", k)):
            dong.append(f"- {nhan}: {_cau(n.s('data_governance', k))}")
    if n.thiet_ke != "sr_ma":
        dong.append(lam_sach_so_lieu(n))
    dong += ["", "## 6.5. Đăng ký nghiên cứu và phổ biến kết quả", ""]
    for x in (n.s("registration_dissemination", "plan"), n.meta.get("dissemination_plan") or
              n.s("registration_dissemination", "dissemination")):
        if _co(x):
            dong.append(f"- {_cau(x)}")
    dong += [chia_se_tai_lieu(n), ""]
    return dong


def phu_luc_a(n: Nguon) -> List[str]:
    dong = ["# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ", ""]
    if not n.ma_tran:
        return dong + [f"Tóm tắt kế hoạch phân tích: {CHAM}", ""]
    ten_vai = {"ket_cuc_chinh": "Kết cục chính", "ket_cuc_phu": "Kết cục phụ", "phoi_nhiem": "Phơi nhiễm/nhóm so sánh",
               "hiep_bien": "Biến hiệu chỉnh", "mo_ta": "Biến mô tả", "phan_nhom": "Biến phân nhóm",
               "su_kien": "Biến cố", "thoi_gian_den_su_kien": "Thời gian đến biến cố", "chi_phi": "Chi phí",
               "du_bao": "Biến dự báo", "tham_chieu": "Tiêu chuẩn tham chiếu", "xet_nghiem": "Xét nghiệm đánh giá",
               # 17/11/2026 (phản biện máy, BTM): «yeu_to» từng in thành «yeu to» không dấu
               "yeu_to": "Yếu tố liên quan", "nhieu": "Biến nhiễu", "dieu_chinh": "Biến điều chỉnh tác động"}
    pp_chinh = _thuong(n.s("analysis", "primary_method"))
    dong += ["| Mục tiêu | Biến | Vai trò | Cách phân tích |", "|---|---|---|---|"]
    for r in n.ma_tran:
        vai = r.get("vai_tro", "")
        cach = {"ket_cuc_chinh": pp_chinh or "Mô hình chính", "phoi_nhiem": "Biến so sánh của mô hình chính",
                "hiep_bien": "Đưa vào mô hình hiệu chỉnh", "mo_ta": "Thống kê mô tả",
                "yeu_to": "Đưa vào mô hình yếu tố liên quan", "nhieu": "Đưa vào mô hình hiệu chỉnh",
                "ket_cuc_phu": "Theo mục 4.9; diễn giải thăm dò"}.get(vai, "Theo kế hoạch phân tích")
        dong.append(f"| {lam_sach(r.get('muc_tieu'))} | {lam_sach(r.get('khai_niem'))} | "
                    f"{ten_vai.get(vai, 'Biến khác')} | {cach} |")
    return dong + [""]


def thong_tin_chung(n: Nguon) -> List[str]:
    ten = lam_sach(n.meta.get("title") or n.s("title"))
    adm = n.meta.get("administrative") or {}
    pi = lam_sach(adm.get("principal_investigator")) or CHAM
    pi_cd = lam_sach(adm.get("pi_title"))
    thoi_gian = _hoa_dau(_thoi_gian(n.g1.get("study_period") or n.s("design", "period")))
    phien_ban = re.sub(r"-?canary$", "", lam_sach(n.g1.get("protocol_version") or n.s("document", "version")),
                       flags=re.IGNORECASE)
    nam = (re.findall(r"20\d{2}", lam_sach(n.s("document", "date"))) or ["……"])[0]
    # lệ «Đồng bộ đề cương nộp» (viet-ban-thao, 15/11/2026): phiên bản = protocol_version; ngày để dòng chấm cho PI điền
    dong = ["# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", "", f"## {ten.upper()}", "",
            f"**Phiên bản đề cương:** {phien_ban or '1.0'}, ngày ……/……/{nam}", ""]
    dong += ["## THÔNG TIN CHUNG VỀ ĐỀ TÀI", "", "| Mục | Nội dung |", "|---|---|",
             f"| Tên đề tài | {ten} |",
             f"| Chủ nhiệm đề tài | {pi}{', ' + pi_cd if pi_cd else ''} |",
             f"| Đơn vị thực hiện | {lam_sach(n.g1.get('setting') or n.s('design', 'setting')) or CHAM} |",
             f"| Thiết kế | {ten_thiet_ke(n).capitalize() or CHAM} |",
             f"| Thời gian thực hiện | {thoi_gian or CHAM} |",
             f"| Kinh phí | {lam_sach(n.meta.get('budget') or n.s('resources', 'budget')) or CHAM} |",
             f"| Phiên bản đề cương | {phien_ban or '1.0'} |", ""]
    return dong


def tom_tat(n: Nguon) -> List[str]:
    tt = n.meta.get("summary") or n.s("summary")
    if not _co(tt):
        return []
    return ["## TÓM TẮT ĐỀ CƯƠNG", "", _cau(n.td.thay(str(tt))), ""]


def _bo_tltk(van: str) -> str:
    """Bỏ danh mục tài liệu tham khảo (tên tác giả «Nguyen HA», «SD» trong tên tạp chí… không phải chữ viết tắt của
    văn bản) — 20/11/2026, K11 bắt mục «HA», «SD», «DE» thừa ở đề cương máy sinh."""
    m = re.search(r"^#{1,2}\s+(?:\d+\.\s*)?TÀI LIỆU THAM KHẢO.*$", van, re.M)
    if not m:
        return van
    j = re.search(r"^#{1,2}\s+PHỤ LỤC", van[m.end():], re.M)
    return van[:m.start()] + (van[m.end() + j.start():] if j else "")


def _khoa_van_viet(k: str) -> str:
    return k.upper().replace("Đ", "D~")


def viet_tat(than: str) -> List[str]:
    """Bảng chữ viết tắt: chỉ mục DÙNG trong văn bản (ngoài danh mục tài liệu tham khảo; «ĐN1», «MT2» tính là dùng),
    xếp theo bảng chữ cái tiếng Việt (K11 của kiem_de_cuong_nop_hoi_dong)."""
    van = _bo_tltk(than)
    co = [(k, v) for k, v in _VIET_TAT.items()
          if re.search(rf"(?<![\w-]){re.escape(k)}(?:\d|(?![\w-]))", van)]
    if not co:
        return []
    return ["## DANH MỤC CHỮ VIẾT TẮT", "", "| Viết tắt | Nghĩa |", "|---|---|"] + [
        f"| {k} | {v} |" for k, v in sorted(co, key=lambda kv: _khoa_van_viet(kv[0]))] + [""]


def _pmid_phuong_phap_hoc() -> set:
    """PMID tài liệu phương pháp/chuẩn mà hệ chèn (protocol_checklist_items.cap_doi_pmid_he_thong)."""
    try:
        import protocol_checklist_items as PCI  # noqa: PLC0415

        return set(PCI.cap_doi_pmid_he_thong().values())
    except ImportError:
        return set()


def _cau_phuong_phap_hoc(n: Nguon) -> List[str]:
    """Một câu dẫn tài liệu PHƯƠNG PHÁP (cỡ mẫu, chuẩn báo cáo…) mà văn bản cổng dẫn nhưng thân đề cương chưa nhắc tự
    nhiên — đặt ở mục cỡ mẫu thay vì dồn vào phần tổng quan bằng chứng (17/11/2026)."""
    # 20/11/2026 (K12): mỗi tài liệu phương pháp gắn với TÊN BÀI của nó thay vì một ngoặc gộp «[a–b]» — đọc được tài
    # liệu nào đỡ việc gì, và không có khối trích dẫn độn.
    muc = []
    for p in getattr(n, "pp_con_lai", ()) or ():
        k = n.td.so(p)
        ten = lam_sach(str((n.td.md.get(p) or {}).get("title") or "")).rstrip(".")
        if k:
            muc.append(f"“{ten}” [{k}]" if ten else f"tài liệu [{k}]")
    if not muc:
        return []
    # 17/11/2026 (phản biện máy vòng 3, 3/16 đề tài): danh sách gồm cả CHUẨN BÁO CÁO (SPIRIT 2025, CONSORT) — câu cũ
    # gọi chung là «hướng dẫn phương pháp học» cho cỡ mẫu nên bị bắt là trích không đúng ngữ cảnh.
    return [f"Việc xác định cỡ mẫu, lập kế hoạch phân tích và trình bày đề cương tham khảo các tài liệu phương pháp "
            f"học và chuẩn báo cáo sau: {'; '.join(muc)}.", ""]


def _than(n: Nguon, con_lai: Sequence[str]) -> List[str]:
    return (chuong_dat_van_de(n) + chuong_muc_tieu(n) + chuong_tong_quan(n, con_lai) + chuong_phuong_phap(n)
            + chuong_du_kien(n) + chuong_ke_hoach(n))


def dung_de_cuong(n: Nguon) -> str:
    """Toàn văn Markdown của bản đề cương nộp.

    Hai lượt: lượt 1 biết nguồn nào được nhắc tự nhiên trong văn; nguồn ứng viên còn lại (SAP, đề cương lắp, tham số
    G3, danh mục trích dẫn) được dẫn MỘT câu cuối phần bằng chứng ở lượt 2 — số Vancouver theo thứ tự xuất hiện."""
    nhap = TrichDan(n.td.md, n.td.cho_phep)
    that, n.td = n.td, nhap
    n.pp_con_lai = ()
    _than(n, ())
    tu_nhien = set(nhap.thu_tu)
    n.td = TrichDan(that.md, that.cho_phep)
    con_lai = [p for p in n.ung_vien if p not in tu_nhien]
    pp = _pmid_phuong_phap_hoc()
    n.pp_con_lai = [p for p in con_lai if p in pp]  # tài liệu phương pháp ⇒ mục cỡ mẫu (chương 4)
    than = _than(n, [p for p in con_lai if p not in pp])
    tltk = n.td.danh_muc()
    than += ["# 7. TÀI LIỆU THAM KHẢO", ""] + (tltk or [f"Danh mục tài liệu tham khảo: {CHAM}"]) + [""]
    than += phu_luc_a(n)
    if n.thiet_ke != "sr_ma":
        if n.g2.get("icf_waiver_requested"):
            than += ["# PHỤ LỤC B. ĐƠN ĐỀ NGHỊ MIỄN ĐỒNG THUẬN THAM GIA NGHIÊN CỨU", ""] + don_mien_dong_thuan(n) + [""]
        else:
            than += ["# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU", ""] + phieu_dong_y(n) + [""]
    hon_hop = bool(_hh().khoi(n.meta))
    ten_c = ("PHIẾU TRÍCH XUẤT DỮ LIỆU" if n.thiet_ke == "sr_ma" else
             "BỘ CÂU HỎI PHỎNG VẤN VÀ PHIẾU THU THẬP THÔNG TIN" if n.thiet_ke == "qualitative" else
             "PHIẾU THU THẬP SỐ LIỆU VÀ HƯỚNG DẪN PHỎNG VẤN" if hon_hop else
             "PHIẾU THU THẬP SỐ LIỆU")
    than += [f"# PHỤ LỤC C. {ten_c}", ""]
    if n.thiet_ke == "qualitative":
        than += huong_dan_phong_van(n) + ["**PHIẾU THÔNG TIN NGƯỜI THAM GIA**", ""]
    if hon_hop:
        than += ["**C1. PHIẾU THU THẬP SỐ LIỆU (CẤU PHẦN ĐỊNH LƯỢNG)**", ""]
    than += phieu_thu_thap(n) + [""]
    if hon_hop:
        than += ["**C2. CẤU PHẦN ĐỊNH TÍNH**", ""] + huong_dan_phong_van(n, _hh().dinh_tinh(n.meta))
    than += ["# PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ", ""] + bang_bien_so(n) + [""]
    dau = thong_tin_chung(n) + tom_tat(n)
    van = "\n".join(dau + viet_tat("\n".join(than)) + than)
    # RECORD 19.1 cần TOÀN văn (phụ lục, phiếu) để biết đề tài có dùng dữ liệu thường quy không — cùng phép đo của K17
    van = van.replace(DAU_THUONG_QUY, "\n".join(he_qua_thuong_quy(n, van)))
    van = van.replace(DAU_DOI_CHIEU_MA, "\n".join(kiem_dinh_ma(n, van)))
    return don_cuoi(van)


def don_cuoi(van: str) -> str:
    """Lượt dọn cuối trên TOÀN văn bản. 17/11/2026 (phản biện máy, BTM): «… 28/02/2027..» — câu nguồn đã có dấu chấm,
    khuôn thêm một dấu nữa. Không đụng «...» hay dòng chấm «………» để chủ nhiệm điền tay."""
    van = re.sub(r"\n{3,}", "\n\n", van)
    van = re.sub(r"(?<![.…])\.\.(?![.…])", ".", van)
    return _chuan_viet(van).rstrip() + "\n"


_NGAY_ISO_VAN_RE = re.compile(r"(?<![\w-])((?:19|20)\d{2})-([01]\d)-([0-3]\d)(?![\w-])")
_SO_0_CHAM_RE = re.compile(r"(?<![\w.,])0\.(\d+)(?![\d.])")
_DONG_TIM_KIEM_RE = re.compile(r"\[(?:Mesh|tiab|pt|ti|tw|majr|dp)\]", re.I)


def _chuan_viet(van: str) -> str:
    """Chuẩn trình bày tiếng Việt (K11, 20/11/2026) trên văn bản máy sinh: ngoặc kép “…” thay «…», ngày dd/mm/yyyy thay
    ISO. Không đụng danh mục tài liệu tham khảo (giữ nguyên văn), mã trong `…`, dòng chuỗi tìm kiếm."""
    ra, trong_tltk = [], False
    for d in van.split("\n"):
        if re.match(r"^#{1,2}\s", d):
            trong_tltk = "TÀI LIỆU THAM KHẢO" in d.upper()
        if trong_tltk or _DONG_TIM_KIEM_RE.search(d):
            ra.append(d)
            continue
        manh = re.split(r"(`[^`]*`)", d)
        for i in range(0, len(manh), 2):
            x = manh[i].replace("«", "“").replace("»", "”")
            x = _SO_0_CHAM_RE.sub(r"0,\1", x)  # «biên Δ = 0.1» (giá trị G3 chèn thô) ⇒ «0,1» (giả lập RCT NI)
            manh[i] = _NGAY_ISO_VAN_RE.sub(r"\3/\2/\1", x)
        ra.append("".join(manh))
    return "\n".join(ra)


# ══════════════════════════════════════════════════════════════════════════════════════════════════ ghi + kiểm
def la_ban_may(p: Path) -> bool:
    """Tệp hiện có là bản máy CHƯA ai sửa: nội dung khớp sha256 trong dấu `_dau_may_sinh/` (hoặc còn dòng dấu cũ
    `DAU_MAY` trong văn bản — bản sinh trước 17/11/2026)."""
    try:
        noi = p.read_text(encoding="utf-8")
    except OSError:
        return False
    if DAU_MAY in noi[:2000]:
        return True
    import dau_may_sinh as DMS  # noqa: PLC0415

    dau = DMS.doc_dau(p)
    return bool(dau) and dau.get("sha256") == DMS.bam_noi_dung(noi)


def xuat_word(out_dir: Path, study: str, van: str, n: Optional[Nguon] = None) -> Optional[str]:
    """Xuất bản Word của đề cương nộp từ chuỗi Markdown `van` (trang bìa từ study_meta). Dùng chung cho `sinh` và lệnh
    thay chương của `khung_bieu_bang` (19/11/2026). Không có python-docx ⇒ None."""
    out_dir = Path(out_dir)
    n = n or Nguon(out_dir, study)
    docx_p = out_dir / (TEN.format(study=study) + ".docx")
    try:
        import md2docx_vn  # noqa: PLC0415
    except ImportError:
        return None
    # 19/11/2026: văn bản đã tự mang bìa/tiêu đề («# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC», dòng cơ quan chủ quản) ⇒ KHÔNG thêm
    # trang bìa máy — bản cũ thêm cả bìa máy lẫn mục lục tự động TRƯỚC bìa của chính văn bản (hai bìa; C1a/BTM đều xuất
    # lại tay không bìa máy để tránh).
    # 21/11/2026: văn bản theo khuôn hướng dẫn chung BVQY175 (có «# CHƯƠNG 1.») ⇒ chế độ khuôn của md2docx (14pt, giãn
    # 1,5, lề 3,5/2/3/3 cm, bìa không số trang, phần đầu số La Mã, từ Đặt vấn đề số Ả rập, mục lục tự động)
    if re.search(r"^# CHƯƠNG 1\.", van, re.M):
        md2docx_vn.markdown_to_docx(van, docx_p, khuon_bvqy175=True)
        return str(docx_p)
    dau = "\n".join(van.lstrip().splitlines()[:14]).upper()
    if "ĐỀ CƯƠNG NGHIÊN CỨU" in dau or "BỘ QUỐC PHÒNG" in dau or "BỘ Y TẾ" in dau:
        md2docx_vn.markdown_to_docx(van, docx_p)
        return str(docx_p)
    tieu_de = lam_sach(n.meta.get("title") or n.s("title"))
    chu_nhiem = lam_sach((n.meta.get("administrative") or {}).get("principal_investigator"))
    trang_bia = {"org_lines": [lam_sach(x) for x in (n.meta.get("org_lines") or []) if _co(x)],
                 "doc_type": "ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", "title": tieu_de,
                 "meta_lines": [f"Chủ nhiệm đề tài: {chu_nhiem or CHAM}"],
                 "place_year": lam_sach(n.meta.get("place_year")) or ""}
    md2docx_vn.markdown_to_docx(van, docx_p, title_page=trang_bia)
    return str(docx_p)


def dung_khuon(study: str, ep: Optional[bool] = None) -> bool:
    """Có dựng theo khuôn hướng dẫn chung BVQY175 không: cờ dòng lệnh thắng; không cờ ⇒ đề tài mang mã «…BVQY175» (quy
    ước đặt mã đề tài của bệnh viện) dùng khuôn, đề tài khác giữ cấu trúc cũ."""
    return ep if ep is not None else study.upper().endswith("BVQY175")


def sinh(out_dir: Path, study: str, ghi: bool = False, khuon: Optional[bool] = None) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    md_p = out_dir / (TEN.format(study=study) + ".md")
    if not (out_dir / "study_meta.json").is_file():
        return {"ma": 2, "loi": ["thiếu study_meta.json"], "md": str(md_p)}
    if md_p.is_file() and not la_ban_may(md_p):
        return {"ma": 4, "loi": [f"{md_p.name} là bản VIẾT TAY (không mang dấu máy) — không ghi đè"], "md": str(md_p)}
    n = Nguon(out_dir, study)
    n.ve_anh = ghi  # hình/biểu đồ của chương 5 chỉ vẽ ra đĩa khi ghi thật
    van = dung_de_cuong(n)
    khuon_bao_cao: List[str] = []
    if dung_khuon(study, khuon):
        import khuon_de_cuong_bvqy175 as KDC  # noqa: PLC0415

        # 22/11/2026: khối ký bìa phụ theo đơn vị của chủ nhiệm khai trong hồ sơ (Viện/Trung tâm/trực thuộc bệnh viện)
        ket = KDC.chuyen(van, don_vi=KDC.don_vi_ho_so(n.meta))
        van, khuon_bao_cao = ket.md, ket.bao_cao + [f"⚠ {x}" for x in ket.canh_bao]
    kq: Dict[str, Any] = {"md": str(md_p), "so_dong": van.count("\n"), "trich_dan": len(n.td.thu_tu), "ghi": ghi}
    if khuon_bao_cao:
        kq["khuon_bvqy175"] = khuon_bao_cao
    if getattr(n, "loi_ve_bieu_bang", None):
        kq["loi_ve_bieu_bang"] = n.loi_ve_bieu_bang
    if not ghi:
        kq["ma"] = 0
        return kq
    md_p.write_text(van, encoding="utf-8", newline="\n")
    import dau_may_sinh as DMS  # noqa: PLC0415 — dấu bản máy NGOÀI văn bản (văn bản nộp không mang dấu vết máy)

    DMS.ghi_dau(md_p, van, {"study": study}, "sinh_de_cuong_nop_hoi_dong.py")
    kq["docx"] = xuat_word(out_dir, study, van, n)
    import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

    kq["loi"] = KDN.kiem(out_dir, study)
    kq["ma"] = 0 if not kq["loi"] else 1
    return kq


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Sinh đề cương nộp Hội đồng từ quyết định đã chốt.")
    ap.add_argument("--study", required=True)
    ap.add_argument("--exports-root", default=str(BASE / "exports"))
    ap.add_argument("--ghi", action="store_true", help="ghi tệp (mặc định chạy khô)")
    ap.add_argument("--json", action="store_true")
    kh = ap.add_mutually_exclusive_group()
    kh.add_argument("--khuon-bvqy175", dest="khuon", action="store_true", default=None,
                    help="dựng theo khuôn hướng dẫn chung BVQY175 (mặc định cho mã đề tài …BVQY175)")
    kh.add_argument("--khong-khuon", dest="khuon", action="store_false", help="giữ cấu trúc cũ 1–7")
    ap.set_defaults(khuon=None)
    a = ap.parse_args(argv)
    kq = sinh(Path(a.exports_root) / a.study, a.study, ghi=a.ghi, khuon=a.khuon)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        print(("Đã ghi" if kq.get("ghi") else "Chạy khô") + f": {kq.get('md')} ({kq.get('so_dong', 0)} dòng, "
              f"{kq.get('trich_dan', 0)} trích dẫn)")
        for d in kq.get("khuon_bvqy175") or []:
            print(f"  • khuôn hướng dẫn chung BVQY175: {d}")
        for d in kq.get("loi") or []:
            print(f"  ✗ {d}")
        if kq.get("ghi") and not kq.get("loi"):
            print("  ✓ K1–K7 đạt")
    return int(kq.get("ma", 1))


if __name__ == "__main__":
    raise SystemExit(main())
