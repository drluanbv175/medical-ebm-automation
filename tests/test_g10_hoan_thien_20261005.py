# -*- coding: utf-8 -*-
"""Soát từng cổng G10 (05/10/2026) — kiểm hồi quy cho từng phát hiện, kèm hai chuỗi THẬT tới G10 khoá.

G10-01/03 Tiền đề CHẤM SỐNG (G0–G6 qua g7_quality_gate.tien_de_song — G2 = g2_da_duyet dùng chung; G7–G9 qua
      cong_song) thay cho trạng thái lưu của G0/G1/G3/G8; G8 phải PASS_G8_REVIEW_RECORDED sống (băm A9).
G10-02 Guardrail đề cương + StudySpec CHẤM LẠI trên tệp/dữ liệu hiện hành; .md/.docx phải đúng bản đã lắp (dấu
      SHA-256 ghi lúc lắp ráp).
G10-04 Manifest ràng buộc artifact hợp đồng của cổng tiền đề (gói đạo đức, SAP, bản thảo, bản nhận xét, artifact G5,
      script R/Python…).
G10-05 Biên nhận rút bài A12 còn hạn 30 ngày lúc PI ký (đã khoá thì chỉ cảnh báo).
G10-06/07 (đã vá ở đợt 0, kiểm lại trên chuỗi thật): kết cục chính diễn đạt khác nhau giữa các cổng ⇒ REVIEW cho tới khi
      chủ nhiệm xác nhận gắn dấu vân tay.
G10-08 §Đạo đức sinh theo thiết kế + quyết định/khai báo G2 (không còn «ICH-GCP · ICF · ẩn danh» cố định).
G10-09 Mục đích phát hành TRƯỚC dữ liệu (ETHICS_SUBMISSION/REGISTRY_UPDATE) chỉ đòi G0–G4 — kiểm trên chuỗi TRƯỚC IRB
      thật: G2 sinh bằng run_g2_auto, PI điền ô trước-nộp ⇒ READY_FOR_IRB_SUBMISSION (CHƯA duyệt), G4 SAP đủ nội dung
      CHƯA ký.
Lộ khi chạy chuỗi THẬT tới G10: nhãn [CẦN] VÔ ĐIỀU KIỆN của khuôn (đặt vấn đề, nguồn giả định G3, pháp lý, DMP, tài
      liệu tham khảo…), ghi chú rà của G3 sau khi thống kê viên đã chốt, repr dict trong ma trận truy xuất, meta phẳng
      không tới được khối dict của section builder, R4 của check_de_cuong không biết PMID đã qua A12 — đề cương đủ dữ
      kiện vẫn không bao giờ qua G10-AUTO-09.
Mọi luồng có ký chạy trong pytest với khoá giả tạm. Không PII (người ký/chủ nhiệm chỉ là mã tham chiếu).
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402
import check_de_cuong as CDC  # noqa: E402
import cong_song as CS  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import g9_quality_gate as G9Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import pipeline_freshness as FR  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g2_auto as G2A  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402
import skill_standards as S  # noqa: E402

from tests._chuoi_da_chot import dien_sap_g4, dung_g0_g3_da_chot, sinh_sap_g4_that, xac_nhan_g4  # noqa: E402
from tests.g5_test_helpers import append_signed_approval, configure_test_signing_key  # noqa: E402
from tests.test_g2_quality_gate import _meta as _meta_g2  # noqa: E402
from tests.test_g8_hoan_thien_20261004 import _ghi  # noqa: E402
from tests.test_g9_hoan_thien_20261005 import _METADATA_THU, _cham9, _de_tai_g9_that  # noqa: E402
from tests.test_g10_quality_gate import _complete_readiness  # noqa: E402
from tests.test_research_study_spec import _complete_meta  # noqa: E402

PMID_GOI = ("12345678", "30560792")  # PMID gốc của chuỗi + PMID nguồn giả định G3 mà đề cương G10 trích
# Đề cương G10 của RCT trích SPIRIT 2025 (tools/protocol_checklist_items.py: PMID 40294593, 40294956) — gói phát hành
# phải có A12 phủ cả hai, như PI chạy check_citations.py trên MỌI PMID của gói cuối.
PMID_SPIRIT_2025 = ("40294593", "40294956")
# Mục SPIRIT của RCT KHÔNG thuộc quyết định G1 — PI khai ở study_meta khi soạn đề cương (giá trị tổng hợp, không PII).
_SPIRIT_RCT_NGOAI_G1 = {
    "comparator_rationale": "Chăm sóc chuẩn là thực hành hiện hành tại đơn vị — so sánh trực tiếp lợi ích tăng thêm",
    "concomitant_care_policy": "Điều trị thường quy được phép; cấm tham gia chương trình can thiệp tương tự",
    "design_specific": {
        "randomization_type": "Ngẫu nhiên khối hoán vị, phân tầng theo cơ sở",
        "allocation_access": "Chỉ điều phối viên trung tâm không tham gia tuyển hay đánh giá",
        "unblinding_procedure": "Mở mù khi có biến cố bất lợi nghiêm trọng theo quy trình của hội đồng theo dõi",
        "ppi_plan": "Đại diện người bệnh góp ý tài liệu thông tin và kết cục quan trọng ở giai đoạn thiết kế",
    },
}


# Mục theo thiết kế KHÔNG thuộc quyết định G0/G1 — PI khai ở study_meta khi soạn đề cương (StudySpec X01/M01/S01/Q01/
# Q02; giá trị tổng hợp, không PII). Chỉ số index test của chẩn đoán đến từ G1 (intervention_or_exposure).
_DE_CUONG_THEO_THIET_KE = {
    "rct": _SPIRIT_RCT_NGOAI_G1,
    "diagnostic": {"design_specific": {
        "reference_standard": "Tiêu chuẩn tham chiếu của hội chuyên ngành, người đọc không biết kết quả test chỉ điểm",
        "threshold": "Ngưỡng dương tính định trước theo y văn; ngưỡng khác chỉ là phân tích thăm dò"}},
    "prediction": {"design_specific": {
        "validation": "Kiểm định nội bằng bootstrap 500 lần, hiệu chỉnh độ lạc quan",
        "calibration": "Độ dốc hiệu chuẩn, hiệu chuẩn tổng thể và đồ thị hiệu chuẩn",
        "discrimination": "Thống kê C kèm KTC 95%"}},
    "sr_ma": {"design_specific": {
        "eligibility": "Thử nghiệm ngẫu nhiên so sánh can thiệp X với chăm sóc chuẩn ở người trưởng thành",
        "risk_of_bias": "RoB 2 cho từng kết cục, hai người đánh giá độc lập"}},
    "qualitative": {"design_specific": {
        "reflexivity": "Nhật ký phản tư của người phỏng vấn; vai trò và quan hệ với người tham gia được khai",
        "audit_trail": "Lưu vết quyết định mã hoá và phiên bản codebook theo ngày",
        "qda_software": "Mã tay theo codebook trên bảng tính"}},
}
# PMID mà đề cương G10 của thiết kế trích do HỆ chèn (chuẩn đề cương / công thức cỡ mẫu G3) — gói phát hành phải có A12
# phủ, như PI chạy check_citations.py trên MỌI PMID của gói cuối.
_PMID_HE_THONG = {"rct": PMID_SPIRIT_2025, "sr_ma": ("25554246",), "diagnostic": ("7063747",)}
# Khoá mà G1 của chuỗi đã chốt — đề cương phải lấy từ G1, PI KHÔNG khai lại ở cấp cao (CHUNG-F).
_KHOA_G1_DA_CHOT = ("objectives", "population", "inclusion_criteria", "exclusion_criteria", "recruitment_plan",
                    "setting", "study_period")
THIET_KE_DAU_CUOI = ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "sr_ma",
                     "qualitative")


def _ck(bao: dict, ma: str) -> dict:
    return next(r for r in bao["automatic_criteria"] if r["id"] == ma)


def _chua_dat(bao: dict) -> list:
    return [(r["id"], r["evidence"][:300]) for r in bao["automatic_criteria"] if r["status"] != "PASS"]


def _lap_g10(goc: Path, study: str, monkeypatch) -> tuple[int, str]:
    monkeypatch.setattr(G10A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g10_assemble.py", "--study", study])
    CS.xoa_dem()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ma = G10A.main()
    CS.xoa_dem()
    return ma, buf.getvalue()


def _cham10(study: str, out: Path, goc: Path, *, write: bool = False) -> dict:
    CS.xoa_dem()
    return G10Q.evaluate_study(study, out, repo_root=goc, write=write)


def _ky_g10(study: str, out: Path, goc: Path) -> None:
    """PI tự ký đúng G10_checkpoint.json chứa manifest cuối (vai PI_PROJECT_OWNER, khoá giả tạm của pytest)."""
    append_signed_approval(study, out / G10Q.CHECKPOINT_JSON, "G10", "PI_PROJECT_OWNER", repo_root=goc)


def _ho_so_g2_that(out: Path, thiet_ke: str) -> None:
    """Chuỗi chung dựng G2 kiểu CŨ (checkpoint tối thiểu + gói đạo đức tổng hợp đã ký IRB). Bổ sung đúng các trường mà
    run_g2_auto (hồ sơ nguy cơ theo thiết kế, danh mục tài liệu) và g2_quality_gate (khi DUYỆT: số/ngày, phiên bản
    ICF) ghi THẬT — G10 §Đạo đức đọc chúng. Không đụng gói đạo đức đã ký."""
    cp_path = out / "G2_checkpoint.json"
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    nguy_co = G2A.get_risk_profile(thiet_ke)
    cp.update({
        "design_code": thiet_ke, "risk_level": nguy_co["risk_level"], "irb_route": nguy_co["irb_route"],
        "registration_required": nguy_co["registration"], "register_where": nguy_co["register_where"],
        "documents_generated": ["TL1 — Đơn xin phê duyệt IRB", "TL4 — ICF tiếng Việt (7 mục Helsinki)",
                                "TL6 — DMP (Luật 91/2025/QH15)"],
        "g2_irb_number": "IRB-REF-2026-01", "g2_approval_date": "2026-01-05", "g2_icf_version": "1.0",
    })
    _ghi(cp_path, json.dumps(cp, ensure_ascii=False, indent=2))
    if thiet_ke == "rct":
        # G2-03: RCT có kế hoạch an toàn riêng (5 mục) + PI xác nhận ở gate_params.G2.safety_plan_confirmed.
        _ghi(out / G2Q.ten_ke_hoach_an_toan(out.name), G2Q.khung_ke_hoach_an_toan(out.name).replace(
            "[CẦN — chủ nhiệm điền]", "Nội dung chủ nhiệm đã điền và rà."))
        meta_p = out / "study_meta.json"
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        meta["gate_params"].setdefault("G2", {})["safety_plan_confirmed"] = True
        _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))


def _noi_dung_de_cuong(out: Path, study: str, thiet_ke: str = "cohort") -> None:
    """Chủ nhiệm soạn nội dung đề cương (StudySpec D01–D18, trang bìa, công cụ, tài liệu tham khảo) vào study_meta —
    MỌI ô [CẦN] của đề cương thống nhất phải đến từ dữ kiện người khai hoặc hệ đã xác minh. Kết cục chính lấy đúng
    khối G1 đã chốt; các mô tả kết cục ở các cổng là CÙNG một kết cục ⇒ chủ nhiệm xác nhận bằng dấu vân tay CLI in
    ra."""
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    noi_dung = _complete_meta()
    noi_dung.pop("design_code", None)
    for khoa in _KHOA_G1_DA_CHOT:
        noi_dung.pop(khoa, None)
    kc1 = dict(meta["gate_params"]["G1"]["primary_outcome"])
    # Khối kết cục cấp cao là CẢ khối (bộ chấm G1 đọc nó trước gate_params.G1) — giữ tên/thời điểm G1, thêm định
    # nghĩa vận hành, nguồn đo, tên biến.
    noi_dung["primary_outcome"] = dict(kc1, definition="Thay đổi điểm thang Y từ ban đầu đến tuần 12",
                                       source="Thang điểm Y đã thẩm định", variable_name="primary_outcome")
    noi_dung["analysis"] = dict(noi_dung["analysis"], primary_outcome=kc1["name"])
    noi_dung["instrument"] = dict(noi_dung["instrument"], note="Công cụ đã thẩm định, giấy phép sử dụng lưu ở đơn vị.")
    noi_dung.update({
        "prepared_by": "PI-REF-01", "approved_by": "PI-REF-01", "authors": "PI-REF-01 và nhóm nghiên cứu",
        "org_lines": ["ĐƠN VỊ CHỦ TRÌ (MÃ ĐƠN VỊ DV-01)"], "place_year": "Thành phố — 2026",
        "flow_diagram_plan": "Sơ đồ STROBE: sàng lọc → đủ tiêu chuẩn → tham gia → phân tích (khung, chưa số).",
        "pmids": list(PMID_GOI),
        "tai_lieu_tieng_viet_khong_ap_dung": "Đề tài chỉ trích tài liệu đã có PMID; không dùng luận văn trong nước.",
    })
    noi_dung.update(_DE_CUONG_THEO_THIET_KE.get(thiet_ke, {}))
    for khoa, gia_tri in noi_dung.items():
        meta.setdefault(khoa, gia_tri)
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    ket = NQ.doi_chieu(out, study)
    nguon_kc = next(k for k in ket["thong_so"] if k["ma"] == "ket_cuc_chinh")["nguon"]
    meta["gate_params"].setdefault("G10", {})["xac_nhan_ket_cuc_chinh"] = {
        "giai_trinh": "Các mô tả cùng chỉ một kết cục chính đã định trước trong SAP — chỉ khác cách diễn đạt.",
        "reviewed_at": datetime.now().replace(microsecond=0).isoformat(),
        "dau_van_tay": NQ.dau_van_tay_ket_cuc(nguon_kc)}
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))


def _a12_that(study: str, out: Path, goc: Path, monkeypatch) -> None:
    """Cổng A12 chạy trên ĐỦ PMID gói trích (rút bài + metadata, như check_citations.py) — khoá giả tạm ký biên nhận."""
    _ghi(out / f"A12_CITATION_VERIFICATION_{study}.md",
         "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n")
    monkeypatch.setattr(CCR, "REPO_ROOT", goc)
    monkeypatch.setattr(CCM, "REPO_ROOT", goc)
    CCR.write_retraction_receipt(study, list(PMID_GOI), {p: {"status": "ok"} for p in PMID_GOI})
    CCM.write_metadata_receipt(study, list(PMID_GOI), {p: {"status": "resolved", **_METADATA_THU} for p in PMID_GOI})


def _de_tai_g10_that(tmp_path: Path, monkeypatch, thiet_ke: str = "cohort") -> tuple[str, Path, Path]:
    """G0→G9 KHOÁ (chuỗi thật; A12 chạy trên đủ PMID gói trích) → chủ nhiệm soạn nội dung đề cương → lắp G10 → PI
    hoàn tất hồ sơ phát hành → lắp lại (manifest + dấu tài liệu)."""
    study, out, goc = _de_tai_g9_that(tmp_path, monkeypatch, thiet_ke,
                                      pmid_a12=PMID_GOI + _PMID_HE_THONG.get(thiet_ke, ()))
    append_signed_approval(study, out / G9Q.CHECKPOINT_JSON, "G9", "PI_PROJECT_OWNER", repo_root=goc)
    assert _cham9(study, out, goc, write=True)["status"] == G9Q.STATUS_LOCKED
    _ho_so_g2_that(out, thiet_ke)
    _noi_dung_de_cuong(out, study, thiet_ke)
    _lap_g10(goc, study, monkeypatch)
    _ghi(out / G10Q.READINESS_JSON, json.dumps(_complete_readiness(study), ensure_ascii=False, indent=2))
    _lap_g10(goc, study, monkeypatch)
    return study, out, goc


# ── Chuỗi TRƯỚC IRB thật (G10-09) ───────────────────────────────────────────────────────────────────────────────────

def _dien_g2_nhu_pi(text: str) -> str:
    """PI điền MỌI ô trước-nộp của hồ sơ G2 do run_g2_auto sinh — theo đúng bộ phân loại của g2_quality_gate; ô chỉ điền
    được SAU phê duyệt/đăng ký (số IRB, ngày duyệt, mã đăng ký…) và ô sau khi kết thúc nghiên cứu GIỮ NGUYÊN."""
    ra, trong_huong_dan = [], False
    for tho in text.splitlines():
        dong = unicodedata.normalize("NFC", tho)
        if G2Q._TIEU_DE_RE.match(dong):
            trong_huong_dan = bool(G2Q._KHOI_HUONG_DAN_RE.match(dong))
        for nhan, o in G2Q._o_trong_cua_dong(tho, dong, quet_ho_moi=not trong_huong_dan):
            if not (G2Q._la_o_sau_phe_duyet(dong, nhan, o) or G2Q._SAU_NGHIEN_CUU_RE.search(o)):
                dong = dong.replace(o, "nội dung chủ nhiệm đã soạn", 1)
        ra.append(dong)
    return "\n".join(ra) + ("\n" if text.endswith("\n") else "")


def _de_tai_truoc_irb(tmp_path: Path, monkeypatch, *, muc_dich: str = "ETHICS_SUBMISSION",
                      dien_g2: bool = True) -> tuple[str, Path, Path]:
    """Đề tài CHƯA trình Hội đồng: G0→G1→G3 chốt thật → run_g2_auto THẬT (PI điền ô trước-nộp ⇒ G2
    READY_FOR_IRB_SUBMISSION, chưa ai duyệt) → SAP sinh thật, điền, thống kê viên xác nhận gắn dấu (G4 sẵn sàng ký,
    CHƯA ký) → A12 → chủ nhiệm soạn nội dung đề cương → hồ sơ phát hành mục đích `muc_dich` → lắp G10."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = "G10IRB-cohort"
    out = goc / "exports" / study
    dung_g0_g3_da_chot(out, study, thiet_ke="cohort", them_meta={
        "G1": {"secondary_outcomes": ["Tỷ lệ nhập viện trong 12 tuần"]},  # WHO TRDS mục 20
        "G2": dict(_meta_g2()["gate_params"]["G2"])})
    monkeypatch.setattr(G2A, "_REPO_ROOT", goc)
    monkeypatch.chdir(goc)  # run_g2_auto ghi exports/<mã> theo thư mục làm việc
    monkeypatch.setattr(sys, "argv", ["run_g2_auto.py", "--study", study, "--design", "cohort", "--skip-registry"])
    CS.xoa_dem()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
        G2A.main()
    if dien_g2:
        goi = out / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        goi.write_text(_dien_g2_nhu_pi(goi.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    G2Q.evaluate_study(study, out, write=True)
    sap = sinh_sap_g4_that(out, study)
    noi_dung_sap = dien_sap_g4(sap.read_text(encoding="utf-8"))
    sap.write_text(noi_dung_sap, encoding="utf-8", newline="\n")
    xac_nhan_g4(out, noi_dung_sap)
    _a12_that(study, out, goc, monkeypatch)
    _noi_dung_de_cuong(out, study)
    ho_so = _complete_readiness(study)
    ho_so["release"]["purpose"] = muc_dich
    _ghi(out / G10Q.READINESS_JSON, json.dumps(ho_so, ensure_ascii=False, indent=2))
    _lap_g10(goc, study, monkeypatch)
    return study, out, goc


# ── CHUNG-H: chuỗi THẬT G0→G9 khoá → G10 READY → PI khoá → ràng buộc ─────────────────────────────────────────────────

@pytest.mark.parametrize("thiet_ke", THIET_KE_DAU_CUOI)
def test_chung_h_dau_cuoi_g10_toi_ready_khoa_va_rang_buoc(tmp_path, monkeypatch, thiet_ke):
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch, thiet_ke)
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)
    cp = json.loads((out / G10Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))
    tep = cp["release_manifest"]["files"]
    # G10-04: manifest gồm artifact hợp đồng của các cổng tiền đề + artifact G5 + script R/Python của luồng phân tích.
    if thiet_ke == "rct":
        assert (tep.get("g2_safety_plan") or {}).get("sha256"), "kế hoạch an toàn G2 của RCT phải nằm trong manifest"
    duong_r = thiet_ke in ("qualitative", "sr_ma")  # CLI Python từ chối hai thiết kế này — tóm tắt G6 từ 03_analysis.R
    for khoa in ("g2_ethics_package", "g4_sap_final", "g5_data_lock_manifest", "g5_data_management",
                 "g5_data_dictionary", "g6_analysis_scripts", "g6_script_03_analysis", "g7_manuscript",
                 "g8_peer_review", "g8_peer_review_report", "g9_publication_readiness", "checkpoint_g6",
                 "checkpoint_g7", "checkpoint_g9",
                 *(("g6_analysis_summary_r",) if duong_r
                   else ("g6_analysis_summary", "g6_script_run_analysis_cli_py"))):
        assert (tep.get(khoa) or {}).get("sha256"), khoa
    # G10-02: dấu lắp ráp đúng hai tài liệu cuối.
    md = out / f"DE_CUONG_THONG_NHAT_{study}.md"
    assert cp["artifacts"]["de_cuong_md_sha256"] == G10Q._sha256(md)
    assert cp["artifacts"]["de_cuong_docx_sha256"] == G10Q._sha256(out / f"DE_CUONG_THONG_NHAT_{study}.docx")
    noi_dung = md.read_text(encoding="utf-8")
    assert "[CẦN" not in noi_dung and "BẢN NHÁP" not in noi_dung
    assert "PMID: 30560792" in noi_dung and "Tạp chí thử nghiệm" in noi_dung  # Vancouver từ biên nhận A12
    # CHUNG-F: quyết định G1 (PI không khai lại ở cấp cao) có mặt trong đề cương thống nhất.
    g1 = json.loads((out / "study_meta.json").read_text(encoding="utf-8"))["gate_params"]["G1"]
    for gia_tri in (g1["setting"], g1["study_period"], g1["population"], g1["inclusion_criteria"][0],
                    g1["exclusion_criteria"][0], g1["recruitment_strategy"], g1["objectives"][0],
                    g1["primary_outcome"]["name"]):
        assert gia_tri in noi_dung, gia_tri

    _ky_g10(study, out, goc)
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_LOCKED, _chua_dat(bao)
    assert GC.g10_quality_contract_satisfied(study, repo_root=goc)
    # Lắp lại sau khoá: không ghi đè gói đã khoá.
    truoc = md.read_bytes()
    ma, ra = _lap_g10(goc, study, monkeypatch)
    assert ma == GC.EXIT_OK and "🔒" in ra and md.read_bytes() == truoc
    # G10-05: biên nhận rút bài hết hạn SAU khi khoá ⇒ chỉ cảnh báo, không tự huỷ khoá.
    monkeypatch.setattr(G10A, "A12_RUT_BAI_HAN_NGAY", -1)
    bao = _cham10(study, out, goc)
    a05 = _ck(bao, "G10-AUTO-05")
    assert bao["status"] == G10Q.STATUS_LOCKED and a05["status"] == "PASS" and a05["evidence"].startswith("⚠"), a05


def test_g10_03_ban_thao_sua_sau_g8_truoc_khi_pi_khoa_g10_thi_khong_ready(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    ban_thao = out / f"G7_A8_MANUSCRIPT_{study}.md"
    ban_thao.write_text(ban_thao.read_text(encoding="utf-8") + "\nCâu thêm sau khi người phản biện đã ký.\n",
                        encoding="utf-8", newline="\n")
    bao = _cham10(study, out, goc)
    a2b, a04 = _ck(bao, "G10-AUTO-02B"), _ck(bao, "G10-AUTO-04")
    assert bao["status"] != G10Q.STATUS_READY
    assert a2b["status"] != "PASS" and "G8" in a2b["evidence"], a2b
    assert a04["status"] == "REVIEW" and "G8=False" in a04["evidence"], a04


def test_g10_01_g6_khong_con_dat_khi_cham_song_thi_g10_khong_ready(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    (out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").unlink()
    bao = _cham10(study, out, goc)
    a2b = _ck(bao, "G10-AUTO-02B")
    assert bao["status"] != G10Q.STATUS_READY and a2b["status"] != "PASS" and "G6" in a2b["evidence"], a2b


def test_g10_02_de_cuong_studyspec_ket_cuc_va_a12_cham_lai_tren_ban_hien_hanh(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    md = out / f"DE_CUONG_THONG_NHAT_{study}.md"
    md_goc = md.read_text(encoding="utf-8")
    meta_p = out / "study_meta.json"
    meta_goc = meta_p.read_text(encoding="utf-8")

    # (a) Sửa tay .md sau lắp ráp ⇒ không còn là bản đã lắp.
    md.write_text(md_goc + "\nGhi chú thêm tay sau khi lắp ráp.\n", encoding="utf-8", newline="\n")
    bao = _cham10(study, out, goc)
    a09 = _ck(bao, "G10-AUTO-09")
    assert a09["status"] == "REVIEW" and "KHÁC bản đã lắp" in a09["evidence"], a09
    assert bao["status"] == G10Q.STATUS_DRAFT

    # (b) Xoá §Đạo đức sau lắp ráp ⇒ guardrail đề cương CHẤM LẠI chặn (bản cũ tin khối guardrail lúc lắp).
    tieu_de = S.de_cuong_heading("daoduc")
    dau = md_goc.index(tieu_de)
    cuoi = md_goc.index("\n#", dau + len(tieu_de))
    md.write_text(md_goc[:dau] + md_goc[cuoi + 1:], encoding="utf-8", newline="\n")
    a02 = _ck(_cham10(study, out, goc), "G10-AUTO-02")
    assert a02["status"] == "BLOCK" and "check_de_cuong sống: passed=False" in a02["evidence"], a02
    md.write_text(md_goc, encoding="utf-8", newline="\n")

    # (c) study_meta đổi sau lắp ⇒ StudySpec tính lại khác bản đã lắp.
    meta = json.loads(meta_goc)
    meta["theoretical_framework"] = "Khung lý thuyết khác, chủ nhiệm đổi sau khi lắp ráp"
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    a06 = _ck(_cham10(study, out, goc), "G10-AUTO-06")
    assert a06["status"] == "REVIEW" and "khác STUDY_SPEC đã lắp" in a06["evidence"], a06

    # (d) G10-07: bỏ xác nhận của chủ nhiệm ⇒ các mô tả kết cục chính khác nhau hiện lại thành LỆCH MỀM.
    meta = json.loads(meta_goc)
    meta["gate_params"]["G10"].pop("xac_nhan_ket_cuc_chinh")
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    a11 = _ck(_cham10(study, out, goc), "G10-AUTO-11")
    assert a11["status"] == "REVIEW" and "LỆCH MỀM" in a11["evidence"], a11
    _ghi(meta_p, meta_goc)

    # (e) G10-05: biên nhận rút bài quá hạn TRƯỚC khi PI ký ⇒ REVIEW, hướng dẫn chạy lại A12.
    monkeypatch.setattr(G10A, "A12_RUT_BAI_HAN_NGAY", -1)
    a05 = _ck(_cham10(study, out, goc), "G10-AUTO-05")
    assert a05["status"] == "REVIEW" and "check_citations.py" in a05["evidence"], a05
    monkeypatch.setattr(G10A, "A12_RUT_BAI_HAN_NGAY", 30)

    # Hoàn nguyên đủ ⇒ READY trở lại (mỗi phép thử trên chỉ đổi đúng một thứ).
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)


def test_g10_04_tep_cong_tien_de_doi_sau_khoa_thi_manifest_chan(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    _ky_g10(study, out, goc)
    assert _cham10(study, out, goc)["status"] == G10Q.STATUS_LOCKED
    for ten in (f"G3_A4_SAMPLE_SIZE_{study}.md", f"G1_A2_PROTOCOL_DESIGN_{study}.md",
                "scripts/run_analysis_cli.py", "scripts/03_analysis.R", f"G5_REDCap_dictionary_{study}.csv"):
        tep = out / ten
        cu = tep.read_bytes()
        tep.write_bytes(cu + "\n# sửa sau khi PI khoá gói phát hành\n".encode("utf-8"))
        bao = _cham10(study, out, goc)
        a10 = _ck(bao, "G10-AUTO-10")
        assert bao["status"] == G10Q.STATUS_BLOCKED and a10["status"] == "BLOCK", (ten, a10)
        assert "manifest_match=False" in a10["evidence"], (ten, a10)
        tep.write_bytes(cu)
        assert _cham10(study, out, goc)["status"] == G10Q.STATUS_LOCKED, ten


# ── G10-09: gói trình Hội đồng Đạo đức TRƯỚC IRB (G0–G4) ─────────────────────────────────────────────────────────────

def test_g10_09_goi_trinh_hoi_dong_truoc_irb_toi_ready_va_khoa(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    CS.xoa_dem()
    song = {g: CS.trang_thai_song(g, study, out, repo_root=goc).get("muc") for g in ("G0", "G1", "G2", "G3", "G4")}
    assert song == {"G0": "PASS", "G1": "PASS", "G2": "READY", "G3": "PASS", "G4": "READY"}, song
    assert not GC.ledger_approved("G2", study, out / f"G2_A3_ETHICS_PACKAGE_{study}.md", repo_root=goc)
    # Bộ đo độ tươi THẬT xếp G10 «mồ côi» vì G5–G9 vắng — đúng trạng thái của gói trước dữ liệu (bộ lọc G10-AUTO-03).
    assert any(i.get("gate") == "G10" and i.get("kind") == "orphan_downstream"
               for i in FR.stale_report(out).get("issues") or [])
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)
    a04 = _ck(bao, "G10-AUTO-04")
    assert a04["status"] == "PASS" and "trước dữ liệu" in a04["evidence"], a04
    noi_dung = (out / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
    assert "bản TRÌNH Hội đồng Đạo đức" in noi_dung and "GÓI ETHICS_SUBMISSION" in noi_dung
    assert "BẢN NHÁP" not in noi_dung and "[CẦN" not in noi_dung
    tep = json.loads((out / G10Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))["release_manifest"]["files"]
    assert {"g2_ethics_package", "g2_registration_draft", "g4_sap_final", "checkpoint_g4"} <= set(tep)
    assert not set(tep) & {"g7_manuscript", "g8_peer_review", "g9_checkpoint", "checkpoint_g5", "checkpoint_g9"}
    # Trước dữ liệu chưa có bản thảo/kết quả/tuyên bố dữ liệu-mã để đối chiếu ⇒ G10-HUMAN-02 không đòi hai mục đó.
    ho_so = json.loads((out / G10Q.READINESS_JSON).read_text(encoding="utf-8"))
    ho_so["cross_document_consistency"].update({"manuscript_results_consistent": False,
                                                "data_code_statements_consistent": False})
    _ghi(out / G10Q.READINESS_JSON, json.dumps(ho_so, ensure_ascii=False, indent=2))
    bao = _cham10(study, out, goc, write=True)  # = chạy g10_quality_gate.py trước ký: cập nhật manifest
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)

    _ky_g10(study, out, goc)
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_LOCKED, _chua_dat(bao)
    # Sửa gói đạo đức SAU khi PI khoá bản trình Hội đồng ⇒ manifest chặn.
    goi = out / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    goi.write_text(goi.read_text(encoding="utf-8") + "\nĐoạn thêm sau khi khoá.\n", encoding="utf-8", newline="\n")
    bao = _cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_BLOCKED and _ck(bao, "G10-AUTO-10")["status"] == "BLOCK"


def test_g10_02_assemble_goi_truc_tiep_cung_ghi_dau_lap_rap(tmp_path, monkeypatch):
    """Công cụ khác gọi thẳng run_g10_assemble.assemble() (không qua main — không chèn biểu ngữ, không ghi lại dấu ở
    bước biểu ngữ) vẫn phải có dấu SHA-256 của ĐÚNG hai tài liệu vừa lắp — nếu không G10-AUTO-09 so với dấu cũ."""
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    CS.xoa_dem()
    ket = G10A.assemble(study, out)
    dau = json.loads((out / G10Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))["artifacts"]
    assert dau["de_cuong_md_sha256"] == G10Q._sha256(ket["md"])
    assert dau["de_cuong_docx_sha256"] == G10Q._sha256(ket["docx"])


def test_g10_09_goi_trinh_hoi_dong_ma_g2_chua_dien_xong_thi_khong_ready(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch, dien_g2=False)
    bao = _cham10(study, out, goc)
    a2b = _ck(bao, "G10-AUTO-02B")
    assert bao["status"] != G10Q.STATUS_READY and a2b["status"] == "REVIEW" and "G2" in a2b["evidence"], a2b


def test_g10_09_muc_dich_sau_du_lieu_van_doi_du_g0_g9(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch, muc_dich="JOURNAL_SUBMISSION")
    bao = _cham10(study, out, goc)
    a02 = _ck(bao, "G10-AUTO-02")
    assert bao["status"] == G10Q.STATUS_BLOCKED and "G5" in a02["evidence"] and "G9" in a02["evidence"], a02


def test_g10_09_do_tuoi_chi_bo_dung_loai_mo_coi_g5_g9_cua_goi_truoc_du_lieu(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    ham_that = FR.stale_report

    def _them_van_de(out_dir):
        r = ham_that(out_dir)
        them = {"gate": "G4", "kind": "stale_downstream", "offending_upstream": ["G3"], "reason": "G4 cũ hơn G3"}
        return dict(r, fresh=False, issues=list(r.get("issues") or []) + [them])

    monkeypatch.setattr(FR, "stale_report", _them_van_de)
    a03 = _ck(_cham10(study, out, goc), "G10-AUTO-03")
    assert a03["status"] == "BLOCK" and "G4 cũ hơn G3" in a03["evidence"], a03


# ── Kiểm đơn vị ─────────────────────────────────────────────────────────────────────────────────────────────────────

def test_g10_09_yeu_cau_tien_de_theo_muc_dich():
    truoc = G10Q.yeu_cau_tien_de("ETHICS_SUBMISSION")
    assert truoc["cong"] == ("G0", "G1", "G2", "G3", "G4") and truoc["chap_nhan_san_sang"] == {"G2", "G4"}
    assert truoc["khoa"] == () and G10Q.yeu_cau_tien_de("REGISTRY_UPDATE") == truoc
    for muc_dich in ("JOURNAL_SUBMISSION", "RESEARCH_DOSSIER", None):
        du = G10Q.yeu_cau_tien_de(muc_dich)
        assert du["cong"] == tuple(f"G{i}" for i in range(10)) and not du["chap_nhan_san_sang"]
        assert du["khoa"] == ("G2", "G4", "G5", "G8", "G9")
    assert G10Q.muc_dich_phat_hanh({"release": {"purpose": " ethics_submission "}}) == "ETHICS_SUBMISSION"
    assert G10Q.muc_dich_phat_hanh({"release": {"purpose": "KHONG-CO"}}) is None


def test_g10_04_09_danh_muc_tep_goi_theo_muc_dich(tmp_path):
    study = "S"
    for ten in (f"G5_A6_DATA_MGMT_{study}.md", f"G2_REGISTRATION_DRAFT_{study}.json", "scripts/a.R", "scripts/b.py"):
        (tmp_path / ten).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / ten).write_text("x", encoding="utf-8", newline="\n")
    truoc, _ = G10Q._package_files(study, tmp_path, {"release": {"purpose": "ETHICS_SUBMISSION"}})
    assert {"g2_ethics_package", "g4_sap_final", "g2_registration_draft", "checkpoint_g4"} <= set(truoc)
    assert not set(truoc) & {"g7_manuscript", "g8_peer_review_report", "g9_checkpoint", "checkpoint_g5",
                             "g5_data_management", "g6_script_a", "g6_script_b_py"}
    du, _ = G10Q._package_files(study, tmp_path, {"release": {"purpose": "JOURNAL_SUBMISSION"}})
    assert {"g7_manuscript", "g8_peer_review", "g8_peer_review_report", "g9_checkpoint", "checkpoint_g9",
            "g5_data_management", "g6_script_a", "g6_script_b_py"} <= set(du)


def test_g10_09_luu_tru_truoc_du_lieu_khong_doi_moi_truong_phan_mem():
    ho_so = _complete_readiness("S")
    ho_so["archive_and_reproducibility"]["software_environment_captured"] = False
    assert G10Q._archive_ok(ho_so, "ETHICS_SUBMISSION")[0]
    assert not G10Q._archive_ok(ho_so, "JOURNAL_SUBMISSION")[0]


def _cps(thiet_ke: str, **g2) -> dict:
    return {"G1": {"design": {"internal_code": thiet_ke}}, "G2": dict(g2)}


@pytest.mark.parametrize("thiet_ke, g2, meta, co, khong", [
    ("sr_ma", {"g2_icf_version": "1.0"}, {}, ["Đồng thuận: không áp dụng"], ["ICH-GCP", "ICF phiên bản"]),
    ("cohort", {"g2_icf_waiver_approved": True}, {}, ["MIỄN đồng thuận (ICF waiver) theo quyết định ở G2"],
     ["ICH-GCP", "ICF đồng thuận tham gia"]),
    ("rct", {"g2_icf_version": "2.0", "g2_irb_number": "IRB-REF-9"}, {},
     ["ICH-GCP E6(R3)", "ICF phiên bản 2.0 đã được Hội đồng duyệt", "Số phê duyệt IRB: **IRB-REF-9**"], []),
    ("cohort", {}, {"_g10": {"muc_dich": "ETHICS_SUBMISSION"}, "gate_params": {"G2": {"icf_version": "2.0"}}},
     ["bản TRÌNH Hội đồng Đạo đức", "ICF phiên bản 2.0 trình Hội đồng cùng đề cương"], ["ICH-GCP", G10A.TAG_DV]),
    ("cohort", {}, {"gate_params": {"G2": {"icf_waiver_requested": True}}},
     ["đề nghị Hội đồng MIỄN đồng thuận", f"Số phê duyệt IRB: {G10A.TAG_DV}"], []),
    ("cohort", {}, {}, [f"Đồng thuận/miễn đồng thuận: {G10A.TAG_DV}"], []),
])
def test_g10_08_dao_duc_theo_thiet_ke_va_quyet_dinh_g2(thiet_ke, g2, meta, co, khong):
    van_ban = G10A.sec_daoduc(_cps(thiet_ke, **g2), meta)
    assert "ẩn danh" not in van_ban
    for chuoi in co:
        assert chuoi in van_ban, chuoi
    for chuoi in khong:
        assert chuoi not in van_ban, chuoi


def test_g10_08_dong_dang_ky_uu_tien_ma_that_roi_ke_hoach():
    co_ma = G10A.sec_daoduc(_cps("cohort", g2_registration="NCT01234567", register_where="ClinicalTrials.gov"), {})
    assert "**Đăng ký nghiên cứu:** NCT01234567 — ClinicalTrials.gov." in co_ma
    tu_g8 = G10A.sec_daoduc(_cps("cohort"), {"gate_params": {"G8": {"registration_id": "NCT07654321"}}})
    assert "NCT07654321" in tu_g8
    ke_hoach = G10A.sec_daoduc(_cps("cohort", register_where="WHO ICTRP"),
                               {"registration": {"plan": "Đăng ký trước khi tuyển người đầu tiên"}})
    assert "**Đăng ký nghiên cứu:** Đăng ký trước khi tuyển người đầu tiên (WHO ICTRP)." in ke_hoach


def test_lo_chuoi_that_vancouver_tu_bien_nhan_a12():
    md = {"status": "resolved", "title": "Một thử nghiệm.", "authors": ["Nguyen A", "Tran B"], "journal": "J Test",
          "year": "2020", "doi": "10.1000/xyz"}
    assert G10A._vancouver("123456", md) == (
        "Nguyen A, Tran B. Một thử nghiệm. J Test. 2020. doi:10.1000/xyz. PMID: 123456.")
    bay = dict(md, authors=[f"T{i}" for i in range(7)])
    assert G10A._vancouver("1", bay).startswith("T0, T1, T2, T3, T4, T5, et al. ")
    assert G10A._vancouver("1", dict(md, status="not_found")) is None
    assert G10A._vancouver("1", dict(md, title="")) is None


@pytest.mark.parametrize("a12_dat", [True, False])
def test_lo_chuoi_that_tai_lieu_tham_khao_chi_dung_metadata_khi_a12_dat(tmp_path, monkeypatch, a12_dat):
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {"12345678": {
        "status": "resolved", **_METADATA_THU}}}, ensure_ascii=False), encoding="utf-8", newline="\n")
    goi = []
    monkeypatch.setattr(G10A, "citation_verification_ok",
                        lambda study, out_dir, **kw: goi.append(kw) or (a12_dat, ""))
    cps = {"G0": {"pmids_used_as_seed": ["12345678"]}, "G7": {}}
    meta = {"_g10": {"out_dir": str(tmp_path)}, "tai_lieu_tieng_viet": ["Tác giả C (2024). Luận văn trong nước."]}
    van_ban = G10A.sec_tltk(cps, meta)
    # CHUNG-H: danh mục tham khảo KHÔNG đối chiếu đề cương CŨ trên đĩa (bản đang được lắp thay nó).
    assert goi and all(kw.get("kiem_ban_g10") is False for kw in goi), goi
    assert "Tài liệu tham khảo tiếng Việt (chủ nhiệm khai)" in van_ban and "Luận văn trong nước" in van_ban
    if a12_dat:
        assert "Nguồn thử nghiệm tổng hợp. Tạp chí thử nghiệm. 2018. PMID: 12345678." in van_ban
        assert G10A.TAG_BS not in van_ban
    else:
        assert f"PMID: 12345678 — {G10A.TAG_BS}" in van_ban


def test_lo_chuoi_that_meta_phang_khong_che_khoi_dict_cua_studyspec():
    spec = {"expected_results": {"primary": "Dự kiến khác biệt 5 điểm"}, "theory": {"framework": "Donabedian"}}
    ra = RS.meta_for_render({"expected_results": "chuỗi thô ở cấp cao nhất", "theory": {"framework": "Của meta"}},
                            spec)
    assert ra["expected_results"] == {"primary": "Dự kiến khác biệt 5 điểm"}
    assert ra["theory"] == {"framework": "Của meta"}  # bản thô đã là dict ⇒ giữ dữ kiện người khai


def test_lo_chuoi_that_r4_nhan_pmid_da_qua_a12(tmp_path):
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {
        "12345678": {"status": "resolved"}, "23456789": {"status": "not_found"}, "abc": {"status": "resolved"},
        "34567890": "resolved"}}), encoding="utf-8", newline="\n")
    assert CDC._a12_pmids(tmp_path) == {"12345678"}
    assert CDC._a12_pmids(tmp_path / "khong-co") == set()


@pytest.mark.parametrize("study", ["KHONG-CO-THU-MUC-XYZ", "ten/sai"])
def test_g10_skill_standards_khong_tin_g10_quality_status_luu_tay(study):
    tin_hieu = S.real_world_signals({"G10": {"quality_contract_version": G10Q.QUALITY_CONTRACT_VERSION,
                                             "study": study}}, meta={"g10_quality_status": G10Q.STATUS_LOCKED})
    assert tin_hieu["release_locked"] is False


# ── CHUNG-H đầu–cuối RCT (06/10/2026): lộ khi chạy chuỗi THẬT RCT tới G10 ──────────────────────────────────────────

def test_chung_h_de_cuong_g10_khong_lam_tut_cong_truoc_da_khoa(tmp_path, monkeypatch):
    """Đề cương G10 trích một PMID chưa có trong biên nhận A12 ⇒ chỉ G10 bị giữ (G10-AUTO-05); G7/G8/G9 đã khoá KHÔNG
    tụt ngược. Bản cũ: hàm A12 dùng chung đối chiếu cả đề cương G10 cho G7/G8/G9 ⇒ lắp G10 cho RCT (đề cương trích PMID
    SPIRIT 2025) làm G7 DRAFT, G8 BLOCKED, G9 mất khoá."""
    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    md = out / f"DE_CUONG_THONG_NHAT_{study}.md"
    md.write_text(md.read_text(encoding="utf-8") + "\nTham khảo bổ sung: PMID: 99999999\n", encoding="utf-8",
                  newline="\n")
    CS.xoa_dem()
    for gate, khoa in (("G7", "PASS_G7_CONFIRMED"), ("G8", "PASS_G8_REVIEW_RECORDED"),
                       ("G9", "PASS_G9_PUBLICATION_INTEGRITY_LOCKED")):
        assert CS.trang_thai_song(gate, study, out, repo_root=goc)["status"] == khoa, gate
    a05 = _ck(_cham10(study, out, goc), "G10-AUTO-05")
    assert a05["status"] == "REVIEW" and "99999999" in a05["evidence"], a05
    # Lắp lại: danh mục tài liệu tham khảo KHÔNG phụ thuộc đề cương CŨ trên đĩa (PMID lạ ở bản cũ không biến Vancouver
    # đã xác minh thành ô «[CẦN BỔ SUNG]»).
    _lap_g10(goc, study, monkeypatch)
    moi_md = md.read_text(encoding="utf-8")
    assert "99999999" not in moi_md and "PMID: 12345678 — [CẦN" not in moi_md
    assert "PMID: 12345678." in moi_md


def test_chung_h_studyspec_dung_quyet_dinh_g1_cho_de_cuong_rct():
    """Quyết định RCT PI đã CHỐT ở G1 (gate_params.G1) nuôi §6 đề cương G10 qua StudySpec — không bắt khai lại."""
    import research_study_spec as RS

    from tests._chuoi_da_chot import _G1_RCT_QUYET_DINH

    meta = {"design_code": "rct", "gate_params": {
        "G0": {"intervention": "Can thiệp X", "comparison": "Chăm sóc chuẩn"},
        "G1": dict(_G1_RCT_QUYET_DINH, intervention_or_exposure="Chương trình X có cấu trúc"),
        "G2": {"safety_plan_confirmed": True}}}
    spec = RS.build_study_spec("S-RCT", {"G1": {"design": {"internal_code": "rct"}}}, meta)
    ds, ei = spec["design_specific"], spec["exposure_intervention"]
    assert ds["randomization"] == _G1_RCT_QUYET_DINH["randomisation"]
    assert ds["allocation_concealment"] == _G1_RCT_QUYET_DINH["allocation_concealment"]
    assert ds["blinding"] == _G1_RCT_QUYET_DINH["blinding"]
    assert ds["stopping_rules"] == _G1_RCT_QUYET_DINH["stopping_rescue_rules"]
    assert ds["schedule"] == _G1_RCT_QUYET_DINH["study_schema_timeline"]
    assert "G2_SAFETY_PLAN_S-RCT.md" in ds["harms"]
    assert ei["description"].startswith("Chương trình X có cấu trúc; Can thiệp X 3 buổi/tuần")
    assert ei["comparator"] == "Chăm sóc chuẩn"
    assert not [r["id"] for r in RS.missing_requirements(spec) if r["id"].startswith("R0")]
    # Khoá riêng của study_meta (PI khai lại có chủ ý) vẫn THẮNG giá trị G1.
    meta["design_specific"] = {"randomization": "Ngẫu nhiên đơn giản theo phong bì"}
    spec = RS.build_study_spec("S-RCT", {"G1": {"design": {"internal_code": "rct"}}}, meta)
    assert spec["design_specific"]["randomization"] == "Ngẫu nhiên đơn giản theo phong bì"
    # Chưa xác nhận kế hoạch an toàn ⇒ không trỏ (R03 còn thiếu).
    meta["gate_params"]["G2"]["safety_plan_confirmed"] = False
    spec = RS.build_study_spec("S-RCT", {"G1": {"design": {"internal_code": "rct"}}}, meta)
    assert "harms" not in spec["design_specific"] or not spec["design_specific"].get("harms")


@pytest.mark.parametrize("khoa_g1, khoa_ds", [
    ("masking", "blinding"), ("randomization", "randomization"), ("follow_up_schedule", "schedule"),
    ("reference_standard", "reference_standard"), ("target_condition", "target_condition"),
    ("search_strategy", "search_strategy")])
def test_chung_h_studyspec_nhan_khoa_g1_thay_the_va_theo_thiet_ke(khoa_g1, khoa_ds):
    """Khoá G1 thay thế mà run_g1_auto cũng nhận (masking, randomization, follow_up_schedule) và khoá của thiết kế chẩn
    đoán/tổng quan hệ thống đều nuôi design_specific — không riêng tên chuẩn của RCT."""
    import research_study_spec as RS

    meta = {"gate_params": {"G1": {khoa_g1: "Quyết định đã chốt ở G1"}}}
    spec = RS.build_study_spec("S-X", {}, meta)
    assert spec["design_specific"][khoa_ds] == "Quyết định đã chốt ở G1"


@pytest.mark.parametrize("ds, co", [
    ({"blinding": "Người đánh giá kết cục được làm mù"}, "Người đánh giá kết cục được làm mù"),
    ({"blinding_who": "Người đánh giá", "blinding_how": "Mã hoá nhóm"}, "Người đánh giá — Mã hoá nhóm"),
    ({}, f"{G10A.TAG_BS} — {G10A.TAG_BS}"),
])
def test_chung_h_dong_lam_mu_doc_quyet_dinh_g1_khi_chua_tach(ds, co):
    """Quyết định làm mù chốt ở G1 là MỘT câu (ai + cách) — §6.3 in nguyên câu đó khi PI chưa tách ai/cách."""
    assert f"(SPIRIT 24a/24b):** {co}\n" in G10A._sec_thietke_rct_subsections({"design_specific": ds})


# ── CHUNG-H 8 thiết kế + CHUNG-F (06/10/2026): lộ khi chạy chuỗi THẬT cắt ngang/chẩn đoán/dự báo/SR/định tính ──

@pytest.mark.parametrize("loai, co, khong", [
    ("descriptive_precision", ["DESCRIPTIVE_PRECISION", "không có biên Δ"], ["Margin Δ", "[CẦN"]),
    ("precision", ["DESCRIPTIVE_PRECISION"], ["Margin Δ"]),
    ("non_inferiority", ["NON_INFERIORITY — Margin Δ = 0.1"], []),
    ("equivalence", ["EQUIVALENCE — Margin Δ = 0.1"], []),
    ("superiority", [], ["Loại giả thuyết (tự động từ G3)"]),
    ("khong_ro_loai", [], ["Margin Δ"]),
])
def test_chung_h_dong_gia_thuyet_chi_in_bien_cho_ni_tuong_duong(loai, co, khong):
    """Đề cương mô tả (cắt ngang — thiết kế của C1a) từng in «Margin Δ = [CẦN…] [CẦN Hội đồng… CONSORT-NI]» ⇒ R3 chặn
    G10. Biên Δ chỉ thuộc NI/tương đương; mô tả nói rõ không có biên."""
    van_ban = G10A.sec_cauhoi({"G1": {}, "G3": {"hypothesis_type": loai, "margin": 0.1}}, {})
    dong = next((d for d in van_ban.splitlines() if d.startswith("**Loại giả thuyết")), "")
    for chuoi in co:
        assert chuoi in dong, chuoi
    for chuoi in khong:
        assert chuoi not in dong, chuoi


@pytest.mark.parametrize("meta, co, khong", [
    ({"recruitment_plan": "Chọn mẫu hệ thống phân tầng theo ngày × khung giờ"},
     ["Chọn mẫu hệ thống phân tầng theo ngày × khung giờ"], [f"{G10A.TAG_BS} — phương pháp chọn mẫu"]),
    ({"sampling_method": "Chọn mẫu liên tiếp", "recruitment_plan": "Sàng lọc tại quầy tiếp đón"},
     ["Chọn mẫu liên tiếp", "**Quy trình tuyển:** Sàng lọc tại quầy tiếp đón"], []),
    ({"population": "Người bệnh ngoại trú từ đủ 18 tuổi"},
     ["**Quần thể nghiên cứu:** Người bệnh ngoại trú từ đủ 18 tuổi"], []),
    ({}, [f"{G10A.TAG_BS} — phương pháp chọn mẫu"], ["Quần thể nghiên cứu"]),
])
def test_chung_f_muc_doi_tuong_in_quan_the_va_quy_trinh_tuyen(meta, co, khong):
    """StudySpec D07 nhận chọn mẫu HOẶC quy trình tuyển (G1 recruitment_strategy) — mục Đối tượng phải in cùng thứ đó,
    không in «[CẦN BỔ SUNG]» khi PI đã chốt cách tuyển ở G1 (C1a)."""
    van_ban = G10A.sec_doituong({}, meta)
    for chuoi in co:
        assert chuoi in van_ban, chuoi
    for chuoi in khong:
        assert chuoi not in van_ban, chuoi


def _meta_kieu_c1a() -> dict:
    """Quyết định CHỈ nằm ở gate_params (đúng hình dạng study_meta của C1a đo 06/10/2026 — giá trị tổng hợp)."""
    return {"design_code": "cross_sectional", "gate_params": {
        "G0": {"population": "Quần thể G0", "intervention": "Phơi nhiễm G0", "comparison": "Không có",
               "primary_outcome": "Kết cục G0", "primary_outcome_measure": "Thang 5 mức",
               "primary_outcome_timepoint": "Một lần sau khám", "novelty_justification": "Khoảng trống G0"},
        "G1": {"research_question": "Câu hỏi G1?", "objectives": ["MT1 G1", "MT2 G1"], "setting": "Bối cảnh G1",
               "study_period": "Năm 2027", "population": "Quần thể G1", "inclusion_criteria": ["Chọn G1"],
               "exclusion_criteria": ["Loại G1"], "recruitment_strategy": "Chọn mẫu hệ thống G1",
               "primary_outcome": {"name": "Kết cục G1", "measure": "Mục đơn Likert 5 mức",
                                   "timepoint": "Ngay sau khi khám"},
               "secondary_outcomes": ["Kết cục phụ G1"], "follow_up_schedule": "Đo một lần",
               "design_rationale": "Lý do thiết kế G1", "background_problem": "Vấn đề G1",
               "knowledge_gap": "Khoảng trống G1", "evidence_summary": "Tổng hợp chứng cứ G1",
               "benefit_risk_rationale": "Lợi ích–nguy cơ G1", "team_roles": "Chủ nhiệm, thống kê viên"}}}


def test_chung_f_studyspec_dung_quyet_dinh_g0_g1_khong_bat_khai_lai():
    """C1a (đo trên bản sao 06/10/2026): G1 đủ câu hỏi/mục tiêu/bối cảnh/thời gian/quần thể/tiêu chuẩn/cách tuyển/kết
    cục nhưng StudySpec chỉ đọc khoá cấp cao ⇒ D02/D03/D05–D08 «thiếu», đề cương in «[CẦN BỔ SUNG]». Nay G1 là nguồn
    kế tiếp (G0 sau cùng); khoá cấp cao vẫn thắng."""
    spec = RS.build_study_spec("S-C1A", {}, _meta_kieu_c1a())
    assert spec["question"]["text"] == "Câu hỏi G1?"
    assert spec["objectives"]["specific"] == ["MT1 G1", "MT2 G1"]
    assert (spec["design"]["setting"], spec["design"]["period"]) == ("Bối cảnh G1", "Năm 2027")
    assert spec["design"]["rationale"] == "Lý do thiết kế G1"
    pop = spec["population"]
    assert (pop["description"], pop["inclusion"], pop["exclusion"], pop["recruitment"]) == (
        "Quần thể G1", ["Chọn G1"], ["Loại G1"], "Chọn mẫu hệ thống G1")
    kc = spec["outcomes"]["primary"]
    assert (kc["name"], kc["definition"], kc["timepoint"]) == (
        "Kết cục G1", "Mục đơn Likert 5 mức", "Ngay sau khi khám")
    assert spec["outcomes"]["secondary"] == [{"name": "Kết cục phụ G1"}]
    assert spec["data_collection"]["measurement_times"] == "Đo một lần"
    assert (spec["rationale"]["problem"], spec["rationale"]["evidence_gap"]) == ("Vấn đề G1", "Khoảng trống G1")
    assert spec["literature"]["summary"] == "Tổng hợp chứng cứ G1"
    assert spec["ethics"]["benefit_risk"] == "Lợi ích–nguy cơ G1"
    assert spec["resources"]["team"] == "Chủ nhiệm, thống kê viên"
    assert spec["question"]["pico"] == {"p": "Quần thể G0", "i_e": "Phơi nhiễm G0", "c": "Không có", "o": "Kết cục G0"}
    thieu = {r["id"] for r in RS.missing_requirements(spec)}
    assert not thieu & {"D02", "D03", "D05", "D06", "D07"}, thieu
    assert "D08" in thieu  # nguồn đo kết cục chưa ai khai — vẫn phải báo
    # Khoá cấp cao (PI ghi đè có chủ ý) thắng; thiếu G1 thì lùi về G0.
    meta = _meta_kieu_c1a()
    meta.update({"research_question": "Câu hỏi cấp cao?", "population": "Quần thể cấp cao",
                 "primary_outcome": {"name": "Kết cục cấp cao", "source": "Phiếu"}})
    for khoa in ("population", "primary_outcome", "knowledge_gap"):
        meta["gate_params"]["G1"].pop(khoa)
    spec = RS.build_study_spec("S-C1A", {}, meta)
    assert (spec["question"]["text"], spec["population"]["description"]) == ("Câu hỏi cấp cao?", "Quần thể cấp cao")
    assert spec["outcomes"]["primary"]["name"] == "Kết cục cấp cao"
    assert spec["rationale"]["evidence_gap"] == "Khoảng trống G0"
    meta.pop("population")
    meta.pop("primary_outcome")
    spec = RS.build_study_spec("S-C1A", {}, meta)
    assert spec["population"]["description"] == "Quần thể G0"
    kc = spec["outcomes"]["primary"]
    assert (kc["name"], kc["definition"], kc["timepoint"]) == ("Kết cục G0", "Thang 5 mức", "Một lần sau khám")


def test_chung_f_studyspec_quan_the_g1_dung_truoc_p_cua_pico():
    meta = _meta_kieu_c1a()
    meta["pico"] = {"p": "P tóm tắt"}
    assert RS.build_study_spec("S", {}, meta)["population"]["description"] == "Quần thể G1"
    meta["gate_params"]["G1"].pop("population")
    assert RS.build_study_spec("S", {}, meta)["population"]["description"] == "P tóm tắt"


@pytest.mark.parametrize("thiet_ke, co_index", [("diagnostic", True), ("cohort", False)])
def test_chung_f_index_test_cua_chan_doan_lay_tu_g1(thiet_ke, co_index):
    meta = {"design_code": thiet_ke, "gate_params": {"G1": {"intervention_or_exposure": "Test nhanh X"}}}
    ds = RS.build_study_spec("S", {}, meta)["design_specific"]
    assert (ds.get("index_test") == "Test nhanh X") is co_index


@pytest.mark.parametrize("gp, mong", [
    ({"G1": {"saturation_criterion": "3 phỏng vấn không mã mới"}}, "3 phỏng vấn không mã mới"),
    ({"G3": {"saturation_stopping_rule": "Dừng khi bão hoà"}}, "Dừng khi bão hoà"),
])
def test_chung_f_tinh_du_cua_mau_dinh_tinh_tu_g1_g3(gp, mong):
    spec = RS.build_study_spec("S", {}, {"design_code": "qualitative", "gate_params": gp})
    assert spec["sample_size"]["sampling_sufficiency"] == mong


def test_chung_h_r4_bai_chuan_de_cuong_cua_he_thong_khong_bi_gan_nghi_bia(tmp_path):
    """Đề cương SR trích PRISMA-P 2015 (PMID 25554246 — do hệ chèn từ protocol_checklist_items) từng bị R4 gắn «nghi
    bịa» ⇒ G10 BLOCKED. Nay là GHI CHÚ (vẫn phải qua A12); PMID lạ thật vẫn chặn."""
    import check_de_cuong as CDC

    md = tmp_path / "de_cuong.md"
    md.write_text("# Đề cương\nPRISMA-P 2015 (PMID: 25554246). SPIRIT 2025 (PMID: 40294956).\n"
                  "Cần bác sĩ kiểm chứng.\n", encoding="utf-8", newline="\n")
    bao = CDC.validate(md, tmp_path)
    assert not [e for e in bao["errors"] if e.startswith("R4")], bao["errors"]
    assert any(w.startswith("R4 GHI CHÚ") and "25554246" in w and "A12" in w for w in bao["warnings"])
    assert bao["checks"]["R4_pmid_traceable"].startswith("WARN")
    md.write_text(md.read_text(encoding="utf-8") + "Thêm PMID: 99999999.\n", encoding="utf-8", newline="\n")
    bao = CDC.validate(md, tmp_path)
    loi = [e for e in bao["errors"] if e.startswith("R4")]
    assert loi and "99999999" in loi[0] and "25554246" not in loi[0], loi


@pytest.mark.parametrize("meta, co", [
    ({"analysis": {"software": "NVivo 14"}}, "Phần mềm mã hóa (QDA): NVivo 14."),
    ({"analysis": {}, "design_specific": {"qda_software": "Mã tay theo codebook"}},
     "Phần mềm mã hóa (QDA): Mã tay theo codebook."),
    ({}, f"Phần mềm mã hóa (QDA): {G10A.TAG_BS} (vd NVivo"),
])
def test_chung_h_dong_phan_mem_qda_doc_khai_bao(meta, co):
    """Đề cương định tính in «Phần mềm mã hóa (QDA): [CẦN BỔ SUNG]» VÔ ĐIỀU KIỆN ⇒ G10-AUTO-09 không bao giờ qua."""
    assert co in G10A.sec_sap({"G4": {}, "G1": {"design": {"internal_code": "qualitative"}}}, meta)


def test_chung_h_studyspec_q02_doi_phan_mem_ma_hoa():
    spec = RS.build_study_spec("S", {}, {"design_code": "qualitative"})
    q02 = next(r for r in RS.missing_requirements(spec) if r["id"] == "Q02")
    assert "phần mềm" in q02["label"]
    spec["analysis"]["primary_method"] = "Phân tích chủ đề"
    spec["design_specific"]["audit_trail"] = "Nhật ký mã hoá"
    q02 = next(r for r in RS.missing_requirements(spec) if r["id"] == "Q02")  # chỉ còn thiếu phần mềm ⇒ vẫn báo
    assert q02["paths"] == ["analysis.software | design_specific.qda_software"], q02
    spec["design_specific"]["qda_software"] = "NVivo"
    assert "Q02" not in {r["id"] for r in RS.missing_requirements(spec)}


def test_chung_h_ky_tu_thong_tin_doi_sang_glyph_times_co():
    import md2docx_vn as MD

    assert MD._font_safe("ℹ️ GÓI") == "► GÓI"
