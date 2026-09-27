"""Hồi quy #18 (26/09/2026): bản tin sáng phải đọc đúng hợp đồng daily_integrity.json.

JSON thật (research_automation.schedule_runner.JobReport) dùng ``ok: bool`` + ``findings``,
KHÔNG có ``status`` — mã cũ chỉ tìm ``status == "FAIL"`` nên lệch hash manifest không bao giờ
hiện lên bản tin, và JSON hỏng bị nuốt im lặng (xanh giả).
"""
from __future__ import annotations

import json

import pytest

from tools import gen_morning_brief


def _ghi(tmp_path, noi_dung: str) -> None:
    (tmp_path / "daily_integrity.json").write_text(noi_dung, encoding="utf-8", newline="\n")


def _dong_di(updates: list[str]) -> list[str]:
    return [u for u in updates if "Daily integrity" in u]


@pytest.fixture
def _thu_muc(tmp_path, monkeypatch):
    monkeypatch.setattr(gen_morning_brief, "RESULTS_DIR", tmp_path)
    return tmp_path


def test_ok_false_la_do_kem_so_phat_hien(_thu_muc):
    _ghi(_thu_muc, json.dumps({
        "job": "daily_integrity", "ok": False,
        "findings": ["AGENT_HASH_MISMATCH:a", "UNTRACKED_CRITICAL:b"], "detail": {},
    }))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1
    assert dong[0].startswith("🔴")
    assert "FAIL" in dong[0]
    assert "2 phát hiện" in dong[0]


def test_ok_true_im_lang(_thu_muc):
    _ghi(_thu_muc, json.dumps({"job": "daily_integrity", "ok": True, "findings": [], "detail": {}}))
    assert _dong_di(gen_morning_brief.check_surveillance_updates()) == []


def test_json_hong_la_chua_do(_thu_muc):
    _ghi(_thu_muc, '{"ok": tru')
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1
    assert dong[0].startswith("⚪")
    assert "CHƯA ĐO" in dong[0]


def test_thieu_khoa_ok_la_chua_do(_thu_muc):
    _ghi(_thu_muc, json.dumps({"job": "daily_integrity", "findings": []}))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1 and dong[0].startswith("⚪")


def test_ok_khong_phai_bool_la_chua_do(_thu_muc):
    """``"ok": "true"`` (chuỗi) không phải xanh — chỉ ``ok is True`` mới là xanh."""
    _ghi(_thu_muc, json.dumps({"ok": "true", "findings": []}))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1 and dong[0].startswith("⚪")


def test_khong_phai_object_la_chua_do(_thu_muc):
    _ghi(_thu_muc, json.dumps([1, 2]))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1 and dong[0].startswith("⚪")


def test_dinh_dang_cu_status_fail_van_do(_thu_muc):
    _ghi(_thu_muc, json.dumps({"status": "FAIL"}))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1 and dong[0].startswith("🔴")


def test_tieng_viet_utf8_doc_duoc(_thu_muc):
    """Tệp UTF-8 có tiếng Việt phải parse được (encoding tường minh, không phụ thuộc locale)."""
    _ghi(_thu_muc, json.dumps({"ok": False, "findings": ["Lệch băm tác nhân"]}, ensure_ascii=False))
    dong = _dong_di(gen_morning_brief.check_surveillance_updates())
    assert len(dong) == 1 and dong[0].startswith("🔴")


def test_khong_co_tep_giu_im_lang(_thu_muc):
    assert _dong_di(gen_morning_brief.check_surveillance_updates()) == []


def test_doc_duoi_locale_khong_utf8(tmp_path):
    """Locale không UTF-8 (ASCII — đại diện cp1252 của Windows): tệp UTF-8 có tiếng Việt vẫn
    phải ra 🔴, không được rơi thành ⚪ vì UnicodeDecodeError (encoding phải tường minh)."""
    import ast
    import os
    import subprocess
    import sys
    from pathlib import Path

    goc = Path(__file__).resolve().parent.parent
    (tmp_path / "daily_integrity.json").write_text(
        json.dumps({"ok": False, "findings": ["Lệch băm tác nhân"]}, ensure_ascii=False),
        encoding="utf-8", newline="\n",
    )
    ma = (
        "import sys; from pathlib import Path; from tools import gen_morning_brief as g; "
        "g.RESULTS_DIR = Path(sys.argv[1]); "
        "print(ascii([u for u in g.check_surveillance_updates() if 'Daily integrity' in u]))"
    )
    env = dict(os.environ)
    env.pop("LANG", None)
    env.update({"LC_ALL": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0",
                "PYTHONPATH": str(goc)})
    kq = subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", ma, str(tmp_path)],
        cwd=str(goc), env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=120,
    )
    assert kq.returncode == 0, kq.stderr
    dong = ast.literal_eval(kq.stdout.strip().splitlines()[-1])
    assert len(dong) == 1 and dong[0].startswith("\U0001f534"), dong
