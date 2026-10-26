"""Load the hyphen-named scripts as modules."""

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def make_icons():
    return _load("make-icons")


@pytest.fixture
def make_notification_icon():
    return _load("make-notification-icon")
