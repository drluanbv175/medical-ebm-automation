"""Hồi quy (vòng audit đối kháng 2026-07-16, round 3): guardrail_check_g0()/guardrail_check_g1()
rule R2 (chặn PII trong artifact) so khớp literal `p in artifact.lower()` với các nhãn tiếng
Việt có dấu ('họ tên', 'ngày sinh', 'số hồ sơ'...) liệt kê ở dạng tổ hợp sẵn (NFC). Artifact ở
dạng NFD (chữ cái nền + dấu tổ hợp rời — cùng hiển thị, khác chuỗi mã, vd dán từ một số nguồn
macOS) khớp trượt hoàn toàn TRƯỚC bản vá, khiến R2 báo "✅ Không có PII" (không lỗi/cảnh báo) dù
artifact còn PII thật. Đây là guardrail THẬT chạy trong pipeline G0/G1 (không phải mô phỏng).
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g0_auto as g0  # noqa: E402
import run_g1_auto as g1  # noqa: E402


def _r2_errors(check_result: dict) -> list[str]:
    return [e for e in check_result["errors"] if e.startswith("R2")]


def test_g0_guardrail_r2_catches_pii_in_nfc_and_nfd_form():
    nfc_text = "Báo cáo G0 hợp lệ, có đủ PMID. Ghi chú: họ tên bệnh nhân đã bị lộ."
    nfd_text = unicodedata.normalize("NFD", nfc_text)

    result_nfc = g0.guardrail_check_g0(nfc_text, {"all_pmids": ["12345678"]})
    result_nfd = g0.guardrail_check_g0(nfd_text, {"all_pmids": ["12345678"]})

    assert _r2_errors(result_nfc), "R2 phải bắt PII ở dạng NFC"
    assert _r2_errors(result_nfd), "R2 phải bắt PII ở dạng NFD (trước bản vá: bỏ sót hoàn toàn)"


def test_g1_guardrail_r2_catches_pii_in_nfc_and_nfd_form():
    nfc_text = "Đề cương G1 hợp lệ. Ghi chú: ngày sinh bệnh nhân đã bị ghi nhầm vào đây."
    nfd_text = unicodedata.normalize("NFD", nfc_text)

    result_nfc = g1.guardrail_check_g1(nfc_text, {})
    result_nfd = g1.guardrail_check_g1(nfd_text, {})

    assert _r2_errors(result_nfc), "R2 phải bắt PII ở dạng NFC"
    assert _r2_errors(result_nfd), "R2 phải bắt PII ở dạng NFD (trước bản vá: bỏ sót hoàn toàn)"


def test_g0_guardrail_r2_passes_clean_artifact():
    clean = "Báo cáo G0 hợp lệ, có đủ PMID, không có thông tin định danh nào."
    result = g0.guardrail_check_g0(clean, {"all_pmids": ["12345678"]})
    assert not _r2_errors(result)
    assert any(w.startswith("R2") and "✅" in w for w in result["warnings"])
