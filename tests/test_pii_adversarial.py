"""Bộ test ĐỐI KHÁNG về khử PII (CAFÉ-S Trụ 4.1).

Ném input cố tình "lách" vào `scrub_pii` (ambient scribe) và `deidentify_patient` (FHIR) để
chứng minh các kênh rò định danh thường gặp đã bị bịt, ĐỒNG THỜI số liệu lâm sàng KHÔNG bị ẩn nhầm.
Cũng ghi nhận TƯỜNG MINH các giới hạn đã biết (tên đầu câu không có "từ khóa dẫn") để khỏi tự huyễn
là khử PII tuyệt đối — đầu ra vẫn cần placeholder + bác sĩ duyệt.
"""
from __future__ import annotations

import pytest

from app.integrations.ambient_scribe import scrub_pii
from app.integrations.fhir_client import deidentify_patient

# (mô tả, input, token PHẢI biến mất, token PHẢI còn)
_ADVERSARIAL = [
    ("phone-space", "SĐT 0912 345 678", ["0912", "345 678"], []),
    ("phone-dot", "Gọi 0912.345.678 nhé", ["0912", "345.678"], ["nhé"]),
    ("phone-dash", "Số 091-234-5678", ["091-234", "5678"], []),
    ("phone-cc-space", "Liên hệ +84 912 345 678", ["912 345", "345 678"], ["Liên hệ"]),
    ("cccd-grouped", "CCCD 012 345 678 901", ["012 345", "678 901"], ["CCCD"]),
    ("cmnd-contiguous", "CMND 012345678", ["012345678"], ["CMND"]),
    ("email", "mail abc.def+x@benhvien.vn", ["abc.def", "benhvien.vn"], ["mail"]),
    ("name-nguoibenh", "Người bệnh tên Nguyễn Văn An", ["Nguyễn", "Văn An"], ["Người bệnh tên"]),
    ("name-bn", "BN tên Trần Thị B", ["Trần", "Thị"], ["BN tên"]),
    ("name-ong", "tên ông Lê Quang C đến khám", ["Lê Quang", "Quang C"], ["khám"]),
    ("date-full", "khám 15/03/2026", ["15/03/2026"], ["khám"]),
    ("date-dob-context", "Sinh ngày 01/02/1980", ["01/02/1980"], ["Sinh"]),
    ("dob-year", "sinh năm 1962", ["1962"], ["sinh"]),
]

# Số liệu lâm sàng KHÔNG được ẩn (chống over-redaction làm hỏng nội dung).
_MUST_NOT_TOUCH = [
    "Huyết áp 140/90 mmHg",
    "mạch 88, SpO2 96%",
    "eGFR 59 mL/phút, đường huyết 7.2",
    "CRP 12, bạch cầu 11000",   # 11000 = 5 chữ số < 9 → không nhầm ID
    "tái khám sau 2 tuần",
]


@pytest.mark.parametrize("desc,text,gone,keep", _ADVERSARIAL, ids=[c[0] for c in _ADVERSARIAL])
def test_adversarial_pii_redacted(desc, text, gone, keep):
    out, n = scrub_pii(text)
    for tok in gone:
        assert tok not in out, f"[{desc}] RÒ PII: {tok!r} còn trong {out!r}"
    for tok in keep:
        assert tok in out, f"[{desc}] ẩn nhầm nội dung: mất {tok!r} trong {out!r}"
    assert n >= 1


@pytest.mark.parametrize("text", _MUST_NOT_TOUCH)
def test_clinical_numbers_preserved(text):
    out, n = scrub_pii(text)
    assert out == text, f"Ẩn nhầm số lâm sàng: {text!r} -> {out!r}"
    assert n == 0


def test_known_limitation_name_without_cue_documented():
    """GIỚI HẠN ĐÃ BIẾT: tên đầu câu KHÔNG có 'từ khóa dẫn' có thể lọt.

    Test này CỐ TÌNH khẳng định hành vi hiện tại (không khử) để giới hạn được ghi nhận minh bạch,
    không phải để tuyên bố khử PII tuyệt đối. Lớp bảo vệ thật: prompt buộc placeholder + bác sĩ duyệt.
    """
    out, _ = scrub_pii("Nguyễn Văn An than đau ngực 3 ngày")
    # Nếu tương lai có NER và khử được, hãy đảo assertion này — đó là cải tiến mong muốn.
    assert "Nguyễn Văn An" in out  # ghi nhận giới hạn hiện tại


def test_deidentify_patient_adversarial():
    """FHIR deidentify: dù resource nhồi thêm trường định danh lạ, CHỈ giữ giới + năm sinh."""
    patient = {
        "resourceType": "Patient", "gender": "male", "birthDate": "1958-07-09",
        "name": [{"text": "Phạm Văn D"}],
        "telecom": [{"system": "phone", "value": "0987654321"}],
        "address": [{"text": "123 Lê Lợi, Q1"}],
        "identifier": [{"value": "BHYT123456789"}],
        "contact": [{"name": {"text": "vợ: Trần Thị E"}}],   # trường lạ
        "photo": [{"url": "http://x/face.jpg"}],
    }
    safe = deidentify_patient(patient)
    assert safe == {"resourceType": "Patient", "gender": "male", "birthYear": "1958"}
    blob = str(safe)
    for leak in ("Phạm", "0987654321", "Lê Lợi", "BHYT123456789", "Trần Thị E", "face.jpg",
                 "1958-07-09"):
        assert leak not in blob
