"""Hồ sơ đăng ký đề tài cấp bệnh viện theo bộ mẫu BVQY175 (21/11/2026) — `tools/ho_so_dtcs_bvqy175.py`.

Fixture tự soạn, ngoại tuyến (repo công khai): đề cương nộp giả mang đủ kiểu dữ kiện của hai đề tài thật (bảng thông tin
chung, mục tiêu kèm giả thuyết H₀/H₁ dạng danh sách — lỗi đếm 4 mục tiêu của C1a, nhân lực dạng bảng và dạng văn xuôi,
tiến độ dạng bảng và dạng các bước quy trình) và TỆP MẪU Word giả dựng bằng python-docx với đúng các mốc, bảng và ô chọn
FORMCHECKBOX của mẫu 01-DK/02-TM — không dùng tệp mẫu của bệnh viện."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

docx = pytest.importorskip("docx")

import ho_so_dtcs_bvqy175 as T  # noqa: E402

MA = "de-tai-thu-dtcs"
DC = f"DE_CUONG_NOP_HOI_DONG_{MA}.md"

DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## KHẢO SÁT THỬ NGHIỆM TẠI KHOA MẪU

## THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Khảo sát thử nghiệm tại Khoa Mẫu C1a, Bệnh viện Quân y 175 |
| Chủ nhiệm đề tài | BS. Người Thử – Khoa Mẫu C1a, Bệnh viện Quân y 175 |
| Đơn vị chủ trì | Khoa Mẫu C1a, Trung tâm Thử, Bệnh viện Quân y 175, Thành phố Hồ Chí Minh |
| Thời gian thực hiện | Từ tháng 12/2026 đến tháng 12/2028 |
| Kinh phí | Tự túc (chủ nhiệm đề tài tự chi trả) |

# 1. ĐẶT VẤN ĐỀ

Câu mở đầu đặt vấn đề.

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

1. Xác định tỷ lệ hài lòng tại khoa mẫu.
2. Phân tích yếu tố liên quan.

## 2.3. Giả thuyết nghiên cứu

- **Giả thuyết H₀:** tỷ số chênh bằng 1.
- **Giả thuyết H₁:** tỷ số chênh khác 1.

# 3. TỔNG QUAN TÀI LIỆU

## 3.1. Khái niệm

Một tổng quan hệ thống quốc tế ghi nhận thời gian chờ liên quan với hài lòng [1].

Tại Việt Nam, các khảo sát cho thấy thủ tục hành chính là điểm yếu [2].

## 3.4. Tình hình trên thế giới

Một nghiên cứu ở Trung Quốc đo thời gian chờ từ phần mềm bệnh viện [3].

## 3.5. Tình hình nghiên cứu tại Việt Nam

Nghiên cứu tại một bệnh viện tỉnh ghi nhận điểm hài lòng cao [4].

## 3.6. Khoảng trống nghiên cứu và đóng góp của đề tài

**Bảng 3.1. Chiến lược tìm kiếm tài liệu**

| Nguồn | Câu tìm |
|---|---|
| PubMed | satisfaction |

**Khoảng trống.** Chưa có số liệu tại khoa mẫu.

**Đóng góp của đề tài.** Đề tài cung cấp số liệu nền cho khoa mẫu.

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 4.1. Thiết kế nghiên cứu

Nghiên cứu mô tả cắt ngang có phân tích [5].

## 4.3. Đối tượng nghiên cứu

### 4.3.1. Tiêu chuẩn lựa chọn

- Người bệnh từ đủ 18 tuổi.

## 4.8. Sai số và biện pháp khống chế sai số

| Nguồn sai lệch | Biện pháp khống chế |
|---|---|
| Sai lệch chọn mẫu | Chọn mẫu hệ thống |

# 6. KẾ HOẠCH THỰC HIỆN

## 6.1. Nhân lực và phân công nhiệm vụ

| Vai trò | Nhiệm vụ chính |
|---|---|
| Chủ nhiệm đề tài | Chịu trách nhiệm chung |
| Điều tra viên | Phát và thu phiếu |

## 6.2. Tiến độ thực hiện

| # | Nội dung công việc | Thời gian dự kiến | Sản phẩm |
|---|---|---|---|
| 1 | Hoàn thiện đề cương | 12/2026 | Đề cương |
| 2 | Thu thập số liệu | 05–10/2027 | Cơ sở dữ liệu đã khóa |
| 3 | Viết báo cáo | 04/2028 | Báo cáo, bản thảo bài báo |

## 6.3. Dự trù kinh phí

| # | Nội dung chi | Thành tiền |
|---|---|---|
| 1 | In phiếu khảo sát | ……… |
| | **Tổng cộng** | ……… |

## 6.6. Kế hoạch phổ biến và ứng dụng kết quả

- Báo cáo kết quả cho Ban Giám đốc và Khoa Mẫu C1a.
- Gửi đăng một bài báo trên tạp chí y học có bình duyệt.

# 7. TÀI LIỆU THAM KHẢO

1. Tác giả A. Bài một. Tạp chí. 2020.
2. Tác giả B. Bài hai. Tạp chí. 2021.
3. Tác giả C. Bài ba. Tạp chí. 2022.
4. Tác giả D. Bài bốn. Tạp chí. 2023.
5. Tác giả E. Bài năm. Tạp chí. 2024.
6. Tác giả F. Bài không được trích. Tạp chí. 2024.
"""

HO_SO = "BS. Người Thử"


def _hop(doc, p, chon: bool = False) -> None:
    """Thêm một ô chọn kiểu FORMCHECKBOX (trường biểu mẫu cũ) vào đoạn p — đúng khuôn mẫu Word của bệnh viện."""
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    xml = (f'<w:r {nsdecls("w")}><w:fldChar w:fldCharType="begin"><w:ffData><w:enabled/><w:checkBox><w:sizeAuto/>'
           f'<w:default w:val="{1 if chon else 0}"/></w:checkBox></w:ffData></w:fldChar></w:r>')
    p._p.append(parse_xml(xml))
    p._p.append(parse_xml(f'<w:r {nsdecls("w")}><w:instrText xml:space="preserve"> FORMCHECKBOX </w:instrText></w:r>'))
    p._p.append(parse_xml(f'<w:r {nsdecls("w")}><w:fldChar w:fldCharType="end"/></w:r>'))


def _bang(doc, hang) -> None:
    tb = doc.add_table(rows=len(hang), cols=len(hang[0]))
    for i, h in enumerate(hang):
        for j, x in enumerate(h):
            tb.rows[i].cells[j].text = x


def _mau_tm(p: Path) -> Path:
    d = docx.Document()
    _bang(d, [["BỘ QUỐC PHÒNG\nBỆNH VIỆN QUÂN Y 175", "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM"]])
    cham = "." * 60
    for t in ("THUYẾT MINH ĐỀ TÀI", "I. THÔNG TIN CHUNG VỀ ĐỀ TÀI", "1. Tên đề tài", cham, cham,
              "- Mã số (được cấp khi Hồ sơ thông qua):", "2. Thời gian thực hiện: ……….tháng",
              "(Từ tháng         /20… đến tháng        /20…)", "4. Tổng kinh phí thực hiện: ..... triệu đồng"):
        d.add_paragraph(t)
    _bang(d, [["Nguồn", "Kinh phí (triệu đồng)"], ["Tự có", ""], ["Khác", ""]])
    d.add_paragraph("7. Lĩnh vực:")
    q = d.add_paragraph("\t")
    _hop(d, q)
    q.add_run(" Kỹ thuật và công nghệ; \t")
    _hop(d, q)
    q.add_run(" Y, dược.")
    for t in ("8. Chủ nhiệm đề tài", f"Họ và tên: {cham} Số định danh cá nhân/CMTQĐ: {cham}",
              f"Điện thoại: {cham} E-mail: {cham}", "Tên đơn vị đang công tác: Khoa …/Bệnh viện Quân y 175",
              "10. Đơn vị chủ trì đề tài", "Tên đơn vị chủ trì thực hiện đề tài:", "12. Thành viên thực hiện đề tài"):
        d.add_paragraph(t)
    _bang(d, [["TT", "Họ và tên,\nhọc hàm, học vị", "Chức danh thực hiện đề tài", "Tổ chức công tác"],
              ["1", "", "Chủ nhiệm đề tài", ""], ["2", "", "Thư ký khoa học", ""], ["3", "", "Thành viên chính", ""]])
    for t in ("13. Mục tiêu của đề tài", cham, cham, "15.1. Đánh giá tổng quan", "Ngoài nước (Phân tích …)", cham,
              "Trong nước (Phân tích …)", cham, "15.2. Luận giải", "(Trên cơ sở đánh giá …)", cham,
              "16. Liệt kê danh mục", "(Tên công trình, tác giả, nơi và năm công bố …)", cham,
              "17. Nội dung nghiên cứu", "- Nội dung thuê chuyên gia …", "Nội dung 1 : " + cham,
              "Công việc 1.1: " + cham,
              "18. Phương án phối hợp", cham, "21. Tiến độ thực hiện"):
        d.add_paragraph(t)
    _bang(d, [["", "Các nội dung, công việc", "Kết quả phải đạt", "Thời gian", "Cá nhân", "Dự kiến kinh phí"],
              ["(1)", "(2)", "(3)", "(4)", "(5)", "(6)"], ["1", "Nội dung 1", "", "", "", ""],
              ["", "- Công việc 1.1", "", "", "", ""]])
    d.add_paragraph("Dạng I: Công bố khoa học")
    _bang(d, [["Số TT", "Tên sản phẩm", "Yêu cầu khoa học cần đạt", "Dự kiến nơi công bố", "Ghi chú"],
              ["(1)", "(2)", "(3)", "(4)", "(5)"], ["1", "", "", "", ""]])
    d.add_paragraph("Dạng II: Nguyên lý ứng dụng; Báo cáo")
    _bang(d, [["TT", "Tên sản phẩm", "Yêu cầu khoa học cần đạt", "Ghi chú"], ["(1)", "(2)", "(3)", "(4)"],
              ["1", "", "", ""]])
    d.add_paragraph("Dạng IV: Đăng ký bảo hộ")
    _bang(d, [["TT", "Tên sản phẩm", "Yêu cầu khoa học cần đạt", "Ghi chú"], ["(1)", "(2)", "(3)", "(4)"],
              ["1", "", "", ""]])
    for t in ("23.4. Mô tả phương thức chuyển giao", "(Chuyển giao …)", cham, "24. Phạm vi và địa chỉ", cham,
              "25.2. Đối với lĩnh vực KH&CN", " (Nêu những …)", cham, "25.3 Đối với đơn vị chủ trì", cham):
        d.add_paragraph(t)
    d.save(str(p))
    return p


def _mau_dk(p: Path) -> Path:
    d = docx.Document()
    tb = d.add_table(rows=1, cols=2)
    tb.rows[0].cells[0].text = "BỆNH VIỆN QUÂN Y 175 "
    tb.rows[0].cells[0].add_paragraph("…")
    tb.rows[0].cells[1].text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
    d.add_paragraph("Kính gửi: Phòng Khoa học quân sự/Bệnh viện Quân y 175.")
    q = d.add_paragraph()
    q.add_run("…")
    q.add_run("1")
    q.add_run(" kính đề nghị Phòng Khoa học Quân sự xem xét và tổ chức đánh giá")
    for t in ("a) Đơn vị đăng ký chủ trì thực hiện nhiệm vụ", "(Tên Khoa, phòng Ban, Trung Tâm, Viện …)",
              "b) Cá nhân đăng ký chủ nhiệm nhiệm vụ", "(Họ tên, học hàm, học vị, cấp bậc, chức vụ …)",
              "Đăng ký chủ trì thực hiện nhiệm vụ KH&CN cấp Bệnh viện:", "." * 60, "." * 60, "Hồ sơ gồm có:"):
        d.add_paragraph(t)
    d.save(str(p))
    return p


def _dung(goc: Path, de_cuong: str = DE_CUONG) -> Path:
    (goc / MA).mkdir(parents=True)
    (goc / MA / DC).write_text(de_cuong, encoding="utf-8", newline="\n")
    return goc


@pytest.fixture()
def goc(tmp_path: Path) -> Path:
    return _dung(tmp_path / "exports")


@pytest.fixture()
def mau(tmp_path: Path) -> Path:
    d = tmp_path / "mau"
    d.mkdir()
    _mau_tm(d / T.MAU["tm"])
    _mau_dk(d / T.MAU["dk"])
    return d


def _mh(de_cuong: str = DE_CUONG) -> T.MoHinh:
    return T.trich(MA, de_cuong.splitlines())


def _chu(p: Path) -> str:
    d = docx.Document(str(p))
    phan = [x.text for x in d.paragraphs] + [c.text for tb in d.tables for r in tb.rows for c in r.cells]
    return "\n".join(phan)


def _anh(d: Path) -> Dict[str, str]:
    return {x.relative_to(d).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in d.rglob("*") if x.is_file()}


# ── Trích ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_trich_thong_tin_chung_va_thoi_gian() -> None:
    mh = _mh()
    assert mh.ten_de_tai.startswith("Khảo sát thử nghiệm tại Khoa Mẫu C1a")
    assert mh.chu_nhiem.startswith(HO_SO) and mh.don_vi.startswith("Khoa Mẫu C1a")
    assert mh.thang == ("12/2026", "12/2028") and mh.tu_co
    assert any("25 tháng" in c for c in mh.canh_bao)


def test_thoi_gian_kieu_btm_lay_khoang_thuc_hien_khong_lay_cua_so_du_lieu() -> None:
    dc = DE_CUONG.replace("| Thời gian thực hiện | Từ tháng 12/2026 đến tháng 12/2028 |",
                          "| Thời gian thực hiện | Cửa sổ dữ liệu 01/01/2026–31/12/2026; thực hiện dự kiến "
                          "11/2026–09/2027 |")
    assert _mh(dc).thang == ("11/2026", "09/2027")


def test_muc_tieu_khong_dem_gia_thuyet_h0_h1() -> None:
    mh = _mh()
    assert [d.van for d in mh.muc_tieu] == ["Xác định tỷ lệ hài lòng tại khoa mẫu.", "Phân tích yếu tố liên quan."]
    dc = DE_CUONG.replace("2. Phân tích yếu tố liên quan.", "2. Phân tích yếu tố liên quan.\n3. Mục tiêu thứ ba.")
    assert any("3 mục tiêu" in c for c in _mh(dc).canh_bao)


def test_tong_quan_tach_theo_ten_muc_roi_tu_khoa_bo_khoang_trong() -> None:
    mh = _mh()
    ngoai = [d.van for d in mh.ngoai_nuoc]
    trong = [d.van for d in mh.trong_nuoc]
    assert "Một nghiên cứu ở Trung Quốc đo thời gian chờ từ phần mềm bệnh viện [3]." in ngoai
    assert "Nghiên cứu tại một bệnh viện tỉnh ghi nhận điểm hài lòng cao [4]." in trong  # theo tên mục «Việt Nam»
    assert "Tại Việt Nam, các khảo sát cho thấy thủ tục hành chính là điểm yếu [2]." in trong  # theo từ khoá
    assert not any("Khoảng trống" in x for x in ngoai + trong)
    assert any(d.van.startswith("**Khoảng trống.**") for d in mh.luan_giai)
    assert not any("Bảng 3.1" in d.van for d in mh.luan_giai)  # chú thích bảng không chép khi không chép bảng
    assert [d.van[:24] for d in mh.dong_gop] == ["**Đóng góp của đề tài.**"]


def test_tltk_chi_tai_lieu_duoc_trich_va_canh_bao_so_la() -> None:
    mh = _mh()
    assert [s for s, _v in mh.tltk] == [1, 2, 3, 4, 5]
    dc = DE_CUONG.replace("có phân tích [5].", "có phân tích [5, 9].")
    assert any("[9]" in c for c in _mh(dc).canh_bao)


def test_vai_tro_tu_bang_va_tu_van_xuoi() -> None:
    assert _mh().vai_tro == ["Chủ nhiệm đề tài", "Điều tra viên"]
    dc = DE_CUONG.replace("| Vai trò | Nhiệm vụ chính |\n|---|---|\n| Chủ nhiệm đề tài | Chịu trách nhiệm chung |\n"
                          "| Điều tra viên | Phát và thu phiếu |",
                          "Chủ nhiệm đề tài: định hướng khoa học. Người trích lại: trích lại 10% hồ sơ. Hội đồng "
                          "chuyên gia (5 người: bác sĩ, dược sĩ): chấm phiếu. Người đảm nhận các vai do chủ nhiệm phân "
                          "công.")
    assert _mh(dc).vai_tro == ["Chủ nhiệm đề tài", "Người trích lại", "Hội đồng chuyên gia"]


def test_tien_do_tu_bang_va_tu_quy_trinh() -> None:
    mh = _mh()
    assert mh.tien_do[1] == ("Thu thập số liệu", "Cơ sở dữ liệu đã khóa", "05–10/2027")
    assert "Cơ sở dữ liệu đã khóa" in mh.san_pham_khac
    assert mh.san_pham_bai_bao == ["Gửi đăng một bài báo trên tạp chí y học có bình duyệt."]
    dc = DE_CUONG.replace("| # | Nội dung công việc | Thời gian dự kiến | Sản phẩm |\n|---|---|---|---|\n"
                          "| 1 | Hoàn thiện đề cương | 12/2026 | Đề cương |\n| 2 | Thu thập số liệu | 05–10/2027 | "
                          "Cơ sở dữ liệu đã khóa |\n| 3 | Viết báo cáo | 04/2028 | Báo cáo, bản thảo bài báo |",
                          "Tiến độ theo các mốc ở quy trình.")
    dc = dc.replace("## 4.8. Sai số", "## 4.7. Quy trình nghiên cứu\n\n1. Chốt đề cương (11/2026).\n2. Trích hồ sơ "
                                     "(22/02–02/04/2027).\n\n## 4.8. Sai số")
    assert _mh(dc).tien_do == [("Chốt đề cương (11/2026).", "", "11/2026"),
                               ("Trích hồ sơ (22/02–02/04/2027).", "", "22/02–02/04/2027")]


def test_moi_doan_chep_la_nguyen_van_de_cuong() -> None:
    mh = _mh()
    for d in mh.muc_tieu + mh.ngoai_nuoc + mh.trong_nuoc + mh.luan_giai + mh.pho_bien:
        assert d.van in DE_CUONG.splitlines()[d.dong - 1], d.van
    md = T.render_tm(mh)
    assert T.LOI_DAN in md and "Số định danh" not in md.split("**8.")[0]


# ── Ghi / chạy khô / PII ─────────────────────────────────────────────────────────────────────────────────────────────

def test_chay_kho_khong_ghi(goc: Path, mau: Path) -> None:
    truoc = _anh(goc)
    assert T.main(["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau)]) == 0
    assert _anh(goc) == truoc


def test_ghi_dien_mau_tm_dung_cho_va_giu_o_ca_nhan(goc: Path, mau: Path) -> None:
    assert T.main(["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau), "--ghi"]) == 0
    ra = goc / MA / T.THU_MUC_RA
    assert sorted(x.name for x in ra.iterdir()) == sorted(v.format(study=MA) for v in T.TEN_RA.values())
    chu = _chu(ra / T.TEN_RA["tm"].format(study=MA))
    assert "Khảo sát thử nghiệm tại Khoa Mẫu C1a" in chu and "(Từ tháng 12/2026 đến tháng 12/2028)" in chu
    assert f"Họ và tên: {HO_SO}" in chu and "Số định danh cá nhân/CMTQĐ: ...." in chu  # ô cá nhân giữ dòng chấm
    assert "Điện thoại: ...." in chu and "Tên đơn vị đang công tác: Khoa Mẫu C1a/Bệnh viện Quân y 175" in chu
    assert "Mục tiêu 1: Xác định tỷ lệ hài lòng tại khoa mẫu." in chu and "Giả thuyết H₀" not in chu.split("15.1")[0]
    assert "**" not in chu and "Khoảng trống." in chu  # đậm thật, không để dấu sao
    assert "Thiết kế nghiên cứu" in chu and "4.1. Thiết kế" not in chu  # bỏ số mục cũ
    assert "Tiêu chuẩn lựa chọn" in chu and "4.3.1." not in chu  # cả tiêu đề cấp 3
    assert "Toàn bộ (đề cương: tự túc)" in chu and "Điều tra viên" in chu
    assert "Thu thập số liệu" in chu and "Nội dung 1 : ." not in chu
    assert "6. Tác giả F" not in chu  # tài liệu không được trích không vào mục 16
    doc = docx.Document(str(ra / T.TEN_RA["tm"].format(study=MA)))
    from docx.oxml.ns import qn
    p = next(x for x in doc.paragraphs if "Y, dược" in x.text)
    assert [c.find(qn("w:default")).get(qn("w:val")) for c in p._p.findall(".//" + qn("w:checkBox"))] == ["0", "1"]
    dang = {T._doan_truoc_bang(doc, tb)[:8]: tb for tb in doc.tables}
    assert dang["Dạng II:"].rows[2].cells[1].text == "Báo cáo tổng hợp kết quả nghiên cứu đề tài"
    assert dang["Dạng IV:"].rows[2].cells[1].text == ""  # bảng Dạng IV cùng khuôn cột — không điền nhầm


def test_ghi_dien_don_dk(goc: Path, mau: Path) -> None:
    assert T.main(["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau), "--ghi"]) == 0
    chu = _chu(goc / MA / T.THU_MUC_RA / T.TEN_RA["dk"].format(study=MA))
    assert "KHOA MẪU C1a" in chu and "C1A" not in chu  # «C1a» giữ nguyên khi viết hoa tên đơn vị
    assert "Khoa Mẫu C1a1 kính đề nghị" in chu  # giữ số chú thích «1» của mẫu
    assert "Khoa Mẫu C1a, Trung tâm Thử, Bệnh viện Quân y 175" in chu
    assert f"{HO_SO}; học hàm, cấp bậc, chức vụ: ………" in chu
    assert "“Khảo sát thử nghiệm tại Khoa Mẫu C1a, Bệnh viện Quân y 175”" in chu


def test_thieu_mau_van_ghi_ban_xem_ma_1(goc: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(T, "tim_thu_muc_mau", lambda: None)
    assert T.main(["--study", MA, "--exports-root", str(goc), "--ghi"]) == 1
    ra = goc / MA / T.THU_MUC_RA
    assert (ra / T.TEN_RA["tm_md"].format(study=MA)).is_file()
    assert "chưa dựng" in (ra / T.TEN_RA["danh_muc"].format(study=MA)).read_text(encoding="utf-8")


def test_ghi_lai_sao_luu_truoc(goc: Path, mau: Path) -> None:
    args = ["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau), "--ghi"]
    assert T.main(args) == 0
    tm = goc / MA / T.THU_MUC_RA / T.TEN_RA["tm_md"].format(study=MA)
    tm.write_text("bản người sửa\n", encoding="utf-8", newline="\n")
    assert T.main(args) == 0
    bk = list((goc / MA / T.THU_MUC_RA / "_sao_luu").glob(tm.name + ".bak-*"))
    assert any(x.read_text(encoding="utf-8") == "bản người sửa\n" for x in bk)


def test_pii_trong_noi_dung_chen_thi_khong_ghi(tmp_path: Path, mau: Path) -> None:
    goc = _dung(tmp_path / "e", DE_CUONG.replace("Báo cáo kết quả cho Ban Giám đốc", "Liên hệ lien.he@vi-du.vn để"))
    truoc = _anh(goc)
    assert T.main(["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau), "--ghi"]) == 3
    assert _anh(goc) == truoc


def test_thieu_de_cuong_ma_2_va_ma_sai_ma_3(tmp_path: Path) -> None:
    (tmp_path / MA).mkdir()
    assert T.main(["--study", MA, "--exports-root", str(tmp_path)]) == 2
    assert T.main(["--study", "../x", "--exports-root", str(tmp_path)]) == 3


def test_tim_thu_muc_mau_theo_bien_moi_truong(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EBM_MAU_DTCS_BVQY175", str(tmp_path))
    assert T.tim_thu_muc_mau() == tmp_path


def test_json_tom_tat(goc: Path, mau: Path, capsys) -> None:
    assert T.main(["--study", MA, "--exports-root", str(goc), "--thu-muc-mau", str(mau), "--json"]) == 0
    t = json.loads(capsys.readouterr().out)
    assert t["muc_tieu"] == 2 and t["vai_tro"] == 2 and t["tien_do"] == 3 and t["pii"] == []
