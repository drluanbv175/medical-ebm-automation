#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hop_dong_sap.py — HỢP ĐỒNG SAP MÁY ĐỌC (`G4_SAP_CONTRACT_<mã>.json`) và BỘ ĐỌC SAP DUY NHẤT.

Vì sao (bác sĩ duyệt 23/11/2026): phần lớn lỗi thật hai ngày qua là G6 và G7 hiểu SAP KHÁC NHAU — họ mô hình (logistic
có điều kiện), phương pháp KTC hiệu số nguy cơ (Newcombe), phân tích chính khi gán đa trị, danh sách phân tích độ nhạy,
α và số phía — vì mỗi công cụ tự dò chữ trong SAP bằng biểu thức riêng. Nay SAP được ĐỌC MỘT LẦN, ở đây, thành một hợp
đồng có cấu trúc; G6 (`chay_sap_g6 kiem`, G6-AUTO-09) và G7 (`run_g7_auto`, G7-AUTO-05/06/08) đọc HỢP ĐỒNG, không đọc
chữ SAP. Các hàm dò chữ trước đây nằm rải ở g6_quality_gate / g4_quality_gate / chay_sap_g6 / run_g7_auto /
quyet_dinh_da_chot nay sống ở đây; tên cũ ở các mô-đun đó chỉ là bí danh trỏ về đây (một bộ đọc, không hai bản).

Hợp đồng (schema `SCHEMA`):
  thiet_ke · kieu_ghep · phan_tich_chinh (kết cục, họ mô hình, liên kết, biến độc lập, cụm, bộ ghép, đơn vị phơi nhiễm,
  quần thể) · khoang_tin_cay (mức, phương pháp KTC hiệu số nguy cơ, phương pháp KTC tỷ lệ) · gia_thuyet (α, số phía,
  khung, biên) · du_lieu_thieu (phương pháp, m, phân tích chính) · bien_co_hiem · do_nhay[] · nhom_con[] · phan_mem ·
  phan_tich_bat_buoc[] · phan_tich_phu_trong_cau[] · thay_doi_sau_khoa[] · muc{§: tiêu đề, dòng, nhãn}.
  v2 (24/11/2026) thêm so_lieu_ky · ket_cuc_sap · seed_sap · alpha_sap · khai_bao · dong_khai · nhac; v3 (24/11/2026)
  thêm pls_sem (khối PLS-SEM của §4: mô hình đo lường/cấu trúc, bootstrap, PLSpredict, xử lý thiếu, hạt giống — None
  khi SAP không khai). Hợp đồng v1/v2 vẫn hợp lệ: `kiem` chỉ so khoá của phiên bản đó.

Khoá và băm:
  • `sha256_sap_noi_dung` = SHA-256 văn bản SAP (bỏ đúng dòng băm hợp đồng) — SAP đổi sau khi lập ⇒ hợp đồng cũ;
  • `sha256_hop_dong` = SHA-256 JSON chuẩn của phần lõi (schema, mã, tệp SAP, sha256_sap_noi_dung, noi_dung);
  • G4 ghi dòng «→ Hợp đồng SAP máy đọc: … sha256 <băm>» vào CHỨNG CHỈ KHOÁ (PHẦN 5) — chữ ký G4 trên SAP vì thế khoá
    luôn hợp đồng (nguồn `sinh_khi_dung`);
  • SAP ĐÃ KÝ trước khi có hợp đồng (BTM, C1a): hợp đồng suy từ chính văn bản đã ký, nguồn `suy_tu_ban_ky`, KHÔNG sửa
    SAP, không bắt ký lại.

Kiểm (`kiem`): đúng schema · băm hợp đồng khớp · SAP chưa đổi · hợp đồng = bộ đọc chạy lại trên SAP hiện tại · băm
trong chứng chỉ khớp (nguồn `sinh_khi_dung`) hoặc SAP không có dòng băm (nguồn `suy_tu_ban_ky`). Bất kỳ lệch nào ⇒ lỗi;
nơi tiêu thụ CHẶN.

Dùng:
  python3 tools/hop_dong_sap.py ghi  --study <mã> [--suy-tu-ban-ky]   # lập/làm mới hợp đồng (+ băm vào chứng chỉ)
  python3 tools/hop_dong_sap.py kiem --study <mã> [--json]            # mã 0 hợp lệ · 1 lệch/thiếu · 3 tham số sai
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import placeholder_contract as PC  # noqa: E402

SCHEMA = "ebm.g4_sap_contract/3"
#: phiên bản 1 (23/11/2026) — vẫn đọc được: kiểm đúng các khoá v1, các trường v2 suy từ CHÍNH văn bản SAP đã khớp băm
SCHEMA_V1 = "ebm.g4_sap_contract/1"
KHOA_V1 = ("thiet_ke", "kieu_ghep", "phan_tich_chinh", "khoang_tin_cay", "gia_thuyet", "du_lieu_thieu", "bien_co_hiem",
           "do_nhay", "nhom_con", "phan_mem", "phan_tich_bat_buoc", "phan_tich_phu_trong_cau", "thay_doi_sau_khoa",
           "muc")
#: phiên bản 2 (24/11/2026) — vẫn đọc được (hợp đồng BTM/C1a suy từ bản ký): kiểm đúng các khoá v2; trường v3
#: (`pls_sem`, 24/11/2026) suy từ CHÍNH văn bản SAP đã khớp băm
SCHEMA_V2 = "ebm.g4_sap_contract/2"
KHOA_V2 = KHOA_V1 + ("so_lieu_ky", "ket_cuc_sap", "seed_sap", "alpha_sap", "khai_bao", "dong_khai", "nhac")
SCHEMA_HO_TRO = (SCHEMA, SCHEMA_V2, SCHEMA_V1)
#: khoá nội dung mà mỗi phiên bản cũ khoá trong băm — `kiem` chỉ đối chiếu đúng các khoá đó
KHOA_THEO_SCHEMA = {SCHEMA_V1: KHOA_V1, SCHEMA_V2: KHOA_V2}
NGUON_SINH = "sinh_khi_dung"
NGUON_SUY = "suy_tu_ban_ky"
NGUON_HOP_LE = (NGUON_SINH, NGUON_SUY)


def ten_tep(study: str) -> str:
    return f"G4_SAP_CONTRACT_{study}.json"


def ten_sap(study: str) -> str:
    return f"G4_A5_SAP_FINAL_{study}.md"


# ─────────────────────────── dòng băm trong chứng chỉ khoá (PHẦN 5) ───────────────────────────
NHAN_DONG_BAM = "Hợp đồng SAP máy đọc"
DONG_BAM_RE = re.compile(rf"^[ \t]*→ {NHAN_DONG_BAM}:[^\n]*?\bsha256 ([0-9a-f]{{64}})[^\n]*(?:\n|\Z)", re.M)


def dong_bam(study: str, bam: str) -> str:
    return f"  → {NHAN_DONG_BAM}: {ten_tep(study)} · sha256 {bam}"


def bo_dong_bam(sap: str) -> str:
    """Văn bản SAP bỏ dòng băm hợp đồng — phần nội dung mà hợp đồng mô tả (dòng băm không tự mô tả chính nó)."""
    return DONG_BAM_RE.sub("", sap or "")


def bam_trong_sap(sap: str) -> List[str]:
    """Các giá trị băm hợp đồng ghi trong SAP (thường 0 hoặc 1)."""
    return DONG_BAM_RE.findall(sap or "")


def bam_sap(sap: str) -> str:
    return hashlib.sha256(bo_dong_bam(sap).encode("utf-8")).hexdigest()


_PHAN_RE = re.compile(r"^##[ \t]*PHẦN[ \t]*(\d+)\b[^\n]*\n(.*?)(?=^##[ \t]|\Z)", re.M | re.S)


def chen_dong_bam(sap: str, study: str, bam: str) -> Optional[str]:
    """SAP với dòng băm hợp đồng ngay dưới khung chứng chỉ khoá (PHẦN 5); đã có dòng ⇒ thay tại chỗ.

    None ⇒ SAP không có PHẦN 5 mang khung chứng chỉ (sai khuôn) — không tự dựng chứng chỉ."""
    moi = dong_bam(study, bam)
    if DONG_BAM_RE.search(sap):
        return DONG_BAM_RE.sub(moi + "\n", sap, count=1)
    m = next((x for x in _PHAN_RE.finditer(sap) if x.group(1) == "5"), None)
    if not m:
        return None
    than = m.group(2)
    k = re.search(r"^[ \t]*╚[^\n]*\n", than, re.M)
    if not k:
        return None
    vi_tri = m.start(2) + k.end()
    return sap[:vi_tri] + moi + "\n" + sap[vi_tri:]


# ─────────────────────────── tiện ích chữ ───────────────────────────
#: chú thích soạn thảo run_g4_auto gắn sau dòng SAP điền sẵn — không phải nội dung (quyet_dinh_da_chot trỏ về đây)
GHI_CHU_DIEN_SAN_RE = re.compile(r"\s*\*\(điền sẵn từ quyết định đã chốt[^)]*\)\*")
_NGOAC_MOT_DONG = re.compile(r"\[[^\[\]\n]*\]|<[^<>\n]*>")


def bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def bo_dau_d(s: str) -> str:
    """bo_dau + «đ» → «d» (NFD không tách «đ») — để từ khoá «có điều kiện» khớp."""
    return bo_dau(s).replace("đ", "d")


def co_noi_dung(v: Any) -> bool:
    t = str(v or "").strip()
    return bool(t) and not PC.co_o_trong(t)


def bo_nhan_chua_dien(van_ban: str) -> str:
    """Bóc NGUYÊN nhãn chưa điền (gồm cả câu ví dụ nằm BÊN TRONG nhãn) trước khi đọc giá trị.

    Sự cố 03/10/2026: «[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]» bị đọc thành seed 2026 đã chốt. Ngoặc đóng trên
    cùng dòng mà mang dấu hiệu ô trống ⇒ thay bằng khoảng trắng; nhãn MỞ không đóng trên dòng ⇒ cắt từ chỗ mở tới hết
    dòng.
    Ô trống trần không ngoặc («___», «CHƯA XÁC NHẬN») KHÔNG cắt."""
    def _thay(m: re.Match) -> str:
        return " " if PC.co_o_trong(m.group(0), PC.TAT_CA_HO) else m.group(0)

    ra = []
    for dong in (van_ban or "").splitlines():
        dong = _NGOAC_MOT_DONG.sub(_thay, dong)
        mo = [m.start() for ho in PC.TAT_CA_HO for bt in PC.mau(ho) for m in bt.finditer(dong)
              if m.group(0)[:1] in "[<"]
        ra.append(dong[:min(mo)] if mo else dong)
    return "\n".join(ra)


# ─────────────────────────── cắt mục SAP ───────────────────────────
_MUC_RE = re.compile(r"^#{2,4}\s*§\s*(\d{1,2})\b([^\n]*)\n(.*?)(?=^#{2,4}\s*§\s*\d|^#{1,2}\s|\Z)", re.M | re.S)


def muc_than(sap: str, so: int) -> str:
    """Thân §so của SAP (tới § kế tiếp / tiêu đề «#»/«##»)."""
    m = re.search(rf"^#{{2,4}}\s*§\s*{so}\b[^\n]*\n(.*?)(?=^#{{2,4}}\s*§\s*\d|^#{{1,2}}\s|\Z)", sap or "", re.M | re.S)
    return m.group(1) if m else ""


def cac_muc(sap: str) -> Dict[str, Tuple[str, str, str]]:
    """{số §: (tiêu đề, thân, nguyên văn gồm dòng tiêu đề)} — § trùng số thì lấy lần đầu."""
    ra: Dict[str, Tuple[str, str, str]] = {}
    for m in _MUC_RE.finditer(sap or ""):
        ra.setdefault(m.group(1), (m.group(2).strip(), m.group(3), m.group(0)))
    return ra


# ─────────────────────────── họ mô hình (SAP §4) ───────────────────────────
#: từ khoá SAP §4 (đã bỏ dấu, chữ thường) theo họ mô hình
HO_SAP = (
    # PLS-SEM (23/11/2026) là họ RIÊNG và ĐỘC QUYỀN (ho_mo_hinh): khối PLS-SEM nhắc «CB-SEM», «mô hình tuyến tính
    # chuẩn» (PLSpredict)… không được kéo theo họ tuyến tính/logistic
    ("pls_sem", ("pls-sem", "pls path", "partial least squares", "binh phuong toi thieu tung phan")),
    ("ordinal", ("proportional odds", "thu bac", "logistic thu tu", "polr", "clmm", "ordinal")),
    ("cox", ("cox", "hazard", "log-rank", "log rank", "thoi gian den bien co", "time-to-event", "kaplan")),
    ("poisson", ("poisson", "log-binomial", "log binomial", "nguy co tuong doi", "relative risk")),
    # logistic CÓ ĐIỀU KIỆN theo bộ ghép là họ RIÊNG (23/11/2026)
    ("logistic_dk", ("logistic co dieu kien", "conditional logistic", "clogit", "conditionallogit")),
    ("logistic", ("logistic", "binomial", "odds ratio", "ty so chenh")),
    ("risk_diff", ("hieu nguy co", "risk difference", "hieu ty le", "newcombe")),
    ("linear", ("tuyen tinh", "linear", "ancova", "t-test", "t test", "chenh lech trung binh", "mean difference",
                "mann-whitney")),
    ("meta", ("meta-analysis", "meta analysis", "phan tich gop", "random effects", "random-effects", "reml")),
    ("roc", ("roc", "auc", "do nhay", "do dac hieu")),
    ("qualitative", ("chu de", "thematic", "dinh tinh")),
    # cắt ngang MÔ TẢ — ước lượng tỷ lệ + KTC (khoá chặt: cụm từ riêng, không «tỷ lệ» trần)
    ("proportion", ("uoc luong ty le", "wilson", "ty le hien mac", "prevalence")),
)


def ho_mo_hinh(sap4: str) -> set:
    """Họ mô hình SAP §4 khai (tập mã của HO_SAP)."""
    bd = bo_dau(sap4)
    # họ logistic_dk dò trên bản «đ» → «d»; các họ khác GIỮ cách dò cũ — chuẩn hoá «đ» cho mọi họ sẽ kích hoạt từ khoá
    # trùng nghĩa («độ nhạy» của phân tích độ nhạy ⇒ ROC, «biến định tính» ⇒ định tính)
    bd_d = bd.replace("đ", "d")
    ho = {ten for ten, tu in HO_SAP if any(t in (bd_d if ten == "logistic_dk" else bd) for t in tu)}
    # PLS-SEM là phân tích chính DUY NHẤT của SAP khai nó — mọi họ khác mà từ khoá trong khối đó kích hoạt không phải
    # phương pháp thay thế
    if "pls_sem" in ho:
        return {"pls_sem"}
    # «logistic thứ tự»/«proportional odds» là họ THỨ BẬC — không để chữ «logistic» trong đó cho qua logistic nhị phân
    if "ordinal" in ho and not re.search(r"logistic\s+(?:nhi\s+phan|binary)|binomial", bd):
        ho.discard("logistic")
    # «logistic có điều kiện» KHÔNG cho qua logistic không điều kiện — trừ khi SAP khai tường minh bản không điều kiện
    if "logistic_dk" in ho and not re.search(r"logistic\s+khong\s+dieu\s+kien|unconditional\s+logistic", bd_d):
        ho.discard("logistic")
    return ho


# ─────────────────────────── khối PLS-SEM (SAP §4) — 23/11/2026 ───────────────────────────
#: nhãn mở khối máy đọc do run_g4_auto in (pls_sem.dong_sap); vắng ⇒ SAP không khai PLS-SEM
PLS_NHAN_KHOI = "**Mô hình đo lường (PLS-SEM):**"
#: cụm ngưỡng định trước phải còn nguyên trong SAP mới được PHÂN LOẠI (Hair 2019 — thiếu ⇒ chỉ in số)
PLS_CUM_NGUONG = ("≥ 0,708", "0,70–0,95", "AVE ≥ 0,50", "HTMT < 0,90", "VIF < 3", "Q²predict > 0")
PLS_TEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
# Bộ chuẩn hoá văn phong của SAP (vn_prose_style) đổi « — » thành «. »/«, » ⇒ chỉ dựa vào MÃ trong backtick, cụm loại đo
# lường cố định và danh sách chỉ báo trong backtick — không dựa vào dấu ngăn cách
_PLS_DONG_CT = re.compile(r"^\s*-\s*`([A-Za-z][A-Za-z0-9_]*)`[\s.,;:—–-]*(.*?)[\s.,;:—–-]*"
                          r"(kết quả \(reflective, Mode A\)|cấu tạo \(formative, Mode B\)):\s*(.+?)\s*$")
_PLS_BIEN = re.compile(r"`([A-Za-z][A-Za-z0-9_]*)`")


def kiem_mo_hinh_pls(mh: Dict[str, Any]) -> List[str]:
    """Lỗi cấu trúc mô hình PLS-SEM (rỗng = hợp lệ): tên, chỉ báo, đường dẫn, chu trình, PLSpredict, bootstrap."""
    loi: List[str] = []
    ct, dd = mh.get("cau_truc") or [], mh.get("duong_dan") or []
    ten = [c.get("ma") for c in ct]
    if len(ct) < 2:
        loi.append("cần ít nhất hai cấu trúc")
    if len(set(ten)) != len(ten):
        loi.append("mã cấu trúc trùng")
    muc_tat_ca = [m for c in ct for m in c.get("muc") or []]
    trung = sorted({m for m in muc_tat_ca if muc_tat_ca.count(m) > 1})
    if trung:
        loi.append(f"chỉ báo thuộc nhiều cấu trúc: {', '.join(trung)}")
    for c in ct:
        if not PLS_TEN_RE.match(str(c.get("ma") or "")):
            loi.append(f"mã cấu trúc không hợp lệ: {c.get('ma')!r}")
        if not c.get("muc"):
            loi.append(f"{c.get('ma')}: không có chỉ báo")
        if c.get("mode") == "B" and len(c.get("muc") or []) < 2:
            loi.append(f"{c.get('ma')}: cấu tạo (Mode B) cần ≥ 2 chỉ báo")
    if not dd:
        loi.append("không có đường dẫn nào ở mô hình cấu trúc")
    for a, b in dd:
        if a not in ten or b not in ten:
            loi.append(f"đường dẫn {a} → {b} dùng cấu trúc chưa khai ở mô hình đo lường")
        if a == b:
            loi.append(f"đường dẫn tự vòng {a} → {b}")
    if len({tuple(p) for p in dd}) != len(dd):
        loi.append("đường dẫn trùng")
    co_dd = {x for p in dd for x in p}
    loi += [f"{t}: không nằm trên đường dẫn nào" for t in ten if t not in co_dd]
    ke = {t: [b for a, b in dd if a == t] for t in ten}  # chu trình: PLS-PM chỉ nhận mô hình đệ quy
    trang: Dict[Any, int] = {}

    def co_vong(u: Any) -> bool:
        trang[u] = 1
        for v in ke.get(u, []):
            if trang.get(v) == 1 or (trang.get(v) is None and co_vong(v)):
                return True
        trang[u] = 2
        return False

    if any(trang.get(t) is None and co_vong(t) for t in ten):
        loi.append("mô hình cấu trúc có chu trình — PLS-PM chỉ ước lượng mô hình đệ quy")
    b = mh.get("bootstrap")
    if b is not None and (isinstance(b, bool) or not isinstance(b, int) or not 1 <= b <= 100000):
        loi.append(f"số mẫu bootstrap phải là số nguyên 1–100.000 (đang {b!r})")
    pp = mh.get("plspredict")
    if isinstance(pp, dict):
        noi = {b_ for _a, b_ in dd}
        if not pp.get("dich"):
            loi.append("PLSpredict thiếu cấu trúc đích")
        loi += [f"PLSpredict: cấu trúc đích {x} không phải cấu trúc nội sinh" for x in pp.get("dich") or []
                if x not in noi]
        if not isinstance(pp.get("k"), int) or pp["k"] < 2:
            loi.append("PLSpredict: số phần k phải ≥ 2")
        if not isinstance(pp.get("lap"), int) or pp["lap"] < 1:
            loi.append("PLSpredict: số lần lặp phải ≥ 1")
    return loi


def pls_sem_sap(sap4: str, sap10: str) -> Optional[Dict[str, Any]]:
    """Khối PLS-SEM của SAP §4 (+ hạt giống §10). None ⇒ SAP không khai PLS-SEM; có khối ⇒ {mo_hinh: dict|None, loi:
    [..]} — mo_hinh chỉ có khi khối đọc trọn và hợp lệ (nơi tiêu thụ chặn khi `loi` khác rỗng)."""
    if PLS_NHAN_KHOI not in (sap4 or ""):
        return None
    loi: List[str] = []
    ct: List[Dict[str, Any]] = []
    trong = False
    for d in sap4.splitlines():
        if PLS_NHAN_KHOI in d:
            trong = True
            continue
        if trong:
            if re.match(r"^\s*-\s*\*\*", d) or not d.strip():
                if d.strip():
                    trong = False
                continue
            m = _PLS_DONG_CT.match(d)
            if not m:
                loi.append(f"dòng mô hình đo lường không đọc được: «{d.strip()[:120]}»")
                continue
            ct.append({"ma": m.group(1), "ten": m.group(2).strip(), "mode": "B" if "Mode B" in m.group(3) else "A",
                       "muc": _PLS_BIEN.findall(m.group(4))})
    m_dd = re.search(r"\*\*Mô hình cấu trúc \(PLS-SEM\):\*\*\s*(.+)", sap4)
    dd = [[a, b] for a, b in re.findall(r"`([A-Za-z][A-Za-z0-9_]*)`\s*→\s*`([A-Za-z][A-Za-z0-9_]*)`",
                                        m_dd.group(1))] if m_dd else []
    m_b = re.search(r"\*\*Bootstrap \(PLS-SEM\):\*\*\s*([\d.\s]+?)\s*mẫu lặp", sap4)
    so_b = re.sub(r"[.\s]", "", m_b.group(1)) if m_b else ""
    bootstrap = int(so_b) if so_b else None
    m_ktc = re.search(r"\*\*Bootstrap \(PLS-SEM\):\*\*[^\n]*?KTC phân vị (\d+)%", sap4)
    alpha = round(1 - int(m_ktc.group(1)) / 100, 6) if m_ktc else None
    m_pp = re.search(r"\*\*PLSpredict \(PLS-SEM\):\*\*\s*(.+)", sap4)
    pp: Optional[Dict[str, Any]] = None
    if not m_pp:
        loi.append("thiếu dòng «PLSpredict (PLS-SEM)» (khai cấu trúc đích hoặc «không thực hiện»)")
    elif "không thực hiện" not in m_pp.group(1):
        k_ = re.search(r"k\s*=\s*(\d+)\s*phần", m_pp.group(1))
        lap = re.search(r"(\d+)\s*lần lặp", m_pp.group(1))
        pp = {"k": int(k_.group(1)) if k_ else None, "lap": int(lap.group(1)) if lap else None,
              "dich": _PLS_BIEN.findall(m_pp.group(1).split("cấu trúc đích", 1)[-1])
              if "cấu trúc đích" in m_pp.group(1) else []}
    m_th = re.search(r"\*\*Dữ liệu thiếu \(PLS-SEM\):\*\*\s*(.+)", sap4)
    thieu = None
    if m_th:
        thieu = ("listwise" if "listwise" in m_th.group(1)
                 else ("trung_binh" if "mean replacement" in m_th.group(1) else None))
    nhan_ng = "**Ngưỡng đánh giá định trước (PLS-SEM):**"
    m_ng = sap4[sap4.find(nhan_ng):] if nhan_ng in sap4 else ""
    # hạt giống §10 — bỏ ví dụ nằm trong ô [CẦN …] chưa điền («ví dụ: set.seed(2026)» không phải quyết định)
    s10 = re.sub(r"\[CẦN[^\]]*\]", "", sap10 or "")
    hat = sorted({int(x) for x in re.findall(r"set\.seed\((\d+)\)", s10)}
                 | {int(x) for x in re.findall(r"\*\*Random seed:\*\*\s*(\d+)\s*$", s10, re.M)})
    mh = {"cau_truc": ct, "duong_dan": dd, "bootstrap": bootstrap, "alpha": alpha, "plspredict": pp,
          "du_lieu_thieu": thieu, "seed": hat[0] if len(hat) == 1 else None,
          "nguong_sap": bool(m_ng) and all(c in m_ng for c in PLS_CUM_NGUONG)}
    if "[CẦN" in sap4.split(nhan_ng)[0]:
        loi.append("khối PLS-SEM của SAP §4 còn ô [CẦN …]")
    if bootstrap is None:
        loi.append("không đọc được số mẫu bootstrap («Bootstrap (PLS-SEM): N mẫu lặp»)")
    if alpha is None:
        loi.append("không đọc được mức KTC phân vị bootstrap («KTC phân vị 95%»)")
    if thieu is None:
        loi.append("không đọc được cách xử lý dữ liệu thiếu («listwise» hoặc «mean replacement»)")
    if len(hat) != 1:
        loi.append(f"SAP §10 cần ĐÚNG một hạt giống set.seed(N) cho bootstrap/PLSpredict (thấy {hat or 'không có'})")
    loi += kiem_mo_hinh_pls(mh)
    return {"mo_hinh": None if loi else mh, "loi": loi}


def pls_sem_van_ban(sap_text: str) -> Optional[Dict[str, Any]]:
    """Khối PLS-SEM đọc thẳng từ VĂN BẢN SAP (cùng hàm `rut_noi_dung` dùng) — cho G4 chấm SAP trước khi lập hợp đồng
    và cho bản nháp/đồ gá trong bộ nhớ."""
    sap = unicodedata.normalize("NFC", bo_dong_bam(sap_text or ""))
    muc = cac_muc(sap)
    return pls_sem_sap(muc.get("4", ("", "", ""))[2], muc.get("10", ("", "", ""))[2])


# ─────────────────────────── KTC hiệu số nguy cơ (SAP §4) ───────────────────────────
DONG_HIEU_SO = re.compile(r"risk\s+difference|hieu\s+(?:so\s+)?nguy\s+co|hieu\s+(?:so\s+)?ty\s+le")
#: (mã, mẫu trên văn bản đã bỏ dấu) — phương pháp KTC hiệu số nguy cơ G6 TÍNH ĐƯỢC (khớp run_stats_analysis.KC_HIEU_SO)
KC_HIEU_SO_HO_TRO = (
    ("newcombe", re.compile(r"newcombe(?![^.;\n]{0,40}(?:hieu\s+chinh\s+lien\s+tuc|continuity|\bcc\b))")),
    ("wald", re.compile(r"\bwald\b")),
)
#: phương pháp có tên trong y văn mà G6 CHƯA tính — SAP khai ⇒ chốt đỏ, không tự lùi về Wald
KC_HIEU_SO_CHUA_HO_TRO = (
    ("newcombe có hiệu chỉnh liên tục", re.compile(
        r"newcombe[^.;\n]{0,40}(?:hieu\s+chinh\s+lien\s+tuc|continuity|\bcc\b)")),
    ("Agresti–Caffo", re.compile(r"agresti")),
    ("Miettinen–Nurminen", re.compile(r"miettinen|nurminen")),
    ("Farrington–Manning", re.compile(r"farrington")),
    ("Mee", re.compile(r"\bmee\b")),
    ("Hauck–Anderson", re.compile(r"hauck")),
    ("Brown–Li–Jeffreys", re.compile(r"brown[\s–-]+li|jeffreys")),
    ("chính xác (exact/Santner–Snell/Chan–Zhang)", re.compile(r"\bexact\b|santner|chan[\s–-]+zhang")),
    ("bootstrap", re.compile(r"bootstrap")),
)


def phuong_phap_kc_hieu_so(sap4: str) -> dict:
    """Phương pháp KTC hiệu số nguy cơ SAP §4 khai — chỉ đọc DÒNG nói về hiệu số nguy cơ/hiệu tỷ lệ.

    {"phuong_phap": mã hỗ trợ đầu tiên hoặc None, "chua_ho_tro": [tên…], "dong": [dòng nguồn…]}."""
    dong = [d for d in (sap4 or "").splitlines() if DONG_HIEU_SO.search(bo_dau_d(d))]
    ho_tro: List[str] = []
    chua: List[str] = []
    for d in dong:
        bd = bo_dau_d(d)
        for ten, mau in KC_HIEU_SO_CHUA_HO_TRO:
            if mau.search(bd) and ten not in chua:
                chua.append(ten)
        vi_tri = sorted((m.start(), ma) for ma, mau in KC_HIEU_SO_HO_TRO for m in [mau.search(bd)] if m)
        ho_tro += [ma for _, ma in vi_tri if ma not in ho_tro]
    return {"phuong_phap": ho_tro[0] if ho_tro else None, "chua_ho_tro": chua, "dong": [d.strip() for d in dong]}


def phuong_phap_kc_ty_le(sap4: str) -> Optional[str]:
    """Phương pháp KTC của TỶ LỆ SAP §4 khai (cắt ngang mô tả): «wilson» · «clopper_pearson» · None."""
    bd = bo_dau_d(sap4)
    if "wilson" in bd:
        return "wilson"
    if "clopper" in bd:
        return "clopper_pearson"
    return None


# ─────────────────────────── biến cố hiếm (SAP §5) ───────────────────────────
def phuong_phap_bien_co_hiem(sap5: str) -> dict:
    """Phương pháp biến cố hiếm SAP §5 khai: {"co_dong", "o_trong", "phuong_phap" (mã | None), "dong"}.

    Mã (khớp g4_quality_gate.BIEN_CO_HIEM): firth_dk (Firth có điều kiện) · firth · mo_ta_chinh_xac (Clopper–Pearson +
    Fisher)."""
    dong = next((d for d in (sap5 or "").splitlines() if "bien co hiem" in bo_dau_d(d)), "")
    bd = bo_dau_d(dong)
    o_trong = "[can" in bd
    pp = None
    if not o_trong:
        if "firth" in bd and re.search(r"co\s+dieu\s+kien|conditional", bd):
            pp = "firth_dk"
        elif "firth" in bd:
            pp = "firth"
        elif "clopper" in bd or ("chinh xac" in bd and "fisher" in bd):
            pp = "mo_ta_chinh_xac"
    return {"co_dong": bool(dong), "o_trong": o_trong, "phuong_phap": pp, "dong": dong.strip()}


# ─────────────────────────── α, số phía, seed, phiên bản R ───────────────────────────
_ALPHA_CHAT_RE = re.compile(r"\*\*Alpha \((one|two)-sided\):\*\*\s*([0-9]+(?:[.,][0-9]+)?)")
#: α trên CÙNG một dòng, cho phép ngoặc chú thích/dấu ** ở giữa («- **Alpha (two-sided):** 0.05»)
MAU_ALPHA = r"(?:alpha|α)[^0-9\n]{0,40}0[\.,](\d+)"


def alpha_sap(sap12: str) -> Dict[str, Any]:
    """{"alpha": float | None, "so_phia": 1 | 2 | None} của SAP §12 — dòng khuôn G4 «- **Alpha (one|two-sided):** x»
    đọc trước (có số phía); không có ⇒ mẫu α lỏng trên bản đã bóc nhãn chưa điền (không biết số phía)."""
    m = _ALPHA_CHAT_RE.search(sap12 or "")
    if m:
        return {"alpha": float(m.group(2).replace(",", ".")), "so_phia": 1 if m.group(1) == "one" else 2}
    m2 = re.search(MAU_ALPHA, bo_dau(bo_nhan_chua_dien(sap12 or "")))
    return {"alpha": float("0." + m2.group(1)) if m2 else None, "so_phia": None}


def doc_alpha(sap: str) -> Optional[float]:
    """α đã khoá ở SAP §12 (None nếu không đọc được hoặc còn ô trống) — nhận TOÀN VĂN SAP."""
    return alpha_sap(muc_than(sap, 12))["alpha"]


def doc_seed(sap10: str) -> Optional[str]:
    """Seed ĐÃ CHỐT trong SAP §10 (chuỗi số, tới 12 chữ số) — đọc trên bản đã bóc nhãn chưa điền."""
    m = re.search(r"set\.seed\((\d+)\)|(?:seed|hạt giống)\D{0,12}(\d{3,12})(?!\d)",
                  bo_nhan_chua_dien(sap10), re.IGNORECASE)
    return next(g for g in m.groups() if g) if m else None


def doc_phien_ban_r(sap10: str) -> Optional[str]:
    """Phiên bản R tối thiểu khai ở SAP §10 («R ≥ 4.3», «R 4.4.1», «R version 4.3.2»)."""
    m = re.search(r"(?<![A-Za-z])R\s*(?:≥|>=|phiên bản|version|v)?\s*(\d\.\d+(?:\.\d+)?)", bo_nhan_chua_dien(sap10))
    return m.group(1) if m else None


# ─────────────────────────── phân tích SAP mà đặc tả G6 phải phủ ───────────────────────────
_NHAN_PHAN_TICH = re.compile(r"phân tích|đặc tính đo lường|đáp ứng|nhóm nhỏ tiền định", re.I)
_BIEN_BANG_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`\s*={1,2}\s*'?([A-Za-z0-9_.-]+)'?")


def muc_sap_bat_buoc(sap_text: str) -> List[Tuple[str, str]]:
    """Phân tích SAP mà đặc tả G6 BẮT BUỘC phải phủ: gạch đầu dòng cấp 1 của §9; mục nhãn đậm là phân tích ở §1/§3/§5/§7
    (trừ mục ghi «KHÔNG CÓ»)."""
    ra: List[Tuple[str, str]] = []
    for m in _MUC_RE.finditer(unicodedata.normalize("NFC", sap_text or "")):
        so, than = m.group(1), m.group(3)
        for dong in than.splitlines():
            if not dong.startswith("- "):
                continue
            if so == "9":
                ra.append((f"§{so}", dong.strip()))
            elif so in ("1", "3", "5", "7"):
                nhan = re.match(r"- \*\*(.+?)\*\*", dong)
                if nhan and _NHAN_PHAN_TICH.search(nhan.group(1)) and "KHÔNG CÓ" not in dong.upper():
                    ra.append((f"§{so}", dong.strip()))
    return ra


def quan_the_chinh(sap_text: str) -> Optional[Tuple[str, str]]:
    """(biến, giá trị) SAP §1 dùng khoanh «Quần thể chính» (vd «mọi hồ sơ có `du_tieu_chuan` = 1»); không có ⇒ None."""
    for m in _MUC_RE.finditer(unicodedata.normalize("NFC", sap_text or "")):
        if m.group(1) != "1":
            continue
        for dong in m.group(3).splitlines():
            if "quần thể chính" in dong.casefold():
                k = _BIEN_BANG_RE.search(dong)
                if k:
                    return k.group(1), k.group(2)
    return None


#: từ phủ định + ranh giới mệnh đề — nhận một cụm nằm trong câu PHỦ ĐỊNH (dùng chung với chay_sap_g6)
TU_PHU_DINH = re.compile(r"(?<!\w)(?:không|chưa|chẳng|loại bỏ|bỏ|thay vì)(?!\w)")
RANH_GIOI_MENH_DE = re.compile(r"[.;:!?\n,()]|—|–")
CUA_SO_PHU_DINH = 50  # ký tự trước cụm được xét (đủ cho «Không áp hiệu chỉnh …», không với sang mệnh đề khác)


def bi_phu_dinh(van_ban_cf: str, vi_tri: int) -> bool:
    """Cụm bắt đầu ở `vi_tri` (trong văn bản đã casefold) đứng sau một từ phủ định của CÙNG mệnh đề."""
    truoc = van_ban_cf[max(0, vi_tri - CUA_SO_PHU_DINH):vi_tri]
    ranh = list(RANH_GIOI_MENH_DE.finditer(truoc))
    if ranh:
        truoc = truoc[ranh[-1].end():]
    return bool(TU_PHU_DINH.search(truoc))


_TU_PHAN_TICH_PHU = re.compile(r"(?<!\w)(?:báo thêm|trình bày thêm|tính thêm|ước lượng thêm|kèm thêm|chạy thêm|làm thêm"
                               r"|thông tin phụ|phân tích phụ|phân tích bổ sung)(?!\w)")


def menh_de_phan_tich_phu(sap_text: str) -> List[Tuple[str, str]]:
    """Mệnh đề SAP hứa một phân tích PHỤ viết liền trong câu (ngoài §9 — §9 đã đòi phủ cả gạch đầu dòng).

    Bỏ qua: dấu hiệu bị phủ định («không báo thêm …»), dòng bảng, tiêu đề, khối mã, trích dẫn."""
    ra: List[Tuple[str, str]] = []
    for m in _MUC_RE.finditer(unicodedata.normalize("NFC", sap_text or "")):
        so, than = m.group(1), m.group(3)
        if so == "9":
            continue
        for dong in than.splitlines():
            s = dong.strip()
            if not s or s.startswith(("|", "#", "```", ">")):
                continue
            for menh_de in re.split(r"(?<=[.;])\s+", s):
                cf = menh_de.casefold()
                if any(not bi_phu_dinh(cf, k.start()) for k in _TU_PHAN_TICH_PHU.finditer(cf)):
                    ra.append((f"§{so}", menh_de.strip()))
    return ra


# ─────────────────────────── các trường có kiểu ───────────────────────────
_NHAN_RE = re.compile(r"\*\*([^*\n]+?):\*\*[ \t]*([^\n]*)")
_NHAN_GACH_RE = re.compile(r"^-\s*\*\*([^*\n]+?):\*\*\s*(.*?)\s*$")
#: nhãn §9 của SAP định tính (độ tin cậy — trustworthiness) — không phải phân tích độ nhạy
NHAN_TIN_CAY = ("Credibility", "Transferability", "Dependability", "Confirmability")


def _dong_muc(than: str) -> List[str]:
    return [d.rstrip() for d in (than or "").splitlines() if d.strip() and not re.fullmatch(r"-{3,}", d.strip())]


def _nhan_muc(dong: Sequence[str]) -> Dict[str, str]:
    ra: Dict[str, str] = {}
    for d in dong:
        for m in _NHAN_RE.finditer(d):
            ra.setdefault(m.group(1).strip(), m.group(2).rstrip())
    return ra


def _sach(x: str) -> str:
    """Bỏ chú thích «*(…)*», dấu mã «`…`», dấu đậm và dấu chấm cuối — chữ dùng trong văn bản."""
    x = GHI_CHU_DIEN_SAN_RE.sub("", x or "")
    x = re.sub(r"\s*\*\([^)]*\)\*", "", x)
    x = re.sub(r"`([^`]*)`", r"\1", x)
    x = x.replace("**", "")
    return x.strip().rstrip(".").strip()


def _so_thuc(x: str) -> Optional[float]:
    m = re.search(r"-?\d+(?:[.,]\d+)?", x or "")
    return float(m.group(0).replace(",", ".")) if m else None


def _gia_tri(nhan: Dict[str, str], ten: str) -> str:
    """Giá trị đã điền của nhãn (bỏ chú thích điền sẵn); còn ô trống ⇒ chuỗi rỗng."""
    v = GHI_CHU_DIEN_SAN_RE.sub("", nhan.get(ten, "")).strip()
    return v if co_noi_dung(v) else ""


def _gia_tri_bat_dau(nhan: Dict[str, str], tien_to: str) -> str:
    k = next((k for k in nhan if k.startswith(tien_to)), None)
    return _gia_tri(nhan, k) if k else ""


def _thiet_ke(out_dir: Optional[Path], sap: str) -> Dict[str, Any]:
    mo_ta = None
    m = next((x for x in _PHAN_RE.finditer(sap) if x.group(1) == "1"), None)
    if m:
        k = re.search(r"^\|\s*Thiết kế\s*\|\s*([^|\n]*?)\s*\|", m.group(2), re.M)
        mo_ta = k.group(1) if k and co_noi_dung(k.group(1)) else None
    ma = None
    if out_dir is not None:
        try:
            import gate_contract as GC  # noqa: PLC0415 — import lười, tránh vòng import

            ma = GC.resolve_design_code(Path(out_dir), default="")[0] or None
        except Exception:  # noqa: BLE001 — không giải được mã thiết kế ⇒ ghi None, không đoán
            ma = None
    return {"ma": ma, "mo_ta": mo_ta}


_LIEN_KET = {"poisson": "log", "logistic": "logit", "logistic_dk": "logit", "ordinal": "logit_tich_luy",
             "linear": "dong_nhat"}


#: đơn vị đo của phơi nhiễm liên tục («mỗi 1 SD», «mỗi 10 năm», «mỗi 5 kg/m²», «mỗi 15 phút») — chỉ nhận đơn vị đo
#: lường, không nhận đếm thủ tục («mỗi 5 bản gỡ băng» của SAP định tính)
_DON_VI_DO = r"SD|ĐLC|độ lệch chuẩn|năm|tuổi|tháng|tuần|ngày|giờ|phút|mmHg|mmol/L|mg/dL|kg/m²|kg/m2|kg|cm|%|điểm"


def _don_vi_phoi_nhiem(*doan: str) -> Optional[str]:
    """Đơn vị phơi nhiễm liên tục SAP khai — đọc đầu tiên thấy (§4 trước §5)."""
    for t in doan:
        m = re.search(rf"(?:mỗi|trên mỗi|per)\s+(\d+(?:[.,]\d+)?\s*(?:{_DON_VI_DO}))(?![\w/])", t or "", re.I)
        if m:
            return m.group(1).strip()
    return None


def _du_lieu_thieu(nhan6: Dict[str, str], than6: str) -> Dict[str, Any]:
    cl = next((k for k in nhan6 if k.startswith("Chiến lược")), None)
    chien_luoc = _gia_tri(nhan6, cl) if cl else ""
    bd = bo_dau_d(chien_luoc)
    co_mi = bool(re.search(r"multiple\s+imputation|\bmi\b|\bmice\b|gan\s+da\s+tri", bd))
    co_cc = bool(re.search(r"complete[\s-]*case|ca\s+day\s+du|phan\s+tich\s+hoan\s+chinh", bd))
    cc_chinh = bool(re.search(r"(?:phan\s+tich\s+)?chinh\s+(?:la\s+)?complete[\s-]*case"
                              r"|complete[\s-]*case\s*\(?\s*chinh", bd))
    mi_chinh = bool(re.search(r"(?:phan\s+tich\s+)?chinh\s+(?:la\s+)?(?:mi\b|mice|gan\s+da\s+tri)", bd))
    if cc_chinh:
        phuong_phap, chinh = ("complete_case", "complete_case")
    elif mi_chinh or (co_mi and not co_cc):
        phuong_phap, chinh = ("mi", "mi")
    elif co_mi:
        phuong_phap, chinh = ("mi", None)
    elif co_cc:
        phuong_phap, chinh = ("complete_case", "complete_case")
    else:
        phuong_phap, chinh = ((None, None) if not chien_luoc else ("khac", None))
    m = re.search(r"\bm\s*(=|≥|>=)\s*(\d+)", chien_luoc)
    return {"chien_luoc": _sach(chien_luoc) or None, "phuong_phap": phuong_phap,
            "m": int(m.group(2)) if m else None, "m_toi_thieu": bool(m and m.group(1) != "="),
            "phan_tich_chinh": chinh,
            "complete_case_song_song": bool(re.search(r"complete\s*case", bo_dau(than6)))}


def _do_nhay(dong9: Sequence[str]) -> List[Dict[str, Any]]:
    ra: List[Dict[str, Any]] = []
    for d in dong9:
        if not d.startswith("- "):
            continue
        m = re.match(r"-\s+\*\*([^*\n]+?):\*\*", d)
        if m and m.group(1).strip() in NHAN_TIN_CAY:
            continue
        mo_ta = d[2:].strip()
        bd = bo_dau(mo_ta)
        loai = ("complete_case" if re.search(r"complete[\s-]*case", bd) else
                "thay_bien" if re.search(r"dinh\s+nghia\s+thay\s+the|thay\s+`", bd + mo_ta.lower()) else
                "loai_tru" if re.search(r"^(?:\*\*)?loai\b|\bchi\s+(?:nguoi|tren)", bd) else
                "mo_hinh_khac" if re.search(r"mo\s+hinh|hieu\s+ung\s+co\s+dinh|hoi\s+quy", bd) else "khac")
        ra.append({"ma": f"DN{len(ra) + 1}", "mo_ta": mo_ta, "da_dien": co_noi_dung(mo_ta),
                   "tham_so": {"loai": loai, "bien": list(dict.fromkeys(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`",
                                                                                      mo_ta)))}})
    return ra


def _nhom_con(nhan7: Dict[str, str]) -> List[Dict[str, Any]]:
    k = next((x for x in nhan7 if x.startswith("Nhóm nhỏ tiền định")), None)
    v = _gia_tri(nhan7, k) if k else ""
    if not v or "KHÔNG CÓ" in v.upper():
        return []
    v = re.sub(r"\s*—\s*ghi trước khi xem dữ liệu\s*$", "", v)
    phan = [re.sub(r"^\(\d+\)\s*", "", x).strip() for x in re.split(r";\s*", v) if x.strip()]
    return [{"ma": f"NC{i}", "mo_ta": _sach(x),
             "tham_so": {"bien": list(dict.fromkeys(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", x)))}}
            for i, x in enumerate(phan, 1)]


def _thay_doi_sau_khoa(sap: str) -> List[List[str]]:
    """Các dòng bảng PHẦN 4 (thay đổi sau khi khoá) — ô thô, bỏ dòng kẻ."""
    m = next((x for x in _PHAN_RE.finditer(sap) if x.group(1) == "4"), None)
    ra: List[List[str]] = []
    for d in (m.group(2).splitlines() if m else []):
        if not d.strip().startswith("|"):
            continue
        o = [c.strip() for c in d.strip().strip("|").split("|")]
        if all(set(c) <= {"-", ":", " "} for c in o):
            continue
        ra.append(o)
    return ra


# ─────────────────────────── v2: bộ cắt mục giữ đúng ngữ nghĩa cũ của từng bộ chấm ───────────────────────────
# 24/11/2026 (bác sĩ duyệt mở rộng hợp đồng): g4_quality_gate, g6_quality_gate, nhat_quan_xuyen_cong, gate_contract và
# quyet_dinh_da_chot từng tự cắt mục/dò chữ SAP bằng bộ cắt riêng. Các bộ cắt dưới đây là bản chuyển NGUYÊN NGỮ NGHĨA
# về đây (tên cũ ở mô-đun cũ là bí danh) — các «lưới không-yếu-hơn» của từng cổng giữ nguyên.
def than_muc_g4(text: str, section_num: str) -> str:
    """Thân mục §N kể cả dòng tiêu đề — tới tiêu đề §-kế-tiếp hoặc «## PHẦN» (bộ cắt của g4_quality_gate; ranh giới từ
    sau số chặn «§1» khớp nhầm «§12»)."""
    lines = (text or "").splitlines()
    mau = rf"^#{{2,3}}\s+{re.escape(section_num)}\b"
    start = next((i for i, line in enumerate(lines) if re.match(mau, line)), None)
    if start is None:
        return ""
    end = next((j for j in range(start + 1, len(lines))
                if re.match(r"^#{2,3}\s+§\d", lines[j]) or re.match(r"^##\s+PHẦN", lines[j])), len(lines))
    return "\n".join(lines[start:end])


def than_phan(text: str, so_phan: str) -> str:
    """Thân «## PHẦN <so_phan>» tới «## PHẦN» kế tiếp (hoặc hết tệp) — "" nếu không có."""
    lines = (text or "").splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(rf"^##\s+PHẦN\s+{re.escape(so_phan)}\b", line)), None)
    if start is None:
        return ""
    end = next((j for j in range(start + 1, len(lines)) if re.match(r"^##\s+PHẦN\b", lines[j])), len(lines))
    return "\n".join(lines[start:end])


def muc_g6(sap: str, so: int, chat: bool = False) -> str:
    """Nguyên văn §N (kể cả tiêu đề) tới «### §» kế tiếp; `chat=True` dừng thêm ở «## …» hoặc «---» (§12 của SAP không
    phải RCT là mục cuối — bản cũ kéo tới hết tệp, đọc nhầm α của hộp chứng chỉ khoá). Bộ cắt của g6_quality_gate."""
    ranh_gioi = r"###\s*§|^##(?!#)\s|^-{3,}\s*$|\Z" if chat else r"###\s*§|\Z"
    m = re.search(rf"###\s*§{so}\b.*?(?={ranh_gioi})", sap or "", re.S | re.M)
    return m.group(0) if m else ""


def dong_con_trong(dong_list: Sequence[str], them: Tuple[str, ...] = ()) -> List[str]:
    """Các dòng (rút gọn) còn ô trống theo MỌI họ của hợp đồng ô trống chung."""
    return [re.sub(r"\s+", " ", d.strip())[:160] for d in dong_list if PC.co_o_trong(d, PC.TAT_CA_HO, them)]


KHONG_AP_DUNG_RE = re.compile(r"không\s+áp\s+dụng|not\s+applicable", re.IGNORECASE)


# ─────────────────────────── v2: số liệu đã ký (§12 + N ở §1 và chứng chỉ khoá) ───────────────────────────
#: một số thập phân viết dấu chấm HOẶC dấu phẩy (không nuốt dấu phẩy ngắt câu «0,05, độ tin cậy»)
SO_KY = r"(\d+(?:[.,]\d+)?)"
#: một số NGUYÊN đã ký: có nhóm nghìn kiểu Việt («25.462» — SAP từ 23/11/2026) hoặc không («25462» — SAP ký trước)
NGUYEN_KY = r"(\d{1,3}(?:\.\d{3})+(?!\d)|\d+)"


def so_thuc_ky(chuoi: str) -> float:
    """Số thập phân đã ký — dấu chấm (SAP ký trước 23/11/2026) hoặc dấu phẩy (quy ước tiếng Việt, chốt Q4)."""
    return float(chuoi.replace(",", "."))


def so_nguyen_ky(chuoi: str) -> int:
    """Số nguyên đã ký, bỏ dấu chấm nhóm nghìn."""
    return int(chuoi.replace(".", ""))


MAU_SO_MUC12: Tuple[Tuple[str, str, Any], ...] = (
    ("alpha", r"\*\*Alpha \([^)]*\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("power_pct", r"\*\*Power:\*\*\s*(\d+)%", int),
    ("n", r"\*\*Cỡ mẫu:\*\*\s*N\s*=\s*" + NGUYEN_KY, so_nguyen_ky),
    ("hypothesis_type", r"\*\*Loại giả thuyết:\*\*\s*(\S+)", str),
    ("margin", r"\*\*Biên \(margin, Δ\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("sd", r"\*\*Độ lệch chuẩn \(SD\) kết cục:\*\*\s*" + SO_KY, so_thuc_ky),
    # VÁ 04/10/2026 (soát từng cổng, G4-06/G4-08): tham số QUYẾT ĐỊNH N mà SAP ký từng không ghi (sai số d của thiết
    # kế theo độ chính xác, p0, bỏ cuộc, chiều kết cục NI, cụm, chẩn đoán, FPC) — nay in ở §12 và đối chiếu G3.
    ("precision", r"\*\*Sai số tuyệt đối cho phép \(d\):\*\*\s*±?\s*" + SO_KY, so_thuc_ky),
    ("p_uoc_luong", r"\*\*Tỷ lệ ước lượng \(p\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("p0", r"\*\*Tỷ lệ biến cố nhóm chứng \(p0\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("p_event", r"\*\*Tỷ lệ biến cố \(log-rank, p_event\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("dropout", r"\*\*Tỷ lệ bỏ cuộc dự kiến:\*\*\s*" + SO_KY, so_thuc_ky),
    ("outcome_direction", r"\*\*Chiều kết cục:\*\*\s*(higher_better|lower_better)", str),
    ("design_effect", r"\*\*Hiệu ứng thiết kế \(DE\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("icc", r"\*\*ICC:\*\*\s*" + SO_KY, so_thuc_ky),
    ("cluster_size", r"\*\*Cỡ cụm trung bình \(m\):\*\*\s*" + SO_KY, so_thuc_ky),
    ("n_clusters", r"\*\*Số cụm:\*\*\s*" + NGUYEN_KY, so_nguyen_ky),
    ("n_benh", r"\*\*Số ca bệnh cần:\*\*\s*" + NGUYEN_KY, so_nguyen_ky),
    ("n_khong_benh", r"\*\*Số ca không bệnh cần:\*\*\s*" + NGUYEN_KY, so_nguyen_ky),
    ("prevalence", r"\*\*Tỷ lệ hiện mắc dự kiến:\*\*\s*" + SO_KY, so_thuc_ky),
    ("population_n", r"\*\*Quần thể hữu hạn \(FPC\):\*\*\s*N\s*=\s*" + NGUYEN_KY, so_nguyen_ky),
)


def doc_so_lieu_ky(text: str) -> Dict[str, Any]:
    """Số liệu đã KÝ: §12 (α/power/N/effect/giả thuyết/biên/SD + tham số quyết định N), N ở §1 (`n_muc1`) và ở chứng
    chỉ khoá PHẦN 5 (`n_chung_chi`); `alpha_khong_ap_dung`/`power_khong_ap_dung` = SAP khai tường minh «KHÔNG ÁP DỤNG».
    Bộ đọc của g4_quality_gate.parse_signed_numbers (chuyển về đây 24/11/2026). Đọc cả hai quy ước số: SAP ký trước
    23/11/2026 (dấu chấm thập phân, N không nhóm nghìn) và SAP sinh từ ngày đó (dấu phẩy, N từ 5 chữ số nhóm nghìn)."""
    text = bo_dong_bam(text or "")
    section = than_muc_g4(text, "§12")
    result: Dict[str, Any] = {"found": bool(section), "effect_type": None, "effect_val": None,
                              "alpha_khong_ap_dung": False, "power_khong_ap_dung": False}
    result.update({khoa: None for khoa, _mau, _kieu in MAU_SO_MUC12})
    if section:
        for khoa, mau, kieu in MAU_SO_MUC12:
            m = re.search(mau, section)
            if m:
                result[khoa] = kieu(m.group(1))
        m = re.search(r"\*\*Effect size dự kiến:\*\*\s*(\S+)\s*=\s*" + SO_KY, section)
        if m:
            result["effect_type"] = m.group(1)
            result["effect_val"] = so_thuc_ky(m.group(2))
        result["alpha_khong_ap_dung"] = bool(re.search(r"\*\*Alpha[^*\n]*:\*\*\s*KHÔNG ÁP DỤNG", section))
        result["power_khong_ap_dung"] = bool(re.search(r"\*\*Power:\*\*\s*KHÔNG ÁP DỤNG", section))
    m1 = re.search(r"\*\*Cỡ mẫu cuối:\*\*\s*N\s*=\s*" + NGUYEN_KY, than_muc_g4(text, "§1"))
    result["n_muc1"] = so_nguyen_ky(m1.group(1)) if m1 else None
    m5 = re.search(r"Cỡ mẫu\s*:\s*N\s*=\s*" + NGUYEN_KY, than_phan(text, "5"))
    result["n_chung_chi"] = so_nguyen_ky(m5.group(1)) if m5 else None
    return result


# ─────────────────────────── v2: kết cục (§2) ───────────────────────────
def ket_cuc_chinh_bien(sap2: str) -> Optional[str]:
    """Tên biến kết cục CHÍNH trong SAP §2 (chữ thường) — None nếu không rút được (bộ đọc của g6_quality_gate).

    Dòng có NHÃN «Kết cục chính»/«Primary outcome» đứng đầu (không phải «phụ»/«secondary») và tối đa hai dòng NỐI TIẾP
    (dừng ở dòng trống, tiêu đề, gạch đầu dòng khác cùng/nông hơn): ưu tiên tên trong backtick, rồi tên trong ngoặc
    đơn («(biến SHLNBChung_TrucTiep)»), rồi định danh snake_case/CamelCase."""
    dong = (sap2 or "").splitlines()
    for i, d in enumerate(dong):
        bd = bo_dau(d)
        if not re.match(r"\s*(?:\|\s*)?(?:[-*•]\s*)?(?:\*\*)?\s*(?:ket\s*cuc\s*chinh|primary\s*outcome)", bd) or \
                re.search(r"\bphu\b|secondary", bd):
            continue
        thut = len(d) - len(d.lstrip())
        tiep = []
        for k in dong[i + 1:i + 3]:
            if not k.strip() or k.lstrip().startswith("#") or (
                    re.match(r"\s*(?:[-*•]|\d+[.)])\s", k) and len(k) - len(k.lstrip()) <= thut):
                break
            tiep.append(k)
        for khoi in (d, *tiep):
            for mau in (r"`([A-Za-z][A-Za-z0-9_]{1,})`",
                        r"\(\s*(?:biến|bien|variable)?\s*:?\s*([A-Za-z][A-Za-z0-9_]{2,})\s*[,)]",
                        r"\b([a-z][a-z0-9]*_[a-z0-9_]+)\b",
                        r"\b([A-Z][a-z0-9]+[A-Z][A-Za-z0-9_]*)\b"):
                m = re.search(mau, khoi)
                if m:
                    return m.group(1).lower()
    return None


def ket_cuc_phu_bien(sap2: str) -> List[str]:
    """Tên biến kết cục PHỤ (backtick) ở các dòng «Kết cục phụ»/«Secondary» của SAP §2 — giữ thứ tự, bỏ trùng."""
    ra: List[str] = []
    for d in (sap2 or "").splitlines():
        if re.search(r"ket\s*cuc\s*phu|secondary", bo_dau(d)):
            for t in re.findall(r"`([A-Za-z][A-Za-z0-9_]{2,})`", d):
                if t.lower() not in ra:
                    ra.append(t.lower())
    return ra


def ten_ket_cuc_trong_muc_2(sap2: str) -> List[str]:
    """Mọi tên kết cục (chính/phụ) ở §2 — backtick hoặc chữ đậm trên dòng nhắc chính/phụ (đã bỏ dấu)."""
    ten: set = set()
    for d in bo_dau(sap2 or "").splitlines():
        if any(k in d for k in ("chinh", "phu", "primary", "secondary")):
            ten.update(re.findall(r"`([a-z0-9_]{3,})`|\*\*([a-z0-9_ ]{4,30})\*\*", d))
    return sorted({next(x for x in t if x).strip() for t in ten if any(t)})


def ket_cuc_chinh_dong(text: str) -> str:
    """Nguyên văn sau «**Kết cục chính[ (MTk)]:**» ở §2 (nhận cả nhãn mục tiêu trong ngoặc)."""
    m = re.search(r"\*\*Kết cục chính(?:\s*\([^)]*\))?:\*\*\s*(.+)", than_muc_g4(text, "§2"))
    return m.group(1).strip() if m else ""


def ten_ket_cuc_chinh(text: str) -> str:
    """Phần TÊN kết cục chính ở §2 — bỏ chú thích điền sẵn và đuôi máy điền («; đo bằng …; thời điểm: … — biến `x`»)."""
    kc = GHI_CHU_DIEN_SAN_RE.sub("", ket_cuc_chinh_dong(text)).strip()
    kc = re.sub(r"[\s.,;—–-]+[Bb]iến\s+`[^`]+`\s*$", "", kc)
    return re.split(r";\s+(?:đo bằng|thời điểm:)\s", kc, maxsplit=1)[0].strip()


KHOANG_TG_RE = re.compile(r"(?<![/\-\d])(\d+(?:[.,]\d+)?)\s*(ngày|tuần|tháng|năm|giờ|phút)\b", re.IGNORECASE)
NGAY_RE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})(?:/(\d{4}))?(?!\d)")


def moc_thoi_gian(chu: str) -> Tuple[frozenset, frozenset]:
    """(khoảng thời gian «12 tháng», mốc ngày «01/01», «31/12», «2026») trong một mô tả thời điểm đo."""
    t = unicodedata.normalize("NFC", str(chu or "")).lower()
    khoang = frozenset(f"{so.replace(',', '.')} {dv}" for so, dv in KHOANG_TG_RE.findall(t))
    ngay = set()
    for d, m, y in NGAY_RE.findall(t):
        if 1 <= int(d) <= 31 and 1 <= int(m) <= 12:
            ngay.add(f"{int(d):02d}/{int(m):02d}")
            if y:
                ngay.add(y)
    return khoang, frozenset(ngay)


def thoi_diem_ket_cuc(text: str) -> Tuple[str, bool]:
    """(mô tả thời điểm đo kết cục chính trong §2, §2 có dòng kết cục chính?)."""
    m = re.search(r"\*\*Thời điểm đo[^*]*:\*\*\s*(.+)", than_muc_g4(text, "§2"))
    if m:
        return m.group(1).strip(), True
    kc = ket_cuc_chinh_dong(text)
    m = re.search(r"thời điểm:\s*([^;]+)", kc, re.IGNORECASE)
    if m:
        return m.group(1).strip(), True
    k, n = moc_thoi_gian(kc)
    return (kc if (k or n) else ""), bool(kc)


# ─────────────────────────── v2: seed (§10) và α (§12) với trạng thái điền ───────────────────────────
def _seed_sap(sap: str) -> Dict[str, Any]:
    sap10 = muc_g6(sap, 10)
    cu = re.search(r"set\.seed\((\d+)\)|seed\D{0,12}(\d{3,12})(?!\d)", sap10)
    dong = [d for d in sap10.splitlines() if re.search(r"seed|hạt giống", d, re.IGNORECASE)]
    return {"gia_tri": doc_seed(sap10), "tho": next((g for g in cu.groups() if g), None) if cu else None,
            "dong_con_trong": dong_con_trong(dong, ("[CẦN",)),
            "khong_ap_dung": any(KHONG_AP_DUNG_RE.search(d) for d in dong), "muc_con_can": "[CẦN" in sap10}


def _alpha_trang_thai(sap: str) -> Dict[str, Any]:
    hep, rong = muc_g6(sap, 12, chat=True), muc_g6(sap, 12)
    a_hep = re.search(MAU_ALPHA, bo_dau(bo_nhan_chua_dien(hep)))
    a_rong = re.search(MAU_ALPHA, bo_dau(rong))
    dong = [d for d in hep.splitlines() if re.search(r"alpha|α", bo_dau(d))]
    return {"chu_so": a_hep.group(1) if a_hep else None, "chu_so_rong": a_rong.group(1) if a_rong else None,
            "dong_con_trong": dong_con_trong(dong), "khong_ap_dung": any(KHONG_AP_DUNG_RE.search(d) for d in dong),
            "can_hep": "[can" in bo_dau(hep), "can_rong": "[can" in bo_dau(rong)}


# ─────────────────────────── v2: khai báo mô hình (gate_contract) và trọng số (g6_trong_so_survey) ───────────────
MAU_THU_BAC = re.compile(r"proportional\s+odds|logistic\s+th[ưứ]\s*t[ựụ]|h[ồo]i\s+quy\s+th[ưứ]\s+b[ậa]c|"
                         r"ordinal\s+logistic", re.I)
#: phương pháp chính là ƯỚC LƯỢNG TỶ LỆ (đề tài MÔ TẢ theo độ chính xác) — chỉ đọc dòng «Phương pháp» của §4
PHUONG_PHAP_TY_LE_RE = re.compile(r"ư[ớo]c\s+l[ưượ]+ng\s+t[ỷỉy]\s+l[ệe]|wilson|t[ỷỉy]\s+l[ệe]\s+hi[ệe]n\s+m[ắa]c|"
                                  r"\bprevalence\b|\bproportion\s+estimat", re.I)


def phuong_phap_la_ty_le(dong_phuong_phap: str) -> bool:
    """Dòng «Phương pháp» khai ước lượng tỷ lệ (Wilson/tỷ lệ hiện mắc) và KHÔNG khai mô hình hồi quy làm phân tích
    chính."""
    t = str(dong_phuong_phap or "")
    return bool(PHUONG_PHAP_TY_LE_RE.search(t)) and not re.search(r"h[ồo]i\s+quy|regression|logistic|poisson|cox",
                                                                    t, re.I)


def goi_post_stratify(sap: str) -> bool:
    """SAP §4 có GỌI `postStratify(` — điều kiện DUY NHẤT để đòi trọng số hậu phân tầng (bộ sinh G6 và G6-AUTO-11)."""
    return bool(re.search(r"postStratify\s*\(", muc_g6(sap, 4)))


def _khai_bao(sap: str) -> Dict[str, Any]:
    m4 = re.search(r"^#{2,4}\s*§\s*4\b[^\n]*\n(.*?)(?=^#{2,4}\s*§\s*\d|^#{1,2}\s|\Z)", sap, re.M | re.S)
    pp = re.search(r"\*\*Phương pháp:\*\*\s*([^\n]+)", m4.group(1)) if m4 else None
    return {"thu_bac": bool(MAU_THU_BAC.search(sap)), "ty_le": bool(pp) and phuong_phap_la_ty_le(pp.group(1)),
            "post_stratify": goi_post_stratify(sap)}


# ─────────────────────────── v2: dòng khai và điều SAP nhắc tới (nhat_quan_xuyen_cong) ───────────────────────────
DONG_CHUAN_BOLD = re.compile(r"^\*\*Chuẩn báo cáo(?: áp dụng)?:\*\*(.*)$", re.M)
DONG_CHUAN_BANG = re.compile(r"^\|\s*Chuẩn báo cáo(?: áp dụng)?\s*\|([^|\n]*)\|", re.M)
DONG_THIET_KE_BANG = re.compile(r"^\|\s*Thiết kế\s*\|([^|\n]*)\|", re.M)
PHIEN_BAN_TIEU_DE = re.compile(r"\*\*Phiên bản SAP:\*\*\s*([0-9]+(?:\.[0-9]+)*)")
DONG_LICH_SU = re.compile(r"^\|\s*([0-9]+(?:\.[0-9]+)*)\b[^|\n]*\|\s*\d{4}-\d{2}-\d{2}\s*\|", re.M)


def dong_dau(rx: "re.Pattern[str]", van_ban: str) -> Optional[str]:
    """Giá trị của DÒNG khai đầu tiên khớp `rx` (nhóm 1, đã gọn) — đọc đúng dòng khai, không cả tệp."""
    m = rx.search(unicodedata.normalize("NFC", van_ban or ""))
    return m.group(1).strip() if m else None


#: kỹ thuật chọn mẫu ⇒ mẫu nhận diện trong văn bản; cụm «chọn mẫu <cách>»; phủ định; thuật lại tài liệu khác
KY_THUAT_CHON_MAU = {"toan_bo": r"toàn\s+bộ", "ngau_nhien_don": r"ngẫu\s+nhiên\s+đơn",
                     "he_thong": r"(?:chọn\s+mẫu|mẫu)\s+hệ\s+thống|systematic", "phan_tang": r"phân\s+tầng|stratif",
                     "cum": r"chùm|cụm|cluster", "lien_tiep": r"liên\s+tiếp|consecutive",
                     "chu_dich": r"chủ\s+đích|purposive", "thuan_tien": r"thuận\s+tiện|convenience"}
CUM_CHON_MAU = re.compile(r"chọn\s+mẫu\s+(ngẫu\s+nhiên\s+đơn|hệ\s+thống|phân\s+tầng|(?:theo\s+)?(?:chùm|cụm)|"
                          r"thuận\s+tiện|chủ\s+đích|toàn\s+bộ)", re.I)
PHU_DINH_CHON_MAU = re.compile(r"(không|thay\s+vì|tránh|chứ\s+không|thay\s+cho|loại\s+bỏ)[^.;\n]{0,25}$", re.I)
THUAT_LAI = re.compile(r"thuyết\s+minh|bản\s+(?:cũ|trước)|phiên\s+bản\s+trước|đề\s+cương\s+(?:cũ|trước)", re.I)
GIAI_TRINH_DOI = re.compile(r"cụ\s+thể\s+h(?:óa|oá|oa)|thay\s+(?:bằng|thế)|điều\s+chỉnh\s+thành", re.I)
GIAI_TRINH_LY_DO = re.compile(r"chặt\s+chẽ\s+hơn|lý\s+do|\bvì\b|bởi\s+vì|nhằm|để\s+(?:tránh|bảo\s+đảm|phủ|giảm)", re.I)


def da_giai_trinh(doan: str) -> bool:
    """Đoạn thuật lại có câu giải trình: «giải trình», hoặc CẢ động từ thay đổi lẫn lý do."""
    return bool(re.search(r"giải\s+trình", doan, re.I)
                or (GIAI_TRINH_DOI.search(doan) and GIAI_TRINH_LY_DO.search(doan)))


def ma_cum_chon_mau(t: str) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    for ma, mau in (("ngau_nhien_don", "ngẫu nhiên đơn"), ("he_thong", "hệ thống"), ("phan_tang", "phân tầng"),
                    ("thuan_tien", "thuận tiện"), ("chu_dich", "chủ đích"), ("toan_bo", "toàn bộ")):
        if re.search(mau.replace(" ", r"\s+"), t):
            return ma
    return "cum"


def phan_tich_chon_mau(van_ban: str) -> Dict[str, Any]:
    """Văn bản nói gì về chọn mẫu: `nhac` {mã kỹ thuật: có nhắc?}; `cum` — mỗi cụm «chọn mẫu <cách>» kèm mã, bị phủ
    định, là câu thuật lại tài liệu khác, đoạn thuật lại đã giải trình. Dùng cho SAP (qua hợp đồng) và mọi văn bản khác
    nhat_quan_xuyen_cong so (chiến lược tuyển chọn G1, đề cương nộp)."""
    vb = unicodedata.normalize("NFC", van_ban or "")
    cum = []
    for mm in CUM_CHON_MAU.finditer(vb):
        dau_cau = max(vb.rfind(". ", 0, mm.start()), vb.rfind("\n", 0, mm.start())) + 1
        thuat_lai = bool(THUAT_LAI.search(vb[dau_cau:mm.start()]))
        giai_trinh = False
        if thuat_lai:
            dau_doan = vb.rfind("\n\n", 0, mm.start()) + 1
            cuoi_doan = vb.find("\n\n", mm.end())
            giai_trinh = da_giai_trinh(vb[dau_doan:cuoi_doan if cuoi_doan >= 0 else len(vb)])
        cum.append({"cum": mm.group(0), "ma": ma_cum_chon_mau(mm.group(1)),
                    "phu_dinh": bool(PHU_DINH_CHON_MAU.search(vb[max(0, mm.start() - 40):mm.start()])),
                    "thuat_lai": thuat_lai, "da_giai_trinh": giai_trinh})
    return {"nhac": {ma: bool(re.search(rx, vb, re.I)) for ma, rx in KY_THUAT_CHON_MAU.items()}, "cum": cum}


def doan_n_toi_thieu(van_ban: str) -> List[str]:
    """90 ký tự sau mỗi lần nhắc «N tối thiểu»/«cỡ mẫu tối thiểu»."""
    vb = van_ban or ""
    return [vb[x.end():x.end() + 90] for x in re.finditer(r"(?:\bN|cỡ\s+mẫu)\s+tối\s+thiểu", vb, re.I)]


def _nhac(sap: str) -> Dict[str, Any]:
    return {
        "muc_tieu": sorted({m.group(1) for m in re.finditer(r"(?:MT|Mục tiêu)\s*(\d+)\b", sap)}, key=int),
        "chon_mau_chum": bool(re.search(r"chọn mẫu (theo )?(chùm|cụm)", sap, re.I)),
        "de": [float(x.replace(",", ".")) for x in re.findall(r"\bDE\s*[:=]?\s*(1[.,]\d+)", sap)],
        "bien_sau_chum": sorted(set(re.findall(r"(?:chùm|cụm|cluster)\s*\(?\s*`([A-Za-z_][A-Za-z0-9_:]*)`", sap,
                                               re.I))),
        "n_toi_thieu": doan_n_toi_thieu(sap),
        "chon_mau": phan_tich_chon_mau(sap),
    }


def _dong_khai(sap: str) -> Dict[str, Any]:
    return {"chuan_bao_cao_tieu_de": dong_dau(DONG_CHUAN_BOLD, sap),
            "chuan_bao_cao_bang": dong_dau(DONG_CHUAN_BANG, sap),
            "thiet_ke_bang": dong_dau(DONG_THIET_KE_BANG, sap),
            "phien_ban_tieu_de": dong_dau(PHIEN_BAN_TIEU_DE, sap[:4000]),
            "phien_ban_lich_su": DONG_LICH_SU.findall(sap)}


def _ket_cuc_sap(sap: str) -> Dict[str, Any]:
    sap2 = muc_g6(sap, 2)
    tp, co = thoi_diem_ket_cuc(sap)
    return {"nguyen_van": ket_cuc_chinh_dong(sap) or None, "ten": ten_ket_cuc_chinh(sap) or None,
            "thoi_diem": tp or None, "co_dong_chinh": co, "bien_chinh": ket_cuc_chinh_bien(sap2),
            "bien_phu": ket_cuc_phu_bien(sap2), "ten_trong_muc_2": ten_ket_cuc_trong_muc_2(sap2)}


def _truong_v2(sap: str) -> Dict[str, Any]:
    """Các trường hợp đồng v2 (24/11/2026) — điều g4/g6_quality_gate, nhat_quan_xuyen_cong, gate_contract và
    quyet_dinh_da_chot từng tự dò chữ SAP."""
    return {"so_lieu_ky": doc_so_lieu_ky(sap), "ket_cuc_sap": _ket_cuc_sap(sap), "seed_sap": _seed_sap(sap),
            "alpha_sap": _alpha_trang_thai(sap), "khai_bao": _khai_bao(sap), "dong_khai": _dong_khai(sap),
            "nhac": _nhac(sap)}


def rut_noi_dung(sap_text: str, out_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Nội dung hợp đồng rút từ văn bản SAP — hàm DUY NHẤT đọc chữ SAP cho G6/G7."""
    sap = unicodedata.normalize("NFC", bo_dong_bam(sap_text or ""))
    muc = cac_muc(sap)

    def than(so: int) -> str:
        return muc.get(str(so), ("", "", ""))[1]

    def nguyen_van(so: int) -> str:
        return muc.get(str(so), ("", "", ""))[2]

    cau_truc = {so: {"tieu_de": td, "dong": _dong_muc(th), "nhan": _nhan_muc(_dong_muc(th))}
                for so, (td, th, _nv) in muc.items()}

    def nh(so: int) -> Dict[str, str]:
        return cau_truc.get(str(so), {}).get("nhan", {})

    pls = pls_sem_sap(nguyen_van(4), nguyen_van(10))
    ho = ["pls_sem"] if pls is not None else sorted(ho_mo_hinh(nguyen_van(4)))
    kc = phuong_phap_kc_hieu_so(nguyen_van(4))
    bch = phuong_phap_bien_co_hiem(than(5))
    a = alpha_sap(than(12))
    lg = re.match(r"\s*([a-z_]+)", _gia_tri(nh(12), "Loại giả thuyết"))
    bien = _gia_tri_bat_dau(nh(12), "Biên")
    kc_chinh = _gia_tri(nh(2), "Kết cục chính")
    bien_kc = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", kc_chinh)
    bien_dl = _gia_tri(nh(5), "Biến độc lập đưa vào")
    cum = _gia_tri(nh(4), "Hiệu chỉnh cụm")
    pp_chinh = _gia_tri(nh(4), "Phương pháp")
    co_cum = bool(cum and not re.match(r"\s*không áp dụng", cum, re.I)) or bool(
        re.search(r"\bcum\b|cluster|\bgee\b|hieu\s+ung\s+ngau\s+nhien\s+theo\s+cum", bo_dau_d(pp_chinh)))
    if "logistic_dk" in ho:
        kieu_ghep = "ca_the"
    elif re.search(r"ghep\s+theo\s+tan\s+suat|frequency\s+match|logistic\s+khong\s+dieu\s+kien",
                   bo_dau_d(than(4) + "\n" + than(5))):
        kieu_ghep = "tan_suat"
    else:
        kieu_ghep = None
    lk = [_LIEN_KET[h] for h in ho if h in _LIEN_KET]
    m_muc = re.search(r"(\d{2})\s*%\s*(?:CI|KTC)|KTC\s*(\d{2})\s*%|độ tin cậy\s*(\d{2})\s*%", than(4) + "\n" + than(12))
    qt = quan_the_chinh(sap)
    return {
        "thiet_ke": _thiet_ke(out_dir, sap),
        "kieu_ghep": kieu_ghep,
        "phan_tich_chinh": {
            "ket_cuc": {"mo_ta": _sach(kc_chinh) or None, "bien": bien_kc[0] if bien_kc else None},
            "phuong_phap": _sach(pp_chinh) or None,
            "ho_mo_hinh": ho,
            "lien_ket": lk[0] if len(set(lk)) == 1 else None,
            "bien_doc_lap": list(dict.fromkeys(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", bien_dl))),
            "cum": {"co": co_cum, "mo_ta": _sach(cum) or None},
            "bo_ghep": kieu_ghep == "ca_the",
            "don_vi_phoi_nhiem": _don_vi_phoi_nhiem(than(4), than(5)),
            "quan_the": {"mo_ta": _sach(_gia_tri(nh(1), "Quần thể chính")) or None,
                         "loc": {"bien": qt[0], "gia_tri": qt[1]} if qt else None,
                         "phan_tich": _sach(_gia_tri(nh(4), "Quần thể")) or None},
        },
        "khoang_tin_cay": {"muc": next((int(g) / 100 for g in (m_muc.groups() if m_muc else ()) if g), None),
                           "hieu_so_nguy_co": kc["phuong_phap"], "hieu_so_chua_ho_tro": kc["chua_ho_tro"],
                           "dong_hieu_so": kc["dong"], "ty_le": phuong_phap_kc_ty_le(than(4))},
        "gia_thuyet": {"alpha": a["alpha"], "so_phia": a["so_phia"], "khung": lg.group(1) if lg else None,
                       "bien": _so_thuc(bien) if bien else None},
        "du_lieu_thieu": _du_lieu_thieu(nh(6), than(6)),
        "bien_co_hiem": {"phuong_phap": bch["phuong_phap"], "co_dong": bch["co_dong"], "o_trong": bch["o_trong"],
                         "dong": bch["dong"] or None},
        "do_nhay": _do_nhay(cau_truc.get("9", {}).get("dong", [])),
        "nhom_con": _nhom_con(nh(7)),
        "phan_mem": {"mo_ta": _sach(_gia_tri(nh(10), "Phần mềm")) or None,
                     "goi": _sach(_gia_tri(nh(10), "Packages")) or None,
                     "seed": doc_seed(than(10)), "r_toi_thieu": doc_phien_ban_r(than(10))},
        "phan_tich_bat_buoc": [{"muc": mu, "dong": d} for mu, d in muc_sap_bat_buoc(sap)],
        "phan_tich_phu_trong_cau": [{"muc": mu, "menh_de": md} for mu, md in menh_de_phan_tich_phu(sap)],
        "thay_doi_sau_khoa": _thay_doi_sau_khoa(sap),
        "muc": cau_truc,
        **_truong_v2(sap),
        # v3 (24/11/2026): khối PLS-SEM máy đọc (None ⇒ SAP không khai) — pls_sem.py, G4-AUTO-10, chay_sap_g6 kiem,
        # G6-AUTO-09 đọc trường này, không dò chữ SAP
        "pls_sem": pls,
    }


# ─────────────────────────── lập · băm · ghi · kiểm ───────────────────────────
def _loi(hd: Dict[str, Any]) -> Dict[str, Any]:
    return {k: hd.get(k) for k in ("schema", "study", "tep_sap", "sha256_sap_noi_dung", "noi_dung")}


def bam_hop_dong(hd: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(_loi(hd), ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def lap(sap_text: str, study: str, out_dir: Optional[Path], nguon: str) -> Dict[str, Any]:
    """Hợp đồng đầy đủ (chưa ghi tệp) cho văn bản SAP `sap_text`."""
    if nguon not in NGUON_HOP_LE:
        raise ValueError(f"nguồn hợp đồng không hợp lệ: {nguon!r}")
    hd = {"schema": SCHEMA, "study": study, "tep_sap": ten_sap(study), "nguon": nguon,
          "ngay_lap": date.today().isoformat(), "sha256_sap_noi_dung": bam_sap(sap_text),
          "noi_dung": rut_noi_dung(sap_text, out_dir)}
    hd["sha256_hop_dong"] = bam_hop_dong(hd)
    return hd


def luu(out_dir: Path, study: str, hd: Dict[str, Any]) -> Path:
    p = Path(out_dir) / ten_tep(study)
    p.write_text(json.dumps(hd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p


def gan_vao_sap(sap_text: str, study: str, out_dir: Optional[Path]) -> Tuple[Optional[str], Dict[str, Any]]:
    """(SAP mang dòng băm trong chứng chỉ khoá, hợp đồng nguồn `sinh_khi_dung`); SAP sai khuôn ⇒ (None, hợp đồng)."""
    hd = lap(sap_text, study, out_dir, NGUON_SINH)
    return chen_dong_bam(sap_text, study, hd["sha256_hop_dong"]), hd


def kiem(out_dir: Path, study: str, hd: Any, sap_text: Optional[str] = None) -> List[str]:
    """Lỗi của hợp đồng `hd` so với SAP hiện tại; rỗng = hợp lệ."""
    out_dir = Path(out_dir)
    if not isinstance(hd, dict):
        return [f"{ten_tep(study)} không phải đối tượng JSON"]
    if hd.get("schema") not in SCHEMA_HO_TRO:
        return [f"{ten_tep(study)} sai schema ({hd.get('schema')!r}, cần {SCHEMA!r})"]
    loi: List[str] = []
    if hd.get("study") != study or hd.get("tep_sap") != ten_sap(study):
        loi.append(f"{ten_tep(study)} khai đề tài/tệp SAP khác ({hd.get('study')!r}, {hd.get('tep_sap')!r})")
    if hd.get("nguon") not in NGUON_HOP_LE:
        loi.append(f"{ten_tep(study)} khai nguồn không hợp lệ: {hd.get('nguon')!r}")
    if hd.get("sha256_hop_dong") != bam_hop_dong(hd):
        loi.append(f"{ten_tep(study)} đã bị SỬA sau khi lập (băm hợp đồng không khớp nội dung)")
    if sap_text is None:
        try:
            sap_text = (out_dir / ten_sap(study)).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return loi + [f"không đọc được {ten_sap(study)} để đối chiếu hợp đồng"]
    if hd.get("sha256_sap_noi_dung") != bam_sap(sap_text):
        loi.append(f"SAP đã ĐỔI sau khi lập {ten_tep(study)} — chạy lại `python3 tools/hop_dong_sap.py ghi --study "
                   f"{study}` trước khi khoá/ký")
    else:
        moi = rut_noi_dung(sap_text, out_dir)
        khoa_cu = KHOA_THEO_SCHEMA.get(hd.get("schema"))
        if khoa_cu:  # v1/v2: chỉ các khoá của phiên bản đó nằm trong băm — đối chiếu đúng các khoá đó
            moi = {k: moi.get(k) for k in khoa_cu}
        if hd.get("noi_dung") != moi:
            loi.append(f"{ten_tep(study)} LỆCH văn bản SAP (bộ đọc chạy lại trên SAP cho nội dung khác) — lập lại hợp "
                       "đồng")
    bam = bam_trong_sap(sap_text)
    if hd.get("nguon") == NGUON_SINH:
        if not bam:
            loi.append(f"chứng chỉ khoá SAP (PHẦN 5) chưa mang băm hợp đồng «{NHAN_DONG_BAM}»")
        elif len(bam) > 1 or bam[0] != hd.get("sha256_hop_dong"):
            loi.append(f"băm hợp đồng trong chứng chỉ khoá SAP ({', '.join(b[:12] for b in bam)}…) khác "
                       f"{ten_tep(study)} ({str(hd.get('sha256_hop_dong'))[:12]}…)")
    elif hd.get("nguon") == NGUON_SUY and bam:
        loi.append(f"SAP mang băm hợp đồng trong chứng chỉ khoá nhưng {ten_tep(study)} khai «suy từ bản ký» — hợp đồng "
                   "của SAP có băm phải là bản sinh khi dựng")
    return loi


def loi_bam_van_ban(sap_text: str, study: str, out_dir: Optional[Path] = None) -> List[str]:
    """Kiểm CHỈ trên văn bản SAP (đồ gá trong bộ nhớ, không có tệp hợp đồng): chứng chỉ khoá mang ĐÚNG một băm và băm
    đó bằng băm của hợp đồng lập từ chính văn bản (cùng `out_dir` khi lập)."""
    bam = bam_trong_sap(sap_text)
    if not bam:
        return [f"chứng chỉ khoá SAP (PHẦN 5) chưa mang băm hợp đồng «{NHAN_DONG_BAM}»"]
    can = lap(sap_text, study, out_dir, NGUON_SINH)["sha256_hop_dong"]
    if len(bam) > 1 or bam[0] != can:
        return [f"băm hợp đồng trong chứng chỉ khoá SAP ({', '.join(b[:12] for b in bam)}…) khác hợp đồng lập từ chính "
                f"văn bản ({can[:12]}…)"]
    return []


def doc(out_dir: Path, study: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """(hợp đồng, lỗi). Có tệp ⇒ đọc và kiểm. Không có tệp:
      • SAP mang dòng băm hợp đồng ⇒ lỗi «thiếu tệp hợp đồng»;
      • SAP KHÔNG mang dòng băm (SAP lập trước khi có hợp đồng — đã ký hoặc tệp thử) ⇒ hợp đồng suy từ chính văn bản
        SAP (nguồn `suy_tu_ban_ky`, khoá `tep_vang`), không lỗi;
      • không có SAP ⇒ (None, lỗi)."""
    out_dir = Path(out_dir)
    sap_p = out_dir / ten_sap(study)
    try:
        sap_text = sap_p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, [f"không có {ten_sap(study)} — chưa có SAP để lập hợp đồng"]
    p = out_dir / ten_tep(study)
    if p.is_file():
        try:
            hd = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            return None, [f"{ten_tep(study)} hỏng (không đọc được JSON)"]
        loi = kiem(out_dir, study, hd, sap_text)
        if isinstance(hd, dict) and not loi and hd.get("schema") in KHOA_THEO_SCHEMA:
            # v1/v2 hợp lệ: nội dung đầy đủ bản hiện hành suy từ CHÍNH văn bản SAP vừa khớp băm (không lập lại/ký lại)
            hd = {**hd, "noi_dung": rut_noi_dung(sap_text, out_dir), "nang_cap_tu": hd.get("schema")}
        return (hd if isinstance(hd, dict) else None), loi
    if bam_trong_sap(sap_text):
        return None, [f"thiếu {ten_tep(study)} dù chứng chỉ khoá SAP mang băm hợp đồng — lập lại bằng "
                      f"`python3 tools/hop_dong_sap.py ghi --study {study}`"]
    hd = lap(sap_text, study, out_dir, NGUON_SUY)
    hd["tep_vang"] = True
    return hd, []


def doc_hop_le(out_dir: Path, study: str) -> Optional[Dict[str, Any]]:
    """Hợp đồng nếu HỢP LỆ, ngược lại None (nơi tiêu thụ báo lỗi qua `doc`)."""
    hd, loi = doc(out_dir, study)
    return hd if hd is not None and not loi else None


def kiem_cho_khoa(out_dir: Path, study: str) -> List[str]:
    """Điều kiện KÝ G4: tệp hợp đồng nguồn `sinh_khi_dung`, hợp lệ, băm nằm trong chứng chỉ khoá (G4-AUTO-13)."""
    out_dir = Path(out_dir)
    p = out_dir / ten_tep(study)
    if not p.is_file():
        return [f"chưa có {ten_tep(study)} — chạy `python3 tools/hop_dong_sap.py ghi --study {study}` sau khi điền "
                "xong SAP (băm hợp đồng vào chứng chỉ khoá)"]
    hd, loi = doc(out_dir, study)
    if hd is not None and hd.get("nguon") != NGUON_SINH and not loi:
        loi = [f"{ten_tep(study)} khai «suy từ bản ký» — SAP chưa ký phải mang hợp đồng sinh khi dựng (băm trong "
               "chứng chỉ khoá)"]
    return loi


# ─────────────────────────── truy cập hợp đồng (không đọc lại chữ SAP) ───────────────────────────
def _muc_hd(hd: Optional[Dict[str, Any]], so: Any) -> Dict[str, Any]:
    nd = (hd or {}).get("noi_dung") if isinstance(hd, dict) else None
    muc = nd.get("muc") if isinstance(nd, dict) else None
    v = muc.get(str(so)) if isinstance(muc, dict) else None
    return v if isinstance(v, dict) else {}


def co_muc(hd: Optional[Dict[str, Any]], so: Any) -> bool:
    return bool(_muc_hd(hd, so))


def dong(hd: Optional[Dict[str, Any]], so: Any) -> List[str]:
    return [str(x) for x in _muc_hd(hd, so).get("dong") or []]


def nhan(hd: Optional[Dict[str, Any]], so: Any, ten: str) -> str:
    """Giá trị ĐÃ ĐIỀN sau «**<ten>:**» trong §so (bỏ chú thích điền sẵn; còn ô trống ⇒ "")."""
    return _gia_tri(_muc_hd(hd, so).get("nhan") or {}, ten)


def nhan_tho(hd: Optional[Dict[str, Any]], so: Any, ten: str) -> str:
    """Giá trị nguyên văn sau «**<ten>:**» (kể cả ô trống) — dùng khi cần biết ô còn trống."""
    return str((_muc_hd(hd, so).get("nhan") or {}).get(ten, ""))


def nhan_bat_dau(hd: Optional[Dict[str, Any]], so: Any, tien_to: str) -> str:
    return _gia_tri_bat_dau(_muc_hd(hd, so).get("nhan") or {}, tien_to)


def gach(hd: Optional[Dict[str, Any]], so: Any) -> List[str]:
    """Các gạch đầu dòng cấp 1 ĐÃ ĐIỀN của §so."""
    return [d[2:].strip() for d in dong(hd, so) if d.startswith("- ") and co_noi_dung(d[2:])]


def cac_nhan(hd: Optional[Dict[str, Any]], so: Any) -> List[Tuple[str, str]]:
    """(nhãn, giá trị nguyên văn) của các gạch «- **Nhãn:** giá trị» ở §so, theo thứ tự."""
    ra = []
    for d in dong(hd, so):
        m = _NHAN_GACH_RE.match(d)
        if m:
            ra.append((m.group(1).strip(), m.group(2)))
    return ra


def bang(hd: Optional[Dict[str, Any]]) -> List[str]:
    """Tên các bảng khung của SAP §11 («**Bảng …:**»)."""
    return [re.sub(r"^\*\*|\*\*:?$|:$", "", d.strip()).strip(" *:") for d in dong(hd, 11)
            if d.strip().startswith("**Bảng")]


def van_ban_muc(hd: Optional[Dict[str, Any]]) -> str:
    """Mọi dòng của mọi § trong hợp đồng — dùng để TRUY NGUYÊN cụm neo của đặc tả G6 (không để đọc tham số)."""
    nd = (hd or {}).get("noi_dung") if isinstance(hd, dict) else None
    muc = nd.get("muc") if isinstance(nd, dict) else {}
    return "\n".join(str(x) for so in sorted(muc, key=lambda s: int(s) if str(s).isdigit() else 99)
                     for x in (muc[so].get("dong") or []))


def chu_muc_bo_dau(hd: Optional[Dict[str, Any]], so: Any) -> str:
    """Tiêu đề + các dòng của §so trong hợp đồng, đã bỏ dấu và hạ chữ — để hỏi «§so có NHẮC tên x không» (vd biến nhóm
    con của script có nằm trong §7). Không có hợp đồng/mục ⇒ ""."""
    m = _muc_hd(hd, so)
    if not m:
        return ""
    return bo_dau(f"### §{so} {m.get('tieu_de') or ''}\n" + "\n".join(str(x) for x in m.get("dong") or []))


def dong_gach_co(hd: Optional[Dict[str, Any]], cac_muc: Sequence[int], mau: str) -> str:
    """Gạch đầu dòng đầu tiên (đã điền) của các § trong hợp đồng chứa mẫu `mau` — bỏ định dạng đậm (bộ đọc
    quyet_dinh_da_chot._dong_sap_co trước đây)."""
    for so in cac_muc:
        for d in dong(hd, so):
            t = d.strip()
            if t.startswith("- ") and re.search(mau, t, re.I) and co_noi_dung(t[2:]):
                return re.sub(r"\*\*", "", t[2:]).strip().rstrip(" ")
    return ""


def truong(hd: Optional[Dict[str, Any]], *khoa: str) -> Any:
    """Giá trị lồng của nội dung hợp đồng: truong(hd, "phan_tich_chinh", "ho_mo_hinh")."""
    v: Any = (hd or {}).get("noi_dung") if isinstance(hd, dict) else None
    for k in khoa:
        v = v.get(k) if isinstance(v, dict) else None
    return v


def _ha_chu_dau(x: str) -> str:
    """Hạ chữ đầu để nối giữa câu — trừ chữ viết tắt («ĐN2», «MI», «MT3»: chữ thứ hai cũng hoa)."""
    return x if len(x) > 1 and x[1].isupper() else x[:1].lower() + x[1:]


def tom_tat_g7(hd: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Điều đã KHOÁ ở SAP mà bản thảo G7 cần — từ hợp đồng (trước đây run_g7_auto._sap_tom_tat dò chữ SAP)."""
    if not isinstance(hd, dict):
        return {}
    ra: Dict[str, Any] = {}
    nhay = [_sach(x["mo_ta"]) for x in truong(hd, "do_nhay") or [] if isinstance(x, dict)]
    if nhay and not any("[CẦN" in x.upper() for x in nhay):
        ra["do_nhay"] = "; ".join(_ha_chu_dau(x) for x in nhay)
    for khoa, so, ten in (("phan_mem", 10, "Phần mềm"), ("du_lieu_thieu", 6, "Chiến lược"),
                          ("bao_hoa", 6, "Tiêu chí bão hòa"), ("gia_dinh_mo_hinh", 5, "Giả định"),
                          ("giua_ky", 13, "Có phân tích giữa kỳ"), ("danh_gia_ton_hai", 15, "Cách đánh giá"),
                          ("phan_tich_ton_hai", 15, "Cách phân tích tổn hại"),
                          ("tuan_thu", 15, "Chiến lược cải thiện và theo dõi tuân thủ"),
                          ("hieu_chinh_cum", 4, "Hiệu chỉnh cụm"), ("phuong_phap_chinh", 4, "Phương pháp"),
                          ("mo_hinh_gop", 5, "Mô hình gộp")):
        v = nhan_tho(hd, so, ten)
        if v and "[CẦN" not in v.upper():
            ra[khoa] = _sach(v)
    for khoa, so, tien_to in (("quy_tac_dung", 13, "Quy tắc dừng"), ("ton_hai", 15, "Định nghĩa tổn hại")):
        k = next((x for x in (_muc_hd(hd, so).get("nhan") or {}) if x.startswith(tien_to)), None)
        v = nhan_tho(hd, so, k) if k else ""
        if v and "[CẦN" not in v.upper():
            ra[khoa] = _sach(v)
    tc = [(k, _sach(v)) for k, v in cac_nhan(hd, 9) if k in NHAN_TIN_CAY]
    tc = [(k, v) for k, v in tc if v and "[CẦN" not in v.upper()]
    if tc:
        ra["tin_cay"] = "; ".join(f"{k}: {v[:1].lower() + v[1:]}" for k, v in tc)
    gt = truong(hd, "gia_thuyet") or {}
    if isinstance(gt.get("alpha"), (int, float)):
        ra["alpha"] = gt["alpha"]
        if gt.get("so_phia") in (1, 2):
            ra["alpha_phia"] = "một phía" if gt["so_phia"] == 1 else "hai phía"
    if gt.get("khung"):
        ra["loai_gia_thuyet"] = gt["khung"]
    bien = nhan_tho(hd, 5, "Biến độc lập đưa vào")
    if bien and "[CẦN" not in bien.upper() and not re.match(r"\s*Không áp dụng", bien, re.IGNORECASE):
        ra["bien_da_bien"] = _sach(bien)
    lt = next((re.match(r"^-\s*Biến liên tục:\s*(.+)$", d) for d in dong(hd, 3)
               if re.match(r"^-\s*Biến liên tục:\s*(.+)$", d)), None)
    if lt and "[CẦN" not in lt.group(1).upper():
        ra["bien_lien_tuc"] = _sach(lt.group(1))
    return ra


# ─────────────────────────── lệnh ───────────────────────────
def _da_ky(study: str, sap_p: Path) -> bool:
    """SAP hiện tại đã có bản ghi phê duyệt G4 (xác minh được, hoặc dấu vết APPROVED trùng nội dung — bảo toàn)."""
    try:
        import dau_may_sinh as DMS  # noqa: PLC0415
        import gate_contract as GC  # noqa: PLC0415
    except ImportError:  # pragma: no cover - lưới an toàn
        return False
    return bool(GC.ledger_approved("G4", study, sap_p, repo_root=BASE)
                or DMS.so_cai_co_duyet_trung_noi_dung(sap_p.parent / "approval_ledger.json", "G4", sap_p))


def _la_de_tai_tong_hop(out_dir: Path) -> bool:
    """study_meta.json khai study_kind = synthetic_test (đề tài tổng hợp — giả lập, kiểm thử)."""
    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return False
    return isinstance(meta, dict) and str(meta.get("study_kind") or "").strip() == "synthetic_test"


def ghi(study: str, out_dir: Optional[Path] = None, suy_tu_ban_ky: bool = False) -> Tuple[int, str]:
    """Lập/làm mới hợp đồng. (mã, thông điệp): 0 xong · 1 từ chối · 3 tham số sai."""
    out_dir = Path(out_dir) if out_dir else BASE / "exports" / study
    sap_p = out_dir / ten_sap(study)
    try:
        sap_text = sap_p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 3, f"không có {sap_p}"
    if suy_tu_ban_ky or _da_ky(study, sap_p):
        if bam_trong_sap(sap_text):
            return 1, ("SAP đã mang băm hợp đồng trong chứng chỉ khoá — hợp đồng của nó là bản sinh khi dựng; không "
                       "lập bản «suy từ bản ký»")
        hd = lap(sap_text, study, out_dir, NGUON_SUY)
        p = luu(out_dir, study, hd)
        return 0, f"đã lập {p.name} (suy từ bản ký — SAP giữ nguyên từng byte), sha256 {hd['sha256_hop_dong']}"
    # Chỉ SỬA SAP (ghi băm vào chứng chỉ) khi máy BIẾT CHẮC SAP chưa ký: có sổ cái phê duyệt của đề tài (không có bản
    # ghi G4 trùng nội dung — đã xét ở trên), hoặc đề tài tổng hợp (study_kind = synthetic_test). Máy không có sổ cái
    # (worktree, máy khác) ⇒ TỪ CHỐI: không bao giờ đụng SAP có thể đã ký (đo 23/11/2026: BTM không nằm trong danh sách
    # đề tài thật bị chặn nên rào theo danh sách tên không đủ).
    if not (out_dir / "approval_ledger.json").is_file() and not _la_de_tai_tong_hop(out_dir):
        return 1, ("máy này không có sổ cái phê duyệt của đề tài — không biết SAP đã ký chưa nên KHÔNG sửa SAP; chạy "
                   "trên máy có sổ cái, hoặc --suy-tu-ban-ky nếu SAP đã ký")
    moi, hd = gan_vao_sap(sap_text, study, out_dir)
    if moi is None:
        return 1, "SAP không có chứng chỉ khoá (PHẦN 5 có khung ╚…╝) để ghi băm hợp đồng — sai khuôn G4"
    if moi != sap_text:
        sap_p.write_text(moi, encoding="utf-8", newline="\n")
    p = luu(out_dir, study, hd)
    return 0, f"đã lập {p.name} và ghi băm vào chứng chỉ khoá SAP, sha256 {hd['sha256_hop_dong']}"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hợp đồng SAP máy đọc (G4_SAP_CONTRACT_<mã>.json)")
    sub = ap.add_subparsers(dest="lenh", required=True)
    g = sub.add_parser("ghi", help="lập/làm mới hợp đồng (+ băm vào chứng chỉ khoá SAP chưa ký)")
    g.add_argument("--study", required=True)
    g.add_argument("--suy-tu-ban-ky", action="store_true", help="SAP đã ký trước khi có hợp đồng: chỉ lập tệp")
    k = sub.add_parser("kiem", help="kiểm hợp đồng ↔ SAP hiện tại")
    k.add_argument("--study", required=True)
    k.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.lenh == "ghi":
        ma, tb = ghi(a.study, suy_tu_ban_ky=a.suy_tu_ban_ky)
        print(("✓ " if ma == 0 else "⛔ ") + tb)
        return ma
    hd, loi = doc(BASE / "exports" / a.study, a.study)
    if a.json:
        print(json.dumps({"hop_le": hd is not None and not loi, "loi": loi,
                          "nguon": (hd or {}).get("nguon"), "tep_vang": bool((hd or {}).get("tep_vang")),
                          "sha256_hop_dong": (hd or {}).get("sha256_hop_dong")}, ensure_ascii=False, indent=2))
    else:
        for x in loi:
            print(f"⛔ {x}")
        if hd is not None and not loi:
            print(f"✓ hợp đồng hợp lệ ({hd.get('nguon')}{', suy tại chỗ' if hd.get('tep_vang') else ''}) — sha256 "
                  f"{hd.get('sha256_hop_dong')}")
    return 0 if hd is not None and not loi else 1


if __name__ == "__main__":
    sys.exit(main())
