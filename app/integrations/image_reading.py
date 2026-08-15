"""Đọc ẢNH y khoa đa phương thức (ECG · X-quang · phiếu cận lâm sàng) → BẢN NHÁP đọc có hệ thống.

Đóng gap Trụ **2.3** của CAFÉ-S ("đa phương thức"). Hoàn tất bộ ba hạ tầng cùng FHIR (2.2) và
ambient scribe (5.2). Bổ trợ agent `dien-giai-can-lam-sang` (diễn giải CLS) và `chan-doan-xac-suat`.

An toàn — ảnh y khoa là PHI nhạy cảm:
- **Khử EXIF** (GPS/thiết bị/trường định danh ẩn) trước khi xử lý — bằng Pillow.
- **Định danh in-trên-ảnh (burned-in):** prompt buộc mô hình KHÔNG chép tên/MRN/ngày sinh; bác sĩ
  nên CHE/CẮT góc định danh trước khi chụp. Module cảnh báo, không bảo đảm xóa chữ trên ảnh.
- **Cổng đồng thuận** + **KHÔNG lưu ảnh/kết quả thô**; đầu ra là NHÁP kèm "Cần bác sĩ đọc lại".
- **Chỉ ĐỀ XUẤT:** đây là hỗ trợ đọc sơ bộ, KHÔNG thay chẩn đoán hình ảnh/đọc ECG chính thức.

Phụ thuộc:
- Khử EXIF: `Pillow` (đã có trong môi trường). Thiếu → cảnh báo, bỏ qua bước khử (không chặn).
- Vision LLM: truyền callable ``vision_llm(image_bytes, prompt, media_type) -> str`` (vd `claude_vision`
  khi có ANTHROPIC_API_KEY). Phần dựng prompt/parse chạy được không cần mạng.
"""
from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass
from typing import Callable, List, Optional

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# vision_llm(image_bytes, prompt, media_type) -> text
VisionFn = Callable[[bytes, str, str], str]

DISCLAIMER = ("⚠️ BẢN NHÁP đọc ảnh do AI — **Cần bác sĩ đọc lại** (không thay đọc ECG/chẩn đoán "
              "hình ảnh chính thức). KHÔNG chứa định danh bệnh nhân.")

# Khung đọc CÓ HỆ THỐNG theo loại ảnh (không bịa — chỉ mô tả cái thấy được).
_MODALITY_FRAMEWORKS = {
    "ecg": ("ECG 12 chuyển đạo — đọc theo trình tự: tần số · nhịp (xoang/không) · trục · "
            "sóng P · khoảng PR · phức bộ QRS (thời gian/biên độ) · đoạn ST (chênh lên/xuống) · "
            "sóng T · QT/QTc · dấu phì đại/blốc/thiếu máu cục bộ."),
    "cxr": ("X-quang ngực — đọc theo ABCDE: Airway (khí quản) · Breathing (nhu mô/2 phế trường, "
            "tràn khí/dịch) · Cardiac (bóng tim, tỷ lệ tim-ngực) · Diaphragm (vòm hoành/góc sườn "
            "hoành) · Everything else (xương, mô mềm, dụng cụ)."),
    "lab": ("Phiếu kết quả cận lâm sàng — đọc từng chỉ số: tên · giá trị · đơn vị · khoảng tham "
            "chiếu · cờ cao/thấp; gom nhóm có ý nghĩa; nêu giá trị NGUY KỊCH nếu có."),
    "generic": ("Mô tả có hệ thống nội dung ảnh y khoa: loại ảnh · cấu trúc thấy được · bất "
                "thường nổi bật · giới hạn chất lượng ảnh."),
}


class ImageReadError(RuntimeError):
    """Lỗi pipeline đọc ảnh (thiếu đồng thuận/vision LLM, lỗi giải mã ảnh)."""


# ---------------------------------------------------------------------------
# 1. Khử EXIF (metadata ẩn) — Pillow
# ---------------------------------------------------------------------------
def strip_exif(image: "bytes | str") -> bytes:
    """Trả bytes ảnh ĐÃ BỎ EXIF (GPS/thiết bị/trường định danh). Nhận đường dẫn hoặc bytes.

    Dùng Pillow vẽ lại pixel sang ảnh mới (không kèm metadata). Nếu thiếu Pillow → cảnh báo và
    trả nguyên bytes (KHÔNG chặn pipeline), ghi rõ EXIF chưa được khử.
    """
    try:
        from PIL import Image  # type: ignore
    except ImportError:  # pragma: no cover - phụ thuộc môi trường
        logger.warning("Thiếu Pillow — KHÔNG khử được EXIF. Cài: pip install Pillow.")
        if isinstance(image, str):
            with open(image, "rb") as f:
                return f.read()
        return image

    src = Image.open(image if isinstance(image, str) else io.BytesIO(image))
    fmt = src.format or "PNG"
    clean = Image.new(src.mode, src.size)
    clean.putdata(list(src.getdata()))  # chỉ chép pixel → rụng toàn bộ metadata
    buf = io.BytesIO()
    clean.save(buf, format=fmt)
    return buf.getvalue()


def _media_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/png")


# ---------------------------------------------------------------------------
# 2. Dựng prompt đọc ảnh (nối agent dien-giai-can-lam-sang)
# ---------------------------------------------------------------------------
def build_reading_prompt(modality: str, *, clinical_context: Optional[str] = None) -> str:
    """Prompt buộc đọc CÓ HỆ THỐNG + KHÔNG chép định danh + nêu cờ đỏ + chỉ là nháp."""
    framework = _MODALITY_FRAMEWORKS.get(modality, _MODALITY_FRAMEWORKS["generic"])
    ctx = f"\nBối cảnh lâm sàng (bác sĩ cung cấp): {clinical_context}\n" if clinical_context else ""
    return (
        "Bạn hỗ trợ bác sĩ ĐỌC SƠ BỘ một ảnh y khoa. Đọc theo khung sau:\n"
        f"{framework}\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. KHÔNG chép bất kỳ định danh nào hiện trên ảnh (tên, mã BN/MRN, ngày sinh). Nếu thấy, "
        "ghi '[ẢNH CÓ ĐỊNH DANH — bác sĩ che trước khi lưu]' và BỎ QUA, không chép lại.\n"
        "2. KHÔNG bịa: chỉ mô tả cái THẤY ĐƯỢC; chất lượng ảnh kém thì ghi rõ giới hạn.\n"
        "3. Phân biệt MÔ TẢ (thấy gì) với GỢI Ý (có thể là gì) — gợi ý ghi kèm '[cần đối chiếu lâm sàng]'.\n"
        "4. Nêu mục 'CỜ ĐỎ:' nếu có dấu hiệu cần xử trí/đọc khẩn (vd ST chênh lên, tràn khí "
        "áp lực, giá trị nguy kịch); không có thì ghi 'CỜ ĐỎ: không thấy trên ảnh'.\n"
        "5. Đây là NHÁP hỗ trợ, KHÔNG phải kết luận chẩn đoán.\n"
        f"{ctx}\n"
        "ĐỊNH DẠNG: \nMÔ TẢ: <đọc có hệ thống>\nGỢI Ý: <ấn tượng sơ bộ + cần đối chiếu>\n"
        "CỜ ĐỎ: <nếu có>\n"
    )


# ---------------------------------------------------------------------------
# 3. Kết quả đọc có cấu trúc
# ---------------------------------------------------------------------------
@dataclass
class ImageReading:
    modality: str
    description: str = ""
    impression: str = ""
    red_flags: str = ""
    raw: str = ""

    def to_markdown(self) -> str:
        return (
            f"# Đọc ảnh ({self.modality.upper()}) — nháp\n\n"
            f"## Mô tả có hệ thống\n{self.description or '[trống]'}\n\n"
            f"## Gợi ý (cần đối chiếu lâm sàng)\n{self.impression or '[trống]'}\n\n"
            f"## 🚩 Cờ đỏ\n{self.red_flags or 'Không thấy trên ảnh'}\n\n"
            f"---\n{DISCLAIMER}\n"
        )


def parse_reading(modality: str, text: str) -> ImageReading:
    """Tách văn bản vision thành MÔ TẢ / GỢI Ý / CỜ ĐỎ (chịu nhiều biến thể nhãn)."""
    buckets = {"description": [], "impression": [], "red_flags": []}
    key_map = [
        (re.compile(r"^\s*(?:#+\s*)?(?:mô tả|description|mo ta)\b[:\s]", re.IGNORECASE), "description"),
        (re.compile(r"^\s*(?:#+\s*)?(?:gợi ý|impression|an tuong|ấn tượng)\b[:\s]", re.IGNORECASE), "impression"),
        (re.compile(r"^\s*(?:#+\s*)?(?:cờ đỏ|red flags?|co do)\b[:\s]", re.IGNORECASE), "red_flags"),
    ]
    current: Optional[str] = None
    for line in text.splitlines():
        matched = None
        for pat, key in key_map:
            if pat.search(line):
                matched = key
                rest = pat.sub("", line, count=1).strip()
                if rest:
                    buckets[key].append(rest)
                break
        if matched:
            current = matched
            continue
        if current:
            buckets[current].append(line.rstrip())
    return ImageReading(
        modality=modality,
        description="\n".join(buckets["description"]).strip(),
        impression="\n".join(buckets["impression"]).strip(),
        red_flags="\n".join(buckets["red_flags"]).strip(),
        raw=text,
    )


def read_image(path: str, *, consent: bool, vision_llm: Optional[VisionFn] = None,
               modality: str = "generic", strip_metadata: bool = True,
               clinical_context: Optional[str] = None) -> ImageReading:
    """Pipeline đọc ảnh: (khử EXIF) → dựng prompt → vision LLM → parse. Bắt buộc consent=True.

    `vision_llm` BẮT BUỘC (bước cần mô hình thị giác). Không có → ImageReadError (gợi ý `claude_vision`).
    """
    if not consent:
        raise ImageReadError("TỪ CHỐI đọc ảnh: chưa xác nhận đồng thuận của bệnh nhân (consent=False).")
    if not path:
        raise ImageReadError("Thiếu đường dẫn ảnh.")
    if vision_llm is None:
        raise ImageReadError(
            "Thiếu `vision_llm`. Truyền callable (image_bytes, prompt, media_type)->str, ví dụ "
            "`claude_vision` (cần ANTHROPIC_API_KEY) hoặc dùng agent dien-giai-can-lam-sang trong Claude."
        )
    try:
        img_bytes = strip_exif(path) if strip_metadata else open(path, "rb").read()
    except FileNotFoundError as exc:
        raise ImageReadError(f"Không đọc được ảnh: {exc}") from exc
    prompt = build_reading_prompt(modality, clinical_context=clinical_context)
    try:
        text = vision_llm(img_bytes, prompt, _media_type(path))
    except ImageReadError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ImageReadError(f"Lỗi gọi vision LLM: {exc}") from exc
    logger.info("Đã đọc ảnh %s (modality=%s, %d byte sau khử EXIF).", path, modality, len(img_bytes))
    return parse_reading(modality, text)


# ---------------------------------------------------------------------------
# 4. Vision LLM Claude (tùy chọn) — cần anthropic SDK + ANTHROPIC_API_KEY
# ---------------------------------------------------------------------------
def claude_vision(image_bytes: bytes, prompt: str, media_type: str = "image/png", *,
                  model: Optional[str] = None, max_tokens: int = 1500) -> str:
    """Gọi Claude (vision) đọc ảnh. Model lấy từ env AMBIENT_VISION_MODEL (mặc định claude-opus-4-8)."""
    import base64

    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise ImageReadError("Thiếu ANTHROPIC_API_KEY — đặt trong .env (ngoài OneDrive) để dùng claude_vision.")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImageReadError("Chưa cài SDK: pip install anthropic.") from exc
    mdl = model or os.getenv("AMBIENT_VISION_MODEL", "claude-opus-4-8")
    client = anthropic.Anthropic(api_key=key)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    resp = client.messages.create(  # pragma: no cover - cần mạng + key
        model=mdl, max_tokens=max_tokens,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": prompt},
        ]}],
    )
    return "".join(getattr(b, "text", "") for b in resp.content)


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - CLI mỏng
    import argparse

    ap = argparse.ArgumentParser(description="Đọc sơ bộ ảnh y khoa (ECG/CXR/CLS) — khử EXIF, không PII.")
    ap.add_argument("image", help="Đường dẫn ảnh.")
    ap.add_argument("--modality", default="generic", choices=list(_MODALITY_FRAMEWORKS))
    ap.add_argument("--consent", action="store_true", help="Xác nhận đồng thuận của bệnh nhân.")
    ap.add_argument("--context", default=None, help="Bối cảnh lâm sàng (tùy chọn).")
    ap.add_argument("--save", help="Lưu bản đọc (đã khử định danh) ra .md.")
    args = ap.parse_args(argv)
    try:
        reading = read_image(args.image, consent=args.consent, vision_llm=claude_vision,
                             modality=args.modality, clinical_context=args.context)
        md = reading.to_markdown()
    except ImageReadError as exc:
        print(f"[!] {exc}\n→ Hoặc dùng agent dien-giai-can-lam-sang trong Claude với prompt:\n")
        print(build_reading_prompt(args.modality, clinical_context=args.context))
        return 1
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[✓] Đã lưu → {args.save}")
    else:
        print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
