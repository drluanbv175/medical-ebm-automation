#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BẢNG BỘ BIẾN G3 CHO PI DUYỆT — `exports/<mã>/G3_BO_BIEN_SO_<mã>.md` (G3-T2, bác sĩ chọn 15/11/2026).

Vì sao: G5-AUTO-11 (`doi_chieu_bien_de_cuong.py`) đòi bộ biến máy khớp một NGUỒN NGƯỜI DUYỆT — bảng biến số của đề cương
nộp Hội đồng hoặc `G3_BO_BIEN_SO_<mã>.md`. Giả lập trọn lần 3 (15/11/2026) đo được: không công cụ nào sinh tệp `.md` đó,
không agent nào được dạy, nên đề tài mới kẹt ở G5. Bác sĩ chọn: «Agent bien-so-nghien-cuu soạn thêm
G3_BO_BIEN_SO_<mã>.md cho PI đọc và duyệt … Giữ nguyên ý của #266: dữ liệu máy phải khớp một nguồn do người duyệt.»

Công cụ dựng bảng từ bộ biến máy (`_bo-bien-rieng.csv` + `_bien-phai-sinh.csv` + `_ma-tran-muc-tieu-bien.csv` +
`_ma-thieu-theo-bien.csv`). Đối chiếu máy với bảng do chính máy sinh ra là vòng tròn, nên:
  • bảng có DẤU MÁY SOẠN (`<!-- BANG-BIEN-G3: … -->`) chỉ được tính là nguồn người duyệt khi PI đã ghi
    `study_meta.json → gate_params.G3.bo_bien_so_duyet = {"reviewed_at": "<ISO-8601>", "dau_van_tay": "<dấu>"}`, với dấu
    trùng nội dung HIỆN TẠI (cùng cơ chế với G3-HUMAN-06, `cong_song.xac_nhan_gan_noi_dung`). Sửa bảng sau khi ghi thì
    xác nhận mất hiệu lực. AGENT KHÔNG GHI xác nhận này;
  • bảng KHÔNG có dấu máy soạn (người soạn tay, vd bảng btm 28/10/2026 chủ nhiệm đã duyệt trong văn bản) vẫn được tính
    như trước (#266);
  • khung trạng thái giữa `<!-- TRANG-THAI:BAT-DAU -->` và `<!-- TRANG-THAI:KET-THUC -->` KHÔNG tính vào dấu, nên PI đổi
    dòng «[CẦN PI DUYỆT]» thành «ĐÃ DUYỆT <ngày>» mà không phải ghi lại dấu.

Trạng thái (`trang_thai()`): KHONG_CO · NGUOI_SOAN · CHUA_DUYET · XAC_NHAN_LECH · DA_DUYET.
Chỉ NGUOI_SOAN và DA_DUYET là nguồn người duyệt.

Ghi tệp: chỉ khi chưa có, hoặc bản máy soạn CHƯA duyệt mà nội dung không bị sửa tay. Không bao giờ ghi đè bảng do người
soạn, bảng đã được duyệt, hay bảng đã bị sửa tay (`--ghi-de` chỉ mở được trường hợp sửa tay/xác nhận lệch của bản máy
soạn; bảng đang có xác nhận hợp lệ thì PI phải gỡ xác nhận trước).

Lệnh:
  python3 tools/bang_bien_g3.py soan --study <mã> [--ghi] [--ghi-de]
      mã 0 đã ghi/xem trước · 1 từ chối · 2 thiếu đầu vào
  python3 tools/bang_bien_g3.py trang-thai --study <mã> [--json]
      mã 0 là nguồn người duyệt · 1 chưa · 2 chưa có bảng

Chỉ đọc bộ biến máy; không ký, không đổi cổng. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:  # stdout UTF-8 trên Windows
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cong_song as CS  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402

BASE = Path(__file__).resolve().parent.parent

TEP_MA_THIEU = "_ma-thieu-theo-bien.csv"
DAU_MAY = "<!-- BANG-BIEN-G3:"
MOC_TT_BD = "<!-- TRANG-THAI:BAT-DAU -->"
MOC_TT_KT = "<!-- TRANG-THAI:KET-THUC -->"
KHOA_DUYET = "bo_bien_so_duyet"
NHAN_CHO_DUYET = "[CẦN PI DUYỆT]"

KHONG_CO = "KHONG_CO"
NGUOI_SOAN = "NGUOI_SOAN"
CHUA_DUYET = "CHUA_DUYET"
XAC_NHAN_LECH = "XAC_NHAN_LECH"
DA_DUYET = "DA_DUYET"
LA_NGUON_NGUOI_DUYET = frozenset({NGUOI_SOAN, DA_DUYET})

_DAU_NGUON_RE = re.compile(r"dau_nguon=([0-9a-f]{8,64})")
_DAU_SOAN_RE = re.compile(r"dau_soan=([0-9a-f]{8,64})")
_DAU_KHUNG_RE = re.compile(r"dau_khung=([0-9a-f]{8,64})")
_CHO_DAU_SOAN = "dau_soan=0000000000000000"
_CHO_DAU_KHUNG = "dau_khung=0000000000000000"
#: Dấu CẤU TRÚC mà chỉ bộ soạn này đặt vào tệp — còn bất kỳ dấu nào mà mất dòng dấu máy ⇒ dấu máy bị gỡ (không phải
#: bảng người soạn). KHÔNG dùng câu chữ («Máy soạn ngày…»): bảng btm người duyệt 28/10 có câu đó mà không có dấu nào.
_DAU_CAU_TRUC_MAY = (MOC_TT_BD, MOC_TT_KT, NHAN_CHO_DUYET, "dau_soan=", "dau_nguon=")


def ten_tep(study: str) -> str:
    return f"G3_BO_BIEN_SO_{study}.md"


# ───────────────────────────── dấu vân tay ─────────────────────────────
def than_bang(chu: str) -> str:
    """Phần tính dấu: sau khung trạng thái (nếu có), CRLF→LF, bỏ khoảng trắng cuối dòng và dòng trống cuối tệp.
    Bộ đọc G5-AUTO-11 (`doi_chieu_bien_de_cuong.doc_bo_bien_g3`) cũng CHỈ đọc phần này của bảng máy soạn — vùng không
    tính dấu thì không được góp nội dung vào đối chiếu (thẩm định #274, ĐỎ 2)."""
    chu = chu.replace("\r\n", "\n")
    if MOC_TT_KT in chu:
        chu = chu.split(MOC_TT_KT, 1)[1]
    return "\n".join(d.rstrip() for d in chu.split("\n")).strip("\n")


def _vung_ngoai_dau(chu: str) -> str:
    """Phần TRƯỚC thân bảng (tiêu đề + khung trạng thái) — không tính dấu."""
    chu = chu.replace("\r\n", "\n")
    return chu.split(MOC_TT_KT, 1)[0] if MOC_TT_KT in chu else ""


def _khung_trang_thai(chu: str) -> str:
    chu = chu.replace("\r\n", "\n")
    if MOC_TT_BD not in chu or MOC_TT_KT not in chu:
        return ""
    return "\n".join(d.rstrip() for d in chu.split(MOC_TT_BD, 1)[1].split(MOC_TT_KT, 1)[0].split("\n")).strip("\n")


def _bam(van_ban: str) -> str:
    """16 hex SHA-256 giữ NGUYÊN ranh giới dòng và từng ký tự (thẩm định #274, ĐỎ 1: cong_song.dau_van_tay gộp mọi
    khoảng trắng kể cả xuống dòng + NFC ⇒ chèn một dòng trống/nối hàng làm bộ đọc bảng đọc khác mà dấu không đổi)."""
    return hashlib.sha256(van_ban.encode("utf-8")).hexdigest()[:16]


def dau_bang(chu: str) -> str:
    return _bam(than_bang(chu))


# Cột của _bien-phai-sinh.csv KHÔNG thuộc định nghĩa biến: dấu ký duyệt công thức của thống kê viên (bien_phai_sinh
# duyet). Ký duyệt sau khi khoá G5 là đúng quy trình (SPSS/R: khoá G5 → bien_phai_sinh kiem → G6) nên không được làm
# MT-12 báo «bộ biến máy đã đổi sau khi soạn bảng» (đo 17/11/2026 trên giả lập chẩn đoán: chỉ cột này đổi).
_COT_KY_DUYET_PHAI_SINH = ("nguoi_duyet",)


def _sha_csv_bo_cot(p: Path, bo: Sequence[str]) -> str:
    """SHA-256 nội dung CSV sau khi bỏ các cột `bo` (CRLF→LF như cong_song.dau_van_tay_tep); vắng ⇒ «<vắng>»."""
    import csv  # noqa: PLC0415
    import io  # noqa: PLC0415

    try:
        chu = Path(p).read_bytes().replace(b"\r\n", b"\n").decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        try:
            return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        except OSError:
            return "<vắng>"
    dong = list(csv.reader(io.StringIO(chu)))
    if not dong:
        return hashlib.sha256(b"").hexdigest()
    giu = [i for i, c in enumerate(dong[0]) if c.strip() not in bo]
    ra = io.StringIO()
    csv.writer(ra, lineterminator="\n").writerows([[r[i] if i < len(r) else "" for i in giu] for r in dong])
    return hashlib.sha256(ra.getvalue().encode("utf-8")).hexdigest()


def dau_nguon(out_dir: Path) -> str:
    """Dấu nguồn của bảng (từ 17/11/2026 bỏ cột ký duyệt công thức phái sinh — `_COT_KY_DUYET_PHAI_SINH`)."""
    d = Path(out_dir)
    phan = []
    for p in (d / MT.TEP_BO_BIEN, d / MT.TEP_PHAI_SINH, d / MT.TEP_MA_TRAN, d / TEP_MA_THIEU):
        if p.name == MT.TEP_PHAI_SINH:
            phan.append(_sha_csv_bo_cot(p, _COT_KY_DUYET_PHAI_SINH))
            continue
        try:
            phan.append(hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        except OSError:
            phan.append("<vắng>")
    return CS.dau_van_tay(*phan)


def _dau_nguon_v1(out_dir: Path) -> str:
    """Dấu nguồn kiểu trước 17/11/2026 (băm nguyên tệp) — bảng đã soạn trước đó ghi dấu này, vẫn nhận để không báo đỏ
    giả cho bảng cũ."""
    d = Path(out_dir)
    return CS.dau_van_tay_tep(d / MT.TEP_BO_BIEN, d / MT.TEP_PHAI_SINH, d / MT.TEP_MA_TRAN, d / TEP_MA_THIEU)


def _bo_dong_dau_may(than: str) -> str:
    return "\n".join(d for d in than.split("\n") if not d.startswith(DAU_MAY))


def dau_noi_dung_khong_dau_may(chu: str) -> str:
    """Dấu phần thân trừ dòng dấu máy — so với `dau_soan` để biết bảng có bị sửa sau khi máy soạn không."""
    return _bam(_bo_dong_dau_may(than_bang(chu)))


def dau_khung(chu: str) -> str:
    """Dấu khung trạng thái — so với `dau_khung` để biết PI/người đã ghi vào khung (thẩm định #274, VÀNG 6)."""
    return _bam(_khung_trang_thai(chu))


def _dau_trong_dong_may(chu: str, mau: "re.Pattern[str]") -> Optional[str]:
    if DAU_MAY not in chu:
        return None
    m = mau.search(chu.split(DAU_MAY, 1)[1].split("-->", 1)[0])
    return m.group(1) if m else None


def bi_sua_sau_khi_soan(chu: str) -> bool:
    """True khi thân bảng HOẶC khung trạng thái khác lúc máy soạn (người đã sửa/ghi chú), hoặc dòng dấu máy thiếu
    dau_soan/dau_khung (không biết ⇒ coi là có)."""
    goc = _dau_trong_dong_may(chu, _DAU_SOAN_RE)
    goc_khung = _dau_trong_dong_may(chu, _DAU_KHUNG_RE)
    return (goc is None or goc != dau_noi_dung_khong_dau_may(chu)
            or goc_khung is None or goc_khung != dau_khung(chu))


# ───────────────────────────── trạng thái duyệt ─────────────────────────────
def trang_thai(out_dir: Path, study: str, meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Trạng thái bảng G3 và xác nhận PI. Không đọc được tệp ⇒ coi như CHƯA duyệt (không bao giờ «đạt» im lặng)."""
    p = Path(out_dir) / ten_tep(study)
    ra: Dict[str, Any] = {"tep": p.name, "trang_thai": KHONG_CO, "ly_do": f"chưa có {p.name}", "dau_hien_tai": None,
                          "nguon_doi": None, "sua_sau_khi_soan": None, "la_nguon_nguoi_duyet": False}
    if not p.is_file():
        return ra
    ra["doc_duoc"] = True
    try:
        chu = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        ra.update(trang_thai=XAC_NHAN_LECH, doc_duoc=False,
                  ly_do=f"không đọc được {p.name} dạng UTF-8 ({type(e).__name__}) — lưu lại bằng UTF-8")
        return ra
    if DAU_MAY not in chu:
        con = [x for x in _DAU_CAU_TRUC_MAY if x in chu]
        if con:  # thẩm định #274, VÀNG 3: gỡ một dòng chú thích không biến bản nháp máy thành «người soạn»
            ra.update(trang_thai=CHUA_DUYET,
                      ly_do=(f"dòng dấu máy đã bị gỡ nhưng tệp còn dấu của bản máy soạn ({', '.join(con[:3])}) — vẫn "
                             "là bản nháp máy CHƯA duyệt; soạn lại bằng bang_bien_g3.py rồi PI duyệt, hoặc người soạn "
                             "lại bảng (bỏ hết khung trạng thái của máy)"))
            return ra
        ra.update(trang_thai=NGUOI_SOAN, la_nguon_nguoi_duyet=True,
                  ly_do="bảng do người soạn (không có dấu máy soạn) — tính là nguồn người duyệt như trước")
        return ra
    dau = dau_bang(chu)
    ra["dau_hien_tai"] = dau
    goc_nguon = _dau_trong_dong_may(chu, _DAU_NGUON_RE)
    if goc_nguon:
        ra["nguon_doi"] = goc_nguon not in (dau_nguon(out_dir), _dau_nguon_v1(out_dir))
    ra["sua_sau_khi_soan"] = bi_sua_sau_khi_soan(chu)
    if any(d.lstrip().startswith("|") for d in _vung_ngoai_dau(chu).split("\n")):
        # thẩm định #274, ĐỎ 2: bảng đặt ngoài vùng tính dấu không được lặng lẽ bỏ qua/được đọc — coi là sửa tay.
        ra.update(trang_thai=XAC_NHAN_LECH,
                  ly_do="có bảng nằm NGOÀI vùng tính dấu (tiêu đề/khung trạng thái) — mọi bảng biến phải nằm dưới "
                        "dòng dấu máy; chuyển vào thân bảng rồi PI duyệt lại")
        return ra
    meta = dict(meta) if meta is not None else MT.doc_meta(Path(out_dir))
    xn = MT._gp(meta, "G3").get(KHOA_DUYET)
    if not xn:
        ra.update(trang_thai=CHUA_DUYET,
                  ly_do=(f"bản máy soạn CHƯA được PI duyệt — chưa có gate_params.G3.{KHOA_DUYET}; PI đọc bảng rồi ghi "
                         f'{{"reviewed_at": "<ISO-8601>", "dau_van_tay": "{dau}"}}'))
        return ra
    ok, ly = CS.xac_nhan_gan_noi_dung(xn, dau)
    ra.update(trang_thai=DA_DUYET if ok else XAC_NHAN_LECH, la_nguon_nguoi_duyet=ok,
              ly_do=("PI đã duyệt đúng nội dung hiện tại" if ok else f"xác nhận PI không còn hiệu lực: {ly}"))
    return ra


# ───────────────────────────── dựng bảng ─────────────────────────────
def _o(v: Any) -> str:
    """Ô bảng Markdown: một dòng, không có «|» (bộ đọc bảng tách cột theo «|»)."""
    return " ".join(str(v or "").replace("|", "/").split())


def loai_truong(row: Mapping[str, str]) -> str:
    ft = str(row.get("Field Type") or "").strip().lower()
    val = str(row.get("Text Validation Type OR Show Slider Number") or "").strip().lower()
    if ft == "text":
        if not val:
            return "chữ tự do"
        if val == "integer":
            return "số nguyên"
        m = re.fullmatch(r"number_(\d)dp(?:_comma_decimal)?", val)
        if m:
            return f"số ({m.group(1)} chữ số lẻ)"
        if val.startswith("number"):
            return "số"
        if val.startswith("datetime"):
            return "ngày giờ"
        if val.startswith("date"):
            return "ngày"
        if val.startswith("time"):
            return "giờ"
        return f"chữ ({val})"
    return {"notes": "văn bản dài", "radio": "chọn một", "dropdown": "chọn một (danh sách)", "checkbox": "chọn nhiều",
            "yesno": "có/không", "truefalse": "đúng/sai", "calc": "tính tự động (calc)", "slider": "thanh trượt",
            "descriptive": "mô tả (không nhập)", "file": "tệp đính kèm"}.get(ft, ft or "—")


def _lua_chon(choices: str) -> List[Tuple[str, str]]:
    ra = []
    for doan in str(choices or "").split("|"):
        if "," in doan:
            ma, nhan = doan.split(",", 1)
            ra.append((ma.strip(), nhan.strip()))
        elif doan.strip():
            ra.append((doan.strip(), ""))
    return ra


def gia_tri_hop_le(row: Mapping[str, str]) -> str:
    """Cách viết bộ đọc G5-AUTO-11 hiểu: ô chọn «1, Có; 0, Không»; ô số «min – max»."""
    ft = str(row.get("Field Type") or "").strip().lower()
    if ft in ("radio", "dropdown", "checkbox"):
        return "; ".join(f"{m}, {n}" for m, n in _lua_chon(row.get("Choices, Calculations, OR Slider Labels") or ""))
    if ft == "yesno":
        return "1, Có; 0, Không"
    if ft == "truefalse":
        return "1, Đúng; 0, Sai"
    if ft == "calc":
        return "công thức: " + str(row.get("Choices, Calculations, OR Slider Labels") or "").strip()
    if ft == "slider":
        # thẩm định #274, VÀNG 5: nhãn thanh trượt «0 = … | 100 = …» trong ô này làm G5-AUTO-11 đọc «100 =» thành mã đặc
        # biệt chưa khai ⇒ LỆCH giả kéo dài sau khi PI duyệt. Ô chỉ ghi khoảng; nhãn sang cột Ghi chú.
        lo = str(row.get("Text Validation Min") or "").strip() or "0"
        hi = str(row.get("Text Validation Max") or "").strip() or "100"
        return f"{lo} – {hi}"
    if ft == "text":
        val = str(row.get("Text Validation Type OR Show Slider Number") or "").strip().lower()
        lo = str(row.get("Text Validation Min") or "").strip()
        hi = str(row.get("Text Validation Max") or "").strip()
        if lo and hi:
            return f"{lo} – {hi}"
        if lo:
            return f"≥ {lo}"
        if hi:
            return f"≤ {hi}"
        if val.startswith("date"):
            return "ngày hợp lệ (YYYY-MM-DD)"
        if val.startswith(("number", "integer")):
            return "số bất kỳ (chưa khai khoảng)"
        return "chữ tự do"
    if ft == "notes":
        return "văn bản tự do"
    return "—"


def _ma_tran_theo_bien(dong: Optional[Sequence[Mapping[str, str]]]) -> Dict[str, List[Mapping[str, str]]]:
    ra: Dict[str, List[Mapping[str, str]]] = {}
    for r in dong or []:
        b = str(r.get("bien") or "").strip()
        if b:
            ra.setdefault(b, []).append(r)
    return ra


def _gop(ds: Sequence[str]) -> str:
    ra: List[str] = []
    for x in ds:
        x = str(x or "").strip()
        if x and x not in ra:
            ra.append(x)
    return "; ".join(ra) or "—"


def _tu_kiem_ma(ten: str, row: Mapping[str, str], o_gia_tri: str) -> Optional[str]:
    """Đọc lại ô «Giá trị hợp lệ» bằng CHÍNH bộ đọc của G5-AUTO-11; lệch mã ⇒ ghi để PI xem tay (không sửa nhãn)."""
    ft = str(row.get("Field Type") or "").strip().lower()
    if ft not in ("radio", "dropdown", "checkbox", "yesno", "truefalse"):
        dac_biet = re.findall(r"(?<![\d.])(\d{3,})\s*=", o_gia_tri or "")
        if dac_biet:  # cùng mẫu «mã đặc biệt» của G5-AUTO-11 cho ô không phải ô chọn
            return (f"`{ten}`: ô «Giá trị hợp lệ» chứa «{dac_biet[0]} =» mà bộ đọc G5-AUTO-11 coi là mã đặc biệt — "
                    "khai ở _ma-thieu-theo-bien.csv hoặc PI sửa ô")
        return None
    try:
        import doi_chieu_bien_de_cuong as DC  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return f"`{ten}`: không tự kiểm được mã ({type(e).__name__})"
    doc, _ = DC.doc_ma(o_gia_tri)
    can = {0, 1} if ft in ("yesno", "truefalse") else DC.ma_tu_dien(
        row.get("Choices, Calculations, OR Slider Labels") or "")
    if doc != can:
        doc_ra = sorted(doc) if doc else "không đọc được"
        return (f"`{ten}`: nhãn lựa chọn làm bộ đọc G5-AUTO-11 đọc ra mã {doc_ra} ≠ từ điển {sorted(can)} "
                "(thường do nhãn chứa «=» hoặc «;») — PI đối chiếu tay mã ↔ nhãn")
    return None


def soan(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None,
         ngay: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
    """(nội dung Markdown | None khi thiếu bộ biến, danh sách việc PI cần xem tay)."""
    out_dir = Path(out_dir)
    bo, loi = MT.doc_bo_bien(out_dir)
    if loi or not bo:
        return None, [loi or f"chưa có {MT.TEP_BO_BIEN} — chưa có gì để soạn bảng"]
    dong_mt, loi_mt = MT.doc_ma_tran(out_dir)
    theo_bien = _ma_tran_theo_bien(dong_mt)
    phai_sinh = MT.doc_phai_sinh(out_dir)
    ma_thieu, _, _ = MT._doc_csv(out_dir / TEP_MA_THIEU)
    ngay = ngay or date.today().isoformat()
    xem: List[str] = []
    if loi_mt:
        xem += [f"ma trận: {x}" for x in loi_mt]
    elif dong_mt is None:
        xem.append(f"chưa có {MT.TEP_MA_TRAN} — cột vai trò/mục tiêu để trống; dựng ma trận trước (G3-AUTO-19)")

    theo_mau: Dict[str, List[Tuple[str, Mapping[str, str]]]] = {}
    for ten, row in bo.items():
        theo_mau.setdefault(str(row.get("Form Name") or "").strip() or "(không tên)", []).append((ten, row))
    ngoai_ma_tran = [t for t in bo if t not in theo_bien and t.lower() != "record_id"
                     and str(bo[t].get("Field Type") or "").strip().lower() != "descriptive"]

    dl: List[str] = [
        f"# Bộ biến số đề tài (G3-T2) · {study}", "", MOC_TT_BD,
        f"> **{NHAN_CHO_DUYET}** Máy soạn ngày {ngay} từ bộ biến máy của đề tài (`{MT.TEP_BO_BIEN}`, "
        f"`{MT.TEP_PHAI_SINH}`, `{MT.TEP_MA_TRAN}`, `{TEP_MA_THIEU}`). Khi PI đã duyệt, bảng này là NGUỒN NGƯỜI DUYỆT: "
        "từ điển nhập liệu G5, mẫu nhập Excel/SPSS và tệp SPSS/R phải khớp bảng này (G5-AUTO-11). Bản nháp CHƯA duyệt "
        "KHÔNG được tính là nguồn người duyệt, vì máy so với bảng do chính nó sinh ra là vòng tròn.",
        ">",
        "> **PI làm:** (1) đọc từng dòng — tên, nhãn, loại, giá trị hợp lệ, vai trò, mục tiêu, bắt buộc, điều kiện "
        "hiện; (2) sai ở đâu thì sửa thẳng trong tệp này, hoặc yêu cầu sửa bộ biến máy rồi soạn lại; "
        "(3) khi đồng ý, ghi vào "
        f"`study_meta.json` → `gate_params.G3.{KHOA_DUYET}` = "
        '`{"reviewed_at": "<ISO-8601>", "dau_van_tay": "<dấu>"}`, dấu lấy từ lệnh '
        f"`python3 tools/bang_bien_g3.py trang-thai --study {study}` (tính trên nội dung HIỆN TẠI; sửa bảng sau khi "
        "ghi thì phải ghi lại). Agent KHÔNG ghi xác nhận này. Khung trạng thái này không tính vào dấu — "
        "PI có thể đổi dòng "
        f"«{NHAN_CHO_DUYET}» thành «ĐÃ DUYỆT <ngày>».",
        MOC_TT_KT, "",
        f"{DAU_MAY} may-soan ngay={ngay} dau_nguon={dau_nguon(out_dir)} {_CHO_DAU_SOAN} {_CHO_DAU_KHUNG} -->", "",
        "## 1. Tóm tắt", "",
        f"- **{len(bo)} trường nhập** trong {len(theo_mau)} biểu mẫu: "
        + ", ".join(f"`{m}` ({len(v)})" for m, v in theo_mau.items()) + ".",
        f"- **{len(phai_sinh)} biến phái sinh** tính ở bước phân tích (không nhập tay).",
        (f"- **Ma trận mục tiêu → biến:** {len(dong_mt)} dòng, "
         f"{len({str(r.get('muc_tieu')) for r in dong_mt})} mục tiêu." if dong_mt else
         f"- **Ma trận mục tiêu → biến:** chưa có `{MT.TEP_MA_TRAN}`."),
        "- Không có trường định danh: "
        + ("đúng." if not [t for t, r in bo.items() if MT._chuan_thuoc_tinh("Identifier?", r.get("Identifier?"))]
           else "**SAI — có trường gắn cờ định danh, xem mục 6.**"),
        "", "## 2. Bảng bộ biến (trường nhập)", "",
    ]
    tieu_de = ("| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Biểu mẫu | Vai trò (ma trận) | Mục tiêu | Câu hỏi | "
               "Bắt buộc | Hiện khi | Ghi chú |")
    for mau, ds in theo_mau.items():
        dl += [f"**Biểu mẫu `{mau}`**", "", tieu_de, "|" + "---|" * 11]
        for ten, row in ds:
            mt = theo_bien.get(ten, [])
            gt = gia_tri_hop_le(row)
            loi_ma = _tu_kiem_ma(ten, row, gt)
            if loi_ma:
                xem.append(loi_ma)
            ghi_chu = [x for x in (str(row.get("Field Note") or "").strip(),
                                   str(row.get("Field Annotation") or "").strip()) if x]
            if str(row.get("Field Type") or "").strip().lower() == "slider" and str(
                    row.get("Choices, Calculations, OR Slider Labels") or "").strip():
                ghi_chu.append("nhãn thanh trượt: " + str(row["Choices, Calculations, OR Slider Labels"]).strip())
            if MT._chuan_thuoc_tinh("Identifier?", row.get("Identifier?")):
                ghi_chu.insert(0, "ĐỊNH DANH")
                xem.append(f"`{ten}`: gắn cờ định danh — G5-AUTO-02 sẽ chặn; bỏ hoặc thay bằng mã nghiên cứu")
            dl.append("| " + " | ".join(_o(x) for x in (
                f"`{ten}`", row.get("Field Label"), loai_truong(row), gt, mau,
                _gop([r.get("vai_tro", "") for r in mt]), _gop([r.get("muc_tieu", "") for r in mt]),
                _gop([r.get("cau_hoi", "") for r in mt]),
                "có" if MT._chuan_thuoc_tinh("Required Field?", row.get("Required Field?")) == "y" else "không",
                row.get("Branching Logic (Show field only if...)") or "—", "; ".join(ghi_chu) or "—")) + " |")
        dl.append("")

    dl += ["## 3. Biến phái sinh (tính ở bước phân tích)", ""]
    if phai_sinh:
        # «Định nghĩa / công thức» = định nghĩa NGƯỜI viết (cột dinh_nghia) nếu có — G5-AUTO-11 đặt nó cạnh công thức
        # máy và báo số ngưỡng của định nghĩa vắng trong công thức (V5); thiếu định nghĩa thì chép công thức.
        dl += ["| Tên | Nhãn | Kiểu | Định nghĩa / công thức | Công thức máy | Biến nguồn | Lặp k | Nhãn giá trị | "
               "Người duyệt công thức |", "|" + "---|" * 9]
        for ten, r in phai_sinh.items():
            dl.append("| " + " | ".join(_o(x) for x in (
                f"`{ten}`", r.get("nhan"), r.get("kieu"), r.get("dinh_nghia") or r.get("cong_thuc"),
                r.get("cong_thuc"), r.get("bien_nguon") or "—", r.get("lap_k") or "—",
                r.get("nhan_gia_tri") or "—", r.get("nguoi_duyet") or "chưa duyệt")) + " |")
            if not str(r.get("nguoi_duyet") or "").strip():
                xem.append(f"`{ten}`: công thức biến phái sinh chưa có người duyệt (thống kê viên/PI — MT-08)")
    else:
        dl.append(f"Không có (`{MT.TEP_PHAI_SINH}` vắng hoặc rỗng).")
    dl += ["", "## 4. Ma trận mục tiêu → biến → câu hỏi → phân tích", ""]
    if dong_mt:
        dl += ["| Mục tiêu | Khái niệm | Vai trò | Biến | Kiểu | Câu hỏi | Công cụ | Phân tích SAP |", "|" + "---|" * 8]
        for r in dong_mt:
            dl.append("| " + " | ".join(_o(r.get(c)) or "—" for c in (
                "muc_tieu", "khai_niem", "vai_tro", "bien", "kieu", "cau_hoi", "cong_cu", "phan_tich_sap")) + " |")
    else:
        dl.append("Chưa có ma trận.")
    dl += ["", "## 5. Mã thiếu theo biến", ""]
    if ma_thieu:
        dl += ["| Biến (hoặc mẫu) | Mã | Nhãn |", "|---|---|---|"]
        dl += [f"| {_o(r.get('bien'))} | {_o(r.get('ma'))} | {_o(r.get('nhan'))} |" for r in ma_thieu]
    else:
        dl.append(f"Không khai (`{TEP_MA_THIEU}` vắng) — ô trống là dữ liệu thiếu.")
    if ngoai_ma_tran:
        xem.append(f"{len(ngoai_ma_tran)} trường chưa gắn mục tiêu nào trong ma trận (mô tả/sàng lọc?): "
                   + ", ".join(f"`{t}`" for t in ngoai_ma_tran[:15]) + (" …" if len(ngoai_ma_tran) > 15 else ""))
    dl += ["", "## 6. Điểm PI cần xem tay", ""]
    dl += [f"- {x}" for x in xem] or ["- Máy không thấy điểm nào cần xem tay (vẫn cần PI đọc toàn bảng)."]
    dl += ["", "Cần bác sĩ kiểm chứng.", ""]
    chu = "\n".join(dl)
    chu = chu.replace(_CHO_DAU_SOAN, f"dau_soan={dau_noi_dung_khong_dau_may(chu)}", 1)
    return chu.replace(_CHO_DAU_KHUNG, f"dau_khung={dau_khung(chu)}", 1), xem


def ghi(out_dir: Path, study: str, *, ghi_de: bool = False,
        meta: Optional[Mapping[str, Any]] = None) -> Tuple[Optional[Path], str, int]:
    """(tệp đã ghi | None, thông điệp, mã thoát 0/1/2) — luật không ghi đè ở docstring đầu tệp."""
    out_dir = Path(out_dir)
    p = out_dir / ten_tep(study)
    chu, xem = soan(out_dir, study, meta=meta)
    if chu is None:
        return None, xem[0], 2
    if p.is_file():
        st = trang_thai(out_dir, study, meta)
        if not st.get("doc_duoc", True):  # thẩm định #274, XÁM 8: tệp không đọc được KHÔNG BAO GIỜ bị ghi đè
            return None, f"{p.name} không đọc được dạng UTF-8 — không ghi đè; người lưu lại bằng UTF-8 rồi chạy lại", 1
        if st["trang_thai"] == NGUOI_SOAN:
            return None, f"{p.name} do người soạn — KHÔNG BAO GIỜ ghi đè nguồn người duyệt", 1
        if st["trang_thai"] == DA_DUYET:
            return None, (f"{p.name} đang có xác nhận PI hợp lệ — không ghi đè; muốn soạn lại thì PI gỡ "
                          f"gate_params.G3.{KHOA_DUYET} trước"), 1
        cu = p.read_text(encoding="utf-8")
        sua_tay = bi_sua_sau_khi_soan(cu)
        if (sua_tay or st["trang_thai"] == XAC_NHAN_LECH) and not ghi_de:
            ly = ("bảng hoặc khung trạng thái đã bị sửa sau khi máy soạn (PI/người sửa tay, ghi chú?)" if sua_tay
                  else st["ly_do"])
            return None, f"{p.name}: {ly} — không ghi đè; xem lại rồi chạy với --ghi-de nếu chắc", 1
        if dau_noi_dung_khong_dau_may(cu) == dau_noi_dung_khong_dau_may(chu):
            return None, f"{p.name} đã đúng bản máy soạn hiện tại — không đổi", 0
    p.write_text(chu, encoding="utf-8", newline="\n")
    return p, f"đã ghi {p.name} ({len(xem)} điểm PI cần xem tay) — dấu nội dung {dau_bang(chu)}", 0


# ───────────────────────────── CLI ─────────────────────────────
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Bảng bộ biến G3 cho PI duyệt (G3_BO_BIEN_SO_<mã>.md).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    s = sub.add_parser("soan", help="soạn bảng từ bộ biến máy (mặc định chỉ xem trước)")
    s.add_argument("--study", required=True)
    s.add_argument("--ghi", action="store_true", help="ghi tệp (không ghi đè bảng người soạn/đã duyệt/sửa tay)")
    s.add_argument("--ghi-de", action="store_true", help="cho ghi đè bản máy soạn đã bị sửa tay / xác nhận lệch")
    t = sub.add_parser("trang-thai", help="bảng có phải nguồn người duyệt không + dấu nội dung cho PI")
    t.add_argument("--study", required=True)
    t.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    study = re.sub(r"[^\w\-]", "_", a.study.strip())
    out = BASE / "exports" / study
    if a.lenh == "trang-thai":
        st = trang_thai(out, study)
        if a.json:
            print(json.dumps(st, ensure_ascii=False, indent=1))
        else:
            bieu = {DA_DUYET: "🟢", NGUOI_SOAN: "🟢", CHUA_DUYET: "🟡", XAC_NHAN_LECH: "🔴", KHONG_CO: "⚪"}
            print(f"BẢNG BỘ BIẾN G3 — {study}: {bieu.get(st['trang_thai'], '•')} {st['trang_thai']} — {st['ly_do']}")
            if st["dau_hien_tai"]:
                print(f"  dấu nội dung hiện tại: {st['dau_hien_tai']}")
            if st["nguon_doi"]:
                print("  🟡 bộ biến máy đã đổi sau khi soạn bảng — chạy doi_chieu_bien_de_cuong để xem lệch")
            print("Chỉ ĐỌC. Agent không ghi xác nhận PI. Cần bác sĩ kiểm chứng.")
        return 0 if st["la_nguon_nguoi_duyet"] else (2 if st["trang_thai"] == KHONG_CO else 1)
    if not a.ghi:
        chu, xem = soan(out, study)
        if chu is None:
            print("• " + xem[0])
            return 2
        sys.stdout.write(chu)
        return 0
    p, tb, ma = ghi(out, study, ghi_de=a.ghi_de)
    print(("✓ " if p else "• ") + tb + (f": {p.as_posix()}" if p else ""))
    return ma


if __name__ == "__main__":
    sys.exit(main())
