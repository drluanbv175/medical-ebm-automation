"""Hồi quy phát hiện MEDIUM/HIGH của Workflow đối kháng đa-agent 2026-09-05
(vòng 6, task #89) — CÙNG lỗi đã vá ở `app/sources/europepmc.py` (task #83,
xem `tests/test_europepmc_workflow_20260905_bad_record_isolation.py`) lặp lại
ở BỐN connector khác chưa từng được kiểm: `crossref.py`, `semantic_scholar.py`,
`openalex.py`, `clinicaltrials.py`.

CƠ CHẾ LỖI (giống hệt europepmc.py): vòng lặp phân tích bản ghi nằm CHUNG
try/except với lệnh gọi mạng. Một bản ghi có cấu trúc bất thường — đã tái
hiện thực nghiệm cho từng API:
  • Crossref: "author": None (thiếu metadata tác giả)
  • Semantic Scholar: "authors": None
  • OpenAlex: "concepts": null (khoá có mặt, giá trị None — .get(key, [])
    KHÔNG áp dụng default vì khoá đã tồn tại)
  • ClinicalTrials.gov: "protocolSection": null
— làm bay exception, bị khối except NGOÀI bắt và XOÁ SẠCH mọi bản ghi đã
phân tích thành công trước đó trong CÙNG trang, không chỉ bản ghi hỏng.

BẢN VÁ: tách vòng lặp phân tích khỏi try/except của lệnh gọi mạng (một
try/except MỚI, RIÊNG, bên trong vòng lặp) ở cả 4 file — lỗi 1 bản ghi chỉ
bỏ qua đúng bản ghi đó. Kèm 2 bản vá tận gốc (không chỉ cô lập): OpenAlex
`w.get("concepts") or []` (thay vì `w.get("concepts", [])`) và
ClinicalTrials `ps.get("identificationModule") or {}` (thay vì `..., {}`) —
áp dụng chuẩn "or {}"/"or []" nhất quán cho các trường lồng có thể là None.

Nguyên tắc viết test: mock `client.http.get_json` trả về payload có bản ghi
hỏng XEN GIỮA các bản ghi hợp lệ, gọi THẲNG `search()` thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.clinicaltrials import ClinicalTrialsClient  # noqa: E402
from app.sources.crossref import CrossrefClient  # noqa: E402
from app.sources.openalex import OpenAlexClient  # noqa: E402
from app.sources.semantic_scholar import SemanticScholarClient  # noqa: E402


def _client(cls, monkeypatch, response: dict):
    client = cls()
    client.use_mock = False
    monkeypatch.setattr(client.http, "get_json", lambda *a, **k: response)
    monkeypatch.setattr(client, "save_raw", lambda *a, **k: None)
    return client


class TestCrossrefBanGhiHongKhongLamRotCaTrang:
    def test_author_none_xen_giua_khong_lam_mat_ban_ghi_hop_le(self, monkeypatch):
        client = _client(CrossrefClient, monkeypatch, {"message": {"items": [
            {"DOI": "10.1/aaa", "title": ["Hợp lệ 1"], "author": [{"family": "A", "given": "B"}]},
            {"DOI": "10.1/bbb", "title": ["Hỏng"], "author": None},
            {"DOI": "10.1/ccc", "title": ["Hợp lệ 2"], "author": [{"family": "C", "given": "D"}]},
        ]}})
        out = client.search("test query")
        dois = {r.doi for r in out}
        assert dois == {"10.1/aaa", "10.1/ccc"}, f"kỳ vọng giữ 2 bản ghi hợp lệ, thực tế: {dois}"

    def test_khong_co_ban_ghi_hong_van_dung_nhu_cu(self, monkeypatch):
        client = _client(CrossrefClient, monkeypatch, {"message": {"items": [
            {"DOI": "10.1/aaa", "title": ["Hợp lệ 1"], "author": [{"family": "A", "given": "B"}]},
        ]}})
        out = client.search("test query")
        assert len(out) == 1

    def test_loi_mang_that_van_tra_ve_rong(self, monkeypatch):
        client = CrossrefClient()
        client.use_mock = False
        monkeypatch.setattr(client.http, "get_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down")))
        assert client.search("test query") == []


class TestSemanticScholarBanGhiHongKhongLamRotCaTrang:
    def test_authors_none_xen_giua_khong_lam_mat_ban_ghi_hop_le(self, monkeypatch):
        client = _client(SemanticScholarClient, monkeypatch, {"data": [
            {"paperId": "p1", "title": "Hợp lệ 1", "authors": [{"name": "A"}], "externalIds": {}},
            {"paperId": "p2", "title": "Hỏng", "authors": None, "externalIds": {}},
            {"paperId": "p3", "title": "Hợp lệ 2", "authors": [{"name": "B"}], "externalIds": {}},
        ]})
        out = client.search("test query")
        titles = {r.title for r in out}
        assert titles == {"Hợp lệ 1", "Hợp lệ 2"}, f"kỳ vọng giữ 2 bản ghi hợp lệ, thực tế: {titles}"

    def test_khong_co_ban_ghi_hong_van_dung_nhu_cu(self, monkeypatch):
        client = _client(SemanticScholarClient, monkeypatch, {"data": [
            {"paperId": "p1", "title": "Hợp lệ 1", "authors": [{"name": "A"}], "externalIds": {}},
        ]})
        out = client.search("test query")
        assert len(out) == 1

    def test_loi_mang_that_van_tra_ve_rong(self, monkeypatch):
        client = SemanticScholarClient()
        client.use_mock = False
        monkeypatch.setattr(client.http, "get_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down")))
        assert client.search("test query") == []


class TestOpenAlexBanGhiHongKhongLamRotCaTrang:
    def test_work_none_xen_giua_khong_lam_mat_ban_ghi_hop_le(self, monkeypatch):
        """Kiểm ISOLATION thuần (không phụ thuộc bản vá tận gốc concepts) —
        một phần tử `None` trong mảng results (dữ liệu không đồng nhất từ
        API bên ngoài) vẫn phải chỉ mất đúng phần tử đó."""
        client = _client(OpenAlexClient, monkeypatch, {"results": [
            {"id": "https://openalex.org/W1", "title": "Hợp lệ 1", "doi": "https://doi.org/10.1/aaa", "concepts": []},
            None,
            {"id": "https://openalex.org/W3", "title": "Hợp lệ 2", "doi": "https://doi.org/10.1/ccc", "concepts": []},
        ]})
        out = client.search("test query")
        dois = {r.doi for r in out}
        assert dois == {"10.1/aaa", "10.1/ccc"}, f"kỳ vọng giữ 2 bản ghi hợp lệ, thực tế: {dois}"

    def test_concepts_none_van_duoc_phan_tich_dung_khong_bi_bo_qua(self, monkeypatch):
        """Bản vá tận gốc: `concepts: null` không còn crash NÊN bản ghi này
        PHẢI được giữ lại (khác europepmc.py — nơi bản ghi hỏng bị bỏ qua
        hẳn vì không có cách sửa tận gốc chung)."""
        client = _client(OpenAlexClient, monkeypatch, {"results": [
            {"id": "https://openalex.org/W2", "title": "Có concepts null",
             "doi": "https://doi.org/10.1/bbb", "concepts": None},
        ]})
        out = client.search("test query")
        assert len(out) == 1
        assert out[0].keywords == []

    def test_khong_co_ban_ghi_hong_van_dung_nhu_cu(self, monkeypatch):
        client = _client(OpenAlexClient, monkeypatch, {"results": [
            {"id": "https://openalex.org/W1", "title": "Hợp lệ 1", "doi": "https://doi.org/10.1/aaa",
             "concepts": [{"display_name": "x"}]},
        ]})
        out = client.search("test query")
        assert len(out) == 1
        assert out[0].keywords == ["x"]

    def test_loi_mang_that_van_tra_ve_rong(self, monkeypatch):
        client = OpenAlexClient()
        client.use_mock = False
        monkeypatch.setattr(client.http, "get_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down")))
        assert client.search("test query") == []


class TestClinicalTrialsBanGhiHongKhongLamRotCaTrang:
    def test_study_none_xen_giua_khong_lam_mat_ban_ghi_hop_le(self, monkeypatch):
        """Kiểm ISOLATION thuần (không phụ thuộc bản vá tận gốc
        protocolSection) — một phần tử `None` trong mảng studies vẫn phải
        chỉ mất đúng phần tử đó."""
        client = _client(ClinicalTrialsClient, monkeypatch, {"studies": [
            {"protocolSection": {"identificationModule": {"nctId": "NCT001", "briefTitle": "Hợp lệ 1"},
                                  "statusModule": {}}},
            None,
            {"protocolSection": {"identificationModule": {"nctId": "NCT003", "briefTitle": "Hợp lệ 2"},
                                  "statusModule": {}}},
        ]})
        out = client.search("test query")
        ncts = {r.nct_id for r in out}
        assert ncts == {"NCT001", "NCT003"}, f"kỳ vọng giữ 2 bản ghi hợp lệ, thực tế: {ncts}"

    def test_protocol_section_none_van_duoc_phan_tich_dung_khong_bi_bo_qua(self, monkeypatch):
        """Bản vá tận gốc: `protocolSection: null` không còn crash NÊN bản
        ghi này PHẢI được giữ lại (title rỗng, nct_id=None — đúng dữ liệu
        thật của nó, không phải bị vứt bỏ)."""
        client = _client(ClinicalTrialsClient, monkeypatch, {"studies": [
            {"protocolSection": None},
        ]})
        out = client.search("test query")
        assert len(out) == 1
        assert out[0].nct_id is None

    def test_khong_co_ban_ghi_hong_van_dung_nhu_cu(self, monkeypatch):
        client = _client(ClinicalTrialsClient, monkeypatch, {"studies": [
            {"protocolSection": {"identificationModule": {"nctId": "NCT001", "briefTitle": "Hợp lệ 1"},
                                  "statusModule": {}}},
        ]})
        out = client.search("test query")
        assert len(out) == 1

    def test_loi_mang_that_van_tra_ve_rong(self, monkeypatch):
        client = ClinicalTrialsClient()
        client.use_mock = False
        monkeypatch.setattr(client.http, "get_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down")))
        assert client.search("test query") == []
