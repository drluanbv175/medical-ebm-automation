#!/usr/bin/env python3
"""gate_contract.py — HỢP ĐỒNG DỪNG (blocked contract) dùng chung cho chuỗi cổng G0–G10.

Mục đích: cho MỌI cổng một cách DỪNG GRACEFUL, MÁY-ĐỌC-ĐƯỢC, MỘT-HÀNH-ĐỘNG khi
thiếu một đầu vào ĐỜI THỰC mà hệ thống KHÔNG được bịa (effect size/MCID, phê
duyệt IRB, khóa SAP, dữ liệu thật, chữ ký liêm chính). Thay cho hai lỗi cũ đã
xác nhận bằng test:
  - "exit 1 KHÔNG ghi checkpoint" (G4 khi thiếu N) → pipeline nhầm là CRASH, báo
    "❌ failed" trống rỗng, không có remediation.
  - "guardrail ✅ PASS trên artifact RỖNG" (G3 khi n=0) → cả chuỗi tưởng G3 xong,
    march tới G4 rồi kẹt vĩnh viễn.

BỐN MÃ THOÁT (rời nghĩa — thiếu-input KHÔNG đụng crash):
  EXIT_OK        = 0  cổng chạy xong + giá trị lõi KHÔNG rỗng + guardrail sạch
  EXIT_BLOCKED   = 2  DỪNG chờ input đời thực (ĐÃ ghi checkpoint DRAFT + needs_input)
  EXIT_GUARDRAIL = 3  artifact vi phạm liêm chính R1–R7 (PII, vượt cổng, PMID bịa…)
  EXIT_CRASH     = 1  lỗi bất ngờ (exception/I-O) — DÀNH RIÊNG cho crash thật

Bất biến LIÊM CHÍNH: mọi remediation chỉ "chạy lại script thật với giá trị bác sĩ
cấp" hoặc "bác sĩ điền/ký" — KHÔNG bịa. Mỗi needs_input liệt kê must_not_fabricate.

Module này chỉ dùng thư viện chuẩn (không phụ thuộc ngoài) để mọi cổng import được.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def ensure_utf8_stdout() -> None:
    """Ép stdout/stderr về UTF-8 để KHÔNG crash trên console Windows mặc định (cp1252).

    Sửa lỗi portability THẬT (đã xác nhận): các cổng in emoji (🚧/✅/🔒) → console
    cp1252 ném UnicodeEncodeError, làm chết script dù logic đúng. Trước đây phải đặt
    PYTHONUTF8=1 tay. Gọi hàm này ở đầu mỗi entry-point để chạy được ngay cả khi
    quên biến môi trường. An toàn/không tác dụng phụ nếu stdout đã UTF-8 hoặc không
    hỗ trợ reconfigure (vd bị pipe/redirect).
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            enc = (getattr(stream, "encoding", "") or "").lower()
            if enc and "utf" not in enc and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError, AttributeError):
            pass

# ── Bốn mã thoát rời nghĩa ───────────────────────────────────────────────────
EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_GUARDRAIL_FAIL = 3
EXIT_CRASH = 1

# ── Từ vựng LÝ DO DỪNG chuẩn (taxonomy) — pipeline + tài liệu tham chiếu ──────
REASON_MISSING_EFFECT_SIZE = "MISSING_EFFECT_SIZE"        # G3: chưa có effect size/MCID
REASON_MISSING_SAMPLE_SIZE = "MISSING_SAMPLE_SIZE"        # G4: chưa có N hợp lệ từ G3
REASON_MISSING_PUBMED = "MISSING_PUBMED_EVIDENCE"         # G0: 0 PMID (cần query_en)
REASON_MISSING_PICO = "MISSING_PICO"                      # G0: PICO chưa được xác nhận
REASON_MISSING_IRB = "MISSING_IRB_APPROVAL"              # G2: chưa có phê duyệt thật
REASON_MISSING_SAP_LOCK = "MISSING_SAP_SIGNATURE"        # G4: chưa ký khóa SAP
REASON_MISSING_DATA = "MISSING_REAL_DATA"                # G5: chưa có dữ liệu thật
REASON_MISSING_INTEGRITY = "MISSING_INTEGRITY_SIGNATURES"  # G9: chưa ký liêm chính

# Chuỗi guardrail cho trạng thái BLOCKED — CỐ Ý không chứa "PASS"/"✅"/"[OK]" để
# bộ đọc guardrail cũ (run_pipeline._read_guardrail) KHÔNG nhầm là đã đạt.
BLOCKED_GUARDRAIL_STR = "🚧 BLOCKED — CHỜ INPUT ĐỜI THỰC (hệ KHÔNG tự vượt)"


def needs_input(reason_code: str, human_message: str, command: str,
                must_not_fabricate: Iterable[str],
                study_meta_patch: Optional[Dict[str, Any]] = None,
                supplied_by: str = "doctor") -> Dict[str, Any]:
    """Dựng khối needs_input MÁY-ĐỌC-ĐƯỢC gắn vào checkpoint khi cổng DỪNG.

    - reason_code: một trong REASON_* (taxonomy chuẩn).
    - human_message: câu tiếng Việt bác sĩ đọc hiểu ngay.
    - command: LỆNH chạy lại DUY NHẤT để đi tiếp sau khi có input thật.
    - must_not_fabricate: các trường hệ thống TUYỆT ĐỐI không được bịa.
    - study_meta_patch: gợi ý khối cần thêm vào study_meta.json (PIN durable).
    """
    return {
        "blocked": True,
        "reason_code": reason_code,
        "human_message": human_message,
        "remediation": {
            "action": "rerun_with_real_input",
            "command": command,
            "study_meta_patch": study_meta_patch or {},
            "must_not_fabricate": list(must_not_fabricate),
        },
        "supplied_by": supplied_by,
    }


def core_value(name: str, value: Any, is_empty: bool) -> Dict[str, Any]:
    """Mô tả GIÁ TRỊ LÕI cổng phải tính ra — is_empty=True thì CẤM báo PASS."""
    return {"name": name, "value": value, "is_empty": bool(is_empty)}


def is_blocked(cp: Dict[str, Any]) -> bool:
    """Checkpoint có ở trạng thái BLOCKED (chờ input đời thực) không."""
    ni = cp.get("needs_input")
    return bool(isinstance(ni, dict) and ni.get("blocked"))


def blocked_detail(cp: Dict[str, Any]) -> Optional[str]:
    """Thông điệp remediation 1-dòng cho bác sĩ, hoặc None nếu không blocked."""
    ni = cp.get("needs_input")
    if not (isinstance(ni, dict) and ni.get("blocked")):
        return None
    msg = ni.get("human_message", "Cổng cần input đời thực.")
    cmd = (ni.get("remediation") or {}).get("command")
    return f"{msg} → {cmd}" if cmd else msg


# ── study_meta.json — NƠI PIN durable quyết định thật của bác sĩ ──────────────
# Cờ bằng-chứng-đời-thực: hệ KHÔNG tự bật, chỉ bác sĩ xác nhận. gate_params là nơi
# PIN tham số (effect size…) để CHẠY LẠI không mất input (khớp run_pipeline._recover_params).
_META_DEFAULTS: Dict[str, Any] = {
    "irb_approved": False,
    "sap_lock_date": None,
    "data_lock_date": None,
    "results_final": False,
    "integrity_signed": False,
}

_GATE_PARAMS_SKELETON: Dict[str, Any] = {
    # G3 — bác sĩ PIN effect size (kèm PMID nguồn) để tính cỡ mẫu; hệ KHÔNG bịa.
    "G3": {
        "effect_size": None,          # vd 0.75 (HR) — [CẦN BÁC SĨ CẤP + PMID/DOI nguồn]
        "effect_type": None,          # HR/OR/RR/ARR%/AUC/MD
        "dropout": None,              # vd 0.15
        "p_event": None,              # tỷ lệ biến cố nền (log-rank)
        "sd": None,                   # độ lệch chuẩn kết cục liên tục (bắt buộc khi effect_type=MD)
    },
}


def ensure_study_meta(out_dir: Path, *, seed: Optional[Dict[str, Any]] = None,
                      with_gate_params: bool = True) -> Dict[str, Any]:
    """Tạo/ĐIỀN-BÙ exports/<study>/study_meta.json — KHÔNG phá dữ liệu bác sĩ đã có.

    Quy tắc hợp nhất:
      - File chưa có → tạo mới từ seed + cờ mặc định + gate_params skeleton.
      - File đã có → chỉ THÊM key còn THIẾU (không đè giá trị bác sĩ đã điền).
      - gate_params.G3 skeleton chỉ thêm key con còn thiếu (giữ effect_size bác sĩ pin).
    Trả về dict meta cuối cùng (đã ghi nếu có thay đổi).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "study_meta.json"

    meta: Dict[str, Any] = {}
    if p.exists():
        try:
            meta = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                meta = {}
        except (json.JSONDecodeError, OSError):
            meta = {}

    changed = False

    # 1) Seed (title/topic/query_en/design_code…) — chỉ điền khi THIẾU/để trống.
    # SỬA 2026-07-06: seed lồng nhau (vd {"gate_params": {"G3": {...}}}) trước
    # đây KHÔNG BAO GIỜ được merge một khi khóa cấp 1 ("gate_params") đã tồn
    # tại — "if not meta.get(k)" coi cả dict con (dù rỗng bên trong) là "đã có
    # giá trị" nên bỏ qua toàn bộ, làm mọi lệnh persist effect_size/SD/dropout
    # từ run_g3_auto.py (gọi SAU khi G0 đã tạo skeleton gate_params) thành
    # KHÔNG-LÀM-GÌ âm thầm — phát hiện qua chạy thật G0→G10 trên đề tài mới.
    # Nay đệ quy vào dict con, chỉ điền SUB-KEY còn thiếu/rỗng, giữ nguyên
    # đúng nguyên tắc "không đè giá trị bác sĩ đã điền" nhưng ở MỌI cấp độ.
    def _fill_recursive(dst: Dict[str, Any], src: Dict[str, Any]) -> bool:
        did_change = False
        for kk, vv in src.items():
            if isinstance(vv, dict):
                if not isinstance(dst.get(kk), dict):
                    dst[kk] = {}
                    did_change = True
                if _fill_recursive(dst[kk], vv):
                    did_change = True
                continue
            if vv is None:
                if kk not in dst:
                    dst[kk] = None
                    did_change = True
                continue
            if not dst.get(kk):
                dst[kk] = vv
                did_change = True
        return did_change

    if _fill_recursive(meta, seed or {}):
        changed = True

    # 2) Cờ bằng-chứng-đời-thực — chỉ thêm nếu key chưa tồn tại (giữ nguyên nếu bác sĩ đã bật).
    for k, v in _META_DEFAULTS.items():
        if k not in meta:
            meta[k] = v
            changed = True

    # 3) gate_params skeleton — thêm khối/khóa con còn thiếu.
    if with_gate_params:
        gp = meta.get("gate_params")
        if not isinstance(gp, dict):
            gp = {}
            meta["gate_params"] = gp
            changed = True
        for gate, skel in _GATE_PARAMS_SKELETON.items():
            sub = gp.get(gate)
            if not isinstance(sub, dict):
                gp[gate] = dict(skel)
                changed = True
            else:
                for kk, vv in skel.items():
                    if kk not in sub:
                        sub[kk] = vv
                        changed = True

    if changed or not p.exists():
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_study_meta(out_dir: Path) -> Dict[str, Any]:
    """Đọc study_meta.json (dict rỗng nếu không có/lỗi)."""
    p = Path(out_dir) / "study_meta.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}
