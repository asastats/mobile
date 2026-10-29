"""Tests for scripts/xccov-cobertura.py, on xccov JSON written by hand."""

import io
import json
import xml.etree.ElementTree as ET

ROOT = "/work/mobile"
SOURCE = f"{ROOT}/plugins/applock/ios/Sources/AppLockPlugin/LockPolicy.swift"
REPORT = {
    SOURCE: [
        {"line": 3, "isExecutable": True, "executionCount": 0},
        {"line": 1, "isExecutable": True, "executionCount": 4, "subranges": []},
        {"line": 2, "isExecutable": False},
        {"line": 4, "isExecutable": True},
    ]
}


def test_executable_lines_skips_the_rest_and_sorts(xccov_cobertura):
    assert xccov_cobertura.executable_lines(REPORT[SOURCE]) == [(1, 4), (3, 0), (4, 0)]


def test_cobertura_relative_names_and_rates(xccov_cobertura):
    document = ET.fromstring(xccov_cobertura.cobertura(REPORT, ROOT))
    assert document.find("sources/source").text == ROOT
    assert (document.get("lines-covered"), document.get("lines-valid")) == ("1", "3")
    assert float(document.get("line-rate")) == 1 / 3
    element = document.find("packages/package/classes/class")
    assert element.get("name") == "LockPolicy"
    assert element.get("filename") == "plugins/applock/ios/Sources/AppLockPlugin/LockPolicy.swift"
    assert [(line.get("number"), line.get("hits")) for line in element.iter("line")] == [
        ("1", "4"),
        ("3", "0"),
        ("4", "0"),
    ]


def test_cobertura_file_without_executable_lines_is_full(xccov_cobertura):
    document = ET.fromstring(xccov_cobertura.cobertura({SOURCE: []}, ROOT))
    assert document.get("line-rate") == "1"


def test_main_writes_the_xml(xccov_cobertura):
    out = io.StringIO()
    assert xccov_cobertura.main(["x", ROOT], io.StringIO(json.dumps(REPORT)), out) == 0
    assert out.getvalue().startswith("<?xml")
    assert ET.fromstring(out.getvalue()).get("lines-valid") == "3"


def test_main_needs_the_root(xccov_cobertura, capsys):
    assert xccov_cobertura.main(["x"], io.StringIO("{}"), io.StringIO()) == 2
    assert "ROOT" in capsys.readouterr().err


def test_main_refuses_an_empty_report(xccov_cobertura, capsys):
    assert xccov_cobertura.main(["x", ROOT], io.StringIO("{}"), io.StringIO()) == 1
    assert "no files" in capsys.readouterr().err
