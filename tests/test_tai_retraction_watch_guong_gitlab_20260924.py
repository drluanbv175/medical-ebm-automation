"""Hồi quy 24/09/2026 — `tools/tai_retraction_watch.py` có nguồn dự phòng là gương GitLab
chính thức của Crossref (`gitlab.com/crossref/retraction-watch-data`).

Vì sao: trên phiên Cloud (môi trường «Trusted»), proxy chặn `api.labs.crossref.org` (403 theo
chính sách) và container không có email ⇒ công cụ cũ thoát mã 2 ngay («Crossref bắt buộc
email») ⇒ tầng ① của chuỗi rút bài — tầng DUY NHẤT bắt được PMID 30267080 (rút-và-thay) —
chưa từng chạy trên Cloud. Đo thật 24/09/2026 sau bản vá: tải 72.606 dòng từ gương GitLab,
31.511 PMID có phán quyết; chuỗi trả `retracted` + `retract_and_replace` cho 30267080.

Các test dưới đây KHÔNG gọi mạng: `_tai_ve` được thay bằng kịch bản; thư mục ghi là tmp."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import tai_retraction_watch as trw  # noqa: E402

_COT = "Record ID,Title,RetractionPubMedID,OriginalPaperPubMedID,RetractionNature,Reason\n"


def _csv_hop_le(so_dong: int = 1200) -> bytes:
    dong = [f"{i},Bai {i},{9000000 + i},{8000000 + i},Retraction,+Error in Data;\n" for i in range(so_dong)]
    return (_COT + "".join(dong)).encode("utf-8")


@pytest.fixture()
def kich_ban(monkeypatch, tmp_path):
    """Chuyển hướng mọi đường ghi sang tmp; `_tai_ve` trả theo kịch bản {url_tiền_tố: bytes|Exception}."""
    monkeypatch.setattr(trw, "THU_MUC", tmp_path)
    monkeypatch.setattr(trw, "CSV_MAC_DINH", tmp_path / "retraction_watch.csv")
    monkeypatch.setattr(trw, "META_MAC_DINH", tmp_path / "retraction_watch.meta.json")
    monkeypatch.setattr(trw, "REPO", tmp_path)  # relative_to() trong thông báo
    monkeypatch.setattr(trw, "RetractionWatchIndex", lambda: type("I", (), {"so_ban_ghi": lambda self: 1})())
    goi: list[str] = []
    ban_do: dict[str, object] = {}

    def gia(url: str) -> bytes:
        goi.append(url)
        for tien_to, kq in ban_do.items():
            if url.startswith(tien_to):
                if isinstance(kq, BaseException):
                    raise kq
                return kq
        raise AssertionError(f"URL ngoài kịch bản: {url}")

    monkeypatch.setattr(trw, "_tai_ve", gia)
    return ban_do, goi, tmp_path


def test_khong_email_di_thang_guong_gitlab_va_meta_ghi_dung_nguon(kich_ban, capsys):
    ban_do, goi, tmp = kich_ban
    ban_do[trw.GUONG_GITLAB[0]] = _csv_hop_le()
    assert trw.tai("", "tu-dong") == 0
    assert goi == [trw.GUONG_GITLAB[0]], "không email ⇒ không được gọi Crossref Labs API"
    meta = json.loads((tmp / "retraction_watch.meta.json").read_text(encoding="utf-8"))
    assert meta["nguon"] == trw.GUONG_GITLAB[0] and meta["so_dong"] == 1200
    assert "gương GitLab" in capsys.readouterr().out


def test_crossref_loi_thi_lui_ve_gitlab_va_meta_khong_chua_email(kich_ban):
    ban_do, goi, tmp = kich_ban
    ban_do[trw.ENDPOINT] = OSError("Tunnel connection failed: 403 Forbidden")
    ban_do[trw.GUONG_GITLAB[0]] = _csv_hop_le()
    assert trw.tai("bacsi@example.org", "tu-dong") == 0
    assert goi[0].startswith(trw.ENDPOINT) and goi[1] == trw.GUONG_GITLAB[0]
    noi_dung_meta = (tmp / "retraction_watch.meta.json").read_text(encoding="utf-8")
    assert "bacsi@example.org" not in noi_dung_meta


def test_nguon_dau_sai_schema_khong_duoc_ghi_va_thu_nguon_ke(kich_ban):
    ban_do, goi, tmp = kich_ban
    ban_do[trw.ENDPOINT] = b"<html>trang loi</html>"
    ban_do[trw.GUONG_GITLAB[0]] = _csv_hop_le()
    assert trw.tai("bacsi@example.org", "tu-dong") == 0
    assert len(goi) == 2
    assert (tmp / "retraction_watch.csv").read_bytes().startswith(b"Record ID")


def test_raw_bi_loi_thi_dung_duong_api_gitlab(kich_ban):
    ban_do, goi, _tmp = kich_ban
    ban_do[trw.GUONG_GITLAB[0]] = OSError("redirect sang host khác bị chặn")
    ban_do[trw.GUONG_GITLAB[1]] = _csv_hop_le()
    assert trw.tai("", "gitlab") == 0
    assert goi == list(trw.GUONG_GITLAB)


def test_moi_nguon_hong_thi_giu_nguyen_ban_cu(kich_ban):
    ban_do, _goi, tmp = kich_ban
    (tmp / "retraction_watch.csv").write_text("BAN CU", encoding="utf-8", newline="\n")
    ban_do[trw.GUONG_GITLAB[0]] = _csv_hop_le(so_dong=10)  # quá ít dòng — nghi bị cắt
    ban_do[trw.GUONG_GITLAB[1]] = OSError("mất mạng")
    assert trw.tai("", "gitlab") == 2
    assert (tmp / "retraction_watch.csv").read_text(encoding="utf-8") == "BAN CU"


def test_chi_crossref_ma_thieu_email_thi_bao_ro_khong_goi_mang(kich_ban, capsys):
    _ban_do, goi, _tmp = kich_ban
    assert trw.tai("", "crossref") == 2
    assert goi == []
    assert "--nguon gitlab" in capsys.readouterr().out


def test_guong_la_kho_chinh_thuc_cua_crossref():
    # Chỉ nhận đúng kho của tổ chức Crossref — đổi sang một bản sao của bên thứ ba là đổi nguồn
    # chứng cứ, phải có quyết định riêng chứ không lặng lẽ qua một lần sửa hằng số.
    assert all(u.startswith("https://gitlab.com/") and "crossref" in u and "retraction-watch-data" in u
               for u in trw.GUONG_GITLAB)
