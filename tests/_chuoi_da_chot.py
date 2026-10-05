# -*- coding: utf-8 -*-
"""Dựng thư mục đề tài TỔNG HỢP có G0 và G1 ĐÃ CHỐT HỢP LỆ — chấm SỐNG là PASS (soát từng cổng, CHUNG-H, 04/10/2026).

Vì sao có: từ khi các cổng sau CHẤM SỐNG cổng trước (cong_song), fixture kiểu «G1_checkpoint chỉ có
quality_gate=PASS_G1_CONFIRMED» không còn mở cửa được nữa — đúng luật, vì G1 sống của một checkpoint rỗng là BLOCKED.
Test của G2…G10 cần một chuỗi G0→G1 chốt THẬT (đủ artifact, đủ xác nhận, dấu vân tay đúng nội dung). Mô-đun này dựng
chuỗi đó một lần, dùng chung; tự kiểm cong_song trả PASS để fixture hỏng thì lộ ngay chỗ dựng, không lộ ở test sau.
Dữ liệu tổng hợp, không PII, không gọi mạng.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent / "tools"
for _p in (str(_TOOLS), str(_TESTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import skill_standards as S  # noqa: E402
from test_g0_quality_gate_20260728 import _artifact_text, _checkpoint, _confirmed_g0_meta  # noqa: E402
from test_g1_quality_gate import _a2_text, _confirmed_meta, _design  # noqa: E402

EFFECTS = [{"pmid": "12345678", "doi": "10.1000/example", "title": "Nguồn thử nghiệm", "type": "RR", "value": "0.80"}]


def _ghi(path: Path, obj: Any) -> None:
    text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8", newline="\n")


def dung_g0_g1_da_chot(out_dir: Path, study: str, *, them_meta: Optional[Dict[str, Any]] = None,
                       kiem: bool = True, thiet_ke: str = "rct") -> Dict[str, Any]:
    """Ghi G0 + G1 vào out_dir; trả study_meta đã ghi. them_meta: dict gộp NÔNG theo từng cổng
    ({"G2": {...}} gộp vào gate_params.G2; khoá ngoài gate_params gộp thẳng).

    thiet_ke="rct" (mặc định): chuỗi CHỐT ĐỦ — kiem=True đòi G0 và G1 chấm sống PASS. Thiết kế khác: dựng G1 đủ artifact
    với thiết kế đó (bộ quyết định mẫu là của RCT nên G1 dừng ở DỰ THẢO) — kiem=True chỉ đòi G1 KHÔNG bị chặn; dùng cho
    test cần «G1 đang soạn, chưa chốt» của một thiết kế cụ thể."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cp0 = _checkpoint(study=study)
    _ghi(out_dir / "G0_checkpoint.json", cp0)
    _ghi(out_dir / f"G0_A1_PICO_FINER_{study}.md", _artifact_text())

    meta = copy.deepcopy(_confirmed_meta())
    meta["gate_params"]["G0"] = _confirmed_g0_meta()
    for khoa, gia_tri in (them_meta or {}).items():
        if khoa.startswith("G") and khoa[1:].isdigit():
            meta["gate_params"].setdefault(khoa, {}).update(gia_tri)
        else:
            meta[khoa] = gia_tri
    if thiet_ke == "rct":
        design = _design()
    else:
        chuan = S.reporting_standards_for(thiet_ke)
        design = _design(internal_code=thiet_ke, primary=f"Thiết kế {thiet_ke}", reporting_standard=chuan["primary"],
                         protocol_standard=chuan["protocol"])
        meta["design_code"] = thiet_ke
        meta["gate_params"]["G1"]["design"] = thiet_ke
    meta["gate_params"]["G1"]["dau_van_tay_chot"] = G1Q.dau_van_tay_g1(meta, design)
    _ghi(out_dir / "study_meta.json", meta)

    G1Q.build_supporting_artifacts(study=study, topic=cp0.get("topic", "Chủ đề"), out_dir=out_dir, design=design,
                                   g0_checkpoint=cp0, effects=EFFECTS, meta=meta,
                                   generated_at="2026-07-27T10:00:00+07:00")
    _ghi(out_dir / f"G1_A2_PROTOCOL_DESIGN_{study}.md", _a2_text())
    _ghi(out_dir / "G1_checkpoint.json", {
        "study": study, "gate": "G1", "question_type": "treatment", "design": design,
        "guardrail": {"passed": True, "errors": []}, "effect_size_samples": EFFECTS,
        "quality_contract_version": G1Q.QUALITY_CONTRACT_VERSION,
    })
    if kiem:
        CS.xoa_dem()
        for gate in ("G0", "G1"):
            song = CS.trang_thai_song(gate, study, out_dir)
            if thiet_ke == "rct":
                assert song["muc"] == "PASS", f"fixture {gate} chưa chốt hợp lệ: {song['status']} — {song.get('ly_do')}"
            else:
                assert song["muc"] != "BLOCKED", f"fixture {gate} bị chặn: {song['status']} — {song.get('ly_do')}"
        CS.xoa_dem()
    return meta
