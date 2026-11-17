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
# Giá Sonnet 5.5 ($2 vào / $10 ra mỗi triệu token; Batch = 50%) — số repo gốc ghi từ tài liệu Claude API đọc
# 17/11/2026 (`tools/quet_lac_chu_de_kho.py`). Model khác: CHƯA ghi giá ⇒ chỉ báo token, không bịa tiền.
GIA_USD_TRIEU_TOKEN = {"claude-sonnet-5-5": {"vao": 2.00, "ra": 10.00}}
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
) -> Dict[str, Any]:
    """Tham số Messages API cho MỘT lời gọi — dùng chung cho gọi trực tiếp và Batch API (Batch không nhận `fallbacks`
    nên phần đó thêm riêng ở `goi`)."""
    if effort not in ("low", "medium", "high", "xhigh", "max"):
        raise LoiCucBo(f"effort «{effort}» không hợp lệ")
    mdl = chon_model(model)
    p: Dict[str, Any] = {
        "model": mdl,
        "max_tokens": int(max_tokens),
        "messages": [{"role": "user", "content": noi_dung}],
    }
    if he_thong:
        p["system"] = he_thong
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
) -> KetQuaGoi:
    """MỘT lời gọi Messages API. Lỗi mạng/khoá/SDK ⇒ LoiApi; cắt cụt/từ chối ⇒ KetQuaHong."""
    p = tham_so(noi_dung, he_thong=he_thong, model=model, max_tokens=max_tokens, effort=effort)
    kh = tao_client(client)
    try:
        if p["model"] in MODEL_HIEN_HANH:
            resp = kh.beta.messages.create(betas=[BETA_DU_PHONG], fallbacks="default", **p)
        else:
            resp = kh.messages.create(**p)
    except LoiApi:
        raise
    except Exception as exc:  # lỗi SDK/mạng/401/429 — tên lớp lỗi đủ để chẩn đoán, không in khoá
        raise LoiApi(f"Gọi API thất bại: {type(exc).__name__}: {str(exc)[:200]}") from exc
    _kiem_stop(
        getattr(resp, "stop_reason", None), getattr(getattr(resp, "stop_details", None), "category", None), max_tokens
    )
    u = getattr(resp, "usage", None)
    return KetQuaGoi(
        van_ban="".join(getattr(b, "text", "") or "" for b in (getattr(resp, "content", None) or [])),
        model=str(getattr(resp, "model", p["model"]) or p["model"]),
        token_vao=int(getattr(u, "input_tokens", 0) or 0),
        token_ra=int(getattr(u, "output_tokens", 0) or 0),
        stop_reason=getattr(resp, "stop_reason", None),
    )


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


def uoc_chi_phi(token_vao: int, token_ra: int, model: str, batch: bool = False) -> Optional[float]:
    """USD theo bảng giá ĐÃ GHI; model chưa có giá ⇒ None (công cụ chỉ báo token)."""
    g = GIA_USD_TRIEU_TOKEN.get(model)
    if not g:
        return None
    he_so = 0.5 if batch else 1.0
    return (token_vao * g["vao"] + token_ra * g["ra"]) * he_so / 1e6


def in_chi_phi(token_vao: int, token_ra: int, model: str, batch: bool = False) -> str:
    usd = uoc_chi_phi(token_vao, token_ra, model, batch)
    duong = "Batch API" if batch else "gọi trực tiếp"
    if usd is None:
        return f"~{token_vao:,} token vào + ~{token_ra:,} token ra ({model}, {duong}; chưa ghi giá model này)"
    return f"~{token_vao:,} token vào + ~{token_ra:,} token ra ≈ {usd:.2f} USD ({model}, {duong})"


def ghi_nhat_ky_api(
    trang_thai: str, ly_do: str = "", so_muc: int = 0, nguon: str = "", tep: Optional[str] = None
) -> None:
    """Ghi kết quả lượt gọi gần nhất cho giác quan hòm việc. Lỗi ghi đều nuốt; dưới pytest không đụng tệp THẬT."""
    duong = tep or NHAT_KY_API
    if _duoi_pytest_cham_that(duong, _NK_THAT):
        return
    try:
        import datetime as _dt

        with open(duong, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(
                {
                    "luc": _dt.datetime.now().isoformat(timespec="seconds"),
                    "trang_thai": str(trang_thai),
                    "ly_do": str(ly_do)[:200],
                    "so_muc": int(so_muc),
                    "nguon": str(nguon)[:80],
                },
                fh,
                ensure_ascii=False,
                indent=1,
            )
    except (OSError, TypeError, ValueError):
        pass


# ── Batch API ─────────────────────────────────────────────────────────────────────────────────────────────────────
def kiem_custom_id(cid: str) -> str:
    if not _CUSTOM_ID.match(cid or ""):
        raise LoiCucBo(f"custom_id «{cid}» sai luật Batch API (chữ/số/_/-, ≤ 64 ký tự)")
    return cid


def nop_batch(yeu_cau: Sequence[Tuple[str, Dict[str, Any]]], client: Any = None) -> str:
    """Nộp MỘT batch, trả id. `yeu_cau` = [(custom_id, tham_so(...))]; custom_id trùng/sai luật ⇒ LoiApi, không gửi."""
    if not yeu_cau:
        raise LoiCucBo("Batch rỗng — không có gì để nộp.")
    ids = [kiem_custom_id(c) for c, _ in yeu_cau]
    if len(set(ids)) != len(ids):
        raise LoiCucBo("custom_id trùng trong batch.")
    kh = tao_client(client)
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


def doc_ket_qua_batch(batch_id: str, client: Any = None) -> Dict[str, Dict[str, Any]]:
    """custom_id → kết quả gọn (cùng khuôn `doc_ket_qua` của repo gốc)."""
    kh = tao_client(client)
    ket: Dict[str, Dict[str, Any]] = {}
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
                "vao": getattr(u, "input_tokens", 0) or 0,
                "ra": getattr(u, "output_tokens", 0) or 0,
            }
        else:
            loi = getattr(getattr(r.result, "error", None), "type", "") or ""
            ket[r.custom_id] = {"loai": loai, "loi": str(loi)}
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
