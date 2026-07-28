"""Hồi quy HÀNH VI cho việc tra prior art ở cổng G2 (vá 2026-07-28).

Hai lỗi được vá, đều đo được thật trên ClinicalTrials.gov API v2 ngày 2026-07-28:

  (1) G2 gửi lên truy vấn TIẾNG VIỆT BỎ DẤU. `search_clinicaltrials()` cũ nhận
      `topic` tiếng Việt thô, cắt 4 từ dài rồi bóc dấu bằng regex (KHÔNG dịch).
      Đề tài "Sự hài lòng của người bệnh ngoại trú tại Khoa Khám bệnh" thành
      `"long nguoi benh ngoai"` → totalCount = 0. Cùng lúc G0 ĐÃ tính và ĐÃ ghi
      `base_query` tiếng Anh vào `G0_checkpoint.json`:
      `"outpatient patient satisfaction hospital"` → totalCount = 1422 (241 đang
      tuyển). Hồ sơ đạo đức vì thế in "Không tìm thấy thử nghiệm tương tự".

  (2) TRA THẤT BẠI HIỂN THỊ Y HỆT "KHÔNG CÓ NGHIÊN CỨU TRÙNG". Lỗi mạng/timeout
      bị nuốt thành `[]`, và `_ct_table([])` in cùng một câu cho cả hai trường
      hợp; checkpoint ghi `clinicaltrials_found: 0`.

CÁCH KIỂM: các test dưới đây soi HÀNH VI (truy vấn thật sự được gửi đi, nội dung
artifact, nội dung checkpoint) — KHÔNG grep mã nguồn. Một bản vá bị hoàn tác hay
viết lại kiểu khác vẫn phải làm các test này đỏ nếu hành vi sai quay lại.

Không gọi mạng: mọi test đều chặn tầng HTTP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "tools"))

import run_g2_auto as G2  # noqa: E402
import trial_registry as TR  # noqa: E402

# Đúng đề tài đã tái hiện được lỗi thật.
TOPIC_VI = "Sự hài lòng của người bệnh ngoại trú tại Khoa Khám bệnh"
BASE_QUERY_EN = "outpatient patient satisfaction hospital"


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích: G0 checkpoint giả + HttpClient giả ghi lại truy vấn đã gửi
# ════════════════════════════════════════════════════════════════════════════

def _write_g0_checkpoint(study_dir: Path, *, topic: str, base_query: str | None) -> None:
    cp = {
        "study": study_dir.name, "gate": "G0", "topic": topic,
        "pubmed_results": {"n_sr": 3, "n_rct": 2},
        "evidence_level": "TRUNG BÌNH",
    }
    if base_query is not None:
        cp["base_query"] = base_query
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(
        json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")


class _RecordingHttp:
    """HttpClient giả: ghi lại mọi params đã gửi, trả về payload định sẵn."""

    sent: list[dict] = []

    def __init__(self, total: int = 0, active: int = 0, studies: list | None = None):
        self.total, self.active, self.studies = total, active, studies or []

    def get_json(self, url, params=None, **_kw):
        type(self).sent.append(dict(params or {}))
        if (params or {}).get("filter.overallStatus"):
            return {"totalCount": self.active, "studies": []}
        return {"totalCount": self.total, "studies": self.studies}


def _install_http(monkeypatch, **kwargs) -> list[dict]:
    """Chặn tầng HTTP + tắt chế độ mock; trả về list params sẽ được ghi vào."""
    from app.config import settings
    monkeypatch.setattr(settings, "use_mock_sources", False, raising=False)
    import app.utils.http as http_mod
    _RecordingHttp.sent = []
    monkeypatch.setattr(http_mod, "HttpClient", lambda *a, **k: _RecordingHttp(**kwargs))
    return _RecordingHttp.sent


def _run_g2(monkeypatch, tmp_path, study: str, extra_argv: list[str] | None = None) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(G2, "export_docx_g2", lambda *_a, **_k: None)
    monkeypatch.setattr(sys, "argv", [
        "run_g2_auto.py", "--study", study, "--design", "cross_sectional",
    ] + (extra_argv or []))
    G2.main()
    return tmp_path / "exports" / study


def _study_dir(tmp_path: Path, study: str) -> Path:
    return tmp_path / "exports" / study


# ════════════════════════════════════════════════════════════════════════════
# LỖI 1 — truy vấn gửi đi phải là base_query TIẾNG ANH của G0
# ════════════════════════════════════════════════════════════════════════════

def test_g2_gui_base_query_tieng_anh_chu_khong_phai_topic_tieng_viet(monkeypatch, tmp_path):
    """ĐÒN GỐC: G2 phải tra bằng `base_query` của G0, không phải topic bỏ dấu."""
    study = "PYTEST-G2-REG-EN"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)
    sent = _install_http(monkeypatch, total=1422, active=241)

    _run_g2(monkeypatch, tmp_path, study)

    terms = [p.get("query.term") for p in sent]
    assert terms, "G2 không gửi truy vấn nào tới ClinicalTrials.gov"
    assert all(t == BASE_QUERY_EN for t in terms), (
        f"G2 phải gửi base_query tiếng Anh của G0, thực tế gửi: {terms}"
    )
    # Chuỗi bỏ dấu kiểu cũ ("long nguoi benh ngoai") phải KHÔNG còn xuất hiện.
    for t in terms:
        assert "nguoi" not in (t or "").lower() and "benh" not in (t or "").lower(), (
            f"truy vấn vẫn là tiếng Việt bỏ dấu: {t!r}"
        )


def test_g2_lui_ve_topic_khi_g0_thieu_base_query(monkeypatch, tmp_path):
    """Checkpoint G0 cũ (không có `base_query`) vẫn chạy được — lùi về topic."""
    study = "PYTEST-G2-REG-FALLBACK"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI, base_query=None)
    sent = _install_http(monkeypatch, total=0, active=0)

    _run_g2(monkeypatch, tmp_path, study)

    assert [p.get("query.term") for p in sent] == [TOPIC_VI, TOPIC_VI], (
        "thiếu base_query thì phải lùi về topic nguyên văn, không được tra rỗng"
    )


def test_g2_dem_tong_va_dem_dang_tuyen(monkeypatch, tmp_path):
    """G2 phải lấy CẢ tổng số hồ sơ lẫn số đang/sắp tuyển (như G0)."""
    study = "PYTEST-G2-REG-COUNTS"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)
    sent = _install_http(monkeypatch, total=1422, active=241)

    out_dir = _run_g2(monkeypatch, tmp_path, study)

    assert any(p.get("countTotal") for p in sent), "thiếu countTotal → không có tổng số thật"
    assert any(p.get("filter.overallStatus") for p in sent), \
        "thiếu filter.overallStatus → không trả lời được 'có ai ĐANG làm'"
    cp = json.loads((out_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["clinicaltrials"]["n_trials"] == 1422
    assert cp["clinicaltrials"]["n_active"] == 241
    assert cp["clinicaltrials"]["query"] == BASE_QUERY_EN, \
        "checkpoint phải ghi ĐÚNG truy vấn đã dùng để Hội đồng tra lại được"


# ════════════════════════════════════════════════════════════════════════════
# LỖI 2 — "CHƯA TRA ĐƯỢC" phải khác hẳn "đã tra, 0 hồ sơ"
# ════════════════════════════════════════════════════════════════════════════

def _artifact_text(out_dir: Path, study: str) -> str:
    return (out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md").read_text(encoding="utf-8")


def test_tra_that_bai_khong_bi_doc_thanh_khong_co_nghien_cuu_trung(monkeypatch, tmp_path):
    """Mạng hỏng → artifact + checkpoint phải nói CHƯA TRA ĐƯỢC, không phải 0."""
    study = "PYTEST-G2-REG-FAIL"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)

    from app.config import settings
    monkeypatch.setattr(settings, "use_mock_sources", False, raising=False)

    class _Boom:
        def get_json(self, *a, **k):
            raise RuntimeError("mạng hỏng")

    import app.utils.http as http_mod
    monkeypatch.setattr(http_mod, "HttpClient", lambda *a, **k: _Boom())

    out_dir = _run_g2(monkeypatch, tmp_path, study)

    art = _artifact_text(out_dir, study)
    assert TR.NOT_CHECKED_LABEL in art, "artifact không gắn nhãn CHƯA TRA ĐƯỢC"
    assert "mạng hỏng" in art, "artifact phải nêu LÝ DO không tra được"

    cp = json.loads((out_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["clinicaltrials"]["checked"] is False
    assert cp["clinicaltrials"]["n_trials"] is None, \
        "lỗi mạng TUYỆT ĐỐI không được biến thành số 0"
    assert cp["clinicaltrials_found"] is None, \
        "khóa tương thích ngược cũng không được ghi 0 khi chưa tra được"
    assert cp["clinicaltrials_checked"] is False
    # Việc-phải-làm nằm trong khối `clinicaltrials`, KHÔNG phải
    # `pending_doctor_actions`: khóa đó bị g2_quality_gate.refresh_checkpoint() ghi
    # đè bằng pending_actions của hợp đồng chất lượng ngay sau write_g2_checkpoint().
    assert TR.NOT_CHECKED_LABEL in (cp["clinicaltrials"]["pending_action"] or ""), \
        "chưa tra được phải thành một việc bác sĩ phải làm, không im lặng bỏ qua"


def test_da_tra_that_va_khong_co_ho_so_thi_noi_ro_la_da_tra(monkeypatch, tmp_path):
    """Tra thành công với 0 kết quả là BẰNG CHỨNG — phải nói khác 'chưa tra được'."""
    study = "PYTEST-G2-REG-ZERO"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)
    _install_http(monkeypatch, total=0, active=0)

    out_dir = _run_g2(monkeypatch, tmp_path, study)

    art = _artifact_text(out_dir, study)
    assert "0 hồ sơ khớp" in art
    assert BASE_QUERY_EN in art, "phải in truy vấn đã dùng để Hội đồng tái lặp được"

    cp = json.loads((out_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["clinicaltrials"]["checked"] is True
    assert cp["clinicaltrials"]["n_trials"] == 0
    assert cp["clinicaltrials_found"] == 0
    assert cp["clinicaltrials"]["pending_action"] is None, \
        "đã tra thật thì không được đẻ ra việc 'tra lại' vô nghĩa cho bác sĩ"


def test_hai_trang_thai_khong_duoc_sinh_ra_cung_mot_van_ban(monkeypatch, tmp_path):
    """Đòn cốt lõi: 'không tra được' và 'đã tra, 0 hồ sơ' phải KHÁC NHAU trên giấy.

    Đây chính là lỗi cũ — `_ct_table([])` in một câu duy nhất cho cả hai.
    """
    khong_tra = TR.format_prior_art_table(
        TR.empty_registry(BASE_QUERY_EN, "timeout"))
    da_tra_0 = TR.format_prior_art_table({
        "registry": "ClinicalTrials.gov", "query": BASE_QUERY_EN, "checked": True,
        "n_trials": 0, "n_active": 0, "trials": [], "error": None,
        "checked_at": "2026-07-28T09:00:00",
    })
    assert khong_tra != da_tra_0
    assert TR.NOT_CHECKED_LABEL in khong_tra and "0 hồ sơ khớp" not in khong_tra
    assert "ĐÃ TRA THẬT" in da_tra_0

    # Dòng "Tham chiếu NCT" cũng từng gộp 2 trạng thái làm một.
    assert TR.format_prior_art_refs(TR.empty_registry(BASE_QUERY_EN, "timeout")) \
        != TR.format_prior_art_refs({"checked": True, "trials": []})


def test_prior_art_co_ket_qua_thi_in_bang_va_nct(monkeypatch, tmp_path):
    """Có prior art → bảng NCT thật, và mục 'Tham chiếu NCT' trỏ đúng link."""
    study = "PYTEST-G2-REG-HITS"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)
    _install_http(monkeypatch, total=2, active=1, studies=[
        {"protocolSection": {
            "identificationModule": {"nctId": "NCT01234567",
                                     "briefTitle": "Outpatient satisfaction survey"},
            "statusModule": {"overallStatus": "RECRUITING",
                             "startDateStruct": {"date": "2025-03"}},
            "designModule": {"studyType": "OBSERVATIONAL", "phases": [],
                             "enrollmentInfo": {"count": 400}},
            "conditionsModule": {"conditions": ["Patient Satisfaction"]},
        }},
    ])

    out_dir = _run_g2(monkeypatch, tmp_path, study)

    art = _artifact_text(out_dir, study)
    assert "NCT01234567" in art
    assert "https://clinicaltrials.gov/study/NCT01234567" in art
    assert "2 hồ sơ khớp" in art and "1 đang/sắp tuyển" in art
    assert TR.NOT_CHECKED_LABEL not in art

    cp = json.loads((out_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["clinicaltrials"]["samples"][0]["nct_id"] == "NCT01234567"
    assert cp["clinicaltrials_found"] == 2


def test_skip_registry_khong_gia_vo_da_tra(monkeypatch, tmp_path):
    """`--skip-registry` (offline) phải rơi vào nhánh CHƯA TRA ĐƯỢC, không phải 0."""
    study = "PYTEST-G2-REG-SKIP"
    _write_g0_checkpoint(_study_dir(tmp_path, study), topic=TOPIC_VI,
                         base_query=BASE_QUERY_EN)
    sent = _install_http(monkeypatch, total=1422, active=241)

    out_dir = _run_g2(monkeypatch, tmp_path, study, ["--skip-registry"])

    assert sent == [], "--skip-registry mà vẫn gọi mạng"
    cp = json.loads((out_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["clinicaltrials"]["checked"] is False
    assert cp["clinicaltrials"]["n_trials"] is None
    assert TR.NOT_CHECKED_LABEL in _artifact_text(out_dir, study)


# ════════════════════════════════════════════════════════════════════════════
# GỘP HAI ĐƯỜNG CODE — G0 và G2 phải dùng CHUNG một hàm tra
# ════════════════════════════════════════════════════════════════════════════

def test_g0_va_g2_dung_chung_mot_duong_tra_dang_ky():
    """Gộp thật: cùng một đối tượng hàm, không phải hai bản sao chép."""
    import run_g0_auto as G0
    assert G0.check_trial_registry is TR.check_trial_registry
    assert G2.lookup_prior_art("", 1)["checked"] is False  # đi qua cùng hợp đồng


def test_che_do_mock_khong_bia_prior_art(monkeypatch):
    """USE_MOCK_SOURCES=true → CHƯA TRA ĐƯỢC, tuyệt đối không bịa NCT."""
    from app.config import settings
    monkeypatch.setattr(settings, "use_mock_sources", True, raising=False)
    out = G2.lookup_prior_art(BASE_QUERY_EN)
    assert out["checked"] is False
    assert out["n_trials"] is None
    assert "mock" in (out["error"] or "").lower()
    assert out["trials"] == []


@pytest.mark.parametrize("truy_van_rong", ["", "   "])
def test_truy_van_rong_khong_goi_mang(monkeypatch, truy_van_rong):
    """Truy vấn rỗng → dừng sớm, không gọi mạng, không giả vờ đã tra."""
    sent = _install_http(monkeypatch, total=999, active=999)
    out = TR.check_trial_registry(truy_van_rong)
    assert sent == []
    assert out["checked"] is False and out["n_trials"] is None
