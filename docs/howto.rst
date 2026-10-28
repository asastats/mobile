Howto
=====

Build these docs
----------------

Install the documentation requirements into an environment and run Sphinx:

.. code-block:: bash

    python3 -m venv venv
    venv/bin/python -m pip install -r requirements-docs.txt
    cd docs
    ../venv/bin/python -m sphinx -W -b html . _build/html

Output lands in ``docs/_build/html``. ``-W`` turns warnings into errors, as the Read the
Docs build does (``fail_on_warning`` in ``.readthedocs.yml``). A warning that appears only
there points at a library or setting that the docs environment lacks. Add the
library to ``autodoc_mock_imports`` in ``docs/conf.py``, or rebuild in a clean
environment to reproduce it.

Read the Docs builds and hosts the documentation automatically from the repository.


Add a page
----------

Write ``reStructuredText`` in ``docs/`` and add the file to a ``toctree`` in
``index.rst``. An unlisted page is not an error, only a missing page, so check the
sidebar after you build.

Add a module to the API pages
-----------------------------

Python modules go into ``api.rst`` as an ``automodule`` block. ``scripts/make-icons.py``
and ``make-notification-icon.py`` have hyphens in their names, so ``conf.py`` loads them
under the underscore names ``make_icons`` and ``make_notification_icon``. Follow that
pattern for any new hyphenated script.

Docstrings use the Sphinx field style (``:param name:``, ``:return:``), which Napoleon
also reads.
