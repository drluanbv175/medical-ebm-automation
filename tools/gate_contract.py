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

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


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
REASON_MISSING_CITATION_VERIFICATION = "MISSING_CITATION_VERIFICATION"  # G10: A12 receipt chưa có/chưa sạch
REASON_MISSING_PEER_REVIEW = "MISSING_PEER_REVIEW_SIGNATURE"  # G10: G8 (bình duyệt độc lập) chưa ký ledger

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


# ── Chữ ký actor thật cho approval_ledger — vá 2026-07-12 (audit cổng G0-G9) ───
# Bối cảnh: tools/approve_gate.py trước đây LUÔN gọi add_approval(created_by_agent=False)
# bất kể ai thực sự gõ lệnh — script không có cách nào phân biệt "bác sĩ tự tay chạy"
# với "agent tự chạy thay". Kiểm định đối kháng xác nhận: agent tự gọi approve_gate.py
# (reviewer_ref tự đặt) tạo ra bản ghi ledger KHÔNG THỂ PHÂN BIỆT với phê duyệt bác sĩ
# thật, rồi chạy trót lọt toàn bộ phân tích thống kê — không có bác sĩ nào tham gia.
#
# Cơ chế: một khóa bí mật ngẫu nhiên, đặt NGOÀI OneDrive tại ~/.ebm-secrets/ (đúng quy
# ước sẵn có của dự án cho mọi secret), do BÁC SĨ tự tạo MỘT LẦN bằng
# tools/setup_gate_approval_key.py (script này PHẢI được bác sĩ tự chạy — nếu agent
# chạy hộ, agent sẽ biết khóa và tính năng mất tác dụng; xem docstring script đó).
# approve_gate.py dùng khóa này để ký HMAC-SHA256 mỗi phê duyệt; ledger_approved() ở
# dưới xác minh LẠI chữ ký bằng ĐÚNG khóa đó trước khi coi một cổng là đã khóa thật.
#
# GIỚI HẠN THẬT (ghi rõ, không giấu): agent (Claude Code) trong phiên này có quyền đọc
# toàn bộ filesystem qua Bash — về mặt kỹ thuật agent VẪN CÓ THỂ tự đọc file khóa nếu cố
# tình làm vậy. Cơ chế này không phải bảo mật chống-agent-cố-ý-phá, mà là: (1) biến việc
# tự-phê-duyệt từ "mặc định âm thầm, không ai biết" thành "hành vi lệch chuẩn rõ ràng,
# phải chủ động đọc một file bí mật có tên/vị trí tường minh" — vi phạm ngay có thể phát
# hiện qua audit; (2) khi khóa CHƯA từng bị agent đụng tới (bác sĩ tự thiết lập, không
# nhờ agent), chữ ký hợp lệ là bằng chứng đủ mạnh rằng một người có quyền truy cập máy
# tính (không nhất thiết chạy qua agent) đã ký. Đây là cải thiện thật so với hiện trạng
# (hardcode luôn =False), không phải tuyên bố "không thể vượt qua".
_SIGNING_KEY_ENV = "EBM_GATE_KEY_PATH"  # override vị trí khóa — dùng cho test, KHÔNG dùng vận hành thật
_DEFAULT_KEY_PATH = Path.home() / ".ebm-secrets" / "gate_approval_key"

_STAKEHOLDER_ROLE_ALIASES: Dict[str, set[str]] = {
    "PI": {
        "PI",
        "PI_PROJECT_OWNER",
        "PRINCIPAL_INVESTIGATOR",
        "CHU_NHIEM_DE_TAI",
        "CHU_NHIEM_NGHIEN_CUU",
        "NGHIEN_CUU_VIEN_CHINH",
        "CHỦ_NHIỆM_ĐỀ_TÀI",
        "CHỦ_NHIỆM_NGHIÊN_CỨU",
        "NGHIÊN_CỨU_VIÊN_CHÍNH",
    },
    "IRB": {
        "IRB",
        "IRB_CHAIR",
        "IRB_MEMBER",
        "IRB_ETHICS_COMMITTEE",
        "ETHICS_COMMITTEE",
        "HOI_DONG_DAO_DUC",
        "HOI_DONG_Y_DUC",
        "HỘI_ĐỒNG_ĐẠO_ĐỨC",
        "HỘI_ĐỒNG_Y_ĐỨC",
    },
    "STATISTICIAN": {
        "STATISTICIAN",
        "BIOSTATISTICIAN",
        "METHODS_STATISTICS_REVIEWER",
        "THONG_KE_VIEN",
        "CHUYEN_GIA_THONG_KE",
        "PHUONG_PHAP_THONG_KE",
        "THỐNG_KÊ_VIÊN",
        "CHUYÊN_GIA_THỐNG_KÊ",
        "PHƯƠNG_PHÁP_THỐNG_KÊ",
    },
    "INDEPENDENT_PEER_REVIEWER": {
        "INDEPENDENT_PEER_REVIEWER",
        "PEER_REVIEWER",
        "EXTERNAL_REVIEWER",
        "PHAN_BIEN_DOC_LAP",
        "PHAN_BIEN",
        "PHẢN_BIỆN_ĐỘC_LẬP",
        "PHẢN_BIỆN",
    },
}

# Vá 2026-07-14 (nâng cấp kiểm soát PI/IRB/thống kê viên/phản biện): mỗi cổng có thể
# chấp nhận NHIỀU nhóm stakeholder (tuple), không chỉ một — vd G4 (khóa SAP) trước đây
# fail-closed CHỈ chấp nhận STATISTICIAN, nhưng doctrine (thiet-ke-nghien-cuu.md) lại
# hướng dẫn "Chủ nhiệm đề tài" (PI) tự ký, khiến bác sĩ làm đúng theo tài liệu vẫn bị
# approve_gate.py từ chối — lệch thật giữa code và doctrine, phát hiện qua audit
# 2026-07-14. Nới G4 chấp nhận CẢ STATISTICIAN lẫn PI (khớp thực tế: bác sĩ đơn lẻ
# thường tự đóng vai trò thống kê cho đề tài của mình). G8 (bình duyệt/phản biện) mới
# thêm — trước đây hoàn toàn không có yêu cầu role/cổng cứng nào.
_GATE_REQUIRED_STAKEHOLDERS: Dict[str, Tuple[str, ...]] = {
    "G2": ("IRB",),
    "G4": ("STATISTICIAN", "PI"),
    "G8": ("INDEPENDENT_PEER_REVIEWER",),
    "G9": ("PI",),
}


def _normalize_role(role: str) -> str:
    return (
        (role or "")
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def reviewer_role_satisfies_gate(gate_id: str, reviewer_role: str) -> bool:
    """Role người duyệt có đúng stakeholder bắt buộc cho cổng không.

    Cổng chưa có stakeholder requirement (vd G5/Gate A/B) trả True để giữ tương
    thích. G2/G4/G8/G9 fail-closed nếu role không thuộc BẤT KỲ nhóm nào được phép:
    IRB · thống kê/phương pháp HOẶC PI (G4) · phản biện độc lập (G8) · PI (G9).
    """
    required_groups = _GATE_REQUIRED_STAKEHOLDERS.get(_normalize_role(gate_id))
    if not required_groups:
        return True
    normalized = _normalize_role(reviewer_role)
    return any(normalized in _STAKEHOLDER_ROLE_ALIASES[group] for group in required_groups)


_ROLE_HINT_TEXT: Dict[str, str] = {
    "IRB": "IRB / IRB_ETHICS_COMMITTEE / ETHICS_COMMITTEE",
    "STATISTICIAN": "METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN",
    "PI": "PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR",
    "INDEPENDENT_PEER_REVIEWER": "PHAN_BIEN / PEER_REVIEWER / EXTERNAL_REVIEWER",
}


def required_reviewer_role_hint(gate_id: str) -> str:
    required_groups = _GATE_REQUIRED_STAKEHOLDERS.get(_normalize_role(gate_id))
    if not required_groups:
        return "không yêu cầu nhóm role riêng"
    return " HOẶC ".join(_ROLE_HINT_TEXT[group] for group in required_groups)


def signing_key_path() -> Path:
    """Đường dẫn file khóa ký — mặc định ~/.ebm-secrets/gate_approval_key, có thể ghi đè
    bằng biến môi trường EBM_GATE_KEY_PATH (chỉ dùng cho test có kiểm soát)."""
    override = os.environ.get(_SIGNING_KEY_ENV)
    return Path(override) if override else _DEFAULT_KEY_PATH


def _load_signing_key() -> Optional[str]:
    """Đọc khóa ký từ đĩa — None nếu chưa thiết lập (BÁC SĨ chưa chạy
    setup_gate_approval_key.py) hoặc file rỗng/không đọc được."""
    p = signing_key_path()
    try:
        key = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return key or None


def signing_key_configured() -> bool:
    """True nếu máy này đã có khóa ký (bất kể nội dung cụ thể)."""
    return _load_signing_key() is not None


def _signature_payload(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str) -> bytes:
    return f"{gate_id}:{study}:{evidence_hash}:{timestamp_utc}".encode("utf-8")


def sign_approval(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str) -> Optional[str]:
    """Ký HMAC-SHA256 một phê duyệt bằng khóa cục bộ. Trả None nếu CHƯA có khóa
    (approve_gate.py khi đó vẫn ghi phê duyệt nhưng CẢNH BÁO rõ — không chặn cứng,
    để không phá vỡ các đề tài/test đã có từ trước khi cơ chế này tồn tại)."""
    key = _load_signing_key()
    if not key:
        return None
    mac = hmac.new(key.encode("utf-8"), _signature_payload(gate_id, study, evidence_hash, timestamp_utc),
                    hashlib.sha256)
    return mac.hexdigest()


def verify_approval_signature(record: Dict[str, Any], study: str) -> bool:
    """Xác minh LẠI chữ ký của một bản ghi ledger bằng khóa cục bộ hiện tại.
    False nếu: chưa có khóa trên máy này, bản ghi chưa từng được ký, hoặc chữ ký
    không khớp (khóa khác / nội dung bị sửa)."""
    key = _load_signing_key()
    sig = record.get("approver_signature")
    if not key or not sig:
        return False
    expected = hmac.new(
        key.encode("utf-8"),
        _signature_payload(record.get("gate_id", ""), study,
                            record.get("evidence_hash", ""), record.get("timestamp_utc", "")),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


def ledger_approved(gate_id: str, study: str, artifact_path: Path,
                    repo_root: Optional[Path] = None) -> bool:
    """CHỐT KIỂM DUY NHẤT nên dùng ở mọi nơi cần biết "cổng gate_id đã được bác sĩ
    duyệt THẬT chưa" — thay cho 5 bản sao gần-giống-nhau từng rải rác ở
    run_g6_auto.py (×4 template) và run_g9_auto.py trước 2026-07-12 (chính cách
    trùng lặp này từng gây lỗi thật ở nơi khác trong hệ thống — sửa 1 chỗ quên 3
    chỗ). True CHỈ khi ĐỦ CẢ NĂM: (1) có bản ghi APPROVED không synthetic cho
    gate_id, (2) không phải agent tạo, (3) reviewer_role của bản ghi thuộc ĐÚNG
    nhóm stakeholder bắt buộc cho gate_id nếu có (xem _GATE_REQUIRED_STAKEHOLDERS
    — vá 2026-07-14, trước đó role chỉ được ép ở approve_gate.py lúc TẠO bản ghi,
    không được xác minh lại ở đây lúc DÙNG), (4) evidence_hash khớp NỘI DUNG HIỆN
    TẠI của artifact_path (sửa file sau duyệt → coi như chưa duyệt), (5) NẾU máy
    này đã cấu hình khóa ký (signing_key_configured()) — chữ ký PHẢI khớp; nếu máy
    CHƯA từng thiết lập khóa, hạ về kiểm tra cũ (1)-(4) để không phá đề tài/test
    có từ trước khi có chữ ký (rely_on_signature=False được ghi rõ qua giá trị
    trả về của signing_key_configured(), gọi riêng nếu cần phân biệt 2 trường hợp)."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    ledger_p = root / "exports" / study / "approval_ledger.json"
    if not ledger_p.exists() or not Path(artifact_path).exists():
        return False
    try:
        records = json.loads(ledger_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    matches = [r for r in records if r.get("gate_id") == gate_id
               and r.get("decision") == "APPROVED" and not r.get("is_synthetic")
               and reviewer_role_satisfies_gate(gate_id, r.get("reviewer_role", ""))]
    if not matches:
        return False
    latest = sorted(matches, key=lambda r: r.get("timestamp_utc", ""))[-1]
    try:
        actual_hash = hashlib.sha256(Path(artifact_path).read_bytes()).hexdigest()
    except OSError:
        return False
    if actual_hash != latest.get("evidence_hash"):
        return False
    if signing_key_configured():
        return verify_approval_signature(latest, study)
    return True
