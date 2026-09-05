"""trial_registry.py — TRA ĐĂNG KÝ NGHIÊN CỨU (ClinicalTrials.gov API v2). DÙNG CHUNG G0 + G2.

★ VÌ SAO GỘP (2026-07-28): trước file này, hệ có HAI đường code tra cùng một API:

  1. `run_g0_auto.py::check_trial_registry()` — gọi qua `HttpClient` (requests), có
     `countTotal`, có `filter.overallStatus`, và có hợp đồng liêm chính rõ ràng:
     tra thất bại → `checked=False`, KHÔNG bao giờ biến thành số 0.
  2. `run_g2_auto.py::search_clinicaltrials()` — bản `urllib` tự viết riêng, KHÔNG
     đếm tổng, KHÔNG phân biệt "đã tra, không có" với "không tra được", và gửi lên
     TRUY VẤN TIẾNG VIỆT BỎ DẤU (bóc dấu bằng regex, không dịch) nên gần như luôn
     trả 0 kết quả.

  Hậu quả ĐO ĐƯỢC THẬT ngày 2026-07-28 với đề tài "Sự hài lòng của người bệnh ngoại
  trú tại Khoa Khám bệnh": G2 gửi `"long nguoi benh ngoai"` → totalCount = 0; cùng
  lúc `base_query` tiếng Anh mà G0 ĐÃ tính và ĐÃ ghi sẵn vào `G0_checkpoint.json`
  (`"outpatient patient satisfaction hospital"`) → totalCount = 1422, trong đó 241 hồ
  sơ đang tuyển. Hồ sơ đạo đức G2 vì thế in "Không tìm thấy thử nghiệm tương tự" và
  Hội đồng Đạo đức đọc thành "chưa ai làm" — một khẳng định SAI về prior art.

  Đường `urllib` còn thua ở một điểm vận hành: nó dùng ngữ cảnh SSL mặc định của
  Python, nên chết ngay (`CERTIFICATE_VERIFY_FAILED`) sau proxy chặn TLS, trong khi
  `HttpClient` (requests + certifi) vẫn đi được — xác minh trên chính máy này.

★ LIÊM CHÍNH — HỢP ĐỒNG 3 TRẠNG THÁI (bất biến của file này):
  - `checked=False`                → CHƯA TRA ĐƯỢC (mất mạng/timeout/chế độ mock/bị
    bỏ qua). TUYỆT ĐỐI không được hiển thị giống "không có nghiên cứu trùng".
  - `checked=True,  n_trials == 0` → ĐÃ TRA THẬT, không có hồ sơ nào khớp.
  - `checked=True,  n_trials  > 0` → ĐÃ TRA THẬT, có prior art (kèm danh sách NCT).

  Hai trạng thái đầu nhìn giống nhau trên giấy nhưng khác nhau hoàn toàn trước Hội
  đồng Đạo đức: một cái là bằng chứng, một cái là chưa có bằng chứng.

★ VỀ `app/sources/clinicaltrials.py`: vẫn KHÔNG dùng ở đây, có chủ ý — client dùng
  chung không trả `overallStatus` (trạng thái tuyển bệnh mới trả lời được câu "có ai
  ĐANG làm không") lẫn `totalCount`. Sửa client đó sẽ đụng mọi nơi khác đang dùng nó.
  Nếu sau này nó được mở rộng, hãy gộp nốt đường này vào đó.

Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CTG_STUDIES_API = "https://clinicaltrials.gov/api/v2/studies"
# Ba trạng thái nghĩa là "chưa thu xong người tham gia" → một đề tài trùng ở đây
# sẽ công bố trước khi đề tài mới kịp thu số liệu.
CTG_ACTIVE_STATUSES = "RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION"

# Nhãn dùng CHUNG cho trạng thái "không tra được". Mọi nơi hiển thị đều phải dùng
# đúng chuỗi này để bác sĩ/Hội đồng nhận ra ngay, và để test hồi quy neo vào được.
NOT_CHECKED_LABEL = "CHƯA TRA ĐƯỢC"


def empty_registry(query: str = "", error: str = "chưa tra") -> dict:
    """Kết quả rỗng ĐÚNG HỢP ĐỒNG: `checked=False`, `n_trials=None` (KHÔNG phải 0)."""
    return {
        "registry": "ClinicalTrials.gov",
        "query": query,
        "checked": False,
        "n_trials": None,
        "n_active": None,
        "trials": [],
        "error": error,
        "checked_at": None,
    }


def check_trial_registry(base_query: str, max_results: int = 5) -> dict:
    """Tra ClinicalTrials.gov: câu hỏi này đã có ai ĐANG TIẾN HÀNH / ĐÃ ĐĂNG KÝ chưa?

    Miễn phí, không cần API key (ClinicalTrials.gov API v2 — xác minh thật ngày
    2026-07-28: `query.term` + `countTotal` + `filter.overallStatus` phân tách bằng
    dấu phẩy đều trả HTTP 200).

    `base_query` PHẢI là truy vấn TIẾNG ANH (khóa `base_query` trong
    `G0_checkpoint.json`). ClinicalTrials.gov đánh chỉ mục tiếng Anh — đưa chủ đề
    tiếng Việt (kể cả đã bỏ dấu) vào đây là bảo đảm 0 kết quả giả tạo.

    LIÊM CHÍNH: không tra được (mất mạng/chế độ mock/HTTP lỗi) thì trả
    `checked=False` kèm lý do — TUYỆT ĐỐI không im lặng coi như "không có ai làm",
    vì im lặng ở đây đọc ra thành một khẳng định sai có hậu quả thật.
    """
    out = empty_registry(base_query)
    out["checked_at"] = datetime.now().isoformat(timespec="seconds")
    if not (base_query or "").strip():
        out["error"] = "truy vấn rỗng"
        return out

    try:
        from app.config import settings
        if getattr(settings, "use_mock_sources", False):
            out["error"] = "USE_MOCK_SOURCES=true — bỏ qua tra đăng ký (không bịa dữ liệu)"
            return out
        # Import BÊN TRONG hàm là có chủ ý: test hồi quy patch
        # `app.utils.http.HttpClient` để mô phỏng mạng hỏng; import ở đầu module sẽ
        # khoá cứng lớp thật vào biến module-level và làm phép patch đó vô hiệu.
        from app.utils.http import HttpClient
        http = HttpClient()

        data = http.get_json(CTG_STUDIES_API, params={
            "query.term": base_query,
            "pageSize": max_results,
            "countTotal": "true",
            "format": "json",
        })
        out["n_trials"] = data.get("totalCount")

        for st in (data.get("studies") or [])[:max_results]:
            ps = st.get("protocolSection", {}) or {}
            ident = ps.get("identificationModule", {}) or {}
            status_mod = ps.get("statusModule", {}) or {}
            design_mod = ps.get("designModule", {}) or {}
            cond_mod = ps.get("conditionsModule", {}) or {}
            nct = ident.get("nctId")
            out["trials"].append({
                "nct_id": nct,
                "title": (ident.get("briefTitle") or ident.get("officialTitle") or "")[:180],
                "status": status_mod.get("overallStatus"),
                "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
                "phases": design_mod.get("phases"),
                "study_type": design_mod.get("studyType"),
                "conditions": ", ".join((cond_mod.get("conditions") or [])[:3]),
                "enrollment": (design_mod.get("enrollmentInfo") or {}).get("count"),
                "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
            })

        active = http.get_json(CTG_STUDIES_API, params={
            "query.term": base_query,
            "pageSize": 1,
            "countTotal": "true",
            "format": "json",
            "filter.overallStatus": CTG_ACTIVE_STATUSES,
        })
        out["n_active"] = active.get("totalCount")
        out["checked"] = isinstance(out["n_trials"], int)
    except Exception as e:  # noqa: BLE001 — mọi lỗi đều phải thành "CHƯA TRA", không thành 0
        out["error"] = f"{type(e).__name__}: {e}"
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 23, phát hiện #4):
        # hàm gọi API 2 lần tuần tự — `n_trials` (dòng ~115) được gán NGAY
        # từ lệnh gọi ĐẦU, trước khi lệnh gọi THỨ HAI (dòng ~136, lấy
        # n_active) chạy. Nếu lệnh gọi thứ hai raise (mất mạng/timeout giữa
        # chừng), nhánh except này chạy nhưng `n_trials`/`trials` đã có giá
        # trị THẬT từ lệnh gọi đầu — vi phạm đúng hợp đồng mà chính
        # empty_registry() khai: "checked=False → n_trials PHẢI là None
        # (không phải một số)". Reset về đúng trạng thái "chưa tra" của
        # empty_registry() để `out` không rơi vào trạng thái nội tại mâu
        # thuẫn (checked=False nhưng n_trials có giá trị thật).
        out["n_trials"] = None
        out["n_active"] = None
        out["trials"] = []
    if out["checked"]:
        out["error"] = None
    return out


def registry_search_url(query: str) -> str:
    """Link để bác sĩ/Hội đồng TỰ tra lại đúng truy vấn hệ đã dùng (tái lặp được)."""
    return f"https://clinicaltrials.gov/search?term={quote_plus(query or '')}"


# ════════════════════════════════════════════════════════════════════════════
# TRÌNH BÀY — mỗi hàm dưới đây phải phân biệt ĐỦ 3 TRẠNG THÁI của hợp đồng
# ════════════════════════════════════════════════════════════════════════════

def format_trial_list(trials: list, max_show: int = 5) -> str:
    """Danh sách gạch đầu dòng (kiểu G0). Chỉ nhận `trials`, không biết `checked`."""
    if not trials:
        return "  → Không có hồ sơ đăng ký nào khớp truy vấn\n"
    lines = []
    for i, t in enumerate(trials[:max_show]):
        phases = ", ".join(t.get("phases") or []) or "—"
        lines.append(
            f"  {i+1}. [{t.get('status') or '?'}] {t.get('title') or '(không tiêu đề)'}\n"
            f"     {t.get('nct_id') or 'NCT: ?'} | Pha: {phases} | "
            f"Cỡ mẫu dự kiến: {t.get('enrollment') if t.get('enrollment') is not None else '?'} | "
            f"Bắt đầu: {t.get('start_date') or '?'}\n"
            f"     URL: {t.get('url') or 'N/A'}"
        )
    return "\n".join(lines) + "\n"


def format_prior_art_table(registry: Optional[dict], max_show: int = 8) -> str:
    """Khối prior art cho hồ sơ G2 — BA trạng thái, BA cách hiển thị khác hẳn nhau."""
    registry = registry or {}
    query = registry.get("query") or ""
    if not registry.get("checked"):
        return (
            f"> ⚠️ **{NOT_CHECKED_LABEL} ClinicalTrials.gov** — lý do: "
            f"{registry.get('error') or 'không rõ'}.\n"
            "> **KHÔNG được đọc mục này thành \"chưa có ai làm đề tài này\".** Hệ thống "
            "chưa có bằng chứng nào về prior art, chứ không phải đã tra và thấy trống.\n"
            f"> Chạy lại khi có mạng, hoặc tự tra rồi dán kết quả vào đây: "
            f"{registry_search_url(query) if query else 'https://clinicaltrials.gov/search'}\n"
        )

    n_trials = registry.get("n_trials") or 0
    n_active = registry.get("n_active")
    checked_at = str(registry.get("checked_at") or "")[:10]
    head = (
        f"> ✅ **ĐÃ TRA THẬT ngày {checked_at or '?'}** trên ClinicalTrials.gov API v2 "
        f"với truy vấn `{query}` — **{n_trials} hồ sơ khớp**"
        + (f", trong đó **{n_active} đang/sắp tuyển**" if isinstance(n_active, int) else "")
        + f". Tra lại: {registry_search_url(query)}\n"
    )
    if n_trials == 0:
        return head + (
            "> Đây là kết quả tra THẬT (khác hẳn "
            f"\"{NOT_CHECKED_LABEL}\"): không có hồ sơ đăng ký nào khớp truy vấn này.\n"
            "> Lưu ý: ClinicalTrials.gov không bao phủ mọi đăng ký — WHO ICTRP, PROSPERO "
            "(nếu SR/MA) và đăng ký trong nước vẫn cần bác sĩ tự tra.\n"
        )

    rows = []
    for t in (registry.get("trials") or [])[:max_show]:
        start = t.get("start_date") or "?"
        rows.append(
            f"| {t.get('nct_id') or '?'} | {(t.get('title') or '')[:70]} | "
            f"{t.get('status') or '?'} | "
            f"{t.get('enrollment') if t.get('enrollment') is not None else '?'} | "
            f"{start[:4]} | {', '.join(t.get('phases') or []) or '—'} |"
        )
    table = (
        "| NCT ID | Tên nghiên cứu | Trạng thái | Cỡ mẫu | Năm | Phase |\n"
        "|--------|---------------|-----------|--------|-----|-------|\n"
        + "\n".join(rows) + "\n"
    )
    return head + "\n" + table


def format_prior_art_refs(registry: Optional[dict], max_show: int = 3) -> str:
    """Dòng "Tham chiếu NCT" — cũng phải phân biệt CHƯA TRA với ĐÃ TRA, 0 hồ sơ."""
    registry = registry or {}
    if not registry.get("checked"):
        return f"[{NOT_CHECKED_LABEL} — chưa có bằng chứng prior art]"
    trials = registry.get("trials") or []
    if not trials:
        return "[Đã tra thật: 0 hồ sơ đăng ký khớp truy vấn]"
    return " · ".join(
        f"[{t.get('nct_id')}]({t.get('url')})" for t in trials[:max_show] if t.get("nct_id")
    ) or "[Đã tra thật: 0 hồ sơ đăng ký khớp truy vấn]"


def checkpoint_block(registry: Optional[dict], max_samples: int = 5) -> dict:
    """Khối MÁY ĐỌC ĐƯỢC để ghi vào checkpoint — giữ nguyên 3 trạng thái.

    `n_trials=None` (chứ không phải 0) khi `checked=False`: mọi consumer đọc
    checkpoint phải phân biệt được "chưa tra" với "tra rồi, không có".
    """
    registry = registry or {}
    checked = bool(registry.get("checked"))
    query = registry.get("query") or ""
    return {
        "registry": registry.get("registry") or "ClinicalTrials.gov",
        "checked": checked,
        "query": query,
        "n_trials": registry.get("n_trials") if checked else None,
        "n_active": registry.get("n_active") if checked else None,
        "error": None if checked else (registry.get("error") or "không rõ"),
        "checked_at": registry.get("checked_at"),
        "search_url": registry_search_url(query),
        # Việc bác sĩ phải làm, để ở ĐÂY chứ không ở `pending_doctor_actions` của
        # checkpoint: khóa đó bị `g2_quality_gate.refresh_checkpoint()` ghi đè hoàn
        # toàn bằng `pending_actions` của hợp đồng chất lượng ngay sau khi
        # `write_g2_checkpoint()` chạy, nên mọi mục thêm vào đó đều là mã chết.
        "pending_action": None if checked else (
            f"{NOT_CHECKED_LABEL} — chạy lại G2 khi có mạng, hoặc tự tra tại "
            f"{registry_search_url(query)} và dán kết quả vào mục prior art trước "
            "khi nộp Hội đồng Đạo đức"
        ),
        "samples": [
            {"nct_id": t.get("nct_id"), "title": (t.get("title") or "")[:80],
             "status": t.get("status"), "url": t.get("url")}
            for t in (registry.get("trials") or [])[:max_samples]
        ],
    }


def console_summary(registry: Optional[dict]) -> list[str]:
    """Dòng in ra màn hình — cùng 3 trạng thái, để bác sĩ thấy ngay lúc chạy."""
    registry = registry or {}
    if not registry.get("checked"):
        return [
            f"  ⚠ {NOT_CHECKED_LABEL}: {registry.get('error') or 'không rõ lý do'}",
            "     (KHÔNG được đọc thành 'không có nghiên cứu trùng')",
        ]
    n_trials = registry.get("n_trials")
    n_active = registry.get("n_active")
    lines = [f"  → Đã tra thật: {n_trials} hồ sơ khớp, {n_active} đang/sắp tuyển"]
    for t in (registry.get("trials") or [])[:3]:
        lines.append(f"     • {t.get('nct_id')} | {(t.get('title') or '')[:60]} | {t.get('status')}")
    if n_trials == 0:
        lines.append("     (đã tra THẬT và không có hồ sơ nào khớp — khác 'chưa tra được')")
    return lines
