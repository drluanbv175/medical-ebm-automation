"""Dựng VIDEO dọc 1080×1920 từ slideshow + GIỌNG ĐỌC tiếng Việt.

Công cụ (đều OFFLINE, không cần mạng, không cần cài hệ thống):
- TTS: lệnh macOS `say -v Linh` (giọng tiếng Việt sẵn trong macOS).
- Ghép video: ffmpeg tĩnh kèm trong gói `imageio-ffmpeg` (nằm trong venv).

Mỗi slide hiển thị đúng thời lượng câu đọc của nó (kèm 0.8s ngân cuối) rồi nối lại.
An toàn: thiếu `say` (không phải macOS) hoặc thiếu ffmpeg -> trả None, packager bỏ
qua video, vẫn xuất slideshow + caption.

LIÊM CHÍNH: lời đọc = đúng văn bản tiếng Việt ĐÃ HIỂN THỊ trên slide (dịch tham
khảo); không thêm nội dung/khuyến cáo mới. Slide vẫn hiện nguyên văn tiếng Anh.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from app.social.render import _strip  # bỏ emoji khỏi lời đọc (đọc ký hiệu rất kỳ)
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

TTS_VOICE = os.getenv("TIKTOK_TTS_VOICE", "Linh")  # giọng vi_VN của macOS `say`
TTS_ENGINE = os.getenv("TIKTOK_TTS_ENGINE", "auto").lower()  # auto|edge|say
EDGE_VOICE = os.getenv("TIKTOK_EDGE_VOICE", "vi-VN-HoaiMyNeural")  # giọng neural mềm
EDGE_RATE = os.getenv("TIKTOK_EDGE_RATE", "-8%")   # chậm nhẹ cho "mềm mại"
TAIL_PAD = 0.8     # giây ngân thêm sau khi đọc xong mỗi slide
MIN_SLIDE_SEC = 2.6  # thời lượng tối thiểu mỗi slide (tránh chớp nhoáng)


def _ffmpeg_exe() -> Optional[str]:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def say_available() -> bool:
    """macOS `say` + giọng tiếng Việt."""
    if not shutil.which("say"):
        return False
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=10)
        return bool(re.search(rf"^{re.escape(TTS_VOICE)}\s", out.stdout, re.M)) or "vi_VN" in out.stdout
    except Exception:
        return False


def edge_available() -> bool:
    """edge-tts (giọng neural mềm, cần mạng lúc dựng)."""
    try:
        import edge_tts  # noqa: F401
        return True
    except Exception:
        return False


def tts_available() -> bool:
    return say_available() or edge_available()


def available() -> bool:
    return tts_available() and _ffmpeg_exe() is not None


# --------------------------------------------------------------------------
def _say(text: str, out_aiff: Path) -> bool:
    text = _strip(text).strip()
    if not text:
        return False
    try:
        r = subprocess.run(["say", "-v", TTS_VOICE, "-o", str(out_aiff), text],
                           capture_output=True, timeout=120)
        return r.returncode == 0 and out_aiff.exists()
    except Exception as exc:  # pragma: no cover
        logger.warning("say TTS lỗi: %s", exc)
        return False


def _edge_synth(text: str, out_mp3: Path) -> bool:
    """Giọng neural mềm qua edge-tts (cần mạng). True nếu tạo được file."""
    text = _strip(text).strip()
    if not text:
        return False
    try:
        import asyncio
        import edge_tts

        async def _run():
            await edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE).save(str(out_mp3))

        asyncio.run(_run())
        return out_mp3.exists() and out_mp3.stat().st_size > 0
    except Exception as exc:
        logger.warning("edge-tts lỗi (offline?): %s", exc)
        return False


def _synth(text: str, tmp_dir: Path, idx: int, engine: str) -> Optional[Path]:
    """Tổng hợp giọng theo engine ưu tiên; trả path audio (mp3/aiff) hoặc None.

    engine: 'edge' (mềm, cần mạng), 'say' (offline macOS), 'auto' (edge rồi say).
    """
    if engine in ("auto", "edge") and edge_available():
        mp3 = tmp_dir / f"a_{idx:02d}.mp3"
        if _edge_synth(text, mp3):
            return mp3
        if engine == "edge":
            return None  # bắt buộc edge mà lỗi -> bỏ (đừng lẫn giọng)
    if engine in ("auto", "say") and say_available():
        aiff = tmp_dir / f"a_{idx:02d}.aiff"
        if _say(text, aiff):
            return aiff
    return None


_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")


def _audio_duration(ff: str, path: Path) -> float:
    try:
        r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True, timeout=30)
        m = _DUR_RE.search(r.stderr)
        if m:
            h, mn, s = m.groups()
            return int(h) * 3600 + int(mn) * 60 + float(s)
    except Exception:  # pragma: no cover
        pass
    return 0.0


def _speak_clean(text: str) -> str:
    """Chuẩn hoá văn bản cho giọng đọc TRÔI CHẢY (bỏ ký hiệu khó đọc)."""
    t = _strip(text or "")
    t = re.sub(r"(\d)\s*/\s*(\d)", r"\1 trên \2", t)   # 135/85 -> 135 trên 85
    t = t.replace("≥", " lớn hơn hoặc bằng ").replace("≤", " nhỏ hơn hoặc bằng ")
    t = t.replace("→", ", ").replace("&", " và ").replace("•", " ").replace("–", " ")
    t = re.sub(r"\s*[/|]\s*", " và ", t)               # 'An toàn / Thận trọng' -> 'và'
    t = re.sub(r"\s{2,}", " ", t).strip(" -·.")
    return t


def _sentence(text: str) -> str:
    """Bảo đảm câu kết thúc bằng dấu để giọng đọc NGẮT NGHỈ đúng."""
    t = _speak_clean(text)
    if not t:
        return ""
    return t if t[-1] in ".!?…:" else t + "."


def _slide_narrations(post: dict) -> List[str]:
    """Lời đọc cho từng slide (cover, các slide điểm, nguồn).

    Mỗi ý là MỘT CÂU kết thúc bằng dấu chấm -> giọng neural tự ngắt nghỉ tự nhiên.
    """
    nar: List[str] = []
    # 1) Cover: chuyên khoa (ngắt) rồi tiêu đề.
    title = post["title"]["vi"] or post["title"]["en"]
    nar.append(" ".join(s for s in (_sentence(post.get("area", "")), _sentence(title)) if s))
    # 2) Slide điểm: tiêu đề slide (ngắt) rồi từng ý là 1 câu.
    for sl in post["point_slides"]:
        parts = [_sentence(sl["heading"])]
        parts += [_sentence(b["vi"] or b["en"]) for b in sl["bullets"]]
        nar.append(" ".join(p for p in parts if p))
    # 3) Slide nguồn + lưu ý.
    tail = [_sentence(f"{label}. {val}") for label, val in post.get("apply", [])]
    if post.get("source_name"):
        tail.append(_sentence(f"Nguồn, {post['source_name']}"))
    tail.append(_sentence(post.get("disclaimer", "")))
    nar.append(" ".join(p for p in tail if p))
    return nar


def default_narrations(post: dict) -> List[str]:
    """Lời đọc mặc định theo post (public, để dashboard cho XEM TRƯỚC & sửa)."""
    return _slide_narrations(post)


def _motion_vf(dur: float) -> str:
    """Bộ lọc chuyển động MỀM: zoom chậm (Ken Burns) + fade vào/ra."""
    frames = max(int(dur * 25), 1)
    fout = max(dur - 0.5, 0.1)
    return (f"scale=1080:1920,zoompan=z='min(zoom+0.0006,1.08)':"
            f"d={frames}:s=1080x1920:fps=25,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={fout:.2f}:d=0.5,"
            f"format=yuv420p")


def _make_segment(ff: str, image: Path, aiff: Optional[Path], dur: float,
                  out_mp4: Path, motion: bool = False) -> bool:
    """1 slide -> 1 đoạn mp4 (ảnh tĩnh + tiếng, hoặc im lặng nếu không có tiếng)."""
    dur = max(dur, MIN_SLIDE_SEC)
    common = [ff, "-y", "-loglevel", "error"]
    vfilter = _motion_vf(dur) if motion else "scale=1080:1920,format=yuv420p"
    vtune = [] if motion else ["-tune", "stillimage"]
    if aiff and aiff.exists():
        cmd = common + [
            "-loop", "1", "-i", str(image),
            "-i", str(aiff),
            "-af", f"apad=pad_dur={TAIL_PAD}",
            "-t", f"{dur:.2f}",
            "-vf", vfilter, "-c:v", "libx264", *vtune, "-r", "25",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", str(out_mp4)]
    else:  # không có tiếng -> ảnh + audio im lặng để concat đồng nhất
        cmd = common + [
            "-loop", "1", "-i", str(image),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", f"{dur:.2f}",
            "-vf", vfilter, "-c:v", "libx264", *vtune, "-r", "25",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        if r.returncode != 0:
            logger.warning("ffmpeg segment lỗi: %s", r.stderr.decode("utf-8", "ignore")[:300])
        return r.returncode == 0 and out_mp4.exists()
    except Exception as exc:  # pragma: no cover
        logger.warning("ffmpeg segment exception: %s", exc)
        return False


def _animated_segment(ff: str, image: Path, audio: Optional[Path], dur: float,
                      out_mp4: Path, fps: int = 25) -> bool:
    """1 slide -> đoạn mp4 với HIỆU ỨNG VẼ TAY (bơm frame numpy vào ffmpeg)."""
    import numpy as np
    from app.social import animate

    dur = max(dur, MIN_SLIDE_SEC)
    common = [ff, "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{animate.W}x{animate.H}",
              "-r", str(fps), "-i", "-"]
    if audio and audio.exists():
        ain = ["-i", str(audio), "-af", f"apad=pad_dur={TAIL_PAD}"]
    else:
        ain = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    cmd = common + ain + [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-t", f"{dur:.2f}", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in animate.slide_frames(image, dur, fps):
            proc.stdin.write(np.ascontiguousarray(fr, dtype=np.uint8).tobytes())
        proc.stdin.close()
        proc.wait(timeout=600)
        return out_mp4.exists() and proc.returncode == 0
    except Exception as exc:  # pragma: no cover
        logger.warning("ffmpeg draw-on lỗi: %s", exc)
        return False


def build_video(post: dict, slide_paths: List[Path], out_dir: Path,
                motion: bool = False, engine: Optional[str] = None,
                draw_on: bool = False, narrations: Optional[List[str]] = None) -> Optional[Path]:
    """Dựng video.mp4 từ các slide PNG + giọng đọc. None nếu không đủ công cụ/slide.

    motion=True: chuyển động mềm (zoom chậm + fade) — hợp phong cách whiteboard.
    draw_on=True: HIỆU ỨNG VẼ TAY (chữ hiện dần + cây bút) — chỉ dùng cho whiteboard.
    engine: 'edge' (giọng neural mềm), 'say' (offline), None -> TTS_ENGINE (auto).
    narrations: lời đọc ĐÃ SỬA cho từng slide (None -> tự sinh từ post).
    """
    ff = _ffmpeg_exe()
    if not ff or not slide_paths:
        return None
    eng = (engine or TTS_ENGINE)
    narrations = narrations if narrations is not None else _slide_narrations(post)
    try:
        from app.social import animate
        use_draw = draw_on and animate.available()
    except Exception:
        use_draw = False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        segments: List[Path] = []
        for i, image in enumerate(slide_paths):
            text = narrations[i] if i < len(narrations) else ""
            audio = _synth(text, tmp_dir, i, eng)
            dur = (_audio_duration(ff, audio) + TAIL_PAD) if audio else MIN_SLIDE_SEC
            seg = tmp_dir / f"seg_{i:02d}.mp4"
            if use_draw:
                ok = _animated_segment(ff, image, audio, dur, seg)
            else:
                ok = _make_segment(ff, image, audio, dur, seg, motion=motion)
            if ok:
                segments.append(seg)

        if not segments:
            return None

        # Nối các đoạn (cùng codec/tham số -> concat copy).
        listfile = tmp_dir / "list.txt"
        listfile.write_text("".join(f"file '{s}'\n" for s in segments), encoding="utf-8")
        out_mp4 = out_dir / "video.mp4"
        try:
            r = subprocess.run(
                [ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(listfile), "-c", "copy", "-movflags", "+faststart", str(out_mp4)],
                capture_output=True, timeout=240)
            if r.returncode != 0:
                # fallback: re-encode khi copy lỗi (timebase lệch...)
                r = subprocess.run(
                    [ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                     "-i", str(listfile), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-movflags", "+faststart", str(out_mp4)],
                    capture_output=True, timeout=300)
            if r.returncode == 0 and out_mp4.exists():
                return out_mp4
            logger.warning("ffmpeg concat lỗi: %s", r.stderr.decode("utf-8", "ignore")[:300])
        except Exception as exc:  # pragma: no cover
            logger.warning("ffmpeg concat exception: %s", exc)
    return None
