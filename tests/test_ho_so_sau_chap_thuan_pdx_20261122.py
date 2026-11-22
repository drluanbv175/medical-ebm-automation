"""Kiểm phiếu đề xuất nhiệm vụ (Mẫu DTCS-XDNV.01-PDX) và hồ sơ gửi Hội đồng Đạo đức sau chấp thuận (22/11/2026).

Luật được canh:
  * Phiếu đề xuất dùng CÙNG nguồn với thuyết minh: tên, mục tiêu nguyên văn, thời gian, kinh phí tự túc, phương án sử
    dụng kết quả; lý do đề xuất là đoạn Đặt vấn đề của đề cương, bỏ số trích dẫn; ô ký/ngày ký thuộc gói ký.
  * Phiếu đề xuất có mặt trong đối chiếu nhất quán; lệch tên/mục tiêu bị bắt.
  * Ba văn bản sau chấp thuận dựng theo nội dung Thông tư 43/2024/TT-BYT (Điều 18 khoản 2–3, Phụ lục I mục 6): mọi ô
    còn thiếu là dữ kiện cần nhập/gói ký có cấu trúc — (a) = 0; Word không còn dấu nội bộ; đọc khoá dữ liệu từ nguồn.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")

from tests import test_ho_so_nguon_chung_20261122 as _TNC  # noqa: E402
from tests.test_ho_so_nguon_chung_20261122 import MT, STUDY, TEN, _chay_dtcs, _chay_hdd  # noqa: E402
from tools import ho_so_dtcs_bvqy175 as DTCS  # noqa: E402
from tools import ho_so_hdd_bvqy175 as HDD  # noqa: E402
from tools import ho_so_nguon_chung as HSC  # noqa: E402
from tools import ho_so_sau_chap_thuan as SCT  # noqa: E402

SCT_CHAY = importlib.import_module("ho_so_sau_chap_thuan")  # mô-đun mà lệnh con `sau-chap-thuan` thực sự nạp (tên trần)

de_tai = _TNC.de_tai  # fixture dùng chung: đề tài giả đủ nguồn + bộ mẫu giả + sổ lý lịch giả
DE_CUONG_DAT_VAN_DE = "# ĐẶT VẤN ĐỀ\n\nTỷ lệ A còn cao [1, 2]. Cần đo tại cơ sở [3].\n\n"


@pytest.fixture()
def de_tai_pdx(de_tai, monkeypatch: pytest.MonkeyPatch):
    def tao(**kw) -> Path:
        goc = de_tai(**kw)
        p = goc / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
        md = p.read_text(encoding="utf-8").replace("## MỤC TIÊU NGHIÊN CỨU",
                                                   DE_CUONG_DAT_VAN_DE + "## MỤC TIÊU NGHIÊN CỨU", 1)
        md = md.replace("# PHỤ LỤC G.", "## Kế hoạch phổ biến và ứng dụng kết quả\n\n- Báo cáo kết quả cho Ban Giám"
                                       " đốc giả.\n\n# PHỤ LỤC G.", 1)
        p.write_text(md, encoding="utf-8", newline="\n")
        return goc
    return tao


def test_trich_phieu_de_xuat_cung_nguon(de_tai_pdx) -> None:
    goc = de_tai_pdx()
    d, _ = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    pd = d["phieu_de_xuat"]
    assert pd["ten_nhiem_vu"] == TEN and pd["don_vi"] == "Khoa Giả"
    assert pd["ly_do"] == ["Tỷ lệ A còn cao. Cần đo tại cơ sở."], "bỏ số trích dẫn, giữ câu chữ"
    assert any(MT[0] in x for x in pd["muc_tieu"]) and any(MT[1] in x for x in pd["muc_tieu"])
    assert pd["thoi_gian"] == "11 tháng (từ tháng 11/2026 đến tháng 09/2027)"
    assert pd["kinh_phi"] == d["thuyet_minh"]["m4_tong_kinh_phi"] == "Tự túc, không đề nghị cấp kinh phí."
    assert pd["phuong_an_su_dung"] == ["Báo cáo kết quả cho Ban Giám đốc giả."]
    assert pd["ngay"].startswith(HSC.TIEN_TO_GOI_KY) and all(x.startswith(HSC.TIEN_TO_GOI_KY) for x in pd["ky"])


KHOI_PDX = {"thuyet_minh": {"m22_san_pham": "Dạng I: 01 bài báo giả."},
            "phieu_de_xuat": {"don_vi_ung_dung": "Khoa Giả, Bệnh viện Quân y 175"}}


def test_dung_phieu_de_xuat_dien_dung_o_mau(de_tai_pdx) -> None:
    goc = de_tai_pdx(meta_sua=lambda m: m["gate_params"]["G1"].__setitem__("ho_so_dtcs", KHOI_PDX))
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "dung", "--ghi") == 0
    p = goc / STUDY / "ho_so_dtcs" / DTCS.ten_ra("de_xuat", STUDY)
    van = "\n".join(HDD._van_ban_docx(p))
    assert f"Tên nhiệm vụ KHCN: {TEN}" in van and "KhoaGiả(K-P-B-TT-V)" in van.replace(" ", "")
    assert "Dạng I: 01 bài báo giả." in van and "đơn vị ứng dụng các kết quả: Khoa Giả, Bệnh viện Quân y 175" in van
    assert "Tỷ lệ A còn cao." in van and "[1" not in van
    assert "Thời gian cần thực hiện: 11 tháng" in van and "Nhu cầu kinh phí cần thực hiện: Tự túc" in van
    assert not HSC.DAU_DANH_DAU.search(van) and "[CẦN" not in van
    dm = (goc / STUDY / "ho_so_dtcs" / f"DANH_MUC_HO_SO_DTCS_{STUDY}.md").read_text(encoding="utf-8")
    assert DTCS.ten_ra("de_xuat", STUDY) in dm and "phiếu đề xuất nhiệm vụ" in dm.lower()


def test_doi_chieu_bat_lech_phieu_de_xuat(de_tai_pdx) -> None:
    goc = de_tai_pdx()
    d, _ = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    n = HSC.NguonDeTai(goc, STUDY, json.loads(Path(DTCS.tim_so_ca_nhan()).read_text(encoding="utf-8"))["nguoi"])
    sach = [x for x in HSC.doi_chieu(n, None, d) if x["tai_lieu"] == "phiếu đề xuất nhiệm vụ"]
    assert sach and all(x["ket"] == "khop" for x in sach), sach
    d["phieu_de_xuat"]["ten_nhiem_vu"] = "Tên khác"
    d["phieu_de_xuat"]["muc_tieu"] = ["Mục tiêu khác"]
    d["phieu_de_xuat"]["thoi_gian"] = "12 tháng (từ tháng 01/2027 đến tháng 12/2027)"
    d["phieu_de_xuat"]["don_vi"] = "Khoa Khác"
    lech = {x["truong"] for x in HSC.doi_chieu(n, None, d) if x["tai_lieu"] == "phiếu đề xuất nhiệm vụ"
            and x["ket"] == "lech"}
    assert lech == {"tên đề tài", "mục tiêu", "thời gian", "đơn vị chủ trì"}


def test_sau_chap_thuan_theo_thong_tu_43(de_tai, capsys) -> None:
    goc = de_tai()
    assert HDD.main(["sau-chap-thuan", "--study", STUDY, "--exports-root", str(goc), "--loai", "ca_ba", "--ghi"]) == 0
    out = capsys.readouterr().out
    assert "(a) suy được từ nguồn đã chốt 0" in out and "không có mẫu" in out
    ra = goc / STUDY / "ho_so_hdd" / "sau_chap_thuan"
    for k in SCT.LOAI:
        van = "\n".join(HDD._van_ban_docx(ra / SCT.ten_tep(k, STUDY)))
        assert SCT.LOAI[k][0] in van and "Thông tư 43/2024/TT-BYT" in van, k
        assert not HSC.DAU_DANH_DAU.search(van) and "[CẦN" not in van, k
    td = "\n".join(HDD._van_ban_docx(ra / SCT.ten_tep("tien_do", STUDY)))
    for muc in ("Tuân thủ đề cương", "Bảo vệ quyền, sức khỏe, an toàn", "Biến cố bất lợi", "Vi phạm đề cương",
                "Sửa đổi, bổ sung đề cương"):
        assert muc in td, f"thiếu nội dung Điều 18 khoản 2: {muc}"
    assert "Hoàn thiện đề cương: 11/2026." in td, "kế hoạch tiến độ lấy từ đề cương"
    kq = "\n".join(HDD._van_ban_docx(ra / SCT.ten_tep("ket_qua", STUDY)))
    assert "STROBE" in kq and "toàn vẹn, chính xác, tin cậy" in kq.lower()
    dm = (ra / f"DANH_MUC_SAU_CHAP_THUAN_{STUDY}.md").read_text(encoding="utf-8")
    assert "## Gói ký" in dm and "## Dữ kiện cần nhập" in dm and "số và ngày quyết định chấp thuận" in dm.lower()
    assert "chữ ký, họ tên và ngày ký của chủ nhiệm đề tài" in dm.lower(), "gói ký phải liệt kê đủ chữ ký"


def _sua_g2(**kv):
    def sua(m: dict) -> None:
        m["gate_params"]["G2"].update(kv)
    return sua


def test_sau_chap_thuan_doc_khoa_du_lieu_khi_co(de_tai) -> None:
    goc = de_tai(meta_sua=lambda m: m.__setitem__("data_lock_date", "2027-12-20"))
    d = SCT.trich(goc, STUDY, {})
    assert d["ket_qua"]["b_du_lieu"][0] == "Cơ sở dữ liệu đã khoá ngày 2027-12-20."
    assert d["tien_do"]["giam_sat_xung_dot"] == [], "G2 không khai người giám sát ⇒ không có mục giám sát"
    assert d["chung"]["quyet_dinh_chap_thuan"].startswith(HSC.TIEN_TO_CAN_NHAP)
    d3 = SCT.trich(de_tai(meta_sua=_sua_g2(qd_chap_thuan_so="Quyết định số 99/QĐ-HĐĐĐ ngày 01/12/2026",
                                           coi={"summary": "Có xung đột lợi ích không tài chính",
                                                "monitor": "Người giám sát độc lập giả rà biên bản mỗi quý."})),
                   STUDY, {})
    assert d3["chung"]["quyet_dinh_chap_thuan"] == "Quyết định số 99/QĐ-HĐĐĐ ngày 01/12/2026"
    gs = d3["tien_do"]["giam_sat_xung_dot"]
    assert gs[0] == "Người giám sát độc lập giả rà biên bản mỗi quý." and gs[1].startswith(HSC.TIEN_TO_GOI_KY)
    d2 = SCT.trich(de_tai(meta_sua=lambda m: m["gate_params"]["G2"].__setitem__(
        "sua_doi_de_cuong", [{"muc": "2.5", "noi_dung_cu": "A", "noi_dung_moi": "B", "ly_do": "C"}])), STUDY, {})
    assert d2["sua_doi"]["thay_doi"] == [{"muc": "2.5", "noi_dung_cu": "A", "noi_dung_moi": "B", "ly_do": "C"}]
    assert d2["tien_do"]["dd_sua_doi"].startswith("1 thay đổi đề cương đã trình Hội đồng")


def test_sau_chap_thuan_nguon_thieu_thi_khong_xanh(tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nguồn chưa chốt (không tên đề tài, không chủ nhiệm) ⇒ (a) > 0 và mã 1 — không dựng như đã đủ. Chốt dấu vết máy
    tạm tắt để chính ô (a) quyết định mã thoát (hai lớp chặn được kiểm riêng)."""
    monkeypatch.setattr(SCT_CHAY, "dau_vet_may", lambda p: [])
    (tmp_path / STUDY).mkdir()
    (tmp_path / STUDY / "study_meta.json").write_text("{}", encoding="utf-8", newline="\n")
    for them in ([], ["--ghi"]):  # cả chạy khô lẫn lượt ghi đều không được trả mã 0
        ma = HDD.main(["sau-chap-thuan", "--study", STUDY, "--exports-root", str(tmp_path), "--loai", "tien_do",
                       *them])
        out = capsys.readouterr().out
        assert ma == 1 and "(a) suy được từ nguồn đã chốt 0" not in out and "chung.ten_de_tai" in out, them


def test_kiem_canh_bao_phieu_de_xuat_qua_dai(de_tai_pdx, capsys) -> None:
    """Mẫu PDX ghi «không quá 04 trang» ⇒ phiếu ước dài hơn bị `kiem` nêu thành việc cần làm."""
    def dai(m: dict) -> None:
        m["gate_params"]["G1"]["ho_so_dtcs"] = KHOI_PDX
    goc = de_tai_pdx(meta_sua=dai)
    p = goc / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    doan = "\n\n".join(f"Đoạn lý do thứ {i} " + "nội dung tính cấp thiết của đề tài " * 12 for i in range(40))
    p.write_text(p.read_text(encoding="utf-8").replace("Cần đo tại cơ sở [3].", "Cần đo tại cơ sở [3].\n\n" + doan,
                                                        1), encoding="utf-8", newline="\n")
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "dung", "--ghi") == 0
    capsys.readouterr()
    _chay_dtcs(goc, "kiem")
    out = capsys.readouterr().out
    assert "phiếu đề xuất ước khoảng" in out and f"> {DTCS.SO_TRANG_TOI_DA_PDX} trang" in out


def test_sau_chap_thuan_tien_do_cung_khoi_voi_thuyet_minh(de_tai) -> None:
    """Mốc thiếu thời gian ở đề cương được khối m21_hang giải ở thuyết minh ⇒ báo cáo tiến độ dùng đúng giá trị đó."""
    def khoi(m: dict) -> None:
        m["gate_params"]["G1"]["ho_so_dtcs"] = {"m21_hang": [{"dau": "Thu thập số liệu",
                                                               "thoi_gian": "01–03/2027 (theo phân công)"}]}
    goc = de_tai(meta_sua=khoi)
    p = goc / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| 2 | Thu thập số liệu | 01–03/2027 | Phiếu |",
                                                        "| 2 | Thu thập số liệu |  | Phiếu |", 1),
                 encoding="utf-8", newline="\n")
    d = SCT.trich(goc, STUDY, {})
    hang = {h["noi_dung"].rstrip("."): h["thoi_gian"] for h in d["tien_do"]["ke_hoach"]}
    assert hang["Thu thập số liệu"] == "01–03/2027 (theo phân công)"
    dt, _ = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    tm = {h["noi_dung"].rstrip("."): h["thoi_gian"] for h in dt["thuyet_minh"]["m21_tien_do"]}
    assert tm["Thu thập số liệu"] == hang["Thu thập số liệu"], "báo cáo tiến độ và thuyết minh phải trùng"


def test_sau_chap_thuan_khong_dua_nhan_may_g5_vao_van_ban(de_tai, capsys) -> None:
    """Checkpoint G5 mang nhãn máy («PENDING …») ⇒ văn bản nộp ghi dữ kiện cần nhập, không chép nhãn; nhãn máy lọt vào
    văn bản thì lệnh trả mã 1."""
    goc = de_tai()
    (goc / STUDY / "G5_checkpoint.json").write_text(json.dumps({"database_lock_status": "PENDING — chờ G2 LOCKED"}),
                                                    encoding="utf-8", newline="\n")
    assert HDD.main(["sau-chap-thuan", "--study", STUDY, "--exports-root", str(goc), "--loai", "tien_do",
                     "--ghi"]) == 0
    p = goc / STUDY / "ho_so_hdd" / "sau_chap_thuan" / SCT.ten_tep("tien_do", STUDY)
    van = "\n".join(HDD._van_ban_docx(p))
    assert "PENDING" not in van and "LOCKED" not in van and SCT.dau_vet_may(p) == []
    d = docx.Document(str(p))
    d.add_paragraph("Trạng thái: READY_FOR_G9")
    d.save(str(p))
    assert any("READY_FOR_G9" in x for x in SCT.dau_vet_may(p)), "chốt phải bắt nhãn trạng thái máy"


def test_sau_chap_thuan_nguon_mang_nhan_may_thi_ma_1(de_tai, capsys) -> None:
    """Nguồn G2 còn nhãn máy lọt vào văn bản (người giám sát «PENDING») ⇒ lệnh báo dấu vết máy và trả mã 1."""
    goc = de_tai(meta_sua=_sua_g2(coi={"summary": "Có xung đột lợi ích không tài chính", "monitor": "PENDING"}))
    ma = HDD.main(["sau-chap-thuan", "--study", STUDY, "--exports-root", str(goc), "--loai", "tien_do", "--ghi"])
    out = capsys.readouterr().out
    assert ma == 1 and "DẤU VẾT MÁY" in out and "PENDING" in out
