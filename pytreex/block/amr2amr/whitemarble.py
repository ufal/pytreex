#!/usr/bin/env python

from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

__author__ = "Silvie Cinková"
__date__ = "2015"                                                                                                         
                    
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
        self.lexicon = Lexicon()    

    def process_amrnode(self, amrnode):
        tnode = amrnode.src_tnode                                         
        if tnode is None: 
           return
        if not tnode.formeme.startswith('n:'):
            return
        else: 
            tchildren = tnode.get_children()
            #detect all descendantst of amrnode, not just children
            #because the relevant amrchildren could have been already
            #relocated by other rules, but unlikely somewhere upwards
            amrdescendants = amrnode.get_descendants()
            #detect all RSTR functored tchildren of tnode
            rstrtnodes = []
            #gather ids of all tchildren functored RSTR
            rstrids = []
            #prepare a list of amrnodes to be labeled 'mod'    
            amrmodchildren = []
            for tchild in tchildren:
                if (tchild.functor == 'RSTR' and
                    tchild.formeme.startswith('adj'):
                    rstrnodes = rstrnodes.extend(tchild)
                    for rstrnode in rstrnodes:
                        rstrids = rstrids.extend(rstrnode.id)
                    for amrmodchild in amrmodchildren:
                        if amrmodchild.id in rstrids:
                            amrmodchild.modifier = 'mod'
                            #just in case amrmodchild happens not
                            #to be a child of amrnode, make it one
                            amrmodchild.parent = amrnode                          
                    
      
                
                
                
        