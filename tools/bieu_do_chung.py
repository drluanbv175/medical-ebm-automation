#!/usr/bin/env python3
"""Nền TRÌNH BÀY chung cho mọi biểu đồ kết quả nghiên cứu (bác sĩ 21/11/2026: «phải thực hiện được tất cả biểu đồ một
cách chi tiết và chính xác nhất»; «tất cả vấn đề trong hệ thống nghiên cứu y khoa phải đạt sự toàn diện, tự động tốt
nhất»).

Một chỗ duy nhất cho các quy ước mà mọi họ biểu đồ (`bieu_do_gop.py` và các họ sau) phải theo:
  - phông có chân (Times New Roman → DejaVu Serif), cỡ 9–10, bỏ viền trên/phải, không 3D, không bóng;
  - số theo NGÔN NGỮ TÀI LIỆU: `vi` dùng dấu phẩy thập phân và dấu trừ «−» (K11 của đề cương/bản thảo tiếng Việt),
    `en` dùng dấu chấm (bản thảo nộp tạp chí quốc tế) — áp cho CẢ nhãn trục lẫn chữ chú thích trong hình;
  - xuất PNG 300 dpi (chèn Word) + PDF vector (tạp chí đòi hình vector), siêu dữ liệu tối thiểu để tệp tái lập được;
  - mỗi lần vẽ trả một từ điển SỐ LIỆU đã dùng (ghi kèm JSON cạnh hình) — chữ trong bài/bảng phải lấy đúng các số này,
    không tính lại ở chỗ khác;
  - kiểm chéo bằng R (Rscript --vanilla qua `cau_noi_r`): không có R ⇒ trạng thái «không kiểm chéo được», KHÔNG bao giờ
    báo là khớp.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import tempfile
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

DPI = 300
NGON_NGU = ("vi", "en")
TRU = "−"  # dấu trừ toán học, không dùng gạch nối

# Nhãn chuẩn hai ngôn ngữ — một chỗ để mọi họ biểu đồ dùng chung, không gõ rải rác.
NHAN: Dict[str, Dict[str, str]] = {
    "do_nhay": {"vi": "Độ nhạy", "en": "Sensitivity"},
    "do_dac_hieu": {"vi": "Độ đặc hiệu", "en": "Specificity"},
    "mot_tru_dac_hieu": {"vi": f"1 {TRU} Độ đặc hiệu", "en": f"1 {TRU} Specificity"},
    "nghien_cuu": {"vi": "Nghiên cứu", "en": "Study"},
    "trong_so": {"vi": "Trọng số", "en": "Weight"},
    "ktc95": {"vi": "KTC 95%", "en": "95% CI"},
    "gop_co_dinh": {"vi": "Gộp — mô hình hiệu ứng cố định", "en": "Common-effect model"},
    "gop_ngau_nhien": {"vi": "Gộp — mô hình hiệu ứng ngẫu nhiên", "en": "Random-effects model"},
    "khoang_du_bao": {"vi": "Khoảng dự báo 95%", "en": "95% prediction interval"},
    "diem_tom_tat": {"vi": "Điểm tóm tắt", "en": "Summary point"},
    "vung_tin_cay": {"vi": "Vùng tin cậy 95%", "en": "95% confidence region"},
    "vung_du_bao": {"vi": "Vùng dự báo 95%", "en": "95% prediction region"},
    "duong_sroc": {"vi": "Đường SROC", "en": "SROC curve"},
    "sai_so_chuan": {"vi": "Sai số chuẩn", "en": "Standard error"},
    "khong_dong_nhat": {"vi": "Không đồng nhất", "en": "Heterogeneity"},
    "kiem_dinh_tong": {"vi": "Kiểm định hiệu ứng chung", "en": "Test for overall effect"},
    "khac_biet_nhom": {"vi": "Khác biệt giữa các phân nhóm", "en": "Test for subgroup differences"},
    "nghien_cuu_bo_sung": {"vi": "Nghiên cứu bù (trim-and-fill)", "en": "Filled studies (trim-and-fill)"},
}


class LoiBieuDo(ValueError):
    """Dữ liệu vào thiếu/sai miền — KHÔNG vẽ «cho có»."""


def nhan(khoa: str, ngon_ngu: str = "vi") -> str:
    return NHAN[khoa]["en" if ngon_ngu == "en" else "vi"]


def kiem_ngon_ngu(ngon_ngu: str) -> str:
    if ngon_ngu not in NGON_NGU:
        raise LoiBieuDo(f"ngon_ngu phải là {'/'.join(NGON_NGU)}, nhận «{ngon_ngu}»")
    return ngon_ngu


def so(x: Optional[float], nd: int = 2, ngon_ngu: str = "vi") -> str:
    """Định dạng số theo ngôn ngữ tài liệu: vi ⇒ «0,49», «−1,20»; en ⇒ «0.49», «−1.20». None/NaN ⇒ «—»."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    s = f"{x:.{nd}f}"
    if s.startswith("-"):
        s = TRU + s[1:]
        if float(x) == 0 or re.fullmatch(TRU + r"0(\.0*)?", s):
            s = s[1:]
    return s.replace(".", ",") if ngon_ngu == "vi" else s


def p_chu(p: Optional[float], ngon_ngu: str = "vi") -> str:
    """p ba chữ số thập phân; < 0,001 viết «< 0,001» (chuẩn trình bày K9)."""
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "p = —"
    if p < 0.001:
        return "p < " + so(0.001, 3, ngon_ngu)
    return "p = " + so(p, 3, ngon_ngu)


def phan_tram(x: float, nd: int = 0, ngon_ngu: str = "vi") -> str:
    return so(100 * x, nd, ngon_ngu) + "%"


def plt_chuan():
    """matplotlib chạy không màn hình, phông có chân, tái lập được (hashsalt cố định, phông nhúng TrueType)."""
    import logging  # noqa: PLC0415

    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    import matplotlib  # noqa: PLC0415

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "font.size": 9.5, "axes.titlesize": 10, "axes.labelsize": 9.5, "legend.fontsize": 8.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8,
        "xtick.major.width": 0.8, "ytick.major.width": 0.8, "lines.linewidth": 1.0,
        "svg.hashsalt": "ebm-bieu-do", "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.unicode_minus": True, "figure.dpi": 100,
    })
    return plt


def dinh_dang_truc(ax, ngon_ngu: str = "vi", truc: str = "xy", nd: Optional[int] = None) -> None:
    """Nhãn vạch trục theo ngôn ngữ (dấu phẩy thập phân cho vi). `nd` None ⇒ số chữ số tự gọn (bỏ số 0 thừa)."""
    from matplotlib.ticker import FuncFormatter  # noqa: PLC0415

    def _f(v, _pos):
        if nd is not None:
            return so(v, nd, ngon_ngu)
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        s = s if s not in ("-0", "") else "0"
        s = s.replace("-", TRU)
        return s.replace(".", ",") if ngon_ngu == "vi" else s

    if "x" in truc:
        ax.xaxis.set_major_formatter(FuncFormatter(_f))
    if "y" in truc:
        ax.yaxis.set_major_formatter(FuncFormatter(_f))


def luu(fig, dich: Path, dinh_dang: Sequence[str] = ("png", "pdf"),
        so_lieu: Optional[Dict[str, Any]] = None) -> List[Path]:
    """Ghi hình ra PNG (300 dpi) + PDF vector cùng tên gốc; `so_lieu` ⇒ thêm `<tên>.json` (số liệu đã vẽ).

    Ghi qua tệp tạm rồi đổi tên (không để lại tệp dở nếu lỗi giữa chừng)."""
    plt = plt_chuan()
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    goc = dich.with_suffix("")
    ra: List[Path] = []
    for dd in dinh_dang:
        p = goc.with_suffix("." + dd)
        tam = p.with_name(p.stem + ".tam." + dd)
        meta = {"Software": None} if dd == "png" else {"Creator": None, "Producer": None, "CreationDate": None}
        fig.savefig(tam, dpi=DPI, bbox_inches="tight", metadata=meta)
        os.replace(tam, p)
        ra.append(p)
    if so_lieu is not None:
        p = goc.with_suffix(".json")
        tam = p.with_name(p.stem + ".tam.json")
        tam.write_text(json.dumps(so_lieu, ensure_ascii=False, indent=1, default=_json_mac_dinh) + "\n",
                       encoding="utf-8", newline="\n")
        os.replace(tam, p)
        ra.append(p)
    plt.close(fig)
    return ra


def _json_mac_dinh(o: Any) -> Any:
    try:
        import numpy as np  # noqa: PLC0415

        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:  # pragma: no cover
        pass
    raise TypeError(f"không ghi JSON được kiểu {type(o).__name__}")


# ── Kiểm chéo bằng R ─────────────────────────────────────────────────────────────────────────────────────────────
def chay_r_kiem_cheo(ma_r: str, *, thoi_han: int = 300) -> Dict[str, Any]:
    """Chạy một đoạn R (in các dòng `KQ <khoá> <số>`); trả {"trang_thai": "da_chay"|"khong_kiem_cheo_duoc", "kq"}.

    Thiếu Rscript, gói R, hoặc R lỗi ⇒ «khong_kiem_cheo_duoc» kèm lý do — không bao giờ coi là khớp."""
    try:
        import cau_noi_r as CR  # noqa: PLC0415

        rscript = CR.tim_r()
    except Exception as exc:  # noqa: BLE001 — KhongDoDuoc hoặc thiếu mô-đun: chỉ là không đo được
        return {"trang_thai": "khong_kiem_cheo_duoc", "ly_do": str(exc)[:300], "kq": {}}
    with tempfile.TemporaryDirectory(prefix="bd-r-") as td:
        p = Path(td) / "kc.R"
        p.write_text(ma_r, encoding="utf-8", newline="\n")
        ma, out, err = CR.chay_r(rscript, [str(p)], thu_muc=Path(td), thoi_han=thoi_han)
    kq: Dict[str, float] = {}
    for dong in out.splitlines():
        m = re.match(r"^KQ\s+(\S+)\s+(\S+)\s*$", dong.strip())
        if m:
            try:
                kq[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    if ma != 0 or not kq:
        return {"trang_thai": "khong_kiem_cheo_duoc", "ly_do": (err or out)[-400:], "kq": kq}
    return {"trang_thai": "da_chay", "kq": kq}


def doi_chieu(python: Dict[str, float], r: Dict[str, Any], dung_sai: float = 1e-4) -> Dict[str, Any]:
    """So từng khoá Python ↔ R: lệch tương đối (hoặc tuyệt đối khi giá trị gần 0) ≤ dung_sai ⇒ khớp.

    Trạng thái: «khop» chỉ khi R đã chạy VÀ mọi khoá có mặt ở cả hai bên đều khớp; thiếu khoá phía R ⇒ «thieu_khoa»."""
    if r.get("trang_thai") != "da_chay":
        return {"trang_thai": "khong_kiem_cheo_duoc", "ly_do": r.get("ly_do", ""), "chi_tiet": []}
    chi_tiet, lech, thieu = [], 0, 0
    for k, v in python.items():
        if k not in r["kq"]:
            thieu += 1
            chi_tiet.append({"khoa": k, "python": v, "r": None, "khop": False})
            continue
        rv = r["kq"][k]
        mau = max(abs(rv), 1.0)
        ok = abs(v - rv) / mau <= dung_sai
        lech += 0 if ok else 1
        chi_tiet.append({"khoa": k, "python": v, "r": rv, "khop": ok})
    tt = "khop" if not lech and not thieu else ("lech" if lech else "thieu_khoa")
    return {"trang_thai": tt, "dung_sai": dung_sai, "chi_tiet": chi_tiet}


def r_vec(xs: Iterable[float]) -> str:
    return "c(" + ", ".join(repr(float(x)) for x in xs) + ")"


def mui_ten_vuot(ax, y: float, x_min: float, x_max: float, lo: float, hi: float, log: bool) -> Tuple[float, float]:
    """KTC vượt khung trục ⇒ cắt tại mép + vẽ đầu mũi tên (không âm thầm cắt cụt). Trả (lo, hi) đã kẹp."""
    lo_k, hi_k = max(lo, x_min), min(hi, x_max)
    kw = {"arrowstyle": "-|>", "lw": 0.8, "color": "#222222", "mutation_scale": 7}
    if lo < x_min:
        ax.annotate("", xy=(x_min, y), xytext=(x_min * 1.25 if log else x_min + (x_max - x_min) * 0.04, y),
                    arrowprops=kw)
    if hi > x_max:
        ax.annotate("", xy=(x_max, y), xytext=(x_max / 1.25 if log else x_max - (x_max - x_min) * 0.04, y),
                    arrowprops=kw)
    return lo_k, hi_k
