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
* Take screenshots from a store build with a demo account, so no real holdings show. If
  swaps are hidden on iOS, they must not appear in the iOS screenshots.


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
count as sharing. Deletion on request: yes, in the app (Profile, Account, Delete account)
and at the account deletion URL.

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
* App access: "All or some functionality is restricted", with the demo account below.
  Add the instruction that no account is needed to look up an address.


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
     - Draft it as one line about tracking Algorand portfolios.
   * - Description, both
     - 4000
     - The current text has the sections Track, Understand, Stay informed and Your
       account, your keys.
   * - What's new / release notes
     - 4000 / 500
     - Play calls it release notes.
   * - Keywords, App Store
     - 100
     - Comma-separated, no spaces. Words already in the name and subtitle count, so do not
       repeat them.

The current description covers live refresh with every block, bundles and alerts as
notifications. It also states that the app never asks for, sees
or stores a private key or recovery phrase, that there are no ads or tracking, and that it
is not a wallet or an exchange and gives no financial advice.

Categories: Finance on both stores, no secondary App Store category. Support and
marketing URL: https://www.asastats.com/.


Screenshot sizes
----------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - Slot
     - Size, portrait
     - Count
   * - iPhone 6.9 inch (required)
     - 1320 by 2868, or 1290 by 2796
     - 3 to 10
   * - iPhone 6.5 inch
     - Not needed; Apple scales the 6.9 inch set
     - 0
   * - iPad 13 inch (required)
     - 2064 by 2752, or 2048 by 2732
     - 3 to 10
   * - Play phone (required)
     - 9:16, 1080 by 1920 or more
     - 2 to 8, 4 or more for featuring
   * - Play 7 and 10 inch tablet
     - 9:16 or 16:9, 320 to 3840 px per side
     - Optional
   * - Play feature graphic (required)
     - 1024 by 500, PNG or JPEG, no alpha
     - 1
   * - Play app icon (required)
     - 512 by 512 PNG
     - 1

Use the same scenes in the same order on every device: an address page with holdings and
the total, the same page with live refresh running, a bundle, an NFT collection with
floor and estimated values, the historic chart, profit and loss, the alerts modal beside a
received notification, and a dark theme.


Review notes
------------

Paste this into App Store Connect, App Review Information, Notes. Fill the demo account in
from the account the team maintains for review; it needs a plan with every widget and a
linked address with real holdings. Never commit its credentials.

.. code-block:: text

    ASA Stats is a portfolio tracker for the Algorand blockchain. It reads public chain
    data and shows what an address holds and what it is worth. The app is the same service
    as www.asastats.com, which it loads, with native features added: push notifications
    for alerts (Firebase Cloud Messaging and APNs), Universal Links for asastats.com
    pages, native share for CSV exports, an offline screen, and Sign in with Apple.

    No account is needed to look up an address. To see account features, sign in with the
    demo account below.

    Non-custodial: the app never asks for, sees or stores private keys or recovery
    phrases. It holds no funds and transmits none. It is not a wallet. Anything that needs
    a signature is signed by the user in their own separate wallet app.

    Nothing is sold in the app. Some account features belong to plans that are obtained on
    the website, outside the app. The app shows no prices, no purchase buttons and no links
    or instructions for buying. It is a free companion to that web service (Guideline
    3.1.3(f)).

    Account deletion: Profile -> Account -> Delete account. The account is closed at once,
    push notifications stop at once, and all data is permanently deleted within 7 days.

    To try alerts: sign in, open Alerts, tap the button to turn on notifications and allow
    them, then add a rule, for example the ALGO price rising above a value just over the
    current price.

    Demo account (email and password):
    Email: <demo email>
    Password: <demo password>

    Contact: <support email>
