#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

here = os.path.abspath(os.path.dirname(__file__))

#DIRECTIVE_PATTERN = re.compile("^\.\. .+?^$.+?^$", re.MULTILINE | re.DOTALL)
INCLUDE_PATTERN = re.compile("^\.\. include:: (.+?)$", re.MULTILINE | re.DOTALL)

def read(inpath):
    with open(inpath, 'r') as instream:
        return instream.read()

def ospath(rstpath):
    parts = rstpath.split("/")
    return os.path.join(here, *parts)

template_path = os.path.join(here, "README.rst.in")
readme_path = os.path.join(here, "README.rst")

template = read(template_path)

readme = INCLUDE_PATTERN.sub(lambda m: read(ospath(m.group(1))), template)

with open(readme_path, 'w') as outstream:
    outstream.write(readme)
