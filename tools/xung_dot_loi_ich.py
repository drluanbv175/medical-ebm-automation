#!/usr/bin/env python3
"""Xung đột lợi ích, tài trợ và quản trị dữ liệu của hồ sơ đạo đức — đọc từ study_meta.json (22/11/2026).

Vì sao có tệp này: Hội đồng đề tài (vòng 22/11/2026) quyết nội dung xung đột lợi ích, kế hoạch quản lý xung đột, người
giữ dữ liệu, phân quyền và người giám sát cho hai đề tài thật, nhưng nội dung đó chỉ là chữ vá trên văn bản G2 —
`run_g2_auto.py --regenerate` sinh lại từ khuôn là mất. Khuôn cũ còn hai lỗi nguồn: (1) Tài liệu 8 không có chỗ cho xung
đột cơ cấu theo hồ sơ (chủ nhiệm là bác sĩ của khoa được đánh giá…), nên người soạn tích sẵn «☑ Không có» ở mục khai
quan hệ cá nhân — tức khai thay người ký; (2) đề cương nộp in cứng «nhóm nghiên cứu cam kết không có xung đột lợi ích».
Nay mọi bộ sinh đọc CÙNG các khoá dưới đây; vắng dữ kiện ⇒ ô trống đúng mẫu, không bao giờ in «không có xung đột».

Khoá trong study_meta.json (mọi khoá đều tuỳ chọn):

- `administrative.sponsor` (đã có): nguồn tài trợ chính.
- `gate_params.G2.external_funding`: false ⇒ không có tài trợ bên ngoài (tài trợ bổ sung «Không có», số hợp đồng
  «Không áp dụng», vai trò nhà tài trợ «Không áp dụng»); true ⇒ giữ ô khai; vắng ⇒ giữ ô khai.
- `gate_params.G2.sponsor_role`: câu khai vai trò nhà tài trợ (mục D Tài liệu 8), thắng câu mặc định.
- `gate_params.G2.coi`: khối xung đột lợi ích theo HỒ SƠ đề tài (không phải quan hệ cá nhân):
  `summary` (dòng COI của Đơn — Tài liệu 1), `structural` (xung đột cơ cấu/thể chế — mục B2 Tài liệu 8),
  `management` (biện pháp quản lý, kèm chỗ trong đề cương), `monitor` (người giám sát độc lập, nếu có).
- `gate_params.G2.checklist_extra`: danh sách hồ sơ kèm thêm của Tài liệu 7 (bản khai, văn bản cử người giữ dữ liệu…).
- `gate_params.G2.icf_coi_statement` và `gate_params.G2.icf_en.coi_statement`: câu mục 4b của phiếu đồng ý (Việt/Anh).
- `data_governance.custodian` (người giữ dữ liệu), `data_governance.access_rules` (phân quyền truy cập),
  `data_governance.access_granted_by` (ai cấp quyền), `data_governance.storage_location` (nơi lưu),
  `data_governance.backup` (sao lưu). Khoá tách riêng vắng ⇒ đọc từ chuỗi gộp đã có `data_governance.access`
  («Phân quyền truy cập: …; Cấp quyền | Phê duyệt quyền: … (DMP mục 2)») và `data_governance.storage` («Nơi lưu: …;
  Bảo mật: …; Sao lưu: …; Thời gian lưu: …») — cùng chuỗi G10, STUDY_SPEC và đề cương đang đọc, không chép hai nơi.
  «Thời gian lưu» không đọc từ đây: thời hạn lấy từ quy trình dữ liệu đã chốt (`_quy-trinh-du-lieu.csv`).

Quan hệ tài chính và phi tài chính CÁ NHÂN (mục A, B Tài liệu 8) do người ký tự khai — không có khoá nào ở đây điền
được, và không bộ sinh nào được tích sẵn ô của hai mục đó.

Căn cứ (hội đồng đọc nguyên văn ngày 22/11/2026, ghi ở biên bản hội đồng của hai đề tài): Thông tư 43/2024/TT-BYT
Điều 2 khoản 1 (định nghĩa xung đột lợi ích) và Phụ lục I mục 6 khoản 3 (thay đổi báo Hội đồng trước khi áp dụng);
Tuyên bố Helsinki 10/2024 đoạn 22 (đề cương nêu nguồn kinh phí và mọi xung đột lợi ích tiềm tàng); CIOMS 2016 Hướng
dẫn 25 (xung đột nghề nghiệp/uy tín của cơ sở là xung đột lợi ích; biện pháp tương xứng); mẫu khai báo của ICMJE
(mục 1 không giới hạn thời gian, mục 2–13 trong 36 tháng gần nhất); Nghị định 356/2025/NĐ-CP Điều 4 khoản 2 (dữ liệu
nhạy cảm phải có phân quyền giới hạn truy cập).
"""
from __future__ import annotations

import re
import textwrap
from typing import Any, Dict, List, Mapping, Optional

#: Nhãn ô của khuôn (giữ nguyên chữ để bộ đếm ô trống G2 nhận như cũ).
O_COI_DON = "[CẦN KHAI BÁO — xem Tài liệu 8]"
O_TAI_TRO_CHINH = '[CẦN BỔ SUNG — "Không có tài trợ bên ngoài" nếu đúng]'
O_TAI_TRO_BO_SUNG = "[CẦN BỔ SUNG]"
O_SO_HOP_DONG = "[CẦN BỔ SUNG]"

#: Lựa chọn chia sẻ dữ liệu (mục 5 Kế hoạch quản lý dữ liệu) — khoá `data_governance.sharing_choice`.
CHIA_SE = ("khong", "theo_yeu_cau", "mo")

#: Câu mặc định cho mục D khi đề tài không có tài trợ bên ngoài.
VAI_TRO_KHONG_TAI_TRO = ("Không áp dụng — không có nhà tài trợ nên không có vai trò nhà tài trợ trong thiết kế, thu "
                         "thập, phân tích, báo cáo hay quyết định công bố.")


def _chu(v: Any) -> str:
    """Chuỗi THẬT (bỏ khoảng trắng thừa); rỗng khi vắng, không phải chuỗi, hoặc còn là ô chờ điền."""
    if not isinstance(v, str):
        return ""
    s = " ".join(v.split())
    if not s or "[CẦN" in s.upper() or s.upper().startswith("[TO BE"):
        return ""
    return s


def _khoi(meta: Optional[Mapping[str, Any]], *duong: str) -> Mapping[str, Any]:
    cur: Any = meta if isinstance(meta, Mapping) else {}
    for k in duong:
        cur = cur.get(k) if isinstance(cur, Mapping) else None
    return cur if isinstance(cur, Mapping) else {}


#: Nhãn của chuỗi gộp `data_governance.access` / `.storage` (khối DMP đã thu về study_meta).
_NHAN_GOP = ("Phân quyền truy cập", "Phê duyệt quyền", "Cấp quyền", "Nơi lưu", "Bảo mật", "Sao lưu", "Thời gian lưu")
_NHAN_GOP_RE = re.compile(r"(?:^|;\s*)(" + "|".join(map(re.escape, _NHAN_GOP)) + r"):\s*")
_THE_NGUON_CUOI_RE = re.compile(r"\s*\(DMP[^()]*\)\s*$")


def tach_chuoi_gop(chuoi: Any) -> Dict[str, str]:
    """{nhãn: giá trị} của chuỗi gộp «Nhãn: …; Nhãn: … (DMP …)» — bỏ thẻ nguồn cuối, dấu «;» thừa."""
    s = _chu(chuoi)
    if not s:
        return {}
    s = _THE_NGUON_CUOI_RE.sub("", s).replace(";;", ";")
    phan = _NHAN_GOP_RE.split(s)
    ra: Dict[str, str] = {}
    for i in range(1, len(phan) - 1, 2):
        gia_tri = phan[i + 1].strip().strip(";").strip()
        if gia_tri:
            ra[phan[i]] = gia_tri
    return ra


def doc(meta: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Gom mọi dữ kiện xung đột lợi ích/tài trợ/quản trị dữ liệu đã khai trong study_meta (chuỗi rỗng = chưa khai)."""
    g2 = _khoi(meta, "gate_params", "G2")
    coi = g2.get("coi") if isinstance(g2.get("coi"), Mapping) else {}
    dg = _khoi(meta, "data_governance")
    quyen, luu = tach_chuoi_gop(dg.get("access")), tach_chuoi_gop(dg.get("storage"))
    cap = _chu(dg.get("access_granted_by"))
    nhan_cap = "Cấp quyền"
    if not cap:
        nhan_cap = "Cấp quyền" if quyen.get("Cấp quyền") else "Phê duyệt quyền"
        cap = quyen.get(nhan_cap, "")
    icf_en = g2.get("icf_en") if isinstance(g2.get("icf_en"), Mapping) else {}
    ngoai = g2.get("external_funding")
    kem = g2.get("checklist_extra")
    return {
        "tom_tat": _chu(coi.get("summary")),
        "co_cau": _chu(coi.get("structural")),
        "quan_ly": _chu(coi.get("management")),
        "giam_sat": _chu(coi.get("monitor")),
        "tai_tro_chinh": _chu(_khoi(meta, "administrative").get("sponsor")),
        "tai_tro_ngoai": ngoai if isinstance(ngoai, bool) else None,
        "vai_tro_tai_tro": _chu(g2.get("sponsor_role")),
        "ho_so_kem": [s for s in (_chu(x) for x in (kem if isinstance(kem, list) else [])) if s],
        "icf": _chu(g2.get("icf_coi_statement")),
        "icf_en": _chu(icf_en.get("coi_statement")),
        "giu_du_lieu": _chu(dg.get("custodian")),
        "phan_quyen": _chu(dg.get("access_rules")) or quyen.get("Phân quyền truy cập", ""),
        "cap_quyen": cap,
        "nhan_cap_quyen": nhan_cap,
        "noi_luu": _chu(dg.get("storage_location")) or luu.get("Nơi lưu", ""),
        "sao_luu": _chu(dg.get("backup")) or luu.get("Sao lưu", ""),
        # 22/11/2026 (tái lập hồ sơ đã nộp): quy trình nội bộ khi vi phạm và lựa chọn chia sẻ dữ liệu đã quyết
        "vi_pham_noi_bo": _chu(dg.get("breach_internal")),
        "vi_pham_them": [x for x in (_chu(v) for v in (dg.get("breach_extra") or [])
                                     if isinstance(dg.get("breach_extra"), list)) if x],
        "vi_pham_quy_trinh": _chu(dg.get("breach_procedure")),
        "chia_se": dg.get("sharing_choice") if dg.get("sharing_choice") in CHIA_SE else "",
        "ghi_chu_thanh_vien": _chu(coi.get("member_note")),
    }


# Không ngắt dòng giữa tên văn bản/điều khoản và số hiệu («Luật | 91/2025/QH15», «Điều | 23»).
_GIU_LIEN_RE = re.compile(r"\b(Luật|định|Thông tư|Điều|khoản|điểm|mục|Bảng|Phụ lục|Tài liệu|\d) "
                          r"(?=[0-9A-ZĐ]|khoản|điểm)")
_NOI = "\ue000"  # ký tự vùng riêng, không có trong văn bản thật


def boc(van: str, dau: str = "", thut: str = " ", rong: int = 110) -> str:
    """Ngắt dòng theo TỪ cho khối mã của hồ sơ (dòng đầu mang `dau`, các dòng sau thụt `thut`)."""
    van = _GIU_LIEN_RE.sub(lambda m: m.group(1) + _NOI, van)
    dong = textwrap.wrap(van, width=rong, initial_indent=dau, subsequent_indent=thut,
                         break_long_words=False, break_on_hyphens=False)
    return "\n".join(dong).replace(_NOI, " ") or dau.rstrip()


# ── Tài liệu 1 — Đơn xin phê duyệt ───────────────────────────────────────────────────────────────────────────────────

def dong_coi_don(k: Mapping[str, Any]) -> str:
    """Giá trị dòng «Xung đột lợi ích (COI):» của Đơn — dữ kiện hồ sơ nếu đã khai, không thì ô khai."""
    return f"{k['tom_tat']}; khai đầy đủ ở Tài liệu 8" if k.get("tom_tat") else O_COI_DON


# ── Tài liệu 8 — Khai báo xung đột lợi ích, tài trợ ──────────────────────────────────────────────────────────────────

MUC_A = (
    "A. XUNG ĐỘT LỢI ÍCH TÀI CHÍNH (theo mẫu khai báo ICMJE: mọi hỗ trợ cho đề tài không giới hạn thời gian,\n"
    " các quan hệ khác trong ba năm gần nhất; chủ nhiệm tự đánh dấu và ký; mỗi thành viên khai bản riêng):\n"
    "☐ Không có\n"
    "☐ Có → [Liệt kê: Tên công ty · Loại quan hệ (cổ phần/tư vấn/\n"
    "         thù lao/tài trợ hội nghị) · Giá trị (nếu phải khai)]"
)
MUC_B = (
    "B. XUNG ĐỘT LỢI ÍCH PHI TÀI CHÍNH CÁ NHÂN — người ký tự đánh dấu:\n"
    "☐ Không có\n"
    "☐ Có → [Quan hệ cá nhân với người được nghiên cứu / lợi ích\n"
    "         học thuật (thăng tiến/bằng sáng chế) / quan điểm đối nghịch]"
)


def muc_b2(k: Mapping[str, Any]) -> str:
    """Mục B2 — xung đột cơ cấu/thể chế THEO HỒ SƠ đề tài (vị trí công tác, quan hệ với đơn vị được nghiên cứu…)."""
    dau = "B2. XUNG ĐỘT LỢI ÍCH CẤU TRÚC/THỂ CHẾ (theo hồ sơ đề tài):\n"
    if not k.get("co_cau"):
        return (dau + "☐ Không có\n"
                "☐ Có → [Vị trí công tác hoặc quan hệ với đơn vị, người được nghiên cứu · nguồn chi trả\n"
                "         cho các vai trò độc lập · biện pháp quản lý]")
    noi = k["co_cau"] + (f" Quản lý: {k['quan_ly']}" if k.get("quan_ly") else "")
    return dau + boc(noi, dau="☑ Có → ")


def muc_c(k: Mapping[str, Any]) -> str:
    """Mục C — nguồn tài trợ; `external_funding` = false ⇒ tài trợ bổ sung «Không có», hợp đồng «Không áp dụng»."""
    khong = k.get("tai_tro_ngoai") is False
    return ("C. NGUỒN TÀI TRỢ:\n"
            f"  Tài trợ chính: {k.get('tai_tro_chinh') or O_TAI_TRO_CHINH}\n"
            f"  Tài trợ bổ sung: {'Không có' if khong else O_TAI_TRO_BO_SUNG}\n"
            f"  Số hợp đồng (nếu có): {'Không áp dụng' if khong else O_SO_HOP_DONG}")


def muc_d(k: Mapping[str, Any]) -> str:
    """Mục D — vai trò nhà tài trợ: câu đã khai, hoặc «Không áp dụng» khi không có tài trợ, hoặc khung ô tích."""
    cau = k.get("vai_tro_tai_tro") or (VAI_TRO_KHONG_TAI_TRO if k.get("tai_tro_ngoai") is False else "")
    if cau:
        return "D. VAI TRÒ NHÀ TÀI TRỢ:\n" + boc(cau, dau="  ", thut="  ")
    return ("D. VAI TRÒ NHÀ TÀI TRỢ:\n"
            "  Nhà tài trợ có can thiệp vào:\n"
            "  ☐ Thiết kế nghiên cứu: ☐ Có ☐ Không\n"
            "  ☐ Thu thập / phân tích dữ liệu: ☐ Có ☐ Không\n"
            "  ☐ Báo cáo / quyết định công bố: ☐ Có ☐ Không")


def cam_ket_khai_bo_sung(k: Mapping[str, Any], hoi_dong: str = "Hội đồng Đạo đức") -> str:
    """Lời cam kết khai bổ sung đặt TRƯỚC chữ ký (Thông tư 43/2024/TT-BYT, Phụ lục I mục 6 khoản 3). `hoi_dong` = tên
    ngắn của Hội đồng nơi nộp (vd «Hội đồng Y đức»)."""
    noi = (hoi_dong or "Hội đồng Đạo đức") + (" và người giám sát độc lập" if k.get("giam_sat") else "")
    return boc(f"Tôi cam kết khai báo bổ sung bằng văn bản cho {noi} khi phát sinh quan hệ hoặc lợi ích mới có "
               "thể ảnh hưởng đến nghiên cứu.", thut="")


GHI_CHU_THANH_VIEN = ("[Mỗi thành viên nhóm nghiên cứu khai báo riêng theo mẫu này trước khi nhận nhiệm vụ; mỗi đồng\n"
                      " tác giả khai báo theo mẫu ICMJE khi nộp bài]")


def ghi_chu_thanh_vien(k: Mapping[str, Any]) -> str:
    """Dòng chú thích dưới chữ ký: câu đề tài đã soạn (`gate_params.G2.coi.member_note`), vắng thì câu chuẩn."""
    return k.get("ghi_chu_thanh_vien") or GHI_CHU_THANH_VIEN


# ── Tài liệu 6 — Kế hoạch quản lý dữ liệu ────────────────────────────────────────────────────────────────────────────

def dong_phan_quyen(k: Mapping[str, Any]) -> str:
    """Hai dòng phân quyền của mục 2 (Thu thập) — dữ kiện đã khai, không thì câu khuôn cũ."""
    pq = boc(k.get("phan_quyen") or "Chỉ nhóm nghiên cứu được cấp phép", dau="   Phân quyền truy cập: ", thut="     ")
    cq = (boc(k["cap_quyen"], dau=f"   {k.get('nhan_cap_quyen') or 'Cấp quyền'}: ", thut="     ")
          if k.get("cap_quyen") else "   Phê duyệt quyền: Chủ nhiệm đề tài")
    return pq + "\n" + cq


def dong_luu_tru(k: Mapping[str, Any], thoi_gian_luu: str, co_thoi_han: bool, can_cu_thoi_han: str) -> str:
    """Mục 4 (Lưu trữ): nơi lưu, người giữ dữ liệu, bảo mật, sao lưu, thời gian lưu (kèm căn cứ khi đã chốt)."""
    dong = [boc(k["noi_luu"], dau="   Nơi lưu: ", thut="     ") if k.get("noi_luu") else
            "   Nơi lưu: [CẦN — máy chủ nội bộ / OneDrive institutional\n"
            "             / ổ cứng mã hóa tại đơn vị]"]
    if k.get("giu_du_lieu"):
        dong.append(boc(k["giu_du_lieu"], dau="   Người giữ dữ liệu: ", thut="     "))
    dong.append("   Bảo mật: AES-256 · mật khẩu cấp người dùng · VPN (nếu từ xa)")
    dong.append(boc(k["sao_luu"], dau="   Sao lưu: ", thut="     ") if k.get("sao_luu") else
                "   Sao lưu: [CẦN — ví dụ: hàng ngày/tuần, 2 bản độc lập]")
    dong.append(f"   Thời gian lưu: {thoi_gian_luu}")
    if co_thoi_han:
        dong.append(boc(f"(thời hạn đã chốt của đề tài; {can_cu_thoi_han})", dau="                  ",
                        thut="                  "))
    return "\n".join(dong)


def dong_vi_pham(k: Mapping[str, Any], han: str, noi_dung: str) -> str:
    """Mục 6 (Xử lý vi phạm) — căn cứ đúng điều khoản; người phát hiện báo ngay cho bên kiểm soát dữ liệu.

    Quy trình NỘI BỘ của đề tài (vd hạn báo cáo nội bộ, thông báo người tham gia — `data_governance.breach_internal`,
    `breach_extra`) là quyết định của đề tài, in như bước nội bộ — không gắn căn cứ luật (không có trong Luật 91/2025,
    Nghị định 356/2025)."""
    bao = "Phát hiện vi phạm → " + (k.get("vi_pham_noi_bo") or (
        "người phát hiện báo ngay cho chủ nhiệm đề tài (bên kiểm soát dữ liệu)"
        + (" và người giám sát độc lập" if k.get("giam_sat") else "")))
    dong = [boc(bao, dau="   ∎ ", thut="     "), boc(f"{han}; {noi_dung}", dau="   ∎ ", thut="     ")]
    dong += [boc(x, dau="   ∎ ", thut="     ") for x in k.get("vi_pham_them") or []]
    dong.append("   ∎ Khắc phục và điều tra nguyên nhân, lưu hồ sơ xử lý")
    return "\n".join(dong)


def dong_chia_se(k: Mapping[str, Any]) -> str:
    """Mục 5 (Chia sẻ dữ liệu): lựa chọn đã quyết ⇒ đánh dấu đúng ô; chưa quyết ⇒ khuôn có ô chờ điền."""
    chon = k.get("chia_se")
    if chon not in CHIA_SE:
        return ("   ☐ Không chia sẻ (lý do: [CẦN])\n"
                "   ☐ Chia sẻ theo yêu cầu hợp lý (DTA cần ký trước)\n"
                "   ☐ Mở hoàn toàn sau ẩn danh hóa (tại: [CẦN — OSF/Zenodo...])\n"
                "   [CẦN BÁC SĨ CHỌN VÀ BIỆN MINH]")
    o = {c: "☑" if c == chon else "☐" for c in CHIA_SE}
    return (f"   {o['khong']} Không chia sẻ\n"
            f"   {o['theo_yeu_cau']} Chia sẻ theo yêu cầu hợp lý (DTA cần ký trước)\n"
            f"   {o['mo']} Mở hoàn toàn sau ẩn danh hóa")


# ── Tài liệu 7 — Checklist ───────────────────────────────────────────────────────────────────────────────────────────

def dong_ho_so_kem(k: Mapping[str, Any]) -> str:
    """Các hồ sơ kèm thêm đã khai (mỗi mục một ô ☐) — chuỗi rỗng khi không khai."""
    return "".join("\n" + boc(x, dau="☐ ", thut=" ") for x in k.get("ho_so_kem") or [])


# ── Đề cương nộp Hội đồng (mục đạo đức) ──────────────────────────────────────────────────────────────────────────────

def cau_de_cuong(k: Mapping[str, Any]) -> List[str]:
    """Dòng «Xung đột lợi ích» của đề cương nộp — dữ kiện hồ sơ + cách khai cá nhân; không bao giờ ghi «không có»."""
    ca_nhan = ("quan hệ tài chính và phi tài chính cá nhân của từng thành viên nhóm nghiên cứu do chính người đó "
               "tự khai và ký trong bản khai báo nộp kèm hồ sơ trình Hội đồng Đạo đức; xung đột lợi ích mới phát sinh "
               "được khai báo bổ sung với Hội đồng.")
    if not k.get("co_cau"):
        return ["- Xung đột lợi ích: " + ca_nhan[:1].upper() + ca_nhan[1:]]
    cau = k["co_cau"].rstrip(".") + "."
    if k.get("quan_ly"):
        cau += " Biện pháp quản lý: " + k["quan_ly"].rstrip(".") + "."
    return ["- Xung đột lợi ích: " + cau + " " + ca_nhan[:1].upper() + ca_nhan[1:]]
