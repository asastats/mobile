Releasing
=========

Workflows
---------

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Workflow
     - What it produces
   * - ``android.yml``
     - Always a debug APK (``com.asastats.app.debug``, "ASA Stats dev"), artifact
       ``asastats-debug-apk``. With the keystore secrets, also a signed ``.aab``,
       artifact ``asastats-release-aab``. The WebAuth plugin tests run first.
   * - ``ios.yml``
     - Without the App Store Connect secrets, a simulator compile. With them, an archive
       that is signed and uploaded to TestFlight. The WebAuth plugin tests run first.
   * - ``tests.yml``
     - Jest and pytest.
   * - ``functional.yml``, ``functional-ios.yml``
     - The Appium suites (:doc:`testing`).

All of them run on pushes to ``main`` and by hand. The secrets are listed in
:doc:`signing`, :doc:`firebase` and the repository README.

Every upload needs a build number the store has not seen. CI derives it from
``package.json`` (:doc:`development`), so a fresh commit is enough. To change the store
version, edit ``version`` in ``package.json`` and nothing else.

Keep the actions current. GitHub forces Node 20 actions onto Node 24, so move to each action's newest major when a deprecation notice appears, and read
the first green run before relying on the change.


Getting a store build onto a phone
----------------------------------

A debug build is the wrong thing to test. It is a different package, and its debug key
is in no App Links fingerprint list. Store builds are what users and reviewers get.

Play internal testing
~~~~~~~~~~~~~~~~~~~~~

Internal testing needs no review and goes live within minutes, with up to 100 testers.

#. Make sure the four ``ANDROID_KEY*`` secrets exist, then download the signed ``.aab``
   from the Android workflow run.
#. Play Console, the app, Test and release, Testing, Internal testing, Testers tab.
   Create an email list with the testers' Google accounts, and tick the list.
#. Create a new release, upload the ``.aab``, name it after the version and build
   number, add release notes, and choose Save and publish. Play may first ask you to
   finish the App content declarations (:doc:`store_listing`).
#. On the Testers tab copy the opt-in link. A tester opens it signed in with a listed
   account, taps Accept invite, and installs from the Play link on that page. It installs
   as an update over the previous app.

If the opt-in link still installs the old version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check in this order:

#. Play Console, Publishing overview. If it lists changes ready to send or in review, the
   release is not live. Send them, or turn Managed publishing off.
#. Internal testing, Releases: the release must read "Available to internal testers", not
   Draft. A draft lists its blocking errors under Review release. Common ones are a
   missing App content declaration and a Data safety form that does not match the bundle.
#. On the phone, Play Store, profile picture: the selected account is the one Play uses,
   and it must be on the testers list. With several Google accounts, it is not the one
   the browser accepted the invite with.
#. Open the opt-in link again signed in with that account. It must say you are a tester
   and not offer "Become a tester".
#. Settings, Apps, Google Play Store, Storage, Clear cache. Play can take up to an hour
   for a first internal release.
#. App bundle explorer, device catalog: the phone model must be supported. If it is not,
   Play serves the newest build the phone can install.

To tell the device apart from the tester status, upload the same ``.aab`` to Internal app
sharing. If its link installs the new version, the device is fine.

Internal app sharing
~~~~~~~~~~~~~~~~~~~~

Internal app sharing gives a one-off link per upload and needs no tester list. Google
re-signs every upload with its own internal test certificate, with two consequences:

* App Links and Android social sign-in check the signing certificate against
  ``assetlinks.json``. Add the internal test certificate's SHA-256 to
  ``ANDROID_CERT_SHA256`` (:doc:`server_settings`), or those features fail on this
  install for that reason alone.
* A Play internal testing or production build cannot install over it, because the
  certificate differs. Uninstall first when you switch back.

TestFlight
~~~~~~~~~~

The iOS workflow uploads the build. In App Store Connect open TestFlight, Internal
Testing, add yourself, install the TestFlight app on the iPhone and accept the invite.
Social sign-in on iOS needs 17.4 or later.


Before you promote a build
--------------------------

#. Run :doc:`beta_checklist` on the store builds, against production. Include an iPad,
   because the listing supports iPad and an update cannot drop it.
#. Check the listing texts and privacy answers against the current behaviour
   (:doc:`store_listing`).
#. Check ``assetlinks.json`` and the Apple file (:doc:`server_settings`).
#. Confirm the website is deployed with the code the build expects.

What changes without a new build
--------------------------------

The app is a shell around the live site, so most fixes ship with a website deploy. These
need no store release:

* Any page, widget or script change.
* Hiding a widget on one platform (``APP_HIDDEN_WIDGETS_*``).
* Hiding purchase links (``APP_HIDE_PURCHASE``).
* Removing a wallet from the sign-in list (``APP_UNSUPPORTED_WALLETS``).

A new build is needed for a change to a native plugin, a manifest or entitlements
change, the icons, the splash screen, ``capacitor.config.ts`` or the Capacitor version.
