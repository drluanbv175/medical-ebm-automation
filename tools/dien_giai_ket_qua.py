#!/usr/bin/env python3
"""dien_giai_ket_qua.py — Hợp đồng BẢN DIỄN GIẢI KẾT QUẢ (G6-T3, `dien-giai-ket-qua`) — 10/10/2026.

Bác sĩ giao: «G6-T3 (diễn giải kết quả) đảm bảo các kết quả được diễn giải và trình bày một cách tốt nhất (bao gồm số
liệu, văn phong và bảng biểu)». Trước đó G6-T3 khai đầu ra là tệp script phân tích chung — bản diễn giải không có tệp
riêng, không có gì để kiểm; `gen_research_docx --artifact interpretation` dựng docx từ JSON tự do.

Hợp đồng: `exports/<mã>/G6_DIEN_GIAI_<mã>.md` — năm mục cố định, Bảng kết quả chính có cột cố định, mỗi dòng TRUY
NGUYÊN về một tệp kết quả phân tích có thật (06_ket_qua/… hoặc 06_phan_tich_R/output/…). Công cụ CHỈ kiểm những gì
máy kiểm được — KHÔNG thay người đọc: đúng ý nghĩa lâm sàng, đúng trích y văn vẫn do người chấm chéo
(`phan-tich-thong-ke`, `binh-duyet`, `huong-dan-lam-sang`) và `kiem-chung-trich-dan`.

Ba trục kiểm:
  SỐ LIỆU   — ước lượng điểm và hai cận KTC 95% đọc được, cận dưới ≤ ước lượng ≤ cận trên; p đúng định dạng (không
              «0,000», không > 1; dưới 0,001 ghi «< 0,001»); mỗi số khớp (theo số chữ số thập phân đã báo) một số
              trong tệp kết quả được dẫn ở cột «Nguồn kết quả»; một dấu thập phân thống nhất trong bảng.
  VĂN PHONG — không cụm diễn giải quá mức: «đã chứng minh», «chứng minh rằng», «khẳng định chắc chắn», «xu hướng có ý
              nghĩa», «gần có ý nghĩa», «rất có ý nghĩa thống kê», «p = 0,000»; thiết kế KHÔNG can thiệp (cắt ngang,
              bệnh–chứng, thuần tập, chẩn đoán, dự báo, định tính) không dùng ngôn ngữ nhân quả «gây ra»/«là nguyên
              nhân»; mục 2 phải nói ý nghĩa LÂM SÀNG, mục 4 phải nêu HẠN CHẾ.
  BẢNG BIỂU — mỗi bảng có chú thích «Bảng N.» ngay trên, đủ hàng tiêu đề + hàng gạch, mọi hàng cùng số cột, không ô
              trống (ô không áp dụng ghi «—»), không còn «[CẦN …]».

Cách dùng:
    python3 tools/dien_giai_ket_qua.py mau --study <mã>          # dựng khung (không ghi đè)
    python3 tools/dien_giai_ket_qua.py kiem --study <mã> [--json] [--thiet-ke <mã thiết kế>]
Mã thoát: 0 đạt · 1 còn lỗi · 2 lỗi đầu vào (thiếu đề tài/tệp). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]

TEN_TEP = "G6_DIEN_GIAI_{study}.md"
MUC = ("## 1. Kết quả chính", "## 2. Ý nghĩa thống kê và ý nghĩa lâm sàng", "## 3. Đối chiếu y văn",
       "## 4. Điểm mạnh và hạn chế", "## 5. Hàm ý thực hành và hướng nghiên cứu tiếp")
COT_BANG_CHINH = ("Kết cục", "Thước đo", "Ước lượng điểm", "KTC 95%", "p", "Ý nghĩa lâm sàng", "Nguồn kết quả")
# Thư mục kết quả phân tích — CÙNG bộ mà g6_quality_gate dùng (_THU_MUC_KET_QUA).
THU_MUC_KET_QUA = ("06_ket_qua", "06_phan_tich_R/output")
# SỬA 15/11/2026 (giả lập trọn vòng đề tài thuần tập): run_stats_analysis.py — engine DUY NHẤT, cũng là đường của
# chay_sap_g6.py — ghi kết quả ở GỐC thư mục đề tài (`G6_table4_poisson_pr.txt`, `G6_<id>_analysis_summary.json`…);
# g6_quality_gate đọc cả gốc (`_THU_MUC_KET_QUA` có ""), riêng bản diễn giải từ chối ⇒ người diễn giải dẫn ĐÚNG tệp kết
# quả thật bị báo sai và phải chép số sang 06_ket_qua/ cho vừa luật. Nay nhận thêm tệp kết quả của engine ở gốc — chỉ
# đúng khuôn tên engine ghi, không nhận mọi tệp ở gốc (G6_DIEN_GIAI, SAP… không phải tệp kết quả).
TEP_KET_QUA_GOC = re.compile(r"G6[A-Za-z0-9_-]*_(?:table\w+|analysis_summary|missing_data_summary)\.(?:txt|json|csv)")
DUOI_VAN_BAN = (".txt", ".csv", ".tsv", ".json", ".md", ".log")
THIET_KE_KHONG_CAN_THIEP = ("cross_sectional", "case_control", "cohort", "diagnostic", "prediction", "qualitative")

_CUM_QUA_MUC = (
    (re.compile(r"\bđã\s+chứng\s+minh\b", re.I), "«đã chứng minh» — kết quả một nghiên cứu không «chứng minh»"),
    (re.compile(r"\bchứng\s+minh\s+(?:được\s+)?rằng\b", re.I), "«chứng minh rằng» — diễn giải quá mức"),
    (re.compile(r"\bkhẳng\s+định\s+chắc\s+chắn\b", re.I), "«khẳng định chắc chắn» — diễn giải quá mức"),
    (re.compile(r"\bxu\s+hướng\s+có\s+ý\s+nghĩa\b", re.I), "«xu hướng có ý nghĩa» — p không đạt thì không «gần đạt»"),
    (re.compile(r"\bgần\s+(?:có|đạt)\s+ý\s+nghĩa\b", re.I), "«gần có ý nghĩa» — p không đạt thì không «gần đạt»"),
    (re.compile(r"\brất\s+có\s+ý\s+nghĩa\s+thống\s+kê\b", re.I),
     "«rất có ý nghĩa thống kê» — p không đo độ lớn hiệu ứng"),
    (re.compile(r"\bp\s*=\s*0[.,]0+\b(?![.,]?\d*[1-9])", re.I), "«p = 0,000» — ghi «p < 0,001»"),
)
_CUM_NHAN_QUA = (
    (re.compile(r"\bgây\s+ra\b", re.I), "«gây ra»"),
    (re.compile(r"\blà\s+nguyên\s+nhân\b", re.I), "«là nguyên nhân»"),
)

# ── Hạn chế & khả năng khái quát theo chuẩn báo cáo của từng thiết kế (22/11/2026) ────────────────────────────────────
# VÌ SAO: kiểm toàn hệ 11 khâu (bác sĩ 22/11/2026) đo 24 kịch bản giả lập: 11 bản diễn giải không bàn khả năng khái
# quát, 11 bản phần hạn chế không nêu nguồn sai lệch, chỉ 2 bản (tổng quan gộp) nói hướng sai lệch — luật cũ chỉ đòi chữ
# «hạn chế» nên tất cả lọt. Số mục lấy đúng danh mục chuẩn đã đối chiếu bản gốc ở `run_g7_auto.CHECKLIST_ITEMS`:
# CONSORT 2025 mục 30 · STROBE mục 19 (sai lệch/độ chính xác, CẢ hướng lẫn độ lớn) và 21 (khái quát) · STARD 2015 mục
# 26 · TRIPOD+AI mục 26 · PRISMA 2020 mục 23b/23c · SRQR mục 18 (chuyển giao) và 19 (hạn chế, độ tin cậy).
# Máy chỉ đo CÓ BÀN hay không (khớp cụm từ), KHÔNG chấm nội dung đúng — người chấm chéo vẫn đọc.
_SAI_LECH = re.compile(
    r"sai\s+lệch|thiên\s+lệch|gây\s+nhiễu|\bnhiễu\b|bất\s+định|(?:độ\s+|không\s+)chính\s+xác|sai\s+số|"
    r"khoảng\s+tin\s+cậy\s+rộng|KTC\s+(?:95\s*%\s+)?rộng|cỡ\s+mẫu\s+(?:nhỏ|hạn\s+chế|chưa\s+đủ)|"
    # nguồn sai lệch gọi theo cơ chế (một tác giả viết «không làm mù» là đã nêu nguồn sai lệch thực hiện/đo lường)
    r"làm\s+mù|che\s+giấu\s+phân\s+bổ|nhớ\s+lại|mất\s+(?:theo\s+dõi|dấu)|lạc\s+quan|quá\s+khớp|overfit", re.I)
_HUONG_SAI_LECH = re.compile(
    r"(?:đánh\s+giá|ước\s+(?:lượng|tính))\s+(?:thấp|cao|quá|non)|(?:thấp|cao)\s+hơn\s+(?:thực|giá\s+trị\s+thật)|"
    r"kéo\s+[^.]{0,60}?về\s+(?:phía\s+)?(?:giá\s+trị\s+)?(?:không|1\b|null)|về\s+phía\s+(?:không|giả\s+thuyết\s+không)|"
    r"phóng\s+đại|làm\s+(?:mạnh|yếu|tăng|giảm)\s+(?:thêm\s+)?(?:mối\s+liên\s+quan|ước\s+lượng|hiệu\s+(?:ứng|quả)|tỷ\s+lệ)|"
    r"hướng\s+(?:của\s+)?(?:sai\s+lệch|ảnh\s+hưởng)|độ\s+lớn\s+(?:của\s+)?(?:sai\s+lệch|ảnh\s+hưởng)|"
    r"phân\s+tích\s+sai\s+lệch\s+định\s+lượng|E-value|giá\s+trị\s+E\b", re.I)
_KHAI_QUAT = re.compile(
    r"khái\s+quát|ngoại\s+suy|giá\s+trị\s+(?:bên\s+)?ngoài|tính\s+áp\s+dụng|suy\s+rộng|external\s+validity|"
    r"generali[sz]|áp\s+dụng\s+(?:kết\s+quả\s+)?(?:cho|ở|tại|vào)\s|kiểm\s+định\s+ngoài", re.I)
_BANG_CHUNG_SR = re.compile(  # PRISMA 2020 mục 23b — hạn chế của bằng chứng được đưa vào
    r"nghiên\s+cứu\s+(?:gốc|thành\s+phần|được\s+đưa\s+vào)|bằng\s+chứng\s+(?:được\s+)?(?:đưa\s+vào|gốc)|"
    r"chất\s+lượng\s+(?:của\s+)?(?:các\s+)?(?:nghiên\s+cứu|bằng\s+chứng)|không\s+đồng\s+nhất|sai\s+lệch\s+công\s+bố|"
    r"\bGRADE\b|RoB\s*2|nguy\s+cơ\s+sai\s+lệch", re.I)
_QUY_TRINH_SR = re.compile(  # PRISMA 2020 mục 23c — hạn chế của chính quy trình tổng quan
    r"quy\s+trình\s+tổng\s+quan|chiến\s+lược\s+tìm|tìm\s+kiếm|cơ\s+sở\s+dữ\s+liệu|giới\s+hạn\s+ngôn\s+ngữ|"
    r"tài\s+liệu\s+xám|sàng\s+lọc|trích\s+xuất", re.I)
_TIN_CAY_DT = re.compile(  # SRQR mục 19 (định tính) — hạn chế về độ tin cậy của phát hiện
    r"độ\s+tin\s+cậy|đáng\s+tin|phản\s+tư|tam\s+giác|kiểm\s+tra\s+lại\s+với\s+người\s+tham\s+gia|bão\s+h[oò]a|"
    r"vai\s+trò\s+(?:của\s+)?(?:nhà\s+nghiên\s+cứu|người\s+phỏng\s+vấn)|trustworth|credib", re.I)
_CHUYEN_GIAO_DT = re.compile(r"chuyển\s+giao|khái\s+quát|transferab", re.I)  # SRQR mục 18
_THIET_KE_QUAN_SAT = ("cohort", "case_control", "cross_sectional")
# thiết kế → [(mục cần đọc: 4 | 45, cụm phải có, chuẩn + mục, nội dung thiếu)]
LUAT_HAN_CHE = {
    "rct": [(4, _SAI_LECH, "CONSORT 2025 mục 30", "nguồn sai lệch hoặc độ không chính xác"),
            (45, _KHAI_QUAT, "CONSORT 2025 mục 30", "khả năng khái quát hoá")],
    **{tk: [(4, _SAI_LECH, "STROBE mục 19", "nguồn sai lệch hoặc độ không chính xác"),
            (4, _HUONG_SAI_LECH, "STROBE mục 19", "hướng hoặc độ lớn của sai lệch tiềm ẩn"),
            (45, _KHAI_QUAT, "STROBE mục 21", "khả năng khái quát hoá (giá trị bên ngoài)")]
       for tk in _THIET_KE_QUAN_SAT},
    "diagnostic": [(4, _SAI_LECH, "STARD 2015 mục 26", "nguồn sai lệch hoặc bất định thống kê"),
                   (45, _KHAI_QUAT, "STARD 2015 mục 26", "khả năng khái quát hoá")],
    "prediction": [(4, _SAI_LECH, "TRIPOD+AI mục 26", "ảnh hưởng của sai lệch hoặc bất định"),
                   (45, _KHAI_QUAT, "TRIPOD+AI mục 26", "khả năng khái quát hoá")],
    "sr_ma": [(4, _BANG_CHUNG_SR, "PRISMA 2020 mục 23b", "hạn chế của bằng chứng được đưa vào"),
              (4, _QUY_TRINH_SR, "PRISMA 2020 mục 23c", "hạn chế của chính quy trình tổng quan")],
    "qualitative": [(4, _TIN_CAY_DT, "SRQR mục 19", "hạn chế về độ tin cậy của phát hiện"),
                    (45, _CHUYEN_GIAO_DT, "SRQR mục 18", "khả năng chuyển giao của phát hiện")],
}


def kiem_han_che_khai_quat(muc4: str, muc5: str, ma_thiet_ke: Optional[str]) -> List[str]:
    """Mục 4 (hạn chế) và mục 4–5 (khái quát) có bàn đủ nội dung chuẩn báo cáo của thiết kế đòi không.
    Không suy được thiết kế ⇒ báo lỗi (không đo được ≠ đạt) — chạy lại với --thiet-ke."""
    if ma_thiet_ke not in LUAT_HAN_CHE:
        return [f"không xác định được thiết kế (gặp «{ma_thiet_ke}») — chưa đối chiếu được mục hạn chế/khái quát "
                "theo chuẩn báo cáo; chạy lại với --thiet-ke"]
    ra = []
    for noi, mau, chuan, noi_dung in LUAT_HAN_CHE[ma_thiet_ke]:
        van = muc4 if noi == 4 else f"{muc4}\n{muc5}"
        if not mau.search(van):
            ra.append(f"{'mục 4' if noi == 4 else 'mục 4–5'} chưa bàn {noi_dung} ({chuan})")
    return ra
_SO = re.compile(r"[-−]?\d+(?:[.,]\d+)?")
_KTC = re.compile(r"([-−]?\d+(?:[.,]\d+)?)\s*(?:–|—|-|;|,\s|đến|to)\s*([-−]?\d+(?:[.,]\d+)?)")
_CHU_THICH_BANG = re.compile(r"^\**\s*Bảng\s+\d+[.:]")
_DINH_DANH = re.compile(r"\bPMID[:\s]*\d{6,9}\b|\b10\.\d{4,9}/\S+", re.I)


class LoiDauVao(ValueError):
    """Đầu vào không dùng được — CLI trả mã 2."""


def duong_dan(study: str, out_dir: Path) -> Path:
    return Path(out_dir) / TEN_TEP.format(study=study)


def sinh_mau(study: str, out_dir: Path) -> Path:
    """Dựng khung bản diễn giải (không ghi đè bản đã có)."""
    p = duong_dan(study, out_dir)
    if p.exists():
        raise LoiDauVao(f"đã có {p.name} — không ghi đè bản diễn giải đã viết")
    bang = ("| " + " | ".join(COT_BANG_CHINH) + " |\n|" + "---|" * len(COT_BANG_CHINH) + "\n"
            "| [CẦN tên kết cục chính] | [CẦN RR/OR/HR/MD…] | [CẦN] | [CẦN cận dưới–cận trên] | [CẦN] | "
            "[CẦN so ngưỡng MCID/ý nghĩa lâm sàng có nguồn] | [CẦN 06_ket_qua/<tệp>] |\n")
    van = (f"# Diễn giải kết quả — {study}\n\n"
           f"{MUC[0]}\n\n**Bảng 1.** Kết quả kết cục chính (ước lượng, KTC 95%, p — đúng như tệp kết quả)\n\n{bang}\n"
           f"{MUC[1]}\n\n[CẦN: kết quả có ý nghĩa thống kê không, và độ lớn hiệu ứng so với ngưỡng ý nghĩa lâm sàng "
           f"(MCID/ngưỡng có nguồn) — hai trục tách riêng]\n\n"
           f"{MUC[2]}\n\n[CẦN: so với nghiên cứu trước — mỗi so sánh kèm PMID/DOI đã kiểm chứng]\n\n"
           f"{MUC[3]}\n\n[CẦN: điểm mạnh; hạn chế — nguồn sai lệch (chọn, đo lường, nhiễu) và độ không chính xác; "
           f"nghiên cứu quan sát nêu cả HƯỚNG và ĐỘ LỚN của sai lệch tiềm ẩn (STROBE 19); tổng quan: hạn chế của "
           f"bằng chứng và của quy trình tổng quan (PRISMA 23b/23c); định tính: độ tin cậy của phát hiện (SRQR 19); "
           f"khả năng khái quát/chuyển giao (STROBE 21, CONSORT 2025 mục 30, SRQR 18)]\n\n"
           f"{MUC[4]}\n\n[CẦN: hàm ý cho thực hành — không vượt quá thiết kế; hướng nghiên cứu tiếp]\n\n"
           "> Cần bác sĩ kiểm chứng.\n")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    p.write_text(van, encoding="utf-8", newline="\n")
    return p


# ── tách bảng ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _o(dong: str) -> List[str]:
    return [x.strip() for x in re.split(r"(?<!\\)\|", dong.strip().strip("|"))]


def cac_bang(van: str) -> List[Tuple[int, str, List[List[str]]]]:
    """[(dòng bắt đầu 1-based, chú thích ngay trên hoặc "", [hàng…])] — hàng đầu là tiêu đề, hàng gạch đã bỏ."""
    dong = van.splitlines()
    ra, i = [], 0
    while i < len(dong):
        if dong[i].lstrip().startswith("|"):
            bat_dau = i
            khoi = []
            while i < len(dong) and dong[i].lstrip().startswith("|"):
                khoi.append(dong[i])
                i += 1
            truoc = [d.strip() for d in dong[max(0, bat_dau - 3):bat_dau] if d.strip()]
            chu_thich = truoc[-1] if truoc and _CHU_THICH_BANG.match(truoc[-1]) else ""
            co_gach = len(khoi) > 1 and re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", khoi[1].strip())
            hang = [_o(khoi[0])] + [_o(d) for d in khoi[(2 if co_gach else 1):]]
            ra.append((bat_dau + 1, chu_thich if co_gach else "\0" + chu_thich, hang))
        else:
            i += 1
    return ra


def _muc(van: str, ten: str) -> str:
    i = van.find(ten)
    if i < 0:
        return ""
    j = van.find("\n## ", i + len(ten))
    return van[i: j if j > 0 else len(van)]


def _so(chuoi: str) -> Optional[float]:
    m = _SO.search(chuoi or "")
    return float(m.group(0).replace("−", "-").replace(",", ".")) if m else None


def _so_le(chuoi: str) -> int:
    m = _SO.search(chuoi or "")
    if not m or not re.search(r"[.,]", m.group(0)):
        return 0
    return len(re.split(r"[.,]", m.group(0))[1])


def _van_ban_nguon(p: Path) -> Optional[str]:
    if p.suffix.lower() in DUOI_VAN_BAN:
        return p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".xlsx":
        try:
            import openpyxl  # noqa: PLC0415

            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            return "\n".join(str(c) for ws in wb.worksheets for row in ws.iter_rows(values_only=True)
                             for c in row if c is not None)
        except Exception:  # noqa: BLE001 — không đọc được ⇒ None (báo «không đối chiếu được»)
            return None
    return None


def _co_trong_nguon(gia_tri: float, so_le: int, van_nguon: str) -> bool:
    nguong = 0.5 * 10 ** (-so_le) + 1e-9
    for m in _SO.finditer(van_nguon):
        try:
            x = float(m.group(0).replace("−", "-").replace(",", "."))
        except ValueError:
            continue
        if abs(x - gia_tri) <= nguong:
            return True
    return False


def _kiem_bang_chinh(out_dir: Path, bang: List[List[str]], ra: List[str]) -> None:
    tieu_de = bang[0]
    thieu = [c for c in COT_BANG_CHINH if c not in tieu_de]
    if thieu:
        ra.append(f"Bảng kết quả chính thiếu cột: {', '.join(thieu)}")
        return
    vi = {c: tieu_de.index(c) for c in COT_BANG_CHINH}
    if len(bang) < 2:
        ra.append("Bảng kết quả chính chưa có dòng kết quả nào")
    dau_tp = set()
    for k, h in enumerate(bang[1:], 1):
        if len(h) != len(tieu_de):
            continue  # đã báo ở kiểm bảng chung
        uoc, ktc, p_val, nguon = h[vi["Ước lượng điểm"]], h[vi["KTC 95%"]], h[vi["p"]], h[vi["Nguồn kết quả"]]
        nhan = f"Bảng kết quả chính, dòng {k} («{h[vi['Kết cục']][:30]}»)"
        diem = _so(uoc)
        if diem is None:
            ra.append(f"{nhan}: ước lượng điểm không đọc được số")
            continue
        m = _KTC.search(ktc.replace("−", "-"))
        if not m:
            ra.append(f"{nhan}: KTC 95% phải ghi hai cận (vd «0,72–0,98»)")
            continue
        duoi, tren = (float(x.replace(",", ".")) for x in m.groups())
        if not duoi <= diem <= tren:
            ra.append(f"{nhan}: ước lượng {uoc} nằm ngoài KTC 95% {ktc}")
        for o in (uoc, m.group(1), m.group(2)):
            mm = re.search(r"\d([.,])\d", o)
            if mm:
                dau_tp.add(mm.group(1))
        if p_val not in ("—", "N/A"):
            if re.fullmatch(r"<\s*0[.,]001", p_val.replace("\u00a0", " ")):
                pass
            else:
                pv = _so(p_val)
                if pv is None or not 0 <= pv <= 1:
                    ra.append(f"{nhan}: p «{p_val}» không hợp lệ (0–1, hoặc «< 0,001», hoặc «—»)")
                elif pv < 0.001:
                    ra.append(f"{nhan}: p «{p_val}» < 0,001 — ghi «< 0,001»")
        duong = nguon.strip().strip("`").strip()
        dp = Path(duong)
        o_goc = len(dp.parts) == 1 and bool(TEP_KET_QUA_GOC.fullmatch(duong))
        if (not duong or dp.is_absolute() or ".." in dp.parts
                or not (o_goc or any(duong.startswith(t + "/") for t in THU_MUC_KET_QUA))):
            ra.append(f"{nhan}: «Nguồn kết quả» phải là tệp trong {' hoặc '.join(THU_MUC_KET_QUA)}/ của đề tài, "
                      "hoặc tệp kết quả engine ghi ở gốc đề tài (G6…_table…/_analysis_summary.json)")
            continue
        tep = Path(out_dir) / dp
        if not tep.is_file():
            ra.append(f"{nhan}: tệp nguồn {duong} không tồn tại")
            continue
        van_nguon = _van_ban_nguon(tep)
        if van_nguon is None:
            ra.append(f"{nhan}: không đối chiếu được số với {duong} (chỉ đọc txt/csv/tsv/json/md/log/xlsx)")
            continue
        for ten, o in (("ước lượng", uoc), ("cận dưới", m.group(1)), ("cận trên", m.group(2))):
            gia = _so(o)
            if gia is not None and not _co_trong_nguon(gia, _so_le(o), van_nguon):
                ra.append(f"{nhan}: {ten} {o} không có trong {duong} — số phải chép đúng tệp kết quả")
    if len(dau_tp) > 1:
        ra.append("Bảng kết quả chính trộn dấu thập phân «,» và «.» — dùng một kiểu thống nhất")


def kiem(study: str, out_dir: Path, ma_thiet_ke: Optional[str] = None) -> List[str]:
    """Danh sách lỗi (rỗng = đạt) của bản diễn giải; thiếu tệp ⇒ LoiDauVao."""
    p = duong_dan(study, out_dir)
    if not p.is_file():
        raise LoiDauVao(f"không thấy {p.name} — dựng khung bằng lệnh «mau»")
    van = p.read_text(encoding="utf-8")
    ra: List[str] = []
    # Cấu trúc
    vi_tri = [van.find(m) for m in MUC]
    for m, k in zip(MUC, vi_tri):
        if k < 0:
            ra.append(f"thiếu mục «{m[3:]}»")
    co = [k for k in vi_tri if k >= 0]
    if co != sorted(co):
        ra.append("năm mục không đúng thứ tự 1→5")
    if "[CẦN" in van:
        ra.append(f"còn {van.count('[CẦN')} ô «[CẦN …]» chưa điền")
    if "cần bác sĩ kiểm chứng" not in van.casefold():
        ra.append("thiếu dòng «Cần bác sĩ kiểm chứng»")
    # Bảng biểu
    bang = cac_bang(van)
    for dong, chu_thich, hang in bang:
        if chu_thich.startswith("\0"):
            ra.append(f"bảng ở dòng {dong}: thiếu hàng gạch «|---|» dưới tiêu đề")
            chu_thich = chu_thich[1:]
        if not chu_thich:
            ra.append(f"bảng ở dòng {dong}: thiếu chú thích «Bảng N.» ngay trên bảng")
        so_cot = len(hang[0])
        for k, h in enumerate(hang[1:], 1):
            if len(h) != so_cot:
                ra.append(f"bảng ở dòng {dong}, hàng {k}: {len(h)} ô ≠ {so_cot} cột tiêu đề")
            elif any(not o for o in h):
                ra.append(f"bảng ở dòng {dong}, hàng {k}: có ô trống (không áp dụng thì ghi «—»)")
    muc1 = _muc(van, MUC[0])
    dau_muc1 = van.find(muc1) if muc1 else -1
    bang_chinh = [h for d, _c, h in bang if muc1 and dau_muc1 <= _vi_tri_dong(van, d) < dau_muc1 + len(muc1)]
    if not bang_chinh:
        ra.append("mục 1 không có Bảng kết quả chính")
    else:
        _kiem_bang_chinh(out_dir, bang_chinh[0], ra)
    # Văn phong (ngoài bảng)
    ngoai_bang = "\n".join(d for d in van.splitlines() if not d.lstrip().startswith("|"))
    for bt, ly_do in _CUM_QUA_MUC:
        if bt.search(ngoai_bang):
            ra.append(f"văn phong: {ly_do}")
    if ma_thiet_ke in THIET_KE_KHONG_CAN_THIEP:
        for bt, cum in _CUM_NHAN_QUA:
            if bt.search(ngoai_bang):
                ra.append(f"văn phong: {cum} — thiết kế {ma_thiet_ke} chỉ cho thấy LIÊN QUAN, không nhân quả")
    muc2 = _muc(van, MUC[1])
    if muc2 and "lâm sàng" not in muc2[len(MUC[1]):].casefold():
        ra.append("mục 2 chưa nói ý nghĩa LÂM SÀNG (tách khỏi ý nghĩa thống kê)")
    muc3 = _muc(van, MUC[2])
    if muc3 and not _DINH_DANH.search(muc3):
        ra.append("mục 3 chưa có PMID/DOI nào cho phần đối chiếu y văn")
    muc4 = _muc(van, MUC[3])
    if muc4 and "hạn chế" not in muc4[len(MUC[3]):].casefold():
        ra.append("mục 4 chưa nêu hạn chế")
    muc5 = _muc(van, MUC[4])
    if muc4:
        ra.extend(kiem_han_che_khai_quat(muc4[len(MUC[3]):], muc5[len(MUC[4]):] if muc5 else "", ma_thiet_ke))
    return ra


def _vi_tri_dong(van: str, so_dong: int) -> int:
    """Vị trí ký tự đầu dòng thứ `so_dong` (1-based)."""
    k = 0
    for _ in range(so_dong - 1):
        k = van.find("\n", k) + 1
    return k


def _thu_muc(study: str) -> Path:
    return BASE / "exports" / study


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hợp đồng bản diễn giải kết quả G6-T3 (dựng khung + kiểm).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("mau", help="dựng khung G6_DIEN_GIAI_<mã>.md (không ghi đè)")
    a.add_argument("--study", required=True)
    a = sub.add_parser("kiem", help="kiểm số liệu · văn phong · bảng biểu")
    a.add_argument("--study", required=True)
    a.add_argument("--thiet-ke", default=None, help="mã thiết kế (mặc định suy từ hồ sơ đề tài)")
    a.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    out_dir = _thu_muc(args.study)
    if not out_dir.is_dir():
        print(f"❌ Không thấy thư mục đề tài exports/{args.study}", file=sys.stderr)
        return 2
    try:
        if args.lenh == "mau":
            p = sinh_mau(args.study, out_dir)
            print(f"✅ Đã dựng khung {p.name} — điền rồi chạy «kiem». Cần bác sĩ kiểm chứng.")
            return 0
        tk = args.thiet_ke
        if tk is None:
            try:
                sys.path.insert(0, str(BASE / "tools"))
                import skill_standards as SK  # noqa: PLC0415

                tk = SK.dac_ta_thiet_ke(out_dir).get("design_code")
            except Exception:  # noqa: BLE001 — không suy được ⇒ bỏ kiểm ngôn ngữ nhân quả
                tk = None
        loi = kiem(args.study, out_dir, tk)
    except LoiDauVao as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"study": args.study, "thiet_ke": tk, "dat": not loi, "loi": loi}, ensure_ascii=False,
                         indent=2))
    else:
        print(("✅ Bản diễn giải đạt kiểm máy (số liệu · văn phong · bảng biểu)" if not loi
               else f"🔴 {len(loi)} lỗi:") + ("" if not loi else "\n" + "\n".join(f"  - {x}" for x in loi)))
        print("Kiểm máy không thay người đọc — ý nghĩa lâm sàng và trích dẫn do người chấm chéo. "
              "Cần bác sĩ kiểm chứng.")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
