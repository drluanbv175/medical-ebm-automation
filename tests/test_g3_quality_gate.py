"""Kiểm thử hợp đồng chất lượng G3 (cỡ mẫu).

Trọng tâm: những ca mà `run_g3_auto.guardrail_check()` KHÔNG bắt được vì nó chỉ
soi văn bản do chính nó sinh ra — cụ thể là các lỗi về SỐ và về NGUỒN. Mỗi test
dưới đây tương ứng một lỗ hổng đã xác nhận bằng cách đọc/chạy thật cổng G3.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
sys.path.insert(0, str(TOOLS_DIR))

import g3_quality_gate as G3Q  # noqa: E402
import run_g3_auto as G3  # noqa: E402


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _seed_g0_g1(study_dir: Path, design_code: str) -> None:
    # 04/10/2026 (soát từng cổng): G3 CHẤM SỐNG G1 — G1_checkpoint chỉ có «design» là G1 BỊ CHẶN. Dựng chuỗi G0→G1 đã
    # chốt thật cho đúng thiết kế (tests/_chuoi_da_chot.py), không mẫu effect size ở G1.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _chuoi_da_chot import dung_g0_g1_da_chot
    dung_g0_g1_da_chot(study_dir, study_dir.name, thiet_ke=design_code, mau_hieu_qua=[])

# ════════════════════════════════════════════════════════════════════════════
# Đồ gá
# ════════════════════════════════════════════════════════════════════════════


def _artifact(
    *,
    n_total: int = 942,
    n_adjusted: int = 1178,
    dropout_pct: int = 20,
    base_cell: int | None = None,
    na_cells: bool = False,
    standard_token: str = "CONSORT 2025",
) -> str:
    """Dựng một artifact A4 tối thiểu nhưng đúng hình dạng bảng của cổng thật."""
    base = n_adjusted if base_cell is None else base_cell
    low = "N/A" if na_cells else str(int(base * 1.5))
    high = "N/A" if na_cells else str(int(base * 0.7))
    return f"""# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)

## PHẦN 2 — KẾT QUẢ TÍNH TOÁN

| N tổng (không dropout) | **{n_total}** |
| N điều chỉnh | **{n_adjusted}** |

## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)

Bảng: Power × Effect size → N tổng (điều chỉnh {dropout_pct}% dropout)

| Power | ES × 0.8 (80%) | ES × 1.0 (cơ sở) | ES × 1.2 (120%) |
|---|---|---|---|
| 70% | {low} | {int(base * 0.8)} | {high} |
| 80% | {low} | {base} | {high} |
| 90% | {low} | {int(base * 1.3)} | {high} |

## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)

Khối này viết theo {standard_token}.

*Cần bác sĩ kiểm chứng.*
"""


def _checkpoint(**overrides) -> dict:
    value = {
        "gate": "G3",
        "study": "TEST-G3",
        "design_code": "rct",
        "design_ambiguous": False,
        "alpha": 0.05,
        "power": 0.80,
        "effect_val": 8.0,
        "effect_type": "ARR%",
        "effect_quality": "labeled",
        "n_per_group": 471,
        "n_total": 942,
        "n_adjusted": 1178,
        "confirmed_n": None,
        "dropout": 0.20,
        "formula_used": "Hai tỷ lệ độc lập (xấp xỉ chuẩn), z(α/2)=1.96",
        "p_event": 0.30,
        "p0": 0.30,
        "sd": None,
        "hypothesis_type": "superiority",
        "margin": None,
        "guardrail": "✅ PASS",
    }
    value.update(overrides)
    return value


def _full_meta(**g3_overrides) -> dict:
    """study_meta của một đề tài đã được xác nhận ĐẦY ĐỦ (đường PASS)."""
    g3 = {
        "effect_size": 8.0,
        "effect_type": "ARR%",
        "effect_source": "PMID: 30560792",
        "effect_source_confirmed": True,
        "p0_source": "PMID: 30560792 — tỷ lệ biến cố nhóm chứng 30%",
        "dropout_source": "Pilot nội bộ 2025, tỷ lệ bỏ cuộc 18%",
        "assumptions_confirmed": True,
        "hypothesis_confirmed": True,
        "powered_for_outcome": "Tử vong do mọi nguyên nhân trong 12 tháng",
        "recruitment_feasibility_confirmed": True,
        "reviewed_by_role": "BIOSTATISTICIAN",
        "reviewed_at": "2026-07-27T09:00:00",
        "software": "run_g3_auto.py + scipy 1.18.0",
    }
    g3.update(g3_overrides)
    return {
        "gate_params": {
            "G1": {"primary_outcome": "Tử vong do mọi nguyên nhân trong 12 tháng"},
            "G3": g3,
        }
    }


# Bộ khai báo NI theo khung FDA đã đủ điều kiện (tách bạch M1/M2).
_NI_FDA = {
    "ni_regulatory_framework": "FDA",
    "margin_justification": (
        "M1 = cận dưới KTC 95% hiệu quả thuốc chứng vs giả dược từ y văn; "
        "M2 = 50% của M1 theo thông lệ tim mạch"
    ),
    "margin_source": "PMID: 30560792",
}

def _checkpoint_cum(n_clusters: int = 60, m: int = 25, icc: float = 0.02) -> dict:
    """Checkpoint G3 của thiết kế cụm mà bộ sinh ĐÃ nhân hệ số thiết kế (04/10/2026, G3-02): N trước DE suy ngược
    để n_total = ⌈N trước DE × DE⌉ và số cụm = ⌈n_total / m⌉ = n_clusters."""
    de = 1 + (m - 1) * icc
    n_total = n_clusters * m
    n_truoc = int(n_total / de)
    while math.ceil(n_truoc * de) < n_total - (m - 1):
        n_truoc += 1
    n_total = math.ceil(n_truoc * de)
    return _checkpoint(icc=icc, cluster_size=m, design_effect=de, n_total_truoc_de=n_truoc, n_total=n_total,
                       n_per_group=math.ceil(n_total / 2), n_adjusted=math.ceil(n_total / 0.8),
                       n_clusters=math.ceil(n_total / m))


def _eval_cum(tmp_path, meta, **kw):
    cp = _checkpoint_cum(**kw)
    return _evaluate(tmp_path, checkpoint=cp, meta=meta,
                     artifact=_artifact(n_total=cp["n_total"], n_adjusted=cp["n_adjusted"],
                                        base_cell=cp["n_adjusted"]))


# Bộ khai báo thiết kế theo chùm đã đủ điều kiện.
_CLUSTER_OK = {
    "icc": 0.02,
    "cluster_size": 25,
    "icc_source": "PMID: 30560792 — ICC 0,02 từ nghiên cứu cùng bối cảnh",
    "n_clusters": 60,
    "equal_cluster_sizes": True,
}


def _chot(meta: dict, checkpoint: dict) -> dict:
    """PI xác nhận ĐÚNG bộ giá trị đang có trong checkpoint (G3-03): dấu vân tay các giá trị quyết định N."""
    meta = json.loads(json.dumps(meta))
    meta.setdefault("gate_params", {}).setdefault("G3", {}).setdefault(
        "dau_van_tay_chot", G3Q.dau_van_tay_g3(checkpoint))
    return meta


def _evaluate(tmp_path: Path, *, checkpoint=None, meta=None, artifact=None, g1=True, g0=True, chot=True):
    study = "TEST-G3"
    artifact_path = tmp_path / f"G3_A4_SAMPLE_SIZE_{study}.md"
    artifact_path.write_text(
        _artifact() if artifact is None else artifact, encoding="utf-8", newline="\n"
    )
    checkpoint = _checkpoint() if checkpoint is None else checkpoint
    meta = _full_meta() if meta is None else meta
    return G3Q.evaluate_g3_quality(
        study=study,
        checkpoint=checkpoint,
        artifact_path=artifact_path,
        g0_checkpoint={"gate": "G0"} if g0 else {},
        g1_checkpoint={"gate": "G1"} if g1 else {},
        meta=_chot(meta, checkpoint) if chot else meta,
    )


def _row(report, criterion_id):
    for row in report["automatic_criteria"] + report["human_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


# ════════════════════════════════════════════════════════════════════════════
# Hợp đồng module và chống trôi so với cổng thật
# ════════════════════════════════════════════════════════════════════════════


def test_khong_troi_danh_sach_thiet_ke_khong_dung_cong_thuc_power():
    """Hai bản hằng phải khớp — lệch là một nhánh sẽ bắt lỗi oan hoặc bỏ sót."""
    assert set(G3Q.N_NOT_APPLICABLE_DESIGNS) == set(G3.N_NOT_APPLICABLE_DESIGNS)


def test_bon_trang_thai_roi_nghia():
    statuses = {
        G3Q.STATUS_BLOCKED,
        G3Q.STATUS_DRAFT_PARAMS,
        G3Q.STATUS_DRAFT_REVIEW,
        G3Q.STATUS_CONFIRMED,
    }
    assert len(statuses) == 4
    assert G3Q.STATUS_CONFIRMED == "PASS_G3_CONFIRMED"


def test_moi_chuan_nen_deu_co_dinh_danh_that():
    """Không được có mục nào trong standards_basis thiếu PMID/DOI/URL."""
    for item in G3Q.STANDARDS_BASIS:
        assert item.get("pmid") or item.get("doi") or item.get("url"), item


# ════════════════════════════════════════════════════════════════════════════
# Lỗi ĐƠN VỊ/Ý NGHĨA tham số — hai ca chặn cứng
# ════════════════════════════════════════════════════════════════════════════


def test_cat_ngang_dung_thuoc_do_lien_he_lam_ty_le_hien_mac_bi_chan(tmp_path):
    """OR/RR/HR không phải tỷ lệ hiện mắc — nhánh cắt ngang dùng thẳng làm p."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(design_code="cross_sectional", effect_type="OR", effect_val=0.75),
        meta=_full_meta(prevalence_source="PMID: 30560792"),
    )
    assert _row(report, "G3-AUTO-03")["status"] == "BLOCK"
    assert report["status"] == G3Q.STATUS_BLOCKED


def test_chan_doan_khong_phai_auc_bi_chan(tmp_path):
    """Nhánh chẩn đoán thay mọi loại khác bằng hằng AUC=0.75 không nguồn."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(design_code="diagnostic", effect_type="OR", effect_val=1.8),
        meta=_full_meta(prevalence_source="PMID: 30560792"),
    )
    assert _row(report, "G3-AUTO-03")["status"] == "BLOCK"


def test_chan_doan_voi_auc_khong_bi_bat_oan(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(design_code="diagnostic", effect_type="AUC", effect_val=0.82),
        meta=_full_meta(prevalence_source="PMID: 30560792"),
        artifact=_artifact(standard_token="STARD"),
    )
    assert _row(report, "G3-AUTO-03")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Tiền đề: thiết kế không được là giá trị mặc định im lặng
# ════════════════════════════════════════════════════════════════════════════


def test_khong_co_g0_lan_g1_thi_chan(tmp_path):
    report = _evaluate(tmp_path, g0=False, g1=False)
    assert _row(report, "G3-AUTO-01")["status"] == "BLOCK"
    assert report["status"] == G3Q.STATUS_BLOCKED


def test_co_g0_nhung_thieu_g1_thi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, g0=True, g1=False)
    assert _row(report, "G3-AUTO-01")["status"] == "REVIEW"


def test_thiet_ke_con_mo_ho_khong_duoc_troi_xuong_g4(tmp_path):
    """G1 gắn ambiguous=true nghĩa là thiết kế mới chỉ là placeholder tạm."""
    report = _evaluate(tmp_path, checkpoint=_checkpoint(design_ambiguous=True))
    row = _row(report, "G3-AUTO-01")
    assert row["status"] == "REVIEW"
    assert "ambiguous" in row["evidence"]
    assert report["status"] != G3Q.STATUS_CONFIRMED


# ════════════════════════════════════════════════════════════════════════════
# Nguồn của effect size — luật nền "KHÔNG bịa"
# ════════════════════════════════════════════════════════════════════════════


def test_nhan_can_khong_duoc_tinh_la_nguon(tmp_path):
    """Chống lách nhãn: dán '[CẦN PMID/DOI]' không phải là có nguồn."""
    report = _evaluate(tmp_path, meta=_full_meta(effect_source="[CẦN PMID/DOI]"))
    assert _row(report, "G3-AUTO-05")["status"] == "REVIEW"


def test_pmid_va_doi_duoc_chap_nhan_lam_nguon():
    assert G3Q.source_kind("PMID: 30560792") == "PMID"
    assert G3Q.source_kind("doi 10.1136/bmj.k3750") == "DOI"
    assert G3Q.source_kind("MCID do chủ nhiệm ấn định là 8 điểm") == "MCID"
    assert G3Q.source_kind("Pilot nội bộ 40 ca") == "PILOT"
    assert G3Q.source_kind("") is None
    assert G3Q.source_kind("[CẦN BÁC SĨ ẤN ĐỊNH]") is None
    assert G3Q.source_kind("lấy từ y văn") is None


def test_effect_size_tho_bi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(effect_quality="crude"))
    assert _row(report, "G3-AUTO-06")["status"] == "REVIEW"


# ════════════════════════════════════════════════════════════════════════════
# Kiểm SỐ: nhất quán nội bộ
# ════════════════════════════════════════════════════════════════════════════


def test_bang_do_nhay_dan_nhan_dropout_sai_bi_bat(tmp_path):
    """Tiêu đề khai 'đã điều chỉnh dropout' nhưng ô cơ sở là N TRƯỚC dropout."""
    report = _evaluate(tmp_path, artifact=_artifact(base_cell=942))
    row = _row(report, "G3-AUTO-09")
    assert row["status"] == "REVIEW"
    assert "dropout" in row["evidence"]


def test_o_co_so_lech_khoi_n_chinh_bi_bat(tmp_path):
    """Bảng tính TRƯỚC khi áp FPC/cluster nên lệch hẳn khỏi N đã kết luận."""
    report = _evaluate(tmp_path, artifact=_artifact(base_cell=245))
    row = _row(report, "G3-AUTO-09")
    assert row["status"] == "REVIEW"
    assert "245" in row["evidence"]


def test_o_na_trong_bang_do_nhay_bi_bat(tmp_path):
    report = _evaluate(tmp_path, artifact=_artifact(na_cells=True))
    row = _row(report, "G3-AUTO-09")
    assert row["status"] == "REVIEW"
    assert "N/A" in row["evidence"]


def test_n_moi_nhom_khong_khop_n_tong_bi_bat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(n_per_group=100))
    row = _row(report, "G3-AUTO-09")
    assert row["status"] == "REVIEW"
    assert "n_per_group" in row["evidence"]


def test_thiet_ke_mot_nhom_khong_bi_bat_oan_ve_n_moi_nhom(tmp_path):
    """Cắt ngang là khảo sát MỘT nhóm — n_per_group == n_total là đúng."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="cross_sectional",
            effect_type="",
            effect_val=None,
            n_per_group=385,
            n_total=385,
            n_adjusted=482,
        ),
        meta=_full_meta(prevalence_source="p=0,5 theo quy ước thận trọng (WHO)"),
        artifact=_artifact(n_total=385, n_adjusted=482, base_cell=482, standard_token="STROBE"),
    )
    evidence = _row(report, "G3-AUTO-09")["evidence"]
    assert "n_per_group" not in evidence


def test_bang_do_nhay_khop_thi_khong_bao_loi(tmp_path):
    report = _evaluate(tmp_path, artifact=_artifact(base_cell=1178))
    assert _row(report, "G3-AUTO-09")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# alpha / power / bội
# ════════════════════════════════════════════════════════════════════════════


def test_power_thap_bi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(power=0.50))
    assert _row(report, "G3-AUTO-07")["status"] == "REVIEW"


def test_alpha_lon_bi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(alpha=0.20))
    assert _row(report, "G3-AUTO-07")["status"] == "REVIEW"


def test_da_ket_cuc_chinh_ma_khong_khai_chien_luoc_alpha_bi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, meta=_full_meta(primary_outcome_count=3))
    row = _row(report, "G3-AUTO-07")
    assert row["status"] == "REVIEW"
    assert "alpha" in row["evidence"].lower()


def test_phan_tich_giua_ky_co_khai_chien_luoc_thi_dat(tmp_path):
    report = _evaluate(
        tmp_path,
        meta=_full_meta(
            interim_analysis_planned=True,
            multiplicity_strategy="alpha-spending O'Brien-Fleming, 2 lần nhìn",
        ),
    )
    assert _row(report, "G3-AUTO-07")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Non-inferiority và thiết kế cụm
# ════════════════════════════════════════════════════════════════════════════


def test_khong_thua_kem_thieu_bien_bi_chan(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=None),
    )
    assert _row(report, "G3-AUTO-11")["status"] == "BLOCK"


def test_khong_thua_kem_co_bien_nhung_thieu_bien_minh_bi_ra_soat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
    )
    row = _row(report, "G3-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "BIỆN MINH" in row["evidence"]


def test_khong_thua_kem_du_bien_minh_va_nguon_thi_dat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
        meta=_full_meta(**_NI_FDA),
    )
    assert _row(report, "G3-AUTO-11")["status"] == "PASS"


def test_khong_khai_khung_quy_dinh_cho_bien_bi_bat(tmp_path):
    """FDA và EMA mâu thuẫn nhau — phải nói rõ đang theo khung nào."""
    meta = dict(_NI_FDA)
    meta.pop("ni_regulatory_framework")
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
        meta=_full_meta(**meta),
    )
    row = _row(report, "G3-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "khung quy định" in row["evidence"]


def test_ema_cam_dinh_nghia_bien_theo_ty_le_hieu_qua(tmp_path):
    """EMA nói rõ KHÔNG phù hợp khi Δ là một tỷ lệ của hiệu số thuốc chứng–giả dược."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
        meta=_full_meta(
            ni_regulatory_framework="EMA",
            margin_justification="Chọn Δ bằng 50% của hiệu số thuốc chứng so với giả dược",
            margin_source="PMID: 30560792",
        ),
    )
    row = _row(report, "G3-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "EMA" in row["evidence"]


def test_ema_cam_bien_minh_vi_nghien_cuu_nho(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
        meta=_full_meta(
            ni_regulatory_framework="EMA",
            margin_justification="Nới biên vì nghiên cứu nhỏ, khó tuyển đủ bệnh nhân",
            margin_source="PMID: 30560792",
        ),
    )
    assert _row(report, "G3-AUTO-11")["status"] == "REVIEW"


def test_khung_fda_doi_tach_bach_m1_va_m2(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(hypothesis_type="non_inferiority", margin=0.10, outcome_direction="higher_better"),
        meta=_full_meta(
            ni_regulatory_framework="FDA",
            margin_justification="Theo ý kiến chuyên gia lâm sàng của khoa",
            margin_source="PMID: 30560792",
        ),
    )
    row = _row(report, "G3-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "M1" in row["evidence"]


def test_thiet_ke_cum_thieu_nguon_icc_bi_ra_soat(tmp_path):
    report = _eval_cum(tmp_path, _full_meta(icc=0.02, cluster_size=25))
    row = _row(report, "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "ICC" in row["evidence"]


def test_thiet_ke_cum_du_thong_tin_thi_dat(tmp_path):
    report = _eval_cum(tmp_path, _full_meta(**_CLUSTER_OK))
    assert _row(report, "G3-AUTO-12")["status"] == "PASS"


def test_design_effect_tu_khai_sai_so_hoc_bi_bat(tmp_path):
    """Không tin con số tự khai: DE phải khớp 1+(m−1)·ICC."""
    report = _eval_cum(tmp_path, _full_meta(**{**_CLUSTER_OK, "design_effect": 1.10}))
    row = _row(report, "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "design_effect" in row["evidence"]


def test_design_effect_dung_so_hoc_thi_dat(tmp_path):
    report = _eval_cum(tmp_path, _full_meta(**{**_CLUSTER_OK, "design_effect": 1 + 24 * 0.02}))
    assert _row(report, "G3-AUTO-12")["status"] == "PASS"


def test_so_chum_nho_phai_khai_hieu_chinh_mau_nho(tmp_path):
    report = _eval_cum(tmp_path, _full_meta(**{**_CLUSTER_OK, "n_clusters": 18}), n_clusters=18)
    row = _row(report, "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "hiệu chỉnh mẫu nhỏ" in row["evidence"]


# ── Số chùm CỐ ĐỊNH (09/10/2026) ──────────────────────────────────────────────────────────────────────────────
# Ca C1a: 50 bàn khám thật, m = 20, N kế hoạch 1000, N tối thiểu ≈ 540 ⇒ cần ≥ 27 chùm. checkpoint["n_clusters"] là
# số chùm TỐI THIỂU cần cho N tối thiểu, không phải số chùm của đề tài. Khai n_clusters là SỰ THẬT THIẾT KẾ; chỉ
# được tin để nới phép thử mẫu nhỏ khi nó nhiều hơn mức tối thiểu VÀ khớp N kế hoạch ÷ m.
_CHUM_CO_DINH = {**_CLUSTER_OK, "cluster_size": 20, "n_clusters": 50}


def _eval_cum_ke_hoach(tmp_path, meta, *, confirmed_n=None, **kw):
    """Như _eval_cum nhưng checkpoint có N kế hoạch (confirmed_n) — thiết kế có số chùm cố định."""
    cp = _checkpoint_cum(**kw)
    cp["confirmed_n"] = confirmed_n
    return _evaluate(tmp_path, checkpoint=cp, meta=meta,
                     artifact=_artifact(n_total=cp["n_total"], n_adjusted=cp["n_adjusted"],
                                        base_cell=cp["n_adjusted"]))


def test_so_chum_co_dinh_nhieu_hon_toi_thieu_khop_n_ke_hoach_thi_dat(tmp_path):
    """Ca C1a: khai 50 chùm, N kế hoạch 1000 = 50 × m 20, tối thiểu cần 27 ⇒ PASS; không bị báo «khác số chùm suy từ N»
    và phép thử mẫu nhỏ chạy trên 50 (≥ 40) nên không đòi hiệu chỉnh."""
    report = _eval_cum_ke_hoach(tmp_path, _full_meta(**_CHUM_CO_DINH), confirmed_n=1000, n_clusters=27, m=20)
    row = _row(report, "G3-AUTO-12")
    assert row["status"] == "PASS", row
    assert "số chùm=50" in row["evidence"] and "tối thiểu cần 27" in row["evidence"]


def test_so_chum_co_dinh_van_bi_phep_thu_mau_nho_khi_duoi_40(tmp_path):
    """Chiều an toàn: 30 chùm cố định (đã khớp N kế hoạch 600 = 30 × 20) vẫn < 40 ⇒ VẪN đòi hiệu chỉnh mẫu nhỏ."""
    meta = {**_CHUM_CO_DINH, "n_clusters": 30}
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**meta), confirmed_n=600, n_clusters=27, m=20), "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "số chùm=30 < 40" in row["evidence"] and "hiệu chỉnh mẫu nhỏ" in row["evidence"]
    assert "khác số chùm suy từ N" not in row["evidence"], "30 khớp N kế hoạch nên không phải khai sai"
    co = _full_meta(**meta, small_sample_correction="Kenward-Roger, bậc tự do Satterthwaite")
    row_co = _row(_eval_cum_ke_hoach(tmp_path, co, confirmed_n=600, n_clusters=27, m=20), "G3-AUTO-12")
    assert row_co["status"] == "PASS", row_co


def test_so_chum_khai_nhieu_hon_toi_thieu_ma_thieu_n_ke_hoach_thi_van_than_trong(tmp_path):
    """Không có N kế hoạch để đối chiếu số chùm × m ⇒ không tin lời khai: báo lệch VÀ phép thử mẫu nhỏ chạy trên 27."""
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**_CHUM_CO_DINH), confirmed_n=None, n_clusters=27, m=20),
               "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "khai tay=50 khác số chùm suy từ N=27" in row["evidence"] and "confirmed_n" in row["evidence"]
    assert "số chùm=27 < 40" in row["evidence"], "chưa đối chiếu được thì KHÔNG nới phép thử mẫu nhỏ"


def test_so_chum_khai_khong_khop_n_ke_hoach_thi_khong_duoc_tin(tmp_path):
    """Khai 50 chùm nhưng N kế hoạch 700 ÷ m 20 = 35 chùm ⇒ lời khai mâu thuẫn với chính N đã chốt."""
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**_CHUM_CO_DINH), confirmed_n=700, n_clusters=27, m=20),
               "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "không khớp N kế hoạch" in row["evidence"] and "35" in row["evidence"]
    assert "số chùm=27 < 40" in row["evidence"]


def test_so_chum_khai_it_hon_toi_thieu_thi_phep_thu_mau_nho_chay_tren_so_it_hon(tmp_path):
    """Khai 18 chùm trong khi N tối thiểu cần 60 chùm: N tối thiểu không đạt được VÀ 18 < 40 ⇒ đòi hiệu chỉnh.
    Bản cũ chạy phép thử trên 60 (số suy từ N) nên chỉ báo lệch, im lặng về mẫu nhỏ."""
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**{**_CLUSTER_OK, "n_clusters": 18}), n_clusters=60, m=25),
               "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "khai tay=18 khác số chùm suy từ N=60" in row["evidence"] and "ít hơn" in row["evidence"]
    assert "số chùm=18 < 40" in row["evidence"]


def test_n_ke_hoach_lon_hon_khong_tu_nang_so_chum(tmp_path):
    """Phương án «suy số chùm từ N kế hoạch» bị bác: N tăng có thể do chùm TO hơn chứ không phải thêm chùm, nên
    không khai n_clusters thì N kế hoạch 1000 cũng KHÔNG làm số chùm từ 27 lên 50 — phép thử mẫu nhỏ vẫn chạy
    trên mức tối thiểu."""
    meta = {k: v for k, v in _CHUM_CO_DINH.items() if k != "n_clusters"}
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**meta), confirmed_n=1000, n_clusters=27, m=20), "G3-AUTO-12")
    assert row["status"] == "REVIEW" and "số chùm=27 < 40" in row["evidence"]


def test_so_chum_khai_lech_trong_dung_sai_lam_tron_nhu_cu(tmp_path):
    """Lệch ±1 chùm do làm tròn lên vẫn coi là khớp mức tối thiểu (hành vi cũ giữ nguyên)."""
    for khai in (26, 27, 28):
        meta = {**_CHUM_CO_DINH, "n_clusters": khai, "small_sample_correction": "Kenward-Roger"}
        row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**meta), n_clusters=27, m=20), "G3-AUTO-12")
        assert row["status"] == "PASS" and "khác số chùm suy từ N" not in row["evidence"], (khai, row)


# 11/10/2026 — «thiếu CV cỡ chùm» là SỐ LIỆU ĐỜI THỰC (HIS) ⇒ còn MỘT vấn đề đó thì bằng chứng mở đầu
# «CHỜ NGƯỜI (PI — …)» để bảng trách nhiệm xếp «chờ người»; trạng thái vẫn REVIEW. Có vấn đề khác đi kèm ⇒ vẫn là
# việc agent (không tiền tố).
def _khong_khai_deu(meta: dict) -> dict:
    return {k: v for k, v in meta.items() if k != "equal_cluster_sizes"}


def test_chi_thieu_cv_co_chum_la_cho_nguoi_pi(tmp_path):
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**_khong_khai_deu(_CHUM_CO_DINH)), confirmed_n=1000,
                                  n_clusters=27, m=20), "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert row["evidence"].startswith(G3Q.CHO_NGUOI_SO_LIEU_CUM) and G3Q.VAN_DE_CUM_CHO_SO_LIEU in row["evidence"]
    assert "HIS" in row["action"] and "KHÔNG ước đoán" in row["action"]


def test_thieu_cv_kem_van_de_khac_van_la_viec_agent(tmp_path):
    meta = _khong_khai_deu({k: v for k, v in _CHUM_CO_DINH.items() if k != "icc_source"})
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**meta), confirmed_n=1000, n_clusters=27, m=20),
               "G3-AUTO-12")
    assert row["status"] in ("REVIEW", "BLOCK") and G3Q.VAN_DE_CUM_CHO_SO_LIEU in row["evidence"]
    assert not row["evidence"].startswith("CHỜ NGƯỜI"), row["evidence"]


def test_co_cv_that_thi_khong_con_cho_nguoi(tmp_path):
    meta = {**_khong_khai_deu(_CHUM_CO_DINH), "cluster_size_cv": 0.15}
    row = _row(_eval_cum_ke_hoach(tmp_path, _full_meta(**meta), confirmed_n=1000, n_clusters=27, m=20), "G3-AUTO-12")
    assert row["status"] == "PASS" and "CHỜ NGƯỜI" not in row["evidence"]


def test_tien_to_khop_bo_doc_cho_nguoi_cua_hoi_dong():
    import hoi_dong_cong as HD
    m = HD._CHO_NGUOI.match(G3Q.CHO_NGUOI_SO_LIEU_CUM + G3Q.VAN_DE_CUM_CHO_SO_LIEU)
    assert m and m.group(1).strip() == "PI"


def test_co_chum_khong_deu_va_cv_lon_phai_hieu_chinh(tmp_path):
    meta = {**_CLUSTER_OK}
    meta.pop("equal_cluster_sizes")
    report = _eval_cum(tmp_path, _full_meta(**{**meta, "cluster_size_cv": 0.65}))
    row = _row(report, "G3-AUTO-12")
    assert row["status"] == "REVIEW"
    assert "CV" in row["evidence"]


def test_co_chum_khong_deu_nhung_cv_nho_thi_dat(tmp_path):
    meta = {**_CLUSTER_OK}
    meta.pop("equal_cluster_sizes")
    report = _eval_cum(tmp_path, _full_meta(**{**meta, "cluster_size_cv": 0.15}))
    assert _row(report, "G3-AUTO-12")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Hiệu chỉnh quần thể hữu hạn dùng đúng chỗ
# ════════════════════════════════════════════════════════════════════════════


def test_fpc_trong_thu_nghiem_ngau_nhien_bi_chan(tmp_path):
    """FPC làm N nhỏ đi sai lầm trong RCT — suy luận không nhắm vào quần thể hữu hạn."""
    report = _evaluate(tmp_path, meta=_full_meta(population_n=5000))
    row = _row(report, "G3-AUTO-16")
    assert row["status"] == "BLOCK"
    assert report["status"] == G3Q.STATUS_BLOCKED


def test_fpc_trong_khao_sat_cat_ngang_co_nguon_thi_dat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="cross_sectional",
            effect_type="",
            effect_val=None,
            n_per_group=385,
            n_total=385,
            n_adjusted=482,
        ),
        meta=_full_meta(
            population_n=1200,
            population_n_source="Danh sách bệnh nhân quản lý tại khoa năm 2025",
            prevalence_source="p=0,5 theo quy ước thận trọng",
        ),
        artifact=_artifact(n_total=385, n_adjusted=482, base_cell=482, standard_token="STROBE"),
    )
    assert _row(report, "G3-AUTO-16")["status"] == "PASS"


def test_fpc_khong_khai_thi_khong_bat_loi_oan(tmp_path):
    report = _evaluate(tmp_path)
    assert _row(report, "G3-AUTO-16")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Thiết kế không dùng power phải dùng đúng khung thay thế
# ════════════════════════════════════════════════════════════════════════════


def test_dinh_tinh_thieu_quy_tac_dung_bi_ra_soat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="qualitative",
            effect_type="",
            effect_val=None,
            n_total=0,
            n_adjusted=0,
            n_per_group=0,
            confirmed_n=20,
        ),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="COREQ"),
    )
    row = _row(report, "G3-AUTO-17")
    assert row["status"] == "REVIEW"
    assert "QUY TẮC DỪNG" in row["evidence"]


def test_dinh_tinh_co_quy_tac_dung_thi_dat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="qualitative",
            effect_type="",
            effect_val=None,
            n_total=0,
            n_adjusted=0,
            n_per_group=0,
            confirmed_n=20,
        ),
        meta=_full_meta(
            saturation_stopping_rule="Dừng khi 3 cuộc phỏng vấn liên tiếp không sinh mã mới"
        ),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="COREQ"),
    )
    assert _row(report, "G3-AUTO-17")["status"] == "PASS"


def test_tieu_de_bang_do_nhay_cua_template_khong_bi_coi_la_ngon_ngu_power(tmp_path):
    """Chữ 'Power × Effect size' là do template in cứng — không phải lỗi nhà nghiên cứu."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="qualitative",
            effect_type="",
            effect_val=None,
            n_total=0,
            n_adjusted=0,
            n_per_group=0,
            confirmed_n=20,
        ),
        meta=_full_meta(saturation_stopping_rule="Dừng khi bão hòa theo quy tắc 3 cuộc"),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="COREQ"),
    )
    assert "power" not in _row(report, "G3-AUTO-17")["evidence"].lower()


def test_tong_quan_he_thong_khong_nhac_ris_bi_ra_soat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="sr_ma",
            effect_type="",
            effect_val=None,
            n_total=0,
            n_adjusted=0,
            n_per_group=0,
            confirmed_n=30,
        ),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="PRISMA 2020"),
    )
    row = _row(report, "G3-AUTO-17")
    assert row["status"] == "REVIEW"
    assert "information size" in row["evidence"]


def test_tong_quan_he_thong_co_ris_tsa_thi_dat(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="sr_ma",
            effect_type="",
            effect_val=None,
            n_total=0,
            n_adjusted=0,
            n_per_group=0,
            confirmed_n=30,
        ),
        meta=_full_meta(
            confirmed_n_method="RIS 3200 người theo TSA có hiệu chỉnh D², biên Lan-DeMets"
        ),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="PRISMA 2020"),
    )
    assert _row(report, "G3-AUTO-17")["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# N chốt: đề tài tự khai thiếu lực không được đi qua im lặng
# ════════════════════════════════════════════════════════════════════════════


def test_n_chot_thap_hon_n_toi_thieu_bi_ra_soat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(confirmed_n=300))
    row = _row(report, "G3-AUTO-13")
    assert row["status"] == "REVIEW"
    assert "THẤP HƠN" in row["evidence"]


def test_n_chot_du_thi_dat(tmp_path):
    report = _evaluate(tmp_path, checkpoint=_checkpoint(confirmed_n=1200))
    assert _row(report, "G3-AUTO-13")["status"] == "PASS"


def test_thiet_ke_khong_dung_power_phai_ghi_phuong_phap_tinh_n(tmp_path):
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="sr_ma",
            effect_type="",
            effect_val=None,
            n_per_group=0,
            n_total=0,
            n_adjusted=0,
            confirmed_n=30,
            formula_used="[CẦN — Tổng quan hệ thống dùng RIS/TSA, không dùng công thức power]",
        ),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="PRISMA 2020"),
    )
    row = _row(report, "G3-AUTO-13")
    assert row["status"] == "REVIEW"
    assert "phương pháp" in row["evidence"]


def test_thiet_ke_khong_dung_power_khong_bi_doi_nguon_dropout(tmp_path):
    """n_total=0 nghĩa là dropout không hề vào phép tính — đừng bắt lỗi oan."""
    report = _evaluate(
        tmp_path,
        checkpoint=_checkpoint(
            design_code="qualitative",
            effect_type="",
            effect_val=None,
            n_per_group=0,
            n_total=0,
            n_adjusted=0,
            confirmed_n=20,
            formula_used="[CẦN — Bão hòa dữ liệu / information power]",
        ),
        meta=_full_meta(dropout_source=None, confirmed_n_method="Bão hòa dữ liệu, Malterud"),
        artifact=_artifact(n_total=0, n_adjusted=0, standard_token="COREQ"),
    )
    assert "bỏ cuộc" not in _row(report, "G3-AUTO-08")["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# Tầng người thật
# ════════════════════════════════════════════════════════════════════════════


def test_vai_tro_khong_phai_thong_ke_vien_hay_chu_nhiem_bi_tu_choi(tmp_path):
    report = _evaluate(tmp_path, meta=_full_meta(reviewed_by_role="IRB"))
    assert _row(report, "G3-HUMAN-06")["status"] == "REVIEW"


def test_vai_tro_thong_ke_vien_va_chu_nhiem_deu_duoc_chap_nhan(tmp_path):
    for role in ("BIOSTATISTICIAN", "STATISTICIAN", "PI"):
        report = _evaluate(tmp_path, meta=_full_meta(reviewed_by_role=role))
        assert _row(report, "G3-HUMAN-06")["status"] == "PASS", role


def test_thoi_diem_ra_soat_o_tuong_lai_bi_tu_choi(tmp_path):
    future = (datetime.now() + timedelta(days=3)).isoformat()
    report = _evaluate(tmp_path, meta=_full_meta(reviewed_at=future))
    assert _row(report, "G3-HUMAN-06")["status"] == "REVIEW"


def test_ket_cuc_duoc_tinh_luc_lech_ket_cuc_chinh_bi_bat(tmp_path):
    report = _evaluate(
        tmp_path, meta=_full_meta(powered_for_outcome="Thời gian nằm viện")
    )
    row = _row(report, "G3-HUMAN-04")
    assert row["status"] == "REVIEW"
    assert "khác kết cục chính" in row["evidence"]


def test_thu_nghiem_then_chot_can_thong_ke_vien_doc_lap(tmp_path):
    report = _evaluate(tmp_path, meta=_full_meta(pivotal_trial=True))
    row = _row(report, "G3-HUMAN-07")
    assert row["status"] == "REVIEW"
    assert "ĐỘC LẬP" in row["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# Bẫy tích hợp và đường PASS
# ════════════════════════════════════════════════════════════════════════════


def test_doc_dung_guardrail_dang_chuoi_cua_g3(tmp_path):
    """G3 ghi guardrail là CHUỖI, không phải dict {'passed': bool} như G1/G2."""
    ok = _evaluate(tmp_path, checkpoint=_checkpoint(guardrail="✅ PASS"))
    assert _row(ok, "G3-AUTO-00")["status"] == "PASS"
    bad = _evaluate(
        tmp_path, checkpoint=_checkpoint(guardrail="🚧 BLOCKED — CHỜ INPUT ĐỜI THỰC")
    )
    assert _row(bad, "G3-AUTO-00")["status"] == "BLOCK"
    assert bad["status"] == G3Q.STATUS_BLOCKED


def test_du_moi_dieu_kien_thi_dat_pass_g3_confirmed(tmp_path):
    report = _evaluate(
        tmp_path,
        artifact=_artifact(base_cell=1178),
        meta=_full_meta(),
    )
    failing = [
        row
        for row in report["automatic_criteria"] + report["human_criteria"]
        if row["status"] != "PASS"
    ]
    assert not failing, failing
    assert report["status"] == G3Q.STATUS_CONFIRMED
    assert report["human_confirmation_complete"] is True


def test_thieu_xac_nhan_nguoi_that_thi_dung_o_cho_ra_soat(tmp_path):
    report = _evaluate(
        tmp_path,
        artifact=_artifact(base_cell=1178),
        meta=_full_meta(reviewed_by_role="", reviewed_at=""),
    )
    assert report["status"] == G3Q.STATUS_DRAFT_REVIEW
    assert report["parameters_ready_for_review"] is True


# ════════════════════════════════════════════════════════════════════════════
# Xuất báo cáo và hợp đồng downstream
# ════════════════════════════════════════════════════════════════════════════


def test_ghi_bao_cao_ra_ca_json_va_markdown(tmp_path):
    report = _evaluate(tmp_path)
    md_path = G3Q.write_quality_report("TEST-G3", tmp_path, report)
    assert md_path.exists()
    assert (tmp_path / "G3_QUALITY_REPORT.json").exists()
    text = md_path.read_text(encoding="utf-8")
    assert "Cần bác sĩ kiểm chứng" in text
    assert "G3-AUTO-05" in text
    assert "PMID:30560792" in text


def test_cap_nhat_checkpoint_giu_nguyen_khoa_downstream(tmp_path):
    """run_g4_auto đọc đúng các khóa này để dựng SAP — không được đụng vào."""
    checkpoint_path = tmp_path / "G3_checkpoint.json"
    original = _checkpoint(confirmed_n=1200, hypothesis_type="non_inferiority", margin=0.1)
    checkpoint_path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8", newline="\n")
    report = _evaluate(tmp_path, checkpoint=original)
    G3Q.refresh_checkpoint(
        study="TEST-G3",
        out_dir=tmp_path,
        report=report,
        quality_report_path=tmp_path / "G3_QUALITY_REPORT.md",
    )
    updated = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    for key in (
        "n_adjusted",
        "n_total",
        "n_per_group",
        "confirmed_n",
        "alpha",
        "power",
        "effect_val",
        "effect_type",
        "sd",
        "hypothesis_type",
        "margin",
    ):
        assert updated[key] == original[key], key
    assert updated["quality_gate"]["status"] == report["status"]
    assert updated["quality_contract_version"] == G3Q.QUALITY_CONTRACT_VERSION


def test_evaluate_study_chay_tron_ven_tren_thu_muc_that(tmp_path):
    study = "TEST-G3"
    (tmp_path / f"G3_A4_SAMPLE_SIZE_{study}.md").write_text(
        _artifact(base_cell=1178), encoding="utf-8", newline="\n"
    )
    (tmp_path / "G3_checkpoint.json").write_text(
        json.dumps(_checkpoint(), ensure_ascii=False), encoding="utf-8", newline="\n"
    )
    # 04/10/2026 (soát từng cổng): G1 được chấm SỐNG — dựng chuỗi G0→G1 đã chốt thật rồi gộp khối G3 đầy đủ.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _chuoi_da_chot import dung_g0_g1_da_chot
    meta = dung_g0_g1_da_chot(tmp_path, study, mau_hieu_qua=[])
    g3 = _chot(_full_meta(powered_for_outcome=meta["gate_params"]["G1"]["primary_outcome"]["name"]),
               _checkpoint())["gate_params"]["G3"]
    meta["gate_params"]["G3"] = g3
    (tmp_path / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n"
    )
    report = G3Q.evaluate_study(study, tmp_path, write=True)
    assert report["status"] == G3Q.STATUS_CONFIRMED
    assert (tmp_path / "G3_QUALITY_REPORT.md").exists()
    assert (tmp_path / "G3_QUALITY_REPORT.json").exists()


def test_bang_do_nhay_duoc_boc_dung_so_o(tmp_path):
    table = G3Q.parse_sensitivity_table(_artifact(base_cell=1178))
    assert table["found"] is True
    assert table["cells_total"] == 9
    assert table["cells_na"] == 0
    assert table["header_dropout_pct"] == 20
    assert G3Q.sensitivity_base_cell(table, 0.80) == 1178


# ════════════════════════════════════════════════════════════════════════════
# Test TÍCH HỢP THẬT — gọi CLI run_g3_auto.py thật, không dùng fixture văn bản
# tự viết tay. Đóng lỗ hổng "test yếu": các test ở trên dùng _artifact() giả
# lập nên không phát hiện được rằng generate_artifact() THẬT không hề in tên
# chuẩn báo cáo (G3-AUTO-10) và luôn in ngôn ngữ power ngay cả cho thiết kế
# không dùng power (G3-AUTO-17/qualitative) — hai lỗi CRITICAL/HIGH chỉ lộ ra
# khi chạy pipeline thật (phát hiện qua kiểm định độc lập 2026-07-29).
# ════════════════════════════════════════════════════════════════════════════


class TestPipelineThatKhongDungFixtureGia:
    def test_rct_dat_auto10_qua_pipeline_that(self):
        study = "TEST-AUDIT-G3-PIPELINE-RCT"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _seed_g0_g1(study_dir, "rct")
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "8", "--effect-type", "ARR%", "--p0", "0.30"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            report = json.loads((study_dir / "G3_QUALITY_REPORT.json").read_text(encoding="utf-8"))
            row = next(r for r in report["automatic_criteria"] if r["id"] == "G3-AUTO-10")
            assert row["status"] == "PASS", row
            assert "CONSORT 2025" in (study_dir / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
        finally:
            _rmtree_retry(study_dir)

    def test_sr_ma_khong_con_pass_gia_qua_pipeline_that(self):
        """Trước khi sửa: formula_used tự in 'RIS/TSA' vô điều kiện nên
        G3-AUTO-17 LUÔN PASS dù chưa ai tính RIS thật. Nay phải REVIEW."""
        study = "TEST-AUDIT-G3-PIPELINE-SRMA"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _seed_g0_g1(study_dir, "sr_ma")
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"), "--study", study, "--confirmed-n", "30"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            artifact_text = (study_dir / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
            assert "RIS" in artifact_text or "TSA" in artifact_text  # xác nhận vẫn còn tautology-bait
            report = json.loads((study_dir / "G3_QUALITY_REPORT.json").read_text(encoding="utf-8"))
            row = next(r for r in report["automatic_criteria"] if r["id"] == "G3-AUTO-17")
            assert row["status"] == "REVIEW", row
        finally:
            _rmtree_retry(study_dir)

    def test_qualitative_khong_con_bi_khoa_cung_qua_pipeline_that(self):
        """Trước khi sửa: PHẦN 4 luôn in 'α =' + 'lực thống kê' vô điều kiện,
        khiến G3-AUTO-17 KHÔNG BAO GIỜ đạt cho thiết kế định tính. Nay phải
        REVIEW vì thiếu quy tắc dừng bão hòa (lý do THẬT), rồi PASS khi được
        cấp quy tắc dừng — chứng minh không còn bị khóa cứng."""
        study = "TEST-AUDIT-G3-PIPELINE-QUAL"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _seed_g0_g1(study_dir, "qualitative")
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"), "--study", study, "--confirmed-n", "20"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            artifact_text = (study_dir / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
            assert "α =" not in artifact_text and "lực thống kê" not in artifact_text

            report = json.loads((study_dir / "G3_QUALITY_REPORT.json").read_text(encoding="utf-8"))
            row = next(r for r in report["automatic_criteria"] if r["id"] == "G3-AUTO-17")
            assert row["status"] == "REVIEW", row
            # Lý do REVIEW phải là thiếu quy tắc dừng THẬT — không phải bị bắt
            # nhầm vì "ngôn ngữ kiểm định power" (đúng lỗi đã sửa).
            assert "khối cỡ mẫu dán vào đề cương" not in row["evidence"]
            assert "QUY TẮC DỪNG" in row["evidence"]

            _meta = json.loads((study_dir / "study_meta.json").read_text(encoding="utf-8"))
            _meta["gate_params"].setdefault("G3", {})["saturation_stopping_rule"] = (
                "Dừng khi 3 cuộc phỏng vấn liên tiếp không sinh mã mới")
            (study_dir / "study_meta.json").write_text(
                json.dumps(_meta, ensure_ascii=False), encoding="utf-8", newline="\n"
            )
            result2 = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"), "--study", study, "--confirmed-n", "20"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert result2.returncode == 0, result2.stdout + result2.stderr
            report2 = json.loads((study_dir / "G3_QUALITY_REPORT.json").read_text(encoding="utf-8"))
            row2 = next(r for r in report2["automatic_criteria"] if r["id"] == "G3-AUTO-17")
            assert row2["status"] == "PASS", row2
        finally:
            _rmtree_retry(study_dir)
