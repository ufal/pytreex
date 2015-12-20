#!/usr/bin/env python
# coding=utf-8
#
# Block for reading CoNLL-U files
#
from __future__ import absolute_import
from __future__ import unicode_literals

from pytreex.core.block import Block
from pytreex.core import Document

from pytreex.core.exception import LoadingException
from pytreex.core.util import file_stream
import re
from pytreex.core.log import log_info

__author__ = "Martin Popel"
__date__ = "2015"


class ReadCoNLLU(Block):
    """\
    Reader for CoNLL-U format used in Universal Dependencies
    https://universaldependencies.github.io/docs/format.html
    """

    def __init__(self, scenario, args):
        """\
        Constructor, checks if language is set and selects encoding according
        to args, defauts to UTF-8.
        """
        Block.__init__(self, scenario, args)
        if self.language is None:
            self.language = 'unk'
        self.encoding = args.get('encoding', 'UTF-8')

    def process_document(self, filename):
        """\
        Read a CoNLL-U file and return its contents as a Document object.
        """
        fh = file_stream(filename, encoding=self.encoding)
        doc = Document(filename)
        bundle = doc.create_bundle()
        zone = bundle.create_zone(self.language, self.selector)
        root = zone.create_atree()
        last_node = root
        nodes = [root]
        parents = [0]
        
        for line in fh:
            
            # Strip newline character
            line = line.rstrip('\n')
            
            # Skip empty lines and comments before start of sentence
            if len(nodes)==1 and (not line or line.startswith('#')): continue
            
            # Empty line as a end of sentence
            if not line:
                for i in xrange(1,len(nodes)):
                    nodes[i].parent = nodes[parents[i]]
                bundle = doc.create_bundle()
                zone = bundle.create_zone(self.language, self.selector)
                root = zone.create_atree()
                last_node = root
                nodes = [root]
                parents = [0]
                continue
            
            columns = line.split('\t')
            
            # TODO: multi-word tokens
            if columns[0].find('-') >= 0: continue
            
            # Create new node
            new_node = root.create_child(data = dict(zip(
                ['form', 'lemma', 'upos', 'xpos', 'feats',    'deprel', 'deps', 'misc'],
                columns[1:6]                                 + columns[7:10]  ) ) )
            nodes.append(new_node)
            parents.append(int(columns[6]))

            # Word order TODO is this needed?
            new_node.shift_after_subtree(last_node)
            last_node = new_node

        # The last bundle should be empty (if the file ended with an empty line),
        # so we need to remove it. But let's check it.
        if len(nodes)==1:
            doc.bundles.pop()
        else:
            for i in xrange(1,len(nodes)):
                nodes[i].parent = nodes[parents[i]]
        fh.close()
        return doc
