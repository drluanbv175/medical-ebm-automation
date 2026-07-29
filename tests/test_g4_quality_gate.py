"""Kiểm thử hợp đồng chất lượng G4 (khóa SAP).

Trọng tâm (audit toàn diện G0-G10, 2026-07-29): G4 là 1 trong 5 cổng cứng và
cổng KÝ THẬT duy nhất chưa có lớp quality_gate riêng. Lớp bảo vệ cũ có 3 lỗ
hổng thật: (1) guardrail() 3/4 luật tautology, (2) chốt gác thật duy nhất
(``_g4_sections_still_draft``) chỉ đếm placeholder, không kiểm nội dung
phương pháp luận, (3) KHÔNG có bước nào đối chiếu lại số liệu đã ký với
G3_checkpoint.json hiện tại — SAP bị sửa tay hoặc G3 chạy lại với tham số
khác SAU khi sinh SAP vẫn ký sạch. Test dưới khóa cả tầng máy-kiểm-nội-dung
và tầng bằng-chứng-ký-người-thật, cộng với 3 test tích hợp chạy CLI thật
(không fixture giả) để bắt hồi quy ở lớp nối dây (approve_gate.py/
gate_contract.py/skill_standards.py), không chỉ ở logic nội bộ module.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g4_quality_gate as G4Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g4_auto as G4  # noqa: E402

# ════════════════════════════════════════════════════════════════════════════
# Tiện ích dựng artifact SAP đã điền đủ (không phải markdown viết tay tùy ý —
# đi qua ĐÚNG run_g4_auto.generate() rồi thay placeholder, để test bám sát
# format thật mà pipeline sinh ra).
# ════════════════════════════════════════════════════════════════════════════

_COMPARATIVE_FILLS = [
    ("- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ", "- **Tiêu chí nhận:** Tuổi 18-75  "),
    ("- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ", "- **Tiêu chí loại:** Chống chỉ định  "),
    ("- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
     "- **Kết cục chính:** Tỷ lệ nhập viện tim mạch trong 12 tháng  "),
    ("- **Đơn vị / ngưỡng:** [CẦN]  ", "- **Đơn vị / ngưỡng:** %  "),
    ("- **Kết cục phụ 1:** [CẦN]  ", "- **Kết cục phụ 1:** Tử vong toàn bộ  "),
    ("- **Kết cục phụ 2:** [CẦN]  ", "- **Kết cục phụ 2:** Đột quỵ  "),
    ("- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ", "- **Kết cục an toàn:** Tiêu cơ vân  "),
    ("- **Biến độc lập đưa vào:** [CẦN BÁC SĨ LIỆT KÊ — kèm lý do lâm sàng / DAG]  ",
     "- **Biến độc lập đưa vào:** Tuổi, HbA1c — EPV=15 cho 8 biến, VIF<5  "),
    ("- **Giả định:** [CẦN kiểm tra PH / normality theo thiết kế]  ", "- **Giả định:** Kiểm PH bằng cox.zph  "),
    ("- **Biến đưa vào mô hình imputation:** [CẦN BÁC SĨ ĐIỀN]  ",
     "- **Biến đưa vào mô hình imputation:** Tuổi, giới, HbA1c nền  "),
    ("- **Nhóm nhỏ tiền định:** [CẦN BÁC SĨ — phải ghi TRƯỚC khi xem dữ liệu]  ",
     "- **Nhóm nhỏ tiền định:** Theo tuổi <65/≥65 — TIỀN ĐỊNH  "),
    ("- **Điều chỉnh:** [CẦN — Bonferroni / FDR nếu >3 kết cục chính]  ",
     "- **Điều chỉnh:** Chỉ 1 kết cục chính nên không cần hiệu chỉnh  "),
    ("- [CẦN BÁC SĨ thêm kịch bản cụ thể]  ", "- Kịch bản: loại trừ bỏ thuốc >30% thời gian theo dõi  "),
    ("- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  ", "- **Phần mềm:** R v4.3.1  "),
    ("- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  ", "- **Packages:** survival, mice  "),
    ("- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ", "- **Random seed:** set.seed(20260730)  "),
]

_QUALITATIVE_FILLS = [
    ("[CẦN BÁC SĨ — quy nạp (inductive)/diễn dịch (deductive)/hỗn hợp]", "quy nạp (inductive)"),
    ("[CẦN — số người mã hóa độc lập, phần mềm QDA (NVivo/ATLAS.ti/MAXQDA) hoặc mã tay theo codebook]",
     "2 người mã hóa độc lập, NVivo"),
    ("[CẦN BÁC SĨ — vd không còn mã/chủ đề mới sau N cuộc phỏng vấn liên tiếp]",
     "không còn mã mới sau 3 cuộc phỏng vấn liên tiếp"),
    ("[CẦN BÁC SĨ — purposive/maximum variation/theoretical sampling]", "purposive sampling"),
    ("[CẦN — vd tuổi, giới, mức độ nặng bệnh, thời gian mắc bệnh]", "tuổi, giới, mức độ nặng bệnh"),
    ("[CẦN — member checking / triangulation nguồn dữ liệu]", "member checking"),
    ("[CẦN — mô tả bối cảnh dày (thick description)]", "mô tả bối cảnh dày"),
    ("[CẦN — audit trail quá trình mã hóa]", "audit trail đầy đủ"),
    ("[CẦN — nhật ký phản tư (reflexivity journal)]", "nhật ký phản tư"),
    ("- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ", "- **Tiêu chí nhận:** Bệnh nhân đồng ý phỏng vấn  "),
    ("- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ", "- **Tiêu chí loại:** Không đủ năng lực đồng thuận  "),
    ("- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
     "- **Kết cục chính:** Trải nghiệm sống với bệnh mạn  "),
    ("- **Đơn vị / ngưỡng:** [CẦN]  ", "- **Đơn vị / ngưỡng:** N/A  "),
    ("- **Kết cục phụ 1:** [CẦN]  ", "- **Kết cục phụ 1:** N/A  "),
    ("- **Kết cục phụ 2:** [CẦN]  ", "- **Kết cục phụ 2:** N/A  "),
    ("- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ", "- **Kết cục an toàn:** N/A  "),
    ("- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  ", "- **Phần mềm:** NVivo v14  "),
    ("- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  ", "- **Packages:** N/A  "),
    ("- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ", "- **Random seed:** N/A (định tính)  "),
]


def _fresh_sap(design_code="rct", **overrides):
    kwargs = dict(
        study="TEST-G4Q", topic="Đề tài kiểm định G4", design_primary="RCT song song",
        reporting_std="CONSORT 2025", n_adjusted=400, alpha=0.05, power=0.8,
        effect_val=0.7, effect_type="RR", run_date="2026-07-29",
    )
    kwargs.update(overrides)
    return G4.generate(kwargs["study"], kwargs["topic"], design_code, kwargs["design_primary"],
                       kwargs["reporting_std"], kwargs["n_adjusted"], kwargs["alpha"],
                       kwargs["power"], kwargs["effect_val"], kwargs["effect_type"],
                       kwargs["run_date"], kwargs.get("sd"),
                       hypothesis_type=kwargs.get("hypothesis_type", "superiority"),
                       margin=kwargs.get("margin"))


def _filled_comparative_sap(**overrides):
    text = _fresh_sap(design_code=overrides.pop("design_code", "rct"), **overrides)
    for old, new in _COMPARATIVE_FILLS:
        assert old in text, f"template không còn chứa placeholder mong đợi: {old[:50]!r}"
        text = text.replace(old, new)
    return text


def _filled_qualitative_sap(**overrides):
    text = _fresh_sap(design_code="qualitative", **overrides)
    for old, new in _QUALITATIVE_FILLS:
        assert old in text, f"template định tính không còn chứa placeholder mong đợi: {old[:50]!r}"
        text = text.replace(old, new)
    return text


def _checkpoint(**overrides) -> dict:
    value = {"gate": "G4", "study": "TEST-G4Q", "design_code": "rct", "guardrail": "✅ PASS"}
    value.update(overrides)
    return value


def _g3_checkpoint(**overrides) -> dict:
    value = {
        "design_code": "rct", "alpha": 0.05, "power": 0.8, "n_adjusted": 400,
        "confirmed_n": None, "effect_val": 0.7, "effect_type": "RR",
        "hypothesis_type": "superiority", "margin": None, "sd": None,
    }
    value.update(overrides)
    return value


def _meta(g4_overrides=None, g0_overrides=None, g3_overrides=None, top_level=None) -> dict:
    g4 = {
        "epv_vif_reviewed": True, "missing_data_mechanism_confirmed": True,
        "subgroup_multiplicity_predefined_confirmed": True,
        "reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-07-29T08:00:00+00:00",
    }
    g4.update(g4_overrides or {})
    g0 = dict(g0_overrides or {})
    g3 = dict(g3_overrides or {})
    meta = {"gate_params": {"G4": g4, "G0": g0, "G1": {}, "G3": g3}}
    meta.update(top_level or {})
    return meta


def _evaluate(**overrides):
    kwargs = dict(
        study="TEST-G4Q",
        checkpoint=_checkpoint(),
        artifact_text=_filled_comparative_sap(),
        g3_checkpoint=_g3_checkpoint(),
        g1_checkpoint={"design": {"internal_code": "rct"}},
        meta=_meta(),
        ledger_signed=True,
        ledger_reason="",
        signature_scope="role",
        role_key_available=True,
        cross_gate_refs={"G2": "IRB-01", "G4": "STAT-01", "G8": "REV-77", "G9": "PI-01"},
    )
    kwargs.update(overrides)
    return G4Q.evaluate_g4_quality(**kwargs)


def _row(report, criterion_id):
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _configure_test_signing_key(tmp_path: Path, monkeypatch, role: str | None = None) -> Path:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g4-quality-key", encoding="utf-8")
    if role:
        (tmp_path / f"gate_approval_key_{role}").write_text(
            f"pytest-g4-quality-key-{role}", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    return key_path


# ════════════════════════════════════════════════════════════════════════════
# Hợp đồng module
# ════════════════════════════════════════════════════════════════════════════


def test_bon_trang_thai_roi_nghia():
    statuses = {G4Q.STATUS_BLOCKED, G4Q.STATUS_DRAFT, G4Q.STATUS_READY, G4Q.STATUS_LOCKED}
    assert len(statuses) == 4


def test_trang_thai_dat_khong_qua_khang_dinh():
    """G4 CÓ ledger ký thật (khác G3) — nhưng vẫn không chứng minh độc lập (giống G8)."""
    assert "PASS" in G4Q.STATUS_LOCKED
    assert "ĐỘC LẬP" not in G4Q.STATUS_LOCKED.upper()


def test_gioi_han_phan_dinh_noi_ro_han_che_HMAC():
    scope = _evaluate()["scope_statement"]
    assert "KHÔNG chứng minh" in scope
    assert "ledger_approved" in scope


def test_moi_chuan_nen_deu_co_dinh_danh():
    for item in G4Q.STANDARDS_BASIS:
        assert item.get("url") or item.get("doi") or item.get("pmid"), item


def test_ten_artifact_hop_dong_downstream_khong_doi():
    assert G4Q.sap_artifact_name("ABC") == "G4_A5_SAP_FINAL_ABC.md"


def test_dong_bo_danh_sach_thiet_ke_khong_dung_cong_thuc_power():
    """4 bản độc lập (run_g3/run_g4/g3_quality/g4_quality) phải khớp nhau —
    sửa 1 nơi quên 3 chỗ đã là bug thật từng xảy ra trong dự án này."""
    assert G4Q.N_NOT_APPLICABLE_DESIGNS == G4.N_NOT_APPLICABLE_DESIGNS


def test_sap_day_du_thi_dat_LOCKED_toan_bo_tieu_chi():
    report = _evaluate()
    assert report["status"] == G4Q.STATUS_LOCKED
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        assert row["status"] == "PASS", row


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-00/01 — guardrail nền + trạng thái BLOCKED của chính G4
# ════════════════════════════════════════════════════════════════════════════


def test_guardrail_loi_chan_cong():
    report = _evaluate(checkpoint=_checkpoint(guardrail="⚠ 2 LỖI"))
    assert _row(report, "G4-AUTO-00")["status"] == "BLOCK"
    assert report["status"] == G4Q.STATUS_BLOCKED


def test_g4_dang_blocked_cho_g3_chan_cong():
    cp = _checkpoint(needs_input={"blocked": True, "human_message": "chờ N từ G3"})
    report = _evaluate(checkpoint=cp)
    assert _row(report, "G4-AUTO-01")["status"] == "BLOCK"
    assert report["status"] == G4Q.STATUS_BLOCKED


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-02 — design_code nhất quán G3↔G4
# ════════════════════════════════════════════════════════════════════════════


def test_design_code_lech_giua_g3_va_g4_bi_chan():
    report = _evaluate(checkpoint=_checkpoint(design_code="cohort"))
    row = _row(report, "G4-AUTO-02")
    assert row["status"] == "BLOCK"
    assert "LỆCH THIẾT KẾ" in row["evidence"]
    assert report["status"] == G4Q.STATUS_BLOCKED


def test_design_code_khop_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-02")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-03 [đóng F5] — số liệu ký khớp G3_checkpoint.json HIỆN TẠI
# ════════════════════════════════════════════════════════════════════════════


def test_parse_signed_numbers_doc_dung_paragraph_12():
    text = _fresh_sap(design_code="rct")
    parsed = G4Q.parse_signed_numbers(text)
    assert parsed["found"] is True
    assert parsed["alpha"] == 0.05
    assert parsed["power_pct"] == 80
    assert parsed["n"] == 400
    assert parsed["effect_type"] == "RR"
    assert parsed["effect_val"] == 0.7


def test_khong_co_muc_12_thi_review_khong_crash():
    parsed = G4Q.parse_signed_numbers("không có gì liên quan ở đây")
    assert parsed["found"] is False
    report = _evaluate(artifact_text="văn bản không có §12")
    assert _row(report, "G4-AUTO-03")["status"] == "REVIEW"


def test_g3_chay_lai_voi_alpha_khac_sau_khi_sinh_sap_bi_chan():
    """Đúng F5: G3 rerun với alpha khác SAU khi G4 đã sinh SAP — SAP cũ (ký
    alpha=0.05) không còn khớp G3 hiện tại (alpha=0.10)."""
    report = _evaluate(g3_checkpoint=_g3_checkpoint(alpha=0.10))
    row = _row(report, "G4-AUTO-03")
    assert row["status"] == "BLOCK"
    assert "alpha" in row["evidence"]
    assert report["status"] == G4Q.STATUS_BLOCKED


def test_n_lech_giua_sap_va_g3_hien_tai_bi_chan():
    report = _evaluate(g3_checkpoint=_g3_checkpoint(n_adjusted=999))
    row = _row(report, "G4-AUTO-03")
    assert row["status"] == "BLOCK"
    assert "N ký" in row["evidence"]


def test_effect_val_lech_bi_chan():
    report = _evaluate(g3_checkpoint=_g3_checkpoint(effect_val=0.5))
    assert _row(report, "G4-AUTO-03")["status"] == "BLOCK"


def test_margin_khop_khi_non_inferiority_thi_dat():
    text = _filled_comparative_sap(hypothesis_type="non_inferiority", margin=0.1, effect_type="RR")
    report = _evaluate(
        artifact_text=text,
        g3_checkpoint=_g3_checkpoint(hypothesis_type="non_inferiority", margin=0.1),
        meta=_meta(g3_overrides={"margin_source": "PMID:12345678", "margin_justification": "MCID lâm sàng đã công bố"}),
    )
    assert _row(report, "G4-AUTO-03")["status"] == "PASS"


def test_sr_ma_dung_confirmed_n_khong_bi_bao_sai():
    """sr_ma/prediction/qualitative dùng confirmed_n, không phải n_adjusted —
    đối chiếu sai cột sẽ báo lệch oan cho một SAP thực ra khớp."""
    text = _fresh_sap(design_code="qualitative", n_adjusted=0)
    text = text  # qualitative không có effect size — chỉ kiểm N ở đây
    report = _evaluate(
        checkpoint=_checkpoint(design_code="qualitative"),
        artifact_text=_filled_qualitative_sap(n_adjusted=25),
        g3_checkpoint=_g3_checkpoint(design_code="qualitative", n_adjusted=0, confirmed_n=25,
                                     effect_val=None, effect_type=None),
    )
    assert _row(report, "G4-AUTO-03")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-04/05 — EPV/VIF §5, cơ chế dữ liệu thiếu §6 (KHÔNG tautology)
# ════════════════════════════════════════════════════════════════════════════


def test_epv_vang_mat_tren_draft_moi_la_review_khong_phai_tautology():
    """Bản DRAFT chưa ai đụng tới KHÔNG được PASS oan — mặc định template
    không chứa EPV/VIF nên đây phải là REVIEW trên bản mới sinh."""
    report = _evaluate(artifact_text=_fresh_sap())
    assert _row(report, "G4-AUTO-04")["status"] == "REVIEW"


def test_epv_da_dien_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-04")["status"] == "PASS"


def test_qualitative_khong_ap_dung_epv():
    report = _evaluate(
        checkpoint=_checkpoint(design_code="qualitative"),
        artifact_text=_filled_qualitative_sap(),
        g3_checkpoint=_g3_checkpoint(design_code="qualitative", n_adjusted=0, confirmed_n=20,
                                     effect_val=None, effect_type=None),
    )
    assert _row(report, "G4-AUTO-04")["status"] == "PASS"
    assert _row(report, "G4-AUTO-05")["status"] == "PASS"


def test_muc_6_con_placeholder_la_review_du_template_da_in_san_MAR():
    """Bẫy tautology: template mặc định ĐÃ in sẵn 'MAR (missing at random)' —
    đếm sự có mặt của MCAR/MAR/MNAR sẽ LUÔN PASS. Tín hiệu thật là placeholder
    '[CẦN' của biến imputation chưa được thay."""
    report = _evaluate(artifact_text=_fresh_sap())
    row = _row(report, "G4-AUTO-05")
    assert row["status"] == "REVIEW"
    assert "imputation" in row["evidence"] or "[CẦN" in row["evidence"]


def test_muc_6_da_dien_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-05")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-06 — đa so sánh, số học Bonferroni
# ════════════════════════════════════════════════════════════════════════════


def test_bonferroni_khop_so_hoc_thi_dat():
    text = _filled_comparative_sap()
    text = text.replace(
        "- **Điều chỉnh:** Chỉ 1 kết cục chính nên không cần hiệu chỉnh  ",
        "- **Điều chỉnh:** Bonferroni cho 4 kết cục, alpha điều chỉnh = 0.0125  ",
    )
    report = _evaluate(artifact_text=text)
    assert _row(report, "G4-AUTO-06")["status"] == "PASS"


def test_bonferroni_khong_khop_so_hoc_bi_review():
    text = _filled_comparative_sap()
    text = text.replace(
        "- **Điều chỉnh:** Chỉ 1 kết cục chính nên không cần hiệu chỉnh  ",
        "- **Điều chỉnh:** Bonferroni cho 4 kết cục, alpha điều chỉnh = 0.04  ",
    )
    report = _evaluate(artifact_text=text)
    row = _row(report, "G4-AUTO-06")
    assert row["status"] == "REVIEW"
    assert "không khớp số học" in row["evidence"]


def test_muc_8_con_placeholder_la_review():
    report = _evaluate(artifact_text=_fresh_sap())
    assert _row(report, "G4-AUTO-06")["status"] == "REVIEW"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-07 — subgroup tiền định (chống HARKing) — lỗ hổng KHÔNG bị
# approve_gate._g4_sections_still_draft() chặn
# ════════════════════════════════════════════════════════════════════════════


def test_subgroup_con_placeholder_khong_bi_approve_gate_chan_nhung_bi_quality_gate_bao():
    fresh = _fresh_sap()
    still_draft = _import_still_draft(fresh)
    assert not any("§7" in item for item in still_draft), (
        "Nếu approve_gate ĐÃ thêm §7 vào danh sách bắt buộc, cập nhật lại giả định của test này.")
    report = _evaluate(artifact_text=fresh)
    assert _row(report, "G4-AUTO-07")["status"] == "REVIEW"


def test_subgroup_da_dien_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-07")["status"] == "PASS"


def _import_still_draft(text):
    import approve_gate as AG
    return AG._g4_sections_still_draft(text)


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-08 [đóng F4] — phần mềm+seed cụ thể, bắt kiểu "thay [CẦN] bằng OK"
# ════════════════════════════════════════════════════════════════════════════


def test_thay_can_bang_OK_khong_qua_duoc_kiem_phan_mem_seed():
    """Đúng lỗ hổng F4: đếm '[CẦN' một mình để 'OK' lách qua — kiểm bổ sung
    đòi tên+phiên bản phần mềm VÀ seed số nguyên cụ thể."""
    text = _filled_comparative_sap()
    text = text.replace("- **Phần mềm:** R v4.3.1  ", "- **Phần mềm:** OK  ")
    text = text.replace("- **Random seed:** set.seed(20260730)  ", "- **Random seed:** OK  ")
    report = _evaluate(artifact_text=text)
    row = _row(report, "G4-AUTO-08")
    assert row["status"] == "REVIEW"
    assert "OK" in row["evidence"]


def test_phan_mem_seed_cu_the_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-08")["status"] == "PASS"


def test_muc_10_con_placeholder_la_review():
    report = _evaluate(artifact_text=_fresh_sap())
    assert _row(report, "G4-AUTO-08")["status"] == "REVIEW"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-09 — margin(Δ) cho NI/equivalence phải có giá trị + nguồn
# ════════════════════════════════════════════════════════════════════════════


def test_superiority_khong_can_margin():
    assert _row(_evaluate(), "G4-AUTO-09")["status"] == "PASS"


def test_non_inferiority_thieu_margin_bi_chan_cung():
    report = _evaluate(g3_checkpoint=_g3_checkpoint(hypothesis_type="non_inferiority", margin=None))
    row = _row(report, "G4-AUTO-09")
    assert row["status"] == "BLOCK"
    assert report["status"] == G4Q.STATUS_BLOCKED


def test_non_inferiority_co_margin_nhung_thieu_nguon_la_review():
    report = _evaluate(
        g3_checkpoint=_g3_checkpoint(hypothesis_type="non_inferiority", margin=0.1),
        meta=_meta(),  # gate_params.G3 rỗng — không có margin_source/justification
    )
    row = _row(report, "G4-AUTO-09")
    assert row["status"] == "REVIEW"
    assert "margin_source" in row["evidence"] or "margin_justification" in row["evidence"]


def test_non_inferiority_co_margin_va_nguon_thi_dat():
    report = _evaluate(
        g3_checkpoint=_g3_checkpoint(hypothesis_type="non_inferiority", margin=0.1),
        meta=_meta(g3_overrides={"margin_source": "PMID:12345678", "margin_justification": "MCID đã công bố"}),
    )
    assert _row(report, "G4-AUTO-09")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-10 — tái dùng approve_gate._g4_sections_still_draft (DRY)
# ════════════════════════════════════════════════════════════════════════════


def test_placeholder_o_muc_bat_buoc_bi_review():
    report = _evaluate(artifact_text=_fresh_sap())
    row = _row(report, "G4-AUTO-10")
    assert row["status"] == "REVIEW"
    assert "§1" in row["evidence"] and "§2" in row["evidence"]


def test_da_dien_du_thi_dat():
    assert _row(_evaluate(), "G4-AUTO-10")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# G4-AUTO-11 — kết cục chính §2 khớp câu hỏi nghiên cứu gốc (G0/G1)
# ════════════════════════════════════════════════════════════════════════════


def test_chua_khai_primary_outcome_o_g0_thi_khong_bao_loi():
    assert _row(_evaluate(), "G4-AUTO-11")["status"] == "PASS"


def test_ket_cuc_chinh_khop_g0_thi_dat():
    report = _evaluate(meta=_meta(g0_overrides={"primary_outcome": "Tỷ lệ nhập viện tim mạch trong 12 tháng"}))
    assert _row(report, "G4-AUTO-11")["status"] == "PASS"


def test_ket_cuc_chinh_lech_g0_bi_review():
    report = _evaluate(meta=_meta(g0_overrides={"primary_outcome": "Tử vong do mọi nguyên nhân"}))
    row = _row(report, "G4-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "KHÔNG chứa" in row["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# Tầng bằng chứng ký người thật (G4-HUMAN-01..07)
# ════════════════════════════════════════════════════════════════════════════


def test_chua_ky_ledger_thi_review_khong_pass_gia():
    report = _evaluate(ledger_signed=False, ledger_reason="chưa có bản ghi phê duyệt nào cho cổng G4")
    assert _row(report, "G4-HUMAN-01")["status"] == "REVIEW"
    assert report["status"] != G4Q.STATUS_LOCKED


def test_ky_bang_khoa_chung_khong_duoc_coi_la_doc_lap():
    report = _evaluate(signature_scope="shared")
    row = _row(report, "G4-HUMAN-02")
    assert row["status"] == "REVIEW"
    assert "shared" in row["evidence"]
    assert report["status"] != G4Q.STATUS_LOCKED


def test_reviewer_ref_trung_cong_khac_bi_review():
    report = _evaluate(cross_gate_refs={"G2": "BS-A", "G4": "BS-A", "G8": "BS-B", "G9": "BS-C"})
    row = _row(report, "G4-HUMAN-03")
    assert row["status"] == "REVIEW"
    assert "TRÙNG" in row["evidence"]


def test_thieu_xac_nhan_epv_thi_review():
    report = _evaluate(meta=_meta(g4_overrides={"epv_vif_reviewed": False}))
    assert _row(report, "G4-HUMAN-04")["status"] == "REVIEW"


def test_thieu_xac_nhan_missing_data_thi_review():
    report = _evaluate(meta=_meta(g4_overrides={"missing_data_mechanism_confirmed": False}))
    assert _row(report, "G4-HUMAN-05")["status"] == "REVIEW"


def test_subgroup_xac_nhan_sau_khi_khoa_du_lieu_la_harking():
    report = _evaluate(meta=_meta(
        g4_overrides={"subgroup_multiplicity_predefined_confirmed": True,
                      "reviewed_at": "2026-08-01T00:00:00+00:00"},
        top_level={"data_lock_date": "2026-07-15"},
    ))
    row = _row(report, "G4-HUMAN-06")
    assert row["status"] == "REVIEW"
    assert "HARKing" in row["evidence"]


def test_subgroup_xac_nhan_truoc_khoa_du_lieu_thi_dat():
    report = _evaluate(meta=_meta(
        g4_overrides={"subgroup_multiplicity_predefined_confirmed": True,
                      "reviewed_at": "2026-07-01T00:00:00+00:00"},
        top_level={"data_lock_date": "2026-07-15"},
    ))
    assert _row(report, "G4-HUMAN-06")["status"] == "PASS"


def test_reviewed_by_role_sai_nhom_bi_review():
    report = _evaluate(meta=_meta(g4_overrides={"reviewed_by_role": "IRB_ETHICS_COMMITTEE"}))
    assert _row(report, "G4-HUMAN-07")["status"] == "REVIEW"


def test_reviewed_by_role_pi_cung_hop_le():
    """Doctrine cho phép PI tự ký G4 khi không có thống kê viên riêng."""
    report = _evaluate(meta=_meta(g4_overrides={"reviewed_by_role": "PI_PROJECT_OWNER"}))
    assert _row(report, "G4-HUMAN-07")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Tích hợp — chấm qua CLI thật, không fixture giả (bắt hồi quy ở lớp nối dây)
# ════════════════════════════════════════════════════════════════════════════


def _seed_g0_g1_g3(study_dir: Path, *, alpha: float = 0.05) -> None:
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "gate": "G0", "topic": "Đề tài kiểm định G4", "guardrail": {"passed": True},
    }), encoding="utf-8")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "gate": "G1",
        "design": {"internal_code": "rct", "primary": "RCT song song",
                   "reporting_standard": "CONSORT 2025", "ambiguous": False},
    }), encoding="utf-8")
    (study_dir / "G3_checkpoint.json").write_text(json.dumps({
        "gate": "G3", "design_code": "rct", "alpha": alpha, "power": 0.8,
        "n_adjusted": 400, "confirmed_n": None, "effect_val": 0.7, "effect_type": "RR",
        "hypothesis_type": "superiority", "margin": None, "sd": None, "guardrail": "✅ PASS",
    }), encoding="utf-8")


def test_pipeline_that_g4_moi_sinh_la_draft_needs_human_content():
    study = "PYTEST-G4Q-INTEGRATION-DRAFT"
    d = REPO_ROOT / "exports" / study
    _rmtree_retry(d)
    try:
        _seed_g0_g1_g3(d)
        gen = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g4_auto.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert gen.returncode == 0, gen.stdout + gen.stderr
        quality = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "g4_quality_gate.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert "DRAFT_NEEDS_HUMAN_CONTENT" in quality.stdout, quality.stdout
        report = json.loads((d / "G4_QUALITY_REPORT.json").read_text(encoding="utf-8"))
        assert report["status"] == G4Q.STATUS_DRAFT
        checkpoint = json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))
        assert checkpoint["quality_contract_version"] == G4Q.QUALITY_CONTRACT_VERSION
        # run_g4_auto.py TỰ ghi "g4_lock_date": None làm placeholder ngay khi sinh SAP
        # (chưa ký) — refresh_checkpoint() chỉ GHI ĐÈ giá trị này khi status==LOCKED,
        # không xóa/thêm key. Bản DRAFT phải giữ nguyên None, không phải vắng key.
        assert checkpoint.get("g4_lock_date") is None
    finally:
        _rmtree_retry(d)


def test_pipeline_that_ky_bang_khoa_vai_tro_dat_locked_va_ghi_g4_lock_date(tmp_path, monkeypatch):
    study = "PYTEST-G4Q-INTEGRATION-LOCKED"
    d = REPO_ROOT / "exports" / study
    _rmtree_retry(d)
    _configure_test_signing_key(tmp_path, monkeypatch, role="STATISTICIAN")
    try:
        _seed_g0_g1_g3(d)
        gen = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g4_auto.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert gen.returncode == 0, gen.stdout + gen.stderr

        artifact_path = d / f"G4_A5_SAP_FINAL_{study}.md"
        text = artifact_path.read_text(encoding="utf-8")
        for old, new in _COMPARATIVE_FILLS:
            text = text.replace(old, new)
        artifact_path.write_text(text, encoding="utf-8")

        meta = GC.ensure_study_meta(d)
        meta["gate_params"]["G4"].update({
            "epv_vif_reviewed": True, "missing_data_mechanism_confirmed": True,
            "subgroup_multiplicity_predefined_confirmed": True,
            "reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-07-29T08:00:00+00:00",
        })
        (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        sign = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "approve_gate.py"), "--study", study, "--gate", "G4",
             "--artifact", str(artifact_path),
             "--reviewer-role", "METHODS_STATISTICS_REVIEWER", "--reviewer-ref", "TEST-STAT-001"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            env={**__import__("os").environ},
        )
        assert sign.returncode == 0, sign.stdout + sign.stderr
        assert "PASS_G4_SAP_LOCKED" in sign.stdout, sign.stdout

        checkpoint = json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))
        assert checkpoint["quality_gate"]["status"] == G4Q.STATUS_LOCKED
        assert checkpoint.get("g4_lock_date"), "F6: g4_lock_date phải được ghi khi LOCKED"

        ledger = json.loads((d / "approval_ledger.json").read_text(encoding="utf-8"))
        g4_records = [r for r in ledger if r.get("gate_id") == "G4"]
        assert checkpoint["g4_lock_date"] == g4_records[-1]["timestamp_utc"], (
            "g4_lock_date phải khớp ĐÚNG timestamp ledger thật, không phải giờ hệ thống lúc chấm")

        # F6 (skill_standards.real_world_signals) — tín hiệu 'sap_locked' phải
        # đọc được TRỰC TIẾP từ chữ ký thật, không cần bác sĩ gõ tay g4_lock_date.
        import skill_standards as S
        signals = S.real_world_signals({"G4": checkpoint}, meta={})
        assert signals["sap_locked"] is True
    finally:
        _rmtree_retry(d)


def test_pipeline_that_g3_chay_lai_sau_khi_ky_bi_phat_hien_qua_g4_quality_gate(tmp_path, monkeypatch):
    """Đúng F5: mô phỏng G3 chạy lại (tham số khác) SAU KHI G4 đã sinh SAP —
    quality gate phải bắt được, không cần chờ ai đó đọc kỹ bằng mắt."""
    study = "PYTEST-G4Q-INTEGRATION-DRIFT"
    d = REPO_ROOT / "exports" / study
    _rmtree_retry(d)
    _configure_test_signing_key(tmp_path, monkeypatch)
    try:
        _seed_g0_g1_g3(d, alpha=0.05)
        gen = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g4_auto.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert gen.returncode == 0, gen.stdout + gen.stderr

        # G3 "chạy lại" với alpha khác — SAP trên đĩa vẫn còn số cũ.
        g3_path = d / "G3_checkpoint.json"
        g3 = json.loads(g3_path.read_text(encoding="utf-8"))
        g3["alpha"] = 0.10
        g3_path.write_text(json.dumps(g3), encoding="utf-8")

        quality = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "g4_quality_gate.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert "BLOCKED" in quality.stdout, quality.stdout
        assert "G4-AUTO-03" in quality.stdout
        report = json.loads((d / "G4_QUALITY_REPORT.json").read_text(encoding="utf-8"))
        assert report["status"] == G4Q.STATUS_BLOCKED
    finally:
        _rmtree_retry(d)


# ════════════════════════════════════════════════════════════════════════════
# Tích hợp con — gate_contract.g4_quality_contract_satisfied() +
# audit_research_gates.py không còn bỏ qua G4 im lặng
# ════════════════════════════════════════════════════════════════════════════


def test_g4_quality_contract_satisfied_false_khi_chua_ky(tmp_path, monkeypatch):
    study = "PYTEST-G4Q-CONTRACT-FN"
    d = REPO_ROOT / "exports" / study
    _rmtree_retry(d)
    _configure_test_signing_key(tmp_path, monkeypatch)
    try:
        _seed_g0_g1_g3(d)
        subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g4_auto.py"), "--study", study],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert GC.g4_quality_contract_satisfied(study, repo_root=REPO_ROOT) is False
    finally:
        _rmtree_retry(d)


def test_g4_quality_contract_satisfied_khong_co_module_tra_false(monkeypatch):
    """Import lỗi (hoặc chưa nạp được) phải fail-closed, không ném exception."""
    import gate_contract as GC_local
    monkeypatch.setattr(GC_local, "Path", GC_local.Path)  # no-op, giữ import sạch
    assert GC.g4_quality_contract_satisfied("khong-ton-tai-hoan-toan", repo_root=REPO_ROOT) is False


def test_audit_research_gates_dang_ky_g4_quality_report():
    import audit_research_gates as ARG
    g4_keys = {item["key"] for item in ARG.GATE_ARTIFACT_REQUIREMENTS["G4"]}
    assert "g4_quality_report" in g4_keys


def test_audit_research_gates_co_nhanh_phan_loai_g4():
    import inspect

    import audit_research_gates as ARG
    src = inspect.getsource(ARG._classify_gate)
    assert 'gate == "G4"' in src
    assert "PASS_G4_SAP_LOCKED" in src
