#!/usr/bin/env python3
"""Nội dung hồ sơ đạo đức G2 ĐÃ SOẠN — đọc từ study_meta để `run_g2_auto.py --regenerate` tái lập đúng bản đang nộp.

Vì sao có tệp này (22/11/2026, nguyên tắc «tính tái lập», «sửa tại nguồn»): hồ sơ G2 của đề tài thật được điền
tay hàng chục ô sau lượt máy sinh (phiếu đồng ý, WHO TRDS, chia sẻ dữ liệu, khai báo AI…) mà không ô nào có khoá
nguồn ⇒ sinh lại là mất, và trạng thái cổng đổi (C1a từ READY về DRAFT). Nay mọi nội dung đó nằm trong study_meta và bộ
sinh đọc:

1. Khoá NGỮ NGHĨA (một dữ kiện, dùng nhiều nơi) — `gate_params.G2`:
   `ngay_phien_ban` (ngày phiên bản hồ sơ: bìa Đơn, Kế hoạch quản lý dữ liệu, checklist, ngày khai báo, đơn xin miễn),
   `tap_chi_du_kien`, `loi_ich_truc_tiep`, `loi_ich_cong_dong`, `rui_ro_xac_nhan` (câu ghi lại lần chủ nhiệm đã rà bảng
   rủi ro), `so_ban_nop`, `ai` ({co_su_dung, cong_cu_khac, nguoi_kiem_tra}), `tra_dang_ky_khac` (kết quả tự tra WHO
   ICTRP/PROSPERO/đăng ký trong nước), `tl1_kem_theo_extra` (hồ sơ kèm thêm ở Đơn), `mien_icf_lap_luan`
   ({i_khong_kha_thi, ii_gia_tri_xa_hoi, iii_nguy_co_toi_thieu} — lập luận ba điều kiện CIOMS 2016 Hướng dẫn 10);
   `data_governance`: `breach_procedure`, `breach_internal`, `breach_extra`, `sharing_choice`
   (khong | theo_yeu_cau | mo).
2. KHỐI ĐÃ SOẠN — `gate_params.G2.da_soan` {tên khối: văn bản}: đoạn văn bản do người soạn (đã duyệt), in NGUYÊN VĂN
   (không qua bộ chuẩn hoá văn phong) thay đúng đoạn khuôn tương ứng. Tên khối hợp lệ ở `KHOI` dưới đây.
3. WHO TRDS — `gate_params.G2.trds_md` {số trường: các dòng giá trị}: thay phần giá trị của «Trường N» trong khối
   đăng ký (bản dịch tiếng Anh, nhà tài trợ, nơi tuyển, chia sẻ IPD…), nguyên văn.

Khối đã soạn KHÔNG tự cập nhật khi G1 đổi — đúng bản chất văn bản đã trình Hội đồng; đổi G1 sau khi nộp thì dấu đầu vào
G2 (`g2_quality_gate.dau_dau_vao_g2`) báo cần sửa đổi đề cương. Không khoá nào ở đây là xác nhận/chữ ký của người.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

#: Khối đã soạn hợp lệ — tên: đoạn khuôn mà khối thay.
KHOI: Dict[str, str] = {
    "tl1_dang_ky": "Tài liệu 1 — giá trị dòng «Đăng ký nghiên cứu:»",
    "tl2_van_de": "Tài liệu 2 mục 1 — dòng vấn đề nghiên cứu",
    "tl2_bang_chung": "Tài liệu 2 mục 1 — dòng «Bằng chứng hiện có» và dòng lý do cần nghiên cứu",
    "tl2_quy_trinh": "Tài liệu 2 mục 4 — dòng «Quy trình:»",
    "tl2_bao_mat": "Tài liệu 2 mục 7 — các dòng bảo mật dữ liệu",
    "tl3_bang_rui_ro": "Tài liệu 3 — bảng rủi ro (tiêu đề bảng và các hàng)",
    "tl4": "Tài liệu 4 — toàn bộ phiếu đồng ý tiếng Việt (giữa tiêu đề và đường kẻ cuối)",
    "tl5": "Tài liệu 5 — toàn bộ phiếu đồng ý tiếng Anh (giữa tiêu đề và đường kẻ cuối)",
    "tl6_loai_du_lieu": "Tài liệu 6 mục 1 — dòng liệt kê loại dữ liệu cụ thể",
    "tl6_cong_cu": "Tài liệu 6 mục 2 — dòng công cụ thu thập đã chọn",
    "tl6_khu_dinh_danh": "Tài liệu 6 mục 3 — các dòng phương pháp khử định danh",
    "tl6_chia_se_ghi_chu": "Tài liệu 6 mục 5 — các dòng ghi lựa chọn chia sẻ dữ liệu",
    "tl6_cuoi_nghien_cuu": "Tài liệu 6 mục 7 — các dòng xử lý dữ liệu cuối nghiên cứu",
    "tl7_du_lieu_thu_cap": "Tài liệu 7 — dòng hồ sơ bổ sung «[Dữ liệu thứ cấp]»",
    "tl9_khong_nop": "Tài liệu 9 — ghi chú quyết định KHÔNG xin miễn phiếu đồng ý (thay đơn xin miễn)",
}

_TOKEN_RE = re.compile("\x02(\\d+)\x03")


def _chu(v: Any, cho_o: bool = False) -> str:
    """Chuỗi THẬT (giữ nguyên xuống dòng và khoảng trắng); rỗng khi vắng. `cho_o=False` (khoá ngữ nghĩa): giá trị chỉ
    là ô chờ điền «[CẦN…]» cũng coi như vắng; `cho_o=True` (văn bản đã soạn): giữ, vì văn bản có thể chứa ô sau phê
    duyệt hợp lệ (số IRB, mã đăng ký…)."""
    if not isinstance(v, str) or not v.strip():
        return ""
    if not cho_o and v.strip().upper().startswith("[CẦN"):
        return ""
    return v.rstrip("\n")


def _g2(meta: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    gp = meta.get("gate_params") if isinstance(meta, Mapping) else None
    g2 = gp.get("G2") if isinstance(gp, Mapping) else None
    return g2 if isinstance(g2, Mapping) else {}


def khoi_da_soan(meta: Optional[Mapping[str, Any]]) -> Dict[str, str]:
    """{tên khối: văn bản} đã soạn (chỉ tên hợp lệ, chỉ văn bản thật)."""
    ds = _g2(meta).get("da_soan")
    if not isinstance(ds, Mapping):
        return {}
    return {k: _chu(v, True) for k, v in ds.items() if k in KHOI and _chu(v, True)}


def khoi_la(meta: Optional[Mapping[str, Any]]) -> List[str]:
    """Tên khối đã soạn KHÔNG có trong `KHOI` (gõ sai ⇒ báo, không lặng lẽ bỏ qua)."""
    ds = _g2(meta).get("da_soan")
    return sorted(k for k in ds if k not in KHOI) if isinstance(ds, Mapping) else []


def trds_md(meta: Optional[Mapping[str, Any]]) -> Dict[int, str]:
    """{số trường WHO TRDS: các dòng giá trị nguyên văn}."""
    tr = _g2(meta).get("trds_md")
    if not isinstance(tr, Mapping):
        return {}
    ra: Dict[int, str] = {}
    for k, v in tr.items():
        if str(k).isdigit() and _chu(v, True):
            ra[int(k)] = _chu(v, True)
    return ra


def gia_tri(meta: Optional[Mapping[str, Any]], *duong: str) -> str:
    """Giá trị chuỗi thật theo đường khoá (vd "gate_params", "G2", "so_ban_nop"); rỗng nếu vắng/ô chờ điền."""
    cur: Any = meta
    for k in duong:
        cur = cur.get(k) if isinstance(cur, Mapping) else None
    return _chu(cur)


def ngay_phien_ban(meta: Optional[Mapping[str, Any]], run_date: str) -> Tuple[str, str]:
    """(YYYY-MM-DD, DD/MM/YYYY) của phiên bản hồ sơ — `gate_params.G2.ngay_phien_ban`, vắng thì ngày chạy."""
    v = _chu(_g2(meta).get("ngay_phien_ban")) or str(run_date or "")[:10]
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v.strip())
    return (v.strip(), f"{m.group(3)}/{m.group(2)}/{m.group(1)}") if m else (v.strip(), v.strip())


def ten_ngan_hoi_dong(irb_name: str) -> str:
    """«Hội đồng Y đức Bệnh viện Quân y 175» ⇒ «Hội đồng Y đức»; không phải tên hội đồng ⇒ «Hội đồng Đạo đức»."""
    s = " ".join(str(irb_name or "").split())
    m = re.match(r"(Hội đồng [^,]*?)(?:\s+(?:Bệnh viện|Trường|Viện|Sở)\b.*)?$", s)
    return m.group(1) if m and not s.startswith("[") else "Hội đồng Đạo đức"


class BaoVe:
    """Đoạn văn bản ĐI THẲNG vào hồ sơ, không qua `vn_prose_style.clean_generated_prose` (bộ này đổi «—» thành dấu
    phẩy/chấm — đúng cho câu máy sinh, sai cho văn bản người đã soạn và dữ kiện nguyên văn). Bộ sinh đặt mã giữ chỗ,
    chuẩn hoá văn phong phần còn lại, rồi `chen` thay mã bằng văn bản."""

    def __init__(self) -> None:
        self._khoi: List[Tuple[str, bool]] = []

    def _dat(self, van: str, gon: bool) -> str:
        self._khoi.append((van, gon))
        return f"\x02{len(self._khoi) - 1}\x03"

    def nguyen_van(self, van: str) -> str:
        """Văn bản người soạn — giữ nguyên từng ký tự (kể cả thụt lề, ngắt dòng)."""
        return self._dat(van, False)

    def sinh(self, van: str) -> str:
        """Văn bản bộ sinh dựng từ dữ kiện — giữ dấu câu của dữ kiện, chỉ gộp khoảng trắng như bộ chuẩn hoá."""
        return self._dat(van, True)

    def chen(self, van_ban: str, gop_khoang_trang: bool = True) -> str:
        """Thay mã bằng văn bản. `gop_khoang_trang=False` (văn bản KHÔNG qua bộ chuẩn hoá — gọi hàm sinh trực tiếp):
        đoạn bộ sinh dựng cũng giữ nguyên thụt lề như phần khuôn quanh nó."""
        def _thay(m: re.Match) -> str:
            van, gon = self._khoi[int(m.group(1))]
            if not gon or not gop_khoang_trang:
                return van
            return "\n".join(re.sub(r" {2,}", " ", d.rstrip(" ")) for d in van.split("\n"))

        # khối có thể chứa mã của khối khác (vd đoạn sinh bọc dữ kiện nguyên văn) ⇒ thay tới khi hết mã
        for _ in range(5):
            moi = _TOKEN_RE.sub(_thay, van_ban)
            if moi == van_ban:
                break
            van_ban = moi
        return van_ban


_TRDS_DAU_RE = re.compile(r"^Trường (\d+)\s+— [^\n]*:\s*$")


def ap_trds(van_ban: str, ghi_de: Mapping[int, str], bv: BaoVe) -> str:
    """Thay phần giá trị của «Trường N» (các dòng thụt lề ngay sau tiêu đề, tới dòng trống) bằng bản đã soạn."""
    if not ghi_de:
        return van_ban
    dong = van_ban.split("\n")
    ra: List[str] = []
    i = 0
    while i < len(dong):
        ra.append(dong[i])
        m = _TRDS_DAU_RE.match(dong[i])
        if m and int(m.group(1)) in ghi_de:
            j = i + 1
            while j < len(dong) and dong[j].strip():
                j += 1
            ra.append(bv.nguyen_van(ghi_de[int(m.group(1))]))
            i = j
            continue
        i += 1
    return "\n".join(ra)


def thay_than_tai_lieu(van_ban: str, so: int, than: str, bv: BaoVe) -> str:
    """Thay toàn bộ thân «## TÀI LIỆU {so}» (sau dòng tiêu đề, tới «---» trước tài liệu kế) bằng bản đã soạn."""
    m = re.search(rf"(^## TÀI LIỆU {so}\b[^\n]*\n)(.*?)(?=^---\n\n## )", van_ban, re.S | re.M)
    if not m:
        return van_ban
    return van_ban[:m.start(2)] + "\n" + bv.nguyen_van(than) + "\n\n" + van_ban[m.end(2):]


def dang_ky_tu_checkpoint(cp: Mapping[str, Any]) -> Optional[dict]:
    """Kết quả tra ClinicalTrials.gov ĐÃ LƯU ở G2_checkpoint (lần tra thật trước) — dùng khi chạy `--skip-registry`
    để hồ sơ sinh lại không lùi về «CHƯA TRA ĐƯỢC». Chưa từng tra thật ⇒ None."""
    ct = cp.get("clinicaltrials") if isinstance(cp, Mapping) else None
    if not isinstance(ct, Mapping) or not ct.get("checked"):
        return None
    mau = ct.get("samples") if isinstance(ct.get("samples"), list) else (cp.get("clinicaltrials_samples") or [])
    return {
        "registry": ct.get("registry") or "ClinicalTrials.gov", "checked": True, "query": ct.get("query") or "",
        "n_trials": ct.get("n_trials") or 0, "n_active": ct.get("n_active"), "error": None,
        "checked_at": ct.get("checked_at"),
        "trials": [dict(t) for t in mau if isinstance(t, Mapping)],
    }
