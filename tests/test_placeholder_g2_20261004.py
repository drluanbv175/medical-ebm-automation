"""G2 nối hợp đồng ô trống chung + tách ô «chỉ điền được SAU phê duyệt» (03–04/10/2026).

Đo 03/10 trên hồ sơ C1a: bộ dò cũ để lọt «Thời gian lưu: ___ năm», «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]», «[sẽ/sẽ không]», thẻ
«[BÁC SĨ RÀ]», 10 ô «[TO BE COMPLETED]» của ICF tiếng Anh…; ngược lại các ô SAU phê duyệt («Số phê duyệt IRB: [CẦN
sau khi nhận]») làm READY_FOR_IRB_SUBMISSION không bao giờ đạt. Khoá: không bao giờ yếu hơn bộ dò cũ; ô sau phê
duyệt chỉ là thông tin ở mốc READY nhưng BẮT BUỘC khi đã có attestation (mốc PASS_G2_APPROVED); chỗ ký/ngày và ô
PII không bị đếm. """
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import g2_quality_gate as G2Q  # noqa: E402
from test_g2_quality_gate import _attestation, _evaluate, _package  # noqa: E402

STUDY = "hai-long-benh-nhan-C1a-BVQY175"
C1A_G2 = ROOT / "exports" / STUDY / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md"


def _ao05(report):
    return next(r for r in report["automatic_criteria"] if r["id"] == "G2-AUTO-05")


# ── _real_text (WHO TRDS 13/14/19/20) ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("v", ["[CẦN PI pin]", "x [tbd] y", "[todo]", "[Pending review]", "[can bo sung]", "[CAN]",
                               "[TO BE COMPLETED]", "___", "[đơn vị]", "CHƯA XÁC NHẬN", "……", ["a"], {"k": "v"}])
def test_real_text_tu_choi_o_trong_va_giu_marker_cu(v):
    assert G2Q._real_text(v) is None, v


@pytest.mark.parametrize("v", ["[Can thiệp giáo dục] cho người bệnh", "[cancer cohort] người lớn",
                               "[Canxi máu] bình thường",
                               "Người bệnh ngoại trú ≥ 18 tuổi"])
def test_real_text_go_bao_nham_can(v):
    assert G2Q._real_text(v) == v


# ── bộ dò dòng: không bao giờ yếu hơn bản cũ ─────────────────────────────────────────────────────────────────────────
_CU_RE = re.compile(r"\[CẦN", re.IGNORECASE)


def _cu_bat(dong: str) -> bool:
    up = dong.upper()
    return ("[CẦN" in up or bool(G2Q._O_MAU_CHUNG_RE.search(dong))) and not any(h in up for h in G2Q._PII_ONLY_HINTS)


@pytest.mark.parametrize("dong", [
    "Quy trình: [CẦN BỔ SUNG quy trình cụ thể của đơn vị]", "Institution: [TO BE COMPLETED]",
    "Nghiên cứu do [đơn vị] thực hiện", "SỐ BẢN NỘP: ___ [CẦN XÁC NHẬN tại Hội đồng đạo đức cơ sở]",
])
def test_moi_dong_bo_cu_bat_thi_bo_moi_cung_bat(dong):
    assert _cu_bat(dong)
    assert G2Q.unresolved_critical_placeholders(_package() + dong + "\n"), dong


@pytest.mark.parametrize("dong", [
    "Thời gian lưu: ___ năm sau kết thúc nghiên cứu", "∎ Dữ liệu nhận dạng: xóa/hủy vật lý trong ___ tháng",
    "Đơn vị chủ trì: [TÊN ĐƠN VỊ — CẦN BỔ SUNG]", "Dữ liệu [sẽ/sẽ không] được chia sẻ", "XÓA mục này nếu không áp dụng",
    "Ngày cụ thể [BÁC SĨ ĐIỀN theo lịch khoa]", "Bệnh viện Quân y 175 [BÁC SĨ RÀ]", "[topic in English] — PROSPERO",
])
def test_o_ma_bo_cu_bo_lot_nay_bi_bat(dong):
    assert G2Q.unresolved_critical_placeholders(_package() + dong + "\n"), dong


@pytest.mark.parametrize("dong", [
    "Ngày ký: ___/___/2026", "Ký tên: ____________", "______ Ký, ghi rõ họ tên", "Họ và tên người tham gia: __________",
    "[Mỗi đồng tác giả cần khai báo COI theo mẫu ICMJE]", "Can thiệp X theo protocol",
])
def test_khong_bao_nham(dong):
    assert G2Q.unresolved_critical_placeholders(_package() + dong + "\n") == [], dong


def test_mien_pii_chi_cho_o_pii_khong_che_ca_dong():
    dong = "Nghiên cứu do [CẦN — họ tên chủ nhiệm], [CẦN — chức danh và khoa] thực hiện"
    con = G2Q.unresolved_critical_placeholders(_package() + dong + "\n")
    assert con and "chức danh" in con[0]                       # bản cũ bỏ qua NGUYÊN dòng vì có «HỌ TÊN»
    chi_pii = "Người liên hệ: [CẦN — họ tên, điện thoại]"
    assert G2Q.unresolved_critical_placeholders(_package() + chi_pii + "\n") == []


# ── mốc trước nộp / sau phê duyệt ─────────────────────────────────────────────────────────────────────────────────
SAU = ["Số phê duyệt IRB: [CẦN sau khi nhận]", "Approval date: [CẦN sau quyết định IRB]",
       "[CẦN — ngày đăng ký thành công]", "[CẦN — chỉ tuyển sau phê duyệt và đăng ký: ___/___/2026]"]


@pytest.mark.parametrize("dong", SAU)
def test_o_sau_phe_duyet_duoc_phan_loai(dong):
    pl = G2Q.classify_placeholders(_package() + dong + "\n")
    assert pl["pre_submission"] == [] and len(pl["post_approval"]) == 1, (dong, pl)


def test_dong_tron_truoc_nop_va_sau_phe_duyet_la_truoc_nop():
    dong = "Số phê duyệt IRB: [CẦN sau khi nhận]; Thời gian lưu: ___ năm"
    pl = G2Q.classify_placeholders(_package() + dong + "\n")
    assert len(pl["pre_submission"]) == 1 and pl["post_approval"] == []


def test_chi_con_o_sau_phe_duyet_thi_ready_duoc(tmp_path):
    report = _evaluate(tmp_path, _package() + "\n".join(SAU) + "\n", ledger=False)
    assert _ao05(report)["status"] == "PASS"
    assert report["status"] == G2Q.STATUS_READY
    assert len(report["post_approval_placeholders"]) == len(SAU)


def test_con_o_truoc_nop_thi_khong_ready(tmp_path):
    report = _evaluate(tmp_path, _package() + "Thời gian lưu: ___ năm\n", ledger=False)
    assert _ao05(report)["status"] == "REVIEW" and report["status"] == G2Q.STATUS_DRAFT


def test_co_attestation_thi_o_sau_phe_duyet_bat_buoc(tmp_path):
    base = _package() + SAU[0] + "\n"
    signed = G2Q.append_attestation(base, _attestation("TEST-G2", base))
    report = _evaluate(tmp_path, signed, ledger=True)
    assert _ao05(report)["status"] == "REVIEW" and report["status"] != G2Q.STATUS_APPROVED


def test_placeholder_total_giam_khi_dien_o_khong_mang_can():
    truoc = "Thời gian lưu: ___ năm\nĐơn vị: [TÊN ĐƠN VỊ — CẦN BỔ SUNG]\n"
    sau = "Thời gian lưu: 10 năm\nĐơn vị: Khoa Khám bệnh C1a\n"
    assert G2Q.placeholder_total(truoc) > G2Q.placeholder_total(sau) == 0
    assert len(_CU_RE.findall(truoc)) == len(_CU_RE.findall(sau)) == 0   # rào cũ (đếm «[CẦN») không thấy khác biệt


@pytest.mark.skipif(not C1A_G2.is_file(), reason="hồ sơ G2 của C1a không có trong checkout này")
def test_c1a_that_khong_it_hon_bo_cu_va_o_sau_phe_duyet_duoc_tach():
    vb = C1A_G2.read_text(encoding="utf-8")
    cu = [d for d in G2Q.strip_attestation(vb).splitlines() if _cu_bat(d)]
    moi = G2Q.unresolved_critical_placeholders(vb)
    assert len(moi) >= len({re.sub(r"\s+", " ", d.strip())[:240] for d in cu if d.strip()})
    pl = G2Q.classify_placeholders(vb)
    assert any("Số phê duyệt IRB" in d for d in pl["post_approval"])
    assert any("TO BE COMPLETED" in d for d in pl["pre_submission"])


# ── rào chống đè hồ sơ đã biên tập của run_g2_auto dùng tổng ô trống của hợp đồng chung ────────────────────────────
def test_rao_chong_de_bat_ca_o_khong_mang_can():
    import shutil as _shutil
    import subprocess as _sp
    study = "PYTEST-G2-RAO-O-TRONG"
    d = ROOT / "exports" / study
    _shutil.rmtree(d, ignore_errors=True)
    try:
        d.mkdir(parents=True)
        # 04/10/2026 (soát từng cổng): G2 CHẤM SỐNG G1 — một G1_checkpoint chỉ có «design» (không artifact, không
        # G0) là G1 BỊ CHẶN và G2 dừng đúng luật (mã 3). Fixture dựng chuỗi G0→G1 thật (tests/_chuoi_da_chot.py).
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: PLC0415
        dung_g0_g1_da_chot(d, study)

        def _chay(*them):
            return _sp.run([sys.executable, str(ROOT / "tools" / "run_g2_auto.py"), "--study", study, "--topic",
                            "Can thiệp X ở người trưởng thành", "--design", "rct", "--skip-registry", *them],
                           cwd=ROOT, capture_output=True, text=True, timeout=180)

        assert _chay().returncode == 0
        ho_so = d / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        mau = ho_so.read_text(encoding="utf-8")
        assert "___" in mau
        bien_tap = mau.replace("___", "10", 1)          # số «[CẦN» KHÔNG đổi — rào cũ không thấy
        assert bien_tap.count("[CẦN") == mau.count("[CẦN")
        ho_so.write_text(bien_tap, encoding="utf-8", newline="\n")
        r = _chay()
        assert r.returncode == 2 and "TỪ CHỐI đè hồ sơ đạo đức" in r.stdout, r.stdout[-800:]
        assert ho_so.read_text(encoding="utf-8") == bien_tap
    finally:
        _shutil.rmtree(d, ignore_errors=True)
