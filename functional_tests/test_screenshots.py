"""Store screenshots of the live site in the app, one PNG per scene in screenshots.json.

Run only by .github/workflows/screenshots.yml (marker `screenshots`).
"""

import json
import os
import struct
import time
from pathlib import Path

import pytest
from appium import webdriver

from conftest import PASSWORD, PLATFORM, SITE, android_options, ios_options, native, sign_in, site_loaded, wait

pytestmark = pytest.mark.screenshots

HERE = Path(__file__).resolve().parent
SCENES = json.loads((HERE / "screenshots.json").read_text())
#: Values for the `{address}` / `{bundle}` placeholders in the scene paths.
VALUES = {
    "address": os.environ.get("ASASTATS_SCREENSHOT_ADDRESS", ""),
    "bundle": os.environ.get("ASASTATS_SCREENSHOT_BUNDLE", ""),
}
#: The store slot, also the output folder name: iphone, ipad, phone, seven-inch, ten-inch.
SLOT = os.environ.get("ASASTATS_SCREENSHOT_SLOT", PLATFORM)
OUTPUT = Path(os.environ.get("ASASTATS_SCREENSHOTS_DIR", HERE / "screenshots")) / SLOT
#: "1320x2868": the size the store slot needs; empty skips the check.
SIZE = os.environ.get("ASASTATS_SCREENSHOT_SIZE", "")
#: Seconds after `ready` for charts and htmx swaps to finish drawing.
SETTLE = 5


def png_size(path):
    """Return (width, height) from a PNG's IHDR chunk."""
    return struct.unpack(">II", path.read_bytes()[16:24])


@pytest.fixture(scope="module")
def session():
    options = ios_options() if PLATFORM == "ios" else android_options()
    driver = webdriver.Remote(os.environ.get("APPIUM_URL", "http://127.0.0.1:4723"), options=options)
    native(driver)
    driver.orientation = "PORTRAIT"
    site_loaded(driver)
    # Signed in only with the demo account's secrets; conftest's USER has a local default.
    if os.environ.get("APP_TEST_USER") and PASSWORD:
        sign_in(driver)
    yield driver
    driver.quit()


@pytest.mark.parametrize("scene", SCENES, ids=[scene["name"] for scene in SCENES])
def test_scene(session, scene):
    try:
        path = scene["path"].format(**VALUES)
    except KeyError as error:
        pytest.fail(f"unknown placeholder {error} in {scene['name']}")
    if path.rstrip("/") == "" and scene["path"] != "/":
        pytest.skip("no value for this scene's placeholder")

    driver = session
    site_loaded(driver)
    theme = scene.get("theme")
    driver.execute_script(
        "arguments[0] ? localStorage.setItem('theme', arguments[0]) : localStorage.removeItem('theme');",
        theme,
    )
    driver.get(f"{SITE}{path}")
    site_loaded(driver)
    wait(driver, lambda d: d.execute_script("return !!document.querySelector(arguments[0]);", scene["ready"]))
    wait(driver, lambda d: d.execute_script("return !document.querySelector('.htmx-request');"))
    if scene.get("scroll_to"):
        driver.execute_script("document.querySelector(arguments[0]).scrollIntoView({block: 'start'});", scene["scroll_to"])
    time.sleep(SETTLE)

    native(driver)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{scene['name']}.png"
    driver.get_screenshot_as_file(str(target))

    if SIZE:
        assert "x".join(map(str, png_size(target))) == SIZE, f"{target.name} is not {SIZE}"
