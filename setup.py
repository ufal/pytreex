#!/usr/bin/env python
# -"- coding: utf-8 -"-

from distutils.core import setup
import codecs

setup(
    name='PyTreex',
    author='Ondrej Dusek',
    packages=['pytreex', 'pytreex.core', 'pytreex.tool', 'pytreex.tool.ml',
              'pytreex.tool.lexicon', 'pytreex.block', 'pytreex.block.t2a',
              'pytreex.block.t2a.cs', 'pytreex.block.a2w', 'pytreex.block.a2w.cs',
              'pytreex.block.util', 'pytreex.block.write', 'pytreex.block.read',
              'pytreex.block.t2t'],
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
