#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from pytreex.core.block import Block
from pytreex.core.exception import LoadingException

__author__ = "Silvie Cinková"
__date__ = "2015"


class Polarity(Block):

    """
    Adds negative polarity to every negative clause (TR verb having gram/negation = neg1)
    """

    def __init__(self, scenario, args):
        "Constructor, just checking the argument values"
        Block.__init__(self, scenario, args)
        if self.language is None:
            raise LoadingException('Language must be defined!')

    def process_amrnode(self, amrnode):
        tnode = amrnode.src_tnode
        if tnode is None:
            return
        if not tnode.formeme.startswith('v:'):
            return
        if tnode.gram_negation == 'neg1':
            polaritynode = amrnode.create_child()
            polaritynode.modifier = 'polarity'
            polaritynode.concept = '-'
        eparents = tnode.get_eparents()
        aniz = False
        for eparent in eparents:
            if eparent.lemma == 'aniž' and tnode.is_right_child:
                aniz = True
        if aniz:
            polaritynode = tnode.create_child()
            polaritynode.concept = '-'
            polaritynode.modifier = 'polarity'
