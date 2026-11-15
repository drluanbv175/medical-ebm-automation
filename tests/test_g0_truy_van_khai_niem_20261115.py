# -*- coding: utf-8 -*-
"""K4 (giả lập lần 3, 15/11/2026) — G0 dựng truy vấn PubMed từ khái niệm PI khai và từ P · I/E · O đã khai.

Đo được: G0-AUTO-08 hướng dẫn PI «viết query_en HOẶC khai gate_params.G0.khai_niem_tim_kiem», nhưng
build_pubmed_query bỏ qua khai_niem_tim_kiem ⇒ PI khai xong G0 vẫn REVIEW và PI vẫn phải tự viết cả câu truy vấn; bộ
dịch VI→EN chỉ đọc CHỦ ĐỀ ⇒ khái niệm chỉ có ở trường PICO bị rơi lặng lẽ. Thư mục tạm, dữ liệu tổng hợp, không mạng.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g0_quality_gate as G0Q  # noqa: E402
import khung_de_tai as KD  # noqa: E402
import run_g0_auto as R0  # noqa: E402
import run_pipeline as RP  # noqa: E402

KHAI = {"P": ["hypertension", "high blood pressure"], "I": ["text messaging", "SMS"],
        "O": ["blood pressure control", '"Medication Adherence"[mh]']}


def _meta(**g0) -> dict:
    return {"gate_params": {"G0": g0}}


def test_truy_van_tu_khai_niem_or_trong_and_giua_va_giu_cu_phap_pubmed():
    q = KD.truy_van_tu_khai_niem(_meta(khai_niem_tim_kiem=KHAI))
    assert q == ('(hypertension OR "high blood pressure") AND ("text messaging" OR SMS) AND '
                 '("blood pressure control" OR ("Medication Adherence"[mh]))')


def test_truy_van_tu_khai_niem_bo_o_mau_trung_lap_va_khai_niem_trong():
    q = KD.truy_van_tu_khai_niem(_meta(khai_niem_tim_kiem={"P": ["hypertension", "hypertension", "[CẦN thêm]"],
                                                           "I": [], "O": "adherence"}))
    assert q == "(hypertension) AND (adherence)"
    assert KD.truy_van_tu_khai_niem(_meta(khai_niem_tim_kiem={"P": ["[CẦN]"]})) is None
    assert KD.truy_van_tu_khai_niem(_meta()) is None and KD.truy_van_tu_khai_niem({}) is None


def test_build_query_thu_tu_nguon():
    meta = _meta(khai_niem_tim_kiem=KHAI)
    assert R0.build_pubmed_query("Chủ đề tiếng Việt", "custom[tiab]", meta=meta)["nguon"] == "query_en"
    q = R0.build_pubmed_query("Chủ đề tiếng Việt", None, meta=meta)
    assert q["nguon"] == "khai_niem_tim_kiem" and q["base"] == KD.truy_van_tu_khai_niem(meta)
    assert q["rct"].startswith(q["base"] + " AND ")
    en = R0.build_pubmed_query("Text messaging for hypertension control", None, meta=_meta())
    assert en["nguon"] == "chu_de_tieng_anh" and en["base"] == "Text messaging for hypertension control"


def test_tu_dien_doc_ca_truong_pico_khong_chi_chu_de():
    """Chủ đề không nhắc «tăng huyết áp» nhưng quần thể G0 có ⇒ thuật ngữ quần thể vào truy vấn máy dịch."""
    vi, en = next((v, e) for v, e in R0.VI_EN_TERMS.items() if v == "tăng huyết áp")
    q = R0.build_pubmed_query("Hiệu quả nhắc uống thuốc", None,
                              meta=_meta(population=f"Người bệnh {vi} điều trị ngoại trú"))
    assert q["nguon"] == "tu_dien" and en in q["base"]
    assert en not in R0.build_pubmed_query("Hiệu quả nhắc uống thuốc", None, meta=_meta())["base"]


def test_g0_auto_08_pi_khai_khai_niem_thi_truy_van_dung_tu_do_va_qua():
    meta = _meta(pico_confirmed=True, population="Người bệnh khoa khám bệnh", intervention="Không can thiệp — mô tả",
                 primary_outcome="Mức hài lòng", khai_niem_tim_kiem={"P": ["outpatients"], "O": ["satisfaction"]})
    base = R0.build_pubmed_query("Mức hài lòng người bệnh khoa khám bệnh", None, meta=meta)["base"]
    c = G0Q._tieu_chi_phu_pico({"base_query": base}, meta, {"query": base}, {})
    assert c["status"] == "PASS", c["evidence"]
    # Đối chứng (lỗi cũ): khai khái niệm mà truy vấn vẫn là bản máy dịch chủ đề ⇒ REVIEW.
    c_cu = G0Q._tieu_chi_phu_pico({"base_query": "satisfaction"}, meta, {"query": "satisfaction"}, {})
    assert c_cu["status"] == "REVIEW"


def test_pipeline_k5_khai_niem_doi_thi_tra_lai_g0(tmp_path):
    out = tmp_path / "exports" / "ZZTEST-K4"
    out.mkdir(parents=True)
    meta = _meta(khai_niem_tim_kiem=KHAI)
    (out / "G0_checkpoint.json").write_text(json.dumps({"gate": "G0", "topic": "Chủ đề", "base_query": "hypertension"}),
                                           encoding="utf-8", newline="\n")
    ly = RP._g0_lech_dau_vao(out, None, meta)
    assert ly and "khai_niem_tim_kiem" in ly, "PI vừa khai khái niệm ⇒ tra lại PubMed"
    (out / "G0_checkpoint.json").write_text(json.dumps({"gate": "G0", "topic": "Chủ đề",
                                                        "base_query": KD.truy_van_tu_khai_niem(meta)}),
                                           encoding="utf-8", newline="\n")
    assert RP._g0_lech_dau_vao(out, None, meta) is None, "đã tra bằng truy vấn đó ⇒ hội tụ"
    assert RP._g0_lech_dau_vao(out, None, {**meta, "query_en": "x[tiab]"}), "query_en vẫn thắng khái niệm"


def test_g0_auto_08_khai_niem_pi_khai_mot_phan_la_truy_van_cua_pi():
    """Khái niệm PI không khai mà từ điển cũng không dịch được (O) ⇒ khi truy vấn dựng từ khái niệm PI khai, đó là lựa
    chọn của PI (ghi chú), không phải «máy tự dịch» (REVIEW)."""
    meta = _meta(pico_confirmed=True, population="Người bệnh khoa khám bệnh", intervention="Không can thiệp — mô tả",
                 primary_outcome="Điểm số Y", khai_niem_tim_kiem={"P": ["outpatients"]})
    base = R0.build_pubmed_query("Điểm số Y ở người bệnh khoa khám bệnh", None, meta=meta)["base"]
    c = G0Q._tieu_chi_phu_pico({"base_query": base}, meta, {"query": base}, {})
    assert c["status"] == "PASS" and "PI tự viết" in c["evidence"], c["evidence"]
    may = _meta(pico_confirmed=True, population="Người bệnh khoa khám bệnh", intervention="Không can thiệp — mô tả",
                primary_outcome="Điểm số Y")
    c2 = G0Q._tieu_chi_phu_pico({"base_query": "outpatients"}, may, {"query": "outpatients"}, {})
    assert c2["status"] == "REVIEW" and "MÁY tự dịch" in c2["evidence"]
