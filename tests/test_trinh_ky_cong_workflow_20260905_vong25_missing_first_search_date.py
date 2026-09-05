"""Hồi quy phát hiện #2 (Trung bình) của Workflow đối kháng đa-agent 2026-09-05
(vòng 25) trong tools/trinh_ky_cong.py — phỏng vấn G2 không hỏi
--g2-first-search-date cho thiết kế SR/MA, dù approve_gate.py BẮT BUỘC cờ
này khi design_code == "sr_ma" (đọc từ G2_checkpoint.json, xem
tools/approve_gate.py quanh dòng 288-292).

CƠ CHẾ LỖI: phong_van_g2() cũ (nhận 0 đối số) không hề đọc
G2_checkpoint.json nên không biết design_code của đề tài — hệ quả là
KHÔNG BAO GIỜ hỏi --g2-first-search-date, kể cả khi đề tài là SR/MA. Người
duyệt trả lời hết toàn bộ phỏng vấn (10+ câu, mỗi câu đòi dữ kiện thật
không được bịa), gõ đúng "KY THAT" để xác nhận, rồi mới bị approve_gate.py
từ chối Ở PHÚT CHÓT ("SR/MA phải có --g2-first-search-date") vì thiếu đúng
cờ mà trợ lý trình-ký lẽ ra phải hỏi từ đầu — đúng lúc trợ lý này được viết
ra để tránh (xem docstring module: "riêng G2 có hơn 15 cờ, người duyệt
không thể nhớ").

BẢN VÁ:
- doc_design_code(study_dir) — đọc design_code từ G2_checkpoint.json,
  logic khớp NGUYÊN VĂN approve_gate.py (đổi ở đó thì đổi ở đây theo).
- phong_van_g2(study_dir) — nhận thêm study_dir; hỏi thêm câu "SR/MA —
  ngày BẮT ĐẦU tìm kiếm..." khi doc_design_code(study_dir) == "sr_ma".
- soan_lenh() — thêm cặp ("g2_first_search_date", "--g2-first-search-date")
  vào danh sách don_gian.

Nguyên tắc viết test: gọi THẲNG doc_design_code()/phong_van_g2()/soan_lenh()
thật. phong_van_g2() đọc dữ liệu qua input() nên test giả lập bằng cách
monkeypatch builtins.input với một iterator câu trả lời theo ĐÚNG thứ tự
các câu hỏi thật của hàm (đối chiếu trực tiếp với mã nguồn, không đoán) —
không mock nội bộ _hoi/_hoi_chon."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import trinh_ky_cong as TK  # noqa: E402


def _ghi_checkpoint(study_dir: Path, design_code: str) -> None:
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G2_checkpoint.json").write_text(
        json.dumps({"design_code": design_code}), encoding="utf-8", newline="\n"
    )


def _tra_loi_lien_tuc(danh_sach):
    """input() giả — trả lần lượt từng phần tử của danh_sach theo đúng thứ tự
    được gọi, bất kể prompt truyền vào là gì."""
    it = iter(danh_sach)

    def _input(_prompt=""):
        return next(it)

    return _input


class TestDocDesignCode:
    def test_doc_dung_design_code_sr_ma(self, tmp_path):
        _ghi_checkpoint(tmp_path, "sr_ma")
        assert TK.doc_design_code(tmp_path) == "sr_ma"

    def test_thieu_checkpoint_khong_bi_hieu_nham_la_sr_ma(self, tmp_path):
        """Đối chứng — không có G2_checkpoint.json thì KHÔNG được suy đoán
        là "sr_ma", không được ném lỗi. (Giống hệt approve_gate.py: khi
        checkpoint rỗng, checkpoint.get("design_code") trả None rồi bị
        str() thành chuỗi "None" — quirk vô hại có sẵn ở approve_gate.py mà
        hàm này cố ý chép nguyên văn để hai nơi luôn khớp nhau; giá trị
        "None" không bao giờ khớp "sr_ma" nên không đổi hành vi thật.)"""
        assert TK.doc_design_code(tmp_path) != "sr_ma"

    def test_checkpoint_json_hong_khong_lam_sap_cong_cu(self, tmp_path):
        """Đối chứng — JSON hỏng (đúng loại lỗi thật gặp trong approve_gate.py,
        vd file bị ghi dở) không được làm crash hàm đọc, và không bị hiểu
        nhầm là "sr_ma"."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "G2_checkpoint.json").write_text(
            "{khong phai json hop le", encoding="utf-8", newline="\n"
        )
        assert TK.doc_design_code(tmp_path) != "sr_ma"


class TestPhongVanG2HoiFirstSearchDateChoSRMA:
    """★★★ Ca chính — SR/MA phải được hỏi --g2-first-search-date NGAY TRONG
    phỏng vấn, không được để approve_gate từ chối ở phút chót."""

    def test_sr_ma_duoc_hoi_va_tra_loi_nam_trong_ket_qua(self, tmp_path, monkeypatch):
        _ghi_checkpoint(tmp_path, "sr_ma")
        cau_tra_loi = [
            "HĐĐĐ/Người Test",      # reviewer_ref
            "HĐĐĐ-TEST",            # g2_ethics_committee_ref
            "123/QĐ-TEST",          # g2_approval_number
            "2026-09-01",           # g2_approval_date
            "1",                    # ethics_decision -> APPROVED
            "v1.0",                 # protocol_version
            "2",                    # hiệu lực -> "Không ghi hạn (xác nhận)"
            "2",                    # ICF -> "Được MIỄN ICF"
            "3",                    # kiểu tuyển mẫu -> NOT_APPLICABLE
            "2026-01-15",           # g2_first_search_date (SR/MA — câu MỚI)
            "",                     # approval_scope (Enter để bỏ qua)
        ]
        monkeypatch.setattr("builtins.input", _tra_loi_lien_tuc(cau_tra_loi))
        tl = TK.phong_van_g2(tmp_path)

        assert tl.get("g2_first_search_date") == "2026-01-15", (
            "TRƯỚC bản vá: phong_van_g2() không hề hỏi câu này cho SR/MA — "
            "người ký sẽ bị approve_gate từ chối ở phút chót sau khi đã trả "
            "lời xong toàn bộ phỏng vấn"
        )

        lenh = TK.soan_lenh("G2", "DE-TAI-SRMA", Path("/x/a.md"), tl)
        assert "--g2-first-search-date" in lenh and "2026-01-15" in lenh, (
            "soan_lenh() phải truyền cờ này cho approve_gate.py — hỏi đúng "
            "mà không truyền thì approve_gate vẫn từ chối như cũ"
        )

    def test_khong_phai_sr_ma_khong_bi_hoi_them(self, tmp_path, monkeypatch):
        """Đối chứng bắt buộc — thiết kế KHÔNG PHẢI sr_ma (vd cohort) không
        bị hỏi thêm câu này, giữ nguyên số bước phỏng vấn như trước bản vá."""
        _ghi_checkpoint(tmp_path, "cohort")
        cau_tra_loi = [
            "HĐĐĐ/Người Test",
            "HĐĐĐ-TEST",
            "123/QĐ-TEST",
            "2026-09-01",
            "1",
            "v1.0",
            "2",
            "2",
            "3",
            "",                     # approval_scope — KHÔNG có câu chen giữa
        ]
        monkeypatch.setattr("builtins.input", _tra_loi_lien_tuc(cau_tra_loi))
        tl = TK.phong_van_g2(tmp_path)

        assert "g2_first_search_date" not in tl
        lenh = TK.soan_lenh("G2", "DE-TAI-COHORT", Path("/x/a.md"), tl)
        assert "--g2-first-search-date" not in lenh

    def test_khong_co_checkpoint_khong_bi_hoi_them(self, tmp_path, monkeypatch):
        """Đối chứng — chưa có G2_checkpoint.json (đề tài mới, chưa chạy
        run_g0_auto.py) không được coi nhầm là sr_ma."""
        cau_tra_loi = [
            "HĐĐĐ/Người Test", "HĐĐĐ-TEST", "123/QĐ-TEST", "2026-09-01",
            "1", "v1.0", "2", "2", "3", "",
        ]
        monkeypatch.setattr("builtins.input", _tra_loi_lien_tuc(cau_tra_loi))
        tl = TK.phong_van_g2(tmp_path)
        assert "g2_first_search_date" not in tl


class TestSoanLenhCoFirstSearchDate:
    def test_gia_tri_ron_khong_sinh_co(self):
        """Đối chứng — theo đúng quy ước don_gian hiện có, giá trị rỗng/
        khoảng trắng không sinh cờ (không riêng gì cờ mới này)."""
        tl = {"reviewer_ref": "X", "g2_first_search_date": "   "}
        lenh = TK.soan_lenh("G2", "DE-TAI", Path("/x/a.md"), tl)
        assert "--g2-first-search-date" not in lenh
