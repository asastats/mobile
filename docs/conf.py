"""Sphinx configuration; why each choice is in docs/logbook.md under docs/conf.py."""

import importlib.util
import json
import sys
from pathlib import Path

from sphinx.ext.autodoc.mock import mock

ROOT = Path(__file__).resolve().parent.parent

project = "ASA Stats app"
copyright = "2026, ASA Stats DAO"
author = "Ivica Paleka"
release = json.loads((ROOT / "package.json").read_text())["version"]

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon", "myst_parser"]
source_suffix = [".rst", ".md"]
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "logbook.md"]

# Not installed by requirements-docs.txt, and never needed to read a docstring.
autodoc_mock_imports = ["PIL", "appium", "selenium", "pytest"]

# The icon scripts have hyphens in their names, so automodule cannot import them.
# They are loaded here, under the mocks, because they import Pillow at the top.
with mock(autodoc_mock_imports):
    for _name, _file in {
        "make_icons": "make-icons.py",
        "make_notification_icon": "make-notification-icon.py",
    }.items():
        _spec = importlib.util.spec_from_file_location(_name, ROOT / "scripts" / _file)
        sys.modules[_name] = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(sys.modules[_name])

sys.path.insert(0, str(ROOT / "functional_tests"))

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

latex_documents = [
    ("index", "asastats-app.tex", "ASA Stats app documentation", author, "howto")
]
