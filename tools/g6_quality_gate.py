#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HỢP ĐỒNG CHẤT LƯỢNG CỔNG G6 — script phân tích ↔ SAP ĐÃ KHOÁ (PHA R LÔ R1, 15/08/2026).

VÌ SAO CÓ — G6 là cổng DUY NHẤT (11 cổng) chưa có lớp quality-gate, trong khi nó
đứng đúng chỗ selective-reporting và HARKing sinh sống: script phân tích lệch SAP
một li là kết quả G6.5/G7 lệch một dặm mà chữ ký G4 không bảo vệ được (chữ ký chỉ
khoá TOÀN VẸN của SAP, không khoá việc script có LÀM THEO SAP hay không).

PHẠM VI THẬT — đối chiếu ba bên: `G6_A7_ANALYSIS_SCRIPTS_<study>.md` (script sinh)
↔ `G4_A5_SAP_FINAL_<study>.md` (SAP đã khoá) ↔ ledger/checkpoint. KHÔNG chấm chất
lượng thống kê học (việc của thống kê viên), KHÔNG phải cổng ký — nhãn đạt là
`PASS_G6_SCRIPTS_CONFIRMED`: lời TỰ KHAI CÓ DẤU VẾT như G3, không phải bảo đảm
mật mã như G2/G4/G5/G8/G9/G10.

4 trạng thái rời nghĩa (khuôn G3):
  BLOCKED                            — lệch SAP/thiếu artifact: phải sửa trước khi đi tiếp
  DRAFT_NEEDS_HUMAN_PARAMETERS       — SAP còn placeholder (seed/alpha) → kết quả ĐÚNG
                                       của lần chạy tự động đầu, không phải lỗi
  READY_FOR_STATISTICIAN_REVIEW      — máy đối chiếu xong, chờ thống kê viên xác nhận
  PASS_G6_SCRIPTS_CONFIRMED          — đã có xác nhận người trong study_meta.gate_params.G6

Dùng:  python3 tools/g6_quality_gate.py --study <mã>     (tự chạy cuối run_g6_auto)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
VERSION = "1.0.0"


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _sec(sap: str, so: int) -> str:
    """Cắt nguyên văn một §N của SAP (tới § kế tiếp)."""
    m = re.search(rf"###\s*§{so}\b.*?(?=###\s*§|\Z)", sap, re.S)
    return m.group(0) if m else ""


def evaluate_study(study: str, write: bool = True) -> dict:
    thu_muc = EXPORTS / study
    ket: list[dict] = []
    trang_thai = "READY_FOR_STATISTICIAN_REVIEW"

    def add(ma: str, dat: bool | None, chi_tiet: str, chan: bool = False) -> None:
        ket.append({"id": ma, "pass": dat, "detail": chi_tiet, "blocking": chan})

    art_p = thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md"
    sap_p = thu_muc / f"G4_A5_SAP_FINAL_{study}.md"
    cp_p = thu_muc / "G6_checkpoint.json"

    # ── G6-AUTO-00: đủ bộ ba đầu vào ─────────────────────────────────────────
    thieu = [p.name for p in (art_p, sap_p, cp_p) if not p.exists()]
    if thieu:
        add("G6-AUTO-00", False, f"thiếu {', '.join(thieu)} — không có gì để đối chiếu", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    art = art_p.read_text(encoding="utf-8", errors="replace")
    # Script thân nằm ở exports/<study>/scripts/*.R|*.py — artifact md chỉ là bìa.
    # Bản đầu chỉ đọc md nên báo «không set.seed» trong khi template R có
    # `SEED <- 2026` (bắt được khi chạy trên đề tài sống 15/08 — bug #2 của gate).
    for sf in sorted((thu_muc / "scripts").glob("*")):
        if sf.suffix in (".R", ".py", ".r"):
            art += "\n" + sf.read_text(encoding="utf-8", errors="replace")
    sap = sap_p.read_text(encoding="utf-8", errors="replace")
    try:
        cp = json.loads(cp_p.read_text(encoding="utf-8"))
    except ValueError as exc:
        add("G6-AUTO-00", False, f"G6_checkpoint hỏng: {exc}", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    add("G6-AUTO-00", True, "artifact + SAP + checkpoint đọc được")

    # ── G6-AUTO-01: SAP phải ĐÃ KHOÁ trước khi sinh script ───────────────────
    # Nguồn mạnh nhất: ledger thật qua gate_contract; máy chưa cấu hình khoá thì
    # hạ mức khẳng định xuống checkpoint g4_was_locked và NÓI RÕ nguồn bằng chứng
    # (không im lặng nhập nhằng hai mức bảo đảm — bài học nhãn 'shared vs role').
    bang_chung_g4 = None
    try:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("gc_g6", HERE / "gate_contract.py")
        gc = ilu.module_from_spec(spec)
        sys.modules["gc_g6"] = gc
        spec.loader.exec_module(gc)
        # ledger_approved đòi (study, gate, artifact_path) — ràng chữ ký vào ĐÚNG
        # file SAP hiện tại; bản đầu gọi thiếu tham số → TypeError bị nuốt và cổng
        # luôn rơi fallback (bắt được khi chạy trên đề tài sống 15/08).
        if gc.ledger_approved(study, "G4", str(sap_p)):
            bang_chung_g4 = "ledger (chữ ký thật)"
    except Exception:  # noqa: BLE001 — thiếu khoá/ledger không được giết cổng chấm
        bang_chung_g4 = None
    if bang_chung_g4 is None and cp.get("g4_was_locked"):
        bang_chung_g4 = "checkpoint g4_was_locked (TỰ KHAI — chưa đối chiếu ledger)"
    if bang_chung_g4:
        add("G6-AUTO-01", True, f"G4 đã khoá trước khi sinh script — nguồn: {bang_chung_g4}")
    else:
        add("G6-AUTO-01", False,
            "KHÔNG có bằng chứng G4 đã khoá — script phân tích sinh trước khi SAP khoá "
            "là mở cửa HARKing", True)

    # ── G6-AUTO-02: SEED script ↔ SAP §10 ────────────────────────────────────
    sap10 = _sec(sap, 10)
    seed_sap = re.search(r"set\.seed\((\d+)\)|seed\D{0,12}(\d{3,6})", sap10)
    seed_art = re.findall(r"set\.seed\((\d+)\)", art) + re.findall(r"SEED\s*<-\s*(\d+)", art)
    if "[CẦN" in sap10 and not seed_sap:
        add("G6-AUTO-02", None, "SAP §10 seed còn [CẦN BÁC SĨ ẤN ĐỊNH] — chưa đối chiếu được")
        trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    elif seed_sap:
        so = next(g for g in seed_sap.groups() if g)
        if seed_art and all(s == so for s in seed_art):
            add("G6-AUTO-02", True, f"seed {so} khớp SAP ở {len(seed_art)} chỗ trong script")
        elif not seed_art:
            add("G6-AUTO-02", False, f"SAP ấn định seed {so} nhưng script KHÔNG set.seed", True)
        else:
            add("G6-AUTO-02", False,
                f"seed LỆCH: SAP={so}, script={sorted(set(seed_art))} — kết quả sẽ không tái lập "
                "đúng SAP", True)
    else:
        add("G6-AUTO-02", None, "SAP §10 không đọc được seed — cần thống kê viên xem")

    # ── G6-AUTO-03: ALPHA script ↔ SAP §12 ───────────────────────────────────
    sap12 = _sec(sap, 12)
    a_sap = re.search(r"alpha\D{0,15}0[\.,](\d+)", _bo_dau(sap12))
    a_art = set(re.findall(r"alpha\s*(?:=|:|<-)\s*0[\.,](\d+)", _bo_dau(art)))
    if "[can" in _bo_dau(sap12) and not a_sap:
        add("G6-AUTO-03", None, "SAP §12 alpha còn placeholder — chưa đối chiếu được")
        trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    elif a_sap and a_art and a_sap.group(1) not in a_art:
        add("G6-AUTO-03", False,
            f"alpha LỆCH: SAP=0.{a_sap.group(1)}, script=0.{'/0.'.join(sorted(a_art))}", True)
    elif a_sap:
        add("G6-AUTO-03", True, f"alpha 0.{a_sap.group(1)} nhất quán"
            + ("" if a_art else " (script không hardcode alpha — dùng mặc định, chấp nhận)"))
    else:
        add("G6-AUTO-03", None, "không đọc được alpha từ SAP §12 — cần người xem")

    # ── G6-AUTO-04: KẾT CỤC SAP §2 phải có mặt trong script (chống bỏ kết cục) ──
    sap2 = _bo_dau(_sec(sap, 2))
    art_bd = _bo_dau(art)
    ten_kc = set()
    for dong in sap2.splitlines():
        if any(k in dong for k in ("chinh", "phu", "primary", "secondary")):
            ten_kc.update(re.findall(r"`([a-z0-9_]{3,})`|\*\*([a-z0-9_ ]{4,30})\*\*", dong))
    ten_kc = {next(x for x in t if x).strip() for t in ten_kc if any(t)}
    if not ten_kc:
        add("G6-AUTO-04", None, "SAP §2 không rút được tên kết cục máy-đọc-được — "
                                "thống kê viên đối chiếu tay (không suy đoán hộ)")
    else:
        vang = [t for t in ten_kc if _bo_dau(t) not in art_bd]
        if vang:
            add("G6-AUTO-04", False,
                f"kết cục trong SAP VẮNG MẶT trong script: {sorted(vang)[:4]} — "
                "mầm selective reporting", True)
        else:
            add("G6-AUTO-04", True, f"{len(ten_kc)} kết cục SAP §2 đều có mặt trong script")

    # ── G6-AUTO-05: SUBGROUP script ⊆ SAP §7 (chống HARKing) ────────────────
    sap7 = _bo_dau(_sec(sap, 7))
    khoi_sub = re.findall(r"(?:PHÂN TÍCH NHÓM CON|subgroup)[^\n]*\n(?:#[^\n]*\n)*", art, re.I)
    sub_art = set(re.findall(r"subgroup[_ ]?(?:var|bien)?\s*(?:=|:|<-)\s*['\"]?([a-z0-9_]{3,})",
                             _bo_dau(art)))
    la_posthoc = "post-hoc" in _bo_dau(art) or "post hoc" in _bo_dau(art)
    ngoai = [s for s in sub_art if s not in sap7]
    if ngoai and not la_posthoc:
        add("G6-AUTO-05", False,
            f"script phân tích nhóm con NGOÀI SAP §7 mà không dán nhãn post-hoc: "
            f"{sorted(ngoai)[:4]} — HARKing", True)
    elif ngoai:
        add("G6-AUTO-05", True, f"{len(ngoai)} nhóm con ngoài SAP nhưng ĐÃ dán nhãn post-hoc "
                                "— hợp lệ, phải giữ nhãn tới tận bản thảo")
    else:
        add("G6-AUTO-05", True,
            f"nhóm con trong script ({len(sub_art)}) đều thuộc SAP §7" if sub_art
            else "script không có phân tích nhóm con — khớp khi SAP §7 trống")
    _ = khoi_sub  # giữ cho mở rộng sau; không dùng để quyết định

    # ── G6-AUTO-06: kỷ luật DATA LOCK khi ĐÃ có kết quả chạy thật ───────────
    kq = sorted(thu_muc.glob("*KET_QUA*")) + sorted(thu_muc.glob("*RESULTS*")) \
        + sorted(thu_muc.glob("stats_output*"))
    g5cp = thu_muc / "G5_checkpoint.json"
    if not kq:
        add("G6-AUTO-06", True, "chưa có file kết quả chạy thật — chưa áp kiểm thứ tự khoá "
                                "(script viết TRƯỚC khoá dữ liệu là đúng tiền đăng ký)")
    elif not g5cp.exists():
        add("G6-AUTO-06", False,
            f"ĐÃ có kết quả ({kq[0].name}) mà KHÔNG có G5_checkpoint — chạy phân tích "
            "trước khoá dữ liệu", True)
    else:
        t5 = datetime.fromtimestamp(g5cp.stat().st_mtime)
        sau = [k.name for k in kq if datetime.fromtimestamp(k.stat().st_mtime) < t5]
        if sau:
            add("G6-AUTO-06", False,
                f"kết quả có TRƯỚC thời điểm khoá G5: {sau[:3]} — vi phạm DATA LOCK", True)
        else:
            add("G6-AUTO-06", True, f"{len(kq)} file kết quả đều SAU khoá G5")

    # ── G6-HUMAN-01: thống kê viên xác nhận (study_meta.gate_params.G6) ─────
    meta_p = thu_muc / "study_meta.json"
    g6p = {}
    if meta_p.exists():
        try:
            g6p = (json.loads(meta_p.read_text(encoding="utf-8"))
                   .get("gate_params", {}).get("G6", {}) or {})
        except ValueError:
            pass
    nguoi_ok = bool(g6p.get("scripts_match_sap_confirmed")) and \
        g6p.get("reviewed_by_role") in ("STATISTICIAN", "PI") and g6p.get("reviewed_at")
    add("G6-HUMAN-01", bool(nguoi_ok) if g6p else None,
        ("thống kê viên/PI đã xác nhận script khớp SAP "
         f"({g6p.get('reviewed_by_role')} @ {g6p.get('reviewed_at')})") if nguoi_ok else
        "chờ xác nhận người: study_meta.json → gate_params.G6 "
        "{scripts_match_sap_confirmed, reviewed_by_role: STATISTICIAN|PI, reviewed_at}")

    if any(k["blocking"] and k["pass"] is False for k in ket):
        trang_thai = "BLOCKED"
    elif trang_thai != "DRAFT_NEEDS_HUMAN_PARAMETERS" and nguoi_ok:
        trang_thai = "PASS_G6_SCRIPTS_CONFIRMED"
    return _finish(study, thu_muc, trang_thai, ket, write)


def _finish(study: str, thu_muc: Path, trang_thai: str, ket: list[dict],
            write: bool) -> dict:
    bao = {"gate": "G6_QUALITY", "version": VERSION, "study": study,
           "status": trang_thai, "checks": ket,
           "generated_at": datetime.now().isoformat(timespec="seconds"),
           "disclaimer": "Tự khai có dấu vết — KHÔNG phải cổng ký; không thay "
                         "thống kê viên. Cần bác sĩ kiểm chứng."}
    if write and thu_muc.exists():
        (thu_muc / "G6_QUALITY_REPORT.json").write_text(
            json.dumps(bao, ensure_ascii=False, indent=1), encoding="utf-8")
        dong = [f"# G6 QUALITY — {study}: **{trang_thai}**", ""]
        for k in ket:
            dau = {True: "✅", False: "❌", None: "◌"}[k["pass"]]
            dong.append(f"- {dau} `{k['id']}`{' 🔴' if k['blocking'] and k['pass'] is False else ''}: {k['detail']}")
        dong.append(f"\n> {bao['disclaimer']}")
        (thu_muc / "G6_QUALITY_REPORT.md").write_text("\n".join(dong) + "\n",
                                                      encoding="utf-8")
        cpp = thu_muc / "G6_checkpoint.json"
        if cpp.exists():
            try:
                cp = json.loads(cpp.read_text(encoding="utf-8"))
                cp["quality_gate"] = {"status": trang_thai, "version": VERSION,
                                      "at": bao["generated_at"]}
                cpp.write_text(json.dumps(cp, ensure_ascii=False, indent=1),
                               encoding="utf-8")
            except ValueError:
                pass
    return bao


def main() -> int:
    ap = argparse.ArgumentParser(description="Hợp đồng chất lượng cổng G6")
    ap.add_argument("--study", required=True)
    a = ap.parse_args()
    bao = evaluate_study(a.study)
    print(f"G6 QUALITY [{a.study}]: {bao['status']}")
    for k in bao["checks"]:
        dau = {True: "✅", False: "❌", None: "◌"}[k["pass"]]
        print(f"  {dau} {k['id']}: {k['detail'][:110]}")
    print("Cần bác sĩ kiểm chứng.")
    return {"BLOCKED": 3, "DRAFT_NEEDS_HUMAN_PARAMETERS": 2,
            "READY_FOR_STATISTICIAN_REVIEW": 2,
            "PASS_G6_SCRIPTS_CONFIRMED": 0}[bao["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
