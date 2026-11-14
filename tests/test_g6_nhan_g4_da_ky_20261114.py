"""N1 (14/11/2026, giả lập RCT lần 2 — mức CAO): G6 phải nhận «G4 đã khoá» theo TRẠNG THÁI SỐNG, không đòi `g4_status`.

Lỗi: `tools/run_stats_analysis.py` đòi trường `g4_status` của G4_checkpoint mang chữ LOCKED — trường mà
`tools/approve_gate.py` (và `g4_quality_gate.refresh_checkpoint`) KHÔNG BAO GIỜ ghi. Đề tài ký G4 đúng quy trình
vẫn bị G6 từ chối, chỉ chạy được nhờ cờ `--i-confirm-sap-locked`; diễn tập C1a 16/10 truyền sẵn cờ nên che lỗi.
Bốn bản template `_check_sap_db_locked` mà `run_g6_auto.py` sinh ra cho bác sĩ chạy tay mang đúng lỗi đó.

Sau vá: «G4 đã khoá» = `g6_quality_gate._g4_da_khoa` (CÙNG hàm cổng G6 dùng: chữ ký sổ cái đúng vai khớp băm SAP HIỆN
TẠI + G4 chấm trực tiếp PASS_G4_SAP_LOCKED — `gate_contract.g4_quality_contract_satisfied`, cũng là hàm G5-AUTO-05
dùng).
Bốn hành vi được khoá:
  (a) G4 ký hợp lệ (chuỗi THẬT G0→G5, khoá giả của pytest) ⇒ G6 chạy KHÔNG cần cờ, dù checkpoint không có
      g4_status LOCKED;
  (b) G4 chưa ký ⇒ từ chối, có cờ cũng từ chối (cờ không thay chữ ký);
  (c) sửa SAP sau khi ký (lệch băm) ⇒ từ chối, có cờ cũng từ chối;
  (d) cờ ghi đè vẫn hoạt động khi chữ ký khớp băm nhưng chấm sống G4 không đạt — và được GHI NHẬN (in + summary JSON);
cùng: «không đo được» ⇒ từ chối (fail-closed), và template sinh ra không còn dòng thi hành đọc g4_status.

Ở (b)/(c)/(d) G5 được cô lập (G5 chấm sống thật cũng đòi G4 khoá ở G5-AUTO-05, nên không cô lập thì lượt bị chặn ở G5 và
phép thử không chứng minh được nhánh G4). Mọi chữ ký dùng khoá GIẢ trong tmp_path — không bao giờ chạm khoá thật; không
ghi vào exports/ thật. Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("pandas")
pytest.importorskip("statsmodels")

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g6_auto as G6A  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

from tests._chuoi_da_chot import (  # noqa: E402
    dien_sap_g4,
    dung_g0_g3_da_chot,
    sinh_sap_g4_that,
    xac_nhan_g4,
)
from tests.g5_test_helpers import configure_test_signing_key, prepare_locked_g5_study  # noqa: E402

STUDY = "N1-G6-rct"
DUNG_G4 = "DỪNG: G4 (SAP) hoặc G5"


class _QuaCong(Exception):
    """Lính canh: lượt chạy đã QUA cổng G2/G4/G5 (tới bước kiểm dữ liệu khoá)."""


def _nguon(p: Path) -> Path:
    dong = ["record_id,age,sex,exposure_var,primary_outcome"]
    for i in range(1, 61):
        nhom = i % 2
        kq = 1 if (7 * i + 3 * nhom) % 5 < 2 else 0
        dong.append(f"S{i:03d},{40 + (13 * i) % 40},{'F' if i % 3 else 'M'},{nhom},{kq}")
    p.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return p


@pytest.fixture()
def de_tai_khoa(tmp_path, monkeypatch):
    """Đề tài RCT đi CHUỖI THẬT G0→G5: G2/G4/G5 ký bằng khoá giả, dữ liệu đã khoá. RSA.BASE trỏ vào gốc tạm."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    out = goc / "exports" / STUDY
    out.mkdir(parents=True)
    (out / "G1_checkpoint.json").write_text(json.dumps({"design_code": "rct"}), encoding="utf-8", newline="\n")
    locked_path, _ = prepare_locked_g5_study(STUDY, _nguon(goc / "nguon.csv"), exports_root=goc / "exports",
                                             repo_root=goc)
    CS.xoa_dem()
    monkeypatch.setattr(RSA, "BASE", goc)
    return goc, out, locked_path


@pytest.fixture()
def de_tai_g4_chua_ky(tmp_path, monkeypatch):
    """Chuỗi THẬT G0→G3 đã chốt + SAP sinh THẬT bằng run_g4_auto, điền và xác nhận như người thật — nhưng CHƯA ký."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    out = goc / "exports" / STUDY
    out.mkdir(parents=True)
    dung_g0_g3_da_chot(out, STUDY, thiet_ke="rct")
    sap = sinh_sap_g4_that(out, STUDY)
    text = dien_sap_g4(sap.read_text(encoding="utf-8"))
    sap.write_text(text, encoding="utf-8", newline="\n")
    xac_nhan_g4(out, text)
    CS.xoa_dem()
    monkeypatch.setattr(RSA, "BASE", goc)
    return goc, out


def _co_lap_g5(monkeypatch) -> None:
    """G5 chấm sống coi như LOCKED — để lượt chạy tới đúng nhánh quyết định G4 (G5 thật cũng đòi G4 khoá)."""
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def _co_lap_g2_g5_khong_so_cai(monkeypatch) -> None:
    """Đề tài chỉ có G0–G4 (chưa ký G4): G2/G5 coi như đã khoá + ký; G4 giữ NGUYÊN đường thật (sổ cái, chấm sống)."""
    _co_lap_g5(monkeypatch)
    nap_goc = RSA._load_checkpoint
    so_cai_goc = RSA._ledger_approved
    monkeypatch.setattr(RSA, "_load_checkpoint",
                        lambda study, gate: {"G2": {"g2_status": "LOCKED"}, "G5": {"g5_status": "LOCKED"}}.get(
                            gate) or nap_goc(study, gate))
    monkeypatch.setattr(RSA, "_ledger_approved",
                        lambda study, gate_id, p: True if gate_id in ("G2", "G5") else so_cai_goc(study, gate_id, p))
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)


def _chan_sau_cong(monkeypatch) -> None:
    def _linh_canh(study, data):
        raise _QuaCong()

    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", _linh_canh)


def _chay(monkeypatch, data: Path | str, *them: str):
    """Gọi run_stats_analysis.main() trong tiến trình; trả (kết_cục, stdout, summary).

    kết_cục: 'XONG' (chạy hết) | 'QUA_CONG' (tới lính canh sau cổng) | mã thoát SystemExit."""
    argv = ["run_stats_analysis.py", "--study", STUDY, "--data", str(data), "--outcome", "primary_outcome",
            "--group", "exposure_var", "--covariates", "age", "--outcome-type", "binary", "--n-imputations", "2",
            *them]
    monkeypatch.setattr(sys, "argv", argv)
    CS.xoa_dem()
    buf = io.StringIO()
    tom = None
    with contextlib.redirect_stdout(buf):
        try:
            tom = RSA.main()
            ket = "XONG"
        except _QuaCong:
            ket = "QUA_CONG"
        except SystemExit as exc:
            ket = exc.code
    return ket, buf.getvalue(), tom


# ── (a) G4 ký hợp lệ ⇒ G6 chạy KHÔNG cần cờ ─────────────────────────────────────────────────────────────────────────
def test_a_g4_ky_hop_le_g6_chay_khong_can_co(de_tai_khoa, monkeypatch):
    goc, out, locked_path = de_tai_khoa
    cp4 = json.loads((out / "G4_checkpoint.json").read_text(encoding="utf-8"))
    # Tiền điều kiện của lỗi N1: checkpoint KHÔNG mang g4_status LOCKED (approve_gate không ghi) ⇒ bản cũ từ chối.
    assert not RSA._is_locked(cp4.get("g4_status", cp4.get("G4_STATUS"))), cp4.get("g4_status")
    ok, nguon = RSA._g4_khoa_song(STUDY)
    assert ok is True, nguon

    ket, stdout, tom = _chay(monkeypatch, locked_path)
    assert ket == "XONG", stdout[-3000:]
    assert DUNG_G4 not in stdout and "DỪNG: G2" not in stdout
    assert "G4 đã khoá theo trạng thái sống" in stdout
    assert "GHI ĐÈ CÓ CHỦ Ý" not in stdout
    k4 = tom["khoa_g4"]
    assert k4["trang_thai_song"] is True and k4["so_cai_khop_sap"] is True
    assert k4["ghi_de_i_confirm_sap_locked"] is False and k4["co_truyen_i_confirm_sap_locked"] is False
    tren_dia = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tren_dia["khoa_g4"] == k4


# ── (b) G4 chưa ký ⇒ từ chối (cả khi có cờ) ─────────────────────────────────────────────────────────────────────────
def test_b_g4_chua_ky_bi_tu_choi_ke_ca_co_co(de_tai_g4_chua_ky, monkeypatch):
    _co_lap_g2_g5_khong_so_cai(monkeypatch)
    _chan_sau_cong(monkeypatch)
    ok, nguon = RSA._g4_khoa_song(STUDY)
    assert ok is False and "sổ cái" in nguon, nguon
    for them in ((), ("--i-confirm-sap-locked",)):
        ket, stdout, _ = _chay(monkeypatch, "khong-dung.csv", *them)
        assert ket == 1, (them, ket, stdout[-2000:])
        assert DUNG_G4 in stdout, stdout[-2000:]
        assert "G4 trạng thái sống: ⚠️" in stdout
        assert "approval_ledger (chữ ký thật): ⚠️ thiếu/không khớp" in stdout


# ── (c) sửa SAP sau khi ký (lệch băm) ⇒ từ chối (cả khi có cờ) ─────────────────────────────────────────────────────
def test_c_sua_sap_sau_khi_ky_bi_tu_choi_ke_ca_co_co(de_tai_khoa, monkeypatch):
    goc, out, locked_path = de_tai_khoa
    assert RSA._g4_khoa_song(STUDY)[0] is True  # mẫu lành: đã khoá — không có nó phép sửa SAP không chứng minh gì
    sap = out / f"G4_A5_SAP_FINAL_{STUDY}.md"
    sap.write_text(sap.read_text(encoding="utf-8") + "\nDòng thêm SAU khi đã ký.\n", encoding="utf-8", newline="\n")
    CS.xoa_dem()
    assert RSA._g4_khoa_song(STUDY)[0] is False
    _co_lap_g5(monkeypatch)
    _chan_sau_cong(monkeypatch)
    for them in ((), ("--i-confirm-sap-locked",)):
        ket, stdout, _ = _chay(monkeypatch, locked_path, *them)
        assert ket == 1, (them, ket, stdout[-2000:])
        assert DUNG_G4 in stdout and "DỪNG: G2" not in stdout, stdout[-2000:]
        assert "approval_ledger (chữ ký thật): ⚠️ thiếu/không khớp" in stdout


# ── (d) cờ ghi đè vẫn hoạt động và được ghi nhận ───────────────────────────────────────────────────────────────────
def test_d_co_ghi_de_van_hoat_dong_va_duoc_ghi_nhan(de_tai_khoa, monkeypatch):
    goc, out, locked_path = de_tai_khoa
    # Chữ ký G4 vẫn khớp băm SAP hiện tại, nhưng chấm sống G4 không đạt (vd luật mới/G3 trôi) ⇒ đường thường từ chối.
    monkeypatch.setattr(GC, "g4_quality_contract_satisfied", lambda *a, **k: False)
    _co_lap_g5(monkeypatch)
    ok, nguon = RSA._g4_khoa_song(STUDY)
    assert ok is False and "PASS_G4_SAP_LOCKED" in nguon, nguon

    ket, stdout, _ = _chay(monkeypatch, locked_path)
    assert ket == 1 and DUNG_G4 in stdout, stdout[-2000:]

    ket, stdout, tom = _chay(monkeypatch, locked_path, "--i-confirm-sap-locked")
    assert ket == "XONG", stdout[-3000:]
    assert "GHI ĐÈ CÓ CHỦ Ý (--i-confirm-sap-locked)" in stdout
    k4 = tom["khoa_g4"]
    assert k4["ghi_de_i_confirm_sap_locked"] is True and k4["trang_thai_song"] is False
    assert k4["so_cai_khop_sap"] is True and k4["co_truyen_i_confirm_sap_locked"] is True
    tren_dia = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tren_dia["khoa_g4"]["ghi_de_i_confirm_sap_locked"] is True


def test_co_khong_can_khi_g4_da_khoa_song_thi_khong_tinh_la_ghi_de(de_tai_khoa, monkeypatch):
    """Truyền cờ cho một G4 đã khoá sống: không tính là ghi đè (khoá «ghi_de» chỉ bật khi cờ thật sự mở cổng)."""
    goc, out, locked_path = de_tai_khoa
    _chan_sau_cong(monkeypatch)
    ket, stdout, _ = _chay(monkeypatch, locked_path, "--i-confirm-sap-locked")
    assert ket == "QUA_CONG", stdout[-2000:]
    assert "GHI ĐÈ CÓ CHỦ Ý" not in stdout
    assert "KHÔNG cần cho G4" in stdout


# ── «Không đo được» ⇒ từ chối (fail-closed) ───────────────────────────────────────────────────────────────────────
def test_khong_do_duoc_trang_thai_g4_thi_tu_choi(de_tai_khoa, monkeypatch):
    goc, out, locked_path = de_tai_khoa
    _co_lap_g5(monkeypatch)
    _chan_sau_cong(monkeypatch)

    def _hong(*a, **k):
        raise RuntimeError("bộ chấm G4 hỏng giữa chừng")

    # Tầng 1: hàm cổng G6 tự nuốt lỗi bộ chấm ⇒ «không đo được», không phải «đã khoá».
    monkeypatch.setattr(GC, "g4_quality_contract_satisfied", _hong)
    ok, nguon = RSA._g4_khoa_song(STUDY)
    assert ok is False and "không đo được" in nguon, nguon
    ket, stdout, _ = _chay(monkeypatch, locked_path)
    assert ket == 1 and DUNG_G4 in stdout and "không đo được" in stdout, stdout[-2000:]

    # Tầng 2: chính hàm đo ném lỗi ⇒ vẫn từ chối.
    monkeypatch.setattr(RSA.G6Q, "_g4_da_khoa", _hong)
    ok, nguon = RSA._g4_khoa_song(STUDY)
    assert ok is False and nguon == "không đo được (RuntimeError)", nguon
    ket, stdout, _ = _chay(monkeypatch, locked_path)
    assert ket == 1 and DUNG_G4 in stdout, stdout[-2000:]


def test_g4_khoa_song_chi_nhan_dung_true(monkeypatch):
    """Giá trị truthy khác True (chuỗi «LOCKED», 1) không phải «đã khoá»."""
    for gia_tri in ("LOCKED", 1, "True"):
        monkeypatch.setattr(RSA.G6Q, "_g4_da_khoa", lambda *a, _g=gia_tri, **k: (_g, "giả"))
        assert RSA._g4_khoa_song("S")[0] is False, gia_tri


# ── Template run_g6_auto (script bác sĩ chạy tay) — cùng luật ─────────────────────────────────────────────────────
_V = {"exposure": "arm", "outcome": "outcome", "time_col": "fu", "covariates": ["age"], "detection_log": []}


@pytest.mark.parametrize("ten,sinh", [
    ("cli_cohort", lambda: G6A.make_run_analysis_cli(_V, 60, "TEST-STUDY", "cohort", "HR")),
    ("cli_case_control", lambda: G6A.make_run_analysis_cli(_V, 60, "TEST-STUDY", "case_control", "OR")),
    ("sens_cohort", lambda: G6A.make_sensitivity_analysis(_V, "TEST-STUDY", "cohort")),
    ("sens_case_control", lambda: G6A.make_sensitivity_analysis(_V, "TEST-STUDY", "case_control")),
])
def test_template_g6_doc_trang_thai_song_g4_khong_doc_g4_status(ten, sinh):
    code = sinh()
    compile(code, ten, "exec")
    thi_hanh = [d.strip() for d in code.splitlines() if d.strip() and not d.strip().startswith("#")]
    assert not [d for d in thi_hanh if "g4_status" in d or "G4_STATUS" in d], ten
    assert any("g4_quality_contract_satisfied(" in d for d in thi_hanh), ten
    assert "g4_locked = (g4_song or i_confirm_sap) and g4_ledger" in code, ten
    assert any(d.startswith("g4_song = False") for d in thi_hanh), f"{ten}: thiếu nhánh «không đo được ⇒ chưa khoá»"


# ── Template: HÀNH VI của phần chấm sống G4 (không chỉ văn bản) ────────────────────────────────────────────────────
# Sửa sau thẩm định PR #255 (15/11/2026): test văn bản ở trên để lọt đột biến đổi `... is True` thành
# `... is not None` (script sinh ra coi «không khoá» là khoá — fail-open). Các test dưới THI HÀNH đúng hàm
# `_check_sap_db_locked` của mã sinh ra (bóc bằng ast), với `gate_contract` GIẢ qua sys.modules, cwd = tmp_path
# (không chạm exports/ thật, không dùng khoá).
_TEMPLATES = [
    ("cli_cohort", lambda: G6A.make_run_analysis_cli(_V, 60, "TEST-STUDY", "cohort", "HR")),
    ("cli_case_control", lambda: G6A.make_run_analysis_cli(_V, 60, "TEST-STUDY", "case_control", "OR")),
    ("sens_cohort", lambda: G6A.make_sensitivity_analysis(_V, "TEST-STUDY", "cohort")),
    ("sens_case_control", lambda: G6A.make_sensitivity_analysis(_V, "TEST-STUDY", "case_control")),
]
_GHI_DE = ("GHI ĐÈ CÓ CHỦ Ý", "GHI DE CO CHU Y")  # CLI in có dấu, bản sensitivity in không dấu


def _ham_kiem_cong_cua_template(code: str, tmp_path: Path, monkeypatch, g4_song, g4_so_cai: bool = True):
    """Trả về hàm `_check_sap_db_locked` THẬT của script sinh ra, nối với gate_contract giả.

    g4_song: giá trị `g4_quality_contract_satisfied` trả về, hoặc một Exception để mô phỏng «không đo được».
    G2/G5 cho đạt (checkpoint LOCKED + sổ cái + chấm) để phép thử cô lập đúng nhánh G4.
    """
    import ast
    import types

    cay = ast.parse(code)
    ham = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_check_sap_db_locked"]
    assert len(ham) == 1, "template phải có đúng một _check_sap_db_locked ở cấp module"
    nguon = ast.get_source_segment(code, ham[0])

    def _g4(study):
        if isinstance(g4_song, Exception):
            raise g4_song
        return g4_song

    gia = types.ModuleType("gate_contract")
    gia.g4_quality_contract_satisfied = _g4
    gia.ledger_approved = lambda gate, *a, **k: g4_so_cai if gate == "G4" else True
    gia.g2_quality_contract_satisfied = lambda *a, **k: True
    gia.g5_quality_contract_satisfied = lambda *a, **k: True
    gia.load_study_meta = lambda *a, **k: {}
    monkeypatch.setitem(sys.modules, "gate_contract", gia)
    monkeypatch.setattr(sys, "path", list(sys.path))  # hàm tự chèn đường dẫn tools/ — trả lại sau test

    d = tmp_path / "exports" / "TEST-STUDY"
    d.mkdir(parents=True)
    (d / "G2_checkpoint.json").write_text('{"g2_status": "LOCKED"}', encoding="utf-8", newline="\n")
    (d / "G5_checkpoint.json").write_text('{"g5_status": "LOCKED"}', encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    ns = {"Path": Path, "sys": sys, "__name__": "template_g6_test",
          "__file__": str(tmp_path / "a" / "b" / "c" / "scripts" / "run_analysis_cli.py")}
    exec(compile(nguon, "<template-g6:_check_sap_db_locked>", "exec"), ns)  # noqa: S102 — mã do run_g6_auto sinh
    return ns["_check_sap_db_locked"]


@pytest.mark.parametrize("ten,sinh", _TEMPLATES)
def test_template_g4_chua_khoa_song_khong_co_thi_dung(ten, sinh, tmp_path, monkeypatch, capsys):
    kiem = _ham_kiem_cong_cua_template(sinh(), tmp_path, monkeypatch, g4_song=False)
    with pytest.raises(SystemExit):
        kiem(False, False)
    ra = capsys.readouterr().out  # đọc MỘT lần — readouterr() xoá bộ đệm
    assert not any(c in ra for c in _GHI_DE), ten


@pytest.mark.parametrize("ten,sinh", _TEMPLATES)
def test_template_g4_chua_khoa_song_co_co_thi_ghi_de_co_chu_y(ten, sinh, tmp_path, monkeypatch, capsys):
    kiem = _ham_kiem_cong_cua_template(sinh(), tmp_path, monkeypatch, g4_song=False)
    kiem(True, False)  # chữ ký sổ cái G4 khớp ⇒ cờ được phép ghi đè phần chấm sống — và phải in rõ
    ra = capsys.readouterr().out  # đọc MỘT lần — readouterr() xoá bộ đệm
    assert any(c in ra for c in _GHI_DE), ten


@pytest.mark.parametrize("ten,sinh", _TEMPLATES)
def test_template_g4_khoa_song_khong_can_co_khong_ghi_de(ten, sinh, tmp_path, monkeypatch, capsys):
    kiem = _ham_kiem_cong_cua_template(sinh(), tmp_path, monkeypatch, g4_song=True)
    kiem(False, False)
    ra = capsys.readouterr().out  # đọc MỘT lần — readouterr() xoá bộ đệm
    assert not any(c in ra for c in _GHI_DE), ten


@pytest.mark.parametrize("ten,sinh", _TEMPLATES)
@pytest.mark.parametrize("gia_tri", [RuntimeError("không đo được"), "LOCKED", 1, None])
def test_template_g4_khong_do_duoc_hoac_khong_dung_true_thi_dung(ten, sinh, gia_tri, tmp_path, monkeypatch):
    kiem = _ham_kiem_cong_cua_template(sinh(), tmp_path, monkeypatch, g4_song=gia_tri)
    with pytest.raises(SystemExit):
        kiem(False, False)


@pytest.mark.parametrize("ten,sinh", _TEMPLATES)
def test_template_co_khong_thay_duoc_so_cai_g4(ten, sinh, tmp_path, monkeypatch):
    kiem = _ham_kiem_cong_cua_template(sinh(), tmp_path, monkeypatch, g4_song=True, g4_so_cai=False)
    with pytest.raises(SystemExit):
        kiem(True, True)
