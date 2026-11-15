"""Chạy giả lập TRỌN VÒNG như một đề tài thật (bác sĩ 15/11/2026) — chỉ khi gọi rõ GIA_LAP_TRON_VONG=1.

Mỗi thiết kế chạy trên bản sao tạm của `tools/ app/ config/ templates/` (thư mục tmp của pytest), khoá ký là khoá GIẢ
của conftest. Báo cáo ghi vào `state/gia-lap-tron-vong/<mã kịch bản>.json` của worktree (ngoài git) để đánh giá và
so sánh giữa các lần. Test chỉ đỏ khi: chạm khoá thật, rò sang `exports/` thật, hoặc không ghi được báo cáo — kết quả
đánh giá (ô hỏi lại, lệch trục, cổng dừng) nằm trong báo cáo, không phải điều kiện đạt của test.

Chạy: GIA_LAP_TRON_VONG=1 python -B -m pytest -q -s -p no:cacheprovider tests/test_gia_lap_tron_vong_20261115.py -k
cohort
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gia_lap_dinh_ky as GL  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402

pytestmark = pytest.mark.skipif(not os.environ.get("GIA_LAP_TRON_VONG"),
                                reason="giả lập trọn vòng chỉ chạy khi gọi rõ GIA_LAP_TRON_VONG=1 (chậm, cần nền G0)")


@pytest.mark.parametrize("ma", list(GL.KICH_BAN), ids=[GL.KICH_BAN[m]["thiet_ke"] for m in GL.KICH_BAN])
def test_gia_lap_tron_vong(ma, tmp_path):
    truoc = set(GL._de_tai_canary_trong_exports(ROOT))
    repo = TV.dung_ban_sao_tron_vong(ROOT, tmp_path)
    bc = TV.chay_mot(ma, repo)
    dich = ROOT / "state" / "gia-lap-tron-vong" / f"{ma}.json"
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(json.dumps(bc, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"\n=== {ma} ({bc['thiet_ke']}) — dừng: {bc['dung']} · ô lỗi máy: {bc['so_o_loi_may']}")
    print("  Phần A:", {k: bc["phan_a"].get(k) for k in ("cong_dung", "ket", "so_can_thiep_do_may")})
    for g, t in bc["o_theo_cong"].items():
        print(f"  {g}: {t['tong']} ô · hỏi lại {t['hoi_lai_da_chot']} · hỏi lặp {t['hoi_lap']} · "
              f"không áp dụng {t['khong_ap_dung']} · mới đúng vai {t['moi_dung_vai']} · chưa có hồ sơ "
              f"{t['chua_co_ho_so']}")
    print("  Cổng:", {g: v.get("trang_thai") for g, v in bc["cong"].items()})
    print("  Trục:", {k: v.get("dem") or v.get("loi") for k, v in bc["truc"].items()})
    assert set(GL._de_tai_canary_trong_exports(ROOT)) == truoc, "rò thư mục ZZCANARY sang exports/ thật"
    assert dich.is_file()
