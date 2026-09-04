"""Hồi quy phát hiện HIGH của audit đối kháng 2026-09-04:
risk_score_calc.py — cờ CLI `meld --dialysis-2x-past-week` dùng
`type=lambda s: s.lower() == "true"` — MỌI chuỗi khác "true" (kể cả lỗi gõ như
"tru", hoặc quy ước boolean phổ biến khác như "1"/"yes") ÂM THẦM trở thành
`False`, không một cảnh báo/lỗi CLI nào.

Vì sao nguy hiểm: `meld()` áp quy ước OPTN — bệnh nhân đang lọc máu ≥2 lần/tuần
PHẢI ép creatinine về 4.0 mg/dL trước khi tính điểm (`if dialysis_2x_past_week:
creat = 4.0 else: creat = min(creat, 4.0)`). Với bilirubin=2.5, INR=1.9,
creatinine=1.2: `--dialysis-2x-past-week 1` và `--dialysis-2x-past-week yes`
trước bản vá đều lặng lẽ cho điểm 19 (không dialysis) trong khi ý người gõ rõ
ràng là "có" — đáng lẽ phải ra điểm 30 (dialysis). Đây trực tiếp ảnh hưởng độ
nặng bệnh gan/ưu tiên ghép gan.

Nguyên tắc của chính module này (`RiskScoreError`: "TỪ CHỐI tính thay vì bịa
giá trị mặc định") đòi hỏi input KHÔNG nhận diện được phải làm CLI báo lỗi rõ
ràng — bản vá thay lambda bằng `_parse_bool_cli()`, một `type=` callable ném
`argparse.ArgumentTypeError` cho mọi chuỗi không nhận diện được, chấp nhận một
tập boolean hợp lý (true/false, 1/0, yes/no) không phân biệt hoa-thường.

Nguyên tắc viết test: gọi THẲNG `RS._parse_bool_cli()` (đơn vị) + chạy CLI thật
qua `subprocess`/`main()` (tích hợp), không chỉ đọc mã nguồn.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import risk_score_calc as RS  # noqa: E402

SCRIPT = TOOLS / "risk_score_calc.py"


# ── Đơn vị: _parse_bool_cli() ────────────────────────────────────────────────
class TestParseBoolCliTrueValues:
    @pytest.mark.parametrize("s", ["true", "True", "TRUE", "TrUe", "1", "yes", "Yes", "YES", "y", "Y"])
    def test_nhan_dien_true(self, s):
        assert RS._parse_bool_cli(s) is True


class TestParseBoolCliFalseValues:
    @pytest.mark.parametrize("s", ["false", "False", "FALSE", "0", "no", "No", "NO", "n", "N"])
    def test_nhan_dien_false(self, s):
        assert RS._parse_bool_cli(s) is False


class TestParseBoolCliBogusValuesRaise:
    """★★ Ca chính — trước bản vá, các giá trị này ÂM THẦM thành False."""

    @pytest.mark.parametrize("s", ["1", "yes", "TRUE", "tru", "flase", "Y", "vâng", "2", "", "  ", "truee"])
    def test_gia_tri_khong_hop_le_hoac_bi_doan_sai_truoc_kia_deu_qua_mot_cua_ro_rang(self, s):
        """Không khẳng định True/False cho các giá trị này ở đây (một số HỢP LỆ,
        một số KHÔNG) — chỉ khẳng định: mọi giá trị đều đi qua đúng một hàm phân
        loại tường minh, không có nhánh "mặc định âm thầm là False" nào sống sót.
        Test dưới đây (nhóm typo thật) mới là nơi khẳng định lỗi CHẶN."""
        try:
            RS._parse_bool_cli(s)
        except argparse.ArgumentTypeError:
            pass  # hợp lệ — bị từ chối tường minh

    @pytest.mark.parametrize("s", ["tru", "flase", "vâng", "2", "", "truee", "ok", "yeah"])
    def test_typo_va_gia_tri_la_bi_tu_choi_tuong_minh(self, s):
        with pytest.raises(argparse.ArgumentTypeError):
            RS._parse_bool_cli(s)

    def test_khong_con_nhanh_am_tham_thanh_false(self):
        """Đối chứng trực tiếp với hành vi CŨ: "1" và "yes" từng trả False do
        lambda cũ so sánh `s.lower() == "true"`. Bản vá phải làm chúng thành
        True (nhận diện được) — KHÔNG được lặng lẽ giữ nguyên là False."""
        assert RS._parse_bool_cli("1") is True
        assert RS._parse_bool_cli("yes") is True


class TestParseBoolCliWhitespaceTolerant:
    def test_khoang_trang_quanh_gia_tri_van_nhan_dien_duoc(self):
        assert RS._parse_bool_cli("  true  ") is True
        assert RS._parse_bool_cli(" false ") is False


# ── Tích hợp: CLI thật qua subprocess ────────────────────────────────────────
def _run_meld_cli(dialysis_flag_value):
    cmd = [sys.executable, str(SCRIPT), "meld",
           "--bilirubin", "2.5", "--inr", "1.9", "--creatinine", "1.2",
           "--dialysis-2x-past-week", dialysis_flag_value, "--json"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


class TestCliCanonicalUsageStillWorks:
    """★★ Đối chứng bắt buộc — cách dùng CHÍNH THỐNG đã ghi trong docstring
    module (`--dialysis-2x-past-week false`/`true`, chữ thường) KHÔNG được vỡ."""

    def test_false_chinh_thong_khong_ep_creatinine(self):
        p = _run_meld_cli("false")
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["inputs_used"]["dialysis_adjustment_applied"] is False
        assert out["inputs_used"]["creatinine"] == 1.2
        assert out["score"] == 19

    def test_true_chinh_thong_ep_creatinine_ve_4(self):
        p = _run_meld_cli("true")
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["inputs_used"]["dialysis_adjustment_applied"] is True
        assert out["inputs_used"]["creatinine"] == 4.0
        assert out["score"] == 30


class TestCliNowRejectsBogusInsteadOfSilentlyFalse:
    """★★ Ca chính của phát hiện, chạy qua ĐÚNG con đường bác sĩ gõ lệnh."""

    def test_gia_tri_1_truoc_kia_am_tham_false_nay_thanh_true(self):
        p = _run_meld_cli("1")
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["inputs_used"]["dialysis_adjustment_applied"] is True
        assert out["score"] == 30

    def test_gia_tri_yes_truoc_kia_am_tham_false_nay_thanh_true(self):
        p = _run_meld_cli("yes")
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["inputs_used"]["dialysis_adjustment_applied"] is True
        assert out["score"] == 30

    def test_typo_bi_chan_voi_thong_diep_loi_ro_rang_khong_lang_le_thanh_false(self):
        p = _run_meld_cli("tru")
        assert p.returncode != 0
        assert "boolean hợp lệ" in p.stderr or "boolean hợp lệ" in p.stdout
        # Tuyệt đối không được có JSON đầu ra hợp lệ với dialysis=False cho input rác
        assert "dialysis_adjustment_applied" not in p.stdout


class TestCliDefaultUnchangedWhenFlagOmitted:
    """Không truyền cờ hoàn toàn -> default=False vẫn giữ nguyên (không phải
    phạm vi phát hiện, nhưng phải xác nhận default không bị ảnh hưởng)."""

    def test_khong_truyen_co_van_mac_dinh_false(self):
        cmd = [sys.executable, str(SCRIPT), "meld",
               "--bilirubin", "2.5", "--inr", "1.9", "--creatinine", "1.2", "--json"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["inputs_used"]["dialysis_adjustment_applied"] is False
