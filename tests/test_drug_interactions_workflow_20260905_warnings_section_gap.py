"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 5, task #79) trong
`app/integrations/drug_interactions.py::DrugSafetyChecker.screen_pair()`.

CƠ CHẾ LỖI: `_LABEL_SECTIONS` khai 5 mục nhãn FDA (`boxed_warning`, `contraindications`,
`drug_interactions`, `warnings_and_cautions`, `warnings`) và `_parse_label()` trích ĐỦ cả 5 vào
`sections`. Nhưng `screen_pair()` (bản gốc) chỉ đối chiếu chéo drug_b với ĐÚNG 2/5 mục:
`drug_interactions` và `contraindications` — bỏ qua HẲN `warnings_and_cautions`/`warnings` dù
docstring đầu module tự khai "kéo các mục `drug_interactions`, `contraindications`,
`boxed_warning`, `warnings`".

HẬU QUẢ LÂM SÀNG: nhiều nhãn FDA (đặc biệt thuốc cũ, trước Physician Labeling Rule) đặt câu
cảnh báo phối hợp thuốc trong mục "Warnings and Precautions" thay vì mục "Drug Interactions"
riêng. Một cảnh báo phối hợp THẬT nằm ở đó bị bỏ sót HOÀN TOÀN — không có cờ `interaction`,
không có `warning`, không có gì báo hiệu bác sĩ biết drug_b được nhắc trong nhãn của drug_a.

BẢN VÁ: `_CROSS_REFERENCE_SECTIONS` mở rộng vòng lặp đối chiếu chéo sang cả 4 mục
(drug_interactions, contraindications, warnings_and_cautions, warnings) — `boxed_warning` CỐ Ý
không nằm trong nhóm đối chiếu chéo (đã có luồng riêng theo-từng-thuốc ở `screen_regimen()`).

Nguyên tắc viết test: gọi THẲNG `screen_pair()`/`screen_regimen()` thật qua nhãn giả lập có
thông tin CHỈ nằm ở `warnings_and_cautions`/`warnings` (không đặt ở `drug_interactions`/
`contraindications`), không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.integrations.drug_interactions import DrugSafetyChecker  # noqa: E402


class FakeHttp:
    """HttpClient giả — trả nhãn theo từ khóa trong params['search'] (giống
    tests/test_drug_interactions.py để tái dùng đúng khuôn fixture đã có)."""

    def __init__(self, labels):
        self.labels = labels

    def get_json(self, url, params=None, use_cache=True):
        search = (params or {}).get("search", "").lower()
        for key, result in self.labels.items():
            if key in search:
                return {"results": [result]}
        return {"results": []}


def _label(generic, *, warnings_and_cautions="", warnings="", brand=None):
    raw = {
        "openfda": {"generic_name": [generic], "brand_name": [brand or generic.title()],
                    "spl_set_id": ["SET-" + generic]},
        "set_id": "SET-" + generic,
    }
    if warnings_and_cautions:
        raw["warnings_and_cautions"] = [warnings_and_cautions]
    if warnings:
        raw["warnings"] = [warnings]
    return raw


def _checker(labels):
    return DrugSafetyChecker(http=FakeHttp(labels))


class TestScreenPairBatDuocCanhBaoOMucWarningsAndCautions:
    """★★★ Ca chính — cảnh báo phối hợp thuốc CHỈ nằm ở warnings_and_cautions (không có ở
    drug_interactions/contraindications) — bản gốc bỏ sót HOÀN TOÀN, không cờ nào."""

    def test_canh_bao_o_warnings_and_cautions_duoc_bat(self):
        labels = {
            "amiodarone": _label(
                "amiodarone",
                warnings_and_cautions=(
                    "Concomitant use with simvastatin doses greater than 20mg increases "
                    "the risk of myopathy and rhabdomyolysis."
                ),
            ),
            "simvastatin": _label("simvastatin"),
        }
        warns = _checker(labels).screen_regimen(["amiodarone", "simvastatin"])
        hits = [w for w in warns if w["type"] == "warning"]
        assert hits, "phải bắt được cảnh báo nằm ở warnings_and_cautions"
        assert set(hits[0]["drugs"]) == {"amiodarone", "simvastatin"}
        assert "simvastatin" in hits[0]["detail"].lower()

    def test_canh_bao_o_warnings_thuan_cung_duoc_bat(self):
        """Mục `warnings` (khác `warnings_and_cautions` — một số nhãn cũ dùng tên trường này)
        cũng phải được đối chiếu, không chỉ warnings_and_cautions."""
        labels = {
            "druga": _label("druga", warnings="May potentiate the effect of drugb on the CNS."),
            "drugb": _label("drugb"),
        }
        warns = _checker(labels).screen_regimen(["druga", "drugb"])
        hits = [w for w in warns if w["type"] == "warning"]
        assert hits and set(hits[0]["drugs"]) == {"druga", "drugb"}


class TestScreenPairKhongOverFlagKhiKhongNhac:
    """Đối chứng — không nhắc tới nhau trong bất kỳ mục nào (kể cả 2 mục mới) thì không có cờ."""

    def test_khong_nhac_toi_nhau_o_bat_ky_muc_moi_nao(self):
        labels = {
            "druga": _label("druga", warnings_and_cautions="Monitor renal function periodically."),
            "drugb": _label("drugb", warnings="Avoid alcohol during treatment."),
        }
        warns = _checker(labels).screen_regimen(["druga", "drugb"])
        assert not [w for w in warns if w["type"] in ("interaction", "contraindication", "warning")]


class TestScreenPairVanGiuHanhViCuChoHaiMucGoc:
    """Đối chứng bắt buộc — hai mục gốc (drug_interactions, contraindications) vẫn hoạt động
    y hệt trước bản vá, không bị ảnh hưởng bởi việc mở rộng sang 2 mục mới."""

    def test_drug_interactions_van_ra_type_interaction(self):
        labels = {
            "metoprolol": _label("metoprolol")
        }
        labels["metoprolol"]["drug_interactions"] = [
            "Use with verapamil may cause severe bradycardia."
        ]
        labels["verapamil"] = _label("verapamil")
        warns = _checker(labels).screen_regimen(["metoprolol", "verapamil"])
        inter = [w for w in warns if w["type"] == "interaction"]
        assert inter and inter[0]["severity"] == "cần rà"

    def test_contraindications_van_ra_type_contraindication(self):
        labels = {"druga": _label("druga")}
        labels["druga"]["contraindications"] = ["Contraindicated with drugb."]
        labels["drugb"] = _label("drugb")
        warns = _checker(labels).screen_regimen(["druga", "drugb"])
        ci = [w for w in warns if w["type"] == "contraindication"]
        assert ci and "nặng" in ci[0]["severity"]
