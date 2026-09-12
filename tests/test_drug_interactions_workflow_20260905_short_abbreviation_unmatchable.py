"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 17) trong app/integrations/drug_interactions.py::_mentions().

CƠ CHẾ LỖI: `_mentions()` khớp một thuốc (hoặc hoạt chất) trong văn bản
nhãn bằng `\\b<term>\\b`, nhưng lọc trước các CANDIDATE bằng `len(c) >= 4`.
Với một tên thuốc VIẾT TẮT ≤3 ký tự — "ASA" (aspirin, viết tắt lâm sàng
rất phổ biến) là ví dụ điển hình — `candidates = {"asa"}` (từ gốc trùng cả
cụm vì chỉ có một từ) bị lọc HẾT bởi ngưỡng độ dài, khiến `any(...)` rỗng
→ `_mentions()` LUÔN trả `False`, kể cả khi nhãn ghi đúng "...concomitant
use with ASA...". Đây là sàng lọc TƯƠNG TÁC THUỐC — bỏ sót một cảnh báo
tương tác thật với aspirin (một thuốc thường trực trong sàng lọc chảy
máu/kháng đông) là hại lâm sàng thật, và không có tín hiệu lỗi nào báo
hiệu (không phải `not_found`/`lookup_failed` — `screen_pair()` chỉ đơn
giản không sinh cờ nào).

BẢN VÁ: hạ ngưỡng lọc từ `len(c) >= 4` xuống `len(c) >= 3`. Ranh giới
`\\b...\\b` đã tự loại các khớp substring giả (vd "asa" không khớp bên
trong "causally"), nên ngưỡng độ dài chỉ còn cần chặn từ 1-2 ký tự cực
chung chung ("a", "in", "of"...).

Nguyên tắc viết test: gọi THẲNG `DrugSafetyChecker.screen_regimen()` thật
qua một HttpClient giả trả nhãn theo từ khóa tìm kiếm (không mock mạng
thật, không mock hàm `_mentions` — kiểm hành vi đầu-cuối)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.integrations.drug_interactions import DrugSafetyChecker  # noqa: E402


class FakeHttp:
    """HttpClient giả: trả nhãn theo từ khóa trong params['search']."""

    def __init__(self, labels):
        self.labels = labels

    def get_json(self, url, params=None, use_cache=True):
        search = (params or {}).get("search", "").lower()
        for key, result in self.labels.items():
            if key in search:
                return {"results": [result]}
        return {"results": []}


def _label(generic, *, interactions="", brand=None):
    raw = {
        "openfda": {"generic_name": [generic], "brand_name": [brand or generic.title()],
                    "spl_set_id": ["SET-" + generic]},
        "set_id": "SET-" + generic,
    }
    if interactions:
        raw["drug_interactions"] = [interactions]
    return raw


class TestVietTatBaKyTuPhaiKhopDungNhuTenDay:
    """★★★ Ca chính — tên/viết tắt thuốc ≤3 ký tự PHẢI được khớp bằng \\b khi
    xuất hiện đúng như một từ trong nhãn, giống hệt tên đầy đủ."""

    def test_asa_duoc_nhan_dien_trong_tuong_tac_warfarin(self):
        labels = {
            "warfarin": _label(
                "warfarin",
                interactions="Concomitant use with ASA (acetylsalicylic acid) "
                             "markedly increases bleeding risk.",
            ),
            "asa": _label("asa"),
        }
        chk = DrugSafetyChecker(http=FakeHttp(labels))
        warns = chk.screen_regimen(["warfarin", "ASA"])
        inter = [w for w in warns if w["type"] == "interaction"]
        assert inter, (
            "TRƯỚC bản vá: ngưỡng len(c)>=4 lọc hết candidate của 'ASA' (3 ký "
            "tự) nên _mentions() luôn trả False — không cờ tương tác nào được "
            "sinh ra dù nhãn ghi rõ 'ASA' trong mục tương tác"
        )
        assert set(inter[0]["drugs"]) == {"warfarin", "ASA"}

    def test_mtx_ba_ky_tu_cung_duoc_nhan_dien(self):
        labels = {
            "leflunomide": _label(
                "leflunomide",
                interactions="Increased hepatotoxicity risk when combined with MTX.",
            ),
            "mtx": _label("mtx"),
        }
        chk = DrugSafetyChecker(http=FakeHttp(labels))
        warns = chk.screen_regimen(["leflunomide", "MTX"])
        inter = [w for w in warns if w["type"] == "interaction"]
        assert inter, "MTX (methotrexate, viết tắt 3 ký tự phổ biến) phải được khớp"


class TestTenThuocDaiVaKhongLienQuanVanGiuHanhViCu:
    """Đối chứng bắt buộc — tên thuốc ≥4 ký tự (hành vi gốc) và các cặp
    không liên quan vẫn hoạt động đúng như trước bản vá."""

    def test_ten_day_du_4_ky_tu_van_khop_nhu_cu(self):
        labels = {
            "metoprolol": _label(
                "metoprolol",
                interactions="Use with verapamil may cause severe bradycardia.",
            ),
            "verapamil": _label("verapamil"),
        }
        chk = DrugSafetyChecker(http=FakeHttp(labels))
        warns = chk.screen_regimen(["metoprolol", "verapamil"])
        inter = [w for w in warns if w["type"] == "interaction"]
        assert inter and set(inter[0]["drugs"]) == {"metoprolol", "verapamil"}

    def test_khong_lien_quan_van_khong_co_co_gia(self):
        labels = {
            "paracetamol": _label("paracetamol", interactions="May interact with warfarin."),
            "amoxicillin": _label("amoxicillin", interactions="May reduce efficacy of oral contraceptives."),
        }
        chk = DrugSafetyChecker(http=FakeHttp(labels))
        warns = chk.screen_regimen(["paracetamol", "amoxicillin"])
        assert not [w for w in warns if w["type"] in ("interaction", "contraindication")]

    def test_mot_ky_tu_khong_bi_lam_dung_de_khop_bua_bai(self):
        """Đảm bảo hạ ngưỡng xuống 3 KHÔNG mở đường cho 1-2 ký tự khớp bừa
        (vd nhãn mô tả liều "od" hoặc tên viết tắt cực ngắn không thật)."""
        labels = {
            "drugx": _label("drugx", interactions="Take with food, not on an empty stomach."),
            "od": _label("od"),
        }
        chk = DrugSafetyChecker(http=FakeHttp(labels))
        warns = chk.screen_regimen(["drugx", "od"])
        inter = [w for w in warns if w["type"] == "interaction"]
        assert not inter, "candidate 2 ký tự ('od') vẫn phải bị lọc bởi len(c)>=3"
