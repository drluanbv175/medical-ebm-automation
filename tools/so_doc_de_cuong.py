#!/usr/bin/env python3
"""SỔ ĐỌC ĐỀ CƯƠNG — đọc từng câu, hàng bảng, hình, công thức, tài liệu trước khi giao (K21, 22/11/2026).

VÌ SAO (bác sĩ 22/11/2026): «Đề cương phải được đọc từng câu từng chữ trước khi hoàn thành đưa cho tôi» và «Đảm bảo
đề cương hoàn thiện từng chữ, câu, bảng, đồ thị… đúng chuẩn đề cương nghiên cứu y khoa». Các chốt K1–K20 đo bằng luật;
chúng không chứng minh được rằng từng đơn vị văn bản đã có người đọc đối chiếu. Sổ này biến «đã đọc» thành dữ kiện kiểm
được: mỗi đơn vị có MÃ ỔN ĐỊNH (vị trí: loại + mục + thứ tự) và MÃ BĂM nội dung; bản ghi đọc gắn đúng băm lúc đọc.

ĐƠN VỊ (`tach_don_vi`):
  • `cau` — câu văn (tách câu tiếng Việt: không cắt ở số thập phân «0,78»/«1.000», viết tắt «tr.», «TS.», «v.v.»,
    «et al.», chữ cái đầu tên «V. A.», «PMID:»…; dấu đầu dòng/đánh số không phải câu);
  • `tieu_de` — đề mục;
  • `hang_bang` — mỗi hàng bảng (kể cả hàng tiêu đề cột), băm gồm tên bảng + hàng tiêu đề cột + hàng đó;
  • `hinh` — hình/biểu đồ: dòng ảnh `![…](bieu-bang/…)` + chú thích «**Hình/Biểu đồ/Sơ đồ …**»; băm gồm chú thích,
    đường dẫn, BĂM TỆP ẢNH và băm tệp dữ liệu vẽ cùng tên (`.json`/`.csv`) nếu có — đổi ảnh là đổi đơn vị;
  • `cong_thuc` — dòng công thức (khối `$$…$$`, hoặc dòng có «=» và ký hiệu toán, ít chữ);
  • `tltk` — mỗi mục tài liệu tham khảo đánh số, mã `tltk:<số>`.
TRẠNG THÁI một đơn vị: `chua_doc` (chưa có bản ghi, hoặc bản ghi mang băm KHÁC băm hiện hành — đã đổi sau khi đọc) ·
`da_doc` (bản ghi `dat` đúng băm) · `can_sua` (bản ghi `sua` đúng băm — chưa xử lý; sửa xong băm đổi ⇒ thành
`chua_doc` và phải đọc lại).

K21 (`loi_k21`/`canh_bao_k21`, nối vào `kiem_de_cuong_nop_hoi_dong`): đề cương ở trạng thái TRÌNH/GIAO — xác định bằng
điều kiện của hệ: có `G10_checkpoint.json` VÀ G10 chấm sống (`cong_song.trang_thai_song`) ở mức READY hoặc PASS (gói
phát hành sẵn sàng/đã khoá) — mà phủ < 100% đơn vị của bản HIỆN HÀNH, hoặc còn đơn vị `can_sua` ⇒ CHẶN. Chưa tới trạng
thái trình ⇒ chỉ BÁO tỷ lệ phủ, không chặn (việc đọc ở khâu cuối, sau khi các khâu trước đã khoá).

Lệnh:
  python3 tools/so_doc_de_cuong.py tach --study <mã> [--goc <thư mục chứa exports/>] [--json]
  python3 tools/so_doc_de_cuong.py trang-thai --study <mã> [--goc …] [--json]
  python3 tools/so_doc_de_cuong.py ghi --study <mã> --tu <tệp JSON> [--goc …]
     JSON: {"ban_ghi": [{"ma", "bam", "ket_qua": "dat"|"sua", "can_cu", "vai", "thoi_diem" (ISO, tuỳ chọn)}]}
Sổ: `exports/<mã>/SO_DOC_DE_CUONG_<mã>.json`. Mã thoát: 0 xong (trang-thai: phủ 100%, không `can_sua`) · 1 chưa đủ/có
bản ghi bị từ chối · 2 thiếu đề cương · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

SCHEMA = "so_doc_de_cuong/v1"
LOAI = ("cau", "tieu_de", "hang_bang", "hinh", "cong_thuc", "tltk")
KET_QUA = ("dat", "sua")


@dataclass
class DonVi:
    ma: str
    loai: str
    bam: str
    dong: int
    noi_dung: str


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _chuan(s: str) -> str:
    return re.sub(r"\s+", " ", _nfc(s)).strip()


def _bam(*phan: str) -> str:
    return hashlib.sha256("\x1f".join(_chuan(x) for x in phan).encode("utf-8")).hexdigest()[:16]


def _bam_tep(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return "THIEU_TEP"


# ───────────────────────────── tách câu tiếng Việt ─────────────────────────────
# Viết tắt kết thúc bằng dấu chấm KHÔNG kết thúc câu (so không phân biệt hoa thường, theo từ đứng ngay trước dấu chấm).
VIET_TAT = frozenset(x.casefold() for x in (
    "tr", "trang", "ts", "ths", "bs", "bsckii", "bscki", "pgs", "gs", "cn", "ks", "ds", "vd", "tp", "st", "no", "vol",
    "fig", "dr", "mr", "ms", "pp", "p", "ed", "eds", "al", "e.g", "i.e", "v.v", "tt", "nđ", "qđ", "q", "ph.d", "cs",
    "pmid", "doi", "isbn", "issn", "tlđd", "sđd", "op", "cit", "ibid", "etc", "vs", "approx", "ca", "khoảng"))
_KHOANG_TRANG = re.compile(r"\s+")


def tach_cau(van: str) -> List[str]:
    """Tách một đoạn văn thành câu. Chỉ cắt sau . ! ? … khi theo sau là khoảng trắng và chữ HOA/số/ngoặc mở, và từ trước
    dấu chấm không phải viết tắt, chữ cái đầu tên, hay số (thập phân «0,78» / «1.000» không có khoảng trắng nên tự an
    toàn; «mục 2.5.» trước chữ thường không cắt)."""
    van = _chuan(van)
    if not van:
        return []
    cau: List[str] = []
    dau = 0
    for m in re.finditer(r"[.!?…]+(?=\s)", van):
        cuoi = m.end()
        sau = van[cuoi:].lstrip()
        if not sau:
            continue
        ky = sau[0]
        if not (ky.isupper() or ky.isdigit() or ky in "«“\"([*"):
            continue
        truoc = van[dau:m.start()]
        tu = re.split(r"[\s(«“\"]", truoc)[-1] if truoc else ""
        tu_k = tu.rstrip(".").casefold()
        # «2.» một–hai chữ số = số thứ tự lựa chọn («1. Có ☐ 2. Không»), không phải hết câu
        # «2.1.» số hiệu mục/bảng nhiều cấp cũng không phải hết câu (gộp thừa an toàn hơn cắt sai: đơn vị vẫn được đọc)
        if m.group(0) == "." and (tu_k in VIET_TAT or re.fullmatch(r"[A-ZĐÀ-Ỹ]", tu) or re.fullmatch(r"\d{1,2}", tu)
                                  or re.fullmatch(r"\d+(?:\.\d+)+", tu)):
            continue
        cau.append(van[dau:cuoi].strip())
        dau = cuoi
    du = van[dau:].strip()
    if du:
        cau.append(du)
    return [c for c in cau if c]


# ───────────────────────────── nhận diện dòng ─────────────────────────────
_DE_MUC = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_ANH = re.compile(r"^\s*!\[([^\]]*)\]\(([^)\s]+)\)")
_CHU_THICH_HINH = re.compile(r"^\s*\*\*(Hình|Biểu đồ|Sơ đồ|Figure)\s", re.IGNORECASE)
_TEN_BANG = re.compile(r"^\s*\*\*(Bảng|Table)\s", re.IGNORECASE)
_PHAN_CACH_BANG = re.compile(r"^\s*\|?\s*:?-{3,}")
_TLTK = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+\S")
_DAU_DONG = re.compile(r"^\s*(?:[-*+•]\s+|\d+[.)]\s+|[a-zđ][.)]\s+)")
_KY_HIEU_TOAN = re.compile(r"[×÷√Σ∑∏±≈≠≤≥²³⁰¹⁴-⁹₀-₉∞π]|\\frac|\\sum|\^")
_CHU_VIET = re.compile(r"[A-Za-zÀ-ỹĐđ]{2,}")


def la_cong_thuc(dong: str) -> bool:
    s = dong.strip()
    if s.startswith("$$") or (s.startswith("$") and s.endswith("$") and len(s) > 2):
        return True
    if " = " not in s or s.startswith(("|", "#", "-", "*")) or len(s) > 220:
        return False
    return bool(_KY_HIEU_TOAN.search(s)) and len(_CHU_VIET.findall(s)) <= 6


def _khoa_muc(tieu_de: str) -> str:
    td = re.sub(r"[*_`]", "", _nfc(tieu_de)).strip()
    m = re.match(r"^(?:PHỤ LỤC\s+([A-Z0-9]+)|CHƯƠNG\s+(\d+)|((?:\d+\.)*\d+)\.?)\s", td, re.IGNORECASE)
    if m:
        if m.group(1):
            return "phu-luc-" + m.group(1).lower()
        if m.group(2):
            return "chuong-" + m.group(2)
        return m.group(3)
    a = unicodedata.normalize("NFKD", td.replace("đ", "d").replace("Đ", "D"))
    a = "".join(c for c in a if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", a).strip("-")[:40] or "muc"


def tach_don_vi(md: str, out_dir: Optional[Path] = None) -> List[DonVi]:
    """Mọi đơn vị đọc của một đề cương (thứ tự xuất hiện). `out_dir` để băm tệp ảnh của hình."""
    out_dir = Path(out_dir) if out_dir else None
    dong = _nfc(md).split("\n")
    ra: List[DonVi] = []
    dem: Dict[Tuple[str, str], int] = {}
    da_dung_muc: Dict[str, int] = {}
    muc = "bia"
    o_tltk = False
    i = 0
    da_tieu_thu: set = set()

    def them(loai: str, so_dong: int, noi_dung: str, *bam_phan: str, ma: Optional[str] = None) -> None:
        if ma is None:
            k = (muc, loai)
            dem[k] = dem.get(k, 0) + 1
            ma = f"{loai}:{muc}:{dem[k]}"
        ra.append(DonVi(ma, loai, _bam(loai, *bam_phan), so_dong, _chuan(noi_dung)[:200]))

    while i < len(dong):
        d = dong[i]
        so = i + 1
        if i in da_tieu_thu or not d.strip():
            i += 1
            continue
        m = _DE_MUC.match(d)
        if m:
            k = _khoa_muc(m.group(2))
            da_dung_muc[k] = da_dung_muc.get(k, 0) + 1
            muc = k if da_dung_muc[k] == 1 else f"{k}~{da_dung_muc[k]}"
            o_tltk = bool(re.search(r"TÀI LIỆU THAM KHẢO", m.group(2), re.IGNORECASE))
            them("tieu_de", so, m.group(2), m.group(2))
            i += 1
            continue
        if d.lstrip().startswith("|"):
            # gom cả bảng; tên bảng = dòng «**Bảng …**» gần nhất phía trên (≤ 3 dòng không trống)
            ten = ""
            j, xet = i - 1, 0
            while j >= 0 and xet < 3:
                if dong[j].strip():
                    xet += 1
                    if _TEN_BANG.match(dong[j]):
                        ten = dong[j].strip()
                        break
                j -= 1
            hang: List[Tuple[int, str]] = []
            while i < len(dong) and dong[i].lstrip().startswith("|"):
                if not _PHAN_CACH_BANG.match(dong[i]):
                    hang.append((i + 1, dong[i].strip()))
                i += 1
            k = (muc, "bang")
            dem[k] = dem.get(k, 0) + 1
            stt_bang = dem[k]
            dau_cot = hang[0][1] if hang else ""
            for r, (sd, h) in enumerate(hang):
                them("hang_bang", sd, h, ten, dau_cot, h, ma=f"hang_bang:{muc}:{stt_bang}:{r}")
            continue
        ma_anh = _ANH.match(d)
        if ma_anh or _CHU_THICH_HINH.match(d):
            chu_thich, duong = (d.strip(), "")
            if ma_anh:
                duong = ma_anh.group(2)
                for j in range(i + 1, min(i + 4, len(dong))):
                    if _CHU_THICH_HINH.match(dong[j]):
                        chu_thich = dong[j].strip()
                        da_tieu_thu.add(j)
                        break
            bam_anh, bam_dl = "KHONG_CO_ANH", ""
            if duong:
                p_anh = (out_dir / duong) if out_dir else Path(duong)
                bam_anh = _bam_tep(p_anh)
                for duoi in (".json", ".csv"):
                    p_dl = p_anh.with_suffix(duoi)
                    if p_dl.is_file():
                        bam_dl += duoi + _bam_tep(p_dl)
            them("hinh", so, chu_thich, chu_thich, duong, bam_anh, bam_dl)
            i += 1
            continue
        if la_cong_thuc(d):
            them("cong_thuc", so, d, d)
            i += 1
            continue
        mt = _TLTK.match(d)
        if o_tltk and mt:
            n = mt.group(1) or mt.group(2)
            them("tltk", so, d, d, ma=f"tltk:{n}")
            i += 1
            continue
        if _TEN_BANG.match(d):  # tên bảng là MỘT đơn vị (không cắt ở «Bảng 2.1.»)
            them("cau", so, d, d)
            i += 1
            continue
        van = _DAU_DONG.sub("", d, count=1)
        for c in tach_cau(van):
            them("cau", so, c, c)
        i += 1
    return ra


# ───────────────────────────── sổ đọc ─────────────────────────────
def tep_de_cuong(out_dir: Path, study: str) -> Path:
    return Path(out_dir) / f"DE_CUONG_NOP_HOI_DONG_{study}.md"


def tep_so(out_dir: Path, study: str) -> Path:
    return Path(out_dir) / f"SO_DOC_DE_CUONG_{study}.json"


def doc_so(out_dir: Path, study: str) -> Dict[str, Any]:
    try:
        v = json.loads(tep_so(out_dir, study).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema": SCHEMA, "study": study, "ban_ghi": {}, "lich_su": []}
    if not isinstance(v, dict) or not isinstance(v.get("ban_ghi"), dict):
        return {"schema": SCHEMA, "study": study, "ban_ghi": {}, "lich_su": []}
    return v


def trang_thai_don_vi(dv: DonVi, ban_ghi: Optional[Dict[str, Any]]) -> str:
    """chua_doc · da_doc · can_sua. Bản ghi mang băm khác băm hiện hành ⇒ chưa đọc (đơn vị đã đổi sau khi đọc)."""
    if not isinstance(ban_ghi, dict) or ban_ghi.get("bam") != dv.bam:
        return "chua_doc"
    return "da_doc" if ban_ghi.get("ket_qua") == "dat" else ("can_sua" if ban_ghi.get("ket_qua") == "sua"
                                                                else "chua_doc")


def trang_thai(out_dir: Path, study: str) -> Dict[str, Any]:
    p = tep_de_cuong(out_dir, study)
    try:
        md = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"co_de_cuong": False, "tong": 0}
    dv = tach_don_vi(md, out_dir)
    so = doc_so(out_dir, study)["ban_ghi"]
    theo: Dict[str, List[DonVi]] = {"chua_doc": [], "da_doc": [], "can_sua": []}
    doi = 0
    for x in dv:
        tt = trang_thai_don_vi(x, so.get(x.ma))
        theo[tt].append(x)
        if tt == "chua_doc" and isinstance(so.get(x.ma), dict):
            doi += 1
    dem_loai = {lo: sum(1 for x in dv if x.loai == lo) for lo in LOAI}
    tong = len(dv)
    return {"co_de_cuong": True, "tong": tong, "theo_loai": dem_loai, "da_doc": len(theo["da_doc"]),
            "chua_doc": len(theo["chua_doc"]), "doi_sau_doc": doi, "can_sua": len(theo["can_sua"]),
            "ty_le_phu": (len(theo["da_doc"]) / tong) if tong else 0.0,
            "ds_chua_doc": [asdict(x) for x in theo["chua_doc"]], "ds_can_sua": [asdict(x) for x in theo["can_sua"]]}


def _iso_hop_le(v: Any) -> bool:
    try:
        t = datetime.fromisoformat(str(v))
    except (TypeError, ValueError):
        return False
    bay_gio = datetime.now(t.tzinfo) if t.tzinfo else datetime.now()
    return t <= bay_gio


def ghi(out_dir: Path, study: str, nhap: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Ghi bản ghi đọc. Từ chối: mã không có trong bản hiện hành, băm khác băm hiện hành, kết quả ngoài dat/sua, thiếu
    căn cứ/vai, thời điểm không phải ISO hoặc ở tương lai. Trả (số bản ghi đã nhận, lý do từ chối)."""
    md = tep_de_cuong(out_dir, study).read_text(encoding="utf-8")
    hien = {x.ma: x for x in tach_don_vi(md, out_dir)}
    so = doc_so(out_dir, study)
    tu_choi: List[str] = []
    nhan = 0
    for r in nhap.get("ban_ghi") or []:
        if not isinstance(r, dict):
            tu_choi.append("bản ghi không phải đối tượng")
            continue
        ma = str(r.get("ma") or "")
        if ma not in hien:
            tu_choi.append(f"{ma}: không có trong bản đề cương hiện hành")
            continue
        if r.get("bam") != hien[ma].bam:
            tu_choi.append(f"{ma}: băm {r.get('bam')} khác băm hiện hành {hien[ma].bam} — đơn vị đã đổi, đọc lại")
            continue
        if r.get("ket_qua") not in KET_QUA:
            tu_choi.append(f"{ma}: kết quả phải là dat hoặc sua")
            continue
        if not str(r.get("can_cu") or "").strip() or not str(r.get("vai") or "").strip():
            tu_choi.append(f"{ma}: thiếu căn cứ hoặc vai người đọc")
            continue
        td = r.get("thoi_diem") or datetime.now().isoformat(timespec="seconds")
        if not _iso_hop_le(td):
            tu_choi.append(f"{ma}: thời điểm không phải ISO hoặc ở tương lai")
            continue
        bg = {"bam": hien[ma].bam, "ket_qua": r["ket_qua"], "can_cu": str(r["can_cu"]).strip(),
              "vai": str(r["vai"]).strip(), "thoi_diem": str(td), "loai": hien[ma].loai}
        so["ban_ghi"][ma] = bg
        so.setdefault("lich_su", []).append({"ma": ma, **bg})
        nhan += 1
    if nhan:
        so["schema"], so["study"] = SCHEMA, study
        p = tep_so(out_dir, study)
        tam = p.with_name(p.name + ".tam")
        tam.write_text(json.dumps(so, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        tam.replace(p)
    return nhan, tu_choi


# ───────────────────────────── K21 ─────────────────────────────
def dang_trinh(out_dir: Path, study: str) -> Tuple[bool, str]:
    """Đề cương ở trạng thái trình/giao: có G10_checkpoint.json và G10 chấm sống ở mức READY hoặc PASS."""
    if not (Path(out_dir) / "G10_checkpoint.json").is_file():
        return False, "chưa có G10_checkpoint.json"
    try:
        import cong_song as CS  # noqa: PLC0415

        s = CS.trang_thai_song("G10", study, Path(out_dir))
    except Exception as e:  # noqa: BLE001 — không đo được trạng thái ⇒ không coi là đang trình (không chặn giả)
        return False, f"không chấm sống được G10: {type(e).__name__}"
    return s.get("muc") in ("READY", "PASS"), f"G10 chấm sống {s.get('status')}"


def loi_k21(out_dir: Path, study: str) -> List[str]:
    """K21 — đang trình/giao mà sổ đọc chưa phủ 100% đơn vị của bản hiện hành, hoặc còn đơn vị cần sửa ⇒ lỗi chặn."""
    if not tep_de_cuong(out_dir, study).is_file():
        return []
    trinh, ly = dang_trinh(out_dir, study)
    if not trinh:
        return []
    tt = trang_thai(out_dir, study)
    loi: List[str] = []
    if tt["da_doc"] < tt["tong"]:
        loi.append(f"K21 đề cương đang ở trạng thái trình ({ly}) nhưng sổ đọc mới phủ {tt['da_doc']}/{tt['tong']} "
                   f"đơn vị ({tt['chua_doc']} chưa đọc, trong đó {tt['doi_sau_doc']} đã đổi sau khi đọc) — đọc từng "
                   f"đơn vị rồi ghi: tools/so_doc_de_cuong.py ghi --study {study} --tu <tệp>")
    if tt["can_sua"]:
        loi.append(f"K21 còn {tt['can_sua']} đơn vị người đọc ghi «sua» chưa xử lý: "
                   + ", ".join(x["ma"] for x in tt["ds_can_sua"][:6]))
    return loi


def canh_bao_k21(out_dir: Path, study: str) -> List[str]:
    """Chưa tới trạng thái trình ⇒ báo tỷ lệ phủ của sổ đọc (không chặn)."""
    if not tep_de_cuong(out_dir, study).is_file():
        return []
    trinh, ly = dang_trinh(out_dir, study)
    if trinh:
        return []
    tt = trang_thai(out_dir, study)
    return [f"K21 sổ đọc từng đơn vị phủ {tt['da_doc']}/{tt['tong']} ({tt['ty_le_phu']:.0%}; {ly}) — chưa tới trạng "
            "thái trình nên chưa chặn; đọc ở khâu cuối sau khi các khâu trước đã khoá"]


# ───────────────────────────── CLI ─────────────────────────────
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Sổ đọc đề cương từng đơn vị (K21).")
    ap.add_argument("lenh", choices=("tach", "trang-thai", "ghi"))
    ap.add_argument("--study", required=True)
    ap.add_argument("--goc", type=Path, default=BASE)
    ap.add_argument("--tu", type=Path, help="(ghi) tệp JSON bản ghi đọc")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 3
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print(f"Mã đề tài không hợp lệ: {a.study!r}")
        return 3
    out_dir = Path(a.goc) / "exports" / a.study
    if not tep_de_cuong(out_dir, a.study).is_file():
        print(f"Không có đề cương nộp: {tep_de_cuong(out_dir, a.study)}")
        return 2
    if a.lenh == "tach":
        dv = tach_don_vi(tep_de_cuong(out_dir, a.study).read_text(encoding="utf-8"), out_dir)
        dem = {lo: sum(1 for x in dv if x.loai == lo) for lo in LOAI}
        if a.json:
            print(json.dumps({"study": a.study, "tong": len(dv), "theo_loai": dem, "don_vi": [asdict(x) for x in dv]},
                             ensure_ascii=False, indent=1))
        else:
            print(f"{a.study}: {len(dv)} đơn vị — " + ", ".join(f"{k} {v}" for k, v in dem.items()))
        return 0
    if a.lenh == "trang-thai":
        tt = trang_thai(out_dir, a.study)
        if a.json:
            print(json.dumps(tt, ensure_ascii=False, indent=1))
        else:
            print(f"{a.study}: phủ {tt['da_doc']}/{tt['tong']} ({tt['ty_le_phu']:.0%}) · chưa đọc {tt['chua_doc']} "
                  f"(đổi sau khi đọc {tt['doi_sau_doc']}) · cần sửa {tt['can_sua']}")
            for x in tt["ds_can_sua"][:20]:
                print(f"  ✎ {x['ma']} (dòng {x['dong']}): {x['noi_dung'][:100]}")
        return 0 if tt["tong"] and tt["da_doc"] == tt["tong"] and not tt["can_sua"] else 1
    if not a.tu:
        print("Lệnh ghi cần --tu <tệp JSON>")
        return 3
    try:
        nhap = json.loads(a.tu.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"Không đọc được {a.tu}: {e}")
        return 3
    nhan, tu_choi = ghi(out_dir, a.study, nhap if isinstance(nhap, dict) else {})
    print(f"Đã ghi {nhan} bản ghi; từ chối {len(tu_choi)}")
    for x in tu_choi[:30]:
        print(f"  ✗ {x}")
    return 1 if tu_choi else 0


if __name__ == "__main__":
    raise SystemExit(main())
