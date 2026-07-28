"""Hồi quy: artifact G1 phải RIÊNG theo thiết kế, không dùng chung khuôn RCT.

BỐI CẢNH (2026-07-28)
--------------------
`generate_g1_artifact()` từng sinh 4 khối GIỐNG HỆT nhau ở cả 8 mã thiết kế canonical:
PHẦN 4 "KHỐI THIẾT KẾ" (dán thẳng vào đề cương nộp Hội đồng Đạo đức), SAP §11 dummy
tables ("Nhóm A/Nhóm B/p"), SAP §12 ("α 0.05 / Power 80%"), cộng một tham chiếu TREO
("xem §Estimand bên trên" trong khi khối estimand chỉ sinh cho RCT).

Vi phạm quy tắc 6 của `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`: "câu hỏi ↔ thiết kế ↔ cỡ mẫu ↔
bộ biến/CRF ↔ SAP ↔ dummy tables phải KHỚP nhau. Mâu thuẫn nội tại → 🔴".

Bộ test này khóa lại bằng cách kiểm HÀNH VI SINH RA (render thật rồi soi văn bản), không
kiểm sự tồn tại của hàm — vì lỗi cũ chính là kiểu "hàm có tồn tại nhưng trả về cùng một
thứ cho mọi thiết kế".
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO), str(_REPO / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_design_blocks as G1D  # noqa: E402
import run_g1_auto as G1  # noqa: E402

CANONICAL = [
    "rct",
    "cohort",
    "case_control",
    "cross_sectional",
    "diagnostic",
    "sr_ma",
    "prediction",
    "qualitative",
]


def _artifact(code: str) -> str:
    design = G1._apply_design_pin(
        G1.infer_study_design("treatment", {}, "chu de kiem thu"), code
    )
    return G1.generate_g1_artifact(
        "chu de kiem thu", "TEST-STUDY", "treatment", design, [], {}, "2026-07-28 10:00"
    )


@pytest.fixture(scope="module")
def artifacts() -> dict[str, str]:
    return {code: _artifact(code) for code in CANONICAL}


def _slice(text: str, start: str, end: str) -> str:
    i = text.find(start)
    assert i >= 0, f"không tìm thấy mốc {start!r} trong artifact"
    j = text.find(end, i + len(start))
    return text[i:j] if j > 0 else text[i:]


_DESIGN_BLOCK_BOUNDS = (
    "KHỐI THIẾT KẾ — TEST-STUDY",
    "═══════════════════════════════════════════════════════════════\n```",
)
_SAP11_BOUNDS = ("### SAP §11", "### SAP §12")
_SAP12_BOUNDS = ("### SAP §12", "\n---")


class TestKhoiTheoThietKeKhongConDungChung:
    """8 mã thiết kế phải cho 8 khối thiết kế và 8 bộ dummy tables khác nhau."""

    def test_khoi_thiet_ke_khac_nhau_o_moi_thiet_ke(self, artifacts):
        seen: dict[str, str] = {}
        for code, text in artifacts.items():
            digest = hashlib.sha256(
                _slice(text, *_DESIGN_BLOCK_BOUNDS).encode("utf-8")
            ).hexdigest()
            assert digest not in seen, (
                f"KHỐI THIẾT KẾ của {code!r} giống hệt {seen[digest]!r} — "
                "đây chính là lỗi khuôn RCT dùng chung đã vá 2026-07-28"
            )
            seen[digest] = code

    def test_dummy_tables_khac_nhau_o_moi_thiet_ke(self, artifacts):
        seen: dict[str, str] = {}
        for code, text in artifacts.items():
            digest = hashlib.sha256(
                _slice(text, *_SAP11_BOUNDS).encode("utf-8")
            ).hexdigest()
            assert digest not in seen, (
                f"SAP §11 dummy tables của {code!r} giống hệt {seen[digest]!r}"
            )
            seen[digest] = code

    def test_sap12_khac_nhau_giua_cac_ho_thiet_ke(self, artifacts):
        """3 thiết kế quan sát dùng chung §12 là ĐÚNG (cùng giải trình STROBE mục 10);
        6 họ còn lại phải khác nhau."""
        by_family: dict[str, str] = {}
        for code, text in artifacts.items():
            fam = G1D.family_of(code)
            digest = hashlib.sha256(
                _slice(text, *_SAP12_BOUNDS).encode("utf-8")
            ).hexdigest()
            if fam in by_family:
                assert by_family[fam] == digest, (
                    f"cùng họ {fam!r} mà §12 lại khác nhau — không nhất quán"
                )
            else:
                assert digest not in by_family.values(), (
                    f"§12 của họ {fam!r} trùng với một họ khác"
                )
                by_family[fam] = digest
        assert len(by_family) == 6, "phải có đúng 6 họ thiết kế phân biệt"


class TestKhongConKhuonRctOThietKeKhongPhaiRct:
    """Các chuỗi đặc trưng RCT không được xuất hiện ở thiết kế không phải RCT."""

    # Chỉ liệt kê chuỗi thuộc KHUÔN CỨNG cũ, KHÔNG liệt kê khái niệm chung như
    # "làm mù" hay "estimand" — lượt phản biện độc lập (2026-07-28) chỉ ra rằng cấm
    # theo khái niệm sẽ báo động giả: làm mù người ĐÁNH GIÁ KẾT CỤC vẫn chính đáng
    # trong nghiên cứu quan sát, và estimand vẫn được bàn cho nghiên cứu chẩn đoán.
    CHUOI_KHUON_RCT = [
        "Nhóm A (n=",
        "Nhóm B (n=",
        "Bố trí: ☐ Song song  ☐ Bắt chéo  ☐ Factorial  ☐ Thích nghi\n",
        "Làm mù: ☐ Mở  ☐ Đơn mù  ☐ Đôi mù  ☐ Tam mù",
        "Power mục tiêu: ___%",
    ]

    @pytest.mark.parametrize("code", [c for c in CANONICAL if c != "rct"])
    def test_khong_con_chuoi_khuon_rct(self, artifacts, code):
        con_sot = [s for s in self.CHUOI_KHUON_RCT if s in artifacts[code]]
        assert not con_sot, f"thiết kế {code!r} vẫn còn khuôn RCT: {con_sot}"


class TestThamChieuEstimandKhongTreo:
    """Khối thiết kế chỉ được trỏ tới §Estimand khi khối đó THỰC SỰ được sinh."""

    @pytest.mark.parametrize("code", CANONICAL)
    def test_tro_va_ton_tai_phai_di_doi(self, artifacts, code):
        text = artifacts[code]
        co_tro = "xem khối ESTIMAND ở PHẦN 2b" in text
        co_khoi = "## PHẦN 2b — ESTIMAND" in text
        assert co_tro == co_khoi, (
            f"{code!r}: trỏ tới estimand={co_tro} nhưng khối tồn tại={co_khoi} "
            "— tham chiếu treo"
        )

    def test_chi_rct_co_khoi_estimand(self, artifacts):
        co = {c for c in CANONICAL if "## PHẦN 2b — ESTIMAND" in artifacts[c]}
        assert co == {"rct"}, f"kỳ vọng chỉ RCT có khối estimand, thực tế: {co}"


class TestDinhTinhKhongConThongKeSuyDien:
    """Nghiên cứu định tính không có α, power, p-value hay nhóm so sánh."""

    def test_khong_con_alpha_power_p(self, artifacts):
        text = artifacts["qualitative"]
        for probe in ("α (hai đuôi): 0.05", "Power mục tiêu", "| p |", "Nhóm A (n="):
            assert probe not in text, f"định tính vẫn còn {probe!r}"

    def test_co_tieu_chi_bao_hoa_thay_cho_co_mau(self, artifacts):
        text = artifacts["qualitative"].upper()
        assert "BÃO HÒA" in text, "định tính phải nêu tiêu chí bão hòa dữ liệu"

    def test_nhac_gioi_han_pham_vi_coreq(self, artifacts):
        """COREQ theo nhan đề gốc chỉ phủ phỏng vấn và nhóm tiêu điểm — phát hiện của
        lượt phản biện độc lập; artifact phải nói rõ để không dùng sai chuẩn."""
        assert "SRQR" in artifacts["qualitative"]


class TestSrMaLayNghienCuuLamDonViPhanTich:
    def test_noi_ro_don_vi_la_nghien_cuu(self, artifacts):
        assert "NGHIÊN CỨU (k)" in artifacts["sr_ma"]

    def test_co_bang_summary_of_findings(self, artifacts):
        assert "Summary of Findings" in artifacts["sr_ma"]

    def test_khong_ap_cong_thuc_co_mau_ca_the(self, artifacts):
        assert "Power mục tiêu" not in artifacts["sr_ma"]


class TestDiagnosticVaPrediction:
    def test_diagnostic_co_bang_cheo_2x2(self, artifacts):
        assert "BẢNG CHÉO 2×2" in artifacts["diagnostic"]

    def test_diagnostic_canh_bao_quadas_la_cong_cu_muc_tong_quan(self, artifacts):
        """Phát hiện của lượt phản biện độc lập: QUADAS-2/3 là công cụ để NGƯỜI KHÁC
        thẩm định nghiên cứu gốc, không phải công cụ tự chấm điểm cho chính mình."""
        assert "QUADAS" in artifacts["diagnostic"]
        assert "tự chấm điểm" in artifacts["diagnostic"]

    def test_prediction_co_calibration_va_dca(self, artifacts):
        text = artifacts["prediction"]
        assert "Calibration slope" in text
        assert "quyết định" in text.lower() or "decision curve" in text.lower()

    def test_prediction_khong_dung_power(self, artifacts):
        assert "Power mục tiêu" not in artifacts["prediction"]


class TestQuanSatKhongDanNhanTienCuuHoiCuu:
    """STROBE Explanation & Elaboration mục 4 khuyến cáo TRÁNH nhãn tiến cứu/hồi cứu
    làm mô tả chính vì hai nhãn này được dùng không thống nhất."""

    @pytest.mark.parametrize("code", ["cohort", "case_control", "cross_sectional"])
    def test_mo_ta_thiet_ke_theo_viec_da_lam(self, artifacts, code):
        block = _slice(artifacts[code], *_DESIGN_BLOCK_BOUNDS)
        assert "Thời điểm đo PHƠI NHIỄM" in block
        assert "[CHỌN: tiến cứu" not in block

    def test_bang_3_khac_nhau_theo_tung_thiet_ke_quan_sat(self, artifacts):
        """STROBE mục 15 có BA câu chữ khác nhau cho thuần tập / bệnh-chứng / cắt ngang."""
        assert "Tổng người-thời gian" in artifacts["cohort"]
        assert "Ca, n (%)" in artifacts["case_control"]
        assert "Tỷ lệ hiện mắc" in artifacts["cross_sectional"]


class TestBuocTiepCoMauKhopVoiHanhViThatCuaG3:
    """`run_g3_auto.py` có N_NOT_APPLICABLE_DESIGNS = {sr_ma, prediction, qualitative}.
    Khối thiết kế G1 không được bảo 3 thiết kế đó 'tính cỡ mẫu theo effect size'."""

    @pytest.mark.parametrize("code", ["sr_ma", "prediction", "qualitative"])
    def test_khong_bao_tinh_co_mau_theo_effect_size(self, artifacts, code):
        block = _slice(artifacts[code], *_DESIGN_BLOCK_BOUNDS)
        assert "sau khi xác nhận effect size" not in block, (
            f"{code!r} không tính N theo effect size — xem N_NOT_APPLICABLE_DESIGNS "
            "trong run_g3_auto.py"
        )

    @pytest.mark.parametrize("code", ["rct", "cohort", "case_control",
                                      "cross_sectional", "diagnostic"])
    def test_thiet_ke_dinh_luong_van_tro_ve_g3(self, artifacts, code):
        block = _slice(artifacts[code], *_DESIGN_BLOCK_BOUNDS)
        assert "run_g3_auto.py" in block or "SAP §12" in block


class TestApiModuleOnDinh:
    def test_moi_ma_canonical_deu_co_khoi_bang_va_sap12(self):
        for code in CANONICAL:
            assert G1D.design_block_body(code).strip()
            assert G1D.dummy_tables(code).strip()
            assert G1D.sap12_note(code).strip()
            assert G1D.sap12_title(code).strip()

    def test_ma_la_roi_ve_quan_sat_khong_vo(self):
        assert G1D.family_of("khong-ton-tai") == "observational"
        assert G1D.dummy_tables("khong-ton-tai").strip()

    def test_dummy_tables_khong_chua_so_lieu_that(self):
        """Vỏ bảng phải RỖNG — mọi ô số liệu là placeholder trong ngoặc vuông."""
        for code in CANONICAL:
            for line in G1D.dummy_tables(code).splitlines():
                if not line.startswith("|") or line.startswith("|---"):
                    continue
                for cell in line.split("|")[1:-1]:
                    cell = cell.strip()
                    # cho phép ô rỗng, placeholder [..], và chữ mô tả tiêu đề cột
                    if cell.replace(".", "").replace(",", "").isdigit():
                        pytest.fail(
                            f"{code}: dummy table chứa số liệu cứng {cell!r} — "
                            "vỏ bảng phải rỗng"
                        )
