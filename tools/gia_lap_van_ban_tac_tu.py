#!/usr/bin/env python3
"""gia_lap_van_ban_tac_tu.py — ba văn bản do AGENT soạn mà bộ giả lập trọn vòng trước đây bỏ trống (19/11/2026).

★ VÌ SAO TỒN TẠI: đo 24 đề tài giả lập ngày 19/11/2026 bằng bảng trách nhiệm cổng (`hoi_dong_cong.py trach-nhiem`),
mọi trục máy sạch nhưng cả 24 đề tài còn đúng 72 lượt «agent còn việc» = 3 nhiệm vụ × 24:

  · G0-T3 `tong-quan-y-van`        → `G0_TONG_HOP_BANG_CHUNG_<mã>.json` (khuôn + kiểm: `tools/g0_tong_hop.py`)
  · G0-T4 `khoang-trong-nghien-cuu` → `G0_KHOANG_TRONG_<mã>.json`       (khuôn + kiểm: `tools/g0_tong_hop.py`)
  · G10-T3 `so-cai-ghi-nho`         → `SO_TRANG_THAI_<mã>.md`            (khuôn + kiểm: `tools/clinical_checkpoint.py`)

Đề tài thật có ba văn bản này (agent đọc bài, soạn tay). Bộ giả lập không mô phỏng việc soạn nên «hoàn thiện» của
đề tài giả lập không đo được. Mô-đun này đóng vai ba agent đó cho đề tài TẠM (mã ZZCANARY-), theo luật TẤT ĐỊNH
đọc được — mọi đầu ra đi qua ĐÚNG bộ kiểm của hệ (`g0_tong_hop.kiem_tong_hop/kiem_khoang_trong`,
`hoi_dong_cong._kiem_so_trang_thai`), không nới bộ kiểm nào.

SÀNG LỌC LÀ THEO TIÊU ĐỀ, KHÔNG PHẢI ĐỌC BÀI. Máy chia truy vấn G0 thành các khối AND; khối mà phần lớn thuật ngữ
là thiết kế (case-control, qualitative…) hay bối cảnh (ngoại trú, chăm sóc ban đầu — khác bối cảnh vẫn là trực tiếp
theo thang 18/11/2026) thì bỏ; tiêu đề chạm MỌI khối khái niệm ⇒ «trực tiếp», thiếu đúng một khối
(≥ 2 khối) ⇒ «gián tiếp», còn lại ⇒ «không liên quan» kèm lý do — TRỪ bài mà hồ sơ đề tài đã dẫn làm bằng chứng
(PMID trong nội dung G0/G1 của kịch bản): tiêu đề hay dùng thuật ngữ rộng hơn truy vấn («digital health
interventions», «non-invasive tests») nên không xếp lạc đề chỉ vì tiêu đề, tối thiểu «gián tiếp». Đó là cách
giả lập tạo dữ kiện có cấu trúc để đo dây chuyền — KHÔNG phải sàng lọc có giá trị khoa học; đề tài thật vẫn do agent
`tong-quan-y-van` đọc từng bài.

NHÁNH KHÔNG LỌC VƯỢT TRẦN: luật G0-T3 (17/10/2026) đòi sàng ĐỦ nhánh không lọc thiết kế của truy vấn G0; nền G0 đã lưu
chỉ giữ ≤ 30 bản ghi đầu trong khi nhánh có 53–875 hit. `--tai` (CÓ MẠNG, PubMed E-utilities) lấy đủ PMID + tiêu đề +
loại xuất bản một lần, lưu `<nền G0>/_khong_loc_day_du/<khoá truy vấn>.json` để lượt ngoại tuyến/CI dùng. Vắng tệp
⇒ tổng hợp ghi đủ phần có được, bộ kiểm báo thiếu — không bịa PMID.

Dùng:
    python3 tools/gia_lap_van_ban_tac_tu.py --tai [--nen <thư mục nền G0>]   # có mạng, một lần
    python3 tools/gia_lap_van_ban_tac_tu.py --kiem [--nen <thư mục nền G0>]  # ngoại tuyến: đủ tệp chưa
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
for _p in (str(TOOLS), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_tong_hop as GT  # noqa: E402

THU_MUC_DAY_DU = "_khong_loc_day_du"
SCHEMA_DAY_DU = "gia_lap/khong_loc_day_du/v1"
TRAN_TAI = 2000  # trần an toàn của một lượt tải (nhánh rộng nhất đo 19/11/2026: 875 hit)
NGUOI_SOAN_G0T3 = "tong-quan-y-van"
NGUOI_SOAN_G0T4 = "khoang-trong-nghien-cuu"
NGUOI_GHI_G10T3 = "so-cai-ghi-nho"
TEP_SO_TRANG_THAI = "SO_TRANG_THAI_{study}.md"

# Thuật ngữ THIẾT KẾ trong truy vấn G0 — khối AND chỉ gồm chúng không phải khái niệm của câu hỏi (tiêu đề hiếm khi
# nhắc thiết kế nên giữ chúng sẽ đẩy gần hết bài về «không liên quan»).
TU_THIET_KE = frozenset({
    "case-control", "case-control studies", "qualitative research", "qualitative", "interview", "prevalence",
    "cross-sectional", "randomized controlled trial", "randomized controlled trials", "randomised controlled trial",
    "non-inferiority", "noninferiority", "follow-up", "sensitivity and specificity", "diagnostic accuracy", "auroc",
    "cohort", "cohort studies", "meta-analysis", "systematic review",
    # 23/11/2026 (kịch bản PLS-SEM): phương pháp phân tích là THIẾT KẾ/kỹ thuật, không phải khái niệm của câu hỏi — bài
    # cùng quần thể, phơi nhiễm, kết cục mà tiêu đề không nêu «structural equation» vẫn là liên quan trực tiếp
    "structural equation", "structural equation modeling", "path analysis", "partial least squares", "pls-sem",
})
# Thuật ngữ BỐI CẢNH — theo thang mức liên quan bác sĩ chốt 18/11/2026 (`g0_tong_hop.DINH_NGHIA_LIEN_QUAN`): khác nước
# hay khác bối cảnh VẪN là trực tiếp ⇒ khối chỉ gồm bối cảnh (ngoại trú, chăm sóc ban đầu…) không tính khi xếp mức.
TU_BOI_CANH = frozenset({"outpatient", "outpatients", "ambulatory", "primary care", "primary health care",
                         "community", "rural", "general practice"})

# Loại xuất bản PubMed → thiết kế (thứ tự = ưu tiên).
LOAI_XUAT_BAN = (
    ("Meta-Analysis", "Phân tích gộp"),
    ("Systematic Review", "Tổng quan hệ thống"),
    ("Practice Guideline", "Hướng dẫn thực hành lâm sàng"),
    ("Guideline", "Hướng dẫn thực hành"),
    ("Randomized Controlled Trial", "Thử nghiệm ngẫu nhiên có đối chứng"),
    ("Clinical Trial Protocol", "Đề cương thử nghiệm lâm sàng"),
    ("Clinical Trial", "Thử nghiệm lâm sàng"),
    ("Observational Study", "Nghiên cứu quan sát"),
    ("Multicenter Study", "Nghiên cứu đa trung tâm"),
    ("Comparative Study", "Nghiên cứu so sánh"),
    ("Validation Study", "Nghiên cứu kiểm định"),
    ("Case Reports", "Báo cáo ca bệnh"),
    ("Review", "Tổng quan tường thuật"),
    ("Editorial", "Xã luận"),
    ("Letter", "Thư gửi toà soạn"),
    ("Comment", "Bình luận"),
)
# Nhóm kết quả của nền G0 → thiết kế (khi bản ghi không mang loại xuất bản).
NHOM_NEN = (("guideline", "Hướng dẫn thực hành (bộ lọc guideline của PubMed)"),
            ("sr_ma", "Tổng quan hệ thống hoặc phân tích gộp (bộ lọc loại xuất bản của PubMed)"),
            ("rct", "Thử nghiệm ngẫu nhiên có đối chứng (bộ lọc loại xuất bản của PubMed)"),
            ("observational", "Nghiên cứu quan sát (bộ lọc MeSH thiết kế quan sát của PubMed)"))
TU_TIEU_DE_THIET_KE = (
    (r"meta-analys", "Phân tích gộp (suy từ tiêu đề)"),
    (r"systematic review", "Tổng quan hệ thống (suy từ tiêu đề)"),
    (r"randomi[sz]ed", "Thử nghiệm ngẫu nhiên (suy từ tiêu đề)"),
    (r"\bcohort\b", "Nghiên cứu thuần tập (suy từ tiêu đề)"),
    (r"case-control", "Nghiên cứu bệnh–chứng (suy từ tiêu đề)"),
    (r"cross-sectional", "Nghiên cứu cắt ngang (suy từ tiêu đề)"),
    (r"qualitative", "Nghiên cứu định tính (suy từ tiêu đề)"), (r"guideline", "Hướng dẫn (suy từ tiêu đề)"),
)


# ════════════════════════════════════════════════════════════════════════════════════════ tiện ích
def _ghi_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def khoa_truy_van(truy_van: str) -> str:
    """Khoá tệp nhánh đầy đủ = 16 ký tự đầu SHA-256 của truy vấn đã gộp khoảng trắng (5 kịch bản RCT dùng chung một
    truy vấn ⇒ một tệp)."""
    return hashlib.sha256(" ".join(str(truy_van).split()).encode("utf-8")).hexdigest()[:16]


def nhanh_khong_loc(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Provenance nhánh KHÔNG lọc thiết kế của `G0_pubmed_raw.json` ({} nếu lượt G0 chưa có nhánh này)."""
    kl = ((raw.get("search_provenance") or {}).get("nhanh") or {}).get("khong_loc")
    return kl if isinstance(kl, dict) else {}


# ════════════════════════════════════════════════════════════════════════════════════════ tải nhánh đầy đủ (mạng)
def tai_nhanh_day_du(truy_van: str, tran: int = TRAN_TAI) -> Dict[str, Any]:
    """CÓ MẠNG: esearch (PMID, sắp theo ngày) + esummary theo lô 200 → {pmid, title, year, journal, pubtypes}.

    Lỗi mạng/NCBI chặn ⇒ ném ngoại lệ (người gọi KHÔNG ghi tệp dở). Số bản ghi trả về khác số hit ⇒ ghi cả hai, không
    tự bù."""
    from app.config import settings  # noqa: PLC0415
    from app.sources.pubmed import ESEARCH  # noqa: PLC0415
    from app.utils.http import HttpClient  # noqa: PLC0415

    esummary = ESEARCH.replace("esearch.fcgi", "esummary.fcgi")
    http = HttpClient(min_interval=0.4)
    chung: Dict[str, Any] = {"db": "pubmed", "retmode": "json"}
    if settings.ncbi_email:
        chung["email"] = settings.ncbi_email
    if settings.ncbi_api_key:
        chung["api_key"] = settings.ncbi_api_key
    d = http.get_json(ESEARCH, params={**chung, "term": f"({truy_van})", "retmax": tran, "sort": "date"},
                      use_cache=False)
    res = d.get("esearchresult")
    if not isinstance(res, dict) or "count" not in res:
        raise RuntimeError(f"esearch không trả «count»: {str(res)[:160]}")
    ids = [str(x) for x in res.get("idlist") or []]
    ban_ghi: List[Dict[str, Any]] = []
    for i in range(0, len(ids), 200):
        lo = ids[i:i + 200]
        s = http.get_json(esummary, params={**chung, "id": ",".join(lo)}, use_cache=False).get("result") or {}
        for pmid in lo:
            r = s.get(pmid)
            if not isinstance(r, dict):
                raise RuntimeError(f"esummary thiếu PMID {pmid}")
            ban_ghi.append({"pmid": pmid, "title": str(r.get("title") or "").strip(),
                            "year": str(r.get("pubdate") or "")[:4], "journal": str(r.get("fulljournalname") or ""),
                            "pubtypes": [str(x) for x in r.get("pubtype") or []]})
    return {"schema": SCHEMA_DAY_DU, "truy_van": truy_van, "so_hit_that": int(res["count"]),
            "so_bai_lay_ve": len(ban_ghi), "ngay_tai": date.today().isoformat(),
            "cach": "PubMed E-utilities esearch (sort=date) + esummary, không lọc thiết kế", "ban_ghi": ban_ghi}


def tep_day_du(nen_dir: Path, truy_van: str) -> Path:
    return Path(nen_dir) / THU_MUC_DAY_DU / f"{khoa_truy_van(truy_van)}.json"


def doc_day_du(nen_dir: Optional[Path], truy_van: str) -> Optional[Dict[str, Any]]:
    """Nhánh đầy đủ đã lưu cho truy vấn (None nếu vắng / hỏng / khác truy vấn)."""
    if not nen_dir or not truy_van:
        return None
    d = _doc_json(tep_day_du(Path(nen_dir), truy_van))
    if d.get("schema") != SCHEMA_DAY_DU or " ".join(str(d.get("truy_van")).split()) != " ".join(truy_van.split()):
        return None
    return d if isinstance(d.get("ban_ghi"), list) else None


def cac_truy_van_nen(nen_dir: Path) -> Dict[str, Tuple[str, Optional[int]]]:
    """khoá → (truy vấn nhánh không lọc, số hit) của mọi kịch bản trong thư mục nền G0."""
    ra: Dict[str, Tuple[str, Optional[int]]] = {}
    for raw_p in sorted(Path(nen_dir).glob("*/G0_pubmed_raw.json")):
        kl = nhanh_khong_loc(_doc_json(raw_p))
        q = str(kl.get("truy_van") or "").strip()
        if q:
            ra[khoa_truy_van(q)] = (q, kl.get("so_hit_that") if isinstance(kl.get("so_hit_that"), int) else None)
    return ra


# ════════════════════════════════════════════════════════════════════════════════════════ sàng lọc theo tiêu đề
def _tach_and(q: str) -> List[str]:
    """Tách truy vấn thành các khối AND ở MỨC NGOÀI CÙNG (bỏ ngoặc bao)."""
    q = q.strip()
    while q.startswith("(") and q.endswith(")"):
        sau, muc = q[1:-1], 0
        for ch in sau:
            muc += {"(": 1, ")": -1}.get(ch, 0)
            if muc < 0:
                break
        if muc != 0:
            break
        q = sau.strip()
    khoi, muc, dau = [], 0, 0
    for m in re.finditer(r"[()]|\bAND\b", q):
        tk = m.group(0)
        if tk == "(":
            muc += 1
        elif tk == ")":
            muc -= 1
        elif muc == 0:
            khoi.append(q[dau:m.start()].strip())
            dau = m.end()
    khoi.append(q[dau:].strip())
    return [k for k in khoi if k]


def _thuat_ngu(khoi: str) -> List[str]:
    """Thuật ngữ của một khối OR: chuỗi trong nháy kép hoặc từ trần trước thẻ trường; bỏ «*», chữ thường."""
    ra = []
    for m in re.finditer(r'"([^"]+)"(?:\[[^\]]*\])?|([A-Za-z0-9][\w\-]*\*?)(?:\[[^\]]*\])?', khoi):
        t = (m.group(1) or m.group(2) or "").strip().rstrip("*").lower()
        if t and t not in {"or", "and", "not"}:
            ra.append(t)
    return list(dict.fromkeys(ra))


def khoi_khai_niem(truy_van: str) -> List[List[str]]:
    """Các khối KHÁI NIỆM (bỏ khối mà phần lớn thuật ngữ là thiết kế hoặc bối cảnh) — mỗi khối một danh sách."""
    ra = []
    for k in _tach_and(truy_van):
        tn = _thuat_ngu(k)
        if tn and sum(t in TU_THIET_KE or t in TU_BOI_CANH for t in tn) * 2 < len(tn):
            ra.append(tn)
    return ra


def _cham(tieu_de: str, tn: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(tn), tieu_de) is not None


def xep_lien_quan(tieu_de: str, khoi: Sequence[Sequence[str]]) -> Tuple[str, List[int]]:
    """(mức liên quan, chỉ số các khối KHÔNG chạm). Luật ở docstring mô-đun."""
    td = str(tieu_de or "").lower()
    thieu = [i for i, k in enumerate(khoi) if not any(_cham(td, t) for t in k)]
    if khoi and not thieu:
        return "truc_tiep", thieu
    if len(khoi) >= 2 and len(thieu) == 1:
        return "gian_tiep", thieu
    return "khong", thieu


def thiet_ke_that(ban_ghi: Mapping[str, Any], nhom: Iterable[str] = ()) -> str:
    """Thiết kế: loại xuất bản PubMed → nhóm bộ lọc của nền G0 → suy từ tiêu đề (ghi rõ nguồn suy)."""
    pt = set(ban_ghi.get("pubtypes") or [])
    for loai, nhan in LOAI_XUAT_BAN:
        if loai in pt:
            return f"{nhan} (loại xuất bản PubMed)"
    nh = set(nhom)
    for k, nhan in NHOM_NEN:
        if k in nh:
            return nhan
    td = str(ban_ghi.get("title") or "").lower()
    for mau, nhan in TU_TIEU_DE_THIET_KE:
        if re.search(mau, td):
            return nhan
    return "Bài báo — PubMed chưa gán loại thiết kế, tiêu đề không nêu thiết kế"


def _nhan_khoi(khoi: Sequence[str]) -> str:
    return f"«{khoi[0]}»" if khoi else "«?»"


def _tom_tat(bai: Mapping[str, Any], muc: str, khoi: Sequence[Sequence[str]], thieu: Sequence[int]) -> str:
    """Tóm tắt theo tiêu đề; `gian_tiep_da_dan` = bài hồ sơ đề tài đã dẫn mà tiêu đề không chạm đủ khối."""
    cham = [_nhan_khoi(k) for i, k in enumerate(khoi) if i not in thieu]
    nguon = ", ".join(x for x in (str(bai.get("journal") or "").strip(), str(bai.get("year") or "").strip()) if x)
    cau = f"Tiêu đề: «{str(bai.get('title') or '').strip()}»" + (f" ({nguon})" if nguon else "") + ". "
    if muc == "truc_tiep":
        return cau + f"Tiêu đề nêu đủ các khái niệm của câu hỏi ({', '.join(cham)})."
    if muc == "gian_tiep":
        return cau + (f"Tiêu đề nêu {', '.join(cham)} nhưng không nêu {_nhan_khoi(khoi[thieu[0]])} — gần câu hỏi, "
                      "khác quần thể hoặc kết cục.")
    if muc == "gian_tiep_da_dan":
        return cau + ("Hồ sơ đề tài dẫn bài này làm bằng chứng nền; tiêu đề dùng thuật ngữ rộng hơn truy vấn nên "
                      "xếp gián tiếp, chờ đọc tóm tắt để xếp lại.")
    return cau + "Tiêu đề không cùng khái niệm chính của câu hỏi."


def _ly_do_khong(khoi: Sequence[Sequence[str]], thieu: Sequence[int]) -> str:
    return "Tiêu đề không nêu " + ", ".join(_nhan_khoi(khoi[i]) for i in thieu) + " — khác khái niệm chính."


# ════════════════════════════════════════════════════════════════════════════════════════ G0-T3
def _rut_bai(pmid_xet: Sequence[str], kho_a12: Optional[Path], hom_nay: date) -> Dict[str, str]:
    """Kiểm rút bài từ kho A12 của bộ giả lập (`GIA_LAP_A12_KHO`, kết quả `check_citations` theo từng PMID). PMID
    không có trong kho ⇒ ghi «chưa kiểm» — TUYỆT ĐỐI không ghi «chưa bị rút»."""
    r = (_doc_json(kho_a12).get("retraction") or {}) if kho_a12 else {}
    try:
        import check_citation_retraction as CCR  # noqa: PLC0415

        la_van_de = CCR.la_van_de
    except Exception:  # noqa: BLE001 — không nạp được bộ luật ⇒ mọi PMID tính là chưa kiểm
        la_van_de, r = None, {}
    da = [p for p in pmid_xet if isinstance(r.get(p), dict) and not str(r[p].get("status")).startswith("unknown")]
    rut = [p for p in da if la_van_de and la_van_de(r[p])]
    chua = [p for p in pmid_xet if p not in da]
    phan = [f"{len(da)}/{len(pmid_xet)} PMID liên quan đã có kết quả kiểm rút bài"]
    phan.append(f"phát hiện rút bài hoặc thông báo biên tập: PMID {', '.join(rut)}" if rut
                else "không phát hiện rút bài hoặc thông báo biên tập trong số đã kiểm")
    if chua:
        phan.append(f"{len(chua)} PMID còn lại chưa kiểm rút bài")
    # 19/11/2026: bộ đối chiếu xuyên cổng chỉ tin danh sách `pmid_da_kiem` (không đọc câu văn) — chỉ PMID có kết quả.
    return {"ngay": hom_nay.isoformat(),
            "cong_cu": "tools/check_citations.py (kho kết quả theo PMID của bộ giả lập — GIA_LAP_A12_KHO)",
            "ket_qua": "; ".join(phan), "pmid_da_kiem": list(dict.fromkeys(da))}


def pmid_trong(*nguon: Any) -> set:
    """PMID nhắc dạng «PMID 12345678» trong nội dung (dict/list/chuỗi) — bằng chứng hồ sơ đề tài đã dẫn."""
    return set(re.findall(r"PMID[:\s]*(\d{6,9})", json.dumps(nguon, ensure_ascii=False), re.I))


def soan_tong_hop(out_dir: Path, study: str, nen_dir: Optional[Path], hom_nay: date,
                  kho_a12: Optional[Path] = None, pmid_da_dan: Iterable[str] = ()) -> Dict[str, Any]:
    """G0-T3: sàng lọc MỌI PMID nền (G0_checkpoint) + MỌI bản ghi nhánh không lọc (nhánh đầy đủ đã lưu nếu vượt trần).

    Bài nhánh không lọc ngoài nền: liên quan ⇒ `nguon_bo_sung` (kèm cách tìm), lạc đề ⇒ `sang_loc_khong_loc`."""
    out_dir = Path(out_dir)
    cp = _doc_json(out_dir / "G0_checkpoint.json")
    raw = _doc_json(out_dir / "G0_pubmed_raw.json")
    pr = cp.get("pubmed_results") if isinstance(cp.get("pubmed_results"), dict) else {}
    nen = [str(p) for p in (pr.get("all_pmids") or cp.get("pmids_verified") or [])]
    kl = nhanh_khong_loc(raw)
    q = str(kl.get("truy_van") or cp.get("base_query") or "")
    khoi = khoi_khai_niem(q)
    # Bản ghi theo PMID: nhóm nền (sr_ma/rct/…/khong_loc) + nhánh đầy đủ (có loại xuất bản).
    theo_pmid: Dict[str, Dict[str, Any]] = {}
    nhom: Dict[str, set] = {}
    for k in ("guideline", "sr_ma", "rct", "observational", "recent", "khong_loc"):
        for b in raw.get(k) or []:
            if isinstance(b, dict) and b.get("pmid"):
                p = str(b["pmid"])
                theo_pmid.setdefault(p, dict(b))
                nhom.setdefault(p, set()).add(k)
    day_du = doc_day_du(nen_dir, q) if kl else None
    for b in (day_du or {}).get("ban_ghi") or []:
        p = str(b.get("pmid") or "")
        if p:
            theo_pmid[p] = {**theo_pmid.get(p, {}), **{k: v for k, v in b.items() if v}}

    da_dan = {str(x) for x in pmid_da_dan}

    def sang(p: str) -> Tuple[Dict[str, Any], str, List[int]]:
        b = theo_pmid.get(p, {"pmid": p})
        muc, thieu = xep_lien_quan(str(b.get("title") or ""), khoi)
        if muc == "khong" and p in da_dan:
            muc = "gian_tiep_da_dan"
        return b, muc, thieu

    sang_loc = []
    for p in nen:
        b, muc, thieu = sang(p)
        dong = {"pmid": p, "thiet_ke_that": thiet_ke_that(b, nhom.get(p, ())),
                "lien_quan": "gian_tiep" if muc == "gian_tiep_da_dan" else muc,
                "tom_tat": _tom_tat(b, muc, khoi, thieu)}
        if muc == "khong":
            dong["ly_do"] = _ly_do_khong(khoi, thieu)
        sang_loc.append(dong)
    # Nhánh không lọc: bản ghi đã lấy về trong lượt G0 + phần vượt trần (nhánh đầy đủ).
    lay_ve = [str(x) for x in kl.get("pmid_lay_ve") or []] if isinstance(kl.get("pmid_lay_ve"), list) else []
    them_vt = [str(b.get("pmid")) for b in (day_du or {}).get("ban_ghi") or [] if b.get("pmid")]
    cach = (f"PubMed E-utilities (esearch + esummary), nhánh không lọc thiết kế của truy vấn G0: {q} — ngày "
            f"{(day_du or {}).get('ngay_tai') or hom_nay.isoformat()}")
    bo_sung, khong_loc = [], []
    tap_nen = set(nen)
    for p in dict.fromkeys(lay_ve + them_vt):
        if p in tap_nen:
            continue
        b, muc, thieu = sang(p)
        if muc == "khong":
            khong_loc.append({"pmid": p, "lien_quan": "khong", "ly_do": _ly_do_khong(khoi, thieu)})
        else:
            bo_sung.append({"pmid": p, "tieu_de": str(b.get("title") or "").strip() or f"PMID {p}",
                            "thiet_ke_that": thiet_ke_that(b, nhom.get(p, ())),
                            "lien_quan": "gian_tiep" if muc == "gian_tiep_da_dan" else muc,
                            "tom_tat": _tom_tat(b, muc, khoi, thieu), "cach_tim": cach})
    tat_ca = sang_loc + bo_sung
    truc = [d["pmid"] for d in tat_ca if d["lien_quan"] == "truc_tiep"]
    gian = [d["pmid"] for d in tat_ca if d["lien_quan"] == "gian_tiep"]
    so_khong = sum(1 for d in sang_loc if d["lien_quan"] == "khong") + len(khong_loc)
    dem_tk: Dict[str, int] = {}
    for d in tat_ca:
        if d["lien_quan"] == "truc_tiep":
            nhan = d["thiet_ke_that"].split(" (")[0]
            dem_tk[nhan] = dem_tk.get(nhan, 0) + 1
    thiet_ke_truc = "; ".join(f"{n} {k.lower()}" for k, n in sorted(dem_tk.items(), key=lambda x: -x[1])[:4])
    vd = "; ".join(f"PMID {p}" for p in truc[:3])
    tong_so = len(sang_loc) + len(bo_sung) + len(khong_loc)
    du = {
        "schema": GT.SCHEMA_TONG_HOP, "nguoi_soan": NGUOI_SOAN_G0T3, "ngay_soan": hom_nay.isoformat(),
        "cach_doc": ("Sàng lọc theo tiêu đề đối chiếu các khối khái niệm của truy vấn G0 (thiết kế không tính); "
                     "thiết kế lấy từ loại xuất bản PubMed hoặc bộ lọc của nhánh."),
        "sang_loc": sang_loc, "nguon_bo_sung": bo_sung, "sang_loc_khong_loc": khong_loc,
        "muc_bang_chung_sau_sang_loc": (
            f"Sau sàng lọc {tong_so} bản ghi (nền G0 và nhánh không lọc thiết kế): {len(truc)} bài liên quan trực "
            f"tiếp" + (f" ({thiet_ke_truc}; vd {vd})" if truc else "") + f", {len(gian)} bài gián tiếp."
            if truc else
            f"Sau sàng lọc {tong_so} bản ghi (nền G0 và nhánh không lọc thiết kế): chưa có bài nào liên quan trực "
            f"tiếp theo tiêu đề; {len(gian)} bài gián tiếp."),
        "tong_hop": (
            f"Đã sàng {len(sang_loc)} PMID nền G0 và {len(bo_sung) + len(khong_loc)} bản ghi của nhánh không lọc thiết "
            f"kế: {len(truc)} trực tiếp, {len(gian)} gián tiếp, {so_khong} không liên quan."
            + (f" Bài trực tiếp tiêu biểu: {vd}." if truc else "")),
        "rut_bai": _rut_bai(truc + gian, kho_a12, hom_nay),
    }
    so_hit, lv = kl.get("so_hit_that"), kl.get("so_bai_lay_ve")
    if isinstance(so_hit, int) and isinstance(lv, int) and so_hit > lv and day_du:
        du["khong_loc_vuot_tran"] = {"ngay": day_du.get("ngay_tai") or hom_nay.isoformat(),
                                     "pmid": [p for p in them_vt if p not in set(lay_ve)],
                                     "cach": f"{day_du.get('cach')}; {day_du.get('so_bai_lay_ve')}/"
                                             f"{day_du.get('so_hit_that')} bản ghi"}
    return du


# ════════════════════════════════════════════════════════════════════════════════════════ G0-T4
_LOAI_THEO_TU = (("bang_chung", ("không đồng nhất", "mâu thuẫn", "thiếu rct", "chưa đủ", "ít rct", "chất lượng thấp")),
                 ("boi_canh", ("việt nam", "trong nước", "ngoại trú", "bối cảnh")),
                 ("cong_cu_do", ("bộ câu hỏi", "công cụ", "thang đo")),
                 ("quan_the", ("người cao tuổi", "từ 60 tuổi", "quần thể")),
                 ("cap_nhat", ("cập nhật",)))


def _cau_dau(v: Any) -> str:
    t = re.sub(r"\s+", " ", str(v or "")).strip()
    m = re.match(r"(.{20,690}?[.;])(\s|$)", t)
    return (m.group(1) if m else t[:690]).strip()


def soan_khoang_trong(out_dir: Path, study: str, meta: Mapping[str, Any], hom_nay: date) -> Dict[str, Any]:
    """G0-T4: bảng guideline (nhánh guideline của nền G0; vắng ⇒ một dòng nói rõ đã rà nhánh nào), phát biểu khoảng
    trống từ biện minh tính mới PI đã khai, trạng thái nguồn từ checkpoint, nháp FINER (F/E để PI quyết)."""
    out_dir = Path(out_dir)
    cp = _doc_json(out_dir / "G0_checkpoint.json")
    raw = _doc_json(out_dir / "G0_pubmed_raw.json")
    g0 = ((meta.get("gate_params") or {}).get("G0") or {}) if isinstance(meta, Mapping) else {}
    gl = []
    for b in raw.get("guideline") or []:
        if isinstance(b, dict) and b.get("pmid"):
            gl.append({"ten": str(b.get("title") or "").strip() or f"PMID {b['pmid']}",
                       "nguon": f"PMID {b['pmid']}" + (f" — {b.get('journal')}, {b.get('year')}"
                                                       if b.get("journal") else ""),
                       "noi_dung": "PARTIAL — chưa đọc văn bản; mới có tiêu đề từ nhánh guideline của truy vấn G0, "
                                   "đối chiếu khuyến cáo khi soạn đề cương."})
    if not gl:
        tc = (raw.get("true_counts") or {}).get("guideline")
        gl.append({"ten": "Không có hướng dẫn thực hành trong nhánh guideline của truy vấn G0",
                   "nguon": f"PubMed, bộ lọc Practice Guideline/Guideline, ngày {hom_nay.isoformat()}",
                   "noi_dung": (f"{tc if isinstance(tc, int) else 0} bản ghi; văn bản quy phạm trong nước không lập "
                                "chỉ mục PubMed — chưa rà trong lượt này.")})
    nj = _cau_dau(g0.get("novelty_justification") or cp.get("novelty_concern") or "")
    if not nj or GT._TUYET_DOI.search(nj):
        nj = "Bằng chứng hiện có chưa trả lời câu hỏi này trong bối cảnh ngoại trú tại Việt Nam (trong phạm vi đã tra)."
    thap = nj.casefold()
    loai = [k for k, tu in _LOAI_THEO_TU if any(t in thap for t in tu)] or ["boi_canh"]
    rc = cp.get("registry_check") if isinstance(cp.get("registry_check"), dict) else {}
    ctgov = "day_du" if rc and not rc.get("error") and rc.get("status") != "error" else ("partial" if rc else
                                                                                      "chua_tra")
    ictrp_ngay = ((g0.get("registry_manual_checked") or {}) if isinstance(g0.get("registry_manual_checked"), dict)
                  else {}).get("ictrp")
    pr = cp.get("pubmed_results") if isinstance(cp.get("pubmed_results"), dict) else {}
    pubmed = "day_du" if pr.get("counts_are_real") and not pr.get("query_errors") else "partial"

    def _bo_dat(v: Any, mac_dinh: str) -> str:
        t = re.sub(r"^\s*Đạt\s*[—-]\s*", "", str(v or "")).strip()
        return t or mac_dinh

    return {
        "schema": GT.SCHEMA_KHOANG_TRONG, "nguoi_soan": NGUOI_SOAN_G0T4, "ngay_soan": hom_nay.isoformat(),
        "guideline_lien_quan": gl,
        "phat_bieu_khoang_trong": nj,
        "loai_khoang_trong": loai,
        "muc_novelty": {"muc": "mo_rong_boi_canh",
                        "y_nghia": "Kiểm chứng câu hỏi đã có bằng chứng ở nơi khác trong bối cảnh ngoại trú tại Việt "
                                   "Nam, trong phạm vi các nguồn đã tra."},
        "trang_thai_nguon": {"pubmed": pubmed, "clinicaltrials_gov": ctgov,
                             "who_ictrp": "day_du" if ictrp_ngay else "chua_tra"},
        "ghi_chu_trang_thai_nguon": ("PubMed theo truy vấn G0; ClinicalTrials.gov theo bước tra đăng ký tự động của "
                                     "G0; WHO ICTRP theo ngày PI tự tra" + (f" ({ictrp_ngay})" if ictrp_ngay else "")),
        "nhap_finer": {
            "finer_feasible": (f"{GT.TIEN_TO_PI} — khả năng tuyển đủ người tham gia trong thời gian dự kiến và nguồn "
                               "lực thu thập số liệu tại cơ sở; cỡ mẫu chốt ở G3."),
            "finer_interesting": _bo_dat(g0.get("finer_interesting"), "Câu hỏi thực hành thường gặp ở ngoại trú."),
            "finer_novel": _bo_dat(g0.get("finer_novel"), nj),
            "finer_ethical": (f"{GT.TIEN_TO_PI} — bảo mật thông tin người tham gia, đồng thuận và mức nguy cơ của "
                              "quy trình thu thập; Hội đồng Đạo đức xét ở G2."),
            "finer_relevant": _bo_dat(g0.get("finer_relevant"), "Kết quả dùng được cho thực hành ngoại trú."),
        },
    }


# ════════════════════════════════════════════════════════════════════════════════════════ G10-T3
TEN_CONG = {"G0": "câu hỏi nghiên cứu", "G1": "thiết kế", "G2": "đạo đức và đăng ký", "G3": "cỡ mẫu và bộ biến",
            "G4": "kế hoạch phân tích thống kê", "G5": "khoá dữ liệu", "G6": "phân tích", "G7": "bản thảo",
            "G8": "bình duyệt trước nộp", "G9": "liêm chính tác giả", "G10": "khoá gói phát hành"}
CONG_KE = {"G0": "G1", "G1": "G2", "G2": "G3", "G3": "G4", "G4": "G5", "G5": "G6", "G6": "G7", "G7": "G8",
           "G8": "G9", "G9": "G10", "G10": ""}


def khoi_so_trang_thai(study: str, cong: str, ngay: str, san_pham: str, buoc_ke: str = "") -> str:
    """Một khối checkpoint đúng schema `_SO-TRANG-THAI-CHECKPOINT.md` (nhãn mở đầu bằng mã đề tài)."""
    ke = buoc_ke or (f"{CONG_KE.get(cong)} ({TEN_CONG.get(CONG_KE.get(cong, ''), '')})" if CONG_KE.get(cong)
                     else "đóng đề tài — lưu trữ gói phát hành")
    return (f"## CHECKPOINT [{ngay}] — đề tài/ca: {study} — {cong} {TEN_CONG.get(cong, '')}\n"
            f"- cong_vua_qua:   {cong}\n- ngay:           {ngay}\n- loai_nhiem_vu:  nghiên cứu\n"
            f"- san_pham_vua_xong: {san_pham}\n- danh_muc_🔴_con_lai: (không)\n- buoc_ke:        {ke}\n"
            f"- agent_ghi:      {NGUOI_GHI_G10T3}\n")


def noi_so_trang_thai(out_dir: Path, study: str, cong: str, ngay: str, san_pham: str, buoc_ke: str = "") -> Path:
    """Nối MỘT khối vào cuối sổ trạng thái của đề tài (tạo tệp kèm đầu sổ nếu chưa có). Chỉ nối thêm."""
    p = Path(out_dir) / TEP_SO_TRANG_THAI.format(study=study)
    dau = "" if p.is_file() else (f"# Sổ trạng thái đề tài {study}\n\nMỗi cổng một khối, chỉ nối thêm ở cuối "
                                  "(khuôn `_SO-TRANG-THAI-CHECKPOINT.md`).\n\n")
    cu = p.read_text(encoding="utf-8") if p.is_file() else ""
    if cu and not cu.endswith("\n\n"):
        cu = cu.rstrip("\n") + "\n\n"
    p.write_text(dau + cu + khoi_so_trang_thai(study, cong, ngay, san_pham, buoc_ke), encoding="utf-8",
                 newline="\n")
    return p


# ════════════════════════════════════════════════════════════════════════════════════════ CLI
def _cli(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Nhánh không lọc đầy đủ cho nền G0 của bộ giả lập (G0-T3).")
    ap.add_argument("--nen", type=Path, default=None, help="thư mục nền G0 (mặc định GIA_LAP_NEN_G0_DIR / state)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tai", action="store_true", help="CÓ MẠNG: tải nhánh đầy đủ còn thiếu")
    g.add_argument("--kiem", action="store_true", help="ngoại tuyến: liệt kê truy vấn còn thiếu tệp")
    a = ap.parse_args(argv)
    if a.nen is None:
        import gia_lap_dinh_ky as GL  # noqa: PLC0415

        a.nen = GL.NEN_G0_DIR
    thieu = 0
    for khoa, (q, so_hit) in cac_truy_van_nen(a.nen).items():
        co = doc_day_du(a.nen, q)
        if co and (so_hit is None or co.get("so_bai_lay_ve", 0) >= min(so_hit, TRAN_TAI)):
            print(f"✅ {khoa}: {co.get('so_bai_lay_ve')}/{co.get('so_hit_that')} bản ghi")
            continue
        if a.kiem:
            thieu += 1
            print(f"⚪ {khoa}: chưa có nhánh đầy đủ ({so_hit} hit) — chạy --tai có mạng")
            continue
        d = tai_nhanh_day_du(q)
        _ghi_json(tep_day_du(a.nen, q), d)
        print(f"⬇ {khoa}: {d['so_bai_lay_ve']}/{d['so_hit_that']} bản ghi")
    return 2 if thieu else 0


if __name__ == "__main__":
    sys.exit(_cli())
