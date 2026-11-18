#!/usr/bin/env python3
"""Kiểm TỔNG QUAN TÀI LIỆU G0 bằng Claude API — G0-T3 (tổng hợp bằng chứng) · G0-T4 (khoảng trống). THÍ ĐIỂM 18/11/2026.

VÌ SAO: bác sĩ 18/11/2026 chọn thí điểm API ở hai khâu giá trị cao nhất — «A12 (câu khẳng định có khớp bài gốc
không) và tổng quan tài liệu G0-T3/T4. Sau đó phù hợp thì hãy xây dựng vào hệ thống nghiên cứu». G0-T3/T4 hiện chỉ
có kiểm CẤU TRÚC (`g0_tong_hop.kiem_tong_hop`/`kiem_khoang_trong`): máy không biết bảng sàng lọc ghi đúng thiết kế /
mức liên quan / tóm tắt so với bài gốc không, đoạn tổng hợp có nói đúng điều bài nói không, và phát biểu khoảng trống
có bị chính các bài «liên quan trực tiếp» trả lời rồi không — phần đó trước nay chỉ đánh giá chéo bằng agent (mỗi lần
hội đồng nhiều agent phải hỏi bác sĩ).

BA PHẦN (mỗi phần một kiểu lượt gọi; lời dặn dùng chung cache):
  A. Bảng sàng lọc (`sang_loc` + `nguon_bo_sung` + `sang_loc_khong_loc`): từng bài ↔ tiêu đề + abstract: thiết kế ·
     mức liên quan với PICO ĐÃ CHỐT (`study_meta → gate_params.G0`) · tóm tắt.
  B. Đoạn `tong_hop` + `muc_bang_chung_sau_sang_loc`: mỗi câu dẫn PMID/DOI ↔ abstract — dùng NGUYÊN lời dặn + máy kiểm
     lại của `kiem_noi_dung_trich_dan` (A12, đã sửa theo nhãn bác sĩ 18/11).
  C. Khoảng trống (`G0_KHOANG_TRONG`): phát biểu + loại + mức tính mới ↔ các bài agent xếp «liên quan trực tiếp».
MÁY KIỂM LẠI câu trả lời: mọi «trích» phải có NGUYÊN VĂN trong abstract của đúng bài (phần C: hoặc trong phát biểu
khoảng trống); định danh nêu ra phải thuộc danh sách được giao; số trong tóm tắt của agent phải có trong abstract.
Không khớp ⇒ «máy không xác minh được căn cứ» — không bao giờ coi lời model là đúng khi chưa kiểm được.

Ranh giới: TƯ VẤN, chỉ cảnh báo — không sửa tệp G0, không ghi gate_params, không mở/chặn cổng. CHẠY KHÔ mặc định (in
số lượt gọi + ước chi phí); `--goi-api` mới lấy abstract + gọi API (tính phí, đi qua trần chi phí tháng của
`api_claude_nc`) + ghi báo cáo `exports/<mã>/kiem_may_api/G0_KIEM_TONG_QUAN_<mã>.{md,json}`. Độ đúng đo bằng nhãn bác
sĩ qua `duyet_kiem_may_api.py` (loại báo cáo «G0»). Cần bác sĩ kiểm chứng.

Mã thoát: 0 không có gì cần xem · 1 có mục cần bác sĩ xem · 2 không kiểm được (thiếu tệp/khoá/abstract/API) ·
3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import api_claude_nc as API  # noqa: E402
import g0_tong_hop as GTH  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402

NGUON = "kiem_tong_quan_g0_api"
SO_BAI_MOI_LO = 8
TEN_BAO_CAO = "G0_KIEM_TONG_QUAN_{s}"
NHOM_BAI = ("sang_loc", "nguon_bo_sung", "sang_loc_khong_loc")
MUC_A = {
    "thiet_ke": ("dung", "sai", "khong_du_thong_tin"),
    "lien_quan": ("hop_ly", "khong_hop_ly", "khong_du_thong_tin"),
    "tom_tat": ("trung_thuc", "sai_lech", "khong_du_thong_tin"),
}
MUC_A_DAT = {"dung", "hop_ly", "trung_thuc", "khong_du_thong_tin"}
LOAI_C = ("da_tra_loi", "novelty_khong_khop", "tuyet_doi_hoa", "loai_khong_khop")
LOAI_C_TRICH_BAI = ("da_tra_loi", "novelty_khong_khop")
TEN = {"thiet_ke": "thiết kế", "lien_quan": "mức liên quan", "tom_tat": "tóm tắt",
       "da_tra_loi": "khoảng trống đã có bài trả lời",
       "novelty_khong_khop": "mức tính mới không khớp bằng chứng", "tuyet_doi_hoa": "phát biểu tuyệt đối hoá",
       "loai_khong_khop": "loại khoảng trống không khớp phát biểu"}

HE_THONG_A = (
    "Bạn là người chấm chéo nhiệm vụ G0-T3 (tổng hợp bằng chứng) của một đề cương nghiên cứu y khoa. Với MỖI bài được "
    "giao, chỉ dựa trên TIÊU ĐỀ + LOẠI XUẤT BẢN + ABSTRACT được cung cấp và PICO đã chốt (không dùng trí nhớ về bài "
    "báo), chấm ba trường mà agent đã ghi trong bảng sàng lọc:\n"
    "- thiet_ke: dung (thiết kế agent ghi khớp abstract) · sai (abstract cho thấy thiết kế khác, vd ghi «thử nghiệm "
    "ngẫu nhiên» mà là cắt ngang) · khong_du_thong_tin;\n"
    "- lien_quan: agent xếp truc_tiep / gian_tiep / khong so với PICO. hop_ly · khong_hop_ly (ghi trong ly_do mức nên "
    "là gì) · khong_du_thong_tin. Trực tiếp = cùng quần thể/bối cảnh và cùng kết cục hoặc khái niệm chính của PICO; "
    "gián tiếp = cùng chủ đề nhưng khác quần thể, nước, bối cảnh hoặc kết cục; không = khác chủ đề. Khác nước nhưng "
    "cùng khái niệm là gián tiếp, KHÔNG phải không liên quan;\n"
    "- tom_tat: trung_thuc · sai_lech (số liệu, chiều hiệu ứng hoặc quần thể khác abstract) · khong_du_thong_tin. Phần "
    "nhận xét của agent về mức liên quan («khác bối cảnh», «chạm trục…») không phải tóm tắt — không chấm.\n"
    "Luật: mức sai / khong_hop_ly / sai_lech phải kèm «trich» là cụm NGUYÊN VĂN ≤ 25 từ chép đúng từng chữ từ tiêu đề "
    "hoặc abstract của CHÍNH bài đó, và ly_do ≤ 30 từ tiếng Việt; mức khác để trich rỗng. Không chắc thì "
    "khong_du_thong_tin — KHÔNG đoán. Trả DUY NHẤT một đối tượng JSON: "
    '{"ket_qua":[{"id":"B001","thiet_ke":{"muc":"dung","trich":"","ly_do":""},'
    '"lien_quan":{"muc":"hop_ly","trich":"","ly_do":""},"tom_tat":{"muc":"trung_thuc","trich":"","ly_do":""}}]}'
    " — đủ mọi id được giao, không thêm id lạ."
)

HE_THONG_C = (
    "Bạn là người chấm chéo nhiệm vụ G0-T4 (khoảng trống nghiên cứu) của một đề cương y khoa. Được cho: PICO đã chốt; "
    "PHÁT BIỂU KHOẢNG TRỐNG, loại khoảng trống, mức tính mới và ý nghĩa mà agent đề xuất; các bài agent xếp «liên quan "
    "trực tiếp» (tiêu đề + loại xuất bản + abstract). Chỉ dựa trên văn bản được cho, tìm vấn đề CÓ CĂN CỨ:\n"
    "- da_tra_loi: một bài được cho đã trả lời ĐÚNG câu hỏi PICO trong CÙNG quần thể và bối cảnh mà phát biểu nói "
    "«chưa có» (cùng chủ đề nhưng khác nước/bối cảnh/kết cục thì KHÔNG tính);\n"
    "- novelty_khong_khop: mức tính mới khai không khớp bằng chứng (vd «mới hoàn toàn» trong khi có bài cùng câu "
    "hỏi);\n"
    "- tuyet_doi_hoa: phát biểu khẳng định tuyệt đối («chưa từng», «lần đầu tiên») vượt phạm vi tìm đã khai;\n"
    "- loai_khong_khop: loại khoảng trống khai không khớp nội dung phát biểu.\n"
    "Luật: da_tra_loi / novelty_khong_khop ghi «dinh_danh» đúng như danh sách (vd «PMID 12345678» hoặc «doi:10.x/y») "
    "và «trich» NGUYÊN VĂN ≤ 25 từ từ abstract của CHÍNH bài đó; tuyet_doi_hoa / loai_khong_khop để dinh_danh rỗng và "
    "trích NGUYÊN VĂN từ phát biểu/ý nghĩa. ly_do ≤ 40 từ tiếng Việt. Không có vấn đề có căn cứ thì trả danh sách "
    'rỗng — KHÔNG bịa vấn đề cho có. Trả DUY NHẤT JSON: {"van_de":[{"loai":"da_tra_loi","dinh_danh":"PMID 1",'
    '"trich":"…","ly_do":"…"}]}'
)


# ── đọc đầu vào ───────────────────────────────────────────────────────────────────────────────────────────────────
def pico_da_chot(out_dir: Path) -> str:
    """PICO đã chốt (study_meta → gate_params.G0) dạng văn bản ngắn cho lời nhắn. Thiếu ⇒ chuỗi rỗng."""
    try:
        g0 = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {}
              ).get("G0") or {}
    except (OSError, ValueError):
        return ""
    nhan = (("population", "Quần thể (P)"), ("intervention", "Can thiệp/phơi nhiễm (I/E)"),
            ("comparison", "So sánh (C)"), ("primary_outcome", "Kết cục chính (O)"),
            ("primary_outcome_measure", "Cách đo kết cục chính"), ("question_type", "Loại câu hỏi"))
    return "\n".join(f"- {t}: {str(g0[k])[:500]}" for k, t in nhan if str(g0.get(k) or "").strip())


def bai_cua_g0(th: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Mọi bài của bảng sàng lọc G0-T3, mỗi bài một mã B001… (theo thứ tự nhóm rồi thứ tự trong nhóm)."""
    ra: List[Dict[str, Any]] = []
    for nhom in NHOM_BAI:
        for b in th.get(nhom) or []:
            if not isinstance(b, dict):
                continue
            pm = str(b.get("pmid") or "").strip()
            doi = str(b.get("doi") or "").strip().lower()
            if not (re.fullmatch(r"\d{6,9}", pm) or doi.startswith("10.")):
                continue
            ra.append({"id": f"B{len(ra) + 1:03d}", "nhom": nhom, "pmid": pm or None, "doi": doi or None,
                       "thiet_ke_that": str(b.get("thiet_ke_that") or ""), "lien_quan": str(b.get("lien_quan") or ""),
                       "tom_tat": str(b.get("tom_tat") or ""), "ly_do": str(b.get("ly_do") or "")})
    return ra


def dinh_danh(b: Dict[str, Any]) -> str:
    return f"PMID {b['pmid']}" if b.get("pmid") else f"doi:{b.get('doi')}"


def lay_abstract_bai(bai: Sequence[Dict[str, Any]], lay=None, lay_doi=None) -> Tuple[Dict[str, Dict], Dict[str, str]]:
    """({dinh_danh: bản ghi có abstract}, {dinh_danh: lý do không dùng được}) — PubMed theo PMID, Europe PMC/Crossref
    cho bài chỉ có DOI (dùng chung đường lấy của A12). `lay`/`lay_doi` tiêm được cho kiểm thử."""
    if lay is None:
        from app.sources.pubmed import PubMedClient  # noqa: PLC0415

        lay = PubMedClient().fetch_abstracts
    pmids = sorted({b["pmid"] for b in bai if b.get("pmid")})
    ban: Dict[str, Dict[str, Any]] = {}
    for i in range(0, len(pmids), 100):
        ban.update(lay(pmids[i:i + 100]) or {})
    dung: Dict[str, Dict] = {}
    ly_do: Dict[str, str] = {}
    for b in bai:
        if not b.get("pmid"):
            continue
        r = ban.get(b["pmid"]) or {}
        if r.get("status") != "resolved" or not str(r.get("abstract") or "").strip():
            ly_do[dinh_danh(b)] = f"{r.get('status', 'không có')} — {r.get('reason', 'không có abstract')}".strip(" —")
        else:
            dung[dinh_danh(b)] = r
    chi_doi = sorted({b["doi"] for b in bai if not b.get("pmid") and b.get("doi")})
    if chi_doi:
        bd = (lay_doi or KND.lay_abstract_theo_doi)(chi_doi) or {}
        for d in chi_doi:
            r = bd.get(d) or {}
            if r.get("status") != "resolved" or not str(r.get("abstract") or "").strip():
                ly_do[f"doi:{d}"] = f"{r.get('status', 'không có')} — {r.get('reason', '')}".strip(" —")
            else:
                dung[f"doi:{d}"] = r
    return dung, ly_do


# ── phần A: bảng sàng lọc ─────────────────────────────────────────────────────────────────────────────────────────
def _khoi_bai(b: Dict[str, Any], r: Dict[str, Any]) -> str:
    return (f"[{b['id']}] {dinh_danh(b)}\nTiêu đề: {r.get('title', '')}\n"
            f"Loại xuất bản: {', '.join(r.get('publication_types') or []) or 'không ghi'}\n"
            f"Abstract:\n{r.get('abstract', '')}\n— Agent ghi: thiết kế «{b['thiet_ke_that']}» · mức liên quan "
            f"«{b['lien_quan']}» · tóm tắt «{b['tom_tat']}»"
            + (f" · lý do «{b['ly_do']}»" if b.get("ly_do") else ""))


def loi_nhan_a(lo: Sequence[Dict[str, Any]], tai_lieu: Dict[str, Dict], pico: str) -> str:
    return ("PICO ĐÃ CHỐT:\n" + (pico or "(không có)") + "\n\nBÀI CẦN CHẤM:\n\n"
            + "\n\n---\n\n".join(_khoi_bai(b, tai_lieu[dinh_danh(b)]) for b in lo))


def kiem_tra_a(lo: Sequence[Dict[str, Any]], dl: Any, tai_lieu: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Máy kiểm lại câu trả lời phần A: đủ id, mức hợp lệ, trích nguyên văn, số trong tóm tắt agent có trong
    abstract."""
    theo = {str(m.get("id")): m for m in (dl.get("ket_qua") if isinstance(dl, dict) else None) or []
            if isinstance(m, dict)}
    ra: List[Dict[str, Any]] = []
    for b in lo:
        r = tai_lieu[dinh_danh(b)]
        nguon = f"{r.get('title', '')}\n{r.get('abstract', '')}"
        m = theo.get(b["id"])
        for truong, hop_le in MUC_A.items():
            o = (m or {}).get(truong) if isinstance((m or {}).get(truong), dict) else None
            kq = {"id": b["id"], "dinh_danh": dinh_danh(b), "nhom": b["nhom"], "truong": truong, "co": []}
            if o is None:
                ra.append({**kq, "muc": "khong_kiem_duoc", "ly_do": "máy không trả kết quả cho trường này"})
                continue
            muc = str(o.get("muc") or "")
            kq.update(muc=muc if muc in hop_le else "khong_kiem_duoc", trich=str(o.get("trich") or "")[:400],
                      ly_do=str(o.get("ly_do") or "")[:300])
            if muc not in hop_le:
                kq["ly_do"] = f"mức lạ «{muc}» — {kq['ly_do']}"
            elif muc not in MUC_A_DAT and not API.co_nguyen_van(kq["trich"], nguon):
                kq["co"].append("can_cu_khong_khop")
                kq["muc"] = "can_xem"
            if truong == "tom_tat" and kq["muc"] == "trung_thuc":
                thieu = [s for s in KND.so_lieu(b["tom_tat"]) if not KND.so_co_trong(s, nguon)]
                if thieu:
                    kq["co"].append("so_khong_thay:" + ",".join(thieu))
            ra.append(kq)
    return ra


def can_xem_a(k: Dict[str, Any]) -> bool:
    return k["muc"] in ("sai", "khong_hop_ly", "sai_lech", "can_xem") or any(
        str(x).startswith("so_khong_thay") for x in k.get("co") or [])


# ── phần B: đoạn tổng hợp (lời dặn + máy kiểm của A12) ─────────────────────────────────────────────────────────────
_REF = re.compile(r"PMID[:\s]*(\d{6,9})|\bdoi:\s*(10\.\d{4,9}/[^\s;,)\]]+)", re.I)


def doan_tong_hop(th: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """(văn bản đoạn tổng hợp + câu mức bằng chứng đã đổi «PMID n»/«doi:…» thành dấu [k] kiểu A12, {định danh: k}).

    Chuỗi định danh liền nhau («PMID a; PMID b») gộp thành MỘT nhóm «[1, 2]» — để A12 xét cả câu đứng trước nhóm
    (tách rời thì nhóm sau chỉ còn dấu «;» làm đoạn khẳng định)."""
    so: Dict[str, int] = {}
    van = "\n\n".join(x for x in (GTH.muc_sau_sang_loc(th), str(th.get("tong_hop") or "").strip()) if x)

    def _token(m: re.Match) -> str:
        dd = f"PMID {m.group(1)}" if m.group(1) else f"doi:{m.group(2).rstrip('.').lower()}"
        so.setdefault(dd, len(so) + 1)
        return f"⟦{so[dd]}⟧"

    van = _REF.sub(_token, van)
    van = re.sub(r"⟦\d+⟧(?:\s*[;,]\s*⟦\d+⟧)*",
                 lambda m: "[" + ", ".join(re.findall(r"⟦(\d+)⟧", m.group(0))) + "]", van)
    return van, so


def chay_b(th: Dict[str, Any], tai_lieu_dd: Dict[str, Dict], *, model: str, client: Any = None
           ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    van, so = doan_tong_hop(th)
    cau = KND.tach_cau_khang_dinh(van)
    theo_so = {k: dd for dd, k in so.items()}
    tai_lieu = {k: {**tai_lieu_dd[dd], "pmid": dd[5:] if dd.startswith("PMID ") else None,
                    "doi": dd[4:] if dd.startswith("doi:") else None}
                for k, dd in theo_so.items() if dd in tai_lieu_dd}
    if not cau or not tai_lieu:
        return [asdict(c) for c in cau], [], {"so_lo": 0, "token_vao": 0, "token_ra": 0, "lo_loi": 0, "loi": []}
    ket, tk = KND.chay(cau, tai_lieu, model=model, client=client)
    for c in cau:  # cặp không có abstract ⇒ «không kiểm được» như A12
        ket += [KND.KetQua(c.id, n, "khong_kiem_duoc", f"không có abstract dùng được cho {theo_so.get(n)}")
                for n in c.so if n not in tai_lieu]
    ket.sort(key=lambda k: (k.id, k.so))
    return [asdict(c) for c in cau], [{**asdict(k), "dinh_danh": theo_so.get(k.so)} for k in ket], tk


# ── phần C: khoảng trống ──────────────────────────────────────────────────────────────────────────────────────────
def van_ban_khoang_trong(kt: Dict[str, Any]) -> str:
    nv = kt.get("muc_novelty") if isinstance(kt.get("muc_novelty"), dict) else {}
    return (f"PHÁT BIỂU KHOẢNG TRỐNG: {kt.get('phat_bieu_khoang_trong', '')}\n"
            f"LOẠI KHOẢNG TRỐNG: {', '.join(str(x) for x in kt.get('loai_khoang_trong') or [])}\n"
            f"MỨC TÍNH MỚI: {nv.get('muc', '')}\nÝ NGHĨA: {nv.get('y_nghia', '')}")


def loi_nhan_c(kt: Dict[str, Any], truc_tiep: Sequence[Dict[str, Any]], tai_lieu: Dict[str, Dict], pico: str) -> str:
    khoi = [f"{dinh_danh(b)}\nTiêu đề: {tai_lieu[dinh_danh(b)].get('title', '')}\nLoại xuất bản: "
            f"{', '.join(tai_lieu[dinh_danh(b)].get('publication_types') or []) or 'không ghi'}\nAbstract:\n"
            f"{tai_lieu[dinh_danh(b)].get('abstract', '')}" for b in truc_tiep]
    return ("PICO ĐÃ CHỐT:\n" + (pico or "(không có)") + "\n\n" + van_ban_khoang_trong(kt)
            + "\n\nCÁC BÀI AGENT XẾP «LIÊN QUAN TRỰC TIẾP»:\n\n" + ("\n\n---\n\n".join(khoi) or "(không có)"))


def kiem_tra_c(dl: Any, kt: Dict[str, Any], truc_tiep: Sequence[Dict[str, Any]], tai_lieu: Dict[str, Dict]
               ) -> List[Dict[str, Any]]:
    duoc_giao = {dinh_danh(b).lower(): dinh_danh(b) for b in truc_tiep}
    phat_bieu = van_ban_khoang_trong(kt)
    ra: List[Dict[str, Any]] = []
    for i, v in enumerate((dl.get("van_de") if isinstance(dl, dict) else None) or [], 1):
        if not isinstance(v, dict):
            continue
        loai = str(v.get("loai") or "")
        k = {"id": f"K{i:02d}", "loai": loai if loai in LOAI_C else "khong_kiem_duoc",
             "dinh_danh": str(v.get("dinh_danh") or "").strip(), "trich": str(v.get("trich") or "")[:400],
             "ly_do": str(v.get("ly_do") or "")[:400], "co": []}
        if loai not in LOAI_C:
            k["ly_do"] = f"loại lạ «{loai}» — {k['ly_do']}"
        elif loai in LOAI_C_TRICH_BAI:
            dd = duoc_giao.get(re.sub(r"\s+", " ", k["dinh_danh"]).lower().replace("doi: ", "doi:"))
            if not dd:
                k["co"].append("dinh_danh_khong_duoc_giao")
            else:
                k["dinh_danh"] = dd
                r = tai_lieu.get(dd) or {}
                if not API.co_nguyen_van(k["trich"], f"{r.get('title', '')}\n{r.get('abstract', '')}"):
                    k["co"].append("can_cu_khong_khop")
        elif not API.co_nguyen_van(k["trich"], phat_bieu):
            k["co"].append("can_cu_khong_khop")
        k["muc"] = "can_xem" if k["co"] else ("van_de" if loai in LOAI_C else "khong_kiem_duoc")
        ra.append(k)
    return ra


# ── chạy ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _goi_json(noi_dung: str, he_thong: str, model: str, client: Any, tk: Dict[str, Any]) -> Any:
    for lan in range(KND.SO_LAN_THU_JSON_HONG):
        kq = API.goi(noi_dung, he_thong=he_thong, model=model, effort="low", client=client, cache_he_thong=True,
                     nguon=NGUON)
        for t in ("token_vao", "token_ra", "token_cache_ghi", "token_cache_doc"):
            tk[t] = tk.get(t, 0) + getattr(kq, t)
        try:
            return API.doc_json(kq.van_ban)
        except API.KetQuaHong:
            if lan + 1 >= KND.SO_LAN_THU_JSON_HONG:
                raise
            tk["lo_thu_lai"] = tk.get("lo_thu_lai", 0) + 1
    return None  # pragma: no cover


def chay(th: Dict[str, Any], kt: Optional[Dict[str, Any]], tai_lieu: Dict[str, Dict], pico: str, *, model: str,
         client: Any = None, lo: int = SO_BAI_MOI_LO) -> Dict[str, Any]:
    """Ba phần A/B/C. Lô hỏng ⇒ mục của lô «không kiểm được» (không đoán); thiếu khoá / chạm trần ⇒ dừng cả lượt."""
    bai = bai_cua_g0(th)
    co_ab = [b for b in bai if dinh_danh(b) in tai_lieu]
    tk: Dict[str, Any] = {"so_lo": 0, "lo_loi": 0, "lo_loi_api": 0, "loi": []}
    ket_a: List[Dict[str, Any]] = [
        {"id": b["id"], "dinh_danh": dinh_danh(b), "nhom": b["nhom"], "truong": "*", "muc": "khong_kiem_duoc",
         "ly_do": "không có abstract dùng được", "co": []} for b in bai if dinh_danh(b) not in tai_lieu]
    for nhom in API.chia_lo(co_ab, lo):
        tk["so_lo"] += 1
        try:
            ket_a += kiem_tra_a(nhom, _goi_json(loi_nhan_a(nhom, tai_lieu, pico), HE_THONG_A, model, client, tk),
                                tai_lieu)
        except (API.ThieuKhoa, API.HetNganSach):
            raise
        except API.LoiApi as exc:
            tk["lo_loi"] += 1
            tk["lo_loi_api"] += 0 if isinstance(exc, API.KetQuaHong) else 1
            tk["loi"].append(str(exc)[:200])
            ket_a += [{"id": b["id"], "dinh_danh": dinh_danh(b), "nhom": b["nhom"], "truong": "*",
                       "muc": "khong_kiem_duoc", "ly_do": f"lô gọi API lỗi: {str(exc)[:120]}", "co": []} for b in nhom]
    cau_b, ket_b, tk_b = chay_b(th, tai_lieu, model=model, client=client)
    for t in ("so_lo", "lo_loi", "token_vao", "token_ra", "token_cache_ghi", "token_cache_doc"):
        tk[t] = tk.get(t, 0) + tk_b.get(t, 0)
    tk["loi"] += tk_b.get("loi") or []
    ket_c: List[Dict[str, Any]] = []
    if kt:
        truc_tiep = [b for b in co_ab if b["lien_quan"] == "truc_tiep" and b["nhom"] != "sang_loc_khong_loc"]
        tk["so_lo"] += 1
        try:
            ket_c = kiem_tra_c(_goi_json(loi_nhan_c(kt, truc_tiep, tai_lieu, pico), HE_THONG_C, model, client, tk),
                               kt, truc_tiep, tai_lieu)
        except (API.ThieuKhoa, API.HetNganSach):
            raise
        except API.LoiApi as exc:
            tk["lo_loi"] += 1
            tk["loi"].append(str(exc)[:200])
            ket_c = [{"id": "K00", "loai": "khong_kiem_duoc", "muc": "khong_kiem_duoc", "dinh_danh": "", "trich": "",
                      "ly_do": f"lượt gọi API lỗi: {str(exc)[:120]}", "co": []}]
    return {"a": sorted(ket_a, key=lambda k: (k["id"], k["truong"])), "cau_b": cau_b, "b": ket_b, "c": ket_c,
            "thong_ke": tk}


def can_xem_b(k: Dict[str, Any]) -> bool:
    return k.get("muc") in ("khong_ho_tro", "ho_tro_mot_phan", "can_xem") or any(
        str(x).startswith("so_khong_thay") for x in k.get("co") or [])


def so_can_xem(kq: Dict[str, Any]) -> int:
    return (sum(1 for k in kq["a"] if can_xem_a(k)) + sum(1 for k in kq["b"] if can_xem_b(k))
            + sum(1 for k in kq["c"] if k.get("muc") in ("van_de", "can_xem")))


# ── báo cáo ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _o(s: Any) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def bao_cao_md(study: str, kq: Dict[str, Any], model: str, luc: str, ly_do_tl: Dict[str, str]) -> str:
    tk = kq["thong_ke"]
    a_xem = [k for k in kq["a"] if can_xem_a(k)]
    b_xem = [k for k in kq["b"] if can_xem_b(k)]
    c_xem = [k for k in kq["c"] if k.get("muc") in ("van_de", "can_xem")]
    cau = {c["id"]: c for c in kq["cau_b"]}
    d = [f"# Kiểm tổng quan tài liệu G0 bằng máy — {study}", "",
         f"- Lúc {luc} · model `{model}` · {tk.get('so_lo', 0)} lượt gọi ({tk.get('lo_loi', 0)} lỗi) · "
         f"{API.in_chi_phi(tk.get('token_vao', 0), tk.get('token_ra', 0), model)}",
         f"- A. bảng sàng lọc: {len({k['id'] for k in kq['a']})} bài · cần xem {len(a_xem)} trường",
         f"- B. đoạn tổng hợp: {len(kq['cau_b'])} đoạn dẫn nguồn · cần xem {len(b_xem)} cặp",
         f"- C. khoảng trống: {len(c_xem)} vấn đề", "",
         "So với TIÊU ĐỀ + ABSTRACT (PubMed; bài chỉ có DOI: Europe PMC/Crossref), không phải toàn văn. Mọi «trích» đã "
         "được máy đối chiếu nguyên văn; không khớp thì xếp «máy không xác minh được căn cứ».", "",
         "## A. Bảng sàng lọc G0-T3 — cần bác sĩ xem", "",
         "| Mã | Bài | Nhóm | Trường | Máy phán | Lý do / cờ | Căn cứ trong abstract |",
         "|---|---|---|---|---|---|---|"]
    d += [f"| {k['id']} | {_o(k['dinh_danh'])} | {k['nhom']} | {TEN.get(k['truong'], k['truong'])} | {k['muc']} | "
          f"{_o(k.get('ly_do'))}{(' — ' + ', '.join(k['co'])) if k.get('co') else ''} | {_o(k.get('trich'))} |"
          for k in a_xem] or ["| — | — | — | — | Không có trường nào cần xem theo máy | — | — |"]
    d += ["", "## B. Đoạn tổng hợp G0-T3 — cần bác sĩ xem", "",
          "| Mã | Đoạn | Tài liệu | Mức | Lý do / cờ | Căn cứ |", "|---|---|---|---|---|---|"]
    d += [f"| {k['id']} | {_o((cau.get(k['id']) or {}).get('doan'))[:300]} | {_o(k.get('dinh_danh'))} | "
          f"{KND.TEN_MUC.get(k['muc'], k['muc'])} | {_o(k.get('ly_do'))}"
          f"{(' — ' + ', '.join(k['co'])) if k.get('co') else ''} | {_o(k.get('trich'))} |" for k in b_xem] or [
        "| — | Không có đoạn nào cần xem theo máy | — | — | — | — |"]
    d += ["", "## C. Khoảng trống G0-T4", "", "| Mã | Vấn đề | Bài | Lý do / cờ | Căn cứ |", "|---|---|---|---|---|"]
    d += [f"| {k['id']} | {TEN.get(k['loai'], k['loai'])} | {_o(k.get('dinh_danh')) or '—'} | {_o(k.get('ly_do'))}"
          f"{(' — ' + ', '.join(k['co'])) if k.get('co') else ''} | {_o(k.get('trich'))} |" for k in c_xem] or [
        "| — | Máy không thấy vấn đề có căn cứ | — | — | — |"]
    kkd = [k for k in kq["a"] + kq["b"] + kq["c"] if k.get("muc") == "khong_kiem_duoc"]
    d += ["", "## Không kiểm được", ""] + ([f"- {k.get('id')} {k.get('dinh_danh') or ''}: {k.get('ly_do')}"
                                              for k in kkd] or ["- Không có."])
    d += ["", "## Bài không dùng được abstract", ""] + ([f"- {k}: {v}" for k, v in sorted(ly_do_tl.items())]
                                                        or ["- Không có."])
    if tk.get("loi"):
        d += ["", "## Lỗi lượt gọi", ""] + [f"- {x}" for x in tk["loi"]]
    d += ["", API.DISCLAIMER, ""]
    return "\n".join(d)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()  # cùng cách duyet_kiem_may_api


def main(argv: Optional[Sequence[str]] = None, client: Any = None, lay=None, lay_doi=None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--goi-api", action="store_true", help="lấy abstract + GỌI Claude API (tính phí) + ghi báo cáo")
    ap.add_argument("--model", default=None)
    ap.add_argument("--lo", type=int, default=SO_BAI_MOI_LO, help="số bài mỗi lượt gọi (phần A)")
    ap.add_argument("--ra", help="thư mục ghi báo cáo (mặc định exports/<mã>/kiem_may_api/)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    out = goc / "exports" / a.study
    th, loi_th = GTH.doc(out, GTH.TEP_TONG_HOP, a.study)
    kt, loi_kt = GTH.doc(out, GTH.TEP_KHOANG_TRONG, a.study)
    if loi_th or not th:
        print(f"⚪ Không kiểm được: {loi_th or GTH.TEP_TONG_HOP.format(study=a.study) + ' chưa có'} (G0-T3).")
        return 2
    try:
        model = API.chon_model(a.model)
    except API.LoiApi as exc:
        print(f"❌ {exc}")
        return 3
    pico = pico_da_chot(out)
    bai = bai_cua_g0(th)
    van_b, so_b = doan_tong_hop(th)
    if not a.goi_api:
        so_lo = len(API.chia_lo(bai, a.lo)) + len(API.chia_lo(KND.tach_cau_khang_dinh(van_b), KND.SO_CAU_MOI_LO)) \
            + (1 if kt else 0)
        vao = (len(API.chia_lo(bai, a.lo)) * (API.uoc_token(HE_THONG_A) + API.uoc_token(pico))
               + len(bai) * (KND.TOKEN_MOI_ABSTRACT + 120) + len(so_b) * KND.TOKEN_MOI_ABSTRACT
               + (API.uoc_token(HE_THONG_C) + KND.TOKEN_MOI_ABSTRACT * sum(1 for b in bai if b["lien_quan"] ==
                                                                            "truc_tiep") if kt else 0))
        ra_tok = len(bai) * 3 * 60 + len(so_b) * 90 + (600 if kt else 0)
        kh = {"study": a.study, "so_bai": len(bai), "theo_nhom": {n: sum(1 for b in bai if b["nhom"] == n)
                                                                 for n in NHOM_BAI},
              "so_dinh_danh_doan_tong_hop": len(so_b), "co_khoang_trong": bool(kt), "loi_khoang_trong": loi_kt,
              "pico": bool(pico), "so_luot_goi": so_lo, "uoc_tinh": API.in_chi_phi(vao, ra_tok, model)}
        if a.json:
            print(json.dumps(kh, ensure_ascii=False, indent=1))
        else:
            print(f"CHẠY KHÔ — {a.study}: {len(bai)} bài bảng sàng lọc ({kh['theo_nhom']}), {len(so_b)} định danh "
                  f"trong đoạn tổng hợp, khoảng trống: {'có' if kt else 'chưa có tệp'}; PICO đã chốt: "
                  f"{'có' if pico else 'KHÔNG'}.")
            print(f"Sẽ gọi {so_lo} lượt · ước {kh['uoc_tinh']}. Gọi thật: thêm --goi-api (tính phí).")
        return 0
    try:
        tai_lieu, ly_do_tl = lay_abstract_bai(bai, lay, lay_doi)
        # đoạn tổng hợp có thể dẫn bài ngoài bảng sàng lọc — lấy thêm abstract cho đủ
        them = [{"id": "", "pmid": dd[5:], "doi": None} if dd.startswith("PMID ") else
                {"id": "", "pmid": None, "doi": dd[4:]} for dd in so_b if dd not in tai_lieu and dd not in ly_do_tl]
        if them:
            t2, l2 = lay_abstract_bai(them, lay, lay_doi)
            tai_lieu.update(t2)
            ly_do_tl.update(l2)
    except Exception as exc:  # mạng/NCBI — không kết luận gì
        print(f"⚪ Không lấy được abstract: {type(exc).__name__}: {exc}")
        return 2
    if not tai_lieu:
        print("⚪ Không bài nào có abstract dùng được — KHÔNG kiểm được (không phải «đúng hết»).")
        return 2
    try:
        kq = chay(th, kt, tai_lieu, pico, model=model, client=client, lo=a.lo)
    except API.ThieuKhoa as exc:
        print(f"⚪ {exc}")
        API.ghi_nhat_ky_api("skipped", str(exc), 0, NGUON)
        return 2
    except API.HetNganSach as exc:
        print(f"⛔ {exc}")
        return 2
    luc = dt.datetime.now().isoformat(timespec="seconds")
    ra_dir = Path(a.ra) if a.ra else out / "kiem_may_api"
    ra_dir.mkdir(parents=True, exist_ok=True)
    ten = TEN_BAO_CAO.format(s=a.study)
    (ra_dir / f"{ten}.md").write_text(bao_cao_md(a.study, kq, model, luc, ly_do_tl), encoding="utf-8", newline="\n")
    p_th = out / GTH.TEP_TONG_HOP.format(study=a.study)
    p_kt = out / GTH.TEP_KHOANG_TRONG.format(study=a.study)
    (ra_dir / f"{ten}.json").write_text(json.dumps({
        "schema": "kiem_tong_quan_g0/v1", "study": a.study, "tep": p_th.name, "tep_sha256": _sha(p_th),
        "tep_phu": {p_kt.name: _sha(p_kt)} if kt else {}, "luc": luc, "model": model,
        "loi_dan_sha256": hashlib.sha256((HE_THONG_A + HE_THONG_C + KND.HE_THONG).encode("utf-8")).hexdigest()[:12],
        "pico": pico, "thong_ke": {k: v for k, v in kq["thong_ke"].items() if k != "loi"},
        "loi": kq["thong_ke"].get("loi", []), "a": kq["a"], "cau_b": kq["cau_b"], "b": kq["b"], "c": kq["c"],
        "bai_khong_dung": ly_do_tl, "luu_y": API.DISCLAIMER}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    tk = kq["thong_ke"]
    API.ghi_nhat_ky_api("error" if tk["so_lo"] and tk.get("lo_loi_api", 0) == tk["so_lo"] else "ok",
                        "; ".join(tk.get("loi", []))[:200], len(kq["a"]) + len(kq["b"]) + len(kq["c"]), NGUON)
    xem = so_can_xem(kq)
    print(f"{'🟠' if xem else '🟢'} {xem} mục cần bác sĩ xem · báo cáo {ra_dir / (ten + '.md')}")
    if tk["so_lo"] and tk["lo_loi"] == tk["so_lo"]:
        return 2
    return 1 if xem else 0


if __name__ == "__main__":
    sys.exit(main())
