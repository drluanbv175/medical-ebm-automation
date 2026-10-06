#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BỘ DÒ PII DÙNG CHUNG cho VĂN BẢN và GIÁ TRỊ TRƯỜNG của hồ sơ nghiên cứu (CHUNG-G, soát từng cổng 04/10/2026).

VÌ SAO CÓ. Rà soát 11 cổng thấy không cổng nào quét PII trên `study_meta.json` (gate_params do bác sĩ gõ tay) hay
trên NỘI DUNG HIỆN HÀNH của hồ sơ (G2 chỉ quét bản lúc sinh, guardrail lưu trong checkpoint có thể cũ hai tháng);
mỗi nơi tự viết một danh sách mẫu khác nhau (run_g0_auto R2, clinical_checkpoint._PII_PATTERNS, import_real_dataset
PII_PATTERNS, app_data_analysis…) và có nơi báo đỏ nhầm chính số phê duyệt IRB thật. Mô-đun này gom các mẫu đã được
kiểm ở những nơi đó thành MỘT hàm, có hai chế độ:

  • che_do="chat"  — GIÁ TRỊ TRƯỜNG/đoạn ngắn người gõ (gate_params, chủ đề G0, quần thể): ở đây KHÔNG được có ngày
    tháng cụ thể, số điện thoại, email, số căn cước, số thẻ BHYT, nhãn «họ tên bệnh nhân/ngày sinh…». Bắt cả hình
    dạng, không chỉ nhãn (mẫu từ run_g0_auto R2 + import_real_dataset).
  • che_do="ho_so" — TÀI LIỆU dài (đề cương, ICF, bản thảo): ngày tháng và thông tin LIÊN HỆ của nghiên cứu viên/Hội
    đồng là hợp lệ nên KHÔNG bắt ngày trơn, SĐT, email; chỉ bắt thứ chỉ có thể là định danh NGƯỜI BỆNH: số căn cước
    (liền hoặc nhóm 3-3-3(-3)), số thẻ BHYT, «ngày sinh» + một ngày cụ thể, nhãn tên bệnh nhân + một tên.

  `mien` = các giá trị CHÍNH XÁC được miễn (vd số phê duyệt IRB thật `attestation.approval_number`, mã đăng ký) — miễn
  theo chuỗi khớp, không theo loại.

Kết quả là danh sách `PhatHienPII(loai, mau_che)` — `mau_che` đã CHE phần giữa (không in lại PII đầy đủ vào báo cáo).
Cố ý thiên về NHẠY ở chế độ «chat» (dương tính giả chỉ khiến cổng giữ REVIEW để người xem lại), thiên về ĐẶC HIỆU ở chế
độ «ho_so» (tài liệu dài nhiều số hợp lệ). Không thay khử định danh dữ liệu (`quan-ly-du-lieu`, import_real_dataset).
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, List

CHAT = "chat"
HO_SO = "ho_so"

_NHAN_CHAT = ("tên bệnh nhân", "họ tên", "họ và tên", "ngày sinh", "cccd", "cmnd", "căn cước", "số hồ sơ",
              "số bhyt", "thẻ bhyt", "bảo hiểm y tế số", "địa chỉ nhà", "số điện thoại", "mã bệnh nhân")

# Số dài đi sau các tiền tố định danh HỌC THUẬT không phải PII (PMID, NCT, DOI, ISBN, ISSN, mã IRB/ethics).
_TIEN_TO_HOC_THUAT = re.compile(r"(?:pmid|pmcid|nct|doi|isbn|issn|irb|ethics|hđđđ|đăng ký|registration)[\s:#./-]*$",
                                re.IGNORECASE)

# Số tiền (kinh phí «150000000 đồng») không phải số căn cước.
_HAU_TO_TIEN = re.compile(r"\s*(?:đ\b|đồng|vnđ|vnd|usd|\$)", re.IGNORECASE)

_MAU_HINH: dict[str, tuple[tuple[str, re.Pattern[str]], ...]] = {
    CHAT: (
        ("ngày tháng cụ thể", re.compile(r"(?<!\d)(?:\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)\d{2}"
                                         r"|(?:19|20)\d{2}[/\-]\d{1,2}[/\-]\d{1,2})(?!\d)")),
        ("số căn cước (nhóm)", re.compile(r"(?<!\d)\d{3}[\s.\-]\d{3}[\s.\-]\d{3}(?:[\s.\-]\d{3})?(?!\d)")),
        ("số căn cước", re.compile(r"(?<!\d)(?:\d{9}|\d{12})(?!\d)")),
        ("số điện thoại", re.compile(r"(?<!\d)\(?(?:\+?84|0)\)?(?:[\s.\-()]{0,3}\d){8,10}(?!\d)")),
        ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
        ("số thẻ BHYT", re.compile(r"\b[A-Z]{2}\d{13}\b")),
    ),
    HO_SO: (
        ("số căn cước (nhóm)", re.compile(r"(?<!\d)\d{3}[\s.\-]\d{3}[\s.\-]\d{3}[\s.\-]\d{3}(?!\d)")),
        ("số căn cước", re.compile(r"(?<![\d.,/])\d{12}(?![\d.,/])")),
        ("số thẻ BHYT", re.compile(r"\b[A-Z]{2}\d{13}\b")),
        ("ngày sinh cụ thể", re.compile(r"ngày\s+sinh\s*[:：]?\s*\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)\d{2}",
                                        re.IGNORECASE)),
        ("tên người bệnh", re.compile(r"(?:họ\s+(?:và\s+)?tên|tên)\s+(?:bệnh\s+nhân|người\s+bệnh|BN)\s*[:：]\s*"
                                      r"[A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4}")),
    ),
}


@dataclass(frozen=True)
class PhatHienPII:
    """Một chỗ nghi PII: loại + mẫu ĐÃ CHE (không in lại PII đầy đủ)."""

    loai: str
    mau_che: str


def che(s: str) -> str:
    """Che phần giữa: giữ 2 ký tự đầu và 2 ký tự cuối (chuỗi ≤ 4 ký tự che hết)."""
    s = str(s)
    return "*" * len(s) if len(s) <= 4 else s[:2] + "*" * (len(s) - 4) + s[-2:]


def _van_ban(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, dict):
        return "\n".join(f"{k}: {_van_ban(x)}" for k, x in v.items())
    if isinstance(v, (list, tuple, set)):
        return "\n".join(_van_ban(x) for x in v)
    return unicodedata.normalize("NFC", str(v))


def quet_pii_van_ban(van_ban: Any, *, che_do: str = CHAT, mien: Iterable[str] = ()) -> List[PhatHienPII]:
    """Danh sách chỗ nghi PII trong văn bản/giá trị (dict/list duyệt đệ quy). Rỗng ⇒ không thấy (không phải «chắc chắn
    sạch»). `mien`: các chuỗi CHÍNH XÁC được miễn (số IRB thật, mã đăng ký)."""
    if che_do not in _MAU_HINH:
        raise ValueError(f"che_do phải là {CHAT!r} hoặc {HO_SO!r}")
    vb = _van_ban(van_ban)
    if not vb.strip():
        return []
    mien_set = {unicodedata.normalize("NFC", str(m)).strip() for m in mien if str(m or "").strip()}
    ra: List[PhatHienPII] = []
    da_thay: set = set()
    if che_do == CHAT:
        thuong = vb.lower()
        for nhan in _NHAN_CHAT:
            if nhan in thuong and ("nhãn", nhan) not in da_thay:
                da_thay.add(("nhãn", nhan))
                ra.append(PhatHienPII(f"nhãn định danh «{nhan}»", nhan))
    for loai, mau in _MAU_HINH[che_do]:
        for m in mau.finditer(vb):
            khop = m.group(0).strip()
            if any(khop in x or x in khop for x in mien_set):
                continue
            if loai.startswith("số căn cước") and (_TIEN_TO_HOC_THUAT.search(vb[max(0, m.start() - 24):m.start()])
                                                  or _HAU_TO_TIEN.match(vb[m.end():m.end() + 8])):
                continue
            if (loai, khop) in da_thay:
                continue
            da_thay.add((loai, khop))
            ra.append(PhatHienPII(loai, che(khop)))
    return ra


def tom_tat(phat_hien: Iterable[PhatHienPII], toi_da: int = 4) -> str:
    """Một dòng bằng chứng cho báo cáo cổng (đã che)."""
    ds = list(phat_hien)
    if not ds:
        return "không thấy mẫu PII"
    phan = [f"{p.loai} ({p.mau_che})" for p in ds[:toi_da]]
    return "; ".join(phan) + (f"; …+{len(ds) - toi_da}" if len(ds) > toi_da else "")
