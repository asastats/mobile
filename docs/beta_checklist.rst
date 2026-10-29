Beta checklist
==============

Run this on every release candidate, on the store builds (TestFlight internal group, Play
internal testing) and against production. Do not use the debug APK: its package and
signing key differ, so App Links and social sign-in cannot work on it.

Copy the tables into a sheet for each round. Fill a cell with ``ok`` or with what you saw;
"nothing happened" is a result. Write ``n/a`` where a row does not apply. Anything that is
not ``ok`` goes into a problems list with the device. How to get the builds onto phones is
in :doc:`releasing`.

Devices
-------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Device
   * - iP
     - iPhone
   * - iPad
     - iPad. Required, because the listing supports iPad.
   * - A
     - Android phone
   * - As
     - Small Android phone (5.5 inch or 720 px wide, or less)
   * - Ao
     - Oldest Android you can find (minSdk 24, Android 7)

Before starting, sign out on every device. Have the review demo account and one account
of your own ready, with alerts and a linked address.


First launch and the shell
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Install, open: splash shows the wordmark, then the home page; splash never sticks
     -
     -
     - ✓
     -
     -
   * - App name under the icon is "ASA Stats"; icon looks right (Android: round and squircle masks)
     -
     -
     - ✓
     -
     -
   * - Status bar and notch / home indicator: nothing covered at the top or bottom
     -
     -
     - ✓
     -
     -
   * - Rotate to landscape and back (iPad especially): layout holds
     -
     -
     - ✓
     -
     -
   * - Android back: closes an open dialog first, then goes back a page, on the first page sends the app to the background
     - n/a
     - n/a
     - ✓
     -
     -

Pages
-----

Open each, scroll to the bottom, tap one link. Check nothing overlaps, nothing is cut off, and the footer has no App Store / Play links.

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Page
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Home ``/`` and ``/home/``
     -
     -
     - ✓
     -
     -
   * - An address page (58-character address)
     -
     -
     - ✓
     -
     -
   * - The same address in the dynamic and dynamic compact layouts
     -
     -
     -
     -
     -
   * - A ``.algo`` name
     -
     -
     - ✓
     -
     -
   * - A bundle page (40-character id)
     -
     -
     - ✓
     -
     -
   * - An NFT collection on an address
     -
     -
     - ✓
     -
     -
   * - Profile: settings, appearance, account, addresses, link an address, API, authorize
     -
     -
     -
     -
     -
   * - Bundle add, edit, delete
     -
     -
     -
     -
     -
   * - Export
     -
     -
     - ✓
     -
     -
   * - FAQ, Features, About, Methodology, Tokenomics, Disclaimer, sitemap
     -
     -
     -
     -
     -
   * - Subscriptions: plans shown as information, no subscribe buttons or steps
     -
     -
     - ✓
     -
     -
   * - ``/asm-privacy/`` and ``/account-deletion/``
     -
     -
     - ✓
     -
     -
   * - A page that does not exist: the site's "not found", not "No connection"
     -
     -
     - ✓
     -
     -

No buying in the app (App Review rejects this)
----------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Free account: every place a tier is needed says "Not included in your current plan." with no link
     -
     -
     -
     -
     -
   * - No link anywhere to ``/subscriptions/`` from a menu, widget or message
     -
     -
     -
     -
     -
   * - No ASASTATS price or "subscribe" text on any page above
     -
     -
     - accepted
     -
     -

Widgets
-------

With the demo account. For each: opens, shows data, its main action works.

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Widget
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Historic data: chart draws; change the range
     -
     -
     -
     -
     -
   * - Real-time refresh: values change with blocks; scroll position kept
     -
     -
     -
     -
     -
   * - Profit and loss: periods, drill-down, winners and losers
     -
     -
     -
     -
     -
   * - Alerts: see section 6
     -
     -
     -
     -
     -
   * - Swap widgets (ASA Stats, Folks, Haystack, HOGSWAP routers, Dust Sweep): quote shown; hidden on iOS if ``APP_HIDDEN_WIDGETS_IOS`` is set
     -
     -
     -
     -
     -
   * - A swap signed in Pera on Android (small amount), if swaps stay on
     - n/a
     - n/a
     -
     -
     -
   * - Historic and real-time refresh after 2 minutes in the background: recover by themselves
     -
     -
     -
     -
     -

Sign-in, sign-out, account
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Method
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Email and password; wrong password shows the error
     -
     -
     -
     -
     -
   * - Sign up with email; the confirmation link from the mail opens in the app
     -
     -
     -
     -
     -
   * - Password reset link from the mail
     -
     -
     -
     -
     -
   * - Sign in with Apple. iOS: Apple's own sheet, no browser; Android: the browser sheet
     -
     -
     -
     -
     -
   * - Google: Google's own sheet (Android, iOS); a phone without a Google account falls back to the browser sheet
     -
     -
     - ✓
     -
     -
   * - Connections: connect Google from the app (Google's sheet); without the sheet, "Connect Google on the website"
     -
     -
     - ✓
     -
     -
   * - Connections (iOS): connect Apple with Apple's sheet
     -
     -
     -
     -
     -
   * - GitHub
     -
     -
     -
     -
     -
   * - Discord
     -
     -
     -
     -
     -
   * - Reddit
     -
     -
     -
     -
     -
   * - X
     -
     -
     -
     -
     -
   * - Social sign-in on Android without Chrome 137+ as the default browser: the "needs Chrome 137" message for Discord, X, Reddit, GitHub and Apple; Google still works (its own sheet); email/wallet sign-in still work
     -
     -
     -
     -
     -
   * - Social sign-in on iOS before 17.4: the "needs iOS 17.4" message for Discord, X, Reddit and GitHub; Apple and Google still work (their own sheets)
     -
     -
     -
     -
     -
   * - After a social sign-in in the app, Chrome on the phone is signed out of the site
     -
     -
     -
     -
     -
   * - New social account: the username form after the provider, then signed in
     -
     -
     -
     -
     -
   * - Pera wallet sign-in
     -
     -
     - ✓
     -
     -
   * - Defly wallet sign-in
     -
     -
     - ✓
     -
     -
   * - Kibisis and Lute are not offered
     -
     -
     - ✓
     -
     -
   * - WalletConnect / EVM, or absent
     -
     -
     - ✓
     -
     -
   * - Close the app fully, reopen: still signed in
     -
     -
     -
     -
     -
   * - Restart the phone, reopen: still signed in
     -
     -
     -
     -
     -
   * - Sign out: signed out, and section 6 "sign-out" row passes
     -
     -
     -
     -
     -
   * - Delete account: the captcha shows and can be solved; after confirming, signed out and cannot sign in again
     -
     -
     -
     -
     -

Use a throwaway account for the last row.

Alerts and notifications
------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Alerts modal offers Notify this device (not "Add to Home Screen")
     -
     -
     -
     -
     -
   * - Tap it, allow: "This device is on."
     -
     -
     -
     -
     -
   * - Deny the permission instead: a clear message, nothing broken
     -
     -
     -
     -
     -
   * - Test notification from the server arrives (app in the foreground; Android shows it in the shade too, and its tap opens the page)
     -
     -
     - ✓
     -
     -
   * - … with the app in the background
     -
     -
     - ✓
     -
     -
   * - … with the app closed (swiped away): tap opens the right page
     -
     -
     -
     -
     -
   * - Android: Settings > Apps > ASA Stats > Notifications lists one "Alerts" channel
     -
     -
     - ✓
     -
     -
   * - A real rule fires (price or total crossing): notification arrives, tap opens the page
     -
     -
     -
     -
     -
   * - Notification icon on Android is legible (white wordmark, purple accent)
     - n/a
     - n/a
     -
     -
     -
   * - Reopen the modal later: still "on", no new permission prompt
     -
     -
     -
     -
     -
   * - Sign out, run the test again: the phone is not counted
     -
     -
     -
     -
     -

App lock
--------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Footer "App lock" opens the native settings screen; turning it on asks for Face ID, fingerprint or the screen lock
     -
     -
     - ✓
     -
     -
   * - Close the app fully, reopen: the lock asks before the page shows
     -
     -
     - ✓
     -
     -
   * - Away less than a minute: no prompt; a minute or more: the prompt
     -
     -
     - ✓
     -
     -
   * - A push tap or a deep link while locked: the page shows after unlocking
     -
     -
     -
     -
     -
   * - App switcher / Recents does not show the page while locked (Android 13+, iOS)
     -
     -
     -
     -
     -
   * - Turning it off asks again; nothing on a web page can turn it off
     -
     -
     - ✓
     -
     -


Exports and sharing
-------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - CSV export from an address: share sheet opens with the file
     -
     -
     -
     -
     -
   * - Save it to Files / Drive, open it: right content
     -
     -
     -
     -
     -
   * - Tax zip (several MB): shares; the app does not crash or freeze
     -
     -
     -
     -
     -
   * - A failed export (e.g. airplane mode): the site's error message
     -
     -
     -
     -
     -

Links
-----

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Another site's link (explorer, Vestige, footer social icon): opens in a browser sheet; closing it returns to the app
     -
     -
     - ✓
     -
     -
   * - On an address page, a link to another site (a listed NFT): close the sheet with its X, then again with Back. Both times the app is back on that address page, not the home page
     -
     -
     - ✓
     -
     -
   * - A ``https://www.asastats.com/faq/`` link tapped in Messages / Keep: opens in the app
     -
     -
     - n/a
     -
     -
   * - A same-site link that opens a new tab: opens in place
     -
     -
     -
     -
     -
   * - ``mailto:`` link: mail app opens
     -
     -
     -
     -
     -
   * - An asastats.com address link pasted in Notes / Messages (iOS) or Messages / Keep (Android), tapped: opens in the app on that page
     -
     -
     -
     -
     -
   * - Android 11 or older: an address link tapped in Messages / Keep opens in the app (only the 58-character address pattern; other links open in the browser there)
     -
     -
     - ✓
     -
     -
   * - The same with the app closed
     -
     -
     - ✓
     -
     -
   * - ``https://www.asastats.com/accounts/login/`` link tapped in Notes/Messages: opens in the browser, not the app (excluded on purpose)
     -
     -
     - ✓
     -
     -

Offline
-------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Airplane mode, open the app: "No connection" page
     -
     -
     - ✓
     -
     -
   * - Retry while offline: same page again
     -
     -
     - ✓
     -
     -
   * - Back online, Retry: the site loads
     -
     -
     - ✓
     -
     -
   * - Go offline while on a page, tap a link: "No connection"; back online, Retry: the page the link went to
     -
     -
     - ✓
     -
     -

Themes and appearance
---------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Phone in dark mode: the site follows; status bar text readable
     -
     -
     - ✓
     -
     -
   * - Phone in light mode: same
     -
     -
     - ✓
     -
     -
   * - Change the theme in the profile (a light and a dark one): status bar follows
     -
     -
     -
     -
     -
   * - Larger text size in the phone's settings: pages still usable
     -
     -
     -
     -
     -

Haptics and small things
------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 13 13 13

   * - Check
     - iP
     - iPad
     - A
     - As
     - Ao
   * - Copy an address: copied, a light tap felt
     -
     - n/a
     -
     -
     -
   * - Pull the page down at the top: nothing odd (no blank screen)
     -
     -
     - ✓
     -
     -
   * - Leave the app for an hour, come back: the page works (sign-in kept, widgets update)
     -
     -
     -
     -
     -
