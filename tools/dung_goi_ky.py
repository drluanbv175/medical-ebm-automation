#!/usr/bin/env python3
"""dung_goi_ky.py — DỰNG GÓI KÝ cho đề tài thật: một lệnh chạy tuần tự đúng thứ tự khâu (23/11/2026).

VÌ SAO (bác sĩ duyệt 23/11/2026): trước lệnh này, chuẩn bị trình ký phải nhớ chạy riêng `buoc_dang_mo`, xuất Word đề
cương nộp, lắp G10, `kiem_de_cuong_nop_hoi_dong`, hai bộ dựng hồ sơ đơn vị, đối chiếu nhất quán, rồi tự ghép danh sách
chữ ký. Lệnh này nối các công cụ CÓ SẴN theo đúng thứ tự và áp NGUYÊN TẮC TỔNG (bác sĩ 22/11/2026): «chỉ được chuyển
sang bước tiếp theo khi bước hiện tại đã đạt chuẩn xác định trước» — khâu nào đỏ thì DỪNG ở khâu đó, báo đúng khâu và
chốt; không xuất gói ký trông như đủ.

CÁC KHÂU (đúng thứ tự):
  1. Khâu đang mở — `buoc_dang_mo.phan_tich`. Dừng khi không đo được, hoặc khâu cần hoàn thiện còn việc tại nguồn
     (chỉ đi tiếp khi khâu đó CHỈ chờ cổng trước khoá — các khoá đó nằm trong gói ký).
  2. Xuất Word đề cương nộp từ bản .md đã khoá — `sinh_de_cuong_nop_hoi_dong.xuat_word` (khuôn BVQY175 khi có).
     Làm TRƯỚC khi lắp G10: G10 ghi mã băm cặp .md/.docx của bản nộp vào manifest; xuất Word sau khi lắp làm manifest
     lệch bản nộp (G10 chấm REVIEW).
  3. Lắp lại G10 — `run_g10_assemble.py --study <mã>`: mã 0 hoặc 2 (dừng chờ chữ ký/dữ kiện đời thực) là đạt khâu;
     3 (đề cương chưa đạt guardrail) hoặc 1 (sập) ⇒ dừng.
  4. Kiểm đề cương nộp K1–K21 — `kiem_de_cuong_nop_hoi_dong.kiem`. Dòng K20 chỉ vì công thức biến phái sinh CHƯA DUYỆT
     /HẾT HIỆU LỰC (công thức hợp lệ, `bien_phai_sinh` không báo lỗi) là việc ký của thống kê viên ⇒ vào gói ký, không
     chặn; mọi lỗi K khác ⇒ dừng. K21 (sổ đọc): liệt kê đơn vị chưa có bản ghi đọc còn khớp mã băm; sổ đọc chưa phủ
     100% là điều kiện tiên quyết của chữ ký G10 (PI ký bản nộp) — chặn theo luật K21 khi đề cương ở trạng thái trình.
  5. Hồ sơ Hội đồng Đạo đức, đề tài cơ sở, phiếu đề xuất nhiệm vụ — `ho_so_hdd_bvqy175` / `ho_so_dtcs_bvqy175`
     (`trich --ghi --ghi-de` → `dung --ghi` → `kiem`), đọc khối `study_meta.ho_so_don_vi`. `kiem` khác 0 ⇒ dừng.
  6. Đối chiếu nhất quán 9 trường — `ho_so_nguon_chung.doi_chieu` (đề cương nộp ↔ gói G2 ↔ HĐĐĐ ↔ ĐTCS ↔ phiếu đề
     xuất). Lệch ⇒ dừng.
  7. Xuất MỘT gói ký đúng thứ tự cổng: mỗi chữ ký nêu vai, tài liệu kèm SHA-256, lệnh người ký tự chạy
     (`approve_gate.py`, `trinh_ky_cong.py`, `bien_phai_sinh.py duyet`, trường xác nhận ở study_meta), điều kiện tiên
     quyết và trạng thái (ký được ngay / chờ điều kiện); kèm chữ ký trên hồ sơ trình đơn vị.

RANH GIỚI: lệnh KHÔNG ký, KHÔNG ghi sổ cái, KHÔNG bật cờ xác nhận, KHÔNG sửa study_meta — chỉ chuẩn bị. Chạy khô mặc
định (khâu 2, 3, 5 chỉ in việc sẽ làm; khâu 1, 4, 6 đo trên tệp hiện có; gói ký chỉ in); `--ghi` mới ghi Word, G10,
hồ sơ và thư mục `exports/<mã>/goi_ky/`. Dừng ở khâu đỏ khi `--ghi` ⇒ ghi báo cáo dừng, dời gói ký cũ (nếu có) vào
`goi_ky/_cu/` để không ai dùng nhầm bản cũ. Đề tài đọc ở `exports/<mã>` của CHÍNH repo này (các công cụ con đều đọc gốc
repo của chúng) — chạy thử trên bản chép thì chép thư mục đề tài vào `exports/` của một worktree riêng.

Dùng:
    python3 tools/dung_goi_ky.py --study <mã>            # chạy khô
    python3 tools/dung_goi_ky.py --study <mã> --ghi      # dựng thật
    python3 tools/dung_goi_ky.py --study <mã> --json
Mã thoát: 0 đủ 7 khâu, gói ký đã dựng (chạy khô: đã in) · 1 dừng ở một khâu đỏ · 2 không đo được · 3 tham số sai.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):  # Windows cp1252 làm hỏng print() tiếng Việt — ép UTF-8
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
for _p in (str(BASE / "tools"), str(BASE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = "dung_goi_ky/v1"
THU_MUC_RA = "goi_ky"
_MA_DE_TAI = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
#: Cổng thuộc gói trình Hội đồng trước khi có dữ liệu (G10 mục đích ETHICS_SUBMISSION chỉ dựa G0–G4) — đúng thứ tự.
CONG_TRINH: Tuple[str, ...] = ("G0", "G1", "G2", "G3", "G4", "G10")
#: Cổng chỉ có sau triển khai (dữ liệu thật) — liệt kê để biết, không thuộc gói trình Hội đồng.
CONG_SAU_TRIEN_KHAI: Tuple[str, ...] = ("G5", "G6", "G7", "G8", "G9")
#: Bộ chấm của cổng thường có dấu vân tay nội dung (lệnh chốt đọc dấu hiện tại từ đây).
_BO_CHAM_CONG_THUONG = {"G0": "g0_quality_gate", "G1": "g1_quality_gate", "G3": "g3_quality_gate",
                        "G6": "g6_quality_gate", "G7": "g7_quality_gate"}
_DAU_TRONG_HANH_DONG = re.compile(r'dau_van_tay_chot\s*=\s*"?([0-9a-f]{16})"?')
_MA_PHEP_DO = re.compile(r"\b([A-Z]{2,}(?:-[A-Z0-9]+)+) \(")
#: Trạng thái công thức phái sinh chỉ cần NGƯỜI DUYỆT ghi lại (công thức hợp lệ) — việc ký, không phải việc sửa.
_PHAI_SINH_CHO_KY = ("CHUA_DUYET", "HET_HIEU_LUC", "SAI_DANG")
CAN_KIEM = "Cần bác sĩ kiểm chứng."


def _sha256(p: Path) -> Optional[str]:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


def _khau(so: int, ma: str, ten: str, chot: str, dat: Optional[bool], tom_tat: str,
          chi_tiet: Optional[List[str]] = None, du_lieu: Optional[Dict[str, Any]] = None,
          chay_kho: bool = False) -> Dict[str, Any]:
    """Kết quả một khâu. dat: True đạt · False đỏ (dừng) · None không đo được (dừng)."""
    return {"so": so, "ma": ma, "ten": ten, "chot": chot, "dat": dat, "tom_tat": tom_tat,
            "chi_tiet": list(chi_tiet or []), "du_lieu": du_lieu or {}, "chay_kho": chay_kho}


def _chay_main(ham: Callable[[List[str]], int], argv: List[str]) -> Tuple[int, str]:
    """Gọi main(argv) của một công cụ con trong cùng tiến trình, giữ lại toàn bộ đầu ra để đưa vào báo cáo."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            ma = ham(argv)
        except SystemExit as exc:  # argparse/công cụ con thoát bằng sys.exit
            ma = exc.code if isinstance(exc.code, int) else 1
    return int(ma or 0), buf.getvalue()


def _duoi(van: str, so_dong: int = 12) -> List[str]:
    return [d for d in van.strip().splitlines() if d.strip()][-so_dong:]


# ───────────────────────────────────────────────────────────────────────────── ngữ cảnh
class NguCanh:
    """Đề tài đang dựng: thư mục, chế độ ghi, kết quả các khâu đã chạy (khâu sau đọc kết quả khâu trước)."""

    def __init__(self, study: str, ghi: bool, goc: Path = BASE) -> None:
        self.study = study
        self.ghi = ghi
        self.goc = Path(goc)
        self.exports = self.goc / "exports"
        self.out_dir = self.exports / study
        self.kq: Dict[str, Dict[str, Any]] = {}

    def tep(self, ten: str) -> Path:
        return self.out_dir / ten.format(study=self.study)


# ───────────────────────────────────────────────────────────────────────────── khâu 1
def khau_buoc_dang_mo(ctx: NguCanh) -> Dict[str, Any]:
    import buoc_dang_mo as BDM  # noqa: PLC0415 — import lười (chấm sống mọi cổng)

    chot = "tools/buoc_dang_mo.py"
    try:
        kq = BDM.phan_tich(ctx.study, ctx.out_dir)
    except Exception as exc:  # noqa: BLE001 — không đo được ≠ đạt
        return _khau(1, "khau_dang_mo", "Khâu đang mở", chot, None, f"không đo được: {type(exc).__name__}: {exc}"[:300])
    if kq.get("ma_thoat") == 2:
        return _khau(1, "khau_dang_mo", "Khâu đang mở", chot, None, "không đo được: " + str(kq.get("ket_luan")),
                     du_lieu=kq)
    ht = kq.get("khau_can_hoan_thien")
    if ht:
        hang = next((c for c in kq.get("cong") or [] if c.get("gate") == ht), {})
        tom = hang.get("hoan_thien") or {}
        cho = tom.get("cho_cong_chua_khoa") or tom.get("cho_cong") or []
        cho_ky = {m.get("gate") for m in kq.get("danh_sach_khoa") or []}
        if tom.get("ket_luan") != "CHO_CONG_TRUOC" or not cho or not set(cho) <= cho_ky:
            viec = tom.get("viec_he_lam_tiep") or []
            return _khau(1, "khau_dang_mo", "Khâu đang mở", chot, False,
                         f"khâu cần hoàn thiện {ht} ({hang.get('status')}): {hang.get('ghi_chu')} — hoàn thiện tại "
                         "nguồn của khâu đó trước khi dựng gói ký", chi_tiet=viec, du_lieu=kq)
    khoa = [m.get("gate") for m in kq.get("danh_sach_khoa") or []]
    return _khau(1, "khau_dang_mo", "Khâu đang mở", chot, True,
                 f"khâu đang mở {kq.get('khau_dang_mo') or 'không có'}; khoá theo thứ tự: {', '.join(khoa) or '—'}"
                 + (f"; {ht} chỉ chờ cổng trước khoá" if ht else ""), du_lieu=kq)


# ───────────────────────────────────────────────────────────────────────────── khâu 2
def khau_xuat_word(ctx: NguCanh) -> Dict[str, Any]:
    chot = "tools/sinh_de_cuong_nop_hoi_dong.py::xuat_word"
    md_p = ctx.tep("DE_CUONG_NOP_HOI_DONG_{study}.md")
    if not md_p.is_file():
        return _khau(2, "xuat_word", "Xuất Word đề cương nộp", chot, False, f"chưa có {md_p.name}")
    if not ctx.ghi:
        return _khau(2, "xuat_word", "Xuất Word đề cương nộp", chot, True,
                     f"chạy khô — sẽ xuất {md_p.with_suffix('.docx').name} từ {md_p.name}", chay_kho=True)
    import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: PLC0415

    try:
        ra = SDC.xuat_word(ctx.out_dir, ctx.study, md_p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return _khau(2, "xuat_word", "Xuất Word đề cương nộp", chot, False, f"xuất Word lỗi: {type(exc).__name__}: "
                     f"{exc}"[:300])
    docx_p = Path(ra) if ra else md_p.with_suffix(".docx")
    if not ra or not docx_p.is_file() or docx_p.stat().st_size == 0:
        return _khau(2, "xuat_word", "Xuất Word đề cương nộp", chot, False, "không xuất được Word (thiếu python-docx?)")
    return _khau(2, "xuat_word", "Xuất Word đề cương nộp", chot, True, f"đã xuất {docx_p.name}",
                 du_lieu={"md": md_p.name, "md_sha256": _sha256(md_p), "docx": docx_p.name,
                          "docx_sha256": _sha256(docx_p)})


# ───────────────────────────────────────────────────────────────────────────── khâu 3
def _chay_lap_g10(ctx: NguCanh) -> Tuple[int, str]:
    r = subprocess.run([sys.executable, "-B", str(BASE / "tools" / "run_g10_assemble.py"), "--study", ctx.study],
                       cwd=str(BASE), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def khau_lap_g10(ctx: NguCanh, chay: Optional[Callable[[NguCanh], Tuple[int, str]]] = None) -> Dict[str, Any]:
    chot = "tools/run_g10_assemble.py"
    if not ctx.ghi:
        return _khau(3, "lap_g10", "Lắp lại G10", chot, True, f"chạy khô — sẽ chạy {chot} --study {ctx.study}",
                     chay_kho=True)
    ma, van = (chay or _chay_lap_g10)(ctx)
    duoi = _duoi(van)
    if ma in (0, 2):
        return _khau(3, "lap_g10", "Lắp lại G10", chot, True,
                     "đã lắp; " + ("G10 đạt/khoá" if ma == 0 else "G10 dừng chờ chữ ký/dữ kiện đời thực (vào gói ký)"),
                     chi_tiet=duoi, du_lieu={"ma_thoat": ma})
    ly = "đề cương chưa đạt guardrail (mã 3)" if ma == 3 else f"lắp G10 lỗi (mã {ma})"
    return _khau(3, "lap_g10", "Lắp lại G10", chot, False, ly, chi_tiet=duoi, du_lieu={"ma_thoat": ma})


# ───────────────────────────────────────────────────────────────────────────── khâu 4
def phai_sinh_cho_ky(out_dir: Path, study: str) -> Dict[str, Any]:
    """Công thức biến phái sinh: {'loi': {...}, 'cho_ky': [{bien, trang_thai, dau}], 'tep', 'sha256'} — 'cho_ky' chỉ
    gồm biến công thức HỢP LỆ mà dòng duyệt thiếu/hết hiệu lực/sai dạng (việc ký của thống kê viên/PI)."""
    import bien_phai_sinh as BPS  # noqa: PLC0415

    tep = Path(out_dir) / BPS.TEP_DAC_TA
    if not tep.is_file():
        return {"co_tep": False, "loi": {}, "cho_ky": [], "tep": tep.name, "sha256": None}
    bien = BPS.doc_dac_ta(out_dir)
    kq = BPS.kiem_dac_ta(bien, BPS.doc_danh_muc_tu_dien(out_dir, study))
    cho, da = [], set()
    for b in bien:
        tt = kq.trang_thai[b.ten]
        if tt in _PHAI_SINH_CHO_KY and b.goc not in da:
            da.add(b.goc)
            cho.append({"bien": b.goc, "trang_thai": tt, "dau_cong_thuc": b.dau})
    return {"co_tep": True, "loi": dict(kq.loi), "cho_ky": cho, "tep": tep.name, "sha256": _sha256(tep)}


def _la_dong_phai_sinh(dong: str) -> bool:
    """Dòng K20 mà MỌI phép đo đỏ trong đó là DC-PHAI-SINH."""
    ma = _MA_PHEP_DO.findall(dong)
    return dong.startswith("K20") and bool(ma) and set(ma) == {"DC-PHAI-SINH"}


def khau_kiem_de_cuong(ctx: NguCanh) -> Dict[str, Any]:
    import kiem_de_cuong_nop_hoi_dong as K  # noqa: PLC0415
    import so_doc_de_cuong as SDD  # noqa: PLC0415

    chot = "tools/kiem_de_cuong_nop_hoi_dong.py (K1–K21) + tools/so_doc_de_cuong.py"
    try:
        loi = K.kiem(ctx.out_dir, ctx.study)
        canh = K.canh_bao_k20_k21(ctx.out_dir, ctx.study) + K.canh_bao_k17(ctx.out_dir, ctx.study)
        ps = phai_sinh_cho_ky(ctx.out_dir, ctx.study)
        sd = SDD.trang_thai(ctx.out_dir, ctx.study)
    except Exception as exc:  # noqa: BLE001
        return _khau(4, "kiem_de_cuong", "Kiểm đề cương nộp", chot, None, f"không đo được: {type(exc).__name__}: "
                     f"{exc}"[:300])
    chuyen_ky = [d for d in loi if _la_dong_phai_sinh(d) and not ps["loi"] and ps["cho_ky"]]
    con = [d for d in loi if d not in chuyen_ky]
    so_doc = {"tong": sd.get("tong", 0), "da_doc": sd.get("da_doc", 0), "chua_doc": sd.get("chua_doc", 0),
              "doi_sau_doc": sd.get("doi_sau_doc", 0), "can_sua": sd.get("can_sua", 0),
              "theo_loai_chua_doc": {}, "ds_chua_doc": [x.get("ma") for x in sd.get("ds_chua_doc") or []],
              "ds_can_sua": [x.get("ma") for x in sd.get("ds_can_sua") or []]}
    for x in sd.get("ds_chua_doc") or []:
        so_doc["theo_loai_chua_doc"][x.get("loai")] = so_doc["theo_loai_chua_doc"].get(x.get("loai"), 0) + 1
    du = {"loi_chan": con, "loi_chuyen_goi_ky": chuyen_ky, "canh_bao": canh, "phai_sinh": ps, "so_doc": so_doc}
    tom_doc = f"sổ đọc phủ {so_doc['da_doc']}/{so_doc['tong']} đơn vị"
    if con:
        return _khau(4, "kiem_de_cuong", "Kiểm đề cương nộp", chot, False,
                     f"{len(con)} lỗi K chưa đạt — sửa tại nguồn của khâu báo lỗi; {tom_doc}", chi_tiet=con, du_lieu=du)
    them = f"; {len(chuyen_ky)} dòng K20 là duyệt công thức phái sinh — vào gói ký" if chuyen_ky else ""
    return _khau(4, "kiem_de_cuong", "Kiểm đề cương nộp", chot, True, f"K1–K21 không còn lỗi chặn{them}; {tom_doc}",
                 chi_tiet=canh, du_lieu=du)


# ───────────────────────────────────────────────────────────────────────────── khâu 5
def _bo_dung(ten: str) -> Tuple[Any, str]:
    if ten == "hdd":
        import ho_so_hdd_bvqy175 as M  # noqa: PLC0415
        return M, "ho_so_hdd/HO_SO_HDD_BVQY175.json"
    import ho_so_dtcs_bvqy175 as M  # noqa: PLC0415
    return M, "ho_so_dtcs/HO_SO_DTCS_BVQY175.json"


def khau_ho_so(ctx: NguCanh) -> Dict[str, Any]:
    chot = "tools/ho_so_hdd_bvqy175.py · tools/ho_so_dtcs_bvqy175.py (trich → dung → kiem)"
    goc = ["--study", ctx.study, "--exports-root", str(ctx.exports)]
    nhat_ky: Dict[str, List[str]] = {}
    hong: List[str] = []
    for ten, nhan in (("hdd", "hồ sơ Hội đồng Đạo đức"), ("dtcs", "hồ sơ đề tài cơ sở + phiếu đề xuất")):
        M, tep_json = _bo_dung(ten)
        if ctx.ghi:
            ma, van = _chay_main(M.main, ["trich", *goc, "--ghi", "--ghi-de"])
            nhat_ky[f"{ten}_trich"] = _duoi(van, 6)
            if ma != 0:
                hong.append(f"{nhan}: trich mã {ma}")
                continue
            dung = ["dung", *goc, "--ghi"]
            if ten == "hdd":
                qt = (_doc_json(ctx.out_dir / tep_json).get("meta") or {}).get("quy_trinh")
                if qt not in ("rut_gon", "day_du", "ca_hai"):
                    hong.append(f"{nhan}: khối ho_so_don_vi.hdd chưa khai meta.quy_trinh (rut_gon/day_du/ca_hai)")
                    continue
                dung += ["--quy-trinh", qt]
            ma, van = _chay_main(M.main, dung)
            nhat_ky[f"{ten}_dung"] = _duoi(van, 8)
            if ma != 0:
                hong.append(f"{nhan}: dung mã {ma} — " + " | ".join(_duoi(van, 3)))
                continue
        ma, van = _chay_main(M.main, ["kiem", *goc])
        nhat_ky[f"{ten}_kiem"] = _duoi(van, 14)
        if ma != 0:
            hong.append(f"{nhan}: kiem mã {ma} — " + " | ".join(_duoi(van, 4)))
    if hong:
        return _khau(5, "ho_so", "Hồ sơ HĐĐĐ / ĐTCS / phiếu đề xuất", chot, False, "; ".join(hong)[:600],
                     chi_tiet=hong, du_lieu={"nhat_ky": nhat_ky}, chay_kho=not ctx.ghi)
    return _khau(5, "ho_so", "Hồ sơ HĐĐĐ / ĐTCS / phiếu đề xuất", chot, True,
                 ("chạy khô — kiem trên bản hiện có sạch" if not ctx.ghi else "đã dựng; kiem sạch cả hai bộ"),
                 du_lieu={"nhat_ky": nhat_ky}, chay_kho=not ctx.ghi)


# ───────────────────────────────────────────────────────────────────────────── khâu 6
def khau_doi_chieu(ctx: NguCanh) -> Dict[str, Any]:
    import ho_so_nguon_chung as HSC  # noqa: PLC0415

    chot = "tools/ho_so_nguon_chung.py::doi_chieu (9 trường)"
    hdd = _doc_json(ctx.out_dir / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json") or None
    dtcs = _doc_json(ctx.out_dir / "ho_so_dtcs" / "HO_SO_DTCS_BVQY175.json") or None
    if hdd is None or dtcs is None:
        return _khau(6, "doi_chieu", "Đối chiếu nhất quán", chot, None, "chưa có JSON hồ sơ HĐĐĐ/ĐTCS để đối chiếu")
    try:
        dc = HSC.doi_chieu(HSC.NguonDeTai(ctx.exports, ctx.study), hdd, dtcs)
    except Exception as exc:  # noqa: BLE001
        return _khau(6, "doi_chieu", "Đối chiếu nhất quán", chot, None, f"không đo được: {type(exc).__name__}")
    khop, lech, khong_do = HSC.tom_tat_doi_chieu(dc)
    lech_ds = [f"{x['truong']} — {x['tai_lieu']}: {x.get('chi_tiet') or ''}"[:200] for x in dc if x["ket"] == "lech"]
    du = {"khop": khop, "lech": lech, "khong_do_duoc": khong_do, "ds_lech": lech_ds}
    if lech:
        return _khau(6, "doi_chieu", "Đối chiếu nhất quán", chot, False, f"{lech} chỗ lệch — sửa tại nguồn chung",
                     chi_tiet=lech_ds, du_lieu=du)
    return _khau(6, "doi_chieu", "Đối chiếu nhất quán", chot, True,
                 f"khớp {khop}, lệch 0, không đo được {khong_do}", du_lieu=du)


# ───────────────────────────────────────────────────────────────────────────── khâu 7 — gói ký
def tai_lieu_cong(out_dir: Path, study: str, gate: str) -> List[Dict[str, Any]]:
    """Tài liệu của cổng kèm SHA-256 — đúng tệp người ký đọc (artifact `<G>_A*`, checkpoint, bản nộp với G10)."""
    out_dir = Path(out_dir)
    tep = sorted(p for p in out_dir.glob(f"{gate}_A*") if p.suffix in (".md", ".docx") and p.is_file()
                 and not p.name.startswith(f"{gate}0"))  # «G1_A…» không khớp «G10_A…»
    cp = out_dir / f"{gate}_checkpoint.json"
    if cp.is_file():
        tep.append(cp)
    if gate == "G10":
        for ten in ("DE_CUONG_NOP_HOI_DONG_{s}.md", "DE_CUONG_NOP_HOI_DONG_{s}.docx", "DE_CUONG_THONG_NHAT_{s}.md",
                    "DE_CUONG_THONG_NHAT_{s}.docx"):
            p = out_dir / ten.format(s=study)
            if p.is_file():
                tep.append(p)
    return [{"tep": p.name, "sha256": _sha256(p)} for p in tep]


def _artifact_ky(gate: str, study: str) -> str:
    """Tệp đại diện mà approve_gate.py đòi cho cổng cứng (lấy tên từ chính bộ chấm — một nguồn sự thật)."""
    if gate == "G2":
        return f"G2_A3_ETHICS_PACKAGE_{study}.md"
    if gate == "G4":
        import g4_quality_gate as G4Q  # noqa: PLC0415
        return G4Q.sap_artifact_name(study)
    if gate == "G5":
        return "G5_checkpoint.json"
    if gate == "G8":
        import g8_quality_gate as G8Q  # noqa: PLC0415
        return G8Q.presubmission_artifact_name(study)
    if gate == "G9":
        import g9_quality_gate as G9Q  # noqa: PLC0415
        return G9Q.CHECKPOINT_JSON
    import g10_quality_gate as G10Q  # noqa: PLC0415
    return G10Q.CHECKPOINT_JSON


def _cham_cong_thuong(gate: str, study: str, out_dir: Path) -> Dict[str, Any]:
    """(dấu nội dung hiện tại, mục người chưa đạt kèm hành động) của một cổng thường — chấm write=False."""
    ten = _BO_CHAM_CONG_THUONG.get(gate)
    if not ten:
        return {"dau": None, "muc": []}
    try:
        mod = __import__(ten)
        kq = mod.evaluate_study(study, out_dir, write=False)
    except Exception as exc:  # noqa: BLE001
        return {"dau": None, "muc": [], "loi": f"{type(exc).__name__}: {str(exc)[:120]}"}
    muc = [c for c in kq.get("human_criteria") or [] if c.get("status") != "PASS"]
    dau = kq.get("dau_van_tay_hien_tai")
    if not dau:
        for c in muc:
            m = _DAU_TRONG_HANH_DONG.search(str(c.get("action") or ""))
            if m:
                dau = m.group(1)
                break
    return {"dau": dau, "muc": [{"id": c.get("id"), "label": c.get("label"), "action": c.get("action")} for c in muc]}


def _vai_cong_thuong(gate: str, study: str, out_dir: Path) -> List[str]:
    """Vai chốt cổng thường theo bảng trách nhiệm (`hoi_dong_cong.trach_nhiem`, mục dành cho người) — chỉ đọc."""
    try:
        import hoi_dong_cong as HD  # noqa: PLC0415

        bang = HD.trach_nhiem(study, gate, out_dir)
    except Exception:  # noqa: BLE001 — không đo được ⇒ ghi rõ, không đoán vai
        return ["vai chốt cổng — chưa đo được bảng trách nhiệm"]
    vai: List[str] = []
    for m in (bang or {}).get("cho_nguoi") or []:
        v = str(m.get("vai") or "").strip()
        if v and v not in vai:
            vai.append(v)
    return vai or ["vai chốt cổng — bảng trách nhiệm không ghi mục cho người"]


def _vai_ky(gate: str) -> List[str]:
    import gate_contract as GC  # noqa: PLC0415
    return list(GC._GATE_REQUIRED_STAKEHOLDERS.get(gate) or ())


def _lenh_cong_cung(gate: str, study: str) -> List[str]:
    if gate == "G2":
        return [f"python3 tools/trinh_ky_cong.py --study {study} --gate G2   # người duyệt (IRB) tự chạy: thẩm tra, "
                "phỏng vấn đủ trường G2 (số và ngày quyết định chấp thuận…) rồi soạn lệnh approve_gate.py"]
    art = _artifact_ky(gate, study)
    return [f"python3 tools/approve_gate.py --study {study} --gate {gate} --artifact exports/{study}/{art} "
            f"--reviewer-role {vai} --reviewer-ref <MÃ_THAM_CHIẾU_KHÔNG_PII>" for vai in _vai_ky(gate)]


def lap_goi_ky(ctx: NguCanh) -> Dict[str, Any]:
    """Gói ký đúng thứ tự cổng từ kết quả khâu 1–6 (chỉ đọc)."""
    bdm = ctx.kq["khau_dang_mo"]["du_lieu"]
    kd = (ctx.kq.get("kiem_de_cuong") or {}).get("du_lieu") or {}
    hang = {c["gate"]: c for c in bdm.get("cong") or []}
    cho_ky = {m["gate"]: m for m in bdm.get("danh_sach_khoa") or []}
    chua_khoa = [g for g in hang if not hang[g].get("da_khoa")]
    muc: List[Dict[str, Any]] = []

    import g10_quality_gate as G10Q  # noqa: PLC0415

    muc_dich = G10Q.muc_dich_phat_hanh(_doc_json(ctx.out_dir / G10Q.READINESS_JSON))
    truoc_du_lieu = muc_dich in G10Q.MUC_DICH_TRUOC_DU_LIEU

    def dieu_kien_truoc(gate: str) -> List[str]:
        """Cổng trước phải khoá. G10 trình Hội đồng trước dữ liệu (ETHICS_SUBMISSION/REGISTRY_UPDATE) chỉ dựa G0–G4,
        trong đó G2/G4 chỉ cần sẵn sàng (READY) — đúng luật g10_quality_gate theo mục đích phát hành."""
        so = int(gate[1:])
        ra = []
        for g in chua_khoa:
            if int(g[1:]) >= so:
                continue
            if gate == "G10" and truoc_du_lieu:
                if int(g[1:]) > 4:
                    continue
                if g in ("G2", "G4"):
                    if str((hang.get(g) or {}).get("muc") or "").upper() != "READY":
                        ra.append(f"{g} sẵn sàng (READY) hoặc đã khoá")
                    continue
            ra.append(f"{g} khoá trước")
        return ra

    for gate in CONG_TRINH:
        r = hang.get(gate) or {}
        if r.get("da_khoa"):
            continue
        cung = gate in ("G2", "G4", "G10")
        dk = dieu_kien_truoc(gate)
        san = gate in cho_ky
        if not san:
            dk.append(f"{gate} đạt bước ký (hiện {r.get('status') or 'chưa chạy'})")
        if gate == "G2":
            dk.append("có quyết định chấp thuận của Hội đồng Đạo đức (số, ngày) — nhập khi ký")
        if gate == "G10":
            sd = kd.get("so_doc") or {}
            if sd.get("tong") and sd.get("da_doc", 0) < sd["tong"]:
                dk.append(f"sổ đọc đề cương nộp phủ 100% bản hiện hành (hiện {sd.get('da_doc', 0)}/{sd['tong']}; "
                          "tools/so_doc_de_cuong.py ghi)")
        item: Dict[str, Any] = {"gate": gate, "loai": "ky_so_cai" if cung else "chot_cong",
                                "trang_thai_cong": r.get("status"), "tai_lieu": tai_lieu_cong(ctx.out_dir, ctx.study,
                                                                                               gate),
                                "dieu_kien": dk, "ky_duoc_ngay": not dk}
        if cung:
            item["vai"] = _vai_ky(gate)
            item["lenh"] = _lenh_cong_cung(gate, ctx.study)
            if gate == "G10":
                item["muc_dich"] = muc_dich or "chưa chọn"
        else:
            cham = _cham_cong_thuong(gate, ctx.study, ctx.out_dir)
            item["vai"] = (cho_ky.get(gate) or {}).get("vai") or _vai_cong_thuong(gate, ctx.study, ctx.out_dir)
            item["dau_noi_dung"] = cham.get("dau")
            item["muc_chua_dat"] = cham.get("muc")
            item["lenh"] = [f"ghi ở exports/{ctx.study}/study_meta.json → gate_params.{gate} theo hành động của từng "
                            "mục chưa đạt dưới đây (vai, thời điểm ISO-8601, dau_van_tay_chot = dấu nội dung hiện "
                            "tại), "
                            f"rồi kiểm: python3 tools/{_BO_CHAM_CONG_THUONG.get(gate, 'gN_quality_gate')}.py --study "
                            f"{ctx.study} (kỳ vọng PASS)"]
        muc.append(item)
        if gate == "G3":
            ps = kd.get("phai_sinh") or {}
            if ps.get("cho_ky") and not ps.get("loi"):
                bien = ",".join(x["bien"] for x in ps["cho_ky"])
                muc.append({"gate": "G3", "loai": "duyet_cong_thuc_phai_sinh", "vai": ["THONG_KE_VIEN"],
                            "bien": ps["cho_ky"], "tai_lieu": [{"tep": ps["tep"], "sha256": ps["sha256"]}],
                            "lenh": [f"python3 tools/bien_phai_sinh.py duyet --study {ctx.study} --vai THONG_KE_VIEN "
                                     f"--tham-chieu <MÃ_NGƯỜI_DUYỆT> --bien {bien}   # chạy khô để xem, thêm --ap-dung "
                                     "để ghi"],
                            "dieu_kien": [], "ky_duoc_ngay": True,
                            "ghi_chu": "công thức hợp lệ (bien_phai_sinh kiem không báo lỗi); dòng duyệt ghi kèm dấu "
                                       "công thức hiện tại"})
    # sắp đúng thứ tự cổng (G0…G4, G10); trong G3, duyệt công thức trước chốt cổng
    muc.sort(key=lambda m: (int(m["gate"][1:]), 0 if m["loai"] == "duyet_cong_thuc_phai_sinh" else 1))
    for i, m in enumerate(muc, 1):
        m["thu_tu"] = i
    ho_so = []
    for nhan, thu_muc, tep_json in (("Hồ sơ Hội đồng Đạo đức", "ho_so_hdd", "HO_SO_HDD_BVQY175.json"),
                                    ("Hồ sơ đề tài cơ sở và phiếu đề xuất nhiệm vụ", "ho_so_dtcs",
                                     "HO_SO_DTCS_BVQY175.json")):
        d = _doc_json(ctx.out_dir / thu_muc / tep_json)
        word = sorted(ctx.out_dir.joinpath(thu_muc).glob("*.docx")) if ctx.out_dir.joinpath(thu_muc).is_dir() else []
        ho_so.append({"ho_so": nhan, "chu_ky": [str(x) for x in d.get("goi_ky") or []],
                      "tai_lieu": [{"tep": f"{thu_muc}/{p.name}", "sha256": _sha256(p)} for p in word]})
    sau = [{"gate": g, "vai": _vai_ky(g) or ["chốt cổng thường"], "trang_thai_cong": (hang.get(g) or {}).get("status")}
           for g in CONG_SAU_TRIEN_KHAI if not (hang.get(g) or {}).get("da_khoa")]
    return {"schema": SCHEMA, "study": ctx.study, "ngay_dung": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "da_khoa": [g for g in hang if hang[g].get("da_khoa")], "muc": muc, "ho_so_don_vi": ho_so,
            "sau_trien_khai": sau, "khau": [_rut_khau(k) for k in ctx.kq.values()],
            "ranh_gioi": "Lệnh dựng gói ký không ký, không ghi sổ cái, không bật cờ xác nhận — chỉ chuẩn bị."}


def _rut_khau(k: Dict[str, Any]) -> Dict[str, Any]:
    return {x: k.get(x) for x in ("so", "ma", "ten", "chot", "dat", "tom_tat", "chay_kho")}


def goi_ky_md(g: Dict[str, Any]) -> str:
    nhan_loai = {"chot_cong": "Chốt cổng", "ky_so_cai": "Ký sổ cái (cổng cứng)",
                 "duyet_cong_thuc_phai_sinh": "Duyệt công thức biến phái sinh"}
    d = [f"# Gói ký — {g['study']}", "",
         f"Dựng lúc {g['ngay_dung']} bằng `tools/dung_goi_ky.py`. {g['ranh_gioi']}", "",
         "## Kết quả các khâu", "", "| Khâu | Kết quả | Chốt |", "|---|---|---|"]
    d += [f"| {k['so']}. {k['ten']} | {'✓' if k['dat'] else '✗'} {k['tom_tat']} | `{k['chot']}` |" for k in g["khau"]]
    d += ["", f"Cổng đã khoá: {', '.join(g['da_khoa']) or '—'}.", "",
          "## Chữ ký và chốt theo đúng thứ tự cổng", ""]
    for m in g["muc"]:
        trang = "KÝ ĐƯỢC NGAY" if m["ky_duoc_ngay"] else "CHỜ ĐIỀU KIỆN"
        d += [f"### {m['thu_tu']}. {m['gate']} — {nhan_loai[m['loai']]} — {trang}", "",
              f"- Vai: {', '.join(m.get('vai') or [])}"]
        if m.get("trang_thai_cong"):
            d.append(f"- Trạng thái cổng hiện tại: `{m['trang_thai_cong']}`")
        if m.get("muc_dich"):
            d.append(f"- Mục đích phát hành G10: `{m['muc_dich']}`")
        if m.get("dau_noi_dung"):
            d.append(f"- Dấu nội dung hiện tại (gắn vào xác nhận): `{m['dau_noi_dung']}`")
        for x in m.get("muc_chua_dat") or []:
            d.append(f"- Mục chưa đạt {x['id']} — {x['label']}: {x['action']}")
        for x in m.get("bien") or []:
            d.append(f"- Biến `{x['bien']}`: {x['trang_thai']}, dấu công thức hiện tại `{x['dau_cong_thuc']}`")
        if m.get("ghi_chu"):
            d.append(f"- Ghi chú: {m['ghi_chu']}")
        d += ["- Tài liệu:", "", "  | Tệp | SHA-256 |", "  |---|---|"]
        d += [f"  | `{t['tep']}` | `{t['sha256']}` |" for t in m.get("tai_lieu") or []] or ["  | — | — |"]
        d += ["", "- Lệnh/thao tác người ký tự chạy:", ""] + [f"  - `{x}`" for x in m.get("lenh") or []]
        d += ["", "- Điều kiện tiên quyết: " + ("; ".join(m["dieu_kien"]) if m["dieu_kien"] else "đã đủ"), ""]
    d += ["## Chữ ký trên hồ sơ trình đơn vị (in và ký)", ""]
    for h in g["ho_so_don_vi"]:
        d += [f"### {h['ho_so']}", ""]
        d += [f"{i}. {x}" for i, x in enumerate(h["chu_ky"], 1)] or ["- (chưa có danh mục chữ ký)"]
        d += ["", "| Tệp | SHA-256 |", "|---|---|"]
        d += [f"| `{t['tep']}` | `{t['sha256']}` |" for t in h["tai_lieu"]] or ["| — | — |"]
        d.append("")
    if g["sau_trien_khai"]:
        d += ["## Sau triển khai (không thuộc gói trình Hội đồng)", ""]
        d += [f"- {x['gate']}: vai {', '.join(x['vai'])} — hiện `{x['trang_thai_cong']}`" for x in g["sau_trien_khai"]]
        d.append("")
    d.append(CAN_KIEM)
    return "\n".join(d) + "\n"


def bao_cao_dung_md(study: str, khau: List[Dict[str, Any]]) -> str:
    dung = khau[-1]
    d = [f"# Dựng gói ký — {study}: DỪNG ở khâu {dung['so']} ({dung['ten']})", "",
         f"- Chốt: `{dung['chot']}`", f"- Kết quả: {dung['tom_tat']}", ""]
    d += [f"  - {x}" for x in dung["chi_tiet"][:40]]
    d += ["", "Nguyên tắc: chỉ chuyển sang bước tiếp theo khi bước hiện tại đã đạt chuẩn xác định trước — sửa tại "
          "nguồn của khâu báo lỗi, kiểm bằng chốt của chính nó, rồi chạy lại lệnh này. Chưa xuất gói ký.", "",
          "## Các khâu đã chạy", ""]
    d += [f"- {k['so']}. {k['ten']}: {'✓' if k['dat'] else ('✗' if k['dat'] is False else '⚪ không đo được')} "
          f"{k['tom_tat']}" for k in khau]
    return "\n".join(d + ["", CAN_KIEM]) + "\n"


def _ghi(p: Path, van: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    tam.write_text(van, encoding="utf-8", newline="\n")
    tam.replace(p)


def _doi_goi_cu(ra: Path, study: str) -> List[str]:
    """Dời gói ký cũ vào goi_ky/_cu/<giờ>/ (không xoá) khi lượt mới dừng ở khâu đỏ."""
    cu = [p for p in ra.glob(f"GOI_KY_{study}.*") if p.is_file()]
    if not cu:
        return []
    dich = ra / "_cu" / datetime.now().strftime("%Y%m%d-%H%M%S")
    dich.mkdir(parents=True, exist_ok=True)
    for p in cu:
        shutil.move(str(p), str(dich / p.name))
    return [p.name for p in cu]


def ghi_goi_ky(ctx: NguCanh, goi: Dict[str, Any]) -> List[str]:
    ra = ctx.out_dir / THU_MUC_RA
    md = goi_ky_md(goi)
    _ghi(ra / f"GOI_KY_{ctx.study}.json", json.dumps(goi, ensure_ascii=False, indent=1) + "\n")
    _ghi(ra / f"GOI_KY_{ctx.study}.md", md)
    tep = [f"GOI_KY_{ctx.study}.json", f"GOI_KY_{ctx.study}.md"]
    try:
        import md2docx_vn  # noqa: PLC0415

        md2docx_vn.markdown_to_docx(md, ra / f"GOI_KY_{ctx.study}.docx")
        tep.append(f"GOI_KY_{ctx.study}.docx")
    except Exception:  # noqa: BLE001 — thiếu python-docx ⇒ vẫn có .md/.json
        pass
    bao = ra / f"DUNG_GOI_KY_{ctx.study}.md"
    if bao.is_file():  # lượt này đủ 7 khâu ⇒ báo cáo dừng của lượt trước hết hiệu lực
        (ra / "_cu").mkdir(parents=True, exist_ok=True)
        shutil.move(str(bao), str(ra / "_cu" / f"{bao.stem}.{datetime.now():%Y%m%d-%H%M%S}.md"))
    return tep


# ───────────────────────────────────────────────────────────────────────────── chạy chuỗi
KHAU: List[Tuple[str, Callable[[NguCanh], Dict[str, Any]]]] = [
    ("khau_dang_mo", khau_buoc_dang_mo),
    ("xuat_word", khau_xuat_word),
    ("lap_g10", khau_lap_g10),
    ("kiem_de_cuong", khau_kiem_de_cuong),
    ("ho_so", khau_ho_so),
    ("doi_chieu", khau_doi_chieu),
]


def chay(ctx: NguCanh, khau: Optional[List[Tuple[str, Callable[[NguCanh], Dict[str, Any]]]]] = None) -> Dict[str, Any]:
    """Chạy tuần tự; dừng ở khâu đầu tiên không đạt. Trả {ma_thoat, khau, goi_ky?, tep_ghi}."""
    for ma, ham in (khau or KHAU):
        k = ham(ctx)
        ctx.kq[ma] = k
        if k["dat"] is not True:
            ds = list(ctx.kq.values())
            tep: List[str] = []
            if ctx.ghi:
                ra = ctx.out_dir / THU_MUC_RA
                da_doi = _doi_goi_cu(ra, ctx.study)
                _ghi(ra / f"DUNG_GOI_KY_{ctx.study}.json",
                     json.dumps({"schema": SCHEMA, "study": ctx.study, "dung_o_khau": k["so"], "khau": ds,
                                 "goi_ky_cu_da_doi": da_doi}, ensure_ascii=False, indent=1, default=str) + "\n")
                _ghi(ra / f"DUNG_GOI_KY_{ctx.study}.md", bao_cao_dung_md(ctx.study, ds))
                tep = [f"DUNG_GOI_KY_{ctx.study}.json", f"DUNG_GOI_KY_{ctx.study}.md"]
            return {"ma_thoat": 2 if k["dat"] is None else 1, "khau": ds, "goi_ky": None, "tep_ghi": tep}
    goi = lap_goi_ky(ctx)
    ctx.kq["goi_ky"] = _khau(7, "goi_ky", "Xuất gói ký", "tools/dung_goi_ky.py::lap_goi_ky", True,
                             f"{len(goi['muc'])} mục ký/chốt theo thứ tự cổng", chay_kho=not ctx.ghi)
    goi["khau"] = [_rut_khau(k) for k in ctx.kq.values()]
    tep = ghi_goi_ky(ctx, goi) if ctx.ghi else []
    return {"ma_thoat": 0, "khau": list(ctx.kq.values()), "goi_ky": goi, "tep_ghi": tep}


def in_ket_qua(kq: Dict[str, Any], study: str, ghi: bool) -> str:
    d = [f"DỰNG GÓI KÝ — {study} ({'ghi' if ghi else 'chạy khô'})"]
    for k in kq["khau"]:
        dau = "✓" if k["dat"] else ("✗" if k["dat"] is False else "⚪")
        d.append(f"  {k['so']}. {k['ten']}: {dau} {k['tom_tat']}")
        if k["dat"] is not True:
            d += [f"       · {x}" for x in k["chi_tiet"][:12]]
    if kq["goi_ky"]:
        d.append("GÓI KÝ — theo thứ tự cổng:")
        for m in kq["goi_ky"]["muc"]:
            d.append(f"  {m['thu_tu']}. {m['gate']} {m['loai']} · vai {', '.join(m.get('vai') or [])} · "
                     + ("ký được ngay" if m["ky_duoc_ngay"] else "chờ: " + "; ".join(m["dieu_kien"])))
    else:
        d.append("Chưa xuất gói ký — sửa tại nguồn của khâu dừng, kiểm bằng chốt của nó, rồi chạy lại.")
    if kq["tep_ghi"]:
        d.append("Đã ghi: " + ", ".join(f"exports/{study}/{THU_MUC_RA}/{t}" for t in kq["tep_ghi"]))
    d.append(CAN_KIEM)
    return "\n".join(d)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Dựng gói ký cho đề tài thật — chạy tuần tự đúng thứ tự khâu.")
    ap.add_argument("--study", required=True)
    ap.add_argument("--ghi", action="store_true", help="ghi Word, G10, hồ sơ và gói ký (mặc định chạy khô)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not _MA_DE_TAI.match(a.study) or not (BASE / "exports" / a.study).is_dir():
        print(f"Tham số sai: không có thư mục exports/{a.study} trong {BASE}")
        return 3
    ctx = NguCanh(a.study, a.ghi)
    kq = chay(ctx)
    if a.json:
        print(json.dumps({**kq, "khau": [_rut_khau(k) for k in kq["khau"]]}, ensure_ascii=False, indent=1,
                         default=str))
    else:
        print(in_ket_qua(kq, a.study, a.ghi))
    return kq["ma_thoat"]


if __name__ == "__main__":
    raise SystemExit(main())
