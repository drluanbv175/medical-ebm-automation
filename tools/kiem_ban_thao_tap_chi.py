#!/usr/bin/env python3
"""Kiểm bản thảo gửi tạp chí theo thể lệ — đo bằng máy, lặp lại được.

Vì sao (19/11/2026): gói nộp Tạp chí Y Dược Thực hành 175 của đề tài BTM do agent soạn có bảng kiểm đếm tay; số trang
ghi «chưa đo được bằng máy». Đo bằng Word thật thì bản thảo 15 trang trong khi thể lệ cho tối đa 10 trang kể cả tài liệu
tham khảo. Cùng lượt rà còn lộ: từ khoá phân cách bằng dấu chấm phẩy (thể lệ: dấu phẩy), nhãn «BẢN NHÁP AI» và ghi chú
cho tác giả nằm ngay trong bản thảo (bác sĩ 17/11/2026: văn bản người đọc không mang dấu vết máy).

Dùng:
    python3 tools/kiem_ban_thao_tap_chi.py <bản thảo .md> --tap-chi "Tạp chí Y Dược Thực hành 175"
        [--docx <bản .docx>] [--dem-trang] [--nop] [--json]

Đo: tổng số từ, tiêu đề, tóm tắt tiếng Việt và tiếng Anh, từ khoá (số lượng, dấu phân cách), số tài liệu tham khảo,
số bảng, số hình, kiểu trích dẫn gộp «[4, 5]», trích dẫn đặt ở Kết quả/Kết luận/Khuyến nghị, dấu vết soạn thảo/máy
(luật K8 dùng chung với đề cương nộp Hội đồng), ô «[CẦN…]» còn chờ điền.
Số trang chỉ đo khi có `--dem-trang` + `--docx` trên macOS có Microsoft Word; không đo được thì ghi «chưa đo» — KHÔNG
BAO GIỜ tính là đạt.

`--nop`: bản sắp nộp — ô «[CẦN…]» còn lại tính là vi phạm (khi chưa có số liệu thì bỏ cờ này).

K18 (22/11/2026, bác sĩ: mọi khâu tới «Viết báo cáo & công bố kết quả» phải đạt TỪNG MỤC chuẩn quốc tế và Việt Nam, cho
mọi thiết kế; không đạt thì loại bỏ): đối chiếu bản thảo với từng mục chuẩn báo cáo theo thiết kế (STROBE/RECORD/CROSS,
CONSORT 2025, STARD, TRIPOD+AI…, chuẩn Việt Nam) bằng `kiem_chuan_de_cuong_theo_muc.doi_chieu(che_do="ban_thao")` —
chi tiết ở `tieu_chi_ban_thao.py`. Mục thiếu ⇒ vi phạm. Bản thảo CHƯA CÓ SỐ LIỆU (còn ô [CẦN…], không `--nop`): chỉ chấm
mục phương pháp và cấu trúc; mục kết quả/bàn luận báo «chưa đo được» (ghi chú) — KHÔNG BAO GIỜ là đạt. BÀI BÁO GIAO THỨC
(tên tệp/tiêu đề có «giao thức», hoặc `--giao-thuc`) dùng tiêu chí ĐỀ CƯƠNG của K17, theo chương IMRAD. Thiết kế lấy
từ `study_meta.json` (gate_params.G1.design) ở thư mục đề tài chứa bản thảo, hoặc `--thiet-ke`; không xác định được ⇒
ghi chú «chưa đo», riêng `--nop` là vi phạm.

Mã thoát: 0 mọi giới hạn đo được đều đạt · 1 có vi phạm · 2 không đọc được tệp hoặc tạp chí chưa khai giới hạn.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import uuid
from pathlib import Path
from typing import Dict, List, Optional

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402
import md2docx_vn as M2D  # noqa: E402
import tieu_chi_ban_thao as TCB  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Giới hạn theo khoá hồ sơ định dạng của md2docx_vn (một nguồn tên tạp chí cho cả định dạng lẫn giới hạn).
GIOI_HAN: Dict[str, Dict] = {
    "tap_chi_y_duoc_thuc_hanh_175": {
        "nguon": "Thể lệ viết bài, Tạp chí Y Dược Thực hành 175 — jpmp175.vn/yduocthuchanh175/guideline-for-"
                 "contributors, đọc 19/11/2026 (bài nghiên cứu gốc)",
        "so_tu": 5000, "so_trang": 10, "tltk": 20, "bang": 5, "hinh": 5, "tom_tat": 250, "tu_khoa": 6,
        "tieu_de": 30, "phan_cach_tu_khoa": ",",
        "khong_trich_dan_o": ("KẾT QUẢ", "KẾT LUẬN", "KHUYẾN NGHỊ", "KIẾN NGHỊ"),
    },
}

_CAN_RE = re.compile(r"\[CẦN[^\]]*\]")
_DE_MUC_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
_TRICH_GOP_RE = re.compile(r"\[\d+\s*(?:[,;–-]\s*\d+)+\]")
_TRICH_RE = re.compile(r"\[\d+(?:,\s*\d+)?\]")
#: một mục của danh mục TLTK: «[1] …» (Vancouver ngoặc vuông), «1. …» (danh sách đánh số), «- [V1] …» (văn bản pháp quy)
_MUC_TLTK_RE = re.compile(r"(?m)^[ \t]*(?:[-*][ \t]+)?(?:\[[A-Za-zĐđ]{0,3}\d+\]|\d+\.)[ \t]")
_TLTK_DE_MUC_RE = re.compile(r"(?m)^#{1,6}\s+(?:\d+\.\s*)?(?:TÀI LIỆU THAM KHẢO|REFERENCES)\b")


def _cap_chuong(md: str) -> int:
    """Cấp đề mục của CHƯƠNG (TÓM TẮT, ĐẶT VẤN ĐỀ, … TÀI LIỆU THAM KHẢO), xác định đúng như K18
    (`tieu_chi_ban_thao.tach_ban_thao`): cấp có nhiều chương IMRAD lõi khác nhau nhất. 0 = không nhận ra chương nào.

    Vì sao (22/11/2026): bản cũ của `_muc` chỉ tách đề mục `##`; bài báo giao thức C1a dùng `#` cho chương
    («# TÓM TẮT», «# 1. ĐẶT VẤN ĐỀ», «# TÀI LIỆU THAM KHẢO») nên bị báo «Thiếu mục TÓM TẮT/ABSTRACT» và đếm TLTK = 0."""
    return TCB.tach_ban_thao(md, nghiem=False).cap_chuong


def _muc(md: str) -> Dict[str, str]:
    """Tách văn bản theo đề mục cấp CHƯƠNG (`_cap_chuong`; không nhận ra chương ⇒ `##` như trước) — khoá là đề mục viết
    hoa, bỏ số thứ tự đầu. Một chương kéo tới đề mục kế tiếp cùng cấp hoặc cấp trên."""
    cap = _cap_chuong(md) or 2
    ra: Dict[str, str] = {}
    vi_tri = [(m.start(), m.end(), len(m.group(1)), m.group(2)) for m in _DE_MUC_RE.finditer(md)]
    for i, (_bd, kt, c, ten) in enumerate(vi_tri):
        if c != cap:
            continue
        ket = next((v[0] for v in vi_tri[i + 1:] if v[2] <= cap), len(md))
        khoa = re.sub(r"^\d+\.\s*", "", ten).strip().upper()
        ra[khoa] = md[kt:ket]
    return ra


def _tieu_de(md: str) -> str:
    """Tên bài: đề mục đầu tiên đứng TRƯỚC chương đầu tiên mà khác cấp chương (bài báo giao thức C1a: «# GIAO THỨC
    NGHIÊN CỨU» là nhãn loại bài ở cấp chương, tên bài là «## Đánh giá … giao thức nghiên cứu cắt ngang có phân
    tích»). Không nhận ra chương ⇒ đề mục `#` đầu tiên như trước."""
    cap = _cap_chuong(md)
    de_muc = [(len(m.group(1)), m.group(2)) for m in _DE_MUC_RE.finditer(md)]
    if not cap:
        return next((t for c, t in de_muc if c == 1), "")
    truoc: List[tuple] = []
    for c, ten in de_muc:
        if c == cap and TCB.khoa_imrad(ten):
            break
        truoc.append((c, ten))
    return next((t for c, t in truoc if c != cap), truoc[0][1] if truoc else "")


def dem_tu(text: str) -> int:
    """Đếm từ gần với Word: bỏ ký hiệu Markdown và dòng kẻ bảng, mỗi cụm cách nhau bằng khoảng trắng là một từ."""
    dong = [d for d in text.splitlines() if not re.match(r"^\s*\|?\s*:?-{3,}", d)]
    sach = re.sub(r"[#*|`>]", " ", "\n".join(dong))
    return len([w for w in sach.split() if re.search(r"\w", w)])


def _tom_tat(phan: str) -> str:
    return "\n".join(d for d in phan.splitlines()
                     if not re.match(r"\s*\*\*(?:Từ khoá|Từ khóa|Keywords?)\s*:", d, re.IGNORECASE))


def _tu_khoa(phan: str) -> Optional[str]:
    m = re.search(r"(?m)^\s*\*\*(?:Từ khoá|Từ khóa|Keywords?)\s*:\*\*\s*(.+)$", phan, re.IGNORECASE)
    return m.group(1).strip().rstrip(".") if m else None


def do_ban_thao(md: str, gh: Dict) -> Dict:
    """Đo mọi chỉ số đọc được từ Markdown; trả dict có danh sách vi phạm và ghi chú."""
    muc = _muc(md)
    vi_pham: List[str] = []
    ghi_chu: List[str] = []
    so: Dict[str, object] = {}

    tieu_de = _tieu_de(md)
    so["tieu_de"] = dem_tu(tieu_de)
    if so["tieu_de"] > gh["tieu_de"]:
        vi_pham.append(f"Tiêu đề {so['tieu_de']} từ > {gh['tieu_de']}")
    if tieu_de and tieu_de != tieu_de.upper():
        vi_pham.append("Tiêu đề chưa in hoa")

    for khoa, nhan in (("TÓM TẮT", "tom_tat_vi"), ("ABSTRACT", "tom_tat_en")):
        phan = muc.get(khoa)
        if phan is None:
            vi_pham.append(f"Thiếu mục {khoa}")
            continue
        so[nhan] = dem_tu(_CAN_RE.sub("X", _tom_tat(phan)))
        if so[nhan] > gh["tom_tat"]:
            vi_pham.append(f"{khoa} {so[nhan]} từ > {gh['tom_tat']}")
        tk = _tu_khoa(phan)
        if tk is None:
            vi_pham.append(f"{khoa}: thiếu dòng từ khoá")
            continue
        if gh["phan_cach_tu_khoa"] == "," and ";" in tk:
            vi_pham.append(f"{khoa}: từ khoá phân cách bằng dấu chấm phẩy — thể lệ yêu cầu dấu phẩy")
        n_tk = len([x for x in re.split(r"[;,]", tk) if x.strip()])
        so[nhan + "_tu_khoa"] = n_tk
        if n_tk > gh["tu_khoa"]:
            vi_pham.append(f"{khoa}: {n_tk} từ khoá > {gh['tu_khoa']}")

    tltk = next((v for k, v in muc.items() if k.startswith("TÀI LIỆU THAM KHẢO") or k == "REFERENCES"), "")
    so["tltk"] = len(_MUC_TLTK_RE.findall(tltk))
    if so["tltk"] > gh["tltk"]:
        vi_pham.append(f"{so['tltk']} tài liệu tham khảo > {gh['tltk']}")
    so["bang"] = len(re.findall(r"(?m)^\*\*Bảng\s+\d+\.", md))
    so["hinh"] = len(re.findall(r"(?m)^\*\*(?:Hình|Biểu đồ)\s+\d+\.", md))
    for khoa in ("bang", "hinh"):
        if so[khoa] > gh[khoa]:
            vi_pham.append(f"{so[khoa]} {'bảng' if khoa == 'bang' else 'hình'} > {gh[khoa]}")

    than = _TLTK_DE_MUC_RE.split(md, maxsplit=1)[0]
    gop = sorted(set(_TRICH_GOP_RE.findall(than)))
    if gop:
        vi_pham.append(f"Trích dẫn gộp trong một ngoặc ({', '.join(gop[:5])}) — thể lệ: mỗi số một ngoặc «[4],[5]»")
    for khoa, phan in muc.items():
        if any(khoa.startswith(c) for c in gh["khong_trich_dan_o"]):
            co = _TRICH_RE.findall(_CAN_RE.sub("", phan))
            if co:
                vi_pham.append(f"Có trích dẫn ở mục {khoa} ({', '.join(co[:3])}) — thể lệ không đặt trích dẫn ở đây")

    khong_o = _CAN_RE.sub("", md)
    k8 = K.loi_k8(khong_o)
    if k8:
        vi_pham.extend(k8)
    # K10 (bác sĩ 20/11/2026): số liệu ở đặt vấn đề/bàn luận phải tự mang trích dẫn — ô [CẦN…] chờ kết quả thật đã bỏ.
    vi_pham.extend(K.loi_k10(khong_o))
    # K11 (bác sĩ 20/11/2026): chuẩn trình bày tiếng Việt — số, ngày, ngoặc kép, chữ viết tắt… như đề cương nộp.
    vi_pham.extend(K.loi_k11(khong_o))
    # K15 (21/11/2026): khẳng định mơ hồ không nguồn ở đặt vấn đề/bàn luận (K16 phạm vi tìm chạy ở `kiem`).
    vi_pham.extend(K.loi_k15(khong_o))
    so["o_can"] = len(_CAN_RE.findall(md))
    so["so_tu"] = dem_tu(md)
    if so["so_tu"] > gh["so_tu"]:
        vi_pham.append(f"Tổng {so['so_tu']} từ > {gh['so_tu']} (ước theo Markdown; đo lại bằng Word)")
    if so["o_can"]:
        ghi_chu.append(f"Còn {so['o_can']} ô [CẦN…] chờ điền")
    return {"so_do": so, "vi_pham": vi_pham, "ghi_chu": ghi_chu}


_GIAO_THUC_RE = re.compile(r"giao[-_ ]?th[uứ]c|study[-_ ]?protocol|protocol[-_ ]?(article|paper)", re.IGNORECASE)


def la_bai_giao_thuc(md_path: Path, md: str) -> bool:
    """Bài báo GIAO THỨC (công bố đề cương trước khi có số liệu): tên tệp hoặc đề mục trong 40 dòng đầu nói «giao thức
    nghiên cứu»/«study protocol» (vd `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md`)."""
    if _GIAO_THUC_RE.search(unicodedata.normalize("NFC", md_path.name)):
        return True
    dau = "\n".join(unicodedata.normalize("NFC", md).splitlines()[:40])
    return bool(re.search(r"(?m)^#{1,3}\s+.*(giao thức nghiên cứu|study protocol)", dau, re.IGNORECASE))


def thiet_ke_cua(md_path: Path) -> str:
    """Mã thiết kế G1 của đề tài chứa bản thảo: tìm `study_meta.json` ở thư mục bản thảo và tối đa 3 thư mục cha
    (`exports/<mã>/tap_chi/<tạp chí>/BAN_THAO_….md`)."""
    for d in [md_path.parent, *list(md_path.parent.parents)[:3]]:
        p = d / "study_meta.json"
        if p.is_file():
            try:
                meta = json.loads(p.read_text(encoding="utf-8"))
                return str(((meta.get("gate_params") or {}).get("G1") or {}).get("design") or "").strip()
            except (OSError, ValueError, AttributeError):
                return ""
    return ""


def k18(md: str, thiet_ke: str, nop: bool = False, giao_thuc: bool = False) -> Dict:
    """K18 — chuẩn báo cáo theo mục. {'vi_pham', 'ghi_chu', 'tom_tat': {chuẩn: {trạng thái: số}}, 'co_so_lieu'}."""
    ra: Dict = {"vi_pham": [], "ghi_chu": [], "tom_tat": {}, "co_so_lieu": None}
    if not KCM.S.canonical_design_code(thiet_ke or ""):
        thong_bao = ("K18: không xác định được thiết kế (gate_params.G1.design của đề tài hoặc --thiet-ke) — chưa đối "
                     "chiếu chuẩn báo cáo theo mục, KHÔNG tính là đạt")
        (ra["vi_pham"] if nop else ra["ghi_chu"]).append(thong_bao)
        return ra
    if giao_thuc:
        kq = KCM.doi_chieu(md, thiet_ke, che_do="giao_thuc", co_so_lieu=nop)
        nhan = "K18 (bài báo giao thức · tiêu chí K17)"
    else:
        kq = KCM.doi_chieu(md, thiet_ke, che_do="ban_thao", co_so_lieu=True if nop else None)
        nhan = "K18"
    ra["co_so_lieu"] = kq.get("co_so_lieu")
    ra["vi_pham"] += [f"{nhan} cấu trúc: {x}" for x in kq.get("cau_truc") or []]
    chua_do: List[str] = []
    for r in kq["ket_qua"]:
        ra["tom_tat"].setdefault(r.chuan, {}).setdefault(r.trang_thai, 0)
        ra["tom_tat"][r.chuan][r.trang_thai] += 1
        if r.trang_thai == "thieu":
            ra["vi_pham"].append(f"{nhan} {r.chuan} mục {r.ma} ({r.chu_de}) thiếu: {'; '.join(r.thieu)} — {r.tieu_chi}")
        elif r.trang_thai == "canh_bao":
            ra["ghi_chu"].append(f"{nhan} {r.chuan} mục {r.ma} ({r.chu_de}) — cảnh báo, không chặn ({r.ly_do}): "
                                 f"{'; '.join(r.thieu)}")
        elif r.trang_thai == "chua_do":
            chua_do.append(f"{r.chuan} {r.ma}")
    if chua_do:
        ra["ghi_chu"].append(f"{nhan}: {len(chua_do)} mục CHƯA ĐO ĐƯỢC — không tính là đạt "
                             + ("(bản thảo chưa có số liệu: phần kết quả/bàn luận, dữ kiện chờ điền; đo lại bằng --nop "
                                "khi đã điền) " if not kq.get("co_so_lieu") else "")
                             + f"[{', '.join(chua_do)}]")
    for c, ly in kq.get("chua_do") or []:
        ra["ghi_chu"].append(f"{nhan}: {c} — {ly}")
    return ra


def dem_trang_word(docx: Path) -> Optional[Dict[str, int]]:
    """Số trang + số từ do Microsoft Word dàn trang thật. Không có Word/macOS hoặc lỗi ⇒ None (chưa đo)."""
    if sys.platform != "darwin" or not Path("/Applications/Microsoft Word.app").exists() or not shutil.which(
            "osascript"):
        return None
    hop = Path.home() / "Library/Containers/com.microsoft.Word/Data/Documents/ebm-do-trang"
    try:
        hop.mkdir(parents=True, exist_ok=True)
        tam = hop / f"do-{uuid.uuid4().hex}.docx"
        shutil.copyfile(docx, tam)
    except OSError:
        return None
    lenh = (f'tell application "Microsoft Word"\nopen (POSIX file "{tam}")\nset d to active document\n'
            'set p to (compute statistics d statistic statistic pages)\n'
            'set w to (compute statistics d statistic statistic words)\nclose d saving no\n'
            'return (p as string) & " " & (w as string)\nend tell')
    try:
        kq = subprocess.run(["osascript", "-e", lenh], capture_output=True, text=True, timeout=180)
        so = [int(x) for x in kq.stdout.split()]
        return {"trang": so[0], "tu_word": so[1]} if kq.returncode == 0 and len(so) == 2 else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    finally:
        tam.unlink(missing_ok=True)


def kiem(md_path: Path, tap_chi: str, docx: Optional[Path] = None, dem_trang: bool = False,
         nop: bool = False, thiet_ke: Optional[str] = None, giao_thuc: Optional[bool] = None) -> Dict:
    hs = M2D.resolve_journal_profile(tap_chi)
    gh = GIOI_HAN.get((hs or {}).get("key", ""))
    if gh is None:
        return {"ma": 2, "loi": f"Tạp chí «{tap_chi}» chưa khai giới hạn trong GIOI_HAN"}
    try:
        md = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return {"ma": 2, "loi": f"Không đọc được {md_path}: {e}"}
    kq = do_ban_thao(md, gh)
    # K16 (21/11/2026): phạm vi tìm nêu trong bản thảo phải khớp nhật ký PRISMA-S của đề tài (cùng thư mục).
    kq["vi_pham"].extend(K.loi_k16(md_path.parent, md))
    # K18 (22/11/2026): chuẩn báo cáo theo từng mục, theo thiết kế
    tk = thiet_ke if thiet_ke else thiet_ke_cua(md_path)
    gt = la_bai_giao_thuc(md_path, md) if giao_thuc is None else giao_thuc
    k = k18(md, tk, nop=nop, giao_thuc=gt)
    kq["vi_pham"].extend(k["vi_pham"])
    kq["ghi_chu"].extend(k["ghi_chu"])
    kq["k18"] = {"thiet_ke": tk, "giao_thuc": gt, "tom_tat": k["tom_tat"], "co_so_lieu": k["co_so_lieu"]}
    kq["nguon_gioi_han"] = gh["nguon"]
    trang = dem_trang_word(docx) if (dem_trang and docx) else None
    kq["so_do"]["trang"] = trang["trang"] if trang else None
    kq["so_do"]["tu_word"] = trang["tu_word"] if trang else None
    if trang is None:
        kq["ghi_chu"].append(f"Số trang: chưa đo (giới hạn {gh['so_trang']} trang) — cần --docx --dem-trang trên máy "
                             "có Microsoft Word")
    else:
        if trang["trang"] > gh["so_trang"]:
            kq["vi_pham"].append(f"{trang['trang']} trang > {gh['so_trang']} (Word dàn trang thật)")
        if trang["tu_word"] > gh["so_tu"]:
            kq["vi_pham"].append(f"Word đếm {trang['tu_word']} từ > {gh['so_tu']}")
    if nop and kq["so_do"]["o_can"]:
        kq["vi_pham"].append(f"Bản nộp còn {kq['so_do']['o_can']} ô [CẦN…]")
    kq["ma"] = 1 if kq["vi_pham"] else 0
    return kq


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm bản thảo gửi tạp chí theo thể lệ (đo bằng máy).")
    ap.add_argument("ban_thao", type=Path)
    ap.add_argument("--tap-chi", required=True)
    ap.add_argument("--docx", type=Path)
    ap.add_argument("--dem-trang", action="store_true", help="Đếm trang bằng Microsoft Word (macOS)")
    ap.add_argument("--nop", action="store_true", help="Bản sắp nộp: ô [CẦN…] còn lại là vi phạm")
    ap.add_argument("--thiet-ke", help="K18: mã thiết kế (mặc định: gate_params.G1.design của đề tài)")
    ap.add_argument("--giao-thuc", action="store_true", default=None,
                    help="K18: bài báo giao thức — tiêu chí đề cương (mặc định: tự nhận theo tên tệp/tiêu đề)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    kq = kiem(a.ban_thao, a.tap_chi, a.docx, a.dem_trang, a.nop, a.thiet_ke, a.giao_thuc)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
        return kq["ma"]
    if kq["ma"] == 2:
        print(f"⚪ {kq['loi']}")
        return 2
    s = kq["so_do"]
    print(f"Bản thảo: {a.ban_thao.name} — giới hạn theo {kq['nguon_gioi_han']}")
    print(f"  Từ (ước Markdown): {s['so_tu']} · Word: {s['tu_word'] if s['tu_word'] is not None else 'chưa đo'}")
    print(f"  Trang (Word): {s['trang'] if s['trang'] is not None else 'chưa đo'}")
    print(f"  Tiêu đề: {s['tieu_de']} từ · Tóm tắt: {s.get('tom_tat_vi', '—')} / {s.get('tom_tat_en', '—')} từ")
    print(f"  TLTK: {s['tltk']} · Bảng: {s['bang']} · Hình: {s['hinh']} · Ô [CẦN…]: {s['o_can']}")
    k = kq.get("k18") or {}
    if k.get("tom_tat"):
        loai = "bài báo giao thức (tiêu chí đề cương)" if k.get("giao_thuc") else "bản thảo"
        print(f"  K18 chuẩn theo mục — {loai}, thiết kế {k.get('thiet_ke')}:")
        for c, dem in k["tom_tat"].items():
            print(f"    {c}: " + " · ".join(f"{t} {n}" for t, n in sorted(dem.items())))
    for x in kq["vi_pham"]:
        print(f"  ✗ {x}")
    for x in kq["ghi_chu"]:
        print(f"  · {x}")
    print("ĐẠT mọi giới hạn đo được." if kq["ma"] == 0 else "CÒN VI PHẠM.")
    return kq["ma"]


if __name__ == "__main__":
    sys.exit(main())
