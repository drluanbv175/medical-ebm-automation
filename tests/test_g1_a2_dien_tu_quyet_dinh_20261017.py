"""A2 của G1 điền từ quyết định ĐÃ CÓ + trỏ sang cổng đã làm — 17/10/2026 (hoàn thiện G1 của C1a: A2 còn 65 ô [CẦN]).

Trước đây khối thiết kế STROBE, bảng thiết kế ứng viên, mục effect size, §0.8 cỡ mẫu và khung SAP 12 mục của A2 luôn là
ô trống — dù PI đã ghi quyết định ở `gate_params` và G3/G4 đã tính/soạn. Test chốt:
① dòng STROBE điền từ G0/G1/G3 kèm NGUỒN khoá; tệp từ điển dữ liệu KHÔNG được ghi là «PI đã chốt»; nhãn [CẦN] trong giá
   trị không được coi là đã ghi;
② câu cỡ mẫu từ G3 nói rõ khi G3 CHƯA được PI xác nhận, và không đặt số ngay sau dấu hai chấm (rào R5);
③ §0.8 trỏ sang G3, giữ nhãn hoãn «[CẦN PI CHỐT Ở G3]» (bộ chấm G1 coi là ô của cổng sau) khi G3 chưa xác nhận;
④ bảng thiết kế: ô khả thi/lực lấy từ quyết định + G3; phương án thay thế đã pin ⇒ «—»; descriptive_precision ⇒ effect
   size «không áp dụng»;
⑤ có SAP G4 ⇒ PHẦN 5/6 trỏ SAP (giữ tiêu đề), không còn ô [CẦN] ở đó; chưa có SAP ⇒ giữ khung.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_design_blocks as G1D  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import run_g1_auto as G1  # noqa: E402

STUDY = "S-G1A2"
THAN = "\n".join([
    "  Thời điểm đo PHƠI NHIỄM so với lúc bắt đầu nghiên cứu: [CẦN]",
    "  Thời điểm xác định KẾT CỤC so với lúc đo phơi nhiễm: [CẦN]",
    "Sai lệch KHÔNG ĐÁP ỨNG (non-response): tỷ lệ dự kiến + cách bàn luận: [CẦN]",
    "  quả; nguồn dữ liệu và phương pháp đo cho TỪNG biến: [CẦN] (mục 7 + 8)",
    "  Dữ liệu thu thập MỚI hay khai thác từ nguồn có sẵn (hồ sơ/đăng bộ): [CẦN]",
])


def _cp_g3(d: Path, *, xac_nhan: bool) -> None:
    cp = {"hypothesis_type": "descriptive_precision", "n_adjusted": 808, "design_effect": 1.78, "confirmed_n": 1000,
          "quality_gate": {"human_confirmation_complete": xac_nhan}}
    (d / "G3_checkpoint.json").write_text(json.dumps(cp), encoding="utf-8", newline="\n")


def test_dong_strobe_dien_tu_g0_g1_g3_kem_nguon():
    them = {"G0.intervention": "Thời gian chờ theo mốc HIS", "primary_outcome.timepoint": "Ngay sau khi khám xong",
            "G3.dropout": "dự phòng 15% — phiếu lỗi", "tu_dien_du_lieu": "`_bo-bien-rieng.csv`"}
    ra = G1D.dien_tu_quyet_dinh(THAN, {}, "", them).splitlines()
    assert ra[0].endswith("Thời gian chờ theo mốc HIS (PI đã chốt — gate_params.G0.intervention)")
    assert "(PI đã chốt — gate_params.G1.primary_outcome.timepoint)" in ra[1]
    assert "dự phòng 15% — phiếu lỗi (PI đã chốt — gate_params.G3.dropout + dropout_source)" in ra[2]
    assert "`_bo-bien-rieng.csv` (trỏ tệp — chưa phải xác nhận của PI)" in ra[3] and "PI đã chốt" not in ra[3]
    assert ra[4].endswith("[CẦN]"), "không có khoá ⇒ giữ ô trống cho PI"


def test_gia_tri_nhan_can_khong_tinh_la_da_ghi():
    ra = G1D.dien_tu_quyet_dinh(THAN, {}, "", {"G0.intervention": "[CẦN BÁC SĨ VIẾT]"})
    assert ra.splitlines()[0].endswith("[CẦN]")


def test_gia_tri_ngoai_g1_chi_lay_khi_du(tmp_path):
    meta = {"gate_params": {"G0": {"intervention": "Thời gian chờ"},
                            "G1": {"primary_outcome": {"timepoint": "Sau khám"}},
                            "G3": {"dropout": 0.15, "dropout_source": "kinh nghiệm vận hành"}}}
    (tmp_path / "_bo-bien-rieng.csv").write_text("bien,kieu\n", encoding="utf-8", newline="\n")
    ra = G1._gia_tri_ngoai_g1(meta, tmp_path)
    assert ra["G0.intervention"] == "Thời gian chờ" and ra["primary_outcome.timepoint"] == "Sau khám"
    assert ra["G3.dropout"] == "dự phòng 15% — kinh nghiệm vận hành" and "tu_dien_du_lieu" in ra
    meta["gate_params"]["G3"].pop("dropout_source")
    (tmp_path / "_bo-bien-rieng.csv").unlink()
    ra = G1._gia_tri_ngoai_g1(meta, tmp_path)
    assert "G3.dropout" not in ra, "tỷ lệ không kèm nguồn ⇒ không điền"
    assert "tu_dien_du_lieu" not in ra


def test_cau_co_mau_g3_noi_ro_chua_xac_nhan_va_khong_vuong_r5(tmp_path):
    _cp_g3(tmp_path, xac_nhan=False)
    cau = G1._cau_co_mau_g3(tmp_path)
    assert "N tối thiểu 808" in cau and "N hiệu lực 1000" in cau and "G3 CHƯA được PI xác nhận" in cau
    assert not re.search(r":\s*\d", cau), "R5 cấm «cỡ mẫu…: <số>» không kèm [CẦN]"
    _cp_g3(tmp_path, xac_nhan=True)
    assert "CHƯA được PI xác nhận" not in G1._cau_co_mau_g3(tmp_path)
    assert G1._cau_co_mau_g3(tmp_path / "khong-co") == ""


def test_muc_08_tro_sang_g3_giu_nhan_hoan(tmp_path):
    loi = "### 0.8 Cỡ mẫu\n" + "\n".join(G1._DONG_08_G3[:1]) + "\n- Effect size/MCID…:\n" + "\n".join(
        G1._DONG_08_G3[1:]) + "\n"
    assert G1._tro_co_mau_g3(loi, tmp_path) == loi, "chưa có G3 ⇒ không đổi"
    _cp_g3(tmp_path, xac_nhan=False)
    ra = G1._tro_co_mau_g3(loi, tmp_path)
    assert "CẦN TÍNH Ở G3" not in ra and "đã tính ở G3 — xem `G3_A4_SAMPLE_SIZE`" in ra
    assert "không áp dụng effect size — cỡ mẫu theo độ chính xác" in ra
    dong = [x for x in ra.splitlines() if "G3_A4_SAMPLE_SIZE" in x]
    assert len(dong) == 3 and all(G1Q._HOAN_CHO_CONG_SAU.search(x) for x in dong), "vẫn là ô của cổng sau"
    _cp_g3(tmp_path, xac_nhan=True)
    assert "[CẦN" not in G1._tro_co_mau_g3(loi, tmp_path)


def _a2(tmp_path: Path, *, g3: bool, kha_thi: bool) -> str:
    design = G1.infer_study_design("descriptive", {}, "hài lòng người bệnh cắt ngang")
    pin = "[Đã pin bởi bác sĩ — không áp dụng bảng thiết kế thay thế tự động]"
    design["alternative_1"] = design["alternative_2"] = pin
    if g3:
        _cp_g3(tmp_path, xac_nhan=False)
    meta = {"gate_params": {"G1": {"feasibility_confirmed": kha_thi}}}
    return G1.generate_g1_artifact("t", STUDY, "descriptive", design, [], {}, "2026-10-17 10:00", meta, tmp_path)


def test_bang_thiet_ke_va_effect_size_khi_co_g3(tmp_path):
    a2 = _a2(tmp_path, g3=True, kha_thi=True)
    hang = next(x for x in a2.splitlines() if "**→ ƯU TIÊN**" in x)
    assert "PI đã xác nhận (gate_params.G1.feasibility_confirmed)" in hang and "N hiệu lực 1000" in hang
    thay = [x for x in a2.splitlines() if x.startswith("| [Đã pin bởi bác sĩ")]
    assert len(thay) == 2 and all(x.count("— (thiết kế đã pin)") == 2 for x in thay)
    assert "Không áp dụng: cỡ mẫu tính theo ĐỘ CHÍNH XÁC" in a2 and "Không trích xuất được effect size" not in a2


def test_bang_thiet_ke_chua_co_quyet_dinh_giu_o_trong(tmp_path):
    a2 = _a2(tmp_path, g3=False, kha_thi=False)
    hang = next(x for x in a2.splitlines() if "**→ ƯU TIÊN**" in x)
    assert "[CẦN BÁC SĨ]" in hang and "[CẦN cỡ mẫu]" in hang
    assert "Không trích xuất được effect size" in a2


def test_khung_sap_tro_sap_g4_khi_co(tmp_path):
    khong_sap = _a2(tmp_path, g3=False, kha_thi=False)
    assert "đã thay bằng SAP chính thức ở G4" not in khong_sap
    (tmp_path / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text("**Phiên bản SAP:** 1.3\n", encoding="utf-8", newline="\n")
    a2 = _a2(tmp_path, g3=False, kha_thi=False)
    p5, p7 = a2.index("## PHẦN 5 — SAP SKELETON (đã thay bằng SAP chính thức ở G4)"), a2.index("## PHẦN 7 —")
    khoi = a2[p5:p7]
    assert "phiên bản 1.3" in khoi and "## PHẦN 6 — SAP LOCK CERTIFICATE (khoá ở G4)" in khoi
    assert "[CẦN" not in khoi
