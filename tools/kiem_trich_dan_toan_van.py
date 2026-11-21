#!/usr/bin/env python3
"""Kiểm nội dung trích dẫn trên TOÀN VĂN — xét lại các cặp (đoạn khẳng định, tài liệu) mà lượt kiểm theo ABSTRACT (A12,
`kiem_noi_dung_trich_dan.py`) đánh dấu «cần xem», bằng các đoạn liên quan lấy từ toàn văn có trong kho.

VÌ SAO (21/11/2026, bác sĩ chọn «C — kiểm trích dẫn trên toàn văn»): lượt A12 chỉ thấy abstract, nên các cặp
«ho_tro_mot_phan»/«khong_ho_tro»/«can_xem» (C1a 14, BTM 12) phần lớn là chi tiết abstract không nêu nhưng có thể có ở
toàn văn. Đo cùng ngày: PMC XML trong kho chỉ phủ 3/13 (C1a) và 1/12 (BTM) tài liệu của các cặp đó — phần còn lại là
bài không mở (J Clin Epidemiol, tạp chí trong nước) mà toàn văn nằm trong PDF đính kèm EndNote.

Nguồn toàn văn (theo thứ tự): (1) PMC XML `exports/<mã>/toan_van_oa/PMID-<pmid>_*.xml`; (2) PDF đặt tay
`exports/<mã>/toan_van_tltk/` (TLTK-<n>.pdf · PMID-<pmid>*.pdf · DOI-<doi, «/»→«_»>.pdf); (3) PDF đính kèm EndNote — tra
PMID/DOI trên BẢN SAO TẠM của sdb.eni (`endnote_suc_khoe.ban_sao_csdl` của repo gốc, chế độ chỉ đọc), không bao giờ mở
hay ghi tệp thật của thư viện. PDF không có lớp chữ (quét ảnh) ⇒ «không đọc được», không đoán.

Mỗi tài liệu: chọn đoạn liên quan (tiêu đề + phần đầu + các cửa sổ chứa SỐ của câu khẳng định hoặc từ khoá tiếng Anh của
câu trích abstract/tiêu đề tài liệu) trong trần `--toi-da-ky-tu`, gọi Claude MỘT lượt cho mọi câu của tài liệu đó. Máy
kiểm «trich» phải có NGUYÊN VĂN trong đoạn đã gửi — không có ⇒ «khong_xac_minh», giữ kết luận abstract.

Ranh giới: TƯ VẤN — không sửa đề cương, không đổi danh mục TLTK, không mở/chặn cổng. Không lưu toàn văn vào báo cáo
(chỉ câu trích ≤ 25 từ). CHẠY KHÔ mặc định (độ phủ + ước chi phí); `--goi-api` mới gọi (tính phí).
Mã thoát: 0 mọi cặp cần xem được toàn văn chống đỡ · 1 còn cặp cần bác sĩ xem · 2 không kiểm được (thiếu/cũ báo cáo
A12, không có toàn văn nào, lỗi API) · 3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("pypdf").setLevel(logging.ERROR)  # PDF nhà xuất bản hay có khoá trùng — cảnh báo vô hại

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import duyet_kiem_may_api as DK  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402

TOI_DA_KY_TU = 16000  # mỗi tài liệu: ~10 nghìn token (1,6 ký tự/token)
CUA_SO = 900
MUC_HOP_LE = ("ho_tro", "ho_tro_mot_phan", "khong_ho_tro", "khong_du_can_cu")
MAX_TOKENS = 6000
CHU_TOI_THIEU = 2000  # PDF ít chữ hơn ⇒ coi là ảnh/hỏng
SO_LAN_THU_JSON_HONG = 2  # JSON sai cú pháp (đo 21/11: chuỗi trích có nháy kép) ⇒ gửi lại đúng một lần
CONG_CU = "kiem_trich_dan_toan_van"

# ── Batch API (bác sĩ duyệt 21/11/2026) ───────────────────────────────────────────────────────────────────────────
# VÌ SAO. Đo trên sổ chi phí thật: công cụ này 88 lượt / 726 N token vào — nguồn tốn thứ hai của hệ. Bật cache
# (`cache_he_thong=True` ở `kiem_tai_lieu`) chỉ cứu được phần `HE_THONG` ~816 token × số tài liệu; phần LỚN là ĐOẠN
# TOÀN VĂN của từng tài liệu, mỗi đoạn gửi đúng một lần ⇒ không cache nào tiết kiệm được (docs/BO-NHO-DEM-API.md §1).
# Batch API giảm 50% MỌI khoản và cộng dồn với cache ⇒ đòn lớn cho đúng đường này.
#
# ĐÁNH ĐỔI: bất đồng bộ. OPT-IN (`--batch`); đường gọi trực tiếp vẫn mặc định.
#
# SỔ TRẠNG THÁI giữ ĐÚNG đoạn toàn văn đã gửi. Lý do giống A12 nhưng mạnh hơn: đoạn đó do `tim_toan_van` dựng từ
# thư viện EndNote/PDF của bác sĩ và `doan_lien_quan` cắt theo trần ký tự — dựng lại có thể ra đoạn KHÁC (thư viện
# đổi, trần đổi, PDF khác bản) ⇒ báo cáo sẽ nói về đoạn mà model KHÔNG đọc. Đó là lỗi liêm chính.
TEN_SO_BATCH = "A12_TOAN_VAN_batch_{study}.json"
_CID_TL = "ktv_tl_{so:05d}"
NGUONG_TIEU_DE = 0.35  # tỷ lệ từ dài của dòng TLTK có trong phần đầu toàn văn — dưới ngưỡng ⇒ nghi gắn nhầm PDF
_TU_DUNG = {"the", "and", "with", "from", "that", "this", "were", "was", "for", "are", "among", "study", "patients",
            "patient", "using", "between", "into", "which", "their", "have", "has", "been", "than", "more"}

HE_THONG = (
    "Bạn là người kiểm trích dẫn (vai kiem-chung-trich-dan) cho đề cương nghiên cứu y khoa. Lượt trước chỉ thấy "
    "ABSTRACT và đánh dấu các cặp dưới đây là cần xem. Nay bạn được xem các ĐOẠN TRÍCH TỪ TOÀN VĂN của tài liệu (không "
    "phải toàn bộ bài). Với MỖI câu khẳng định, chỉ dựa trên các đoạn đã cho (không dùng trí nhớ về bài báo), xếp một "
    "mức:\n"
    "- ho_tro: toàn văn nêu rõ điều câu khẳng định gán cho tài liệu này (kể cả con số, quần thể, chiều hiệu ứng);\n"
    "- ho_tro_mot_phan: toàn văn nói khác hoặc vắng đúng một chi tiết câu gán RIÊNG cho tài liệu (nêu chi tiết "
    "nào);\n"
    "- khong_ho_tro: toàn văn nói khác/ngược, số khác, hoặc bài thuộc chủ đề/quần thể/thiết kế khác hẳn;\n"
    "- khong_du_can_cu: các đoạn đã cho không chứa phần liên quan — KHÔNG kết luận được (không phải lỗi).\n"
    "Phạm vi một tài liệu [n]: chỉ xét phần câu mà [n] được giao chống đỡ; câu trích nhiều tài liệu cùng lúc được "
    "chống đỡ CHUNG; tên tác giả/năm/tạp chí không dùng để hạ mức; câu chung «được tham khảo khi…» chỉ đòi đúng chủ "
    "đề.\n"
    "Luật: «trich» là cụm NGUYÊN VĂN ≤ 25 từ chép đúng từng chữ từ CÁC ĐOẠN ĐÃ CHO, bắt buộc với ho_tro/"
    "ho_tro_mot_phan/khong_ho_tro, để trống với khong_du_can_cu. ly_do ≤ 30 từ, tiếng Việt. Trả DUY NHẤT JSON "
    '{"ket_qua":[{"id":"C001","so":5,"muc":"ho_tro","trich":"…","ly_do":"…"}]} — đủ mọi cặp được giao, không thêm '
    "cặp lạ."
)


# ── Đọc toàn văn ─────────────────────────────────────────────────────────────────────────────────────────────────────
def van_pmc_xml(p: Path) -> str:
    """Chữ của bài PMC (tiêu đề, abstract, thân, bảng) — mỗi đoạn một dòng."""
    goc = ET.parse(p).getroot()
    dong: List[str] = []
    for the in goc.iter():
        ten = the.tag.rsplit("}", 1)[-1]
        if ten in ("article-title", "title", "p", "td", "th", "caption"):
            s = " ".join("".join(the.itertext()).split())
            if s and (not dong or dong[-1] != s):
                dong.append(s)
    return "\n".join(dong)


def van_pdf(du_lieu: bytes) -> str:
    try:
        from app.sources.guideline_fulltext_common import trich_van_ban_tu_pdf  # noqa: PLC0415
    except Exception:  # thiếu pypdf/engine — không đọc được, không đoán
        return ""
    return trich_van_ban_tu_pdf(du_lieu, None) or ""


def _nap_endnote_goc() -> Any:
    """Mô-đun `endnote_suc_khoe` của repo gốc (repo y khoa nằm lồng trong workspace gốc, hoặc EBM_WORKSPACE_ROOT)."""
    for goc in filter(None, (os.environ.get("EBM_WORKSPACE_ROOT"), str(REPO.parent))):
        p = Path(goc) / "tools" / "endnote_suc_khoe.py"
        if p.is_file():
            spec = importlib.util.spec_from_file_location("endnote_suc_khoe_goc", p)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    return None


def pdf_endnote(tl: Any, thu_vien: Optional[Path], es: Any) -> Tuple[Optional[Path], str]:
    """(đường dẫn PDF, ghi chú) của bản ghi EndNote khớp PMID rồi DOI; tra trên bản sao tạm, chỉ đọc."""
    if es is None or thu_vien is None:
        return None, "EndNote: không có công cụ/thư viện (⚪ không đo được)"
    try:
        with es.ban_sao_csdl(thu_vien) as kn:
            rec: List[int] = []
            if tl.pmid:
                rec = [r for (r,) in kn.execute(
                    "SELECT id FROM refs WHERE trim(accession_number) = ? AND trash_state = 0", (tl.pmid,))]
            if not rec and tl.doi:
                d = es._chuan_doi(tl.doi)
                rec = [r for (r,) in kn.execute(
                    "SELECT id FROM refs WHERE lower(trim(electronic_resource_number)) IN (?, ?) AND trash_state = 0",
                    (d, "https://doi.org/" + d))]
            tep = [fp for r in rec for (fp,) in kn.execute("SELECT file_path FROM file_res WHERE refs_id = ?", (r,))]
    except Exception as exc:  # thư viện đang ghi/hỏng — không đo được
        return None, f"EndNote: không đọc được ({type(exc).__name__})"
    goc_pdf = thu_vien.with_suffix(".Data") / "PDF"
    for fp in tep:
        p = goc_pdf / str(fp)
        if p.suffix.lower() == ".pdf" and p.is_file() and p.stat().st_size > 0:
            return p, f"EndNote rec {rec[0]}"
    return None, ("EndNote: bản ghi không có PDF đính kèm" if rec else "EndNote: không có bản ghi khớp PMID/DOI")


def _tu_dai(s: str) -> set:
    return {w for w in re.findall(r"\w{5,}", unicodedata.normalize("NFKC", s or "").lower()) if not w.isdigit()}


def khop_tieu_de(tl: Any, van: str) -> float:
    """Tỷ lệ từ dài (≥ 5 chữ) của dòng TLTK xuất hiện trong 6.000 ký tự đầu toàn văn — chỉ dấu bắt PDF gắn nhầm bài."""
    tu = _tu_dai(tl.van)
    return len(tu & _tu_dai(van[:6000])) / len(tu) if tu else 1.0


def tim_toan_van(so: int, tl: Any, out_dir: Path, thu_vien: Optional[Path], es: Any) -> Tuple[str, str]:
    """(chữ toàn văn đã chuẩn NFKC, nguồn) — chữ rỗng thì nguồn là lý do không có. 21/11/2026: chữ PDF tiếng Việt
    trích ra ở dạng tổ hợp (không NFC) ⇒ câu trích của model (NFC) không bao giờ khớp nguyên văn; nay chuẩn NFKC một lần
    (cũng gỡ chữ ghép ﬁ/ﬂ) trước khi gửi và đối chiếu. Toàn văn không khớp tiêu đề dòng TLTK ⇒ không dùng."""
    chu, nguon = _tim_toan_van_tho(so, tl, out_dir, thu_vien, es)
    if not chu:
        return chu, nguon
    chu = unicodedata.normalize("NFKC", chu)
    ty_le = khop_tieu_de(tl, chu)
    if ty_le < NGUONG_TIEU_DE:
        return "", f"{nguon}: phần đầu toàn văn chỉ khớp {ty_le:.0%} từ của dòng TLTK — nghi gắn nhầm bài, không dùng"
    return chu, nguon


def _tim_toan_van_tho(so: int, tl: Any, out_dir: Path, thu_vien: Optional[Path], es: Any) -> Tuple[str, str]:
    if tl.pmid:
        for p in sorted((out_dir / "toan_van_oa").glob(f"PMID-{tl.pmid}_*.xml")):
            try:
                van = van_pmc_xml(p)
            except ET.ParseError:
                continue
            if len(van) >= CHU_TOI_THIEU:
                return van, f"PMC XML {p.name}"
    tay = out_dir / "toan_van_tltk"
    ung = [tay / f"TLTK-{so}.pdf"]
    if tl.pmid:
        ung += sorted(tay.glob(f"PMID-{tl.pmid}*.pdf"))
    if tl.doi:
        ung.append(tay / f"DOI-{tl.doi.lower().replace('/', '_')}.pdf")
    ghi = []
    for p in ung:
        if p.is_file():
            van = van_pdf(p.read_bytes())
            if len(van) >= CHU_TOI_THIEU:
                return van, f"PDF đặt tay {p.name}"
            ghi.append(f"{p.name} không có lớp chữ")
    p, ly_do = pdf_endnote(tl, thu_vien, es)
    if p is not None:
        van = van_pdf(p.read_bytes())
        if len(van) >= CHU_TOI_THIEU:
            return van, ly_do
        ghi.append(f"{ly_do}: PDF không có lớp chữ (quét ảnh?)")
    else:
        ghi.append(ly_do)
    return "", "; ".join(ghi) or "không có toàn văn"


# ── Chọn đoạn liên quan ──────────────────────────────────────────────────────────────────────────────────────────────
def _so(s: str) -> set:
    """Số đã chuẩn hoá để so hai ngôn ngữ: phẩy thập phân → chấm, bỏ số 0 đầu («0,78» ≡ «0.78» ≡ «.78» — bài tiếng
    Anh hay viết «.78»), bỏ số trong ngoặc trích dẫn «[42]», «[38, 41]». Chỉ giữ số có ≥ 2 chữ số."""
    s = re.sub(r"\[[\d,\s–-]+\]", " ", s or "")
    ra = set()
    for x in re.findall(r"\d*[.,]\d+|\d+", s):
        x = x.replace(",", ".")
        x = re.sub(r"^0+(?=\d)", "", x) if "." not in x else re.sub(r"^0+(?=\.)", "", x)
        if sum(ch.isdigit() for ch in x) >= 2:
            ra.add(x)
    return ra


def _tu_khoa(s: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z-]{3,}", (s or "").lower()) if w not in _TU_DUNG}


def doan_lien_quan(van: str, cau: Sequence[str], goi_y: str, toi_da: int = TOI_DA_KY_TU) -> str:
    """Phần đầu (tiêu đề + abstract) + các cửa sổ ~CUA_SO ký tự xếp theo: số của câu khẳng định (×3) và từ khoá tiếng
    Anh của câu trích abstract/tiêu đề tài liệu (×1). Giữ thứ tự xuất hiện; tổng ≤ `toi_da` ký tự."""
    dau = van[:2500]
    so = set().union(*(_so(c) for c in cau)) if cau else set()
    tk = _tu_khoa(goi_y)
    cua = [(i, van[i:i + CUA_SO]) for i in range(2500, len(van), CUA_SO)]
    diem = []
    for i, w in cua:
        d = 3 * len(so & _so(w)) + len(tk & _tu_khoa(w))
        if d:
            diem.append((d, i, w))
    chon, dung = [], len(dau)
    for _d, i, w in sorted(diem, key=lambda x: (-x[0], x[1])):
        if dung + len(w) > toi_da:
            continue
        chon.append((i, w))
        dung += len(w)
    return "\n…\n".join([dau] + [w for _i, w in sorted(chon)])


# ── Lượt kiểm ────────────────────────────────────────────────────────────────────────────────────────────────────────
def cap_can_xem(bc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Cặp «cần xem» của báo cáo A12 (cùng luật `kiem_noi_dung_trich_dan.can_xem`), kèm câu khẳng định."""
    cau = {c["id"]: c for c in bc.get("cau") or []}
    ra = []
    for k in bc.get("ket_qua") or []:
        if k.get("muc") in DK.MUC_A12_CAN_XEM or any(str(x).startswith("so_khong_thay") for x in k.get("co") or []):
            c = cau.get(k["id"]) or {}
            ra.append({**k, "cau": c.get("cau") or c.get("doan") or ""})
    return ra


def co_nguyen_van_toan_van(trich: str, doan: str) -> bool:
    """Nguyên văn như `API.co_nguyen_van`; trượt thì so lần hai bỏ MỌI khoảng trắng — 21/11/2026: PDF tiếng Việt bị
    thư viện đọc PDF cắt dòng giữa từ («b\\nệnh nhân», «t\\nỷ lệ») nên câu trích thật không khớp. Chữ vẫn phải trùng
    từng ký tự; câu model tự diễn đạt lại vẫn bị loại."""
    if API.co_nguyen_van(trich, doan):
        return True
    t = re.sub(r"\s+", "", API.chuan_hoa(trich))
    if len(t) < 15:
        return False
    # 21/11/2026 (Terwee 2007 thật): chữ ngắt dòng bằng gạch nối «high- est» ⇒ so thêm bản bỏ gạch nối cuối dòng
    for d in (doan, re.sub(r"(?<=\w)-\s+(?=\w)", "", doan)):
        if t in re.sub(r"\s+", "", API.chuan_hoa(d)):
            return True
    return False


def loi_nhan_tai_lieu(so: int, cap: List[Dict[str, Any]], doan: str, tltk: str = "") -> str:
    """Lời nhắn cho MỘT tài liệu — tách riêng để đường gọi trực tiếp và đường Batch dùng CHUNG một cách dựng."""
    giao = [{"id": c["id"], "so": so, "cau": c["cau"], "abstract_ket_luan": c["muc"], "abstract_ly_do": c.get("ly_do")}
            for c in cap]
    return ("CÁC CẶP CẦN XÉT LẠI (JSON):\n" + json.dumps(giao, ensure_ascii=False, indent=1)
            + (f"\n\nTÀI LIỆU [{so}] TRONG DANH MỤC THAM KHẢO: {tltk}" if tltk else "")
            + f"\n\nĐOẠN TRÍCH TỪ TOÀN VĂN CỦA TÀI LIỆU [{so}]:\n" + doan)


def doc_tra_loi_tai_lieu(so: int, cap: List[Dict[str, Any]], doan: str, dl: Any) -> List[Dict]:
    """Máy kiểm lại câu trả lời của MỘT tài liệu — dùng chung cho cả hai đường. Câu trích không có nguyên văn trong
    đoạn ĐÃ GỬI ⇒ hạ xuống `khong_xac_minh`, giữ kết luận gốc của máy ở `muc_may` để đối chiếu offline."""
    theo = {(str(x.get("id")), int(x.get("so") or so)): x for x in (dl.get("ket_qua") or []) if isinstance(x, dict)} \
        if isinstance(dl, dict) else {}
    ra = []
    for c in cap:
        x = theo.get((c["id"], so)) or {}
        muc, trich = str(x.get("muc") or ""), str(x.get("trich") or "")
        if muc not in MUC_HOP_LE:
            muc_tv, ly = "khong_xac_minh", "không có phán quyết hợp lệ cho cặp này"
        elif muc != "khong_du_can_cu" and not (trich and co_nguyen_van_toan_van(trich, doan)):
            muc_tv, ly = "khong_xac_minh", "câu trích không có nguyên văn trong đoạn toàn văn đã gửi"
        else:
            muc_tv, ly = muc, str(x.get("ly_do") or "")[:300]
        ra.append({"id": c["id"], "so": so, "cau": c["cau"][:400], "muc_abstract": c["muc"], "muc_toan_van": muc_tv,
                   "trich": trich[:300] if muc_tv in MUC_HOP_LE else "", "ly_do": ly,
                   "trich_may": "" if muc_tv in MUC_HOP_LE else trich[:300],  # chẩn đoán — không trình như trích
                   "muc_may": muc if muc_tv != muc else ""})  # kết luận gốc của máy khi bị hạ (đối chiếu lại offline)
    return ra


def kiem_tai_lieu(so: int, cap: List[Dict[str, Any]], doan: str, model: str, client: Any,
                  tltk: str = "") -> Tuple[List[Dict], Any]:
    """MỘT lượt gọi cho mọi câu của một tài liệu; máy kiểm câu trích có nguyên văn trong đoạn đã gửi."""
    noi = loi_nhan_tai_lieu(so, cap, doan, tltk)
    for lan in range(SO_LAN_THU_JSON_HONG):
        kq = API.goi(noi, he_thong=HE_THONG, model=model, max_tokens=MAX_TOKENS, effort="medium", client=client,
                     # Đo 21/11/2026 trên sổ chi phí thật: công cụ này 88 lượt / 726 N token vào / 0% đọc cache —
                     # thiếu đúng cờ này. `HE_THONG` = 816 token (trên ngưỡng 512) và gửi Y NGUYÊN cho MỖI tài liệu,
                     # nên hoà vốn ngay từ tài liệu thứ hai (xem docs/BO-NHO-DEM-API.md §1).
                     cache_he_thong=True,
                     nguon=CONG_CU)
        try:
            dl = API.doc_json(kq.van_ban)
            break
        except API.KetQuaHong:  # câu trả lời đủ (goi đã kiểm cụt/từ chối) mà JSON hỏng ⇒ gửi lại một lần
            if lan + 1 >= SO_LAN_THU_JSON_HONG:
                raise
    return doc_tra_loi_tai_lieu(so, cap, doan, dl), kq


def _bam(van: str) -> str:
    return hashlib.sha256((van or "").encode("utf-8")).hexdigest()


def duong_so_batch(study: str, ra_dir: Path) -> Path:
    return ra_dir / TEN_SO_BATCH.format(study=study)


def doc_so_batch(duong: Path) -> Optional[Dict[str, Any]]:
    """Sổ batch đang chờ, hoặc None. Sổ hỏng ⇒ LoiCucBo: sổ hỏng có thể đang che một batch ĐÃ TRẢ PHÍ, coi là
    «chưa nộp» rồi nộp lại là trả phí đôi."""
    if not duong.is_file():
        return None
    try:
        st = json.loads(duong.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise API.LoiCucBo(
            f"Sổ batch {duong.name} không đọc được ({type(exc).__name__}) — có thể đang có batch ĐÃ TRẢ PHÍ chờ lấy. "
            "Kiểm tay trên Claude Console trước khi xoá sổ; KHÔNG nộp lại khi chưa rõ."
        ) from exc
    if not isinstance(st, dict) or not (st.get("batch") or {}).get("id"):
        return None
    return st


def nop_batch_ktv(
    co_van: Dict[int, Tuple[str, str]],
    theo_so: Dict[int, List[Dict[str, Any]]],
    tltk: Dict[int, Any],
    khong: List[Dict[str, Any]],
    *,
    model: str,
    van: str,
    client: Any = None,
    duong: Path,
) -> Dict[str, Any]:
    """Nộp MỘT batch cho mọi tài liệu có toàn văn; ghi sổ giữ ĐÚNG đoạn đã gửi. Không có kết quả ở bước này."""
    if not co_van:
        raise API.LoiCucBo("Không tài liệu nào có toàn văn — không nộp batch rỗng.")
    yc = []
    for so, (doan, _nguon) in sorted(co_van.items()):
        tl = tltk.get(so)
        p = API.tham_so(
            loi_nhan_tai_lieu(so, theo_so[so], doan, getattr(tl, "van", "") if tl else ""),
            he_thong=HE_THONG, model=model, max_tokens=MAX_TOKENS, effort="medium", cache_he_thong=True,
        )
        yc.append((_CID_TL.format(so=so), p))
    bid = API.nop_batch(yc, client, nguon=CONG_CU)
    st = {
        "cong_cu": CONG_CU,
        "tep_sha256": _bam(van),
        "he_thong_sha256": _bam(HE_THONG),
        "model": model,
        "batch": {"id": bid, "nop_luc": dt.datetime.now().isoformat(timespec="seconds"), "so_tai_lieu": len(yc)},
        # ĐOẠN TOÀN VĂN đã gửi + nguồn của nó. Dựng lại từ thư viện EndNote/PDF có thể ra đoạn KHÁC ⇒ báo cáo sẽ
        # nói về đoạn model KHÔNG đọc. Khoá JSON là chuỗi; đọc lại phải đổi về int.
        "co_van": {str(so): {"doan": d, "nguon": n} for so, (d, n) in co_van.items()},
        "theo_so": {str(so): ds for so, ds in theo_so.items()},
        # Tài liệu KHÔNG tìm được toàn văn: kết quả của `tim_toan_van` (đọc EndNote/PDF, chậm và không tất định)
        # ⇒ lưu lại, không dò lại lúc lấy kết quả.
        "khong": khong,
    }
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return st


def _tu_so_batch(st: Dict[str, Any]) -> Tuple[Dict[int, Tuple[str, str]], Dict[int, List[Dict[str, Any]]]]:
    co_van = {int(k): (v["doan"], v["nguon"]) for k, v in (st.get("co_van") or {}).items()}
    theo_so = {int(k): v for k, v in (st.get("theo_so") or {}).items()}
    return co_van, theo_so


def lay_batch_ktv(
    st: Dict[str, Any], van: str, *, client: Any = None
) -> Tuple[Optional[List[Dict]], Dict[str, Any]]:
    """Lấy kết quả batch. Chưa xong ⇒ (None, trạng_thái). Xong ⇒ (kết quả, thống kê).

    Canh trước khi ghép: tệp đề cương và lời dặn phải y nguyên lúc nộp — khác ⇒ LoiCucBo."""
    if _bam(van) != st.get("tep_sha256"):
        raise API.LoiCucBo(
            "Tệp đề cương đã ĐỔI sau khi nộp batch — không ghép kết quả cũ vào văn bản mới. Nộp lại batch."
        )
    if _bam(HE_THONG) != st.get("he_thong_sha256"):
        raise API.LoiCucBo("Lời dặn (HE_THONG) đã đổi sau khi nộp batch — kết quả không so sánh được. Nộp lại.")
    tt = API.trang_thai_batch(st["batch"]["id"], client)
    if tt["trang_thai"] != "ended":
        return None, tt
    co_van, theo_so = _tu_so_batch(st)
    ket_batch = API.doc_ket_qua_batch(st["batch"]["id"], client, nguon=CONG_CU)
    ket: List[Dict] = []
    tk: Dict[str, Any] = {
        "vao": 0, "ra": 0, "cache_ghi": 0, "cache_doc": 0,
        "batch": True, "batch_id": st["batch"]["id"], "loi": [],
    }
    for so, (doan, nguon) in sorted(co_van.items()):
        kq = ket_batch.get(_CID_TL.format(so=so))
        if kq is None:
            tk["loi"].append(f"[{so}] batch không trả kết quả cho tài liệu này")
            ket += [
                dict(x, nguon=nguon)
                for x in doc_tra_loi_tai_lieu(so, theo_so[so], doan, {})  # không có phán quyết ⇒ khong_xac_minh
            ]
            continue
        for k in ("vao", "ra", "cache_ghi", "cache_doc"):
            tk[k] += int(kq.get(k, 0) or 0)
        try:
            dl = API.doc_json(API.van_ban_ket_qua_batch(kq, MAX_TOKENS))
        except API.KetQuaHong as exc:
            # Batch không gửi lại được trong cùng lượt (khác đường gọi trực tiếp, vốn thử lại 1 lần).
            tk["loi"].append(f"[{so}] {type(exc).__name__}: {str(exc)[:160]}")
            ket += [dict(x, nguon=nguon) for x in doc_tra_loi_tai_lieu(so, theo_so[so], doan, {})]
            continue
        ket += [dict(x, nguon=nguon) for x in doc_tra_loi_tai_lieu(so, theo_so[so], doan, dl)]
    return ket, tk


def _o(s: Any) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def _dong_chi_phi(bc: Dict[str, Any]) -> str:
    """Dòng chi phí của báo cáo: nêu RÕ đường gọi (Batch = 50%), token cache, và id batch nếu có."""
    tok = bc.get("token") or {}
    batch = str(bc.get("duong") or "") == "batch"
    ra = [
        "Đường gọi: **" + ("Batch API (giảm 50%)" if batch else "gọi trực tiếp") + "**",
        API.in_chi_phi(int(tok.get("vao", 0)), int(tok.get("ra", 0)), str(bc.get("model") or ""), batch=batch),
    ]
    g, d = int(tok.get("cache_ghi", 0) or 0), int(tok.get("cache_doc", 0) or 0)
    ra.append(f"cache: ghi {g:,} · đọc {d:,} token" if (g or d) else "cache: không có token cache nào ở lượt này")
    if bc.get("batch_id"):
        ra.append(f"batch `{bc['batch_id']}`")
    return " · ".join(ra)


def bao_cao_md(bc: Dict[str, Any]) -> str:
    dong = [f"# Kiểm trích dẫn trên toàn văn — {bc['study']}", "",
            f"- Tệp: `{bc['tep']}` · SHA-256 `{str(bc['tep_sha256'])[:12]}…` · báo cáo A12 lúc {bc['a12_luc']} · "
            f"lúc {bc['luc']} · model `{bc.get('model')}`",
            f"- Cặp cần xem từ A12: {bc['so_cap']} · có toàn văn: {bc['so_co_toan_van']} · "
            f"toàn văn chống đỡ: {bc['so_ho_tro']} · còn cần xem: {bc['so_con_xem']}",
            # 21/11/2026: báo cáo cũ KHÔNG in đường gọi lẫn token cache. Giá Batch bằng 50% giá gọi trực tiếp, nên
            # một con số tiền không kèm tên đường là con số dễ đọc sai; token cache thì cho thấy cache có chạy không.
            "- " + _dong_chi_phi(bc),
            "- Chỉ là đoạn chọn lọc từ toàn văn; «khong_du_can_cu» là chưa kết luận được, không phải lỗi. TƯ VẤN.", "",
            "| Đoạn | TL | Abstract | Toàn văn | Trích (toàn văn) | Lý do | Nguồn |", "|---|---|---|---|---|---|---|"]
    for k in bc["ket_qua"]:
        dong.append(f"| {k['id']} | [{k['so']}] | {k['muc_abstract']} | **{k['muc_toan_van']}** | "
                    f"{_o(k['trich'])[:160]} | {_o(k['ly_do'])[:160]} | {_o(k.get('nguon'))[:60]} |")
    if bc["khong_toan_van"]:
        dong += ["", "## Không có toàn văn đọc được (giữ kết luận abstract — bác sĩ xem tay hoặc bổ sung PDF)", ""]
        dong += [f"- [{x['so']}] ({', '.join(x['id'])}): {x['ly_do']}" for x in bc["khong_toan_van"]]
    dong += ["", "Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(dong)


def _ghi(p: Path, chu: str) -> None:
    tmp = p.with_suffix(p.suffix + ".tam")
    tmp.write_text(chu, encoding="utf-8", newline="\n")
    os.replace(tmp, p)


def _ghi_bao_cao(a, tep: Path, bc12: Dict[str, Any], model: str, cap: List[Dict[str, Any]],
                 ket: List[Dict], khong: List[Dict[str, Any]], loi: List[str], tok: Dict[str, Any],
                 co_van: Dict[int, Tuple[str, str]], ra_dir: Path) -> int:
    """Ghi báo cáo + mã thoát — DÙNG CHUNG cho đường gọi trực tiếp và đường Batch, để hai đường không bao giờ
    sinh ra hai khuôn báo cáo khác nhau. Giá in theo ĐÚNG đường đã dùng (Batch = 50%)."""
    ho_tro = sum(1 for k in ket if k["muc_toan_van"] == "ho_tro")
    con = len(cap) - ho_tro
    batch = bool(tok.get("batch"))
    bc = {"schema": "kiem_trich_dan_toan_van/v1", "study": a.study, "tep": tep.name,
          "tep_sha256": hashlib.sha256(tep.read_bytes()).hexdigest(), "a12_luc": bc12.get("luc"),
          "luc": dt.datetime.now().isoformat(timespec="seconds"), "model": model, "token": tok,
          "duong": "batch" if batch else "goi_truc_tiep",
          "usd": API.uoc_chi_phi(tok["vao"], tok["ra"], model, batch=batch,
                                 cache_ghi=tok.get("cache_ghi", 0), cache_doc=tok.get("cache_doc", 0)),
          "loi_dan_sha256": hashlib.sha256(HE_THONG.encode("utf-8")).hexdigest()[:12],
          "so_cap": len(cap), "so_co_toan_van": len(ket), "so_ho_tro": ho_tro, "so_con_xem": con,
          "ket_qua": ket, "khong_toan_van": khong, "loi": loi}
    if tok.get("batch_id"):
        bc["batch_id"] = tok["batch_id"]
    _ghi(ra_dir / f"A12_TOAN_VAN_{a.study}.json", json.dumps(bc, ensure_ascii=False, indent=1) + "\n")
    _ghi(ra_dir / f"A12_TOAN_VAN_{a.study}.md", bao_cao_md(bc))
    print(f"{'🟢' if not con else '🟠'} {ho_tro}/{len(cap)} cặp được toàn văn chống đỡ · còn {con} cần xem · "
          f"{len(khong)} tài liệu không có toàn văn · "
          f"{API.in_chi_phi(tok['vao'], tok['ra'], model, batch=batch)}"
          + (f" · batch `{tok['batch_id']}`" if tok.get("batch_id") else "")
          + f" · báo cáo {ra_dir / ('A12_TOAN_VAN_' + a.study + '.md')}")
    # Mọi tài liệu đều lỗi ⇒ KHÔNG kiểm được, không trả mã thành công.
    if loi and len(loi) >= max(1, len(co_van)):
        return 2
    return 2 if loi else (0 if not con else 1)


def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO, es: Any = "tu_dong") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--goi-api", action="store_true", help="gọi Claude API (TÍNH PHÍ) và ghi báo cáo")
    ap.add_argument("--model", default=None)
    ap.add_argument("--thu-vien", help="tệp .enl của EndNote (mặc định theo ~/.ebm-endnote.json)")
    ap.add_argument("--toi-da-ky-tu", type=int, default=TOI_DA_KY_TU, help="trần ký tự đoạn toàn văn mỗi tài liệu")
    ap.add_argument(
        "--batch",
        action="store_true",
        help="dùng Batch API: giảm 50% mọi khoản nhưng BẤT ĐỒNG BỘ (nộp xong phải quay lại lấy kết quả)",
    )
    ap.add_argument("--chi-lay", action="store_true", help="chỉ LẤY kết quả batch đã nộp, KHÔNG nộp batch mới")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    if a.chi_lay and not a.batch:
        print("❌ --chi-lay chỉ dùng cùng --batch (đường gọi trực tiếp không có gì để lấy lại).")
        return 3
    out_dir = goc / "exports" / a.study
    tep = out_dir / f"DE_CUONG_NOP_HOI_DONG_{a.study}.md"
    p12 = out_dir / "kiem_may_api" / f"A12_KIEM_NOI_DUNG_{a.study}.json"
    if not tep.is_file():
        print(f"❌ Không thấy {tep}")
        return 3
    try:
        model = API.chon_model(a.model)
        bc12 = json.loads(p12.read_text(encoding="utf-8"))
    except API.LoiApi as exc:
        print(f"❌ {exc}")
        return 3
    except (OSError, ValueError):
        print(f"⚪ Chưa có báo cáo A12 đọc được ({p12.name}) — chạy `kiem_noi_dung_trich_dan.py --goi-api` trước.")
        return 2
    cu, ly_do_cu = DK.hieu_luc(bc12, a.study, goc)
    if cu is not False:
        print(f"⚪ Báo cáo A12 không dùng được cho bản hiện hành ({ly_do_cu}) — chạy lại kiểm A12 trước.")
        return 2
    if es == "tu_dong":
        es = _nap_endnote_goc()
    thu_vien = Path(a.thu_vien) if a.thu_vien else (es.thu_vien_cau_hinh() if es is not None else None)
    van = tep.read_text(encoding="utf-8")
    tltk = KND.tach_tltk(van)
    cap = cap_can_xem(bc12)
    ra_dir = out_dir / "kiem_may_api"
    so_batch = duong_so_batch(a.study, ra_dir)
    try:
        st_cho = doc_so_batch(so_batch) if a.batch else None
    except API.LoiCucBo as exc:
        print(f"⛔ {exc}")
        return 3

    if a.batch and st_cho:
        # ── LẤY kết quả: dùng đoạn toàn văn ĐÃ GỬI trong sổ, KHÔNG dò lại thư viện EndNote/PDF.
        try:
            ket, tok = lay_batch_ktv(st_cho, van, client=client)
        except API.LoiCucBo as exc:
            print(f"⛔ {exc}")
            return 3
        except API.ThieuKhoa as exc:
            print(f"⚪ {exc}")
            return 2
        if ket is None:  # tok = trạng thái batch
            print(f"⏳ batch {tok['id']}: đang xử lý {tok['dang_xu_ly']} · xong {tok['xong']} · lỗi {tok['loi']} — "
                  "chạy lại `--batch --chi-lay` sau.")
            return 4
        co_van, _ = _tu_so_batch(st_cho)
        khong = st_cho.get("khong") or []
        loi = list(tok.get("loi") or [])
        so_batch.unlink(missing_ok=True)  # đã lấy xong ⇒ sổ hết nhiệm vụ
        return _ghi_bao_cao(a, tep, bc12, model, cap, ket, khong, loi, tok, co_van, ra_dir)

    theo_so: Dict[int, List[Dict[str, Any]]] = {}
    for c in cap:
        theo_so.setdefault(int(c["so"]), []).append(c)
    co_van: Dict[int, Tuple[str, str]] = {}
    khong: List[Dict[str, Any]] = []
    for so, ds in sorted(theo_so.items()):
        tl = tltk.get(so)
        if tl is None:
            khong.append({"so": so, "id": [c["id"] for c in ds], "ly_do": "số trích không có trong danh mục TLTK"})
            continue
        chu, nguon = tim_toan_van(so, tl, out_dir, thu_vien, es)
        if chu:
            goi_y = " ".join([tl.van] + [c.get("trich") or "" for c in ds])
            co_van[so] = (doan_lien_quan(chu, [c["cau"] for c in ds], goi_y, a.toi_da_ky_tu), nguon)
        else:
            khong.append({"so": so, "id": [c["id"] for c in ds], "ly_do": nguon})
    vao = sum(API.uoc_token(HE_THONG) + API.uoc_token(d) + 300 * len(theo_so[s]) for s, (d, _n) in co_van.items())
    uoc = API.uoc_chi_phi(vao, 1500 * len(co_van), model, batch=a.batch)
    if not a.goi_api:
        kh = {"study": a.study, "so_cap": len(cap), "so_tai_lieu": len(theo_so), "co_toan_van": {
            s: n for s, (_d, n) in co_van.items()}, "khong_toan_van": khong, "so_luot_goi": len(co_van),
            "duong": "batch" if a.batch else "goi_truc_tiep",
            "uoc_usd": uoc, "uoc_tinh": API.in_chi_phi(vao, 1500 * len(co_van), model, batch=a.batch)}
        if a.json:
            print(json.dumps(kh, ensure_ascii=False, indent=1))
        else:
            print(f"CHẠY KHÔ — {a.study}: {len(cap)} cặp cần xem / {len(theo_so)} tài liệu · có toàn văn "
                  f"{len(co_van)} · thiếu {len(khong)} · {len(co_van)} lượt gọi · ước {kh['uoc_tinh']}. "
                  "Gọi thật: thêm --goi-api (tính phí).")
            for x in khong:
                print(f"  · [{x['so']}] {x['ly_do']}")
        return 0
    if not co_van:
        print("⚪ Không cặp nào có toàn văn đọc được — KHÔNG kiểm được (không phải «đúng hết»).")
        return 2
    try:
        API.kiem_ngan_sach(uoc, model, CONG_CU)
    except API.LoiApi as exc:
        print(f"⛔ {exc}")
        return 2

    if a.batch and a.chi_lay:
        print("Không có batch nào đang chờ — `--chi-lay` không nộp gì.")
        return 0
    if a.batch:
        # ── NỘP batch. Bước này KHÔNG có kết quả; mã 4 = chưa xong.
        try:
            st = nop_batch_ktv(co_van, theo_so, tltk, khong, model=model, van=van, client=client, duong=so_batch)
        except API.ThieuKhoa as exc:
            print(f"⚪ {exc}")
            API.ghi_nhat_ky_api("skipped", str(exc), 0, CONG_CU)
            return 2
        except (API.HetNganSach, API.LoiCucBo) as exc:
            print(f"⛔ {exc}")
            return 2
        print(f"📤 Đã nộp batch {st['batch']['id']} · {st['batch']['so_tai_lieu']} tài liệu · giá Batch (giảm 50%). "
              f"Sổ: {so_batch}\nLấy kết quả: chạy lại cùng lệnh kèm `--batch --chi-lay`.")
        return 4

    ket: List[Dict[str, Any]] = []
    loi: List[str] = []
    # Đếm cả token cache: trước 21/11/2026 sổ chỉ có vao/ra nên báo cáo không cho thấy cache có chạy hay không.
    tok = {"vao": 0, "ra": 0, "cache_ghi": 0, "cache_doc": 0}
    for so, (doan, nguon) in sorted(co_van.items()):
        try:
            ra, kq = kiem_tai_lieu(so, theo_so[so], doan, model, client, tltk[so].van)
        except API.HetNganSach as exc:  # hết tín dụng / chạm trần ⇒ dừng CẢ lượt, không ghi báo cáo dở (21/11/2026)
            print(f"⛔ {exc}")
            return 2
        except API.LoiApi as exc:
            loi.append(f"[{so}] {type(exc).__name__}: {str(exc)[:160]}")
            ket += [{"id": c["id"], "so": so, "cau": c["cau"][:400], "muc_abstract": c["muc"],
                     "muc_toan_van": "khong_xac_minh", "trich": "", "ly_do": "lượt gọi lỗi", "nguon": nguon}
                    for c in theo_so[so]]
            continue
        tok["vao"] += kq.token_vao
        tok["ra"] += kq.token_ra
        tok["cache_ghi"] += kq.token_cache_ghi
        tok["cache_doc"] += kq.token_cache_doc
        ket += [dict(x, nguon=nguon) for x in ra]
    return _ghi_bao_cao(a, tep, bc12, model, cap, ket, khong, loi, tok, co_van, out_dir / "kiem_may_api")


if __name__ == "__main__":
    sys.exit(main())
