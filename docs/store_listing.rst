Store listings
==============

Both stores list the app under ``com.asastats.app``.

Keep the listing and the privacy policy in step. The policy is at
https://www.asastats.com/asm-privacy/ and account deletion is described at
https://www.asastats.com/account-deletion/. If the app starts collecting something new,
change the policy, the two data forms below and the review notes in the same release.

Rules the texts must follow
---------------------------

* No plans, prices or ASASTATS payments anywhere in the store texts or screenshots. The
  review notes rely on Apple guideline 3.1.3(f), a free companion to a paid web service.
* No other companies' names in the keywords (Pera, Defly, Tinyman). Apple rejects
  keywords that are other apps' trademarks (guideline 2.3.7).
* Name the wallets in the description only while wallet sign-in works on the build under
  review. Otherwise remove those words.
* Name every social sign-in provider only if social sign-in ships in that build.
* iPad support stays. The earlier app shipped for iPhone and iPad, and an update cannot
  drop a device family. 13 inch iPad screenshots are therefore required.
* Screenshots show ZRN, our own testing address, so every figure in them is public
  Mainnet data. If swaps are hidden on iOS, they must not appear in the iOS screenshots.


Swap widgets on iOS
-------------------

Apple guideline 3.1.5(iii) ties crypto exchange features to licensing per region, and a
reviewer may read swaps that way. For a first submission, or after a rejection, hide the
swap widgets on iOS with the server setting and change nothing in the metadata:

.. code-block:: text

    APP_HIDDEN_WIDGETS_IOS=asastats,folks,haystack,hogswap,dustsweep,swapcore

The listing texts never mention swaps, so the switch can change at any time without a new
build or a new submission.


App Store Connect: App Privacy
------------------------------

Data is collected: yes. Tracking: no. There is no advertising SDK, and nothing is used
across other companies' apps or sites.

Every type below is linked to the user, is not used for tracking, and has one purpose,
App Functionality.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Category and type
     - Why it is declared
   * - Contact Info, Email Address
     - Account sign-up, confirmation, password reset.
   * - Contact Info, Name
     - Optional first and last name, and the name a social sign-in shares.
   * - Identifiers, User ID
     - The account, and the identifier a social sign-in shares.
   * - Identifiers, Device ID
     - The push notification token.
   * - Financial Info, Other Financial Info
     - Wallet addresses the user links, bundles, and profit-and-loss figures they enter.
   * - User Content, Other User Content
     - Bundle names, alert rules, settings.

Not collected: Health and Fitness, Location, Sensitive Info, Contacts, Browsing History,
Search History, Purchases, Payment Info, Credit Info, Photos and Videos, Audio, Gameplay,
Customer Support, Diagnostics, Usage Data.

Three judgment calls sit behind that table:

* The push token is declared as Device ID. Apple aims that type at advertising
  identifiers and many apps leave a push token out. Declaring it is the conservative
  choice and costs nothing at review.
* Wallet addresses are public, but linked to an account they describe someone's holdings.
  A reviewer expects them declared.
* Server logs (IP address, requested page, about two weeks) are not declared. Apple does
  not count data processed to serve a request and kept only for operations and security as
  collected. Declare Diagnostics, Other Diagnostic Data if you prefer to be stricter.


Google Play: Data safety
------------------------

Collected: yes. Encrypted in transit: yes. Shared: none. Firebase Cloud Messaging, the
Apple push service and the sign-in providers act as service providers, which Play does not
count as sharing. Deletion on request: yes, in the app (:menuselection:`Profile -->
Account --> Delete account`) and at the account deletion URL.

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Data type
     - Optional
     - Purposes
   * - Personal info, Email address
     - yes
     - Account management, App functionality
   * - Personal info, Name
     - yes
     - Account management
   * - Personal info, User IDs
     - yes
     - Account management, App functionality
   * - Financial info, Other financial info
     - yes
     - App functionality
   * - App activity, Other user-generated content
     - yes
     - App functionality
   * - Device or other IDs
     - yes, only with alerts on
     - App functionality

Each type is stored with the account, so "processed ephemerally" is no. Not collected:
location, contacts, messages, photos and videos, audio, files, calendar, health and
fitness, web browsing, app info and performance (there is no crash reporting or analytics
SDK), purchase history, payment info.

Other Play forms
~~~~~~~~~~~~~~~~

* Financial features: declare a cryptocurrency portfolio tracker, information only. The
  app is non-custodial, with no keys and no exchange. Answer no to holding user funds.
* Ads: none.
* Target audience: 18 and over.
* Government app, News app: no.
* App access: filled in by hand, because the Play API has no such field (``notes.txt``
  goes to Apple only). See *Play: App access* below.


Age ratings
-----------

App Store Connect: answer None or No everywhere. Unrestricted web access is No, because
the app loads only asastats.com and another site's link opens in a separate browser sheet.
Expect 4+. If a reviewer disagrees about web access, Yes raises the rating to 18+ and
costs nothing else.

Google Play IARC questionnaire: category All Other App Types. Violence, sexuality,
language, controlled substances, user interaction, location sharing, digital purchases,
gambling and web browsing are all No. Expect Everyone, PEGI 3, USK 0.


Text limits
-----------

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Field
     - Limit
     - Notes
   * - App name, both stores
     - 30
     - ``ASA Stats``
   * - Subtitle, App Store
     - 30
     - ``Algorand portfolio tracker``
   * - Promotional text, App Store
     - 170
     - Can change without a review.
   * - Short description, Play
     - 80
     - ``Track Algorand portfolios: ASAs, NFTs and DeFi positions, priced every block.``
   * - Description, both
     - 4000
     - In ``fastlane/metadata/``, see *Where the texts live* below.
   * - What's new / release notes
     - 4000 / 500
     - Play calls it release notes.
   * - Keywords, App Store
     - 100
     - Comma-separated, no spaces. Words already in the name and subtitle count, so do not
       repeat them.

Categories: Finance on both stores, no secondary App Store category. Support and
marketing URL: https://www.asastats.com/.


Where the texts live
~~~~~~~~~~~~~~~~~~~~

The texts are files in ``fastlane/metadata/``, and the Store workflow uploads them
(:doc:`publishing`). Change them there and nowhere else. The App Store listing is en-US,
the Play listing en-GB.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Field
     - File
   * - App Store name, subtitle
     - ``en-US/name.txt``, ``en-US/subtitle.txt``
   * - App Store description, keywords, promotional text
     - ``en-US/description.txt``, ``en-US/keywords.txt``, ``en-US/promotional_text.txt``
   * - App Store What's New
     - ``en-US/release_notes.txt``
   * - App Store URLs
     - ``en-US/support_url.txt``, ``marketing_url.txt``, ``privacy_url.txt``
   * - App Store category
     - ``primary_category.txt``
   * - App Store review notes and contact
     - ``review_information/notes.txt``, ``review_information/email_address.txt``
   * - Play title, short and full description
     - ``android/en-GB/title.txt``, ``short_description.txt``, ``full_description.txt``
   * - Play release notes
     - ``android/en-GB/changelogs/default.txt``
   * - Play promo video
     - ``android/en-GB/video.txt``
   * - Play icon, feature graphic
     - ``android/en-GB/images/icon.png``, ``featureGraphic.png``

The description is the same text on both stores, so change ``description.txt`` and
``full_description.txt`` together. It names the Pera and Defly wallets, which sign in on
the current builds; remove those words if a build under review loses wallet sign-in (see
the rules at the top).


Screenshots
-----------

``screenshots.yml`` makes every screenshot slot below except Apple Watch, Android XR and,
while GitHub's Xcode has no Duo simulator, iPhone Duo. It checks each shot's pixel size.
:doc:`publishing` says where the files go.

.. list-table::
   :header-rows: 1
   :widths: 38 32 30

   * - Slot, as the console names it
     - Size
     - Count
   * - App Store: iPhone with Dynamic Island, medium display (required)
     - 1206 by 2622, or 1179 by 2556
     - 3 to 10
   * - App Store: iPhone with Dynamic Island, large display
     - 1320 by 2868, 1290 by 2796 or 1260 by 2736
     - Optional
   * - App Store: iPad 13 inch display (required)
     - 2064 by 2752, or 2048 by 2732
     - 3 to 10
   * - App Store: iPhone Duo
     - 1398 by 2034, or 2007 by 2853
     - Required for builds with the iOS 27.1 SDK, from April 2027
   * - App Store: Apple Watch
     - Not offered: there is no watchOS app
     - 0
   * - Play: phone (required)
     - Exactly 9:16, 1080 by 1920
     - 2 to 8, 4 or more at 1080 px or more for promotion
   * - Play: 7 inch tablet (required)
     - Exactly 9:16, 1080 by 1920
     - 1 to 8
   * - Play: 10 inch tablet (required)
     - Exactly 9:16, 1440 by 2560 (sides 1080 to 7680)
     - 1 to 8
   * - Play: desktop
     - 2560 by 1440, landscape. Uploaded by hand, because the Play API has no desktop slot
     - Optional, 4 to 8
   * - Play: Android XR
     - Not made; needs an XR emulator
     - Optional
   * - Play: feature graphic (required)
     - 1024 by 500, PNG or JPEG, no alpha
     - 1
   * - Play: app icon (required)
     - 512 by 512 PNG
     - 1

The scenes are in ``functional_tests/screenshots.json``. Every device gets the same eight,
in this order:

#. the address page;
#. the same page with its first asset opened;
#. the bundle page with its first NFT collection opened (ZRN holds no NFTs);
#. the Historic data page;
#. the Profit and loss page;
#. the bundle page in the ``aqua`` theme;
#. the Appearance page's theme list in the ``cyberpunk`` theme;
#. the address page in the dark theme.

The default address is ZRN (``ZRNRW3X4WMRJZLP2UZR5PECN4A23SW7QETVR4H53F6FFG3NHC6MVSLMQPM``).
The run takes Historic data, Profit and loss and Appearance only when it signs in with the
demo account. Appearance also needs the account at the Asastatser tier or higher, or the
site sends it to the subscriptions page and the scene fails waiting for the tabs. Profit
and loss shows only addresses linked to that account whose profit and loss is already
processed. Play takes at most 8 phone shots, so a ninth scene has to replace one of these.

Each scene can set:

``path``
    The page. ``{address}`` and ``{bundle}`` are the run's inputs; a scene whose input is
    empty is skipped.
``ready``
    A selector, or a list of selectors, that must exist before the shot.
``ready_script``
    JavaScript that returns true once the page is drawn.
``open``
    Opens the first matching ``<details>`` row and scrolls it to the top, below the
    status bar.
``scroll_to``
    Scrolls the first match to the top, below the status bar.
``theme``
    The site theme, such as ``asastats-dark``, ``aqua`` or ``cyberpunk`` (the names in the
    frontend's ``AVAILABLE_THEMES_BY_SCHEME``).
``settle``
    Seconds to wait before the shot, 5 by default.
``signed_in``
    Skip the scene unless the run signs in.

On Android the test hides the system bars for every shot, so the tablets show no taskbar.

Not made, and all optional: App Store *App Previews* (up to three short screen-recording
videos per device slot) and the *Header and Search Results* assets (a product page banner,
5244 by 2950 or 3840 by 1646, and a search result image). Without a search result asset
the store shows the first screenshots there. Fastlane uploads neither and leaves any that
were added by hand.


Review notes
------------

The notes are ``fastlane/metadata/review_information/notes.txt``; *ios listing* uploads
them with the demo account's email and password from the secrets ``REVIEW_DEMO_USER`` and
``REVIEW_DEMO_PASSWORD``, which App Store Connect shows in its Sign-In Information fields.
The account needs a plan with every widget and a linked address with real holdings. Never
commit its credentials. Play's App access form takes the same account, typed in by hand.


Play: App access
~~~~~~~~~~~~~~~~

Play's reviewers sign in with the account given in this form. Do it once, and again only
when the demo account's password changes.

#. In Play Console open :menuselection:`Monitor and improve --> Policy and programs -->
   App content --> Sign-in details` (formerly *App access*).
#. Choose "All or some functionality in my app is restricted", then
   :guilabel:`Add instructions`.
#. Name ``Demo account``; the username and password of the account the secrets
   ``REVIEW_DEMO_USER`` and ``REVIEW_DEMO_PASSWORD`` hold; leave "No other information is
   required" unticked, and paste this into the field for other information
   (500 characters at most):

   .. code-block:: text

      The start screen field takes only an Algorand address or .algo name, not a login. To sign in:
      1. Scroll down to the footer and tap "Log in".
      2. Enter the username and password above on the next screen.
      3. Tap "Log in".
      This opens account features (bundles, historic data, P&L, alerts).
      No account is needed to look up an address, for example ZRNRW3X4WMRJZLP2UZR5PECN4A23SW7QETVR4H53F6FFG3NHC6MVSLMQPM or devpool.asastats.algo.
      Non-custodial: it never asks for private keys and holds no funds.

#. :guilabel:`Add`, then :guilabel:`Save`. App content then shows the row as done.
