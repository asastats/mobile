App lock
========

An optional lock: with it on, the app asks for Face ID, Touch ID, a fingerprint or the
phone's screen lock when it starts and after a minute or more in the background. The
local plugin in ``plugins/applock/`` does it all natively.

What a page can do
------------------

One call, which the footer's "App lock" entry makes:

.. code-block:: javascript

    await AppLock.openSettings();

It opens a small native settings screen with the switch. Turning the lock on or off
asks for the screen lock first. The setting lives in SharedPreferences (Android) or
UserDefaults (iOS), out of page script's reach, so nothing on a web page can turn the
lock off.

How it behaves
--------------

* Locked on a cold start when on, and again after 60 seconds or more away, measured on
  a monotonic clock so a changed phone clock cannot unlock it.
* While locked, a cover hides the page. A deep link or a push tap loads under the
  cover and shows after unlocking.
* If the phone no longer has a screen lock, the app does not lock, rather than
  locking the reader out for good.
* Android: the cover goes up when the app stops, not when a dialog covers it (the
  wallet chooser does not flash it). On Android 13 and later the Recents thumbnail
  is hidden; screenshots are not blocked.
* iOS: the cover goes up before the app-switcher snapshot.
  ``NSFaceIDUsageDescription`` in ``Info.plist`` is required: without it iOS ends the
  app at the first Face ID prompt.

Working on it
-------------

Every decision is in ``LockPolicy`` (Java and Swift, the same tests, 100 %). The
plugin, the cover and the settings screens only call the operating system. The
design and the reasons are in ``docs/logbook.md``.
