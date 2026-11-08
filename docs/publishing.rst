Publishing with fastlane
========================

This page is the whole path from a commit to the app in both stores: the first release of
the Capacitor app, and every update after it. The texts and the forms are in
:doc:`store_listing`; the builds themselves are in :doc:`releasing`.


How the pieces fit
------------------

Nothing in fastlane builds the app. Builds come from the normal CI on every push to
``main``; fastlane only moves them through the stores and keeps the store pages in step
with the files in ``fastlane/``.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - When
     - What happens
   * - Every push to ``main``
     - ``ios.yml`` uploads a signed build to TestFlight. ``android.yml`` uploads the
       signed ``.aab`` to Play's internal testing track, with the release notes from
       ``fastlane/metadata/android/en-GB/changelogs/default.txt``. Nobody outside the
       testers sees either.
   * - By hand: Screenshots
     - ``screenshots.yml`` takes the store screenshots of the live site in the app, one
       artifact per store slot.
   * - By hand: Store
     - ``store.yml`` runs one task (a lane of ``fastlane/Fastfile``) picked from its
       "What to do" list.

To run a manual workflow, open the repository on GitHub, then :menuselection:`Actions -->
Store` (or Screenshots) :menuselection:`--> Run workflow`, fill the boxes and press Run
workflow. Files a run produces are under Artifacts at the bottom of the run's page, each
as a zip.

The Store tasks
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 58 20

   * - Task
     - What it does
     - Public?
   * - download listings
     - Fetches what both stores show today (texts, images, screenshots) as the artifact
       ``store-listings``. Changes nothing.
     - No
   * - ios listing
     - Creates the App Store version ``package.json`` names if it does not exist yet, then
       uploads the texts from ``fastlane/metadata/`` (release notes included), the
       screenshots from ``fastlane/screenshots/`` and the review notes with the demo
       account from the secrets. Submits nothing.
     - No, until that version is released
   * - ios submit
     - Attaches the TestFlight build given in **build_number** to that version and sends it
       to review. You release it by hand after approval, and Apple phases it in over 7 days.
     - After you release it
   * - android listing
     - Uploads the Play texts, icon, feature graphic and screenshots from
       ``fastlane/metadata/android/en-GB/``.
     - **Yes, at once** (after Google's check)
   * - android production
     - Promotes the release on the internal track, with its notes, to production for the
       share of users in **rollout** (``0.2`` is 20 %, ``1.0`` is everyone, with no
       *android complete* afterwards).
     - Yes, to that share
   * - android complete
     - Raises the production rollout to 100 %.
     - Yes, to everyone

Each run uses one of the three jobs in ``store.yml`` and shows the other two as skipped.
**build_number** matters only to "ios submit", **rollout** only to "android production".

Play has no draft listing, so "android listing" changes the page of the app that is live
now. The App Store keeps texts per version, so "ios listing" can run any time before
submission.

What fastlane does not do
~~~~~~~~~~~~~~~~~~~~~~~~~

These stay in the consoles, filled once and checked at every release
(:doc:`store_listing`):

* App Store Connect: App Privacy, age rating, pricing and availability.
* Play Console: Data safety, the App content declarations (financial features, ads,
  target audience, sign-in details for the reviewers: :doc:`store_listing`, *Play: App
  access*), the content rating questionnaire, countries.
* Play's desktop screenshots. The Play API has no slot for them, so upload the
  ``screenshots-android-desktop`` shots by hand on the main store listing in Play
  Console.
* Pressing Release on an approved App Store version, and pausing a rollout.


One-time setup
--------------

All of it is done already; check it after a key or an account changes.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Secret
     - Used for
   * - ``ASC_KEY_ID``, ``ASC_ISSUER_ID``, ``ASC_KEY_P8_BASE64``
     - TestFlight upload and every iOS task. The key's role must be App Manager or Admin.
   * - ``ANDROID_KEY*`` (four)
     - The signed ``.aab`` (:doc:`signing`).
   * - ``PLAY_SERVICE_ACCOUNT_JSON_BASE64``
     - The internal track upload and every Android task.
   * - ``REVIEW_DEMO_USER``, ``REVIEW_DEMO_PASSWORD``
     - The App Store review sign-in and the signed-in screenshots. Never in git.

The Play service account needs, for this app only: *Release to production, exclude
devices, and use Play App Signing*, *Release apps to testing tracks*, *Manage testing
tracks and edit tester lists* and *Manage store presence*. After a new invitation the
API can answer 403 for up to a day.


The first release
-----------------

The first Capacitor version, 1.1.0, replaces "ASA Stats Mobile" 0.9.x in the same store
records (``com.asastats.app`` on both). It is an update to the stores, so it needs
release notes, and it must keep iPad support. Play Console keeps calling the app "ASA
Stats Mobile" until "android listing" uploads the new title.

#. **Compare with the stores.** Run Store with *download listings* and compare the
   artifact with ``fastlane/metadata/``. Fastlane leaves a field alone when its file is
   missing locally, so an upload never clears one. Read the differences anyway, because
   the artifact shows what reviewers saw last time.

#. **Make the build.** Set ``version`` in ``package.json`` (``1.1.0``), push to ``main``
   and wait for both workflows. Note the iOS run's build number. Its log prints
   ``Build number …``, and TestFlight in App Store Connect lists the build after 5 to 30
   minutes of "Processing".

#. **Test the store builds.** Install from TestFlight and from the Play internal testing
   link (:doc:`releasing`) and work through :doc:`beta_checklist`, including an iPad.

#. **Take the screenshots.** Run Screenshots. The address box defaults to ZRN; add a
   bundle id for the bundle scene. Historic data and Profit and loss need the demo
   account secrets, with the address linked to that account and its profit and loss
   processed (:doc:`store_listing`, *Screenshots*). Download the artifacts, choose, and
   copy:

   * all iOS folders into ``fastlane/screenshots/en-US/``, each file prefixed with its
     folder (``ipad-01-address.png``), because the folders share file names. Deliver
     sorts iPhone and iPad by pixel size;
   * Android phone, 7 inch and 10 inch into
     ``fastlane/metadata/android/en-GB/images/`` under ``phoneScreenshots``,
     ``sevenInchScreenshots`` and ``tenInchScreenshots``.

   Commit them with the texts.

#. **Fill the console forms** listed under *What fastlane does not do*, with the answers
   in :doc:`store_listing`. Play blocks a production release until they are complete.

#. **App Store.** Run Store with *ios listing*. In App Store Connect open version 1.1.0
   and read every field and screenshot. Then run *ios submit* with the build number from
   step 2. Review usually takes one to two days. After approval press :guilabel:`Release
   This Version`; the phased release then reaches all users over 7 days.

#. **Google Play, on release day.** Run *android listing*, then *android production*
   with ``0.2``. Watch Android vitals and the reviews for a few days, then run
   *android complete*.

Do the Play steps on the day the iOS version is released, so that both pages describe the
new app at the same time.


Updates
-------

First decide whether an update needs the stores at all. Anything on the website ships with
a deploy, and some features can be switched per platform on the server (:doc:`releasing`,
*What changes without a new build*). A store release is needed for native code, plugins,
icons, the splash screen, manifest or entitlement changes and the Capacitor version.

#. **Version.** Raise ``version`` in ``package.json`` (``1.1.0`` to ``1.1.1`` or
   ``1.2.0``). The App Store needs a new version for every release; CI sets the build
   numbers.

#. **Release notes, before the push.** Write them in
   ``fastlane/metadata/en-US/release_notes.txt`` (App Store, up to 4000 characters) and
   ``fastlane/metadata/android/en-GB/changelogs/default.txt`` (Play, up to 500). The Play
   notes are attached when ``android.yml`` uploads the build, so they must be in the commit
   that builds the release. Commit them with the version.

#. **Build and test.** Push to ``main``, note the iOS build number, test the TestFlight
   and internal testing builds.

#. **Listing changes, if any.** Change only the files that need it. Take new screenshots only
   when the screens look different.

#. **App Store.** Run *ios listing* (it creates the new version and uploads its notes,
   so it is needed every time), check the version in App Store Connect, then *ios submit*
   with the build number. Release by hand after approval.

#. **Google Play.** Run *android listing* only if the Play texts or images changed. Then
   *android production* with ``0.2`` and, after a few quiet days, *android complete*.

A rollout that goes wrong
~~~~~~~~~~~~~~~~~~~~~~~~~

* Play: :menuselection:`Test and release --> Production --> Releases`, then Halt rollout.
  Users who have it keep it. Fix, push (a new build reaches the internal track), and run
  *android production* again. The new release replaces the halted one.
* App Store: pause the phased release on the version page. A pause lasts up to 30 days;
  anyone can still update by hand from the App Store. A fix needs a new version and a new
  submission.

If Apple rejects a build
~~~~~~~~~~~~~~~~~~~~~~~~

Answer in App Store Connect, under the version's review messages. If the fix is on the
website or in the server settings, reply and resubmit the same build in App Store
Connect. If it needs a new build, push it and run *ios submit* with the new build number;
the version stays the same until it has been released. Listing changes go up with *ios
listing* first.


When a task fails
-----------------

* **Android, 403 or "The caller does not have permission":** the service account lacks a
  permission above, or was invited less than a day ago.
* **"Track 'internal' doesn't have any releases":** no push has uploaded a build since
  the internal track was emptied. Push, or check the "Play internal track" step of the
  last Android run.
* **iOS, "Could not find build":** the build is still processing, or the number is wrong.
  Copy it from TestFlight.
* **Deliver reports an unknown device for a screenshot:** its pixel size matches no App
  Store slot. Retake it on the right simulator; the Screenshots run checks the sizes.
* **The Play page did not change:** Google checks listing changes like releases; see
  :menuselection:`Publishing overview` for changes waiting to be sent or in review.
