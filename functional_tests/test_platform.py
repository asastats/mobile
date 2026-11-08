"""What a WebView shell leaves to the app on iOS and Android: research of 2026-11-08 (logbook)."""

import os
import subprocess
import sys
import time

import pytest
from selenium.common.exceptions import TimeoutException, WebDriverException

from conftest import (
    IN_BACKGROUND,
    IN_FOREGROUND,
    PACKAGE,
    PLATFORM,
    SITE,
    native,
    native_tap,
    page_is_dark,
    press_back,
    safe_area,
    simctl,
    site_loaded,
    status_bar_style,
    wait,
    webview,
)

pytestmark = pytest.mark.live

PROBE = "asastats_ft_probe"


def to_faq(driver):
    site_loaded(driver)
    driver.find_element("css selector", 'a[href="/faq/"]').click()
    wait(driver, lambda d: d.current_url.endswith("/faq/"))
    site_loaded(driver)


def script(driver, code, *args):
    """Run `code`, or None while the WebView is reloading or detached."""
    try:
        return driver.execute_script(code, *args)
    except WebDriverException:
        return None


def simulator():
    return os.environ["ASASTATS_SIMULATOR"]


# Zoom and the keyboard


def test_tapping_the_address_field_does_not_zoom_the_page(driver):
    # iOS zooms a focused field below 16px; daisyUI's .input raises it to 1rem on focus there
    site_loaded(driver)

    native_tap(driver, "#id_address")

    webview(driver)
    wait(driver, lambda d: d.execute_script("return document.activeElement.id === 'id_address';"))
    time.sleep(1)  # the zoom animates
    assert driver.execute_script("return window.visualViewport.scale;") == pytest.approx(1)
    if PLATFORM == "ios":
        assert driver.execute_script(
            "return parseFloat(getComputedStyle(document.activeElement).fontSize);"
        ) >= 16


def test_a_focused_field_low_on_the_page_stays_above_the_keyboard(driver):
    site_loaded(driver)
    driver.get(f"{SITE}/accounts/login/")
    site_loaded(driver)
    field = "#id_password"
    # Room below, so the field can sit at the bottom edge where the keyboard will rise
    driver.execute_script(
        "document.body.style.paddingBottom = window.innerHeight + 'px';"
        "var r = document.querySelector(arguments[0]).getBoundingClientRect();"
        "window.scrollBy(0, r.bottom - window.innerHeight + 8);",
        field,
    )

    native_tap(driver, field)

    wait(driver, lambda d: d.is_keyboard_shown())
    webview(driver)
    wait(driver, lambda d: d.execute_script(
        "var e = document.activeElement, v = window.visualViewport;"
        "if (!e || '#' + e.id !== arguments[0]) return false;"
        "return e.getBoundingClientRect().bottom <= v.offsetTop + v.height;",
        field,
    ))


# Content process


@pytest.mark.xfail(
    PLATFORM == "android",
    strict=True,
    reason="Capacitor's onRenderProcessGone returns false: Android closes the app (logbook 2026-11-08)",
)
def test_a_killed_web_content_process_brings_the_page_back(driver):
    to_faq(driver)
    driver.execute_script("window.kept = true;")

    if PLATFORM == "ios":
        if sys.platform != "darwin":
            pytest.skip("kills the simulator's WebContent process from the macOS host")
        killed = subprocess.run(["pkill", "-9", "-f", "CoreSimulator.*com.apple.WebKit.WebContent"])
        if killed.returncode != 0:
            pytest.skip("no WebContent process found")
    else:
        driver.set_page_load_timeout(10)
        try:
            driver.get("chrome://kill")
        except WebDriverException:
            pass  # the renderer died under the command

    native(driver)
    time.sleep(5)
    assert driver.query_app_state(PACKAGE) == IN_FOREGROUND, "the app closed"
    webview(driver)
    try:
        wait(driver, lambda d: script(d, "return window.kept === undefined;"), timeout=30)
    except TimeoutException:
        pytest.skip("the content process was not killed")
    site_loaded(driver)
    assert driver.current_url.endswith("/faq/")


# Lifecycle


def test_cookies_and_storage_survive_closing_the_app_from_recents(driver):
    # WebViews write cookies to disk lazily; MainActivity flushes on pause
    site_loaded(driver)
    driver.execute_script(
        f"document.cookie = '{PROBE}=1; max-age=600; path=/; secure; samesite=lax';"
        f"localStorage.setItem('{PROBE}', '1');"
    )
    try:
        driver.background_app(2)
        native(driver)  # the WebView is attached afresh after the restart
        driver.terminate_app(PACKAGE)
        driver.activate_app(PACKAGE)

        site_loaded(driver)
        assert driver.execute_script(
            f"return [document.cookie.indexOf('{PROBE}=1') !== -1, localStorage.getItem('{PROBE}')];"
        ) == [True, "1"]
    finally:
        webview(driver)
        script(
            driver,
            f"document.cookie = '{PROBE}=; max-age=0; path=/; secure; samesite=lax';"
            f"localStorage.removeItem('{PROBE}');",
        )


def test_a_return_from_the_background_keeps_the_page(driver):
    to_faq(driver)

    driver.background_app(20)

    webview(driver)
    wait(driver, lambda d: script(d, "return document.readyState === 'complete';"))
    assert driver.current_url.endswith("/faq/")
    assert not script(driver, "return !!document.getElementById('retry');"), "offline page shown"


def test_the_page_survives_a_rotation(driver):
    to_faq(driver)
    driver.execute_script("window.kept = true;")
    native(driver)

    driver.orientation = "LANDSCAPE"
    try:
        webview(driver)
        wait(driver, lambda d: d.execute_script("return window.innerWidth > window.innerHeight;"))
        assert driver.execute_script("return window.kept;"), "the page reloaded"
        assert driver.execute_script(
            "return document.documentElement.scrollWidth <= window.innerWidth + 1;"
        ), "wider than the screen"
        left = driver.execute_script(
            "return document.querySelector('main').getBoundingClientRect().left;"
        )
        assert left >= safe_area(driver)[3] - 0.5, "content under the notch"
    finally:
        native(driver)
        driver.orientation = "PORTRAIT"


def test_content_pages_fit_the_screen_width(driver):
    site_loaded(driver)
    for path in ("/", "/faq/", "/about/", "/features/", "/methodology/", "/tokenomics/"):
        driver.get(f"{SITE}{path}")
        site_loaded(driver)
        assert driver.execute_script(
            "return document.documentElement.scrollWidth <= window.innerWidth + 1;"
        ), path


# Appearance


def set_dark_mode(driver, on):
    if PLATFORM == "ios":
        simctl("ui", simulator(), "appearance", "dark" if on else "light")
    else:
        native(driver)
        driver.execute_script("mobile: shell", {"command": "cmd", "args": ["uimode", "night", "yes" if on else "no"]})


def test_system_dark_mode_keeps_the_status_bar_readable(driver):
    # uiMode is in configChanges: no new activity, so nothing on the native side resyncs
    to_faq(driver)
    set_dark_mode(driver, True)
    try:
        webview(driver)
        time.sleep(2)
        wait(driver, lambda d: status_bar_style(d) == ("DARK" if page_is_dark(d) else "LIGHT"))
    finally:
        set_dark_mode(driver, False)


@pytest.mark.skipif(PLATFORM != "ios", reason="Android: test_shell.py, text size")
@pytest.mark.xfail(
    strict=True,
    reason="WKWebView ignores Dynamic Type unless the page uses -apple-system-body (logbook 2026-11-08)",
)
def test_ios_larger_text_enlarges_the_page_text(driver):
    to_faq(driver)
    size = "return parseFloat(getComputedStyle(document.querySelector('main p')).fontSize);"
    before = driver.execute_script(size)

    simctl("ui", simulator(), "content_size", "accessibility-extra-large")
    try:
        webview(driver)
        wait(driver, lambda d: d.execute_script(size) > before * 1.15, timeout=20)
    finally:
        simctl("ui", simulator(), "content_size", "large")


# Leaving the app


def test_another_site_never_opens_inside_the_app(driver):
    site_loaded(driver)

    driver.execute_script("document.querySelector('a[href^=\"https://github.com/\"]').click();")

    time.sleep(3)
    native(driver)
    driver.activate_app(PACKAGE)
    webview(driver)
    wait(driver, lambda d: script(d, "return location.origin;") == SITE)


@pytest.mark.android
def test_android_back_closes_an_open_dialog_first(driver):
    site_loaded(driver)
    driver.execute_script("document.getElementById('modalLogin').showModal();")

    press_back(driver)

    webview(driver)
    wait(driver, lambda d: d.execute_script("return !document.getElementById('modalLogin').open;"))
    native(driver)
    assert driver.query_app_state(PACKAGE) == IN_FOREGROUND


@pytest.mark.android
def test_android_back_on_the_first_page_keeps_the_app_and_its_page(driver):
    # backButton.ts: minimizeApp, so the page is still there on return
    site_loaded(driver)
    driver.execute_script("window.kept = true;")

    press_back(driver)

    wait(driver, lambda d: d.query_app_state(PACKAGE) in IN_BACKGROUND)
    driver.activate_app(PACKAGE)
    webview(driver)
    assert driver.execute_script("return window.kept;")
