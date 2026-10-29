Development
===========

Requirements
------------

* Node 22 or newer.
* Python 3.12 for the icon scripts and the functional tests.
* Android builds: JDK 21 and the Android SDK (API 36).
* iOS builds: Xcode 26 and a Mac.

GitHub Actions (``.github/workflows/``) builds the releases. A local build is for
trying a change on a device.


Run against a local website
---------------------------

The app loads whatever ``ASASTATS_URL`` names at ``cap sync`` and ``cap run`` time:

.. code-block:: bash

    npm ci
    ASASTATS_URL=http://<lan-ip>:8000 npx cap run android

Start Django with ``runserver 0.0.0.0:8000`` so the phone can reach it. An ``http:``
URL turns on cleartext traffic. A release build (``ASASTATS_RELEASE=1``, set in CI)
refuses one. With no ``ASASTATS_URL`` the app loads production.

Run ``npx cap sync`` again before you commit. It writes the URL into the committed
native configs, and those must point at production.


Firebase config files
---------------------

Push notifications need two git-ignored files. CI writes them from secrets. For a
local build, copy them in:

.. code-block:: text

    android/app/google-services.json
    ios/App/App/GoogleService-Info.plist

The iOS project lists the plist as a resource, so Xcode stops with "Build input file
cannot be found" when it is missing. How to get fresh copies is in :doc:`firebase`.


Icons and splash screens
------------------------

Edit ``assets/icon.png`` (1024 px square, opaque) or ``assets/icon-foreground.png``
(the Android adaptive foreground), then run:

.. code-block:: bash

    python3 scripts/make-icons.py

It needs Pillow and rewrites files in both native projects. Commit what it rewrites.

The Android status-bar icon is a white silhouette of ``assets/logo.svg``. After a logo
change, run ``python3 scripts/make-notification-icon.py`` (standard library only) and
commit ``android/app/src/main/res/drawable/ic_stat_asastats.xml``. The tint in the
notification shade is ``notification_accent`` in ``res/values/colors.xml``.

App Store Connect rejects an icon with an alpha channel, so the store icon must stay
RGB. The tests check it.


Versions and build numbers
--------------------------

``package.json`` holds both numbers. Gradle and the iOS workflow read them from there.

``version``
    The store version, for example ``1.1.0``. The user-agent token carries it.

``buildNumber`` and ``buildEpoch``
    A local build uses ``buildNumber`` as is. CI uses ``buildNumber`` plus the minutes
    between ``buildEpoch`` and the commit time, the same on both platforms (Android
    ``versionCode``, iOS ``CFBundleVersion``).

Never lower either value. The stores reject a build number they have already seen.
Re-running a workflow for a commit that already uploaded fails for the same reason, so
push a new commit instead.


Capacitor packages
------------------

The website bundles the JavaScript half of the same Capacitor packages
(``frontend/wallet``). Their versions are pinned exactly and must match
``package.json`` here. Bump both repositories together.

CocoaPods goes read-only on 2 December 2026, so every iOS dependency comes in through
Swift Package Manager. Do not add a plugin that only ships a podspec.


What the website and the app agree on
-------------------------------------

Three contracts cross the repository boundary. Changing one side alone breaks the
other.

User-agent token
    ``ASAStatsApp/<version> (<ios|android>)``, appended by ``ios.appendUserAgent`` and
    ``android.appendUserAgent`` in ``capacitor.config.ts``. The website parses it in one
    place, ``core/appclient.py`` in the frontend repository, and switches to app mode.
    Nothing else may parse the user agent.

``window.ASAStatsApp``
    Defined by the website's ``app.js``. Widget scripts feature-detect it before calling
    ``enablePush()``, ``disablePush()``, ``signIn()`` or ``download()``.

Links host
    ``www.asastats.com``. Universal Links and App Links only open the app when the
    website serves a correct ``apple-app-site-association`` and ``assetlinks.json``.
    Both are generated from settings listed in :doc:`server_settings`.


Native plugins are a security boundary
--------------------------------------

On Android the Capacitor bridge exists only for the ``server.url`` origin, and every
page on that origin can call every plugin the app registers. A cross-site scripting
hole on www.asastats.com would therefore reach the device.

* Register only the plugins in ``package.json``: App, Browser, SplashScreen, StatusBar,
  Share, Filesystem, Preferences, Haptics, FirebaseMessaging and the local WebAuth,
  AppLock and NativeSignIn plugins.
* Never add an HTTP plugin, broad filesystem access or anything that reads other apps'
  data.
* A plugin method trusts nothing from JavaScript. :doc:`webauth` and
  :doc:`nativesignin` show what that looks like; :doc:`applock` keeps its only
  setting out of JavaScript's reach altogether.
* Revisit this list before the website admits a third-party widget.
