#!/usr/bin/env python
# coding=utf-8
#
# Block for writing CoNLL-U files
# https://universaldependencies.github.io/docs/format.html

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import map
from builtins import str
from pytreex.block.write.basewriter import BaseWriter
from pytreex.core.util import file_stream

__author__ = "Martin Popel"
__date__ = "2015"


class WriteCoNLLU(BaseWriter):

    default_extension = '.conllu'

    def __init__(self, scenario, args):
        "Empty constructor (just call the base constructor)"
        BaseWriter.__init__(self, scenario, args)

    def process_document(self, doc):
        "Write a CoNLL-U file"
        out = file_stream(self.get_output_file_name(doc), 'w', encoding='UTF-8')
        for bundle in doc.bundles:
            zone = bundle.get_zone(self.language, self.selector)
            nodes = zone.atree.get_descendants(ordered=1)
            # Empty sentences are not allowed in CoNLL-U.
            if len(nodes)==0:
                continue
            comment = zone.wild['comment']
            if comment:
                out.write('#' + comment.rstrip('\r\n').replace('\n','\n#') + '\n')
            index = 1
            for node in nodes:
                out.write('\t'.join(
                    '_' if value is None else value for value in
                    map((lambda x: str(x) if type(x)==int else getattr(node, x, '_')),
                        [index, 'form', 'lemma', 'upos', 'xpos', 'feats', node.parent.ord, 'deprel', 'deps', 'misc'])
                ) + '\n')
                index += 1
            out.write('\n')
