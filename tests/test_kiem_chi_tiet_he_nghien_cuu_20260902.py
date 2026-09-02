"""Hồi quy: kiem_chi_tiet_he_nghien_cuu — ghép 5 trục × 11 cổng, luật màu BH08, mã thoát.

Vì sao có (02/09/2026, Prompt audit/09 repo gốc): muốn biết «hệ đã tự động và đúng
chuẩn ở TỪNG cổng chưa» phải chạy tay ≥7 công cụ rời rạc rồi tự ghép — mỗi lần ghép
là một lần bỏ sót. Khoá bốn hành vi của bộ ghép:
1. Tiêu chí quality gate tách MÁY/NGƯỜI đúng (HUMAN FAIL vẫn là việc người, không đỏ máy).
2. .docx sai font/cỡ/ký tự trang trí ⇒ 🔴 máy-sửa-được; .docx qua chuan_trinh_bay ⇒ 🟢.
3. Chuỗi cổng: chỉ cổng ĐẦU máy-làm-được-mà-chưa-chạy đỏ; cổng sau chờ theo chuỗi = vàng;
   cổng chờ chữ ký thật = vàng (không phải lỗi).
4. Checkpoint tự mâu thuẫn (needs_input.blocked mà quality_gate đã PASS) ⇒ 🔴, mã 2;
   đề tài không tồn tại ⇒ mã 3, không im lặng.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import chuan_trinh_bay as C  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402


def test_phan_loai_tieu_chi_tach_may_va_nguoi():
    rep = {
        "status": "DRAFT",
        "automatic_criteria": [
            {"id": "G4-AUTO-01", "status": "PASS"},
            {"id": "G4-AUTO-02", "status": "FAIL"},
            {"id": "G4-AUTO-03", "status": "REVIEW"},
        ],
        "approval_criteria": [
            {"id": "G4-HUMAN-01", "status": "REVIEW"},
            {"id": "G4-HUMAN-02", "status": "FAIL"},
        ],
        "checks": [  # khuôn G6
            {"id": "G6-AUTO-05", "pass": False, "blocking": True},
            {"id": "G6-AUTO-06", "pass": None},
            {"id": "G6-AUTO-07", "pass": True},
        ],
    }
    pl = K.phan_loai_tieu_chi(rep)
    assert pl["auto_do"] == ["G4-AUTO-02", "G6-AUTO-05"]
    assert pl["auto_vang"] == ["G4-AUTO-03", "G6-AUTO-06"]
    assert pl["nguoi_vang"] == ["G4-HUMAN-01"]
    assert pl["nguoi_do"] == ["G4-HUMAN-02"], "HUMAN FAIL là việc người thật, không được lẫn vào auto_do"


def test_mau_trang_thai():
    assert K.mau_trang_thai("PASS_G0_CONFIRMED") == K.XANH
    assert K.mau_trang_thai("PASS_G4_SAP_LOCKED") == K.XANH
    assert K.mau_trang_thai("BLOCKED") == K.DO
    assert K.mau_trang_thai("DRAFT_NEEDS_HUMAN_CONTENT") == K.VANG
    assert K.mau_trang_thai("READY_FOR_SIGNATURE") == K.VANG
    assert K.mau_trang_thai(None) == K.TRANG


def test_docx_sai_chuan_do_docx_chuan_xanh(tmp_path):
    md = tmp_path / "G2_A3_ETHICS_PACKAGE_X.md"
    md.write_text("# Hồ sơ\n", encoding="utf-8", newline="\n")
    docx = md.with_suffix(".docx")
    # (a) thiếu .docx → đỏ, máy sửa được
    r = K.danh_gia_docx(md, docx)
    assert r[0][0] == K.DO and r[0][3] is True
    # (b) .docx sai: Courier New 9pt + ký tự trang trí
    doc = Document()
    doc.styles["Normal"].font.name = "Courier New"
    doc.styles["Normal"].font.size = Pt(9)
    doc.add_paragraph("✅ Đã duyệt nội dung " * 20)
    doc.save(docx)
    r = K.danh_gia_docx(md, docx)
    assert r[0][0] == K.DO and r[0][3] is True
    bc = r[0][2]
    assert "font ưu thế" in bc and "cỡ thân bài" in bc and "ký tự trang trí" in bc, bc
    # (c) .docx đi qua chuan_trinh_bay → xanh
    doc = Document()
    doc.add_paragraph("✅ Nội dung chuẩn " * 20)
    t = doc.add_table(rows=1, cols=1)
    t.rows[0].cells[0].text = "ô bảng"
    C.ap_dinh_dang_tai_lieu(doc)
    doc.save(docx)
    r = K.danh_gia_docx(md, docx)
    assert r[0][0] == K.XANH, r
    assert all(x[0] != K.DO for x in r)


def test_trang_thai_chuoi_chi_cong_dau_do():
    m0, _ = K.trang_thai_chuoi("G0", {}, {})
    assert m0 == K.DO, "G0 không có tiền đề — máy làm được mà chưa chạy"
    m1, ly1 = K.trang_thai_chuoi("G1", {}, {})
    assert m1 == K.VANG and "G0" in ly1, "cổng sau chờ theo chuỗi — không dựng bức tường đỏ"
    m5, ly5 = K.trang_thai_chuoi("G5", {"G4": {}}, {"G4": False})
    assert m5 == K.VANG and "G4" in ly5, "chờ chữ ký thật là việc người, không phải lỗi"
    m5b, _ = K.trang_thai_chuoi("G5", {"G4": {}}, {"G4": True})
    assert m5b == K.DO, "G4 đã ký mà G5 chưa chạy — máy làm được"


def _run(root: Path, study: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS / "kiem_chi_tiet_he_nghien_cuu.py"), "--study", study,
         "--exports-root", str(root), "--no-write", "--khong-canary", *extra],
        capture_output=True, text=True, timeout=300, encoding="utf-8")


def _bang_diem(stdout: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    sau = stdout.split("BẢNG ĐIỂM", 1)[1] if "BẢNG ĐIỂM" in stdout else ""
    for line in sau.splitlines():
        m = re.match(r"\s+(G\d{1,2})\s+(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).split()
    return out


def test_de_tai_khong_ton_tai_ma_3(tmp_path):
    r = _run(tmp_path, "KHONG-TON-TAI-KCT")
    assert r.returncode == 3, r.stdout + r.stderr


def test_checkpoint_tu_mau_thuan_bi_bat_ma_2(tmp_path):
    study = "PYTEST-KCT-MAU-THUAN"
    d = tmp_path / study
    d.mkdir()
    (d / "G0_checkpoint.json").write_text(json.dumps({
        "gate": "G0", "guardrail": {"passed": True},
        "needs_input": {"blocked": True, "reason_code": "MISSING_PICO", "human_message": "PICO chưa chốt"},
        "quality_gate": {"status": "PASS_G0_CONFIRMED"},
    }), encoding="utf-8", newline="\n")
    r = _run(tmp_path, study)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "TỰ MÂU THUẪN" in r.stdout
    assert _bang_diem(r.stdout)["G0"][0] == K.DO


def test_de_tai_moi_g0_do_cong_sau_vang(tmp_path):
    """Đề tài ĐÃ ghim chủ đề trong study_meta nhưng chưa chạy cổng nào.

    Fixture sửa 02/09 (vòng rà 2): bản đầu dùng thư mục RỖNG — nay thư mục rỗng bị
    TỪ CHỐI đúng (không phải đề tài, mã 3). Khẳng định gốc giữ NGUYÊN, không nới:
    chỉ cổng ĐẦU chuỗi máy-làm-được-mà-chưa-chạy mới đỏ, cổng sau vàng.
    """
    study = "PYTEST-KCT-MOI"
    d = tmp_path / study
    d.mkdir()
    (d / "study_meta.json").write_text(json.dumps({"topic": "Đề tài mới ghim chủ đề"}),
                                       encoding="utf-8", newline="\n")
    r = _run(tmp_path, study)
    assert r.returncode == 2, r.stdout + r.stderr
    bd = _bang_diem(r.stdout)
    assert bd["G0"][0] == K.DO, bd
    assert bd["G1"][0] == K.VANG and bd["G5"][0] == K.VANG and bd["G10"][0] == K.VANG, bd
    assert "Cần bác sĩ kiểm chứng" in r.stdout


class TestDocxMoCoi:
    """Điểm mù vòng rà thứ hai (02/09): .docx KHÔNG có .md đi kèm từng thoát mọi phép kiểm.

    Đo trên C1a: 4 bản do gen_research_docx sinh thẳng từ checkpoint (G6a/G6b/G6d/
    G9_READINESS) chưa từng bị soi lần nào; 3/4 còn thân bài 11pt + ký tự trang trí.
    """

    def test_gom_docx_theo_tien_to_ten_file(self, tmp_path):
        for ten in ("G6a_ANALYSIS_X.docx", "G1_A2_PROTOCOL_DESIGN_X.docx",
                    "G10_GOI_NOP_X.docx", "DE_CUONG_THONG_NHAT_X.docx"):
            (tmp_path / ten).write_bytes(b"x")
        theo = K.docx_theo_cong(tmp_path)
        assert [p.name for p in theo["G6"]] == ["G6a_ANALYSIS_X.docx"]
        assert [p.name for p in theo["G1"]] == ["G1_A2_PROTOCOL_DESIGN_X.docx"]
        assert sorted(p.name for p in theo["G10"]) == ["DE_CUONG_THONG_NHAT_X.docx",
                                                       "G10_GOI_NOP_X.docx"], "tài liệu gói nộp về G10"

    def test_docx_mo_coi_sai_chuan_van_bi_bat(self, tmp_path):
        dx = tmp_path / "G6a_ANALYSIS_X.docx"
        doc = Document()
        doc.styles["Normal"].font.size = Pt(11)
        doc.add_paragraph("⚠ Tài liệu nháp " * 20)
        doc.save(dx)
        assert not dx.with_suffix(".md").exists()
        r = K.danh_gia_docx(None, dx)
        assert r[0][0] == K.DO and r[0][3] is True, r
        assert "cỡ thân bài" in r[0][2] and "ký tự trang trí" in r[0][2], r[0][2]

    def test_mo_coi_dat_chuan_thi_xanh_va_khong_doi_mtime(self, tmp_path):
        dx = tmp_path / "G6a_ANALYSIS_X.docx"
        doc = Document()
        doc.add_paragraph("Nội dung nháp " * 20)
        C.ap_dinh_dang_tai_lieu(doc)
        doc.save(dx)
        r = K.danh_gia_docx(None, dx)
        assert [x[0] for x in r] == [K.XANH], r

    def test_bao_cao_bat_mo_coi_va_chi_dung_cach_sua(self, tmp_path):
        study = "PYTEST-KCT-MOCOI"
        d = tmp_path / study
        d.mkdir()
        (d / "G0_checkpoint.json").write_text(json.dumps({"gate": "G0"}), encoding="utf-8", newline="\n")
        doc = Document()
        doc.styles["Normal"].font.size = Pt(11)
        doc.add_paragraph("⚠ nháp " * 20)
        doc.save(d / f"G6a_ANALYSIS_{study}.docx")
        r = _run(tmp_path, study)
        assert r.returncode == 2, r.stdout + r.stderr
        assert "G6a_ANALYSIS" in r.stdout
        assert "KHÔNG có .md nguồn" in r.stdout, "phải chỉ đúng cách sửa (chạy lại bộ sinh)"
        assert _bang_diem(r.stdout)["G6"][3] == K.DO


class TestTuChoiThuMucKhongPhaiDeTai:
    """Đo 02/09 (vòng rà 2): chạy trên exports/chatgpt_project và exports/phase_2b —
    hai thư mục KHÔNG phải đề tài — vẫn ra bảng điểm 11 cổng, 38 🟡 và một 🔴 «G0 chưa
    chạy, máy làm được» kèm lời khuyên chạy run_g0_auto trên chúng. Bảng điểm trông có
    thẩm quyền cho thứ không có cổng nào = báo động giả BH08, gặp ngay lần gõ nhầm mã.
    """

    def test_nhan_dien_dung_ba_truong_hop(self, tmp_path):
        co_g0 = tmp_path / "co-g0"
        co_g0.mkdir()
        (co_g0 / "G0_checkpoint.json").write_text('{"topic": "X"}', encoding="utf-8", newline="\n")
        assert K.la_de_tai_nghien_cuu(co_g0)[0] is True

        la = tmp_path / "thu-muc-la"
        la.mkdir()
        (la / "README.md").write_text("x", encoding="utf-8", newline="\n")
        ok, vi_sao = K.la_de_tai_nghien_cuu(la)
        assert ok is False and "G0_checkpoint.json" in vi_sao

        rong = tmp_path / "rong"
        rong.mkdir()
        ok, vi_sao = K.la_de_tai_nghien_cuu(rong)
        assert ok is False and "RỖNG" in vi_sao

    def test_cli_tu_choi_ma_3_va_khong_in_bang_diem(self, tmp_path):
        study = "PYTEST-KCT-KHONG-PHAI-DE-TAI"
        d = tmp_path / study
        d.mkdir()
        (d / "bao_cao_smoke.json").write_text("{}", encoding="utf-8", newline="\n")
        r = _run(tmp_path, study)
        assert r.returncode == 3, r.stdout + r.stderr
        assert "KHÔNG phải một đề tài nghiên cứu" in r.stdout
        assert "BẢNG ĐIỂM" not in r.stdout, "không được in bảng điểm cho thứ không có cổng nào"
        assert "list_studies.py" in r.stdout, "phải chỉ đường xem danh sách đề tài thật"
