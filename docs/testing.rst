Testing
=======

Every ASA Stats repository follows one rule: 100 % unit test coverage, functional tests
for every visible feature, and as many integration tests as practical.

Where the code is tested
------------------------

Most of the app's behaviour is website code and is tested in the frontend repository:
``app.js`` with Jest, the app-mode middleware, templates, push devices and the
``apple-app-site-association`` and ``assetlinks.json`` views with pytest, and the pages
with Selenium using the app's user-agent token. This repository tests the shell.

.. list-table::
   :header-rows: 1
   :widths: 34 22 44

   * - Code
     - Tool
     - Command
   * - ``capacitor.config.ts``, ``offline/``
     - Jest
     - ``npm test``
   * - ``scripts/*.py``
     - pytest, 100 % enforced
     - ``python -m pytest``
   * - WebAuth plugin, Android
     - JUnit and JaCoCo
     - ``./gradlew :asastats-webauth:jacocoCoverageCheck`` in ``android/``
   * - WebAuth plugin, iOS
     - XCTest and ``xccov``
     - ``xcodebuild test -scheme AsastatsWebauth`` in ``plugins/webauth``
   * - AppLock plugin, Android
     - JUnit and JaCoCo
     - ``./gradlew :asastats-applock:jacocoCoverageCheck`` in ``android/``
   * - AppLock plugin, iOS
     - XCTest and ``xccov``
     - ``xcodebuild test -scheme AsastatsApplock`` in ``plugins/applock``
   * - NativeSignIn plugin, Android
     - JUnit and JaCoCo
     - ``./gradlew :asastats-nativesignin:jacocoCoverageCheck`` in ``android/``
   * - NativeSignIn plugin, iOS
     - XCTest and ``xccov``
     - ``xcodebuild test -scheme AsastatsNativesignin`` in ``plugins/nativesignin``
   * - FlutterData plugin, Android
     - JUnit and JaCoCo
     - ``./gradlew :asastats-flutterdata:jacocoCoverageCheck`` in ``android/``
   * - FlutterData plugin, iOS
     - XCTest and ``xccov``
     - ``xcodebuild test -scheme AsastatsFlutterdata`` in ``plugins/flutterdata``
   * - The installed app
     - Appium
     - see below

``MainActivity``, ``AppDelegate`` and ``SceneDelegate`` have no unit tests. The Appium
suite exercises them.

Jest and pytest
---------------

.. code-block:: bash

    npm ci
    npm test
    python -m pip install -r requirements-dev.txt
    python -m pytest

``pytest.ini`` makes the Python run fail under 100 % coverage of ``scripts/``.
``jest.config.cjs`` sets a 100 % threshold for statements, branches, functions and
lines. ``tests.yml`` runs both on every push and pull request.

Native code that only calls the operating system, such as the sign-in sheet, sits behind
a thin adapter. The tests use a fake. Coverage counts our files and ignores the files
Capacitor generates.

Appium
------

Selenium cannot drive an installed app. Appium speaks the same WebDriver protocol, and
its Python client extends Selenium's. Inside the app it switches to the WebView
context, where ``find_element(By.CSS_SELECTOR, ...)`` works as it does in the website's
tests. Outside the WebView it taps native UI: system alerts, the share sheet, the
notification prompt, the Back button.

The tests are in ``functional_tests/`` and carry three markers:

``live``
    The debug app against www.asastats.com, read-only. App mode and the user-agent
    token, ``window.ASAStatsApp``, an external link opening the browser sheet, Back,
    a deep link, offline then Retry, text size.

``local``
    The debug app against a Django server that CI starts from the frontend repository
    with a test database (``functional_tests/server/``). Email sign-in, account
    deletion with its captcha, the Connections page's Google button through the
    NativeSignIn bridge, a social button through the WebAuth bridge, the EVM wallet
    hand-off after a restart, push registration and unregistration checked in the
    database, and a delivered notification, in the background and with the app open,
    when the ``FCM_SERVICE_ACCOUNT_BASE64`` secret exists.

``android``
    Android only: Back, App Links, the browser sheet, connectivity. Skipped on iOS.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Workflow
     - Runs on
     - Notes
   * - ``functional.yml``
     - Android emulator, ubuntu with KVM
     - Jobs ``live`` and ``local``. ``functional_tests/run-android.sh`` starts Appium and
       runs one marker.
   * - ``functional-ios.yml``
     - iOS simulator, macOS runner
     - The platform-neutral live tests. Costs more runner minutes.

A machine without KVM cannot run the emulator, so these suites run in CI only. When one
fails, ``functional_tests/failures/`` and the ``appium-log`` or ``logs-local`` artifact
of the failed run hold a screenshot, the available contexts, the page source and
logcat from the moment of failure.

A failure from Play services being killed after boot is an emulator flake. If it
repeats, warm the emulator up in ``run-android.sh``.

Appium on iOS
~~~~~~~~~~~~~

Web Inspector lists the app as ``process-App``. The suite passes
``additionalWebviewBundleIds`` for that reason.

What stays manual
-----------------

Real Google, Apple and X sign-ins block automation with bot checks, and the native
sheets need a real account on the phone. The app lock's Face ID or fingerprint prompt
needs a person too. The Pera and Defly
hand-off needs the wallet apps and a funded account. A push arriving on a locked phone
and a store build installed from Play or TestFlight cannot be scripted either. These
rows live in :doc:`beta_checklist`.

Adding a test
-------------

* A new visible feature needs an Appium test in the marker that fits. Prefer ``live``
  when the feature works against production without an account.
* A new Python helper in ``scripts/`` needs a pytest case. The coverage gate will say
  which lines are missing.
* A new native branch in a plugin needs a case in its pure class (``WebAuthController``,
  ``LockPolicy``, ``NativeSignInRequest``) or against the fake adapter.
* Wait with ``wait(driver, predicate)`` from ``functional_tests/conftest.py``.
