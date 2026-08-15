"""Test CLI hợp nhất công cụ tích hợp (offline — không gọi mạng/sub-main thật)."""
from __future__ import annotations

from app.integrations import cli


def test_list_runs(capsys):
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    for tool in ("drug", "soap", "image", "fhir"):
        assert tool in out
    assert "KHÔNG lưu PII" in out


def test_empty_and_help_show_list():
    assert cli.main([]) == 0
    assert cli.main(["--help"]) == 0
    assert cli.main(["-h"]) == 0


def test_unknown_tool_errors():
    assert cli.main(["khong_co"]) == 2


def test_dispatch_drug_routes_rest(monkeypatch):
    seen = {}

    def fake(rest):
        seen["rest"] = rest
        return 0

    monkeypatch.setattr("app.integrations.drug_interactions.main", fake)
    assert cli.main(["drug", "warfarin", "aspirin"]) == 0
    assert seen["rest"] == ["warfarin", "aspirin"]


def test_dispatch_soap_routes_rest(monkeypatch):
    seen = {}

    def fake(rest):
        seen["rest"] = rest
        return 0

    monkeypatch.setattr("app.integrations.ambient_scribe.main", fake)
    assert cli.main(["soap", "--transcript", "ca.txt"]) == 0
    assert seen["rest"] == ["--transcript", "ca.txt"]


def test_dispatch_image_routes_rest(monkeypatch):
    seen = {}

    def fake(rest):
        seen["rest"] = rest
        return 7  # propagate exit code

    monkeypatch.setattr("app.integrations.image_reading.main", fake)
    assert cli.main(["image", "x.jpg", "--modality", "ecg"]) == 7
    assert seen["rest"] == ["x.jpg", "--modality", "ecg"]
