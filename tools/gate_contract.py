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
import unicodedata
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


# ── Danh sách đề tài THẬT — chặn cứng khỏi cơ chế admin-bypass synthetic ──────
# Thêm 2026-07-15 theo yêu cầu bác sĩ: xây "quyền phê duyệt tất cả" (tools/
# approve_gate_synthetic_admin.py) nhưng CHỈ cho dữ liệu tổng hợp/thử nghiệm,
# KHÔNG BAO GIỜ cho nghiên cứu người thật. Đây là LỚP PHÒNG THỦ THỨ HAI — lớp
# thứ nhất là study_meta.json["study_kind"] phải được TỰ TAY đặt = "synthetic_test"
# qua tools/mark_study_synthetic.py (script đó cũng từ chối tự đặt cờ này lên
# bất kỳ tên nào trong danh sách dưới đây). Nếu ai đó lỡ đặt study_kind lên một
# đề tài THẬT (nhầm lẫn/copy-paste study_meta.json giữa các đề tài), danh sách
# CỐ Ý KHÔNG CÓ CỜ NÀO GHI ĐÈ ĐƯỢC này vẫn chặn — không có --force/--i-confirm
# nào bỏ qua được nó, đúng nguyên tắc "PI không thể tự làm hội đồng đạo đức của
# chính mình" cho G2/G8.
# BẮT BUỘC: thêm tên thư mục (khớp exports/<tên>/) vào đây NGAY khi tạo một đề
# tài nghiên cứu NGƯỜI THẬT mới — trước khi chạy bất kỳ pipeline nào cho nó.
REAL_STUDY_DENYLIST: frozenset = frozenset({
    "hai-long-benh-nhan-C1a-BVQY175",
    # KKB-HAI-LONG-2026: BÍ DANH của CÙNG đề tài thật (cùng tiêu đề/viện/PICO —
    # "Khoa Khám bệnh C1a, Bệnh viện Quân y 175") — thư mục chạy-thử G0-G10 dùng
    # ĐÚNG chủ đề thật làm dữ liệu; xem exports/hai-long-benh-nhan-C1a-BVQY175/
    # _LIEN-KET-VOI-BAN-CHAY-THU-KKB.md. Thêm vào denylist 2026-07-15 sau khi
    # red-team đối kháng phát hiện nó KHÔNG bị chặn (chạy `--study KKB-HAI-LONG-2026`
    # trót lọt, không cần thủ thuật) — đúng loại "bí danh đề tài thật ngoài danh
    # sách" mà denylist-theo-tên một mình không bắt được.
    "KKB-HAI-LONG-2026",
})


def is_real_study_denylisted(study: str) -> bool:
    """True nếu tên đề tài nằm trong danh sách đề tài THẬT bị chặn cứng khỏi mọi
    cơ chế admin-bypass synthetic — kiểm tra KHÔNG phân biệt hoa/thường, bỏ
    khoảng trắng đầu/cuối, và CHUẨN HÓA NFC trước khi so khớp để tránh né tránh
    bằng biến thể chữ hoa/khoảng trắng/dạng tổ hợp Unicode (NFD vs NFC — cùng
    hiển thị, khác chuỗi mã). Phòng thủ theo chiều sâu: REAL_STUDY_DENYLIST hôm
    nay chỉ chứa slug thuần ASCII nên .casefold() một mình đã đủ, nhưng nếu sau
    này có mục thêm dấu tiếng Việt thì so khớp vẫn đúng ngay từ đầu."""
    needle = unicodedata.normalize("NFC", (study or "").strip()).casefold()
    return needle in {unicodedata.normalize("NFC", s).casefold() for s in REAL_STUDY_DENYLIST}


def resolve_synthetic_study_dir(study: str, repo_root: Path) -> Tuple[Optional[Path], Optional[str]]:
    """CHỐT AN TOÀN dùng chung cho 2 tool admin-synthetic (mark_study_synthetic.py +
    approve_gate_synthetic_admin.py). Giải exports/<study> thành MỘT đường dẫn CANONICAL
    (đã resolve toàn bộ symlink, "."/".."), kiểm CONTAINMENT + DENYLIST, rồi trả về
    (real_dir, None) khi hợp lệ hoặc (None, thông_điệp_lỗi) khi từ chối.

    Đóng CÙNG LÚC 4 lớp lỗ hổng red-team đối kháng đã tái hiện được (2026-07-15):
      1. TOCTOU symlink race: TRẢ VỀ đường dẫn đã resolve(strict=True) — mọi I/O sau
         PHẢI dùng real_dir này, KHÔNG dùng lại Path chưa resolve (đi qua symlink có
         thể bị tráo giữa lúc-kiểm và lúc-ghi). resolve() giải cả chuỗi nên real_dir
         không còn thành phần symlink nào.
      2. Thoát sandbox bằng --study tuyệt đối / "../" / symlink trỏ ra ngoài: ép
         real_dir.parent PHẢI ĐÚNG exports/ (con trực tiếp), nếu không → từ chối.
      3. --study rỗng ("" khiến exports/"" == exports/ gốc): bắt riêng đầu hàm.
      4. Denylist: kiểm trên real_dir.name (tên CANONICAL sau resolve), không phải
         chuỗi --study thô — bắt cả "./<tên thật>", dấu "/" cuối, "../<tên>/<tên>".
    """
    if not study or not str(study).strip():
        return None, "Tên đề tài (--study) rỗng — không xác định được thư mục."
    exports_root = (Path(repo_root) / "exports").resolve()
    study_dir = Path(repo_root) / "exports" / study
    try:
        real_dir = study_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None, f"Không thấy thư mục đề tài (hoặc không giải được đường dẫn): {study_dir}"
    if real_dir.parent != exports_root:
        return None, (
            f"Thư mục đề tài phải là con TRỰC TIẾP của {exports_root} — "
            f"'{study}' giải ra '{real_dir}' (nằm ngoài). Từ chối đường dẫn tuyệt đối, "
            "'../', chuỗi rỗng, hoặc symlink trỏ ra ngoài exports/."
        )
    if is_real_study_denylisted(real_dir.name):
        return None, (
            f"'{study}' (→ thư mục thật '{real_dir.name}') nằm trong "
            "gate_contract.REAL_STUDY_DENYLIST — đề tài nghiên cứu người thật đã biết. "
            "KHÔNG cờ/đường-dẫn nào bỏ qua được kiểm tra này."
        )
    return real_dir, None


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
_SIGNING_KEY_ENV = "EBM_GATE_KEY_PATH"  # override vị trí khóa — CHỈ có tác dụng khi chạy dưới pytest (vá 2026-07-26)
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


# ── VÁ 2026-07-26 (audit độc lập lớp bảo mật, KHÔNG phải vòng lặp doctrine) ───
# Ba lỗ hổng THẬT trong chính cơ chế chữ ký ở trên, chưa vòng kiểm tra nào chạm tới
# vì 30 vòng trước đều soi NỘI DUNG doctrine, không soi thiết kế mật mã:
#
#   (1) TÁCH VAI TRÒ KHÔNG ĐƯỢC THỰC THI. _signature_payload() cũ ký đúng
#       "gate_id:study:evidence_hash:timestamp" — KHÔNG có reviewer_role. Cộng với
#       MỘT khóa duy nhất dùng chung cho cả máy, hệ quả: người giữ khóa ký hợp lệ
#       được CẢ 4 vai trò (IRB · thống kê · phản biện độc lập G8 · PI G9), và 4 bản
#       ghi đó KHÔNG THỂ PHÂN BIỆT về mặt mật mã với 4 người thật ký độc lập. Nguyên
#       tắc "PI không thể tự làm hội đồng đạo đức của chính mình" (ghi ở dòng ~254)
#       chỉ được kiểm bằng một chuỗi role TỰ GÕ VÀO, không xác thực gì.
#       → Vá: (a) role_group + reviewer_ref nay NẰM TRONG nội dung được ký (chống
#       tái dùng chữ ký của vai trò này cho vai trò khác); (b) hỗ trợ KHÓA RIÊNG
#       THEO VAI TRÒ gate_approval_key_<NHÓM> — khi có, chữ ký của nhóm đó chỉ tạo
#       được bằng đúng khóa đó, nên tách vai trò trở thành THẬT (giao khóa IRB cho
#       hội đồng thật giữ); (c) chữ ký TỰ KHAI phạm vi ("role" vs "shared") để
#       downstream nói đúng sự thật thay vì ngầm định mọi chữ ký đều tương đương.
#
#   (2) EBM_GATE_KEY_PATH ghi đè được ở code VẬN HÀNH THẬT. Comment cũ ghi "chỉ dùng
#       cho test" nhưng KHÔNG có gì thực thi điều đó: đặt biến môi trường trỏ tới một
#       khóa tự tạo là tự ký mọi cổng trót lọt. → Vá: chỉ đọc override khi ĐANG chạy
#       trong pytest (_test_context_active()); ngoài test, biến này bị bỏ qua hoàn toàn.
#
#   (3) FAIL-OPEN khi máy chưa cấu hình khóa. ledger_approved() cũ trả True cho mọi
#       đề tài KHÔNG nằm trong REAL_STUDY_DENYLIST — một danh sách phải nhớ cập nhật
#       BẰNG TAY cho từng đề tài thật mới. Đề tài người thật vừa tạo, chưa kịp thêm
#       vào danh sách, trên máy chưa có khóa → ledger JSON bịa tay vẫn được coi là
#       "đã duyệt". → Vá: LẬT MẶC ĐỊNH sang fail-closed. Không có khóa ⇒ CHƯA DUYỆT,
#       trừ đúng một ngoại lệ tường minh: đề tài đã được đánh dấu study_kind ==
#       "synthetic_test" qua tools/mark_study_synthetic.py (vốn đã tự từ chối đề tài
#       trong denylist). Denylist từ nay là lớp phòng thủ THỨ HAI, không còn là lớp
#       duy nhất đứng giữa một đề tài thật và một phê duyệt giả.
_SIGNATURE_SCHEME = "v2"
_SIGNATURE_SCOPE_ROLE = "role"      # ký bằng khóa RIÊNG của nhóm stakeholder
_SIGNATURE_SCOPE_SHARED = "shared"  # ký bằng khóa CHUNG (một người giữ — KHÔNG chứng minh tách vai trò)


def _test_context_active() -> bool:
    """True khi đang chạy dưới pytest — điều kiện DUY NHẤT cho phép EBM_GATE_KEY_PATH
    ghi đè vị trí khóa. Ngoài test, biến môi trường đó bị bỏ qua hoàn toàn (lỗ hổng
    (2) ở trên: comment 'chỉ dùng cho test' trước đây không được thực thi)."""
    return "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ


def role_group_for(reviewer_role: str) -> Optional[str]:
    """Nhóm stakeholder chuẩn của một role tự khai (None nếu không thuộc nhóm nào).
    Biên lai máy sinh (A12 trích dẫn, metadata) không có vai trò người → None."""
    normalized = _normalize_role(reviewer_role)
    for group, aliases in _STAKEHOLDER_ROLE_ALIASES.items():
        if normalized in aliases:
            return group
    return None


def _base_key_path() -> Path:
    override = os.environ.get(_SIGNING_KEY_ENV) if _test_context_active() else None
    return Path(override) if override else _DEFAULT_KEY_PATH


def signing_key_path(role_group: Optional[str] = None) -> Path:
    """Đường dẫn file khóa ký. Có khóa RIÊNG cho nhóm (gate_approval_key_<NHÓM>) thì
    ưu tiên dùng; không thì về khóa chung ~/.ebm-secrets/gate_approval_key."""
    base = _base_key_path()
    if role_group:
        per_role = base.with_name(f"{base.name}_{role_group}")
        if per_role.exists():
            return per_role
    return base


def _read_key(p: Path) -> Optional[str]:
    try:
        key = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return key or None


def _load_signing_key(role_group: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Trả (khóa, phạm_vi). phạm_vi='role' khi dùng được khóa riêng của nhóm (tách vai
    trò THẬT), ='shared' khi phải dùng khóa chung (một người giữ — không chứng minh
    được có người thứ hai tham gia)."""
    if role_group:
        per_role_path = signing_key_path(role_group)
        if per_role_path != _base_key_path():
            key = _read_key(per_role_path)
            if key:
                return key, _SIGNATURE_SCOPE_ROLE
    return _read_key(_base_key_path()), _SIGNATURE_SCOPE_SHARED


def signing_key_configured(role_group: Optional[str] = None) -> bool:
    """True nếu máy này có khóa ký dùng được cho nhóm (hoặc khóa chung khi không nêu nhóm)."""
    key, _ = _load_signing_key(role_group)
    return key is not None


def per_role_key_available(role_group: str) -> bool:
    """True nếu tồn tại khóa RIÊNG cho nhóm stakeholder này — tức chữ ký của nhóm đó
    là bằng chứng tách vai trò thật, không phải tự ký bằng khóa chung."""
    if not role_group:
        return False
    key, scope = _load_signing_key(role_group)
    return bool(key) and scope == _SIGNATURE_SCOPE_ROLE


def _signature_payload(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str,
                       role_group: str = "", reviewer_ref: str = "") -> bytes:
    """Nội dung được ký. KHÁC bản trước 2026-07-26: có thêm role_group + reviewer_ref,
    và tiền tố scheme — nên chữ ký tạo cho vai trò này KHÔNG dùng lại được cho vai trò
    khác, kể cả khi cùng cổng/cùng artifact/cùng thời điểm."""
    return "|".join([
        _SIGNATURE_SCHEME,
        gate_id or "",
        study or "",
        evidence_hash or "",
        timestamp_utc or "",
        role_group or "",
        (reviewer_ref or "").strip(),
    ]).encode("utf-8")


def sign_approval(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str, *,
                  reviewer_role: str = "", reviewer_ref: str = "") -> Optional[str]:
    """Ký HMAC-SHA256 một phê duyệt. Trả None nếu CHƯA có khóa (approve_gate.py khi đó
    vẫn ghi phê duyệt nhưng CẢNH BÁO rõ, và ledger_approved() sẽ KHÔNG coi là đã duyệt).

    Chuỗi trả về: "v2:<phạm_vi>:<hex>" — phạm_vi 'role' nghĩa là ký bằng khóa riêng của
    nhóm stakeholder (tách vai trò thật), 'shared' nghĩa là ký bằng khóa chung của máy.
    Phạm vi nằm NGAY TRONG chữ ký để mọi nơi đọc ledger nói đúng mức bảo đảm, thay vì
    ngầm hiểu mọi chữ ký đều là bằng chứng độc lập."""
    group = role_group_for(reviewer_role) or ""
    key, scope = _load_signing_key(group or None)
    if not key:
        return None
    mac = hmac.new(
        key.encode("utf-8"),
        _signature_payload(gate_id, study, evidence_hash, timestamp_utc, group, reviewer_ref),
        hashlib.sha256,
    ).hexdigest()
    return f"{_SIGNATURE_SCHEME}:{scope}:{mac}"


def _record_reviewer_ref(record: Dict[str, Any]) -> str:
    """Mã định danh người duyệt trong một bản ghi ledger.

    CẨN TRỌNG (bẫy thật, suýt tự gây lỗi khi vá 2026-07-26): tên trường CHUẨN trong
    runtime/schemas.py::ApprovalRecord là `reviewer_identity_reference`, KHÔNG phải
    `reviewer_ref` — `reviewer_ref` chỉ là tên THAM SỐ của factory
    ApprovalLedger.make_human_approval(). Đọc nhầm khóa sẽ luôn ra chuỗi rỗng, làm mọi
    chữ ký thật (ký kèm reviewer_ref có giá trị) không bao giờ khớp. Đọc trường chuẩn
    trước, chấp nhận `reviewer_ref` như bí danh cho các bản ghi/test dựng tay."""
    for key in ("reviewer_identity_reference", "reviewer_ref"):
        val = record.get(key)
        if val:
            return str(val)
    return ""


def signature_scope(record: Dict[str, Any]) -> Optional[str]:
    """Phạm vi khóa đã ký bản ghi ('role' | 'shared'), None nếu không có/không đúng định dạng."""
    sig = record.get("approver_signature")
    if not isinstance(sig, str):
        return None
    parts = sig.split(":")
    if len(parts) != 3 or parts[0] != _SIGNATURE_SCHEME:
        return None
    return parts[1] if parts[1] in (_SIGNATURE_SCOPE_ROLE, _SIGNATURE_SCOPE_SHARED) else None


def verify_approval_signature(record: Dict[str, Any], study: str) -> bool:
    """Xác minh LẠI chữ ký một bản ghi ledger bằng khóa cục bộ hiện tại.

    False nếu: chưa có khóa phù hợp trên máy này, bản ghi chưa từng được ký, chữ ký sai
    định dạng v2, nội dung bị sửa, HOẶC role/reviewer_ref của bản ghi khác lúc ký (vì cả
    hai nay nằm trong payload) — tức không thể lấy chữ ký hợp lệ của một vai trò rồi đổi
    nhãn role trong JSON thành vai trò khác. Bản ghi tự khai phạm vi 'role' mà máy hiện
    KHÔNG có khóa riêng của nhóm đó cũng bị từ chối (chống hạ cấp về khóa chung)."""
    sig = record.get("approver_signature")
    if not isinstance(sig, str) or not sig:
        return False
    parts = sig.split(":")
    if len(parts) != 3 or parts[0] != _SIGNATURE_SCHEME:
        return False
    claimed_scope, mac_hex = parts[1], parts[2]
    if claimed_scope not in (_SIGNATURE_SCOPE_ROLE, _SIGNATURE_SCOPE_SHARED):
        return False
    group = role_group_for(record.get("reviewer_role", "")) or ""
    key, actual_scope = _load_signing_key(group or None)
    if not key or actual_scope != claimed_scope:
        return False
    expected = hmac.new(
        key.encode("utf-8"),
        _signature_payload(record.get("gate_id", ""), study, record.get("evidence_hash", ""),
                           record.get("timestamp_utc", ""), group, _record_reviewer_ref(record)),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, mac_hex)


def is_synthetic_test_study(study: str, repo_root: Optional[Path] = None) -> bool:
    """True CHỈ khi đề tài đã được đánh dấu TƯỜNG MINH study_kind == 'synthetic_test'
    (qua tools/mark_study_synthetic.py) VÀ không nằm trong denylist đề tài thật. Đây là
    ngoại lệ DUY NHẤT còn được đi tiếp khi máy chưa cấu hình khóa ký."""
    if is_real_study_denylisted(study):
        return False
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    meta = load_study_meta(root / "exports" / study)
    return str(meta.get("study_kind", "")).strip().casefold() == "synthetic_test"


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
    TẠI của artifact_path (sửa file sau duyệt → coi như chưa duyệt), (5) chữ ký
    mật mã PHẢI khớp bằng đúng khóa của nhóm stakeholder tương ứng.

    SỬA 2026-07-26 (audit độc lập lớp bảo mật) — điều kiện (5) nay FAIL-CLOSED THEO
    MẶC ĐỊNH. Trước đây, khi máy chạy kiểm tra chưa cấu hình khóa ký, hàm này HẠ
    CHUẨN về (1)-(4) cho mọi đề tài không nằm trong REAL_STUDY_DENYLIST — mà denylist
    là danh sách phải nhớ cập nhật BẰNG TAY cho từng đề tài người thật mới. Hệ quả
    thật: một đề tài người thật vừa tạo (chưa kịp thêm vào danh sách) chỉ cần một
    approval_ledger.json tự bịa — không chữ ký, reviewer_ref bất kỳ, tính đúng
    evidence_hash (hash KHÔNG phải bí mật, ai cũng tính được) — là qua cổng. Nay
    "chưa có khóa ⇒ CHƯA DUYỆT" áp dụng cho MỌI đề tài; ngoại lệ duy nhất là đề tài
    đã được TỰ TAY đánh dấu study_kind == "synthetic_test". Denylist trở thành lớp
    phòng thủ thứ hai thay vì lớp duy nhất."""
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
    group = role_group_for(latest.get("reviewer_role", "")) or None
    if signing_key_configured(group):
        return verify_approval_signature(latest, study)
    # VÁ 2026-07-26 — LẬT MẶC ĐỊNH SANG FAIL-CLOSED (lỗ hổng (3) mô tả ở trên).
    # Trước: mọi đề tài KHÔNG có trong REAL_STUDY_DENYLIST đều được coi là "đã duyệt"
    # khi máy chưa cấu hình khóa ký — nghĩa là một đề tài NGƯỜI THẬT vừa tạo, chưa kịp
    # thêm tay vào danh sách, chỉ cần một approval_ledger.json bịa (tính đúng
    # evidence_hash — không cần bí mật gì) là qua cổng. Nay: KHÔNG có khóa ⇒ CHƯA DUYỆT,
    # ngoại lệ duy nhất là đề tài đã tự tay đánh dấu study_kind == "synthetic_test"
    # (tools/mark_study_synthetic.py, vốn đã từ chối mọi tên trong denylist).
    return is_synthetic_test_study(study, root)
