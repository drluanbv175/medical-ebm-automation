"""Cầu nối hook «một cửa vào» cho phiên mở trong repo y khoa (29/10/2026).

Lỗ hổng đo được 29/10: hook UserPromptSubmit nhắc định tuyến (BH172) chỉ khai ở `.claude/settings.json` của repo GỐC;
Claude Code không đọc settings của thư mục cha ⇒ phiên mở trong `medical-ebm-automation/` (hay worktree của nó) không
có hook. Các ca dưới dựng một repo gốc GIẢ (hook gốc giả in lại câu bác sĩ gõ) để kiểm cầu nối tìm đúng repo gốc ở mọi
bố cục, chuyển nguyên dữ liệu hook, và im lặng mã 0 khi không tìm thấy/có lỗi. Ca cuối chạy với repo gốc THẬT khi
máy có.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CAU_NOI = REPO / "tools" / "nhac_dinh_tuyen_cau_noi.py"
CAU_CHU_DE = ("Tiếp cận chẩn đoán điều trị,tiên lương suy tim một cách toàn diện dựa trên chứng cứ mới nhất "
              "và độ tin cậy cao nhất")

# Hook gốc GIẢ: in lại câu bác sĩ gõ và thư mục chạy để ca kiểm biết chắc ĐÚNG repo gốc nào đã được gọi.
HOOK_GIA = """import json, os, sys
du_lieu = json.loads(sys.stdin.read() or "{}")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
      "additionalContext": "GIA|" + du_lieu.get("prompt", "") + "|" + os.getcwd()}}, ensure_ascii=False))
"""


def _ghi(p: Path, noi_dung: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(noi_dung, encoding="utf-8", newline="\n")
    return p


def _dung_goc(goc: Path, hook: str = HOOK_GIA, co_intent: bool = True) -> Path:
    _ghi(goc / "tools" / "nhac_dinh_tuyen.py", hook)
    if co_intent:
        _ghi(goc / "tools" / "orchestrator" / "intent.py", "")
    return goc


def _chep_cau_noi(du_an: Path) -> Path:
    (du_an / "tools").mkdir(parents=True, exist_ok=True)
    return Path(shutil.copy2(CAU_NOI, du_an / "tools" / CAU_NOI.name))


def _moi_truong(du_an: Path | None, goc_khai: Path | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("EBM_WORKSPACE_ROOT", "CLAUDE_PROJECT_DIR")}
    if du_an is not None:
        env["CLAUDE_PROJECT_DIR"] = str(du_an)
    if goc_khai is not None:
        env["EBM_WORKSPACE_ROOT"] = str(goc_khai)
    return env


def _chay(cau_noi: Path, du_an: Path | None, du_lieu: bytes | None = None, goc_khai: Path | None = None):
    if du_lieu is None:
        du_lieu = json.dumps({"prompt": CAU_CHU_DE}).encode("utf-8")
    return subprocess.run([sys.executable, str(cau_noi)], input=du_lieu, capture_output=True, timeout=30,
                          env=_moi_truong(du_an, goc_khai))


def _nap_cau_noi(monkeypatch):
    """Nạp cầu nối trong tiến trình (môi trường sạch) để gọi thẳng tim_goc()/main()."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.delenv("EBM_WORKSPACE_ROOT", raising=False)
    spec = importlib.util.spec_from_file_location("_cau_noi_trong_tien_trinh", CAU_NOI)
    cn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cn)
    return cn


def _loi_nhac(r) -> str:
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    if not r.stdout:
        return ""
    return json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]


# ── ① tìm repo gốc ở mọi bố cục ─────────────────────────────────────────────────────────────────────────────────────


def test_repo_y_khoa_nam_trong_repo_goc(tmp_path):
    goc = _dung_goc(tmp_path / "Claude AI")
    y_khoa = goc / "medical-ebm-automation"
    nhac = _loi_nhac(_chay(_chep_cau_noi(y_khoa), y_khoa))
    assert nhac == f"GIA|{CAU_CHU_DE}|{goc.resolve()}"


def test_worktree_long_trong_repo_y_khoa(tmp_path):
    goc = _dung_goc(tmp_path / "Claude AI")
    wt = goc / "medical-ebm-automation" / ".claude" / "worktrees" / "strange-turing"
    assert _loi_nhac(_chay(_chep_cau_noi(wt), wt)).startswith(f"GIA|{CAU_CHU_DE}|")


def test_worktree_ngoai_cay_tim_qua_checkout_chinh(tmp_path):
    """Worktree ở ~/.ebm-worktrees không nằm dưới repo gốc: phải lần `.git` → commondir → checkout chính rồi đi lên."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("máy không có git")
    goc = _dung_goc(tmp_path / "Claude AI")
    y_khoa = goc / "medical-ebm-automation"
    _ghi(y_khoa / "README.md", "x\n")

    def g(*args, cwd=y_khoa):
        subprocess.run([git, *args], cwd=cwd, check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t"})
    g("init", "-q")
    g("add", "README.md")
    g("-c", "commit.gpgsign=false", "commit", "-q", "--no-verify", "-m", "x")
    wt = tmp_path / "ebm-worktrees" / "hook-mot-cua"
    g("worktree", "add", "-q", str(wt))
    assert (wt / ".git").is_file()
    nhac = _loi_nhac(_chay(_chep_cau_noi(wt), wt))
    assert nhac == f"GIA|{CAU_CHU_DE}|{goc.resolve()}"


def test_bien_moi_truong_khai_goc_thang_moi_cach_khac(tmp_path):
    goc_khai = _dung_goc(tmp_path / "goc-khai")
    goc_cha = _dung_goc(tmp_path / "goc-cha")
    y_khoa = goc_cha / "medical-ebm-automation"
    nhac = _loi_nhac(_chay(_chep_cau_noi(y_khoa), y_khoa, goc_khai=goc_khai))
    assert nhac.endswith(f"|{goc_khai.resolve()}")


def test_bien_moi_truong_khai_sai_thi_van_tu_tim(tmp_path):
    goc = _dung_goc(tmp_path / "Claude AI")
    y_khoa = goc / "medical-ebm-automation"
    nhac = _loi_nhac(_chay(_chep_cau_noi(y_khoa), y_khoa, goc_khai=tmp_path / "khong-ton-tai"))
    assert nhac.endswith(f"|{goc.resolve()}")


def test_thieu_claude_project_dir_van_tim_tu_vi_tri_tep(tmp_path):
    goc = _dung_goc(tmp_path / "Claude AI")
    y_khoa = goc / "medical-ebm-automation"
    assert _loi_nhac(_chay(_chep_cau_noi(y_khoa), None)).startswith("GIA|")


# ── ② im lặng, mã 0 khi không tìm thấy hoặc có lỗi ──────────────────────────────────────────────────────────────────


def test_khong_co_repo_goc_thi_im_lang(tmp_path):
    y_khoa = tmp_path / "chi-co-y-khoa"
    r = _chay(_chep_cau_noi(y_khoa), y_khoa)
    assert r.returncode == 0 and r.stdout == b""


def test_thieu_mot_dau_hieu_khong_coi_la_repo_goc(tmp_path):
    """Một tệp nhac_dinh_tuyen.py lạc chỗ (không có bộ định tuyến đi kèm) không phải repo gốc."""
    goc = _dung_goc(tmp_path / "Claude AI", co_intent=False)
    y_khoa = goc / "medical-ebm-automation"
    r = _chay(_chep_cau_noi(y_khoa), y_khoa)
    assert r.returncode == 0 and r.stdout == b""


def test_hook_goc_loi_thi_im_lang(tmp_path):
    goc = _dung_goc(tmp_path / "Claude AI", hook="print('nua chung')\nraise SystemExit(3)\n")
    y_khoa = goc / "medical-ebm-automation"
    r = _chay(_chep_cau_noi(y_khoa), y_khoa)
    assert r.returncode == 0 and r.stdout == b""


def test_loi_trong_cau_noi_thi_im_lang_ma_0(tmp_path, monkeypatch, capsysbinary):
    """Hook gốc treo quá hạn (hoặc bất kỳ lỗi nào trong cầu nối) ⇒ không ném lỗi ra lượt gõ của bác sĩ."""
    goc = _dung_goc(tmp_path / "Claude AI")
    cn = _nap_cau_noi(monkeypatch)
    monkeypatch.setenv("EBM_WORKSPACE_ROOT", str(goc))

    def _qua_han(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd="nhac_dinh_tuyen.py", timeout=cn.THOI_HAN_GIAY)
    monkeypatch.setattr(cn.subprocess, "run", _qua_han)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b'{"prompt": "x"}')))
    assert cn.main() == 0
    assert capsysbinary.readouterr().out == b""


@pytest.mark.parametrize("rac", [b"khong phai json", b"", b"\xff\xfe"])
def test_du_lieu_rac_chuyen_nguyen_va_khong_chan(tmp_path, rac):
    goc = _dung_goc(tmp_path / "Claude AI", hook="import sys\nd = sys.stdin.buffer.read()\nprint(len(d))\n")
    y_khoa = goc / "medical-ebm-automation"
    r = _chay(_chep_cau_noi(y_khoa), y_khoa, du_lieu=rac)
    assert r.returncode == 0 and r.stdout.strip() == str(len(rac)).encode()


# ── ③ lệnh khai trong settings.json đi qua git chạy THẬT ────────────────────────────────────────────────────────────


def _lenh_khai() -> str:
    cfg = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    lenh = [h["command"] for m in cfg["hooks"]["UserPromptSubmit"] for h in m["hooks"]]
    assert len(lenh) == 1, lenh
    assert "/Users/" not in lenh[0] and "C:\\" not in lenh[0], "lệnh hook không được mang đường dẫn riêng một máy"
    return lenh[0]


def _chay_lenh_khai(du_an: Path, cau: str, goc_khai: Path | None = None):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("máy không có bash — Claude Code chạy hook bằng bash")
    return subprocess.run([bash, "-c", _lenh_khai()], input=json.dumps({"prompt": cau}).encode("utf-8"),
                          capture_output=True, timeout=30, env=_moi_truong(du_an, goc_khai))


def test_lenh_khai_trong_settings_chay_ra_loi_nhac(tmp_path):
    """Chạy ĐÚNG lệnh đã khai (không chỉ tìm chuỗi): khai sai tên tệp thì hook im lặng mãi mà không ai biết (BH41)."""
    goc = _dung_goc(tmp_path / "Claude AI")
    y_khoa = goc / "medical-ebm-automation"
    _chep_cau_noi(y_khoa)
    assert _loi_nhac(_chay_lenh_khai(y_khoa, CAU_CHU_DE)).startswith(f"GIA|{CAU_CHU_DE}|")


def test_lenh_khai_khong_co_cau_noi_thi_im_lang(tmp_path):
    r = _chay_lenh_khai(tmp_path / "thu-muc-khac", CAU_CHU_DE)
    assert r.returncode == 0 and r.stdout == b""


# ── ④ với repo gốc THẬT (chỉ khi máy có — CI chỉ checkout repo y khoa thì bỏ qua) ───────────────────────────────────


def _goc_that(monkeypatch) -> Path | None:
    return _nap_cau_noi(monkeypatch).tim_goc()


@pytest.mark.parametrize("cau,dich", [
    (CAU_CHU_DE, "cap-nhat-chung-cu-y-khoa"),
    ("tôi có bệnh nhân nam 60 tuổi đau ngực", "dieu-phoi-lam-sang"),
    ("tính cỡ mẫu cho đề tài hài lòng người bệnh", None),
])
def test_repo_goc_that_nhac_dung_duong(cau, dich, monkeypatch):
    if _goc_that(monkeypatch) is None:
        pytest.skip("máy này không có repo gốc (CI chỉ checkout repo y khoa)")
    r = _chay_lenh_khai(REPO, cau)
    assert r.returncode == 0
    if dich is None:
        assert r.stdout == b""
    else:
        assert dich in r.stdout.decode("utf-8")
