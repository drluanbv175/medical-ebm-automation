#!/usr/bin/env python3
"""Giả lập TRỌN VÒNG G0→G10 như MỘT ĐỀ TÀI THẬT, xuyên suốt và thống nhất — cho cả 8 thiết kế.

VÌ SAO CÓ (bác sĩ 15/11/2026)
------------------------------
«Việc giả lập phải được thực hiện như một đề tài thật xuyên suốt thống nhất từ đó mới đánh giá và hoàn thiện được hệ
thống.» Canary tháng (`gia_lap_dinh_ky.py`) chỉ đi tới G5 (chờ ký SAP). Diễn tập RCT lần 2–3 (14–15/11) đi G2→G7 nhưng
điền MỌI ô [CẦN] bằng một nhãn chung — cách đó che mất đúng loại lỗi cần tìm: cổng sau HỎI LẠI điều cổng trước đã chốt,
hỏi CÙNG một thông tin nhiều lần, hay đòi phần KHÔNG ÁP DỤNG cho thiết kế.

LÀM GÌ
------
Mỗi thiết kế là MỘT hồ sơ đề tài (`gia_lap_kich_ban_them` + `gia_lap_dinh_ky.KICH_BAN`): nội dung G0/G1/G3, bộ biến, ma
trận mục tiêu → biến, câu trả lời của từng vai ở G2/G4/G5… Mọi vai mô phỏng (PI, IRB, thống kê viên, quản lý dữ liệu,
phản biện độc lập) CHỈ điền từ hồ sơ đó.

1. Phần A (G0→G4): chạy canary `GiaLap` trên bản sao tạm — PI điền nội dung + xác nhận dấu vân tay G0/G1/G3.
2. Phần B (G2, G4, G5, G6, G6.5, G7) và Phần C (G8, G9, G10): chạy công cụ THẬT của hệ trên cùng thư mục đề tài tạm; mỗi
   tài liệu người phải hoàn thiện được QUÉT ô [CẦN]/[TO BE COMPLETED] và phân loại TRƯỚC khi điền:
     hoi_lai_da_chot · ô hỏi điều cổng trước đã chốt (giá trị lấy được từ gate_params/checkpoint) ⇒ KHIẾM KHUYẾT MÁY;
     hoi_lap         · cùng nhãn đã hỏi ở chỗ khác của cùng cổng ⇒ KHIẾM KHUYẾT MÁY (hỏi một lần, dùng nhiều nơi);
     khong_ap_dung   · phần không thuộc thiết kế/đề tài (mẫu sinh học cho đề tài hồ sơ, «Mục tiêu 2» khi chỉ có 1…);
     moi_dung_vai    · thông tin MỚI đúng vai người điền (số IRB, phần mềm, tác giả…) — đúng thiết kế;
     chua_co_ho_so   · hồ sơ chưa có câu trả lời (bổ sung hồ sơ, không phải lỗi máy).
   Điền xong mới chấm cổng; cổng cứng ký bằng KHOÁ GIẢ của pytest.
3. Sau MỖI cổng đo trục nhất quán xuyên cổng (`nhat_quan_xuyen_cong.doi_chieu`) — lệch xuất hiện ở cổng nào ghi ở
cổng đó.

RANH GIỚI
---------
- Chỉ chạy dưới pytest (khoá giả của conftest, `EBM_GATE_KEY_PATH` ngoài `~/.ebm-secrets`); ngoài pytest ⇒ từ chối ký,
  chuỗi dừng ở cổng cứng đầu tiên và báo «không đo được». Không đọc/sửa `exports/` thật, `~/.ebm-secrets`, `.env`.
- Đề tài tạm mang tiền tố `ZZCANARY-` trong thư mục tạm; đánh dấu `synthetic_test` trong bản sao. Dữ liệu là MÔ PHỎNG.
- Chỉ ĐO và BÁO: không sửa mã hệ thống.

Dùng: `GIA_LAP_TRON_VONG=1 python -B -m pytest -q -s tests/test_gia_lap_tron_vong_20261115.py [-k cohort]`.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import secrets
import shutil
import subprocess
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import gia_lap_dinh_ky as GL  # noqa: E402

NHAN_MO_PHONG = "DỮ LIỆU MÔ PHỎNG — không dùng lâm sàng (giả lập trọn vòng)"
NHOM_KHOA = ("IRB", "STATISTICIAN", "PI", "DATA_MANAGER", "INDEPENDENT_PEER_REVIEWER", "METHODOLOGIST",
             "DATA_GOVERNANCE", "PI_PROJECT_OWNER")
O_RE = re.compile(r"\[(?:CẦN|CẦN|TO BE COMPLETED)[^\]\n]*\]")
LOAI_O = ("hoi_lai_da_chot", "hoi_lap", "khong_ap_dung", "moi_dung_vai", "chua_co_ho_so")
LOAI_O_LOI_MAY = ("hoi_lai_da_chot", "hoi_lap")


# ══════════════════════════════════════════════════════════════════════════════════════════════ tiện ích
def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or ""))


def bo_dau(s: Any) -> str:
    t = unicodedata.normalize("NFD", _nfc(s).replace("đ", "d").replace("Đ", "D"))
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn")).strip().lower()


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _ghi_json(p: Path, obj: Any) -> None:
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _text(v: Any) -> str:
    if isinstance(v, (list, tuple)):
        return "; ".join(_text(x) for x in v if _text(x))
    if isinstance(v, Mapping):
        return "; ".join(f"{k}: {_text(x)}" for k, x in v.items() if _text(x))
    return re.sub(r"\s*\(GIẢ LẬP CANARY[^)]*\)", "", _nfc(v)).strip()


def moi_truong_ky() -> Dict[str, str]:
    """Môi trường tiến trình con của PHẦN B/C: như canary (UTF-8, nguồn giả lập) NHƯNG GIỮ `PYTEST_CURRENT_TEST` và
    `EBM_GATE_KEY_PATH`. `GL.moi_truong` bỏ mọi biến PYTEST_* (canary chạy như phiên thường) — dùng nguyên nó thì
    `approve_gate` trong tiến trình con không biết đang kiểm thử và rơi về khoá THẬT ở ~/.ebm-secrets."""
    env = GL.moi_truong(False)
    for k in ("PYTEST_CURRENT_TEST", "EBM_GATE_KEY_PATH"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def duoi_pytest_khoa_gia() -> bool:
    """Chỉ ký khi đang trong pytest VÀ khoá trỏ ra ngoài thư mục bí mật thật."""
    k = os.environ.get("EBM_GATE_KEY_PATH", "")
    return bool(os.environ.get("PYTEST_CURRENT_TEST")) and bool(k) and "ebm-secrets" not in k


# ══════════════════════════════════════════════════════════════════════════════════════════════ phân loại ô
def nhan_cua_o(dong: str, vi_tri: int) -> str:
    """Nhãn đứng TRƯỚC ô trên cùng dòng (bỏ ký hiệu markdown/bảng), hoặc nội dung trong ô khi trước ô trống."""
    truoc = re.sub(r"[*_`>#|☐☑]+", " ", dong[:vi_tri])
    truoc = re.sub(r"^\s*(?:[-•]|\d+[.)]|[a-z][.)])\s*", "", truoc).strip(" :–—-\t")
    nhan = truoc.split(":")[-1].strip() if ":" in truoc else truoc
    return nhan[-80:] or re.sub(r"[\[\]]", "", O_RE.search(dong[vi_tri:]).group(0))[:80]  # type: ignore[union-attr]


def _gp(meta: Mapping[str, Any], cong: str) -> Dict[str, Any]:
    return dict(((meta.get("gate_params") or {}).get(cong) or {}))


def gia_tri_da_chot(meta: Mapping[str, Any], cps: Mapping[str, Mapping[str, Any]]) -> List[Tuple[re.Pattern, str, str]]:
    """Bảng (mẫu nhãn, giá trị đã chốt, tên trường) — chỉ trường CÓ giá trị. Mẫu so trên nhãn đã bỏ dấu."""
    g0, g1, g3 = _gp(meta, "G0"), _gp(meta, "G1"), _gp(meta, "G3")
    po = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), Mapping) else {}
    cp3 = cps.get("G3") or {}
    n = cp3.get("confirmed_n") or cp3.get("n_adjusted")
    est = g1.get("estimand") if isinstance(g1.get("estimand"), Mapping) else {}
    bang = [
        (r"^tieu de", meta.get("title") or meta.get("topic"), "title"),
        (r"phan mem", (cps.get("_SAP") or {}).get("phan_mem"), "SAP.§10"),
        (r"tieu chi (nhan|chon|lua chon|thu nhan)|inclusion", g1.get("inclusion_criteria"), "G1.inclusion_criteria"),
        (r"tieu chi loai|exclusion", g1.get("exclusion_criteria"), "G1.exclusion_criteria"),
        (r"ket cuc chinh|kq chinh|primary outcome",
         " — ".join(_text(po.get(k)) for k in ("name", "measure", "timepoint") if po.get(k)), "G1.primary_outcome"),
        (r"ket cuc phu|secondary outcome", g1.get("secondary_outcomes"), "G1.secondary_outcomes"),
        # 17/11/2026 (diễn tập BTM): «Mục tiêu chung» là G1.aim — quyết định KHÁC danh sách mục tiêu cụ thể; bản cũ
        # khớp mọi nhãn «mục tiêu…» với G1.objectives ⇒ ô mục tiêu chung của đề tài chưa khai aim bị đếm «hỏi lại».
        (r"^muc tieu chung|^aim\b|^general objective", g1.get("aim"), "G1.aim"),
        (r"^muc tieu(?! chung)|^objective|muc tieu 1", g1.get("objectives"), "G1.objectives"),
        (r"doi tuong nghien cuu|quan the nghien cuu|^population", g1.get("population"), "G1.population"),
        (r"dia diem|noi (nghien cuu|thuc hien)|co so nghien cuu|setting", g1.get("setting"), "G1.setting"),
        (r"thoi gian nghien cuu|thoi gian thu thap|study period", g1.get("study_period"), "G1.study_period"),
        (r"(^|\s)co mau|sample size|so nguoi tham gia du kien", n, "G3.n"),
        (r"ten de tai|^title|public title", meta.get("title") or meta.get("topic"), "title"),
        (r"dinh nghia bien co", po.get("measure"), "G1.primary_outcome.measure"),
        (r"gia thuyet|hypothes", " / ".join(_text(g0.get(k)) for k in ("hypothesis_h0", "hypothesis_h1") if g0.get(k)),
         "G0.hypothesis"),
        # 16/11/2026: neo đầu nhãn — «post-trial access to the intervention» (ICF tiếng Anh) không hỏi lại can thiệp
        (r"^can thiep|^phoi nhiem|^intervention|^exposure|mo ta chi tiet tu pico i", g1.get("intervention_or_exposure"),
         "G1.intervention"),
        (r"so sanh|doi chung|comparator", g1.get("comparator"), "G1.comparator"),
        (r"chien luoc tuyen|tuyen chon|recruitment", g1.get("recruitment_strategy"), "G1.recruitment_strategy"),
        # «follow-up contact for safety» sau khi RÚT khỏi nghiên cứu ≠ lịch theo dõi của đề cương
        (r"lich theo doi|follow.?up schedule|schedule of (visits|follow)", g1.get("follow_up_schedule"),
         "G1.follow_up_schedule"),
        (r"quy trinh.*pico|so do nghien cuu|tien trinh nghien cuu|schema", g1.get("study_schema_timeline"),
         "G1.study_schema_timeline"),
        (r"ngau nhien hoa|randomi", g1.get("randomisation"), "G1.randomisation"),
        (r"che giau|concealment", g1.get("allocation_concealment"), "G1.allocation_concealment"),
        (r"lam mu|blinding", g1.get("blinding"), "G1.blinding"),
        (r"quan the phan tich", est.get("population_summary_measure") and
         f"{_text(est.get('population'))}; {_text(est.get('intercurrent_events_strategy'))}", "G1.estimand"),
        (r"(^|\s)alpha|muc y nghia", g3.get("alpha"), "G3.alpha"),
        (r"(^|\s)luc thong ke|(^|\s)power", g3.get("power"), "G3.power"),
        # G1.stopping_rescue_rules là tiêu chí ngừng/cứu trợ cho TỪNG người (SPIRIT 15b — SAP §15); quy tắc dừng CẢ thử
        # nghiệm (SAP §13, phân tích giữa kỳ) là quyết định MỚI của thống kê viên/DMC, không phải điều G1 đã chốt
        (r"ngung.{0,20}(mot nguoi|nguoi tham gia)|tieu chi ngung|rescue", g1.get("stopping_rescue_rules"),
         "G1.stopping_rescue_rules"),
        (r"ke hoach giam sat|monitoring", g1.get("monitoring_plan"), "G1.monitoring_plan"),
        (r"phien ban de cuong|protocol version", g1.get("protocol_version"), "G1.protocol_version"),
        (r"loi ich.*nguy co|benefit.?risk", g1.get("benefit_risk_rationale"), "G1.benefit_risk_rationale"),
        (r"khoang trong|ly do can nghien cuu", g1.get("knowledge_gap"), "G1.knowledge_gap"),
        # 17/11/2026 (G2 BTM thật): PI đã chốt KHÔNG bắt buộc đăng ký / quy trình lưu trữ–huỷ trong
        # _quy-trinh-du-lieu.csv mà khuôn G2 vẫn hỏi lại — bộ giả lập trước đây không biết hai nguồn này nên không đếm
        # là lỗi máy
        (r"^dang ky nghien cuu", "Không bắt buộc đăng ký" if _gp(meta, "G2").get("registration_required") is False
         else None, "G2.registration_required"),
        (r"^thoi gian luu", (cps.get("_QT") or {}).get("luu_tru"), "quy_trinh.luu_tru"),
        (r"^du lieu nhan dang", (cps.get("_QT") or {}).get("huy_bang_noi"), "quy_trinh.huy_bang_noi"),
    ]
    return [(re.compile(m), _text(v), ten) for m, v, ten in bang if _text(v)]


def khong_ap_dung(nhan: str, dong: str, thiet_ke: str, meta: Mapping[str, Any]) -> Optional[str]:
    """Lý do phần này KHÔNG áp dụng cho đề tài (None = có áp dụng)."""
    t = bo_dau(dong)
    g1 = _gp(meta, "G1")
    if re.search(r"mau sinh hoc|lay mau|lay mau mau|biological sample|5 ml mau", t) and thiet_ke != "diagnostic":
        return "đề tài không thu mẫu sinh học"
    if re.search(r"muc tieu 2", t) and len(g1.get("objectives") or []) < 2:
        return "đề tài chỉ có 1 mục tiêu"
    if thiet_ke != "rct" and re.search(r"ngau nhien hoa|dsmb|dmc|phan tich giua ky|randomi", t):
        return "chỉ áp dụng cho thử nghiệm ngẫu nhiên"
    if thiet_ke in ("sr_ma", "qualitative") and re.search(r"ket cuc an toan|bien co bat loi", t):
        return "thiết kế không có biến cố bất lợi do can thiệp"
    if re.search(r"prospero", t) and thiet_ke != "sr_ma":
        return "PROSPERO chỉ cho tổng quan hệ thống"
    if _gp(meta, "G2").get("registration_required") is False and re.search(
            r"nct_|anzctr|ma dang ky|so dang ky|dang ky thanh cong|ngay dang ky|registration|registry|"
            r"dang ky nghien cuu|tuyen sau phe duyet va dang ky", t):
        return "PI đã chốt đề tài không bắt buộc đăng ký"
    return None


# Ô có thể XUỐNG DÒNG và LỒNG một cấp ngoặc («[CẦN, máy chủ nội bộ … tại [đơn vị]]»).
O_DA_DONG_RE = re.compile(
    r"\[(?:CẦN|CẦN|TO BE COMPLETED)(?:[^\[\]]|\[[^\[\]]{0,80}\]){0,600}\]"   # ô [CẦN…] (xuống dòng, lồng 1 cấp)
    r"|\[[^\[\]\n]{1,60}(?:CẦN|CẦN)[^\[\]\n]{0,80}\]"                      # «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]»
    r"|_{3,}(?:\s*/\s*_{2,}\s*/\s*_{2,})?",                                  # ô gạch dưới «___», «___/___/____»
    re.S)


# 17/11/2026 (bác sĩ: văn bản không mang dấu vết máy): ô mà hồ sơ giả lập KHÔNG có câu trả lời (số phê duyệt, chữ ký,
# ORCID, số đếm từ dữ liệu thật…) điền lời trung tính của biểu mẫu thật — không bịa giá trị, không nhãn «GIẢ LẬP».
# Loại ô vẫn được đếm là «chua_co_ho_so» trong báo cáo giả lập.
DIEN_CHUA_CO_HO_SO = "chưa có thông tin"
# Dòng ký/ngày điền tay của phiếu đồng ý G2 (khớp cách g2_quality_gate che chỗ ký trước khi đếm ô trống).
_DONG_KY_G2_RE = re.compile(r"(?i)\b(?:họ(?: và)? tên|ký tên|chữ ký|ký, ghi rõ|participant|witness|investigator|"
                            r"signature|điện thoại|email|phone)\b|_{3,}\s*/\s*_{2,}\s*/")


# Từ không mang nghĩa của nhãn ô: nhãn chỉ gồm chúng («N =», «/», «Ngày», «___», «[CẦN BỔ SUNG]») là nhãn CHUNG của
# khuôn — nhiều ô khác nhau cùng nhãn (N của từng hộp sơ đồ luồng, ngày/tháng của từng dòng ký) không phải «hỏi lặp».
_TU_CHUNG = {"n", "ngay", "thang", "nam", "bo", "sung", "can", "ky", "ten", "ho", "o", "trong", "va", "vd", "xac",
             "nhan", "change", "response", "the", "to", "be", "completed", "date", "neu", "co"}


def nhan_co_nghia(k: str) -> bool:
    """Nhãn ô đủ nghĩa để so «hỏi lặp» (17/11/2026 — bộ đếm cũ tính «N =», «/», «Ngày» là hỏi lặp ⇒ 18–39 ô «lỗi
    máy» mỗi đề tài toàn là nhiễu): còn ≥ 2 từ (≥ 2 chữ cái) ngoài các từ chung của khuôn. Cùng với điều kiện nhãn
    là NHÃN TRƯỜNG đứng trước ô (không phải lời dặn bên trong ô như «[CHỦ NHIỆM ĐIỀN]», «[CẦN KẾT QUẢ THẬT]»)."""
    return len([t for t in re.findall(r"[a-z]{2,}", k or "") if t not in _TU_CHUNG]) >= 2


def ly_do_giu_nguyen(o_txt: str, dong: str, cong: str = "", tep: str = "") -> Optional[str]:
    """Ô KHÔNG thuộc vai đang điền — giữ nguyên chữ: lời hướng dẫn «[CẦN...]» của khuôn; ô KẾT QUẢ của bảng khung (điền
    sau phân tích, G6.5); ô gạch dưới trong dòng bảng (ô kết quả/chữ ký người tham gia — không phải ô người soạn)."""
    if cong == "G9" and tep.startswith("G9_A10") and re.fullmatch(r"_{3,}(?:\s*/\s*_{2,}\s*/\s*\S*)?", o_txt.strip()):
        return "ô ký/ngày điền tay trên bản in — người thật ký (G9 không đếm «___» của gói A10)"
    if cong and cong not in ("G4", "G6", "G7"):  # hồ sơ G2/G5/G8/G9: cổng đếm MỌI ô, kể cả ô bảng ⇒ vai điền hết
        return None
    gon = o_txt.strip()
    if re.fullmatch(r"\[\s*(?:CẦN|CẦN)\s*(?:\.\.\.|…)\s*\]", gon):
        return "lời hướng dẫn của khuôn"
    if "ket qua that" in bo_dau(gon) and cong in ("G4", "G6"):
        return "ô kết quả — điền sau phân tích"
    if re.fullmatch(r"_{3,}", gon) and dong.lstrip().startswith("|"):
        return "ô trống của bảng khung (kết quả/chữ ký) — điền sau"
    return None


def phan_loai_o(tep_text: str, cong: str, tep: str, meta: Mapping[str, Any], cps: Mapping[str, Mapping[str, Any]],
                thiet_ke: str, tra_loi: Sequence[Tuple[str, str]], da_hoi: Dict[str, str]) -> List[Dict[str, Any]]:
    """Mọi ô (kể cả ô XUỐNG DÒNG — khuôn ICF «[CẦN, chức danh/trình độ chuyên\\n môn…]») kèm loại + giá trị sẽ điền.
    `da_hoi` (nhãn đã bỏ dấu → giá trị) dùng chung trong CÙNG cổng."""
    bang = gia_tri_da_chot(meta, cps)
    ra: List[Dict[str, Any]] = []
    for m in O_DA_DONG_RE.finditer(tep_text):
        dau_dong = tep_text.rfind("\n", 0, m.start()) + 1
        cuoi_dong = tep_text.find("\n", m.start())
        dong = tep_text[dau_dong:cuoi_dong if cuoi_dong >= 0 else len(tep_text)]
        so = tep_text.count("\n", 0, m.start()) + 1
        o_txt = m.group(0)
        truoc = re.sub(r"[*_`>#|☐☑]+", " ", dong[:m.start() - dau_dong])
        truoc = re.sub(r"^\s*(?:[-•]|\d+[.)]|[a-z][.)])\s*", "", truoc).strip(" :–—-\t")
        nhan = (truoc.split(":")[-1].strip() if ":" in truoc else ("" if len(truoc) > 60 else truoc))[-80:]
        trong_o = re.sub(r"^\[\s*(?:cần|can|to be completed)[\s,.—:–-]*", "", bo_dau(o_txt)).rstrip("] ").strip()
        nhan_truoc = bool(nhan) and "]" not in nhan and "[" not in nhan  # nhãn trường thật đứng trước ô
        if not nhan_truoc:
            nhan = trong_o[:80] or nhan  # nhãn trước ô lẫn đuôi ô khác ⇒ dùng nội dung trong ô
        k = bo_dau(nhan)
        o = {"cong": cong, "tep": tep, "dong": so, "nhan": nhan, "o": o_txt, "vi_tri": m.start()}
        giu = ly_do_giu_nguyen(o_txt, dong, cong, tep)
        if giu:  # không phải ô của vai này: lời hướng dẫn khuôn, ô kết quả của bảng khung — để nguyên
            ra.append({**o, "loai": "khong_ap_dung", "dien": o_txt, "ly_do": giu})
            continue
        o_tich = tep_text.rfind("☐", dau_dong, m.start())
        if (dong.lstrip().startswith("|") and o_tich >= 0 and not tep_text[o_tich + 1:m.start()].strip()
                and re.match(r"\s*\|\s*\d+[a-z]?(?:-[A-Z]{2,})?\s*\|", dong)):
            # dòng bảng kiểm chuẩn báo cáo («| 7a |», cả mục mở rộng «| 2a-NI |» — 17/11/2026: trước đây mã có hậu
            # tố không khớp ⇒ ô bị điền nhầm giá trị đã chốt hoặc «hồ sơ chưa có»): tác giả đánh dấu đã báo cáo
            ra.append({**o, "vi_tri": o_tich, "o": tep_text[o_tich:m.end()], "loai": "moi_dung_vai",
                       "dien": "☑ đã báo cáo trong bản thảo"})
            continue
        so_0 = re.search(r"(?<![\d.])0(?:\.0+)?\s*$", tep_text[dau_dong:m.start()])
        if "lam tron ve 0" in trong_o and so_0:
            # p mà G6 làm tròn về 0 kèm ô «báo cáo p < 0,001 theo chuẩn tạp chí» (17/11/2026): tác giả viết lại
            # ĐÚNG ngưỡng báo cáo thay cả «0.0 [ô]» — trước đây chữ «tạp chí» trong ô khớp câu trả lời tạp chí đích
            # ⇒ bảng ghi «0.0 Tạp chí Y học Việt Nam» ở cột p
            a0 = dau_dong + so_0.start()
            ra.append({**o, "vi_tri": a0, "o": tep_text[a0:m.end()], "loai": "moi_dung_vai", "dien": "< 0,001"})
            continue
        if "doi chieu g6" in trong_o and re.search(r"\d", dong[:m.start() - dau_dong]):
            # bản thảo chép NGUYÊN VĂN số từ G6 rồi gắn nhãn đối chiếu — tác giả đối chiếu xong thì gỡ nhãn
            ra.append({**o, "loai": "moi_dung_vai", "dien": ""})
            continue
        if cong == "G2" and re.fullmatch(r"_{3,}", o_txt.strip()) and _DONG_KY_G2_RE.search(dong):
            # chỗ ký/ngày điền tay của người tham gia/người chứng kiến/nghiên cứu viên — cổng G2 che khi đếm; điền chữ
            # vào đó làm phiếu đồng ý mất chỗ ký (16/11/2026)
            ra.append({**o, "loai": "khong_ap_dung", "dien": o_txt, "ly_do": "chỗ ký/ngày điền tay trên bản in"})
            continue
        if unicodedata.normalize("NFC", o_txt.strip()) == "[CẦN]" and re.search(
                r"(?:con|day du|moi o|cac o|khong con|het|vs)\s*\(?\s*$",
                                                              bo_dau(dong[:m.start() - dau_dong])):
            # câu HƯỚNG DẪN nhắc tới nhãn («Điền trường còn [CẦN] trước khi gửi», «không còn [CẦN]»): người soạn đã
            # điền xong ⇒ đọc thành «còn ô trống», không phải một ô để chép câu trả lời vào
            ra.append({**o, "loai": "moi_dung_vai", "dien": "ô trống"})
            continue
        if re.fullmatch(r"\[\s*(?:CẦN|CẦN)\s+(?:CHỦ NHIỆM|BÁC SĨ|PI)\s+XÁC NHẬN\s*\]", o_txt.strip()) \
                and tep_text[m.end():m.end() + 1] == ":":
            # dấu nhắc «[CẦN CHỦ NHIỆM XÁC NHẬN]: <câu>» — chủ nhiệm đã xác nhận ⇒ gỡ cả dấu nhắc lẫn dấu hai chấm
            duoi = re.match(r":\s*", tep_text[m.end():]).group(0)
            ra.append({**o, "o": o_txt + duoi, "loai": "moi_dung_vai", "dien": ""})
            continue
        ly_do = khong_ap_dung(nhan, dong + " " + o_txt, thiet_ke, meta)
        # ô KẾT QUẢ không hỏi điều đã chốt (tên kết cục ≠ kết quả của kết cục) ⇒ không lấy bảng đã chốt
        # (16/11/2026) cùng lẽ: ô đòi nhận định «sau khi có dữ liệu thật» (vd tính đại diện quần thể) là nội dung
        # MỚI của tác giả — dòng có chữ «cỡ mẫu» không biến nó thành câu hỏi lại G3.n
        # ô kết quả của bảng giả «để trống» trước khi có dữ liệu cũng không phải câu hỏi lại kết cục đã chốt
        chot = None if re.search(r"ket qua that|sau khi co du lieu|so lieu de trong", trong_o + " " + k) else next(
            ((v, ten) for mau, v, ten in bang if mau.search(k)), None)
        tl = next((v for mau, v in tra_loi if k and re.search(mau, k)), None)
        if tl is None:  # nhãn không khớp mẫu nào ⇒ mới so nội dung trong ô
            tl = next((v for mau, v in tra_loi if re.search(mau, trong_o)), None)
        if ly_do:
            o.update(loai="khong_ap_dung", dien=f"Không áp dụng — {ly_do}")
        elif chot:
            o.update(loai="hoi_lai_da_chot", dien=chot[0], nguon=chot[1])
        elif k and k in da_hoi and nhan_truoc and nhan_co_nghia(k):
            o.update(loai="hoi_lap", dien=da_hoi[k])
        elif tl is not None:
            o.update(loai="moi_dung_vai", dien=tl)
        elif re.fullmatch(r"_{3,}(?:\s*/\s*_{2,}\s*/\s*_{2,})?", o_txt.strip()) and "/" in o_txt:
            o.update(loai="moi_dung_vai", dien=date.today().strftime("%d/%m/%Y"))
        else:
            o.update(loai="chua_co_ho_so", dien=DIEN_CHUA_CO_HO_SO)
        if k and nhan_truoc and nhan_co_nghia(k) and o["loai"] in ("moi_dung_vai", "chua_co_ho_so"):
            da_hoi.setdefault(k, o["dien"])
        ra.append(o)
    return ra


def dien_o(tep_text: str, cac_o: Sequence[Mapping[str, Any]]) -> str:
    """Thay từng ô bằng giá trị đã phân loại — theo VỊ TRÍ trong cả tệp (từ cuối lên để vị trí không trôi)."""
    s = tep_text
    for o in sorted(cac_o, key=lambda x: x["vi_tri"], reverse=True):
        a, b = o["vi_tri"], o["vi_tri"] + len(o["o"])
        if s[a:b] == o["o"] and o["dien"] != o["o"]:
            s = s[:a] + str(o["dien"]).replace("\n", " ") + s[b:]
    return s


def tom_tat_o(cac_o: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    dem = {k: 0 for k in LOAI_O}
    for o in cac_o:
        dem[o["loai"]] = dem.get(o["loai"], 0) + 1
    vi_du = {k: sorted({f"{o['tep']}:{o['dong']} «{o['nhan']}»" + (f" ← {o['nguon']}" if o.get("nguon") else "")
                        for o in cac_o if o["loai"] == k})[:60] for k in LOAI_O}
    return {"tong": len(cac_o), **dem, "vi_du": vi_du}


# ══════════════════════════════════════════════════════════════════════════════════════════════ dữ liệu mô phỏng
def _bern(rng: random.Random, p: float) -> int:
    return 1 if rng.random() < max(0.0, min(1.0, p)) else 0


def _ap_bien_the(rows: List[Dict[str, Any]], bien_the: Mapping[str, Any], kc: Optional[str], pn: Optional[str],
                 g3: Mapping[str, Any], rng: random.Random) -> None:
    """Dữ liệu ĐẶC THÙ của kịch bản biến thể khó (`gia_lap_bien_the_kho`, 16/11/2026) — sửa tại chỗ.

    khong_kem: p_test = effect_size, p_control = p0 (không kém hơn). cum: mã cụm theo khối co_cum người, phân bổ THEO
    CỤM, hiệu ứng ngẫu nhiên cụm trên thang logit. song_con: thời gian mũ (nguy cơ nền từ p_event trong toi_da tháng,
    HR = effect_size), kiểm duyệt hành chính đều 6–toi_da. thieu: hiệp biến thiếu MAR — xác suất thiếu tăng theo biến
    phu_thuoc (tuổi)."""
    p0 = float(g3.get("p0") or 0.3)
    eff = float(g3.get("effect_size") or 1.0)
    if bien_the.get("khong_kem") and kc and pn:
        for r in rows:
            r[kc] = _bern(rng, eff if r[pn] else p0)
    cum = bien_the.get("cum")
    if cum and kc and pn:
        m = int(cum.get("co_cum") or 20)
        so_cum = max(2, math.ceil(len(rows) / m))
        nhanh = [k % 2 for k in range(so_cum)]
        rng.shuffle(nhanh)
        u = [rng.gauss(0, float(cum.get("sd_cum") or 0.3)) for _ in range(so_cum)]
        for i, r in enumerate(rows):
            k = i // m
            r[cum["cot"]] = k + 1
            r[pn] = nhanh[k]
            p = min(0.95, p0 * (eff if r[pn] else 1.0))
            lg = math.log(p / (1 - p)) + u[k]
            r[kc] = _bern(rng, 1 / (1 + math.exp(-lg)))
    sc = bien_the.get("song_con")
    if sc and pn:
        toi_da = float(sc.get("toi_da") or 36)
        p_ev = float(g3.get("p_event") or 0.1)
        lam0 = -math.log(1 - p_ev) / toi_da
        for r in rows:
            lam = lam0 * (eff if r.get(pn) else 1.0)
            t = rng.expovariate(lam)
            c = rng.uniform(6, toi_da)
            r[sc["thoi_gian"]] = round(min(t, c), 1)
            r[sc["bien_co"]] = int(t <= c)
    kt = bien_the.get("kinh_te")
    if kt and kc and pn:  # chi phí 6 tháng: nền + chi phí chương trình (nhánh can thiệp) − tiết kiệm khi đạt kiểm soát
        for r in rows:
            cp = rng.gauss(float(kt["nen"]), float(kt["sd"])) + float(kt["chuong_trinh"]) * (1 if r[pn] else 0) \
                - float(kt["tiet_kiem"]) * (1 if r[kc] else 0)
            r[kt["cot"]] = int(round(max(0.0, cp), -3))
    th = bien_the.get("thieu")
    if th:
        pt = th.get("phu_thuoc")
        for r in rows:
            nen = float(th.get("ty_le") or 0.15)
            if pt and isinstance(r.get(pt), (int, float)):
                nen = min(0.6, nen * (0.4 + 1.2 * max(0.0, (r[pt] - 60) / 25)))
            for cot in th.get("cot") or []:
                if rng.random() < nen:
                    r[cot] = None


def _kich_ban_kho() -> Dict[str, Dict[str, Any]]:
    """Sổ biến thể khó (16/11/2026) + kịch bản chân thực (17/11/2026) — nạp khi cần, không nhập vào KICH_BAN của lượt
    giả lập định kỳ."""
    import gia_lap_bien_the_kho as BTK  # noqa: PLC0415
    import gia_lap_chan_thuc as GCT  # noqa: PLC0415

    return {**BTK.kich_ban_kho(), **GCT.kich_ban_chan_thuc()}


def sinh_du_lieu(thiet_ke: str, bien_so: Mapping[str, Any], g3: Mapping[str, Any], n: int,
                 seed: int = 20261115, bien_the: Optional[Mapping[str, Any]] = None) -> List[Dict[str, Any]]:
    """Dữ liệu MÔ PHỎNG theo bộ biến + giả định G3 (đúng hướng hiệu ứng đã khai). Không dùng lâm sàng."""
    rng = random.Random(seed)
    ma_tran = bien_so["ma_tran"]
    vai = {d[3]: d[2] for d in ma_tran}
    kc = next((d[3] for d in ma_tran if d[2] == "ket_cuc_chinh"), None)
    pn = next((d[3] for d in ma_tran if d[2] == "phoi_nhiem"), None)
    rows: List[Dict[str, Any]] = []
    if thiet_ke == "sr_ma":
        for i in range(max(8, min(int(n or 12), 15))):
            n1 = rng.randint(800, 5000)
            n0 = n1 + rng.randint(-50, 50)
            p0 = rng.uniform(0.02, 0.05)
            rows.append({"study_id": f"TN{i + 1:02d}-{2016 + i % 9}", "thuoc_sglt2": rng.randint(1, 4),
                         "n_can_thiep": n1, "bien_co_can_thiep": int(round(n1 * p0 * rng.uniform(0.6, 0.85))),
                         "n_chung": n0, "bien_co_chung": int(round(n0 * p0)),
                         "theo_doi_thang": round(rng.uniform(18, 50), 1), "rob2_tong": rng.choice((1, 1, 2))})
        return rows
    p0 = float(g3.get("p0") or g3.get("prevalence") or 0.3)
    eff = float(g3.get("effect_size") or 1.0)
    for i in range(int(n)):
        r: Dict[str, Any] = {}
        for ten, kieu, nhan, lua, val, lo_kb, hi_kb in bien_so["bo_bien"]:
            if ten in ("record_id", "ma_nguoi_tham_gia", "study_id"):
                r[ten] = f"R{i + 1:04d}"
            elif ten == "transcript_id":
                r[ten] = f"GB{i + 1:02d}"
            elif kieu == "yesno":
                r[ten] = _bern(rng, 0.3)
            elif kieu in ("radio", "dropdown"):
                so = [int(x.split(",")[0]) for x in lua.split("|")]
                r[ten] = so[_bern(rng, 0.3)] if len(so) == 2 else rng.choice(so)
            elif str(val).startswith("date"):
                r[ten] = (date(2027, 3, 1) + timedelta(days=rng.randint(0, 300))).isoformat()
            elif kieu == "calc":
                r[ten] = None
            elif kieu == "notes":
                r[ten] = rng.choice(["Sợ kim tiêm; lo phải tiêm suốt đời", "Ngại hạ đường huyết khi đi làm",
                                     "Gia đình hỗ trợ học cách tiêm", "Chi phí và việc bảo quản bút tiêm"])
            elif val in ("integer", "number"):
                lo, hi = {"tuoi": (40, 85), "ha_tt_nen": (125, 175), "ha_tt": (110, 175), "ha_ttr": (65, 105),
                          "lvef": (20, 65), "egfr": (25, 100), "natri": (128, 145), "hb": (9, 16),
                          "ast": (15, 120), "alt": (12, 140), "tieu_cau": (90, 350), "lsm_kpa": (3, 25),
                          "ntprobnp": (100, 6000), "thoi_gian_theo_doi": (6, 36), "so_thuoc_nen": (1, 4),
                          "so_thuoc": (1, 4), "thoi_gian_dtd": (3, 25), "diem_tuan_thu_t6": (0, 10),
                          "ha_tt_t6": (110, 170), "ha_tt_tb": (110, 175)}.get(ten, (None, None))
                # 16/11/2026: biến chưa có khoảng lâm sàng ở bảng trên ⇒ dùng khoảng KHAI trong bộ biến (từ điển G5);
                # luôn ép vào khoảng đã khai — từng sinh ha_tt_tb trong 0–100 ⇒ 217 ô ngoài khoảng, cổng tiếp nhận chặn
                lo_khai = float(lo_kb) if str(lo_kb).strip() else None
                hi_khai = float(hi_kb) if str(hi_kb).strip() else None
                lo, hi = (lo, hi) if lo is not None else (lo_khai if lo_khai is not None else 0,
                                                          hi_khai if hi_khai is not None else 100)
                x = rng.uniform(lo, hi)
                x = max(x, lo_khai) if lo_khai is not None else x
                x = min(x, hi_khai) if hi_khai is not None else x
                r[ten] = round(x, 1) if val == "number" else int(round(x))
            else:
                r[ten] = f"{ten}-{i + 1}"
        # kết cục theo đúng giả định G3
        if thiet_ke in ("rct", "cohort") and kc and pn:
            r[pn] = _bern(rng, 0.5 if thiet_ke == "rct" else 0.35)
            r[kc] = _bern(rng, p0 * (eff if r[pn] else 1.0))
        elif thiet_ke == "case_control" and kc and pn:
            r[kc] = 1 if i % 3 == 0 else 0
            odds0 = p0 / (1 - p0)
            p_exp = (odds0 * eff) / (1 + odds0 * eff) if r[kc] else p0
            r[pn] = _bern(rng, p_exp)
        elif thiet_ke == "cross_sectional" and kc:
            r[kc] = _bern(rng, p0)
            if "ha_tt_tb" in r:  # kiểm soát huyết áp phải khớp trị số đo (< 140 mmHg) — dữ liệu không tự mâu thuẫn
                r["ha_tt_tb"] = rng.randint(110, 139) if r[kc] else rng.randint(140, 175)
        elif thiet_ke == "diagnostic" and kc:
            r[kc] = _bern(rng, float(g3.get("prevalence") or 0.3))
            d = math.sqrt(2) * _phi_nguoc(eff)
            r["ast"] = int(round(rng.gauss(35 + 25 * d * r[kc], 12)))
            r["ast"] = max(10, r["ast"])
            r["fib4"] = round((r["tuoi"] * r["ast"]) / (max(r["tieu_cau"], 50) * math.sqrt(max(r["alt"], 5))), 2)
            r["lsm_kpa"] = round(rng.uniform(10.5, 22) if r[kc] else rng.uniform(3.5, 9.5), 1)
        elif thiet_ke == "prediction" and kc:
            lp = -1.6 + 0.03 * (r["tuoi"] - 65) - 0.02 * (r["lvef"] - 40) + 0.0002 * (r["ntprobnp"] - 1500)
            r[kc] = _bern(rng, 1 / (1 + math.exp(-lp)))
        if "ha_tt_t6" in r and kc and pn and thiet_ke == "rct":
            # huyết áp tháng 6 khớp kết cục «kiểm soát» (< 140 mmHg); nhóm can thiệp thấp hơn ~5 mmHg trong cùng tầng
            r["ha_tt_t6"] = (rng.randint(112, 139) if r[kc] else rng.randint(140, 172)) - (3 if r[pn] else 0)
            r["ha_tt_t6"] = min(r["ha_tt_t6"], 139) if r[kc] else max(r["ha_tt_t6"], 140)
        _ = vai
        rows.append(r)
    if bien_the:
        _ap_bien_the(rows, bien_the, kc, pn, g3, rng)
    return rows


def ten_khoa_ban_ghi(hang: Sequence[Mapping[str, Any]]) -> str:
    for k in ("record_id", "ma_nguoi_tham_gia", "study_id"):
        if hang and k in hang[0]:
            return k
    return next(iter(hang[0])) if hang else "record_id"


def cai_loi_nhap(hang: Sequence[Mapping[str, Any]]) -> Tuple[Dict[Tuple[str, str], Any], Dict[Tuple[str, str], Any]]:
    """Lỗi nhập CÓ CHỦ Ý, mỗi lỗi chỉ ở MỘT lần nhập (kiểu lỗi nhập kép bắt được): lần 1 đảo chữ số một biến số;
    lần 2 lệch một mã phân loại. Trả {(mã phiếu, biến): giá trị nhập sai}."""
    khoa = ten_khoa_ban_ghi(hang)
    lan1: Dict[Tuple[str, str], Any] = {}
    lan2: Dict[Tuple[str, str], Any] = {}
    for r in hang[3:]:
        so = [k for k, v in r.items() if isinstance(v, int) and not isinstance(v, bool) and 10 <= v <= 98
              and k != khoa and str(v)[0] != str(v)[1]]
        if so and len(lan1) < 2:
            lan1[(str(r[khoa]), so[0])] = int(str(r[so[0]])[::-1])
        nhi = [k for k, v in r.items() if v in (0, 1) and k != khoa]
        if nhi and len(lan2) < 2 and (str(r[khoa]), nhi[0]) not in lan1:
            lan2[(str(r[khoa]), nhi[0])] = 1 - int(r[nhi[0]])
        if len(lan1) >= 2 and len(lan2) >= 2:
            break
    return lan1, lan2


def _doc_csv(p: Path) -> List[Dict[str, str]]:
    try:
        with Path(p).open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


# Chạy bằng Python ĐI KÈM SPSS (external mode): mở mẫu .sav của hệ, gõ từng phiếu, lưu — như người nhập trong Data View.
MA_NHAP_SAV = r"""
import json, sys
import spss
mau, dl, ra = sys.argv[1:4]
try:
    spss.Submit("GET FILE='" + mau.replace("'", "''") + "'.")
    hang = json.load(open(dl, encoding="utf-8"))
    spss.StartDataStep()
    ds = spss.Dataset()
    bien = [(v.name, v.type) for v in ds.varlist]
    for r in hang:
        dong = []
        for ten, kieu in bien:
            v = r.get(ten)
            if kieu == 0:
                try:
                    if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                        import datetime as _dt
                        dong.append((_dt.date.fromisoformat(v) - _dt.date(1582, 10, 14)).days * 86400.0)
                    else:
                        dong.append(None if v in (None, "") else float(v))
                except (TypeError, ValueError):
                    dong.append(None)
            else:
                dong.append("" if v is None else str(v)[:kieu])
        ds.cases.append(dong)
    spss.EndDataStep()
    spss.Submit("SAVE OUTFILE='" + ra.replace("'", "''") + "'.")
    print("SO_CA=" + str(len(hang)))
finally:
    try:
        spss.StopSPSS()
    except Exception:
        pass
"""


def _phi_nguoc(p: float) -> float:
    """Φ⁻¹(p) xấp xỉ (Acklam) — đủ cho dựng dữ liệu mô phỏng có AUC đích."""
    from statistics import NormalDist  # noqa: PLC0415

    return NormalDist().inv_cdf(min(max(p, 1e-6), 1 - 1e-6))


def _chen_cuoi_muc(s: str, muc: str, doan: str) -> str:
    """Chèn một đoạn vào CUỐI mục có dòng tiêu đề bắt đầu bằng `muc` (vd «## IV. BÀN LUẬN») — trước tiêu đề «## » kế
    tiếp và dấu «---» ngăn mục. Không thấy mục ⇒ ValueError (không chèn bừa chỗ khác)."""
    dong = s.split("\n")
    i = next((k for k, x in enumerate(dong) if x.strip().startswith(muc.strip())), None)
    if i is None:
        raise ValueError(f"không thấy mục {muc!r} trong bản thảo")
    j = next((k for k in range(i + 1, len(dong)) if dong[k].startswith("## ")), len(dong))
    while j > i + 1 and (not dong[j - 1].strip() or dong[j - 1].strip() == "---"):
        j -= 1
    return "\n".join(dong[:j] + ["", doan] + dong[j:])


def _them_tltk(s: str, tltk: str) -> str:
    """Thêm một mục vào danh mục TÀI LIỆU THAM KHẢO, đánh số tiếp sau mục «[n]» cuối cùng của danh mục."""
    dong = s.split("\n")
    i = next((k for k, x in enumerate(dong) if x.strip().upper().startswith("## TÀI LIỆU THAM KHẢO")), None)
    if i is None:
        raise ValueError("bản thảo không có mục TÀI LIỆU THAM KHẢO")
    j = next((k for k in range(i + 1, len(dong)) if dong[k].startswith("## ")), len(dong))
    so = [(k, int(m.group(1))) for k in range(i + 1, j) if (m := re.match(r"^\[(\d+)\]", dong[k].strip()))]
    k_cuoi, n_cuoi = so[-1] if so else (i, 0)
    return "\n".join(dong[:k_cuoi + 1] + [f"[{n_cuoi + 1}] {tltk}"] + dong[k_cuoi + 1:])


def _than_muc_sap(text: str, so: str) -> str:
    m = re.search(rf"^#{{2,4}}\s*§\s*{so}\b[^\n]*\n(.*?)(?=^#{{2,4}}\s*§\s*\d|^#{{1,2}}\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def phuong_phap_sap(text: str) -> str:
    """Cụm chữ NGUYÊN VĂN của phương pháp phân tích chính (§4) — làm `sap_neo` cho phân tích chính."""
    than = _than_muc_sap(text, "4")
    m = re.search(r"\*\*Phương pháp:\*\*\s*([^\n]+)", than)
    goc = m.group(1) if m else next((d[2:] for d in than.splitlines() if d.startswith("- ")), "")
    return goc.strip()[:50].strip()


def loai_kc_tu_sap(text: str) -> str:
    """Kiểu kết cục của phân tích chính theo phương pháp SAP §4 đã khoá (thống kê viên đọc SAP, không đoán)."""
    t = bo_dau(_than_muc_sap(text, "4"))
    for mau, loai in ((r"poisson|log-binomial", "poisson_pr"), (r"logistic thu tu|thu tu|ordinal|ty le chenh tich luy",
                                                                 "ordinal"),
                      (r"logistic", "binary"), (r"tuyen tinh|ancova|t-test|linear", "continuous")):
        if re.search(mau, t):
            return loai
    return "auto"


# ══════════════════════════════════════════════════════════════════════════════════════════════ chạy trọn vòng
class TronVong:
    """Một đề tài trên bản sao tạm `repo` (đã có tools/app/config/templates). `chay` tiêm được để test khung."""

    def __init__(self, ma: str, repo: Path, *, hom_nay: Optional[date] = None,
                 chay: Callable[..., Dict[str, Any]] = GL.chay_lenh, nen_g0_dir: Path = GL.NEN_G0_DIR):
        self.ma, self.kb = ma, (GL.KICH_BAN.get(ma) or _kich_ban_kho()[ma])
        self.repo = Path(repo)
        self.study = self.kb["study"]
        self.out = self.repo / "exports" / self.study
        self.thiet_ke = self.kb["thiet_ke"]
        self.hom_nay = hom_nay or date.today()
        self.chay_lenh = chay
        self.env = moi_truong_ky()
        self.nen_g0_dir = Path(nen_g0_dir)
        self.buoc: List[Dict[str, Any]] = []
        self.o: List[Dict[str, Any]] = []
        self.cong: Dict[str, Dict[str, Any]] = {}
        self.truc: Dict[str, Dict[str, Any]] = {}
        self.dung: Optional[str] = None
        self.phan_a: Dict[str, Any] = {}
        self.du_lieu: Dict[str, Any] = {}

    # ── tiện ích
    def _ngay(self, v: Any) -> str:
        """«<HOM_NAY>» → ngày chạy; «<+N>» → ngày chạy + N ngày; giá trị khác giữ nguyên."""
        t = str(v)
        if t == "<HOM_NAY>":
            return self.hom_nay.isoformat()
        m = re.fullmatch(r"<\+(\d+)>", t)
        return (self.hom_nay + timedelta(days=int(m.group(1)))).isoformat() if m else t

    def _meta(self) -> Dict[str, Any]:
        return _doc_json(self.out / "study_meta.json")

    def _ghi_meta(self, meta: Mapping[str, Any]) -> None:
        _ghi_json(self.out / "study_meta.json", meta)

    def _cp(self, g: str) -> Dict[str, Any]:
        return _doc_json(self.out / f"{g}_checkpoint.json")

    def _lenh(self, ten: str, *tham: str) -> List[str]:
        return [sys.executable, "-B", str(self.repo / "tools" / ten), *tham]

    def chay(self, ten_buoc: str, ten_tool: str, *tham: str, timeout: int = 1800) -> Dict[str, Any]:
        kq = self.chay_lenh(self._lenh(ten_tool, *tham), self.repo, self.env, timeout)
        ra = str(kq.get("ra") or "")
        if "KhoaThatKhiKiemThuError" in ra:
            raise RuntimeError(f"DỪNG: {ten_tool} chạm khoá THẬT dưới pytest")
        dong = [x for x in ra.splitlines() if x.strip()]
        self.buoc.append({"buoc": ten_buoc, "lenh": ten_tool, "ma": kq.get("ma"), "crash": bool(kq.get("crash")),
                          "cuoi": dong[-6:]})
        return {**kq, "dong": dong}

    def cham(self, g: str) -> str:
        bao = GL.cham_song(g, self.study, self.out, self.repo)
        return str(bao.get("status") or "?")

    def do_truc(self, nhan: str) -> None:
        """Ảnh chụp các trục nhất quán sau một cổng (đếm theo mức + liệt kê trục lệch/cần xem)."""
        try:
            import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

            kq = NQ.doi_chieu(self.out, self.study)
        except Exception as exc:  # noqa: BLE001 — đo không được thì ghi, không đoán
            self.truc[nhan] = {"loi": f"{type(exc).__name__}: {exc}"[:200]}
            return
        dem: Dict[str, int] = {}
        lech: List[str] = []
        for t in kq.get("thong_so") or []:
            muc = str(t.get("muc") or t.get("trang_thai") or "?")
            dem[muc] = dem.get(muc, 0) + 1
            if muc in ("lech_cung", "lech_mem"):
                lech.append(f"{t.get('ma')}:{muc}")
        self.truc[nhan] = {"dem": dem, "lech": lech}

    def _ky(self, g: str, artifact: str, vai: str, ref: str, *them: str) -> Dict[str, Any]:
        k = self.env.get("EBM_GATE_KEY_PATH", "")
        if not duoi_pytest_khoa_gia() or not self.env.get("PYTEST_CURRENT_TEST") or not k or "ebm-secrets" in k:
            self.dung = self.dung or f"{g}:khong_ky_ngoai_pytest"
            return {"ma": None}
        return self.chay(f"{g} ký {vai} (khoá giả)", "approve_gate.py", "--study", self.study, "--gate", g,
                         "--artifact", f"exports/{self.study}/{artifact}", "--reviewer-role", vai,
                         "--reviewer-ref", ref, "--scope", "GIẢ LẬP TRỌN VÒNG — khoá giả pytest, thư mục tạm", *them)

    def _khoa_vai(self) -> None:
        k = os.environ.get("EBM_GATE_KEY_PATH", "")
        if not duoi_pytest_khoa_gia():
            return
        goc = Path(k)
        for nhom in NHOM_KHOA:
            p = goc.parent / f"{goc.name}_{nhom}"
            if not p.exists():
                p.write_text(secrets.token_hex(32), encoding="utf-8", newline="\n")

    def hoan_thien_tep(self, g: str, tep: Path, tra_loi: Sequence[Tuple[str, str]], da_hoi: Dict[str, str]) -> None:
        if not tep.is_file() or ".bak-" in tep.name:  # bản sao lưu do bộ sinh để lại khi chạy lại — không phải hồ sơ
            return
        s = tep.read_text(encoding="utf-8")
        cps: Dict[str, Any] = {x: self._cp(x) for x in ("G0", "G1", "G3")}
        sap = self.out / f"G4_A5_SAP_FINAL_{self.study}.md"
        if g != "G4" and sap.is_file():  # SAP đã khoá là nguồn đã chốt cho các cổng sau
            pm = re.search(r"\*\*Phần mềm:\*\*\s*([^\n]+)", _than_muc_sap(sap.read_text(encoding="utf-8"), "10"))
            if pm and not O_RE.search(pm.group(1)):
                cps["_SAP"] = {"phan_mem": pm.group(1).strip()}
        qt = self.out / "_quy-trinh-du-lieu.csv"  # quy trình dữ liệu đã chốt (G1/G5) — nguồn đã chốt cho G2/G5
        if qt.is_file():
            with qt.open(encoding="utf-8-sig", newline="") as fh:
                cps["_QT"] = {r.get("muc"): r.get("gia_tri") for r in csv.DictReader(fh) if r.get("gia_tri")}
        cac_o = phan_loai_o(s, g, tep.name, self._meta(), cps, self.thiet_ke, tra_loi, da_hoi)
        self.o.extend(cac_o)
        s = dien_o(s, cac_o)
        # Ô LỒNG NHAU (16/11/2026, biến thể NI): ô ngoài «[CẦN THỐNG KÊ VIÊN — diễn giải …: [CẦN … CHIỀU DIỄN GIẢI] …]»
        # chỉ lộ ra sau khi ô trong đã điền ⇒ thêm tối đa 2 lượt, CHỈ điền/đếm ô MỚI lộ ra (không đếm trùng ô cũ).
        da_thay = {c["o"] for c in cac_o}
        for _lan in range(2):
            moi = [c for c in phan_loai_o(s, g, tep.name, self._meta(), cps, self.thiet_ke, tra_loi, da_hoi)
                   if c["o"] not in da_thay]
            if not moi:
                break
            self.o.extend(moi)
            da_thay |= {c["o"] for c in moi}
            s = dien_o(s, moi)
        tep.write_text(s, encoding="utf-8", newline="\n")

    # ── Phần A
    def _nen_g0_tu_goc(self) -> None:
        """Biến thể GIỮ NGUYÊN mã đề tài của kịch bản gốc (khoá `goc`, vd «trích dẫn đã rút», «vòng sửa sau phản biện»)
        ⇒ G0 trùng hệt ⇒ dùng chung nền G0 đã lưu của gốc. Khác mã đề tài thì không chép (nền phải tra riêng)."""
        goc = self.kb.get("goc")
        dich, nguon = self.nen_g0_dir / self.ma, self.nen_g0_dir / str(goc)
        if self.kb.get("nen_g0_tu"):  # kịch bản kế thừa ĐỌC thẳng nền gốc (GiaLap._nen_g0) — không chép bản trùng
            return
        if not goc or goc == self.ma or (dich / "_nen.json").is_file() or not (nguon / "_nen.json").is_file():
            return
        if (GL.KICH_BAN.get(goc) or {}).get("study") == self.kb.get("study"):
            shutil.copytree(nguon, dich, dirs_exist_ok=True)

    def phan_a_chay(self) -> bool:
        self._nen_g0_tu_goc()
        gl = GL.GiaLap(self.ma, self.kb, self.repo, False, chay=self.chay_lenh, nen_g0_dir=self.nen_g0_dir)
        kq = gl.chay_kich_ban()
        self.phan_a = {k: kq.get(k) for k in ("do_duoc", "cong_dung", "cham_song_cuoi", "ket", "khiem_khuyet",
                                              "so_can_thiep_do_may", "crash")}
        self.do_truc("sau_G0_G4")
        if not kq.get("do_duoc"):
            self.dung = "phan_a:khong_do_duoc"
            return False
        return True

    # ── G2
    def _ghi_quy_trinh_du_lieu(self) -> None:
        """PI chốt quy trình thu thập · nhập liệu · lưu trữ (`_quy-trinh-du-lieu.csv`, khuôn tools/quy_trinh_du_lieu.py)
        TRƯỚC khi soạn G2 — như đề tài thật BTM (17/11/2026). Neo G2 của ba điều hứa với người tham gia là cụm nguyên
        văn mà G2 in lại từ chính bảng này. Tổng quan (không thu số liệu trên người) và bảng đã có ⇒ không ghi."""
        tep = self.out / "_quy-trinh-du-lieu.csv"
        tt = str(self._meta().get("gate_params", {}).get("G1", {}).get("data_collection_method") or "").strip()
        if tep.is_file() or not tt or "[" in tt:
            return
        nguon = "G1 data_collection_method; quyết định chủ nhiệm"
        dong = [
            ("thu_thap", tt, "G1 data_collection_method", ""),
            ("an_danh", "Phiếu chỉ mang mã nghiên cứu, không ghi họ tên hay số hồ sơ của người tham gia", nguon,
             "Phiếu chỉ mang mã nghiên cứu"),
            ("nhap_lieu", "Nhập vào REDCap theo từ điển dữ liệu của đề tài, hai lượt nhập độc lập", nguon, ""),
            ("kiem_chung", "Đối chiếu hai lượt nhập; khác biệt được giải quyết theo phiếu gốc", nguon, ""),
            ("huy_bang_noi", "Bảng nối mã nghiên cứu với danh tính lưu riêng trong tệp mã hoá, chỉ chủ nhiệm giữ, huỷ "
                             "sau khi khoá dữ liệu", nguon, "huỷ sau khi khoá dữ liệu"),
            ("luu_tru", "Số liệu điện tử và phiếu giấy lưu 5 năm sau khi kết thúc nghiên cứu", nguon,
             "lưu 5 năm sau khi kết thúc nghiên cứu"),
            ("huy_du_lieu", "Hết thời hạn lưu trữ, tệp điện tử được xoá an toàn và phiếu giấy được huỷ, có biên bản",
             nguon, ""),
        ]
        with tep.open("w", encoding="utf-8", newline="") as fh:  # da-nen: bo-qua (CSV RFC 4180 — khuôn QTD)
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["muc", "gia_tri", "nguon", "neo_de_cuong", "neo_g2", "ghi_chu"])
            for muc, gt, ng, neo in dong:
                w.writerow([muc, gt, ng, "", neo, ""])

    def g2(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        self._ghi_quy_trinh_du_lieu()
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault("G2", {}).update(hs.get("G2", {}))
        for k, v in HANH_CHINH.items():  # hành chính PI khai MỘT lần — không ghi đè giá trị đã có
            meta.setdefault("administrative", {}).setdefault(k, v)
        if self.ma == "tong_quan_gop" or self.kb.get("goc") == "tong_quan_gop":  # tổng quan: không có phiếu đồng ý
            meta["gate_params"]["G2"].setdefault(
                "title_en", "SGLT2 inhibitors and hospitalisation for heart failure in type 2 diabetes without heart "
                            "failure at baseline: a systematic review and meta-analysis of randomised trials")
        cd = ICF_EN_CHU_DE.get(self.ma) or ICF_EN_CHU_DE.get(str(self.kb.get("goc") or ""))
        if cd:  # bản dịch tiếng Anh của chủ nhiệm cho phiếu đồng ý (phần chữ tự do)
            meta["gate_params"]["G2"].setdefault("icf_en", {**ICF_EN_CHUNG, **cd})
        self._ghi_meta(meta)
        self._soan_phieu_thu_thap()
        self.chay("G2 sinh hồ sơ đạo đức", "run_g2_auto.py", "--study", self.study)
        da_hoi: Dict[str, str] = {}
        tra = list(hs.get("tra_loi_G2", [])) + list(TRA_LOI_G2_CHUNG) + list(TRA_LOI_CHUNG)
        for tep in sorted(self.out.glob(f"G2_*{self.study}*.md")):
            self.hoan_thien_tep("G2", tep, tra, da_hoi)
        self.cong["G2_truoc_ky"] = {"trang_thai": self.cham("G2")}
        ky = hs.get("ky_G2") or {}
        self._ky("G2", f"G2_A3_ETHICS_PACKAGE_{self.study}.md", "IRB", "GIA-LAP-IRB",
                 *[x for k, v in ky.items() for x in ((k, self._ngay(v)) if v is not True else (k,))])
        self.cong["G2"] = {"trang_thai": self.cham("G2")}
        self._lam_tuoi_g3()
        self.do_truc("sau_G2")

    def _lam_tuoi_g3(self) -> None:
        """G2 sinh lại SAU G3 (hồ sơ đạo đức cần phiếu thu thập số liệu) ⇒ G3/G4 thành «cũ» theo luật độ tươi (G3 đọc
        G2 — pipeline_freshness) và G10 chặn. Như đề tài thật: chạy lại G3 với đúng tham số đã chốt, PI xác nhận lại dấu
        vân tay nếu nội dung đổi; G4 sinh lại sau đó (bước g4)."""
        import run_pipeline as RP  # noqa: PLC0415

        tham = RP._recover_params("G3", self.out, self._meta())
        self.chay("G3 chạy lại sau G2 (độ tươi chuỗi)", "run_g3_auto.py", "--study", self.study, *tham)
        gl = GL.GiaLap(self.ma, self.kb, self.repo, False, chay=self.chay_lenh, nen_g0_dir=self.nen_g0_dir)
        for _ in range(4):
            if gl.mot_buoc_pi() is None:
                break
        self.cong["G3_lam_tuoi"] = {"trang_thai": self.cham("G3")}

    # ── G4
    def g4(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        sap = self.out / f"G4_A5_SAP_FINAL_{self.study}.md"
        self.chay("G4 sinh SAP (sau G3 đã làm tươi)", "run_g4_auto.py", "--study", self.study)
        da_hoi: Dict[str, str] = {}
        them_bien = "; ".join(r[1] for r in (self.kb.get("bien_so") or {}).get("ma_tran", [])
                              if r[2] in ("hiep_bien", "mo_ta", "yeu_to"))
        tl = list(hs.get("tra_loi_G4", [])) + ([(r"them bien", them_bien)] if them_bien else [])
        rct = list(TRA_LOI_G4_RCT) if self.thiet_ke == "rct" else []
        self.hoan_thien_tep("G4", sap, tl + rct + list(TRA_LOI_CHUNG), da_hoi)
        self._bo_sung_epv(sap)
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault("G4", {}).update({
            "epv_vif_reviewed": True, "missing_data_mechanism_confirmed": True,
            "subgroup_multiplicity_predefined_confirmed": True,
            "subgroup_multiplicity_predefined_at": self.hom_nay.isoformat(),
            "reviewed_by_role": "STATISTICIAN", "reviewed_at": GL._bay_gio()})
        self._ghi_meta(meta)
        import g4_quality_gate as G4Q  # noqa: PLC0415 — dấu nội dung PHẦN 3 (G4-HUMAN-08 nằm ở nhóm phê duyệt)

        dau = G4Q.dau_van_tay_g4(sap.read_text(encoding="utf-8")) if sap.is_file() else None
        if dau:
            meta = self._meta()
            meta["gate_params"]["G4"]["dau_van_tay_chot"] = dau
            self._ghi_meta(meta)
        self.cong["G4_truoc_ky"] = {"trang_thai": self.cham("G4"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G4", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G4", sap.name, "METHODS_STATISTICS_REVIEWER", "GIA-LAP-TKV")
        self._ky("G4", sap.name, "PI", "GIA-LAP-PI")
        self.cong["G4"] = {"trang_thai": self.cham("G4")}
        self.do_truc("sau_G4")

    # ── G5: nhập kép (Excel + SPSS) → tiếp nhận → làm sạch → DMP/vận hành → khoá → ký
    def _n_g3(self) -> int:
        cp3 = self._cp("G3")
        n = int(cp3.get("confirmed_n") or cp3.get("n_adjusted") or 0)
        return n or 60

    def _ghi_excel(self, mau: Path, ra: Path, hang: Sequence[Mapping[str, Any]],
                   sai: Mapping[Tuple[str, str], Any]) -> None:
        """Người nhập lần 1 gõ phiếu vào mẫu Excel của hệ (mỗi biểu mẫu một trang, tên biến dòng 1, dữ liệu từ dòng 4).

        VÁ 17/11/2026 (diễn tập trên khung BTM, 6 biểu mẫu): bản cũ chỉ ghi trang PHIẾU đầu tiên ⇒ năm trang còn lại
        trống ⇒ so nhập kép báo 25.556 ô lệch giả (lỗi của bộ giả lập, không phải của công cụ). Nay ghi MỌI trang có cột
        mã nghiên cứu ở dòng 1; mỗi mã một hàng ở mọi trang (công cụ nhập đòi vậy — `kiem_trang_thieu`), câu bị nhánh
        ẩn để trống."""
        import openpyxl  # noqa: PLC0415

        wb = openpyxl.load_workbook(mau)
        khoa = ten_khoa_ban_ghi(hang)
        # trang PHIẾU là trang có cột mã nghiên cứu ở dòng 1 (mẫu còn HUONG_DAN, _DANH_MUC, TU_DIEN, _META)
        trang = [w for w in wb.worksheets if khoa in [c.value for c in w[1]]] or [wb.worksheets[0]]
        for ws in trang:
            ten = [c.value for c in ws[1]]
            for i, r in enumerate(hang):
                for j, t in enumerate(ten):
                    if t:
                        v = sai.get((str(r.get(khoa)), t), r.get(t))
                        if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                            v = date.fromisoformat(v)
                        ws.cell(row=4 + i, column=j + 1, value=v)
        wb.save(ra)

    def _ghi_sav(self, mau: Path, ra: Path, hang: Sequence[Mapping[str, Any]],
                 sai: Mapping[Tuple[str, str], Any]) -> Dict[str, Any]:
        """Người nhập lần 2 gõ phiếu vào mẫu .sav của hệ BẰNG SPSS (API spss.Dataset của Python đi kèm SPSS)."""
        import shutil  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        import cau_noi_spss as SP  # noqa: PLC0415

        tam = Path(tempfile.mkdtemp(prefix="gltv_sav_", dir=str(SP._goc_tam_ngan())))
        try:
            shutil.copy2(mau, tam / "mau.sav")
            khoa = ten_khoa_ban_ghi(hang)
            dl = [{k: sai.get((str(r.get(khoa)), k), v) for k, v in r.items()} for r in hang]
            (tam / "dl.json").write_text(json.dumps(dl, ensure_ascii=False), encoding="utf-8", newline="\n")
            (tam / "nhap.py").write_text(MA_NHAP_SAV, encoding="utf-8", newline="\n")
            kq = subprocess.run([str(SP.tim_spss()), "-I", str(tam / "nhap.py"), str(tam / "mau.sav"),
                                 str(tam / "dl.json"), str(tam / "ra.sav")], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=900, cwd=str(tam))
            if (tam / "ra.sav").is_file():
                shutil.copy2(tam / "ra.sav", ra)
            return {"ma": kq.returncode, "loi": [x for x in (kq.stderr or "").splitlines() if x.strip()][-4:],
                    "ra": kq.stdout.strip().splitlines()[-2:]}
        finally:
            shutil.rmtree(tam, ignore_errors=True)

    def g5(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        self.chay("G5 sinh bộ công cụ (từ điển REDCap, DMP)", "run_g5_auto.py", "--study", self.study)
        da_hoi: Dict[str, str] = {}
        for tep in sorted(self.out.glob(f"G5_*{self.study}*.md")):
            self.hoan_thien_tep("G5", tep, list(hs.get("tra_loi_G5", [])) + list(TRA_LOI_G5_G9_CHUNG)
                                + list(TRA_LOI_CHUNG), da_hoi)
        # dữ liệu mô phỏng theo bộ biến + giả định G3
        n = self._n_g3()
        dl_redcap = self.kb.get("du_lieu_redcap")
        tu_dien_g5 = self.out / f"G5_REDCap_dictionary_{self.study}.csv"
        if dl_redcap and tu_dien_g5.is_file():
            # 17/11/2026 (diễn tập trên khung THẬT): sinh theo đúng từ điển G5 — logic nhánh, calc, khoảng, thứ tự
            # ngày — để dữ liệu mô phỏng đi qua đúng cổng tiếp nhận mà dữ liệu thật sẽ đi qua.
            import sinh_du_lieu_redcap as SR  # noqa: PLC0415

            hm = getattr(SR, dl_redcap["hinh_mau"]) if isinstance(dl_redcap.get("hinh_mau"), str) else dl_redcap.get(
                "hinh_mau")
            # «N_G3» ⇒ đúng cỡ mẫu G3 đã chốt; trần số hồ sơ mở = so_ho_so hoặc hệ số × N (tuyển/trích tới khi đủ N)
            dk = dl_redcap.get("dung_khi")
            if dk:
                dk = [dk[0], n if str(dk[1]) == "N_G3" else int(dk[1])]
            tran = int(dl_redcap.get("so_ho_so") or 0) or int(float(dl_redcap.get("so_ho_so_he_so") or 1) * n)
            hang = SR.sinh(SR.doc_tu_dien(tu_dien_g5), tran, hm, dung_khi=dk)
        else:
            hang = sinh_du_lieu(self.thiet_ke, self.kb["bien_so"], _gp(self._meta(), "G3"), n,
                                bien_the=self.kb.get("bien_the"))
        nl = self.repo.parent / "nhap_lieu"
        nl.mkdir(parents=True, exist_ok=True)
        # biến thể «dữ liệu thiếu» (16/11/2026): PI khai mã thiếu cho cột hồi cứu hay trống TRƯỚC khi dựng mẫu nhập —
        # ô bắt buộc không được để trống; người nhập ghi mã (Excel: chữ «KDD»; SPSS: nhãn giá trị = mã số thay).
        th = (self.kb.get("bien_the") or {}).get("thieu") or {}
        hang_x, hang_s = hang, hang
        if th.get("ma"):
            import nhap_lieu_excel as NL  # noqa: PLC0415

            mt_p = self.out / "_ma-thieu-theo-bien.csv"
            with mt_p.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["bien", "ma", "nhan"])
                w.writerows([[c, th["ma"], th.get("nhan") or th["ma"]] for c in th.get("cot") or []])
            so = NL.ma_chu_so(NL.SP.doc_ma_thieu(mt_p)).get(th["ma"])
            hang_x = [{k: (th["ma"] if v is None and k in th["cot"] else v) for k, v in r.items()} for r in hang]
            hang_s = [{k: (so if v is None and k in th["cot"] else v) for k, v in r.items()} for r in hang]
            self.buoc.append({"buoc": f"PI khai mã thiếu {th['ma']} cho {', '.join(th['cot'])}",
                              "lenh": "_ma-thieu-theo-bien.csv", "ma": 0, "crash": False,
                              "cuoi": [f"mã số thay trong SPSS: {so}"]})
            self._cap_nhat_bang_bien_g3("PI khai mã thiếu theo biến")
        (nl / "PHIEU_GOC_mo_phong.json").write_text(json.dumps(hang, ensure_ascii=False, indent=1), encoding="utf-8",
                                                    newline="\n")
        self.chay("Nhập liệu — mẫu Excel", "nhap_lieu_excel.py", "mau", "--study", self.study, "--ra",
                  str(nl / "MAU.xlsx"), "--so-dong", str(len(hang) + 10))
        # 17/11/2026 (16 kịch bản vào CI): máy chạy CI không có IBM SPSS Statistics (phần mềm bản quyền) ⇒ người nhập
        # lần 2 dùng Excel thay SPSS; so nhập kép Excel ↔ Excel. Máy có SPSS vẫn đi đường SPSS như cũ.
        import cau_noi_spss as SP  # noqa: PLC0415

        try:
            co_spss = bool(SP.tim_spss())
        except Exception:  # noqa: BLE001 — KhongDoDuoc: máy không cài SPSS
            co_spss = False
        if co_spss:
            self.chay("Nhập liệu — mẫu SPSS (.sav)", "nhap_lieu_excel.py", "mau", "--study", self.study, "--dang",
                      "sav", "--ra", str(nl / "MAU.sav"))
        else:
            self.buoc.append({"buoc": "Nhập liệu — mẫu SPSS (.sav)", "lenh": "—", "ma": None, "crash": False,
                              "cuoi": ["máy không có IBM SPSS Statistics — người nhập lần 2 dùng Excel"]})
        lan1, lan2 = cai_loi_nhap(hang)
        self.du_lieu = {"n": len(hang), "loi_cai_lan1": len(lan1), "loi_cai_lan2": len(lan2)}
        if not (nl / "MAU.xlsx").is_file():
            # 17/11/2026 (kịch bản chân thực): G5 không dựng được từ điển (vd SAP chưa khoá vì G3 còn REVIEW) ⇒ không có
            # mẫu nhập. Dừng GỌN với lý do của hệ — bản cũ sập FileNotFoundError, che mất cổng thật đang chặn.
            self.dung = self.dung or "g5:khong_co_mau_nhap_lieu"
            return
        self._ghi_excel(nl / "MAU.xlsx", nl / "lan1_excel.xlsx", hang_x, lan1)
        if co_spss:
            sav = self._ghi_sav(nl / "MAU.sav", nl / "lan2_spss.sav", hang_s, lan2)
            self.du_lieu["nhap_spss"] = sav
            lan2_tep, ten_so = nl / "lan2_spss.sav", "Nhập liệu — so nhập kép (Excel ↔ SPSS)"
        else:
            self._ghi_excel(nl / "MAU.xlsx", nl / "lan2_excel.xlsx", hang_x, lan2)
            self.du_lieu["nhap_spss"] = {"ma": None, "loi": ["không có SPSS — lần 2 nhập bằng Excel"]}
            lan2_tep, ten_so = nl / "lan2_excel.xlsx", "Nhập liệu — so nhập kép (Excel ↔ Excel, máy không có SPSS)"
        r = self.chay(ten_so, "nhap_lieu_excel.py", "so-sanh", "--study", self.study,
                      "--excel1", str(nl / "lan1_excel.xlsx"), "--excel2", str(lan2_tep), "--ra",
                      str(nl / "so_sanh_1"))
        lech = _doc_csv(nl / "so_sanh_1" / "NHAP_KEP_chi_tiet.csv")
        self.du_lieu["o_lech_bat_duoc"] = len(lech)
        # đối chiếu phiếu gốc: sửa CẢ hai bản về đúng phiếu gốc, nhập lại bản sạch qua cổng tiếp nhận
        self._ghi_excel(nl / "MAU.xlsx", nl / "lan1_excel_da_sua.xlsx", hang_x, {})
        self.chay("Nhập liệu — tiếp nhận bản đã đối chiếu", "nhap_lieu_excel.py", "nhap", "--study", self.study,
                  "--excel", str(nl / "lan1_excel_da_sua.xlsx"), "--ra", str(nl / "ra_cuoi"), "--tiep-nhan")
        _ = r
        raw = ((self._meta().get("real_data_intake") or {}).get("raw_readonly_path"))
        if not raw:
            self.dung = self.dung or "G5:khong_tiep_nhan_duoc"
            return
        tu_dien = self.out / f"G5_REDCap_dictionary_{self.study}.csv"
        self.chay("G5 làm sạch", "clean_research_dataset.py", "--study", self.study, "--data",
                  str(self.repo / "exports" / self.study / raw) if not Path(raw).is_absolute() else raw,
                  *(["--dictionary", str(tu_dien)] if tu_dien.is_file() else []))
        bc = _doc_json(self.out / "DATA_CLEANING_report.json")
        self.du_lieu["lam_sach"] = {k: bc.get(k) for k in ("status", "open_query_count", "ready_for_lock",
                                                          "clean_dataset_path", "query_log")}
        self._van_hanh_g5()
        self._chot_dmp()
        nay = self.hom_nay.isoformat()
        tham = ["--study", self.study, "--clean-data", str(self.out / str(bc.get("clean_dataset_path") or "")),
                "--dictionary", str(tu_dien), "--cleaning-report", str(self.out / "DATA_CLEANING_report.json"),
                "--operational-readiness", str(self.out / "G5_OPERATIONAL_READINESS.json"), "--lock-date", nay,
                "--reviewer-role", "DATA_GOVERNANCE_QA_REVIEWER", "--reviewer-ref", "GIA-LAP-DM",
                "--sap-version", "1.0",
                "--confirm-deidentified", "--confirm-clean-copy", "--confirm-no-open-query", "--confirm-sap-locked",
                "--confirm-dictionary-crf-aligned", "--confirm-access-control-reviewed",
                "--confirm-backup-restore-tested", "--confirm-retention-plan",
                "--confirm-protocol-deviations-reconciled", "--confirm-audit-trail-reviewed"]
        if bc.get("query_log"):
            tham += ["--query-log", str(self.out / str(bc["query_log"]))]
        if self.thiet_ke == "qualitative":
            self._ban_go_bang(hang)
        self.chay("G5 khoá dữ liệu (quản lý dữ liệu)", "lock_analysis_dataset.py", *tham)
        self.cong["G5_truoc_ky"] = {"trang_thai": self.cham("G5"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G5", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G5", "G5_checkpoint.json", "DATA_GOVERNANCE_QA_REVIEWER", "GIA-LAP-DM")
        self._ky("G5", "G5_checkpoint.json", "PI", "GIA-LAP-PI")
        self.cong["G5"] = {"trang_thai": self.cham("G5")}
        self.do_truc("sau_G5")

    def _ban_go_bang(self, hang: Sequence[Mapping[str, Any]]) -> None:
        """Đề tài ĐỊNH TÍNH: quản lý dữ liệu nộp bản gỡ băng ĐÃ KHỬ ĐỊNH DANH (mỗi người tham gia một tệp .txt, chỉ
        đọc) và khai TRANSCRIPT_manifest (băm SHA-256, deidentified, mã người rà) — việc ĐÚNG VAI trước khi khoá
        (G5-AUTO-10). Nội dung là lời mô phỏng theo chủ đề đã mã hoá, không chứa mẫu PII (ngày, số điện thoại, email,
        số định danh)."""
        import hashlib  # noqa: PLC0415
        import stat  # noqa: PLC0415

        import g5_quality_gate as G5Q  # noqa: PLC0415

        thu = self.out / "transcripts"
        thu.mkdir(exist_ok=True)
        muc = []
        for r in hang:
            tid = str(r.get("transcript_id") or "").strip()
            if not tid:
                continue
            tep = thu / f"{tid}.txt"
            if tep.exists():
                tep.chmod(stat.S_IWUSR | stat.S_IRUSR)
            noi_dung = (f"BẢN GỠ BĂNG ĐÃ KHỬ ĐỊNH DANH — {tid} ({GL.NHAN})\n\n"
                        "Người phỏng vấn: Anh/chị cảm thấy thế nào khi được bác sĩ đề nghị bắt đầu tiêm insulin?\n"
                        f"Người tham gia: {r.get('chu_de') or 'Tôi còn nhiều băn khoăn lúc đầu'}. "
                        "Lúc đầu tôi ngại, nhưng được hướng dẫn kỹ thì yên tâm hơn.\n"
                        "Người phỏng vấn: Điều gì giúp anh/chị duy trì việc tiêm?\n"
                        "Người tham gia: Gia đình nhắc nhở và nhân viên y tế giải thích rõ cách tiêm.\n")
            tep.write_text(noi_dung, encoding="utf-8", newline="\n")
            tep.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            muc.append({"transcript_id": tid, "file": f"transcripts/{tep.name}",
                        "sha256": hashlib.sha256(tep.read_bytes()).hexdigest(), "deidentified": True,
                        "reviewer_ref": "GIA-LAP-DM"})
        mf = self.out / G5Q.TRANSCRIPT_MANIFEST_JSON
        du = _doc_json(mf) or {"schema_version": "G5-TRANSCRIPT-2026.1", "disclaimer": "Cần bác sĩ kiểm chứng."}
        du["transcripts"] = muc
        mf.write_text(json.dumps(du, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        self.du_lieu["ban_go_bang"] = len(muc)

    def _soan_phieu_thu_thap(self) -> None:
        """PI soạn PHIẾU THU THẬP SỐ LIỆU nộp Hội đồng (G2) từ bộ biến + mã câu hỏi của ma trận — việc ĐÚNG VAI
        (hệ chưa có lệnh sinh khung phiếu; G5-AUTO-11/13 đối chiếu phiếu này với từ điển nhập liệu).

        17/11/2026 (diễn tập trên khung THẬT BTM): phiếu đã có mà không do bộ giả lập sinh (không mang nhãn giả lập) là
        phiếu chủ nhiệm soạn — KHÔNG ghi đè (bản cũ thay phiếu 6 phần của BTM bằng danh sách biến phẳng)."""
        tep = self.out / f"PHIEU_THU_THAP_SO_LIEU_{self.study}.md"
        if tep.is_file() and GL.NHAN not in tep.read_text(encoding="utf-8"):
            return
        bs = self.kb.get("bien_so") or {}
        ma_cau = {d[3]: d[5] for d in bs.get("ma_tran", ()) if len(d) > 5 and d[5]}
        dong = [f"# PHIẾU THU THẬP SỐ LIỆU — {self._meta().get('title') or self.kb.get('topic')}", "",
                f"Phiên bản 1.0 · nộp kèm hồ sơ Hội đồng Đạo đức · {GL.NHAN}", ""]
        # 17/11/2026 (kịch bản chân thực): có `meta_bien` ⇒ phiếu chia PHẦN theo tiêu đề phần của từ điển, câu có
        # nhánh ghi «chỉ hỏi khi …», câu chọn nhiều ghi «chọn mọi ý đúng», trường calc ghi «máy tự tính».
        meta = bs.get("meta_bien") or {}
        so_cau = {d[0]: (meta.get(d[0]) or {}).get("ma_cau") or ma_cau.get(d[0]) or f"C{i}"
                  for i, d in enumerate(bs.get("bo_bien", ()), 1)}

        def doc_nhanh(bt: str) -> str:
            """«[x] = '1' and [y] >= 2» ⇒ «câu C3 = 1 và câu C7 ≥ 2» (văn bản nộp không mang cú pháp REDCap)."""
            v = re.sub(r"\[(\w+)(?:\((\w+)\))?\]", lambda k: f"câu {so_cau.get(k.group(1), k.group(1))}"
                       + (f" chọn ý {k.group(2)}" if k.group(2) else ""), bt)
            v = re.sub(r"'([^']*)'", r"\1", v).replace(">=", "≥").replace("<=", "≤").replace("<>", "≠")
            return re.sub(r"\s+and\s+", " và ", re.sub(r"\s+or\s+", " hoặc ", v, flags=re.I), flags=re.I)

        for i, (ten, kieu, nhan, lua, _v, _lo, _hi) in enumerate(bs.get("bo_bien", ()), 1):
            m = meta.get(ten) or {}
            if m.get("phan"):
                dong += ["", f"## PHẦN {m['phan']}", ""]
            ma = so_cau[ten]
            lc = f" — lựa chọn: {lua}" if lua and kieu in ("radio", "dropdown") else (
                " — Có/Không" if kieu == "yesno" else f" — chọn mọi ý đúng: {lua}" if kieu == "checkbox" else
                " — máy tự tính, không ghi tay" if kieu == "calc" else "")
            dk = f" *(chỉ hỏi khi {doc_nhanh(m['nhanh'])})*" if m.get("nhanh") else ""
            dong.append(f"- {ma}. {nhan} (`{ten}`){lc}{dk}")
        (self.out / f"PHIEU_THU_THAP_SO_LIEU_{self.study}.md").write_text("\n".join(dong) + "\n", encoding="utf-8",
                                                                         newline="\n")
        self.o.append({"cong": "G2", "tep": f"PHIEU_THU_THAP_SO_LIEU_{self.study}.md", "dong": 0,
                       "nhan": "PI soạn phiếu thu thập (hệ chưa có lệnh sinh khung)", "o": "", "vi_tri": -1,
                       "loai": "moi_dung_vai", "dien": f"{len(bs.get('bo_bien', ()))} câu"})

    def _chot_dmp(self) -> None:
        """Quản lý dữ liệu CHỐT DMP lúc khoá (đúng vai): đánh dấu checklist khoá, bỏ nhãn nháp ở tiêu đề."""
        import g5_quality_gate as G5Q  # noqa: PLC0415

        for p in self.out.glob(f"G5_A6_DATA_MGMT_{self.study}*.md"):
            t = p.read_text(encoding="utf-8")
            khoi = G5Q._dmp_khoi_khoa(t)
            if khoi:
                t = t.replace(khoi, re.sub(r"^(\s*[-*]\s+)\[\s\]", r"\1[x]", khoi, flags=re.M), 1)
            # danh sách việc của DMP (nhập CRF, nạp từ điển, thu thập, kiểm 10% phiếu, làm sạch, ký biên bản) đã làm
            # xong khi khoá ⇒ quản lý dữ liệu đánh dấu
            t = re.sub(r"^(\s*[-*]\s+)\[\s\]", r"\1[x]", t, flags=re.M)
            dong = t.splitlines()
            for i, ln in enumerate(dong[:15]):
                if "**Trạng thái:**" in ln:  # dòng trạng thái nháp («DRAFT — CHỜ … ĐIỀN CÁC [CẦN...]») ⇒ chốt cả dòng
                    chot = f"ĐÃ CHỐT KHI KHOÁ ({self.hom_nay.isoformat()}) — quản lý dữ liệu đã xác nhận"
                    dong[i] = re.sub(r"(\*\*Trạng thái:\*\*).*$", lambda m: f"{m.group(1)} {chot}", ln)
                elif ln.startswith("# "):
                    dong[i] = re.sub(r"\s*\(?\bDRAFT\b\)?", " (ĐÃ CHỐT KHI KHOÁ)", ln)
            p.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")

    def _van_hanh_g5(self) -> None:
        """Quản lý dữ liệu khai hồ sơ vận hành G5 (phân quyền, sao lưu–phục hồi, lưu trữ, sai lệch đề cương, nhật ký
        kiểm toán, đối chiếu nguồn) — việc ĐÚNG VAI, ghi bằng ngày chạy."""
        nay = self.hom_nay.isoformat()
        p = self.out / "G5_OPERATIONAL_READINESS.json"
        ops = _doc_json(p)
        ops.update({"schema_version": "G5-OPS-2026.2", "status": "VERIFIED",
                    "access_control_review": {"completed": True, "reviewed_at": nay, "least_privilege_confirmed": True,
                                              "evidence_ref": "GIA-LAP-ACCESS"},
                    "backup_restore_test": {"completed": True, "tested_at": nay, "restore_verified": True,
                                            "checksum_verified": True, "evidence_ref": "GIA-LAP-BACKUP"},
                    "retention_plan": {"confirmed": True, "retention_rule": "2 năm sau khi kết thúc nghiên cứu"},
                    "protocol_deviations": {"reconciled": True, "open_count": 0, "log_ref": "GIA-LAP-DEV"},
                    "audit_trail_review": {"completed": True, "reviewed_at": nay, "evidence_ref": "GIA-LAP-AUDIT"},
                    "source_data_verification": {"method": "Nhập kép độc lập 100% phiếu (Excel + SPSS) + đối chiếu "
                                                           "phiếu gốc mọi ô lệch", "fraction_or_n": "100%",
                                                 "completed": True, "evidence_ref": "nhap_lieu/so_sanh_1"},
                    "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER", "reviewer_ref": "GIA-LAP-DM"})
        _ghi_json(p, ops)

    def _bo_sung_epv(self, sap: Path) -> None:
        """Thống kê viên bổ sung EPV/VIF vào §5 (G4-AUTO-04) — tính từ N hiệu lực và tỷ lệ biến cố của G3. Việc ĐÚNG VAI
        (không phải ô máy để lại), ghi `moi_dung_vai` để đếm."""
        if not sap.is_file():
            return
        s = sap.read_text(encoding="utf-8")
        # 16/11/2026: §5 của định tính (chiến lược mã hoá) và tổng quan–gộp (tổng hợp cấp nghiên cứu) không có mô hình
        # hồi quy cá thể — G4-AUTO-04 miễn; thống kê viên không chèn EPV/VIF (bản cũ chèn «EPV ≈ 4 biến cố» vào SAP
        # định tính)
        if re.search(r"### §5 (?:CHIẾN LƯỢC MÃ HÓA|TỔNG HỢP ĐỊNH LƯỢNG)", s):
            return
        than5 = re.search(r"(### §5[^\n]*\n)(.*?)(?=\n### §6|\Z)", s, re.S)
        if not than5 or re.search(r"\b(EPV|EPP|VIF|pmsampsize)\b", than5.group(2)):
            return
        g3, cp3 = _gp(self._meta(), "G3"), self._cp("G3")
        n = float(cp3.get("confirmed_n") or cp3.get("n_adjusted") or 0)
        so_bien = sum(1 for d in (self.kb.get("bien_so") or {}).get("ma_tran", ())
                      if d[2] in ("phoi_nhiem", "hiep_bien", "yeu_to"))
        p = float(g3.get("p0") or g3.get("prevalence") or 0.2)
        bien_co = n * min(p, 1 - p)
        cau = (f"- **EPV/VIF (thống kê viên):** EPV ước tính ≈ {bien_co:.0f} biến cố / {max(so_bien, 1)} tham số ≈ "
               f"{bien_co / max(so_bien, 1):.0f}; kiểm đa cộng tuyến VIF < 5 trước khi chốt mô hình.\n")
        s = s[:than5.end(1)] + cau + s[than5.end(1):]
        sap.write_text(s, encoding="utf-8", newline="\n")
        self.o.append({"cong": "G4", "tep": sap.name, "dong": 0, "nhan": "EPV/VIF §5 (thống kê viên bổ sung)",
                       "o": "", "vi_tri": -1, "loai": "moi_dung_vai", "dien": cau.strip()})

    # ── G6: script phân tích → đặc tả SAP (thống kê viên) → chạy trọn SAP + kiểm chéo SPSS/R → .sav → xác nhận
    def _dac_ta_g6(self) -> Optional[Dict[str, Any]]:
        """Thống kê viên giả lập soạn `G6_DAC_TA_SAP.json` từ hồ sơ + SAP đã khoá; mục SAP bắt buộc mà hồ sơ chưa ánh xạ
        ⇒ `chua_tu_dong` (liệt kê «chờ làm tay», không bỏ im). Duyệt kèm dấu đặc tả — CHỈ đề tài tổng hợp trong thư mục
        tạm (người thật ghi `nguoi_duyet` cho đề tài thật)."""
        mau = (self.kb.get("ho_so_tron_vong") or {}).get("g6")
        sap = self.out / f"G4_A5_SAP_FINAL_{self.study}.md"
        if not mau or not sap.is_file():
            return None
        import chay_sap_g6 as CS6  # noqa: PLC0415

        text = sap.read_text(encoding="utf-8")
        chinh = next(x for x in mau if x.get("vai") == "chinh")
        ts_chinh = dict(chinh["tham_so"])
        if ts_chinh.get("outcome") and "outcome_type" not in ts_chinh and not ts_chinh.get("loai_dac_thu"):
            ts_chinh["outcome_type"] = loai_kc_tu_sap(text)
        ds: List[Dict[str, Any]] = []
        for x in mau:
            pt = {k: v for k, v in x.items() if k != "ke_thua"}
            if x is chinh:
                pt["tham_so"] = ts_chinh
            elif x.get("ke_thua"):
                pt["tham_so"] = {k: v for k, v in {**ts_chinh, **(x.get("tham_so") or {})}.items() if v is not None}
            if pt.get("sap_neo") == "<§4>":
                pt["sap_neo"] = phuong_phap_sap(text)
            ds.append(pt)
        for i, (muc, dong) in enumerate(CS6.kiem_phu_sap({"phan_tich": ds}, text)["muc_chua_phu"], 1):
            neo = dong[2:].strip()[:60].strip()
            ds.append({"id": f"CHO_LAM_TAY_{i}", "vai": "do_nhay" if muc == "§9" else "phu", "sap_muc": muc,
                       "mo_ta": neo, "sap_neo": neo,
                       "chua_tu_dong": "hồ sơ chưa ánh xạ mục SAP này sang tham số phân tích — thống kê viên làm tay"})
        dt: Dict[str, Any] = {"nguon_sap": sap.name, "sha256_sap": CS6.sha256_tep(sap), "phan_tich": ds}
        if duoi_pytest_khoa_gia():
            dt["nguoi_duyet"] = f"STATISTICIAN:GIA-LAP-TKV:{self.hom_nay.isoformat()}:{CS6.dau_dac_ta(dt)}"
        _ghi_json(self.out / CS6.TEP_DAC_TA, dt)
        return dt

    # Dòng mẫu do run_g6_auto để dạng chú thích: nạp RDS khoá + kiểm dấu, công thức mô hình chính, lời gọi ước lượng
    # robust. Thống kê viên đối chiếu với SAP §4 rồi BẬT (G6-AUTO-09: chỉ dòng thi hành mới chứng minh script chạy
    # mô hình).
    # 16/11/2026: khuôn mọi thiết kế đánh dấu dòng mô hình chính «◆ MÔ HÌNH CHÍNH (SAP §4)» — thống kê viên bật đúng
    # dòng đó (bệnh chứng/chẩn đoán/dự báo/tổng hợp/cắt ngang mô tả), không chỉ dòng «fit_…» của khuôn thuần tập.
    DONG_MO_HINH_CHINH = re.compile(r"^# ((?:df <- readRDS|extracted <- read\.csv|stopifnot\(identical\(attr\(df|"
                                    r"fit_\w+ <- |lmtest::coeftest\(fit_|(?=[^\n]*◆ MÔ HÌNH CHÍNH))[^\n]*)$", re.M)

    def _cong_thuc_phai_sinh(self) -> None:
        """Thống kê viên soạn công thức biến PHÁI SINH từ trường calc của từ điển (vd FIB-4) rồi ghi duyệt — đúng quy
        trình bien_phai_sinh (soan-tu-calc → duyet), CHỈ trên đề tài tổng hợp trong thư mục tạm (16/11/2026)."""
        td = self.out / f"G5_REDCap_dictionary_{self.study}.csv"
        if not td.is_file() or ",calc," not in td.read_text(encoding="utf-8"):
            return
        self.chay("G6 soạn công thức phái sinh từ calc", "bien_phai_sinh.py", "soan-tu-calc", "--study", self.study,
                  "--ghi")
        r = self.chay("G6 thống kê viên duyệt công thức phái sinh", "bien_phai_sinh.py", "duyet", "--study",
                      self.study, "--vai", "THONG_KE_VIEN", "--tham-chieu", "GIA-LAP-TKV", "--ap-dung")
        self.du_lieu["phai_sinh"] = {"ma": r.get("ma"), "cuoi": r["dong"][-2:]}
        self._cap_nhat_bang_bien_g3("công thức biến phái sinh soạn từ trường calc")

    def _bat_mo_hinh_chinh(self) -> None:
        p = self.out / "scripts" / "03_analysis.R"
        if p.is_file():
            t = p.read_text(encoding="utf-8")
            moi = self.DONG_MO_HINH_CHINH.sub(r"\1", t)
            if moi != t:
                p.write_text(moi, encoding="utf-8", newline="\n")
                self.du_lieu.setdefault("g6_thong_ke_vien", []).append(
                    f"bật {len(self.DONG_MO_HINH_CHINH.findall(t))} dòng mô hình chính trong 03_analysis.R")

    def g6(self) -> None:
        self.chay("G6 sinh script phân tích", "run_g6_auto.py", "--study", self.study)
        a7 = self.out / f"G6_A7_ANALYSIS_SCRIPTS_{self.study}.md"
        self.hoan_thien_tep("G6", a7, list(TRA_LOI_CHUNG), {})
        self._cong_thuc_phai_sinh()
        dt = self._dac_ta_g6()
        if dt:
            self.chay("G6 kiểm đặc tả SAP", "chay_sap_g6.py", "kiem", "--study", self.study)
            self.chay("G6 chạy trọn SAP + kiểm chéo SPSS/R", "chay_sap_g6.py", "chay", "--study", self.study,
                      "--kiem-cheo", timeout=7200)
            kq = _doc_json(self.out / "G6_SAP_ket_qua.json")
            self.du_lieu["g6"] = {"dem": kq.get("dem"), "phan_tich": [
                {k: x.get(k) for k in ("id", "vai", "trang_thai", "kiem_cheo", "ly_do", "uoc_luong")}
                for x in kq.get("phan_tich") or []]}
        else:
            self.du_lieu["g6"] = {"khong_tu_dong": f"thiết kế {self.thiet_ke}: engine phân tích (run_stats_analysis/"
                                                   "chay_sap_g6) chưa có đường cho phân tích chính của thiết kế này"}
        self._bat_mo_hinh_chinh()
        r = self.chay("SPSS — xuất .sav có nhãn từ dữ liệu khoá", "cau_noi_spss.py", "xuat-sav", "--study", self.study)
        self.du_lieu["sav"] = {"ma": r.get("ma"), "cuoi": r["dong"][-2:]}
        import g6_quality_gate as G6Q  # noqa: PLC0415

        meta = self._meta()
        meta.setdefault("gate_params", {})["G6"] = {
            "scripts_match_sap_confirmed": True, "reviewed_by_role": "STATISTICIAN", "reviewed_at": GL._bay_gio(),
            "dau_van_tay_chot": G6Q.dau_van_tay_script(self.out, self.study)}
        self._ghi_meta(meta)
        self.cong["G6"] = {"trang_thai": self.cham("G6"),
                           "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G6", self.study, self.out, self.repo))}
        self.do_truc("sau_G6")

    # ── G6.5: bản diễn giải — người diễn giải chép số TỪ tóm tắt phân tích, dẫn đúng tệp kết quả engine ghi
    # Thước đo người diễn giải có thể chép (16/11/2026 — mở rộng từ thuần tập ra 8 thiết kế): mỗi thước đo đọc ĐÚNG khoá
    # engine ghi và dẫn ĐÚNG tệp kết quả chứa số đó (bản diễn giải đối chiếu số với tệp nguồn).
    THUOC_DO = ("pr_hieu_chinh", "pr_tho", "hieu_so_nguy_co", "or_hieu_chinh", "or_tho", "ty_le", "auc", "do_nhay",
                "do_dac_hieu", "ppv", "npv", "c_statistic", "rr_gop", "rr_gop_co_dinh", "chu_de_1", "hr_hieu_chinh",
                "hr_tho", "pr_mi")

    def _uoc_luong(self, lay: str, gate: str) -> Optional[Dict[str, Any]]:
        tom = _doc_json(self.out / f"{gate}_analysis_summary.json")
        nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
        dt = tom.get("dac_thu") or {}
        tep_tom = f"{gate}_analysis_summary.json"

        def kq(uoc: Any, ci: Any, p: Any, nguon: str, so_le: int, he: float = 1.0) -> Optional[Dict[str, Any]]:
            if uoc is None or not ci or None in ci:
                return None
            return {"uoc": he * uoc, "ci": [he * ci[0], he * ci[1]], "p": p, "nguon": nguon, "so_le": so_le}

        def theo_bien(ds: Any, khoa: str) -> Optional[Dict[str, Any]]:
            return next((x for x in ds or [] if x.get("variable") == nhom and x.get(khoa) is not None), None)

        if lay in ("pr_hieu_chinh", "pr_tho"):
            khoi = tom.get("poisson_pr") or {}
            r = theo_bien(khoi.get("results" if lay == "pr_hieu_chinh" else "tho"),
                          "PR_adj" if lay == "pr_hieu_chinh" else "PR")
            return r and kq(r.get("PR_adj", r.get("PR")), r.get("CI_95"), r.get("p"),
                            f"{gate}_table4_poisson_pr.txt", 2)
        if lay in ("hr_hieu_chinh", "hr_tho"):
            t = (tom.get("survival") or {}).get("adjusted" if lay == "hr_hieu_chinh" else "crude") or {}
            return kq(t.get("HR"), t.get("CI_95"), t.get("p"), f"{gate}_table3_survival.txt", 2)
        if lay == "pr_mi":
            khoi = tom.get("multiple_imputation") or {}
            r = next((x for x in khoi.get("results") or [] if x.get("variable") == nhom), None) or {}
            return kq(r.get("PR_adj", r.get("OR_adj")), r.get("CI_95"), r.get("p"),
                      f"{gate}_table5_multiple_imputation.txt", 2)
        if lay == "hieu_so_nguy_co":
            pc = tom.get("primary_outcome") or {}
            return kq(pc.get("risk_diff"), pc.get("risk_diff_ci_95"), pc.get("p_value"),
                      f"{gate}_table2_main_outcome.txt", 3)
        if lay == "or_hieu_chinh":
            r = theo_bien((tom.get("multivariate") or {}).get("results"), "OR_adj")
            return r and kq(r["OR_adj"], r.get("CI_95"), r.get("p"), f"{gate}_table4_multivariate.txt", 2)
        if lay == "or_tho":
            pc = tom.get("primary_outcome") or {}
            return kq(pc.get("or_crude"), pc.get("ci_95"), pc.get("p_value"), f"{gate}_table2_main_outcome.txt", 2)
        if lay == "ty_le":
            t = next(iter(tom.get("ty_le") or []), None) or {}
            return kq(t.get("ty_le"), t.get("CI_95_wilson_doc_lap"), None, f"{gate}_table1b_proportions.txt", 1, 100.0)
        if lay in ("do_nhay", "do_dac_hieu", "ppv", "npv"):
            t = dt.get(lay) or {}
            return kq(t.get("uoc_luong"), t.get("ci_95_wilson"), None, tep_tom, 2)
        if lay in ("auc", "c_statistic"):
            t = dt.get(lay) or {}
            return kq(t.get("auc"), t.get("ci_95"), None, tep_tom, 2)
        if lay == "rr_gop":
            return kq(dt.get("rr_gop_ngau_nhien"), dt.get("ci_95"), None, tep_tom, 2)
        if lay == "rr_gop_co_dinh":
            return kq(dt.get("rr_gop_co_dinh"), dt.get("ci_95_co_dinh"), None, tep_tom, 2)
        if lay == "chu_de_1":
            t = next(iter(dt.get("chu_de") or []), None) or {}
            return kq(t.get("ty_le"), t.get("ci_95_wilson"), None, tep_tom, 2)
        if lay in ("delta_c", "nmb"):  # kinh tế: VND, KTC 95% bootstrap
            return kq(dt.get("delta_c" if lay == "delta_c" else "nmb_tai_wtp"),
                      dt.get("ci_95_delta_c" if lay == "delta_c" else "ci_95_nmb"), None, tep_tom, 0)
        if lay == "delta_e":
            return kq(dt.get("delta_e"), dt.get("ci_95_delta_e"), None, tep_tom, 3)
        return None

    def _gia_tri_kinh_te(self) -> Dict[str, Any]:
        """Khoá lời văn của phân tích kinh tế (biến thể khó 16/11/2026) — đọc tóm tắt của phân tích «kinh_te»."""
        g = next((f"G6_{pt['id']}" for pt in (self.kb.get("ho_so_tron_vong") or {}).get("g6") or []
                  if (pt.get("tham_so") or {}).get("loai_dac_thu") == "kinh_te"), None)
        kt = (_doc_json(self.out / f"{g}_analysis_summary.json").get("dac_thu") or {}) if g else {}
        if not kt:
            return {}

        def tien(v: Any) -> str:
            return f"{v:,.0f}".replace(",", ".")

        ceac = next((x["ty_le_chi_phi_hieu_qua"] for x in kt.get("ceac") or [] if x.get("boi_so") == 1.0), None)
        return {"icer": tien(kt["icer"]) if kt.get("icer") is not None else "không xác định (ΔE ≈ 0)",
                "delta_c": tien(kt["delta_c"]), "delta_c_duoi": tien(kt["ci_95_delta_c"][0]),
                "delta_c_tren": tien(kt["ci_95_delta_c"][1]), "delta_e_pt": self._so_vn(100 * kt["delta_e"], 1),
                "nmb": tien(kt["nmb_tai_wtp"]), "nmb_duoi": tien(kt["ci_95_nmb"][0]),
                "nmb_tren": tien(kt["ci_95_nmb"][1]), "wtp": tien(kt["nguong_wtp"]),
                "ceac_wtp": "—" if ceac is None else self._so_vn(100 * ceac, 1),
                "goc_phan_tu": str(kt.get("goc_phan_tu") or "").split(" — ")[0]}

    @staticmethod
    def _so_vn(x: float, le: int) -> str:
        return f"{x:.{le}f}".replace(".", ",")

    def g6_5(self) -> None:
        dg = (self.kb.get("ho_so_tron_vong") or {}).get("dien_giai")
        if not dg:
            self.du_lieu["g6_5"] = {"bo_qua": "hồ sơ chưa có bản diễn giải cho thiết kế này"}
            return
        import dien_giai_ket_qua as DG  # noqa: PLC0415

        hang = []
        gt = self._gia_tri_ket_qua()
        for r in dg["bang"]:
            u = self._uoc_luong(r["lay"], r["gate"])
            if not u:
                self.du_lieu.setdefault("g6_5_thieu", []).append(f"{r['gate']}:{r['lay']}")
                continue
            p = u["p"]
            p_txt = "—" if p is None else ("< 0,001" if p < 0.001 else self._so_vn(p, 3))
            hang.append(f"| {r['ket_cuc'].format(**gt)} | {r['thuoc_do']} | {self._so_vn(u['uoc'], u['so_le'])} | "
                        f"{self._so_vn(u['ci'][0], u['so_le'])}–{self._so_vn(u['ci'][1], u['so_le'])} | {p_txt} | "
                        f"{r['y_nghia'].format(**gt)} | `{u['nguon']}` |")
        bang = ("| " + " | ".join(DG.COT_BANG_CHINH) + " |\n|" + "---|" * len(DG.COT_BANG_CHINH) + "\n"
                + "\n".join(hang) + "\n")
        van = (f"# Diễn giải kết quả — {self.study}\n\n"
               f"{DG.MUC[0]}\n\n**Bảng 1.** Kết quả kết cục chính, nhóm nhỏ và độ nhạy (ước lượng, KTC 95%, p — "
               f"đúng như tệp kết quả)\n\n{bang}\n"
               + "".join(f"{DG.MUC[i]}\n\n{dg[f'muc_{i + 1}'].format(**gt)}\n\n" for i in range(1, 5))
               + "> Cần bác sĩ kiểm chứng.\n")
        DG.duong_dan(self.study, self.out).write_text(van, encoding="utf-8", newline="\n")
        r = self.chay("G6.5 kiểm bản diễn giải", "dien_giai_ket_qua.py", "kiem", "--study", self.study)
        self.cong["G6_5"] = {"trang_thai": "DAT" if r.get("ma") == 0 else f"CON_LOI (mã {r.get('ma')})",
                             "loi": [d for d in r["dong"] if d.lstrip().startswith(("✗", "-", "•"))][:12]}

    def _gia_tri_ket_qua(self) -> Dict[str, Any]:
        """Số của phân tích chính để điền lời văn (G6.5, G7…) — luôn đọc lại tệp kết quả, không giữ trong bộ nhớ.

        Mỗi thước đo có trong tóm tắt G6 cho bốn khoá «{ten}», «{ten}_duoi», «{ten}_tren», «{ten}_p» (định dạng Việt,
        đúng số lẻ bản diễn giải dùng) — lời văn của hồ sơ từng thiết kế chỉ dùng chỗ giữ của thước đo thiết kế đó có;
        chỗ giữ không có ⇒ KeyError (lộ ngay, không điền rỗng)."""
        tom = _doc_json(self.out / "G6_analysis_summary.json")
        pc = tom.get("primary_outcome") or {}
        dt = tom.get("dac_thu") or {}
        gt: Dict[str, Any] = {"n": tom.get("n_total")}
        for ten in self.THUOC_DO:
            u = self._uoc_luong(ten, "G6")
            if not u:
                continue
            le = u["so_le"]
            gt.update({ten: self._so_vn(u["uoc"], le), f"{ten}_duoi": self._so_vn(u["ci"][0], le),
                       f"{ten}_tren": self._so_vn(u["ci"][1], le),
                       f"{ten}_p": "—" if u["p"] is None else ("< 0,001" if u["p"] < 0.001
                                                                else self._so_vn(u["p"], 3))})
        # Khoá cũ của thuần tập (hồ sơ 15/11/2026) — giữ nguyên nghĩa
        chinh = self._uoc_luong("pr_hieu_chinh", "G6") or {}
        rd = self._uoc_luong("hieu_so_nguy_co", "G6") or {}
        ci = chinh.get("ci") or [0, 0]
        gt.update({"rr": self._so_vn(chinh.get("uoc", 0), 2), "rr_duoi": self._so_vn(ci[0], 2),
                   "rr_tren": self._so_vn(ci[1], 2), "rd_phan_tram": self._so_vn(100 * rd.get("uoc", 0), 1),
                   "pct1": self._so_vn((pc.get("group_1") or {}).get("pct", 0), 1),
                   "pct0": self._so_vn((pc.get("group_0") or {}).get("pct", 0), 1),
                   "nnh": round(1 / rd["uoc"]) if rd.get("uoc") else "—",
                   "bien_co": (tom.get("poisson_pr") or {}).get("n_bien_co"),
                   "p": "< 0,001" if (chinh.get("p") or 1) < 0.001 else self._so_vn(chinh.get("p") or 0, 3)})
        # Số đếm/thống kê phụ của phân tích đặc thù (đọc thẳng khoá engine ghi)
        bang = dt.get("bang_2x2") or {}
        gt.update({f"so_{k}": v for k, v in bang.items() if k != "nguong"})
        if "nguong" in bang:
            gt["nguong"] = self._so_vn(bang["nguong"], 2)
        for k in ("lr_duong", "lr_am", "brier", "i2_pct", "tau2"):
            if isinstance(dt.get(k), (int, float)):
                gt[k] = self._so_vn(dt[k], 3 if k in ("brier", "tau2") else (1 if k == "i2_pct" else 2))
        for k in ("k", "epv", "n_ban_go_bang", "so_chu_de"):
            if dt.get(k) is not None:
                gt[k] = dt[k]
        for i, cd in enumerate(dt.get("chu_de") or [], 1):
            gt[f"chu_de_{i}_ten"] = cd.get("chu_de")
            gt[f"chu_de_{i}_n"] = cd.get("n")
        t = next(iter(tom.get("ty_le") or []), None) or {}
        if t:
            gt.update({"so_su_kien": t.get("so_su_kien"), "n_ty_le": t.get("n")})
        # biến thể khó (16/11/2026): không kém hơn · cụm · sống còn · dữ liệu thiếu
        if rd:
            gt.update({"hieu_so_phan_tram": self._so_vn(100 * rd["uoc"], 1),
                       "hieu_so_duoi_pt": self._so_vn(100 * rd["ci"][0], 1),
                       "hieu_so_tren_pt": self._so_vn(100 * rd["ci"][1], 1)})
        g3 = _gp(self._meta(), "G3") if hasattr(self, "_meta") else {}
        bien = g3.get("margin")
        if bien and rd:
            gt["bien_ni"] = self._so_vn(100 * float(bien), 0)
            dat_ni = rd["ci"][0] > -float(bien)
            gt["ni_ket_luan"] = ("cận dưới KTC 95% nằm trên biên — đạt tiêu chí không kém hơn" if dat_ni
                                 else "cận dưới KTC 95% chạm hoặc dưới biên — CHƯA chứng minh được không kém hơn")
        ic = tom.get("icc_cluster") or {}
        if ic.get("icc") is not None:
            gt.update({"icc": self._so_vn(float(ic["icc"]), 3),
                       "de": self._so_vn(float(ic.get("hieu_ung_thiet_ke") or 1), 2)})
        sv = tom.get("survival") or {}
        if sv:
            gt["bien_co_sc"] = sv.get("n_events") or sv.get("events") or (sv.get("adjusted") or {}).get("n_events")
        mi = tom.get("multiple_imputation") or {}
        if mi.get("pct_missing_rows") is not None:
            gt["pct_thieu"] = self._so_vn(float(mi["pct_missing_rows"]), 1)
        gt.update(self._gia_tri_kinh_te())
        if pc.get("group_1"):
            gt.update({"n1": pc["group_1"].get("n"), "n0": (pc.get("group_0") or {}).get("n"),
                       "su_kien1": pc["group_1"].get("events"), "su_kien0": (pc.get("group_0") or {}).get("events")})
        return gt

    def _env_mang(self) -> Dict[str, str]:
        """Môi trường cho bước TRA CỨU mạng (kiểm trích dẫn): như phần A — bỏ biến pytest và khoá giả (bước này không
        ký gì; dưới pytest app.config không nạp cấu hình nguồn ⇒ nguồn giả)."""
        return {k: v for k, v in self.env.items()
                if not k.startswith("PYTEST_") and k not in ("EBM_GATE_KEY_PATH", "USE_MOCK_SOURCES")}

    def _tra_a12(self, pmid: Sequence[str]) -> Dict[str, Any]:
        """Tra rút bài + metadata cho tập PMID (bước mạng DUY NHẤT của giả lập).

        17/11/2026 (bác sĩ: «đưa 16 kịch bản vào CI»): CI không có mạng ổn định lẫn khoá NCBI. `GIA_LAP_A12_KHO=<tệp
        .json>` là kho kết quả THEO TỪNG PMID: đủ mọi PMID trong kho ⇒ dựng lại đúng JSON của `check_citations --json`
        và mã thoát theo CÙNG luật «sạch» (`la_van_de`, metadata «resolved») — không gọi mạng. Lượt có mạng thì ghi
        thêm vào kho các PMID có kết luận dứt khoát (bỏ «unknown_*» — lỗi mạng không được thành dữ kiện).
        `GIA_LAP_A12_CHI_KHO=1` ⇒ thiếu PMID trong kho là LỖI nói rõ cách bổ sung, không lặng lẽ gọi mạng."""
        kho = os.environ.get("GIA_LAP_A12_KHO", "").strip()
        d_kho: Dict[str, Dict[str, Any]] = {"retraction": {}, "metadata": {}}
        if kho and Path(kho).is_file():
            try:
                d_kho = json.loads(Path(kho).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                d_kho = {"retraction": {}, "metadata": {}}
        if kho:
            thieu = [x for x in pmid if x not in d_kho.get("retraction", {}) or x not in d_kho.get("metadata", {})]
            if not thieu:
                import check_citation_retraction as CCR  # noqa: PLC0415

                r = {x: d_kho["retraction"][x] for x in pmid}
                m = {x: d_kho["metadata"][x] for x in pmid}
                van_de = any(CCR.la_van_de(r.get(x)) for x in pmid) or any(
                    not isinstance(m.get(x), dict) or m[x].get("status") != "resolved" for x in pmid)
                return {"ma": 1 if van_de else 0, "crash": False, "tu_kho": True,
                        "ra": json.dumps({"retraction": r, "metadata": m}, ensure_ascii=False, indent=2)}
            if os.environ.get("GIA_LAP_A12_CHI_KHO") == "1":
                return {"ma": 9, "crash": False, "ra": (
                    f"Kho A12 ghi sẵn thiếu {len(thieu)} PMID ({', '.join(thieu[:8])}) — chạy giả lập CÓ MẠNG một lần "
                    f"với GIA_LAP_A12_KHO={kho} để bổ sung kho rồi commit tệp kho.")}
        kq = self.chay_lenh(self._lenh("check_citations.py", "--pmids", ",".join(pmid), "--json"),
                            self.repo, self._env_mang(), 900)
        m_json = re.search(r"^\{.*^\}", str(kq.get("ra") or ""), re.S | re.M)
        if kho and m_json:
            try:
                moi = json.loads(m_json.group(0))
            except ValueError:
                moi = {}
            doi = False
            for x in pmid:
                r, mt = (moi.get("retraction") or {}).get(x), (moi.get("metadata") or {}).get(x)
                if (isinstance(r, dict) and isinstance(mt, dict) and not str(r.get("status")).startswith("unknown")
                        and not str(mt.get("status")).startswith("unknown")):
                    d_kho.setdefault("retraction", {})[x] = r
                    d_kho.setdefault("metadata", {})[x] = mt
                    doi = True
            if doi:
                Path(kho).parent.mkdir(parents=True, exist_ok=True)
                Path(kho).write_text(json.dumps({k: dict(sorted(v.items())) for k, v in d_kho.items()},
                                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        return kq

    def _a12(self, *tep: Path, them: Sequence[str] = ()) -> None:
        """Người kiểm trích dẫn: mọi PMID trong các tệp (+ `them`: PMID chuẩn đề cương G10 sẽ chèn) ⇒ check_citations
        (rút bài 3 tầng + metadata, ghi receipt) ⇒ A12 chỉ ghi dòng «đã xác minh» khi lệnh trả 0."""
        pmid = sorted({x for t in tep if t.is_file() for x in re.findall(r"PMID[:\s]*(\d{6,9})",
                                                                         t.read_text(encoding="utf-8"))} | set(them))
        if not pmid:
            return
        # Hai bước TÁCH: (1) tra mạng KHÔNG --study ⇒ không ký gì, dùng cấu hình nguồn thật (dưới pytest app.config
        # không nạp cấu hình ⇒ nguồn giả); (2) ghi receipt bằng ĐÚNG hàm của check_citations trong môi trường KHOÁ GIẢ.
        # Bản đầu
        # gọi thẳng `--study` ngoài biến pytest ⇒ receipt của thư mục giả lập bị ký bằng khoá THẬT (sửa 15/11/2026).
        kq = self._tra_a12(pmid)
        ra = str(kq.get("ra") or "")
        dong = [x for x in ra.splitlines() if x.strip() and "| INFO" not in x]
        self.buoc.append({"buoc": "A12 tra rút bài + metadata (mạng, không ký)", "lenh": "check_citations.py",
                          "ma": kq.get("ma"), "crash": bool(kq.get("crash")), "cuoi": dong[-3:]})
        m = re.search(r"^\{.*^\}", ra, re.S | re.M)
        sach = False
        if m and duoi_pytest_khoa_gia():
            tam = self.repo.parent / "a12_ket_qua.json"
            tam.write_text(m.group(0), encoding="utf-8", newline="\n")
            ky = self.repo.parent / "a12_ky_receipt.py"
            ky.write_text(MA_KY_RECEIPT_A12, encoding="utf-8", newline="\n")
            r2 = self.chay_lenh([sys.executable, "-B", str(ky), self.study, str(tam), ",".join(pmid)], self.repo,
                                self.env, 300)
            self.buoc.append({"buoc": "A12 ghi receipt (khoá giả)", "lenh": "a12_ky_receipt.py", "ma": r2.get("ma"),
                              "crash": bool(r2.get("crash")), "cuoi": str(r2.get("ra") or "").splitlines()[-2:]})
            sach = kq.get("ma") == 0 and r2.get("ma") == 0
        van = (f"# A12 — Xác minh trích dẫn — {self.study}\n\n"
               f"PMID đã kiểm ({len(pmid)}): {', '.join(pmid)}\n\n"
               "Lệnh: `python tools/check_citations.py --pmids <danh sách> --study <mã>` (chuỗi rút bài 3 tầng + "
               "metadata "
               "gốc; receipt `A12_RETRACTION_RECEIPT.json`, `A12_METADATA_RECEIPT.json`).\n\n"
               + ("KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN\n" if sach else
                  f"Còn vấn đề (mã {kq.get('ma')}) — chưa xác minh xong:\n\n"
                  + "\n".join(f"    {d}" for d in dong[-12:])
                  + "\n")
               + "\nCần bác sĩ kiểm chứng.\n")
        (self.out / f"A12_CITATION_VERIFICATION_{self.study}.md").write_text(van, encoding="utf-8", newline="\n")
        rut: List[str] = []
        if m:
            try:
                rut = sorted(k for k, v in (json.loads(m.group(0)).get("retraction") or {}).items()
                             if isinstance(v, dict) and v.get("status") == "retracted")
            except (ValueError, AttributeError):
                rut = []
        self.du_lieu["a12"] = {"pmid": pmid, "sach": sach, "ma": kq.get("ma"), "rut": rut}

    def _quet_a12(self, cong: str) -> None:
        """Người kiểm trích dẫn quét lại TRƯỚC khi ký `cong` (16/11/2026): PMID trong mọi tệp gói cổng đó đòi
        (run_g10_assemble.tep_phu_a12) + đề cương G10 đã lắp mà biên nhận A12 chưa có ⇒ chạy lại A12 trên HỢP, giữ mọi
        PMID đã kiểm (phạm vi chỉ tăng). Quét ở G8/G9 để G10 không phải ghi lại biên nhận nằm trong manifest G9."""
        import danh_muc_trich_dan as DMT  # noqa: PLC0415
        import run_g10_assemble as G10A  # noqa: PLC0415

        tep = [*G10A.tep_phu_a12(self.study, self.out, cong),
               *[t for t in (self.out / f"DE_CUONG_THONG_NHAT_{self.study}.md",) if t.is_file()]]
        van = [t.read_text(encoding="utf-8") for t in tep]
        pmid = {x for v in van for x in G10A._pmids_from_text(v)}
        # 17/11/2026: + nguồn mà đề cương nộp sẽ dẫn (thiết kế G1 A2, bộ biến G3, SAP, đề cương G10, G3 *_source) và DOI
        # tài liệu chuẩn quy về PMID (Piaggio ở bản thảo G7 chỉ có DOI) — cùng phạm vi trục trich_dan_tong_quan; trước
        # đó A12 không kiểm chúng nên bộ sinh đề cương (chỉ nhận PMID đã kiểm) bỏ khỏi TLTK.
        pmid |= set(DMT.pmid_cua_van_ban(*van, *DMT.van_ban_nguon_cong(
            self.out, self.study, _doc_json(self.out / "study_meta.json"))))
        da_kiem = set(_doc_json(self.out / "A12_RETRACTION_RECEIPT.json").get("pmids_checked") or [])
        moi = sorted(pmid - da_kiem)
        if not moi:
            return
        self.du_lieu.setdefault("a12_quet", []).append({"cong": cong, "pmid_moi": moi})
        self._a12(*tep, them=sorted(da_kiem | pmid))

    def _bien_tap_ban_nop(self, a8: Path) -> None:
        """Tác giả chốt bản NỘP: gỡ khung bản nháp bằng công cụ của hệ (`go_khung_ban_thao_g7.py --ap-dung`, thêm
        16/11/2026 — trước đó tác giả phải xoá tay ~40 dòng) rồi tự viết câu khai báo AI trong bản thảo (ICMJE V.A)."""
        if not a8.is_file():
            return
        import g8_quality_gate as G8Q  # noqa: PLC0415

        r = self.chay("G7 gỡ khung bản nháp (công cụ hệ)", "go_khung_ban_thao_g7.py", "--study", self.study,
                      "--ap-dung")
        go = next((int(m.group(1)) for d in r["dong"] for m in [re.search(r"Đã gỡ (\d+) dòng", d)] if m), 0)
        van = a8.read_text(encoding="utf-8")
        ai = ((self.kb.get("ho_so_tron_vong") or {}).get("tac_gia_G7") or {}).get("ai_manuscript_statement")
        if ai and not any(t in van.casefold() for t in ("trí tuệ nhân tạo", "artificial intelligence")):
            van = van.replace("\nCần bác sĩ kiểm chứng.\n", "") .rstrip() + (
                "\n\n**Khai báo sử dụng trí tuệ nhân tạo:** " + ai + "\n\nCần bác sĩ kiểm chứng.\n")
            a8.write_text(van, encoding="utf-8", newline="\n")
        con = G8Q.manuscript_residues(van) + [f"vệt: {v}" for v in G8Q.scan_internal_traces(van)]
        self.du_lieu["g7_bien_tap"] = {"dong_khung_da_go_boi_cong_cu_he": go, "con_lai": [x[:120] for x in con][:20]}

    def _trich_dan_rut_bai(self, a8: Path, rb: Mapping[str, Any]) -> None:
        """Biến thể «trích dẫn đã rút» (16/11/2026): tác giả trích nhầm một bài ĐÃ RÚT ⇒ người kiểm trích dẫn chạy A12
        (chuỗi rút bài 3 tầng) ⇒ phải CHẶN ⇒ tác giả đọc A12, thay bằng nguồn còn hiệu lực ⇒ A12 lần 2 là bước chung
        của G7 (phủ mọi PMID gói sẽ trích)."""
        s = _them_tltk(_chen_cuoi_muc(a8.read_text(encoding="utf-8"), rb["muc"], rb["cau_rut"]), rb["tltk_rut"])
        a8.write_text(s, encoding="utf-8", newline="\n")
        self._a12(a8)
        self.du_lieu["rut_bai"] = {"pmid_rut": rb["pmid_rut"], "pmid_thay": rb["pmid_thay"],
                                   "lan_1": dict(self.du_lieu.get("a12") or {})}
        s = a8.read_text(encoding="utf-8").replace(rb["cau_rut"], rb["cau_thay"]).replace(rb["tltk_rut"],
                                                                                          rb["tltk_thay"])
        a8.write_text(s, encoding="utf-8", newline="\n")
        self.buoc.append({"buoc": f"Tác giả thay trích dẫn đã rút PMID {rb['pmid_rut']} bằng PMID {rb['pmid_thay']} "
                                  "theo A12", "lenh": "(sửa bản thảo)", "ma": 0, "crash": False,
                          "cuoi": [f"còn PMID {rb['pmid_rut']} trong bản thảo: {rb['pmid_rut'] in s}"]})

    def g7(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tg = hs.get("tac_gia_G7") or {}
        tap_chi = tg.get("target_journal") or "Tạp chí Y học Việt Nam"
        self.chay("G7 sinh bản thảo", "run_g7_auto.py", "--study", self.study, "--target-journal", tap_chi)
        a8 = self.out / f"G7_A8_MANUSCRIPT_{self.study}.md"
        gt = self._gia_tri_ket_qua()
        dg = hs.get("dien_giai") or {}
        gt.update({f"muc_{i}": str(dg.get(f"muc_{i}", "")).format(**gt) for i in range(2, 6)})
        tl = [(m, v.format(**gt)) for m, v in hs.get("tra_loi_G7", [])]
        self.hoan_thien_tep("G7", a8, tl + list(TRA_LOI_CHUNG), {})
        self._bien_tap_ban_nop(a8)
        rb = hs.get("rut_bai")
        if rb and a8.is_file():
            self._trich_dan_rut_bai(a8, rb)
        import protocol_checklist_items as PCI  # noqa: PLC0415

        # 16/11/2026: người kiểm trích dẫn phủ MỌI PMID mà gói phát hành sẽ trích TRƯỚC khi G9 khoá — gồm đề cương G10
        # (nguồn cỡ mẫu G3, chuẩn báo cáo, PMID chuẩn đề cương SPIRIT 2025 / PRISMA-P 2015). Kiểm muộn ở G10 thì ghi lại
        # biên nhận A12 làm vỡ manifest G9 đã khoá (RCT: 20332511, 35342691; tổng quan: 25554246). Bản nháp đề cương
        # dựng ở đây chỉ để đọc PMID — G10 dựng lại sau G9.
        self.chay("G7 dựng nháp đề cương G10 (liệt kê PMID gói sẽ trích)", "run_g10_assemble.py", "--study", self.study)
        self._a12(a8, self.out / f"G6_DIEN_GIAI_{self.study}.md", self.out / f"DE_CUONG_THONG_NHAT_{self.study}.md",
                  them=sorted(PCI.pmid_tai_lieu_chuan(self._cp("G1").get("design", {}).get("internal_code")
                                                      or self._cp("G3").get("design_code") or "")))
        if rb:
            self.du_lieu.setdefault("rut_bai", {})["lan_2"] = dict(self.du_lieu.get("a12") or {})
        import cong_song as CS  # noqa: PLC0415

        meta = self._meta()
        meta["results_final"] = True  # PI xác nhận số trong bản thảo là số cuối của G6 (đề tài tổng hợp)
        meta.setdefault("gate_params", {})["G7"] = {
            **{k: v for k, v in tg.items()}, "target_journal": tap_chi,
            "title": tg.get("title") or meta.get("title") or meta.get("topic"),
            "manuscript_reviewed_confirmed": True, "reviewed_by_role": "PI", "reviewed_at": GL._bay_gio(),
            "dau_van_tay_chot": CS.dau_van_tay(a8.read_text(encoding="utf-8").replace("\r\n", "\n"))
            if a8.is_file() else None}
        self._ghi_meta(meta)
        self.cong["G7"] = {"trang_thai": self.cham("G7"),
                           "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G7", self.study, self.out, self.repo))}
        self.do_truc("sau_G7")

    # ── G8–G10: bình duyệt độc lập · liêm chính tác giả · khoá gói phát hành
    def _dien_cong(self, g: str, mau_tep: str, tra_loi: Sequence[Tuple[str, str]] = ()) -> None:
        da_hoi: Dict[str, str] = {}
        for tep in sorted(self.out.glob(mau_tep)):
            if "PEER_REVIEW_REPORT" not in tep.name:
                self.hoan_thien_tep(g, tep, list(tra_loi) + list(TRA_LOI_CHUNG), da_hoi)

    def _cap_nhat_bang_bien_g3(self, ly_do: str) -> None:
        """PI cập nhật bảng bộ biến G3 khi bộ biến máy đổi SAU khi bảng đã duyệt (mã thiếu khai lúc nhập liệu, công
        thức phái sinh soạn từ calc ở G6) — 17/11/2026, MT-12 «bộ biến máy đã đổi sau khi soạn bảng». Như nhóm thật:
        PI gỡ xác nhận cũ → agent soạn lại bằng bang_bien_g3 → PI đọc và ghi xác nhận gắn dấu nội dung mới. Bảng do
        người soạn hoặc nguồn không đổi ⇒ không làm gì (công cụ cũng không bao giờ ghi đè bảng người soạn)."""
        import bang_bien_g3 as BB  # noqa: PLC0415

        st = BB.trang_thai(self.out, self.study, self._meta())
        if not st.get("nguon_doi") or st.get("trang_thai") == BB.NGUOI_SOAN:
            return
        meta = self._meta()
        cu = meta.setdefault("gate_params", {}).setdefault("G3", {}).pop(BB.KHOA_DUYET, None)
        self._ghi_meta(meta)
        r = self.chay(f"PI soạn lại bảng bộ biến G3 ({ly_do})", "bang_bien_g3.py", "soan", "--study", self.study,
                      "--ghi")
        st = BB.trang_thai(self.out, self.study, self._meta())
        if r.get("ma") == 0 and st.get("dau_hien_tai") and not st.get("nguon_doi"):
            self._vao_meta("G3", {BB.KHOA_DUYET: {"reviewed_at": GL._bay_gio(), "dau_van_tay": st["dau_hien_tai"]}})
            self.buoc.append({"buoc": f"PI đọc bảng bộ biến G3 soạn lại và ghi dấu {st['dau_hien_tai']}",
                              "lenh": "(PI duyệt bảng G3)", "ma": 0, "crash": False, "cuoi": [ly_do]})
        elif cu is not None:  # công cụ từ chối soạn lại (bảng đã sửa tay…) ⇒ giữ xác nhận cũ, MT-12 còn cảnh báo
            self._vao_meta("G3", {BB.KHOA_DUYET: cu})

    def _vao_meta(self, g: str, gia_tri: Mapping[str, Any]) -> None:
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault(g, {}).update(dict(gia_tri))
        self._ghi_meta(meta)

    def _ghi_phan_bien(self, vong: Optional[int] = None) -> None:
        """Người phản biện ĐỘC LẬP (mô phỏng, vai riêng GIA-LAP-PB) viết bản nhận xét theo mẫu binh-duyet.md từ hồ
        sơ. `vong` (biến thể «vòng sửa sau phản biện»): 1 ⇒ «Sửa lớn» + bảng lỗi nghiêm trọng + «cần sửa thêm»; 2 ⇒
        bản vòng sau, đối chiếu từng lỗi vòng 1 đã xử lý; None ⇒ một vòng như mọi kịch bản."""
        hs = self.kb.get("ho_so_tron_vong") or {}
        pb, vs = hs.get("phan_bien_G8"), hs.get("vong_sua_G8") or {}
        if not pb:
            return
        gt = self._gia_tri_ket_qua()
        if vong == 1:
            khuyen, lk1 = "☐ Chấp nhận ☐ Sửa nhỏ ☑ Sửa lớn ☐ Từ chối", "☐ PASS ☐ Lỗi nhỏ ☑ Lỗi nghiêm trọng"
            ly_do = vs["vong_1"]["ly_do"]
            hang = [f"| {i} | {vt} | {lo} | {de} |" for i, (vt, lo, de) in enumerate(vs["vong_1"]["loi"], 1)]
            loi = "| # | Vị trí | Lỗi | Đề xuất sửa |\n|---|--------|-----|-------------|\n" + "\n".join(hang)
            ket_luan = f"cần sửa thêm (xử lý {len(vs['vong_1']['loi'])} lỗi nghiêm trọng rồi gửi lại vòng 2)"
        else:
            khuyen, lk1 = "☐ Chấp nhận ☑ Sửa nhỏ ☐ Sửa lớn ☐ Từ chối", "☐ PASS ☑ Lỗi nhỏ ☐ Lỗi nghiêm trọng"
            ly_do = ((vs["vong_2"]["ly_do"] + " ") if vong == 2 else "") + pb["ly_do"].format(**gt)
            loi = "Không có."
            ket_luan = "sẵn sàng nộp (sau khi xử lý các góp ý nhỏ)"
        doi_chieu = ("\n════════ ĐỐI CHIẾU LỖI VÒNG 1 (người phản biện đọc lại bản sửa) ════════\n"
                     + "\n".join(f"- {d}" for d in vs["vong_2"]["doi_chieu"]) + "\n") if vong == 2 else ""
        nhan_vong = f" — VÒNG {vong}" if vong else ""
        bang_nho = "\n".join(f"| {i} | {vt} | {gy} |" for i, (vt, gy) in enumerate(pb["gop_y_nho"], 1))
        hoi = "\n".join(f"{i}. {c}" for i, c in enumerate(pb["cau_hoi"], 1))
        van = f"""# Bản nhận xét phản biện — {self.study}

════════════════════════════════════════════════════════════════
TÓM TẮT NHẬN XÉT — {pb["ten_bai"]} — {pb["thiet_ke"]} — G8{nhan_vong} / {self.hom_nay.isoformat()}
════════════════════════════════════════════════════════════════

KHUYẾN NGHỊ: {khuyen}
Lý do: {ly_do}

════════ LỖI NGHIÊM TRỌNG (phải sửa trước khi nộp) ════════
{loi}
{doi_chieu}
════════ GÓP Ý NHỎ (nên sửa) ════════
| # | Vị trí | Góp ý |
|---|--------|-------|
{bang_nho}

════════ CÂU HỎI CHO TÁC GIẢ ════════
{hoi}

════════ ĐỐI CHIẾU CHECKLIST {pb["checklist"]} ════════
Tỷ lệ đạt: {pb["checklist_dat"]}
Mục thiếu quan trọng: {pb["checklist_thieu"]}

════════ CỔNG TRÍCH DẪN ════════
Trích dẫn nghi vấn cần xác minh: không có — A12 đã chạy chuỗi rút bài 3 tầng + metadata
Trạng thái tổng thể: ☑ PASS (đã qua kiem-chung-trich-dan) ☐ CẦN XÁC MINH

════════ ĐA LĂNG KÍNH TÓM TẮT ════════
Lăng kính 1 (Phương pháp): {lk1}
Lăng kính 2 (Thống kê): ☑ PASS ☐ Lỗi nhỏ ☐ Lỗi nghiêm trọng
Lăng kính 3 (Liêm chính): ☑ PASS ☐ Lỗi nhỏ ☐ Lỗi nghiêm trọng

════════ KHAI BÁO CỦA NGƯỜI PHẢN BIỆN (bắt buộc — ICMJE Mục V.B + §II.B.1.b) ════════
Xung đột lợi ích với nhóm nghiên cứu: ☑ Không có ☐ Có (ghi rõ):
Có phải đồng tác giả/cấp trên/cấp dưới trực tiếp của tác giả không: ☑ Không ☐ Có
Có dùng AI khi phản biện không: ☐ Không ☑ Có (tên công cụ + mục đích): công cụ hỗ trợ rà soát theo bảng kiểm chuẩn \
báo cáo; người phản biện đọc toàn văn và chịu trách nhiệm nhận xét
Cam kết KHÔNG tải bản thảo lên công cụ AI thiếu bảo đảm bảo mật khi chưa được tạp chí/chủ nhiệm cho phép: ☑ Xác nhận

Kết luận tổng thể: {ket_luan}
════════════════════════════════════════════════════════════════
"""
        (self.out / f"G8_PEER_REVIEW_REPORT_{self.study}.md").write_text(van, encoding="utf-8", newline="\n")

    def _tham_so_g8(self) -> Dict[str, Any]:
        hs = self.kb.get("ho_so_tron_vong") or {}
        po = _gp(self._meta(), "G1").get("primary_outcome") or {}
        return {**(hs.get("tham_so_G8") or {}), "primary_outcome": po.get("name") if isinstance(po, Mapping) else None,
                "reviewer_coi_declared": True, "reviewer_independence_declared": True,
                "reviewer_ai_use_declared": True, "reviewer_confidentiality_declared": True,
                "reviewed_at": GL._bay_gio()}

    def _vong_1_g8(self, vs: Mapping[str, Any], tap_chi: str) -> None:
        """Biến thể «vòng sửa sau phản biện» (16/11/2026): vòng 1 phản biện «Sửa lớn» ⇒ G8 KHÔNG được ký (PI thử ký
        phải bị từ chối) ⇒ tác giả sửa bản thảo ⇒ chấm G7 phải thấy bản thảo đổi sau xác nhận ⇒ PI đọc lại và xác nhận
        bản sửa ⇒ người phản biện viết vòng 2 (bước chung của G8)."""
        hs = self.kb.get("ho_so_tron_vong") or {}
        self._ghi_phan_bien(vong=1)
        self._quet_a12("G8")
        self._vao_meta("G8", self._tham_so_g8())
        self.chay("G8 vòng 1 — sinh hồ sơ trước nộp (A9)", "run_g8_auto.py", "--study", self.study,
                  "--target-journal", tap_chi)
        self._dien_cong("G8", f"G8_*{self.study}*.md", hs.get("tra_loi_G8", []))
        v1: Dict[str, Any] = {"trang_thai": self.cham("G8"),
                              "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G8", self.study, self.out, self.repo))}
        v1["ky_ma"] = self._ky("G8", f"G8_A9_PRESUBMISSION_{self.study}.md", "INDEPENDENT_PEER_REVIEWER",
                               "GIA-LAP-PB").get("ma")
        self.cong["G8_vong_1"] = v1
        a8 = self.out / f"G7_A8_MANUSCRIPT_{self.study}.md"
        s = a8.read_text(encoding="utf-8")
        for muc, doan in vs["sua"]:
            s = _chen_cuoi_muc(s, muc, doan)
        a8.write_text(s, encoding="utf-8", newline="\n")
        self.buoc.append({"buoc": f"Tác giả sửa bản thảo theo {len(vs['sua'])} lỗi nghiêm trọng của phản biện vòng 1",
                          "lenh": "(sửa bản thảo)", "ma": 0, "crash": False, "cuoi": [m for m, _d in vs["sua"]]})
        self.cong["G7_sau_sua_chua_xac_nhan"] = {
            "trang_thai": self.cham("G7"),
            "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G7", self.study, self.out, self.repo))}
        import cong_song as CS  # noqa: PLC0415

        meta = self._meta()  # PI đọc bản sửa và xác nhận lại (dấu vân tay mới của bản thảo)
        meta.setdefault("gate_params", {}).setdefault("G7", {}).update({
            "dau_van_tay_chot": CS.dau_van_tay(s.replace("\r\n", "\n")), "reviewed_at": GL._bay_gio(),
            "manuscript_reviewed_confirmed": True})
        self._ghi_meta(meta)
        self.cong["G7_sau_sua"] = {"trang_thai": self.cham("G7"),
                                   "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G7", self.study, self.out,
                                                                                self.repo))}
        self.du_lieu["vong_sua"] = {"vong_1": v1, "da_sua_du": all(k in s for k in vs["vong_2"]["kiem_co"])}

    def g8(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tap_chi = (hs.get("tac_gia_G7") or {}).get("target_journal") or "Tạp chí Y học Việt Nam"
        vs = hs.get("vong_sua_G8")
        if vs:
            self._vong_1_g8(vs, tap_chi)
            # giữ vết kiểm toán: bản nhận xét vòng 1 lưu vào thư mục con (tên tệp của cổng là cố định — vòng 2 thay)
            v1 = self.out / f"G8_PEER_REVIEW_REPORT_{self.study}.md"
            if v1.is_file():
                (self.out / "G8_lich_su_phan_bien").mkdir(exist_ok=True)
                shutil.copy2(v1, self.out / "G8_lich_su_phan_bien" / f"VONG_1_{v1.name}")
        self._ghi_phan_bien(vong=2 if vs else None)  # bản nhận xét có TRƯỚC A9 — A9 nhúng băm nó (G8-AUTO-12b)
        self._quet_a12("G8")  # bản nhận xét có thể trích chuẩn báo cáo (vd CONSORT mở rộng) chưa qua A12
        self._vao_meta("G8", self._tham_so_g8())
        self.chay("G8 sinh hồ sơ trước nộp (A9)", "run_g8_auto.py", "--study", self.study, "--target-journal", tap_chi)
        self._dien_cong("G8", f"G8_*{self.study}*.md", hs.get("tra_loi_G8", []))
        self.cong["G8_truoc_ky"] = {"trang_thai": self.cham("G8"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G8", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G8", f"G8_A9_PRESUBMISSION_{self.study}.md", "INDEPENDENT_PEER_REVIEWER", "GIA-LAP-PB")
        self.cong["G8"] = {"trang_thai": self.cham("G8"),
                           "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G8", self.study, self.out, self.repo))}
        if vs:
            self.du_lieu.setdefault("vong_sua", {})["vong_2"] = dict(self.cong["G8"])
        self.do_truc("sau_G8")

    def g9(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tap_chi = (hs.get("tac_gia_G7") or {}).get("target_journal") or "Tạp chí Y học Việt Nam"
        self.chay("G9 sinh bộ khai báo liêm chính", "run_g9_auto.py", "--study", self.study, "--n-authors", "2",
                  "--target-journal", tap_chi)
        self._khai_g9()
        self._vao_meta("G9", {**(hs.get("tham_so_G9") or {}), "reviewed_by_role": "PI", "reviewed_at": GL._bay_gio()})
        # Quy trình thật: tác giả khai phiếu có cấu trúc rồi sinh lại gói — A10/cover letter lấy CRediT, người truy cập
        # dữ liệu, COI, tài trợ, AI, chia sẻ dữ liệu từ phiếu và từ quyết định đã chốt (run_g9_auto 16/11/2026).
        self.chay("G9 sinh lại gói sau khi tác giả khai phiếu", "run_g9_auto.py", "--study", self.study, "--n-authors",
                  "2", "--target-journal", tap_chi)
        self._dien_cong("G9", f"G9_*{self.study}*.md", list(hs.get("tra_loi_G9", [])) + list(TRA_LOI_G5_G9_CHUNG))
        self._checklist_bao_cao()
        self._quet_a12("G9")  # biên nhận A12 nằm trong manifest G9 ⇒ phủ đủ gói TRƯỚC khi chấm manifest
        # chấm lại SAU khi khai ⇒ manifest SHA-256 của gói ghi vào checkpoint đúng bản đã khai (G9-AUTO-07)
        self.chay("G9 chấm lại sau khai báo (manifest gói)", "g9_quality_gate.py", "--study", self.study)
        self.cong["G9_truoc_ky"] = {"trang_thai": self.cham("G9"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G9", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G9", "G9_checkpoint.json", "PI", "GIA-LAP-PI")
        self.cong["G9"] = {"trang_thai": self.cham("G9"),
                           "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G9", self.study, self.out, self.repo))}
        self.do_truc("sau_G9")

    def _checklist_bao_cao(self) -> Optional[str]:
        """Tác giả tách bảng checklist chuẩn báo cáo của bản thảo G7 thành tệp nộp kèm (tạp chí đòi checklist riêng)."""
        a8 = self.out / f"G7_A8_MANUSCRIPT_{self.study}.md"
        if not a8.is_file():
            return None
        hang = [d for d in a8.read_text(encoding="utf-8").splitlines() if re.match(r"\s*\|\s*\d+[a-z]?\s*\|", d)]
        if not hang:
            return None
        ten = f"G9_REPORTING_CHECKLIST_{self.study}.md"
        (self.out / ten).write_text(f"# Checklist chuẩn báo cáo — {self.study}\n\n"
                                    "| Mục | Nội dung | Trạng thái | Ghi chú |\n|---|---|---|---|\n"
                                    + "\n".join(hang) + "\n",
                                    encoding="utf-8", newline="\n")
        return ten

    def _khai_g9(self) -> None:
        """PI và từng tác giả (mã vai, không tên thật) khai `G9_PUBLICATION_READINESS.json` — bằng chứng chữ ký giữ
        ngoài repo nên chỉ ghi mã tham chiếu GIA-LAP-…; đề tài tổng hợp, không tài trợ, không phải thử nghiệm lâm
        sàng."""
        p = self.out / "G9_PUBLICATION_READINESS.json"
        d = _doc_json(p)
        if not d:
            return
        tg = (self.kb.get("ho_so_tron_vong") or {}).get("tac_gia_G7") or {}
        nay, luc = self.hom_nay.isoformat(), GL._bay_gio()
        vai = {"AUTHOR-01": ["Conceptualization", "Investigation", "Writing - original draft"],
               "AUTHOR-02": ["Formal analysis", "Methodology", "Writing - review & editing"]}
        for i, a in enumerate(d.get("authors") or [], 1):
            a.update({"icmje_criteria": {k: True for k in ("substantial_contribution", "drafting_or_critical_revision",
                                                            "final_approval", "accountability")},
                      "credit_roles": vai.get(a.get("author_ref"), ["Writing - review & editing"]),
                      "coi_form_completed": True, "coi_evidence_ref": f"GIA-LAP-COI-{i:02d}",
                      "data_access_confirmed": True, "attested_at": nay,
                      "attestation_evidence_ref": f"GIA-LAP-ICMJE-{i:02d}"})
        d["authorship"] = {"order_confirmed": True, "credit_mapping_confirmed": True,
                           "acknowledgements_permission_confirmed": True, "guarantor_author_ref": "AUTHOR-01",
                           "dispute_absent_or_resolved": True}
        d["coi_funding"] = {"all_author_forms_complete": True,
                            "collective_coi_statement": tg.get("coi_declared") or "Không có xung đột lợi ích",
                            "funding_statement": tg.get("funding_declared") or "Không có tài trợ bên ngoài",
                            "sponsor_role_statement": ("Không có nhà tài trợ; không bên nào tác động thiết kế, "
                                                       "phân tích hay quyết định công bố"),
                            "sponsor_no_publication_restriction_confirmed": True}
        d["ai_disclosure"] = {"ai_used": True, "tools": ["Bộ giả lập trọn vòng của hệ EBM"],
                              "purposes": ["soạn nháp và kiểm dây chuyền; tác giả đọc lại, đối chiếu số liệu"],
                              "human_verification_confirmed": True, "sensitive_or_confidential_data_uploaded": False,
                              "ai_not_author_confirmed": True, "manuscript_statement_final": True,
                              "cover_letter_statement_final": True, "confirmed_at": nay}
        thu_nghiem = self.kb.get("design_code") == "rct" or "rct" in str(self.ma)
        d["data_availability"] = {**(d.get("data_availability") or {}), "decision": "NOT_SHARED_WITH_JUSTIFICATION",
                                  "statement_final": True, "clinical_trial": thu_nghiem,
                                  "registry_statement_consistent": True if thu_nghiem else None,
                                  "access_criteria": "Dữ liệu cá thể không chia sẻ công khai theo cam kết bảo mật "
                                                     "với người tham gia; kịch bản phân tích kèm gói phát hành"}
        d["data_access_governance"] = {**(d.get("data_access_governance") or {}),
                                       "all_authors_can_review_supporting_data": True,
                                       "primary_data_access_author_ref": "AUTHOR-01",
                                       "primary_data_access_confirmed": True, "analysis_participation_confirmed": True,
                                       "academic_nonacademic_collaboration": False, "sponsored_research": False,
                                       "confirmed_at": nay}
        d["publication_integrity"] = {"original_work_confirmed": True, "duplicate_submission_absent": True,
                                      "overlap_disclosed": True, "preprint_status_declared": True,
                                      "plagiarism_review_completed": True, "plagiarism_report_ref": "GIA-LAP-SIM-01",
                                      "journal_or_institution_criterion": "trùng lặp < 15% (tiêu chí đơn vị)",
                                      "human_similarity_review_confirmed": True, "image_integrity_reviewed": True,
                                      "results_match_locked_analysis": True, "analysis_deviations_disclosed": True}
        d["venue_due_diligence"] = {**(d.get("venue_due_diligence") or {}),
                                    "official_journal_url": "https://tapchiyhocvietnam.vn",
                                    **{k: True for k in ("scope_fit_confirmed", "peer_review_process_checked",
                                                         "fees_checked", "archiving_checked",
                                                         "correction_retraction_policy_checked",
                                                         "indexing_verified_from_primary_source")},
                                    "checked_at": nay}
        d["ethics_and_privacy"] = {k: True for k in ("ethics_statement_final", "consent_or_waiver_statement_final",
                                                     "registration_statement_final",
                                                     "no_identifiable_participant_content_confirmed")}
        d["institutional_confirmation"] = {**(d.get("institutional_confirmation") or {}),
                                           "department_head_required": False, "internal_review_required": False,
                                           "sponsor_review_required": False}
        d["final_package"] = {**(d.get("final_package") or {}), "reporting_checklist_path": self._checklist_bao_cao(),
                              "manuscript_version": "1.0", "package_version": "1.0", "finalized_at": luc,
                              "prepared_for_pi_review": True}
        _ghi_json(p, d)

    def _khai_dac_ta_g10(self) -> None:
        """PI khai các thành phần đề cương MỚI (sai lệch, tiến độ–nhân lực–kinh phí, tổng quan, pilot…). Điều ĐÃ CHỐT ở
        SAP/G2/G5/G7/ma trận nay HỆ tự lấp (`quyet_dinh_da_chot`, 16/11/2026) — bộ giả lập ghi khoá hệ đã lấp vào
        `du_lieu.g10_he_tu_lap` để đo, không khai lại thay hệ."""
        import quyet_dinh_da_chot as QD  # noqa: PLC0415

        meta = self._meta()
        hs = (self.kb.get("ho_so_tron_vong") or {}).get("dac_ta_G10") or {}
        _moi, he_lap = QD.lop_phu(meta, self.out, self.study)
        self.du_lieu["g10_he_tu_lap"] = he_lap
        ghi: Dict[str, str] = {}
        for k, v in hs.items():
            if v and not meta.get(k):
                meta[k] = v
                ghi[k] = "mới đúng vai (hồ sơ đề tài)"
        self._ghi_meta(meta)
        self.du_lieu["g10_khai_lai"] = ghi

    def _khai_g10(self) -> None:
        """PI khai `G10_RELEASE_READINESS.json` cho gói NỘP TẠP CHÍ (mã tham chiếu, không tên/liên hệ thật)."""
        p = self.out / "G10_RELEASE_READINESS.json"
        d = _doc_json(p)
        if not d:
            return
        nay = GL._bay_gio()
        d["release"] = {**(d.get("release") or {}), "purpose": "JOURNAL_SUBMISSION", "package_version": "1.0",
                        "target_system_or_recipient_ref": "GIA-LAP-TAP-CHI-01", "target_requirements_checked": True,
                        "prepared_at": nay, "owner_ref": "GIA-LAP-PI", "change_log_reviewed": True,
                        "final_files_confirmed": True, "no_unresolved_critical_issues": True,
                        "prepared_for_pi_review": True}
        d["cross_document_consistency"] = {k: True for k in (d.get("cross_document_consistency") or {})}
        d["privacy_and_permissions"] = {k: True for k in (d.get("privacy_and_permissions") or {})}
        d["archive_and_reproducibility"] = {
            "archive_location_ref": "GIA-LAP-LUU-TRU-01", "retention_policy_ref": "GIA-LAP-CHINH-SACH-LUU-02",
            "software_environment_captured": True, "data_dictionary_included_or_not_applicable": True,
            "audit_trail_preserved": True, "responsible_owner_ref": "GIA-LAP-PI"}
        _ghi_json(p, d)

    def _de_cuong_nop(self) -> None:
        """PI dùng công cụ soạn ĐỀ CƯƠNG NỘP HỘI ĐỒNG (bản đọc được, không ký hiệu nội bộ) từ quyết định đã chốt rồi
        để G10 ràng buộc vào gói (16/11/2026 — bác sĩ chê bản lắp DE_CUONG_THONG_NHAT có câu chữ không phù hợp với
        một đề cương hoàn chỉnh). Kết quả K1–K7 ghi vào du_lieu để phép thử trọn vòng đòi sạch."""
        kq = self.chay("PI soạn đề cương nộp Hội đồng", "sinh_de_cuong_nop_hoi_dong.py", "--study", self.study,
                       "--ghi", "--json")
        dong = kq.get("dong") or []
        dau = next((i for i, d in enumerate(dong) if d.strip() == "{"), None)  # bỏ dòng cảnh báo font của md2docx
        try:
            ra = json.loads("\n".join(dong[dau:])) if dau is not None else {}
        except ValueError:
            ra = {"ma": kq.get("ma"), "loi": ["không đọc được kết quả JSON của bộ sinh"]}
        self.du_lieu["de_cuong_nop"] = {"ma": ra.get("ma"), "loi": ra.get("loi") or [],
                                        "trich_dan": ra.get("trich_dan"), "so_dong": ra.get("so_dong")}

    def g10(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        self._khai_dac_ta_g10()
        self.chay("G10 lắp gói phát hành (lượt dựng)", "run_g10_assemble.py", "--study", self.study)
        self._dien_cong("G10", f"*G10*{self.study}*.md", hs.get("tra_loi_G10", []))
        self._dien_cong("G10", f"DE_CUONG_THONG_NHAT_{self.study}.md", hs.get("tra_loi_G10", []))
        # A12 phủ HỢP mọi PMID của gói — gồm đề cương thống nhất G10 (kiem_ban_g10). Ghi lại biên nhận ở đây làm vỡ
        # manifest G9 đã khoá ⇒ chỉ chạy khi còn PMID CHƯA kiểm (G8/G9 đã quét — lượt này thường không có gì mới)
        self._quet_a12("G10")
        self._khai_g10()
        self._de_cuong_nop()
        self.chay("G10 lắp lại gói sau khi PI khai", "run_g10_assemble.py", "--study", self.study)
        self.cong["G10_truoc_ky"] = {"trang_thai": self.cham("G10"),
                                     "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G10", self.study, self.out,
                                                                                  self.repo))}
        self._ky("G10", "G10_checkpoint.json", "PI", "GIA-LAP-PI")
        self.cong["G10"] = {"trang_thai": self.cham("G10"),
                            "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G10", self.study, self.out, self.repo))}
        self.do_truc("sau_G10")

    # ── báo cáo
    def kiem_chinh_xac(self) -> Dict[str, Any]:
        """Kịch bản chân thực (17/11/2026): ước lượng chính G6 phải TÌM LẠI tham số đã dùng sinh dữ liệu
        (`gia_lap_chan_thuc.KIEM_CHINH_XAC`). Kịch bản khác / chưa có kết quả G6 ⇒ «không áp dụng»/«chưa đo»."""
        import gia_lap_chan_thuc as GCT  # noqa: PLC0415

        if self.ma not in GCT.KIEM_CHINH_XAC:
            return {"ket": "KHONG_AP_DUNG"}
        lay, _dich, thang_log = GCT.KIEM_CHINH_XAC[self.ma]
        u = self._uoc_luong(lay, "G6")
        if not u:
            return {"ket": "CHUA_DO", "lay": lay}
        he = 100.0 if lay == "ty_le" else 1.0  # tỷ lệ báo theo %
        try:
            that = GCT.tham_so_that(self.ma) * he
        except Exception as exc:  # noqa: BLE001 — không tính được đích thì nói rõ, không coi là đạt
            return {"ket": "CHUA_DO", "lay": lay, "loi": f"{type(exc).__name__}: {exc}"[:200]}
        return {"lay": lay, **GCT.phan_xet_chinh_xac(that, u["uoc"], tuple(u["ci"]), thang_log)}

    def bao_cao(self) -> Dict[str, Any]:
        theo_cong: Dict[str, Any] = {}
        for g in sorted({o["cong"] for o in self.o}):
            theo_cong[g] = tom_tat_o([o for o in self.o if o["cong"] == g])
        loi_may = [f"{self.ma}:{o['cong']}:{o['loai']}:{o['tep']}:«{o['nhan']}»" for o in self.o
                   if o["loai"] in LOAI_O_LOI_MAY]
        return {"ma": self.ma, "study": self.study, "thiet_ke": self.thiet_ke, "phan_a": self.phan_a,
                "cong": self.cong, "o_theo_cong": theo_cong, "du_lieu": self.du_lieu, "truc": self.truc,
                "dung": self.dung,
                "so_o_loi_may": len(loi_may), "o_loi_may": sorted(set(loi_may))[:200],
                "crash": [b["buoc"] for b in self.buoc if b.get("crash")], "buoc": self.buoc,
                "chinh_xac": self._chinh_xac_an_toan()}

    def _chinh_xac_an_toan(self) -> Dict[str, Any]:
        try:
            return self.kiem_chinh_xac()
        except Exception as exc:  # noqa: BLE001 — báo cáo không được sập vì phép kiểm phụ
            return {"ket": "CHUA_DO", "loi": f"{type(exc).__name__}: {exc}"[:200]}

    def chay_tron_vong(self, tu_cong: Optional[str] = None, den_cong: Optional[str] = None) -> Dict[str, Any]:
        """`tu_cong` (vd «G6») = chạy TIẾP trên bản sao đã đi qua các cổng trước (cùng khoá giả); `den_cong` = dừng SAU
        cổng đó (vd «G6» khi chỉ cần dữ liệu khoá + phân tích SPSS/R)."""
        self._khoa_vai()
        thu_tu = [("G2", self.g2), ("G4", self.g4), ("G5", self.g5), ("G6", self.g6), ("G6_5", self.g6_5),
                  ("G7", self.g7), ("G8", self.g8), ("G9", self.g9), ("G10", self.g10)]
        if tu_cong:
            ten = [g for g, _ in thu_tu]
            if tu_cong not in ten:
                raise ValueError(f"tu_cong phải thuộc {ten}")
            thu_tu = thu_tu[ten.index(tu_cong):]
            self.phan_a = {"bo_qua": f"chạy tiếp từ {tu_cong}"}
        else:
            if not self.phan_a_chay():
                return self.bao_cao()
            if duoi_pytest_khoa_gia():
                self.chay("Đánh dấu đề tài tổng hợp (bản sao tạm)", "mark_study_synthetic.py", "--study", self.study,
                          "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        if den_cong:
            ten = [g for g, _ in thu_tu]
            thu_tu = thu_tu[:ten.index(den_cong) + 1] if den_cong in ten else thu_tu
        for _g, buoc in thu_tu:
            try:
                buoc()
            except Exception as exc:  # noqa: BLE001 — giả lập ghi mọi lỗi, không dừng im lặng
                self.buoc.append({"buoc": buoc.__name__, "loi": f"{type(exc).__name__}: {exc}"[:300], "crash": True})
                self.dung = self.dung or f"{buoc.__name__}:loi_noi_bo"
                break
            if self.dung:
                break
        return self.bao_cao()


# Tên VÍ DỤ theo lệ văn bản mẫu tiếng Việt («Nguyễn Văn A») — không phải người thật; trước 16/11/2026 dùng mã vai trò
# «PI-REF-01 (chủ nhiệm — mã vai trò, giả lập)» chèn giữa câu, làm phiếu đồng ý/đề cương đọc như văn bản lỗi.
TEN_CHU_NHIEM = "BS. Nguyễn Văn A"
TEN_HOI_DONG = "Hội đồng Đạo đức trong nghiên cứu y sinh học của bệnh viện chủ trì"
# Hành chính đã chốt của chủ nhiệm (study_meta.administrative) — run_g2_auto điền thẳng vào hồ sơ thay vì để ô.
HANH_CHINH = {"principal_investigator": TEN_CHU_NHIEM, "pi_title": "Bác sĩ chuyên khoa II",
              "pi_unit": "Khoa Khám bệnh", "irb_name": TEN_HOI_DONG, "sponsor": "Không có tài trợ bên ngoài"}

# Bản tiếng Anh của phiếu đồng ý do chủ nhiệm song ngữ soạn (gate_params.G2.icf_en) — phần chữ tự do máy không dịch
# (17/11/2026). Phần chung của đơn vị + phần riêng theo CHỦ ĐỀ (biến thể dùng chủ đề của kịch bản gốc).
ICF_EN_CHUNG = {
    "institution": "Outpatient Department, the sponsoring hospital",
    "pi_qualifications": "MD, Specialist Level II",
    "irb": "Biomedical Research Ethics Committee of the sponsoring hospital",
    "benefits": "No treatment benefit is guaranteed. You will be monitored and advised during the study and told "
                "promptly if any measurement is abnormal. The results may help improve care for other patients.",
    "coi": "no",
    "reimbursement": "Travel costs for each study visit are reimbursed according to the institution's rate.",
    "injury_compensation": "The sponsoring institution covers the full cost of examination and treatment of any "
                           "study-related injury, in line with current regulations",
    "source_access_scope": "Access is limited to records relevant to the study.",
    "post_trial_care": "If the intervention proves beneficial, you will be able to continue receiving it; health "
                       "problems outside the scope of the study will be referred for standard care.",
    "new_info_how": "by telephone and at your next follow-up visit",
    "follow_up_after_withdrawal": "We will contact you for safety follow-up; data collected before withdrawal are kept "
                                  "in de-identified form and analysed according to the intention-to-treat principle",
    "termination": "for your safety, if you no longer meet the eligibility criteria, or if the study is stopped by "
                   "the Ethics Committee or a regulatory authority",
    "samples": "Not applicable — no biological samples are collected in this study.",
    "extra_step": "No blood samples or extra examinations are taken beyond routine care.",
    "location": "Outpatient clinic of the sponsoring hospital",
}
_SMS = {"title": "Effect of text-message reminders versus usual care on blood pressure control at 6 months in "
                 "outpatients with hypertension: a randomised controlled trial",
        "purpose": "find out whether daily text-message reminders to take blood-pressure medicines, added to usual "
                   "care, improve blood pressure control compared with usual care alone.",
        "intervention": "daily automated text-message reminders for 6 months, plus usual care",
        "comparator": "usual care without reminder messages", "alternative": "usual care without reminder messages"}
ICF_EN_CHU_DE = {
    "rct_nhi_phan": _SMS, "rct_cum": _SMS, "rct_rut_bai": _SMS, "rct_kinh_te": _SMS,
    "rct_khong_kem": {"title": "Telephone versus in-person monthly follow-up for blood pressure control: a "
                               "non-inferiority randomised controlled trial",
                      "purpose": "find out whether monthly follow-up by telephone keeps blood pressure control at "
                                 "least as good as monthly visits in person.",
                      "intervention": "monthly telephone follow-up for 6 months",
                      "comparator": "monthly in-person follow-up at the clinic",
                      "alternative": "monthly in-person follow-up at the clinic"},
    "cat_ngang_mo_ta": {"title": "Blood pressure control among outpatients treated for hypertension: a "
                                 "cross-sectional study",
                        "purpose": "estimate how many people treated for high blood pressure at the clinic have their "
                                   "blood pressure under control."},
    "thuan_tap_phoi_nhiem": {"title": "Long-term proton pump inhibitor use and fracture risk in people aged 60 and "
                                      "over: a cohort study",
                             "purpose": "compare the risk of fractures over 3 years between people aged 60 and over "
                                        "who use stomach-acid-reducing medicines (proton pump inhibitors) long term "
                                        "and those who do not."},
    "benh_chung": {"title": "NSAID use and upper gastrointestinal bleeding in people aged 60 and over: a case-control "
                            "study",
                   "purpose": "find out whether recent use of anti-inflammatory pain medicines (NSAIDs) is linked to "
                              "bleeding in the upper digestive tract in people aged 60 and over."},
    "chan_doan": {"title": "Diagnostic accuracy of the FIB-4 score for advanced liver fibrosis",
                  "purpose": "find out how accurately the FIB-4 score, calculated from routine blood tests, detects "
                             "advanced liver scarring compared with liver stiffness measurement.",
                  "index_test": "The FIB-4 score is calculated from your routine blood test results (no extra blood "
                                "is taken).",
                  "reference_standard": "Liver stiffness is measured with a painless ultrasound-based scan (about 10 "
                                        "minutes)."},
    "mo_hinh_du_bao": {"title": "A model to predict 12-month hospital admission in outpatients with heart failure: "
                                "development and validation",
                       "purpose": "build and test a tool that estimates the risk of hospital admission within 12 "
                                  "months for people with heart failure treated as outpatients."},
    "dinh_tinh": {"title": "Experiences and barriers when starting insulin among people with type 2 diabetes: a "
                           "qualitative study",
                  "purpose": "understand the experiences and difficulties of people with type 2 diabetes when "
                             "starting insulin injections."},
}
for _ma_cd in ("thuan_tap_song_con", "thuan_tap_mi", "thuan_tap_vong_sua"):
    ICF_EN_CHU_DE[_ma_cd] = ICF_EN_CHU_DE["thuan_tap_phoi_nhiem"]

# Câu trả lời của CHỦ NHIỆM cho các ô phiếu đồng ý/hồ sơ đạo đức mà G1 không chốt (chính sách của đơn vị, cam kết với
# người tham gia). Đặt TRƯỚC TRA_LOI_CHUNG: mẫu cụ thể phải thắng mẫu chung «chu nhiem»/«don vi» (16/11/2026 — trước
# đó «[CẦN CHỦ NHIỆM XÁC NHẬN phạm vi truy cập]» bị điền tên chủ nhiệm, «… sẽ [CẦN — sẽ/sẽ không]» thành tên người).
TRA_LOI_G2_CHUNG: Tuple[Tuple[str, str], ...] = (
    (r"chi phi dieu tri bien co", "đơn vị chủ trì chi trả toàn bộ chi phí khám và điều trị biến cố liên quan đến "
                                  "nghiên cứu"),
    (r"loi ich truc tiep|truc tiep voi ntg|xac dinh xem co loi ich truc tiep",
     "Không có lợi ích điều trị nào được bảo đảm; người tham gia được theo dõi, tư vấn và được báo ngay khi kết quả "
     "đo có bất thường"),
    (r"^nhom nghien cuu$", "không"),
    (r"^co ho tro", "hỗ trợ chi phí đi lại cho mỗi lần tái khám theo định mức của đơn vị chủ trì"),
    (r"ghi ro chinh sach", "Dữ liệu đã thu thập trước khi rút lui được giữ ở dạng đã khử định danh và vẫn được phân "
                           "tích, trừ khi anh/chị yêu cầu xoá."),
    (r"xac nhan pham vi truy cap", "Phạm vi truy cập chỉ gồm hồ sơ liên quan đến nghiên cứu."),
    (r"nha tai tro/don vi", "đơn vị chủ trì"),
    (r"^co/khong$", "không"),
    (r"^don vi/chu nhiem", "Đơn vị chủ trì"),
    (r"mo ta chinh sach chi tra|cach chi tra", "chi trả toàn bộ chi phí khám và điều trị tổn hại đó theo quy định "
                                               "hiện hành"),
    (r"chu nhiem chon.*se.*se khong|^se\s*/\s*se khong", "sẽ"),
    (r"vd chuyen tuyen dieu tri", "chuyển tuyến điều trị theo phác đồ chuẩn"),
    (r"cach thong bao", "qua điện thoại và tại lần tái khám kế tiếp"),
    (r"xu ly the nao", "giữ lại ở dạng đã khử định danh để phân tích theo nguyên tắc ý định điều trị"),
    (r"vi ly do an toan, khong con du tieu chuan", "vì lý do an toàn của anh/chị, khi anh/chị không còn đủ tiêu "
                                                   "chuẩn tham gia, hoặc khi nghiên cứu bị dừng theo quyết định của "
                                                   "Hội đồng Đạo đức hay cơ quan quản lý"),
    (r"bang rui ro phu hop voi de tai", "Chủ nhiệm đã rà và xác nhận bảng rủi ro phù hợp với đề tài."),
    (r"se co so irb", "Số phê duyệt của Hội đồng: HĐĐĐ-GL-2026/01"),
    (r"dang ky nghien cuu", "theo kế hoạch ở mục Đăng ký nghiên cứu; số đăng ký bổ sung khi được cấp"),
    (r"quy trinh cu the cua don vi", "Theo quy trình ứng phó sự cố an toàn thông tin của bệnh viện chủ trì"),
    (r"so hop dong", "Không có hợp đồng tài trợ"),
    (r"bo sung them neu co", "không dùng công cụ nào khác"),
)


# Thống kê viên trả lời §13–§15 của SAP thử nghiệm (giữa kỳ, hội đồng theo dõi dữ liệu, tổn hại/tuân thủ) — chung cho
# các thử nghiệm can thiệp hành vi nguy cơ tối thiểu của bộ giả lập (16/11/2026: trước đó ba mục này còn nguyên
# «(GIẢ LẬP — hồ sơ chưa có)» trong SAP đã khoá của mọi kịch bản RCT).
TRA_LOI_G4_RCT: Tuple[Tuple[str, str], ...] = (
    (r"^co phan tich giua ky", "Không"),
    (r"quy tac dung", "Không dừng sớm vì hiệu quả; chỉ dừng khi Hội đồng Đạo đức yêu cầu vì lý do an toàn"),
    (r"ai xem ket qua giua ky", "Không áp dụng — không có phân tích giữa kỳ"),
    (r"neu khong co phan tich giua ky", "Can thiệp hành vi nguy cơ tối thiểu, theo dõi ngắn; phân tích giữa kỳ không "
                                        "đem lại lợi ích cho người tham gia"),
    (r"neu khong can dmc", "Can thiệp nguy cơ tối thiểu; chủ nhiệm theo dõi an toàn qua báo cáo biến cố hằng tháng "
                           "và báo Hội đồng Đạo đức theo quy định"),
    (r"^co dmc|^co dsmb", "Không"),
    (r"thanh phan va vai tro", "Không áp dụng — không lập hội đồng theo dõi dữ liệu"),
    (r"dieu le|charter", "Không áp dụng"),
    (r"dinh nghia ton hai|harms", "Biến cố bất lợi liên quan can thiệp: phàn nàn, lo âu, cơn tăng huyết áp từ "
                                  "180/110 mmHg trở lên"),
    (r"^cach danh gia", "Hỏi chủ động tại mỗi lần tái khám và ghi phiếu biến cố"),
    (r"cai thien va theo doi tuan thu", "Theo dõi tỷ lệ can thiệp được thực hiện đúng kế hoạch và tự báo cáo dùng "
                                        "thuốc tại tháng 3 và tháng 6"),
)


# Tác giả/quản lý dữ liệu trả lời các ô hồ sơ công bố và quản lý dữ liệu (17/11/2026): ghi THỦ TỤC/KẾ HOẠCH đã định,
# không bịa kết quả đo chưa làm (tỷ lệ trùng lặp, số phê duyệt của tạp chí…).
TRA_LOI_G5_G9_CHUNG: Tuple[Tuple[str, str], ...] = (
    (r"du lieu se chia se", "Bộ dữ liệu đã khử định danh dùng cho phân tích chính và từ điển dữ liệu"),
    (r"tai lieu lien quan", "Đề cương, kế hoạch phân tích thống kê và kịch bản phân tích R/SPSS"),
    (r"bat dau/thoi han", "Từ khi bài báo được công bố, trong 5 năm"),
    (r"tieu chi truy cap|co che xet duyet|repository", "Theo đề nghị có đề cương phân tích hợp lý gửi chủ nhiệm đề "
                                                       "tài; ký thoả thuận sử dụng dữ liệu trước khi chia sẻ"),
    (r"cong cu kiem tra", "iThenticate (kiểm tra ngay trước khi nộp tạp chí)"),
    (r"ty le similarity|ty le thuc te", "chưa kiểm tra — thực hiện ngay trước khi nộp; ngưỡng chấp nhận dưới 15%"),
    (r"ngay kiem tra", "ngay trước ngày nộp bài"),
    (r"neu co an pham lien quan", "Không có ấn phẩm liên quan"),
    (r"preprint", "Không đăng bản thảo trước (preprint)"),
    (r"^co ->", "không áp dụng"),
    (r"da ky day du", "đủ chữ ký của các tác giả"),
    (r"ngay khai bao cuoi|ngay g9 passed du kien", date.today().strftime("%d/%m/%Y")),
    (r"db lock date|ngay khoa db", date.today().strftime("%d/%m/%Y")),
    (r"nguoi khoa db", "ThS. Lê Văn C (quản lý dữ liệu)"),
    (r"nguoi chung kien", "BS. Nguyễn Văn A (chủ nhiệm đề tài)"),
    (r"nguong canh bao thieu", "☑ Ngưỡng cảnh báo thiếu: > 5% ở biến trọng yếu ⇒ rà soát nguồn và báo chủ nhiệm"),
)


# Câu trả lời CHUNG của các vai (thông tin hành chính, không PII thật): mẫu nhãn đã bỏ dấu → giá trị.
TRA_LOI_CHUNG: Tuple[Tuple[str, str], ...] = (
    (r"^bac si( \+ doi nc)?$", "Bác sĩ/nhóm nghiên cứu"),  # thẻ NGƯỜI PHỤ TRÁCH ở danh sách việc của DMP
    (r"chu nhiem|ho ten chu nhiem|ten chu nhiem|nghien cuu vien chinh|principal investigator",
     TEN_CHU_NHIEM),
    (r"chuc vu|chuc danh|trinh do", "Bác sĩ chuyên khoa II"),
    (r"^don vi|don vi thuc hien|co quan|institution", "Khoa Khám bệnh, bệnh viện chủ trì"),
    (r"dien thoai|phone", "—"), (r"email", "—"),
    (r"tai tro|funding|sponsor", "Không có tài trợ bên ngoài"),
    (r"xung dot loi ich|coi\b|conflict", "Không có xung đột lợi ích"),
    (r"hoi dong dao duc|ethics committee", TEN_HOI_DONG),
    (r"^tinh$|tinh/thanh|tinh thanh|province", "TP. Hồ Chí Minh"),
    (r"noi luu|luu tai|may chu", "Máy chủ nội bộ có mã hoá, phân quyền theo vai trò"),
    (r"sao luu|backup", "Sao lưu hằng ngày, 2 bản độc lập"),
    (r"thoi gian luu|nam\]?$|xoa/an danh", "2"),
    (r"ten tac gia|tac gia", "ThS. Trần Thị B"),
    (r"phan mem", "R 4.6 (phân tích chính); kiểm chéo SPSS 31"),
    (r"packages", "stats, sandwich, lmtest, mice"),
    (r"random seed|seed", "20261115"),
    (r"tap chi|hoi nghi", "Tạp chí Y học Việt Nam"),
    (r"nguoi kiem tra dau ra", TEN_CHU_NHIEM),
    (r"so ban nop", "3"),
    (r"thoi gian luu", "2"),
    (r"xoa/huy|huy vat ly|trong\s*$", "6"),
    (r"ten don vi", "Khoa Khám bệnh, bệnh viện chủ trì"),
)


# Ghi receipt A12 bằng ĐÚNG hàm của check_citations.py từ kết quả tra mạng (JSON) — chạy trong môi trường KHOÁ GIẢ.
MA_KY_RECEIPT_A12 = """import json, sys
sys.path.insert(0, "tools")
import check_citation_metadata as CCM
import check_citation_retraction as CCR
d = json.load(open(sys.argv[2], encoding="utf-8"))
pm = sys.argv[3].split(",")
CCR.write_retraction_receipt(sys.argv[1], pm, d["retraction"])
CCM.write_metadata_receipt(sys.argv[1], pm, d["metadata"])
print("receipt A12 da ghi (khoa gia)")
"""


# Bản sao trọn vòng cần thêm `runtime/` (sổ cái phê duyệt của approve_gate) và `scripts/` so với canary (chỉ G0→G5).
THU_MUC_CHEP_THEM = ("runtime", "scripts")


def dung_ban_sao_tron_vong(goc: Path, dich: Path) -> Path:
    import shutil  # noqa: PLC0415

    repo = GL.dung_ban_sao(goc, dich)
    for ten in THU_MUC_CHEP_THEM:
        nguon = Path(goc) / ten
        if nguon.is_dir() and not (repo / ten).exists():
            shutil.copytree(nguon, repo / ten, ignore=GL.BO_QUA_KHI_CHEP, symlinks=False)
    return repo


def chay_mot(ma: str, repo: Path, tu_cong: Optional[str] = None, den_cong: Optional[str] = None,
             **kw: Any) -> Dict[str, Any]:
    return TronVong(ma, repo, **kw).chay_tron_vong(tu_cong=tu_cong, den_cong=den_cong)
