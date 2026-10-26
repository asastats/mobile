"""The shell around the live site, on an emulator, read-only against production."""

import pytest

from conftest import PACKAGE, SITE, VERSION, native, site_loaded, wait, webview

pytestmark = pytest.mark.live


def test_the_site_loads_in_app_mode(driver):
    site_loaded(driver)

    html = driver.execute_script(
        "return [document.documentElement.dataset.appPlatform, navigator.userAgent];"
    )
    assert html[0] == "android"
    assert html[1].endswith(f"ASAStatsApp/{VERSION} (android)")


def test_app_js_publishes_the_api_page_scripts_use(driver):
    site_loaded(driver)

    api = driver.execute_script(
        "var a = window.ASAStatsApp;"
        "return [a.isApp, typeof a.download, typeof a.enablePush, typeof a.signIn];"
    )
    assert api == [True, "function", "function", "function"]


def test_external_links_open_in_the_browser(driver):
    site_loaded(driver)

    driver.execute_script("document.querySelector('a[href^=\"https://github.com/\"]').click();")

    native(driver)
    wait(driver, lambda d: d.current_package != PACKAGE)
    driver.back()
    wait(driver, lambda d: d.current_package == PACKAGE)


def test_the_back_button_goes_back_in_history(driver):
    site_loaded(driver)
    driver.execute_script(f"window.location.assign('{SITE}/faq/');")
    wait(driver, lambda d: d.current_url.endswith("/faq/"))

    native(driver)
    driver.back()

    webview(driver)
    wait(driver, lambda d: d.current_url.rstrip("/") == SITE)


def test_a_link_to_the_site_opens_in_the_app(driver):
    site_loaded(driver)
    native(driver)

    driver.execute_script("mobile: deepLink", {"url": f"{SITE}/faq/", "package": PACKAGE})

    webview(driver)
    wait(driver, lambda d: d.current_url.endswith("/faq/"))


def test_offline_shows_retry_and_retry_comes_back(driver):
    site_loaded(driver)
    native(driver)
    driver.execute_script("mobile: setConnectivity", {"wifi": False, "data": False})
    try:
        webview(driver)
        driver.execute_script("window.location.reload();")
        wait(driver, lambda d: d.execute_script("return !!document.getElementById('retry');"))
        assert "No connection" in driver.page_source
    finally:
        native(driver)
        driver.execute_script("mobile: setConnectivity", {"wifi": True, "data": True})

    webview(driver)
    driver.execute_script("document.getElementById('retry').click();")
    site_loaded(driver)
