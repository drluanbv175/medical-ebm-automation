"""Hai lỗ hổng hệ nghiên cứu (18/11/2026, bác sĩ: «Trước tiên làm 2 và 3»).

(2) Đặc tả SAP G6: cụm neo `sap_neo` chỉ nằm trong câu PHỦ ĐỊNH của SAP («Không áp hiệu chỉnh quần thể hữu hạn») vẫn
    được coi là neo hợp lệ ⇒ mục SAP đã loại vẫn chạy. Nay `kiem` CẢNH BÁO khi MỌI lần xuất hiện của cụm neo đều bị phủ
    định trong cùng mệnh đề; có một lần khẳng định thì không cảnh báo.
(3) Kiểm nội dung trích dẫn A12: tài liệu CHỈ có DOI (bài tạp chí trong nước, sách, bài phương pháp) luôn «không kiểm
    được». Nay tra abstract Europe PMC → Crossref theo đúng DOI; nguồn ghi rõ trong lời nhắn và báo cáo.
Dữ liệu giả, không mạng (HTTP và PubMed được tiêm).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
pytest.importorskip("pandas")
import chay_sap_g6 as CS  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402

# ───────────────────────────── (2) cụm neo trong câu phủ định ─────────────────────────────


@pytest.mark.parametrize(
    "sap, neo, phu_dinh",
    [
        ("Ước lượng tỷ lệ. Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính.", "quần thể hữu hạn", True),
        # cùng cụm có một lần KHẲNG ĐỊNH (ca thật BTM: «… thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn») ⇒ không
        ("Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính; nếu biết khung mẫu thì báo thêm KTC có hiệu chỉnh "
         "quần thể hữu hạn như thông tin phụ.", "quần thể hữu hạn", False),
        ("Báo KTC có hiệu chỉnh quần thể hữu hạn.", "quần thể hữu hạn", False),
        ("Nếu không có dữ liệu thiếu, dùng hồi quy logistic.", "hồi quy logistic", False),  # phủ định ở mệnh đề khác
        ("Không có biến số nào được loại khỏi mô hình sau bước chọn biến hai chiều theo AIC và hồi quy logistic.",
         "hồi quy logistic", False),  # «không» quá xa (ngoài cửa sổ) — không phủ định cụm neo
        ("Dùng hồi quy Poisson thay vì hồi quy logistic.", "hồi quy logistic", True),
        ("Đã bỏ phân tích nhóm nhỏ theo giới.", "phân tích nhóm nhỏ", True),
        ("CHƯA làm mô hình đa mức.", "mô hình đa mức", True),  # không phân biệt hoa thường
    ],
)
def test_nhan_dien_cum_neo_chi_trong_cau_phu_dinh(sap, neo, phu_dinh):
    ra = CS.neo_chi_trong_cau_phu_dinh(sap, neo)
    assert (ra is not None) is phu_dinh
    if phu_dinh:
        assert neo.casefold() in ra.casefold()  # trả đúng câu chứa cụm neo để in kèm cảnh báo


def test_muc_co_mot_neo_khang_dinh_thi_khong_canh_bao():
    sap = "§4\nKhông áp hiệu chỉnh quần thể hữu hạn. Báo KTC Wilson cho tỷ lệ chính.\n"
    dt = {"phan_tich": [
        {"id": "a", "sap_neo": ["quần thể hữu hạn"]},
        {"id": "b", "sap_neo": ["quần thể hữu hạn", "KTC Wilson"]},  # neo phụ khẳng định ⇒ mục vẫn có căn cứ
    ]}
    assert [p[0] for p in CS.kiem_phu_sap(dt, sap)["neo_phu_dinh"]] == ["a"]


def _de_tai_g6(tmp_path: Path, sap: str, neo_phu: str) -> tuple[Path, dict]:
    d = tmp_path / "exports" / "S"
    d.mkdir(parents=True)
    p = d / "G4_A5_SAP_FINAL_S.md"
    p.write_text(sap, encoding="utf-8", newline="\n")
    dt = {"nguon_sap": p.name, "sha256_sap": hashlib.sha256(p.read_bytes()).hexdigest(), "phan_tich": [
        {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "tỷ lệ", "sap_neo": ["KTC Wilson"],
         "tham_so": {"ty_le": ["y"], "nguong_ty_le": 1}},
        {"id": "MT1_fpc", "vai": "mo_ta", "sap_muc": "§4", "mo_ta": "KTC có hiệu chỉnh quần thể hữu hạn",
         "sap_neo": [neo_phu], "chua_tu_dong": "tính tay"},
    ]}
    return d, dt


def test_kiem_dac_ta_canh_bao_va_truc_nhat_quan_mo_khi_neo_chi_phu_dinh(tmp_path):
    d, dt = _de_tai_g6(tmp_path, "## §4 Phân tích\nBáo KTC Wilson. Không áp hiệu chỉnh quần thể hữu hạn.\n",
                       "quần thể hữu hạn")
    k = CS.kiem_dac_ta(d, dt)
    assert k["loi"] == []  # chỉ cảnh báo, không chặn
    cb = [x for x in k["canh_bao"] if "PHỦ ĐỊNH" in x]
    assert len(cb) == 1 and cb[0].startswith("MT1_fpc:") and "Không áp hiệu chỉnh quần thể hữu hạn" in cb[0]


def test_kiem_dac_ta_khong_canh_bao_khi_sap_con_cau_khang_dinh(tmp_path):
    d, dt = _de_tai_g6(tmp_path, "## §4 Phân tích\nBáo KTC Wilson. Không áp hiệu chỉnh quần thể hữu hạn ở phân "
                                 "tích chính; nếu biết khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn.\n",
                       "quần thể hữu hạn")
    assert not [x for x in CS.kiem_dac_ta(d, dt)["canh_bao"] if "PHỦ ĐỊNH" in x]


# ───────────── (2b) phân tích PHỤ viết liền trong câu phải vào đặc tả (giới hạn còn lại, 18/11/2026) ─────────────
SAP_PHU = (
    "## §4 Kết cục chính\n"
    "- **Phương pháp:** ước lượng tỷ lệ kèm KTC Wilson. Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính; "
    "nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.\n"
    "## §5 Mục tiêu phụ\n"
    "- **Giả định:** xem đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với biến chia nhóm.\n"  # chỉ «báo thêm»
    "- Không báo thêm mô hình nào khác.\n"  # dấu hiệu bị phủ định ⇒ không phải phân tích phụ
    "| 1.5 | thêm thông tin phụ ở §4 |\n"  # dòng bảng (lịch sử phiên bản) ⇒ bỏ qua
    "## §9 Độ nhạy\n"
    "- Báo thêm phân tích độ nhạy bỏ ca thiếu.\n"  # §9 do luật cũ phủ cả gạch đầu dòng
)


def test_nhan_dien_menh_de_phan_tich_phu_viet_trong_cau():
    assert CS.menh_de_phan_tich_phu(SAP_PHU) == [
        ("§4", "nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ."),
        ("§5", "nếu lệch rõ thì báo thêm mô hình với biến chia nhóm.")]


def _dt_phu(*muc_phu: dict) -> dict:
    return {"phan_tich": [{"id": "chinh", "sap_neo": ["KTC Wilson"]}, {"id": "dn", "sap_neo": ["bỏ ca thiếu"]},
                          {"id": "chia_nhom", "sap_neo": ["biến chia nhóm"]}, *muc_phu]}


def test_bo_muc_phan_tich_phu_thi_bao_chua_phu_du_cung_dong_co_neo_chinh():
    """Ca thật MT1_fpc: neo «KTC Wilson» của phân tích chính nằm CÙNG gạch đầu dòng — phủ theo dòng sẽ lọt."""
    phu = CS.kiem_phu_sap(_dt_phu(), SAP_PHU)
    assert phu["muc_chua_phu"] == [] and [m for m, _ in phu["phu_chua_phu"]] == ["§4"]


def test_co_muc_neo_trong_dung_menh_de_thi_du():
    phu = CS.kiem_phu_sap(_dt_phu({"id": "fpc", "sap_neo": ["báo thêm KTC có hiệu chỉnh"]}), SAP_PHU)
    assert phu["phu_chua_phu"] == []


def test_kiem_dac_ta_bao_loi_khi_phan_tich_phu_chua_vao_dac_ta(tmp_path):
    d = tmp_path / "exports" / "S"
    d.mkdir(parents=True)
    p = d / "G4_A5_SAP_FINAL_S.md"
    p.write_text(SAP_PHU, encoding="utf-8", newline="\n")
    dt = {"nguon_sap": p.name, "sha256_sap": hashlib.sha256(p.read_bytes()).hexdigest(), "phan_tich": [
        {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "tỷ lệ", "sap_neo": ["KTC Wilson"],
         "tham_so": {"ty_le": ["y"], "nguong_ty_le": 1}},
        {"id": "dn", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "bỏ ca thiếu", "sap_neo": ["bỏ ca thiếu"],
         "chua_tu_dong": "tính tay"},
        {"id": "chia_nhom", "vai": "do_nhay", "sap_muc": "§5", "mo_ta": "biến chia nhóm", "sap_neo": ["biến chia nhóm"],
         "chua_tu_dong": "khi lệch tuyến tính"}]}
    loi = [x for x in CS.kiem_dac_ta(d, dt)["loi"] if "PHỤ viết trong câu" in x]
    assert len(loi) == 1 and "§4" in loi[0] and "thông tin phụ" in loi[0]
    dt["phan_tich"].append({"id": "fpc", "vai": "mo_ta", "sap_muc": "§4", "mo_ta": "KTC hiệu chỉnh",
                            "sap_neo": ["báo thêm KTC có hiệu chỉnh"], "chua_tu_dong": "tính tay"})
    assert not [x for x in CS.kiem_dac_ta(d, dt)["loi"] if "PHỤ viết trong câu" in x]


# ───────────────────────────── (3) tài liệu chỉ có DOI ─────────────────────────────
class HttpGia:
    """`get_json` giả: trả theo tiền tố URL; giá trị là Exception thì ném ra."""

    def __init__(self, epmc=None, crossref=None):
        self.epmc, self.crossref, self.goi = epmc, crossref, []

    def get_json(self, url, params=None):
        self.goi.append((url, params))
        tra = self.epmc if "europepmc" in url else self.crossref
        if isinstance(tra, Exception):
            raise tra
        return tra or {}


DOI = "10.1234/vn.2024.5"
EPMC_CO = {"resultList": {"result": [{"doi": DOI.upper(), "pmid": None, "title": "Sự hài lòng <i>người bệnh</i>",
                                      "abstractText": "Tỷ lệ hài lòng chung là 87,5%.",
                                      "pubTypeList": {"pubType": "research-article"}}]}}
CR_CO = {"message": {"DOI": DOI, "title": ["Sự hài lòng người bệnh"], "type": "journal-article",
                     "abstract": "<jats:p>Tỷ lệ hài lòng chung là 87,5%.</jats:p>"}}


def test_doi_tra_europe_pmc_truoc():
    http = HttpGia(epmc=EPMC_CO, crossref=CR_CO)
    b = KND.lay_abstract_theo_doi([DOI], http=http)[DOI.lower()]
    assert b["status"] == "resolved" and b["nguon"] == "Europe PMC"
    assert b["title"] == "Sự hài lòng người bệnh" and b["publication_types"] == ["research-article"]
    assert len(http.goi) == 1  # có abstract ở Europe PMC ⇒ không hỏi Crossref


def test_doi_europe_pmc_khac_doi_thi_bo_qua_va_dung_crossref_bo_the_jats():
    lech = {"resultList": {"result": [{"doi": "10.9999/khac", "abstractText": "bài khác"}]}}
    b = KND.lay_abstract_theo_doi([DOI], http=HttpGia(epmc=lech, crossref=CR_CO))[DOI.lower()]
    assert b["status"] == "resolved" and b["nguon"] == "Crossref"
    assert b["abstract"] == "Tỷ lệ hài lòng chung là 87,5%."  # thẻ <jats:p> đã bỏ


def test_doi_crossref_khac_doi_khong_dung():
    cr_lech = {"message": {**CR_CO["message"], "DOI": "10.9999/khac"}}
    b = KND.lay_abstract_theo_doi([DOI], http=HttpGia(epmc={}, crossref=cr_lech))[DOI.lower()]
    assert b["status"] == "not_found"


def test_doi_co_ban_ghi_khong_abstract_thi_no_abstract():
    epmc_rong = {"resultList": {"result": [{"doi": DOI, "title": "Sách"}]}}
    cr_rong = {"message": {"DOI": DOI, "title": ["Sách"], "type": "book"}}
    b = KND.lay_abstract_theo_doi([DOI], http=HttpGia(epmc=epmc_rong, crossref=cr_rong))[DOI.lower()]
    assert b["status"] == "no_abstract" and "không có abstract" in b["reason"]


def test_doi_loi_mang_ca_hai_nguon_la_error_khong_phai_khong_thay():
    b = KND.lay_abstract_theo_doi([DOI], http=HttpGia(epmc=OSError("dns"), crossref=OSError("dns")))[DOI.lower()]
    assert b["status"] == "error" and "Europe PMC lỗi" in b["reason"] and "Crossref lỗi" in b["reason"]


def test_doi_europe_pmc_loi_van_hoi_crossref():
    b = KND.lay_abstract_theo_doi([DOI], http=HttpGia(epmc=OSError("dns"), crossref=CR_CO))[DOI.lower()]
    assert b["status"] == "resolved" and b["nguon"] == "Crossref"


DE_CUONG_DOI = """# ĐỀ CƯƠNG
# 1. ĐẶT VẤN ĐỀ
Tỷ lệ hài lòng chung là 87,5% [1]. Tỷ lệ chờ lâu cao [2]. Chất lượng dịch vụ quan trọng [3].
# 7. TÀI LIỆU THAM KHẢO
1. Nguyen A. Su hai long. Tap chi Y hoc Viet Nam. 2024. doi:10.1234/vn.2024.5.
2. Tran B. Thoi gian cho. Tap chi. 2023. doi:10.1234/vn.2023.9.
3. Le C. Chat luong. Ky yeu. 2022.
"""


def _goc_doi(tmp_path: Path) -> Path:
    d = tmp_path / "exports" / "S1"
    d.mkdir(parents=True)
    (d / "DE_CUONG_NOP_HOI_DONG_S1.md").write_text(DE_CUONG_DOI, encoding="utf-8", newline="\n")
    return tmp_path


def _lay_doi(dois):
    return {DOI.lower(): {"status": "resolved", "nguon": "Crossref", "title": "Sự hài lòng người bệnh",
                          "abstract": "Tỷ lệ hài lòng chung là 87,5%.", "publication_types": ["journal-article"]},
            "10.1234/vn.2023.9": {"status": "no_abstract", "reason": "có bản ghi nhưng không có abstract"}}


def test_lay_abstract_dua_tai_lieu_chi_doi_vao_va_ghi_ly_do():
    tltk = KND.tach_tltk(DE_CUONG_DOI)
    dung, ly = KND.lay_abstract(tltk, lay=lambda p: {}, lay_doi=_lay_doi)
    assert list(dung) == [1] and dung[1]["doi"] == DOI and dung[1]["nguon"] == "Crossref"
    assert "DOI 10.1234/vn.2023.9: no_abstract" in ly[2]
    assert 3 not in ly  # không PMID lẫn DOI: không tra gì
    loi_nhan = KND.dung_loi_nhan(KND.tach_cau_khang_dinh(DE_CUONG_DOI)[:1], dung)
    assert "[1] DOI 10.1234/vn.2024.5 (abstract Crossref)" in loi_nhan


def test_ly_do_khong_kiem_duoc_tach_doi_va_khong_dinh_danh():
    tltk = KND.tach_tltk(DE_CUONG_DOI)
    cau = KND.tach_cau_khang_dinh(DE_CUONG_DOI)
    ly = {k.so: k.ly_do for k in KND.ket_qua_may(cau, tltk, {})}
    assert "theo DOI" in ly[2] and "không có PMID lẫn DOI" in ly[3]


def test_chay_kho_liet_ke_tai_lieu_chi_doi(tmp_path, capsys):
    goc = _goc_doi(tmp_path)

    def cam(*_a):
        raise AssertionError("chạy khô không được gọi mạng")

    assert KND.main(["--study", "S1"], client=object(), lay=cam, lay_doi=cam, goc=goc) == 0
    out = capsys.readouterr().out
    assert "chỉ có DOI — tra abstract Europe PMC/Crossref: [1, 2]" in out and "không PMID lẫn DOI: [3]" in out


def test_goi_api_kiem_duoc_tai_lieu_chi_doi_va_bao_cao_ghi_nguon(tmp_path):
    from tests.test_api_claude_nghien_cuu_20261117 import KhachGia  # khách Claude giả dùng chung của bộ A12

    goc = _goc_doi(tmp_path)

    def tra(kw):
        nd = kw["messages"][0]["content"]
        assert "[1] DOI 10.1234/vn.2024.5 (abstract Crossref)" in nd
        cau = json.loads(nd.split("CÂU KHẲNG ĐỊNH CẦN KIỂM:\n", 1)[1])
        return json.dumps({"ket_qua": [{"id": c["id"], "tham_chieu": [
            {"so": n, "muc": "khong_ho_tro", "trich": "Tỷ lệ hài lòng chung là 87,5%", "ly_do": "thử"}
            for n in c["giao_tham_chieu"]]} for c in cau]})

    ma = KND.main(["--study", "S1", "--goi-api"], client=KhachGia(tra), lay=lambda p: {}, lay_doi=_lay_doi, goc=goc)
    ra = goc / "exports" / "S1" / "kiem_may_api"
    js = json.loads((ra / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    muc = {k["so"]: k["muc"] for k in js["ket_qua"]}
    assert muc == {1: "khong_ho_tro", 2: "khong_kiem_duoc", 3: "khong_kiem_duoc"}
    md = (ra / "A12_KIEM_NOI_DUNG_S1.md").read_text(encoding="utf-8")
    assert "[1] DOI 10.1234/vn.2024.5 (abstract Crossref)" in md and ma == 1
