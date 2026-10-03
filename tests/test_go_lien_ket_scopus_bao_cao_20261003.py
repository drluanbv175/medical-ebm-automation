"""Không bao giờ để liên kết / mã EID Scopus lên báo cáo của repo CÔNG KHAI (03/10/2026).

Sự cố: commit 7fc55a2 (Routine Cloud, chế độ chỉ báo cáo) đăng 79 liên kết `scopus.com/inward/record.uri?…` trong
`reports/giam-sat-cloud/2026-09-29/`. Điều khoản Elsevier (riêng Scopus sửa 16/09/2026; API Service Agreement §2.4)
cấm phát tán dữ liệu Scopus. Kiểm, không gọi mạng:
(1) `lien_ket_cong_khai`: URL Scopus ⇒ DOI, rồi PubMed, không có thì None; URL khác giữ nguyên;
(2) `lam_sach_van_ban` trên ĐÚNG khuôn dòng của bản tin/bảng kháng sinh: thay bằng liên kết công khai của cùng mục,
    mục không có DOI/PMID ⇒ ghi chú, không in trùng, idempotent, giữ CRLF, không bắt nhầm;
(3) ba bộ dựng báo cáo (bản tin, an toàn thuốc/kháng sinh, EBM tuần) không in URL Scopus;
(4) chế độ chỉ báo cáo làm sạch NGAY LÚC CHÉP + tóm tắt ghi số đã gỡ; còn sót ⇒ xoá tệp + từ chối;
(5) công cụ `tools/kiem_lien_ket_scopus_bao_cao.py` (--path/--lam-sach/--staged, tên tệp tiếng Việt);
(6) pre-commit gọi chốt trên DÒNG THI HÀNH; (7) mọi tệp đã track dưới `reports/` sạch; (8) lõi chỉ dùng thư viện chuẩn.
Dữ liệu Scopus trong test là GIẢ (partnerID/scp/EID bịa) — không chép lại định danh bản ghi thật.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import bao_cao_giam_sat_chi_doc as BC  # noqa: E402
import kiem_lien_ket_scopus_bao_cao as KS  # noqa: E402

from app.config import settings  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.reports import alert_digest, safety_reports, weekly_ebm  # noqa: E402
from app.utils import lien_ket_scopus as L  # noqa: E402

MIEN = "https://www." + "scopus.com"
URL_SCOPUS = f"{MIEN}/inward/record.uri?partnerID=XXXXXXXX&scp=1&origin=inward"
EID = "2-s2.0-" + "85000000001"
DOI = "10.1093/esj/aakag044"
PMID = "42095755"


def _sach(text: str) -> str:
    moi, _ = L.lam_sach_van_ban(text)
    assert L.tim_vi_pham(moi) == [], moi
    return moi


# ---------------------------------------------------------------- (1) liên kết công khai cho bộ dựng
def test_lien_ket_cong_khai_doi_roi_pmid_khong_co_thi_bo():
    assert L.lien_ket_cong_khai(URL_SCOPUS, DOI, PMID) == f"https://doi.org/{DOI}"
    assert L.lien_ket_cong_khai(URL_SCOPUS, None, PMID) == f"https://pubmed.ncbi.nlm.nih.gov/{PMID}/"
    assert L.lien_ket_cong_khai(URL_SCOPUS, None, None) is None
    assert L.lien_ket_cong_khai(URL_SCOPUS, "không-phải-doi", "abc") is None
    assert L.lien_ket_cong_khai(f"{MIEN}/record/display.uri?eid={EID}", "doi:10.1000/xyz.", None) == \
        "https://doi.org/10.1000/xyz"
    assert L.lien_ket_cong_khai(EID, DOI) == f"https://doi.org/{DOI}"  # EID trơn cũng là dữ liệu Scopus
    assert L.lien_ket_cong_khai("https://core.ac.uk/works/1", DOI) == "https://core.ac.uk/works/1"
    assert L.lien_ket_cong_khai(None, DOI) is None and L.lien_ket_cong_khai("", DOI) == ""


# ---------------------------------------------------------------- (2) chốt hậu kiểm trên văn bản
def test_lam_sach_dong_ban_tin_giu_nguyen_phan_khac():
    dong = f"  - Nguồn: DOI:{DOI} ; PMID:{PMID} ; {URL_SCOPUS}"
    assert _sach(dong) == f"  - Nguồn: DOI:{DOI} ; PMID:{PMID} ; https://doi.org/{DOI}"


def test_lam_sach_hang_bang_khang_sinh_va_doi_co_ngoac():
    hang = (f"| Bài A | Lancet | C | Có | DOI:10.1016/s2213-8587(26)00119-1 ; {URL_SCOPUS} |"
            f" Bài B | {MIEN}/inward/record.uri?scp=2 |")
    moi = _sach(hang)
    assert "| DOI:10.1016/s2213-8587(26)00119-1 ; https://doi.org/10.1016/s2213-8587(26)00119-1 |" in moi
    # ô thứ hai không có DOI/PMID trong CHÍNH ô đó ⇒ không mượn DOI của ô khác
    assert moi.endswith(f" Bài B | {L.GHI_CHU_GO} |")


def test_lam_sach_pmid_khi_khong_co_doi_va_ghi_chu_khi_khong_co_gi():
    assert _sach(f"Nguồn: PMID:{PMID} ; {URL_SCOPUS}") == \
        f"Nguồn: PMID:{PMID} ; https://pubmed.ncbi.nlm.nih.gov/{PMID}/"
    assert _sach(f"- **Tiêu đề X**\n  - Nguồn: {URL_SCOPUS}\n") == f"- **Tiêu đề X**\n  - Nguồn: {L.GHI_CHU_GO}\n"


def test_lam_sach_eid_tron_lien_ket_markdown_va_khong_in_trung():
    assert _sach(f"EID: {EID} — DOI {DOI}") == f"https://doi.org/{DOI} — DOI {DOI}"
    assert _sach(f"[Bài]({MIEN}/record/display.uri?eid={EID}) DOI:{DOI}") == f"[Bài](https://doi.org/{DOI}) DOI:{DOI}"
    assert _sach(f"[Bài]({URL_SCOPUS})") == f"Bài {L.GHI_CHU_GO}"
    # đã có liên kết DOI ⇒ chỉ gỡ token Scopus kèm « ; » thừa, không in trùng
    assert _sach(f"DOI:{DOI} ; https://doi.org/{DOI} ; {URL_SCOPUS}") == f"DOI:{DOI} ; https://doi.org/{DOI}"
    assert _sach(f"DOI:{DOI} ; {URL_SCOPUS} ; EID:{EID}") == f"DOI:{DOI} ; https://doi.org/{DOI}"
    # URL đã html-escape (&amp;) trong thuộc tính href
    assert _sach(f'<a href="{URL_SCOPUS.replace("&", "&amp;")}">x</a> DOI:{DOI}') == \
        f'<a href="https://doi.org/{DOI}">x</a> DOI:{DOI}'


def test_lam_sach_idempotent_giu_crlf_va_khong_bat_nham():
    goc = f"dòng 1\r\nDOI:{DOI} ; {URL_SCOPUS}\r\nkhông đổi\r\n"
    moi, n = L.lam_sach_van_ban(goc)
    assert n == 1 and moi == f"dòng 1\r\nDOI:{DOI} ; https://doi.org/{DOI}\r\nkhông đổi\r\n"
    assert L.lam_sach_van_ban(moi) == (moi, 0)
    vo_hai = "Scopus bị Cloudflare chặn (403) · xscopus.com · scopus.community · DOI:10.1000/2-s2.0-12"
    assert L.lam_sach_van_ban(vo_hai) == (vo_hai, 0) and L.tim_vi_pham(vo_hai) == []


def test_tim_vi_pham_bat_ca_url_lan_eid():
    vp = L.tim_vi_pham(f"a\n{URL_SCOPUS}\nEID:{EID}\nhttp://scopus.com/x")
    assert [d for d, _ in vp] == [2, 3, 4]


# ---------------------------------------------------------------- (3) bộ dựng báo cáo
def _ban_ghi(**kw) -> EvidenceItem:
    mac_dinh = dict(id=1, title="European stroke organisation guideline", doi=DOI, pmid=PMID, url=URL_SCOPUS,
                    clinical_area="Thần kinh", reliability_tier="B", source="scopus")
    mac_dinh.update(kw)
    return EvidenceItem(**mac_dinh)


@pytest.mark.parametrize("ham", [alert_digest._ref, safety_reports._ref,
                                 lambda r: weekly_ebm._ref_str(weekly_ebm._row(r))],
                         ids=["ban_tin", "an_toan_thuoc_khang_sinh", "ebm_tuan"])
def test_bo_dung_bao_cao_doi_url_scopus_sang_doi(ham):
    ref = ham(_ban_ghi())
    assert f"https://doi.org/{DOI}" in ref and L.tim_vi_pham(ref) == []
    ref_pmid = ham(_ban_ghi(doi=None))
    assert f"https://pubmed.ncbi.nlm.nih.gov/{PMID}/" in ref_pmid and L.tim_vi_pham(ref_pmid) == []
    ref_trong = ham(_ban_ghi(doi=None, pmid=None))
    assert L.tim_vi_pham(ref_trong) == [] and "http" not in ref_trong  # không có DOI/PMID ⇒ không in liên kết
    khac = ham(_ban_ghi(url="https://core.ac.uk/works/7"))
    assert "https://core.ac.uk/works/7" in khac  # nguồn không phải Scopus giữ nguyên


def test_ban_tin_ngan_va_dong_ban_tin_day_du_khong_co_scopus():
    r = _ban_ghi(doi=None, pmid=None)
    assert alert_digest._dong_ngan(r, frozenset()).endswith("— —")
    dong = "\n".join(alert_digest._bullets([_ban_ghi()]))
    assert f"  - Nguồn: DOI:{DOI} ; PMID:{PMID} ; https://doi.org/{DOI}" in dong and L.tim_vi_pham(dong) == []


# ---------------------------------------------------------------- (4) chế độ chỉ báo cáo
def _sh(status="PASS", **kw):
    return {"source_health": {"status": status, "total_records": 42, **kw}, "new_items": 5}


def _xuat_co_scopus(ngay):
    noi_dung = {
        "alert_digest_md": (f"# Bản tin\n- **A**\n  - Nguồn: DOI:{DOI} ; PMID:{PMID} ; {URL_SCOPUS}\n"
                            f"- **B**\n  - Nguồn: {MIEN}/inward/record.uri?scp=3\n"),
        "weekly_md": "# Tuần\n",
        "drug_safety_md": "# An toàn thuốc\n",
        "antibiotic_md": f"| T | J | C | Có | DOI:10.1186/s12890-026-04169-3 ; {URL_SCOPUS} |\n",
    }
    out = {}
    for khoa, txt in noi_dung.items():
        p = settings.reports_dir / f"{khoa}.md"
        p.write_text(txt, encoding="utf-8", newline="\n")
        out[khoa] = p
    return out


def test_che_do_chi_bao_cao_lam_sach_khi_chep_va_ghi_so_da_go(tmp_path):
    ra = tmp_path / "ra"
    t = BC.chay_bao_cao_chi_doc(ra, 10, 3, _xuat=_xuat_co_scopus,
                                _chay_pipeline=lambda q, n: _sh("PARTIAL", warnings=[f"scopus 403 {URL_SCOPUS}"]))
    assert L.quet_thu_muc(ra) == {}
    ban_tin = (ra / "ban-tin-moi.md").read_text(encoding="utf-8")
    assert f"; https://doi.org/{DOI}\n" in ban_tin and f"  - Nguồn: {L.GHI_CHU_GO}\n" in ban_tin
    assert "https://doi.org/10.1186/s12890-026-04169-3 |" in (ra / "khang-sinh.md").read_text(encoding="utf-8")
    assert t["lien_ket_scopus_da_go"] == {"ban-tin-moi.md": 2, "khang-sinh.md": 1}
    assert t == json.loads((ra / "tom_tat.json").read_text(encoding="utf-8"))
    assert "Liên kết/EID Scopus đã gỡ" in (ra / "TOM-TAT.md").read_text(encoding="utf-8")


def test_con_scopus_sau_lam_sach_thi_xoa_tep_va_tu_choi(tmp_path, monkeypatch):
    """Lưới cuối: giả lập bộ làm sạch hỏng (chép nguyên) ⇒ tệp bẩn bị XOÁ, công cụ từ chối (main trả 3)."""
    def chep_tho(nguon, dich):
        shutil.copyfile(nguon, dich)
        return 0

    monkeypatch.setattr(BC, "chep_da_lam_sach", chep_tho)
    ra = tmp_path / "ra"
    with pytest.raises(ValueError, match="Scopus"):
        BC.chay_bao_cao_chi_doc(ra, _chay_pipeline=lambda q, n: _sh(), _xuat=_xuat_co_scopus)
    assert not (ra / "ban-tin-moi.md").exists() and not (ra / "khang-sinh.md").exists()
    assert (ra / "an-toan-thuoc.md").exists()  # tệp sạch giữ lại
    monkeypatch.setattr(BC, "_mac_dinh_chay_pipeline", lambda q, n: _sh())
    monkeypatch.setattr(BC, "_mac_dinh_xuat", _xuat_co_scopus)
    assert BC.main(["--out", str(tmp_path / "ra2")]) == 3


# ---------------------------------------------------------------- (5) công cụ kiểm
def test_cong_cu_path_va_lam_sach(tmp_path, capsys):
    d = tmp_path / "giam-sat-cloud" / "2026-10-05"
    d.mkdir(parents=True)
    (d / "ban-tin-moi.md").write_text(f"Nguồn: DOI:{DOI} ; {URL_SCOPUS}\n", encoding="utf-8", newline="\n")
    (d / "tom_tat.json").write_text(json.dumps({"x": f"EID {EID}"}), encoding="utf-8", newline="\n")
    assert KS.main(["--path", str(tmp_path)]) == 1
    assert KS.main(["--lam-sach", str(tmp_path)]) == 0
    assert KS.main(["--path", str(tmp_path)]) == 0
    assert (d / "ban-tin-moi.md").read_text(encoding="utf-8") == f"Nguồn: DOI:{DOI} ; https://doi.org/{DOI}\n"
    assert json.loads((d / "tom_tat.json").read_text(encoding="utf-8")) == {"x": L.GHI_CHU_GO}
    assert KS.main(["--path", str(tmp_path / "khong-co")]) == 2


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_staged_doc_index_chi_trong_reports_ke_ca_ten_tieng_viet(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    bao_cao = repo / "reports" / "giam-sat-cloud" / "2026-10-05" / "bản-tin-mới.md"
    bao_cao.parent.mkdir(parents=True)
    bao_cao.write_text(f"Nguồn: DOI:{DOI} ; {URL_SCOPUS}\n", encoding="utf-8", newline="\n")
    ngoai = repo / "tests" / "fixture.md"
    ngoai.parent.mkdir()
    ngoai.write_text(f"{URL_SCOPUS}\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    vp = KS.quet_staged(repo)
    assert list(vp) == ["reports/giam-sat-cloud/2026-10-05/bản-tin-mới.md"]  # tests/ ngoài phạm vi
    assert KS.main(["--staged", "--repo", str(repo)]) == 1
    # sửa cây làm việc mà CHƯA git add ⇒ index vẫn bẩn ⇒ vẫn chặn
    assert KS.main(["--lam-sach", str(bao_cao)]) == 0
    assert KS.main(["--staged", "--repo", str(repo)]) == 1
    _git(repo, "add", "-A")
    assert KS.main(["--staged", "--repo", str(repo)]) == 0


# ---------------------------------------------------------------- (6) pre-commit nối chốt
def test_pre_commit_goi_chot_scopus_tren_dong_thi_hanh():
    dong = [d.strip() for d in (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8").splitlines()]
    thi_hanh = [d for d in dong if d and not d.startswith("#")]
    assert "python3 tools/kiem_lien_ket_scopus_bao_cao.py --staged" in thi_hanh
    i = thi_hanh.index("python3 tools/kiem_lien_ket_scopus_bao_cao.py --staged")
    assert thi_hanh[i + 1] == "MA_SCOPUS=$?"
    assert thi_hanh[i + 2] == 'if [ "$MA_SCOPUS" -eq 1 ]; then'
    assert thi_hanh[i + 4] == "exit 1"
    assert i < len(thi_hanh) - 1 - thi_hanh[::-1].index("exit 0")  # trước lệnh thoát 0 cuối cùng


# ---------------------------------------------------------------- (7) mọi tệp đã track dưới reports/
def test_moi_tep_da_track_duoi_reports_khong_co_lien_ket_scopus():
    try:
        tep = [p for p in subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--", "reports/"],
                                         capture_output=True, check=True).stdout.decode("utf-8").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):  # không có git (bản tarball) ⇒ quét thẳng thư mục, không bỏ qua
        tep = [p.relative_to(ROOT).as_posix() for p in (ROOT / "reports").rglob("*") if p.is_file()]
    assert tep, "không thấy tệp nào dưới reports/ — phép quét sẽ xanh giả"
    vi_pham = {}
    for p in tep:
        duong = ROOT / p
        if duong.is_file():
            vp = L.tim_vi_pham(duong.read_bytes().decode("utf-8", errors="replace"))
            if vp:
                vi_pham[p] = len(vp)
    assert vi_pham == {}, f"reports/ còn liên kết/EID Scopus (repo CÔNG KHAI): {vi_pham}"


# ---------------------------------------------------------------- (8) lõi chỉ dùng thư viện chuẩn
def test_loi_va_cong_cu_khong_keo_thu_vien_ngoai():
    """pre-commit gọi bằng python3 hệ thống (không venv): nạp lõi + công cụ không được kéo SQLAlchemy/pydantic."""
    ma = ("import sys; sys.path[:0] = [sys.argv[1], sys.argv[1] + '/tools']; "
          "import kiem_lien_ket_scopus_bao_cao; "
          "print(sorted(m for m in ('sqlalchemy', 'pydantic', 'app.config') if m in sys.modules))")
    ra = subprocess.run([sys.executable, "-B", "-c", ma, str(ROOT)], capture_output=True, text=True, check=True)
    assert ra.stdout.strip() == "[]"
