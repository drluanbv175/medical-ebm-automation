"""Hồi quy cho `app/sources/retraction_chain.py::RetractionChain` — CHƯA có test
file nào trước đây (đo được: 0 file trong tests/ tham chiếu RetractionChain),
đúng khoảng trống mà Workflow đối kháng đa-agent 2026-09-03 xác nhận qua chạy
THẬT (không mock hàm gộp, chỉ mock 2 client mạng — đúng cơ chế inject sẵn có
trong __init__).

Hai phát hiện (#3, #4) cùng nằm trong `RetractionChain.check()`:

  #3  Tầng Europe PMC (dự phòng) KHÔNG BAO GIỜ được hỏi khi PubMed trả
      status='unresolved' — kể cả khi 'unresolved' đó là do LỖI TẦNG API của
      NCBI (HTTP 200 hợp lệ nhưng KHÔNG chứa PubmedArticle nào cho CẢ LÔ,
      xem docstring PubMedClient._parse_retraction_xml) chứ không phải PMID
      thật sự không tồn tại. Nhánh xử lý bất đồng "một nguồn lấy được bản
      ghi, nguồn kia bảo không có" trong `_gop()` là DEAD CODE trước bản vá
      này vì `ep` không bao giờ được truyền dữ liệu cho một PMID có
      pm.status='unresolved'.

  #4  `sources_tried` trong kết quả trả về là MỘT list DÙNG CHUNG cho cả lô,
      không phải đúng những nguồn thực sự được hỏi cho TỪNG PMID — một PMID
      được PubMed trả lời dứt khoát (vd 'ok') và KHÔNG hề được Europe PMC
      hỏi tới vẫn bị ghi 'sources_tried': ['pubmed','europepmc'], làm sai
      lệch bằng chứng máy-kiểm trong receipt A12 đã ký.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.retraction_chain import RetractionChain  # noqa: E402


class _FakeRW:
    """Giả lập RetractionWatchIndex — tra cứu ngoại tuyến, không mạng."""

    def __init__(self, ready: bool = False, data: dict | None = None) -> None:
        self._ready = ready
        self._data = data or {}

    def san_sang(self) -> bool:
        return self._ready

    def tra(self, pmid: str):
        return self._data.get(pmid)


class _FakeClient:
    """Giả lập PubMedClient/EuropePMCClient — chỉ expose check_retraction_status()
    và ghi lại đúng danh sách pmid đã được gọi, để test xác minh AI ĐÃ ĐƯỢC HỎI
    (không chỉ kết quả cuối)."""

    def __init__(self, responses: dict) -> None:
        self._responses = responses
        self.called_with: list[list[str]] = []

    def check_retraction_status(self, pmids):
        self.called_with.append(list(pmids))
        return {p: self._responses[p] for p in pmids if p in self._responses}


def _ok(pmid="ok") -> dict:
    return {"status": "ok"}


def _unresolved() -> dict:
    return {"status": "unresolved", "reason": "PubMed không trả về bản ghi..."}


def _unknown_fetch_error() -> dict:
    return {"status": "unknown_fetch_error", "reason": "NCBI đang CHẶN máy này"}


# ── #3: Europe PMC chỉ được hỏi khi TOÀN BỘ lô cùng 'unresolved' ────────────


def test_europepmc_not_called_for_lone_unresolved_pmid_in_mixed_batch():
    """Đối chứng — hành vi CŨ phải giữ nguyên: 1 PMID 'unresolved' lẫn trong
    lô phần lớn giải quyết được (nhiều khả năng là trích dẫn ma thật) KHÔNG
    được kích hoạt Europe PMC — tránh gọi tràn lan theo đúng caveat của
    chính đợt vá này."""
    pubmed = _FakeClient({"AAA": _ok(), "BBB": _unresolved()})
    europepmc = _FakeClient({})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA", "BBB"])

    assert europepmc.called_with == []
    assert result["BBB"]["status"] == "unresolved"
    assert "europepmc" not in result["BBB"]["sources_tried"]


def test_europepmc_called_when_whole_batch_unresolved():
    """★ Ca chính của phát hiện #3: TOÀN BỘ lô 'unresolved' cùng lúc — dấu
    hiệu lỗi tầng API — phải kích hoạt Europe PMC cho các PMID đó."""
    pubmed = _FakeClient({"AAA": _unresolved(), "BBB": _unresolved()})
    europepmc = _FakeClient({"AAA": _ok(), "BBB": _unresolved()})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA", "BBB"])

    assert sorted(europepmc.called_with[0]) == ["AAA", "BBB"]
    # Europe PMC xác nhận AAA có thật ('ok') dù pubmed bảo 'unresolved' —
    # nhánh xử lý bất đồng trong _gop() (trước đây là dead code) phải chạy.
    assert result["AAA"]["status"] == "ok"
    assert result["AAA"]["source"] == "europepmc"
    assert "nghi lỗi tầng API" in result["AAA"].get("ghi_chu", "")
    # BBB vẫn 'unresolved' ở cả hai nguồn — không có cơ sở nói khác.
    assert result["BBB"]["status"] == "unresolved"


def test_single_pmid_batch_unresolved_also_triggers_europepmc():
    """Lô CHỈ MỘT PMID: 'toàn bộ lô unresolved' và 'một PMID lẻ tẻ unresolved'
    trùng nhau về mặt hình thức — vẫn phải cho phép kiểm chéo (tốn thêm đúng
    MỘT lệnh gọi, không phải 'tràn lan'), vì không có PMID nào khác trong lô
    để so sánh 'phần lớn giải quyết được' hay không."""
    pubmed = _FakeClient({"CCC": _unresolved()})
    europepmc = _FakeClient({"CCC": _ok()})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["CCC"])

    assert europepmc.called_with == [["CCC"]]
    assert result["CCC"]["status"] == "ok"


def test_khong_biet_status_still_triggers_europepmc_regardless_of_batch_shape():
    """Đối chứng: hành vi CŨ cho KHONG_BIET (unknown_fetch_error/
    unknown_mock_or_no_email) không đổi — vẫn kích hoạt kiểm chéo dù chỉ MỘT
    PMID trong lô rơi vào trạng thái đó (khác 'unresolved', vốn giờ cần TOÀN
    BỘ lô mới kích hoạt)."""
    pubmed = _FakeClient({"AAA": _ok(), "BBB": _unknown_fetch_error()})
    europepmc = _FakeClient({"BBB": _ok()})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA", "BBB"])

    assert europepmc.called_with == [["BBB"]]
    assert result["BBB"]["status"] == "ok"
    assert result["BBB"]["source"] == "europepmc"


# ── #4: sources_tried phải đúng THEO TỪNG PMID ──────────────────────────────


def test_sources_tried_excludes_europepmc_for_pmid_never_queried():
    """★ Ca chính của phát hiện #4: AAA được pubmed trả lời dứt khoát ('ok'),
    KHÔNG bao giờ được hỏi Europe PMC — sources_tried của AAA không được
    liệt europepmc, dù BBB trong CÙNG lô có được hỏi thật (dùng
    unknown_fetch_error cho BBB — trạng thái này LUÔN kích hoạt kiểm chéo,
    không phụ thuộc hình dạng cả lô như 'unresolved')."""
    pubmed = _FakeClient({"AAA": _ok(), "BBB": _unknown_fetch_error()})
    europepmc = _FakeClient({"BBB": _ok()})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA", "BBB"])

    assert europepmc.called_with == [["BBB"]]
    assert result["AAA"]["sources_tried"] == ["pubmed"]
    assert result["BBB"]["sources_tried"] == ["pubmed", "europepmc"]


def test_sources_tried_includes_retraction_watch_when_ready():
    rw = _FakeRW(ready=True, data={"AAA": {"status": "retracted", "reason": "test"}})
    pubmed = _FakeClient({"AAA": _ok()})
    europepmc = _FakeClient({})
    chain = RetractionChain(rw=rw, pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA"])

    assert result["AAA"]["sources_tried"] == ["retraction_watch", "pubmed"]
    # Retraction Watch có bản ghi DƯƠNG TÍNH → thắng, bất kể pubmed nói 'ok'.
    assert result["AAA"]["status"] == "retracted"
    assert result["AAA"]["source"] == "retraction_watch"


def test_sources_tried_omits_retraction_watch_when_not_ready():
    chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=_FakeClient({"AAA": _ok()}),
                             europepmc=_FakeClient({}))

    result = chain.check(["AAA"])

    assert "retraction_watch" not in result["AAA"]["sources_tried"]
    assert "CHƯA tải nền ngoại tuyến" not in result["AAA"].get("reason", "")  # status=ok, không chạm nhánh fail-closed


def test_sources_tried_empty_pubmed_absent_does_not_claim_pubmed_tried():
    """Tầng NCBI vắng mặt (mô phỏng máy thiếu thư viện) — sources_tried không
    được ghi 'pubmed'. Lưu ý: truyền pubmed=None cho __init__ KHÔNG tắt được
    tầng này (constructor tự dựng PubMedClient() thật khi tham số là None —
    hành vi sẵn có, không phải phần đang vá) — phải gán thẳng vào instance
    SAU KHI dựng để mô phỏng đúng 'thư viện thiếu' (PubMedClient = None ở
    module-level try/except)."""
    rw = _FakeRW(ready=True, data={})
    chain = RetractionChain(rw=rw, pubmed=_FakeClient({}), europepmc=_FakeClient({}))
    chain.pubmed = None

    result = chain.check(["AAA"])

    assert "pubmed" not in result["AAA"]["sources_tried"]


# ── Đối chứng chung — không phá vỡ hành vi đã có ────────────────────────────


def test_empty_pmid_list_returns_empty_dict():
    chain = RetractionChain(rw=_FakeRW(), pubmed=_FakeClient({}), europepmc=_FakeClient({}))
    assert chain.check([]) == {}


def test_fail_closed_when_no_source_resolves():
    """Không nguồn nào kết luận được → giữ KHÔNG BIẾT, không suy diễn 'ok'."""
    pubmed = _FakeClient({"AAA": _unknown_fetch_error()})
    europepmc = _FakeClient({"AAA": _unknown_fetch_error()})
    chain = RetractionChain(rw=_FakeRW(), pubmed=pubmed, europepmc=europepmc)

    result = chain.check(["AAA"])

    assert result["AAA"]["status"] == "unknown_fetch_error"
    assert result["AAA"]["source"] is None
