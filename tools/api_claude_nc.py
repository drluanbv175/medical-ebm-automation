"""Cầu nối Claude API dùng chung cho hệ nghiên cứu G0–G10.

VÌ SAO (17/11/2026, bác sĩ: «Kết nối API Claude» — chọn ba việc: kiểm nội dung trích dẫn A12, phản biện máy đề cương
nộp, hội đồng cổng qua Batch API). Trước đó cổng G0–G10 không gọi API: agent chạy trong phiên Claude Code, nên ba việc
trên chỉ làm được khi có người mở phiên. Mô-đun này gom MỌI luật an toàn của một lượt gọi API vào một chỗ để ba công cụ
không mỗi cái tự viết một kiểu:

- TƯ VẤN, chỉ cảnh báo: không công cụ nào dùng mô-đun này được mở/chặn cổng, ghi sổ cái, `study_meta` hay ký.
- CHẠY KHÔ mặc định: công cụ chỉ gọi API khi có cờ `--goi-api` (tính phí); chạy khô in số lượt gọi + ước tính token.
- Khoá: biến môi trường `ANTHROPIC_API_KEY` → kho bí mật `~/.ebm-secrets/medical-ebm-automation.env` (dòng cuối
  thắng — cùng luật với `check_topic_relevance.py` ở repo gốc). KHÔNG BAO GIỜ in giá trị khoá.
- Dưới pytest: không đọc kho khoá thật, không ghi nhật ký thật, không dựng khách API thật (đo thật: đặt
  `EBM_KIEM_API_THAT=1`). Kiểm thử luôn tiêm khách giả qua tham số `client`.
- Kiểm `stop_reason` TRƯỚC khi đọc nội dung: cắt cụt (`max_tokens`) hay từ chối (`refusal`) ⇒ `KetQuaHong`; JSON hỏng
  ⇒ `KetQuaHong` — không bao giờ đoán nửa câu trả lời.
- Ghi sức khoẻ lượt gọi vào `~/.ebm-api-claude.json` (cùng tệp, cùng khoá với repo gốc — giác quan hòm việc
  `giac_quan_api_claude` đọc tệp này để báo bác sĩ khi khoá hết tín dụng/bị thu hồi).
- TRẦN CHI PHÍ THÁNG (18/11/2026, bác sĩ chọn «trần chi phí tháng»): mọi lượt gọi và mọi batch đi qua
  `kiem_ngan_sach` TRƯỚC khi gửi — ước TỐI ĐA (token vào ước + toàn bộ max_tokens) cộng số đã tiêu trong tháng vượt trần
  ⇒ `HetNganSach`, không gửi. Số tiêu THẬT (theo `usage`) ghi vào `~/.ebm-api-claude-chi-phi.json`. Sổ hỏng/không đọc
  được ⇒ chặn (không đoán là còn tiền). Nâng trần là quyết định của bác sĩ (`EBM_API_CLAUDE_TRAN_USD_THANG`).
- PROMPT CACHING (18/11/2026, bác sĩ chọn): system prompt lặp lại giữa nhiều yêu cầu (tệp agent của hội đồng, lời dặn
  của kiểm A12 theo lô) được đánh dấu `cache_control` — đọc từ cache chỉ tính một phần nhỏ giá token vào. Lượt gọi một
  lần (phản biện máy) KHÔNG đánh dấu: ghi cache tính 1,25× mà không ai đọc lại.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Nội dung một lượt: chuỗi, hoặc danh sách khối (ảnh + chữ — tích hợp đọc ảnh của app, 17/11/2026).
NoiDung = Union[str, List[Dict[str, Any]]]

KHO_BI_MAT = os.path.join(os.path.expanduser("~"), ".ebm-secrets", "medical-ebm-automation.env")
NHAT_KY_API = os.path.join(os.path.expanduser("~"), ".ebm-api-claude.json")
# Bản chụp đường THẬT lúc nạp — kiểm thử vá hai hằng trên sang tệp tạm thì không đụng các bản chụp này.
_KHO_THAT = KHO_BI_MAT
_NK_THAT = NHAT_KY_API

MODEL_MAC_DINH = "claude-sonnet-5-5"
# Model nhận `output_config.effort` + `fallbacks` (beta dự phòng khi model từ chối) — cùng danh sách repo gốc đã chạy
# thật 17/11/2026. Model khác gọi như cũ, không thêm tham số mới, để khỏi lỗi 400.
MODEL_HIEN_HANH = frozenset(
    {
        "claude-sonnet-5-5",
        "claude-opus-5-5",
        "claude-haiku-5-5",
        "claude-opus-5",
        "claude-fable-5-1",
        "claude-fable-5-2",
    }
)
BETA_DU_PHONG = "server-side-fallback-2026-07-01"
MAX_TOKENS_MAC_DINH = 16000
# Giá USD mỗi triệu token — bảng giá tài liệu Claude API (skill `claude-api`, bảng chụp 03/11/2026, đọc 18/11/2026).
# «doc_cache» = giá đọc cache (Sonnet/Opus 5.5 = 0,05× giá vào; Fable 5.2 = 0,025×; model khác ~0,1×). Ghi cache TTL 5
# phút = HE_SO_GHI_CACHE × giá vào. Batch API = 50% mọi khoản. Haiku 5.5: giá cho lời nhắn ≤ 100K token (dài hơn
# $0,50/$2,50 — các công cụ ở đây không gửi lời nhắn dài như vậy). Model không có trong bảng ⇒ None: chỉ báo token,
# không bịa tiền — và khi trần chi phí đang bật thì KHÔNG gọi (không kiểm được trần).
GIA_USD_TRIEU_TOKEN = {
    "claude-sonnet-5-5": {"vao": 2.00, "ra": 10.00, "doc_cache": 0.10},
    "claude-opus-5-5": {"vao": 4.00, "ra": 20.00, "doc_cache": 0.20},
    "claude-haiku-5-5": {"vao": 0.10, "ra": 0.50, "doc_cache": 0.01},
    "claude-opus-5": {"vao": 5.00, "ra": 25.00, "doc_cache": 0.50},
    "claude-fable-5-2": {"vao": 8.00, "ra": 40.00, "doc_cache": 0.20},
    "claude-fable-5-1": {"vao": 10.00, "ra": 50.00, "doc_cache": 0.25},
    "claude-fable-5": {"vao": 10.00, "ra": 50.00, "doc_cache": 1.00},
    "claude-sonnet-5": {"vao": 2.00, "ra": 10.00, "doc_cache": 0.20},
    "claude-opus-4-8": {"vao": 5.00, "ra": 25.00, "doc_cache": 0.50},
    "claude-opus-4-7": {"vao": 5.00, "ra": 25.00, "doc_cache": 0.50},
    "claude-opus-4-6": {"vao": 5.00, "ra": 25.00, "doc_cache": 0.50},
    "claude-sonnet-4-6": {"vao": 3.00, "ra": 15.00, "doc_cache": 0.30},
    "claude-haiku-4-5": {"vao": 1.00, "ra": 5.00, "doc_cache": 0.10},
}
HE_SO_GHI_CACHE = 1.25
# Trần chi phí tháng mặc định (USD) — bác sĩ đổi bằng biến môi trường EBM_API_CLAUDE_TRAN_USD_THANG (≤ 0 = khoá hẳn).
# Đo 17/11/2026: một lượt kiểm A12 + một lượt phản biện máy trên BTM tốn ≈ 0,3 USD; 20 USD đủ cho vài chục lượt/tháng.
TRAN_USD_THANG_MAC_DINH = 20.0
SO_CHI_PHI = os.path.join(os.path.expanduser("~"), ".ebm-api-claude-chi-phi.json")
_SO_CP_THAT = SO_CHI_PHI
# Ước token cho một khối ảnh khi tính trần (ảnh ~1.600 token ở cỡ thường) — chỉ để ước TỐI ĐA, không tính tiền thật.
TOKEN_UOC_MOI_ANH = 1600
# Batch API: custom_id chỉ nhận chữ/số/_/- và ≤ 64 ký tự.
_CUSTOM_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class LoiApi(RuntimeError):
    """Mọi lỗi của lượt gọi API (thiếu khoá, thiếu SDK, kết quả hỏng). Công cụ gọi bắt lỗi này ⇒ «bỏ qua/không chấm»."""


class ThieuKhoa(LoiApi):
    """Không có khoá — công cụ in hướng dẫn và thoát êm, không bao giờ coi là «đã kiểm, không có vấn đề»."""


class LoiCucBo(LoiApi):
    """Lỗi PHÍA MÁY (thiếu tệp agent, tham số sai) — không phải kênh API: không ghi vào nhật ký sức khoẻ API."""


class KetQuaHong(LoiApi):
    """Kết quả bị cắt cụt, bị từ chối, hoặc không phải JSON đúng khuôn — KHÔNG đọc tiếp."""


class HetNganSach(LoiCucBo):
    """Lượt gọi sẽ vượt trần chi phí tháng (hoặc sổ chi phí hỏng / model chưa ghi giá) — KHÔNG gửi. Lỗi phía máy:
    không ghi vào nhật ký sức khoẻ API (khoá vẫn sống). Công cụ gọi phải dừng CẢ lượt, không chạy tiếp lô sau."""


def _duoi_pytest_cham_that(duong: str, that: str) -> bool:
    """True khi đang chạy DƯỚI PYTEST mà sắp đọc/ghi đúng tệp THẬT ở thư mục nhà ⇒ phải từ chối.

    `PYTEST_CURRENT_TEST` được tiến trình con kế thừa nên chặn cả đường gián tiếp (test chạy công cụ bằng subprocess).
    Chủ động đo thật thì đặt EBM_KIEM_API_THAT=1."""
    if not os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("EBM_KIEM_API_THAT") == "1":
        return False
    try:
        return os.path.realpath(duong) == os.path.realpath(that)
    except (OSError, ValueError):
        return True  # không phân định được ⇒ thận trọng: coi là tệp thật


def khoa_api(ten: str = "ANTHROPIC_API_KEY", kho: Optional[str] = None) -> str:
    """Khoá theo thứ tự §5: biến môi trường OS → kho bí mật (DÒNG CUỐI thắng — kho ghi kiểu nối thêm). Trả "" khi
    không có. Mọi lỗi đọc đều nuốt. KHÔNG in giá trị."""
    if os.environ.get(ten, "").strip():
        if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("EBM_KIEM_API_THAT") != "1":
            return ""  # dưới pytest không dùng khoá thật của môi trường máy bác sĩ
        return os.environ[ten].strip()
    duong = kho or KHO_BI_MAT
    if _duoi_pytest_cham_that(duong, _KHO_THAT):
        return ""
    gia_tri = ""
    try:
        with open(duong, "r", encoding="utf-8", errors="replace") as fh:
            for dong in fh:
                dong = dong.strip()
                if not dong or dong.startswith("#") or "=" not in dong:
                    continue
                k, _, v = dong.partition("=")
                if k.strip() == ten and v.strip().strip("'\""):
                    gia_tri = v.strip().strip("'\"")  # không return sớm: dòng sau đè dòng trước
    except OSError:
        pass
    return gia_tri


def tao_client(client: Any = None) -> Any:
    """Khách Anthropic. Tiêm `client` (kiểm thử) ⇒ dùng nguyên. Không tiêm ⇒ dựng khách THẬT — bị từ chối dưới pytest
    (một lượt CI không bao giờ được tiêu tiền của bác sĩ)."""
    if client is not None:
        return client
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("EBM_KIEM_API_THAT") != "1":
        raise LoiApi("Dưới pytest không dựng khách Claude API THẬT — tiêm khách giả qua tham số client.")
    key = khoa_api()
    if not key:
        raise ThieuKhoa(
            "Thiếu ANTHROPIC_API_KEY — đặt trong biến môi trường hoặc kho bí mật "
            "~/.ebm-secrets/medical-ebm-automation.env (ngoài OneDrive). Không dán khoá vào khung chat."
        )
    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise LoiApi("Chưa cài SDK: `~/.ebm-venv/bin/pip install anthropic`.") from exc
    return anthropic.Anthropic(api_key=key)  # pragma: no cover - cần mạng + khoá


def chon_model(model: Optional[str], bien_moi_truong: str = "EBM_NC_API_MODEL") -> str:
    """Model: tham số > biến môi trường > mặc định Sonnet 5.5. Tên trống/lạ ký tự ⇒ LoiApi (không gửi rác tới API)."""
    m = (model or os.environ.get(bien_moi_truong) or MODEL_MAC_DINH).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.\-]{2,63}", m):
        raise LoiCucBo(f"Tên model không hợp lệ: «{m}».")
    return m


def tham_so(
    noi_dung: NoiDung,
    *,
    he_thong: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = MAX_TOKENS_MAC_DINH,
    effort: str = "low",
    cache_he_thong: bool = False,
) -> Dict[str, Any]:
    """Tham số Messages API cho MỘT lời gọi — dùng chung cho gọi trực tiếp và Batch API (Batch không nhận `fallbacks`
    nên phần đó thêm riêng ở `goi`). `cache_he_thong=True` ⇒ system thành khối có `cache_control` (TTL 5 phút) — chỉ
    bật khi cùng system prompt được gửi lại nhiều lần; prefix dưới ngưỡng tối thiểu (512 token với model hiện hành) thì
    API lặng lẽ không cache, không tính phí ghi."""
    if effort not in ("low", "medium", "high", "xhigh", "max"):
        raise LoiCucBo(f"effort «{effort}» không hợp lệ")
    mdl = chon_model(model)
    p: Dict[str, Any] = {
        "model": mdl,
        "max_tokens": int(max_tokens),
        "messages": [{"role": "user", "content": noi_dung}],
    }
    if he_thong:
        p["system"] = (
            [{"type": "text", "text": he_thong, "cache_control": {"type": "ephemeral"}}] if cache_he_thong else he_thong
        )
    if mdl in MODEL_HIEN_HANH:
        p["output_config"] = {"effort": effort}
    return p


@dataclass
class KetQuaGoi:
    """Kết quả gọn của một lượt gọi (không giữ đối tượng SDK)."""

    van_ban: str
    model: str
    token_vao: int = 0
    token_ra: int = 0
    stop_reason: Optional[str] = None
    token_cache_ghi: int = 0
    token_cache_doc: int = 0


def _kiem_stop(stop_reason: Optional[str], nhom: Optional[str], max_tokens: int) -> None:
    if stop_reason == "max_tokens":
        raise KetQuaHong(f"Kết quả bị CẮT CỤT ở max_tokens={max_tokens} — không đọc nửa câu trả lời.")
    if stop_reason == "refusal":
        raise KetQuaHong(f"Model từ chối (refusal, nhóm {nhom or 'không rõ'}).")


def goi(
    noi_dung: NoiDung,
    *,
    he_thong: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = MAX_TOKENS_MAC_DINH,
    effort: str = "low",
    client: Any = None,
    cache_he_thong: bool = False,
    nguon: str = "",
) -> KetQuaGoi:
    """MỘT lời gọi Messages API. Lỗi mạng/khoá/SDK ⇒ LoiApi; cắt cụt/từ chối ⇒ KetQuaHong; vượt trần tháng ⇒
    HetNganSach (không gửi). Số tiêu thật ghi vào sổ chi phí theo `nguon`."""
    p = tham_so(
        noi_dung, he_thong=he_thong, model=model, max_tokens=max_tokens, effort=effort, cache_he_thong=cache_he_thong
    )
    kh = tao_client(client)
    kiem_ngan_sach(uoc_toi_da(p), p["model"], nguon)
    try:
        if p["model"] in MODEL_HIEN_HANH:
            resp = kh.beta.messages.create(betas=[BETA_DU_PHONG], fallbacks="default", **p)
        else:
            resp = kh.messages.create(**p)
    except LoiApi:
        raise
    except Exception as exc:  # lỗi SDK/mạng/401/429 — tên lớp lỗi đủ để chẩn đoán, không in khoá
        raise LoiApi(f"Gọi API thất bại: {type(exc).__name__}: {str(exc)[:200]}") from exc
    u = getattr(resp, "usage", None)
    kq = KetQuaGoi(
        van_ban="".join(getattr(b, "text", "") or "" for b in (getattr(resp, "content", None) or [])),
        model=str(getattr(resp, "model", p["model"]) or p["model"]),
        token_vao=_so_nguyen(getattr(u, "input_tokens", 0)),
        token_ra=_so_nguyen(getattr(u, "output_tokens", 0)),
        stop_reason=getattr(resp, "stop_reason", None),
        token_cache_ghi=_so_nguyen(getattr(u, "cache_creation_input_tokens", 0)),
        token_cache_doc=_so_nguyen(getattr(u, "cache_read_input_tokens", 0)),
    )
    ghi_chi_phi(
        uoc_chi_phi(kq.token_vao, kq.token_ra, p["model"], cache_ghi=kq.token_cache_ghi, cache_doc=kq.token_cache_doc),
        nguon,
        p["model"],
        {"vao": kq.token_vao, "ra": kq.token_ra, "cache_ghi": kq.token_cache_ghi, "cache_doc": kq.token_cache_doc},
    )
    # Lượt bị cắt cụt/từ chối VẪN tính phí ⇒ ghi sổ trước, rồi mới kiểm stop_reason.
    _kiem_stop(kq.stop_reason, getattr(getattr(resp, "stop_details", None), "category", None), max_tokens)
    return kq


def doc_json(van_ban: str) -> Any:
    """JSON từ câu trả lời (chịu được rào ```json). Không đọc được ⇒ KetQuaHong — KHÔNG đoán."""
    s = (van_ban or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    if not s.startswith(("{", "[")):
        dau = min([i for i in (s.find("{"), s.find("[")) if i >= 0], default=-1)
        if dau < 0:
            raise KetQuaHong("Câu trả lời không chứa JSON.")
        s = s[dau:]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        try:
            return json.JSONDecoder().raw_decode(s)[0]  # JSON đúng, theo sau là lời bình — chỉ lấy khối JSON đầu
        except json.JSONDecodeError as exc:
            raise KetQuaHong(f"JSON hỏng: {exc}") from exc


def uoc_token(van_ban: str) -> int:
    """Ước lượng THÔ số token (tiếng Việt có dấu ~3 ký tự/token) — chỉ để chạy khô báo quy mô, không tính tiền thật."""
    return max(1, len(van_ban or "") // 3)


def uoc_chi_phi(
    token_vao: int, token_ra: int, model: str, batch: bool = False, cache_ghi: int = 0, cache_doc: int = 0
) -> Optional[float]:
    """USD theo bảng giá ĐÃ GHI; model chưa có giá ⇒ None (công cụ chỉ báo token). `token_vao` là phần vào KHÔNG qua
    cache (đúng nghĩa `usage.input_tokens`); ghi cache tính HE_SO_GHI_CACHE × giá vào, đọc cache theo «doc_cache»."""
    g = GIA_USD_TRIEU_TOKEN.get(model)
    if not g:
        return None
    he_so = 0.5 if batch else 1.0
    tong = (
        token_vao * g["vao"]
        + cache_ghi * g["vao"] * HE_SO_GHI_CACHE
        + cache_doc * g.get("doc_cache", g["vao"])
        + token_ra * g["ra"]
    )
    return tong * he_so / 1e6


def in_chi_phi(token_vao: int, token_ra: int, model: str, batch: bool = False) -> str:
    usd = uoc_chi_phi(token_vao, token_ra, model, batch)
    duong = "Batch API" if batch else "gọi trực tiếp"
    if usd is None:
        return f"~{token_vao:,} token vào + ~{token_ra:,} token ra ({model}, {duong}; chưa ghi giá model này)"
    return f"~{token_vao:,} token vào + ~{token_ra:,} token ra ≈ {usd:.2f} USD ({model}, {duong})"


def _so_nguyen(x: Any) -> int:
    """Số token từ `usage` (thiếu/None/lạ ⇒ 0) — không để một trường lạ làm sập lượt đã TRẢ TIỀN."""
    try:
        return max(0, int(x or 0))
    except (TypeError, ValueError):
        return 0


def _van_ban_noi_dung(nd: Any) -> Tuple[str, int]:
    """(chữ, số ảnh) của `content`/`system` — chuỗi hoặc danh sách khối."""
    if isinstance(nd, str):
        return nd, 0
    chu, anh = [], 0
    for k in nd or []:
        if isinstance(k, dict):
            if k.get("type") == "image":
                anh += 1
            elif isinstance(k.get("text"), str):
                chu.append(k["text"])
    return "\n".join(chu), anh


def van_ban_he_thong(p: Dict[str, Any]) -> str:
    """Chữ của system prompt trong một bộ tham số, dù là chuỗi hay khối có cache_control."""
    return _van_ban_noi_dung(p.get("system") or "")[0]


def uoc_toi_da(p: Dict[str, Any], batch: bool = False) -> Optional[float]:
    """Chi phí TỐI ĐA của một bộ tham số: token vào ước (chữ + ảnh, KHÔNG trừ cache) + TOÀN BỘ max_tokens ra.
    Dùng để chặn trước khi gửi — luôn lớn hơn hoặc bằng chi phí thật (trừ khi ước token chữ thấp hơn thật)."""
    chu, anh = _van_ban_noi_dung(p.get("system") or "")
    for m in p.get("messages") or []:
        c, a = _van_ban_noi_dung(m.get("content"))
        chu, anh = chu + "\n" + c, anh + a
    return uoc_chi_phi(uoc_token(chu) + anh * TOKEN_UOC_MOI_ANH, int(p.get("max_tokens") or 0), p["model"], batch)


def tran_usd_thang() -> float:
    """Trần USD tháng: biến môi trường EBM_API_CLAUDE_TRAN_USD_THANG > mặc định. Giá trị không đọc được ⇒ 0 (khoá —
    fail-closed: gõ nhầm không được thành «không giới hạn»)."""
    v = os.environ.get("EBM_API_CLAUDE_TRAN_USD_THANG", "").strip()
    if not v:
        return TRAN_USD_THANG_MAC_DINH
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return 0.0


def _thang_nay() -> str:
    import datetime as _dt

    return _dt.date.today().strftime("%Y-%m")


def doc_so_chi_phi(duong: Optional[str] = None) -> Dict[str, Any]:
    """Sổ chi phí tháng hiện hành. Chưa có tệp ⇒ sổ rỗng. Tệp có mà hỏng/sai khuôn ⇒ HetNganSach (không đoán còn tiền,
    không ghi đè). Sang tháng mới ⇒ đếm lại từ 0 (giữ tổng tháng trước ở «thang_truoc»).
    Dưới pytest không đọc tệp THẬT."""
    duong = duong or SO_CHI_PHI
    rong = {"thang": _thang_nay(), "usd": 0.0, "luot": [], "batch_da_ghi": []}
    if _duoi_pytest_cham_that(duong, _SO_CP_THAT):
        return dict(rong, _khong_ghi=True)
    try:
        with open(duong, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except FileNotFoundError:
        return rong
    except (OSError, ValueError) as exc:
        raise HetNganSach(
            f"Sổ chi phí API {duong} không đọc được ({type(exc).__name__}) — không kiểm được trần ⇒ không gọi. "
            "Mở tệp xem lại (OneDrive chưa tải về? sửa tay hỏng?)."
        ) from exc
    if not isinstance(d, dict) or not isinstance(d.get("usd"), (int, float)) or not isinstance(d.get("luot"), list):
        raise HetNganSach(f"Sổ chi phí API {duong} sai khuôn — không kiểm được trần ⇒ không gọi.")
    if d.get("thang") != _thang_nay():
        return dict(rong, thang_truoc={"thang": d.get("thang"), "usd": round(float(d["usd"]), 4)})
    d.setdefault("batch_da_ghi", [])
    return d


def kiem_ngan_sach(uoc_usd: Optional[float], model: str, nguon: str = "", duong: Optional[str] = None) -> None:
    """Chặn TRƯỚC khi gửi: trần ≤ 0, model chưa ghi giá, sổ hỏng, hay đã tiêu + ước tối đa > trần ⇒ HetNganSach."""
    tran = tran_usd_thang()
    if tran <= 0:
        raise HetNganSach(
            "Trần chi phí Claude API tháng đang = 0 (khoá hẳn, hoặc EBM_API_CLAUDE_TRAN_USD_THANG không đọc được) — "
            "không gọi. Mở lại là quyết định của bác sĩ."
        )
    if uoc_usd is None:
        raise HetNganSach(f"Chưa ghi giá model «{model}» — không kiểm được trần chi phí ⇒ không gọi.")
    so = doc_so_chi_phi(duong)
    da = float(so.get("usd") or 0.0)
    if da + uoc_usd > tran:
        raise HetNganSach(
            f"Trần chi phí Claude API tháng {so['thang']}: đã dùng {da:.2f}/{tran:.2f} USD; lượt «{nguon or '?'}» ước "
            f"tối đa {uoc_usd:.2f} USD ⇒ vượt trần, KHÔNG gửi. Nâng trần là quyết định của bác sĩ "
            "(biến môi trường EBM_API_CLAUDE_TRAN_USD_THANG)."
        )


def ghi_chi_phi(
    usd: Optional[float],
    nguon: str,
    model: str,
    token: Dict[str, int],
    batch_id: Optional[str] = None,
    duong: Optional[str] = None,
) -> None:
    """Cộng số tiêu THẬT vào sổ tháng. Batch đã ghi (theo id) ⇒ bỏ qua (không đếm hai lần). Sổ hỏng ⇒ không ghi đè
    (lượt sau sẽ bị chặn ở `kiem_ngan_sach`). Dưới pytest không đụng tệp THẬT. Mọi lỗi ghi đều nuốt."""
    duong = duong or SO_CHI_PHI
    try:
        so = doc_so_chi_phi(duong)
    except HetNganSach:
        return
    if so.pop("_khong_ghi", False):
        return
    if batch_id and batch_id in so["batch_da_ghi"]:
        return
    try:
        import datetime as _dt

        so["usd"] = round(float(so.get("usd") or 0.0) + float(usd or 0.0), 6)
        so["luot"] = (
            so["luot"]
            + [
                {
                    "luc": _dt.datetime.now().isoformat(timespec="seconds"),
                    "nguon": str(nguon)[:80],
                    "model": model,
                    "usd": None if usd is None else round(float(usd), 6),
                    "batch": batch_id,
                    "token": {k: int(v) for k, v in token.items()},
                }
            ]
        )[-200:]
        if batch_id:
            so["batch_da_ghi"] = (so["batch_da_ghi"] + [batch_id])[-200:]
        _ghi_nguyen_tu(duong, so)
    except (OSError, TypeError, ValueError):
        pass


_TRUONG_LUOT = ("luc", "trang_thai", "ly_do", "so_muc")


def gop_theo_nguon(duong: str, ban_ghi: Dict[str, Any]) -> Dict[str, Any]:
    """Trộn lượt mới vào nhật ký đã có: «theo_nguon» giữ lượt gần nhất của TỪNG công cụ; khoá cấp cao = lượt mới.

    VÌ SAO (17/11/2026, bác sĩ duyệt «mục 2»): tệp trước chỉ giữ MỘT lượt — 8 công cụ (5 ở repo này, 3 ở repo gốc) ghi
    chung một ô nên lượt sau xoá lượt trước; công cụ A lỗi 401 rồi công cụ B chạy ổn ngay sau thì lỗi của A biến mất
    trước khi hòm việc kịp đọc. Khoá cấp cao vẫn là lượt gần nhất để bản đọc cũ đọc như trước. Nhật ký kiểu cũ (chưa
    có «theo_nguon») được giữ làm mục của nguồn đã ghi nó. Khuôn trộn có ở BA nơi ghi — đây · repo gốc
    `tools/nhat_ky_api_claude.py` · cổng skill `check_topic_relevance.py` (mỗi nơi phải tự đứng, không nhập chung
    được) — sửa một nơi phải sửa cả ba; repo gốc có chốt đối chiếu khuôn khi hai repo nằm cạnh nhau."""
    try:
        with open(duong, "r", encoding="utf-8") as fh:
            cu = json.load(fh)
    except (OSError, ValueError):
        cu = None
    theo: Dict[str, Any] = {}
    if isinstance(cu, dict):
        tn = cu.get("theo_nguon")
        if isinstance(tn, dict):
            theo = {str(k): v for k, v in tn.items() if isinstance(v, dict)}
        elif cu.get("trang_thai"):
            theo[str(cu.get("nguon") or "")] = {k: cu.get(k) for k in _TRUONG_LUOT}
    theo[str(ban_ghi.get("nguon") or "")] = {k: ban_ghi.get(k) for k in _TRUONG_LUOT}
    return dict(ban_ghi, theo_nguon=theo)


def _ghi_nguyen_tu(duong: str, du_lieu: Dict[str, Any]) -> None:
    """Ghi qua tệp tạm rồi đổi tên: hai công cụ ghi cùng lúc không bao giờ để lại tệp cụt nửa chừng."""
    tam = f"{duong}.{os.getpid()}.tmp"
    try:
        with open(tam, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(du_lieu, fh, ensure_ascii=False, indent=1)
        os.replace(tam, duong)
    finally:
        if os.path.exists(tam):
            try:
                os.remove(tam)
            except OSError:
                pass


def ghi_nhat_ky_api(
    trang_thai: str, ly_do: str = "", so_muc: int = 0, nguon: str = "", tep: Optional[str] = None
) -> None:
    """Ghi kết quả lượt gọi gần nhất (theo từng công cụ — `gop_theo_nguon`) cho giác quan hòm việc.

    Lỗi ghi đều nuốt; dưới pytest không đụng tệp THẬT."""
    duong = tep or NHAT_KY_API
    if _duoi_pytest_cham_that(duong, _NK_THAT):
        return
    try:
        import datetime as _dt

        ban_ghi = {
            "luc": _dt.datetime.now().isoformat(timespec="seconds"),
            "trang_thai": str(trang_thai),
            "ly_do": str(ly_do)[:200],
            "so_muc": int(so_muc),
            "nguon": str(nguon)[:80],
        }
        _ghi_nguyen_tu(duong, gop_theo_nguon(duong, ban_ghi))
    except (OSError, TypeError, ValueError):
        pass


# ── Batch API ─────────────────────────────────────────────────────────────────────────────────────────────────────
def kiem_custom_id(cid: str) -> str:
    if not _CUSTOM_ID.match(cid or ""):
        raise LoiCucBo(f"custom_id «{cid}» sai luật Batch API (chữ/số/_/-, ≤ 64 ký tự)")
    return cid


def nop_batch(yeu_cau: Sequence[Tuple[str, Dict[str, Any]]], client: Any = None, nguon: str = "") -> str:
    """Nộp MỘT batch, trả id. `yeu_cau` = [(custom_id, tham_so(...))]; custom_id trùng/sai luật ⇒ LoiApi, không gửi.
    Ước TỐI ĐA cả batch (giá Batch) vượt trần tháng ⇒ HetNganSach, không gửi."""
    if not yeu_cau:
        raise LoiCucBo("Batch rỗng — không có gì để nộp.")
    ids = [kiem_custom_id(c) for c, _ in yeu_cau]
    if len(set(ids)) != len(ids):
        raise LoiCucBo("custom_id trùng trong batch.")
    kh = tao_client(client)
    uoc = [uoc_toi_da(p, batch=True) for _, p in yeu_cau]
    kiem_ngan_sach(None if any(x is None for x in uoc) else sum(uoc), yeu_cau[0][1]["model"], nguon)
    try:
        b = kh.messages.batches.create(requests=[{"custom_id": c, "params": p} for c, p in yeu_cau])
    except Exception as exc:
        raise LoiApi(f"Nộp batch thất bại: {type(exc).__name__}: {str(exc)[:200]}") from exc
    return str(b.id)


def trang_thai_batch(batch_id: str, client: Any = None) -> Dict[str, Any]:
    kh = tao_client(client)
    b = kh.messages.batches.retrieve(batch_id)
    rc = getattr(b, "request_counts", None)
    return {
        "id": batch_id,
        "trang_thai": getattr(b, "processing_status", "?"),
        "dang_xu_ly": getattr(rc, "processing", 0),
        "xong": getattr(rc, "succeeded", 0),
        "loi": getattr(rc, "errored", 0),
        "het_han": getattr(rc, "expired", 0),
        "huy": getattr(rc, "canceled", 0),
    }


def doc_ket_qua_batch(batch_id: str, client: Any = None, nguon: str = "") -> Dict[str, Dict[str, Any]]:
    """custom_id → kết quả gọn (cùng khuôn `doc_ket_qua` của repo gốc). Số tiêu thật của cả batch (giá Batch, gồm
    token cache) ghi vào sổ chi phí MỘT lần theo id batch."""
    kh = tao_client(client)
    ket: Dict[str, Dict[str, Any]] = {}
    model = ""
    for r in kh.messages.batches.results(batch_id):
        loai = r.result.type
        if loai == "succeeded":
            m = r.result.message
            u = getattr(m, "usage", None)
            ket[r.custom_id] = {
                "loai": loai,
                "stop_reason": m.stop_reason,
                "nhom": getattr(getattr(m, "stop_details", None), "category", None),
                "text": "".join(getattr(b, "text", "") or "" for b in m.content),
                "vao": _so_nguyen(getattr(u, "input_tokens", 0)),
                "ra": _so_nguyen(getattr(u, "output_tokens", 0)),
                "cache_ghi": _so_nguyen(getattr(u, "cache_creation_input_tokens", 0)),
                "cache_doc": _so_nguyen(getattr(u, "cache_read_input_tokens", 0)),
            }
            model = model or str(getattr(m, "model", "") or "")
        else:
            loi = getattr(getattr(r.result, "error", None), "type", "") or ""
            ket[r.custom_id] = {"loai": loai, "loi": str(loi)}
    tok = {k: sum(int(v.get(k, 0)) for v in ket.values()) for k in ("vao", "ra", "cache_ghi", "cache_doc")}
    if any(tok.values()):
        mdl = model or MODEL_MAC_DINH
        usd = uoc_chi_phi(
            tok["vao"], tok["ra"], mdl, batch=True, cache_ghi=tok["cache_ghi"], cache_doc=tok["cache_doc"]
        )
        ghi_chi_phi(usd, nguon, mdl, tok, batch_id=batch_id)
    return ket


def van_ban_ket_qua_batch(kq: Dict[str, Any], max_tokens: int = MAX_TOKENS_MAC_DINH) -> str:
    """Văn bản của MỘT kết quả batch sau khi kiểm loại + stop_reason; hỏng ⇒ KetQuaHong."""
    if kq.get("loai") != "succeeded":
        raise KetQuaHong(f"batch: {kq.get('loai')} {kq.get('loi', '')}".strip())
    _kiem_stop(kq.get("stop_reason"), kq.get("nhom"), max_tokens)
    return str(kq.get("text") or "")


# ── Tiện ích văn bản dùng chung ───────────────────────────────────────────────────────────────────────────────────
def chuan_hoa(s: str) -> str:
    """Chuẩn để so «trích nguyên văn»: thường hoá, gộp khoảng trắng, đồng nhất gạch nối/nháy."""
    s = (s or "").lower()
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = re.sub(r"\*\*|__|`", "", s)
    return re.sub(r"\s+", " ", s).strip(" .;:,")


def co_nguyen_van(trich: str, van_ban: str) -> bool:
    """Trích có thật trong văn bản (sau chuẩn hoá)? Trích rỗng ⇒ False. Chặn kiểu «trích» do model tự viết."""
    t = chuan_hoa(trich)
    return bool(t) and t in chuan_hoa(van_ban)


def chia_lo(ds: Sequence[Any], co: int) -> List[List[Any]]:
    co = max(1, int(co))
    return [list(ds[i : i + co]) for i in range(0, len(ds), co)]


DISCLAIMER = "TƯ VẤN của máy (Claude API) — không mở, không chặn cổng, không thay người đọc. Cần bác sĩ kiểm chứng."
