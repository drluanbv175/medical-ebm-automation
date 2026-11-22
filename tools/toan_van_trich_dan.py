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

GIỮ TRÍCH DẪN ĐẠT CHUẨN (bác sĩ 18/11/2026, RIÊNG từng đề tài — C1a: «Riêng với đề tài C1a hãy giữ lại trích dẫn đủ
tiêu chuẩn của nghiên cứu y khoa chuẩn»): TLTK chưa có toàn văn vẫn được GIỮ khi bác sĩ cho phép ở
`exports/<mã>/GIU_TRICH_DAN_CHUAN_<mã>.json` (schema `de_tai/giu_trich_dan_chuan/v1`, bắt buộc nguyên văn lời bác sĩ) VÀ
TLTK đạt ĐỦ ba tiêu chí chuẩn trích dẫn — đo bằng máy, không tin lời khai trong tệp:
  · dinh_danh  — PMID phân giải trong biên nhận A12 (khớp DOI hoặc tiêu đề) / DOI có bản ghi Crossref khớp tiêu đề +
                 năm / văn bản không định danh nhận diện được cơ quan ban hành + số hiệu (văn bản quy phạm) hoặc tổ chức
                 y tế quốc tế là nhà xuất bản;
  · rut_bai    — đã kiểm rút bài (sổ `KIEM_RUT_BAI_TRICH_DAN_<mã>.json` hoặc biên nhận A12) trong
                 `HAN_RUT_BAI_NGAY` ngày, không rút / không «expression of concern» (văn bản quy phạm, tài liệu tổ
                 chức quốc tế: không áp dụng);
  · loai_nguon — bài tạp chí có bình duyệt, sách học thuật, văn bản quy phạm của cơ quan nhà nước, tài liệu tổ chức y tế
                 quốc tế (`LOAI_NGUON_CHUAN`); tiền ấn phẩm chưa bình duyệt KHÔNG đạt.
`giu-chuan --loi "<nguyên văn>"` đo đủ ba tiêu chí (DOI tra Crossref thật) rồi đề xuất / `--ap-dung` ghi tệp; cổng đo
lại mọi lần chạy: bài đã bị rút ⇒ quyền giữ mất hiệu lực (BLOCK); kiểm rút bài quá hạn/vắng ⇒ REVIEW. Toàn TLTK còn
lại có toàn văn hoặc được giữ hợp lệ ⇒ `DAT_CO_GIU` ⇒ G10-AUTO-12 PASS kèm số TLTK giữ (không trông như mọi bài có
toàn văn).
Được giữ KHÔNG miễn việc tìm toàn văn: làn chưa thử vẫn báo để thu-thu-tai-lieu thử tiếp.

Ranh giới: chỉ đo trên biên nhận máy ghi, không tự lấy toàn văn, không ký, không đổi decision. Cần bác sĩ kiểm chứng.

Mã thoát `kiem`: 0 mọi TLTK có toàn văn hoặc được giữ hợp lệ (hoặc không có trích dẫn nào) · 1 còn việc (chưa thử hết
làn/chưa đo) hoặc
vi phạm (phải loại) · 2 không đo được (có định danh mà không tách được mục TLTK, biên nhận vắng/hỏng) · 3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
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

# Giữ trích dẫn đạt chuẩn khi chưa có toàn văn (xem docstring mô-đun).
TEP_GIU = "GIU_TRICH_DAN_CHUAN_{study}.json"
SCHEMA_GIU = "de_tai/giu_trich_dan_chuan/v1"
#: Hạn của kết luận rút bài (CLAUDE.md §6.4: 30 ngày cho trạng thái rút bài).
HAN_RUT_BAI_NGAY = 30
LOAI_NGUON_CHUAN = {
    "bai_tap_chi": "bài tạp chí có bình duyệt",
    "sach_hoc_thuat": "sách chuyên khảo của nhà xuất bản học thuật",
    "van_ban_phap_quy": "văn bản quy phạm/hướng dẫn của cơ quan nhà nước",
    "tai_lieu_to_chuc_quoc_te": "tài liệu của tổ chức y tế quốc tế",
}
#: Loại xuất bản của Crossref ⇒ loại nguồn chuẩn; loại khác (posted-content = tiền ấn phẩm, dataset…) không đạt.
_LOAI_CROSSREF = {"journal-article": "bai_tap_chi", "book": "sach_hoc_thuat", "monograph": "sach_hoc_thuat",
                  "edited-book": "sach_hoc_thuat", "reference-book": "sach_hoc_thuat",
                  "book-chapter": "sach_hoc_thuat"}
_TIEN_AN_PHAM = re.compile(r"medrxiv|biorxiv|research ?square|preprints?\b|ssrn|arxiv", re.I)
#: Văn bản quy phạm: «<Cơ quan>. <Loại văn bản> số <số hiệu> …» — cơ quan nhà nước đứng đầu câu TLTK.
_VAN_BAN_PHAP_QUY = re.compile(
    r"^\s*(?:Bộ Y tế|Bộ [A-ZĐ][\w ]{2,40}|Chính phủ|Quốc hội|Thủ tướng Chính phủ|Cục [A-ZĐ][\w ]{2,60})\.\s+"
    r"(?:Quyết định|Thông tư(?: liên tịch)?|Nghị định|Luật|Chỉ thị|Công văn|Hướng dẫn)\s+(?:số\s+)?\d+[\w/.-]*")
#: Tài liệu tổ chức y tế quốc tế: tổ chức là NHÀ XUẤT BẢN («Nơi: World Health Organization; năm»).
_NXB_TO_CHUC = re.compile(r":\s*(?:World Health Organization|Tổ chức Y tế Thế giới|WHO Regional Office[\w ]*)"
                          r"[^;]{0,60};\s*(?:19|20)\d{2}")


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


# ── giữ trích dẫn đạt chuẩn khi chưa có toàn văn ──────────────────────────────────────────────────────────────────
_DUONG_TINH = ("retracted", "expression_of_concern")
_KHONG_RUT = ("ok", "correction")


def doc_giu(out_dir: Path, study: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(tệp giữ, lỗi). Vắng ⇒ (None, None). Hỏng / sai khuôn / sai đề tài / thiếu nguyên văn lời bác sĩ ⇒ (None, lỗi):
    không giữ TLTK nào (fail-closed — quyền giữ là quyết định của bác sĩ, không có lời thì không có quyền)."""
    p = Path(out_dir) / TEP_GIU.format(study=study)
    if not p.is_file():
        return None, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{p.name}: không đọc được ({type(exc).__name__}) — không giữ TLTK nào"
    if (not isinstance(d, dict) or d.get("schema") != SCHEMA_GIU or d.get("study") != study
            or not isinstance(d.get("muc"), list)):
        return None, (f"{p.name}: sai khuôn (cần schema «{SCHEMA_GIU}», study «{study}», danh sách «muc») — không giữ "
                      "TLTK nào")
    if not str(d.get("loi_bac_si") or "").strip():
        return None, f"{p.name}: thiếu nguyên văn lời bác sĩ («loi_bac_si») — không giữ TLTK nào"
    return d, None


def _tuoi_ngay(v: Any) -> Optional[int]:
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(v)[:10])).days
    except (TypeError, ValueError):
        return None


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _gop_rut(a: Optional[Tuple[str, str, Optional[int]]],
             b: Optional[Tuple[str, str, Optional[int]]]) -> Optional[Tuple[str, str, Optional[int]]]:
    """Gộp BẤT ĐỐI XỨNG (CLAUDE.md §6.4): tín hiệu DƯƠNG từ bất kỳ nguồn nào là nhận; giữa hai kết luận «không rút» lấy
    bản mới hơn; không kết luận được thì không thay được kết luận đã có."""
    if a is None or b is None:
        return a or b
    for x in (a, b):
        if x[0] in _DUONG_TINH:
            return x
    co = [x for x in (a, b) if x[0] in _KHONG_RUT]
    if not co:
        return a
    return min(co, key=lambda x: x[2] if x[2] is not None and x[2] >= 0 else 10 ** 6)


def so_xac_minh(out_dir: Path, study: str) -> Dict[str, Any]:
    """{meta: {pmid: bản ghi A12}, rut: {«pmid:…»/«doi:…»: (trạng thái, tệp nguồn, tuổi ngày)}} — từ biên nhận A12 +
    sổ kiểm rút bài theo từng mã (`tools/kiem_rut_bai_trich_dan.py`)."""
    out_dir = Path(out_dir)
    a12m = _doc_json(out_dir / "A12_METADATA_RECEIPT.json")
    a12r = _doc_json(out_dir / "A12_RETRACTION_RECEIPT.json")
    so = _doc_json(out_dir / f"KIEM_RUT_BAI_TRICH_DAN_{study}.json")
    meta = a12m.get("metadata") if isinstance(a12m.get("metadata"), dict) else {}
    rut: Dict[str, Tuple[str, str, Optional[int]]] = {}
    nguon = ((a12r.get("results"), "A12_RETRACTION_RECEIPT.json", _tuoi_ngay(a12r.get("checked_at_utc")), "pmid:"),
             (so.get("ket_qua"), f"KIEM_RUT_BAI_TRICH_DAN_{study}.json", _tuoi_ngay(so.get("checked_at")), ""))
    for kq, ten, tuoi, tien_to in nguon:
        for k, v in (kq.items() if isinstance(kq, dict) else ()):
            if isinstance(v, dict):
                khoa = (tien_to + str(k)).lower()
                rut[khoa] = _gop_rut(rut.get(khoa), (str(v.get("status")), ten, tuoi))
    return {"meta": meta, "rut": rut}


def _kiem_rut(khoa: Sequence[str], so: Mapping[str, Any]) -> Tuple[str, str]:
    """(ok|rut|cu|chua, mô tả) — kết luận rút bài của MỘT TLTK theo mọi định danh của nó."""
    kq = [so["rut"][k] for k in khoa if k in so["rut"]]
    if not kq:
        return "chua", "chưa có kết luận rút bài (chạy tools/kiem_rut_bai_trich_dan.py --study <mã> --ghi)"
    duong = next((x for x in kq if x[0] in _DUONG_TINH), None)
    if duong:
        return "rut", f"«{duong[0]}» theo {duong[1]}"
    tot = [x for x in kq if x[0] in _KHONG_RUT]
    if not tot:
        return "chua", f"nguồn kiểm rút bài không kết luận được ({', '.join(sorted({x[0] for x in kq}))})"
    moi = min(tot, key=lambda x: x[2] if x[2] is not None and x[2] >= 0 else 10 ** 6)
    if moi[2] is None or moi[2] < 0 or moi[2] > HAN_RUT_BAI_NGAY:
        return "cu", (f"kết luận rút bài «{moi[0]}» ({moi[1]}) đã {moi[2]} ngày, quá hạn {HAN_RUT_BAI_NGAY} ngày — "
                      "kiểm lại bằng tools/kiem_rut_bai_trich_dan.py --study <mã> --ghi")
    return "ok", f"không rút («{moi[0]}», {moi[1]}, {moi[2]} ngày trước)"


def _ty_le_tieu_de(tieu_de: Any, van: str) -> float:
    """Tỷ lệ từ (> 2 ký tự) của tiêu đề có mặt trong câu TLTK."""
    t = [w for w in chuan_van(str(tieu_de or "")).split() if len(w) > 2]
    v = set(chuan_van(van).split())
    return sum(1 for w in t if w in v) / len(t) if t else 0.0


def tra_crossref(doi: str) -> Optional[Dict[str, Any]]:
    """Bản ghi Crossref `GET /works/{doi}` (khoá «message») hoặc None — tra CHÍNH XÁC một DOI đã biết."""
    from urllib.parse import quote  # noqa: PLC0415

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from app.utils.http import HttpClient  # noqa: PLC0415

    data = HttpClient().get_json("https://api.crossref.org/works/" + quote(doi, safe=""))
    it = (data or {}).get("message") if isinstance(data, dict) else None
    return it if isinstance(it, dict) else None


def tieu_chuan_trich_dan(khoa: Sequence[str], van: str, so: Mapping[str, Any], *,
                         tra_doi: Optional[Any] = None) -> Dict[str, Any]:
    """Đo BA tiêu chí chuẩn trích dẫn (dinh_danh · rut_bai · loai_nguon) cho MỘT TLTK.

    `tra_doi(doi)` → bản ghi Crossref | None; None (không truyền) ⇒ TLTK chỉ có DOI «chưa tra được» (không đạt)."""
    pm = next((k.split(":", 1)[1] for k in khoa if k.startswith("pmid:")), None)
    doi = next((k.split(":", 1)[1] for k in khoa if k.startswith("doi:")), None)
    tc: Dict[str, Tuple[bool, str]] = {}
    loai: Optional[str] = None
    rut = "khong_ap_dung"
    if pm:
        md = so["meta"].get(pm)
        if not isinstance(md, dict) or md.get("status") != "resolved":
            tc["dinh_danh"] = (False, f"PMID {pm} chưa phân giải trong A12_METADATA_RECEIPT.json")
            tc["loai_nguon"] = (False, "không đo được (thiếu bản ghi PubMed)")
        else:
            khop_doi = bool(doi) and str(md.get("doi") or "").lower() == doi
            tl = _ty_le_tieu_de(md.get("title"), van)
            tc["dinh_danh"] = (khop_doi or tl >= 0.6, f"PubMed PMID {pm}: "
                               + ("khớp DOI" if khop_doi else f"khớp tiêu đề {tl:.2f} (cần ≥ 0,60)"))
            tap_chi = str(md.get("journal") or "")
            loai = "bai_tap_chi" if tap_chi and not _TIEN_AN_PHAM.search(tap_chi) else None
            tc["loai_nguon"] = (loai is not None, f"bài tạp chí — {tap_chi} {md.get('year') or ''}".strip() if loai
                                else f"không phải tạp chí có bình duyệt ({tap_chi or 'không rõ tạp chí'})")
    elif doi:
        cr = None
        if tra_doi is not None:
            try:
                cr = tra_doi(doi)
            except Exception:  # noqa: BLE001 — lỗi mạng = không đo được, không phải «đạt»
                cr = None
        if not cr:
            tc["dinh_danh"] = (False, f"không lấy được bản ghi Crossref cho DOI {doi}")
            tc["loai_nguon"] = (False, "không đo được (thiếu bản ghi Crossref)")
        else:
            nam = ((cr.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            tl = _ty_le_tieu_de((cr.get("title") or [""])[0], van)
            co_nam = bool(nam) and str(nam) in van
            tc["dinh_danh"] = (tl >= 0.8 and co_nam, f"Crossref DOI {doi}: khớp tiêu đề {tl:.2f} (cần ≥ 0,80), năm "
                               f"{nam} " + ("có" if co_nam else "KHÔNG có") + " trong câu TLTK")
            kieu = str(cr.get("type") or "")
            noi = html.unescape(str((cr.get("container-title") or [""])[0] or cr.get("publisher") or ""))
            loai = _LOAI_CROSSREF.get(kieu) if not _TIEN_AN_PHAM.search(noi) else None
            tc["loai_nguon"] = (loai is not None, f"{kieu or 'không rõ loại'} — {noi or 'không rõ nơi xuất bản'}")
    else:
        if _VAN_BAN_PHAP_QUY.search(van):
            loai, mo = "van_ban_phap_quy", "văn bản quy phạm: nhận diện cơ quan ban hành + số hiệu"
        elif _NXB_TO_CHUC.search(van):
            loai, mo = "tai_lieu_to_chuc_quoc_te", "tổ chức y tế quốc tế là nhà xuất bản (kèm năm)"
        else:
            mo = "không định danh, không nhận diện được cơ quan ban hành hay tổ chức xuất bản"
        tc["dinh_danh"] = (loai is not None, mo)
        tc["loai_nguon"] = (loai is not None, LOAI_NGUON_CHUAN.get(loai or "", "không rõ loại nguồn"))
        tc["rut_bai"] = (loai is not None, "không áp dụng (văn bản quy phạm / tài liệu tổ chức)" if loai else "—")
    if "rut_bai" not in tc:
        rut, mo = _kiem_rut([str(k).lower() for k in khoa], so)
        tc["rut_bai"] = (rut == "ok", mo)
    return {"dat": all(v[0] for v in tc.values()), "loai_nguon": loai, "rut": rut,
            "tieu_chi": {k: {"dat": v[0], "mo_ta": v[1]} for k, v in tc.items()}}


def _giu_hop_le(t: Mapping[str, Any], muc_giu: Mapping[str, Any], so: Mapping[str, Any]) -> Tuple[str, str]:
    """(giu|cho_kiem|vo_hieu|khong_dat, lý do) — cổng ĐO LẠI tiêu chí mỗi lần chạy, không tin lời khai trong tệp giữ.

    Riêng định danh + loại nguồn của TLTK CHỈ có DOI (cổng chạy ngoại tuyến, không tra Crossref) lấy bằng chứng máy đã
    ghi lúc `giu-chuan` tra Crossref thật; rút bài luôn đo lại từ sổ kiểm rút bài."""
    tc = tieu_chuan_trich_dan(t["khoa"], t["van"], so)
    chi_doi = not any(k.startswith("pmid:") for k in t["khoa"]) and any(k.startswith("doi:") for k in t["khoa"])
    if chi_doi:
        bc = muc_giu.get("tieu_chi") if isinstance(muc_giu.get("tieu_chi"), dict) else {}
        for k in ("dinh_danh", "loai_nguon"):
            x = bc.get(k) if isinstance(bc.get(k), dict) else {}
            tc["tieu_chi"][k] = {"dat": x.get("dat") is True and muc_giu.get("loai_nguon") in LOAI_NGUON_CHUAN,
                                 "mo_ta": str(x.get("mo_ta") or "thiếu bằng chứng tra Crossref trong tệp giữ")}
    if tc["rut"] == "rut":
        return "vo_hieu", f"bài ĐÃ BỊ RÚT/có thông báo quan ngại — mất quyền giữ ({tc['tieu_chi']['rut_bai']['mo_ta']})"
    hong = [f"{k}: {v['mo_ta']}" for k, v in tc["tieu_chi"].items() if k != "rut_bai" and not v["dat"]]
    if hong:
        return "khong_dat", "không đạt chuẩn trích dẫn — " + "; ".join(hong)
    if not tc["tieu_chi"]["rut_bai"]["dat"]:
        return "cho_kiem", tc["tieu_chi"]["rut_bai"]["mo_ta"]
    return "giu", "đạt chuẩn trích dẫn — " + "; ".join(v["mo_ta"] for v in tc["tieu_chi"].values())


def danh_gia(out_dir: Path, study: str) -> Dict[str, Any]:
    """Đánh giá luật toàn văn cho mọi TLTK của đề tài.

    trang_thai: DAT · DAT_CO_GIU (mọi TLTK có toàn văn hoặc được bác sĩ giữ hợp lệ, có ít nhất một bài giữ) ·
    KHONG_CO_TRICH_DAN (không văn bản nào có mục TLTK lẫn định danh trích dẫn) · CON_VIEC (chưa thử hết làn / chưa đo /
    bài giữ chờ kiểm lại rút bài) · VI_PHAM (còn trích bài đã loại, không lấy được toàn văn mà không được giữ hợp lệ,
    hoặc bài giữ đã bị rút) · KHONG_DO_DUOC (có định danh mà không tách được mục TLTK, hoặc biên nhận vắng/hỏng)."""
    out_dir = Path(out_dir)
    tltk, van_ban = tltk_de_tai(out_dir, study)
    bn, loi = doc_bien_nhan(out_dir, study)
    giu_d, loi_giu = doc_giu(out_dir, study)
    so = so_xac_minh(out_dir, study) if giu_d else None
    loai = {str(k).lower(): v for k, v in (DMT.loai_bo(out_dir, study) or {}).items()}
    ra: Dict[str, Any] = {"study": study, "van_ban": van_ban, "bien_nhan": TEP_BIEN_NHAN.format(study=study),
                          "bien_nhan_luc": (bn or {}).get("luc"), "tltk": [],
                          "giu_tep": TEP_GIU.format(study=study) if giu_d else None,
                          "loi": [x for x in (loi, loi_giu) if x]}
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
        giu = giu_ly_do = None
        if giu_d and so is not None and kl in ("chua_thu_het", "khong_lay_duoc") and not da_loai:
            mg = _tim_muc(t["khoa"], giu_d)
            if mg:
                giu, giu_ly_do = _giu_hop_le(t, mg, so)
        ra["tltk"].append({**t, "van": t["van"][:160], "ket_luan": kl, "nguon": (m or {}).get("nguon"),
                           "lan_da_thu": (m or {}).get("lan_da_thu") or [], "da_loai_bo": da_loai,
                           "giu": giu, "giu_ly_do": giu_ly_do})
    dem = {k: sum(1 for x in ra["tltk"] if x["ket_luan"] == k) for k in KET_LUAN}
    dem["da_loai_ma_con_trich"] = sum(1 for x in ra["tltk"] if x["da_loai_bo"])
    for k in ("giu", "cho_kiem", "vo_hieu", "khong_dat"):
        dem["giu_" + k] = sum(1 for x in ra["tltk"] if x["giu"] == k)
    ra["dem"] = dem
    duoc_giu = ("giu", "cho_kiem")
    vi_pham = [x for x in ra["tltk"] if x["da_loai_bo"] or x["giu"] == "vo_hieu"
               or (x["ket_luan"] == "khong_lay_duoc" and x["giu"] not in duoc_giu)]
    con_viec = [x for x in ra["tltk"] if x["giu"] == "cho_kiem"
                or (x["ket_luan"] in ("chua_thu_het", "khong_do") and x["giu"] not in duoc_giu)]
    if bn is None:
        ra["trang_thai"] = "KHONG_DO_DUOC"
        if not loi:
            ra["loi"].append(f"chưa có biên nhận {ra['bien_nhan']} — đo bằng repo gốc: python3 tools/nap_endnote_de_tai"
                             f".py --study {study} --ghi-bien-nhan-toan-van")
    elif vi_pham:
        ra["trang_thai"] = "VI_PHAM"
    elif con_viec:
        ra["trang_thai"] = "CON_VIEC"
    else:
        ra["trang_thai"] = "DAT_CO_GIU" if dem["giu_giu"] else "DAT"
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
        if kq.get("giu_tep"):
            tom += (f" · bác sĩ cho giữ (đạt chuẩn, chưa có toàn văn) {dem.get('giu_giu', 0)} · giữ chờ kiểm lại "
                    f"rút bài {dem.get('giu_cho_kiem', 0)} · giữ mất hiệu lực vì bị rút {dem.get('giu_vo_hieu', 0)} · "
                    f"không đạt chuẩn để giữ {dem.get('giu_khong_dat', 0)}")
    if kq["trang_thai"] == "DAT":
        return "PASS", tom
    if kq["trang_thai"] == "DAT_CO_GIU":
        giu = [str(x["so"]) for x in kq["tltk"] if x["giu"] == "giu"]
        return "PASS", (f"{tom} — mọi TLTK còn lại có toàn văn; TLTK {', '.join(giu)} được giữ theo "
                        f"{kq['giu_tep']} (lời bác sĩ, đạt đủ ba tiêu chí chuẩn trích dẫn) dù chưa có toàn văn")
    if kq["trang_thai"] == "KHONG_CO_TRICH_DAN":
        return "PASS", ("không văn bản nào của đề tài có mục TÀI LIỆU THAM KHẢO hay định danh trích dẫn — không có gì "
                        "để kiểm")
    if kq["trang_thai"] == "VI_PHAM":
        sai = [f"TLTK {x['so']} ({x['tai_lieu']})" + (" — bài giữ ĐÃ BỊ RÚT" if x["giu"] == "vo_hieu" else "")
               for x in kq["tltk"] if x["da_loai_bo"] or x["giu"] == "vo_hieu"
               or (x["ket_luan"] == "khong_lay_duoc" and x["giu"] not in ("giu", "cho_kiem"))]
        return "BLOCK", f"{tom} — phải LOẠI: {', '.join(sai[:8])}"
    cho = [f"TLTK {x['so']}: {x['giu_ly_do']}" for x in kq.get("tltk") or [] if x.get("giu") == "cho_kiem"]
    return "REVIEW", "; ".join([tom] * bool(tom) + cho[:3] + kq.get("loi", []))


# ── loại bỏ ───────────────────────────────────────────────────────────────────────────────────────────────────────
def de_xuat_loai_bo(out_dir: Path, study: str) -> Dict[str, Any]:
    """{loai: [mục sẽ ghi vào loai_bo], sua_tay: [TLTK không định danh phải sửa tay văn bản]}."""
    kq = danh_gia(out_dir, study)
    nay = dt.date.today().isoformat()
    loai: List[Dict[str, Any]] = []
    sua_tay: List[str] = []
    da: Set[str] = set()
    for x in kq.get("tltk") or []:
        if x["ket_luan"] != "khong_lay_duoc" or x["da_loai_bo"] or x.get("giu") in ("giu", "cho_kiem"):
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


# ── giữ trích dẫn đạt chuẩn: đề xuất / ghi ────────────────────────────────────────────────────────────────────────
def de_xuat_giu(out_dir: Path, study: str, tra_doi: Optional[Any] = tra_crossref) -> Dict[str, Any]:
    """{giu: [mục đạt đủ ba tiêu chí], khong_dat: [{so, ly_do}]} cho mọi TLTK chưa có toàn văn (còn làn chưa thử hoặc
    không lấy được) — đo trên câu TLTK ĐẦY ĐỦ; DOI tra Crossref thật qua `tra_doi`."""
    out_dir = Path(out_dir)
    kq = danh_gia(out_dir, study)
    so = so_xac_minh(out_dir, study)
    day = {(t["tai_lieu"], t["so"]): t["van"] for t in tltk_de_tai(out_dir, study)[0]}
    nay = dt.date.today().isoformat()
    giu: List[Dict[str, Any]] = []
    khong_dat: List[Dict[str, Any]] = []
    for x in kq.get("tltk") or []:
        if x["ket_luan"] not in ("chua_thu_het", "khong_lay_duoc") or x["da_loai_bo"]:
            continue
        van = day.get((x["tai_lieu"], x["so"]), x["van"])
        tc = tieu_chuan_trich_dan(x["khoa"], van, so, tra_doi=tra_doi)
        if tc["dat"]:
            giu.append({"so": x["so"], "tai_lieu": x["tai_lieu"], "khoa": x["khoa"], "ket_luan_toan_van": x["ket_luan"],
                        "loai_nguon": tc["loai_nguon"], "tieu_chi": tc["tieu_chi"], "ngay": nay})
        else:
            khong_dat.append({"so": x["so"], "tai_lieu": x["tai_lieu"],
                              "ly_do": "; ".join(f"{k}: {v['mo_ta']}" for k, v in tc["tieu_chi"].items()
                                                 if not v["dat"])})
    return {"trang_thai": kq["trang_thai"], "giu": giu, "khong_dat": khong_dat}


def ap_dung_giu(out_dir: Path, study: str, loi_bac_si: str, tra_doi: Optional[Any] = tra_crossref) -> Dict[str, Any]:
    """Ghi `GIU_TRICH_DAN_CHUAN_<mã>.json` CHỈ với TLTK đạt đủ ba tiêu chí; bắt buộc nguyên văn lời bác sĩ; sao lưu tệp
    cũ trước khi ghi đè."""
    if not str(loi_bac_si or "").strip():
        raise ValueError("thiếu nguyên văn lời bác sĩ (--loi) — quyền giữ trích dẫn là quyết định của bác sĩ")
    dx = de_xuat_giu(out_dir, study, tra_doi=tra_doi)
    p = Path(out_dir) / TEP_GIU.format(study=study)
    if not dx["giu"]:
        return {**dx, "da_ghi": 0}
    if p.is_file():
        shutil.copy2(p, p.with_name(f"{p.stem}.bak-{dt.datetime.now():%Y%m%d-%H%M%S}.json"))
    d = {"schema": SCHEMA_GIU, "study": study, "ngay": dt.date.today().isoformat(), "loi_bac_si": loi_bac_si.strip(),
         "cong_cu": "tools/toan_van_trich_dan.py giu-chuan --ap-dung",
         "tieu_chi": {"dinh_danh": ("PMID phân giải (A12) khớp DOI/tiêu đề · DOI có bản ghi Crossref khớp tiêu đề "
                                    "+ năm · văn bản không định danh nhận diện được cơ quan ban hành + số hiệu hoặc tổ "
                                    "chức y tế quốc tế là nhà xuất bản"),
                      "rut_bai": f"đã kiểm, không rút, trong {HAN_RUT_BAI_NGAY} ngày",
                      "loai_nguon": " · ".join(LOAI_NGUON_CHUAN.values())},
         "muc": dx["giu"]}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {**dx, "da_ghi": len(dx["giu"]), "tep": p.name}


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _in(kq: Dict[str, Any]) -> None:
    bieu = {"DAT": "🟢", "DAT_CO_GIU": "🟢", "KHONG_CO_TRICH_DAN": "🟢", "CON_VIEC": "🟠", "VI_PHAM": "🔴",
            "KHONG_DO_DUOC": "⚪"}.get(kq["trang_thai"], "⚪")
    print(f"{bieu} Toàn văn trích dẫn — {kq['study']}: {kq['trang_thai']}")
    dem = kq.get("dem") or {}
    # Có tệp giữ: «không lấy được» chưa chắc «phải loại» (bài được giữ hợp lệ) — nhãn trung tính, số giữ in dòng dưới.
    ten = {**TEN_KET_LUAN, "khong_lay_duoc": "KHÔNG lấy được toàn văn"} if kq.get("giu_tep") else TEN_KET_LUAN
    if kq.get("tltk"):
        print("   " + " · ".join(f"{ten[k]} {dem.get(k, 0)}" for k in KET_LUAN)
              + f" · đã loại mà còn trích {dem.get('da_loai_ma_con_trich', 0)}")
        if kq.get("giu_tep"):
            print(f"   Giữ theo lời bác sĩ ({kq['giu_tep']}): hợp lệ {dem.get('giu_giu', 0)} · chờ kiểm lại rút bài "
                  f"{dem.get('giu_cho_kiem', 0)} · mất hiệu lực vì bị rút {dem.get('giu_vo_hieu', 0)} · không đạt "
                  f"chuẩn {dem.get('giu_khong_dat', 0)}")
    nhan_giu = {"giu": " · GIỮ (đạt chuẩn, lời bác sĩ)", "cho_kiem": " · GIỮ — chờ kiểm lại rút bài",
                "vo_hieu": " · GIỮ MẤT HIỆU LỰC: bài đã bị rút", "khong_dat": " · không đạt chuẩn để giữ"}
    can = [x for x in kq.get("tltk") or [] if x["ket_luan"] != "co" or x["da_loai_bo"]]
    for x in can[:20]:
        them = (" · ĐÃ Ở loai_bo MÀ CÒN TRÍCH" if x["da_loai_bo"] else "") + nhan_giu.get(x.get("giu") or "", "")
        nhan = ten[x["ket_luan"]] if x.get("giu") in ("giu", "cho_kiem") else TEN_KET_LUAN[x["ket_luan"]]
        print(f"   - TLTK {x['so']} ({x['tai_lieu']}): {nhan}{them} — {x['van'][:90]}")
    if len(can) > 20:
        print(f"   … và {len(can) - 20} TLTK nữa (--json để xem đủ)")
    for e in kq.get("loi") or []:
        print(f"   ⚪ {e}")
    print("   Cần bác sĩ kiểm chứng.")


EXPORTS = REPO / "exports"


# ─────────────────── SỔ ĐỊNH DANH VÀ SIÊU DỮ LIỆU TLTK (22/11/2026) ───────────────────
# VÌ SAO (bác sĩ 22/11/2026: «Tài liệu tham khảo, trích dẫn … hoàn thiện đúng chuẩn»): (b) mỗi tài liệu phải có
# định danh KIỂM ĐƯỢC — bài tạp chí: DOI (Crossref, kể cả tạp chí trong nước có tiền tố 10.51298, 10.52163…) và
# PMID/PMCID; văn bản quy phạm: số hiệu và đường dẫn nguồn chính thức; sách: ISBN — không tìm được thì GHI LÝ DO, không
# bịa; (c) siêu dữ liệu khớp nguồn — năm, tập, số, trang, tiêu đề đối chiếu với Crossref (mục có DOI) và PubMed (mục có
# PMID, qua idconv lấy PMCID). Sổ `exports/<mã>/SO_DINH_DANH_TLTK_<mã>.json` gắn băm dòng TLTK: dòng đổi ⇒ mục sổ hết
# hiệu lực. K13 (`kiem_de_cuong_nop_hoi_dong.loi_k13_nlm`) đọc sổ: lệch nguồn ⇒ lỗi kèm giá trị nguồn; bài tạp chí thiếu
# trang mà Crossref CÓ trang ⇒ lỗi kèm trang nguồn; Crossref xác nhận nguồn KHÔNG ghi trang ⇒ không đòi (theo nguồn,
# không miễn tay).
TEP_DINH_DANH = "SO_DINH_DANH_TLTK_{study}.json"
SCHEMA_DINH_DANH = "de_tai/so_dinh_danh_tltk/v1"
NGUONG_TIEU_DE = 0.85


def bam_dong(dong: str) -> str:
    return hashlib.sha256(chuan_van(dong).encode("utf-8")).hexdigest()[:16]


def _tieu_de_tltk(dong: str) -> str:
    """Tiêu đề = câu thứ hai của dòng Vancouver («Tác giả. Tiêu đề. Tạp chí. …»)."""
    phan = [x.strip() for x in re.split(r"(?<=[.?!])\s+(?=[A-ZĐÀ-Ỹ0-9\[])", str(dong or "")) if x.strip()]
    return phan[1].rstrip(".") if len(phan) > 1 else ""


def _ty_le_chuoi(a: str, b: str) -> float:
    import difflib  # noqa: PLC0415

    return difflib.SequenceMatcher(None, chuan_van(a), chuan_van(b)).ratio()


def _vi_tri_tltk(dong: str) -> Dict[str, Optional[str]]:
    """{nam, tap, so, trang} của dòng bài tạp chí «năm;tập(số):trang»."""
    m = re.search(r"(?<!\d)((?:19|20)\d{2})(?:\s+[A-Z][a-z]{2}(?:\s+\d{1,2})?)?\s*;\s*([\w-]+)?\s*(?:\(([^)]*)\))?"
                  r"(?:\s*:\s*([eSA-Za-z]{0,2}\d[\w-]*))?", dong)
    if not m:
        m2 = re.search(r"(?<!\d)((?:19|20)\d{2})\s*:\s*([eSA-Za-z]{0,2}\d[\w-]*)", dong)
        return {"nam": m2.group(1), "tap": None, "so": None, "trang": m2.group(2)} if m2 else \
            {"nam": (re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", dong) or [None])[-1], "tap": None, "so": None,
             "trang": None}
    return {"nam": m.group(1), "tap": m.group(2), "so": m.group(3), "trang": m.group(4)}


def _trang_bang_nhau(a: str, b: str) -> bool:
    """«785-94» ≡ «785-794» (NLM rút gọn chữ số đầu trùng); «b2393-b2393» ≡ «b2393»; nguồn chỉ ghi TRANG ĐẦU
    («1045») khớp dòng «1045-1056» (Crossref thường chỉ nộp trang đầu)."""
    def _mo(x: str) -> Tuple[str, str]:
        x = re.sub(r"\s+", "", str(x or "")).replace("–", "-")
        dau, _, cuoi = x.partition("-")
        if cuoi and len(cuoi) < len(dau) and dau.isdigit() and cuoi.isdigit():
            cuoi = dau[: len(dau) - len(cuoi)] + cuoi
        return dau.lower(), ("" if cuoi.lower() == dau.lower() else cuoi.lower())
    ma, mb = _mo(a), _mo(b)
    return ma == mb or (ma[0] == mb[0] and (not ma[1] or not mb[1]))


def _so_bang_nhau(nguon: str, dong: str) -> bool:
    """Tập/số khớp theo CHỮ SỐ: «5+6» chứa «5», «Suppl 1» ≡ «Supplement_1», «4S» ≡ «4»."""
    a, b = re.findall(r"\d+", str(nguon or "")), re.findall(r"\d+", str(dong or ""))
    if not a or not b:
        return str(nguon or "").strip().lower() == str(dong or "").strip().lower() or not a or not b
    return a[0].lstrip("0") in {x.lstrip("0") for x in b} or b[0].lstrip("0") in {x.lstrip("0") for x in a}


def tra_crossref_tieu_de(tieu_de: str, nam: Optional[str]) -> Optional[Dict[str, Any]]:
    """Bản ghi Crossref khớp tiêu đề (query.bibliographic, 3 kết quả đầu) — chỉ trả khi tỷ lệ chuỗi tiêu đề ≥ ngưỡng VÀ
    năm trùng (± 1 cho bản in/bản điện tử). Không khớp ⇒ None (không đoán DOI)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from app.utils.http import HttpClient  # noqa: PLC0415

    data = HttpClient().get_json("https://api.crossref.org/works",
                                 params={"query.bibliographic": tieu_de, "rows": 3}) or {}
    for it in ((data.get("message") or {}).get("items") or []) if isinstance(data, dict) else []:
        td = " ".join(it.get("title") or [])
        nam_it = str(((it.get("issued") or {}).get("date-parts") or [[None]])[0][0] or "")
        if _ty_le_chuoi(td, tieu_de) >= 0.9 and (not nam or not nam_it or abs(int(nam_it) - int(nam)) <= 1):
            return it
    return None


def tra_pmcid(pmids: Sequence[str]) -> Dict[str, str]:
    """{pmid: PMCID} qua NCBI PMC ID Converter (miễn phí). Lỗi mạng ⇒ {} (không đo được — ghi lý do ở sổ)."""
    if not pmids:
        return {}
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from app.utils.http import HttpClient  # noqa: PLC0415

    data = HttpClient().get_json("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                                 params={"ids": ",".join(pmids), "format": "json", "tool": "ebm-tltk"}) or {}
    return {str(r.get("pmid")): str(r["pmcid"]) for r in (data.get("records") or []) if isinstance(r, dict)
            and r.get("pmcid") and r.get("pmid")}


def _nam_crossref(it: Mapping[str, Any]) -> List[str]:
    ra = []
    for k in ("published-print", "published-online", "issued"):
        dp = ((it.get(k) or {}).get("date-parts") or [[None]])[0]
        if dp and dp[0]:
            ra.append(str(dp[0]))
    return ra


def doi_chieu_crossref(dong: str, it: Mapping[str, Any]) -> Dict[str, Any]:
    """So dòng TLTK với bản ghi Crossref: {'lech': [...], 'trang_nguon': …, 'nguon_khong_co_trang': bool}."""
    vt = _vi_tri_tltk(dong)
    lech: List[str] = []
    td = " ".join(it.get("title") or [])
    # tỷ lệ từ của tiêu đề NGUỒN có mặt trong dòng (không tách câu theo «?»/«:» — tiêu đề hay có dấu hỏi, dấu hai chấm)
    if td and _ty_le_tieu_de(td, dong) < NGUONG_TIEU_DE:
        lech.append(f"tiêu đề khác nguồn — Crossref: «{td[:120]}»")
    nam = _nam_crossref(it)
    if nam and vt["nam"] and vt["nam"] not in nam:
        lech.append(f"năm {vt['nam']} — Crossref ghi {'/'.join(dict.fromkeys(nam))}")
    for khoa, ten in (("volume", "tap"), ("issue", "so")):
        gt = str(it.get(khoa) or "").strip()
        if gt and vt[ten] and not _so_bang_nhau(gt, str(vt[ten])):
            lech.append(f"{'tập' if ten == 'tap' else 'số'} {vt[ten]} — Crossref ghi {gt}")
    trang = str(it.get("page") or "").strip() or None
    if trang and vt["trang"] and not _trang_bang_nhau(trang, vt["trang"]):
        lech.append(f"trang {vt['trang']} — Crossref ghi {trang}")
    return {"lech": lech, "trang_nguon": trang, "nguon_khong_co_trang": trang is None,
            "crossref": {"tieu_de": td[:300], "nam": nam[:1], "tap": it.get("volume"), "so": it.get("issue"),
                         "trang": trang, "tap_chi": (it.get("container-title") or [None])[0]}}


def dung_so_dinh_danh(out_dir: Path, study: str, *, tra_doi: Any = tra_crossref, tra_td: Any = tra_crossref_tieu_de,
                      tra_pmc: Any = tra_pmcid) -> Dict[str, Any]:
    """Sổ định danh + đối chiếu siêu dữ liệu cho MỌI TLTK của đề cương nộp (mạng: Crossref, NCBI idconv — miễn phí).
    Hàm tra tiêm được cho kiểm thử."""
    import danh_muc_trich_dan as DMT  # noqa: PLC0415

    md = (Path(out_dir) / f"DE_CUONG_NOP_HOI_DONG_{study}.md").read_text(encoding="utf-8")
    muc = tach_tltk(md) or {}
    pmids = [m.group(1) for d in muc.values() for m in [re.search(r"PMID:\s*(\d+)", d)] if m]
    # PMCID: trước hết từ biên nhận A12 (PubMed `ArticleIdList`, cùng lượt kiểm rút bài), rồi NCBI idconv cho phần còn
    # thiếu. Đo 22/11/2026: idconv trả HTTP 403 qua đường mạng hiện hành ⇒ biên nhận A12 là nguồn chính.
    pmc: Dict[str, str] = {}
    try:
        meta = json.loads((Path(out_dir) / "A12_METADATA_RECEIPT.json").read_text(encoding="utf-8")).get("metadata")
        pmc = {str(k): str(v["pmcid"]) for k, v in (meta or {}).items() if isinstance(v, dict) and v.get("pmcid")}
    except (OSError, ValueError, AttributeError):
        pass
    pmc_loi = None
    con = [x for x in pmids if x not in pmc]
    try:
        pmc.update((tra_pmc(con) or {}) if (tra_pmc and con) else {})
    except Exception as exc:  # noqa: BLE001 — mạng: ghi lý do, không đoán
        pmc_loi = f"NCBI idconv lỗi {type(exc).__name__}"
    ra: List[Dict[str, Any]] = []
    for so, dong in sorted(muc.items()):
        loai = DMT.loai_tltk(dong)
        pm = re.search(r"PMID:\s*(\d+)", dong)
        doi = next(iter(sorted(DMT.dinh_danh(dong) - {f"pmid:{pm.group(1)}"} if pm else DMT.dinh_danh(dong))), "")
        doi = doi.split(":", 1)[1] if doi.startswith("doi:") else ""
        e: Dict[str, Any] = {"so": so, "bam_dong": bam_dong(dong), "loai": loai, "pmid": pm.group(1) if pm else None,
                             "pmcid": None, "doi": doi or None, "doi_de_xuat": None, "isbn": None, "so_hieu": None,
                             "url": None, "lech": [], "ly_do": [], "trang_nguon": None, "nguon_khong_co_trang": None}
        if e["pmid"]:
            e["pmcid"] = pmc.get(e["pmid"])
            if not e["pmcid"]:
                e["ly_do"].append(pmc_loi or "PubMed Central không có bản của bài (idconv không trả PMCID)")
        if loai == "bai_bao":
            it = None
            if e["doi"]:
                try:
                    it = tra_doi(e["doi"]) if tra_doi else None
                except Exception as exc:  # noqa: BLE001
                    e["ly_do"].append(f"Crossref lỗi {type(exc).__name__} — chưa đối chiếu siêu dữ liệu")
                if it is None and tra_doi:
                    e["ly_do"].append("Crossref không có bản ghi của DOI — chưa đối chiếu siêu dữ liệu")
            elif not e["pmid"]:
                try:
                    it = tra_td(_tieu_de_tltk(dong), _vi_tri_tltk(dong)["nam"]) if tra_td else None
                except Exception as exc:  # noqa: BLE001
                    e["ly_do"].append(f"Crossref lỗi {type(exc).__name__} khi tìm DOI theo tiêu đề")
                if it is not None:
                    e["doi_de_xuat"] = it.get("DOI")
                else:
                    e["ly_do"].append("không tìm thấy DOI khớp tiêu đề + năm trên Crossref")
            if it is not None:
                dc = doi_chieu_crossref(dong, it)
                if e["pmid"]:
                    # mục có PMID: nguồn có thẩm quyền là PubMed (K13 đối chiếu biên nhận A12); khác biệt với Crossref
                    # chỉ ghi THAM KHẢO (vd bài tiếng Tây Ban Nha: PubMed giữ tiêu đề gốc, Crossref ghi tiêu đề khác)
                    dc["lech_tham_khao"], dc["lech"] = dc["lech"], []
                e.update(dc)
        elif loai == "van_ban_quy_pham":
            sh = re.search(r"\d+(?:/\d{4})?/[\wĐđ\-]+", dong)
            e["so_hieu"] = sh.group(0) if sh else None
            u = re.search(r"https?://\S+", dong)
            e["url"] = u.group(0).rstrip(".") if u else None
            if not e["url"]:
                e["ly_do"].append("dòng TLTK chưa ghi đường dẫn nguồn chính thức (Cổng TTĐT cơ quan ban hành)")
        elif loai in ("sach", "chuong_sach"):
            isbn = re.search(r"ISBN[:\s]*([\dXx-]{10,17})", dong)
            e["isbn"] = isbn.group(1) if isbn else None
            if not e["isbn"] and not e["doi"]:
                e["ly_do"].append("sách chưa ghi ISBN hoặc DOI")
        ra.append(e)
    return {"schema": SCHEMA_DINH_DANH, "study": study, "luc": dt.datetime.now().isoformat(timespec="seconds"),
            "nguon": "Crossref /works, NCBI PMC ID Converter", "muc": ra}


def doc_so_dinh_danh(out_dir: Path, study: str) -> Dict[int, Dict[str, Any]]:
    """{số TLTK: mục sổ} — sổ vắng/hỏng ⇒ {}."""
    try:
        j = json.loads((Path(out_dir) / TEP_DINH_DANH.format(study=study)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {int(e["so"]): e for e in (j.get("muc") or []) if isinstance(e, dict) and str(e.get("so", "")).isdigit()}


def main(argv: Optional[Sequence[str]] = None, exports: Optional[Path] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("kiem", "loai-bo", "giu-chuan", "dinh-danh"))
    ap.add_argument("--study", required=True)
    ap.add_argument("--ap-dung", action="store_true",
                    help="loai-bo: ghi thật vào danh mục trích dẫn · giu-chuan: ghi tệp giữ trích dẫn đạt chuẩn")
    ap.add_argument("--loi", default=None,
                    help="nguyên văn lời bác sĩ làm căn cứ (loai-bo: mặc định luật 18/11; giu-chuan: BẮT BUỘC khi ghi)")
    ap.add_argument("--khong-mang", action="store_true", help="giu-chuan: không tra Crossref (DOI-only ⇒ không đạt)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not _STUDY.match(a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    out = Path(exports or EXPORTS) / a.study
    if not out.is_dir():
        print(f"❌ Không thấy thư mục đề tài {out}")
        return 3
    if a.lenh == "dinh-danh":
        so = dung_so_dinh_danh(out, a.study)
        p = out / TEP_DINH_DANH.format(study=a.study)
        p.write_text(json.dumps(so, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        if a.json:
            print(json.dumps(so, ensure_ascii=False, indent=1))
            return 0
        m = so["muc"]
        print(f"📒 Sổ định danh {p.name}: {len(m)} TLTK · PMID {sum(1 for e in m if e['pmid'])} · PMCID "
              f"{sum(1 for e in m if e['pmcid'])} · DOI {sum(1 for e in m if e['doi'])} (+ đề xuất "
              f"{sum(1 for e in m if e['doi_de_xuat'])}) · lệch nguồn {sum(1 for e in m if e['lech'])}")
        for e in m:
            for x in e["lech"]:
                print(f"   ≠ TLTK {e['so']}: {x}")
        return 1 if any(e["lech"] for e in m) else 0
    if a.lenh == "kiem":
        kq = danh_gia(out, a.study)
        print(json.dumps(kq, ensure_ascii=False, indent=1)) if a.json else _in(kq)
        ma = {"DAT": 0, "DAT_CO_GIU": 0, "KHONG_CO_TRICH_DAN": 0, "CON_VIEC": 1, "VI_PHAM": 1}
        return ma.get(kq["trang_thai"], 2)
    if a.lenh == "giu-chuan":
        tra = None if a.khong_mang else tra_crossref
        if a.ap_dung and not str(a.loi or "").strip():
            print("❌ giu-chuan --ap-dung cần --loi \"<nguyên văn lời bác sĩ>\" — quyền giữ là quyết định của bác sĩ")
            return 3
        kq = ap_dung_giu(out, a.study, a.loi, tra_doi=tra) if a.ap_dung else {**de_xuat_giu(out, a.study, tra),
                                                                              "da_ghi": 0}
        if a.json:
            print(json.dumps(kq, ensure_ascii=False, indent=1))
            return 0
        print(f"{'GHI THẬT' if a.ap_dung else 'CHẠY KHÔ'} — giữ {len(kq['giu'])} TLTK chưa có toàn văn mà đạt đủ ba "
              f"tiêu chí chuẩn trích dẫn" + (f" vào {kq.get('tep')}" if kq.get("da_ghi") else ""))
        for x in kq["giu"]:
            print(f"   ✓ TLTK {x['so']} [{LOAI_NGUON_CHUAN.get(x['loai_nguon'], x['loai_nguon'])}]: "
                  + " · ".join(v["mo_ta"] for v in x["tieu_chi"].values()))
        for x in kq["khong_dat"]:
            print(f"   ✗ TLTK {x['so']} KHÔNG giữ — {x['ly_do']}")
        if not a.ap_dung and kq["giu"]:
            print("   Thêm --ap-dung --loi \"<nguyên văn lời bác sĩ>\" để ghi.")
        print("   Được giữ không miễn việc tìm toàn văn. Cần bác sĩ kiểm chứng.")
        return 0
    loi = a.loi or LOI_BAC_SI_MAC_DINH
    kq = ap_dung_loai_bo(out, a.study, loi) if a.ap_dung else {**de_xuat_loai_bo(out, a.study), "da_ghi": 0}
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
