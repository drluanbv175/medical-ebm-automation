"""Điều phối sinh GÓI nội dung TikTok và xuất ra thư mục để bác sĩ duyệt + đăng.

Cấu trúc xuất:
    data/tiktok/<YYYYMMDD-HHMM>/
        index.html              # trang xem trước cả lô (ảnh + caption)
        manifest.json           # dữ liệu lô (truy vết nguồn)
        <slug>/
            slide_01.png ...    # ảnh slideshow (nếu có Pillow)
            caption.txt         # caption + hashtag để dán lên TikTok
            script.md           # kịch bản đầy đủ (có nguyên văn + dịch)

Nguồn chủ đề:
    1) Pipeline EBM: bản ghi actionable / "mới tuần này", chấm điểm cao.
    2) Hàng đợi tay: data/tiktok/queue.txt — mỗi dòng là id bản ghi hoặc từ khoá tiêu đề.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.reports.weekly_ebm import build_weekly_data
from app.social.content import build_manual_post, build_post, render_caption
from app.social import render as render_mod
from app.social import video as video_mod
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

TIKTOK_DIR = settings.data_dir / "tiktok"
QUEUE_PATH = TIKTOK_DIR / "queue.txt"


def _slug(text: str, maxlen: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text[:maxlen] or "post").strip("-")


def _read_queue() -> List[str]:
    if not QUEUE_PATH.exists():
        return []
    lines = []
    for ln in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            lines.append(ln)
    return lines


def select_rows(limit: int = 5, include_watch: bool = False,
                queue_only: bool = False) -> List[Dict]:
    """Chọn các row chứng cứ làm chủ đề bài đăng (đã chấm điểm sẵn).

    Ưu tiên: hàng đợi tay -> actionable mới -> actionable -> điểm cao.
    Không trùng id. Lọc 'excluded'.
    """
    data = build_weekly_data()
    by_id = {r["id"]: r for r in data["all_rows"]}
    queue = _read_queue()

    picked: List[Dict] = []
    seen = set()

    def _add(row: Dict):
        if row and row["id"] not in seen and row.get("classification") != "excluded":
            seen.add(row["id"])
            picked.append(row)

    # 1) Hàng đợi tay (id chính xác hoặc khớp tiêu đề).
    for token in queue:
        if token.isdigit() and int(token) in by_id:
            _add(by_id[int(token)])
        else:
            low = token.lower()
            for r in data["all_rows"]:
                if low in (r["title"] or "").lower():
                    _add(r)
                    break

    if not queue_only:
        # 2) Actionable mới tuần này -> 3) actionable -> 4) điểm cao.
        for r in data["new_items"]:
            if r.get("is_actionable"):
                _add(r)
        for r in data["actionable_checklist"]:
            _add(r)
        for r in data["executive"]:
            _add(r)

    picked = picked[: max(limit * 3, limit)]  # dư ra để bù row build_post trả None

    # Nạp abstract + trường thật từ DB (weekly_ebm._row không mang abstract).
    _enrich_with_db_fields(picked)
    return picked


def _enrich_with_db_fields(rows: List[Dict]) -> None:
    """Bổ sung abstract/safety_signal/practice_impact (không có trong row báo cáo tuần)."""
    from app.database import session_scope
    from app.models import EvidenceItem
    ids = [r["id"] for r in rows if r.get("id") is not None]
    if not ids:
        return
    with session_scope() as s:
        recs = {e.id: e for e in s.query(EvidenceItem).filter(EvidenceItem.id.in_(ids)).all()}
        for r in rows:
            e = recs.get(r["id"])
            if e is not None:
                r.setdefault("abstract", e.abstract)
                r.setdefault("safety_signal", e.safety_signal or r.get("safety_signal"))
                r.setdefault("practice_impact", e.practice_impact)
                r.setdefault("population", e.population)


def _write_post_folder(batch_dir: Path, post: Dict, idx: int,
                       make_video: bool = False, style: str = "clinical",
                       draw_on: bool = False) -> Dict:
    title = post["title"]["vi"] or post["title"]["en"]
    slug = f"{idx:02d}-{_slug(title)}"
    folder = batch_dir / slug
    folder.mkdir(parents=True, exist_ok=True)

    # Ảnh slideshow (theo phong cách: clinical | whiteboard).
    slide_paths = render_mod.render_slides(post, folder, style=style)

    # Caption.
    caption = render_caption(post)
    (folder / "caption.txt").write_text(caption, encoding="utf-8")

    # Kịch bản đầy đủ (md) — có nguyên văn + dịch để truy vết.
    (folder / "script.md").write_text(_script_md(post), encoding="utf-8")

    # Video dọc + giọng đọc (tuỳ chọn). Whiteboard -> chuyển động mềm.
    video_name = None
    if make_video and slide_paths:
        _draw = draw_on and style == "whiteboard"
        vpath = video_mod.build_video(post, slide_paths, folder,
                                      motion=(style == "whiteboard" and not _draw),
                                      draw_on=_draw)
        if vpath:
            video_name = vpath.name

    return {
        "slug": slug,
        "kind": post["kind"],
        "area": post["area"],
        "title_vi": post["title"]["vi"],
        "title_en": post["title"]["en"],
        "tier": post["tier"],
        "source": post["source_name"],
        "ids": post["ids"],
        "url": post["url"],
        "slides": [p.name for p in slide_paths],
        "n_slides": len(slide_paths),
        "video": video_name,
        "caption_file": "caption.txt",
        "script_file": "script.md",
        "eligibility": post["eligibility_reason"],
    }


def _script_md(post: Dict) -> str:
    L = [f"# {post['title']['vi'] or post['title']['en']}", ""]
    if post["title"]["vi"]:
        L.append(f"> Nguyên văn: *{post['title']['en']}*  ")
    L.append(f"**{post['kind_label']}** · {post['area']} · Độ tin: {post['tier'] or '?'} "
             f"· Mức CC: {post['evidence_level'] or '?'}")
    L.append("")
    for sl in post["point_slides"]:
        L.append(f"## {sl['heading']}")
        for b in sl["bullets"]:
            L.append(f"- {b['vi'] or b['en']}")
            if b["vi"] and b["en"]:
                L.append(f"  - *(nguyên văn: {b['en']})*")
        L.append("")
    if post["apply"]:
        L.append("## Áp dụng")
        for label, val in post["apply"]:
            L.append(f"- **{label}:** {val}")
        L.append("")
    L.append("## Nguồn")
    L.append(f"- {post['source_name']}")
    for i in post["ids"]:
        L.append(f"- {i}")
    if post["url"]:
        L.append(f"- {post['url']}")
    L.append("")
    L.append(f"> ⚠️ {post['disclaimer']}")
    L.append("")
    L.append("## Caption (dán lên TikTok)")
    L.append("```")
    L.append(render_caption(post))
    L.append("```")
    return "\n".join(L)


def _write_index_html(batch_dir: Path, items: List[Dict], stamp: str) -> Path:
    cards = []
    for it in items:
        thumb = ""
        if it["slides"]:
            thumb = (f"<img src='{it['slug']}/{it['slides'][0]}' "
                     f"style='width:200px;border-radius:12px;border:1px solid #ddd'>")
        ids = " · ".join(it["ids"]) if it["ids"] else ""
        kind_color = "#0c4a6e" if it["kind"] == "recommendation" else "#92400e"
        video_link = (f" · <a href='{it['slug']}/{it['video']}'>🎬 video.mp4</a>"
                      if it.get("video") else "")
        cards.append(f"""
        <div class='card'>
          <div class='thumb'>{thumb}</div>
          <div class='meta'>
            <span class='badge' style='background:{kind_color}'>{it['kind']}</span>
            <span class='area'>{it['area']} · Tier {it['tier'] or '?'}</span>
            <h3>{it['title_vi'] or it['title_en']}</h3>
            <p class='src'>📚 {it['source']} {('— ' + ids) if ids else ''}</p>
            <p class='files'>🖼️ {it['n_slides']} ảnh{video_link} ·
               <a href='{it['slug']}/caption.txt'>caption.txt</a> ·
               <a href='{it['slug']}/script.md'>script.md</a> ·
               <a href='{it['slug']}/'>📂 thư mục</a></p>
          </div>
        </div>""")
    html = f"""<!doctype html><html lang='vi'><head><meta charset='utf-8'>
<title>Gói nội dung TikTok EBM — {stamp}</title>
<style>
body{{font-family:system-ui,Arial;max-width:900px;margin:2rem auto;padding:0 1rem;background:#f8fafc}}
h1{{color:#0c4a6e}} .card{{display:flex;gap:1rem;background:#fff;border:1px solid #e2e8f0;
border-radius:16px;padding:1rem;margin:1rem 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.meta{{flex:1}} .badge{{color:#fff;padding:2px 10px;border-radius:999px;font-size:.75rem;
text-transform:uppercase;letter-spacing:.04em}} .area{{color:#64748b;font-size:.85rem;margin-left:.5rem}}
h3{{margin:.4rem 0}} .src{{color:#475569;font-size:.85rem;margin:.2rem 0}}
.files{{font-size:.85rem}} .note{{background:#fff7ed;border-left:4px solid #fb923c;padding:.75rem 1rem;border-radius:8px}}
</style></head><body>
<h1>📱 Gói nội dung TikTok EBM</h1>
<p>Tạo lúc: {stamp} · {len(items)} bài. Mỗi bài: duyệt nội dung → mở thư mục → tải ảnh + dán caption lên TikTok.</p>
<div class='note'>⚠️ Đây là bản nháp tự sinh từ chứng cứ. <b>Hãy đọc kỹ và tự chịu trách nhiệm chuyên môn trước khi đăng.</b>
Nội dung mang tính tham khảo, không thay khám bệnh.</div>
{''.join(cards)}
</body></html>"""
    p = batch_dir / "index.html"
    p.write_text(html, encoding="utf-8")
    return p


def parse_manual_content(text: str) -> List[Dict]:
    """Tách văn bản tự soạn thành các slide.

    Quy ước: MỘT DÒNG TRỐNG = sang slide mới. Trong mỗi đoạn, DÒNG ĐẦU là tiêu đề
    slide, các dòng sau là gạch đầu dòng. Đoạn 1 dòng -> dòng đó là 1 ý.
    """
    blocks = re.split(r"\n\s*\n", (text or "").strip())
    slides: List[Dict] = []
    for blk in blocks:
        lines = [ln.strip(" -•\t") for ln in blk.splitlines() if ln.strip()]
        if not lines:
            continue
        if len(lines) == 1:
            slides.append({"heading": "", "bullets": [lines[0]]})
        else:
            slides.append({"heading": lines[0], "bullets": lines[1:]})
    return slides


def generate_manual_post(title: str, content_text: str, area: str = "Kiến thức y khoa",
                         source: str = "", url: str = "", style: str = "whiteboard",
                         make_video: bool = True, draw_on: bool = False) -> Dict:
    """Tạo MỘT bài TikTok từ nội dung TỰ SOẠN của người dùng (kèm video nếu bật)."""
    TIKTOK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M")
    batch_dir = TIKTOK_DIR / f"{stamp}-tuso"
    batch_dir.mkdir(parents=True, exist_ok=True)

    slides = parse_manual_content(content_text)
    post = build_manual_post(title, slides, area=area, source=source, url=url)
    if post is None:
        return {"count": 0, "error": "Nội dung trống — hãy nhập tiêu đề và vài ý.",
                "batch_dir": str(batch_dir)}

    item = _write_post_folder(batch_dir, post, 1, make_video=make_video, style=style,
                              draw_on=draw_on)
    index = _write_index_html(batch_dir, [item], stamp)
    manifest = {"generated_at": stamp, "style": style, "manual": True, "count": 1,
                "render_available": render_mod.available(),
                "video_available": video_mod.available(), "items": [item]}
    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "batch_dir": str(batch_dir), "index_html": str(index), "count": 1,
        "video": item.get("video"), "n_slides": item["n_slides"],
        "render_available": render_mod.available(),
        "video_available": video_mod.available(),
        "slug": item["slug"],
    }


def preview_manual(title: str, content_text: str, area: str = "Kiến thức y khoa",
                   source: str = "", url: str = "", style: str = "whiteboard") -> Dict:
    """Bước XEM TRƯỚC: dựng slide (ảnh, KHÔNG video) + lời đọc đề xuất để bác sửa."""
    TIKTOK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    batch_dir = TIKTOK_DIR / f"{stamp}-tuso"
    batch_dir.mkdir(parents=True, exist_ok=True)

    slides_struct = parse_manual_content(content_text)
    post = build_manual_post(title, slides_struct, area=area, source=source, url=url)
    if post is None:
        return {"ok": False, "error": "Nội dung trống — hãy nhập tiêu đề và vài ý."}

    item = _write_post_folder(batch_dir, post, 1, make_video=False, style=style)
    folder = batch_dir / item["slug"]
    slide_paths = [str(folder / n) for n in item["slides"]]
    narrations = video_mod.default_narrations(post)
    return {"ok": True, "batch_dir": str(batch_dir), "slug": item["slug"],
            "folder": str(folder), "slides": slide_paths, "narrations": narrations,
            "post": post, "n_slides": item["n_slides"], "style": style}


def create_manual_video(folder: str, post: Dict, slide_paths: List[str],
                        narrations: List[str], style: str = "whiteboard",
                        draw_on: bool = False) -> Dict:
    """Bước TẠO: dựng video từ slide đã xem trước + LỜI ĐỌC ĐÃ SỬA."""
    folder_p = Path(folder)
    paths = [Path(p) for p in slide_paths]
    if not video_mod.available():
        return {"ok": False, "error": "Chưa có giọng đọc/ffmpeg để dựng video."}
    _draw = draw_on and style == "whiteboard"
    vpath = video_mod.build_video(post, paths, folder_p,
                                  motion=(style == "whiteboard" and not _draw),
                                  draw_on=_draw, narrations=narrations)
    return {"ok": bool(vpath), "video": vpath.name if vpath else None,
            "folder": str(folder_p)}


def generate_tiktok_batch(limit: int = 5, include_watch: bool = False,
                          queue_only: bool = False, make_video: bool = False,
                          style: str = "clinical", draw_on: bool = False) -> Dict:
    """Sinh một lô bài đăng TikTok. Trả về dict tóm tắt + đường dẫn.

    style: "clinical" (nền y khoa) hoặc "whiteboard" (bảng trắng viết tay).
    """
    TIKTOK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M")
    batch_dir = TIKTOK_DIR / stamp
    batch_dir.mkdir(parents=True, exist_ok=True)

    rows = select_rows(limit=limit, include_watch=include_watch, queue_only=queue_only)
    items: List[Dict] = []
    skipped = 0
    for row in rows:
        if len(items) >= limit:
            break
        post = build_post(row)
        if post is None:
            skipped += 1
            continue
        if post["kind"] == "watch" and not include_watch:
            skipped += 1
            continue
        items.append(_write_post_folder(batch_dir, post, len(items) + 1,
                                        make_video=make_video, style=style,
                                        draw_on=draw_on))

    index = _write_index_html(batch_dir, items, stamp)
    manifest = {
        "generated_at": stamp,
        "style": style,
        "count": len(items),
        "skipped": skipped,
        "include_watch": include_watch,
        "render_available": render_mod.available(),
        "video_available": video_mod.available(),
        "made_video": make_video,
        "items": items,
    }
    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Đã sinh %d bài TikTok tại %s", len(items), batch_dir)
    return {
        "batch_dir": str(batch_dir),
        "index_html": str(index),
        "count": len(items),
        "skipped": skipped,
        "render_available": render_mod.available(),
        "video_available": video_mod.available(),
        "n_videos": sum(1 for it in items if it.get("video")),
        "items": [{"slug": it["slug"], "title": it["title_vi"] or it["title_en"],
                   "kind": it["kind"], "n_slides": it["n_slides"],
                   "video": it.get("video")} for it in items],
    }
