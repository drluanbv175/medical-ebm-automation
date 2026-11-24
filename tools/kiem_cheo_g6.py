#!/usr/bin/env python3
"""Kiểm chéo G6 bằng phần mềm thứ hai — MỘT lệnh cho cả IBM SPSS lẫn R.

Bác sĩ giao 14/11/2026 (gói tự động hoá A–D): «sau khi gộp hãy thực hiện A, B, C và D».

  A. `chay`        — một lệnh chạy trọn chuỗi của CẢ HAI cầu nối rồi ghi MỘT báo cáo chung
                     `exports/<mã>/G6_kiem_cheo.json` + `.md`:
                     SPSS: xuat-sav (chỉ khi .sav chưa có/không khớp dữ liệu khoá) → cu-phap → chay → doi-chieu
                     R:    cu-phap → chay → doi-chieu
                     Máy thiếu một phần mềm ⇒ phần đó «⚪ không đo được», phần kia vẫn chạy.
  B/D. `trang-thai` — đọc nhanh, KHÔNG chạy phần mềm nào: chưa kiểm chéo · CŨ (kết quả Python hoặc dữ liệu khoá đổi
                     sau lượt kiểm chéo) · khớp · lệch nhỏ · LỆCH · lỗi. Hòm việc (repo gốc tools/tu_de_xuat_viec.py),
                     study_readiness.py và đài kiểm soát (audit_research_gates.py) đọc qua hàm `trang_thai`.
  C. Agent `dieu-phoi-g6` gọi `chay` sau bước phân tích của `phan-tich-thong-ke`.
  E. (15/11/2026 — bác sĩ: «chú ý là phần mềm RStudio» và «đúng phần mềm SPSS đang chạy») `chay --trong-ung-dung` MỞ
     cú pháp trong giao diện IBM SPSS Statistics (cùng bộ cài với cầu nối) và script trong RStudio để bác sĩ tự bấm
     Run > All / Source và xem bảng; xong `nhan-ket-qua` đọc kết quả hai phần mềm vừa ghi, đối chiếu và ghi báo cáo
     chung như `chay`.

RANH GIỚI: kiểm chéo là TƯ VẤN kỹ thuật — không đổi trạng thái cổng G6, không thay G6-HUMAN-01 (thống kê viên), không
ký, không ghi study_meta/approval_ledger. Phân tích chính vẫn là run_stats_analysis.py.

Mã thoát của `chay`: 0 khớp/lệch nhỏ · 1 LỆCH hoặc một bước lỗi · 2 không đo được (không có phần mềm, chưa có kết quả
Python) · 3 từ chối. `trang-thai`: 0 khớp/lệch nhỏ/không áp dụng · 1 LỆCH/lỗi · 2 chưa chạy/cũ/không đo được.
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows cp1252 (BH55/R4)
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
EXPORTS = BASE / "exports"
TEP_JSON, TEP_MD = "G6_kiem_cheo.json", "G6_kiem_cheo.md"  # tên của gate G6 (tương thích ngược)


def tep_kiem_cheo(gate: str = "G6") -> tuple[str, str]:
    """F3 (14/11/2026): tên tệp kết quả kiểm chéo THEO GATE — chạy trọn SAP (chay_sap_g6.py) kiểm chéo nhiều phân tích
    (G6, G6_<mã>…); tên cố định cũ để lượt sau ghi đè kết quả lượt trước."""
    return f"{gate}_kiem_cheo.json", f"{gate}_kiem_cheo.md"
CAN_KIEM = "Cần bác sĩ kiểm chứng."

KHONG_AP_DUNG, CHUA_CHAY, CU = "KHONG_AP_DUNG", "CHUA_CHAY", "CU"
CHO_UNG_DUNG = "CHO_CHAY_TRONG_UNG_DUNG"
TEN_HIEN = {"spss": "SPSS", "r": "R / RStudio"}  # tên hiển thị — khoá máy đọc vẫn là «spss»/«r»
KHOP, LECH_NHO, LECH, LOI, TU_CHOI, KHONG_DO_DUOC = "KHOP", "LECH_NHO", "LECH", "LOI", "TU_CHOI", "KHONG_DO_DUOC"
NHAN = {
    KHONG_AP_DUNG: "⚪ không áp dụng (chưa có kết quả Python G6)",
    CHUA_CHAY: "🛎 chưa kiểm chéo",
    CU: "🛎 CŨ — kết quả Python hoặc dữ liệu khoá đổi sau lượt kiểm chéo",
    KHOP: "✓ khớp",
    LECH_NHO: "⚠ lệch nhỏ (khác phương pháp đã biết)",
    LECH: "✗ LỆCH",
    LOI: "✗ một bước kiểm chéo lỗi",
    TU_CHOI: "⛔ từ chối (dữ liệu/đặc tả không khớp)",
    KHONG_DO_DUOC: "⚪ không đo được (máy thiếu SPSS/R)",
}
#: Trạng thái cần người xử lý (đếm là việc còn treo ở study_readiness / hòm việc).
CAN_XU_LY = frozenset({CHUA_CHAY, CU, LECH, LOI, TU_CHOI})


def _doc_json(p: Path) -> dict:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


def _sha256(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def thu_muc_de_tai(study: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", study or ""):
        raise ValueError(f"mã đề tài không hợp lệ: {study!r}")
    return EXPORTS / study


def van_tay(d: Path, gate: str = "G6") -> dict | None:
    """Dấu vân tay của ĐẦU VÀO kiểm chéo: tóm tắt Python G6 + SHA-256 dữ liệu khoá mà nó ghi. None ⇒ chưa có G6."""
    tom_p = d / f"{gate}_analysis_summary.json"
    if not tom_p.is_file():
        return None
    return {
        "sha256_tom_tat": _sha256(tom_p),
        "sha256_du_lieu": (_doc_json(tom_p).get("data_lock") or {}).get("sha256"),
    }


def _trang_thai_tu_dem(dem: dict | None) -> str:
    dem = dem or {}
    if dem.get("lech"):
        return LECH
    if dem.get("lech_nho"):
        return LECH_NHO
    if dem.get("khop"):
        return KHOP
    return KHONG_DO_DUOC


def tong_hop(phan_mem: dict[str, dict]) -> str:
    """Trạng thái chung: LỆCH > lỗi > từ chối > lệch nhỏ > khớp; mọi phần mềm «không đo được» ⇒ không đo được."""
    tt = [x.get("trang_thai") for x in phan_mem.values()]
    for muc in (LECH, LOI, TU_CHOI, LECH_NHO, KHOP):
        if muc in tt:
            return muc
    return KHONG_DO_DUOC


def trang_thai(d: Path, gate: str = "G6") -> dict:
    """Đọc nhanh (chỉ đọc tệp, không chạy SPSS/R): {trang_thai, nhan, ly_do, luc, phan_mem}."""
    vt = van_tay(d, gate)
    if vt is None:
        return {"trang_thai": KHONG_AP_DUNG, "nhan": NHAN[KHONG_AP_DUNG], "ly_do": "chưa có kết quả Python G6"}
    kc = _doc_json(d / tep_kiem_cheo(gate)[0])
    if not kc:
        return {"trang_thai": CHUA_CHAY, "nhan": NHAN[CHUA_CHAY], "ly_do": "có kết quả Python G6 nhưng chưa kiểm chéo"}
    if kc.get("van_tay") != vt:
        return {
            "trang_thai": CU,
            "nhan": NHAN[CU],
            "ly_do": f"kết quả Python/dữ liệu khoá đổi sau lượt kiểm chéo {kc.get('luc', '?')}",
            "luc": kc.get("luc"),
        }
    tt = kc.get("trang_thai") or KHONG_DO_DUOC
    pm = {k: v.get("trang_thai") for k, v in (kc.get("phan_mem") or {}).items()}
    return {
        "trang_thai": tt,
        "nhan": NHAN.get(tt, tt),
        "ly_do": " · ".join(f"{k.upper()}: {NHAN.get(v, v)}" for k, v in pm.items()),
        "luc": kc.get("luc"),
        "phan_mem": pm,
    }


def trang_thai_tat_ca(exports: Path | None = None, gate: str = "G6") -> list[tuple[str, dict]]:
    """Mọi đề tài trong exports/ có kết quả Python G6."""
    goc = Path(exports) if exports else EXPORTS
    if not goc.is_dir():
        return []
    ra = []
    for d in sorted(p for p in goc.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        if (d / f"{gate}_analysis_summary.json").is_file():
            ra.append((d.name, trang_thai(d, gate)))
    return ra


# ───────────────────────────── A. chạy cả hai cầu nối ─────────────────────────────


def _tt_tu_ma(ma: int) -> str:
    return {2: KHONG_DO_DUOC, 3: TU_CHOI}.get(ma, LOI)


def _chay_spss(study: str, gate: str, d: Path, vt: dict, args, che_do: str = "nen") -> dict:
    """che_do: «nen» chạy trọn ở chế độ nền · «mo» mở cú pháp trong giao diện SPSS · «nhan» đọc kết quả lượt
    giao diện."""
    sys.path.insert(0, str(TOOLS))
    import cau_noi_spss as C  # noqa: PLC0415

    try:
        py = C.tim_spss()
    except C.KhongDoDuoc as e:
        return {"trang_thai": KHONG_DO_DUOC, "ly_do": str(e)}
    buoc: list[list] = []
    if che_do == "nhan":
        nk = ["nhan-ket-qua", "--study", study, "--gate", gate] + (["--khong-r"] if args.khong_r_tham_chieu else [])
        ma = C.main(nk)
        buoc.append(["nhan-ket-qua", ma])
        if ma != 0:
            return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": "nhan-ket-qua không thành công"}
        return _doi_chieu_spss(C, study, gate, d, buoc)
    man = _doc_json(d / "spss" / f"{study}_khoa.sav.manifest.json")
    sav_ok = man.get("sav_da_tao") and Path(man.get("sav") or "").is_file()
    if not sav_ok or man.get("sha256_nguon") != vt.get("sha256_du_lieu"):
        ma = C.main(["xuat-sav", "--study", study])
        buoc.append(["xuat-sav", ma])
        if ma != 0:
            return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": "xuat-sav không thành công", "python": str(py)}
    cp = ["cu-phap", "--study", study, "--gate", gate]
    for x in args.thang_do or []:
        cp += ["--thang-do", x]
    cp += ["--khong-hon-hop"] if args.khong_hon_hop else []
    cp += ["--khong-trong-so"] if args.khong_trong_so else []
    ch = ["chay", "--study", study, "--gate", gate, "--thoi-han", str(args.thoi_han)]
    ch += ["--khong-r"] if args.khong_r_tham_chieu else []
    ch += ["--trong-spss"] if che_do == "mo" else []
    for lenh in (cp, ch):
        ma = C.main(lenh)
        buoc.append([lenh[0], ma])
        if ma != 0:
            return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": f"{lenh[0]} không thành công"}
    if che_do == "mo":
        return {"trang_thai": CHO_UNG_DUNG, "buoc": buoc,
                "ly_do": "đã mở trong giao diện IBM SPSS Statistics — Run > All"}
    return _doi_chieu_spss(C, study, gate, d, buoc)


def _doi_chieu_spss(C, study: str, gate: str, d: Path, buoc: list) -> dict:
    ma = C.main(["doi-chieu", "--study", study, "--gate", gate])
    buoc.append(["doi-chieu", ma])
    dc = _doc_json(d / f"{gate}_spss_doi_chieu.json")
    if not dc:
        return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": "doi-chieu không ra báo cáo"}
    return {
        "trang_thai": _trang_thai_tu_dem(dc.get("dem")),
        "dem": dc.get("dem"),
        "buoc": buoc,
        "phien_ban": dc.get("spss_phien_ban"),
        "chay_bang": _doc_json(d / f"{gate}_spss_ket_qua.json").get("chay_bang"),
        "r_tham_chieu": dc.get("r_phien_ban"),
        "bao_cao": f"{gate}_spss_doi_chieu.md",
    }


def _chay_r(study: str, gate: str, d: Path, args, che_do: str = "nen") -> dict:
    """che_do: «nen» Rscript --vanilla · «mo» mở script trong RStudio · «nhan» đọc kết quả lượt RStudio."""
    sys.path.insert(0, str(TOOLS))
    try:
        import cau_noi_r as R  # noqa: PLC0415
    except ImportError as e:
        return {"trang_thai": KHONG_DO_DUOC, "ly_do": f"chưa có tools/cau_noi_r.py ({e})"}
    try:
        R.tim_r()
    except R.KhongDoDuoc as e:
        return {"trang_thai": KHONG_DO_DUOC, "ly_do": str(e)}
    buoc: list[list] = []
    if che_do == "nhan":
        ds_lenh = [["nhan-ket-qua", "--study", study, "--gate", gate]]
    else:
        ds_lenh = [["cu-phap", "--study", study, "--gate", gate],
                   ["chay", "--study", study, "--gate", gate, "--thoi-han", str(args.thoi_han)]
                   + (["--trong-rstudio"] if che_do == "mo" else [])]  # fmt: skip
    for lenh in ds_lenh:
        ma = R.main(lenh)
        buoc.append([lenh[0], ma])
        if ma != 0:
            return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": f"{lenh[0]} không thành công"}
    if che_do == "mo":
        return {"trang_thai": CHO_UNG_DUNG, "buoc": buoc, "ly_do": "đã mở trong RStudio — bấm Source"}
    ma = R.main(["doi-chieu", "--study", study, "--gate", gate])
    buoc.append(["doi-chieu", ma])
    dc = _doc_json(d / f"{gate}_r_doi_chieu.json")
    if not dc:
        return {"trang_thai": _tt_tu_ma(ma), "buoc": buoc, "ly_do": "doi-chieu không ra báo cáo"}
    return {
        "trang_thai": _trang_thai_tu_dem(dc.get("dem")),
        "dem": dc.get("dem"),
        "buoc": buoc,
        "phien_ban": dc.get("r_phien_ban"),
        "chay_bang": _doc_json(d / f"{gate}_r_ket_qua.json").get("chay_bang"),
        "bao_cao": f"{gate}_r_doi_chieu.md",
    }


def _md(study: str, ket: dict) -> str:
    dong = [
        f"# Kiểm chéo G6 bằng phần mềm thứ hai — {study}",
        "",
        f"{ket['luc']} · trạng thái chung: **{NHAN.get(ket['trang_thai'], ket['trang_thai'])}**",
        "",
        f"Dấu vân tay đầu vào: tóm tắt Python `{(ket['van_tay'] or {}).get('sha256_tom_tat', '?')[:16]}…` · dữ liệu "
        f"khoá `{str((ket['van_tay'] or {}).get('sha256_du_lieu') or '?')[:16]}…` — đổi một trong hai ⇒ kết quả "
        "này «CŨ».",
        "",
        "| Phần mềm | Trạng thái | Khớp | Lệch nhỏ | Lệch | Không so được | Phiên bản | Chạy bằng | Chi tiết |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ten, x in ket["phan_mem"].items():
        dem = x.get("dem") or {}
        dong.append(
            f"| {TEN_HIEN.get(ten, ten.upper())} | {NHAN.get(x['trang_thai'], x['trang_thai'])} | "
            f"{dem.get('khop', '—')} | "
            f"{dem.get('lech_nho', '—')} | {dem.get('lech', '—')} | {dem.get('khong_so_duoc', '—')} | "
            f"{x.get('phien_ban') or '—'} | {x.get('chay_bang') or '—'} | {x.get('bao_cao') or x.get('ly_do') or '—'} |"
        )
    dong += [
        "",
        "Đọc: ✓ khớp ⇒ phương pháp có thể ghi «kết quả được tái lập độc lập bằng …»; ⚠ lệch nhỏ ⇒ chép nguyên ghi chú, "
        "thống kê viên chọn cách báo cáo theo SAP; ✗ LỆCH / lỗi ⇒ tìm nguyên nhân TRƯỚC khi dùng số — KHÔNG sửa Python "
        "cho "
        "khớp phần mềm khác hay ngược lại; ⚪ không đo được KHÔNG phải khớp.",
        "",
        "Kiểm chéo là TƯ VẤN kỹ thuật — không đổi trạng thái cổng G6, không thay thống kê viên (G6-HUMAN-01).",
        "",
        CAN_KIEM,
        "",
    ]
    return "\n".join(dong)


def _chi_mo_ta(d: Path, gate: str) -> str | None:
    """None = có kết cục/thời gian (kiểm chéo đầy đủ) · "ty_le" = chỉ mô tả, có tỷ lệ Wilson Bảng 1b (cầu nối R
    22/11/2026 và SPSS 23/11/2026 đều có bản đối chiếu) · "khong_co_ban_kiem_cheo" = chỉ mô tả, không có phép nào hai
    cầu nối tái lập được."""
    tom = _doc_json(d / f"{gate}_analysis_summary.json")
    dt = tom.get("dac_ta_phan_tich") or {}
    if dt.get("outcome") or dt.get("time"):
        return None
    return "ty_le" if (dt.get("ty_le") or tom.get("ty_le")) else "khong_co_ban_kiem_cheo"


def lenh_chay(args) -> int:
    d = thu_muc_de_tai(args.study)
    vt = van_tay(d, args.gate)
    if vt is None:
        print(f"⚪ chưa có {args.gate}_analysis_summary.json — chạy run_stats_analysis.py (phân tích chính) trước")
        return 2
    mo_ta = _chi_mo_ta(d, args.gate)
    if mo_ta == "khong_co_ban_kiem_cheo":
        # F3 (14/11/2026): lượt chỉ mô tả KHÔNG có tỷ lệ Wilson — hai cầu nối chưa có bản kiểm chéo cho dạng này; ghi rõ
        # «không áp dụng» kèm lý do (trước đây báo «từ chối/lỗi» như thể phân tích hỏng).
        ket = {"study": args.study, "gate": args.gate, "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
               "van_tay": vt, "phan_mem": {}, "trang_thai": KHONG_AP_DUNG,
               "ly_do": "phân tích chỉ mô tả (không có kết cục/thời gian/tỷ lệ Wilson) — chưa có bản kiểm chéo SPSS/R",
               "disclaimer": CAN_KIEM}  # fmt: skip
        tj, tm = tep_kiem_cheo(args.gate)
        (d / tj).write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        (d / tm).write_text(_md(args.study, ket), encoding="utf-8", newline="\n")
        print(f"⚪ {args.gate}: {ket['ly_do']}")
        return 0
    che_do = "mo" if getattr(args, "trong_ung_dung", False) else "nen"
    phan_mem: dict[str, dict] = {}
    if args.chi in (None, "spss"):
        print("\n══════ IBM SPSS Statistics" + (" (mở giao diện)" if che_do == "mo" else " (nền)") + " ══════")
        phan_mem["spss"] = _chay_spss(args.study, args.gate, d, vt, args, che_do)
    if args.chi in (None, "r"):
        nhan_r = "RStudio (mở script)" if che_do == "mo" else "R — Rscript nền, cùng R với RStudio"
        print(f"\n══════ {nhan_r} ══════")
        phan_mem["r"] = _chay_r(args.study, args.gate, d, args, che_do)
    if che_do == "mo":
        mo = [k for k, x in phan_mem.items() if x["trang_thai"] == CHO_UNG_DUNG]
        print(f"\n══════ ĐÃ MỞ: {', '.join(TEN_HIEN[k] for k in mo) or 'không phần mềm nào'} ══════")
        if "spss" in mo:
            print("  • IBM SPSS Statistics: menu Run > All (bảng hiện ở cửa sổ Viewer).")
        if "r" in mo:
            print("  • RStudio: bấm «Source» (⇧⌘S) — kết quả hiện ở Console.")
        for k, x in phan_mem.items():
            if x["trang_thai"] != CHO_UNG_DUNG:
                print(f"  ⚪ {TEN_HIEN[k]}: {NHAN.get(x['trang_thai'], x['trang_thai'])} — {x.get('ly_do') or ''}")
        print(f"  Xong: python3 tools/kiem_cheo_g6.py nhan-ket-qua --study {args.study} --gate {args.gate}"
              + (f" --chi {args.chi}" if args.chi else "") + f"\n{CAN_KIEM}")  # fmt: skip
        return 0 if mo and len(mo) == len(phan_mem) else 2
    return _ghi_tong_hop(args, d, vt, phan_mem)


def lenh_nhan_ket_qua(args) -> int:
    """Sau khi bác sĩ chạy xong trong SPSS / RStudio: đọc kết quả, đối chiếu với Python, ghi báo cáo chung như
    `chay`."""
    d = thu_muc_de_tai(args.study)
    vt = van_tay(d, args.gate)
    if vt is None:
        print(f"⚪ chưa có {args.gate}_analysis_summary.json — chạy run_stats_analysis.py (phân tích chính) trước")
        return 2
    phan_mem: dict[str, dict] = {}
    if args.chi in (None, "spss"):
        print("\n══════ IBM SPSS Statistics (kết quả lượt giao diện) ══════")
        phan_mem["spss"] = _chay_spss(args.study, args.gate, d, vt, args, "nhan")
    if args.chi in (None, "r"):
        print("\n══════ RStudio (kết quả lượt Source) ══════")
        phan_mem["r"] = _chay_r(args.study, args.gate, d, args, "nhan")
    return _ghi_tong_hop(args, d, vt, phan_mem)


def _ghi_tong_hop(args, d: Path, vt: dict, phan_mem: dict[str, dict]) -> int:
    ket = {
        "study": args.study,
        "gate": args.gate,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "van_tay": vt,
        "phan_mem": phan_mem,
        "trang_thai": tong_hop(phan_mem),
        "disclaimer": CAN_KIEM,
    }
    if van_tay(d, args.gate) != vt:  # tóm tắt Python bị ghi lại GIỮA lượt — kết quả không còn gắn với đầu vào nào
        ket["trang_thai"] = LOI
        ket["canh_bao"] = "kết quả Python G6 đổi trong lúc kiểm chéo — chạy lại"
    tj, tm = tep_kiem_cheo(args.gate)
    (d / tj).write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (d / tm).write_text(_md(args.study, ket), encoding="utf-8", newline="\n")
    print(f"\n══════ KIỂM CHÉO G6 — {args.study}: {NHAN.get(ket['trang_thai'], ket['trang_thai'])} ══════")
    for ten, x in phan_mem.items():
        print(
            f"  {TEN_HIEN.get(ten, ten.upper()):12} {NHAN.get(x['trang_thai'], x['trang_thai'])}"
            + (f" — {x['ly_do']}" if x.get("ly_do") else "")
        )
    print(f"✓ {d / tm}\n{CAN_KIEM}")
    tt = ket["trang_thai"]
    return {LECH: 1, LOI: 1, TU_CHOI: 3, KHONG_DO_DUOC: 2}.get(tt, 0)


def lenh_trang_thai(args) -> int:
    ds = (
        trang_thai_tat_ca(gate=args.gate)
        if args.tat_ca
        else [(args.study, trang_thai(thu_muc_de_tai(args.study), args.gate))]
    )
    if args.json:
        print(json.dumps({k: v for k, v in ds}, ensure_ascii=False, indent=1))
    else:
        for st, t in ds:
            print(f"{st}: {t['nhan']}" + (f" — {t['ly_do']}" if t.get("ly_do") else ""))
        if not ds:
            print("không có đề tài nào có kết quả Python G6")
    tt = {t["trang_thai"] for _, t in ds}
    if tt & {LECH, LOI, TU_CHOI}:
        return 1
    return 2 if tt & {CHUA_CHAY, CU, KHONG_DO_DUOC} else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Kiểm chéo G6 bằng IBM SPSS Statistics + R/RStudio — một lệnh. " + CAN_KIEM
    )
    sub = ap.add_subparsers(dest="lenh", required=True)
    c = sub.add_parser("chay", help="chạy trọn chuỗi SPSS + R và ghi G6_kiem_cheo.json/.md")
    c.add_argument("--study", required=True)
    c.add_argument("--gate", default="G6")
    c.add_argument("--chi", choices=["spss", "r"], help="chỉ chạy một phần mềm")
    c.add_argument("--thang-do", action="append", help="thang đo cho RELIABILITY của SPSS: «TÊN:mục1,…» (lặp được)")
    c.add_argument("--khong-hon-hop", action="store_true", help="SPSS: bỏ mô hình hỗn hợp (GENLINMIXED)")
    c.add_argument("--khong-trong-so", action="store_true", help="SPSS: bỏ Complex Samples có trọng số")
    c.add_argument("--khong-r-tham-chieu", action="store_true", help="SPSS: không chạy R làm tham chiếu khối bổ sung")
    c.add_argument("--thoi-han", type=int, default=1200, help="giây cho mỗi lượt SPSS/R (mặc định 1200)")
    c.add_argument("--trong-ung-dung", action="store_true",
                   help="MỞ trong giao diện IBM SPSS Statistics và RStudio để bác sĩ tự chạy; xong gọi nhan-ket-qua")
    nk = sub.add_parser("nhan-ket-qua", help="đọc kết quả lượt chạy trong SPSS/RStudio, đối chiếu, ghi báo cáo chung")
    nk.add_argument("--study", required=True)
    nk.add_argument("--gate", default="G6")
    nk.add_argument("--chi", choices=["spss", "r"], help="chỉ một phần mềm")
    nk.add_argument("--khong-r-tham-chieu", action="store_true", help="SPSS: không chạy R làm tham chiếu khối bổ sung")
    t = sub.add_parser("trang-thai", help="đọc nhanh trạng thái kiểm chéo (không chạy SPSS/R)")
    g = t.add_mutually_exclusive_group(required=True)
    g.add_argument("--study")
    g.add_argument("--tat-ca", action="store_true", help="mọi đề tài có kết quả Python G6")
    t.add_argument("--gate", default="G6")
    t.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        return {"chay": lenh_chay, "nhan-ket-qua": lenh_nhan_ket_qua, "trang-thai": lenh_trang_thai}[args.lenh](args)
    except ValueError as e:
        print(f"⛔ {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
