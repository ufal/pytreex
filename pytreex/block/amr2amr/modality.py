#!/usr/bin/env python
from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

__author__ = "Silvie Cinková"
__date__ = "2015"                                                                                                         
                    
class Modality(Block):
    """
    This class treats modal predicates. Modal verbs are hidden in
    TR (encoded as gram/deontmod in the lexical verb), but not in AMR.
    #We create a parent node with the modal verb to govern the lexical verb.
    The modal labels are derived from the grammatemes like this:
    - deb: "muset-01"
    - hrt: "mít_povinnost-01"
    - vol: "chtít-01"
    - poss: "moci-01"
    - perm: "smět-01"
    - fac: "umět-01"
    """
    
    def __init__(self, scenario, args):                                               
        "Constructor, just checking the argument values"                              
        Block.__init__(self, scenario, args)                                          
        if self.language is None:                                                     
          raise LoadingException('Language must be defined!')                        
        self.lexicon = Lexicon()    

    def process_amrnode(self, amrnode):
        tnode = amrnode.src_tnode                                         
        if tnode is None: 
            return
        if tnode.gram_deontmod not in ('deb', 'hrt', 'vol', 'poss', 'perm', 'fac'):
            return
        else:
            #identify the parent of amrnode
            amr_original_parent = amrnode.parent
            #create a child node on the parent
            amr_new_parent = create.child(amr_original_parent)
            #this child node will be the modal node, so give it a label
            if tnode.gram_deontmod == 'deb':
                amr_new_parent.modifier == 'muset-01'
            if tnode.gram_deontmod == 'hrt':
                amr_new_parent.modifier == 'mít_povinnost-01'
            if tnode.gram_deontmod == 'vol':
                amr_new_parent.modifier == 'chtít-01'
            if tnode.gram_deontmod == 'poss':
                amr_new_parent.modifier == 'moci-01'
            if tnode.gram_deontmod == 'perm':
                amr_new_parent.modifier == 'smět-01'
            if tnode.gram_deontmod == 'fac':
                amr_new_parent.modifier == 'umět-01'
            #relocate amrnode as a child of this new modal node
            amrnode.parent = amr_new_parent    