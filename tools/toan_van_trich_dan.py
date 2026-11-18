#!/usr/bin/env python3
"""Chốt TOÀN VĂN cho mọi trích dẫn của đề tài nghiên cứu (18/11/2026).

VÌ SAO: bác sĩ 18/11/2026 — «xây dựng đảm bảo tất cả trích dẫn cho nghiên cứu trong hệ thống nghiên cứu phải luôn là
toàn văn, nếu không phải toàn văn và không thể lấy được toàn văn thì loại bỏ». Cùng luật bác sĩ đặt cho BTM ngày
25/10/2026 («Với các trích dẫn cho nghiên cứu không thể lấy được toàn văn hãy loại bỏ luôn cho tôi») — nhưng tới nay
luật chỉ là QUY TRÌNH: đo 18/11 trên thư viện EndNote thật, đề cương nộp C1a có 24/58 TLTK mang toàn văn mà không cổng
nào báo.

BIÊN NHẬN `exports/<mã>/TOAN_VAN_TLTK_<mã>.json` (schema `de_tai/toan_van_tltk/v1`) do repo gốc
`tools/nap_endnote_de_tai.py --ghi-bien-nhan-toan-van` đo trên thư viện EndNote thật + kho toàn văn chung + thư mục
`exports/<mã>/toan_van_tltk/` (máy chạy CI không có EndNote — biên nhận là cầu nối). Mỗi mục:
  {so, tai_lieu, khoa: ["pmid:…" | "doi:…" | "van:<băm>"], toan_van: true|false|null, nguon, tep,
   lan_da_thu: [{lan, ngay, ket_qua}]}

KẾT LUẬN từng TLTK (theo đúng quy trình bác sĩ đặt 25/10: thử hết truy cập mở → làn trình duyệt có uỷ quyền → vẫn
thiếu thì loại):
  · co              — có toàn văn;
  · chua_thu_het    — chưa có, còn làn chưa thử (việc của thu-thu-tai-lieu);
  · khong_lay_duoc  — chưa có VÀ đã thử ĐỦ `LAN_BAT_BUOC` ⇒ PHẢI LOẠI;
  · khong_do        — biên nhận không phủ TLTK này, hoặc biên nhận ghi «không đo được» (null).

CHỐT G10-AUTO-12 (fail-closed): còn trích bài đã ở `loai_bo` của danh mục trích dẫn, hoặc bài «không lấy được toàn văn»
⇒ BLOCK; thiếu biên nhận / TLTK chưa đo / còn làn chưa thử ⇒ REVIEW; mọi TLTK có toàn văn ⇒ PASS.

LOẠI BỎ: `loai-bo --ap-dung` ghi TLTK «không lấy được toàn văn» (có PMID/DOI) vào `loai_bo` của
`DANH_MUC_TRICH_DAN_<mã>.json` — bộ sinh đề cương nộp (`sinh_de_cuong_nop_hoi_dong.py`) đã tự bỏ bài trong `loai_bo`,
nên sinh lại đề cương là TLTK rút khỏi văn bản và đánh số lại. TLTK không định danh (văn bản quy phạm, sách) thì báo để
agent sửa tay văn bản. Chạy khô mặc định; sao lưu danh mục trước khi ghi; không đụng EndNote (gỡ khỏi nhóm do repo gốc).

Ranh giới: chỉ đo trên biên nhận máy ghi, không tự lấy toàn văn, không ký, không đổi decision. Cần bác sĩ kiểm chứng.

Mã thoát `kiem`: 0 mọi TLTK có toàn văn (hoặc không có trích dẫn nào) · 1 còn việc (chưa thử hết làn/chưa đo) hoặc
vi phạm (phải loại) · 2 không đo được (có định danh mà không tách được mục TLTK, biên nhận vắng/hỏng) · 3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import danh_muc_trich_dan as DMT  # noqa: E402

TEP_BIEN_NHAN = "TOAN_VAN_TLTK_{study}.json"
SCHEMA = "de_tai/toan_van_tltk/v1"
#: Hai làn bác sĩ quy định (25/10/2026) trước khi được kết luận «không lấy được toàn văn».
LAN_BAT_BUOC = ("truy_cap_mo", "trinh_duyet")
TEN_LAN = {"truy_cap_mo": "truy cập mở (PMC/Unpaywall/Europe PMC)",
           "trinh_duyet": "trình duyệt có uỷ quyền (hoặc sổ «không truy cập»)"}
KET_LUAN = ("co", "chua_thu_het", "khong_lay_duoc", "khong_do")
TEN_KET_LUAN = {"co": "có toàn văn", "chua_thu_het": "chưa có — còn làn chưa thử",
                "khong_lay_duoc": "KHÔNG lấy được toàn văn — phải loại", "khong_do": "chưa đo"}
#: Văn bản của đề tài có mục TÀI LIỆU THAM KHẢO phải chịu luật toàn văn (tệp vắng / không có mục TLTK thì bỏ qua).
VAN_BAN = (
    ("DE_CUONG_NOP_HOI_DONG_{s}.md", "đề cương nộp Hội đồng"),
    ("G7_A8_MANUSCRIPT_{s}.md", "bản thảo G7"),
)
NHOM_LY_DO = "khong_lay_duoc_toan_van"
LOI_BAC_SI_MAC_DINH = ("Bác sĩ 18/11/2026: «xây dựng đảm bảo tất cả trích dẫn cho nghiên cứu trong hệ thống nghiên cứu "
                       "phải luôn là toàn văn, nếu không phải toàn văn và không thể lấy được toàn thì loại bỏ» (cùng "
                       "luật 25/10/2026)")
_STUDY = re.compile(r"^[A-Za-z0-9._-]+$")
_DONG_TLTK = re.compile(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})\.)\s+(.+)$")


# ── tách TLTK ─────────────────────────────────────────────────────────────────────────────────────────────────────
def chuan_van(van: str) -> str:
    """Chuẩn để băm câu TLTK không định danh: NFC, thường hoá, bỏ dấu câu/khoảng trắng thừa."""
    s = unicodedata.normalize("NFC", str(van or "")).lower()
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"[^\w]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def khoa_tltk(van: str) -> Set[str]:
    """Khoá «pmid:…»/«doi:…» của câu TLTK; không định danh ⇒ «van:<16 hex>» băm câu đã chuẩn hoá."""
    k = DMT.dinh_danh(van)
    return k or {"van:" + hashlib.sha256(chuan_van(van).encode("utf-8")).hexdigest()[:16]}


def tach_tltk(text: str) -> Optional[Dict[int, str]]:
    """{số: câu TLTK} của mục TÀI LIỆU THAM KHẢO / REFERENCES — nhận cả «n. …» (đề cương nộp) lẫn «[n] …» (bản thảo
    G7). None khi văn bản không có mục TLTK. Mục kết thúc ở tiêu đề kế tiếp cùng cấp hoặc cấp cao hơn."""
    dong = str(text or "").splitlines()
    dau = cap = None
    for i, d in enumerate(dong):
        m = DMT._TIEU_DE_TLTK.match(d)
        if m:
            dau, cap = i, len(m.group(1))
            break
    if dau is None:
        return None
    ra: Dict[int, str] = {}
    for d in dong[dau + 1:]:
        m = re.match(r"^(#+)\s", d)
        if m and len(m.group(1)) <= cap:
            break
        mm = _DONG_TLTK.match(d)
        if mm:
            ra.setdefault(int(mm.group(1) or mm.group(2)), mm.group(3).strip())
    return ra


def tltk_de_tai(out_dir: Path, study: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """([{tai_lieu, ten, so, van, khoa}], [tên văn bản có mục TLTK]) — mọi văn bản `VAN_BAN` đang có."""
    ra: List[Dict[str, Any]] = []
    co: List[str] = []
    for mau, nhan in VAN_BAN:
        p = Path(out_dir) / mau.format(s=study)
        try:
            muc = tach_tltk(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if muc is None:
            continue
        co.append(p.name)
        ra += [{"tai_lieu": p.name, "ten": nhan, "so": so, "van": van, "khoa": sorted(khoa_tltk(van))}
               for so, van in sorted(muc.items())]
    return ra, co


# ── biên nhận ─────────────────────────────────────────────────────────────────────────────────────────────────────
def doc_bien_nhan(out_dir: Path, study: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(biên nhận, lỗi). Vắng ⇒ (None, None); có mà hỏng/sai schema ⇒ (None, lỗi) — không đọc được ≠ «không có»."""
    p = Path(out_dir) / TEP_BIEN_NHAN.format(study=study)
    if not p.is_file():
        return None, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{p.name}: không đọc được ({type(exc).__name__})"
    if not isinstance(d, dict) or d.get("schema") != SCHEMA or not isinstance(d.get("muc"), list):
        return None, f"{p.name}: sai khuôn (cần schema «{SCHEMA}» và danh sách «muc»)"
    return d, None


def _ngay(v: Any) -> bool:
    try:
        return dt.date.fromisoformat(str(v)[:10]) <= dt.date.today()
    except (TypeError, ValueError):
        return False


def dung_bien_nhan(out_dir: Path, study: str, *, toan_van: Optional[bool], nguon: str, nguoi_do: str,
                   ghi_chu: str = "") -> Dict[str, Any]:
    """Biên nhận phủ MỌI TLTK hiện hành của đề tài với cùng một trạng thái — cho bộ giả lập và đồ gá kiểm thử (đề tài
    thật: repo gốc đo từng TLTK trên EndNote). Không ghi tệp."""
    tltk, van_ban = tltk_de_tai(out_dir, study)
    return {"schema": SCHEMA, "study": study, "luc": dt.datetime.now().isoformat(timespec="seconds"),
            "nguoi_do": nguoi_do, "ghi_chu": ghi_chu, "tai_lieu": van_ban,
            "muc": [{"so": t["so"], "tai_lieu": t["tai_lieu"], "khoa": t["khoa"], "toan_van": toan_van,
                     "nguon": nguon, "tep": None, "lan_da_thu": []} for t in tltk]}


def ghi_bien_nhan(out_dir: Path, study: str, bien_nhan: Mapping[str, Any]) -> Path:
    p = Path(out_dir) / TEP_BIEN_NHAN.format(study=study)
    p.write_text(json.dumps(bien_nhan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p


def ket_luan_muc(muc: Mapping[str, Any]) -> str:
    """Kết luận MỘT mục biên nhận (xem docstring mô-đun)."""
    tv = muc.get("toan_van")
    if tv is True:
        return "co"
    if tv is not False:
        return "khong_do"
    da = {str(x.get("lan")) for x in muc.get("lan_da_thu") or [] if isinstance(x, dict) and _ngay(x.get("ngay"))}
    return "khong_lay_duoc" if all(lan in da for lan in LAN_BAT_BUOC) else "chua_thu_het"


def _tim_muc(khoa: Sequence[str], bien_nhan: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """Mục biên nhận khớp TLTK theo giao khoá (PMID/DOI/băm câu) — không theo số thứ tự (đánh số lại không làm mất)."""
    k = set(khoa)
    for m in bien_nhan.get("muc") or []:
        if isinstance(m, dict) and k & {str(x).lower() for x in m.get("khoa") or []}:
            return m
    return None


def _doc_van(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def danh_gia(out_dir: Path, study: str) -> Dict[str, Any]:
    """Đánh giá luật toàn văn cho mọi TLTK của đề tài.

    trang_thai: DAT · KHONG_CO_TRICH_DAN (không văn bản nào có mục TLTK lẫn định danh trích dẫn) · CON_VIEC (chưa thử
    hết làn / chưa đo) · VI_PHAM (còn trích bài đã loại hoặc không lấy được toàn văn) · KHONG_DO_DUOC (có định danh mà
    không tách được mục TLTK, hoặc biên nhận vắng/hỏng)."""
    out_dir = Path(out_dir)
    tltk, van_ban = tltk_de_tai(out_dir, study)
    bn, loi = doc_bien_nhan(out_dir, study)
    loai = {str(k).lower(): v for k, v in (DMT.loai_bo(out_dir, study) or {}).items()}
    ra: Dict[str, Any] = {"study": study, "van_ban": van_ban, "bien_nhan": TEP_BIEN_NHAN.format(study=study),
                          "bien_nhan_luc": (bn or {}).get("luc"), "tltk": [], "loi": [loi] if loi else []}
    if not van_ban:
        # Không văn bản nào có mục TLTK: không có định danh trích dẫn nào ⇒ không có gì để kiểm (đạt); CÓ PMID/DOI mà
        # không tách được mục TLTK (tiêu đề lạ, khuôn đánh số lạ) ⇒ KHÔNG ĐO ĐƯỢC — không bao giờ coi là đạt.
        co_dd = sorted({k for mau, _n in VAN_BAN for k in DMT.dinh_danh(_doc_van(out_dir / mau.format(s=study)))})
        if co_dd:
            ra.update(trang_thai="KHONG_DO_DUOC", loi=ra["loi"] + [
                f"văn bản có {len(co_dd)} định danh trích dẫn (vd {', '.join(co_dd[:3])}) nhưng không tách được mục "
                "TÀI LIỆU THAM KHẢO đánh số «n. …»/«[n] …»"])
        else:
            ra.update(trang_thai="KHONG_CO_TRICH_DAN", dem={k: 0 for k in KET_LUAN})
        return ra
    for t in tltk:
        m = _tim_muc(t["khoa"], bn) if bn else None
        kl = ket_luan_muc(m) if m else "khong_do"
        da_loai = sorted(k for k in t["khoa"] if k in loai)
        ra["tltk"].append({**t, "van": t["van"][:160], "ket_luan": kl, "nguon": (m or {}).get("nguon"),
                           "lan_da_thu": (m or {}).get("lan_da_thu") or [], "da_loai_bo": da_loai})
    dem = {k: sum(1 for x in ra["tltk"] if x["ket_luan"] == k) for k in KET_LUAN}
    dem["da_loai_ma_con_trich"] = sum(1 for x in ra["tltk"] if x["da_loai_bo"])
    ra["dem"] = dem
    if bn is None:
        ra["trang_thai"] = "KHONG_DO_DUOC"
        if not loi:
            ra["loi"].append(f"chưa có biên nhận {ra['bien_nhan']} — đo bằng repo gốc: python3 tools/nap_endnote_de_tai"
                             f".py --study {study} --ghi-bien-nhan-toan-van")
    elif dem["khong_lay_duoc"] or dem["da_loai_ma_con_trich"]:
        ra["trang_thai"] = "VI_PHAM"
    elif dem["chua_thu_het"] or dem["khong_do"]:
        ra["trang_thai"] = "CON_VIEC"
    else:
        ra["trang_thai"] = "DAT"
    return ra


def tieu_chi_g10(out_dir: Path, study: str) -> Tuple[str, str]:
    """(PASS|REVIEW|BLOCK, bằng chứng) cho G10-AUTO-12. Bộ đánh giá hỏng ⇒ REVIEW (không đo được ≠ đạt)."""
    try:
        kq = danh_gia(out_dir, study)
    except Exception as exc:  # noqa: BLE001 — lỗi phải hiện ra, không im lặng như «đạt»
        return "REVIEW", f"không chạy được bộ chốt toàn văn: {type(exc).__name__}: {exc}"
    dem = kq.get("dem") or {}
    tom = ""
    if kq.get("tltk"):
        tom = (f"{len(kq['tltk'])} TLTK ({', '.join(kq['van_ban'])}): có toàn văn {dem.get('co', 0)} · còn làn chưa "
               f"thử {dem.get('chua_thu_het', 0)} · chưa đo {dem.get('khong_do', 0)} · không lấy được "
               f"{dem.get('khong_lay_duoc', 0)} · đã loại mà còn trích {dem.get('da_loai_ma_con_trich', 0)}")
    if kq["trang_thai"] == "DAT":
        return "PASS", tom
    if kq["trang_thai"] == "KHONG_CO_TRICH_DAN":
        return "PASS", ("không văn bản nào của đề tài có mục TÀI LIỆU THAM KHẢO hay định danh trích dẫn — không có gì "
                        "để kiểm")
    if kq["trang_thai"] == "VI_PHAM":
        sai = [f"TLTK {x['so']} ({x['tai_lieu']})" for x in kq["tltk"]
               if x["ket_luan"] == "khong_lay_duoc" or x["da_loai_bo"]]
        return "BLOCK", f"{tom} — phải LOẠI: {', '.join(sai[:8])}"
    return "REVIEW", "; ".join([tom] * bool(tom) + kq.get("loi", []))


# ── loại bỏ ───────────────────────────────────────────────────────────────────────────────────────────────────────
def de_xuat_loai_bo(out_dir: Path, study: str) -> Dict[str, Any]:
    """{loai: [mục sẽ ghi vào loai_bo], sua_tay: [TLTK không định danh phải sửa tay văn bản]}."""
    kq = danh_gia(out_dir, study)
    nay = dt.date.today().isoformat()
    loai: List[Dict[str, Any]] = []
    sua_tay: List[str] = []
    da: Set[str] = set()
    for x in kq.get("tltk") or []:
        if x["ket_luan"] != "khong_lay_duoc" or x["da_loai_bo"]:
            continue
        pm = next((k.split(":", 1)[1] for k in x["khoa"] if k.startswith("pmid:")), None)
        doi = next((k.split(":", 1)[1] for k in x["khoa"] if k.startswith("doi:")), None)
        if not (pm or doi):
            sua_tay.append(f"TLTK {x['so']} ({x['tai_lieu']}): {x['van'][:100]}")
            continue
        if (pm or doi) in da:
            continue
        da.add(pm or doi)
        lan = "; ".join(
            f"{TEN_LAN.get(str(y.get('lan')), y.get('lan'))} {y.get('ngay')}: {y.get('ket_qua', '')}".strip()
            for y in x["lan_da_thu"] if isinstance(y, dict))
        loai.append({"pmid": pm, "doi": doi, "vai": "tltk_de_tai", "nhom_ly_do": NHOM_LY_DO,
                     "ly_do": f"Không lấy được toàn văn — đã thử {lan} (TLTK {x['so']} của {x['tai_lieu']})",
                     "ngay": nay})
    return {"trang_thai": kq["trang_thai"], "loai": loai, "sua_tay": sua_tay}


def ap_dung_loai_bo(out_dir: Path, study: str, loi_bac_si: str = LOI_BAC_SI_MAC_DINH) -> Dict[str, Any]:
    """Ghi đề xuất vào `loai_bo` của danh mục trích dẫn (tạo danh mục nếu chưa có); sao lưu bản cũ trước khi ghi."""
    dx = de_xuat_loai_bo(out_dir, study)
    if not dx["loai"]:
        return {**dx, "da_ghi": 0}
    p = Path(out_dir) / DMT.TEP.format(study=study)
    goc = DMT.doc(out_dir, study) or {"schema": "de_tai/danh_muc_trich_dan/v1", "study": study, "trich_dan": []}
    if p.is_file():
        shutil.copy2(p, p.with_name(f"{p.stem}.bak-{dt.datetime.now():%Y%m%d-%H%M%S}-truoc-loai-toan-van.json"))
    goc.setdefault("loai_bo", []).extend(dx["loai"])
    goc["quyet_dinh_loai_bo_toan_van"] = {"ngay": dt.date.today().isoformat(), "loi_bac_si": loi_bac_si,
                                          "cong_cu": "tools/toan_van_trich_dan.py loai-bo --ap-dung"}
    p.write_text(json.dumps(goc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {**dx, "da_ghi": len(dx["loai"]), "tep": p.name}


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _in(kq: Dict[str, Any]) -> None:
    bieu = {"DAT": "🟢", "KHONG_CO_TRICH_DAN": "🟢", "CON_VIEC": "🟠", "VI_PHAM": "🔴",
            "KHONG_DO_DUOC": "⚪"}.get(kq["trang_thai"], "⚪")
    print(f"{bieu} Toàn văn trích dẫn — {kq['study']}: {kq['trang_thai']}")
    dem = kq.get("dem") or {}
    if kq.get("tltk"):
        print("   " + " · ".join(f"{TEN_KET_LUAN[k]} {dem.get(k, 0)}" for k in KET_LUAN)
              + f" · đã loại mà còn trích {dem.get('da_loai_ma_con_trich', 0)}")
    can = [x for x in kq.get("tltk") or [] if x["ket_luan"] != "co" or x["da_loai_bo"]]
    for x in can[:20]:
        them = " · ĐÃ Ở loai_bo MÀ CÒN TRÍCH" if x["da_loai_bo"] else ""
        print(f"   - TLTK {x['so']} ({x['tai_lieu']}): {TEN_KET_LUAN[x['ket_luan']]}{them} — {x['van'][:90]}")
    if len(can) > 20:
        print(f"   … và {len(can) - 20} TLTK nữa (--json để xem đủ)")
    for e in kq.get("loi") or []:
        print(f"   ⚪ {e}")
    print("   Cần bác sĩ kiểm chứng.")


EXPORTS = REPO / "exports"


def main(argv: Optional[Sequence[str]] = None, exports: Optional[Path] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("kiem", "loai-bo"))
    ap.add_argument("--study", required=True)
    ap.add_argument("--ap-dung", action="store_true", help="loai-bo: ghi thật vào danh mục trích dẫn")
    ap.add_argument("--loi", default=LOI_BAC_SI_MAC_DINH, help="loai-bo: nguyên văn lời bác sĩ làm căn cứ")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not _STUDY.match(a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    out = Path(exports or EXPORTS) / a.study
    if not out.is_dir():
        print(f"❌ Không thấy thư mục đề tài {out}")
        return 3
    if a.lenh == "kiem":
        kq = danh_gia(out, a.study)
        print(json.dumps(kq, ensure_ascii=False, indent=1)) if a.json else _in(kq)
        ma = {"DAT": 0, "KHONG_CO_TRICH_DAN": 0, "CON_VIEC": 1, "VI_PHAM": 1}
        return ma.get(kq["trang_thai"], 2)
    kq = ap_dung_loai_bo(out, a.study, a.loi) if a.ap_dung else {**de_xuat_loai_bo(out, a.study), "da_ghi": 0}
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=1))
    else:
        print(f"{'GHI THẬT' if a.ap_dung else 'CHẠY KHÔ'} — loại {len(kq['loai'])} TLTK không lấy được toàn văn"
              + (f" vào {kq.get('tep')}" if kq.get("da_ghi") else ""))
        for x in kq["loai"]:
            print(f"   - {'PMID ' + x['pmid'] if x['pmid'] else 'DOI ' + str(x['doi'])}: {x['ly_do']}")
        for x in kq["sua_tay"]:
            print(f"   ✎ sửa tay văn bản (không định danh): {x}")
        if kq["loai"]:
            print("   Sau khi ghi: sinh lại đề cương nộp (sinh_de_cuong_nop_hoi_dong.py --study <mã> --ghi) để TLTK "
                  "rút khỏi văn bản; gỡ khỏi nhóm EndNote của đề tài ở repo gốc.")
        if not a.ap_dung and kq["loai"]:
            print("   Thêm --ap-dung để ghi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
