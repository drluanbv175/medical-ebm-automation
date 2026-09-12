#!/usr/bin/env python3
"""Kiểm hành vi ICH E6(R3) Annex 2 cho thử nghiệm có phương pháp mới.

Annex 2 chỉ áp dụng khi thử nghiệm can thiệp dùng ít nhất một trong ba nhóm:
decentralised elements, pragmatic elements hoặc real-world data (RWD). Hệ không suy
đoán từ khóa để tránh gắn nhầm; PI/methodologist khai rõ tại
``study_meta.gate_params.G1.annex2``. Khi đã khai áp dụng, thiếu mục G1/G2 sẽ BLOCK.

Nguồn: ICH E6(R3) Annex 2, Step 4, thông qua 03/06/2026.
"""

from __future__ import annotations

from typing import Any, Mapping

VERSION = "ICH E6(R3) Annex 2 Step 4"
ADOPTED_DATE = "2026-06-03"
SOURCE_URL = (
    "https://database.ich.org/sites/default/files/"
    "ICH_E6%28R3%29_Annex%202_Guideline_Step%204_2026_0603_0.pdf"
)
METHODS = {"decentralised", "pragmatic", "rwd"}

COMMON_G1_FIELDS = {
    "fit_for_purpose_justification": "lý do và tính phù hợp mục đích của phương pháp",
    "participant_burden_and_access": "gánh nặng, khả năng tiếp cận và hỗ trợ người tham gia",
    "roles_and_oversight": "vai trò, trách nhiệm và giám sát theo mức rủi ro",
    "safety_information_flow": "luồng phát hiện/chuyển thông tin an toàn kịp thời",
}
METHOD_G1_FIELDS = {
    "decentralised": {
        "remote_data_collection_plan": "kế hoạch thu dữ liệu từ xa/DHT và hỗ trợ kỹ thuật",
    },
    "pragmatic": {
        "usual_care_activities": "hoạt động chăm sóc thường quy: ai làm, khi nào, trong hoàn cảnh nào",
        "data_variability_and_sap": "biến thiên giữa nguồn/bối cảnh và cách xử lý trong SAP",
    },
    "rwd": {
        "data_provenance_and_quality": "nguồn gốc, chất lượng và fitness-for-use của RWD",
        "data_variability_and_sap": "biến thiên giữa nguồn/bối cảnh và cách xử lý trong SAP",
    },
}
COMMON_G2_FIELDS = {
    "irb_information_plan": "thông tin phương pháp cung cấp cho IRB/IEC",
    "privacy_confidentiality_security": "bảo vệ riêng tư, bí mật và an toàn dữ liệu",
}
METHOD_G2_FIELDS = {
    "decentralised": {
        "remote_consent_and_identity": "đồng thuận từ xa, xác minh danh tính và bảo vệ dữ liệu",
        "alternative_access_path": "lựa chọn giấy/trực tiếp khả thi cho người không dùng công nghệ",
        "dht_validation_and_support": "tính phù hợp của DHT, đào tạo và hỗ trợ kỹ thuật",
    },
    "pragmatic": {
        "training_and_record_sharing": "đào tạo, chia sẻ/lưu hồ sơ và toàn vẹn dữ liệu thường quy",
    },
    "rwd": {
        "access_and_permissions": "quyền truy cập, đồng thuận/cho phép dùng RWD",
        "data_governance": "quản trị dữ liệu và trách nhiệm của sponsor/service provider",
    },
}


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and "[CẦN" not in text and "[DỰ THẢO]" not in text
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def annex2_config(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params") if isinstance(meta, Mapping) else None
    g1 = params.get("G1") if isinstance(params, Mapping) else None
    cfg = g1.get("annex2") if isinstance(g1, Mapping) else None
    return cfg if isinstance(cfg, Mapping) else {}


def evaluate(meta: Mapping[str, Any], design_code: str, stage: str) -> dict[str, Any]:
    """Trả trạng thái PASS/NOT_APPLICABLE/BLOCK và danh sách trường thiếu."""
    cfg = annex2_config(meta)
    raw_methods = cfg.get("methodologies") or []
    if isinstance(raw_methods, str):
        raw_methods = [raw_methods]
    methods = {str(item).strip().lower() for item in raw_methods if str(item).strip()}
    unknown = sorted(methods - METHODS)
    applicable = cfg.get("applicable") is True or bool(methods)

    if str(design_code) != "rct":
        if applicable:
            return {
                "status": "BLOCK", "applicable": True, "methods": sorted(methods),
                "missing": [], "errors": ["Annex 2 được khai áp dụng nhưng design_code không phải rct"],
                "version": VERSION, "source": SOURCE_URL,
            }
        return {"status": "NOT_APPLICABLE", "applicable": False, "methods": [],
                "missing": [], "errors": [], "version": VERSION, "source": SOURCE_URL}
    if not applicable:
        return {"status": "NOT_APPLICABLE", "applicable": False, "methods": [],
                "missing": [], "errors": [], "version": VERSION, "source": SOURCE_URL}
    if cfg.get("applicable") is False and methods:
        unknown.append("applicable=false mâu thuẫn với methodologies")
    if not methods:
        unknown.append("đã khai applicable=true nhưng chưa chọn methodology")

    required = dict(COMMON_G1_FIELDS if stage == "G1" else COMMON_G2_FIELDS)
    method_fields = METHOD_G1_FIELDS if stage == "G1" else METHOD_G2_FIELDS
    for method in methods & METHODS:
        required.update(method_fields[method])
    missing = [f"{key}: {label}" for key, label in required.items() if not _present(cfg.get(key))]
    errors = [f"methodology không hợp lệ: {item}" for item in unknown]
    return {
        "status": "BLOCK" if missing or errors else "PASS",
        "applicable": True,
        "methods": sorted(methods & METHODS),
        "missing": missing,
        "errors": errors,
        "version": VERSION,
        "adopted_date": ADOPTED_DATE,
        "source": SOURCE_URL,
    }
