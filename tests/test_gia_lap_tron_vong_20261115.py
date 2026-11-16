"""Chạy giả lập TRỌN VÒNG như một đề tài thật (bác sĩ 15/11/2026) — chỉ khi gọi rõ GIA_LAP_TRON_VONG=1.

Mỗi thiết kế chạy trên bản sao tạm của `tools/ app/ config/ templates/` (thư mục tmp của pytest), khoá ký là khoá GIẢ
của conftest. Báo cáo ghi vào `state/gia-lap-tron-vong/<mã kịch bản>.json` của worktree (ngoài git) để đánh giá và
so sánh giữa các lần. Test chỉ đỏ khi: chạm khoá thật, rò sang `exports/` thật, hoặc không ghi được báo cáo — kết quả
đánh giá (ô hỏi lại, lệch trục, cổng dừng) nằm trong báo cáo, không phải điều kiện đạt của test.

Chạy: GIA_LAP_TRON_VONG=1 python -B -m pytest -q -s -p no:cacheprovider tests/test_gia_lap_tron_vong_20261115.py -k
cohort

Chạy TIẾP từ một cổng (đề tài dài, mỗi lượt từ đầu mất nhiều phút): đặt GIA_LAP_TRON_VONG_DIR=<thư mục bền NGOÀI repo>
— bản sao + khoá GIẢ của đề tài nằm ở <thư mục>/<mã kịch bản>/{repo, khoa-gia} và được dùng lại giữa các lượt —, rồi
GIA_LAP_TU_CONG=G6 (hoặc G6_5 · G7 · G8 · G9 · G10) để bỏ qua các cổng đã đi. Khoá vẫn là khoá GIẢ sinh bằng
`tao_khoa_gia`, chỉ dùng dưới pytest; đường dẫn chứa «ebm-secrets» bị từ chối.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gia_lap_bien_the_kho as BTK  # noqa: E402
import gia_lap_dinh_ky as GL  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402

pytestmark = pytest.mark.skipif(not os.environ.get("GIA_LAP_TRON_VONG"),
                                reason="giả lập trọn vòng chỉ chạy khi gọi rõ GIA_LAP_TRON_VONG=1 (chậm, cần nền G0)")


@pytest.mark.parametrize("ma", list(GL.KICH_BAN), ids=[GL.KICH_BAN[m]["thiet_ke"] for m in GL.KICH_BAN])
def test_gia_lap_tron_vong(ma, tmp_path, monkeypatch):
    _chay_tron_vong(ma, tmp_path, monkeypatch)


# 16/11/2026 — biến thể KHÓ (không kém hơn · cụm · sống còn · dữ liệu thiếu…): sổ riêng `gia_lap_bien_the_kho`, cùng
# thân chạy. Chạy đích danh: …::test_gia_lap_bien_the_kho[rct_ni] (lọc -k «rct» sẽ khớp cả biến thể).
_KHO = BTK.danh_sach()


@pytest.mark.parametrize("ma", [m for m, _i in _KHO], ids=[i for _m, i in _KHO])
def test_gia_lap_bien_the_kho(ma, tmp_path, monkeypatch):
    _chay_tron_vong(ma, tmp_path, monkeypatch)


def _chay_tron_vong(ma, tmp_path, monkeypatch):
    from tests import canh_bi_mat_that as CBM  # noqa: PLC0415

    truoc = set(GL._de_tai_canary_trong_exports(ROOT))
    ben = os.environ.get("GIA_LAP_TRON_VONG_DIR")
    goc = Path(ben).expanduser() / ma if ben else tmp_path
    if ben:
        assert "ebm-secrets" not in str(goc) and not goc.resolve().is_relative_to(ROOT.resolve()), \
            "thư mục bền phải ở NGOÀI repo và ngoài kho bí mật"
        khoa = goc / "khoa-gia" / CBM.TEN_KHOA_GIA
        if not khoa.is_file():
            CBM.tao_khoa_gia(khoa.parent)
        monkeypatch.setenv("EBM_GATE_KEY_PATH", str(khoa))
    repo = goc / "repo"
    if not repo.is_dir():
        repo = TV.dung_ban_sao_tron_vong(ROOT, goc)
    elif os.environ.get("GIA_LAP_TU_CONG"):  # chạy tiếp: mã công cụ lấy bản MỚI của worktree (bản vá giữa hai lượt)
        import shutil  # noqa: PLC0415

        shutil.copytree(ROOT / "tools", repo / "tools", ignore=GL.BO_QUA_KHI_CHEP, dirs_exist_ok=True)
    bc = TV.chay_mot(ma, repo, tu_cong=os.environ.get("GIA_LAP_TU_CONG") or None,
                     den_cong=os.environ.get("GIA_LAP_DEN_CONG") or None)
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
    dc = bc["du_lieu"].get("de_cuong_nop") or {}
    print("  Đề cương nộp:", {k: dc.get(k) for k in ("ma", "so_dong", "trich_dan")}, dc.get("loi") or "K1–K7 đạt")
    assert set(GL._de_tai_canary_trong_exports(ROOT)) == truoc, "rò thư mục ZZCANARY sang exports/ thật"
    assert dich.is_file()
    # 16/11/2026 (bác sĩ: đề cương giả lập phải là đề cương hoàn chỉnh, câu chữ phù hợp): đề tài đi hết tới G10 thì bản
    # đề cương nộp Hội đồng do công cụ soạn phải qua K1–K7 (không ký hiệu nội bộ, đủ chương, cỡ mẫu khớp G3…)
    # 17/11/2026: lượt chạy qua nửa đêm làm G2 bị từ chối ký ⇒ G6.5 sập (KeyError) mà phép thử vẫn «passed» vì sập chỉ
    # nằm trong báo cáo. Sập bước nội bộ là lỗi của bộ giả lập/hệ — phải đỏ.
    assert not bc["crash"], f"bước sập: {bc['crash']} — dừng tại {bc['dung']}"
    if not bc["dung"] and not os.environ.get("GIA_LAP_DEN_CONG"):
        assert dc and not dc.get("loi"), f"đề cương nộp còn lỗi: {dc.get('loi') or 'chưa sinh'}"
