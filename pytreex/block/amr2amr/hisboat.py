#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from pytreex.core.block import Block
from pytreex.core.exception import LoadingException


__author__ = "Silvie Cinková"
__date__ = "2015"


# OD's note: same as WhiteMarble: why not just check for the APP functor and the tag match,
# why look for descendants of nouns? IMHO it would be the same in 99.9% cases...


class HisBoat(Block):

    """
    This class creates this AMR structure:
    (b / boat
        :poss (h / he))
    from "his boat". We ignore the case "boat that is his".
    Also, this time we ignore adjectival attributes in coordinations and
    #look only for attributes as direct children of the governing noun,
    #since coordinated attributes are already covered by
    #the Coordination class!
    #We capture cases like "babiččin hrnek", "její lékař", "svoje pochyby",
    but we ignore genitive cases as "život Rudyarda Kiplinga", since the APP
    functor has a broader scope here than AMR's "poss" modifier.
    This class is written based on WhiteMarble, so make possible
    updates in both places.
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
        if not tnode.formeme.startswith('n:'):
            return
        else:
            # is really OK, ignore attr in coord
            tchildren = tnode.get_children()
            # detect all descendants of amrnode, not just children
            # because the relevant amrchildren could have been already
            # relocated by other rules, but unlikely somewhere upwards
            amrdescendants = amrnode.get_descendants()
            # detect all APP functored tchildren of tnode
            tappnodes = set()
            for tchild in tchildren:
                if (tchild.functor == 'APP' and
                    tchild.lex_anode and
                    (tchild.lex_anode.tag.match('.....[MFXZ]') or  # if match
                     # really takes the first match from the beginning of string
                     # this is the regex pattern that worked in PMLTQ:
                     # "(^.[SU8]|^.....[MFXZ])" --the line start was necessary!
                     tchild.lex_anode.tag.match('.[[SU8]]'))):
                    # ok write tchild.lex_anode.tag.match('.....[MFXZ]|.[SU8]')?
                    tappnodes = tappnodes.add(tchild)  # have all APP nodes in one list

            for amrdescendant in amrdescendants:  # find amrnode
                # descendants with the same id as their corresponding t-nodes
                if amrdescendant.src_tnode in tappnodes:
                    amrdescendant.modifier = 'poss'
                    # make sure that this amrmoddescendant is
                    # amrmod's child:
                    amrdescendant.parent = amrnode
