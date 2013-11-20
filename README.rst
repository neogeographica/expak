expak: Extract and process resources from Quake-style pak files
===============================================================

.. image:: https://api.travis-ci.org/neogeographica/expak.png?branch=master
    :target: http://travis-ci.org/neogeographica/expak
    :alt: build status of the master branch

*expak* is a GPLv3_-licensed tool to extract and optionally process resources
from one or more `Quake-style pak files`_.

The main component delivered by expak installation is a pure Python module,
for programmatically working with pak files. The installation also creates a
command-line utility for simple resource-extraction operations.

Currently expak is compatible with Python 2.6 and 2.7. It has no dependencies
outside of the standard Python modules.

.. _GPLv3: http://www.gnu.org/copyleft/gpl.html
.. _Quake-style pak files: http://quakewiki.org/wiki/.pak


Installation
============

The latest version of expak can always be installed or updated to via the `pip`_
package manager, and this is the preferred method:

.. code-block:: none

    pip install expak

The easy_install utility can also install expak:

.. code-block:: none

    easy_install expak

And if you are on Windows, you could also choose to use an installer program,
available among the `downloads for expak`_ at the Python Package Index (PyPI)
(look for downloads of the type "MS Windows installer").

.. _pip: http://www.pip-installer.org/en/latest
.. _downloads for expak: https://pypi.python.org/pypi/expak#downloads

Documentation
=============

- `expak module`_
- `simple expak utility`_

.. _expak module: http://expak.readthedocs.org/en/latest/expak.html
.. _simple expak utility: http://expak.readthedocs.org/en/latest/simple_expak.html


