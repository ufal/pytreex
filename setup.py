#!/usr/bin/env python
# -"- coding: utf-8 -"-

from distutils.core import setup
import codecs

setup(
    name='PyTreex',
    version='0.1dev',
    author='Ondrej Dusek',
    packages=['pytreex'],
    scripts=['bin/pytreex'],
    url='https://github.com/ufal/pytreex',
    license='LICENSE.txt',
    description='A minimal Python implementation of the Treex API',
    long_description=codecs.open('README.md', 'rb', 'UTF-8').read(),
    install_requires=[
        "PyYAML",
        "Unidecode",
    ],
)
