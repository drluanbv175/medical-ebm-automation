"""Hồi quy phát hiện #2 (HIGH) của Workflow đối kháng đa-agent 2026-09-06 (vòng
29) trong tools/verify_direct_clinical_practice_readiness.py —
_has_trusted_source_type() khớp chuỗi con KHÔNG ranh giới từ cho các tên viết
tắt tổ chức uy tín NGẮN, tái diễn CHÍNH lỗ hổng mà app/sources/authority.py đã
được vá để chống (vòng 20, _AMBIGUOUS_SHORT_ALIASES).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _has_trusted_source_type(card):
        if match_authority_source(...):        # ← đã có ranh giới từ, AN TOÀN
            return True
        ...
        compact = _norm(joined)
        return any(term in compact for term in TRUSTED_SOURCE_TERMS + TRUSTED_AGENCY_TERMS)
                                                  #        ↑ khớp `in` THUẦN TÚY, KHÔNG ranh giới từ

`match_authority_source()` (app/sources/authority.py) ĐÃ được vá để dùng khớp
ranh giới từ (regex `(?<![a-z0-9])alias(?![a-z0-9])`) cho chính các tên viết
tắt ngắn dễ trùng từ tiếng Anh thông dụng (who/esc/acc/aga/ada/aha/gold...) —
xem `_AMBIGUOUS_SHORT_ALIASES`. Nhưng khi hàm đó trả None (không khớp — ĐÚNG,
vì văn bản không thật sự nhắc tới tổ chức nào), `_has_trusted_source_type()`
lại tự thử lại CHÍNH các tên viết tắt đó (TRUSTED_AGENCY_TERMS chứa đúng
kdigo/nejm/lancet/jama/bmj/cochrane/nice/who/cdc/fda/ema/mhra/acg/aga/esc/
aha/acc/ada/easl/aasld/gold — trùng gần như tuyệt đối với alias đã được
match_authority_source() bảo vệ) bằng `in` THUẦN TÚY, không có ranh giới từ —
mở lại đúng lỗ hổng đã đóng ở tầng dưới.

Hậu quả: một thẻ chứng cứ có `critical_appraisal` chứa các từ tiếng Anh rất
phổ biến — "descriptive" (chứa "esc"), "acceptable"/"access" (chứa "acc"),
"gold standard" (chứa "gold" — trớ trêu là cụm hay dùng để CHÊ thiết kế
thiếu gold standard), "whole" (chứa "who") — khiến hàm trả True dù nguồn
không hề liên quan tới tổ chức nào, làm sai lệch đúng cổng được thiết kế để
chặn "nguồn không đủ thẩm quyền".

BẢN VÁ: xoá TRUSTED_AGENCY_TERMS khỏi module — mọi tên viết tắt trong đó đã
có mặt trong TRUSTED_AUTHORITY_SOURCES (app/sources/authority.py) với khớp
ranh giới từ đúng đắn qua match_authority_source() ở NHÁNH TRƯỚC, nên nhánh
substring thô không thêm được năng lực phát hiện nào mới — chỉ thêm lại lỗ
hổng. Nhánh fallback chỉ còn TRUSTED_SOURCE_TERMS (từ mô tả THIẾT KẾ nghiên
cứu — dài, không trùng từ tiếng Anh thông dụng: "guideline", "systematic",
"meta-analysis", "rct", "randomized", "regulatory", "drug safety", "hta").

Nguyên tắc viết test:
1. Ca chính — các cụm chứa "esc"/"acc"/"gold" như một PHẦN của từ khác (không
   phải nhắc tới tổ chức) phải trả False.
2. Đối chứng — nguồn THẬT SỰ nhắc tới một tổ chức uy tín (WHO, NICE, Cochrane)
   vẫn phải trả True (qua match_authority_source(), không đổi hành vi).
3. Đối chứng — TRUSTED_SOURCE_TERMS (mô tả thiết kế nghiên cứu) vẫn hoạt động
   bình thường, không bị ảnh hưởng bởi việc xoá TRUSTED_AGENCY_TERMS."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import verify_direct_clinical_practice_readiness as V  # noqa: E402


def _card(source_type: str = "", agency: str = "", title: str = "",
          critical_appraisal: str = "", topic: str = "test") -> dict:
    return {
        "id": "test-card",
        "topic": topic,
        "source": {"type": source_type, "agency": agency, "title": title},
        "critical_appraisal": critical_appraisal,
    }


class TestKhongCoTinBaoDongGiaTuTuVietTatNgan:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. Từ tiếng Anh thông dụng chứa
    tên viết tắt tổ chức làm chuỗi con KHÔNG được coi là nhắc tới tổ chức đó."""

    def test_descriptive_khong_bi_hieu_thanh_esc(self):
        card = _card(
            source_type="case series",
            critical_appraisal="This is a descriptive study with limited external validity.",
        )
        assert V._has_trusted_source_type(card) is False, (
            "TRƯỚC bản vá: 'descriptive' chứa chuỗi con 'esc' — TRUSTED_AGENCY_TERMS "
            "khớp 'esc' bằng `in` không ranh giới từ, khiến hàm trả True sai dù bài "
            "không hề nhắc tới European Society of Cardiology."
        )

    def test_acceptable_khong_bi_hieu_thanh_acc(self):
        card = _card(
            source_type="retrospective chart review",
            critical_appraisal="No formal comparator; acceptable only as hypothesis-generating.",
        )
        assert V._has_trusted_source_type(card) is False

    def test_gold_standard_khong_bi_hieu_thanh_to_chuc_gold(self):
        card = _card(
            source_type="retrospective chart review",
            critical_appraisal="No gold standard comparator was used in this study.",
        )
        assert V._has_trusted_source_type(card) is False, (
            "TRƯỚC bản vá: cụm 'gold standard' (dùng để CHÊ thiết kế thiếu đối chứng "
            "chuẩn) chứa chuỗi con 'gold' — bị hiểu nhầm thành nhắc tới tổ chức GOLD "
            "(COPD guideline body), làm nguồn KÉM tin cậy lại được chấm là uy tín."
        )


class TestDoiChungToChucThatVanDuocNhanDien:
    """Đối chứng bắt buộc — nguồn THẬT SỰ nhắc tới tổ chức uy tín vẫn phải
    được nhận diện (qua match_authority_source(), không bị ảnh hưởng)."""

    def test_who_that_van_duoc_nhan_dien(self):
        card = _card(
            source_type="guideline",
            agency="World Health Organization",
            title="WHO guideline on hypertension",
            critical_appraisal="Official WHO guideline.",
        )
        assert V._has_trusted_source_type(card) is True

    def test_nice_that_van_duoc_nhan_dien(self):
        card = _card(
            source_type="guideline",
            agency="National Institute for Health and Care Excellence",
            title="NICE guideline",
        )
        assert V._has_trusted_source_type(card) is True

    def test_cochrane_that_van_duoc_nhan_dien(self):
        card = _card(
            source_type="systematic review",
            title="Cochrane Database Syst Rev",
        )
        assert V._has_trusted_source_type(card) is True


class TestDoiChungTrustedSourceTermsKhongDoi:
    """Đối chứng bắt buộc — TRUSTED_SOURCE_TERMS (mô tả thiết kế nghiên cứu,
    không phải tên tổ chức) không bị ảnh hưởng bởi việc xoá
    TRUSTED_AGENCY_TERMS."""

    def test_randomized_controlled_trial_van_duoc_nhan_dien(self):
        card = _card(source_type="randomized controlled trial")
        assert V._has_trusted_source_type(card) is True

    def test_systematic_review_van_duoc_nhan_dien(self):
        card = _card(source_type="systematic review")
        assert V._has_trusted_source_type(card) is True

    def test_nguon_hoan_toan_khong_lien_quan_van_tra_false(self):
        card = _card(
            source_type="expert opinion",
            critical_appraisal="Single-center case report, no comparator group.",
        )
        assert V._has_trusted_source_type(card) is False
