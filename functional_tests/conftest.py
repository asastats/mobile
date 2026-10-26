"""The installed debug app, driven by Appium (UiAutomator2) on an emulator.

Run by .github/workflows/functional.yml; see capacitor/MOBILE-TESTING.md.
"""

import json
import os
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parent.parent
APK = Path(os.environ.get("ASASTATS_APK", ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"))
#: The debug build's package (`applicationIdSuffix '.debug'`).
PACKAGE = "com.asastats.app.debug"
SITE = os.environ.get("ASASTATS_URL", "https://www.asastats.com")
APPIUM = os.environ.get("APPIUM_URL", "http://127.0.0.1:4723")
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
TIMEOUT = 60
#: The local suite's account (functional_tests/server/seed.py) and database.
USER = os.environ.get("APP_TEST_USER", "apptester")
PASSWORD = os.environ.get("APP_TEST_PASSWORD", "app-tester-pw-1")
DATABASE_URL = os.environ.get("ASASTATS_DB_URL", "")


@pytest.fixture
def driver():
    options = UiAutomator2Options()
    options.set_capability("appium:app", str(APK.resolve()))
    options.set_capability("appium:appPackage", PACKAGE)
    options.set_capability("appium:autoGrantPermissions", True)
    # The WebView's Chrome version decides the chromedriver; Appium fetches it.
    options.set_capability("appium:chromedriverAutodownload", True)
    options.set_capability("appium:newCommandTimeout", 300)
    session = webdriver.Remote(APPIUM, options=options)
    yield session
    session.quit()


def wait(driver, predicate, timeout=TIMEOUT):
    """Wait until `predicate(driver)` is truthy and return its value."""
    return WebDriverWait(driver, timeout, poll_frequency=1).until(predicate)


def webview(driver):
    """Switch to the app's WebView, once it exists."""
    name = wait(driver, lambda d: next((c for c in d.contexts if c.startswith("WEBVIEW")), None))
    driver.switch_to.context(name)


def native(driver):
    """Switch to the native UI (back button, other apps, system settings)."""
    driver.switch_to.context("NATIVE_APP")


def site_loaded(driver):
    """Wait for a page of the site in app mode, in the WebView."""
    webview(driver)
    wait(
        driver,
        lambda d: d.execute_script(
            "return document.readyState === 'complete'"
            " && document.documentElement.classList.contains('in-app');"
        ),
    )


def sign_in(driver):
    """Sign in with email and password, as a reader does in the WebView."""
    site_loaded(driver)
    driver.get(f"{SITE}/accounts/login/")
    site_loaded(driver)
    driver.find_element("id", "id_login").send_keys(USER)
    driver.find_element("id", "id_password").send_keys(PASSWORD)
    driver.find_element("css selector", "#login_form button[type=submit]").click()
    wait(driver, lambda d: "/accounts/login/" not in d.current_url)
    site_loaded(driver)


def devices():
    """Return the platforms of the test account's push devices, from the database."""
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        rows = connection.execute(
            "SELECT d.platform FROM widgets_nativepushdevice d"
            " JOIN auth_user u ON u.id = d.user_id WHERE u.username = %s",
            (USER,),
        ).fetchall()
    return [row[0] for row in rows]
