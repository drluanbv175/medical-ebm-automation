#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hồi quy 25/10/2026 — đề tài mô tả có MỤC TIÊU PHỤ phân tích với giả thuyết định trước.

Bối cảnh: hội đồng G1 của C1a (DP-G1-2) chỉ ra A2 «Giả thuyết chính» và SAP §12 in cứng «nghiên cứu mô tả — không kiểm
định giả thuyết» trong khi MT2 có H0/H1 hai phía (đề cương nộp Hội đồng). PI chọn phương án (i): MT1 ước lượng theo độ
chính xác, MT2 có giả thuyết định trước. Khoá `gate_params.G0.hypothesis_secondary` (G0 là nơi chốt giả thuyết) được
A2 (G1), SAP §12 (G4) và mục giả thuyết của đề cương (G10) cùng đọc; vắng khoá ⇒ câu cũ. Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_quality_gate as G1Q  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

GT_PHU = "MT2: H0: OR chung = 1; H1: OR ≠ 1, hai phía, α = 0,05; mô hình chính logistic thứ tự"


def _meta(co_gia_thuyet: bool) -> dict:
    g0 = {"test_type": "descriptive"}
    if co_gia_thuyet:
        g0["hypothesis_secondary"] = GT_PHU
    return {"gate_params": {"G0": g0, "G1": {}}}


def _a2(co_gia_thuyet: bool) -> str:
    return G1Q.build_protocol_core(study="THU", topic="Hài lòng người bệnh",
                                   design={"internal_code": "cross_sectional"}, meta=_meta(co_gia_thuyet),
                                   generated_at="2026-10-25")


def test_a2_noi_ro_gia_thuyet_muc_tieu_phu():
    assert GT_PHU in _a2(True) and "Kết cục chính mô tả" in _a2(True)
    assert "Nghiên cứu mô tả — không kiểm định giả thuyết" in _a2(False) and GT_PHU not in _a2(False)


def _sap12(gia_thuyet_phu) -> str:
    sap = G4.generate("THU", "Hài lòng", "cross_sectional", "Cắt ngang", "STROBE", 1000, 0.05, 0.8, 0.5, "PREVALENCE",
                      "2026-10-25", hypothesis_type="descriptive_precision",
                      g3={"precision": 0.05, "effect_type": "PREVALENCE"}, gia_thuyet_phu=gia_thuyet_phu)
    sap = sap if isinstance(sap, str) else sap[0]
    return sap[sap.index("### §12"):]


def test_sap_muc_12_co_dong_gia_thuyet_muc_tieu_phu():
    co = _sap12(GT_PHU)
    assert f"Giả thuyết mục tiêu phụ (định trước, gate_params.G0.hypothesis_secondary):** {GT_PHU}" in co
    assert "mục tiêu phụ xem dòng «Giả thuyết mục tiêu phụ»" in co
    khong = _sap12(None)
    assert "Giả thuyết mục tiêu phụ" not in khong
    assert "- **Power:** không dùng — cỡ mẫu theo độ chính xác của ước lượng, không kiểm định giả thuyết" in khong


def test_de_cuong_g10_noi_ro_gia_thuyet_muc_tieu_phu():
    cps = {"G1": {}, "G3": {"hypothesis_type": "descriptive_precision"}}
    assert GT_PHU in G10.sec_cauhoi(cps, _meta(True))
    assert "Giả thuyết mục tiêu phụ" not in G10.sec_cauhoi(cps, _meta(False))
