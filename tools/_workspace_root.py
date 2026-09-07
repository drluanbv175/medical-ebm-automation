"""_workspace_root.py — Giải quyết thư mục "workspace gốc" dùng chung (chứa tools/, sync/,
EBM-Dashboards/, EBM_MASTER/) — tương ứng thư mục "Claude AI" trên máy thật của bác sĩ.

VÁ 07/09/2026 (cùng đợt với tools/ban_sao_tran.py bên repo drluanbv175/ebm-drluanbv175— xem
CLAUDE.md của repo đó, mục "VÁ 07/09/2026"). Nhiều script ở đây (`ROOT = REPO.parent`, ví dụ
`verify_evidence_surveillance_deployment.py`) giả định `medical-ebm-automation` (REPO) nằm
LỒNG một cấp bên trong workspace gốc — đúng trên máy thật (kiến trúc OneDrive cây chung: REPO
là con trực tiếp của "Claude AI", cùng cấp với EBM-Dashboards/, sync/, tools/ cấp gốc). Trên
phiên cloud, `add_repo` dựng workspace gốc (repo drluanbv175/ebm-drluanbv175) làm ANH EM
(sibling) của REPO dưới CÙNG một thư mục cha, không phải CHA trực tiếp của REPO — nên
`REPO.parent` chỉ trỏ tới thư mục chứa cả hai repo, không chứa `tools/`, `sync/` nào cả. Ví dụ
đã đo được: `verify_evidence_surveillance_deployment.py::_check_offline_pipeline()` gọi
`ROOT / "tools" / "verify_clinical_evidence_update_pipeline.py"` và báo lỗi "No such file or
directory" dù file đó tồn tại thật — chỉ là nằm ở repo anh em, không phải REPO.parent.

Nhận diện workspace gốc bằng NỘI DUNG (thư mục `sync/`), không phải TÊN thư mục — tên thư mục
gốc khác nhau giữa các máy (Mac gọi "Claude AI", phiên cloud gọi theo tên repo GitHub đã
add_repo). `.claude/agents/` KHÔNG dùng được làm dấu hiệu vì `medical-ebm-automation` cũng có
bản mirror riêng của `.claude/agents/` (đồng bộ Codex) — `sync/` mới là thư mục CHỈ workspace
gốc có, REPO không có.
"""
from __future__ import annotations

from pathlib import Path

_MARKER = "sync"


def resolve_workspace_root(repo: Path) -> Path:
    """Trả về đường dẫn workspace gốc THẬT (chứa tools/, sync/, EBM-Dashboards/, EBM_MASTER/).

    Ưu tiên vị trí LỒNG (`repo.parent`, đúng máy thật — có `repo.parent/sync`); nếu không,
    dò các thư mục ANH EM của `repo` dưới `repo.parent` (đúng phiên cloud) tìm thư mục có
    `sync/`. Không tìm thấy đâu cả → fallback về `repo.parent` như hành vi cũ (lỗi đường dẫn
    rõ ràng hơn thà báo "không tìm thấy file" còn hơn suy đoán sai trong im lặng).
    """
    parent = repo.parent
    if (parent / _MARKER).is_dir():
        return parent
    if parent.is_dir():
        for sibling in sorted(parent.iterdir()):
            if sibling == repo or not sibling.is_dir():
                continue
            if (sibling / _MARKER).is_dir():
                return sibling
    return parent
