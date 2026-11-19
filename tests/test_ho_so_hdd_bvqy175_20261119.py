"""Kiểm `tools/ho_so_hdd_bvqy175.py` — hồ sơ Hội đồng Đạo đức BVQY175.

KHÔNG phụ thuộc bộ mẫu thật của bệnh viện (ngoài git, CI không có): tự dựng
mẫu .docx tối thiểu trong `tmp_path` mang đúng các nhãn/FORMCHECKBOX mà công
cụ tìm, và một đề tài giả trong `tmp_path` (study_meta.json tối thiểu).

Luật được canh, mỗi luật tương ứng một hành vi bắt buộc của tool:
  * `trich` KHÔNG bịa — ô không có dữ kiện phải giữ `[CẦN...]`.
  * `trich` không ghi đè JSON đã có (chỉ bổ sung khoá thiếu) trừ `--ghi-de`.
  * `icf` và `mien_icf` loại trừ nhau theo `icf_waiver_requested`.
  * `dung` điền đúng ô đánh dấu theo `--quy-trinh` đã chọn.
  * `kiem` bắt được lệch tên đề tài và vi phạm logic icf/mien_icf.
  * mã thoát: `mau` 2 khi thiếu mẫu; `trich`/`dung` 2 khi thiếu đề tài/JSON;
    `kiem` 0 sạch · 1 còn việc · 2 không đo được.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

docx = pytest.importorskip("docx")

from tools import ho_so_hdd_bvqy175 as hs  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures: đề tài giả + mẫu .docx giả
# ---------------------------------------------------------------------------


def _ghi_study_meta(thu_muc: Path, *, icf_waiver: bool, recruitment_mode: str, title: str) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": title,
        "gate_params": {
            "G1": {"design": "cross_sectional"},
            "G2": {
                "icf_waiver_requested": icf_waiver,
                "recruitment_mode": recruitment_mode,
            },
        },
    }
    (thu_muc / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")


def _ghi_ethics_md(thu_muc: Path, study: str) -> None:
    noi_dung = f"""# A3 | {study}

## TÀI LIỆU 1. ĐƠN XIN PHÊ DUYỆT IRB

```
 Nơi thực hiện: Khoa Khám bệnh giả định, Bệnh viện giả định.
 Cỡ mẫu dự kiến: 123
```

## TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF

```
Chủ nhiệm: [CẦN BỔ SUNG]
Ngày: 2026-11-19
Loại dữ liệu: Hồ sơ điện tử có sẵn
Mã hóa: Mã nghiên cứu, không ghi định danh
Quyền truy cập: Chỉ nhóm nghiên cứu
Kế hoạch hủy: 2 năm, xoá an toàn có biên bản
```
"""
    (thu_muc / f"G2_A3_ETHICS_PACKAGE_{study}.md").write_text(noi_dung, encoding="utf-8", newline="\n")


def _tao_de_tai(
    tmp_path: Path,
    study: str,
    *,
    icf_waiver: bool,
    recruitment_mode: str,
    title: str = "Đề tài giả định",
) -> Path:
    exports_root = tmp_path / "exports"
    thu_muc = exports_root / study
    _ghi_study_meta(thu_muc, icf_waiver=icf_waiver, recruitment_mode=recruitment_mode, title=title)
    _ghi_ethics_md(thu_muc, study)
    return exports_root


def _tao_de_tai_hoi_cuu(tmp_path: Path, study: str) -> Path:
    """Đề tài giả — hồi cứu dữ liệu sẵn có, xin miễn ICF (trường hợp lặp lại
    ở nhiều test, rút ngắn lời gọi `_tao_de_tai`)."""
    return _tao_de_tai(
        tmp_path, study, icf_waiver=True, recruitment_mode="RETROSPECTIVE_SECONDARY_DATA"
    )


def _tao_mau_don4(thu_muc_mau: Path) -> None:
    doc = docx.Document()
    doc.add_paragraph("BỘ QUỐC PHÒNG\tCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    doc.add_paragraph("Họ và tên Chủ nhiệm đề tài (dự án): ")
    doc.add_paragraph("Đơn vị: ")
    doc.add_paragraph("Tên đề tài (dự án) xin đánh giá đạo đức trong nghiên cứu: ")
    doc.add_paragraph("Tên đơn vị chủ trì đề tài (dự án): ")
    doc.add_paragraph("Địa điểm, thời gian triển khai nghiên cứu: ")
    for _ in range(8):
        p = doc.add_paragraph()
        p.add_run(" FORMCHECKBOX \tMục hồ sơ kèm theo")
    thu_muc_mau.mkdir(parents=True, exist_ok=True)
    doc.save(str(thu_muc_mau / hs.TEN_TEP_MAU["don_mau4"]))


def _tao_mau_ly_lich(thu_muc_mau: Path) -> None:
    doc = docx.Document()
    doc.add_paragraph("1. Họ và tên: ")
    doc.add_paragraph("2. Ngày tháng năm sinh: ")
    doc.add_paragraph("3. Nam, nữ: ")
    doc.add_paragraph("4. Địa chỉ gửi thư: ")
    doc.add_paragraph("5. Mobile: ")
    doc.add_paragraph("6. E-mail: ")
    doc.add_paragraph("7. Chức vụ: ")
    doc.add_paragraph("8. Cơ quan - nơi  làm việc: ")
    doc.save(str(thu_muc_mau / hs.TEN_TEP_MAU["ly_lich"]))


@pytest.fixture()
def thu_muc_mau_gia(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    thu_muc = tmp_path / "mau"
    _tao_mau_don4(thu_muc)
    _tao_mau_ly_lich(thu_muc)
    monkeypatch.setenv("EBM_MAU_HDD_BVQY175", str(thu_muc))
    return thu_muc


# ---------------------------------------------------------------------------
# `mau`
# ---------------------------------------------------------------------------


def test_mau_bao_thieu_khi_khong_co_bo_mau(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Dùng thư mục CÓ TỒN TẠI nhưng rỗng: override hợp lệ (is_dir() đúng) nên
    # KHÔNG rơi về auto-detect máy thật — tránh test phụ thuộc máy đang chạy
    # có sẵn bộ mẫu thật hay không.
    thu_muc_rong = tmp_path / "thu-muc-rong"
    thu_muc_rong.mkdir()
    monkeypatch.setenv("EBM_MAU_HDD_BVQY175", str(thu_muc_rong))
    args = hs.build_parser().parse_args(["mau"])
    assert hs.kiem_mau(args) == 2


def test_mau_bao_du_khi_du_bo_mau(thu_muc_mau_gia: Path) -> None:
    for khoa, ten in hs.TEN_TEP_MAU.items():
        if khoa in ("don_mau4", "ly_lich"):
            continue
        (thu_muc_mau_gia / ten).write_bytes(b"")
    args = hs.build_parser().parse_args(["mau"])
    assert hs.kiem_mau(args) == 0


# ---------------------------------------------------------------------------
# `trich` — không bịa
# ---------------------------------------------------------------------------


def test_trich_khong_bia_o_thieu_du_kien(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-01")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-01")
    # Ô cá nhân KHÔNG CÓ trong study_meta — phải giữ placeholder, không bịa.
    assert d["bia"]["nghien_cuu_vien_chinh"] == hs.CAN_BAC_SI_DIEN
    assert d["don_mau4"]["ho_ten_chu_nhiem"] == hs.CAN_BAC_SI_DIEN
    assert d["ly_lich_khoa_hoc"][0]["ngay_thang_nam_sinh"] == hs.CAN_BAC_SI_DIEN
    # Trường trích được PHẢI đúng dữ kiện thật, không rỗng.
    assert d["bia"]["ten_de_tai"] == "Đề tài giả định"
    assert d["don_mau4"]["dia_diem_thoi_gian"].startswith("Khoa Khám bệnh giả định")


def test_trich_suy_luan_a9_tu_hoi_cuu_du_lieu_san_co(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-02")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-02")
    assert d["phu_luc_10"]["phan_ba"]["A"]["A9"]["gia_tri"] is True
    assert d["phu_luc_10"]["phan_ba"]["A"]["A1"]["gia_tri"] is False
    # Mục không suy luận được (A7, A8, A10) vẫn phải để ngỏ — không đoán.
    assert d["phu_luc_10"]["phan_ba"]["A"]["A7"]["gia_tri"] is None


def test_trich_khong_suy_luan_khi_tien_cuu(tmp_path: Path) -> None:
    exports_root = _tao_de_tai(
        tmp_path, "gia-dinh-03", icf_waiver=False, recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS"
    )
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-03")
    assert d["phu_luc_10"]["phan_ba"]["A"]["A9"]["gia_tri"] is None
    assert d["icf"] is not None
    assert d["mien_icf"] is None


def test_trich_bao_loi_khi_khong_co_de_tai(tmp_path: Path) -> None:
    exports_root = tmp_path / "exports"
    exports_root.mkdir()
    with pytest.raises(FileNotFoundError):
        hs.trich_du_kien(exports_root, "khong-ton-tai")


# ---------------------------------------------------------------------------
# `trich --ghi` — không ghi đè, trừ --ghi-de
# ---------------------------------------------------------------------------


def test_lenh_trich_khong_ghi_de_gia_tri_da_sua(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-04")
    duong_dan_json = exports_root / "gia-dinh-04" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    duong_dan_json.parent.mkdir(parents=True)
    da_sua = {
        "phien_ban_schema": "1.0",
        "bia": {"nghien_cuu_vien_chinh": "BS. Nguyễn Văn A (đã bác sĩ điền tay)"},
    }
    duong_dan_json.write_text(json.dumps(da_sua, ensure_ascii=False), encoding="utf-8", newline="\n")

    args = hs.build_parser().parse_args(
        ["trich", "--study", "gia-dinh-04", "--exports-root", str(exports_root), "--ghi"]
    )
    rc = hs.lenh_trich(args)
    assert rc == 0

    ket_qua = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    # Giá trị bác sĩ đã sửa PHẢI còn nguyên.
    assert ket_qua["bia"]["nghien_cuu_vien_chinh"] == "BS. Nguyễn Văn A (đã bác sĩ điền tay)"
    # Khoá còn thiếu (vd don_mau4) PHẢI được bổ sung.
    assert "don_mau4" in ket_qua


def test_lenh_trich_ghi_de_khi_co_co_ghi_de_va_sao_luu(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-05")
    duong_dan_json = exports_root / "gia-dinh-05" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    duong_dan_json.parent.mkdir(parents=True)
    duong_dan_json.write_text(
        json.dumps({"bia": {"nghien_cuu_vien_chinh": "Giá trị cũ"}}, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )

    args = hs.build_parser().parse_args(
        [
            "trich", "--study", "gia-dinh-05", "--exports-root", str(exports_root),
            "--ghi", "--ghi-de",
        ]
    )
    rc = hs.lenh_trich(args)
    assert rc == 0
    ket_qua = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    assert ket_qua["bia"]["nghien_cuu_vien_chinh"] == hs.CAN_BAC_SI_DIEN
    sao_luu = list(duong_dan_json.parent.glob("HO_SO_HDD_BVQY175.bak-*.json"))
    assert len(sao_luu) == 1


# ---------------------------------------------------------------------------
# `dung` — điền ô đánh dấu theo quy trình
# ---------------------------------------------------------------------------


def test_dung_dien_checkbox_theo_quy_trinh_rut_gon(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-06")
    trich_args = hs.build_parser().parse_args(
        ["trich", "--study", "gia-dinh-06", "--exports-root", str(exports_root), "--ghi"]
    )
    assert hs.lenh_trich(trich_args) == 0

    dung_args = hs.build_parser().parse_args(
        [
            "dung", "--study", "gia-dinh-06", "--exports-root", str(exports_root),
            "--quy-trinh", "rut_gon", "--ghi",
        ]
    )
    rc = hs.lenh_dung(dung_args)
    assert rc == 0

    out = exports_root / "gia-dinh-06" / "ho_so_hdd" / "MAU4_DON_XIN_DANH_GIA_DAO_DUC_gia-dinh-06.docx"
    assert out.is_file()
    doc = docx.Document(str(out))
    dau = []
    for p in doc.paragraphs:
        if "☒" in p.text or "☐" in p.text:
            dau.append("☒" if "☒" in p.text else "☐")
    # Mục đầu (bảng kiểm rút gọn) phải ĐÁNH DẤU; mục 2 (phiếu đầy đủ) phải TRỐNG.
    assert dau[0] == "☒"
    assert dau[1] == "☐"
    # Không còn FORMCHECKBOX sống nào trong tệp đã dựng.
    assert "FORMCHECKBOX" not in "\n".join(p.text for p in doc.paragraphs)


def test_dung_dien_checkbox_ca_hai_quy_trinh(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-07")
    hs.lenh_trich(
        hs.build_parser().parse_args(
            ["trich", "--study", "gia-dinh-07", "--exports-root", str(exports_root), "--ghi"]
        )
    )
    hs.lenh_dung(
        hs.build_parser().parse_args(
            ["dung", "--study", "gia-dinh-07", "--exports-root", str(exports_root), "--quy-trinh", "ca_hai", "--ghi"]
        )
    )
    out = exports_root / "gia-dinh-07" / "ho_so_hdd" / "MAU4_DON_XIN_DANH_GIA_DAO_DUC_gia-dinh-07.docx"
    doc = docx.Document(str(out))
    dau = [("☒" if "☒" in p.text else "☐") for p in doc.paragraphs if ("☒" in p.text or "☐" in p.text)]
    assert dau[0] == "☒"  # bảng kiểm rút gọn
    assert dau[1] == "☒"  # phiếu đầy đủ


def test_dung_sinh_mien_icf_khi_xin_mien(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-08")
    hs.lenh_trich(
        hs.build_parser().parse_args(
            ["trich", "--study", "gia-dinh-08", "--exports-root", str(exports_root), "--ghi"]
        )
    )
    hs.lenh_dung(
        hs.build_parser().parse_args(
            ["dung", "--study", "gia-dinh-08", "--exports-root", str(exports_root), "--quy-trinh", "rut_gon", "--ghi"]
        )
    )
    out = exports_root / "gia-dinh-08" / "ho_so_hdd" / "MIEN_ICF_gia-dinh-08.docx"
    assert out.is_file()
    # Mẫu ICF (Mẫu 8) KHÔNG được sinh khi đã xin miễn.
    assert not any(
        p.name.startswith("MAU8") for p in (exports_root / "gia-dinh-08" / "ho_so_hdd").glob("*.docx")
    )


def test_dung_bao_loi_khi_chua_trich(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = tmp_path / "exports"
    (exports_root / "gia-dinh-09").mkdir(parents=True)
    args = hs.build_parser().parse_args(
        ["dung", "--study", "gia-dinh-09", "--exports-root", str(exports_root), "--quy-trinh", "rut_gon", "--ghi"]
    )
    assert hs.lenh_dung(args) == 2


# ---------------------------------------------------------------------------
# `kiem`
# ---------------------------------------------------------------------------


def test_kiem_khong_do_duoc_khi_chua_trich(tmp_path: Path) -> None:
    exports_root = tmp_path / "exports"
    (exports_root / "gia-dinh-10").mkdir(parents=True)
    args = hs.build_parser().parse_args(["kiem", "--study", "gia-dinh-10", "--exports-root", str(exports_root)])
    assert hs.lenh_kiem(args) == 2


def test_kiem_bat_lech_ten_de_tai(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-11")
    hs.lenh_trich(
        hs.build_parser().parse_args(
            ["trich", "--study", "gia-dinh-11", "--exports-root", str(exports_root), "--ghi"]
        )
    )
    duong_dan_json = exports_root / "gia-dinh-11" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    d["bia"]["ten_de_tai"] = "Tên đề tài SAI, không khớp study_meta.json"
    duong_dan_json.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")

    args = hs.build_parser().parse_args(["kiem", "--study", "gia-dinh-11", "--exports-root", str(exports_root)])
    rc = hs.lenh_kiem(args)
    assert rc == 1


def test_kiem_bat_vi_pham_logic_icf_xor_mien_icf(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-12")
    hs.lenh_trich(
        hs.build_parser().parse_args(
            ["trich", "--study", "gia-dinh-12", "--exports-root", str(exports_root), "--ghi"]
        )
    )
    duong_dan_json = exports_root / "gia-dinh-12" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    # Phá luật: xin miễn ICF (waiver=true ở study_meta) nhưng JSON lại có CẢ icf lẫn mien_icf.
    d["icf"] = {"ten_nghien_cuu": "x", "muc": {}}
    duong_dan_json.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")

    args = hs.build_parser().parse_args(["kiem", "--study", "gia-dinh-12", "--exports-root", str(exports_root)])
    rc = hs.lenh_kiem(args)
    assert rc == 1


def test_kiem_sach_khi_du_viec_va_khong_con_can(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-13")
    hs.lenh_trich(
        hs.build_parser().parse_args(
            ["trich", "--study", "gia-dinh-13", "--exports-root", str(exports_root), "--ghi"]
        )
    )
    duong_dan_json = exports_root / "gia-dinh-13" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    _dien_het_can(d)
    duong_dan_json.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")

    hs.lenh_dung(
        hs.build_parser().parse_args(
            ["dung", "--study", "gia-dinh-13", "--exports-root", str(exports_root), "--quy-trinh", "rut_gon", "--ghi"]
        )
    )
    args = hs.build_parser().parse_args(["kiem", "--study", "gia-dinh-13", "--exports-root", str(exports_root)])
    assert hs.lenh_kiem(args) == 0


def _dien_het_can(obj):
    """Giả lập bác sĩ đã điền hết — thay mọi chuỗi còn `[CẦN...]` bằng giá trị."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and "[CẦN" in v:
                obj[k] = "đã điền"
            else:
                _dien_het_can(v)
    elif isinstance(obj, list):
        for v in obj:
            _dien_het_can(v)


# ---------------------------------------------------------------------------
# Đếm [CẦN...]
# ---------------------------------------------------------------------------


def test_dem_can_khong_dem_chuoi_khong_lien_quan() -> None:
    assert hs._dem_can({"a": "bình thường", "b": ["[CẦN BỔ SUNG]", "ổn"]}) == 1
    assert hs._dem_can("[CẦN BÁC SĨ ĐIỀN]") == 1
    assert hs._dem_can({"a": {"b": {"c": "[CẦN KÝ]"}}}) == 1
