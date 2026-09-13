#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xuat_phieu_ky_thang_diem.py — Sinh PHIẾU KÝ XÁC NHẬN CHUYÊN KHOA cho 32 thang
điểm/công cụ lâm sàng "verified" (app/clinical_scores/verified.py::VERIFIED_SCORES).

VÌ SAO CÓ (13/09/2026, bác sĩ yêu cầu "soạn sẵn tất cả nội dung để ký xác thực"
— tiếp nối mục #4 của báo cáo đề xuất nâng cấp cùng ngày):
====================================================================
Đề xuất #4 có hai phần: (a) ký xác nhận chuyên khoa cho danh mục đã kiểm định
— THUỘC THẨM QUYỀN bác sĩ chuyên khoa, KHÔNG thể tự động hoá; (b) thêm lịch
tái-kiểm định kỳ — đã xong (tools/kiem_do_tuoi_thang_diem.py + tác vụ cloud
kiem-thang-diem-quy). Công cụ NÀY chỉ chuẩn bị NỘI DUNG cho phần (a): gom mọi
dữ kiện ĐÃ CÓ SẴN và ĐÃ ĐƯỢC XÁC MINH trong hệ thống (công thức, ngưỡng, nguồn
gốc PMID/DOI, trạng thái rút bài đo được hôm nay) thành MỘT phiếu đọc-và-ký
cho bác sĩ chuyên khoa — để họ chỉ cần RÀ SOÁT rồi ký, không phải tự tra lại
từ đầu 32 nguồn.

TUYỆT ĐỐI KHÔNG tự ký, không tự đánh dấu "đã xác nhận", không bịa nội dung
chuyên môn nào ngoài dữ liệu đã có trong `VERIFIED_SCORES` — công cụ chỉ TRÌNH
BÀY LẠI dữ liệu đã tồn tại kèm ô ký trống thật (BH10: không tự gán quyết định
thay người có thẩm quyền).

Dùng:
    python tools/xuat_phieu_ky_thang_diem.py
    python tools/xuat_phieu_ky_thang_diem.py --ra reports/PHIEU_KY.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.clinical_scores.verified import VERIFIED_SCORES, citation_links  # noqa: E402

STATE_PATH = REPO_ROOT / "state" / "kiem-thang-diem-quy.json"
MAC_DINH_RA = REPO_ROOT / "reports" / "PHIEU_KY_XAC_NHAN_CHUYEN_KHOA_THANG_DIEM.md"

_NHAN_RUT_BAI = {
    "ok": "✅ Còn nguyên vẹn (đã kiểm rút bài)",
    "retracted": "🔴 ĐÃ BỊ RÚT — CẦN RÀ SOÁT TRƯỚC KHI KÝ",
    "expression_of_concern": "🟡 Expression of concern — CẦN RÀ SOÁT TRƯỚC KHI KÝ",
    "unresolved": "🔴 Không xác minh được (nghi định danh sai) — CẦN RÀ SOÁT",
    "unknown_mock_or_no_email": "⚠️ Chưa kiểm được (mạng/cấu hình)",
    "unknown_fetch_error": "⚠️ Chưa kiểm được (nguồn không trả lời)",
    "khong_co_dinh_danh": "⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay)",
}


def _doc_trang_thai_rut_bai() -> tuple[Optional[str], dict]:
    """Đọc sổ do tools/kiem_do_tuoi_thang_diem.py ghi — KHÔNG tự gọi mạng ở đây
    (công cụ này chỉ trình bày lại, không kiểm tra lại)."""
    if not STATE_PATH.exists():
        return None, {}
    try:
        so = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, {}
    theo_id: dict = {}
    for h in so.get("hang_muc", []):
        theo_id[h["score_id"]] = h.get("ket_qua", {})
    return so.get("checked_at"), theo_id


def _dong_field(nhan: str, gia_tri) -> str:
    if not gia_tri:
        return ""
    if isinstance(gia_tri, list):
        noi_dung = "\n".join(f"  - {x}" for x in gia_tri)
        return f"- **{nhan}:**\n{noi_dung}\n"
    return f"- **{nhan}:** {gia_tri}\n"


def sinh_noi_dung() -> str:
    checked_at, theo_id = _doc_trang_thai_rut_bai()
    hom_nay = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    dong: list[str] = []
    dong.append("# PHIẾU KÝ XÁC NHẬN CHUYÊN KHOA — 32 thang điểm/công cụ lâm sàng \"verified\"\n")
    dong.append(f"_Sinh tự động ngày {hom_nay} từ `app/clinical_scores/verified.py::VERIFIED_SCORES` "
                "— MỘT NGUỒN DUY NHẤT, không gõ tay lại. Sửa nội dung phải sửa file nguồn đó rồi "
                "sinh lại phiếu này, KHÔNG sửa tay bản `.md`/`.docx` đã xuất._\n")
    if checked_at:
        dong.append(f"_Trạng thái rút bài đo lần gần nhất: **{checked_at}** "
                    "(`python tools/kiem_do_tuoi_thang_diem.py`). Quá 120 ngày thì chạy lại trước khi "
                    "ký — chạy `--nhanh` để chỉ kiểm độ tươi, không tốn mạng._\n")
    else:
        dong.append("_⚠️ CHƯA CÓ dữ liệu rút bài — chạy `python tools/kiem_do_tuoi_thang_diem.py` "
                    "trước khi in phiếu này để cột trạng thái rút bài không rỗng._\n")

    dong.append("\n## Hướng dẫn cho người ký\n")
    dong.append(
        "Phiếu này **KHÔNG phải bằng chứng đã có ai xác nhận** — nó chỉ gom lại dữ liệu công thức/"
        "ngưỡng/nguồn gốc **đã có sẵn trong hệ thống** thành một bản để bác sĩ chuyên khoa RÀ SOÁT rồi "
        "TỰ TAY ký. Với mỗi thang điểm, xin xác nhận:\n"
        "1. Công thức/thành phần và ngưỡng hành động mô tả dưới đây còn ĐÚNG với thực hành hiện tại.\n"
        "2. Nguồn gốc (PMID/DOI) khớp đúng thang điểm đang dùng.\n"
        "3. Trạng thái rút bài (nếu 🔴/🟡) đã được đối chiếu — nếu có rút bài/expression of concern "
        "thật, XIN GHI RÕ QUYẾT ĐỊNH ở ô ghi chú (giữ nguyên/thay nguồn khác/ngừng dùng), KHÔNG chỉ ký "
        "cho qua.\n\n"
        "Ký = *\"Tôi, BS. ___________________, chuyên khoa ___________________, đã rà soát và xác nhận "
        "nội dung thang điểm này phù hợp áp dụng lâm sàng tại đơn vị.\"*\n"
    )

    dong.append("\n## Bảng tổng hợp nhanh (32 thang điểm)\n")
    dong.append("| # | Thang điểm | Lĩnh vực | PMID/DOI | Trạng thái rút bài | Ký |")
    dong.append("|---|---|---|---|---|---|")
    for i, s in enumerate(VERIFIED_SCORES, start=1):
        dinh_danh = s.get("pmid") or s.get("doi") or "—"
        trang_thai = theo_id.get(s["score_id"], {}).get("status")
        nhan_ngan = "⚪ chưa kiểm" if not checked_at else _NHAN_RUT_BAI.get(trang_thai, trang_thai or "—")
        dong.append(f"| {i} | {s['score_name']} | {s.get('clinical_area', '—')} | "
                    f"{dinh_danh} | {nhan_ngan} | ☐ |")
    dong.append("")

    dong.append("\n---\n\n## Chi tiết từng thang điểm\n")
    for i, s in enumerate(VERIFIED_SCORES, start=1):
        links = citation_links(s)
        trang_thai = theo_id.get(s["score_id"], {})
        nhan_rut_bai = (_NHAN_RUT_BAI.get(trang_thai.get("status"), trang_thai.get("status"))
                        if checked_at else "⚪ chưa kiểm — chạy tools/kiem_do_tuoi_thang_diem.py trước")

        dong.append(f"### {i}. {s['score_name']}  <sub>(`{s['score_id']}`)</sub>\n")
        dong.append(_dong_field("Lĩnh vực", s.get("clinical_area")))
        dong.append(_dong_field("Tình huống lâm sàng", s.get("clinical_situation")))
        dong.append(_dong_field("Mục đích sử dụng", s.get("purpose")))
        dong.append(_dong_field("Đối tượng áp dụng", s.get("target_population")))
        dong.append(_dong_field("Thành phần/tiêu chí", s.get("components")))
        dong.append(_dong_field("Cách tính", s.get("calculation_method")))
        dong.append(_dong_field("Diễn giải", s.get("interpretation")))
        dong.append(_dong_field("Ngưỡng hành động", s.get("action_thresholds")))
        dong.append(_dong_field("Xử trí lâm sàng", s.get("clinical_action")))
        dong.append(_dong_field("Hạn chế", s.get("limitations")))
        dong.append(_dong_field("Nguồn gốc", s.get("source")))
        dong.append(_dong_field("Guideline tham chiếu", s.get("guideline_reference")))
        if links.get("pubmed"):
            dong.append(f"- **PubMed:** {links['pubmed']}\n")
        if links.get("doi"):
            dong.append(f"- **DOI:** {links['doi']}\n")
        if not s.get("pmid") and not s.get("doi"):
            dong.append("- **Định danh tự kiểm chứng:** KHÔNG CÓ — nguồn là báo cáo thể chế/sách, "
                        "bác sĩ tự đối chiếu bản gốc bằng tay.\n")
        dong.append(f"- **Trạng thái rút bài (đo tự động):** {nhan_rut_bai}\n")
        dong.append(
            "\n**Ô KÝ XÁC NHẬN:**\n\n"
            "☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.\n"
            "☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.\n\n"
            "Ghi chú (nếu có): ______________________________________________\n\n"
            "Chữ ký: ________________________  Ngày: ____________\n"
        )
        dong.append("\n---\n")

    dong.append(
        "\n## Ký tổng kết\n\n"
        "Tôi, BS. ______________________________, chuyên khoa ______________________________, "
        "đơn vị ______________________________, đã rà soát toàn bộ 32 thang điểm/công cụ lâm sàng "
        "liệt kê trên. Các mục còn treo (nếu có, xem ghi chú từng mục) đã được xử lý theo quyết định "
        "ghi rõ ở trên, không có mục nào còn để ngỏ mà chưa quyết định.\n\n"
        "Chữ ký: ________________________________  Ngày ký: ____________\n\n"
        "_Cần bác sĩ kiểm chứng — phiếu này là bản trình bày lại dữ liệu đã có, không thay thế việc "
        "bác sĩ tự đọc và đối chiếu nguồn gốc trước khi ký._\n"
    )
    return "\n".join(dong)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--ra", type=Path, default=MAC_DINH_RA, help="File .md đầu ra")
    args = ap.parse_args()

    noi_dung = sinh_noi_dung()
    args.ra.parent.mkdir(parents=True, exist_ok=True)
    args.ra.write_text(noi_dung, encoding="utf-8")
    print(f"✅ Đã sinh phiếu ký: {args.ra}")
    print(f"   {len(VERIFIED_SCORES)} thang điểm. Chạy tiếp để có bản .docx Times New Roman:")
    print(f"   python \"{REPO_ROOT.parent}/tools/md_sang_docx_times.py\" \"{args.ra}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
