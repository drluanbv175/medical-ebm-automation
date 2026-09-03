# -*- coding: utf-8 -*-
"""Hồi quy phát hiện #5 của Workflow đối kháng đa-agent (2026-09-03):

14 agent doctrine LÂM SÀNG khai `--artifact <khóa>` bằng khóa KHÔNG tồn tại
trong ARTIFACT_MAP — cùng lớp lỗi "mất định danh cổng, rơi về generic GX" đã
vá ở vòng 11/15/16/vòng rà 6, lần này bị bỏ sót vì 14 agent này (quan-ly-
khang-dong.md, theo-doi-benh-man.md, dau-man-tinh.md, tram-cam-lo-au.md,
tham-dinh-do-chinh-xac-chan-doan.md, tham-dinh-grade-nnt.md, khai-thac-benh-
su-kham.md, dien-giai-can-lam-sang.md, ke-don-an-toan.md, cham-soc-giam-
nhe.md, pico-lam-sang.md, du-phong-tam-soat.md, chan-doan-xac-suat.md,
thang-diem-nguy-co.md) được thêm vào đội SAU các đợt vá trước — không đợt
nào trong số đó quét lại TOÀN BỘ .claude/agents/*.md để bắt khóa mới.

Đo bằng grep thật (không dùng danh sách bịa): 43 khóa `--artifact <x>` được
tham chiếu trên toàn repo; đối chiếu ARTIFACT_MAP tại thời điểm phát hiện
(39 khóa) ra 16 "thiếu", nhưng 2 trong số đó là false positive:
  - "exports" (binh-duyet.md) — đây là `--artifact exports/<tên>/...md` của
    approve_gate.py (CLI khác, tham số đường dẫn file, không phải khóa của
    gen_research_docx.py).
  - "bilingual-editing" (hieu-dinh-song-ngu.md) — dòng đó là ghi chú LỊCH SỬ
    tự khai đã BỎ khóa này (2026-07-11), không phải một lệnh mẫu đang sống.
Còn lại đúng 14 khóa thật, tất cả đều thuộc agent HỖ TRỢ CA NGOẠI TRÚ, chỉ
ĐỀ XUẤT ở Cổng A (mỗi file đã xác nhận tường minh câu "chỉ ĐỀ XUẤT (Cổng
A)"), gắn mã CA5..CA18 tiếp nối CA4.

Theo đúng đề xuất của Workflow: thay vì chỉ hồi quy 14 khóa đã biết (dễ lặp
lại chính lỗi này — thêm agent mới mà quên khóa), lớp `TestNoOrphanArtifactKeyAcrossDoctrine`
quét ĐỘNG mọi `--artifact ([\\w-]+)` trong .claude/agents/*.md ở lần chạy và
assert từng khóa (trừ 2 false-positive đã xác minh ở trên, cùng "exports"
lặp lại nhiều dòng trong artifact-path pattern của approve_gate) nằm trong
ARTIFACT_MAP — bắt được đợt agent MỚI thêm khóa MỚI trong tương lai mà không
cần sửa lại file test này.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gen_research_docx as G  # noqa: E402

# Dùng LẠI bộ dò đường dẫn canonical đã có (V4.3.2.1, xem
# tests/test_offline_workflow_integration.py TC-15B) thay vì tự tính lại:
# thử `.claude/agents` vendored TRONG repo trước, rồi mới lùi về thư mục cha
# (trường hợp 2 repo được checkout làm anh em, đúng cấu trúc môi trường dev
# hiện tại) — khớp đúng cách skipif của TC-15B để không đỏ trên CI checkout
# đơn-repo (medical-ebm-automation .github/workflows/offline-ci.yml chỉ
# `actions/checkout@v4` chính repo này, không có repo gốc làm anh em).
from runtime.agent_registry import AGENTS_DIR  # noqa: E402

# Khóa đã xác minh KHÔNG phải tham chiếu sống tới ARTIFACT_MAP của
# gen_research_docx.py (xem docstring ở trên) — loại khỏi phép quét động.
KNOWN_FALSE_POSITIVES = {
    "exports",             # approve_gate.py --artifact <đường-dẫn>, CLI khác
    "bilingual-editing",   # ghi chú lịch sử "đã bỏ khóa này", không phải lệnh sống
}

NEW_KEYS_AND_CODES = [
    ("anticoagulation-plan", "CA5"),
    ("chronic-disease", "CA6"),
    ("chronic-pain", "CA7"),
    ("depression-anxiety", "CA8"),
    ("diagnostic-accuracy-appraisal", "CA9"),
    ("grade-etd", "CA10"),
    ("history-exam", "CA11"),
    ("lab-interpretation", "CA12"),
    ("medication-safety", "CA13"),
    ("palliative-care", "CA14"),
    ("pico-clinical", "CA15"),
    ("prevention-screening", "CA16"),
    ("probabilistic-dx", "CA17"),
    ("risk-score", "CA18"),
]


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    return d


class TestFinding5FourteenNewClinicalKeys:
    def test_each_new_key_present_in_artifact_map_with_gate_a(self):
        for key, code in NEW_KEYS_AND_CODES:
            assert key in G.ARTIFACT_MAP, f"{key} thiếu trong ARTIFACT_MAP"
            got_code, got_gate, _title = G.ARTIFACT_MAP[key]
            assert got_code == code, f"{key}: kỳ vọng mã {code}, thấy {got_code}"
            assert got_gate == "A", (
                f"{key}: cả 14 agent nguồn đều tự khai 'chỉ ĐỀ XUẤT (Cổng A)' "
                f"— thấy gate={got_gate!r}"
            )

    def test_each_new_key_generates_with_correct_code_not_generic(self, capsys):
        for key, code in NEW_KEYS_AND_CODES:
            d = _study_dir(f"TEST-WF20260903-{key.upper()}")
            try:
                gen = G.ResearchDocxGenerator(study_name=d.name)
                path = gen.generate(key, {})
                assert re.search(rf"{re.escape(code)}_{re.escape(key.upper())}_", path, re.IGNORECASE), (
                    f"{key} không sinh đúng mã {code}: {path}"
                )
                captured = capsys.readouterr()
                assert "ngoài danh mục nghiên cứu chuẩn" not in captured.out, (
                    f"{key} vẫn rơi vào fallback generic (cảnh báo còn xuất hiện)"
                )
            finally:
                _rmtree_retry(d)

    def test_no_code_collision_introduced_by_the_14_new_keys(self):
        codes = [v[0] for v in G.ARTIFACT_MAP.values()]
        assert len(codes) == len(set(codes)), "Có mã artifact_code bị trùng trong ARTIFACT_MAP"


@pytest.mark.skipif(
    not AGENTS_DIR.exists(),
    reason=(
        "Cần .claude/agents/ (vendored trong repo, hoặc repo gốc làm anh em "
        "— xem runtime.agent_registry.AGENTS_DIR). CI checkout đơn-repo của "
        "medical-ebm-automation không có thư mục này; test này CHỈ chạy khi "
        "cả hai repo cùng có mặt (đúng như 'PASS' của tools/verify_claude_"
        "code_repo_alignment.py chỉ tính được trên máy có đủ 2 repo)."
    ),
)
class TestNoOrphanArtifactKeyAcrossDoctrine:
    """Quét ĐỘNG toàn bộ .claude/agents/*.md — không hardcode danh sách khóa,
    nên bắt được cả agent MỚI thêm SAU đợt vá này mà quên đăng ký khóa,
    đúng đề xuất sửa lỗi của Workflow đối kháng đa-agent."""

    def test_every_referenced_artifact_key_exists_in_artifact_map(self):
        pattern = re.compile(r"--artifact ([\w-]+)")
        referenced: dict[str, set[str]] = {}
        for md in sorted(AGENTS_DIR.glob("*.md")):
            text = md.read_text(encoding="utf-8", errors="ignore")
            for key in pattern.findall(text):
                referenced.setdefault(key, set()).add(md.name)

        missing = {
            key: files
            for key, files in referenced.items()
            if key not in G.ARTIFACT_MAP and key not in KNOWN_FALSE_POSITIVES
        }
        assert not missing, (
            "Khóa --artifact được agent doctrine tham chiếu nhưng KHÔNG có "
            f"trong ARTIFACT_MAP (sẽ rơi vào fallback generic 'GX'): {missing}"
        )


class TestKnownFalsePositivesStayValid:
    """Không phụ thuộc AGENTS_DIR — luôn chạy được kể cả trên CI đơn-repo.
    Nếu một trong hai false-positive VÔ TÌNH được thêm vào ARTIFACT_MAP sau
    này (vd trùng tên với khóa mới), danh sách loại trừ của phép quét động ở
    trên sẽ che mất một khóa thật — chốt này canh điều đó."""

    def test_known_false_positives_are_still_genuinely_not_map_keys(self):
        for key in KNOWN_FALSE_POSITIVES:
            assert key not in G.ARTIFACT_MAP, (
                f"'{key}' đã có mặt trong ARTIFACT_MAP — gỡ khỏi "
                f"KNOWN_FALSE_POSITIVES vì nó không còn là false positive."
            )
