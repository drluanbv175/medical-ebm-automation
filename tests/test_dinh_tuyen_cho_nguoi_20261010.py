"""Hồi quy 10/10/2026 — ô trống GỬI ĐÍCH DANH người không được tính là «agent còn việc»; chặn chờ người là vàng.

Đo trên C1a (gộp cục bộ #110 + #111): G1-AUTO-07 chỉ còn «Thời gian nghiên cứu» (quyết định PI — G1-HUMAN-03) và
G4-AUTO-10 chỉ còn «[CẦN CHỦ NHIỆM XÁC NHẬN]» ở SAP §5, nhưng bảng trách nhiệm vẫn giao agent G1-T1/G4-T1 — việc agent
không làm được. Kiểm chi tiết tô ĐỎ «máy sửa được» một G0 bị chặn vì CHÍNH nó chờ PI (needs_input MISSING_PICO). Không
test nào gọi mạng; không đổi trạng thái tiêu chí của cổng (vẫn REVIEW), chỉ đổi người chịu trách nhiệm/màu báo.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402
import placeholder_contract as PC  # noqa: E402

STUDY = "S-DINH-TUYEN"


def test_vai_cua_o_trong():
    assert PC.vai_cua_o_trong("[CẦN CHỦ NHIỆM XÁC NHẬN]") == "PI"
    assert PC.vai_cua_o_trong("[CẦN PI ẤN ĐỊNH]") == "PI"
    assert PC.vai_cua_o_trong("[CẦN THỐNG KÊ VIÊN KÝ]") == "STATISTICIAN"
    assert PC.vai_cua_o_trong("[CẦN CNTT BỆNH VIỆN XÁC NHẬN phương pháp]") == "CNTT bệnh viện"
    assert PC.vai_cua_o_trong("[CẦN HỘI ĐỒNG DUYỆT]") == "IRB"
    assert PC.vai_cua_o_trong("[CẦN BỔ SUNG]") is None
    assert PC.vai_cua_o_trong("[CẦN PIPELINE CHẠY LẠI]") is None, "«PI» phải là một từ, không phải tiền tố"


def test_dong_cua_pi_g1():
    assert G1Q.dong_cua_pi_g1("- Thời gian nghiên cứu: [CẦN BỔ SUNG]")
    assert G1Q.dong_cua_pi_g1("- Chiến lược tuyển/chọn mẫu và tránh thiên lệch chọn mẫu: [CẦN BỔ SUNG]")
    assert not G1Q.dong_cua_pi_g1("- Vấn đề nghiên cứu và gánh nặng liên quan: [CẦN BỔ SUNG]")
    assert not G1Q.dong_cua_pi_g1("- Critical-to-quality factors và quality tolerance limits: [CẦN BỔ SUNG]")


def _sap(than_5: str) -> str:
    return ("## PHẦN 3\n### §4 PHÂN TÍCH CHÍNH\n- xong\n\n### §5 PHÂN TÍCH ĐA BIẾN\n" + than_5
            + "\n\n### §6 DỮ LIỆU THIẾU\n- x\n")


def test_g4_o_trong_chi_cua_chu_nhiem():
    sd = ["§5 (Covariates/Phân tích đa biến)"]
    chi_pi = _sap("- biến `chuyenkhoa` [CẦN CHỦ NHIỆM XÁC NHẬN] khoa có tách được không")
    assert G4Q._vai_o_trong_cua_nguoi(chi_pi, sd) == ["PI"]
    assert G4Q._vai_o_trong_cua_nguoi(_sap("- a [CẦN CHỦ NHIỆM XÁC NHẬN]; b [CẦN BỔ SUNG]"), sd) == [], \
        "còn ô trống chung ⇒ vẫn là việc agent"
    assert G4Q._vai_o_trong_cua_nguoi(_sap("- a [CẦN CHỦ NHIỆM XÁC NHẬN]; mã ___"), sd) == []
    assert G4Q._vai_o_trong_cua_nguoi("## PHẦN 3\n### §4 X\n- y\n", sd) == [], "mục VẮNG ⇒ agent khôi phục"
    # Hai mục: §5 chỉ còn ô của chủ nhiệm nhưng §9 VẮNG ⇒ vẫn còn việc agent (không được báo «chờ người»).
    assert G4Q._vai_o_trong_cua_nguoi(chi_pi, sd + ["§9 (Phân tích độ nhạy)"]) == []


def _gia_cham(monkeypatch, gate, rows):
    bao = {"automatic_criteria": rows}
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "DRAFT_X", "nguon": "song", "bao_cao": bao})


def test_trach_nhiem_xep_cho_nguoi_khi_bang_chung_bao(monkeypatch, tmp_path):
    _gia_cham(monkeypatch, "G1", [
        {"id": "G1-AUTO-07", "status": "REVIEW", "label": "x",
         "evidence": "CHỜ NGƯỜI (PI — G1-HUMAN-01/03): 1 dòng còn trống: - Thời gian nghiên cứu: [CẦN BỔ SUNG]",
         "action": "Điền các khoá"}])
    kq = HD.trach_nhiem(STUDY, "G1", tmp_path)
    assert not any(m["id"] == "G1-AUTO-07" for m in kq["agent_con_viec"])
    m = next(x for x in kq["cho_nguoi"] if x["id"] == "G1-AUTO-07")
    assert m["vai"] == "PI" and m["chuan_bi"] == "G1-T1" and m["viec"].startswith("CHỜ NGƯỜI")


def test_trach_nhiem_van_giao_agent_khi_con_o_chung(monkeypatch, tmp_path):
    _gia_cham(monkeypatch, "G1", [
        {"id": "G1-AUTO-07", "status": "REVIEW", "label": "x",
         "evidence": "2 dòng còn trống: - Thời gian nghiên cứu: [CẦN BỔ SUNG] | - Vấn đề nghiên cứu: [CẦN BỔ SUNG]",
         "action": "Điền các khoá"}])
    kq = HD.trach_nhiem(STUDY, "G1", tmp_path)
    assert any(m["id"] == "G1-AUTO-07" for m in kq["agent_con_viec"])


def test_kiem_chi_tiet_chan_cho_nguoi_la_vang_con_lai_van_do():
    def mau_g0(reason):
        cp = {"gate": "G0", "guardrail": {"passed": True}, "quality_gate": {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW"},
              "needs_input": {"blocked": True, "reason_code": reason, "human_message": "chờ"}}
        muc = K.kiem_cong("G0", STUDY, Path("."), {"G0": cp}, {}, {}, {})
        return next(m.muc for m in muc if m.truc == "①" and "Checkpoint" in m.nhan)

    assert mau_g0(GC.REASON_MISSING_PICO) == K.VANG
    assert mau_g0(GC.REASON_MISSING_IRB) == K.VANG
    assert mau_g0(GC.REASON_MISSING_RELEASE_READINESS) == K.DO, "lý do máy làm được vẫn phải đỏ"
    assert GC.REASON_MISSING_SAMPLE_SIZE not in K.LY_DO_CHO_NGUOI
