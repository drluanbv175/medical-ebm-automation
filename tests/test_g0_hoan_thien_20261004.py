# -*- coding: utf-8 -*-
"""Hoàn thiện cổng G0 (soát từng cổng G0–G10, 04/10/2026) — mỗi test neo vào MỘT phát hiện đã được phản biện xác nhận.

G0-01 bộ chấm lưu dấu nội dung lúc chấm · G0-02 đếm đúng số đang tuyển (không bịa số 0) · G0-03 FINER phủ định / cờ
trơn không lý do ⇒ không PASS · G0-04/QĐ-17 PI tự tra ICTRP (+PROSPERO cho SR), đánh giá chồng lấn · G0-05 loại câu hỏi
chuẩn hoá dùng chung · G0-06 câu hỏi có hiệu ứng mà chỉ mô tả ⇒ cần lý do · G0-07 xác nhận gắn dấu vân tay + ngày không
ở tương lai · G0-08 chuẩn báo cáo dự kiến theo thiết kế đã ghim/loại câu hỏi · G0-09 PII trong gate_params.G0 ⇒ BLOCK.
Ngoại tuyến; số liệu định danh trong test là GIẢ.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g0_quality_gate as G0Q  # noqa: E402
import gate_contract as GC  # noqa: E402
from test_g0_quality_gate_20260728 import _artifact_text, _checkpoint, _confirmed_g0_meta  # noqa: E402


def _cham(g0=None, cp=None, registry=None, meta_them=None):
    cp = cp or _checkpoint()
    meta = {"gate_params": {"G0": g0 if g0 is not None else _confirmed_g0_meta()}}
    meta.update(meta_them or {})
    return G0Q.evaluate_g0_quality(checkpoint=cp, meta=meta, artifact_text=_artifact_text(),
                                   registry_check=registry if registry is not None else cp.get("registry_check"))


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


def _chot_lai(g0, cp=None):
    """Mô phỏng bác sĩ chốt lại: dấu vân tay tính trên ĐÚNG nội dung hiện tại."""
    g0 = copy.deepcopy(g0)
    g0["dau_van_tay_chot"] = G0Q.dau_van_tay_g0(cp or _checkpoint(), {"gate_params": {"G0": g0}})
    return g0


def test_duong_pass_van_dat_duoc():
    assert _cham()["status"] == G0Q.STATUS_CONFIRMED


# ── G0-02 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_02_bang_chung_dung_so_dang_tuyen_va_khong_bia_so_0():
    assert "16 đang tuyển" in _row(_cham(), "G0-AUTO-06")["evidence"]
    r = _cham(registry={"checked": True, "n_trials": 3, "n_active": None})
    assert "không rõ số đang tuyển" in _row(r, "G0-AUTO-06")["evidence"]
    r = _cham(registry={"checked": True, "n_trials": 3, "n_recruiting": 2})
    assert "2 đang tuyển" in _row(r, "G0-AUTO-06")["evidence"], "n_recruiting là bí danh cũ"


# ── G0-03 + bỏ sót bool trơn ───────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("gia_tri,ket_luan", [
    ("KHÔNG KHẢ THI vì thiếu nhân lực", "khong_dat"), ("Not feasible within budget", "khong_dat"),
    ("Không đạt — thiếu bệnh nhân", "khong_dat"), (False, "khong_dat"), (0, "khong_dat"),
    (True, "can_ly_do"), (1, "can_ly_do"), (None, "thieu"), ("[CẦN BÁC SĨ ĐIỀN]", "thieu"),
    ("Chưa có dữ liệu Việt Nam", "dat"), ("Đủ 320 BN/năm, có điều phối viên", "dat"),
])
def test_g0_03_ket_luan_finer(gia_tri, ket_luan):
    assert G0Q._finer_ket_luan(gia_tri) == ket_luan


def test_g0_03_finer_phu_dinh_hoac_tron_thi_khong_pass():
    for k, v, chu in (("finer_feasible", "Không khả thi trong 12 tháng", "KHÔNG ĐẠT"),
                      ("finer_ethical", True, "chưa có lý do")):
        g0 = _confirmed_g0_meta()
        g0[k] = v
        r = _cham(_chot_lai(g0))
        h5 = _row(r, "G0-HUMAN-05")
        assert h5["status"] == "REVIEW" and chu in h5["evidence"], h5
        assert r["status"] != G0Q.STATUS_CONFIRMED


# ── G0-04 / QĐ-17 ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_04_thieu_ngay_tra_ictrp_hoac_ngay_tuong_lai_thi_review():
    for tra in ({"ictrp": None}, {"ictrp": "2099-01-01"}, {"ictrp": "04/10/2026"}):
        g0 = _confirmed_g0_meta()
        g0["registry_manual_checked"] = tra
        h8 = _row(_cham(_chot_lai(g0)), "G0-HUMAN-08")
        assert h8["status"] == "REVIEW" and "ictrp" in h8["evidence"], (tra, h8)


def test_g0_04_tong_quan_he_thong_doi_ca_prospero():
    g0 = _confirmed_g0_meta()
    h8 = _row(_cham(_chot_lai(g0), meta_them={"design_code": "systematic_review"}), "G0-HUMAN-08")
    assert h8["status"] == "REVIEW" and "prospero" in h8["evidence"]
    g0["registry_manual_checked"] = {"ictrp": "2026-07-28", "prospero": "2026-07-28"}
    assert _row(_cham(_chot_lai(g0), meta_them={"design_code": "sr_ma"}), "G0-HUMAN-08")["status"] == "PASS"


def test_g0_04_co_thu_nghiem_dang_tuyen_phai_danh_gia_chong_lan():
    g0 = _confirmed_g0_meta()
    g0.pop("registry_overlap_assessment")
    h8 = _row(_cham(_chot_lai(g0)), "G0-HUMAN-08")
    assert h8["status"] == "REVIEW" and "registry_overlap_assessment" in h8["evidence"]
    r = _cham(_chot_lai(g0), registry={"checked": True, "n_trials": 2, "n_active": 0})
    assert _row(r, "G0-HUMAN-08")["status"] == "PASS", "0 đang tuyển ⇒ không đòi đánh giá chồng lấn"


def test_g0_04_khuon_gate_params_co_khoa_moi():
    sk = GC._GATE_PARAMS_SKELETON["G0"]
    for k in ("registry_manual_checked", "registry_overlap_assessment", "descriptive_justification",
              "dau_van_tay_chot"):
        assert k in sk, k


# ── G0-05 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("qt", ["therapy", "treatment", "Điều trị", "qualitative", "prediction_model", "harm",
                                "tác hại", "diagnosis", "descriptive"])
def test_g0_05_loai_cau_hoi_chuan_hoa(qt):
    g0 = _confirmed_g0_meta()
    g0["question_type"] = qt
    assert _row(_cham(_chot_lai(g0)), "G0-HUMAN-04")["status"] == "PASS", qt


def test_g0_05_sr_la_thiet_ke_khong_phai_loai_cau_hoi():
    g0 = _confirmed_g0_meta()
    g0["question_type"] = "sr"
    h4 = _row(_cham(_chot_lai(g0)), "G0-HUMAN-04")
    assert h4["status"] == "REVIEW" and "THIẾT KẾ" in h4["evidence"]


# ── G0-06 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_06_cau_hoi_hieu_ung_ma_chi_mo_ta_can_ly_do():
    g0 = _confirmed_g0_meta()
    g0["test_type"] = "descriptive"
    h3 = _row(_cham(_chot_lai(g0)), "G0-HUMAN-03")
    assert h3["status"] == "REVIEW" and "descriptive_justification" in h3["action"]
    g0["descriptive_justification"] = "Giai đoạn đầu chỉ ước lượng tỷ lệ dùng thuốc trước khi thiết kế thử nghiệm"
    assert _row(_cham(_chot_lai(g0)), "G0-HUMAN-03")["status"] == "PASS"
    g0 = _confirmed_g0_meta()
    g0.update({"test_type": "descriptive", "question_type": "descriptive"})
    assert _row(_cham(_chot_lai(g0)), "G0-HUMAN-03")["status"] == "PASS", "câu hỏi mô tả thuần không cần lý do thêm"


# ── G0-07 / CHUNG-C ────────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_07_doi_chu_de_hoac_pmid_sau_khi_chot_thi_xac_nhan_het_hieu_luc():
    g0 = _confirmed_g0_meta()
    for cp in (_checkpoint(topic="heart failure — đề tài KHÁC"),
               _checkpoint(pubmed_results={**_checkpoint()["pubmed_results"], "all_pmids": ["39999999"]})):
        h7 = _row(_cham(g0, cp=cp), "G0-HUMAN-07")
        assert h7["status"] == "REVIEW" and "đã đổi" in h7["evidence"], h7


def test_g0_07_sua_pico_sau_khi_chot_hoac_ngay_tuong_lai_hoac_kieu_cu():
    g0 = _confirmed_g0_meta()
    g0["population"] = "Bệnh nhân ≥18 tuổi suy tim EF GIẢM"
    assert _row(_cham(g0), "G0-HUMAN-07")["status"] == "REVIEW"
    g0 = _chot_lai({**_confirmed_g0_meta(), "reviewed_at": "2099-12-31T00:00:00"})
    assert _row(_cham(g0), "G0-HUMAN-07")["status"] == "REVIEW"
    g0 = _confirmed_g0_meta()
    g0.pop("dau_van_tay_chot")
    h7 = _row(_cham(g0), "G0-HUMAN-07")
    assert h7["status"] == "REVIEW" and "kiểu cũ" in h7["evidence"]
    assert G0Q.dau_van_tay_g0(_checkpoint(), {"gate_params": {"G0": g0}}) in h7["action"], \
        "hành động phải in dấu hiện tại để bác sĩ chép"


def test_g0_07_dau_khong_doi_khi_chi_doi_khoa_xac_nhan():
    g0 = _confirmed_g0_meta()
    dau = G0Q.dau_van_tay_g0(_checkpoint(), {"gate_params": {"G0": g0}})
    g0.update({"reviewed_at": "2026-07-29T10:00:00", "reviewed_by_role": "methodologist"})
    assert G0Q.dau_van_tay_g0(_checkpoint(), {"gate_params": {"G0": g0}}) == dau


# ── G0-08 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_08_chuan_bao_cao_theo_thiet_ke_ghim_va_loai_cau_hoi():
    goi_y = "RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu"
    mo_ta = G0Q.expected_reporting_standard(goi_y, {"gate_params": {"G0": {"question_type": "descriptive"}}})
    assert mo_ta["design_code"] == "cross_sectional" and "CONSORT" not in mo_ta["primary"]
    ghim = G0Q.expected_reporting_standard(goi_y, {"design_code": "RCT"})
    assert ghim["design_code"] == "rct" and "CONSORT" in ghim["primary"]
    mo_ho = G0Q.expected_reporting_standard(goi_y)
    assert mo_ho["design_code"] == "" and "[CẦN XÁC ĐỊNH Ở G1]" in mo_ho["primary"], "gợi ý «HOẶC» ⇒ không đoán"
    assert G0Q.expected_reporting_standard("RCT ngẫu nhiên có đối chứng")["design_code"] == "rct"


def test_g0_08_bao_cao_cham_dung_meta():
    r = _cham(meta_them={"design_code": "cross_sectional"})
    assert r["expected_reporting_standard"]["design_code"] == "cross_sectional"


# ── G0-09 / CHUNG-G ────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("khoa,gia_tri", [
    ("population", "Bệnh nhân suy tim, liên hệ 0912345678"),
    ("novelty_justification", "Theo hồ sơ CCCD 012345678901"),  # bimat-mien: số giả trong test
    ("population", "Ngày sinh: 03/11/1958, nam"),
    ("comparison", "Gửi kết quả về a.b@example.org"),
])
def test_g0_09_pii_trong_gate_params_thi_block_va_khong_in_gia_tri(khoa, gia_tri):
    g0 = _confirmed_g0_meta()
    g0[khoa] = gia_tri
    r = _cham(_chot_lai(g0))
    a7 = _row(r, "G0-AUTO-07")
    assert a7["status"] == "BLOCK" and khoa in a7["evidence"], a7
    assert gia_tri not in a7["evidence"] and r["status"] == G0Q.STATUS_BLOCKED


def test_g0_09_thoi_gian_nghien_cuu_khong_bi_coi_la_pii():
    g0 = _confirmed_g0_meta()
    g0["population"] = "Bệnh nhân ngoại trú khám từ 01/01/2026 đến 31/12/2026"
    assert _row(_cham(_chot_lai(g0)), "G0-AUTO-07")["status"] == "PASS"


# ── G0-01 phía bộ chấm ─────────────────────────────────────────────────────────────────────────────────────────────
def test_g0_01_checkpoint_luu_dau_noi_dung_luc_cham(tmp_path):
    d = tmp_path / "S"
    d.mkdir()
    cp = _checkpoint()
    (d / "G0_checkpoint.json").write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")
    meta = {"gate_params": {"G0": _confirmed_g0_meta()}}
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "G0_A1_PICO_FINER_S.md").write_text(_artifact_text(), encoding="utf-8", newline="\n")
    r = G0Q.evaluate_study("S", d, write=True)
    luu = json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))["quality_gate"]
    assert luu["dau_van_tay_luc_cham"] == r["dau_van_tay_hien_tai"] == G0Q.dau_van_tay_g0(cp, meta)


def test_g0_01_dong_thi_hanh_run_g0_auto_luu_dau():
    dong = [x.strip() for x in (ROOT / "tools" / "run_g0_auto.py").read_text(encoding="utf-8").splitlines()]
    assert '"dau_van_tay_luc_cham": quality.get("dau_van_tay_hien_tai"),' in dong
