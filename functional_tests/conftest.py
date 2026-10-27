"""The installed debug app, driven by Appium: UiAutomator2 on an Android emulator,
XCUITest on an iOS simulator (ASASTATS_PLATFORM=ios).

Run by .github/workflows/functional.yml; see capacitor/MOBILE-TESTING.md.
"""

import json
import os
from pathlib import Path

import pytest
from appium import webdriver
from appium.common.exceptions import NoSuchContextException
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parent.parent
PLATFORM = os.environ.get("ASASTATS_PLATFORM", "android")
APK = Path(os.environ.get("ASASTATS_APK", ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"))
#: The simulator build, from functional-ios.yml's -derivedDataPath.
IOS_APP = Path(os.environ.get("ASASTATS_IOS_APP", ROOT / "build/Build/Products/Debug-iphonesimulator/App.app"))
#: The debug build's package (`applicationIdSuffix '.debug'`); iOS has no debug suffix.
PACKAGE = "com.asastats.app.debug" if PLATFORM == "android" else "com.asastats.app"
SITE = os.environ.get("ASASTATS_URL", "https://www.asastats.com")
APPIUM = os.environ.get("APPIUM_URL", "http://127.0.0.1:4723")
VERSION = json.loads((ROOT / "package.json").read_text())["version"]
TIMEOUT = 60
#: The local suite's account (functional_tests/server/seed.py) and database.
USER = os.environ.get("APP_TEST_USER", "apptester")
PASSWORD = os.environ.get("APP_TEST_PASSWORD", "app-tester-pw-1")
DATABASE_URL = os.environ.get("ASASTATS_DB_URL", "")
#: Uploaded by functional.yml when a job fails.
FAILURES = Path(__file__).resolve().parent / "failures"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call" and report.failed and "driver" in item.funcargs:
        save_evidence(item.funcargs["driver"], FAILURES / item.name)
    return report


def save_evidence(driver, folder):
    """Save what the phone showed: screenshot, contexts, the page, logcat."""
    folder.mkdir(parents=True, exist_ok=True)
    notes = []
    for name, read in (
        ("context", lambda: driver.current_context),
        ("contexts", lambda: driver.contexts),
        ("package", lambda: driver.current_package),
        ("activity", lambda: driver.current_activity),
    ):
        try:
            notes.append(f"{name}: {read()}")
        except Exception as error:  # noqa: BLE001 - evidence, never a second failure
            notes.append(f"{name}: {error!r}")
    for context in [c for c in _contexts(driver) if c.startswith("WEBVIEW")]:
        try:
            driver.switch_to.context(context)
            notes.append(f"{context} url: {driver.current_url}")
            (folder / f"{context}.html").write_text(driver.page_source)
        except Exception as error:  # noqa: BLE001
            notes.append(f"{context}: {error!r}")
    try:
        native(driver)
        driver.get_screenshot_as_file(str(folder / "screen.png"))
        (folder / "native.xml").write_text(driver.page_source)
        log = "logcat" if PLATFORM == "android" else "syslog"
        entries = driver.get_log(log)
        (folder / f"{log}.txt").write_text("\n".join(entry["message"] for entry in entries))
    except Exception as error:  # noqa: BLE001
        notes.append(f"native: {error!r}")
    (folder / "notes.txt").write_text("\n".join(notes) + "\n")


def _contexts(driver):
    try:
        return driver.contexts
    except Exception:  # noqa: BLE001
        return []


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "android" in item.keywords and PLATFORM != "android":
            item.add_marker(pytest.mark.skip(reason="Android only"))


@pytest.fixture
def driver():
    options = ios_options() if PLATFORM == "ios" else android_options()
    session = webdriver.Remote(APPIUM, options=options)
    yield session
    session.quit()


def ios_options():
    options = XCUITestOptions()
    options.set_capability("appium:app", str(IOS_APP.resolve()))
    options.set_capability("appium:udid", os.environ["ASASTATS_SIMULATOR"])
    # The push permission prompt would cover the page.
    options.set_capability("appium:autoAcceptAlerts", True)
    options.set_capability("appium:webviewConnectTimeout", 30000)
    options.set_capability("appium:wdaLaunchTimeout", 240000)
    options.set_capability("appium:newCommandTimeout", 300)
    return options


def android_options():
    options = UiAutomator2Options()
    options.set_capability("appium:app", str(APK.resolve()))
    options.set_capability("appium:appPackage", PACKAGE)
    options.set_capability("appium:autoGrantPermissions", True)
    # The WebView's Chrome version decides the chromedriver; Appium fetches it.
    options.set_capability("appium:chromedriverAutodownload", True)
    options.set_capability("appium:newCommandTimeout", 300)
    return options


def wait(driver, predicate, timeout=TIMEOUT):
    """Wait until `predicate(driver)` is truthy and return its value."""
    return WebDriverWait(driver, timeout, poll_frequency=1).until(predicate)


def webview(driver):
    """Switch to the app's own WebView, once it exists and accepts the switch."""

    def switched(d):
        names = [c for c in d.contexts if c.startswith("WEBVIEW")]
        # the app's own first: a browser opened from it lists one too
        names.sort(key=lambda c: c != f"WEBVIEW_{PACKAGE}")
        if not names:
            return False
        try:
            d.switch_to.context(names[0])
        except NoSuchContextException:
            return False  # listed a moment before it can be attached
        return True

    wait(driver, switched)


def native(driver):
    """Switch to the native UI (back button, other apps, system settings)."""
    driver.switch_to.context("NATIVE_APP")


def press_back(driver):
    """Press Back in the native UI, after answering an "isn't responding" dialog."""
    native(driver)
    for button in driver.find_elements("id", "android:id/aerr_wait"):
        button.click()
    driver.back()


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
    driver.find_element("css selector", "#id_login").send_keys(USER)
    driver.find_element("css selector", "#id_password").send_keys(PASSWORD)
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
