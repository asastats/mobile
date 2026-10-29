NativeSignIn plugin
===================

Apple and Google have their own sign-in sheets on the phone. The local plugin in
``plugins/nativesignin/`` shows them and hands the sheet's ID token to the page,
which posts it to the website, so the WebView's own session signs in. There is no
browser round trip and no ticket, unlike :doc:`webauth`.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Provider
     - iOS
     - Android
   * - Apple
     - Native sheet (``ASAuthorizationAppleIDProvider``)
     - :doc:`webauth` (no Apple sheet on Android)
   * - Google
     - Native sheet (Google's ``GoogleSignIn`` SDK)
     - Native sheet (Credential Manager); :doc:`webauth` when the phone has no
       Google account
   * - Discord, X, Reddit, GitHub
     - :doc:`webauth`
     - :doc:`webauth`

The same sheets connect Apple or Google to a signed-in account on the
Connections page.

The calls
---------

.. code-block:: javascript

    const { available } = await NativeSignIn.isAvailable({ provider });
    const { idToken, authorizationCode, givenName, familyName } =
        await NativeSignIn.signIn({ provider, nonce, serverClientId });

``provider``
    ``apple`` or ``google``. The list must equal ``NATIVE_PROVIDERS`` in the
    frontend's ``core/views_appnative.py``. Android accepts only ``google``.

``nonce``
    43 base64url characters from the website's ``/app/auth/native/nonce/``. It is
    single-use and valid for five minutes. Apple's sheet gets its SHA-256 (hex) and
    Google's gets it as is. The ID token carries it back, and the server checks it.

``serverClientId``
    Google only: the website's Google client id, which the nonce endpoint returns.
    The token is issued to it, so the server accepts it. Checked against
    ``<digits>-<letters and digits>.apps.googleusercontent.com``.

``isAvailable`` answers ``false`` for other providers, for Apple on Android and on
Android without Play services. An app version without the plugin rejects every
call, and the page reads that as "not available" and uses :doc:`webauth`.

``signIn`` resolves with the ID token. Apple adds the authorization code (the
server trades it for the refresh token it needs to revoke the account on
deletion) and, on the first sign-in only, the name. It rejects with one of these
names:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Name
     - Meaning
   * - ``invalid``
     - The provider, the nonce or a client id failed validation.
   * - ``busy``
     - A sheet is already open. One at a time.
   * - ``cancelled``
     - The user closed the sheet. The page says nothing.
   * - ``unavailable``
     - Android: no Google account on the phone. The page falls back to
       :doc:`webauth` for sign-in, and to "connect Google on the website" for
       Connections.
   * - ``failed``
     - Anything else. The page says "Sign-in did not finish".

What happens after the sheet
----------------------------

The page (``signIn.ts`` in the frontend's ``wallet/src/app/``) posts a hidden form to
``/app/auth/native/`` with the provider, the token, Apple's code and name,
``process`` (``login`` or ``connect``) and ``next``. The server verifies the token
against the provider's keys (issuer, audience, expiry, signature), checks the nonce,
and hands the result to django-allauth, which signs in, shows its signup form for a
new account, or connects. The form post, rather than ``fetch``, lets allauth's
answer become the next page.

Google client ids
-----------------

All of them are in the Google Cloud project ``asa-stats``, together with the
website's web client. Android clients have no secret; they bind the package name and
the signing certificate's SHA-1:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Client
     - Package or bundle id
     - Bound to
   * - Android, Play
     - ``com.asastats.app``
     - Play app signing key
   * - Android, upload
     - ``com.asastats.app``
     - Upload key
   * - Android, debug
     - ``com.asastats.app.debug``
     - The kept CI debug key
   * - iOS
     - ``com.asastats.app``
     - Team ``DF2V3954Z7``; its client id is ``GIDClientID`` in ``Info.plist`` and
       its reversed id is a URL scheme there

A new signing key (a new debug keystore, a new upload key) needs its own Android
client, or Google sign-in fails on that build with "Sign-in did not finish". The
website accepts tokens for its web client and the iOS client
(``GOOGLE_IOS_CLIENT_ID`` in the frontend's settings).

Apple needs the Sign in with Apple capability on the App ID (:doc:`signing`) and the
``com.apple.developer.applesignin`` entitlement, which ``App.entitlements`` carries.
The website accepts the bundle id as a second Apple audience next to its Services ID.

Working on it
-------------

* The checks and the error mapping sit in ``NativeSignInRequest`` (Java and Swift)
  and are tested to 100 %. The plugin classes only call the operating system.
* A change that adds a parameter, a provider or a failure name needs a second
  reviewer first (:doc:`conduct`), as for :doc:`webauth`.
* Real sign-ins need a real account and cannot be automated. The Appium test checks
  the Connections button and the round trip through the bridge; the device rows are
  in :doc:`beta_checklist`.
