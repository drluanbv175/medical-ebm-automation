"""Nhập 45 thang điểm lâm sàng từ tài liệu HTML do người dùng biên soạn.

NGUYÊN TẮC LIÊM CHÍNH:
- CHỈ tách & lưu NGUYÊN VĂN nội dung từ file HTML nguồn (bảng chấm điểm, diễn giải,
  hành động, cảnh báo, nguồn). KHÔNG tóm tắt lại, KHÔNG sinh nội dung mới.
- Mỗi thang điểm giữ lại đúng khối HTML gốc của thẻ <article class="card"> để hiển thị
  lại y hệt tài liệu gốc (kèm CSS gốc) -> truy vết 100%.

Có 'mục cập nhật': trỏ tới file HTML mới (khi guideline đổi) rồi nhập lại; bản sao
nguồn được lưu trong data/reference/source/ để không phụ thuộc thư mục Downloads.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings

REF_DIR = settings.data_dir / "reference"
SOURCE_DIR = REF_DIR / "source"
JSON_PATH = REF_DIR / "clinical_scores_45.json"

# Các trường mô tả lấy từ thẻ .field (label -> khóa)
_FIELD_MAP = {
    "Tình huống lâm sàng cần dùng": "situation",
    "Mục đích sử dụng": "purpose",
    "Loại công cụ": "tool_type",
    "Đối tượng áp dụng": "population",
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def parse_html(path: Path) -> Dict:
    """Tách 45 thẻ thang điểm + CSS gốc từ file HTML. Trả về {css, items:[...]}."""
    from bs4 import BeautifulSoup

    html = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Gom toàn bộ CSS gốc để hiển thị chi tiết giống hệt tài liệu
    css = "\n".join(tag.get_text() for tag in soup.find_all("style"))

    items: List[Dict] = []
    # Duyệt theo thứ tự xuất hiện để gán đúng nhóm chuyên khoa (h3.group) cho từng card
    current_group = ""
    for el in soup.find_all(["h3", "article"]):
        cls = el.get("class") or []
        if el.name == "h3" and "group" in cls:
            current_group = el.get_text(" ", strip=True)
            continue
        if el.name == "article" and "card" in cls and str(el.get("id", "")).startswith("tool-"):
            h4 = el.find("h4")
            raw_name = h4.get_text(" ", strip=True) if h4 else el.get("id")
            # Bỏ số thứ tự đầu tên: "7. Wells DVT" -> stt=7, name="Wells DVT"
            stt, name = _split_stt(raw_name)
            ev = el.find(class_="evidence")
            evidence = ev.get_text(strip=True) if ev else ""
            fields = {}
            for f in el.find_all(class_="field"):
                lab = f.find(class_="label")
                val = f.find(class_="value")
                if lab and val:
                    key = _FIELD_MAP.get(lab.get_text(strip=True))
                    if key:
                        fields[key] = val.get_text(" ", strip=True)
            items.append({
                "id": el.get("id"),
                "stt": stt,
                "name": name,
                "group": current_group,
                "evidence": evidence,
                "situation": fields.get("situation", ""),
                "purpose": fields.get("purpose", ""),
                "tool_type": fields.get("tool_type", ""),
                "population": fields.get("population", ""),
                "html": el.decode_contents(),  # NGUYÊN VĂN khối thẻ
            })
    return {"css": css, "items": items}


def _split_stt(raw: str):
    import re
    m = re.match(r"\s*(\d+)\s*[.)]\s*(.+)", raw or "")
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None, (raw or "").strip()


def import_from_html(path: str | Path) -> Dict:
    """Nhập/cập nhật từ file HTML: lưu bản sao nguồn + sinh JSON có cấu trúc.

    Trả về meta {source, imported_at, count}. Ném lỗi nếu file không tồn tại/không có thẻ.
    """
    src = Path(path).expanduser()
    if not src.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {src}")
    parsed = parse_html(src)
    if not parsed["items"]:
        raise ValueError("File HTML không chứa thẻ thang điểm (article.card id=tool-*).")

    REF_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    # Lưu bản sao nguồn (không phụ thuộc Downloads)
    saved_src = SOURCE_DIR / src.name
    try:
        if Path(src).resolve() != saved_src.resolve():
            shutil.copy2(src, saved_src)
    except Exception:
        saved_src = src  # nếu copy lỗi vẫn tiếp tục

    meta = {
        "source": src.name,
        "source_path": str(saved_src),
        "imported_at": _now(),
        "count": len(parsed["items"]),
    }
    payload = {"meta": meta, "css": parsed["css"], "items": parsed["items"]}
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    return meta


def load_reference() -> Optional[Dict]:
    """Đọc kho thang điểm đã nhập. None nếu chưa nhập lần nào."""
    if not JSON_PATH.exists():
        return None
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def is_imported() -> bool:
    return JSON_PATH.exists()
