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
from datetime import datetime, timezone
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
REASON_MISSING_RELEASE_READINESS = "MISSING_G10_RELEASE_READINESS"
REASON_MISSING_RELEASE_APPROVAL = "MISSING_G10_RELEASE_APPROVAL"

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


def g2_quality_contract_satisfied(
    checkpoint: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """True khi checkpoint G2 mới đã qua hợp đồng chất lượng có cấu trúc.

    Checkpoint cũ chưa mang ``quality_contract_version`` được giữ tương thích;
    workflow sinh từ G2-2026.1 trở đi bắt buộc ``PASS_G2_APPROVED`` ngoài chữ
    ký ledger. Nhờ vậy, một chữ ký đúng kỹ thuật trên hồ sơ thiếu metadata,
    sai phiên bản hoặc hết hiệu lực không mở được đường dữ liệu thật.
    """
    if not isinstance(checkpoint, dict):
        return False
    if not checkpoint.get("quality_contract_version"):
        return True
    quality = checkpoint.get("quality_gate")
    if not (
        isinstance(quality, dict)
        and quality.get("status") == "PASS_G2_APPROVED"
    ):
        return False

    valid_until = str(checkpoint.get("g2_approval_valid_until") or "").strip()
    no_expiry = checkpoint.get("g2_no_expiry_confirmed") is True
    if valid_until:
        try:
            expiry = datetime.fromisoformat(valid_until[:10]).date()
        except ValueError:
            return False
        if expiry < datetime.now(timezone.utc).date():
            return False
    elif not no_expiry:
        return False

    if isinstance(meta, dict):
        params = meta.get("gate_params")
        g2 = params.get("G2") if isinstance(params, dict) else {}
        if isinstance(g2, dict):
            current_protocol = str(g2.get("protocol_version") or "").strip()
            approved_protocol = str(
                checkpoint.get("g2_protocol_version") or ""
            ).strip()
            if current_protocol and current_protocol != approved_protocol:
                return False
            current_icf = str(g2.get("icf_version") or "").strip()
            approved_icf = str(checkpoint.get("g2_icf_version") or "").strip()
            waiver = checkpoint.get("g2_icf_waiver_approved") is True
            if current_icf and not waiver and current_icf != approved_icf:
                return False
    return True


def g5_quality_contract_satisfied(
    study: str,
    repo_root: Optional[Path] = None,
) -> bool:
    """True khi G5 được chấm trực tiếp là dataset khóa + phê duyệt hợp lệ.

    Import lười tránh vòng import ở lúc nạp module: ``g5_quality_gate`` dùng lại
    các primitive ledger trong file này. Không tin riêng report JSON lưu sẵn vì
    dataset/dictionary/query log có thể đã thay đổi sau lần chấm trước.
    """
    try:
        import g5_quality_gate as g5_quality  # noqa: PLC0415
    except ImportError:
        return False
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    try:
        report = g5_quality.evaluate_study(
            str(study),
            root / "exports" / str(study),
            repo_root=root,
            write=False,
        )
    except (OSError, RuntimeError, ValueError):
        return False
    return report.get("status") == g5_quality.STATUS_LOCKED


def g9_quality_contract_satisfied(
    study: str,
    repo_root: Optional[Path] = None,
) -> bool:
    """True khi G9 được chấm trực tiếp là đã khóa liêm chính công bố.

    Không tin ``submission_package_ready`` hoặc report JSON lưu sẵn. Việc chấm
    trực tiếp bắt lại thay đổi ở manuscript/readiness/A12/G8 sau chữ ký PI.
    """
    try:
        import g9_quality_gate as g9_quality  # noqa: PLC0415
    except ImportError:
        return False
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    try:
        report = g9_quality.evaluate_study(
            str(study),
            root / "exports" / str(study),
            repo_root=root,
            write=False,
        )
    except (OSError, RuntimeError, ValueError):
        return False
    return report.get("status") == g9_quality.STATUS_LOCKED


def g10_quality_contract_satisfied(
    study: str,
    repo_root: Optional[Path] = None,
) -> bool:
    """True khi gói G10 được chấm trực tiếp là đã khóa phát hành.

    Không tin ``release_package_ready`` hoặc report JSON lưu sẵn. Việc chấm
    trực tiếp bắt lại thay đổi ở đề cương, StudySpec, readiness, A12, G8, G9
    và mọi artifact trong manifest sau chữ ký PI.
    """
    try:
        import g10_quality_gate as g10_quality  # noqa: PLC0415
    except ImportError:
        return False
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    try:
        report = g10_quality.evaluate_study(
            str(study),
            root / "exports" / str(study),
            repo_root=root,
            write=False,
        )
    except (OSError, RuntimeError, ValueError):
        return False
    return report.get("status") == g10_quality.STATUS_LOCKED


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
    # G0 — CÂU HỎI NGHIÊN CỨU. Thêm 2026-07-28: trước đây G0 là cổng DUY NHẤT
    # không có khối gate_params, nên bác sĩ KHÔNG CÓ CHỖ CHUẨN để pin quyết định
    # "PICO này là PICO cuối" — và hệ quả là G0 luôn in "✅ HOÀN THÀNH" trong khi
    # mọi ô P/I/C/O trong artifact A1 vẫn còn nguyên placeholder [CẦN BÁC SĨ...].
    # Hằng số REASON_MISSING_PICO ở trên đã dự trù đúng tình huống này từ đầu
    # nhưng chưa từng có nơi nào dùng — khối này là chỗ đóng vòng đó.
    # Hệ KHÔNG tự bật cờ nào ở đây; g0_quality_gate.py chỉ ĐỌC.
    "G0": {
        # PICO/PECO — bác sĩ tự viết, hệ không suy ra (xem docstring run_g0_auto.py).
        "population": None,
        "intervention": None,
        "comparison": None,          # "không có nhóm so sánh — mô tả" cũng là câu trả lời hợp lệ
        "outcomes": [],
        # Kết cục CHÍNH phải DUY NHẤT và ĐO ĐƯỢC (doctrine cau-hoi-nghien-cuu).
        "primary_outcome": None,
        "primary_outcome_measure": None,     # đơn vị/thang đo
        "primary_outcome_timepoint": None,   # thời điểm đo
        # Giả thuyết + loại kiểm định (THÀNH PHẦN 3 của doctrine).
        "hypothesis_h0": None,
        "hypothesis_h1": None,
        "expected_direction": None,
        "test_type": None,           # superiority/non_inferiority/equivalence/descriptive
        "question_type": None,       # therapy/diagnosis/prognosis/harm/descriptive
        # FINER — 5 tiêu chí, bác sĩ đánh giá từng cái (không phải 1 cờ gộp).
        "finer_feasible": None,
        "finer_interesting": None,
        "finer_novel": None,
        "finer_ethical": None,
        "finer_relevant": None,
        # Đã ĐỌC LẠI bằng chứng G0 tìm được, và biện minh tính mới bằng chữ.
        "evidence_reviewed_confirmed": False,
        "novelty_justification": None,
        "pico_confirmed": False,
        "reviewed_by_role": None,
        "reviewed_at": None,
    },
    # G1 — quyết định phương pháp do PI/methodologist xác nhận. Hệ chỉ sinh
    # dự thảo và kiểm nhất quán; không tự bật các cờ xác nhận người thật.
    "G1": {
        "protocol_version": "1.0",
        "design": None,
        "design_confirmed": False,
        "design_rationale": None,
        "objectives": [],
        "research_question": None,
        "primary_outcome": None,
        "secondary_outcomes": [],
        "population": None,
        "inclusion_criteria": [],
        "exclusion_criteria": [],
        "setting": None,
        "study_period": None,
        "intervention_or_exposure": None,
        "comparator": None,
        "recruitment_strategy": None,
        "follow_up_schedule": None,
        "central_phenomenon": None,
        "qualitative_approach": None,
        "data_collection_method": None,
        "saturation_criterion": None,
        "information_sources": [],
        "search_strategy": None,
        "search_last_date": None,
        "study_selection_process": None,
        "estimand": {
            "population": None,
            "treatment_condition": None,
            "variable": None,
            "intercurrent_events_strategy": None,
            "population_summary_measure": None,
        },
        "bias_controls_confirmed": False,
        "protocol_core_confirmed": False,
        "feasibility_confirmed": False,
        "evidence_review_confirmed": False,
        "reviewed_by_role": None,
        "reviewed_at": None,
    },
    # G2 — metadata phiên bản và đường đi đạo đức/đăng ký. Các trường này chỉ
    # mô tả hồ sơ hiện hành; KHÔNG phải phê duyệt. G2 chỉ khóa khi ledger có
    # chữ ký đúng vai trò IRB và phụ lục approval attestation hợp lệ.
    "G2": {
        "protocol_version": "1.0",
        "icf_version": "1.0",
        "recruitment_mode": None,
        "registration_required": None,
        "registration_registry": None,
        "registration_id": None,
        "registration_date": None,
        "first_enrolment_date": None,
        "icf_waiver_requested": False,
        "safety_plan_required": None,
    },
    # G7 — BẢN THẢO. Thêm 2026-07-28. G7 là cổng có đầu ra đi RA NGOÀI xa nhất
    # (bản thảo gửi tạp chí), nhưng trước đây không có chỗ nào để tác giả chốt
    # những thứ chỉ người thật quyết được: ai là tác giả, khai báo ICMJE, và
    # quan trọng nhất — đã có người ĐỌC LẠI TOÀN VĂN chưa. Hệ KHÔNG tự bật cờ nào.
    "G7": {
        "title": None,
        "authors": None,              # tên/đơn vị/ORCID — hệ không suy ra được
        "target_journal": None,
        # 5 khai báo bắt buộc theo ICMJE — thiếu là tạp chí trả lại.
        "author_contributions": None,
        "coi_declared": None,
        "funding_declared": None,
        "data_sharing_statement": None,
        "ai_use_declared": None,
        # Bản nháp do công cụ sinh KHÔNG được gửi đi khi chưa có người đọc lại.
        "manuscript_reviewed_confirmed": False,
        "reviewed_by_role": None,
        "reviewed_at": None,
    },
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
      - gate_params từng cổng chỉ thêm key con còn thiếu (giữ mọi quyết định đã pin).
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


def resolve_design_code(out_dir: Path, default: str = "cohort") -> Tuple[str, Optional[str]]:
    """Mã THIẾT KẾ nghiên cứu dùng chung cho MỌI cổng: (design_code, cảnh báo nếu có).

    ★ VÁ 2026-07-27 — LỖI THẬT phát hiện qua chạy thử trọn G0→G10: `--design rct` truyền ở
    G2 BỊ NUỐT, và G3/G4/G6 rơi về "cohort".
    Nguyên nhân: G2 nhận `--design`, dùng đúng cho phần việc của nó, và có ghi `design_code`
    vào G2_checkpoint.json — nhưng G3/G4/G6 chỉ đọc G1_checkpoint.json rồi mặc định
    "cohort" nếu không thấy. Hệ quả KHÔNG hề nhỏ với một pipeline nghiên cứu: **chuẩn báo
    cáo bị chọn sai** (STROBE thay vì CONSORT cho một RCT), nhánh công thức cỡ mẫu sai,
    template phân tích sai — mà không một dòng cảnh báo nào. Hội đồng Đạo đức hoặc tạp chí
    sẽ nhận một hồ sơ tự khai sai loại thiết kế.
    (G5/G7/G9 vốn đã đọc cả hai checkpoint nên không dính; đúng mẫu "sửa/viết 1 chỗ quên
    chỗ anh em" đã lặp ở mọi vòng kiểm định của đợt này — nên đặt hàm này ở chỗ dùng chung
    thay vì vá riêng từng cổng.)

    Thứ tự ưu tiên: G2 (nơi bác sĩ có thể truyền `--design` TƯỜNG MINH) > G1 (suy luận tự
    động) > default. Khi hai nơi KHÁC nhau thì trả kèm cảnh báo để cổng in ra — im lặng
    chọn một bên là đúng cách lỗi này đã tồn tại mà không ai biết.
    """
    out_dir = Path(out_dir)

    def _read(name: str, *path: str) -> Optional[str]:
        p = out_dir / name
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return None
        for key in path:
            if not isinstance(data, dict):
                return None
            data = data.get(key)
        return data if isinstance(data, str) and data.strip() else None

    g1 = _read("G1_checkpoint.json", "design", "internal_code")
    g2 = _read("G2_checkpoint.json", "design_code")
    if g1 and g2 and g1 != g2:
        return g2, (f"⚠️  THIẾT KẾ LỆCH GIỮA CÁC CỔNG: G1 suy luận '{g1}' nhưng G2 ghi "
                    f"'{g2}' (thường do bác sĩ truyền --design {g2} ở G2). Đang dùng '{g2}'. "
                    "Nếu SAI, chạy lại G1/G2 cho khớp TRƯỚC khi đi tiếp — mã thiết kế quyết "
                    "định chuẩn báo cáo (CONSORT/STROBE/PRISMA…) và công thức cỡ mẫu.")
    return (g2 or g1 or default), None


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


def _study_path_components(study: Any) -> set:
    """MỌI tên thành phần xuất hiện trong chuỗi --study, sau khi chuẩn hóa lexically.

    Mục đích: denylist phải bắt được tên đề tài thật DÙ NGƯỜI TA VIẾT ĐƯỜNG DẪN KIỂU GÌ —
    "./TÊN", "TÊN/", "TÊN/.", "TÊN/../TÊN", ".//TÊN". Kiểm mỗi chuỗi thô là không đủ (đó
    chính là cách red-team ghép đòn để vượt cả hai phép kiểm ở vòng 3)."""
    s = str(study or "").strip()
    if not s:
        return set()
    names = {s}
    normalized = os.path.normpath(s)
    names.add(normalized)
    names.add(os.path.basename(normalized))
    names.update(Path(normalized).parts)
    return {n for n in names if n and n not in (".", "..", os.sep)}


def _symlink_chain_names(path: Path, limit: int = 40) -> set:
    """Tên của MỌI CHẶNG trong chuỗi symlink từ `path` tới đích cuối cùng.

    Kiểm tên ở chặng CUỐI (real_dir.name) một mình không đủ: tên bị cấm có thể nằm ở một
    chặng GIỮA (a → TÊN-BỊ-CẤM → b), khi đó chặng cuối mang tên vô hại. `limit` chặn vòng
    lặp symlink tự trỏ vào nhau."""
    names: set = set()
    cur = path
    for _ in range(limit):
        names.add(cur.name)
        try:
            if not cur.is_symlink():
                break
            target = os.readlink(cur)
            cur = Path(target) if os.path.isabs(target) else (cur.parent / target)
        except OSError:
            break
    names.add(cur.name)
    return {n for n in names if n}


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
      4. Denylist: kiểm trên CẢ HAI — chuỗi --study THÔ *và* real_dir.name (tên CANONICAL
         sau resolve). Xem khối cảnh báo ngay dưới: kiểm một trong hai là KHÔNG ĐỦ.
    """
    # ★ VÁ 2026-07-27 (workflow kiểm định 6 góc nhìn — REGRESSION do chính bản vá
    # 2026-07-26 vòng 2 gây ra, mức HIGH). Lịch sử để không ai "sửa lùi" lần nữa:
    #   - Bản gốc kiểm denylist trên real_dir.name (CANONICAL). Chặn được "./TÊN",
    #     "TÊN/", "TÊN/." — các biến thể chuỗi trỏ cùng một thư mục.
    #   - Vòng 2 phát hiện is_synthetic_test_study() kiểm trên CHUỖI THÔ nên bị các biến
    #     thể đó lách, và "sửa" bằng cách BỎ HẲN phép kiểm thô, giao trọn cho hàm này.
    #   - Red-team độc lập chỉ ra ngay: như vậy chỉ ĐỔI lỗ hổng này lấy lỗ hổng kia.
    #     Kiểm CANONICAL một mình bị "giặt tên" bằng symlink — đổi tên thư mục thật thành
    #     tên khác rồi tạo symlink mang ĐÚNG tên bị cấm trỏ vào đó:
    #         mv exports/hai-long-benh-nhan-C1a-BVQY175 exports/du-lieu-noi-bo-2026
    #         ln -s du-lieu-noi-bo-2026 exports/hai-long-benh-nhan-C1a-BVQY175
    #     → real_dir.name = "du-lieu-noi-bo-2026" (không nằm trong danh sách) → LỌT, và
    #     4 cổng G2/G4/G8/G9 trả True cho đề tài NGƯỜI THẬT với ledger bịa không chữ ký.
    #     `ls` thường vẫn hiện đúng tên cũ, chỉ `ls -l` mới lộ — rất khó nhận ra bằng mắt.
    # ⇒ Kết luận: hai phép kiểm bắt hai lớp tấn công KHÁC NHAU (biến thể chuỗi vs giặt tên
    #   qua symlink). PHẢI GIỮ CẢ HAI. Đừng bao giờ thay cái này bằng cái kia.
    if not study or not str(study).strip():
        return None, "Tên đề tài (--study) rỗng — không xác định được thư mục."
    # ★ VÁ 2026-07-27 vòng 4 — kiểm MỌI THÀNH PHẦN đường dẫn, không chỉ chuỗi thô.
    # Vòng 3 kiểm "chuỗi thô" + "tên canonical" và tưởng thế là phủ hai lớp tấn công.
    # Red-team GHÉP hai đòn lại thì cả hai phép kiểm cùng trượt: "./TÊN-THẬT" không khớp
    # chuỗi thô (khác ký tự), còn symlink đổi tên làm real_dir.name thành tên khác — nên
    # `./hai-long-benh-nhan-C1a-BVQY175` trỏ vào thư mục đã đổi tên vẫn LỌT, và
    # mark_study_synthetic.py + approve_gate_synthetic_admin.py chấp nhận nó (tái hiện
    # bằng CLI thật). Nay chuẩn hóa lexically rồi soi TỪNG thành phần: bắt "./TÊN",
    # "TÊN/", "TÊN/.", "TÊN/../TÊN", ".//TÊN" — mọi cách viết đường dẫn có chứa tên bị cấm.
    for candidate in _study_path_components(study):
        if is_real_study_denylisted(candidate):
            return None, (
                f"'{study}' chứa thành phần đường dẫn '{candidate}' nằm trong "
                "gate_contract.REAL_STUDY_DENYLIST — đề tài nghiên cứu người thật đã biết."
            )
    exports_root = (Path(repo_root) / "exports").resolve()
    # str(study) — không để một study id phi-chuỗi (vd đọc từ JSON metadata) ném TypeError
    # ở phép "/" bên dưới: đây là chốt fail-closed, phải TRẢ VỀ lỗi chứ không được ném.
    study_dir = Path(repo_root) / "exports" / str(study)
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
    # Kiểm TỪNG CHẶNG của chuỗi symlink, không chỉ chặng cuối: tên bị cấm có thể nằm ở
    # giữa chuỗi (a → TÊN-BỊ-CẤM → b) khiến real_dir.name trông vô hại.
    for hop_name in _symlink_chain_names(study_dir) | {real_dir.name}:
        if is_real_study_denylisted(hop_name):
            return None, (
                f"'{study}' giải qua '{hop_name}' — tên này nằm trong "
                "gate_contract.REAL_STUDY_DENYLIST (đề tài nghiên cứu người thật đã biết). "
                "Kiểm trên MỌI chặng symlink, không chỉ thư mục đích."
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
    "DATA_MANAGER": {
        "DATA_MANAGER",
        "CLINICAL_DATA_MANAGER",
        "DATA_GOVERNANCE_REVIEWER",
        "DATA_GOVERNANCE_QA_REVIEWER",
        "DATA_STEWARD",
        "QUAN_LY_DU_LIEU",
        "QUẢN_LÝ_DỮ_LIỆU",
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
    "G5": ("DATA_MANAGER", "PI"),
    "G8": ("INDEPENDENT_PEER_REVIEWER",),
    "G9": ("PI",),
    "G10": ("PI",),
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

    Cổng chưa có stakeholder requirement (vd Gate A/B) trả True để giữ tương
    thích. G2/G4/G5/G8/G9/G10 fail-closed nếu role không thuộc BẤT KỲ nhóm nào
    được phép: IRB · thống kê/phương pháp HOẶC PI (G4) · quản trị dữ liệu HOẶC
    PI (G5) · phản biện độc lập (G8) · PI (G9/G10).
    """
    required_groups = _GATE_REQUIRED_STAKEHOLDERS.get(_normalize_role(gate_id))
    if not required_groups:
        return True
    normalized = _normalize_role(reviewer_role)
    return any(normalized in _STAKEHOLDER_ROLE_ALIASES[group] for group in required_groups)


_ROLE_HINT_TEXT: Dict[str, str] = {
    "IRB": "IRB / IRB_ETHICS_COMMITTEE / ETHICS_COMMITTEE",
    "STATISTICIAN": "METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN",
    "DATA_MANAGER": "DATA_MANAGER / DATA_GOVERNANCE_QA_REVIEWER / DATA_STEWARD",
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
#       được bằng đúng khóa đó; (c) chữ ký TỰ KHAI phạm vi ("role" vs "shared") để
#       downstream nói đúng sự thật thay vì ngầm định mọi chữ ký đều tương đương.
#
#       ★ GIỚI HẠN THẬT của (b) — SỬA 2026-07-26 vòng 2 sau khi red-team ĐỘC LẬP chỉ ra
#       bản ghi chú đầu tiên NÓI QUÁ ("tách vai trò trở thành THẬT"). HMAC là mật mã
#       ĐỐI XỨNG: máy nào XÁC MINH cũng phải giữ ĐÚNG khóa đã KÝ. Nên trên một máy đơn
#       lẻ chạy cả pipeline, muốn cổng G2/G8 xác minh được thì khóa IRB/phản biện PHẢI
#       nằm sẵn trên chính máy đó — tức cấu hình DUY NHẤT triển khai được lại chính là
#       cấu hình mà một người giữ đủ 4 khóa và ký được cả 4 vai trò. Red-team đã chứng
#       minh: đưa khóa IRB cho hội đồng thật giữ (gỡ khỏi máy) → xác minh G2 trả False.
#       Vậy khóa riêng theo vai trò MANG LẠI: tách bạch về mặt VẬN HÀNH (mỗi vai trò
#       một tệp khóa, tạo/lưu/luân chuyển riêng, mất 1 khóa không vô hiệu các vai trò
#       khác) và một dấu vết TỰ KHAI kiểm toán được ("role" vs "shared"). Nó KHÔNG mang
#       lại: bằng chứng mật mã rằng người ký độc lập với chủ nhiệm đề tài.
#       Muốn có bảo đảm ĐÓ thì phải dùng chữ ký BẤT ĐỐI XỨNG (vd Ed25519): người duyệt
#       giữ khóa RIÊNG, máy chạy pipeline chỉ cần khóa CÔNG để xác minh — khi đó gỡ khóa
#       riêng khỏi máy vẫn xác minh được. Đây là hướng đi đúng nhưng đổi cả quy trình
#       quản lý khóa, cần bác sĩ quyết định trước khi làm.
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
# v3 (2026-07-27): thêm `decision` + `is_synthetic` vào nội dung ký — xem
# _signature_payload(). Nâng số hiệu để chữ ký v2 (thiếu 2 trường đó) bị từ chối thẳng
# thay vì được chấp nhận âm thầm. An toàn: tại thời điểm nâng KHÔNG có approval_ledger.json
# nào tồn tại trên đĩa (đã kiểm `find exports -name approval_ledger.json`), nên không phê
# duyệt thật nào bị vô hiệu.
# v4 (2026-07-27): thêm `prev_hash` — SỔ CÁI CHUỖI BĂM LIÊN KẾT. Xem chain_prev_hash().
# Lý do nâng số hiệu: prev_hash nằm TRONG nội dung ký, nên chữ ký v3 (không có nó) phải bị
# từ chối thay vì chấp nhận âm thầm. An toàn: tại thời điểm nâng KHÔNG có approval_ledger.json
# nào tồn tại trên đĩa (`find exports -name approval_ledger.json` rỗng).
_SIGNATURE_SCHEME = "v4"
# Mắt xích đầu tiên của chuỗi — bản ghi đầu sổ cái ký với giá trị này.
_CHAIN_GENESIS = "GENESIS"
_SIGNATURE_SCOPE_ROLE = "role"      # ký bằng khóa RIÊNG của nhóm stakeholder
_SIGNATURE_SCOPE_SHARED = "shared"  # ký bằng khóa CHUNG (một người giữ — KHÔNG chứng minh tách vai trò)
# Bí danh công khai để nơi khác (vd run_g10_assemble.py) không phải dùng tên có gạch dưới.
SIGNATURE_SCOPE_ROLE = _SIGNATURE_SCOPE_ROLE
SIGNATURE_SCOPE_SHARED = _SIGNATURE_SCOPE_SHARED


def _test_context_active() -> bool:
    """True khi đang chạy dưới pytest — điều kiện DUY NHẤT cho phép EBM_GATE_KEY_PATH
    ghi đè vị trí khóa.

    ★ NÓI THẲNG MỨC BẢO ĐẢM (sửa 2026-07-27 — đây là lần thứ BA trong cùng file này một
    dòng tài liệu hứa nhiều hơn code làm được, nên viết dứt khoát):
    **Đây KHÔNG PHẢI một ranh giới bảo mật, và không thể là.** Cả hai tín hiệu đều giả
    lập được: `PYTEST_CURRENT_TEST` chỉ là biến môi trường ai cũng `export` được, còn
    `"pytest" in sys.modules` chỉ cần một dòng `import pytest`. Đừng ở đâu mô tả cơ chế
    này là "đã đóng cửa ghi đè khóa".

    Vì sao vẫn giữ, và vì sao thế là ĐỦ: giả lập được cờ này chỉ giúp kẻ tấn công tự ký
    một chữ ký xác minh được TRONG CHÍNH TIẾN TRÌNH CỦA HỌ. Mọi tiến trình bình thường
    (bác sĩ chạy cổng thật) đọc khóa thật ở ~/.ebm-secrets/ và vẫn trả False — nên KHÔNG
    tạo ra được phê duyệt giả BỀN VỮNG trên đĩa. Red-team độc lập đã xác nhận điểm này
    bằng thực nghiệm. Giá trị thật của hàm là chống VÔ Ý: một biến EBM_GATE_KEY_PATH sót
    lại trong shell profile không được phép âm thầm làm hỏng một lần chạy cổng THẬT.

    ĐÃ THỬ bỏ vế `PYTEST_CURRENT_TEST` (2026-07-27) và ĐÃ HOÀN NGUYÊN: 17 test hợp lệ vỡ.
    Lý do đáng ghi lại — nhiều test chạy các cổng như TIẾN TRÌNH CON
    (`subprocess.run([...run_stats_analysis.py...])`); tiến trình con KHÔNG có `pytest`
    trong sys.modules, nên chỉ còn biến môi trường (pytest tự đặt và truyền xuống) là tín
    hiệu khả dụng. Bỏ nó = chặn oan chính luồng kiểm thử đang bảo vệ hệ thống, đổi lấy
    một lợi ích bảo mật bằng KHÔNG (kẻ tấn công vốn đọc được file khóa). Siết ở đây là
    siết nhầm chỗ."""
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


def chain_prev_hash(record: Optional[Dict[str, Any]]) -> str:
    """Vân tay của một bản ghi, dùng làm mắt xích cho bản ghi KẾ TIẾP trong sổ cái.

    ★ SỔ CÁI CHUỖI BĂM LIÊN KẾT (2026-07-27) — vá lỗ hổng IM LẶNG cuối cùng mà cả SÁU
    vòng kiểm định độc lập đều ghi nhận là chưa đóng được: **xóa hẳn một bản ghi THU HỒI
    khỏi file thì không ai phát hiện được**. Chữ ký chứng minh từng bản ghi không bị sửa,
    nhưng KHÔNG nói gì về những bản ghi ĐÃ TỪNG CÓ MÀ NAY KHÔNG CÒN — một sổ cái bị cắt
    bớt trông y hệt một sổ cái ngắn.

    Cách đóng: mỗi bản ghi ký kèm vân tay của bản ghi ĐỨNG NGAY TRƯỚC nó. Xóa một bản ghi
    ⇒ bản kế tiếp trỏ tới một vân tay không còn tồn tại ⇒ ĐỨT XÍCH, phát hiện được. Đảo
    thứ tự hoặc chèn thêm cũng đứt. Vì prev_hash nằm TRONG nội dung ký, kẻ không có khóa
    không thể vá lại xích.

    Vân tay tính trên ĐÚNG các trường đã được ký (không gồm scope/approval_id — những
    trường không ký, để một thay đổi vô hại ở đó không làm đứt xích oan).
    """
    if not isinstance(record, dict):
        return _CHAIN_GENESIS
    ref, _ok = _record_reviewer_ref(record)
    role_raw = record.get("reviewer_role")
    material = "|".join([
        str(record.get("gate_id") or ""),
        str(record.get("evidence_hash") or ""),
        str(record.get("timestamp_utc") or ""),
        role_group_for(role_raw if isinstance(role_raw, str) else "") or "",
        ref,
        str(record.get("decision") or "").strip().upper(),
        "1" if record.get("is_synthetic") else "0",
        str(record.get("approver_signature") or ""),
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _signature_payload(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str,
                       role_group: str = "", reviewer_ref: str = "",
                       decision: str = "", is_synthetic: bool = False,
                       prev_hash: str = "") -> bytes:
    """Nội dung được ký.

    v2 (2026-07-26) thêm role_group + reviewer_ref — chống dùng lại chữ ký của vai trò này
    cho vai trò khác.

    ★ v3 (2026-07-27) — VÁ LỖ HỔNG NẶNG NHẤT CẢ ĐỢT, do workflow kiểm định 6 góc nhìn tìm
    ra: `decision` và `is_synthetic` là HAI TRƯỜNG mà ledger_approved() DÙNG ĐỂ LỌC
    (chỉ nhận decision=="APPROVED" và không synthetic) nhưng LẠI KHÔNG NẰM TRONG nội dung
    được ký. Hệ quả cụ thể: hội đồng đạo đức xét và TỪ CHỐI đề tài, chữ ký được tạo hợp lệ
    cho quyết định "REJECTED" — kẻ khác chỉ cần sửa MỘT chuỗi trong JSON thành "APPROVED"
    là chữ ký vẫn khớp (vì payload không hề nhắc tới trường đó) và cổng mở. KHÔNG cần biết
    khóa. Đây là cách tệ nhất để đánh lừa bác sĩ: hệ báo "đã qua cổng đạo đức" trong khi
    hồ sơ thật là ĐÃ BỊ TỪ CHỐI. Tương tự với is_synthetic: một phê duyệt CHỈ dành cho dữ
    liệu thử nghiệm có thể bị lật thành phê duyệt cho đề tài thật.
    Nay mọi trường mà chốt kiểm dựa vào để RA QUYẾT ĐỊNH đều nằm trong nội dung ký.

    Nguyên tắc rút ra (ghi lại để không tái phạm): TRƯỜNG NÀO ĐƯỢC DÙNG ĐỂ LỌC/QUYẾT ĐỊNH
    THÌ TRƯỜNG ĐÓ PHẢI ĐƯỢC KÝ. Ký một phần bản ghi rồi tin vào phần không ký là vô nghĩa.
    """
    return "|".join([
        _SIGNATURE_SCHEME,
        gate_id or "",
        study or "",
        evidence_hash or "",
        timestamp_utc or "",
        role_group or "",
        (reviewer_ref or "").strip(),
        (decision or "").strip().upper(),
        "1" if is_synthetic else "0",
        prev_hash or _CHAIN_GENESIS,
    ]).encode("utf-8")


def sign_approval(gate_id: str, study: str, evidence_hash: str, timestamp_utc: str, *,
                  reviewer_role: str = "", reviewer_ref: str = "",
                  decision: str = "", is_synthetic: bool = False,
                  prev_hash: str = "") -> Optional[str]:
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
        _signature_payload(gate_id, study, evidence_hash, timestamp_utc, group, reviewer_ref,
                           decision, is_synthetic, prev_hash),
        hashlib.sha256,
    ).hexdigest()
    return f"{_SIGNATURE_SCHEME}:{scope}:{mac}"


# Các trường mà một bản ghi ledger dùng để TỰ KHAI rằng agent đã tạo/duyệt nó
# (runtime/schemas.py::ApprovalRecord có artifact_creator_agent/reviewer_agent;
# `created_by_agent` là tham số của add_approval nhưng vẫn có thể xuất hiện trong JSON
# dựng tay). Xem giới hạn ở docstring ledger_approved() điều kiện (2).
_AGENT_AUTHORSHIP_FIELDS = ("created_by_agent", "reviewer_agent", "artifact_creator_agent")


def _declares_agent_authorship(record: Dict[str, Any]) -> bool:
    """True nếu bản ghi TỰ KHAI do agent tạo/duyệt. KHÔNG phải cơ chế chống giả mạo —
    kẻ dựng ledger bằng tay chỉ cần bỏ trống các trường này. Chỉ chặn bản ghi trung thực."""
    return any(bool(record.get(f)) for f in _AGENT_AUTHORSHIP_FIELDS)


def _record_reviewer_ref(record: Dict[str, Any]) -> Tuple[str, bool]:
    """Mã định danh người duyệt trong một bản ghi ledger.

    CẨN TRỌNG (bẫy thật, suýt tự gây lỗi khi vá 2026-07-26): tên trường CHUẨN trong
    runtime/schemas.py::ApprovalRecord là `reviewer_identity_reference`, KHÔNG phải
    `reviewer_ref` — `reviewer_ref` chỉ là tên THAM SỐ của factory
    ApprovalLedger.make_human_approval(). Đọc nhầm khóa sẽ luôn ra chuỗi rỗng, làm mọi
    chữ ký thật (ký kèm reviewer_ref có giá trị) không bao giờ khớp. Đọc trường chuẩn
    trước, chấp nhận `reviewer_ref` như bí danh cho các bản ghi/test dựng tay.

    VÁ 2026-07-26 vòng 2 (red-team độc lập, liêm chính-kiểm toán): bản đầu lấy khóa TRUTHY
    ĐẦU TIÊN, nên một bản ghi mang ĐỒNG THỜI hai khóa khác giá trị
    (reviewer_identity_reference="dr-x" + reviewer_ref="NGƯỜI-KHÁC-HẲN") vẫn xác minh ĐẠT
    trong khi danh tính HIỂN THỊ khác danh tính ĐƯỢC KÝ — sổ cái nói một đằng, chữ ký bảo
    đảm một nẻo. Không phải vượt cổng, nhưng phá đúng thứ ledger sinh ra để làm: truy vết
    ai đã duyệt. Nay trả (ref, ok) và ok=False khi hai khóa mâu thuẫn → xác minh từ chối.

    Trả về: (mã_định_danh, hợp_lệ)."""
    canonical = record.get("reviewer_identity_reference")
    alias = record.get("reviewer_ref")
    if canonical and alias and str(canonical) != str(alias):
        return "", False
    return str(canonical or alias or ""), True


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
    KHÔNG có khóa riêng của nhóm đó cũng bị từ chối (chống hạ cấp về khóa chung).

    VÁ 2026-07-26 vòng 2 (red-team độc lập): hàm PHẢI trả False cho mọi đầu vào dị dạng,
    KHÔNG được ném exception — nó là chốt fail-closed, caller chỉ xử lý True/False; một
    ngoại lệ lọt ra sẽ thành crash pipeline thay vì "chưa duyệt". Hai ca đã tái hiện được:
    (a) MAC chứa ký tự NGOÀI ASCII → hmac.compare_digest ném TypeError; (b) bản ghi không
    phải dict / trường không phải chuỗi → AttributeError."""
    if not isinstance(record, dict):
        return False
    sig = record.get("approver_signature")
    if not isinstance(sig, str) or not sig:
        return False
    parts = sig.split(":")
    if len(parts) != 3 or parts[0] != _SIGNATURE_SCHEME:
        return False
    claimed_scope, mac_hex = parts[1], parts[2]
    if claimed_scope not in (_SIGNATURE_SCOPE_ROLE, _SIGNATURE_SCOPE_SHARED):
        return False
    # compare_digest CHỈ nhận chuỗi ASCII — chặn sớm thay vì để nó ném TypeError.
    if not mac_hex or not mac_hex.isascii():
        return False
    reviewer_ref, ref_ok = _record_reviewer_ref(record)
    if not ref_ok:
        return False  # bản ghi mang 2 mã định danh mâu thuẫn — xem _record_reviewer_ref
    role_raw = record.get("reviewer_role", "")
    group = role_group_for(role_raw if isinstance(role_raw, str) else "") or ""
    key, actual_scope = _load_signing_key(group or None)
    if not key or actual_scope != claimed_scope:
        return False
    try:
        expected = hmac.new(
            key.encode("utf-8"),
            _signature_payload(str(record.get("gate_id", "") or ""), study,
                               str(record.get("evidence_hash", "") or ""),
                               str(record.get("timestamp_utc", "") or ""), group, reviewer_ref,
                               str(record.get("decision", "") or ""),
                               bool(record.get("is_synthetic")),
                               str(record.get("prev_hash") or "")),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, mac_hex)
    except (TypeError, ValueError, AttributeError):
        return False


def _parse_iso_utc(value: Any) -> Optional[datetime]:
    """Phân giải timestamp_utc thành datetime có múi giờ; None nếu không hợp lệ.

    THÊM 2026-07-27 vòng 5: trước đây thứ tự thời gian được quyết bằng SO CHUỖI THÔ
    (`str(r.get("timestamp_utc") or "")`). Vòng kiểm định thứ tư chỉ ra ba hệ quả thật:
    timestamp rỗng/None sắp lên ĐẦU nên bản thu hồi bị coi là cũ nhất (mất tác dụng);
    "2026-07-27 11:00:00" (dấu cách < 'T') là định dạng trông rất hợp lý nhưng im lặng
    không thu hồi được; và một timestamp tương lai xa làm phê duyệt VĨNH VIỄN không thu
    hồi nổi. Nay bắt buộc ISO-8601 phân giải được — không phân giải được thì bản ghi bị
    coi là BẤT THƯỜNG (fail-closed), không phải "xếp cuối bảng"."""
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _latest_authoritative_record(records: Any, gate_id: str, study: str,
                                 root: Path) -> Optional[Dict[str, Any]]:
    """Bản ghi MỚI NHẤT có thẩm quyền quyết định trạng thái một cổng — bất kể nó là
    APPROVED hay REJECTED. Trả None nếu không có bản ghi nào đủ điều kiện được TÍNH.

    THÊM 2026-07-27 vòng 4 để đóng hai lỗi mà workflow kiểm định vòng 3 tìm ra:
      (A) THU HỒI KHÔNG CÓ TÁC DỤNG — nơi gọi trước đây lọc decision=="APPROVED" TRƯỚC
          khi chọn bản mới nhất, nên một REJECTED ký hợp lệ về sau bị vứt đi trước khi
          kịp được nhìn tới. Nay việc chọn "bản mới nhất" và việc xét "quyết định là gì"
          được TÁCH RIÊNG: hàm này chỉ chọn, nơi gọi mới xét.
      (B) HAI NƠI ĐỌC LEDGER LỆCH NHAU — approving_signature_scope() (phục vụ công bố
          mức bảo đảm trong gói nộp G10) trước đây lọc KHÁC ledger_approved(): không
          kiểm vai trò, không kiểm agent, và KHÔNG XÁC MINH CHỮ KÝ. Hệ quả: chỉ cần
          nối thêm một dòng JSON rác tự khai `v3:role:...` là tắt được đoạn cảnh báo
          "cổng này ký bằng khóa chung" — tức tính năng minh bạch vừa thêm ở vòng 3 bị
          vô hiệu bằng một thao tác KHÔNG CẦN KHÓA. Nay cả hai nơi dùng CHUNG hàm này,
          nên không thể lệch nhau nữa.

    ★★ VÁ 2026-07-27 vòng 5 — BẤT THƯỜNG PHẢI FAIL-CLOSED, KHÔNG ĐƯỢC LỜ ĐI.
    Bản vòng 4 (ngay trên) đòi bản REJECTED cũng phải có chữ ký hợp lệ mới được TÍNH —
    ý định đúng (chống ai đó ghi một dòng REJECTED giả để chặn oan phê duyệt thật), nhưng
    CÁCH LÀM sai: bản ghi KHÔNG qua kiểm bị coi như KHÔNG TỒN TẠI. Vòng kiểm định thứ tư
    khai thác đúng chỗ đó: **đổi MỘT ký tự hex trong chữ ký của bản TỪ CHỐI** (không cần
    khóa) là bản thu hồi rơi khỏi danh sách → cổng MỞ LẠI, gói nộp in "✅ Đã qua cổng G8
    (bình duyệt độc lập)", còn dòng REJECTED vẫn nằm nguyên trong file mà gói nộp không hề
    nhắc tới. Sáu biến thể đều được: sửa MAC, thêm created_by_agent, thêm reviewer_agent,
    đổi reviewer_ref, đổi reviewer_role sang nhóm khác, thêm khoảng trắng vào gate_id.
    ⇒ Kết cục: **phê duyệt thì chống-sửa-đổi (fail-closed), còn thu hồi thì XÓA-ĐƯỢC
    (fail-OPEN)** — đúng NGƯỢC chiều an toàn, và đúng với kẻ tấn công mà cơ chế chữ ký
    sinh ra để chống (người ghi được ledger nhưng không có khóa).

    Nguyên tắc thay thế: **ledger chỉ do approve_gate.py ghi, và nó LUÔN ký + LUÔN kiểm
    vai trò.** Vậy một bản ghi không xác minh được, sai vai trò, tự khai do agent tạo, hay
    có timestamp không phải ISO-8601 là DẤU HIỆU BẤT THƯỜNG — không phải "rác vô hại".
    Gặp bất thường ⇒ coi như CHƯA DUYỆT (trả None), thay vì lặng lẽ bỏ qua rồi tin phần
    còn lại. Hướng sai lệch mới là AN TOÀN: kẻ tấn công chỉ có thể làm cổng ĐÓNG oan (bác
    sĩ nhìn thấy, kiểm ledger, gỡ dòng lạ) chứ không MỞ được cổng đã thu hồi (âm thầm,
    không ai biết).

    Trả None khi: không có bản ghi nào cho cổng, HOẶC phát hiện bất thường ở BẤT KỲ bản
    ghi nào của cổng đó.
    """
    record, _reason = _diagnose_gate_records(records, gate_id, study, root)
    return record


_SEAL_GATE_ID = "LEDGER_SEAL"   # gate_id giả lập, chỉ để tái dùng cơ chế ký sẵn có


def ledger_seal_path(study: str, repo_root: Optional[Path] = None) -> Path:
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    return root / "exports" / str(study) / "approval_ledger.seal.json"


def compute_ledger_tip(records: Any) -> Tuple[int, str]:
    """(số bản ghi, vân tay bản ghi CUỐI) — trạng thái 'đuôi' của sổ cái."""
    if not isinstance(records, list):
        return 0, _CHAIN_GENESIS
    last = records[-1] if records else None
    return len(records), chain_prev_hash(last if isinstance(last, dict) else None)


def write_ledger_seal(study: str, records: Any, repo_root: Optional[Path] = None) -> bool:
    """Ghi CON DẤU NIÊM PHONG cho sổ cái. True nếu ký được (máy có khóa).

    ★ Vì sao cần, dù đã có chuỗi băm: chuỗi bắt được xóa ở GIỮA và đảo thứ tự, nhưng
    KHÔNG bắt được CẮT ĐUÔI — xóa bản ghi cuối cùng thì phần còn lại vẫn là một chuỗi
    hoàn hảo. Đây là bài toán kinh điển của mọi sổ append-only: muốn biết sổ có bị cắt
    ngắn hay không thì phải có một MỐC NEO NGOÀI FILE. Đúng đòn nguy hiểm nhất trong bối
    cảnh này: gỡ bản ghi THU HỒI mới nhất để mở lại một cổng đã bị đóng.

    Con dấu ghi (số bản ghi, vân tay đuôi) và được KÝ. Kẻ không có khóa muốn cắt đuôi
    trót lọt thì phải làm giả con dấu — bất khả. Xóa luôn file dấu cũng không thoát: sổ
    cái có bản ghi v4 mà THIẾU dấu chính là một bất thường (xem verify_ledger_seal)."""
    count, tip = compute_ledger_tip(records)
    sealed_at = datetime.now(timezone.utc).isoformat()
    sig = sign_approval(_SEAL_GATE_ID, str(study), tip, sealed_at, decision=str(count))
    if not sig:
        return False
    p = ledger_seal_path(study, repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "kind": "approval_ledger_seal",
        "record_count": count,
        "tip_hash": tip,
        "sealed_at_utc": sealed_at,
        "seal_signature": sig,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def verify_ledger_seal(study: str, records: Any,
                       repo_root: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """Đối chiếu sổ cái với con dấu niêm phong: (khớp?, lý do lệch)."""
    # ★ VÁ 2026-07-27 (tự tấn công bản vá của chính mình, ngay sau khi triển khai):
    # Bản đầu chỉ đòi con dấu khi sổ cái CÓ bản ghi mang prev_hash ("sổ cái đời cũ thì
    # miễn"). Quy tắc khoan dung đó BỊ LỢI DỤNG ĐƯỢC — đã tái hiện: kẻ tấn công (1) cắt
    # đuôi để gỡ bản THU HỒI, (2) gỡ luôn trường prev_hash khỏi bản ghi còn lại, (3) xóa
    # file con dấu ⇒ sổ cái trông y hệt đời cũ, né được CẢ chuỗi băm LẪN con dấu, cổng mở
    # lại, không một dòng cảnh báo nào. Tức là toàn bộ cơ chế vô nghĩa trước đúng kẻ tấn
    # công nó nhắm tới.
    # (Đòn này chỉ hiệu quả trên bản ghi ĐẦU chuỗi, vì prev_hash của nó vốn là GENESIS nên
    # gỡ đi không làm hỏng chữ ký; với bản ghi thứ hai trở đi, gỡ prev_hash là chữ ký vỡ
    # ngay. Nhưng "chỉ bản ghi đầu" vẫn đủ để xóa sạch một sổ cái 2 dòng.)
    # ⇒ Nay: MỌI sổ cái KHÔNG RỖNG đều phải có con dấu. An toàn để siết vì tại thời điểm
    # này KHÔNG có approval_ledger.json nào tồn tại trên đĩa — "sổ cái đời cũ" là trường
    # hợp phòng xa cho một thứ chưa từng tồn tại, và cái giá của nó là thủng cả cơ chế.
    # Đường phục hồi vẫn rõ ràng: ký lại bằng approve_gate.py sẽ niêm phong lại.
    if not isinstance(records, list) or not records:
        return True, None          # sổ cái rỗng — chưa có gì để niêm phong
    if not signing_key_configured(None):
        # Máy chưa có khóa thì KHÔNG niêm phong được mà cũng không xác minh được dấu.
        # Đòi con dấu ở đây là chặn oan; đường fail-closed cho trường hợp này đã do
        # quy tắc "chưa có khóa ⇒ chỉ đề tài synthetic_test mới đi tiếp" lo (xem
        # _diagnose_gate_records), nên không có kẽ hở.
        return True, None
    p = ledger_seal_path(study, repo_root)
    if not p.exists():
        return False, (
            f"sổ cái có {len(records)} bản ghi nhưng THIẾU file niêm phong {p.name}. "
            "Con dấu bị xóa (hoặc sổ cái được tạo ngoài approve_gate.py) — đây chính là "
            "cách che giấu việc CẮT ĐUÔI sổ cái, gỡ bản ghi cuối vốn thường là một quyết "
            "định THU HỒI."
        )
    try:
        seal = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False, f"không đọc được {p.name} (file hỏng?)"
    if not isinstance(seal, dict):
        return False, f"{p.name} không đúng định dạng"
    count, tip = compute_ledger_tip(records)
    probe = {
        "gate_id": _SEAL_GATE_ID, "evidence_hash": str(seal.get("tip_hash") or ""),
        "timestamp_utc": str(seal.get("sealed_at_utc") or ""),
        "decision": str(seal.get("record_count")),
        "reviewer_role": "", "reviewer_identity_reference": "",
        "approver_signature": seal.get("seal_signature"),
    }
    if signing_key_configured(None) and not verify_approval_signature(probe, str(study)):
        return False, (f"chữ ký của {p.name} KHÔNG xác minh được bằng khóa trên máy này "
                       "(dấu bị sửa, hoặc niêm phong ở máy/khóa khác)")
    if int(seal.get("record_count") or -1) != count or str(seal.get("tip_hash")) != tip:
        return False, (
            f"SỔ CÁI KHÔNG KHỚP CON DẤU — dấu niêm phong {seal.get('record_count')} bản ghi "
            f"(đuôi {str(seal.get('tip_hash'))[:12]}…) nhưng file hiện có {count} bản ghi "
            f"(đuôi {tip[:12]}…). Có bản ghi ĐÃ BỊ XÓA KHỎI CUỐI SỔ — rất có thể là một "
            "quyết định THU HỒI vừa bị gỡ đi."
        )
    return True, None


def verify_ledger_chain(records: Any) -> Tuple[bool, Optional[str]]:
    """Kiểm CHUỖI BĂM của sổ cái: (còn nguyên vẹn?, lý do đứt nếu có).

    Xóa một bản ghi, đảo thứ tự, hay chèn thêm đều làm bản ghi KẾ TIẾP trỏ tới một vân tay
    không khớp ⇒ phát hiện được. Đây là thứ chữ ký MỘT MÌNH không làm được: chữ ký chứng
    minh từng bản ghi không bị sửa, nhưng một sổ cái bị CẮT BỚT trông y hệt một sổ cái ngắn.

    Bỏ qua (không coi là đứt) các bản ghi CHƯA có prev_hash — sổ cái ghi bằng phiên bản
    trước khi có chuỗi. Chúng chỉ không được chuỗi bảo vệ, chứ không phải dấu hiệu bị sửa;
    coi chúng là đứt xích sẽ khóa oan mọi đề tài cũ (đúng lỗi "siết quá tay" đã mắc 3 lần).
    """
    if not isinstance(records, list):
        return False, "sổ cái không phải danh sách bản ghi"
    prev: Optional[Dict[str, Any]] = None
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            prev = None          # dòng rác cắt chuỗi — đã báo ở nơi khác, không nhân đôi lỗi
            continue
        declared = rec.get("prev_hash")
        if declared is None:
            prev = rec           # bản ghi thời chưa có chuỗi — bỏ qua, vẫn nối tiếp
            continue
        expected = chain_prev_hash(prev)
        if str(declared) != expected:
            return False, (
                f"ĐỨT CHUỖI SỔ CÁI tại bản ghi #{idx + 1} (cổng {rec.get('gate_id')!r}, "
                f"{rec.get('timestamp_utc')}): nó ghi mắt xích {str(declared)[:12]}… nhưng bản "
                f"ghi đứng trước hiện có vân tay {expected[:12]}…. Nghĩa là có bản ghi ĐÃ BỊ "
                "XÓA, bị chèn thêm, hoặc bị đảo thứ tự — thứ mà chữ ký một mình không phát "
                "hiện được. Rất có thể một quyết định THU HỒI đã bị gỡ khỏi sổ cái."
            )
        prev = rec
    return True, None


def _diagnose_gate_records(records: Any, gate_id: str, study: str,
                           root: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Như _latest_authoritative_record() nhưng trả kèm LÝ DO khi không có bản ghi hợp lệ.

    THÊM 2026-07-27 vòng 5b — tự vá một khiếm khuyết của chính thiết kế vòng 5, không chờ
    vòng kiểm định sau chỉ ra. Quy tắc "bất thường ⇒ coi như CHƯA DUYỆT" là đúng hướng an
    toàn, NHƯNG nếu chốt kiểm chỉ trả về `False` trống không thì bác sĩ thấy đúng một câu
    "chưa có phê duyệt" — không phân biệt được ba tình huống KHÁC HẲN NHAU:
      · thật sự chưa ai duyệt (bình thường, cứ đi duyệt);
      · đã duyệt rồi nhưng bị THU HỒI (phải hỏi lại hội đồng — KHÔNG được tự đi tiếp);
      · sổ cái có dấu hiệu BỊ SỬA (phải điều tra, tuyệt đối không bỏ qua).
    Một cổng đóng mà không nói lý do sẽ đẩy người dùng bực bội sang dùng cờ `--i-confirm-*`
    / `--i-know-*-not-*` — tức chính cơ chế an toàn lại tạo ra đường vòng quanh nó. Trong
    hệ y khoa, "chặn mà không giải thích" là một vấn đề AN TOÀN, không phải chuyện tiện dụng.
    """
    if not isinstance(records, list):
        return None, "approval_ledger.json không phải danh sách bản ghi (file hỏng?)"

    key_available = signing_key_configured(None)

    # ★★ VÁ 2026-07-27 vòng 6 — QUÉT TOÀN SỔ CÁI TRƯỚC KHI LỌC THEO CỔNG.
    # Vòng kiểm định thứ năm phá được vòng 5 ở đúng chỗ này: bộ lọc `gate_id` chạy TRƯỚC
    # các phép kiểm bất thường, mà "bản ghi này thuộc cổng nào" lại đọc từ dữ liệu CHƯA
    # XÁC MINH. Hệ quả: sửa MỘT ký tự trong gate_id của bản THU HỒI ("G8"→"g8", hoặc chèn
    # một ký tự vô hình U+200B), hay biến nó thành chuỗi JSON thay vì object, là bản ghi
    # đó rơi khỏi tầm nhìn TRƯỚC KHI chữ ký kịp được kiểm → cổng đã thu hồi MỞ LẠI, âm
    # thầm. Đúng điều mà chú thích vòng 5 khẳng định là không thể.
    # Nay: bất kỳ mục nào trong sổ cái KHÔNG phải object, hoặc có chữ ký KHÔNG xác minh
    # được, đều là bất thường của CẢ SỔ CÁI — không cần biết nó tự nhận thuộc cổng nào.
    # (gate_id nằm trong nội dung ký, nên sửa gate_id ⇒ chữ ký hỏng ⇒ bị bắt tại đây.)
    def _same_gate_raw(value: Any) -> bool:
        s = unicodedata.normalize("NFC", str(value or ""))
        s = "".join(ch for ch in s if ch.isprintable() and not ch.isspace())
        return s.casefold() == gate_id.strip().casefold()

    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            return None, (f"BẤT THƯỜNG — mục #{idx + 1} trong approval_ledger.json không phải "
                          "một bản ghi (object). Sổ cái có dấu hiệu bị sửa tay.")
        # ★ VÁ 2026-07-27 vòng 7 — SỬA REGRESSION DO CHÍNH VÒNG 6 GÂY RA.
        # Vòng 6 coi MỌI bản ghi không xác minh được là bất thường của CẢ sổ cái. Điều đó
        # PHÁ HỎNG kịch bản hai máy mà chính dự án tài liệu hóa là BÌNH THƯỜNG:
        # setup_gate_approval_key.py ghi rõ "mỗi máy một khóa, khóa khác nhau là BÌNH
        # THƯỜNG", còn ~/.ebm-secrets/ nằm NGOÀI OneDrive nên không đồng bộ — vậy một
        # approval_ledger.json dùng chung HỢP LỆ chứa bản ghi ký bằng nhiều khóa. Đã tái
        # hiện: ký G2 trên Mac + G8 trên Windows ⇒ trên Mac CẢ HAI cổng đều bị chặn, kể
        # cả G2 vốn ký bằng đúng khóa máy đó. Bác sĩ bị khóa khỏi chính đề tài của mình,
        # không lối thoát ngoài sửa tay sổ cái kiểm toán — đúng thứ đẩy người ta sang cờ
        # bỏ qua. "Siết quá tay làm hỏng việc hợp lệ" cũng là một lỗi an toàn.
        #
        # Cách phân biệt ĐÚNG (không cần phân biệt được "khóa lạ" với "bị sửa" bằng mật mã):
        # thử xác minh bản ghi NHƯ THỂ nó thuộc cổng ĐANG XÉT. Vì gate_id nằm trong nội
        # dung ký, phép thử này chỉ khớp khi bản ghi VỐN LÀ của cổng này rồi bị đổi nhãn
        # để giấu — đúng đòn tấn công vòng 5. Bản ghi của máy khác (khóa khác) sẽ KHÔNG
        # khớp, nên được bỏ qua đúng như trước, không làm hỏng cổng khác.
        if key_available and not _same_gate_raw(rec.get("gate_id")):
            probe = dict(rec)
            probe["gate_id"] = gate_id
            if verify_approval_signature(probe, study):
                return None, (
                    f"BẤT THƯỜNG — mục #{idx + 1} tự nhận thuộc cổng {rec.get('gate_id')!r}, "
                    f"nhưng chữ ký của nó khớp CHÍNH XÁC với cổng {gate_id}. Đây là một bản ghi "
                    f"của {gate_id} đã bị ĐỔI NHÃN để giấu khỏi cổng này (rất có thể là một "
                    "quyết định THU HỒI). KHÔNG tự bỏ qua — đối chiếu sổ cái với người đã duyệt."
                )

    def _same_gate(value: Any) -> bool:
        """So khớp gate_id CHỐNG NÉ: bỏ ký tự vô hình/điều khiển, chuẩn hóa NFC, không
        phân biệt hoa-thường — để 'g8' hay 'G8<U+200B>' không lọt thành cổng khác."""
        s = unicodedata.normalize("NFC", str(value or ""))
        s = "".join(ch for ch in s if ch.isprintable() and not ch.isspace())
        return s.casefold() == gate_id.strip().casefold()

    gate_recs = [r for r in records if _same_gate(r.get("gate_id"))]
    if not gate_recs:
        return None, f"chưa có bản ghi phê duyệt nào cho cổng {gate_id}"
    # Chuỗi băm kiểm TRƯỚC mọi thứ khác: nó bắt được loại tấn công mà các phép kiểm bên
    # dưới (vốn chỉ soi từng bản ghi CÒN LẠI) không thể thấy — bản ghi đã bị XÓA.
    chain_ok, chain_reason = verify_ledger_chain(records)
    if not chain_ok:
        return None, f"BẤT THƯỜNG — {chain_reason}"
    # Con dấu bắt CẮT ĐUÔI — thứ chuỗi băm một mình không thấy (xóa bản ghi CUỐI vẫn để
    # lại một chuỗi hoàn hảo). Đây đúng là đòn nguy hiểm nhất: gỡ bản THU HỒI mới nhất.
    seal_ok, seal_reason = verify_ledger_seal(study, records, root)
    if not seal_ok:
        return None, (f"BẤT THƯỜNG — {seal_reason} Nếu đây là sổ cái hợp lệ vừa được ghi ở "
                      "máy/khóa khác, hãy KÝ LẠI cổng này trên máy hiện tại để niêm phong lại.")

    if not key_available and not is_synthetic_test_study(study, root):
        return None, (
            "máy này CHƯA cấu hình khóa ký (chạy tools/setup_gate_approval_key.py) nên "
            "không xác minh được phê duyệt nào. Chỉ đề tài đã tự tay đánh dấu "
            "study_kind=synthetic_test mới được bỏ qua bước ký."
        )

    # ★★ VÁ 2026-07-27 vòng 8 — QUY TẮC THEO THỜI GIAN, thay cho "bất kỳ bản ghi lạ nào
    # cũng khóa cổng". Vòng kiểm định thứ sáu chứng minh quy tắc cũ tạo ra trạng thái
    # KHÔNG THỂ PHỤC HỒI trong chính quy trình mà tài liệu dự án hướng dẫn:
    #   · cùng một cổng được ký trên CẢ HAI máy (mỗi máy một khóa — tài liệu nói là bình
    #     thường) ⇒ CẢ HAI máy đều thấy False, đề tài "vỡ đôi", không máy nào qua được;
    #   · ĐỔI KHÓA đúng như setup_gate_approval_key.py chỉ dẫn ("tự tay xóa file cũ rồi
    #     chạy lại") ⇒ cổng chết, ký lại bằng khóa MỚI cũng KHÔNG cứu được;
    #   · bản ghi KHÔNG chữ ký mà chính approve_gate.py ghi ra khi máy chưa có khóa
    #     (nó chỉ cảnh báo rồi vẫn ghi) ⇒ cổng chết vĩnh viễn;
    #   · chữ ký định dạng v2 cũ ⇒ cổng chết.
    # Và KHÔNG có công cụ phục hồi nào (`ls tools/ | grep -i ledger|repair|recover` rỗng);
    # lối ra duy nhất là sửa tay sổ cái kiểm toán — đúng thứ hệ thống sinh ra để chống.
    #
    # Quy tắc mới, dựa trên một nhận xét đơn giản: MỘT BẢN THU HỒI PHẢI ĐẾN SAU BẢN PHÊ
    # DUYỆT NÓ THU HỒI. Vậy một bản ghi lạ CŨ HƠN bản phê duyệt hợp lệ mới nhất KHÔNG THỂ
    # là một quyết định thu hồi bị giấu — nó chỉ là dấu vết lịch sử (khóa cũ, máy khác,
    # định dạng cũ). Chỉ bản ghi lạ MỚI HƠN mới có thể đang che giấu một thu hồi ⇒ chỉ
    # trường hợp đó mới khóa cổng.
    # Hệ quả quan trọng: KÝ LẠI TRÊN MÁY NÀY LUÔN LÀ ĐƯỜNG PHỤC HỒI — bản ghi mới hợp lệ
    # đẩy mọi dấu vết lạ vào quá khứ. Đó chính là lối thoát mà quy tắc cũ không có.
    # Đồng thời vẫn chặn được đòn của vòng 5/6 (làm hỏng một bản THU HỒI để nó "biến
    # mất"): bản thu hồi bị sửa luôn MỚI HƠN bản phê duyệt nó nhắm tới, nên vẫn khóa cổng.
    verified: list = []
    suspects: list = []
    for idx, rec in enumerate(gate_recs):
        where = f"bản ghi #{idx + 1}/{len(gate_recs)} của {gate_id}"
        ts = _parse_iso_utc(rec.get("timestamp_utc"))
        role_raw = rec.get("reviewer_role")
        problem = None
        if _declares_agent_authorship(rec):
            problem = (f"{where} tự khai do agent tạo/duyệt — approve_gate.py không bao giờ "
                       "ghi các trường này")
        elif not reviewer_role_satisfies_gate(gate_id, role_raw if isinstance(role_raw, str) else ""):
            problem = (f"{where} có reviewer_role={role_raw!r} không thuộc nhóm bắt buộc của "
                       f"{gate_id} ({required_reviewer_role_hint(gate_id)})")
        elif ts is None:
            problem = (f"{where} có timestamp_utc={rec.get('timestamp_utc')!r} "
                       "không phải ISO-8601 hợp lệ")
        elif key_available and not verify_approval_signature(rec, study):
            problem = (f"{where} có chữ ký KHÔNG xác minh được bằng khóa trên máy này "
                       "(bị sửa sau khi ký, ký bằng máy/khóa khác, hoặc khóa đã đổi)")
        if problem:
            suspects.append((ts, problem))
        else:
            verified.append((ts, rec))

    newest_verified_ts = max((t for t, _ in verified), default=None)
    for ts, problem in suspects:
        # Bản ghi lạ KHÔNG phân giải được thời điểm ⇒ không loại trừ được khả năng nó mới
        # hơn ⇒ vẫn khóa (fail-closed đúng chỗ, không phải khóa tràn lan).
        if newest_verified_ts is None or ts is None or ts > newest_verified_ts:
            return None, (
                f"BẤT THƯỜNG — {problem}. Bản ghi này KHÔNG cũ hơn phê duyệt hợp lệ mới nhất, "
                "nên không loại trừ được khả năng nó đang che giấu một quyết định THU HỒI. "
                "KHÔNG tự bỏ qua — đối chiếu sổ cái với người đã duyệt. Nếu đây là dấu vết "
                "hợp lệ từ máy/khóa khác, hãy KÝ LẠI cổng này trên máy hiện tại "
                "(tools/approve_gate.py) — bản ghi mới sẽ đưa dấu vết cũ về quá khứ."
            )

    parsed = verified

    # Chọn bản mới nhất. HÒA thì ưu tiên REJECTED — hướng an toàn: hai bản ghi cùng giây
    # thì thứ tự dòng trong file KHÔNG được quyết định cổng mở hay đóng (sorted() ổn định
    # nên trước đây đảo 2 dòng JSON là lật được cổng mà không đổi một byte đã ký nào).
    # Khóa phụ: APPROVED = 0, mọi quyết định khác = 1. Sắp tăng dần rồi lấy phần tử CUỐI
    # ⇒ khi hòa thời điểm, bản KHÔNG-phải-APPROVED (thu hồi/từ chối) được chọn.
    parsed.sort(key=lambda p: (p[0], 0 if str(p[1].get("decision")) == "APPROVED" else 1))
    latest = parsed[-1][1]
    if str(latest.get("decision") or "").strip().upper() != "APPROVED":
        return latest, (
            f"cổng {gate_id} đã bị THU HỒI/TỪ CHỐI — bản ghi mới nhất "
            f"({latest.get('timestamp_utc')}) mang quyết định "
            f"{latest.get('decision')!r} của {latest.get('reviewer_role')}. "
            "Phải xin phê duyệt MỚI, không được dùng phê duyệt cũ trước đó."
        )
    return latest, None


def gate_block_reason(gate_id: str, study: str, artifact_path: Path,
                      repo_root: Optional[Path] = None) -> Optional[str]:
    """Lý do NGƯỜI ĐỌC HIỂU ĐƯỢC khi ledger_approved() trả False; None nếu cổng thật sự đạt.

    Dùng ở mọi nơi báo cho bác sĩ biết cổng chưa qua — để phân biệt "chưa ai duyệt" (bình
    thường) với "đã bị THU HỒI" (phải hỏi lại hội đồng) và "sổ cái có dấu hiệu BỊ SỬA"
    (phải điều tra). Xem lý do đầy đủ ở docstring _diagnose_gate_records()."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    ledger_p = root / "exports" / str(study) / "approval_ledger.json"
    if not ledger_p.exists():
        return f"chưa có sổ cái phê duyệt ({ledger_p.name}) cho đề tài này"
    if not Path(artifact_path).exists():
        return f"không thấy artifact cần đối chiếu: {artifact_path}"
    try:
        records = json.loads(ledger_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return f"không đọc được {ledger_p.name} ({exc.__class__.__name__}) — file hỏng?"
    latest, reason = _diagnose_gate_records(records, gate_id, str(study), root)
    if reason:
        return reason
    if latest is None:
        return f"chưa có bản ghi phê duyệt hợp lệ cho cổng {gate_id}"
    if latest.get("is_synthetic"):
        return (f"cổng {gate_id} chỉ có phê duyệt MÔ PHỎNG (is_synthetic) — "
                "không phải phê duyệt của người thật, không dùng cho đề tài thật")
    try:
        actual_hash = hashlib.sha256(Path(artifact_path).read_bytes()).hexdigest()
    except (OSError, ValueError):
        return f"không đọc được nội dung artifact để đối chiếu hash: {artifact_path}"
    if actual_hash != latest.get("evidence_hash"):
        return (f"NỘI DUNG ĐÃ ĐỔI SAU KHI DUYỆT — {Path(artifact_path).name} hiện có hash "
                f"{actual_hash[:12]}… nhưng bản duyệt gắn với {str(latest.get('evidence_hash'))[:12]}…. "
                "Phải trình lại bản đã sửa cho người duyệt.")
    return None


def approving_signature_scope(gate_id: str, study: str,
                              repo_root: Optional[Path] = None) -> Optional[str]:
    """Phạm vi khóa đã ký bản ghi phê duyệt MỚI NHẤT của một cổng: 'role' | 'shared' | None.

    THÊM 2026-07-27 để đóng phát hiện của workflow kiểm định: trường "phạm vi" được GHI vào
    chữ ký nhưng KHÔNG AI ĐỌC — `signature_scope()` không có một nơi dùng thật nào ngoài
    test. Nghĩa là gói nộp G10 in "✅ Đã qua cổng G8 (bình duyệt độc lập)" y hệt nhau dù
    G2+G8+G9 đều được ký bằng CÙNG MỘT khóa chung của một người. Một gói nộp KHÔNG ĐƯỢC
    khẳng định có bình duyệt độc lập khi hệ không biết điều đó có thật hay không.
    Hàm này cấp dữ liệu để nơi phát hành nói ĐÚNG mức bảo đảm."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    ledger_p = root / "exports" / str(study) / "approval_ledger.json"
    if not ledger_p.exists():
        return None
    try:
        records = json.loads(ledger_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    # VÁ 2026-07-27 vòng 4: dùng CHUNG _latest_authoritative_record() với ledger_approved()
    # — trước đây hàm này lọc riêng (không kiểm vai trò/agent, KHÔNG xác minh chữ ký), nên
    # một dòng JSON rác tự khai "v3:role:..." nối vào ledger là tắt được cảnh báo "ký bằng
    # khóa chung" mà không cần khóa. Hai nơi đọc cùng một sổ mà lọc khác nhau thì sớm muộn
    # cũng nói hai chuyện khác nhau về cùng một cổng.
    latest = _latest_authoritative_record(records, gate_id, str(study), root)
    if latest is None or latest.get("decision") != "APPROVED":
        return None
    # VÁ 2026-07-27 vòng 5: thêm kiểm is_synthetic. Vòng kiểm định thứ tư chỉ ra hai nơi
    # VẪN lệch nhau dù đã dùng chung hàm chọn: ledger_approved() từ chối bản ghi
    # is_synthetic (phê duyệt MÔ PHỎNG, không phải người thật duyệt) còn hàm này thì không
    # — nên gói nộp G10 công bố "cổng G2 đã ký (shared)" cho một đề tài mà cổng đạo đức
    # chỉ có phê duyệt mô phỏng. Trong hồ sơ nghiên cứu người thật, dòng đó đọc thành
    # "cổng đạo đức đã có phê duyệt mật mã" — sai sự thật theo hướng nguy hiểm nhất.
    if latest.get("is_synthetic"):
        return None
    return signature_scope(latest)


def is_synthetic_test_study(study: str, repo_root: Optional[Path] = None) -> bool:
    """True CHỈ khi đề tài đã được đánh dấu TƯỜNG MINH study_kind == 'synthetic_test'
    (qua tools/mark_study_synthetic.py) VÀ không nằm trong denylist đề tài thật.

    Đây là ngoại lệ DUY NHẤT còn được đi tiếp khi máy chưa cấu hình khóa ký — nên nó
    phải chặt bằng đúng resolve_synthetic_study_dir().

    VÁ 2026-07-26 vòng 2 (red-team ĐỘC LẬP tái hiện được, HIGH): bản đầu tiên của hàm này
    kiểm denylist trên CHUỖI THÔ `study` rồi mới ghép đường dẫn, nên các biến thể trỏ ĐÚNG
    thư mục đề tài thật vẫn lọt: `is_real_study_denylisted("./hai-long-benh-nhan-C1a-BVQY175")`
    → False (chuỗi khác), trong khi `load_study_meta` giải ra ĐÚNG thư mục thật đó → hàm
    trả True cho một đề tài NGƯỜI THẬT. Đã tái hiện: "./TÊN", "TÊN/", "TÊN/." đều cho
    {G2,G4,G8,G9} = True. Đường dẫn tuyệt đối/"../" còn khiến nó đọc study_meta.json từ
    NGOÀI exports/. Cùng lớp lỗi mà resolve_synthetic_study_dir() (dòng ~283) đã cố ý
    phòng bằng cách kiểm trên real_dir.name — bản vá vòng 1 quên tái dùng.
    (Giảm nhẹ: các run_g*_auto.py sanitize `re.sub(r'[^\\w\\-]','_')` nên biến thể này
    không tới được từ CLI — nhưng đây là hàm hợp đồng dùng chung, không được dựa vào việc
    caller nào cũng sanitize.)"""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    real_dir, err = resolve_synthetic_study_dir(study, root)
    if err or real_dir is None:
        return False
    meta = load_study_meta(real_dir)
    return str(meta.get("study_kind", "")).strip().casefold() == "synthetic_test"


def ledger_approved(gate_id: str, study: str, artifact_path: Path,
                    repo_root: Optional[Path] = None) -> bool:
    """CHỐT KIỂM DUY NHẤT nên dùng ở mọi nơi cần biết "cổng gate_id đã được bác sĩ
    duyệt THẬT chưa" — thay cho 5 bản sao gần-giống-nhau từng rải rác ở
    run_g6_auto.py (×4 template) và run_g9_auto.py trước 2026-07-12 (chính cách
    trùng lặp này từng gây lỗi thật ở nơi khác trong hệ thống — sửa 1 chỗ quên 3
    chỗ). True CHỈ khi ĐỦ CẢ NĂM: (1) có bản ghi APPROVED không synthetic cho
    gate_id, (2) bản ghi KHÔNG tự khai do agent tạo/duyệt, (3) reviewer_role của bản ghi thuộc ĐÚNG
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
    phòng thủ thứ hai thay vì lớp duy nhất.

    SỬA 2026-07-26 vòng 2 (red-team độc lập) — hai điểm ở ĐIỀU KIỆN (2):
    a) Docstring này TỪNG khai "(2) không phải agent tạo" nhưng bộ lọc bên dưới CHƯA BAO
       GIỜ kiểm điều đó — red-team ghi một bản ghi `created_by_agent: true` kèm chữ ký hợp
       lệ và vẫn được trả True. Nay có kiểm thật (_AGENT_AUTHORSHIP_FIELDS).
    b) Nhưng phải nói RÕ GIỚI HẠN, không lặp lại lỗi khai quá: cờ này do CHÍNH bản ghi tự
       khai, mà kẻ dựng ledger bằng tay thì không việc gì phải khai thật. Nó chỉ chặn bản
       ghi TRUNG THỰC tự nhận do agent tạo (vd tool nội bộ ghi đúng cờ). Bảo đảm THẬT duy
       nhất chống ledger bịa vẫn là CHỮ KÝ ở điều kiện (5) — `created_by_agent` là lớp
       phòng thủ theo chiều sâu, KHÔNG phải bằng chứng độc lập.
    Kèm: chống ledger dị dạng (JSON không phải list, phần tử không phải dict) — trước đây
    ném AttributeError thay vì trả False, biến chốt fail-closed thành crash pipeline."""
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    ledger_p = root / "exports" / study / "approval_ledger.json"
    if not ledger_p.exists() or not Path(artifact_path).exists():
        return False
    try:
        records = json.loads(ledger_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        # UnicodeDecodeError thêm 2026-07-27: ledger không phải UTF-8 hợp lệ (file hỏng /
        # bị OneDrive ghi dở) từng ném ra ngoài thay vì trả False — chốt fail-closed phải
        # luôn TRẢ VỀ, không được ném.
        return False
    if not isinstance(records, list):
        return False
    latest = _latest_authoritative_record(records, gate_id, study, root)
    if latest is None:
        return False
    # ★ VÁ 2026-07-27 vòng 4 — TÔN TRỌNG THU HỒI. Bản trước LỌC decision=="APPROVED"
    # TRƯỚC khi chọn bản ghi mới nhất, nên một quyết định TỪ CHỐI ký hợp lệ SAU đó
    # không bao giờ đóng được cổng: hội đồng đạo đức rút phê duyệt, phản biện độc lập
    # ký REJECTED — `ledger_approved` vẫn trả True và gói nộp G10 vẫn in "✅ Đã qua cổng
    # G8 (bình duyệt độc lập)". Red-team tái hiện bằng CHÍNH tools/approve_gate.py với
    # `--decision REJECTED` (một lựa chọn argparse hợp lệ, tức quy trình được hỗ trợ),
    # và tools/stakeholder_review_audit.py cũng in [PASS] — nên bác sĩ kiểm tay cũng
    # thấy "ổn". Schema có sẵn trường `supersedes` nhưng KHÔNG nơi nào đọc.
    # Nay: lấy bản ghi MỚI NHẤT theo thời gian rồi mới xét quyết định của nó.
    if latest.get("decision") != "APPROVED" or latest.get("is_synthetic"):
        return False
    try:
        actual_hash = hashlib.sha256(Path(artifact_path).read_bytes()).hexdigest()
    except (OSError, ValueError):
        return False
    if actual_hash != latest.get("evidence_hash"):
        return False
    return True
    # VÁ 2026-07-26 — LẬT MẶC ĐỊNH SANG FAIL-CLOSED (lỗ hổng (3) mô tả ở trên).
    # Trước: mọi đề tài KHÔNG có trong REAL_STUDY_DENYLIST đều được coi là "đã duyệt"
    # khi máy chưa cấu hình khóa ký — nghĩa là một đề tài NGƯỜI THẬT vừa tạo, chưa kịp
    # thêm tay vào danh sách, chỉ cần một approval_ledger.json bịa (tính đúng
    # evidence_hash — không cần bí mật gì) là qua cổng. Nay: KHÔNG có khóa ⇒ CHƯA DUYỆT,
    # ngoại lệ duy nhất là đề tài đã tự tay đánh dấu study_kind == "synthetic_test"
    # (tools/mark_study_synthetic.py, vốn đã từ chối mọi tên trong denylist).
    return is_synthetic_test_study(study, root)
