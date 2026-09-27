"""ESD07 canary KHÔNG được tiêu hạn mức tính phí/giới hạn — vá 27/09/2026.

Đo thật: mỗi lần chạy `verify_evidence_surveillance_deployment.py --online`, canary quét 2 chủ đề GIẢ đã gọi THẬT
Consensus (10 lượt/tháng, dùng chung với MCP) và SerpApi (trả phí). Nay tiến trình canary nhận
`ENABLE_CONSENSUS=false` + `ENABLE_SERPAPI_SCHOLAR=false` (engine đọc biến HĐH TRƯỚC kho bí mật). Kèm: lời gợi ý khi
ESD07 đỏ vì NCBI lỗi phía máy chủ, để không chẩn đoán nhầm thành lỗi mã. Ngoại tuyến.
"""
from __future__ import annotations

import sys

from tests.test_verify_esd_bo_cuc_cloud_20260924 import _dung_ebm
from tools import verify_evidence_surveillance_deployment as V


def test_run_ghi_de_bien_he_dieu_hanh_bang_env_them(tmp_path, monkeypatch):
    monkeypatch.setenv("ENABLE_CONSENSUS", "true")
    monkeypatch.setenv("ENABLE_SERPAPI_SCHOLAR", "true")
    ok, ra = V._run([sys.executable, "-c",
                     "import os; print(os.environ['ENABLE_CONSENSUS'], os.environ['ENABLE_SERPAPI_SCHOLAR'])"],
                    cwd=tmp_path, env_them=V._ENV_CANARY_KHONG_TINH_PHI)
    assert ok and ra.endswith("false false"), ra


def test_canary_esd07_chay_scanner_voi_lan_tinh_phi_da_tat(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    monkeypatch.setattr(V, "ROOT", goc)
    goi: list[tuple[list[str], dict | None]] = []

    def gia(command, *, cwd, env_them=None):
        goi.append(([str(x) for x in command], env_them))
        return True, ""
    monkeypatch.setattr(V, "_run", gia)
    V._check_online_scanner()
    quet = [env for lenh, env in goi if any(x.endswith("surveillance_scan.py") for x in lenh)]
    assert quet, "không thấy lượt chạy scanner nào — test đang đo nhầm chỗ"
    for env in quet:
        assert env and env.get("ENABLE_CONSENSUS") == "false" and env.get("ENABLE_SERPAPI_SCHOLAR") == "false", \
            "canary (chủ đề GIẢ) chạy scanner mà không tắt Consensus/SerpApi ⇒ tiêu hạn mức thật"


def test_goi_y_chi_hien_khi_moi_chu_de_suy_giam_vi_ncbi():
    loi_ncbi = ("SUY GIẢM: tầng chung: NCBI lỗi (PubMed request thất bại sau 3 lần: HTTP Error 500)"
                " — Europe PMC dự phòng")
    assert "GỢI Ý" in V._goi_y_ncbi_loi([loi_ncbi, loi_ncbi])
    assert V._goi_y_ncbi_loi([loi_ncbi, "Không đọc được audit JSON"]) == ""
    assert V._goi_y_ncbi_loi([]) == ""
