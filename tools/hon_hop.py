#!/usr/bin/env python3
"""Thiết kế HỖN HỢP định lượng–định tính (mixed methods) trên chuỗi G0–G10 (17/11/2026).

Vì sao có: giả lập đo được `mixed_methods` nằm ngoài 8 mã thiết kế ⇒ G1-AUTO-02c chặn; hệ không có cách nào chạy một đề
tài hỗn hợp. Kiến trúc chọn (giữ nguyên hợp đồng 8 mã của gate_contract): đề tài mang MÃ THIẾT KẾ của CẤU PHẦN ĐỊNH
LƯỢNG (rct/cohort/cross_sectional/…) — cổng G3/G4/G6 chạy trên cấu phần đó như mọi đề tài; CẤU PHẦN ĐỊNH TÍNH và kế
hoạch TÍCH HỢP khai ở `gate_params.G1.mixed_methods`. Đề cương nộp in mục thiết kế hỗn hợp, hướng dẫn phỏng vấn của
cấu phần định tính và bảng tích hợp (joint display); báo cáo theo GRAMMS (O'Cathain 2008) + chuẩn của từng cấu phần.

Ba thiết kế lõi (Creswell & Plano Clark): song song hội tụ · giải thích tuần tự (định lượng → định tính) · khám phá
tuần tự (định tính → định lượng).

Khối `gate_params.G1.mixed_methods`:
  thiet_ke            hoi_tu | giai_thich_tuan_tu | kham_pha_tuan_tu
  ly_do               vì sao cần cả hai cấu phần (GRAMMS 1)
  uu_tien             ngang_nhau | dinh_luong | dinh_tinh (GRAMMS 2)
  cau_phan_dinh_tinh  {muc_tieu [số thứ tự mục tiêu G1 do cấu phần định tính trả lời], central_phenomenon,
                       qualitative_approach, chon_mau, co_mau_du_kien, data_collection_method, saturation_criterion,
                       phan_tich, interview_guide?}  (GRAMMS 3)
  tich_hop            {thoi_diem, cach, nguoi}  (GRAMMS 4 — tích hợp ở đâu, bằng cách nào, ai làm)

Lệnh:  python3 tools/hon_hop.py --study <mã>   (kiểm khối; mã 0 đạt · 1 thiếu/sai · 2 đề tài không khai hỗn hợp)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]

THIET_KE = {
    "hoi_tu": ("song song hội tụ (convergent)",
               "hai cấu phần được thu thập trong cùng giai đoạn, phân tích riêng rồi so sánh và hợp nhất kết quả"),
    "giai_thich_tuan_tu": ("giải thích tuần tự (explanatory sequential)",
                           "cấu phần định lượng được thực hiện trước; cấu phần định tính tiếp theo nhằm giải thích "
                           "kết quả định lượng"),
    "kham_pha_tuan_tu": ("khám phá tuần tự (exploratory sequential)",
                         "cấu phần định tính được thực hiện trước để xây dựng công cụ hoặc giả thuyết; cấu phần định "
                         "lượng tiếp theo nhằm kiểm định"),
}
UU_TIEN = {"ngang_nhau": "hai cấu phần có vai trò ngang nhau", "dinh_luong": "cấu phần định lượng là chính",
           "dinh_tinh": "cấu phần định tính là chính"}
CAN_DINH_TINH = ("central_phenomenon", "qualitative_approach", "chon_mau", "data_collection_method",
                 "saturation_criterion", "phan_tich")
CAN_TICH_HOP = ("thoi_diem", "cach", "nguoi")
# Chuẩn báo cáo của đề tài hỗn hợp — PMID đã tra PubMed 17/11/2026: GRAMMS (O'Cathain A, Murphy E, Nicholl J. J Health
# Serv Res Policy 2008;13(2):92-8, doi:10.1258/jhsrp.2007.007074) · COREQ (Tong A, Sainsbury P, Craig J. Int J Qual
# Health Care 2007;19(6):349-57, doi:10.1093/intqhc/mzm042). Bản thảo G7 dẫn kèm PMID ⇒ A12 kiểm rút bài.
PMID_CHUAN = ("18416914", "17872937")


#: 22/11/2026 (COREQ 2007, SRQR 2014 — đối chiếu bản in lại toàn văn bảng gốc): dữ kiện quy trình định tính chủ nhiệm
#: chốt khi thiết kế, cùng tên khoá cho đề tài định tính (`gate_params.G1`) và cấu phần định tính của đề tài hỗn hợp
#: (`gate_params.G1.mixed_methods.cau_phan_dinh_tinh`). (khoá, nhãn trong văn bản, việc cần khai khi còn trống, mục
#: chuẩn). Đề cương nộp và bản thảo G7 đọc CÙNG danh sách này — thêm khoá ở đây thì cả hai văn bản cùng có.
KHOA_QUY_TRINH_DINH_TINH = (
    ("research_paradigm", "Hệ hình nghiên cứu", "hệ hình nghiên cứu và lý do chọn", "SRQR S5"),
    ("interviewer", "Người phỏng vấn", "ai trực tiếp phỏng vấn, công việc, bằng cấp, giới, kinh nghiệm và tập huấn, "
                                       "quan hệ với người tham gia trước nghiên cứu", "COREQ 1–6"),
    ("participant_information", "Thông tin người tham gia được biết",
     "người tham gia được biết gì về người phỏng vấn và mục đích nghiên cứu", "COREQ 7"),
    ("researcher_reflexivity", "Phản tư của người nghiên cứu",
     "giả định, mối quan tâm với chủ đề và cách nhóm nghiên cứu xử lý ảnh hưởng của mình", "COREQ 8, SRQR S6"),
    ("participant_approach", "Cách tiếp cận người tham gia", "mời trực tiếp, qua điện thoại, thư hay email",
     "COREQ 11"),
    ("non_participation", "Người từ chối hoặc rút lui", "cách ghi số người từ chối hoặc rút lui và lý do", "COREQ 13"),
    ("interview_setting", "Nơi phỏng vấn và người có mặt", "nơi thu thập dữ liệu và có người khác có mặt không",
     "COREQ 14–15"),
    ("interview_guide_pilot", "Hướng dẫn phỏng vấn", "bộ hướng dẫn phỏng vấn, đã thử trước chưa, có thay đổi trong "
                                                    "quá trình thu thập không", "COREQ 17, SRQR S11"),
    ("repeat_interviews", "Số lần phỏng vấn", "mỗi người được phỏng vấn mấy lần", "COREQ 18"),
    ("recording_field_notes", "Ghi âm và ghi chép thực địa", "thiết bị ghi âm hoặc ghi hình và ghi chép thực địa",
     "COREQ 19–20"),
    ("transcript_return", "Gửi lại bản gỡ băng", "có gửi lại bản gỡ băng cho người tham gia không", "COREQ 23"),
    ("coding_process", "Mã hoá và phân tích", "số người mã hoá, bộ mã, cách hình thành chủ đề, phần mềm, kiểm tra lại "
                                             "với người tham gia", "COREQ 24–28"),
)


def nguon_dinh_tinh(meta: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Khối khai quy trình định tính của đề tài: cấu phần định tính nếu đề tài hỗn hợp, không thì `gate_params.G1`
    khi mã thiết kế là «qualitative»; đề tài không có định tính ⇒ {}."""
    if khoi(meta):
        return dinh_tinh(meta)
    g1 = (((meta or {}).get("gate_params") or {}).get("G1") or {}) if isinstance(meta, Mapping) else {}
    return g1 if isinstance(g1, dict) and str(g1.get("design") or "") == "qualitative" else {}


def khoi(meta: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    g1 = (((meta or {}).get("gate_params") or {}).get("G1") or {}) if isinstance(meta, Mapping) else {}
    k = g1.get("mixed_methods")
    return k if isinstance(k, dict) else {}


def _co(v: Any) -> bool:
    s = str(v or "").strip()
    return bool(s) and "[CẦN" not in s.upper()


def kiem(meta: Optional[dict]) -> List[str]:
    """Lỗi của khối hỗn hợp theo GRAMMS (rỗng = đạt; đề tài không khai hỗn hợp ⇒ rỗng)."""
    k = khoi(meta)
    if not k:
        return []
    loi: List[str] = []
    if k.get("thiet_ke") not in THIET_KE:
        loi.append(f"thiet_ke phải thuộc {sorted(THIET_KE)} (GRAMMS 2)")
    if not _co(k.get("ly_do")):
        loi.append("thiếu ly_do — vì sao cần cả hai cấu phần (GRAMMS 1)")
    if k.get("uu_tien") not in UU_TIEN:
        loi.append(f"uu_tien phải thuộc {sorted(UU_TIEN)} (GRAMMS 2)")
    dt = k.get("cau_phan_dinh_tinh") if isinstance(k.get("cau_phan_dinh_tinh"), dict) else {}
    loi += [f"cau_phan_dinh_tinh thiếu «{x}» (GRAMMS 3)" for x in CAN_DINH_TINH if not _co(dt.get(x))]
    so_mt = len(((meta or {}).get("gate_params") or {}).get("G1", {}).get("objectives") or []) if isinstance(
        meta, dict) else 0
    mt = dt.get("muc_tieu")
    if not isinstance(mt, list) or not mt or not all(isinstance(x, int) and x >= 1 for x in mt):
        loi.append("cau_phan_dinh_tinh thiếu «muc_tieu» — danh sách số thứ tự mục tiêu G1 do cấu phần định tính trả "
                   "lời, vd [2] (GRAMMS 3)")
    elif so_mt and max(mt) > so_mt:
        loi.append(f"cau_phan_dinh_tinh.muc_tieu {mt} vượt số mục tiêu G1 đã chốt ({so_mt})")
    th = k.get("tich_hop") if isinstance(k.get("tich_hop"), dict) else {}
    loi += [f"tich_hop thiếu «{x}» (GRAMMS 4)" for x in CAN_TICH_HOP if not _co(th.get(x))]
    g1 = ((meta or {}).get("gate_params") or {}).get("G1") or {}
    if str(g1.get("design") or "") in ("qualitative", "mixed_methods"):
        loi.append("mã thiết kế của đề tài hỗn hợp phải là mã của CẤU PHẦN ĐỊNH LƯỢNG (rct/cohort/cross_sectional/…); "
                   "cấu phần định tính khai trong mixed_methods")
    return loi


def muc_tieu_dinh_tinh(meta: Optional[Mapping[str, Any]]) -> frozenset:
    """Số thứ tự mục tiêu G1 do cấu phần định tính của đề tài hỗn hợp trả lời — các mục tiêu này được phủ bởi cấu
    phần định tính và SAP §17, không đòi biến định lượng trong ma trận mục tiêu–biến (MT-03/MT-04)."""
    mt = dinh_tinh(meta).get("muc_tieu")
    return frozenset(x for x in mt if isinstance(x, int) and x >= 1) if isinstance(mt, list) else frozenset()


def mo_ta(meta: Optional[dict]) -> Dict[str, str]:
    """Tên thiết kế, mô tả trình tự và mức ưu tiên bằng lời (cho đề cương)."""
    k = khoi(meta)
    ten, mt = THIET_KE.get(str(k.get("thiet_ke") or ""), ("", ""))
    return {"ten": ten, "mo_ta": mt, "uu_tien": UU_TIEN.get(str(k.get("uu_tien") or ""), "")}


def dinh_tinh(meta: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    k = khoi(meta)
    return k.get("cau_phan_dinh_tinh") if isinstance(k.get("cau_phan_dinh_tinh"), dict) else {}


def tich_hop(meta: Optional[dict]) -> Dict[str, Any]:
    k = khoi(meta)
    return k.get("tich_hop") if isinstance(k.get("tich_hop"), dict) else {}


def chu_de_tich_hop(meta: Optional[dict]) -> List[Dict[str, str]]:
    """Các dòng của bảng tích hợp (joint display) dự kiến: {chu_de, dinh_luong, dinh_tinh}. Chủ nhiệm khai
    `tich_hop.chu_de`; chưa khai ⇒ một dòng dựng từ kết cục chính và hiện tượng trung tâm."""
    th = tich_hop(meta)
    ds: List[Dict[str, str]] = []
    for x in th.get("chu_de") or []:
        if isinstance(x, dict) and _co(x.get("chu_de")):
            ds.append({"chu_de": str(x.get("chu_de")).strip(), "dinh_luong": str(x.get("dinh_luong") or "").strip(),
                       "dinh_tinh": str(x.get("dinh_tinh") or "").strip()})
    if not ds:
        g1 = ((meta or {}).get("gate_params") or {}).get("G1") or {}
        kc = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), dict) else {}
        ds.append({"chu_de": str(kc.get("name") or "Kết cục chính").strip(),
                   "dinh_luong": str(kc.get("name") or "").strip(),
                   "dinh_tinh": str(dinh_tinh(meta).get("central_phenomenon") or "").strip()})
    return ds


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm khối thiết kế hỗn hợp (GRAMMS).")
    ap.add_argument("--study", required=True)
    a = ap.parse_args(argv)
    try:
        meta = json.loads((BASE / "exports" / a.study / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("Không đọc được study_meta.json")
        return 2
    if not khoi(meta):
        print("Đề tài không khai thiết kế hỗn hợp (gate_params.G1.mixed_methods).")
        return 2
    loi = kiem(meta)
    for x in loi:
        print(f"  ✗ {x}")
    print("✓ Khối thiết kế hỗn hợp đủ mục GRAMMS" if not loi else f"{len(loi)} mục cần bổ sung")
    return 0 if not loi else 1


if __name__ == "__main__":
    raise SystemExit(main())
