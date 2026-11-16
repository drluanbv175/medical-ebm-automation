"""Cổng sau KHÔNG hỏi lại điều đã chốt ở cổng trước (bác sĩ 16/11/2026, «Hãy hoàn thiện vấn đề giả lập»).

Giả lập trọn vòng đề tài thuần tập đo được: G10 bắt PI khai lại 21 khoá đã chốt (SAP §4/§6/§11, G2, G5, G7, ma trận),
G7 để trống 14 ô có sẵn ở G1/SAP và ~40 dòng khung phải xoá tay, G9 hỏi lặp 53 ô (cover letter chép hai nơi, COI/tài
trợ/chia sẻ dữ liệu/AI đã khai ở G7–G8). Test này khoá: (1) `quyet_dinh_da_chot.lop_phu` lấp đúng khoá TRỐNG, không đè
khoá PI, không chép ô trống; (2) `run_g10_assemble.load_meta` áp lớp phủ (bộ lắp và cổng G10 cùng dùng); (3) G7 lấp ô từ
quyết định đã chốt + công cụ gỡ khung; (4) G9 lấy COI/tài trợ/N/kết quả… và A10 không chép lại cover letter.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import go_khung_ban_thao_g7 as GK  # noqa: E402
import quyet_dinh_da_chot as QD  # noqa: E402

STUDY = "ZZ-QDDC"
SAP = """# SAP

### §2 KẾT CỤC

- **Kết cục chính:** Gãy xương mọi vị trí trong thời gian theo dõi; đo bằng phim X-quang
- **Kết cục phụ 1:** Gãy cổ xương đùi trong 3 năm

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** Hồi quy Poisson với sai số chuẩn robust → RR

### §6 DỮ LIỆU THIẾU

- **Chiến lược:** Multiple Imputation (MI, m=20)

### §7 PHÂN TÍCH NHÓM NHỎ

- **Nhóm nhỏ tiền định:** Giới (nam/nữ)

### §9 PHÂN TÍCH ĐỘ NHẠY

- Complete case vs MI

### §10 PHẦN MỀM + SEED

- **Phần mềm:** R 4.6

### §11 DUMMY TABLES

**Bảng 1, Đặc điểm nền:**
| Biến | A |
|---|---|

### §12 ALPHA
"""
MA_TRAN = [
    {"vai_tro": "ket_cuc_chinh", "bien": "gay_xuong", "khai_niem": "Gãy xương 3 năm",
     "cong_cu": "Hồ sơ + phim X-quang"},
    {"vai_tro": "phoi_nhiem", "bien": "ppi", "khai_niem": "Dùng PPI kéo dài", "cong_cu": "Đơn thuốc cấp phát"},
    {"vai_tro": "hiep_bien", "bien": "tuoi", "khai_niem": "Tuổi", "cong_cu": "Hồ sơ"},
]


def _de_tai(tmp_path: Path, meta_them: dict | None = None) -> Path:
    out = tmp_path / STUDY
    out.mkdir()
    meta = {"title": "PPI và gãy xương (thử)", "gate_params": {
        "G1": {"objectives": ["So sánh nguy cơ gãy xương giữa nhóm dùng và không dùng PPI"],
               "setting": "Phòng khám ngoại trú", "study_period": "2023–2025",
               "inclusion_criteria": ["Tuổi ≥60"], "exclusion_criteria": ["Ung thư di căn xương"],
               "secondary_outcomes": ["Gãy cổ xương đùi"],
               "primary_outcome": {"name": "Gãy xương mọi vị trí", "measure": "Phim X-quang xác nhận",
                                   "timepoint": "3 năm"}},
        "G0": {"hypothesis_h1": "PPI kéo dài làm tăng nguy cơ gãy xương"},
        "G2": {"protocol_version": "1.0", "icf_waiver_requested": True, "registration_required": False},
        "G7": {"authors": "Tác giả A · Tác giả B", "coi_declared": "Không có xung đột lợi ích",
               "funding_declared": "Không có tài trợ", "data_sharing_statement": "Không chia sẻ — dữ liệu hồ sơ"},
        "G8": {"ai_use_declared": True, "ai_tools": "Công cụ X", "ai_purpose": "soạn nháp", "ipd_sharing": False}}}
    meta.update(meta_them or {})
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (out / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(SAP, encoding="utf-8", newline="\n")
    (out / "G2_checkpoint.json").write_text(json.dumps({"risk_level": "TỐI THIỂU", "g2_irb_number": "IRB-01"}),
                                            encoding="utf-8", newline="\n")
    (out / "DATA_LOCK_manifest.json").write_text(json.dumps({"status": "LOCKED_FOR_ANALYSIS", "row_count": 4396}),
                                                 encoding="utf-8", newline="\n")
    (out / "G5_OPERATIONAL_READINESS.json").write_text(json.dumps({
        "retention_plan": {"retention_rule": "2 năm"}, "access_control_review": {"least_privilege_confirmed": True},
        "backup_restore_test": {"restore_verified": True},
        "source_data_verification": {"method": "Nhập kép 100% phiếu"}}, ensure_ascii=False),
        encoding="utf-8", newline="\n")
    (out / "approval_ledger.json").write_text(json.dumps([{"gate_id": "G2", "decision": "APPROVED",
                                                           "timestamp_utc": "2026-11-15T10:00:00+00:00"}]),
                                              encoding="utf-8", newline="\n")
    return out


@pytest.fixture
def ma_tran(monkeypatch):
    monkeypatch.setattr(QD, "ma_tran", lambda *_a, **_k: [dict(r) for r in MA_TRAN])


# ── (1) lớp phủ quyết định đã chốt ────────────────────────────────────────────────────────────────────────────────
def test_lop_phu_lap_khoa_trong_tu_sap_g2_g5_g7_ma_tran(tmp_path, ma_tran):
    out = _de_tai(tmp_path)
    moi, ng = QD.lop_phu(json.loads((out / "study_meta.json").read_text()), out, STUDY)
    for khoa in ("primary_outcome", "exposure", "confounders", "data_source", "instrument", "primary_analysis",
                 "missing_data_analysis", "table_shells", "expected_results", "aim", "protocol_version",
                 "version_date", "consent_plan", "registration_plan", "risk_benefit", "data_collection_procedure",
                 "quality_control", "deidentification_plan", "data_governance", "privacy_plan", "authors"):
        assert khoa in ng, f"không lấp {khoa}"
    assert moi["primary_outcome"]["source"] == "Hồ sơ + phim X-quang"
    assert moi["primary_outcome"]["variable_name"] == "gay_xuong"
    assert "Poisson" in moi["primary_analysis"] and "SAP §4" in moi["primary_analysis"]
    assert moi["table_shells"] == ["Bảng 1, Đặc điểm nền"]
    assert moi["version_date"] == "2026-11-15"
    assert moi["data_governance"]["retention"] == "2 năm"
    assert "miễn phiếu đồng ý" in moi["consent_plan"]
    assert QD.KHOA_NGUON in moi


def test_lop_phu_khong_de_khoa_pi_va_bo_sung_khoi_thieu_truong(tmp_path, ma_tran):
    out = _de_tai(tmp_path, {"primary_analysis": "PI tự viết", "data_governance": {"retention": "5 năm"}})
    moi, ng = QD.lop_phu(json.loads((out / "study_meta.json").read_text()), out, STUDY)
    assert moi["primary_analysis"] == "PI tự viết" and "primary_analysis" not in ng
    assert moi["data_governance"]["retention"] == "5 năm"  # khoá PI giữ nguyên
    assert "access" in moi["data_governance"]  # chỉ bổ sung trường trống


def test_lop_phu_khong_chep_o_trong_cua_sap(tmp_path, ma_tran):
    out = _de_tai(tmp_path)
    p = out / f"G4_A5_SAP_FINAL_{STUDY}.md"
    p.write_text(p.read_text().replace("Hồi quy Poisson với sai số chuẩn robust → RR", "[CẦN THỐNG KÊ VIÊN]"),
                 encoding="utf-8", newline="\n")
    _moi, ng = QD.lop_phu(json.loads((out / "study_meta.json").read_text()), out, STUDY)
    assert "primary_analysis" not in ng


def test_cong_cu_thang_do_khong_bi_dien_thay(tmp_path, monkeypatch):
    rows = [dict(r) for r in MA_TRAN]
    rows[0]["cong_cu"] = "Bộ câu hỏi hài lòng (thang 5 mức)"
    monkeypatch.setattr(QD, "ma_tran", lambda *_a, **_k: rows)
    out = _de_tai(tmp_path)
    _moi, ng = QD.lop_phu(json.loads((out / "study_meta.json").read_text()), out, STUDY)
    assert "instrument" not in ng  # PROM/thang đo ⇒ PI khai công cụ ĐÃ KIỂM ĐỊNH
    assert "data_source" in ng


# ── (2) G10 dùng lớp phủ ở load_meta ──────────────────────────────────────────────────────────────────────────────
def test_load_meta_g10_ap_lop_phu(tmp_path, ma_tran):
    import run_g10_assemble as G10A

    out = _de_tai(tmp_path)
    assert G10A.load_meta(out).get("primary_analysis")
    assert "primary_analysis" not in G10A.load_meta(out, lop_phu=False)


# ── (3) G7 ────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g7_lap_o_tu_quyet_dinh_da_chot(tmp_path, ma_tran):
    import run_g7_auto as G7A

    out = _de_tai(tmp_path)
    van = ("**Objective:** [CẦN — câu hỏi PICO chính một câu]  \n"
           "*Tiêu chí loại:* [CẦN]  \n"
           "*Cơ sở nghiên cứu:* [CẦN — tên bệnh viện/phòng khám, tuyến, địa bàn]  \n"
           "Phần mềm: [CẦN — R/Stata/SPSS phiên bản]. \n"
           "Phương pháp chính: [CẦN — từ SAP §4; theo effect_type=RR gợi ý: Poisson]. \n"
           "**Registration:** [CẦN SỐ ĐĂNG KÝ CLINICALTRIALS.GOV/PROSPERO]  \n"
           "Chúng tôi giả thuyết rằng [CẦN nêu chiều hướng kỳ vọng của mối liên quan/hiệu quả].  \n"
           "**Results:** [CẦN KẾT QUẢ THẬT — không điền trước khi phân tích xong]\n")
    moi, da = G7A.lap_o_da_chot_g7(van, out, STUDY)
    assert "So sánh nguy cơ gãy xương" in moi and "Ung thư di căn xương" in moi and "Phòng khám ngoại trú" in moi
    assert "R 4.6" in moi and "Hồi quy Poisson" in moi and "Không đăng ký" in moi and "PPI kéo dài làm tăng" in moi
    assert "[CẦN KẾT QUẢ THẬT" in moi  # kết quả KHÔNG phải điều đã chốt — giữ nguyên
    assert {"muc_tieu", "tieu_chi_loai_pp", "co_so_pp", "phan_mem", "phuong_phap_chinh", "dang_ky",
            "gia_thuyet"} <= set(da)


def test_g7_khong_co_quyet_dinh_thi_giu_o(tmp_path, ma_tran):
    import run_g7_auto as G7A

    out = _de_tai(tmp_path)
    meta = json.loads((out / "study_meta.json").read_text())
    meta["gate_params"]["G1"].pop("setting")
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    moi, _ = G7A.lap_o_da_chot_g7("*Cơ sở nghiên cứu:* [CẦN — tên bệnh viện/phòng khám, tuyến, địa bàn]", out, STUDY)
    assert "[CẦN — tên bệnh viện" in moi


def test_go_khung_ban_thao_g7_chi_go_khung():
    nhap = ("# A8 — BẢN THẢO IMRAD SKELETON (DRAFT — CHỜ KẾT QUẢ THẬT)\n\n> ⚠️ **DRAFT — BẢN NHÁP TỰ ĐỘNG:**  \n"
            "> • hướng dẫn\n\n## TIÊU ĐỀ  *(ước tính: 0 từ — điền thủ công)*\n\nPPI và gãy xương\n\n"
            "## BẢNG ƯỚC TÍNH SỐ TỪ THEO PHẦN\n\n| Phần | Từ |\n|---|---|\n\n## III. KẾT QUẢ\n\n"
            "*(Xem file Table2.docx — từ G6)*\nRR 1,33 (KTC 95% 1,11–1,60)\nTiêu chí: [CẦN BỔ SUNG]\n\n"
            "*[BẢN NHÁP TỰ ĐỘNG — DRAFT G7] Cần bác sĩ kiểm chứng.*\n")
    moi, bo = GK.go_khung(nhap, "PPI và gãy xương ở người cao tuổi")
    assert moi.startswith("# PPI và gãy xương ở người cao tuổi")
    assert ">" not in moi and "ước tính" not in moi and "BẢNG ƯỚC TÍNH" not in moi and "DRAFT" not in moi
    assert "RR 1,33 (KTC 95% 1,11–1,60)" in moi and "[CẦN BỔ SUNG]" in moi  # nội dung + ô còn thiếu giữ nguyên
    assert bo >= 8


# ── (4) G9 ────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g9_cover_letter_va_a10_lay_dieu_da_chot(tmp_path, ma_tran):
    import run_g9_auto as G9A

    out = _de_tai(tmp_path)
    (out / f"G7_A8_MANUSCRIPT_{STUDY}.md").write_text(
        "**Results:** RR hiệu chỉnh 1,33 (KTC 95% 1,11–1,60).\n\n**Bảng 1.** x\n\nPMID: 26462494\n",
        encoding="utf-8", newline="\n")
    (out / "G9_PUBLICATION_READINESS.json").write_text(json.dumps({
        "authors": [{"author_ref": "AUTHOR-01", "credit_roles": ["Conceptualization"]}],
        "data_access_governance": {"primary_data_access_author_ref": "AUTHOR-01", "sponsored_research": False},
        "data_availability": {"decision": "NOT_SHARED_WITH_JUSTIFICATION", "clinical_trial": False},
        "ai_disclosure": {"ai_used": True, "tools": ["Công cụ X"], "purposes": ["soạn nháp"]},
        "authorship": {"guarantor_author_ref": "AUTHOR-01"}}, ensure_ascii=False), encoding="utf-8", newline="\n")
    a10 = "\n".join([G9A.build_part1_icmje(1, STUDY), G9A.build_part2_coi(1, STUDY),
                     G9A.build_part3_data_availability({}, STUDY), G9A.build_part4_ai_disclosure({}, STUDY),
                     G9A.build_part6_pointer(STUDY)])
    thu = G9A.build_part6_cover_letter({}, STUDY, "Tạp chí thử")
    a10_moi, thu_moi, da = G9A.lap_o_da_chot_g9(a10, thu, out, STUDY)
    # A10: mã tác giả không hỏi lại, CRediT/người truy cập dữ liệu/COI/chia sẻ dữ liệu/AI lấy từ phiếu + G7/G8
    assert "Mã tác giả nội bộ (không PII): AUTHOR-01" in a10_moi
    assert "Conceptualization" in a10_moi and "[CẦN — AUTHOR-__]" not in a10_moi
    assert "Đã chọn Option A" in a10_moi and "Option B (Có COI" not in a10_moi
    assert "☑ Lựa chọn C" in a10_moi and "Lựa chọn A —" not in a10_moi and "Lựa chọn B —" not in a10_moi
    assert "AI used: ☐ No  ☑ Yes" in a10_moi and "Công cụ X" in a10_moi
    assert "COVER LETTER SHELL" not in a10_moi  # Phần 6 chỉ trỏ tệp riêng
    # cover letter
    for chuoi in ("PPI và gãy xương (thử)", "= 4396", "not required", "IRB-01", "RR hiệu chỉnh 1,33",
                  "Conflicts of interest: Không có xung đột lợi ích", "Funding: Không có tài trợ",
                  "Data availability: Không chia sẻ", "Yes — Công cụ X", "On behalf of all authors: Tác giả A"):
        assert chuoi in thu_moi, chuoi
    assert "SUGGESTED REVIEWERS" in thu_moi and "[CẦN — Tên | Institution" not in thu_moi  # mục tuỳ chọn
    assert len(da) >= 15


def test_check_de_cuong_dung_cung_lop_phu_voi_bo_lap(tmp_path, ma_tran):
    """Bộ kiểm đề cương (R15–R17) phải dựng StudySpec từ CÙNG lớp phủ bộ lắp/cổng G10 dùng — từng đọc study_meta thô
    nên giả lập trọn vòng thấy R16/R17 chặn D08/D11/D12/D13/D15/D18 mà bộ lắp đã lấp đúng."""
    import check_de_cuong as CDC
    import run_g10_assemble as G10A

    out = _de_tai(tmp_path)
    tho = json.loads((out / "study_meta.json").read_text())
    moi = CDC._meta_co_lop_phu(out, tho)
    assert moi.get("primary_analysis") and moi.get("table_shells")
    assert {k: moi.get(k) for k in QD.rut(out, STUDY, tho)} == {
        k: G10A.load_meta(out).get(k) for k in QD.rut(out, STUDY, tho)}


def test_g8_ket_cuc_sap_bo_chu_thich_dien_san_nhu_g7():
    """SAP điền sẵn §2 kèm chú thích soạn thảo; G7 chép kết cục vào bản nộp KHÔNG kèm chú thích ⇒ G8-AUTO-05 phải so
    phần kết cục (bỏ chú thích) — từng chặn nhầm «kết cục chính vắng trong bản thảo» ở cả 8 thiết kế."""
    import g8_quality_gate as G8Q

    sap = ("- **Kết cục chính:** Thay đổi điểm số Y; đo bằng Thang điểm Y; thời điểm: 12 tuần. Biến `kc` "
           "*(điền sẵn từ quyết định đã chốt — thống kê viên/PI sửa nếu cần)*  \n")
    chinh, _ = G8Q.ket_cuc_sap(sap)
    assert chinh and "điền sẵn" not in chinh[0]
    ban_thao = ("## II. PHƯƠNG PHÁP\n\nKết cục chính: Thay đổi điểm số Y; đo bằng Thang điểm Y; thời điểm: 12 tuần. "
                "Biến `kc`\n")
    trang_thai, _ = G8Q.primary_outcome_consistency(sap, ban_thao, chinh[0])
    assert trang_thai == "PASS"


def test_gia_lap_o_sau_khi_co_du_lieu_khong_phai_hoi_lai_g3():
    """Ô «tính đại diện quần thể… sau khi có dữ liệu thật» nằm trên dòng có chữ «cỡ mẫu» — là nội dung MỚI của tác giả,
    không phải câu hỏi lại G3.n (bộ giả lập từng điền nhầm «4396»)."""
    import gia_lap_tron_vong as GL

    dong = ("*(2)* Cỡ mẫu được tính TRƯỚC: N = 4396 — không phải cỡ mẫu tiện lợi. "
            "[CẦN bổ sung: tính đại diện quần thể nghiên cứu sau khi có dữ liệu thật]  \n")
    cps = {"G3": {"n": 4396, "confirmed_n": 4396}}
    o = GL.phan_loai_o(dong, "G7", "G7_A8_MANUSCRIPT_X.md", {}, cps, "cohort", [], {})
    assert o and all(x["loai"] != "hoi_lai_da_chot" for x in o)
