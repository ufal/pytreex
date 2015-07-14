#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from pytreex.core.block import Block
from pytreex.core.exception import LoadingException

__author__ = "Silvie Cinková"
__date__ = "2015"


# OD's note: this seems really complicated -- why not just relabel all RSTRs to mod ??
# I think that it would work the same in 99.9% cases


class WhiteMarble(Block):

    """
    This class creates this AMR structure:
    (m / marble
        :mod (w / white))
    from "white marble". We ignore the case "marble that is white".
    Also, this time we ignore adjectival attributes in coordinations and
    #look only for attributes as direct children of the governing noun,
    #since coordinated attributes are already covered by
    #the Coordination class!
    #This class served as the base for the HisBoat class, so if one
    #gets an update/correction, the other ought to as well.
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
            # detect all RSTR functored tchildren of tnode
            rstr_tnodes = set()
            for tchild in tchildren:
                if (tchild.functor == 'RSTR' and
                        tchild.formeme.startswith('adj')):
                    # have all RSTR nodes
                    rstr_tnodes.add(tchild)

            for amrdescendant in amrdescendants:  # find amrnode
                # descendants with the same id as their corresponding t-nodes
                if amrdescendant.src_tnode in rstr_tnodes:
                    amrdescendant.modifier = 'mod'
                    # make sure that this amrmoddescendant is
                    # amrmod's child:
                    amrdescendant.parent = amrnode
