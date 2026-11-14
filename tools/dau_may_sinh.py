"""dau_may_sinh.py — DẤU BẢN MÁY SINH cho hồ sơ do máy soạn (G2 hồ sơ đạo đức, G4 SAP) — K6, 14/11/2026.

VÌ SAO CÓ MÔ-ĐUN NÀY
--------------------
Rào chống đè của run_g2_auto/run_g4_auto (01/09/2026) đoán «bác sĩ đã biên tập» bằng cách ĐẾM nhãn [CẦN…]/ô trống:
bản đang có ít ô trống hơn bản máy sắp sinh ⇒ coi là đã biên tập ⇒ từ chối đè (mã 2). Giả lập đề tài RCT 14/11/2026
(báo cáo K6) lộ chỗ sai của phép đếm: đề tài bị suy nhầm thiết kế cắt ngang rồi PI sửa sang RCT; hồ sơ RCT vốn có
NHIỀU mục hơn nên bản máy sinh cho thiết kế CŨ (chưa ai đụng tới) có «91 vs 92 nhãn [CẦN…]» ⇒ bị coi là đã biên tập ⇒
hệ từ chối sinh lại hồ sơ đúng thiết kế mới, pipeline dừng ở mã 2.

CÁCH MỚI
--------
Mỗi lần máy GHI bản .md, lưu SHA-256 của ĐÚNG nội dung đã ghi cùng các đầu vào quyết định (thiết kế, N) vào tệp
`exports/<đề tài>/_dau_may_sinh/<tên tệp>.json`. Lượt chạy sau so nội dung hiện tại với dấu đó:

- KHỚP dấu        ⇒ bản máy sinh NGUYÊN, chưa ai sửa ⇒ được sinh lại (vẫn sao lưu .bak-*), kể cả khi thiết kế/N đã đổi.
- LỆCH dấu        ⇒ đã có người sửa tay (hoặc công cụ khác ghi đè) ⇒ GIỮ nguyên, báo lý do và cờ sinh lại có chủ đích.
- KHÔNG có dấu    ⇒ hồ sơ sinh trước bản vá này (vd đề tài thật C1a) ⇒ nơi gọi dùng LUẬT CŨ (đếm nhãn), hành vi cũ
                    giữ nguyên từng chi tiết.

Mô-đun chỉ đọc/ghi tệp dấu, không in gì, không đụng nội dung hồ sơ. Dấu chỉ là BẰNG CHỨNG «máy đã ghi đúng nội dung
này»; nó không phải chữ ký và không thay sổ cái phê duyệt (approve_gate).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

# Tên thư mục chứa dấu, nằm trong thư mục đề tài. Tiền tố «_» theo quy ước tài liệu nội bộ (không phải sản phẩm nộp).
THU_MUC_DAU = "_dau_may_sinh"
PHIEN_BAN_DAU = 1

# Ba kết luận của phép so dấu.
MAY_SINH_NGUYEN = "MAY_SINH_NGUYEN"  # nội dung hiện tại khớp đúng bản máy ghi lần trước
DA_SUA_TAY = "DA_SUA_TAY"  # có dấu nhưng nội dung đã khác ⇒ có người/công cụ khác sửa
KHONG_CO_DAU = "KHONG_CO_DAU"  # chưa có dấu (hồ sơ cũ) hoặc tệp dấu hỏng ⇒ nơi gọi tự dùng luật cũ


def bam_noi_dung(noi_dung: str) -> str:
    """SHA-256 (hex) của nội dung văn bản; quy CRLF/CR về LF để đổi kiểu xuống dòng không bị coi là «đã sửa»."""
    chuan = noi_dung.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(chuan.encode("utf-8")).hexdigest()


def duong_dan_dau(tep_ho_so: Path) -> Path:
    """Đường dẫn tệp dấu của một hồ sơ: <thư mục hồ sơ>/_dau_may_sinh/<tên hồ sơ>.json."""
    tep_ho_so = Path(tep_ho_so)
    return tep_ho_so.parent / THU_MUC_DAU / f"{tep_ho_so.name}.json"


def _chuan_dau_vao(dau_vao: Optional[Mapping[str, Any]]) -> dict:
    """Chuẩn hoá đầu vào để so: N = 0 hoặc rỗng nghĩa là «chưa có N» (None)."""
    ra: dict = {}
    for khoa, gia_tri in dict(dau_vao or {}).items():
        if khoa == "n" and not gia_tri:
            gia_tri = None
        ra[str(khoa)] = gia_tri
    return ra


def ghi_dau(tep_ho_so: Path, noi_dung: str, dau_vao: Optional[Mapping[str, Any]], cong_cu: str) -> Path:
    """Ghi dấu cho nội dung máy VỪA ghi vào `tep_ho_so`. Ghi qua tệp tạm rồi thay thế (không để dấu dở dang)."""
    dich = duong_dan_dau(tep_ho_so)
    dich.parent.mkdir(parents=True, exist_ok=True)
    ban_ghi = {
        "phien_ban": PHIEN_BAN_DAU,
        "tep": Path(tep_ho_so).name,
        "sha256": bam_noi_dung(noi_dung),
        "dau_vao": _chuan_dau_vao(dau_vao),
        "sinh_luc": datetime.now().replace(microsecond=0).isoformat(),
        "cong_cu": cong_cu,
        "ghi_chu": ("Dấu bản MÁY SINH (K6, 14/11/2026): nội dung hồ sơ khớp sha256 này ⇒ chưa ai sửa, máy được sinh "
                    "lại; lệch ⇒ đã có người sửa, máy GIỮ nguyên. Không phải chữ ký, không thay sổ cái phê duyệt."),
    }
    tam = dich.with_name(dich.name + ".tmp")
    tam.write_text(json.dumps(ban_ghi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tam, dich)
    return dich


def doc_dau(tep_ho_so: Path) -> Optional[dict]:
    """Đọc dấu của hồ sơ; vắng, hỏng JSON hoặc thiếu sha256 ⇒ None (nơi gọi coi như KHÔNG CÓ DẤU)."""
    p = duong_dan_dau(tep_ho_so)
    if not p.exists():
        return None
    try:
        ban_ghi = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(ban_ghi, dict) or not isinstance(ban_ghi.get("sha256"), str) or len(ban_ghi["sha256"]) != 64:
        return None
    return ban_ghi


def so_cai_co_duyet_trung_noi_dung(so_cai: Path, gate_id: str, tep_ho_so: Path) -> bool:
    """Sổ cái phê duyệt có bản ghi APPROVED của `gate_id` mà evidence_hash TRÙNG SHA-256 nội dung hồ sơ hiện tại không.

    Chỉ dùng cho quyết định GIỮ (sửa sau thẩm định #248, mục «thấp»): GC.ledger_approved() fail-closed theo chiều
    «đã duyệt» — máy thiếu khoá xác minh hoặc con dấu niêm phong hỏng thì trả False ⇒ nhánh «không đè bản đã ký» không
    kích hoạt và máy đè hồ sơ/SAP người đã ký nguyên trạng. Với việc GIỮ, đi theo chiều BẢO TOÀN: có dấu vết APPROVED
    trùng nội dung là giữ, KHÔNG xác minh chữ ký. Hàm này không mở cổng nào và không bao giờ được dùng để kết luận
    «đã duyệt» — chỉ thêm khả năng giữ lại (PI vẫn sinh lại có chủ đích được bằng --regenerate). Băm đúng cách
    approve_gate/ledger_approved băm: SHA-256 của BYTES tệp (không quy đổi xuống dòng). Sổ vắng/hỏng/dị dạng ⇒ False
    (luật dấu bình thường quyết)."""
    try:
        ban_ghi = json.loads(Path(so_cai).read_text(encoding="utf-8"))
        bam = hashlib.sha256(Path(tep_ho_so).read_bytes()).hexdigest()
    except (OSError, ValueError, UnicodeDecodeError):
        return False
    if not isinstance(ban_ghi, list):
        return False
    cong = str(gate_id or "").strip().casefold()
    for rec in ban_ghi:
        if not isinstance(rec, dict):
            continue
        if (str(rec.get("gate_id") or "").strip().casefold() == cong
                and str(rec.get("decision") or "").strip().upper() == "APPROVED"
                and str(rec.get("evidence_hash") or "").strip().lower() == bam):
            return True
    return False


def xet_ban_hien_co(tep_ho_so: Path, noi_dung_hien_tai: str,
                    dau_vao_moi: Optional[Mapping[str, Any]]) -> dict:
    """So nội dung hồ sơ hiện tại với dấu bản máy sinh lần trước.

    Trả dict:
      trang_thai — MAY_SINH_NGUYEN | DA_SUA_TAY | KHONG_CO_DAU
      dau_vao_cu — đầu vào lúc máy sinh lần trước (None nếu không có dấu)
      doi        — {khoá: (cũ, mới)} các đầu vào đã đổi kể từ lần máy sinh (rỗng nếu không đổi/không có dấu)
      sinh_luc   — thời điểm máy sinh lần trước (None nếu không có dấu)
    """
    ban_ghi = doc_dau(tep_ho_so)
    if ban_ghi is None:
        return {"trang_thai": KHONG_CO_DAU, "dau_vao_cu": None, "doi": {}, "sinh_luc": None}
    cu = ban_ghi.get("dau_vao") if isinstance(ban_ghi.get("dau_vao"), dict) else {}
    moi = _chuan_dau_vao(dau_vao_moi)
    doi = {k: (cu.get(k), moi.get(k)) for k in sorted(set(cu) | set(moi)) if cu.get(k) != moi.get(k)}
    khop = bam_noi_dung(noi_dung_hien_tai) == ban_ghi["sha256"]
    return {"trang_thai": MAY_SINH_NGUYEN if khop else DA_SUA_TAY, "dau_vao_cu": cu, "doi": doi,
            "sinh_luc": ban_ghi.get("sinh_luc")}


def quyet_dinh_ghi_de(tep_ho_so: Path, noi_dung_cu: str, dau_vao_moi: Optional[Mapping[str, Any]], *,
                      ep_sinh_lai: bool, cu_day_du_hon_theo_luat_cu: bool, chi_tiet_luat_cu: str = "",
                      da_ky: Optional[Callable[[], bool]] = None,
                      thiet_ke_cu_checkpoint: Optional[str] = None) -> dict:
    """Quyết định máy được ĐÈ hồ sơ đang có hay phải GIỮ — một luật chung cho G2 và G4.

    Thứ tự:
      1. Cờ sinh lại có chủ đích (--regenerate) ⇒ đè (nơi gọi đã sao lưu .bak-* trước).
      2. Khớp dấu (bản máy sinh nguyên) ⇒ đè — trừ khi chính nội dung này đã được KÝ trong sổ cái phê duyệt
         (`da_ky()` True): luật mới không được hạ cấp quyết định đã ký, nên vẫn GIỮ. Nơi gọi (G2/G4) nối
         `da_ky` = GC.ledger_approved(...) HOẶC so_cai_co_duyet_trung_noi_dung(...) — chiều bảo toàn khi máy thiếu khoá.
      3. Lệch dấu ⇒ GIỮ (đã có người sửa tay).
      4. Không có dấu (hồ sơ cũ) ⇒ luật cũ do nơi gọi tính (`cu_day_du_hon_theo_luat_cu`).

    Trả dict: giu (bool), ly_do (câu ngắn, rỗng khi đè), trang_thai, doi ({khoá: (cũ, mới)}), mo_ta_doi (str),
    ghi_chu (câu giải thích vì sao được đè, để nơi gọi in).
    """
    xet = xet_ban_hien_co(tep_ho_so, noi_dung_cu, dau_vao_moi)
    trang_thai, doi = xet["trang_thai"], dict(xet["doi"])
    moi = _chuan_dau_vao(dau_vao_moi)
    if trang_thai == KHONG_CO_DAU and thiet_ke_cu_checkpoint and thiet_ke_cu_checkpoint != moi.get("design_code"):
        # Hồ sơ cũ không có dấu: thiết kế lúc sinh lấy tạm từ checkpoint lượt trước — chỉ để BÁO, không để quyết.
        doi["design_code"] = (thiet_ke_cu_checkpoint, moi.get("design_code"))
    ra = {"giu": False, "ly_do": "", "trang_thai": trang_thai, "doi": doi, "mo_ta_doi": mo_ta_doi(doi),
          "ghi_chu": ""}
    if ep_sinh_lai:
        ra["ghi_chu"] = "sinh lại CÓ CHỦ ĐÍCH theo cờ --regenerate (bản cũ đã sao lưu .bak-*)"
    elif trang_thai == MAY_SINH_NGUYEN:
        if da_ky is not None and da_ky():
            ra.update(giu=True, ly_do=("bản đang có khớp dấu bản máy sinh NHƯNG chính nội dung này đã được ký trong "
                                       "sổ cái phê duyệt (approval_ledger.json có bản ghi APPROVED trùng SHA-256) — "
                                       "máy không tự đè bản đã ký"))
        else:
            ra["ghi_chu"] = ("bản đang có là bản MÁY SINH NGUYÊN (khớp dấu SHA-256 lần sinh trước, chưa ai sửa) — "
                             + (f"đầu vào đã đổi ({ra['mo_ta_doi']}), tự sinh lại" if doi
                                else "sinh lại theo thượng nguồn hiện hành"))
    elif trang_thai == DA_SUA_TAY:
        ra.update(giu=True, ly_do="nội dung khác bản máy sinh lần trước (lệch dấu SHA-256) — đã có người sửa tay")
    elif cu_day_du_hon_theo_luat_cu:
        ra.update(giu=True, ly_do=("chưa có dấu bản máy sinh (hồ sơ sinh trước 14/11/2026) và bản đang có ít ô trống "
                                   "hơn bản máy sắp sinh" + (f" ({chi_tiet_luat_cu})" if chi_tiet_luat_cu else "")
                                   + " — coi như đã biên tập"))
    return ra


def mo_ta_doi(doi: Mapping[str, Any]) -> str:
    """Câu ngắn mô tả đầu vào đã đổi, vd «thiết kế: cross_sectional → rct; N: 482 → 218»."""
    ten = {"design_code": "thiết kế", "n": "N"}
    phan = []
    for khoa, cap in doi.items():
        cu, moi = cap
        phan.append(f"{ten.get(khoa, khoa)}: {cu if cu is not None else '—'} → {moi if moi is not None else '—'}")
    return "; ".join(phan)


def dong_cuoi_giu_ban_bien_tap(cong: str, study: str, quyet_dinh: Mapping[str, Any], lenh: str) -> list:
    """ĐÚNG 6 dòng in CUỐI CÙNG khi cổng giữ bản đã biên tập (thoát mã 2).

    run_pipeline lấy 6 dòng cuối stdout của cổng làm lời giải thích khi cổng thoát mã 2 và in dòng đầu cạnh tên cổng —
    nên dòng đầu phải nói được LÝ DO và CỜ sinh lại, không phải một dòng thủ tục không liên quan (K6)."""
    ly_do = str(quyet_dinh.get("ly_do") or "bản đang có được coi là đã biên tập")
    doi = str(quyet_dinh.get("mo_ta_doi") or "")
    return [
        f"🟡 {cong} GIỮ bản đã biên tập, không sinh lại (mã 2) — lý do: {ly_do}. Sinh lại có chủ đích: --regenerate",
        (f"   ⚠ Đầu vào đã đổi kể từ lần máy sinh: {doi} — bản đang giữ có thể lệch thiết kế/cỡ mẫu hiện hành."
         if doi else "   Đầu vào (thiết kế, N) không đổi kể từ lần máy sinh, hoặc chưa có dấu để so."),
        f"   Sinh lại (bản cũ đã sao lưu .bak-*): python3 {lenh} --study {study} --regenerate",
        "   Bí danh cũ vẫn nhận: --regenerate-artifact (G2) · --regenerate-sap (G4).",
        f"   Chỉ cần .docx chuẩn từ bản đã biên tập: python3 tools/xuat_docx_chuan.py --study {study}",
        f"   Checkpoint {cong} đã làm mới theo thượng nguồn hiện hành.",
    ]


def khoi_checkpoint(quyet_dinh: Mapping[str, Any], giu: bool, dau_vao: Optional[Mapping[str, Any]]) -> dict:
    """Khối `sinh_lai` ghi vào checkpoint cổng (máy đọc được): lượt này sinh lại hay giữ, vì sao, cờ cần dùng.

    Chỉ để BÁO — không phải `needs_input`: giữ bản đã biên tập là trạng thái bình thường của đề tài thật, đánh dấu
    «chặn» sẽ làm pipeline chạy lại cổng mãi."""
    return {
        "giu_ban_bien_tap": bool(giu),
        "trang_thai_dau": str(quyet_dinh.get("trang_thai") or "CHUA_CO_BAN_CU"),
        "ly_do": str(quyet_dinh.get("ly_do") or quyet_dinh.get("ghi_chu") or ""),
        "dau_vao_doi": str(quyet_dinh.get("mo_ta_doi") or ""),
        "dau_vao_hien_hanh": _chuan_dau_vao(dau_vao),
        "co_sinh_lai": "--regenerate",
    }
