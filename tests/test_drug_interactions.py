"""Test sàng lọc tương tác thuốc openFDA (offline — inject HttpClient giả, không gọi mạng).

Phủ: parse nhãn · cờ tương tác/CCĐ chéo · boxed_warning · không-tìm-thấy · lỗi tra · không over-flag.
"""
from __future__ import annotations

import pytest

from app.integrations.drug_interactions import (
    DISCLAIMER,
    DrugInteractionError,
    DrugSafetyChecker,
)


class FakeHttp:
    """HttpClient giả: trả nhãn theo từ khóa trong params['search']."""

    def __init__(self, labels):
        # labels: {generic_lowercase: result_dict}
        self.labels = labels
        self.calls = []

    def get_json(self, url, params=None, use_cache=True):
        self.calls.append(params)
        search = (params or {}).get("search", "").lower()
        for key, result in self.labels.items():
            if key in search:
                return {"results": [result]}
        return {"results": []}


def _label(generic, *, interactions="", contraindications="", boxed="", brand=None):
    raw = {
        "openfda": {"generic_name": [generic], "brand_name": [brand or generic.title()],
                    "spl_set_id": ["SET-" + generic]},
        "set_id": "SET-" + generic,
    }
    if interactions:
        raw["drug_interactions"] = [interactions]
    if contraindications:
        raw["contraindications"] = [contraindications]
    if boxed:
        raw["boxed_warning"] = [boxed]
    return raw


def _checker(labels):
    return DrugSafetyChecker(http=FakeHttp(labels))


# -- Tra & parse nhãn ------------------------------------------------------
def test_fetch_label_parses_sections():
    chk = _checker({"metoprolol": _label("metoprolol",
                    interactions="Concomitant use with verapamil may cause bradycardia.")})
    lab = chk.fetch_label("metoprolol")
    assert lab is not None
    assert "metoprolol" in [g.lower() for g in lab["generic_names"]]
    assert "verapamil" in lab["sections"]["drug_interactions"].lower()
    assert lab["source"].startswith("openFDA label")


def test_fetch_label_empty_drug_raises():
    chk = _checker({})
    with pytest.raises(DrugInteractionError):
        chk.fetch_label("  ")


def test_fetch_label_not_found_returns_none():
    chk = _checker({})
    assert chk.fetch_label("khongtontai") is None


# -- Sàng lọc cặp / đơn ----------------------------------------------------
def test_regimen_flags_cross_interaction():
    labels = {
        "metoprolol": _label("metoprolol",
                             interactions="Use with verapamil may cause severe bradycardia and AV block."),
        "verapamil": _label("verapamil"),
    }
    warns = _checker(labels).screen_regimen(["metoprolol", "verapamil"])
    inter = [w for w in warns if w["type"] == "interaction"]
    assert inter, "phải có cờ tương tác chéo"
    assert set(inter[0]["drugs"]) == {"metoprolol", "verapamil"}
    assert inter[0]["source"].startswith("openFDA label")
    assert inter[0]["disclaimer"] == DISCLAIMER


def test_regimen_flags_contraindication_as_severe():
    labels = {
        "druga": _label("druga", contraindications="Contraindicated with drugb due to QT prolongation."),
        "drugb": _label("drugb"),
    }
    warns = _checker(labels).screen_regimen(["druga", "drugb"])
    ci = [w for w in warns if w["type"] == "contraindication"]
    assert ci and "nặng" in ci[0]["severity"]


def test_regimen_boxed_warning_per_drug():
    labels = {"warfarin": _label("warfarin", boxed="WARNING: bleeding risk can be fatal.")}
    warns = _checker(labels).screen_regimen(["warfarin"])
    boxed = [w for w in warns if w["type"] == "boxed_warning"]
    assert boxed and "warfarin" in boxed[0]["drugs"]


def test_regimen_no_false_flag_when_unrelated():
    labels = {
        "paracetamol": _label("paracetamol", interactions="May interact with warfarin."),
        "amoxicillin": _label("amoxicillin", interactions="May reduce efficacy of oral contraceptives."),
    }
    warns = _checker(labels).screen_regimen(["paracetamol", "amoxicillin"])
    # Không thuốc nào nhắc thuốc kia → không có cờ interaction/contraindication.
    assert not [w for w in warns if w["type"] in ("interaction", "contraindication")]


def test_regimen_reports_not_found():
    labels = {"metoprolol": _label("metoprolol")}
    warns = _checker(labels).screen_regimen(["metoprolol", "thuoc_la"])
    nf = [w for w in warns if w["type"] == "not_found"]
    assert nf and "thuoc_la" in nf[0]["drugs"]


def test_regimen_handles_lookup_error_gracefully():
    class BoomHttp:
        def get_json(self, url, params=None, use_cache=True):
            raise RuntimeError("network down")

    warns = DrugSafetyChecker(http=BoomHttp()).screen_regimen(["metoprolol"])
    assert any(w["type"] == "lookup_failed" for w in warns)
