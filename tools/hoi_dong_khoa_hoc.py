#!/usr/bin/env python3
"""Hội đồng Khoa học MÁY cấp đề tài — chấm đề cương như một hội đồng thật, qua Claude Batch API (22/11/2026).

VÌ SAO (bác sĩ 22/11/2026): «Nội dung có đúng chuẩn, đề cương có đúng chuẩn, đề tài nghiên cứu có đúng chuẩn hay tất
cả các vấn đề của hệ thống nghiên cứu có đúng chuẩn hay không thì vẫn do hội đồng chấm. Hãy xây dựng cho tôi hội đồng
đúng chuẩn tốt nhất và kết hợp API Claude». Hệ đã có hội đồng CỔNG (`hoi_dong_cong[_batch].py`: chấm từng NHIỆM VỤ của
một cổng theo RQ1–RQ8) và phản biện máy MỘT người đọc (`phan_bien_may_de_cuong.py`). Chưa có hội đồng CẤP ĐỀ TÀI chấm
trọn đề cương theo đúng thể thức Hội đồng Khoa học — đó là công cụ này.

Thể thức (mô phỏng Hội đồng Khoa học xét đề cương; mục chấm = «Phiếu nhận xét», Phụ lục 2 hướng dẫn chung bác sĩ gửi
21/11/2026 — cùng bảng `goi_bao_ve_hoi_dong.TIEU_CHI_PHIEU`):
- Năm thành viên CHẤM ĐỘC LẬP (mỗi người một yêu cầu, không thấy điểm người khác — tránh neo điểm): Phản biện 1
  (phương pháp luận), Phản biện 2 (chuyên môn lâm sàng), Uỷ viên thống kê, Uỷ viên đạo đức–pháp lý–liêm chính, Uỷ viên
  tổng quan–trích dẫn. Mỗi người chấm mục 1–4 của phiếu (thang 1–5 có mô tả mốc) và nêu tồn tại (mục 5).
- MỌI nhận xét phải trích NGUYÊN VĂN đề cương kèm số dòng; MÁY kiểm lại (`api_claude_nc.co_nguyen_van` trong cửa sổ
  ±3 dòng). Không khớp ⇒ «máy không xác minh được», KHÔNG vào biên bản như lỗi (liệt kê riêng, không giấu).
- Chủ tịch (bước 2) đọc các nhận xét ĐÃ xác minh: gộp trùng, phán từng nhận xét giữ/hạ mức/loại (chỉ được HẠ, không
  nâng, không thêm nhận xét mới), viết nhận xét chung và thứ tự yêu cầu chỉnh sửa.
- Thư ký là MÁY tất định: điểm trung vị từng mục, độ lệch giữa thành viên, KẾT LUẬN theo luật cố định
  (`ket_luan_tat_dinh`) — model không tự tuyên kết luận.
- Hồ sơ kiểm máy (K17 theo từng mục chuẩn, K1–K17, nhất quán xuyên cổng) phát kèm cho mọi thành viên để hội đồng dành
  sức cho PHÁN ĐOÁN chuyên môn, không đếm lại cái máy đã đếm.
- HIỆU CHUẨN (`hieu-chuan`): cài lỗi đã biết vào một BẢN SAO đề cương (đáp án lưu riêng), cho hội đồng chấm bản sao,
  rồi đo tỷ lệ bắt lỗi — chất lượng hội đồng phải chứng minh bằng số, không bằng lời tự khen.

Model: mặc định Claude Opus 5.5, `effort=high` + suy nghĩ thích ứng; Batch API (−50%) + cache prompt cho phần đề cương
dùng chung (mọi thành viên cùng một tiền tố ⇒ đọc cache 0,05×). Ước chi phí: `uoc-tinh` (0 gọi API).

Ranh giới: TƯ VẤN — không thay Hội đồng Khoa học/Hội đồng Đạo đức thật, không mở/chặn cổng, không ký, không ghi
gate_params/sổ cái, không sửa đề cương. Triệu tập tính phí là quyết định của bác sĩ: `hop` chạy khô mặc định,
`--goi-api` mới nộp/lấy batch; `bien-ban --ap-dung` mới ghi biên bản.

Dùng:
  hoi_dong_khoa_hoc.py uoc-tinh  --study <mã> [--tep <md>]
  hoi_dong_khoa_hoc.py hop       --study <mã> [--tep <md>] [--goi-api] [--lam-lai]   # lặp tới «xong»
  hoi_dong_khoa_hoc.py bien-ban  --study <mã> [--tep <md>] [--ap-dung]
  hoi_dong_khoa_hoc.py hieu-chuan --study <mã> --tao | --cham
Mã thoát: 0 xong bước · 1 có phần không hợp lệ · 2 không gọi được API · 3 tham số sai · 4 batch đang xử lý.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import api_claude_nc as API  # noqa: E402

SCHEMA = "hoi_dong_khoa_hoc/v1"
CONG_CU = "tools/hoi_dong_khoa_hoc.py"
THU_MUC = "hoi_dong_khoa_hoc"
MODEL_MAC_DINH = "claude-opus-5-5"
EFFORT = "high"
MAX_TOKENS_TV = 24000
MAX_TOKENS_CT = 24000
TOKEN_RA_UOC = 7000          # ước token ra mỗi thành viên (gồm suy nghĩ) — để báo chi phí điển hình, không phải trần
CUA_SO_DONG = 3              # trích phải nằm trong ±3 dòng quanh số dòng thành viên nêu
MUC_DO = ("nghiem_trong", "can_sua", "goi_y")
KET_LUAN = {"thong_qua": "Thông qua", "thong_qua_co_sua": "Thông qua sau khi chỉnh sửa",
            "khong_thong_qua": "Không thông qua (chỉnh sửa lớn, trình lại)"}
# Mục chấm điểm của Phiếu nhận xét (mục 5 «Tồn tại và đề xuất» là danh sách nhận xét, không chấm điểm).
MUC_PHIEU = {"1": "Tính cấp thiết, ý nghĩa khoa học và thực tiễn",
             "2": "Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật",
             "3": "Dự kiến kết quả",
             "4": "Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)"}
MOC_DIEM = ("5 — Xuất sắc: đáp ứng đầy đủ chuẩn, không còn điểm cần sửa.\n"
            "4 — Tốt: chỉ còn góp ý nhỏ (mức «goi_y»).\n"
            "3 — Đạt: có điểm cần sửa nhưng không ảnh hưởng tính hợp lệ khoa học.\n"
            "2 — Chưa đạt: thiếu sót ảnh hưởng tính hợp lệ hoặc khả thi, phải sửa trước khi thông qua.\n"
            "1 — Không đạt: thiếu sót nghiêm trọng hoặc thiếu hẳn nội dung.")
# Chuẩn chung được phép dẫn (ngoài chuẩn báo cáo theo thiết kế do K17 xác định cho từng đề cương).
CHUAN_CHUNG = ("Helsinki", "CIOMS", "ICH E6", "ICH E9", "Luật 91/2025", "Nghị định 13/2023", "Vancouver", "ICMJE",
               "SAMPL", "GRADE", "COPE", "EQUATOR", "WHO TRDS", "Phiếu nhận xét")

THANH_VIEN: Tuple[Dict[str, Any], ...] = (
    {"ma": "pb1", "vai": "Phản biện 1 — Phương pháp luận nghiên cứu", "trong_tam": ("2", "3"),
     "nhiem_vu": "thiết kế có phù hợp câu hỏi và mục tiêu không; kiểm soát sai lệch chọn, đo lường, nhiễu; quần thể, "
                 "tiêu chuẩn chọn–loại, kỹ thuật chọn mẫu; định nghĩa biến và kết cục; công cụ đo (COSMIN khi có thang "
                 "đo); đề cương đáp ứng TỪNG mục của chuẩn báo cáo áp dụng cho thiết kế (danh sách ở hồ sơ kiểm máy)."},
    {"ma": "pb2", "vai": "Phản biện 2 — Chuyên môn lâm sàng", "trong_tam": ("1", "2", "3"),
     "nhiem_vu": "tính cấp thiết và ý nghĩa lâm sàng; định nghĩa bệnh, kết cục, ngưỡng có đúng TIÊU CHUẨN của nguồn "
                 "được dẫn (vd định nghĩa theo guideline nào, thời gian kéo dài bao lâu); tính khả thi tại cơ sở ngoại "
                 "trú Việt Nam; kết quả dự kiến có dùng được cho thực hành không."},
    {"ma": "uv_tk", "vai": "Uỷ viên — Thống kê sinh học", "trong_tam": ("2", "3"),
     "nhiem_vu": "công thức cỡ mẫu đúng thiết kế, tham số có nguồn, tính lại ra đúng N; kế hoạch phân tích (kiểm "
                 "định/mô hình đúng loại biến, biến hiệu chỉnh có lý do, dữ liệu thiếu, đa so sánh, phân tích độ nhạy, "
                 "phân tích nhóm nhỏ định trước); khung bảng dự kiến khớp mục tiêu; trình bày số theo SAMPL."},
    {"ma": "uv_dd", "vai": "Uỷ viên — Đạo đức, pháp lý và liêm chính nghiên cứu", "trong_tam": ("2", "4"),
     "nhiem_vu": "đồng thuận tham gia (hoặc lý do miễn), quyền rút lui, rủi ro–lợi ích, bảo vệ dữ liệu cá nhân (Luật "
                 "91/2025), khử định danh, lưu trữ–huỷ, xung đột lợi ích, nguồn kinh phí, đăng ký nghiên cứu; theo "
                 "Helsinki, CIOMS, ICH E6(R3). Đây là ý kiến tư vấn — KHÔNG thay Hội đồng Đạo đức."},
    {"ma": "uv_tl", "vai": "Uỷ viên — Tổng quan tài liệu và trích dẫn", "trong_tam": ("1", "4"),
     "nhiem_vu": "tổng quan cập nhật, đủ nghiên cứu then chốt trong và ngoài nước; khoảng trống có căn cứ; MỌI con số "
                 "và khẳng định ở đặt vấn đề/tổng quan có trích dẫn; trích dẫn đúng thứ tự Vancouver, tài liệu khớp "
                 "câu khẳng định; văn bản rõ ràng, nhất quán, không mâu thuẫn giữa các chương."},
)


class LoiThamSo(ValueError):
    """Tham số sai — mã 3."""


# ── văn bản & hồ sơ kiểm máy ─────────────────────────────────────────────────────────────────────────────────────────
def tep_mac_dinh(study: str, goc: Path = REPO) -> Path:
    return goc / "exports" / study / f"DE_CUONG_NOP_HOI_DONG_{study}.md"


def danh_so_dong(van: str) -> str:
    return "\n".join(f"{i}| {d}" for i, d in enumerate(van.splitlines(), 1))


def _sha(van: str) -> str:
    return hashlib.sha256(van.encode("utf-8")).hexdigest()


def _thiet_ke(out_dir: Path) -> str:
    try:
        meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
        return str(((meta.get("gate_params") or {}).get("G1") or {}).get("design") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


def ho_so_kiem_may(study: str, out_dir: Path, van: str, la_ban_chinh: bool) -> Dict[str, Any]:
    """Kết quả các bộ kiểm TẤT ĐỊNH phát kèm cho hội đồng. Bộ nào lỗi ⇒ ghi «không đo được», không bao giờ ghi «đạt»."""
    ra: Dict[str, Any] = {"thiet_ke": _thiet_ke(out_dir)}
    try:
        import kiem_chuan_de_cuong_theo_muc as K17  # noqa: PLC0415

        dc = K17.doi_chieu(van, ra["thiet_ke"])
        ra["chuan_ap_dung"] = [c for c, _ in dc["chuan"]]
        thieu = [r for r in dc["ket_qua"] if r.trang_thai in ("thieu", "canh_bao")]
        ra["k17"] = {"dat": sum(1 for r in dc["ket_qua"] if r.trang_thai == "dat"), "thieu": len(thieu),
                     "muc_thieu": [f"{r.chuan} {r.ma} — {r.chu_de}" for r in thieu][:40],
                     "chua_do": [f"{c}: {ly}" for c, ly in dc["chua_do"]]}
    except Exception as exc:  # noqa: BLE001
        ra["chuan_ap_dung"] = []
        ra["k17"] = f"không đo được ({type(exc).__name__})"
    if la_ban_chinh:
        try:
            import kiem_de_cuong_nop_hoi_dong as KDC  # noqa: PLC0415

            ra["k1_k17"] = KDC.kiem(out_dir, study)[:40]
        except Exception as exc:  # noqa: BLE001
            ra["k1_k17"] = f"không đo được ({type(exc).__name__})"
        try:
            import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

            kq = NQ.doi_chieu(out_dir, study)
            ra["nhat_quan"] = {"tong": kq.get("tong"),
                               "can_luu_y": [{"ten": x.get("ten"), "muc": x.get("muc"), "ghi_chu": x.get("ghi_chu")}
                                             for x in kq.get("thong_so") or [] if x.get("muc") != "khop"]}
        except Exception as exc:  # noqa: BLE001
            ra["nhat_quan"] = f"không đo được ({type(exc).__name__})"
    else:
        ra["k1_k17"] = "không chạy (tài liệu không phải bản đề cương nộp chính thức của đề tài)"
    return ra


def khoi_chung(study: str, ten_tep: str, van: str, ho_so: Dict[str, Any]) -> str:
    """Tiền tố DÙNG CHUNG cho mọi thành viên và chủ tịch (được cache): đề cương đánh số dòng + hồ sơ kiểm máy."""
    return (f"BẠN LÀ THÀNH VIÊN HỘI ĐỒNG KHOA HỌC xét đề cương đề tài «{study}» (hội đồng MÁY, tư vấn — không thay hội "
            "đồng thật). Tài liệu được giao là đề cương nộp Hội đồng, mỗi dòng mang số «n| ».\n\n"
            f"=== TÀI LIỆU: {ten_tep} ===\n{danh_so_dong(van)}\n=== HẾT TÀI LIỆU ===\n\n"
            "=== HỒ SƠ KIỂM MÁY (bộ kiểm tất định; «không đo được» KHÔNG có nghĩa là đạt) ===\n"
            f"{json.dumps(ho_so, ensure_ascii=False, indent=1, default=str)}\n=== HẾT HỒ SƠ ===\n")


def _khuon_tv() -> str:
    return json.dumps({
        "diem": {"1": "số nguyên 1–5", "2": "…", "3": "…", "4": "…"},
        "ly_do_diem": {"1": "một–hai câu, nói căn cứ", "2": "…", "3": "…", "4": "…"},
        "phat_hien": [{"muc_phieu": "1|2|3|4", "muc_do": "nghiem_trong|can_sua|goi_y", "dong": "số dòng",
                       "trich": "NGUYÊN VĂN một đoạn ngắn của dòng đó (chép đúng từng chữ)",
                       "van_de": "điều chưa đạt, nói cụ thể",
                       "chuan": "chuẩn + mục nếu có (vd «STROBE 12d»), không thì «»",
                       "de_xuat": "sửa cụ thể thế nào"}],
        "diem_manh": ["…"], "ket_luan": "thong_qua|thong_qua_co_sua|khong_thong_qua"}, ensure_ascii=False, indent=1)


def loi_nhan_thanh_vien(tv: Dict[str, Any]) -> str:
    return (f"VAI CỦA BẠN: {tv['vai']}.\nTRỌNG TÂM: {tv['nhiem_vu']}\n\n"
            "Chấm ĐỘC LẬP — bạn không biết ý kiến thành viên khác. Chấm cả bốn mục của Phiếu nhận xét, nhưng nhận xét "
            f"chuyên sâu ở mục {', '.join(tv['trong_tam'])}:\n"
            + "\n".join(f"  {k}. {v}" for k, v in MUC_PHIEU.items())
            + f"\nMốc điểm (dùng ĐÚNG mốc):\n{MOC_DIEM}\n\n"
            "LUẬT BẮT BUỘC:\n"
            "1. Mỗi nhận xét phải có «dong» và «trich» chép NGUYÊN VĂN từ đúng dòng đó — máy sẽ đối chiếu, trích không "
            "khớp thì nhận xét bị loại. Nhận xét về điều THIẾU: trích dòng nơi lẽ ra phải có (tiêu đề mục).\n"
            "2. Điểm 1–2 ở mục nào phải có ít nhất một nhận xét «nghiem_trong» hoặc «can_sua» ở mục đó; đã có "
            "«can_sua» thì không chấm 5.\n"
            "3. Không bịa số liệu, nguồn, mục chuẩn; không đòi điều chuẩn không đòi. Không đánh giá lại lựa chọn thuộc "
            "thẩm quyền chủ nhiệm khi lựa chọn đó có lý do ghi trong đề cương — chỉ nêu khi lý do sai hoặc thiếu.\n"
            "4. Không nhắc lại lỗi mà hồ sơ kiểm máy đã liệt kê trừ khi bạn có thêm điều máy không thấy.\n"
            "5. Không ghi thông tin định danh cá nhân.\n"
            "Trả về DUY NHẤT một đối tượng JSON theo khuôn:\n" + _khuon_tv())


def loi_nhan_chu_tich(ds: Sequence[Dict[str, Any]], bang_diem: Dict[str, Dict[str, int]]) -> str:
    gon = [{k: f[k] for k in ("id", "thanh_vien", "muc_phieu", "muc_do", "dong", "trich", "van_de", "chuan", "de_xuat")}
           for f in ds]
    return ("VAI CỦA BẠN: CHỦ TỊCH HỘI ĐỒNG. Năm thành viên đã chấm độc lập; dưới đây là các nhận xét ĐÃ được máy xác "
            "minh trích nguyên văn, và bảng điểm.\nNHIỆM VỤ:\n"
            "1. Với TỪNG nhận xét: «giu», «ha_muc» (chỉ được HẠ: nghiem_trong→can_sua→goi_y) hoặc «loai» (báo động giả "
            "— đề cương thật ra đã đáp ứng ở chỗ khác: nêu số dòng đó; hoặc đòi điều chuẩn không đòi). Mỗi phán quyết "
            "kèm lý do có căn cứ trong tài liệu.\n"
            "2. Gộp các nhận xét trùng ý (cùng một vấn đề) thành nhóm.\n"
            "3. Viết «nhan_xet_chung» (3–6 câu, khách quan) và «yeu_cau_chinh_sua» theo thứ tự ưu tiên.\n"
            "Bạn KHÔNG thêm nhận xét mới, KHÔNG nâng mức, KHÔNG sửa điểm, KHÔNG tuyên kết luận (máy tính theo luật).\n"
            f"NHẬN XÉT:\n{json.dumps(gon, ensure_ascii=False, indent=1)}\n"
            f"BẢNG ĐIỂM:\n{json.dumps(bang_diem, ensure_ascii=False)}\n"
            "Trả về DUY NHẤT JSON: " + json.dumps({
                "phan_quyet": [{"id": "F01", "quyet": "giu|ha_muc|loai", "muc_do_moi": "chỉ khi ha_muc",
                                "ly_do": "…"}],
                "gop": [["F01", "F07"]], "nhan_xet_chung": "…", "yeu_cau_chinh_sua": ["…"]}, ensure_ascii=False))


# ── yêu cầu API ─────────────────────────────────────────────────────────────────────────────────────────────────────
def tham_so_yeu_cau(chung: str, loi_nhan: str, model: str, max_tokens: int) -> Dict[str, Any]:
    p = API.tham_so(loi_nhan, he_thong=chung, model=model, max_tokens=max_tokens, effort=EFFORT, cache_he_thong=True)
    if p["model"] in API.MODEL_HIEN_HANH:
        p["thinking"] = {"type": "adaptive"}
    return p


def yeu_cau_thanh_vien(chung: str, model: str, sha8: str) -> List[Tuple[str, Dict[str, Any]]]:
    return [(f"{tv['ma']}_{sha8}", tham_so_yeu_cau(chung, loi_nhan_thanh_vien(tv), model, MAX_TOKENS_TV))
            for tv in THANH_VIEN]


# ── xác minh (máy) ──────────────────────────────────────────────────────────────────────────────────────────────────
_SO_DIEN_THOAI = re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")


def _trong_cua_so(trich: str, dong: int, cac_dong: Sequence[str]) -> bool:
    if not (1 <= dong <= len(cac_dong)):
        return False
    a, b = max(0, dong - 1 - CUA_SO_DONG), min(len(cac_dong), dong + CUA_SO_DONG)
    return API.co_nguyen_van(trich, "\n".join(cac_dong[a:b]))


def _chuan_hop_le(chuan: str, chuan_ap_dung: Sequence[str]) -> bool:
    c = (chuan or "").strip()
    if not c:
        return True
    ten = [x.split()[0] for x in chuan_ap_dung if x and x != "(không xác định)"] + list(CHUAN_CHUNG)
    return any(t.casefold() in c.casefold() for t in ten)


def xac_minh_thanh_vien(ma: str, dl: Any, van: str, chuan_ap_dung: Sequence[str]) -> Dict[str, Any]:
    """Chuẩn hoá + kiểm một bản chấm. Trả {'diem', 'ly_do_diem', 'dat': [...], 'khong_xac_minh': [...], 'canh_bao'}."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("bản chấm không phải đối tượng JSON")
    cac_dong = van.splitlines()
    diem: Dict[str, int] = {}
    for k in MUC_PHIEU:
        v = (dl.get("diem") or {}).get(k)
        if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5:
            raise API.KetQuaHong(f"điểm mục {k} không hợp lệ: {v!r}")
        diem[k] = v
    dat, khong, canh_bao = [], [], []
    for f in dl.get("phat_hien") or []:
        if not isinstance(f, dict):
            continue
        g = {"thanh_vien": ma, "muc_phieu": str(f.get("muc_phieu") or "").strip(),
             "muc_do": str(f.get("muc_do") or "").strip(), "trich": str(f.get("trich") or "").strip(),
             "van_de": str(f.get("van_de") or "").strip(), "chuan": str(f.get("chuan") or "").strip(),
             "de_xuat": str(f.get("de_xuat") or "").strip()}
        try:
            g["dong"] = int(f.get("dong"))
        except (TypeError, ValueError):
            g["dong"] = 0
        ly = []
        if g["muc_phieu"] not in MUC_PHIEU:
            ly.append("mục phiếu không hợp lệ")
        if g["muc_do"] not in MUC_DO:
            ly.append("mức độ không hợp lệ")
        if not g["van_de"] or not g["de_xuat"]:
            ly.append("thiếu vấn đề hoặc đề xuất")
        if not _trong_cua_so(g["trich"], g["dong"], cac_dong):
            ly.append("trích không có nguyên văn quanh dòng đã nêu")
        if any(_SO_DIEN_THOAI.search(g[k]) for k in ("van_de", "de_xuat", "trich")):
            ly.append("có chuỗi giống số điện thoại (PII)")
        if not _chuan_hop_le(g["chuan"], chuan_ap_dung):
            g["chuan_goc"], g["chuan"] = g["chuan"], ""
            canh_bao.append(f"{ma}: chuẩn «{g['chuan_goc']}» ngoài danh mục áp dụng — bỏ nhãn chuẩn, giữ nhận xét")
        (khong if ly else dat).append({**g, "ly_do_loai": "; ".join(ly)} if ly else g)
    for k, v in diem.items():
        nang = [x for x in dat if x["muc_phieu"] == k and x["muc_do"] in ("nghiem_trong", "can_sua")]
        if v <= 2 and not nang:
            canh_bao.append(f"{ma}: điểm {v} mục {k} không có nhận xét nghiêm trọng/cần sửa đã xác minh")
        if v == 5 and nang:
            canh_bao.append(f"{ma}: điểm 5 mục {k} trong khi có nhận xét cần sửa")
    kl = str(dl.get("ket_luan") or "").strip()
    return {"diem": diem, "ly_do_diem": dl.get("ly_do_diem") or {}, "dat": dat, "khong_xac_minh": khong,
            "canh_bao": canh_bao, "diem_manh": [str(x) for x in (dl.get("diem_manh") or [])][:8],
            "ket_luan": kl if kl in KET_LUAN else ""}


def ap_phan_quyet(ds: Sequence[Dict[str, Any]], dl: Any) -> Dict[str, Any]:
    """Áp phán quyết của chủ tịch (chỉ hạ/loại, không thêm). Thiếu phán quyết cho một nhận xét ⇒ GIỮ (fail-safe)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("phán quyết chủ tịch không phải đối tượng JSON")
    theo_id = {f["id"]: dict(f) for f in ds}
    loai, canh_bao = [], []
    for pq in dl.get("phan_quyet") or []:
        if not isinstance(pq, dict) or pq.get("id") not in theo_id:
            canh_bao.append(f"phán quyết trỏ id không có: {pq.get('id') if isinstance(pq, dict) else pq!r}")
            continue
        f, quyet, ly = theo_id[pq["id"]], str(pq.get("quyet") or ""), str(pq.get("ly_do") or "").strip()
        if quyet == "loai":
            if not ly:
                canh_bao.append(f"{f['id']}: loại mà không có lý do — giữ nguyên")
                continue
            loai.append({**f, "ly_do_chu_tich": ly})
            del theo_id[f["id"]]
        elif quyet == "ha_muc":
            moi = str(pq.get("muc_do_moi") or "")
            if moi in MUC_DO and MUC_DO.index(moi) > MUC_DO.index(f["muc_do"]):
                f.update(muc_do_goc=f["muc_do"], muc_do=moi, ly_do_chu_tich=ly)
            else:
                canh_bao.append(f"{f['id']}: «hạ mức» không hợp lệ ({f['muc_do']}→{moi}) — giữ nguyên")
        elif quyet != "giu":
            canh_bao.append(f"{f['id']}: phán quyết lạ «{quyet}» — giữ nguyên")
    nhom = [[i for i in g if i in theo_id] for g in (dl.get("gop") or []) if isinstance(g, list)]
    return {"giu": list(theo_id.values()), "loai": loai, "gop": [g for g in nhom if len(g) > 1],
            "nhan_xet_chung": str(dl.get("nhan_xet_chung") or "").strip(),
            "yeu_cau_chinh_sua": [str(x) for x in (dl.get("yeu_cau_chinh_sua") or [])][:20], "canh_bao": canh_bao}


def _nhom_dai_dien(giu: Sequence[Dict[str, Any]], gop: Sequence[Sequence[str]]) -> List[Dict[str, Any]]:
    """Một vấn đề = một dòng: nhóm gộp lấy nhận xét có mức NẶNG NHẤT làm đại diện."""
    trong_nhom = {i for g in gop for i in g}
    ra = [f for f in giu if f["id"] not in trong_nhom]
    theo_id = {f["id"]: f for f in giu}
    for g in gop:
        cac = [theo_id[i] for i in g if i in theo_id]
        if cac:
            dd = min(cac, key=lambda f: MUC_DO.index(f["muc_do"]))
            ra.append({**dd, "gop_voi": [f["id"] for f in cac if f is not dd]})
    return sorted(ra, key=lambda f: (MUC_DO.index(f["muc_do"]), f["muc_phieu"], f["dong"]))


def ket_luan_tat_dinh(van_de: Sequence[Dict[str, Any]], trung_vi: Dict[str, float]) -> Tuple[str, str]:
    """LUẬT CỐ ĐỊNH của thư ký máy (không phải quy định của bệnh viện — luật nội bộ để kết luận tái lập được):
    - Không thông qua: ≥ 3 vấn đề nghiêm trọng còn giữ, HOẶC trung vị mục 1 hoặc 2 ≤ 2.
    - Thông qua sau khi chỉnh sửa: ≥ 1 vấn đề nghiêm trọng/cần sửa còn giữ, HOẶC trung vị mục nào ≤ 3.
    - Thông qua: còn lại."""
    nt = sum(1 for f in van_de if f["muc_do"] == "nghiem_trong")
    cs = sum(1 for f in van_de if f["muc_do"] == "can_sua")
    if nt >= 3 or min(trung_vi.get("1", 5), trung_vi.get("2", 5)) <= 2:
        return "khong_thong_qua", (f"{nt} vấn đề nghiêm trọng; trung vị mục 1 = {trung_vi.get('1')}, "
                                   f"mục 2 = {trung_vi.get('2')}")
    if nt or cs or min(trung_vi.values()) <= 3:
        return "thong_qua_co_sua", (f"{nt} vấn đề nghiêm trọng, {cs} vấn đề cần sửa; "
                                    f"trung vị thấp nhất {min(trung_vi.values())}")
    return "thong_qua", "không còn vấn đề nghiêm trọng/cần sửa; mọi trung vị ≥ 4"


def tong_hop(st: Dict[str, Any]) -> Dict[str, Any]:
    """Bảng điểm, trung vị, độ lệch, vấn đề còn giữ và kết luận — từ trạng thái đã xong cả hai bước."""
    tv = st["thanh_vien"]
    bang = {ma: kq["diem"] for ma, kq in tv.items() if isinstance(kq, dict) and "diem" in kq}
    trung_vi = {k: statistics.median([b[k] for b in bang.values()]) for k in MUC_PHIEU} if bang else {}
    lech = {k: max(b[k] for b in bang.values()) - min(b[k] for b in bang.values()) for k in MUC_PHIEU} if bang else {}
    ct = st.get("chu_tich") or {}
    van_de = _nhom_dai_dien(ct.get("giu") or [], ct.get("gop") or [])
    kl, ly = ket_luan_tat_dinh(van_de, trung_vi) if trung_vi else ("", "chưa đủ bản chấm")
    return {"bang_diem": bang, "trung_vi": trung_vi, "do_lech": lech, "van_de": van_de, "ket_luan": kl,
            "ly_do_ket_luan": ly,
            "phieu_bau": {ma: kq.get("ket_luan") for ma, kq in tv.items() if isinstance(kq, dict)}}


# ── trạng thái & các bước ───────────────────────────────────────────────────────────────────────────────────────────
def thu_muc_hd(out_dir: Path) -> Path:
    return out_dir / THU_MUC


def tep_trang_thai(out_dir: Path, sha: str) -> Path:
    return thu_muc_hd(out_dir) / f"trang_thai_{sha[:12]}.json"


def _doc_st(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _ghi_json(p: Path, du_lieu: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    tam.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                   newline="\n")
    tam.replace(p)


def khoi_tao(study: str, out_dir: Path, tep: Path, model: str) -> Dict[str, Any]:
    van = tep.read_text(encoding="utf-8")
    la_chinh = tep.resolve() == tep_mac_dinh(study, out_dir.parents[1]).resolve()
    ho_so = ho_so_kiem_may(study, out_dir, van, la_chinh)
    return {"schema": SCHEMA, "study": study, "tep": str(tep), "sha": _sha(van), "model": model,
            "ho_so": ho_so, "buoc": "thanh_vien", "batch": {}, "thanh_vien": {}, "chu_tich": None,
            "bat_dau": dt.datetime.now().isoformat(timespec="seconds")}


def uoc_tinh(st: Dict[str, Any], van: str) -> Dict[str, Any]:
    chung = khoi_chung(st["study"], Path(st["tep"]).name, van, st["ho_so"])
    yc = yeu_cau_thanh_vien(chung, st["model"], st["sha"][:8])
    tok_chung = API.uoc_token(chung)
    tok_tv = [API.uoc_token(p["messages"][0]["content"]) for _, p in yc]
    n = len(yc) + 1  # + chủ tịch
    toi_da = sum(API.uoc_toi_da(p, batch=True) or 0 for _, p in yc) * n / len(yc)
    # điển hình: ghi cache 1 lần (1,25×), đọc cache n−1 lần; ra TOKEN_RA_UOC mỗi yêu cầu
    gia = API.GIA_USD_TRIEU_TOKEN.get(st["model"], API.GIA_USD_TRIEU_TOKEN[API.MODEL_MAC_DINH])
    vao = tok_chung * 1.25 * gia["vao"] + tok_chung * (n - 1) * gia["doc_cache"] + (sum(tok_tv) + 6000) * gia["vao"]
    ra = n * TOKEN_RA_UOC * gia["ra"]
    return {"so_yeu_cau": n, "token_tai_lieu": tok_chung, "usd_dien_hinh": round((vao + ra) / 1e6 * 0.5, 2),
            "usd_toi_da": round(toi_da, 2), "model": st["model"]}


def _chay_buoc(st: Dict[str, Any], van: str, goi_api: bool, client: Any) -> int:
    """Một lượt: nộp hoặc lấy batch của bước hiện tại. Trả mã thoát."""
    chung = khoi_chung(st["study"], Path(st["tep"]).name, van, st["ho_so"])
    sha8 = st["sha"][:8]
    if st["buoc"] == "xong":
        print("✅ Hội đồng đã họp xong — chạy «bien-ban» để xem/ghi biên bản.")
        return 0
    bid = st["batch"].get(st["buoc"])
    if not bid:
        if st["buoc"] == "thanh_vien":
            yc = yeu_cau_thanh_vien(chung, st["model"], sha8)
        else:
            ds = [f for kq in st["thanh_vien"].values() if isinstance(kq, dict) for f in kq.get("dat", [])]
            for i, f in enumerate(ds, 1):
                f["id"] = f"F{i:02d}"
            st["ds_xac_minh"] = ds
            bang = {ma: kq["diem"] for ma, kq in st["thanh_vien"].items() if isinstance(kq, dict) and "diem" in kq}
            yc = [(f"ct_{sha8}", tham_so_yeu_cau(chung, loi_nhan_chu_tich(ds, bang), st["model"], MAX_TOKENS_CT))]
        if not goi_api:
            print(f"(chạy khô) bước «{st['buoc']}»: {len(yc)} yêu cầu — thêm --goi-api để nộp batch (tính phí).")
            return 0
        st["batch"][st["buoc"]] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"📨 Đã nộp batch bước «{st['buoc']}»: {st['batch'][st['buoc']]} ({len(yc)} yêu cầu).")
        return 4
    if not goi_api:
        print(f"(chạy khô) batch bước «{st['buoc']}» {bid} đang chờ — thêm --goi-api để lấy kết quả.")
        return 0
    tt = API.trang_thai_batch(bid, client=client)
    if tt["trang_thai"] != "ended":
        print(f"⏳ Batch {bid} đang xử lý ({tt['dang_xu_ly']} yêu cầu) — chạy lại sau.")
        return 4
    ket = API.doc_ket_qua_batch(bid, client=client, nguon=CONG_CU)
    ma_loi = 0
    if st["buoc"] == "thanh_vien":
        for tv in THANH_VIEN:
            cid = f"{tv['ma']}_{sha8}"
            try:
                dl = API.doc_json(API.van_ban_ket_qua_batch(ket.get(cid, {"loai": "thieu"}), MAX_TOKENS_TV))
                st["thanh_vien"][tv["ma"]] = xac_minh_thanh_vien(tv["ma"], dl, van, st["ho_so"].get("chuan_ap_dung")
                                                                 or [])
            except API.LoiApi as exc:
                st["thanh_vien"][tv["ma"]] = {"loi": str(exc)[:300]}
                ma_loi = 1
        hop_le = [m for m, kq in st["thanh_vien"].items() if "diem" in kq]
        if len(hop_le) < 3:
            print(f"🔴 Chỉ {len(hop_le)}/5 bản chấm hợp lệ — không đủ túc số (≥ 3). Chạy lại với --lam-lai.")
            return 1
        st["buoc"] = "chu_tich"
    else:
        try:
            dl = API.doc_json(API.van_ban_ket_qua_batch(ket.get(f"ct_{sha8}", {"loai": "thieu"}), MAX_TOKENS_CT))
            st["chu_tich"] = ap_phan_quyet(st.get("ds_xac_minh") or [], dl)
        except API.LoiApi as exc:
            # Chủ tịch hỏng ⇒ GIỮ mọi nhận xét đã xác minh (fail-safe), ghi rõ không có tổng hợp của chủ tịch.
            st["chu_tich"] = {"giu": st.get("ds_xac_minh") or [], "loai": [], "gop": [], "nhan_xet_chung": "",
                              "yeu_cau_chinh_sua": [], "canh_bao": [f"chủ tịch không trả lời hợp lệ: {exc}"[:300]]}
            ma_loi = 1
        st["buoc"] = "xong"
    print(f"✅ Xong bước — bước kế tiếp: «{st['buoc']}».")
    return ma_loi


# ── biên bản ────────────────────────────────────────────────────────────────────────────────────────────────────────
def bien_ban_md(st: Dict[str, Any]) -> str:
    th = tong_hop(st)
    ten_tv = {tv["ma"]: tv["vai"] for tv in THANH_VIEN}
    d = [f"# Biên bản Hội đồng Khoa học (máy) — {st['study']}", "",
         f"- Tài liệu: `{Path(st['tep']).name}` (SHA-256 {st['sha'][:16]}…)",
         f"- Thành phần: 5 thành viên chấm độc lập + chủ tịch tổng hợp; thư ký là máy tất định. Model {st['model']} "
         f"(Batch API, effort {EFFORT}).", f"- Bắt đầu: {st.get('bat_dau')}", "",
         f"## Kết luận (luật cố định của thư ký máy): **{KET_LUAN.get(th['ket_luan'], '—')}**", "",
         f"Căn cứ: {th['ly_do_ket_luan']}.", "",
         "## Bảng điểm (thang 1–5, Phiếu nhận xét)", "",
         "| Thành viên | " + " | ".join(f"Mục {k}" for k in MUC_PHIEU) + " | Phiếu bầu |",
         "|---|" + "---|" * (len(MUC_PHIEU) + 1)]
    for ma, b in th["bang_diem"].items():
        d.append(f"| {ten_tv.get(ma, ma)} | " + " | ".join(str(b[k]) for k in MUC_PHIEU)
                 + f" | {KET_LUAN.get(th['phieu_bau'].get(ma) or '', '—')} |")
    if th["trung_vi"]:
        d.append("| **Trung vị** | " + " | ".join(str(th["trung_vi"][k]).replace(".", ",") for k in MUC_PHIEU) + " | |")
        d.append("| Độ lệch (cao − thấp) | " + " | ".join(str(th["do_lech"][k]) for k in MUC_PHIEU) + " | |")
    for ma, kq in st["thanh_vien"].items():
        if "loi" in kq:
            d.append(f"\n> {ten_tv.get(ma, ma)}: không có bản chấm hợp lệ ({kq['loi'][:160]}).")
    lech_lon = [k for k, v in th["do_lech"].items() if v >= 2]
    if lech_lon:
        d += ["", f"> Bất đồng lớn (lệch ≥ 2 điểm) ở mục {', '.join(lech_lon)} — xem lý do điểm từng thành viên."]
    ct = st.get("chu_tich") or {}
    d += ["", "## Nhận xét chung của chủ tịch", "", ct.get("nhan_xet_chung") or "(không có)", "",
          "## Tồn tại và yêu cầu chỉnh sửa (mục 5 — nhận xét đã máy xác minh nguyên văn, chủ tịch giữ)", ""]
    nhan = {"nghiem_trong": "🔴 Nghiêm trọng", "can_sua": "🟠 Cần sửa", "goi_y": "🟢 Gợi ý"}
    for f in th["van_de"]:
        d += [f"- **{nhan[f['muc_do']]} · mục {f['muc_phieu']} · dòng {f['dong']}** ({ten_tv.get(f['thanh_vien'])}"
              + (f"; trùng ý {', '.join(f['gop_voi'])}" if f.get("gop_voi") else "") + ")",
              f"  - Trích: «{f['trich']}»", f"  - Vấn đề: {f['van_de']}" + (f" ({f['chuan']})" if f["chuan"] else ""),
              f"  - Đề xuất: {f['de_xuat']}"]
    if ct.get("yeu_cau_chinh_sua"):
        d += ["", "**Thứ tự chỉnh sửa (chủ tịch):**", ""]
        d += [f"{i}. {x}" for i, x in enumerate(ct["yeu_cau_chinh_sua"], 1)]
    if ct.get("loai"):
        d += ["", "## Nhận xét chủ tịch loại (báo động giả) — giữ để minh bạch", ""]
        d += [f"- {f['id']} dòng {f['dong']} ({ten_tv.get(f['thanh_vien'])}): {f['van_de']} — lý do loại: "
              f"{f['ly_do_chu_tich']}" for f in ct["loai"]]
    khong = [f for kq in st["thanh_vien"].values() for f in (kq.get("khong_xac_minh") or [])]
    if khong:
        d += ["", "## Nhận xét máy KHÔNG xác minh được (không tính vào kết luận)", ""]
        d += [f"- {ten_tv.get(f['thanh_vien'])} dòng {f.get('dong')}: {f.get('van_de')[:200]} — {f['ly_do_loai']}"
              for f in khong]
    cb = [x for kq in st["thanh_vien"].values() for x in (kq.get("canh_bao") or [])] + (ct.get("canh_bao") or [])
    if cb:
        d += ["", "## Cảnh báo của thư ký máy", ""] + [f"- {x}" for x in cb]
    manh = [(ma, x) for ma, kq in st["thanh_vien"].items() for x in (kq.get("diem_manh") or [])]
    if manh:
        d += ["", "## Điểm mạnh thành viên ghi nhận", ""] + [f"- {x} ({ten_tv.get(ma)})" for ma, x in manh]
    d += ["", "---", "", "Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật, không mở/chặn "
          "cổng, không ký. Nhận xét đã xác minh nguyên văn là căn cứ để nhóm nghiên cứu/agent sửa; kết luận là luật "
          "nội bộ tái lập được. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(d)


# ── hiệu chuẩn: cài lỗi đã biết vào bản sao ──────────────────────────────────────────────────────────────────────────
LOI_CAI: Tuple[Tuple[str, str, str, str], ...] = (
    # (mã, mô tả, mẫu dòng neo — chèn NGAY SAU dòng khớp đầu tiên, câu chèn). Neo chỉ bám ĐỀ MỤC («#…»/«**…»): dòng
    # mục lục («- PHỤ LỤC B…») và câu giữa đoạn không phải chỗ một lỗi thật nằm.
    ("khong_nguon", "khẳng định số liệu không có trích dẫn ở đặt vấn đề",
     r"(?i)^#+\s*(?:\d+\.?\s*)?đặt vấn đề",
     "Tại Việt Nam, tỷ lệ người bệnh không hài lòng với dịch vụ ngoại trú là 47,3%."),
    ("nhan_qua", "ngôn ngữ nhân quả vượt thiết kế quan sát",
     r"(?i)^#+.*(?:ý nghĩa|dự kiến kết quả)", "Kết quả nghiên cứu sẽ chứng minh các yếu tố trên là nguyên nhân gây ra "
     "tình trạng của người bệnh."),
    ("kiem_dinh_sai", "kiểm định thống kê sai loại biến",
     r"(?i)^#+.*(?:phân tích|xử lý) (?:số liệu|thống kê|dữ liệu)", "So sánh tỷ lệ giữa hai nhóm bằng kiểm định "
     "t-Student cho hai mẫu độc lập."),
    ("tieu_chuan_mau_thuan", "tiêu chuẩn loại trừ mâu thuẫn tiêu chuẩn chọn",
     r"(?i)^(?:#+|\*\*).*tiêu chuẩn loại trừ", "- Người bệnh từ 18 tuổi trở lên."),
    ("muc_tieu_khong_phan_tich", "mục tiêu không có phương pháp/phân tích tương ứng",
     r"(?i)^#+.*mục tiêu", "Mục tiêu bổ sung: đánh giá chi phí điều trị trực tiếp của người bệnh trong 12 tháng."),
    ("dong_thuan_sai", "quyền rút lui trái nguyên tắc tự nguyện",
     r"(?i)^(?:#+|\*\*).*(?:đồng thuận|đồng ý tham gia|phiếu đồng ý|chấp thuận tham gia)",
     "Người tham gia không được rút khỏi nghiên cứu sau khi đã ký phiếu đồng ý."),
)


def cai_loi(van: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Chèn mỗi lỗi một dòng sau neo đầu tiên còn chưa dùng; trả (văn bản mới, đáp án theo SỐ DÒNG mới)."""
    dong = van.splitlines()
    chen: List[Tuple[int, str, str, str]] = []
    for ma, mo_ta, neo, cau in LOI_CAI:
        i = next((k for k, d in enumerate(dong) if re.search(neo, d) and all(k != c[0] for c in chen)), None)
        if i is not None:
            chen.append((i, ma, mo_ta, cau))
    dap_an = []
    for lech, (i, ma, mo_ta, cau) in enumerate(sorted(chen)):
        vi_tri = i + 1 + lech  # vị trí trong danh sách SAU khi đã chèn các lỗi phía trước
        dong.insert(vi_tri, cau)
        dap_an.append({"ma": ma, "mo_ta": mo_ta, "dong": vi_tri + 1, "cau": cau})
    return "\n".join(dong) + "\n", dap_an


def cham_hieu_chuan(dap_an: Sequence[Dict[str, Any]], st: Dict[str, Any]) -> Dict[str, Any]:
    """Một lỗi cài được tính là BẮT khi có vấn đề hội đồng giữ (sau chủ tịch) nằm trong ±3 dòng quanh dòng cài. Ghép
    MỘT–MỘT: mỗi vấn đề chỉ được tính cho một lỗi cài (gần nhất) — hai lỗi cài sát nhau không được «bắt» bằng một nhận
    xét (đo được ở test: ghép nhiều–một thổi phồng độ nhạy)."""
    van_de = tong_hop(st)["van_de"]
    da_dung: set = set()
    ket = []
    for a in sorted(dap_an, key=lambda x: int(x["dong"])):
        ung = sorted((abs(int(f["dong"]) - int(a["dong"])), i) for i, f in enumerate(van_de)
                     if i not in da_dung and abs(int(f["dong"]) - int(a["dong"])) <= CUA_SO_DONG)
        if ung:
            da_dung.add(ung[0][1])
        ket.append({**a, "bat": bool(ung), "boi": [van_de[ung[0][1]]["thanh_vien"]] if ung else []})
    bat = sum(1 for k in ket if k["bat"])
    return {"so_loi_cai": len(ket), "bat": bat, "do_nhay": round(bat / len(ket), 3) if ket else None, "chi_tiet": ket,
            "van_de_ngoai_loi_cai": sum(1 for f in van_de if all(abs(int(f["dong"]) - int(a["dong"])) > CUA_SO_DONG
                                                                    for a in dap_an))}


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description="Hội đồng Khoa học máy cấp đề tài (Claude Batch API).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    for ten in ("uoc-tinh", "hop", "bien-ban", "hieu-chuan"):
        p = sub.add_parser(ten)
        p.add_argument("--study", required=True)
        p.add_argument("--tep", type=Path, help="tài liệu (mặc định: đề cương nộp Hội đồng của đề tài)")
        p.add_argument("--model", default=MODEL_MAC_DINH)
        if ten == "hop":
            p.add_argument("--goi-api", action="store_true", help="nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--lam-lai", action="store_true", help="bỏ trạng thái cũ của tài liệu này, họp lại")
        if ten == "bien-ban":
            p.add_argument("--ap-dung", action="store_true", help="ghi biên bản .md + .json")
        if ten == "hieu-chuan":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--tao", action="store_true", help="tạo bản sao cài lỗi + đáp án (0 gọi API)")
            g.add_argument("--cham", action="store_true", help="chấm độ nhạy sau khi hội đồng họp bản sao")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print("❌ mã đề tài không hợp lệ", file=sys.stderr)
        return 3
    out_dir = goc / "exports" / a.study
    hc_dir = thu_muc_hd(out_dir) / "hieu_chuan"
    if a.lenh == "hieu-chuan":
        goc_tep = a.tep or tep_mac_dinh(a.study, goc)
        if a.tao:
            if not goc_tep.is_file():
                print(f"❌ không thấy {goc_tep}", file=sys.stderr)
                return 3
            van_moi, dap_an = cai_loi(goc_tep.read_text(encoding="utf-8"))
            ban = hc_dir / f"BAN_CAI_LOI_{a.study}.md"
            ban.parent.mkdir(parents=True, exist_ok=True)
            tam = ban.with_name(ban.name + ".tam")
            tam.write_text(van_moi, encoding="utf-8", newline="\n")
            tam.replace(ban)
            _ghi_json(hc_dir / "dap_an.json", {"tep": str(ban), "sha": _sha(van_moi), "dap_an": dap_an})
            print(f"🧪 Đã cài {len(dap_an)} lỗi vào {ban.name} (đáp án riêng, hội đồng không thấy). Họp bằng:\n"
                  f"   hoi_dong_khoa_hoc.py hop --study {a.study} --tep {ban} --goi-api")
            return 0
        da = _doc_st(hc_dir / "dap_an.json")
        if not da:
            print("❌ chưa có đáp án — chạy «hieu-chuan --tao» trước", file=sys.stderr)
            return 3
        st = _doc_st(tep_trang_thai(out_dir, da["sha"]))
        if not st or st.get("buoc") != "xong":
            print("⏳ hội đồng chưa họp xong bản cài lỗi", file=sys.stderr)
            return 4
        kq = cham_hieu_chuan(da["dap_an"], st)
        _ghi_json(hc_dir / "ket_qua.json", kq)
        print(f"🎯 Độ nhạy hội đồng: bắt {kq['bat']}/{kq['so_loi_cai']} lỗi cài ({kq['do_nhay']}); "
              f"{kq['van_de_ngoai_loi_cai']} vấn đề khác ngoài lỗi cài.")
        for k in kq["chi_tiet"]:
            print(f"   {'✓' if k['bat'] else '✗'} {k['ma']} (dòng {k['dong']}) {', '.join(k['boi'])}")
        return 0 if kq["bat"] == kq["so_loi_cai"] else 1
    tep = a.tep or tep_mac_dinh(a.study, goc)
    if not tep.is_file():
        print(f"❌ không thấy tài liệu {tep}", file=sys.stderr)
        return 3
    van = tep.read_text(encoding="utf-8")
    p_st = tep_trang_thai(out_dir, _sha(van))
    st = None if getattr(a, "lam_lai", False) else _doc_st(p_st)
    if st and st.get("sha") != _sha(van):
        st = None
    try:
        if st is None:
            st = khoi_tao(a.study, out_dir, tep, a.model)
        if a.lenh == "uoc-tinh":
            u = uoc_tinh(st, van)
            print(f"Hội đồng: {u['so_yeu_cau']} yêu cầu ({len(THANH_VIEN)} thành viên + chủ tịch), model {u['model']}, "
                  f"tài liệu ≈ {u['token_tai_lieu']:,} token. Chi phí điển hình ≈ {u['usd_dien_hinh']} USD "
                  f"(Batch −50%, cache tài liệu); trần ước tối đa {u['usd_toi_da']} USD. 0 gọi API.")
            return 0
        if a.lenh == "hop":
            ma = _chay_buoc(st, van, a.goi_api, client)
            if a.goi_api or st.get("batch"):
                _ghi_json(p_st, st)
            return ma
        if st.get("buoc") != "xong":
            print("⏳ hội đồng chưa họp xong — chạy «hop --goi-api» tới khi xong.", file=sys.stderr)
            return 4
        md = bien_ban_md(st)
        if not a.ap_dung:
            print(md)
            print("(chạy khô — thêm --ap-dung để ghi biên bản)")
            return 0
        ngay = dt.date.today().strftime("%Y%m%d")
        p_md = thu_muc_hd(out_dir) / f"BIEN_BAN_HDKH_{a.study}_{ngay}_{st['sha'][:8]}.md"
        tam = p_md.with_name(p_md.name + ".tam")
        tam.write_text(md, encoding="utf-8", newline="\n")
        tam.replace(p_md)
        _ghi_json(p_md.with_suffix(".json"), {"schema": SCHEMA, "study": a.study, "tep": st["tep"], "sha": st["sha"],
                                              "model": st["model"], "tong_hop": tong_hop(st),
                                              "chu_tich": st.get("chu_tich"), "disclaimer": API.DISCLAIMER})
        print(f"📝 Đã ghi {p_md.name} (+ .json). Cần bác sĩ kiểm chứng.")
        return 0
    except API.HetNganSach as exc:
        print(f"⛔ {exc}", file=sys.stderr)
        return 2
    except API.LoiApi as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
