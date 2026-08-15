"""CLI HỢP NHẤT cho công cụ tích hợp CAFÉ-S — một cửa duy nhất cho bác sĩ gọi 5 module.

Trước đây các module (FHIR · ambient SOAP · tương tác thuốc · đọc ảnh) chỉ gọi rời qua
`python -m app.integrations.<module>` → khó nhớ, dễ "mồ côi". File này gom thành một entry:

    python -m app.integrations.cli list
    python -m app.integrations.cli drug warfarin aspirin
    python -m app.integrations.cli soap --transcript ca.txt
    python -m app.integrations.cli image ecg.jpg --modality ecg --consent
    python -m app.integrations.cli fhir            # smoke FHIR (mặc định HAPI sandbox)

An toàn (đồng nhất mọi công cụ): KHÔNG lưu PII; đầu ra là BẢN NHÁP "Cần bác sĩ kiểm chứng";
ambient/đọc ảnh có cổng đồng thuận; chỉ ĐỀ XUẤT, bác sĩ duyệt.
"""
from __future__ import annotations

import sys
from typing import List, Optional

# tool -> (mô tả, ví dụ dùng, yêu cầu thêm)
_TOOLS = {
    "drug": ("Sàng lọc tương tác/CCĐ thuốc qua nhãn openFDA (miễn phí, không key)",
             "drug <thuoc1> <thuoc2> ...", "cần mạng (openFDA)"),
    "soap": ("Ambient: audio/transcript buổi khám → bản nháp SOAP (khử PII)",
             "soap --transcript f.txt  |  soap --audio a.m4a --consent", "STT cần faster-whisper; SOAP cần LLM/skill"),
    "image": ("Đọc ảnh ECG/CXR/CLS (khử EXIF) → bản nháp đọc có hệ thống",
              "image <file> --modality ecg --consent", "cần Pillow + vision LLM (ANTHROPIC_API_KEY)"),
    "fhir": ("Kết nối FHIR R4 (EMR/HIS chuẩn) — smoke đọc, chặn ghi mặc định",
             "fhir [--base URL]", "mặc định HAPI public sandbox"),
}


def _list() -> int:
    print("Công cụ tích hợp CAFÉ-S — python -m app.integrations.cli <tool> ...\n")
    for name, (desc, usage, req) in _TOOLS.items():
        print(f"  {name:6s} {desc}")
        print(f"         vd : python -m app.integrations.cli {usage}")
        print(f"         yêu cầu: {req}\n")
    print("⚠️ Mọi công cụ: KHÔNG lưu PII; đầu ra là NHÁP 'Cần bác sĩ kiểm chứng'; chỉ ĐỀ XUẤT.")
    return 0


def _fhir(argv: List[str]) -> int:  # pragma: no cover - cần mạng
    import argparse
    import os

    from app.integrations.fhir_client import FhirClient, FhirError

    ap = argparse.ArgumentParser(prog="cli fhir")
    ap.add_argument("--base", default=os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4"))
    a = ap.parse_args(argv)
    try:
        c = FhirClient(a.base)
        ver = c.assert_r4()
        n = len(c.search_resources("Patient", {"_count": "1"}))
        print(f"[✓] FHIR R4 OK: {a.base} (fhirVersion={ver}); đọc thử Patient={n} (dữ liệu sandbox).")
        print("    Ghi bị CHẶN mặc định (allow_write=False). KHÔNG lưu PHI vào dự án.")
        return 0
    except FhirError as exc:
        print(f"[!] {exc}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("list", "-h", "--help"):
        return _list()
    tool, rest = argv[0], argv[1:]
    if tool == "drug":
        from app.integrations.drug_interactions import main as run
        return run(rest)
    if tool == "soap":
        from app.integrations.ambient_scribe import main as run
        return run(rest)
    if tool == "image":
        from app.integrations.image_reading import main as run
        return run(rest)
    if tool == "fhir":
        return _fhir(rest)
    print(f"[!] Không rõ công cụ: {tool!r}. Chạy: python -m app.integrations.cli list", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
