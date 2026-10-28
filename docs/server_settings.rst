Website settings for the app
============================

The app needs a few settings on the website's server. They live in the frontend
repository: put every key in ``deploy/.env.production`` and let the ``projectsetup``
role write the server's ``.env`` (mode 600). The role writes only the keys listed in
``roles/projectsetup/tasks/environment.yml``, and a key you leave out keeps its safe
default.

.. list-table::
   :header-rows: 1
   :widths: 30 22 48

   * - Key
     - Default
     - Purpose
   * - ``FCM_PROJECT_ID``
     - empty
     - Firebase project ID. Native push is on only when this and the next key are both
       set. One alone counts as off.
   * - ``FCM_CREDENTIALS_FILE``
     - empty
     - Absolute path, on the server, of the service-account JSON.
   * - ``APPLE_CLIENT_ID``, ``APPLE_KEY_ID``, ``APPLE_TEAM_ID``, ``APPLE_PRIVATE_KEY_FILE``
     - empty
     - Sign in with Apple. The button appears only when all four are set and the file is
       readable.
   * - ``APPLE_APP_ID_PREFIX``
     - the Team ID
     - Prefix in ``apple-app-site-association``. Change it only if it differs from the
       Team ID.
   * - ``ANDROID_CERT_SHA256``
     - empty
     - Comma-separated signing fingerprints for ``assetlinks.json``.
   * - ``APP_HIDE_PURCHASE``
     - ``ios,android``
     - Platforms where purchase links are hidden.
   * - ``APP_HIDDEN_WIDGETS_IOS``, ``APP_HIDDEN_WIDGETS_ANDROID``
     - empty
     - Comma-separated widget names to hide on one platform, for example
       ``hogswap,swapcore``. Takes effect without a new app build.
   * - ``APP_UNSUPPORTED_WALLETS``
     - ``kibisis,lute``
     - Wallets the app does not offer because they cannot return to it.


Service-account file
--------------------

Copy the JSON to the server by hand. No role copies key files, by design. Keep it outside
the repository and readable only by the web application's user:

.. code-block:: bash

    scp fcm-service-account.json <admin>@<server>:/tmp/
    # on the server
    sudo mkdir -p /var/www/asastats.com/keys
    sudo mv /tmp/fcm-service-account.json /var/www/asastats.com/keys/
    sudo chown -R <webapp user>:<webapp group> /var/www/asastats.com/keys
    sudo chmod 700 /var/www/asastats.com/keys
    sudo chmod 600 /var/www/asastats.com/keys/fcm-service-account.json

``<webapp user>`` is the ``WEBAPP_USER`` value in the same ``.env.production``. The path
is a suggestion; any path outside the repository works.

Without ``google-auth`` installed, the site still starts. Only sending to phones fails,
and the log says "native push failed".

Sign in with Apple key
----------------------

Copy the ``AuthKey_<KEY_ID>.p8`` to the server the same way, mode 600, owned by the web
application's user. Use the Sign in with Apple key, never the APNs key.

.. warning::

   If the file exists but the web application's user cannot read it, for example mode 600
   while still owned by root, Django fails at startup and the whole site goes down. The
   settings read it with no error handling. Check before every deploy:

   .. code-block:: bash

       sudo -u <webapp user> head -c 30 /var/www/asastats.com/keys/AuthKey_<KEY_ID>.p8

   It must print ``-----BEGIN PRIVATE KEY-----``. The FCM JSON is read only when sending,
   so a mistake there fails the phone notifications and nothing else.


Android fingerprints
--------------------

``ANDROID_CERT_SHA256`` takes one line, no spaces and no quotes:

.. code-block:: text

    ANDROID_CERT_SHA256=<app signing SHA-256>,<upload key SHA-256>

Copy both values from Play Console, Test and release, App integrity, App signing, in the
colon form (``AB:CD:...``). Case does not matter. These are public values: anyone can
read them from ``assetlinks.json``.

Until the setting is filled in, links to www.asastats.com open in the browser instead of
the app. Social sign-in on Android answers "unsupported". Nothing else breaks.

An Internal app sharing install is re-signed by Google with an internal test certificate.
Add that certificate's SHA-256 to the list too, or App Links and social sign-in fail on
that install and only on that install. You find it in Play Console under Internal app
sharing, Uploaders and testers. A debug build can never pass these checks, because its
package name is in no asset links document.

After a deploy, check the result:

.. code-block:: bash

    curl -s https://www.asastats.com/.well-known/assetlinks.json
    curl -s https://www.asastats.com/.well-known/apple-app-site-association

``assetlinks.json`` must list every fingerprint under ``com.asastats.app``. The Apple file
must carry ``DF2V3954Z7.com.asastats.app`` under both ``applinks`` and ``webcredentials``.
Also open ``/app/auth/return/`` in a browser; it shows "Return to the ASA Stats app".


Deploying
---------

From the frontend repository's ``deploy/`` folder:

.. code-block:: bash

    ansible-playbook site_playbook.yml --limit production --tags update-project-code

What it does:

* It clones GitHub ``main`` on the server, with submodules at the commits ``main``
  points to. It does not deploy your working tree, so push first.
* It rewrites the server ``.env`` from your local ``deploy/.env.production`` and
  ``environment.yml``.
* It installs ``requirements/production.txt``, runs ``migrate.sh`` and ``collectstatic``,
  and reloads the web server. Without the ``upgrade`` tag it upgrades no package.
* Keys whose code is not on the server yet are unused, so setting them early is harmless.
* ``FCM_*`` belongs together with the service-account file on the server.

Verify native push afterwards:

.. code-block:: bash

    python manage.py showmigrations widgets | grep nativepushdevice
    python -c "import google.auth; print('google-auth ok')"

Then send a test notification from the site's Django shell, with a real account's email:

.. code-block:: python

    from django.contrib.auth import get_user_model
    from widgets.inhouse.alerts.push import notify
    user = get_user_model().objects.get(email="you@example.com")
    print(notify(user, {"title": "ASA Stats", "body": "Test", "url": "/faq/"}))

It prints how many browsers and phones it reached. Tapping the notification must open
``/faq/``, with the app in the foreground, in the background and swiped away. After you
log out in the app, the same command must no longer count the phone.


Content security policy and firewall
------------------------------------

The nginx ``form-action`` directive must allow ``https://appleid.apple.com``. Nothing
else changes for the app: FCM is called by the server and not the page, and the host
firewall already allows outgoing traffic to ``fcm.googleapis.com`` and
``oauth2.googleapis.com``.
