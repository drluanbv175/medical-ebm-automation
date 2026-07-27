"""Hồi quy cổng G0 — 4 lỗi làm G0 TRƯỢT kiểm định độc lập ngày 2026-07-27.

Bối cảnh quan trọng để người đọc sau hiểu đúng: những lỗi dưới đây KHÔNG có sẵn trong hệ —
chúng do CHÍNH bản vá G0 sáng cùng ngày tạo ra (bản vá mở nhánh "nghiên cứu quan sát" và
thêm đếm số hit thật). Bản vá đó tự test xanh, ruff sạch, và được tuyên bố "hoàn thiện";
một vòng kiểm định độc lập sau đó chấm ĐẠT 15 / CHƯA ĐẠT 38.

Bài học ghi lại: "test xanh + lint sạch + chạy thử một lần" KHÔNG đủ để tuyên bố một cổng
đạt chuẩn. Riêng lỗi (1) khiến cổng chuyển từ CHẶN sang QUA — tức bản vá làm hệ NGUY HIỂM
HƠN trước, chứ không phải chỉ chưa đủ tốt.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_g0_auto as G0  # noqa: E402

from app.sources.pubmed import PubMedClient  # noqa: E402

PYTHON = sys.executable


def test_counts_are_real_requires_every_branch_not_just_one():
    """LỖI (2): dùng any() nên chỉ cần MỘT nhánh tra được số thật là cả báo cáo bị dán nhãn
    "số hit THẬT" — kể cả khi nhánh khác timeout (rate-limit HTTP 429 xảy ra thật khi kiểm
    định) và lùi về len([]) = 0.

    Tái hiện gốc: nhánh sr_ma timeout trên "outpatient satisfaction hospital" → in
    "SR/MA: 0 … (số hit THẬT từ PubMed)" trong khi sự thật là 203 → evidence_level tụt từ
    "MẠNH" xuống "CÓ HẠN" kèm khẳng định SAI "Chưa có systematic review". Một số 0 BỊA được
    dán nhãn THẬT là kiểu sai nguy hiểm nhất ở cổng này."""
    res = {
        "sr_ma": [], "rct": [], "guideline": [], "observational": [], "recent": [],
        "true_counts": {"sr_ma": None, "rct": 1080, "guideline": 5,
                        "observational": 2989, "recent": 335},
    }
    gaps = G0.analyze_evidence_gaps(res, "outpatient satisfaction hospital")
    assert gaps["counts_are_real"] is False, "một nhánh hỏng mà vẫn dán nhãn 'số hit THẬT'"
    assert "sr_ma" in gaps["counts_unavailable"], "phải nêu đích danh nhánh không tra được"


def test_counts_are_real_true_only_when_all_branches_resolved():
    """Đối chứng: mọi nhánh tra được thì mới được nhận nhãn THẬT (không chặn oan)."""
    res = {
        "sr_ma": [], "rct": [], "guideline": [], "observational": [], "recent": [],
        "true_counts": {"sr_ma": 203, "rct": 1080, "guideline": 5,
                        "observational": 2989, "recent": 335},
    }
    gaps = G0.analyze_evidence_gaps(res, "x")
    assert gaps["counts_are_real"] is True
    assert gaps["counts_unavailable"] == []


def test_count_hits_returns_none_not_zero_on_error_payload(monkeypatch):
    """LỖI (4): `.get("count", 0)` mặc định 0 khi THIẾU khóa — fail-OPEN ngay tại hàm mà lý
    do tồn tại là "phân biệt KHÔNG BIẾT với BẰNG 0". E-utilities trả
    {"esearchresult": {"ERROR": ...}} khi truy vấn hỏng; khi đó 0 nghĩa là "không tra được",
    KHÔNG phải "không có bài nào" — và 0 sẽ được diễn giải thành "khoảng trống nghiên cứu"."""
    import app.sources.pubmed as PM

    client = PubMedClient()
    client.use_mock = False
    monkeypatch.setattr(PM.settings, "ncbi_email", "test@example.com", raising=False)
    for payload in ({"esearchresult": {"ERROR": "Empty term and query_key - nothing todo"}},
                    {},
                    {"esearchresult": None}):
        monkeypatch.setattr(client.http, "get_json", lambda *a, **k: payload)
        assert client.count_hits("bat ky") is None, f"payload {payload} phải cho None, không phải 0"


def test_empty_topic_is_blocked_not_completed(tmp_path):
    """LỖI (3): `--topic ""` làm truy vấn thành "() AND (bộ lọc)" → PubMed trả 1.139.330 hit
    → G0 liệt kê 50 bài KHÔNG LIÊN QUAN dưới tiêu đề "BẰNG CHỨNG HIỆN CÓ (THẬT)", guardrail
    in ✅ PASS, exit 0. Một cổng khởi đầu nghiên cứu không được phép báo "hoàn thành" khi
    chưa có đề tài. Test này chạy OFFLINE — chặn phải xảy ra TRƯỚC mọi lời gọi mạng."""
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "USE_MOCK_SOURCES": "true"}
    for topic in ("", "   "):
        r = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g0_auto.py"), "--study", "PYTEST-G0-EMPTY",
             "--topic", topic],
            cwd=tmp_path, capture_output=True, text=True, timeout=120, env=env)
        assert r.returncode == 2, f"topic={topic!r} phải DỪNG (exit 2), nhận {r.returncode}"
        assert "DỪNG" in r.stdout
        # Kiểm ĐÚNG biểu ngữ thành công, không phải chữ "HOÀN THÀNH" bất kỳ —
        # chính thông điệp chặn có nhắc lại cụm đó khi giải thích lỗi cũ.
        assert "✅ G0 HOÀN THÀNH" not in r.stdout


def test_observational_evidence_is_written_not_just_counted():
    """★ LỖI (1) — NẶNG NHẤT, và là lỗi do chính bản vá buổi sáng gây ra.

    Nhánh quan sát ĐƯỢC ĐẾM nhưng KHÔNG BAO GIỜ được ghi ra artifact A1 hay
    G0_pubmed_raw.json. Đối chiếu thật trên cùng chủ đề/cùng máy: bản trước → "🚧 G0 DỪNG:
    0 PMID", exit 2; bản sau → "R1 ✅ 13 PMIDs thật", exit 0, trong khi
    `grep -c "PMID:"` trên artifact = 0 và artifact in "→ Không tìm thấy bài nào trên
    PubMed" ngay dưới câu "PMIDs đã được xác minh".

    ⇒ Cổng chuyển từ CHẶN sang QUA nhờ bằng chứng bác sĩ KHÔNG nhìn thấy và KHÔNG kiểm
    chứng được — vi phạm trực tiếp bất biến "mọi đầu ra kèm PMID để bác sĩ kiểm chứng".

    Test này kiểm ĐƯỜNG GHI (không gọi mạng): nhánh observational phải có mặt trong cả
    artifact lẫn raw JSON."""
    src = (TOOLS_DIR / "run_g0_auto.py").read_text(encoding="utf-8")
    assert 'obs_list = _format_article_list(results.get("observational", []))' in src, \
        "artifact A1 không dựng danh sách bài quan sát"
    assert "### 3.5 Nghiên cứu QUAN SÁT" in src, "artifact A1 thiếu mục hiển thị bài quan sát"
    assert '"observational": [{"pmid"' in src, "G0_pubmed_raw.json không lưu nhánh quan sát"


def test_observational_count_is_labelled_as_overlapping():
    """Con số "Quan sát: N" là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN với RCT/SR (đo
    thật: 389/2989 ≈ 13% cũng là RCT, 16 cũng là SR/MA). Phải nói rõ, không để bác sĩ hiểu
    đó là số nghiên cứu quan sát thuần."""
    src = (TOOLS_DIR / "run_g0_auto.py").read_text(encoding="utf-8")
    assert "CÓ CHỒNG LẤN" in src, "chưa cảnh báo con số quan sát bị chồng lấn"


def test_raw_json_records_true_counts_for_audit():
    """Số hit thật phải lưu được để bác sĩ/người phản biện đối chiếu về sau."""
    src = (TOOLS_DIR / "run_g0_auto.py").read_text(encoding="utf-8")
    assert '"true_counts": results.get("true_counts", {})' in src
