"""Hồi quy #15 (2026-09-26): g2_quality_contract_satisfied phải lấy attestation trong
gói G2 ĐÃ KÝ làm nguồn sự thật về hạn hiệu lực IRB + phiên bản protocol/ICF.

Lỗi gốc (đã tái lập): checkpoint G2 KHÔNG ký — xoá tệp, ghi ``{}``, hay sửa tay
``g2_approval_valid_until`` thành 2099 — đủ để dữ liệu người thật được khoá/phân tích
dưới một phê duyệt IRB ĐÃ HẾT HẠN (nhánh «checkpoint thiếu version ⇒ True»).

Mọi test dựng gói trong tmp_path; không đụng exports/ thật.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g2_quality_gate as G2Q  # noqa: E402
import gate_contract as GC  # noqa: E402

_STUDY = "PYTEST-G2-ATTEST-20260926"


def _meta(protocol: str = "2.0", icf: str = "1.1") -> dict:
    return {"gate_params": {"G2": {"protocol_version": protocol, "icf_version": icf}}}


def _goi(out_dir: Path, **attest) -> Path:
    base = {
        "schema_version": G2Q.ATTESTATION_SCHEMA, "study": _STUDY,
        "ethics_decision": "APPROVED", "approval_number": "IRB-01",
        "approved_protocol_version": "2.0", "approved_icf_version": "1.1",
        "valid_until": "2099-12-31",
    }
    base.update(attest)
    p = out_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    p.write_text(G2Q.append_attestation("# Hồ sơ đạo đức\n", base), encoding="utf-8", newline="\n")
    return p


def _cp_hop_le(valid_until: str = "2099-12-31") -> dict:
    return {
        "quality_contract_version": "G2-2026.1",
        "quality_gate": {"status": "PASS_G2_APPROVED"},
        "g2_approval_valid_until": valid_until,
        "g2_protocol_version": "2.0", "g2_icf_version": "1.1",
    }


def _ok(cp, out_dir: Path, meta=None) -> bool:
    return GC.g2_quality_contract_satisfied(cp, meta or _meta(), study=_STUDY, out_dir=out_dir)


# Checkpoint bị xoá (caller đọc thành {}), bị ghi {} / dạng cũ không version, hoặc bị
# sửa tay hạn thành 2099 — KHÔNG ca nào được mở cổng khi attestation đã ký nói «hết hạn».
_CHECKPOINT_BI_SUA = [
    pytest.param({}, id="checkpoint-xoa-hoac-rong"),
    pytest.param({"g2_status": "LOCKED"}, id="checkpoint-khong-version"),
    pytest.param(_cp_hop_le("2099-12-31"), id="checkpoint-sua-han-2099"),
]


@pytest.mark.parametrize("cp", _CHECKPOINT_BI_SUA)
def test_attestation_het_han_luon_chan(tmp_path, cp):
    _goi(tmp_path, valid_until="2020-01-01")
    assert _ok(cp, tmp_path) is False


@pytest.mark.parametrize("cp", _CHECKPOINT_BI_SUA)
def test_attestation_lech_protocol_luon_chan(tmp_path, cp):
    _goi(tmp_path, approved_protocol_version="1.0")
    assert _ok(cp, tmp_path, _meta(protocol="2.0")) is False


def test_attestation_lech_icf_chan(tmp_path):
    _goi(tmp_path, approved_icf_version="1.0")
    assert _ok(_cp_hop_le(), tmp_path, _meta(icf="1.1")) is False


def test_attestation_thieu_han_khong_xac_nhan_chan(tmp_path):
    _goi(tmp_path, valid_until="")
    assert _ok(_cp_hop_le(), tmp_path) is False


def test_co_attestation_thi_checkpoint_rong_khong_con_duoc_mien(tmp_path):
    """Attestation hợp lệ nhưng checkpoint bị xoá ⇒ KHÔNG áp nhánh «thiếu version ⇒ True»."""
    _goi(tmp_path)
    assert _ok({}, tmp_path) is False
    assert _ok({"g2_status": "LOCKED"}, tmp_path) is False


def test_doi_chung_attestation_va_checkpoint_hop_le(tmp_path):
    _goi(tmp_path)
    assert _ok(_cp_hop_le(), tmp_path) is True


def test_doi_chung_attestation_khong_ghi_han_da_xac_nhan(tmp_path):
    _goi(tmp_path, valid_until="", no_expiry_confirmed=True)
    assert _ok(_cp_hop_le(), tmp_path) is True


def test_goi_khong_attestation_giu_nhanh_tuong_thich(tmp_path):
    """Gói KHÔNG có attestation (fixture tổng hợp): giữ đúng hành vi cũ, không nới thêm."""
    (tmp_path / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md").write_text(
        "# Hồ sơ\n", encoding="utf-8", newline="\n")
    assert _ok({"g2_status": "LOCKED"}, tmp_path) is True
    assert _ok(_cp_hop_le("2020-01-01"), tmp_path) is False


def test_moi_noi_goi_trong_tools_deu_truyen_out_dir():
    """Sót một nơi gọi không truyền out_dir thì chỗ đó giữ hành vi cũ mà không ai biết."""
    thieu = []
    for f in sorted(TOOLS_DIR.glob("*.py")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"g2_quality_contract_satisfied\(", text):
            if text[max(0, m.start() - 4):m.start()] == "def ":
                continue
            window = text[m.end():m.end() + 400]
            # Cắt tới dấu đóng ngoặc cân bằng đầu tiên của lời gọi.
            depth, end = 1, len(window)
            for i, ch in enumerate(window):
                depth += ch == "("
                depth -= ch == ")"
                if depth == 0:
                    end = i
                    break
            if "out_dir=" not in window[:end]:
                line = text.count("\n", 0, m.start()) + 1
                thieu.append(f"{f.name}:{line}")
    assert thieu == [], f"nơi gọi thiếu out_dir=: {thieu}"


@pytest.mark.parametrize("khoi", [
    pytest.param("```json\n{hỏng\n```", id="json-hong"),
    pytest.param("```json\n[1, 2]\n```", id="goc-khong-phai-dict"),
    pytest.param("khong co khoi json", id="thieu-khoi-json"),
])
def test_khoi_attestation_hong_khong_roi_ve_nhanh_tuong_thich(tmp_path, khoi):
    """Rà phản biện 2026-09-26: gói CÓ dấu mở attestation nhưng khối bị hỏng/sửa không
    được coi như «không có attestation» (nhánh tương thích checkpoint thiếu version ⇒
    True là xanh giả) — phải False."""
    (tmp_path / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md").write_text(
        f"# Hồ sơ\n{G2Q.ATTESTATION_BEGIN}\n{khoi}\n{G2Q.ATTESTATION_END}\n",
        encoding="utf-8", newline="\n")
    assert _ok({"g2_status": "LOCKED"}, tmp_path) is False
