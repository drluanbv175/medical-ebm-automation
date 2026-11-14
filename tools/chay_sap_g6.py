#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chay_sap_g6.py — CHẠY TRỌN SAP bằng MỘT lệnh: mọi phân tích SAP đã khoá (chính · phụ · nhóm con · độ nhạy) theo
một ĐẶC TẢ MÁY ĐỌC, mỗi phân tích qua đúng run_stats_analysis.py (+ kiểm chéo SPSS/R tuỳ chọn), rồi một CHỈ MỤC kết quả.

Vì sao có tệp này (14/11/2026, soát chuỗi SPSS/R theo yêu cầu bác sĩ — «F3 Chạy trọn SAP một lệnh»): SAP thật cam kết
nhiều phân tích (C1a: tỷ lệ mục tiêu 1, mô hình thứ tự chính, logistic nhị phân, loại phiếu có hỗ trợ ghi…; BTM: tỷ lệ
kết cục chính, 3 kết cục phụ, nhóm con, Poisson PR, 9 độ nhạy) nhưng run_stats_analysis chạy MỘT đặc tả mỗi lần, gõ tay
từng bộ tham số — dễ sót, dễ lệch SAP, không có chỗ nào cho biết đã chạy hết chưa.

Đặc tả: `exports/<mã>/G6_DAC_TA_SAP.json`
  {
    "nguon_sap": "G4_A5_SAP_FINAL_<mã>.md",
    "sha256_sap": "<SHA-256 của SAP lúc soạn đặc tả>",
    "phan_tich": [
      {"id": "MT2_chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "…",
       "tham_so": {"outcome": "g1", "group": "thoigian_cho", "covariates": ["tuoi", "khunggio_kham"],
                   "hiep_bien_phan_loai": ["khunggio_kham"], "outcome_type": "ordinal", "don_vi_phoi_nhiem": 15,
                   "cot_cum": "ma_ban_kham", "loc": "PhieuHopLe == 1"}},
      {"id": "DN_spline", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "…", "chua_tu_dong": "lý do"}
    ],
    "nguoi_duyet": "<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu đặc tả 12 hex>"
  }
  • vai ∈ chinh (đúng MỘT, chạy với gate G6 — tệp G6_analysis_summary.json chính thức) · phu · nhom_con · do_nhay ·
    mo_ta; phân tích khác chạy với gate G6_<id> (tệp riêng, không ghi đè nhau).
  • `chua_tu_dong` = phân tích SAP cam kết mà hệ CHƯA có công cụ (vd spline RCS, partial PO) — liệt kê rõ trong chỉ mục
    là «chờ thống kê viên làm tay», không bỏ im.
  • `sha256_sap` khác SAP hiện tại ⇒ đặc tả CŨ (SAP đã sửa đổi) — từ chối chạy.
  • nguoi_duyet do THỐNG KÊ VIÊN/PI ghi kèm dấu đặc tả (lệnh `kiem` in ra) — agent soạn đặc tả, KHÔNG ghi cột duyệt;
    sửa đặc tả sau khi duyệt ⇒ hết hiệu lực. Chưa duyệt ⇒ từ chối chạy (đề tài synthetic_test: cảnh báo).

Lệnh
  kiem    --study <mã> [--json]                         đặc tả hợp lệ? dấu, trạng thái duyệt, SAP còn khớp?
  chay    --study <mã> [--chi id1,id2] [--kiem-cheo]    chạy lần lượt (dữ liệu ĐÃ KHOÁ G5 — kiểm bằng hàm của cổng)
  ket-qua --study <mã> [--json]                         chỉ mục G6_SAP_ket_qua.json
Không bao giờ truyền cờ ghi đè cổng (--i-confirm-*). Mã thoát: 0 đạt · 1 có phân tích lỗi/lệch · 2 không đo được ·
3 từ chối (đặc tả sai/cũ/chưa duyệt, dữ liệu chưa khoá). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import bien_phai_sinh as BPS  # noqa: E402

TEP_DAC_TA = "G6_DAC_TA_SAP.json"
TEP_KQ_JSON, TEP_KQ_MD = "G6_SAP_ket_qua.json", "G6_SAP_ket_qua.md"
THU_MUC_NHAT_KY = "G6_SAP_nhat_ky"
VAI = ("chinh", "phu", "nhom_con", "do_nhay", "mo_ta")
CAN_KIEM = "Cần bác sĩ kiểm chứng."
THOI_HAN = 7200
# tham số đặc tả ⇒ cờ run_stats_analysis.py (kiểu: s = tên/chuỗi, ds = danh sách tên, so = số, nguyen = số nguyên)
THAM_SO = {
    "outcome": ("--outcome", "s"),
    "group": ("--group", "s"),
    "covariates": ("--covariates", "ds"),
    "hiep_bien_phan_loai": ("--hiep-bien-phan-loai", "ds"),
    "outcome_type": ("--outcome-type", "s"),
    "don_vi_phoi_nhiem": ("--don-vi-phoi-nhiem", "so"),
    "cot_cum": ("--cot-cum", "s"),
    "ty_le": ("--ty-le", "ds_rieng"),
    "nguong_ty_le": ("--nguong-ty-le", "so"),
    "vars": ("--vars", "ds"),
    "time": ("--time", "s"),
    "event": ("--event", "s"),
    "n_imputations": ("--n-imputations", "nguyen"),
    "loc": ("--loc", "bt"),
}
LOAI_KC = ("auto", "binary", "continuous", "ordinal", "poisson_pr")
TEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class TuChoi(RuntimeError):
    pass


class KhongDoDuoc(RuntimeError):
    pass


def thu_muc(study: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", study or ""):
        raise TuChoi(f"mã đề tài không hợp lệ: {study!r}")
    d = BASE / "exports" / study
    if not d.is_dir():
        raise TuChoi(f"không có thư mục đề tài exports/{study}")
    return d


def sha256_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dau_dac_ta(dt: dict) -> str:
    """Dấu 12 hex của (SAP gốc, danh sách phân tích) — cột nguoi_duyet phải mang đúng dấu này."""
    goi = json.dumps([dt.get("sha256_sap"), dt.get("phan_tich")], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(goi.encode("utf-8")).hexdigest()[:12]


def doc_dac_ta(d: Path) -> dict:
    p = d / TEP_DAC_TA
    if not p.exists():
        raise KhongDoDuoc(f"đề tài chưa có {TEP_DAC_TA}")
    try:
        dt = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise TuChoi(f"{TEP_DAC_TA} không phải JSON hợp lệ: {e}") from e
    if not isinstance(dt, dict):
        raise TuChoi(f"{TEP_DAC_TA} phải là một đối tượng JSON")
    return dt


def _kiem_gia_tri(ten: str, kieu: str, v) -> list[str]:
    def chuoi_an_toan(x) -> bool:
        return isinstance(x, str) and x.strip() != "" and not x.strip().startswith("-") and "\n" not in x

    if kieu == "s":
        if not chuoi_an_toan(v) or (ten != "outcome_type" and not TEN_RE.match(v)):
            return [f"{ten}: cần tên cột hợp lệ"]
        if ten == "outcome_type" and v not in LOAI_KC:
            return [f"outcome_type phải thuộc {LOAI_KC}"]
    elif kieu in ("ds", "ds_rieng"):
        if not isinstance(v, list) or not v or not all(chuoi_an_toan(x) and TEN_RE.match(x) for x in v):
            return [f"{ten}: cần danh sách tên cột hợp lệ (không rỗng)"]
    elif kieu == "so":
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return [f"{ten}: cần một số"]
    elif kieu == "nguyen":
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 200:
            return [f"{ten}: cần số nguyên 0–200"]
    elif kieu == "bt":
        if not chuoi_an_toan(v):
            return [f"{ten}: cần biểu thức (không bắt đầu bằng «-»)"]
        try:
            BPS.phan_tich(v)
        except BPS.LoiCongThuc as e:
            return [f"{ten}: {e}"]
    return []


def kiem_dac_ta(d: Path, dt: dict) -> dict:
    """Kiểm cấu trúc + SAP còn khớp + trạng thái duyệt. Trả {loi[], canh_bao[], dau, duyet, sap_khop, phan_tich[]}."""
    loi: list[str] = []
    canh_bao: list[str] = []
    sap = d / str(dt.get("nguon_sap") or "")
    sap_khop: bool | None = None
    if not dt.get("nguon_sap") or not sap.is_file():
        loi.append(f"nguon_sap không trỏ tới tệp SAP có thật trong thư mục đề tài ({dt.get('nguon_sap')!r})")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(dt.get("sha256_sap") or "")):
        loi.append("sha256_sap thiếu hoặc sai dạng (64 hex)")
    else:
        sap_khop = sha256_tep(sap) == dt["sha256_sap"]
        if not sap_khop:
            loi.append("SAP đã ĐỔI sau khi soạn đặc tả (SHA-256 khác) — soạn lại theo SAP hiện tại rồi duyệt lại")
    ds = dt.get("phan_tich")
    if not isinstance(ds, list) or not ds:
        loi.append("phan_tich phải là danh sách không rỗng")
        ds = []
    ids: set[str] = set()
    so_chinh = 0
    for i, pt in enumerate(ds):
        nhan = f"phan_tich[{i}]"
        if not isinstance(pt, dict):
            loi.append(f"{nhan}: phải là đối tượng")
            continue
        pid = pt.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,40}", pid):
            loi.append(f"{nhan}: id phải gồm chữ/số/_ (1–40 ký tự)")
            continue
        if pid in ids:
            loi.append(f"id trùng: {pid}")
        ids.add(pid)
        if pt.get("vai") not in VAI:
            loi.append(f"{pid}: vai phải thuộc {VAI}")
        if not pt.get("sap_muc") or not pt.get("mo_ta"):
            loi.append(f"{pid}: thiếu sap_muc hoặc mo_ta (truy nguyên về SAP)")
        if pt.get("chua_tu_dong"):
            if pt.get("tham_so"):
                loi.append(f"{pid}: đã khai chua_tu_dong thì không khai tham_so")
            if pt.get("vai") == "chinh":
                loi.append(f"{pid}: phân tích CHÍNH không được để «chưa tự động»")
            continue
        ts = pt.get("tham_so")
        if not isinstance(ts, dict) or not ts:
            loi.append(f"{pid}: thiếu tham_so (hoặc khai chua_tu_dong kèm lý do)")
            continue
        la = [k for k in ts if k not in THAM_SO]
        if la:
            loi.append(f"{pid}: tham số không hỗ trợ: {', '.join(la)}")
        for k, v in ts.items():
            if k in THAM_SO:
                loi += [f"{pid}: {x}" for x in _kiem_gia_tri(k, THAM_SO[k][1], v)]
        if not ts.get("outcome") and not ts.get("time") and not ts.get("ty_le"):
            loi.append(f"{pid}: cần outcome, hoặc time+event, hoặc ty_le")
        if bool(ts.get("time")) != bool(ts.get("event")):
            loi.append(f"{pid}: time và event phải đi cùng nhau")
        if pt.get("vai") == "chinh":
            so_chinh += 1
    if so_chinh != 1:
        loi.append(f"cần ĐÚNG một phân tích vai «chinh» có tham_so (đang có {so_chinh})")
    dau = dau_dac_ta(dt)
    duyet = BPS.trang_thai_duyet(str(dt.get("nguoi_duyet") or ""), dau)
    if duyet != "DA_DUYET":
        canh_bao.append(f"đặc tả {duyet} — thống kê viên/PI ghi nguoi_duyet «<VAI>:<tham chiếu>:<YYYY-MM-DD>:{dau}»")
    return {"loi": loi, "canh_bao": canh_bao, "dau": dau, "duyet": duyet, "sap_khop": sap_khop, "phan_tich": ds}


def gate_cua(pt: dict) -> str:
    return "G6" if pt.get("vai") == "chinh" else f"G6_{pt['id']}"


def doi_so_run_stats(pt: dict) -> list[str]:
    ds: list[str] = []
    for k, v in (pt.get("tham_so") or {}).items():
        co, kieu = THAM_SO[k]
        if kieu == "ds":
            ds += [co, ",".join(v)]
        elif kieu == "ds_rieng":
            ds += [co, *v]
        elif kieu in ("so", "nguyen"):
            ds += [co, format(v, "g") if isinstance(v, float) else str(v)]
        else:
            ds += [co, str(v)]
    if any(x.startswith("--i-confirm") for x in ds):  # rào cứng: không bao giờ ghi đè cổng
        raise TuChoi("cờ ghi đè cổng bị cấm")
    return ds


def _tom_tat_uoc_luong(tom: dict) -> dict:
    """Vài ước lượng chính của MỘT lượt (để chỉ mục đọc nhanh) — không thay bảng đầy đủ."""
    ra: dict = {"n_total": tom.get("n_total")}
    if tom.get("loc"):
        ra["loc"] = tom["loc"]
    pc = tom.get("primary_outcome") or {}
    if pc.get("or_crude") is not None:
        ra["or_tho"] = {"uoc_luong": pc["or_crude"], "ci_95": pc.get("ci_95"), "p": pc.get("p_value")}
    elif pc.get("md_crude") is not None:
        ra["md_tho"] = {"uoc_luong": pc["md_crude"], "p": pc.get("p_value")}
    nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
    for khoa, nhan in (("multivariate", "da_bien"), ("ordinal", "thu_tu"), ("poisson_pr", "poisson_pr")):
        mv = tom.get(khoa) or {}
        if mv.get("error"):
            ra[nhan] = {"loi": mv["error"]}
            continue
        for r in mv.get("results") or []:
            if r.get("variable") in (nhom, f"{nhom}_dv") or str(r.get("variable", "")).startswith(f"{nhom}"):
                ra[nhan] = {k: r.get(k) for k in ("variable", "OR_adj", "beta", "PR_adj", "OR", "CI_95", "p") if k in r}
                break
    if tom.get("ty_le"):
        ra["ty_le"] = [{k: x.get(k) for k in ("cot", "ty_le", "ci_95", "n", "ci_wilson_hieu_dung") if k in x}
                       for x in tom["ty_le"]][:6]  # fmt: skip
    sv = tom.get("survival") or {}
    if (sv.get("adjusted") or {}).get("HR") is not None:
        ra["hr_hieu_chinh"] = {k: sv["adjusted"].get(k) for k in ("HR", "CI_95", "p")}
    return ra


def _doc_json(p: Path) -> dict:
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def lenh_kiem(args) -> int:
    d = thu_muc(args.study)
    dt = doc_dac_ta(d)
    k = kiem_dac_ta(d, dt)
    if args.json:
        print(json.dumps({x: k[x] for x in ("loi", "canh_bao", "dau", "duyet", "sap_khop")} | {
            "phan_tich": [{"id": p.get("id"), "vai": p.get("vai"), "sap_muc": p.get("sap_muc"),
                           "chua_tu_dong": p.get("chua_tu_dong")} for p in k["phan_tich"] if isinstance(p, dict)]},
            ensure_ascii=False, indent=1))  # fmt: skip
    else:
        print(f"Đặc tả SAP G6 — {args.study}: {len(k['phan_tich'])} phân tích · dấu {k['dau']} · {k['duyet']}"
              f" · SAP {'khớp' if k['sap_khop'] else 'KHÔNG khớp/không đo được'}")  # fmt: skip
        for p in k["phan_tich"]:
            if isinstance(p, dict):
                tt = f"CHỜ LÀM TAY: {p['chua_tu_dong']}" if p.get("chua_tu_dong") else f"gate {gate_cua(p)}"
                print(f"  {p.get('id', '?'):24} {p.get('vai', '?'):9} {p.get('sap_muc', ''):6} {tt}")
        for x in k["loi"]:
            print(f"  ✗ {x}")
        for x in k["canh_bao"]:
            print(f"  ⚠ {x}")
        print(CAN_KIEM)
    return 1 if k["loi"] else 0


def lenh_chay(args) -> int:
    d = thu_muc(args.study)
    dt = doc_dac_ta(d)
    k = kiem_dac_ta(d, dt)
    if k["loi"]:
        raise TuChoi("đặc tả không hợp lệ: " + "; ".join(k["loi"][:5]))
    gia_lap = BPS.la_de_tai_gia_lap(d)
    if k["duyet"] != "DA_DUYET" and not gia_lap:
        raise TuChoi(f"đặc tả {k['duyet']} — chỉ chạy khi thống kê viên/PI đã duyệt (dấu {k['dau']})")
    import cau_noi_spss as S  # noqa: PLC0415 — kiểm khoá G5 bằng ĐÚNG hàm của cổng

    try:
        csv_khoa, _man = S.tim_du_lieu_khoa(args.study)
    except Exception as e:  # noqa: BLE001
        raise TuChoi(f"chưa có dữ liệu ĐÃ KHOÁ (G5) dùng được: {e}") from e
    chi = {x.strip() for x in (args.chi or "").split(",") if x.strip()}
    nk = d / THU_MUC_NHAT_KY
    nk.mkdir(exist_ok=True)
    ket: list[dict] = []
    ma = 0
    for pt in k["phan_tich"]:
        if chi and pt["id"] not in chi:
            continue
        muc = {"id": pt["id"], "vai": pt["vai"], "sap_muc": pt.get("sap_muc"), "mo_ta": pt.get("mo_ta")}
        if pt.get("chua_tu_dong"):
            ket.append(muc | {"trang_thai": "CHUA_TU_DONG", "ly_do": pt["chua_tu_dong"]})
            print(f"⏸  {pt['id']}: CHỜ thống kê viên làm tay — {pt['chua_tu_dong']}")
            continue
        gate = gate_cua(pt)
        lenh = [sys.executable, str(TOOLS / "run_stats_analysis.py"), "--data", str(csv_khoa), "--study", args.study,
                "--gate", gate, *doi_so_run_stats(pt), *(["--kiem-cheo"] if args.kiem_cheo else [])]  # fmt: skip
        print(f"▶  {pt['id']} ({pt['vai']}, {pt.get('sap_muc')}) — gate {gate}", flush=True)
        try:
            r = subprocess.run(lenh, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=THOI_HAN, stdin=subprocess.DEVNULL, cwd=BASE, check=False)  # fmt: skip
            ma_pt, out, err = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            ma_pt, out, err = None, "", f"quá thời hạn {THOI_HAN} giây"
        (nk / f"{pt['id']}.log").write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8",
                                            newline="\n")  # fmt: skip
        tom = _doc_json(d / f"{gate}_analysis_summary.json")
        muc |= {"gate": gate, "ma_thoat": ma_pt, "nhat_ky": f"{THU_MUC_NHAT_KY}/{pt['id']}.log"}
        if ma_pt != 0 or not tom:
            dong_cuoi = [x for x in (out + "\n" + err).splitlines() if x.strip()][-3:]
            muc |= {"trang_thai": "LOI", "ly_do": " | ".join(dong_cuoi)[:500]}
            ma = 1
            print(f"   ✗ lỗi (mã {ma_pt}) — {muc['ly_do'][:200]}")
        else:
            muc |= {"trang_thai": "DA_CHAY", "uoc_luong": _tom_tat_uoc_luong(tom)}
            if args.kiem_cheo:
                kc = _doc_json(d / f"{gate}_kiem_cheo.json")
                muc["kiem_cheo"] = kc.get("trang_thai") or "KHONG_DO_DUOC"
                if muc["kiem_cheo"] in ("LECH", "LOI", "TU_CHOI"):
                    ma = max(ma, 1)
            print("   ✓ xong" + (f" · kiểm chéo {muc.get('kiem_cheo')}" if args.kiem_cheo else ""))
        ket.append(muc)
    chi_muc = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dac_ta": {"tep": TEP_DAC_TA, "dau": k["dau"], "duyet": k["duyet"], "sha256_sap": dt.get("sha256_sap")},
        "du_lieu_khoa": {"tep": str(csv_khoa.relative_to(d)) if csv_khoa.is_relative_to(d) else csv_khoa.name,
                         "sha256": sha256_tep(csv_khoa)},  # fmt: skip
        "kiem_cheo": bool(args.kiem_cheo),
        "phan_tich": ket,
        "dem": {t: sum(1 for x in ket if x["trang_thai"] == t) for t in ("DA_CHAY", "LOI", "CHUA_TU_DONG")},
        "canh_bao": (["ĐỀ TÀI GIẢ LẬP — đặc tả chưa duyệt"] if k["duyet"] != "DA_DUYET" else []),
        "disclaimer": CAN_KIEM,
    }
    (d / TEP_KQ_JSON).write_text(json.dumps(chi_muc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (d / TEP_KQ_MD).write_text(md_chi_muc(chi_muc), encoding="utf-8", newline="\n")
    dm = chi_muc["dem"]
    print(f"\n══ SAP G6 — {args.study}: {dm['DA_CHAY']} đã chạy · {dm['LOI']} lỗi · "
          f"{dm['CHUA_TU_DONG']} chờ làm tay ══")
    print(f"✓ {d / TEP_KQ_MD}\n{CAN_KIEM}")
    return ma


def md_chi_muc(cm: dict) -> str:
    dong = [f"# Chỉ mục kết quả SAP G6 — {cm['study']}", "",
            f"Lúc {cm['luc']} · đặc tả `{cm['dac_ta']['tep']}` dấu `{cm['dac_ta']['dau']}` ({cm['dac_ta']['duyet']}) · "
            f"dữ liệu khoá SHA-256 `{cm['du_lieu_khoa']['sha256'][:16]}…` · kiểm chéo SPSS/R: "
            f"{'có' if cm['kiem_cheo'] else 'không'}", "",
            "| id | vai | SAP | trạng thái | gate | ước lượng chính | kiểm chéo |",
            "|---|---|---|---|---|---|---|"]  # fmt: skip
    for x in cm["phan_tich"]:
        u = x.get("uoc_luong") or {}
        chinh = next((json.dumps(u[k], ensure_ascii=False) for k in ("poisson_pr", "thu_tu", "da_bien", "or_tho",
                                                                       "md_tho", "hr_hieu_chinh", "ty_le") if k in u),
                     x.get("ly_do") or "")  # fmt: skip
        dong.append(f"| {x['id']} | {x['vai']} | {x.get('sap_muc') or ''} | {x['trang_thai']} | {x.get('gate', '—')} | "
                    f"{str(chinh)[:160].replace('|', '/')} | {x.get('kiem_cheo', '—')} |")  # fmt: skip
    cho = [x for x in cm["phan_tich"] if x["trang_thai"] == "CHUA_TU_DONG"]
    if cho:
        dong += ["", "## Chờ thống kê viên làm tay (hệ chưa có công cụ)", ""]
        dong += [f"- **{x['id']}** ({x.get('sap_muc')}): {x.get('mo_ta')} — {x.get('ly_do')}" for x in cho]
    dong += ["", "Bảng đầy đủ của từng phân tích: các tệp `<gate>_*.txt` và `<gate>_analysis_summary.json`.", "",
             CAN_KIEM]  # fmt: skip
    return "\n".join(dong) + "\n"


def lenh_ket_qua(args) -> int:
    d = thu_muc(args.study)
    cm = _doc_json(d / TEP_KQ_JSON)
    if not cm:
        raise KhongDoDuoc(f"chưa có {TEP_KQ_JSON} — chạy `chay_sap_g6.py chay --study {args.study}`")
    if args.json:
        print(json.dumps(cm, ensure_ascii=False, indent=1))
    else:
        print(md_chi_muc(cm))
    return 1 if cm.get("dem", {}).get("LOI") else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chạy trọn SAP G6 theo đặc tả máy đọc. " + CAN_KIEM)
    sp = ap.add_subparsers(dest="lenh", required=True)
    k = sp.add_parser("kiem")
    k.add_argument("--study", required=True)
    k.add_argument("--json", action="store_true")
    c = sp.add_parser("chay")
    c.add_argument("--study", required=True)
    c.add_argument("--chi", default="")
    c.add_argument("--kiem-cheo", action="store_true")
    q = sp.add_parser("ket-qua")
    q.add_argument("--study", required=True)
    q.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        return {"kiem": lenh_kiem, "chay": lenh_chay, "ket-qua": lenh_ket_qua}[args.lenh](args)
    except KhongDoDuoc as e:
        print(f"⚪ Không đo được: {e}", file=sys.stderr)
        return 2
    except (TuChoi, BPS.TuChoi) as e:
        print(f"✗ Từ chối: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
