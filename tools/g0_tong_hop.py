#!/usr/bin/env python3
"""g0_tong_hop.py — phần ĐỌC BÀI của G0 do agent soạn, tách khỏi bộ sinh A1 (10/10/2026).

★ VÌ SAO TỒN TẠI: hai biên bản đánh giá chéo của hội đồng cổng G0 (C1a, 07/10/2026 — G0-DG-…-0b213597 cho G0-T3,
G0-DG-…-79f9a227 cho G0-T4) trả về sửa vì A1 chỉ là SỐ HIT + TIÊU ĐỀ: không sàng lọc mức liên quan (5/12 bài lạc đề
vẫn được gọi «nền quan sát»), không bảng guideline/văn bản quy phạm, khẳng định phủ định không ghi phạm vi, không có
nháp lý do FINER. Máy KHÔNG đọc bài được — đó là việc của agent nhiệm vụ. Nhưng nếu agent viết thẳng vào A1 thì lần
chạy lại G0 xoá sạch công đọc. Nên công đọc nằm ở HAI TỆP DỮ LIỆU riêng (mỗi agent một tệp, đúng chủ nhiệm vụ),
bộ sinh A1 chỉ TRÌNH BÀY:

  · `G0_TONG_HOP_BANG_CHUNG_<mã>.json` — G0-T3 `tong-quan-y-van`: sàng lọc TỪNG PMID của nền G0 (thiết kế thật · liên
    quan trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung (kèm cách tìm — PRISMA-S), đoạn tóm lược dẫn PMID, kiểm
    rút bài.
  · `G0_KHOANG_TRONG_<mã>.json` — G0-T4 `khoang-trong-nghien-cuu`: bảng guideline/văn bản quy phạm (kể cả văn bản
    trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái
    từng nguồn tra, nháp lý do FINER (F và E BẮT BUỘC để PI quyết — máy/agent không tự đánh giá khả thi/đạo đức).

Cả hai là ĐỀ XUẤT: nơi chốt vẫn là `study_meta.json → gate_params.G0` do PI ghi. Mô-đun thuần — không gọi mạng, không
ghi tệp; `kiem_*` trả danh sách lỗi CẤU TRÚC (rỗng = đạt), đúng/sai nội dung khoa học do đánh giá chéo bảo đảm.
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TEP_TONG_HOP = "G0_TONG_HOP_BANG_CHUNG_{study}.json"
TEP_KHOANG_TRONG = "G0_KHOANG_TRONG_{study}.json"
SCHEMA_TONG_HOP = "g0/tong_hop_bang_chung/v1"
SCHEMA_KHOANG_TRONG = "g0/khoang_trong/v1"

LIEN_QUAN = ("truc_tiep", "gian_tiep", "khong")
NHAN_LIEN_QUAN = {"truc_tiep": "trực tiếp", "gian_tiep": "gián tiếp", "khong": "không liên quan"}
LOAI_KHOANG_TRONG = ("bang_chung", "quan_the", "boi_canh", "phuong_phap", "cong_cu_do", "ket_cuc", "cap_nhat")
MUC_NOVELTY = ("moi_hoan_toan", "mo_rong_boi_canh", "nhan_rong_co_kiem_chung", "cap_nhat", "trung_lap")
TRANG_THAI_NGUON = ("day_du", "partial", "chua_tra", "khong_ap_dung")
NGUON_BAT_BUOC = ("pubmed", "clinicaltrials_gov", "who_ictrp")
FINER_KHOA = ("finer_feasible", "finer_interesting", "finer_novel", "finer_ethical", "finer_relevant")
# F và E: agent KHÔNG tự đánh giá (g0_quality_gate G0-HUMAN-05) — nháp chỉ được nêu rủi ro để PI quyết.
FINER_CHI_PI = ("finer_feasible", "finer_ethical")
TIEN_TO_PI = "CẦN PI QUYẾT"

_PMID = re.compile(r"^\d{6,9}$")
_DOI = re.compile(r"^10\.\d{4,9}/\S+$")
_PMID_TRONG_VAN = re.compile(r"PMID[:\s]*(\d{6,9})", re.I)
# Khẳng định tuyệt đối mà không chiến lược tìm nào chứng minh được (đề cương C1a §3.5 tự hạ mức đúng vì lý do này).
# Đúng mẫu «hình dạng ngày» của guardrail R2 trong run_g0_auto (nghi ngày sinh ⇒ A1 bị CHẶN): tệp agent viết ngày ISO.
_NGAY_DD_MM = re.compile(r"\b\d{2}[/-]\d{2}[/-](19|20)\d{2}\b")
_TUYET_DOI = re.compile(r"chưa từng|lần đầu tiên|chưa có (?:bất kỳ |một )?nghiên cứu nào|chưa ai nghiên cứu|"
                        r"\bfirst (?:ever|study)\b|\bno (?:previous|prior) stud", re.I)


def _chuoi(v: Any) -> str:
    return v.strip() if isinstance(v, str) else ""


def _ngay_hop_le(v: Any) -> bool:
    try:
        d = date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return False
    return d <= date.today()


def doc(out_dir: Path, mau: str, study: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(dữ liệu, lỗi đọc). Tệp vắng ⇒ (None, None) — vắng không phải lỗi CẤU TRÚC (bảng trách nhiệm báo «thiếu đầu
    ra» riêng); tệp có mà hỏng ⇒ (None, «lỗi»)."""
    p = Path(out_dir) / mau.format(study=study)
    if not p.is_file():
        return None, None
    try:
        du_lieu = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{p.name}: không đọc được ({type(exc).__name__})"
    if not isinstance(du_lieu, dict):
        return None, f"{p.name}: gốc phải là object JSON"
    return du_lieu, None


def _quet_pii(nhan: str, du_lieu: Any, loi: List[str]) -> None:
    van = json.dumps(du_lieu, ensure_ascii=False)
    m = _NGAY_DD_MM.search(van)
    if m:
        loi.append(f"{nhan}: ngày «{m.group(0)}» dạng dd/mm/yyyy — viết ISO YYYY-MM-DD (guardrail R2 của G0 coi "
                   "dd/mm/yyyy là nghi ngày sinh và CHẶN A1)")
    try:
        import clinical_checkpoint as CC  # noqa: PLC0415 — bộ mẫu PII dùng chung của hệ
    except ImportError:  # pragma: no cover - lưới an toàn khi chạy rời
        return
    for ten, mau in CC._PII_PATTERNS:
        if mau.search(van):
            loi.append(f"{nhan}: có mẫu định danh ({ten}) — tệp tổng hợp KHÔNG được chứa PII")


def _kiem_dau(du_lieu: Dict[str, Any], schema: str, nhan: str, loi: List[str]) -> None:
    if du_lieu.get("schema") != schema:
        loi.append(f"{nhan}: «schema» phải là «{schema}»")
    if not _chuoi(du_lieu.get("nguoi_soan")):
        loi.append(f"{nhan}: thiếu «nguoi_soan» (agent soạn)")
    if not _ngay_hop_le(du_lieu.get("ngay_soan")):
        loi.append(f"{nhan}: «ngay_soan» phải là ngày ISO YYYY-MM-DD, không ở tương lai")


def kiem_tong_hop(du_lieu: Any, all_pmids: Iterable[Any]) -> List[str]:
    """G0-T3 — lỗi cấu trúc của `G0_TONG_HOP_BANG_CHUNG_<mã>.json` (rỗng = đạt)."""
    nhan = "tổng hợp G0-T3"
    if not isinstance(du_lieu, dict):
        return [f"{nhan}: không phải object JSON"]
    loi: List[str] = []
    _kiem_dau(du_lieu, SCHEMA_TONG_HOP, nhan, loi)
    nen = {str(p) for p in all_pmids or []}
    sang_loc = du_lieu.get("sang_loc")
    da_loc: Dict[str, str] = {}
    if not isinstance(sang_loc, list) or not sang_loc:
        loi.append(f"{nhan}: «sang_loc» phải là danh sách ≥ 1 bài")
        sang_loc = []
    for i, bai in enumerate(sang_loc, 1):
        if not isinstance(bai, dict):
            loi.append(f"{nhan}: sang_loc[{i}] không phải object")
            continue
        pmid = _chuoi(str(bai.get("pmid") or ""))
        if not _PMID.match(pmid):
            loi.append(f"{nhan}: sang_loc[{i}] PMID «{pmid}» sai dạng")
            continue
        if pmid in da_loc:
            loi.append(f"{nhan}: PMID {pmid} sàng lọc hai lần")
        if nen and pmid not in nen:
            loi.append(f"{nhan}: PMID {pmid} không thuộc nền G0 (G0_checkpoint) — bài tìm thêm đưa vào «nguon_bo_sung»")
        lq = bai.get("lien_quan")
        if lq not in LIEN_QUAN:
            loi.append(f"{nhan}: PMID {pmid} «lien_quan» phải ∈ {', '.join(LIEN_QUAN)}")
        for k in ("thiet_ke_that", "tom_tat"):
            if not _chuoi(bai.get(k)):
                loi.append(f"{nhan}: PMID {pmid} thiếu «{k}»")
        if lq == "khong" and not _chuoi(bai.get("ly_do")):
            loi.append(f"{nhan}: PMID {pmid} xếp «không liên quan» phải có «ly_do»")
        da_loc[pmid] = lq if isinstance(lq, str) else ""
    thieu = sorted(nen - set(da_loc))
    if thieu:
        loi.append(f"{nhan}: chưa sàng lọc {len(thieu)}/{len(nen)} PMID của nền G0 (vd {', '.join(thieu[:5])}) — "
                   "phải đọc ĐỦ, không chỉ bài đứng đầu")
    truc_tiep = {p for p, lq in da_loc.items() if lq == "truc_tiep"}
    bo_sung = du_lieu.get("nguon_bo_sung", [])
    if not isinstance(bo_sung, list):
        loi.append(f"{nhan}: «nguon_bo_sung» phải là danh sách (rỗng được)")
        bo_sung = []
    for i, bai in enumerate(bo_sung, 1):
        if not isinstance(bai, dict):
            loi.append(f"{nhan}: nguon_bo_sung[{i}] không phải object")
            continue
        pmid = _chuoi(str(bai.get("pmid") or ""))
        doi = _chuoi(bai.get("doi"))
        if not (_PMID.match(pmid) or _DOI.match(doi)):
            loi.append(f"{nhan}: nguon_bo_sung[{i}] cần PMID hoặc DOI hợp lệ")
        if pmid and pmid in nen:
            loi.append(f"{nhan}: nguon_bo_sung[{i}] PMID {pmid} đã thuộc nền G0 — sàng lọc ở «sang_loc»")
        if bai.get("lien_quan") not in LIEN_QUAN:
            loi.append(f"{nhan}: nguon_bo_sung[{i}] «lien_quan» phải ∈ {', '.join(LIEN_QUAN)}")
        for k in ("tieu_de", "thiet_ke_that", "tom_tat", "cach_tim"):
            if not _chuoi(bai.get(k)):
                loi.append(f"{nhan}: nguon_bo_sung[{i}] thiếu «{k}»"
                           + (" (CSDL · truy vấn · ngày — PRISMA-S)" if k == "cach_tim" else ""))
        if bai.get("lien_quan") == "truc_tiep" and _PMID.match(pmid):
            truc_tiep.add(pmid)
    tong = _chuoi(du_lieu.get("tong_hop"))
    if not tong:
        loi.append(f"{nhan}: thiếu «tong_hop» (đoạn tóm lược bằng chứng)")
    elif not set(_PMID_TRONG_VAN.findall(tong)) & truc_tiep:
        loi.append(f"{nhan}: «tong_hop» phải dẫn ≥ 1 PMID của bài liên quan TRỰC TIẾP")
    rb = du_lieu.get("rut_bai")
    if not isinstance(rb, dict) or not _ngay_hop_le(rb.get("ngay")) or not _chuoi(rb.get("cong_cu")) \
            or not _chuoi(rb.get("ket_qua")):
        loi.append(f"{nhan}: «rut_bai» cần {{ngay ISO, cong_cu, ket_qua}} — không kiểm được thì ghi «chưa kiểm», "
                   "TUYỆT ĐỐI không ghi «chưa bị rút»")
    _quet_pii(nhan, du_lieu, loi)
    return loi


def kiem_khoang_trong(du_lieu: Any) -> List[str]:
    """G0-T4 — lỗi cấu trúc của `G0_KHOANG_TRONG_<mã>.json` (rỗng = đạt)."""
    nhan = "khoảng trống G0-T4"
    if not isinstance(du_lieu, dict):
        return [f"{nhan}: không phải object JSON"]
    loi: List[str] = []
    _kiem_dau(du_lieu, SCHEMA_KHOANG_TRONG, nhan, loi)
    gl = du_lieu.get("guideline_lien_quan")
    if not isinstance(gl, list) or not gl:
        loi.append(f"{nhan}: «guideline_lien_quan» cần ≥ 1 dòng (kể cả văn bản quy phạm trong nước không lập chỉ "
                   "mục PubMed); thật sự không có thì một dòng nói rõ đã rà nguồn nào")
        gl = []
    for i, d in enumerate(gl, 1):
        if not isinstance(d, dict):
            loi.append(f"{nhan}: guideline_lien_quan[{i}] không phải object")
            continue
        for k in ("ten", "nguon", "noi_dung"):
            if not _chuoi(d.get(k)):
                loi.append(f"{nhan}: guideline_lien_quan[{i}] thiếu «{k}»")
    pb = _chuoi(du_lieu.get("phat_bieu_khoang_trong"))
    if not pb:
        loi.append(f"{nhan}: thiếu «phat_bieu_khoang_trong» (1–2 câu)")
    elif len(pb) > 700:
        loi.append(f"{nhan}: «phat_bieu_khoang_trong» dài {len(pb)} ký tự — tối đa 700 (1–2 câu)")
    for tr in (pb, json.dumps(du_lieu.get("muc_novelty"), ensure_ascii=False)):
        m = _TUYET_DOI.search(tr or "")
        if m:
            loi.append(f"{nhan}: khẳng định tuyệt đối «{m.group(0)}» — không chiến lược tìm nào chứng minh được; "
                       "hạ về đúng phạm vi đã tra")
    loai = du_lieu.get("loai_khoang_trong")
    if not isinstance(loai, list) or not loai or any(x not in LOAI_KHOANG_TRONG for x in loai):
        loi.append(f"{nhan}: «loai_khoang_trong» là danh sách ≥ 1 ⊆ {', '.join(LOAI_KHOANG_TRONG)}")
    nv = du_lieu.get("muc_novelty")
    if not isinstance(nv, dict) or nv.get("muc") not in MUC_NOVELTY or not _chuoi(nv.get("y_nghia")):
        loi.append(f"{nhan}: «muc_novelty» cần {{muc ∈ {', '.join(MUC_NOVELTY)}, y_nghia}}")
    tt = du_lieu.get("trang_thai_nguon")
    if not isinstance(tt, dict):
        loi.append(f"{nhan}: thiếu «trang_thai_nguon»")
        tt = {}
    for k in NGUON_BAT_BUOC:
        if tt.get(k) not in TRANG_THAI_NGUON:
            loi.append(f"{nhan}: trang_thai_nguon.{k} phải ∈ {', '.join(TRANG_THAI_NGUON)}")
    finer = du_lieu.get("nhap_finer")
    if not isinstance(finer, dict):
        loi.append(f"{nhan}: thiếu «nhap_finer» (5 khoá finer_*)")
        finer = {}
    for k in FINER_KHOA:
        v = finer.get(k)
        if not _chuoi(v):
            loi.append(f"{nhan}: nhap_finer.{k} phải là câu có lý do (không phải cờ đúng/sai)")
        elif k in FINER_CHI_PI and not _chuoi(v).upper().startswith(TIEN_TO_PI):
            loi.append(f"{nhan}: nhap_finer.{k} phải mở đầu «{TIEN_TO_PI} —» rồi nêu rủi ro cụ thể — agent KHÔNG tự "
                       "đánh giá khả thi/đạo đức (G0-HUMAN-05)")
    _quet_pii(nhan, du_lieu, loi)
    return loi


# ════════════════════════════════════════════════════════════════════════════
# Trình bày trong A1 — tệp vắng ⇒ nhãn [CẦN …] chỉ đúng agent và đúng tệp
# ════════════════════════════════════════════════════════════════════════════

def _o(v: Any) -> str:
    """Ô bảng Markdown: một dòng, không «|»."""
    return re.sub(r"\s+", " ", str(v if v is not None else "")).replace("|", "/").strip() or "—"


def khoi_tong_hop(out_dir: Optional[Path], study: str, all_pmids: Iterable[Any]) -> str:
    ten = TEP_TONG_HOP.format(study=study)
    du_lieu, loi_doc = doc(out_dir, TEP_TONG_HOP, study) if out_dir else (None, None)
    if du_lieu is None:
        return (f"> [CẦN `tong-quan-y-van` LẬP `{ten}`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế "
                "thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút "
                "bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`." + (f"\n> ⚠ {loi_doc}" if loi_doc else "") + "\n")
    loi = kiem_tong_hop(du_lieu, all_pmids)
    thu_tu = {k: i for i, k in enumerate(LIEN_QUAN)}
    dong = ["| PMID | Thiết kế thật | Liên quan | Tóm tắt | Ghi chú |", "|---|---|---|---|---|"]
    for bai in sorted((b for b in du_lieu.get("sang_loc") or [] if isinstance(b, dict)),
                      key=lambda b: (thu_tu.get(b.get("lien_quan"), 9), str(b.get("pmid")))):
        dong.append(f"| {_o(bai.get('pmid'))} | {_o(bai.get('thiet_ke_that'))} | "
                    f"{_o(NHAN_LIEN_QUAN.get(bai.get('lien_quan'), bai.get('lien_quan')))} | "
                    f"{_o(bai.get('tom_tat'))} | "
                    f"{_o(bai.get('ly_do'))} |")
    ra = [f"Nguồn: `{ten}` — soạn bởi `{_o(du_lieu.get('nguoi_soan'))}` ngày {_o(du_lieu.get('ngay_soan'))} "
          f"({_o(du_lieu.get('cach_doc') or 'đọc tiêu đề + tóm tắt PubMed')}). **ĐỀ XUẤT — PI duyệt.**", "",
          *dong, ""]
    bo_sung = [b for b in du_lieu.get("nguon_bo_sung") or [] if isinstance(b, dict)]
    if bo_sung:
        ra += ["**Nguồn bổ sung ngoài truy vấn G0** (kèm cách tìm — PRISMA-S):", "",
               "| PMID/DOI | Tiêu đề | Thiết kế thật | Liên quan | Tóm tắt | Cách tìm |", "|---|---|---|---|---|---|"]
        for b in bo_sung:
            ra.append(f"| {_o(b.get('pmid') or b.get('doi'))} | {_o(b.get('tieu_de'))} | "
                      f"{_o(b.get('thiet_ke_that'))} | "
                      f"{_o(NHAN_LIEN_QUAN.get(b.get('lien_quan'), b.get('lien_quan')))} | {_o(b.get('tom_tat'))} | "
                      f"{_o(b.get('cach_tim'))} |")
        ra.append("")
    ra += [f"**Tóm lược:** {_o(du_lieu.get('tong_hop'))}", ""]
    rb = du_lieu.get("rut_bai") if isinstance(du_lieu.get("rut_bai"), dict) else {}
    ra.append(f"**Kiểm rút bài:** {_o(rb.get('ket_qua') or 'chưa kiểm')} "
              f"(ngày {_o(rb.get('ngay'))}; công cụ {_o(rb.get('cong_cu'))})")
    if loi:
        ra += ["", "> ⚠ Tệp tổng hợp còn lỗi cấu trúc — sửa rồi dựng lại A1:"] + [f"> - {x}" for x in loi]
    return "\n".join(ra) + "\n"


def khoi_khoang_trong(out_dir: Optional[Path], study: str) -> str:
    ten = TEP_KHOANG_TRONG.format(study=study)
    du_lieu, loi_doc = doc(out_dir, TEP_KHOANG_TRONG, study) if out_dir else (None, None)
    if du_lieu is None:
        return (f"> [CẦN `khoang-trong-nghien-cuu` LẬP `{ten}`] — bảng guideline/văn bản quy phạm (kể cả văn bản "
                "trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, "
                "trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`."
                + (f"\n> ⚠ {loi_doc}" if loi_doc else "") + "\n")
    loi = kiem_khoang_trong(du_lieu)
    ra = [f"Nguồn: `{ten}` — soạn bởi `{_o(du_lieu.get('nguoi_soan'))}` ngày {_o(du_lieu.get('ngay_soan'))}. "
          "**ĐỀ XUẤT — PI duyệt; nơi chốt là `gate_params.G0.novelty_justification`.**", "",
          "**Guideline / văn bản quy phạm liên quan:**", "",
          "| Văn bản / guideline | Năm | Nguồn | Nội dung liên quan | Mức/phân hạng theo nguồn |",
          "|---|---|---|---|---|"]
    for d in du_lieu.get("guideline_lien_quan") or []:
        if isinstance(d, dict):
            ra.append(f"| {_o(d.get('ten'))} | {_o(d.get('nam'))} | {_o(d.get('nguon'))} | {_o(d.get('noi_dung'))} | "
                      f"{_o(d.get('muc') or 'nguồn không phân hạng')} |")
    nv = du_lieu.get("muc_novelty") if isinstance(du_lieu.get("muc_novelty"), dict) else {}
    tt = du_lieu.get("trang_thai_nguon") if isinstance(du_lieu.get("trang_thai_nguon"), dict) else {}
    ra += ["", f"**Phát biểu khoảng trống:** {_o(du_lieu.get('phat_bieu_khoang_trong'))}", "",
           f"**Loại khoảng trống:** {', '.join(_o(x) for x in du_lieu.get('loai_khoang_trong') or []) or '—'}", "",
           f"**Mức tính mới:** {_o(nv.get('muc'))} — {_o(nv.get('y_nghia'))}", "",
           "**Trạng thái nguồn đã tra:** " + " · ".join(f"{k}={_o(v)}" for k, v in tt.items())]
    if _chuoi(du_lieu.get("ghi_chu_trang_thai_nguon")):
        ra += ["", f"**Ghi chú nguồn:** {_o(du_lieu.get('ghi_chu_trang_thai_nguon'))}"]
    if loi:
        ra += ["", "> ⚠ Tệp khoảng trống còn lỗi cấu trúc — sửa rồi dựng lại A1:"] + [f"> - {x}" for x in loi]
    return "\n".join(ra) + "\n"


def khoi_nhap_finer(out_dir: Optional[Path], study: str) -> str:
    du_lieu, _ = doc(out_dir, TEP_KHOANG_TRONG, study) if out_dir else (None, None)
    finer = (du_lieu or {}).get("nhap_finer") if isinstance((du_lieu or {}).get("nhap_finer"), dict) else None
    if not finer:
        return ("> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong "
                f"`{TEP_KHOANG_TRONG.format(study=study)}`"
                " → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.\n")
    ra = ["**Nháp lý do FINER (đề xuất của `khoang-trong-nghien-cuu` — PI đọc, sửa rồi TỰ ghi vào "
          "`gate_params.G0.finer_*`, mỗi khoá một câu «ĐẠT — <lý do>»):**", ""]
    for k in FINER_KHOA:
        ra.append(f"- `{k}`: {_o(finer.get(k))}")
    return "\n".join(ra) + "\n"
