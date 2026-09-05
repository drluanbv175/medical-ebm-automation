"""FHIR R4 client — kết nối nguồn dữ liệu y tế chuẩn (EMR/HIS) qua HL7 FHIR R4.

Đóng gap Trụ 2.2 của CAFÉ-S ("phải hỗ trợ FHIR R4"). Thiết kế an toàn cho bối cảnh lâm sàng:

- **Mặc định CHỈ ĐỌC.** Thao tác ghi (create/update) bị từ chối trừ khi bật `allow_write=True`
  một cách tường minh — tránh vô tình ghi vào EMR thật.
- **KHÔNG lưu PHI** vào DB/đĩa của dự án. Có hàm `deidentify_patient` để khử định danh trước khi
  xử lý/log. Dữ liệu FHIR là PHI → chỉ trỏ tới EMR thật khi ĐƯỢC PHÉP; để thử nghiệm dùng
  HAPI public R4 sandbox (https://hapi.fhir.org/baseR4 — dữ liệu giả).
- Có retry/backoff + xử lý lỗi (theo quy tắc dự án). Chỉ phụ thuộc `requests`.

Ví dụ:
    c = FhirClient("https://hapi.fhir.org/baseR4")
    c.assert_r4()                              # đảm bảo server là R4
    pts = c.search_resources("Patient", {"_count": "1"})
    meds = extract_medication_requests(c.search_resources("MedicationRequest", {"_count": "5"}))
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

FHIR_JSON = "application/fhir+json"


class FhirError(RuntimeError):
    """Lỗi khi gọi máy chủ FHIR (mạng, HTTP, hoặc vi phạm an toàn ghi)."""


class FhirClient:
    """Client FHIR R4 tối giản, an toàn (read-only mặc định)."""

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 30,
                 max_retries: int = 3, allow_write: bool = False) -> None:
        if not base_url:
            raise FhirError("Thiếu base_url FHIR. Để thử nghiệm dùng HAPI sandbox; "
                            "EMR thật chỉ trỏ khi được phép.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.allow_write = allow_write
        self.session = requests.Session()
        self.session.headers.update({"Accept": FHIR_JSON})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    # -- HTTP lõi -------------------------------------------------------
    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                 json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        last: Any = None
        for attempt in range(self.max_retries):
            try:
                headers = {"Content-Type": FHIR_JSON} if json is not None else None
                resp = self.session.request(method, url, params=params, json=json,
                                            headers=headers, timeout=self.timeout)
                if resp.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {resp.status_code}"
                    time.sleep(1.5 * (2 ** attempt))
                    continue
                resp.raise_for_status()
                return resp.json() if resp.content else {}
            except requests.RequestException as exc:
                last = exc
                logger.warning("FHIR %s %s lỗi: %s (thử lại)", method, url, exc)
                time.sleep(1.5 * (2 ** attempt))
        raise FhirError(f"FHIR {method} {url} thất bại sau {self.max_retries} lần: {last}")

    # -- Năng lực & phiên bản ------------------------------------------
    def capability(self) -> Dict[str, Any]:
        """Lấy CapabilityStatement (metadata) của server."""
        return self._request("GET", "metadata", params={"_summary": "true"})

    def fhir_version(self) -> Optional[str]:
        return self.capability().get("fhirVersion")

    def assert_r4(self) -> str:
        """Đảm bảo server là FHIR R4 (4.0.x). Ném FhirError nếu không."""
        ver = self.fhir_version() or ""
        if not str(ver).startswith("4."):
            raise FhirError(f"Server KHÔNG phải FHIR R4 (fhirVersion={ver!r}).")
        return ver

    # -- Đọc -----------------------------------------------------------
    def read(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        return self._request("GET", f"{resource_type}/{resource_id}")

    def search(self, resource_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trả Bundle thô."""
        return self._request("GET", resource_type, params=dict(params or {}))

    def search_resources(self, resource_type: str,
                         params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Trả danh sách resource (rút từ Bundle.entry).

        SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 17) — bản gốc
        `"resource" in e` giả định MỌI phần tử `entry` là dict. Bundle là dữ
        liệu từ MÁY CHỦ FHIR THẬT (EMR/HIS ngoài dự án, theo đúng docstring
        module) — một entry không tuân thủ spec (không phải dict) làm câu
        lệnh ném lỗi (`TypeError` nếu là số, hoặc âm thầm bỏ sót nếu là chuỗi
        do `in` đổi nghĩa thành kiểm tra substring), MẤT TOÀN BỘ resource hợp
        lệ khác trong cùng Bundle — kể cả những cái đứng trước/sau entry lỗi.
        Nay bỏ qua CHỈ entry không phải dict, giữ nguyên mọi resource hợp lệ.
        """
        bundle = self.search(resource_type, params)
        return [e["resource"] for e in bundle.get("entry", [])
                if isinstance(e, dict) and "resource" in e]

    # -- Ghi (mặc định CẤM) --------------------------------------------
    def create(self, resource_type: str, resource: Dict[str, Any]) -> Dict[str, Any]:
        if not self.allow_write:
            raise FhirError("allow_write=False — TỪ CHỐI ghi để an toàn. "
                            "Chỉ bật khi thật sự cần và được phép.")
        return self._request("POST", resource_type, json=resource)


# -- Helpers an toàn / nối skill lâm sàng ------------------------------
def deidentify_patient(patient: Dict[str, Any]) -> Dict[str, Any]:
    """Khử định danh Patient: BỎ name/telecom/address/identifier; chỉ giữ giới + NĂM sinh.

    Dùng trước khi log/xử lý để không lộ PHI (Trụ 4.1 CAFÉ-S).
    """
    safe: Dict[str, Any] = {"resourceType": "Patient", "gender": patient.get("gender")}
    birth = patient.get("birthDate")
    if birth:
        safe["birthYear"] = str(birth)[:4]  # chỉ năm, bỏ ngày/tháng
    return safe


def extract_medication_requests(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rút danh sách thuốc gọn từ MedicationRequest → nối được sang skill ke-don-an-toan.

    KHÔNG kèm thông tin định danh bệnh nhân.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 17) — bản gốc gọi thẳng
    `r.get(...)` giả định mọi phần tử `resources` là dict. Cùng lớp lỗi "một
    bản ghi hỏng làm rớt cả lô" đã gặp ở `europepmc.py`/`pubmed.py`: một
    resource không tuân thủ spec (không phải dict) từ máy chủ FHIR thật ném
    `AttributeError`, làm MẤT TOÀN BỘ đơn thuốc hợp lệ khác trong cùng danh
    sách. Nay bỏ qua chỉ resource không phải dict.
    """
    out: List[Dict[str, Any]] = []
    for r in resources:
        if not isinstance(r, dict) or r.get("resourceType") != "MedicationRequest":
            continue
        mcc = r.get("medicationCodeableConcept") or {}
        med = mcc.get("text") or " / ".join(
            c.get("display", "") for c in mcc.get("coding", []) if c.get("display"))
        out.append({"medication": med or "(không rõ)",
                    "status": r.get("status"), "intent": r.get("intent")})
    return out


def from_settings(allow_write: bool = False) -> "FhirClient":
    """Tạo client từ biến môi trường FHIR_BASE_URL / FHIR_TOKEN (không hardcode endpoint)."""
    import os
    base = os.getenv("FHIR_BASE_URL", "")
    token = os.getenv("FHIR_TOKEN", "") or None
    return FhirClient(base, token=token, allow_write=allow_write)
