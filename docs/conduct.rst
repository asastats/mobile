Working agreements
==================

These rules apply to everyone who changes this repository, people and AI assistants
alike.

The logbook rule
----------------

Comments and docstrings stay short. Before writing one longer than about three lines,
write it in ``docs/logbook.md`` and leave the code with the shortest note that stops
the next reader from breaking something.

The test for what stays in the code is whether somebody editing that line would get it
wrong without the comment.

Stays in the code
    A contract the reader cannot see: an id a fragment swaps on, a class a script binds
    to, an attribute that must be quoted, an ordering another tool depends on, a name a
    test asserts.

Goes to the logbook
    Why it was built, what it replaced, the incident that prompted it, the alternative
    that was rejected, the measurement behind a number.

This applies to workflows, Gradle files and ``capacitor.config.ts`` as much as to
Python. A workflow step gets one line and a pointer.

A logbook entry is filed under the path of the file it explains and dated where the
date is known. The logbook is append-only. When a note turns out to be wrong, add a
correction beneath it. "We believed X until this date" is the useful part, so do not
edit the original.



Tests come with the change
--------------------------

* Every line of our own code is covered by a unit test. CI fails under 100 %.
* Every visible feature gets a functional test on a device or emulator.
* Where a feature calls the website, add an integration test as well.
* What cannot be automated goes into :doc:`beta_checklist` instead of being left out.

Details and commands are in :doc:`testing`.


Secrets
-------

* No key, keystore, certificate, service-account file or ``.p8`` goes into any
  repository, including a private one. The ignore rules cover ``*.jks``, ``*.keystore``,
  ``*.p8``, ``*.p12``, ``*.mobileprovision``, ``google-services.json`` and
  ``GoogleService-Info.plist``. Do not weaken them.
* CI receives secrets as base64 repository secrets. Set them with ``gh secret set NAME``
  without a value on the command line, so the value stays out of shell history.
* Keep the originals in a store outside the repository that you back up. A lost Android
  upload key costs days (see :doc:`signing`).
* Docs and issues name placeholders such as ``<KEY_ID>``, never real key ids or file
  names of credentials. Identifiers that are public anyway (bundle ids, the Team ID, the
  Firebase project ID) and the names of accounts these docs tell you to create may appear.


Commits and review
------------------

* Write code that reads like the code around it: docstring style, naming, comment
  density.
* Run each repository's test suite on its own. Two runs that share a test database
  collide, and the failure looks like a regression.
* Stage only your own files. A working tree often holds somebody else's unfinished
  edits.
* Ask for a second opinion before changing the architecture, any sign-in, session or
  ticket code, anything that exposes a new native call to web pages, or a store-policy
  decision.


Store rules the code has to respect
-----------------------------------

App Review checks these points.

* Nothing in the app sells, prices or links to a purchase. Places that need a plan say
  "Not included in your current plan." and carry no link. The listing relies on Apple
  guideline 3.1.3(f), a free companion to a paid web service.
* The app never asks for, sees or stores a private key or recovery phrase. It is not a
  wallet, and the review notes say so.
* Templates that hide something in the app must fail open. A hiding check evaluated
  without a request must show the content, so use the ``widget_shown`` filter on the
  request and never a raw membership test on a context variable. Django's ``{% if %}``
  turns an error into false.
* The privacy policy at ``/asm-privacy/`` and the store privacy answers describe the
  same data. Change one and you change the other (:doc:`store_listing`).


Physical devices
----------------

Never toggle Wi-Fi, mobile data or airplane mode on a test phone over adb; the reason is
in :doc:`devices`.
