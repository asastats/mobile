"""The API pages' Back link, tapped through the native UI: the reader's report of 2026-11-07."""

import pytest

from conftest import (
    PLATFORM,
    SITE,
    native_tap,
    page_is_dark,
    press_back,
    safe_area,
    site_loaded,
    status_bar_style,
    uncovered,
    wait,
    webview,
)

pytestmark = pytest.mark.live

SWAGGER = "/api/v2/schema/swagger-ui/"
REDOC = "/api/v2/schema/redoc/"
BACK = "#api-back"


def on_faq(driver):
    """Start on the FAQ page, reached by a tap, so Back has somewhere to go."""
    site_loaded(driver)
    driver.find_element("css selector", 'a[href="/faq/"]').click()
    wait(driver, lambda d: d.current_url.endswith("/faq/"))
    site_loaded(driver)


def open_swagger(driver):
    """The footer's API link, as the reader reached it; the hamburger's copy is hidden."""
    driver.find_element("css selector", f'footer a[href="{SWAGGER}"]').click()
    wait(driver, lambda d: d.current_url.endswith(SWAGGER))
    wait(driver, lambda d: d.execute_script(
        "return document.readyState === 'complete' && !!document.querySelector(arguments[0]);", BACK
    ))


def assert_back_is_tappable(driver):
    """Below the status bar, nothing over it."""
    top = driver.execute_script(
        "return document.querySelector(arguments[0]).getBoundingClientRect().top;", BACK
    )
    inset = safe_area(driver)[0]
    if PLATFORM == "ios":
        # 0 means no viewport-fit=cover: the link would sit under the clock again
        assert inset > 0
    assert top >= inset - 0.5
    assert uncovered(driver, BACK)


def tap_back_lands_on_faq(driver):
    native_tap(driver, BACK)
    webview(driver)
    wait(driver, lambda d: d.current_url.endswith("/faq/"))


def test_swagger_back_taps_on_arrival_and_returns(driver):
    on_faq(driver)
    open_swagger(driver)

    assert_back_is_tappable(driver)
    tap_back_lands_on_faq(driver)


def test_swagger_back_taps_after_scrolling(driver):
    on_faq(driver)
    open_swagger(driver)
    wait(driver, lambda d: d.execute_script("return !!document.querySelector('.opblock');"))
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight / 2);")
    wait(driver, lambda d: d.execute_script("return window.scrollY > 200;"))

    assert_back_is_tappable(driver)
    tap_back_lands_on_faq(driver)


def test_redoc_back_taps_and_returns(driver):
    on_faq(driver)
    driver.get(f"{SITE}{REDOC}")
    wait(driver, lambda d: d.execute_script(
        "var r = document.querySelector('redoc');"
        "return document.readyState === 'complete' && !!r && r.children.length > 0;"
    ))

    assert_back_is_tappable(driver)
    tap_back_lands_on_faq(driver)


def test_status_bar_follows_the_page_after_back(driver):
    # frontend 055c065: the back-forward cache restores the page without rerunning scripts
    on_faq(driver)
    driver.execute_script(
        "localStorage.setItem('theme', 'asastats-dark');"
        "document.documentElement.setAttribute('data-theme', 'asastats-dark');"
    )
    try:
        assert page_is_dark(driver)
        wait(driver, lambda d: status_bar_style(d) == "DARK")
        open_swagger(driver)
        wait(driver, lambda d: status_bar_style(d) == "LIGHT")

        tap_back_lands_on_faq(driver)

        wait(driver, lambda d: status_bar_style(d) == "DARK")
    finally:
        webview(driver)
        driver.execute_script("localStorage.removeItem('theme');")


@pytest.mark.android
def test_android_back_leaves_the_api_page(driver):
    on_faq(driver)
    open_swagger(driver)

    press_back(driver)

    webview(driver)
    wait(driver, lambda d: d.current_url.endswith("/faq/"))
