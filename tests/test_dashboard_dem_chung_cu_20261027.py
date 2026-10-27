"""Dashboard EBM — đệm danh sách chứng cứ (27/10/2026, bác sĩ báo ứng dụng «rất chậm»).

Đo trên cơ sở dữ liệu thật: mỗi lượt chạy lại trang (bấm BẤT KỲ nút nào) nạp lại toàn bộ ~22.000 bản ghi chứng cứ tới
5 lần (tab 1–5). Nay các tab dùng `_evidence_rows_cached` (st.cache_data, 5 phút) và ba nút đổi dữ liệu xoá đệm ngay.
Chốt khớp DÒNG THI HÀNH (bỏ dòng chú thích), không khớp cả tệp.
"""
from __future__ import annotations

import re
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "app" / "dashboard" / "main.py"


def _dong_thi_hanh() -> list[str]:
    return [d for d in MAIN.read_text(encoding="utf-8").splitlines() if d.strip() and not d.strip().startswith("#")]


def test_cac_tab_khong_con_nap_thang_toan_bo_chung_cu():
    goi_thang = [d for d in _dong_thi_hanh()
                 if re.search(r"\b_evidence_rows\(s\b", d) and not d.lstrip().startswith("def ")]
    # Chỉ còn lời gọi BÊN TRONG bản đệm (dòng `return _evidence_rows(s, **dict(filters))`).
    assert [d.strip() for d in goi_thang] == ["return _evidence_rows(s, **dict(filters))"]
    assert sum("_evidence_rows_cached(" in d for d in _dong_thi_hanh()) >= 6


def test_ban_dem_co_han_va_bi_xoa_sau_thao_tac_doi_du_lieu():
    dong = _dong_thi_hanh()
    i = next(k for k, d in enumerate(dong) if d.startswith("def _evidence_rows_cached("))
    assert re.fullmatch(r"@st\.cache_data\(ttl=\d+, show_spinner=False\)", dong[i - 1].strip())
    for thao_tac in ("res = cmd_live_update()", "seed_all(run_pipeline_mock=True)", "run_pipeline()"):
        k = next(k for k, d in enumerate(dong) if d.strip() == thao_tac)
        assert "_evidence_rows_cached.clear()" in dong[k + 1], thao_tac
