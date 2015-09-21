#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from pytreex.core.block import Block
from pytreex.core.exception import LoadingException
from pytreex.core.log import log_info
import re

__author__ = "Ondřej Dušek"
__date__ = "2015"


class NormalizeNumbers(Block):

    """
    """

    def __init__(self, scenario, args):
        "Constructor, just checking the argument values"
        Block.__init__(self, scenario, args)
        if self.language is None:
            raise LoadingException('Language must be defined!')

    def process_amrtree(self, amrtree):
        for child in amrtree.get_children():
            self.process_subtree(child)

    def process_subtree(self, amrnode):
        # progress depth-first
        for child in amrnode.get_children():
            self.process_subtree(child)
        # #Separ is "+"
        if amrnode.concept == '#Separ':
            val = 0
            for child in amrnode.get_children():
                num = self.get_numeric_value(child)
                if num is None:
                    continue
                val += num
                self.rehang_children_and_remove(child)
            amrnode.concept = unicode(val)
            log_info('Separ: ' + amrnode.concept)
            return
        # / is "/"
        if amrnode.concept in ['/', '#Slash']:
            children = amrnode.get_children(ordered=True)
            if len(children) == 2 and all([self.get_numeric_value(c) is not None for c in children]):
                val = self.get_numeric_value(children[0]) / float(self.get_numeric_value(children[1]))
                amrnode.concept = unicode(val)
                log_info('/: ' + amrnode.concept)
                self.rehang_children_and_remove(children[0])
                self.rehang_children_and_remove(children[1])
            return
        # check if we are a number, normalize our concept name
        val = self.get_numeric_value(amrnode)
        if val is not None:
            # any numeric children = '*'
            for child in amrnode.get_children(preceding_only=True):
                num = self.get_numeric_value(child)
                if num is not None:
                    val *= num
                    self.rehang_children_and_remove(child)
                    log_info('Number child: ' + str(num))
            log_info('Number: ' + amrnode.concept)
            amrnode.concept = unicode(val)
    
    def get_numeric_value(self, amrnode):
        try:
            val = float(amrnode.concept)
            return val
        except TypeError:
            return None  # for None
        except ValueError:
            val = self.NUM_FOR_WORD.get(amrnode.concept)
            if val is not None:
                return val
            m = re.match(r'^(jedn|dva|tři|čtyři|pět|šest|sedm|osm|devět)' +
                         r'a((?:dva|tři|čtyři)cet|(?:pa|še|sedm|osm|deva)desát)$', amrnode.concept)
            if m:
                ones, tens = m.groups()
                return self.NUM_FOR_WORD[ones] + self.NUM_FOR_WORD[tens]
            return None

    def rehang_children_and_remove(self, amrnode):
        parent = amrnode.parent
        for child in amrnode.get_children():
            child.parent = parent
        amrnode.remove()


    NUM_FOR_WORD = {
        'nula': 0, 'jedna': 1, 'jeden': 1, 'dva': 2, 'tři': 3, 'čtyři': 4, 'pět': 5,
        'šest': 6, 'sedm': 7, 'osm': 8, 'devět': 9, 'deset': 10,
        'jedenáct': 11, 'dvanáct': 12, 'třináct': 13, 'čtrnáct': 14, 'patnáct': 15,
        'šestnáct': 16, 'sedmnáct': 17, 'osmnáct': 18, 'devatenáct': 19,
        'dvacet': 20, 'třicet': 30, 'čtyřicet': 40, 'padesát': 50,
        'šedesát': 60, 'sedmdesát': 70, 'osmdesát': 80, 'devadesát': 90,
        'sto': 100, 'tisíc': 1000, 'milión': 1000000, 'milion': 1000000, 'miliarda': 1000000000,

        # fractions
        'půl': 1/2, 'polovina': 1/2, 'třetina': 1/3, 'čtvrt': 1/4, 'čtvrtina': 1/4,
        'pětina': 1/5, 'šestina': 1/6, 'sedmina': 1/7, 'osmina': 1/8, 'devítina': 1/9,
        'desetina': 1/10, 'jedenáctina': 1/11, 'dvanáctina': 1/12, 'třináctina': 1/13,
        'čtrnáctina': 1/14, 'patnáctina': 1/15, 'šestnáctina': 1/16, 'sedmnáctina': 1/17,
        'osmnáctina': 1/18, 'devatenáctina': 1/19, 'dvacetina': 1/20,
        'třicetina': 1/30, 'čtyřicetina': 1/40, 'padesátina': 1/50, 'šedesátina': 1/60,
        'sedmdesátina': 1/70, 'osmdesátina': 1/80, 'devadesátina': 1/90,
        'setina': 1/100, 'tisícina': 1/1000, 'milióntina': 1/1000000, 'miliontina': 1/1000000,

        # other
        'tucet': 12, 'kopa': 60, 'veletucet': 144,
    }
