Firebase, APNs and Sign in with Apple
=====================================

Push notifications go through Firebase Cloud Messaging on both platforms. The app
registers a token with the website, and the website sends through the FCM v1 API.

Firebase project
----------------

Project ID ``asa-stats-d0931``. It is the value of ``FCM_PROJECT_ID`` on the server. It is
not the display name and not the numeric project number.

To start again:

#. In the Firebase console, create a project and turn Google Analytics off. The app has
   no use for it and it would change the store privacy answers.
#. Add an Android app with package ``com.asastats.app`` and an iOS app with bundle id
   ``com.asastats.app``. No SHA-1 is needed. Download ``google-services.json`` and
   ``GoogleService-Info.plist`` and skip the rest of each wizard. The Capacitor plugin
   does those steps.
#. Add the debug app too (next section).
#. Check under Project settings, Cloud Messaging, that Firebase Cloud Messaging API (V1)
   shows Enabled.

Adding a package name
~~~~~~~~~~~~~~~~~~~~~

The debug APK is ``com.asastats.app.debug``. Without a Firebase app for it, the Android
workflow stops with "No matching client found for package name". Add an Android app
with that package name and the nickname "ASA Stats dev", then download
``google-services.json`` again. One file now lists both packages. Replace it in:

* ``android/app/google-services.json`` and ``google-services.json`` in the repository
  root (both git-ignored),
* your key store, and
* the secret:

  .. code-block:: bash

      base64 -w0 google-services.json | gh secret set GOOGLE_SERVICES_JSON_BASE64

Both apps belong to one project, so the same service account sends to both and the
server changes nothing.

iOS config
~~~~~~~~~~

.. code-block:: bash

    base64 -w0 GoogleService-Info.plist | gh secret set GOOGLE_SERVICE_INFO_PLIST_BASE64

The iOS secret is required for every iOS build, the simulator build included. The
workflow stops without it. The Android secret is optional, but that APK has no push.


Service account for the website
-------------------------------

The website needs credentials to call the FCM API:

#. In the Google Cloud console, select the same project, then IAM and Admin, Service
   Accounts, and create ``fcm-sender``.
#. Give it the role Firebase Cloud Messaging API Admin.
#. Open it, Keys, Add key, JSON. The file goes onto the web server and never into a
   repository. :doc:`server_settings` shows where it goes.

The Firebase console's "Generate new private key" shortcut also works, but that account
has far broader rights.


APNs key
--------

#. Apple Developer, Keys, add a key named ``ASA Stats APNs`` and tick Apple Push
   Notifications service.
#. On the configure screen choose environment Sandbox and Production and key restriction
   Team Scoped (All Topics). You cannot change either after saving.
#. Download the ``.p8`` and note the Key ID. Apple shows the file once.
#. Firebase, Project settings, Cloud Messaging, the iOS app, APNs Authentication Key,
   Upload. Enter the Key ID, the Team ID ``DF2V3954Z7`` and the file.

One key serves development and production pushes. Keep the ``.p8`` out of the web server.
That server holds only the Sign in with Apple key, and a separate APNs key means a leak
there cannot send pushes.

To rotate it, create a new key, upload it to Firebase, then revoke the old one.


Sign in with Apple for the website
----------------------------------

The values the console asks for:

.. list-table::
   :widths: 40 60

   * - Services ID identifier
     - ``com.asastats.web``
   * - Services ID description
     - ``ASA Stats website``
   * - Domain, without ``https://``
     - ``www.asastats.com``
   * - Return URL
     - ``https://www.asastats.com/accounts/apple/login/callback/``
   * - Primary App ID
     - ``com.asastats.app``

The return URL must match exactly, trailing slash included.

Services ID
~~~~~~~~~~~

Identifiers, plus, Services IDs. Register ``com.asastats.web``. Open it, tick Sign in
with Apple, Configure, then enter the primary App ID, the domain and the return URL.

Key
~~~

Keys, plus, named ``ASA Stats Sign in with Apple``. Tick Sign in with Apple, Configure,
choose ``com.asastats.app``. Download the ``.p8``. The ten characters in its file name are
the Key ID, which becomes ``APPLE_KEY_ID``. This file goes onto the web server with
``chmod 600`` and the web application's user as owner.

Email relay
~~~~~~~~~~~

Users who choose "Hide My Email" get an ``@privaterelay.appleid.com`` address, and
Apple drops mail to it from unregistered senders. Their confirmation and password-reset
emails would never arrive. Under Services, Sign in with Apple for Email Communication,
Configure:

#. Add the domain ``asastats.com``. Apple shows a TXT record; add it at the DNS provider
   and press Verify.
#. Add the sender address the site uses (the ``EMAIL_DEFAULT_FROM`` setting).
#. The domain's mail must pass SPF or DKIM.

One real round trip
~~~~~~~~~~~~~~~~~~~

After any change here, sign in with Apple, sign out and sign in again on the live
site. Apple returns with a cross-site POST that allauth handles with its own cookie. The
round trip proves the session survives it.
