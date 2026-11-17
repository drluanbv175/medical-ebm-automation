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
