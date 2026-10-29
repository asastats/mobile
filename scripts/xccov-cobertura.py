"""Turn one Swift file's line coverage from an Xcode result bundle into Cobertura XML.

Run in CI (standard library only):
xcrun xccov view --archive --json --file SOURCE RESULT | python3 scripts/xccov-cobertura.py ROOT
ROOT is the checkout; paths in the XML are relative to it, for Codecov.
See docs/logbook.md.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET


def executable_lines(entries):
    """Return (line number, execution count) for every executable line.

    :param entries: one file's list from `xccov view --archive --json`
    :return: list of (int, int), in line order
    """
    return sorted(
        (entry["line"], entry.get("executionCount") or 0)
        for entry in entries
        if entry.get("isExecutable")
    )


def cobertura(report, root):
    """Return a Cobertura document for every file in `report`.

    :param report: the parsed `xccov view --archive --json` output, path to lines
    :param root: directory the file names are made relative to
    :return: the XML as a string
    """
    covered_total = valid_total = 0
    document = ET.Element("coverage", version="1")
    ET.SubElement(ET.SubElement(document, "sources"), "source").text = root
    package = ET.SubElement(ET.SubElement(document, "packages"), "package", name="swift")
    classes = ET.SubElement(package, "classes")
    for path in sorted(report):
        lines = executable_lines(report[path])
        covered = sum(1 for _, hits in lines if hits)
        covered_total += covered
        valid_total += len(lines)
        element = ET.SubElement(
            classes,
            "class",
            name=os.path.splitext(os.path.basename(path))[0],
            filename=os.path.relpath(path, root),
            **{"line-rate": _rate(covered, len(lines)), "branch-rate": "0"},
        )
        rows = ET.SubElement(element, "lines")
        for number, hits in lines:
            ET.SubElement(rows, "line", number=str(number), hits=str(hits))
    document.set("lines-covered", str(covered_total))
    document.set("lines-valid", str(valid_total))
    document.set("line-rate", _rate(covered_total, valid_total))
    document.set("branch-rate", "0")
    return ET.tostring(document, encoding="unicode", xml_declaration=True)


def _rate(covered, valid):
    return str(covered / valid if valid else 1)


def main(argv, stdin, stdout):
    """Read the xccov JSON from `stdin` and write Cobertura XML to `stdout`.

    :param argv: command line; argv[1] is the checkout root
    :return: process exit status
    """
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    report = json.load(stdin)
    if not report:
        print("xccov reported no files", file=sys.stderr)
        return 1
    stdout.write(cobertura(report, os.path.abspath(argv[1])) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv, sys.stdin, sys.stdout))
