ASA Stats mobile documentation
==============================

The iOS and Android app "ASA Stats" (``com.asastats.app``) is a Capacitor 8 shell
around https://www.asastats.com. It adds native features the website cannot have
in a browser: push notifications, system-browser sign-in, links that open in the
app, native sharing and an offline screen.

These pages cover running the app, keeping it releasable and answering the store
reviews. Why a given line of code or configuration looks the way it does is in
``docs/logbook.md`` in the repository.

.. toctree::
   :maxdepth: 2
   :caption: Working on the app

   development
   conduct
   testing
   devices

.. toctree::
   :maxdepth: 2
   :caption: Shipping it

   signing
   firebase
   server_settings
   releasing
   beta_checklist
   store_listing

.. toctree::
   :maxdepth: 2
   :caption: Reference

   webauth
   howto
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
