"""Hồi quy 14/10/2026: sổ A2b của G1 không được nhặt PMID từ bản sao lưu A1 của G0.

`--dung-lai-a1` để lại `G0_A1_PICO_FINER_<mã>.bak-<thời điểm>.md`; glob `G0_A1_PICO_FINER_*.md` của
`collect_evidence_identifiers` khớp cả chúng ⇒ sau khi chạy lại tìm G0 (C1a, 14/10), PMID của tập cũ đã rời nền
(bài lạc đề) quay lại sổ bằng chứng G1.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g1_quality_gate as G1Q  # noqa: E402

MA = "de-tai-thu"


def _ghi(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8", newline="\n")


def test_bo_ban_sao_luu_a1_giu_a1_hien_hanh(tmp_path):
    _ghi(tmp_path / f"G0_A1_PICO_FINER_{MA}.md", "Nền mới: PMID 11111111; doi:10.1234/moi.1\n")
    _ghi(tmp_path / f"G0_A1_PICO_FINER_{MA}.bak-20261014-182827.md", "Nền cũ: PMID 22222222; doi:10.1234/cu.2\n")
    kq = G1Q.collect_evidence_identifiers(tmp_path, {}, [])
    assert "11111111" in kq["pmids"] and "10.1234/moi.1" in kq["dois"]
    assert "22222222" not in kq["pmids"] and "10.1234/cu.2" not in kq["dois"]


def test_doc_danh_muc_doc_bo_sung_co_cau_truc(tmp_path):
    """A1 ghi PMID nguồn bổ sung ở ô bảng trần (không tiền tố «PMID») ⇒ phải lấy từ checkpoint G0."""
    _ghi(tmp_path / f"G0_A1_PICO_FINER_{MA}.md", "| 44444444 | Tiêu đề bài bổ sung |\n")
    cp = {"danh_muc_doc_bo_sung": ["pmid:44444444", "doi:10.52163/yhc.v66i1.1940", "la:bo-qua"]}
    kq = G1Q.collect_evidence_identifiers(tmp_path, cp, [])
    assert kq["pmids"] == ["44444444"]
    assert kq["dois"] == ["10.52163/yhc.v66i1.1940"]


def test_van_doc_pmid_nen_tu_checkpoint(tmp_path):
    _ghi(tmp_path / f"G0_A1_PICO_FINER_{MA}.bak-20261014-182827.md", "PMID 22222222\n")
    kq = G1Q.collect_evidence_identifiers(tmp_path, {"pubmed_results": {"all_pmids": ["33333333"]}}, [])
    assert kq["pmids"] == ["33333333"]
