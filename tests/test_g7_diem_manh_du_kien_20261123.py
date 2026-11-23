# -*- coding: utf-8 -*-
"""Bàn luận «Điểm mạnh» của bản thảo G7 dựng từ dữ kiện đã chốt; chốt máy ô chờ ở chỗ đã có dữ kiện (23/11/2026).

Đo trên giả lập: câu (2) «Điểm mạnh» mang ô «[CẦN bổ sung: tính đại diện quần thể…]» (13/13 kịch bản) và nhánh thiết kế
không tính cỡ mẫu theo lực (định tính, dự báo, tổng quan–gộp) chỉ có ô chờ dù G3 đã chốt N — ô rơi về «chưa có thông
tin» trong bản thảo. Nay:
  • `diem_manh_tu_du_kien_g7`: (2) cỡ mẫu G3, (3) biện pháp kiểm soát từng nguồn sai lệch đã chốt ở G1, (4) độ đầy đủ
    dữ liệu đo trên dữ liệu đã khoá (G6) + cách xử lý dữ liệu thiếu SAP đã khoá; thiếu dữ kiện mới để ô chờ;
  • `g7_quality_gate.o_cho_co_du_kien` + G7-AUTO-05: ô chờ ở chỗ bộ sinh đã có dữ kiện ⇒ CHẶN, kể cả khi người điền đã
    lấp ô (bộ sinh ghi ô của bản vừa sinh vào G7_checkpoint).

Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g7_quality_gate as G7Q  # noqa: E402
import run_g7_auto as G7  # noqa: E402

SAI_LECH = [
    {"sai_lech": "Nhiễu do chỉ định: người dùng thuốc A có nhiều bệnh kèm hơn",
     "bien_phap": "Hiệu chỉnh đa biến theo DAG; phân tích độ nhạy", "chieu": "cao hơn thực tế"},
    {"sai_lech": "Sai lệch thông tin do mã chẩn đoán", "bien_phap": "Kiểm 10% hồ sơ biến cố bằng phim X-quang."},
    {"sai_lech": "Sai lệch do chuyển nơi khám"},                                   # không khai biện pháp ⇒ không in
]
TT_THIEU = {"missing_data": {"n_complete_cases": 3448, "n_total": 4396, "pct_complete": 78.4}}
KHUNG = dict(n_adjusted=4396, formula_used="so sánh hai tỷ lệ", sample_size_detail="N = 4396, alpha = 0.05",
             effect_text="với RR = 1.33 (theo PMID: 26462494)", g3_n_chot=None, design_code="cohort")


def _ghi(p: Path, s: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")
    return p


def test_diem_manh_tu_du_kien_da_chot_khong_o_cho():
    dm = G7.diem_manh_tu_du_kien_g7(**KHUNG, bias_controls=SAI_LECH, tom_tat_g6=TT_THIEU,
                                    sap_tom_tat={"du_lieu_thieu": "Multiple Imputation (MI, m=20, method=pmm)"})
    assert dm[0] == ("*(2)* Cỡ mẫu được tính TRƯỚC (a priori) theo so sánh hai tỷ lệ: N = 4396, alpha = 0.05, với RR = "
                     "1.33 (theo PMID: 26462494) — không phải cỡ mẫu tiện lợi (convenience sample).  ")
    assert dm[1] == ("*(3)* Mỗi nguồn sai lệch tiềm ẩn xác định ở thiết kế có biện pháp kiểm soát định trước (G1, "
                     "xem §6b) — nhiễu do chỉ định: hiệu chỉnh đa biến theo DAG, phân tích độ nhạy; sai lệch thông tin "
                     "do mã chẩn đoán: kiểm 10% hồ sơ biến cố bằng phim X-quang.  ")
    assert dm[2] == ("*(4)* Độ đầy đủ dữ liệu đo trên tập dữ liệu phân tích: 3448/4396 người (78.4%) đủ dữ liệu "
                     "mọi biến phân tích (G6); dữ liệu thiếu xử lý theo SAP: Multiple Imputation (MI, m=20, "
                     f"method=pmm). {G7.NHAN_DOI_CHIEU_G6}  ")
    # câu (4) không thành khẳng định trần «đã khoá dữ liệu/SAP» khi cổng trước chưa có bằng chứng (G7-AUTO-06)
    assert G7Q.find_unsupported_claims("\n".join(dm), {}) == []
    assert not any("[CẦN" in x.replace(G7.NHAN_DOI_CHIEU_G6, "") for x in dm)
    assert "chuyển nơi khám" not in "\n".join(dm)


def test_thiet_ke_khong_tinh_theo_luc_dung_n_chot_o_g3():
    dm = G7.diem_manh_tu_du_kien_g7(**{**KHUNG, "n_adjusted": 0, "g3_n_chot": 900, "design_code": "prediction"},
                                    bias_controls=[], tom_tat_g6=None, sap_tom_tat={})
    assert dm[0] == ("*(2)* Cỡ mẫu chốt trước khi thu thập dữ liệu (G3): N = 900 người — cỡ mẫu phát triển mô hình "
                     "theo Riley 2020 (BMJ, PMID 32188600; pmsampsize).  ")
    # chưa chốt sổ sai lệch ⇒ ô chờ cho tác giả; chưa có số G6 ⇒ không in câu độ đầy đủ
    assert dm[1].startswith("*(3)* [CẦN — điểm mạnh khác") and len(dm) == 2


def test_thieu_du_kien_thi_o_cho_va_du_lieu_day_du_khong_in_cach_xu_ly():
    dm = G7.diem_manh_tu_du_kien_g7(**{**KHUNG, "n_adjusted": 0}, bias_controls=None,
                                    tom_tat_g6={"missing_data": {"n_complete_cases": 577, "n_total": 577,
                                                                 "pct_complete": 100.0}},
                                    sap_tom_tat={"du_lieu_thieu": "MI"})
    assert dm[0].startswith("*(2)* [CẦN thêm điểm mạnh")
    assert dm[2].startswith("*(4)* Độ đầy đủ dữ liệu đo trên tập dữ liệu phân tích: 577/577 người (100.0%)")
    assert "xử lý theo SAP" not in dm[2], "đủ dữ liệu ⇒ không nói xử lý dữ liệu thiếu"
    g6_loi = G7.diem_manh_tu_du_kien_g7(**KHUNG, bias_controls=[], tom_tat_g6={"missing_data": {"error": "x"}},
                                        sap_tom_tat={})
    assert len(g6_loi) == 2


def _de_tai(d: Path, *, g3: dict | None = None, g1_sai_lech: list | None = None) -> Path:
    _ghi(d / "G3_checkpoint.json", json.dumps(g3 if g3 is not None else {"n_adjusted": 4396}))
    _ghi(d / "study_meta.json", json.dumps({"gate_params": {"G1": {"bias_controls": g1_sai_lech or []}}},
                                           ensure_ascii=False))
    _ghi(d / "G4_A5_SAP_FINAL_X.md", "# SAP\n\n### §6 DỮ LIỆU THIẾU\n\n- **Chiến lược:** MI  \n\n"
                                     "### §9 PHÂN TÍCH ĐỘ NHẠY\n\n- Ca đầy đủ  \n\n"
                                     "### §10 PHẦN MỀM + SEED\n\n- **Phần mềm:** R 4.6  \n\n## PHẦN 4\n")
    return d


def test_chot_bat_o_cho_o_cho_da_co_du_kien(tmp_path):
    d = _de_tai(tmp_path, g1_sai_lech=SAI_LECH)
    ban = ("*(2)* [CẦN thêm điểm mạnh: cỡ mẫu…]  \n*(3)* [CẦN — điểm mạnh khác, vd…]  \n"
           "[CẦN — liệt kê nguồn sai lệch tiềm ẩn theo thiết kế]\n[CẦN CỠ MẪU TỪ G3 — …]\n"
           "Phần mềm: [CẦN — R]. Phân tích độ nhạy: [CẦN — từ SAP]. Dữ liệu thiếu: [CẦN — MI].")
    ten = [x.split(":")[0] for x in G7Q.o_cho_co_du_kien(d, "X", ban)]
    assert ten == ["Bàn luận §4 điểm mạnh (2) — cỡ mẫu đã chốt ở G3",
                   "Bàn luận §4 điểm mạnh (3) — biện pháp kiểm soát sai lệch đã chốt ở G1",
                   "Phương pháp §6b — sổ sai lệch đã chốt ở G1", "Phương pháp §5 — cỡ mẫu đã chốt ở G3",
                   "Phương pháp §6 — phần mềm SAP §10", "Phương pháp §6 — phân tích độ nhạy SAP §9",
                   "Phương pháp §6 — dữ liệu thiếu SAP §6"]
    # không có dữ kiện ⇒ ô chờ là phần của tác giả, không phải lỗi bộ sinh
    trong = tmp_path / "trong"
    _ghi(trong / "G3_checkpoint.json", "{}")
    assert G7Q.o_cho_co_du_kien(trong, "X", ban) == []
    # sổ sai lệch có mục nhưng không mục nào khai biện pháp ⇒ (3) vẫn là phần của tác giả
    d2 = _de_tai(tmp_path / "khong_bien_phap", g1_sai_lech=[{"sai_lech": "Nhiễu"}])
    assert not any("(3)" in x for x in G7Q.o_cho_co_du_kien(d2, "X", ban))


def _ban_thao_ma(text_dm: str) -> str:
    return "\n".join(["## III. KẾT QUẢ", "", "## IV. BÀN LUẬN", "", "**§4 Điểm mạnh (Strengths):**  ", text_dm, ""])


def test_g7_auto_05_chan_o_cho_co_du_kien_ke_ca_khi_da_bi_lap(tmp_path):
    base = dict(checkpoints={}, meta={})
    rep = G7Q.evaluate_g7_quality(manuscript_text=_ban_thao_ma("*(2)* chưa có thông tin"), **base,
                                  o_cho_du_kien=["Bàn luận §4 điểm mạnh (2) — cỡ mẫu đã chốt ở G3: «*(2)* [CẦN thêm"])
    row = next(r for r in rep["automatic_criteria"] if r["id"] == "G7-AUTO-05")
    assert row["status"] == "BLOCK" and "lỗi bộ sinh" in row["evidence"] and rep["status"] == G7Q.STATUS_BLOCKED
    rep2 = G7Q.evaluate_g7_quality(manuscript_text=_ban_thao_ma("*(2)* Cỡ mẫu N = 10."), **base, o_cho_du_kien=[])
    assert next(r for r in rep2["automatic_criteria"] if r["id"] == "G7-AUTO-05")["status"] == "PASS"


def test_evaluate_study_gop_o_cua_ban_vua_sinh_trong_checkpoint(tmp_path):
    """Người điền đã lấp ô (bản trên đĩa sạch) nhưng bộ sinh từng để ô ở chỗ có dữ kiện ⇒ vẫn CHẶN."""
    d = _de_tai(tmp_path / "exports" / "X", g1_sai_lech=SAI_LECH)
    _ghi(d / "G7_A8_MANUSCRIPT_X.md", _ban_thao_ma("*(2)* chưa có thông tin"))
    _ghi(d / "G7_checkpoint.json", json.dumps({"o_cho_co_du_kien_khi_sinh": [
        "Bàn luận §4 điểm mạnh (2) — cỡ mẫu đã chốt ở G3: «*(2)* [CẦN thêm điểm mạnh»"]}, ensure_ascii=False))
    rep = G7Q.evaluate_study("X", d, write=False, repo_root=tmp_path)
    row = next(r for r in rep["automatic_criteria"] if r["id"] == "G7-AUTO-05")
    assert row["status"] == "BLOCK" and "cỡ mẫu đã chốt ở G3" in row["evidence"]
    # bản trên đĩa còn ô và checkpoint sạch ⇒ vẫn bắt nhờ quét bản hiện tại
    _ghi(d / "G7_checkpoint.json", "{}")
    _ghi(d / "G7_A8_MANUSCRIPT_X.md", _ban_thao_ma("*(3)* [CẦN — điểm mạnh khác, vd]"))
    row = next(r for r in G7Q.evaluate_study("X", d, write=False, repo_root=tmp_path)["automatic_criteria"]
               if r["id"] == "G7-AUTO-05")
    assert row["status"] == "BLOCK" and "biện pháp kiểm soát sai lệch" in row["evidence"]


def test_bo_sinh_ghi_o_cua_ban_vua_sinh_vao_checkpoint(tmp_path):
    src = inspect.getsource(G7.main)
    assert "o_cho_co_du_kien_khi_sinh=G7Q.o_cho_co_du_kien(out_dir, study, artifact)," in src
    cp = G7.write_checkpoint(
        study="X", out_dir=tmp_path, run_date="2026-11-23", design_code="cohort", reporting_std="STROBE",
        target_journal=None, word_limit=3000, pmids_used=[], n_adjusted=10, guardrail_status="PASS",
        guardrail_errors=[], md_path=tmp_path / "a.md", docx_path=None, checklist_auto=0, checklist_total=0,
        o_cho_co_du_kien_khi_sinh=["x: «y»"])
    assert json.loads(cp.read_text(encoding="utf-8"))["o_cho_co_du_kien_khi_sinh"] == ["x: «y»"]


def test_ban_thao_dung_diem_manh_tu_du_kien(tmp_path, monkeypatch):
    """generate_manuscript dùng đúng hàm dựng Điểm mạnh — không còn ô «tính đại diện quần thể»."""
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    d = _de_tai(tmp_path, g1_sai_lech=SAI_LECH)
    kw = dict(study="X", topic="Chủ đề", n_sr=1, n_rct=1, n_guideline=0, research_gaps=["g"], pmids=["11111111"],
              pmid_meta={}, design_code="cohort", design_primary="Nghiên cứu Đoàn hệ (Cohort)", reporting_std="STROBE",
              irb_number="GL-1/2026", icf_version="1.0", registration="Không đăng ký", n_total=100, n_adjusted=110,
              alpha=0.05, power=0.8, effect_val=1.33, effect_type="RR", formula_used="so sánh hai tỷ lệ",
              g4_status="LOCKED", g4_lock_date="2026-11-01", target_journal="J", word_limit=3500,
              run_date="2026-11-23", bias_controls=SAI_LECH, sap_tom_tat=G7._sap_tom_tat(d, "X"))
    md = G7.generate_manuscript(**kw)
    dm = md.split("**§4 Điểm mạnh (Strengths):**", 1)[1].split("**§5 Hạn chế", 1)[0]
    assert "tính đại diện quần thể" not in dm and "[CẦN — điểm mạnh khác" not in dm
    assert "nhiễu do chỉ định: hiệu chỉnh đa biến theo DAG" in dm
    assert G7Q.o_cho_co_du_kien(d, "X", md) == []
