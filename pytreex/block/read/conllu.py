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
        comment = ''
        
        for line in fh:
            
            # Strip newline character (\n or \r\n)
            line = line.rstrip('\r\n')

            # Empty line as a end of sentence
            if not line:
                # Ignore (multiple) empty lines before start of sentence (invalid CoNLL-U)
                if len(nodes)==1:
                    continue

                # Rehang to correct parents and save nonempty comment to root
                for i in xrange(1,len(nodes)):
                    nodes[i].parent = nodes[parents[i]]
                if len(comment):
                    root.set_attr('wild/comment', comment)

                # Prepare a new bundle
                bundle = doc.create_bundle()
                zone = bundle.create_zone(self.language, self.selector)
                root = zone.create_atree()
                last_node = root
                nodes = [root]
                parents = [0]
                comment = ''
            
            # Comment
            elif line[0] == '#':
                comment = comment + line[1:] + "\n"

            # A normal line with one token
            else:
                columns = line.split('\t')
            
                # TODO: multi-word tokens
                if '-' in columns[0]: continue
            
                # Create new node
                new_node = root.create_child(data = dict(
                    (key, value) for key, value in
                    zip(['form', 'lemma', 'upos', 'xpos', 'feats',    'deprel', 'deps', 'misc'],
                        columns[1:6]                                 + columns[7:10]  )
                    if value is not None and value != '_'
                    ) )
                nodes.append(new_node)
                try:
                    parent_index = int(columns[6])
                except (ValueError, TypeError):
                    # TODO: warning?
                    parent_index = 0
                parents.append(parent_index)

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
            if len(comment):
                root.set_attr('wild/comment', comment)

        fh.close()
        return doc
