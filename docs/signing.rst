Signing keys and certificates
=============================

Four credentials sign or authorise builds. All of them stay outside the repository and
reach CI as base64 secrets in ``asastats/mobile``. :doc:`conduct` explains the rules for
handling them.

.. list-table::
   :header-rows: 1
   :widths: 28 30 42

   * - Credential
     - Secrets
     - Used for
   * - Android upload keystore
     - ``ANDROID_KEYSTORE_BASE64``, ``ANDROID_KEYSTORE_PASSWORD``, ``ANDROID_KEY_ALIAS``,
       ``ANDROID_KEY_PASSWORD``
     - The release ``.aab`` that goes to Play.
   * - Android debug keystore
     - ``ANDROID_DEBUG_KEYSTORE_BASE64``
     - Debug APKs, so each installs over the last. Optional.
   * - Apple Development certificate
     - ``IOS_DEV_P12_BASE64``, ``IOS_DEV_P12_PASSWORD``
     - Signing the iOS archive in CI. Optional, but see below.
   * - App Store Connect API key
     - ``ASC_KEY_ID``, ``ASC_ISSUER_ID``, ``ASC_KEY_P8_BASE64``
     - Cloud-managed signing and the TestFlight upload.


Android upload keystore
-----------------------

Play signs what users install with its own app signing key. Our keystore is the
upload key that proves a bundle comes from us.

Set the four secrets from the repository folder:

.. code-block:: bash

    base64 -w0 /path/to/upload.jks | gh secret set ANDROID_KEYSTORE_BASE64
    gh secret set ANDROID_KEYSTORE_PASSWORD
    gh secret set ANDROID_KEY_ALIAS
    gh secret set ANDROID_KEY_PASSWORD

Before you set them, check that the keystore is the right one. Its SHA-256 must equal the
upload key fingerprint shown in Play Console under Test and release, App integrity, App
signing:

.. code-block:: bash

    keytool -list -v -keystore /path/to/upload.jks -alias <keyAlias>

The ``SHA256:`` line is the one to compare.

If the keystore is lost
~~~~~~~~~~~~~~~~~~~~~~~

Request an upload key reset in Play Console, in the same App signing page. Then:

.. code-block:: bash

    keytool -genkeypair -v -keystore upload.jks -keyalg RSA -keysize 2048 \
        -validity 10000 -alias upload
    keytool -export -rfc -keystore upload.jks -alias upload \
        -file upload_certificate.pem

Upload the ``.pem``. Google takes a day or two. Replace the old upload fingerprint in the
``ANDROID_CERT_SHA256`` setting (:doc:`server_settings`) and in your key records.
Users notice nothing, because Play re-signs with the app signing key, which does not
change.


Android debug keystore
----------------------

The passwords are ``android`` and the alias is ``androiddebugkey``, which are the
Android defaults:

.. code-block:: bash

    base64 -w0 asastats-debug.keystore | gh secret set ANDROID_DEBUG_KEYSTORE_BASE64

Losing it only means one ``adb uninstall`` before the next debug APK.


Apple Development certificate
-----------------------------

Without a kept certificate, every iOS run asks Xcode to create a new Apple Development
certificate, until Apple refuses with "maximum number of certificates". CI imports one
certificate instead (the "Development certificate" step in ``ios.yml``).

The certificate is valid for one year. Renew it before October 2027.

Create or renew
~~~~~~~~~~~~~~~

#. Generate the private key and a signing request on a machine you control. Keep the key.
   To renew, reuse the same key:

   .. code-block:: bash

       openssl req -new -key ios-development.key -out ios-development.csr

#. In the Apple Developer account, open Certificates and revoke the Apple Development
   certificates CI created earlier. Keep any Distribution certificate. This also frees
   room under the certificate limit.
#. Add a new certificate: Apple Development, upload ``ios-development.csr`` and download
   the ``.cer``.
#. Combine the certificate and the key into a ``.p12``. First check that the
   certificate belongs to your key: the two public keys must be identical. Then export
   with SHA-1 and 3DES. macOS ``security import`` rejects the default encryption of
   OpenSSL 3, and CI fails at the import step with an unhelpful message.

   .. code-block:: bash

       openssl x509 -inform DER -in development.cer -out ios-development.pem
       test "$(openssl x509 -in ios-development.pem -noout -pubkey)" = \
            "$(openssl pkey -in ios-development.key -pubout)" && echo match
       openssl rand -hex 16 > ios-development.p12.password
       openssl pkcs12 -export -inkey ios-development.key -in ios-development.pem \
           -name "ASA Stats CI" -out ios-development.p12 \
           -keypbe PBE-SHA1-3DES -certpbe PBE-SHA1-3DES -macalg sha1 \
           -passout file:ios-development.p12.password

#. Set the two secrets:

   .. code-block:: bash

       base64 -w0 ios-development.p12 | gh secret set IOS_DEV_P12_BASE64
       gh secret set IOS_DEV_P12_PASSWORD < ios-development.p12.password

#. Push and read the next iOS run. The "Development certificate" step must list one valid
   identity, and the archive step must pass.


App Store Connect API key
-------------------------

Create it under Users and Access, Integrations, App Store Connect API, Team Keys, with
the Admin role. Cloud-managed signing then needs no ``.p12`` for distribution. Apple
shows the ``.p8`` once, so store it safely when you download it.

.. code-block:: bash

    gh secret set ASC_KEY_ID
    gh secret set ASC_ISSUER_ID
    base64 -w0 /path/to/AuthKey_<KEY_ID>.p8 | gh secret set ASC_KEY_P8_BASE64

With these set and the App ID configured (:doc:`firebase`), the iOS workflow archives,
signs and uploads to TestFlight on every push to ``main``.


App ID capabilities
-------------------

The App ID ``com.asastats.app`` needs three capabilities: Push Notifications,
Associated Domains and Sign in with Apple. Tick each one, then press Save at the top
right of the page. Until you save, none of the ticks count.

* Push Notifications. The Configure button opens the SSL Certificates dialog. Create
  nothing and press Done, because the app sends through Firebase with an APNs key.
* Sign in with Apple. Choose "Enable as a primary App ID" and leave the server-to-server
  endpoint empty.
* Associated Domains. Ticking the box is all of it. The domain list lives in the app's
  entitlements.

You never need to regenerate a provisioning profile by hand. CI uses cloud-managed
signing and fetches a fresh one.
