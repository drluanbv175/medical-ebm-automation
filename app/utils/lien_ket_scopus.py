"""Không bao giờ in liên kết / mã EID Scopus vào BÁO CÁO (03/10/2026).

Vì sao: repo y khoa đang CÔNG KHAI, và Routine Cloud commit `reports/giam-sat-cloud/<ngày>/` vào git (commit
7fc55a2 đã đăng 79 liên kết `scopus.com/inward/record.uri?partnerID=…&scp=…`). Điều khoản Elsevier (điều khoản
riêng Scopus sửa 16/09/2026; API Service Agreement §2.4) cấm chia sẻ/phát tán dữ liệu Scopus cho bên thứ ba —
liên kết bản ghi Scopus (kèm partnerID, mã `scp`) và mã EID `2-s2.0-…` là dữ liệu Scopus. DOI/PMID là định danh
công khai của CHÍNH bài báo (Crossref/NLM cấp), không thuộc Scopus — nên thay bằng liên kết DOI/PubMed.

Hai lớp dùng CHUNG một bộ nhận diện (`_RE_URL`, `_RE_EID`):
1. `lien_ket_cong_khai(url, doi, pmid)` — bộ dựng báo cáo gọi thay cho `r.url`: URL Scopus ⇒ `https://doi.org/<doi>`;
   không có DOI ⇒ `https://pubmed.ncbi.nlm.nih.gov/<pmid>/`; không có cả hai ⇒ None (KHÔNG in liên kết).
2. `lam_sach_van_ban(text)` — chốt hậu kiểm TẤT ĐỊNH trên văn bản đã sinh (Markdown/JSON/HTML): URL Scopus / EID còn
   sót bị thay bằng liên kết DOI/PubMed của CÙNG mục (cùng ô bảng, hoặc cùng dòng nếu không phải bảng); mục không có
   DOI/PMID thì thay bằng `GHI_CHU_GO`. Liên kết công khai đã có sẵn trong mục ⇒ chỉ gỡ (kèm dấu ` ; ` thừa), không
   in trùng. Hậu điều kiện: `tim_vi_pham(kết quả) == []` (bảo đảm bằng lượt cuối thay thẳng bằng ghi chú).
   `tim_vi_pham(text)` chỉ ĐỌC — dùng cho pre-commit/test.

Chỉ dùng thư viện chuẩn: pre-commit gọi bằng `python3` hệ thống (không có venv, không có SQLAlchemy).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

GHI_CHU_GO = "(liên kết Scopus đã gỡ — không có DOI/PMID)"
# Đuôi tệp văn bản mà chốt hậu kiểm đọc/sửa trong một thư mục báo cáo.
DUOI_VAN_BAN = (".md", ".json", ".html", ".htm", ".txt", ".csv")

# Miền scopus.com và mọi miền con (www., …); chặn hai đầu để «xscopus.com» / «scopus.community» không bị bắt.
_MIEN = r"(?<![a-z0-9-])(?:[a-z0-9-]+\.)*scopus\.com(?![a-z0-9-])"
# Phần đuôi URL dừng ở khoảng trắng hoặc ký tự đóng liên kết Markdown/HTML/ô bảng. KHÔNG dừng ở «;» vì URL đã
# html-escape chứa «&amp;».
_DUOI_URL = r"(?:[/?#:][^\s<>\"'|)\]`]*)?"
_RE_URL = re.compile(rf"(?:https?://)?{_MIEN}{_DUOI_URL}", re.IGNORECASE)
# EID Scopus «2-s2.0-<số>», kèm tiền tố «EID:» nếu có.
_RE_EID = re.compile(r"(?:\bEID\s*[:=]?\s*)?(?<![\w.-])2-s2\.0-\d{6,}(?!\d)", re.IGNORECASE)
# Liên kết Markdown trỏ thẳng tới Scopus: [nhãn](url "tiêu đề").
_RE_MD = re.compile(rf"\[(?P<nhan>[^\]\n]*)\]\(\s*<?(?P<url>(?:https?://)?{_MIEN}{_DUOI_URL})>?"
                    r"(?:\s+\"[^\"\n]*\")?\s*\)", re.IGNORECASE)
# Một «token Scopus» bất kỳ — liên kết Markdown đứng trước để thắng khi cùng vị trí bắt đầu.
_RE_TOKEN = re.compile(rf"{_RE_MD.pattern}|{_RE_URL.pattern}|{_RE_EID.pattern}", re.IGNORECASE)

# Định danh công khai trong NGỮ CẢNH của mục (để chọn liên kết thay thế).
_RE_DOI = re.compile(r"(?:\bDOI\s*:?\s*|doi\.org/)(?P<doi>10\.\d{4,9}/[^\s|<>\"']+)", re.IGNORECASE)
_RE_PMID = re.compile(r"(?:\bPMID\s*:?\s*|pubmed\.ncbi\.nlm\.nih\.gov/)(?P<pmid>\d{1,9})(?!\d)", re.IGNORECASE)
_RE_DAU_PHAN_CACH_TRUOC = re.compile(r"\s*;\s*$")
_RE_DAU_PHAN_CACH_SAU = re.compile(r"^\s*;\s*")


def _chuan_doi(doi: object) -> Optional[str]:
    """DOI trần «10.xxxx/…» (bỏ tiền tố doi:/https://doi.org/, dấu câu cuối, ngoặc đóng không cân)."""
    if not doi:
        return None
    s = str(doi).strip()
    s = re.sub(r"^(?:doi\s*:\s*|https?://(?:dx\.)?doi\.org/)", "", s, flags=re.IGNORECASE)
    s = s.rstrip(".,;:")
    for mo, dong in (("(", ")"), ("[", "]")):
        while s.endswith(dong) and s.count(dong) > s.count(mo):
            s = s[:-1]
    return s if re.match(r"^10\.\d{4,9}/\S+$", s) else None


def _chuan_pmid(pmid: object) -> Optional[str]:
    s = str(pmid).strip() if pmid is not None else ""
    return s if s.isdigit() and 0 < len(s) <= 9 else None


def lien_ket_doi(doi: str) -> str:
    return f"https://doi.org/{doi}"


def lien_ket_pubmed(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def la_lien_ket_scopus(url: object) -> bool:
    """True nếu chuỗi chứa URL miền scopus.com hoặc mã EID Scopus."""
    if not url:
        return False
    s = str(url)
    return bool(_RE_URL.search(s) or _RE_EID.search(s))


def lien_ket_cong_khai(url: Optional[str], doi: object = None, pmid: object = None) -> Optional[str]:
    """URL được phép in vào báo cáo. URL không phải Scopus ⇒ giữ nguyên. URL Scopus ⇒ liên kết DOI, rồi PubMed;
    không có DOI/PMID hợp lệ ⇒ None (bộ dựng KHÔNG in liên kết nào cho mục đó)."""
    if not la_lien_ket_scopus(url):
        return url
    d = _chuan_doi(doi)
    if d:
        return lien_ket_doi(d)
    p = _chuan_pmid(pmid)
    if p:
        return lien_ket_pubmed(p)
    return None


def tim_vi_pham(text: str) -> List[Tuple[int, str]]:
    """[(số dòng, đoạn khớp)] mọi URL Scopus / EID trong văn bản. Chỉ đọc."""
    ra: List[Tuple[int, str]] = []
    for i, dong in enumerate(text.splitlines(), start=1):
        for m in _RE_URL.finditer(dong):
            ra.append((i, m.group(0)))
        for m in _RE_EID.finditer(_RE_URL.sub(lambda x: " " * len(x.group(0)), dong)):
            ra.append((i, m.group(0).strip()))
    return ra


def _o_chua(dong: str, vi_tri: int) -> Tuple[int, int]:
    """Biên [đầu, cuối) của ô bảng Markdown chứa `vi_tri` (dòng không phải bảng ⇒ cả dòng)."""
    dau = dong.rfind("|", 0, vi_tri) + 1
    cuoi = dong.find("|", vi_tri)
    return dau, (len(dong) if cuoi < 0 else cuoi)


def _gan_nhat(regex: re.Pattern, ngu_canh: str, vi_tri: int, nhom: str) -> Optional[str]:
    """Giá trị gần nhất ĐỨNG TRƯỚC `vi_tri` trong ngữ cảnh; không có thì giá trị đầu tiên đứng sau."""
    truoc = [m for m in regex.finditer(ngu_canh) if m.start() < vi_tri]
    if truoc:
        return truoc[-1].group(nhom)
    sau = [m for m in regex.finditer(ngu_canh) if m.start() >= vi_tri]
    return sau[0].group(nhom) if sau else None


def _lien_ket_thay(ngu_canh: str, vi_tri: int) -> Optional[str]:
    d = _chuan_doi(_gan_nhat(_RE_DOI, ngu_canh, vi_tri, "doi"))
    if d:
        return lien_ket_doi(d)
    p = _chuan_pmid(_gan_nhat(_RE_PMID, ngu_canh, vi_tri, "pmid"))
    return lien_ket_pubmed(p) if p else None


def _lam_sach_dong(dong: str) -> Tuple[str, int]:
    tokens = list(_RE_TOKEN.finditer(dong))
    if not tokens:
        return dong, 0
    # Che mọi token Scopus trước khi tìm DOI/PMID ngữ cảnh — DOI nằm TRONG chính URL Scopus không được tính.
    da_che = list(dong)
    for m in tokens:
        da_che[m.start():m.end()] = " " * (m.end() - m.start())
    che = "".join(da_che)
    ra: List[str] = []
    con_tro = 0
    da_chen: Dict[int, set] = {}  # liên kết đã chèn theo từng ô — token Scopus thứ hai cùng mục không in trùng
    for m in tokens:
        dau, cuoi = m.start(), m.end()
        o_dau, o_cuoi = _o_chua(dong, dau)
        ngu_canh = che[o_dau:o_cuoi]
        lien_ket = _lien_ket_thay(ngu_canh, dau - o_dau)
        nhan = m.group("nhan") if m.group("url") else None
        if lien_ket and (lien_ket in ngu_canh or lien_ket in da_chen.get(o_dau, ())):
            # Mục đã có sẵn đúng liên kết công khai ⇒ chỉ gỡ token Scopus (kèm « ; » thừa), không in trùng.
            thay = nhan if nhan is not None else ""
            if not thay:
                truoc = _RE_DAU_PHAN_CACH_TRUOC.search(dong[con_tro:dau])
                if truoc:
                    dau = con_tro + truoc.start()
                else:
                    sau = _RE_DAU_PHAN_CACH_SAU.match(dong[cuoi:])
                    if sau:
                        cuoi += sau.end()
        elif nhan is not None:
            thay = f"[{nhan}]({lien_ket})" if lien_ket else f"{nhan} {GHI_CHU_GO}".strip()
        else:
            thay = lien_ket or GHI_CHU_GO
        if lien_ket:
            da_chen.setdefault(o_dau, set()).add(lien_ket)
        ra.append(dong[con_tro:dau])
        ra.append(thay)
        con_tro = cuoi
    ra.append(dong[con_tro:])
    return "".join(ra), len(tokens)


def lam_sach_van_ban(text: str) -> Tuple[str, int]:
    """(văn bản đã làm sạch, số token Scopus đã thay/gỡ). Tất định và idempotent; giữ nguyên ký tự xuống dòng."""
    tong = 0
    for _ in range(3):  # nhãn của liên kết Markdown có thể chứa chính URL Scopus ⇒ cần thêm lượt
        dong_moi: List[str] = []
        so = 0
        for dong in text.splitlines(keepends=True):
            than = dong.rstrip("\r\n")
            moi, n = _lam_sach_dong(than)
            dong_moi.append(moi + dong[len(than):])
            so += n
        text = "".join(dong_moi)
        tong += so
        if so == 0:
            break
    if tim_vi_pham(text):  # lưới cuối: không bao giờ trả văn bản còn dữ liệu Scopus
        text, n = _RE_URL.subn(GHI_CHU_GO, text)
        text, m = _RE_EID.subn(GHI_CHU_GO, text)
        tong += n + m
    return text, tong


def _tep_van_ban(thu_muc: Path) -> List[Path]:
    return sorted(p for p in thu_muc.rglob("*") if p.is_file() and p.suffix.lower() in DUOI_VAN_BAN)


def _doc(tep: Path) -> str:
    # Đọc BYTE (không dịch CRLF) + surrogateescape ⇒ ghi lại giữ nguyên từng byte ngoài phần đã thay.
    return tep.read_bytes().decode("utf-8", errors="surrogateescape")


def lam_sach_tep(tep: Path) -> int:
    """Làm sạch tại chỗ một tệp văn bản UTF-8; trả số token đã thay (0 ⇒ không ghi lại tệp)."""
    moi, n = lam_sach_van_ban(_doc(tep))
    if n:
        tep.write_bytes(moi.encode("utf-8", errors="surrogateescape"))
    return n


def chep_da_lam_sach(nguon: Path, dich: Path) -> int:
    """Chép `nguon` → `dich` với nội dung ĐÃ làm sạch (bản chưa sạch không bao giờ chạm `dich`).

    Trả số token Scopus đã thay."""
    moi, n = lam_sach_van_ban(_doc(nguon))
    dich.write_bytes(moi.encode("utf-8", errors="surrogateescape"))
    return n


def lam_sach_thu_muc(thu_muc: Path) -> Dict[str, int]:
    """Làm sạch mọi tệp văn bản dưới thư mục; {đường dẫn tương đối: số token đã thay} (chỉ tệp có thay)."""
    ra: Dict[str, int] = {}
    for tep in _tep_van_ban(thu_muc):
        n = lam_sach_tep(tep)
        if n:
            ra[tep.relative_to(thu_muc).as_posix()] = n
    return ra


def quet_thu_muc(thu_muc: Path) -> Dict[str, List[Tuple[int, str]]]:
    """{đường dẫn tương đối: vi phạm} cho mọi tệp văn bản dưới thư mục. Chỉ đọc."""
    ra: Dict[str, List[Tuple[int, str]]] = {}
    for tep in _tep_van_ban(thu_muc):
        vp = tim_vi_pham(_doc(tep))
        if vp:
            ra[tep.relative_to(thu_muc).as_posix()] = vp
    return ra
