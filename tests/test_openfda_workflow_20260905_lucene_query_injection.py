"""Hồi quy phát hiện LOW của Workflow đối kháng đa-agent 2026-09-04 (vòng 2,
task #75): `app/sources/openfda.py::OpenFDAClient.search()` — chuỗi `query`
được nhét THẲNG vào cụm trích dẫn Lucene, không thoát dấu `"`.

CƠ CHẾ LỖI: openFDA (nền Elasticsearch) dùng cú pháp truy vấn Lucene —
`field:"cụm từ"` là khớp NGUYÊN CỤM. Dòng gốc
    params = {"search": f'patient.drug.medicinalproduct:"{query}"', ...}
nhét `query` thẳng vào giữa hai dấu `"` mà không thoát bất kỳ dấu `"` nào
CÓ SẴN trong `query`. Nếu `query` chứa `"` (ví dụ một chuỗi truy vấn lắp
ghép từ nhiều nguồn, hoặc dữ liệu nhập không kiểm soát), dấu đó sẽ ĐÓNG cụm
trích dẫn SỚM — phần còn lại của `query` rơi ra ngoài dấu ngoặc và bị
Lucene diễn giải như CÚ PHÁP TRUY VẤN THÊM (toán tử `AND`/`OR`, ký tự đại
diện, hoặc bộ lọc trường khác `field:value`) thay vì dữ liệu văn bản thuần
— một dạng "query injection" qua chuỗi định dạng không thoát ký tự.

BẢN VÁ: `_escape_lucene_phrase()` thoát dấu gạch chéo ngược (trước) rồi `"`
(sau) — đúng thứ tự bắt buộc để không thoát đúp dấu gạch chéo ngược mới
sinh ra khi thoát `"`.

Nguyên tắc viết test: gọi THẲNG `_escape_lucene_phrase()` và
`OpenFDAClient.search()` thật (mock tầng HTTP để bắt tham số `search` đã
xây dựng), không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.openfda import OpenFDAClient, _escape_lucene_phrase  # noqa: E402


class TestEscapeLucenePhraseHamNguon:
    """★★ Ca chính — hàm thoát ký tự tự thân, kiểm trực tiếp không qua HTTP."""

    def test_dau_ngoac_kep_duoc_thoat(self):
        assert _escape_lucene_phrase('drug"injected') == 'drug\\"injected'

    def test_dau_gach_cheo_nguoc_duoc_thoat_truoc(self):
        """Thứ tự BẮT BUỘC: thoát gạch chéo ngược trước `"`. Nếu đảo ngược,
        một chuỗi `\\"` có sẵn trong input sẽ bị thoát đúp sai."""
        assert _escape_lucene_phrase('a\\"b') == 'a\\\\\\"b'

    def test_chuoi_binh_thuong_khong_doi(self):
        assert _escape_lucene_phrase("aspirin") == "aspirin"

    def test_ket_qua_khong_con_dau_ngoac_kep_tho(self):
        """Đối chứng ngữ nghĩa quan trọng nhất — sau khi thoát, MỌI dấu `"`
        còn lại trong chuỗi kết quả đều phải có gạch chéo ngược đứng ngay
        trước nó (không còn dấu `"` "trần" nào có thể đóng cụm trích dẫn sớm)."""
        ket_qua = _escape_lucene_phrase('drug"name"here')
        i = 0
        while True:
            i = ket_qua.find('"', i)
            if i == -1:
                break
            assert ket_qua[i - 1] == "\\", f"dấu \" ở vị trí {i} không có \\ đứng trước"
            i += 1


class TestSearchXayDungParamsAnToan:
    """★★ Ca tích hợp — search() thật (mock HttpClient.get_json) phải gửi
    tham số `search` đã thoát, không còn dấu `"` trần từ query gốc."""

    def _client(self, monkeypatch):
        c = OpenFDAClient()
        c.use_mock = False
        goi: dict = {}

        def _fake_get_json(url, params=None, use_cache=True):
            goi["params"] = params
            return {"results": []}

        monkeypatch.setattr(c.http, "get_json", _fake_get_json)
        monkeypatch.setattr(c, "save_raw", lambda *a, **k: None)
        return c, goi

    def test_query_co_dau_ngoac_kep_duoc_thoat_truoc_khi_gui(self, monkeypatch):
        client, goi = self._client(monkeypatch)
        client.search('drug" OR patient.patientdeath.patientdeathdate:*')
        search_param = goi["params"]["search"]
        assert search_param == (
            'patient.drug.medicinalproduct:"drug\\" OR '
            'patient.patientdeath.patientdeathdate:*"'
        )
        # Đối chứng ngữ nghĩa: cụm trích dẫn phải ĐÓNG ở cuối chuỗi (dấu `"`
        # cuối cùng không có `\` đứng trước) — chứng minh toàn bộ payload độc
        # hại nằm TRỌN trong một cụm trích dẫn, không rò ra ngoài.
        assert search_param.endswith('*"')
        assert not search_param.endswith('\\"')

    def test_query_binh_thuong_khong_doi_hanh_vi(self, monkeypatch):
        client, goi = self._client(monkeypatch)
        client.search("aspirin")
        assert goi["params"]["search"] == 'patient.drug.medicinalproduct:"aspirin"'
