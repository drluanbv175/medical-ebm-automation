"""Đầu–cuối run_g2_auto (15/11/2026, chạy G2 cho BTM): giữ xác nhận G1, in đúng quy trình dữ liệu đã chốt.

Chạy thật `tools/run_g2_auto.py --skip-registry` trên đề tài giả (dữ liệu tổng hợp, không PII). Khoá đường nối trong
`main()` mà test hàm thuần không chạm tới.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_quality_gate as G1Q  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402


def _chay_g2(study: str, thiet_ke: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "tools" / "run_g2_auto.py"), "--study", study,
                           "--design", thiet_ke, "--skip-registry"],
                          cwd=ROOT, capture_output=True, text=True, timeout=240)


def test_g2_khong_chen_design_code_va_g1_giu_pass():
    study = "PYTEST-G2-KHONG-GIEO-DESIGN-20261115"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        dung_g0_g1_da_chot(d, study)
        # Tái hiện BTM: đề tài CHƯA ghim study_meta.design_code; PI chốt G1 với dấu tính khi chưa có khoá đó.
        truoc = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
        truoc.pop("design_code", None)
        design = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))["design"]
        truoc["gate_params"]["G1"]["dau_van_tay_chot"] = G1Q.dau_van_tay_g1(truoc, design)
        (d / "study_meta.json").write_text(json.dumps(truoc, ensure_ascii=False), encoding="utf-8", newline="\n")
        assert G1Q.evaluate_study(study, d)["status"] == G1Q.STATUS_CONFIRMED
        r = _chay_g2(study, "rct")
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
        sau = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
        assert "design_code" not in sau
        assert G1Q.evaluate_study(study, d)["status"] == G1Q.STATUS_CONFIRMED
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_g2_cat_ngang_hoi_cuu_in_quy_trinh_va_rui_ro_dung():
    study = "PYTEST-G2-QUY-TRINH-20261115"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional",
                           them_meta={"G1": {"data_collection_method": "Hồi cứu hồ sơ bệnh án điện tử eHospital"}})
        (d / "_quy-trinh-du-lieu.csv").write_text(
            "muc,gia_tri,nguon,neo_de_cuong,neo_g2,ghi_chu\n"
            "thu_thap,Trích hồ sơ theo quy tắc viết trước,SOP,,,\n"
            "an_danh,Phiếu chỉ mang mã nghiên cứu,SOP,,,\n"
            "nhap_lieu,Nhập REDCap,SOP,,,\n"
            "luu_tru,[CẦN PI QUYẾT — thời hạn lưu trữ],—,,,\n"
            "huy_du_lieu,[CẦN PI QUYẾT — cách hủy],—,,,\n", encoding="utf-8", newline="\n")
        r = _chay_g2(study, "cross_sectional")
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
        md = (d / f"G2_A3_ETHICS_PACKAGE_{study}.md").read_text(encoding="utf-8")
        assert "Quy trình dữ liệu đã chốt" in md and "Phiếu chỉ mang mã nghiên cứu" in md
        assert "dữ liệu trích hồ sơ" in md and "Rò rỉ thông tin từ bộ câu hỏi" not in md
        assert "Không cần (không có PII)" not in md and "Lưu trữ 5 năm sau công bố" not in md
    finally:
        shutil.rmtree(d, ignore_errors=True)
