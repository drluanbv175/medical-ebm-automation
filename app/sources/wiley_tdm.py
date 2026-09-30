"""Kết nối Wiley Text and Data Mining (TDM) API — thêm 23/09/2026 theo yêu cầu bác sĩ,
sau khi đã có TDM API token thật từ tài khoản Wiley Online Library (WOL) của bác sĩ.

KHÁC HOÀN TOÀN mọi connector khác trong app/sources/: đây KHÔNG phải nguồn TÌM KIẾM/
KHÁM PHÁ (không có `SourceClient.search()`) — TDM API chỉ TẢI TOÀN VĂN PDF theo DOI ĐÃ
BIẾT trước. Vì vậy `WileyTdmClient` KHÔNG kế thừa `SourceClient`, KHÔNG có trong
`get_enabled_sources()`/`get_fallback_sources()`, và KHÔNG tham gia bất kỳ vòng quét
song song nào (`ingest_all`, `research/manager.py`, `research/dossier.py`). Dùng khi một
agent/quy trình ĐÃ CÓ DOI (từ PubMed/Crossref/Scopus/Europe PMC…) và cần lấy toàn văn
của một bài xuất bản trên nền tảng Wiley Online Library — ví dụ để trích xuất dữ liệu
chi tiết ngoài phạm vi abstract cho tổng quan hệ thống.

Thư viện nền: gói PyPI chính thức `wiley-tdm` (import `wiley_tdm`), mã nguồn
`github.com/WileyLabs/tdm-client` — bọc lại ở đây theo đúng khuôn NẠP CHỊU LỖI của gói
này (xem `app/sources/__init__.py::_nap_client`): thiếu thư viện thì VẮNG MẶT CÓ KHAI
BÁO ở nơi gọi, không kéo sập cả gói `app.sources`.

Đây KHÔNG phải MCP connector `plugin:bio-research:wiley` (claude.ai connector, cần bác
sĩ tự cấp quyền OAuth qua giao diện claude.ai) — hai thứ hoàn toàn tách biệt, ghi ở
`data/sources.json` với hai mã SRC khác nhau.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm mức độ phủ:
  • ⚠️ QUAN TRỌNG NHẤT — "Access is IP address based only" (README chính thức của
    WileyLabs/tdm-client, mục Known Limitations): dù token hợp lệ, IP gọi request PHẢI
    nằm trong dải IP mà tài khoản WOL của bác sĩ được cấp quyền truy cập (thường là
    mạng của bệnh viện/tổ chức đã mua gói Wiley Online Library). Gọi từ mạng nhà/VPN/
    máy ngoài dải đó → `DownloadStatus.ACCESS_DENIED` cho các bài KHÔNG PHẢI Open
    Access, dù token đúng. CHỈ bài Open Access chắc chắn tải được từ mọi IP.
    **CHƯA được xác nhận chạy thật** với dải IP của bác sĩ lúc viết module này — phải
    tự kiểm bằng `python run.py wiley-tdm-test <DOI Open Access>` rồi một DOI KHÔNG Open
    Access để biết đúng ranh giới thật của tài khoản, KHÔNG giả định nó "chắc chắn chạy".
  • Không phải nguồn tìm kiếm — không có DOI thì không tải được gì (khác PubMed/
    Crossref/Scopus có thể tìm THEO từ khoá).
  • Trần nhịp gọi do Wiley công bố: ~3 bài/giây, 60 request/10 phút; thư viện mặc định
    nghỉ 5 giây giữa các lượt tải hàng loạt (`api_rate_limit`), README khuyến nghị
    10 giây cho việc dùng LIÊN TỤC — cấu hình qua `WILEY_TDM_RATE_LIMIT_SECONDS`.
  • KHÔNG tham gia chuỗi 3 tầng kiểm rút bài (`retraction_chain.py`) — tải được PDF
    không xác nhận bài chưa bị rút; PHẢI kiểm rút bài qua kênh hiện có (PubMed/Europe
    PMC/Retraction Watch offline) TRƯỚC khi dùng nội dung PDF tải về cho việc gì.
  • Token là chuỗi UUID lấy từ trang "Text and Data Mining" trong tài khoản Wiley Online
    Library của bác sĩ — KHÔNG BAO GIỜ nhập/dán token qua Claude Code; xem hướng dẫn ở
    `.env.example`.
  • PDF tải về là nội dung CÓ BẢN QUYỀN của nhà xuất bản, mà repo này CÔNG KHAI — đưa
    vào git là phân phối lại công khai. Thư mục mặc định `THU_MUC_TAI_MAC_DINH` được
    `.gitignore` bắt ở mọi cấp (vá 30/09/2026 — trước đó `git status` hiện
    `?? downloads_wiley_tdm/`). Luật ignore KHÔNG đi theo cấu hình, nên từ 30/09/2026
    client TỪ CHỐI (RuntimeError kèm cách sửa) khi thư mục tải tự đặt — qua
    `WILEY_TDM_DOWNLOAD_DIR` hoặc `download_dir` — nằm trong một cây git ở chỗ git nhìn
    thấy. Phép kiểm hỏi chính git (`app/utils/tam_nhin_git.py`) về thư mục THẬT mà thư viện
    ghi: thư viện coi tên có dấu chấm («wiley.pdfs») là tên tệp và lùi về thư mục MẸ.
  • `thanh_cong=True` nghĩa là có một tệp TRÔNG NHƯ PDF trọn vẹn trên đĩa, không chỉ là thư
    viện báo `SUCCESS`/`EXISTING_FILE`: đứt mạng giữa chừng để lại tệp ghi dở, và lượt sau
    thư viện thấy tệp đó là trả `EXISTING_FILE` mà không gọi mạng. Xem `_ly_do_pdf_ghi_do`
    (phép kiểm cấu trúc hai đầu tệp — không bắt được tệp hỏng ở giữa).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from app.config import settings
from app.utils.logging_config import get_logger
from app.utils.tam_nhin_git import GIT_THAY, KHONG_DO_DUOC, TamNhinGit, tam_nhin_git

logger = get_logger(__name__)

_TRANG_THAI_THANH_CONG = {"SUCCESS", "EXISTING_FILE"}
_TRANG_THAI_LOI_GHI = "STORAGE_ERROR"

# Số byte đọc ở MỖI đầu tệp khi kiểm PDF có trọn vẹn không — xem `_ly_do_pdf_ghi_do`.
_CUA_SO_KIEM_PDF = 1024
_STARTXREF_VE_BYTE_0 = re.compile(rb"startxref\s+0\s*$")

# Tên tệp đem hỏi git khi chưa có DOI nào: thư viện đặt tên PDF theo DOI («10.1002/x» ⇒
# «10.1002-x.pdf»), nên hỏi về một tên cùng khuôn nằm trong thư mục tải.
_TEN_TEP_THU = "10.1002-kiem-thu-muc-tai.pdf"

# Tên thư mục tải MẶC ĐỊNH — tương đối so với thư mục đang đứng lúc dựng client (thư viện
# tự `mkdir` ngay trong `TDMClient.__init__`). `.gitignore` có luật cùng tên, không neo gốc,
# để PDF có bản quyền không hiện trong `git status` của repo công khai này. Đổi tên ở đây
# PHẢI đổi luật ignore cùng lúc: tests/test_toan_van_khong_lot_vao_git_20260930.py đọc đúng
# hằng số này rồi hỏi `git check-ignore`.
THU_MUC_TAI_MAC_DINH = "downloads_wiley_tdm"


@dataclass
class KetQuaTaiWiley:
    """Kết quả một lượt tải PDF qua Wiley TDM — Việt hoá lại `DownloadResult`/
    `DownloadStatus` của thư viện gốc để phần còn lại của hệ thống không phải import
    `wiley_tdm` trực tiếp (thư viện đổi kiểu dữ liệu thì chỉ sửa ở `_quy_doi_ket_qua`)."""

    doi: str
    trang_thai: str  # tên gốc của DownloadStatus: SUCCESS, ACCESS_DENIED, UNKNOWN_DOI,
    # KNOWN_ISSUE, API_ERROR, EXISTING_FILE, STORAGE_ERROR, INVALID_DOI, NETWORK_ERROR
    thanh_cong: bool
    duong_dan: Optional[str] = None
    # Byte THẬT của tệp trên đĩa (`st_size`), chỉ có khi tải thành công và đo được — xem
    # `_kich_thuoc_byte_tren_dia`. KHÔNG phải `DownloadResult.size` của thư viện (KiB).
    kich_thuoc_byte: Optional[int] = None
    ghi_chu: Optional[str] = None
    ma_http: Optional[int] = None


def _kich_thuoc_byte_tren_dia(duong_dan) -> Optional[int]:
    """Kích thước THẬT, tính bằng byte, của tệp PDF trên đĩa. Không đo được thì trả `None`.

    Không dùng `DownloadResult.size` của thư viện: trường đó mang KiB làm tròn
    (`FileUtils.get_file_size_kb` = round(st_size / 1024)) và để trống với `EXISTING_FILE`.
    Đo 30/09/2026 với DOI 10.1002/jcsm.70385: tệp 8.913.789 byte, thư viện báo 8705 — trước
    bản vá, con số 8705 đó đi ra ngoài dưới tên `kich_thuoc_byte`. Nhân lại với 1024 cũng
    không ra số thật (8.913.920), nên đo thẳng trên đĩa; cách này còn đứng vững nếu thư viện
    đổi đơn vị."""
    if not duong_dan:
        return None
    try:
        tep = Path(duong_dan)
        return tep.stat().st_size if tep.is_file() else None
    except OSError:
        return None


def _ly_do_pdf_ghi_do(duong_dan) -> Optional[str]:
    """Vì sao tệp trên đĩa KHÔNG trông như một PDF trọn vẹn. `None` = trông trọn vẹn, hoặc không
    xét được (không có đường dẫn, không phải tệp, không đọc được).

    Đo 30/09/2026: đứt mạng giữa chừng thì thư viện trả `STORAGE_ERROR` và để lại tệp ghi dở; lượt
    sau nó thấy tệp đã có nên trả `EXISTING_FILE` mà không gọi mạng. Chỉ nhìn trạng thái của thư
    viện thì PDF cụt đó được báo «thành công» mãi, tới khi có người xoá tệp.

    Phép kiểm chỉ đọc hai đầu tệp, không mở PDF ra:
      * «%PDF-» trong 1024 byte đầu — không có thì đây không phải PDF, hoặc ghi dở ngay từ đầu;
      * «%%EOF» trong 1024 byte cuối — tệp bị cắt giữa chừng thì mất dấu này;
      * dấu «%%EOF» cuối cùng không được đứng ngay sau «startxref 0»: PDF tuyến tính hoá
        (linearized) có một đoạn kết như vậy GẦN ĐẦU tệp, nên tệp bị cắt ngay sau đoạn đó vẫn có
        «%%EOF» ở đuôi. Đuôi thật của một PDF không bao giờ trỏ về byte 0 (ở đó là chữ ký «%PDF-»).
    Cùng ngày, đo trên 109 PDF thật có sẵn trên máy: cả 109 có «%PDF-» ở byte 0 và «%%EOF» trong 7
    byte cuối; 4 tệp tuyến tính hoá đều có «startxref 0 %%EOF» ở byte 450–1364.

    Giới hạn: đây là phép kiểm CẤU TRÚC HAI ĐẦU. Nó bắt tệp bị cắt và tệp không phải PDF; nó
    không bắt được tệp hỏng ở giữa mà hai đầu còn nguyên."""
    if not duong_dan:
        return None
    try:
        tep = Path(duong_dan)
        if not tep.is_file():
            return None
        kich_thuoc = tep.stat().st_size
        with tep.open("rb") as dau_vao:
            dau = dau_vao.read(_CUA_SO_KIEM_PDF)
            dau_vao.seek(max(0, kich_thuoc - _CUA_SO_KIEM_PDF))
            cuoi = dau_vao.read(_CUA_SO_KIEM_PDF)
    except OSError:
        return None
    if kich_thuoc == 0:
        return "tệp rỗng, 0 byte"
    if b"%PDF-" not in dau:
        return "không có chữ ký «%PDF-» ở đầu tệp"
    vi_tri_ket = cuoi.rfind(b"%%EOF")
    if vi_tri_ket < 0:
        return "không có dấu kết thúc «%%EOF» ở cuối tệp"
    if _STARTXREF_VE_BYTE_0.search(cuoi[:vi_tri_ket]):
        return "tệp dừng ngay sau phần mở đầu của một PDF tuyến tính hoá («startxref 0»)"
    return None


def _ghi_chu_tep_do(ghi_chu_thu_vien: Optional[str], duong_dan, ly_do: str) -> str:
    canh_bao = (
        f"Tệp trên đĩa có vẻ ghi dở hoặc không phải PDF ({ly_do}): {duong_dan}. KHÔNG dùng tệp này làm "
        "toàn văn. Xoá tệp đó rồi tải lại — chừng nào tệp còn nằm đó, thư viện không gọi mạng lần nữa."
    )
    return f"{ghi_chu_thu_vien} | {canh_bao}" if ghi_chu_thu_vien else canh_bao


def _quy_doi_ket_qua(ket_qua) -> KetQuaTaiWiley:
    ten_trang_thai = ket_qua.status.name
    thanh_cong = ten_trang_thai in _TRANG_THAI_THANH_CONG
    ghi_chu = ket_qua.comment or None
    # `SUCCESS`/`EXISTING_FILE` chỉ nói thư viện đã ghi, hoặc đã thấy, MỘT tệp — không nói tệp đó
    # trọn vẹn. `STORAGE_ERROR` cũng xét, để chỉ ra tệp dở mà lượt sau sẽ vấp phải.
    if thanh_cong or ten_trang_thai == _TRANG_THAI_LOI_GHI:
        ly_do_ghi_do = _ly_do_pdf_ghi_do(ket_qua.path)
        if ly_do_ghi_do:
            thanh_cong = False
            ghi_chu = _ghi_chu_tep_do(ghi_chu, ket_qua.path, ly_do_ghi_do)
    # Chỉ đo khi tải THÀNH CÔNG: `STORAGE_ERROR` có thể để lại tệp ghi dở trên đĩa, mà kích
    # thước của tệp dở không phải «kích thước PDF đã tải».
    kich_thuoc = _kich_thuoc_byte_tren_dia(ket_qua.path) if thanh_cong else None
    if thanh_cong and kich_thuoc is None:
        logger.warning(
            "[wiley_tdm] trạng_thái=%s nhưng không đo được kích thước tệp doi=%s đường_dẫn=%s",
            ten_trang_thai, ket_qua.doi, ket_qua.path,
        )
    return KetQuaTaiWiley(
        doi=ket_qua.doi,
        trang_thai=ten_trang_thai,
        thanh_cong=thanh_cong,
        duong_dan=str(ket_qua.path) if ket_qua.path else None,
        kich_thuoc_byte=kich_thuoc,
        ghi_chu=ghi_chu,
        ma_http=int(ket_qua.api_status) if ket_qua.api_status else None,
    )


def _thong_diep_tu_choi_thu_muc(
        ket_luan: TamNhinGit, thu_muc_that: Path, cau_hinh: Path, bi_thu_vien_doi: bool) -> str:
    """Thông điệp từ chối thư mục tải: nói rõ thư mục nào, vì sao, và sửa thế nào."""
    dong = [f"[wiley_tdm] TỪ CHỐI thư mục tải «{thu_muc_that}»: nó nằm trong cây git «{ket_luan.goc_cay}»"]
    if ket_luan.trang_thai == GIT_THAY:
        dong.append(
            "mà không luật ignore nào của kho bắt. PDF tải về là nội dung có bản quyền của nhà xuất bản: "
            "`git status` sẽ hiện tệp và một lần `git add -A` là đưa nó vào lịch sử — với repo công khai như "
            "dự án này, đó là phân phối lại.")
    else:
        dong.append(
            f"nhưng không đo được git có nhìn thấy nó hay không ({ket_luan.ly_do}). Không đo được không có "
            "nghĩa là an toàn: PDF tải về là nội dung có bản quyền, và cây làm việc có thể đồng bộ sang máy "
            "có git.")
    if bi_thu_vien_doi:
        dong.append(
            f"Cấu hình là «{cau_hinh}», nhưng thư viện wiley-tdm coi thành phần cuối có dấu chấm là tên tệp "
            "và lùi về thư mục mẹ, nên nơi ghi thật là thư mục nêu trên.")
    cach_sua = []
    if cau_hinh != Path(THU_MUC_TAI_MAC_DINH):
        cach_sua.append(
            "bỏ trống WILEY_TDM_DOWNLOAD_DIR (và không truyền download_dir) để dùng mặc định "
            f"«{THU_MUC_TAI_MAC_DINH}/», đã có luật ignore trong repo này")
    cach_sua.append(
        "trỏ WILEY_TDM_DOWNLOAD_DIR ra NGOÀI mọi cây git, vd «~/wiley_tdm_pdf» (tên thư mục đừng có dấu chấm)")
    cach_sua.append(
        "thêm luật ignore cho thư mục đó vào `.gitignore` của kho" if ket_luan.trang_thai == GIT_THAY
        else "cài hoặc sửa git trên máy này")
    dong.append("Cách sửa, chọn một: " + "; ".join(f"({i}) {c}" for i, c in enumerate(cach_sua, 1)) + ".")
    return " ".join(dong)


class WileyTdmClient:
    """Bọc `wiley_tdm.TDMClient` — tải TOÀN VĂN PDF theo DOI qua Wiley TDM API.

    KHÔNG kế thừa `SourceClient` (xem docstring module). Dùng trực tiếp::

        client = WileyTdmClient()
        kq = client.download_pdf("10.1002/xxxx")
        if kq.thanh_cong:
            ...  # kq.duong_dan là đường dẫn PDF trên đĩa
    """

    name = "wiley_tdm"

    def __init__(self, download_dir: Optional[str] = None) -> None:
        if not settings.enable_wiley_tdm:
            raise RuntimeError(
                "[wiley_tdm] ENABLE_WILEY_TDM chưa bật — đặt true trong "
                "~/.ebm-secrets/medical-ebm-automation.env sau khi đã có "
                "WILEY_TDM_API_TOKEN."
            )
        if not settings.wiley_tdm_api_token:
            # Chặn SỚM bằng tiếng Việt rõ ràng, thay vì để thư viện gốc ném ValueError
            # tiếng Anh mù mờ — cùng nguyên tắc đã áp cho Scopus/Epistemonikos/SerpApi.
            raise RuntimeError(
                "[wiley_tdm] ENABLE_WILEY_TDM=true nhưng thiếu WILEY_TDM_API_TOKEN — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại. Token "
                "lấy từ trang 'Text and Data Mining' trong tài khoản Wiley Online "
                "Library của bác sĩ."
            )
        try:
            from wiley_tdm import TDMClient  # nạp trễ, xem docstring module
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "[wiley_tdm] thiếu thư viện `wiley-tdm` — cài: "
                "~/.ebm-venv/bin/pip install wiley-tdm (macOS/Linux) hoặc "
                "%USERPROFILE%\\.ebm-venv\\Scripts\\pip.exe install wiley-tdm (Windows)."
            ) from exc

        thu_muc = download_dir or settings.wiley_tdm_download_dir or THU_MUC_TAI_MAC_DINH
        # Thư viện không giải «~»: để nguyên thì nó tạo một thư mục TÊN «~» ngay trong thư mục đang đứng.
        self._thu_muc_cau_hinh = Path(str(thu_muc)).expanduser()
        self._client = TDMClient(api_token=settings.wiley_tdm_api_token, download_dir=self._thu_muc_cau_hinh)
        self._client.api_rate_limit = settings.wiley_tdm_rate_limit_seconds
        # skip_existing_files=True là mặc định của thư viện — giữ nguyên để không tải
        # lại PDF đã có trên đĩa.
        self._thu_muc_da_kiem: Optional[Path] = None
        self._kiem_thu_muc_tai()

    def _kiem_thu_muc_tai(self) -> None:
        """Từ chối khi nơi thư viện SẼ GHI nằm ở chỗ git nhìn thấy (repo này công khai, PDF có bản quyền).

        Xét `self._client.download_dir` — thư mục THẬT của thư viện, không phải chuỗi cấu hình: thư
        viện coi tên có đuôi («wiley.pdfs») là tên TỆP và lùi về thư mục mẹ (đo 30/09/2026). Thư mục
        tương đối được tính theo thư mục đang đứng LÚC GHI, nên phép kiểm chạy lại trước mỗi lượt
        tải; thư mục đã kiểm được nhớ theo đường tuyệt đối để không hỏi git lặp lại."""
        thu_muc_that = Path(self._client.download_dir).resolve()
        if thu_muc_that == self._thu_muc_da_kiem:
            return
        ket_luan = tam_nhin_git(thu_muc_that / _TEN_TEP_THU)
        bi_thu_vien_doi = thu_muc_that != self._thu_muc_cau_hinh.resolve()
        if ket_luan.trang_thai in (GIT_THAY, KHONG_DO_DUOC):
            raise RuntimeError(
                _thong_diep_tu_choi_thu_muc(ket_luan, thu_muc_that, self._thu_muc_cau_hinh, bi_thu_vien_doi))
        if bi_thu_vien_doi:
            logger.warning(
                "[wiley_tdm] cấu hình thư mục tải là «%s» nhưng thư viện coi tên có dấu chấm là tên tệp và "
                "lùi về thư mục mẹ: PDF sẽ nằm ở «%s»", self._thu_muc_cau_hinh, thu_muc_that,
            )
        self._thu_muc_da_kiem = thu_muc_that

    def download_pdf(self, doi: str) -> KetQuaTaiWiley:
        """Tải MỘT bài theo DOI. Không bịa kết quả khi lỗi — trả nguyên trạng thái thật
        của Wiley (ACCESS_DENIED/UNKNOWN_DOI/NETWORK_ERROR/...), không quy hết về 'lỗi'
        chung chung để người gọi biết chính xác phải làm gì tiếp theo.

        `thanh_cong` chỉ đúng khi tệp trên đĩa trông như một PDF trọn vẹn (`_ly_do_pdf_ghi_do`)."""
        self._kiem_thu_muc_tai()
        ket_qua = self._client.download_pdf(doi)
        out = _quy_doi_ket_qua(ket_qua)
        if not out.thanh_cong:
            logger.warning(
                "[wiley_tdm] tải thất bại doi=%s trạng_thái=%s ghi_chú=%s",
                doi, out.trang_thai, out.ghi_chu,
            )
        return out

    def download_pdfs(
        self,
        dois: List[str],
        on_result: Optional[Callable[[KetQuaTaiWiley], None]] = None,
    ) -> List[KetQuaTaiWiley]:
        """Tải HÀNG LOẠT theo danh sách DOI — thư viện tự giãn nhịp giữa các lượt
        (xem `api_rate_limit`). `on_result` (tuỳ chọn) được gọi sau MỖI lượt tải."""

        def _cb(ket_qua):
            if on_result:
                on_result(_quy_doi_ket_qua(ket_qua))

        self._kiem_thu_muc_tai()
        ket_qua_tho = self._client.download_pdfs(dois, on_result=_cb if on_result else None)
        return [_quy_doi_ket_qua(k) for k in ket_qua_tho]

    @property
    def download_dir(self) -> Path:
        return self._client.download_dir
