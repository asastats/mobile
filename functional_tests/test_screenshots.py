"""Store screenshots of the live site in the app, one PNG per scene in screenshots.json.

Run only by .github/workflows/screenshots.yml (marker `screenshots`).
"""

import json
import os
import string
import struct
import time
from pathlib import Path

import pytest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy

from conftest import PASSWORD, PLATFORM, SITE, android_options, ios_options, native, sign_in, site_loaded, wait

pytestmark = pytest.mark.screenshots

HERE = Path(__file__).resolve().parent
SCENES = json.loads((HERE / "screenshots.json").read_text())
#: Values for the `{address}` / `{bundle}` placeholders in the scene paths.
VALUES = {
    "address": os.environ.get("ASASTATS_SCREENSHOT_ADDRESS", ""),
    "bundle": os.environ.get("ASASTATS_SCREENSHOT_BUNDLE", ""),
}
#: The store slot, also the output folder name (screenshots.yml lists them).
SLOT = os.environ.get("ASASTATS_SCREENSHOT_SLOT", PLATFORM)
OUTPUT = Path(os.environ.get("ASASTATS_SCREENSHOTS_DIR", HERE / "screenshots")) / SLOT
#: "1206x2622|1179x2556": the sizes the store slot accepts; empty skips the check.
SIZES = [size for size in os.environ.get("ASASTATS_SCREENSHOT_SIZE", "").split("|") if size]
#: PORTRAIT, or LANDSCAPE for Play's desktop slot.
ORIENTATION = os.environ.get("ASASTATS_SCREENSHOT_ORIENTATION", "PORTRAIT")
#: Seconds after `ready` for charts and htmx swaps to finish drawing; a scene's `settle` overrides it.
SETTLE = 5
#: Floating controls that cover content in a still picture.
HIDDEN = "#scroll-to-top"
# Element top below the iOS status bar (safe-area inset) with a small margin; the strip
# behind the bar gets the page background, so scrolled-past content does not show there.
SCROLL_TO = (
    "var cover = document.createElement('div');"
    "cover.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; z-index: 2147483647;"
    " height: env(safe-area-inset-top, 0px);';"
    "cover.style.background = getComputedStyle(document.body).backgroundColor;"
    "document.body.appendChild(cover);"
    "var inset = cover.getBoundingClientRect().height;"
    "var el = document.querySelector(arguments[0]);"
    "if (!el) throw new Error('nothing matches ' + arguments[0]);"
    "var top = el.getBoundingClientRect().top + window.scrollY;"
    "window.scrollTo(0, Math.max(0, top - inset - 12));"
)
#: Signed in as the demo account; conftest's USER has a local default, so test the variable.
SIGNED_IN = bool(os.environ.get("APP_TEST_USER") and PASSWORD)
#: True once every image of `arguments[0]` inside the viewport has loaded (lazy ones below it never do).
IMAGES_DRAWN = """
var box = document.querySelector(arguments[0]);
return Array.from(box.querySelectorAll('img')).every(function (img) {
  var r = img.getBoundingClientRect();
  return img.complete || r.bottom < 0 || r.top > window.innerHeight || !r.width;
});
"""


def png_size(path):
    """Return (width, height) from a PNG's IHDR chunk."""
    return struct.unpack(">II", path.read_bytes()[16:24])


@pytest.fixture(scope="module")
def session():
    options = ios_options() if PLATFORM == "ios" else android_options()
    driver = webdriver.Remote(os.environ.get("APPIUM_URL", "http://127.0.0.1:4723"), options=options)
    native(driver)
    driver.orientation = ORIENTATION
    site_loaded(driver)
    if SIGNED_IN:
        sign_in(driver)
    yield driver
    driver.quit()


@pytest.mark.parametrize("scene", SCENES, ids=[scene["name"] for scene in SCENES])
def test_scene(session, scene):
    try:
        path = scene["path"].format(**VALUES)
    except KeyError as error:
        pytest.fail(f"unknown placeholder {error} in {scene['name']}")
    if any(field and not VALUES.get(field) for _, field, _, _ in string.Formatter().parse(scene["path"])):
        pytest.skip("no value for this scene's placeholder")
    if scene.get("signed_in") and not SIGNED_IN:
        pytest.skip("needs the demo account (REVIEW_DEMO_USER, REVIEW_DEMO_PASSWORD)")

    driver = session
    site_loaded(driver)
    theme = scene.get("theme")
    driver.execute_script(
        "arguments[0] ? localStorage.setItem('theme', arguments[0]) : localStorage.removeItem('theme');",
        theme,
    )
    driver.get(f"{SITE}{path}")
    site_loaded(driver)
    if PLATFORM == "android":
        # Immersive: no taskbar on the tablets, no light bar over the dark theme (logbook).
        driver.execute_script("try { window.Capacitor.nativePromise('SystemBars', 'hide', {}); } catch (e) {}")
    ready = scene["ready"] if isinstance(scene["ready"], list) else [scene["ready"]]
    for selector in ready:
        wait(driver, lambda d: d.execute_script("return !!document.querySelector(arguments[0]);", selector))
    if scene.get("ready_script"):
        wait(driver, lambda d: d.execute_script(scene["ready_script"]))
    wait(driver, lambda d: d.execute_script("return !document.querySelector('.htmx-request');"))
    if scene.get("open"):
        # A <details> row; opening an NFT collection fetches its items (hx-trigger "toggle once").
        opened = driver.execute_script(
            "var row = document.querySelector(arguments[0]);"
            "if (!row) return false;"
            "row.open = true; return true;",
            scene["open"],
        )
        assert opened, f"{scene['name']}: nothing matches {scene['open']}"
        driver.execute_script(SCROLL_TO, scene["open"])
        time.sleep(1)
        wait(driver, lambda d: d.execute_script("return !document.querySelector('.htmx-request');"))
        wait(driver, lambda d: d.execute_script(IMAGES_DRAWN, scene["open"]))
    elif scene.get("scroll_to"):
        driver.execute_script(SCROLL_TO, scene["scroll_to"])
    driver.execute_script(
        "var style = document.createElement('style');"
        "style.textContent = arguments[0] + ' { display: none !important; }';"
        "document.head.appendChild(style);",
        HIDDEN,
    )
    time.sleep(scene.get("settle", SETTLE))

    native(driver)
    if PLATFORM == "android":
        # Fallback for the immersive notice run-android.sh turns off.
        for button in driver.find_elements(AppiumBy.XPATH, '//*[@text="Got it"]'):
            button.click()
            time.sleep(2)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{scene['name']}.png"
    driver.get_screenshot_as_file(str(target))

    if SIZES:
        size = "x".join(map(str, png_size(target)))
        assert size in SIZES, f"{target.name} is {size}, not {' or '.join(SIZES)}"
