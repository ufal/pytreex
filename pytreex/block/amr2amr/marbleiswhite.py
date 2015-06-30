from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

import logging

__author__ = "Silvie Cinková"
__date__ = "2015"  


class MarbleIsWhite(Block):
     """
     Create the following AMR structure from copula predicates (ignoring the 
     #"the whiteness of the marble" case)
     (w / white
     :domain (m / marble))
     The marble is white.
     the whiteness of the marble
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
         
         tchildren = tnode.get_echildren()
         amrchildren = amrnode.get_children()

         if CopulaPredicates.is_adj_copula_clause(amrnode, tchildren=tchildren):
             new_parent = determine_functored_head(amrnode, functor="PAT")
             new_parent.parent = amrnode.parent
             for child in amrchildren:
                if child != new_parent:
                  child.parent = new_parent
             amrnode.remove() 
                                
           
def determine_functored_head(amrnode, functor):
    """Find the AMR child node which maps to a t-node with the given functor
    or to a coordination head that has [functor] members"""
    # Map amrnode to t-node
    tnode = amrnode.src_tnode
    
    # Find pathead t-node
    # (mutually exclusive)
    tchildren = tnode.get_children()
    
    tnode_echildren = None # May need them in resolving coap pathead candidates
    
    pathead_tnode = None
    for tc in tchildren:
      #  - Without coordination: find PAT child, return it
      if tc.functor == functor:
         pathead_tnode = tc
        #  - With coordination: find COORD head of PAT echildren, return it
         tc_descs = None
      if tc.nodetype == "coap":
         # (These are for efficiency, so that we compute children/descendants
         #  only once per node in question.)
         # Unfortunately, we will need to compute the echildren after all,
         # but let's only do this once per tnode
        if not tnode_echildren:           
          tnode_echildren = set(tnode.get_echildren())
        # Same here, but will need to do this once per coap child of tnode (tc)        
        if not tc_descs:
          tc_descs = set(tc.get_descendants()) # Match PAT candidates against these       
          
        for tnode_echild in tnode_echildren:
          if not tnode_echild in tc_descs:
            continue 
          if tnode_echild.functor == "PAT":
            pathead_node = tc
            
            # Corner cases, strange cases worth investigation:
            if not tc_echild.is_member:
              logging.warn('Found echild PAT of coap which is NOT a member. '
                            'This should never happen.')     
    
    # Map pathead t-node back to corresponding amrnode (which is non-trivial!)
    # Two steps:
    #  - find "direct" amrnode that directly corresponds to pathead_tnode
    #  - mark as pathead_amrnode the highest amrnode on the path from the
    #    direct amrnode to the input amrnode
    # NOTE: Is this algorithm for finding the right pathead_amrnode correct?
    # NOTE: How to generalize?

    # Step one:
    # Presupposes that coap and PAT t-nodes always have an AMR counterpart.
    direct_pathead_amrnode = get_corresponding_amrnode(pathead_tnode)
    
    # Step two:
    #
    # Presupposes that the amr tree topology is not so convoluted that the
    # amrnode which corresponds to the pathead_tnode is NOT a descendant of
    # the input amrnode.
    pathead_amrnode = direct_pathead_amrnode
    
    # Syntax note: try/except blocks are used when you suspect that a certain
    # type of error (called an Exception, like AttributeError, KeyError, etc.)
    # may happen in a part of your code. You can "wrap" the suspicious code
    # in a try-block and if the error happens, the except-block will activate
    # and deal with it.
    try:
      while pathead_amrnode.parent != amrnode:
        pathead_amrnode = direct_pathead_amrnode.parent
    except AttributeError:  # Specify which kind of errors you want to handle.
      logging.error('AMR strange topology: amr nodes corresponding to ancestor/'
                    'descendant pair of t-nodes are themselves not an ancestor/'
                    'descendant pair.')
      # Re-raise the error, so that the program terminates.
      raise
    
    return pathead_amrnode       
     
     
 
 class CopulaPredicates(object):
      """
      This class introduces checks for copula predicates  and the case 
      #"whiteness of the marble" 
      """   
      @staticmethod
      def is_adj_copula_clause(amrnode, tchildren=None): #"John is old." "John and Mary are good and 
      #nice"
          tnode = amrnode.src_tnode
          is_adj_copula_clause = False
          if tnode is None: 
             return False
          if tnode.t_lemma not in ('být', 'stát_se', 'zůstat'):
              return False
          else:
               if tchildren is None:
                   tchildren = tnode.get_echildren()
               
               for tchild in tchildren:
                  if (tchild.functor == "PAT" 
                          and tchild.formeme == startswith('adj:')):
                      is_adj_copula_clause = True
                  if tchild.functor == "ACT":
                      is_adj_copula_clause = True
               return is_adj_copula_clause 
           
               
                     
       
                                                                    