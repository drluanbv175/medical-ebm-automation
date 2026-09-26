"""Dò gốc repo EBM (EBM-drluanbv175) cho công cụ trong repo y khoa — MỘT định nghĩa dùng chung (26/09/2026).

Trên Mac/Windows repo y khoa nằm LỒNG trong repo EBM (gốc = REPO.parent); trên phiên Cloud hai repo là
ANH EM (/home/user/medical-ebm-automation cạnh /home/user/EBM-drluanbv175). Bốn verifier viết cứng
`ROOT = REPO.parent` nên trên Cloud tìm `sync/skills/`, `.claude/agents/` ở `/home/user` và báo FAIL
cả những tệp ĐANG CÓ trong git. Cùng thứ tự dò với `_tim_goc_ebm()` của
verify_evidence_surveillance_deployment.py: EBM_REPO_ROOT → lồng → anh em; không thấy thì giữ hành vi
cũ (REPO.parent) — không bao giờ đoán một thư mục không mang dấu vết repo EBM.
"""
from __future__ import annotations

import os
from pathlib import Path

TEN_REPO_EBM_ANH_EM = ("EBM-drluanbv175", "ebm-drluanbv175")


def la_goc_ebm(path: Path) -> bool:
    """Nhận diện gốc repo EBM bằng DẤU VẾT NỘI DUNG (tệp có trong git), không bằng tên thư mục."""
    return (path / "tools" / "verify_clinical_evidence_update_pipeline.py").is_file() and (
        path / ".claude" / "agents"
    ).is_dir()


def tim_goc_ebm(repo: Path) -> Path:
    env = os.environ.get("EBM_REPO_ROOT", "").strip()
    if env and la_goc_ebm(Path(env).expanduser()):
        return Path(env).expanduser().resolve()
    cha = repo.parent
    if la_goc_ebm(cha):
        return cha
    for ten in TEN_REPO_EBM_ANH_EM:
        if la_goc_ebm(cha / ten):
            return cha / ten
    return cha
