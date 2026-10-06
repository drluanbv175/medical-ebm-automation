"""G6 nối hợp đồng ô trống chung (03–04/10/2026) — đề tài giả dựng trong tmp_path (không đụng exports/).

Khoá ba lỗ đo được 03/10: (1) seed đọc từ CÂU VÍ DỤ trong nhãn «[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]» ⇒
cổng báo «seed khớp SAP» khi SAP chưa chốt seed; (2) seed/alpha không đọc được vẫn cho trạng thái chờ duyệt;
(3) §12 của SAP không phải RCT kéo tới hết tệp nên alpha đọc từ hộp chứng nhận khoá. Cộng G6-AUTO-07 (tham số
riêng của khuôn sinh script).
Lệch seed/alpha vẫn BLOCKED như cũ; đề tài điền thật vẫn tới READY_FOR_STATISTICIAN_REVIEW.

04/10/2026 (soát từng cổng G6): G6-AUTO-01 đòi G4 khoá THẬT (sổ cái + G4 chấm trực tiếp), không nhận g4_was_locked tự
khai — đề tài giả trong tmp_path giả lập đúng kết quả đó qua _g4_da_khoa; SAP có §4 (G6-AUTO-09 họ mô hình) và script
ghi sessionInfo() (G6-AUTO-10) như một đề tài điền thật.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDY = "ZZT-G6-O-TRONG"


def _nap():
    spec = importlib.util.spec_from_file_location("g6qg_o_trong", ROOT / "tools" / "g6_quality_gate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["g6qg_o_trong"] = m
    spec.loader.exec_module(m)
    return m


G6 = _nap()

@pytest.fixture(autouse=True)
def _g4_khoa_that(monkeypatch):
    monkeypatch.setattr(G6, "_g4_da_khoa", lambda *a, **k: (True, "giả lập: sổ cái + G4 PASS_G4_SAP_LOCKED"))


SEED_THAT = "Seed ngẫu nhiên: set.seed(2026) cho bootstrap/đa phép gán."
ALPHA_THAT = "Alpha: 0.05 hai phía."


def _sap(seed: str = SEED_THAT, alpha: str = ALPHA_THAT, hop_khoa: str = "alpha 0.05 (đã khoá)") -> str:
    return (
        "# SAP\n\n### §2 Kết cục\nKết cục chính: `diem_hai_long` (thang 5 mức).\n\n"
        "### §4 Phân tích chính\nHồi quy tuyến tính (lm) cho `diem_hai_long`.\n\n"
        "### §7 Nhóm con\nKhông có phân tích nhóm con.\n\n"
        f"### §10 Phần mềm & tái lập\nR 4.4.1.\n{seed}\n\n"
        f"### §12 Ngưỡng ý nghĩa\n{alpha}\n\n"
        f"---\n\n## PHẦN 5 — PHIẾU KHOÁ\n{hop_khoa}\nKý: ____________\n"
    )


SCRIPT_THAT = ("SEED <- 2026\nset.seed(SEED)\nalpha <- 0.05\nfit <- lm(diem_hai_long ~ tuoi, data = d)\n"
               "writeLines(capture.output(sessionInfo()), \"session_info.txt\")\n")


def _de_tai(tmp_path: Path, sap: str, script: str = SCRIPT_THAT, a7: str = "**Phân tích chính:** Hồi quy tuyến tính\n"):
    d = tmp_path / STUDY
    (d / "scripts").mkdir(parents=True)
    (d / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(sap, encoding="utf-8", newline="\n")
    (d / f"G6_A7_ANALYSIS_SCRIPTS_{STUDY}.md").write_text(a7, encoding="utf-8", newline="\n")
    (d / "G6_checkpoint.json").write_text(json.dumps({"g4_was_locked": True}), encoding="utf-8", newline="\n")
    (d / "scripts" / "01_analysis.R").write_text(script, encoding="utf-8", newline="\n")
    return G6.evaluate_study(STUDY, d, write=False)


def _ck(bao, ma):
    return next(k for k in bao["checks"] if k["id"] == ma)


def test_de_tai_dien_that_toi_ready(tmp_path):
    bao = _de_tai(tmp_path, _sap())
    assert bao["status"] == "READY_FOR_STATISTICIAN_REVIEW", [k for k in bao["checks"] if k["pass"] is not True]
    assert _ck(bao, "G6-AUTO-02")["pass"] is True and _ck(bao, "G6-AUTO-03")["pass"] is True
    assert _ck(bao, "G6-AUTO-07")["pass"] is True


def test_seed_trong_cau_vi_du_cua_nhan_khong_phai_seed_da_chot(tmp_path):
    bao = _de_tai(tmp_path, _sap(seed="Seed: [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]"))
    c = _ck(bao, "G6-AUTO-02")
    assert c["pass"] is None and "câu ví dụ" in c["detail"]
    assert bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


def test_seed_khong_doc_duoc_la_draft(tmp_path):
    bao = _de_tai(tmp_path, _sap(seed="Tái lập: dùng renv."))
    assert _ck(bao, "G6-AUTO-02")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


def test_seed_khai_khong_ap_dung_khong_giu_draft(tmp_path):
    bao = _de_tai(tmp_path, _sap(seed="Seed: không áp dụng (không có bước ngẫu nhiên)."))
    assert _ck(bao, "G6-AUTO-02")["pass"] is None and bao["status"] == "READY_FOR_STATISTICIAN_REVIEW"


def test_seed_lech_van_blocked(tmp_path):
    bao = _de_tai(tmp_path, _sap(seed="Seed: set.seed(9999)"))
    assert _ck(bao, "G6-AUTO-02")["pass"] is False and bao["status"] == "BLOCKED"


def test_seed_dung_nhung_dong_seed_con_o_trong_la_draft(tmp_path):
    bao = _de_tai(tmp_path, _sap(seed="Seed: set.seed(2026) — phần mềm [TO BE COMPLETED]"))
    assert _ck(bao, "G6-AUTO-02")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


def test_alpha_12_trong_khong_doc_tu_hop_khoa(tmp_path):
    """§12 còn ô trống; hộp khoá PHẦN 5 sau «---»/«## » ghi alpha 0.05 — bản cũ đọc nhầm từ đó ⇒ PASS."""
    bao = _de_tai(tmp_path, _sap(alpha="Alpha: [CẦN BÁC SĨ ẤN ĐỊNH]"))
    assert _ck(bao, "G6-AUTO-03")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


def test_alpha_lech_van_blocked(tmp_path):
    bao = _de_tai(tmp_path, _sap(alpha="Alpha: 0.01 hai phía."))
    assert _ck(bao, "G6-AUTO-03")["pass"] is False and bao["status"] == "BLOCKED"


def test_tham_so_khuon_sinh_con_trong_la_draft(tmp_path):
    bao = _de_tai(tmp_path, _sap(), script=SCRIPT_THAT + "cluster_var <- '[CẦN TÊN BIẾN CỤM]'\n")
    c = _ck(bao, "G6-AUTO-07")
    assert c["pass"] is None and "TÊN BIẾN" in c["detail"].upper() and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


def test_bang_canh_bao_va_cu_phap_ma_khong_bi_g6_auto_07_bat(tmp_path):
    them = "# [CẦN CHÚ Ý — kiểm giả định trước khi diễn giải]\nx <- d[['col']]\n"
    bao = _de_tai(tmp_path, _sap(), script=SCRIPT_THAT + them)
    assert _ck(bao, "G6-AUTO-07")["pass"] is True and bao["status"] == "READY_FOR_STATISTICIAN_REVIEW"


def test_bien_thoi_gian_du_phong_chi_bat_khi_phan_tich_chinh_la_cox(tmp_path):
    them = "# Không tự phát hiện time — dùng follow_time\n"
    assert _ck(_de_tai(tmp_path / "a", _sap(), script=SCRIPT_THAT + them), "G6-AUTO-07")["pass"] is True
    cox = "**Phân tích chính:** Cox proportional hazards\n"
    assert _ck(_de_tai(tmp_path / "b", _sap(), script=SCRIPT_THAT + them, a7=cox), "G6-AUTO-07")["pass"] is None


def test_alpha_12_khong_ghi_khong_muon_so_cua_hop_khoa(tmp_path):
    """§12 không ghi alpha (không nhãn) — phạm vi §12 cũ kéo tới hết tệp đọc «alpha 0.05» của hộp khoá ⇒ PASS sai."""
    bao = _de_tai(tmp_path, _sap(alpha="Ngưỡng ý nghĩa: chưa ghi."))
    assert _ck(bao, "G6-AUTO-03")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"
