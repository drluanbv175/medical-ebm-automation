"""Bước 5: Clinical synthesis – tạo tóm tắt lâm sàng theo mẫu cố định.

KHÔNG bịa số liệu hiệu quả/chi phí. Chỉ tóm tắt từ metadata sẵn có và nêu rõ
mức chứng cứ + lý do (chưa) nên thay đổi thực hành. Mọi mục đều có link truy vết.
"""
from __future__ import annotations

from typing import Dict

from app.services.extraction import extract_clinical_points, extract_pico


def synthesize(item: Dict) -> Dict[str, str]:
    """Tạo dict synthesis theo các trường mẫu của đề bài."""
    classification = item.get("classification", "watch_only")
    actionable = item.get("is_actionable", False)
    area = item.get("clinical_area") or "Chưa phân loại"
    title = item.get("title", "")

    if actionable:
        practice_change = "Có – cân nhắc thay đổi thực hành nếu phù hợp bối cảnh."
        action = ("Cân nhắc áp dụng theo guideline / nội dung nguồn gốc; đối chiếu bối cảnh "
                  "và từng bệnh nhân cụ thể trước khi triển khai.")
        not_yet = ""
    elif classification == "need_full_text":
        practice_change = "Chưa chắc – cần đọc toàn văn/guideline gốc."
        action = "Đọc toàn văn, đối chiếu guideline nền trước khi quyết định."
        not_yet = item.get("reason_for_exclusion") or "Cần thêm dữ liệu/toàn văn."
    elif classification == "excluded":
        practice_change = "Không – loại khỏi báo cáo chính."
        action = "Lưu vào mục theo dõi, không đưa vào checklist thực hành."
        not_yet = item.get("reason_for_exclusion") or ""
    else:  # watch_only
        practice_change = "Chưa – chỉ theo dõi."
        action = "Theo dõi cập nhật tiếp theo (RCT/guideline/phân tích an toàn)."
        not_yet = item.get("reason_for_exclusion") or "Chứng cứ chưa đủ để thay đổi thực hành."

    evidence_level = item.get("operational_evidence_level") or "Không xác định"
    if item.get("official_grade"):
        evidence_level += f" | GRADE nguồn: {item['official_grade']}"

    src = item.get("url") or item.get("doi") or item.get("pmid") or "Không có link"

    # Trích NGUYÊN VĂN các câu mang tín hiệu lâm sàng từ abstract (không bịa).
    diem_chinh = extract_clinical_points(item.get("abstract") or "")
    pico = extract_pico(item.get("abstract") or "")

    # Nếu trích được câu đối tượng/an toàn nguyên văn -> ưu tiên dùng (truy vết tốt hơn).
    doi_tuong = (item.get("population")
                 or (diem_chinh.get("doi_tuong") or [None])[0]
                 or _infer_population(item))
    canh_bao = (item.get("safety_signal")
                or (diem_chinh.get("an_toan") or [None])[0]
                or "Không có cảnh báo an toàn đặc biệt.")

    return {
        "cau_hoi_lam_sang": f"[{area}] Thông tin mới về: {title[:120]}",
        "thong_tin_moi": (item.get("abstract") or "")[:600] or "(Không có abstract)",
        "doi_tuong_ap_dung": doi_tuong,
        "muc_chung_cu": evidence_level,
        "co_thay_doi_thuc_hanh": practice_change,
        "hanh_dong_de_xuat": action,
        "canh_bao_can_trong": canh_bao,
        "nguon_truy_vet": str(src),
        "ly_do_chua_doi_thuc_hanh": not_yet,
        "diem_chinh": diem_chinh,  # {nhóm: [câu nguyên văn]} – trích từ abstract
        "pico": pico,              # {P|I|C|O: [câu nguyên văn]} – tóm tắt theo PICO
    }


def _infer_population(item: Dict) -> str:
    area = item.get("clinical_area") or ""
    return f"Người bệnh thuộc chuyên khoa {area} (xem chi tiết trong nguồn gốc)." if area \
        else "Chưa rõ đối tượng – xem nguồn gốc."
