"""Khoá một lượt cho 4 script giám sát chủ sở hữu — vá 29/09/2026.

29/09 hai lượt weekly_safety.sh chạy CHỒNG trên cùng máy (tác vụ lịch nổ bù 18:31 + hook tự khởi động phóng thêm 18:33)
⇒ gấp đôi lời gọi nguồn, 429 hàng loạt, hai tiến trình cùng ghi một log. Mỗi kịch bản chạy trong MỘT tiến trình
bash; lượt «đang chạy» là một tiến trình `sleep` của chính bash đó (PID cùng không gian — chạy được cả Git Bash
trên Windows).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
KHOA_SH = REPO / "scripts" / "_khoa_mot_luot.sh"
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="không có bash")

CHU_SO_HUU = ("weekly_safety", "monthly_update", "evidence_integrity_monthly", "quarterly_superseded")


def _chay(tmp_path: Path, chuan_bi: str) -> tuple[int, str, str]:
    """Chạy `chuan_bi` (dựng khoá giả) rồi thử giành khoá tên `x` trong subshell; trả (mã, stdout, log)."""
    kich_ban = f"""
set -u
export EBM_KHOA_DIR='{tmp_path.as_posix()}'
LOG='{(tmp_path / 'log').as_posix()}'
{chuan_bi}
( . '{KHOA_SH.as_posix()}'; khoa_mot_luot x; echo CHAY ); ma=$?
[ -n "${{giu:-}}" ] && kill "$giu" 2>/dev/null
echo "ma=$ma"
"""
    r = subprocess.run([BASH, "-c", kich_ban], capture_output=True, text=True, timeout=60)
    log = (tmp_path / "log").read_text(encoding="utf-8") if (tmp_path / "log").exists() else ""
    ma = int(re.search(r"ma=(\d+)", r.stdout).group(1))
    return ma, r.stdout, log


def test_luot_thu_hai_bo_qua_ma_75_khong_chay(tmp_path):
    ma, out, log = _chay(tmp_path, """
sleep 30 & giu=$!
mkdir -p "$EBM_KHOA_DIR/x.khoa"; echo "$giu" > "$EBM_KHOA_DIR/x.khoa/pid"; date +%s > "$EBM_KHOA_DIR/x.khoa/luc"
""")
    assert ma == 75 and "CHAY" not in out, "lượt thứ hai vẫn chạy chồng lên lượt đang giữ khoá"
    assert "BỎ QUA" in log
    assert "BẮT ĐẦU" not in log and "KẾT THÚC" not in log, "dòng BỎ QUA không được bị bộ đọc log coi là một lượt"


def test_khoa_cua_tien_trinh_da_chet_thi_chiem_lai_va_nha_khi_xong(tmp_path):
    ma, out, _log = _chay(tmp_path, """
sleep 0 & chet=$!; wait "$chet"
mkdir -p "$EBM_KHOA_DIR/x.khoa"; echo "$chet" > "$EBM_KHOA_DIR/x.khoa/pid"; date +%s > "$EBM_KHOA_DIR/x.khoa/luc"
""")
    assert ma == 0 and "CHAY" in out, "khoá mồ côi (tiến trình đã chết) phải được chiếm lại"
    assert not (tmp_path / "x.khoa").exists(), "xong lượt phải nhả khoá"


def test_khoa_qua_han_du_pid_con_song_thi_chiem_lai(tmp_path):
    ma, out, _log = _chay(tmp_path, """
sleep 30 & giu=$!
mkdir -p "$EBM_KHOA_DIR/x.khoa"; echo "$giu" > "$EBM_KHOA_DIR/x.khoa/pid"
echo $(( $(date +%s) - 30000 )) > "$EBM_KHOA_DIR/x.khoa/luc"
""")
    assert ma == 0 and "CHAY" in out, \
        "PID có thể bị cấp lại sau khi khởi động lại máy — khoá quá hạn phải được chiếm lại"


def test_khoa_vua_tao_chua_kip_ghi_pid_thi_coi_nhu_dang_giu(tmp_path):
    ma, out, _log = _chay(tmp_path, 'mkdir -p "$EBM_KHOA_DIR/x.khoa"')
    assert ma == 75 and "CHAY" not in out


def test_khong_co_khoa_thi_chay_binh_thuong(tmp_path):
    ma, out, _log = _chay(tmp_path, "")
    assert ma == 0 and "CHAY" in out


@pytest.mark.parametrize("ten", CHU_SO_HUU)
def test_moi_script_chu_so_huu_gianh_khoa_truoc_dong_bat_dau(ten):
    """Dòng thi hành (không tính bình luận): gọi `khoa_mot_luot <tên script>` TRƯỚC `echo … BẮT ĐẦU`. Tên phải trùng tên
    tệp — hợp đồng với tools/tu_khoi_dong.py::_khoa_script_dang_giu ở repo gốc."""
    dong = [d for d in (REPO / "scripts" / f"{ten}.sh").read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.lstrip().startswith("#")]
    goi = [i for i, d in enumerate(dong) if re.search(r"\bkhoa_mot_luot\s+(\S+)", d)]
    bat_dau = [i for i, d in enumerate(dong) if "BẮT ĐẦU" in d and d.lstrip().startswith("echo")]
    assert goi and bat_dau, f"{ten}.sh: thiếu lời gọi khoá hoặc dòng BẮT ĐẦU"
    assert goi[0] < bat_dau[0], f"{ten}.sh: giành khoá SAU dòng BẮT ĐẦU — lượt bị bỏ qua sẽ để lại «BẮT ĐẦU» mồ côi"
    assert re.search(r"\bkhoa_mot_luot\s+(\S+)", dong[goi[0]]).group(1) == ten
    assert not any(re.match(r"\s*trap\b", d) for d in dong), f"{ten}.sh: trap riêng sẽ đè trap nhả khoá"
