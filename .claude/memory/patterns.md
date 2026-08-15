# Patterns (SSOT — Layer 2)

> Cách làm/gotcha tái sử dụng được của `medical-ebm-automation`, thăng cấp từ auto-memory Layer 1.
> Mỗi mục là "HOW" (phòng tái phát lỗi, mẫu giải pháp). Lý do "WHY" nằm ở `decisions.md`.

---

## P1: Launcher phải tự suy đường dẫn trong OneDrive và ưu tiên venv

**Date**: 2026-06-07
**Updated**: 2026-06-18
**Tags**: #pattern #macos #windows #onedrive #launcher #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Launcher GUI/launchd dễ gãy khi hardcode đường dẫn OneDrive của một máy (`/Users/.../Claude AI/...`) hoặc ép `arch -arm64` trên môi trường không cần/không có lệnh đó. Trước đây việc ép `arch -arm64` giúp tránh lỗi Rosetta trên một máy Apple Silicon, nhưng khi đồng bộ Mac↔Windows/Codex↔Claude Code thì hardcode này làm giảm tính di động.

### Solution
Launcher nằm trong repo phải tự suy `PROJ` từ vị trí file:

```bash
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
```

Ưu tiên Python của venv ngoài OneDrive nếu có, rồi fallback sang `python3/python`:

```bash
PY="$HOME/.ebm-venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || command -v python)"
fi
```

Gọi bằng `"$PY" ...`. Chỉ ép `arch -arm64` khi đã xác nhận launcher chạy dưới Rosetta trên riêng máy đó; không đưa hardcode này vào launcher dùng chung.

### Application Conditions
Mọi entry point GUI/launchd/script nằm trong `medical-ebm-automation/` và được đồng bộ qua OneDrive.

### Non-Application Conditions
Script cá nhân chỉ dùng trên một máy có thể có wrapper riêng, nhưng không commit hardcode máy cá nhân vào repo.

### Notes
Nếu gặp lỗi kiến trúc numpy/pandas trên Mac Apple Silicon, xử lý ở venv/cách mở terminal trước; chỉ thêm `arch -arm64` vào wrapper cá nhân khi thật sự cần.

---

## P2: Verify dashboard Streamlit phải mở SESSION thật, không dùng curl

**Date**: 2026-06-06
**Tags**: #pattern #streamlit #verification #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
`curl` HTTP 200 KHÔNG đủ để xác minh dashboard chạy đúng: Streamlit chỉ chạy script lúc websocket connect, nên grep log sau curl trần là vô nghĩa.

### Solution
Verify bằng `streamlit.testing.v1.AppTest` (kích hoạt script thật). Hoặc mở session thật rồi kiểm `data/archive/dashboard.log` có dòng "Uncaught app execution" không.

### Application Conditions
Bất cứ khi nào cần xác minh dashboard/tab chạy không lỗi.

### Non-Application Conditions
Không có (curl không thay thế được cho mục tiêu này).

### Example
`from streamlit.testing.v1 import AppTest` → chạy app → assert không exception, đúng số widget mong đợi.

### Notes
Đã dùng AppTest cho test tab TikTok, preview_manual, v.v.

---

## P3: Tên file dashboard là `main.py`, KHÔNG đặt `app.py`

**Date**: 2026-06-06
**Tags**: #pattern #streamlit #packaging #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Đặt entry dashboard là `app.py` trùng tên package `app/` → `ModuleNotFoundError: 'app' is not a package` khi streamlit chạy.

### Solution
Dashboard ở `app/dashboard/main.py`. `run.py` + app launcher trỏ tới `main.py`.

### Application Conditions
Khi tạo/đổi tên entry point Streamlit trong dự án có package tên `app/`.

### Notes
Đây là lỗi import dễ tái phát khi refactor.

---

## P4: Làm sạch abstract — gỡ thẻ TRƯỚC rồi unescape entity; bỏ CJK song ngữ trùng lặp

**Date**: 2026-06-06
**Tags**: #pattern #text-cleaning #i18n #ebm
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
(1) Abstract PMC/EuropePMC/CTgov chứa thẻ `<sec><st><p>`, `<abstracttext label>`, `<A HREF>` + entity `&ge;`/`&le;`/`&lt;`; hiển thị thô và dịch máy dịch nhầm thẻ (`</sec>`→"</giây>").
(2) Tạp chí TQ có abstract Anh+Trung trùng lặp → dịch `source="en"` sinh rác lặp.

### Solution
`app/utils/text.py::clean_text(text, structured=True)`: gỡ thẻ (giữ chữ trong `<a>`), chuyển `<st>`/`label` thành tiêu đề mục đọc được, rồi `html.unescape`. THỨ TỰ quan trọng: gỡ thẻ TRƯỚC, unescape SAU → "p&lt;0.05" an toàn thành "p<0.05" mà không bị nhận nhầm là thẻ.
`strip_secondary_cjk()`: nếu có tiếng Anh đáng kể (latin≥60 và latin≥0.5×CJK) thì bỏ phần CJK trùng; nếu chủ yếu Trung thì giữ để dịch ZH→VI.
Dịch dùng `source="auto"` + `_is_degenerate()` loại bản dịch lặp.

### Application Conditions
`normalization.normalize()` (abstract structured=True; title+safety_signal structured=False) + lúc render dashboard.

### Notes
Khi sửa logic, chạy `tests/test_clean_text.py` (gỡ thẻ, decode entity, song ngữ bỏ Trung/giữ Anh, _is_degenerate). Khi đổi schema làm sạch — nhớ cleanup in-place các bản ghi DB cũ.

---

## P5: Pattern URL RSS đã verify chạy / nhà cung cấp chặn bot

**Date**: 2026-06-06
**Tags**: #pattern #rss #sources
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Cần biết pattern URL RSS nào chạy được và nhà cung cấp nào chặn bot để khỏi thêm feed lỗi.

### Solution
Pattern chạy:
- BMJ family: `https://<journal>.bmj.com/rss/current.xml`
- Springer: `link.springer.com/search.rss?query=&facet-journal-id=<id>`
- Atypon: `showFeed?type=etoc&feed=rss&jc=<code>` (NEJM/JAMA OK)

Chặn bot (403, đừng thêm): AHA/ATS/AGA qua Atypon; ESC/Eur Heart J, AHA Circulation, ATS, ERS, Lancet, WHO, EMA, NICE, Cochrane, ACP, Gastroenterology(AGA).

### Application Conditions
Khi mở rộng `GUIDELINE_FEEDS`. FDA chặn UA bot → connector phải dùng UA giống trình duyệt.

### Notes
Luôn verify live HTTP 200 + XML trước khi thêm. Nguồn bị chặn → lấy qua PubMed (xem decisions.md D5).

---

## P6: Sửa file dashboard bằng script Python replace (assert count), không chỉ Edit

**Date**: 2026-06-06
**Tags**: #pattern #editing #onedrive #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
`main.py`/`run.py`/`config.py` bị linter/OneDrive re-save liên tục → Edit hay báo "modified since read".

### Solution
Vá bằng script Python replace với `assert count == 1` (đảm bảo thay đúng 1 chỗ) cho chắc.

### Application Conditions
Khi sửa các file hay bị OneDrive/linter chạm vào trong lúc làm việc.

### Notes
Giảm rủi ro sửa nhầm/nhiều chỗ ngoài ý muốn.

---

## P7: Trích NGUYÊN VĂN abstract — mọi câu là substring nguồn (chống bịa)

**Date**: 2026-06-06
**Tags**: #pattern #ebm #data-integrity #extraction
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Phải đảm bảo điểm chính/điểm mấu chốt hiển thị (thẻ lâm sàng, slide TikTok) không bị paraphrase/bịa.

### Solution
`app/services/extraction.py`: `extract_conclusion()` ưu tiên mục nhãn Conclusion/Interpretation qua `_sections`, fallback câu chứa cue ("we conclude/these findings suggest"), fallback câu cuối; `_best_result()` ưu tiên câu CÓ SỐ/thống kê và đúng loại (tránh nhặt nhầm câu "we aimed to"). Tất cả verbatim + nhãn dịch.

### Application Conditions
Thẻ "Điểm mấu chốt" (`render_clinical_application`), slide TikTok (`app/social/content.py` tái dùng extraction).

### Notes
Test khóa đảm bảo mọi câu EN trên slide/thẻ là substring của abstract gốc. Khi guideline không có abstract → fallback dùng trường THẬT đã lưu (safety_signal/thong_tin_moi/practice_impact), không tự sinh.

---

## P8: Font tiếng Việt cho render ảnh — chỉ vài font hỗ trợ đúng dấu

**Date**: 2026-06-06
**Tags**: #pattern #rendering #pillow #i18n #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Render slide bằng Pillow: nhiều font không có glyph emoji (→ ô vuông) hoặc mất dấu tiếng Việt.

### Solution
- Slide thường: font `Arial Unicode.ttf`; BỎ emoji khi vẽ (emoji vẫn giữ trong caption/markdown).
- Phong cách whiteboard: tiêu đề `Brush Script.ttf`, thân `ChalkboardSE.ttc` — CHỈ 2 font viết tay macOS này render đúng dấu tiếng Việt (Comic Sans/Bradley Hand/Chalkduster bị mất dấu, đã test).

### Application Conditions
`app/social/render.py` và các render whiteboard.

### Notes
Có fallback an toàn nếu thiếu Pillow (chỉ xuất text).

---

## P9: TTS tiếng Việt — edge-tts (cần mạng) fallback macOS `say` (offline)

**Date**: 2026-06-06
**Tags**: #pattern #tts #video #offline-fallback
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
Cần giọng đọc tiếng Việt cho video, vừa mềm vừa có fallback offline.

### Solution
`app/social/video.py::_synth`: ưu tiên `edge-tts` (giọng `vi-VN-HoaiMyNeural`, rate −8%, cần MẠNG) → fallback macOS `say -v Linh` (offline). Ghép video bằng ffmpeg tĩnh trong gói `imageio-ffmpeg` (`get_ffmpeg_exe()`, không cần ffmpeg hệ thống). Lời đọc làm suôn qua `_speak_clean` (135/85→"135 trên 85", "/"→"và", bỏ ≥≤) + `_sentence` (mỗi ý 1 câu kết bằng dấu để neural ngắt nghỉ).

### Application Conditions
Tạo video TikTok có giọng đọc.

### Non-Application Conditions
Thiếu say/ffmpeg → `available()` False → bỏ video, vẫn xuất ảnh (an toàn).

### Notes
Lời đọc = đúng văn bản VI đã hiển thị (bỏ emoji), không thêm nội dung. Config: `TIKTOK_TTS_ENGINE`(auto|edge|say), `TIKTOK_EDGE_VOICE`, `TIKTOK_EDGE_RATE`.

---

## P10: Nhập 45 thang điểm NGUYÊN VĂN từ HTML người dùng (chống bịa)

**Date**: 2026-06-06
**Tags**: #pattern #clinical-scores #data-integrity
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
45 thang điểm phải giữ nguyên nội dung người dùng biên soạn, không tự sinh/bịa hệ số.

### Solution
`app/clinical_scores/reference_import.py`: parse bằng bs4 các thẻ `<article class="card" id="tool-NN">` từ file HTML → JSON `data/reference/clinical_scores_45.json` (giữ CSS gốc + HTML từng thẻ + nhóm theo `<h3 class="group">`), lưu bản sao nguồn `data/reference/source/`. Render chi tiết qua `st.components.v1.html` (iframe + CSS gốc).

### Application Conditions
Tab 7 dashboard; có mục "CẬP NHẬT" để nhập lại khi guideline đổi.

### Notes
Test `tests/test_reference_import.py` đảm bảo tên thang điểm là substring nguồn. Công cụ độc quyền (ASCVD/SCORE2/MELD) ghi rõ dùng calculator chính thức, không bịa hệ số.

---

## P11: Nạp abstract từ DB khi đóng gói TikTok (weekly_ebm không mang abstract)

**Date**: 2026-06-06
**Tags**: #pattern #social #data-flow #gotcha
**Observation ID**: memory/project-medical-ebm-automation.md

### Problem
`weekly_ebm._row()` KHÔNG mang theo abstract → slide TikTok thiếu nội dung để trích.

### Solution
`app/social/package.py` phải `_enrich_with_db_fields` (nạp abstract từ DB) trước khi dựng slide. Lọc bỏ chuỗi chấm điểm nội bộ (`Evidence=`, `PracticeChange=`, `Tier X`) khỏi slide công khai.

### Application Conditions
Mọi đường tạo gói TikTok từ dữ liệu weekly.

### Notes
Quên enrich → slide guideline rỗng; nhớ fallback safety_signal/thong_tin_moi/practice_impact khi không có abstract.

---

## P12: Re-score dữ liệu cũ khi luật scoring đổi

**Tags**: #pattern #scoring #data #phase4

### Problem
Đổi luật scoring chỉ áp cho lần quét mới; bản ghi cũ giữ phân loại cũ.

### Solution
`scripts/rescore.py` (DRY-RUN mặc định, `--apply` để ghi). Tái dùng `pipeline.score_item` + `filtering.classify` trên INPUT_FIELDS (không mang điểm/tier cũ). LUÔN backup DB (`data/archive/`) trước `--apply`; dry-run để xem tác động trước.

### Application Conditions
Mỗi lần đổi luật ở `app/scoring/*` hoặc `filtering.py`.

### Notes
Backup `.db` đặt trong `data/archive/` (đã gitignore). Dashboard đọc DB live → refresh là thấy.

---

## P13: Lint — sửa lỗi thật, per-file-ignore E501 cho file dữ liệu/template

**Tags**: #pattern #lint #phase4

### Problem
Codebase nhiều chuỗi tiếng Việt dài ⇒ E501 nhiễu; nhưng lỗi logic (import/biến thừa, semicolon) là thật.

### Solution
`ruff.toml`: line-length 120 + `[lint.per-file-ignores]` E501 cho file NỘI DUNG (`verified.py`, `_fixtures.py`, `package.py`). Lỗi thực (F/E702/E741) sửa thật, không ignore. Mục tiêu `ruff check` = 0.

### Application Conditions
Khi thêm rule lint hoặc thêm file dữ liệu/template có chuỗi dài hợp lệ.
