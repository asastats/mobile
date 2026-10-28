Debugging on a device
=====================

Setting up adb
--------------

On a Raspberry Pi or any ARM64 Debian machine, install Debian's package. Google's zip
is built for x86.

.. code-block:: bash

    sudo apt install adb

On the phone (MIUI wording; other makers differ a little):

#. Settings, About phone, tap the MIUI version seven times to turn Developer options on.
#. Settings, Additional settings, Developer options: switch on USB debugging, "USB
   debugging (Security settings)" and Install via USB. MIUI needs the security option
   for taps and settings changes over adb, and it asks for a Mi account and a SIM.
#. Unplug and replug the cable. Accept "Allow USB debugging?" and tick "Always allow from
   this computer".

Check:

.. code-block:: bash

    adb devices -l

The phone must appear as ``device``, not ``unauthorized``.

Which build to debug
--------------------

Debug builds are ``com.asastats.app.debug``, named "ASA Stats dev", so they install
next to the store app. WebView debugging is on only in the debug build.

CI signs every debug APK with one kept key, so a new APK installs over the last one and
needs no ``adb uninstall``. Without the ``ANDROID_DEBUG_KEYSTORE_BASE64`` secret each
APK gets a fresh key and has to be uninstalled first.

A debug build cannot finish a social sign-in. Its package name is in no asset links
document, so the operating system refuses the callback. Use a Play internal testing build
or TestFlight for that (:doc:`releasing`).

Inspecting the WebView
----------------------

The tools below speak the Chrome DevTools protocol to the debug app. They live in the
maintainer's workspace, outside this repository, and the list says what each does.
They need a Python with ``websocket-client``, which Appium's client
installs.

* Evaluate JavaScript in the app's page and print the result.
* Log WebSockets, console messages, exceptions, navigations and live-refresh polls with
  timestamps, and inject a probe that records socket messages as the page sees them,
  wallet store writes with stack traces, visibility changes and card redraws.
* Take a heap snapshot and call a function on a live object. Minified class names change
  with each bundle build, so look the name up again after every rebuild.
* Serve a local ``bundle.js`` to the WebView instead of the site's, to try a frontend fix
  before deploying it.
* Print the SHA-256 of an APK's v2 or v3 signer, which ``keytool`` cannot read.

Cautions
--------

* Never toggle Wi-Fi, mobile data or airplane mode over adb on a phone that supplies
  your workstation's connection.
* Stop a helper script by its PID. ``pkill -f`` matches the shell that runs it.
* Create virtual environments inside the project, not in a shared location.
