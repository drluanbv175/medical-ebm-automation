"""Danh mục trích dẫn của đề tài và danh mục TÀI LIỆU THAM KHẢO trong văn bản (15/11/2026).

Bác sĩ 15/11/2026 giao đồng bộ giai đoạn «Tổng quan tài liệu … đảm bảo sự đồng bộ xuyên suốt và chính xác nhất» + «mỗi
vấn đề xây dựng và hoàn thiện phải được cập nhật vào hệ thống». Đo trên BTM: `DANH_MUC_TRICH_DAN_<mã>.json` (repo gốc
dựng, bác sĩ quyết loại 19 bài ngày 25/10/2026 — không lấy được toàn văn hoặc lệch đề tài) KHÔNG được công cụ nào của
repo y khoa đọc — sổ chứng cứ G1 (A2b) dựng ngày 28/10 vẫn liệt kê 17 bài đã loại như chứng cứ của đề tài.

Module này là MỘT chỗ đọc chung:
- `doc` / `loai_bo` / `trich_dan`: danh mục trích dẫn, khoá theo «pmid:<số>» hoặc «doi:<chữ thường>»;
- `tach_tltk`: tách mục TÀI LIỆU THAM KHẢO đánh số của một văn bản Markdown khỏi phần thân, và các số trích dẫn
  «[n]», «[n, m]», «[n–m]» trong thân;
- `dinh_danh`: PMID/DOI trong một chuỗi.
Chỉ đọc — không ghi gì.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

TEP = "DANH_MUC_TRICH_DAN_{study}.json"

_PMID = re.compile(r"\bPMID\s*:?\s*(\d{6,9})\b", re.I)
_DOI = re.compile(r"\b(10\.\d{4,9}/[^\s|<>\"'\]]+)", re.I)
_TIEU_DE_TLTK = re.compile(r"^(#+)\s*(?:\d+\.\s*)?(?:TÀI LIỆU THAM KHẢO|REFERENCES)\b", re.I)
# «[3]», «[2, 3]», «[4–6]», «[1, 5–7]» — không nhận nhóm có số 0 (thang «[0–100]») hay số > 999.
_TRICH = re.compile(r"\[(\d{1,3}(?:\s*[,;–-]\s*\d{1,3})*)\](?!\()")


def _doi_sach(d: str) -> str:
    return d.rstrip(".,;:)").lower()


def dinh_danh(text: str) -> Set[str]:
    """Tập khoá «pmid:<số>» / «doi:<chữ thường>» có trong chuỗi."""
    s = str(text or "")
    return {f"pmid:{p}" for p in _PMID.findall(s)} | {f"doi:{_doi_sach(d)}" for d in _DOI.findall(s)}


def khoa_cua(item: Mapping[str, Any]) -> Set[str]:
    """Khoá của một mục danh mục (có thể có cả PMID lẫn DOI)."""
    ra: Set[str] = set()
    if str(item.get("pmid") or "").strip():
        ra.add(f"pmid:{str(item['pmid']).strip()}")
    if str(item.get("doi") or "").strip():
        ra.add(f"doi:{_doi_sach(str(item['doi']).strip())}")
    return ra


def doc(out_dir: Path, study: str) -> Dict[str, Any]:
    p = Path(out_dir) / TEP.format(study=study)
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return j if isinstance(j, dict) else {}


def _theo_khoa(ds: Any) -> Dict[str, Dict[str, Any]]:
    ra: Dict[str, Dict[str, Any]] = {}
    for x in ds if isinstance(ds, list) else []:
        if isinstance(x, dict):
            for k in khoa_cua(x):
                ra[k] = x
    return ra


def trich_dan(out_dir: Path, study: str) -> Dict[str, Dict[str, Any]]:
    return _theo_khoa(doc(out_dir, study).get("trich_dan"))


def loai_bo(out_dir: Path, study: str) -> Dict[str, Dict[str, Any]]:
    """Bài chủ nhiệm đã cho LOẠI khỏi danh mục trích dẫn (khoá → mục, có `ly_do`, `ngay`)."""
    return _theo_khoa(doc(out_dir, study).get("loai_bo"))


# 17/11/2026: văn bản cổng có nguồn dẫn phải nằm trong TLTK đề cương nộp. MỘT danh sách dùng chung cho trục
# trich_dan_tong_quan (nhat_quan_xuyen_cong), bộ sinh đề cương nộp (ứng viên TLTK) và người kiểm trích dẫn A12 (bộ giả
# lập). Trước đó bộ sinh không đọc thiết kế G1 (A2) và bộ biến G3, A12 không quét chúng ⇒ trục báo «dẫn nguồn chưa
# có trong TLTK» ở 7/16 đề tài giả lập (EPV van Smeden ở A2, ICC Adams ở G3, Piaggio ở đề cương G10).
VAN_BAN_CONG_TRICH = (
    ("G1", "G1_A2_PROTOCOL_DESIGN_{s}.md", "thiết kế G1 (A2)"),
    ("G3", "G3_BO_BIEN_SO_{s}.md", "bộ biến G3"),
    ("G4", "G4_A5_SAP_FINAL_{s}.md", "SAP"),
    ("G10", "DE_CUONG_THONG_NHAT_{s}.md", "đề cương thống nhất G10"),
)


def van_ban_nguon_cong(out_dir: Path, study: str, meta: Optional[Mapping[str, Any]] = None) -> List[str]:
    """Văn bản các tệp `VAN_BAN_CONG_TRICH` đang có + chuỗi tham số G3 `*_source` của study_meta (tệp vắng ⇒ bỏ)."""
    ra: List[str] = []
    for _g, mau, _nhan in VAN_BAN_CONG_TRICH:
        try:
            ra.append((Path(out_dir) / mau.format(s=study)).read_text(encoding="utf-8"))
        except OSError:
            continue
    g3 = ((meta or {}).get("gate_params") or {}).get("G3") or {}
    if isinstance(g3, Mapping):
        ra.append(" ".join(str(v) for k, v in g3.items() if str(k).endswith("_source")))
    return ra


def pmid_cua_van_ban(*van: str) -> List[str]:
    """PMID nêu trong các văn bản, kể cả DOI tài liệu chuẩn quy về PMID qua cặp đã xác minh
    (protocol_checklist_items.cap_doi_pmid_he_thong). Thứ tự xuất hiện, không trùng."""
    try:
        import protocol_checklist_items as PCI  # noqa: PLC0415

        cap = PCI.cap_doi_pmid_he_thong()
    except ImportError:
        cap = {}
    ra: List[str] = []
    for t in van:
        ra += _PMID.findall(str(t or ""))
        ra += [cap[_doi_sach(d)] for d in _DOI.findall(str(t or "")) if _doi_sach(d) in cap]
    return list(dict.fromkeys(ra))


def tach_tltk(text: str) -> Optional[Tuple[Dict[int, str], str]]:
    """({số: dòng TLTK}, phần thân không gồm mục TLTK) — None khi văn bản không có mục TÀI LIỆU THAM KHẢO.

    Mục TLTK kết thúc ở tiêu đề kế tiếp cùng cấp hoặc cấp cao hơn (vd «# PHỤ LỤC A»). Phụ lục sau TLTK vẫn tính là
    thân (có thể chứa trích dẫn). Chỉ nhận dòng đánh số «n. …» — văn bản quy phạm liệt kê gạch đầu dòng không có số
    nên không được trích bằng số."""
    dong = str(text or "").splitlines()
    dau = cap = None
    for i, d in enumerate(dong):
        m = _TIEU_DE_TLTK.match(d)
        if m:
            dau, cap = i, len(m.group(1))
            break
    if dau is None:
        return None
    cuoi = next((j for j in range(dau + 1, len(dong))
                 if (m := re.match(r"^(#+)\s", dong[j])) and len(m.group(1)) <= cap), len(dong))
    muc: Dict[int, str] = {}
    for d in dong[dau + 1:cuoi]:
        m = re.match(r"^\s*(\d{1,3})\.\s+(.+)", d)
        if m:
            muc[int(m.group(1))] = m.group(2)
    return muc, "\n".join(dong[:dau] + dong[cuoi:])


def so_trich_dan(than: str) -> List[int]:
    """Các số trích dẫn theo THỨ TỰ xuất hiện (có lặp) trong phần thân."""
    ra: List[int] = []
    for m in _TRICH.finditer(str(than or "")):
        nhom: List[int] = []
        for phan in re.split(r"\s*[,;]\s*", m.group(1)):
            ab = re.split(r"\s*[–-]\s*", phan)
            if len(ab) == 2:
                a, b = int(ab[0]), int(ab[1])
                nhom += list(range(a, b + 1)) if 0 < a <= b else [0]
            else:
                nhom.append(int(ab[0]))
        if 0 not in nhom:
            ra += nhom
    return ra


# ───────────────────── Chuẩn trình bày NLM «Citing Medicine» theo LOẠI tài liệu (22/11/2026) ─────────────────────
# VÌ SAO (bác sĩ 22/11/2026: «Tài liệu tham khảo, trích dẫn đã có nền, hãy nâng cấp và hoàn thiện đúng chuẩn»): K13 cũ
# chỉ kiểm mục CÓ PMID theo metadata A12. Mục không PMID (bài tạp chí trong nước, văn bản quy phạm, sách) không được
# kiểm yếu tố bắt buộc nào — đo trên C1a: 7/11 bài tạp chí trong nước thiếu số trang. Chuẩn: NLM Citing Medicine 2nd ed.
# (chuẩn ICMJE khuyến nghị; tài liệu chính phủ Mỹ, phạm vi công cộng). Văn bản quy phạm Việt Nam theo yếu tố tương ứng
# của Citing Medicine cho văn bản pháp quy: cơ quan ban hành, số hiệu, ngày, nơi ban hành. Hàm THUẦN — không mạng, không
# ghi.
LOAI_TLTK = ("bai_bao", "sach", "chuong_sach", "van_ban_quy_pham", "luan_van", "trang_web", "tien_in")
TEN_LOAI_TLTK = {"bai_bao": "bài tạp chí", "sach": "sách", "chuong_sach": "chương sách",
                 "van_ban_quy_pham": "văn bản quy phạm", "luan_van": "luận văn/luận án", "trang_web": "trang web",
                 "tien_in": "bản tiền in"}
_VB_QUY_PHAM = re.compile(r"\b(?:Quyết định|Thông tư|Nghị định|Luật|Công văn|Chỉ thị|Nghị quyết|Thông tư liên tịch)\b"
                          r"(?:\s+số)?\s*\d+(?:/\d{4})?/[\wĐđ\-]+|\b\d+/(?:\d{4}/)?(?:QĐ|TT|NĐ|QH\d*|CT|NQ)-[\wĐđ]+")
_TIEN_IN = re.compile(r"\[(?:Preprint|Bản tiền in)\]|\b(?:medRxiv|bioRxiv|Research Square|SSRN|arXiv)\b", re.I)
_LUAN_VAN = re.compile(r"\bLuận (?:văn|án)\b|\[(?:luận văn|luận án|(?:master'?s |doctoral )?(?:thesis|dissertation))",
                       re.I)
_CHUONG = re.compile(r"(?:^|\.\s)(?:In|Trong):\s")
_WEB = re.compile(r"\[Internet\]|Available from:|Có tại:", re.I)
_NAM_TAP = re.compile(r"(?<!\d)(?:19|20)\d{2}(?:\s+[A-Z][a-z]{2}(?:\s+\d{1,2})?)?\s*;\s*[\w-]+")
_NXB = re.compile(r"[A-ZĐÀ-Ỹ][^.;:\n]{1,60}:\s*[^;:\n]{2,120};\s*(?:c\s*)?(?:19|20)\d{2}")
_NGAY_VB = re.compile(r"ngày\s+\d{1,2}(?:/|\s+tháng\s+)\d{1,2}(?:/|\s+năm\s+)\d{4}")
_TRUY_CAP = re.compile(r"\[(?:cited|trích dẫn|truy cập)[^\]]*(?:19|20)\d{2}[^\]]*\]", re.I)
_URL = re.compile(r"https?://\S+|www\.\S+")
_KET_TAC_GIA = re.compile(r",?\s*(?:et al\.?|và cộng sự|và cs\.?)\s*$", re.I)


def loai_tltk(dong: str) -> str:
    """Loại tài liệu của một dòng TLTK (một trong `LOAI_TLTK`). Thứ tự xét: văn bản quy phạm → bản tiền in → luận văn →
    chương sách → bài tạp chí (năm;tập, DOI/PMID kèm tên tạp chí) → trang web → sách (nơi: nhà xuất bản; năm)."""
    s = str(dong or "")
    if _VB_QUY_PHAM.search(s) and not _NAM_TAP.search(s):
        return "van_ban_quy_pham"
    if _TIEN_IN.search(s):
        return "tien_in"
    if _LUAN_VAN.search(s):
        return "luan_van"
    if _CHUONG.search(s):
        return "chuong_sach"
    if _NAM_TAP.search(s) or re.search(r"(?<!\d)(?:19|20)\d{2}\s*:\s*\d", s):
        return "bai_bao"
    if _WEB.search(s) or (_URL.search(s) and not _NXB.search(s)):
        return "trang_web"
    if _NXB.search(s):
        return "sach"
    return "bai_bao" if (_PMID.search(s) or _DOI.search(s)) else "sach"


def tac_gia_ca_nhan(dong: str) -> Tuple[List[str], bool]:
    """(tác giả CÁ NHÂN ghi trong mục, có «et al./và cộng sự» không). Đoạn tác giả = phần trước dấu «. » đầu tiên; tác
    giả tập thể ghi sau «;» (NLM) không tính."""
    s = re.sub(r"^\s*\d{1,3}\.\s+", "", str(dong or ""))
    m = re.match(r"(.+?)\.\s", s)
    doan = m.group(1) if m else ""
    doan = doan.split(";")[0]
    co_et_al = bool(_KET_TAC_GIA.search(doan))
    doan = _KET_TAC_GIA.sub("", doan)
    ten = [x.strip() for x in doan.split(",") if x.strip()]
    return ten, co_et_al


def yeu_to_nlm(dong: str) -> Dict[str, Any]:
    """Yếu tố BẮT BUỘC theo NLM Citing Medicine cho loại của mục: {'loai', 'thieu': [...], 'tac_gia': n}.

    Bài tạp chí: tác giả (≤ 6 tên rồi «et al.»/«và cộng sự»; > 6 tên ⇒ thiếu quy tắc), tiêu đề, tên tạp chí, năm, tập
    hoặc số, trang hoặc mã bài (e-location). Sách: tác giả/biên tập, tên sách, nơi xuất bản: nhà xuất bản; năm. Chương
    sách: thêm «In:/Trong:» và trang. Văn bản quy phạm: cơ quan ban hành, số hiệu, ngày ban hành, nơi ban hành: cơ quan;
    năm. Luận văn: loại văn bằng, nơi: trường; năm. Trang web: «[Internet]» hoặc «Có tại/Available from», địa chỉ URL,
    ngày truy cập. Bản tiền in: máy chủ, năm, DOI."""
    s = re.sub(r"^\s*\d{1,3}\.\s+", "", str(dong or "")).strip()
    loai = loai_tltk(s)
    thieu: List[str] = []
    ten, co_et_al = tac_gia_ca_nhan(s)
    phan = [x.strip() for x in re.split(r"(?<=[.?!])\s+(?=[A-ZĐÀ-Ỹ0-9\[])", s) if x.strip()]
    if loai in ("bai_bao", "tien_in", "luan_van", "chuong_sach", "sach", "trang_web"):
        if not ten and not re.match(r"[^.]{3,}\.\s", s):
            thieu.append("tác giả hoặc tác giả tập thể")
        if len(ten) > 6 and not (len(ten) == 1):
            thieu.append(f"quy tắc tác giả NLM: ghi 6 tác giả đầu rồi «et al.»/«và cộng sự» (đang ghi {len(ten)})")
        elif co_et_al and len(ten) != 6:
            thieu.append(f"quy tắc tác giả NLM: «et al.»/«và cộng sự» đứng sau đúng 6 tác giả (đang có {len(ten)})")
        if len(phan) < 3:
            thieu.append("tiêu đề")
    if loai == "bai_bao":
        if not re.search(r"(?<!\d)(?:19|20)\d{2}", s):
            thieu.append("năm xuất bản")
        nam_tap = _NAM_TAP.search(s)
        if not nam_tap and not re.search(r"(?<!\d)(?:19|20)\d{2}\s*:\s*\d", s):
            thieu.append("tập hoặc số (năm;tập(số))")
        # vị trí trong số: trang in, mã bài (e-location) hoặc — chỉ khi bài điện tử thật sự KHÔNG phân trang và không
        # có mã bài — độ dài ước tính trong ngoặc vuông theo NLM Citing Medicine («[about 3 p.]», «[5 p.]»). Không có
        # ngoại lệ «nguồn không ghi trang»: Crossref thiếu trường page KHÔNG chứng minh bài không có trang (22/11/2026:
        # cả 8 bài C1a mà Crossref không ghi trang đều in số trang trên bản PDF của tạp chí).
        if not re.search(r"(?:(?:19|20)\d{2}\s*;\s*[\w-]+(?:\s*\([^)]*\))?|(?:19|20)\d{2})\s*:\s*"
                         r"(?:[eSA-Za-z]{0,2}\d|\[(?:about\s+|khoảng\s+)?\d+\s*(?:p|tr|screens?)\.?\])", s):
            thieu.append("trang hoặc mã bài (năm;tập(số):trang)")
        if len(phan) < 4 and not re.search(r"\.\s+[A-ZĐ][\w .&()-]*\.\s+(?:19|20)\d{2}", s):
            thieu.append("tên tạp chí")
    elif loai in ("sach", "luan_van", "chuong_sach"):
        if not _NXB.search(s):
            thieu.append("nơi xuất bản: nhà xuất bản; năm")
        if loai == "luan_van" and not _LUAN_VAN.search(s):
            thieu.append("loại văn bằng")
        if loai == "chuong_sach" and not re.search(r"\b(?:p|tr)\.\s*\d", s):
            thieu.append("trang của chương (p. …/tr. …)")
    elif loai == "van_ban_quy_pham":
        if not re.match(r"[^.]{2,}\.\s", s):
            thieu.append("cơ quan ban hành")
        if not re.search(r"\d+(?:/\d{4})?/[\wĐđ\-]+", s):
            thieu.append("số hiệu")
        if not _NGAY_VB.search(s):
            thieu.append("ngày ban hành")
        if not _NXB.search(s):
            thieu.append("nơi ban hành: cơ quan; năm")
    elif loai == "trang_web":
        if not _URL.search(s):
            thieu.append("địa chỉ URL")
        if not _TRUY_CAP.search(s):
            thieu.append("ngày truy cập ([trích dẫn …]/[cited …])")
    if loai == "tien_in":
        if not _DOI.search(s):
            thieu.append("DOI của bản tiền in")
    return {"loai": loai, "thieu": thieu, "tac_gia": len(ten)}
