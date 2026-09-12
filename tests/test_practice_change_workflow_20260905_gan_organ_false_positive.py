"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 19) trong app/scoring/practice_change.py::practice_change_score().

CƠ CHẾ LỖI: tuple từ khóa nhóm dễ tổn thương chứa "gan" (chỉ bệnh gan tiếng
Việt) kiểm bằng substring thô (`"gan" in text`, text đã lowercase). Chuỗi
con "gan" khớp bừa bên trong nhiều từ tiếng Anh hoàn toàn không liên quan
bệnh gan/nhóm dễ tổn thương: "organ" (cơ quan), "organic" (hữu cơ),
"reorganize" (tái tổ chức), "afghan", "morgan"... Một bài về "organ
transplant outcomes" (kết cục ghép tạng) hay "organic compound" bị cộng
nhầm breakdown["vulnerable_pop"]=6, làm practice_change_score cao giả tạo
cho các bài không hề liên quan tới nhóm bệnh nhân dễ tổn thương.

BẢN VÁ: bỏ "gan" khỏi tuple substring, thêm regex `\\bgan\\b` (_GAN_RE)
kiểm RIÊNG — đòi ranh giới từ ở cả hai đầu nên vẫn khớp đúng "gan" đứng một
mình trong các cụm tiếng Việt luôn cách nhau bằng khoảng trắng ("bệnh gan",
"suy gan", "xơ gan", "viêm gan") mà không khớp bừa vào giữa "organ" (trước
"gan" trong "organ" là "r", không phải ranh giới từ).

Nguyên tắc viết test: gọi THẲNG practice_change_score() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scoring.practice_change import practice_change_score  # noqa: E402


class TestOrganKhongBiGanNhamBenhGan:
    """★★★ Ca chính — chuỗi con "gan" không được khớp bừa bên trong các từ
    tiếng Anh chứa "organ"/"organic" không liên quan bệnh gan."""

    def test_organ_transplant_khong_bi_gan_nham_nhom_de_ton_thuong(self):
        _, breakdown = practice_change_score(
            {"title": "Organ transplant outcomes in the ICU", "abstract": "x"})
        assert "vulnerable_pop" not in breakdown, (
            "TRƯỚC bản vá: 'gan' trong tuple substring khớp bừa chuỗi con "
            "bên trong 'organ', gán nhầm bài về ghép tạng thành bài về "
            "nhóm dễ tổn thương/bệnh gan"
        )

    def test_organic_compound_khong_bi_gan_nham(self):
        _, breakdown = practice_change_score(
            {"title": "An organic compound with novel bioactivity", "abstract": "x"})
        assert "vulnerable_pop" not in breakdown

    def test_reorganize_khong_bi_gan_nham(self):
        _, breakdown = practice_change_score(
            {"abstract": "The hospital plans to reorganize its outpatient workflow"})
        assert "vulnerable_pop" not in breakdown

    def test_afghan_khong_bi_gan_nham(self):
        _, breakdown = practice_change_score(
            {"title": "Health system reconstruction in Afghan provinces", "abstract": "x"})
        assert "vulnerable_pop" not in breakdown


class TestBenhGanThatVanDuocNhanDienDung:
    """Đối chứng bắt buộc — các cụm tiếng Việt về bệnh gan THẬT (luôn cách
    nhau bằng khoảng trắng) vẫn được nhận diện đúng như trước bản vá."""

    def test_benh_gan_man_tinh_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "Bệnh gan mạn tính ở người cao tuổi", "abstract": "x"})
        assert breakdown.get("vulnerable_pop") == 6

    def test_suy_gan_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"abstract": "Bệnh nhân suy gan cấp cần theo dõi sát"})
        assert breakdown.get("vulnerable_pop") == 6

    def test_xo_gan_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "Xử trí biến chứng xơ gan mất bù", "abstract": "x"})
        assert breakdown.get("vulnerable_pop") == 6

    def test_hepatic_tieng_anh_van_duoc_nhan_dien(self):
        """Từ khóa tiếng Anh khác trong cùng tuple (không đụng tới bản vá)
        vẫn hoạt động như cũ."""
        _, breakdown = practice_change_score(
            {"title": "Dose adjustment in hepatic impairment", "abstract": "x"})
        assert breakdown.get("vulnerable_pop") == 6

    def test_elderly_van_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "Polypharmacy risk in elderly patients", "abstract": "x"})
        assert breakdown.get("vulnerable_pop") == 6
