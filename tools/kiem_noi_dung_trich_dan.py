#!/usr/bin/env python3
"""Kiểm NỘI DUNG trích dẫn (A12) bằng Claude API: mỗi câu khẳng định có [n] ↔ abstract PubMed của tài liệu [n].

VÌ SAO (17/11/2026, bác sĩ chọn «Kiểm nội dung trích dẫn A12» khi kết nối API Claude): `check_citations.py` đã kiểm
máy PMID có thật, chưa bị rút, đúng metadata — nhưng «câu này có đúng là điều bài [n] nói không» vẫn là việc đọc tay
(trích sai nội dung, gán số liệu của bài khác, dẫn hướng dẫn cho điều nó không khuyến cáo). Công cụ này làm phần đọc đó
ở mức ABSTRACT, có hai lớp máy kiểm lại câu trả lời của model:
  1. «trích» căn cứ phải có NGUYÊN VĂN trong tiêu đề/abstract của đúng tài liệu — không có ⇒ «căn cứ không khớp».
  2. Số liệu (%, số thập phân) trong đoạn khẳng định phải có trong abstract — không có ⇒ «số không thấy trong abstract».

Ranh giới: TƯ VẤN, chỉ cảnh báo — không ghi A12 receipt, không mở/chặn cổng, không sửa đề cương. «Không đủ thông tin»
nghĩa là abstract không nói tới (có thể ở toàn văn), KHÔNG phải trích sai. CHẠY KHÔ mặc định (không mạng, không ghi);
`--goi-api` mới lấy abstract + gọi API (tính phí) + ghi báo cáo vào exports/<mã>/kiem_may_api/.

Mã thoát: 0 không phát hiện gì cần xem · 1 có câu cần bác sĩ xem · 2 không kiểm được (thiếu khoá/NCBI/API) ·
3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import api_claude_nc as API  # noqa: E402

MUC = ("ho_tro", "ho_tro_mot_phan", "khong_ho_tro", "khong_du_thong_tin")
MUC_CAN_TRICH = ("ho_tro", "ho_tro_mot_phan", "khong_ho_tro")
TEN_MUC = {
    "ho_tro": "hỗ trợ",
    "ho_tro_mot_phan": "hỗ trợ một phần",
    "khong_ho_tro": "KHÔNG hỗ trợ",
    "khong_du_thong_tin": "abstract không đủ thông tin",
    "khong_kiem_duoc": "không kiểm được",
    "can_xem": "máy không xác minh được căn cứ",
}
_DAU = re.compile(r"\[(\d+(?:\s*[-–]\s*\d+)?(?:\s*[,;]\s*\d+(?:\s*[-–]\s*\d+)?)*)\]")
_TLTK = re.compile(r"^#{1,3}\s*(?:\d+\.?\s*)?(TÀI LIỆU THAM KHẢO|REFERENCES)\b", re.I)
_SO_LIEU = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.,]\d+)?)\s*%|(?<![\w.,])(\d+[,.]\d+)(?![\w.,])")
_SO_MUC_TRUOC = re.compile(r"(?:\b(?:[Mm]ục|[Pp]hụ lục|[Bb]ảng|[Hh]ình|[Ss]ơ đồ|[Cc]hương)|§)\s*$")
SO_CAU_MOI_LO = 6
SO_LAN_THU_JSON_HONG = 2  # lô trả JSON sai cú pháp ⇒ gửi lại đúng lô đó tối đa 1 lần (tính phí thêm 1 lượt)
TOKEN_MOI_ABSTRACT = 1000  # tiêu đề + loại xuất bản + abstract có cấu trúc, đo trên BTM
TOI_DA_MAC_DINH = 200
CONG_CU = "kiem_noi_dung_trich_dan"

# ── Batch API (bác sĩ chọn 21/11/2026: «merge, rồi làm luôn Batch API cho A12») ────────────────────────────────────
# VÌ SAO. Công cụ này là nguồn tốn token vào lớn nhất của hệ (đo Console 7 ngày tới 20/11/2026: Sonnet 5.5 13 Tr
# token vào, 12,7% đọc cache). Phần đầu vào KHÔNG cache được vì bản chất: mỗi lô mang abstract của riêng nó, mỗi
# abstract gửi đúng một lần — prompt caching không tiết kiệm cho nội dung gửi một lần (xem docs/BO-NHO-DEM-API.md §1).
# Batch API thì khác: giảm 50% MỌI khoản (vào, ra, ghi cache, đọc cache) và CỘNG DỒN với cache. Đây là đòn tiết kiệm
# lớn hơn cache cho đúng đường này.
#
# ĐÁNH ĐỔI, nói rõ: batch là BẤT ĐỒNG BỘ. Nộp xong không có kết quả ngay — phải quay lại lấy. Vì vậy đây là lựa chọn
# OPT-IN (`--batch`), đường gọi trực tiếp vẫn là mặc định để lượt khám/lượt gấp không bị chờ.
#
# SỔ TRẠNG THÁI. Giữ ĐÚNG abstract đã gửi, không tra lại lúc lấy kết quả: tra lại có thể ra abstract khác (bản ghi
# PubMed/Crossref cập nhật) ⇒ báo cáo sẽ nói về tài liệu KHÁC với tài liệu model đã đọc. Đó là lỗi liêm chính, không
# phải lỗi hiệu năng. Phần suy ra được từ chính tệp Markdown (đoạn khẳng định, danh mục TLTK) thì KHÔNG lưu — tính
# lại và canh bằng SHA-256 của tệp: tệp đổi giữa hai bước ⇒ TỪ CHỐI, không ghép kết quả cũ vào văn bản mới.
TEN_SO_BATCH = "A12_batch_{study}.json"
_CID_LO = "a12_lo_{i:04d}"


def _bam(van: str) -> str:
    return hashlib.sha256((van or "").encode("utf-8")).hexdigest()


def _lo_can_kiem(cau_ds: Sequence[Cau], tai_lieu: Dict[int, Dict[str, Any]], lo: int) -> List[List[Cau]]:
    """Danh sách lô — PHẢI dùng chung cho cả bước nộp và bước lấy để custom_id ứng đúng lô."""
    return API.chia_lo([c for c in cau_ds if any(n in tai_lieu for n in c.so)], lo)


def tham_so_lo(nhom: Sequence[Cau], tai_lieu: Dict[int, Dict[str, Any]], *, model: str) -> Dict[str, Any]:
    """Tham số MỘT lô — cùng lời nhắn, cùng system, cùng cache như đường gọi trực tiếp (chỉ khác đường vận chuyển)."""
    return API.tham_so(
        dung_loi_nhan(nhom, tai_lieu), he_thong=HE_THONG, model=model, effort="low", cache_he_thong=True
    )


def duong_so_batch(study: str, ra_dir: Path) -> Path:
    return ra_dir / TEN_SO_BATCH.format(study=study)


def doc_so_batch(duong: Path) -> Optional[Dict[str, Any]]:
    """Sổ batch đang chờ, hoặc None. Sổ hỏng ⇒ LoiCucBo (không đoán là «chưa nộp» rồi nộp lần hai, tính phí đôi)."""
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


def nop_batch_a12(
    cau_ds: Sequence[Cau],
    tai_lieu: Dict[int, Dict[str, Any]],
    ly_do_tl: Dict[int, str],
    *,
    model: str,
    lo: int,
    tep: Path,
    van: str,
    toi_da: int,
    client: Any = None,
    duong: Path,
) -> Dict[str, Any]:
    """Nộp TOÀN BỘ lô thành một batch, ghi sổ trạng thái, trả sổ. Không có kết quả ở bước này."""
    nhoms = _lo_can_kiem(cau_ds, tai_lieu, lo)
    if not nhoms:
        raise API.LoiCucBo("Không lô nào cần kiểm — không nộp batch rỗng.")
    yc = [(_CID_LO.format(i=i), tham_so_lo(nhom, tai_lieu, model=model)) for i, nhom in enumerate(nhoms)]
    bid = API.nop_batch(yc, client, nguon=CONG_CU)
    st = {
        "cong_cu": CONG_CU,
        "tep": str(tep),
        "tep_sha256": _bam(van),
        "he_thong_sha256": _bam(HE_THONG),
        "model": model,
        "lo": int(lo),
        "toi_da": int(toi_da),
        "batch": {"id": bid, "nop_luc": dt.datetime.now().isoformat(timespec="seconds"), "so_lo": len(yc)},
        # Khoá JSON là chuỗi — đọc lại phải đổi về int (xem `_tai_lieu_tu_so`).
        "tai_lieu": {str(k): v for k, v in tai_lieu.items()},
        "ly_do_tl": {str(k): v for k, v in (ly_do_tl or {}).items()},
    }
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return st


def _tai_lieu_tu_so(st: Dict[str, Any]) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, str]]:
    tl = {int(k): v for k, v in (st.get("tai_lieu") or {}).items()}
    ly = {int(k): v for k, v in (st.get("ly_do_tl") or {}).items()}
    return tl, ly


def lay_batch_a12(
    st: Dict[str, Any], cau_ds: Sequence[Cau], van: str, *, client: Any = None
) -> Tuple[Optional[List[KetQua]], Dict[str, Any]]:
    """Lấy kết quả batch đã nộp. Chưa xong ⇒ (None, trạng_thái). Xong ⇒ (kết quả, thống kê) đúng khuôn `chay`.

    Canh trước khi ghép: tệp Markdown và system prompt phải y nguyên lúc nộp — khác ⇒ LoiCucBo. Ghép kết quả của
    văn bản cũ vào văn bản mới sẽ cho báo cáo nói về những dòng không còn tồn tại."""
    if _bam(van) != st.get("tep_sha256"):
        raise API.LoiCucBo(
            "Tệp đã ĐỔI sau khi nộp batch — không ghép kết quả cũ vào văn bản mới. Nộp lại batch cho bản mới "
            "(kết quả batch cũ vẫn xem được trên Claude Console nếu cần)."
        )
    if _bam(HE_THONG) != st.get("he_thong_sha256"):
        raise API.LoiCucBo("Lời dặn (HE_THONG) đã đổi sau khi nộp batch — kết quả không so sánh được. Nộp lại batch.")
    tt = API.trang_thai_batch(st["batch"]["id"], client)
    if tt["trang_thai"] != "ended":
        return None, tt
    tai_lieu, _ = _tai_lieu_tu_so(st)
    ket_batch = API.doc_ket_qua_batch(st["batch"]["id"], client, nguon=CONG_CU)
    nhoms = _lo_can_kiem(cau_ds, tai_lieu, int(st["lo"]))
    ra: List[KetQua] = []
    tk: Dict[str, Any] = {
        "so_lo": 0, "lo_loi": 0, "lo_loi_api": 0, "token_vao": 0, "token_ra": 0,
        "token_cache_ghi": 0, "token_cache_doc": 0, "loi": [], "batch": True,
        "batch_id": st["batch"]["id"], "lo_thieu": 0,
    }
    for i, nhom in enumerate(nhoms):
        tk["so_lo"] += 1
        kq = ket_batch.get(_CID_LO.format(i=i))
        if kq is None:
            # Batch trả thiếu lô — KHÔNG đoán là «đúng hết»; mọi cặp của lô thành «không kiểm được».
            tk["lo_loi"] += 1
            tk["lo_thieu"] += 1
            tk["loi"].append(f"lô {i}: batch không trả kết quả cho {_CID_LO.format(i=i)}")
            ra.extend(
                KetQua(c.id, n, "khong_kiem_duoc", "batch không trả kết quả cho lô này")
                for c in nhom for n in c.so if n in tai_lieu
            )
            continue
        for k in ("vao", "ra", "cache_ghi", "cache_doc"):
            tk["token_" + k] += int(kq.get(k, 0) or 0)
        try:
            tra_loi = API.doc_json(API.van_ban_ket_qua_batch(kq))
        except API.KetQuaHong as exc:
            # Batch không gửi lại được trong cùng lượt (khác đường gọi trực tiếp, vốn thử lại 1 lần). Ghi rõ lý do
            # và để bác sĩ nộp lại riêng lô đó nếu muốn — KHÔNG im lặng coi như đã kiểm.
            tk["lo_loi"] += 1
            tk["loi"].append(f"lô {i}: {str(exc)[:160]}")
            ra.extend(
                KetQua(c.id, n, "khong_kiem_duoc", f"lô batch hỏng: {str(exc)[:120]}")
                for c in nhom for n in c.so if n in tai_lieu
            )
            continue
        ra.extend(kiem_tra_tra_loi(nhom, tra_loi, tai_lieu))
    return ra, tk


@dataclass
class TaiLieu:
    so: int
    van: str
    pmid: Optional[str] = None
    doi: Optional[str] = None


@dataclass
class Cau:
    id: str
    vi_tri: str
    cau: str
    doan: str
    so: List[int]


@dataclass
class KetQua:
    id: str
    so: int
    muc: str
    ly_do: str = ""
    trich: str = ""
    co: List[str] = field(default_factory=list)


def _bo_dinh_dang(s: str) -> str:
    return re.sub(r"\*\*|__|`", "", s).strip()


def mo_rong_dau(chuoi: str) -> List[int]:
    """«5–7, 9» ⇒ [5, 6, 7, 9]. Khoảng ngược hoặc quá 30 số ⇒ chỉ lấy hai đầu (không bịa dải)."""
    ra: List[int] = []
    for phan in re.split(r"\s*[,;]\s*", chuoi.strip()):
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", phan)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            ra.extend(range(a, b + 1) if a <= b and b - a <= 30 else [a, b])
        elif phan.isdigit():
            ra.append(int(phan))
    return list(dict.fromkeys(ra))


def tach_tltk(van: str) -> Dict[int, TaiLieu]:
    """Mục «TÀI LIỆU THAM KHẢO»: dòng «n. …», lấy PMID/DOI ghi trong dòng."""
    ds: Dict[int, TaiLieu] = {}
    trong = False
    for dong in van.splitlines():
        if _TLTK.match(dong.strip()):
            trong = True
            continue
        if trong and re.match(r"^#{1,2}\s", dong):
            break
        m = re.match(r"^\s*(\d{1,3})\.\s+(.+)$", dong) if trong else None
        if m:
            n = int(m.group(1))
            pm = re.search(r"PMID:?\s*(\d{4,9})", m.group(2))
            do = re.search(r"doi:\s*(10\.\S+?)\.?(?:\s|$)", m.group(2), re.I)
            ds[n] = TaiLieu(
                so=n, van=m.group(2).strip(), pmid=pm.group(1) if pm else None, doi=do.group(1) if do else None
            )
    return ds


def _tach_cau(dong: str) -> List[str]:
    manh = re.split(r"(?<=[.!?])\s+", dong.strip())
    ra: List[str] = []
    for m in manh:
        if ra and m and (m[0].islower() or m[0].isdigit()):
            ra[-1] = f"{ra[-1]} {m}"  # «et al. 2020», «vs. 2» — không phải đầu câu mới
        elif m:
            ra.append(m)
    return ra


def tach_cau_khang_dinh(van: str) -> List[Cau]:
    """Mọi đoạn có dấu [n] ngoài mục TLTK. Mỗi nhóm dấu là MỘT đơn vị kiểm, với đoạn đứng ngay trước nó (để số liệu
    của [5] không bị so với abstract của [6] khi một câu trích hai bài)."""
    ra: List[Cau] = []
    vi_tri = ""
    trong_tltk = False
    for dong in van.splitlines():
        s = dong.strip()
        if re.match(r"^#{1,4}\s", s):
            trong_tltk = bool(_TLTK.match(s))
            vi_tri = _bo_dinh_dang(s.lstrip("#").strip())[:90]
            continue
        if trong_tltk or not _DAU.search(s):
            continue
        if s.startswith("|"):
            o = [c.strip() for c in s.strip("|").split("|") if c.strip() and not re.fullmatch(r"[-: ]+", c.strip())]
            cau_ds = [" | ".join(o)]
        else:
            cau_ds = _tach_cau(s)
        for cau in cau_ds:
            cau = _bo_dinh_dang(cau)
            dau = list(_DAU.finditer(cau))
            truoc = 0
            for m in dau:
                doan = cau[truoc : m.end()].lstrip(" ;,.:").strip()
                truoc = m.end()
                so = mo_rong_dau(m.group(1))
                if so:
                    ra.append(
                        Cau(id=f"C{len(ra) + 1:03d}", vi_tri=vi_tri, cau=cau, doan=doan if len(dau) > 1 else cau, so=so)
                    )
    return ra


def so_lieu(doan: str) -> List[str]:
    """Số cần đối chiếu trong một đoạn: % và số thập phân (bỏ dấu [n]); «24,9» chuẩn thành «24.9»."""
    sach = _DAU.sub(" ", doan)
    ra = []
    for m in _SO_LIEU.finditer(sach):
        if m.group(2) and _SO_MUC_TRUOC.search(sach[:m.start()]):
            # 18/11/2026: «mục 4.9», «Bảng 5.2» là số đề mục, không phải số liệu (trước đây bị gắn «số không thấy»).
            continue
        ra.append((m.group(1) or m.group(2)).replace(",", "."))
    return list(dict.fromkeys(ra))


def so_co_trong(so: str, van: str) -> bool:
    """Số `so` (đã chuẩn «24.9») có trong văn bản nguồn? Nguồn «24,9»/«24·9» chuẩn về «24.9».

    18/11/2026 (thí điểm A12 trên C1a): «1.298 người bệnh» — dấu chấm phân cách NGHÌN kiểu Việt — bị so như số thập
    phân 1.298 trong khi abstract ghi «1298»/«4,372» ⇒ cờ «số không thấy» giả. Số dạng «d.ddd» (1–3 chữ số, chấm, đúng
    3 chữ số) nhập nhằng nghìn/thập phân ⇒ nhận cả dạng liền «1298» và dạng cách «1 298»."""
    v = (van or "").replace("\u2008", " ").replace("\u202f", " ").replace("\u00a0", " ").replace("\u00b7", ".")
    v = re.sub(r"(?<=\d),(?=\d)", ".", v)
    cac = [so]
    if re.fullmatch(r"\d{1,3}\.\d{3}", so):
        cac += [so.replace(".", ""), so.replace(".", " ")]
    return any(re.search(rf"(?<![\d.]){re.escape(x)}(?![\d])", v) is not None for x in cac)


HE_THONG = (
    "Bạn là người kiểm trích dẫn (vai kiem-chung-trich-dan) cho đề cương nghiên cứu y khoa. Với MỖI câu khẳng định và "
    "MỖI tài liệu được giao cho nó, chỉ dựa trên TIÊU ĐỀ + LOẠI XUẤT BẢN + ABSTRACT được cung "
    "cấp (không dùng trí nhớ về "
    "bài báo), xếp một mức:\n"
    "- ho_tro: abstract nêu rõ điều đoạn khẳng định nói (kể cả con số, quần thể, chiều hiệu ứng);\n"
    "- ho_tro_mot_phan: abstract nói KHÁC, hoặc vắng, đúng một chi tiết mà đoạn khẳng định gắn RIÊNG cho tài liệu này "
    "(ghi rõ chi tiết nào trong ly_do);\n"
    "- khong_ho_tro: abstract nói khác/ngược, số liệu khác, hoặc bài thuộc quần thể/chủ đề/thiết kế khác hẳn;\n"
    "- khong_du_thong_tin: abstract không đủ để kết luận (có thể ở toàn văn) — KHÔNG phải lỗi.\n"
    # 18/11/2026 — bác sĩ gắn nhãn 17 phát hiện: 4/4 mục «ho_tro_mot_phan» là báo nhầm, cùng bốn kiểu dưới đây.
    "Phạm vi của MỘT tài liệu [n]: (1) chỉ xét phần đoạn khẳng định mà [n] được giao chống đỡ — phần câu gắn với số "
    "trích dẫn KHÁC trong cùng câu không thuộc [n]; (2) câu trích nhiều tài liệu cùng lúc (vd [38, 41]) được chống đỡ "
    "CHUNG — [n] chỉ cần ủng hộ ý chung, không phải tự nêu đủ mọi chi tiết; (3) tên tác giả, năm, tạp chí là siêu dữ "
    "liệu thư mục, không có trong abstract và được kiểm ở bước khác — KHÔNG dùng chúng để hạ mức; (4) câu chung kiểu "
    "«… được tham khảo khi xây dựng đề cương» chỉ đòi tài liệu ĐÚNG CHỦ ĐỀ — đúng chủ đề thì ho_tro.\n"
    "Luật: «trich» là cụm NGUYÊN VĂN ≤ 25 từ chép đúng từng chữ từ tiêu đề hoặc abstract của "
    "CHÍNH tài liệu đó, bắt buộc "
    "với ho_tro/ho_tro_mot_phan/khong_ho_tro, để trống với khong_du_thong_tin. ly_do ≤ 30 từ, tiếng Việt. Khẳng định "
    "về loại thiết kế hay khuyến cáo của hướng dẫn: so với loại xuất bản và nội dung abstract. "
    "Đoạn có số liệu: số phải "
    "khớp abstract. Trả DUY NHẤT một đối tượng JSON: "
    '{"ket_qua":[{"id":"C001","tham_chieu":[{"so":5,"muc":"ho_tro","trich":"…","ly_do":"…"}]}]} — đủ mọi id và mọi số '
    "tham chiếu được giao, không thêm id lạ."
)


def dinh_danh(t: Dict[str, Any]) -> str:
    """«PMID n» (abstract PubMed) hoặc «DOI d (abstract Europe PMC/Crossref)» — tài liệu chỉ có DOI (18/11/2026)."""
    if t.get("pmid") and not t.get("nguon"):
        return f"PMID {t['pmid']}"
    nguon = f" (abstract {t['nguon']})" if t.get("nguon") else ""
    return f"DOI {t.get('doi')}{nguon}" if t.get("doi") else f"PMID {t.get('pmid')}{nguon}"


def dung_loi_nhan(lo: Sequence[Cau], tai_lieu: Dict[int, Dict[str, Any]]) -> str:
    so_dung = sorted({n for c in lo for n in c.so if n in tai_lieu})
    khoi = []
    for n in so_dung:
        t = tai_lieu[n]
        khoi.append(
            f"[{n}] {dinh_danh(t)}\nTiêu đề: {t.get('title', '')}\n"
            f"Loại xuất bản: {', '.join(t.get('publication_types') or []) or 'không ghi'}\n"
            f"Abstract:\n{t.get('abstract', '')}"
        )
    cau = [
        {
            "id": c.id,
            "doan_khang_dinh": c.doan,
            "ca_cau": c.cau if c.cau != c.doan else None,
            "giao_tham_chieu": [n for n in c.so if n in tai_lieu],
        }
        for c in lo
    ]
    return (
        "TÀI LIỆU:\n\n"
        + "\n\n---\n\n".join(khoi)
        + "\n\nCÂU KHẲNG ĐỊNH CẦN KIỂM:\n"
        + json.dumps(cau, ensure_ascii=False, indent=1)
    )


def kiem_tra_tra_loi(lo: Sequence[Cau], dl: Any, tai_lieu: Dict[int, Dict[str, Any]]) -> List[KetQua]:
    """Máy kiểm lại câu trả lời: đủ id/số, mức hợp lệ, trích có nguyên văn, số liệu có trong abstract."""
    theo_id: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for m in (dl.get("ket_qua") if isinstance(dl, dict) else None) or []:
        if isinstance(m, dict):
            for t in m.get("tham_chieu") or []:
                if isinstance(t, dict) and str(t.get("so", "")).isdigit():
                    theo_id.setdefault(str(m.get("id")), {})[int(t["so"])] = t
    ra: List[KetQua] = []
    for c in lo:
        for n in c.so:
            if n not in tai_lieu:
                continue
            t = theo_id.get(c.id, {}).get(n)
            if t is None:
                ra.append(KetQua(c.id, n, "khong_kiem_duoc", "máy không trả kết quả cho cặp này"))
                continue
            muc = str(t.get("muc") or "")
            k = KetQua(
                c.id,
                n,
                muc if muc in MUC else "khong_kiem_duoc",
                str(t.get("ly_do") or "")[:300],
                str(t.get("trich") or "")[:400],
            )
            if muc not in MUC:
                k.ly_do = f"mức lạ «{muc}» — {k.ly_do}"
            nguon = f"{tai_lieu[n].get('title', '')}\n{tai_lieu[n].get('abstract', '')}"
            if k.muc in MUC_CAN_TRICH and not API.co_nguyen_van(k.trich, nguon):
                k.co.append("can_cu_khong_khop")
                k.muc = "can_xem"
            if k.muc in ("ho_tro", "ho_tro_mot_phan"):
                thieu = [s for s in so_lieu(c.doan) if not so_co_trong(s, nguon)]
                if thieu:
                    k.co.append("so_khong_thay:" + ",".join(thieu))
            ra.append(k)
    return ra


def ket_qua_may(cau_ds: Sequence[Cau], tltk: Dict[int, TaiLieu], tai_lieu: Dict[int, Dict[str, Any]]) -> List[KetQua]:
    """Cặp (câu, [n]) máy tự kết luận «không kiểm được» — không gửi API."""
    ra = []
    for c in cau_ds:
        for n in c.so:
            if n in tai_lieu:
                continue
            if n not in tltk:
                ly = "số trích dẫn không có trong danh mục tài liệu tham khảo"
            elif not tltk[n].pmid and not tltk[n].doi:
                ly = "tài liệu không có PMID lẫn DOI (máy chỉ đọc abstract tra theo định danh)"
            elif not tltk[n].pmid:
                ly = "không lấy được abstract theo DOI ở Europe PMC lẫn Crossref (xem lý do ở phần Tài liệu)"
            else:
                ly = "không lấy được abstract PubMed (xem lý do ở phần Tài liệu)"
            ra.append(KetQua(c.id, n, "khong_kiem_duoc", ly))
    return ra


def _bo_the(s: str) -> str:
    """Bỏ thẻ JATS/HTML (abstract Crossref dạng <jats:p>…) và khoảng trắng thừa."""
    import html  # noqa: PLC0415

    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def lay_abstract_theo_doi(dois: Sequence[str], http: Any = None) -> Dict[str, Dict[str, Any]]:
    """{doi viết thường: bản ghi} cho tài liệu CHỈ có DOI (18/11/2026 — trước đây mọi cặp loại này «không kiểm được»).

    Thứ tự: Europe PMC (`DOI:"…"`, gồm cả bài ngoài MEDLINE; DOI bản ghi phải TRÙNG đúng DOI tra) → Crossref
    (`/works/<doi>`, abstract nhà xuất bản nộp, dạng JATS). Không nguồn nào có abstract ⇒ status khác «resolved» kèm lý
    do — không đoán. Lỗi mạng của một DOI không làm hỏng DOI khác. `http` tiêm được cho kiểm thử (có `get_json`)."""
    from urllib.parse import quote  # noqa: PLC0415

    if http is None:
        from app.utils.http import HttpClient  # noqa: PLC0415

        # Đo 18/11/2026: VPN làm DNS www.ebi.ac.uk lúc được lúc không — 5 lần thử mặc định ⇒ ~45 giây/DOI. Một lần thử
        # lại là đủ; nguồn sau (Crossref) vẫn được hỏi.
        http = HttpClient(max_retries=1)
    from app.sources.europepmc import SEARCH, trang_thai_rut_bai_epmc  # noqa: PLC0415

    ra: Dict[str, Dict[str, Any]] = {}
    for doi in dois:
        khoa = doi.strip().lower()
        ban: Dict[str, Any] = {"status": "not_found", "reason": "không thấy ở Europe PMC lẫn Crossref", "doi": doi}
        loi: List[str] = []
        try:
            dl = http.get_json(SEARCH, params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core",
                                               "pageSize": 5}) or {}
            for r in (dl.get("resultList") or {}).get("result") or []:
                if str(r.get("doi") or "").strip().lower() != khoa:
                    continue
                loai = (r.get("pubTypeList") or {}).get("pubType") or []
                ban = {"status": "resolved", "doi": doi, "nguon": "Europe PMC", "pmid": r.get("pmid"),
                       "title": _bo_the(r.get("title") or ""), "abstract": _bo_the(r.get("abstractText") or ""),
                       "publication_types": [loai] if isinstance(loai, str) else list(loai),
                       "rut_bai": trang_thai_rut_bai_epmc(r)}
                break
        except Exception as exc:  # noqa: BLE001 — mạng/định dạng: ghi lý do, thử nguồn sau
            loi.append(f"Europe PMC lỗi {type(exc).__name__}")
        if not str(ban.get("abstract") or "").strip():
            co_ban_ghi = ban.get("status") == "resolved"
            try:
                dl_cr = http.get_json(f"https://api.crossref.org/works/{quote(doi, safe='/')}") or {}
                it = dl_cr.get("message") or {}
                tom = _bo_the(it.get("abstract") or "")
                khop = str(it.get("DOI") or "").strip().lower() == khoa
                if khop and tom:
                    ban = {"status": "resolved", "doi": doi, "nguon": "Crossref", "pmid": ban.get("pmid"),
                           "title": _bo_the((it.get("title") or [""])[0]) or ban.get("title", ""), "abstract": tom,
                           "publication_types": [it["type"]] if it.get("type") else [], "rut_bai": ban.get("rut_bai")}
                co_ban_ghi = co_ban_ghi or khop
            except Exception as exc:  # noqa: BLE001
                loi.append(f"Crossref lỗi {type(exc).__name__}")
            if co_ban_ghi and not str(ban.get("abstract") or "").strip():
                ban = {**ban, "status": "no_abstract",
                       "reason": "có bản ghi nhưng Europe PMC lẫn Crossref không có abstract"}
        if loi and ban.get("status") == "no_abstract":
            ban = {**ban, "reason": f"{ban['reason']}; {'; '.join(loi)}"}
        elif loi and ban.get("status") != "resolved":  # không đo được ≠ «không có»
            ban = {**ban, "status": "error", "reason": "; ".join(loi)}
        ra[khoa] = ban
    return ra


def lay_abstract(
    tltk: Dict[int, TaiLieu], lay=None, lay_doi=None
) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, str]]:
    """{n: bản ghi có abstract} + {n: lý do không dùng được}.

    `lay` (PubMed theo PMID) và `lay_doi` (tài liệu CHỈ có DOI, mặc định `lay_abstract_theo_doi`) tiêm được cho kiểm
    thử."""
    if lay is None:
        from app.sources.pubmed import PubMedClient

        lay = PubMedClient().fetch_abstracts
    pmids = sorted({t.pmid for t in tltk.values() if t.pmid})
    ban_ghi: Dict[str, Dict[str, Any]] = {}
    for i in range(0, len(pmids), 100):
        ban_ghi.update(lay(pmids[i : i + 100]) or {})
    dung: Dict[int, Dict[str, Any]] = {}
    ly_do: Dict[int, str] = {}
    for n, t in tltk.items():
        if not t.pmid:
            continue
        b = ban_ghi.get(t.pmid) or {}
        if b.get("status") != "resolved":
            ly_do[n] = f"PMID {t.pmid}: {b.get('status', 'không có')} — {b.get('reason', '')}".strip(" —")
        elif not (b.get("abstract") or "").strip():
            ly_do[n] = f"PMID {t.pmid}: bài không có abstract trên PubMed"
        else:
            dung[n] = {**b, "pmid": t.pmid}
            if b.get("rut_bai"):
                ly_do[n] = f"PMID {t.pmid}: PubMed gắn «{b['rut_bai']}» — xem A12"
    chi_doi = {n: t for n, t in tltk.items() if not t.pmid and t.doi}
    if chi_doi:
        ban_doi = (lay_doi or lay_abstract_theo_doi)(sorted({t.doi for t in chi_doi.values()}))
        for n, t in chi_doi.items():
            b = (ban_doi or {}).get(t.doi.strip().lower()) or {}
            if b.get("status") != "resolved" or not str(b.get("abstract") or "").strip():
                ly_do[n] = f"DOI {t.doi}: {b.get('status', 'không có')} — {b.get('reason', '')}".strip(" —")
                continue
            dung[n] = {**b, "doi": t.doi}
            if b.get("rut_bai"):
                ly_do[n] = f"DOI {t.doi}: {b.get('nguon')} gắn «{b['rut_bai']}» — xem A12"
    return dung, ly_do


def chay(
    cau_ds: List[Cau], tai_lieu: Dict[int, Dict[str, Any]], *, model: str, lo: int = SO_CAU_MOI_LO, client: Any = None
) -> Tuple[List[KetQua], Dict[str, Any]]:
    """Gọi API theo lô; lô hỏng ⇒ mọi cặp của lô «không kiểm được» kèm lý do (không đoán), lô khác vẫn chạy."""
    can = [c for c in cau_ds if any(n in tai_lieu for n in c.so)]
    ra: List[KetQua] = []
    tk = {
        "so_lo": 0, "lo_loi": 0, "lo_loi_api": 0, "token_vao": 0, "token_ra": 0,
        "token_cache_ghi": 0, "token_cache_doc": 0, "loi": [],
    }
    for nhom in API.chia_lo(can, lo):
        tk["so_lo"] += 1
        try:
            for lan in range(SO_LAN_THU_JSON_HONG):
                kq = API.goi(
                    dung_loi_nhan(nhom, tai_lieu), he_thong=HE_THONG, model=model, effort="low", client=client,
                    cache_he_thong=True,  # cùng lời dặn cho mọi lô ⇒ lô sau đọc từ cache
                    nguon="kiem_noi_dung_trich_dan",
                )
                tk["token_vao"] += kq.token_vao
                tk["token_ra"] += kq.token_ra
                tk["token_cache_ghi"] += kq.token_cache_ghi
                tk["token_cache_doc"] += kq.token_cache_doc
                try:
                    tra_loi = API.doc_json(kq.van_ban)
                    break
                except API.KetQuaHong:
                    # 18/11/2026 (BTM): một lô trả JSON hỏng ⇒ 12/51 cặp «không kiểm được». Câu trả lời ĐỦ (không cắt
                    # cụt/từ chối — `goi` đã ném trước) mà sai cú pháp là lỗi ngẫu nhiên ⇒ gửi lại ĐÚNG lô đó một lần.
                    if lan + 1 >= SO_LAN_THU_JSON_HONG:
                        raise
                    tk["lo_thu_lai"] = tk.get("lo_thu_lai", 0) + 1
            ra.extend(kiem_tra_tra_loi(nhom, tra_loi, tai_lieu))
        except (API.ThieuKhoa, API.HetNganSach):
            raise  # thiếu khoá / chạm trần chi phí ⇒ dừng CẢ lượt, không gửi lô sau
        except API.LoiApi as exc:
            tk["lo_loi"] += 1
            if not isinstance(exc, API.KetQuaHong):  # lỗi của KÊNH (khoá/mạng/hạn mức), không phải câu trả lời hỏng
                tk["lo_loi_api"] += 1
            tk["loi"].append(str(exc)[:200])
            ra.extend(
                KetQua(c.id, n, "khong_kiem_duoc", f"lô gọi API lỗi: {str(exc)[:120]}")
                for c in nhom
                for n in c.so
                if n in tai_lieu
            )
    return ra, tk


def can_xem(k: KetQua) -> bool:
    return k.muc in ("khong_ho_tro", "ho_tro_mot_phan", "can_xem") or any(x.startswith("so_khong_thay") for x in k.co)


def _o(s: str) -> str:
    return (s or "").replace("|", "/").replace("\n", " ").strip()


def bao_cao_md(
    study: str,
    tep: Path,
    cau_ds: List[Cau],
    tltk: Dict[int, TaiLieu],
    ket: List[KetQua],
    ly_do_tl: Dict[int, str],
    model: str,
    tk: Dict[str, Any],
    luc: str,
    tai_lieu: Optional[Dict[int, Dict[str, Any]]] = None,
) -> str:
    theo_id = {c.id: c for c in cau_ds}

    def _tl(n: int) -> str:
        if tai_lieu and n in tai_lieu:
            return dinh_danh(tai_lieu[n])
        t = tltk.get(n) or TaiLieu(0, "")
        return f"PMID {t.pmid}" if t.pmid else (f"DOI {t.doi}" if t.doi else "không định danh")

    dem: Dict[str, int] = {}
    for k in ket:
        dem[k.muc] = dem.get(k.muc, 0) + 1
    so_thay = sum(1 for k in ket if any(x.startswith("so_khong_thay") for x in k.co))
    dong = [
        f"# Kiểm nội dung trích dẫn bằng máy — {study}",
        "",
        f"- Tệp: `{tep.name}` · lúc {luc} · model `{model}` · {tk.get('so_lo', 0)} lượt gọi "
        # `batch=…` phải truyền đúng: giá Batch bằng 50% giá gọi trực tiếp, in sai đường thì con số tiền bị đọc sai.
        f"({tk.get('lo_loi', 0)} lỗi) · "
        + API.in_chi_phi(tk.get("token_vao", 0), tk.get("token_ra", 0), model, batch=bool(tk.get("batch")))
        + (f" · batch `{tk['batch_id']}`" if tk.get("batch_id") else ""),
        f"- {len(cau_ds)} đoạn khẳng định có trích dẫn · {len(tltk)} tài liệu tham khảo · "
        f"{len(ket)} cặp (đoạn, tài liệu)",
        "- Kết quả: "
        + " · ".join(f"{TEN_MUC.get(m, m)} {n}" for m, n in sorted(dem.items()))
        + f" · số liệu không thấy trong abstract {so_thay}",
        "",
        "So với TIÊU ĐỀ + ABSTRACT (PubMed theo PMID; tài liệu chỉ có mã DOI thì lấy qua Europe PMC hoặc Crossref, ghi "
        "ở cột Tài liệu), không phải toàn văn. «Abstract không đủ thông tin» không có nghĩa trích "
        "sai. Mọi căn cứ «trích» đã được máy đối chiếu nguyên văn với abstract; không khớp thì xếp «máy không xác "
        "minh được căn cứ».",
        "",
        "## Cần bác sĩ xem",
        "",
        "| Mã | Vị trí | Đoạn khẳng định | Tài liệu | Mức | Lý do / cờ | Căn cứ trong abstract |",
        "|---|---|---|---|---|---|---|",
    ]
    xem = [k for k in ket if can_xem(k)]
    for k in xem:
        c = theo_id[k.id]
        co = "; ".join(
            x.replace("so_khong_thay:", "số không thấy trong abstract: ").replace(
                "can_cu_khong_khop", "căn cứ máy trả không có nguyên văn"
            )
            for x in k.co
        )
        dong.append(
            f"| {k.id} | {_o(c.vi_tri)} | {_o(c.doan)[:300]} | [{k.so}] {_o(_tl(k.so))} "
            f"| {TEN_MUC.get(k.muc, k.muc)} | {_o(k.ly_do)}{(' — ' + co) if co else ''} | {_o(k.trich)} |"
        )
    if not xem:
        dong.append("| — | — | Không có đoạn nào cần xem theo máy | — | — | — | — |")
    kkd = [k for k in ket if k.muc == "khong_kiem_duoc"]
    dong += ["", "## Không kiểm được", ""]
    dong += [f"- {k.id} [{k.so}]: {k.ly_do}" for k in kkd] or ["- Không có."]
    dong += ["", "## Tài liệu không dùng được abstract", ""]
    dong += [f"- [{n}] {v}" for n, v in sorted(ly_do_tl.items())] or ["- Không có."]
    if tk.get("loi"):
        dong += ["", "## Lỗi lượt gọi", ""] + [f"- {x}" for x in tk["loi"]]
    dong += ["", "## Toàn bộ", "", "| Mã | Tài liệu | Mức | Lý do |", "|---|---|---|---|"]
    dong += [f"| {k.id} | [{k.so}] | {TEN_MUC.get(k.muc, k.muc)} | {_o(k.ly_do)} |" for k in ket]
    dong += ["", API.DISCLAIMER, ""]
    return "\n".join(dong)


def _tep_de_cuong(study: str, tep: Optional[str], goc: Path) -> Path:
    if tep:
        return Path(tep)
    return goc / "exports" / study / f"DE_CUONG_NOP_HOI_DONG_{study}.md"


def main(
    argv: Optional[Sequence[str]] = None, client: Any = None, lay=None, goc: Path = REPO, lay_doi=None
) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--tep", help="tệp Markdown cần kiểm (mặc định: đề cương nộp Hội đồng của đề tài)")
    ap.add_argument("--goi-api", action="store_true", help="lấy abstract + GỌI Claude API (tính phí) + ghi báo cáo")
    ap.add_argument("--model", default=None)
    ap.add_argument("--lo", type=int, default=SO_CAU_MOI_LO, help="số đoạn mỗi lượt gọi")
    ap.add_argument("--toi-da", type=int, default=TOI_DA_MAC_DINH, help="trần số đoạn kiểm mỗi lượt")
    ap.add_argument("--ra", help="thư mục ghi báo cáo (mặc định exports/<mã>/kiem_may_api/)")
    ap.add_argument(
        "--batch",
        action="store_true",
        help="dùng Batch API: giảm 50%% mọi khoản nhưng BẤT ĐỒNG BỘ (nộp xong phải quay lại lấy kết quả)",
    )
    ap.add_argument(
        "--chi-lay",
        action="store_true",
        help="chỉ LẤY kết quả batch đã nộp (đã trả phí), KHÔNG nộp batch mới",
    )
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    if a.chi_lay and not a.batch:
        print("❌ --chi-lay chỉ dùng cùng --batch (đường gọi trực tiếp không có gì để lấy lại).")
        return 3
    tep = _tep_de_cuong(a.study, a.tep, goc)
    if not tep.is_file():
        print(f"❌ Không thấy tệp {tep}")
        return 3
    try:
        model = API.chon_model(a.model)
    except API.LoiApi as exc:
        print(f"❌ {exc}")
        return 3
    van = tep.read_text(encoding="utf-8")
    tltk = tach_tltk(van)
    cau_ds = tach_cau_khang_dinh(van)
    bo = cau_ds[a.toi_da :] if a.toi_da > 0 else []
    cau_ds = cau_ds[: a.toi_da] if a.toi_da > 0 else cau_ds
    khong_pmid = sorted(n for n, t in tltk.items() if not t.pmid)
    chi_doi = sorted(n for n, t in tltk.items() if not t.pmid and t.doi)
    khong_dinh_danh = sorted(n for n, t in tltk.items() if not t.pmid and not t.doi)
    khong_co = sorted({n for c in cau_ds for n in c.so if n not in tltk})
    if not a.goi_api:
        so_cap = sum(len(c.so) for c in cau_ds)
        so_lo = len(API.chia_lo(cau_ds, a.lo))
        # 17/11/2026: lượt thật đầu tiên (BTM) tốn 39,5 nghìn token vào trong khi bản ước cũ (6 × 450/lô) báo 17 nghìn —
        # abstract dài hơn giả định và mỗi lô mang mọi tài liệu khác nhau của nó. Ước theo số tài liệu THẬT của từng lô.
        vao = sum(API.uoc_token(HE_THONG) + TOKEN_MOI_ABSTRACT * len({n for c in lo for n in c.so if n in tltk})
                  + API.uoc_token(" ".join(c.cau for c in lo)) for lo in API.chia_lo(cau_ds, a.lo))
        ra = so_cap * 90
        kh = {
            "study": a.study,
            "tep": str(tep),
            "so_doan": len(cau_ds),
            "so_cap": so_cap,
            "so_tltk": len(tltk),
            "tltk_khong_pmid": khong_pmid,
            "tltk_chi_doi": chi_doi,
            "tltk_khong_dinh_danh": khong_dinh_danh,
            "so_trich_khong_co_trong_tltk": khong_co,
            "so_luot_goi": so_lo,
            "bo_qua_vi_tran": len(bo),
            "duong": "batch" if a.batch else "goi_truc_tiep",
            "uoc_tinh": API.in_chi_phi(vao, ra, model, batch=a.batch),
            "uoc_usd": API.uoc_chi_phi(vao, ra, model, batch=a.batch),
        }
        if a.json:
            print(json.dumps(kh, ensure_ascii=False, indent=1))
        else:
            print(
                f"CHẠY KHÔ — {a.study}: {len(cau_ds)} đoạn khẳng định, {so_cap} cặp (đoạn, tài liệu), {len(tltk)} "
                f"tài liệu (chỉ có DOI — tra abstract Europe PMC/Crossref: {chi_doi or 'không'}; không PMID lẫn DOI: "
                f"{khong_dinh_danh or 'không'}; số trích không có trong danh mục: {khong_co or 'không'})."
            )
            if bo:
                print(
                    f"⚠ Trần --toi-da {a.toi_da}: BỎ {len(bo)} đoạn cuối (từ {bo[0].id}) — tăng --toi-da để kiểm hết."
                )
            print(f"Sẽ gọi {so_lo} lượt · ước {kh['uoc_tinh']}. Gọi thật: thêm --goi-api (tính phí).")
        return 0
    ra_dir = Path(a.ra) if a.ra else goc / "exports" / a.study / "kiem_may_api"
    so_batch = duong_so_batch(a.study, ra_dir)
    try:
        st_cho = doc_so_batch(so_batch) if a.batch else None
    except API.LoiCucBo as exc:
        print(f"⛔ {exc}")
        return 3

    if a.batch and st_cho:
        # ── LẤY kết quả batch đã nộp. Dùng abstract ĐÃ GỬI trong sổ, không tra lại (xem ghi chú ở TEN_SO_BATCH);
        # và dùng `lo`/`toi_da` ĐÃ NỘP, không dùng cờ dòng lệnh, để ranh giới lô trùng khít với lúc nộp.
        tai_lieu, ly_do_tl = _tai_lieu_tu_so(st_cho)
        td = int(st_cho.get("toi_da", a.toi_da))
        cau_ds = (lambda ds: ds[:td] if td > 0 else ds)(tach_cau_khang_dinh(van))
        try:
            ket, tk = lay_batch_a12(st_cho, cau_ds, van, client=client)
        except API.LoiCucBo as exc:
            print(f"⛔ {exc}")
            return 3
        except API.ThieuKhoa as exc:
            print(f"⚪ {exc}")
            return 2
        if ket is None:  # tk = trạng thái batch
            print(
                f"⏳ batch {tk['id']}: đang xử lý {tk['dang_xu_ly']} · xong {tk['xong']} · lỗi {tk['loi']} — "
                f"chạy lại `--batch --chi-lay` sau."
            )
            return 4
        so_batch.unlink(missing_ok=True)  # đã lấy xong ⇒ sổ hết nhiệm vụ (giữ lại sẽ bị đọc là «còn batch chờ»)
    elif a.batch and a.chi_lay:
        print("Không có batch nào đang chờ — `--chi-lay` không nộp gì.")
        return 0
    elif a.batch:
        # ── NỘP batch. Bước này KHÔNG có kết quả; mã 4 = chưa xong.
        try:
            tai_lieu, ly_do_tl = lay_abstract(tltk, lay, lay_doi)
        except Exception as exc:  # mạng/NCBI — không kết luận gì
            print(f"⚪ Không lấy được abstract (PubMed/Europe PMC/Crossref): {type(exc).__name__}: {exc}")
            return 2
        if not tai_lieu:
            print("⚪ Không tài liệu nào có abstract dùng được — KHÔNG kiểm được (không phải «đúng hết»).")
            return 2
        try:
            st = nop_batch_a12(
                cau_ds, tai_lieu, ly_do_tl, model=model, lo=a.lo, tep=tep, van=van,
                toi_da=a.toi_da, client=client, duong=so_batch,
            )
        except API.ThieuKhoa as exc:
            print(f"⚪ {exc}")
            API.ghi_nhat_ky_api("skipped", str(exc), 0, CONG_CU)
            return 2
        except (API.HetNganSach, API.LoiCucBo) as exc:
            print(f"⛔ {exc}")
            return 2
        print(
            f"📤 Đã nộp batch {st['batch']['id']} · {st['batch']['so_lo']} lô · giá Batch (giảm 50%). "
            f"Sổ: {so_batch}\nLấy kết quả: chạy lại cùng lệnh kèm `--batch --chi-lay`."
        )
        return 4
    else:
        try:
            tai_lieu, ly_do_tl = lay_abstract(tltk, lay, lay_doi)
        except Exception as exc:  # mạng/NCBI — không kết luận gì
            print(f"⚪ Không lấy được abstract (PubMed/Europe PMC/Crossref): {type(exc).__name__}: {exc}")
            return 2
        if not tai_lieu:
            print("⚪ Không tài liệu nào có abstract dùng được — KHÔNG kiểm được (không phải «đúng hết»).")
            return 2
        try:
            ket, tk = chay(cau_ds, tai_lieu, model=model, lo=a.lo, client=client)
        except API.ThieuKhoa as exc:
            print(f"⚪ {exc}")
            API.ghi_nhat_ky_api("skipped", str(exc), 0, CONG_CU)
            return 2
        except API.HetNganSach as exc:  # lỗi phía máy — khoá vẫn sống, không ghi nhật ký sức khoẻ; không báo cáo dở
            print(f"⛔ {exc}")
            return 2
    ket = ket_qua_may(cau_ds, tltk, tai_lieu) + ket
    ket.sort(key=lambda k: (k.id, k.so))
    luc = dt.datetime.now().isoformat(timespec="seconds")
    ra_dir.mkdir(parents=True, exist_ok=True)
    md = ra_dir / f"A12_KIEM_NOI_DUNG_{a.study}.md"
    md.write_text(bao_cao_md(a.study, tep, cau_ds, tltk, ket, ly_do_tl, model, tk, luc, tai_lieu),
                  encoding="utf-8", newline="\n")
    (ra_dir / f"A12_KIEM_NOI_DUNG_{a.study}.json").write_text(
        json.dumps(
            {
                "schema": "kiem_noi_dung_trich_dan/v1",
                "study": a.study,
                "tep": tep.name,
                "tep_sha256": hashlib.sha256(van.encode("utf-8")).hexdigest(),  # đề cương đổi ⇒ báo cáo cũ
                "luc": luc,
                "model": model,
                # 18/11/2026: đo độ đúng theo TỪNG phiên bản lời dặn (nhãn bác sĩ gắn cho lượt nào thì thuộc lời dặn đó)
                "loi_dan_sha256": hashlib.sha256(HE_THONG.encode("utf-8")).hexdigest()[:12],
                "thong_ke": {k: v for k, v in tk.items() if k != "loi"},
                "loi": tk.get("loi", []),
                "bo_qua_vi_tran": [c.id for c in bo],
                "cau": [asdict(c) for c in cau_ds],
                "ket_qua": [asdict(k) for k in ket],
                "tai_lieu_khong_dung": {str(k): v for k, v in ly_do_tl.items()},
                "luu_y": API.DISCLAIMER,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    xem = sum(1 for k in ket if can_xem(k))
    het_loi = tk["so_lo"] > 0 and tk["lo_loi"] == tk["so_lo"]
    API.ghi_nhat_ky_api(
        "error" if tk["so_lo"] and tk["lo_loi_api"] == tk["so_lo"] else "ok",
        "; ".join(tk.get("loi", []))[:200],
        len(ket),
        "kiem_noi_dung_trich_dan",
    )
    print(f"{'🟠' if xem else '🟢'} {xem} cặp cần bác sĩ xem / {len(ket)} · báo cáo {md}")
    if bo:
        print(f"⚠ Trần --toi-da {a.toi_da}: KHÔNG kiểm {len(bo)} đoạn cuối (từ {bo[0].id}).")
    if het_loi:
        return 2
    return 1 if xem else 0


if __name__ == "__main__":
    sys.exit(main())
