"""Template dashboard VENDORED của engine không được trôi khỏi bản chuẩn của repo gốc. 14/10/2026.

VÌ SAO. `app/reports/evidence_workbench._tpl()` LUÔN ưu tiên bản vendored `dashboard_mockups/templates/`
(V4.3.2.1 — `git archive` tự chứa); bản này được track nên Mac lẫn Cloud đều dựng dashboard bằng nó, rồi
xuất `EBM-Dashboards/WebDashboard_EBM_VanDeCuThe_*` — đúng glob mà `build_antifacts.py` quét lên hub.
Rà đồng bộ 14/10 đo được: hai bản vendored đổi lần cuối ở 3e94b0d (12/09), trước các bản vá 16/09 của
bản chuẩn — KHÔNG có `escHtml`/`escUrl`/`escJs` (đếm 0 so với 44/36 ở bản chuẩn), thiếu tab
standards/sourceHierarchy/robEntries. Không chốt nào so bản này: bộ 4 bản đồng bộ byte của gốc chỉ gồm
dashboard_mockups gốc, EBM_MASTER và 2 bản skill. Đường khai thác THẬT (kiểm bằng Chromium): `clean_text`
gỡ thẻ rồi `html.unescape`, nên tiêu đề nguồn mang thẻ mã hoá entity (`&lt;img onerror…&gt;`) thành thẻ
thật trong DATA; template cũ chèn thẳng vào innerHTML ⇒ onerror CHẠY (EW 3 lần, DA 2 lần); template
chuẩn ⇒ 0.

Hai lớp: (1) LUÔN chạy (cả CI đơn-repo): bản vendored phải có các hàm thoát HTML/URL/JS; (2) chạy khi
tìm thấy repo gốc EBM: bản vendored phải TRÙNG BYTE bản chuẩn
`sync/skills/cap-nhat-chung-cu-y-khoa/templates/web-dashboard-*.html`. Sửa khi đỏ: chép bản chuẩn của
gốc đè lên bản vendored (marker DATA giống nhau nên `render_html` vẫn tương thích).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
VENDORED = REPO / "dashboard_mockups" / "templates"
# tên vendored (engine) → tên bản chuẩn trong skill của repo gốc
CAP = {
    "evidence-workbench-template.html": "web-dashboard-evidence-workbench.html",
    "dark-analyst-template.html": "web-dashboard-dark-analyst.html",
}
HAM_THOAT = ("function escHtml", "function escUrl", "function escJs")


def _nap(ten: str, duong: Path):
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("ten", sorted(CAP))
def test_template_vendored_co_lop_thoat_html_url_js(ten):
    noi_dung = (VENDORED / ten).read_text(encoding="utf-8")
    thieu = [h for h in HAM_THOAT if h not in noi_dung]
    assert not thieu, (f"{ten} thiếu {thieu} — dashboard dựng từ bản này chèn chuỗi nguồn thẳng vào innerHTML (XSS). "
                       "Chép bản chuẩn sync/skills/cap-nhat-chung-cu-y-khoa/templates/ của repo gốc đè lên.")
    assert "const DATA" in noi_dung and "HẾT KHỐI DATA" in noi_dung, f"{ten} mất marker DATA — render_html sẽ hỏng"


@pytest.mark.parametrize("ten", sorted(CAP))
def test_template_vendored_trung_byte_ban_chuan_cua_goc(ten):
    goc_ebm = _nap("goc_ebm_test_template_20261014", REPO / "tools" / "goc_ebm.py")
    goc = goc_ebm.tim_goc_ebm(REPO)
    chuan = goc / "sync" / "skills" / "cap-nhat-chung-cu-y-khoa" / "templates" / CAP[ten]
    if not (goc_ebm.la_goc_ebm(goc) and chuan.is_file()):
        pytest.skip("không tìm thấy repo gốc EBM (CI đơn-repo; đặt EBM_REPO_ROOT để bật) — lớp 1 vẫn canh hàm thoát")
    assert (VENDORED / ten).read_bytes() == chuan.read_bytes(), (
        f"dashboard_mockups/templates/{ten} lệch bản chuẩn {chuan} — chép bản chuẩn đè lên bản vendored.")
