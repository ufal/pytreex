#!/usr/bin/env python3
from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

__author__ = "Silvie Cinková"
__date__ = "2015"                                                                                                         
                    
class RelativeClause(Block):
    """
    This class creates the AMR structure for relative clauses modifying a noun.
    (b/boy
        ARG0-of (b2/believe))
    "Boy who believes"
    First we make sure that the starting AMR structure corresponds to
    the t-structure we describe. Then we label the relclause head with ARGn-of
    according to the rule of thumb (ARG0 = ACT, etc.) and remove the amr node
    corresponding to the relative pronoun, if there is any.
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
        techildren = tnode.get_echildren()
        #list amr nodes with source tnodes functored RSTR(incl. coordinated)
        #and with formeme 'v'
        amrrelclauseheads = [] #amr counterparts of t-verbs functored RSTR
        tcorefnodes = [] #nodes with gramcoref reference
        amrnodedescendants = amrnode.get_descendants() #will need them later
        tfordeletions = [] #tnode ids of relative pronouns - we list them
        #and then we delete all their corresponding amrnodes.
        #search among techildren of tnode
        for techild in techildren:
           amrpreselecteditems = determine_functored_head(techild, functor = 'RSTR')
           #We have all RSTR's but have to pick verbs only:
           for amrpreselecteditem in amrpreselecteditems:
            if amrpreselecteditem.src_tnode.formeme.startswith('v'):
                #only verbs are listed as relclause heads
                amrrelclauseheads = amrrelclauseheads.extend(
                                        amrpreselecteditem)
        
        for amrrelclausehead in amrrelclauseheads:
            #check that amrrelclausehead has amrnode as parent
            #if not, check that amrrelclausehead has a conjunction as parent
            #if not even that, return
            if not amrrelclausehead.parent.src_tnode.id == tnode.id:
                if not (amrrelclausehead.parent.src_tnode.nodetype == 'coap'):
                    return
                else: #i.e. if amrrelclausehead has a conjunction as parent
                    #check whether this conjunction has amrnode as amrchild
                    #We assume that it has not and would exit the function#
                    #by default
                    amrcandidates = amrrelclausehead.parent.get_children()
                    nocandidates == True
                    for amrcandidate in amrcandidates:
                        if amrcandidate.src_tnode.id == tnode.id:
                            nocandidates == False
                    if nocandidates == True:
                        return
            #If we haven't exited the function by now,
            #we should be pretty confident that the starting amr structure
            #corresponds to the t-structure we are going to describe. 
            #At this point, we can start the amr tree transformation.
            #Search t-tree only to make it easy
            tverbrel = amrrelclausehead.src_tnode #this is the verb in ttree
            trelargs = tverbrel.get_echildren()
            #in these find args with grammatical coref. - ttree
            #identify the relative pronoun among arguments of relclause head verb(s)
            for trelarg in trelargs:
                #don't know whether it's length of a list or a string, please check
                #but if this attribute is empty, it should be 0 in either case...
                if len(trelarg.coref_gram_nodes()) != 0:
                    if trelarg.functor == 'ACT':
                        amrrelclausehead.modifier = 'ARG0-of'
                    if trelarg.functor == 'PAT':
                        amrrelclausehead.modifier = 'ARG1-of'
                    if trelarg.functor == 'ADDR':
                        amrrelclausehead.modifier = 'ARG2-of'
                    if trelarg.functor == 'ORIG':
                        amrrelclausehead.modifier = 'ARG3-of'    
                    if trelarg.functor == 'EFF':
                        amrrelclausehead.modifier = 'ARG4-of'
                    if trelarg.functor == 'DIR1':
                        amrrelclausehead.modifier = 'source-of'
                    if trelarg.functor == ('DIR2'):
                        amrrelclausehead.modifier = 'path-of'
                    if trelarg.functor == 'DIR3':
                        amrrelclausehead.modifier = 'direction-of'
                    if trelarg.functor == 'ACMP':
                        amrrelclausehead.modifier = 'accompanier-of'
                    if trelarg.functor in ('THL', 'TFHL'):
                        amrrelclausehead.modifier = 'duration-of'
                    if trelarg.functor == 'MANN':
                        amrrelclausehead.modifier = 'manner-of'
                    if trelarg.functor == 'AIM':
                        amrrelclausehead.modifier = 'purpose-of'
                    if trelarg.functor == 'CAUS':
                        amrrelclausehead.modifier = 'cause-of'
                    if trelarg.functor == 'CNCS':
                        amrrelclausehead.modifier = 'concession-of'    
                    if trelarg.functor == 'COND':
                        amrrelclausehead.modifier = 'condition-of'
                    if trelarg.functor == 'THO':
                        amrrelclausehead.modifier = 'frequency-of'     
                        
                    #remove the amr-node corresponding to the relpronoun
                    tfordeletions = tfordeletions.extend(trelarg.id)
                    for amrnodedescendant in amrnodedescendants:
                        if amrnodedescendant.src_tnode in tfordeletions:
                            if len(amrnodedescendant.get_children) > 0:
                                continue #this case would be something odd
                            else: amrnodedescendant.remove()
                                
                        
                    
                
                    
                    
                    
                    
                
                    
        
       

