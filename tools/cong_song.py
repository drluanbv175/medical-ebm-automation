#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG SỐNG — hạ tầng dùng chung để cổng sau ĐỌC ĐÚNG cổng trước (soát từng cổng G0–G10, 04/10/2026).

VÌ SAO CÓ. Rà soát 11 cổng (mỗi cổng một agent độc lập + phản biện đối kháng) tìm ra ba gốc lỗi lặp ở NHIỀU cổng:
  • CHUNG-A — cổng sau tin TRẠNG THÁI LƯU SẴN của cổng trước (`quality_gate.status` trong checkpoint) hoặc chỉ hỏi
    «checkpoint có tồn tại không», không chấm lại. Ví dụ thật: G0 của C1a lưu PASS_G0_CONFIRMED (02/09) trong khi chấm
    sống ra DRAFT (study_meta sửa 04/10) — G1, study_readiness, G10 đều in «đã chốt». Cổng CỨNG có sổ cái nên không
    dính; cổng MỀM (G0/G1/G3/G6/G7) thì gần như không cổng sau nào chấm lại.
  • CHUNG-C — xác nhận của người (reviewed_at + cờ True) KHÔNG gắn với nội dung được xác nhận: sửa nội dung sau khi xác
    nhận vẫn PASS; `reviewed_at` ở tương lai (2099) vẫn PASS ở nhiều cổng.
  • Bộ đo độ tươi bằng mtime không đáng tin (bản clone dàn phẳng) — băm nội dung là thước đo bền hơn.

HÀM CÔNG KHAI (chỉ thư viện chuẩn; import lười bộ chấm nên không tạo vòng import):
  • trang_thai_song(gate, study, out_dir, repo_root=None) → dict: chấm SỐNG cổng `gate` bằng chính
    gN_quality_gate.evaluate_study(write=False) — KHÔNG ghi gì. Lỗi/crash/SystemExit/vòng lặp ⇒ «KHÔNG ĐO ĐƯỢC»,
    `dat=False` (không bao giờ PASS vì lỗi). Bản lưu chỉ để hiển thị (`trang_thai_luu`), không bao giờ cho `dat=True`.
    Cổng chưa có evaluate_study (G1 tới khi có) ⇒ đọc bản lưu NHƯNG đánh dấu nguon="luu" và `dat` chỉ True khi bản lưu
    PASS và checkpoint không mang `design.pin_bi_tu_choi` — người gọi phải coi nguon="luu" là kém tin cậy.
  • iso_khong_tuong_lai(v) → bool: ISO-8601 thật (có hoặc không múi giờ), KHÔNG ở tương lai. «04/10/2026» ⇒ False.
  • dau_van_tay(*phan) → str: 16 ký tự hex SHA-256 của JSON chuẩn tắc (sắp khoá, NFC, gọn khoảng trắng chuỗi) — dấu
    của NỘI DUNG mà một xác nhận chứng cho.
  • xac_nhan_gan_noi_dung(xac_nhan, dau_hien_tai, khoa="dau_van_tay") → (hợp lệ?, lý do): xác nhận của người hợp lệ khi
    có `reviewed_at` ISO không ở tương lai VÀ `dau_van_tay` trùng dấu nội dung HIỆN TẠI. Xác nhận cũ chưa có dấu ⇒
    KHÔNG hợp lệ (chuyển tiếp: chủ nhiệm xác nhận lại một lần — QĐ-7 chờ bác sĩ duyệt qua PR).
  • HỢP ĐỒNG BĂM CHUỖI BẢN THẢO (CHUNG-E): A9 của G8 nhúng băm bản thảo (`NHAN_BAM_BAN_THAO`, đã có từ 04/09/2026) và
    — từ 04/10/2026 — băm báo cáo phản biện (`NHAN_BAM_BAO_CAO_PHAN_BIEN`) dưới dạng dòng
    «**<nhãn> (`<tên tệp>`):** `<64 hex>`». `trich_bam_a9(text)` trả {"ban_thao", "bao_cao_phan_bien"} (None nếu vắng);
    `bam_van_ban_tep(p)` = SHA-256 của NỘI DUNG CHỮ (đọc UTF-8, xuống dòng chuẩn hoá) — ĐÚNG cách run_g8_auto băm bản
    thảo. G8 sinh, G9/G10 so lại: bản thảo hay báo cáo phản biện đổi sau khi ký G8 ⇒ cổng sau không READY.

KHÔNG làm thay người: chỉ ĐO; không ghi checkpoint/sổ cái, không tự xác nhận, không chọn giá trị.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import inspect
import io
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

KHONG_DO_DUOC = "KHONG_DO_DUOC"
NGUON_SONG = "song"
NGUON_LUU = "luu"
NGUON_LOI = "loi"

# Bộ nhớ đệm theo (cổng, thư mục, chữ ký tệp) — một lượt chấm G10 gọi chấm sống G0..G9, mỗi cổng lại chấm cổng trước
# nó: không có đệm thì số lần chấm là O(n²). Chữ ký = (tên, mtime_ns, kích thước) của mọi tệp trong thư mục đề tài ⇒
# tệp nào đổi thì đệm tự mất hiệu lực.
_DEM: Dict[Tuple[str, str, Tuple], Dict[str, Any]] = {}
_DANG_CHAM: set = set()


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return v if isinstance(v, dict) else {}


def _chu_ky_thu_muc(out_dir: Path) -> Tuple:
    try:
        return tuple(sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in out_dir.iterdir() if p.is_file()))
    except OSError:
        return ()


def muc_cua_trang_thai(status: Any) -> str:
    """Xếp một trạng thái bộ chấm về 4 mức chung: PASS · READY · DRAFT · BLOCKED (KHONG_DO_DUOC giữ nguyên)."""
    s = str(status or "").strip().upper()
    if not s:
        return KHONG_DO_DUOC
    if s == KHONG_DO_DUOC:
        return KHONG_DO_DUOC
    if s.startswith("PASS_"):
        return "PASS"
    if s.startswith("BLOCKED"):
        return "BLOCKED"
    if s.startswith(("READY_", "PENDING_")):
        return "READY"
    return "DRAFT"


def _trang_thai_luu(out_dir: Path, gate: str) -> Tuple[Optional[str], Dict[str, Any]]:
    cp = _doc_json(out_dir / f"{gate}_checkpoint.json")
    qg = cp.get("quality_gate")
    st = qg.get("status") if isinstance(qg, dict) else None
    if not st:
        rep = _doc_json(out_dir / f"{gate}_QUALITY_REPORT.json")
        st = rep.get("status")
    return (str(st) if st else None), cp


def _ket(gate: str, status: Optional[str], nguon: str, ly_do: str, luu: Optional[str],
         bao_cao: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    muc = muc_cua_trang_thai(status) if status else KHONG_DO_DUOC
    return {"gate": gate, "status": status or KHONG_DO_DUOC, "muc": muc,
            # nguon=loi luôn đi với status None ⇒ muc KHONG_DO_DUOC ⇒ dat=False (không cần điều kiện riêng).
            "dat": muc == "PASS", "bi_chan": muc == "BLOCKED",
            "nguon": nguon, "ly_do": ly_do, "trang_thai_luu": luu, "bao_cao": bao_cao}


def trang_thai_song(gate: str, study: str, out_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Chấm SỐNG cổng `gate` của đề tài (chỉ đọc). Xem docstring module."""
    out_dir = Path(out_dir)
    gate = str(gate).upper()
    luu, cp = _trang_thai_luu(out_dir, gate)
    khoa = (gate, str(out_dir.resolve()), _chu_ky_thu_muc(out_dir))
    if khoa in _DEM:
        return _DEM[khoa]
    if (gate, str(out_dir.resolve())) in _DANG_CHAM:
        return _ket(gate, None, NGUON_LOI, "vòng lặp chấm sống (cổng gọi lại chính nó) — không đo được", luu)
    _DANG_CHAM.add((gate, str(out_dir.resolve())))
    try:
        ket = _cham(gate, study, out_dir, repo_root, luu, cp)
    finally:
        _DANG_CHAM.discard((gate, str(out_dir.resolve())))
    _DEM[khoa] = ket
    return ket


def _cham(gate: str, study: str, out_dir: Path, repo_root: Optional[Path], luu: Optional[str],
          cp: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(f"{gate.lower()}_quality_gate")
    except Exception as exc:  # noqa: BLE001
        return _ket(gate, None, NGUON_LOI, f"không nạp được bộ chấm: {type(exc).__name__}: {exc}", luu)
    fn = getattr(mod, "evaluate_study", None)
    if fn is None:
        # Cổng chưa có hàm chấm lại từ tệp (G1 tới khi có): đọc bản lưu, đánh dấu kém tin cậy; pin thiết kế bị từ chối
        # trong checkpoint thì luôn coi là BỊ CHẶN dù bản lưu nói gì.
        design = cp.get("design") if isinstance(cp.get("design"), dict) else {}
        if design.get("pin_bi_tu_choi"):
            return _ket(gate, "BLOCKED", NGUON_LUU,
                        f"checkpoint mang design.pin_bi_tu_choi={design['pin_bi_tu_choi']!r} — bị chặn", luu)
        if not luu:
            return _ket(gate, None, NGUON_LOI, "bộ chấm không có evaluate_study và chưa có trạng thái lưu", luu)
        return _ket(gate, luu, NGUON_LUU, "bộ chấm chưa có evaluate_study — dùng bản LƯU (kém tin cậy)", luu)
    try:
        params = inspect.signature(fn).parameters
        kw: Dict[str, Any] = {}
        if "out_dir" in params:
            kw["out_dir"] = out_dir
        if "write" in params:
            kw["write"] = False
        if "repo_root" in params:
            # Quy ước out_dir = <repo>/exports/<study> (giống kiem_chi_tiet_he_nghien_cuu._cham_song): suy repo_root từ
            # out_dir để không đọc sổ cái của repo THẬT khi đang chấm một thư mục thử.
            kw["repo_root"] = Path(repo_root) if repo_root is not None else out_dir.parent.parent
        with contextlib.redirect_stdout(io.StringIO()):
            bao_cao = fn(study, **kw)
    except SystemExit as exc:
        return _ket(gate, None, NGUON_LOI, f"bộ chấm thoát mã {exc.code} — không đo được", luu)
    except Exception as exc:  # noqa: BLE001 — lỗi ⇒ không đo được, KHÔNG BAO GIỜ PASS
        return _ket(gate, None, NGUON_LOI, f"bộ chấm hỏng: {type(exc).__name__}: {str(exc)[:160]}", luu)
    if not isinstance(bao_cao, dict) or not bao_cao.get("status"):
        return _ket(gate, None, NGUON_LOI, "bộ chấm không trả trạng thái", luu)
    return _ket(gate, str(bao_cao["status"]), NGUON_SONG, "chấm sống (write=False)", luu, bao_cao)


def xoa_dem() -> None:
    """Xoá bộ nhớ đệm chấm sống (test, hoặc tiến trình dài sau khi tệp đổi mà mtime không đổi)."""
    _DEM.clear()


# ───────────────────────────────────────────────────────────────────────────── xác nhận gắn nội dung
def iso_khong_tuong_lai(v: Any) -> bool:
    """`reviewed_at` phải là ISO-8601 thật và không nằm ở tương lai (cùng quy tắc g3_quality_gate._valid_iso_time)."""
    text = str(v or "").strip()
    if not text:
        return False
    try:
        t = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return t <= (datetime.now(tz=t.tzinfo) if t.tzinfo else datetime.now())


def _rong(v: Any) -> bool:
    return v is None or (isinstance(v, (str, list, tuple, set, dict)) and len(v) == 0)


def _chuan_tac(v: Any) -> Any:
    # VÁ 04/10/2026 (soát từng cổng, phát hiện khi làm G3): khoá KHÔNG có nội dung (None, "", [], {} — kể cả dict con
    # rỗng sau khi lọc) bị bỏ khỏi dấu vân tay. Trước đây ensure_study_meta thêm khoá khuôn rỗng (team_roles: None,
    # annex2: {applicable: None, methodologies: []}…) làm ĐỔI dấu G1/G0 và vô hiệu xác nhận của PI dù không ai đổi quyết
    # định nào. False và 0 VẪN là nội dung.
    if isinstance(v, Mapping):
        ra = {}
        for k, x in sorted(v.items(), key=lambda kv: str(kv[0])):
            cx = _chuan_tac(x)
            if not _rong(cx):
                ra[str(k)] = cx
        return ra
    if isinstance(v, (list, tuple)):
        return [_chuan_tac(x) for x in v]
    if isinstance(v, set):
        return sorted(_chuan_tac(x) for x in v)
    if isinstance(v, str):
        return " ".join(unicodedata.normalize("NFC", v).split())
    if isinstance(v, Path):
        return v.as_posix()
    return v


def dau_van_tay(*phan: Any) -> str:
    """16 ký tự hex SHA-256 của JSON chuẩn tắc các phần nội dung — đổi một chữ ⇒ đổi dấu."""
    goc = json.dumps([_chuan_tac(p) for p in phan], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                     default=str)
    return hashlib.sha256(goc.encode("utf-8")).hexdigest()[:16]


def dau_van_tay_tep(*duong_dan: Path) -> str:
    """Dấu vân tay NỘI DUNG các tệp (byte, CRLF→LF để Mac/Windows ra cùng dấu); tệp vắng góp chuỗi «<vắng>»."""
    phan = []
    for p in duong_dan:
        try:
            phan.append(hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        except OSError:
            phan.append("<vắng>")
    return dau_van_tay(*phan)


# ───────────────────────────────────────────────────────────────────────────── hợp đồng băm chuỗi bản thảo (CHUNG-E)
NHAN_BAM_BAN_THAO = "Hash SHA-256 bản thảo đã ràng buộc"
NHAN_BAM_BAO_CAO_PHAN_BIEN = "Hash SHA-256 báo cáo phản biện đã ràng buộc"
_RE_BAM_A9 = {
    "ban_thao": re.compile(re.escape(NHAN_BAM_BAN_THAO) + r"[^:\n]*:\*\*\s*`([0-9a-f]{64})`", re.IGNORECASE),
    "bao_cao_phan_bien": re.compile(re.escape(NHAN_BAM_BAO_CAO_PHAN_BIEN) + r"[^:\n]*:\*\*\s*`([0-9a-f]{64})`",
                                    re.IGNORECASE),
}


def dong_bam_a9(nhan: str, ten_tep: str, bam: str) -> str:
    """Dòng máy-đọc-được để nhúng một băm vào A9 (bộ sinh G8 dùng; trich_bam_a9 đọc ngược)."""
    return f"**{nhan} (`{ten_tep}`):** `{bam}`"


def trich_bam_a9(text: Any) -> Dict[str, Optional[str]]:
    """{"ban_thao": hex|None, "bao_cao_phan_bien": hex|None} trích từ nội dung A9."""
    vb = str(text or "")
    ra: Dict[str, Optional[str]] = {}
    for khoa, mau in _RE_BAM_A9.items():
        m = mau.search(vb)
        ra[khoa] = m.group(1).lower() if m else None
    return ra


def bam_van_ban_tep(p: Any) -> Optional[str]:
    """SHA-256 (64 hex) của nội dung CHỮ tệp (UTF-8, xuống dòng chuẩn hoá như read_text) — None nếu vắng/rỗng."""
    try:
        text = Path(p).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text.strip() else None


def xac_nhan_gan_noi_dung(xac_nhan: Any, dau_hien_tai: str, khoa: str = "dau_van_tay",
                          khoa_ngay: str = "reviewed_at") -> Tuple[bool, str]:
    """(hợp lệ?, lý do) — xác nhận của người phải có ngày ISO không ở tương lai VÀ dấu vân tay trùng nội dung HIỆN TẠI.

    Xác nhận cũ (trước 04/10/2026) chưa có dấu ⇒ không hợp lệ, lý do nói rõ cách xác nhận lại (chuyển tiếp QĐ-7)."""
    if not isinstance(xac_nhan, Mapping):
        return False, "chưa có xác nhận của người"
    if not iso_khong_tuong_lai(xac_nhan.get(khoa_ngay)):
        return False, f"`{khoa_ngay}` không phải ISO-8601 hợp lệ hoặc ở tương lai"
    dau = str(xac_nhan.get(khoa) or "").strip().lower()
    if not dau:
        return False, (f"xác nhận chưa gắn `{khoa}` (xác nhận kiểu cũ) — chủ nhiệm xác nhận lại với "
                       f"{khoa}={dau_hien_tai} (dấu nội dung hiện tại)")
    if dau != str(dau_hien_tai).strip().lower():
        return False, (f"nội dung đã đổi sau khi xác nhận (dấu lúc xác nhận {dau} ≠ hiện tại {dau_hien_tai}) — "
                       "chủ nhiệm đọc lại rồi xác nhận lại")
    return True, "xác nhận gắn đúng nội dung hiện tại"
