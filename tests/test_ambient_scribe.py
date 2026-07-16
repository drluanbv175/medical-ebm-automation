"""Test ambient scribe STT→SOAP (offline — không mạng, không cần faster-whisper/anthropic).

Phủ: cổng đồng thuận · khử PII (cấu trúc + tên theo ngữ cảnh) · dựng prompt · parse SOAP ·
pipeline với LLM stub · disclaimer · lưới an toàn 2 lớp.
"""
from __future__ import annotations

import unicodedata

import pytest

from app.integrations.ambient_scribe import (
    DISCLAIMER,
    AmbientError,
    blank_soap,
    build_soap_prompt,
    from_audio,
    parse_soap,
    scrub_pii,
    transcribe,
    transcript_to_soap,
)


# -- Khử PII ----------------------------------------------------------------
def test_scrub_pii_structural():
    raw = ("Liên hệ 0912345678, email an.nguyen@example.com, "
           "CCCD 012345678901, sinh năm 1974. Đau ngực 3 ngày.")
    clean, n = scrub_pii(raw)
    assert "0912345678" not in clean
    assert "an.nguyen@example.com" not in clean
    assert "012345678901" not in clean
    assert "1974" not in clean
    assert "Đau ngực 3 ngày" in clean  # nội dung lâm sàng được giữ
    assert n >= 4


def test_scrub_pii_name_by_cue():
    raw = "Bệnh nhân tên Nguyễn Văn An, nam, than đau đầu."
    clean, _ = scrub_pii(raw)
    assert "Nguyễn Văn An" not in clean
    assert "[ĐÃ ẨN]" in clean
    assert "đau đầu" in clean


def test_scrub_pii_catches_name_in_nfd_unicode_form():
    """Hồi quy: transcript dán từ macOS dictation/Notes có thể ở dạng NFD (chữ cái nền +
    dấu tổ hợp rời) thay vì NFC (tổ hợp sẵn) mà _NAME_CUE/_PII_PATTERNS liệt kê. Trước bản vá,
    scrub_pii() "mù" hoàn toàn với input NFD — tên bệnh nhân thật lọt nguyên vẹn vào prompt gửi
    LLM ngoài (0 lần ẩn, không lỗi/cảnh báo)."""
    raw_nfc = "Bệnh nhân tên Nguyễn Văn An, nam, than đau đầu."
    raw_nfd = unicodedata.normalize("NFD", raw_nfc)
    clean_nfc, n_nfc = scrub_pii(raw_nfc)
    clean_nfd, n_nfd = scrub_pii(raw_nfd)
    assert n_nfc >= 1 and n_nfd >= 1
    assert "Nguyễn Văn An" not in clean_nfc
    assert "Nguyễn Văn An" not in unicodedata.normalize("NFC", clean_nfd)
    assert "[ĐÃ ẨN]" in clean_nfd


def test_scrub_pii_keeps_clinical_numbers():
    # Số lâm sàng ngắn (huyết áp, nhịp) KHÔNG bị nhầm là ID.
    raw = "Huyết áp 140/90, nhịp tim 88, đường huyết 7.2."
    clean, n = scrub_pii(raw)
    assert "140/90" in clean and "88" in clean
    assert n == 0


# -- Cổng đồng thuận + STT backend -----------------------------------------
def test_transcribe_requires_consent():
    with pytest.raises(AmbientError):
        transcribe("ca.m4a", consent=False, backend=lambda p, lang: "x")


def test_transcribe_uses_injected_backend():
    tr = transcribe("ca.m4a", consent=True, language="vi",
                    backend=lambda path, lang: "bệnh nhân than mệt")
    assert tr.text == "bệnh nhân than mệt"
    assert tr.language == "vi"


def test_transcribe_wraps_backend_error():
    def boom(path, lang):
        raise ValueError("decode fail")

    with pytest.raises(AmbientError):
        transcribe("ca.m4a", consent=True, backend=boom)


# -- Prompt + khung -------------------------------------------------------
def test_build_soap_prompt_has_rules():
    p = build_soap_prompt("hội thoại mẫu")
    for token in ("[BN]", "KHÔNG bịa", "PMID/DOI", "safety-netting", "S:", "O:", "A:", "P:"):
        assert token in p
    assert "hội thoại mẫu" in p


def test_blank_soap_uses_placeholders_no_pii():
    note = blank_soap()
    md = note.to_markdown()
    assert "[BN]" in md and "[tuổi]" in md
    assert DISCLAIMER in md


# -- Parse SOAP -----------------------------------------------------------
def test_parse_soap_sections():
    text = (
        "S: [BN] nam [tuổi] đau ngực 2 giờ, lan tay trái.\n"
        "O: HA 150/90, mạch 96.\n"
        "A: Theo dõi hội chứng vành cấp — nguy cơ cao.\n"
        "P: ECG ngay; aspirin; safety-netting: đau tăng → cấp cứu."
    )
    note = parse_soap(text)
    assert "đau ngực" in note.subjective
    assert "150/90" in note.objective
    assert "vành cấp" in note.assessment
    assert "ECG" in note.plan


def test_parse_soap_markdown_headers_variant():
    text = "## S — Chủ quan\nho khan\n## O\nphổi ran\n## A\nviêm phế quản\n## P\nsymptomatic"
    note = parse_soap(text)
    assert "ho khan" in note.subjective
    assert "ran" in note.objective
    assert "viêm phế quản" in note.assessment
    assert "symptomatic" in note.plan


# -- Pipeline với LLM stub -------------------------------------------------
def test_transcript_to_soap_requires_llm():
    with pytest.raises(AmbientError):
        transcript_to_soap("transcript", llm=None)


def test_transcript_to_soap_scrubs_before_llm():
    seen = {}

    def stub_llm(prompt):
        seen["prompt"] = prompt
        return ("S: [BN] đau ngực.\nO: HA 150/90.\n"
                "A: theo dõi vành cấp.\nP: ECG; safety-netting đau tăng → cấp cứu.")

    raw = "Bệnh nhân tên Trần Thị Bình, SĐT 0987654321, đau ngực."
    note = transcript_to_soap(raw, llm=stub_llm)
    # PII KHÔNG được lọt vào prompt gửi LLM.
    assert "Trần Thị Bình" not in seen["prompt"]
    assert "0987654321" not in seen["prompt"]
    # Đầu ra parse đúng + disclaimer.
    assert "đau ngực" in note.subjective
    assert DISCLAIMER in note.to_markdown()


def test_transcript_to_soap_second_layer_scrub():
    # LLM "lỡ" chép tên vào đầu ra → lưới an toàn lớp 2 phải ẩn.
    def leaky_llm(prompt):
        return ("S: bệnh nhân tên Lê Văn C, đau bụng.\nO: bụng mềm.\n"
                "A: theo dõi.\nP: theo dõi; tái khám.")

    note = transcript_to_soap("đau bụng", llm=leaky_llm)
    assert "Lê Văn C" not in note.subjective
    assert "[ĐÃ ẨN]" in note.subjective


def test_from_audio_end_to_end_with_stubs():
    def stub_stt(path, lang):
        return "Bệnh nhân tên Phạm D, 0901112223, sốt 3 ngày."

    def stub_llm(prompt):
        return ("S: [BN] sốt 3 ngày.\nO: nhiệt độ 38.5.\n"
                "A: theo dõi nhiễm siêu vi.\nP: hạ sốt; safety-netting; tái khám.")

    note = from_audio("ca.m4a", consent=True, llm=stub_llm, backend=stub_stt)
    md = note.to_markdown()
    assert "Phạm D" not in md and "0901112223" not in md
    assert "sốt" in note.subjective
    assert DISCLAIMER in md
