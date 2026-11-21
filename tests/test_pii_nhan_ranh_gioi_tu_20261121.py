"""Nhãn PII khớp theo RANH GIỚI TỪ — mã băm hex không còn bị báo là PII (21/11/2026).

Đo thật: giả lập trọn vòng kịch bản cắt ngang trượt khi mã SHA-256 của báo cáo phản biện («…f95cccdadfdd…») chứa chuỗi
con «cccd» — R2 của G8 báo PII ⇒ G8 BLOCKED ⇒ G9/G10 không khoá được. Mã băm đổi mỗi lượt nên CI lúc xanh lúc đỏ. Nay
nhãn chỉ khớp khi đứng riêng (không chữ/số liền trước, liền sau); nhãn thật trong văn bản vẫn bị bắt. Ngoại tuyến.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import pii_van_ban as PV  # noqa: E402
import retry_loop as RL  # noqa: E402
import run_g0_auto as G0  # noqa: E402
import run_g8_auto as G8  # noqa: E402

BAM = "f17a19664ef95cccdadfdda54254b6323584448308de7eccddddb628a04ab151"  # mã thật của lượt trượt — chứa «cccd»
PIPE = {"rows": [{"checkpoint_exists": True}], "n_pass": 0}


@pytest.mark.parametrize("van, nhan, co", [
    (f"Hash: `{BAM}`", "cccd", False),
    ("Số CCCD: 079012345678", "cccd", True),
    ("không thu thập cccd.", "cccd", True),
    ("(CCCD)", "cccd", True),
    ("Họ tên: Nguyễn Văn A", "họ tên", True),
    ("thuhọ tênx", "họ tên", False),
    ("Ngày sinh: 01/02/1960", "ngày sinh", True),
])
def test_co_nhan(van, nhan, co):
    assert PV.co_nhan(van, nhan) is co


def _r2_g8(van: str) -> list:
    return [e for e in G8.guardrail_g8(van, PIPE)["errors"] if e.startswith("R2")]


def test_g8_ma_bam_chua_cccd_khong_phai_pii():
    assert not _r2_g8(f"**Hash SHA-256 báo cáo phản biện:** `{BAM}`\nCần bác sĩ kiểm chứng.")


def test_g8_nhan_cccd_dung_rieng_van_bi_bat():
    assert _r2_g8("Bệnh nhân CCCD 079012345678.\nCần bác sĩ kiểm chứng.")


def _r2_g0(van: str) -> list:
    loi = G0.guardrail_check_g0(van + "\n[CẦN BÁC SĨ XÁC NHẬN]\nCần bác sĩ kiểm chứng.", {"all_pmids": []})["errors"]
    return [e for e in loi if e.startswith("R2")]


def test_g0_ma_bam_chua_cccd_khong_phai_pii():
    assert not _r2_g0(f"Dấu vân tay nội dung: {BAM}.")


def test_g0_nhan_cccd_dung_rieng_van_bi_bat():
    assert _r2_g0("Người bệnh có CCCD 079012345678.")


def test_retry_loop_ma_bam_va_nhan():
    assert not [e for e in RL.simple_guardrail(f"Hash {BAM}. Cần bác sĩ kiểm chứng.").errors
                if "R2" in str(getattr(e, "code", "")) + str(e)]
    assert [e for e in RL.simple_guardrail("Ghi CCCD người bệnh. Cần bác sĩ kiểm chứng.").errors
            if "R2" in str(getattr(e, "code", "")) + str(e)]


def test_quet_pii_che_do_chat_khong_bat_ma_bam():
    assert not [p for p in PV.quet_pii_van_ban(f"mã {BAM}") if "cccd" in p.loai]
    assert [p for p in PV.quet_pii_van_ban("số CCCD của người bệnh") if "cccd" in p.loai]
