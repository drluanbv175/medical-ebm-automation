"""Hồi quy cổng G6 (2026-07-29) — 3 lỗi tìm được khi soi cổng G6.

F1 (HIGH) — `run_stats_analysis.py` KHÔNG dùng bộ giải mã thiết kế dùng chung
    `gate_contract.resolve_design_code()`, mà đọc THẲNG `G1_checkpoint.json`.
    Bộ giải đó ra đời đúng vì lỗi "`--design` bác sĩ truyền TƯỜNG MINH ở G2 bị nuốt"
    (vá 2026-07-27) và đã được nối vào run_g3/g4/g6_auto.py — sót đúng file này.
    Đây là file NGUY HIỂM NHẤT để sót: 3 file kia chỉ SINH TEMPLATE, còn file này
    CHẠY THẬT trên dữ liệu đã khóa.

F2 (MEDIUM-HIGH) — Bảng 1 của MỌI thiết kế đều phân tầng theo phơi nhiễm.
    Sai rõ nhất ở bệnh-chứng (lấy mẫu THEO KẾT CỤC → phải trình bày riêng ca/chứng;
    STROBE mục 14a dấu *) và ở nghiên cứu độ chính xác chẩn đoán (trục là KẾT QUẢ
    TIÊU CHUẨN THAM CHIẾU; STARD mục 20 + 21a + 21b).

F3 (MEDIUM) — Bảng 1 của RCT chào sẵn `add_p()` cho đặc điểm nền, mâu thuẫn với
    chính SAP §3 mà G1 sinh ra ("RCT: mô tả cân bằng nền, không kiểm định ý nghĩa
    khác biệt baseline") — mâu thuẫn nội tại giữa hai cổng cùng hệ.

Cách kiểm: soi HÀNH VI SINH RA / GIẢI RA, không kiểm sự tồn tại của hàm — vì cả ba
lỗi đều thuộc kiểu "hàm có tồn tại nhưng trả về thứ sai".
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO), str(_REPO / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402
import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "phoi_nhiem",
    "outcome": "ket_cuc",
    "time_col": "thoi_gian",
    "covariates": ["tuoi", "gioi"],
    "all_vars": ["ma_bn", "tuoi", "gioi", "phoi_nhiem", "ket_cuc", "thoi_gian"],
    "detection_log": [],
}

CANONICAL = [
    "rct", "cohort", "case_control", "cross_sectional",
    "diagnostic", "sr_ma", "prediction", "qualitative",
]


def _group_by(code: str) -> str | None:
    m = re.findall(r'by\s*=\s*"([^"]+)"', G6.make_r02_tables(_V, code))
    return m[0] if m else None


def _offers_baseline_pvalue(code: str) -> bool:
    text = G6.make_r02_tables(_V, code)
    return "gtsummary::add_p(" in text


# ── F2 ───────────────────────────────────────────────────────────────────────
class TestBang1PhanTangTheoTrucLayMauCuaThietKe:
    def test_benh_chung_phan_tang_theo_ca_chung_khong_theo_phoi_nhiem(self):
        """STROBE mục 14a (dấu *): bệnh-chứng trình bày RIÊNG theo ca và chứng."""
        assert _group_by("case_control") == _V["outcome"], (
            "bệnh-chứng lấy mẫu THEO KẾT CỤC — Bảng 1 phải phân tầng theo ca/chứng, "
            "không theo phơi nhiễm (phơi nhiễm là biến đem SO)"
        )

    def test_chan_doan_phan_tang_theo_tieu_chuan_tham_chieu(self):
        """STARD mục 20 + 21a + 21b: chia theo có/không có bệnh đích."""
        assert _group_by("diagnostic") == _V["outcome"]

    def test_thiet_ke_lay_mau_theo_phoi_nhiem_van_giu_nguyen(self):
        """Không sửa quá tay: thuần tập/cắt ngang/RCT vẫn phân tầng theo phơi nhiễm."""
        for code in ("rct", "cohort", "cross_sectional"):
            assert _group_by(code) == _V["exposure"], code

    def test_caption_noi_ro_truc_phan_tang(self):
        cc = G6.make_r02_tables(_V, "case_control")
        assert "CA VÀ CHỨNG" in cc.upper()
        dx = G6.make_r02_tables(_V, "diagnostic")
        assert "tiêu chuẩn tham chiếu" in dx

    def test_dong_message_song_bao_dung_bien_nhom(self):
        """Dòng message() là dòng SỐNG (không bị chú thích) — nó phải báo đúng biến."""
        for code in ("case_control", "diagnostic"):
            live = [
                line for line in G6.make_r02_tables(_V, code).splitlines()
                if line.strip().startswith("message(")
            ]
            assert live, f"{code}: không tìm thấy dòng message()"
            assert _V["outcome"] in live[0], (
                f"{code}: dòng message() sống vẫn báo sai biến nhóm"
            )


# ── F3 ───────────────────────────────────────────────────────────────────────
class TestRctKhongKiemDinhYNghiaKhacBietNen:
    def test_rct_khong_chao_san_add_p_cho_bang_1(self):
        assert not _offers_baseline_pvalue("rct"), (
            "khác biệt nền trong thử nghiệm ngẫu nhiên là do NGẪU NHIÊN — p-value ở đây "
            "không trả lời câu hỏi nào; mâu thuẫn với SAP §3 do G1 sinh"
        )

    def test_rct_van_giu_smd_de_mo_ta_mat_can_bang(self):
        assert "add_smd()" in G6.make_r02_tables(_V, "rct")

    def test_rct_giai_thich_ly_do_thay_vi_lang_le_bo(self):
        """Bỏ im lặng thì người đọc tưởng quên — phải nêu lý do ngay trong file sinh ra."""
        text = G6.make_r02_tables(_V, "rct")
        assert "KHÔNG add_p()" in text
        assert "SAP §3" in text

    def test_thiet_ke_quan_sat_van_duoc_phep_kiem_dinh_nen(self):
        """Không nới rộng lệnh cấm sang thiết kế quan sát — ở đó so sánh nền có nghĩa."""
        for code in ("cohort", "cross_sectional", "case_control"):
            assert _offers_baseline_pvalue(code), code


# ── F1 ───────────────────────────────────────────────────────────────────────
class TestMaThietKeTuG2KhongBiEngineChayThatBoQua:
    """`--design` truyền TƯỜNG MINH ở G2 phải thắng suy luận tự động của G1."""

    def _study(self, tmp_path: Path, g1: dict | None, g2: dict | None) -> Path:
        d = tmp_path / "exports" / "S"
        d.mkdir(parents=True)
        if g1 is not None:
            (d / "G1_checkpoint.json").write_text(json.dumps(g1), encoding="utf-8")
        if g2 is not None:
            (d / "G2_checkpoint.json").write_text(json.dumps(g2), encoding="utf-8")
        return d

    def test_g2_thang_g1_khi_hai_ben_lech(self, tmp_path):
        d = self._study(
            tmp_path,
            {"design": {"internal_code": "cohort"}},
            {"design_code": "case_control"},
        )
        code, warn = GC.resolve_design_code(d, default="cohort")
        assert code == "case_control", (
            "bác sĩ đã sửa thiết kế ở G2 mà engine chạy thật vẫn dùng suy luận sai của G1"
        )
        assert warn and "LỆCH" in warn.upper(), "lệch thiết kế phải được nói ra, không im lặng"

    def test_khong_co_g2_thi_giu_nguyen_hanh_vi_cu(self, tmp_path):
        """Chống hồi quy: khóa `design_code` cấp cao nhất của G1 vẫn phải được tôn trọng."""
        d = self._study(tmp_path, {"design_code": "diagnostic"}, None)
        g1 = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))
        cu = g1.get("design_code") or (g1.get("design") or {}).get("internal_code")
        moi, _ = GC.resolve_design_code(d, default=cu or "cohort")
        assert moi == cu == "diagnostic"

    def test_engine_chay_that_da_noi_vao_bo_giai_dung_chung(self):
        """Kiểm bằng mã nguồn: file chạy dữ liệu thật phải gọi resolve_design_code."""
        src = (_REPO / "tools" / "run_stats_analysis.py").read_text(encoding="utf-8")
        assert "GC.resolve_design_code(" in src, (
            "run_stats_analysis.py là file DUY NHẤT chạy thật trên dữ liệu đã khóa — "
            "không được đọc thẳng G1_checkpoint.json"
        )

    @pytest.mark.parametrize(
        "path", ["run_g3_auto.py", "run_g4_auto.py", "run_g6_auto.py", "run_stats_analysis.py"]
    )
    def test_moi_cong_ha_nguon_deu_dung_chung_mot_bo_giai(self, path):
        """Chống tái diễn 'vá 3 nơi sót nơi thứ 4'."""
        src = (_REPO / "tools" / path).read_text(encoding="utf-8")
        assert "resolve_design_code(" in src, f"{path} chưa nối vào bộ giải dùng chung"
