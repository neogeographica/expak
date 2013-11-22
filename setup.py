from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import codecs
import os
import sys
import re

ANCHOR_PATTERN = re.compile('^\.\. _([^:]+):$')

# Work around 2.6 error when exiting tests:
try:
    import multiprocessing
except ImportError:
    pass

# Force bdist_wininst to use the correct bundled installer, even when building
# on non-Windows platforms.
import distutils.msvccompiler
def correct_build_version():
    return 9.0
distutils.msvccompiler.get_build_version = correct_build_version

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

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--strict', '--verbose', '--tb=long']
        # disabling coverage in "setup.py test" for now (& see below)
#                          '--cov', 'expak',
#                          '--cov-report=html', '--cov-report=term']
        self.test_suite = True
    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

# Set a default description just in case we don't find it in the readme.
description = 'Extract and process resources from Quake-style pak files'

# Pick the desired sections out of the readme for use in the long description,
# and also look for the short description in the readme header.
readme_orig = read('README.rst')
readme_sections = set(['blurb_section', 'documentation_section'])
readme = ''
section = None
include_line = False
for readme_line in readme_orig.splitlines(True):
    is_anchor = ANCHOR_PATTERN.match(readme_line)
    if is_anchor:
        section = is_anchor.group(1)
        include_line = False
        continue
    if section == 'header_section':
        if readme_line.startswith('expak:'):
            description = readme_line[6:].strip()
    if include_line:
        readme = readme + readme_line
    elif section in readme_sections:
        include_line = True

# Form long description from select readme sections + history/changelog.
long_description = readme + read('HISTORY.rst')

setup(
    py_modules = ['expak'],
    name = 'expak',
    version = find_version('expak.py'),
    author = 'Joel Baxter',
    author_email = 'joel.baxter@neogeographica.com',
    url = 'http://github.com/neogeographica/expak',
    description = description,
    long_description = long_description,
    classifiers = [
#        'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    platforms = 'any',
    license = 'GPLv3',
    zip_safe = True,
    install_requires = [],
    entry_points={'console_scripts': ['simple_expak = expak:simple_expak']},
    test_suite = 'test.test_expak',
    # disabling coverage in "setup.py test" for now (& see above)
#    tests_require = ['pytest-cov', 'pytest'],
    tests_require = ['pytest'],
    cmdclass = {'test': PyTest}
)
