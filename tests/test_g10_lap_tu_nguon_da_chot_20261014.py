"""Hồi quy 14/10/2026: đề cương G10 (gói ETHICS_SUBMISSION của C1a) in 22 ô «[CẦN…]» dù dữ kiện đã chốt ở G0/G1/G2/G4.

Bộ dựng chỉ đọc khoá cấp cao của study_meta. `bo_sung_tu_nguon_da_chot` lấp ô TRỐNG từ nguồn đã chốt (không ghi đè, mỗi
giá trị mang nhãn nguồn); `meta_for_render` bù khoá còn trống cho MỌI khối dict (trước chỉ khối resources).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import research_study_spec as RS  # noqa: E402
import run_g10_assemble as A  # noqa: E402

MA = "de-tai-thu"
SAP = """# SAP
### §2 KẾT CỤC
- **Kết cục chính:** hài lòng chung, Likert 1–5.
### §3 THỐNG KÊ MÔ TẢ
- Tỷ lệ theo lĩnh vực.
### §5 PHÂN TÍCH ĐA BIẾN
- **Exposure chính:** `thoigian_cho` (phút; mốc HIS).
### §7 PHÂN TÍCH NHÓM NHỎ
- Không có nhóm nhỏ tiền định.
### §8 ĐA SO SÁNH
- Không áp FDR cho bảng đơn biến.
| Bảng | không lấy |
### §9 PHÂN TÍCH ĐỘ NHẠY
- Mô hình nhị phân hoá.
### §10 PHẦN MỀM + SEED
- R ≥ 4.3.
### §11 DUMMY TABLES
"""


def _ghi(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8", newline="\n")


def _thu_muc(tmp_path: Path, muc_dich: str = "ETHICS_SUBMISSION") -> Path:
    _ghi(tmp_path / f"G4_A5_SAP_FINAL_{MA}.md", SAP)
    _ghi(tmp_path / f"G4_A5_SAP_FINAL_{MA}.md.bak-20261014-000000", "### §9 PHÂN TÍCH ĐỘ NHẠY\n- BẢN CŨ\n")
    _ghi(tmp_path / f"G2_A3_ETHICS_PACKAGE_{MA}.md",
         "☐ Tài liệu 3: Bảng rủi ro–lợi ích\n Thời gian lưu: 5 năm sau kết thúc nghiên cứu\n"
         "Chủ nhiệm đã rà và xác nhận bảng rủi ro theo đề cương (03/10/2026).\n")
    _ghi(tmp_path / A.G10Q.READINESS_JSON, json.dumps({"release": {"purpose": muc_dich, "owner_ref": "PI-THU"}}))
    return tmp_path


def _meta() -> dict:
    return {
        "gate_params": {
            "G0": {"hypothesis_h0": "Không liên quan: OR = 1.", "hypothesis_h1": "OR khác 1."},
            "G1": {"study_schema_timeline": "đăng ký công khai OSF Registries trước T0 → phê duyệt đạo đức"},
        },
        "primary_outcome": {"name": "G1 — hài lòng chung (biến SHLNB_Chung)", "measure": "Likert 5 mức",
                            "source": "Phiếu tự điền ẩn danh."},
        "instrument": {"name": "Bộ câu hỏi", "source": "Nhóm nghiên cứu phát triển và kiểm định trước thu thập chính"},
        "registration": {"registry": "ClinicalTrials.gov hoặc WHO ICTRP primary registry"},
        "ethics": {"consent": "ICF"},
    }


def test_muc_sap_gop_doan_bo_bang_va_vang():
    assert A._muc_sap(SAP, 8) == "Không áp FDR cho bảng đơn biến."
    assert A._muc_sap(SAP, 2) == "**Kết cục chính:** hài lòng chung, Likert 1–5."
    assert A._muc_sap(SAP, 11) is None and A._muc_sap(SAP, 13) is None


def test_lap_tu_nguon_da_chot(tmp_path):
    meta = _meta()
    da = A.bo_sung_tu_nguon_da_chot(meta, {"G2": {"risk_level": "TỐI THIỂU"}}, _thu_muc(tmp_path))
    assert meta["hypothesis"] == "H0: Không liên quan: OR = 1. H1: OR khác 1. (G0 — PI đã chốt)"
    assert meta["primary_outcome"]["definition"] == "Likert 5 mức"
    assert meta["primary_outcome"]["variable_name"] == "SHLNB_Chung"
    assert meta["analysis"]["sensitivity"] == "Mô hình nhị phân hoá. (SAP §9)"  # bản .bak bị bỏ qua
    assert meta["analysis"]["software"] == "R ≥ 4.3. (SAP §10)"
    assert meta["effect_modifiers"] == "Không có nhóm nhỏ tiền định. (SAP §7)"
    assert "Phơi nhiễm: `thoigian_cho` (phút; mốc HIS) (SAP §5)" in meta["data_source"]
    assert meta["data_governance"]["retention"] == "5 năm sau kết thúc nghiên cứu (PI nhập ở hồ sơ G2)"
    assert meta["ethics"]["safety"].startswith("Nguy cơ tối thiểu; ") and meta["ethics"]["consent"] == "ICF"
    assert meta["registration"]["registry"] == "OSF Registries"  # quyết định G1 thắng gợi ý chung của G2
    assert "OSF Registries trước T0" in meta["registration"]["plan"]
    assert meta["prepared_by"] == "PI-THU (khối phát hành G10)"
    assert meta["instrument"]["note"].startswith("Trạng thái kiểm định: chưa có chỉ số")
    assert "expected_results.flow_diagram" in da and "hypothesis" in da


def test_khong_ghi_de_gia_tri_da_co(tmp_path):
    meta = _meta()
    meta["hypothesis"] = "Giả thuyết PI tự viết"
    meta["analysis"] = {"software": "Stata 18"}
    meta["registration"] = {"registry": "OSF Registries — mã osf.io/abcd"}
    da = A.bo_sung_tu_nguon_da_chot(meta, {}, _thu_muc(tmp_path))
    assert meta["hypothesis"] == "Giả thuyết PI tự viết" and "hypothesis" not in da
    assert meta["analysis"]["software"] == "Stata 18"
    assert meta["registration"]["registry"] == "OSF Registries — mã osf.io/abcd"


def test_khong_ghi_trang_thai_kiem_dinh_khi_khong_phai_goi_truoc_du_lieu(tmp_path):
    meta = _meta()
    A.bo_sung_tu_nguon_da_chot(meta, {}, _thu_muc(tmp_path, "JOURNAL_SUBMISSION"))
    assert "note" not in meta["instrument"]


def test_meta_for_render_bu_khoa_moi_khoi_dict():
    spec = {"ethics": {"benefit_risk": "Lợi ích vượt nguy cơ tối thiểu", "consent": "từ spec"},
            "analysis": {"primary_method": "từ spec", "missing_data": "MICE"}}
    out = RS.meta_for_render({"ethics": {"consent": "ICF thô"}, "analysis": {"primary_method": "thô"}}, spec)
    assert out["ethics"] == {"consent": "ICF thô", "benefit_risk": "Lợi ích vượt nguy cơ tối thiểu"}
    assert out["analysis"] == {"primary_method": "thô", "missing_data": "MICE"}
