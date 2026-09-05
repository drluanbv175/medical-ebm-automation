"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 20) trong app/sources/authority.py + app/sources/classify_meta.py.

CƠ CHẾ LỖI: `_AMBIGUOUS_SHORT_ALIASES` (authority.py) chỉ chặn bí danh NGẮN
(≤4 ký tự: who/ada/acc/aha/esc/acr/ema/ash/ags/gold/gut/nice). Nhưng nhiều
bí danh DÀI hơn cũng là từ tiếng Anh/thuật ngữ y khoa thông dụng, trùng bí
danh tổ chức uy tín: "circulation" (ACC/AHA), "thorax" (ATS/ERS/BTS), "gina"
(GINA — cũng là tên người phổ biến), "hepatology"/"gastroenterology"
(AASLD/EASL và ACG/AGA/ASGE — tên CHUYÊN KHOA y học), "lancet" (The Lancet
— cũng là tên dụng cụ y khoa "kim chích máu mao mạch"). Vì không nằm trong
`_AMBIGUOUS_SHORT_ALIASES`, các bí danh này được đối chiếu với `combined`
(GỘP CẢ title/authors) thay vì chỉ `primary_blob` (journal) — một bài về
"Collateral circulation after stroke" (không liên quan ACC/AHA) bị gắn
nhãn nguồn uy tín Tier A + cộng 5 điểm, đủ để lật ngưỡng Tier C→B/B→A ở
app/scoring/reliability.py.

Đây CÙNG LỚP LỖI đã vá cho "nice" (vòng 2, 04/09/2026): bản sao RIÊNG của
cùng danh sách chống-mơ-hồ tồn tại ở classify_meta.py::_AMBIGUOUS_ORG_SIGNALS
(dùng cho detect_official_org()::OFFICIAL_ORG_SIGNALS) — vá một nơi không
đóng được lỗ hổng ở tầng detect_official_org(), vì hàm đó rơi xuống
OFFICIAL_ORG_SIGNALS ngay khi match_authority_source() không khớp.

BẢN VÁ: thêm 6 alias (circulation/thorax/gina/hepatology/gastroenterology/
lancet) vào authority.py::_AMBIGUOUS_SHORT_ALIASES, và 3 alias trong số đó
có mặt trong classify_meta.py::OFFICIAL_ORG_SIGNALS (circulation/gina/
hepatology) vào classify_meta.py::_AMBIGUOUS_ORG_SIGNALS.

Nguyên tắc viết test: gọi THẲNG authority_breakdown_for()/match_authority_
source()/detect_official_org() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.authority import authority_breakdown_for  # noqa: E402
from app.sources.classify_meta import detect_official_org  # noqa: E402


class TestAliasDaiKhongConKhopBuaTrongTieuDe:
    """★★★ Ca chính — 6 alias dài/từ thông dụng không được khớp bừa khi CHỈ
    xuất hiện trong title/authors (không phải journal)."""

    def test_circulation_trong_tieu_de_khong_bi_gan_nham_acc_aha(self):
        source, breakdown = authority_breakdown_for(
            ("Local Journal of Physiology", "pubmed", "Doe A",
             "Collateral circulation after stroke: a single-center retrospective study"))
        assert source is None, (
            "TRƯỚC bản vá: 'circulation' không nằm trong _AMBIGUOUS_SHORT_ALIASES, "
            "khớp bừa vào tiêu đề không liên quan ACC/AHA"
        )
        assert breakdown == {}

    def test_thorax_trong_tieu_de_khong_bi_gan_nham_ats_ers_bts(self):
        source, _ = authority_breakdown_for(
            ("Local Trauma Journal", "pubmed", "Doe A",
             "Penetrating trauma to the thorax: a case series"))
        assert source is None

    def test_gina_ten_tac_gia_khong_bi_gan_nham_to_chuc_gina(self):
        source, _ = authority_breakdown_for(
            ("Local Journal", "pubmed", "Rossi Gina", "A cohort study of unrelated topic"))
        assert source is None

    def test_hepatology_trong_tieu_de_khong_bi_gan_nham_aasld_easl(self):
        source, _ = authority_breakdown_for(
            ("Local Journal", "pubmed", "Doe A",
             "Alcohol use and hepatology outcomes in a rural cohort"))
        assert source is None

    def test_gastroenterology_trong_tieu_de_khong_bi_gan_nham_acg_aga_asge(self):
        source, _ = authority_breakdown_for(
            ("Local Journal", "pubmed", "Doe A",
             "A retrospective review of gastroenterology consult patterns in a rural ED"))
        assert source is None

    def test_lancet_dung_cu_y_khoa_trong_tieu_de_khong_bi_gan_nham_tap_chi_lancet(self):
        source, _ = authority_breakdown_for(
            ("Local Journal", "pubmed", "Doe A",
             "Comparing lancet devices for capillary blood glucose testing in diabetes"))
        assert source is None


class TestAliasThatOJournalVanNhanDienDung:
    """Đối chứng bắt buộc — 6 alias THẬT khi xuất hiện đúng vị trí journal
    (primary_blob) vẫn được nhận diện đúng như trước bản vá."""

    def test_circulation_o_journal_van_khop_acc_aha(self):
        source, _ = authority_breakdown_for(
            ("Circulation", "pubmed", "Doe A", "A study of unrelated topic"))
        assert source is not None
        assert source.name == "ACC/AHA"

    def test_lancet_o_journal_van_khop_the_lancet(self):
        source, _ = authority_breakdown_for(
            ("The Lancet", "pubmed", "Doe A", "A study of unrelated topic"))
        assert source is not None
        assert source.name == "The Lancet"

    def test_thorax_o_journal_van_khop_ats_ers_bts(self):
        source, _ = authority_breakdown_for(
            ("Thorax", "pubmed", "Doe A", "A study of unrelated topic"))
        assert source is not None
        assert source.name == "ATS/ERS/BTS"


class TestClassifyMetaFallbackCungKhongConKhopBua:
    """★★★ Ca chính (lớp thứ hai) — detect_official_org() rơi xuống
    OFFICIAL_ORG_SIGNALS khi match_authority_source() không khớp; bản sao
    ở classify_meta.py cũng phải được vá đồng thời."""

    def test_circulation_qua_detect_official_org_khong_gan_nham(self):
        result = detect_official_org(
            "Collateral circulation after stroke: a single-center retrospective study",
            "Local Journal of Physiology", "Doe A")
        assert result != "AHA"
        assert result is None

    def test_gina_qua_detect_official_org_khong_gan_nham(self):
        result = detect_official_org(
            "A cohort study of unrelated topic", "Local Journal", "Rossi Gina")
        assert result != "GINA"
        assert result is None

    def test_hepatology_qua_detect_official_org_khong_gan_nham(self):
        result = detect_official_org(
            "Alcohol use and hepatology outcomes in a rural cohort",
            "Local Journal", "Doe A")
        assert result != "AASLD"
        assert result is None


class TestDoiChungCacBiDanhMoHoKhacKhongDoiHanhVi:
    """Đối chứng bắt buộc — các bí danh mơ hồ ĐÃ ĐÚNG từ trước (who/ada/
    gold/nice...) không bị ảnh hưởng bởi việc thêm 6 alias mới."""

    def test_nice_van_khong_khop_trong_cau_thuong(self):
        result = detect_official_org(
            "A nice case series of unusual dermatology presentations",
            "Case Reports in Dermatology")
        assert result != "NICE"

    def test_ada_journal_that_van_khop_dung(self):
        source, _ = authority_breakdown_for(
            ("Diabetes Care", "pubmed", "Doe A", "A study of unrelated topic"))
        assert source is not None
        assert source.name == "ADA/EASD"
