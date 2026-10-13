"""Connector TẢI TOÀN VĂN guideline đã lưu trữ trên PubMed Central (PMC) — thêm
23/09/2026, ban đầu cho ADA "Standards of Care in Diabetes" (professional.diabetes.org/
diabetesjournals.org KHÔNG đọc được robots.txt — mọi lần fetch đều 403/lỗi DNS, nên
KHÔNG được coi là "cho phép ngầm"), nhưng viết GENERIC theo PMCID nên dùng lại được
cho BẤT KỲ hội chuyên khoa nào khác có nộp lưu guideline lên PMC (nhiều hội nhận tài
trợ liên quan NIH có nghĩa vụ nộp lưu; hội châu Âu như ESC thì chưa chắc — phải tra
riêng, không suy đoán).

VIẾT LẠI 23/09/2026 (audit/14 vấn đề 4) — bản đầu scrape trực tiếp
`pmc.ncbi.nlm.nih.gov/articles/<PMCID>/` bị chặn HTTP 403 tối giản (không phải
Cloudflare — không có header `Cf-Mitigated`, không đổi theo User-Agent, cả API OA
`ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi` lẫn OAI-PMH `ncbi.nlm.nih.gov/pmc/oai/oai.cgi`
đều cùng bị chặn — kết luận cũ: "chặn cấp biên mạng, ngoài tầm sửa code").

Điều tra tiếp (audit/14 vấn đề 4, cùng ngày) tìm ra đường THẬT sự khác: readme.txt
chính thức của NCBI (`ftp.ncbi.nlm.nih.gov/pub/pmc/readme.txt`, đọc trực tiếp 23/09/2026)
khai FTP Service cũ đang bị khai tử (thông báo 02/2026, đang gỡ dần từ 08/2026), thay
bằng **PMC Cloud Service trên AWS Open Data Registry** — một bản sao PMC Open Access
Subset (chỉ bài có giấy phép cho phép phân phối lại nguyên văn) ở bucket S3 công khai,
KHÔNG CẦN tài khoản AWS, KHÔNG cùng hạ tầng/WAF với `pmc.ncbi.nlm.nih.gov`:
  • Bucket: `pmc-oa-opendata` (arn:aws:s3:::pmc-oa-opendata), region us-east-1.
  • Xác nhận sống 23/09/2026: `https://pmc-oa-opendata.s3.amazonaws.com/` trả lời qua
    HTTPS thường (`requests`), KHÔNG bị 403/WAF — khác hẳn `pmc.ncbi.nlm.nih.gov`.
  • Mỗi bài có thư mục `<PMCID>.<phiên bản>/` chứa `<PMCID>.<phiên bản>.txt` (văn bản
    thuần, có khối metadata đầu file) + `.xml`/`.pdf`/`.json`/ảnh minh hoạ — CHỈ dùng
    `.txt`, không cần thư viện đọc PDF cho đường này.
  • KHÔNG có robots.txt cho bucket này (S3 không tự sinh robots.txt — 404 NoSuchKey,
    KHÔNG phải "cấm crawl"). Điều khoản áp dụng là chính readme.txt ở trên: cho phép
    tải/dùng dữ liệu, chỉ cấm dùng logo/thương hiệu PMC và cấm phân phối lại dữ liệu
    KHÔNG có giấy phép tương ứng — khớp đúng nguyên tắc "chỉ dùng tham chiếu nội bộ,
    không đăng lại toàn văn" đã áp cho GOLD/GINA/BTS ở `guideline_fulltext_common.py`.

GIỚI HẠN THẬT, đã đo bằng 4 PMCID (không đoán, tra qua PubMed trước) — CHỈ bài đã có
mặt trong PMC Open Access Subset (đăng ký `.txt`/`.xml` toàn văn) mới có trong bucket
này; bài chỉ nộp PDF-không-kèm-văn-bản-máy-đọc hoặc chưa từng nộp lưu PMC OA Subset sẽ
KHÔNG có (0 kết quả liệt kê theo prefix — KHÔNG PHẢI lỗi, là sự thật "nguồn không có
toàn văn ở PMC", đúng khuôn "báo trung thực" của module `guideline_fulltext_common.py`).
Không tự tìm PMCID (đó là việc của `app/sources/pubmed.py`/Europe PMC hiện có) — class
này CHỈ nhận PMCID đã biết.

CHỌN PHIÊN BẢN — VIẾT LẠI 13/10/2026 theo tài liệu chính thức PMC Cloud Service
(`pmc.ncbi.nlm.nih.gov/tools/pmcaws/` và `README.txt` của bucket, đọc 13/10/2026). Bản cũ
chọn `.txt` của số phiên bản LỚN NHẤT và coi đó là «mới nhất» — sai theo tài liệu:
  • số phiên bản phản ánh THỨ TỰ PMC xử lý, số lớn hơn KHÔNG có nghĩa là mới hơn hay nên dùng;
  • một PMCID có thể giữ cả bản thảo tác giả lẫn bản công bố chính thức;
  • có thể có `.2` mà không có `.1` (bản 1 không có giấy phép phù hợp);
  • mỗi phiên bản có `PMC<id>.<n>.json` với `is_manuscript`, `is_retracted`, `license_code`
    (mã Creative Commons hoặc «TDM»), `text_url` dạng `s3://pmc-oa-opendata/...?md5=<hex>`.
Nay: liệt kê bằng `delimiter=/` lấy CommonPrefixes (danh mục bị cắt `IsTruncated=true` ⇒ LỖI,
không phải «không có») → đọc JSON của MỌI phiên bản → BẤT KỲ phiên bản nào `is_retracted` ⇒
CHẶN (tín hiệu dương) · cờ không rõ ⇒ KHÔNG kết luận → ưu tiên bản công bố (`is_manuscript`
false) rồi mới tới số phiên bản → tải `.txt` qua `get_bytes` (không ghi cache đĩa) và kiểm md5
theo tham số `md5` của `text_url`. Cùng luật với `tools/gom_toan_van_dashboard.py`
(`phien_ban_pmc_s3`/`chon_ban_pmc_s3`/`tai_jats_pmc_s3`) của repo gốc — PR
drluanbv175/EBM-drluanbv175#174. KHÔNG lọc theo `license_code` ở đây (connector chỉ trích để
tham chiếu nội bộ, không lưu/đăng lại); giấy phép của bản đã chọn được ghi vào `ghi_chu`.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    GIOI_HAN_KY_TU_MAC_DINH,
    ConnectorChuaBat,
    KetQuaToanVanGuideline,
    sha256_hex,
    thong_diep_co_tat,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_S3_GOC = "https://pmc-oa-opendata.s3.amazonaws.com/"
_MAU_PMCID = re.compile(r"^PMC\d+$", re.IGNORECASE)
_GIOI_HAN_KY_TU = GIOI_HAN_KY_TU_MAC_DINH  # đồng bộ với trich_van_ban_tu_pdf() ở guideline_fulltext_common.py


class _LoiLietKeBucket(RuntimeError):
    """Không liệt kê được bucket (lỗi mạng/proxy, trả về không phải danh mục S3, danh mục bị
    cắt) — KHÁC «liệt kê được trọn vẹn nhưng 0 phiên bản».

    Vá 25/09/2026: trước đây cả hai trường hợp cùng trả `None`, nên lỗi mạng bị báo thành
    «bài KHÔNG có trong PMC Open Access Subset» — biến «không biết» thành «không có».
    """


class _BaiDaRut(RuntimeError):
    """Ít nhất một phiên bản ghi `is_retracted` — tín hiệu DƯƠNG, nhận dù phiên bản khác lỗi."""

    def __init__(self, phien_ban_rut: List[int]) -> None:
        super().__init__(", ".join(f".{n}" for n in phien_ban_rut))
        self.phien_ban_rut = phien_ban_rut


class _KhongKetLuan(RuntimeError):
    """Siêu dữ liệu không đủ để kết luận: JSON không đọc được/lệch khoá, cờ `is_retracted`
    không rõ, `text_url` thiếu hoặc lạ. KHÔNG BIẾT — không phải «chưa rút»."""


def _co_khong(gia_tri: Any) -> Optional[bool]:
    """Cờ trong JSON của PMC: JSON thật dùng true/false (đo PMC13555224.1, 13/10/2026), trang
    pmcaws lại viết `is_manuscript` «set to "yes"» ⇒ nhận cả chuỗi yes/no/true/false. Còn lại
    (vắng, null, số, chuỗi lạ) ⇒ None, tức KHÔNG BIẾT."""
    if isinstance(gia_tri, bool):
        return gia_tri
    chuoi = gia_tri.strip().lower() if isinstance(gia_tri, str) else ""
    if chuoi in ("yes", "true"):
        return True
    if chuoi in ("no", "false"):
        return False
    return None


def _loai_ban(md: Dict[str, Any]) -> str:
    return {True: "bản thảo tác giả", False: "bản công bố chính thức"}.get(
        _co_khong(md.get("is_manuscript")), "loại bản không rõ")


class PmcGuidelineFullTextClient:
    """Tải TOÀN VĂN một bài/chương guideline đã có trong PMC Open Access Subset, theo
    PMCID đã biết — qua bản sao S3 công khai của NCBI (KHÔNG qua trang HTML
    `pmc.ncbi.nlm.nih.gov` — trang đó chặn 403, xem docstring module).

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()` — cùng khuôn `WileyTdmClient`.
    Dùng khi đã có PMCID (từ `app/sources/pubmed.py`/Europe PMC) và cần trích toàn văn
    để lấy câu chữ khuyến cáo cụ thể, không dùng để khám phá/tìm kiếm."""

    name = "pmc_guideline_fulltext"

    def __init__(self) -> None:
        if not settings.enable_pmc_guideline_fulltext:
            raise ConnectorChuaBat(thong_diep_co_tat("pmc_guideline_fulltext", "ENABLE_PMC_GUIDELINE_FULLTEXT"))
        self.http = HttpClient()

    def _liet_ke_phien_ban(self, pmcid_chuan: str) -> List[int]:
        """Các phiên bản `<PMCID>.<n>/` có trong bucket, tra bằng DANH MỤC (ListObjectsV2,
        `delimiter=/` ⇒ mỗi phiên bản là một CommonPrefixes; tiền tố «<PMCID>.» có dấu chấm để
        không lẫn PMC<id>0…). Không đoán «.1»: tài liệu PMC nói có bài có `.2` mà không có `.1`.

        Trả [] CHỈ khi danh mục trọn vẹn khẳng định bài không có trong bucket. Lỗi mạng, trả về
        không phải danh mục S3, hoặc danh mục bị cắt (`IsTruncated=true` — chưa chắc đã thấy mọi
        phiên bản) ⇒ NÉM `_LoiLietKeBucket`. Không dùng cache: danh mục quyết định phiên bản
        nào được đọc siêu dữ liệu rút bài."""
        try:
            xml = self.http.get_text(
                _S3_GOC,
                params={"list-type": "2", "prefix": f"{pmcid_chuan}.", "delimiter": "/"},
                use_cache=False,
            )
        except Exception as exc:  # noqa: BLE001 — lỗi mạng, KHÔNG bịa kết quả
            logger.warning("[pmc_guideline_fulltext] không liệt kê được bucket cho %s: %s",
                            pmcid_chuan, exc)
            raise _LoiLietKeBucket(f"{type(exc).__name__}: {exc}") from exc
        if "<ListBucketResult" not in xml:
            raise _LoiLietKeBucket("trả về không phải danh mục S3 (thiếu <ListBucketResult>)")
        if re.search(r"<IsTruncated>\s*true\s*</IsTruncated>", xml, flags=re.IGNORECASE):
            raise _LoiLietKeBucket("danh mục S3 bị cắt (IsTruncated=true) — chưa chắc đã thấy mọi phiên bản")
        mau = re.compile(rf"<Prefix>{re.escape(pmcid_chuan)}\.(\d+)/</Prefix>")
        return sorted({int(n) for n in mau.findall(xml)})

    def _doc_sieu_du_lieu(self, pmcid_chuan: str, phien_ban: int) -> Any:
        """JSON siêu dữ liệu của MỘT phiên bản. Tải bằng `get_bytes` (không cache — cờ rút bài
        phải tươi) rồi tự giải mã UTF-8: bucket trả `binary/octet-stream`, không có charset."""
        url = f"{_S3_GOC}{pmcid_chuan}.{phien_ban}/{pmcid_chuan}.{phien_ban}.json"
        return json.loads(self.http.get_bytes(url).decode("utf-8"))

    def _chon_phien_ban(self, pmcid_chuan: str,
                        phien_ban: List[int]) -> Tuple[int, Dict[str, Any], str, str]:
        """Đọc JSON của MỌI phiên bản rồi chọn bản để trích. Trả (n, siêu dữ liệu, key `.txt`,
        md5 kỳ vọng).

        • BẤT KỲ phiên bản hợp lệ nào ghi `is_retracted` ⇒ `_BaiDaRut` — tín hiệu dương, thắng
          mọi lỗi của phiên bản khác (gộp bất đối xứng, như chuỗi rút bài 3 tầng).
        • JSON không đọc được / lệch khoá `pmcid`·`version` / cờ `is_retracted` không rõ ⇒
          `_KhongKetLuan` — không trích bản nào, vì chưa biết bản còn lại có bị rút không.
        • Ưu tiên bản công bố chính thức (`is_manuscript` false) rồi mới tới số phiên bản lớn
          hơn — tài liệu PMC: số lớn hơn KHÔNG có nghĩa là mới hơn hay nên dùng.
        • `text_url` của bản đã chọn phải đúng `s3://pmc-oa-opendata/<PMCID>.<n>/<PMCID>.<n>.txt
          ?md5=<32 hex>` — sai/thiếu ⇒ `_KhongKetLuan`, không tự đoán key."""
        hop_le: List[Tuple[int, Dict[str, Any]]] = []
        van_de: List[str] = []
        for n in phien_ban:
            try:
                md = self._doc_sieu_du_lieu(pmcid_chuan, n)
            except Exception as exc:  # noqa: BLE001 — lỗi mạng/JSON hỏng ⇒ không biết
                van_de.append(f".{n}: không đọc được JSON ({type(exc).__name__}: {exc})")
                continue
            if not isinstance(md, dict) or md.get("pmcid") != pmcid_chuan or str(md.get("version")) != str(n):
                van_de.append(f".{n}: JSON lệch khoá pmcid/version")
                continue
            hop_le.append((n, md))

        phien_ban_rut = [n for n, md in hop_le if _co_khong(md.get("is_retracted")) is True]
        if phien_ban_rut:
            raise _BaiDaRut(phien_ban_rut)
        van_de += [f".{n}: cờ is_retracted không rõ ({md.get('is_retracted')!r})"
                   for n, md in hop_le if _co_khong(md.get("is_retracted")) is None]
        if van_de:
            raise _KhongKetLuan("; ".join(van_de))

        n, md = max(hop_le, key=lambda cap: (_co_khong(cap[1].get("is_manuscript")) is False, cap[0]))
        khop = re.fullmatch(
            rf"s3://pmc-oa-opendata/({re.escape(pmcid_chuan)}\.{n}/{re.escape(pmcid_chuan)}\.{n}\.txt)"
            r"\?md5=([0-9a-fA-F]{32})",
            str(md.get("text_url") or ""),
        )
        if not khop:
            raise _KhongKetLuan(f".{n}: text_url thiếu hoặc không đúng dạng ({md.get('text_url')!r})")
        return n, md, khop.group(1), khop.group(2).lower()

    def tai_toan_van(self, pmcid: str,
                     gioi_han_ky_tu: Optional[int] = _GIOI_HAN_KY_TU) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản một bài PMC theo PMCID (định dạng "PMC1234567", có hoặc
        không tiền tố PMC đều được chuẩn hoá). Không bịa PMCID — người gọi phải tự tra
        qua PubMed/Europe PMC trước. Danh mục trọn vẹn 0 phiên bản ⇒ bài KHÔNG có trong PMC
        Open Access Subset — sự thật, không phải lỗi công cụ. Có phiên bản thì chọn theo
        `_chon_phien_ban` (rút bài chặn, cờ không rõ không kết luận, bản công bố trước) và
        chỉ trả văn bản khi md5 tệp `.txt` khớp siêu dữ liệu."""
        pmcid_chuan = pmcid.strip().upper()
        if not pmcid_chuan.startswith("PMC"):
            pmcid_chuan = f"PMC{pmcid_chuan}"
        if not _MAU_PMCID.match(pmcid_chuan):
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=pmcid, thanh_cong=False,
                ghi_chu=f"'{pmcid}' không đúng định dạng PMCID (kỳ vọng 'PMC' + số).",
            )

        try:
            phien_ban = self._liet_ke_phien_ban(pmcid_chuan)
        except _LoiLietKeBucket as exc:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=_S3_GOC + pmcid_chuan, thanh_cong=False,
                ghi_chu=(
                    f"Không liệt kê được bucket PMC OA cho {pmcid_chuan} ({exc}) — CHƯA BIẾT bài "
                    "có trong PMC Open Access Subset hay không (lỗi mạng/proxy, không phải sự "
                    "thật của nguồn). Thử lại sau hoặc đọc trực tiếp trên trang tạp chí."
                ),
            )
        if not phien_ban:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=_S3_GOC + pmcid_chuan, thanh_cong=False,
                ghi_chu=(
                    f"{pmcid_chuan} KHÔNG có trong PMC Open Access Subset (bucket S3 "
                    "công khai của NCBI) — bài này chưa từng nộp lưu toàn văn máy-đọc "
                    "cho PMC, hoặc chỉ nộp PDF không kèm bản văn bản/XML. Đây là giới "
                    "hạn THẬT của nguồn, không phải lỗi mạng — cần xác nhận thủ công "
                    "(vd đọc trực tiếp trên trang tạp chí gốc)."
                ),
            )

        try:
            n, md, key, md5_ky_vong = self._chon_phien_ban(pmcid_chuan, phien_ban)
        except _BaiDaRut as exc:
            logger.warning("[pmc_guideline_fulltext] PMC Cloud ghi %s ĐÃ RÚT (%s)", pmcid_chuan, exc)
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=_S3_GOC + pmcid_chuan, thanh_cong=False,
                ghi_chu=(
                    f"⛔ PMC Cloud ghi {pmcid_chuan} ĐÃ RÚT (is_retracted ở phiên bản {exc}) — KHÔNG "
                    "trích toàn văn của bất kỳ phiên bản nào. CẦN BÁC SĨ XEM: đối chiếu chuỗi rút bài "
                    "(Retraction Watch → NCBI → Europe PMC) trước khi dùng bài này."
                ),
            )
        except _KhongKetLuan as exc:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=_S3_GOC + pmcid_chuan, thanh_cong=False,
                ghi_chu=(
                    f"Siêu dữ liệu PMC Cloud của {pmcid_chuan} không đủ để kết luận ({exc}) — CHƯA "
                    "BIẾT bài có bị rút không (KHÔNG phải «chưa rút»), nên không trích phiên bản nào. "
                    "Thử lại sau hoặc tra rút bài qua chuỗi Retraction Watch → NCBI → Europe PMC."
                ),
            )

        url_txt = _S3_GOC + key
        try:
            du_lieu = self.http.get_bytes(url_txt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[pmc_guideline_fulltext] tải %s thất bại: %s", url_txt, exc)
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False, ghi_chu=str(exc),
            )
        md5_that = hashlib.md5(du_lieu, usedforsecurity=False).hexdigest()
        if md5_that != md5_ky_vong:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False,
                ghi_chu=(f"md5 của {key} ({md5_that}) LỆCH md5 trong text_url của siêu dữ liệu "
                         f"({md5_ky_vong}) — tệp hỏng hoặc đang được thay; không dùng, thử lại sau."),
            )
        try:
            van_ban_tho = du_lieu.decode("utf-8")
        except UnicodeDecodeError as exc:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False,
                ghi_chu=f"Tệp {key} khớp md5 nhưng không phải UTF-8 hợp lệ ({exc}) — cần xác nhận thủ công.",
            )
        if not van_ban_tho.strip():
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False,
                ghi_chu="Object .txt tồn tại trong bucket nhưng nội dung rỗng — bất "
                        "thường, cần xác nhận thủ công.",
            )
        bi_cat = gioi_han_ky_tu is not None and len(van_ban_tho) > gioi_han_ky_tu
        van_ban = van_ban_tho[:gioi_han_ky_tu] if bi_cat else van_ban_tho
        cac_phien_ban = ", ".join(f".{p}" for p in phien_ban)
        giay_phep = md.get("license_code") or "không ghi"
        ghi_chu = (f"Phiên bản đã chọn: {pmcid_chuan}.{n} ({_loai_ban(md)}, giấy phép {giay_phep}); "
                   f"phiên bản trong bucket: {cac_phien_ban}; md5 khớp siêu dữ liệu.")
        if bi_cat:
            ghi_chu += (f" Văn bản ĐÃ BỊ CẮT ở {gioi_han_ky_tu} ký tự (bản gốc {len(van_ban_tho)} ký tự) — "
                        "muốn đọc/tìm toàn bộ thì truyền gioi_han_ky_tu=None.")
        return KetQuaToanVanGuideline(
            to_chuc="PMC", url_nguon=url_txt, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
            bi_cat=bi_cat, sha256_nguon=sha256_hex(du_lieu),
            ghi_chu=ghi_chu,
        )
