"""Kiểm connector PMC full-text (`app/sources/pmc_guideline_fulltext.py`) — thêm
23/09/2026, VIẾT LẠI cùng ngày (audit/14 vấn đề 4) sau khi đổi cơ chế từ scrape HTML
`pmc.ncbi.nlm.nih.gov` (bị chặn 403) sang bucket S3 công khai `pmc-oa-opendata`
(PMC Open Access Subset chính thức của NCBI). Tất cả test OFFLINE, không gọi mạng
thật.

MỞ RỘNG 13/10/2026 — chọn phiên bản theo tài liệu chính thức PMC Cloud Service
(`pmc.ncbi.nlm.nih.gov/tools/pmcaws/` + `README.txt` của bucket): số phiên bản lớn hơn
KHÔNG có nghĩa là mới hơn; một PMCID có thể giữ cả bản thảo tác giả lẫn bản công bố; có
thể có `.2` mà không có `.1`; mỗi phiên bản có JSON `is_manuscript`/`is_retracted`/
`license_code`/`text_url?md5=`. Bucket giả `_BucketGia` dựng danh mục `delimiter=/` và JSON
theo ĐÚNG định dạng đo bằng WebFetch 13/10/2026 (PMC13555224 một phiên bản; PMC12805672
chỉ có `.2`, bản thảo tác giả, boolean JSON thật).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.pmc_guideline_fulltext import PmcGuidelineFullTextClient  # noqa: E402

_S3_GOC = "https://pmc-oa-opendata.s3.amazonaws.com/"

# Định dạng thật đo 13/10/2026: `?list-type=2&prefix=PMC12805672.&delimiter=/` — tài liệu PMC
# lấy chính PMCID này làm ví dụ «có .2 mà không có .1».
_XML_THAT_CHI_CO_BAN_2 = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>pmc-oa-opendata</Name>'
    "<Prefix>PMC12805672.</Prefix><KeyCount>1</KeyCount><MaxKeys>1000</MaxKeys><Delimiter>/</Delimiter>"
    "<IsTruncated>false</IsTruncated><CommonPrefixes><Prefix>PMC12805672.2/</Prefix></CommonPrefixes>"
    "</ListBucketResult>"
)

_NOI_DUNG_TXT_MAU = "JOURNAL INFORMATION\n==============================\nNoi dung guideline that."
_TXT_MAU = _NOI_DUNG_TXT_MAU.encode("utf-8")


def _md5(du_lieu: bytes) -> str:
    return hashlib.md5(du_lieu).hexdigest()


def _xml_liet_ke(pmcid: str, phien_ban: List[int], bi_cat: bool = False) -> str:
    """Danh mục ListObjectsV2 có `delimiter=/` — cùng khuôn `_XML_THAT_CHI_CO_BAN_2`."""
    cac_tien_to = "".join(f"<CommonPrefixes><Prefix>{pmcid}.{n}/</Prefix></CommonPrefixes>" for n in phien_ban)
    co_cat = "true" if bi_cat else "false"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>pmc-oa-opendata</Name>'
        f"<Prefix>{pmcid}.</Prefix><KeyCount>{len(phien_ban)}</KeyCount><MaxKeys>1000</MaxKeys>"
        f"<Delimiter>/</Delimiter><IsTruncated>{co_cat}</IsTruncated>{cac_tien_to}</ListBucketResult>"
    )


def _meta(ma: str, so: int, *, txt: bytes = _TXT_MAU, is_manuscript: Any = False,
          is_retracted: Any = False, license_code: str = "CC BY", **ghi_de: Any) -> Dict[str, Any]:
    """JSON siêu dữ liệu một phiên bản, đúng các khoá đo ở PMC13555224.1 / PMC12805672.2.
    `ghi_de` đè thẳng khoá JSON (kể cả `pmcid`/`version`/`text_url`) để dựng ca lệch."""
    md5_xml = "0" * 32
    md: Dict[str, Any] = {
        "pmcid": ma, "version": so, "is_pmc_openaccess": True,
        "is_manuscript": is_manuscript, "is_historical_ocr": False, "is_retracted": is_retracted,
        "license_code": license_code,
        "xml_url": f"s3://pmc-oa-opendata/{ma}.{so}/{ma}.{so}.xml?md5={md5_xml}",
        "text_url": f"s3://pmc-oa-opendata/{ma}.{so}/{ma}.{so}.txt?md5={_md5(txt)}",
    }
    md.update(ghi_de)
    return md


class _BucketGia:
    """Bucket S3 giả. `json_phien_ban`: {n: dict | bytes | Exception}; `txt`: {n: bytes |
    Exception} (mặc định `_TXT_MAU` cho mọi phiên bản). Danh mục tự dựng từ khoá của
    `json_phien_ban`, trừ khi truyền `liet_ke` (chuỗi XML hoặc ngoại lệ). Key không có ⇒
    ném lỗi như 404 NoSuchKey của `HttpClient`. Ghi lại mọi lời gọi để test soi."""

    def __init__(self, pmcid: str, json_phien_ban: Dict[int, Any],
                 txt: Optional[Dict[int, Any]] = None, liet_ke: Any = None) -> None:
        self.pmcid = pmcid
        self.json_phien_ban = json_phien_ban
        self.txt = txt if txt is not None else {n: _TXT_MAU for n in json_phien_ban}
        self.liet_ke = liet_ke
        self.goi_get_text: List[tuple] = []
        self.goi_get_bytes: List[str] = []

    def gan(self, monkeypatch, client: PmcGuidelineFullTextClient) -> "_BucketGia":
        monkeypatch.setattr(client.http, "get_text", self.get_text)
        monkeypatch.setattr(client.http, "get_bytes", self.get_bytes)
        return self

    def get_text(self, url, params=None, **kw):
        self.goi_get_text.append((url, params, kw))
        assert url == _S3_GOC, f"get_text chỉ được dùng để liệt kê bucket, không tải {url}"
        if isinstance(self.liet_ke, Exception):
            raise self.liet_ke
        if self.liet_ke is not None:
            return self.liet_ke
        return _xml_liet_ke(self.pmcid, sorted(self.json_phien_ban))

    def get_bytes(self, url, params=None):
        self.goi_get_bytes.append(url)
        khop = re.fullmatch(r"(PMC\d+)\.(\d+)/\1\.\2\.(json|txt)", url[len(_S3_GOC):])
        assert url.startswith(_S3_GOC) and khop, f"URL lạ: {url}"
        n = int(khop.group(2))
        kho = self.json_phien_ban if khop.group(3) == "json" else self.txt
        if n not in kho:
            raise RuntimeError(f"404 Client Error: Not Found (NoSuchKey) for url: {url}")
        gia_tri = kho[n]
        if isinstance(gia_tri, Exception):
            raise gia_tri
        if isinstance(gia_tri, dict):
            return json.dumps(gia_tri).encode("utf-8")
        return gia_tri

    @property
    def da_tai_txt(self) -> List[str]:
        return [u for u in self.goi_get_bytes if u.endswith(".txt")]


@pytest.fixture(autouse=True)
def _bat_pmc(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", True)
    yield


def _mot_phien_ban(monkeypatch, client, txt: bytes = _TXT_MAU) -> _BucketGia:
    return _BucketGia("PMC13555224", {1: _meta("PMC13555224", 1, txt=txt)}, txt={1: txt}).gan(monkeypatch, client)


# ════════════════════════════════════════════════════════════════════════════
# Hành vi cơ bản (giữ từ 23/09/2026)
# ════════════════════════════════════════════════════════════════════════════

def test_pmc_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_PMC_GUIDELINE_FULLTEXT"):
        PmcGuidelineFullTextClient()


def test_tai_toan_van_normalizes_pmcid_without_prefix(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _mot_phien_ban(monkeypatch, client)
    kq = client.tai_toan_van("13555224")  # KHÔNG có tiền tố "PMC"
    assert kq.thanh_cong is True
    assert "PMC13555224.1/PMC13555224.1.txt" in kq.url_nguon


def test_tai_toan_van_rejects_invalid_pmcid_format_without_network_call(monkeypatch):
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC1", {}).gan(monkeypatch, client)
    kq = client.tai_toan_van("khong-phai-pmcid")
    assert kq.thanh_cong is False
    assert bucket.goi_get_text == [] and bucket.goi_get_bytes == []


def test_tai_toan_van_returns_honest_failure_when_not_in_oa_subset(monkeypatch):
    """Hồi quy cho ca thật ADA Standards of Care (PMC12690171) — danh mục trọn vẹn 0 phiên bản
    PHẢI báo rõ "không có trong PMC Open Access Subset", KHÔNG được đọc thành lỗi mạng
    (đúng nguyên tắc "báo trung thực" — thiếu deposit là sự thật của nguồn, không phải
    lỗi công cụ)."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12690171", {}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False
    assert "không có trong pmc open access subset" in kq.ghi_chu.lower()
    assert bucket.goi_get_bytes == []


def test_tai_toan_van_list_call_network_error_returns_failure_not_raise(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12690171", {}, liet_ke=ConnectionError("mat mang khi liet ke bucket")).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False
    # Vá 25/09/2026: lỗi mạng KHÔNG được báo thành «không có trong PMC OA» (không biết ≠ không có)
    assert "không có trong pmc open access subset" not in kq.ghi_chu.lower()
    assert "chưa biết" in kq.ghi_chu.lower()


def test_tai_toan_van_object_fetch_error_returns_failure_not_raise(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC13555224", {1: _meta("PMC13555224", 1)},
               txt={1: ConnectionError("mat mang khi tai .txt")}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False
    assert kq.van_ban_trich is None


def test_tai_toan_van_empty_object_content_reported_not_silently_succeeded(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _mot_phien_ban(monkeypatch, client, txt=b"   ")
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False
    assert "rỗng" in kq.ghi_chu.lower()


def test_tai_toan_van_success_reports_org_and_copyright_note(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _mot_phien_ban(monkeypatch, client)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is True
    assert kq.to_chuc == "PMC"
    assert kq.van_ban_trich == _NOI_DUNG_TXT_MAU
    assert kq.so_trang_hoac_ky_tu == len(_NOI_DUNG_TXT_MAU)
    assert "không đăng lại toàn văn" in kq.ghi_chu_ban_quyen.lower()
    assert kq.sha256_nguon == hashlib.sha256(_TXT_MAU).hexdigest()
    # Ghi chú nói rõ ĐÃ CHỌN bản nào, loại gì, giấy phép gì — người đọc không phải đoán.
    assert "PMC13555224.1" in kq.ghi_chu and "bản công bố chính thức" in kq.ghi_chu and "CC BY" in kq.ghi_chu


def test_tai_toan_van_truncates_to_character_limit(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _mot_phien_ban(monkeypatch, client, txt=b"x" * 250_000)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is True
    assert kq.bi_cat is True
    assert kq.so_trang_hoac_ky_tu == 200_000
    assert "ĐÃ BỊ CẮT" in kq.ghi_chu


# ════════════════════════════════════════════════════════════════════════════
# Danh mục bucket: delimiter=/, IsTruncated, trả về lạ (13/10/2026)
# ════════════════════════════════════════════════════════════════════════════

def test_liet_ke_dung_delimiter_tien_to_co_dau_cham_va_khong_cache(monkeypatch):
    """Liệt kê theo CommonPrefixes (`delimiter=/`) với tiền tố «PMC<id>.» — không quét từng
    object; không dùng cache vì danh mục quyết định phiên bản nào được đọc cờ rút bài."""
    client = PmcGuidelineFullTextClient()
    bucket = _mot_phien_ban(monkeypatch, client)
    client.tai_toan_van("PMC13555224")
    assert len(bucket.goi_get_text) == 1
    _url, params, kw = bucket.goi_get_text[0]
    assert params == {"list-type": "2", "prefix": "PMC13555224.", "delimiter": "/"}
    assert kw.get("use_cache") is False


def test_danh_muc_bi_cat_la_loi_khong_phai_khong_co(monkeypatch):
    """`IsTruncated=true` ⇒ chưa chắc đã thấy mọi phiên bản (có thể bản bị rút nằm ở trang sau)
    ⇒ LỖI «chưa biết», không trích, không đọc JSON nào."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {1: _meta("PMC12345678", 1)},
                        liet_ke=_xml_liet_ke("PMC12345678", [1], bi_cat=True)).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "chưa biết" in kq.ghi_chu.lower() and "istruncated" in kq.ghi_chu.lower()
    assert "không có trong pmc open access subset" not in kq.ghi_chu.lower()
    assert bucket.goi_get_bytes == []


def test_tra_ve_khong_phai_danh_muc_s3_la_loi_khong_phai_khong_co(monkeypatch):
    """Trang HTML (proxy/cổng mạng) không có CommonPrefixes nào — KHÔNG được đọc thành «bài
    không có trong PMC OA»."""
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12345678", {}, liet_ke="<html><body>Access portal</body></html>").gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "chưa biết" in kq.ghi_chu.lower()
    assert "không có trong pmc open access subset" not in kq.ghi_chu.lower()


# ════════════════════════════════════════════════════════════════════════════
# Chọn phiên bản: bản công bố trước, rồi mới tới số (13/10/2026)
# ════════════════════════════════════════════════════════════════════════════

def test_chi_co_ban_2_khong_doan_ban_1(monkeypatch):
    """Ca thật PMC12805672 (đo 13/10/2026): bucket chỉ có `.2` (bản thảo tác giả). Phải trích
    `.2` và KHÔNG gọi bất kỳ URL nào của `.1`."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12805672", {2: _meta("PMC12805672", 2, is_manuscript=True, license_code="CC BY-NC")},
                        liet_ke=_XML_THAT_CHI_CO_BAN_2).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12805672")
    assert kq.thanh_cong is True
    assert kq.url_nguon == _S3_GOC + "PMC12805672.2/PMC12805672.2.txt"
    assert not any("PMC12805672.1" in u for u in bucket.goi_get_bytes)
    assert "bản thảo tác giả" in kq.ghi_chu


def test_ban_cong_bo_thang_ban_thao_tac_gia_so_lon_hon(monkeypatch):
    """`.1` là bản công bố, `.2` là bản thảo tác giả: số lớn hơn KHÔNG có nghĩa là mới hơn ⇒
    chọn `.1`. (Bản cũ chọn số lớn nhất ⇒ trích nhầm bản thảo.)"""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {
        1: _meta("PMC12345678", 1, is_manuscript=False),
        2: _meta("PMC12345678", 2, is_manuscript=True, license_code="TDM"),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is True
    assert kq.url_nguon == _S3_GOC + "PMC12345678.1/PMC12345678.1.txt"
    assert bucket.da_tai_txt == [kq.url_nguon]


def test_ban_cong_bo_so_lon_hon_van_duoc_chon_khi_ban_1_la_ban_thao(monkeypatch):
    """Chiều ngược lại: `.1` bản thảo, `.2` bản công bố ⇒ `.2` (không phải luật «số nhỏ nhất»)."""
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12345678", {
        1: _meta("PMC12345678", 1, is_manuscript=True, license_code="TDM"),
        2: _meta("PMC12345678", 2, is_manuscript=False),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.url_nguon == _S3_GOC + "PMC12345678.2/PMC12345678.2.txt"


def test_hai_ban_cung_loai_thi_moi_xet_so_phien_ban(monkeypatch):
    """Hai bản công bố (tạp chí dùng phiên bản) ⇒ số lớn hơn."""
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12345678", {1: _meta("PMC12345678", 1), 3: _meta("PMC12345678", 3)}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.url_nguon == _S3_GOC + "PMC12345678.3/PMC12345678.3.txt"


def test_co_is_manuscript_dang_chuoi_yes_no(monkeypatch):
    """Trang pmcaws viết `is_manuscript` «set to "yes"» — chuỗi yes/no phải được hiểu như
    boolean, không rơi về «không rõ»."""
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12345678", {
        1: _meta("PMC12345678", 1, is_manuscript="no", is_retracted="no"),
        2: _meta("PMC12345678", 2, is_manuscript="yes", is_retracted="no"),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is True
    assert kq.url_nguon == _S3_GOC + "PMC12345678.1/PMC12345678.1.txt"


# ════════════════════════════════════════════════════════════════════════════
# Rút bài: tín hiệu dương chặn; cờ không rõ ⇒ không kết luận (13/10/2026)
# ════════════════════════════════════════════════════════════════════════════

def test_mot_phien_ban_bi_rut_chan_moi_phien_ban(monkeypatch):
    """Bản thảo `.2` ghi `is_retracted` dù bản công bố `.1` không ghi ⇒ CHẶN, không trích `.1`
    (bản cũ không đọc JSON nên không bao giờ thấy cờ này)."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {
        1: _meta("PMC12345678", 1, is_manuscript=False, is_retracted=False),
        2: _meta("PMC12345678", 2, is_manuscript=True, is_retracted=True),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert kq.van_ban_trich is None
    assert "ĐÃ RÚT" in kq.ghi_chu and ".2" in kq.ghi_chu and "CẦN BÁC SĨ XEM" in kq.ghi_chu
    assert bucket.da_tai_txt == []


def test_co_rut_bai_dang_chuoi_yes_cung_chan(monkeypatch):
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {1: _meta("PMC12345678", 1, is_retracted="yes")}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False and "ĐÃ RÚT" in kq.ghi_chu
    assert bucket.da_tai_txt == []


def test_tin_hieu_rut_bai_thang_loi_cua_phien_ban_khac(monkeypatch):
    """Gộp bất đối xứng: `.1` không đọc được JSON, `.2` ghi đã rút ⇒ báo ĐÃ RÚT (tín hiệu dương
    nhận từ bất kỳ phiên bản nào), không hạ xuống «chưa biết»."""
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC12345678", {
        1: ConnectionError("mat mang khi tai json"),
        2: _meta("PMC12345678", 2, is_retracted=True),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "ĐÃ RÚT" in kq.ghi_chu


@pytest.mark.parametrize("co_rut", [None, "unknown", 1, "VẮNG"])
def test_co_rut_bai_khong_ro_thi_khong_ket_luan(monkeypatch, co_rut):
    """Cờ `is_retracted` vắng/null/lạ ⇒ KHÔNG BIẾT — không trích, không nói «chưa rút», cũng
    không nói «đã rút»."""
    client = PmcGuidelineFullTextClient()
    md = _meta("PMC12345678", 1)
    if co_rut == "VẮNG":
        del md["is_retracted"]
    else:
        md["is_retracted"] = co_rut
    bucket = _BucketGia("PMC12345678", {1: md}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "chưa biết" in kq.ghi_chu.lower() and "is_retracted không rõ" in kq.ghi_chu
    assert "ĐÃ RÚT" not in kq.ghi_chu
    assert bucket.da_tai_txt == []


def test_json_cua_mot_phien_ban_loi_thi_khong_trich_ban_con_lai(monkeypatch):
    """`.2` không tải được JSON ⇒ chưa biết `.2` có bị rút không ⇒ không trích cả `.1` dù
    `.1` sạch."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {
        1: _meta("PMC12345678", 1),
        2: ConnectionError("mat mang khi tai json .2"),
    }).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "chưa biết" in kq.ghi_chu.lower() and ".2" in kq.ghi_chu
    assert bucket.da_tai_txt == []
    # Đã đọc JSON của MỌI phiên bản trong danh mục.
    assert {u.rsplit("/", 1)[1] for u in bucket.goi_get_bytes} == {"PMC12345678.1.json", "PMC12345678.2.json"}


@pytest.mark.parametrize("ghi_de", [{"pmcid": "PMC99999999"}, {"version": 2}], ids=["lech-pmcid", "lech-version"])
def test_json_lech_khoa_thi_khong_ket_luan(monkeypatch, ghi_de):
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {1: _meta("PMC12345678", 1, **ghi_de)}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False
    assert "lệch khoá" in kq.ghi_chu
    assert bucket.da_tai_txt == []


def test_json_hong_thi_khong_ket_luan(monkeypatch):
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC12345678", {1: b"{khong phai json"}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is False and "chưa biết" in kq.ghi_chu.lower()
    assert bucket.da_tai_txt == []


# ════════════════════════════════════════════════════════════════════════════
# text_url và md5 (13/10/2026)
# ════════════════════════════════════════════════════════════════════════════

def test_md5_lech_sieu_du_lieu_thi_khong_tra_van_ban(monkeypatch):
    client = PmcGuidelineFullTextClient()
    _BucketGia("PMC13555224", {1: _meta("PMC13555224", 1, txt=b"ban khac")},
               txt={1: _TXT_MAU}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False
    assert kq.van_ban_trich is None
    assert "md5" in kq.ghi_chu.lower() and "lệch" in kq.ghi_chu.lower()


@pytest.mark.parametrize("text_url", [
    None,
    "s3://pmc-oa-opendata/PMC13555224.1/PMC13555224.1.txt",  # thiếu md5
    "s3://pmc-oa-opendata/PMC13555224.1/PMC13555224.1.txt?md5=" + "z" * 32,  # md5 không phải hex
    f"s3://pmc-oa-opendata/PMC99999999.1/PMC99999999.1.txt?md5={_md5(_TXT_MAU)}",  # sai bài
    f"s3://bucket-khac/PMC13555224.1/PMC13555224.1.txt?md5={_md5(_TXT_MAU)}",  # sai bucket
], ids=["vang", "thieu-md5", "md5-khong-hex", "sai-bai", "sai-bucket"])
def test_text_url_thieu_hoac_la_thi_khong_doan_key(monkeypatch, text_url):
    """Không tự ghép key `.txt` khi `text_url` thiếu/lạ — không có md5 thì không kiểm được tệp."""
    client = PmcGuidelineFullTextClient()
    bucket = _BucketGia("PMC13555224", {1: _meta("PMC13555224", 1, text_url=text_url)}).gan(monkeypatch, client)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False
    assert "text_url" in kq.ghi_chu
    assert bucket.da_tai_txt == []


def test_toan_van_tai_bang_get_bytes_khong_ghi_cache(monkeypatch):
    """`.txt` tải bằng `get_bytes` (không cache đĩa — toàn văn chỉ dùng tham chiếu nội bộ) và
    md5 tính trên byte thô; `get_text` chỉ được gọi cho danh mục (bucket giả assert điều đó)."""
    client = PmcGuidelineFullTextClient()
    bucket = _mot_phien_ban(monkeypatch, client)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is True
    assert bucket.da_tai_txt == [_S3_GOC + "PMC13555224.1/PMC13555224.1.txt"]
    assert [u for u, _p, _k in bucket.goi_get_text] == [_S3_GOC]
