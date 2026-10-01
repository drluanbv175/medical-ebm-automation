"""Dấu vân ĐƯỜNG MẠNG lúc chạy — mỗi lượt quét tự ghi nó đi qua VPN hay ra thẳng (thêm 01/10/2026).

Vì sao (bác sĩ yêu cầu «giải quyết vấn đề VPN triệt để»): cùng một nguồn lúc chạy lúc bị chặn tuỳ IP thoát ra Internet,
không cố định theo «VPN bật/tắt». Source Log thật: ECDC chạy được ngày 21/09 qua VPN nhưng bị CloudFront chặn 4/4 lượt
29/09 cũng qua VPN; NCBI chặn IP TRỰC TIẾP suốt 01→16/09 rồi tự hết; Scopus bị Cloudflare chặn qua VPN 21→29/09 nhưng
chạy được qua VPN ngày 01/10. Muốn đọc đúng nguyên nhân một lỗi phải biết lượt đó đi đường nào — trước đây không lượt
nào ghi điều này, người đọc log phải đoán.

Nguyên tắc:
- Chỉ đọc TẠI MÁY (`scutil`/`route` trên macOS, `ip route` trên Linux). KHÔNG gọi dịch vụ ngoài để tra IP công khai
  (lộ IP và thêm một máy chủ ra ngoài).
- KHÔNG lưu địa chỉ máy chủ VPN — chỉ 8 ký tự đầu SHA-256 của nó (`may_chu_vpn`), đủ để thấy «cùng/khác máy chủ thoát»
  giữa các lượt. Không đọc giá trị biến môi trường proxy (có thể chứa mật khẩu) — chỉ ghi CÓ/KHÔNG.
- Ba trạng thái: `qua_vpn` True/False/None. None = KHÔNG đo được (vd Windows chưa hỗ trợ, lệnh hệ thống lỗi) — không
  được đọc thành «không có VPN» (luật «không đo được ≠ ổn»).
- Không bao giờ ném lỗi; mỗi lệnh hệ thống có trần thời gian; dùng đường dẫn tuyệt đối vì launchd có PATH tối giản.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

# Giao diện đường hầm (VPN) theo tên: macOS utun/ipsec/ppp, Linux tun/tap/wg/ppp.
_GIAO_DIEN_DUONG_HAM = ("utun", "ipsec", "ppp", "tun", "tap", "wg")
_TRAN_GIAY = 5
_SCUTIL = "/usr/sbin/scutil"
_ROUTE = "/sbin/route"
_BIEN_PROXY = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

ChayLenh = Callable[[Sequence[str]], str]


def _chay_lenh(lenh: Sequence[str]) -> str:
    """Chạy một lệnh hệ thống CHỈ ĐỌC, trả stdout ("" nếu lệnh thiếu/lỗi/quá giờ)."""
    try:
        return subprocess.run(list(lenh), capture_output=True, text=True, timeout=_TRAN_GIAY, check=False).stdout or ""
    except (OSError, subprocess.SubprocessError, ValueError):
        return ""


def _bam(gia_tri: str) -> str:
    return hashlib.sha256(gia_tri.encode("utf-8")).hexdigest()[:8]


def _la_duong_ham(giao_dien: Optional[str]) -> bool:
    return bool(giao_dien) and str(giao_dien).startswith(_GIAO_DIEN_DUONG_HAM)


def _do_macos(kq: Dict[str, Any], chay: ChayLenh) -> None:
    ds = chay([_SCUTIL, "--nc", "list"])
    vpn: List[str] = []
    for dong in ds.splitlines():
        if "(Connected)" in dong:
            ten = re.findall(r'"([^"]+)"', dong)
            vpn.append(ten[-1] if ten else dong.strip()[:60])
    kq["vpn_dang_noi"] = vpn
    if vpn:
        trang_thai = chay([_SCUTIL, "--nc", "status", vpn[0]])
        m = re.search(r"^\s*(?:RemoteAddress|ServerAddress)\s*:\s*(\S+)\s*$", trang_thai, re.M)
        if m:
            kq["may_chu_vpn"] = _bam(m.group(1))
        m = re.search(r"^\s*LastStatusChangeTime\s*:\s*(.+?)\s*$", trang_thai, re.M)
        if m:
            kq["vpn_doi_trang_thai_luc"] = m.group(1)
    tuyen = chay([_ROUTE, "-n", "get", "default"])
    m = re.search(r"^\s*interface:\s*(\S+)\s*$", tuyen, re.M)
    kq["tuyen_mac_dinh"] = m.group(1) if m else None
    if kq["tuyen_mac_dinh"]:
        kq["qua_vpn"] = _la_duong_ham(kq["tuyen_mac_dinh"])
    elif vpn:
        kq["ghi_chu"] = "có VPN đang nối nhưng không đọc được tuyến mặc định"
    else:
        kq["ghi_chu"] = "không đọc được tuyến mặc định (route lỗi?)"


def _do_linux(kq: Dict[str, Any], chay: ChayLenh) -> None:
    ip = shutil.which("ip") or next((p for p in ("/usr/sbin/ip", "/sbin/ip", "/usr/bin/ip") if os.path.exists(p)), None)
    if not ip:
        kq["ghi_chu"] = "thiếu lệnh `ip` — không đo được tuyến mặc định"
        return
    m = re.search(r"\bdev\s+(\S+)", chay([ip, "-o", "route", "show", "default"]))
    kq["tuyen_mac_dinh"] = m.group(1) if m else None
    if kq["tuyen_mac_dinh"]:
        kq["qua_vpn"] = _la_duong_ham(kq["tuyen_mac_dinh"])
    else:
        kq["ghi_chu"] = "không có/không đọc được tuyến mặc định"


def dau_van_mang(chay: Optional[ChayLenh] = None, nen_tang: Optional[str] = None) -> Dict[str, Any]:
    """Dấu vân đường mạng của máy LÚC NÀY. Không ném lỗi; `qua_vpn` None = không đo được.

    `chay`/`nen_tang` chỉ để kiểm thử (tiêm lệnh giả, giả lập hệ điều hành)."""
    chay = chay or _chay_lenh
    nen_tang = nen_tang or sys.platform
    kq: Dict[str, Any] = {
        "luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "he_dieu_hanh": nen_tang,
        "qua_vpn": None,
        "vpn_dang_noi": [],
        "tuyen_mac_dinh": None,
        "may_chu_vpn": None,
        "co_proxy_moi_truong": any(os.environ.get(b) for b in _BIEN_PROXY),
        "ghi_chu": "",
    }
    try:
        if nen_tang == "darwin":
            _do_macos(kq, chay)
        elif nen_tang.startswith("linux"):
            _do_linux(kq, chay)
        else:
            kq["ghi_chu"] = f"chưa hỗ trợ đo đường mạng trên {nen_tang} — không đo được ≠ không có VPN"
    except Exception as exc:  # noqa: BLE001 — số đo phụ trợ không được làm hỏng lượt quét
        kq["qua_vpn"] = None
        kq["ghi_chu"] = f"lỗi khi đo đường mạng: {type(exc).__name__}"
    return kq


def mo_ta_ngan(dv: Optional[Dict[str, Any]]) -> str:
    """Một dòng tiếng Việt cho log: «qua VPN «Kaspersky VPN» (tuyến utun4, máy chủ #63dc5145)»…"""
    if not dv:
        return "không đo"
    if dv.get("qua_vpn") is None:
        return f"KHÔNG đo được ({dv.get('ghi_chu') or dv.get('he_dieu_hanh')})"
    chi_tiet = [f"tuyến {dv.get('tuyen_mac_dinh')}"]
    if dv.get("may_chu_vpn"):
        chi_tiet.append(f"máy chủ #{dv['may_chu_vpn']}")
    if dv.get("co_proxy_moi_truong"):
        chi_tiet.append("có proxy môi trường")
    if dv.get("qua_vpn"):
        ten = ", ".join(dv.get("vpn_dang_noi") or []) or "không rõ tên"
        return f"qua VPN «{ten}» ({', '.join(chi_tiet)})"
    noi = ""
    if dv.get("vpn_dang_noi"):
        noi = f"; VPN đang nối nhưng không làm tuyến mặc định: {', '.join(dv['vpn_dang_noi'])}"
    return f"ra thẳng, không qua VPN ({', '.join(chi_tiet)}{noi})"


def cung_duong(a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> bool:
    """Hai số đo có cùng đường mạng không (bỏ qua thời điểm đo)."""
    khoa = ("qua_vpn", "tuyen_mac_dinh", "may_chu_vpn", "vpn_dang_noi", "co_proxy_moi_truong")
    return all((a or {}).get(k) == (b or {}).get(k) for k in khoa)
