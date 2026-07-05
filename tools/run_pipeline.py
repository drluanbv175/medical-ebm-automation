#!/usr/bin/env python3
"""Nhạc trưởng TỰ ĐỘNG chuỗi cổng nghiên cứu G0→G10 — có CƠ CHẾ TỰ SỬA CHỮA.

Chỉ cần TÊN ĐỀ TÀI (+ chủ đề lần đầu) → chạy trọn G0→G10, tự:
  1. FRESHNESS GUARD: phát hiện cổng CŨ (downstream sinh trước upstream — lớp bug
     đã làm nhiễm G7 seed) và tự CHẠY LẠI theo dây chuyền để đồng bộ.
  2. VÒNG LẶP RETRY CÓ TRẦN: lỗi tạm thời (mạng/exit≠0) thử lại tối đa N lần.
  3. HARD-STOP TRUNG THỰC: chỗ cần bằng chứng đời thực (IRB/SAP ký/dữ liệu thật)
     KHÔNG bịa — cổng vẫn sinh bản DỰ THẢO, còn trạng thái KHOÁ để bác sĩ cấp.
  4. RUN REPORT: JSON + tóm tắt (cổng nào chạy/tự-sửa/lỗi + kết luận sẵn sàng G10).

BẤT BIẾN AN TOÀN:
  - KHÔNG bịa số liệu/PMID/phê duyệt (mọi remediation chỉ chạy lại script thật).
  - Retry CÓ TRẦN + tổng số lần chạy CÓ TRẦN → không vòng lặp vô hạn.
  - Cổng cứng (G2/G4/G9) và dữ liệu thật là điểm DỪNG, không tự "đạt".
  - Idempotent: chạy lại khi đã tươi → không làm gì (hội tụ).

Dùng:
  python3 tools/run_pipeline.py --study <MÃ> [--topic "<chủ đề>"] [--check-only]
                                [--max-attempts 2] [--from G0]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import pipeline_freshness as FRESH  # noqa: E402
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG: mã thoát + needs_input)

try:
    import skill_standards as SKILL  # noqa: E402  (tín hiệu bằng-chứng-đời-thực)
except Exception:  # noqa: BLE001
    SKILL = None

GATE_ORDER = [f"G{i}" for i in range(11)]  # G0..G10
DATA_GATES = {"G0", "G1", "G2", "G7"}       # cổng có thể chạm mạng (degrade được)
MAX_TOTAL_RUNS = 40                          # trần cứng chống runaway

# Cổng CỨNG (🔒) — sinh DRAFT tự động nhưng CHỜ bằng chứng đời-thực (bác sĩ ký/nộp).
# Ánh xạ tới tín hiệu real_world_signals tương ứng để BÁO TRUNG THỰC (D6): không
# để "✅ ok" (draft) bị hiểu nhầm là "đã xong thật".
HARD_GATE_SIGNAL = {
    "G2": ("irb_approved", "phê duyệt IRB thật (số + ngày)"),
    "G4": ("sap_locked", "ký + ngày khóa SAP"),
    "G5": ("db_locked", "dữ liệu thật đã khóa (KHÔNG PII)"),
    "G9": ("integrity_signed", "gói liêm chính đã ký (COI/tài trợ/AI/đóng góp)"),
}


def _script_for(gate: str) -> Path:
    if gate == "G10":
        return TOOLS / "run_g10_assemble.py"
    return TOOLS / f"run_{gate.lower()}_auto.py"


def _load_meta(out_dir: Path) -> dict:
    p = out_dir / "study_meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _existing_topic(out_dir: Path) -> Optional[str]:
    """Lấy chủ đề từ G0 checkpoint đã có (để chạy lại G0 không cần nhập lại)."""
    p = out_dir / "G0_checkpoint.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("topic")
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _load_cp(out_dir: Path, gate: str) -> dict:
    p = out_dir / f"{gate}_checkpoint.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _recover_params(gate: str, out_dir: Path, meta: dict) -> List[str]:
    """Khôi phục THAM SỐ do bác sĩ cấp cho 1 cổng khi CHẠY LẠI (tự sửa chữa).

    CỰC KỲ QUAN TRỌNG: chạy lại 1 cổng chỉ với --study sẽ MẤT tham số bác sĩ đã
    nhập (vd G3 effect-size/dropout → N tụt về 0, làm G4 từ chối). Ưu tiên
    study_meta.json['gate_params'][gate]; nếu không có, khôi phục từ checkpoint
    CŨ của chính cổng. KHÔNG bịa: chỉ dùng giá trị THẬT đã có.
    """
    # 1) study_meta ưu tiên (bác sĩ khai tường minh).
    mp = (meta.get("gate_params") or {}).get(gate) or {}

    args: List[str] = []
    if gate == "G3":
        cp = _load_cp(out_dir, "G3")
        ev = mp.get("effect_size", cp.get("effect_val"))
        et = mp.get("effect_type", cp.get("effect_type"))
        dr = mp.get("dropout", cp.get("dropout"))
        pe = mp.get("p_event", cp.get("p_event"))
        p0 = mp.get("p0", cp.get("p0"))   # tỷ lệ biến cố nhóm chứng (chạy lại không mất)
        al = mp.get("alpha", cp.get("alpha"))
        pw = mp.get("power", cp.get("power"))
        if ev is not None:
            args += ["--effect-size", str(ev)]
        if et:
            args += ["--effect-type", str(et)]
        if dr is not None:
            args += ["--dropout", str(dr)]
        if pe is not None:
            args += ["--p-event", str(pe)]
        if p0 is not None:
            args += ["--p0", str(p0)]
        if al is not None:
            args += ["--alpha", str(al)]
        if pw is not None:
            args += ["--power", str(pw)]
    elif gate == "G8":
        cp = _load_cp(out_dir, "G8")
        tj = mp.get("target_journal", cp.get("target_journal"))
        iff = mp.get("impact_factor", cp.get("target_journal_if"))
        if tj:
            args += ["--target-journal", str(tj)]
        if iff is not None:
            args += ["--impact-factor", str(iff)]
    elif gate == "G9":
        cp = _load_cp(out_dir, "G9")
        na = mp.get("n_authors", cp.get("n_authors"))
        tj = mp.get("target_journal", cp.get("target_journal"))
        if na is not None:
            args += ["--n-authors", str(na)]
        if tj:
            args += ["--target-journal", str(tj)]
    return args


def _build_cmd(gate: str, study: str, out_dir: Path,
               topic: Optional[str], meta: dict) -> Optional[List[str]]:
    """Dựng lệnh chạy 1 cổng. None nếu thiếu điều kiện tối thiểu (vd G0 thiếu topic)."""
    py = sys.executable
    script = str(_script_for(gate))
    if gate == "G0":
        t = topic or _existing_topic(out_dir) or meta.get("title")
        if not t:
            return None  # không thể chạy G0 nếu không có chủ đề
        cmd = [py, script, "--study", study, "--topic", t]
        if meta.get("query_en"):
            cmd += ["--query-en", meta["query_en"]]
        return cmd
    # Các cổng còn lại: --study + THAM SỐ bác sĩ khôi phục được (nếu có).
    return [py, script, "--study", study] + _recover_params(gate, out_dir, meta)


def _read_guardrail(out_dir: Path, gate: str) -> Optional[bool]:
    """Đọc guardrail của checkpoint cổng: True/False/None(không rõ)."""
    p = out_dir / f"{gate}_checkpoint.json"
    if not p.exists():
        return None
    try:
        cp = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    g = cp.get("guardrail")
    if isinstance(g, dict):
        if "passed" in g:
            return bool(g.get("passed"))
        st = g.get("status")
        if isinstance(st, str):
            up = st.upper()
            return ("PASS" in up) or ("✅" in st) or ("[OK]" in up)
        return None
    if isinstance(g, str):
        up = g.upper()
        return ("PASS" in up) or ("✅" in g) or ("[OK]" in up)
    return None


def _run_gate_once(cmd: List[str], out_dir: Path) -> Dict[str, object]:
    """Chạy 1 lần; trả dict{exit_code, stdout_tail, stderr_tail}."""
    # Ép UTF-8 cho CỔNG CON: nhiều cổng in emoji (🚧/✅/🔒) → console/pipe cp1252
    # trên Windows ném UnicodeEncodeError làm chết cổng dù logic đúng. Truyền env
    # UTF-8 + decode UTF-8 để chạy được KHÔNG cần đặt PYTHONUTF8 tay.
    child_env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(cmd, cwd=str(BASE), capture_output=True,
                              text=True, timeout=600, env=child_env,
                              encoding="utf-8", errors="replace")
        return {
            "exit_code": proc.returncode,
            "stdout_tail": "\n".join(proc.stdout.splitlines()[-6:]),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-6:]),
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": 124, "stdout_tail": "", "stderr_tail": "TIMEOUT >600s"}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": 1, "stdout_tail": "", "stderr_tail": str(exc)[:300]}


def _diagnose_blocked(gate: str, out_dir: Path) -> Optional[str]:
    """Thông điệp remediation 1-dòng khi cổng DỪNG chờ input đời thực.

    GENERIC: đọc khối needs_input MÁY-ĐỌC-ĐƯỢC (gate_contract) từ checkpoint của
    BẤT KỲ cổng nào — không còn hardcode riêng G0. Fallback cho checkpoint CŨ
    (trước khi có needs_input): G0 0-PMID.
    """
    cp = _load_cp(out_dir, gate)
    detail = GC.blocked_detail(cp)
    if detail:
        return detail
    if gate == "G0":
        n_pmids = (cp.get("pubmed_results") or {}).get("n_pmids")
        if n_pmids == 0:
            return (
                "G0 tìm được 0 PMID — truy vấn PubMed từ chủ đề tiếng Việt thường "
                "KHÔNG khớp (PubMed không đánh chỉ mục tiếng Việt). CẦN BÁC SĨ cấp "
                "TỪ KHÓA TIẾNG ANH: chạy lại với --query-en \"...\" hoặc thêm "
                "\"query_en\" vào study_meta.json. Hệ KHÔNG bịa PMID để 'đi tiếp'."
            )
    return None


def _checkpoint_blocked(out_dir: Path, gate: str) -> bool:
    """Checkpoint của cổng đang ở trạng thái BLOCKED (chờ input đời thực) không.

    Dùng cho freshness/`need`: một checkpoint BLOCKED KHÔNG được coi là 'tươi/xong'
    — phải chạy lại để RE-SURFACE cần gì (idempotent: thiếu input → lại blocked;
    có input → đi tiếp), tránh lỗi 'skip fresh trên artifact rỗng'.
    """
    return GC.is_blocked(_load_cp(out_dir, gate))


def run_gate_with_healing(gate: str, study: str, out_dir: Path,
                          topic: Optional[str], meta: dict,
                          max_attempts: int) -> Dict[str, object]:
    """Chạy 1 cổng với vòng lặp retry CÓ TRẦN cho lỗi tạm thời.

    Trả dict{gate, status, attempts, guardrail, detail}. status ∈
    {'ok', 'ok_no_guardrail', 'blocked_missing_input', 'failed'}.
    """
    cmd = _build_cmd(gate, study, out_dir, topic, meta)
    if cmd is None:
        return {
            "gate": gate, "status": "blocked_missing_input", "attempts": 0,
            "guardrail": None,
            "detail": "Thiếu CHỦ ĐỀ để chạy G0 — cung cấp --topic hoặc "
                      "study_meta.json{title}. KHÔNG bịa chủ đề.",
        }
    last: Dict[str, object] = {}
    for attempt in range(1, max_attempts + 1):
        last = _run_gate_once(cmd, out_dir)
        exit_code = last["exit_code"]

        # ── HỢP ĐỒNG DỪNG — 4 mã thoát RỜI NGHĨA ──────────────────────────────
        # 2 = BLOCKED (chờ input đời thực): DỪNG graceful, KHÔNG retry (thử lại
        #     vô ích — thiếu input là xác định, không phải lỗi tạm thời).
        if exit_code == GC.EXIT_BLOCKED:
            return {"gate": gate, "status": "blocked_missing_input",
                    "attempts": attempt, "guardrail": None,
                    "detail": _diagnose_blocked(gate, out_dir) or last["stdout_tail"]}
        # 3 = GUARDRAIL FAIL (vi phạm liêm chính R1–R7): DỪNG, KHÔNG retry.
        if exit_code == GC.EXIT_GUARDRAIL_FAIL:
            return {"gate": gate, "status": "failed", "attempts": attempt,
                    "guardrail": False,
                    "detail": "Guardrail liêm chính R1–R7 lỗi — TRẢ-VỀ-SỬA: "
                              + (last["stdout_tail"] or "")}
        # 0 = OK: nhưng phòng thủ — cổng có thể exit 0 dù checkpoint tự đánh dấu
        #     blocked (cổng cũ chưa theo mã 2), hoặc guardrail=False.
        if exit_code == GC.EXIT_OK:
            if _checkpoint_blocked(out_dir, gate):
                return {"gate": gate, "status": "blocked_missing_input",
                        "attempts": attempt, "guardrail": None,
                        "detail": _diagnose_blocked(gate, out_dir) or ""}
            guardrail = _read_guardrail(out_dir, gate)
            status = "ok" if guardrail is True else (
                "failed" if guardrail is False else "ok_no_guardrail")
            if status != "failed":
                return {"gate": gate, "status": status, "attempts": attempt,
                        "guardrail": guardrail, "detail": last["stdout_tail"]}
            blocked = _diagnose_blocked(gate, out_dir)
            if blocked:
                return {"gate": gate, "status": "blocked_missing_input",
                        "attempts": attempt, "guardrail": False, "detail": blocked}
            # guardrail=False không rõ lý do → coi là lỗi liêm chính, KHÔNG retry.
            return {"gate": gate, "status": "failed", "attempts": attempt,
                    "guardrail": False,
                    "detail": "exit=0 nhưng guardrail=False: " + (last["stdout_tail"] or "")}
        # 1 = CRASH/tạm thời (exception/mạng) → thử lại tới trần.
        if attempt < max_attempts:
            continue
    # Hết lượt mà vẫn lỗi cứng (crash).
    blocked = _diagnose_blocked(gate, out_dir)
    if blocked:
        return {"gate": gate, "status": "blocked_missing_input",
                "attempts": max_attempts, "guardrail": None, "detail": blocked}
    return {
        "gate": gate, "status": "failed", "attempts": max_attempts,
        "guardrail": _read_guardrail(out_dir, gate),
        "detail": f"exit={last.get('exit_code')} | {last.get('stderr_tail','')}",
    }


def _load_all_checkpoints(out_dir: Path) -> Dict[str, dict]:
    """Nạp mọi checkpoint G0–G10 có mặt (bỏ qua cổng chưa chạy)."""
    cps: Dict[str, dict] = {}
    for g in GATE_ORDER:
        cp = _load_cp(out_dir, g)
        if cp:
            cps[g] = cp
    return cps


def _hard_gate_report(out_dir: Path, meta: dict) -> List[Dict[str, object]]:
    """D6 — BÁO TRUNG THỰC trạng thái cổng CỨNG (🔒).

    Cổng cứng sinh DRAFT tự động (guardrail PASS) nhưng CHỜ bằng chứng đời-thực.
    Trước đây pipeline chỉ in '✅ ok' cho G2/G4/G5/G9 → đọc như 'đã xong', dù
    IRB chưa duyệt/SAP chưa khóa/dữ liệu chưa có/liêm chính chưa ký. Ở đây dùng
    skill_standards.real_world_signals (nguồn chân lý, KHÔNG suy từ artifact) để
    phân biệt 'draft xong' vs 'đã khóa thật'.
    """
    if SKILL is None:
        return []
    cps = _load_all_checkpoints(out_dir)
    try:
        signals = SKILL.real_world_signals(cps, meta or {})
    except Exception:  # noqa: BLE001
        return []
    out: List[Dict[str, object]] = []
    for gate, (sig_key, need_label) in HARD_GATE_SIGNAL.items():
        if gate not in cps:
            continue
        locked = bool(signals.get(sig_key))
        out.append({
            "gate": gate, "signal": sig_key, "locked": locked,
            "state": ("🔒 ĐÃ KHÓA (có bằng chứng thật)" if locked
                      else f"🔒 draft — CHỜ {need_label}"),
            "need": None if locked else need_label,
        })
    return out


def orchestrate(study: str, topic: Optional[str], max_attempts: int,
                start_gate: Optional[str], check_only: bool) -> Dict[str, object]:
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = _load_meta(out_dir)

    # 1) Kiểm freshness trước.
    pre = FRESH.stale_report(out_dir)

    if check_only:
        return {"study": study, "mode": "check_only", "freshness_before": pre,
                "gate_results": [], "note": "Chỉ kiểm, không chạy."}

    # 2) Xác định điểm 'bẩn' đầu tiên: cổng thiếu / stale / orphan; hoặc --from.
    stale_set = set(pre["stale_gates"]) | set(pre["orphan_gates"])
    start_idx = 0
    if start_gate and start_gate in GATE_ORDER:
        start_idx = GATE_ORDER.index(start_gate)

    gate_results: List[Dict[str, object]] = []
    dirty = False   # một khi 1 cổng chạy lại, MỌI cổng sau phải chạy lại
    total_runs = 0

    for idx, gate in enumerate(GATE_ORDER):
        if idx < start_idx:
            gate_results.append({"gate": gate, "status": "skipped_before_start",
                                 "attempts": 0, "guardrail": None, "detail": ""})
            continue
        cp_exists = (out_dir / f"{gate}_checkpoint.json").exists()
        # --from ÉP chạy lại từ cổng chỉ định (và cascade xuống downstream).
        forced_start = bool(start_gate) and idx == start_idx
        # Checkpoint BLOCKED KHÔNG được coi 'tươi' — phải chạy lại để RE-SURFACE
        # cần gì (sửa lỗi 'skip fresh trên artifact rỗng' do freshness chỉ xét mtime).
        blocked_cp = cp_exists and _checkpoint_blocked(out_dir, gate)
        need = (dirty or (not cp_exists) or (gate in stale_set)
                or forced_start or blocked_cp)
        if not need:
            gate_results.append({"gate": gate, "status": "skipped_fresh",
                                 "attempts": 0,
                                 "guardrail": _read_guardrail(out_dir, gate),
                                 "detail": "đã tươi, bỏ qua"})
            continue

        if total_runs >= MAX_TOTAL_RUNS:
            gate_results.append({"gate": gate, "status": "failed", "attempts": 0,
                                 "guardrail": None,
                                 "detail": "Đạt trần MAX_TOTAL_RUNS — dừng an toàn."})
            break

        res = run_gate_with_healing(gate, study, out_dir, topic, meta, max_attempts)
        total_runs += 1
        gate_results.append(res)

        if res["status"] in ("ok", "ok_no_guardrail"):
            dirty = True   # cổng này mới → downstream phải chạy lại
        elif res["status"] == "blocked_missing_input":
            # G0 thiếu chủ đề: không thể tiếp tục chuỗi.
            break
        elif res["status"] == "failed":
            # Lỗi cứng: dừng để không lan lỗi xuống downstream.
            break

    # 3) Kiểm freshness sau (phải tươi nếu chạy trọn).
    post = FRESH.stale_report(out_dir)

    # 4) Kết luận sẵn sàng từ G10 checkpoint (nếu có).
    readiness = None
    g10 = out_dir / "G10_checkpoint.json"
    if g10.exists():
        try:
            readiness = json.loads(g10.read_text(encoding="utf-8")).get("readiness")
        except (json.JSONDecodeError, OSError):
            readiness = None

    ran = [r for r in gate_results if r["status"] in ("ok", "ok_no_guardrail")]
    failed = [r for r in gate_results if r["status"] == "failed"]
    blocked = [r for r in gate_results if r["status"] == "blocked_missing_input"]

    report = {
        "study": study,
        "mode": "run",
        "freshness_before": pre,
        "freshness_after": post,
        "gate_results": gate_results,
        "n_ran": len(ran),
        "n_failed": len(failed),
        "n_blocked": len(blocked),
        "total_gate_runs": total_runs,
        "converged_fresh": post["fresh"],
        "readiness": readiness,
        "hard_gates": _hard_gate_report(out_dir, meta),
    }
    # Ghi report.
    (out_dir / "pipeline_run_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def print_summary(report: Dict[str, object]) -> None:
    print(f"\n📋 BÁO CÁO CHUỖI CỔNG — {report['study']}")
    if report.get("mode") == "check_only":
        FRESH.print_report(report["freshness_before"])
        return
    print("  Kết quả từng cổng:")
    icon = {"ok": "✅", "ok_no_guardrail": "☑️", "skipped_fresh": "⏭️",
            "skipped_before_start": "·", "blocked_missing_input": "🚧",
            "failed": "❌"}
    for r in report["gate_results"]:
        mark = icon.get(r["status"], "?")
        extra = ""
        if r["status"] in ("failed", "blocked_missing_input"):
            extra = f" — {r['detail'][:120]}"
        att = f" (x{r['attempts']})" if r.get("attempts") else ""
        print(f"    {mark} {r['gate']}: {r['status']}{att}{extra}")
    print(f"  Đã chạy: {report['n_ran']} · lỗi: {report['n_failed']} · "
          f"chặn(thiếu input): {report['n_blocked']} · tổng lần chạy: "
          f"{report['total_gate_runs']}")

    # DỪNG chờ input đời-thực: nêu CHÍNH XÁC 1 hành động bác sĩ cần làm.
    stops = [r for r in report["gate_results"]
             if r["status"] == "blocked_missing_input"]
    if stops:
        print("  🚧 DỪNG chờ bác sĩ cấp input (hệ KHÔNG bịa để đi tiếp):")
        for r in stops:
            print(f"    • {r['gate']}: {r['detail']}")

    fresh = report["freshness_after"]
    print(f"  Freshness sau: {'✅ TƯƠI' if fresh['fresh'] else '⚠ còn stale: ' + ', '.join(fresh['stale_gates'])}")

    # D6 — trạng thái TRUNG THỰC cổng cứng (draft vs đã-khóa-thật).
    hard = report.get("hard_gates") or []
    if hard:
        print("  🔒 Cổng cứng (draft đã sinh — CHỜ bằng chứng đời-thực):")
        for h in hard:
            print(f"    • {h['gate']}: {h['state']}")

    if report.get("readiness"):
        print("  Kết luận sẵn sàng (G10):")
        for r in report["readiness"]:
            print(f"    • {r['moc']}: {r['dat']}")
    print("  → Cần bác sĩ kiểm chứng. Cổng cứng (IRB/SAP/dữ liệu thật) chờ bằng "
          "chứng đời thực, hệ KHÔNG tự vượt.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Nhạc trưởng tự động G0→G10 có cơ chế tự sửa chữa.")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--topic", default=None,
                    help="Chủ đề (bắt buộc cho đề tài MỚI; đề tài cũ tự lấy từ G0)")
    ap.add_argument("--max-attempts", type=int, default=2,
                    help="Số lần thử lại tối đa mỗi cổng khi lỗi tạm thời")
    ap.add_argument("--from", dest="from_gate", default=None,
                    help="Bắt đầu từ cổng này (vd G3)")
    ap.add_argument("--check-only", action="store_true",
                    help="Chỉ kiểm freshness, không chạy cổng nào")
    args = ap.parse_args()

    GC.ensure_utf8_stdout()  # chạy được trên console Windows mặc định (cp1252)
    print(f"🎼 Nhạc trưởng chuỗi cổng — đề tài: {args.study}")
    report = orchestrate(args.study, args.topic, args.max_attempts,
                         args.from_gate, args.check_only)
    print_summary(report)
    # Mã thoát: 0 nếu không có cổng lỗi/chặn và đã hội tụ tươi.
    if report.get("mode") == "check_only":
        return 0 if report["freshness_before"]["fresh"] else 1
    ok = (report["n_failed"] == 0 and report["n_blocked"] == 0
          and report["converged_fresh"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
