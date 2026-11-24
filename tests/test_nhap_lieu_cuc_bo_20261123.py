"""Hệ nhập liệu CỤC BỘ theo từ điển REDCap của G5 (tools/nhap_lieu_cuc_bo.py — bác sĩ chọn 23/11/2026: bệnh viện chưa
có REDCap, nhập lại phiếu giấy trên máy người nhập).

DÒNG ĐẦU docstring mỗi test ghi mã yêu cầu (YC-xx) — `ho-so-tham-dinh` đọc dòng đó để dựng ma trận truy vết.
Từ điển + dữ liệu đều GIẢ (không PII); chuỗi giống định danh được ghép từ mảnh để không lọt máy quét bí mật/PII.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as SP  # noqa: E402
import nhap_lieu_cuc_bo as M  # noqa: E402
import sinh_du_lieu_redcap as SDR  # noqa: E402

STUDY = "gia-lap-nhap-lieu-cuc-bo"
TD_COT = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip
# ten, form, loai, nhan, lua_chon, kiem_tra, min, max, nhanh, bat_buoc, chu_thich, dinh_danh
TRUONG = [
    ("record_id", "sang_loc", "text", "Mã phiếu", "", "", "", "", "", "y", "", ""),
    ("ho_ten", "sang_loc", "text", "Họ tên", "", "", "", "", "", "n", "", "y"),
    ("ma_noi_bo", "sang_loc", "text", "Mã nội bộ khoa", "", "", "", "", "", "n", "", "y"),
    ("so_dien_thoai", "sang_loc", "text", "Số điện thoại", "", "", "", "", "", "n", "", ""),
    ("tc_dien_thoai", "sang_loc", "radio", "Có điện thoại nhận tin", "1, Có | 0, Không", "", "", "", "", "n", "", ""),
    ("tuoi", "sang_loc", "text", "Tuổi", "", "integer", "18", "90", "", "y", "", ""),
    ("gioi", "sang_loc", "radio", "Giới", "1, Nam | 2, Nữ", "", "", "", "", "y", "", ""),
    ("co_benh_kem", "sang_loc", "yesno", "Có bệnh kèm", "", "", "", "", "", "y", "", ""),
    ("benh_kem", "sang_loc", "checkbox", "Bệnh kèm", "1, THA | 2, ĐTĐ | 3, Khác", "", "", "",
     "[co_benh_kem] = '1'", "n", "@MAXCHECKED=2", ""),
    ("du_tieu_chuan", "sang_loc", "calc", "Đủ tiêu chuẩn", "if([tuoi] >= 40, 1, 0)", "", "", "", "", "n", "", ""),
    ("ngay_kham", "theo_doi", "text", "Ngày khám", "", "date_ymd", "2026-01-01", "2026-12-31", "", "y", "", ""),
    ("ha_tam_thu", "theo_doi", "text", "HA tâm thu", "", "integer", "70", "250", "", "y", "", ""),
    ("hba1c", "theo_doi", "text", "HbA1c (%)", "", "number", "4", "15", "[du_tieu_chuan] = '1'", "y", "", ""),
    ("ghi_chu", "theo_doi", "notes", "Ghi chú", "", "", "", "", "", "n", "", ""),
]  # fmt: skip
MA_THIEU = [("*", "BTR", "Bỏ trống"), ("*", "KDD", "Không đọc được")]
LUAT_DQ = [("DQ01", "truy_van", "HA tâm thu rất cao", "[ha_tam_thu] > 180")]
SDT_GIA = "09" + "12" + "345678"  # mảnh ghép — số điện thoại GIẢ để thử chặn định danh
HINH_MAU = {
    "record_id": {"co_dinh": "GL-{i:03d}"}, "tuoi": {"chuan": (55, 12)}, "ha_tam_thu": {"chuan": (150, 30)},
    "hba1c": {"chuan": (7.5, 1.5), "so_le": 1}, "ngay_kham": {"tu": "2026-02-01", "den": "2026-10-31"},
    "ghi_chu": {"chon_chu": ["", "tái khám đúng hẹn", "quên thuốc hai ngày"]}, "co_benh_kem": {"p": 0.6},
    "benh_kem": {"p": {"1": 0.5, "2": 0.4, "3": 0.2}}, "tc_dien_thoai": {"p": 0.7}, "gioi": {"phan_bo": {"1": 0.5,
                                                                                                         "2": 0.5}},
}  # fmt: skip


def _ghi_csv(p: Path, tieu_de: list[str], hang: list[list[str]]) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows(hang)


def _ghi_tu_dien(p: Path, truong=TRUONG) -> None:
    hang = []
    for ten, form, loai, nhan, lc, kt, mn, mx, nh, bb, ct, dd in truong:
        r = dict.fromkeys(TD_COT, "")
        r.update({TD_COT[0]: ten, TD_COT[1]: form, TD_COT[3]: loai, TD_COT[4]: nhan, TD_COT[5]: lc, TD_COT[7]: kt,
                  TD_COT[8]: mn, TD_COT[9]: mx, TD_COT[10]: dd, TD_COT[11]: nh, TD_COT[12]: bb, TD_COT[17]: ct})
        hang.append([r[k] for k in TD_COT])
    _ghi_csv(p, TD_COT, hang)


@pytest.fixture()
def de_tai(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(SP, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    _ghi_tu_dien(d / f"G5_REDCap_dictionary_{STUDY}.csv")
    _ghi_csv(d / "_ma-thieu-theo-bien.csv", ["bien", "ma", "nhan"], [list(x) for x in MA_THIEU])
    _ghi_csv(d / "_luat-dq.csv", ["ma_luat", "muc_do", "mo_ta", "bieu_thuc_redcap"], [list(x) for x in LUAT_DQ])
    (d / "study_meta.json").write_text(json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
    return d


@pytest.fixture()
def kho(tmp_path, de_tai) -> M.Kho:
    return M.Kho.khoi_tao(STUDY, tmp_path / "may_nhap" / "kho", "QL01", pin="2468")


@pytest.fixture()
def phien(kho):
    ql = kho.dang_nhap("QL01", "2468")
    kho.them_nguoi(ql, "NV1", "nhap_lieu_1", pin="1357")
    kho.them_nguoi(ql, "NV2", "nhap_lieu_2")
    return {"ql": ql, "n1": kho.dang_nhap("NV1", "1357"), "n2": kho.dang_nhap("NV2")}


def _gt_form(kho: M.Kho, hang: dict, form: str) -> dict[str, str]:
    return {c.ten: SDR._chuoi(hang.get(c.ten)) for c in kho.kh.cot_cua_form(form)}


def _nhap_luot(kho, ph, rid: str, lan: str, hang: dict) -> None:
    for form in kho.kh.forms:
        kq = kho.luu_bieu_mau(ph, rid, lan, form, _gt_form(kho, hang, form))
        assert kq.luu and not kq.co_loi(), (rid, form, kq.loi, kq.loi_chung)
    kho.hoan_tat_luot(ph, rid, lan)


HANG_MAU = {"record_id": "BN-001", "tc_dien_thoai": "1", "tuoi": "45", "gioi": "2", "co_benh_kem": "1",
            "benh_kem___1": "1", "benh_kem___2": "0", "benh_kem___3": "0", "ngay_kham": "2026-03-12",
            "ha_tam_thu": "130", "hba1c": "7.2", "ghi_chu": "tái khám đúng hẹn"}  # fmt: skip


def _phieu_doi_chieu_xong(kho, phien, rid="BN-001", hang=None, hang2=None) -> str:
    h = {**HANG_MAU, "record_id": rid, **(hang or {})}
    kho.tao_phieu(phien["n1"], rid)
    _nhap_luot(kho, phien["n1"], rid, "lan1", h)
    _nhap_luot(kho, phien["n2"], rid, "lan2", {**h, **(hang2 or {})})
    kho.doi_chieu(phien["ql"], rid)
    return rid


_TRIGGER_SQL = "CREATE TRIGGER" + M._LUOC_DO.split("CREATE TRIGGER", 1)[1]


def _sua_nhat_ky(kho: M.Kho, sql: str, ts=()) -> None:
    """Giả lập kẻ sửa ngầm: gỡ trigger, sửa thẳng SQLite, DỰNG LẠI trigger (không để lại dấu trigger bị gỡ)."""
    cn = sqlite3.connect(kho.duong_dan, isolation_level=None)
    try:
        cn.execute("DROP TRIGGER nhat_ky_khong_sua")
        cn.execute("DROP TRIGGER nhat_ky_khong_xoa")
        cn.execute(sql, ts)
        cn.executescript(_TRIGGER_SQL)
    finally:
        cn.close()


def _tinh_lai_chuoi(kho: M.Kho, stt_sua: int, *, viet_lai_neo: bool) -> None:
    """Giả lập kẻ sửa TINH VI: sửa lý do của một bản ghi rồi TÍNH LẠI băm của cả chuỗi phía sau (chuỗi tự nhất quán);
    `viet_lai_neo` ⇒ viết lại cả tệp neo cạnh kho cho khớp chuỗi mới."""
    cn = sqlite3.connect(kho.duong_dan, isolation_level=None)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("DROP TRIGGER nhat_ky_khong_sua")
        ds = [dict(r) for r in cn.execute("SELECT * FROM nhat_ky ORDER BY stt")]
        truoc = M.HASH_GOC
        for d in ds:
            if d["stt"] == stt_sua:
                d["ly_do"] = "đã sửa rồi tính lại chuỗi"
            d["prev_hash"] = truoc
            d["hash"] = M.bam_ban_ghi(d["stt"], truoc, d)
            cn.execute("UPDATE nhat_ky SET ly_do = ?, prev_hash = ?, hash = ? WHERE stt = ?",
                       (d["ly_do"], d["prev_hash"], d["hash"], d["stt"]))  # fmt: skip
            truoc = d["hash"]
        cn.execute("DROP TRIGGER nhat_ky_khong_xoa")
        cn.executescript(_TRIGGER_SQL)
    finally:
        cn.close()
    if viet_lai_neo:
        theo = {d["stt"]: d["hash"] for d in ds}
        dong = [json.loads(x) for x in kho.tep_neo.read_text(encoding="utf-8").splitlines() if x.strip()]
        kho.tep_neo.write_text("".join(json.dumps({"stt": n["stt"], "hash": theo[n["stt"]]}) + "\n" for n in dong),
                               encoding="utf-8", newline="\n")  # fmt: skip


# ───────────────────────────── vị trí kho ─────────────────────────────


def test_tu_choi_onedrive_va_dam_may(tmp_path):
    """YC-01: kho trong OneDrive / CloudStorage / iCloud bị TỪ CHỐI (kể cả đi qua symlink)."""
    for p in (tmp_path / "OneDrive - Personal" / "kho", tmp_path / "Library" / "CloudStorage" / "x" / "kho",
              tmp_path / "Mobile Documents" / "kho"):
        with pytest.raises(M.TuChoi, match="ĐỒNG BỘ ĐÁM MÂY"):
            M.kiem_vi_tri_du_lieu(p)
    od = tmp_path / "OneDrive-Personal" / "that"
    od.mkdir(parents=True)
    lien_ket = tmp_path / "NhapLieuLienKet"
    try:
        lien_ket.symlink_to(od, target_is_directory=True)
    except (OSError, NotImplementedError):  # Windows không quyền tạo symlink: phần này không đo được trên máy đó
        lien_ket = None
    if lien_ket is not None:
        with pytest.raises(M.TuChoi, match="ĐỒNG BỘ ĐÁM MÂY"):
            M.kiem_vi_tri_du_lieu(lien_ket / "kho")
    M.kiem_vi_tri_du_lieu(tmp_path / "NhapLieu" / "de-tai")  # thư mục thường: được


def test_tu_choi_trong_repo_git(tmp_path):
    """YC-01: kho nằm trong một repo git (bất kỳ repo nào) bị TỪ CHỐI; repo hệ thống cũng vậy."""
    (tmp_path / "repo_khac" / ".git").mkdir(parents=True)
    with pytest.raises(M.TuChoi, match="repo git"):
        M.kiem_vi_tri_du_lieu(tmp_path / "repo_khac" / "du_lieu" / "kho")
    with pytest.raises(M.TuChoi, match="repo git"):
        M.kiem_vi_tri_du_lieu(M.BASE / "exports" / "x")


def test_mac_dinh_ngoai_onedrive(tmp_path, monkeypatch, de_tai):
    """YC-01: mặc định ~/NhapLieu/<mã>; khởi tạo ở đó được, kho là SQLite, quyền chỉ chủ trên POSIX."""
    monkeypatch.setenv("HOME", str(tmp_path / "nha"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "nha"))
    assert M.thu_muc_kho_mac_dinh(STUDY) == tmp_path / "nha" / "NhapLieu" / STUDY
    k = M.Kho.khoi_tao(STUDY, None, "QL01")
    assert k.duong_dan == tmp_path / "nha" / "NhapLieu" / STUDY / M.TEN_KHO
    assert k.duong_dan.read_bytes()[:16] == b"SQLite format 3\x00"
    if M.os.name != "nt":
        assert (k.duong_dan.stat().st_mode & 0o077) == 0
    with pytest.raises(M.TuChoi, match="không tạo đè"):
        M.Kho.khoi_tao(STUDY, None, "QL02")


# ───────────────────────────── dấu vân tay từ điển ─────────────────────────────


def test_tu_dien_doi_tu_choi_mo_khong_di_tru(kho, de_tai, tmp_path):
    """YC-02: đổi mã lựa chọn ⇒ từ chối mở và nói cách xử lý; sửa câu chữ nhãn ⇒ vẫn mở; mở bằng từ điển cũ được."""
    td = de_tai / f"G5_REDCap_dictionary_{STUDY}.csv"
    goc = td.read_text(encoding="utf-8")
    td.write_text(goc.replace("Có bệnh kèm", "Có bệnh mạn kèm theo"), encoding="utf-8", newline="")
    M.Kho.mo(STUDY, kho.thu_muc)  # chỉ đổi nhãn: dấu vân tay không đổi
    td.write_text(goc.replace("1, Nam | 2, Nữ", "1, Nam | 2, Nữ | 3, Khác"), encoding="utf-8", newline="")
    with pytest.raises(M.TuChoi) as e:
        M.Kho.mo(STUDY, kho.thu_muc)
    assert "TỪ ĐIỂN ĐÃ ĐỔI" in str(e.value) and "không tự di trú" in str(e.value).lower()
    assert "tu-dien-kho" in str(e.value)
    cu = tmp_path / "ngoai" / "tu_dien_cu.csv"
    assert M.main(["tu-dien-kho", "--study", STUDY, "--kho", str(kho.thu_muc), "--ra", str(cu)]) == M.MA_OK
    M.Kho.mo(STUDY, kho.thu_muc, tu_dien=cu)  # mở bằng đúng từ điển kho đang ràng
    assert M.main(["trang-thai", "--study", STUDY, "--kho", str(kho.thu_muc)]) == M.MA_TU_CHOI


# ───────────────────────────── định danh ─────────────────────────────


def test_khong_luu_truong_dinh_danh(kho, phien):
    """YC-03: Identifier? = y và tên cột định danh theo luật cổng tiếp nhận ⇒ không lưu; cột phân loại có mã miễn."""
    assert set(kho.kh.dinh_danh) == {"ho_ten", "ma_noi_bo", "so_dien_thoai"}
    assert "tc_dien_thoai" in kho.kh.cot_theo_ten  # «Có điện thoại — Có/Không» không phải số điện thoại
    assert "ma_noi_bo" not in [c.ten for c in kho.kh.cot]
    kho.tao_phieu(phien["n1"], "BN-001")
    for ten in ("ho_ten", "ma_noi_bo", "so_dien_thoai"):
        with pytest.raises(M.TuChoi, match="ĐỊNH DANH"):
            kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {ten: "x"})


def test_ma_ban_ghi_dinh_danh_tu_choi_khoi_tao(tmp_path, de_tai):
    """YC-03: trường mã bản ghi mang tên định danh (ma_bn) ⇒ không tạo kho."""
    td = de_tai / f"G5_REDCap_dictionary_{STUDY}.csv"
    _ghi_tu_dien(td, [("ma_bn", *TRUONG[0][1:]), *TRUONG[1:]])
    with pytest.raises(M.TuChoi, match="mã bản ghi"):
        M.Kho.khoi_tao(STUDY, tmp_path / "k2", "QL01")


def test_gia_tri_va_ma_phieu_giong_dinh_danh_bi_chan(kho, phien):
    """YC-03: mã phiếu chỉ là mã nghiên cứu; giá trị/lý do khớp mẫu định danh của cổng tiếp nhận ⇒ không lưu."""
    for sai in (SDT_GIA, "BN 01", "Nguyễn", ""):
        with pytest.raises(M.TuChoi):
            kho.tao_phieu(phien["n1"], sai)
    kho.tao_phieu(phien["n1"], "BN-001")
    kq = kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "theo_doi", {"ghi_chu": f"gọi {SDT_GIA}"})
    assert not kq.luu and "định danh" in " ".join(kq.loi["ghi_chu"])
    kq = kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "theo_doi", {"ngay_kham": "2026-03-12"})
    assert kq.luu  # cột khai kiểu ngày: cổng miễn mẫu «date» ⇒ hệ cũng nhận


# ───────────────────────────── biểu mẫu, logic nhánh, calc ─────────────────────────────


def test_bieu_mau_kiem_kieu_khoang_ma_thieu_loi_tai_cho(kho, phien):
    """YC-05: lỗi định dạng chặn lưu (tiếng Việt, tại ô); ngoài khoảng/danh mục là truy vấn tại chỗ; mã thiếu nhận."""
    kho.tao_phieu(phien["n1"], "BN-001")
    kq = kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {"tuoi": "4,5", "gioi": "01"})
    assert not kq.luu and set(kq.loi) == {"tuoi", "gioi"}
    assert "dấu phẩy" in kq.loi["tuoi"][0]
    kq = kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "theo_doi", {"ngay_kham": "12/03/2026"})
    assert not kq.luu and "năm-tháng-ngày" in kq.loi["ngay_kham"][0]
    kq = kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {"tuoi": "95", "gioi": "btr"})
    assert kq.luu and "lớn hơn 90" in " ".join(kq.canh_bao["tuoi"])
    assert kq.da_luu["gioi"] == "BTR"  # mã thiếu gõ thường ⇒ chuẩn hoá đúng mã của từ điển
    assert any("bắt buộc" in x for x in kq.canh_bao["co_benh_kem"])


def test_logic_nhanh_va_calc_dung_bo_danh_gia_chung(kho, phien):
    """YC-06: câu nhánh ẩn/hiện theo ĐÚNG danh_gia_logic; calc tính bằng tinh_calc mở câu phía sau."""
    kho.tao_phieu(phien["n1"], "BN-001")
    kq = kho.xem_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {"co_benh_kem": "0", "tuoi": "30"})
    assert kq.hien_thi["benh_kem___1"] is False and kq.hien_thi["hba1c"] is False
    assert kq.calc["du_tieu_chuan"] == "0"
    kq = kho.xem_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {"co_benh_kem": "1", "tuoi": "45"})
    assert kq.hien_thi["benh_kem___1"] is True and kq.hien_thi["hba1c"] is True
    assert kq.calc["du_tieu_chuan"] == "1"
    assert kq.hien_thi["tuoi"] is True


def test_logic_khong_danh_gia_duoc_canh_bao_khong_doan(tmp_path, de_tai):
    """YC-06: biểu thức ngoài tập con (datediff) ⇒ hiển thị None + cảnh báo, không coi là đúng/sai."""
    td = de_tai / f"G5_REDCap_dictionary_{STUDY}.csv"
    them = ("tai_kham", "theo_doi", "text", "Tái khám", "", "", "", "", "datediff([ngay_kham], 'today', 'd') > 30",
            "n", "", "")
    _ghi_tu_dien(td, [*TRUONG, them])
    k = M.Kho.khoi_tao(STUDY, tmp_path / "k3", "QL01")
    ql = k.dang_nhap("QL01")
    k.them_nguoi(ql, "NV1", "nhap_lieu_1")
    n1 = k.dang_nhap("NV1")
    k.tao_phieu(n1, "BN-001")
    kq = k.xem_bieu_mau(n1, "BN-001", "lan1", "theo_doi", {"tai_kham": "x"})
    assert kq.hien_thi["tai_kham"] is None
    assert any("không đánh giá được" in x for x in kq.canh_bao["tai_kham"])


# ───────────────────────────── người nhập, PIN ─────────────────────────────


def test_pin_bam_co_muoi_khong_luu_ro(kho, phien):
    """YC-07: PIN băm PBKDF2 có muối riêng; tệp kho không chứa PIN dạng rõ; sai PIN bị từ chối và ghi nhật ký."""
    ql = phien["ql"]
    kho.them_nguoi(ql, "NV3", "nhap_lieu_1", pin="1357")
    with sqlite3.connect(kho.duong_dan) as cn:
        hang = {r[0]: r for r in cn.execute("SELECT ma, pin_bam, pin_muoi, pin_vong FROM nguoi")}
    assert hang["NV1"][1] != hang["NV3"][1] and hang["NV1"][2] != hang["NV3"][2]  # cùng PIN, muối khác ⇒ băm khác
    assert hang["NV1"][3] == M.VONG_BAM_PIN and hang["NV2"][1] is None
    # 24/11/2026: trước đây quét thô `b"1357" not in tệp` — đỏ giả ngẫu nhiên (CI #429) vì tệp chứa nhiều chuỗi băm hex
    # (muối, chuỗi nhật ký) mà chữ số thập phân cũng là chữ số hex. Ý định giữ nguyên: PIN không được nằm DẠNG RÕ —
    # (1) không ô nào của mọi bảng bằng PIN hay chứa PIN như một cụm riêng; (2) quét thô tệp (bắt cả trang trống) chỉ bỏ
    # qua lần xuất hiện nằm lọt giữa một chuỗi hex.
    import re  # noqa: PLC0415
    with sqlite3.connect(kho.duong_dan) as cn:
        bang = [r[0] for r in cn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        o = [v for b in bang for hang_o in cn.execute(f'SELECT * FROM "{b}"') for v in hang_o]
    for pin in ("1357", "2468"):
        cum_rieng = re.compile(rf"(?<![0-9a-fA-F]){pin}(?![0-9a-fA-F])")
        for v in o:
            chu = v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)
            assert chu != pin and not cum_rieng.search(chu), f"PIN {pin} nằm dạng rõ trong kho"
        assert not re.search(rb"(?<![0-9a-fA-F])" + pin.encode() + rb"(?![0-9a-fA-F])",
                             kho.duong_dan.read_bytes()), f"PIN {pin} nằm dạng rõ trong tệp kho"
    with pytest.raises(M.TuChoi):
        kho.dang_nhap("NV1", "0000")
    with pytest.raises(M.TuChoi):
        kho.dang_nhap("Nguyen Van A", None)
    with sqlite3.connect(kho.duong_dan) as cn:
        sai = cn.execute("SELECT nguoi FROM nhat_ky WHERE hanh_dong = 'DANG_NHAP_SAI'").fetchall()
    assert [r[0] for r in sai] == ["NV1", "?"]  # mã gõ sai không được ghi nguyên văn
    assert "KHÔNG phải chữ ký điện tử" in M.QUY_TRACH


def test_vai_va_phien_gan_nguoi(kho, phien):
    """YC-07: chỉ quản lý dữ liệu khai người; phiên giả (vai không khớp kho) bị từ chối."""
    with pytest.raises(M.TuChoi, match="quan_ly_du_lieu"):
        kho.them_nguoi(phien["n1"], "NV9", "nhap_lieu_2")
    with pytest.raises(M.TuChoi, match="phiên"):
        kho.tao_phieu(M.Phien("NV1", "quan_ly_du_lieu"), "BN-009")
    with pytest.raises(M.TuChoi, match="vai"):
        kho.them_nguoi(phien["ql"], "NV9", "admin")


# ───────────────────────────── nhật ký chuỗi băm ─────────────────────────────


def test_nhat_ky_ghi_du_truong_va_ly_do_bat_buoc(kho, phien):
    """YC-08: mỗi ô đổi một bản ghi (múi giờ, người, mã phiếu, lượt, trường, cũ→mới); sửa giá trị đã lưu đòi lý do."""
    n1 = phien["n1"]
    kho.tao_phieu(n1, "BN-001")
    assert kho.luu_bieu_mau(n1, "BN-001", "lan1", "sang_loc", {"tuoi": "50"}).luu
    kq = kho.luu_bieu_mau(n1, "BN-001", "lan1", "sang_loc", {"tuoi": "51"})
    assert not kq.luu and "lý do" in kq.loi["tuoi"][0]
    assert kho.luu_bieu_mau(n1, "BN-001", "lan1", "sang_loc", {"tuoi": "51"}, {"tuoi": "gõ nhầm, đối chiếu phiếu"}).luu
    with sqlite3.connect(kho.duong_dan) as cn:
        cn.row_factory = sqlite3.Row
        ds = [dict(r) for r in cn.execute("SELECT * FROM nhat_ky WHERE hanh_dong = 'NHAP' AND cot = 'tuoi'")]
    assert [(d["cu"], d["moi"]) for d in ds] == [("", "50"), ("50", "51")]
    d = ds[1]
    assert d["nguoi"] == "NV1" and d["record_id"] == "BN-001" and d["lan"] == "lan1"
    assert d["ly_do"] == "gõ nhầm, đối chiếu phiếu" and M.re.search(r"[+-]\d{2}:\d{2}$", d["luc"])
    with sqlite3.connect(kho.duong_dan) as cn, pytest.raises(sqlite3.DatabaseError, match="chi ghi them"):
        cn.execute("UPDATE nhat_ky SET moi = 'x' WHERE stt = 1")
    with sqlite3.connect(kho.duong_dan) as cn, pytest.raises(sqlite3.DatabaseError, match="chi ghi them"):
        cn.execute("DELETE FROM nhat_ky WHERE stt = 1")


def test_kiem_nhat_ky_bat_sua_ngam_truong_khong_phat_lai(kho, phien):
    """YC-09: sửa ngầm MỘT trường không dùng để phát lại (lý do) ⇒ chuỗi băm bắt, mã thoát CLI khác 0."""
    _phieu_doi_chieu_xong(kho, phien)
    assert kho.kiem_nhat_ky()["dat"]
    assert M.main(["kiem-nhat-ky", "--study", STUDY, "--kho", str(kho.thu_muc)]) == M.MA_OK
    _sua_nhat_ky(kho, "UPDATE nhat_ky SET ly_do = 'sửa ngầm' WHERE hanh_dong = 'DANG_NHAP' AND stt = "
                      "(SELECT MIN(stt) FROM nhat_ky WHERE hanh_dong = 'DANG_NHAP')")
    kt = kho.kiem_nhat_ky()
    assert not kt["dat"] and any("bị sửa" in x for x in kt["loi"])
    assert M.main(["kiem-nhat-ky", "--study", STUDY, "--kho", str(kho.thu_muc)]) == M.MA_LOI


def test_kiem_nhat_ky_bat_tinh_lai_chuoi(kho, phien):
    """YC-09: kẻ sửa rồi TÍNH LẠI cả chuỗi (chuỗi tự nhất quán, trigger dựng lại) ⇒ tệp neo cạnh kho bắt."""
    _phieu_doi_chieu_xong(kho, phien)
    _tinh_lai_chuoi(kho, 3, viet_lai_neo=False)
    kt = M.kiem_kho_tep(kho.duong_dan, kho.tep_neo, thu_muc_bang_chung=None)
    assert not kt["dat"] and any("neo stt" in x for x in kt["loi"]), kt["loi"]


def test_kiem_nhat_ky_trigger_bi_go_la_do(kho, phien):
    """YC-09: trigger chặn sửa/xoá nhật ký bị gỡ ⇒ ĐỎ dù chưa sửa bản ghi nào."""
    _phieu_doi_chieu_xong(kho, phien)
    with sqlite3.connect(kho.duong_dan) as cn:
        cn.execute("DROP TRIGGER nhat_ky_khong_xoa")
    kt = kho.kiem_nhat_ky()
    assert not kt["dat"] and any("trigger" in x for x in kt["loi"])


def test_dau_chuoi_trong_tom_tat_bang_chung_la_neo(kho, phien, tmp_path):
    """YC-09, YC-16: sau khi xuất, kẻ tính lại chuỗi VÀ viết lại cả tệp neo ⇒ đầu chuỗi ghi ở tóm tắt bằng chứng bắt."""
    ql = phien["ql"]
    rid = _phieu_doi_chieu_xong(kho, phien)
    kho.quet_truy_van(ql)
    kho.khoa_phieu(ql, rid)
    kho.xuat(ql, tmp_path / "xuat")
    _tinh_lai_chuoi(kho, 3, viet_lai_neo=True)
    assert M.kiem_kho_tep(kho.duong_dan, kho.tep_neo, thu_muc_bang_chung=None)["dat"]  # neo cạnh kho đã bị viết lại
    kt = kho.kiem_nhat_ky()
    assert not kt["dat"] and any("tóm tắt" in x or "NHAP_LIEU_CUC_BO" in x for x in kt["loi"]), kt["loi"]


def test_kiem_nhat_ky_bat_cat_duoi_va_sua_thang_kho(kho, phien):
    """YC-09: xoá bản ghi cuối (chuỗi còn tự nhất quán) ⇒ neo cuối bắt; sửa thẳng bảng giá trị ⇒ phát lại bắt."""
    _phieu_doi_chieu_xong(kho, phien)
    _sua_nhat_ky(kho, "DELETE FROM nhat_ky WHERE stt = (SELECT MAX(stt) FROM nhat_ky)")
    kt = kho.kiem_nhat_ky()
    assert not kt["dat"] and any("neo" in x for x in kt["loi"])


def test_phat_lai_bat_sua_thang_bang_gia_tri(kho, phien):
    """YC-09: giá trị sửa thẳng trong SQLite không qua công cụ ⇒ phát lại nhật ký khác kho ⇒ ĐỎ."""
    _phieu_doi_chieu_xong(kho, phien)
    with sqlite3.connect(kho.duong_dan) as cn:
        cn.execute("UPDATE gia_tri SET gia_tri = '99' WHERE lan = 'chot' AND cot = 'tuoi'")
    kt = kho.kiem_nhat_ky()
    assert not kt["dat"] and any("KHÔNG khớp nhật ký" in x for x in kt["loi"])


def test_khong_co_lenh_xoa_nhat_ky():
    """YC-09: không lệnh CLI nào xoá/sửa nhật ký; mã nguồn hai tệp hệ không có câu SQL sửa/xoá bảng nhật ký."""
    nguon = Path(M.__file__).read_text(encoding="utf-8")
    nguon_web = (Path(M.__file__).parent / "nhap_lieu_cuc_bo_web.py").read_text(encoding="utf-8")
    for van in (nguon, nguon_web):
        assert not M.re.search(r"DELETE\s+FROM\s+nhat_ky|UPDATE\s+nhat_ky\s+SET", van, M.re.I)
    lenh = M.re.findall(r'sub\.add_parser\("([a-z-]+)"', nguon)
    assert "kiem-nhat-ky" in lenh and len(lenh) >= 10
    assert not [x for x in lenh if x.startswith(("xoa", "sua", "lam-lai"))]
    with pytest.raises(SystemExit):
        M.main(["xoa-nhat-ky", "--study", STUDY])


# ───────────────────────────── nhập kép ─────────────────────────────


def test_nhap_kep_doc_lap_hai_nguoi(kho, phien):
    """YC-10: người lượt 2 không xem/ghi được lượt 1 (kể cả phiếu chưa ai nhập lượt 1), không thấy giá trị lượt 1."""
    n1, n2 = phien["n1"], phien["n2"]
    kho.tao_phieu(n1, "BN-001")
    with pytest.raises(M.TuChoi, match="nhập kép phải độc lập"):
        kho.luu_bieu_mau(n2, "BN-001", "lan1", "sang_loc", {"tuoi": "40"})
    kho.luu_bieu_mau(n1, "BN-001", "lan1", "sang_loc", {"tuoi": "45"})
    with pytest.raises(M.TuChoi):
        kho.xem_bieu_mau(n2, "BN-001", "lan1", "sang_loc")
    kq = kho.xem_bieu_mau(n2, "BN-001", "lan2", "sang_loc")
    assert kq.da_luu == {} and kq.gia_tri["tuoi"] == ""
    assert "45" not in json.dumps(kho.danh_sach_phieu())
    with pytest.raises(M.TuChoi, match="quan_ly_du_lieu"):
        kho.doi_chieu(n2, "BN-001")


def test_doi_chieu_giai_quyet_lech_co_ly_do_tham_chieu(kho, phien):
    """YC-11: ô lệch giải quyết theo phiếu gốc có lý do + tham chiếu; báo cáo tỷ lệ lệch theo biến không giá trị."""
    rid = _phieu_doi_chieu_xong(kho, phien, hang2={"ha_tam_thu": "139", "ghi_chu": "tái khám trễ"})
    tt = kho.trang_thai_doi_chieu(rid)
    assert {x["cot"] for x in tt["lech"]} == {"ha_tam_thu", "ghi_chu"} and tt["con_lech"] == 2
    with pytest.raises(M.TuChoi, match="tham chiếu"):
        kho.giai_quyet_lech(phien["ql"], rid, "ha_tam_thu", "130", "đối chiếu phiếu gốc", "")
    kho.giai_quyet_lech(phien["ql"], rid, "ha_tam_thu", "130", "lượt 2 gõ nhầm", "phiếu giấy BN-001 trang 2")
    kho.giai_quyet_lech(phien["ql"], rid, "ghi_chu", "tái khám đúng hẹn", "lượt 2 đọc nhầm", "phiếu giấy trang 2")
    assert kho.trang_thai_doi_chieu(rid)["con_lech"] == 0
    assert kho.gia_tri_chot(phien["ql"], rid)["ha_tam_thu"] == "130"
    bc = kho.bao_cao_lech()
    assert bc["so_o_lech"] == 2 and bc["so_o_lech_da_giai_quyet"] == 2 and bc["trang_thai"] == "DA_GIAI_QUYET_HET"
    assert bc["lech_theo_bien"] == {"ha_tam_thu": {"so_o": 1, "so_lech": 1}, "ghi_chu": {"so_o": 1, "so_lech": 1}}
    p = kho.ghi_bao_cao_lech()
    van = p.read_text(encoding="utf-8")
    assert "139" not in van and "tái khám" not in van and rid not in van
    with pytest.raises(M.TuChoi):
        kho.luu_bieu_mau(phien["n1"], rid, "lan1", "sang_loc", {"tuoi": "46"}, {"tuoi": "sửa"})  # lượt đã đóng băng


def test_cung_nguoi_khong_nhap_hai_luot(kho, phien):
    """YC-10: hai lượt cùng một người ⇒ không đối chiếu được (độc lập)."""
    ql = phien["ql"]
    kho.them_nguoi(ql, "NV5", "nhap_lieu_2")
    rid = kho.tao_phieu(phien["n1"], "BN-001")
    _nhap_luot(kho, phien["n1"], rid, "lan1", HANG_MAU)
    with sqlite3.connect(kho.duong_dan) as cn:  # cả hai lượt thuộc một mã — chỉ tạo được bằng sửa thẳng
        cn.execute("INSERT INTO luot(record_id, lan, nguoi, xong) VALUES ('BN-001', 'lan2', 'NV1', 1)")
    with pytest.raises(M.TuChoi, match="cùng một người"):
        kho.doi_chieu(ql, rid)


# ───────────────────────────── truy vấn + khoá ─────────────────────────────


def test_truy_van_tu_dong_tay_mo_tra_loi_dong(kho, phien):
    """YC-12: luật DQ/khoảng sinh truy vấn tự động; truy vấn tay; trả lời; đóng; sửa giá trị ⇒ tự đóng có lý do."""
    ql = phien["ql"]
    rid = _phieu_doi_chieu_xong(kho, phien, hang={"ha_tam_thu": "200"})
    assert kho.quet_truy_van(ql)["tao"] == 1
    q = kho.danh_sach_truy_van(rid, chi_mo=True)
    assert [(x["ma"], x["cot"], x["nguon"]) for x in q] == [("luat_DQ01", "ha_tam_thu", "tu_dong")]
    qid = kho.tao_truy_van(ql, rid, "tuoi", "tuổi trên phiếu có tẩy xoá — kiểm lại")
    kho.tra_loi_truy_van(phien["n1"], qid, "đã xem phiếu gốc: 45 tuổi")
    with pytest.raises(M.TuChoi, match="quan_ly_du_lieu"):
        kho.dong_truy_van(phien["n1"], qid, "đóng")
    kho.dong_truy_van(ql, qid, "xác nhận đúng theo phiếu gốc")
    kho.sua_chot(ql, rid, "ha_tam_thu", "120", "trả lời truy vấn: phiếu ghi 120", "phiếu giấy trang 2")
    assert kho.quet_truy_van(ql)["dong"] == 1
    assert kho.danh_sach_truy_van(rid, chi_mo=True) == []
    with sqlite3.connect(kho.duong_dan) as cn:
        hd = [r[0] for r in cn.execute("SELECT hanh_dong FROM nhat_ky WHERE tham_chieu LIKE 'truy_van#%'")]
    assert hd.count("TAO_TRUY_VAN") == 2 and "TRA_LOI_TRUY_VAN" in hd and hd.count("DONG_TRUY_VAN") == 2
    assert kho.kiem_nhat_ky()["dat"]


def test_khoa_chi_quan_ly_sau_doi_chieu_het_truy_van(kho, phien):
    """YC-13: chỉ quản lý dữ liệu khoá; còn lượt/ô lệch/truy vấn mở ⇒ từ chối; mở khoá đòi lý do; khoá chặn sửa."""
    ql = phien["ql"]
    kho.tao_phieu(phien["n1"], "BN-009")
    with pytest.raises(M.TuChoi, match="đối chiếu"):
        kho.khoa_phieu(ql, "BN-009")
    rid = _phieu_doi_chieu_xong(kho, phien, hang={"ha_tam_thu": "200"})
    with pytest.raises(M.TuChoi, match="quan_ly_du_lieu"):
        kho.khoa_phieu(phien["n1"], rid)
    with pytest.raises(M.TuChoi, match="truy vấn chưa đóng"):
        kho.khoa_phieu(ql, rid)
    for q in kho.danh_sach_truy_van(rid, chi_mo=True):
        kho.dong_truy_van(ql, q["id"], "xác nhận đúng theo phiếu gốc (HA 200)")
    kho.khoa_phieu(ql, rid)
    with pytest.raises(M.TuChoi, match="KHOÁ"):
        kho.sua_chot(ql, rid, "tuoi", "46", "sửa thử")
    with pytest.raises(M.TuChoi, match="lý do"):
        kho.mo_khoa_phieu(ql, rid, "")
    kho.mo_khoa_phieu(ql, rid, "cần sửa tuổi theo phiếu gốc")
    kho.sua_chot(ql, rid, "tuoi", "46", "phiếu gốc ghi 46")
    assert kho.kiem_nhat_ky()["dat"]


# ───────────────────────────── xuất ─────────────────────────────


def test_xuat_chi_khi_khoa_het_hoac_ban_nhap(kho, phien, tmp_path):
    """YC-14: còn phiếu chưa khoá ⇒ từ chối; bản nháp gắn nhãn NHÁP và không qua cổng; thư mục trong repo ⇒ từ chối."""
    ql = phien["ql"]
    rid = _phieu_doi_chieu_xong(kho, phien)
    with pytest.raises(M.TuChoi, match="CHƯA KHOÁ"):
        kho.xuat(ql, tmp_path / "xuat")
    kq = kho.xuat(ql, tmp_path / "xuat", ban_nhap=True)
    assert kq["csv"].name.endswith("_BAN_NHAP.csv") and kq["bang_chung"].name.endswith("_BAN_NHAP.json")
    assert json.loads(kq["bang_chung"].read_text(encoding="utf-8"))["ban_nhap"] is True
    with pytest.raises(M.TuChoi, match="NHÁP"):
        kho.xuat(ql, tmp_path / "xuat", ban_nhap=True, tiep_nhan=True)
    kho.quet_truy_van(ql)
    kho.khoa_phieu(ql, rid)
    with pytest.raises(M.TuChoi, match="repo git"):
        kho.xuat(ql, M.BASE / "exports" / "khong_duoc")
    with pytest.raises(M.TuChoi, match="quan_ly_du_lieu"):
        kho.xuat(phien["n1"], tmp_path / "xuat")


def test_xuat_khuon_redcap_thu_tu_cot_checkbox_ma_thieu(kho, phien, tmp_path):
    """YC-14, YC-15, YC-16: thứ tự cột từ điển, cột <trường>___<mã>, mã thiếu, UTF-8; tự kiểm; tóm tắt không giá trị."""
    ql = phien["ql"]
    rid = _phieu_doi_chieu_xong(kho, phien, hang={"gioi": "BTR", "ghi_chu": "bệnh nhân hẹn tái khám"})
    kho.quet_truy_van(ql)
    kho.khoa_phieu(ql, rid)
    kq = kho.xuat(ql, tmp_path / "xuat")
    raw = kq["csv"].read_bytes()
    raw.decode("utf-8")
    with open(kq["csv"], encoding="utf-8", newline="") as f:
        dong = list(csv.reader(f))
    assert dong[0] == [c.ten for c in kho.kh.cot]
    assert dong[0][:4] == ["record_id", "tc_dien_thoai", "tuoi", "gioi"]
    assert ["benh_kem___1", "benh_kem___2", "benh_kem___3"] == [x for x in dong[0] if x.startswith("benh_kem")]
    assert "ho_ten" not in dong[0] and "du_tieu_chuan" not in dong[0]
    hang = dict(zip(dong[0], dong[1]))
    assert hang["gioi"] == "BTR" and hang["benh_kem___1"] == "1" and hang["ghi_chu"] == "bệnh nhân hẹn tái khám"
    assert set(kq["tu_kiem_doc_bang"]) >= {"csv", "bộ làm sạch", "pandas"}
    tom = kq["bang_chung"].read_text(encoding="utf-8")
    assert kq["bang_chung"].parent == SP.thu_muc_de_tai(STUDY) / "nhap_lieu"
    for gia in (rid, "bệnh nhân hẹn", "NV1", "QL01", str(kho.thu_muc)):
        assert gia not in tom, gia
    t = json.loads(tom)
    assert t["csv"]["sha256"] == M._sha256_tep(kq["csv"])
    assert t["nhat_ky"]["dau_chuoi"]["hash"] == kho.dau_chuoi()["hash"]
    assert t["dau_van_tay_kho"] == kho.kh.dau_van_tay and t["truy_van"]["mo"] == 0
    kho.tep_neo.write_text("", encoding="utf-8", newline="\n")  # mất neo cạnh kho ⇒ không chứng minh được ⇒ ĐỎ
    assert not kho.kiem_nhat_ky()["dat"]


# ───────────────────────────── đầu–cuối ─────────────────────────────


def test_dau_cuoi_mo_phong_nhap_kep_khoa_xuat_qua_cong_tiep_nhan(kho, phien, tmp_path, de_tai):
    """YC-17, YC-15, YC-11, YC-12: dữ liệu mô phỏng ĐÚNG từ điển (sinh_du_lieu_redcap) nhập hai lượt, cài ô lệch,
    giải quyết theo phiếu gốc, đóng truy vấn, khoá, xuất, qua cổng tiếp nhận import_real_dataset, khớp từng ô."""
    ql, n1, n2 = phien["ql"], phien["n1"], phien["n2"]
    td_rows = SDR.doc_tu_dien(de_tai / f"G5_REDCap_dictionary_{STUDY}.csv")
    sinh = SDR.sinh(td_rows, 12, HINH_MAU, seed=20261123)
    lech_cai = {"GL-002": {"ha_tam_thu": "+7"}, "GL-005": {"gioi": "doi"}, "GL-009": {"ghi_chu": "chép lệch"}}
    for h in sinh:
        rid = h["record_id"]
        kho.tao_phieu(n1, rid)
        _nhap_luot(kho, n1, rid, "lan1", h)
        h2 = dict(h)
        for cot, cach in lech_cai.get(rid, {}).items():
            if cach == "+7":
                h2[cot] = int(h[cot]) + 7
            elif cach == "doi":
                h2[cot] = 2 if str(h[cot]) == "1" else 1
            else:
                h2[cot] = cach
        _nhap_luot(kho, n2, rid, "lan2", h2)
    so_lech = 0
    for h in sinh:
        tt = kho.doi_chieu(ql, h["record_id"])
        for x in tt["lech"]:
            so_lech += 1
            kho.giai_quyet_lech(ql, h["record_id"], x["cot"], SDR._chuoi(h.get(x["cot"])),
                                "lượt 2 gõ lệch phiếu gốc", f"phiếu giấy {h['record_id']}")  # fmt: skip
    assert so_lech == 3
    kho.quet_truy_van(ql)
    for q in kho.danh_sach_truy_van(chi_mo=True):
        kho.tra_loi_truy_van(n1, q["id"], "đã đối chiếu phiếu gốc: đúng như phiếu")
        kho.dong_truy_van(ql, q["id"], "xác nhận đúng theo phiếu gốc")
    for h in sinh:
        kho.khoa_phieu(ql, h["record_id"])
    kq = kho.xuat(ql, tmp_path / "xuat", tiep_nhan=True, exports_root=SP.EXPORTS)
    man = kq["tiep_nhan"]
    assert man["status"] == "READY_FOR_CLEANING_NOT_LOCKED", man["pii_scan"]
    assert man["row_count"] == 12 and man["column_count"] == len(kho.kh.cot)
    with open(kq["csv"], encoding="utf-8", newline="") as f:
        xuat = {r["record_id"]: r for r in csv.DictReader(f)}
    for h in sinh:
        for c in kho.kh.cot:
            mong = SDR._chuoi(h.get(c.ten))
            if c.kieu == "hop" and mong == "":
                mong = "0"  # quy ước xuất REDCap: ô chọn nhiều không chọn (kể cả câu bị ẩn) = 0
            assert xuat[h["record_id"]][c.ten] == mong, (h["record_id"], c.ten)
    bc = json.loads(kq["bang_chung"].read_text(encoding="utf-8"))
    assert bc["nhap_kep"]["so_o_lech"] == 3 and bc["nhap_kep"]["trang_thai"] == "DA_GIAI_QUYET_HET"
    assert bc["so_phieu_khoa"] == 12 and bc["nhat_ky"]["kiem_chuoi"] == "KHOP"
    assert kho.kiem_nhat_ky()["dat"]


def test_phieu_nham_ma_loai_khoi_xuat_khong_xoa(kho, phien, tmp_path):
    """YC-14: phiếu tạo nhầm mã ⇒ đánh dấu (kèm lý do), loại khỏi xuất/khoá, KHÔNG xoá dữ liệu/nhật ký."""
    ql = phien["ql"]
    rid = _phieu_doi_chieu_xong(kho, phien)
    kho.tao_phieu(phien["n1"], "BN-0O1")
    with pytest.raises(M.TuChoi, match="lý do"):
        kho.danh_dau_nham(ql, "BN-0O1", "")
    kho.danh_dau_nham(ql, "BN-0O1", "gõ nhầm chữ O thay số 0")
    kho.quet_truy_van(ql)
    kho.khoa_phieu(ql, rid)
    kq = kho.xuat(ql, tmp_path / "xuat")
    assert kq["so_phieu"] == 1
    assert kho.trang_thai()["so_phieu_nham_ma"] == 1 and kho.kiem_nhat_ky()["dat"]


# ───────────────────────────── sao lưu + hồ sơ thẩm định ─────────────────────────────


def test_sao_luu_kiem_ban_sao(kho, phien, tmp_path):
    """YC-19: sao lưu bằng API backup của SQLite + tệp neo; bản sao kiểm chuỗi KHỚP; đích trong đám mây bị từ chối."""
    _phieu_doi_chieu_xong(kho, phien)
    kq = kho.sao_luu(phien["ql"], tmp_path / "o_ngoai")
    assert kq["kiem"]["dat"] and kq["tep"].exists()
    with pytest.raises(M.TuChoi, match="ĐỒNG BỘ"):
        kho.sao_luu(phien["ql"], tmp_path / "OneDrive" / "sao_luu")
    assert kho.kiem_nhat_ky()["dat"]


def test_ho_so_tham_dinh_truy_vet_du_yeu_cau(tmp_path):
    """YC-18: mọi yêu cầu có ≥ 1 test; hồ sơ ghi commit/phiên bản, giới hạn, đối chiếu ICH/ALCOA+ không bịa số mục."""
    tv = M.truy_vet_test()
    thieu = [ma for ma, ds in tv.items() if not ds]
    assert not thieu, f"yêu cầu chưa có test: {thieu}"
    ju = tmp_path / "ket_qua.xml"
    ca = "".join(f'<testcase classname="tests.{t.split("::")[0][:-3]}" name="{t.split("::")[1]}"/>'
                 for ds in tv.values() for t in ds)  # fmt: skip
    ju.write_text(f'<testsuites><testsuite name="pytest">{ca}</testsuite></testsuites>', encoding="utf-8",
                  newline="\n")  # fmt: skip
    kq = M.ho_so_tham_dinh(tmp_path / "ra", junit=ju)
    assert kq["trang_thai"] == "DAT" and kq["moi_truong"]["python"]
    md = kq["md"].read_text(encoding="utf-8")
    assert "Ma trận truy vết" in md and "ICH E6(R3)" in md and "ALCOA+" in md and "Giới hạn" in md
    assert not M.re.search(r"E6\(R3\)[^|\n]{0,40}\b\d+\.\d+", md), "không ghi số mục khi chưa đối chiếu nguyên văn"
    assert str(Path.home()) not in md
    ju.write_text(ju.read_text(encoding="utf-8").replace("/>", "><failure/></testcase>", 1), encoding="utf-8",
                  newline="\n")  # fmt: skip
    assert M.ho_so_tham_dinh(tmp_path / "ra", junit=ju)["trang_thai"] == "CHUA_DAT"
