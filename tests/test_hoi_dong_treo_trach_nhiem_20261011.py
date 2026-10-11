"""Hồi quy 11/10/2026 — bảng trách nhiệm không được im lặng trước việc treo của hội đồng; tệp khai áp dụng không phải
biên bản.

Đo trên C1a: `trach-nhiem --gate G0` báo DAT_TIEU_CHI (mã 0) trong khi tranh biện BD-G0-T2 (07/10) kết luận
«sua_ket_luan» — giao thu-thu-tai-lieu gộp 5 DOI trong nước vào danh mục đọc của PI — mà việc đó chưa làm; PI chốt câu
tính mới thiếu một bài sát (Khoa Khám bệnh theo yêu cầu, BV TƯQĐ 108). Cùng lúc `study_readiness` báo G1 «HỎNG — gate
phải thuộc…» chỉ vì `hoi_dong/G1/ap_dung_nhiem_vu.json` bị đọc như biên bản. Không test nào gọi mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402

STUDY = "S-HOI-DONG-TREO"


def _ghi(p: Path, noi_dung: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(noi_dung)


def test_tep_khai_ap_dung_khong_bi_doc_nhu_bien_ban(tmp_path):
    _ghi(tmp_path / "hoi_dong" / "G1" / HD.TEP_KHAI_AP_DUNG,
         json.dumps({"G1-T4": {"ap_dung": True, "ly_do": "bộ câu hỏi tự xây"}}, ensure_ascii=False))
    assert HD.doc_bien_ban(tmp_path, "G1") == []
    assert HD.tom_tat_cong("G1", tmp_path)["trang_thai"] == "CHƯA HỌP"


def test_bien_ban_json_hong_van_bao_hong(tmp_path):
    """Chỉ bỏ qua ĐÚNG tệp khai áp dụng — biên bản hỏng thật vẫn phải lộ ra."""
    _ghi(tmp_path / "hoi_dong" / "G1" / HD.TEP_KHAI_AP_DUNG, "{}")
    _ghi(tmp_path / "hoi_dong" / "G1" / "G1-DG-20261011T000000-deadbeef.json", "{hỏng")
    tt = HD.tom_tat_cong("G1", tmp_path)
    assert tt["trang_thai"] == "HỎNG" and tt["ly_do"]


def _gia_cham_dat(monkeypatch):
    bao = {"automatic_criteria": [{"id": "G0-AUTO-01", "status": "PASS", "label": "x", "evidence": "ok",
                                   "action": ""}]}
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "DRAFT_X", "nguon": "song", "bao_cao": bao})


def test_trach_nhiem_hien_viec_treo_cua_hoi_dong(monkeypatch, tmp_path):
    _gia_cham_dat(monkeypatch)
    monkeypatch.setattr(HD, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "gate": gate, "trang_thai": "CẦN SỬA", "ly_do": ["BD-G0-T2: hội đồng yêu cầu sửa"]})
    kq = HD.trach_nhiem(STUDY, "G0", tmp_path)
    assert kq["hoi_dong_treo"] == {"trang_thai": "CẦN SỬA", "ly_do": ["BD-G0-T2: hội đồng yêu cầu sửa"]}
    van_ban = HD.in_trach_nhiem(kq)
    assert "HỘI ĐỒNG CÒN VIỆC TREO (CẦN SỬA)" in van_ban and "BD-G0-T2" in van_ban
    # Hội đồng là TƯ VẤN: kết luận và mã thoát chỉ nói về tiêu chí bộ chấm — y hệt lượt hội đồng đồng thuận.
    monkeypatch.setattr(HD, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "gate": gate, "trang_thai": "ĐỒNG THUẬN", "ly_do": []})
    nen = HD.trach_nhiem(STUDY, "G0", tmp_path)
    assert kq["ket_luan"] == nen["ket_luan"]
    assert HD.ma_thoat_trach_nhiem(kq["ket_luan"]) == HD.ma_thoat_trach_nhiem(nen["ket_luan"])


def test_trach_nhiem_im_khi_hoi_dong_dong_thuan(monkeypatch, tmp_path):
    _gia_cham_dat(monkeypatch)
    monkeypatch.setattr(HD, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "gate": gate, "trang_thai": "ĐỒNG THUẬN", "ly_do": []})
    kq = HD.trach_nhiem(STUDY, "G0", tmp_path)
    assert kq["hoi_dong_treo"] is None
    assert "HỘI ĐỒNG CÒN VIỆC TREO" not in HD.in_trach_nhiem(kq)


def test_khong_doc_duoc_bien_ban_thi_bao_khong_do_duoc(monkeypatch, tmp_path):
    """Lỗi đọc biên bản KHÔNG được biến thành «không có gì treo»."""
    _gia_cham_dat(monkeypatch)

    def _no(*a, **k):
        raise OSError("OneDrive chưa tải về")

    monkeypatch.setattr(HD, "tom_tat_cong", _no)
    kq = HD.trach_nhiem(STUDY, "G0", tmp_path)
    assert kq["hoi_dong_treo"]["trang_thai"] == "KHÔNG ĐO ĐƯỢC"


def test_bang_toan_de_tai_liet_ke_cong_co_viec_treo(monkeypatch, tmp_path):
    _gia_cham_dat(monkeypatch)
    monkeypatch.setattr(HD, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "gate": gate, "trang_thai": "CẦN SỬA" if gate == "G0" else "CHƯA HỌP", "ly_do": ["x"]})
    van_ban = HD.in_tong_trach_nhiem(HD.tong_trach_nhiem(STUDY, tmp_path))
    assert "Hội đồng còn việc treo" in van_ban and "G0 (CẦN SỬA)" in van_ban
    assert "G1 (" not in van_ban.split("Hội đồng còn việc treo")[1].splitlines()[0]
