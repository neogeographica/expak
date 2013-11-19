from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import codecs
import os
import sys
import re

# Work around 2.6 error when exiting tests:
try:
    import multiprocessing
except ImportError:
    pass

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read('README.rst') + '\n\n' + read('HISTORY.rst')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--strict', '--verbose', '--tb=long',
                          '--cov', 'expak',
                          '--cov-report=html', '--cov-report=term']
        self.test_suite = True
    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    py_modules = ['expak'],
    name = 'expak',
    version = find_version('expak.py'),
    author = 'Joel Baxter',
    author_email = 'joel.baxter@neogeographica.com',
    url = 'http://github.com/neogeographica/expak',
    description = 'Extract and process resources from Quake-style pak files',
    long_description = long_description,
    classifiers = [
        'Development Status :: 4 - Beta',
#        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    platforms = 'any',
    license = 'GPLv3',
    zip_safe = True,
    install_requires = [],
    entry_points={'console_scripts': ['simple_expak = expak:simple_expak']},
    test_suite = 'test.test_expak',
    tests_require = ['pytest-cov', 'pytest'],
    cmdclass = {'test': PyTest}
)
