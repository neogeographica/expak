.. _header_section:

expak: Extract and process resources from Quake-style pak files
===============================================================

.. image:: https://badge.fury.io/py/expak.png
    :target: http://badge.fury.io/py/expak
    :alt: current version

.. image:: https://api.travis-ci.org/neogeographica/expak.png?branch=master
    :target: http://travis-ci.org/neogeographica/expak
    :alt: build status of the master branch

.. _blurb_section:

*expak* is a GPLv3_-licensed tool to extract and optionally process resources
from one or more `Quake-style pak files`_.

The main component delivered by expak installation is a pure Python module,
for programmatically working with pak files. The installation also creates a
command-line utility for simple resource-extraction operations.

Currently expak is compatible with Python 2.6, 2.7, 3.2, and 3.3. It has no
dependencies outside of the standard Python modules.

.. _GPLv3: http://www.gnu.org/copyleft/gpl.html
.. _Quake-style pak files: http://quakewiki.org/wiki/.pak


.. _prerequisites_section:

Prerequisites
-------------

It's a Python module and utility, so you need Python! If you don't have Python
installed, `go get it`_. The latest stable version of either Python 2 or Python 3
will work... if you're new to Python, you should look elsewhere for advice on
whether to use 2 or 3, but the general consideration is that currently more
stuff is compatible with Python 2.

You'll probably also want a Python package manager to help install expak (and
other things). If you're going to be running on Windows, you can skip this
part by downloading a custom expak installer as described below ... although
even on Windows, it can be convenient to have a Python package manager, so you
may want to take care of this anyway.

The `pip`_ package manager is a fine choice for anyone running Python 2.6 or
later. If you don't currently have pip then you can run through the
`instructions for installing pip`_ and be good to go; it can do many things,
but you can ignore all of its complexity for the purposes of installing expak.

.. _go get it: http://python.org/download/
.. _pip: http://www.pip-installer.org/en/latest
.. _instructions for installing pip: http://www.pip-installer.org/en/latest/installing.html

.. _installation_section:

Installation
------------

The latest version of expak can always be installed or updated to via the `pip`_
package manager, and this is the preferred method:

.. code-block:: none

    pip install expak

The easy_install utility can also install expak, if you have setuptools
installed but can't or don't want to use pip:

.. code-block:: none

    easy_install expak

Finally, if you are on Windows, you could also choose to use an installer
program, although the methods above work fine on Windows. Custom expak
installers are included in the downloads list for expak
`at the Python Package Index`_ (PyPI).

If PyPI and its mirrors are down, the Windows installers and other forms of
distribution files (including source distribution) are mirrored
`in the releases for the GitHub repo`_.

.. _at the Python Package Index: https://pypi.python.org/pypi/expak
.. _in the releases for the GitHub repo: https://github.com/neogeographica/expak/releases

.. _documentation_section:

Documentation
-------------

- `expak module`_
- `simple expak utility`_

.. _expak module: http://expak.readthedocs.org/en/latest/expak.html
.. _simple expak utility: http://expak.readthedocs.org/en/latest/simple_expak.html


