"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 6,
task #91) trong
`app/evidence/citation_validator.py::validate_identifier()` — citation có
`pmid` bị nhiễm bẩn KÈM `doi` hợp lệ bị báo `valid=False` vì hàm dừng ngay
ở nhánh pmid, không bao giờ xét tới doi.

CƠ CHẾ LỖI: bản gốc trả về NGAY khi gặp trường ĐẦU TIÊN có mặt
(`if pmid: return CitationValidation(bool(_PMID.match(pmid)), ...)`), bất
kể trường đó có ĐÚNG ĐỊNH DẠNG hay không. Một citation có `pmid` dán nhầm
kiểu "PMID:12345678" (thay vì "12345678" — lỗi copy-paste thực tế thường
gặp) NHƯNG có `doi` hợp lệ đi kèm sẽ bị `validate_identifier()` báo
`valid=False`, dù `doi` đủ để truy nguyên trích dẫn.

PHẠM VI: file này chỉ được `app/evidence/citation_verification.py` import —
một nhánh MỒ CÔI đã được xác nhận qua
`tests/test_no_orphaned_citation_verification_in_real_gates.py` (không cổng
G0-G10 thật nào gọi tới). Vẫn vá vì đây là code THẬT, có test, cùng họ các
nhánh mồ côi khác mà CLAUDE.md tự khai lịch sử.

BẢN VÁ: thử LẦN LƯỢT từng định danh theo thứ tự ưu tiên cũ (pmid > doi >
url), CHỈ dừng khi một định danh THỰC SỰ khớp định dạng; không định danh
nào khớp mới báo lỗi (dùng định danh đầu tiên có mặt để gắn nhãn lỗi, giữ
đúng hành vi báo lỗi cũ khi chỉ có một trường và nó sai).

Nguyên tắc viết test: gọi THẲNG `validate_identifier()` thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.citation_validator import validate_identifier  # noqa: E402


class TestPmidNhiemBanKemDoiHopLeVanDuocChapNhan:
    """★★★ Ca chính — pmid dán nhầm kèm doi hợp lệ phải được chấp nhận qua
    doi, không bị báo lỗi vì pmid sai."""

    def test_pmid_dang_prefix_kem_doi_hop_le_duoc_chap_nhan_qua_doi(self):
        result = validate_identifier({"pmid": "PMID:12345678", "doi": "10.1056/NEJMoa2034577"})
        assert result.valid is True
        assert result.identifier_type == "doi"

    def test_pmid_rong_kem_url_hop_le_duoc_chap_nhan_qua_url(self):
        """Cùng cơ chế lỗi, kiểm tra tổ hợp pmid sai + url hợp lệ (không có
        doi) — đảm bảo bản vá không chỉ xử lý riêng cặp pmid/doi."""
        result = validate_identifier({"pmid": "khong-phai-so", "url": "https://example.org/guideline"})
        assert result.valid is True
        assert result.identifier_type == "url"


class TestChiMotDinhDanhSaiVanBaoLoiNhuCu:
    """Đối chứng bắt buộc — hành vi gốc (chỉ một định danh, sai định dạng)
    không đổi: vẫn báo valid=False, gắn đúng nhãn định danh đó."""

    def test_chi_co_pmid_sai_van_bao_loi(self):
        result = validate_identifier({"pmid": "not-a-pmid"})
        assert result.valid is False
        assert result.identifier_type == "pmid"

    def test_chi_co_doi_sai_van_bao_loi(self):
        result = validate_identifier({"doi": "khong-phai-doi"})
        assert result.valid is False
        assert result.identifier_type == "doi"

    def test_khong_co_dinh_danh_nao_van_bao_thieu(self):
        result = validate_identifier({})
        assert result.valid is False
        assert result.identifier_type == "none"


class TestDinhDanhDungNgayTuDauVanDuocChapNhanNhuCu:
    """Đối chứng bắt buộc — pmid/doi/url ĐÚNG định dạng ngay từ đầu (không
    cần lùi về định danh khác) vẫn hoạt động như hành vi gốc."""

    def test_pmid_dung_duoc_chap_nhan(self):
        result = validate_identifier({"pmid": "12345678"})
        assert result.valid is True
        assert result.identifier_type == "pmid"

    def test_doi_dung_duoc_chap_nhan(self):
        result = validate_identifier({"doi": "10.1000/test"})
        assert result.valid is True
        assert result.identifier_type == "doi"

    def test_pmid_dung_thang_khong_can_lui_ve_doi(self):
        """Khi pmid ĐÃ ĐÚNG, không được lùi xuống kiểm tra doi (dù doi có
        mặt và cũng đúng) — pmid vẫn thắng theo đúng thứ tự ưu tiên cũ."""
        result = validate_identifier({"pmid": "12345678", "doi": "10.1000/test"})
        assert result.valid is True
        assert result.identifier_type == "pmid"
