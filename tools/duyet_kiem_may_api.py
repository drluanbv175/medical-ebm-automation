#!/usr/bin/env python3
"""Duyệt và đo độ đúng của kiểm máy bằng Claude API (A12 nội dung trích dẫn · phản biện máy đề cương).

VÌ SAO (18/11/2026, bác sĩ chọn «báo cáo cũ + đo độ đúng» khi hoàn thiện kết nối Claude API). Đo trên BTM:
- Lượt kiểm chạy 17/11 lúc 17:59, đề cương sinh lại lúc 20:14 ⇒ cả hai báo cáo đã CŨ mà không ai biết: báo cáo không
  ghi mã băm của tệp đã kiểm. Nay công cụ kiểm ghi `tep_sha256`; báo cáo cũ hơn (chưa có mã băm) được suy theo thời
  điểm sửa tệp.
- 24 phát hiện phản biện máy + 8 cặp A12 cần xem chưa ai duyệt ⇒ không biết máy đúng bao nhiêu phần. Công cụ dựng PHIẾU
  đánh số, ghi NHÃN từ đúng lời bác sĩ (nguyên văn), rồi đo tỷ lệ đúng = đúng / (đúng + sai) theo công cụ và mức.

Ranh giới: TƯ VẤN, chỉ đọc báo cáo máy. Máy KHÔNG tự gắn nhãn đúng/sai — nhãn chỉ từ `ghi --loi "<nguyên văn bác sĩ>"`.
Không gọi API, không sửa đề cương, không mở/chặn cổng. Chỉ dùng thư viện chuẩn để hòm việc ở repo gốc nạp trực tiếp.

Dùng:
  duyet_kiem_may_api.py tinh-trang --study <mã> | --tat-ca [--json]   # báo cáo cũ? bao nhiêu mục chưa duyệt? tỷ lệ đúng
  duyet_kiem_may_api.py phieu --study <mã>                            # phiếu đánh số các mục cần duyệt
  duyet_kiem_may_api.py ghi --study <mã> --loi "1-3 đúng, 4 sai, 5 không rõ" [--ap-dung]
  duyet_kiem_may_api.py do --study <mã> [--json]                      # tỷ lệ đúng theo công cụ và mức
Mã thoát: 0 mọi báo cáo còn hiệu lực và đã duyệt hết · 1 có báo cáo cũ hoặc mục chưa duyệt · 2 không đo được ·
3 tham số sai / phiếu cũ / lời ghi không đọc được.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
BAO_CAO = {
    "A12": "A12_KIEM_NOI_DUNG_{s}.json",
    "PHAN_BIEN": "PHAN_BIEN_MAY_{s}.json",
    # 18/11/2026 — thí điểm kiểm tổng quan tài liệu G0-T3/T4 bằng API (tools/kiem_tong_quan_g0_api.py)
    "G0": "G0_KIEM_TONG_QUAN_{s}.json",
}
TEN = {"A12": "kiểm nội dung trích dẫn A12", "PHAN_BIEN": "phản biện máy đề cương",
       "G0": "kiểm tổng quan tài liệu G0-T3/T4"}
MUC_G0_A_CAN_XEM = ("sai", "khong_hop_ly", "sai_lech", "can_xem")  # cùng luật `kiem_tong_quan_g0_api.can_xem_a`
MUC_A12_CAN_XEM = ("khong_ho_tro", "ho_tro_mot_phan", "can_xem")  # cùng luật `kiem_noi_dung_trich_dan.can_xem`
THU_TU_MUC = {"cao": 0, "vua": 1, "thap": 2}
NHAN_HOP_LE = ("dung", "sai", "khong_ro")
_STUDY = re.compile(r"^[A-Za-z0-9._-]+$")


def _sha_tep(p: Path) -> str:
    return hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _doc_json(p: Path) -> Optional[Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _ghi_json(p: Path, du_lieu: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(f"{p.name}.{os.getpid()}.tmp")
    tam.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    os.replace(tam, p)


def thu_muc(study: str, goc: Path = REPO) -> Path:
    return goc / "exports" / study / "kiem_may_api"


def _luc(s: Any) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(str(s or "")[:19])
    except ValueError:
        return None


# ── Báo cáo cũ hay còn hiệu lực ──────────────────────────────────────────────────────────────────────────────────
def hieu_luc(bc: Dict[str, Any], study: str, goc: Path = REPO) -> Tuple[Optional[bool], str]:
    """(cũ?, lý do). True = cũ · False = còn hiệu lực · None = không đo được (thiếu tệp đã kiểm, thiếu mốc)."""
    tep = goc / "exports" / study / str(bc.get("tep") or "")
    if not bc.get("tep") or not tep.is_file():
        return None, f"không thấy tệp đã kiểm «{bc.get('tep')}»"
    if bc.get("tep_sha256"):
        if _sha_tep(tep) != bc["tep_sha256"]:
            return True, f"{tep.name} đã đổi sau lượt kiểm (mã băm khác)"
        # 18/11/2026: báo cáo đọc NHIỀU tệp (kiểm G0: tổng hợp + khoảng trống) — tệp phụ đổi/vắng cũng là báo cáo cũ
        for ten, sha in (bc.get("tep_phu") or {}).items():
            phu = goc / "exports" / study / str(ten)
            if not phu.is_file():
                return True, f"tệp phụ {ten} không còn"
            if _sha_tep(phu) != sha:
                return True, f"{ten} đã đổi sau lượt kiểm (mã băm khác)"
        return False, "mã băm khớp"
    luc = _luc(bc.get("luc"))
    if luc is None:
        return None, "báo cáo không có mốc thời gian"
    sua = dt.datetime.fromtimestamp(tep.stat().st_mtime)
    if sua > luc:
        return True, (
            f"{tep.name} sửa lúc {sua:%d/%m %H:%M}, sau lượt kiểm {luc:%d/%m %H:%M} (báo cáo cũ chưa có mã băm)"
        )
    return None, "báo cáo cũ chưa có mã băm — không khẳng định được còn hiệu lực; chạy lại để có mã băm"


# ── Mục cần duyệt ────────────────────────────────────────────────────────────────────────────────────────────────
def muc_can_duyet(loai: str, bc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Danh sách mục cần bác sĩ duyệt, mỗi mục một khoá BỀN (không phụ thuộc thứ tự)."""
    ra: List[Dict[str, Any]] = []
    if loai == "A12":
        cau = {c.get("id"): c.get("cau", "") for c in bc.get("cau") or []}
        for k in bc.get("ket_qua") or []:
            co = [str(x) for x in k.get("co") or []]
            if k.get("muc") in MUC_A12_CAN_XEM or any(x.startswith("so_khong_thay") for x in co):
                ra.append(
                    {
                        "khoa": f"A12|{k.get('id')}|{k.get('so')}",
                        "cong_cu": "A12",
                        "muc": str(k.get("muc")),
                        "tieu_de": f"{k.get('id')} ↔ tài liệu [{k.get('so')}] — máy phán «{k.get('muc')}»",
                        "chi_tiet": [
                            f"Câu: {str(cau.get(k.get('id'), ''))[:400]}",
                            f"Máy nói: {k.get('ly_do', '')}",
                            *([f"Trích căn cứ: «{k.get('trich')}»"] if k.get("trich") else []),
                            *([f"Cờ máy: {', '.join(co)}"] if co else []),
                        ],
                    }
                )
    elif loai == "G0":
        ra += _muc_g0(bc)
    else:
        ds = sorted(bc.get("phat_hien") or [], key=lambda p: (THU_TU_MUC.get(str(p.get("muc")), 9), p.get("dong") or 0))
        for p in ds:
            tr = str(p.get("trich") or "")
            ra.append(
                {
                    "khoa": f"PB|{p.get('dong')}|{p.get('loai')}|{hashlib.sha1(tr.encode('utf-8')).hexdigest()[:10]}",
                    "cong_cu": "PHAN_BIEN",
                    "muc": str(p.get("muc")),
                    "tieu_de": f"dòng {p.get('dong')} · {p.get('loai')} · mức {p.get('muc')}",
                    "chi_tiet": [
                        f"Trích: «{tr[:300]}»",
                        *(
                            [f"Đối chiếu dòng {p['doi_chieu'].get('dong')}: «{str(p['doi_chieu'].get('trich'))[:300]}»"]
                            if isinstance(p.get("doi_chieu"), dict)
                            else []
                        ),
                        f"Vấn đề: {p.get('van_de', '')}",
                        f"Gợi ý: {p.get('goi_y', '')}",
                    ],
                }
            )
    return ra


def _muc_g0(bc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Mục cần duyệt của báo cáo kiểm G0 (18/11/2026): A — trường bảng sàng lọc · B — cặp đoạn tổng hợp ↔ tài liệu ·
    C — vấn đề khoảng trống. Khoá bền theo định danh bài/trường, không theo thứ tự."""
    ra: List[Dict[str, Any]] = []
    for k in bc.get("a") or []:
        co = [str(x) for x in k.get("co") or []]
        if k.get("muc") in MUC_G0_A_CAN_XEM or any(x.startswith("so_khong_thay") for x in co):
            ra.append({"khoa": f"G0A|{k.get('dinh_danh')}|{k.get('truong')}", "cong_cu": "G0_SANG_LOC",
                       "muc": str(k.get("muc")),
                       "tieu_de": (f"bảng sàng lọc · {k.get('dinh_danh')} · {k.get('truong')} — máy phán "
                                   f"«{k.get('muc')}»"),
                       "chi_tiet": [f"Máy nói: {k.get('ly_do', '')}",
                                    *([f"Trích căn cứ: «{k.get('trich')}»"] if k.get("trich") else []),
                                    *([f"Cờ máy: {', '.join(co)}"] if co else [])]})
    cau = {c.get("id"): c for c in bc.get("cau_b") or []}
    for k in bc.get("b") or []:
        co = [str(x) for x in k.get("co") or []]
        if k.get("muc") in MUC_A12_CAN_XEM or any(x.startswith("so_khong_thay") for x in co):
            doan = str((cau.get(k.get("id")) or {}).get("doan") or "")
            ra.append({"khoa": f"G0B|{hashlib.sha1(doan.encode('utf-8')).hexdigest()[:10]}|{k.get('dinh_danh')}",
                       "cong_cu": "G0_TONG_HOP", "muc": str(k.get("muc")),
                       "tieu_de": f"đoạn tổng hợp ↔ {k.get('dinh_danh')} — máy phán «{k.get('muc')}»",
                       "chi_tiet": [f"Đoạn: {doan[:400]}", f"Máy nói: {k.get('ly_do', '')}",
                                    *([f"Trích căn cứ: «{k.get('trich')}»"] if k.get("trich") else []),
                                    *([f"Cờ máy: {', '.join(co)}"] if co else [])]})
    for k in bc.get("c") or []:
        if k.get("muc") in ("van_de", "can_xem"):
            tr = str(k.get("trich") or "")
            ra.append({"khoa": f"G0C|{k.get('loai')}|{hashlib.sha1(tr.encode('utf-8')).hexdigest()[:10]}",
                       "cong_cu": "G0_KHOANG_TRONG", "muc": str(k.get("loai")),
                       "tieu_de": f"khoảng trống · {k.get('loai')}" + (f" · {k['dinh_danh']}" if k.get("dinh_danh")
                                                                       else ""),
                       "chi_tiet": [f"Trích: «{tr[:300]}»", f"Máy nói: {k.get('ly_do', '')}",
                                    *([f"Cờ máy: {', '.join(k['co'])}"] if k.get("co") else [])]})
    return ra


def doc_bao_cao(study: str, goc: Path = REPO) -> Dict[str, Dict[str, Any]]:
    """loại → {bc, sha (của tệp báo cáo), muc}. Báo cáo vắng thì không có khoá; hỏng ⇒ {"hong": True}."""
    ra: Dict[str, Dict[str, Any]] = {}
    for loai, mau in BAO_CAO.items():
        p = thu_muc(study, goc) / mau.format(s=study)
        if not p.is_file():
            continue
        bc = _doc_json(p)
        if not isinstance(bc, dict):
            ra[loai] = {"hong": True, "tep_bao_cao": p.name}
            continue
        ra[loai] = {"bc": bc, "sha_bao_cao": _sha_tep(p), "tep_bao_cao": p.name, "muc": muc_can_duyet(loai, bc)}
    return ra


def tep_duyet(study: str, goc: Path = REPO) -> Path:
    return thu_muc(study, goc) / f"DUYET_KIEM_MAY_{study}.json"


def tep_phieu(study: str, goc: Path = REPO) -> Path:
    return thu_muc(study, goc) / f"PHIEU_DUYET_KIEM_MAY_{study}.json"


def doc_nhan(study: str, goc: Path = REPO) -> Dict[str, Any]:
    d = _doc_json(tep_duyet(study, goc))
    return d if isinstance(d, dict) and isinstance(d.get("nhan"), dict) else {"nhan": {}, "lan_ghi": []}


# ── Tình trạng · độ đúng ─────────────────────────────────────────────────────────────────────────────────────────
def do_dung(muc: Sequence[Dict[str, Any]], nhan: Dict[str, Any]) -> Dict[str, Any]:
    """Tỷ lệ đúng = đúng / (đúng + sai); «không rõ» và chưa duyệt không tính vào mẫu số."""

    def _dem(ds: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        n = {"dung": 0, "sai": 0, "khong_ro": 0, "chua_duyet": 0}
        for m in ds:
            n[(nhan.get(m["khoa"]) or {}).get("nhan") or "chua_duyet"] += 1
        mau = n["dung"] + n["sai"]
        n["ty_le_dung"] = round(n["dung"] / mau, 3) if mau else None
        return n

    theo: Dict[str, Any] = {"tong": _dem(muc)}
    for cc in sorted({m["cong_cu"] for m in muc}):
        theo[cc] = _dem([m for m in muc if m["cong_cu"] == cc])
        for mc in sorted({m["muc"] for m in muc if m["cong_cu"] == cc}):
            theo[f"{cc}/{mc}"] = _dem([m for m in muc if m["cong_cu"] == cc and m["muc"] == mc])
    return theo


def tinh_trang(study: str, goc: Path = REPO) -> Dict[str, Any]:
    """Tình trạng kiểm máy API của một đề tài. `do_duoc=False` khi chưa có báo cáo nào đọc được."""
    bcs = doc_bao_cao(study, goc)
    nhan = doc_nhan(study, goc)["nhan"]
    ds, tat_ca_muc = [], []
    for loai, x in bcs.items():
        if x.get("hong"):
            ds.append({"loai": loai, "ten": TEN[loai], "hong": True, "tep_bao_cao": x["tep_bao_cao"]})
            continue
        cu, ly_do = hieu_luc(x["bc"], study, goc)
        muc = x["muc"]
        tat_ca_muc += muc
        dd = do_dung(muc, nhan)
        ds.append(
            {
                "loai": loai,
                "ten": TEN[loai],
                "luc": x["bc"].get("luc"),
                "model": x["bc"].get("model"),
                "cu": cu,
                "ly_do": ly_do,
                "can_duyet": len(muc),
                "chua_duyet": dd["tong"]["chua_duyet"],
                "ty_le_dung": dd["tong"]["ty_le_dung"],
            }
        )
    return {
        "study": study,
        "do_duoc": bool(ds) and not all(b.get("hong") for b in ds),
        "bao_cao": ds,
        "do_dung": do_dung(tat_ca_muc, nhan) if tat_ca_muc else None,
    }


def cac_de_tai(goc: Path = REPO) -> List[str]:
    """Đề tài có thư mục kiem_may_api (đề tài thật lẫn giả lập ZZCANARY — hòm việc tự lọc giả lập)."""
    ex = goc / "exports"
    if not ex.is_dir():
        return []
    return sorted(d.name for d in ex.iterdir() if (d / "kiem_may_api").is_dir() and _STUDY.match(d.name))


def tinh_trang_tat_ca(goc: Path = REPO, bo_gia_lap: bool = True) -> List[Dict[str, Any]]:
    return [tinh_trang(s, goc) for s in cac_de_tai(goc) if not (bo_gia_lap and s.upper().startswith("ZZCANARY"))]


def ma_thoat(tt: Sequence[Dict[str, Any]]) -> int:
    if not tt or not any(t["do_duoc"] for t in tt):
        return 2
    for t in tt:
        for b in t["bao_cao"]:
            if b.get("hong") or b.get("cu") or b.get("chua_duyet"):
                return 1
    return 0


# ── Phiếu · ghi nhãn ─────────────────────────────────────────────────────────────────────────────────────────────
def dung_phieu(study: str, goc: Path = REPO) -> Tuple[Path, Path, int]:
    """Ghi phiếu Markdown + bảng số→khoá (JSON). Mục đã có nhãn vẫn liệt kê (kèm nhãn hiện có) để bác sĩ sửa được."""
    bcs = doc_bao_cao(study, goc)
    nhan = doc_nhan(study, goc)["nhan"]
    muc: List[Dict[str, Any]] = []
    for loai in BAO_CAO:
        if loai in bcs and not bcs[loai].get("hong"):
            muc += bcs[loai]["muc"]
    luc = dt.datetime.now().isoformat(timespec="seconds")
    so_khoa = {str(i): m["khoa"] for i, m in enumerate(muc, 1)}
    sha = {loai: x.get("sha_bao_cao") for loai, x in bcs.items() if not x.get("hong")}
    _ghi_json(tep_phieu(study, goc), {"study": study, "luc": luc, "sha_bao_cao": sha, "so_khoa": so_khoa})
    dong = [
        f"# Phiếu duyệt kiểm máy Claude API — {study}",
        "",
        f"Dựng lúc {luc}. Mỗi mục là MỘT phát hiện của máy. Bác sĩ trả lời theo số, ví dụ:",
        "`1-3 đúng, 4 sai, 5 không rõ` — «đúng» = máy nói đúng (có vấn đề thật), «sai» = máy báo nhầm.",
        "Máy KHÔNG tự gắn nhãn. Tỷ lệ đúng chỉ tính trên các mục bác sĩ đã trả lời «đúng» hoặc «sai».",
        "",
    ]
    for loai in BAO_CAO:
        x = bcs.get(loai)
        if not x:
            continue
        if x.get("hong"):
            dong += [f"## {TEN[loai]}", "", f"⚠ Báo cáo {x['tep_bao_cao']} hỏng — không đọc được.", ""]
            continue
        cu, ly_do = hieu_luc(x["bc"], study, goc)
        trang = {True: "⚠ CŨ", False: "còn hiệu lực", None: "chưa khẳng định được"}[cu]
        dong += [f"## {TEN[loai]} — lượt {x['bc'].get('luc')} · {trang} ({ly_do})", ""]
        for so, k in so_khoa.items():
            m = next((y for y in x["muc"] if y["khoa"] == k), None)
            if m is None:
                continue
            hien = (nhan.get(k) or {}).get("nhan")
            dong.append(f"**{so}.** {m['tieu_de']}" + (f" — nhãn hiện có: **{hien}**" if hien else ""))
            dong += [f"   - {c}" for c in m["chi_tiet"]]
            dong.append("")
    md = thu_muc(study, goc) / f"PHIEU_DUYET_KIEM_MAY_{study}.md"
    md.write_text("\n".join(dong).rstrip() + "\n", encoding="utf-8", newline="\n")
    return md, tep_phieu(study, goc), len(muc)


_NHAN_TU = [
    (re.compile(r"^(đúng|dung|đ|d|✓|ok)$", re.I), "dung"),
    (re.compile(r"^(sai|s|✗|x|nhầm|nham)$", re.I), "sai"),
    (re.compile(r"^(không\s*rõ|khong\s*ro|chưa\s*rõ|chua\s*ro|\?)$", re.I), "khong_ro"),
]
_DOAN = re.compile(
    r"((?:\d+\s*(?:[-–]\s*\d+)?\s*[,\s]\s*)*\d+(?:\s*[-–]\s*\d+)?)\s*[:=]?\s*"
    r"(đúng|dung|sai|nhầm|nham|không\s*rõ|khong\s*ro|chưa\s*rõ|chua\s*ro|✓|✗|\?)",
    re.I,
)


def doc_loi(loi: str, toi_da: int) -> Dict[int, str]:
    """«1-3 đúng, 4 sai; 5,7 không rõ» ⇒ {1: dung, 2: dung, 3: dung, 4: sai, 5: khong_ro, 7: khong_ro}.

    Số ngoài 1..toi_da, một số có hai nhãn khác nhau, hay không đọc được đoạn nào ⇒ ValueError (không đoán)."""
    ra: Dict[int, str] = {}
    thay = False
    for m in _DOAN.finditer(loi or ""):
        thay = True
        tu = re.sub(r"\s+", " ", m.group(2).strip().lower())
        nhan = next((n for r, n in _NHAN_TU if r.match(tu)), None)
        if nhan is None:
            raise ValueError(f"không hiểu nhãn «{m.group(2)}»")
        for phan in re.split(r"[,\s]+", re.sub(r"\s*[-–]\s*", "-", m.group(1).strip())):
            if not phan:
                continue
            a, _, b = phan.partition("-")
            dau, cuoi = int(a), int(b or a)
            if dau > cuoi:
                raise ValueError(f"khoảng ngược «{phan}»")
            for so in range(dau, cuoi + 1):
                if not 1 <= so <= toi_da:
                    raise ValueError(f"mục {so} không có trong phiếu (1–{toi_da})")
                if ra.get(so, nhan) != nhan:
                    raise ValueError(f"mục {so} có hai nhãn khác nhau")
                ra[so] = nhan
    if not thay:
        raise ValueError("không đọc được đoạn «<số> <đúng|sai|không rõ>» nào")
    return ra


def ghi_nhan(study: str, loi: str, ap_dung: bool, goc: Path = REPO) -> Dict[str, Any]:
    """Ghi nhãn từ lời bác sĩ. Phiếu cũ hơn báo cáo (máy đã chạy lại sau khi dựng phiếu) ⇒ từ chối (số đã đổi nghĩa)."""
    ph = _doc_json(tep_phieu(study, goc))
    if not isinstance(ph, dict) or not ph.get("so_khoa"):
        raise ValueError("chưa có phiếu — chạy `phieu --study` trước")
    bcs = doc_bao_cao(study, goc)
    for loai, sha in (ph.get("sha_bao_cao") or {}).items():
        if (bcs.get(loai) or {}).get("sha_bao_cao") != sha:
            raise ValueError(f"báo cáo {TEN[loai]} đã đổi sau khi dựng phiếu — dựng lại phiếu (`phieu`), trả lời lại")
    so = doc_loi(loi, len(ph["so_khoa"]))
    d = doc_nhan(study, goc)
    luc = dt.datetime.now().isoformat(timespec="seconds")
    for n, nhan in so.items():
        d["nhan"][ph["so_khoa"][str(n)]] = {"nhan": nhan, "luc": luc, "phieu_so": n}
    d["lan_ghi"] = (d.get("lan_ghi") or []) + [{"luc": luc, "loi_nguyen_van": loi, "so_muc": len(so)}]
    if ap_dung:
        _ghi_json(tep_duyet(study, goc), d)
    return {"so_muc": len(so), "nhan": {str(k): v for k, v in sorted(so.items())}, "da_ghi": ap_dung}


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _in_tinh_trang(t: Dict[str, Any]) -> None:
    if not t["do_duoc"]:
        print(f"⚪ {t['study']}: chưa có báo cáo kiểm máy API nào đọc được.")
        return
    for b in t["bao_cao"]:
        if b.get("hong"):
            print(f"⚠ {t['study']} · {b['ten']}: báo cáo {b['tep_bao_cao']} hỏng.")
            continue
        dau = {True: "🟠 CŨ", False: "🟢 còn hiệu lực", None: "⚪ chưa khẳng định"}[b["cu"]]
        tl = "chưa đo" if b["ty_le_dung"] is None else f"{b['ty_le_dung']:.0%}"
        print(
            f"{dau} · {t['study']} · {b['ten']} (lượt {b['luc']}): {b['ly_do']}. "
            f"Cần duyệt {b['can_duyet']}, chưa duyệt {b['chua_duyet']}, tỷ lệ đúng {tl}."
        )


def main(argv: Optional[Sequence[str]] = None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("tinh-trang", "phieu", "ghi", "do"))
    ap.add_argument("--study")
    ap.add_argument("--tat-ca", action="store_true", help="tinh-trang: mọi đề tài thật có kiem_may_api")
    ap.add_argument("--loi", help="ghi: NGUYÊN VĂN lời bác sĩ, vd «1-3 đúng, 4 sai, 5 không rõ»")
    ap.add_argument("--ap-dung", action="store_true", help="ghi: ghi nhãn thật (mặc định chạy khô)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.study and not _STUDY.match(a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    if a.lenh == "tinh-trang":
        if not (a.study or a.tat_ca):
            print("❌ cần --study hoặc --tat-ca")
            return 3
        tt = tinh_trang_tat_ca(goc) if a.tat_ca else [tinh_trang(a.study, goc)]
        if a.json:
            print(json.dumps(tt, ensure_ascii=False, indent=1))
        else:
            for t in tt or [{"study": "(không đề tài nào)", "do_duoc": False, "bao_cao": []}]:
                _in_tinh_trang(t)
        return ma_thoat(tt)
    if not a.study:
        print("❌ cần --study")
        return 3
    if a.lenh == "phieu":
        md, _, n = dung_phieu(a.study, goc)
        print(f"📝 Phiếu {n} mục: {md}" if n else f"🟢 Không có mục nào cần duyệt — phiếu: {md}")
        return 1 if n else 0
    if a.lenh == "ghi":
        if not a.loi:
            print("❌ ghi cần --loi \"<nguyên văn bác sĩ>\"")
            return 3
        try:
            kq = ghi_nhan(a.study, a.loi, a.ap_dung, goc)
        except ValueError as exc:
            print(f"❌ {exc}")
            return 3
        print(
            f"{'✅ Đã ghi' if kq['da_ghi'] else 'CHẠY KHÔ — sẽ ghi'} {kq['so_muc']} nhãn: "
            + ", ".join(f"{k}={v}" for k, v in kq["nhan"].items())
            + ("" if kq["da_ghi"] else ". Ghi thật: thêm --ap-dung.")
        )
        return 0
    t = tinh_trang(a.study, goc)
    if a.json:
        print(json.dumps(t["do_dung"], ensure_ascii=False, indent=1))
    elif not t["do_dung"]:
        print(f"⚪ {a.study}: chưa có mục kiểm máy nào để đo.")
    else:
        for khoa, n in t["do_dung"].items():
            tl = "chưa đo" if n["ty_le_dung"] is None else f"{n['ty_le_dung']:.0%}"
            print(
                f"{khoa}: đúng {n['dung']} · sai {n['sai']} · không rõ {n['khong_ro']} · "
                f"chưa duyệt {n['chua_duyet']} ⇒ tỷ lệ đúng {tl}"
            )
    return 2 if not t["do_dung"] else 0


if __name__ == "__main__":
    sys.exit(main())
