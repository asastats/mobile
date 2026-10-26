"""The app against a Django server started in CI, signed in as a test account."""

import os

import pytest

from conftest import SITE, TIMEOUT, devices, native, sign_in, site_loaded, wait

pytestmark = pytest.mark.local

DEVICE_URLS = {
    "register": "/widgets/alerts/device/register",
    "unregister": "/widgets/alerts/device/unregister",
}


def test_email_sign_in_works_in_the_app(driver):
    sign_in(driver)

    assert driver.execute_script("return !!document.getElementById('logout');")


def test_delete_account_is_reachable_with_its_captcha(driver):
    sign_in(driver)
    driver.get(f"{SITE}/profile/deactivate/")
    site_loaded(driver)

    assert "Delete account" in driver.page_source
    assert driver.execute_script(
        """return !!document.querySelector('img[src*="/captcha/image/"]');"""
    )


def test_connections_ask_for_google_on_the_website(driver):
    sign_in(driver)
    driver.get(f"{SITE}/accounts/3rdparty/")
    site_loaded(driver)

    assert driver.execute_script(
        "return !!document.getElementById('id_google_connect_on_website');"
    )
    assert "/accounts/google/login/" not in driver.page_source


def test_social_sign_in_without_https_says_it_did_not_finish(driver):
    # The WebAuth plugin refuses an http server ("invalid"); the round trip
    # through the bridge to the native plugin and back is what is tested.
    site_loaded(driver)
    driver.get(f"{SITE}/accounts/login/")
    site_loaded(driver)

    driver.execute_script("document.getElementById('id_github').click();")

    # Capacitor shows window.alert as a native dialog.
    native(driver)
    message = wait(driver, lambda d: d.find_elements("id", "android:id/message"))
    assert message[0].text.startswith("Sign-in did not finish")
    driver.find_element("id", "android:id/button1").click()


@pytest.mark.skipif(
    not os.environ.get("ASASTATS_PUSH"), reason="the build has no google-services.json"
)
def test_push_registers_this_device_and_logout_removes_it(driver):
    sign_in(driver)
    driver.set_script_timeout(TIMEOUT)

    result = driver.execute_async_script(
        "var done = arguments[arguments.length - 1];"
        "window.ASAStatsApp.enablePush(arguments[0]).then(done, function (e) { done(String(e)); });",
        DEVICE_URLS,
    )
    assert result == {"ok": True, "message": "This device is on."}
    assert devices() == ["android"]

    driver.execute_script("document.getElementById('logout').click();")
    wait(driver, lambda d: not d.execute_script("return !!document.getElementById('logout');"))
    assert devices() == []
