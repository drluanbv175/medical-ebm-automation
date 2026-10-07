"""07/10/2026 — bác sĩ yêu cầu giải quyết hai việc treo:

1. THU HẸP NHÁNH TƯƠNG THÍCH G2 KIỂU CŨ (gate_contract.g2_quality_contract_satisfied): gói G2 KHÔNG có attestation
   chỉ còn được xét theo checkpoint (không ký) khi phê duyệt G2 có thẩm quyền KÝ TRƯỚC mốc hợp đồng G2-2026.1
   (G2_MOC_HOP_DONG_PHIEN_BAN — mốc lấy từ bản ghi sổ cái ĐÃ KÝ). Ký sau mốc mà không attestation ⇒ CHẶN.
2. Hai việc của đợt khoá giả pytest 05/10:
   (a) gate_contract BÁO LỖI (KhoaThatKhiKiemThuError) khi đang kiểm thử mà đường dẫn khoá ký trỏ vào thư mục bí mật
       THẬT — trước đây thiếu EBM_GATE_KEY_PATH là lặng lẽ dùng khoá riêng của bác sĩ;
   (b) app/config (và hai công cụ tự đọc kho) KHÔNG nạp kho secrets khi đang kiểm thử ⇒ chốt canh bỏ miễn trừ đọc.

Mọi đề tài dựng trong tmp_path, ký bằng khoá GIẢ của conftest; không đụng exports/ thật, không mở tệp bí mật thật.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402

from tests import g5_test_helpers as H  # noqa: E402
from tests._chuoi_da_chot import dung_g0_g3_da_chot  # noqa: E402

STUDY = "PYTEST-THU-HEP-G2-20261007"
TRUOC_MOC = "2026-07-20T08:00:00+00:00"
CP_CU = {"g2_status": "LOCKED"}
CP_HIEN_DAI = {"quality_contract_version": "G2-2026.1", "quality_gate": {"status": "PASS_G2_APPROVED"},
               "g2_approval_valid_until": "2099-12-31"}


def _de_tai_goi_khong_attestation(tmp_path: Path, ky_luc=None) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    goi = out / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md"
    goi.write_text("# Hồ sơ đạo đức (chưa có attestation)\n", encoding="utf-8", newline="\n")
    H.append_signed_approval(STUDY, goi, "G2", "IRB_ETHICS_COMMITTEE", repo_root=tmp_path, timestamp_utc=ky_luc)
    return out


def _ok(cp, out) -> bool:
    return GC.g2_quality_contract_satisfied(cp, {}, study=STUDY, out_dir=out)


# ── 1. Thu hẹp nhánh tương thích G2 kiểu cũ ──────────────────────────────────────────────────────────────────────────

def test_moc_la_commit_hop_dong_g2_phien_ban():
    """Mốc = commit 64b278f đưa G2-2026.1 + attestation vào nhánh làm việc (2026-07-28 17:47:50 +07:00)."""
    assert GC.G2_MOC_HOP_DONG_PHIEN_BAN.isoformat() == "2026-07-28T10:47:50+00:00"


def test_goi_khong_attestation_ky_sau_moc_khong_con_duoc_nhan(tmp_path):
    out = _de_tai_goi_khong_attestation(tmp_path)  # ký «bây giờ»
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is False
    for cp in (CP_CU, {}, CP_HIEN_DAI):  # kể cả checkpoint hiện đại tự ghi PASS — checkpoint không ký
        assert _ok(cp, out) is False, cp


def test_goi_khong_attestation_ky_truoc_moc_giu_nhanh_cu_khong_noi_them(tmp_path):
    out = _de_tai_goi_khong_attestation(tmp_path, ky_luc=TRUOC_MOC)
    assert GC.ledger_approved("G2", STUDY, out / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md", repo_root=tmp_path) is True
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is True
    assert _ok(CP_CU, out) is True
    assert _ok(CP_HIEN_DAI, out) is True
    # nhánh cũ vẫn giữ mọi phép kiểm checkpoint có version (hết hạn ⇒ chặn) — không nới thêm
    assert _ok(dict(CP_HIEN_DAI, g2_approval_valid_until="2020-01-01"), out) is False


def test_ky_dung_moc_tinh_la_sau_moc(tmp_path):
    out = _de_tai_goi_khong_attestation(tmp_path, ky_luc=GC.G2_MOC_HOP_DONG_PHIEN_BAN.isoformat())
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is False
    assert _ok(CP_CU, out) is False


def test_lui_ngay_ky_bang_tay_pha_chu_ky_khong_mo_nhanh_cu(tmp_path):
    """timestamp_utc nằm trong nội dung ký: sửa tay về trước mốc ⇒ chữ ký hỏng ⇒ bất thường ⇒ không có mốc ký."""
    out = _de_tai_goi_khong_attestation(tmp_path)
    so_cai = out / "approval_ledger.json"
    ban_ghi = json.loads(so_cai.read_text(encoding="utf-8"))
    ban_ghi[-1]["timestamp_utc"] = TRUOC_MOC
    so_cai.write_text(json.dumps(ban_ghi, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is False
    assert _ok(CP_CU, out) is False


def test_khong_so_cai_hoac_khong_truyen_de_tai_thi_chan(tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text("# Hồ sơ\n", encoding="utf-8", newline="\n")
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is False
    assert _ok(CP_CU, out) is False
    # không truyền study/out_dir ⇒ không đọc được attestation lẫn mốc ký ⇒ chặn (mọi nơi gọi trong tools đều truyền)
    assert GC.g2_quality_contract_satisfied(CP_CU, {}) is False
    assert GC.g2_quality_contract_satisfied(CP_HIEN_DAI, {}) is False


@pytest.mark.parametrize("thiet_ke", ["rct", "sr_ma", "cohort", "qualitative"])
def test_do_ga_g2_hien_dai_qua_hop_dong_bang_attestation(tmp_path, thiet_ke):
    """Đồ gá dùng chung (prepare_upstream_approvals) dựng G2 bằng attestation của lệnh ký thật — đạt hợp đồng nhờ
    attestation (không nhờ nhánh cũ), hợp lệ theo từng thiết kế (RCT/SR-MA bắt đăng ký)."""
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    dung_g0_g3_da_chot(out, STUDY, thiet_ke=thiet_ke)
    goi = H.ky_g2_hien_dai(STUDY, out, repo_root=tmp_path)
    assert GC._g2_signed_attestation_state(STUDY, out, None) is True
    assert GC.ledger_approved("G2", STUDY, goi, repo_root=tmp_path) is True
    cp = json.loads((out / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert GC.g2_quality_contract_satisfied(cp, GC.load_study_meta(out), study=STUDY, out_dir=out) is True
    assert GC.g2_ky_truoc_moc_hop_dong(STUDY, out) is False  # ký «bây giờ»: đạt nhờ attestation, không nhờ mốc


# ── 2a. gate_contract báo lỗi khi khoá ký trỏ vào thư mục bí mật THẬT lúc kiểm thử ────────────────────────────────

def test_thieu_bien_khoa_khi_kiem_thu_bao_loi_khong_roi_ve_khoa_that(monkeypatch):
    monkeypatch.delenv(GC._SIGNING_KEY_ENV, raising=False)
    for ham in (GC._base_key_path, GC._ed_private_dir, lambda: GC.signing_key_path("IRB"),
                lambda: GC.signing_key_configured(None), lambda: GC.ed25519_private_key_available("IRB")):
        with pytest.raises(GC.KhoaThatKhiKiemThuError):
            ham()


def test_rao_loi_mat_ma_khong_nuot_chot_khoa_that(monkeypatch):
    """_load_ed_private bọc `except BaseException` (BH99-A) — chốt «khoá THẬT khi kiểm thử» phải xuyên qua rào đó."""
    pytest.importorskip("cryptography")
    monkeypatch.delenv(GC._SIGNING_KEY_ENV, raising=False)
    with pytest.raises(GC.KhoaThatKhiKiemThuError):
        GC._load_ed_private("IRB")


def test_bien_khoa_tro_vao_kho_that_cung_bao_loi(monkeypatch):
    monkeypatch.setenv(GC._SIGNING_KEY_ENV, str(GC._THU_MUC_BI_MAT_THAT / "gate_approval_key"))
    with pytest.raises(GC.KhoaThatKhiKiemThuError):
        GC._base_key_path()
    with pytest.raises(GC.KhoaThatKhiKiemThuError):
        GC._ed_private_dir()


def test_khoa_gia_cua_conftest_khong_bi_chan():
    assert not GC._nam_trong(GC._base_key_path(), GC._THU_MUC_BI_MAT_THAT)
    assert not GC._nam_trong(GC._ed_private_dir(), GC._THU_MUC_BI_MAT_THAT)


def test_gia_lap_van_hanh_that_thi_chot_nhuong(monkeypatch):
    """Ngoài pytest mọi hành vi giữ nguyên (khoá mặc định ~/.ebm-secrets) — chỉ so đường dẫn, không đọc khoá."""
    monkeypatch.setattr(GC, "_test_context_active", lambda: False)
    monkeypatch.delenv(GC._SIGNING_KEY_ENV, raising=False)
    assert GC._base_key_path() == GC._DEFAULT_KEY_PATH
    assert GC._ed_private_dir() == GC._ED_PRIVATE_DIR


def test_tien_trinh_con_ke_thua_pytest_ma_mat_bien_khoa_thi_bao_loi(tmp_path):
    """Lỗ móc audit của conftest không thấy: tiến trình con kế thừa PYTEST_CURRENT_TEST nhưng mất EBM_GATE_KEY_PATH."""
    env = {k: v for k, v in os.environ.items() if k != GC._SIGNING_KEY_ENV}
    env["PYTEST_CURRENT_TEST"] = "tien-trinh-con"
    kq = subprocess.run([sys.executable, "-B", "-c",
                         "import sys; sys.path.insert(0, 'tools'); import gate_contract as GC; GC._base_key_path()"],
                        cwd=REPO_ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert kq.returncode != 0 and "KhoaThatKhiKiemThuError" in kq.stderr, kq.stderr


# ── 2b. Không nạp kho secrets khi kiểm thử ───────────────────────────────────────────────────────────────────────────

def test_app_config_khong_nap_tep_moi_truong_khi_kiem_thu():
    import app.config as CFG

    assert CFG.dang_chay_kiem_thu() is True
    assert CFG.NAP_TEP_MOI_TRUONG is False and CFG.TEP_DA_NAP == []
    goi = []
    assert CFG._nap_tep_moi_truong(True, nap=goi.append) == [] and goi == []


def test_lan_chay_that_van_nap_kho_secrets_roi_env_repo(tmp_path, monkeypatch):
    """Thứ tự nạp của lần chạy THẬT giữ nguyên — kiểm bằng bộ nạp giả, không mở tệp thật nào."""
    import app.config as CFG

    kho_gia = tmp_path / "medical-ebm-automation.env"
    kho_gia.write_text("X=1\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(CFG, "_SECRETS_ENV", kho_gia)
    goi = []
    assert CFG._nap_tep_moi_truong(False, nap=goi.append) == [kho_gia, CFG.BASE_DIR / ".env"]
    assert goi == [kho_gia, CFG.BASE_DIR / ".env"]


def test_tien_trinh_con_ke_thua_pytest_khong_nap_tep_moi_truong():
    env = dict(os.environ, PYTEST_CURRENT_TEST="tien-trinh-con")
    kq = subprocess.run([sys.executable, "-B", "-c",
                         "import app.config as C; print(C.NAP_TEP_MOI_TRUONG, len(C.TEP_DA_NAP))"],
                        cwd=REPO_ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert kq.returncode == 0 and kq.stdout.strip() == "False 0", kq.stdout + kq.stderr


def test_hai_cong_cu_tu_doc_kho_khong_doc_khi_kiem_thu(tmp_path, monkeypatch):
    """HOME trỏ vào thư mục tạm CÓ kho giả mang email — dưới pytest hai công cụ vẫn KHÔNG đọc (trả rỗng). Kho thật
    không bị chạm: chốt canh conftest đánh ĐỎ test này nếu tệp trong ~/.ebm-secrets thật bị mở."""
    import gom_toan_van_oa as GOM
    import tai_retraction_watch as TRW

    (tmp_path / ".ebm-secrets").mkdir()
    (tmp_path / ".ebm-secrets" / "medical-ebm-automation.env").write_text(
        "NCBI_EMAIL=gia@example.org\nOPENALEX_EMAIL=gia@example.org\n", encoding="utf-8", newline="\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for ten in ("NCBI_EMAIL", "OPENALEX_EMAIL", "UNPAYWALL_EMAIL"):
        monkeypatch.delenv(ten, raising=False)
    assert GOM._email_lien_he() == ""
    assert TRW._email() == ""


def test_gom_toan_van_oa_lan_chay_that_van_doc_kho(tmp_path):
    """Ngoài kiểm thử (không PYTEST_CURRENT_TEST, không import pytest) công cụ vẫn đọc email từ kho — HOME GIẢ."""
    nha = tmp_path / "nha"
    (nha / ".ebm-secrets").mkdir(parents=True)
    (nha / ".ebm-secrets" / "medical-ebm-automation.env").write_text("NCBI_EMAIL=gia@example.org\n",
                                                                       encoding="utf-8", newline="\n")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_CURRENT_TEST", "NCBI_EMAIL")}
    env.update(HOME=str(nha), USERPROFILE=str(nha))
    kq = subprocess.run([sys.executable, "-B", "-c",
                         "import sys; sys.path.insert(0, 'tools'); import gom_toan_van_oa as G; print(G.MAILTO)"],
                        cwd=REPO_ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert kq.returncode == 0 and kq.stdout.strip() == "gia@example.org", kq.stdout + kq.stderr
