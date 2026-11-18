"""Lời dặn kiểm máy Claude API sửa theo nhãn bác sĩ (18/11/2026) — khoá các quy tắc chống báo nhầm đã đo.

Bác sĩ gắn nhãn 17 phát hiện của lượt kiểm BTM: tỷ lệ đúng 41% (A12 1/5; «hỗ trợ một phần» 0/4; phản biện máy 6/12).
Quy tắc thêm vào lời dặn được rút từ đúng các kiểu báo nhầm đó. Chạy lại cùng đề cương: A12 khớp 5/5 nhãn (1 đúng còn
báo, 4 nhầm hết, 0 nhầm mới); phản biện máy hết 4/6 kiểu nhầm (tự cộng số, phiên bản phần mềm, mã biến CRF, khung mẫu).
Test khoá để quy tắc không bị xoá âm thầm; độ đúng thật đo bằng nhãn bác sĩ theo `loi_dan_sha256` của từng báo cáo.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402


@pytest.mark.parametrize("cum", [
    "phần câu gắn với số trích dẫn KHÁC trong cùng câu không thuộc [n]",  # mục 4: định nghĩa trích [3], không [39]
    "được chống đỡ CHUNG",  # mục 5: [38, 41]
    "siêu dữ liệu thư mục",  # mục 2: tên tác giả, năm
    "ĐÚNG CHỦ ĐỀ",  # mục 3: câu chung «được tham khảo»
    "gắn RIÊNG cho tài liệu này",  # định nghĩa hẹp lại của ho_tro_mot_phan
])
def test_loi_dan_a12_giu_quy_tac_chong_bao_nham(cum):
    assert cum in KND.HE_THONG


@pytest.mark.parametrize("cum", [
    "cộng/đối chiếu lại; số khớp thì KHÔNG ghi",  # mục 8
    "thiết kế của MỘT NGHIÊN CỨU ĐƯỢC TRÍCH khác thiết kế của đề tài",  # mục 10
    "«không có thật» khi văn bản không tự mâu thuẫn",  # mục 12
    "cỡ mẫu cần trích khác kích thước khung mẫu",  # mục 14
    "cột mã biến đặt cạnh nội dung tiếng Việt",  # mục 13
    "đã đối chiếu bảng viết tắt",  # mục 15
])
def test_loi_dan_phan_bien_giu_quy_tac_chong_bao_nham(cum):
    assert cum in " ".join(PBM.HE_THONG.split())  # lời dặn ngắt dòng trong mã ⇒ chuẩn hoá khoảng trắng


def test_bao_cao_a12_ghi_dau_loi_dan(tmp_path):
    from tests.test_api_claude_nghien_cuu_20261117 import ABS, KhachGia, _goc_tam, _tra_knd

    goc = _goc_tam(tmp_path)
    KND.main(["--study", "S1", "--goi-api"], client=KhachGia(_tra_knd), lay=lambda p: ABS, goc=goc)
    js = json.loads((goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    assert js["loi_dan_sha256"] == hashlib.sha256(KND.HE_THONG.encode("utf-8")).hexdigest()[:12]
