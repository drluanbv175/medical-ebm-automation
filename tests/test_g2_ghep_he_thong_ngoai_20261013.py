# -*- coding: utf-8 -*-
"""Kiểm máy cấp nhiệm vụ G2-T1: hồ sơ G2 phải nêu việc ghép dữ liệu từ hệ thống NGOÀI phiếu mà G1 đã chốt (13/10/2026).

Lộ khi diễn tập trọn đường PI trên C1a: G1 chốt ghép thời gian chờ từ HIS/eHospital (CNTT/QLCL giữ bảng ghép, huỷ trong
30 ngày) mà ICF Việt/Anh lẫn DMP không nhắc một lần; DMP §3 còn câu khuôn «bảng liên kết ID–tên do chủ nhiệm giữ».
Doctrine dao-duc-dang-ky 4b/4d có luật nhưng không phép kiểm nào bắt. Test chốt: có ghép ⇒ thiếu ở ICF Việt/ICF Anh/DMP
đều bị nêu; «ẩn danh hoàn toàn» khi có ghép bị nêu (4d); không có ghép ⇒ không kiểm; hồ sơ C1a thật sau khi sửa ⇒ sạch.
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402

STUDY = "GHEP-THU"
C1A = "hai-long-benh-nhan-C1a-BVQY175"

_HO_SO_CO_GHEP = """# A3
## TÀI LIỆU 4. PHIẾU ĐỒNG Ý
Thời gian chờ được lấy từ hệ thống quản lý bệnh viện (HIS) qua mã nghiên cứu; bảng đối chiếu huỷ trong 30 ngày.
## TÀI LIỆU 5. ICF TIẾNG ANH
Your waiting time will be taken from the hospital information system (HIS) via the study code.
## TÀI LIỆU 6. DMP
3. KHỬ ĐỊNH DANH: giả danh hóa có kiểm soát; ghép HIS do CNTT giữ bảng ghép, huỷ trong 30 ngày.
## TÀI LIỆU 7. CHECKLIST
"""


def _dung(tmp_path: Path, g1: dict, ho_so: str) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    (d / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": g1}}, ensure_ascii=False), encoding="utf-8",
                                       newline="\n")
    (d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text(ho_so, encoding="utf-8", newline="\n")
    return d


G1_CO_GHEP = {"intervention_dose_adherence": "thời gian chờ lấy từ hai mốc HIS/eHospital do CNTT trích"}


def test_da_dang_ky_cho_g2_t1():
    assert HD.KIEM_NHIEM_VU["G2-T1"][1] is HD._kiem_g2_ghep_ngoai


def test_co_ghep_ma_ho_so_khong_neu_thi_bao_ca_ba_tai_lieu(tmp_path):
    ho_so = _HO_SO_CO_GHEP.replace("(HIS)", "").replace("ghép HIS", "ghép").replace("hospital information system", "x")
    loi = HD._kiem_g2_ghep_ngoai(_dung(tmp_path, G1_CO_GHEP, ho_so), STUDY)
    assert len(loi) == 3, loi
    assert any("ICF tiếng Việt" in x for x in loi) and any("ICF tiếng Anh" in x for x in loi)
    assert any("DMP" in x for x in loi)


def test_co_ghep_va_ho_so_neu_du_thi_sach(tmp_path):
    assert HD._kiem_g2_ghep_ngoai(_dung(tmp_path, G1_CO_GHEP, _HO_SO_CO_GHEP), STUDY) == []


def test_chi_thieu_icf_tieng_viet_thi_chi_bao_icf_tieng_viet(tmp_path):
    ho_so = _HO_SO_CO_GHEP.replace("hệ thống quản lý bệnh viện (HIS)", "sổ khám")
    loi = HD._kiem_g2_ghep_ngoai(_dung(tmp_path, G1_CO_GHEP, ho_so), STUDY)
    assert len(loi) == 1 and "ICF tiếng Việt" in loi[0], loi


def test_an_danh_hoan_toan_khi_co_ghep_bi_neu(tmp_path):
    ho_so = _HO_SO_CO_GHEP.replace("giả danh hóa có kiểm soát", "ẩn danh hoàn toàn")
    loi = HD._kiem_g2_ghep_ngoai(_dung(tmp_path, G1_CO_GHEP, ho_so), STUDY)
    assert len(loi) == 1 and "4d" in loi[0], loi


def test_khong_co_ghep_thi_khong_kiem(tmp_path):
    g1 = {"intervention_dose_adherence": "thời gian chờ tự báo cáo trên phiếu"}
    ho_so = "## TÀI LIỆU 4. ICF\nẩn danh hoàn toàn\n## TÀI LIỆU 6. DMP\nphiếu giấy\n"
    assert HD._kiem_g2_ghep_ngoai(_dung(tmp_path, g1, ho_so), STUDY) == []


def test_chu_this_khong_bi_nhan_nham_la_his(tmp_path):
    g1 = {"ghi_chu": "THIS study uses paper forms only"}
    assert HD._kiem_g2_ghep_ngoai(_dung(tmp_path, g1, "## TÀI LIỆU 4. ICF\nx\n"), STUDY) == []


@pytest.mark.skipif(not (ROOT / "exports" / C1A / f"G2_A3_ETHICS_PACKAGE_{C1A}.md").is_file(),
                    reason="hồ sơ G2 của C1a không có trong checkout này")
def test_ho_so_c1a_that_neu_du_viec_ghep_his():
    assert HD._kiem_g2_ghep_ngoai(ROOT / "exports" / C1A, C1A) == []
