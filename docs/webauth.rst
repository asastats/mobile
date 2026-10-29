WebAuth plugin
==============

Google refuses sign-in inside a WebView. The local plugin in ``plugins/webauth/`` opens the system browser
sheet for a social sign-in and hands a one-time ticket back to the page. Apple on iOS and
Google use their native sheets instead where the phone has one (:doc:`nativesignin`);
WebAuth handles the other providers and is the fallback for those two. It ships as a
local npm package (``asastats-webauth``) with a Java implementation for Android and a
Swift one for iOS.

Because every page on www.asastats.com can call it, the plugin trusts nothing that
JavaScript passes in.

The call
--------

.. code-block:: javascript

    const { url } = await WebAuth.start({ provider, challenge, next });

``provider``
    One of the provider ids the website knows. The native list must equal ``PROVIDERS``
    in the frontend's ``core/views_appauth.py``. Add a provider on both sides.

``challenge``
    A 43-character base64url string, ``^[A-Za-z0-9_-]{43}$``. The page keeps the matching
    verifier and redeems the returned ticket with it.

``next``
    Where to land after sign-in. The native side passes it as a query value only.

The promise resolves with the callback URL, ``https://www.asastats.com/app/auth/return/``
plus a ``ticket`` query. It rejects with one of five names, which the page shows as the
error message:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Name
     - Meaning
   * - ``invalid``
     - The provider or the challenge failed validation.
   * - ``busy``
     - A sign-in sheet is already open. One at a time.
   * - ``unsupported``
     - The device cannot verify an https callback. See below.
   * - ``cancelled``
     - The user closed the sheet.
   * - ``failed``
     - The sheet ended with a callback that is not ours, or any other failure.

What the plugin refuses to take from JavaScript
-----------------------------------------------

* There is no ``url`` parameter and no callback scheme. The native side builds the start
  URL from the ``server.url`` origin and ``/app/auth/start/<provider>/``. A page cannot
  use the plugin to open an auth sheet on another site.
* The callback host and path are constants in native code. The plugin returns only a URL
  that matches them exactly.
* ``next`` never becomes part of the path.

A cross-site scripting hole on the site therefore gains one thing: it can make the user
sign in to their own account through a visible system sheet.

Why the callback is an https URL
--------------------------------

A custom URL scheme returns to whichever app registered it. A malicious app could open its
own sheet on our start URL with its own challenge and receive the ticket. Both platforms
can instead bind an https callback to the app that the domain names:

iOS 17.4 and later
    ``ASWebAuthenticationSession`` with an https callback. The system delivers it only to
    an app with the ``webcredentials:www.asastats.com`` associated domain, which the
    ``apple-app-site-association`` file lists. The plugin keeps the session ephemeral, so
    nothing is shared with Safari.

Android with Chrome 137 or later
    Chrome's Auth Tab in https mode. Chrome checks Digital Asset Links, which
    ``assetlinks.json`` serves, and returns ``RESULT_VERIFICATION_FAILED`` to an app that
    the domain does not name. The Auth Tab has no ephemeral mode, so ``start`` on the
    website logs the browser session out first.

Devices that cannot verify, which means iOS 15 to 17.3 and Android with another default
browser or an older Chrome, get the ``unsupported`` rejection. The page then says that
social sign-in needs iOS 17.4 or Chrome 137 and offers email or wallet sign-in. No
custom-scheme fallback exists, on purpose. Apple on iOS and Google do not depend on
this: their native sheets (:doc:`nativesignin`) work on those devices too.

Working on it
-------------

* The logic sits in ``WebAuthController`` and ``WebAuthRequest`` (Android) and the matching
  Swift types, behind a small launcher protocol. Only the thin adapter calls the operating
  system. Keep it that way, because the 100 % coverage gate counts the logic and tests
  drive a fake launcher.
* A change that adds a parameter, a native method or a new failure name needs a decision
  from a second reviewer first (:doc:`conduct`).
* The Java and Swift sources are not part of the generated API pages. Read the classes
  directly; their Javadoc and doc comments carry the contracts.
