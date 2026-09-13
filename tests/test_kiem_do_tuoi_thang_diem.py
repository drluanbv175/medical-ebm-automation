"""Kiểm `tools/kiem_do_tuoi_thang_diem.py` — kiểm rút bài + độ tươi cho 32 thang
điểm lâm sàng "verified" (khoảng trống đo được 13/09/2026: kho này có 0 cơ chế
tự động tái-kiểm định kỳ trước khi công cụ này ra đời).

Tất cả test ở đây OFFLINE — tiêm sẵn RetractionChain/CrossrefRetraction giả
qua monkeypatch, KHÔNG gọi mạng thật (mạng thật chỉ chạy khi bác sĩ/lịch quý
gọi tay `python tools/kiem_do_tuoi_thang_diem.py`).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(TOOLS_DIR))

import kiem_do_tuoi_thang_diem as CLI  # noqa: E402

from app.clinical_scores.verified import VERIFIED_SCORES  # noqa: E402


class _FakeChain:
    """Giả RetractionChain — .check(pmids) trả đúng shape thật, không gọi mạng."""

    def __init__(self, ket_qua: Dict[str, dict]) -> None:
        self._ket_qua = ket_qua

    def check(self, pmids: List[str]) -> Dict[str, dict]:
        return {p: self._ket_qua.get(p, {"status": "ok"}) for p in pmids}


class _FakeCrossref:
    def __init__(self, ket_qua: Dict[str, dict]) -> None:
        self._ket_qua = ket_qua

    def check(self, dois: List[str]) -> Dict[str, dict]:
        return {d: self._ket_qua.get(d, {"status": "ok"}) for d in dois}


@pytest.fixture(autouse=True)
def _co_lap_state_path(tmp_path, monkeypatch):
    """Không bao giờ chạm state/kiem-thang-diem-quy.json thật khi chạy test."""
    monkeypatch.setattr(CLI, "STATE_PATH", tmp_path / "kiem-thang-diem-quy.json")
    yield


# ════════════════════════════════════════════════════════════════════════════
# thu_thap_dinh_danh() — độ phủ đúng 32 thang điểm
# ════════════════════════════════════════════════════════════════════════════

def test_thu_thap_dinh_danh_dem_du_32_thang():
    items = CLI.thu_thap_dinh_danh()
    assert len(items) == len(VERIFIED_SCORES) == 32
    assert {it["score_id"] for it in items} == {s["score_id"] for s in VERIFIED_SCORES}


def test_moi_thang_co_dung_mot_trong_ba_trang_thai_dinh_danh():
    """Mỗi thang: có PMID, HOẶC chỉ có DOI, HOẶC không có gì — không lẫn lộn."""
    for it in CLI.thu_thap_dinh_danh():
        co_pmid = bool(it["pmid"])
        co_doi = bool(it["doi"])
        assert co_pmid or co_doi or (not co_pmid and not co_doi)


# ════════════════════════════════════════════════════════════════════════════
# kiem_day_du() — phân loại đúng theo trạng thái chuỗi rút bài
# ════════════════════════════════════════════════════════════════════════════

def test_kiem_day_du_moi_pmid_ok_khong_co_van_de():
    chain = _FakeChain({})  # rỗng -> mọi PMID mặc định "ok" theo _FakeChain
    crossref = _FakeCrossref({})
    ket_qua = CLI.kiem_day_du(chain=chain, crossref=crossref)

    assert ket_qua["n_scores"] == 32
    van_de = [h for h in ket_qua["hang_muc"] if h["ket_qua"]["status"] in CLI._VAN_DE]
    assert van_de == []


def test_kiem_day_du_bat_dung_pmid_bi_rut():
    # cha2ds2_vasc có PMID 19762550 (verified.py) — gài "retracted" cho đúng nó.
    chain = _FakeChain({"19762550": {"status": "retracted",
                                      "reason": "giả lập cho test"}})
    ket_qua = CLI.kiem_day_du(chain=chain, crossref=_FakeCrossref({}))

    hang = next(h for h in ket_qua["hang_muc"] if h["score_id"] == "cha2ds2_vasc")
    assert hang["ket_qua"]["status"] == "retracted"
    van_de = [h for h in ket_qua["hang_muc"] if h["ket_qua"]["status"] in CLI._VAN_DE]
    assert len(van_de) == 1
    assert van_de[0]["score_id"] == "cha2ds2_vasc"


def test_kiem_day_du_khong_kiem_duoc_van_tinh_la_van_de():
    """BH27 (đã vá ở check_citation_retraction.py): 'không kiểm được' PHẢI là
    một vấn đề, KHÔNG được fail-open thành sạch. Test này khoá đúng nguyên tắc
    đó cho công cụ mới."""
    chain = _FakeChain({"19762550": {"status": "unknown_fetch_error",
                                      "reason": "mạng lỗi giả lập"}})
    ket_qua = CLI.kiem_day_du(chain=chain, crossref=_FakeCrossref({}))
    van_de = [h for h in ket_qua["hang_muc"] if h["ket_qua"]["status"] in CLI._VAN_DE]
    assert len(van_de) == 1
    assert van_de[0]["score_id"] == "cha2ds2_vasc"


def test_kiem_day_du_doi_only_dung_crossref():
    # kdigo_grid: pmid=None, doi='10.1016/j.kint.2023.10.018' trong verified.py.
    crossref = _FakeCrossref({"10.1016/j.kint.2023.10.018": {"status": "retracted",
                                                              "reason": "giả lập"}})
    ket_qua = CLI.kiem_day_du(chain=_FakeChain({}), crossref=crossref)
    hang = next(h for h in ket_qua["hang_muc"] if h["score_id"] == "kdigo_grid")
    assert hang["nguon_kiem"] == "doi"
    assert hang["ket_qua"]["status"] == "retracted"


def test_kiem_day_du_khong_co_dinh_danh_khong_bi_coi_la_van_de():
    """BH08: thiếu nguyên liệu (báo cáo/sách không có PMID/DOI) không phải bằng
    chứng nguy hiểm — 3-4 mục như news2/nyha/gold_abe không được lọt vào _VAN_DE."""
    ket_qua = CLI.kiem_day_du(chain=_FakeChain({}), crossref=_FakeCrossref({}))
    khong_dd = [h for h in ket_qua["hang_muc"] if h["ket_qua"]["status"] == "khong_co_dinh_danh"]
    assert khong_dd, "phải có ít nhất 1 thang không PMID/DOI (news2/nyha/gold_abe)"
    for h in khong_dd:
        assert h["ket_qua"]["status"] not in CLI._VAN_DE


# ════════════════════════════════════════════════════════════════════════════
# main() — exit code + JSON PHẢI SẠCH (đúng bug thật đã bắt được và vá khi
# xây công cụ này: bản đầu in thêm dòng văn xuôi SAU khối json.dumps, phá định
# dạng JSON thuần cả ở nhánh sạch lẫn nhánh có vấn đề)
# ════════════════════════════════════════════════════════════════════════════

def _chay_main(monkeypatch, argv, chain=None, crossref=None):
    monkeypatch.setattr(CLI, "RetractionChain", lambda: chain or _FakeChain({}))
    monkeypatch.setattr(CLI, "CrossrefRetraction", lambda: crossref or _FakeCrossref({}))
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", *argv])
    return CLI.main()


def test_main_json_sach_la_json_thuan_khong_lan_van_ban(monkeypatch, capsys):
    rc = _chay_main(monkeypatch, ["--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)  # phải parse được — không có dòng thừa sau khối JSON
    assert data["n_scores"] == 32


def test_main_json_co_van_de_van_la_json_thuan(monkeypatch, capsys):
    """Regression trực tiếp cho bug đã bắt được: nhánh CÓ vấn đề càng dễ in thừa
    dòng '🔴 ... ĐỌC NGAY' phía sau — đây đúng là nhánh code cũ bị vỡ."""
    chain = _FakeChain({"19762550": {"status": "retracted", "reason": "giả lập"}})
    rc = _chay_main(monkeypatch, ["--json"], chain=chain)
    out = capsys.readouterr().out
    assert rc == 1
    data = json.loads(out)  # KHÔNG được ném json.JSONDecodeError
    van_de = [h for h in data["hang_muc"] if h["ket_qua"]["status"] in CLI._VAN_DE]
    assert len(van_de) == 1


def test_main_text_mode_bao_do_khi_co_rut_bai(monkeypatch, capsys):
    chain = _FakeChain({"19762550": {"status": "retracted", "reason": "giả lập"}})
    rc = _chay_main(monkeypatch, [], chain=chain)
    out = capsys.readouterr().out
    assert rc == 1
    assert "🔴" in out
    assert "ĐỌC NGAY" in out


def test_main_text_mode_sach_in_dung_dong_ket(monkeypatch, capsys):
    rc = _chay_main(monkeypatch, [])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Không phát hiện rút bài" in out
    assert "Cần bác sĩ kiểm chứng." in out


def test_main_ghi_so_sau_khi_chay_day_du(monkeypatch):
    _chay_main(monkeypatch, [])
    assert CLI.STATE_PATH.exists()
    so = json.loads(CLI.STATE_PATH.read_text(encoding="utf-8"))
    assert so["n_scores"] == 32
    assert so["n_van_de"] == 0


def test_main_loi_cong_cu_tra_ve_ma_2_khong_phai_1(monkeypatch, capsys):
    def _no(*a, **kw):
        raise RuntimeError("lỗi giả lập")
    monkeypatch.setattr(CLI, "kiem_day_du", _no)
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py"])
    rc = CLI.main()
    assert rc == 2  # KHÔNG lẫn với mã 1 (= có phát hiện), lỗi công cụ ≠ phát hiện


# ════════════════════════════════════════════════════════════════════════════
# --nhanh — chỉ đọc sổ, không gọi mạng
# ════════════════════════════════════════════════════════════════════════════

def test_nhanh_chua_tung_chay_tra_ve_1(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", "--nhanh"])
    rc = CLI.main()
    assert rc == 1
    assert "CHƯA TỪNG CHẠY" in capsys.readouterr().out


def test_nhanh_con_han_tra_ve_0(monkeypatch, capsys):
    moc = datetime.now(timezone.utc) - timedelta(days=10)
    CLI.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLI.STATE_PATH.write_text(json.dumps({"checked_at": moc.isoformat()}),
                               encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", "--nhanh"])
    rc = CLI.main()
    assert rc == 0
    assert "Còn trong hạn" in capsys.readouterr().out


def test_nhanh_qua_han_tra_ve_1(monkeypatch, capsys):
    moc = datetime.now(timezone.utc) - timedelta(days=CLI.NGUONG_QUA_HAN_NGAY + 5)
    CLI.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLI.STATE_PATH.write_text(json.dumps({"checked_at": moc.isoformat()}),
                               encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", "--nhanh"])
    rc = CLI.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "QUÁ HẠN" in out


def test_nhanh_json_khong_lan_van_ban(monkeypatch, capsys):
    moc = datetime.now(timezone.utc) - timedelta(days=10)
    CLI.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLI.STATE_PATH.write_text(json.dumps({"checked_at": moc.isoformat()}),
                               encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", "--nhanh", "--json"])
    rc = CLI.main()
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["qua_han"] is False


def test_nhanh_so_hong_tra_ve_2(monkeypatch, capsys):
    CLI.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLI.STATE_PATH.write_text(json.dumps({"checked_at": "khong-phai-ngay-hop-le"}),
                               encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", ["kiem_do_tuoi_thang_diem.py", "--nhanh"])
    rc = CLI.main()
    assert rc == 2
