"""Ambient scribe — chuyển HỘI THOẠI buổi khám (audio) thành BẢN NHÁP SOAP.

Đóng gap Trụ **5.2** của CAFÉ-S ("ambient / đa phương thức"). Nối skill
`giao-tiep-quyet-dinh-soap` (mục 4 — ghi hồ sơ SOAP): module này lo phần KỸ THUẬT
(audio → chữ → khử PII → khung SOAP), còn skill lo phần NGÔN NGỮ/LÂM SÀNG (chất lượng câu chữ).

An toàn — đây là DỮ LIỆU NHẠY CẢM NHẤT (giọng nói bệnh nhân = PHI):

- **Chạy CỤC BỘ.** STT dùng `faster-whisper` (mã nguồn mở, miễn phí) chạy trên máy;
  KHÔNG upload audio lên đám mây.
- **Cổng đồng thuận.** Phải `transcribe(..., consent=True)` mới chạy; mặc định TỪ CHỐI.
- **KHÔNG lưu PII.** Không ghi audio/transcript thô ra đĩa. `scrub_pii` khử định danh
  TRƯỚC khi dựng prompt/log. Đầu ra SOAP dùng placeholder `[BN]`, `[tuổi]`, `[mã ẩn danh]`.
- **Chỉ ĐỀ XUẤT.** Bản SOAP là NHÁP, kèm disclaimer "Cần bác sĩ kiểm chứng"; bác sĩ sửa & duyệt.

Phụ thuộc:

- STT (TÙY CHỌN): `faster-whisper` — chỉ cần khi gọi `transcribe()` với backend mặc định.
  Phần SOAP (khử PII · dựng prompt · parse) chạy ĐƯỢC mà không cần STT.
- LLM dựng câu chữ SOAP: truyền callable ``llm(prompt) -> str`` (vd gọi Claude API khi có
  ANTHROPIC_API_KEY, hoặc dùng skill `giao-tiep-quyet-dinh-soap` ngay trong Claude).

Ví dụ (đã có faster-whisper + một callable LLM):
    tr = transcribe("buoi_kham.m4a", consent=True, language="vi")
    note = transcript_to_soap(tr.text, llm=claude_llm)
    print(note.to_markdown())          # SOAP đã khử PII + disclaimer
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Loại STT trả về: hàm nhận (đường_dẫn_audio, ngôn_ngữ) -> văn bản transcript.
SttBackend = Callable[[str, str], str]
# Loại LLM: hàm nhận prompt -> văn bản SOAP (S/O/A/P).
LlmFn = Callable[[str], str]

DISCLAIMER = "⚠️ BẢN NHÁP do AI dựng từ hội thoại — **Cần bác sĩ kiểm chứng**. KHÔNG chứa PII."
REDACTED = "[ĐÃ ẨN]"


class AmbientError(RuntimeError):
    """Lỗi pipeline ambient scribe (thiếu đồng thuận, thiếu STT/LLM, hoặc lỗi giải mã)."""


# ---------------------------------------------------------------------------
# 1. Khử PII (chạy TRƯỚC khi gửi LLM / ghi log) — phòng thủ nhiều lớp
# ---------------------------------------------------------------------------
# Chữ hoa tiếng Việt (để bắt tên riêng sau "từ khóa dẫn").
_VN_UPPER = ("A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊ"
             "ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ")
# Một "từ" tên riêng: bắt đầu bằng chữ hoa, theo sau là chữ cái (kể cả dấu).
_NAME_WORD = rf"[{_VN_UPPER}][^\W\d_]+"

# Từ khóa dẫn tới TÊN bệnh nhân (bắt theo ngữ cảnh — tiếng Việt không có NER sẵn).
_NAME_CUE = re.compile(
    r"(?P<cue>họ\s+và\s+tên|họ\s+tên|bệnh\s+nhân\s+tên|tên\s+bệnh\s+nhân|"
    r"tên\s+(?:là|cháu|con|em|bác|cô|chú|anh|chị)|tôi\s+(?:tên|là))"
    rf"(?P<sep>\s*(?:là|:)?\s*)(?P<name>(?:{_NAME_WORD}\s*){{1,4}})",
    re.IGNORECASE,
)

# Cấu trúc định danh (không phụ thuộc ngữ cảnh).
_PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    # Số điện thoại VN: +84/0 + 8–10 chữ số.
    ("phone", re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")),
    # Chuỗi ≥9 chữ số liền: CMND(9)/CCCD(12)/thẻ BHYT/mã HS… → ẩn.
    ("id_number", re.compile(r"(?<!\d)\d{9,}(?!\d)")),
    # Ngày sinh theo ngữ cảnh "sinh ... dd/mm/yyyy" hoặc "sinh năm yyyy".
    ("dob", re.compile(r"(sinh(?:\s+(?:năm|ngày))?\s*:?\s*)"
                       r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})", re.IGNORECASE)),
]


def scrub_pii(text: str) -> Tuple[str, int]:
    """Khử định danh best-effort khỏi transcript: email, SĐT, số CMND/CCCD/BHYT, ngày sinh, TÊN.

    Trả về ``(văn_bản_đã_ẩn, số_lần_ẩn)``. Đây là phòng thủ LỚP 1 (cùng với prompt buộc LLM
    dùng placeholder + bác sĩ rà cuối) — KHÔNG bảo đảm tuyệt đối; tên không theo "từ khóa dẫn"
    có thể lọt → bác sĩ phải kiểm. Triết lý: thà ẩn dư còn hơn lộ.
    """
    n = 0
    out = text

    # Tên riêng theo ngữ cảnh: giữ lại từ khóa dẫn, chỉ ẩn phần tên.
    def _mask_name(m: re.Match) -> str:
        return f"{m.group('cue')}{m.group('sep')}{REDACTED}"

    out, c = _NAME_CUE.subn(_mask_name, out)
    n += c

    for _label, pat in _PII_PATTERNS:
        if _label == "dob":
            out, c = pat.subn(lambda m: f"{m.group(1)}{REDACTED}", out)
        else:
            out, c = pat.subn(REDACTED, out)
        n += c

    return out, n


# ---------------------------------------------------------------------------
# 2. STT — chuyển audio thành transcript (cục bộ, có cổng đồng thuận)
# ---------------------------------------------------------------------------
@dataclass
class Transcript:
    """Bản ghi lời nói (CHỈ trong bộ nhớ — không tự ghi ra đĩa)."""

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[dict] = field(default_factory=list)


def _faster_whisper_backend(model_size: str = "base") -> SttBackend:
    """Tạo backend STT dùng faster-whisper (chạy CỤC BỘ, miễn phí).

    Lazy-import để không bắt buộc cài đặt: nếu thiếu thư viện → AmbientError kèm hướng dẫn.
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise AmbientError(
            "Chưa cài STT cục bộ. Cài: `pip install faster-whisper` "
            "(chạy offline, miễn phí; lần đầu tự tải model). "
            "Hoặc truyền backend=... (callable) để tự cấp engine STT."
        ) from exc

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def _run(audio_path: str, language: str) -> str:  # pragma: no cover - cần audio thật
        segments, _info = model.transcribe(audio_path, language=language or None)
        return " ".join(seg.text.strip() for seg in segments).strip()

    return _run


def transcribe(audio_path: str, *, consent: bool, language: str = "vi",
               model_size: str = "base", backend: Optional[SttBackend] = None) -> Transcript:
    """Phiên âm audio buổi khám → Transcript. **Bắt buộc consent=True** (PHI nhạy cảm).

    - `consent`: đã được bệnh nhân đồng thuận ghi âm? Mặc định pipeline TỪ CHỐI nếu False.
    - `backend`: engine STT tùy biến (để test/đổi engine). Mặc định = faster-whisper cục bộ.
    - Audio KHÔNG bị sao chép/lưu; transcript chỉ ở bộ nhớ (gọi `scrub_pii` trước khi log).
    """
    if not consent:
        raise AmbientError(
            "TỪ CHỐI phiên âm: chưa xác nhận đồng thuận ghi âm của bệnh nhân (consent=False). "
            "Ghi âm hội thoại lâm sàng là PHI — chỉ chạy khi đã được phép."
        )
    if not audio_path:
        raise AmbientError("Thiếu đường dẫn audio.")
    run = backend or _faster_whisper_backend(model_size)
    try:
        text = run(audio_path, language)
    except AmbientError:
        raise
    except Exception as exc:  # noqa: BLE001 - gói mọi lỗi engine thành AmbientError
        raise AmbientError(f"Lỗi phiên âm audio: {exc}") from exc
    logger.info("Đã phiên âm %s (ngôn ngữ=%s, %d ký tự).", audio_path, language, len(text))
    return Transcript(text=text, language=language)


# ---------------------------------------------------------------------------
# 3. Dựng SOAP từ transcript (nối skill giao-tiep-quyet-dinh-soap)
# ---------------------------------------------------------------------------
@dataclass
class SoapNote:
    """Bản nháp SOAP có cấu trúc (đã khử PII)."""

    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""

    def to_markdown(self) -> str:
        """Kết xuất Markdown — LUÔN kèm disclaimer; placeholder thay cho PII."""
        return (
            f"# Hồ sơ SOAP (nháp)\n\n"
            f"## S — Chủ quan (Subjective)\n{self.subjective or '[trống]'}\n\n"
            f"## O — Khách quan (Objective)\n{self.objective or '[trống]'}\n\n"
            f"## A — Đánh giá (Assessment)\n{self.assessment or '[trống]'}\n\n"
            f"## P — Kế hoạch (Plan)\n{self.plan or '[trống]'}\n\n"
            f"---\n{DISCLAIMER}\n"
        )


def blank_soap() -> SoapNote:
    """Khung SOAP rỗng với placeholder (không PII) — dùng làm khung cho LLM hoặc điền tay."""
    return SoapNote(
        subjective="Lý do khám của [BN], [tuổi], [giới]: …\nBệnh sử / triệu chứng theo lời kể: …\n"
                   "Tiền sử · thuốc đang dùng · dị ứng: …",
        objective="Sinh hiệu: …\nKhám thực thể: …\nCận lâm sàng có sẵn: …",
        assessment="Chẩn đoán / chẩn đoán phân biệt + mức độ-nguy cơ; lý giải ngắn (có nguồn). …",
        plan="Xét nghiệm / điều trị / liều (kèm PMID/DOI): …\n"
             "Giáo dục & teach-back đã làm: …\n"
             "Safety-netting (dấu hiệu quay lại ngay): …\n"
             "Hẹn tái khám · điều cần theo dõi: …",
    )


def build_soap_prompt(transcript_text: str, *, extra_context: Optional[str] = None) -> str:
    """Dựng prompt yêu cầu LLM viết SOAP theo skill `giao-tiep-quyet-dinh-soap` (mục 4).

    Prompt buộc: dùng placeholder thay PII · không bịa · trích nguồn cho phần điều trị ·
    nêu safety-netting · phân biệt số liệu nguồn vs đánh giá. KHÔNG nhúng PII vào prompt
    (caller nên `scrub_pii` trước — `transcript_to_soap` làm sẵn).
    """
    ctx = f"\nBối cảnh thêm (do bác sĩ cung cấp):\n{extra_context}\n" if extra_context else ""
    return (
        "Bạn là trợ lý ghi hồ sơ y khoa theo chuẩn SOAP (skill giao-tiep-quyet-dinh-soap).\n"
        "Từ bản ghi hội thoại buổi khám dưới đây, hãy soạn BẢN NHÁP SOAP bằng tiếng Việt.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. Dùng placeholder [BN], [tuổi], [giới], [mã ẩn danh] — TUYỆT ĐỐI không ghi tên/định danh thật.\n"
        "2. KHÔNG bịa: chỉ ghi điều có trong hội thoại; thiếu thì ghi '[chưa rõ — cần hỏi thêm]'.\n"
        "3. Phần P (điều trị/liều) nếu viện dẫn chứng cứ phải kèm PMID/DOI; không chắc thì ghi "
        "'[CẦN BÁC SĨ XÁC NHẬN]'.\n"
        "4. P phải có safety-netting (dấu hiệu cần quay lại ngay) và hẹn tái khám.\n"
        "5. Tách rõ dữ kiện (S/O) với nhận định của bạn (A).\n\n"
        "ĐỊNH DẠNG ĐẦU RA — đúng 4 mục, mỗi mục bắt đầu bằng nhãn:\n"
        "S: <chủ quan>\nO: <khách quan>\nA: <đánh giá>\nP: <kế hoạch>\n"
        f"{ctx}\n"
        "BẢN GHI HỘI THOẠI (đã khử định danh):\n"
        f"\"\"\"\n{transcript_text}\n\"\"\"\n"
    )


# Nhãn mở đầu mỗi mục SOAP mà parser chấp nhận (EN + VN).
_SECTION_HEADERS = {
    "subjective": ["s (subjective)", "subjective", "chủ quan", "s"],
    "objective": ["o (objective)", "objective", "khách quan", "o"],
    "assessment": ["a (assessment)", "assessment", "đánh giá", "nhận định", "a"],
    "plan": ["p (plan)", "plan", "kế hoạch", "p"],
}


def _match_section(line: str) -> Optional[str]:
    """Nếu dòng là HEADER của một mục SOAP → trả tên mục; ngược lại None."""
    # Bỏ ký tự trang trí markdown đầu dòng (#, *, khoảng trắng).
    stripped = line.strip().lstrip("#* ").strip()
    low = stripped.lower()
    for key, labels in _SECTION_HEADERS.items():
        for lab in labels:
            # Header phải là "nhãn" + dấu phân cách (:, ), -, —, .) hoặc đứng một mình.
            if low == lab:
                return key
            if low.startswith(lab) and len(low) > len(lab) and low[len(lab)] in ":).-— \t":
                return key
    return None


def parse_soap(llm_text: str) -> SoapNote:
    """Phân tích văn bản LLM (S/O/A/P) thành SoapNote có cấu trúc (chịu được nhiều biến thể nhãn)."""
    sections = {"subjective": [], "objective": [], "assessment": [], "plan": []}
    current: Optional[str] = None
    for raw in llm_text.splitlines():
        key = _match_section(raw)
        if key:
            current = key
            # Giữ phần nội dung viết cùng dòng header (sau dấu phân cách).
            body = re.split(r"[:).\-—]\s*", raw.strip().lstrip("#* ").strip(), maxsplit=1)
            if len(body) > 1 and body[1].strip():
                sections[key].append(body[1].strip())
            continue
        if current:
            sections[current].append(raw.rstrip())
    return SoapNote(
        subjective="\n".join(sections["subjective"]).strip(),
        objective="\n".join(sections["objective"]).strip(),
        assessment="\n".join(sections["assessment"]).strip(),
        plan="\n".join(sections["plan"]).strip(),
    )


def transcript_to_soap(transcript_text: str, *, llm: Optional[LlmFn] = None,
                       scrub: bool = True, extra_context: Optional[str] = None) -> SoapNote:
    """Pipeline transcript → SOAP: (khử PII) → dựng prompt → gọi LLM → parse.

    - `llm`: callable ``(prompt) -> str``. BẮT BUỘC (đây là bước cần mô hình ngôn ngữ).
      Không truyền → AmbientError (gợi ý dùng `claude_llm` hoặc skill trong Claude).
    - `scrub=True`: khử PII trước khi gửi LLM (mặc định BẬT — không tắt khi có PHI thật).
    """
    if llm is None:
        raise AmbientError(
            "Thiếu `llm`. Cần một callable (prompt)->str để viết SOAP, ví dụ `claude_llm` "
            "(khi có ANTHROPIC_API_KEY) hoặc chạy skill `giao-tiep-quyet-dinh-soap` trong Claude. "
            "Khung rỗng để điền tay: dùng `blank_soap()`."
        )
    text = transcript_text
    if scrub:
        text, n = scrub_pii(text)
        if n:
            logger.info("Đã ẩn %d mục nghi PII trước khi dựng SOAP.", n)
    prompt = build_soap_prompt(text, extra_context=extra_context)
    note = parse_soap(llm(prompt))
    # Lưới an toàn LỚP 2: khử PII lần nữa trên đầu ra LLM (phòng LLM chép tên vào).
    for attr in ("subjective", "objective", "assessment", "plan"):
        cleaned, _ = scrub_pii(getattr(note, attr))
        setattr(note, attr, cleaned)
    return note


def from_audio(audio_path: str, *, consent: bool, llm: Optional[LlmFn] = None,
               language: str = "vi", model_size: str = "base",
               backend: Optional[SttBackend] = None,
               extra_context: Optional[str] = None) -> SoapNote:
    """Pipeline TRỌN: audio → STT → khử PII → SOAP. Bao gói `transcribe` + `transcript_to_soap`."""
    tr = transcribe(audio_path, consent=consent, language=language,
                    model_size=model_size, backend=backend)
    return transcript_to_soap(tr.text, llm=llm, scrub=True, extra_context=extra_context)


# ---------------------------------------------------------------------------
# 4. LLM Claude (tùy chọn) — chỉ chạy khi có anthropic SDK + ANTHROPIC_API_KEY
# ---------------------------------------------------------------------------
def claude_llm(prompt: str, *, model: Optional[str] = None, max_tokens: int = 1500) -> str:
    """Gọi Claude API để viết SOAP. Cần `pip install anthropic` + ANTHROPIC_API_KEY.

    Model lấy từ env AMBIENT_SOAP_MODEL (mặc định claude-sonnet-4-6 — đủ cho ghi SOAP).
    Tách riêng để pipeline vẫn test được với llm stub (không tốn API).
    """
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise AmbientError("Thiếu ANTHROPIC_API_KEY — đặt trong .env (ngoài OneDrive) để dùng claude_llm.")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise AmbientError("Chưa cài SDK: `pip install anthropic`.") from exc
    mdl = model or os.getenv("AMBIENT_SOAP_MODEL", "claude-sonnet-4-6")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(  # pragma: no cover - cần mạng + key
        model=mdl, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(getattr(b, "text", "") for b in resp.content)


# ---------------------------------------------------------------------------
# 5. CLI — chạy thử trên một file audio hoặc transcript có sẵn
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - lớp CLI mỏng
    import argparse

    ap = argparse.ArgumentParser(
        description="Ambient scribe: audio/transcript buổi khám → bản nháp SOAP (cục bộ, khử PII).")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--audio", help="Đường dẫn file audio buổi khám (cần faster-whisper).")
    src.add_argument("--transcript", help="File .txt transcript có sẵn (bỏ qua STT).")
    ap.add_argument("--consent", action="store_true",
                    help="Xác nhận đã có đồng thuận ghi âm của bệnh nhân (bắt buộc khi --audio).")
    ap.add_argument("--language", default="vi")
    ap.add_argument("--model", default="base", help="Cỡ model whisper (tiny/base/small…).")
    ap.add_argument("--save", help="Lưu SOAP (đã khử PII) ra file .md. KHÔNG lưu audio/transcript thô.")
    args = ap.parse_args(argv)

    # Lấy transcript.
    if args.audio:
        tr = transcribe(args.audio, consent=args.consent, language=args.language,
                        model_size=args.model)
        transcript_text = tr.text
    else:
        with open(args.transcript, encoding="utf-8") as f:
            transcript_text = f.read()

    clean, n = scrub_pii(transcript_text)
    print(f"[i] Đã ẩn {n} mục nghi PII.")

    # Cần LLM để viết SOAP; nếu không có key thì in PROMPT + khung rỗng để bác sĩ tự xử lý.
    try:
        note = transcript_to_soap(transcript_text, llm=claude_llm)
    except AmbientError as exc:
        print(f"[!] {exc}\n")
        print("→ Dán PROMPT sau vào Claude (skill giao-tiep-quyet-dinh-soap), hoặc dùng khung rỗng:\n")
        print(build_soap_prompt(clean))
        note = blank_soap()

    md = note.to_markdown()
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[✓] Đã lưu SOAP (khử PII) → {args.save}")
    else:
        print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
