# -*- coding: utf-8 -*-
"""Dựng thư mục đề tài TỔNG HỢP có G0 và G1 ĐÃ CHỐT HỢP LỆ — chấm SỐNG là PASS (soát từng cổng, CHUNG-H, 04/10/2026).

Vì sao có: từ khi các cổng sau CHẤM SỐNG cổng trước (cong_song), fixture kiểu «G1_checkpoint chỉ có
quality_gate=PASS_G1_CONFIRMED» không còn mở cửa được nữa — đúng luật, vì G1 sống của một checkpoint rỗng là BLOCKED.
Test của G2…G10 cần một chuỗi G0→G1 chốt THẬT (đủ artifact, đủ xác nhận, dấu vân tay đúng nội dung). Mô-đun này dựng
chuỗi đó một lần, dùng chung; tự kiểm cong_song trả PASS để fixture hỏng thì lộ ngay chỗ dựng, không lộ ở test sau.
Dữ liệu tổng hợp, không PII, không gọi mạng.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent / "tools"
for _p in (str(_TOOLS), str(_TESTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g0_quality_gate as G0Q  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import skill_standards as S  # noqa: E402
from test_g0_quality_gate_20260728 import _artifact_text, _checkpoint, _confirmed_g0_meta  # noqa: E402
from test_g1_quality_gate import _a2_text, _confirmed_meta, _design  # noqa: E402

# Loại câu hỏi G0 hợp với từng thiết kế (g1_quality_gate._THIET_KE_HOP_LE_THEO_CAU_HOI) và loại kiểm định tương ứng.
_CAU_HOI_THEO_THIET_KE = {
    "rct": ("therapy", "superiority"), "cohort": ("harm", "superiority"), "case_control": ("harm", "superiority"),
    "cross_sectional": ("descriptive", "descriptive"), "diagnostic": ("diagnosis", "superiority"),
    "prediction": ("prediction_model", "descriptive"), "qualitative": ("qualitative", "descriptive"),
    "sr_ma": ("therapy", "superiority"),
}

# Khoá G1 riêng theo thiết kế mà G1-HUMAN-02/03/04 đòi (giá trị tổng hợp, không PII).
_G1_THEO_THIET_KE = {
    "qualitative": {
        "research_question": "Người bệnh trải nghiệm quy trình khám ngoại trú như thế nào?",
        "central_phenomenon": "Trải nghiệm chờ khám", "qualitative_approach": "Phân tích chủ đề (thematic analysis)",
        "data_collection_method": "Phỏng vấn sâu bán cấu trúc",
        "saturation_criterion": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới",
    },
    "sr_ma": {
        "research_question": "Can thiệp X có giảm kết cục Y so với chăm sóc chuẩn?",
        "information_sources": ["PubMed", "Embase", "CENTRAL"],
        "search_strategy": "Chiến lược tìm kiếm đã soạn theo PRISMA-S",
        "search_last_date": "2026-09-30",
        "study_selection_process": "Hai người sàng lọc độc lập, bất đồng do người thứ ba",
    },
}
_G0_THEO_THIET_KE = {"sr_ma": {"registry_manual_checked": {"ictrp": "2026-07-28", "prospero": "2026-07-28"}}}

EFFECTS = [{"pmid": "12345678", "doi": "10.1000/example", "title": "Nguồn thử nghiệm", "type": "RR", "value": "0.80"}]


def _ghi(path: Path, obj: Any) -> None:
    text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8", newline="\n")


def danh_dau_de_tai_thu(exports_root: Path, study: str) -> Path:
    """Đánh dấu ``study_kind=synthetic_test`` (đúng khoá mà tools/mark_study_synthetic.py ghi) cho test chỉ kiểm CƠ CHẾ
    nạp/khử định danh/làm sạch, không dựng chuỗi G0→G4.

    Từ 04/10/2026 (G5-02), đề tài thật chỉ nạp được dữ liệu khi SAP (G4) đã khoá hợp lệ; đề tài thử nghiệm tổng hợp được
    miễn như ở mọi chốt sổ cái khác. Test cần đường «đề tài thật» thì dựng chuỗi bằng
    g5_test_helpers.prepare_upstream_approvals."""
    thu_muc = Path(exports_root) / study
    thu_muc.mkdir(parents=True, exist_ok=True)
    meta_path = thu_muc / "study_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta["study_kind"] = "synthetic_test"
    _ghi(meta_path, meta)
    return meta_path


def dung_g0_g1_da_chot(out_dir: Path, study: str, *, them_meta: Optional[Dict[str, Any]] = None,
                       kiem: bool = True, thiet_ke: str = "rct", chot_g1: bool = True,
                       mau_hieu_qua: Optional[list] = None) -> Dict[str, Any]:
    """Ghi G0 + G1 vào out_dir; trả study_meta đã ghi. them_meta: dict gộp NÔNG theo từng cổng
    ({"G2": {...}} gộp vào gate_params.G2; khoá ngoài gate_params gộp thẳng).

    thiet_ke: một trong 8 mã chuỗi — G0 mang loại câu hỏi hợp thiết kế, G1 ghim đúng thiết kế đó; kiem=True đòi G0 và G1
    chấm sống PASS (chuỗi CHỐT ĐỦ). chot_g1=False: G1 đủ artifact nhưng PI CHƯA xác nhận thiết kế (G1 dừng ở DỰ THẢO)
    — dùng cho test cần «G1 đang soạn»; khi đó kiem chỉ đòi G1 không bị chặn. mau_hieu_qua: mẫu effect size trích ở
    G1 (mặc định một RR 0,80 có PMID); truyền [] cho test cần «G1 không trích được effect size»."""
    hieu_qua = EFFECTS if mau_hieu_qua is None else mau_hieu_qua
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cp0 = _checkpoint(study=study)
    _ghi(out_dir / "G0_checkpoint.json", cp0)
    _ghi(out_dir / f"G0_A1_PICO_FINER_{study}.md", _artifact_text())

    meta = copy.deepcopy(_confirmed_meta())
    g0 = _confirmed_g0_meta()
    loai_cau_hoi, loai_kiem_dinh = _CAU_HOI_THEO_THIET_KE[thiet_ke]
    if (loai_cau_hoi, loai_kiem_dinh) != ("therapy", "superiority") or thiet_ke in _G0_THEO_THIET_KE:
        g0.update({"question_type": loai_cau_hoi, "test_type": loai_kiem_dinh, **_G0_THEO_THIET_KE.get(thiet_ke, {})})
        g0["dau_van_tay_chot"] = G0Q.dau_van_tay_g0(cp0, {"gate_params": {"G0": g0}})
    meta["gate_params"]["G0"] = g0
    for khoa, gia_tri in (them_meta or {}).items():
        if khoa.startswith("G") and khoa[1:].isdigit():
            meta["gate_params"].setdefault(khoa, {}).update(gia_tri)
        else:
            meta[khoa] = gia_tri
    if thiet_ke == "rct":
        design = _design()
    else:
        chuan = S.reporting_standards_for(thiet_ke)
        design = _design(internal_code=thiet_ke, primary=f"Thiết kế {thiet_ke}", reporting_standard=chuan["primary"],
                         protocol_standard=chuan["protocol"])
        meta["design_code"] = thiet_ke
        meta["gate_params"]["G1"]["design"] = thiet_ke
        meta["gate_params"]["G1"].update(_G1_THEO_THIET_KE.get(thiet_ke, {}))
    if not chot_g1:
        meta["gate_params"]["G1"]["design_confirmed"] = False
    meta["gate_params"]["G1"]["dau_van_tay_chot"] = G1Q.dau_van_tay_g1(meta, design)
    _ghi(out_dir / "study_meta.json", meta)

    G1Q.build_supporting_artifacts(study=study, topic=cp0.get("topic", "Chủ đề"), out_dir=out_dir, design=design,
                                   g0_checkpoint=cp0, effects=hieu_qua, meta=meta,
                                   generated_at="2026-07-27T10:00:00+07:00")
    _ghi(out_dir / f"G1_A2_PROTOCOL_DESIGN_{study}.md", _a2_text())
    _ghi(out_dir / "G1_checkpoint.json", {
        "study": study, "gate": "G1", "question_type": S.chuan_hoa_question_type(loai_cau_hoi), "design": design,
        "guardrail": {"passed": True, "errors": []}, "effect_size_samples": hieu_qua,
        "quality_contract_version": G1Q.QUALITY_CONTRACT_VERSION,
    })
    if kiem:
        CS.xoa_dem()
        for gate in ("G0", "G1"):
            song = CS.trang_thai_song(gate, study, out_dir)
            if chot_g1 or gate == "G0":
                assert song["muc"] == "PASS", f"fixture {gate} chưa chốt hợp lệ: {song['status']} — {song.get('ly_do')}"
            else:
                assert song["muc"] != "BLOCKED", f"fixture {gate} bị chặn: {song['status']} — {song.get('ly_do')}"
        CS.xoa_dem()
    return meta


# ═══════════════════════════════════ G3 chốt thật → G4 (soát từng cổng G4, 04/10/2026) ═══════════════════════════════
# Từ khi G4 CHẤM SỐNG G3 (G4-AUTO-12), fixture «G3_checkpoint trơn» không còn mở được G4 — đúng luật. Chuỗi dưới chạy
# run_g3_auto THẬT trên chuỗi G0→G1 RCT đã chốt (kết cục liên tục «Thay đổi điểm số Y», estimand đủ 5 thuộc tính) rồi
# thống kê viên xác nhận ĐÚNG bộ giá trị G3 (dấu vân tay) ⇒ G3 chấm sống PASS_G3_CONFIRMED. Dữ liệu tổng hợp.
KET_CUC_G1 = "Thay đổi điểm số Y"
G3_ARGV_RCT = ["--effect-size", "5", "--effect-type", "MD", "--sd", "10", "--dropout", "0.1"]
G3_DA_CHOT_RCT: Dict[str, Any] = {
    "effect_source": "PMID: 30560792", "effect_source_confirmed": True,
    "sd_source": "PMID: 30560792 — SD 10 điểm", "dropout_source": "Pilot nội bộ 2025, bỏ cuộc 10%",
    "assumptions_confirmed": True, "hypothesis_confirmed": True,
    "powered_for_outcome": KET_CUC_G1, "recruitment_feasibility_confirmed": True,
    "software": "run_g3_auto.py + scipy",
}
# Tham số G3 (dòng lệnh) + xác nhận RIÊNG theo thiết kế để G3 chấm sống PASS_G3_CONFIRMED (đo 04/10/2026). Thiết kế theo
# độ chính xác/không dùng power truyền tham số TƯỜNG MINH qua CLI để run_g3_auto ghim (G3-AUTO-14).
G3_THEO_THIET_KE: Dict[str, tuple] = {
    "rct": (G3_ARGV_RCT, {}),
    "cohort": (["--effect-size", "0.7", "--effect-type", "RR", "--p0", "0.3", "--dropout", "0.1"],
               {"p0_source": "PMID: 30560792 — tỷ lệ biến cố nhóm không phơi nhiễm 30%"}),
    "case_control": (["--effect-size", "2.0", "--effect-type", "OR", "--p0", "0.2", "--dropout", "0.1"],
                     {"p0_source": "PMID: 30560792 — tỷ lệ phơi nhiễm ở nhóm chứng 20%"}),
    "cross_sectional": (["--prevalence", "0.5", "--precision", "0.05", "--dropout", "0.1"],
                        {"prevalence_source": "PMID: 30560792 — tỷ lệ 50% (thận trọng nhất)"}),
    "diagnostic": (["--effect-size", "0.75", "--effect-type", "AUC", "--prevalence", "0.3", "--dropout", "0.1"],
                   {"prevalence_source": "PMID: 30560792 — tỷ lệ hiện mắc 30%"}),
    "qualitative": (["--confirmed-n", "20"],
                    {"confirmed_n_method": "Bão hoà dữ liệu: dừng khi 3 phỏng vấn liên tiếp không có mã mới",
                     "saturation_stopping_rule": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới (n tối thiểu 12)"}),
    "sr_ma": (["--confirmed-n", "15"], {"confirmed_n_method": "RIS/TSA cho kết cục chính (tổng hợp)"}),
    "prediction": (["--confirmed-n", "500"], {"confirmed_n_method": "pmsampsize cho 10 tham số dự báo (tổng hợp)"}),
}


def chay_g3_that(out_dir: Path, study: str, argv: list) -> tuple:
    """Chạy run_g3_auto.main() THẬT với BASE = thư mục chứa exports/ của out_dir; trả (G3_checkpoint, mã thoát)."""
    import contextlib
    import io

    import run_g3_auto as R3

    out_dir = Path(out_dir)
    assert out_dir.parent.name == "exports", "out_dir phải có dạng <gốc>/exports/<đề tài>"
    base_cu, argv_cu = R3.BASE, sys.argv[:]
    R3.BASE = out_dir.parent.parent
    sys.argv = ["run_g3_auto.py", "--study", study, *argv]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                rc = R3.main()
            except SystemExit as exc:
                rc = exc.code
    finally:
        R3.BASE, sys.argv = base_cu, argv_cu
    return json.loads((out_dir / "G3_checkpoint.json").read_text(encoding="utf-8")), rc


def xac_nhan_g3(out_dir: Path, checkpoint: Dict[str, Any]) -> None:
    """Thống kê viên xác nhận ĐÚNG bộ giá trị G3 hiện tại (gate_params.G3.dau_van_tay_chot)."""
    import g3_quality_gate as G3Q

    p = Path(out_dir) / "study_meta.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    meta.setdefault("gate_params", {}).setdefault("G3", {}).update({
        "reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-09-01T09:00:00",
        "dau_van_tay_chot": G3Q.dau_van_tay_g3(checkpoint)})
    _ghi(p, meta)


def dung_g0_g3_da_chot(out_dir: Path, study: str, *, thiet_ke: str = "rct", g3_argv: Optional[list] = None,
                       them_meta: Optional[Dict[str, Any]] = None, chot_g3: bool = True,
                       kiem: bool = True) -> Dict[str, Any]:
    """G0→G1 (thiết kế `thiet_ke`, đã chốt) → G3 chạy THẬT → (chot_g3) xác nhận gắn dấu ⇒ G3 chấm sống PASS.

    Trả G3_checkpoint. them_meta gộp NÔNG theo cổng lên bộ xác nhận G3 mặc định
    (vd {"G3": {"underpowered_acceptance_justification": …}})."""
    argv_mac_dinh, meta_rieng = G3_THEO_THIET_KE[thiet_ke]
    them: Dict[str, Any] = {"G3": {**G3_DA_CHOT_RCT, **meta_rieng}}
    for khoa, gia_tri in (them_meta or {}).items():
        if isinstance(gia_tri, dict) and isinstance(them.get(khoa), dict):
            them[khoa].update(gia_tri)
        else:
            them[khoa] = gia_tri
    dung_g0_g1_da_chot(out_dir, study, thiet_ke=thiet_ke, mau_hieu_qua=[], them_meta=them, kiem=kiem)
    cp, rc = chay_g3_that(out_dir, study, g3_argv or argv_mac_dinh)
    if chot_g3:
        xac_nhan_g3(out_dir, cp)
    if kiem:
        CS.xoa_dem()
        song = CS.trang_thai_song("G3", study, out_dir)
        if chot_g3:
            ly_do = [f"{r['id']}={r['status']}" for r in (song.get("bao_cao") or {}).get("automatic_criteria", [])
                     + (song.get("bao_cao") or {}).get("human_criteria", []) if r.get("status") != "PASS"]
            assert song["muc"] == "PASS", f"fixture G3 ({thiet_ke}) chưa chốt (rc={rc}): {song['status']} — {ly_do}"
        CS.xoa_dem()
    return cp


def dien_chung_chi(text: str, ket_cuc: str = f"{KET_CUC_G1} tại tuần 12") -> str:
    """Điền hai ô của chứng chỉ khoá (PHẦN 5) theo MẪU — vn_prose_style gọn khoảng trắng trong khung nên chuỗi cố
    định của khuôn không khớp bản run_g4_auto ghi ra đĩa."""
    import re

    text = re.sub(r"(║ KQ chính\s*:\s*)\[CẦN[^\]]*\]", lambda m: m.group(1) + ket_cuc, text)
    return re.sub(r"(║ Phân tích\s*:\s*)\[CẦN[^\]]*\]", lambda m: m.group(1) + "ITT (treatment-policy)", text)


def dien_phan_rct(text: str) -> str:
    """Điền phần RIÊNG của SAP RCT: «Quần thể phân tích CHÍNH» (§4) và mọi ô của §13–§15 (bắt buộc từ 04/10/2026)."""
    import re

    text = re.sub(r"(- \*\*Quần thể phân tích CHÍNH:\*\*) \[CẦN[^\]]*\]",
                  r"\1 ITT — khớp chiến lược treatment-policy; per-protocol là phân tích độ nhạy ở §9", text)
    dau, cuoi = text.index("### §13"), text.index("## PHẦN 4")
    khoi = re.sub(r"\[CẦN[^\]]*\]", "Không — can thiệp nguy cơ thấp, theo dõi 12 tuần; lý do ghi trong đề cương",
                  text[dau:cuoi])
    return text[:dau] + khoi + text[cuoi:]


# Ô có NỘI DUNG mà bộ chấm kiểm (EPV/VIF ở §5, phần mềm+seed ở §10, đa so sánh ở §8, kết cục chính ở §2) điền theo
# NHÃN dòng; mọi ô còn lại của PHẦN 3 điền câu trung tính. Theo MẪU (không chuỗi cố định) để bền với vn_prose_style.
_DIEN_THEO_NHAN = (
    ("Kết cục chính", f"{KET_CUC_G1} tại tuần 12"),
    ("Biến độc lập đưa vào", "Tuổi, điểm Y nền — EPV=15 cho 8 biến, VIF<5"),
    ("Biến đưa vào mô hình imputation", "Tuổi, giới, điểm Y nền"),
    ("Nhóm nhỏ tiền định", "Theo tuổi <65/≥65 — TIỀN ĐỊNH"),
    ("Điều chỉnh", "Chỉ 1 kết cục chính nên không cần hiệu chỉnh"),
    ("Packages", "mice, lme4"),
    ("Random seed", "set.seed(20261004)"),
)


def dien_sap_g4(text: str) -> str:
    """Điền SAP do run_g4_auto sinh (mọi thiết kế) như người thật: ô theo nhãn, mọi ô còn lại của PHẦN 2–3, chứng chỉ
    khoá; SAP RCT thêm «Quần thể phân tích CHÍNH» và §13–§15."""
    import re

    dinh_tinh = "CHIẾN LƯỢC MÃ HÓA" in text
    for nhan, gia_tri in _DIEN_THEO_NHAN:
        text = re.sub(rf"(- \*\*{re.escape(nhan)}:\*\*) \[CẦN[^\]]*\]", lambda m, g=gia_tri: f"{m.group(1)} {g}", text)
    phan_mem = "NVivo v14" if dinh_tinh else "R v4.3.1"
    text = re.sub(r"(- \*\*Phần mềm:\*\*) \[CẦN[^\]]*\]", lambda m: f"{m.group(1)} {phan_mem}", text)
    if "### §13" in text:
        text = dien_phan_rct(text)
    dau, cuoi = text.index("## PHẦN 2"), text.index("## PHẦN 4")
    khoi = re.sub(r"\[CẦN[^\]]*\]", "Đã xác định trong đề cương (tổng hợp)", text[dau:cuoi])
    return dien_chung_chi(text[:dau] + khoi + text[cuoi:])


def sinh_sap_g4_that(out_dir: Path, study: str) -> Path:
    """Chạy run_g4_auto.main() THẬT (BASE = thư mục chứa exports/ của out_dir); trả đường dẫn SAP đã sinh."""
    import contextlib
    import io

    import g4_quality_gate as G4Q
    import run_g4_auto as R4

    out_dir = Path(out_dir)
    assert out_dir.parent.name == "exports", "out_dir phải có dạng <gốc>/exports/<đề tài>"
    base_cu, argv_cu = R4.BASE, sys.argv[:]
    R4.BASE = out_dir.parent.parent
    sys.argv = ["run_g4_auto.py", "--study", study]
    CS.xoa_dem()
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            try:
                rc = R4.main()
            except SystemExit as exc:
                rc = exc.code
    finally:
        R4.BASE, sys.argv = base_cu, argv_cu
    sap = out_dir / G4Q.sap_artifact_name(study)
    assert sap.exists(), f"run_g4_auto không sinh SAP (rc={rc}): {buf.getvalue()[-400:]}"
    return sap


def xac_nhan_g4(out_dir: Path, artifact_text: str, **them: Any) -> Dict[str, Any]:
    """Thống kê viên xác nhận G4 (EPV/VIF, dữ liệu thiếu, nhóm nhỏ, vai trò) GẮN DẤU nội dung SAP hiện tại."""
    import g4_quality_gate as G4Q

    p = Path(out_dir) / "study_meta.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    g4 = meta.setdefault("gate_params", {}).setdefault("G4", {})
    g4.update({"epv_vif_reviewed": True, "missing_data_mechanism_confirmed": True,
               "subgroup_multiplicity_predefined_confirmed": True, "reviewed_by_role": "STATISTICIAN",
               "reviewed_at": "2026-09-02T08:00:00+00:00", "dau_van_tay_chot": G4Q.dau_van_tay_g4(artifact_text)})
    g4.update(them)
    _ghi(p, meta)
    return meta
