"""The app against a Django server started in CI, signed in as a test account."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException

from conftest import PACKAGE, SITE, TIMEOUT, USER, devices, native, sign_in, site_loaded, wait, webview

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


def test_connections_offer_google_through_the_native_sheet(driver):
    # The emulator (google_apis) has Play services, so app.js arms the Google
    # button and hides the website note (O3). This server has no Google client
    # id, so the plugin refuses ("invalid"): nonce, bridge, plugin and back.
    sign_in(driver)
    driver.get(f"{SITE}/accounts/3rdparty/")
    site_loaded(driver)

    wait(driver, lambda d: d.execute_script(
        "var b = document.getElementById('id_google_connect');"
        "return b && !b.hidden && b.hasAttribute('data-app-connect-ready');"
    ))
    assert driver.execute_script(
        "return document.getElementById('id_google_connect_on_website').hidden;"
    )

    driver.execute_script("document.getElementById('id_google_connect').click();")

    native(driver)
    message = wait(driver, lambda d: d.find_elements("id", "android:id/message"))
    assert message[0].text.startswith("Sign-in did not finish")
    driver.find_element("id", "android:id/button1").click()


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


def test_a_restart_behind_walletconnect_comes_back_to_the_login_page_and_says_so(driver):
    site_loaded(driver)
    driver.get(f"{SITE}/accounts/login/")
    site_loaded(driver)
    button = wait(
        driver,
        lambda d: d.find_elements(
            "css selector", "#evm-wallet-connect [data-connector-id='walletconnect']"
        ),
    )[0]
    # app.js notes the tap in the capture phase; WalletConnect itself is not opened.
    driver.execute_script(
        "document.getElementById('evm-wallet-connect')"
        ".addEventListener('click', function (e) { e.stopPropagation(); }, true);"
        "arguments[0].click();",
        button,
    )
    assert driver.execute_script("return localStorage.getItem('asastats.walletHandoff');")
    # Chromium writes localStorage to disk a few seconds late; see docs/logbook.md.
    time.sleep(8)

    # As MIUI does behind the wallet. Native first, so the WebView is attached afresh.
    native(driver)
    driver.terminate_app(PACKAGE)
    driver.activate_app(PACKAGE)
    site_loaded(driver)

    notice = wait(
        driver,
        lambda d: d.find_elements(
            "css selector", "#evm-wallet-connect [data-wallet-handoff='evm']"
        ),
    )[0]
    assert driver.current_url == f"{SITE}/accounts/login/"
    assert "Your phone closed ASA Stats while your wallet was open" in notice.text


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


#: Sends through the CI server's own `notify`, as an alert would.
SEND = """
from django.contrib.auth import get_user_model
from widgets.inhouse.alerts.push import notify
user = get_user_model().objects.get(username={user!r})
print("sent", notify(user, {{"title": {title!r}, "body": "Delivered to the emulator", "url": "/"}}))
"""


needs_fcm = pytest.mark.skipif(
    not (os.environ.get("ASASTATS_PUSH") and os.environ.get("FCM_CREDENTIALS_FILE")),
    reason="no google-services.json or no Firebase service account in CI",
)


def turn_push_on(driver):
    """Sign in and register this emulator for pushes, as the Profile switch does."""
    sign_in(driver)
    driver.set_script_timeout(TIMEOUT)
    result = driver.execute_async_script(
        "var done = arguments[arguments.length - 1];"
        "window.ASAStatsApp.enablePush(arguments[0]).then(done, function (e) { done(String(e)); });",
        DEVICE_URLS,
    )
    assert result == {"ok": True, "message": "This device is on."}


def send_alert(title):
    """Send `title` to the test account through the server's real FCM request."""
    manage = Path(os.environ["GITHUB_WORKSPACE"]) / "frontend/website/manage.py"
    sent = subprocess.run(
        [sys.executable, str(manage), "shell", "-c", SEND.format(user=USER, title=title)],
        capture_output=True, text=True, check=True,
    )
    assert "sent " in sent.stdout and "sent 0" not in sent.stdout, sent.stdout + sent.stderr


def delivered(driver, title, attempts=3):
    """Send `title` and return its notification from the shade, resending if it never shows.

    A freshly booted emulator may not have its FCM connection up yet (logbook).
    """
    for attempt in range(attempts):
        send_alert(title)
        driver.open_notifications()
        try:
            return wait(driver, lambda d: d.find_elements("xpath", f'//*[@text="{title}"]'))[0]
        except TimeoutException:
            if attempt == attempts - 1:
                raise


@needs_fcm
def test_a_push_reaches_the_notification_shade(driver):
    turn_push_on(driver)
    # In the background FCM draws it; the open-app case is the next test.
    native(driver)
    driver.press_keycode(3)  # HOME

    title = f"Functional test {os.getpid()} background"
    delivered(driver, title)


@needs_fcm
def test_a_push_while_the_app_is_open_is_shown_and_its_tap_opens_the_page(driver):
    turn_push_on(driver)
    assert "/home/" in driver.current_url
    native(driver)

    title = f"Functional test {os.getpid()} foreground"
    delivered(driver, title).click()
    webview(driver)
    # SEND's url is "/": the tap reaches app.js as notificationActionPerformed.
    wait(driver, lambda d: d.current_url == f"{SITE}/")
