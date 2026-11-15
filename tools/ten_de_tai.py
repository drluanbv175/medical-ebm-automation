"""Tên đề tài CHÍNH THỨC dùng chung cho mọi bộ sinh văn bản (15/11/2026).

Bác sĩ 15/11/2026 giao đồng bộ «Xác Định Vấn Đề & Hình Thành Câu Hỏi Nghiên Cứu … đảm bảo sự đồng bộ xuyên suốt và chính
xác nhất». Đo trên C1a: `study_meta.title` (tên chính thức — đề cương nộp, hồ sơ đạo đức đã sửa tay) khác
`study_meta.topic` (chuỗi CHỦ ĐỀ dùng để tìm y văn ở G0 — «… tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến
cuối»). Các bộ sinh G2/G3/G4/G5/G6/G10 lại in `topic` làm «Tên đề tài», kể cả mục 10 «Scientific Title» của bản đăng ký
WHO TRDS 1.3.1 — nên SAP đã ký, đề cương thống nhất và bản đăng ký mang một tên khác đề cương nộp.

Luật: tên in trên văn bản = `study_meta.title` (hoặc `gate_params.G2.scientific_title` cho bản đăng ký); chưa khai ⇒ lùi
về `topic` như cũ (đề tài chưa có tên chính thức không đổi hành vi). `topic` vẫn là chuỗi tìm y văn — không đổi.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Union

_O_TRONG = re.compile(r"^\s*(\[\s*CẦN|\[\s*CAN\s|TBD\b|TODO\b|N/?A\b|none\b|null\b)", re.I)


def _that(v: Any) -> Optional[str]:
    s = str(v or "").strip()
    return s if s and not _O_TRONG.match(s) and "[CẦN" not in s.upper() else None


def doc_meta(nguon: Union[Mapping[str, Any], Path, str, None]) -> Mapping[str, Any]:
    """`nguon` là dict study_meta, thư mục đề tài (chứa study_meta.json) hoặc chính tệp study_meta.json."""
    if isinstance(nguon, Mapping):
        return nguon
    if not nguon:
        return {}
    p = Path(nguon)
    p = p / "study_meta.json" if p.is_dir() else p
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return m if isinstance(m, Mapping) else {}


def ten_chinh_thuc(nguon: Union[Mapping[str, Any], Path, str, None], du_phong: str = "") -> str:
    """Tên đề tài chính thức (`study_meta.title`); không có ⇒ `du_phong` (thường là `topic`)."""
    return _that(doc_meta(nguon).get("title")) or (du_phong or "")


def ten_khoa_hoc_dang_ky(nguon: Union[Mapping[str, Any], Path, str, None], du_phong: str = "") -> str:
    """Mục 10 WHO TRDS «Scientific Title»: `gate_params.G2.scientific_title` nếu PI khai, không thì tên chính thức."""
    m = doc_meta(nguon)
    g2 = (m.get("gate_params") or {}).get("G2") if isinstance(m.get("gate_params"), Mapping) else None
    rieng = _that(g2.get("scientific_title")) if isinstance(g2, Mapping) else None
    return rieng or ten_chinh_thuc(m, du_phong)
