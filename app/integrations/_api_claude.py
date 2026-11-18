"""Lối gọi Claude API cho tích hợp của app (ambient scribe, đọc ảnh) qua cầu nối chung `tools/api_claude_nc.py`.

VÌ SAO (17/11/2026, bác sĩ: «làm mục 1 và 2»). Hai tích hợp viết từ 23/08/2026 tự gọi SDK theo kiểu riêng; đo ra
ba hở:
- Model mặc định đã cũ (`claude-sonnet-4-6`, `claude-opus-4-8`) trong khi cả hệ đã sang Sonnet 5.5 / Opus 5.5.
- Không kiểm `stop_reason`: `max_tokens=1500` mà model hiện hành luôn suy nghĩ và tính phần suy nghĩ VÀO
  `max_tokens` ⇒ câu trả lời có thể bị cắt cụt rồi được đọc như bản nháp hoàn chỉnh (SOAP thiếu mục P, bản đọc
  ECG thiếu cờ đỏ) mà không ai hay.
- Không ghi nhật ký sức khoẻ `~/.ebm-api-claude.json` ⇒ giác quan hòm việc (`giac_quan_api_claude`, repo gốc)
  mù với hai đường này: khoá hết tín dụng đúng lúc dùng thì bác sĩ chỉ thấy lỗi trên màn hình, hòm việc không báo.

Mô-đun này KHÔNG viết luật mới: mượn nguyên luật của cầu nối chung (khoá theo §5 qua kho bí mật, cấm khách thật
và tệp thật dưới pytest, kiểm cắt cụt/từ chối, model dự phòng phía máy chủ) rồi đổi lỗi sang lớp lỗi riêng của
từng tích hợp để mã gọi (bảng tích hợp Streamlit, CLI) không phải sửa. Nội dung gửi đi vẫn do tích hợp tự khử
định danh TRƯỚC khi gọi.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Optional, Type

_TOOLS = Path(__file__).resolve().parents[2] / "tools"

# Model mặc định theo việc: viết SOAP từ transcript đủ với Sonnet; đọc ảnh (ECG/X-quang) cần thị giác tốt nhất ⇒ Opus.
MODEL_SOAP = "claude-sonnet-5-5"
MODEL_ANH = "claude-opus-5-5"


def cau_noi() -> Any:
    """Nạp `tools/api_claude_nc.py` (repo y khoa không đóng gói `tools/` thành package)."""
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    return importlib.import_module("api_claude_nc")


def goi_claude(
    noi_dung: Any,
    *,
    nguon: str,
    loi: Type[Exception],
    model: Optional[str],
    bien_model: str,
    model_mac_dinh: str,
    max_tokens: Optional[int] = None,
    effort: str = "low",
    client: Any = None,
) -> str:
    """MỘT lượt gọi qua cầu nối chung; trả văn bản đầy đủ hoặc ném `loi` (KHÔNG bao giờ trả nửa câu trả lời).

    Ghi sức khoẻ lượt gọi đúng luật của cầu nối (cùng cách các công cụ hệ nghiên cứu ghi):
    thiếu khoá ⇒ skipped · kết quả cắt cụt/từ chối ⇒ ok kèm lý do (khoá vẫn dùng được) · lỗi kênh API ⇒ error ·
    lỗi phía máy (tham số sai) ⇒ không ghi · thành công ⇒ ok."""
    api = cau_noi()
    mdl = model or os.environ.get(bien_model) or model_mac_dinh
    try:
        kq = api.goi(
            noi_dung,
            model=mdl,
            max_tokens=int(max_tokens or api.MAX_TOKENS_MAC_DINH),
            effort=effort,
            client=client,
            nguon=nguon,
        )
    except api.ThieuKhoa as exc:
        api.ghi_nhat_ky_api("skipped", str(exc), 0, nguon)
        raise loi(str(exc)) from exc
    except api.LoiCucBo as exc:
        raise loi(str(exc)) from exc
    except api.KetQuaHong as exc:
        api.ghi_nhat_ky_api("ok", f"kết quả hỏng: {exc}", 0, nguon)
        raise loi(f"Không dùng được câu trả lời của Claude: {exc}") from exc
    except api.LoiApi as exc:
        api.ghi_nhat_ky_api("error", str(exc), 0, nguon)
        raise loi(str(exc)) from exc
    api.ghi_nhat_ky_api("ok", "", 1, nguon)
    return kq.van_ban
