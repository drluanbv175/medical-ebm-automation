"""Vị từ trường và nơi tiêu thụ nối hợp đồng ô trống chung `tools/placeholder_contract.py` (03–04/10/2026).

Mỗi vị từ chỉ được CHẶT hơn: marker cũ vẫn bắt, ô mẫu khuôn sinh (đo 03/10: «[TO BE COMPLETED]», «___», «[đơn vị]»,
«[nơi thực hiện]»…) không còn được coi là giá trị thật, còn giá trị hợp lệ (số 0, phép so sánh «< 3 ngày», mã IRB thật,
«[Cancer …]») không bị báo nhầm. Ngoại tuyến; chỉ ĐỌC dữ liệu C1a đã vào git.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import annex2_quality_gate as A2X  # noqa: E402
import audit_research_gates as ARG  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as KCT  # noqa: E402
import md2docx_vn as MD  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g8_auto as G8A  # noqa: E402
import skill_standards as S  # noqa: E402

C1A = ROOT / "exports" / "hai-long-benh-nhan-C1a-BVQY175"

O_MAU = ["[TO BE COMPLETED]", "___", "[đơn vị]", "[nơi thực hiện]", "thuốc/can thiệp X", "<CẦN ĐIỀN>",
         "[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]", "CHƯA XÁC NHẬN", "……"]


# ── research_study_spec.is_present (StudySpec + run_g10_assemble._text) ────────────────────────────────────────────
@pytest.mark.parametrize("v", O_MAU + ["[Cần bổ sung]", "-", "?"])
def test_studyspec_khong_coi_o_mau_la_gia_tri(v):
    assert RS.is_present(v) is False, v


@pytest.mark.parametrize("v", ["[CẦN BỔ SUNG]", "[DỰ THẢO] x", "tbd", "TODO", "", None])
def test_studyspec_giu_marker_cu(v):
    assert RS.is_present(v) is False


@pytest.mark.parametrize("v", [0, 0.0, "Bệnh nhân nằm viện < 3 ngày hoặc tuổi > 80", "Khoa Nội — BVQY175",
                               "[Cancer cohort] người lớn", True])
def test_studyspec_khong_bao_nham(v):
    assert RS.is_present(v) is True, v


def test_studyspec_dict_list_giu_any():
    assert RS.is_present({"a": "___", "b": "Khoa Nội"}) is True
    assert RS.is_present({"a": "___", "b": "[TO BE COMPLETED]"}) is False


# ── skill_standards._is_real_value (tín hiệu đời thực: irb_approved, sap_locked…) ─────────────────────────────────
@pytest.mark.parametrize("v", O_MAU + ["[CẦN BỔ SUNG]", "TBD", "[TÁC GIẢ ĐIỀN: số]", "-", "?"])
def test_skill_standards_tin_hieu_khong_bat_sai(v):
    assert S._is_real_value(v) is False, v


@pytest.mark.parametrize("v", ["IRB-2026-015", "175/QĐ-HĐĐĐ ngày 12/10/2026", "2026-10-12"])
def test_skill_standards_gia_tri_that(v):
    assert S._is_real_value(v) is True


# ── audit_research_gates._present_value ───────────────────────────────────────────────────────────────────────────
def test_audit_present_value():
    assert ARG._present_value(["Tử vong", "[CẦN BỔ SUNG]"]) is False
    assert ARG._present_value(["Tử vong", "Nhập viện"]) is True
    assert ARG._present_value({"x": "[đơn vị]"}) is False
    assert ARG._present_value("[REQUIRE_HUMAN_INPUT]") is False
    assert ARG._present_value("Bệnh viện Quân y 175") is True
    assert ARG._present_value(0) is True and ARG._present_value(False) is False


# ── annex2_quality_gate._present (dùng chung G1/G2) ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("v", ["[cần PI ấn định]", "[DỰ THẢO — chờ]", "___", "[TO BE COMPLETED]", "CHƯA XÁC NHẬN",
                               ["[CẦN]"], {"x": "[CẦN]"}, ["ok", "___"], "[CẦN BỔ SUNG]", "[DỰ THẢO]", ""])
def test_annex2_present_chat_hon(v):
    assert A2X._present(v) is False, v


@pytest.mark.parametrize("v", ["Tiêu chí loại trừ: bệnh nhân cấp cứu", ["Tiêu chí A", "Tiêu chí B"],
                               {"k": "v thật"}, 3])
def test_annex2_present_gia_tri_that(v):
    assert A2X._present(v) is True


# ── kiem_chi_tiet_he_nghien_cuu: con số 🟡 trục ③ không bao giờ nhỏ hơn bản cũ ───────────────────────────────────────
def test_dem_o_chua_dien_khong_nho_hon_ban_cu():
    vb = ("A [CẦN BỔ SUNG]\nB [CẦN X] và [CẦN Y]\nInstitution: [TO BE COMPLETED]\n"
          "[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]\n___")
    cu = len(KCT.SO_TAG_CAN.findall(vb))
    moi = KCT.dem_tag_can(vb)
    assert cu == 3 and moi == 5, (cu, moi)          # +[TO BE COMPLETED] +[XÁC NHẬN THỦ CÔNG…]; «___» không cộng
    assert KCT.dem_o_theo_ho(vb)["trong"] == 1


@pytest.mark.skipif(not C1A.is_dir(), reason="thư mục C1a không có trong checkout này")
def test_dem_o_chua_dien_tren_c1a_that_khong_nho_hon():
    for f in sorted(C1A.glob("*.md")):
        vb = f.read_text(encoding="utf-8")
        assert KCT.dem_tag_can(vb) >= len(KCT.SO_TAG_CAN.findall(vb)), f.name


# ── study_readiness: chuỗi mà tools/tu_de_xuat_viec.py của repo gốc PHÂN TÍCH phải còn nguyên ────────────────────────
def test_study_readiness_giu_chuoi_repo_goc_doc():
    nguon = (ROOT / "tools" / "study_readiness.py").read_text(encoding="utf-8")
    assert "CHƯA được bác sĩ chốt" in nguon and "0/4" in nguon


def test_study_readiness_dem_theo_ho(tmp_path):
    import study_readiness as SR
    (tmp_path / "a.md").write_text("Institution: [TO BE COMPLETED]\n| ___ | ___ |\nKhoa Nội\n",
                                   encoding="utf-8", newline="\n")
    blanks, dem = SR._collect_blanks(tmp_path)
    assert any("TO BE COMPLETED" in b for b in blanks)
    assert dem["nhan"] == 1 and dem["trong"] == 2


# ── md2docx_vn: tô cam ô chưa điền, KHÔNG tô «___» và «[Cancer…]» ─────────────────────────────────────────────────
def test_md2docx_to_o_chua_dien():
    assert MD._looks_like_flag("[TO BE COMPLETED]") is True
    assert MD._looks_like_flag("[đơn vị]") is True
    assert MD._looks_like_flag("[CẦN BỔ SUNG]") is True            # tiền tố cũ
    assert MD._looks_like_flag("[Cancer cohort]") is False
    assert MD._residue_spans("Nghiên cứu thuốc/can thiệp X có giúp") != []
    assert MD._residue_spans("| ___ | ký tên ___ |") == []


# ── run_g8_auto._item_auto_check: «[CAN]», «___», «[đơn vị]» trong mục I/II ⇒ ☐ ─────────────────────────────────────
GATES = {f"G{i}": {"_file_exists": True} for i in range(8)} | {"G2": {"_file_exists": True, "g2_irb_number": "IRB-1"}}


@pytest.mark.parametrize("o", ["[CAN]", "___", "[đơn vị]", "[TO BE COMPLETED]"])
def test_g8_muc_checklist_khong_tich_khi_con_o(o):
    vb = (f"## I. GIỚI THIỆU\n\nBối cảnh đầy đủ {o}.\n\n## II. PHƯƠNG PHÁP\n\nThiết kế đầy đủ.\n\n"
          "## III. KẾT QUẢ\n\n[CẦN KẾT QUẢ THẬT]\n")
    assert G8A._item_auto_check("Background/rationale", GATES, "rct", vb) == "☐"


def test_g8_muc_checklist_van_tich_khi_du():
    vb = ("## I. GIỚI THIỆU\n\nBối cảnh và mục tiêu đã viết đầy đủ.\n\n## II. PHƯƠNG PHÁP\n\nThiết kế đầy đủ.\n\n"
          "## III. KẾT QUẢ\n\n[CẦN KẾT QUẢ THẬT]\n")
    assert G8A._item_auto_check("Background/rationale", GATES, "rct", vb) == "☑"


# ── run_g10_assemble: trường khoá phạm vi là ô mẫu ⇒ có dòng «chưa được cung cấp/xác nhận» ──────────────────────────
def test_g10_assemble_khoa_pham_vi_bat_o_mau():
    import run_g10_assemble as G10A
    bang = G10A.build_missing_information({}, {"primary_outcome": "[nơi thực hiện]"})
    assert "Kết cục chính chưa được cung cấp/xác nhận" in bang
    bang_du = G10A.build_missing_information({}, {"primary_outcome": "Điểm hài lòng trung bình (thang 5 mức)"})
    assert "Kết cục chính chưa được cung cấp/xác nhận" not in bang_du
