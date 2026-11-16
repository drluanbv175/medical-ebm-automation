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
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


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
        (r"^muc tieu|^objective|muc tieu 1", g1.get("objectives"), "G1.objectives"),
        (r"doi tuong nghien cuu|quan the nghien cuu|^population", g1.get("population"), "G1.population"),
        (r"dia diem|noi (nghien cuu|thuc hien)|co so nghien cuu|setting", g1.get("setting"), "G1.setting"),
        (r"thoi gian nghien cuu|thoi gian thu thap|study period", g1.get("study_period"), "G1.study_period"),
        (r"(^|\s)co mau|sample size|so nguoi tham gia du kien", n, "G3.n"),
        (r"ten de tai|^title|public title", meta.get("title") or meta.get("topic"), "title"),
        (r"dinh nghia bien co", po.get("measure"), "G1.primary_outcome.measure"),
        (r"gia thuyet|hypothes", " / ".join(_text(g0.get(k)) for k in ("hypothesis_h0", "hypothesis_h1") if g0.get(k)),
         "G0.hypothesis"),
        (r"^can thiep|^phoi nhiem|intervention|exposure", g1.get("intervention_or_exposure"), "G1.intervention"),
        (r"so sanh|doi chung|comparator", g1.get("comparator"), "G1.comparator"),
        (r"chien luoc tuyen|tuyen chon|recruitment", g1.get("recruitment_strategy"), "G1.recruitment_strategy"),
        (r"lich theo doi|follow.?up", g1.get("follow_up_schedule"), "G1.follow_up_schedule"),
        (r"quy trinh.*pico|so do nghien cuu|tien trinh nghien cuu|schema", g1.get("study_schema_timeline"),
         "G1.study_schema_timeline"),
        (r"ngau nhien hoa|randomi", g1.get("randomisation"), "G1.randomisation"),
        (r"che giau|concealment", g1.get("allocation_concealment"), "G1.allocation_concealment"),
        (r"lam mu|blinding", g1.get("blinding"), "G1.blinding"),
        (r"quan the phan tich", est.get("population_summary_measure") and
         f"{_text(est.get('population'))}; {_text(est.get('intercurrent_events_strategy'))}", "G1.estimand"),
        (r"(^|\s)alpha|muc y nghia", g3.get("alpha"), "G3.alpha"),
        (r"(^|\s)luc thong ke|(^|\s)power", g3.get("power"), "G3.power"),
        (r"quy tac dung|stopping", g1.get("stopping_rescue_rules"), "G1.stopping_rescue_rules"),
        (r"ke hoach giam sat|monitoring", g1.get("monitoring_plan"), "G1.monitoring_plan"),
        (r"phien ban de cuong|protocol version", g1.get("protocol_version"), "G1.protocol_version"),
        (r"loi ich.*nguy co|benefit", g1.get("benefit_risk_rationale"), "G1.benefit_risk_rationale"),
        (r"khoang trong|ly do can nghien cuu", g1.get("knowledge_gap"), "G1.knowledge_gap"),
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


DIEN_CHUA_CO_HO_SO = "(GIẢ LẬP — hồ sơ chưa có)"


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
        if not nhan or "]" in nhan or "[" in nhan:
            nhan = trong_o[:80] or nhan  # nhãn trước ô lẫn đuôi ô khác ⇒ dùng nội dung trong ô
        k = bo_dau(nhan)
        o = {"cong": cong, "tep": tep, "dong": so, "nhan": nhan, "o": o_txt, "vi_tri": m.start()}
        giu = ly_do_giu_nguyen(o_txt, dong, cong, tep)
        if giu:  # không phải ô của vai này: lời hướng dẫn khuôn, ô kết quả của bảng khung — để nguyên
            ra.append({**o, "loai": "khong_ap_dung", "dien": o_txt, "ly_do": giu})
            continue
        o_tich = tep_text.rfind("☐", dau_dong, m.start())
        if (dong.lstrip().startswith("|") and o_tich >= 0 and not tep_text[o_tich + 1:m.start()].strip()
                and re.match(r"\s*\|\s*\d+[a-z]?\s*\|", dong)):
            ra.append({**o, "vi_tri": o_tich, "o": tep_text[o_tich:m.end()], "loai": "moi_dung_vai",
                       "dien": "☑ đã báo cáo trong bản thảo (tác giả đối chiếu)"})
            continue
        if "doi chieu g6" in trong_o and re.search(r"\d", dong[:m.start() - dau_dong]):
            # bản thảo chép NGUYÊN VĂN số từ G6 rồi gắn nhãn đối chiếu — tác giả đối chiếu xong thì gỡ nhãn
            ra.append({**o, "loai": "moi_dung_vai", "dien": ""})
            continue
        ly_do = khong_ap_dung(nhan, dong + " " + o_txt, thiet_ke, meta)
        # ô KẾT QUẢ không hỏi điều đã chốt (tên kết cục ≠ kết quả của kết cục) ⇒ không lấy bảng đã chốt
        # (16/11/2026) cùng lẽ: ô đòi nhận định «sau khi có dữ liệu thật» (vd tính đại diện quần thể) là nội dung
        # MỚI của tác giả — dòng có chữ «cỡ mẫu» không biến nó thành câu hỏi lại G3.n
        chot = None if re.search(r"ket qua that|sau khi co du lieu", trong_o) else next(
            ((v, ten) for mau, v, ten in bang if mau.search(k)), None)
        tl = next((v for mau, v in tra_loi if k and re.search(mau, k)), None)
        if tl is None:  # nhãn không khớp mẫu nào ⇒ mới so nội dung trong ô
            tl = next((v for mau, v in tra_loi if re.search(mau, trong_o)), None)
        if ly_do:
            o.update(loai="khong_ap_dung", dien=f"Không áp dụng — {ly_do}")
        elif chot:
            o.update(loai="hoi_lai_da_chot", dien=chot[0], nguon=chot[1])
        elif k and k in da_hoi:
            o.update(loai="hoi_lap", dien=da_hoi[k])
        elif tl is not None:
            o.update(loai="moi_dung_vai", dien=tl)
        elif re.fullmatch(r"_{3,}(?:\s*/\s*_{2,}\s*/\s*_{2,})?", o_txt.strip()) and "/" in o_txt:
            o.update(loai="moi_dung_vai", dien=date.today().strftime("%d/%m/%Y"))
        else:
            o.update(loai="chua_co_ho_so", dien=DIEN_CHUA_CO_HO_SO)
        if k and o["loai"] in ("moi_dung_vai", "chua_co_ho_so"):
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


def sinh_du_lieu(thiet_ke: str, bien_so: Mapping[str, Any], g3: Mapping[str, Any], n: int,
                 seed: int = 20261115) -> List[Dict[str, Any]]:
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
        for ten, kieu, nhan, lua, val, _lo, _hi in bien_so["bo_bien"]:
            if ten in ("record_id", "ma_nguoi_tham_gia", "study_id"):
                r[ten] = f"R{i + 1:04d}"
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
                          "ha_tt_t6": (110, 170)}.get(ten, (0, 100))
                x = rng.uniform(lo, hi)
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
            r["ha_tt_t6"] = int(round(r.get("ha_tt_nen", 150) - (12 if r[pn] else 6) + rng.gauss(0, 10)))
        _ = vai
        rows.append(r)
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
        self.ma, self.kb = ma, GL.KICH_BAN[ma]
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
        cac_o = phan_loai_o(s, g, tep.name, self._meta(), cps, self.thiet_ke, tra_loi, da_hoi)
        self.o.extend(cac_o)
        tep.write_text(dien_o(s, cac_o), encoding="utf-8", newline="\n")

    # ── Phần A
    def phan_a_chay(self) -> bool:
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
    def g2(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault("G2", {}).update(hs.get("G2", {}))
        self._ghi_meta(meta)
        self._soan_phieu_thu_thap()
        self.chay("G2 sinh hồ sơ đạo đức", "run_g2_auto.py", "--study", self.study)
        da_hoi: Dict[str, str] = {}
        tra = list(hs.get("tra_loi_G2", [])) + list(TRA_LOI_CHUNG)
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
        self.hoan_thien_tep("G4", sap, tl + list(TRA_LOI_CHUNG), da_hoi)
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
        """Người nhập lần 1 gõ phiếu vào mẫu Excel của hệ (trang đầu, tên biến dòng 1, dữ liệu từ dòng 4)."""
        import openpyxl  # noqa: PLC0415

        wb = openpyxl.load_workbook(mau)
        khoa = ten_khoa_ban_ghi(hang)
        # trang PHIẾU là trang có cột mã nghiên cứu ở dòng 1 (mẫu còn HUONG_DAN, _DANH_MUC, TU_DIEN, _META)
        ws = next((w for w in wb.worksheets if khoa in [c.value for c in w[1]]), wb.worksheets[0])
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
            self.hoan_thien_tep("G5", tep, list(hs.get("tra_loi_G5", [])) + list(TRA_LOI_CHUNG), da_hoi)
        # dữ liệu mô phỏng theo bộ biến + giả định G3
        n = self._n_g3()
        hang = sinh_du_lieu(self.thiet_ke, self.kb["bien_so"], _gp(self._meta(), "G3"), n)
        nl = self.repo.parent / "nhap_lieu"
        nl.mkdir(parents=True, exist_ok=True)
        (nl / "PHIEU_GOC_mo_phong.json").write_text(json.dumps(hang, ensure_ascii=False, indent=1), encoding="utf-8",
                                                    newline="\n")
        self.chay("Nhập liệu — mẫu Excel", "nhap_lieu_excel.py", "mau", "--study", self.study, "--ra",
                  str(nl / "MAU.xlsx"), "--so-dong", str(len(hang) + 10))
        self.chay("Nhập liệu — mẫu SPSS (.sav)", "nhap_lieu_excel.py", "mau", "--study", self.study, "--dang", "sav",
                  "--ra", str(nl / "MAU.sav"))
        lan1, lan2 = cai_loi_nhap(hang)
        self.du_lieu = {"n": len(hang), "loi_cai_lan1": len(lan1), "loi_cai_lan2": len(lan2)}
        self._ghi_excel(nl / "MAU.xlsx", nl / "lan1_excel.xlsx", hang, lan1)
        sav = self._ghi_sav(nl / "MAU.sav", nl / "lan2_spss.sav", hang, lan2)
        self.du_lieu["nhap_spss"] = sav
        r = self.chay("Nhập liệu — so nhập kép (Excel ↔ SPSS)", "nhap_lieu_excel.py", "so-sanh", "--study", self.study,
                      "--excel1", str(nl / "lan1_excel.xlsx"), "--excel2", str(nl / "lan2_spss.sav"), "--ra",
                      str(nl / "so_sanh_1"))
        lech = _doc_csv(nl / "so_sanh_1" / "NHAP_KEP_chi_tiet.csv")
        self.du_lieu["o_lech_bat_duoc"] = len(lech)
        # đối chiếu phiếu gốc: sửa CẢ hai bản về đúng phiếu gốc, nhập lại bản sạch qua cổng tiếp nhận
        self._ghi_excel(nl / "MAU.xlsx", nl / "lan1_excel_da_sua.xlsx", hang, {})
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
        self.chay("G5 khoá dữ liệu (quản lý dữ liệu)", "lock_analysis_dataset.py", *tham)
        self.cong["G5_truoc_ky"] = {"trang_thai": self.cham("G5"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G5", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G5", "G5_checkpoint.json", "DATA_GOVERNANCE_QA_REVIEWER", "GIA-LAP-DM")
        self._ky("G5", "G5_checkpoint.json", "PI", "GIA-LAP-PI")
        self.cong["G5"] = {"trang_thai": self.cham("G5")}
        self.do_truc("sau_G5")

    def _soan_phieu_thu_thap(self) -> None:
        """PI soạn PHIẾU THU THẬP SỐ LIỆU nộp Hội đồng (G2) từ bộ biến + mã câu hỏi của ma trận — việc ĐÚNG VAI
        (hệ chưa có lệnh sinh khung phiếu; G5-AUTO-11/13 đối chiếu phiếu này với từ điển nhập liệu)."""
        bs = self.kb.get("bien_so") or {}
        ma_cau = {d[3]: d[5] for d in bs.get("ma_tran", ()) if len(d) > 5 and d[5]}
        dong = [f"# PHIẾU THU THẬP SỐ LIỆU — {self._meta().get('title') or self.kb.get('topic')}", "",
                f"Phiên bản 1.0 · nộp kèm hồ sơ Hội đồng Đạo đức · {GL.NHAN}", ""]
        for i, (ten, kieu, nhan, lua, _v, _lo, _hi) in enumerate(bs.get("bo_bien", ()), 1):
            ma = ma_cau.get(ten) or f"C{i}"
            lc = f" — lựa chọn: {lua}" if lua and kieu in ("radio", "dropdown") else (
                " — Có/Không" if kieu == "yesno" else "")
            dong.append(f"- {ma}. {nhan} (`{ten}`){lc}")
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
                    "retention_plan": {"confirmed": True, "retention_rule": "2 năm sau khi kết thúc (giả lập)"},
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
        if ts_chinh.get("outcome") and "outcome_type" not in ts_chinh:
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
    DONG_MO_HINH_CHINH = re.compile(r"^# ((?:df <- readRDS|stopifnot\(identical\(attr\(df|fit_\w+ <- |"
                                    r"lmtest::coeftest\(fit_)[^\n]*)$", re.M)

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
    def _uoc_luong(self, lay: str, gate: str) -> Optional[Dict[str, Any]]:
        tom = _doc_json(self.out / f"{gate}_analysis_summary.json")
        nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
        if lay == "pr_hieu_chinh":
            r = next((x for x in (tom.get("poisson_pr") or {}).get("results") or [] if x.get("variable") == nhom), None)
            return r and {"uoc": r["PR_adj"], "ci": r["CI_95"], "p": r.get("p"),
                          "nguon": f"{gate}_table4_poisson_pr.txt", "so_le": 2}
        if lay == "hieu_so_nguy_co":
            pc = tom.get("primary_outcome") or {}
            return pc.get("risk_diff") is not None and {
                "uoc": pc["risk_diff"], "ci": pc["risk_diff_ci_95"], "p": pc.get("p_value"),
                "nguon": f"{gate}_table2_main_outcome.txt", "so_le": 3} or None
        return None

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
        for r in dg["bang"]:
            u = self._uoc_luong(r["lay"], r["gate"])
            if not u:
                self.du_lieu.setdefault("g6_5_thieu", []).append(f"{r['gate']}:{r['lay']}")
                continue
            p = u["p"]
            p_txt = "—" if p is None else ("< 0,001" if p < 0.001 else self._so_vn(p, 3))
            hang.append(f"| {r['ket_cuc']} | {r['thuoc_do']} | {self._so_vn(u['uoc'], u['so_le'])} | "
                        f"{self._so_vn(u['ci'][0], u['so_le'])}–{self._so_vn(u['ci'][1], u['so_le'])} | {p_txt} | "
                        f"{r['y_nghia']} | `{u['nguon']}` |")
        gt = self._gia_tri_ket_qua()
        bang = ("| " + " | ".join(DG.COT_BANG_CHINH) + " |\n|" + "---|" * len(DG.COT_BANG_CHINH) + "\n"
                + "\n".join(hang) + "\n")
        van = (f"# Diễn giải kết quả — {self.study}\n\n> {NHAN_MO_PHONG}\n\n"
               f"{DG.MUC[0]}\n\n**Bảng 1.** Kết quả kết cục chính, nhóm nhỏ và độ nhạy (ước lượng, KTC 95%, p — "
               f"đúng như tệp kết quả)\n\n{bang}\n"
               + "".join(f"{DG.MUC[i]}\n\n{dg[f'muc_{i + 1}'].format(**gt)}\n\n" for i in range(1, 5))
               + "> Cần bác sĩ kiểm chứng.\n")
        DG.duong_dan(self.study, self.out).write_text(van, encoding="utf-8", newline="\n")
        r = self.chay("G6.5 kiểm bản diễn giải", "dien_giai_ket_qua.py", "kiem", "--study", self.study)
        self.cong["G6_5"] = {"trang_thai": "DAT" if r.get("ma") == 0 else f"CON_LOI (mã {r.get('ma')})",
                             "loi": [d for d in r["dong"] if d.lstrip().startswith(("✗", "-", "•"))][:12]}

    def _gia_tri_ket_qua(self) -> Dict[str, Any]:
        """Số của phân tích chính để điền lời văn (G6.5, G7…) — luôn đọc lại tệp kết quả, không giữ trong bộ nhớ."""
        chinh = self._uoc_luong("pr_hieu_chinh", "G6") or {}
        rd = self._uoc_luong("hieu_so_nguy_co", "G6") or {}
        tom = _doc_json(self.out / "G6_analysis_summary.json")
        pc = tom.get("primary_outcome") or {}
        ci = chinh.get("ci") or [0, 0]
        return {"rr": self._so_vn(chinh.get("uoc", 0), 2), "rr_duoi": self._so_vn(ci[0], 2),
                "rr_tren": self._so_vn(ci[1], 2), "rd_phan_tram": self._so_vn(100 * rd.get("uoc", 0), 1),
                "pct1": self._so_vn((pc.get("group_1") or {}).get("pct", 0), 1),
                "pct0": self._so_vn((pc.get("group_0") or {}).get("pct", 0), 1),
                "nnh": round(1 / rd["uoc"]) if rd.get("uoc") else "—", "n": tom.get("n_total"),
                "bien_co": (tom.get("poisson_pr") or {}).get("n_bien_co"),
                "p": "< 0,001" if (chinh.get("p") or 1) < 0.001 else self._so_vn(chinh.get("p") or 0, 3)}

    def _env_mang(self) -> Dict[str, str]:
        """Môi trường cho bước TRA CỨU mạng (kiểm trích dẫn): như phần A — bỏ biến pytest và khoá giả (bước này không
        ký gì; dưới pytest app.config không nạp cấu hình nguồn ⇒ nguồn giả)."""
        return {k: v for k, v in self.env.items()
                if not k.startswith("PYTEST_") and k not in ("EBM_GATE_KEY_PATH", "USE_MOCK_SOURCES")}

    def _a12(self, *tep: Path) -> None:
        """Người kiểm trích dẫn: mọi PMID trong các tệp ⇒ check_citations (rút bài 3 tầng + metadata, ghi receipt) ⇒
        A12 chỉ ghi dòng «đã xác minh» khi lệnh trả 0."""
        pmid = sorted({x for t in tep if t.is_file() for x in re.findall(r"PMID[:\s]*(\d{6,9})",
                                                                         t.read_text(encoding="utf-8"))})
        if not pmid:
            return
        # Hai bước TÁCH: (1) tra mạng KHÔNG --study ⇒ không ký gì, dùng cấu hình nguồn thật (dưới pytest app.config
        # không nạp cấu hình ⇒ nguồn giả); (2) ghi receipt bằng ĐÚNG hàm của check_citations trong môi trường KHOÁ GIẢ.
        # Bản đầu
        # gọi thẳng `--study` ngoài biến pytest ⇒ receipt của thư mục giả lập bị ký bằng khoá THẬT (sửa 15/11/2026).
        kq = self.chay_lenh(self._lenh("check_citations.py", "--pmids", ",".join(pmid), "--json"),
                            self.repo, self._env_mang(), 900)
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
        van = (f"# A12 — Xác minh trích dẫn — {self.study}\n\n> {NHAN_MO_PHONG}\n\n"
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
        self.du_lieu["a12"] = {"pmid": pmid, "sach": sach}

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

    def g7(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tg = hs.get("tac_gia_G7") or {}
        tap_chi = tg.get("target_journal") or "Tạp chí Y học Việt Nam (giả lập)"
        self.chay("G7 sinh bản thảo", "run_g7_auto.py", "--study", self.study, "--target-journal", tap_chi)
        a8 = self.out / f"G7_A8_MANUSCRIPT_{self.study}.md"
        gt = self._gia_tri_ket_qua()
        dg = hs.get("dien_giai") or {}
        gt.update({f"muc_{i}": str(dg.get(f"muc_{i}", "")).format(**gt) for i in range(2, 6)})
        tl = [(m, v.format(**gt)) for m, v in hs.get("tra_loi_G7", [])]
        self.hoan_thien_tep("G7", a8, tl + list(TRA_LOI_CHUNG), {})
        self._bien_tap_ban_nop(a8)
        self._a12(a8, self.out / f"G6_DIEN_GIAI_{self.study}.md")
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

    def _vao_meta(self, g: str, gia_tri: Mapping[str, Any]) -> None:
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault(g, {}).update(dict(gia_tri))
        self._ghi_meta(meta)

    def _ghi_phan_bien(self) -> None:
        """Người phản biện ĐỘC LẬP (mô phỏng, vai riêng GIA-LAP-PB) viết bản nhận xét theo mẫu binh-duyet.md từ hồ
        sơ."""
        pb = (self.kb.get("ho_so_tron_vong") or {}).get("phan_bien_G8")
        if not pb:
            return
        gt = self._gia_tri_ket_qua()
        bang_nho = "\n".join(f"| {i} | {vt} | {gy} |" for i, (vt, gy) in enumerate(pb["gop_y_nho"], 1))
        hoi = "\n".join(f"{i}. {c}" for i, c in enumerate(pb["cau_hoi"], 1))
        van = f"""# Bản nhận xét phản biện — {self.study}

> {NHAN_MO_PHONG} — người phản biện MÔ PHỎNG (vai riêng, không phải tác giả/chủ nhiệm)

════════════════════════════════════════════════════════════════
TÓM TẮT NHẬN XÉT — {pb["ten_bai"]} — {pb["thiet_ke"]} — G8 / {self.hom_nay.isoformat()}
════════════════════════════════════════════════════════════════

KHUYẾN NGHỊ: ☐ Chấp nhận ☑ Sửa nhỏ ☐ Sửa lớn ☐ Từ chối
Lý do: {pb["ly_do"].format(**gt)}

════════ LỖI NGHIÊM TRỌNG (phải sửa trước khi nộp) ════════
Không có.

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
Lăng kính 1 (Phương pháp): ☐ PASS ☑ Lỗi nhỏ ☐ Lỗi nghiêm trọng
Lăng kính 2 (Thống kê): ☑ PASS ☐ Lỗi nhỏ ☐ Lỗi nghiêm trọng
Lăng kính 3 (Liêm chính): ☑ PASS ☐ Lỗi nhỏ ☐ Lỗi nghiêm trọng

════════ KHAI BÁO CỦA NGƯỜI PHẢN BIỆN (bắt buộc — ICMJE Mục V.B + §II.B.1.b) ════════
Xung đột lợi ích với nhóm nghiên cứu: ☑ Không có ☐ Có (ghi rõ):
Có phải đồng tác giả/cấp trên/cấp dưới trực tiếp của tác giả không: ☑ Không ☐ Có
Có dùng AI khi phản biện không: ☐ Không ☑ Có (tên công cụ + mục đích): bộ giả lập trọn vòng của hệ — mô phỏng vai \
người phản biện để kiểm dây chuyền
Cam kết KHÔNG tải bản thảo lên công cụ AI thiếu bảo đảm bảo mật khi chưa được tạp chí/chủ nhiệm cho phép: ☑ Xác nhận

Kết luận tổng thể: sẵn sàng nộp (sau khi xử lý các góp ý nhỏ)
════════════════════════════════════════════════════════════════
"""
        (self.out / f"G8_PEER_REVIEW_REPORT_{self.study}.md").write_text(van, encoding="utf-8", newline="\n")

    def g8(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tap_chi = (hs.get("tac_gia_G7") or {}).get("target_journal") or "Tạp chí Y học Việt Nam (giả lập)"
        self._ghi_phan_bien()  # bản nhận xét có TRƯỚC A9 — A9 nhúng băm nó (G8-AUTO-12b)
        po = _gp(self._meta(), "G1").get("primary_outcome") or {}
        self._vao_meta("G8", {**(hs.get("tham_so_G8") or {}),
                              "primary_outcome": po.get("name") if isinstance(po, Mapping) else None,
                              "reviewer_coi_declared": True,
                              "reviewer_independence_declared": True, "reviewer_ai_use_declared": True,
                              "reviewer_confidentiality_declared": True, "reviewed_at": GL._bay_gio()})
        self.chay("G8 sinh hồ sơ trước nộp (A9)", "run_g8_auto.py", "--study", self.study, "--target-journal", tap_chi)
        self._dien_cong("G8", f"G8_*{self.study}*.md", hs.get("tra_loi_G8", []))
        self.cong["G8_truoc_ky"] = {"trang_thai": self.cham("G8"),
                                    "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G8", self.study, self.out,
                                                                                 self.repo))}
        self._ky("G8", f"G8_A9_PRESUBMISSION_{self.study}.md", "INDEPENDENT_PEER_REVIEWER", "GIA-LAP-PB")
        self.cong["G8"] = {"trang_thai": self.cham("G8"),
                           "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G8", self.study, self.out, self.repo))}
        self.do_truc("sau_G8")

    def g9(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        tap_chi = (hs.get("tac_gia_G7") or {}).get("target_journal") or "Tạp chí Y học Việt Nam (giả lập)"
        self.chay("G9 sinh bộ khai báo liêm chính", "run_g9_auto.py", "--study", self.study, "--n-authors", "2",
                  "--target-journal", tap_chi)
        self._khai_g9()
        self._vao_meta("G9", {**(hs.get("tham_so_G9") or {}), "reviewed_by_role": "PI", "reviewed_at": GL._bay_gio()})
        # Quy trình thật: tác giả khai phiếu có cấu trúc rồi sinh lại gói — A10/cover letter lấy CRediT, người truy cập
        # dữ liệu, COI, tài trợ, AI, chia sẻ dữ liệu từ phiếu và từ quyết định đã chốt (run_g9_auto 16/11/2026).
        self.chay("G9 sinh lại gói sau khi tác giả khai phiếu", "run_g9_auto.py", "--study", self.study, "--n-authors",
                  "2", "--target-journal", tap_chi)
        self._dien_cong("G9", f"G9_*{self.study}*.md", hs.get("tra_loi_G9", []))
        self._checklist_bao_cao()
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
        (self.out / ten).write_text(f"# Checklist chuẩn báo cáo — {self.study}\n\n> {NHAN_MO_PHONG}\n\n"
                                    "| Mục | Nội dung | Trạng thái | Ghi chú |\n|---|---|---|---|\n"
                                    + "\n".join(hang) + "\n\nCần bác sĩ kiểm chứng.\n",
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
                                                       "phân tích hay quyết định công bố (giả lập)"),
                            "sponsor_no_publication_restriction_confirmed": True}
        d["ai_disclosure"] = {"ai_used": True, "tools": ["Bộ giả lập trọn vòng của hệ EBM (giả lập)"],
                              "purposes": ["soạn nháp và kiểm dây chuyền; tác giả đọc lại, đối chiếu số liệu"],
                              "human_verification_confirmed": True, "sensitive_or_confidential_data_uploaded": False,
                              "ai_not_author_confirmed": True, "manuscript_statement_final": True,
                              "cover_letter_statement_final": True, "confirmed_at": nay}
        d["data_availability"] = {**(d.get("data_availability") or {}), "decision": "NOT_SHARED_WITH_JUSTIFICATION",
                                  "statement_final": True, "clinical_trial": False,
                                  "access_criteria": "Dữ liệu mô phỏng của bộ giả lập — không có dữ liệu người thật để "
                                                     "chia sẻ; kịch bản phân tích kèm gói phát hành"}
        d["data_access_governance"] = {**(d.get("data_access_governance") or {}),
                                       "all_authors_can_review_supporting_data": True,
                                       "primary_data_access_author_ref": "AUTHOR-01",
                                       "primary_data_access_confirmed": True, "analysis_participation_confirmed": True,
                                       "academic_nonacademic_collaboration": False, "sponsored_research": False,
                                       "confirmed_at": nay}
        d["publication_integrity"] = {"original_work_confirmed": True, "duplicate_submission_absent": True,
                                      "overlap_disclosed": True, "preprint_status_declared": True,
                                      "plagiarism_review_completed": True, "plagiarism_report_ref": "GIA-LAP-SIM-01",
                                      "journal_or_institution_criterion": "trùng lặp < 15% (tiêu chí đơn vị, giả lập)",
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

    def g10(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        self._khai_dac_ta_g10()
        self.chay("G10 lắp gói phát hành (lượt dựng)", "run_g10_assemble.py", "--study", self.study)
        self._dien_cong("G10", f"*G10*{self.study}*.md", hs.get("tra_loi_G10", []))
        self._dien_cong("G10", f"DE_CUONG_THONG_NHAT_{self.study}.md", hs.get("tra_loi_G10", []))
        # A12 phủ HỢP mọi PMID của gói — gồm đề cương thống nhất G10 (kiem_ban_g10) — rồi PI khai và lắp lại
        tep_goi = [*sorted(self.out.glob(f"G[6-9]*_{self.study}.md")),
                   self.out / f"DE_CUONG_THONG_NHAT_{self.study}.md"]
        pmid_goi = {x for t in tep_goi if t.is_file()
                    for x in re.findall(r"PMID[:\s]*(\d{6,9})", t.read_text(encoding="utf-8"))}
        da_kiem = set(_doc_json(self.out / "A12_RETRACTION_RECEIPT.json").get("pmids_checked") or [])
        if pmid_goi - da_kiem:  # ghi lại receipt làm vỡ manifest G9 đã khoá ⇒ chỉ khi gói có PMID CHƯA kiểm
            self.du_lieu["g10_pmid_moi"] = sorted(pmid_goi - da_kiem)
            self._a12(*tep_goi)
        self._khai_g10()
        self.chay("G10 lắp lại gói sau khi PI khai", "run_g10_assemble.py", "--study", self.study)
        self.cong["G10_truoc_ky"] = {"trang_thai": self.cham("G10"),
                                     "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G10", self.study, self.out,
                                                                                  self.repo))}
        self._ky("G10", "G10_checkpoint.json", "PI", "GIA-LAP-PI")
        self.cong["G10"] = {"trang_thai": self.cham("G10"),
                            "chua_dat": GL.GiaLap._chua_dat(GL.cham_song("G10", self.study, self.out, self.repo))}
        self.do_truc("sau_G10")

    # ── báo cáo
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
                "crash": [b["buoc"] for b in self.buoc if b.get("crash")], "buoc": self.buoc}

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


# Câu trả lời CHUNG của các vai (thông tin hành chính, không PII thật): mẫu nhãn đã bỏ dấu → giá trị.
TRA_LOI_CHUNG: Tuple[Tuple[str, str], ...] = (
    (r"^bac si( \+ doi nc)?$", "Bác sĩ/nhóm nghiên cứu (giả lập)"),  # thẻ NGƯỜI PHỤ TRÁCH ở danh sách việc của DMP
    (r"chu nhiem|ho ten chu nhiem|ten chu nhiem|nghien cuu vien chinh|principal investigator",
     "PI-REF-01 (chủ nhiệm — mã vai trò, giả lập)"),
    (r"chuc vu|chuc danh|trinh do", "Bác sĩ điều trị (giả lập)"),
    (r"^don vi|don vi thuc hien|co quan|institution", "Phòng khám ngoại trú bệnh viện (giả lập)"),
    (r"dien thoai|phone", "—"), (r"email", "—"),
    (r"tai tro|funding|sponsor", "Không có tài trợ bên ngoài"),
    (r"xung dot loi ich|coi\b|conflict", "Không có xung đột lợi ích"),
    (r"hoi dong dao duc|ethics committee", "Hội đồng Đạo đức cơ sở (giả lập)"),
    (r"tinh|tinh thanh|province", "TP. Hồ Chí Minh"),
    (r"noi luu|luu tai|may chu", "Máy chủ nội bộ có mã hoá, phân quyền theo vai trò"),
    (r"sao luu|backup", "Sao lưu hằng ngày, 2 bản độc lập"),
    (r"thoi gian luu|nam\]?$|xoa/an danh", "2"),
    (r"ten tac gia|tac gia", "Thống kê viên (vai trò — giả lập)"),
    (r"phan mem", "R 4.6 (phân tích chính); kiểm chéo SPSS 31"),
    (r"packages", "stats, sandwich, lmtest, mice"),
    (r"random seed|seed", "20261115"),
    (r"tap chi|hoi nghi", "Tạp chí Y học Việt Nam (giả lập)"),
    (r"nguoi kiem tra dau ra", "PI-REF-01"),
    (r"so ban nop", "3"),
    (r"thoi gian luu", "2"),
    (r"xoa/huy|huy vat ly|trong\s*$", "6"),
    (r"ten don vi", "Phòng khám ngoại trú bệnh viện (giả lập)"),
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
