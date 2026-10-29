"""The shell around the live site, on an emulator, read-only against production."""

import pytest
from selenium.common.exceptions import WebDriverException

from conftest import PACKAGE, PLATFORM, SITE, VERSION, native, press_back, site_loaded, wait, webview

pytestmark = pytest.mark.live


def test_the_site_loads_in_app_mode(driver):
    site_loaded(driver)

    html = driver.execute_script(
        "return [document.documentElement.dataset.appPlatform, navigator.userAgent];"
    )
    assert html[0] == PLATFORM
    assert html[1].endswith(f"ASAStatsApp/{VERSION} ({PLATFORM})")


def test_app_js_publishes_the_api_page_scripts_use(driver):
    site_loaded(driver)

    api = driver.execute_script(
        "var a = window.ASAStatsApp;"
        "return [a.isApp, typeof a.download, typeof a.enablePush, typeof a.signIn];"
    )
    assert api == [True, "function", "function", "function"]


@pytest.mark.android
def test_external_links_open_in_the_browser(driver):
    site_loaded(driver)

    driver.execute_script("document.querySelector('a[href^=\"https://github.com/\"]').click();")

    native(driver)
    wait(driver, lambda d: d.current_package != PACKAGE)
    press_back(driver)
    wait(driver, lambda d: d.current_package == PACKAGE)


@pytest.mark.android
def test_the_back_button_goes_back_in_history(driver):
    site_loaded(driver)
    start = driver.current_url
    # A tap, not location.assign(): Chromium skips, on Back, a page that navigated without one
    driver.find_element("css selector", 'a[href="/faq/"]').click()
    wait(driver, lambda d: d.current_url.endswith("/faq/"))

    press_back(driver)

    webview(driver)
    wait(driver, lambda d: d.current_url == start)


@pytest.mark.android
def test_a_link_to_the_site_opens_in_the_app(driver):
    site_loaded(driver)
    native(driver)

    # /<word>/ is in the App Links filter (AndroidManifest.xml)
    driver.execute_script("mobile: deepLink", {"url": f"{SITE}/faq/", "package": PACKAGE})

    webview(driver)
    wait(driver, lambda d: d.current_url.endswith("/faq/"))


@pytest.mark.android
def test_a_new_text_size_keeps_the_page_and_applies(driver):
    site_loaded(driver)
    driver.find_element("css selector", 'a[href="/faq/"]').click()
    wait(driver, lambda d: d.current_url.endswith("/faq/"))
    size = "return [window.kept, parseFloat(getComputedStyle(document.querySelector('main p')).fontSize)];"
    driver.execute_script("window.kept = true;")
    before = driver.execute_script(size)[1]

    native(driver)
    driver.execute_script("mobile: shell", {"command": "settings", "args": ["put", "system", "font_scale", "1.3"]})
    try:
        webview(driver)
        # kept: the activity was not recreated (fontScale in configChanges)
        wait(driver, lambda d: d.execute_script(size) == [True, pytest.approx(before * 1.3, abs=0.5)])
        assert driver.current_url.endswith("/faq/")
    finally:
        native(driver)
        driver.execute_script("mobile: shell", {"command": "settings", "args": ["put", "system", "font_scale", "1.0"]})


def test_a_missing_page_shows_the_sites_404_not_no_connection(driver):
    site_loaded(driver)
    driver.execute_script(f"window.location.assign('{SITE}/no/such/page/');")

    # MainActivity keeps offline.html for unreachable sites only (S11)
    wait(driver, lambda d: d.execute_script("return document.title").startswith("Page not found"))
    assert "/no/such/page/" in driver.current_url
    assert "No connection" not in driver.page_source


@pytest.mark.android
def test_offline_shows_retry_and_retry_comes_back(driver):
    site_loaded(driver)
    driver.get(f"{SITE}/faq/")
    site_loaded(driver)
    native(driver)
    driver.execute_script("mobile: setConnectivity", {"wifi": False, "data": False})
    try:
        webview(driver)
        # A link to another page fails: native code tells offline.html, for Retry.
        driver.execute_script(
            "var a = document.createElement('a'); a.href = '/about/';"
            "document.body.appendChild(a); a.click();"
        )
        wait(driver, offline_page_shown)
        assert "No connection" in driver.page_source
        wait(driver, lambda d: retry_target(d).endswith("/about/"))
    finally:
        native(driver)
        driver.execute_script("mobile: setConnectivity", {"wifi": True, "data": True})

    # The emulator takes a few seconds to come back online: Retry until it does.
    webview(driver)
    wait(driver, retried)
    site_loaded(driver)
    assert driver.execute_script("return location.pathname;") == "/about/"


def offline_page_shown(driver):
    """True once offline.html is up; false while the WebView is still switching to it."""
    try:
        return driver.execute_script("return !!document.getElementById('retry');")
    except WebDriverException:
        return False


def retry_target(driver):
    """The page offline.html's Retry will open; empty until native code has set it."""
    try:
        return driver.execute_script("return window.ASASTATS_RETRY || '';")
    except WebDriverException:
        return ""


def retried(driver):
    """Click Retry once per offline page; true once the site is back."""
    # Once: a click every poll restarts a load that takes longer than the poll.
    try:
        return driver.execute_script(
            "var retry = document.getElementById('retry');"
            "if (retry) { if (!window.retried) { window.retried = true; retry.click(); }"
            " return false; }"
            "return document.documentElement.classList.contains('in-app');"
        )
    except WebDriverException:
        return False  # the click navigated while the script ran
