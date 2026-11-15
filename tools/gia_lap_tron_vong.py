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

import json
import math
import os
import random
import re
import secrets
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
        (r"tieu chi (nhan|chon|lua chon|thu nhan)|inclusion", g1.get("inclusion_criteria"), "G1.inclusion_criteria"),
        (r"tieu chi loai|exclusion", g1.get("exclusion_criteria"), "G1.exclusion_criteria"),
        (r"ket cuc chinh|kq chinh|primary outcome",
         " — ".join(_text(po.get(k)) for k in ("name", "measure", "timepoint") if po.get(k)), "G1.primary_outcome"),
        (r"ket cuc phu|secondary outcome", g1.get("secondary_outcomes"), "G1.secondary_outcomes"),
        (r"^muc tieu|^objective|muc tieu 1", g1.get("objectives"), "G1.objectives"),
        (r"doi tuong nghien cuu|quan the nghien cuu|^population", g1.get("population"), "G1.population"),
        (r"dia diem|noi (nghien cuu|thuc hien)|co so nghien cuu|setting", g1.get("setting"), "G1.setting"),
        (r"thoi gian nghien cuu|study period", g1.get("study_period"), "G1.study_period"),
        (r"(^|\s)co mau|sample size|so nguoi tham gia du kien", n, "G3.n"),
        (r"ten de tai|^title|public title", meta.get("title") or meta.get("topic"), "title"),
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
            r"nct_|anzctr|ma dang ky|dang ky thanh cong|ngay dang ky|registration (id|number|date)|registry|"
            r"dang ky nghien cuu|tuyen sau phe duyet va dang ky", t):
        return "PI đã chốt đề tài không bắt buộc đăng ký"
    return None


# Ô có thể XUỐNG DÒNG và LỒNG một cấp ngoặc («[CẦN, máy chủ nội bộ … tại [đơn vị]]»).
O_DA_DONG_RE = re.compile(
    r"\[(?:CẦN|CẦN|TO BE COMPLETED)(?:[^\[\]]|\[[^\[\]]{0,80}\]){0,600}\]"   # ô [CẦN…] (xuống dòng, lồng 1 cấp)
    r"|\[[^\[\]\n]{1,60}(?:CẦN|CẦN)[^\[\]\n]{0,80}\]"                      # «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]»
    r"|_{3,}(?:\s*/\s*_{2,}\s*/\s*_{2,})?",                                  # ô gạch dưới «___», «___/___/____»
    re.S)


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
        nhan = (truoc.split(":")[-1].strip() if ":" in truoc else truoc)[-80:]
        trong_o = re.sub(r"^\[\s*(?:cần|can|to be completed)[\s,.—:–-]*", "", bo_dau(o_txt)).rstrip("] ").strip()
        if not nhan or "]" in nhan or "[" in nhan:
            nhan = trong_o[:80] or nhan  # nhãn trước ô lẫn đuôi ô khác ⇒ dùng nội dung trong ô
        k = bo_dau(nhan)
        o = {"cong": cong, "tep": tep, "dong": so, "nhan": nhan, "o": o_txt, "vi_tri": m.start()}
        ly_do = khong_ap_dung(nhan, dong + " " + o_txt, thiet_ke, meta)
        chot = next(((v, ten) for mau, v, ten in bang if mau.search(k)), None)
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
            o.update(loai="chua_co_ho_so",
                     dien=re.sub(r"_{2,}", "", f"{nhan or 'nội dung'} (GIẢ LẬP — hồ sơ chưa có)"))
        if k and o["loai"] in ("moi_dung_vai", "chua_co_ho_so"):
            da_hoi.setdefault(k, o["dien"])
        ra.append(o)
    return ra


def dien_o(tep_text: str, cac_o: Sequence[Mapping[str, Any]]) -> str:
    """Thay từng ô bằng giá trị đã phân loại — theo VỊ TRÍ trong cả tệp (từ cuối lên để vị trí không trôi)."""
    s = tep_text
    for o in sorted(cac_o, key=lambda x: x["vi_tri"], reverse=True):
        a, b = o["vi_tri"], o["vi_tri"] + len(o["o"])
        if s[a:b] == o["o"]:
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


def sinh_du_lieu(thiet_ke: str, ho_so_bien: Mapping[str, Any], g3: Mapping[str, Any], n: int,
                 seed: int = 20261115) -> List[Dict[str, Any]]:
    """Dữ liệu MÔ PHỎNG theo bộ biến + giả định G3 (đúng hướng hiệu ứng đã khai). Không dùng lâm sàng."""
    rng = random.Random(seed)
    ma_tran = ho_so_bien["ma_tran"]
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
        for ten, kieu, nhan, lua, val, _muc in ho_so_bien["bo_bien"]:
            if ten in ("record_id", "ma_nguoi_tham_gia", "study_id"):
                r[ten] = f"R{i + 1:04d}"
            elif kieu in ("yesno",) or (kieu == "radio" and lua.count("|") == 1):
                r[ten] = _bern(rng, 0.3)
            elif kieu in ("radio", "dropdown"):
                so = [int(x.split(",")[0]) for x in lua.split("|")]
                r[ten] = rng.choice(so)
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


def _phi_nguoc(p: float) -> float:
    """Φ⁻¹(p) xấp xỉ (Acklam) — đủ cho dựng dữ liệu mô phỏng có AUC đích."""
    from statistics import NormalDist  # noqa: PLC0415

    return NormalDist().inv_cdf(min(max(p, 1e-6), 1 - 1e-6))


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
        if not tep.is_file():
            return
        s = tep.read_text(encoding="utf-8")
        cac_o = phan_loai_o(s, g, tep.name, self._meta(), {x: self._cp(x) for x in ("G0", "G1", "G3")},
                            self.thiet_ke, tra_loi, da_hoi)
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
        self.do_truc("sau_G2")

    # ── G4
    def g4(self) -> None:
        hs = self.kb.get("ho_so_tron_vong") or {}
        sap = self.out / f"G4_A5_SAP_FINAL_{self.study}.md"
        if not sap.is_file():
            self.chay("G4 sinh SAP", "run_g4_auto.py", "--study", self.study)
        da_hoi: Dict[str, str] = {}
        self.hoan_thien_tep("G4", sap, list(hs.get("tra_loi_G4", [])) + list(TRA_LOI_CHUNG), da_hoi)
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
        so_bien = sum(1 for d in (self.kb.get("ho_so_bien") or {}).get("ma_tran", ())
                      if d[2] in ("phoi_nhiem", "hiep_bien", "yeu_to"))
        p = float(g3.get("p0") or g3.get("prevalence") or 0.2)
        bien_co = n * min(p, 1 - p)
        cau = (f"- **EPV/VIF (thống kê viên):** EPV ước tính ≈ {bien_co:.0f} biến cố / {max(so_bien, 1)} tham số ≈ "
               f"{bien_co / max(so_bien, 1):.0f}; kiểm đa cộng tuyến VIF < 5 trước khi chốt mô hình.\n")
        s = s[:than5.end(1)] + cau + s[than5.end(1):]
        sap.write_text(s, encoding="utf-8", newline="\n")
        self.o.append({"cong": "G4", "tep": sap.name, "dong": 0, "nhan": "EPV/VIF §5 (thống kê viên bổ sung)",
                       "o": "", "vi_tri": -1, "loai": "moi_dung_vai", "dien": cau.strip()})

    # ── báo cáo
    def bao_cao(self) -> Dict[str, Any]:
        theo_cong: Dict[str, Any] = {}
        for g in sorted({o["cong"] for o in self.o}):
            theo_cong[g] = tom_tat_o([o for o in self.o if o["cong"] == g])
        loi_may = [f"{self.ma}:{o['cong']}:{o['loai']}:{o['tep']}:«{o['nhan']}»" for o in self.o
                   if o["loai"] in LOAI_O_LOI_MAY]
        return {"ma": self.ma, "study": self.study, "thiet_ke": self.thiet_ke, "phan_a": self.phan_a,
                "cong": self.cong, "o_theo_cong": theo_cong, "truc": self.truc, "dung": self.dung,
                "so_o_loi_may": len(loi_may), "o_loi_may": sorted(set(loi_may))[:200],
                "crash": [b["buoc"] for b in self.buoc if b.get("crash")], "buoc": self.buoc}

    def chay_tron_vong(self) -> Dict[str, Any]:
        self._khoa_vai()
        if not self.phan_a_chay():
            return self.bao_cao()
        if duoi_pytest_khoa_gia():
            self.chay("Đánh dấu đề tài tổng hợp (bản sao tạm)", "mark_study_synthetic.py", "--study", self.study,
                      "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        for buoc in (self.g2, self.g4):
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


def chay_mot(ma: str, repo: Path, **kw: Any) -> Dict[str, Any]:
    return TronVong(ma, repo, **kw).chay_tron_vong()
