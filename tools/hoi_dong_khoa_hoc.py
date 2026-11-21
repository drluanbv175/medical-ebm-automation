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


# ── QUY CHẾ hội đồng — khoá TRƯỚC khi họp (bác sĩ 22/11/2026) ───────────────────────────────────────────────────────
# «Phải đảm bảo hội đồng hoạt động theo quy trình khoa học nghiêm ngặt, được lên kế hoạch kỹ lưỡng ngay từ đầu và được
# thực hiện với sự trung thực tuyệt đối. Khi hội đồng đã quyết định thì vấn đề được thông qua … nếu không được thì phải
# chỉnh sửa theo hội đồng». ⇒ Mọi luật (thành phần, tiêu chí, mốc điểm, xác minh, kết luận, rào biên tập, hiệu chuẩn,
# model, NGUYÊN VĂN mọi lời dặn) gom vào MỘT quy chế có phiên bản + SHA-256. Phiên mang SHA lúc khởi tạo; quy chế đổi
# giữa phiên ⇒ phiên hết hiệu lực. Kết luận chỉ có HIỆU LỰC khi hội đồng đã hiệu chuẩn đạt ngưỡng DƯỚI ĐÚNG quy chế đó.
PHIEN_BAN_QUY_CHE = "QC-HDKH-1.0"
NGAY_KHOA_QUY_CHE = "2026-11-22"
TUC_SO = 3
DO_NHAY_TOI_THIEU = 5 / 6        # mỗi bản cài lỗi phải bắt ≥ 5/6 lỗi
TEP_QUY_CHE = "docs/QUY-CHE-HOI-DONG-KHOA-HOC-MAY.md"


def ke_hoach(model: str = MODEL_MAC_DINH) -> Dict[str, Any]:
    """Quy chế đầy đủ (dữ liệu thuần, xác định) — nguồn của SHA và của văn bản quy chế."""
    return {
        "phien_ban": PHIEN_BAN_QUY_CHE, "ngay_khoa": NGAY_KHOA_QUY_CHE,
        "muc_dich": "Chấm đề cương nộp Hội đồng theo thể thức Hội đồng Khoa học, tư vấn — không thay hội đồng thật.",
        "thanh_phan": [{"ma": t["ma"], "vai": t["vai"], "trong_tam": list(t["trong_tam"]), "nhiem_vu": t["nhiem_vu"]}
                       for t in THANH_VIEN],
        "doc_lap": "mỗi thành viên một yêu cầu riêng, không thấy điểm/nhận xét của người khác",
        "chu_tich": "chỉ giữ, hạ mức (không nâng) hoặc loại kèm lý do; không thêm nhận xét, không sửa điểm, không "
                    "tuyên kết luận; chủ tịch hỏng ⇒ giữ mọi nhận xét đã xác minh",
        "thu_ky": "máy tất định: trung vị, độ lệch, kết luận theo luật, biên bản",
        "tieu_chi": dict(MUC_PHIEU), "moc_diem": MOC_DIEM, "muc_do": list(MUC_DO),
        "xac_minh": {"trich_nguyen_van_cua_so_dong": CUA_SO_DONG, "pii": "loại nhận xét có chuỗi giống số điện thoại",
                     "chuan_ngoai_danh_muc": "bỏ nhãn chuẩn, giữ nhận xét, cảnh báo", "chuan_chung": list(CHUAN_CHUNG),
                     "diem": "số nguyên 1–5 (nhận chuỗi một chữ số); điểm ≤ 2 phải có nhận xét nặng đã xác minh"},
        "tuc_so": TUC_SO,
        "ket_luan": " ".join((ket_luan_tat_dinh.__doc__ or "").split()),
        "vong_kin": {"so_vong_toi_da": SO_VONG_TOI_DA, "tran_ky_tu_thay": TRAN_KY_TU_THAY,
                     "rao_thay_the": ["đoạn cũ đúng 1 lần, đúng dòng ±3", "không trích dẫn mới", "không con số mới",
                                      "không ô [CẦN]/dấu vết máy", "không PII"],
                     "rao_van_ban": ["K17 không thêm mục thiếu", "K1–K17 không tăng lỗi theo mã",
                                     "nhất quán xuyên cổng không tăng lệch", "xấu đi ⇒ hoàn nguyên .md + Word",
                                     "luôn sao lưu bản cũ"]},
        "hieu_chuan": {"loi_cai": [[m, mo] for m, mo, *_ in LOI_CAI], "ghep": "một–một trong ±3 dòng",
                       "do_nhay_toi_thieu": round(DO_NHAY_TOI_THIEU, 4),
                       "dieu_kien": "vòng kín chỉ chạy, kết luận chỉ có hiệu lực, khi hiệu chuẩn đạt dưới cùng SHA"},
        "mo_hinh": {"model": model, "effort": EFFORT, "thinking": "adaptive", "batch_api": True,
                    "cache": "tiền tố đề cương + hồ sơ kiểm máy dùng chung"},
        "trung_thuc": ["lưu nguyên văn mọi trả lời của model", "liệt kê mọi nhận xét bị loại kèm lý do",
                       "không đổi quy chế giữa phiên", "biên bản gắn SHA tài liệu và SHA quy chế",
                       "chi phí thật ghi sổ theo id batch"],
        "loi_nhan": {"dau_tien_to": khoi_chung("<MA>", "<TEP>", "", {}),
                     "thanh_vien": {t["ma"]: loi_nhan_thanh_vien(t) for t in THANH_VIEN},
                     "chu_tich": loi_nhan_chu_tich([], {}), "bien_tap": loi_nhan_bien_tap([])},
    }


def sha_ke_hoach(model: str = MODEL_MAC_DINH) -> str:
    return hashlib.sha256(json.dumps(ke_hoach(model), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def van_ban_quy_che(model: str = MODEL_MAC_DINH) -> str:
    """Văn bản quy chế (Markdown) sinh từ ĐÚNG dữ liệu khoá — test buộc tệp trong repo khớp SHA."""
    k = ke_hoach(model)
    d = [f"# Quy chế Hội đồng Khoa học máy cấp đề tài — {k['phien_ban']}", "",
         f"- Khoá ngày: {k['ngay_khoa']} · SHA-256 quy chế: `{sha_ke_hoach(model)}`",
         f"- Mục đích: {k['muc_dich']}", f"- Công cụ: `{CONG_CU}` (văn bản này sinh bằng lệnh `ke-hoach --ghi`).", "",
         "## 1. Thành phần (chấm độc lập)", ""]
    d += [f"- **{t['vai']}** — mục trọng tâm {', '.join(t['trong_tam'])}: {t['nhiem_vu']}" for t in k["thanh_phan"]]
    d += [f"- Độc lập: {k['doc_lap']}.", f"- Chủ tịch: {k['chu_tich']}.", f"- Thư ký: {k['thu_ky']}.", "",
          "## 2. Tiêu chí (Phiếu nhận xét, Phụ lục 2) và mốc điểm", ""]
    d += [f"{so}. {ten}" for so, ten in k["tieu_chi"].items()] + ["", "```", k["moc_diem"], "```", "",
                                                                 "## 3. Xác minh nhận xét (máy)", ""]
    d += [f"- {a}: {b}" for a, b in k["xac_minh"].items() if a != "chuan_chung"]
    d += [f"- Chuẩn chung được dẫn: {', '.join(k['xac_minh']['chuan_chung'])}; cộng chuẩn báo cáo theo thiết kế (K17).",
          "", "## 4. Túc số và kết luận", "", f"- Túc số: ≥ {k['tuc_so']} bản chấm hợp lệ.", f"- {k['ket_luan']}", "",
          "## 5. Vòng kín: chỉnh sửa theo hội đồng", "",
          f"- Tối đa {k['vong_kin']['so_vong_toi_da']} vòng; mỗi đoạn thay ≤ {k['vong_kin']['tran_ky_tu_thay']} ký tự.",
          "- Rào từng thay thế: " + "; ".join(k["vong_kin"]["rao_thay_the"]) + ".",
          "- Rào toàn văn bản: " + "; ".join(k["vong_kin"]["rao_van_ban"]) + ".", "",
          "## 6. Hiệu chuẩn (điều kiện tiên quyết)", ""]
    d += [f"- Lỗi cài: {m} — {mo}." for m, mo in k["hieu_chuan"]["loi_cai"]]
    d += [f"- Ghép {k['hieu_chuan']['ghep']}; độ nhạy tối thiểu {k['hieu_chuan']['do_nhay_toi_thieu']} mỗi bản.",
          f"- {k['hieu_chuan']['dieu_kien']}.", "", "## 7. Mô hình", ""]
    d += [f"- {a}: {b}" for a, b in k["mo_hinh"].items()]
    d += ["", "## 8. Trung thực", ""] + [f"- {x}." for x in k["trung_thuc"]]
    d += ["", "Nguyên văn mọi lời dặn gửi hội đồng nằm trong mã và được tính vào SHA ở trên — sửa một chữ là đổi "
          "quy chế.",
          "", "Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(d)


def hieu_luc_hieu_chuan(out_dir: Path, model: str = MODEL_MAC_DINH) -> Tuple[bool, str]:
    """Hội đồng đã hiệu chuẩn đạt ngưỡng DƯỚI quy chế hiện hành cho đề tài này chưa? (không đo được ⇒ chưa)."""
    kq = _doc_st(thu_muc_hd(out_dir) / "hieu_chuan" / "ket_qua.json")
    if not kq:
        return False, "chưa hiệu chuẩn"
    if kq.get("sha_quy_che") != sha_ke_hoach(model):
        return False, "hiệu chuẩn dưới quy chế khác (SHA không khớp) — hiệu chuẩn lại"
    if not isinstance(kq.get("do_nhay"), (int, float)) or kq["do_nhay"] < DO_NHAY_TOI_THIEU:
        return False, f"độ nhạy {kq.get('do_nhay')} < ngưỡng {round(DO_NHAY_TOI_THIEU, 3)}"
    return True, f"độ nhạy {kq['bat']}/{kq['so_loi_cai']} dưới {PHIEN_BAN_QUY_CHE} (SHA khớp)"


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
        "diem": {"1": 4, "2": 3, "3": 4, "4": 3},
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
        # 22/11/2026 (lượt hiệu chuẩn thật đầu tiên): khuôn cũ ghi «"số nguyên 1–5"» nên model trả điểm dạng CHUỖI "3"
        # ⇒ 9/10 bản chấm bị loại. Nhận chuỗi MỘT chữ số 1–5; mọi dạng khác (0, 6, 4.5, true, rỗng) vẫn hỏng.
        if isinstance(v, str) and v.strip() in {"1", "2", "3", "4", "5"}:
            v = int(v.strip())
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
            "quy_che": {"phien_ban": PHIEN_BAN_QUY_CHE, "sha": sha_ke_hoach(model)},
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
                tho = API.van_ban_ket_qua_batch(ket.get(cid, {"loai": "thieu"}), MAX_TOKENS_TV)
                st.setdefault("tho", {})[tv["ma"]] = tho  # nguyên văn trả lời — kiểm toán/đọc lại không tốn phí
                dl = API.doc_json(tho)
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
         f"(Batch API, effort {EFFORT}).", f"- Bắt đầu: {st.get('bat_dau')} · vòng {st.get('vong', 1)}",
         f"- Quy chế: {(st.get('quy_che') or {}).get('phien_ban', '—')} (SHA "
         f"{str((st.get('quy_che') or {}).get('sha', '—'))[:16]}…) — khoá trước khi họp, không đổi giữa phiên.",
         f"- Hiệu chuẩn hội đồng: {st.get('hieu_luc_ly_do', 'không áp dụng (bản hiệu chuẩn)')}.",
         "- **Hiệu lực kết luận: " + ("CÓ" if st.get("hieu_luc")
                                       else "CHƯA — hội đồng chưa hiệu chuẩn đạt dưới quy chế này") + "**",
         "",
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


def ghi_bien_ban(st: Dict[str, Any], out_dir: Path) -> Path:
    """Ghi biên bản .md + .json của MỘT lần họp (tên gắn ngày + SHA tài liệu)."""
    ngay = dt.date.today().strftime("%Y%m%d")
    p_md = thu_muc_hd(out_dir) / f"BIEN_BAN_HDKH_{st['study']}_{ngay}_{st['sha'][:8]}.md"
    p_md.parent.mkdir(parents=True, exist_ok=True)
    tam = p_md.with_name(p_md.name + ".tam")
    tam.write_text(bien_ban_md(st), encoding="utf-8", newline="\n")
    tam.replace(p_md)
    _ghi_json(p_md.with_suffix(".json"), {"schema": SCHEMA, "study": st["study"], "tep": st["tep"], "sha": st["sha"],
                                          "vong": st.get("vong", 1), "model": st["model"], "tong_hop": tong_hop(st),
                                          "chu_tich": st.get("chu_tich"), "bien_tap": st.get("bien_tap"),
                                          "disclaimer": API.DISCLAIMER})
    return p_md


# ── vòng kín: hội đồng → biên tập (có rào liêm chính) → họp lại tới khi thông qua ────────────────────────────────────
# Bác sĩ 22/11/2026: «Hội đồng đã được xây dựng đủ tiêu chuẩn để phản biện nên đừng để xảy ra vấn đề phát hiện lỗi và để
# tôi phải quyết; tôi chỉ nhận lại là những nội dung liêm chính và chuẩn mực nhất». Nhận xét đã xác minh ⇒ biên tập viên
# (Claude) đề xuất THAY THẾ NGUYÊN VĂN; MÁY chỉ áp thay thế qua đủ rào; bản mới họp lại; tối đa `SO_VONG_TOI_DA` vòng.
SO_VONG_TOI_DA = 3
MAX_TOKENS_BT = 32000
TRAN_KY_TU_THAY = 1500
_SO_RE = re.compile(r"\d+(?:[.,]\d+)*")
_TRICH_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
_DAU_VET_MAY = re.compile(r"\[CẦN|giả lập|máy sinh|Claude|trí tuệ nhân tạo sinh|\bAI\b", re.IGNORECASE)


def loi_nhan_bien_tap(van_de: Sequence[Dict[str, Any]]) -> str:
    gon = [{k: f.get(k) for k in ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "chuan", "de_xuat")}
           for f in van_de]
    dong = [
        "VAI CỦA BẠN: BIÊN TẬP VIÊN thay mặt nhóm nghiên cứu, sửa đề cương theo các vấn đề hội đồng đã giữ (đã xác",
        "minh nguyên văn). Với TỪNG vấn đề chọn một hành động:",
        "- «sua»: danh sách thay thế {dong, cu, moi} — «cu» là đoạn NGUYÊN VĂN, đủ dài để chỉ xuất hiện MỘT lần",
        "  trong tài liệu, nằm ở dòng «dong»; «moi» là đoạn thay.",
        "- «khong_sua»: đề cương thật ra đã đáp ứng — nêu số dòng chứng minh.",
        "- «vuot_tham_quyen»: chỉ khi cần dữ kiện/quyết định KHÔNG có trong tài liệu và hồ sơ (số liệu thật, kinh",
        "  phí, chữ ký, quyết định của Hội đồng Đạo đức) — nêu đúng dữ kiện cần.",
        "LUẬT LIÊM CHÍNH (máy kiểm, vi phạm ⇒ thay thế bị loại):",
        "1. KHÔNG thêm con số nào chưa có trong tài liệu; KHÔNG thêm trích dẫn/tài liệu tham khảo mới (chỉ dùng số",
        "   trích dẫn đã có).",
        "2. KHÔNG đổi quyết định đã chốt: thiết kế, cỡ mẫu, kết cục chính, quần thể, kế hoạch phân tích đã khoá",
        "   trong SAP. Vấn đề đòi đổi những điều đó ⇒ «vuot_tham_quyen» kèm đề xuất.",
        "3. Khẳng định không có nguồn ⇒ viết lại cho đúng mức chứng cứ hoặc bỏ; KHÔNG bịa nguồn.",
        "4. Văn phong tiếng Việt học thuật, đọc như văn bản người viết: không «[CẦN …]», không nhắc máy/giả lập/AI.",
        "5. Sửa tối thiểu đủ giải quyết vấn đề; mỗi «moi» ≤ 1.500 ký tự.",
        f"VẤN ĐỀ:\n{json.dumps(gon, ensure_ascii=False, indent=1)}",
        "Trả về DUY NHẤT JSON: " + json.dumps({"sua": [{"id": "F01", "hanh_dong": "sua|khong_sua|vuot_tham_quyen",
                                                    "thay": [{"dong": 12, "cu": "…", "moi": "…"}], "ly_do": "…"}]},
                                            ensure_ascii=False),
    ]
    return "\n".join(dong)


def kiem_thay(th: Dict[str, Any], van: str) -> Optional[str]:
    """Lý do LOẠI một thay thế (None = nhận). Kiểm trên văn bản HIỆN TẠI (sau các thay thế đã áp trước nó)."""
    cu, moi = str(th.get("cu") or ""), str(th.get("moi") or "")
    if not cu.strip():
        return "thiếu đoạn cũ"
    if van.count(cu) != 1:
        return f"đoạn cũ xuất hiện {van.count(cu)} lần (phải đúng 1)"
    try:
        dong = int(th.get("dong"))
    except (TypeError, ValueError):
        return "thiếu số dòng"
    if abs(van[:van.index(cu)].count("\n") + 1 - dong) > CUA_SO_DONG:
        return "đoạn cũ không nằm ở dòng đã nêu"
    if len(moi) > TRAN_KY_TU_THAY:
        return f"đoạn thay dài {len(moi)} ký tự (> {TRAN_KY_TU_THAY})"
    da_co = {int(x) for m in _TRICH_RE.findall(van) for x in re.findall(r"\d+", m)}
    trich_moi = {int(x) for m in _TRICH_RE.findall(moi) for x in re.findall(r"\d+", m)} - da_co
    if trich_moi:
        return f"trích dẫn mới không có trong đề cương: {sorted(trich_moi)}"
    khong_trich = _TRICH_RE.sub(" ", moi)
    so_moi = set(_SO_RE.findall(khong_trich)) - set(_SO_RE.findall(cu)) - set(_SO_RE.findall(van))
    if so_moi:
        return f"số mới không có trong đề cương: {', '.join(sorted(so_moi))}"
    if _DAU_VET_MAY.search(moi):
        return "đoạn thay có ô trống hoặc dấu vết máy"
    if _SO_DIEN_THOAI.search(moi):
        return "đoạn thay có chuỗi giống số điện thoại (PII)"
    return None


def ap_bien_tap(dl: Any, van: str) -> Tuple[str, Dict[str, Any]]:
    """Áp các thay thế hợp lệ theo thứ tự; trả (văn bản mới, nhật ký nhận/loại/không sửa/vượt thẩm quyền)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("đề xuất biên tập không phải đối tượng JSON")
    nk: Dict[str, Any] = {"nhan": [], "loai": [], "khong_sua": [], "vuot_tham_quyen": []}
    for muc in dl.get("sua") or []:
        if not isinstance(muc, dict):
            continue
        hd, fid, ly = str(muc.get("hanh_dong") or ""), muc.get("id"), str(muc.get("ly_do") or "")
        if hd in ("khong_sua", "vuot_tham_quyen"):
            nk[hd].append({"id": fid, "ly_do": ly})
            continue
        for th in muc.get("thay") or []:
            if not isinstance(th, dict):
                continue
            loi = kiem_thay(th, van)
            ban = {"id": fid, "dong": th.get("dong"), "cu": str(th.get("cu") or "")[:300],
                   "moi": str(th.get("moi") or "")[:TRAN_KY_TU_THAY]}
            if loi:
                nk["loai"].append({**ban, "ly_do_loai": loi})
            else:
                van = van.replace(str(th["cu"]), str(th.get("moi") or ""), 1)
                nk["nhan"].append(ban)
    return van, nk


def _do_chuan(van: str, study: str, out_dir: Path, la_chinh: bool) -> Dict[str, Any]:
    """Số đo tất định để so TRƯỚC/SAU biên tập: số mục chuẩn thiếu (K17), lỗi K1–K17, lệch xuyên cổng."""
    hs = ho_so_kiem_may(study, out_dir, van, la_chinh)
    k17 = hs.get("k17") if isinstance(hs.get("k17"), dict) else {}
    nq = (hs.get("nhat_quan") or {}) if isinstance(hs.get("nhat_quan"), dict) else {}
    tong = nq.get("tong") or {}
    return {"k17_thieu": k17.get("thieu"), "k1_k17": hs.get("k1_k17") if isinstance(hs.get("k1_k17"), list) else None,
            "lech": (tong.get("lech_cung") or 0) + (tong.get("lech_mem") or 0) if tong else None}


def _xau_di(truoc: Dict[str, Any], sau: Dict[str, Any]) -> List[str]:
    ra = []
    if isinstance(truoc.get("k17_thieu"), int) and isinstance(sau.get("k17_thieu"), int) \
            and sau["k17_thieu"] > truoc["k17_thieu"]:
        ra.append(f"K17 thiếu {truoc['k17_thieu']} → {sau['k17_thieu']}")
    if isinstance(truoc.get("k1_k17"), list) and isinstance(sau.get("k1_k17"), list):
        # So SỐ LỖI theo từng mã K, không so nguyên chuỗi: thông điệp lỗi trích đoạn văn nên cùng một lỗi cũ ở cùng
        # chỗ đổi chữ sau khi sửa câu (đo 22/11: K10 dòng 8 bị coi là «mới» ⇒ hoàn nguyên nhầm một bản sửa đúng).
        def _dem(ds: Sequence[str]) -> Dict[str, int]:
            d: Dict[str, int] = {}
            for x in ds:
                m = re.match(r"\s*(K\d+)", str(x))
                d[m.group(1) if m else "khac"] = d.get(m.group(1) if m else "khac", 0) + 1
            return d
        dt_, ds_ = _dem(truoc["k1_k17"]), _dem(sau["k1_k17"])
        tang = [f"{k} {dt_.get(k, 0)}→{v}" for k, v in sorted(ds_.items()) if v > dt_.get(k, 0)]
        if tang:
            ra.append("lỗi K1–K17 tăng: " + ", ".join(tang))
    if isinstance(truoc.get("lech"), int) and isinstance(sau.get("lech"), int) and sau["lech"] > truoc["lech"]:
        ra.append(f"lệch xuyên cổng {truoc['lech']} → {sau['lech']}")
    return ra


def _ghi_van(p: Path, van: str) -> None:
    tam = p.with_name(p.name + ".tam")
    tam.write_text(van, encoding="utf-8", newline="\n")
    tam.replace(p)


def _xuat_word(out_dir: Path, study: str, van: str) -> str:
    """Xuất lại Word của đề cương nộp (bộ xuất riêng của đề cương, không thêm bìa máy). Trả ghi chú kết quả."""
    try:
        import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: PLC0415

        kq = SDC.xuat_word(out_dir, study, van)
        return "đã xuất lại Word" if kq else "chưa xuất lại Word (thiếu python-docx)"
    except Exception as exc:  # noqa: BLE001
        return f"chưa xuất lại Word: {type(exc).__name__}"


def vong_kin_buoc(st: Dict[str, Any], van: str, tep: Path, out_dir: Path, goi_api: bool, ap_dung: bool,
                  client: Any) -> int:
    """MỘT bước của vòng kín trên tài liệu hiện tại. Trả mã thoát; 0 + st['buoc']=='dat' ⇒ đã thông qua."""
    if st["buoc"] in ("thanh_vien", "chu_tich"):
        return _chay_buoc(st, van, goi_api, client)
    th = tong_hop(st) if st["buoc"] in ("xong", "bien_tap") else None
    if st["buoc"] == "xong":
        con = [f for f in th["van_de"] if f["muc_do"] in ("nghiem_trong", "can_sua")]
        if th["ket_luan"] == "thong_qua" and not con:
            st["buoc"] = "dat"
        elif int(st.get("vong", 1)) >= SO_VONG_TOI_DA:
            print(f"⛔ Đã {st.get('vong', 1)} vòng mà còn {len(con)} vấn đề nghiêm trọng/cần sửa — dừng, xem biên bản.")
            return 1
        else:
            st["buoc"] = "bien_tap"
    if st["buoc"] == "dat":
        print(f"✅ ĐẠT: hội đồng thông qua ở vòng {st.get('vong', 1)} — không còn vấn đề nghiêm trọng/cần sửa.")
        return 0
    if st["buoc"] == "da_sua":
        print(f"↻ Đã sửa ở vòng {st.get('vong', 1)} — chạy lại để hội đồng họp bản mới.")
        return 0
    # bien_tap
    chung = khoi_chung(st["study"], Path(st["tep"]).name, van, st["ho_so"])
    cid = f"bt_{st['sha'][:8]}"
    bid = st["batch"].get("bien_tap")
    if not bid:
        if not goi_api:
            print(f"(chạy khô) biên tập {len(th['van_de'])} vấn đề — thêm --goi-api.")
            return 0
        yc = [(cid, tham_so_yeu_cau(chung, loi_nhan_bien_tap(th["van_de"]), st["model"], MAX_TOKENS_BT))]
        st["batch"]["bien_tap"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"📨 Đã nộp batch biên tập: {st['batch']['bien_tap']}.")
        return 4
    if not goi_api:
        return 0
    tt = API.trang_thai_batch(bid, client=client)
    if tt["trang_thai"] != "ended":
        print(f"⏳ Batch biên tập {bid} đang xử lý — chạy lại sau.")
        return 4
    ket = API.doc_ket_qua_batch(bid, client=client, nguon=CONG_CU)
    tho = API.van_ban_ket_qua_batch(ket.get(cid, {"loai": "thieu"}), MAX_TOKENS_BT)
    st.setdefault("tho", {})["bien_tap"] = tho
    van_moi, nk = ap_bien_tap(API.doc_json(tho), van)
    la_chinh = Path(st["tep"]).resolve() == tep_mac_dinh(st["study"], out_dir.parents[1]).resolve()
    truoc, sau = _do_chuan(van, st["study"], out_dir, False), _do_chuan(van_moi, st["study"], out_dir, False)
    xau = _xau_di(truoc, sau)
    nk.update(do_truoc=truoc, do_sau=sau, xau_di=xau)
    st["bien_tap"] = nk
    if not nk["nhan"]:
        print(f"⛔ Không thay thế nào qua rào liêm chính ({len(nk['loai'])} bị loại) — dừng.")
        return 1
    if xau:
        print("⛔ Bản sửa làm chuẩn xấu đi — KHÔNG áp: " + "; ".join(xau))
        return 1
    if not ap_dung:
        print(f"(chạy khô) {len(nk['nhan'])} thay thế qua rào, {len(nk['loai'])} bị loại — thêm --ap-dung để ghi.")
        return 0
    sao_luu = thu_muc_hd(out_dir) / f"sao_luu_{st['sha'][:12]}{tep.suffix}"
    if not sao_luu.exists():
        _ghi_van(sao_luu, van)
    # K1–K17 và nhất quán xuyên cổng đọc TỆP trên đĩa ⇒ đo «trước» khi ghi bản mới, đo «sau» khi đã ghi.
    k_truoc = _do_chuan(van, st["study"], out_dir, True) if la_chinh else {}
    _ghi_van(tep, van_moi)
    if la_chinh:
        # Word xuất TRƯỚC khi đo «sau»: K1–K17 so Word với .md — đo khi Word còn cũ sẽ báo lỗi giả và hoàn nguyên nhầm.
        nk["word"] = _xuat_word(out_dir, st["study"], van_moi)
        try:
            k_sau = _do_chuan(van_moi, st["study"], out_dir, True)
        except Exception as exc:  # noqa: BLE001 — không đo được ⇒ coi là xấu đi, hoàn nguyên (không bao giờ «đạt»)
            k_sau = {"loi": str(exc)}
        xau2 = _xau_di(k_truoc, k_sau) + ([f"không đo được sau sửa: {k_sau['loi']}"] if "loi" in k_sau else [])
        if xau2:
            _ghi_van(tep, van)  # hoàn nguyên cả .md lẫn Word
            _xuat_word(out_dir, st["study"], van)
            nk["xau_di"] = xau2
            print("⛔ K1–K17/nhất quán xấu đi trên bản chính — đã HOÀN NGUYÊN: " + "; ".join(xau2))
            return 1
    st["buoc"], st["sha_moi"] = "da_sua", _sha(van_moi)
    moi = khoi_tao(st["study"], out_dir, tep, st["model"])
    moi.update(vong=int(st.get("vong", 1)) + 1, ban_truoc=st["sha"])
    _ghi_json(tep_trang_thai(out_dir, moi["sha"]), moi)
    print(f"✍️ Đã áp {len(nk['nhan'])} thay thế ({len(nk['loai'])} bị loại, {len(nk['vuot_tham_quyen'])} vượt thẩm "
          f"quyền) — vòng {moi['vong']} sẽ họp bản mới.")
    return 0


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
    k = sub.add_parser("ke-hoach", help="in/ghi văn bản quy chế (khoá trước khi họp)")
    k.add_argument("--ghi", action="store_true", help=f"ghi {TEP_QUY_CHE}")
    for ten in ("uoc-tinh", "hop", "bien-ban", "hieu-chuan", "vong-kin"):
        p = sub.add_parser(ten)
        p.add_argument("--study", required=True)
        p.add_argument("--tep", type=Path, help="tài liệu (mặc định: đề cương nộp Hội đồng của đề tài)")
        p.add_argument("--model", default=MODEL_MAC_DINH)
        if ten == "hop":
            p.add_argument("--goi-api", action="store_true", help="nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--lam-lai", action="store_true", help="bỏ trạng thái cũ của tài liệu này, họp lại")
        if ten == "bien-ban":
            p.add_argument("--ap-dung", action="store_true", help="ghi biên bản .md + .json")
        if ten == "vong-kin":
            p.add_argument("--goi-api", action="store_true", help="nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--ap-dung", action="store_true",
                           help="ghi bản đã sửa (sao lưu bản cũ; hoàn nguyên nếu xấu đi)")
            p.add_argument("--lam-lai", action="store_true", help="bỏ phiên cũ của tài liệu này (vd quy chế đã đổi)")
        if ten == "hieu-chuan":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--tao", action="store_true", help="tạo bản sao cài lỗi + đáp án (0 gọi API)")
            g.add_argument("--cham", action="store_true", help="chấm độ nhạy sau khi hội đồng họp bản sao")
    a = ap.parse_args(argv)
    if a.lenh == "ke-hoach":
        vb = van_ban_quy_che()
        if a.ghi:
            p_qc = goc / TEP_QUY_CHE
            p_qc.parent.mkdir(parents=True, exist_ok=True)
            _ghi_van(p_qc, vb)
            print(f"📜 Đã ghi {TEP_QUY_CHE} ({PHIEN_BAN_QUY_CHE}, SHA {sha_ke_hoach()[:16]}…).")
        else:
            print(vb)
        return 0
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
            _ghi_json(hc_dir / "dap_an.json", {"tep": str(ban), "sha": _sha(van_moi), "dap_an": dap_an,
                                               "sha_goc": _sha(goc_tep.read_text(encoding="utf-8")),
                                               "sha_quy_che": sha_ke_hoach(a.model), "quy_che": PHIEN_BAN_QUY_CHE})
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
        if not (st.get("quy_che") or {}).get("sha") == da.get("sha_quy_che") == sha_ke_hoach(a.model):
            print("⛔ Phiên hiệu chuẩn không cùng quy chế hiện hành — tạo lại bản cài lỗi và họp lại.", file=sys.stderr)
            return 1
        kq = cham_hieu_chuan(da["dap_an"], st)
        kq.update(sha_quy_che=da["sha_quy_che"], quy_che=PHIEN_BAN_QUY_CHE, sha_goc=da.get("sha_goc"),
                  ngay=dt.date.today().isoformat(),
                  dat=kq["do_nhay"] is not None and kq["do_nhay"] >= DO_NHAY_TOI_THIEU)
        _ghi_json(hc_dir / "ket_qua.json", kq)
        print(f"🎯 Độ nhạy hội đồng: bắt {kq['bat']}/{kq['so_loi_cai']} lỗi cài ({kq['do_nhay']}); "
              f"{kq['van_de_ngoai_loi_cai']} vấn đề khác ngoài lỗi cài.")
        for k in kq["chi_tiet"]:
            print(f"   {'✓' if k['bat'] else '✗'} {k['ma']} (dòng {k['dong']}) {', '.join(k['boi'])}")
        return 0 if kq["dat"] else 1
    tep = a.tep or tep_mac_dinh(a.study, goc)
    if not tep.is_file():
        print(f"❌ không thấy tài liệu {tep}", file=sys.stderr)
        return 3
    van = tep.read_text(encoding="utf-8")
    p_st = tep_trang_thai(out_dir, _sha(van))
    st = None if getattr(a, "lam_lai", False) else _doc_st(p_st)
    if st and st.get("sha") != _sha(van):
        st = None
    if st and (st.get("quy_che") or {}).get("sha") != sha_ke_hoach(st.get("model", a.model)):
        print(f"⛔ Phiên của tài liệu này khởi tạo dưới quy chế khác (hoặc chưa có quy chế) — hết hiệu lực. Chạy lại "
              f"với --lam-lai để họp dưới {PHIEN_BAN_QUY_CHE}.", file=sys.stderr)
        return 1
    try:
        if st is None:
            st = khoi_tao(a.study, out_dir, tep, a.model)
        la_ban_chinh = tep.resolve() == tep_mac_dinh(a.study, goc).resolve()
        if la_ban_chinh:
            st["hieu_luc"], st["hieu_luc_ly_do"] = hieu_luc_hieu_chuan(out_dir, st["model"])
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
        if a.lenh == "vong-kin":
            if not la_ban_chinh or not st.get("hieu_luc"):
                print(f"⛔ Vòng kín chỉ chạy trên đề cương chính khi hội đồng đã hiệu chuẩn đạt dưới "
                      f"{PHIEN_BAN_QUY_CHE}: "
                      f"{st.get('hieu_luc_ly_do', 'không phải đề cương chính')}. Chạy «hieu-chuan --tao», họp bản cài "
                      "lỗi, «hieu-chuan --cham» trước.", file=sys.stderr)
                return 3
            ma = vong_kin_buoc(st, van, tep, out_dir, a.goi_api, a.ap_dung, client)
            if a.goi_api or st.get("batch"):
                if st["buoc"] in ("bien_tap", "dat", "da_sua") and not st.get("bien_ban"):
                    st["bien_ban"] = ghi_bien_ban(st, out_dir).name  # mỗi vòng một biên bản — để kiểm toán
                _ghi_json(p_st, st)
            return ma
        if st.get("buoc") not in ("xong", "bien_tap", "dat", "da_sua"):
            print("⏳ hội đồng chưa họp xong — chạy «hop --goi-api» tới khi xong.", file=sys.stderr)
            return 4
        if not a.ap_dung:
            print(bien_ban_md(st))
            print("(chạy khô — thêm --ap-dung để ghi biên bản)")
            return 0
        print(f"📝 Đã ghi {ghi_bien_ban(st, out_dir).name} (+ .json). Cần bác sĩ kiểm chứng.")
        return 0
    except API.HetNganSach as exc:
        print(f"⛔ {exc}", file=sys.stderr)
        return 2
    except API.LoiApi as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
